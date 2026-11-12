from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from PIL import Image

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

from odoo.addons.tp_hr_workspace.models.identity import _IDENTITY


@tagged('post_install', '-at_install')
class TestIdentityOrg(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.old, cls.kd, cls.other = cls.env['hr.department'].create([
            {'name': name, 'company_id': cls.company.id} for name in ('Synthetic Design', 'Synthetic KD', 'Synthetic Other')])
        cls.team = cls.env['crm.team'].create({'name': 'Synthetic Identity Team', 'company_id': cls.company.id, 'kd_department_id': cls.kd.id})
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Identity', 'login': 'identity.org.synthetic', 'password': 'Synthetic-Identity-2026',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({'name': cls.user.name, 'company_id': cls.company.id,
            'department_id': cls.old.id, 'date_version': fields.Date.today() - timedelta(days=10), 'user_id': cls.user.id})

    def wizard(self, target=None, **values):
        return self.env['tp.hr.role.wizard'].with_user(self.admin).create({
            'employee_id': self.employee.id, 'change_kind': 'transfer',
            'target_department_id': (target or self.kd).id, 'reason': 'Synthetic department transfer', **values})

    def move(self, target=None, **values):
        wizard = self.wizard(target, **values)
        wizard.action_preview()
        wizard.action_apply()
        return wizard

    @staticmethod
    def photo(color):
        stream = BytesIO()
        Image.new('RGB', (80, 80), color).save(stream, 'PNG')
        return BinaryBytes(stream.getvalue())

    def test_name_photo_bidirectional_identity_and_private_scope(self):
        login = self.user.login
        self.env.cr.execute('SELECT password,totp_secret FROM res_users WHERE id=%s', [self.user.id])
        auth = self.env.cr.fetchone()
        identity = (self.employee.id, self.employee.resource_id.id, self.user.id, self.user.partner_id.id)
        customer = self.env['res.partner'].create({'name': self.employee.name})
        same_name = self.env['hr.employee'].create({'name': self.employee.name, 'company_id': self.company.id})
        self.employee.with_user(self.admin).write({'name': 'Synthetic Official Name', 'image_1920': self.photo('red')})
        self.assertEqual(self.user.name, self.employee.name)
        self.assertEqual(bytes(self.user.image_1920), bytes(self.employee.image_1920))
        self.user.with_user(self.user).write({'image_1920': self.photo('blue')})
        self.assertEqual(bytes(self.user.image_1920), bytes(self.employee.image_1920))
        with self.assertRaises(AccessError):
            self.user.with_user(self.user).write({'name': 'Self elevation name'})
        self.assertEqual(self.user.login, login)
        self.env.cr.execute('SELECT password,totp_secret FROM res_users WHERE id=%s', [self.user.id])
        self.assertEqual(auth, self.env.cr.fetchone())
        self.assertEqual(identity, (self.employee.id, self.employee.resource_id.id, self.user.id, self.user.partner_id.id))
        self.assertEqual(customer.name, 'Synthetic Identity')
        self.assertEqual(same_name.name, 'Synthetic Identity')
        with self.assertRaises(AccessError):
            self.employee.with_user(self.user).read(['private_email', 'identification_id'])
        self.employee.with_user(self.admin).write({'image_1920': False})
        self.assertEqual(bytes(self.employee.avatar_128), bytes(self.user.partner_id.avatar_128))

    def test_reconciliation_conflict_requires_choice_and_stale_rejected(self):
        self.employee.with_context(_tp_identity=_IDENTITY).write({'image_1920': self.photo('red')})
        self.user.with_context(_tp_identity=_IDENTITY).write({'image_1920': self.photo('blue')})
        wizard = self.env['tp.hr.identity.wizard'].with_user(self.admin).create({'employee_id': self.employee.id})
        wizard.action_preview()
        self.assertFalse(wizard.choice)
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.choice = 'account'
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.action_preview()
        wizard.action_apply()
        self.assertEqual(bytes(self.employee.image_1920), bytes(self.user.image_1920))
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_transfer_in_staff_empty_without_money_or_admin(self):
        old_version = self.employee.current_version_id
        self.move()
        self.assertEqual(self.employee.department_id, self.kd)
        self.assertEqual(old_version.department_id, self.old)
        self.assertTrue(self.user.has_group('tp_kd_workspace.group_scoped_staff'))
        self.assertTrue(self.user.with_user(self.user)._tp_can_kd_workspace())
        for group in ('base.group_system', 'hr.group_hr_user', 'tp_core.group_manager'):
            self.assertFalse(self.user.has_group(group))
        self.assertFalse(self.env['tp.kd.department.role']._roles(user=self.user))
        self.assertFalse(self.env['project.project'].with_user(self.user).search([('tp_managed', '=', True)]))
        self.assertEqual(self.user.with_user(self.user).get_tp_department_workspace()['id'], self.kd.id)

    def test_transfer_out_revokes_role_assignments_grants_and_team(self):
        self.user.group_ids = [Command.link(self.env.ref('base.group_allow_export').id)]
        self.move(target_role='head')
        project = self.env['project.project'].create({'name': 'Synthetic Scope', 'tp_managed': True, 'tp_code': 'IDENTITY-ORG-TEST',
            'company_id': self.company.id, 'tp_department_id': self.kd.id})
        assignment = self.env['tp.project.assignment'].create({'user_id': self.user.id, 'project_id': project.id})
        grant = self.env['tp.project.grant'].create({'user_id': self.user.id, 'project_id': project.id,
            'capability': 'financial_read', 'reason': 'Synthetic direct grant'})
        attachment = self.env['ir.attachment'].create({'name': 'Synthetic project file', 'res_model': project._name,
            'res_id': project.id, 'raw': b'Synthetic scope evidence'})
        self.assertTrue(attachment.with_user(self.user).has_access('read'))
        self.team.member_ids = [Command.link(self.user.id)]
        revision = self.user.tp_lock_revision
        self.move(self.other)
        self.assertFalse(assignment.active)
        self.assertFalse(grant.active)
        self.assertFalse(self.env['tp.kd.department.role']._roles(user=self.user))
        self.assertNotIn(self.user, self.team.member_ids)
        self.assertGreater(self.user.tp_lock_revision, revision)
        self.assertFalse(self.user.with_user(self.user)._tp_can_kd_workspace())
        self.assertFalse(project.with_user(self.user).has_access('read'))
        with self.assertRaises(AccessError):
            project.with_user(self.user).export_data(['name'])
        with self.assertRaises(AccessError):
            attachment.with_user(self.user).read(['raw'])
        with self.assertRaises(AccessError):
            self.env['tp.kd.overview'].with_user(self.user).get_kd_dashboard()
        with self.assertRaises(AccessError):
            self.env['tp.kd.report.center'].with_user(self.user).get_kd_report('R01')

    def test_explicit_cross_department_retains_listed_scope(self):
        self.move()
        project = self.env['project.project'].create({'name': 'Synthetic Cross', 'tp_managed': True, 'tp_code': 'IDENTITY-CROSS',
            'company_id': self.company.id, 'tp_department_id': self.kd.id})
        assignment = self.env['tp.project.assignment'].create({'user_id': self.user.id, 'project_id': project.id})
        self.move(self.other, keep_cross_department=True)
        self.assertTrue(assignment.active and assignment.tp_cross_department)
        self.assertTrue(self.user.with_user(self.user)._tp_can_kd_workspace())
        self.assertTrue(project.with_user(self.user).has_access('read'))

    def test_no_account_move_then_create_account_current_workspace(self):
        employee = self.env['hr.employee'].create({'name': 'Synthetic No Account', 'company_id': self.company.id, 'department_id': self.old.id})
        wizard = self.wizard(employee_id=employee.id)
        wizard.action_preview()
        wizard.action_apply()
        self.assertFalse(employee.user_id)
        account = self.env['tp.hr.account.wizard'].with_user(self.admin).create({'employee_id': employee.id, 'new_user_login': 'identity.noaccount.synthetic'})
        with patch.object(type(account), '_require_recent_identity', return_value=None):
            account.action_create_user(password='Synthetic-Identity-2026', confirmation='Synthetic-Identity-2026')
        self.assertTrue(employee.user_id.has_group('tp_kd_workspace.group_scoped_staff'))

    def test_stale_preview_retry_and_rollback(self):
        wizard = self.wizard()
        wizard.action_preview()
        wizard.reason = 'Changed after preview'
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.action_preview()
        before = (self.employee.current_version_id, self.employee.department_id, self.user.group_ids, self.user.tp_lock_revision)
        with patch.object(type(self.employee), 'message_post', side_effect=UserError('Synthetic audit failure')):
            with self.assertRaises(UserError):
                wizard.action_apply()
        self.assertEqual(before, (self.employee.current_version_id, self.employee.department_id, self.user.group_ids, self.user.tp_lock_revision))
        wizard.action_apply()
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_direct_version_context_import_and_self_service_guards(self):
        for actor in (self.user, self.admin):
            with self.assertRaises(AccessError):
                self.employee.with_user(actor).with_context(_tp_transfer=True).write({'department_id': self.kd.id})
        with self.assertRaises(AccessError):
            self.employee.current_version_id.with_user(self.admin).write({'department_id': self.kd.id})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.admin).create_version({'date_version': fields.Date.today() + timedelta(days=5), 'department_id': self.kd.id})
        history = self.employee.current_version_id.copy({'date_version': fields.Date.today() - timedelta(days=20)})
        history.with_user(self.admin).write({'department_id': self.other.id})
        self.assertEqual(self.employee.department_id, self.old)
        with self.assertRaises(AccessError):
            self.employee.with_user(self.admin).write({'current_version_id': history.id})
        for values in ({'date_version': history.date_version - timedelta(days=1)}, {'active': False}):
            with self.assertRaises(AccessError):
                self.employee.current_version_id.with_user(self.admin).write(values)
        with self.assertRaises(AccessError):
            self.employee.current_version_id.with_user(self.admin).unlink()

    def test_work_contact_never_publishes_private_email(self):
        self.employee.with_user(self.admin).write({'private_email': 'private@example.invalid', 'work_email': False})
        self.employee.with_user(self.admin).write({'work_phone': '0123456789'})
        self.assertFalse(self.user.email)
        self.assertEqual(self.user.partner_id.phone, '0123456789')
        self.employee.with_user(self.admin).write({'work_email': 'work@example.invalid'})
        self.assertEqual(self.user.email, 'work@example.invalid')
        self.assertEqual(self.employee.private_email, 'private@example.invalid')

    def test_foreign_version_cannot_replace_current_or_rebind_history(self):
        other = self.env['hr.employee'].create({'name': 'Synthetic foreign version owner', 'company_id': self.company.id,
            'department_id': self.old.id})
        # Same department must not make another person's version a valid source.
        with self.assertRaises(AccessError):
            self.employee.with_user(self.admin).write({'current_version_id': other.current_version_id.id})
        for version in (self.employee.current_version_id, self.employee.current_version_id.copy({
            'date_version': fields.Date.today() - timedelta(days=20)})):
            with self.assertRaises(AccessError):
                version.with_user(self.admin).write({'employee_id': other.id})
        foreign = self.env['res.company'].create({'name': 'Synthetic foreign version company'})
        with self.assertRaises(AccessError):
            self.env['hr.version'].with_user(self.admin).create({'employee_id': self.employee.id,
                'department_id': self.old.id, 'company_id': foreign.id})
        self.assertEqual(self.employee.current_version_id.employee_id, self.employee)
        self.assertEqual(self.employee.department_id, self.old)

    def test_handover_and_privileged_groups_require_resolution(self):
        task = self.env['project.task'].create({'name': 'Synthetic pending handover', 'company_id': self.company.id,
            'user_ids': [Command.link(self.user.id)]})
        wizard = self.wizard()
        wizard.action_preview()
        self.assertIn(str(task.id), wizard.preview)
        with self.assertRaises(UserError):
            wizard.action_apply()
        wizard.acknowledge_handover = True
        wizard.action_preview()
        wizard.action_apply()
        self.assertEqual(task.user_ids, self.user)
        self.user.group_ids = [Command.link(self.env.ref('hr.group_hr_manager').id)]
        with self.assertRaisesRegex(UserError, 'nhóm quyền quản lý'):
            self.wizard(self.other).action_preview()

    def test_target_head_incumbent_and_company_scope(self):
        self.user.group_ids = [Command.link(self.env.ref('tp_kd_workspace.group_scoped_staff').id)]
        self.env['tp.kd.department.role'].create({'user_id': self.user.id, 'department_id': self.kd.id,
            'company_id': self.company.id, 'reason': 'Synthetic incumbent'})
        with self.assertRaisesRegex(UserError, 'Synthetic Identity'):
            self.wizard(target_role='head').action_preview()

    def test_server_menus_same_scope_and_admin_kept(self):
        kd = self.env.ref('tp_kd_workspace.menu_kd')
        generic = self.env.ref('tp_hr_workspace.menu_department_workspace')
        menus = self.env['ir.ui.menu'].with_user(self.user)
        self.assertNotIn(kd.id, menus._visible_menu_ids())
        self.assertIn(generic.id, menus._visible_menu_ids())
        self.move()
        self.assertIn(kd.id, menus._visible_menu_ids())
        self.assertNotIn(generic.id, menus._visible_menu_ids())
        self.assertIn(self.env.ref('base.menu_administration').id, self.env['ir.ui.menu'].with_user(self.admin)._visible_menu_ids())
