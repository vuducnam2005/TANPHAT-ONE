# KD-UI-002 — Sidebar và hoàn thiện Tổng quan KH-KD

Ngày 06/11/2026, Asia/Saigon. Prompt: `docs/prompts/CLAUDE_KD_UI_002_SIDEBAR_POLISH.md` (CHG-20261106-018, mục 5A theo CHG-20261106-019). Phạm vi là giao diện native trong addon `tp_kd_workspace`. Không đổi workflow, state, công thức, quyền, dữ liệu, KD-NATIVE-001 audit, Q2/G7 hoặc pilot.

Đây **không chỉ là CSS**:

- Thêm helper báo cáo read-only bằng Python: `models/dashboard.py`, chạy bằng env user hiện tại.
- Thêm 5 menu nhóm cha và reparent các menu lá hiện hữu. Menu lá giữ XMLID và action.
- Thêm OWL client code: sidebar, controller Tổng quan, tùy chọn hiển thị.

## 1. Kiến trúc

| Lớp | File | Ghi chú |
| --- | --- | --- |
| Menu | `views/workspace.xml` | 5 nhóm cha không có action: Kinh doanh và dự án, Hợp đồng và triển khai, Sản lượng và kế hoạch, Thanh toán và hồ sơ, Báo cáo và quản trị. Menu lá giữ XMLID, action, groups và sequence tương đối. Tổng quan vẫn là lá gốc. |
| Sidebar | `static/src/sidebar/*` | Template inheritance `web.WebClient` thêm `TpKdSidebar` sau NavBar trong nhánh không-fullscreen; không thay WebClient. Component chỉ render khi app hiện tại có XMLID `tp_kd_workspace.menu_kd`. Khi render, nó gắn class `o_tp_kd_shell` lên `.o_web_client`, gỡ class khi unmount hoặc rời app. Cây menu lấy từ `menu` service đã lọc quyền; không RPC, không sudo, không hardcode ID. |
| Tổng quan | `static/src/overview/*` | `overview_form` có `js_class="tp_kd_overview"`. View registry đặt Controller riêng nên action/XMLID `action_overview` và deep link cũ giữ nguyên. Controller gọi các helper whitelisted qua `orm.call`. |
| Tùy chọn | `static/src/prefs.js` | localStorage key `tp_kd_ui:v1:<db>:<uid>`. Chỉ lưu `collapsed`, `density`, `motion`, `groups` (danh sách nhóm mở) và các khối Tổng quan đang mở. Validate từng giá trị; storage lỗi thì dùng mặc định. |
| List/form | `static/src/kd.scss` | Chỉ scope dưới `.o_tp_kd_shell`, `.tp_kd_dossier`, `.o_tp_kd_list` và `.o_tp_kd_overview`. Không style `.btn`, `.modal`, `.o_form_view` toàn cục. |

### Active menu

Cách xác định:

1. Lấy `actionStack[0].action` của router.
2. Tìm các lá KH-KD có cùng action.
3. Nếu nhiều lá cùng action (Tổng quan và Báo cáo cùng `action_overview`), ưu tiên lá được bấm gần nhất. Lá này lưu ở `sessionStorage['tp_kd_ui:last_leaf']`, chỉ là ID menu.
4. Nếu không có lá nào được bấm, fallback về lá có sequence nhỏ nhất, tức Tổng quan.

Cập nhật khi có `ACTION_MANAGER:UI-UPDATED`, nên cover cả click, smart button, Back/Forward và refresh. Nhóm cha của lá active tự mở; bấm nhóm chỉ đổi trạng thái mở/đóng, không điều hướng.

### Điều hướng

Mỗi lá là `<a href="/odoo/<actionPath|action-ID>">`, có `aria-current="page"` khi active. Click thường gọi `menu.selectMenu(menu)` (native: clearBreadcrumbs, cảnh báo form chưa lưu). Ctrl/Cmd/Shift/middle-click để trình duyệt mở tab mới. Không dùng `window.location`.

### Layout

| Bề rộng | Hiển thị |
| --- | --- |
| ≥1200px | `.o_web_client` dùng grid: navbar ở hàng 1 kéo hết chiều ngang; sidebar ở cột 1, rộng 264px, hoặc 68px khi thu gọn; `.o_action_manager` ở cột 2. `.o-main-components-container` nằm ngoài luồng. |
| 768–1199px | Mặc định rail 68px. Mở rộng sẽ thành drawer overlay. |
| <768px | Sidebar ẩn. Navbar có nút "Menu KH-KD". |

Drawer overlay:

- Có backdrop.
- Đóng bằng Escape, nút X, bấm backdrop hoặc khi điều hướng thành công.
- Focus trap bằng keydown Tab trong drawer.
- Đóng thì trả focus về nút mở.

Khi sidebar đang mount, menu section native của navbar KH-KD bị ẩn để không lặp. Rời app thì menu native trở lại bình thường.

## 2. Hướng thẩm mỹ

Công cụ điều hành dự án cầu đường: sạch, rõ, mật độ vừa phải. Điểm nhấn là sidebar xanh than và vùng "Việc của tôi". Không dùng hero, gradient toàn trang hay count-up.

- **Màu:**
  - Sidebar `#17324D`; mục active nền `#22476A`, vạch trái `#7FB3D5`.
  - Nền `#F4F6F8`, surface `#FFFFFF`, viền `#D9E2EC`.
  - Action `#255F85`, cảnh báo `#B45309`, trả lại `#A12A35`, hoàn thành `#2F7D4F`.
- **Màu trạng thái dùng thống nhất ở biểu đồ, bảng và badge:**
  - Nháp: xám xanh `#8A9BB0`.
  - Đang rà soát: xanh `#255F85`.
  - Bị trả lại: đỏ gạch `#A12A35`.
- **Chữ:** font hệ thống Odoo. Tiêu đề 24px, khối 16px, nội dung 14px. Số tabular-nums, căn phải trong bảng.
- **Nhịp:** khoảng cách 8/12/16/24px, bo góc 8px, shadow rất nhẹ.
- **Chuyển động:**
  - Submenu 180ms. Sidebar 200ms, chỉ animate width.
  - Chevron xoay.
  - Hover đổi nền và viền nhẹ; `:focus-visible` có viền 2px.
  - Tắt chuyển động khi `prefers-reduced-motion: reduce` hoặc khi user chọn "Giảm chuyển động".

## 3. Bố cục Tổng quan

```text
[Tổng quan KH-KD · Cập nhật hh:mm]           [Tạo hồ sơ ▾] [Làm mới] [Xóa bộ lọc] [Xem dữ liệu ▾] [⚙]
[Dự án ▾] [Người phụ trách ▾] [Từ ngày] [Đến ngày]
[Chờ tôi rà soát][Trả lại cho tôi][Quá hạn của tôi][Đến hạn ≤3 ngày của tôi][Hợp đồng · phiên bản][Dự án]
[G01 Tình trạng hồ sơ nội bộ — thanh ngang xếp chồng, 7 nhóm + tổng]
[G02 Công việc theo dự án               ][G03 Cơ hội / hồ sơ thầu        ]
[Tab chi tiết: G04 Kế hoạch sản lượng theo kỳ | G05 Hạn năng lực/chứng chỉ]  (tải khi mở)
[Bảng điều hành dự án: tìm, sắp xếp, phân trang, chọn cột, thao tác dòng]
[Việc của tôi: Chờ tôi rà soát | Bị trả lại | Đến/quá hạn — có tổng thật, phân trang]
[Bảng nguồn hồ sơ (đủ thông tin bảng cũ) — khối mở rộng; mở sẵn khi vào từ menu Báo cáo KH-KD]
```

Biểu đồ được vẽ bằng HTML/CSS từ số server trả về. Mỗi phần tử là `<button>` có aria-label đầy đủ, tooltip khi hover/focus và bấm để mở nguồn. Không dùng thư viện ngoài, canvas hay CDN. Bề rộng thanh chỉ là trình bày; số hiển thị là count/tiền do server format.

## 4. Metric catalog

Ký hiệu:

- `D(model, date_field)` là `tp.kd.overview._domain` với bộ lọc người dùng. Dự án được lấy bằng `project.project.search([('tp_managed','=',True)])` trong env user, cộng owner nếu có chọn, cộng ngày nếu có chọn.
- `I(model, query)` là `_inbox_domain` hiện có.
- Mọi count dùng `search_count` hoặc `_read_group` trong env user, với cùng record rules như list nguồn.
- Đơn vị là **số hồ sơ**, trừ G04.

| ID | Tiêu đề | Model | Domain / grain | date_field | Quyền | Công thức | Drilldown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K1 | Chờ tôi rà soát | 7 model typed + `tp.contract.revision` | `I(m,'review')`, mỗi (model,id) một dòng | theo `I` | rule model + grant `review` cho dự án đủ điều kiện | Σ count từng nguồn. Đây là tổng dòng của tab "Việc của tôi", không cộng tiền. | Tab Việc của tôi → Chờ tôi rà soát |
| K2 | Trả lại cho tôi | 7 typed + revision | `I(m,'returned')` | theo `I` | rule | như K1 | Tab Bị trả lại |
| K3 | Quá hạn của tôi | 7 typed (trừ plan) + task + lead | `I(m,'overdue')` + owner = tôi (`owner_id` / `user_ids` / `user_id`) | `date_due` / `date_deadline` / `kd_deadline` | rule | Σ count. Có thể giao với K1 và K2, nên không cộng K1–K4 với nhau. | Tab Đến/quá hạn |
| K4 | Đến hạn ≤3 ngày của tôi | như K3 | `I(m,'due')` + owner = tôi; khoảng [hôm nay, hôm nay+4) | như K3 | rule | Σ count | Tab Đến/quá hạn |
| K5 | Hợp đồng · phiên bản | `tp.contract`, `tp.contract.revision` | `action_contracts` domain; `I(revision,'all')` | không có / `recorded_at` | rule TP Contracts | Hai số riêng; phụ lục là phiên bản, không thành hợp đồng mới. | `action_contracts` / nguồn phiên bản |
| K6 | Dự án | `project.project` | `tp_managed` (+ dự án chọn) | — | rule | count | `action_projects` |
| G01 | Tình trạng hồ sơ nội bộ | 7 typed | `I(m,'all')` + `state ∈ {draft, in_review, returned}` | `date` (plan: `period_from`; credential: `valid_to`) | rule model | 3 phần rời nhau, mỗi record hiện hành 1 lần. Tổng = Σ (model,id). Không đếm event/submission, không phải % tiến độ. | `I(m,'all') + state` |
| G02 | Công việc theo dự án | `project.task` | `D(task, date_deadline)`, owner = `user_ids`, nhóm theo project | `date_deadline` | rule task | Hoàn thành = `is_closed`. Quá hạn = mở và `date_deadline < hôm nay`. Còn lại = mở khác, gồm việc không có hạn. 3 nhóm rời nhau. Mặc định hiện top 8 theo (quá hạn, mở); có nút xem toàn bộ. | task theo dự án + nhóm |
| G03 | Cơ hội / hồ sơ thầu | `crm.lead` | `D(lead,'kd_deadline')`, owner = `user_id`; nhóm `kd_route` × `kd_bid_state` | `kd_deadline` | rule CRM | Đấu thầu: Tìm hiểu / Chuẩn bị / Đã khai báo nộp (chưa xác minh). Giao trực tiếp đếm riêng. Không phải trúng thầu hay doanh thu. | lead theo route + state |
| G04 | Kế hoạch sản lượng và số đã gửi rà soát | `tp.periodic.plan` + `.amount` (measure=production) | `D(plan,'period_from')` + `period_kind` (mặc định month), 12 kỳ gần nhất | `period_from` | record readable **và** `_kd_money_allowed()`; plan không đủ quyền bị loại khỏi tập, chỉ báo số lượng | Mục tiêu chỉ hiện khi `amount_state=confirmed`. Nguồn = `source_value` chỉ khi `source_status=comparable`; còn lại hiện khoảng trống kèm nhãn trạng thái, không vẽ 0. % chỉ khi mục tiêu > 0. Không cộng tháng/quý/năm. Doanh thu kế hoạch không vẽ. | form plan / `action_source_productions` |
| G05 | Hạn năng lực / chứng chỉ | `tp.credential` | `D(cred,'valid_to')` | `valid_to`, so với ngày theo tz user | rule | Đã hết hạn: `< hôm nay`. Trong 30 ngày: `[hôm nay, hôm nay+30]`. Sau 30 ngày: `> hôm nay+30`. `valid_to` bắt buộc nên không có nhóm "chưa có ngày". Ngưỡng minh họa, không xác minh pháp lý. | credential theo nhóm |
| T1 | Bảng điều hành dự án | `project.project` | `tp_managed` (+ dự án chọn), tìm theo mã/tên/khách hàng | — | rule | Cột Công việc mở/quá hạn dùng grain G02. Cột Hồ sơ chờ tôi/trả lại dùng K1/K2 theo dự án. Sort server whitelist: name, tp_code, partner, user, kd_deadline. Có phân trang. | form dự án; task theo nhóm; Việc của tôi lọc dự án |
| W1 | Việc của tôi | như K1/K2/K3+K4 | Trộn theo hạn hoặc ngày; mỗi dòng giữ (model,id) | — | rule | Tổng là tổng count thật từng nguồn, không lấy độ dài trang. | form record đúng model |
| S1 | Bảng nguồn hồ sơ | 10 nguồn `SOURCES` × all/review/returned/overdue/due + 3 chỉ số phụ | `I(m,q)` | theo `I` | rule | Giữ đủ thông tin bảng cũ. Overdue/due ở đây là **theo phạm vi**, khác K3/K4 là "của tôi". | `action_inbox` tương đương |

Lọc ngày khác nhau theo model: hồ sơ typed lọc theo `date`, plan theo `period_from`, chứng chỉ theo `valid_to`, task theo `date_deadline`, cơ hội theo `kd_deadline`. Tooltip của bộ lọc nêu rõ điều này.

## 5. Helper backend (`models/dashboard.py`)

Tất cả đều là `@api.model` trên `tp.kd.overview`, chạy bằng env user hiện tại.

- Filter được whitelist: `project_id` (int, phải nằm trong `search` dự án của user), `owner_id` (int, `res.users` đọc được), `date_from`/`date_to` (ISO date).
- Sau khi validate, dựng record ảo `self.new()` để tái dùng `_domain` và `_inbox_domain`. Không ghi DB.
- Client không gửi model, field hay domain. Drilldown nhận `key` trong whitelist kèm tham số enum hoặc int; server dựng domain và trả act_window qua `open_records` hoặc action hiện có.

| Helper | Trả về |
| --- | --- |
| `get_kd_dashboard(filters)` | meta, tùy chọn lọc, KPI, G01, G02, G03, danh sách loại hồ sơ được tạo |
| `get_kd_plan_compare(filters, period_kind)` | G04, tải khi mở tab |
| `get_kd_credential_expiry(filters)` | G05, tải khi mở tab |
| `get_kd_source_table(filters)` | S1, tải khi mở khối |
| `get_kd_project_rows(filters, search, order, offset, limit)` | T1, limit ≤ 50 |
| `get_kd_my_work(filters, tab, offset, limit)` | W1 |
| `action_kd_open(key, filters, params)` | act_window cho drilldown |
| `action_kd_create(kind, project_id)` | form/wizard chuẩn có default dự án. Hợp đồng dùng `tp_contract.action_native_draft`. Backend create vẫn kiểm grant. |

## 6. Toolbar

- **Tạo hồ sơ ▾** là action chính duy nhất. Chỉ liệt kê loại user được phép:
  - 7 typed: `get_kd_ui_permissions().create`.
  - Hợp đồng: `contract_draft_edit`.
  - Cơ hội: grant opportunity prepare.
  - Công việc: `tp_core.group_manager`.
- **Làm mới**, **Xóa bộ lọc**, **Xem dữ liệu ▾**: mở list nguồn native, nơi xuất dữ liệu dùng export native có guard. Không có nút xuất giả.
- **⚙ Tùy chọn hiển thị**.
- Mỗi lần đổi filter hoặc refresh tăng request id; kết quả cũ bị bỏ.
- Lỗi refresh giữ số cũ, gắn nhãn "Dữ liệu có thể đã cũ" và có nút Thử lại. Không tự retry.

## 6A. Điều chỉnh sau kiểm thử clone

- **Quyền đọc từng nguồn:** `get_kd_dashboard` trả `readable` (theo nguồn và theo list) và `project_actions` đã lọc quyền đọc. Mỗi dòng G01, G02, G03, G04, G05 có `available`. Nút, đoạn biểu đồ và mục "Xem dữ liệu" của nguồn user không đọc được thì không hiện; khối biểu đồ hiện "Bạn chưa có quyền xem nguồn này" thay vì bấm ra lỗi. Ví dụ: reviewer không có quyền CRM nên G03 hiện thông báo này.
- **Thao tác dòng trong bảng dự án:** gồm "Mở hồ sơ dự án" cộng các `action_kd_*` hiện có trên `project.project` (cơ hội, hợp đồng, kế hoạch/WBS, giao khoán, sản lượng, nghiệm thu, đề nghị thanh toán, kế hoạch định kỳ, nghĩa vụ). Mỗi nút gọi đúng method backend đã kiểm quyền; không dựng domain ở client.
- **Act_window từ `orm.call`:** chỉ `/web/dataset/call_button` chạy `clean_action` sinh `views` từ `view_mode`. Controller Tổng quan có `withViews()` làm cùng phép suy ra đó trước `doAction`, nên drilldown mở cùng list/form native. Hàm này không thay domain/context.
- **Bố cục:** "Việc của tôi" chỉ nằm cạnh bảng dự án khi màn hình ≥1760px. Dưới mức đó hai khối xếp dọc để bảng dự án đủ cột mã/tên mà không cuộn ngang. Root controller nhận `props.className` (`o_action`) như view native.
- **Hành vi native được giữ:** form mới có thay đổi, bấm lá sidebar thì Odoo vẫn thử lưu. Thiếu trường bắt buộc thì giữ form và báo "Missing required fields"; không mất dữ liệu đã nhập.

## 7. Giới hạn

- G04 chỉ có giá trị khi dữ liệu có cặp confirmed và comparable. Dataset tổng hợp hiện chủ yếu là chưa xác nhận, nên biểu đồ sẽ hiện "Chưa đủ căn cứ so sánh" một cách trung thực.
- Dữ liệu là bộ tổng hợp 254 hồ sơ cộng 14 hồ sơ UI. Nhãn sản lượng tự khai, rà soát nội bộ và ngưỡng minh họa được giữ.
- Không xuất báo cáo tổng hợp, không batch action, không duyệt, ký hay chi tiền.
- Section menu native trên navbar bị ẩn trong KH-KD (sidebar thay thế). Probe trình duyệt cũ của KD-NATIVE-001 nếu bấm qua section menu navbar cần đổi sang lá sidebar hoặc deep link action; XMLID/action không đổi.
