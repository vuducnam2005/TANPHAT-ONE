import importlib.util
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError
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
    """HR-CORRECTION-008: TP code allocation and deletion of mistaken entries (synthetic data)."""

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
        mistaken.with_user(self.admin)._tp_delete_mistaken('Synthetic duplicate entry')
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
    # Delete a mistaken entry vs archive
    # ------------------------------------------------------------------
    def test_admin_deletes_unused_manual_entry_with_durable_audit(self):
        employee = self.manual('Synthetic Mistaken Entry')
        self.assertFalse(employee._tp_deletion_blockers(), 'auto sidecars (resource, first version, avatar, log) must not block')
        partner, resource, code, ref = employee.work_contact_id, employee.resource_id, employee.tp_employee_code, employee.id
        with self.assertRaises(UserError):
            employee.with_user(self.admin)._tp_delete_mistaken('   ')
        count = employee.with_user(self.admin)._tp_delete_mistaken('Synthetic duplicate manual entry')
        self.assertEqual(count, 1)
        self.assertFalse(employee.exists())
        self.assertFalse(resource.exists())
        self.assertTrue(partner.exists(), 'the shared work contact is never cascaded')
        self.assertTrue(self.admin.exists() and self.admin.active)
        audit = self.env['tp.hr.employee.audit'].with_user(self.admin).search([('employee_ref', '=', ref)])
        self.assertEqual((audit.action, audit.employee_code, audit.employee_name, audit.actor_id),
                         ('delete', code, 'Synthetic Mistaken Entry', self.admin))
        self.assertEqual(audit.snapshot['work_contact_id'], partner.id)
        with self.assertRaises(AccessError):
            audit.with_user(self.admin).write({'reason': 'tamper'})
        with self.assertRaises(AccessError):
            audit.with_user(self.admin).unlink()
        with self.assertRaises(AccessError):
            self.env['tp.hr.employee.audit'].create({'action': 'delete', 'employee_ref': 1, 'reason': 'forged', 'company_id': self.env.company.id})

    def test_native_and_unauthorized_deletion_are_blocked(self):
        employee = self.manual('Synthetic Guarded Entry')
        with self.assertRaises(UserError):
            employee.unlink()
        with self.assertRaises(UserError):
            employee.with_context(_tp_employee_delete=True).unlink()
        with self.assertRaises(AccessError):
            employee.with_user(self.manager)._tp_delete_mistaken('Synthetic not admin')
        foreign_company = self.env['res.company'].create({'name': 'Synthetic Foreign Delete Co'})
        foreign = self.Employee.create({'name': 'Synthetic Foreign Entry', 'company_id': foreign_company.id})
        self.admin.write({'company_ids': [Command.link(foreign_company.id)]})
        with self.assertRaises(AccessError):
            foreign.with_user(self.admin)._tp_delete_mistaken('Synthetic other company')
        self.assertTrue(employee.exists() and foreign.exists())

    def test_used_records_are_blocked_with_reasons(self):
        user = self.env['res.users'].create({'name': 'Synthetic With Account', 'login': 'hr008.synthetic.linked'})
        with_account = self.linked('Synthetic With Account', user)
        manager = self.manual('Synthetic Referenced Manager')
        self.manual('Synthetic Report', parent_id=manager.id)
        department = self.env['hr.department'].create({'name': 'Synthetic Head Unit', 'manager_id': manager.id})
        noted = self.manual('Synthetic With Note')
        noted.message_post(body='Synthetic business note', message_type='comment')
        attached = self.manual('Synthetic With File')
        self.env['ir.attachment'].create({'name': 'synthetic.txt', 'raw': b'x', 'res_model': 'hr.employee', 'res_id': attached.id})
        batch = self.env['tp.hr.import.batch'].create({'file_data': BinaryBytes(workbook([[1, 981101, 'Synthetic Imported', 981101, '']])),
                                                       'file_name': 'synthetic.xlsx'})
        batch.action_preview()
        batch.action_apply()
        imported = batch.line_ids.employee_id
        blockers = (with_account | manager | noted | attached | imported)._tp_deletion_blockers()
        self.assertIn('hr008.synthetic.linked', ' '.join(blockers[with_account.id]))
        self.assertTrue(any('Phòng ban' in reason or department._description in reason for reason in blockers[manager.id]))
        self.assertTrue(blockers[noted.id] and blockers[attached.id])
        self.assertIn('981101', ' '.join(blockers[imported.id]))
        for employee in (with_account, manager, noted, attached, imported):
            with self.assertRaises(UserError) as error:
                employee.with_user(self.admin)._tp_delete_mistaken('Synthetic should be blocked')
            self.assertIn('Lưu trữ nhân viên', str(error.exception))
            self.assertTrue(employee.exists())
        self.assertTrue(user.exists() and user.active)

    def test_batch_is_all_or_nothing_and_rolls_back_mid_process(self):
        free = self.manual('Synthetic Free Entry')
        used = self.manual('Synthetic Used Entry')
        used.message_post(body='Synthetic work note', message_type='comment')
        with self.assertRaises(UserError):
            (free | used).with_user(self.admin)._tp_delete_mistaken('Synthetic batch')
        self.assertTrue(free.exists() and used.exists())
        Audit = self.env['tp.hr.employee.audit']
        other = self.manual('Synthetic Second Free')
        with patch.object(self.registry['resource.resource'], 'unlink', autospec=True, side_effect=RuntimeError('Synthetic failure')):
            with self.assertRaises(RuntimeError), self.cr.savepoint():
                (free | other).with_user(self.admin)._tp_delete_mistaken('Synthetic mid-process failure')
        self.Employee.invalidate_model()
        self.assertTrue(free.exists() and other.exists())
        self.assertFalse(Audit.search([('employee_ref', 'in', (free | other).ids)]))
        self.assertEqual((free | other).with_user(self.admin)._tp_delete_mistaken('Synthetic batch ok'), 2)
        self.assertEqual(len(Audit.search([('employee_ref', 'in', [free.id, other.id])])), 2)

    def test_archive_keeps_account_state(self):
        user = self.env['res.users'].create({'name': 'Synthetic Archive Entry', 'login': 'hr008.synthetic.archive'})
        employee = self.linked('Synthetic Archive Entry', user)
        employee.with_user(self.manager).action_archive()
        self.assertFalse(employee.active)
        self.assertTrue(user.active)
        employee.with_user(self.manager).action_unarchive()
        self.assertTrue(employee.active)
