# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""J1: Recruitment Requisition, Applicant Pipeline, Interview Link & Controlled Applicant->Employee Onboarding (Cases #15 & #18)."""
from datetime import datetime

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import (
    fold_text,
    format_date_vn,
    format_dt_local,
    is_live_admin_user,
)


def _is_recruitment_officer(env, company=None):
    user = env.user
    company = company or env.company
    if is_live_admin_user(user, company=company):
        return True
    return bool(
        user.has_group('hr_recruitment.group_hr_recruitment_user')
        or user.has_group('hr.group_hr_manager')
        or user.has_group('tp_hr_workspace.group_tp_hr_manager')
    )


class TpRecruitmentRequisition(models.Model):
    _name = 'tp.recruitment.requisition'
    _description = 'Đề xuất nhu cầu tuyển dụng phòng ban'
    _inherit = ['mail.thread']
    _order = 'id desc'

    code = fields.Char(string='Mã nhu cầu', required=True, copy=False, readonly=True, default='Mới', index=True)
    name = fields.Char(string='Vị trí đề xuất tuyển', required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban đề xuất', required=True, index=True)
    job_id = fields.Many2one('hr.job', string='Chức danh tuyển dụng')
    requester_user_id = fields.Many2one('res.users', default=lambda s: s.env.user, required=True)
    headcount_requested = fields.Integer(string='Số lượng cần tuyển', required=True, default=1)
    expected_date = fields.Date(string='Thời điểm cần nhân sự')
    requirements_note = fields.Text(string='Yêu cầu chuyên môn / chứng chỉ hành nghề')
    state = fields.Selection(
        [
            ('draft', 'Nháp'),
            ('submitted', 'Chờ phê duyệt'),
            ('approved', 'Đang tuyển dụng'),
            ('closed', 'Đã đóng'),
        ],
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )
    applicant_ids = fields.One2many('hr.applicant', 'tp_requisition_id', string='Hồ sơ ứng viên')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == 'Mới':
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('tp.recruitment.requisition') or 'TD-0001'
        return super().create(vals_list)

    def action_approve_requisition(self):
        for rec in self:
            if not is_live_admin_user(self.env.user, company=rec.company_id) and not self.env.user.has_group('hr.group_hr_manager'):
                raise AccessError(_('Chỉ Ban Giám đốc hoặc Trưởng phòng Nhân sự mới phê duyệt nhu cầu tuyển dụng.'))
            rec.write({'state': 'approved'})
        return True


class HrApplicantEnterprise(models.Model):
    _inherit = 'hr.applicant'

    tp_requisition_id = fields.Many2one('tp.recruitment.requisition', string='Theo nhu cầu tuyển', ondelete='set null', index=True)
    tp_national_id = fields.Char(string='Số CCCD / Định danh (kiểm trùng)', index=True)
    tp_interview_event_id = fields.Many2one('calendar.event', string='Lịch phỏng vấn', ondelete='set null')
    tp_evaluation_ids = fields.One2many('tp.applicant.evaluation', 'applicant_id', string='Phiếu đánh giá phỏng vấn')
    tp_offer_note = fields.Text(string='Thông tin đề nghị tiếp nhận (Offer)')

    def write(self, vals):
        # Mandatory Case #15: Dragging/changing stage_id NEVER auto-creates hr.employee or res.users!
        return super().write(vals)

    @api.model
    def tp_create_applicant(self, payload):
        if not _is_recruitment_officer(self.env):
            raise AccessError(_('Bạn không có quyền thêm hồ sơ ứng viên.'))
        payload = payload or {}
        name = (payload.get('partner_name') or '').strip()
        if not name:
            raise UserError(_('Vui lòng nhập Họ và tên ứng viên.'))
        first_stage = payload.get('stage_id') or self.env['hr.recruitment.stage'].sudo().search([], order='sequence, id', limit=1).id
        app = self.sudo().create({
            'partner_name': name,
            'email_from': (payload.get('email_from') or '').strip() or False,
            'partner_phone': (payload.get('partner_phone') or '').strip() or False,
            'tp_national_id': (payload.get('tp_national_id') or '').strip() or False,
            'department_id': int(payload['department_id']) if int(payload.get('department_id') or 0) > 0 else False,
            'job_id': int(payload['job_id']) if int(payload.get('job_id') or 0) > 0 else False,
            'stage_id': int(first_stage) if first_stage else False,
            'company_id': self.env.company.id,
        })
        return {'id': app.id, 'name': app.partner_name}

    @api.model
    def tp_move_applicant_stage(self, applicant_id, stage_id):
        if not _is_recruitment_officer(self.env):
            raise AccessError(_('Bạn không có quyền chuyển vòng tuyển dụng.'))
        app = self.sudo().browse(int(applicant_id or 0)).exists()
        if not app:
            raise UserError(_('Không tìm thấy ứng viên.'))
        # Stage move NEVER auto-creates hr.employee!
        app.write({'stage_id': int(stage_id)})
        return {'id': app.id, 'stage_id': app.stage_id.id, 'employee_id': app.employee_id.id or 0}

    @api.model
    def tp_schedule_interview(self, applicant_id, start_iso, stop_iso, interviewer_user_ids=None):
        if not _is_recruitment_officer(self.env):
            raise AccessError(_('Bạn không có quyền lập lịch phỏng vấn tuyển dụng.'))
        app = self.sudo().browse(int(applicant_id or 0)).exists()
        if not app:
            raise UserError(_('Không tìm thấy hồ sơ ứng viên.'))
        dt_start = datetime.fromisoformat(start_iso.replace('Z', ''))
        dt_stop = datetime.fromisoformat(stop_iso.replace('Z', ''))
        if dt_stop <= dt_start:
            raise UserError(_('Giờ kết thúc phỏng vấn phải sau giờ bắt đầu.'))

        uids = [int(x) for x in (interviewer_user_ids or []) if int(x or 0) > 0] or [self.env.uid]
        partners = self.env['res.users'].sudo().browse(uids).mapped('partner_id')
        ev_vals = {
            'name': f'Phỏng vấn ứng viên: {app.partner_name or "Ứng viên"}',
            'start': dt_start,
            'stop': dt_stop,
            'partner_ids': [Command.set(partners.ids)],
        }
        Ev = self.env['calendar.event'].with_user(self.env.user)
        if 'tp_event_kind' in Ev._fields:
            ev_vals['tp_event_kind'] = 'meeting'
        ev = Ev.create(ev_vals)
        app.write({'tp_interview_event_id': ev.id})
        return {'event_id': ev.id, 'name': ev.name}

    @api.model
    def tp_hire_applicant_to_employee(self, applicant_id, confirm_hire=False, department_id=0, job_id=0):
        """Controlled onboarding wizard: checks duplicate CCCD/email/phone, creates ONLY hr.employee, NEVER res.users or admin!

        Mandatory Cases #15 & #18:
        - Never triggered on stage drag; requires confirm_hire=True.
        - Rejects duplicate CCCD / work_email / mobile_phone against existing hr.employee.
        - Never creates res.users and never grants admin groups.
        """
        if not _is_recruitment_officer(self.env):
            raise AccessError(_('Chỉ Quản trị Nhân sự hoặc Admin mới được chuyển ứng viên trúng tuyển sang Hồ sơ nhân viên.'))
        if not confirm_hire:
            raise UserError(_('Vui lòng xác nhận tường minh thao tác Tiếp nhận nhân sự trước khi tạo hồ sơ nhân viên.'))

        app = self.sudo().browse(int(applicant_id or 0)).exists()
        if not app:
            raise UserError(_('Không tìm thấy hồ sơ ứng viên.'))
        if app.employee_id:
            return {'employee_id': app.employee_id.id, 'already_hired': True}

        cand_name = (app.partner_name or '').strip()
        if not cand_name:
            raise UserError(_('Ứng viên cần có Họ và tên đầy đủ trước khi lập hồ sơ nhân viên.'))

        Emp = self.env['hr.employee'].sudo().with_context(active_test=False)
        company = app.company_id or self.env.company

        # Duplicate identity check (CCCD, email, phone)
        cccd = (app.tp_national_id or '').strip()
        if cccd and 'identification_id' in Emp._fields:
            dup_id = Emp.search([('company_id', '=', company.id), ('identification_id', '=', cccd)], limit=1)
            if dup_id:
                raise UserError(_('Trùng số CCCD/Định danh (%s) với hồ sơ nhân viên hiện có: %s.') % (cccd, dup_id.name))

        email = (app.email_from or '').strip().lower()
        if email:
            dup_mail = Emp.search([('company_id', '=', company.id), ('work_email', '=ilike', email)], limit=1)
            if dup_mail:
                raise UserError(_('Trùng email (%s) với hồ sơ nhân viên hiện có: %s.') % (email, dup_mail.name))

        phone = (app.partner_phone or '').strip()
        if phone:
            dup_phone = Emp.search([
                ('company_id', '=', company.id),
                '|', ('work_phone', '=', phone), ('mobile_phone', '=', phone),
            ], limit=1)
            if dup_phone:
                raise UserError(_('Trùng số điện thoại (%s) với hồ sơ nhân viên hiện có: %s.') % (phone, dup_phone.name))

        target_dept = int(department_id or 0) or app.department_id.id or app.tp_requisition_id.department_id.id or False
        target_job = int(job_id or 0) or app.job_id.id or app.tp_requisition_id.job_id.id or False

        emp_vals = {
            'name': cand_name,
            'company_id': company.id,
            'department_id': target_dept,
            'job_id': target_job,
            'work_email': email or False,
            'mobile_phone': phone or False,
            'date_version': fields.Date.context_today(self),
            'user_id': False,  # NEVER auto-create or link res.users during recruitment onboarding!
        }
        if cccd and 'identification_id' in Emp._fields:
            emp_vals['identification_id'] = cccd

        new_emp = self.env['hr.employee'].with_user(self.env.user).sudo().create(emp_vals)
        app.write({'employee_id': new_emp.id})
        return {
            'employee_id': new_emp.id,
            'employee_code': getattr(new_emp, 'tp_employee_code', '') or '',
            'user_created': False,
            'already_hired': False,
        }

    @api.model
    def tp_recruitment_workspace_data(self, params=None):
        if not _is_recruitment_officer(self.env):
            raise AccessError(_('Phân hệ Tuyển dụng chỉ dành cho bộ phận Nhân sự và Ban Giám đốc.'))
        params = params or {}
        company = self.env.company

        stages = self.env['hr.recruitment.stage'].sudo().search([], order='sequence asc, id asc')
        dom = [('company_id', 'in', [company.id, False])]
        dept_id = int(params.get('department_id') or 0)
        if dept_id > 0:
            dom.append(('department_id', '=', dept_id))
        stage_id = int(params.get('stage_id') or 0)
        if stage_id > 0:
            dom.append(('stage_id', '=', stage_id))

        apps = self.sudo().search(dom, order='sequence asc, id desc', limit=200)
        q = (params.get('search') or '').strip()
        if q:
            needle = fold_text(q)
            apps = apps.filtered(lambda a: any(needle in fold_text(v) for v in (a.partner_name, a.email_from, a.partner_phone)))

        cards = [{
            'id': a.id,
            'name': a.partner_name or 'Ứng viên chưa đặt tên',
            'email': a.email_from or '',
            'phone': a.partner_phone or '',
            'national_id': a.tp_national_id or '',
            'job_name': a.job_id.name if a.job_id else 'Chưa gán vị trí',
            'department_name': a.department_id.name if a.department_id else '—',
            'stage_id': a.stage_id.id,
            'stage_name': a.stage_id.name if a.stage_id else 'Mới',
            'employee_id': a.employee_id.id or 0,
            'interview_event_name': a.tp_interview_event_id.name if a.tp_interview_event_id else '',
            'eval_count': len(a.tp_evaluation_ids),
            'created_at': format_dt_local(a.create_date),
        } for a in apps]

        reqs = self.env['tp.recruitment.requisition'].sudo().search([('company_id', '=', company.id)], limit=50)
        depts = self.env['hr.department'].sudo().search([('company_id', '=', company.id)], order='name')
        jobs = self.env['hr.job'].sudo().search([('company_id', 'in', [company.id, False])], order='name')

        return {
            'stages': [{'id': s.id, 'name': s.name} for s in stages],
            'applicants': cards,
            'total_applicants': len(cards),
            'requisitions': [{
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'department_name': r.department_id.name,
                'headcount': r.headcount_requested,
                'state': r.state,
                'state_label': dict(r._fields['state'].selection).get(r.state, r.state),
                'expected_date': format_date_vn(r.expected_date),
            } for r in reqs],
            'departments': [{'id': d.id, 'name': d.name} for d in depts],
            'jobs': [{'id': j.id, 'name': j.name} for j in jobs],
        }


class TpApplicantEvaluation(models.Model):
    _name = 'tp.applicant.evaluation'
    _description = 'Phiếu đánh giá phỏng vấn ứng viên (bảo mật nội bộ tuyển dụng)'
    _order = 'create_date desc, id desc'

    applicant_id = fields.Many2one('hr.applicant', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='applicant_id.company_id', store=True, index=True)
    interviewer_user_id = fields.Many2one('res.users', required=True, default=lambda s: s.env.user, index=True)
    score_technical = fields.Integer(string='Điểm chuyên môn (1-10)', default=8)
    score_culture = fields.Integer(string='Điểm tác phong / phối hợp (1-10)', default=8)
    recommendation = fields.Selection(
        [('hire', 'Đề nghị tuyển'), ('consider', 'Cân nhắc thêm'), ('reject', 'Không phù hợp')],
        required=True,
        default='hire',
    )
    comment = fields.Text(string='Nhận xét hội đồng phỏng vấn', required=True)
