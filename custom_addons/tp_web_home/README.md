# tp_web_home — TANPHAT ONE Trang chủ & Shell thống nhất

Native Odoo Community home page and unified shell identity layer. Since `UI-SHELL-UNIFY-001` (`DEC-043`, `CHG-20261114-001`), Home uses one unified component/template (`#tp-unified-home`) and visual design (ice-blue gradient wave backdrop, consistent navbar, `"Trang chủ"` / `"Không gian làm việc của TANPHAT ONE"`, 3-column desktop grid preserving card size) for every user while server-filtered menus and `user.isSystem` determine which sections (`Phòng ban và đơn vị`, `Nhân sự và tuyển dụng`, `Công cụ cá nhân`) and admin tools (`Tất cả ứng dụng`, `Cài đặt`, `Quản lý ứng dụng`) appear.

### Logo hệ thống (`BRAND-LOGO-001`, `CHG-20261116-009`, 20.0.1.9.0)

Nguồn: `logo/logo.png` (người dùng cung cấp). `static/img/brand/` chứa bản tách từ ảnh gốc, giữ đúng màu `#0092dd`, nền trong suốt:
- `tp_logo_mark.png` (512×512): biểu tượng tam giác TP, dùng trên navbar (ô trắng 32px, mobile 28px) và trang đăng nhập (ô trắng 48px, mobile 34px).
- `tp_logo_full.png` (900×885): biểu tượng + `TAN PHAT JOINT STOCK.Co`, dùng cho thẻ logo trên trang đăng nhập (`tp_web_login`) và logo công ty.
- `favicon.ico` (16/32/48/64): template `layout_brand_favicon` kế thừa `web.layout`, giữ `x_icon` của trang tự đặt.
- `tp_logo_touch.png` (180×180, nền trắng): `apple-touch-icon` của web client; `theme-color` đổi sang `#061b40` theo navbar.

Biểu tượng cây cầu cũ (SVG) đã bỏ khỏi navbar và trang đăng nhập. Logo công ty (`res.company.logo`) được đặt bằng dữ liệu trên main, không nằm trong module.

Shared shell identity & logout live under `static/src/identity/`:
- `identity_service.js`: Singleton `tp_identity` service providing reactive logged-in user identity (`name`, `partnerId`, `avatarUrl`, `initials`), broken-avatar fallback, single `bus_service.subscribe("tp.identity/changed")` subscription (updating only when `payload.partner_id === user.partnerId`), `openPersonalProfile()` via the `tp_personal_profile` registry (falling back to native `res.users` `action_get`), and `performNativeLogout()` (`/web/session/logout` + CSRF + service worker + error toast on failure).
- `user_menu_patch.js`: Patches `UserMenu` (and BurgerMenu template via `shell_navbar.xml`) so the dropdown contains `[profile icon] Thông tin cá nhân` and `[logout icon] Đăng xuất` while leaving `user_menuitems`, presence (`im_status`), and systray registries intact.
- `user_account_menu.js` / `.xml` / `.scss`: Reusable `<TpIdentityAvatar>` and `<TpUserAccountMenu>` (with 2-item dropdown `Thông tin cá nhân` + `Đăng xuất`) mounted in HR and KH-KD sidebars; navbar hides `.o_user_menu` and `.o_mobile_menu_toggle` only while `body.o_tp_hr_shell` or `body.o_tp_kd_shell` is active so each view keeps a single user menu entry point.
- Note: `"Quản lý nhân sự"` only maps to `tp_hr_workspace.menu_tp_hr_root` (no fallback to base `hr.menu_hr_root`), ensuring users without HR workspace access do not see HR on Home.

See `docs/demo/UI_SHELL_UNIFY_001_ACCEPTANCE.md` and `docs/demo/UI_SHELL_AUTH_001_ACCEPTANCE.md`.

### Shared Table Filter Bar (`UI-TABLE-FILTER-001` — 14/11/2026)

Shared OWL search/filter components live under `static/src/search/` (`filter_domain.js`, `relation_search_helper.js`, `table_filter_bar.js`, `table_filter_bar.xml`, `table_filter_bar.scss`) and HOOT tests under `static/tests/search/`:
- Pending vs Applied state (`Chưa áp dụng` -> `Áp dụng` / `Xóa bộ lọc` / `Bộ lọc nâng cao`), chip removal, `Tất cả` vs `Chưa khai báo` (`__false__`), multi-select `OR` across `AND` criteria, `Asia/Ho_Chi_Minh` date/datetime bounds validation (`from <= to`), server-side `Many2one` (`name_search(domain=...)`), bidirectional sync with Odoo `SearchModel` / Favorites, and desktop/mobile grid layout in ControlPanel without overlapping pagers.

## What it adds

| Record | XML ID | Notes |
| --- | --- | --- |
| Client action | `tp_web_home.action_home` | tag `tp_web_home.home`, path `tp-home` → `/odoo/tp-home` |
| Root menu | `tp_web_home.menu_home` | "Trang chủ", `base.group_user`, sequence 1 |
| Systray item | `tp_web_home.home_button` | home icon in the navbar, label "Trang chủ" |

Nothing else: no model, no ACL, no controller, no override of another module's record.
Depends only on `web`. Static files: launcher JS/XML/SCSS, shared `identity/` components/service, local SVG icons (incl. `apps.svg`).

## Layout (UI-SHELL-UNIFY-001)

| Section | Entries | Shown when |
| --- | --- | --- |
| Phòng ban và đơn vị | Kế hoạch Kinh doanh (`tp_kd_workspace.menu_kd`) + placeholder Phòng Thiết kế, Phòng Kỹ Thuật, Phòng BIM-QC, TADIC (`user.isSystem`) | at least 1 permitted entry |
| Nhân sự và tuyển dụng | Quản lý nhân sự (`tp_hr_workspace.menu_tp_hr_root`) + placeholder Tuyển dụng (`user.isSystem`) | at least 1 permitted entry |
| Công cụ cá nhân | Việc cá nhân (`project_todo.menu_todo_todos`), Lịch làm việc (`calendar.mail_menu_calendar`), Trao đổi (`mail.menu_root_discuss`) | at least 1 menu in the user's tree |
| Công cụ hệ thống (header tools) | Tất cả ứng dụng (in-page panel), Cài đặt (`base.menu_administration`), Quản lý ứng dụng (`base.menu_management`) | session `is_system` (`base.group_system`) and permitted menu |

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

## Back button (UI-BACK-001, DEC-046, CHG-20261115-002)

- `static/src/back/back_button.{js,xml,scss}` patches the ControlPanel so every act_window
  form (not dialogs, lists, kanban, client dashboards, `res.config.settings` or module
  wizards) shows one `← Quay lại` button (40px, 44px on small screens) with the tooltip
  `Quay lại: <previous screen>`.
- `static/src/back/back_navigation.js` holds the shared helpers: `action.restore` of the
  previous breadcrumb (keeps filters, page and page size), otherwise a model fallback from
  the `tp_back_fallbacks` registry (xmlids only), the action's own list, then Home. A dirty
  form asks Save and go back / Discard / Stay; a failed save stays on the form.
- New screens register `registry.category("tp_back_fallbacks").add(model, xmlid)` instead of
  drawing their own button. Standard and coverage: `docs/ui/UI_BACK_001_STANDARD.md`.

## Input fields (UI-INPUT-001, CHG-20261113-009)

- `static/src/inputs/input_tokens.css` is the only source of input colours and sizes
  (`--tp-input-*`). It is in `web.assets_backend` (glob) and, through this manifest, in
  `tp_web_login.assets_login`. Modules use the tokens and never copy the values.
- `static/src/inputs/inputs.scss` styles native widgets:
  - Editable fields get a 4-sided frame with hover, focus (blue ring), error (red border,
    tint and inset line) and disabled states.
  - Many2one/selection carets are always visible; date fields show a calendar icon.
  - Labels of required fields get a `*` from the same `o_required_modifier` Odoo validates.
  - A locked field in edit mode reads as read-only (tint, no frame).
  - Editable list rows get an inset cell frame, so the row height does not change.
- Scope: only the outermost `.o_input` of an editable widget in `.o_form_editable`. Nested
  inputs, checkbox/radio/toggle, file inputs and list cells are left out. No bare
  `input, select, textarea` selectors and no `!important`.
- Below md, Odoo's outlined field box is the single frame. Reduced motion turns transitions off.
- Rollback: remove `static/src/inputs/` only together with the module SCSS that reads the
  tokens (see [acceptance](../../docs/demo/UI_INPUT_001_ACCEPTANCE.md)).

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
