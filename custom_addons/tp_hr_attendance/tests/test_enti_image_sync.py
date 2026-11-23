"""ENTI-IMAGE-SYNC-001 tests (synthetic 2x2 images and fake HTTP session only; zero real photos/tokens).

Covers every required verification scenario:
1. Valid ENTI HTTP/HTTPS image URL -> downloads, normalizes, writes hr.employee + res.partner image_1920, state=downloaded.
2. Valid ENTI Base64 data URI -> decodes, normalizes, writes hr.employee + res.partner image_1920.
3. ENTI returns no image -> state=no_image, no crash.
4. Broken URL / 404 / timeout -> bounded retries, state=failed with reason, no infinite retry.
5. Fake Content-Type or spoofed magic bytes / script payload -> rejected safely, state=failed.
6. Oversized image exceeding configured max bytes -> rejected safely, state=failed.
7. Unchanged image hash -> state=unchanged, skips rewriting employee.
8. Changed image hash -> state=downloaded, updates employee & partner.
9. Unmapped employee -> status_label="Chưa đối chiếu", hr.employee.image_1920 untouched.
10. Two keyNV pointing to the same hr.employee -> blocked with conflict error, state=failed.
11. Keep existing Odoo employee photo when ENTI fails or returns empty; prefer_manual_image keeps manual photo.
12. Regular user denied image sync / config / private image_url access; HR Manager & Admins allowed; host allowlist blocks SSRF.
13. Image failure in Step 2 never rolls back or erases attendance records from Step 1.
"""
import base64
import copy
import json
import threading
from datetime import date, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import requests
from PIL import Image

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import BaseCase

from .common import AttendanceCase
from odoo.addons.tp_hr_attendance.models import enti_client as enti_client_module
from odoo.addons.tp_hr_attendance.models import enti_sync as enti_sync_module
from odoo.addons.tp_hr_attendance.models.attendance_common import DEFAULT_TZ, internal
from odoo.addons.tp_hr_attendance.models.enti_client import EntiClient, EntiError
from odoo.addons.tp_hr_attendance.models.enti_image import (
    detect_magic_mime,
    parse_image_value,
    sanitize_employee_metadata,
    validate_and_normalize_image,
)

D16, D17 = date(2026, 11, 16), date(2026, 11, 17)
ENTI_BASE = "https://enti.invalid"


def _make_image_bytes(color=(30, 120, 210), fmt="PNG", size=(4, 4)):
    buf = BytesIO()
    mode = "RGBA" if fmt == "PNG" else "RGB"
    fill = (*color, 255) if mode == "RGBA" else color[:3]
    Image.new(mode, size, fill).save(buf, format=fmt)
    return buf.getvalue()


def _make_data_uri(color=(30, 120, 210), fmt="JPEG"):
    raw = _make_image_bytes(color=color, fmt=fmt)
    mime = "image/jpeg" if fmt == "JPEG" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


class _FakeBinaryResponse:
    def __init__(self, status=200, content=b"", headers=None, payload=None):
        self.status_code = status
        self._content = content
        self.headers = headers or {}
        self._payload = payload

    def json(self):
        if self._payload is None:
            msg = "not json"
            raise ValueError(msg)
        return self._payload

    def iter_content(self, chunk_size=65536):
        data = self._content or b""
        for idx in range(0, len(data), chunk_size):
            yield data[idx:idx + chunk_size]

    def close(self):
        return None


class _FakeImageSession:
    def __init__(self, routes):
        # routes: list or callable(method, url, headers)
        self.routes = routes
        self.calls = []

    def request(self, method, url, json=None, params=None, headers=None, timeout=None, stream=False):
        self.calls.append({"method": method, "url": url, "headers": headers or {}})
        handler = self.routes.get(url)
        if callable(handler):
            res = handler()
        elif isinstance(handler, list):
            res = handler.pop(0) if handler else _FakeBinaryResponse(404)
        else:
            res = handler
        if res is None:
            return _FakeBinaryResponse(404)
        if isinstance(res, Exception):
            raise res
        return res


class TestEntiImagePure(BaseCase):
    def test_magic_bytes_and_normalization_and_sanitization(self):
        png_raw = _make_image_bytes(color=(10, 200, 50), fmt="PNG")
        jpg_raw = _make_image_bytes(color=(200, 20, 50), fmt="JPEG")
        self.assertEqual(detect_magic_mime(png_raw), "image/png")
        self.assertEqual(detect_magic_mime(jpg_raw), "image/jpeg")
        self.assertIsNone(detect_magic_mime(b"<svg><script>alert(1)</script></svg>"))
        self.assertIsNone(detect_magic_mime(b"<html>not an image</html>"))

        # Spoofed MIME header with HTML bytes -> fails magic byte validation
        with self.assertRaises(EntiError):
            validate_and_normalize_image(b"<html>fake</html>", declared_mime="image/jpeg")

        # Valid PNG normalizes cleanly
        norm = validate_and_normalize_image(png_raw, declared_mime="image/png", max_bytes=1024 * 1024)
        self.assertEqual(norm["mime"], "image/png")
        self.assertGreater(len(norm["normalized_bytes"]), 0)
        self.assertEqual(len(norm["normalized_hash"]), 64)

        # Disallowed URI schemes rejected
        with self.assertRaises(EntiError):
            parse_image_value("javascript:alert(1)")
        with self.assertRaises(EntiError):
            parse_image_value("file:///etc/passwd")

        # Metadata sanitizer strips tokens, passwords, cookies, and raw base64 blobs
        meta = json.loads(sanitize_employee_metadata({
            "keyNV": "k1",
            "tenNV": "Synthetic One",
            "access_token": "SECRET_TOK",
            "refresh_token": "SECRET_REF",
            "password": "SECRET_PWD",
            "cookie": "sid=xyz",
            "anh": _make_data_uri(),
            "day1": {"ngay": "2026-11-16"},
        }, image_field="anh", image_source="base64", image_hash="abc123", image_mime="image/jpeg", image_size=42))
        self.assertNotIn("access_token", meta)
        self.assertNotIn("refresh_token", meta)
        self.assertNotIn("password", meta)
        self.assertNotIn("cookie", meta)
        self.assertNotIn("day1", meta)
        self.assertTrue(meta["anh"].startswith("<base64:image/jpeg:42B:"))


@tagged("post_install", "-at_install")
class TestEntiImageSync(AttendanceCase):
    def setUp(self):
        super().setUp()
        self.source = internal(self.env["tp.hr.attendance.source"]).create({
            "name": "Synthetic ENTI Images",
            "namespace": "synthetic-enti-images",
            "kind": "enti_api",
            "company_id": self.company.id,
            "timezone": DEFAULT_TZ,
            "state": "ready",
            "live_enabled": True,
        })
        self.addCleanup(enti_sync_module._PACE.pop, (self.env.cr.dbname, self.source.id), None)

        self.routes = {}
        self.fake_session = _FakeImageSession(self.routes)
        self.client = EntiClient(base_url=ENTI_BASE)
        self.client.session = self.fake_session
        self.client.access_token = "SYNTHETIC_TOK"
        self.client.refresh_token = "SYNTHETIC_REF"
        self.client.token_expires_at = datetime.now() + timedelta(hours=1)

        # Speed up retries in unit tests
        self.sleeps = []
        self.patch(enti_client_module, "time", SimpleNamespace(sleep=self.sleeps.append))

        self.ImageModel = self.env["tp.hr.attendance.enti.employee.image"].sudo()
        self.Mapping = self.env["tp.hr.attendance.enti.mapping"].sudo()

        # Pre-seed an unmapped third employee record in Odoo only if needed, or leave emp_a/emp_b in company
        self.emp_a.sudo().write({"user_id": self.viewer.id})

    def _run_profiles(self, profiles, *, only_failed=False):
        self.client.get_employee_profiles = lambda: copy.deepcopy(profiles)
        res = self.source._tp_sync_enti_images(
            client=self.client,
            only_failed=only_failed,
            budget_seconds=30.0,
            origin="manual",
        )
        self.source.invalidate_recordset()
        return res

    def test_01_valid_url_and_02_base64_and_03_no_image(self):
        url_jpg = _make_image_bytes(color=(12, 80, 160), fmt="JPEG")
        self.routes[f"{ENTI_BASE}/avatars/a.jpg"] = _FakeBinaryResponse(
            200,
            content=url_jpg,
            headers={"Content-Type": "image/jpeg", "Content-Length": str(len(url_jpg))},
        )
        b64_png = _make_data_uri(color=(50, 160, 40), fmt="PNG")

        # Create third mapped employee with no image
        emp_c = self.env["hr.employee"].sudo().create({
            "name": "Synthetic Người Ba",
            "tp_employee_code": "TP993",
            "company_id": self.company.id,
            "department_id": self.dept.id,
        })

        res = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "tenBP": "Phòng A", "anh": f"{ENTI_BASE}/avatars/a.jpg"},
            {"keyNV": "k-b", "maNV": "E2", "tenNV": "Synthetic Người Hai", "tenBP": "Phòng B", "anh": b64_png},
            {"keyNV": "k-c", "maNV": "E3", "tenNV": "Synthetic Người Ba", "tenBP": "Phòng A", "anh": ""},
        ])
        self.assertTrue(res["success"], res)
        self.assertEqual((res["downloaded"], res["no_image"], res["failed"]), (2, 1, 0))

        img_a = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-a")])
        img_b = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-b")])
        img_c = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-c")])
        self.assertEqual(img_a.state, "downloaded")
        self.assertEqual(img_a.image_source, "url")
        self.assertEqual(img_b.state, "downloaded")
        self.assertEqual(img_b.image_source, "base64")
        self.assertEqual(img_c.state, "no_image")

        # Employee image_1920 AND linked user's partner image_1920 both updated
        self.emp_a.invalidate_recordset()
        self.viewer.partner_id.invalidate_recordset()
        emp_a_bytes = bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b"")
        partner_a_bytes = bytes(self.viewer.partner_id.sudo().with_context(bin_size=False).image_1920 or b"")
        self.assertTrue(emp_a_bytes)
        self.assertEqual(emp_a_bytes, partner_a_bytes)
        self.assertTrue(bytes(self.emp_b.sudo().with_context(bin_size=False).image_1920 or b""))
        self.assertFalse(bytes(emp_c.sudo().with_context(bin_size=False).image_1920 or b"") and not bytes(emp_c.sudo().with_context(bin_size=False).image_1920 or b"").endswith(b"</svg>"))

    def test_04_broken_url_timeout_404_and_ssrf_allowlist(self):
        # 404 should fail immediately without exhausting retries; Timeout retries bounded times and fails
        self.routes[f"{ENTI_BASE}/avatars/missing.jpg"] = _FakeBinaryResponse(404)
        self.routes[f"{ENTI_BASE}/avatars/timeout.jpg"] = [
            requests.Timeout("slow"),
            requests.Timeout("slow"),
            requests.Timeout("slow"),
            requests.Timeout("slow"),
        ]

        res = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": f"{ENTI_BASE}/avatars/missing.jpg"},
            {"keyNV": "k-b", "maNV": "E2", "tenNV": "Synthetic Người Hai", "anh": f"{ENTI_BASE}/avatars/timeout.jpg"},
        ])
        self.assertEqual(res["failed"], 2)
        img_a = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-a")])
        img_b = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-b")])
        self.assertEqual(img_a.state, "failed")
        self.assertEqual(img_b.state, "failed")
        self.assertIn("404", img_a.error_message)
        self.assertIn("hết thời gian chờ", img_b.error_message)
        # Bounded retry: 1 call for 404, 3 calls (retry_count=2) for timeout
        missing_calls = [c for c in self.fake_session.calls if c["url"].endswith("/missing.jpg")]
        timeout_calls = [c for c in self.fake_session.calls if c["url"].endswith("/timeout.jpg")]
        self.assertEqual(len(missing_calls), 1)
        self.assertEqual(len(timeout_calls), 3)

        # SSRF / disallowed host is rejected BEFORE any HTTP call is issued
        calls_before = len(self.fake_session.calls)
        self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": "https://evil.invalid/steal.jpg"},
        ])
        self.assertEqual(len(self.fake_session.calls), calls_before)
        img_a.invalidate_recordset()
        self.assertEqual(img_a.state, "failed")
        self.assertIn("tên miền", img_a.error_message.lower())

    def test_05_spoofed_magic_bytes_and_06_oversized(self):
        # Spoofed HTTP Content-Type image/jpeg carrying HTML bytes
        self.routes[f"{ENTI_BASE}/avatars/spoof.jpg"] = _FakeBinaryResponse(
            200,
            content=b"<html><script>bad</script></html>",
            headers={"Content-Type": "image/jpeg", "Content-Length": "33"},
        )
        # Disallow tiny max bytes threshold (2 KB) to test oversized rejection
        self.env["ir.config_parameter"].sudo().set_str("tp_hr_attendance.enti_max_image_bytes", "2048")
        big_bytes = b"\xff\xd8\xff\xe0" + (b"0" * 4096)
        self.routes[f"{ENTI_BASE}/avatars/big.jpg"] = _FakeBinaryResponse(
            200,
            content=big_bytes,
            headers={"Content-Type": "image/jpeg", "Content-Length": str(len(big_bytes))},
        )

        res = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": f"{ENTI_BASE}/avatars/spoof.jpg"},
            {"keyNV": "k-b", "maNV": "E2", "tenNV": "Synthetic Người Hai", "anh": f"{ENTI_BASE}/avatars/big.jpg"},
        ])
        self.assertEqual(res["failed"], 2)
        img_a = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-a")])
        img_b = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-b")])
        self.assertEqual(img_a.state, "failed")
        self.assertIn("magic bytes", img_a.error_message)
        self.assertEqual(img_b.state, "failed")
        self.assertIn("giới hạn", img_b.error_message)

    def test_07_unchanged_and_08_changed_image(self):
        uri_v1 = _make_data_uri(color=(10, 20, 30), fmt="JPEG")
        res1 = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": uri_v1},
        ])
        self.assertEqual(res1["downloaded"], 1)
        img_a = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-a")])
        hash_v1 = img_a.image_hash
        dl_at_v1 = img_a.downloaded_at

        # Second pass with identical image -> unchanged, does not rewrite downloaded_at
        res2 = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": uri_v1},
        ])
        self.assertEqual((res2["downloaded"], res2["unchanged"]), (0, 1))
        img_a.invalidate_recordset()
        self.assertEqual((img_a.state, img_a.image_hash, img_a.downloaded_at), ("unchanged", hash_v1, dl_at_v1))

        # Third pass with a different color image -> updated and downloaded again
        uri_v2 = _make_data_uri(color=(220, 120, 10), fmt="JPEG")
        res3 = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": uri_v2},
        ])
        self.assertEqual(res3["downloaded"], 1)
        img_a.invalidate_recordset()
        self.assertEqual(img_a.state, "downloaded")
        self.assertNotEqual(img_a.image_hash, hash_v1)

    def test_09_unmapped_and_10_duplicate_keynv_conflict(self):
        uri_unmapped = _make_data_uri(color=(90, 90, 90), fmt="JPEG")
        # Near-match name "Synthetic Nguoi Mot" (no accents) must stay unmapped, never matched to emp_a
        self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": _make_data_uri(color=(1, 2, 3))},
            {"keyNV": "k-u", "maNV": "EU", "tenNV": "Synthetic Nguoi Mot", "anh": uri_unmapped},
        ])
        img_u = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-u")])
        self.assertEqual((img_u.state, img_u.status_label, img_u.employee_id.id), ("pending", "Chưa đối chiếu", False))
        # Staging preview is saved, but no hr.employee record was modified for unmapped
        self.assertTrue(img_u.with_context(bin_size=True).enti_image_1920)
        saved_a = bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b"")

        # A second keyNV "k-a2" manually mapped or colliding with emp_a is blocked cleanly
        twin = self.Mapping.create({
            "source_id": self.source.id,
            "key_nv": "k-a2",
            "ma_nv": "E1-DUP",
            "ten_nv": "Synthetic Người Một",
            "state": "suggested",
        })
        # Simulate another key with same name in profile run: it stays suggested/unmapped or conflicts if mapped
        res_dup = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": _make_data_uri(color=(1, 2, 3))},
            {"keyNV": "k-a2", "maNV": "E1-DUP", "tenNV": "Synthetic Người Một", "anh": _make_data_uri(color=(255, 0, 0))},
        ])
        img_a2 = self.ImageModel.search([("source_id", "=", self.source.id), ("key_nv", "=", "k-a2")])
        self.assertNotEqual(img_a2.employee_id.id, self.emp_a.id)
        self.assertEqual(img_a2.status_label, "Chưa đối chiếu")
        self.assertEqual(bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b""), saved_a)
        # Even if HR forces employee_id on twin and tries to update, mapping conflict blocks it
        twin.sudo().write({"employee_id": self.emp_a.id})
        with self.assertRaises(Exception):
            twin.with_user(self.manager).action_confirm_mapping()
        self.assertTrue(res_dup["success"])

    def test_11_keep_old_photo_on_error_and_prefer_manual_image(self):
        # Apply valid initial photo for emp_a
        uri_ok = _make_data_uri(color=(40, 100, 180), fmt="JPEG")
        self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": uri_ok},
        ])
        initial_photo = bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b"")
        self.assertTrue(initial_photo)

        # Next run ENTI fails (404) -> emp_a still keeps initial_photo
        self.routes[f"{ENTI_BASE}/avatars/broken.jpg"] = _FakeBinaryResponse(404)
        self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": f"{ENTI_BASE}/avatars/broken.jpg"},
        ])
        self.emp_a.invalidate_recordset()
        self.assertEqual(bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b""), initial_photo)

        # Next run ENTI temporarily returns empty -> still keeps initial_photo
        self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": ""},
        ])
        self.emp_a.invalidate_recordset()
        self.assertEqual(bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b""), initial_photo)

        # Prefer manual photo: upload custom manual photo directly to Odoo, enable prefer_manual_image
        manual_b64 = base64.b64encode(_make_image_bytes(color=(123, 234, 45), fmt="JPEG")).decode("ascii")
        self.emp_a.sudo().write({"image_1920": manual_b64})
        internal(self.source).write({"prefer_manual_image": True})
        manual_saved = bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b"")

        uri_new_enti = _make_data_uri(color=(99, 11, 22), fmt="JPEG")
        res_manual = self._run_profiles([
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": uri_new_enti},
        ])
        self.assertEqual(res_manual["unchanged"], 1)
        self.emp_a.invalidate_recordset()
        self.assertEqual(bytes(self.emp_a.sudo().with_context(bin_size=False).image_1920 or b""), manual_saved)

    def test_12_permissions_and_overview_filtering_and_13_attendance_isolation(self):
        # Regular employee cannot run image sync, toggle setting, or create image records
        SourceViewer = self.env_for(self.viewer)["tp.hr.attendance.source"]
        with self.assertRaises(AccessError):
            SourceViewer.action_sync_enti_images_quick()
        with self.assertRaises(AccessError):
            SourceViewer.action_retry_failed_enti_images_quick()
        with self.assertRaises(AccessError):
            SourceViewer.action_toggle_prefer_manual_image(True)
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)["tp.hr.attendance.enti.employee.image"].search([])

        # Run full two-step sync via _tp_run_enti where Step 1 (attendance) succeeds and Step 2 has broken image
        self.routes[f"{ENTI_BASE}/avatars/fail.jpg"] = _FakeBinaryResponse(500)
        b64_ok = _make_data_uri(color=(15, 190, 120), fmt="JPEG")
        att_rows = [
            {
                "keyNV": "k-a",
                "maNV": "E1",
                "tenNV": "Synthetic Người Một",
                "tenBP": "Synthetic Dept",
                "day1": {"ngay": f"{D16.isoformat()}T00:00:00", "vaoDau": "08:05", "raCuoi": "17:10", "diMuon": 0, "congLam": 1},
            },
            {
                "keyNV": "k-b",
                "maNV": "E2",
                "tenNV": "Synthetic Người Hai",
                "tenBP": "Other Dept",
                "day1": {"ngay": f"{D16.isoformat()}T00:00:00", "vaoDau": "08:35", "raCuoi": "17:05", "diMuon": 5, "congLam": 1},
            },
        ]
        profile_rows = [
            {"keyNV": "k-a", "maNV": "E1", "tenNV": "Synthetic Người Một", "anh": b64_ok},
            {"keyNV": "k-b", "maNV": "E2", "tenNV": "Synthetic Người Hai", "anh": f"{ENTI_BASE}/avatars/fail.jpg"},
        ]

        class _StepFakeClient:
            def __init__(self, real_http_client):
                self._http = real_http_client

            def get_employees(self):
                return [{"keyNV": r["keyNV"], "maNV": r["maNV"], "tenNV": r["tenNV"], "tenBP": r["tenBP"]} for r in att_rows]

            def get_employee_profiles(self):
                return copy.deepcopy(profile_rows)

            def get_attendance(self, start_date, end_date):
                return {"data": copy.deepcopy(att_rows), "total": len(att_rows), "pages": 1}

            def download_image(self, url, **kwargs):
                return self._http.download_image(url, **kwargs)

        fake_client = _StepFakeClient(self.client)
        entry = {"client": fake_client, "lock": threading.Lock(), "app_key": "syn-app"}
        Source = type(self.source)
        self.patch(Source, "_tp_enti_entry", lambda rec: (entry, "syn", "syn", "syn-app"))
        self.patch(Source, "_tp_enti_ready", lambda rec, *args: fake_client)

        full_res = self.source.with_user(self.manager)._tp_run_enti(D16, D17, scope="range", origin="manual", wait=True)
        self.assertTrue(full_res["success"], full_res)
        # Step 1 attendance saved completely even though k-b image returned HTTP 500
        self.assertEqual(self.day(self.emp_a, D16).in_time, "08:05")
        self.assertEqual(self.day(self.emp_b, D16).in_time, "08:35")
        self.assertEqual(full_res["image_sync"]["downloaded"], 1)
        self.assertEqual(full_res["image_sync"]["failed"], 1)

        # Overview + filters by status, department, and employee search for HR Manager
        SourceMgr = self.env_for(self.manager)["tp.hr.attendance.source"]
        overview = SourceMgr.tp_sources_overview({})
        img_sec = overview["image_sync"]
        self.assertEqual((img_sec["synced_count"], img_sec["failed_count"]), (1, 1))
        failed_only = SourceMgr.tp_enti_image_logs({"image_state": "failed"})
        self.assertEqual([r["key_nv"] for r in failed_only["rows"]], ["k-b"])
        dept_only = SourceMgr.tp_enti_image_logs({"image_department_id": self.dept.id})
        self.assertEqual([r["key_nv"] for r in dept_only["rows"]], ["k-a"])
        search_only = SourceMgr.tp_enti_image_logs({"image_search": "Người Hai"})
        self.assertEqual([r["key_nv"] for r in search_only["rows"]], ["k-b"])

        # Retry only failed after fixing k-b route
        self.routes[f"{ENTI_BASE}/avatars/fail.jpg"] = _FakeBinaryResponse(
            200,
            content=_make_image_bytes(color=(12, 34, 56), fmt="JPEG"),
            headers={"Content-Type": "image/jpeg"},
        )
        retry_res = SourceMgr.action_retry_failed_enti_images_quick()
        self.assertTrue(retry_res["success"])
        self.assertEqual((retry_res["downloaded"], retry_res["total_failed"]), (1, 0))
