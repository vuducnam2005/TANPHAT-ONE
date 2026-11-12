# tp_web_home — TANPHAT ONE Trang chủ (UI-HOME-003)

Native Odoo Community home page. Since UI-HOME-003 (DEC-031, KH-KD first) Home is a short
entry page, not a launcher for every app: one workspace (Kế hoạch Kinh doanh), three personal
tools and, for system administrators only, an administration area. Every other app the user
is granted stays in the native app switcher. Version 20.0.1.4.0.

UI-SHELL-AUTH-001 extends the native navbar with a local bridge wordmark, current
application context, 56px navy styling and an account heading/name. Section
measurement/More, company switcher, systray, HomeButton, native logout and the
KH-KD body grid are retained. Mobile keeps app and account drawers; scoped
hover/focus styles respect reduced motion. See docs/demo/UI_SHELL_AUTH_001_ACCEPTANCE.md.

## What it adds

| Record | XML ID | Notes |
| --- | --- | --- |
| Client action | `tp_web_home.action_home` | tag `tp_web_home.home`, path `tp-home` → `/odoo/tp-home` |
| Root menu | `tp_web_home.menu_home` | "Trang chủ", `base.group_user`, sequence 1 |
| Systray item | `tp_web_home.home_button` | home icon in the navbar, label "Trang chủ" |

Nothing else: no model, no ACL, no controller, no override of another module's record.
Depends only on `web`. Static files: launcher JS/XML/SCSS, local SVG icons (incl. `apps.svg`).

## Layout (UI-HOME-003)

| Section | Entries | Shown when |
| --- | --- | --- |
| Không gian làm việc | Kế hoạch Kinh doanh (`tp_kd_workspace.menu_kd`) | the menu is in the user's tree |
| Công cụ cá nhân | Việc cá nhân (`project_todo.menu_todo_todos`), Lịch làm việc (`calendar.mail_menu_calendar`), Trao đổi (`mail.menu_root_discuss`) | each menu is in the user's tree |
| Quản trị hệ thống | Tất cả ứng dụng (in-page panel), Cài đặt (`base.menu_administration`), Quản lý ứng dụng (`base.menu_management`) | session `is_system` (`base.group_system`) and, for the two links, the menu is in the tree |

- There is no "Ứng dụng nghiệp vụ" grid any more. CRM, Project, TP Projects, TP Contracts,
  HR, Invoicing, dashboards and unknown apps open from the native switcher (desktop: apps
  button at the left of the navbar; phone: ☰ → All Apps). A note under Home says so whenever
  the user has such apps.
- "Tất cả ứng dụng" opens a panel inside Home listing only the user's own menus, with its own
  search. Escape clears its search, then closes it and returns focus to the toggle; it never
  propagates further. A menu reload closes it.
- The admin gate is `user.isSystem` from `@web/core/user`, not `isAdmin`
  (`base.group_erp_manager`), not a login, user ID or TP group. For other users the
  administration entries and the panel list are never built, so neither the DOM nor the main
  search can reach them. This is presentation only: the server still filters every menu and
  record, and `base.menu_management`/Settings stay in the switcher for whoever the server
  grants them to.

## How it works

- Entries come from the native menu service (`/web/webclient/load_menus`), which Odoo already
  filters by the user's groups. The page never reads `ir.ui.menu` itself and keeps no menu
  copy. Each Home mount calls `menu.reload()` and hides entries until that fresh response has
  been applied; a load sequence discards late responses after a newer load or an unmount.
  Loading, error/retry and the empty states (search / apps only in the switcher / no app at
  all) are separate. A failed request never unlocks an IndexedDB tree from a previous user.
- `static/src/home/home_catalog.js` maps known XML IDs to Vietnamese labels, hints, search
  aliases, icons and a section. `buildCatalog()` returns `{home, system, all, otherApps}`.
  Only entries whose metadata names a Home section appear on Home; everything else counts as
  `otherApps`. A mapping applies only when that XML ID is in the user's tree.
- Main search covers only the entries visible on Home (with or without diacritics, aliases
  such as `khkd`, `lich`, `chat`). Enter opens the first displayed result; IME composing Enter
  is ignored; Escape/clear reset the search.
- A menu entry is an `<a href="/odoo/…">`. A plain click calls `menu.selectMenu(menu)`, exactly
  like the native apps menu (dirty-form guard included); Ctrl/Cmd/Shift/middle click is left
  to the browser.
- `/odoo` without an action opens the first root menu (native `WebClient._loadDefaultApp`),
  which is Home because of its sequence. A user's own Home Action (`res.users.action_id`)
  still wins; the module never writes that field.
- Motion 120–200 ms (`--tp-home-motion`), disabled under `prefers-reduced-motion`. All styles
  are scoped under `.o_tp_web_home`, except the keyframes and the existing action overflow rule.

## Mobile and accessibility (MOBILE-001, CHG-20261104-005)

- `views/tp_web_home_templates.xml` inherits `web.webclient_bootstrap` and sets the backend
  viewport to `width=device-width, initial-scale=1`: native Odoo shipped `user-scalable=no`,
  which blocks pinch zoom. Server test `test_backend_viewport_keeps_user_zoom` guards it.
- Below 768 px the header stacks and grids use two columns; below 576 px one column. Targets are
  at least 44×44 px. The Home root scrolls vertically, with no overflow hiding.
- `static/src/home/burger_menu_patch.js` patches the native phone drawer (`BurgerMenu`):
  Escape closes it, focus moves to its close button when it opens and back to the ☰ toggle
  when it closes. Opening/closing by button or backdrop tap stays native.
- No `overflow-x: hidden`, no smaller fonts, no PWA/service worker/offline cache.

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

UI-HOME-003: [design](../../docs/ui/UI_HOME_003_DESIGN.md),
[acceptance](../../docs/demo/UI_HOME_003_ACCEPTANCE.md),
[user guide](../../docs/demo/UI_HOME_003_USER_GUIDE.md). Operational wrapper:
`scripts/ui_home003.py` (owned clone 18689, verified backup, module-only apply/rollback);
browser checks `scripts/ui_home003_ui.cjs` + `scripts/ui_home003_checks.cjs`.
Earlier: UI-HOME-002 ([design](../../docs/ui/UI_HOME_002_DESIGN.md)), UI-HOME-001
(`docs/demo/UI_HOME_001_RUNBOOK.md`).
The addon still depends only on `web`; it does not install optional apps or write user Home Actions.
