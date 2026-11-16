from io import BytesIO

from openpyxl import Workbook
from psycopg2.errors import UniqueViolation

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

from odoo.addons.tp_organization.models.roster_parser import employee_code, parse_roster


def workbook(rows, repeat=True):
    book = Workbook()
    sheet = book.active
    sheet.append(['STT', 'Mã nhân viên', 'Tên nhân viên', 'ID', 'Chức vụ'])
    sheet.append(['Synthetic Unit'])
    for row in rows:
        sheet.append(row)
    if repeat:
        other = book.create_sheet('Week 2')
        for row in sheet.values:
            other.append(row)
    output = BytesIO()
    book.save(output)
    return output.getvalue()


@tagged('post_install', '-at_install')
class TestHrRoster(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Batch = cls.env['tp.hr.import.batch']

    def batch(self, rows):
        return self.Batch.create({'file_data': BinaryBytes(workbook(rows)), 'file_name': 'synthetic.xlsx'})

    def test_parser_duplicates_unicode_and_codes(self):
        result = parse_roster(workbook([[1, 1, 'Nhân viên giả', 1, 'TV'], [1, 60, 'Test Second', 60, '']]))
        self.assertEqual(len(result['rows']), 2)
        self.assertEqual(result['row_count'], 4)
        self.assertEqual(employee_code(1), 'TP10001')
        self.assertEqual(employee_code(60), 'TP10060')
        for invalid in (None, '', -1, 1.5, 0, 'nan'):
            with self.assertRaises(ValueError):
                employee_code(invalid)
        conflict = parse_roster(workbook([[1, 1, 'Test', 2, '']]))
        self.assertFalse(conflict['rows'])
        self.assertEqual(len(conflict['errors']), 2)
        invalid = parse_roster(workbook([[1, -1, 'Synthetic invalid source', -1, '']]))
        self.assertEqual(invalid['row_count'], 2)
        self.assertEqual(len(invalid['errors']), 2)
        with self.assertRaises(ValueError):
            parse_roster(b'corrupt')

    def test_preview_apply_retry_and_archive(self):
        batch = self.batch([[1, 981001, 'Synthetic Roster One', 981001, 'TV']])
        before = self.env['hr.employee'].search_count([])
        batch.action_preview()
        self.assertEqual(self.env['hr.employee'].search_count([]), before)
        batch.action_apply()
        employee = batch.line_ids.employee_id
        self.assertEqual(employee.tp_employee_code, 'TP991001')
        self.assertEqual(employee.tp_source_title, 'TV')
        self.assertFalse(employee.job_id)
        self.assertFalse(employee.tp_personal_defaults_confirmed)
        self.assertFalse(employee.tp_wage_confirmed)
        versions = employee.version_ids
        batch.action_apply()
        second = self.batch([[1, 981001, 'Synthetic Roster One', 981001, 'TV']])
        second.action_preview()
        second.action_apply()
        self.assertEqual(second.line_ids.employee_id, employee)
        self.assertEqual(employee.version_ids, versions)
        employee.active = False
        with self.assertRaises(UserError):
            employee.unlink()
        with self.assertRaises(UserError):
            employee.load_demo_data()
        with self.assertRaises(UniqueViolation), self.cr.savepoint():
            self.env['hr.employee'].create({'name': 'Duplicate', 'tp_employee_code': employee.tp_employee_code})

    def test_delta_review_and_manual_changes(self):
        first = self.batch([[1, 981002, 'Synthetic Two', 981002, 'Old']])
        first.action_preview()
        first.action_apply()
        employee = first.line_ids.employee_id
        changed = self.batch([[1, 981002, 'Synthetic Two', 981002, 'New']])
        changed.action_preview()
        self.assertEqual(changed.line_ids.action, 'update')
        changed.line_ids.review_update = True
        changed.action_apply()
        self.assertEqual(employee.tp_source_title, 'New')
        employee.name = 'Manual correction'
        third = self.batch([[1, 981002, 'Synthetic Two', 981002, 'Another']])
        third.action_preview()
        third.line_ids.review_update = True
        third.action_apply()
        self.assertEqual(third.line_ids.action, 'conflict')
        self.assertEqual(employee.name, 'Manual correction')

    def test_state_and_preview_tamper_guards(self):
        batch = self.batch([[1, 981003, 'Synthetic Three', 981003, '']])
        with self.assertRaises(AccessError):
            batch.write({'state': 'applied'})
        batch.action_preview()
        with self.assertRaises(AccessError):
            batch.line_ids.write({'source_code': '99'})
        with self.assertRaises(UserError):
            batch.write({'file_data': BinaryBytes(b'changed')})
        with self.assertRaises(AccessError):
            self.env['tp.hr.import.line'].create({'batch_id': batch.id, 'name': 'Injected'})

    def test_manual_sequence_and_company_scope(self):
        first = self.env['hr.employee'].create({'name': 'Synthetic Manual'})
        first.active = False
        second = self.env['hr.employee'].create({'name': 'Synthetic Manual Second'})
        self.assertNotEqual(first.tp_employee_code, second.tp_employee_code)
        self.assertTrue(first.tp_employee_code.startswith('TP'))
        staff = self.env['res.users'].create({'name': 'Synthetic Directory', 'login': 'synthetic.hr.directory', 'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.assertEqual(self.env['hr.employee.public'].with_user(staff).browse(second.id).tp_employee_code, second.tp_employee_code)
        with self.assertRaises(AccessError):
            self.Batch.with_user(staff).search_read([], ['checksum'])
        with self.assertRaises(AccessError):
            second.with_user(staff).read(['tp_source_code'])

    def test_private_version_wage_files_and_company(self):
        def actor(login, group):
            return self.env['res.users'].create({'name': login, 'login': login,
                'group_ids': [(6, 0, [self.env.ref(group).id])]})
        officer = actor('synthetic.hr.officer', 'hr.group_hr_user')
        manager = actor('synthetic.hr.manager', 'hr.group_hr_manager')
        staff = actor('synthetic.hr.staff', 'base.group_user')
        employee = self.env['hr.employee'].create({'name': 'Synthetic Private', 'private_email': 'private@example.invalid', 'wage': 123})
        version = employee.current_version_id
        self.assertEqual(version.with_user(manager).read(['wage'])[0]['wage'], 123)
        self.assertFalse(version.tp_personal_defaults_confirmed)
        self.assertFalse(version.tp_wage_confirmed)
        with self.assertRaises(AccessError):
            version.with_user(officer).read(['tp_wage_confirmed'])
        with self.assertRaises(AccessError):
            version.with_user(staff).read(['tp_personal_defaults_confirmed'])
        version.with_user(manager).write({'tp_wage_confirmed': True, 'wage': 0})
        self.assertEqual(version.with_user(manager).read(['wage', 'tp_wage_confirmed'])[0]['wage'], 0)
        with self.assertRaises(AccessError):
            version.with_user(officer).read(['wage'])
        with self.assertRaises(AccessError):
            version.with_user(staff).read(['wage'])
        with self.assertRaises(AccessError):
            employee.with_user(staff).read(['private_email'])
        with self.assertRaises(AccessError):
            employee.with_user(officer).write({'active': False})
        with self.assertRaises(AccessError):
            employee.resource_id.with_user(officer).write({'active': False})
        employee.resource_id.with_user(manager).write({'active': False})
        self.assertFalse(employee.active)
        employee.resource_id.with_user(manager).write({'active': True})
        employee.with_user(manager).write({'active': False})
        employee.with_user(manager).write({'active': True})
        attachment = self.env['ir.attachment'].create({'name': 'Synthetic private HR', 'res_model': 'hr.employee', 'res_id': employee.id,
            'raw': b'private synthetic file', 'mimetype': 'text/plain'})
        with self.assertRaises(AccessError):
            attachment.with_user(staff).read(['raw'])
        message = employee.message_post(body='Synthetic private HR history')
        with self.assertRaises(AccessError):
            message.with_user(staff).read(['body'])
        other_company = self.env['res.company'].create({'name': 'Synthetic Isolated HR'})
        other = self.env['hr.employee'].with_company(other_company).create({'name': 'Synthetic Other Company', 'company_id': other_company.id})
        self.assertFalse(self.env['hr.employee'].with_user(manager).search([('id', '=', other.id)]))
        with self.assertRaises(AccessError):
            other.with_user(manager).read(['private_email'])

    def test_two_previews_and_isolated_conflicts(self):
        rows = [[1, 981005, 'Synthetic Preview A', 981005, ''], [2, 981006, '', 981006, ''], [3, None, 'Missing code', 981007, '']]
        first = self.batch(rows)
        second = self.batch(rows)
        first.action_preview()
        second.action_preview()
        self.assertEqual(len(first.line_ids.filtered(lambda line: line.action == 'conflict')), 4)
        first.action_apply()
        second.action_apply()
        created = first.line_ids.filtered(lambda line: line.source_code == '981005')
        skipped = second.line_ids.filtered(lambda line: line.source_code == '981005')
        self.assertEqual(skipped.action, 'skip')
        self.assertEqual(skipped.employee_id, created.employee_id)
        self.assertTrue(skipped.source_cells)

    def test_failed_apply_rolls_back_and_retry(self):
        batch = self.batch([[1, 981008, 'Synthetic Rollback A', 981008, ''], [2, 981009, 'Synthetic Rollback B', 981009, '']])
        batch.action_preview()
        foreign = self.env['res.company'].create({'name': 'Synthetic Mapping Company'})
        department = self.env['hr.department'].with_company(foreign).create({'name': 'Synthetic Foreign Unit', 'company_id': foreign.id})
        # Company consistency rejects a malicious cross-company mapping before apply.
        with self.assertRaises(UserError), self.cr.savepoint():
            batch.line_ids[-1].department_id = department
        with self.assertRaises(UserError), self.cr.savepoint():
            batch.action_apply()
            msg = 'Synthetic downstream failure'
            raise UserError(msg)
        batch.invalidate_recordset()
        self.assertEqual(batch.state, 'preview')
        self.assertFalse(self.env['hr.employee'].search([('tp_source_code', 'in', ['981008', '981009'])]))
        batch.action_apply()
        self.assertEqual(len(batch.line_ids.employee_id), 2)
        with self.assertRaises(AccessError):
            batch.line_ids[0].write({'review_update': True})
        with self.assertRaises(AccessError):
            batch.line_ids[0].write({'department_id': False})

    def test_assigned_codes_cannot_change(self):
        manager = self.env['res.users'].create({'name': 'Synthetic Code Manager', 'login': 'synthetic.hr.code.manager', 'group_ids': [(6, 0, [self.env.ref('hr.group_hr_manager').id])]})
        employee = self.env['hr.employee'].create({'name': 'Synthetic Immutable Code'})
        with self.assertRaises(UserError):
            employee.with_user(manager).write({'tp_employee_code': 'TP99999'})
        with self.assertRaises(AccessError):
            employee.with_user(manager).write({'tp_source_code': '10'})
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(manager).create({'name': 'Synthetic spoofed source', 'tp_source_snapshot': {'name': 'injected'}})
        for invalid in ('TP1', 'TP010001', 'TP10000', 'wrong'):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.env['hr.employee'].create({'name': 'Synthetic invalid', 'tp_employee_code': invalid})

    def test_unlink_only_through_guarded_deletion_of_unimported(self):
        manager = self.env['res.users'].create({'name': 'Synthetic Cleanup Manager', 'login': 'synthetic.hr.cleanup.manager',
            'group_ids': [(6, 0, [self.env.ref('hr.group_hr_manager').id])]})
        admin = self.env.ref('base.user_admin')
        sample = self.env['hr.employee'].sudo().create({'name': 'Synthetic verified fixture'})
        self.assertFalse(sample.tp_source_code)
        with self.assertRaises(UserError):
            sample.with_user(manager).unlink()
        # HR-CORRECTION-008: no superuser shortcut; deletion is the audited admin flow.
        with self.assertRaises(UserError):
            sample.sudo().unlink()
        # HR-DELETE-010: the native unlink stays closed even for imported records;
        # permanent deletion is the password-verified admin flow (tested there).
        batch = self.batch([[1, 981010, 'Synthetic protected import', 981010, '']])
        batch.action_preview()
        batch.action_apply()
        with self.assertRaises(UserError):
            batch.line_ids.employee_id.sudo().unlink()
        with self.assertRaises(UserError):
            batch.line_ids.employee_id.with_user(admin).unlink()
        self.assertTrue(sample.exists() and batch.line_ids.employee_id.exists())

    def test_duplicate_department_requires_mapping(self):
        departments = self.env['hr.department'].create([
            {'name': 'Synthetic Unit', 'company_id': self.env.company.id},
            {'name': 'Synthetic Unit', 'company_id': self.env.company.id},
        ])
        ambiguous = self.batch([[1, 981011, 'Synthetic Ambiguous Unit', 981011, '']])
        ambiguous.action_preview()
        self.assertFalse(ambiguous.line_ids.department_id)
        self.assertEqual(ambiguous.line_ids.action, 'conflict')
        ambiguous.action_apply()
        self.assertEqual(ambiguous.line_ids.action, 'conflict')
        self.assertFalse(ambiguous.line_ids.employee_id)
        mapped = self.batch([[1, 981011, 'Synthetic Ambiguous Unit', 981011, '']])
        mapped.action_preview()
        mapped.line_ids.department_id = departments[1]
        mapped.action_apply()
        self.assertEqual(mapped.line_ids.employee_id.department_id, departments[1])

    def test_source_title_update_preserves_department_mapping(self):
        department = self.env['hr.department'].create({'name': 'Synthetic Canonical Unit', 'company_id': self.env.company.id})
        first = self.batch([[1, 981012, 'Synthetic Canonical Mapping', 981012, 'Old']])
        first.action_preview()
        first.line_ids.department_id = department
        first.action_apply()
        before = self.env['hr.department'].search_count([])
        changed = self.batch([[1, 981012, 'Synthetic Canonical Mapping', 981012, 'New']])
        changed.action_preview()
        self.assertEqual(changed.line_ids.department_id, department)
        changed.line_ids.review_update = True
        changed.action_apply()
        self.assertEqual(changed.line_ids.employee_id.department_id, department)
        self.assertEqual(changed.line_ids.employee_id.tp_source_title, 'New')
        self.assertEqual(self.env['hr.department'].search_count([]), before)
