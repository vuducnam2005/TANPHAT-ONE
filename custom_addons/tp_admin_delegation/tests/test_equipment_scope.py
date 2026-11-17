import base64

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEquipmentDelegation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.departments = cls.env['hr.department'].create([
            {'name': name, 'company_id': cls.company.id}
            for name in ('Synthetic Equipment Own', 'Synthetic Equipment Other')
        ])
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic equipment delegate', 'login': 'synthetic.equipment.delegate',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            # Delegation preserves the existing export permission.
            'group_ids': [Command.set([cls.env.ref(xmlid).id for xmlid in (
                'base.group_user', 'base.group_allow_export')])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': cls.user.name, 'company_id': cls.company.id, 'department_id': cls.departments[0].id,
            'user_id': cls.user.id, 'date_version': fields.Date.today(),
        })
        cls.other_employee = cls.env['hr.employee'].create({
            'name': 'Synthetic equipment holder', 'company_id': cls.company.id,
            'department_id': cls.departments[1].id, 'date_version': fields.Date.today(),
        })
        cls.category = cls.env['maintenance.equipment.category'].create({'name': 'Synthetic equipment category'})
        cls.equipment = cls.env['maintenance.equipment'].create([
            {'name': name, 'company_id': cls.company.id, 'category_id': cls.category.id,
             'tp_custody': 'employee', 'tp_employee_id': employee.id, 'tp_technical_state': 'good'}
            for name, employee in [('Synthetic own device', cls.employee), ('Synthetic other device', cls.other_employee)]
        ])
        cls.equipment.action_tp_register()
        cls.stock = cls.env['maintenance.equipment'].create({
            'name': 'Synthetic stock', 'company_id': cls.company.id, 'category_id': cls.category.id,
        })

    def grant(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.user, self.company, operation, 'Synthetic equipment authority')

    def test_read_count_export_and_revoke_preserve_own_scope(self):
        own, other = self.equipment.with_user(self.user)
        with self.assertRaises(AccessError):
            other.read(['name'])
        self.grant()
        model = self.env['maintenance.equipment'].with_user(self.user)
        domain = [('id', 'in', (self.equipment | self.stock).ids)]
        self.assertEqual(model.search(domain), other)
        self.assertEqual(model.search_count(domain), 1)
        self.assertEqual(other.export_data(['name'])['datas'], [[other.name]])
        for record in own | self.stock.with_user(self.user):
            with self.assertRaises(AccessError):
                record.read(['name'])
        self.grant('revoke')
        with self.assertRaises(AccessError):
            other.read(['name'])

    def test_metadata_sudo_parent_and_bulk_cannot_change_own_or_stock(self):
        self.grant()
        own, other = self.equipment.with_user(self.user)
        other.write({'tp_brand': 'Synthetic brand'})
        self.assertEqual(other.tp_brand, 'Synthetic brand')
        with self.assertRaises((AccessError, UserError)):
            other.write({'tp_employee_id': self.employee.id})
        with self.assertRaises(AccessError):
            own.sudo().write({'tp_brand': 'Escalated'})
        with self.assertRaises(AccessError):
            (own | other).write({'tp_brand': 'Mixed bulk'})
        self.assertEqual(other.tp_brand, 'Synthetic brand')
        child = self.env['maintenance.equipment'].create({
            'name': 'Synthetic mixed source', 'company_id': self.company.id,
            'tp_custody': 'employee', 'tp_employee_id': self.other_employee.id, 'tp_parent_id': own.id,
        })
        with self.assertRaises(AccessError):
            child.with_user(self.user).read(['name'])

    def test_repair_workflow_child_scope_and_private_stream(self):
        self.grant()
        other = self.equipment[1].with_user(self.user)
        meter = self.env['tp.equipment.meter'].with_user(self.user).create({
            'equipment_id': other.id, 'value': 10,
        })
        with self.assertRaises(AccessError):
            meter.write({'equipment_id': self.equipment[0].id})
        request = self.env['maintenance.request'].with_user(self.user).create({
            'name': 'Synthetic repair', 'company_id': self.company.id, 'equipment_id': other.id,
        })
        self.assertFalse(request.employee_id)
        with self.assertRaises(AccessError):
            request.write({'employee_id': self.employee.id})
        request.action_tp_start()
        request.write({'tp_result': 'fixed', 'tp_state_after': 'good'})
        request.action_tp_done()
        self.assertEqual(request.tp_state, 'done')
        self.assertTrue(other.message_ids)
        with self.assertRaises(AccessError):
            self.equipment[0].with_user(self.user).sudo().message_post(body='Own source')
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['mail.message'].with_user(self.user).with_context(_tp_equipment_post=True).create({
                'model': 'maintenance.equipment', 'res_id': other.id, 'body': 'Forged direct log',
            })
        attachment = self.env['ir.attachment'].create({
            'name': 'synthetic-private.txt', 'res_model': 'maintenance.equipment', 'res_id': other.id,
            'datas': base64.b64encode(b'synthetic private equipment'),
        })
        self.assertEqual(attachment.with_user(self.user).read(['name'])[0]['name'], 'synthetic-private.txt')
        found = self.env['ir.binary'].with_user(self.user)._find_record(res_id=attachment.id)
        self.assertEqual(found.id, attachment.id)
        self.grant('revoke')
        with self.assertRaises(AccessError):
            self.env['ir.binary'].with_user(self.user)._find_record(res_id=attachment.id)

    def test_holder_transfer_closes_previously_read_equipment_scope(self):
        self.grant()
        other = self.equipment[1].with_user(self.user)
        self.assertTrue(other.has_access('write'))
        self.assertEqual(other.tp_employee_id.department_id, self.departments[1])
        transfer = self.env['tp.hr.role.wizard'].with_user(self.main).create({
            'employee_id': self.other_employee.id, 'change_kind': 'transfer',
            'target_department_id': self.departments[0].id, 'target_role': 'staff',
            'reason': 'Synthetic equipment holder transfer', 'acknowledge_handover': True,
        })
        transfer.action_preview()
        transfer.action_apply()
        with self.assertRaises(AccessError):
            other.write({'tp_brand': 'After holder transfer'})
        with self.assertRaises(AccessError):
            self.env['tp.equipment.meter'].with_user(self.user).create({'equipment_id': other.id, 'value': 20})
        self.assertFalse(self.equipment[1].tp_brand)
