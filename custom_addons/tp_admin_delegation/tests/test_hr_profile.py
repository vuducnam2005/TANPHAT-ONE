from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, UserError

from .test_delegation import DelegationCase


class TestDelegatedHrProfile(DelegationCase):
    def test_open_edit_and_archive_without_reason_rejects_confirmation(self):
        self.grant()
        employee = self.env['hr.employee'].create({
            'name': 'Synthetic unopened reason', 'company_id': self.company.id,
            'department_id': self.departments[1].id,
        }).with_user(self.users[0])
        for method in ('action_tp_edit_delegated_profile', 'action_tp_archive_delegated_profile'):
            action = getattr(employee, method)()
            wizard = self.env[action['res_model']].with_user(self.users[0]).browse(action['res_id'])
            self.assertFalse(wizard.reason)
            for reason in (False, '  \n '):
                wizard.reason = reason
                with self.assertRaises(UserError):
                    wizard.action_apply()
            self.assertTrue(employee.active)

    def test_native_hr_views_only_request_allowed_fields_and_keep_original_hr_views(self):
        self.grant()
        model = self.env['hr.employee'].with_user(self.users[0])
        original = [(self.env.ref('tp_hr_workspace.employee_' + kind).id, kind) for kind in ('list', 'form', 'search')]
        result = model.get_views(original)
        visible = result['models']['hr.employee']['fields']
        for kind, view in result['views'].items():
            self.assertEqual(view['id'], self.env.ref('tp_admin_delegation.delegated_employee_' + kind).id)
            fields = etree.fromstring(view['arch']).xpath('//field/@name')
            self.assertFalse(set(fields) - set(visible))
            self.assertNotIn('tp_employment_kind', fields)
        self.assertNotIn('private_email', visible)
        self.assertNotIn('wage', visible)
        self.assertIn('job_title', visible)
        self.assertIn('tp_account_status', visible)
        safe_fields = etree.fromstring(result['views']['form']['arch']).xpath('//field/@name')
        read = self.employees[1].with_user(self.users[0]).read(list(set(safe_fields)))
        self.assertEqual(read[0]['name'], self.employees[1].name)
        self.users[0].group_ids = [Command.link(self.env.ref('hr.group_hr_user').id)]
        self.assertEqual(model.get_view(original[0][0], 'list')['id'], original[0][0])

    def wizard(self, **values):
        return self.env['tp.hr.delegated.profile.wizard'].with_user(self.users[0]).create({
            'reason': 'Synthetic HR profile operation', **values,
        })

    def test_scoped_hr_create_edit_archive_without_identity_or_role_changes(self):
        self.grant()
        create = self.wizard(operation='create', name='Synthetic outside hire', department_id=self.departments[1].id,
                             job_title='Synthetic descriptive role', work_email='synthetic@example.invalid').with_context(
                                 default_user_id=self.admin.id, default_resource_id=self.employees[0].resource_id.id,
                                 default_department_id=self.departments[0].id,
                                 default_work_contact_id=self.admin.partner_id.id)
        create.action_apply()
        employee = self.env['hr.employee'].search([('name', '=', 'Synthetic outside hire')])
        self.assertEqual(employee.department_id, self.departments[1])
        self.assertFalse(employee.user_id)
        self.assertNotEqual(employee.work_contact_id, self.admin.partner_id)
        groups = self.users[0].group_ids
        edit = self.wizard(employee_id=employee.id, operation='edit')
        edit.write({'name': 'Synthetic renamed hire', 'job_title': 'Updated description', 'mobile_phone': '000000000'})
        edit.action_apply()
        self.assertEqual(employee.name, 'Synthetic renamed hire')
        self.assertEqual(employee.job_title, 'Updated description')
        self.assertEqual(employee.mobile_phone, '000000000')
        self.assertEqual(self.users[0].group_ids, groups)
        archive = self.wizard(employee_id=employee.id, operation='archive')
        archive.action_apply()
        self.assertFalse(employee.active)

    def test_scoped_hr_self_target_scope_and_revoked_wizard_rejected(self):
        self.grant()
        with self.assertRaises(AccessError):
            self.wizard(employee_id=self.employees[0].id, operation='edit')
        invalid = self.wizard(operation='create', name='Synthetic own department hire', department_id=self.departments[0].id)
        with self.assertRaises(AccessError):
            invalid.action_apply()
        other = self.wizard(employee_id=self.employees[1].id, operation='edit')
        with self.assertRaises(AccessError):
            other.write({'department_id': self.departments[2].id})
        self.grant(operation='revoke')
        with self.assertRaises(AccessError):
            other.action_apply()

    def test_scoped_hr_linked_archive_and_stale_preview_rejected(self):
        self.grant()
        linked = self.wizard(employee_id=self.employees[1].id, operation='archive')
        with self.assertRaises(AccessError):
            linked.action_apply()
        stale = self.wizard(employee_id=self.employees[1].id, operation='edit')
        self.employees[1].work_phone = 'Changed after preview'
        with self.assertRaises(UserError):
            stale.action_apply()

    def test_account_create_cannot_reuse_partner_or_groups_from_client_context(self):
        self.grant()
        employee = self.env['hr.employee'].create({
            'name': 'Synthetic scoped new account', 'company_id': self.company.id,
            'department_id': self.departments[1].id,
        })
        wizard = self.env['tp.hr.account.wizard'].with_user(self.users[0]).with_context(
            default_partner_id=self.admin.partner_id.id,
            default_group_ids=[self.env.ref('base.group_system').id],
        ).create({'employee_id': employee.id, 'expected_user_id': False,
                  'new_user_login': 'synthetic.delegate.create.account'})
        with patch.object(type(wizard), '_require_recent_identity', return_value=None):
            wizard.action_create_user(password='Synthetic-Account-Only-2026', confirmation='Synthetic-Account-Only-2026')
        user = employee.user_id
        self.assertNotEqual(user.partner_id, self.admin.partner_id)
        self.assertFalse(user.has_group('base.group_system'))
        self.assertFalse(user.has_group('tp_core.group_manager'))

    def test_delegated_overview_projection_matches_list_and_export(self):
        workspace = self.env['tp.hr.workspace'].with_user(self.users[0])
        with self.assertRaises(AccessError):
            workspace.get_overview()
        self.grant()
        data = workspace.get_overview()
        own = self.departments[0]
        self.assertFalse(data['can_create'])
        self.assertTrue(data['delegated_scope'])
        self.assertNotIn(own.id, [row['id'] for row in data['departments']])
        self.assertNotIn(own.id, [row['id'] for row in data['catalog_departments']])
        action = workspace.action_employees({}, [('user_id', '!=', False)])
        listed = self.env['hr.employee'].with_user(self.users[0]).search(action['domain'])
        self.assertIn(self.employees[1], listed)
        self.assertNotIn(self.employees[0], listed)
        # HR-only or private fields are never accepted as a delegated drill-down.
        for extra in ([('private_email', '!=', False)], [('department_id.name', '=', 'x')], 'bad'):
            with self.assertRaises(UserError):
                workspace.action_employees({}, extra)
        # A filter on the actor's own department cannot widen the counted rows.
        self.assertEqual(workspace.get_overview({'department_id': own.id})['total'], 0)
        self.assertTrue(workspace._build_xlsx({}))
        self.grant(operation='revoke')
        with self.assertRaises(AccessError):
            workspace.get_overview()
