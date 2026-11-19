from io import BytesIO

from openpyxl import load_workbook
from psycopg2.errors import UniqueViolation

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class BaseHrWorkspace(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        state = cls.env.cr.fetchone()
        cls.addClassCleanup(cls._restore_employee_sequence, sequence.id, *state)
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())
        cls.company = cls.env['res.company'].create({'name': 'Synthetic HR Company'})
        cls.other = cls.env['res.company'].create({'name': 'Synthetic Other HR'})
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic HR Unit', 'company_id': cls.company.id})
        cls.other_department = cls.env['hr.department'].create({'name': 'Synthetic Other Unit', 'company_id': cls.other.id})
        cls.hr = cls.env['res.users'].create({
            'name': 'Synthetic HR Officer', 'login': 'hr001.synthetic.officer',
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_user').id])],
        })
        cls.staff = cls.env['res.users'].create({
            'name': 'Synthetic HR Staff', 'login': 'hr001.synthetic.staff',
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.admin = cls.env.ref('base.user_admin')
        cls.admin.write({'company_ids': [Command.link(cls.company.id), Command.link(cls.other.id)]})
        cls.employees = cls.env['hr.employee'].with_company(cls.company).create([
            {'name': '=SYNTHETIC()', 'company_id': cls.company.id, 'department_id': cls.department.id},
            {'name': 'Synthetic Private', 'company_id': cls.company.id, 'department_id': cls.department.id},
            {'name': 'Synthetic Archived', 'company_id': cls.company.id, 'department_id': cls.department.id, 'active': False},
        ])
        cls.env['hr.employee'].with_company(cls.other).create({'name': 'Synthetic Other Secret', 'company_id': cls.other.id})

    @classmethod
    def _restore_employee_sequence(cls, sequence_id, last_value, is_called):
        # PostgreSQL nextval is not rolled back with synthetic employees.
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    def report(self, actor=None):
        return self.env['tp.hr.workspace'].with_user(actor or self.hr).with_context(allowed_company_ids=[self.company.id])


class TestHrWorkspace(BaseHrWorkspace):
    def test_population_filter_drilldown_parity(self):
        overview = self.report().get_overview()
        self.assertEqual(overview['total'], 2)
        self.assertEqual(sum(row['count'] for row in overview['departments']), 2)
        self.assertEqual(overview['missing_basic'], 2)
        self.assertEqual(overview['linked'] + overview['pending'], 2)
        self.assertEqual(self.report().get_overview({'status': 'archived'})['total'], 1)
        self.assertEqual(self.report().get_overview({'status': 'all'})['total'], 3)
        filtered = self.report().get_overview({'department_id': self.department.id})
        self.assertEqual(filtered['total'], len(self.env['hr.employee'].with_user(self.hr).search(filtered['domain'])))
        for invalid in ({'status': 'unknown'}, {'domain': []}, {'department_id': '1.2'}, {'department_id': True}):
            with self.assertRaises(ValidationError):
                self.report().get_overview(invalid)
        action = self.report().action_employees({'department_id': self.department.id}, [('user_id', '=', False)])
        self.assertIn(('company_id', '=', self.company.id), action['domain'])
        self.assertIn(('department_id', '=', self.department.id), action['domain'])
        self.assertEqual(action['view_id'][0], self.env.ref('tp_hr_workspace.employee_list').id)

    def test_full_table_actions_keep_scope_and_permission(self):
        versions = self.employees[0].with_user(self.hr).with_context(allowed_company_ids=[self.company.id]).action_open_versions()
        self.assertEqual(versions['domain'], [('employee_id', '=', self.employees[0].id)])
        self.assertEqual(versions['views'][0], (self.env.ref('tp_hr_workspace.version_list').id, 'list'))
        self.assertEqual(versions['view_mode'], 'list')
        self.assertEqual(len(versions['views']), 1)
        batch = self.env['tp.hr.import.batch'].create({'name': 'Synthetic table permission'})
        with self.assertRaises(AccessError):
            batch.with_user(self.staff).action_open_lines()
        self.assertEqual(batch.action_open_lines()['domain'], [('batch_id', '=', batch.id)])

    def test_report_export_scope_and_literal_text(self):
        workbook = load_workbook(BytesIO(self.report()._build_xlsx({'status': 'all'})), data_only=False)
        detail = workbook['Dữ liệu chi tiết']
        self.assertEqual(detail['C7'].value, '=SYNTHETIC()')
        self.assertEqual(detail['C7'].data_type, 's')
        self.assertEqual(detail.freeze_panes, 'D7')
        self.assertEqual(len(list(detail.iter_rows(min_row=7, max_row=9))), 3)
        self.assertNotIn('Synthetic Other Secret', str(list(detail.values)))
        self.assertEqual(workbook.sheetnames[:2], ['Danh sách nhân viên', 'Dữ liệu chi tiết'])
        workbook.close()
        with self.assertRaises(AccessError):
            self.report().get_overview({'department_id': self.other_department.id})
        with self.assertRaises(AccessError):
            self.report(self.staff).get_overview()
        with self.assertRaises(AccessError):
            self.report(self.staff)._build_xlsx()

    def test_private_fields_files_and_chatter(self):
        employee = self.employees[1]
        employee.identification_id = 'SYNTHETIC-PRIVATE'
        employee.wage = 12345
        self.assertEqual(employee.with_user(self.hr).identification_id, 'SYNTHETIC-PRIVATE')
        with self.assertRaises(AccessError):
            employee.with_user(self.hr).read(['wage'])
        with self.assertRaises(AccessError):
            employee.with_user(self.staff).read(['identification_id'])
        with self.assertRaises(AccessError):
            employee.current_version_id.with_user(self.staff).read(['identification_id'])
        attachment = self.env['ir.attachment'].create({
            'name': 'Synthetic private HR file', 'raw': b'SYNTHETIC-PRIVATE',
            'res_model': 'hr.employee', 'res_id': employee.id,
        })
        with self.assertRaises(AccessError):
            attachment.with_user(self.staff).read(['raw'])
        message = employee.message_post(body='Synthetic private HR history')
        with self.assertRaises(AccessError):
            message.with_user(self.staff).read(['body'])

    def test_hr_ui_002_account_status_and_login(self):
        emp = self.employees[0]
        self.assertFalse(emp.tp_user_login)
        self.assertEqual(emp.tp_account_status, 'unlinked')

        user = self.env['res.users'].create({
            'name': 'Synthetic Linked User',
            'login': 'hrui002.linked.test',
            'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        emp.write({'user_id': user.id})
        self.assertEqual(emp.tp_user_login, 'hrui002.linked.test')
        self.assertEqual(emp.tp_account_status, 'active')

        user.active = False
        self.assertEqual(emp.tp_account_status, 'disabled')

        user.active = True
        self.assertEqual(emp.tp_account_status, 'active')
        emp.write({'user_id': False})
        self.assertFalse(emp.tp_user_login)
        self.assertEqual(emp.tp_account_status, 'unlinked')

    def test_personal_identity_rpc_and_write_guards(self):
        emp1, emp2 = self.employees[:2]
        emp1.user_id = self.staff
        for actor in (self.hr, self.admin):
            employee = emp1.with_user(actor).with_context(allowed_company_ids=[self.company.id])
            for values in ({'user_id': False}, {'user_id': self.hr.id}, {'resource_id': emp2.resource_id.id}):
                with self.assertRaises(AccessError):
                    employee.with_context(_tp_personal_account=True).write(values)
            with self.assertRaises(AccessError):
                employee.resource_id.write({'user_id': False})
            with self.assertRaises(AccessError):
                self.env['hr.employee'].with_user(actor).with_context(allowed_company_ids=[self.company.id]).create({
                    'name': 'Synthetic blocked import', 'company_id': self.company.id, 'user_id': self.staff.id})
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({'employee_id': emp1.id})
        for action in (wizard.action_link, wizard.action_unlink):
            with self.assertRaises(AccessError):
                action()
        for method in ('action_send_invitation', 'action_copy_invitation_link', 'action_toggle_user_active', 'action_deactivate_user_and_depart'):
            with self.assertRaises(AccessError):
                getattr(emp1.with_user(self.admin), method)()
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            emp2.user_id = self.staff

    def test_hr_ui_002_reset_password_and_orm_preservation(self):
        emp = self.employees[0]
        with self.assertRaises(UserError):
            emp.with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).action_reset_user_password()

        user = self.env['res.users'].create({
            'name': 'Synthetic Reset User',
            'login': 'hrui002.reset.target',
            'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        emp.write({'user_id': user.id})
        with self.assertRaises(UserError):
            emp.with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).action_reset_user_password()

        # Verify schedule/calendar ORM field still exists and works
        self.assertIn('resource_calendar_id', emp._fields)
        self.assertTrue(emp.resource_id.exists())

    def test_hr_ui_002_department_sync_and_no_secret_leak(self):
        emp = self.employees[0]
        user = self.env['res.users'].create({
            'name': 'Synthetic Dept User',
            'login': 'hrui002.dept.user',
            'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        emp.write({'user_id': user.id})
        dept2 = self.env['hr.department'].create({'name': 'Synthetic Dept 2', 'company_id': self.company.id})
        groups_before = user.group_ids
        with self.assertRaises(AccessError):
            emp.write({'department_id': dept2.id})
        transfer = self.env['tp.hr.role.wizard'].with_user(self.admin).with_company(self.company).create({
            'employee_id': emp.id, 'change_kind': 'transfer', 'target_department_id': dept2.id,
            'reason': 'Synthetic reviewed department move',
        })
        transfer.action_preview()
        transfer.action_apply()
        self.assertEqual(user.with_company(self.company).department_id, dept2)
        self.assertEqual(user.group_ids, groups_before)

        # Verify no password or secret fields on employee read or wizard
        self.assertNotIn('password', self.env['hr.employee']._fields)
        wiz = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).create({
            'employee_id': emp.id,
            'reason': 'Verify no secret in chatter',
        })
        with self.assertRaises(AccessError):
            wiz.action_link()
        msgs = emp.message_ids.mapped('body')
        for m in msgs:
            self.assertNotIn('pbkdf2', m.lower())
            self.assertNotIn('OldActorPass', m)
        xlsx = self.report()._build_xlsx()
        self.assertNotIn(b'pbkdf2', xlsx)

    def test_hr_job_position_management(self):
        # Create job positions with sequence and department
        job_lead = self.env['hr.job'].create({
            'name': 'Synthetic Lead',
            'department_id': self.department.id,
            'company_id': self.company.id,
            'sequence': 10,
        })
        job_member = self.env['hr.job'].create({
            'name': 'Synthetic Member',
            'department_id': self.department.id,
            'company_id': self.company.id,
            'sequence': 20,
        })
        self.assertTrue(job_lead.exists())
        self.assertEqual(job_lead.no_of_employee, 0)

        # Assign job to employee
        emp = self.employees[0]
        emp.write({'job_id': job_lead.id})
        self.assertEqual(emp.job_id, job_lead)
        self.assertEqual(job_lead.no_of_employee, 1)
        self.assertIn(emp, job_lead.employee_ids)

        # Change job
        emp.write({'job_id': job_member.id})
        self.assertEqual(job_lead.no_of_employee, 0)
        self.assertEqual(job_member.no_of_employee, 1)

    def test_odoobot_silenced_and_neutralized(self):
        partner_root = self.env.ref('base.partner_root')
        odoobot_id = partner_root.id

        # 1. Partner root name and image
        self.assertEqual(partner_root.name, 'Hệ thống')
        self.assertFalse(partner_root.image_1920)

        # 2. _message_fetch filters out partner_root authored messages
        dept = self.department
        msg_bot = self.env['mail.message'].sudo().create({
            'model': 'hr.department',
            'res_id': dept.id,
            'body': 'OdooBot test noise',
            'author_id': odoobot_id,
            'message_type': 'comment',
        })
        msg_user = self.env['mail.message'].sudo().create({
            'model': 'hr.department',
            'res_id': dept.id,
            'body': 'User legit message',
            'author_id': self.admin.partner_id.id,
            'message_type': 'comment',
        })
        fetched = self.env['mail.message']._message_fetch([], thread=dept)
        fetched_ids = [m['id'] if isinstance(m, dict) else m.id for m in fetched.get('messages', [])]
        self.assertNotIn(msg_bot.id, fetched_ids)
        self.assertIn(msg_user.id, fetched_ids)

        # 3. New user defaults odoobot_state to disabled
        test_user = self.env['res.users'].create({
            'name': 'Synthetic Bot Tester',
            'login': 'bot.tester.user',
            'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])],
        })
        self.assertEqual(test_user.odoobot_state, 'disabled')
        self.assertFalse(test_user._init_odoobot())

        # 4. _get_or_create_chat with odoobot returns empty recordset
        chat = self.env['discuss.channel']._get_or_create_chat([odoobot_id, test_user.partner_id.id])
        self.assertFalse(chat)
