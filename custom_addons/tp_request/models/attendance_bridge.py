# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""1-1 bridge between tp.hr.attendance.correction and tp.request (Section XI).

- tp.hr.attendance.correction remains the single authoritative source of truth for attendance
  corrections, period locks, anti-self-approval and live admin rules (DEC-061).
- Never creates a second duplicate correction record; never causes two-way write loops.
- Requests created from 'Công của tôi' appear immediately in 'Đề nghị & Phê duyệt', and
  requests created from 'Đề nghị & Phê duyệt' create/operate the exact same backend record.
"""
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from .request_common import (
    BRIDGE_INTERNAL,
    BRIDGE_KEY,
    add_working_hours,
    format_date_vn,
    internal,
    is_bridge,
)

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
        'tp.request', string='Hồ sơ Đề nghị & Phê duyệt', readonly=True, copy=False, ondelete='set null',
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
        self._tp_sync_to_request()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._tp_sync_to_request(action_event='withdraw')
        return res

    def _tp_sync_reviewers(self):
        res = super()._tp_sync_reviewers()
        self._tp_sync_to_request()
        return res

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
        if rec and rec.attendance_correction_id:
            corr = rec.attendance_correction_id
            corr.write(corr_vals)
        else:
            corr = Correction.create(corr_vals)
            rec = corr.sudo().tp_request_id
            if not rec:
                corr._tp_sync_to_request(action_event='create')
                rec = corr.sudo().tp_request_id
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
            corr.action_submit()
        if not rec:
            raise UserError(_('Không khởi tạo được hồ sơ đề nghị điều chỉnh công.'))
        return self.browse(rec.id)
