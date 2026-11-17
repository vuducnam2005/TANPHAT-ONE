from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDelegationBusinessBaseline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.department = cls.env['hr.department'].create({
            'name': 'Synthetic HR baseline', 'company_id': cls.company.id,
        })
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic preexisting HR officer', 'login': 'synthetic.delegate.hr.baseline',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref(xmlid).id for xmlid in (
                'base.group_user', 'hr.group_hr_user', 'tp_reporting.group_reporting_config')])],
        })
        cls.employee, cls.coworker = cls.env['hr.employee'].create([
            {'name': name, 'company_id': cls.company.id, 'department_id': cls.department.id,
             'user_id': user_id, 'date_version': fields.Date.today()}
            for name, user_id in ((cls.user.name, cls.user.id), ('Synthetic HR coworker', False))
        ])
        cls.schedule = cls.env['tp.report.schedule'].with_user(cls.user).create({
            'name': 'Synthetic baseline schedule', 'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

    def grant(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.user, self.company, operation, 'Synthetic baseline preservation')

    def test_existing_hr_job_metadata_preserved_and_self_protected(self):
        coworker = self.coworker.with_user(self.user)
        coworker.write({'job_title': 'Before delegation'})
        self.grant()
        coworker.write({'job_title': 'During delegation'})
        self.assertEqual(coworker.job_title, 'During delegation')
        coworker.current_version_id.write({'job_title': 'Version metadata'})
        self.assertEqual(coworker.job_title, 'Version metadata')
        with self.assertRaises(AccessError):
            self.employee.with_user(self.user).sudo().write({'job_title': 'Self promotion'})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.user).sudo().current_version_id.write({'job_title': 'Self promotion'})
        self.grant('revoke')
        coworker.write({'job_title': 'After delegation'})
        self.assertEqual(coworker.job_title, 'After delegation')

    def test_existing_reporting_schedule_crud_preserved(self):
        schedule = self.schedule.with_user(self.user)
        schedule.write({'deadline_days': 2})
        self.grant()
        schedule.write({'deadline_days': 3})
        temporary = self.env['tp.report.schedule'].with_user(self.user).create({
            'name': 'Synthetic delegated baseline schedule', 'company_id': self.company.id,
            'department_id': self.department.id,
        })
        temporary.unlink()
        self.assertEqual(schedule.deadline_days, 3)
        self.grant('revoke')
        schedule.write({'deadline_days': 4})
        self.assertEqual(schedule.deadline_days, 4)
