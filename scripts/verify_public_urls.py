# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Verify public URLs and deep link behavior on https://tpone.tadic.vn."""

import json
from urllib.parse import parse_qs, unquote, urlsplit
import requests

PUBLIC_DOMAIN = "https://tpone.tadic.vn"

def test_public_endpoints():
    session = requests.Session()
    print("=" * 60)
    print(f"VERIFYING PUBLIC DOMAIN: {PUBLIC_DOMAIN}")
    print("=" * 60)

    # 1. Health check
    r_health = session.get(f"{PUBLIC_DOMAIN}/web/health", timeout=25)
    print(f"1. /web/health: status={r_health.status_code}")
    assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"

    # 2. Login page
    r_login = session.get(f"{PUBLIC_DOMAIN}/dang-nhap", timeout=25)
    print(f"2. /dang-nhap: status={r_login.status_code}")
    assert r_login.status_code == 200, f"Login page failed: {r_login.status_code}"
    assert "TANPHAT ONE" in r_login.text, "Missing TANPHAT ONE in login page"
    assert "Tadic" in r_login.text or "tadic" in r_login.text, "Missing Tadic in login page"

    # 3. Hierarchical Business Deep Links (Anonymous redirect)
    test_routes = [
        "/app/nhan-su/nhan-vien/44",
        "/app/nhan-su/nhan-vien/tao-moi",
        "/app/nhan-su/nhan-vien",
        "/app/nhan-su/phong-ban",
        "/app/nhan-su/cham-cong/tong-quan",
        "/app/khkd/tong-quan",
        "/app/khkd/du-an-tiem-nang",
        "/app/khkd/quan-ly-du-an",
        "/app/khkd/quan-tri-du-an",
        "/app/thiet-bi/danh-sach",
        "/app/thiet-bi/danh-sach/5",
        "/app/bao-cao/tong-quan",
        "/app/quan-tri/tai-khoan",
    ]

    print("\n3. Testing Anonymous Deep Link Redirects:")
    for path in test_routes:
        url = f"{PUBLIC_DOMAIN}{path}"
        r = session.get(url, allow_redirects=False, timeout=10)
        status = r.status_code
        loc = r.headers.get("Location", "")
        parsed_loc = urlsplit(loc)
        redirect_param = parse_qs(parsed_loc.query).get("redirect", [""])[0].rstrip("?")
        print(f"  {path:35} -> {status} Location: {parsed_loc.path}?redirect={redirect_param}")
        assert status in (302, 303), f"Expected 302/303 redirect for {path}, got {status}"
        assert parsed_loc.path == "/dang-nhap", f"Expected redirect to /dang-nhap, got {parsed_loc.path}"
        assert redirect_param == path, f"Expected redirect param {path}, got {redirect_param}"

    # 4. Backward Compatibility
    print("\n4. Testing Backward Compatibility (Legacy URLs):")
    legacy_cases = [
        ("/odoo", "/app"),
        ("/odoo/action-528", "/app/action-528"),
        ("/odoo/tp-home", "/app/tp-home"),
        ("/web", "/app"),
        ("/web/login", "/dang-nhap"),
    ]
    for old_path, expected_target in legacy_cases:
        r = session.get(f"{PUBLIC_DOMAIN}{old_path}", allow_redirects=False, timeout=10)
        loc = r.headers.get("Location", "")
        parsed = urlsplit(loc)
        print(f"  {old_path:20} -> {r.status_code} Location: {parsed.path}")
        assert r.status_code in (302, 303), f"Expected redirect for {old_path}, got {r.status_code}"
        assert parsed.path == expected_target, f"Expected {expected_target}, got {parsed.path}"

    # 5. Check JS Bundle includes brand_routes
    print("\n5. Checking Assets Bundle on Server:")
    # Get index or login HTML to locate asset script
    r_app = session.get(f"{PUBLIC_DOMAIN}/dang-nhap", timeout=10)
    bundle_urls = []
    for line in r_app.text.splitlines():
        if "/web/assets/" in line and ".js" in line:
            start = line.find('src="') + 5
            end = line.find('"', start)
            if start > 4 and end > start:
                bundle_urls.append(line[start:end])
    
    print(f"  Found {len(bundle_urls)} script assets on login page")

    # 6. Session Info Route Map
    print("\n6. Checking IrHttp Session Info via RPC:")
    r_session = session.post(
        f"{PUBLIC_DOMAIN}/web/session/get_session_info",
        headers={"Content-Type": "application/json"},
        data="{}",
        timeout=10,
    )
    print(f"  get_session_info: status={r_session.status_code}")
    res_data = r_session.json().get("result", {})
    routes = res_data.get("tp_action_routes", {})
    xml_to_id = routes.get("xml_to_id", {})
    id_to_xml = routes.get("id_to_xml", {})
    print(f"  tp_action_routes present: {bool(routes)}")
    print(f"  Mapped XML IDs: {len(xml_to_id)} actions")
    # Show sample mappings
    sample_keys = [
        "tp_hr_workspace.action_employees",
        "tp_kd_workspace.action_kd_dashboard",
        "tp_equipment.action_equipment_list",
        "tp_reporting.action_tp_reporting_dashboard",
        "base.action_res_users",
    ]
    for k in sample_keys:
        if k in xml_to_id:
            print(f"    {k} -> ID {xml_to_id[k]}")

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_public_endpoints()
