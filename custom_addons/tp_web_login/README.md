# TANPHAT ONE Login

Native authentication UI for `/web/login`, `/web/login/totp`, `/web/signup` and
`/web/reset_password` (UI-SHELL-AUTH-001). It keeps Odoo authentication, fields, CSRF, captcha, cooldown, passkey and
trusted-device behavior. The HR lock model extends native active users and session-token revision; no authentication controller or new route is defined.

The centered two-region panel layout (`UI-LOGIN-002`, `20.0.1.6.2`) shows a compact 40/60 navy-and-white frame on a light `#F3F7FC` canvas: company mark on a white tile beside `TANPHAT ONE` and **“Vững Vàng Hội Nhập”** directly below, `Hệ thống quản trị điều hành`, a lightweight non-interactive three-step workflow decorative indicator (`Kế hoạch – Công việc – Báo cáo`) placed directly under the heading, `copyright @by Tadic` (`by Tadic` underlined link to `https://tanphatjsc.com/` in a new tab) left-aligned at the bottom, and a clean form panel (`#0073AD` primary action, integrated input styling, Vietnamese Passkey label `Đăng nhập bằng khóa truy cập` / `Hoặc`, and no duplicate product footer or large square logo card). Images are served from `/tp_web_home/static/img/brand/` with Segoe UI/system fonts. Mobile prioritizes the single-column layout while preserving the logo, `TANPHAT ONE`, `Vững Vàng Hội Nhập`, and `copyright @by Tadic`. Remembered users use the native public OWL component and storage, with separate accessible remove controls.
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

BRAND-WHITELABEL-002: `tp_branding` adds branded aliases on top of this layout:
`/dang-nhap` (login), `/dang-nhap/xac-thuc` (TOTP), `/quen-mat-khau` (reset)
and `/tao-tai-khoan` (signup). The signup/reset policy is unchanged. The form posts
to `/dang-nhap` and gets the same native CSRF, cooldown, passkey and TOTP checks.
GET/HEAD on `/web/login…` gets a 302 to the alias; POST is never redirected.
The UI-LOGIN-002 layout and left-panel copy stay as configured. The page title
is "Đăng nhập | TANPHAT ONE". This addon does not depend on `tp_branding`.

AUTH-SESSION-001 (`20.0.2.0.1`, DEC-057) enforces one active browser/PWA session per
account per database via `res.users._after_session_login()`, the internal PostgreSQL
table `tp_user_active_session`, and transactional advisory locks (`761157`). Multiple
tabs sharing the same browser cookie stay active together; a new completed login
(including MFA completion) replaces the previous session, pushes a generation-scoped
`tp.auth/session_replaced` bus event (with visible-tab poll/focus/online/bfcache
fallback), blocks old cookies across RPC/HTTP/files/API, and shows the light
session-ended screen with a single **Đăng nhập lại** button that lands on Trang chủ.

Winner checks use a fresh primary cursor after the request's shared transaction
lock, avoiding stale Odoo REPEATABLE READ snapshots. The lock lasts through the
business commit. Termination hides the document and navigates to the standalone,
server-validated `/tp/session-ended` page, disposing the old webclient and its
pending callbacks. Cached history documents remain hidden until authenticated reload.

PASSKEY-001 (`20.0.2.3.0`) keeps native `auth_passkey`/WebAuthn and its origin,
RP ID, challenge, signature, counter and user-verification checks. The login
button shows a busy state, sends one `start-auth`, and explains browser errors in
Vietnamese below it (cancel/timeout/no key share one message because
`NotAllowedError` cannot tell them apart). Backend rejections map to cause-specific
Vietnamese messages; a lock is reported only after a valid assertion. The
identity check runs the native passkey branch, and the account page renames and
revokes only the session user's own keys. `/tp_web_login/passkey/client-event`
accepts whitelisted enum codes only (no challenge, credential or cookie).
