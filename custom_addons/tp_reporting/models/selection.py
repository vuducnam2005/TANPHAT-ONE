"""Explicit reporting pickers return identity labels, never arbitrary user records."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain


class ReportingPeople(models.AbstractModel):
    _name = 'tp.report.people'
    _description = 'Chọn nhân sự theo phạm vi Báo cáo'

    @api.model
    def get_options(self, purpose, model=False, resource_id=False, company_id=False, department_id=False, search=''):
        if purpose not in ('plan', 'directive', 'report_owner', 'configuration'):
            raise ValidationError(_('Mục đích chọn người không hợp lệ.'))
        if not self.env.user.has_group('tp_reporting.group_reporting_user'):
            raise AccessError(_('Bạn không có quyền dùng Trung tâm Báo cáo.'))
        for value in (resource_id, company_id, department_id):
            if value is not False and value is not None and (type(value) is not int or value <= 0):
                raise ValidationError(_('Định danh phạm vi không hợp lệ.'))
        allowed_models = {'plan': 'tp.report.plan', 'directive': 'tp.report.directive',
                          'report_owner': 'tp.report.document', 'configuration': False}
        if purpose != 'configuration' and model not in (False, allowed_models[purpose]):
            raise ValidationError(_('Loại hồ sơ không phù hợp bộ chọn người.'))
        if purpose == 'configuration' and model not in (False, 'tp.report.assignment', 'tp.report.schedule'):
            raise ValidationError(_('Cấu hình chỉ dùng bộ chọn assignment/lịch.'))
        record = self.env[model].browse(resource_id).exists() if model and resource_id else False
        if resource_id and not record:
            raise AccessError(_('Hồ sơ không còn trong phạm vi.'))
        if record:
            record.check_access('read')
            company_id, department_id = record.company_id.id, record.department_id.id
        company_id = company_id or self.env.company.id
        if company_id not in self.env.companies.ids:
            raise AccessError(_('Công ty không thuộc phiên hiện tại.'))
        if department_id:
            department = self.env['hr.department'].browse(department_id).exists()
            department.check_access('read')
            if not department or (department.company_id and department.company_id.id != company_id):
                raise AccessError(_('Phòng ban không thuộc công ty đã chọn.'))
        if not isinstance(search, str) or len(search) > 120:
            raise ValidationError(_('Nội dung tìm người không hợp lệ.'))
        if purpose == 'configuration':
            if not self.env.user.has_group('tp_reporting.group_reporting_config'):
                raise AccessError(_('Chỉ người cấu hình được chọn đối tượng assignment/lịch.'))
            scopes = [(department_id, False)]
        else:
            capability = {'plan': 'plan', 'directive': 'direct', 'report_owner': 'consolidate'}[purpose]
            if record:
                authority = record.document_id if purpose == 'directive' else record
                if purpose == 'report_owner' and record.level == 'personal':
                    return self._own_option(search)
                if not authority._has_capability(capability):
                    if purpose in ('plan', 'report_owner') and record.owner_id == self.env.user:
                        return self._own_option(search)
                    raise AccessError(_('Không được chọn người cho hồ sơ trong phạm vi này.'))
            today = fields.Date.context_today(self)
            assignments = self.env['tp.report.assignment'].search([
                ('user_id', '=', self.env.uid), ('capability', '=', capability),
                ('company_id', '=', company_id), ('active', '=', True), ('date_start', '<=', today),
                '|', ('date_end', '=', False), ('date_end', '>=', today),
            ])
            scopes = []
            for assignment in assignments:
                if department_id and assignment.department_id and assignment.department_id.id != department_id:
                    continue
                if purpose == 'report_owner' and record and assignment.level not in ('all', record.level):
                    continue
                scopes.append((department_id or assignment.department_id.id, assignment.subject_id.id))
            if not scopes:
                if purpose in ('plan', 'report_owner'):
                    return self._own_option(search)
                raise AccessError(_('Chưa có quyền giao chỉ đạo trong phạm vi đã chọn.'))
        parts = []
        for scope_department, subject in scopes:
            part = Domain.TRUE
            if scope_department:
                # Narrow HR elevation resolves IDs only; no HR fields cross the boundary.
                employee_ids = self.env['hr.employee'].sudo().search([
                    ('company_id', '=', company_id), ('active', '=', True),
                    ('current_version_id.department_id', '=', scope_department), ('user_id', '!=', False),
                ]).mapped('user_id').ids
                part &= Domain('id', 'in', employee_ids)
            if subject:
                part &= Domain('id', '=', subject)
            parts.append(part)
        user_domain = Domain.AND([
            [('active', '=', True), ('share', '=', False), ('company_ids', 'in', [company_id])],
            Domain.OR(parts), [('name', 'ilike', search.strip())] if search.strip() else Domain.TRUE,
        ])
        # Only the authorized identity subset is elevated; never expose login/contact/groups.
        users = self.env['res.users'].sudo().search_fetch(user_domain, ['name'], order='name,id', limit=100)
        return [{'id': user.id, 'display_name': user.name} for user in users]

    def _own_option(self, search):
        user = self.env.user
        return [{'id': user.id, 'display_name': user.name}] if not search.strip() or search.casefold() in user.name.casefold() else []
