# KD-UI-007 — Inventory bảng KH-KD

Ngày 07/11/2026. Đối chiếu source và view đã resolve trên clone owned18889: **38 view /43 table**, trong đó **36 view /41 table** thuộc KH-KD; 2 view/2 table TP Projects ngoài app dùng đối chiếu scope. Các table là vị trí hiển thị, không phải41model. Actor editor cho hồ sơ, planner có group_manager cho phân công. Bằng chứng private: `.local/kd-ui007/inventory-after.json`, `arch-after/`; baseline `inventory-before.json`, `arch-before/` trước sửa.

**15 list chính/hỗ trợ +26 bảng con**, gồm5bảng snapshot tiền tại popup lịch sử mà trước đây Odoo tự sinh chỉ cột ID. Quyền đọc/ghi do ACL/rule/grant backend hiện có; không cấp thêm quyền. Snapshot/history/audit chỉ đọc. Bảng giá trị chỉ hiện khi parent có quyền tiền; no-money actor không nhận giá trị ở RPC/DOM.

| View/entrypoint | Model bảng | Vị trí | Trường lọc phù hợp/searchable trong các cột | Field tình trạng | Phân trang/guard |
| --- | --- | --- | --- | --- | --- |
| `tp_kd_workspace.acceptance_form` | `tp.acceptance.amount` | `amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.acceptance_form` | `tp.acceptance.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.acceptance_form` | `tp.acceptance.event.amount` | `event_ids.amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.acceptance_list` | `tp.acceptance` | `list` | `code`, `name`, `project_id`, `round_code`, `period_from`, `period_to`, `state`, `date_due`, `owner_id`, `production_id`, `counterparty_id`, `contract_id` | `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.allocation_form` | `tp.allocation` | `child_ids` | `code`, `name`, `state` | `state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.allocation_form` | `tp.allocation.amount` | `amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.allocation_form` | `tp.allocation.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.allocation_form` | `tp.allocation.event.amount` | `event_ids.amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.allocation_list` | `tp.allocation` | `list` | `code`, `name`, `project_id`, `allocation_kind`, `contract_id`, `state`, `date_due`, `owner_id`, `recipient_department_id`, `partner_id`, `parent_id`, `period_from`, `period_to` | `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.credential_form` | `tp.credential.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.credential_list` | `tp.credential` | `list` | `code`, `name`, `subject_id`, `credential_kind`, `valid_to`, `state`, `project_id`, `subject_kind`, `valid_from`, `period_from`, `period_to`, `owner_id`, `date_due` | `expiry_status`, `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.obligation_form` | `tp.obligation.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.obligation_list` | `tp.obligation` | `list` | `code`, `name`, `project_id`, `obligation_kind`, `checklist_status`, `state`, `date_due`, `contract_id`, `period_from`, `period_to`, `owner_id` | `checklist_status`, `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.opportunity_list` | `crm.lead` | `list` | `name`, `partner_id`, `kd_bid_state`, `kd_deadline`, `user_id`, `kd_route`, `tp_project_id`, `kd_source`, `kd_scope` | `kd_bid_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.payment_form` | `tp.payment.request.amount` | `amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.payment_form` | `tp.payment.request.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.payment_form` | `tp.payment.request.event.amount` | `event_ids.amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.payment_list` | `tp.payment.request` | `list` | `code`, `name`, `project_id`, `direction`, `partner_id`, `state`, `date_due`, `payment_basis`, `reconciliation_state`, `acceptance_id`, `period_from`, `period_to`, `owner_id` | `state`, `reconciliation_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.plan_form` | `tp.periodic.plan.amount` | `amount_ids` | `measure`, `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.plan_form` | `tp.periodic.plan.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.plan_form` | `tp.periodic.plan.event.amount` | `event_ids.amount_ids` | `measure`, `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.plan_list` | `tp.periodic.plan` | `list` | `code`, `name`, `project_id`, `period_kind`, `period_from`, `period_to`, `state`, `date_due`, `owner_id` | `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.production_form` | `tp.production.amount` | `amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.production_form` | `tp.production.event` | `event_ids` | `actor_id`, `acted_at`, `action`, `state_before`, `state_after`, `reason`, `fix_summary` | `state_before`, `state_after` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.production_form` | `tp.production.event.amount` | `event_ids.amount_ids` | `amount_state`, `currency_id`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.production_list` | `tp.production` | `list` | `code`, `name`, `project_id`, `period_from`, `period_to`, `state`, `date_due`, `owner_id`, `allocation_id`, `contract_id`, `reconciliation_state`, `unit` | `state`, `reconciliation_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.project_form` | `tp.project.assignment` | `tp_assignment_ids` | `user_id`, `role` | Không tạo state | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_kd_workspace.kd_task_list` | `project.task` | `list` | `name`, `project_id`, `parent_id`, `kd_responsible_id`, `date_deadline`, `kd_deliverable`, `state` | `state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_contract.view_audit_list` | `tp.contract.audit` | `list` | `acted_at`, `actor_id`, `action`, `revision_id`, `state_before`, `state_after`, `reason` | `state_before`, `state_after` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_contract.view_document_list` | `tp.contract.document` | `list` | `name`, `document_kind`, `confidentiality`, `revision_id`, `file_name` | Không tạo state | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_contract.view_amount_list` | `tp.contract.line.amount` | `list` | `line_id`, `amount_state`, `tax_basis`, `currency_id` | `amount_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_contract.view_native_draft_form` | `tp.contract.native.draft.line` | `line_ids` | `scope_key`, `name` | Không tạo state | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_native_draft_form` | `tp.contract.native.amount.input` | `amount_input_ids` | `scope_key`, `amount_state`, `value`, `tax_basis` | `amount_state` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_contract_form` | `tp.contract.revision` | `revision_ids` | `revision_kind`, `name`, `reference`, `review_state`, `signature_status`, `effectivity_status` | `review_state`, `signature_status`, `effectivity_status` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_contract_list` | `tp.contract` | `list` | `code`, `name`, `project_id`, `partner_id`, `contract_type`, `department_id`, `lifecycle_state` | `lifecycle_state`, `tp_latest_review_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_contract.view_native_return_form` | `tp.contract.native.return.issue` | `issue_ids` | `scope_key`, `note` | Không tạo state | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_revision_form` | `tp.contract.line` | `line_ids` | `scope_key`, `name`, `work_item_id`, `change_kind`, `previous_line_id` | Không tạo state | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_revision_form` | `tp.contract.submission` | `submission_ids` | `submitted_by_id`, `submitted_at`, `reviewer_id`, `outcome`, `fix_summary`, `return_reason` | `outcome` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_revision_form` | `tp.approval.reference` | `approval_reference_ids` | `reference_kind`, `base_reference`, `decision`, `verification_state`, `authority_status` | `decision`, `verification_state`, `authority_status` | Relation 10/20/50/100; lọc readonly toàn currentIds; khóa khi new/dirty |
| `tp_contract.view_revision_list` | `tp.contract.revision` | `list` | `contract_id`, `revision_kind`, `name`, `reference`, `review_state` | `review_state` | Native server limit/offset 10/20/50/100; mặc định20 |
| `tp_kd_workspace.kd_project_list` | `project.project` | `list` | `tp_code`, `name`, `partner_id`, `tp_department_id`, `company_id`, `date_start`, `date`, `user_id`, `kd_deadline`, `last_update_status` | Không tạo state | Native server limit/offset 10/20/50/100; mặc định20 |

Search chính giữ field/domain của search view native. Ô Trường lọc chỉ tạo domain trên metadata searchable thuộc whitelist; danh sách trên là các cột searchable, không hứa mọi cột đều là ô lọc nhanh. `expiry_status` là Char compute không searchable: màu theo valid_to, lọc Hết hạn theo ngày `valid_to`; không domain thẳng expiry_status. Ngày lọc đến hết ngày theo timezone native. Không có filter tiền/số tiền/attachment binary, không enumerate tên ngoài scope.

| Menu/action | Model/view/controller/search |
| --- | --- |
| Cơ hội — `action_opportunities` | crm.lead /opportunity_list +opportunity_form +opportunity_search /KdTableController |
| Dự án — `action_projects` | project.project /kd_project_list +project_form /KdProjectListController giữ ProjectListController /search native |
| Hợp đồng — menu server TP Contracts | tp.contract /view_contract_list +view_contract_form +view_contract_search /KdTableController chỉ bật trong KH-KD |
| Công việc — `action_tasks` | project.task /kd_task_list +kd_task_form +kd_task_search /KdListController giữ create/delete/duplicate guard |
| Giao khoán, Sản lượng, Nghiệm thu, Thanh toán, Kế hoạch, Chứng chỉ, Nghĩa vụ | action_allocations/productions/acceptances/payments/plans/credentials/obligations; list/search/form tương ứng ở bảng trên /KdListController +KdReviewFormController giữ version/save/beacon |
| Smart button hợp đồng | Tài liệu, audit, số tiền; phiên bản qua Tổng quan → danh sách hoặc revision_ids → modal. Domain/quyền/action backend giữ nguyên |
| Bảng con | KdRelationField kế thừa X2ManyField; list gốc giữ ORM commands, native pager. Dialog lọc clone arch readonly, domain toàn ID liên quan và backend áp quyền lại |

## Tổng quan/Báo cáo và ngoại lệ có lý do

Hai menu dùng action Tổng quan hiện có. Không dựng báo cáo mới hoặc thay công thức.

| Vùng | Dòng/giới hạn thật | Cách tìm/lọc/xem tiếp |
| --- | --- | --- |
| Bảng điều hành dự án | Danh sách record; total theo scope | Search mã/tên/khách hàng +filter chung; server size10/20/50/100, sort/cột/row action native giữ |
| Việc của tôi | Record hợp nhất từ nguồn; MERGE_MAX500 | Tab review/returned/due +filter chung, size10/20/50/100; pager dừng ở500 và giải thích thu hẹp lọc/mở nguồn |
| Bảng nguồn |10nhóm nguồn cấu trúc cố định theo quyền | Ghi rõ10nhóm; filter chung/count đúng scope; click count mở list có filter/size. Không pager giả cho10nhóm |
| G01/donut |7nguồn ×3state; legend3state | Cấu trúc tổng hợp, không phải row hồ sơ; filter chung/click segment mở list native |
| Công việc theo dự án | Biểu đồ theo dự án, thu gọn8/hiện tất cả | Giữ nút xem toàn bộ và số đang xem; click project/segment mở task list có filter/size |
| Cơ hội |3bước đấu thầu +1nhóm giao trực tiếp | Cấu trúc tổng hợp; filter chung/click số → list native; submitted vẫn chưa xác minh |
| So sánh kế hoạch | Biểu đồ record tối đa12kế hoạch gần nhất theo kỳ/quyền tiền, có in_scope/excluded/more | Ghi rõ giới hạn12; nút “Mở danh sách để tìm, lọc và phân trang” dùng action source hiện có. Không đổi backend công thức/cap để làm pager giả trên12dòng đã tải |
| Chứng chỉ |3bucket hạn; danh sách gần nhất tối đa5record | Ghi rõ5; nút mở **tất cả hồ sơ sắp hết hạn** dùng backend domain ngày hiện có rồi lọc/phân trang native; không coi bucket còn hạn là xác minh |
| Wizard/inline mới hoặc bẩn | Dòng chưa lưu chưa có tậpID ổn định | Disable bộ lọc/size với “Lưu thay đổi để lọc”; giữ add/edit/ORM commands/save/discard native. Wizard xác nhận theo action gốc, không tự save để lọc |
| Tags năng lực và trường văn bản checklist | Không phải record table | Giữ tags/private links/textarea và guard; không tạo pager cho văn bản |

Ca acceptance A01–A12, ảnh từng nhóm, popup, trang2, grouped, saved filter, dirty, scope âm và zoom thật được ghi tại [acceptance](../demo/KD_UI_007_ACCEPTANCE.md). Tổng quan không bị thay bằng mockup; bảng cấu trúc/biểu đồ luôn có số dòng/giới hạn và đường sang list đầy đủ khi phù hợp.
