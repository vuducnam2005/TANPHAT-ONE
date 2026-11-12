from odoo import Command
from odoo.exceptions import AccessError, UserError

from .test_hr_workspace import TestHrWorkspace


class TestEmployeeDeleteDialog(TestHrWorkspace):
    """HR-CORRECTION-008: the guarded "Xóa hồ sơ nhập nhầm" dialog (synthetic data)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['res.users'].create({
            'name': 'Synthetic Delete HR Manager', 'login': 'hr008.synthetic.dialog.manager',
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_manager').id])],
        })

    def scoped(self, records, actor=None):
        return records.with_user(actor or self.admin).with_context(allowed_company_ids=[self.company.id])

    def open_dialog(self, employees, actor=None):
        action = self.scoped(employees, actor).action_tp_delete_mistaken()
        return self.scoped(self.env['tp.hr.employee.delete.wizard'], actor).browse(action['res_id']), action

    def test_entries_point_to_the_guarded_dialog_only(self):
        server_action = self.env.ref('tp_hr_workspace.action_server_delete_mistaken')
        self.assertEqual(server_action.group_ids, self.env.ref('base.group_system'))
        self.assertEqual(server_action.binding_model_id.model, 'hr.employee')
        self.assertFalse(self.env.ref('hr_timesheet.unlink_employee_action').binding_model_id)
        employee = self.employees[1]
        for action in (self.scoped(employee).action_unlink_wizard(),
                       server_action.with_user(self.admin).with_context(active_model='hr.employee', active_ids=employee.ids,
                                                                        allowed_company_ids=[self.company.id]).run()):
            self.assertEqual((action['res_model'], action['target']), ('tp.hr.employee.delete.wizard', 'new'))
        for actor in (self.hr, self.manager):
            with self.assertRaises(AccessError):
                self.scoped(employee, actor).action_tp_delete_mistaken()
        views = self.env['hr.employee'].get_views([(False, 'form')])
        self.assertIn('delete="0"', views['views']['form']['arch'])

    def test_dialog_deletes_unused_entry_after_reason(self):
        employee = self.scoped(self.env['hr.employee']).create({'name': 'Synthetic Dialog Mistake', 'company_id': self.company.id})
        code = employee.tp_employee_code
        wizard, action = self.open_dialog(employee)
        self.assertEqual(action['name'], 'Xóa hồ sơ nhập nhầm')
        self.assertTrue(wizard.eligible)
        self.assertIn('Synthetic Dialog Mistake', wizard.summary)
        self.assertIn(code, wizard.summary)
        self.assertIn('Đủ điều kiện xóa', wizard.summary)
        with self.assertRaises(UserError) as error:
            wizard.action_confirm_delete()
        self.assertIn('lý do', str(error.exception))
        self.assertTrue(employee.exists())
        wizard.reason = 'Synthetic: tạo trùng khi nhập tay'
        result = wizard.action_confirm_delete()
        self.assertFalse(employee.exists())
        self.assertIn('Đã xóa vĩnh viễn 1 hồ sơ', result['params']['message'])
        self.assertEqual(result['params']['next']['target'], 'main')
        audit = self.env['tp.hr.employee.audit'].search([('employee_code', '=', code), ('action', '=', 'delete')])
        self.assertEqual(audit.reason, 'Synthetic: tạo trùng khi nhập tay')

    def test_used_entry_explains_and_offers_archive(self):
        user = self.env['res.users'].create({
            'name': 'Synthetic Private', 'login': 'hr008.synthetic.dialog.account',
            'company_id': self.company.id, 'company_ids': [Command.set([self.company.id])],
        })
        used = self.employees[1]
        used.user_id = user
        free = self.scoped(self.env['hr.employee']).create({'name': 'Synthetic Dialog Free', 'company_id': self.company.id})
        wizard, _action = self.open_dialog(used | free)
        self.assertFalse(wizard.eligible)
        self.assertTrue(wizard.can_archive)
        self.assertIn('hr008.synthetic.dialog.account', wizard.summary)
        wizard.reason = 'Synthetic attempt'
        with self.assertRaises(UserError) as error:
            wizard.action_confirm_delete()
        message = str(error.exception)
        self.assertIn('Không hồ sơ nào bị xóa', message)
        self.assertIn('Lưu trữ nhân viên', message)
        self.assertNotIn('Traceback', message)
        self.assertTrue(used.exists() and free.exists())
        result = wizard.action_archive_instead()
        self.assertIn('Tài khoản cá nhân (nếu có) không thay đổi', result['params']['message'])
        self.assertFalse(used.active or free.active)
        self.assertTrue(user.active)
        self.assertEqual(used.user_id, user)
