import importlib.util
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

from .test_hr_roster import workbook
from odoo.addons.tp_organization.models.hr_employee import (
    CODE_MAX,
    CODE_MIN,
    code_number,
)


@tagged('post_install', '-at_install')
class TestEmployeeCorrection(TransactionCase):
    """HR-CORRECTION-008 TP codes and HR-DELETE-010 permanent deletion core (synthetic data)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee'].with_context(active_test=False)
        cls.sequence = cls.Employee._tp_code_sequence()
        # nextval/setval are not transactional: put the sequence back after the class.
        cls.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % cls.sequence.id)
        state = cls.cr.fetchone()
        cls.addClassCleanup(cls._restore_sequence, cls.sequence.id, *state)
        cls.admin = cls.env['res.users'].create({
            'name': 'Synthetic Correction Admin', 'login': 'hr008.synthetic.admin',
            'group_ids': [Command.set([cls.env.ref('base.group_system').id, cls.env.ref('hr.group_hr_manager').id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Synthetic Correction HR Manager', 'login': 'hr008.synthetic.manager',
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_manager').id])],
        })

    @classmethod
    def _restore_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    def setUp(self):
        super().setUp()
        # Codes taken by earlier tests (any class, any run) were rolled back with them, but nextval
        # is not: start every test with the sequence on the floor, as the upgrade leaves it, so
        # expectations do not depend on test order. The class cleanup restores the original state.
        self.Employee._tp_reset_code_sequence(self.Employee._tp_code_floor())

    def manual(self, name, **values):
        return self.Employee.with_user(self.admin).create({'name': name, **values})

    def linked(self, name, user):
        # A personal account is linked by the account flow (TP HR Workspace forbids user_id on a
        # plain create); outside it a superuser link stands in for an already provisioned account.
        employee = self.manual(name)
        employee.sudo().user_id = user
        return employee

    def number(self, employee):
        return code_number(employee.tp_employee_code)

    # ------------------------------------------------------------------
    # TP codes
    # ------------------------------------------------------------------
    def test_next_code_follows_highest_valid_code(self):
        # The upgrade moved the sequence back into the band (never 20000+).
        self.assertTrue(CODE_MIN <= self.Employee._tp_sequence_next(self.sequence) <= CODE_MAX)
        floor = self.Employee._tp_code_floor()
        first = self.manual('Synthetic Next One')
        self.assertEqual(first.tp_employee_code, f'TP{floor}')
        self.assertNotEqual(self.number(first), first.id + CODE_MIN)
        second = self.manual('Synthetic Next Two')
        self.assertEqual(self.number(second), floor + 1)

    def test_legacy_sequence_value_is_ignored(self):
        floor = self.Employee._tp_code_floor()
        self.Employee._tp_reset_code_sequence(20000)
        employee = self.manual('Synthetic Legacy Sequence')
        self.assertEqual(employee.tp_employee_code, f'TP{floor}')
        # A sequence behind the issued codes is moved forward, not reused.
        self.Employee._tp_reset_code_sequence(CODE_MIN)
        self.assertEqual(self.number(self.manual('Synthetic Behind Sequence')), floor + 1)

    def test_archived_explicit_and_deleted_codes_are_skipped(self):
        floor = self.Employee._tp_code_floor()
        archived = self.Employee.create({'name': 'Synthetic Archived Code', 'tp_employee_code': f'TP{floor + 4}'})
        archived.active = False
        self.assertEqual(self.number(self.manual('Synthetic After Archived')), floor + 5)
        mistaken = self.manual('Synthetic Deleted Code')
        deleted_code = mistaken.tp_employee_code
        self.delete(mistaken, 'Synthetic duplicate entry')
        # Even if the sequence is moved back, a code recorded by a deletion is not issued again.
        self.Employee._tp_reset_code_sequence(code_number(deleted_code))
        self.assertGreater(self.number(self.manual('Synthetic After Deleted')), code_number(deleted_code))

    def test_rollover_band_end_and_string_order(self):
        if self.Employee._tp_code_floor() <= 10099:
            self.Employee.create({'name': 'Synthetic TP10099', 'tp_employee_code': 'TP10099'})
            self.assertEqual(self.manual('Synthetic Rollover').tp_employee_code, 'TP10100')
        floor = self.Employee._tp_code_floor()
        # TP2xxxx and longer codes never count as the highest code (numeric, in band).
        self.Employee.create([{'name': 'Synthetic Out Of Band', 'tp_employee_code': 'TP990001'},
                              {'name': 'Synthetic Wrong Band', 'tp_employee_code': 'TP20050'}])
        self.assertEqual(self.Employee._tp_code_floor(), floor)
        self.assertEqual(self.number(self.manual('Synthetic After Out Of Band')), floor)
        self.Employee.create({'name': 'Synthetic Band End', 'tp_employee_code': f'TP{CODE_MAX}'})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.manual('Synthetic Exhausted')

    def test_rolled_back_allocation_never_reuses_a_code(self):
        with self.assertRaises(UserError), self.cr.savepoint():
            first = self.manual('Synthetic Rolled Back')
            used = first.tp_employee_code
            msg = 'Synthetic failure after allocation'
            raise UserError(msg)
        second = self.manual('Synthetic After Rollback')
        self.assertNotEqual(second.tp_employee_code, used)
        self.assertGreater(self.number(second), code_number(used))

    def test_roster_and_manual_codes_do_not_overwrite_each_other(self):
        floor = self.Employee._tp_code_floor()
        source = floor + 3 - 10000
        batch = self.env['tp.hr.import.batch'].create({'file_data': BinaryBytes(workbook([[1, source, 'Synthetic Roster In Band', source, '']])),
                                                       'file_name': 'synthetic.xlsx'})
        batch.action_preview()
        batch.action_apply()
        imported = batch.line_ids.employee_id
        self.assertEqual(imported.tp_employee_code, f'TP{floor + 3}')
        # The imported code raised the high-water mark: the next manual code is after it.
        self.assertEqual(self.number(self.manual('Synthetic Manual After Import')), floor + 4)
        manual = self.manual('Synthetic Manual Before Import')
        clash = self.number(manual) - 10000
        conflict = self.env['tp.hr.import.batch'].create({'file_data': BinaryBytes(workbook([[1, clash, 'Synthetic Other Identity', clash, '']])),
                                                          'file_name': 'synthetic.xlsx'})
        conflict.action_preview()
        self.assertEqual(conflict.line_ids.action, 'conflict')
        conflict.action_apply()
        self.assertFalse(conflict.line_ids.employee_id)
        self.assertEqual(manual.name, 'Synthetic Manual Before Import')
        self.assertFalse(manual.tp_source_code)

    def test_code_change_only_through_internal_correction(self):
        employee = self.manual('Synthetic Fixed Code')
        code = employee.tp_employee_code
        for actor in (self.admin, self.manager):
            with self.assertRaises(UserError):
                employee.with_user(actor).write({'tp_employee_code': 'TP19998'})
        with self.assertRaises(UserError):
            employee.sudo().with_context(_tp_code_correction=True).write({'tp_employee_code': 'TP19998'})
        employee.invalidate_recordset()
        self.assertEqual(employee.tp_employee_code, code)

    def test_migration_maps_only_unused_legacy_manual_codes(self):
        floor = self.Employee._tp_code_floor()
        untouched = self.manual('Synthetic Band Code')
        legacy = self.Employee.create({'name': 'Synthetic Legacy Manual', 'tp_employee_code': 'TP20001'})
        linked = self.Employee.create({'name': 'Synthetic Legacy Linked', 'tp_employee_code': 'TP20002'})
        report = self.Employee.create({'name': 'Synthetic Legacy Report', 'tp_employee_code': 'TP20003', 'parent_id': linked.id})
        stranger = self.Employee.create({'name': 'Synthetic Not Legacy', 'tp_employee_code': 'TP29999'})
        before = {employee.id: employee.tp_employee_code for employee in self.Employee.search([])}
        self.Employee._tp_reset_code_sequence(20004)  # what the old sequence had issued
        path = get_module_path('tp_organization') + '/migrations/20.0.2.1.0/post-migrate.py'
        spec = importlib.util.spec_from_file_location('tp_organization_hr008_migration', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.cr, '20.0.2.0.0')
        self.Employee.invalidate_model()
        after = {employee.id: employee.tp_employee_code for employee in self.Employee.search([])}
        changed = {employee_id: (before[employee_id], code) for employee_id, code in after.items() if before[employee_id] != code}
        # Only unused manual codes of the issued legacy range move; IDs and links are kept.
        self.assertEqual(changed, {legacy.id: ('TP20001', f'TP{floor + 1}'), report.id: ('TP20003', f'TP{floor + 2}')})
        self.assertEqual((linked.tp_employee_code, stranger.tp_employee_code), ('TP20002', 'TP29999'))
        self.assertEqual(report.parent_id, linked)
        self.assertEqual(untouched.tp_employee_code, f'TP{floor}')
        audit = self.env['tp.hr.employee.audit'].search([('employee_ref', '=', legacy.id)])
        self.assertEqual((audit.action, audit.employee_code, audit.new_code), ('code_correction', 'TP20001', f'TP{floor + 1}'))
        self.assertTrue(CODE_MIN <= self.Employee._tp_sequence_next(self.sequence) <= CODE_MAX)
        self.assertEqual(self.number(self.manual('Synthetic After Migration')), floor + 3)

    # ------------------------------------------------------------------
    # HR-DELETE-010: permanent deletion core (password/accounts: tp_hr_workspace)
    # ------------------------------------------------------------------
    def delete(self, employees, reason='Synthetic permanent delete', actor=None):
        """The guarded core path used by the dialog after the password check."""
        employees = employees.with_user(actor or self.admin).with_context(active_test=False)
        employees._tp_check_permanent_delete_rights()
        employees._tp_delete_lock()
        plan = employees._tp_delete_plan()
        vals = [{'action': 'permanent_delete', 'employee_ref': employee.id, 'employee_name': employee.name,
                 'employee_code': employee.tp_employee_code, 'source_code': employee.tp_source_code,
                 'company_id': employee.company_id.id, 'reason': reason, 'snapshot': {}} for employee in employees.sudo()]
        return employees._tp_permanent_unlink(plan, vals)

    def test_permanent_delete_removes_profile_and_owned_rows(self):
        employee = self.manual('Synthetic Permanent Entry')
        employee.message_post(body='Synthetic note on the profile', message_type='comment')
        employee.activity_schedule('mail.mail_activity_data_todo', summary='Synthetic follow up', user_id=self.admin.id)
        file = self.env['ir.attachment'].create({'name': 'synthetic.txt', 'raw': b'x', 'res_model': 'hr.employee', 'res_id': employee.id})
        version = employee.version_id
        version.message_post(body='Synthetic note on the version', message_type='comment')
        version_file = self.env['ir.attachment'].create({'name': 'synthetic-version.txt', 'raw': b'y', 'res_model': 'hr.version', 'res_id': version.id})
        self.env['ir.model.data'].create({'module': '__synthetic__', 'name': f'hr010_version_{version.id}', 'model': 'hr.version', 'res_id': version.id})
        partner, resource, code, ref = employee.work_contact_id, employee.resource_id, employee.tp_employee_code, employee.id
        plan = employee._tp_delete_plan()['employees'][ref]
        self.assertFalse(plan['block'], 'auto sidecars, chatter and files never block')
        labels = ' '.join(label for label, _value in plan['delete'])
        self.assertIn('Phiên bản hồ sơ', labels)
        self.assertIn('Tệp đính kèm', labels)
        self.delete(employee, 'Synthetic duplicate manual entry')
        Employee = self.env['hr.employee'].with_context(active_test=False)
        self.assertFalse(Employee.search([('id', '=', ref)]), 'gone from active and archived lists')
        self.assertFalse(Employee.search_count([('tp_employee_code', '=', code)]))
        self.assertFalse(resource.exists() or version.exists() or file.exists() or version_file.exists())
        for model, res_id in (('hr.employee', ref), ('hr.version', version.id)):
            self.assertFalse(self.env['mail.message'].sudo().search_count([('model', '=', model), ('res_id', '=', res_id)]), model)
            self.assertFalse(self.env['mail.followers'].sudo().search_count([('res_model', '=', model), ('res_id', '=', res_id)]), model)
            self.assertFalse(self.env['mail.activity'].sudo().search_count([('res_model', '=', model), ('res_id', '=', res_id)]), model)
            self.assertFalse(self.env['ir.attachment'].sudo().search_count([('res_model', '=', model), ('res_id', '=', res_id)]), model)
            self.assertFalse(self.env['ir.model.data'].sudo().search_count([('model', '=', model), ('res_id', '=', res_id)]), model)
        self.assertFalse(partner.exists(), 'an unused private work contact goes with the profile')
        self.assertTrue(self.admin.exists() and self.admin.active)
        audit = self.env['tp.hr.employee.audit'].with_user(self.admin).search([('employee_ref', '=', ref)])
        self.assertEqual((audit.action, audit.employee_code, audit.employee_name, audit.actor_id),
                         ('permanent_delete', code, 'Synthetic Permanent Entry', self.admin))
        self.assertEqual(audit.snapshot['work_contact'], 'Đã xóa')
        with self.assertRaises(AccessError):
            audit.with_user(self.admin).write({'reason': 'tamper'})
        with self.assertRaises(AccessError):
            audit.with_user(self.admin).unlink()
        with self.assertRaises(AccessError):
            self.env['tp.hr.employee.audit'].create({'action': 'permanent_delete', 'employee_ref': 1, 'reason': 'forged', 'company_id': self.env.company.id})

    def test_archived_and_imported_profiles_are_deleted_import_trace_kept(self):
        archived = self.manual('Synthetic Archived Permanent')
        archived.action_archive()
        batch = self.env['tp.hr.import.batch'].create({'file_data': BinaryBytes(workbook([[1, 981201, 'Synthetic Imported Permanent', 981201, '']])),
                                                       'file_name': 'synthetic.xlsx'})
        batch.action_preview()
        batch.action_apply()
        line = batch.line_ids
        imported = line.employee_id
        source, code = imported.tp_source_code, imported.tp_employee_code
        plan = (archived | imported)._tp_delete_plan()['employees']
        self.assertFalse(plan[archived.id]['block'] or plan[imported.id]['block'], 'Excel source and archive never block')
        self.assertIn('Dòng nhập', ' '.join(label for label, _value in plan[imported.id]['keep']))
        self.delete(archived | imported, 'Synthetic batch of archived and imported')
        self.assertFalse(archived.exists() or imported.exists())
        self.assertTrue(batch.exists() and line.exists() and batch.file_data, 'import batch, line and file stay')
        self.assertFalse(line.employee_id)
        self.assertEqual(line.source_code, source)
        audit = self.env['tp.hr.employee.audit'].search([('employee_code', '=', code)])
        self.assertEqual((audit.source_code, audit.snapshot['import_lines']), (source, [[line.id, batch.id]]))
        # The same identity in a new file is a conflict, never a silent re-creation.
        again = self.env['tp.hr.import.batch'].create({'file_data': BinaryBytes(workbook([[1, 981201, 'Synthetic Imported Permanent', 981201, '']])),
                                                       'file_name': 'synthetic-again.xlsx'})
        again.action_preview()
        self.assertEqual(again.line_ids.action, 'conflict')
        self.assertIn('đã xóa vĩnh viễn', again.line_ids.detail)
        again.action_apply()
        self.assertFalse(again.line_ids.employee_id)
        self.assertFalse(self.Employee.search([('tp_source_code', '=', source)]))

    def test_deleted_code_is_never_issued_again(self):
        employee = self.manual('Synthetic Retired Code')
        code = employee.tp_employee_code
        self.delete(employee)
        self.Employee._tp_reset_code_sequence(code_number(code))
        self.assertGreater(self.number(self.manual('Synthetic After Retired')), code_number(code))
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Employee.create({'name': 'Synthetic Reused Code', 'tp_employee_code': code})

    def test_native_and_unauthorized_deletion_are_blocked(self):
        employee = self.manual('Synthetic Guarded Entry')
        with self.assertRaises(UserError):
            employee.unlink()
        with self.assertRaises(UserError):
            employee.sudo().unlink()
        with self.assertRaises(UserError):
            employee.with_context(_tp_employee_delete=True).unlink()
        with self.assertRaises(AccessError):
            employee.with_user(self.manager)._tp_check_permanent_delete_rights()
        system_only = self.env['res.users'].create({
            'name': 'Synthetic System Only', 'login': 'hr010.synthetic.system',
            'group_ids': [Command.set([self.env.ref('base.group_system').id])],
        })
        if not system_only.has_group('hr.group_hr_manager'):
            with self.assertRaises(AccessError):
                employee.with_user(system_only)._tp_check_permanent_delete_rights()
        foreign_company = self.env['res.company'].create({'name': 'Synthetic Foreign Delete Co'})
        foreign = self.Employee.create({'name': 'Synthetic Foreign Entry', 'company_id': foreign_company.id})
        self.admin.write({'company_ids': [Command.link(foreign_company.id)]})
        with self.assertRaises(AccessError):
            foreign.with_user(self.admin)._tp_check_permanent_delete_rights()
        self.assertTrue(employee.exists() and foreign.exists())

    def test_independent_links_block_with_resolution_hint(self):
        manager = self.manual('Synthetic Referenced Manager')
        report = self.manual('Synthetic Report', parent_id=manager.id)
        self.env['hr.department'].create({'name': 'Synthetic Head Unit', 'manager_id': manager.id})
        user = self.env['res.users'].create({'name': 'Synthetic With Account', 'login': 'hr010.synthetic.linked'})
        with_account = self.linked('Synthetic With Account', user)
        plan = (manager | with_account)._tp_delete_plan()
        blocks = plan['employees'][manager.id]['block']
        hints = ' '.join(hint for _label, _count, hint in blocks)
        self.assertIn('đổi người quản lý', hints)
        self.assertIn('đổi quản lý phòng ban', hints)
        self.assertFalse(plan['employees'][with_account.id]['block'], 'the account is decided in the dialog, not here')
        self.assertFalse(plan['partners'][str(with_account.work_contact_id.id)]['delete'], 'account contact is kept')
        with self.assertRaises(UserError):
            self.delete(manager | with_account)
        self.assertTrue(manager.exists() and with_account.exists() and report.parent_id == manager)
        self.assertFalse(self.env['tp.hr.employee.audit'].search([('employee_ref', 'in', (manager | with_account).ids)]))
        report.parent_id = False
        self.env['hr.department'].search([('manager_id', '=', manager.id)]).manager_id = False
        # Odoo keeps the former manager as coach: still a link to resolve first.
        hints = ' '.join(hint for _label, _count, hint in manager._tp_delete_plan()['employees'][manager.id]['block'])
        self.assertIn('đổi người hướng dẫn', hints)
        report.coach_id = False
        self.delete(manager | with_account)
        self.assertFalse(manager.exists() or with_account.exists())
        self.assertTrue(user.exists() and user.active and user.partner_id.exists(), 'the account and its contact stay')

    def test_batch_rolls_back_mid_process(self):
        free = self.manual('Synthetic Free Entry')
        other = self.manual('Synthetic Second Free')
        Audit = self.env['tp.hr.employee.audit']
        with patch.object(self.registry['resource.resource'], 'unlink', autospec=True, side_effect=RuntimeError('Synthetic failure')):
            with self.assertRaises(RuntimeError), self.cr.savepoint():
                self.delete(free | other, 'Synthetic mid-process failure')
        self.Employee.invalidate_model()
        self.assertTrue(free.exists() and other.exists())
        self.assertFalse(Audit.search([('employee_ref', 'in', (free | other).ids)]))
        self.delete(free | other, 'Synthetic batch ok')
        self.assertEqual(len(Audit.search([('employee_ref', 'in', [free.id, other.id])])), 2)

    def test_archive_keeps_account_state(self):
        user = self.env['res.users'].create({'name': 'Synthetic Archive Entry', 'login': 'hr008.synthetic.archive'})
        employee = self.linked('Synthetic Archive Entry', user)
        employee.with_user(self.manager).action_archive()
        self.assertFalse(employee.active)
        self.assertTrue(user.active)
        employee.with_user(self.manager).action_unarchive()
        self.assertTrue(employee.active)
