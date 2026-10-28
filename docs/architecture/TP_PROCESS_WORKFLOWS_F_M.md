# TANPHAT ONE — Khung quy trình F–M (BIZ-002)

**Trạng thái:** đề xuất thiết kế để chủ nghiệp vụ xác nhận; chưa phải quy chế, chưa tạo model/action/runtime.  
**Ngày:** 28/10/2026 (Asia/Saigon). **Phạm vi:** TP Survey, TP Design, TP Contracts/Tasks, TP Finance, TP Documents, TP HR và TP Dashboard cùng các tác vụ nền.

Tài liệu này mở rộng baseline BIZ-001 cho các bước F–M trong [TP_ENTERPRISE_PROCESS_MAP.md](TP_ENTERPRISE_PROCESS_MAP.md). Đọc cùng [TP_KD_WORKFLOW_AND_PERMISSIONS.md](TP_KD_WORKFLOW_AND_PERMISSIONS.md), [TP_KD_EVIDENCE_AND_ACCEPTANCE.md](TP_KD_EVIDENCE_AND_ACCEPTANCE.md), [TP_DATABASE_DESIGN.md](TP_DATABASE_DESIGN.md), [TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md](TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md), [TP_BIZ002_INTEGRATION_AND_REPORTING.md](TP_BIZ002_INTEGRATION_AND_REPORTING.md) và [TP_BIZ002_ACCEPTANCE_AND_READINESS.md](TP_BIZ002_ACCEPTANCE_AND_READINESS.md).

Các role/capability dưới đây là tên đề xuất, không đồng nghĩa group Odoo đã có. Mỗi transition phải kiểm actor, capability, company/project/department scope, state trước, điều kiện dữ liệu, bằng chứng và concurrency/idempotency trong **một transaction Odoo**; frontend chỉ gọi command. `null`, `0`, số âm và chưa xác nhận giữ khác nhau. Không đặt hạn mức, SLA, bốn mắt hoặc ngày bắt buộc khi chưa có Q1–Q14. Quyền backend áp dụng đồng nhất cho ORM/RPC/API/export/file/chatter/notification/audit.

## Quy ước lớp và ma trận transition

| Lớp | Ý nghĩa | Ranh giới |
|---|---|---|
| Nội bộ | Rà soát, điều phối, chuẩn bị, KCS, đối chiếu trong TANPHAT ONE | Không phải phê duyệt pháp lý hay posting |
| BASE | Record/link kết quả phê duyệt chính thức trên BASE | BASE là **official** giai đoạn đầu; TANPHAT ONE không thay BASE/không xây ledger |
| Chữ ký | Bản ký và người/bên ký được ghi nhận | Upload/chữ ký ghi nhận không tự xác nhận thẩm quyền |
| Pháp lý | Hiệu lực, nghĩa vụ, chứng từ có căn cứ ủy quyền/pháp luật | Chỉ mở khi Q1–Q4/Q8 và hồ sơ thực tế đủ; không suy từ chức danh |
| Thực hiện | Task, sản lượng, nghiệm thu, hóa đơn, thu/chi, bàn giao | Kế toán/Odoo là nguồn chính thức cho posting/reconcile; request không phải tiền |

Mỗi bảng state dùng format: **actor/capability; scope; guards; evidence; output; history/notification**. Mọi hàng mặc định lưu actor từ session, before/after không lộ trường tiền, reason áp dụng, request/correlation ID, expected version, business/effective date riêng recorded timestamp, evidence hash và recipient có quyền. Không gửi thông báo trong lượt phân tích. Người lập và người record/verify có thể là vai trò khác nhau theo Q2; chưa tuyên bố bắt buộc four-eyes. RACI `A` được hiểu **một người/đơn vị chịu trách nhiệm cho từng record hoặc transition**; A của phạm vi khác chỉ được ghi thành C/I ở bước đó. Mỗi task cụ thể vẫn chỉ một owner và phải được chủ nghiệp vụ xác nhận.

| Nguồn / mức căn cứ | Nội dung được quan sát | Phần còn là đề xuất |
|---|---|---|
| S01 P026–P031, P084–P100, T02; E01/E04 | Một task một owner; Kỹ thuật chủ trì khảo sát; Thiết kế làm hồ sơ; BIM-QC/KCS kiểm soát; hồ sơ chỉ xuất bản/trình sau KCS | Actor/capability chi tiết, tiêu chuẩn đo, checklist, stage/issue catalog và guard phát hành: Q9/Q10 |
| S01 P059–P080, T02; E05–E16 từ S03/S05 | KD điều phối nghiệm thu/request, QT-TC kiểm soát; sản lượng/NT/hóa đơn/tiền/giữ lại là các khái niệm riêng | State, bằng chứng tạm ứng/giải tỏa giữ lại và bridge kế toán: Q4/Q6/Q8 |
| S01 P070–P074, P103–P107; T03 | QT-TC có HR/văn thư; CNTT vận hành NAS/BASE; có nhu cầu báo cáo quản trị | Quyền HR, retention/privacy, catalog/import/cutover, KPI cadence và incident: Q11–Q14 |
| DEC-013–017, CTR-001, OPS-001 | BASE official; grant tiền theo project; read slice hợp đồng; đã diễn tập restore local | Các workflow F–M chưa runtime; không nhận source chuẩn Odoo có sẵn là đã cài/đã nghiệm thu |

S01/S03/S05 và E01–E18 có registry/hash tại [bằng chứng BIZ-001](TP_KD_EVIDENCE_AND_ACCEPTANCE.md); chúng không tự chứng minh quy chế đang hiệu lực. Chưa có bộ hồ sơ kỹ thuật/HR/kế toán thật được chủ nghiệp vụ xác nhận cho F–M.

## F — Khảo sát hiện trường (TP Survey)

**Purpose/start/end/owner-RACI.** Chuẩn hóa đề cương, phương án, đo đạc địa hình–địa chất–thủy văn, nhật ký và bàn giao báo cáo khảo sát cho thiết kế/KCS/nghiệm thu. Bắt đầu khi project/task có phạm vi và người chịu trách nhiệm; kết thúc khi bộ hồ sơ được KCS ghi nhận và bàn giao đúng revision (hoặc bị trả/hủy có lý do). Owner đề xuất: Kỹ thuật/Chủ nhiệm khảo sát là A/R cho record khảo sát; BIM-QC/KCS là C; KD/Project Owner là A riêng cho phạm vi/giao việc (C ở record khảo sát); QT-TC là I về chi phí; thầu phụ khảo sát là R theo giao khoán. Input: scope hợp đồng/phiếu giao việc, đề cương, mốc/điều kiện hiện trường, assignment và căn cứ BASE nếu có. Output: nhật ký, tọa độ/đo đạc, ảnh/biên bản hiện trường, báo cáo, checklist KCS, revision và liên kết hồ sơ. Handoff: `F.handed_over` → TP Design/KCS; bản chưa KCS không được dùng làm hồ sơ phát hành.

| Từ → đến | Actor/capability; scope | Guard | Evidence/output; history/notification |
|---|---|---|---|
| `draft → planned` | Kỹ thuật; `survey.prepare`; project/company/department | task có owner, scope/version, phương án/đề cương; chưa xóa bản cũ | đề cương + assignment; audit actor/time/reason; báo owner/KD |
| `planned → in_field` | Chủ nhiệm; `survey.start`; đúng project/đợt | điều kiện tiếp cận/biện pháp an toàn và mốc hiện trường được ghi (chi tiết cần Q10) | nhật ký bắt đầu, người/thiết bị; audit; notify team |
| `in_field → submitted` | Kỹ thuật/thầu phụ; `survey.result_submit` | đủ trường bắt buộc, file checksum, business_date/recorded_at; không tự điền 0 | bộ khảo sát revision; log source; notify KCS |
| `submitted → kcs_passed` | BIM-QC; `technical.review`; cùng scope | checklist áp dụng, sai số/thiếu file được xử lý; không kiểm tra thay nghiệm thu/BASE | checklist + kết luận; history trước/sau; notify owner/KD |
| `submitted → returned` | KCS; `technical.review` | lý do/mục thiếu bắt buộc; giữ version bất biến | return reason, issue list; notify người lập |
| `returned → superseded`; bản mới `draft → planned` | Chủ nhiệm/Kỹ thuật; `survey.revise`; cùng project/đợt | previous revision, reason và issue links; sửa tạo version mới, không mở khóa bản đã trả | new revision rồi resubmit qua `in_field/submitted` phù hợp phạm vi; audit; notify KCS |
| `kcs_passed → handed_over` | Chủ nhiệm/KD; `survey.handoff`; project scope | KCS pass, revision/hash, recipient xác nhận; không suy đã được CĐT duyệt | biên bản bàn giao/link design; audit + notification |
| `planned/in_field/submitted → cancelled` | Owner có `survey.cancel` | lý do; rà soát tác động giao khoán/chi phí; không xóa | cancellation record, link replacement; notify liên quan |

**Ngoại lệ và cổng xác nhận.** `return/reject` tạo version sửa; `reopen` chỉ capability đặc biệt, lý do và link hồ sơ thay thế. Duplicate điểm đo/file phải giữ cả hai và gắn `duplicate_of` để xử lý, không âm thầm ghi đè. Thiếu dữ liệu là `missing`, không phải zero; sai ngày ghi nhận vẫn giữ business date và recorded time. Bản sau KCS chỉ là nội bộ; ký/chấp thuận CĐT là lớp riêng. GAP: tiêu chuẩn đo, ngưỡng sai số, mẫu biên bản, an toàn, quy tắc nghiệm thu (Q1/Q4/Q5/Q8/Q10).

**Acceptance examples.** Chấp nhận: đợt F-01 có owner, đề cương, nhật ký và ảnh; KCS pass revision `R1`, bàn giao đúng project/scope, Design nhận cùng checksum. Từ chối: thiếu nhật ký/ảnh hoặc file đổi sau submit; KCS trả `returned` nêu mục thiếu, không chuyển sang Design/phát hành và không tạo nghiệm thu tiền.

## G — Thiết kế, BIM và KCS (TP Design)

**Purpose/start/end/owner-RACI.** Tạo hồ sơ BCNCTKT/BCNCKT/TKKT/TKBVTC, dự toán, BIM/3D, thẩm tra và kiểm soát chất lượng trước phát hành. Start từ survey/brief đã được nhận; end khi KCS pass và chủ nhiệm/giám đốc dự án ghi nhận phát hành, hoặc return/cancel/revise. Owner đề xuất: chủ nhiệm thiết kế là A package, Phòng Thiết kế là R; BIM-QC là A riêng cho KCS/BIM record (C ở package); Project Owner/KD là A riêng cho phạm vi/giao việc (C ở package); Kỹ thuật/TVGS là C theo chuyên môn; CĐT/BASE là I/official khi áp dụng. **Input:** survey handoff, brief/phạm vi hợp đồng, catalog work item/stage, tiêu chuẩn áp dụng và assignment. **Output:** package bản vẽ/tính toán/BIM, checklist KCS, revision/hash, release hoặc issue list. **Handoff:** `G.released` → task/TP Documents/KD/CĐT theo quyền; chỉ package pass KCS được trình/phát hành.

| Từ → đến | Actor/capability; scope | Guard | Evidence/output; history/notification |
|---|---|---|---|
| `brief → drafting` | Thiết kế/BIM; `design.prepare`; project/discipline | survey handoff, stage/work item, owner, input version | design package draft; audit; notify owner |
| `drafting → internal_review` | Chủ nhiệm; `design.submit`; cùng revision | file/checksum, model coordination, checklist và ngày; freeze submitted payload | submitted revision; notify BIM-QC/TVGS |
| `internal_review → returned` | BIM-QC/technical reviewer; `technical.review` | checklist/issue severity theo catalog cần Q5; reason bắt buộc | issue list, return event; notify author |
| `internal_review → kcs_passed` | BIM-QC; `technical.review` | checklist đủ, clash/quality evidence, required disciplines | KCS certificate/checklist; history; notify KD/Project Owner |
| `kcs_passed → released` | Chủ nhiệm/Project Owner; `design.release` | KCS pass, revision/hash, recipient and release purpose; không tự tạo legal approval | release record; notify recipients, lock revision |
| `returned → superseded`; bản mới `drafting → internal_review` | Chủ nhiệm; `design.revise`; project/discipline | previous revision, issue fixes, input hash và reason; không bỏ KCS | revision mới + evidence sửa; audit; notify reviewer |
| Bản cũ giữ `released`; bản mới `drafting` | Owner; `design.revise`; project/discipline | change reason, previous_revision, impact/risk; bản cũ read-only; bản mới phải đi lại review/KCS | new revision + diff/provenance; notify affected tasks |
| Bản cũ `released → superseded` khi bản mới `kcs_passed → released` | Chủ nhiệm; `design.release`; cùng package/scope | bản thay thế KCS pass, release evidence/hash và ngày áp dụng; chưa có bản mới đạt không tự bỏ bản đang dùng | supersession link/version và ngày; audit; notify consumers |
| `drafting/internal_review → cancelled` | Owner; `design.cancel`; project/discipline | reason, no active downstream dependency or explicit impact handling | cancel history; notify team |

Nội bộ/KCS, BASE, chữ ký và pháp lý là bốn lớp riêng; `released` không có nghĩa CĐT đã phê duyệt. BIM model/version, drawing và calculation phải cùng package hoặc liên kết rõ; không dùng file mới nhất theo tên. GAP: chuẩn LOD/IFC, clash threshold, stage catalog, checklist, người có quyền phát hành, điều kiện pháp lý, Q5/Q10.

**Acceptance examples.** Chấp nhận: survey `R1` → design `R2`, BIM-QC pass checklist, release khóa hash và chuyển task triển khai. Từ chối: clash chưa xử lý hoặc file không khớp checksum; KCS trả, revision cũ vẫn truy xuất, không được trình/ghi nhận hoàn thành.

## H — Sản lượng, nghiệm thu, payment request, tạm ứng và giữ lại

**Purpose/start/end/owner-RACI.** Tách sự kiện thực hiện khỏi nghiệm thu, request, hóa đơn, tiền và retention; phục vụ TP Contracts/Tasks/Finance mà không tạo ledger. Start từ allocation/contract line và kỳ công việc; end khi hồ sơ nghiệm thu/request được chốt hoặc bị return/reject/cancel/void. Owner đề xuất: phòng thực hiện/Project Owner (R sản lượng); KD/Kế hoạch (A nghiệm thu và request); KCS/technical (C); QT-TC/FINANCE (R review tài chính); BASE approver (official); Kế toán (R invoice/payment khi bridge). **Input:** allocation/contract revision, production evidence, biên bản/chấp thuận, terms tạm ứng/giữ lại, currency/basis và BASE reference nếu cần. **Output:** production/acceptance/request/retention links, trạng thái và reconciliation-ready links; cash/invoice chỉ là observation tới khi Odoo bridge. **Handoff:** production/acceptance → FINANCE/KD; request `awaiting_base` → BASE; posted/reconciled → I/Dashboard; không chuyển `approved` thành `paid`.

| Đối tượng/state | Actor/capability; scope | Guards/evidence | Output/history/notification |
|---|---|---|---|
| Production `draft → submitted` | Performer `production.prepare/submit`; project/company/period/work-item | quantity/unit/work item/period/evidence; null ≠ 0; freeze version | production revision; history; notify technical/KD |
| Production `submitted → confirmed/returned` | Technical `production.quantity_confirm`; cùng scope | checklist + evidence; returned cần reason; confirmed chỉ chuyên môn, không phải tiền/NT | conclusion/issue; history; notify owner |
| Production `returned → superseded`; bản mới `draft → submitted` | Performer `production.prepare/submit`; cùng project/kỳ/work item | reason/issue fixes, previous entry; bản cũ bất biến, chỉ bản hiện hành đóng góp | revision mới, audit; notify reviewer khi gửi lại |
| Acceptance `draft → reviewed` | KD `acceptance.prepare`, technical `technical.review`; project/contract/party/period | scope/period/party/biên bản/checklist; tránh overlap/duplicate event; reviewed chưa phải signed | reviewed version; history; notify parties |
| Acceptance review `draft → returned`; bản sửa mới `draft → reviewed` | Reviewer `technical.review`, owner `acceptance.prepare`; cùng biên bản/scope | thiếu mục phải có reason; sửa tạo version mới và xử lý từng ý kiến | giữ bản bị trả, previous/replacement links; audit; notify owner/reviewer |
| Acceptance signature `unsigned → signed_recorded` | Người được giao `legal_evidence.record`; cùng project/version/bên | bản ký, người/bên/ngày và nguồn thẩm quyền; thiếu nguồn là unconfirmed | signature evidence/hash; history; notify KD |
| Acceptance `reviewed → confirmed` | Designated owner `acceptance.confirm`; project/contract | chỉ khi signatures/authority/conditions áp dụng đủ; Q1/Q4/Q8 còn mở thì không activate | confirmed immutable event; history; notify FINANCE |
| Acceptance `confirmed → void` | Designated owner `acceptance.void`; scope bản gốc | reason + căn cứ correction, replacement/reversal links và downstream impact; không tự đảo kế toán | void event, previous value history; notify KD/FINANCE |
| Request `draft → finance_review` | KD `payment_request.prepare/submit`; project/contract/allocation | link acceptance/contract/terms, currency/basis/request amount; tạm ứng có thể chưa acceptance khi điều khoản cho phép (Q8) | frozen request version; history; notify FINANCE |
| Request `finance_review → ready_for_base/returned` | FINANCE `finance.review`; cùng scope và quyền tiền | chứng từ hợp lệ/checklist; returned cần reason; không thay quyết định BASE | review result; history; notify KD |
| Request `returned → superseded`; bản mới `draft → finance_review` | KD `payment_request.prepare/submit`; đúng scope/version | sửa theo reason, previous request; key/version mới, không dùng BASE reference của bản đổi tiền | bản mới, audit; notify FINANCE; bản cũ không góp tổng hai lần |
| Request `ready_for_base → awaiting_base` | Designated `base_reference.record`; company/project/request version | ID/link/chứng cứ gửi, hash hồ sơ/mục đích/giá trị cùng currency; chưa có interface thì manual reference | pending reference; audit; notify recorder/owner |
| BASE result `pending → approved/rejected/cancelled` | Designated `base_result.record`; đúng scope/version | evidence + decided_by/at; reject/cancel reason; verification vẫn pending | declared result; history; notify owner/FINANCE |
| BASE verification `pending → verified/disputed` | Designated `base_result.verify`; đúng scope/version | đối chiếu nguồn/hash, actor/time/value/authority; Q1–Q3 chặn khi chưa đủ | verified/disputed reference; history; notify owner |
| Request projection `awaiting_base → externally_approved` | Backend dựa reference; đúng company/project/request scope; không capability approve trong Odoo | decision `approved` + verification `verified` + authority confirmed + hồ sơ không đổi | approved projection; chưa có payment thì cash không đổi; notify owner |
| Request projection `awaiting_base → rejected` | Backend dựa reference; đúng company/project/request scope | decision `rejected`, rejection reason; giữ riêng verification `pending/verified/disputed` và authority; chưa xác minh hiển thị “khai báo bị từ chối” | rejected projection có nhãn xác minh; `disputed` tự nó không phải rejected; audit; notify owner |
| Request `draft/finance_review/awaiting_base → withdrawn` | Owner `payment_request.withdraw`; project/request | reason, xác nhận không dùng request nữa; nếu đã có payment mở correction riêng | withdraw event; history; notify FINANCE/BASE recorder |
| Advance obligation `unverified → tracked → offset/returned` | FINANCE `advance.record/reconcile`; project/contract/request | terms, evidence giải ngân và phân bổ/hoàn ứng; chưa có policy thì `unknown` | advance links/residual, không NT giả; audit; notify KD |
| Retention `unverified → held → released/adjusted` | FINANCE `retention.record/release`; project/contract/acceptance | điều khoản/tỷ lệ/số tiền/ngày/điều kiện giải tỏa có nguồn; chưa xác nhận không tự tính; release event riêng | retention balance/links; không trừ hai lần; audit; notify KD |
| Invoice/cash theo native accounting | Kế toán; chuẩn Odoo `account.move/account.payment`; company/ledger + source project | chỉ posting/reconcile của Odoo là official; request/approval/receipt observation không tạo cash | links phân bổ cho nhiều request/đợt; audit/notify như I |

State của review, BASE decision/verification, signature và thực hiện nằm ở record/field khác nhau. `externally_approved` chỉ là projection đọc của request, không thay stored BASE result hoặc xác nhận paid. Rejected/withdrawn là disposition request riêng với verification của evidence; không biến `disputed` thành một quyết định từ BASE. Một payment phân bổ nhiều request/một request nhiều payment bằng links có tổng và currency được đối chiếu; không nhân số tiền khi join báo cáo.

**Ngoại lệ.** `rejected/returned` bắt buộc lý do; sửa tạo revision/request mới. `cancel/withdraw` không xóa; `void` đóng đúng event và giữ audit. Duplicate request/payment idempotency key hoặc source binding phải chặn; payload khác cùng key bị từ chối. Backdate giữ business_date/period và recorded_at, không reset hôm nay; kỳ khóa do kế toán quyết định (Q4/Q6). Thiếu hóa đơn/BASE/biên bản là `missing_source`, không zero. Vượt khoán mẹ là cảnh báo theo Q7, chưa hard-block. Scope sai trả 403/404 nhất quán.

**Acceptance examples.** Chấp nhận: production 100, acceptance 80, invoice 80, cash 72, retention 8; request 80 pending hiển thị riêng, cash chỉ 72 từ chứng từ đã đối chiếu. Từ chối nội bộ vì thiếu acceptance/điều khoản tạm ứng thì giữ `returned`; BASE evidence disputed giữ `awaiting_base` kèm verification disputed, không tự biến thành BASE rejected. Không ghi paid hoặc phát sinh account move từ các trạng thái đó.

## I — Hóa đơn, thu/chi, công nợ và kế toán (TP Finance)

**Purpose/start/end/owner-RACI.** Theo dõi chứng từ hóa đơn, thu/chi, phân bổ, công nợ và đối chiếu; không dựng sổ cái thứ hai. Start khi có request/contract/đối tác và chứng từ; end khi account move/payment được post, reconcile hoặc case được đóng với lý do. Owner đề xuất: Kế toán là A/R cho posting/reconcile; QT-TC là A riêng cho review/control record (C ở posting); KD/Project Owner là C source; BASE là official duyệt chi khi áp dụng; auditor/leadership là I. **Input:** request/acceptance/contract links, invoice/bank/receipt evidence, account/tax/analytic config và kỳ kế toán. **Output:** draft/posted `account.move`, payment, reconciliation/residual, exception và audit; official ledger vẫn ở Odoo Account. **Handoff:** FINANCE review ↔ source owner; posted/reconciled → TP Dashboard/KD; reversal/correction → source owner và audit, không xóa chứng từ.

| Từ → đến | Actor/capability; scope | Guard | Evidence/output; history/notification |
|---|---|---|---|
| `observation → finance_review` | FINANCE; `finance.review`; company/project/partner | source doc, currency/tax basis, period, duplicate check; unknown giữ unknown | review checklist, mapping; audit; notify source owner |
| `finance_review → ready_to_post` | Accountant; `accounting.prepare`; company/ledger scope | Odoo account/tax/analytic configuration, balanced lines; không đoán tax/gross-net | draft account move; link source; notify approver |
| `ready_to_post → posted` | Authorized accountant; `accounting.post`; ledger company | Odoo validation/period open/authority; posting là official | `account.move` posted, immutable history; notification |
| `posted → reconciled/partially_reconciled` | Accountant; `accounting.reconcile`; partner/account scope | matched bank/receipt/payment, amount/currency; không lấy request làm cash | reconciliation links, residual; audit/notify |
| `finance_review → returned/rejected` | FINANCE reviewer; `finance.review` | missing/duplicate/invalid evidence + reason | issue list, no posting; notify preparer |
| `returned → finance_review` (bộ sửa mới); `rejected → observation` (case mới nếu có căn cứ) | Source owner chuẩn bị; FINANCE `finance.review`; cùng scope | version/chứng từ mới, lý do mở lại, xử lý duplicate trước post; không sửa chứng từ đã posted | giữ hồ sơ cũ và correction links; audit; notify reviewer |
| `posted → reversed/corrected` | Accountant; `accounting.reverse/correct`; source/period scope | approved reversal/credit/debit note, reason, link original; không delete | reversal/correction documents, audit; notify stakeholders |

BASE approval, chữ ký, hiệu lực và posting/reconcile là các lớp khác nhau. Công nợ quản trị chỉ tính từ account/links đã đối chiếu; thiếu feed kế toán là `missing_source`. Không đặt ngưỡng chênh lệch; 1.000 VND trong nguồn chỉ là cảnh báo đối chiếu, không phải duyệt chi. GAP: Q1 (thẩm quyền), Q4 (tax/basis/currency/date), Q6 (feed/lịch đối chiếu), Q8 (sửa sau thanh lý).

Tên state bảng I là nhãn nghiệp vụ để thảo luận, không phải thêm field `state` cho `account.move`: posting state, payment state và residual/reconciliation là các chiều native khác nhau. Bridge phải gọi action native và đối chiếu edition/module/localization đang cài; chưa chứng minh kế toán, ngân hàng hoặc hóa đơn điện tử đã vận hành chỉ từ source `addons/account` có sẵn.

**Acceptance examples.** Chấp nhận: invoice posted, payment matched một phần, residual công nợ hiển thị theo Odoo và link request/acceptance. Từ chối: chứng từ trùng hoặc tax basis chưa xác nhận; finance trả về, không tạo move và dashboard đánh dấu missing/unknown.

## J — Hồ sơ, version, chia sẻ và lưu trữ (TP Documents)

**Purpose/start/end/owner-RACI.** Quản lý metadata, version, checksum, quyền chia sẻ, retention/archive của hồ sơ xuyên A–M. Start khi tạo record/document; end khi archived theo policy hoặc retained legal hold. Owner đề xuất: Văn thư/Document Controller (A/R); record owner (R); KCS/Finance/Legal (C); IT (filestore/backup); recipient (I). NAS là nguồn tham khảo/legacy; runtime là Odoo metadata + filestore/adapter đã kiểm quyền. **Input:** hồ sơ từ A–M, classification/confidentiality, source binding, revision và retention/legal-hold metadata. **Output:** immutable document versions, checksum, access/share/revoke/archive events và index; file tải chỉ sau backend scope check. **Handoff:** reviewed/approved_for_use → owner/KD/KCS/Finance; superseded/rejected → author; archived → audit/IT theo retention.

| Từ → đến | Actor/capability; scope | Guard | Evidence/output; history/notification |
|---|---|---|---|
| `draft → uploaded` | Owner; `document.prepare`; project/department | classification, source binding, checksum, filename; không upload vào scope khác | attachment metadata/version; audit; notify owner |
| `uploaded → reviewed` | Reviewer/KCS/Finance; `document.review`; scope | readable file, malware/format check theo vận hành, required metadata | review result/issues; notify uploader |
| `reviewed → approved_for_use` | designated owner; `document.use_confirm`; contract/project scope | link to immutable revision/evidence; BASE/signature/legal status không suy từ file | usable version, audit; notify consumers |
| `approved_for_use → superseded` | Owner; `document.revise`; same record/scope | reason, previous version, diff/checksum; bản thay thế đã approved_for_use; old version read-only | replacement version/provenance; notify consumers |
| `uploaded/reviewed → rejected` | Reviewer; `document.review` | reason and issue list | rejected flag/history; notify uploader |
| `approved_for_use → archived` | Controller; `document.archive`; policy/legal hold scope | retention/hold check, archive reason, index remains searchable per policy | archive event, access audit; notify owner |
| Authorization `no_share → share_requested → shared` | Owner với `document.share`; recipient/scope cụ thể | document phải `approved_for_use`, grant/confidentiality, expiry/recipient; no public token/UNC | share record/decision/audit; notify recipient/owner |
| Authorization `shared → revoked` | Owner/HR/IT với `document.share_revoke`; recipient/project scope | departure/role-change/expiry or reason; revoke downstream links too | revoke audit; notify recipient/owner |
| `archived → uploaded` (unarchive) | Controller; `document.archive_restore`; record/scope | policy/legal hold, reason và re-review/re-approval; không tự phục hồi signed/effective | restore event + new review; notify owner |
| `rejected → draft` (bản mới) | Author; `document.revise`; cùng scope | reason/issues đã xử lý; version mới liên kết bản bị reject | new version, giữ rejection cũ; audit; notify reviewer khi resubmit |

Authorization của share record là chiều riêng với document review/version/archive. Financial/legal files require grant/capability; filename, preview, chatter, notification và audit không lộ số tiền. `share` không đổi source permission; revoke phải có hiệu lực request sau. Duplicate file giữ checksum/link and case; missing file là broken reference, không tự coi complete. Backdate/retention/legal hold theo Q4/Q8; GAP Q11: thời hạn, legal hold, e-sign provider, DLP/virus và NAS migration.

**Acceptance examples.** Chấp nhận: hồ sơ design `R2` có checksum, KCS result, recipient scope và supersedes `R1`; download ngoài project trả 404. Từ chối: file financial chia cho SUPPORT không có grant; share bị từ chối, notification không chứa số tiền.

## K — HR, tổ chức, bàn giao và cấp/thu hồi quyền (TP HR)

**Purpose/start/end/owner-RACI.** Quản lý tổ chức, vị trí, assignment, onboarding/offboarding, bàn giao và quyền theo capability/scope. Start từ quyết định nhân sự/phân công; end khi assignment active/handed-over hoặc revoked/closed có audit. Owner đề xuất: QT-TC/HR là A cho nhân sự/assignment record; trưởng phòng/Project Owner là R/C; IT/Platform Manager là R cho provisioning kỹ thuật (không phải A nhân sự); lãnh đạo là I hoặc A nếu văn bản giao riêng; user là I. Không suy quyền từ title; `tp.project.assignment` hiện chỉ là nền đọc project và `financial_read` grant hiện chỉ superuser khi Q2 chưa chốt. **Input:** quyết định nhân sự, company/department/project scope, assignment/task/document inventory và departure/role-change evidence. **Output:** assignment/grant/revocation, handover checklist, open-item owner và audit/notification. **Handoff:** approved → IT provision; handed-over → incoming owner; revoked → HR/IT/audit và downstream task/document owners.

| Từ → đến | Actor/capability; scope | Guard | Evidence/output; history/notification |
|---|---|---|---|
| `requested → approved` | HR/manager; `org.assignment_review`; company/department/project | quyết định/role/scope/start/end, conflict/duplicate check; Q2 approver cần xác nhận | assignment request + decision; notify user/owner |
| `approved → provisioned` | ACCESS-OPS (IT được giao); `access.provision`; exact capability/scope | no self-grant, least scope, active employee, quyết định ACCESS-DEC; thao tác không tự mở rộng scope | grant/assignment audit có decision link + actor kỹ thuật; notify user/manager |
| Handover `open → handed_over` | Outgoing/incoming owner + manager; `handover.record`; project/department | inventory open tasks/docs/keys, recipient acknowledgement, effective date; grant có state riêng | handover checklist, links; notify stakeholders |
| Quyết định thu hồi/tạm dừng grant (không thay grant ngay) | ACCESS-DEC theo ủy quyền; company/project/capability scope | Căn cứ HR/role-change/security, reason, thời điểm và scope; quyết định riêng với thực thi | decision/evidence/actor/time; notify ACCESS-OPS |
| Grant `provisioned/suspended → revoked` hoặc `provisioned → suspended` | ACCESS-OPS; `access.revoke`; company/scope đúng quyết định | decision link, revoke time/reason, preserve records; không đợi giả biên nhận handover; không tự tăng quyền | revocation audit + decision link; notify user/owners |
| `requested → rejected` | HR/manager; `org.assignment_review` | reason, missing authority/scope | rejection history; notify requester |
| Request `rejected → requested` (request mới); grant hết hạn/thu hồi không tự khôi phục | HR/manager `org.assignment_review`, IT `access.provision`; exact scope | quyết định/căn cứ mới, lý do, kiểm quyền mới; không copy grant cũ | new request/grant links, audit; notify user/manager |

Departure/role change must revoke grants and shares, reassign open tasks/docs, preserve audit and avoid deleting posted/legal records. Duplicate assignment, overlapping grants or wrong company/project are validation failures; backdated effective date requires authority and keeps recorded_at. Break-glass admin access is technical and separately audited. GAP: Q1/Q2 approval authority, HRIS source, delegation, time rules, payroll/contractor policy, emergency access and retention.

**Acceptance examples.** Chấp nhận: user được phân công project P với `task.result_submit`, nhận checklist bàn giao và chỉ thấy financial khi grant riêng còn hạn. Từ chối: SUPPORT tự cấp `financial_read` hoặc assignment project khác company; backend rejects, no token/file leak, audit records attempt.

Request nhân sự, assignment/grant, handover và departure case là record riêng; `handed_over` không thay trạng thái còn hiệu lực của grant. Quyết định nhân sự/ủy quyền có căn cứ và chữ ký riêng; review HR hoặc thao tác IT không thay chữ ký/BASE/pháp lý. Hồ sơ lương, BHXH, khoán cá nhân và năng lực/chứng chỉ là dữ liệu nhạy cảm cần catalog/privacy Q11, chưa được mở thành payroll engine.

Phân công Q2-P1 tại [KD mục 7.4](TP_KD_WORKFLOW_AND_PERMISSIONS.md#74-ma-trận-q2-p1--trách-nhiệm-và-quyền-cần-xác-nhận) tách ACCESS-REQ, ACCESS-DEC và ACCESS-OPS theo trách nhiệm; công ty chưa xác nhận bắt buộc khác cá nhân. Nhật ký và bundle mô phỏng bàn giao B03 ở [readiness 7.1](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#71-nhật-ký-quyết-định-và-nghiệm-thu-điền-khi-review); không có quyền/nghiệp vụ mới nào được kích hoạt từ tài liệu này.

## L — Dashboard, KPI, cảnh báo và báo cáo (TP Dashboard)

**Purpose/start/end/owner-RACI.** Tổng hợp read-only theo scope, hiển thị nguồn, as-of, freshness và cảnh báo độc lập; không tạo/duyệt state. Start khi query/report run; end khi snapshot trả về hoặc job lỗi được ghi. Owner đề xuất: TGĐ/QT-TC (A KPI); domain owners (R source quality); BI/reporting (R build); IT (C operation); auditors (I). **Input:** typed domain records/F–K, definitions, scope, as-of/freshness and source snapshots. **Output:** KPI/report snapshot, formula/source links, complete warning list and quality status. **Handoff:** warning/blocked → domain owner/incident; published result → authorized readers; no write-back to domain state. KPI definitions phải tham chiếu [TP_BIZ002_INTEGRATION_AND_REPORTING.md](TP_BIZ002_INTEGRATION_AND_REPORTING.md), data dictionary và Q4/Q6; không dùng JS float để quyết định tiền.

| State | Actor/capability; scope | Guards/evidence | Output/history/notification |
|---|---|---|---|
| Definition `draft → defined` | KPI owner; `report.define`; company/project scope | formula, unit/currency/basis, source models, owner, as-of/freshness; chưa có threshold nếu chưa xác nhận | versioned definition; audit/notify reviewer |
| Definition `defined → published` | Reporting owner; `report.publish`; company/project scope | validation against fixtures, permission fields, no hidden aggregation; source links | published definition/version; audit |
| Definition `defined → returned`; bản sửa mới `draft → defined` | KPI owner/reviewer `report.define`; cùng definition/scope | reason, công thức/nguồn/field policy sửa theo checklist; version mới, chưa publish | giữ ý kiến/version cũ, audit; notify author/reviewer |
| Run `queued → refreshed` | scheduler/user; `report.run`; definition + caller scope | source snapshot/time, scope, query allowlist; missing/unknown preserved | run result + provenance/freshness; notify only actionable failure |
| Run quality `unchecked → warning/blocked/validated` | system/domain owner; `report.quality_manage`; source scope | stale/missing/unmapped/duplicate or policy breach; no invented value | warning list/incident link; notify owner |
| Definition `published → superseded/retired` | KPI owner; `report.revise`; company/project scope | reason, effective version, preserve historical outputs; revision mới từ draft | revision/retire audit; notify consumers |

Warning list must retain all warnings (coverage, unmapped, missing accounting, duplicate, stale); priority label must not hide others. Examples of proposed indicators: production vs acceptance, acceptance vs invoice/cash, retention outstanding, task freshness, KCS returns, allocation level-1 vs level-2; formulas/thresholds/cadence remain GAP/Q4–Q7/Q13. Definition, report run và run quality là ba chiều riêng, không đổi state nguồn nghiệp vụ. A report is not BASE approval, legal evidence or ledger. `null` and 0 remain distinct; cohort year from project code is not accounting period.

**Acceptance examples.** Chấp nhận: as-of report shows acceptance 80, invoice 80, cash 72, retention 8 with source links and freshness. Từ chối: accounting source missing; report labels `missing_source`, keeps other warnings and does not display zero or “paid”.

## M — Import, audit, notify, backup/restore và incident

**Purpose/start/end/owner-RACI.** Vận hành an toàn dữ liệu, provenance, thông báo, backup/restore và xử lý sự cố cho A–L. Start từ file/event/job/incident; end khi published/reconciled, backup verified, restore rehearsed, or incident closed with evidence. Owner đề xuất: Data Steward/Domain owner (R import); IT/Platform (A backup/restore/incident); Security/Audit (C); business owner (A acceptance); recipients (I). **Input:** source file/event, model/binding, audit/notification policy, DB+filestore+source/config và incident evidence. **Output:** staging/error/reconciliation, immutable audit/delivery log, backup manifest/restore report và incident timeline/actions. **Handoff:** released import → domain owner; failed notification/backup/restore → incident; accepted restore → operations/business owner. `scripts/backup_restore.py` đã có diễn tập local OPS-001; production RPO/RTO, mã hóa, kho ngoài máy và lịch giữ vẫn GAP.

| Luồng/state | Actor/capability; scope | Guards | Evidence/output; history/notification |
|---|---|---|---|
| Import `file_received → staged → mapped → validated → released/rejected` | Steward; `import.prepare/validate/release`; source/company/project scope | file SHA256, source/sheet/row, parser version, binding; mapping approval; duplicate/idempotency; ORM release only | row errors/reconciliation/provenance; notify steward/owner |
| Audit event `emitted → recorded` | System records actor/time/before-after/reason/request/version; scoped reader `audit.read_scoped` | immutable append-only, field redaction by scope, correlation id; no physical delete | audit record; alerts for anomalies |
| Audit case `open → reviewed → closed/reopened` | Auditor/owner; `audit.review`; related record/scope | case links immutable events, review result/reason; close only after evidence/action | case outcome, follow-up notification; reopening keeps history |
| Notify `queued → sent/acknowledged/failed` | System/owner; recipient scope | template, sensitivity, dedupe/idempotency, no financial leakage; failed retry policy | delivery log/ack/failure; notify owner only on actionable failure |
| Backup `planned → captured → verified → retained/expired` | IT; `backup.run/verify`; environment scope | DB+filestore+source/config version; checksum, manifest, access control; no credential in Git; expiry chỉ sau Q14/hold policy | backup manifest/report; alert failure; chưa tự xóa payload |
| Restore `requested → rehearsed → accepted/rejected → cleaned` | IT + business owner; `restore.rehearse/accept`; isolated target | checksum/fingerprint, attachment bytes, login/API/scope tests, cleanup; never overwrite production implicitly | restore report, evidence, incident link; notify stakeholders |
| Incident `detected → contained → investigated → recovered → closed/reopened` | IT/Security; `incident.manage`; tenant/env scope | severity/timeline/impact/containment; preserve logs/evidence; no blame-only closure | incident timeline/root cause/actions; notifications/escalation per unconfirmed policy |

**Ngoại lệ.** Import row missing/duplicate/mismatched scope is rejected per row and remains staging; cả batch quarantine mặc định; partial release chỉ nếu Q12 xác nhận policy/transaction/reconcile riêng. Re-run same file/binding is idempotent; changed payload with same binding blocks. Sensitive transition và audit cùng transaction: không ghi được audit thì rollback, incident được ghi qua kênh vận hành phù hợp; không bỏ lịch sử. Notification failure does not change business state; retry is safe. Restore never uses production credentials in dev; backup/restore errors remain open incidents. `cleaned` nghĩa đã dừng đúng process/cổng của bản diễn tập và xác nhận dev gốc, không mặc định xóa DB/artifact. Backdate is preserved with source date and recorded_at. GAP Q14: retention/RPO/RTO, encryption/key custody, external storage, notification channel/retention, incident severity/escalation and legal reporting.

**Acceptance examples.** Chấp nhận: một batch giả lập có hash/file/sheet/row và mapping đã xác nhận; hết lỗi, totals đối chiếu đạt, release đúng một lần bằng ORM. Hai dòng sai của batch khác vẫn nằm staging và chặn release batch đó; chưa mặc định partial release. Từ chối: cùng source binding nhưng payload khác hoặc mã dự án nhập mơ hồ; import bị block, audit ghi nguyên nhân, không tạo trùng hợp đồng/tiền. Restore chỉ đạt khi checksum, rowset/attachment và scoped login/API probes khớp như OPS-001; mismatch bác bỏ diễn tập và mở incident.

## Ma trận ngoại lệ bắt buộc F–M

Đây là xử lý đề xuất để nghiệm thu; không tự mở action reopen/cancel/void ngoài domain đã triển khai. Người thực hiện có capability tương ứng, cùng scope và phải ghi reason/evidence/version; không xóa hồ sơ đã chốt. `return` là yêu cầu sửa nội bộ; `reject` BASE là quyết định ngoài hệ thống; hai loại không được đổi tên cho nhau.

| Domain | Return / reject | Cancel / revise / reopen | Missing / duplicate | Departure / backdate |
|---|---|---|---|---|
| F khảo sát | KCS trả issue theo đúng đợt; CĐT từ chối là evidence riêng | draft sửa; submitted freeze; sau handoff tạo survey revision, reopen cần review tác động G/H | thiếu nhật ký/điểm đo là missing; trùng hash/source điểm đo giữ nguồn và gắn case, không cộng sản lượng hai lần | đổi chủ nhiệm phải bàn giao raw data/mốc/open issues; ngày đo/biên bản không đổi theo ngày upload |
| G thiết kế/BIM/KCS | Trả checklist/issue có owner; thẩm định/CĐT reject tách KCS nội bộ | release bất biến; revision lại KCS; reopen issue liên kết package cũ, không mở khóa bản phát hành | thiếu survey/discipline/file chặn release; duplicate package theo project/stage/version/hash | departure chuyển owner drawings/model/issue; backdate phát hành cần căn cứ, không sửa recorded_at |
| H sản lượng/NT/request | Production/NT return giữ lý do; BASE reject đúng request version | cancel draft/request; NT confirmed dùng void/correction; reopen sau thanh lý đợi Q8 | thiếu chứng từ/basis là missing; request/payment source duplicate không tăng tổng | task/hồ sơ chuyển owner nhưng chữ ký lịch sử giữ nguyên; backdate cần Q4/kỳ và evidence |
| I hóa đơn/thu/chi | Finance return chưa posting; BASE reject không đảo payment cũ | native reversal/credit note/reconcile correction; không delete posted; kỳ đã khóa theo kế toán | missing feed là missing_source; trùng số hóa đơn/bank/source giữ exception, không auto-post | chuyển accountant không đổi posted actor; ngày chứng từ/kỳ khác recorded_at, khóa theo Q4/Q6 |
| J hồ sơ | Rejected cần lý do và người nhận sửa; không tự thay legal status | supersede/revoke/archive có audit; reopen archive cần legal-hold/policy và recheck quyền | file mất mở incident; hash trùng cho biết content giống, không mặc định hồ sơ cùng pháp lý | revoke shares và giao owner/index; signed/effective dates không đổi khi migrate |
| K HR/quyền | Request thiếu authority/scope bị trả/reject | role change thu hồi grant cũ rồi provision đúng scope; reopen account phải approval mới | thiếu quyết định không cấp; assignment/grant trùng theo key được chặn/đối chiếu | offboarding giữ audit/chuyển việc; ngày hiệu lực nhân sự riêng recorded_at; không xóa lịch sử user |
| L KPI/report | Definition sai bị return; data invalid/missing chưa publish | revise formula là version mới; reopen warning khi nguồn tái lỗi; retire không xóa report lịch sử | source freshness/unmapped/duplicate độc lập; null không thành zero; join không nhân tổng | KPI owner chuyển giao; backdate nguồn làm snapshot mới với business as-of và known-at |
| M nền/vận hành | Validation/reconcile/restore fail giữ evidence và reject run | import correction là batch mới; failed notify retry an toàn; backup/incident reopen giữ timeline | thiếu payload/manifest hoặc checksum mismatch bác restore; retry dedupe theo run/key/binding | IT departure thu hồi access/key theo kế hoạch; audit timestamps không sửa hồi tố, sự kiện nguồn có ngày riêng |

## Mức bằng chứng khi bàn giao và thông báo

Mỗi handoff F–M phải có source record ID/version, company/project/department áp dụng, người giao/nhận, ngày nghiệp vụ và recorded_at, output/evidence hash, open items và acknowledgement hoặc lý do chưa nhận. Giao task không tự cấp quyền document/financial; bên nhận chỉ tải đúng scope. Notification gồm định danh/thông điệp đủ dùng, link kiểm quyền ở backend; giá trị tiền hoặc file nhạy cảm chỉ gửi tới recipient có grant, hoặc dùng thông báo đã che tiền. Thu hồi grant/departure kiểm lại khi gửi và khi mở link.

Nếu input downstream thiếu hoặc bản cũ bị supersede/void/disputed, downstream phải ghi dependency warning/blocked case, thông báo owner và giữ lịch sử; không âm thầm đổi signed/posted record. Chính sách cần re-KCS/re-acceptance/re-BASE/reconcile lại phải chốt trong Q3 (BASE), Q6 (reconcile), Q8/Q9/Q10 theo domain; không mặc định mọi thay đổi đều đòi duyệt lại trên BASE.

## Cross-workflow role/capability and evidence gaps

| Capability (đề xuất) | Phạm vi tối thiểu | Cổng xác nhận |
|---|---|---|
| `survey.prepare`, `design.prepare`, `technical.review` | company/project/department + work item | Q5, owner/RACI |
| `production.prepare/quantity_confirm`, `acceptance.prepare`, `payment_request.prepare` | project/contract/allocation + period | Q4/Q7/Q8, hồ sơ đại diện |
| `finance.review`, `accounting.post/reconcile` | company/ledger/partner theo Odoo | Q4/Q6, kế toán owner |
| `document.share/archive`, `audit.read_scoped` | record/project + confidentiality | Q8, retention/legal hold |
| `access.provision/revoke`, `grant.manage` | exact user/company/project/department | Q1/Q2, HR/IT owner |
| `report.define/publish`, `import.release`, `backup.verify`, `incident.manage` | environment + domain | Q4–Q8, IT/security owner |

Q1–Q8 hiện có trong [TP_KD_WORKFLOW_AND_PERMISSIONS.md](TP_KD_WORKFLOW_AND_PERMISSIONS.md) vẫn là cổng chung: Q1 thẩm quyền/hạn mức; Q2 phân tách lập–soát–record–verify và người cấp grant; Q3 BASE ID/evidence; Q4 thuế/gross-net/currency/ngày/kỳ; Q5 catalog work item/design stage; Q6 hóa đơn/thu/chi/feed/lịch đối chiếu; Q7 vượt khoán mẹ; Q8 sửa/void sau thanh lý, tạm ứng/giữ lại. BIZ-002 bổ sung Q9–Q14 trong [tích hợp/KPI](TP_BIZ002_INTEGRATION_AND_REPORTING.md) và [readiness](TP_BIZ002_ACCEPTANCE_AND_READINESS.md): Q9 project/task/handover; Q10 survey/design/KCS; Q11 hồ sơ/HR/privacy; Q12 import/cutover; Q13 KPI/threshold/export; Q14 backup/RPO/RTO/incident. Khi thiếu căn cứ, trạng thái/role là `proposed` hoặc `unconfirmed`, không tự chuyển sang `confirmed`.

Các câu hỏi thiết kế BIZ-002 bổ sung cần giữ mở trong gói thiết kế/acceptance: **Q9** vòng đời project/task/BASE và handoff; **Q10** tiêu chuẩn khảo sát–thiết kế/BIM/KCS, issue và release; **Q11** HR, khoán cá nhân, privacy và retention hồ sơ; **Q12** data dictionary/catalog/import/cutover; **Q13** KPI, công thức, cadence/freshness và owner cảnh báo; **Q14** vận hành, RPO/RTO/SLA, backup/restore và incident. Tài liệu này chỉ tham chiếu nhóm câu hỏi, không tự chốt chúng.

## Invariants and implementation boundary

- BASE official giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và record kết quả, không làm engine phê duyệt ngang BASE.
- TP Finance bridge liên kết `account.move`/`account.payment`/analytic; không tạo ledger hay posting engine riêng. TP Dashboard chỉ đọc tổng hợp.
- Odoo là nguồn sự thật cho quyền, state, history và công thức; NAS/Excel chỉ source/staging/provenance, không phải runtime database.
- Bản chốt không xóa vật lý; revise/cancel/reopen/void có reason, previous version và audit. Chốt/duyệt/phát hành kiểm optimistic concurrency + idempotency.
- Model/API/frontend tương lai phải map vào [TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md](TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md) và integration/report contract; không thêm addon rỗng chỉ để đủ tên phân hệ.

## Gaps và bước nghiệm thu BIZ-002

Chưa có runtime cho F–M ngoài nền project/assignment, TP Contracts read slice, grant `financial_read` và backup rehearsal local. Trước khi mở action ghi, chủ nghiệp vụ cần xác nhận RACI/owner từng phòng, state/transition, evidence mẫu khử dữ liệu, Q1–Q14 liên quan, scope quyền và acceptance cases trong [TP_BIZ002_ACCEPTANCE_AND_READINESS.md](TP_BIZ002_ACCEPTANCE_AND_READINESS.md). Mỗi vertical slice phải có model → security → API → UI → tests; không coi bảng đề xuất hoặc ca giả lập là nghiệm thu Odoo.
