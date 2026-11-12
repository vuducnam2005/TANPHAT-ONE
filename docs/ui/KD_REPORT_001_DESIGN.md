# KD-REPORT-001 — Thiết kế Trung tâm Báo cáo KH-KD độc lập

Tài liệu này quy định kiến trúc, phân ranh nghiệp vụ, nguồn dữ liệu, công thức tổng hợp, phân quyền, giao diện và xuất Excel của **Báo cáo KH-KD** (`tp_kd_workspace.action_reports`), tách độc lập khỏi **Tổng quan KH-KD** (`tp_kd_workspace.action_overview`).

---

## 1. Phân ranh vai trò hai màn hình

| Tiêu chí | Tổng quan KH-KD (`menu_overview`) | Báo cáo KH-KD (`menu_reports`) |
|---|---|---|
| **Mục đích** | Bàn làm việc điều hành hằng ngày: xem tình hình hiện tại, hộp việc cá nhân (`Việc của tôi`), tạo hồ sơ mới, đi thẳng vào xử lý. | Trung tâm báo cáo theo kỳ, đối chiếu số liệu đa chiều, nhóm dữ liệu, mở hồ sơ đối chiếu và xuất Excel toàn bộ kết quả đã lọc. |
| **Menu & Action XML ID** | `tp_kd_workspace.menu_overview` → `tp_kd_workspace.action_overview` | `tp_kd_workspace.menu_reports` → `tp_kd_workspace.action_reports` |
| **Model & View `js_class`** | `tp.kd.overview` (`js_class="tp_kd_overview"`, root `.o_tp_kd_ov`) | `tp.kd.report.center` (`js_class="tp_kd_report_center"`, root `.o_tp_kd_rc`) |
| **Thao tác chính trên thanh đầu** | `Tạo hồ sơ`, `Làm mới`, `Xem dữ liệu`, `Tùy chọn hiển thị`. | `Áp dụng bộ lọc`, `Đặt lại`, `Làm mới`, `Xuất Excel` (không đặt nút `Tạo hồ sơ`). |
| **Cách lọc dữ liệu** | Lọc tức thời trên phạm vi làm việc hằng ngày. | Bộ lọc kỳ báo cáo (`Tháng này`, `Quý này`, `Năm nay`, `Tùy chọn` `date_from`–`date_to`), dự án, người phụ trách/rà soát, trạng thái/loại; phân biệt rõ bộ lọc đang chọn (pending) và bộ lọc đã áp dụng (applied). |

---

## 2. Đặc tả nghiệp vụ và nguồn dữ liệu 6 nhóm báo cáo (`R01`–`R06`)

### R01 — Báo cáo Dự án và Hợp đồng (`projects_contracts`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Có bao nhiêu dự án trong phạm vi quyền? Mỗi dự án có bao nhiêu hợp đồng, phụ lục điều chỉnh và bản đính chính?
   - Những hợp đồng nào đã ghi nhận hiệu lực (`effective`) so với chưa hiệu lực (`not_effective`) hoặc đang rà soát?
   - Giá trị hợp đồng gốc, giá trị biến động theo phụ lục và giá trị tại phiên bản hiệu lực hiện hành là bao nhiêu (theo đúng tiền tệ và cơ sở thuế)?
3. **Nguồn model/field thực tế**:
   - `project.project`: `id`, `name`, `tp_code`, `company_id`, `user_id`, `partner_id`, `date_start`, `date`.
   - `tp.contract`: `id`, `code`, `name`, `project_id`, `company_id`, `partner_id`, `contract_type` (`revenue`/`cost`), `lifecycle_state`, `tp_latest_review_state`, `revision_ids`.
   - `tp.contract.revision`: `id`, `contract_id`, `sequence`, `revision_kind` (`original`/`amendment`/`correction`), `review_state`, `signature_status`, `signature_authority_status`, `effectivity_status`, `effective_date`, `signed_date`, `submitted_by_id`, `reviewer_id`, `line_ids`.
   - `tp.contract.line` & `tp.contract.line.amount`: `amount_state` (`unconfirmed`/`confirmed`), `tax_basis` (`before_tax`/`after_tax`/`unspecified`), `currency_id`, `amount` (qua `revision._amount_summary()`).
4. **Trường ngày lọc theo kỳ**:
   - Lọc theo ngày hiệu lực `effective_date` của phiên bản hợp đồng; nếu phiên bản chưa có `effective_date` thì đối chiếu `signed_date` hoặc `create_date` của phiên bản (ghi rõ cơ sở ngày trong mô tả báo cáo và dòng chi tiết).
5. **Trường người phụ trách / rà soát**:
   - Dự án: `project.user_id`; Phiên bản hợp đồng: `submitted_by_id` (người trình) và `reviewer_id` (người rà soát).
6. **Trạng thái và ý nghĩa**:
   - Tách 4 lớp trạng thái độc lập của hợp đồng/phiên bản:
     - Rà soát nội bộ (`review_state`): `draft`, `in_review`, `returned`, `review_complete`, `cancelled`.
     - Ký kết (`signature_status`): `unsigned` (`Chưa ký`), `signed_recorded` (`Đã ghi nhận bản ký`).
     - Thẩm quyền ký (`signature_authority_status`): `pending`, `confirmed`.
     - Hiệu lực (`effectivity_status` / `lifecycle_state`): `not_effective`, `effective_recorded` / `effective`, `suspended`, `execution_completed`, `liquidated`, `terminated`.
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - Bảng chi tiết hiển thị ở hạt độ **Hợp đồng (`tp.contract`)** kèm số lượng phiên bản (`original`, `amendment`, `correction`), phiên bản hiệu lực hiện hành (`_effective_revision`) và phiên bản mới nhất (`_latest_revision`).
   - Hỗ trợ nhóm theo: Dự án (`project`), Loại hợp đồng (`contract_type`), Trạng thái vòng đời (`lifecycle_state`), Trạng thái rà soát (`review_state`).
   - **Cấm cộng trùng**: Không bao giờ cộng tổng tất cả các `tp.contract.revision` của cùng một hợp đồng với nhau. Giá trị hợp đồng hiệu lực chỉ lấy từ phiên bản hiệu lực hiện hành (`_effective_revision`, có `effectivity_status == 'effective_recorded'` và `review_state != 'cancelled'`). Giá trị hợp đồng gốc lấy từ phiên bản `original` (`sequence == 0`). Phiên bản đang `draft`/`in_review`/`returned` được hiển thị ở cột trạng thái/phiên bản đang xử lý, không cộng gộp vào tổng giá trị hợp đồng hiệu lực.
8. **Đơn vị tính / tiền tệ / VAT**:
   - Tiền chỉ cộng tổng khi phiên bản có `_amount_summary()['state'] == 'confirmed'` và cùng cặp `(currency_id, tax_basis)`.
   - Hợp đồng có dòng tiền `unconfirmed`, `mixed_basis` hoặc `empty` được giữ nguyên nhãn (`Chưa xác nhận đủ dòng tiền`, `Khác cơ sở thuế`, `Chưa kê khai tiền`) và đếm vào bộ đếm `excluded_from_money_total`, tuyệt đối không đổi thành `0`.
9. **Quy tắc quyền**:
   - Phạm vi dự án/hợp đồng theo record rule hiện hành (`tp.project.assignment` active).
   - Quyền xem tiền theo `tp.project.grant._tp_has_capability(project, "financial_read")` và ACL `tp.contract.line.amount`. Nếu không có quyền xem tiền tại dự án, cột tiền trả về `allowed: false`, nhãn `"Không có quyền xem tiền"`.
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Giá trị thanh quyết toán cuối cùng và doanh thu kế toán ghi sổ chưa có chứng từ hạch toán xác minh.
11. **Drill-down**:
    - Mở form `tp.contract` hoặc danh sách `tp_contract.action_tp_contracts_list` / `project.project` với domain tương ứng.

---

### R02 — Báo cáo Cơ hội và Hồ sơ thầu (`opportunities_bidding`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Có bao nhiêu cơ hội/hồ sơ thầu đang ở bước Đã nhận diện (`identified`), Đang chuẩn bị (`preparation`), Đã khai báo nộp (`submitted`)?
   - Cơ hội nào gắn với dự án, cơ hội nào là cơ hội tiền dự án (`tp_project_id = False`)?
   - Cơ hội nào sắp đến hạn hoặc quá hạn nộp (`kd_deadline`)?
3. **Nguồn model/field thực tế**:
   - `crm.lead` (`type = 'opportunity'`, `kd_accessible = True`): `id`, `name`, `tp_project_id`, `company_id`, `partner_id`, `user_id`, `kd_bid_state` (`identified`/`preparation`/`submitted`), `kd_route`, `kd_source`, `kd_scope`, `kd_checklist`, `kd_deadline`, `kd_receipt`, `kd_credential_link_ids`, `expected_revenue`, `company_currency`.
4. **Trường ngày lọc theo kỳ**:
   - Lọc theo hạn nộp hồ sơ thầu `kd_deadline` (hoặc tùy chọn lọc theo ngày tạo `create_date` khi đối chiếu nguồn). Mặc định lọc theo `kd_deadline`; các cơ hội chưa có `kd_deadline` được thống kê rõ số lượng khi áp dụng lọc ngày.
5. **Trường người phụ trách / rà soát**:
   - `user_id` (Người phụ trách cơ hội).
6. **Trạng thái và ý nghĩa**:
   - `identified`: `Đã nhận diện`
   - `preparation`: `Đang chuẩn bị`
   - `submitted`: `Đã khai báo nộp — chưa xác minh` (hiển thị nguyên văn nhãn để không hiểu nhầm là đã trúng thầu hay đã xác minh biên nhận bên ngoài).
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - Hạt độ dòng: Mỗi `crm.lead` là 1 dòng.
   - Nhóm theo: Trạng thái hồ sơ thầu (`kd_bid_state`), Dự án / Tiền dự án (`project`), Người phụ trách (`owner`), Hướng thực hiện (`kd_route`).
   - Khi không lọc dự án cụ thể: bao gồm cả cơ hội gắn dự án trong phạm vi và cơ hội tiền dự án (`tp_project_id = False`) mà người dùng được phân công (`user_id = uid` + `tp.kd.grant` `opportunity_prepare`/`opportunity_submit`). Có tùy chọn lọc riêng `"Chưa gắn dự án (tiền dự án)"`.
8. **Đơn vị tính / tiền tệ / VAT**:
   - Trường `expected_revenue` là giá trị dự kiến ban đầu theo `company_currency` (chưa tách cơ sở thuế VAT, chỉ mang tính dự kiến). Chỉ cộng tổng các cơ hội mà người dùng có quyền `financial_read` trên `tp_project_id`; cơ hội tiền dự án (`tp_project_id = False`) không có grant tài chính dự án nên luôn hiển thị `"Không có quyền xem tiền"` / tách khỏi tổng tiền xác nhận.
9. **Quy tắc quyền**:
   - Tuân thủ `_search_kd_accessible` và `OpportunityMoney` trong `opportunity_access.py`. Vai trò `support` (không có `financial_read`) không nhận bất kỳ số tiền nào.
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Kết quả trúng/trượt thầu chính thức, tỷ lệ thắng thầu (`probability` không dùng làm căn cứ), biên nhận nộp thầu bên ngoài (`kd_receipt` chỉ là thông tin khai báo nội bộ).
11. **Drill-down**:
    - Mở form `crm.lead` hoặc danh sách `tp_kd_workspace.action_opportunities`.

---

### R03 — Báo cáo Kế hoạch, Sản lượng, Nghiệm thu và Đề nghị thanh toán (`plan_production_acceptance_payment`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Trong kỳ và theo từng dự án, kế hoạch sản lượng (`tp.periodic.plan`), sản lượng thực hiện (`tp.production`), giá trị nghiệm thu (`tp.acceptance`) và đề nghị thanh toán (`tp.payment.request`) đang ở trạng thái nào?
   - Từng dự án có thể đối chiếu Kế hoạch sản lượng so với Sản lượng đang rà soát hay không (`comparable`, `no_data`, `unknown`, `no_posted_evidence`)?
   - Đề nghị thanh toán tách biệt Thu (`receipt`) và Chi (`disbursement`), Tạm ứng (`advance`) và Nghiệm thu (`acceptance`) như thế nào?
3. **Nguồn model/field thực tế**:
   - `tp.periodic.plan` & `tp.periodic.plan.amount`: `code`, `name`, `project_id`, `period_kind`, `period_from`, `period_to`, `state`, `owner_id`, `reviewer_id`, `measure` (`production`/`revenue`), `target_amount`, `amount_state`, `tax_basis`, `currency_id`, `source_amount`, `source_status`.
   - `tp.production` & `tp.production.amount`: `code`, `name`, `project_id`, `contract_id`, `allocation_id`, `period_from`, `period_to`, `work_item`, `quantity`, `uom_name`, `state`, `reconciliation_state`, `owner_id`, `reviewer_id`, `amount_id`.
   - `tp.acceptance` & `tp.acceptance.amount`: `code`, `name`, `project_id`, `contract_id`, `production_id`, `acceptance_date`, `document_ref`, `state`, `reconciliation_state`, `owner_id`, `reviewer_id`, `amount_id`.
   - `tp.payment.request` & `tp.payment.request.amount`: `code`, `name`, `project_id`, `contract_id`, `acceptance_id`, `partner_id`, `direction` (`receipt`/`disbursement`), `payment_basis` (`advance`/`acceptance`), `request_date`, `date_due`, `state`, `reconciliation_state`, `owner_id`, `reviewer_id`, `amount_id`.
4. **Trường ngày lọc theo kỳ**:
   - `tp.periodic.plan` và `tp.production`: giao khoảng kỳ (`period_to >= date_from` và `period_from <= date_to`).
   - `tp.acceptance`: `acceptance_date` trong `[date_from, date_to]`.
   - `tp.payment.request`: `request_date` trong `[date_from, date_to]`.
5. **Trường người phụ trách / rà soát**:
   - `owner_id` (Người lập/phụ trách) và `reviewer_id` (Người rà soát).
6. **Trạng thái và ý nghĩa**:
   - Trạng thái rà soát (`state`): `draft` (`Nháp`), `in_review` (`Đang rà soát`), `returned` (`Bị trả lại`).
   - Trạng thái đối chiếu (`reconciliation_state`): `unreconciled` (`Chưa đối chiếu`), `needs_evidence` (`Cần bổ sung chứng từ`), `pending` (`Chờ đối chiếu kế toán`), `missing_documents` (`Thiếu hồ sơ`), `internal_checked` (`Đã kiểm tra nội bộ — chưa ghi nhận thu/chi`).
   - Trạng thái đối chiếu kế hoạch (`source_status`): `comparable` (`Cùng đơn vị tiền và thuế`), `no_data` (`Chưa có sản lượng đang rà soát`), `unknown` (`Chưa cùng cơ sở hoặc chưa xác nhận`), `no_posted_evidence` (`Chưa có chứng từ doanh thu ghi sổ`).
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - **Cấm cộng gộp xuyên giai đoạn**: Không bao giờ cộng `Kế hoạch + Sản lượng + Nghiệm thu + Đề nghị thanh toán` thành một con số tổng. Không cộng gộp Đề nghị thu (`receipt`) với Đề nghị chi (`disbursement`).
   - Báo cáo trình bày:
     - Bảng đối chiếu theo Dự án / Giai đoạn (tách riêng cột cho Kế hoạch sản lượng, Sản lượng thực hiện, Nghiệm thu, Đề nghị thu, Đề nghị chi theo đúng cặp `(currency_id, tax_basis)`).
     - Bảng chi tiết từng hồ sơ thuộc 4 nguồn (`plan`, `production`, `acceptance`, `payment_request`), cho phép lọc riêng từng giai đoạn hoặc xem toàn bộ với nhóm theo Giai đoạn / Dự án / Trạng thái.
8. **Đơn vị tính / tiền tệ / VAT**:
   - Chỉ cộng trong cùng một giai đoạn (và cùng chiều `direction` đối với `tp.payment.request`) khi `amount_state == 'confirmed'` và cùng `(currency_id, tax_basis)`.
   - Tỷ lệ thực hiện so với kế hoạch (`%`) chỉ tính khi dòng kế hoạch có `measure == 'production'`, `source_status == 'comparable'` và `target_amount > 0`. Chỉ tiêu `revenue` luôn giữ `source_status == 'no_posted_evidence'`.
9. **Quy tắc quyền**:
   - Đọc hồ sơ theo record rule `tp.project.assignment` active.
   - Đọc tiền theo `_kd_money_allowed()` (`tp.project.grant` `financial_read`).
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Tiền thực thu / thực chi qua ngân hàng hoặc sổ cái kế toán; doanh thu ghi sổ kế toán; hóa đơn thuế đã phát hành.
11. **Drill-down**:
    - Mở form hoặc danh sách nguồn tương ứng (`action_plans`, `action_productions`, `action_acceptances`, `action_payments`).

---

### R04 — Báo cáo Giao khoán và Thầu phụ (`allocations_subcontracts`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Có bao nhiêu hồ sơ giao khoán nội bộ (`internal`) và thầu phụ (`subcontract`) theo từng dự án?
   - Cơ cấu giao khoán cấp 1 (`parent_id = False`) và phân bổ chi tiết cấp 2 (`parent_id != False`) như thế nào?
   - Có giao khoán cấp 1 nào bị cảnh báo vượt trần phân bổ con (`overrun_warning`) hay chưa xác nhận giá trị?
3. **Nguồn model/field thực tế**:
   - `tp.allocation` & `tp.allocation.amount`: `id`, `code`, `name`, `project_id`, `contract_id`, `allocation_kind` (`internal`/`subcontract`), `recipient_department_id`, `partner_id`, `parent_id`, `child_ids`, `level` (`1`/`2`), `scope_note`, `date_due`, `state`, `reconciliation_state`, `overrun_warning`, `owner_id`, `reviewer_id`, `amount_id` (`amount`, `amount_state`, `tax_basis`, `currency_id`).
4. **Trường ngày lọc theo kỳ**:
   - Lọc theo `date_due` (Hạn rà soát/thực hiện giao khoán). Các hồ sơ chưa có `date_due` được hiển thị rõ khi không lọc ngày hoặc báo số lượng hồ sơ không có hạn khi lọc ngày.
5. **Trường người phụ trách / rà soát**:
   - `owner_id` và `reviewer_id`.
6. **Trạng thái và ý nghĩa**:
   - `state`: `draft`, `in_review`, `returned`.
   - `reconciliation_state`: `unreconciled` (`Chưa đối chiếu`), `needs_evidence` (`Cần bổ sung chứng từ`).
   - `overrun_warning`: Cảnh báo tổng phân bổ cấp 2 (đã xác nhận, cùng cơ sở thuế/tiền tệ) vượt giá trị giao khoán cấp 1 (`Vượt trần cấp 1`).
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - **Cấm cộng trùng cha + con**: Tổng giá trị giao khoán toàn báo cáo hoặc theo dự án/loại giao khoán **chỉ cộng các hồ sơ cấp 1 (`level == '1'`, `parent_id = False`)** đã xác nhận tiền (`amount_state == 'confirmed'`) và cùng `(currency_id, tax_basis)`.
   - Tổng các dòng cấp 2 (`level == '2'`, `parent_id != False`) được hiển thị ở cột/chỉ tiêu đối chiếu riêng (`Tổng phân bổ cấp 2`) để so sánh với cấp 1, tuyệt đối không cộng gộp `cấp 1 + cấp 2`.
8. **Đơn vị tính / tiền tệ / VAT**:
   - Tách theo `(currency_id, tax_basis)`. Hồ sơ `unconfirmed` hoặc chưa có dòng tiền được giữ nhãn `"Chưa xác nhận tiền"`, không đổi thành `0`.
9. **Quy tắc quyền**:
   - Hồ sơ theo `tp.project.assignment` active; tiền theo `tp.project.grant` (`financial_read`).
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Giá trị quyết toán thầu phụ cuối cùng và số tiền đã thanh toán thực tế cho thầu phụ.
11. **Drill-down**:
    - Mở form `tp.allocation` hoặc danh sách `tp_kd_workspace.action_allocations`.

---

### R05 — Báo cáo Tình trạng xử lý và Trách nhiệm hồ sơ (`workflow_responsibility`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Trong phạm vi lọc, có bao nhiêu hồ sơ đang ở trạng thái Nháp, Đang rà soát, Bị trả lại, Quá hạn hoặc Đến hạn trong 3 ngày?
   - Từng người phụ trách (`owner_id`) và người rà soát (`reviewer_id`) đang nắm giữ bao nhiêu hồ sơ ở từng bước?
   - Phần việc thuộc trách nhiệm trực tiếp của người đang đăng nhập (`Việc của tôi`) khác gì với tổng hồ sơ trong phạm vi phòng/dự án?
3. **Nguồn model/field thực tế**:
   - 10 nguồn nghiệp vụ KH-KD (`SOURCES` trong `reporting.py`):
     - 7 hồ sơ nghiệp vụ định danh: `tp.allocation`, `tp.production`, `tp.acceptance`, `tp.payment.request`, `tp.periodic.plan`, `tp.credential`, `tp.obligation` (`state`, `owner_id`, `reviewer_id`, `date_due`, `project_id`).
     - `tp.contract.revision`: `review_state` (`draft`/`in_review`/`returned`/`review_complete`/`cancelled`), `submitted_by_id`, `reviewer_id`, `effective_date`, `contract_id.project_id`.
     - `crm.lead`: `kd_bid_state` (`identified`/`preparation`/`submitted`), `user_id`, `kd_deadline`, `tp_project_id`.
     - `project.task`: `state` (`01_in_progress`, `02_changes_requested`, `03_approved`, `04_waiting_normal`, `1_done`, `1_canceled`), `user_ids`, `date_deadline`, `project_id`.
4. **Trường ngày lọc theo kỳ**:
   - Hạn xử lý của từng loại hồ sơ: `date_due` (7 hồ sơ định danh), `kd_deadline` (`crm.lead`), `date_deadline` (`project.task`), `effective_date` / `create_date` (`tp.contract.revision`).
5. **Trường người phụ trách / rà soát**:
   - `owner_id` / `submitted_by_id` / `user_id` / `user_ids` và `reviewer_id`.
6. **Trạng thái và ý nghĩa**:
   - Giữ đúng trạng thái gốc của từng model (`state`, `review_state`, `kd_bid_state`, `task.state`) kèm phân nhóm điều hành: `Nháp / Chuẩn bị`, `Đang rà soát`, `Bị trả lại / Cần chỉnh sửa`, `Hoàn tất rà soát / Đã khai báo nộp`, `Quá hạn` (`due_date < today`), `Đến hạn 3 ngày` (`today <= due_date <= today + 3`).
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - Hạt độ dòng: Mỗi hồ sơ thuộc 10 nguồn là 1 dòng định danh (`source_key + res_id`).
   - Nhóm theo: Loại hồ sơ (`source`), Người phụ trách (`owner`), Người rà soát (`reviewer`), Dự án (`project`), Tình trạng hạn (`sla_status`).
   - **Không cộng trùng KPI giao nhau**: Một hồ sơ vừa `Đang rà soát` vừa `Quá hạn` được đếm vào từng chỉ tiêu theo đúng định nghĩa nhưng cột `Tổng số hồ sơ` chỉ đếm mỗi hồ sơ 1 lần duy nhất. Tách rõ chỉ tiêu `Toàn phạm vi đang lọc` và `Việc của tôi`.
8. **Đơn vị tính / tiền tệ / VAT**:
   - Đơn vị tính: `hồ sơ` (số nguyên).
9. **Quy tắc quyền**:
   - Kiểm tra ACL + record rule của từng nguồn; nguồn nào không có quyền đọc thì đánh dấu `readable: false` và ghi rõ không tính vào tổng.
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Thời gian xử lý chuẩn (SLA cam kết theo quy chế phê duyệt chính thức ngoài hệ thống).
11. **Drill-down**:
    - Mở trực tiếp form hồ sơ nguồn (`res_model`, `res_id`) hoặc danh sách nguồn tương ứng.

---

### R06 — Báo cáo Năng lực, Chứng chỉ và Nghĩa vụ hồ sơ (`credentials_obligations`)

1. **Người dùng chính**: Trưởng phòng, Phó phòng, Chủ nhiệm dự án, Chuyên viên KH-TH, Nhân sự phối hợp.
2. **Câu hỏi quản trị**:
   - Có bao nhiêu hồ sơ năng lực/chứng chỉ (`tp.credential`) đang hết hạn (`< today`), sắp hết hạn trong 30 ngày (`[today, today + 30]`), còn hạn trên 30 ngày (`> today + 30`) hoặc chưa có ngày hết hạn?
   - Các chứng chỉ này đang được gắn vào những cơ hội thầu (`crm.lead`) nào?
   - Các nghĩa vụ hồ sơ hợp đồng/dự án (`tp.obligation`: bảo lãnh tạm ứng, bảo lãnh thực hiện, bảo hiểm, hồ sơ pháp lý…) đang ở mức kiểm tra nào (`missing`, `collecting`, `internal_checked`)?
3. **Nguồn model/field thực tế**:
   - `tp.credential`: `id`, `code`, `name`, `project_id`, `subject_kind` (`organization`/`person`), `holder_ref`, `credential_kind`, `issuer`, `issue_date`, `valid_from`, `valid_to`, `expiry_status`, `state`, `reconciliation_state`, `owner_id`, `reviewer_id`.
   - Liên kết chứng chỉ – cơ hội thầu: M2M `crm.lead.kd_credential_link_ids` (`tp_kd_lead_credential_rel`).
   - `tp.obligation` & `tp.obligation.amount`: `id`, `code`, `name`, `project_id`, `contract_id`, `obligation_kind` (`bid_security`/`performance_security`/`advance_security`/`warranty_security`/`insurance`/`legal_dossier`), `checklist_status` (`missing`/`collecting`/`internal_checked`), `reference_no`, `issuer`, `valid_from`, `valid_to`, `date_due`, `state`, `reconciliation_state`, `owner_id`, `reviewer_id`, `amount_id`.
4. **Trường ngày lọc theo kỳ**:
   - `tp.credential`: lọc theo `valid_to` (Ngày hết hạn hiệu lực).
   - `tp.obligation`: lọc theo `date_due` (hoặc `valid_to` nếu không có `date_due`).
5. **Trường người phụ trách / rà soát**:
   - `owner_id` và `reviewer_id`.
6. **Trạng thái và ý nghĩa**:
   - Chứng chỉ (`tp.credential`):
     - `expired` (`valid_to < today`): `Hết hạn — ngưỡng 30 ngày minh họa`
     - `expiring_30d` (`today <= valid_to <= today + 30`): `Sắp hết hạn (≤ 30 ngày — ngưỡng minh họa)`
     - `valid_gt_30d` (`valid_to > today + 30`): `Còn hạn (> 30 ngày) — chưa xác minh`
     - `no_expiry` (`valid_to = False`): `Chưa khai báo ngày hết hạn`
   - Nghĩa vụ hồ sơ (`tp.obligation.checklist_status`):
     - `missing`: `Chưa có hồ sơ`
     - `collecting`: `Đang tập hợp`
     - `internal_checked`: `Đã kiểm tra nội bộ — chưa xác minh pháp lý`
7. **Quy tắc gom nhóm và hạt độ cộng tổng**:
   - **Cấm nhân bản số chứng chỉ khi gắn nhiều cơ hội thầu**: Mỗi `tp.credential` chỉ đếm 1 lần trong tổng số chứng chỉ (`distinct credential count`). Số lượng cơ hội thầu đang gắn chứng chỉ đó được hiển thị ở cột riêng (`Số cơ hội sử dụng` / `usage_count`) kèm danh sách tên cơ hội.
   - Cho phép xem tất cả hoặc lọc theo phân loại bản ghi (`credential` vs `obligation`), nhóm theo Phân loại (`record_kind`), Dự án (`project`), Tình trạng hạn / Checklist (`status_bucket`), Người phụ trách (`owner`).
8. **Đơn vị tính / tiền tệ / VAT**:
   - Đơn vị đếm: `chứng chỉ` và `nghĩa vụ hồ sơ` (tách rõ).
   - Với `tp.obligation` có giá trị bảo lãnh (`tp.obligation.amount`): chỉ hiển thị và cộng tổng theo `(currency_id, tax_basis)` khi `amount_state == 'confirmed'` và người dùng có quyền `financial_read` trên dự án.
9. **Quy tắc quyền**:
   - `tp.credential` có `subject_kind == 'person'` tuân thủ record rule hạn chế: chỉ người phụ trách (`owner_id`), người rà soát (`reviewer_id`) hoặc quản lý có grant phù hợp trong phạm vi dự án mới đọc được.
   - Quyền xem tiền bảo lãnh (`tp.obligation.amount`) theo `tp.project.grant` (`financial_read`).
10. **Chỉ tiêu chưa có căn cứ xác minh**:
    - Xác thực pháp lý bên ngoài của chứng chỉ/bảo lãnh ngân hàng; ngưỡng cảnh báo 30 ngày ghi rõ là ngưỡng minh họa hệ thống.
11. **Drill-down**:
    - Mở form `tp.credential` / `tp.obligation` hoặc danh sách `action_credentials` / `action_obligations`.

---

## 3. Kiến trúc giao diện, Bộ lọc, Biểu đồ, Bảng và Xuất Excel

### 3.1. Bố cục màn hình (`tp_kd_workspace.ReportCenter`)
1. **Header báo cáo (`.o_tp_kd_rc_head`)**:
   - Tiêu đề `Báo cáo KH-KD`, tên báo cáo đang mở (`R01`–`R06`), câu hỏi quản trị ngắn, thời điểm lấy số liệu (`Dữ liệu lúc HH:MM:SS DD/MM/YYYY · trong phạm vi quyền của bạn`).
   - Thanh công cụ báo cáo: `Áp dụng bộ lọc`, `Đặt lại`, `Làm mới`, `Xuất Excel (.xlsx)` và nút `Tùy chọn hiển thị` (`TpKdPrefs`). Không có nút `Tạo hồ sơ`.
2. **Thanh chọn 6 nhóm báo cáo (`.o_tp_kd_rc_nav`)**:
   - 6 thẻ/tab `R01` → `R06` có mã báo cáo, tên báo cáo, mô tả ngắn, hỗ trợ điều hướng bàn phím (`ArrowLeft`/`ArrowRight`/`Home`/`End`, `role="tablist"`).
3. **Khu bộ lọc báo cáo (`.o_tp_kd_rc_filters`)**:
   - Chọn nhanh kỳ: `Tất cả kỳ`, `Tháng này`, `Quý này`, `Năm nay`, `Tùy chọn`.
   - `Từ ngày` (`date_from`) – `Đến ngày` (`date_to`) có kiểm tra `date_from > date_to`.
   - `Dự án` (`project_id`, kèm tùy chọn `"Chưa gắn dự án (tiền dự án)"` khi ở `R02`/`R05`/`R06`).
   - `Người phụ trách / Rà soát` (`owner_id`).
   - `Trạng thái / Phân loại` (`status_filter`, `sub_filter` tùy theo từng báo cáo `R01`–`R06`).
   - `Nhóm dữ liệu theo` (`group_by`) và `Cột sắp xếp` (`sort_by`, `sort_dir`).
   - **Trạng thái bộ lọc**: Khi người dùng đổi điều khiển lọc nhưng chưa bấm `Áp dụng bộ lọc`, giao diện hiển thị badge `"Bộ lọc đã thay đổi — bấm Áp dụng bộ lọc để cập nhật số liệu và xuất Excel"`, đồng thời giữ rõ dải chip `"Đang áp dụng: ..."` khớp 100% với bảng, tổng và file Excel.
4. **Dải thẻ tổng hợp & Ghi chú quy tắc cộng (`.o_tp_kd_rc_summary`)**:
   - Hiển thị 4–6 thẻ chỉ tiêu tổng hợp cho báo cáo đang chọn, kèm hộp giải thích quy tắc tính (`Basis & Exclusion Note`: trường ngày lọc, số bản ghi loại khỏi tổng tiền do chưa xác nhận / khác cơ sở thuế / không có quyền xem tiền).
5. **Khu biểu đồ giải thích + Bảng tổng hợp theo nhóm (`.o_tp_kd_rc_visual`)**:
   - Biểu đồ thanh ngang hoặc donut đồng bộ bảng màu `--kd-*` (chỉ vẽ tỷ trọng phần-trên-tổng khi cùng mẫu số và cùng đơn vị).
   - Bảng tổng hợp theo nhóm (`group_rows`) có số lượng bản ghi, các cột chỉ tiêu theo nhóm và thao tác lọc nhanh vào nhóm đó.
6. **Bảng chi tiết báo cáo (`.o_tp_kd_rc_table_card`)**:
   - Grid có viền rõ (`border: 1px solid var(--kd-line)`), header cố định khi cuộn, căn phải số liệu (`tabular-nums`), căn giữa mã/ngày, căn trái nội dung, badge trạng thái theo `statusTone`.
   - Công cụ bảng: tìm kiếm nhanh từ khóa (`search`), ẩn/hiện cột tùy chọn (`Column Selector`), chọn số dòng mỗi trang (`10 / 20 / 50 / 100`), phân trang server-side trên toàn bộ tập kết quả, dòng tổng cộng chân bảng (`tfoot`) tính trên toàn bộ kết quả đã lọc.
   - Mỗi dòng có nút/liên kết mở trực tiếp hồ sơ nguồn hoặc danh sách nguồn, bảo toàn trạng thái báo cáo (`sessionStorage` theo `db + uid`) khi quay lại bằng breadcrumb.

### 3.2. Bảo vệ Race Condition & Thu hồi quyền giữa phiên
- Mỗi request `get_kd_report` gắn bộ đếm tăng dần `seq`. Khi response trả về có `seq !== this.lastSeq`, kết quả cũ bị bỏ qua hoàn toàn.
- Khi RPC hoặc HTTP trả về `AccessError` / `SessionExpired`, màn hình xóa ngay dữ liệu cũ trên state (`this.state.data = null`, `this.state.denied = true`) và hiển thị thông báo thu hồi quyền rõ ràng.

### 3.3. Xuất Excel (`.xlsx`) thực sự từ tập dữ liệu đã lọc
- Endpoint backend: Controller `/tp_kd/report/export` (POST với `csrf_token` + session Odoo hợp lệ) gọi `env['tp.kd.report.center']._build_xlsx_report(params)` chạy hoàn toàn bằng `request.env` của người dùng hiện tại (không dùng `sudo()`).
- Cấu trúc file `.xlsx` (tạo bằng `xlsxwriter` trong bộ nhớ, trả về HTTP attachment với `Cache-Control: no-store`):
  1. **Khối tiêu đề báo cáo**: Tên hệ thống `TANPHAT ONE — Báo cáo KH-KD`, mã & tên báo cáo (`R01`–`R06`), thời điểm xuất, người xuất (`user.name`), các bộ lọc đã áp dụng, ghi chú quy tắc cộng tổng & loại trừ.
  2. **Bảng chỉ tiêu tổng hợp & Tổng theo nhóm**: Đầy đủ các chỉ tiêu tổng hợp và dòng nhóm (`group_rows`).
  3. **Bảng chi tiết toàn bộ kết quả đã lọc**: Xuất **toàn bộ các dòng thỏa điều kiện lọc** (không bị giới hạn bởi `page_size` đang hiển thị trên trang), giữ đúng kiểu số (`number`) cho cột số/tiền đã xác nhận và kiểu chuỗi cho trạng thái/ghi chú (`Chưa xác nhận`, `Không có quyền xem tiền`).
  4. **Chống Formula Injection**: Mọi giá trị chuỗi bắt đầu bằng `=`, `+`, `-`, `@`, `\t`, `\r` đều được tiền tố dấu nháy đơn `'` trước khi ghi vào ô text, trong khi số âm thực sự vẫn được ghi bằng kiểu số (`write_number`).
