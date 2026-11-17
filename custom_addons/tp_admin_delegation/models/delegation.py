"""Live, separate administrative authority. Never provision business groups."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain

from odoo.addons.base.models.res_users import check_identity

_LEDGER = object()
LOCK_NAMESPACE = 761118


class DelegationUser(models.Model):
    _inherit = 'res.users'

    tp_admin_scope_revision = fields.Integer(default=0, readonly=True, copy=False)

    def _tp_is_main_admin(self):
        self.ensure_one()
        return bool(self.active and not self.share and self.has_group('base.group_system'))

    def _tp_admin_lock(self, exclusive=False):
        """Hold authority until transaction end; revoke and scope changes serialize."""
        self.ensure_one()
        function = 'pg_advisory_xact_lock' if exclusive else 'pg_advisory_xact_lock_shared'
        self.env.cr.execute(f'SELECT {function}(%s, %s)', [LOCK_NAMESPACE, self.id])
        if exclusive:
            self.env.cr.execute('UPDATE res_users SET tp_admin_scope_revision=COALESCE(tp_admin_scope_revision, 0)+1 WHERE id=%s', [self.id])
        # A changed row in a stale REPEATABLE READ transaction raises a serialization
        # failure here; Odoo retries the request instead of using stale authority.
        self.env.cr.execute(
            'SELECT id FROM tp_admin_delegation WHERE user_id=%s ORDER BY id FOR SHARE', [self.id])
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR SHARE', [self.id])
        self.invalidate_recordset(['active', 'share', 'company_ids'])

    def _tp_has_admin_delegation(self, company=None, lock=False):
        self.ensure_one()
        if lock:
            self._tp_admin_lock()
        if not self.active or self.share or self._tp_is_main_admin():
            return False
        companies = self.company_ids & self.env.companies
        if company:
            companies &= company
        if not companies:
            return False
        self.env.cr.execute(
            "SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND company_id IN %s AND state='active' LIMIT 1",
            [self.id, tuple(companies.ids)])
        return bool(self.env.cr.fetchone())

    def _tp_delegation_scope(self, company):
        """Every effective work responsibility counts, including alternate identities."""
        self.ensure_one()
        departments = self.env['hr.department'].sudo().browse()
        complete = True
        employees = self.env['hr.employee'].sudo().with_context(active_test=False, version_id=False).search([
            ('user_id', '=', self.id), ('company_id', '=', company.id),
        ])
        for employee in employees:
            version = employee._get_version()
            department = version.department_id
            if not department or department.company_id != company:
                complete = False
            departments |= department
        today = fields.Date.context_today(self)
        roles = self.env['tp.kd.department.role'].sudo().search([
            ('user_id', '=', self.id), ('company_id', '=', company.id), ('active', '=', True),
            ('date_start', '<=', today), '|', ('date_end', '=', False), ('date_end', '>=', today),
        ])
        departments |= roles.department_id
        for model in ('tp.project.assignment', 'tp.project.grant', 'tp.kd.grant'):
            domain = [('user_id', '=', self.id), ('company_id', '=', company.id), ('active', '=', True)]
            if 'date_end' in self.env[model]._fields:
                domain += ['|', ('date_end', '=', False), ('date_end', '>=', today)]
            for responsibility in self.env[model].sudo().search(domain):
                project_department = responsibility.project_id.tp_department_id
                explicit = (responsibility.department_id if 'department_id' in responsibility._fields
                            else self.env['hr.department'])
                sources = project_department | explicit
                complete &= bool(project_department and all(dept.company_id == company for dept in sources))
                departments |= sources
        members = self.env['crm.team.member'].sudo().search([
            ('user_id', '=', self.id), ('crm_team_id.company_id', 'in', [False, company.id]), ('active', '=', True),
        ])
        for member in members:
            department = member.crm_team_id.kd_department_id
            complete &= bool(department and department.company_id == company)
            departments |= department
        for team in self.env['crm.team'].sudo().search([
                ('user_id', '=', self.id), ('company_id', 'in', [False, company.id]), ('active', '=', True)]):
            department = team.kd_department_id
            complete &= bool(department and department.company_id == company)
            departments |= department
        reporting = self.env['tp.report.assignment'].sudo().search([
            ('user_id', '=', self.id), ('company_id', '=', company.id), ('active', '=', True),
            ('date_start', '<=', today), '|', ('date_end', '=', False), ('date_end', '>=', today),
        ])
        for responsibility in reporting:
            department = responsibility.department_id
            # A companywide/subject-only responsibility does not identify an outside
            # department reliably; keep all added authority closed for this company.
            complete &= bool(department and department.company_id == company)
            departments |= department
        return departments, bool(complete and departments)

    def _tp_delegation_departments(self, company=None):
        self.ensure_one()
        departments = self.env['hr.department'].sudo().browse()
        for current in (company or (self.company_ids & self.env.companies)):
            departments |= self._tp_delegation_scope(current)[0]
        return departments

    def _tp_delegated_other_department(self, company, departments, lock=False):
        self.ensure_one()
        if not company or len(company) != 1 or not departments:
            return False
        if not self._tp_has_admin_delegation(company, lock=lock):
            return False
        own, complete = self._tp_delegation_scope(company)
        return bool(complete and not (own & departments)
                    and all(department.company_id == company for department in departments.sudo()))

    def _tp_delegation_domain(self, company_field='company_id', department_field='department_id'):
        """Only explicit department-owned records. No parent or unknown fallback."""
        self.ensure_one()
        domains = []
        for company in self.company_ids & self.env.companies:
            if not self._tp_has_admin_delegation(company):
                continue
            own, complete = self._tp_delegation_scope(company)
            if complete:
                domains.append(Domain([
                    (company_field, '=', company.id), (department_field, '!=', False),
                    (department_field, 'not in', own.ids),
                    (department_field + '.company_id', '=', company.id),
                ]))
        return Domain.OR(domains)

    @api.model
    def get_tp_admin_capabilities(self):
        """Only caller identity; presentation does not impersonate Odoo isSystem."""
        user = self.env.user
        main = user._tp_is_main_admin()
        delegated = user._tp_has_admin_delegation()
        return {'level': 'main' if main else 'delegated' if delegated else 'business',
                'can_manage_delegation': main, 'delegated': delegated,
                'scope': 'Phòng mình giữ quyền nghiệp vụ; phòng khác chỉ dùng chức năng đã rà soát.' if delegated else '',
                'department_ids': user._tp_delegation_departments().ids if delegated else []}


class AdminDelegation(models.Model):
    _name = 'tp.admin.delegation'
    _description = 'Lịch sử ủy quyền quản trị'
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Tài khoản', required=True, ondelete='restrict', index=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, ondelete='restrict', index=True, readonly=True)
    state = fields.Selection([('active', 'Đang được ủy quyền'), ('revoked', 'Đã thu hồi')], string='Trạng thái', required=True, readonly=True)
    granted_by_id = fields.Many2one('res.users', string='Người cấp quyền', required=True, ondelete='restrict', readonly=True)
    granted_at = fields.Datetime(string='Thời điểm cấp quyền', required=True, readonly=True)
    grant_reason = fields.Text(string='Lý do cấp quyền', required=True, readonly=True)
    revoked_by_id = fields.Many2one('res.users', string='Người thu hồi', ondelete='restrict', readonly=True)
    revoked_at = fields.Datetime(string='Thời điểm thu hồi', readonly=True)
    revoke_reason = fields.Text(string='Lý do thu hồi', readonly=True)

    _one_live = models.UniqueIndex('(user_id, company_id) WHERE state=\'active\'', 'Tài khoản đã được ủy quyền tại công ty này.')
    _reason_required = models.Constraint('CHECK(length(btrim(grant_reason)) > 0)', 'Cần lý do cấp quyền.')
    _revoked_audit = models.Constraint(
        "CHECK(state != 'revoked' OR (revoked_by_id IS NOT NULL AND revoked_at IS NOT NULL AND length(btrim(revoke_reason)) > 0))",
        'Thu hồi phải giữ người thực hiện, thời điểm và lý do.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_delegation_ledger') is not _LEDGER:
            raise AccessError(self.env._('Cấp quyền qua thao tác quản trị đã xác thực.'))
        return super().create(vals_list)

    def write(self, vals):
        if (self.env.context.get('_tp_delegation_ledger') is not _LEDGER
                or set(vals) != {'state', 'revoked_by_id', 'revoked_at', 'revoke_reason'}
                or vals.get('state') != 'revoked' or any(row.state != 'active' for row in self)):
            raise AccessError(self.env._('Lịch sử ủy quyền không được sửa; chỉ thu hồi qua thao tác đã xác thực.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Giữ lịch sử cấp và thu hồi quyền quản trị.'))

    @api.model
    def _change(self, user, company, operation, reason):
        if not self.env.user._tp_is_main_admin():
            raise AccessError(self.env._('Chỉ Quản trị chính được cấp hoặc thu hồi quyền quản trị.'))
        if operation not in ('grant', 'revoke') or not isinstance(reason, str) or not reason.strip():
            raise UserError(self.env._('Chọn thao tác và nhập lý do.'))
        if not user or not company or company not in self.env.companies or company not in user.sudo().company_ids:
            raise AccessError(self.env._('Tài khoản hoặc công ty không thuộc phạm vi quản lý.'))
        user._tp_admin_lock(exclusive=True)
        protected = self.env['res.users']
        for xmlid in ('base.user_root', 'base.user_admin', 'base.public_user', 'base.template_portal_user', 'base.default_user'):
            protected |= self.env.ref(xmlid, raise_if_not_found=False) or self.env['res.users']
        if operation == 'grant' and (user.share or not user.active or user._tp_is_main_admin()
                                     or not user.has_group('base.group_user') or user in protected):
            raise AccessError(self.env._('Chỉ cấp ủy quyền cho tài khoản nội bộ đang mở, không phải Quản trị chính.'))
        ledger = self.sudo().with_context(_tp_delegation_ledger=_LEDGER)
        current = ledger.search([('user_id', '=', user.id), ('company_id', '=', company.id), ('state', '=', 'active')])
        if operation == 'grant':
            if current:
                raise UserError(self.env._('Tài khoản đã được ủy quyền.'))
            ledger.create({'user_id': user.id, 'company_id': company.id, 'state': 'active',
                           'granted_by_id': self.env.uid, 'granted_at': fields.Datetime.now(), 'grant_reason': reason.strip()})
        else:
            if not current:
                raise UserError(self.env._('Không có quyền quản trị đang hiệu lực để thu hồi.'))
            current.write({'state': 'revoked', 'revoked_by_id': self.env.uid,
                           'revoked_at': fields.Datetime.now(), 'revoke_reason': reason.strip()})
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.transaction.invalidate_access_cache()
        self.env.transaction.invalidate_ormcache()
        return True


class AdminEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_admin_level = fields.Selection([('business', 'Người dùng nghiệp vụ'), ('delegated', 'Quản trị được ủy quyền'),
                                       ('main', 'Quản trị chính')], compute='_compute_tp_admin_level', string='Quyền quản trị')
    tp_admin_scope = fields.Text(compute='_compute_tp_admin_level', string='Phạm vi quản trị')
    tp_can_manage_delegation = fields.Boolean(compute='_compute_tp_admin_level')

    @api.depends('user_id', 'company_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_admin_level(self):
        for employee in self:
            user = employee.sudo().user_id
            main = bool(user and user.has_group('base.group_system'))
            self.env.cr.execute(
                "SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND company_id=%s AND state='active' LIMIT 1",
                [user.id or 0, employee.sudo().company_id.id])
            delegated = bool(self.env.cr.fetchone())
            employee.tp_admin_level = 'main' if main else 'delegated' if delegated else 'business'
            employee.tp_can_manage_delegation = self.env.user._tp_is_main_admin()
            employee.tp_admin_scope = ('Phòng mình giữ nguyên quyền nghiệp vụ. Phòng khác chỉ mở chức năng đã rà soát; '
                                       'không cấp tiếp quyền, đổi vai trò, chuyển phòng hoặc quản lý tài khoản đặc quyền.'
                                       if delegated else 'Theo quyền quản trị hiện có.' if main else 'Theo vai trò và phân công nghiệp vụ.')

    def _tp_admin_wizard_action(self, operation):
        self.ensure_one()
        if not self.env.user._tp_is_main_admin():
            raise AccessError(self.env._('Chỉ Quản trị chính được quản lý ủy quyền.'))
        self.check_access('read')
        if not self.user_id:
            raise UserError(self.env._('Cần tạo tài khoản cá nhân trước khi cấp quyền quản trị.'))
        wizard = self.env['tp.admin.delegation.wizard'].create({'employee_id': self.id, 'operation': operation})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id,
                'view_mode': 'form', 'target': 'new', 'name': 'Cấp quyền quản trị' if operation == 'grant' else 'Thu hồi quyền quản trị'}

    def action_tp_grant_admin(self):
        return self._tp_admin_wizard_action('grant')

    def action_tp_revoke_admin(self):
        return self._tp_admin_wizard_action('revoke')


class AdminDelegationWizard(models.TransientModel):
    _name = 'tp.admin.delegation.wizard'
    _description = 'Cấp hoặc thu hồi quyền quản trị có giới hạn'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string='Nhân viên')
    user_id = fields.Many2one(related='employee_id.user_id', readonly=True, string='Tài khoản')
    expected_user_id = fields.Many2one('res.users', readonly=True)
    company_id = fields.Many2one(related='employee_id.company_id', readonly=True, string='Công ty')
    operation = fields.Selection([('grant', 'Cấp quyền quản trị'), ('revoke', 'Thu hồi quyền quản trị')], required=True, string='Thao tác')
    # The dialog is created before the administrator can enter a reason.
    reason = fields.Text(string='Lý do')
    scope_preview = fields.Text(compute='_compute_preview', string='Phạm vi thực tế')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals.get('employee_id')).exists()
            employee.check_access('read')
            vals['expected_user_id'] = employee.user_id.id
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'employee_id', 'expected_user_id'}:
            raise AccessError(self.env._('Tài khoản đích đã chốt khi mở hộp thoại; hãy mở lại để chọn hồ sơ khác.'))
        return super().write(vals)

    @api.depends('employee_id', 'operation')
    def _compute_preview(self):
        for wizard in self:
            departments = wizard.user_id._tp_delegation_departments(wizard.company_id) if wizard.user_id else self.env['hr.department']
            wizard.scope_preview = ('Phòng nghiệp vụ được bảo vệ: ' + (', '.join(departments.mapped('name')) or 'Chưa xác định — không mở thêm nghiệp vụ.')
                                    + '\nCấp/thu không đổi chức vụ, nhóm, phân công hoặc quyền tiền. '
                                    'Dữ liệu chung, nguồn chưa rõ và chức năng chưa rà soát giữ quyền nghiệp vụ hiện hành.')

    @check_identity
    def action_apply(self):
        self.ensure_one()
        if not self.env.user._tp_is_main_admin():
            raise AccessError(self.env._('Chỉ Quản trị chính được quản lý ủy quyền.'))
        if not (self.reason or '').strip():
            raise UserError(self.env._('Nhập lý do cấp hoặc thu hồi quyền quản trị.'))
        self.employee_id.check_access('read')
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [self.employee_id.id])
        self.employee_id.invalidate_recordset(['user_id', 'company_id'])
        self.invalidate_recordset(['user_id', 'company_id'])
        if not self.user_id or self.user_id != self.expected_user_id:
            raise UserError(self.env._('Tài khoản đã đổi. Vui lòng mở lại hộp thoại.'))
        with self.env.cr.savepoint():
            self.env['tp.admin.delegation']._change(self.user_id, self.company_id, self.operation, self.reason)
            self.employee_id.message_post(body=self.env._('%(action)s cho %(login)s. Lý do: %(reason)s',
                                          action='Đã cấp quyền quản trị' if self.operation == 'grant' else 'Đã thu hồi quyền quản trị',
                                          login=self.user_id.login, reason=self.reason.strip()))
        return {'type': 'ir.actions.act_window_close'}
