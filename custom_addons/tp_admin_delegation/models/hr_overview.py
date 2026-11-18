"""Delegated HR overview: one row scope, a whitelisted projection, no HR group."""
from odoo import api, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain

DELEGATED_LABEL = ('Quản trị được ủy quyền: chỉ hồ sơ của phòng khác trong công ty đang xem. '
                   'Phòng của bạn giữ quyền nghiệp vụ như cũ.')
# Business metadata already shown by the overview, drill-down and XLSX. Private
# identity, personal/mobile contact, address, bank, contract, salary and document fields stay closed.
PROJECTION_FIELDS = frozenset({
    'id', 'active', 'department_id', 'job_id', 'user_id', 'tp_employee_code', 'tp_source_title',
    'tp_employment_kind', 'tp_account_status', 'work_email', 'work_phone',
})
MISSING_WORK_CONTACT_DOMAIN = [('work_email', '=', False), ('work_phone', '=', False)]
OPERATORS = frozenset({'=', '!=', 'in', 'not in'})


def _scalar(value):
    return value is None or isinstance(value, bool | int) or (isinstance(value, str) and len(value) <= 254)


class DelegatedHrWorkspace(models.AbstractModel):
    _inherit = 'tp.hr.workspace'

    @api.model
    def _tp_delegated_hr(self):
        user = self.env.user
        return not user.has_group('hr.group_hr_user') and user._tp_has_admin_delegation(self.env.company)

    @api.model
    def _tp_population_source(self):
        if not self._tp_delegated_hr():
            return super()._tp_population_source()
        company = self.env.company
        own, complete = self.env.user._tp_delegation_scope(company)
        if not complete:
            raise AccessError(self.env._('Chưa xác định đủ phòng của bạn nên chưa mở tổng quan nhân sự được ủy quyền.'))
        employees = self.env['hr.employee'].with_context(active_test=False)
        employees.check_access('read')
        # Rows are chosen with the caller's own access and an explicit outside
        # department; unknown or own departments stay out. Only these rows are
        # then counted for the whitelisted fields below.
        ids = employees.search(Domain.AND([
            Domain('company_id', '=', company.id), Domain('department_id', '!=', False),
            Domain('department_id', 'not in', own.ids), Domain('department_id.company_id', '=', company.id),
        ])).ids
        return employees.sudo(), [('id', 'in', ids)]

    @api.model
    def _tp_projection_domain(self, domain):
        if not isinstance(domain, list):
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
        result = []
        for item in domain:
            if item in ('&', '|', '!'):
                result.append(item)
                continue
            if not isinstance(item, list | tuple) or len(item) != 3:
                raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
            field, operator, value = item
            valid = (_scalar(value) if operator in ('=', '!=') else
                     isinstance(value, list | tuple) and len(value) <= 1000 and all(_scalar(part) for part in value))
            if field not in PROJECTION_FIELDS or operator not in OPERATORS or not valid:
                raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
            result.append((field, operator, list(value) if isinstance(value, list | tuple) else value))
        try:
            Domain(result)  # well-formed prefix notation
        except ValueError as exc:
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.')) from exc
        return result

    @api.model
    def _tp_action_domain(self, employees, domain, extra_domain):
        if not self._tp_delegated_hr():
            return super()._tp_action_domain(employees, domain, extra_domain)
        # The native list runs with the caller's own access; give it the exact
        # rows counted above instead of a domain on HR-only fields.
        return [('id', 'in', employees.search(domain + self._tp_projection_domain(extra_domain or [])).ids)]

    @api.model
    def get_overview(self, filters=None):
        result = super().get_overview(filters)
        if self._tp_delegated_hr():
            employees, domain, _status = self._population(filters)
            own = self.env.user._tp_delegation_scope(self.env.company)[0]
            result['catalog_departments'] = [row for row in result['catalog_departments'] if row['id'] not in own.ids]
            result.update(
                can_create=False,
                delegated_scope=DELEGATED_LABEL,
                missing_contact=employees.search_count(domain + MISSING_WORK_CONTACT_DOMAIN),
                missing_contact_domain=MISSING_WORK_CONTACT_DOMAIN,
            )
        return result
