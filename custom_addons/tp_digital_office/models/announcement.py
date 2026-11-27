# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""G2: Thông báo nội bộ (tp.announcement) with explicit versioned Read Acknowledgement (Mandatory Case #9)."""
from markupsafe import Markup, escape
from psycopg2 import IntegrityError

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import (
    active_internal_users,
    fold_text,
    format_date_vn,
    format_dt_local,
    is_live_admin_user,
)

ANNOUNCEMENT_CATEGORIES = [
    ('executive', 'Chỉ đạo / Điều hành Ban Giám đốc'),
    ('policy', 'Quy chế / Quy định nội bộ'),
    ('hr_admin', 'Hành chính - Nhân sự'),
    ('project', 'Thông báo Dự án / Kỹ thuật'),
    ('general', 'Thông báo chung'),
]

AUDIENCE_SCOPES = [
    ('company', 'Toàn công ty'),
    ('departments', 'Theo phòng ban'),
    ('users', 'Người nhận cụ thể'),
]

ANNOUNCEMENT_STATES = [
    ('draft', 'Nháp'),
    ('published', 'Đang hiệu lực'),
    ('superseded', 'Đã thay thế'),
    ('revoked', 'Đã thu hồi'),
]

_INTERNAL_ANN_CTX = '_tp_announcement_internal'


class TpAnnouncement(models.Model):
    _name = 'tp.announcement'
    _description = 'Thông báo nội bộ chính thức TANPHAT ONE'
    _inherit = ['mail.thread']
    _order = 'published_at desc, id desc'

    code = fields.Char(string='Số hiệu thông báo', required=True, copy=False, readonly=True, default='Mới', index=True)
    name = fields.Char(string='Tiêu đề thông báo', required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    category = fields.Selection(ANNOUNCEMENT_CATEGORIES, default='general', required=True, index=True)
    issuing_department_id = fields.Many2one('hr.department', string='Đơn vị ban hành', ondelete='set null', index=True)
    issuer_user_id = fields.Many2one(
        'res.users', string='Người ban hành', required=True,
        default=lambda s: s.env.user, index=True,
    )
    audience_scope = fields.Selection(AUDIENCE_SCOPES, default='company', required=True, index=True)
    target_department_ids = fields.Many2many(
        'hr.department', 'tp_announcement_dept_rel', 'announcement_id', 'department_id',
        string='Phòng ban nhận',
    )
    target_user_ids = fields.Many2many(
        'res.users', 'tp_announcement_user_rel', 'announcement_id', 'user_id',
        string='Người nhận cụ thể',
    )
    body = fields.Text(string='Nội dung chính thức', required=True)
    effective_date = fields.Date(string='Ngày hiệu lực', default=fields.Date.context_today, index=True)
    require_ack = fields.Boolean(string='Yêu cầu xác nhận đã đọc', default=True)
    ack_deadline = fields.Date(string='Hạn xác nhận đã đọc')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'tp_announcement_attachment_rel', 'announcement_id', 'attachment_id',
        string='Văn bản đính kèm',
    )
    state = fields.Selection(ANNOUNCEMENT_STATES, default='draft', required=True, index=True, tracking=True)
    version = fields.Integer(string='Phiên bản', default=1, readonly=True)
    published_at = fields.Datetime(string='Thời điểm phát hành', readonly=True, index=True)
    revoked_reason = fields.Text(string='Lý do thu hồi / thay thế', readonly=True)
    ack_ids = fields.One2many('tp.announcement.ack', 'announcement_id', string='Danh sách xác nhận đã đọc')

    _code_company_uniq = models.Constraint(
        'UNIQUE(company_id, code)',
        'Số hiệu thông báo phải là duy nhất trong công ty.',
    )

    # ------------------------------------------------------------------ Authority & Audience Helpers
    @api.model
    def _tp_can_user_publish(self, user=None, scope='departments', dept_ids=None):
        user = user or self.env.user
        if is_live_admin_user(user, company=self.env.company):
            return True
        if user.has_group('tp_hr_workspace.group_tp_hr_manager') or user.has_group('hr.group_hr_manager'):
            return True
        managed_depts = self.env['hr.department'].sudo().search([
            ('company_id', '=', self.env.company.id),
            ('manager_id.user_id', '=', user.id),
        ])
        if not managed_depts:
            return False
        if scope == 'company':
            return False
        if scope == 'departments' and dept_ids:
            return set(dept_ids).issubset(set(managed_depts.ids))
        return True

    def _tp_can_manage(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if is_live_admin_user(user, company=self.company_id):
            return True
        return bool(
            self.issuer_user_id.id == user.id
            and self._tp_can_user_publish(
                user=user, scope=self.audience_scope, dept_ids=self.target_department_ids.ids,
            ),
        )

    def _tp_target_recipient_users(self):
        self.ensure_one()
        all_internal = active_internal_users(
            self.env['res.users'].sudo().search([('active', '=', True), ('share', '=', False)]),
            company=self.company_id,
        )
        if self.audience_scope == 'company':
            return all_internal
        if self.audience_scope == 'departments':
            emps = self.env['hr.employee'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('department_id', 'child_of', self.target_department_ids.ids or [0]),
                ('user_id', '!=', False),
            ])
            return all_internal & emps.mapped('user_id')
        return all_internal & self.target_user_ids.sudo()

    def _tp_is_user_in_audience(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if self._tp_can_manage(user):
            return True
        if self.state == 'draft':
            return False
        return user.id in self._tp_target_recipient_users().ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            scope = vals.get('audience_scope') or 'departments'
            if not self._tp_can_user_publish(self.env.user, scope=scope):
                raise AccessError(_(
                    'Chỉ Ban Giám đốc (Admin), Quản lý Nhân sự hoặc Trưởng bộ phận mới có thẩm quyền soạn thông báo nội bộ theo phạm vi này.',
                ))
            if not vals.get('code') or vals['code'] == 'Mới':
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('tp.announcement') or 'TBNB-0001'
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(_INTERNAL_ANN_CTX):
            for rec in self:
                if not rec._tp_can_manage():
                    raise AccessError(_('Bạn không có quyền chỉnh sửa thông báo này.'))
                if rec.state != 'draft':
                    raise UserError(_(
                        'Thông báo đã phát hành. Vui lòng dùng thao tác "Cập nhật phiên bản" hoặc "Thu hồi" kèm lý do.',
                    ))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Không xóa vật lý thông báo nội bộ đã phát hành.'))
            if not rec._tp_can_manage():
                raise AccessError(_('Bạn không có quyền xóa bản nháp thông báo này.'))
        return super().unlink()

    # ------------------------------------------------------------------ Transitions & Explicit Read Ack
    def action_publish(self):
        for rec in self:
            if not rec._tp_can_manage():
                raise AccessError(_('Bạn không có quyền phát hành thông báo này.'))
            if not self._tp_can_user_publish(
                self.env.user, scope=rec.audience_scope, dept_ids=rec.target_department_ids.ids,
            ):
                raise AccessError(_('Phạm vi đối tượng nhận vượt quá thẩm quyền phát hành của bạn.'))
            if rec.state != 'draft':
                raise UserError(_('Chỉ thông báo ở trạng thái Nháp mới có thể phát hành.'))
            if rec.audience_scope == 'departments' and not rec.target_department_ids:
                raise UserError(_('Vui lòng chọn ít nhất một Phòng ban nhận thông báo.'))
            if rec.audience_scope == 'users' and not rec.target_user_ids:
                raise UserError(_('Vui lòng chọn ít nhất một Người nhận thông báo.'))

            rec.with_context(**{_INTERNAL_ANN_CTX: True}).write({
                'state': 'published',
                'published_at': fields.Datetime.now(),
            })
            rec.message_post(
                body=Markup('<p>Đã phát hành chính thức thông báo nội bộ <strong>%s</strong> (Phiên bản v%s).</p>') % (
                    escape(rec.code), rec.version,
                ),
            )
        return True

    def action_revise_published(self, updated_vals, major_reack=True, reason=''):
        """Revise a published announcement. If major_reack=True, increments version so recipients must re-acknowledge."""
        self.ensure_one()
        if not self._tp_can_manage():
            raise AccessError(_('Bạn không có quyền cập nhật phiên bản thông báo này.'))
        if self.state != 'published':
            raise UserError(_('Chỉ cập nhật phiên bản cho thông báo đang hiệu lực.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập Lý do cập nhật thông báo đã phát hành.'))

        new_ver = self.version + 1 if major_reack else self.version
        wvals = {'version': new_ver, 'published_at': fields.Datetime.now()}
        for k in ('name', 'body', 'effective_date', 'ack_deadline', 'require_ack'):
            if updated_vals and k in updated_vals and updated_vals[k] is not None:
                wvals[k] = updated_vals[k]
        self.with_context(**{_INTERNAL_ANN_CTX: True}).write(wvals)
        self.message_post(
            body=Markup('<p>Cập nhật thông báo lên <strong>v%s</strong> (%s). Lý do: %s</p>') % (
                new_ver,
                'yêu cầu xác nhận lại' if major_reack else 'hiệu đính nhỏ',
                escape(clean_reason),
            ),
        )
        return {'version': new_ver}

    def action_revoke(self, reason, mode='revoked'):
        self.ensure_one()
        if not self._tp_can_manage():
            raise AccessError(_('Bạn không có quyền thu hồi thông báo này.'))
        if self.state != 'published':
            raise UserError(_('Chỉ thu hồi hoặc thay thế thông báo đang hiệu lực.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập Lý do thu hồi / thay thế thông báo.'))
        target_state = 'superseded' if mode == 'superseded' else 'revoked'
        self.with_context(**{_INTERNAL_ANN_CTX: True}).write({
            'state': target_state,
            'revoked_reason': clean_reason,
        })
        self.message_post(
            body=Markup('<p>Đã chuyển trạng thái sang <strong>%s</strong>. Lý do: %s</p>') % (
                escape(dict(ANNOUNCEMENT_STATES).get(target_state, target_state)),
                escape(clean_reason),
            ),
        )
        return True

    @api.model
    def tp_acknowledge_announcement(self, announcement_id, operation_token=''):
        """Explicit user action 'Xác nhận đã đọc' — NEVER triggered merely by opening detail (Mandatory Case #9)."""
        rec = self.browse(int(announcement_id or 0)).exists()
        if not rec or not rec._tp_is_user_in_audience():
            raise AccessError(_('Bạn không thuộc đối tượng nhận thông báo này.'))
        if rec.state != 'published':
            raise UserError(_('Chỉ xác nhận đã đọc đối với thông báo đang có hiệu lực.'))

        Ack = self.env['tp.announcement.ack'].sudo()
        existing = Ack.search([
            ('announcement_id', '=', rec.id),
            ('user_id', '=', self.env.uid),
            ('acked_version', '=', rec.version),
        ], limit=1)
        if existing:
            return {
                'already_acked': True,
                'acked_version': existing.acked_version,
                'acked_at': format_dt_local(existing.acked_at),
            }
        try:
            with self.env.cr.savepoint():
                ack = Ack.create({
                    'announcement_id': rec.id,
                    'user_id': self.env.uid,
                    'acked_version': rec.version,
                    'operation_token': (operation_token or '').strip() or False,
                })
        except IntegrityError:
            existing = Ack.search([
                ('announcement_id', '=', rec.id),
                ('user_id', '=', self.env.uid),
                ('acked_version', '=', rec.version),
            ], limit=1)
            return {
                'already_acked': True,
                'acked_version': existing.acked_version if existing else rec.version,
                'acked_at': format_dt_local(existing.acked_at) if existing else '',
            }
        return {
            'already_acked': False,
            'acked_version': ack.acked_version,
            'acked_at': format_dt_local(ack.acked_at),
        }

    @api.model
    def tp_get_ack_tracking(self, announcement_id):
        rec = self.browse(int(announcement_id or 0)).exists()
        if not rec:
            raise UserError(_('Không tìm thấy thông báo.'))
        if not rec._tp_can_manage():
            raise AccessError(_('Chỉ người ban hành hoặc Quản trị viên mới xem được báo cáo chi tiết người chưa xác nhận.'))
        recipients = rec._tp_target_recipient_users()
        acks_current = {
            a.user_id.id: a
            for a in rec.ack_ids.sudo().filtered(lambda x: x.acked_version == rec.version)
        }
        acked_list = []
        unacked_list = []
        for u in recipients.sorted('name'):
            if u.id in acks_current:
                ack = acks_current[u.id]
                acked_list.append({
                    'user_id': u.id,
                    'name': u.name,
                    'acked_at': format_dt_local(ack.acked_at),
                    'version': ack.acked_version,
                })
            else:
                unacked_list.append({
                    'user_id': u.id,
                    'name': u.name,
                })
        return {
            'version': rec.version,
            'total_recipients': len(recipients),
            'acked_count': len(acked_list),
            'unacked_count': len(unacked_list),
            'acked_users': acked_list,
            'unacked_users': unacked_list,
        }

    # ------------------------------------------------------------------ OWL Workspace RPCs
    @api.model
    def tp_announcement_list_data(self, params=None):
        params = params or {}
        uid = self.env.uid
        all_candidates = self.search([('company_id', '=', self.env.company.id)], order='published_at desc, id desc')
        visible = all_candidates.filtered(lambda r: r._tp_is_user_in_audience())

        cat = (params.get('category') or '').strip()
        if cat in dict(ANNOUNCEMENT_CATEGORIES):
            visible = visible.filtered(lambda r: r.category == cat)
        st = (params.get('state') or '').strip()
        if st in dict(ANNOUNCEMENT_STATES):
            visible = visible.filtered(lambda r: r.state == st)
        dept_id = int(params.get('department_id') or 0)
        if dept_id > 0:
            visible = visible.filtered(lambda r: r.issuing_department_id.id == dept_id)

        ack_filter = (params.get('ack_filter') or '').strip()
        if ack_filter in ('unacked', 'acked'):
            def _matches_ack(r):
                has_ack = any(a.user_id.id == uid and a.acked_version == r.version for a in r.ack_ids.sudo())
                return has_ack if ack_filter == 'acked' else (r.require_ack and r.state == 'published' and not has_ack)
            visible = visible.filtered(_matches_ack)

        search_q = (params.get('search') or '').strip()
        if search_q:
            needle = fold_text(search_q)
            visible = visible.filtered(lambda r: any(needle in fold_text(v) for v in (r.code, r.name, r.body)))

        total = len(visible)
        page_size = int(params.get('page_size') or 20)
        if page_size not in (10, 20, 50, 100):
            page_size = 20
        page = max(int(params.get('page') or 1), 1)
        max_page = max((total + page_size - 1) // page_size, 1)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size

        rows = []
        for r in visible[offset:offset + page_size]:
            my_ack = r.ack_ids.sudo().filtered(lambda a: a.user_id.id == uid and a.acked_version == r.version)[:1]
            rows.append({
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'category': r.category,
                'category_label': dict(ANNOUNCEMENT_CATEGORIES).get(r.category, r.category),
                'issuing_department': r.issuing_department_id.sudo().name if r.issuing_department_id else 'Ban Giám đốc',
                'issuer_name': r.issuer_user_id.sudo().name,
                'audience_label': dict(AUDIENCE_SCOPES).get(r.audience_scope, r.audience_scope),
                'effective_date': format_date_vn(r.effective_date),
                'published_at': format_dt_local(r.published_at),
                'state': r.state,
                'state_label': dict(ANNOUNCEMENT_STATES).get(r.state, r.state),
                'version': r.version,
                'require_ack': r.require_ack,
                'is_acked': bool(my_ack),
                'acked_at': format_dt_local(my_ack.acked_at) if my_ack else '',
            })

        depts = self.env['hr.department'].search([('company_id', '=', self.env.company.id)], order='name')
        users = active_internal_users(
            self.env['res.users'].sudo().search([('active', '=', True), ('share', '=', False)]),
            company=self.env.company,
        )
        return {
            'rows': rows,
            'total': total,
            'page': page,
            'page_size': page_size,
            'max_page': max_page,
            'can_create': self._tp_can_user_publish(self.env.user, scope='users'),
            'can_publish_company': self._tp_can_user_publish(self.env.user, scope='company'),
            'filter_options': {
                'categories': [{'key': k, 'label': v} for k, v in ANNOUNCEMENT_CATEGORIES],
                'states': [{'key': k, 'label': v} for k, v in ANNOUNCEMENT_STATES],
                'scopes': [{'key': k, 'label': v} for k, v in AUDIENCE_SCOPES],
                'departments': [{'id': d.id, 'name': d.name} for d in depts],
                'users': [{'id': u.id, 'name': u.name} for u in users],
            },
        }

    @api.model
    def tp_announcement_detail_data(self, announcement_id):
        """Read-only fetch — NEVER writes an acknowledgement row automatically!"""
        rec = self.browse(int(announcement_id or 0)).exists()
        if not rec or not rec._tp_is_user_in_audience():
            raise AccessError(_('Không tìm thấy thông báo hoặc bạn không thuộc phạm vi nhận.'))

        uid = self.env.uid
        my_ack = rec.ack_ids.sudo().filtered(lambda a: a.user_id.id == uid and a.acked_version == rec.version)[:1]
        prev_acks = rec.ack_ids.sudo().filtered(lambda a: a.user_id.id == uid and a.acked_version < rec.version)
        atts = [{
            'id': a.id,
            'name': a.name,
            'file_size': a.file_size or 0,
            'download_url': f'/tp_digital_office/attachment/tp.announcement/{rec.id}/{a.id}',
        } for a in rec.attachment_ids.sudo() if a.res_model == 'tp.announcement' and a.res_id == rec.id]
        return {
            'id': rec.id,
            'code': rec.code,
            'name': rec.name,
            'category': rec.category,
            'category_label': dict(ANNOUNCEMENT_CATEGORIES).get(rec.category, rec.category),
            'issuing_department_id': rec.issuing_department_id.id or 0,
            'issuing_department_name': rec.issuing_department_id.sudo().name if rec.issuing_department_id else 'Ban Giám đốc',
            'issuer_name': rec.issuer_user_id.sudo().name,
            'audience_scope': rec.audience_scope,
            'audience_label': dict(AUDIENCE_SCOPES).get(rec.audience_scope, rec.audience_scope),
            'target_department_ids': rec.target_department_ids.ids,
            'target_department_names': [d.name for d in rec.target_department_ids.sudo()],
            'target_user_ids': rec.target_user_ids.ids,
            'target_user_names': [u.name for u in rec.target_user_ids.sudo()],
            'body': rec.body or '',
            'effective_date': rec.effective_date.isoformat() if rec.effective_date else '',
            'effective_date_display': format_date_vn(rec.effective_date),
            'require_ack': rec.require_ack,
            'ack_deadline': rec.ack_deadline.isoformat() if rec.ack_deadline else '',
            'ack_deadline_display': format_date_vn(rec.ack_deadline),
            'state': rec.state,
            'state_label': dict(ANNOUNCEMENT_STATES).get(rec.state, rec.state),
            'version': rec.version,
            'published_at': format_dt_local(rec.published_at),
            'revoked_reason': rec.revoked_reason or '',
            'is_acked': bool(my_ack),
            'acked_at': format_dt_local(my_ack.acked_at) if my_ack else '',
            'had_previous_version_ack': bool(prev_acks and not my_ack),
            'attachments': atts,
            'can_manage': rec._tp_can_manage(),
        }

    @api.model
    def tp_save_announcement(self, payload, publish_now=False):
        payload = payload or {}
        field_errors = []
        name = (payload.get('name') or '').strip()
        body = (payload.get('body') or '').strip()
        scope = payload.get('audience_scope') or 'company'
        dept_ids = [int(x) for x in (payload.get('target_department_ids') or []) if int(x or 0) > 0]
        user_ids = [int(x) for x in (payload.get('target_user_ids') or []) if int(x or 0) > 0]

        if not name:
            field_errors.append({
                'id': 'ann_name',
                'label': 'Tiêu đề thông báo',
                'location': 'Nội dung thông báo',
                'message': 'Vui lòng nhập Tiêu đề thông báo.',
            })
        if not body:
            field_errors.append({
                'id': 'ann_body',
                'label': 'Nội dung chính thức',
                'location': 'Nội dung thông báo',
                'message': 'Vui lòng nhập Nội dung chính thức của thông báo.',
            })
        if scope == 'departments' and not dept_ids:
            field_errors.append({
                'id': 'ann_depts',
                'label': 'Phòng ban nhận',
                'location': 'Đối tượng nhận',
                'message': 'Vui lòng chọn ít nhất một Phòng ban nhận.',
            })
        if scope == 'users' and not user_ids:
            field_errors.append({
                'id': 'ann_users',
                'label': 'Người nhận cụ thể',
                'location': 'Đối tượng nhận',
                'message': 'Vui lòng chọn ít nhất một Người nhận.',
            })
        if field_errors:
            return {'ok': False, 'field_errors': field_errors}

        vals = {
            'name': name,
            'category': payload.get('category') or 'general',
            'issuing_department_id': int(payload['issuing_department_id']) if int(payload.get('issuing_department_id') or 0) > 0 else False,
            'audience_scope': scope,
            'target_department_ids': [Command.set(dept_ids)],
            'target_user_ids': [Command.set(user_ids)],
            'body': body,
            'effective_date': payload.get('effective_date') or fields.Date.context_today(self),
            'require_ack': bool(payload.get('require_ack', True)),
            'ack_deadline': payload.get('ack_deadline') or False,
        }
        ann_id = int(payload.get('id') or 0)
        if ann_id > 0:
            rec = self.browse(ann_id).exists()
            if not rec:
                raise UserError(_('Không tìm thấy thông báo.'))
            rec.write(vals)
        else:
            rec = self.create(vals)

        if publish_now:
            rec.action_publish()
        return {'ok': True, 'id': rec.id, 'code': rec.code, 'state': rec.state}


class TpAnnouncementAck(models.Model):
    _name = 'tp.announcement.ack'
    _description = 'Xác nhận đã đọc Thông báo nội bộ'
    _order = 'acked_at desc, id desc'

    announcement_id = fields.Many2one('tp.announcement', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade', index=True)
    acked_version = fields.Integer(string='Phiên bản đã xác nhận', required=True, default=1)
    acked_at = fields.Datetime(string='Thời điểm xác nhận', required=True, default=fields.Datetime.now)
    operation_token = fields.Char(index=True)

    _user_version_uniq = models.Constraint(
        'UNIQUE(announcement_id, user_id, acked_version)',
        'Mỗi người nhận chỉ xác nhận một lần cho cùng một phiên bản thông báo.',
    )
