# BIZ-001 — Workflow và ma trận quyền Kế hoạch Kinh doanh

**Phiên bản:** 1.0 — baseline phân tích ngày 28/10/2026 (Asia/Saigon).  
**Phạm vi:** Ban Kinh doanh/Kế hoạch và các bên phối hợp.  
**Kết quả:** đủ đầu vào để thiết kế TP Contracts đọc hồ sơ; chưa phải biên bản nghiệm thu nghiệp vụ hoặc văn bản ủy quyền ký/duyệt.

Các tên model, state, capability và command dưới đây là **đề xuất triển khai**, chưa tồn tại trong runtime hợp đồng. Quy tắc quan sát từ tài liệu có mã E01–E18 tại [Nguồn và ca nghiệm thu](TP_KD_EVIDENCE_AND_ACCEPTANCE.md). Quyết định trực tiếp của người dùng được ghi riêng; không coi hướng dẫn trong tài liệu là lệnh thay đổi source.

## 1. Quyết định hiện hành

1. **BASE vẫn là nơi phê duyệt chính thức ở giai đoạn đầu.** TANPHAT ONE quản trị hồ sơ, rà soát nội bộ và ghi nhận kết quả BASE. Chưa có tích hợp BASE được kiểm chứng; không tự tuyên bố đồng bộ hoặc xây luồng duyệt ngang BASE.
2. **Người quản trị dự án được giao, Trưởng ban, QT-TC và lãnh đạo được xem số tiền đúng phạm vi.** Nhân sự hỗ trợ/kỹ thuật cần cấp riêng. Giao task hoặc xem metadata không tự cấp quyền đọc hợp đồng có giá trị.
3. **Chưa biết hạn mức ký/duyệt.** Không đặt ngưỡng giả hoặc gán quyền ký từ tên chức danh. Ngưỡng đối chiếu 1.000 VND trong Master không phải hạn mức phê duyệt.

S01/S02 giúp xác định người chuẩn bị, kiểm tra và điều phối; trách nhiệm không tự trở thành quyền ký pháp lý hoặc quyền xem toàn bộ dữ liệu.

## 2. Luồng vận hành và điểm bàn giao

KD điều phối từ tiếp cận cơ hội đến hợp đồng, kế hoạch, nghiệm thu và thanh quyết toán (E01–E04):

~~~mermaid
flowchart TD
    A[Cơ hội / đánh giá tham gia] --> B[Chuẩn bị và nộp hồ sơ thầu]
    B --> C[Trúng thầu / được giao trực tiếp]
    C --> D[Đàm phán, rà soát, ký hợp đồng]
    D --> E[Kế hoạch, giao việc và giao khoán]
    E --> F[Khảo sát / thiết kế / BIM / KCS]
    F --> G[Nghiệm thu theo phạm vi và đợt]
    G --> H[Đề nghị thanh toán, hóa đơn, thu chi và đối chiếu]
    H --> I[Hoàn thành / thanh lý / lưu hồ sơ]
    J[Quyết định chính thức trên BASE] -.-> A
    J -.-> B
    J -.-> D
    J -.-> H
~~~

Đây là trình tự điển hình, không phải chuỗi bắt buộc mọi hồ sơ: project có thể lập từ dự thầu; có đường giao trực tiếp; nghiệm thu nhiều đợt; tạm ứng có thể trước nghiệm thu. Không đặt thiết kế/khảo sát trước mọi hợp đồng hoặc buộc có hóa đơn mới ghi nhận tạm ứng.

| Công đoạn | Đầu mối | Phối hợp | Đầu ra / điều kiện bàn giao |
| --- | --- | --- | --- |
| Cơ hội/dự thầu | KD/Trưởng ban | Kỹ thuật, BIM-QC, các phòng chuyên môn | Đánh giá, quyết định tham gia, hồ sơ và bằng chứng nộp/kết quả |
| Hợp đồng/phụ lục | Chủ trì dự án KD | QT-TC, kỹ thuật, người có thẩm quyền | Phạm vi, giá trị, điều khoản; kết quả duyệt và bản ký là bằng chứng riêng |
| Kế hoạch/giao việc | Chủ trì KD và phòng nhận | Các phòng thực hiện | Một owner mỗi task, đầu ra/hạn, tham chiếu BASE (E01) |
| Giao khoán/thầu phụ | KD | Phòng nhận khoán, QT-TC, lãnh đạo | Phạm vi, loại cấp 1/2, cha-con, căn cứ được phép thực hiện |
| Sản lượng/KCS | Phòng thực hiện/chủ trì chuyên môn | KD, BIM-QC/KCS | Khối lượng/kỳ, hồ sơ kỹ thuật đã kiểm tra; chưa đồng nhất nghiệm thu tiền |
| Nghiệm thu | KD/Kế hoạch điều phối | Chủ trì, đối tác, phòng thực hiện, QT-TC | Biên bản theo bên/phạm vi; xác nhận chuyên môn khác duyệt chi |
| Đề nghị chi/thu tiền/đối chiếu | KD chuẩn bị, QT-TC kiểm tra | Người có thẩm quyền trên BASE, kế toán | Request, quyết định, hóa đơn/tiền thực tế và đối chiếu là các record riêng |
| Thanh lý/lưu | KD và QT-TC | Đối tác/phòng thực hiện | Hồ sơ thanh lý, nghĩa vụ/giữ lại còn tồn hoặc lý do, lịch sử truy xuất được |

Duyệt chi trên BASE không thay nghiệm thu chuyên môn, chữ ký hai bên hoặc hạch toán. Giao việc trong TANPHAT ONE giai đoạn đầu phản ánh hồ sơ/kết quả và tham chiếu BASE; không mặc định thay công cụ giao việc chính thức hiện có.

## 3. Bốn lớp trạng thái

| Câu hỏi | Nơi lưu đề xuất | Không được suy ra |
| --- | --- | --- |
| Hồ sơ đã rà soát nội bộ chưa? | Review của đúng version hồ sơ | Reviewer là approver trên BASE |
| BASE quyết định gì, bằng chứng đã được kiểm tra chưa? | Approval reference + evidence verification | Bấm trình = approved; upload ảnh = verified |
| Hợp đồng đã ký/có hiệu lực/đang thực hiện ra sao? | Bản ký, ngày/điều kiện hiệu lực và lifecycle | BASE approved = signed/effective |
| Bản/sự kiện nào được tính ở ngày báo cáo? | Revision/reversal, business/effective date, recorded time | ID lớn nhất/dòng Excel cuối luôn đúng |

Không tạo workflow engine tổng quát hoặc bảng transaction chứa mọi trường tiền. Dùng model có kiểu nghiệp vụ: contract/revision, allocation, production, acceptance, payment request và bridge kế toán. Nhật ký Excel chỉ là staging/provenance khi import.

## 4. Hợp đồng và BASE

### 4.1. Review một phiên bản hồ sơ

| Từ → đến | Command / capability | Guard và đầu ra |
| --- | --- | --- |
| Mới → draft | create_draft / contract.draft_edit | Company/project/owner/loại/đối tác; tiền chưa xác nhận không điền 0 |
| draft → in_review | submit_review / contract.submit | Scope, currency, giá trị/basis, ngày, hồ sơ, version; đóng băng bản gửi |
| in_review → returned | return_review / reviewer của checklist | Lý do, mục thiếu; owner nhận thông báo; sửa tạo version mới liên kết bản trước |
| in_review → review_complete | complete_review / reviewer phù hợp | Đủ mục thương mại/tài chính/kỹ thuật áp dụng; kết luận, actor, thời gian; chưa phải phê duyệt |
| review_complete → BASE pending | register_base_submission / base_reference.record | ID/link hoặc chứng cứ gửi; ràng buộc version, scope, amount/currency và checksum hồ sơ |
| BASE pending → approved/rejected/cancelled | record_external_decision / base_result.record | Ghi kết quả được khai báo từ BASE, người/ngày/evidence, lý do từ chối/hủy; verification vẫn pending |
| Evidence pending → verified/disputed | verify_external_evidence / base_result.verify | Đối chiếu nguồn, phiên bản, actor/thời gian/giá trị; disputed không dùng cho action chốt |

Review thuộc hồ sơ; pending/approved thuộc approval reference; verified thuộc evidence. Bảng không gộp chúng vào một state. Action nào cũng kiểm company/project scope và lưu actor, trước/sau, reason/evidence, request ID, version. Owner nhận thông báo trả lại/kết quả/tranh chấp; lượt phân tích này không gửi thông báo.

### 4.2. Ràng buộc approval reference

Lưu tối thiểu:

- company/project, loại đối tượng cụ thể, ID/version hồ sơ bất biến và mục đích quyết định;
- BASE task/approval ID nếu có, URL nguồn; chưa chuẩn hóa ID thì tham chiếu thủ công có provenance, không giả ID;
- decision, identity người quyết định trên BASE, decided_at, lý do;
- evidence/hash, hash hồ sơ trình, approved amount/currency khi áp dụng;
- recorded_by/at khác decided_by/at; verification_state pending/verified/disputed và verified_by/at;
- authority_status unconfirmed/confirmed cùng nguồn ủy quyền; correction/revocation liên kết bản trước, ngày tác động và audit.

Chép trạng thái hoặc thêm file chỉ tạo kết quả đã khai báo. Chỉ decision approved + evidence verified + authority phù hợp + hồ sơ chưa đổi được dùng cho command đòi quyết định chính thức. Thiếu căn cứ thẩm quyền hiển thị “chưa xác minh”, không tự hợp thức hóa.

Không dùng approval cũ cho bản đổi giá/phạm vi. Thu hồi/tranh chấp evidence chặn action mới phụ thuộc nó và mở việc xử lý; không xóa hoặc tự đảo kế toán đã posted. Đề xuất người record và verify khác nhau cho action chốt: đây là kiểm soát kỹ thuật đề xuất, chưa khẳng định công ty đã ban hành quy chế bốn mắt.

### 4.3. Chữ ký, hiệu lực và thực hiện

| Action / chuyển tiếp | Capability bổ sung | Guard |
| --- | --- | --- |
| record_signature / chưa có → ghi bản ký | legal_evidence.record | Bản ký, bên ký, ngày/người nhập; thiếu căn cứ quyền ký vẫn authority_pending |
| confirm_effectivity / signed → effective | contract.effectivity_confirm | Đủ chữ ký/điều kiện hợp đồng; effective_date, căn cứ thẩm quyền; BASE verified nếu quy trình yêu cầu |
| suspend/resume / effective ↔ suspended | contract.lifecycle_manage | Quyết định/bằng chứng, ngày, lý do; không sửa tiền bản ký |
| complete_execution / effective → execution_completed | contract.lifecycle_manage | Căn cứ hoàn thành; liệt kê nghĩa vụ tiền/giữ lại còn tồn; không tự đánh dấu đã trả |
| record_liquidation / execution_completed → liquidated | contract.lifecycle_manage | Hồ sơ thanh lý, đối chiếu, xử lý nghĩa vụ còn lại; không tự xóa công nợ |
| terminate / effective hoặc suspended → terminated | contract.lifecycle_manage | Quyết định/bằng chứng, ngày, lý do; rà soát tác động chứng từ riêng |

Các action ghi nhận hiệu lực theo bằng chứng, không tự tạo hiệu lực pháp lý. Hồ sơ lịch sử thiếu căn cứ vẫn lưu/đọc với legacy_unverified; không bịa approval để làm sạch báo cáo.

## 5. Revision, dữ liệu tiền và ngày báo cáo

### 5.1. Phụ lục và sửa sai

S03 ghi giá cập nhật là tổng mới của hạng mục/đơn vị được cập nhật, còn sản lượng/nghiệm thu/hóa đơn/tiền là phát sinh lần ghi (E05–E08). Không cộng giá mới vào giá cũ.

Đề xuất contract revision là snapshot đầy đủ sau phụ lục, có previous_revision và tài liệu nguồn. Phụ lục sửa một hạng mục thì dựng snapshot từ bản trước + thay hạng mục đó, giữ nguyên nguồn. Không thay tổng hợp đồng bằng giá trị chỉ thuộc một hạng mục.

- Chọn revision theo effective_date/chuỗi thay thế đã xác nhận; không theo dòng cuối hoặc giá dương cuối.
- Tổng mới có thể giảm/bằng 0 khi có căn cứ. Số âm chỉ cho loại điều chỉnh/đảo được quy định, không mở tùy tiện bản gốc.
- Phát hiện mâu thuẫn/trùng hiệu lực, không tự chọn ID lớn nhất. Bản tương lai chưa thay số hiện tại.
- Sửa lỗi nhập tạo correction/version; phụ lục thay đổi pháp lý có tài liệu/ngày hiệu lực riêng.
- Void loại đóng góp đúng sự kiện và giữ lịch sử. Kế toán posted dùng đảo/credit note chuẩn.
- ID Excel chỉ duy nhất trong file/sổ; khóa import gồm source binding + loại sổ + ID/root.

### 5.2. Thời gian và nguồn

Lưu riêng signed_date, effective_date, business_date/period, recorded_at và source_snapshot_at. Datetime UTC, hiển thị Asia/Ho_Chi_Minh; không reset ngày nghiệp vụ thành hôm nay khi sửa.

Báo cáo ghi rõ “hiệu lực tại ngày X, dựa trên dữ liệu biết tại Y”. Ghi hồi tố vẫn phải truy được báo cáo đã biết lúc Y. Kỳ kế toán khóa theo kế toán; không copy hành vi reset ngày sửa của macro.

### 5.3. Chỉ tiêu

| Chỉ tiêu | Ý nghĩa / giới hạn |
| --- | --- |
| Contract original/effective | Giữ giá gốc; snapshot hiệu lực đúng scope/ngày |
| Production | Phần thực hiện; chưa nhập là chưa xác nhận |
| Acceptance | Theo biên bản/bên/phạm vi; khác dòng tiền |
| Invoiced | Hóa đơn đã xuất thực tế; khác nghĩa vụ cần xuất (E07) |
| Cash received/paid | Theo chứng từ tiền, có thể gồm tạm ứng; request không tạo tiền |
| Retention | Theo điều khoản/đợt; giải tỏa riêng, không trừ hai lần |
| Acceptance trừ cash | Chênh lệch quản trị cùng basis/currency; chưa đủ để gọi công nợ đến hạn |
| Acceptance trừ invoice | Chênh lệch kiểm tra; nghĩa vụ xuất hóa đơn theo kế toán/thuế |
| NT chính trừ NT cấp 1 | Chỉ số quản trị, chưa phải lợi nhuận kế toán đầy đủ (E13) |

Không cộng khác currency hoặc gross/net. Basis thuế chưa biết phải ghi unknown. Đối chiếu PKH–KT theo company/project mapping/chứng từ/kỳ/currency/nguồn; thiếu KT là missing_source. Ngưỡng 1.000 VND chỉ dùng đối chiếu, không duyệt chi.

Giữ đồng thời các cảnh báo, kèm primary summary; không để nhãn ưu tiên che cảnh báo khác. “Năm” từ mã dự án trong Master là cohort, khác kỳ hạch toán. Freshness phải theo nguồn/project, không dùng lần import mới để làm mọi project có vẻ mới (E12–E16).

## 6. Project, task, giao khoán và nghiệm thu

| Đối tượng | Luồng đề xuất | Guard chính |
| --- | --- | --- |
| Project | draft → review → active ↔ on_hold → completed/cancelled | Mã/company/phòng/owner/assignment; reopen cần quyền đặc biệt/lý do |
| Task/kế hoạch | draft → assigned → in_progress → result_submitted → completed/returned/cancelled | Một owner, hạn/đầu ra/scope, tham chiếu BASE; xong task không tạo acceptance tiền |
| Allocation | draft → in_review → ready_for_execution → executing → completed/terminated | Loại cấp 1/2, cha, scope, currency/giá trị và căn cứ được phép thực hiện |
| Production | draft → submitted → confirmed/returned | Kỳ/khối lượng/evidence, người xác nhận chuyên môn; tiền cần capability riêng |
| Acceptance | draft → reviewed → signed_recorded → confirmed/void | Biên bản/chấp thuận, bên/phạm vi/kỳ; rà soát chuyên môn khác thương mại |
| Payment request | draft → finance_review → ready_for_base → awaiting_base → externally_approved/rejected/withdrawn | QT-TC kiểm tra; BASE đúng bản; tách trạng thái thực trả |
| Invoice/receipt/payment | Theo account.move/account.payment khi bridge triển khai | Kế toán posting/reconcile; trước đó chỉ observation có nhãn chưa đối chiếu |

Tạm ứng có thể có request theo hợp đồng chưa có nghiệm thu; không tạo nghiệm thu giả. Một request trả nhiều lần, một payment phân bổ nhiều request; theo dõi links/phân bổ tiền riêng. Trạng thái đã trả/đối chiếu tính từ links này, không từ action duyệt request.

Quy tắc cấp khoán (E09):

- external_subcontract (thầu phụ công ty) và internal_allocation (khoán nội bộ) là cấp 1.
- department_subcontract là cấp 2; cha bắt buộc internal_allocation cùng company/project, đúng phòng nhận, không vòng lặp.
- Tổng công ty chỉ cộng cấp 1. Cấp 2 phục vụ quản trị phòng, không cộng khoản con lần nữa.
- Hợp đồng thầu phụ giữ danh tính/revision riêng; allocation liên kết scope, không tạo hai nghĩa vụ cho cùng hồ sơ.
- Khoán nội bộ không tạo vendor bill/PO giả. Lương/cá nhân nhận khoán thuộc HR/Finance và cần quy chế.
- Vượt khoán mẹ là cảnh báo quan sát được; hard block chưa chốt. Policy tương lai phải minh thị và lưu cách xử lý.

## 7. Ma trận quyền đề xuất

### 7.1. Role preset và capability

Đây chưa phải XML ID/group runtime. Mỗi grant có user, capability, company, project/department scope, thời hạn, người cấp, lý do và audit. Company membership/cùng phòng không tự cho xem tất cả project.

| Role | Scope mặc định | Lưu ý |
| --- | --- | --- |
| KD_HEAD | Hồ sơ KD trong company được giao | Không tự có quyền ký/duyệt BASE |
| PROJECT_OWNER | Project được giao quản trị | Khác coordinator chỉ đọc hiện tại |
| PLANNING | Project/task được giao | Tiền cần grant riêng hoặc kiêm PROJECT_OWNER |
| SUPPORT | Metadata/task/tài liệu được giao | Không tiền mặc định |
| TECHNICAL | Hạng mục/task/phần kỹ thuật được giao | Không tiền mặc định |
| FINANCE | Finance scope được giao | Posting theo quyền kế toán chuẩn |
| EXECUTIVE | Company/project được ủy quyền đọc | Đọc không tự thành quyền thao tác |

✓ = cấp mặc định trong scope; — = không cấp mặc định. Quyền ghi vẫn phải thỏa state/field/cổng BASE. Tiền đọc khác tiền sửa.

| Capability | KD_HEAD | PROJECT_OWNER | PLANNING | SUPPORT | TECHNICAL | FINANCE | EXECUTIVE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| project.metadata_read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| document.metadata_prepare | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| financial.read | ✓ | ✓ | — | — | — | ✓ | ✓ |
| contract.draft_edit / contract.submit | ✓ | ✓ | — | — | — | — | — |
| contract.review_commercial | ✓ | — | — | — | — | — | — |
| financial.draft_edit | ✓ | ✓ | — | — | — | — | — |
| work_plan.prepare | ✓ | ✓ | ✓ | — | — | — | — |
| task.result_submit / production.quantity_prepare | — | ✓ | ✓ | — | ✓ | — | — |
| allocation.prepare / acceptance.prepare / payment_request.prepare | ✓ | ✓ | — | — | — | — | — |
| technical.review | — | — | — | — | ✓ | — | — |
| finance.review / reconciliation.record | — | — | — | — | — | ✓ | — |
| audit.read_scoped | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Capability bổ sung phải cấp rõ, không tự suy từ chức danh:

| Capability | Điều kiện/giới hạn |
| --- | --- |
| financial.read | PLANNING/SUPPORT/TECHNICAL có phân công cụ thể; đúng project/hạng mục, không kéo quyền sửa |
| financial.draft_edit | Cần financial.read và quyền prepare đúng domain; dự toán, hợp đồng, nghiệm thu phân biệt |
| base_reference.record | Chỉ metadata/evidence được xem; support không upload/read evidence tiền chưa được cấp |
| base_result.record / base_result.verify | Người chỉ định riêng; cần financial.read nếu kết quả có tiền; verify không tạo thẩm quyền |
| legal_evidence.record / contract.effectivity_confirm | Căn cứ phân công/thẩm quyền; chưa cấp mặc định khi Q1/Q2 chưa đóng |
| revision.propose / revision.confirm / record.void | Đúng domain/state/reason, kiểm tác động; proposer không tự xác nhận hiệu lực pháp lý |
| contract.lifecycle_manage | Đình chỉ, hoàn thành, thanh lý/chấm dứt và căn cứ thẩm quyền |
| financial.export | Cấp riêng; xem không tự cho xuất toàn bảng |
| project.scope_manage / grant.manage | Người được chỉ định, theo quyết định chủ nghiệp vụ; không tự cấp tiền cho mình |

Không có capability “phê duyệt chính thức trong Odoo” ở giai đoạn đầu. Người duyệt trên BASE do BASE/văn bản ủy quyền quyết định.

### 7.2. Field, file và kênh rò rỉ

- Metadata read không cho amount, rate, cost, margin, công nợ, retention; DTO thiếu quyền không có trường tiền, không điền 0.
- Metadata prepare chỉ sửa allowlist không nhạy cảm; không sửa tiền, review/BASE result, hash evidence đã chốt.
- Hợp đồng ký, phụ lục giá, biên bản tiền, năng lực tài chính là file financial. Cần grant hoặc bản che tiền cho support; không cấp download chỉ vì có project.
- Chatter/filename/notification/audit before-after, search/group_by/aggregate, related fields, export và preview phải cùng policy.
- Upload file chưa phân loại vào vùng hạn chế; link/copy sang task không hạ mức nhạy cảm. Không public attachment/token để né quyền.
- Áp dụng cả native Odoo/RPC và API/report/export; chỉ lọc DTO web riêng chưa đủ.

### 7.3. Thực thi Odoo và quyền quản trị

ACL kiểm model; global rules giới hạn company/project; action checks giới hạn state/capability. Tiền theo grant từng project cần lớp dữ liệu tài chính có scope riêng hoặc cơ chế ORM tương đương được kiểm chứng; một field group financial toàn cục không đủ khi cùng user được xem metadata project A nhưng chỉ xem tiền project B. Ưu tiên record tài chính được bảo vệ riêng; chốt schema cụ thể ở CTR-001 và kiểm native read/search/read_group/export/RPC, không chỉ React.

ACL/group rules cộng quyền; global rules giao nhau, group rules có thể hợp nhau. Không giả định role hạn chế hơn tự thắng. Người SUPPORT kiêm FINANCE có thể xem tiền đúng finance scope; đánh giá grant theo từng project. Thu hồi grant phải có hiệu lực request sau cả API/tệp.

Runtime hiện có Project Reader/Platform Manager và assignment reader/coordinator; coordinator chỉ đọc. Không ánh xạ chúng thành quyền ghi/tiền. Platform Manager quản lý metadata/assignment hiện tại, không mặc nhiên thành reviewer/approver nghiệp vụ.

System administrator/superuser và quản trị database có khả năng truy cập kỹ thuật. Dùng tài khoản quản trị riêng, break-glass và audit; không hứa họ không thể xem tiền. API nghiệp vụ không dùng sudo để né quyền caller.

## 8. API, audit và đồng thời

Mọi transition phải có actor/capability, scope, state trước/sau, guard, reason/evidence, audit và người nhận thông báo. Các slice ngoài hợp đồng ở mục 6 phải chi tiết hóa action matrix trước khi code action.

- Actor lấy từ session; không tin company/grant/state/total/approval do frontend quyết định.
- Validate cùng company/project/currency, source scope, parent-child và ID. Cross-scope dùng 403/404 thống nhất, không lộ sự tồn tại hồ sơ.
- Draft sửa theo quyền; đã submit/chốt cần version/revision bất biến. Chặn direct state write cả ORM/RPC.
- Transaction nguyên tử, optimistic version, khóa/constraint khi đổi revision để tránh hai bản mâu thuẫn.
- Idempotency theo actor/project/command/key + payload hash; retry payload khác bị từ chối.
- Audit bảo vệ before/after theo field policy; có actor/time/reason/evidence/version/request ID; chatter không thay toàn bộ audit.
- Tiền theo currency/rounding Odoo, DTO decimal string + currency + basis/verification; JavaScript không tính tiền chính thức.
- Request không tạo tiền thực tế, ghi BASE không auto-post kế toán.

**Sau baseline được phép:** read-only vertical slice cho tp.contract, tp.contract.revision, tp.contract.line và tp.approval.reference; chưa mở command ghi/chốt pháp lý khi Q1/Q2 chưa đóng.

## 9. Câu hỏi còn mở và cổng triển khai

| Mã | Cần xác minh / đầu mối | Tạm thời | Chặn phần nào |
| --- | --- | --- | --- |
| Q1 | Văn bản ký/duyệt/ủy quyền, hạn mức theo loại hồ sơ | authority_pending, không ngưỡng giả | Auto-routing, xác nhận thẩm quyền/action chốt pháp lý |
| Q2 | Phân tách lập/soát/record/verify, người cấp grant | Đề xuất tách record/verify | Cấp quyền ghi/xác minh/chốt cho pilot |
| Q3 | BASE ID/bằng chứng một quyết định thực tế | Manual reference, verification pending | Đồng bộ và dùng evidence chốt |
| Q4 | Thuế/gross-net/currency, ngày hiệu lực/hồi tố/kỳ khóa | Tách date/basis, unknown không suy tính | Tính công nợ/thuế/as-of chính thức, import thật |
| Q5 | Work item/design stage | Catalog riêng, mapping duyệt | Import/báo cáo xuyên hồ sơ |
| Q6 | Invoice/thu/chi chính thức và lịch đối chiếu | Observation chưa đối chiếu | Finance bridge/số liệu chính thức |
| Q7 | Vượt khoán mẹ | Cảnh báo | Policy activate/close allocation |
| Q8 | Sửa/void sau thanh lý, giữ lại/tạm ứng | Không xóa/không tự đảo sổ | Ngoại lệ/nghiệm thu pilot |

Thiếu Q1 không ngăn đọc hồ sơ/thiết kế schema hoặc draft development trên test. Nó ngăn tự nhận thẩm quyền/phát hành quyết định. Không cần người dùng biết mọi hạn mức ngay; khi đến cổng liên quan, đối chiếu văn bản/hồ sơ với đầu mối.

| Giai đoạn | Làm tiếp được | Điều kiện qua cổng |
| --- | --- | --- |
| CTR-001 đọc | Model/revision/line, quyền, DTO, màn hình, BASE reference có nhãn xác minh; dữ liệu giả | Security/API/UI tests, không import thật/action chốt |
| CTR-002a draft | Phát triển draft/submit/return trên test | Capability/CSRF/version/idempotency/audit, negative tests; grant xác nhận trước pilot |
| CTR-002b evidence/pháp lý | Record/verify BASE, chữ ký, hiệu lực | Q1–Q3 và phần Q4/Q8 liên quan; chưa đủ giữ cổng đóng |
| ALC/STL/FIN/IMP | Mỗi nghiệp vụ theo slice | Q4–Q8 liên quan, hồ sơ khử dữ liệu, reconcile, tests và owner nghiệm thu |

## 10. Kết quả và bước tiếp theo

Đã đọc năm nguồn, đối chiếu dạng phụ lục/sửa sai/khoán cấp 2/tiền và lập [ca nghiệm thu giả lập](TP_KD_EVIDENCE_AND_ACCEPTANCE.md). Đây là hoàn tất baseline phân tích BIZ-001.

Chưa có chủ nghiệp vụ ký xác nhận ma trận, chưa có văn bản hạn mức, chưa đối chiếu 2–3 bộ hợp đồng/biên bản/phiếu duyệt thực tế đầy đủ. Các state/capability/ca test là thiết kế, chưa triển khai/chạy trên Odoo.

**Bước tiếp theo:** CTR-001 — TP Contracts đọc hợp đồng, revision, line và tham chiếu BASE; ưu tiên quyền tiền/attachment. Thu thập Q1–Q3 để chuẩn bị ghi/chốt sau; không tạo engine chung hoặc mở đủ chín phân hệ.

