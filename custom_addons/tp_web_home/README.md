# tp_web_home — TANPHAT ONE Trang chủ (UI-HOME-001)

Native Odoo Community home page: a grid of the apps the signed-in user can open.

## What it adds

| Record | XML ID | Notes |
| --- | --- | --- |
| Client action | `tp_web_home.action_home` | tag `tp_web_home.home`, path `tp-home` → `/odoo/tp-home` |
| Root menu | `tp_web_home.menu_home` | "Trang chủ", `base.group_user`, sequence 1 |
| Systray item | `tp_web_home.home_button` | home icon in the navbar, label "Trang chủ" |

Nothing else: no model, no ACL, no controller, no override of another module's record.
Depends only on `web`.

## How it works

- Tiles come from the native menu service (`/web/webclient/load_menus`), which Odoo already
  filters by the user's groups. The page never reads `ir.ui.menu` itself and keeps no menu
  copy of its own; it waits for the fresh `load_menus` response before the first render, so
  a menu tree cached in IndexedDB by a previous user of the browser is never shown.
- `static/src/home/home_catalog.js` maps known XML IDs to Vietnamese labels, hints, search
  aliases and the two groups. A mapping applies only when that XML ID is in the user's tree;
  unknown apps keep their native name and icon (or a monogram). Home itself is excluded.
  `tp_core.menu_platform` is replaced by its action leaves (TP Projects, Danh mục công việc).
- A tile is an `<a href="/odoo/…">`. A plain click calls `menu.selectMenu(menu)`, exactly like
  the native apps menu; Ctrl/Cmd/Shift/middle click is left to the browser.
- `/odoo` without an action opens the first root menu (native `WebClient._loadDefaultApp`),
  which is Home because of its sequence. A user's own Home Action (`res.users.action_id`)
  still wins; the module never writes that field.

## Install / upgrade / uninstall

```powershell
.\.venv\Scripts\python.exe odoo-bin -c <config> -d <db> -i tp_web_home --stop-after-init --no-http
.\.venv\Scripts\python.exe odoo-bin -c <config> -d <db> -u tp_web_home --stop-after-init --no-http
```

Uninstall from Apps (or `button_immediate_uninstall`); the action, menu and systray item
disappear and the previous first root menu becomes the default app again.

## Tests

- Server: `odoo-bin … --test-enable --test-tags /tp_web_home`
- HOOT: `/web/tests?filter=tp_web_home` (bundle `web.assets_unit_tests`)

See `docs/demo/UI_HOME_001_RUNBOOK.md` for the runbook and verification record.
