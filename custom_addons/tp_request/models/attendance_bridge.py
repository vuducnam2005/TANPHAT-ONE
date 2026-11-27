# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""1-1 bridge between tp.hr.attendance.correction and tp.request (Section XI).

- tp.hr.attendance.correction remains the single authoritative source of truth for attendance
  corrections, period locks, anti-self-approval and live admin rules (DEC-061).
- Never creates a second duplicate correction record; never causes two-way write loops.
- Requests created from 'Công của tôi' appear immediately in 'Đề nghị & Phê duyệt', and
  requests created from 'Đề nghị & Phê duyệt' create/operate the exact same backend record.
"""
import base64

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from .request_common import (
    BRIDGE_INTERNAL,
    BRIDGE_KEY,
    INTERNAL,
    add_working_hours,
    format_date_vn,
    internal,
    is_bridge,
)

CORR_EVIDENCE_TAG = 'tp_att_corr_evidence'

CORR_TO_REQ_STATE = {
    'draft': 'draft',
    'submitted': 'pending',
    'withdrawn': 'withdrawn',
    'approved': 'approved',
    'returned': 'returned',
    'cancelled': 'withdrawn',
}


class AttendanceCorrectionBridge(models.Model):
    _inherit = 'tp.hr.attendance.correction'

    tp_request_id = fields.Many2one(
        'tp.request', string='Hồ sơ Yêu cầu phê duyệt', readonly=True, copy=False, ondelete='set null',
    )

    def _tp_bridge_request_type(self):
        rtype = self.env.ref('tp_request.type_attendance_correction', raise_if_not_found=False)
        if rtype:
            return rtype.sudo()
        return self.env['tp.request.type'].sudo().with_context(active_test=False).search(
            [('handler_kind', '=', 'attendance_correction')], limit=1,
        )

    def _tp_sync_to_request(self, action_event=None, note=''):
        """One-way authoritative projection from tp.hr.attendance.correction -> tp.request."""
        if is_bridge(self):
            return
        rtype = self._tp_bridge_request_type()
        if not rtype:
            return
        Request = self.env['tp.request'].sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL})
        Step = self.env['tp.request.step'].sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL})

        for corr in self.sudo():
            emp = corr.employee_id
            owner_user = emp.user_id if emp else self.env.user
            if not owner_user:
                continue
            target_state = CORR_TO_REQ_STATE.get(corr.state, 'draft')
            reviewers = corr.reviewer_user_ids
            if corr.state == 'submitted' and not reviewers:
                reviewers = self._tp_reviewers_for(corr.company_id, corr.department_id, owner_user)

            req = corr.tp_request_id or Request.search([('attendance_correction_id', '=', corr.id)], limit=1)
            if req:
                req = req.sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL})
            default_title = _('Điều chỉnh công ngày %(day)s (%(code)s)',
                              day=format_date_vn(corr.work_date) or '—', code=corr.name or 'Mới')
            due = add_working_hours(corr.submitted_at or fields.Datetime.now(), rtype.sla_hours or 24.0) if target_state == 'pending' else False

            vals = {
                'type_id': rtype.id,
                'company_id': corr.company_id.id,
                'requester_user_id': owner_user.id,
                'requester_employee_id': emp.id if emp else False,
                'department_id': corr.department_id.id or (emp.department_id.id if emp and emp.department_id else False),
                'requester_name_snap': corr.employee_name or (emp.name if emp else owner_user.name),
                'requester_code_snap': corr.employee_code or (emp.tp_employee_code if emp else ''),
                'department_name_snap': corr.department_id.name if corr.department_id else '',
                'description': corr.reason or False,
                'approval_state': target_state,
                'execution_state': 'not_applicable',
                'version': corr.version or 1,
                'submitted_at': corr.submitted_at or False,
                'approved_at': corr.reviewed_at if target_state == 'approved' else False,
                'due_at': due,
                'return_reason': corr.review_note if target_state == 'returned' else False,
                'withdraw_reason': corr.withdraw_reason if corr.state == 'withdrawn' else False,
                'attendance_correction_id': corr.id,
                'att_work_date': corr.work_date,
                'att_requested_in': corr.requested_in,
                'att_requested_out': corr.requested_out,
                'att_current_in': corr.current_in or False,
                'att_current_out': corr.current_out or False,
                'current_approver_ids': [Command.set(reviewers.ids)] if target_state == 'pending' else [Command.clear()],
            }
            if req:
                old_state = req.approval_state
                all_ids = set(req.all_approver_ids.ids) | set(reviewers.ids)
                if corr.reviewer_id:
                    all_ids.add(corr.reviewer_id.id)
                vals['all_approver_ids'] = [Command.set(sorted(all_ids))]
                # Keep custom title if user entered one in Request; refresh default title if still default
                if not req.title or req.title.startswith('Điều chỉnh công ngày '):
                    vals['title'] = default_title
                req.write(vals)
            else:
                old_state = ''
                vals['title'] = default_title
                vals['all_approver_ids'] = [Command.set(reviewers.ids)]
                req = Request.create(vals)
                self.env.cr.execute(
                    'UPDATE tp_hr_attendance_correction SET tp_request_id=%s WHERE id=%s',
                    [req.id, corr.id],
                )
                corr.invalidate_recordset(['tp_request_id'])

            self._tp_sync_evidence_to_request(corr, req, owner_user)

            # Sync single authoritative admin approval step snapshot
            step = req.step_ids.filtered(lambda s: s.request_version == (corr.version or 1))[:1]
            if target_state == 'pending':
                prev_open = req.step_ids.filtered(lambda s: s.state in ('waiting', 'pending') and s != step)
                if prev_open:
                    prev_open.sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL}).write({'state': 'skipped'})
                if not step:
                    step = Step.create({
                        'request_id': req.id,
                        'sequence': 10,
                        'name': _('Quản trị hệ thống phê duyệt'),
                        'approver_rule': 'admin_group',
                        'approval_policy': 'any_one',
                        'eligible_user_ids': [Command.set(reviewers.ids)],
                        'state': 'pending',
                        'sla_hours': rtype.sla_hours or 24.0,
                        'due_at': due,
                        'request_version': corr.version or 1,
                        'can_return': True,
                        'can_reject': False,
                    })
                else:
                    step.sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL}).write({'eligible_user_ids': [Command.set(reviewers.ids)], 'state': 'pending', 'due_at': due})
                req.write({'current_step_id': step.id})
            elif target_state in ('approved', 'returned', 'withdrawn'):
                open_step = req.current_step_id or req.step_ids.filtered(lambda s: s.state == 'pending')[:1]
                if open_step:
                    mapped = {'approved': 'approved', 'returned': 'returned', 'withdrawn': 'skipped'}[target_state]
                    open_step.sudo().with_context(**{BRIDGE_KEY: BRIDGE_INTERNAL}).write({
                        'state': mapped,
                        'decided_by_id': corr.reviewer_id.id if target_state in ('approved', 'returned') else False,
                        'decided_at': corr.reviewed_at if target_state in ('approved', 'returned') else False,
                        'decision_note': corr.review_note if target_state in ('approved', 'returned') else False,
                    })
                req.write({'current_step_id': False})

            # History & internal notification on actual transitions
            if action_event:
                req._tp_record_history(
                    action_event,
                    state_before=old_state,
                    state_after=target_state,
                    step_name=_('Quản trị hệ thống phê duyệt') if action_event in ('approve_final', 'return', 'submit', 'resubmit') else '',
                    note=note or corr.review_note or '',
                    result_ref=corr.name,
                )
                if action_event in ('submit', 'resubmit') and reviewers:
                    req._tp_notify_internal(
                        reviewers,
                        _('Đề nghị điều chỉnh công cần duyệt'),
                        _('%(emp)s gửi đề nghị điều chỉnh công ngày %(day)s.',
                          emp=corr.employee_name, day=format_date_vn(corr.work_date)),
                        event_type='pending_approval',
                    )
                elif action_event == 'approve_final':
                    req._tp_notify_internal(
                        owner_user,
                        _('Đề nghị điều chỉnh công đã được duyệt'),
                        _('%(actor)s đã duyệt %(code)s và cập nhật giờ vào/ra vào bảng công.',
                          actor=self.env.user.name, code=corr.name),
                        event_type='approved',
                    )
                elif action_event == 'return':
                    req._tp_notify_internal(
                        owner_user,
                        _('Đề nghị điều chỉnh công bị trả lại'),
                        _('%(actor)s đã trả lại %(code)s. Lý do: %(note)s',
                          actor=self.env.user.name, code=corr.name, note=corr.review_note or ''),
                        event_type='returned',
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._tp_sync_to_request(action_event='create')
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('_tp_attendance_internal'):
            self._tp_sync_to_request()
        return res

    def action_submit(self):
        before = {r.id: r.state for r in self}
        res = super().action_submit()
        for rec in self:
            ev = 'resubmit' if before.get(rec.id) == 'returned' else 'submit'
            rec._tp_sync_to_request(action_event=ev)
        return res

    def action_approve(self, note=None):
        res = super().action_approve(note=note)
        self._tp_sync_to_request(action_event='approve_final', note=note or '')
        return res

    def action_return(self, note=None):
        res = super().action_return(note=note)
        self._tp_sync_to_request(action_event='return', note=note or '')
        return res

    def action_withdraw(self, reason=None):
        res = super().action_withdraw(reason=reason)
        self._tp_sync_to_request(action_event='withdraw', note=(reason or '').strip())
        return res

    def action_reopen_draft(self):
        res = super().action_reopen_draft()
        self._tp_sync_to_request(
            action_event='reopen_draft',
            note=_('Mở lại bản nháp điều chỉnh công để chỉnh sửa.'),
        )
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._tp_sync_to_request(action_event='withdraw')
        return res

    def _tp_sync_reviewers(self):
        res = super()._tp_sync_reviewers()
        self._tp_sync_to_request()
        return res

    def _tp_sync_evidence_to_request(self, corr, req, owner_user):
        """Idempotently mirror corr.evidence_file <-> req.attachment_ids without duplicating files."""
        if self.env.context.get('_tp_skip_evidence_mirror'):
            return
        Attachment = self.env['ir.attachment'].sudo()
        src_att = Attachment.search([
            ('res_model', '=', 'tp.hr.attendance.correction'),
            ('res_id', '=', corr.id),
            ('res_field', '=', 'evidence_file'),
        ], order='id desc', limit=1)
        mirrored = req.attachment_ids.sudo().filtered(
            lambda a: a.res_model == 'tp.request' and a.res_id == req.id and a.description == CORR_EVIDENCE_TAG,
        )
        if src_att:
            raw_obj = src_att.raw
            raw_bytes = raw_obj.content if hasattr(raw_obj, 'content') else (raw_obj or b'')
            if raw_bytes:
                fname = (corr.evidence_name or src_att.name or f'minh_chung_{corr.name or corr.id}').strip()
                mime = src_att.mimetype or 'application/octet-stream'
                same_cs = req.attachment_ids.sudo().filtered(
                    lambda a: a.res_model == 'tp.request' and a.res_id == req.id and a.checksum == src_att.checksum,
                )[:1]
                if same_cs:
                    upd_att = {}
                    if same_cs.description != CORR_EVIDENCE_TAG:
                        upd_att['description'] = CORR_EVIDENCE_TAG
                    if fname and same_cs.name != fname:
                        upd_att['name'] = fname
                    if upd_att:
                        same_cs.write(upd_att)
                    stale = mirrored - same_cs
                    if stale:
                        req.write({'attachment_ids': [Command.unlink(a.id) for a in stale]})
                        stale.unlink()
                elif mirrored:
                    keep = mirrored[:1]
                    keep.write({
                        'name': fname,
                        'raw': raw_bytes,
                        'mimetype': mime,
                        'description': CORR_EVIDENCE_TAG,
                    })
                    extra = mirrored - keep
                    if extra:
                        req.write({'attachment_ids': [Command.unlink(a.id) for a in extra]})
                        extra.unlink()
                else:
                    new_att = self.env['ir.attachment'].with_user(owner_user).sudo().create({
                        'name': fname,
                        'raw': raw_bytes,
                        'mimetype': mime,
                        'res_model': 'tp.request',
                        'res_id': req.id,
                        'description': CORR_EVIDENCE_TAG,
                        'public': False,
                        'access_token': False,
                    })
                    req.write({'attachment_ids': [Command.link(new_att.id)]})
                return
        if mirrored and corr.state in ('draft', 'returned'):
            req.write({'attachment_ids': [Command.unlink(a.id) for a in mirrored]})
            mirrored.unlink()

    def unlink(self):
        linked_reqs = self.sudo().mapped('tp_request_id')
        res = super().unlink()
        if linked_reqs:
            internal(linked_reqs).with_context(_tp_request_cascade_draft=INTERNAL).unlink()
        return res


class TpRequestAttendanceHelper(models.Model):
    _inherit = 'tp.request'

    @api.model
    def _tp_save_attendance_request(self, rec, rtype, payload, att_in, att_out, submit=False):
        """Create or update the authoritative tp.hr.attendance.correction record and return its 1-1 tp.request."""
        Correction = self.env['tp.hr.attendance.correction']
        corr_vals = {
            'work_date': payload.get('att_work_date'),
            'requested_in': att_in,
            'requested_out': att_out,
            'reason': (payload.get('description') or '').strip() or False,
        }
        att_ids = [int(x) for x in (payload.get('attachment_ids') or []) if str(x).isdigit()]
        valid_atts = self.env['ir.attachment'].sudo().browse()
        if att_ids:
            for att in self.env['ir.attachment'].sudo().browse(att_ids).exists():
                if att.create_uid.id == self.env.uid and (
                    (rec and att.res_model == 'tp.request' and att.res_id == rec.id) or not att.res_model
                ):
                    valid_atts |= att
        if valid_atts:
            first_att = valid_atts[0]
            raw_obj = first_att.raw
            raw_bytes = raw_obj.content if hasattr(raw_obj, 'content') else (raw_obj or b'')
            if raw_bytes:
                corr_vals['evidence_file'] = base64.b64encode(raw_bytes).decode('ascii')
                corr_vals['evidence_name'] = first_att.name or 'minh_chung'

        CorrectionCtx = Correction.with_context(_tp_skip_evidence_mirror=True) if valid_atts else Correction
        if rec and rec.attendance_correction_id:
            corr = rec.attendance_correction_id.with_context(_tp_skip_evidence_mirror=bool(valid_atts))
            corr.write(corr_vals)
        else:
            corr = CorrectionCtx.create(corr_vals)
            rec = corr.sudo().tp_request_id
            if not rec:
                corr._tp_sync_to_request(action_event='create')
                rec = corr.sudo().tp_request_id

        if valid_atts and rec:
            stale_mirrored = rec.sudo().attachment_ids.filtered(
                lambda a: a.res_model == 'tp.request' and a.res_id == rec.id and a.description == CORR_EVIDENCE_TAG and a not in valid_atts,
            )
            if stale_mirrored:
                internal(rec).write({'attachment_ids': [Command.unlink(a.id) for a in stale_mirrored]})
                stale_mirrored.unlink()
            for idx, att in enumerate(valid_atts):
                att_upd = {
                    'res_model': 'tp.request',
                    'res_id': rec.id,
                    'public': False,
                    'access_token': False,
                }
                if idx == 0:
                    att_upd['description'] = CORR_EVIDENCE_TAG
                att.sudo().write(att_upd)
            internal(rec).write({'attachment_ids': [Command.link(a.id) for a in valid_atts]})

        # Preserve user's custom title & priority on the linked tp.request
        title = (payload.get('title') or '').strip()
        upd = {}
        if title:
            upd['title'] = title
        if payload.get('priority'):
            upd['priority'] = payload['priority']
        if upd and rec:
            internal(rec).write(upd)
        if submit:
            corr.with_context(_tp_skip_evidence_mirror=False).action_submit()
        if not rec:
            raise UserError(_('Không khởi tạo được hồ sơ đề nghị điều chỉnh công.'))
        return self.browse(rec.id)
