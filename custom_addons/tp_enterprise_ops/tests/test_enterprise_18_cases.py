# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Section O: Complete 18 Mandatory Cross-Module Cases + Unified Certificate, Survey Calibration, Payroll Gate & AI RBAC."""
import base64
from datetime import UTC, date, datetime, time, timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.tp_equipment.models.common import INTERNAL as EQ_INTERNAL
from odoo.addons.tp_hr_attendance.models.attendance_common import internal as att_internal, local_to_utc


@tagged('post_install', '-at_install')
class TestEnterprise18MandatoryCases(TransactionCase):
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

        cls.dept_a = cls.env['hr.department'].create({'name': 'Phòng Cầu Đường A (18Case)', 'company_id': cls.company.id})
        cls.dept_b = cls.env['hr.department'].create({'name': 'Phòng Khảo Sát B (18Case)', 'company_id': cls.company.id})

        base_group = cls.env.ref('base.group_user')
        tp_user_group = cls.env.ref('tp_core.group_user')
        mgr_group = cls.env.ref('tp_core.group_manager')
        hr_mgr_group = cls.env.ref('hr.group_hr_manager')
        rep_group = cls.env.ref('tp_reporting.group_reporting_user')

        cls.user_mgr_a = cls._make_user('c18.mgra', 'Trưởng phòng A (18Case)', [base_group.id, mgr_group.id, rep_group.id])
        cls.user_emp_a = cls._make_user('c18.empa', 'Kỹ sư A (18Case)', [base_group.id, tp_user_group.id, rep_group.id])
        cls.user_emp_b = cls._make_user('c18.empb', 'Nhân viên Phòng B (18Case)', [base_group.id, tp_user_group.id, rep_group.id])
        cls.user_hr_mgr = cls._make_user('c18.hrmgr', 'Trưởng phòng Nhân sự (18Case)', [base_group.id, hr_mgr_group.id])
        cls.user_del_admin = cls._make_user('c18.deladm', 'Admin Ủy Quyền (18Case)', [base_group.id])

        cls.emp_mgr_a = cls._make_employee(cls.user_mgr_a, cls.dept_a)
        cls.dept_a.write({'manager_id': cls.emp_mgr_a.id})
        cls.emp_a = cls._make_employee(cls.user_emp_a, cls.dept_a, parent=cls.emp_mgr_a)
        cls.emp_b = cls._make_employee(cls.user_emp_b, cls.dept_b)
        cls.emp_hr = cls._make_employee(cls.user_hr_mgr, cls.dept_a)
        cls.emp_del = cls._make_employee(cls.user_del_admin, cls.dept_a)

        cls.env['tp.admin.delegation'].with_user(cls.admin)._change(
            cls.user_del_admin, cls.company, 'grant', 'Synthetic delegated admin for Case 18',
        )

        cls.project_a = cls.env['project.project'].with_user(cls.user_mgr_a).create({
            'name': 'Dự án Cao tốc Liên thông 18 Case',
            'company_id': cls.company.id,
            'tp_managed': True,
            'tp_code': 'DA-18CASE-01',
            'tp_department_id': cls.dept_a.id,
        })
        cls.env['tp.project.assignment'].sudo().create([
            {'project_id': cls.project_a.id, 'user_id': cls.user_mgr_a.id, 'role': 'coordinator', 'active': True},
            {'project_id': cls.project_a.id, 'user_id': cls.user_emp_a.id, 'role': 'reader', 'active': True},
        ])

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
            'date_version': date(2026, 1, 1),
        })

    def test_cases_01_02_03_04_05_06_work_calendar_chat_minute_wbs(self):
        """Cases #1, #2, #3, #4, #5, #6."""
        # Case #1: Assign project task -> appears in My Work without creating a duplicate record
        proj_stage = self.env['project.task.type'].sudo().create({'name': 'Đang thiết kế (Dự án)'})
        ptask = self.env['project.task'].sudo().create({
            'name': 'Bản vẽ trắc dọc Km12',
            'project_id': self.project_a.id,
            'stage_id': proj_stage.id,
            'user_ids': [Command.set([self.user_emp_a.id])],
        })
        my_dom = self.env['project.task'].with_user(self.user_emp_a)._tp_my_work_domain()
        found = self.env['project.task'].with_user(self.user_emp_a).search(my_dom)
        self.assertIn(ptask, found)
        self.assertEqual(self.env['project.task'].sudo().search_count([('name', '=', 'Bản vẽ trắc dọc Km12')]), 1)

        # Case #2: Moving personal stage for emp_a NEVER mutates project stage_id!
        pstages = self.env['project.task'].with_user(self.user_emp_a)._tp_ensure_my_personal_stages()
        self.env['project.task'].with_user(self.user_emp_a).tp_move_personal_task(ptask.id, pstages[-1].id)
        self.assertEqual(ptask.stage_id.id, proj_stage.id)

        # Case #3: Message -> Task preserves tp_source_message_id and idempotency
        chan = self.env['discuss.channel'].with_user(self.user_mgr_a).tp_create_scoped_channel(
            {'scope': 'project', 'source_id': self.project_a.id, 'name': 'Kênh dự án 18Case'}, 'tok-ch-18',
        )
        channel_rec = self.env['discuss.channel'].sudo().browse(chan['id'])
        msg = channel_rec.with_user(self.user_mgr_a).message_post(body='Kiểm tra cao độ cống ngang Km14', message_type='comment')
        m_res = self.env['discuss.channel'].with_user(self.user_mgr_a).tp_create_task_from_message(
            msg.id, {'name': 'Rà soát cao độ cống Km14', 'user_ids': [self.user_emp_a.id]}, 'tok-msg-18',
        )
        mtask = self.env['project.task'].sudo().browse(m_res['id'])
        self.assertEqual(mtask.tp_source_message_id.id, msg.id)
        self.assertEqual(mtask.tp_source_kind, 'chat')

        # Case #4: Room booking conflict rejects overlapping second reservation
        room = self.env['tp.meeting.room'].with_user(self.admin).create({
            'code': 'PH-18C', 'name': 'Phòng họp 18Case', 'company_id': self.company.id,
        })
        t0 = datetime.now() + timedelta(days=2)
        self.env['calendar.event'].with_user(self.user_mgr_a).create({
            'name': 'Họp dự án A', 'start': t0, 'stop': t0 + timedelta(hours=1), 'tp_room_id': room.id,
        })
        with self.assertRaises(UserError):
            self.env['calendar.event'].with_user(self.user_emp_b).create({
                'name': 'Họp trùng giờ', 'start': t0 + timedelta(minutes=15), 'stop': t0 + timedelta(minutes=45), 'tp_room_id': room.id,
            })

        # Case #5 & #6: Meeting minute issues task once; completing task NEVER marks volume_accepted
        mm = self.env['tp.meeting.minute'].with_user(self.user_mgr_a).tp_save_minute({
            'name': 'Biên bản họp kỹ thuật Km12',
            'conclusion_content': 'Chốt khẩu độ cống hộp.',
            'project_id': self.project_a.id,
            'action_items': [{'name': 'Xuất bản vẽ cống hộp', 'assignee_user_id': self.user_emp_a.id}],
        }, issue_now=True)
        min_rec = self.env['tp.meeting.minute'].browse(mm['id'])
        spawned_task = min_rec.action_item_ids[0].task_id
        self.assertTrue(spawned_task)
        spawned_task.with_user(self.user_emp_a).action_update_wbs_progress(100.0)
        self.assertTrue(spawned_task.tp_state_exec_reported)
        self.assertFalse(spawned_task.tp_state_volume_accepted)

    def test_cases_12_13_leave_attendance_conflict_and_survey_gear_calibration_block(self):
        """Cases #12 & #13: Leave -> Attendance without mutating raw punches (conflict -> review); Expired survey gear blocked."""
        # Case #12: Day 1 (leave only -> 'leave', no fake punch); Day 2 (leave + real punch -> 'review' conflict, punch preserved!)
        d1 = date(2026, 11, 10)
        d2 = date(2026, 11, 11)
        type_leave = self.env.ref('tp_request.type_leave_request')
        req_res = self.env['tp.request'].with_user(self.user_emp_a).tp_save_request({
            'type_id': type_leave.id,
            'title': 'Nghỉ phép 2 ngày 10-11/11',
            'description': 'Nghỉ phép năm đã đăng ký',
            'leave_kind': 'annual',
            'leave_date_from': d1.isoformat(),
            'leave_date_to': d2.isoformat(),
            'leave_days_count': 2.0,
        }, submit=True)
        leave_req = self.env['tp.request'].browse(req_res['id'])
        leave_req.with_user(self.user_mgr_a).action_approve_step(note='Đồng ý')
        self.assertEqual(leave_req.approval_state, 'approved')

        # Insert real punch ONLY on d2 (11/11) via official internal attendance session + _tp_refresh
        Session = att_internal(self.env['tp.hr.attendance.session'].sudo())
        Session.create({
            'employee_id': self.emp_a.id,
            'company_id': self.company.id,
            'work_date': d2,
            'check_in': local_to_utc(d2, time(8, 30)),
            'check_out': local_to_utc(d2, time(17, 0)),
            'source': 'import',
        })
        self.env['tp.hr.attendance.day'].sudo()._tp_refresh(self.company, {(self.emp_a.id, d2)})

        # Verify raw session count on d1 is STILL ZERO (no fabricated punches!)
        self.assertEqual(
            self.env['tp.hr.attendance.session'].sudo().search_count([
                ('employee_id', '=', self.emp_a.id), ('work_date', '=', d1),
            ]),
            0,
        )
        cells, has_leave = self.env['tp.hr.attendance.day'].sudo()._tp_presence(
            self.company, [self.emp_a.id], d1, d2, date(2026, 11, 20),
        )
        self.assertTrue(has_leave)
        # d1: approved leave, no punch -> 'leave'
        self.assertEqual(cells[(self.emp_a.id, d1)]['state'], 'leave')
        self.assertEqual(cells[(self.emp_a.id, d1)]['in'], '')
        # d2: approved leave + real punch -> 'review' conflict AND original clock times preserved!
        self.assertEqual(cells[(self.emp_a.id, d2)]['state'], 'review')
        self.assertTrue(cells[(self.emp_a.id, d2)].get('tp_leave_conflict'))
        self.assertEqual(cells[(self.emp_a.id, d2)]['in'], '08:30')
        self.assertEqual(cells[(self.emp_a.id, d2)]['out'], '17:00')

        # Case #13: Survey gear with expired calibration CANNOT be issued via tp.equipment.move!
        cat = self.env['maintenance.equipment.category'].create({'name': 'Máy toàn đạc điện tử (18Case)'})
        rtk = self.env['maintenance.equipment'].with_user(self.admin).create({
            'name': 'Máy GNSS RTK Trimble R8s (Quá hạn KĐ)',
            'category_id': cat.id,
            'company_id': self.company.id,
            'tp_technical_state': 'good',
            'tp_is_survey_gear': True,
            'tp_calibration_date': date.today() - timedelta(days=400),
            'tp_calibration_due_date': date.today() - timedelta(days=10),
        })
        rtk.action_tp_register()
        self.assertEqual(rtk.tp_calibration_state, 'expired')

        bad_move = self.env['tp.equipment.move'].with_user(self.admin).with_context(tp_equipment_move_internal=EQ_INTERNAL).create({
            'move_type': 'assign',
            'company_id': self.company.id,
            'target_custody': 'employee',
            'target_employee_id': self.emp_a.id,
            'reason': 'Xuất máy đi đo đạc',
            'line_ids': [Command.create({'equipment_id': rtk.id})],
        })
        with self.assertRaises(UserError):
            bad_move.action_done()

        # Renew calibration -> handover now succeeds!
        rtk.with_user(self.admin).write({'tp_calibration_due_date': date.today() + timedelta(days=180)})
        self.assertEqual(rtk.tp_calibration_state, 'valid')
        bad_move.action_done()
        self.assertEqual(rtk.tp_custody, 'employee')

    def test_cases_15_16_17_18_recruitment_certs_ai_rbac_payroll_and_delegated_admin(self):
        """Cases #15, #16, #17, #18 + J2 Unified Certificate sync."""
        # Case #15: Applicant stage drag never creates employee; controlled hire checks duplicate CCCD & never creates user/admin!
        st1 = self.env['hr.recruitment.stage'].sudo().create({'name': 'Vòng CV (18C)', 'sequence': 1})
        st2 = self.env['hr.recruitment.stage'].sudo().create({'name': 'Trúng tuyển (18C)', 'sequence': 2})
        app1_res = self.env['hr.applicant'].with_user(self.user_hr_mgr).tp_create_applicant({
            'partner_name': 'Nguyễn Văn Ứng Viên Mới',
            'email_from': 'ungvien18c@tanphat.test',
            'partner_phone': '0919888777',
            'tp_national_id': '048099001122',
            'department_id': self.dept_a.id,
            'stage_id': st1.id,
        })
        app1 = self.env['hr.applicant'].sudo().browse(app1_res['id'])
        # Stage move -> NO employee created
        self.env['hr.applicant'].with_user(self.user_hr_mgr).tp_move_applicant_stage(app1.id, st2.id)
        self.assertFalse(app1.employee_id)

        # Controlled onboarding -> creates hr.employee ONLY, user_id=False!
        hired = self.env['hr.applicant'].with_user(self.user_hr_mgr).tp_hire_applicant_to_employee(
            app1.id, confirm_hire=True,
        )
        new_emp = self.env['hr.employee'].sudo().browse(hired['employee_id'])
        self.assertTrue(new_emp.exists())
        self.assertFalse(new_emp.user_id)

        # Second applicant with duplicate CCCD or email MUST be rejected!
        app_dup_res = self.env['hr.applicant'].with_user(self.user_hr_mgr).tp_create_applicant({
            'partner_name': 'Ứng Viên Trùng CCCD',
            'email_from': 'ungvien18c@tanphat.test',
            'tp_national_id': '048099001122',
            'stage_id': st2.id,
        })
        with self.assertRaises(UserError):
            self.env['hr.applicant'].with_user(self.user_hr_mgr).tp_hire_applicant_to_employee(app_dup_res['id'], confirm_hire=True)

        # J2: Unified Practicing Certificate on hr.employee.skill synced to tp.credential without duplicate table
        sk_type = self.env['hr.skill.type'].sudo().create({'name': 'Chứng chỉ Hành nghề Xây dựng (18C)', 'is_certification': True})
        sk = self.env['hr.skill'].sudo().create({'name': 'Chủ trì Thiết kế Cầu Hầm', 'skill_type_id': sk_type.id})
        lvl = self.env['hr.skill.level'].sudo().create({'name': 'Hạng I', 'skill_type_id': sk_type.id, 'level_progress': 100})
        emp_cert = self.env['hr.employee.skill'].sudo().create({
            'employee_id': self.emp_a.id,
            'skill_type_id': sk_type.id,
            'skill_id': sk.id,
            'skill_level_id': lvl.id,
            'tp_certificate_no': 'CCHN-BXD-99881',
            'tp_issuer_org': 'Bộ Xây dựng',
            'tp_scope_of_practice': 'Thiết kế kết cấu công trình Cầu - Hầm Hạng I',
            'tp_valid_from': date(2025, 1, 1),
            'tp_valid_to': date.today() + timedelta(days=20),
        })
        self.assertEqual(emp_cert.tp_expiry_state, 'expiring_soon')

        # Case #16: AI Assistant enforces strict ORM ACL — user_emp_b (Dept B) CANNOT see Project A's secret dossier or Dept A's announcement!
        secret_dossier = self.env['tp.project.dossier'].with_user(self.user_mgr_a).create({
            'project_id': self.project_a.id,
            'phase_stage': 'tkkt',
            'name': 'BÍ MẬT KẾT CẤU DẦM CÁP DỰ ỨNG LỰC 9912',
        })
        self.assertTrue(secret_dossier)
        ai_out_b = self.env['tp.ai.assistant'].with_user(self.user_emp_b).tp_grounded_query('9912')
        self.assertEqual(len(ai_out_b['citations']), 0)
        ai_out_a = self.env['tp.ai.assistant'].with_user(self.user_emp_a).tp_grounded_query('9912')
        self.assertEqual(len(ai_out_a['citations']), 1)

        # Case #17: Regular employee blocked from Payroll Input Reconciliation & Live Salary blocked pending policy
        with self.assertRaises(AccessError):
            self.env['tp.payroll.input.sheet'].with_user(self.user_emp_a).tp_generate_input_reconciliation('2026-11')

        p_res = self.env['tp.payroll.input.sheet'].with_user(self.user_hr_mgr).tp_generate_input_reconciliation('2026-11')
        p_sheet = self.env['tp.payroll.input.sheet'].sudo().browse(p_res['sheet_id'])
        with self.assertRaises(UserError):
            p_sheet.with_user(self.user_hr_mgr).action_compute_live_salary()

        # Case #18: Delegated Admin blocked from granting admin or mutating Original Admin (DEC-054 / DEC-062)
        with self.assertRaises(AccessError):
            self.env['tp.admin.delegation'].with_user(self.user_del_admin)._change(
                self.user_emp_b, self.company, 'grant', 'Trái thẩm quyền DEC-054',
            )
        with self.assertRaises(AccessError):
            self.admin.with_user(self.user_del_admin).write({'email': 'hack@example.com'})
