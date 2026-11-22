from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .test_delegation import DelegationCase
from odoo.addons.tp_hr_workspace.models import audit_cleanup


@tagged('post_install', '-at_install', 'tp_audit_cleanup')
class TestAuditCleanup(DelegationCase):
    def row(self, **values):
        return self.env['tp.hr.employee.audit']._tp_record([dict({
            'action': 'permanent_delete', 'employee_ref': 987654,
            'employee_code': 'TP998', 'source_code': '998',
            'company_id': self.company.id, 'reason': 'Xóa hồ sơ nhập nhầm',
        }, **values)])

    def test_readable_reason_preserves_original_and_old_data(self):
        row = self.row(action='account_profile_change',
                       reason='Cập nhật tài khoản/hồ sơ qua hr.employee #39',
                       snapshot={'model': 'hr.employee', 'changes': {'department_id': {'before': 1, 'after': 2}}, 'image_changed': True})
        self.assertEqual(row.reason_display, 'Cập nhật phòng ban, ảnh đại diện.')
        self.assertIn('hr.employee', row.reason)
        self.assertEqual(self.row(reason='Theo đề nghị của nhân viên').reason_display, 'Theo đề nghị của nhân viên')

    def test_staff_denied_and_direct_write_unlink_always_denied(self):
        row = self.row()
        with self.assertRaises(AccessError):
            row.with_user(self.users[2]).action_hide_from_list()
        for actor in (self.admin, self.users[2]):
            for operation in (lambda: row.with_user(actor).write({'active': False}),
                              lambda: row.with_user(actor).unlink()):
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    operation()

    def test_each_cleanup_requires_correct_password_and_keeps_tombstone(self):
        row = self.row()
        service = row.with_user(self.admin)
        action = service.action_hide_from_list()
        wizard = self.env['tp.hr.audit.cleanup'].with_user(self.admin).browse(action['res_id'])
        fake_request = SimpleNamespace(session=SimpleNamespace(uid=self.admin.id))
        with patch.object(audit_cleanup, 'request', fake_request):
            with self.assertRaises(UserError):
                wizard.action_confirm()
            with patch.object(type(self.env['hr.employee']), '_tp_verify_admin_password', return_value='Mật khẩu không đúng'):
                with self.assertRaises(UserError):
                    wizard.with_context(password='wrong-synthetic').action_confirm()
            self.assertTrue(row.active)
            with patch.object(type(self.env['hr.employee']), '_tp_verify_admin_password', return_value='') as verify:
                wizard.with_context(password='synthetic').action_confirm()
                verify.assert_called_once()
        self.assertFalse(row.active)
        self.assertEqual(row.hidden_by_id, self.admin)
        self.assertFalse(self.env['tp.hr.employee.audit'].search([('id', '=', row.id)]))
        self.assertIn(row, self.env['tp.hr.employee.audit']._tp_removed_identities(self.company.id, ['998']))
        self.env.cr.execute('SELECT employee_code FROM tp_hr_employee_audit WHERE id=%s', [row.id])
        self.assertEqual(self.env.cr.fetchone()[0], 'TP998')

    def test_delegated_admin_allowed_and_revoke_blocks_confirmation(self):
        self.grant(self.users[0])
        row = self.row()
        action = row.with_user(self.users[0]).action_hide_from_list()
        wizard = self.env['tp.hr.audit.cleanup'].with_user(self.users[0]).browse(action['res_id'])
        self.grant(self.users[0], operation='revoke')
        with patch.object(audit_cleanup, 'request', SimpleNamespace(session=SimpleNamespace(uid=self.users[0].id))):
            with self.assertRaises(AccessError):
                wizard.with_context(password='synthetic').action_confirm()
        self.assertTrue(row.active)
