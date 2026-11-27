# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Comprehensive automated tests for tp_request covering all 18 acceptance scenarios."""
import io
import json
from datetime import date, timedelta

from openpyxl import load_workbook

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.tp_branding.brand_routes import (
    get_route_by_action_xml_id,
    get_route_by_url,
)
from odoo.addons.tp_equipment.models.common import INTERNAL as EQ_INTERNAL


@tagged('post_install', '-at_install')
class TestTpRequestWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Preserve employee code sequence cleanliness
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        cls.addClassCleanup(cls._restore_sequence, sequence.id, *cls.env.cr.fetchone())
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())

        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()

        cls.dept_design = cls.env['hr.department'].create({
            'name': 'Synthetic Req Design Dept',
            'company_id': cls.company.id,
        })
        cls.dept_no_mgr = cls.env['hr.department'].create({
            'name': 'Synthetic Req NoManager Dept',
            'company_id': cls.company.id,
        })

        base_group = cls.env.ref('base.group_user')
        cls.user_emp = cls._make_user('req.emp.1', 'Nhân viên A (Test)', [base_group.id])
        cls.user_outsider = cls._make_user('req.outsider.1', 'Nhân viên Ngoài Cuộc (Test)', [base_group.id])
        cls.user_mgr = cls._make_user('req.mgr.1', 'Trưởng phòng A (Test)', [base_group.id])
        cls.user_step2 = cls._make_user('req.step2.1', 'Giám đốc duyệt B2 (Test)', [base_group.id])
        cls.user_step2_alt = cls._make_user('req.step2.2', 'Phó GĐ duyệt B2 (Test)', [base_group.id])
        cls.user_exec = cls._make_user('req.exec.1', 'Chuyên viên IT Thực hiện (Test)', [base_group.id])
        cls.user_delegated = cls._make_user('req.del.admin', 'Admin Ủy Quyền (Test)', [base_group.id])

        cls.emp_mgr = cls._make_employee(cls.user_mgr, cls.dept_design)
        cls.dept_design.write({'manager_id': cls.emp_mgr.id})
        cls.emp_a = cls._make_employee(cls.user_emp, cls.dept_design, parent=cls.emp_mgr)
        cls.emp_outsider = cls._make_employee(cls.user_outsider, cls.dept_no_mgr)
        cls.emp_step2 = cls._make_employee(cls.user_step2, cls.dept_design)
        cls.emp_step2_alt = cls._make_employee(cls.user_step2_alt, cls.dept_design)
        cls.emp_exec = cls._make_employee(cls.user_exec, cls.dept_design)
        cls.emp_delegated = cls._make_employee(cls.user_delegated, cls.dept_design)

        # Grant full delegated admin to user_delegated via official API
        cls.env['tp.admin.delegation'].with_user(cls.admin)._change(
            cls.user_delegated, cls.company, 'grant', 'Synthetic test delegated admin',
        )

        # Equipment catalog & real stock/assigned machines (registered into warehouse via official action_tp_register)
        cls.eq_cat = cls.env['maintenance.equipment.category'].create({'name': 'Synthetic Laptop Req'})
        EqAdmin = cls.env['maintenance.equipment'].with_user(cls.admin)
        cls.eq_assigned = EqAdmin.create({
            'name': 'Laptop Đang Dùng A',
            'category_id': cls.eq_cat.id,
            'company_id': cls.company.id,
            'tp_brand': 'Dell',
            'model': 'Latitude 5440',
            'tp_technical_state': 'good',
        })
        cls.eq_assigned.action_tp_register()
        # Assign eq_assigned to emp_a using official move
        mv_init = cls.env['tp.equipment.move'].with_user(cls.admin).with_context(tp_equipment_move_internal=EQ_INTERNAL).create({
            'move_type': 'assign',
            'company_id': cls.company.id,
            'target_custody': 'employee',
            'target_employee_id': cls.emp_a.id,
            'reason': 'Synthetic initial assign',
            'line_ids': [Command.create({'equipment_id': cls.eq_assigned.id})],
        })
        mv_init.action_done()

        cls.eq_stock_1 = EqAdmin.create({
            'name': 'Laptop Kho Sẵn 01',
            'category_id': cls.eq_cat.id,
            'company_id': cls.company.id,
            'tp_brand': 'Lenovo',
            'model': 'ThinkPad T14',
            'tp_technical_state': 'good',
        })
        cls.eq_stock_1.action_tp_register()
        cls.eq_stock_2 = EqAdmin.create({
            'name': 'Laptop Kho Sẵn 02',
            'category_id': cls.eq_cat.id,
            'company_id': cls.company.id,
            'tp_brand': 'HP',
            'model': 'ProBook 450',
            'tp_technical_state': 'good',
        })
        cls.eq_stock_2.action_tp_register()
        cls.eq_broken = EqAdmin.create({
            'name': 'Laptop Kho Hỏng',
            'category_id': cls.eq_cat.id,
            'company_id': cls.company.id,
            'tp_technical_state': 'broken',
        })
        cls.eq_broken.action_tp_register()

        # Custom 2-step sequential type for testing sequential approval, return, transfer, concurrency
        cls.type_two_step = cls.env['tp.request.type'].with_user(cls.admin).create({
            'code': 'SYNTH_2STEP',
            'name': 'Đề nghị 2 bước tuần tự (Test)',
            'handler_kind': 'general',
            'require_reason': True,
            'requires_execution': True,
            'executor_mode': 'specific_users',
            'executor_user_ids': [Command.set([cls.user_exec.id])],
            'step_ids': [
                Command.create({
                    'sequence': 10,
                    'name': 'Trưởng phòng duyệt',
                    'approver_rule': 'department_manager',
                    'sla_hours': 16.0,
                    'can_return': True,
                    'can_reject': True,
                }),
                Command.create({
                    'sequence': 20,
                    'name': 'Ban Giám đốc duyệt',
                    'approver_rule': 'specific_users',
                    'approver_user_ids': [Command.set([cls.user_step2.id, cls.user_step2_alt.id])],
                    'sla_hours': 24.0,
                    'can_return': True,
                    'can_reject': True,
                }),
            ],
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

    # ------------------------------------------------------------------ 1, 2, 3: Create, Validation, Missing Config
    def test_01_02_03_draft_validation_and_missing_approver_guard(self):
        Req = self.env['tp.request'].with_user(self.user_emp)

        # (2) Missing required fields returns exact field names/IDs
        res_err = Req.tp_save_request({
            'type_id': self.type_two_step.id,
            'title': '',
            'description': '',
        }, submit=True)
        self.assertFalse(res_err['ok'])
        err_ids = {e['id'] for e in res_err['field_errors']}
        self.assertIn('req_title', err_ids)
        self.assertIn('req_description', err_ids)

        # (3) Unconfigured type (INTERNAL_GENERAL) allows draft save, blocks submit with clear step message
        type_general = self.env.ref('tp_request.type_internal_general')
        res_draft = Req.tp_save_request({
            'type_id': type_general.id,
            'title': 'Đề nghị nội bộ chờ cấu hình duyệt',
            'description': 'Cần hỗ trợ nội bộ',
        }, submit=False)
        self.assertTrue(res_draft['ok'])
        rec_gen = Req.browse(res_draft['id'])
        self.assertEqual(rec_gen.approval_state, 'draft')
        with self.assertRaisesRegex(UserError, 'Chưa thể gửi đề nghị'):
            rec_gen.action_submit(expected_version=rec_gen.version)

        # Also department without manager blocks submit on department_manager rule
        ReqOut = self.env['tp.request'].with_user(self.user_outsider)
        res_out = ReqOut.tp_save_request({
            'type_id': self.type_two_step.id,
            'title': 'Đề nghị phòng chưa có trưởng phòng',
            'description': 'Mô tả',
        }, submit=False)
        rec_out = ReqOut.browse(res_out['id'])
        with self.assertRaisesRegex(UserError, 'chưa cấu hình Trưởng phòng'):
            rec_out.action_submit(expected_version=rec_out.version)

        # (1) Happy path: create draft -> submit -> verify snapshot & route
        res_ok = Req.tp_save_request({
            'type_id': self.type_two_step.id,
            'title': 'Đề nghị triển khai công việc A',
            'description': 'Chi tiết đầy đủ',
        }, submit=True)
        self.assertTrue(res_ok['ok'])
        req = Req.browse(res_ok['id'])
        self.assertEqual(req.approval_state, 'pending')
        self.assertEqual(req.execution_state, 'waiting_approval')
        self.assertEqual(req.current_step_id.sequence, 10)
        self.assertEqual(req.current_approver_ids, self.user_mgr)
        self.assertEqual(req.requester_name_snap, self.emp_a.name)
        self.assertEqual(req.department_name_snap, self.dept_design.name)
        # Detail payload works for requester
        detail = Req.tp_detail_data(req.id)
        self.assertEqual(detail['code'], req.code)
        self.assertEqual(len(detail['steps']), 2)

    # ------------------------------------------------------------------ 4, 16: Privacy, Attachment Guard, Immutable History, Comments
    def test_04_16_privacy_attachment_guard_and_immutable_history(self):
        Req = self.env['tp.request'].with_user(self.user_emp)
        res = Req.tp_save_request({
            'type_id': self.type_two_step.id,
            'title': 'Hồ sơ riêng tư của A',
            'description': 'Nội dung bảo mật',
        }, submit=False)
        req = Req.browse(res['id'])

        # Attach a private file while draft, then submit
        att = self.env['ir.attachment'].with_user(self.user_emp).create({
            'name': 'minh_chung.txt',
            'raw': b'secret evidence',
            'res_model': 'tp.request',
            'res_id': req.id,
            'mimetype': 'text/plain',
            'public': False,
        })
        req.action_submit(expected_version=req.version)
        # Guard blocks making attachment public or generating public token
        with self.assertRaises(AccessError):
            att.with_user(self.admin).write({'public': True})
        with self.assertRaises(AccessError):
            att.with_user(self.admin).generate_access_token()

        # Outsider cannot read request, detail, steps, history, or attachment
        ReqOut = self.env['tp.request'].with_user(self.user_outsider)
        self.assertFalse(ReqOut.search([('id', '=', req.id)]))
        with self.assertRaises((AccessError, UserError)):
            ReqOut.tp_detail_data(req.id)
        self.assertFalse(self.env['tp.request.step'].with_user(self.user_outsider).search([('request_id', '=', req.id)]))
        self.assertFalse(self.env['tp.request.history'].with_user(self.user_outsider).search([('request_id', '=', req.id)]))
        with self.assertRaises(AccessError):
            att.with_user(self.user_outsider).check_access('read')

        # Employee cannot spoof state or requester via ORM write
        with self.assertRaises(AccessError):
            req.write({'approval_state': 'approved'})
        with self.assertRaises(AccessError):
            req.write({'requester_user_id': self.user_outsider.id})

        # Comments NEVER change state
        Req.tp_post_comment(req.id, 'Xin anh duyệt sớm giúp em')
        self.assertEqual(req.approval_state, 'pending')

        # Audit history is strictly immutable even for admin
        hist = req.history_ids[0]
        with self.assertRaises(AccessError):
            hist.with_user(self.admin).write({'note': 'Tampered'})
        with self.assertRaises(AccessError):
            hist.with_user(self.admin).unlink()

    # ------------------------------------------------------------------ 5, 7, 8, 9, 18: Sequential Steps, Anti-Self-Approve, Return/Resubmit, Concurrency, Transfer, Frozen Route
    def test_05_07_08_09_18_sequential_return_concurrency_transfer_and_frozen_route(self):
        ReqEmp = self.env['tp.request'].with_user(self.user_emp)
        res = ReqEmp.tp_save_request({
            'type_id': self.type_two_step.id,
            'title': 'Hồ sơ tuần tự 2 bước',
            'description': 'Bản lần 1',
        }, submit=True)
        req_id = res['id']
        req_mgr = self.env['tp.request'].with_user(self.user_mgr).browse(req_id)
        req_s2 = self.env['tp.request'].with_user(self.user_step2).browse(req_id)
        req_s2_alt = self.env['tp.request'].with_user(self.user_step2_alt).browse(req_id)

        # (5) Step 2 approver CANNOT approve while Step 1 is pending
        with self.assertRaises(AccessError):
            req_s2.action_approve_step(note='Duyệt vượt cấp', expected_version=req_s2.version)

        # (18) Changing request type config after submit does NOT mutate submitted request's frozen route
        self.type_two_step.with_user(self.admin).write({
            'step_ids': [Command.clear(), Command.create({
                'sequence': 10, 'name': 'Bước mới sau đổi cấu hình',
                'approver_rule': 'admin_group', 'sla_hours': 8.0,
            })],
        })
        self.assertEqual(len(req_mgr.step_ids), 2)
        self.assertEqual(req_mgr.current_approver_ids, self.user_mgr)

        # (8) Return requires mandatory reason -> edit -> resubmit increments version & preserves history
        with self.assertRaises(UserError):
            req_mgr.action_return(reason='   ', expected_version=req_mgr.version)
        req_mgr.action_return(reason='Bổ sung dự toán chi tiết', expected_version=req_mgr.version)
        req_emp = ReqEmp.browse(req_id)
        self.assertEqual(req_emp.approval_state, 'returned')
        prev_ver = req_emp.version

        # Re-restore 2-step config before resubmit so resubmit builds 2-step route again
        self.type_two_step.with_user(self.admin).write({
            'step_ids': [
                Command.clear(),
                Command.create({
                    'sequence': 10, 'name': 'Trưởng phòng duyệt',
                    'approver_rule': 'department_manager', 'sla_hours': 16.0,
                }),
                Command.create({
                    'sequence': 20, 'name': 'Ban Giám đốc duyệt',
                    'approver_rule': 'specific_users',
                    'approver_user_ids': [Command.set([self.user_step2.id, self.user_step2_alt.id])],
                    'sla_hours': 24.0,
                }),
            ],
        })
        ReqEmp.tp_save_request({
            'id': req_id,
            'title': 'Hồ sơ tuần tự 2 bước (đã bổ sung)',
            'description': 'Đã bổ sung đầy đủ dự toán',
        }, submit=True)
        req_emp.invalidate_recordset()
        self.assertEqual(req_emp.approval_state, 'pending')
        self.assertGreater(req_emp.version, prev_ver)

        # Step 1 approves -> advances to Step 2
        req_mgr.invalidate_recordset()
        out1 = req_mgr.action_approve_step(note='Nhất trí bước 1', expected_version=req_mgr.version)
        self.assertEqual(out1['status'], 'next_step')
        req_s2.invalidate_recordset()
        self.assertEqual(req_s2.current_step_id.sequence, 20)

        # (9) Stale expected_version rejected cleanly; second approver after any_one decision rejected cleanly
        stale_ver = req_s2.version
        out2 = req_s2.action_approve_step(note='GĐ phê duyệt', expected_version=stale_ver)
        self.assertEqual(out2['status'], 'approved')
        self.assertEqual(req_s2.approval_state, 'approved')
        self.assertEqual(req_s2.execution_state, 'pending')  # Distinct from execution done!

        # Concurrent/duplicate approval by second eligible approver fails cleanly
        req_s2_alt.invalidate_recordset()
        with self.assertRaises((UserError, AccessError)):
            req_s2_alt.action_approve_step(note='Phó GĐ duyệt trùng', expected_version=stale_ver)
        with self.assertRaises((UserError, AccessError)):
            req_s2_alt.action_approve_step(note='Phó GĐ duyệt lại', expected_version=req_s2_alt.version)

        # Executor cannot mutate approval decision, can execute & complete
        req_exec = self.env['tp.request'].with_user(self.user_exec).browse(req_id)
        with self.assertRaises(AccessError):
            req_exec.write({'approval_state': 'rejected'})
        req_exec.action_start_execution(note='Đã tiếp nhận', expected_version=req_exec.version)
        self.assertEqual(req_exec.execution_state, 'in_progress')
        req_exec.action_complete_execution(result_note='Đã hoàn thành bàn giao kết quả', expected_version=req_exec.version)
        self.assertEqual(req_exec.execution_state, 'done')

        # (7) Anti-self-approval even for Admin!
        type_it = self.env.ref('tp_request.type_it_support')
        res_adm = self.env['tp.request'].with_user(self.admin).tp_save_request({
            'type_id': type_it.id,
            'title': 'Admin tự gửi hỗ trợ IT',
            'description': 'Test chống tự duyệt',
            'it_category': 'software',
        }, submit=True)
        req_adm = self.env['tp.request'].with_user(self.admin).browse(res_adm['id'])
        self.assertNotIn(self.admin, req_adm.current_approver_ids)
        with self.assertRaises(AccessError):
            req_adm.action_approve_step(note='Tự duyệt', expected_version=req_adm.version)

        # (18) Manager transfer approver with mandatory reason & audit log (cannot transfer to requester)
        with self.assertRaises(UserError):
            req_adm.action_transfer_approver([self.admin.id], reason='Chuyển về chính mình', expected_version=req_adm.version)
        req_adm.action_transfer_approver([self.user_step2.id], reason='Phân công duyệt thay', expected_version=req_adm.version)
        self.assertEqual(req_adm.current_approver_ids, self.user_step2)
        self.assertTrue(any(h.action == 'transfer_approver' for h in req_adm.history_ids))

    # ------------------------------------------------------------------ 6, 17: Revoked Delegated Admin loses rights immediately + DEC-062 intact
    def test_06_17_revoked_delegated_admin_and_policy_preservation(self):
        type_it = self.env.ref('tp_request.type_it_support')
        res = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_it.id,
            'title': 'Hỗ trợ cài đặt AutoCAD',
            'description': 'Cần cài đặt bản quyền mới',
            'it_category': 'software',
        }, submit=True)
        req_id = res['id']

        # Delegated admin can read admin console & approve while active
        self.assertTrue(self.env['tp.request'].with_user(self.user_delegated).tp_admin_data()['types'])
        req_del = self.env['tp.request'].with_user(self.user_delegated).browse(req_id)
        self.assertIn(self.user_delegated, req_del.current_approver_ids)

        # Now original admin revokes delegation
        self.env['tp.admin.delegation'].with_user(self.admin)._change(
            self.user_delegated, self.company, 'revoke', 'Synthetic revoke check',
        )

        # Immediately loses approval right AND admin console access!
        req_del.invalidate_recordset()
        with self.assertRaises(AccessError):
            req_del.action_approve_step(note='Thử duyệt sau thu hồi', expected_version=req_del.version)
        with self.assertRaises(AccessError):
            self.env['tp.request'].with_user(self.user_delegated).tp_admin_data()

        # Re-grant check: delegated admin still cannot grant admin to another user (DEC-054 intact)
        self.env['tp.admin.delegation'].with_user(self.admin)._change(
            self.user_delegated, self.company, 'grant', 'Synthetic re-grant',
        )
        with self.assertRaises(AccessError):
            self.env['tp.admin.delegation'].with_user(self.user_delegated)._change(
                self.user_emp, self.company, 'grant', 'Attempt privilege escalation',
            )

    # ------------------------------------------------------------------ 10: Attendance Correction 1-1 Bridge & Period Lock
    def test_10_attendance_correction_single_source_of_truth_and_period_lock(self):
        work_day = date.today() - timedelta(days=2)
        type_att = self.env.ref('tp_request.type_attendance_correction')

        # (A) Create & submit from tp_request -> creates exactly 1 tp.hr.attendance.correction -> approve updates real attendance
        res = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_att.id,
            'title': 'Điều chỉnh công quên chấm ra',
            'description': 'Đi khảo sát hiện trường về muộn',
            'att_work_date': work_day.isoformat(),
            'att_requested_in': '08:30',
            'att_requested_out': '17:30',
        }, submit=True)
        self.assertTrue(res['ok'])
        req = self.env['tp.request'].with_user(self.admin).browse(res['id'])
        corr = req.attendance_correction_id
        self.assertTrue(corr)
        self.assertEqual(corr.state, 'submitted')
        self.assertEqual(req.approval_state, 'pending')
        # Zero duplicate corrections
        self.assertEqual(self.env['tp.hr.attendance.correction'].search_count([
            ('employee_id', '=', self.emp_a.id), ('work_date', '=', work_day),
        ]), 1)

        # Approve via tp_request -> delegates to corr.action_approve() -> updates real tp.hr.attendance.day!
        req.action_approve_step(note='Đã xác nhận lịch công tác', expected_version=req.version)
        corr.invalidate_recordset()
        req.invalidate_recordset()
        self.assertEqual(corr.state, 'approved')
        self.assertEqual(req.approval_state, 'approved')
        att_day = self.env['tp.hr.attendance.day'].search([
            ('employee_id', '=', self.emp_a.id), ('work_date', '=', work_day),
        ], limit=1)
        self.assertTrue(att_day)

        # (B) Create directly in tp.hr.attendance.correction -> automatically mirrored 1-1 into tp.request
        work_day_2 = date.today() - timedelta(days=3)
        corr2 = self.env['tp.hr.attendance.correction'].with_user(self.user_emp).create({
            'work_date': work_day_2,
            'requested_in': 8.5,
            'requested_out': 17.0,
            'reason': 'Tạo trực tiếp từ Công của tôi',
        })
        corr2.action_submit()
        self.assertTrue(corr2.tp_request_id)
        self.assertEqual(corr2.tp_request_id.approval_state, 'pending')
        self.assertEqual(self.env['tp.request'].sudo().search_count([('attendance_correction_id', '=', corr2.id)]), 1)

        request = corr2.tp_request_id
        pending_version = request.version
        with self.assertRaises(UserError):
            request.action_withdraw(expected_version=pending_version - 1)
        self.assertEqual(corr2.state, 'submitted')
        request.action_withdraw(expected_version=pending_version)
        with self.assertRaises(UserError):
            request.with_user(self.admin).action_approve_step(expected_version=pending_version)
        self.assertEqual((request.approval_state, corr2.state), ('withdrawn', 'withdrawn'))
        self.assertFalse(corr2.session_id)

    def test_attendance_bridge_private_read_follows_correction_access(self):
        work_day = date.today() - timedelta(days=4)
        type_att = self.env.ref('tp_request.type_attendance_correction')
        res = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_att.id,
            'title': 'Đề nghị điều chỉnh riêng tư',
            'description': 'Lý do riêng tư không dành cho quản lý đề nghị',
            'att_work_date': work_day.isoformat(),
            'att_requested_in': '08:30',
            'att_requested_out': '17:00',
        }, submit=True)
        req = self.env['tp.request'].browse(res['id'])
        self.assertEqual(req.with_user(self.user_delegated).description, req.description)

        request_manager = self.env.ref('tp_request.group_request_manager')
        self.user_mgr.write({'group_ids': [Command.link(request_manager.id)]})
        self.env['tp.admin.delegation'].with_user(self.admin)._change(
            self.user_delegated, self.company, 'revoke', 'Synthetic privacy revoke',
        )
        for user in (self.user_mgr, self.user_delegated):
            with self.subTest(user=user.login):
                view = req.with_user(user)
                self.assertFalse(view.search_count([('id', '=', req.id)]))
                with self.assertRaises(AccessError):
                    view.read(['description'])
                self.assertFalse(self.env['tp.request.history'].with_user(user).search_count([('request_id', '=', req.id)]))

    # ------------------------------------------------------------------ 11, 12, 13: Equipment Assign, Double-Assign Guard, Swap Atomic, Purchase Proposal
    def test_11_12_13_equipment_assign_double_assign_swap_and_purchase(self):
        # Employee sees ONLY their own assigned device (not stock or broken devices)
        my_eq = self.env['tp.request'].with_user(self.user_emp).tp_my_equipment_options()
        self.assertEqual([e['id'] for e in my_eq], [self.eq_assigned.id])
        # Employee cannot read eligible stock list
        type_assign = self.env.ref('tp_request.type_equipment_assign')

        # Create 2 approved assign requests
        r1_id = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_assign.id, 'title': 'Cấp máy lần 1', 'description': 'Phục vụ thiết kế',
            'equipment_category_id': self.eq_cat.id,
        }, submit=True)['id']
        r2_id = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_assign.id, 'title': 'Cấp máy lần 2', 'description': 'Phục vụ khảo sát',
            'equipment_category_id': self.eq_cat.id,
        }, submit=True)['id']

        r1 = self.env['tp.request'].with_user(self.admin).browse(r1_id)
        r2 = self.env['tp.request'].with_user(self.admin).browse(r2_id)
        r1.action_approve_step(note='Duyệt cấp 1', expected_version=r1.version)
        r2.action_approve_step(note='Duyệt cấp 2', expected_version=r2.version)
        self.assertEqual(r1.approval_state, 'approved')
        self.assertEqual(r1.execution_state, 'pending')  # Distinct from done!

        # (11) Cannot assign broken or already-assigned equipment
        with self.assertRaises(UserError):
            r1.action_complete_execution(
                result_note='Thử cấp máy hỏng', expected_version=r1.version,
                extra_payload={'fulfilled_equipment_id': self.eq_broken.id},
            )
        with self.assertRaises(UserError):
            r1.action_complete_execution(
                result_note='Thử cấp máy đang dùng', expected_version=r1.version,
                extra_payload={'fulfilled_equipment_id': self.eq_assigned.id},
            )

        # Assign valid stock machine eq_stock_1 to r1 -> succeeds
        r1.action_complete_execution(
            result_note='Đã bàn giao ThinkPad T14', expected_version=r1.version,
            extra_payload={'fulfilled_equipment_id': self.eq_stock_1.id},
        )
        self.assertEqual(r1.execution_state, 'done')
        self.assertEqual(self.eq_stock_1.tp_employee_id, self.emp_a)
        self.assertEqual(self.eq_stock_1.tp_custody, 'employee')

        # (12) Second approved request CANNOT assign the same machine eq_stock_1!
        with self.assertRaises(UserError):
            r2.action_complete_execution(
                result_note='Thử cấp trùng ThinkPad T14', expected_version=r2.version,
                extra_payload={'fulfilled_equipment_id': self.eq_stock_1.id},
            )

        # (13A) Swap: returns old eq_assigned with mandatory condition & assigns eq_stock_2 atomically
        type_swap = self.env.ref('tp_request.type_equipment_swap')
        rswap_id = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_swap.id, 'title': 'Đổi máy cũ sang cấu hình cao hơn',
            'description': 'Máy cũ chạy chậm', 'equipment_id': self.eq_assigned.id,
        }, submit=True)['id']
        rswap = self.env['tp.request'].with_user(self.admin).browse(rswap_id)
        rswap.action_approve_step(note='Đồng ý đổi', expected_version=rswap.version)
        # Missing old condition must fail
        with self.assertRaises(UserError):
            rswap.action_complete_execution(
                result_note='Đổi máy thiếu tình trạng cũ', expected_version=rswap.version,
                extra_payload={'fulfilled_equipment_id': self.eq_stock_2.id, 'old_equipment_condition': ''},
            )
        rswap.action_complete_execution(
            result_note='Đã thu hồi máy cũ tình trạng hạn chế và giao HP ProBook',
            expected_version=rswap.version,
            extra_payload={'fulfilled_equipment_id': self.eq_stock_2.id, 'old_equipment_condition': 'limited'},
        )
        self.assertEqual(rswap.execution_state, 'done')
        self.assertEqual(self.eq_assigned.tp_custody, 'stock')
        self.assertFalse(self.eq_assigned.tp_employee_id)
        self.assertEqual(self.eq_assigned.tp_technical_state, 'limited')
        self.assertEqual(self.eq_stock_2.tp_custody, 'employee')
        self.assertEqual(self.eq_stock_2.tp_employee_id, self.emp_a)
        self.assertEqual(len(rswap.equipment_move_ids), 2)

        # (13B) Equipment Purchase approval does NOT auto-create maintenance.equipment stock assets!
        eq_count_before = self.env['maintenance.equipment'].sudo().search_count([])
        type_buy = self.env.ref('tp_request.type_equipment_purchase')
        rbuy_id = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_buy.id, 'title': 'Mua thêm 2 máy trạm',
            'description': 'Phục vụ dự án cầu đường mới', 'equipment_category_id': self.eq_cat.id,
            'equipment_quantity': 2, 'equipment_desired_spec': 'RAM 32GB',
            'needed_date': (date.today() + timedelta(days=7)).isoformat(),
        }, submit=True)['id']
        # Step 1 = dept manager, Step 2 = admin_group
        rbuy_mgr = self.env['tp.request'].with_user(self.user_mgr).browse(rbuy_id)
        rbuy_mgr.action_approve_step(note='TP nhất trí', expected_version=rbuy_mgr.version)
        rbuy_adm = self.env['tp.request'].with_user(self.admin).browse(rbuy_id)
        rbuy_adm.action_approve_step(note='Duyệt chủ trương mua', expected_version=rbuy_adm.version)
        self.assertEqual(self.env['maintenance.equipment'].sudo().search_count([]), eq_count_before)
        # Executor creates real tp.equipment.proposal (still zero stock assets created!)
        prop_res = rbuy_adm.action_create_equipment_proposal(expected_version=rbuy_adm.version)
        self.assertTrue(prop_res['proposal_id'])
        self.assertEqual(self.env['maintenance.equipment'].sudo().search_count([]), eq_count_before)

    # ------------------------------------------------------------------ 14, 15: Dashboard, Filters, Branded Routes
    def test_14_15_dashboard_filter_consistency_and_branded_routes(self):
        type_it = self.env.ref('tp_request.type_it_support')
        self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_it.id, 'title': 'Hỗ trợ VPN khẩn', 'description': 'Không kết nối được VPN',
            'it_category': 'network', 'priority': 'urgent',
        }, submit=True)

        dash = self.env['tp.request'].with_user(self.user_emp).tp_dashboard_data()
        lst = self.env['tp.request'].with_user(self.user_emp).tp_list_data('mine', {'priority': 'urgent'})
        self.assertGreaterEqual(dash['counts']['mine_pending'], 1)
        self.assertEqual(dash['counts']['overdue'], 0)
        self.assertEqual(lst['total'], len(lst['rows']))
        self.assertTrue(all(r['priority'] == 'urgent' for r in lst['rows']))
        # Verify overdue search accurately distinguishes future vs past due_at (Odoo 20 Domain 'in' operator)
        to_app_lst = self.env['tp.request'].with_user(self.admin).tp_list_data('to_approve', {})
        self.assertEqual(to_app_lst['tab_counts']['overdue'], 0)

        # Branded route resolution check (tp_branding)
        for path, xmlid in [
            ('/app/de-nghi/tong-quan', 'tp_request.action_overview'),
            ('/app/de-nghi/cua-toi', 'tp_request.action_mine'),
            ('/app/de-nghi/can-duyet', 'tp_request.action_to_approve'),
            ('/app/de-nghi/can-thuc-hien', 'tp_request.action_to_execute'),
            ('/app/de-nghi/theo-doi', 'tp_request.action_watching'),
            ('/app/de-nghi/quan-tri', 'tp_request.action_admin'),
            ('/app/de-nghi/ho-so', 'tp_request.action_detail'),
        ]:
            route = get_route_by_url(path)
            self.assertIsNotNone(route, f'Missing route for {path}')
            self.assertEqual(route['action_xml_id'], xmlid)
            by_xml = get_route_by_action_xml_id(xmlid)
            self.assertEqual(by_xml['url'], path)
        self.assertTrue(get_route_by_url('/app/de-nghi/ho-so')['has_detail'])

    # ------------------------------------------------------------------ 16: Draft time validation, reopen history & safe excel cell
    def test_16_draft_attendance_time_order_reopen_history_and_excel_formula_guard(self):
        from odoo.addons.tp_request.controllers.main import _safe_excel_cell  # noqa: I001, PLC0415

        self.assertEqual(_safe_excel_cell('=SUM(A1:A2)'), "'=SUM(A1:A2)")
        self.assertEqual(_safe_excel_cell('  =CMD()'), "'  =CMD()")
        self.assertEqual(_safe_excel_cell('\n+1+1'), "'\n+1+1")
        self.assertEqual(_safe_excel_cell('Bình thường - không công thức'), 'Bình thường - không công thức')

        type_att = self.env.ref('tp_request.type_attendance_correction')
        bad_draft = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_att.id,
            'title': 'Nháp sai giờ ra trước giờ vào',
            'description': 'Kiểm tra lưu nháp giờ công',
            'att_work_date': date.today().isoformat(),
            'att_requested_in': '17:30',
            'att_requested_out': '08:00',
        }, submit=False)
        self.assertFalse(bad_draft['ok'])
        self.assertTrue(any(err['id'] == 'req_att_out' for err in bad_draft.get('field_errors', [])))

        good_res = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_att.id,
            'title': 'Đề nghị điều chỉnh công hợp lệ',
            'description': 'Quên chấm vân tay buổi chiều',
            'att_work_date': (date.today() - timedelta(days=1)).isoformat(),
            'att_requested_in': '08:30',
            'att_requested_out': '17:30',
        }, submit=True)
        self.assertTrue(good_res['ok'])
        req = self.env['tp.request'].browse(good_res['id'])
        corr = req.attendance_correction_id
        self.assertTrue(corr)
        corr.with_user(self.user_emp).action_withdraw(reason='Cần chỉnh lại giờ ra')
        corr.with_user(self.user_emp).action_reopen_draft()
        req.invalidate_recordset()
        self.assertEqual(req.approval_state, 'draft')
        self.assertIn('reopen_draft', req.history_ids.mapped('action'))

    # ------------------------------------------------------------------ 17: 2-way attendance evidence sync (Step E)
    def test_17_bidirectional_attendance_evidence_sync(self):
        import base64 as b64  # noqa: PLC0415

        type_att = self.env.ref('tp_request.type_attendance_correction')

        # 1) Direction: Công của tôi (tp.hr.attendance.correction.evidence_file) -> Yêu cầu phê duyệt (tp.request)
        day_a = date.today() - timedelta(days=2)
        corr_res = self.env['tp.hr.attendance.correction'].with_user(self.user_emp).tp_save_and_submit(
            {
                'work_date': day_a.isoformat(),
                'requested_in': 8.5,
                'requested_out': 17.5,
                'reason': 'Quên chấm máy buổi sáng có xác nhận',
                'evidence_file': b64.b64encode(b'EVIDENCE_FROM_MINE_PDF').decode('ascii'),
                'evidence_name': 'xac_nhan_cong.pdf',
            },
            False,
            True,
            '0123456789abcdef',
        )
        corr_a = self.env['tp.hr.attendance.correction'].sudo().browse(corr_res['id'])
        req_a = corr_a.tp_request_id
        self.assertTrue(req_a)
        detail_a = self.env['tp.request'].with_user(self.admin).tp_detail_data(req_a.id)
        self.assertEqual(len(detail_a['attachments']), 1, 'Evidence must appear once on Request detail without duplication')
        self.assertEqual(detail_a['attachments'][0]['name'], 'xac_nhan_cong.pdf')

        # Approve and verify still exactly 1 attachment (idempotent across transitions)
        corr_a.with_user(self.admin).action_approve(note='Đồng ý minh chứng')
        detail_a_after = self.env['tp.request'].with_user(self.admin).tp_detail_data(req_a.id)
        self.assertEqual(len(detail_a_after['attachments']), 1)

        # 2) Direction: Yêu cầu phê duyệt popup (orphan ir.attachment) -> tp.request + corr.evidence_file
        orphan_att = self.env['ir.attachment'].with_user(self.user_emp).sudo().create({
            'name': 'minh_chung_popup.txt',
            'raw': b'POPUP_EVIDENCE_BYTES',
            'mimetype': 'text/plain',
            'res_model': False,
            'res_id': 0,
            'public': False,
        })
        day_b = date.today() - timedelta(days=3)
        saved_b = self.env['tp.request'].with_user(self.user_emp).tp_save_request({
            'type_id': type_att.id,
            'title': 'Giải trình công kèm tệp từ popup',
            'description': 'Đính kèm tệp từ Yêu cầu phê duyệt',
            'att_work_date': day_b.isoformat(),
            'att_requested_in': '08:15',
            'att_requested_out': '17:30',
            'attachment_ids': [orphan_att.id],
        }, submit=True)
        self.assertTrue(saved_b['ok'])
        req_b = self.env['tp.request'].sudo().browse(saved_b['id'])
        corr_b = req_b.attendance_correction_id.sudo()
        self.assertEqual(orphan_att.sudo().res_model, 'tp.request')
        self.assertEqual(orphan_att.sudo().res_id, req_b.id)
        self.assertEqual(len(req_b.attachment_ids), 1)
        self.assertTrue(bool(corr_b.evidence_file))
        self.assertEqual(corr_b.evidence_name, 'minh_chung_popup.txt')


@tagged('post_install', '-at_install')
class TestTpRequestHttp(HttpCase):
    """HTTP-level checks for private attachment access, XLSX export consistency, and branded routes."""

    def test_http_attachment_privacy_and_xlsx_export(self):
        company = self.env.company
        base_group = self.env.ref('base.group_user')
        u_owner = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'HTTP Owner', 'login': 'http.req.owner', 'password': 'TpReqTestPassword123!',
            'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set([base_group.id])],
        })
        self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'HTTP Other', 'login': 'http.req.other', 'password': 'TpReqTestPassword123!',
            'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set([base_group.id])],
        })
        type_it = self.env.ref('tp_request.type_it_support')
        res = self.env['tp.request'].with_user(u_owner).tp_save_request({
            'type_id': type_it.id, 'title': 'HTTP Export Test Request', 'description': 'Chi tiết HTTP',
            'it_category': 'account', 'priority': 'high',
        }, submit=False)
        req_id = res['id']
        att = self.env['ir.attachment'].with_user(u_owner).create({
            'name': 'private_doc.txt', 'raw': b'PRIVATE_REQ_BYTES',
            'res_model': 'tp.request', 'res_id': req_id, 'mimetype': 'text/plain', 'public': False,
        })
        self.env['tp.request'].with_user(u_owner).browse(req_id).action_submit()

        # Unrelated user gets 403/404 on attachment download
        self.authenticate('http.req.other', 'TpReqTestPassword123!')
        r_denied = self.url_open(f'/tp_request/attachment/{att.id}')
        self.assertIn(r_denied.status_code, (403, 404))

        # Owner downloads attachment cleanly
        self.authenticate('http.req.owner', 'TpReqTestPassword123!')
        r_ok = self.url_open(f'/tp_request/attachment/{att.id}')
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.content, b'PRIVATE_REQ_BYTES')

        # Export XLSX matches exact applied filter count
        params = json.dumps({'priority': 'high'})
        r_xlsx = self.url_open(f'/tp_request/export.xlsx?mode=mine&params={params}')
        self.assertEqual(r_xlsx.status_code, 200)
        wb = load_workbook(io.BytesIO(r_xlsx.content))
        ws = wb.active
        data_rows = list(ws.iter_rows(min_row=2, values_only=True))
        self.assertEqual(len(data_rows), 1)
        self.assertEqual(data_rows[0][1], 'HTTP Export Test Request')

        # Branded direct URLs & F5 reload return 200 webclient shell
        for url in ('/app/de-nghi/tong-quan', '/app/de-nghi/cua-toi', f'/app/de-nghi/ho-so/{req_id}'):
            resp = self.url_open(url)
            self.assertEqual(resp.status_code, 200, f'Expected 200 for {url}')

        # Cross-model attachment delete MUST be blocked with HTTP 403 even if created by same user (F-A07-0001)
        foreign_partner = u_owner.partner_id
        foreign_att = self.env['ir.attachment'].with_user(u_owner).sudo().create({
            'name': 'avatar_or_hr_doc.txt',
            'raw': b'DO_NOT_DELETE_ME',
            'res_model': 'res.partner',
            'res_id': foreign_partner.id,
            'mimetype': 'text/plain',
            'create_uid': u_owner.id,
        })
        csrf = self.csrf_token()
        r_del_foreign = self.url_open(
            f'/tp_request/attachment/{foreign_att.id}/delete',
            data={'csrf_token': csrf},
        )
        self.assertEqual(r_del_foreign.status_code, 403)
        self.assertTrue(foreign_att.exists(), 'Foreign model attachment must remain intact!')

        # Submitted tp.request attachment delete MUST also be blocked with HTTP 403
        r_del_submitted = self.url_open(
            f'/tp_request/attachment/{att.id}/delete',
            data={'csrf_token': csrf},
        )
        self.assertEqual(r_del_submitted.status_code, 403)
        self.assertTrue(att.exists(), 'Submitted request attachment must remain intact!')
