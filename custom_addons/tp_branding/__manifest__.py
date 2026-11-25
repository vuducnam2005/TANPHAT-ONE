# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
{
    'name': 'TANPHAT ONE Branding',
    'summary': 'TANPHAT ONE identity, tab titles, branded /app URLs and business routes',
    'description': """
BRAND-WHITELABEL-002, SYSTEM-URL-001:

* Webclient served under /app with business routes:
  /app/trang-chu
  /app/nhan-su/...
  /app/cham-cong/...
  /app/khkd/...
  /app/thiet-bi/...
  /app/bao-cao/...
  /app/de-nghi/...
  /app/ca-nhan/...
  /app/quan-tri/...
* Two-way route adapter with action stack, detail records (/id), creation (/tao-moi),
  and full backward compatibility for legacy action-ID and slug URLs.
* Dynamic XML ID <-> Action ID resolution via session_info (no hardcoded numeric IDs).
* Branded auth URLs: /dang-nhap, /dang-nhap/xac-thuc, /quen-mat-khau, /tao-tai-khoan.
* Tab titles "<page> | TANPHAT ONE", SSR titles, dialogs, offline page,
  PWA manifest/service worker on /app, credit "Phát triển bởi TADIC".

Platform licence/copyright notices and technical identifiers are kept.
""",
    'version': '20.0.2.5.0',
    'category': 'Hidden',
    'author': 'Tan Phat JSC',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'http_routing',
        'portal',
        'mail',
        'auth_signup',
        'auth_totp',
        'tp_web_login',
        'tp_web_home',
    ],
    'data': [
        'views/branding_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tp_branding/static/src/brand_routes.js',
            'tp_branding/static/src/brand_urls.js',
            'tp_branding/static/src/router_patch.js',
            'tp_branding/static/src/title_patch.js',
            'tp_branding/static/src/webclient_patch.js',
            'tp_branding/static/src/dialog_patch.js',
            'tp_branding/static/src/links_patch.js',
            'tp_branding/static/src/webview_error_guard.js',
            'tp_branding/static/src/branding.xml',
        ],
        'web.assets_frontend': [
            'tp_branding/static/src/webview_error_guard.js',
        ],
        'web.assets_unit_tests': [
            'tp_branding/static/tests/**/*.test.js',
        ],
    },
    'installable': True,
    'application': False,
}
