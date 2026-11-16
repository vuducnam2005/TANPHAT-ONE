# TANPHAT ONE Login

Native authentication UI for `/web/login`, `/web/login/totp`, `/web/signup` and
`/web/reset_password` (UI-SHELL-AUTH-001). It keeps Odoo authentication, fields, CSRF, captcha, cooldown, passkey and
trusted-device behavior. The HR lock model extends native active users and session-token revision; no authentication controller or new route is defined.

The two-region desktop layout shows the company logo (BRAND-LOGO-001,
CHG-20261116-009: mark on a white tile beside `TANPHAT ONE`, full logo card in
place of the former bridge drawing; images served from
`/tp_web_home/static/img/brand/`) and Segoe UI/system
fonts. Mobile prioritizes the single-column form. Remembered users use the
native public OWL component and storage, with separate accessible remove controls.
The dedicated `tp_web_login.assets_login` bundle loads only on the four auth
routes. Public JS preserves native show-password, adds ARIA state and a retry
timeout for stalled submits. Reduced motion and keyboard focus are supported.

Installation and upgrade do not set auth policy parameters, including absent
keys. The old `data/ir_config_parameter_data.xml` is retained as AUTH-002 history
and deliberately not loaded. Enabled signup/reset links retain native handlers.
The database manager link stays controlled by Odoo `list_db`. TOTP cancel uses
POST logout + CSRF and returns to `/web/login`; full logout retains Odoo's
service-worker/PWA callback. No new auth endpoint or credential storage.

AUTH-002's earlier test-only acceptance remains historical. UI-SHELL-AUTH-001
separately authorizes clone verification, fresh verified backup and dev installation.
It is not added to default setup modules. See docs/demo/UI_SHELL_AUTH_001_ACCEPTANCE.md.

HR-ACCOUNT-ROLE-001 keeps the explicit locked-account message “Tài khoản đã bị khóa. Vui lòng gửi phản hồi.” after valid credentials. Wrong passwords stay generic. Feedback remains an informational placeholder without outgoing requests. Role changes also increment the existing lock revision to invalidate prior sessions; native password/TOTP/CSRF behavior remains in place.

HR-AUTH-FOCUS-009 (20.0.1.4.1) adds a native identity form controller: submit
focuses the enabled password input before RPC so closing a native error restores
that input. The shared opener hook listens to native UI ownership events.
Native check_identity, current-password, expiry, server checks and MFA are unchanged.
