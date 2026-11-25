# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Automated tests for enterprise request types: Leave, Business Trip, Expense Settlement Separation & Linked Task."""
from datetime import date, timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEnterpriseRequestTypes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        cls.addClassCleanup(cls._restore_sequence, sequence.id, *cls.env.cr.fetchone())
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())

        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()

        cls.dept = cls.env['hr.department'].create({
            'name': 'Phòng Kỹ thuật Cầu Đường (Test)',
            'company_id': cls.company.id,
        })
        base_group = cls.env.ref('base.group_user')
        cls.user_staff = cls._make_user('ent.req.staff', 'Kỹ sư Thiết kế (Test)', [base_group.id])
        cls.user_mgr = cls._make_user('ent.req.mgr', 'Trưởng phòng Kỹ thuật (Test)', [base_group.id])
        cls.user_fin = cls._make_user('ent.req.fin', 'Kế toán Thanh toán (Test)', [base_group.id])

        cls.emp_mgr = cls._make_employee(cls.user_mgr, cls.dept)
        cls.dept.write({'manager_id': cls.emp_mgr.id})
        cls.emp_staff = cls._make_employee(cls.user_staff, cls.dept, parent=cls.emp_mgr)
        cls.emp_fin = cls._make_employee(cls.user_fin, cls.dept, parent=cls.emp_mgr)

        cls.type_leave = cls.env.ref('tp_request.type_leave_request')
        cls.type_trip = cls.env.ref('tp_request.type_business_trip')
        cls.type_expense = cls.env.ref('tp_request.type_expense_advance')
        # Configure explicit finance executor so non-admin finance executor can confirm voucher
        cls.type_expense.with_user(cls.admin).write({
            'executor_mode': 'specific_users',
            'executor_user_ids': [Command.set([cls.user_fin.id])],
        })

    @classmethod
    def _restore_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    @classmethod
    def _make_user(cls, login, name, group_ids):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': name,
            'login': login,
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set(group_ids)],
        })

    @classmethod
    def _make_employee(cls, user, dept, parent=False):
        return cls.env['hr.employee'].create({
            'name': user.name,
            'company_id': cls.company.id,
            'department_id': dept.id,
            'parent_id': parent.id if parent else False,
            'user_id': user.id,
            'date_version': fields.Date.today(),
        })

    def test_01_leave_and_business_trip_workflow(self):
        Req = self.env['tp.request'].with_user(self.user_staff)
        d1 = date.today() + timedelta(days=3)
        d2 = d1 + timedelta(days=1)

        # Leave request submit + approve
        res_leave = Req.tp_save_request({
            'type_id': self.type_leave.id,
            'title': 'Xin nghỉ phép năm thăm gia đình',
            'description': 'Đã bàn giao hồ sơ bản vẽ cho đồng nghiệp',
            'leave_kind': 'annual',
            'leave_date_from': d1.isoformat(),
            'leave_date_to': d2.isoformat(),
            'leave_days_count': 2.0,
            'leave_handover_note': 'Kỹ sư B nhận bàn giao',
        }, submit=True)
        self.assertTrue(res_leave['ok'])
        leave_rec = self.env['tp.request'].browse(res_leave['id'])
        self.assertEqual(leave_rec.approval_state, 'pending')

        # Step 1 manager approve completes 1-step HR_LEAVE
        leave_rec.with_user(self.user_mgr).action_approve_step(note='Đồng ý cho nghỉ')
        self.assertEqual(leave_rec.approval_state, 'approved')
        self.assertEqual(leave_rec.leave_days_count, 2.0)

        # Business trip requires destination
        bad_trip = Req.tp_save_request({
            'type_id': self.type_trip.id,
            'title': 'Công tác khảo sát cầu',
            'description': 'Khảo sát địa hình',
            'leave_date_from': d1.isoformat(),
            'leave_date_to': d1.isoformat(),
            'leave_days_count': 1.0,
            'trip_destination': '',
        }, submit=True)
        self.assertFalse(bad_trip['ok'])
        self.assertTrue(any(e['id'] == 'req_trip_dest' for e in bad_trip['field_errors']))

        ok_trip = Req.tp_save_request({
            'type_id': self.type_trip.id,
            'title': 'Công tác khảo sát cầu vượt Km18',
            'description': 'Đo đạc cao độ mố trụ',
            'leave_date_from': d1.isoformat(),
            'leave_date_to': d1.isoformat(),
            'leave_days_count': 1.0,
            'trip_destination': 'Quảng Ngãi - Km18',
            'trip_transport': 'Xe công ty',
        }, submit=True)
        self.assertTrue(ok_trip['ok'])

    def test_02_mandatory_case_11_expense_approval_never_fakes_disbursement(self):
        """Case #11: Approving expense/advance sets pending_disbursement, NEVER settled_confirmed until voucher verified."""
        Req = self.env['tp.request'].with_user(self.user_staff)
        res = Req.tp_save_request({
            'type_id': self.type_expense.id,
            'title': 'Tạm ứng chi phí khảo sát địa chất tuyến ĐT.601',
            'description': 'Phục vụ thuê nhân công phụ trợ tại hiện trường',
            'needed_date': (date.today() + timedelta(days=2)).isoformat(),
            'expense_kind': 'advance',
            'requested_amount': 8500000,
            'beneficiary_note': 'VCB - 0123456789',
        }, submit=True)
        self.assertTrue(res['ok'])
        exp = self.env['tp.request'].browse(res['id'])

        # Step 1 & Step 2 approval
        exp.with_user(self.user_mgr).action_approve_step(note='Trưởng phòng duyệt nhu cầu')
        exp.with_user(self.admin).action_approve_step(note='Ban giám đốc duyệt chủ trương')

        self.assertEqual(exp.approval_state, 'approved')
        # MUST NOT be settled_confirmed upon approval!
        self.assertEqual(exp.financial_settlement_state, 'pending_disbursement')
        self.assertFalse(exp.voucher_ref)

        # Requester cannot confirm settlement of their own expense
        with self.assertRaises(AccessError):
            exp.with_user(self.user_staff).action_confirm_financial_settlement('PC-FAKE-001')

        # Finance executor cannot confirm without voucher number
        with self.assertRaises(UserError):
            exp.with_user(self.user_fin).action_confirm_financial_settlement('   ')

        # Finance executor confirms with real voucher reference
        out = exp.with_user(self.user_fin).action_confirm_financial_settlement(
            'UNC-202611-089', note='Đã chuyển khoản tạm ứng đợt 1',
        )
        self.assertEqual(out['status'], 'settled_confirmed')
        self.assertEqual(exp.financial_settlement_state, 'settled_confirmed')
        self.assertEqual(exp.voucher_ref, 'UNC-202611-089')
        self.assertEqual(exp.settlement_confirmed_by_id, self.user_fin)

        # Linked task creation is idempotent
        t1 = exp.with_user(self.user_fin).action_create_linked_task()
        t2 = exp.with_user(self.user_fin).action_create_linked_task()
        self.assertFalse(t1['already_existed'])
        self.assertTrue(t2['already_existed'])
        self.assertEqual(t1['id'], t2['id'])
        task = self.env['project.task'].sudo().browse(t1['id'])
        if 'tp_source_kind' in task._fields:
            self.assertEqual(task.tp_source_kind, 'request')
