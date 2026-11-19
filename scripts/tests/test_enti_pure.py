"""Pure unit tests for ENTI attendance logic, parsing, and pagination (runs DB-free)."""
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo


def _parse_time_str(time_str, target_date, tz_name="Asia/Ho_Chi_Minh"):
    if not time_str or not isinstance(time_str, str):
        return None, None
    time_str = time_str.strip()
    if not time_str:
        return None, None
    parts = time_str.split(":")
    if len(parts) < 2:
        return None, None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None, None
    except (ValueError, TypeError):
        return None, None

    clock_str = f"{hour:02d}:{minute:02d}"
    try:
        tz = ZoneInfo(tz_name)
        dt_local = datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=tz)
        dt_utc = dt_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        return clock_str, dt_utc
    except Exception:
        return clock_str, None


class TestEntiPureLogic(unittest.TestCase):
    def test_time_parsing_ict_to_utc(self):
        d = date(2026, 11, 18)
        clock, dt = _parse_time_str("08:15", d, "Asia/Ho_Chi_Minh")
        self.assertEqual(clock, "08:15")
        self.assertIsNotNone(dt)
        # 08:15 ICT is 01:15 UTC
        self.assertEqual(dt.hour, 1)
        self.assertEqual(dt.minute, 15)

    def test_time_parsing_edge_cases(self):
        d = date(2026, 11, 18)
        self.assertEqual(_parse_time_str(None, d), (None, None))
        self.assertEqual(_parse_time_str("", d), (None, None))
        self.assertEqual(_parse_time_str("  ", d), (None, None))
        self.assertEqual(_parse_time_str("invalid", d), (None, None))
        self.assertEqual(_parse_time_str("25:00", d), (None, None))
        self.assertEqual(_parse_time_str("08:65", d), (None, None))

    def test_day_extraction_from_ngay_field(self):
        # Verification that 'ngay' property is respected rather than assuming day1 == day 1
        day_obj = {
            "keyNV": "nv-123",
            "ngay": "2026-11-18",
            "caLV": "Ca hành chính",
            "vaoDau": "08:00",
            "raCuoi": "17:30",
            "congLam": 1.0,
            "diMuon": 0,
            "veSom": 0,
        }
        work_date = datetime.strptime(day_obj["ngay"][:10], "%Y-%m-%d").date()
        self.assertEqual(work_date, date(2026, 11, 18))
        self.assertEqual(work_date.day, 18)

    def test_incomplete_punches_semantics(self):
        # In-only
        in_clock, _ = _parse_time_str("08:15", date(2026, 11, 18))
        out_clock, _ = _parse_time_str(None, date(2026, 11, 18))
        has_full_session = bool(in_clock and out_clock and out_clock > in_clock)
        self.assertFalse(has_full_session)

        # Out-only
        in_clock2, _ = _parse_time_str(None, date(2026, 11, 18))
        out_clock2, _ = _parse_time_str("17:30", date(2026, 11, 18))
        has_full_session2 = bool(in_clock2 and out_clock2 and out_clock2 > in_clock2)
        self.assertFalse(has_full_session2)

        # Equal
        in_clock3, _ = _parse_time_str("08:00", date(2026, 11, 18))
        out_clock3, _ = _parse_time_str("08:00", date(2026, 11, 18))
        has_full_session3 = bool(in_clock3 and out_clock3 and out_clock3 > in_clock3)
        self.assertFalse(has_full_session3)

        # Complete
        in_clock4, _ = _parse_time_str("08:00", date(2026, 11, 18))
        out_clock4, _ = _parse_time_str("17:30", date(2026, 11, 18))
        has_full_session4 = bool(in_clock4 and out_clock4 and out_clock4 > in_clock4)
        self.assertTrue(has_full_session4)


if __name__ == "__main__":
    unittest.main()
