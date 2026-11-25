# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""G1: Biên bản họp (tp.meeting.minute) linked to calendar.event and generating project.task once on issue."""
from datetime import datetime
from markupsafe import Markup, escape

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import (
    active_internal_users,
    fold_text,
    format_date_vn,
    format_dt_local,
    is_live_admin_user,
)

MINUTE_STATES = [
    ('draft', 'Nháp'),
    ('confirmed', 'Đã xác nhận nội dung'),
    ('issued', 'Đã phát hành & giao việc'),
]

_INTERNAL_MINUTE_CTX = '_tp_minute_internal_write'


class TpMeetingMinute(models.Model):
    _name = 'tp.meeting.minute'
    _description = 'Biên bản họp TANPHAT ONE'
    _inherit = ['mail.thread']
    _order = 'meeting_date desc, id desc'

    code = fields.Char(string='Mã biên bản', required=True, copy=False, readonly=True, default='Mới', index=True)
    name = fields.Char(string='Tiêu đề cuộc họp', required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    calendar_event_id = fields.Many2one('calendar.event', string='Lịch họp liên kết', ondelete='set null', index=True)
    meeting_date = fields.Datetime(string='Thời gian họp', required=True, default=fields.Datetime.now, index=True)
    chair_user_id = fields.Many2one('res.users', string='Chủ trì', index=True)
    secretary_user_id = fields.Many2one(
        'res.users', string='Thư ký lập biên bản', required=True,
        default=lambda s: s.env.user, index=True,
    )
    attendee_user_ids = fields.Many2many(
        'res.users', 'tp_meeting_minute_attendee_rel', 'minute_id', 'user_id',
        string='Thành phần tham dự',
    )
    project_id = fields.Many2one('project.project', string='Dự án liên quan', ondelete='set null', index=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban chủ trì', ondelete='set null', index=True)
    discussion_content = fields.Text(string='Nội dung thảo luận')
    conclusion_content = fields.Text(string='Kết luận chính thức')
    action_item_ids = fields.One2many('tp.meeting.action.item', 'minute_id', string='Đầu việc kết luận', copy=False)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'tp_meeting_minute_attachment_rel', 'minute_id', 'attachment_id',
        string='Tệp đính kèm',
    )
    state = fields.Selection(MINUTE_STATES, default='draft', required=True, index=True, tracking=True)
    version = fields.Integer(string='Phiên bản', default=1, readonly=True)
    issued_at = fields.Datetime(string='Thời điểm phát hành', readonly=True)
    issued_by_id = fields.Many2one('res.users', string='Người phát hành', readonly=True)
    revision_reason = fields.Text(string='Lý do hiệu chỉnh phiên bản gần nhất', readonly=True)

    _code_company_uniq = models.Constraint(
        'UNIQUE(company_id, code)',
        'Mã biên bản họp phải là duy nhất trong công ty.',
    )

    # ------------------------------------------------------------------ Helpers & Guards
    def _tp_can_manage(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if is_live_admin_user(user, company=self.company_id):
            return True
        if user.id in (self.secretary_user_id.id, self.chair_user_id.id):
            return True
        if self.department_id and self.department_id.sudo().manager_id.user_id.id == user.id:
            return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == 'Mới':
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('tp.meeting.minute') or 'BBH-0001'
            if not vals.get('secretary_user_id'):
                vals['secretary_user_id'] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(_INTERNAL_MINUTE_CTX):
            for rec in self:
                if not rec._tp_can_manage():
                    raise AccessError(_('Chỉ Thư ký, Chủ trì cuộc họp, Trưởng phòng chủ trì hoặc Admin mới được sửa biên bản họp.'))
                if rec.state == 'issued':
                    raise UserError(_(
                        'Biên bản họp đã phát hành. Vui lòng sử dụng thao tác "Hiệu chỉnh phiên bản" kèm lý do bắt buộc.'
                    ))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Không xóa vật lý biên bản họp đã xác nhận hoặc đã phát hành.'))
            if not rec._tp_can_manage():
                raise AccessError(_('Bạn không có quyền xóa biên bản nháp này.'))
        return super().unlink()

    # ------------------------------------------------------------------ State Transitions
    def action_confirm(self):
        for rec in self:
            rec.check_access('read')
            if not rec._tp_can_manage():
                raise AccessError(_('Bạn không có quyền xác nhận biên bản họp này.'))
            if rec.state != 'draft':
                raise UserError(_('Chỉ biên bản ở trạng thái Nháp mới chuyển sang Đã xác nhận.'))
            if not (rec.conclusion_content or '').strip():
                raise UserError(_('Vui lòng nhập Kết luận chính thức trước khi xác nhận biên bản.'))
            rec.with_context(**{_INTERNAL_MINUTE_CTX: True}).write({'state': 'confirmed'})
            rec.message_post(body=Markup('<p>Đã xác nhận nội dung biên bản họp (Phiên bản v%s).</p>') % rec.version)
        return True

    def action_issue(self):
        """Issue meeting minute under row lock and generate project.task ONCE per action item (Mandatory Case #5)."""
        for rec in self:
            rec.check_access('read')
            self.env.cr.execute('SELECT id FROM tp_meeting_minute WHERE id = %s FOR UPDATE', [rec.id])
            rec.invalidate_recordset(['state', 'version'])
            if not rec._tp_can_manage():
                raise AccessError(_('Chỉ Chủ trì, Thư ký, Trưởng phòng chủ trì hoặc Admin mới được phát hành biên bản.'))
            if rec.state not in ('draft', 'confirmed'):
                raise UserError(_('Biên bản đã ở trạng thái phát hành.'))
            if not (rec.conclusion_content or '').strip():
                raise UserError(_('Bắt buộc có Kết luận chính thức trước khi phát hành biên bản họp.'))

            Task = self.env['project.task'].sudo()
            created_tasks = []
            for item in rec.action_item_ids:
                if item.task_id:
                    # Already generated in an earlier version -> NEVER duplicate!
                    continue
                if not (item.name or '').strip() or not item.assignee_user_id:
                    raise UserError(_('Mỗi đầu việc kết luận phải có đầy đủ Nội dung và Người phụ trách.'))
                task_vals = {
                    'name': item.name.strip(),
                    'description': Markup(
                        '<p>Giao từ Biên bản họp <strong>%s — %s</strong> (v%s).</p><p>Kết luận: %s</p>'
                    ) % (escape(rec.code), escape(rec.name), rec.version, escape(rec.conclusion_content or '')),
                    'user_ids': [Command.set([item.assignee_user_id.id])],
                    'project_id': rec.project_id.id or False,
                    'date_deadline': item.deadline or False,
                }
                if 'tp_deliverable' in Task._fields and item.deliverable_expected:
                    task_vals['tp_deliverable'] = item.deliverable_expected.strip()
                if 'tp_source_kind' in Task._fields:
                    task_vals['tp_source_kind'] = 'meeting'
                new_task = Task.create(task_vals)
                item.with_context(**{_INTERNAL_MINUTE_CTX: True}).write({'task_id': new_task.id})
                created_tasks.append(new_task)

            now = fields.Datetime.now()
            rec.with_context(**{_INTERNAL_MINUTE_CTX: True}).write({
                'state': 'issued',
                'issued_at': now,
                'issued_by_id': self.env.uid,
            })
            rec.message_post(
                body=Markup('<p>Đã phát hành biên bản họp <strong>v%s</strong> (%s đầu việc mới được khởi tạo).</p>') % (
                    rec.version, len(created_tasks)
                )
            )
        return True

    def action_revise(self, reason, updated_vals=None):
        """Open a post-issue revision with mandatory reason, incrementing version without deleting tasks."""
        self.ensure_one()
        self.check_access('read')
        self.env.cr.execute('SELECT id FROM tp_meeting_minute WHERE id = %s FOR UPDATE', [self.id])
        if not self._tp_can_manage():
            raise AccessError(_('Bạn không có quyền hiệu chỉnh biên bản họp này.'))
        if self.state != 'issued':
            raise UserError(_('Chỉ hiệu chỉnh phiên bản đối với biên bản đã phát hành.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập Lý do hiệu chỉnh biên bản sau phát hành.'))

        new_ver = self.version + 1
        write_vals = {
            'state': 'confirmed',
            'version': new_ver,
            'revision_reason': clean_reason,
        }
        if updated_vals:
            for k in ('name', 'discussion_content', 'conclusion_content'):
                if k in updated_vals and updated_vals[k] is not None:
                    write_vals[k] = updated_vals[k]
        self.with_context(**{_INTERNAL_MINUTE_CTX: True}).write(write_vals)
        self.message_post(
            body=Markup('<p>Mở hiệu chỉnh biên bản lên <strong>v%s</strong>. Lý do: %s</p>') % (
                new_ver, escape(clean_reason)
            )
        )
        return {'version': new_ver, 'state': self.state}

    # ------------------------------------------------------------------ OWL Workspace RPCs
    @api.model
    def tp_prefill_from_calendar_event(self, event_id):
        ev = self.env['calendar.event'].browse(int(event_id or 0)).exists()
        if not ev:
            raise UserError(_('Không tìm thấy lịch họp liên kết.'))
        ev.check_access('read')
        existing = self.search([('calendar_event_id', '=', ev.id)], limit=1)
        if existing:
            return {'existing_minute_id': existing.id}
        att_users = active_internal_users(ev.partner_ids.sudo().user_ids, company=self.env.company)
        return {
            'existing_minute_id': 0,
            'calendar_event_id': ev.id,
            'name': ev.name or '',
            'meeting_date': ev.start.strftime('%Y-%m-%dT%H:%M') if ev.start else '',
            'project_id': ev.tp_project_id.id if 'tp_project_id' in ev._fields and ev.tp_project_id else False,
            'chair_user_id': ev.user_id.id or self.env.uid,
            'attendee_user_ids': att_users.ids,
        }

    @api.model
    def tp_minute_list_data(self, params=None):
        params = params or {}
        dom = [('company_id', '=', self.env.company.id)]
        st = (params.get('state') or '').strip()
        if st in dict(MINUTE_STATES):
            dom.append(('state', '=', st))
        dept_id = int(params.get('department_id') or 0)
        if dept_id > 0:
            dom.append(('department_id', '=', dept_id))
        proj_id = int(params.get('project_id') or 0)
        if proj_id > 0:
            dom.append(('project_id', '=', proj_id))
        date_from = (params.get('date_from') or '').strip()
        date_to = (params.get('date_to') or '').strip()
        if date_from and date_to and date_from > date_to:
            raise UserError(_('Từ ngày không được lớn hơn Đến ngày.'))
        if date_from:
            dom.append(('meeting_date', '>=', f'{date_from} 00:00:00'))
        if date_to:
            dom.append(('meeting_date', '<=', f'{date_to} 23:59:59'))

        search_q = (params.get('search') or '').strip()
        if search_q:
            needle = fold_text(search_q)
            cands = self.search_fetch(dom, ['code', 'name', 'conclusion_content'])
            matched = [r.id for r in cands if any(needle in fold_text(v) for v in (r.code, r.name, r.conclusion_content))]
            dom.append(('id', 'in', matched))

        total = self.search_count(dom)
        page_size = int(params.get('page_size') or 20)
        if page_size not in (10, 20, 50, 100):
            page_size = 20
        page = max(int(params.get('page') or 1), 1)
        max_page = max((total + page_size - 1) // page_size, 1)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size

        rows = []
        for r in self.search(dom, order='meeting_date desc, id desc', offset=offset, limit=page_size):
            tasks_done = sum(1 for it in r.action_item_ids if it.task_id and it.task_id.sudo().state == '1_done')
            rows.append({
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'meeting_date': format_dt_local(r.meeting_date),
                'chair_name': r.chair_user_id.sudo().name if r.chair_user_id else '—',
                'secretary_name': r.secretary_user_id.sudo().name if r.secretary_user_id else '—',
                'department_name': r.department_id.sudo().name if r.department_id else '—',
                'project_name': r.project_id.sudo().name if r.project_id else '—',
                'state': r.state,
                'state_label': dict(MINUTE_STATES).get(r.state, r.state),
                'version': r.version,
                'action_count': len(r.action_item_ids),
                'tasks_done': tasks_done,
            })

        depts = self.env['hr.department'].search([('company_id', '=', self.env.company.id)], order='name')
        projs = self.env['project.project'].search([], order='name', limit=100)
        users = active_internal_users(
            self.env['res.users'].sudo().search([('active', '=', True), ('share', '=', False)]),
            company=self.env.company,
        )
        events = self.env['calendar.event'].search([], order='start desc', limit=50)
        return {
            'rows': rows,
            'total': total,
            'page': page,
            'page_size': page_size,
            'max_page': max_page,
            'filter_options': {
                'states': [{'key': k, 'label': v} for k, v in MINUTE_STATES],
                'departments': [{'id': d.id, 'name': d.name} for d in depts],
                'projects': [{'id': p.id, 'name': p.name} for p in projs],
                'users': [{'id': u.id, 'name': u.name} for u in users],
                'events': [{'id': e.id, 'name': f"{e.name} ({format_dt_local(e.start)})"} for e in events],
            },
        }

    @api.model
    def tp_minute_detail_data(self, minute_id):
        rec = self.browse(int(minute_id or 0)).exists()
        if not rec:
            raise UserError(_('Không tìm thấy biên bản họp hoặc bạn không có quyền xem.'))
        rec.check_access('read')
        can_manage = rec._tp_can_manage()
        items = []
        for it in rec.action_item_ids:
            tsudo = it.task_id.sudo() if it.task_id else False
            items.append({
                'id': it.id,
                'name': it.name,
                'assignee_user_id': it.assignee_user_id.id,
                'assignee_name': it.assignee_user_id.sudo().name,
                'deadline': it.deadline.isoformat() if it.deadline else '',
                'deadline_display': format_date_vn(it.deadline),
                'deliverable_expected': it.deliverable_expected or '',
                'task_id': tsudo.id if tsudo else 0,
                'task_state_label': (
                    'Đã xác nhận hoàn thành' if (tsudo and tsudo.state == '1_done')
                    else ('Đã báo hoàn thành' if (tsudo and getattr(tsudo, 'tp_exec_report_state', '') == 'reported_done')
                          else ('Đang thực hiện' if tsudo else 'Chưa phát hành việc'))
                ),
            })
        atts = [{
            'id': a.id,
            'name': a.name,
            'file_size': a.file_size or 0,
            'download_url': f'/tp_digital_office/attachment/tp.meeting.minute/{rec.id}/{a.id}',
        } for a in rec.attachment_ids.sudo() if a.res_model == 'tp.meeting.minute' and a.res_id == rec.id]
        return {
            'id': rec.id,
            'code': rec.code,
            'name': rec.name,
            'calendar_event_id': rec.calendar_event_id.id or 0,
            'calendar_event_name': rec.calendar_event_id.sudo().name if rec.calendar_event_id else '',
            'meeting_date_iso': rec.meeting_date.strftime('%Y-%m-%dT%H:%M') if rec.meeting_date else '',
            'meeting_date_display': format_dt_local(rec.meeting_date),
            'chair_user_id': rec.chair_user_id.id or 0,
            'chair_name': rec.chair_user_id.sudo().name if rec.chair_user_id else '—',
            'secretary_user_id': rec.secretary_user_id.id,
            'secretary_name': rec.secretary_user_id.sudo().name,
            'attendee_user_ids': rec.attendee_user_ids.ids,
            'attendee_names': [u.name for u in rec.attendee_user_ids.sudo()],
            'project_id': rec.project_id.id or 0,
            'project_name': rec.project_id.sudo().name if rec.project_id else '',
            'department_id': rec.department_id.id or 0,
            'department_name': rec.department_id.sudo().name if rec.department_id else '',
            'discussion_content': rec.discussion_content or '',
            'conclusion_content': rec.conclusion_content or '',
            'state': rec.state,
            'state_label': dict(MINUTE_STATES).get(rec.state, rec.state),
            'version': rec.version,
            'issued_at': format_dt_local(rec.issued_at),
            'issued_by': rec.issued_by_id.sudo().name if rec.issued_by_id else '',
            'revision_reason': rec.revision_reason or '',
            'action_items': items,
            'attachments': atts,
            'can_manage': can_manage,
        }

    @api.model
    def tp_save_minute(self, payload, issue_now=False):
        payload = payload or {}
        field_errors = []
        name = (payload.get('name') or '').strip()
        if not name:
            field_errors.append({
                'id': 'min_name',
                'label': 'Tiêu đề cuộc họp',
                'location': 'Thông tin cuộc họp',
                'message': 'Vui lòng nhập Tiêu đề cuộc họp.',
            })
        conclusion = (payload.get('conclusion_content') or '').strip()
        if issue_now and not conclusion:
            field_errors.append({
                'id': 'min_conclusion',
                'label': 'Kết luận chính thức',
                'location': 'Nội dung biên bản',
                'message': 'Vui lòng nhập Kết luận chính thức trước khi phát hành.',
            })
        raw_items = payload.get('action_items') or []
        for idx, it in enumerate(raw_items, start=1):
            if not (it.get('name') or '').strip() or not int(it.get('assignee_user_id') or 0):
                field_errors.append({
                    'id': 'min_action_items',
                    'label': f'Đầu việc kết luận #{idx}',
                    'location': 'Bảng giao việc',
                    'message': f'Đầu việc #{idx} cần có đầy đủ Nội dung và Người phụ trách.',
                })
        if field_errors:
            return {'ok': False, 'field_errors': field_errors}

        mdate = payload.get('meeting_date_iso') or ''
        parsed_dt = fields.Datetime.now()
        if mdate:
            try:
                parsed_dt = datetime.fromisoformat(mdate.replace('Z', ''))
            except ValueError:
                pass

        vals = {
            'name': name,
            'calendar_event_id': int(payload['calendar_event_id']) if int(payload.get('calendar_event_id') or 0) > 0 else False,
            'meeting_date': parsed_dt,
            'chair_user_id': int(payload['chair_user_id']) if int(payload.get('chair_user_id') or 0) > 0 else self.env.uid,
            'project_id': int(payload['project_id']) if int(payload.get('project_id') or 0) > 0 else False,
            'department_id': int(payload['department_id']) if int(payload.get('department_id') or 0) > 0 else False,
            'discussion_content': (payload.get('discussion_content') or '').strip() or False,
            'conclusion_content': conclusion or False,
            'attendee_user_ids': [Command.set([int(x) for x in (payload.get('attendee_user_ids') or []) if int(x or 0) > 0])],
        }

        min_id = int(payload.get('id') or 0)
        if min_id > 0:
            rec = self.browse(min_id).exists()
            if not rec:
                raise UserError(_('Không tìm thấy biên bản họp.'))
            rec.write(vals)
        else:
            rec = self.create(vals)

        # Sync action items without deleting items that already spawned a task
        existing_by_id = {it.id: it for it in rec.action_item_ids}
        keep_ids = set()
        for idx, it in enumerate(raw_items, start=1):
            it_id = int(it.get('id') or 0)
            item_vals = {
                'sequence': idx * 10,
                'name': (it.get('name') or '').strip(),
                'assignee_user_id': int(it['assignee_user_id']),
                'deadline': it.get('deadline') or False,
                'deliverable_expected': (it.get('deliverable_expected') or '').strip() or False,
            }
            if it_id and it_id in existing_by_id:
                keep_ids.add(it_id)
                existing_by_id[it_id].write(item_vals)
            else:
                created_it = self.env['tp.meeting.action.item'].create({**item_vals, 'minute_id': rec.id})
                keep_ids.add(created_it.id)

        for old_id, old_it in existing_by_id.items():
            if old_id not in keep_ids and not old_it.task_id:
                old_it.unlink()

        if issue_now:
            rec.action_issue()
        return {'ok': True, 'id': rec.id, 'code': rec.code, 'state': rec.state}


class TpMeetingActionItem(models.Model):
    _name = 'tp.meeting.action.item'
    _description = 'Đầu việc kết luận từ Biên bản họp'
    _order = 'sequence, id'

    minute_id = fields.Many2one('tp.meeting.minute', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Nội dung đầu việc', required=True)
    assignee_user_id = fields.Many2one('res.users', string='Người phụ trách', required=True, index=True)
    deadline = fields.Date(string='Hạn hoàn thành')
    deliverable_expected = fields.Char(string='Sản phẩm đầu ra')
    task_id = fields.Many2one('project.task', string='Công việc đã sinh', readonly=True, ondelete='restrict', index=True)

    def unlink(self):
        for item in self:
            if item.task_id:
                raise UserError(_(
                    'Không được xóa đầu việc "%s" vì đã sinh Công việc #%s trên hệ thống.'
                ) % (item.name, item.task_id.id))
        return super().unlink()
