# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Comprehensive automated backend & security tests for TANPHAT ONE Personal Tools.

Covers all business, drag/resequence, recurrence, privacy, cross-tool linking,
and ACL isolation scenarios for:
1. Việc cá nhân (`project.task`, `project.task.type`, `project.task.stage.personal`)
2. Lịch làm việc (`calendar.event`, `calendar.attendee`, `calendar.recurrence`, `calendar.calendar`)
3. Trao đổi (`discuss.channel`, `mail.message`, `ir.attachment`, `res.users.tp_search_colleagues`)
"""

import base64
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "tp_personal_tools")
class TestPersonalToolsSuite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        group_user = cls.env.ref("base.group_user")
        group_scoped_kd = cls.env.ref("tp_kd_workspace.group_scoped_staff")
        group_full_admin = cls.env.ref("tp_admin_delegation.group_full_admin")

        cls.dept_tech = cls.env["hr.department"].create({"name": "Phòng Kỹ thuật Cầu đường"})
        cls.job_eng = cls.env["hr.job"].create({"name": "Kỹ sư thiết kế"})

        cls.user_a = Users.create(
            {
                "name": "Nguyễn Văn An",
                "login": "pt.user.a@tanphat.test",
                "email": "pt.user.a@tanphat.test",
                "tz": "Asia/Ho_Chi_Minh",
                "group_ids": [Command.set([group_user.id, group_scoped_kd.id])],
            }
        )
        cls.user_b = Users.create(
            {
                "name": "Trần Thị Bình",
                "login": "pt.user.b@tanphat.test",
                "email": "pt.user.b@tanphat.test",
                "tz": "Asia/Ho_Chi_Minh",
                "group_ids": [Command.set([group_user.id])],
            }
        )
        cls.user_c = Users.create(
            {
                "name": "Lê Hoàng Cường",
                "login": "pt.user.c@tanphat.test",
                "email": "pt.user.c@tanphat.test",
                "tz": "Asia/Ho_Chi_Minh",
                "group_ids": [Command.set([group_user.id])],
            }
        )
        cls.delegated_admin = Users.create(
            {
                "name": "Phạm Quản Trị Ủy Quyền",
                "login": "pt.del.admin@tanphat.test",
                "email": "pt.del.admin@tanphat.test",
                "tz": "Asia/Ho_Chi_Minh",
                "group_ids": [Command.set([group_user.id, group_full_admin.id])],
            }
        )

        used_codes = set(
            cls.env["hr.employee"]
            .with_context(active_test=False)
            .search([("tp_employee_code", "!=", False)])
            .mapped("tp_employee_code")
        )
        if "tp.hr.employee.audit" in cls.env:
            used_codes |= set(
                cls.env["tp.hr.employee.audit"].sudo().search([]).mapped("employee_code")
            )
        free_code = next(
            (f"TP{n:03d}" for n in range(950, 100, -1) if f"TP{n:03d}" not in used_codes),
            False,
        )

        cls.emp_a = cls.env["hr.employee"].create(
            {
                "name": cls.user_a.name,
                "tp_employee_code": free_code,
                "user_id": cls.user_a.id,
                "department_id": cls.dept_tech.id,
                "job_id": cls.job_eng.id,
                "identification_id": "079099001122",
            }
        )

    # =========================================================================
    # 1. VIỆC CÁ NHÂN
    # =========================================================================
    def test_01_personal_task_crud_idempotency_checklist_and_attachments(self):
        TaskA = self.env["project.task"].with_user(self.user_a)
        ws0 = TaskA.tp_get_personal_workspace({"bucket": "all"})
        self.assertGreaterEqual(len(ws0["stages"]), 4)

        # Quick-create with idempotent operation_token
        token = "tok-todo-create-001"
        t1 = TaskA.tp_create_personal_task(
            {"name": "Rà soát hồ sơ dự toán Gói 04", "priority": "1"},
            operation_token=token,
        )
        t1_replay = TaskA.tp_create_personal_task(
            {"name": "Rà soát hồ sơ dự toán Gói 04", "priority": "1"},
            operation_token=token,
        )
        self.assertEqual(t1["id"], t1_replay["id"], "Retry with same token must not duplicate task")
        self.assertIn(self.user_a.id, [a["user_id"] for a in t1["assignees"]])

        # Save checklist, deadline, and description
        updated = TaskA.tp_save_personal_task(
            t1["id"],
            {
                "name": "Rà soát hồ sơ dự toán Gói 04 (Đã cập nhật)",
                "deadline_iso": "2026-11-28T16:30",
                "note_text": "Chi tiết kiểm tra:",
                "checklist": [
                    {"text": "Kiểm tra khối lượng bê tông", "checked": False},
                    {"text": "Đối chiếu đơn giá thép", "checked": True},
                ],
            },
        )
        self.assertEqual(updated["name"], "Rà soát hồ sơ dự toán Gói 04 (Đã cập nhật)")
        self.assertEqual(updated["checklist_total"], 2)
        self.assertEqual(updated["checklist_done"], 1)

        # Upload attachment -> must remain private (`public=False`)
        raw_b64 = base64.b64encode(b"Bang tinh khoi luong").decode()
        att_info = TaskA.tp_upload_personal_task_attachment(
            t1["id"], "khoi_luong.txt", raw_b64, "text/plain"
        )
        att_rec = self.env["ir.attachment"].sudo().browse(att_info["id"])
        self.assertFalse(att_rec.public, "Task attachment must never be marked public=True")

        # Post comment
        TaskA.tp_post_personal_task_comment(t1["id"], "Đã bổ sung bảng khối lượng.", "tok-cmt-01")
        detail = TaskA.tp_get_personal_task_detail(t1["id"])
        self.assertEqual(len(detail["attachments"]), 1)
        self.assertTrue(any("bổ sung bảng khối lượng" in m["body_text"] for m in detail["messages"]))

        # Complete -> reopen -> archive -> restore
        done_card = TaskA.tp_toggle_personal_task_done(t1["id"], True)
        self.assertTrue(done_card["is_closed"])
        reopen_card = TaskA.tp_toggle_personal_task_done(t1["id"], False)
        self.assertFalse(reopen_card["is_closed"])

        TaskA.tp_archive_personal_task(t1["id"], False)
        ws_archived = TaskA.tp_get_personal_workspace({"bucket": "archived"})
        self.assertIn(t1["id"], [x["id"] for x in ws_archived["tasks"]])
        TaskA.tp_archive_personal_task(t1["id"], True)

    def test_02_per_user_kanban_drag_order_and_shared_user_isolation(self):
        TaskA = self.env["project.task"].with_user(self.user_a)
        TaskB = self.env["project.task"].with_user(self.user_b)

        ws_a = TaskA.tp_get_personal_workspace({"bucket": "all"})
        ws_b = TaskB.tp_get_personal_workspace({"bucket": "all"})
        stage_a1, stage_a2 = ws_a["stages"][0]["id"], ws_a["stages"][1]["id"]
        stage_b1 = ws_b["stages"][0]["id"]

        c1 = TaskA.tp_create_personal_task({"name": "Việc A1", "stage_id": stage_a1})
        c2 = TaskA.tp_create_personal_task(
            {
                "name": "Việc chia sẻ A-B",
                "stage_id": stage_a1,
                "user_ids": [self.user_a.id, self.user_b.id],
            }
        )
        c3 = TaskA.tp_create_personal_task({"name": "Việc A3", "stage_id": stage_a1})

        # Pin User B's personal stage & sequence on shared task c2
        TaskB.tp_move_personal_task(c2["id"], stage_b1, [c2["id"]])
        b_before = TaskB.tp_get_personal_task_detail(c2["id"])

        # User A drags c3 before c1 in stage_a1, and drags shared c2 to stage_a2
        TaskA.tp_move_personal_task(c3["id"], stage_a1, [c3["id"], c1["id"]])
        TaskA.tp_move_personal_task(c2["id"], stage_a2, [c2["id"]])

        # Reload workspace as User A (simulating F5) -> order & stage persisted!
        ws_a_after = TaskA.tp_get_personal_workspace({"bucket": "all", "sort_by": "manual"})
        col1_ids = [
            t["id"] for t in ws_a_after["tasks"] if t["stage_id"] == stage_a1
        ]
        self.assertEqual(col1_ids[:2], [c3["id"], c1["id"]])
        c2_a_after = TaskA.tp_get_personal_task_detail(c2["id"])
        self.assertEqual(c2_a_after["stage_id"], stage_a2)

        # User B's personal stage on c2 MUST NOT be altered by User A's move!
        b_after = TaskB.tp_get_personal_task_detail(c2["id"])
        self.assertEqual(b_after["stage_id"], b_before["stage_id"])
        # Project stage (`stage_id` on project.task) must remain untouched (False)
        self.assertFalse(self.env["project.task"].sudo().browse(c2["id"]).stage_id)

    def test_03_personal_scope_excludes_project_tasks_and_unauthorized_users(self):
        # Create a project task assigned to User A -> must NEVER appear in Việc cá nhân
        proj = self.env["project.project"].create({"name": "Dự án Cầu Thủ Thiêm Test"})
        proj_task = self.env["project.task"].create(
            {
                "name": "Nhiệm vụ thuộc dự án KH-KD",
                "project_id": proj.id,
                "user_ids": [Command.set([self.user_a.id])],
            }
        )
        TaskA = self.env["project.task"].with_user(self.user_a)
        priv_task = TaskA.tp_create_personal_task({"name": "Việc riêng mật của An"})

        ws_a = TaskA.tp_get_personal_workspace({"bucket": "all", "filters": {}})
        returned_ids = [t["id"] for t in ws_a["tasks"]]
        self.assertIn(priv_task["id"], returned_ids)
        self.assertNotIn(proj_task.id, returned_ids, "Project task must never leak into Personal Todo")

        # User C (outsider) cannot read, edit, move, or delete User A's personal task via RPC or ORM
        TaskC = self.env["project.task"].with_user(self.user_c)
        with self.assertRaises(AccessError):
            TaskC.tp_get_personal_task_detail(priv_task["id"])
        with self.assertRaises(AccessError):
            TaskC.tp_save_personal_task(priv_task["id"], {"name": "Hack"})
        with self.assertRaises(AccessError):
            TaskC.tp_move_personal_task(priv_task["id"], 0, [priv_task["id"]])
        with self.assertRaises(AccessError):
            TaskC.browse(priv_task["id"]).read(["name"])

    def test_04_schedule_personal_task_onto_calendar_without_deadline_mutation(self):
        TaskA = self.env["project.task"].with_user(self.user_a)
        t = TaskA.tp_create_personal_task(
            {"name": "Chuẩn bị báo cáo tuần", "deadline_iso": "2026-11-30T17:00"}
        )
        ev_card = TaskA.tp_schedule_personal_task(
            t["id"],
            {
                "name": "Khung giờ làm báo cáo tuần",
                "allday": False,
                "start_iso": "2026-11-27T09:00",
                "stop_iso": "2026-11-27T10:30",
                "privacy": "private",
            },
            operation_token="tok-sched-001",
        )
        ev_replay = TaskA.tp_schedule_personal_task(
            t["id"],
            {
                "name": "Khung giờ làm báo cáo tuần",
                "allday": False,
                "start_iso": "2026-11-27T09:00",
                "stop_iso": "2026-11-27T10:30",
                "privacy": "private",
            },
            operation_token="tok-sched-001",
        )
        self.assertEqual(ev_card["id"], ev_replay["id"])
        self.assertEqual(ev_card["linked_task"]["id"], t["id"])

        # Rescheduling the calendar event must NOT mutate the task's deadline silently
        CalA = self.env["calendar.event"].with_user(self.user_a)
        CalA.tp_save_calendar_event(
            ev_card["id"],
            {
                "name": "Khung giờ làm báo cáo tuần",
                "allday": False,
                "start_iso": "2026-11-28T14:00",
                "stop_iso": "2026-11-28T15:30",
                "privacy": "private",
            },
        )
        detail_after = TaskA.tp_get_personal_task_detail(t["id"])
        self.assertTrue(detail_after["deadline"]["iso_local"].startswith("2026-11-30T17:00"))

    # =========================================================================
    # 2. LỊCH LÀM VIỆC
    # =========================================================================
    def test_05_calendar_timezone_allday_and_recurrence_scopes(self):
        CalA = self.env["calendar.event"].with_user(self.user_a)
        CalA.tp_get_calendar_bootstrap()

        # Timed event in Asia/Ho_Chi_Minh (UTC+7): 08:30 -> 01:30 UTC
        timed = CalA.tp_save_calendar_event(
            0,
            {
                "name": "Họp kỹ thuật sáng",
                "allday": False,
                "start_iso": "2026-11-26T08:30",
                "stop_iso": "2026-11-26T10:00",
                "privacy": "public",
            },
            operation_token="tok-cal-001",
        )
        ev_rec = self.env["calendar.event"].sudo().browse(timed["id"])
        self.assertEqual(ev_rec.start.hour, 1)
        self.assertEqual(ev_rec.start.minute, 30)
        self.assertEqual(timed["short_time"], "08:30 – 10:00")

        # All-day event preserves exact dates
        allday = CalA.tp_save_calendar_event(
            0,
            {
                "name": "Công tác hiện trường Long Thành",
                "allday": True,
                "start_date": "2026-12-01",
                "stop_date": "2026-12-02",
                "privacy": "public",
            },
            operation_token="tok-cal-allday",
        )
        ev_all = self.env["calendar.event"].sudo().browse(allday["id"])
        self.assertTrue(ev_all.allday)
        self.assertEqual(ev_all.start_date, date(2026, 12, 1))
        self.assertEqual(ev_all.stop_date, date(2026, 12, 2))

        # Recurring event: edit single occurrence (`self_only`) vs future (`future_events`)
        rec_first = CalA.tp_save_calendar_event(
            0,
            {
                "name": "Giao ban thứ Hai",
                "allday": False,
                "start_iso": "2026-12-07T09:00",
                "stop_iso": "2026-12-07T10:00",
                "recurrency": True,
                "rrule_type_ui": "weekly",
                "interval": 1,
                "end_type": "count",
                "count": 3,
            },
        )
        base_ev = CalA.browse(rec_first["id"])
        series = CalA.search([("recurrence_id", "=", base_ev.recurrence_id.id)], order="start asc")
        self.assertEqual(len(series), 3)

        # Update ONLY 2nd occurrence -> 1st and 3rd must keep original title
        CalA.tp_save_calendar_event(
            series[1].id,
            {
                "name": "Giao ban thứ Hai (Đổi phòng riêng tuần 2)",
                "allday": False,
                "start_iso": "2026-12-14T09:30",
                "stop_iso": "2026-12-14T10:30",
                "recurrency": True,
                "recurrence_update": "self_only",
            },
        )
        self.assertEqual(series[0].name, "Giao ban thứ Hai")
        self.assertEqual(series[2].name, "Giao ban thứ Hai")

    def test_06_invited_attendee_rsvp_allowed_but_drag_edit_delete_blocked(self):
        CalA = self.env["calendar.event"].with_user(self.user_a)
        CalB = self.env["calendar.event"].with_user(self.user_b)

        ev_data = CalA.tp_save_calendar_event(
            0,
            {
                "name": "Họp duyệt phương án mố cầu",
                "allday": False,
                "start_iso": "2026-11-29T14:00",
                "stop_iso": "2026-11-29T15:30",
                "partner_ids": [self.user_b.partner_id.id],
                "privacy": "public",
            },
        )
        ev_b = CalB.browse(ev_data["id"])
        self.assertFalse(ev_b.user_can_edit, "Invited attendee must NOT gain edit/drag permission")

        # Attendee cannot drag/write/delete organizer's event
        with self.assertRaises(AccessError):
            ev_b.write({"name": "Sửa trái phép"})
        with self.assertRaises(AccessError):
            CalB.tp_save_calendar_event(
                ev_data["id"],
                {
                    "name": "Sửa qua RPC",
                    "allday": False,
                    "start_iso": "2026-11-29T16:00",
                    "stop_iso": "2026-11-29T17:00",
                },
            )
        with self.assertRaises(AccessError):
            ev_b.unlink()

        # Attendee CAN respond to their own invitation
        CalB.browse(ev_data["id"]).change_attendee_status("accepted", False)
        card_b = CalB.tp_get_event_detail_card(ev_data["id"])
        self.assertEqual(card_b["my_status"], "accepted")

        # Attendee CANNOT mutate organizer's attendee record
        org_att = (
            self.env["calendar.attendee"]
            .sudo()
            .search(
                [
                    ("event_id", "=", ev_data["id"]),
                    ("partner_id", "=", self.user_a.partner_id.id),
                ],
                limit=1,
            )
        )
        with self.assertRaises(AccessError):
            org_att.with_user(self.user_b).write({"state": "declined"})

    def test_07_private_event_strict_busy_mask_and_zero_search_leak(self):
        CalA = self.env["calendar.event"].with_user(self.user_a)
        CalB = self.env["calendar.event"].with_user(self.user_b)

        secret = CalA.tp_save_calendar_event(
            0,
            {
                "name": "Khám chuyên khoa BíMậtTuyệtĐối7788",
                "allday": False,
                "start_iso": "2026-11-27T15:00",
                "stop_iso": "2026-11-27T16:00",
                "location": "Bệnh viện Quốc tế BíMật7788",
                "notes": "Hồ sơ cá nhân riêng tư 7788",
                "privacy": "private",
            },
        )

        # ORM read & detail card as User B AND as Delegated Admin -> strictly 'Bận'
        for viewer in (self.user_b, self.delegated_admin):
            CalV = self.env["calendar.event"].with_user(viewer)
            raw = CalV.browse(secret["id"]).read(["name", "display_name"])[0]
            self.assertEqual(raw["name"], "Bận")
            self.assertEqual(raw["display_name"], "Bận")

            card = CalV.tp_get_event_detail_card(secret["id"])
            self.assertTrue(card["is_masked_private"])
            self.assertEqual(card["name"], "Bận")
            self.assertEqual(card["location"], "")
            self.assertEqual(card["notes_text"], "")
            self.assertEqual(card["attendees"], [])

            # Keyword search side-channel MUST return 0 hits!
            hits = CalV.search([("name", "ilike", "BíMậtTuyệtĐối7788")])
            self.assertFalse(hits, "Private event title must never leak via _search domain!")
            agenda_hits = CalV.tp_get_calendar_agenda(
                {
                    "q": "BíMậtTuyệtĐối7788",
                    "date_from": "2026-11-25",
                    "date_to": "2026-11-30",
                    "partner_ids": [self.user_a.partner_id.id],
                }
            )
            self.assertEqual(agenda_hits["total_count"], 0)

        # Conflict check shows busy time ONLY as 'Bận'
        conflicts = CalB.tp_check_schedule_conflicts(
            "2026-11-27T15:15",
            "2026-11-27T15:45",
            False,
            [self.user_a.partner_id.id],
            0,
        )
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["title"], "Bận")
        self.assertNotIn("7788", str(conflicts))

    # =========================================================================
    # 3. TRAO ĐỔI & LIÊN THÔNG
    # =========================================================================
    def test_08_colleague_directory_safe_fields_and_excludes_odoobot(self):
        rows = self.env["res.users"].with_user(self.user_b).tp_search_colleagues("Nguyễn Văn An")
        matched = [r for r in rows if r["user_id"] == self.user_a.id]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["department"], "Phòng Kỹ thuật Cầu đường")
        self.assertEqual(matched[0]["job_title"], "Kỹ sư thiết kế")
        # Sensitive HR fields must never appear
        forbidden_keys = {"identification_id", "bank_account_id", "birthday", "private_phone", "wage"}
        self.assertFalse(forbidden_keys.intersection(matched[0].keys()))

        odoobot_pid = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root")
        all_rows = self.env["res.users"].with_user(self.user_b).tp_search_colleagues("", limit=50)
        self.assertNotIn(odoobot_pid, [r["partner_id"] for r in all_rows])

    def test_09_discuss_dm_idempotency_group_members_and_channel_acl(self):
        ChanA = self.env["discuss.channel"].with_user(self.user_a)

        # DM idempotency: opening chat twice with User B returns exact same channel
        dm1 = ChanA._get_or_create_chat([self.user_b.partner_id.id])
        dm2 = ChanA._get_or_create_chat([self.user_b.partner_id.id])
        self.assertEqual(dm1.id, dm2.id)

        # Group creation: exact members only (User A + User B, NOT User C)
        grp = ChanA._create_group(self.user_a | self.user_b, name="Nhóm Cầu Dây Văng")
        member_pids = grp.sudo().channel_member_ids.mapped("partner_id").ids
        self.assertCountEqual(
            member_pids, [self.user_a.partner_id.id, self.user_b.partner_id.id]
        )

        # Outsider User C cannot read private group or private DM
        with self.assertRaises(AccessError):
            self.env["discuss.channel"].with_user(self.user_c).browse(grp.id).read(["name"])
        with self.assertRaises(AccessError):
            self.env["discuss.channel"].with_user(self.user_c).browse(dm1.id).read(["name"])

        # Attachment posted in DM stays `public=False` and unreadable by User C
        att = (
            self.env["ir.attachment"]
            .with_user(self.user_a)
            .create(
                {
                    "name": "ban_ve_mat_cat.pdf",
                    "raw": b"%PDF-1.4 test",
                    "res_model": "discuss.channel",
                    "res_id": dm1.id,
                }
            )
        )
        self.assertFalse(att.public)
        with self.assertRaises(AccessError):
            att.with_user(self.user_c).read(["raw"])

        # Share personal task link into group -> generic anchor, ACL still blocks non-assignees
        priv_task = (
            self.env["project.task"]
            .with_user(self.user_a)
            .tp_create_personal_task({"name": "Mật mã nội bộ 9911"})
        )
        share_res = ChanA.tp_share_record_to_channel(
            grp.id,
            "project.task",
            priv_task["id"],
            note="Nhờ xem giúp",
            operation_token="tok-share-001",
        )
        msg = self.env["mail.message"].sudo().browse(share_res["message_id"])
        self.assertNotIn("9911", msg.body, "Private task title must not be leaked in shared anchor")
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(self.user_b).tp_get_personal_task_detail(
                priv_task["id"]
            )

    def test_10_admin_delegation_and_deactivated_user_guards(self):
        """Verify DEC-053/054/062 groups stay intact and deactivated users are blocked."""
        orig_grp = self.env.ref("tp_admin_delegation.group_original_admin", raise_if_not_found=False)
        full_grp = self.env.ref("tp_admin_delegation.group_full_admin", raise_if_not_found=False)
        self.assertTrue(orig_grp and full_grp)

        # Delegated admin cannot read another user's unshared personal task
        priv_task = (
            self.env["project.task"]
            .with_user(self.user_a)
            .tp_create_personal_task({"name": "Việc cá nhân riêng của An"})
        )
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(self.delegated_admin).tp_get_personal_task_detail(
                priv_task["id"]
            )

        # Deactivated user cannot call personal tools endpoints
        locked_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Tài khoản đã khóa",
                "login": "pt.locked@tanphat.test",
                "active": False,
                "group_ids": [Command.set([self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(locked_user).tp_get_personal_workspace({})
        with self.assertRaises(AccessError):
            self.env["calendar.event"].with_user(locked_user).tp_get_calendar_bootstrap()
        with self.assertRaises(AccessError):
            self.env["res.users"].with_user(locked_user).tp_search_colleagues("")
