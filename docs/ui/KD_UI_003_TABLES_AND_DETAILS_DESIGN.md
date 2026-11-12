# KD-UI-003 — Bảng có đường kẻ và màn hình chi tiết theo nghiệp vụ KH-KD

Ngày 06/11/2026, Asia/Saigon. Prompt: `docs/prompts/CLAUDE_KD_UI_003_TABLES_AND_DETAILS.md` (CHG-20261106-021). Change triển khai: CHG-20261106-022. Baseline: CHG-20261106-020, `tp_kd_workspace` 20.0.1.1.0, KD-UI-002 IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT.

Phạm vi là trình bày native Odoo trong `tp_kd_workspace`: XML view/inheritance, SCSS có scope, OWL nhỏ cho toolbar bảng và sidebar. Không đổi model, field, công thức, ACL/record rule/capability, state/transition, API/report backend, dữ liệu, TASK-001 hay TP Contracts workflow. Không cài React/antd.

Thay đổi Python duy nhất: action helper KH-KD thêm view id KH-KD và context `tp_kd_leaf` (chỉ để tô sidebar). Không đổi domain, quyền hay dữ liệu trả về.

## 1. Phản hồi thiết kế từ hai ảnh của người dùng

Ảnh không được đưa vào repository. Phiên này đọc chúng qua mô tả trong prompt và tái hiện trên clone bằng ảnh "trước". Tên/mã trong ảnh là dữ liệu mẫu, không phải lỗi dữ liệu cần sửa.

| Quan sát | Nguyên nhân trong source | Hướng xử lý |
| --- | --- | --- |
| Bảng dày, khó phân biệt cột | List native chỉ có đường ngang mảnh, header trong suốt, không kẻ dọc | Bordered table: kẻ ngang và dọc 1px `#D9E2EC`, header nền `#EEF3F8`, viền ngoài bo 8px |
| Nhiều dấu ba chấm | Mọi `td` native dùng `text-truncate`; Odoo 20 không còn tooltip trên ô | Cột nhận diện (tên, dự án, khách hàng) xuống dòng; min-width theo nghiệp vụ; cột phụ dài chuyển sang tùy chọn |
| Header bị cắt, ví dụ "Chịu trách nhiệm ..." | Nhãn `th` là `span.text-truncate` | Trong scope KH-KD, nhãn header được xuống dòng; min-width đủ cho nhãn |
| Trạng thái bị cắt, ví dụ "Đang th..." | Badge trong ô hẹp, chiều rộng tự tính | Cột trạng thái min 130–180px; badge được xuống dòng, không cắt |
| Form thiếu phân vùng, khoảng trắng lớn | Hai group không tiêu đề; Năng lực sử dụng là group tag ngắn đặt cuối sheet; trường phụ nằm rải trong tab | Hai khối có tiêu đề (căn cứ / phụ trách), khối nghiệp vụ riêng, notebook theo nghiệp vụ, sheet rộng hơn |
| Mở Cơ hội nhưng sidebar tô Tổng quan | Action mở từ Tổng quan không có `id`; `syncActive` không khớp nên giữ lá cũ | Context `tp_kd_leaf` từ action helper KH-KD (mục 8) |

## 2. Inventory: menu → action → model → view → controller

Quyền đọc/ghi do ACL, record rule và capability backend quyết định. Không có thay đổi quyền.

| Lá sidebar (XMLID `tp_kd_workspace.*`) | Action | Model | List | Form | Controller | Bảng con / dialog |
| --- | --- | --- | --- | --- | --- | --- |
| `menu_overview`, `menu_reports` | `action_overview` | `tp.kd.overview` | — | `overview_form` | `tp_kd_overview` (OWL) | Bảng dự án, Việc của tôi, bảng nguồn |
| `menu_opportunities` | `action_opportunities` | `crm.lead` | `opportunity_list` | `opportunity_form` + `opportunity_credentials` | List thường → `tp_kd_table`; form native | many2many năng lực |
| `menu_projects` | `action_projects` | `project.project` | mặc định `project.view_project` → mới `kd_project_list` (primary inherit) | `project_form` | `project_project_list` → `tp_kd_project_list` (kế thừa) | `tp_assignment_ids` (chỉ manager) |
| `menu_contracts` | `tp_contract.action_tp_contracts` (server) | `tp.contract` | `tp_contract.view_contract_list` | `view_contract_form` | native | `revision_ids`; revision form: `line_ids`, `submission_ids`, `approval_reference_ids`; 5 wizard |
| `menu_tasks` | `action_tasks` | `project.task` | `kd_task_list` | `kd_task_form` | `tp_kd_list` / `tp_kd_review_form` | smart button Công việc con |
| `menu_allocations` | `action_allocations` | `tp.allocation` | `allocation_list` | `allocation_form` | `tp_kd_list` / `tp_kd_review_form` | `amount_ids`, `child_ids`, `event_ids`, wizard `tp.kd.transition` |
| `menu_productions` | `action_productions` | `tp.production` | list | form | như trên | `amount_ids`, `event_ids` |
| `menu_acceptances` | `action_acceptances` | `tp.acceptance` | list | form | như trên | `amount_ids`, `event_ids` |
| `menu_payments` | `action_payments` | `tp.payment.request` | list | form | như trên | `amount_ids`, `event_ids` |
| `menu_plans` | `action_plans` | `tp.periodic.plan` | list | form | như trên | `amount_ids` (có `source_value`), `event_ids` |
| `menu_credentials` | `action_credentials` | `tp.credential` | list | form | như trên | `event_ids` |
| `menu_obligations` | `action_obligations` | `tp.obligation` | list | form | như trên | `event_ids` |

Đường mở phụ, đi cùng view ở trên:

- Smart button ở `project_form`: `action_kd_<loại>`.
- Tổng quan qua `get_kd_action`, `action_kd_open` và `action_kd_create`.
- Nút nguồn trong dossier: `action_allocation`, `action_production`, `action_acceptance`, `action_project`, `action_source_productions`, `action_used_opportunities`.
- Phiên bản hợp đồng: `tp.contract.revision` qua `view_revision_list` / `view_revision_form`.

Ngoài phạm vi, giữ nguyên: CRM/Project/Finance native ngoài app, Home, wizard của module khác. `overview_inbox` (`reporting.xml`) là arch cũ không còn render vì `js_class` đã thay renderer; bảng nguồn mới nằm trong OWL.

## 3. Token

| Token | Giá trị | Dùng cho |
| --- | --- | --- |
| `--tp-kd-bg` | `#F4F6F8` | nền vùng nội dung |
| `--tp-kd-surface` | `#FFFFFF` | mặt bảng, sheet |
| `--tp-kd-head` | `#EEF3F8` | header bảng |
| `--tp-kd-line` | `#D9E2EC` | đường kẻ ô, viền ngoài, phân cách section |
| `--tp-kd-ink` | `#1F2937` | chữ chính |
| `--tp-kd-muted` | `#52677D` | label, chú thích |
| `--tp-kd-action` | `#255F85` | link/nút chính, focus |
| `--tp-kd-zebra` | `#FAFBFD` | dòng chẵn |
| `--tp-kd-hover` | `#EEF5FB` | hover dòng |
| `--tp-kd-selected` | `#DCEBF7` | dòng chọn, kèm checkbox |
| Bo góc | 8px ngoài bảng/sheet | không bo từng ô |
| Chữ | header 13px semibold; thân 14px; label form 13px; field 14px; tiêu đề form 24px | font hệ thống Odoo |
| Padding ô | Dễ đọc 11px 12px (dòng 44–52px); Gọn 7px 12px (36–40px) | không ép height cố định |
| Spacing | 8/12/16/24px | section form |
| Chuyển động | hover 120ms nền; không animate dòng; tắt khi reduced-motion | |

## 4. Quy tắc bảng chung và cơ chế

### 4.1 Gắn scope

| Đối tượng | Hook | Selector |
| --- | --- | --- |
| List chính KH-KD | `<list class="tp_kd_table">` → class trên root view | `body.o_tp_kd_shell .o_list_view.tp_kd_table` |
| Form KH-KD (cả wizard/dialog) | `<form class="tp_kd_form">` | `body.o_tp_kd_shell .o_form_view.tp_kd_form` |
| Bảng con | x2many trong form có `tp_kd_form` | `… .tp_kd_form .o_field_x2many .o_list_table` |
| Cột xuống dòng | `<field class="tp_kd_wrap">` → class trên `td` khi dùng formatter | `… td.tp_kd_wrap` |
| Bảng OWL Tổng quan | `table.o_tp_kd_table` | `.o_tp_kd_overview .o_tp_kd_table` |

Không selector nào nhắm `.o_list_view`, `.o_form_view`, `.modal`, `.btn` hay `.table` toàn cục. Không dùng nth-child, không dùng ID số.

Dialog chỉ được style khi form bên trong có `tp_kd_form`. Wizard TP Contracts mở từ app TP Contracts không có body class, nên không đổi. Mở từ KH-KD thì cùng chuẩn.

Class thêm vào view của `tp_contract` là inert ngoài KH-KD vì mọi rule cần cả body class.

### 4.2 Đường kẻ, header, dòng

- `border-collapse: separate; border-spacing: 0`.
- Viền ngoài 1px, bo 8px; header/ô kẻ phải và dưới 1px.
- Không kẻ lên ô checkbox, filler, resize handle hoặc ô "Thêm dòng".
- Header `th` nền `#EEF3F8`, 13px semibold. Nhãn được xuống dòng (`white-space: normal`), icon sort giữ vị trí native.
- Sticky header native trong `.o_list_renderer`. Không đổi container cuộn, nên cuộn ngang ở trong bảng.
- Dòng zebra nhẹ, hover xanh nhạt, selected `#DCEBF7` kèm checkbox. Màu không là tín hiệu duy nhất vì badge/nhãn vẫn có chữ.
- Số căn phải `tabular-nums` (native `o_list_number`). Ngày theo formatter native và múi giờ người dùng.

### 4.3 Bề rộng và xuống dòng

Dùng thuộc tính `width="[min,max]"` native, parse bởi `parseWidthAttribute`. Thiếu chỗ thì `.o_list_renderer` cuộn ngang; trang không cuộn ngang. Resize bằng kéo mép header là native và chỉ giữ trong phiên. Double-click mép header trả về bề rộng tính lại.

Cột nhận diện có `class="tp_kd_wrap"` và xuống dòng không cắt chữ. Với min-width 260–360px, tên thông thường nằm trong 1–2 dòng; tên rất dài được hiện đủ và dòng cao hơn. Không clamp để tránh mất chữ trên mobile.

Đường đọc đầy đủ bằng chuột, bàn phím (mũi tên + Enter) và cảm ứng: bấm dòng để mở form native.

Badge trạng thái được xuống dòng trong ô; cột trạng thái min 130–180px.

### 4.4 Chọn cột, mật độ, khôi phục

- **Chọn cột:** dropdown tùy chọn cột native (biểu tượng điều chỉnh ở cuối header). Cột phụ dài để `optional="hide"`. Native lưu localStorage `optional_fields,<model>,list,<viewId>,…`. View KH-KD là view riêng nên không đè cấu hình CRM/Project.
- **Mật độ:** toolbar list KH-KD có nhóm "Thoáng | Gọn". Ghi vào `kdPrefs.density`, cùng nguồn với ⚙ sidebar, nên không có hai nơi lưu đánh nhau.
- **Khôi phục cột:** nút "Khôi phục cột" chỉ xóa key `optional_fields,<model>,list,<viewId>,` của view đang mở, rồi đặt lại tùy chọn theo `optional` của arch.
- **Khôi phục mặc định** ở ⚙ sidebar xóa key KH-KD và các key cột của view KH-KD đã đăng ký trong phiên. Không đụng storage app khác.
- Toolbar được thêm bằng template `t-inherit-mode="primary"` của `web.ListView`. Chỉ controller KH-KD dùng (`tp_kd_list`, `tp_kd_table`, `tp_kd_project_list`). Không patch `ListController` toàn cục.
- Ngoại lệ: list TP Contracts dùng view và action của `tp_contract`, nên không gắn controller KH-KD. Mật độ đổi qua ⚙ sidebar vẫn áp vì CSS theo body class.

### 4.5 Phân trang và thao tác

- `limit="20"` trên list chính KH-KD; arch thắng limit của action (`archInfo.limit || props.limit`).
- Server-side, pager native. Tổng lấy theo domain/quyền. x2many giữ pager native.
- Search, filter, group by, sort, export (theo `base.group_allow_export`) và selection giữ native.
- Không thêm xóa/nhân bản. `KdListController` vẫn tắt delete/duplicate và chặn create theo `get_kd_ui_permissions`.
- Mỗi dòng: bấm để mở. Hành động phụ có sẵn duy nhất là nút "View Tasks" của list dự án native, được giữ.
- Không tổng tiền phía frontend. List không có cột tiền vì tiền chỉ nằm ở `amount_ids` theo quyền.

## 5. Wireframe

### List

```text
┌ breadcrumb: Công việc / WBS ─────────────────────────────────────────────────────────┐
│ [Mới]            [🔍 Tìm kiếm… ▾ Bộ lọc/Nhóm]          [Thoáng|Gọn] [↺ cột]  1-20/57 ‹ › │
├──────────────────────────────────────────────────────────────────────────────────────┤
│☐│ Công việc (280–360, wrap)  │ Dự án (240–320, wrap) │ Chịu trách    │ Thời hạn │ Trạng │⚙│
│ │                            │                       │ nhiệm chính   │          │ thái  │ │
├─┼────────────────────────────┼───────────────────────┼───────────────┼──────────┼───────┤ │
│☐│ Khảo sát địa chất trụ T3   │ Cầu Nam Phong – gói 2 │ Nguyễn Văn A  │ 12/11 …  │[Đang  │ │
│ │ và lập báo cáo bổ sung     │                       │               │          │ thực  │ │
│ │                            │                       │               │          │ hiện] │ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Mobile (<768px) giữ cùng bảng với cột chính, cuộn ngang trong vùng bảng; control panel native thu gọn.

### Chi tiết

```text
┌ breadcrumb: Công việc / WBS / Khảo sát địa chất… ─────── [Lưu][Bỏ]  ‹ 3/57 › ┐
│ [header: nút nghiệp vụ theo quyền]                   [statusbar trạng thái]     │
│ ┌ sheet rộng tối đa 1280px ──────────────────────────────── [smart buttons] ┐ │
│ │ Mã · TÊN HỒ SƠ (24px)                                                       │ │
│ │ ── Căn cứ và dự án ──────────────    ── Phụ trách và hạn ─────────────     │ │
│ │ Dự án        …                        Người phụ trách  …                    │ │
│ │ Hợp đồng     …                        Hạn xử lý        …                    │ │
│ │ ── Khối nghiệp vụ (vd. Nguồn và kỳ) ────────────────────────────────────── │ │
│ │ [Phạm vi / đầu ra] [Giá trị minh họa*] [Lịch sử lần trình]   *theo quyền    │ │
│ │ ┌ bảng con có kẻ ───────────────────────────────────────────────────────┐  │ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 6. Ma trận từng màn

Ký hiệu:

- **S** = hiện mặc định; **O** = tùy chọn, ẩn mặc định.
- **W** = `tp_kd_wrap`; số trong ngoặc là `width="[min,max]"`.
- Mọi list chính: `class="tp_kd_table" limit="20"`.
- Mọi form: `class="tp_kd_form"`.
- Không field/nút/thuộc tính quyền nào bị bỏ. Chỉ thêm thuộc tính trình bày: `class`, `width`, `optional`, `string` của group/page, `nolabel`, `colspan`.

### A. Cơ hội và hồ sơ thầu (`crm.lead`)

**List** `opportunity_list` (js_class `tp_kd_table`):

| Cột | Field | Hiển thị | Bề rộng |
| --- | --- | --- | --- |
| Cơ hội | `name` | S, W | [280,360] |
| Khách hàng / chủ đầu tư | `partner_id` | S, W | [200,280] |
| Dự án liên quan | `tp_project_id` | S, W | [220,300] |
| Người phụ trách | `user_id` | S | [150,200] |
| Hình thức | `kd_route` | S | [120,160] |
| Tình trạng hồ sơ | `kd_bid_state` | S, W | [170,230] |
| Hạn chuẩn bị / nộp | `kd_deadline` | S | native |
| Nguồn thông tin | `kd_source` | O, W | [200] |
| Phạm vi / gói thầu | `kd_scope` | O, text | [240] |

**Form** `opportunity_form`:

- Header giữ `action_kd_prepare` và `action_kd_record_submission` cùng điều kiện, statusbar `kd_bid_state`. Nhãn "Đã khai báo nộp — chưa xác minh" giữ nguyên.
- Tiêu đề: tên.
- Hai khối:
  - "Khách hàng và dự án": `partner_id`, `tp_project_id`, `kd_source`, `company_id` (ẩn), `type` (ẩn).
  - "Phụ trách và kế hoạch": `user_id`, `kd_route`, `kd_deadline`.
- Notebook:
  - "Phạm vi / gói thầu": `kd_scope`.
  - "Checklist hồ sơ": `kd_checklist`, `kd_receipt`, ghi chú không phải trúng thầu.
  - "Năng lực sử dụng": `kd_credential_ids` many2many_tags, cùng domain/options. Chuyển từ group cuối sheet vào page, nên không còn vùng trắng cao.

### B. Hồ sơ dự án (`project.project`, domain `tp_managed`)

**List** `kd_project_list`:

- Primary inherit `project.view_project`, js_class `tp_kd_project_list` kế thừa `project_project_list`, giữ guard duplicate/archive và template dropdown.
- Mặc định: `tp_code` "Mã dự án" [110,150] → `name` W [260,360] → `partner_id` W [200,280] → `tp_department_id` [180,240] → `user_id` [160,200] → `kd_deadline` native.
- Tùy chọn: `company_id`, `stage_id`, `last_update_status`, `date_start`, `tag_ids`, các cột milestone native.
- Giữ nút dòng "View Tasks" native. Không thêm % hoàn thành.

**Form** `project_form`:

- Smart buttons gọn: 3 nút KH-KD + 7 nút dossier, chỉ hiện theo group/quyền như hiện tại, tràn sẽ vào "Thêm" native.
- Tiêu đề: tên.
- Hai khối:
  - "Nhận diện và khách hàng": `tp_code`, `partner_id`, `company_id`.
  - "Phụ trách và mốc": `tp_department_id`, `user_id`, `kd_deadline`.
- Notebook:
  - "Phạm vi / đầu ra": `kd_scope`.
  - "Phân công" (`groups="tp_core.group_manager"`), giữ nguyên chính sách.

### C. TP Contracts (`tp.contract`, `tp.contract.revision`)

Chỉ kế thừa extension để thêm `class`. Không đổi field, nút, widths hay optional của view `tp_contract`, nên app TP Contracts ngoài KH-KD không đổi hành vi.

- **List hợp đồng:** `class="tp_kd_table"`; W trên `code`, `name`, `project_id`, `partner_id`. Giữ `create/edit/delete=0` và nút "Tạo nháp hợp đồng" theo `tp_can_create_contract`.
- **List phiên bản:** `class="tp_kd_table"`; W trên `contract_id`, `name`.
- **Form hợp đồng:** `class="tp_kd_form"`. Section có sẵn là "Bản gốc/phụ lục" (`revision_ids`). Smart button tài liệu/lịch sử giữ nguyên.
- **Form phiên bản:** `class="tp_kd_form"`. Notebook có sẵn: Dòng phạm vi, Lần trình rà soát, Tham chiếu BASE. Nút tiền `action_tp_open_amounts` chỉ khi `tp_financial_read_granted`.
- **Wizard** draft/amendment/submit/return/rework: `class="tp_kd_form"`. Giữ `issue_ids`, `line_ids`, `amount_input_ids` editable, required và validation.

Version, idempotency và unsaved guard ở wizard/controller `tp_contract` không đổi.

### D. Kế hoạch và công việc / WBS (`project.task`) — mẫu đầu tiên

**List** `kd_task_list` (`tp_kd_list`):

| Cột | Field | Hiển thị | Bề rộng |
| --- | --- | --- | --- |
| Công việc | `name` | S, W | [280,360] |
| Dự án | `project_id` | S, W | [240,320] |
| Chịu trách nhiệm chính | `kd_responsible_id` | S | [160,200] |
| Thời hạn | `date_deadline` | S, datetime giữ giờ | [150,180] |
| Trạng thái | `state` | S, badge | [140,180] |
| Nhiệm vụ cha | `parent_id` | O, W | [200,280] |
| Đầu ra bàn giao | `kd_deliverable` | O, W | [220,320] |

Không dựng cây/indent giả.

**Form** `kd_task_form` (`tp_kd_review_form`):

- Giữ smart button "Công việc con".
- Tiêu đề: tên (readonly theo `kd_task_can_write`) và trạng thái dạng badge readonly. Đây là field `state` có sẵn chuyển chỗ.
- Hai khối:
  - "Công việc và dự án": `project_id`, `parent_id`, `kd_contract_id`, `company_id` (ẩn).
  - "Phân công và hạn": `kd_responsible_id`, `user_ids`, `date_deadline`.
- Khối "Đầu ra bàn giao": `kd_deliverable` (required giữ nguyên), `description`.
- Ghi chú TASK-001 giữ nguyên. Không thêm nút giao, sửa hay hoàn thành.

### E–K. Bảy loại hồ sơ rà soát (khung chung)

**List chung** (`tp_kd_list`, giữ `decoration-danger` cho returned):

| Field | Bề rộng / kiểu |
| --- | --- |
| `code` | [110,150] |
| `name` | W [260,360] |
| `project_id` | W [220,300] |
| `state` | badge [130,170] |
| `owner_id` | [150,200] |
| `date_due` | native |

**Form chung:**

- Header: `action_submit`, `action_return`, `action_rework` cùng `invisible` và context `kd_expected_version`, statusbar `state`.
- Smart button "Hồ sơ dự án".
- Tiêu đề: tên.
- Hai khối:
  - "Căn cứ và dự án": `code`, `project_id`, `company_id` (ẩn), `department_id`, `contract_id`, `task_id`.
  - "Phụ trách và hạn": `owner_id`, `reviewer_id`, `date`, `date_due`, `version`.
- Khối nghiệp vụ riêng có tiêu đề.
- Notebook nghiệp vụ, rồi "Giá trị minh họa" (`invisible="not can_read_money"`, render bởi server-side modifier, không tải rồi che bằng CSS), rồi "Lịch sử lần trình".
- Ghi chú miễn trừ giữ nguyên.

| Loại | Cột list thêm (S) | Cột O | Khối nghiệp vụ trên sheet | Notebook nghiệp vụ |
| --- | --- | --- | --- | --- |
| E. Giao khoán `tp.allocation` | `contract_id` W, `allocation_kind`, `recipient_department_id` "Đơn vị nhận", `partner_id` "Thầu phụ", `parent_id` | `owner_id`, `period_from`, `period_to` | "Bên nhận và phân cấp": `allocation_kind`, `recipient_department_id`, `partner_id`, `parent_id` · "Kỳ thực hiện": `period_from`, `period_to` | Phạm vi / đầu ra; Khoán cấp 2 (`child_ids` readonly + ghi chú không cộng trùng); Giá trị minh họa (`amount_ids`, `overrun_warning`); Lịch sử |
| F. Sản lượng `tp.production` | `name`, `period_from`, `period_to`, `allocation_id` "Giao khoán nguồn" W, `owner_id` "Người lập" | `contract_id`, `reconciliation_state`, `quantity`, `unit`, `date_due` | "Nguồn và kỳ": `allocation_id`, nút `action_allocation`, `period_from`, `period_to` · "Khối lượng tự khai": `quantity`, `unit`, `completion_percent`, `reconciliation_state` | Phạm vi / đầu ra; Giá trị minh họa; Lịch sử. Nhãn "tự khai, không phải doanh thu" giữ |
| G. Nghiệm thu `tp.acceptance` | `name`, `round_code`, `period_from`, `period_to`, `production_id` "Sản lượng nguồn" W | `counterparty_id`, `contract_id` | "Nguồn và đợt": `production_id`, nút `action_production`, `round_code`, `counterparty_id` · "Kỳ và khối lượng": `period_from`, `period_to`, `quantity`, `unit` | Phạm vi / đầu ra; Kiểm kê căn cứ (`evidence_checklist`); Giá trị minh họa; Lịch sử. Không là ký nghiệm thu pháp lý |
| H. Đề nghị thanh toán `tp.payment.request` | `direction`, `payment_basis`, `partner_id` "Bên liên quan" W, `reconciliation_state` W | `acceptance_id`, `period_from`, `period_to`, `owner_id` | "Loại đề nghị và căn cứ": `direction`, `payment_basis`, `acceptance_id`, nút `action_acceptance`, `advance_basis` · "Đối tượng và kỳ": `partner_id`, `period_from`, `period_to`, `reconciliation_state` | Nội dung / phạm vi; Chứng từ và đối chiếu (`document_checklist`); Giá trị minh họa; Lịch sử. Không có nhãn "Đã thanh toán" |
| I. Kế hoạch định kỳ `tp.periodic.plan` | `period_kind`, `period_from`, `period_to` | `owner_id`, `date_due` | "Kỳ kế hoạch": `period_kind`, `period_from`, `period_to`, nút `action_source_productions` | Phạm vi; Chỉ tiêu và đối chiếu nguồn (= page tiền, cùng `invisible`; `measure`, `amount_state`, `value`, `source_status`, `source_value`); Lịch sử |
| J. Năng lực `tp.credential` | `subject_kind`, `subject_id` W, `credential_kind` W, `valid_to`, `expiry_status` W | `project_id`, `valid_from`, `period_from`, `period_to`, `date_due` | "Đối tượng năng lực": `subject_kind`, `subject_id`, `credential_kind`, nút `action_used_opportunities` · "Hiệu lực": `valid_from`, `valid_to`, `expiry_status` | Phạm vi năng lực; Nguồn / xác minh (`source_note`); Lịch sử. Private restriction giữ |
| K. Nghĩa vụ `tp.obligation` | `obligation_kind` W, `checklist_status` W | `contract_id`, `period_from`, `period_to` | "Loại và tình trạng": `obligation_kind`, `checklist_status` | Yêu cầu / phạm vi; Danh mục hồ sơ (`document_checklist`, `checklist_update_reason`); Lịch sử |

Production và acceptance list trước đây thiếu `name`. Thêm field có sẵn, không đổi model.

**Wizard** `transition_form` (`tp.kd.transition`): `class="tp_kd_form"`. Giữ `reason`, `fix_summary` theo `action`, footer Xác nhận/Hủy.

**Bảng con:**

- `amount_ids` editable bottom, giữ required/invisible.
- `event_ids` readonly, create/delete false.
- `child_ids` readonly.

Cả ba dùng style bảng con; không thêm cột hay nút.

### L. Tổng quan và Báo cáo KH-KD

- **Bảng điều hành dự án** (`table.o_tp_kd_table`): bordered theo token, header `#EEF3F8`, tên dự án wrap, số `tabular-nums`, giữ `aria-sort`, chọn cột, phân trang và Thao tác ▾.
- **Bảng nguồn hồ sơ:** cùng chuẩn; schema theo loại nguồn giữ nguyên.
- **Việc của tôi:** là danh sách `ul`, không phải bảng (N/A cho kẻ cột). Thêm đường phân cách dòng cùng token để đồng bộ.
- **Danh sách mở từ biểu đồ/KPI:** qua `open_records` / `get_kd_action`, nay mở đúng list/form KH-KD nên có cùng style.
- G01–G05, bộ lọc, metric và domain không đổi.

## 7. Form chung

- Sheet: tối đa 1280px, padding 24px; mobile padding 12px.
- Tiêu đề 24px semibold.
- Group có tiêu đề: separator 13px chữ hoa nhẹ màu `#52677D`, kẻ dưới `#D9E2EC`.
- Label 13px `#52677D`, field 14px.
- Desktop hai cột cân đối (native `o_inner_group`); <768px một cột native.
- Read mode: field trống hiện "—" bằng CSS `:empty::before` trên phần tử readonly. Không ghi vào DB, edit mode không đổi.
- Notebook: tab active có gạch dưới `#255F85`; mobile cuộn ngang native.
- Không thêm nút Lưu thứ hai; Save/Discard/autosave theo controller hiện có.

## 8. Sidebar: quy tắc mục lá đang mở

**Quy tắc:** lá được tô là nghiệp vụ của danh sách hoặc hồ sơ đang mở, theo thứ tự ưu tiên:

1. Action của lá (menu).
2. Context `tp_kd_leaf` do helper KH-KD đặt (Tổng quan, smart button, nút nguồn, tạo hồ sơ).
3. Lá vừa bấm (sessionStorage).
4. Giữ lá trước.

Cách hoạt động:

- Quay lại breadcrumb Tổng quan thì Tổng quan được tô lại vì action của nó khớp.
- `tp_kd_leaf` là XMLID menu, gắn theo model trong helper KH-KD (`open_records`, `_kd_form`, `action_project`, nút nguồn, `action_kd_create`, `action_kd_contracts`/`action_contracts`).
- Server action Hợp đồng trả action khác id; sidebar giữ lá vừa bấm khi action trả về không khớp lá nào.
- Không tô theo model chung: CRM/Project ở app khác không có context này.
- Không ghi state/model, không tạo action trùng.

## 9. Gap ghi nhận, không xử lý trong task

| Gap | Lý do |
| --- | --- |
| Hợp đồng không có field phiên bản, người phụ trách hoặc hạn ở cấp hợp đồng; `tp_latest_review_state` là compute không lưu | Không tạo field/model |
| Không có cột tiền ở list dossier | Tiền nằm ở `amount_ids` one2many theo quyền; không cộng nhiều currency/basis |
| Năng lực không có field "số hiệu" | `code` là mã hồ sơ nội bộ |
| Kế hoạch định kỳ: "loại chỉ tiêu" chỉ có ở dòng `amount_ids` | Không đưa lên list |
| `expiry_status` có chữ "Còn30ngày" thiếu khoảng trắng trong compute | Chuỗi trong model; không sửa model trong task UI |
| List TP Contracts không có toolbar mật độ/khôi phục cột | View/action thuộc `tp_contract`; dùng ⚙ sidebar |
| Resize cột không lưu qua lần tải trang | Hành vi native Odoo 20 |
| Dark mode chưa có token KH-KD riêng | Không đổi theme toàn hệ thống; bảng giữ màu sáng theo đặc tả |
| Ô many2one đang sửa (input) vẫn cắt chữ khi hẹp | Widget autocomplete native; chỉ ô chỉ đọc được cho xuống dòng |
| Mã hợp đồng thử dài (`KD-UI3-HD-…`, `HD-BROWSER-…`) xuống dòng giữa chuỗi trên list TP Contracts | Bề rộng cột thuộc view `tp_contract`; inherit chỉ thêm class, không chỉnh width |
| Tên tổng hợp rất dài làm dòng cao hơn ở mật độ Gọn | Ưu tiên đọc đủ chữ (wrap) hơn giữ chiều cao cố định |
| Grouped list hiện "N records" bằng tiếng Anh | Chuỗi i18n native của `web`; không sửa `addons/` |
| Trên Windows, Odoo test đôi khi ghi WinError 5 khi dọn filestore tạm | Môi trường; không ảnh hưởng kết quả test |
| Trình rà soát hợp đồng yêu cầu mọi dòng phạm vi có giá trị đã xác nhận | Rule backend `amounts_not_confirmed`, đúng nghiệp vụ; script kiểm thử nhập giá trị đã xác nhận trên clone |

## 10. Bản đã dựng (07/11/2026)

Các con số ở mục 6 là đề xuất trước code. Khi dựng mẫu WBS ở 1440px, sidebar mở để lại khoảng 1142px cho bảng, và Odoo cộng thêm khoảng 24px vào mỗi `min` (padding, icon sort). Tổng min ban đầu làm cột Trạng thái tràn khỏi vùng nhìn, nên min được hạ. Max giữ để cột dài vẫn được nới khi màn rộng.

### 10.1 Cột list đã dựng

Ký hiệu như mục 6.

| List | Cột hiện sẵn (thứ tự) | Cột O |
| --- | --- | --- |
| Cơ hội `opportunity_list` | `name` W [220,360] · `partner_id` W [160,260] · `kd_bid_state` W [130,200] · `kd_deadline` [130,160] · `user_id` "Người phụ trách" W [130,200] · `kd_route` [100,140] | `tp_project_id` "Dự án liên quan" W [180,280], `kd_source` W [200], `kd_scope` [240] |
| Dự án `kd_project_list` | `tp_code` "Mã dự án" [100,140] · `name` "Tên dự án" W [240,360] · `partner_id` W [180,280] · `user_id` [140,200] · `kd_deadline` [130,160] | `tp_department_id` [150,240], `company_id`, `last_update_status`, `stage_id` và cột tùy chọn native |
| WBS `kd_task_list` | `name` W [240,360] · `project_id` W [220,300] · `kd_responsible_id` W [190,220] · `date_deadline` [130,170] · `state` badge [130,170] | `parent_id` W [200,280], `kd_deliverable` W [220,320] |
| Giao khoán | `code` W [100,140] · `name` W [190,360] · `project_id` W [160,280] · `allocation_kind` [100,150] · `contract_id` W [140,260] · `state` [120,160] · `date_due` [100,130] | `owner_id`, `recipient_department_id` "Đơn vị nhận", `partner_id` "Thầu phụ", `parent_id` "Khoán cha", `period_from`, `period_to` |
| Sản lượng | `code` · `name` · `project_id` · `period_from` [90,120] · `period_to` [90,120] · `state` · `date_due` | `owner_id` "Người lập", `allocation_id` "Giao khoán nguồn", `contract_id`, `reconciliation_state`, `quantity`, `unit` |
| Nghiệm thu | `code` · `name` · `project_id` · `round_code` [80,120] · `period_from` · `period_to` · `state` | `date_due`, `owner_id`, `production_id` "Sản lượng nguồn", `counterparty_id`, `contract_id` |
| Đề nghị thanh toán | `code` · `name` · `project_id` · `direction` [90,130] · `partner_id` "Bên liên quan" W [140,240] · `state` · `date_due` | `payment_basis`, `reconciliation_state`, `acceptance_id`, `period_from`, `period_to`, `owner_id` |
| Kế hoạch định kỳ | `code` · `name` · `project_id` · `period_kind` [100,140] · `period_from` · `period_to` · `state` | `date_due`, `owner_id` |
| Năng lực | `code` · `name` · `subject_id` "Đối tượng" W [150,240] · `credential_kind` W [130,200] · `valid_to` [90,120] · `expiry_status` W [110,160] · `state` | `project_id`, `subject_kind`, `valid_from`, `period_from`, `period_to`, `owner_id`, `date_due` |
| Nghĩa vụ | `code` · `name` · `project_id` · `obligation_kind` W [120,200] · `checklist_status` W [110,200] · `state` · `date_due` | `contract_id`, `period_from`, `period_to`, `owner_id` |

Bảy list hồ sơ dùng chung `code` W [100,140], `name` W [190,360], `project_id` W [160,280], `state` badge [120,160], `date_due` [100,130]; cột người (`owner_id`) W [130,200]. Mã hồ sơ được wrap vì mã dài (vd. `ALLOC-…`) không vừa 100px. Các cột liên kết chỉ hiển thị một số ít mặc định để bảng vừa 1142px; phần còn lại bật bằng chọn cột.

### 10.2 Khác với đề xuất

- WBS: Odoo co đều mọi cột rộng hơn `min` khi thiếu chỗ. Với min 140, tên người phụ trách tổng hợp bị co xuống hai dòng ở mọi dòng nên mật độ Gọn không còn gọn; min được nâng lên 190 (Dự án max 300 để bù).
- Cơ hội: `tp_project_id` chuyển sang O vì domain action đã lọc theo dự án và tên dự án dài chiếm nhiều chỗ nhất; Hạn đứng trước Người phụ trách.
- Dự án: Phòng chủ trì chuyển sang O (cùng lý do bề rộng). Thêm `tp_code` "Mã dự án" có sẵn ở model.
- Năng lực: `subject_kind` chuyển sang O vì `subject_id` đã cho biết đối tượng.
- Thanh toán: `payment_basis`, `reconciliation_state` chuyển sang O để Bên liên quan đọc đủ chữ.
- Giao khoán, Sản lượng, Nghiệm thu: cột nguồn liên kết (Đơn vị nhận, Thầu phụ, Khoán cha, Giao khoán nguồn, Sản lượng nguồn) và Người lập chuyển sang O. Liên kết vẫn mở được từ form qua nút nguồn có sẵn.
- Kẻ header dùng `box-shadow: inset` thay border trên `th` để không lệch với cột sticky và resize handle native.
- Form: ô readonly trống hiện "—" cả với field Odoo đã gắn `o_field_empty` (ngày, lựa chọn, many2one rỗng). Many2one chỉ đọc dài (dự án, hợp đồng nguồn) xuống dòng thay vì "…". `version` có nhãn "Phiên bản".
- Toolbar Thoáng/Gọn và Khôi phục cột nằm trong `.o_tp_kd_list_tools`, ẩn khi đang chọn dòng để nhường chỗ thao tác hàng loạt native.
- Tổng quan: style bảng chỉ áp cho `table.o_tp_kd_table` trong `.o_tp_kd_overview`; trạng thái `.is-busy` cũng nằm trong scope đó.
- TP Contracts: chỉ thêm class (`tp_kd_table`, `tp_kd_form`, `tp_kd_wrap`, `tp_kd_strong`); không đổi width/optional của view gốc.
- Tổng quan cuộn bằng chuột (CHG-20261107-001, 20.0.1.2.1): gốc `.o_tp_kd_ov` cũng là phần tử `.o_action` của action. Trên desktop, layout gốc Odoo `html .o_web_client > .o_action_manager > .o_action` đặt `overflow: hidden` và ẩn scrollbar (view native cuộn trong `.o_content`), đè `overflow: auto` của Tổng quan nên lăn chuột/touchpad không cuộn; lỗi có từ KD-UI-002, mobile <992px không bị vì Odoo tự cho `.o_action` cuộn. Sửa bằng selector `.o_web_client > .o_action_manager > .o_tp_kd_ov.o_action` (chỉ phần tử Tổng quan): `overflow: auto`, `overscroll-behavior-y: contain`, scrollbar mảnh hiện lại. Action khác giữ layout Odoo.
