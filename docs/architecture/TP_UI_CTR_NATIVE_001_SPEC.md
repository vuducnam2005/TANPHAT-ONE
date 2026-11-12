# UI-CTR-NATIVE-001 — Đặc tả giao diện native TP Contracts

**Audit implementation 06/11/2026 — CHG-20261106-003: `TECHNICAL_ACCEPTED_TEST_ONLY` cho 001a.** [Báo cáo độc lập](../reviews/UI_CTR_NATIVE_001A_INDEPENDENT_AUDIT.md): chạy lại Odoo107/107, browser42/42, runner18/18; D1/D2/owner/đối chứng và AT-17 đạt trên implementation. Không sửa application; chưa áp dev18069. G7/Q2/business/pilot giữ mở; phạm vi upload/BASE/ký/hiệu lực/thanh toán/grant thật không mở. Trạng thái chờ audit CHG002 bên dưới là lịch sử đã được audit này thay cho đúng slice001a.

**Implementation 06/11/2026 — CHG-20261106-002: `IMPLEMENTED_VERIFIED_TEST_PENDING_AUDIT` cho 001a.** [Báo cáo và24 AT](../reviews/UI_CTR_NATIVE_001A_IMPLEMENTATION.md): RED22 trước implementation, GREEN Odoo107/browser42 trên owned clone18169 với dữ liệu giả. D1/D2 có control trên model thật; AT-17/G8 đạt kỹ thuật theo request mới, không write grant lúc đổi ngày. Chờ audit implementation bởi phiên khác, G7/Q2/business/pilot giữ mở, không áp dev.

**Gate thiết kế trước implementation — audit độc lập CHG-20261106-001: D1/D2 `PASS_SPEC`; 001a `READY_FOR_TEST_CODE`.** [Audit chấp nhận đặc tả](../reviews/NATIVE_STABILIZE_001_D1_D2_ACCEPTANCE_AUDIT.md), [prompt code Claude](../prompts/CLAUDE_UI_CTR_NATIVE_001A.md). Những đoạn chờ audit/NEEDS_FIX dưới đây là lịch sử; không yêu cầu correction D1/D2 thêm trước code.

**Correction delta 05/11/2026 — CHG-20261105-006: `CORRECTED_PENDING_AUDIT_DELTA_D1_D2`.**
- D1: mục 9.2 thêm restriction `[('wizard_id', 'access', 'read')]` cho `draft.line`/`return.issue`; thêm AT-18.
- D2: mục 9.3 bước 2/3, mục 12, G7 thêm guard capability cho `current_amount_text`; AT-10 tách thành AT-10a..AT-10d, ca metadata đổi thành AT-10g.

Trạng thái tại bàn giao006 là chờ audit đúng hai delta; đã được audit CHG-20261106-001 chấp nhận ở tầng đặc tả (xem đầu tài liệu). [Báo cáo correction](../reviews/NATIVE_STABILIZE_001_CORRECTION.md) mục 7.

**Kết luận audit delta CHG-20261105-005 (lịch sử, đã xử lý bằng CHG-20261105-006): `NEEDS_FIX`.** A3 runner đạt. Đặc tả A1/A2 còn D1/P2 (scope restriction riêng trên `draft.line`/`return.issue`) và D2/P2 (guard assignment cho compute tiền, AT-10/§12 phải khớp G7). [Báo cáo/bằng chứng độc lập](../reviews/NATIVE_STABILIZE_001_DELTA_AUDIT.md), [prompt correction D1/D2](../prompts/CLAUDE_NATIVE_STABILIZE_001_DELTA_CORRECTION.md). Các đề xuất READY/chờ audit phía dưới là lịch sử; chưa phát prompt code001a. Lượt audit này không tự sửa thiết kế chi tiết, ACL hoặc wizard.

**Audit override 05/11/2026 — CHG-20261105-003: `NEEDS_FIX`, chưa phát prompt code 001a.** Kết luận READY bên dưới là đề xuất tự kiểm CHG-20261105-002, chưa được chấp nhận. [Audit độc lập](../reviews/NATIVE_STABILIZE_001_INDEPENDENT_AUDIT.md) phát hiện A1 (transient không có owner rule mặc định trong source này) và A2 (chưa bảo vệ bản sao tiền trong wizard sau revoke). Cần sửa đặc tả/acceptance và audit delta trước code; nội dung lịch sử dưới đây giữ làm căn cứ correction.

**Correction 05/11/2026 — CHG-20261105-004:** đã sửa A1 (mục 9.1, 9.2, 9.4, 9.5; AT-09, AT-14..AT-16) và A2 (mục 8 "Gửi khóa `amount`", 9.3, 10, 12; AT-03, AT-10..AT-10f, AT-17; G7, G8). Báo cáo: [correction](../reviews/NATIVE_STABILIZE_001_CORRECTION.md). Vẫn **chờ audit delta**, chưa phát prompt code 001a.

**Trạng thái:** đặc tả viết05/11/2026, correction CHG-20261105-004/006, audit thiết kế CHG-20261106-001; implementation001a trên DB test CHG-20261106-002, audit độc lập CHG-20261106-003 đạt phạm vi test.
**Kết luận hiện hành:** `TECHNICAL_ACCEPTED_TEST_ONLY` cho phạm vi **001a** (mục 1, 16), chưa áp dev hoặc nghiệm thu công ty. **Upload/phân loại tài liệu chưa sẵn sàng** (mục 15, G1).
**Căn cứ:** DEC-030 (UI native Odoo), DEC-017 (`financial_read` theo project), DEC-020/DEC-021 (CTR-002a chỉ trên DB test với actor fixture), DEC-025 (nhãn `tp_contract/i18n/vi.po`), source `custom_addons/tp_contract` và `tp_planning_api/controllers/contracts.py` đọc ngày 05/11/2026.

Đặc tả này **không thêm state, capability, nhóm quyền hay quy tắc nghiệp vụ mới**. Giao diện native gọi lại đúng workflow CTR-002a đã có. Các phần chưa có backend hoặc chưa có quyết định được ghi ở mục 15, không tự bù bằng giả định.

## 1. Phạm vi

**001a (sẵn sàng viết test và code trên DB test):**

- menu, danh sách và form chỉ đọc cho hợp đồng, bản gốc/phụ lục, dòng phạm vi, số tiền (theo grant), lần trình, tham chiếu BASE (chỉ đọc), tài liệu (xem/tải theo quyền) và lịch sử;
- sáu action đã có: tạo nháp hợp đồng, tạo nháp phụ lục, sửa nháp, trình/trình lại rà soát, trả lại có lý do, bắt đầu chỉnh sửa lại ("mở lại" bản bị trả lại).

**Ngoài phạm vi (không nút, không wizard, không đổi state):**

- BASE record/verify, `review_complete`, ký/thẩm quyền ký, hiệu lực, chuyển `lifecycle_state`;
- nghiệm thu, thanh toán, giao khoán;
- hủy bản sửa đổi (`cancelled`), đổi người rà soát;
- quản trị grant, cấp quyền cho người thật;
- pilot.

DEC-020 vẫn áp dụng: chỉ chạy trên DB test với actor fixture. Q2 còn chặn người dùng thật.

## 2. Nguồn sự thật đã kiểm

| Thành phần | Source | Ghi chú dùng cho UI |
|---|---|---|
| Hợp đồng | `tp.contract` (`models/tp_contract.py`) | `code` duy nhất theo company; `department_id` cố định; `aggregate_version` chỉ đổi qua workflow; header khóa khi có revision đang rà soát (`_tp_check_protected_write`) |
| Bản gốc/phụ lục | `tp.contract.revision` (`models/tp_contract_revision.py:9` `REVIEW_STATES`) | `review_state` ∈ `draft`, `in_review`, `returned`, `review_complete`, `cancelled`; `_tp_is_frozen()` dòng 114; `_amount_summary()` dòng 130 |
| Dòng phạm vi | `tp.contract.line` | Không có trường tiền; `change_kind` ∈ `original`, `unchanged`, `amended`, `added` do server tính |
| Số tiền dòng | `tp.contract.line.amount` | `amount_state` `unconfirmed`/`confirmed`, `tax_basis`; record rule `line_amount_financial_reader` đòi `project_id.tp_financial_read_granted` |
| Lần trình | `tp.contract.submission` + `.amount` | Bất biến, trừ một lần ghi kết quả trả lại và một lần ghi bắt đầu chỉnh sửa (`RETURN_FIELDS`, `REWORK_FIELDS`) |
| Tài liệu | `tp.contract.document` | `confidentiality` mặc định `financial`; `FINANCIAL_KINDS` (dòng 4) luôn financial; `_tp_check_not_submitted()` dòng 52; `ir_attachment.py` chặn sửa binary trực tiếp |
| BASE | `tp.approval.reference` (+ `.amount`) | Chỉ khai báo; không suy ra đã ký/hiệu lực (`test_base_approval_does_not_make_revision_signed_or_effective`) |
| Lịch sử, thông báo, idempotency | `tp.contract.audit`, `tp.contract.outbox`, `tp.contract.idempotency` | Audit append-only, không lưu tiền; outbox chỉ người nhận đọc; idempotency chỉ `base.group_system` đọc |
| Workflow | `tp.contract.workflow` (`models/tp_contract_workflow.py`) | `_tp_run` dòng 268; `ACTION_CAPABILITIES` dòng 33; `_tp_lock` 360; `_tp_guard` 373; `_tp_replay` 388; `_tp_claim` 402; `_tp_audit` 425; `_tp_notify` 445; `_tp_eligible_reviewers` 625; `_tp_available_actions` 640; sáu action 667–863 |
| ACL | `security/ir.access.csv` | `tp_core.group_user` chỉ có quyền `r` trên mọi model hợp đồng; mọi ghi đi qua workflow với quyền superuser sau khi đã kiểm tra |
| API cũ (giữ) | `/api/v1/contracts…` | Contract giữ nguyên; UI native không bắt buộc đi qua REST (AGENTS §2) |

Tất cả method workflow đều bắt đầu bằng `_`, nên không gọi được qua RPC. Giao diện native cần một điểm vào public hẹp (mục 9).

## 3. Actor và quyền

Capability lấy từ `tp.project.grant` (`tp_project_grant.py:5`). Các capability hợp đồng gắn theo project + phòng ban của hợp đồng; `financial_read` gắn theo project. Hàm `_tp_capabilities` trả về rỗng nếu user không có assignment còn hiệu lực trên project. Chức danh, nhóm `tp_core.group_manager` và admin kỹ thuật **không** tự có tiền hay quyền thao tác (`test_platform_manager_and_admin_get_no_money_by_default`).

| Actor (fixture DEC-020) | Grant | Xem | Thao tác native được hiện |
|---|---|---|---|
| Người đọc theo phạm vi | chỉ assignment | metadata hợp đồng/revision/dòng/lần trình/audit, tài liệu `general` | không |
| Người soạn metadata | `contract_draft_edit` | như trên | tạo hợp đồng không kèm tiền, tạo phụ lục, sửa nháp không đụng tiền, bắt đầu chỉnh sửa lại |
| Người soạn đầy đủ | `contract_draft_edit`, `contract_submit`, `financial_read`, `financial_draft_edit` | thêm số tiền, tổng, tài liệu financial của project | thêm: nhập/sửa tiền, đổi tiền tệ, trình/trình lại |
| Người rà soát thương mại | `contract_review_commercial`, `financial_read` | như người soạn đầy đủ (chỉ đọc) | trả lại, chỉ khi là reviewer của lần trình đang chờ và không phải người trình |
| Chỉ xem tiền | `financial_read` | metadata và tiền | không |
| Khác phòng ban / khác project / khác company | grant sai phạm vi | bên khác phòng ban: chỉ phần đọc theo assignment; khác project/company: không thấy hồ sơ (tương đương 404) | không |

**Quyền theo trường:**

- Số tiền dòng, tổng revision, `submission.amount.financial_snapshot`, `approval.reference.amount` và tài liệu `financial` chỉ hiện khi record rule cho đọc, tức user có `financial_read` trên đúng project.
- UI chỉ được ẩn phần này **thêm** dựa trên `project_id.tp_financial_read_granted`; việc ẩn không thay cho record rule.
- Header (`code`, `name`, `partner_id`, `contract_type`, `currency_id`) chỉ sửa ở bản gốc đang nháp. Đổi tiền tệ được tính là sửa tiền (`_tp_edit_draft`, dòng 736–738).

## 4. Menu và danh sách

- **Menu:** `TP Contracts` là lá con của `tp_core.menu_platform`, nhóm `tp_core.group_user`, action danh sách `tp.contract`. Home catalog đã mở rộng các lá của `menu_platform`, nên mục này tự thành ô ứng dụng. Không tạo nhóm mới.
- **Danh sách hợp đồng:**
  - Cột: `code`, `name`, `project_id`, `partner_id`, `contract_type`, `department_id`, `lifecycle_state`, trạng thái bản mới nhất (trường compute không lưu, tính bằng quyền của user).
  - Không có cột tiền.
  - Bộ lọc: theo dự án; "Có bản đang rà soát" = `[('revision_ids.review_state', '=', 'in_review')]`; "Có bản bị trả lại"; "Có bản nháp".
  - Nhóm theo dự án/phòng ban.
  - `create="0"`, `delete="0"`, `edit="0"`. ACL đã chặn ghi; nút tạo chuẩn không được hiện.
- **Nút trên danh sách:** "Tạo nháp hợp đồng" mở wizard `create_contract` (mục 8). Hiện khi user có `contract_draft_edit` trên ít nhất một project được giao; server vẫn kiểm tra lại.
- **Trạng thái rỗng:** "Chưa có hợp đồng trong các dự án bạn được phân công."
- **Export, `read_group`, tìm kiếm:** không lộ tiền, vì tiền nằm ở model riêng (`test_native_aggregates_and_export_hide_amounts`).

## 5. Form hợp đồng

- **Chỉ đọc cho mọi user.** Nút ở header là action server (mục 8), không lưu form.
- **Thông tin chung:**
  - mã, tên, dự án, đối tác, loại hợp đồng, tiền tệ, phòng ban, `lifecycle_state` (nhãn "Chưa có hiệu lực");
  - nhãn `legacy_unverified` ("Dữ liệu cũ chưa xác minh").
- **Tab "Bản gốc/phụ lục":** danh sách `revision_ids` gồm `sequence`, `revision_kind`, `name`, `reference`, `review_state`, `signature_status`, `effectivity_status`; bấm để mở form revision.
- **Nút thống kê "Tài liệu":** mở danh sách `tp.contract.document` với `[('contract_id', '=', id)]`; record rule tự lọc theo `confidentiality`.
- **Nút thống kê "Lịch sử":** mở danh sách `tp.contract.audit` với `[('contract_id', '=', id)]`.
- **Nút ở header:** "Tạo nháp phụ lục sửa đổi", hiện khi `create_amendment` có trong `_tp_available_actions(contract)`.
- **Chatter:** không bật trong 001a. Lịch sử chính thức là `tp.contract.audit`, và chatter có thể làm lộ nội dung hoặc tên tệp.

## 6. Form bản gốc/phụ lục, dòng và số tiền

- **Statusbar `review_state`:**
  - luôn hiện `draft`, `in_review`, `returned`;
  - `review_complete` và `cancelled` chỉ hiện khi record đang ở đó;
  - không có nút nào đưa tới hai state này.
- **Thông tin revision:**
  - Hiện: `revision_kind`, `name`, `reference` ("Số văn bản"), `previous_revision_id`, `signature_status`, `signature_authority_status`, `effectivity_status`, `signed_date`, `effective_date`, `recorded_at`.
  - Tất cả chỉ đọc. Nhãn ký/hiệu lực là dữ liệu đã ghi, không phải kết quả rà soát.
- **Dòng phạm vi** (`line_ids`): `sequence`, `scope_key`, `name`, `work_item_id`, `change_kind`, `previous_line_id`. Không có tiền.
- **Số tiền:**
  - Nút thống kê "Số tiền" mở `tp.contract.line.amount` với `[('revision_id', '=', id)]`, gồm dòng, `amount_state`, `amount`, `tax_basis`, `currency_id`.
  - Nút chỉ hiện khi `project_id.tp_financial_read_granted`; record rule vẫn là lớp bảo vệ chính.
  - Trường tổng compute không lưu gọi `_amount_summary()` bằng quyền của user và chỉ trả kết quả khi có `financial_read`:
    - `confirmed` → số tiền kèm đơn vị tiền tệ;
    - `incomplete` → "Chưa đủ giá trị đã xác nhận";
    - `mixed_basis` → "Khác cơ sở thuế, không cộng tổng";
    - `empty` → "Chưa có dòng phạm vi".
  - **Không bao giờ hiển thị 0 thay cho `null`.**
- **Tab "Lần trình rà soát"** (`submission_ids`):
  - Cột: `sequence`, `submitted_by_id`, `submitted_at`, `reviewer_id`, `outcome` ("Chờ rà soát"/"Trả lại"), `fix_summary`, `returned_by_id`, `returned_at`, `return_reason`, `return_issues` (hiển thị dạng danh sách đọc), `rework_started_by_id`, `rework_started_at`, `rework_reason`.
  - Không hiện `metadata_snapshot` thô hay các hash, trừ khi mở chế độ kỹ thuật cho `base.group_system`.
- **Tab "Tham chiếu BASE"** (`approval_reference_ids`):
  - chỉ đọc `reference_kind`, `base_reference`, `decision`, `verification_state`, `authority_status`;
  - kèm dòng giải thích "Ghi nhận khai báo; không phải đã ký hoặc đã có hiệu lực";
  - không có nút.
- **Nút ở header:** mục 8, theo `_tp_available_actions(contract, revision)`.

## 7. Tài liệu

| Chức năng | 001a | Căn cứ |
|---|---|---|
| Danh sách | `name`, `document_kind`, `confidentiality`, `revision_id`, `file_name` | Rule `document_reader`: tài liệu financial không hiện bản ghi, nên cả tên tệp cũng không lộ |
| Tải tệp | Widget binary chuẩn (`/web/content`) với quyền của user; không dùng `sudo`, không tạo link công khai/token | `test_financial_attachment_requires_grant`, `test_general_attachment_follows_project_scope`; API cũ dùng `ir.binary._get_stream_from` với quyền người gọi |
| Upload, phân loại, thay tệp | **Không có trong 001a** | Không có action workflow hay capability cho tài liệu; `group_user` chỉ có quyền `r` (G1) |
| Sửa/xóa tài liệu của revision đã trình | Bị chặn ở model | `_tp_check_not_submitted`, `ir_attachment._tp_check_contract_documents` |

## 8. Nút, wizard, state và method

Mỗi nút mở một wizard (`TransientModel`). Wizard đọc dữ liệu bằng quyền của user, dựng payload đúng dạng parser hiện có (`PARSERS`), rồi gọi `tp.contract.workflow._tp_run(action, payload, key=…, contract_id=…, revision_id=…)`. Wizard không bao giờ ghi trực tiếp vào model hợp đồng.

| Nút (nhãn vi.po) | Action / method | Capability (`ACTION_CAPABILITIES`) | State trước → sau | Trường wizard | Audit / thông báo |
|---|---|---|---|---|---|
| Tạo nháp hợp đồng | `create_contract` / `_tp_create_contract` | `contract_draft_edit`; thêm `financial_read` và `financial_draft_edit` nếu có dòng kèm tiền | (mới) → `draft` | project (managed, đọc được), mã, tên, loại, tiền tệ, đối tác, tên/số văn bản revision, dòng | audit `create_contract`, `version_before = None`; không gửi thông báo |
| Tạo nháp phụ lục sửa đổi | `create_amendment` / `_tp_create_amendment` | `contract_draft_edit` | (mới) → `draft`; báo `409 invalid_state` nếu còn revision mở (`OPEN_STATES`) | `expected_version`, tên, số văn bản | audit `create_amendment`; dòng và tiền được chép sang ở trạng thái `unchanged` |
| Chỉnh sửa nháp | `edit_draft` / `_tp_edit_draft` | `contract_draft_edit`; thêm `FINANCIAL_EDIT` khi đổi tiền tệ hoặc `_tp_touches_money` | `draft` → `draft` | `expected_version`; header chỉ ở bản gốc; tên/số văn bản revision; dòng | audit `edit_draft` |
| Trình rà soát / Trình rà soát lại | `submit_review` / `_tp_submit_review` | `contract_submit`, `financial_read` | `draft` → `in_review`; tạo submission, `outcome = pending` | `expected_version`, reviewer, `fix_summary` (bắt buộc từ lần trình thứ hai) | audit `submit_review` hoặc `resubmit_review`; outbox gửi reviewer |
| Trả lại để chỉnh sửa | `return_review` / `_tp_return_review` | `contract_review_commercial`, `financial_read`; phải là `reviewer_id` của lần trình đang chờ, khác `submitted_by_id` | `in_review` → `returned`; submission `outcome = returned` | `expected_version`, lý do (bắt buộc), các ý kiến (`scope_key` lấy từ snapshot, nội dung) | audit `return_review` kèm lý do; outbox gửi người trình |
| Bắt đầu chỉnh sửa lại ("mở lại") | `begin_rework` / `_tp_begin_rework` | `contract_draft_edit` | `returned` → `draft`; ghi `rework_*` một lần | `expected_version`, lý do (bắt buộc) | audit `begin_rework` kèm lý do; không gửi thông báo |

**Quy tắc wizard:**

- **Hiện nút:**
  - Nút chỉ hiện khi action có trong `_tp_available_actions`, lấy qua trường compute không lưu `tp_available_actions` trên contract/revision. Trường này chỉ trả tên action, không trả dữ liệu.
  - Ẩn nút chỉ là gợi ý giao diện; server kiểm tra lại toàn bộ.
  - Nút phải hiện rõ, không chỉ hiện khi hover; dùng chung cho màn hình cảm ứng.
- **Số tiền:**
  - Nhập bằng trường **Char** dạng thập phân, chọn `amount_state` và `tax_basis`.
  - Không dùng `Monetary`/float để quyết định số tiền. Server kiểm `DECIMAL_PATTERN`, độ chính xác của tiền tệ và `MAX_AMOUNT_DIGITS`.
  - `unconfirmed` → `value = null`; `confirmed` cùng `"0"` là số 0 hợp lệ.
  - Số tiền mới do user nhập chỉ nằm ở model riêng `tp.contract.native.amount.input`. Header wizard, dòng metadata và ý kiến trả lại không có trường tiền (mục 9.1, 9.3).
- **Gửi khóa `amount`** (correction A2, CHG-20261105-004: bỏ quy tắc cũ "so với giá trị nạp lúc mở"; wizard **không lưu baseline**):
  - Wizard không lưu số tiền hiện tại, giá trị lúc mở, tổng hay payload dựng sẵn. Số tiền hiện tại chỉ hiển thị qua trường compute không lưu, tính bằng quyền user ở từng request (mục 9.3).
  - Dòng có bản ghi `amount.input` (user chủ động nhập số tiền mới) thì gửi khóa `amount`. Dòng không có thì không gửi, và backend giữ nguyên số tiền đang có.
  - User không có `financial_read` không tạo được `amount.input` vì rule mục 9.3, nên luồng metadata không bao giờ gửi `amount`.
  - Xóa một dòng đang có tiền vẫn cần `FINANCIAL_EDIT` (server trả 403); UI phải báo trước điều này khi user không có quyền.
- **Chọn reviewer:**
  - Danh sách chỉ gồm `_tp_eligible_reviewers(contract)`, đã loại người trình.
  - Chỉ user có `contract_submit` mới xem được danh sách này, như route `/reviewers`.
  - Server kiểm tra lại khi trình (`reviewer_ineligible`).
- **Trình lại:**
  - Nhãn "Trình rà soát lại" khi revision đã có submission.
  - `fix_summary` bắt buộc; hiện lý do và các ý kiến của lần trả lại gần nhất để người soạn đối chiếu.

## 9. Điểm vào RPC native, quyền sở hữu wizard và bản sao tiền

Mục này được viết lại trong correction CHG-20261105-004 để xử lý A1/A2 của [audit độc lập](../reviews/NATIVE_STABILIZE_001_INDEPENDENT_AUDIT.md). Bản trước giả định "rule transient mặc định chỉ cho người tạo đọc record của mình". **Giả định đó sai và đã bị bỏ.**

Căn cứ source Odoo 20 đọc ngày 05/11/2026:

- `TransientModel` dùng cùng cơ chế ACL và record rule như `Model` (`odoo/orm/models_transient.py:10-15`). Không có rule "chỉ người tạo" nào được thêm tự động.
- Trong `ir.access`, dòng có `group_id` là permission. Các permission được OR với nhau giữa mọi nhóm của user.
- Dòng không có `group_id` là restriction, được AND với mọi user (`BaseModel._access_domain`, `odoo/orm/models.py`).
- ORM bỏ `create_uid`/`write_uid` khỏi vals của `create`/`write`. Ngoại lệ duy nhất là superuser lúc nạp registry (`odoo/orm/models.py:3857-3861`, `4269-4273`). Vì vậy dùng được `create_uid` làm owner.

### 9.1 Model

| Model (`TransientModel` trong `tp_contract`) | Vai trò | Trường tiền |
|---|---|---|
| `tp.contract.native.draft` | `create_contract` (`mode = create`) và `edit_draft` (`mode = edit`) | Không |
| `tp.contract.native.draft.line` | Dòng metadata của draft: `scope_key`, `name`; trường hiển thị số tiền hiện tại (không lưu) | Không lưu |
| `tp.contract.native.amount.input` | Số tiền **mới do user nhập**: `wizard_id`, `scope_key`, `amount_state`, `value` (Char), `tax_basis` | Có. Đây là model duy nhất lưu tiền |
| `tp.contract.native.amendment`, `tp.contract.native.submit`, `tp.contract.native.rework` | Mỗi model một action | Không |
| `tp.contract.native.return`, `tp.contract.native.return.issue` | `return_review` và các ý kiến (`scope_key` lấy từ `metadata_snapshot`, nội dung) | Không |

Các model này là điểm vào kỹ thuật, không phải capability mới. `metadata_snapshot` của submission không chứa tiền (`tp_contract_submission.py:14`); phần tiền nằm ở `tp.contract.submission.amount`, có rule riêng.

### 9.2 Quyền sở hữu và phạm vi: ACL và restriction tường minh

Thêm các dòng sau vào `tp_contract/security/ir.access.csv` và không sửa dòng hiện có:

| Model | Permission (`tp_core.group_user`) | Restriction (không group, áp cho mọi user kể cả manager/admin) |
|---|---|---|
| 5 header wizard (`draft`, `amendment`, `submit`, `return`, `rework`) | `crud`, `[('create_uid', '=', user.id)]` | `crud`, `[('create_uid', '=', user.id)]`<br>`crud`, `[('company_id', 'in', company_ids)]`<br>`crud`, `[('project_id', 'access', 'read')]` |
| `draft.line`, `return.issue` | `crud`, `[('wizard_id.create_uid', '=', user.id)]` | `crud`, cùng domain owner<br>`crud`, `[('wizard_id.company_id', 'in', company_ids)]`<br>`crud`, `[('wizard_id', 'access', 'read')]` (D1, CHG-20261105-006) |
| `amount.input` | `crud`, `[('wizard_id.create_uid', '=', user.id)]` | Owner và company như dòng trên, cộng restriction tiền ở mục 9.3 (đã gồm `wizard_id.project_id access read`; giữ nguyên) |

- **Dòng con phải có restriction phạm vi riêng (D1).**
  - Owner và company qua `wizard_id.create_uid`/`wizard_id.company_id` **không** kéo theo quyền đọc header hay project:
    - Odoo tối ưu security domain bằng môi trường sudo (`odoo/orm/models.py:4913-4916`);
    - `_access_domain` chỉ tự thêm restriction của model cha cho quan hệ `_inherits` (`models.py:3622-3628`), không cho mọi Many2one.
  - Probe rollback của audit delta (`.local/native-stabilize001-delta-audit/rollback-probes.json`): sau khi owner mất project access, header bị chặn (read `AccessError`, `search_count` 0) nhưng child vẫn đọc được (read đọc được, `search_count` 1). Thêm `[('wizard_id', 'access', 'read')]` thì child bị chặn.
  - Toán tử `access` trên Many2one thay điều kiện bằng `_access_domain('read')` của header cho **user hiện tại** (`odoo/orm/domains.py:1926-1950`). Header lại có restriction owner + company + `project_id access read`. Vì vậy dòng con theo đúng phạm vi header từ một nguồn, gồm cả khi chính owner mất quyền đọc project.
  - Không suy phạm vi dòng con từ domain `wizard_id.create_uid`.
- **Owner phải là restriction, không chỉ là permission.** Permission được OR giữa các nhóm. Nếu chỉ có permission, một nhóm khác có permission rộng hơn sẽ mở rộng quyền, ví dụ `tp_core.group_manager`, `base.group_system`, nhóm `hr_expense` hoặc một addon cài sau. Restriction được AND nên chặn được mọi trường hợp này.
- **Phạm vi lấy từ target.** `project_id` và `company_id` của header là trường lưu, đặt trong `create()` từ target đọc bằng quyền user (mục 9.4). Giá trị client gửi bị bỏ.
- **Chỉ superuser/`sudo()` bỏ qua `ir.access`.** Code wizard không đọc hay ghi record wizard bằng `sudo()`. Ngoại lệ duy nhất là phép đếm ở bước 5 mục 9.5, chỉ đếm và không đọc giá trị.
- **Giao diện không phải lớp bảo vệ.** Ẩn trường, `readonly` hay `invisible` trên view không bảo vệ được gì.

### 9.3 Bản sao tiền trong wizard (A2)

**Thiết kế đã chọn:** wizard không lưu bản sao nào của tiền hiện có. Tiền do user nhập mới chỉ nằm ở `amount.input` và bị restriction chặn ngay từ request kế tiếp khi user mất grant hoặc assignment.

1. **Không có baseline lưu.** Không trường nào lưu số tiền hiện tại, giá trị lúc mở, tổng hay payload dựng sẵn. Các nơi sau cũng không chứa số tiền:
   - header, `draft.line`, `return.issue`;
   - idempotency (`fingerprint` là HMAC);
   - audit (`payload_sha256`);
   - outbox.
2. **Hiển thị tiền hiện tại bằng compute không lưu, có guard capability (sửa D2, CHG-20261105-006).** Trên `draft.line`, `current_amount_text` là Char với `store=False`, `compute_sudo=False`, không search, không group, không `ormcache`.
   - **Guard trước mọi lần tính.** Compute gom dòng theo header và gọi method riêng của header `_tp_amount_display_allowed()`. Method có dấu `_` nên không gọi được qua RPC. Nó trả `True` chỉ khi `env.user` ở request hiện tại thỏa cả hai điều kiện:
     1. **Project đọc được bằng quyền user:** `wizard.project_id.has_access('read')` (`odoo/orm/models.py:3464`).
     2. **`'financial_read' in env['tp.contract.workflow']._tp_capabilities(project, contract.department_id)`.** Đây là helper backend hiện có (`tp_contract_workflow.py:333-346`):
        - không có assignment `active` thì trả tập rỗng;
        - `financial_read` chỉ có khi grant `active` và `date_end` rỗng hoặc ≥ `context_today` (`_active_grant_domain`, `tp_project_grant.py:92-112`).

     Không tạo capability hay helper quyền mới.
   - **Thiếu một điều kiện:**
     - Mọi dòng của header đó có `current_amount_text = False` và compute không đọc `tp.contract.line.amount`.
     - Nếu header hoặc dòng đã ngoài phạm vi thì restriction mục 9.2 trả `AccessError` trước khi compute chạy.
     - Kết quả: **rỗng** khi còn phạm vi nhưng thiếu quyền tiền; **`AccessError`** khi mất phạm vi.
   - **Đủ điều kiện:** đọc `tp.contract.line.amount` theo `revision_id` và `scope_key` bằng quyền user, không `sudo()`. ACL tiền gốc vẫn là lớp thứ hai.
   - **`_tp_capabilities` không đọc tiền.** Helper này chỉ dùng `sudo().search_count` để kiểm có tồn tại assignment và grant.
   - **Lý do không chỉ dựa vào `compute_sudo=False` hay ACL tiền gốc:** theo G7, manager có grant và còn đọc được project vẫn đọc được tiền gốc khi không có assignment. Chỉ guard này làm tiền hiển thị trong wizard khớp `_tp_capabilities` và restriction `amount.input` ở bước 3.
   - **Mọi kênh đều qua guard.** Vì không lưu, `read`, `web_read`, `onchange` và export đều tính lại kèm guard ở request hiện tại.
   - **Metadata không phụ thuộc guard.** User đủ quyền metadata nhưng không có `financial_read` vẫn đọc và sửa `scope_key`/`name` (AT-10g).
3. **Restriction tiền cho `amount.input`** (`crud`). Điều kiện bám `_tp_capabilities` cộng rule `line_amount_financial_reader`:
   `[('wizard_id.project_id', 'access', 'read'), ('wizard_id.project_id.tp_financial_read_granted', '=', True), ('wizard_id.project_id.tp_assignment_ids', 'any', [('user_id', '=', user.id), ('active', '=', True)])]`.
   - Từ request kế tiếp sau khi grant bị thu hồi (`active = False`), grant hết hạn (`date_end` trước hôm nay) hoặc assignment bị tắt, mọi thao tác trên `amount.input` của project đó bị lọc hoặc trả `AccessError`. Các thao tác gồm `read`, `search_read`, `web_read`, `read_group`, export, `write`, `unlink`, `create`.
   - User không có `financial_read` không tạo được `amount.input`.
   - Restriction không phụ thuộc group: manager mất assignment cũng bị chặn, dù ACL gốc vẫn cho manager đọc tiền gốc (G7, AT-10d).
4. **`default_get` và `onchange` chỉ trả metadata:** header, `scope_key`, `name`, version.
   - Hai method này không điền `amount.input` từ dữ liệu DB.
   - `default_*` cho trường tiền trong context bị bỏ qua.
   - Mọi đọc trong đó dùng quyền user, không dùng `sudo()`. `contract_id` ngoài phạm vi cho kết quả rỗng hoặc `AccessError`.
5. **Xác nhận thành công thì xóa tiền nhập.**
   - Trong cùng transaction: xóa các `amount.input` của wizard bằng quyền user (lúc đó `_tp_run` vừa kiểm `FINANCIAL_EDIT`), đặt `state = done`, lưu id kết quả.
   - Khi lỗi, dữ liệu nhập được giữ theo mục 11 và vẫn được bước 3 bảo vệ.
   - Vacuum transient chỉ là dọn dẹp, không phải lớp bảo vệ.
6. **Chống relink.**
   - Sau `create()`, các trường sau bất biến: `mode`, `contract_id`, `revision_id`, `project_id`, `company_id`, `expected_version`, `key`, và `wizard_id` của dòng. `write` chứa một trong các khóa này → `UserError`.
   - `copy()` → `UserError`.
   - Muốn đổi project trong luồng tạo thì đóng wizard và mở wizard mới.
   - Hợp đồng không đổi được project (`_tp_check_protected_write`, `tp_contract.py:74-88`). Vì vậy `project_id` đã lưu luôn khớp `contract_id.project_id`, và `action_confirm` vẫn kiểm lại.
7. **Giới hạn.** Không thu lại được dữ liệu đã tới trình duyệt trước khi thu hồi: màn hình đang mở, cache trình duyệt, file đã export. Bảo đảm chỉ bắt đầu từ request server kế tiếp.

### 9.4 Tạo wizard (`create`)

- `mode` khớp với model. Client không chọn action.
- **Đọc lại target bằng quyền user:**
  - contract qua `tp.contract.search([('id', '=', contract_id)])`;
  - revision phải thuộc contract;
  - project của luồng tạo phải `tp_managed` và đọc được.
  - Không thấy → `AccessError` với thông báo `not_found` (mục 9.6).
- **Server tự đặt `project_id`, `company_id`, `key`.** `project_id` và `company_id` lấy từ target. `key = 'native-' + uuid4().hex` sinh ở server. Giá trị client gửi cho ba trường này bị bỏ.
- **`expected_version` lấy từ giá trị `default_get` đã đưa ra form** (mục 10). Đây là token concurrency, không phải kiểm soát bảo mật: client gửi sai thì chỉ nhận `stale_version`.

Chi tiết native đã kiểm trong CHG-20261106-002: năm wizard dùng `force_save="1"` cho version readonly để `web_save` giữ token form. Nút từ contract/revision truyền `default_expected_version` của bản đang hiển thị; revision có related readonly `tp_contract_version`. Action sau transition bỏ context `default_*` cũ và mang `tp_native_version` mới để web client tải dữ liệu mới khi quay lại cùng revision. Không refresh token lúc create để che cập nhật đồng thời; browser stale thật vẫn bị chặn. Đây là cơ chế UI/cache, không đổi policy/action nghiệp vụ.

### 9.5 `action_confirm()`: method public duy nhất

`action_confirm(self)` không nhận tham số; tham số thừa qua `call_kw` gây lỗi. Thứ tự:

1. `ensure_one()`. Nếu `env.su` thì từ chối: method chỉ chạy bằng quyền user.
2. `check_access('write')` trên header và kiểm `create_uid == env.uid`. Sai → `AccessError`, không gọi `_tp_run`.
3. `state == 'done'` → trả action mở revision kết quả, đọc bằng quyền user. Không chạy lại workflow.
4. **Kiểm target:** `revision_id.contract_id == contract_id`, `project_id == contract_id.project_id`, `company_id == contract_id.company_id`. Sai → `AccessError`.
5. **Đếm tiền nhập.** Đếm `amount.input` của wizard bằng `sudo().search_count` (chỉ đếm), so với `self.amount_input_ids` đọc bằng quyền user. Lệch → `forbidden` (403); không gửi payload thiếu tiền.
6. **Dựng payload chỉ từ record của wizard**, đọc bằng quyền user:
   - dòng metadata gửi `scope_key` và `name`;
   - `scope_key` của `amount.input` phải có trong dòng của wizard;
   - context, `kwargs` và dữ liệu client khác không vào payload.
7. **Gọi workflow:** `_tp_run(action, payload, key=self.key, contract_id=self.contract_id.id, revision_id=self.revision_id.id, request_id=…)` bằng quyền user.
   - `_tp_run` tự suy project từ contract, kiểm revision thuộc contract và capability hiện tại (`tp_contract_workflow.py:268-319`).
   - Replay idempotency kiểm lại capability (`_tp_replay`).
8. **Thành công** → thực hiện bước 5 mục 9.3, rồi trả action mở form revision. Thông báo không chứa số tiền.

Không có method public nào nhận tên action tùy ý, nên `_tp_run` không mở ra RPC. Các method ORM chuẩn vẫn gọi được qua `call_kw` và chịu rule mục 9.2 và 9.3: `read`, `search_read`, `web_read`, `web_save`, `write`, `unlink`, `copy`, `export_data`, `read_group`.

### 9.6 Ánh xạ lỗi và kết quả

- **Ánh xạ lỗi** `ContractWorkflowError` (`exceptions.py`):
  - `403` → `AccessError`;
  - `404` → `AccessError`, với cùng thông báo "không tìm thấy hoặc ngoài phạm vi";
  - `400`, `409`, `422` → `UserError` mang thông báo tiếng Việt ở mục 11.
  - `ConcurrencyError` cùng khóa idempotency để Odoo tự thử lại; lần thử lại sẽ nhận kết quả replay.
- **Kết quả thành công:** đóng wizard và mở lại form revision kết quả. Không trả về số tiền trong thông báo.

## 10. Concurrency, version, idempotency, audit

- **Version:**
  - `default_get` đọc `contract.aggregate_version` bằng quyền user và đưa ra form. `create()` lưu giá trị đó, rồi giá trị trở thành bất biến (mục 9.3 bước 6).
  - `_tp_lock` khóa dòng (`SELECT … FOR UPDATE`); `_tp_guard` trả `409 stale_version` nếu version đã đổi.
  - UI báo "tải lại", đóng wizard; không tự gộp thay đổi.
  - Version là token concurrency, không phải kiểm soát quyền.
- **Idempotency:**
  - Server sinh `key = 'native-' + uuid4().hex` trong `create()`, đáp ứng `KEY_PATTERN`; giá trị client gửi bị bỏ (mục 9.4). Replay chỉ tra theo `user_id = env.uid`, nên khóa của user khác không dùng được.
  - Bấm hai lần, hoặc thử lại sau khi mất phản hồi, dùng cùng record wizard và cùng khóa → `_tp_replay` trả kết quả cũ (sau khi kiểm lại capability), không tạo bản trình thứ hai. Wizard đã `done` trả thẳng action kết quả (mục 9.5 bước 3).
  - Cùng khóa nhưng payload khác → `409 idempotency_conflict`.
  - Lỗi trước bước commit rollback cả bản ghi claim, nên sửa dữ liệu trong wizard rồi bấm lại vẫn hợp lệ.
- **Audit:**
  - Mỗi action ghi một `tp.contract.audit` gồm actor, thời điểm, `state_before`/`state_after`, `version_before`/`version_after`, `payload_sha256` (khi có lần trình) và lý do.
  - Audit append-only và cùng transaction: lỗi ghi lịch sử làm action rollback (`test_n08_history_write_failure_rolls_the_action_back`).
- **Thông báo:**
  - `tp.contract.outbox` là hộp thư trong ứng dụng.
  - Có thể thêm danh sách "Thông báo hợp đồng" chỉ đọc, lọc theo `recipient_id = user` (rule `outbox_recipient`).
  - Chưa có kênh email (`_tp_send` rỗng).

## 11. Lỗi và thông báo

Thông báo lấy theo mã lỗi; câu chữ dùng lại từ bản React cũ (`frontend/src/features/contracts/workflow.ts`). Các mã chưa có câu riêng thì dùng thông báo của server.

| Mã | Thông báo |
|---|---|
| `stale_version` | Hồ sơ vừa được cập nhật ở nơi khác. Tải lại bản mới nhất rồi thực hiện lại; thay đổi chưa được lưu. |
| `invalid_state` | Trạng thái bản hợp đồng đã thay đổi. Tải lại để xem trạng thái hiện tại. |
| `forbidden` | Bạn chưa được cấp quyền cho thao tác này trong phạm vi hợp đồng. |
| `not_found` | Không tìm thấy hồ sơ, hoặc hồ sơ nằm ngoài phạm vi được phân công. |
| `not_assigned_reviewer` | Chỉ người rà soát được giao cho lần trình này mới trả lại được. |
| `reviewer_ineligible` | Người rà soát đã chọn không còn đủ quyền rà soát hợp đồng này. |
| `submission_incomplete` | Chưa trình được: liệt kê `no_lines`, `amounts_not_confirmed`, `tax_basis_mixed` bằng câu tiếng Việt |
| `fix_summary_required` / `reason_required` / `issue_note_required` | Cần mô tả nội dung đã sửa / Cần nhập lý do / Mỗi ý kiến cần có nội dung |
| `scope_incomplete` | Dự án chưa có phòng ban chủ trì nên chưa tạo được hợp đồng. |
| `header_locked` | Thông tin chung chỉ sửa được ở bản gốc. |
| `duplicate_code`, `unknown_currency`, `unknown_partner`, `unknown_scope_key` | Câu tương ứng trong bản React cũ |
| `amount_*` | Giá trị đã xác nhận cần có số tiền / chưa xác nhận thì để trống / không được âm / quá nhiều chữ số / sai số chữ số thập phân |
| `idempotency_conflict` | Thao tác trùng với một yêu cầu khác. Vui lòng thử lại. |
| `invalid_request` (400) | Dữ liệu gửi lên chưa hợp lệ (kèm tên trường) |

Khi gặp lỗi, wizard vẫn mở với dữ liệu đã nhập, trừ `stale_version`/`invalid_state` là hai lỗi bắt buộc tải lại. Không dịch lỗi bằng cách đổi nhãn trong `addons/`.

## 12. Kênh có thể làm lộ dữ liệu

Cần kiểm và test các kênh sau:

- `search_read`, `read_group`, export, bộ lọc/nhóm;
- trường related và compute (tổng tiền phải tính bằng quyền user, không dùng `sudo` để đọc tiền);
- `/web/content` và ảnh xem trước tệp;
- tên tệp, chatter (tắt), thông báo outbox (không chứa tiền), nội dung audit (không chứa tiền);
- thông báo lỗi (không nêu số tiền hay tên tài liệu financial);
- in/báo cáo (không có báo cáo trong 001a).

- bản ghi transient của wizard: header, dòng, ý kiến, `amount.input` (mục 9.2, 9.3);
- `default_get`, `onchange`, `web_read` lồng dòng, `web_save` trả về giá trị.

**Thu hồi/hết hạn grant và tắt assignment** (A2, sửa D2 trong CHG-20261105-006). Phạm vi tác động khác nhau theo loại dữ liệu:

- **Tiền trong wizard** (`amount.input`, `current_amount_text`): bị chặn từ request kế tiếp với **mọi group, kể cả manager**, khi grant `financial_read` bị thu hồi hoặc hết hạn, **hoặc** khi assignment bị tắt. Cơ chế là restriction ở mục 9.3 bước 3 và guard ở bước 2.
- **Workflow:** mọi action chạy `_tp_capabilities`, nên mất assignment hoặc `financial_read` thì `action_confirm` có tiền trả 403, với mọi group.
- **Tiền gốc** (`tp.contract.line.amount`, tổng, tài liệu financial) theo ACL baseline hiện hành, không đổi trong đặc tả này:
  - thu hồi hoặc hết hạn grant: chặn từ request kế tiếp (`test_revoked_grant_applies_to_next_read`);
  - tắt assignment: chỉ chặn khi user mất luôn quyền đọc project, như staff;
  - manager còn đọc project và còn grant thì vẫn đọc được tiền gốc (G7).

  Vì vậy **không** tuyên bố mất assignment luôn chặn tiền gốc cho mọi group.

Từ chối lúc xác nhận là cần nhưng chưa đủ. Bảo vệ chính cho bản sao trong wizard là:

- không lưu bản sao tiền hiện có (mục 9.3 bước 1);
- guard capability cho tiền hiển thị (bước 2);
- restriction tiền trên `amount.input` (bước 3);
- restriction phạm vi dòng con (mục 9.2, D1);
- xóa tiền nhập khi thành công (bước 5).

Không tuyên bố thu lại dữ liệu đã tới trình duyệt trước đó (bước 7).

## 13. Giao diện, responsive, tiếng Việt

- Dùng view/action chuẩn (list, form, search, wizard). OWL chỉ dùng khi view chuẩn không đủ, ví dụ hiển thị `return_issues` theo dòng.
- Ở 360/390, 768, 1280/1440 và zoom 125/150: trang không tràn ngang; bảng dòng/tiền cuộn trong vùng của nó; wizard dùng được trên điện thoại; không chặn zoom.
- Nhãn theo `tp_contract/i18n/vi.po` (DEC-025), ví dụ "Nháp", "Đang rà soát", "Trả lại", "Trình rà soát", "Trình rà soát lại", "Trả lại để chỉnh sửa", "Bắt đầu chỉnh sửa lại", "Tài chính"/"Chung", "Chưa xác nhận".
- Không dùng chữ "duyệt", "đã ký", "hiệu lực" cho kết quả rà soát.

## 14. Acceptance tests (viết test trước khi code)

Tất cả chạy trên DB test với actor fixture DEC-020 (`TpContractWorkflowCommon`). Các ca trình duyệt chạy trên clone/test, ghi rõ nếu chỉ là Chromium emulation.

| ID | Ca kiểm tra | Kết quả mong đợi |
|---|---|---|
| AT-01 | Menu và danh sách theo actor | Ô `TP Contracts` có cho `group_user`; chỉ thấy hợp đồng của project được giao; khác project/company không thấy; trạng thái rỗng đúng câu |
| AT-02 | Tiền trên list/form/`read_group`/export | Không có `financial_read` → không có dòng tiền, tổng, tài liệu financial; có grant project A → chỉ thấy A; manager/admin không có tiền mặc định |
| AT-03 | Tạo nháp hợp đồng | Người soạn đầy đủ tạo được, kèm tiền; người soạn metadata tạo được khi không kèm tiền, tạo `amount.input` → `AccessError` (không có grant) hoặc 403 lúc xác nhận (có grant đọc nhưng thiếu `financial_draft_edit`); khác phòng ban → 403; project không có phòng ban → `scope_incomplete`; mã trùng → `duplicate_code` |
| AT-04 | Sửa nháp | Đúng version → version +1, có audit; version cũ → `stale_version`, không ghi gì; header của phụ lục → `header_locked`; revision không ở `draft` → nút ẩn, gọi thẳng → `invalid_state` |
| AT-05 | Trình/trình lại | Danh sách reviewer chỉ gồm người đủ điều kiện, loại người trình; thiếu dòng/chưa xác nhận tiền/khác cơ sở thuế → `submission_incomplete` có liệt kê vấn đề; trình lại thiếu `fix_summary` → 422; bấm hai lần → 1 submission, 1 audit, 1 outbox |
| AT-06 | Trả lại | Chỉ reviewer được giao thấy nút; người khác gọi → `not_assigned_reviewer`; thiếu lý do → 422; ý kiến có `scope_key` ngoài snapshot → 422; outbox chỉ người trình đọc được |
| AT-07 | Bắt đầu chỉnh sửa lại | Thiếu lý do → 422; `returned` → `draft`; `rework_*` ghi một lần; lần sau đã khóa |
| AT-08 | Tài liệu | Tài liệu financial và tên tệp không hiện với người không có grant; `/web/content` bị từ chối; tài liệu general theo project; tài liệu của revision đã trình không sửa/xóa được, kể cả qua `ir.attachment` |
| AT-09 | RPC trực tiếp | Gọi `_tp_run` hoặc các `_tp_*` qua `call_kw` → bị chặn; `write` vào `review_state`/`aggregate_version`/submission → `UserError`; tạo wizard với `contract_id` ngoài phạm vi → `AccessError`; `action_confirm` với tham số thừa → lỗi, không ghi gì; `copy()` wizard → `UserError` |
| AT-10a | Thu hồi `financial_read` — bản sao tiền (A2/D2) | **Chuẩn bị chung AT-10a..AT-10d:** wizard `edit` của user A đã `web_save` với một `amount.input` và một dòng metadata. Trước thay đổi, `current_amount_text` có giá trị. Mỗi ca chạy riêng, đọc ở **request mới** (làm mới env/access cache như request kế tiếp). Ca này: A là staff (`tp_core.group_user`), có assignment và grant; đặt grant `active = False`. Kỳ vọng: `amount.input` qua `read`/`search_read`/`web_read` (kể cả lồng `amount_input_ids`)/`read_group`/`export_data` → rỗng hoặc `AccessError`; `write`/`unlink`/`create` → `AccessError`; `current_amount_text` rỗng; `default_get`/`onchange` không có tiền; `action_confirm` có tiền → 403 `forbidden`, không audit/claim/đổi version; tiền gốc `tp.contract.line.amount` → không đọc được; header và dòng metadata vẫn đọc được vì A còn assignment |
| AT-10b | Hết hạn `financial_read` do đổi `date_end` (A2/D2) | Như AT-10a, nhưng nguyên nhân là `write` grant `date_end` = hôm qua qua ORM (`_invalidate_grant_access` chạy). Kỳ vọng giống AT-10a |
| AT-10c | Staff mất assignment và project access (A2/D2) | A là staff, grant giữ nguyên; đặt assignment `active = False`, A không còn đọc được project. Kỳ vọng: header, `draft.line`, `amount.input` → `AccessError`/0 theo AT-18; `current_amount_text` không đọc được (dòng bị chặn); `action_confirm` → `AccessError`, không audit/claim/đổi version; tiền gốc → không đọc được vì mất project access |
| AT-10d | Manager mất assignment, còn project access và `financial_read` (A2/D2, G7) | A có `tp_core.group_user` + `tp_core.group_manager`, grant `financial_read` còn hiệu lực; đặt assignment `active = False`. Kỳ vọng: A vẫn đọc được project, header và dòng metadata (không có tiền); `amount.input` → rỗng hoặc `AccessError` với mọi thao tác như AT-10a; `current_amount_text` **rỗng** do guard mục 9.3 bước 2 dù ACL gốc cho đọc; `default_get`/`onchange` không có tiền; `action_confirm` → 403 `forbidden` (`_tp_capabilities` rỗng), không audit/claim/đổi version. **Tiền gốc:** không kỳ vọng bị chặn; ghi nhận hành vi ACL baseline hiện hành (đọc được) như G7; nếu G7 được chốt siết thì đổi kỳ vọng cùng thay đổi ACL. **Đối chứng:** trong test, patch `_tp_amount_display_allowed` luôn trả `True` → khẳng định `current_amount_text` rỗng phải fail, chứng minh guard là thứ chặn |
| AT-10e | Không có baseline, xóa sau thành công | Kiểm schema: header, `draft.line`, `return.issue` không có cột tiền hay JSON payload; sau `action_confirm` thành công không còn `amount.input` của wizard (kiểm bằng `sudo().search_count`), `state = done`; gọi lại `action_confirm` trả action kết quả, không tạo audit thứ hai; `tp.contract.idempotency` chỉ có HMAC |
| AT-10f | Relink | `write` `contract_id`/`revision_id`/`project_id`/`company_id`/`mode`/`key`/`expected_version` của header, `wizard_id` của dòng hoặc `amount.input` → `UserError`; tạo `amount.input` trỏ tới wizard của project không có grant → `AccessError`; header có `project_id` lệch `contract_id.project_id` (dựng bằng SQL trong test) → `action_confirm` từ chối, không gọi `_tp_run` |
| AT-10g | Luồng metadata không cần `financial_read` (ID cũ AT-10d của CHG-20261105-004) | User chỉ có `contract_draft_edit`: `default_get`/`onchange`/`web_read` của wizard `edit` không có tiền, `current_amount_text` rỗng; đổi tên revision và tên dòng → thành công, audit đúng; payload không có khóa `amount`; số tiền trên DB không đổi |
| AT-11 | Ngoài phạm vi | Không có nút/route cho BASE verify, `review_complete`, ký, hiệu lực, hủy, thanh toán; `lifecycle_state` vẫn chỉ đọc |
| AT-12 | Responsive/console | Không tràn trang ở các kích thước trên; không có lỗi console hay request thất bại ngoài các ca 403 đã dự kiến; có ảnh chụp và đã xem |
| AT-13 | Hồi quy | Test `tp_contract`, `tp_planning_api` (contract) và React `features/contracts` cũ vẫn đạt; OpenAPI không đổi |
| AT-14 | Owner wizard qua ORM/RPC (A1) | Với **mỗi** model mục 9.1, user A tạo record. User B cùng project, cùng company, cùng capability gọi trên id của A: `read`, `search` (không thấy), `search_read`, `search_count` (0), `read_group`, `web_read`, `export_data`, `write`, `unlink`, `copy` → không thấy hoặc `AccessError`; `call_kw` `action_confirm` → `AccessError`, không có audit/claim/thay đổi version. Tạo `draft.line`/`return.issue`/`amount.input` với `wizard_id` của A → `AccessError` |
| AT-15 | Tổ hợp nhiều group (A1) | User B có `tp_core.group_user` + `tp_core.group_manager` + nhóm `hr_expense` (user/team approver, nếu module có trong DB test; không có thì ghi rõ đã bỏ) + `base.group_system` vẫn không đọc/ghi/xác nhận được wizard của A. Trong test, thêm tạm một dòng `ir.access` permission `crud` không domain cho một nhóm khác của B: vẫn bị restriction owner chặn. Gỡ owner restriction trong test thì test phải fail (chứng minh test có nghĩa) |
| AT-16 | Giả mạo target/payload (A1) | Tạo wizard với `revision_id` của hợp đồng khác `contract_id` → `AccessError`; `contract_id` ngoài phạm vi hoặc khác company → `AccessError` (`not_found`); `project_id`/`company_id`/`key` client gửi bị bỏ (giá trị lưu = target/server); `amount.input.scope_key` không có trong dòng wizard → từ chối; `scope_key` ý kiến ngoài snapshot → 422; context `default_amount_*` không tạo tiền |
| AT-17 | Hết hạn tự nhiên theo ngày | Grant có `date_end = hôm nay`; giả lập sang ngày kế tiếp **không ghi** `tp.project.grant` (không gọi `_invalidate_grant_access`); request mới không đọc được `amount.input` và `tp.contract.line.amount`, `current_amount_text` rỗng (guard dùng `_active_grant_domain` theo `context_today`). Nếu cache access giữ kết quả cũ thì ghi lỗi/rủi ro (G8), không tuyên bố đạt |
| AT-18 | Owner mất quyền đọc project — dòng con (D1) | **Khác AT-14** (khác owner) và **khác AT-16** (khác company/target): A vẫn là owner, vẫn cùng company. A là staff, tạo wizard `edit` có `draft.line` và wizard `return` có `return.issue` (A là reviewer được giao), rồi tắt assignment của A → A không đọc được project. Ở request mới, với **mỗi** model con, theo id cụ thể: `read` → `AccessError`; `search([('id', '=', id)])` rỗng; `search_count` → 0; `search_read`/`read_group` rỗng; `export_data` → `AccessError` hoặc rỗng; `web_read` → `AccessError`; `write`/`unlink` → `AccessError`; `create` dòng mới với `wizard_id` đó → `AccessError`. Header: `read` và `web_read` lồng `line_ids`/`issue_ids` → `AccessError`; không phản hồi nào chứa tên dòng hay nội dung ý kiến. **Đối chứng:** trong transaction test, gỡ **riêng** dòng `ir.access` `[('wizard_id', 'access', 'read')]` của model con, giữ owner/company, làm mới access cache → các khẳng định âm trên model con phải fail (đọc được, `search_count` 1), chứng minh restriction phạm vi là thứ chặn |

## 15. Gaps và câu hỏi còn mở

| ID | Nội dung | Ảnh hưởng |
|---|---|---|
| G1 | Không có action/capability để upload, phân loại hay thay tài liệu; chưa quyết định ai upload tài liệu general hay financial, ai được hạ mức `financial` → `general`, loại/kích thước tệp, quét mã độc | **Chặn phần upload**; 001a chỉ xem/tải. Cần người dùng quyết định trước khi đặc tả 001b |
| G2 | Không có action hủy revision nháp (`cancelled`) hoặc thay reviewer khi reviewer mất quyền trong lúc `in_review` | Revision có thể bị kẹt ở `in_review`; 001a chỉ hiển thị. Cần chính sách (DEC-020 đã loại "cancel revision") |
| G3 | `review_complete`, BASE, ký, hiệu lực, lifecycle không có action trong phạm vi | Chỉ hiển thị; không mở |
| G4 | Ô `TP Contracts` hiện với mọi `group_user`, kể cả người chưa có hợp đồng nào | Không chặn; ẩn theo assignment cần quyết định UX, không tạo nhóm mới |
| G5 | Lý do và ý kiến là văn bản tự do; người dùng có thể tự gõ số tiền vào đó | Không chặn; cần hướng dẫn sử dụng hoặc chính sách nội dung |
| G6 | Q2 (DEC-020) còn mở: chưa có actor thật hay ủy quyền | Chặn người thật/pilot, không chặn code/test trên DB test |
| G7 | Rule hiện có `line_amount_financial_reader` chỉ cần project đọc được và có grant `financial_read`. Manager đọc được mọi project managed, nên manager có grant nhưng không có assignment vẫn đọc được tiền gốc, trong khi `_tp_capabilities` yêu cầu assignment. Probe rollback của audit delta CHG-20261105-005 xác nhận: tắt assignment thì đọc tiền gốc vẫn được nhưng workflow mất `financial_read`; thu hồi thêm grant thì hết đọc | **Quyết định policy riêng, chưa chốt.** Không đổi ACL gốc, grant/capability hay backend trong correction. Riêng wizard dùng điều kiện chặt hơn: restriction `amount.input` và guard `current_amount_text` yêu cầu assignment (mục 9.3 bước 2–3). AT-10d ghi nhận hành vi baseline của tiền gốc. Mất assignment **không** luôn chặn tiền gốc cho mọi group (mục 12) |
| G8 | Gate ban đầu: cần kiểm grant hết hạn tự nhiên qua ngày, không ghi `tp.project.grant`, với cache request mới | **Đạt kỹ thuật CHG-20261106-002, chờ audit implementation:** AT-17 warm ngày06, freeze sang07, không write/invalidate grant lúc đổi ngày; flush/env.clear mô phỏng request mới; input/tiền gốc bị chặn, compute rỗng. Không thay G7 hoặc thu lại dữ liệu browser đã nhận |

## 16. Kết luận

**`IMPLEMENTED_VERIFIED_TEST_PENDING_AUDIT` cho UI-CTR-NATIVE-001a, CHG-20261106-002.** Correction CHG-20261105-004/006 được audit CHG-20261106-001 chấp nhận về đặc tả D1/D2; A3 runner đạt audit005. Implementation đã tự kiểm trên clone, chờ phiên khác audit source/evidence; chưa business/pilot hoặc áp dev.

- Mọi action, state, capability, kiểm tra version/idempotency/audit và quyền đọc tiền/tệp gốc đều đã có trong backend, có tên method và test hiện có làm căn cứ.
- Correction đã bổ sung phần còn thiếu:
  - owner và phạm vi wizard bằng restriction tường minh, gồm restriction `wizard_id access read` cho dòng con (mục 9.2, D1);
  - thiết kế bản sao tiền không baseline: guard capability cho `current_amount_text`, restriction theo grant/assignment hiện tại cho `amount.input` (mục 9.3, D2);
  - kiểm owner/target/payload ở `create` và `action_confirm` (mục 9.4, 9.5);
  - acceptance AT-10a..AT-10g và AT-14..AT-18.
- G7 vẫn là policy mở; đặc tả không đổi ACL tiền gốc.
- Phần cần làm: view, menu, wizard và các model ở mục 9, cộng acceptance test ở mục 14.

Thứ tự code sau khi audit delta đã chấp nhận, thực hiện theo prompt UI-CTR-NATIVE-001a:

1. Viết test AT-01..AT-11 và AT-14..AT-18 ở tầng Odoo. Test owner/restriction/guard phải fail khi gỡ restriction hoặc guard tương ứng.
2. Thêm model wizard, `ir.access` mục 9.2/9.3 và view.
3. Chạy test trình duyệt AT-12.

**Chưa sẵn sàng:** upload/phân loại tài liệu (G1) và mọi thứ ở G2/G3. Không triển khai lên dev, không cấp grant cho người thật, không pilot.
