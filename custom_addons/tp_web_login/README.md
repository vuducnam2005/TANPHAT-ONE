# TANPHAT ONE Login

Template/configuration addon for the native `/web/login` and `/web/login/totp`
pages. It keeps Odoo authentication, fields, CSRF, captcha, cooldown, passkey and
trusted-device behavior. No model, controller, or route is defined.

The monogram matches React. Native pages use the local system font stack
(`system-ui`, Segoe UI, sans-serif), which supports Vietnamese and requires no
CDN or duplicate font files. CSS is served through the dedicated
`tp_web_login.assets_login` Odoo bundle and loaded only by the two native login
routes; portal/backend pages retain their layout.

On initial installation, `noupdate` data sets the D6-a policy: invitation scope
`b2b` and password reset disabled. Subsequent upgrades preserve administrator
changes. The database manager link is controlled by Odoo `list_db`, not removed
by this addon.

AUTH-002 installs this addon only on the owned isolated test database. It is not
included in the development module list.
