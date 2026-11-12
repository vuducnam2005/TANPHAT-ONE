# UI-HOME-003 — Trang chủ theo workspace, KH-KD trước

Ngày 07/11/2026, Asia/Saigon. CHG-20261107-006. Căn cứ: [prompt](../prompts/CLAUDE_UI_HOME_003_KD_FIRST.md), [DEC-031](../DECISIONS.md#dec-031--trang-chủ-theo-workspace-ưu-tiên-hoàn-thành-kh-kd-07112026), DEC-030. Baseline: UI-HOME-002 CHG-20261107-004 (`tp_web_home` 20.0.1.2.0), KD-UI-004 CHG-20261107-003 (`tp_kd_workspace` 20.0.1.3.0), cả hai `IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT`; checker CHG-005 PASS, không có checkpoint mở khi bắt đầu.

## 1. Phạm vi

- Chỉ đổi trình bày/catalog/tìm kiếm của `tp_web_home`. Không đổi model, quyền, menu/action XML, parent/sequence menu, Home Action, dữ liệu hoặc phụ thuộc (`web`).
- `tp_kd_workspace` không sửa: inventory mục 3 cho thấy không có link KH-KD còn thiếu thật sự.
- Không dựng workspace phòng khác, thẻ phòng ban, nút trống hoặc “sắp ra mắt”; không đưa HR/Hóa đơn vào KH-KD.
- Clone riêng: `tp_tanphat_home003_20261107`, cổng 18689, source/config/data trong `.local/ui-home003/` (tooling `scripts/ui_home003.py`). Không dùng clone 18589 (UI-HOME-002), 18489 (KD-UI-004), 18169/18269 hoặc demo 18109.

## 2. Inventory root menu (dev 18069, payload `load_menus` UI-HOME-002 verify)

ID số/URL là bằng chứng runtime ngày kiểm, không hardcode vào catalog. “Admin” = `base.group_system`; “KH-KD” = tài khoản KH-KD editor của bộ dữ liệu KD-NATIVE-001 (không có `base.group_system`).

| XMLID root | Tên native | Action (runtime) | Actor thấy menu | Trên Home trước (002) | Trên Home sau (003) | Cách mở còn lại |
| --- | --- | --- | --- | --- | --- | --- |
| `tp_kd_workspace.menu_kd` | Kế hoạch Kinh doanh | 510 Tổng quan KH-KD | `tp_core.group_user` (admin, KH-KD) | Không gian làm việc | **Không gian làm việc** (thẻ chính) | Switcher native; Tìm `khkd` |
| `project_todo.menu_todo_todos` | Việc cá nhân | 287 `/odoo/to-do` | internal | Công việc cá nhân | **Công cụ cá nhân** | Switcher |
| `calendar.mail_menu_calendar` | Lịch làm việc | 301 `/odoo/calendar` | internal | Công việc cá nhân | **Công cụ cá nhân** | Switcher |
| `mail.menu_root_discuss` | Trao đổi | 125 `/odoo/discuss` | internal | Công việc cá nhân | **Công cụ cá nhân** | Switcher |
| `tp_core.menu_platform` → `tp_project.menu_tp_projects`, `tp_contract.menu_tp_contracts`, `tp_core.menu_work_items` | TANPHAT ONE → TP Projects / TP Contracts / Danh mục công việc | 289 / 509 / 79 | `tp_core.group_user` | Ứng dụng nghiệp vụ (3 ô lá) | Không trên Home chính; admin: panel Tất cả ứng dụng | Switcher “TANPHAT ONE” → mục con; KH-KD sidebar có Hồ sơ dự án và TP Contracts |
| `contacts.menu_contacts` | Khách hàng & đối tác | 303 `/odoo/contacts` | admin, KH-KD | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher |
| `crm.crm_menu_root` | CRM | 442 `/odoo/crm` | admin, KH-KD | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher; KH-KD sidebar “Cơ hội và hồ sơ thầu” |
| `project.menu_main_pm` | Dự án | 238 `/odoo/project` | admin (KH-KD editor không có) | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher; KH-KD sidebar “Kế hoạch và công việc” |
| `spreadsheet_dashboard.spreadsheet_dashboard_menu_root` | Bảng tổng hợp | 458 | admin, KH-KD | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher |
| `account.menu_finance` | Hóa đơn | 377 | admin | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher |
| `hr_timesheet.timesheet_menu_root` | Giờ làm việc | 485 | admin | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher |
| `hr.menu_hr_root` | Nhân sự | 210 admin / 207 KH-KD | admin, KH-KD | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher (giữ action khác nhau theo actor) |
| `hr_expense.menu_hr_expense_root` | Chi phí | 475 | admin, KH-KD | Ứng dụng nghiệp vụ | Không trên Home chính; panel admin | Switcher |
| `base.menu_administration` | Cài đặt | 89 `/odoo/settings` | admin | Quản trị hệ thống | **Quản trị hệ thống** (chỉ `isSystem`) | Switcher |
| `base.menu_management` | Ứng dụng Odoo | 36 `/odoo/apps` | admin, KH-KD (theo server) | Quản trị hệ thống | **Quản lý ứng dụng** (chỉ `isSystem`) | Switcher (KH-KD editor vẫn có theo quyền server) |
| `base.menu_tests`, `utm.menu_link_tracker_root`, root lạ | Tên native | runtime | theo server | Quản trị / Ứng dụng nghiệp vụ | Panel admin | Switcher |
| `tp_web_home.menu_home` | Trang chủ | 502 `/odoo/tp-home` | `base.group_user` | (chính trang) | (chính trang) | Nút ngôi nhà, switcher, `/odoo` |

Không xóa root, không đổi parent/sequence/groups. Mỗi menu được cấp vẫn còn lối mở thật bằng switcher native: desktop `.o_navbar_apps_menu` (dropdown), màn nhỏ `.o_menu_toggle` → “All Apps”. Browser test kiểm thực tế cả hai (H06).

## 3. Đối chiếu link KH-KD với app ngoài workspace

| Nhu cầu | Trong KH-KD (sidebar) | App native tương ứng | Kết luận |
| --- | --- | --- | --- |
| Hồ sơ dự án | `menu_projects` → action 511, `project.project` `tp_managed=True`, view KH-KD | TP Projects 289: cùng model/domain, view `tp_project` | Cùng dữ liệu; không thêm link |
| Hợp đồng/phụ lục | `menu_contracts` → server action 509 `tp_contract.action_tp_contracts` | TP Contracts 509 | Cùng action; không thêm link |
| Cơ hội/thầu | `menu_opportunities` → 512, `crm.lead` có `tp_project_id` | CRM 442: toàn pipeline | Domain KH-KD giữ; CRM vẫn qua switcher |
| Kế hoạch/WBS | `menu_tasks` → 513, `project.task` dự án `tp_managed` | Dự án 238: mọi dự án | Domain KH-KD giữ; Project qua switcher |
| Hồ sơ khác | Giao khoán, sản lượng, nghiệm thu, kế hoạch định kỳ, thanh toán, chứng chỉ, nghĩa vụ, báo cáo | — | Đã có trong sidebar |

Không có link thiếu thật sự → không sửa `tp_kd_workspace`, không làm lại sidebar/Tổng quan. Danh mục công việc (`tp_core`) là cấu hình chung, mở qua switcher “TANPHAT ONE”.

## 4. Bố cục

```text
TANPHAT ONE                                   [Tìm không gian hoặc công cụ…   ×]
Trang chủ

Không gian làm việc
[icon  Kế hoạch Kinh doanh                                        →]
[      Hồ sơ, kế hoạch và điều hành KH‑KD                          ]

Công cụ cá nhân
[Việc cá nhân]        [Lịch làm việc]        [Trao đổi]

Quản trị hệ thống                                   (chỉ user.isSystem)
[Tất cả ứng dụng ▾]   [Cài đặt]   [Quản lý ứng dụng]
└ panel trong trang: ô tìm riêng + lưới gọn các app của chính user

ⓘ Ứng dụng khác được cấp cho tài khoản mở từ nút ứng dụng ở góc trái thanh điều hướng.
   (cuối trang; chỉ khi còn app ngoài Home, không tìm kiếm và có mục hiển thị)
```

- KH-KD: thẻ ngang xanh than, cao ~96px, rộng tối đa ~640px; không banner, không KPI/biểu đồ.
- Công cụ cá nhân và hàng quản trị: lưới 3 cột (tối đa 920px), 2 cột dưới 768px, 1 cột dưới 576px; ô cao ≥64px (≥72px dưới 576px).
- Quản trị: hàng nút viền nhẹ, nhỏ hơn; “Tất cả ứng dụng” là nút `aria-expanded/aria-controls`, mở panel ngay dưới, không modal. Panel: tiêu đề, ô tìm, lưới `auto-fill minmax(min(100%, 210px), 1fr)` (1–4 cột trong 920px), nút Đóng. Escape trong panel: xóa từ khóa nếu có, nếu không thì đóng và trả focus về nút mở; `stopPropagation` để không ảnh hưởng phần sau.
- Responsive 360–1920px, zoom thật 125/150%: cuộn dọc ở `.o_tp_web_home.o_action`, không tràn ngang, vùng chạm ≥44px, focus ring rõ.
- Motion: hover/focus 150ms (nền/viền/translate 1px của mũi tên KH-KD); panel mở 160ms opacity/translate; tắt khi `prefers-reduced-motion: reduce`. Không animation lặp/chớp.
- Token giữ UI-HOME-002 (`#F4F6F8`, `#17324D`, `#255F85`, …). Style chỉ dưới `.o_tp_web_home`; không đổi navbar/theme.

## 5. Catalog, search, quyền

- Nguồn duy nhất: cây menu của menu service native (server đã lọc theo nhóm của chính user). Không đọc `ir.ui.menu` riêng, không sudo, không localStorage.
- `buildCatalog(tree, { debug, isSystem })` trả `{ home, system, all, otherApps }`:
  - `home`: workspace (`tp_kd_workspace.menu_kd`) + personal (To-do, Calendar, Discuss), chỉ khi XMLID có trong cây và có action.
  - `system` (chỉ khi `isSystem`): mục “Tất cả ứng dụng” (mở panel) + `base.menu_administration` (Cài đặt) + `base.menu_management` (Quản lý ứng dụng) nếu có trong cây.
  - `all` (chỉ dùng trong panel, chỉ khi `isSystem`): mọi app của user (giữ quy tắc UI-HOME-002: mở rộng lá `tp_core.menu_platform`, dedup theo menu ID, app lạ giữ tên/icon native).
  - `otherApps`: số app được cấp không có trên Home → quyết định dòng gợi ý switcher và empty state.
- Gate quản trị: `user.isSystem` (`session.is_system` = `res.users._is_system()` = `base.group_system`). Không dùng username, user ID, `tp_core.group_manager` hay `user.isAdmin` (= `base.group_erp_manager`). Gate chỉ là trình bày; quyền dữ liệu/menu vẫn do backend.
- Search chính: chỉ trên mục đang hiển thị ở Home (`home` + `system`), không gồm `all`. Mỗi từ gõ phải là đầu một từ của nhãn/mô tả/tên native/alias (`du an` khớp “dự án” nhưng không khớp “ứng dụng”/“quản”). Có/không dấu, alias (`khkd`, `kinh doanh`, `todo`, `lich`, `chat`…), Enter mở kết quả đầu theo thứ tự hiển thị, IME guard (`isComposing`, keyCode 229), Escape/nút xóa. Search trong panel chỉ tồn tại khi panel mở (sau gate quản trị).
- Empty: nếu user không có mục Home nhưng còn app → “Trang chủ chưa có không gian làm việc cho tài khoản này” + hướng dẫn switcher; chỉ khi không còn app nào mới báo “chưa được cấp ứng dụng”.

## 6. Tải menu và trạng thái

Giữ cơ chế UI-HOME-002: mỗi lần mount gọi `menu.reload()`, chỉ dựng catalog sau response được áp; loading/error/Thử lại riêng; lỗi (gồm 401/403/503) không mở cây IndexedDB cũ. Sequence guard bỏ kết quả của lần tải cũ đến muộn và khi unmount. Panel chỉ render khi trạng thái `ready`; tải lại bắt đầu → panel đóng. Không ghi `res.users.action_id`, không đổi session/auth.

## 7. Điều hướng

Mỗi lối vào menu là `<a href="/odoo/…">`; click thường gọi `menu.selectMenu(menu)` (giữ dirty-form guard native), Ctrl/Cmd/Shift/middle để trình duyệt xử lý. Giữ `/odoo/tp-home`, deep link, refresh/Back, nút Home systray, drawer mobile (patch MOBILE-001), Home Action cá nhân.

## 8. Kiểm thử và áp dụng

[Acceptance H01–H10](../demo/UI_HOME_003_ACCEPTANCE.md). Odoo test `/tp_web_home`, HOOT catalog/component, browser clone (actor admin, KH-KD editor/reviewer/planner, fixture: nhân viên không KH-KD, user HR/Hóa đơn không quản trị, quản lý kinh doanh không `base.group_system`, quản trị đa công ty, Home Action riêng, portal). Backup verify sát áp, upgrade chỉ `tp_web_home`, dev verify chỉ đọc, so dữ liệu/quyền/menu payload bằng nội dung.

## 9. As-built

`tp_web_home` 20.0.1.3.0, chỉ depends `web`; không model/ACL/controller/menu/action mới. Thay đổi so với UI-HOME-002:

| File | Thay đổi |
| --- | --- |
| `static/src/home/home_catalog.js` | `SECTIONS` còn 3 khu (workspace/personal/system); `buildCatalog(tree, {debug, isSystem})` → `{home, system, all, otherApps}`; mục panel `all-apps`; `filterTiles` khớp đầu từ; `homeSections` chỉ đi qua mục Home |
| `static/src/home/home_launcher.js` | Gate `user.isSystem`; panel `Tất cả ứng dụng` (mở/đóng, ô tìm riêng, Escape hai nấc có `stopPropagation`, trả focus nút mở, đóng khi reload); empty `search`/`switcher`/`none`; Enter chỉ trên mục hiển thị |
| `static/src/home/home_launcher.xml` | Bỏ khu Ứng dụng nghiệp vụ; thẻ KH-KD ngang; hàng quản trị; panel `role=region` + `aria-expanded/controls`; dòng ghi chú switcher ở cuối |
| `static/src/home/home_launcher.scss` | Thẻ KH-KD 640px/96px, ô cá nhân ≥64px, panel 160ms, `--tp-home-motion` 150ms, reduced-motion; tất cả dưới `.o_tp_web_home` |
| `static/img/apps.svg` | Icon cục bộ cho Tất cả ứng dụng |
| `tests/test_home_menu.py` | + `test_administration_area_follows_group_system_not_access_rights` (12 test) |
| `static/tests/home/home_launcher.test.js` | Viết lại cho bố cục mới: 9 catalog + 13 launcher + 2 nút Home = 24 test |
| `README.md`, `__manifest__.py` | Mô tả UI-HOME-003, version 20.0.1.3.0 |

- Link KH-KD giữ nguyên: không sửa `tp_kd_workspace` (mục 3 không thấy link thiếu thật). Menu/action dùng lại: `tp_kd_workspace.menu_kd`, `project_todo.menu_todo_todos`, `calendar.mail_menu_calendar`, `mail.menu_root_discuss`, `base.menu_administration`, `base.menu_management`; không tạo link mới ngoài mục panel trong trang.
- Khác wireframe ban đầu: dòng phụ chỉ ghi “Trang chủ” (không in tên người dùng); dòng ghi chú switcher nằm cuối trang, sau khu quản trị; search khớp đầu từ thay vì chuỗi con.
- Tooling: `scripts/ui_home003.py` (clone 18689 `tp_tanphat_home003_20261107`, backup verify, áp/rollback chỉ module), `scripts/ui_home003_ui.cjs` + `scripts/ui_home003_checks.cjs` (browser clone before/after/hoot, dev before/verify chỉ đọc).
- Kết quả, backup, rollback: [acceptance](../demo/UI_HOME_003_ACCEPTANCE.md). Hướng dẫn: [user guide](../demo/UI_HOME_003_USER_GUIDE.md).
