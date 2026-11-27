# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Automated tests for tp_digital_office: Mandatory Cases #5 (Minutes->Tasks), #7/#8 (Plan->Task->Frozen Snapshot), #9 (Explicit Ack), and Honest Workload."""
from datetime import date, datetime, timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDigitalOffice(TransactionCase):
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

        cls.dept_eng = cls.env['hr.department'].create({
            'name': 'Phòng Thiết kế Cầu (DO Test)',
            'company_id': cls.company.id,
        })
        cls.dept_other = cls.env['hr.department'].create({
            'name': 'Phòng Khác (DO Test)',
            'company_id': cls.company.id,
        })

        base_group = cls.env.ref('base.group_user')
        rep_group = cls.env.ref('tp_reporting.group_reporting_user')
        cls.user_mgr = cls._make_user('do.mgr', 'Trưởng phòng Cầu (DO)', [base_group.id, rep_group.id])
        cls.user_eng = cls._make_user('do.eng', 'Chủ nhiệm Thiết kế (DO)', [base_group.id, rep_group.id])
        cls.user_out = cls._make_user('do.out', 'Nhân viên Phòng Khác (DO)', [base_group.id, rep_group.id])

        cls.emp_mgr = cls._make_employee(cls.user_mgr, cls.dept_eng)
        cls.dept_eng.write({'manager_id': cls.emp_mgr.id})
        cls.emp_eng = cls._make_employee(cls.user_eng, cls.dept_eng, parent=cls.emp_mgr)
        cls.emp_out = cls._make_employee(cls.user_out, cls.dept_other)

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

    def test_01_mandatory_case_05_meeting_minute_issues_task_once_and_protects_revision(self):
        """Case #5: Issuing minute creates project.task ONCE; post-issue revision requires reason, never deletes or duplicates tasks."""
        ev = self.env['calendar.event'].with_user(self.user_mgr).create({
            'name': 'Họp rà soát tiến độ cầu vượt nút giao',
            'start': datetime.now() + timedelta(hours=1),
            'stop': datetime.now() + timedelta(hours=2),
            'partner_ids': [Command.set([self.user_mgr.partner_id.id, self.user_eng.partner_id.id])],
        })
        pre = self.env['tp.meeting.minute'].with_user(self.user_mgr).tp_prefill_from_calendar_event(ev.id)
        self.assertEqual(pre['calendar_event_id'], ev.id)
        self.assertIn(self.user_eng.id, pre['attendee_user_ids'])

        res = self.env['tp.meeting.minute'].with_user(self.user_mgr).tp_save_minute({
            'name': pre['name'],
            'calendar_event_id': ev.id,
            'chair_user_id': self.user_mgr.id,
            'department_id': self.dept_eng.id,
            'attendee_user_ids': [self.user_mgr.id, self.user_eng.id],
            'discussion_content': 'Thống nhất phương án kết cấu nhịp chính.',
            'conclusion_content': 'Giao kỹ sư hoàn thành bản vẽ bố trí chung.',
            'action_items': [{
                'name': 'Hoàn thành bản vẽ bố trí chung cầu vượt',
                'assignee_user_id': self.user_eng.id,
                'deadline': (date.today() + timedelta(days=5)).isoformat(),
                'deliverable_expected': 'Bản vẽ PDF + DWG ký nháy',
            }],
        }, issue_now=True)
        self.assertTrue(res['ok'])
        minute = self.env['tp.meeting.minute'].browse(res['id'])
        self.assertEqual(minute.state, 'issued')
        self.assertEqual(len(minute.action_item_ids), 1)
        first_task = minute.action_item_ids[0].task_id
        self.assertTrue(first_task)
        self.assertEqual(first_task.tp_source_kind, 'meeting')

        # Outsider cannot read non-participating minute
        with self.assertRaises(AccessError):
            minute.with_user(self.user_out).check_access('read')

        # Direct edit on issued minute is blocked
        with self.assertRaises(UserError):
            minute.with_user(self.user_mgr).write({'conclusion_content': 'Sửa ngầm không qua revise'})

        # Adding, editing, or spoofing task_id on action items of an issued minute is strictly blocked (F-A07-0007)
        with self.assertRaises(UserError):
            self.env['tp.meeting.action.item'].with_user(self.user_mgr).create({
                'minute_id': minute.id,
                'name': 'Thêm lén đầu việc khi đã phát hành',
                'assignee_user_id': self.user_eng.id,
            })
        with self.assertRaises(UserError):
            minute.action_item_ids[0].with_user(self.user_mgr).write({'name': 'Sửa lén tên đầu việc'})
        with self.assertRaises(AccessError):
            minute.action_item_ids[0].with_user(self.admin).write({'task_id': False})

        # Deleting an action item that already spawned a task is blocked
        with self.assertRaises(UserError):
            minute.action_item_ids[0].with_user(self.admin).unlink()

        # Revision requires reason; re-issuing with 1 existing item + 1 new item creates ONLY 1 new task (no duplicate of first_task!)
        with self.assertRaises(UserError):
            minute.with_user(self.user_mgr).action_revise('   ')
        minute.with_user(self.user_mgr).action_revise('Bổ sung đầu việc thuyết minh tính toán')
        self.assertEqual(minute.version, 2)
        self.assertEqual(minute.state, 'confirmed')

        self.env['tp.meeting.action.item'].with_user(self.user_mgr).create({
            'minute_id': minute.id,
            'name': 'Lập thuyết minh tính toán tải trọng HL93',
            'assignee_user_id': self.user_eng.id,
        })
        minute.with_user(self.user_mgr).action_issue()
        self.assertEqual(minute.state, 'issued')
        self.assertEqual(minute.action_item_ids[0].task_id.id, first_task.id)
        self.assertTrue(minute.action_item_ids[1].task_id)
        self.assertNotEqual(minute.action_item_ids[0].task_id.id, minute.action_item_ids[1].task_id.id)

    def test_02_mandatory_case_09_announcement_explicit_ack_and_version_reack(self):
        """Case #9: Opening announcement never auto-acks; explicit button records ack; major v2 revision requires re-ack."""
        # Regular staff cannot publish company-wide announcement
        with self.assertRaises(AccessError):
            self.env['tp.announcement'].with_user(self.user_eng).create({
                'name': 'Thông báo trái thẩm quyền',
                'audience_scope': 'company',
                'body': 'Nội dung',
            })

        # Department manager creates & publishes to own department
        res = self.env['tp.announcement'].with_user(self.user_mgr).tp_save_announcement({
            'name': 'Quy định kiểm soát chất lượng bản vẽ Q4/2026',
            'category': 'policy',
            'issuing_department_id': self.dept_eng.id,
            'audience_scope': 'departments',
            'target_department_ids': [self.dept_eng.id],
            'body': 'Áp dụng checklist kiểm tra chéo 2 bước trước khi trình ký.',
            'require_ack': True,
        }, publish_now=True)
        self.assertTrue(res['ok'])
        ann_id = res['id']

        # Outsider in another department is blocked from reading department-scoped announcement (RPC + direct ORM)
        with self.assertRaises(AccessError):
            self.env['tp.announcement'].with_user(self.user_out).tp_announcement_detail_data(ann_id)
        with self.assertRaises(AccessError):
            self.env['tp.announcement'].with_user(self.user_out).browse(ann_id).read(['name', 'body'])
        self.assertEqual(
            self.env['tp.announcement'].with_user(self.user_out).search_count([('id', '=', ann_id)]),
            0,
        )

        # Recipient opens detail -> MUST NOT auto-acknowledge!
        detail_v1 = self.env['tp.announcement'].with_user(self.user_eng).tp_announcement_detail_data(ann_id)
        self.assertFalse(detail_v1['is_acked'])
        track_before = self.env['tp.announcement'].with_user(self.user_mgr).tp_get_ack_tracking(ann_id)
        self.assertIn(self.user_eng.id, [u['user_id'] for u in track_before['unacked_users']])

        # Recipient explicitly clicks "Xác nhận đã đọc"
        ack1 = self.env['tp.announcement'].with_user(self.user_eng).tp_acknowledge_announcement(ann_id, 'tok-1')
        self.assertFalse(ack1['already_acked'])
        self.assertEqual(ack1['acked_version'], 1)
        # Idempotent retry & ORM ack privacy check (F-A07-0002 / F-A07-0006)
        ack1_dup = self.env['tp.announcement'].with_user(self.user_eng).tp_acknowledge_announcement(ann_id, 'tok-1')
        self.assertTrue(ack1_dup['already_acked'])
        self.assertEqual(
            self.env['tp.announcement.ack'].with_user(self.user_out).search_count([('announcement_id', '=', ann_id)]),
            0,
        )

        # Major revision bumps to v2 -> recipient must re-acknowledge v2 while v1 ack audit remains intact!
        ann = self.env['tp.announcement'].browse(ann_id)
        ann.with_user(self.user_mgr).action_revise_published(
            {'body': 'Bổ sung phụ lục biểu mẫu kiểm tra cầu dây văng.'},
            major_reack=True,
            reason='Bổ sung phụ lục cầu dây văng',
        )
        detail_v2 = self.env['tp.announcement'].with_user(self.user_eng).tp_announcement_detail_data(ann_id)
        self.assertEqual(detail_v2['version'], 2)
        self.assertFalse(detail_v2['is_acked'])
        self.assertTrue(detail_v2['had_previous_version_ack'])

    def test_03_mandatory_cases_07_08_year_plan_task_pull_and_frozen_snapshot_immutability(self):
        """Cases #7 & #8: Year->Quarter->Month->Week plan hierarchy, task pull into draft report, and 100% immutable snapshot."""
        # Grant official 'plan' and 'review' capability assignments to user_mgr for dept_eng
        self.env['tp.report.assignment'].sudo().create([
            {
                'name': 'Phân quyền lập kế hoạch Phòng Cầu (Test)',
                'reason': 'Phân công lập kế hoạch năm/quý Phòng Cầu (Test)',
                'user_id': self.user_mgr.id,
                'company_id': self.company.id,
                'department_id': self.dept_eng.id,
                'capability': 'plan',
                'level': 'all',
                'date_start': date(2026, 1, 1),
            },
            {
                'name': 'Phân quyền rà soát báo cáo Phòng Cầu (Test)',
                'reason': 'Phân công rà soát báo cáo cá nhân Phòng Cầu (Test)',
                'user_id': self.user_mgr.id,
                'company_id': self.company.id,
                'department_id': self.dept_eng.id,
                'capability': 'review',
                'level': 'all',
                'date_start': date(2026, 1, 1),
            },
        ])
        Plan = self.env['tp.report.plan'].with_user(self.user_mgr)
        p_year = Plan.create({
            'name': 'Kế hoạch Năm 2026 Phòng Cầu',
            'period_type': 'year',
            'department_id': self.dept_eng.id,
            'owner_id': self.user_mgr.id,
            'target': 40.0,
            'unit': 'hồ sơ',
            'date_start': date(2026, 1, 1),
            'date_end': date(2026, 12, 31),
        })
        p_q4 = Plan.create({
            'name': 'Kế hoạch Quý 4/2026 Phòng Cầu',
            'period_type': 'quarter',
            'parent_id': p_year.id,
            'department_id': self.dept_eng.id,
            'owner_id': self.user_mgr.id,
            'target': 12.0,
            'unit': 'hồ sơ',
            'date_start': date(2026, 10, 1),
            'date_end': date(2026, 12, 31),
        })
        self.assertEqual(p_q4.parent_id, p_year)

        # Create an official work task (from meeting/plan) for user_eng and verify honest workload
        # (no hour estimate -> insufficient_data, not fake overload; private self-todos stay excluded!)
        self.env['project.task'].with_user(self.user_eng).create({
            'name': 'Việc cá nhân riêng tư không tính tải phòng ban',
            'user_ids': [Command.set([self.user_eng.id])],
            'tp_source_kind': 'self',
        })
        task = self.env['project.task'].with_user(self.user_eng).create({
            'name': 'Thiết kế mố M1 cầu sông Hàn',
            'user_ids': [Command.set([self.user_eng.id])],
            'date_deadline': date(2026, 11, 25),
            'tp_deliverable': 'Bản vẽ cốt thép mố M1',
            'tp_source_kind': 'meeting',
        })
        wl = self.env['project.task'].with_user(self.user_mgr).tp_get_honest_workload_summary(self.dept_eng.id)
        eng_wl = next(r for r in wl['rows'] if r['user_id'] == self.user_eng.id)
        self.assertEqual(eng_wl['open_task_count'], 1)
        self.assertEqual(eng_wl['workload_status'], 'insufficient_data')

        # Create draft weekly personal report document (Monday 2026-11-23 .. Sunday 2026-11-29) and pull task in idempotently
        doc = self.env['tp.report.document'].with_user(self.user_eng).create({
            'name': 'Báo cáo tuần 48/2026 - Kỹ sư Cầu',
            'period_type': 'week',
            'level': 'personal',
            'owner_id': self.user_eng.id,
            'reviewer_id': self.user_mgr.id,
            'department_id': self.dept_eng.id,
            'date_start': date(2026, 11, 23),
            'date_end': date(2026, 11, 29),
        })
        r1 = doc.with_user(self.user_eng).tp_load_tasks_into_draft([task.id])
        r2 = doc.with_user(self.user_eng).tp_load_tasks_into_draft([task.id])
        self.assertEqual(r1['loaded_count'], 1)
        self.assertEqual(r2['loaded_count'], 0)
        self.assertEqual(r2['updated_count'], 1)
        self.assertEqual(len(doc.line_ids), 1)

        # Submit report -> freezes snapshot!
        doc.invalidate_recordset(['version'])
        doc.with_user(self.user_eng).with_context(tp_reporting_expected_version=doc.version).action_submit()
        self.assertEqual(doc.state, 'submitted')
        snap = doc.current_snapshot_id
        self.assertTrue(snap)
        snap_payload_before = snap.payload
        self.assertIn('Thiết kế mố M1 cầu sông Hàn', snap_payload_before)

        # Now mutate the live project.task -> frozen report snapshot MUST NOT CHANGE (Mandatory Case #8)!
        task.with_user(self.user_eng).write({'name': 'Tên công việc đã đổi sau khi nộp báo cáo'})
        snap.invalidate_recordset(['payload'])
        self.assertEqual(snap.payload, snap_payload_before)
        self.assertIn('Thiết kế mố M1 cầu sông Hàn', snap.payload)
        self.assertNotIn('Tên công việc đã đổi sau khi nộp báo cáo', snap.payload)

    def test_04_meeting_minute_timezone_roundtrip_vn(self):
        """F-A06-0004: meeting_date_iso round-trips accurately between Asia/Ho_Chi_Minh local time and naive UTC."""
        self.user_mgr.sudo().write({'tz': 'Asia/Ho_Chi_Minh'})
        res = self.env['tp.meeting.minute'].with_user(self.user_mgr).tp_save_minute({
            'name': 'Họp giao ban 09:00 sáng giờ VN',
            'meeting_date_iso': '2026-11-27T09:00',
            'chair_user_id': self.user_mgr.id,
            'department_id': self.dept_eng.id,
        }, issue_now=False)
        self.assertTrue(res['ok'])
        minute = self.env['tp.meeting.minute'].browse(res['id'])
        # 09:00 Asia/Ho_Chi_Minh (+07:00) == 02:00 UTC
        self.assertEqual(minute.meeting_date, datetime(2026, 11, 27, 2, 0, 0))
        detail = self.env['tp.meeting.minute'].with_user(self.user_mgr).tp_minute_detail_data(minute.id)
        self.assertEqual(detail['meeting_date_iso'], '2026-11-27T09:00')
        self.assertIn('27/11/2026 09:00', detail['meeting_date_display'])
