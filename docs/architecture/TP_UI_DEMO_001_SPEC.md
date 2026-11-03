# UI-DEMO-001 — Đặc tả demo native Odoo toàn hệ thống

**Change:** CHG-20261030-002 · **Căn cứ:** DEC-024 (demo native Odoo toàn hệ thống), DEC-023 (shell chung, workspace theo quyền), DEC-017 (grant `financial_read` theo project), DEC-013 (BASE là nơi duyệt chính thức), DEC-020/021 (actor fixture cho workflow draft/review) · **Trạng thái:** IMPLEMENTED_PENDING_AUDIT sau khi bàn giao; không phải technical/business acceptance.

Demo này là một **khung trình diễn cho lãnh đạo** chạy trong Odoo web client gốc, trên database và cổng riêng, chỉ có dữ liệu giả. Nó không thay frontend React chính thức (DEC-001/023), không mở pilot và không biến phần minh họa thành nghiệp vụ đã chốt.

## UI-DEMO-002 — Điều hướng theo công việc (CHG-20261030-005)

Yêu cầu trực tiếp ngày 30/10/2026 thay lựa chọn “giữ nguyên menu” của CHG-003 trong app `tp_demo_workspace.menu_demo_root`. Giữ SCSS của CHG-003 và nội dung dashboard; đây là delta demo native theo DEC-024, không phải common shell React chính thức. Đã triển khai trên demo và kiểm cuối 31/10/2026, trạng thái `IMPLEMENTED_PENDING_AUDIT`; bằng chứng runtime/test trong [bàn giao CHG-005](../demo/UI_DEMO_002_HANDOFF.md).

```text
[Ứng dụng] TANPHAT ONE [Demo] [Tất cả phân hệ]       [Dữ liệu trình diễn] [Tiện ích native]
[Tổng quan] [Dự án & công việc ▾] [Hợp đồng & hồ sơ ▾] [Kinh doanh ▾] [Nguồn lực ▾] [Đề nghị]
Breadcrumb/ngữ cảnh của control panel native
```

Tầng đầu giữ app switcher, thông báo, công ty, tài khoản/đăng xuất và cảnh báo môi trường. Tầng hai có tối đa sáu nhóm, trong đó Kinh doanh chỉ có khi server trả menu CRM/Bid. Dưới 992px, “Phân hệ” mở cùng dialog responsive chứa các nhóm và ô tìm kiếm; app switcher native trên điện thoại chỉ liệt kê ứng dụng, tránh trùng menu nghiệp vụ. Không thay navigation của app `tp_core.menu_platform` hoặc app native khác.

### Mapping trước/sau theo actor

Mọi XML ID dưới đây giữ namespace `tp_demo_workspace`; action path và action cũ giữ nguyên. Dấu ✓ là menu server trả cho actor; giới hạn dữ liệu backend vẫn áp dụng. Nhóm chỉ mở danh sách, không gọi action giả.

| Nhóm mới | Nhãn Việt / tên chuẩn | Leaf menu XML ID → action XML ID (bỏ tiền tố namespace) | Lãnh đạo trước/sau | Kỹ sư trước/sau | Loại |
| --- | --- | --- | --- | --- | --- |
| Tổng quan | Điều hành doanh nghiệp / TP Dashboard | `menu_demo_dashboard` → `action_demo_dashboard` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Dự án & công việc | Dự án / TP Projects | `menu_demo_projects` → `action_demo_projects` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Dự án & công việc | Dự án / TP Projects | `menu_demo_project_overview` → `action_demo_project_overview` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Dự án & công việc | Khảo sát hiện trường / TP Survey | `menu_demo_survey` → `action_demo_survey` | ✓ / ✓ | ✓ / ✓ | Minh họa |
| Dự án & công việc | Hồ sơ thiết kế / TP Design | `menu_demo_design` → `action_demo_design` | ✓ / ✓ | ✓ / ✓ | Minh họa |
| Dự án & công việc | Tiến độ và giao việc / TP Tasks | `menu_demo_tasks` → `action_demo_tasks` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Hợp đồng & hồ sơ | Hợp đồng / TP Contracts | `menu_demo_contracts` → `action_demo_contracts` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Hợp đồng & hồ sơ | Hợp đồng / TP Contracts | `menu_demo_revisions` → `action_demo_revisions` | ✓ / ✓ | ✓ / ✓ | Odoo |
| Hợp đồng & hồ sơ | Hợp đồng / TP Contracts | `menu_demo_contract_flow` → `action_demo_contract_flow` | ✓ / ✓ | ✓ / ✓ | Odoo, chỉ đọc |
| Hợp đồng & hồ sơ | Tài liệu và hồ sơ / TP Documents | `menu_demo_documents` → `action_demo_documents` | ✓ / ✓ | ✓ / ✓ | Tệp theo quyền |
| Kinh doanh | Cơ hội kinh doanh / CRM | `menu_demo_crm` → `action_demo_crm` | ✓ / ✓ | — / — | Odoo |
| Kinh doanh | Dự thầu / Bid | `menu_demo_bid` → `action_demo_bid` | ✓ / ✓ | — / — | Minh họa |
| Nguồn lực | Nhân sự / TP HR | `menu_demo_employees` → `action_demo_employees` | ✓ / ✓ | ✓ / ✓ | Danh bạ Odoo |
| Nguồn lực | Nhân sự / TP HR | `menu_demo_staffing` → `action_demo_staffing` | ✓ / ✓ | ✓ / ✓ | Minh họa |
| Nguồn lực | Tài chính và chi phí / TP Finance | `menu_demo_finance` → `action_demo_finance` | ✓ / ✓ | ✓ / ✓ | Số HĐ từ Odoo; nghiệm thu/tiền thu minh họa; kỹ sư không có tiền |
| Nguồn lực | Tài chính và chi phí / TP Finance | `menu_demo_line_amounts` → `action_demo_line_amounts` | ✓ / ✓ | ✓ / ✓ | Kỹ sư danh sách rỗng theo rule |
| Đề nghị | Đề nghị nội bộ / Request | `menu_demo_request` → `action_demo_request` | ✓ / ✓ | ✓ / ✓ | Minh họa; BASE duyệt chính thức |

Tổng: 17 leaf / 12 phân hệ cho `demo.lanhdao`, 15 leaf / 10 phân hệ cho `demo.kysu`; Hợp đồng không nằm trong nhóm bảo mật kinh doanh. Trước/sau được đối chiếu theo server menu và action ID thực, không theo tên hiển thị. Finance không được mô tả là kế toán, thanh toán hoặc nghiệm thu đã hoàn thiện.

### Native extension và quyền

- Tổ chức feature tại `static/src/navigation/` (catalog, JS, XML, SCSS), HOOT tại `static/tests/navigation/`.
- QWeb inheritance gắn lớp riêng trên header khi current app đúng XML ID Demo; thay section native trong đúng app, nên `NavBar.adapt()` không đo vùng custom. App khác giữ container `appSubMenus`, nút More 46px và native overflow.
- Patch tĩnh tối thiểu `NavBar.components` để đăng ký hai component vì NavBar chưa có component registry extension point. Không patch prototype, service hoặc router; không copy WebClient/NavBar.
- Catalog chỉ bổ sung nhãn/icon/mô tả cho leaf action có trong `menuService.getMenuAsTree(currentApp.id)` từ `/web/webclient/load_menus`. Không RPC mới, numeric ID hardcode, URL mới, quyền frontend hoặc `sudo`. Chọn mục gọi `menuService.selectMenu(actualMenu)`; native href dùng `actionPath/actionID` do server trả.
- Active đọc `action.currentController.action` khi `ACTION_MANAGER:UI-UPDATED` (và action update cho client actions), khớp action ID/path hoặc model form native. Không gọi `doAction` phụ để đồng bộ; context/domain/breadcrumb/history do Odoo giữ.
- Dropdown và dialog dùng component native cho keyboard/Esc/focus; listener gắn bằng Owl `useListener`, tự dọn khi unmount. Dialog đóng khi launcher unmount/rời app, focus trả về nút mở nếu còn tồn tại. Portal có namespace riêng.

### Tìm nhanh, hình ảnh, responsive và nghiệm thu

Tìm chỉ trên tên/mô tả/alias và leaf menu được server cho phép, không trên hồ sơ nghiệp vụ. Chuẩn hóa NFD, bỏ dấu và `đ`, không phân biệt hoa thường; alias gồm project/dự án, contract/hợp đồng, bid/đấu thầu, request/đề nghị/yêu cầu, hồ sơ/tài liệu. Có xóa tìm kiếm và lời dẫn khi rỗng. Thẻ phân hệ có icon Odoo local (`oi`, `data-icon`) một màu, tên Việt, tên chuẩn, mô tả, leaf bấm trực tiếp và nhãn minh họa đúng leaf (HR/Finance hỗn hợp ghi rõ trong mô tả).

Tokens: mực `#17324F`, xanh tương tác `#2F6DB3`, chữ phụ `#526578`, nền `#FFFFFF`, vùng hover `#EEF4FB`, vùng active `#E8F1FB`; font hệ thống Odoo hỗ trợ tiếng Việt. Chữ menu 14–15px, vùng bấm tối thiểu 40px; active có nền + đường nhấn, focus có outline. Không CDN, rainbow/gradient mới. Mở panel 150ms, chỉ khi không `prefers-reduced-motion`. Dialog desktop 3 cột nhóm, tablet 2 cột, mobile 1 cột; body cuộn bên trong.

Tự review theo [frontend-design](C:/Users/vuduc/.codex/skills/frontend-design/SKILL.md): chọn cấu trúc nhóm theo công việc tư vấn cầu đường, tên Việt giải thích bằng hành động; không lặp dashboard thành lưới thẻ điều hướng khác hoặc nhồi tên dài vào một hàng. Màu giữ CHG-003; không đổi typography/nội dung nghiệp vụ chỉ để trang trí.

Tiêu chí kiểm: mọi leaf mở đúng action cho cả hai actor; kỹ sư không có CRM/Bid trong tree/panel/search; Finance/tệp/tiền theo rule; deep link/reload/back/forward giữ app/active/context; rời app Demo không còn custom navigation/theme; tiện ích/logout/breadcrumb và neutralized banner giữ nguyên; keyboard/Esc/focus; 1440/1366/1024/768/375 và zoom 125%/150%; không horizontal overflow hoặc lỗi console/network không giải thích. HOOT kiểm mapping/filter/active/no-menu; Odoo test kiểm cây menu và toàn bộ regression addon trên DB demo test sở hữu riêng.

**Kết quả triển khai, 31/10/2026:** Odoo 21/21 trên `tp_tanphat_demo_ui001_test`; HOOT 6/6; live 17/17 leaf lãnh đạo và 15/15 kỹ sư, không mất menu/action so baseline. Hai actor đạt 5 viewport 1440×900, 1366×768, 1024×768, 768×768, 375×812 và zoom Chromium thật 125%/150%. Bàn phím/focus, reduced motion, context `DEMO-DUONG-02`, reload/history/chuyển app và logout native đạt; console/network ma trận không lỗi. Bằng chứng số đo, ảnh đã tự xem, giới hạn log và file delta ở [bàn giao](../demo/UI_DEMO_002_HANDOFF.md). Đây là kết quả kiểm triển khai, chưa phải audit độc lập hoặc nghiệm thu nghiệp vụ.

## 1. Mục tiêu trình diễn

Lãnh đạo xem xong phải trả lời được:

1. TANPHAT ONE quản lý những mảng nào, và giao diện thống nhất ra sao (một app, một menu, một ngôn ngữ thiết kế).
2. Một dự án liên kết với cơ hội, hợp đồng, công việc và tài liệu như thế nào.
3. Các phòng ban dùng chung một nền tảng nhưng menu, workspace và dữ liệu khác nhau theo quyền (so sánh hai tài khoản demo).
4. Phần nào lấy từ Odoo/source hiện có (**Dữ liệu Odoo**), phần nào chỉ minh họa hướng phát triển (**Minh họa định hướng**).

## 2. Môi trường

| Thành phần | Giá trị |
| --- | --- |
| Database | `tp_tanphat_demo_ui001` (tạo mới từ source, `template0`, owner `tp_odoo`); DB test riêng `tp_tanphat_demo_ui001_test` |
| Thư mục runtime | `.local/ui-demo-001/` (config, data-dir/filestore, log, pid, owner marker, credential, ảnh chụp) — đã ignore |
| HTTP | `127.0.0.1:18109` (demo), `127.0.0.1:18119` (HttpCase khi chạy test); không bind mạng ngoài |
| PostgreSQL | cluster local hiện có `.local/postgres` cổng 55432 (khởi động bằng `dev.ensure_postgres` sau kiểm ownership); chỉ tạo/sửa DB demo |
| Module | `tp_demo_workspace` và dependency của nó: `tp_core`, `tp_organization`, `tp_project`, `tp_contract`, `project`, `hr`, `crm` (kéo theo `mail`, `sales_team`…). Không cài `tp_api`, `tp_planning_api`, `tp_web_login`, `account`, `hr_timesheet`, `survey`, `purchase_requisition` |
| Ngôn ngữ | `vi_VN` được nạp khi khởi tạo DB; actor demo dùng `vi_VN`, múi giờ `Asia/Ho_Chi_Minh` |
| Cron/thư | `max_cron_threads = 0` và mọi `ir.cron` của DB demo bị tắt khi seed; `smtp_server` trỏ cổng đóng trên loopback; `neutralize_database` chạy sau seed; actor nhận thông báo trong Odoo (`notification_type = inbox`); mật khẩu demo được băm trực tiếp (không kích hoạt thư “đổi mật khẩu” của `mail`); không có connector BASE, payment, SMS, webhook. Lần seed đầu (trước bản sửa) để lại 20 `mail.mail` trạng thái `exception`, không gửi được, giữ nguyên không xóa |
| Tooling | `scripts/ui_demo.py prepare / seed / start / status / stop / test` với guard target, ownership, cổng bận và PID |

## 3. Actor demo

Không dùng admin để trình diễn. Mật khẩu sinh ngẫu nhiên khi `prepare`, lưu ở `.local/ui-demo-001/credentials.json`.

| Login | Vai trò trình diễn | Nhóm | Phạm vi dữ liệu |
| --- | --- | --- | --- |
| `demo.lanhdao` | DEMO Lãnh đạo điều hành | `group_demo_viewer`, `group_demo_business` (ngầm định `tp_core.group_user`) | Assignment `reader` trên 3 dự án DEMO; grant `financial_read` trên 3 dự án; xem CRM/Bid |
| `demo.kysu` | DEMO Kỹ sư thiết kế | `group_demo_viewer` | Assignment `reader` chỉ trên `DEMO-DUONG-02`; **không** có `financial_read`; không thấy menu Kinh doanh |
| `demo.lap-hd` | Actor fixture lập/gửi hợp đồng | `tp_core.group_user` | Không có mật khẩu, không đăng nhập được; chỉ để chạy workflow CTR-002a tạo hồ sơ draft/in_review/returned |
| `demo.ra-soat` | Actor fixture rà soát thương mại | `tp_core.group_user` | Không có mật khẩu; chỉ để chạy `return_review`; khác người gửi theo DEC-021 |

Grant do fixture tạo bằng superuser trên DB demo theo đúng model `tp.project.grant` hiện có (DEC-024 cho phép fixture actor/grant trong DB demo). Không cấp `tp_core.group_manager`, HR Manager, Sales Manager hay quyền quản trị cho actor demo.

## 4. Bản đồ menu và workspace

App **TANPHAT ONE – Demo** (menu gốc, chỉ hiện với `group_demo_viewer`). Trang đích của actor demo là TP Dashboard.

| Menu | Mục con | Loại | Nguồn |
| --- | --- | --- | --- |
| TP Dashboard | — | Client action | Projection đọc trong addon demo (ORM theo quyền người xem) |
| TP Projects | Danh sách dự án · Tổng quan dự án | Native list/kanban/form · client action | `project.project` (`tp_managed`, `tp_code`, `tp_department_id`) |
| TP Survey | Khảo sát (minh họa) | Client action | Dữ liệu minh họa trả từ backend theo dự án đọc được |
| TP Design | Hồ sơ thiết kế (minh họa) | Client action | Như trên |
| TP Contracts | Hợp đồng · Phiên bản rà soát · Luồng rà soát | Native list/form (chỉ đọc) · client action | `tp.contract`, `tp.contract.revision`, `tp.contract.line` |
| TP Tasks | Công việc | Native kanban/list/form (chỉ đọc) | `project.task`, `project.task.type`, `project.tags` |
| TP HR | Danh bạ nhân sự · Năng lực & phân bổ (minh họa) | Native · client action | `hr.employee.public`, `hr.department` |
| TP Finance | Tổng hợp tài chính | Client action (thật + minh họa) | `tp.contract.line.amount` qua `_amount_summary()`; số minh họa chỉ trả cho grant |
| TP Documents | Tài liệu hồ sơ | Native list/form (chỉ đọc) | `tp.contract.document` (general/financial) |
| Kinh doanh | Cơ hội (CRM) · Dự thầu (minh họa) | Native · client action | `crm.lead`; Bid minh họa không có số tiền |
| Đề nghị | Đề nghị BASE (minh họa) | Client action | Request minh họa theo [kiến thức BASE](TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md) |

**Workspace theo quyền:** menu Kinh doanh chỉ hiện với `group_demo_business`; dữ liệu mọi màn hình theo assignment/grant. Bộ chọn **Góc nhìn** trên dashboard (Điều hành · Dự án & kỹ thuật · Kinh doanh · Tài chính) chỉ sắp xếp lại bố cục và có nhãn “Chỉ đổi bố cục — quyền dữ liệu không đổi”; nó không đổi nhóm, không gọi backend với vai trò khác. Góc nhìn Kinh doanh chỉ có trong danh sách khi người xem thuộc `group_demo_business`.

**Nhãn môi trường:** mọi màn hình web client của DB demo có huy hiệu systray “Dữ liệu trình diễn”; mỗi màn hình minh họa có nhãn “Minh họa định hướng”; mã/tên dữ liệu mang dấu `DEMO`.

## 5. Kịch bản trình diễn (5–7 phút)

1. Đăng nhập `demo.lanhdao` → TP Dashboard: bản đồ phân hệ (thật/minh họa), KPI, chuỗi liên kết dự án, mục cần chú ý.
2. Bấm KPI “Công việc quá hạn” → danh sách native cùng bộ lọc → quay lại bằng breadcrumb.
3. Mở chuỗi `DEMO-CAU-01` → Tổng quan dự án: hợp đồng (review_state tách lifecycle_state), công việc, tài liệu, khảo sát/thiết kế minh họa.
4. TP Contracts → Luồng rà soát: draft → in_review → returned → rework; review_complete/BASE/ký/hiệu lực ở lớp riêng.
5. TP Finance: giá trị hợp đồng theo tiền tệ (Odoo), nghiệm thu/tiền thu (minh họa) tách cột, không cộng khác tiền tệ, không tính lãi.
6. CRM, Dự thầu, Đề nghị BASE (minh họa) — nhấn mạnh BASE vẫn là nơi duyệt.
7. Đăng xuất, đăng nhập `demo.kysu`: chỉ một dự án, không có menu Kinh doanh, không có số tiền/tệp tài chính; thử URL trực tiếp tới tệp tài chính → bị chặn.

Chi tiết lời dẫn ở [kịch bản trình diễn](../demo/UI_DEMO_001_PRESENTATION.md).

## 6. Màn hình

Trạng thái chung cho mọi client action: **loading** (khung xám có `aria-busy`), **empty** (câu giải thích + không có số 0 giả), **error** (thông điệp ngắn, nút “Tải lại”; lỗi quyền hiển thị “Không có quyền xem” thay vì trang trắng), **denied** (backend trả `AccessError` → thông báo Odoo; thẻ phân hệ không thuộc quyền hiển thị khóa, không có liên kết).

| Mã | Màn hình | Mục tiêu | Actor | Nguồn | Thật/minh họa | Trường cần grant tài chính |
| --- | --- | --- | --- | --- | --- | --- |
| A | TP Dashboard | Toàn cảnh, KPI bấm được, chuỗi dự án, mục cần chú ý | Cả hai | `search_count`/`search` theo quyền người xem trên project, task, revision, document, crm.lead | KPI thật từ fixture; không KPI vận hành hardcode | Không hiển thị tiền trên dashboard; số tài liệu tài chính chỉ đếm với project có grant |
| B | TP Projects | Danh sách/kanban/form; tổng quan giữ ngữ cảnh dự án | Cả hai | `project.project`, `project.task`, `tp.contract` | Thật | Không có trên view dự án |
| C | TP Survey | Kế hoạch, vị trí/hạng mục, nhân sự/thiết bị, nhật ký, kết quả | Cả hai | Backend demo, lọc theo dự án đọc được | Minh họa | Không |
| D | TP Design | Bộ bản vẽ, revision, ý kiến kiểm tra, gói bàn giao | Cả hai | Như trên | Minh họa; không duyệt/ký | Không |
| E | TP Contracts | Hợp đồng, phiên bản, luồng rà soát | Cả hai | `tp.contract`, `tp.contract.revision`, workflow CTR-002a đã chạy | Thật, chỉ đọc; không nút ghi/duyệt | Tab số tiền dòng (`tp.contract.line.amount`) do record rule lọc |
| F | TP Tasks | Kanban theo giai đoạn, hạn, người phụ trách | Cả hai | `project.task` | Thật, chỉ đọc; không timesheet/Gantt | Không |
| G | TP HR | Danh bạ; năng lực/phân bổ minh họa | Cả hai | `hr.employee.public`; backend demo | Danh bạ thật; phân bổ minh họa; không lương | Không |
| H | TP Finance | Giá trị hợp đồng thật; nghiệm thu/tiền thu minh họa | Cả hai | `_amount_summary()` theo người xem; backend demo | Hỗn hợp, ghi rõ từng cột | Toàn bộ số tiền; dự án không grant chỉ có dòng “Không có quyền xem số tiền” |
| I | TP Documents | Tệp hồ sơ theo general/financial | Cả hai | `tp.contract.document` | Thật (tệp giả) | Tệp `financial` |
| J | CRM | Pipeline cơ hội | `demo.lanhdao` | `crm.lead` | Thật (fixture) | Doanh thu kỳ vọng chỉ ở actor có `group_demo_business` |
| K | Đề nghị BASE | Danh sách, form mẫu, tiến trình Proposed-TP | Cả hai | Backend demo | Minh họa; không approve/connector/ký/chi | Số tiền đề nghị |
| L | Dự thầu | Gói thầu, hạn, hồ sơ, liên danh, kết quả dự kiến | `demo.lanhdao` | Backend demo | Minh họa; Tấn Phát là nhà thầu/tư vấn | Không trả giá dự thầu |

Liên kết “cơ hội ↔ dự án” trên dashboard là **liên kết minh họa theo cùng khách hàng** (`partner_id`), ghi rõ trên UI; không thêm field mới vào `crm.lead` hay `project.project`.

## 7. Thiết kế backend và bảo mật

- Addon `custom_addons/tp_demo_workspace/` chỉ thêm: nhóm demo, menu/action/view mới, một `AbstractModel` `tp.demo.workspace` làm projection đọc, assets web, test. Không thêm field/method vào model canonical, không sửa ACL/rule hiện có.
- Một ACL mới: `crm.lead` **chỉ đọc** cho `group_demo_business` (giới hạn company). Lý do: tránh cấp `sales_team.group_sale_salesman` (có quyền ghi) chỉ để trình diễn.
- Projection công khai (`get_dashboard`, `get_project_overview`, `get_contract_flow`, `get_showcase`, `get_finance`): kiểm `group_demo_viewer` (và `group_demo_business` cho Bid/CRM), đọc bằng ORM của chính người xem — record rule company/project/assignment/grant tự lọc. Không `sudo`, không SQL thô. DTO là danh sách khóa cho phép; tiền là chuỗi do Odoo định dạng theo currency, không có float.
- Dữ liệu minh họa nằm trong Python của addon (`demo_catalog.py`), gắn với mã dự án DEMO; backend chỉ trả các dòng của dự án mà người xem đọc được qua ORM, và chỉ kèm số tiền khi `tp_financial_read_granted` đúng. Không có dữ liệu tiền/tệp trong static JS/XML/JSON.
- View native cho model TP và CRM đặt `create="0" edit="0" delete="0"`; quyền thật vẫn do ACL/rule hiện có quyết định (actor demo vốn không ghi được project/task/contract TP).
- Workflow hợp đồng chỉ chạy qua `tp.contract.workflow._tp_run` với actor fixture có assignment/grant phòng ban. Một hợp đồng “đã ký/hiệu lực” được tạo theo đúng mẫu nhập legacy của seed dev CTR-001 (`review_complete` + `legacy_unverified`), ghi rõ là hồ sơ nhập ban đầu. Cũng như `seed_dev_contracts` trong `scripts/dev.py`, `lifecycle_state = 'effective'` của hồ sơ này do fixture gán (superuser, DB demo) và được constraint `_check_lifecycle_evidence` kiểm; đây là điểm cần coordinator xác nhận khi audit, không phải đường ghi của actor demo.
- Actor demo không có `base.group_allow_export`: Export của Odoo bị từ chối. Test chứng minh nếu cấp quyền export thì `export_data` vẫn chỉ trả dòng record rule cho phép. Tệp `financial` trả 404 qua `/web/content/<model>/<id>/file` và `/web/content/<attachment_id>` với người không có grant.
- Tính năng native không thuộc demo vẫn có mặt: chat chào mừng OdooBot, kênh chung, to-do riêng “Chào mừng” do `project_todo` tạo cho mỗi user mới (không có `project_id`, KPI không đếm).
- Menu app của actor demo có cả “TANPHAT ONE – Demo” (addon này) và “TANPHAT ONE” (`tp_core.menu_platform`, hiện vì nhóm demo kế thừa `tp_core.group_user` mà rule phạm vi dự án cần), cùng các app native từ dependency; “Ứng dụng” mở cho người dùng thường bởi `base_install_request` (chỉ gửi yêu cầu cài). Ngày 30/10/2026 người dùng chọn giữ nguyên menu; runbook và kịch bản trình bày ghi chỉ dùng app Demo.

## 8. Ngôn ngữ thiết kế

### Bảng màu (namespace `o_tp_demo_workspace`, biến SCSS, không ghi đè `:root`)

| Tên | Hex | Dùng cho |
| --- | --- | --- |
| Mực bản vẽ | `#17324F` → `#24557F` | Tiêu đề, số liệu, nét liền “dữ liệu Odoo”, focus ring; dải đầu trang dạng bản vẽ (gradient mực + lưới 24px) |
| Xanh chỉ dẫn | `#2F6DB3` | Hover/đang chọn (liên kết, dòng bảng, viền trái KPI) |
| Thép mạ | `#5A6A7B` | Chữ phụ, đường kẻ, nhãn cột |
| Giấy can | `#F2F5F9` | Nền màn hình client action |
| Vạch sơn | `#D99A1E` (chữ: `#8A5A00`) | Cần chú ý: quá hạn, bị trả lại; dải sọc nhãn “Dữ liệu trình diễn” |
| Cọc mốc | `#2E7D5B` | Nhãn “Dữ liệu Odoo”, trạng thái đã có kết quả |

Nền thẻ là trắng. Tương phản chữ ≥ 4.5:1 (Mực/Giấy can ≈ 12:1; Thép mạ/trắng ≈ 5.5:1; Xanh chỉ dẫn/trắng ≈ 5.3:1; `#8A5A00`/trắng ≈ 5.9:1; chữ trắng 80% trên dải mực ≥ 5.6:1).

### Chữ, khoảng cách, chuyển động

- Chữ thân: font hệ thống của Odoo (Segoe UI trên Windows, đủ dấu tiếng Việt). Số KPI/đếm: **Oswald** từ bản local `web/static/fonts/google/Oswald` (chỉ chữ số, không phụ thuộc CDN), `font-variant-numeric: tabular-nums`.
- Khoảng cách theo bậc 4px: 4 · 8 · 12 · 16 · 20 · 24 · 28. Bo góc 8px (thẻ con, chip) và 14px (panel, KPI, dải đầu trang); nhãn trạng thái dạng viên thuốc. Viền 1px, bóng hai lớp nhẹ, đậm hơn khi hover.
- Chuyển động: 180ms ease cho hover/focus (KPI và thẻ phân hệ nhấc 2px); KPI/panel dashboard hiện dần 320ms so le 40ms; nét nối chuỗi dự án vẽ trong 300ms. Tắt toàn bộ khi `prefers-reduced-motion: reduce`.
- Focus: viền 2px Mực bản vẽ, offset 2px, trên mọi phần tử bấm được (KPI, nút chuỗi, thẻ phân hệ, dòng bảng); trên dải đầu trang tối dùng viền trắng.

### Nguyên tắc

1. **Nét liền là dữ liệu thật, nét đứt là minh họa** — mượn quy ước bản vẽ kỹ thuật (nét đứt = phương án/ẩn). Thẻ, bảng và nhãn minh họa dùng viền đứt và huy hiệu “Minh họa định hướng”.
2. Mỗi con số bấm được để mở danh sách native cùng bộ lọc; không có số không truy được nguồn.
3. Không có số 0 giả: thiếu quyền hoặc thiếu dữ liệu ghi bằng chữ.
4. Chữ thường theo câu, không eyebrow viết hoa toàn bộ, không CTA mũi tên; bóng chỉ đủ tách lớp, không đổ bóng nặng.

Tự rà soát so với mặc định chung chung: tránh bộ thẻ SaaS đồng dạng (bản đồ phân hệ là các làn nghiệp vụ có đường kẻ, không lưới thẻ đều), tránh màu kem/đất nung; gradient chỉ dùng cho dải đầu trang dạng bản vẽ (mực + lưới), điểm nhấn ngữ cảnh công trường vẫn là dải sọc vạch sơn.

Làm mới giao diện ngày 30/10/2026 (CHG-20261030-003, theo yêu cầu người dùng “chỉnh lại giao diện cho đẹp hơn”): chỉ đổi SCSS trong `static/src/**` của addon, mọi selector vẫn trong namespace `.o_tp_demo`/`.o_tp_demo_badge`; không đổi template, JS, Python, ACL/rule hay dữ liệu. Ô “Góc nhìn” trên dải tối có nền trắng vì `.form-select` của Odoo 20 trong suốt; trên khổ ≤ 575px dải “Dữ liệu trình diễn” chuyển thành khối bo 8px để chữ xuống dòng gọn.

### Wireframe nội dung UI-DEMO-001 trước delta điều hướng

```text
TP Dashboard (1440 / 1366)
┌ Odoo navbar: TANPHAT ONE – Demo | TP Dashboard  TP Projects …            [Dữ liệu trình diễn] ┐
│ ▚▚ Dữ liệu trình diễn · không phải hồ sơ thật           Góc nhìn [Điều hành ▾] chỉ đổi bố cục │
│ TP Dashboard                                   DEMO Lãnh đạo điều hành · 3 dự án được giao   │
│ ┌ 3 ──────┐┌ 14 ─────┐┌ 3 ──────┐┌ 2 ──────┐┌ 7 ──────┐   (mỗi ô mở danh sách cùng lọc)     │
│ │Dự án    ││CV đang mở││CV quá hạn││HĐ đang rà││Tài liệu │                                     │
│ └─────────┘└─────────┘└─────────┘└─────────┘└─────────┘                                     │
│ Chuỗi liên kết dự án                                  │ Cần chú ý                            │
│ DEMO-CAU-01  Cơ hội ┄┄ Dự án ── HĐ 2 ── CV 6 ── TL 3   │ ▲ HĐ … bị trả lại: <lý do>          │
│ DEMO-DUONG-02 …                                       │ ▲ CV … quá hạn 4 ngày               │
│ Bản đồ TANPHAT ONE                                                                          │
│ Kinh doanh   │ CRM ▮ │ Dự thầu ┆ │ Đề nghị BASE ┆                                            │
│ Thực hiện    │ Projects ▮ │ Survey ┆ │ Design ┆ │ Tasks ▮                                     │
│ Hồ sơ        │ Contracts ▮ │ Documents ▮                                                    │
│ Nguồn lực    │ HR ▮/┆ │ Finance ▮/┆                       ▮ Dữ liệu Odoo  ┆ Minh họa          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

Tổng quan dự án                     Màn hình minh họa (Survey/Design/Request/Bid/HR)
┌ breadcrumb: TP Dashboard / DEMO-CAU-01 ┐   ┌ ┆Minh họa định hướng┆  Dự án [Tất cả ▾] Trạng thái [▾] [Tìm] ┐
│ Dự án [DEMO-CAU-01 ▾]  KH · Phòng · PM   │   │ Bảng danh sách (mã, tên, dự án, trạng thái) │ Chi tiết mẫu  │
│ Hợp đồng │ Công việc │ Tài liệu           │   │ dòng chọn được bằng bàn phím                │ các mục, nhật │
│ Khảo sát ┆ Thiết kế ┆ Cơ hội cùng KH ┆     │   │                                             │ ký, ngoài phạm│
└──────────────────────────────────────────┘   └─────────────────────────────────────────────────────────┘
```

Responsive: dưới 992px các làn và cột xếp dọc; bảng minh họa chuyển chi tiết xuống dưới danh sách; không cuộn ngang trang.

## 9. Dữ liệu fixture

Công ty `Công ty Trình diễn TANPHAT ONE (DEMO)`, tiền tệ VND. Năm phòng ban DEMO (KHKD, KS, TK, TCKT, HCNS); 3 dự án cầu/đường (`DEMO-CAU-01`, `DEMO-DUONG-02`, `DEMO-NUT-03`); 4 hợp đồng (draft, in_review, returned qua workflow; một hồ sơ nhập ban đầu đã ghi ký/hiệu lực); 20 công việc với giai đoạn và hạn (có quá hạn, chưa giao; ngoài ra 13 to-do riêng “Chào mừng” do `project_todo` tạo, không thuộc dự án); 10 cơ hội CRM; 12 nhân viên giả; tài liệu general/financial với nội dung văn bản giả. Mọi bản ghi được lưu external ID dưới module `tp_demo_seed` để seed lại không tạo trùng.

## 10. Kiểm thử

- Odoo tests (`/tp_demo_workspace`) trên DB test demo: seed hai lần không trùng; projection theo scope/grant; ORM, `read_group`, `export_data` của amount/tệp tài chính; tải tệp trực tiếp qua `/web/content`; ghi trực tiếp bị chặn; người không thuộc nhóm demo không gọi được projection.
- Unit test tooling (`scripts/tests/test_ui_demo.py`): từ chối DB dev/test và tên ngoài mẫu, owner lạ, cổng bận, PID không thuộc tool.
- Browser live UI-DEMO-001 (bằng chứng lịch sử CHG-002/003, thủ công qua trình duyệt tích hợp Claude desktop trên `127.0.0.1:18109`): đăng nhập hai actor, mọi menu, KPI → list, mở dự án/hợp đồng, actor không tiền, URL/tệp trực tiếp và RPC `call_kw` phủ định; 1440×900, 1366×768, 375×812; focus bàn phím và reduced motion; ảnh `.local/ui-demo-001/screenshots/`. UI-DEMO-002 bổ sung script Playwright live và HOOT, xem [bàn giao CHG-005](../demo/UI_DEMO_002_HANDOFF.md).

## 11. Ngoài phạm vi

Không ghi/duyệt hợp đồng từ UI demo, không review_complete/cancel, không BASE connector/approve/ký/hiệu lực/nghiệm thu/thanh toán, không invoice/payment/entry, không payroll, không Gantt/Enterprise/theme mua, không `survey`/`purchase_requisition`, không thay React/OpenAPI/API hiện hành, không cài lên DB dev/test, không cấp quyền người thật.
