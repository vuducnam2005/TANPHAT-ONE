"""Exercise RPC-equivalent directory reads and the native employee export proxy."""
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import AttendanceCase


@tagged('post_install', '-at_install')
class TestDirectoryPrivacy(AttendanceCase):
    def test_contact_fields_are_protected_on_both_models(self):
        self.emp_b.write({'mobile_phone': '0900000002'})
        restricted = ('mobile_phone', 'mobile_phone_sanitized', 'mobile_phone_formatted',
                      'phone_sanitized', 'phone_formatted', 'phone', 'email')
        for model_name in ('hr.employee', 'hr.employee.public'):
            model = self.env_for(self.viewer)[model_name]
            metadata = model.fields_get()
            for field in restricted:
                self.assertNotIn(field, metadata)
                with self.assertRaises(AccessError):
                    model.browse(self.emp_b.id).read([field])
            for operation in (
                lambda: model.search([('mobile_phone', '=', '0900000002')]),
                lambda: model.search_count([('mobile_phone', '=', '0900000002')]),
                lambda: model.search([], order='mobile_phone'),
            ):
                with self.assertRaises(AccessError):
                    operation()
            work = model.browse(self.emp_b.id).read(['name', 'work_phone', 'work_phone_formatted',
                                                     'work_email', 'avatar_128', 'user_id', 'resource_id'])
            self.assertEqual(work[0]['name'], self.emp_b.name)
            self.assertEqual(self.env_for(self.manager)[model_name].browse(self.emp_b.id).mobile_phone,
                             '0900000002')
        profile = self.env_for(self.viewer)['res.users'].tp_get_my_profile()
        self.assertTrue(profile['has_employee'])

    def test_employee_proxy_export_cannot_bypass_directory_guard(self):
        (self.viewer | self.manager).write({'group_ids': [Command.link(self.env.ref('base.group_allow_export').id)]})
        for model_name in ('hr.employee', 'hr.employee.public'):
            colleague = self.env_for(self.viewer)[model_name].browse(self.emp_b.id)
            with self.assertRaises(AccessError):
                colleague.export_data(['name', 'work_email'])
        self.assertEqual(self.env_for(self.manager)['hr.employee'].browse(self.emp_b.id)
                         .export_data(['name'])['datas'], [[self.emp_b.name]])

    def test_personal_resume_and_certificate_follow_owner(self):
        own, other = self.env['hr.resume.line'].create([
            {'employee_id': employee.id, 'name': 'Personal resume', 'date_start': '2026-01-01',
             'description': '<p>Private details</p>', 'certificate_file': 'cHJpdmF0ZQ=='}
            for employee in (self.emp_a, self.emp_b)
        ])
        resumes = self.env_for(self.viewer)['hr.resume.line']
        self.assertEqual(resumes.search([('id', 'in', (own | other).ids)]).ids, own.ids)
        self.assertIn(bytes(resumes.browse(own.id).certificate_file), (b'cHJpdmF0ZQ==', b'private'))
        with self.assertRaises(AccessError):
            resumes.browse(other.id).read(['description', 'certificate_file'])
        self.viewer.write({'group_ids': [Command.link(self.env.ref('base.group_allow_export').id)]})
        self.assertEqual(resumes.browse(own.id).export_data(['name'])['datas'], [['Personal resume']])
        with self.assertRaises(AccessError):
            resumes.browse(other.id).export_data(['description'])
        self.assertEqual(self.env_for(self.manager)['hr.resume.line'].search_count(
            [('id', 'in', (own | other).ids)]), 2)
