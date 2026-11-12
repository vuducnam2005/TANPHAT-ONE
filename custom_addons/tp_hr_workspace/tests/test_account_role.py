from unittest.mock import patch

from psycopg2.errors import UniqueViolation

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

from .test_hr_workspace import TestHrWorkspace


class TestPersonalAccountRole(TestHrWorkspace):
    def setUp(self):
        super().setUp()
        self.identity_patch = patch.object(type(self.env['tp.hr.account.wizard']), '_require_recent_identity', return_value=None)
        self.identity_patch.start()
        self.addCleanup(self.identity_patch.stop)

    def create_account(self, wizard):
        return wizard.action_create_user(password='Synthetic-Strong-Password-2026', confirmation='Synthetic-Strong-Password-2026')

    def wizard(self, employee=None, actor=None, **values):
        return self.env['tp.hr.account.wizard'].with_user(actor or self.admin).with_context(
            allowed_company_ids=[self.company.id],
        ).create({'employee_id': (employee or self.employees[0]).id, **values})

    def test_create_duplicate_retry_and_no_department_name_inference(self):
        self.department.name = 'Kế hoạch Kinh doanh synthetic'
        wizard = self.wizard(new_user_login='hraccount.synthetic.new')
        groups_before = self.staff.group_ids
        action = self.create_account(wizard)
        user = self.employees[0].user_id
        self.assertTrue(action)
        self.assertEqual(user.login, 'hraccount.synthetic.new')
        self.assertEqual(user.company_ids, self.company)
        # HR-CORRECTION-008: personal accounts open in Vietnamese when it is installed.
        self.assertEqual(user.lang, 'vi_VN' if self.env['res.lang']._lang_get('vi_VN') else self.env.lang)
        self.assertFalse(user.has_group('tp_core.group_user'))
        self.assertEqual(groups_before, self.staff.group_ids)
        with self.assertRaises(UserError):
            self.create_account(wizard)
        with self.assertRaises(ValidationError):
            self.create_account(self.wizard(self.employees[1], new_user_login=user.login))
        self.assertFalse(self.employees[1].user_id)
        with self.assertRaises(AccessError):
            self.create_account(self.wizard(self.employees[1], self.hr, new_user_login='forbidden.new'))
        with self.assertRaises(AccessError):
            self.create_account(self.wizard(self.employees[1], new_user_login='outside.company').with_context(allowed_company_ids=[self.other.id]))
        with self.assertRaises(UserError):
            self.create_account(self.wizard())

    def test_creation_failure_rolls_back_user_and_mapping(self):
        wizard = self.wizard(new_user_login='hraccount.orphan.blocked')
        with patch.object(type(self.employees), 'message_post', side_effect=UserError('Synthetic audit failure')):
            with self.assertRaises(UserError):
                self.create_account(wizard)
        self.assertFalse(self.env['res.users'].with_context(active_test=False).search([('login', '=', 'hraccount.orphan.blocked')]))
        self.assertFalse(self.employees[0].user_id)

    def test_password_validation_reauth_and_no_secret_fields(self):
        self.env['ir.config_parameter'].sudo().set_int('auth_password_policy.minlength', 8)
        wizard = self.wizard(new_user_login='hraccount.password.validation')
        for password, confirm in (('', ''), ('short', 'short'), ('Strong-Password-2026', 'different'), (' padded ', ' padded ')):
            with self.assertRaises(ValidationError):
                wizard.action_create_user(password=password, confirmation=confirm)
        self.assertFalse(self.employees[0].user_id)
        self.assertFalse(any('password' in field or 'passwd' in field for field in wizard._fields))
        self.identity_patch.stop()
        try:
            with self.assertRaises(UserError):
                self.create_account(wizard)
        finally:
            self.identity_patch.start()

    def test_reset_password_and_audit_failure_are_atomic(self):
        self.create_account(self.wizard(new_user_login='hraccount.password.reset'))
        user = self.employees[0].user_id
        wizard = self.wizard(expected_user_id=user.id)

        def password_hash():
            self.env.cr.execute('SELECT password FROM res_users WHERE id=%s', [user.id])
            return self.env.cr.fetchone()[0]
        original = password_hash()
        with patch.object(type(self.employees), 'message_post', side_effect=UserError('Synthetic audit failure')):
            with self.assertRaises(UserError):
                wizard.action_set_password('Synthetic-New-Password-2026', 'Synthetic-New-Password-2026')
        self.assertEqual(password_hash(), original)
        self.assertTrue(wizard.action_set_password('Synthetic-New-Password-2026', 'Synthetic-New-Password-2026'))
        self.assertNotEqual(password_hash(), original)
        self.assertNotIn('Synthetic-New-Password-2026', str(self.employees[0].message_ids.mapped('body')))
        with self.assertRaises(AccessError):
            self.wizard(actor=self.hr, expected_user_id=user.id).action_set_password('Forbidden-New-Password', 'Forbidden-New-Password')

    def role_fixture(self):
        self.env['crm.team'].create({'name': 'Synthetic Scope Team', 'company_id': self.company.id,
                                     'kd_department_id': self.department.id})
        self.employees[0].user_id = self.staff
        return self.employees[0].with_user(self.admin).with_context(allowed_company_ids=[self.company.id])

    def test_position_entry_and_job_change_without_account_preserve_access(self):
        employee = self.employees[0].with_user(self.admin).with_context(allowed_company_ids=[self.company.id])
        action = employee.action_change_position()
        self.assertEqual(action['context']['default_change_kind'], 'job')
        job = self.env['hr.job'].create({'name': 'Synthetic Position Head', 'company_id': self.company.id})
        wizard = self.env['tp.hr.role.wizard'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({
            'employee_id': employee.id, 'change_kind': 'job', 'job_id': job.id, 'reason': 'Synthetic appointment',
        })
        self.assertFalse(wizard.role_available)
        wizard.action_preview()
        self.assertIn('Quyền sử dụng hệ thống: giữ nguyên', wizard.preview)
        wizard.action_apply()
        self.assertEqual(employee.job_id, job)
        self.assertFalse(employee.user_id)
        wizard.change_kind = 'role'
        wizard.new_role = 'head'
        with self.assertRaises(UserError):
            wizard.action_preview()
        with self.assertRaises(AccessError):
            employee.with_user(self.hr).action_change_position()
        with self.assertRaises(AccessError):
            employee.with_context(allowed_company_ids=[self.other.id]).action_change_position()

    def test_job_change_requires_reason_preview_current_snapshot_and_atomic_audit(self):
        employee = self.role_fixture()
        before = employee._tp_access_snapshot()
        job, other = self.env['hr.job'].create([
            {'name': 'Synthetic New Job', 'company_id': self.company.id},
            {'name': 'Synthetic Concurrent Job', 'company_id': self.company.id},
        ])
        wizard = self.env['tp.hr.role.wizard'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({
            'employee_id': employee.id, 'change_kind': 'job', 'job_id': job.id, 'reason': ' ',
        })
        with self.assertRaises(UserError):
            wizard.action_preview()
        wizard.reason = 'Synthetic change'
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.action_preview()
        employee.job_id = other
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.action_preview()
        with patch.object(type(employee), 'message_post', side_effect=UserError('Synthetic audit failure')):
            with self.assertRaises(UserError):
                wizard.action_apply()
        self.assertEqual(employee.job_id, other)
        wizard.action_apply()
        after = employee._tp_access_snapshot()
        self.assertEqual(after['job'], job.id)
        self.assertEqual({k: v for k, v in before.items() if k != 'job'}, {k: v for k, v in after.items() if k != 'job'})

    def test_position_job_scope_and_role_with_job_are_checked(self):
        employee = self.role_fixture()
        job = self.env['hr.job'].create({'name': 'Synthetic Head', 'company_id': self.company.id})
        outside = self.env['hr.job'].create({'name': 'Synthetic Outside Job', 'company_id': self.other.id})
        wizard = self.role_wizard(employee, 'head')
        wizard.write({'update_job': True, 'job_id': outside.id})
        with self.assertRaises((UserError, AccessError)):
            wizard.action_preview()
        wizard.job_id = job
        job.active = False
        with self.assertRaises(UserError):
            wizard.action_preview()
        job.active = True
        wizard.action_preview()
        wizard.action_apply()
        self.assertEqual(employee.job_id, job)
        self.assertTrue(self.env['tp.kd.department.role']._roles(self.staff))

    def test_one_head_requires_demotion_before_promoting_another_employee(self):
        employee = self.role_fixture()
        self.employees[1].user_id = self.hr
        second = self.employees[1].with_user(self.admin).with_context(allowed_company_ids=[self.company.id])
        waiting = self.role_wizard(second, 'head')
        waiting.action_preview()
        up = self.role_wizard(employee, 'head')
        up.action_preview()
        up.action_apply()
        for action in (waiting.action_preview, waiting.action_apply):
            with self.assertRaisesRegex(UserError, 'hạ cấp trưởng phòng hiện tại'):
                action()
        self.assertTrue(self.env['tp.kd.department.role']._roles(self.staff))
        self.assertFalse(self.env['tp.kd.department.role']._roles(self.hr))
        down = self.role_wizard(employee, 'staff')
        down.action_preview()
        down.action_apply()
        waiting.action_preview()
        waiting.action_apply()
        self.assertFalse(self.env['tp.kd.department.role']._roles(self.staff))
        self.assertTrue(self.env['tp.kd.department.role']._roles(self.hr))

    def test_single_head_index_covers_direct_provisioning_reactivation_and_scope(self):
        self.role_fixture()
        (self.staff | self.hr).write({'group_ids': [Command.link(self.env.ref('tp_kd_workspace.group_scoped_staff').id)]})
        Role = self.env['tp.kd.department.role'].sudo()
        values = {'company_id': self.company.id, 'department_id': self.department.id, 'reason': 'Synthetic single head'}
        incumbent = Role.create({**values, 'user_id': self.staff.id})
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            Role.create({**values, 'user_id': self.hr.id})
        department = self.env['hr.department'].create({'name': 'Synthetic Other Head Scope', 'company_id': self.company.id})
        other = Role.create({**values, 'user_id': self.hr.id, 'department_id': department.id})
        self.assertTrue(other.active)
        incumbent.write({'active': False, 'reason': 'Synthetic demotion'})
        replacement = Role.create({**values, 'user_id': self.hr.id})
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            incumbent.write({'active': True, 'reason': 'Synthetic reactivation denied'})
        self.assertTrue(replacement.active)
        self.assertFalse(incumbent.active)

    def role_wizard(self, employee, role):
        return self.env['tp.hr.role.wizard'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({
            'employee_id': employee.id, 'new_role': role, 'reason': 'Synthetic role acceptance',
        })

    def test_head_promotion_demotion_revokes_backend_money_export_and_audit(self):
        employee = self.role_fixture()
        project = self.env['project.project'].create({
            'name': 'Synthetic Role Project', 'company_id': self.company.id,
            'tp_managed': True, 'tp_department_id': self.department.id, 'tp_code': 'HR-ACCOUNT-ROLE-TEST',
        })
        other = project.copy({'name': 'Synthetic Outside', 'tp_code': 'HR-ACCOUNT-ROLE-OUT', 'tp_department_id': self.other_department.id})
        actor_project = project.with_user(self.staff)
        attachment = self.env['ir.attachment'].create({'name': 'Synthetic role file', 'raw': b'SYNTHETIC',
                                                      'res_model': 'project.project', 'res_id': project.id})
        message = project.message_post(body='Synthetic role history', author_id=self.admin.partner_id.id)
        wizard = self.role_wizard(employee, 'head')
        wizard.action_preview()
        wizard.action_apply()
        self.assertTrue(actor_project.has_access('read'))
        self.assertTrue(self.env['tp.project.grant'].with_user(self.staff)._tp_has_capability(actor_project, 'financial_read'))
        self.assertFalse(other.with_user(self.staff).has_access('read'))
        self.assertFalse(self.staff.has_group('base.group_system'))
        self.assertFalse(self.staff.has_group('hr.group_hr_user'))
        self.assertEqual(len(actor_project.export_data(['name'])['datas']), 1)
        self.assertEqual(attachment.with_user(self.staff).read(['raw'])[0]['raw']['content'], 'U1lOVEhFVElD')
        self.assertTrue(message.with_user(self.staff).read(['body']))
        role = self.env['tp.kd.department.role'].sudo().search([('user_id', '=', self.staff.id)])
        self.assertEqual(role.provisioned_by_id, self.admin)
        version = self.staff.tp_lock_revision
        down = self.role_wizard(employee, 'staff')
        down.action_preview()
        down.action_apply()
        self.assertFalse(actor_project.has_access('read'))
        self.assertFalse(actor_project._tp_head_allowed())
        self.assertFalse(self.env['tp.project.grant'].with_user(self.staff)._tp_has_capability(actor_project, 'financial_read'))
        with self.assertRaises(AccessError):
            actor_project.export_data(['name'])
        with self.assertRaises(AccessError):
            attachment.with_user(self.staff).read(['raw'])
        with self.assertRaises(AccessError):
            message.with_user(self.staff).read(['body'])
        self.assertGreater(self.staff.tp_lock_revision, version)
        events = self.env['tp.kd.department.role.event'].sudo().search([('role_id', '=', role.id)])
        self.assertTrue(all(e.actor_id == self.admin for e in events))
        self.assertTrue(any('groups' in (e.before or '') for e in events))
        self.assertFalse(role.active)

    def test_reason_stale_preview_group_conflict_and_job_do_not_grant(self):
        employee = self.role_fixture()
        action = employee.action_change_business_role()
        self.assertEqual(action['context']['default_employee_id'], employee.id)
        self.assertNotIn('res_id', action)
        employee.job_id = self.env['hr.job'].create({'name': 'Trưởng phòng synthetic', 'company_id': self.company.id})
        self.assertFalse(self.env['tp.kd.department.role']._roles(self.staff))
        wizard = self.role_wizard(employee, 'head')
        wizard.reason = ' '
        with self.assertRaises(UserError):
            wizard.action_preview()
        wizard.reason = 'Synthetic reason'
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.action_preview()
        wizard.reason = 'Changed after preview'
        with self.assertRaises(UserError):
            wizard.action_apply()
        with self.assertRaises(AccessError):
            wizard.write({'expected_digest': 'forged'})
        with self.assertRaises(AccessError):
            wizard.with_user(self.hr).action_preview()
        wizard.action_preview()
        wizard.action_apply()
        self.staff.group_ids = [Command.link(self.env.ref('project.group_project_manager').id)]
        down = self.role_wizard(employee, 'staff')
        down.action_preview()
        self.assertIn('Nhóm', down.preview)
        with self.assertRaises(UserError):
            down.action_apply()
        self.assertTrue(self.env['tp.kd.department.role']._roles(self.staff))

    def test_direct_grants_are_visible_and_conflicting_demotion_is_blocked(self):
        employee = self.role_fixture()
        up = self.role_wizard(employee, 'head')
        up.action_preview()
        up.action_apply()
        project = self.env['project.project'].create({'name': 'Synthetic Grant Project', 'tp_code': 'HR-GRANT-TEST',
            'company_id': self.company.id, 'tp_managed': True, 'tp_department_id': self.department.id})
        grant = self.env['tp.project.grant'].create({'project_id': project.id, 'user_id': self.staff.id,
            'capability': 'contract_draft_edit', 'department_id': self.department.id, 'reason': 'Synthetic extra'})
        down = self.role_wizard(employee, 'staff')
        down.action_preview()
        self.assertIn('Sửa bản nháp hợp đồng', down.preview)
        with self.assertRaises(UserError):
            down.action_apply()
        self.assertTrue(grant.active)
        grant.write({'active': False})
        financial = self.env['tp.project.grant'].create({
            'project_id': project.id, 'user_id': self.staff.id,
            'capability': 'financial_read', 'reason': 'Synthetic independent financial read',
        })
        down.action_preview()
        self.assertIn('Đọc thông tin tài chính', down.preview)
        down.action_apply()
        self.assertFalse(self.env['tp.kd.department.role']._roles(self.staff))
        self.assertTrue(financial.active)
        self.assertTrue(self.env['tp.project.grant'].with_user(self.staff)._tp_has_capability(
            project.with_user(self.staff), 'financial_read'))

    def test_native_user_binding_does_not_bypass_identity_guard(self):
        self.staff.email = 'native.binding@example.invalid'
        candidate = self.env['hr.employee'].new({
            'name': 'Synthetic email match', 'work_email': self.staff.email,
            'company_id': self.company.id,
        })
        candidate._onchange_work_email_link_user()
        self.assertFalse(candidate.user_id)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['res.users'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({
                'name': 'Synthetic native binding', 'login': 'hraccount.native.binding',
                'company_id': self.company.id, 'company_ids': [Command.set([self.company.id])],
                'group_ids': [Command.set([self.env.ref('base.group_user').id])],
                'create_employee_id': self.employees[0].id,
            })
        self.assertFalse(self.env['res.users'].search([('login', '=', 'hraccount.native.binding')]))
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.staff.with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).write({
                'employee_ids': [Command.link(self.employees[0].id)],
            })
        self.assertFalse(self.employees[0].user_id)
