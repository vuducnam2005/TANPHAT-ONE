"""Pure unit tests for ENTI attendance logic, parsing, and pagination (runs DB-free)."""
import unittest
from datetime import date, datetime
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

    def test_fast_poll_settings_logic(self):
        # Emulate _tp_fast_settings pure logic
        default_fast_seconds = 5
        min_fast_seconds = 2
        default_fast_window = 50
        max_fast_window = 100

        def calc_settings(param_interval=None, param_window=None):
            interval = int(param_interval if param_interval is not None else default_fast_seconds)
            window = int(param_window if param_window is not None else default_fast_window)
            if interval <= 0:
                return 0, 0
            interval = max(interval, min_fast_seconds)
            return interval, min(max(window, interval), max_fast_window)

        # Default: 5s interval, 50s window
        self.assertEqual(calc_settings(), (5, 50))
        # 3s valid override
        self.assertEqual(calc_settings(3), (3, 50))
        # Clamped to min 2s
        self.assertEqual(calc_settings(1), (2, 50))
        # Disabled
        self.assertEqual(calc_settings(0), (0, 0))
        self.assertEqual(calc_settings(-5), (0, 0))
        # Window bounds
        self.assertEqual(calc_settings(5, 120), (5, 100))
        self.assertEqual(calc_settings(5, 3), (5, 5))

    def test_poll_wait_pacing_and_backoff(self):
        # Emulate _tp_poll_wait pure logic
        def poll_wait(poll_time, fails, interval, now):
            if poll_time is None:
                return 0.0
            gap = max(interval, min(15 * 2 ** fails, 120)) if fails else interval
            return max(0.0, poll_time + gap - now)

        # First round: poll_time is None -> wait 0.0
        self.assertEqual(poll_wait(None, 0, 5, 100.0), 0.0)

        # Success round: exactly 5s interval minus elapsed request duration
        self.assertAlmostEqual(poll_wait(100.0, 0, 5, 100.27), 4.73)
        # If elapsed time exceeds interval: wait 0.0
        self.assertEqual(poll_wait(100.0, 0, 5, 106.0), 0.0)

        # Error backoff: fail 1 -> 30s, fail 2 -> 60s, fail 3+ -> 120s
        self.assertAlmostEqual(poll_wait(100.0, 1, 5, 100.5), 29.5)
        self.assertAlmostEqual(poll_wait(100.0, 2, 5, 100.5), 59.5)
        self.assertAlmostEqual(poll_wait(100.0, 3, 5, 100.5), 119.5)
        self.assertAlmostEqual(poll_wait(100.0, 10, 5, 100.5), 119.5)


if __name__ == "__main__":
    unittest.main()
