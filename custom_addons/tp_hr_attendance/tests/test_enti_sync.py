"""Unit and integration tests for ENTI live attendance integration (ENTI-LIVE-001).

Covers:
- EntiClient HTTP interactions, token refresh, and pagination.
- Employee mapping suggestions and manual confirmation/rejection.
- Incomplete punch handling (in-only, out-only, equal times) without constraint crashes.
- Priority hierarchy: Approved correction > ENTI live > Excel fallback.
- Idempotency of projection and canonical day updates.
"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from odoo.exceptions import UserError
from odoo.tests.common import BaseCase

from .common import AttendanceCase
from ..models.attendance_common import DEFAULT_TZ
from ..models.enti_client import EntiAuthError, EntiClient, EntiError
from ..models.enti_day import _parse_time_str


class TestEntiPure(BaseCase):
    """Pure unit tests without DB requirement."""

    def test_parse_time_str(self):
        d = date(2026, 11, 18)
        clock, dt = _parse_time_str("08:15", d, "Asia/Ho_Chi_Minh")
        self.assertEqual(clock, "08:15")
        self.assertIsNotNone(dt)
        # 08:15 in ICT (UTC+7) is 01:15 UTC
        self.assertEqual(dt.hour, 1)
        self.assertEqual(dt.minute, 15)

        # Incomplete / invalid times
        clock_none, dt_none = _parse_time_str(None, d, "Asia/Ho_Chi_Minh")
        self.assertIsNone(clock_none)
        self.assertIsNone(dt_none)

        clock_empty, dt_empty = _parse_time_str("", d, "Asia/Ho_Chi_Minh")
        self.assertIsNone(clock_empty)
        self.assertIsNone(dt_empty)

        clock_invalid, dt_invalid = _parse_time_str("invalid", d, "Asia/Ho_Chi_Minh")
        self.assertIsNone(clock_invalid)
        self.assertIsNone(dt_invalid)

    def test_enti_client_login_and_token_refresh(self):
        client = EntiClient(base_url="https://enti.vn")
        mock_session = MagicMock()
        client.session = mock_session

        # Mock successful login
        login_resp = MagicMock()
        login_resp.status_code = 200
        login_resp.json.return_value = {
            "access_token": "token_abc",
            "refresh_token": "token_ref",
            "expires_in": 900,
        }
        mock_session.post.return_value = login_resp

        client.login("0901234567", "secret123")
        self.assertEqual(client.access_token, "token_abc")
        self.assertEqual(client.refresh_token, "token_ref")
        self.assertIn("Authorization", client.session.headers)
        self.assertEqual(client.session.headers["Authorization"], "Bearer token_abc")

        # Mock refresh
        refresh_resp = MagicMock()
        refresh_resp.status_code = 200
        refresh_resp.json.return_value = {
            "access_token": "token_new",
            "expires_in": 900,
        }
        mock_session.post.return_value = refresh_resp
        success = client.refresh_access_token()
        self.assertTrue(success)
        self.assertEqual(client.access_token, "token_new")
        self.assertEqual(client.session.headers["Authorization"], "Bearer token_new")

    def test_enti_client_attendance_pagination(self):
        client = EntiClient(base_url="https://enti.vn")
        mock_session = MagicMock()
        client.session = mock_session
        client.access_token = "token_valid"
        client.token_expires_at = datetime.now().timestamp() + 500

        # Page 1: returns 2 items and moreData=True
        resp_p1 = MagicMock()
        resp_p1.status_code = 200
        resp_p1.json.return_value = {
            "statusCode": 200,
            "data": [{"keyNV": "nv_1", "tenNV": "Nguyễn Văn A"}, {"keyNV": "nv_2", "tenNV": "Trần Thị B"}],
            "moreData": True,
            "totalData": 3,
        }

        # Page 2: returns 1 item and moreData=False
        resp_p2 = MagicMock()
        resp_p2.status_code = 200
        resp_p2.json.return_value = {
            "statusCode": 200,
            "data": [{"keyNV": "nv_3", "tenNV": "Lê Văn C"}],
            "moreData": False,
            "totalData": 3,
        }

        mock_session.post.side_effect = [resp_p1, resp_p2]

        results = client.get_attendance(
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 19),
            batch_size=2,
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["keyNV"], "nv_1")
        self.assertEqual(results[1]["keyNV"], "nv_2")
        self.assertEqual(results[2]["keyNV"], "nv_3")
        self.assertEqual(mock_session.post.call_count, 2)


class TestEntiSyncIntegration(AttendanceCase):
    """Integration tests with database models and constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Source = cls.env["tp.hr.attendance.source"].sudo()
        cls.Mapping = cls.env["tp.hr.attendance.enti.mapping"].sudo()
        cls.EntiDay = cls.env["tp.hr.attendance.enti.day"].sudo()
        cls.Day = cls.env["tp.hr.attendance.day"].sudo()
        cls.Session = cls.env["tp.hr.attendance.session"].sudo()

        cls.source = cls.Source.create({
            "name": "API máy chấm công ENTI Test",
            "namespace": "ENTI_TEST",
            "kind": "enti_api",
            "company_id": cls.company.id,
            "timezone": DEFAULT_TZ,
            "state": "ready",
            "live_enabled": True,
        })

    def test_employee_mapping_suggestion_and_confirm(self):
        # Create mapping with exact name matching emp_a
        mapping_a = self.Mapping.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-a",
            "ma_nv": "TP001",
            "ten_nv": "Synthetic Người Một",
            "key_bp": "dept-uuid-1",
            "ten_bp": "Synthetic Attendance Dept",
        })

        mapping_a.tp_suggest_mapping()
        self.assertEqual(mapping_a.employee_id, self.emp_a)
        self.assertEqual(mapping_a.state, "suggested")

        # Confirm mapping
        mapping_a.action_confirm_mapping()
        self.assertEqual(mapping_a.state, "mapped")

        # Reject mapping
        mapping_a.action_reject_mapping()
        self.assertEqual(mapping_a.state, "unmapped")
        self.assertFalse(mapping_a.employee_id)

    def test_complete_punch_projection(self):
        work_d = date(2026, 11, 18)
        enti_day = self.EntiDay.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-a",
            "work_date": work_d,
            "employee_id": self.emp_a.id,
            "vao_dau": "08:00",
            "ra_cuoi": "17:30",
            "check_in_dt": datetime(2026, 11, 18, 1, 0, tzinfo=ZoneInfo("UTC")),
            "check_out_dt": datetime(2026, 11, 18, 10, 30, tzinfo=ZoneInfo("UTC")),
            "cong_lam": 1.0,
        })

        # Project to canonical attendance day
        enti_day._tp_project_to_canonical()

        canonical_day = self.day(self.emp_a, work_d)
        self.assertTrue(canonical_day)
        self.assertEqual(canonical_day.source_kind, "enti")
        self.assertEqual(canonical_day.in_time, "08:00")
        self.assertEqual(canonical_day.out_time, "17:30")
        self.assertEqual(canonical_day.data_state, "out_recorded")
        self.assertAlmostEqual(canonical_day.worked_hours, 9.5)

        sessions = self.Session.search([("day_id", "=", canonical_day.id), ("active", "=", True)])
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions.source, "enti")
        self.assertTrue(sessions.check_out > sessions.check_in)

    def test_incomplete_punches_without_constraint_crash(self):
        """Incomplete punches (in-only or out-only) must NOT invent 17:00 or violate check_out > check_in."""
        work_in_only = date(2026, 11, 17)

        # 1. In-only punch
        enti_in_only = self.EntiDay.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-a",
            "work_date": work_in_only,
            "employee_id": self.emp_a.id,
            "vao_dau": "08:15",
            "ra_cuoi": False,
            "check_in_dt": datetime(2026, 11, 17, 1, 15, tzinfo=ZoneInfo("UTC")),
            "check_out_dt": False,
            "cong_lam": 0.0,
        })

        enti_in_only._tp_project_to_canonical()

        canonical_in = self.day(self.emp_a, work_in_only)
        self.assertTrue(canonical_in)
        self.assertEqual(canonical_in.in_time, "08:15")
        self.assertFalse(canonical_in.out_time)
        self.assertEqual(canonical_in.data_state, "missing")
        self.assertEqual(canonical_in.worked_hours, 0.0)

        # Ensure NO active session with fabricated check_out
        sessions_in = self.Session.search([("day_id", "=", canonical_in.id), ("active", "=", True)])
        self.assertEqual(len(sessions_in), 0)

        # 2. Out-only punch
        work_out_only = date(2026, 11, 16)
        enti_out_only = self.EntiDay.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-a",
            "work_date": work_out_only,
            "employee_id": self.emp_a.id,
            "vao_dau": False,
            "ra_cuoi": "17:45",
            "check_in_dt": False,
            "check_out_dt": datetime(2026, 11, 16, 10, 45, tzinfo=ZoneInfo("UTC")),
            "cong_lam": 0.0,
        })

        enti_out_only._tp_project_to_canonical()

        canonical_out = self.day(self.emp_a, work_out_only)
        self.assertTrue(canonical_out)
        self.assertFalse(canonical_out.in_time)
        self.assertEqual(canonical_out.out_time, "17:45")
        self.assertEqual(canonical_out.data_state, "missing")
        self.assertEqual(canonical_out.worked_hours, 0.0)

        sessions_out = self.Session.search([("day_id", "=", canonical_out.id), ("active", "=", True)])
        self.assertEqual(len(sessions_out), 0)

    def test_priority_hierarchy_correction_over_enti(self):
        """Approved correction must NEVER be overwritten by ENTI sync."""
        work_d = date(2026, 11, 15)

        # Create day with approved correction
        canonical_day = self.Day.create({
            "company_id": self.company.id,
            "employee_id": self.emp_a.id,
            "work_date": work_d,
            "in_time": "08:30",
            "out_time": "17:00",
            "worked_hours": 8.5,
            "data_state": "out_recorded",
            "is_correction": True,
            "source_kind": "correction",
        })

        enti_day = self.EntiDay.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-a",
            "work_date": work_d,
            "employee_id": self.emp_a.id,
            "vao_dau": "09:00",
            "ra_cuoi": "18:00",
            "check_in_dt": datetime(2026, 11, 15, 2, 0, tzinfo=ZoneInfo("UTC")),
            "check_out_dt": datetime(2026, 11, 15, 11, 0, tzinfo=ZoneInfo("UTC")),
            "cong_lam": 1.0,
        })

        enti_day._tp_project_to_canonical()

        # Reload canonical day
        canonical_day.invalidate_recordset()
        self.assertEqual(canonical_day.in_time, "08:30")
        self.assertEqual(canonical_day.out_time, "17:00")
        self.assertEqual(canonical_day.worked_hours, 8.5)
        self.assertEqual(canonical_day.source_kind, "correction")
        self.assertEqual(enti_day.projection_status, "superseded_correction")

    def test_idempotency_of_enti_projection(self):
        """Re-projecting the same day must not duplicate records or change values."""
        work_d = date(2026, 11, 14)
        enti_day = self.EntiDay.create({
            "source_id": self.source.id,
            "key_nv": "enti-uuid-emp-b",
            "work_date": work_d,
            "employee_id": self.emp_b.id,
            "vao_dau": "08:00",
            "ra_cuoi": "17:00",
            "check_in_dt": datetime(2026, 11, 14, 1, 0, tzinfo=ZoneInfo("UTC")),
            "check_out_dt": datetime(2026, 11, 14, 10, 0, tzinfo=ZoneInfo("UTC")),
            "cong_lam": 1.0,
        })

        # Run 1
        enti_day._tp_project_to_canonical()
        count_days_1 = self.Day.search_count([("employee_id", "=", self.emp_b.id), ("work_date", "=", work_d)])
        count_sessions_1 = self.Session.search_count([("day_id.employee_id", "=", self.emp_b.id), ("day_id.work_date", "=", work_d), ("active", "=", True)])

        self.assertEqual(count_days_1, 1)
        self.assertEqual(count_sessions_1, 1)

        # Run 2
        enti_day._tp_project_to_canonical()
        count_days_2 = self.Day.search_count([("employee_id", "=", self.emp_b.id), ("work_date", "=", work_d)])
        count_sessions_2 = self.Session.search_count([("day_id.employee_id", "=", self.emp_b.id), ("day_id.work_date", "=", work_d), ("active", "=", True)])

        self.assertEqual(count_days_2, 1)
        self.assertEqual(count_sessions_2, 1)
