# BIZ-002 — Kịch bản xuyên suốt, câu hỏi và checklist sẵn sàng code

**Ngày:** 28/10/2026. **Trạng thái:** thiết kế nghiệm thu; các ca dưới đây là dữ liệu giả lập, chưa phải UAT hoặc Odoo test. Không đưa tên người, credential hay số liệu doanh nghiệp thật vào fixture.

## 1. Quy tắc nghiệm thu

Một quy trình chỉ “đủ thiết kế” khi có mục đích/phạm vi/start-end, owner/RACI, input/output/handoff, state/transition, actor/capability/scope/guard, field/evidence, nơi ra quyết định, history/notification/deadline, return/reject/cancel/revise/reopen/backdate/duplicate/absence và ca normal + rejected. “Đã viết bảng” không đồng nghĩa “đã được chủ nghiệp vụ xác nhận”.

Walkthrough dùng một bộ dữ liệu giả lập liên kết ID, ngày, currency/basis và hash giả; mỗi ca ghi actor/scope trước và sau, expected state/DTO/audit/warning. Không nhập vào dev/test runtime chỉ để chứng minh tài liệu. Khi phát triển, chuyển ca thành fixture khử dữ liệu và test model/API/UI riêng; không gọi kết quả walkthrough là test ứng dụng.

## 2. Bộ dữ liệu giả lập xuyên suốt

| ID | Nội dung | Giá trị thiết kế | Cố ý kiểm |
| --- | --- | --- | --- |
| OPP-01 | Cơ hội/gói thầu | company C1, package PB-01, owner role KD, deadline theo hồ sơ | A outcome/handoff |
| PRJ-01 | Project | code P-A, C1, phòng KD, owner PO-1, kế hoạch v1 | B scope/assignment |
| CTR-01 | Hợp đồng | original lines 60 + 40 = 100; currency VND, **basis `excluding_tax` chỉ là basis giả lập của ca, không phải quy định công ty** | C snapshot/read; Q4 vẫn chặn số chính thức |
| REV-02 | Phụ lục | line 60 → 70, line 40 giữ; effective 01/11; snapshot 110 | C no delta double count |
| AL-01/AL-02/AL-03 | Khoán | parent cấp 1 70; hai con 30,45 cùng P-A | E parent/child overrun 5 |
| TASK-01 | Giao việc | owner PO-1, reviewer technical, result v1/v2 | D return/re-submit |
| SUR-01/DES-01 | Khảo sát/thiết kế | evidence v1, issue I-01, revision v2 | F/G review/revision |
| PROD-01/ACC-01 | Thực hiện/NT | production 100; acceptance 80; evidence giả | H tách record |
| PAY-01/INV-01/CASH-01 | Payment/financial | invoice 80; cash 72; retention 8; request pending | I request ≠ cash |
| DOC-01/BATCH-01V/BATCH-01E | Hồ sơ/import | financial doc + general doc; batch V có rows hợp lệ, batch E có legacy row unmapped | J/M security/quarantine |

Các số 60/40/100/80/72/8 là **triệu VND giả lập** cùng basis `excluding_tax` chỉ cho phép thử; production 100 là giá trị quản trị giả lập, không phải khối lượng 100 chưa có đơn giá. Khối lượng/unit được lưu riêng. Chưa cấu hình thuế/rounding doanh nghiệp. N-05 có cash `null` (chưa xác nhận) khác cash xác nhận `0`; N-06 có mapping/source unknown, không đổi thành 0. Không tính tiền bằng JavaScript float.

## 3. Ca nghiệm thu bình thường

| ID | Luồng | Bước chính | Kết quả cần quan sát |
| --- | --- | --- | --- |
| N-01 | A→B | OPP-01 assessing → ready → won; tạo PRJ-01 draft → review → active | Handoff có version/evidence; assignment đúng C1/P-A; không tự cấp financial grant |
| N-02 | B→C | Kế hoạch P-A giao TASK-01; tạo CTR-01 draft → in_review → review_complete; register BASE pending | Task một owner; contract version đóng băng; BASE pending không phải approved/effective |
| N-03 | C→E | Ghi REV-02 sau khi đủ căn cứ; tạo AL-01 cấp 1 và AL-02/03 cấp 2 | As-of trước 01/11=100, sau=110; company total allocation=70; child total=75/cảnh báo +5 |
| N-04 | D→F/G | TASK result v1 bị trả; v2 được nhận; khảo sát tạo evidence → design review/KCS | Bản trả giữ nguyên; v2/handoff có reviewer; file không hạ confidentiality qua task |
| N-05 | G→H→I | production 100 → acceptance 80 → invoice 80 → cash 72/retention 8; request pending; thêm một record cash `null`, một record cash xác nhận `0` | 5 record riêng; request không thành paid; gaps 20/8/0 chỉ là phép thử cùng basis giả lập; DTO giữ `null` khác `0`, cảnh báo missing/unknown không biến thành zero |
| N-06 | J/K/L/M | DOC-01 version/share đúng role; dashboard scope P-A; BATCH-01V đủ mapping; BATCH-01E có row unmapped | File financial chỉ grant; KPI có as_of/known_at; raw row/provenance giữ lại; E bị quarantine và không release cho đến khi mapping được duyệt |

## 4. Ca sửa sai, từ chối và ngoại lệ

| ID | Tình huống | Expected |
| --- | --- | --- |
| X-01 | BASE rejected REV-02 kèm reason | Revision không effective; lý do bất biến; propose version mới; không xóa reference |
| X-02 | BASE approved nhưng evidence pending/authority unconfirmed | UI/API ghi rõ chưa xác minh; effectivity/action phụ thuộc bị chặn |
| X-03 | Hủy draft phụ lục | `review_state=cancelled` theo action/authority sau khi Q; bản gốc vẫn áp dụng; không auto-cancel BASE cũ |
| X-04 | Correction giảm 70→50 hoặc về 0 | Snapshot mới 90 hoặc 40; không bỏ dòng vì giá 0; audit ngày nghiệp vụ/recorded_at tách |
| X-05 | Cash event 72 sửa thành 70 rồi void | Contribution còn 70 hoặc 0 tùy event; không thành 142; posted accounting dùng reversal |
| X-06 | Allocation child khác project/cycle hoặc vượt parent | Constraint/validation fail; không link theo tên; cảnh báo overrun chưa hard-block cho tới Q7 |
| X-07 | Caller metadata P-A, grant financial chỉ P-B | Không amount/aggregate/file P-A qua ORM/RPC/API/export/search/read_group; 404/403 nhất quán |
| X-08 | Grant hết hạn/thu hồi khi session còn mở | Request/tải mới bị chặn; cache không giữ tiền; audit revoke khi có policy |
| X-09 | Người owner nghỉ, hồ sơ duplicate, version conflict | Handoff có biên nhận; duplicate quarantine/owner quyết định; retry stale trả 409, không ghi nửa transaction |
| X-10 | NAS/BASE/accounting unavailable hoặc import row lỗi | Giữ pending/missing_source/quarantine; không giả paid/verified; retry hạ tầng idempotent, lỗi dữ liệu cần sửa/version |
| X-11 | Ký nhưng thiếu điều kiện hiệu lực; project hold | `signed_recorded` nhưng not_effective; project hold chặn action mới theo policy, lưu nghĩa vụ đang chạy |
| X-12 | Bản đã thanh lý nhưng cần sửa/đảo | Tạo correction/void case, đánh giá báo cáo/chứng từ; không xóa lịch sử/posted; Q8 cần xác nhận |

## 5. Walkthrough theo từng quy trình A–M

Mỗi hàng là một ca tối thiểu để chuyển thành fixture/test sau khi slice được phép code. `before → after` là state logic; DTO, audit và warning phải được kiểm ở backend, không chỉ kiểm nút giao diện. Tất cả actor đều phải ở đúng company/project/department scope; BASE/Pháp lý/Kế toán là lớp riêng.

| ID | Quy trình và actor/capability | Sequence/state trước → sau | DTO/evidence sau action | Audit/notify/warning; cổng |
| --- | --- | --- | --- | --- |
| A-N / A-X | KD `opportunity.prepare/assess`, reviewer; C1/department KD | identified → assessing → assessment_ready → bid_preparation → ready_to_submit → submitted → won; X thiếu authority giữ assessment_ready, không cho bước phụ thuộc | opportunity code, checklist version, submission hash/receipt; X reason + source | audit actor/version/evidence; notify owner; warning pending BASE/Q1–Q3; Q1/Q3 |
| B-N / B-X | Project owner `project.prepare/lifecycle_manage`, assigned planner; C1/P-A | draft → review → active → on_hold → active/completed; X thiếu owner không qua review; cancel chỉ khi có căn cứ | project code/assignment/plan baseline/hold reason; X duplicate candidate | handoff receipt, version conflict 409, notify owners; warning open obligations; Q9 |
| C-N / C-X | KD `contract.draft_edit/submit`, reviewer; C1/P-A | draft → in_review → returned → bản mới in_review → review_complete; BASE decision approved và verification pending → verified là hai field; X rejected/cancelled theo lớp tương ứng | revision/previous/hash/BASE ref; X correction/cancel reason | financial fields redacted without grant; audit before/after; notify reviewer; pending authority/effectivity warning; Q1–Q4/Q8 |
| D-N / D-X | Planner `task.assign`, owner `task.result_submit`; P-A/task | assigned → in_progress → result_submitted → completed; X return/reopen/owner absent | one owner, result version, handoff receipt; X return issue list | deadline warning without auto-reject; audit notification scoped; Q9 |
| E-N / E-X | Allocation owner `allocation.submit/settle`; C1/P-A/parent | draft → in_review → ready_for_execution → executing → settlement_review → completed; X wrong parent/cycle không lưu/không chuyển bước | parent ID, level, source line, value/currency/basis; warning child>parent | audit links and overrun warning (+5); no double count/vendor bill; Q7/Q8 |
| F-N / F-X | Survey lead `survey.prepare/start/result_submit`, technical reviewer; P-A | draft → planned → in_field → submitted → kcs_passed → handed_over; X duplicate/missing point → returned | dataset/version, measurement metadata, checksum, field note; X duplicate_of/missing | evidence hash, notify reviewer; missing data/accuracy warning; Q10 |
| G-N / G-X | Designer `design.prepare/revise`, BIM-QC `technical.review`; P-A | brief → drafting → internal_review → returned → bản mới drafting/internal_review → kcs_passed → released; X failed KCS → returned | package/revision, issue IDs, checksum, KCS result; X supersedes link | audit issue severity, notify author/consumer; released ≠ BASE/legal; Q5/Q10 |
| H-N / H-X | Technical `production.quantity_confirm`, acceptance owner, Finance request preparer; P-A | production submitted → confirmed; acceptance reviewed → confirmed sau chữ ký/guard; request draft → finance_review → ready_for_base → awaiting_base; X trả nội bộ/BASE rejected ở đúng record | quantity/period/evidence; acceptance scope/sign; request amount/terms/BASE ref | null/0 preserved; notify Finance; warning request pending/retention; Q4/Q8 |
| I-N / I-X | Accountant `accounting.post/reconcile`; company ledger/P-A | observation → finance_review → ready_to_post → posted → partially_reconciled/reconciled; X duplicate/tax unknown → returned | `account.move`/payment/reconcile links, currency/tax/period; X reason | audit immutable/reversal link, notify source owner; missing_source not zero; Q4/Q6 |
| J-N / J-X | Document owner `document.prepare/share`, controller `document.review/archive`; P-A | draft → uploaded → reviewed → approved_for_use → superseded/archived; X share without grant → denied | metadata/version/hash/classification/share recipient; X 404/reason | download/share/revoke audit, no filename leakage; warning retention/legal hold; Q11 |
| K-N / K-X | ACCESS-DEC quyết định, ACCESS-OPS `access.provision/revoke`, HR-HANDOVER phối hợp; C1/P-A | Request requested→approved/rejected; grant provisioned→revoked; handover open→handed_over riêng; X self-grant/departure theo record tương ứng | assignment/grant scope, start/end, decision link, handover ack, revoke reason; X no token | audit quyết định/thao tác riêng; notify incoming/old owner; cùng/khác người còn Q2; Q1/Q2/Q11 |
| L-N / L-X | KPI owner `report.define/publish`, reader `report.run`; scope P-A | draft → defined → published → refreshed; X stale/missing source → warning/blocked | metric formula, as_of/known_at/freshness, source links; X `missing_source`/unknown | all warnings retained; notify owner on actionable failure; no financial aggregate outside grant; Q4/Q6/Q13 |
| M-N / M-X | Steward `import.validate/release`, IT `backup.verify`, `restore.rehearse/accept`, incident owner; env/scope | batch file_received → staged → mapped → validated → released/rejected; backup captured→verified; X duplicate/restore mismatch → quarantine/incident | SHA-256/binding/row report/reconcile; backup manifest/restore fingerprint; X error rows/incident timeline | immutable audit/delivery, no partial release unless Q12 policy; alert failed restore; Q12/Q14 |

### 5.1. Sửa sai và ngoại lệ của từng đường bàn giao

| Ca | Đầu vào giả lập và hành động sửa/ngoại lệ | Kết quả kiểm logic cần giữ khi nghiệm thu |
| --- | --- | --- |
| A-R | PB-01 được giao trực tiếp; kết quả công bố sau đó đính chính | Không tạo receipt đấu thầu giả; correction kết quả liên kết bản cũ, thông báo owner B/C; tên gói giống không tự merge |
| B-R | P-A complete nhưng retention 8 còn tồn; mở lại vì thay phạm vi, owner cũ nghỉ | Complete thực hiện giữ nghĩa vụ I; reopen về review bằng căn cứ mới; handover chưa nhận thì vẫn unresolved, không tự khôi phục grant |
| C-R | Revision 110 sửa thành 90 hoặc 40; đã ký nhưng thiếu điều kiện; effective date trùng | Giữ 100/110 lịch sử, snapshot mới 90/40; unsigned/authority pending không bị suy effective; trùng ngày trả conflict, không chọn ID cuối |
| D-R | Người phối hợp upload; owner vắng; bản completed cần reopen | Upload không đổi owner; biên nhận bàn giao cần người nhận; result v1 không sửa đè, v2 có reason/checklist và notify downstream |
| E-R | Khoán mẹ 70 đang executing điều chỉnh xuống 65, con vẫn 75; quyết toán còn giữ lại | Version mới và warning vượt 10; tổng company dùng cấp 1 mới 65, không 140; không sửa NT/contract/cash con tự động |
| F-R | Điểm đo thiếu hoặc trùng; hồ sơ đã handed_over được hiệu chỉnh | Không điền zero; giữ raw + duplicate_of; revision mới re-KCS/biên nhận, G nhận dependency warning, bản đã nhận không tự thay |
| G-R | Bản released hash H1 cần sửa clash, author đổi việc | Bản H1 chỉ đọc; bản mới drafting→review/KCS→released hash H2, supersedes có lịch sử; reviewer/người nhận đúng scope, không tự xác nhận CĐT |
| H-R | Tạm ứng 20 trước NT theo điều khoản giả lập; bù 5 và hoàn 3; retention 8 giải tỏa 3 rồi 5 | Không NT giả; dư tạm ứng 12; retention còn 5 rồi 0, không trừ hai lần; void/correction có căn cứ/Q8, không tự tạo cash |
| I-R | Request 80 trả hai lần 30+42; payment 50 phân bổ 20+30 cho hai request; kỳ khóa | Request còn 8 theo links giả lập; payment đếm một lần 50; over-allocation bị chặn; hồi tố/kỳ khóa theo kế toán, correction bằng reversal/link |
| J-R | Archive bản kỹ thuật, restore; legal hold; người nhận nghỉ | Restore recheck quyền và review bản nếu cần; archive không phá hold/xóa hồ sơ; share revoked chặn request sau, file ngoài quyền 404 |
| K-R | Điều chuyển người có quyền tiền P-A sang P-B, còn TASK-01 chưa nhận bàn giao | Không copy grant P-A sang P-B; thu hồi/share audit theo thời điểm và người nhận; task chưa nhận vẫn mở, không sửa người ký/actor lịch sử |
| L-R | Không due date, thiếu KT, source cũ, unmapped cùng lúc; query user chỉ có tiền P-B | age/overdue công nợ = unknown, không false zero; giữ đủ warning; tổng P-A không có tiền, known_at trước correction giữ số cũ |
| M-R | BATCH-01E có 2 lỗi, notification fail, audit write fail, restore mismatch | Cả batch quarantine mặc định; retry notification không đổi state/không gửi trùng; audit fail rollback transition và mở incident; restore rejected, không thay DB gốc; expiry backup theo Q14 chưa tự xóa |

Các kết quả trên được rà soát bàn giấy theo guard và phép tính giả lập; nội dung chưa có căn cứ để định luật công ty vẫn là D/Q. “Kết quả cần giữ” chưa phải bằng chứng ứng dụng đã thực thi. Điều kiện bước chuyển không đạt thì walkthrough kết luận bị chặn ở đúng record, không tạo approval/chữ ký/chứng từ giả để đi tiếp.

## 6. Ma trận đầu vào/đầu mối phải chốt

| Nhóm | Câu hỏi | Cần tài liệu/bằng chứng | Đầu mối theo vai trò | Cổng bị chặn |
| --- | --- | --- | --- | --- |
| Q1 | Ai được ký/duyệt/hạn mức/ủy quyền theo loại? | quyết định/phân công có hiệu lực | Lãnh đạo/Pháp chế | action legal/auto-routing |
| Q2 | Ai lập/soát/record/verify và cấp/thu hồi grant? | ma trận capability có người chịu trách nhiệm | Chủ nghiệp vụ/Platform | pilot write/grant admin |
| Q3 | BASE ID/evidence/hash/reference thực tế? | 1–3 hồ sơ khử dữ liệu | KD/BASE owner | evidence sync/verification |
| Q4 | VAT/gross-net/currency/rounding/date hồi tố/kỳ khóa? | contract/finance sample | QT-TC/Kế toán | official calculations/import |
| Q5 | Catalog work item/discipline/stage mapping? | master được duyệt | Kỹ thuật/BIM/KD | design/import/report |
| Q6 | Invoice/thu/chi/reconcile feed và cadence? | account config/chứng từ mẫu | Kế toán/QT-TC | FIN bridge/KPI cash |
| Q7 | Vượt khoán mẹ xử lý cảnh báo hay block? | quy chế/giao khoán | KD/QT-TC/lãnh đạo | allocation close |
| Q8 | correction/void sau thanh lý, retention/advance? | policy + hồ sơ thực tế | Lãnh đạo/QT-TC/Pháp chế | settlement/reopen |
| Q9 | Mở/hold/complete/reopen project; handover/task tool? | quyết định vận hành | Lãnh đạo/KD/phòng | PRJ/task pilot |
| Q10 | Survey/design/KCS reviewer, release, issue/revision? | checklist chuyên môn | Kỹ thuật/BIM/KCS | Survey/Design |
| Q11 | File classification/share/retention/privacy; HR leaver/delegation? | policy hồ sơ/nhân sự | HR/Docs/Pháp chế | Documents/HR |
| Q12 | Legacy mapping/batch/cutover/reconcile owner? | mapping + sample rows | Data owner/KD/QT-TC | import/pilot |
| Q13 | KPI owner/formula/cadence/threshold/export scope? | dashboard catalogue được duyệt | Lãnh đạo/KD/QT-TC | reporting |
| Q14 | RPO/RTO/retention/encryption/backup host/incident SLA? | ops runbook/approval | Ops/Platform/lãnh đạo | production |

Không chờ các Q ngoài phạm vi để hoàn thiện read-only/document design; không dùng câu hỏi chưa trả lời để tự đặt default quyền hay threshold.

## 7. Checklist sẵn sàng bắt đầu code theo slice

Một slice chỉ đạt “đủ điều kiện code” khi tất cả ô bắt buộc của slice có owner và bằng chứng; “đề xuất” có thể đủ cho draft trên test nếu không chạm pháp lý/tiền thật, nhưng phải ghi rõ giới hạn.

| Slice | Đủ khi | Không được làm trước cổng |
| --- | --- | --- |
| BIZ-002 documentation baseline | Link/checker sạch; process/data/integration/scenario/readiness được review; quyết định/gap ghi status | Không coi tài liệu là UAT/chốt quy chế |
| A cơ hội/đấu thầu | Owner KD, outcome/direct-award/duplicate rules, evidence version/submission, actor scope trước project, Q1/Q3 liên quan | Không tự cho nộp thầu/ký/bảo lãnh hoặc auto-routing từ chức danh |
| PRJ-002 project lifecycle | Q9; transition/assignment/handover/hold rules; audit/concurrency; owner + sample | Không mở active/complete/cancel tùy ý từ frontend |
| CTR-002a draft/submit/return trên test | Có action matrix + actor fixture/capability test rõ scope, state code KD 4.4; CSRF/version/idempotency/audit/negative tests; dữ liệu giả. Q2 cần trước cấp quyền người dùng thật/pilot, không dùng fixture làm quyết định quyền công ty | Không record/verify BASE, ký, effectivity, payment hoặc mở grant admin; cancel revision nằm ngoài slice tối thiểu nếu actor/thẩm quyền còn Q |
| D giao việc/kết quả | Q9; một owner, recipient review, deadline basis, dependency/handover, bản kết quả/reopen và tài liệu đã phân loại | Không thay công cụ chính thức hoặc biến complete task thành NT tiền |
| ALC-001 allocation | Q7/Q8 liên quan; parent-child/currency/scope/reconcile sample; grant policy | Không cộng cấp 2 hoặc tạo PO/bill giả |
| F/G survey/design | Q10 + taxonomy/reviewer/evidence/version/attachment policy; issue/revision tests | Không gọi review nội bộ là legal release |
| STL-001 settlement | Q4/Q6/Q8; production/acceptance/request/cash/retention links; accounting sample; negative cases | Không tự post/reconcile hoặc suy paid từ approval |
| J/K documents/HR/grant | Q2/Q11; capability/scope/field/file matrix; joiner/mover/leaver/revoke audit | Không mở grant self-service hoặc share UNC/public token |
| L reporting | Q13; formulas/source/as-of/known-at/freshness; aggregate permission tests | Không tạo reporting DB/cache bypass scope |
| M import/ops | Q12/Q14; hash/batch/mapping/quarantine/release/reconcile; restore/incident evidence | Không import toàn Excel thật, chạy macro, production cutover |

**Cổng kỹ thuật sau khi được phép code:** model → security → API/OpenAPI → frontend → meaningful tests; action backend transaction/version/idempotency/audit; `git diff --check`; cập nhật status/changelog/workflow. Không dùng checker `finish` để tuyên bố nghiệp vụ được duyệt.

**Đánh giá hiện tại:** A–E/H đủ cấu trúc thiết kế để review theo walkthrough, với Q1–Q9 liên quan vẫn mở; I có thiết kế ranh giới kế toán và công thức quản trị, chưa đủ số liệu/tax/reconcile chính thức. F/G/J/K/L/M là khung chi tiết có điều kiện chờ chủ chuyên môn (Q10–Q14 và Q liên quan). Không có quy trình mới nào đủ điều kiện pilot/production chỉ từ gói tài liệu. Sau khi người dùng chọn chuyển giai đoạn, phạm vi gần nhất có thể bắt đầu với dữ liệu giả là CTR-002a tối thiểu theo dòng trên; các slice còn lại qua cổng riêng, không mở action pháp lý hoặc dữ liệu thật trước xác nhận.

### 7.1. Nhật ký quyết định và nghiệm thu (điền khi review)

Bảng này là nơi ghi **kết luận thực tế** sau mỗi buổi review. Không điền tên người, mã hồ sơ thật hoặc nội dung nhạy cảm vào Git; dùng mã vai trò, mã bundle đã khử dữ liệu và hash/tham chiếu tới kho bằng chứng được kiểm soát. Một dòng chỉ được chuyển sang `accepted` khi có người chịu trách nhiệm được ủy quyền, phạm vi/môi trường, bằng chứng, ngày và phiên bản kết luận.

Trạng thái dùng thống nhất: `open` (chưa review), `proposed` (đề xuất đang xem), `accepted` (đã xác nhận trong phạm vi ghi), `rejected` (không chấp nhận, phải có lý do), `deferred` (hoãn, có ngày/điều kiện xem lại). `technical_check_passed`, `business_acceptance_pending` và `code_phase_unauthorized` là ba trạng thái độc lập; kiểm tra kỹ thuật không thay cho nghiệm thu nghiệp vụ hoặc quyết định mở giai đoạn.

| Mã Q/slice/bundle | Phạm vi và môi trường | R/A/C/I hoặc vai trò xác nhận | Kết luận/trạng thái | Bằng chứng khử dữ liệu — mã/hash | Người review và ngày/phiên bản | Gap, lý do hoặc bước tiếp theo |
| --- | --- | --- | --- | --- | --- | --- |
| Q2-A | KD/BASE; review tài liệu offline, chưa quyền người dùng thật | R đề xuất KD-PREP/REVIEW-C/F/T/BASE-REC/VER; A và người xác nhận do công ty chỉ định, còn thiếu | `proposed`; ma trận Q2-P1 có 5 action hồ sơ/BASE, chưa xác nhận bổ nhiệm hoặc cùng/khác người | KD 7.4; `U-20261028-Q2-ANALYSIS` (mục 7.1.1); chưa có văn bản ủy quyền | AI rà soát 28/10/2026, Q2-P1; công ty chưa nghiệm thu | Chủ nghiệp vụ KD/chủ nguồn BASE chỉ định vai trò, scope, căn cứ; Q1/Q3 vẫn mở |
| Q2-B | Grant/handover; review offline, chỉ fixture khi phát triển test | R đề xuất ACCESS-REQ/DEC/OPS, HR-HANDOVER; A/owner capability cần công ty chỉ định | `proposed`; tách quyết định và thao tác, chưa bắt buộc hai cá nhân; không cấp quyền thật | KD 7.4, dictionary 7.1, workflow K; cùng tham chiếu phản hồi U ở trên | AI rà soát 28/10/2026, Q2-P1; chưa có xác nhận công ty | Owner quyền/HR/Platform xác nhận grant/revoke/handover và thời điểm; runtime thiếu ledger/export cap riêng |
| BIZ-002-B01 | Chuỗi contract→amendment→allocation→NT→request→invoice/cash; mô phỏng offline | R AI review logic; cần KD-OWNER + REVIEW-F/T + BASE-VER/ACCOUNTANT xác nhận hồ sơ thật | `proposed`; logic bình thường có điều kiện, business acceptance pending | `SIM-P1/B01-C…B01-I`, mục 7.1.2; không có hash hồ sơ thật | AI 28/10/2026, SIM-P1; công ty chưa review | KD-OWNER tập hợp bundle B01 thực tế khử dữ liệu; không lấy mô phỏng làm bằng chứng chạy ứng dụng |
| BIZ-002-B02 | Cùng chuỗi; return/rework/resubmit, mô phỏng offline | Cần KD-PREP/reviewer + REVIEW-F/T + ACCOUNTANT; người xác nhận chưa chỉ định | `proposed`; giữ S1/S2, chặn thiếu evidence và sai scope; chưa nghiệm thu thực tế | `SIM-P1/B02-C…B02-I`, mục 7.1.2; thiếu bản trả/sửa thật | AI 28/10/2026, SIM-P1 | KD-OWNER/reviewer cung cấp bản gửi, reason, bản sửa/biên nhận; Q3/Q4/Q6 liên quan còn thiếu |
| BIZ-002-B03 | Correction/void và mover/revoke; mô phỏng offline C1/P-A/P-B | Cần KD-OWNER/HR-HANDOVER/ACCESS-DEC/OPS + ACCOUNTANT; công ty chưa chỉ định | `proposed`; giữ lịch sử, không copy grant, action thiếu căn cứ bị chặn | `SIM-P1/B03-C/PL…B03-K`, mục 7.1.2; chưa có căn cứ Q8/HR thật | AI 28/10/2026, SIM-P1 | HR/owner quyền cung cấp case bàn giao/thu hồi; Q8 sửa sai sau chốt phải được xác nhận |
| CTR-002a gate | Chỉ thiết kế; test riêng dữ liệu giả là môi trường đích, chưa thực thi | R đề xuất development/QA; người dùng quyết định chuyển giai đoạn; owner công ty cho pilot còn thiếu | `proposed`; chuẩn bị P1 đủ để review/làm đầu vào phát triển test; `code_phase_unauthorized` | `CTR-002a-P1/T1–T6/T-P01/T-N01–09`, mục 7.1.3; source CTR-001 đối chiếu tĩnh | AI 28/10/2026, CTR-002a-P1 | Chờ yêu cầu chuyển giai đoạn; sau đó thực thi guard và tests, không BASE/legal/grant/payment/pilot |

Khi review một bundle, ghi tối thiểu: mã phiên bản từng chặng, actor/scope, trạng thái trước–sau, reference BASE (nếu có), lý do trả/sửa, kết quả đối chiếu và lỗi còn mở. Hồ sơ gốc và bằng chứng có dữ liệu nhạy cảm phải ở kho kiểm soát ngoài Git; dòng này chỉ lưu mã tham chiếu/hash.

### 7.1.1. Kết luận Q2-P1 và căn cứ của lượt review

Ma trận 11 hành động, R/A, scope, field/file, căn cứ và audit nằm duy nhất tại [KD mục 7.4 — Q2-P1](TP_KD_WORKFLOW_AND_PERMISSIONS.md#74-ma-trận-q2-p1--trách-nhiệm-và-quyền-cần-xác-nhận). Các mã vai trò chức năng ở đó được dùng trong walkthrough này. `REVIEW-C/F/T` lần lượt là review thương mại/tài chính/kỹ thuật; `FINANCE`/`ACCOUNTANT` chỉ là actor mô phỏng được chỉ định, chưa phải bổ nhiệm người thật.

Tham chiếu nội bộ `U-20261028-Q2-ANALYSIS`: phản hồi trong chat ngày 28/10/2026 cho nhóm Q2-A và Q2-B yêu cầu tiếp tục làm đúng nghiệp vụ, phân tích kỹ và đề xuất hướng phù hợp. Kết luận: **được tiếp tục phân tích**, chưa có xác nhận vai trò/cá nhân, phạm vi ủy quyền hoặc quy tắc cùng/khác người; không chuyển Q2 sang `accepted`, không tạo quyết định mới trong DECISIONS. Mã này nhận diện phản hồi trong chat; chưa có tệp bằng chứng/ủy quyền công ty và không giả hash. Q1 về ký/duyệt/hạn mức và các Q chưa có căn cứ tiếp tục mở.

Khuyến nghị Q2-P1 là capability theo công việc + company/project/department scope, cấp rõ và có thời hạn/căn cứ; mẫu vai trò chỉ hỗ trợ phân công. Owner nghiệp vụ được ủy quyền quyết định quyền, IT thực hiện theo quyết định; ghi riêng actor của hai trách nhiệm, chưa ép hai cá nhân khác nhau. Đây là lựa chọn phù hợp nền Odoo hiện có, giảm rò rỉ khi một người tham gia nhiều dự án, và truy được thay đổi khi điều chuyển. Quyền xem tiền, sửa, xuất và quản trị grant được xét riêng. Không mở engine quyền tổng quát hoặc quy tắc duyệt từ chức danh.

### 7.1.2. Inventory, hồ sơ còn cần và ba bundle mô phỏng (SIM-P1)

**Kết quả inventory ngày 28/10/2026:** trong tài liệu repository, `.local/biz-001`, `.local/biz-002` và tệp yêu cầu của lượt này, chưa có bundle thực tế khử dữ liệu đủ điều kiện sử dụng. Năm bản sao nguồn S01–S05 có hash khớp registry BIZ-001; S01/S02 là quy trình/phân công, S03–S05 là biểu mẫu/pattern, không có chuỗi bản ký–BASE–chứng từ đầy đủ. Không kiểm toàn bộ kho ngoài Git/NAS trong lượt này; kết luận chỉ là **chưa được cung cấp bundle đủ điều kiện**, không kết luận công ty không có hồ sơ. Không đọc thêm hàng kế toán thật, chạy macro hoặc truy external link.

| Hồ sơ cần, dùng mã khử dữ liệu | Đầu mối cần cung cấp/xác nhận | Điều kiện dùng và phần còn thiếu |
| --- | --- | --- |
| B01 thực tế: hợp đồng, phụ lục, căn cứ giao khoán, production/biên bản NT, đề nghị thanh toán | KD-OWNER + REVIEW-F/T | Liên kết đúng version/ID/phạm vi/bên; ngày, currency/basis; bản ký và điều kiện hiệu lực; hiện chưa có |
| B02 thực tế: bản gửi, ý kiến trả, bản sửa và biên nhận gửi lại | KD-PREP + reviewer được chỉ định | Có checklist/reason, version trước-sau và người nhận; không chỉ ảnh trạng thái; hiện chưa có |
| B03 thực tế: correction/void hoặc điều chuyển người phụ trách/quyền | KD-OWNER + HR-HANDOVER + ACCESS-DEC/OPS | Căn cứ sửa/thu hồi, thời điểm, biên nhận bàn giao, tác động downstream; hiện chưa có |
| BASE cho các bundle liên quan | BASE-REC/VER + chủ nguồn BASE | ID/link hoặc provenance thực, quyết định/actor/time, hash bộ trình và evidence; thẩm quyền Q1 riêng; hiện chưa có |
| Hóa đơn/thu chi nếu có căn cứ, điều khoản tạm ứng/giữ lại | ACCOUNTANT + REVIEW-F | Chứng từ/link/phân bổ, currency/basis/kỳ; không có thì ghi missing, không giả chứng từ để đi tiếp |

**Quy ước walkthrough:** các B01–B03 dưới đây là mô phỏng bàn giấy SIM-P1, chưa là hồ sơ thực tế, UAT hoặc test ứng dụng. Tiền theo triệu VND giả lập, cùng basis `excluding_tax` như mục 2; unit/quantity tách riêng. Mã `SIM-*` chỉ là nhãn đầu vào giả định, **không phải hash/bằng chứng đã nhận**. Mỗi chặng được xét riêng với điều kiện giả định có đầu vào hợp lệ; thiếu bằng chứng thật thì chặng thực tế vẫn bị chặn, không tự tạo căn cứ để nối bước. Toàn bộ action mới kể cả draft/submit/return/BASE/legal/grant đều chưa chạy runtime. E/H/I chỉ kiểm logic thiết kế. Kết quả `logic phù hợp` dưới đây chỉ nói quy tắc không mâu thuẫn trong giả định.

**B01 — đường bình thường** (mô phỏng, company C1/project P-A/phòng KD).

| Chặng và input/version | Actor → người nhận; scope | Trước → sau | Điều kiện và evidence cần có | Bị chặn khi | History/notification cần lưu | Kết quả đối chiếu / gap |
| --- | --- | --- | --- | --- | --- | --- |
| B01-C: `SIM-CTR1/R0/S1`, dòng 60+40 | KD-PREP → REVIEW-C/F/T; C1/P-A/KD | draft → in_review → review_complete (thiết kế đầy đủ C) | Phân công, checklist, currency/basis, hash bộ trình S1; BASE record/verify ở reference riêng | Thiếu source/authority; BASE approved nhưng unsigned vẫn not_effective | Actor/time, snapshot/hash, checklist và người nhận; notify chỉ nhãn/link | Logic phù hợp: 100 là tổng bản gốc; chưa có hồ sơ ký/BASE thực tế; review_complete ngoài CTR-002a |
| B01-PL: `SIM-CTR1/R1/S1`, thay 60→70, giữ 40; ngày hiệu lực giả định 01/11/2026 | KD-PREP → REVIEW-C/F/T → KD-OWNER; C1/P-A/KD | draft → review_complete; unsigned → signed_recorded và not_effective → effective_recorded chỉ khi đủ căn cứ riêng | previous_revision/line, hồ sơ phụ lục, BASE đúng hash khi áp dụng; chữ ký/authority/điều kiện/ngày hiệu lực | Approved nhưng chưa ký/thiếu điều kiện; effective date trùng | Giữ R0, R1, provenance và cảnh báo cho E/H/I; không sửa ngày ghi nhận thành ngày nghiệp vụ | As-of 31/10=100; 01/11=110 nếu đủ căn cứ; không 210. Hiệu lực thực tế chưa xác nhận |
| B01-E: `SIM-AL1/v1` cấp 1=70, con `AL2/3/v1`=30+35 | KD-OWNER → phòng nhận khoán → REVIEW-F; C1/P-A/phòng nhận | draft → in_review → ready_for_execution → executing | Revision nguồn hiệu lực/căn cứ cho thực hiện, cùng project/currency/basis, parent/level; hợp đồng thầu phụ riêng nếu áp dụng | Cha khác project/company, cycle; thiếu căn cứ thực hiện | Baseline khoán, handoff/ack, người nhận, audit links; notify H | Tổng project cấp 1=70; tổng con=65, còn 5; không 135. ALC chưa runtime, Q7 vẫn mở |
| B01-H: `SIM-PROD1/v1`=100, `SIM-ACC1/v1`=80 | Phòng thực hiện → REVIEW-T → KD-OWNER/REVIEW-F; C1/P-A/phạm vi NT | production submitted → confirmed; acceptance draft → reviewed → confirmed sau chữ ký/guard | Quantity/unit/kỳ và evidence chuyên môn; biên bản/bên/phạm vi/version, signatures/authority riêng | Thiếu biên bản/chữ ký, trùng phạm vi; không dùng production làm NT | Audit từng record, checklist, biên nhận chuyển Finance; notify đúng scope | Production 100, NT 80 là hai record; chênh 20 chưa là tiền thu; STL chưa runtime |
| B01-PR: `SIM-PAY1/v1` request=80, điều khoản giữ lại=8 | KD-PREP → REVIEW-F → BASE-REC/VER; C1/P-A/KD/QT-TC | draft → finance_review → ready_for_base → awaiting_base | Links ACC/terms, amount/currency/basis, hash request; BASE reference đúng bản | Thiếu NT hoặc điều khoản hợp lệ; evidence pending giữ pending | Request snapshot, Finance conclusion, declared/verified tách biệt; notify owner | Request pending không tạo cash; giữ lại chỉ theo terms giả định. Q3/Q4/Q8 thiếu căn cứ |
| B01-I: `SIM-INV1`=80, `SIM-CASH1`=72, retention=8 | ACCOUNTANT → REVIEW-F/KD-OWNER; C1/ledger/P-A | Observation → đối chiếu; posting/reconcile chỉ qua native Accounting khi có bridge | Chứng từ, period/currency/basis, payment links/allocations và terms | Chưa có feed/chứng từ: missing_source, không suy paid từ BASE | Chứng từ/link/reconcile, actor/time; notify quản lý bằng nhãn theo quyền | Trong giả định: NT−invoice=0, NT−cash=8; chưa là kết luận công nợ đến hạn. FIN chưa runtime |

**B02 — trả lại, sửa và gửi lại** (mô phỏng C1/P-A, giữ mọi bản gửi).

| Chặng và input/version | Actor → người nhận; scope | Trước → sau | Điều kiện và evidence cần có | Bị chặn khi | History/notification cần lưu | Kết quả đối chiếu / gap |
| --- | --- | --- | --- | --- | --- | --- |
| B02-C: `SIM-CTR2/R0/S1` thiếu phạm vi; ý kiến `RET-C1` | KD-PREP → REVIEW-C → KD-PREP; C1/P-A/KD | draft → in_review → returned | Checklist chỉ rõ dòng thiếu; return reason; S1 đóng băng | Reviewer không được giao hoặc reason rỗng; không sửa payload S1 | Return event, issue list/hash S1, actor/time; notify owner | Logic chặn đúng chỗ; chưa có bản bị trả thực tế |
| B02-C2: S2 bổ sung scope, liên kết S1 | KD-PREP → REVIEW-C/F/T; C1/P-A/KD | returned → draft với S2 mới → in_review; S1 giữ returned | Reason/fix mapping; current version, snapshot/hash mới; round review khác legal revision R0 | Stale S1, sửa trực tiếp S1; retry key khác payload | Previous submission link; submit mới/audit; notify reviewer một lần | Một hợp đồng original R0, hai vòng S1/S2; không tạo correction pháp lý cho lần sửa nháp |
| B02-PL: `SIM-CTR2/R1/S1→S2` thiếu scope/basis cần làm rõ | KD-PREP → REVIEW-F/C; C1/P-A/KD/QT-TC | in_review → returned; bản sửa draft → in_review | Tài liệu phụ lục/line mapping và basis được xác nhận; không lấy approval S1 cho S2 đổi giá | Basis unknown hoặc hash BASE sai: giữ pending; không hiệu lực | Bản trả, reason, hash/fix, thông báo E/H về dependency | Logic không dùng approval cũ; Q3/Q4 vẫn thiếu hồ sơ |
| B02-E: `SIM-AL2/v1` cố gắn cha P-B; bản sửa v2 cha P-A | KD-OWNER → phòng nhận/REVIEW-F; C1/P-A/phòng nhận | draft v1 không qua validation; v2 → in_review khi đúng scope | Parent ID cùng project/company, không cycle, nguồn revision/basis | Khác project/company dù trùng tên; thiếu căn cứ không ready | Validation outcome/audit theo policy; v1 và v2 có link; notify người sửa | Sai parent bị chặn theo thiết kế; không tuyên bố constraint ALC đã chạy |
| B02-H: `SIM-ACC2/v1` thiếu chữ ký, v2 bổ sung có căn cứ | Phòng thực hiện/REVIEW-T → KD-PREP/REVIEW-F; C1/P-A/phạm vi NT | draft → returned; bản mới draft → reviewed; confirmed chỉ sau guard chữ ký | Production/evidence, biên bản/bên/kỳ, return reason/previous link | Thiếu chữ ký vẫn reviewed/chưa confirmed; không bịa biên bản | Giữ bản trả, checklist/fix, signature evidence riêng; notify Finance | Logic tách review và chữ ký; chưa có NT nguồn |
| B02-PR: `SIM-PAY2/v1` thiếu NT/terms, bản mới v2 | KD-PREP → REVIEW-F → KD-PREP → BASE-REC; C1/P-A/KD/QT-TC | finance_review → returned; bản mới draft → finance_review → ready_for_base nếu đủ | Links ACC hợp lệ hoặc terms tạm ứng; fix list; v1 superseded, không góp tổng lần hai | Thiếu cả NT lẫn terms: tiếp tục returned | Return/resubmit reason, hash mỗi bản, notification; reference mới cho bản thay đổi | Logic không dùng request làm cash; chưa có hồ sơ để cho bước BASE thực tế |
| B02-I: chưa có chứng từ kế toán, cash chưa xác nhận; thêm event cash xác nhận 0 riêng | ACCOUNTANT → REVIEW-F; C1/ledger/P-A | missing_source giữ missing; event xác nhận 0 là record riêng | Chứng từ/confirmation xác định đúng event; không copy số request | Không có chứng từ không đặt cash=0 hoặc paid | Source missing và known_at, thông báo đầu mối bổ sung; không tạo move giả | null khác 0; thiếu feed Q6 vẫn chặn số chính thức |

**B03 — sửa sai và thay người/quyền** (mô phỏng, không mở action correction/void/grant thật).

| Chặng và input/version | Actor → người nhận; scope | Trước → sau | Điều kiện và evidence cần có | Bị chặn khi | History/notification cần lưu | Kết quả đối chiếu / gap |
| --- | --- | --- | --- | --- | --- | --- |
| B03-C/PL: lịch sử R0=100, R1=110; `SIM-CTR3/R2` sửa 70→50, giữ 40 | KD-PREP/owner được giao → REVIEW-C/F/T; C1/P-A/KD | R1 giữ lịch sử; R2 draft → review; chỉ ghi hiệu lực khi đủ căn cứ | Correction nhập sai hay phụ lục pháp lý phải phân loại; previous revision/line, reason, ngày/basis | Không căn cứ Q8/authority; không dùng review cancelled để xóa hiệu lực đã có | Impact case, as_of/known_at, hồ sơ trước/sau; notify E/H/I | Tổng mới giả định 90, không 200/310; bản 110 vẫn truy xuất; chưa cho correction thực tế |
| B03-E: mẹ 70→65, con 30+45=75 | KD-OWNER → phòng nhận/REVIEW-F; C1/P-A/phòng nhận | executing giữ; baseline v2 chỉ sau review/căn cứ | Links revision, tác động con/NT, reason và ngày áp dụng | Q7 chưa chốt hard-block hay cho qua; chỉ mô phỏng warning | Baseline cũ/mới, warning vượt 10 và notify H/I | Tổng cấp 1 mới=65, không 140; không tự sửa contract/cash/NT con |
| B03-H: `SIM-ACC3/v1` cần correction/void vì sai phạm vi | KD-OWNER/REVIEW-T/F → owner case; C1/P-A/phạm vi NT | confirmed → đề nghị void; chỉ void khi policy/căn cứ đủ | Biên bản sửa, links gốc/thay thế, affected request/invoice/payment, Q8 | Q8 hoặc chứng cứ thiếu: giữ case mở, không void thực tế | Lịch sử biên bản, impact/reason và notify Finance; không delete | Logic chặn action thiếu căn cứ; downstream chưa tự đảo |
| B03-PR: `SIM-PAY3/v1` đang awaiting_base dựa ACC3 | KD-PREP/REVIEW-F → BASE-REC/owner case; C1/P-A | Không auto approved/paid; mở xử lý request phụ thuộc | Reference đúng bản, đánh giá ACC3, căn cứ sửa/rút theo workflow H | BASE/evidence disputed chặn action phụ thuộc; không suy rejected từ disputed | Dependency warning, request history, notify owner và Finance | Request và BASE/cash riêng; quyết định sửa/rút còn Q3/Q8 |
| B03-I: `SIM-CASH3/v1`=72 sửa v2=70, đề nghị void đúng event | ACCOUNTANT → REVIEW-F/KD-OWNER; C1/ledger/P-A | Observation correction; nếu posted chỉ native reversal/credit/debit note phù hợp | Chứng từ và phân bổ gốc, reason, period và replacement/reversal links | Q4/Q6/Q8 thiếu; không xóa posted hoặc cộng bản cũ+mới | Actor/time, business_date/recorded_at, links gốc/thay; notify source owner | Contribution event=70 hoặc 0 sau void hợp lệ, không 142; mô phỏng không tạo tiền |
| B03-K: `SIM-HO3/v1`, người A chuyển P-A→P-B, người B nhận | Outgoing/incoming → HR-HANDOVER/KD-OWNER; C1/P-A và P-B xét riêng | Handover open → acknowledged nếu B nhận; grant P-A revoke riêng; P-B request/decision/provision mới | HR decision, inventory task/doc/grant, ack, scope/thời điểm, quyết định ACCESS-DEC → ACCESS-OPS | Chưa ack: handover unresolved; quyền cũ xử lý theo quyết định, không chờ giả ack; thiếu quyền mới không provision | Giữ actor lịch sử, HO/decision/revoke/provision links, audit; notify đúng scope | Không copy tiền/quyền P-A sang P-B; request sau revoke phải chặn. Ledger/handover chưa runtime |

**Kết luận SIM-P1:** ba bundle đủ ba đường logic bình thường/trả-sửa-gửi lại/correction và bàn giao. B01 cần các evidence giả định mới đi hết; B02 dừng đúng điểm thiếu; B03 nêu tác động và các action bị chặn. Không bundle nào đủ nghiệm thu bằng hồ sơ thực tế. Đầu mối KD-OWNER tập hợp B01/B02; HR-HANDOVER/ACCESS-DEC/OPS cho B03; BASE-REC/VER và ACCOUNTANT bổ sung chứng cứ theo Q3/Q6; từng người có thẩm quyền phải được công ty chỉ định.

### 7.1.3. Đặc tả chuẩn bị CTR-002a-P1 — test giả lập, chưa code

**Phạm vi:** tạo/sửa nháp → gửi rà soát → trả lại → mở vòng sửa mới → gửi lại trên môi trường test riêng. Ngoài slice: complete_review, cancel revision, record/verify BASE, chữ ký, hiệu lực, thanh toán, grant admin/người dùng thật, import và dữ liệu doanh nghiệp. Company/project/assignment nền tạo bằng fixture, không mở PRJ lifecycle mới. Review scope không có người nhận hợp lệ thì submit bị chặn.

**Đối chiếu tĩnh source 28/10/2026:** [revision](../../custom_addons/tp_contract/models/tp_contract_revision.py) có legal sequence/previous revision và enum review nhưng chưa có action/snapshot/version; [ACL](../../custom_addons/tp_contract/security/ir.access.csv) chỉ cho đọc; [controller](../../custom_addons/tp_planning_api/controllers/contracts.py) và [OpenAPI](../../contracts/openapi/tanphat-v1.yaml) chỉ có bốn GET; [grant](../../custom_addons/tp_project/models/tp_project_grant.py) chỉ financial_read, thiếu ledger revoke/export cap riêng. P1 là đề xuất mở rộng, không mô tả tính năng đang hoạt động.

**Quyết định thiết kế đề xuất về version:** `tp.contract.revision.sequence=0` là bản original duy nhất; amendment/correction là revision nghiệp vụ/pháp lý với previous revision. Không copy original thành original thứ hai hay dùng correction pháp lý cho mọi vòng bị trả. CTR-002a-P1 chọn **bản làm việc + snapshot gửi review bất biến** trong cùng revision chưa ký/chưa hiệu lực. Khái niệm mới `submission_id/sequence`, `previous_submission_id`, `aggregate_version`, `payload_hash`, `submitted_by/at`, `returned_by/at/reason/issues` là D, chưa có schema runtime. Snapshot bao gồm metadata/line/amount/basis và document hash theo field policy; không dựa vào JSON do frontend tự ký.

Khi submit S1, backend chụp và khóa snapshot/nội dung bản làm việc. Return chỉ thêm kết luận và chuyển `review_state` in_review→returned; snapshot payload S1 không đổi. Snapshot phải giữ metadata document bất biến **và tham chiếu tới binary/version được bảo toàn**; S2 tạo document version mới. Không chỉ lưu hash/ID trên attachment mutable: phải chặn replace/unlink bản S1 cả qua `tp.contract.document` và `ir.attachment`, hoặc lưu bản sao immutable ngoài record mutable với ACL tương đương. `begin_rework` giữ S1/return history, mở bản làm việc S2 từ S1, `review_state` returned→draft, tăng aggregate version và liên kết previous submission. Sửa S2 không sửa S1; resubmit tạo snapshot S2 mới. `review_state` của revision tiếp tục dùng enum KD 4.4; không thêm state engine hoặc đổi ý nghĩa sequence pháp lý. Mọi child mutation tăng aggregate version; `contract.write_date` hiện tại không phải token đủ bao phủ aggregate. Constraint/read-only guard mới phải được triển khai và test khi chuyển code, không mở ACL ghi đơn thuần.

| ID / action đề xuất | Trước → sau | Capability/actor fixture; scope | Guard/allowlist và output | Reason/evidence; history/receiver |
| --- | --- | --- | --- | --- |
| T1 `create_draft` | chưa có → draft | F-EDIT: contract.draft_edit; C1/P-A/KD | Code unique company, partner/type/project managed, currency; tạo original R0; current company/assignment từ backend. Amount chỉ với financial_read + financial.draft_edit | Nguồn giả lập/căn cứ giao việc; audit ID/version/actor/time; owner F-EDIT |
| T2 `edit_draft` | draft → draft | F-EDIT-META hoặc F-EDIT; C1/P-A/KD | Metadata/scope/terms/docs general đã phân loại; amount/basis/file financial cần capability riêng. Cấm state/BASE/legal/hash/audit/grant fields từ caller; không đổi company/project/parent để né scope | Current aggregate_version bắt buộc; tăng version cả child line/amount/file; audit redacted theo quyền |
| T3 `submit_review` | draft → in_review | F-EDIT: contract.submit + quyền đọc toàn bộ phần cần gửi; C1/P-A | Owner/reviewer được giao, checklist/scope/currency, mọi amount confirmed cho fixture đầy đủ; hash snapshot server, version hiện tại; unknown/null vẫn lưu được ở draft nhưng thiếu bắt buộc thì chưa submit | Submission S1/version/hash, selected reviewer, audit + outbox; notify F-REVIEW nhãn/link |
| T4 `return_review` | in_review → returned | F-REVIEW: contract.review_commercial; C1/P-A/checklist | Chỉ nhận xét/checklist/issue và reason; không sửa nội dung gốc. Reviewer cần financial_read nếu checklist chứa tiền; reviewer metadata không nhận payload tiền | S1/hash và version đã review; reason/issues; audit+outbox notify F-EDIT |
| T5 `begin_rework` | returned → draft với S2 làm việc | F-EDIT: contract.draft_edit; C1/P-A | Reference S1/return hợp lệ, reason và fix mapping; chỉ một vòng làm việc mở; bản cũ immutable, không legal revision mới | Previous submission link, aggregate version mới; audit rework/owner, chưa notify gửi lại |
| T6 `resubmit_review` | draft S2 → in_review | F-EDIT: contract.submit; C1/P-A | Guard T3 + previous/fix list; snapshot/hash S2, không ghi đè S1; không tái dùng approval BASE | Audit submission mới/outbox notify reviewer; retry không tạo S2/audit trùng |

**Actor fixture (tạo sau khi được mở code):** tất cả là mã giả, không suy từ chức danh. Scope gồm C1/P-A/KD, C1/P-B/phòng khác, C2/P-C; user có nhiều company phải vẫn bị giới hạn project/capability.

| Fixture | Assignment/grant/capability test | Có thể / phải bị chặn |
| --- | --- | --- |
| F-EDIT | C1/P-A; financial_read fixture + contract.draft_edit/submit + financial.draft_edit | T1–T3/T5–T6 trong P-A; không tự T4 hay grant/export |
| F-EDIT-META | C1/P-A; contract.draft_edit, không financial_read/financial.draft_edit | Sửa allowlist metadata draft; không tiền/file financial, không submit checklist có tiền |
| F-REVIEW | C1/P-A; reviewer assignment + contract.review_commercial, financial_read nếu cần | T4; không sửa payload/T1–T3 hay BASE |
| F-DUAL | C1/P-A; hợp cả capability F-EDIT và F-REVIEW theo policy fixture | Kiểm tách capability, không tự thêm guard bắt buộc actor khác nhau. Fixture này không quyết định policy cùng/khác người của công ty |
| F-READ/F-FINREAD | C1/P-A; chỉ metadata hoặc chỉ financial_read | Đọc đúng scope; không mutation, export capability hoặc grant.manage |
| F-OTHER-P/F-OTHER-C | C1/P-B hoặc C2/P-C; có capability cùng tên ở scope riêng | Không đọc/mutate/guess P-A, không link line/amount/document khác scope |
| F-OTHER-DP | C1/P-A nhưng department khác assignment; capability cùng tên ở phòng khác | Bị chặn riêng bởi Dp scope dù đúng company/project; không để test pass chỉ nhờ project denial |
| F-PLATFORM | Platform Manager quản trị nền nhưng thiếu capability hợp đồng/tiền | Không draft/review/financial hoặc grant nghiệp vụ mặc định |
| SUPERUSER-SETUP | Superuser tạo fixture/cleanup test | Không dùng để chứng minh positive/negative của actor; không cấp quyền thật |

**Hợp đồng kỹ thuật đề xuất, phải thực thi khi code:**

- Session Odoo lấy actor; CSRF token bắt buộc trên mọi action ghi theo route same-origin, kiểm Origin, không miễn CSRF vì body JSON. OpenAPI mới sẽ mô tả method/payload/response/error; hiện chỉ có GET, chưa có endpoint mutation. Request allowlist, 400 dữ liệu lỗi, 401 hết session, 403 thiếu capability trong scope, 404 ngoài company/project và không lộ record; 409 sai state/stale/idempotency conflict; `no-store`, tiền decimal string.
- `expected_version` bắt buộc ở T2–T6, T1 có key tạo mới. Aggregate version bao phủ contract/revision/line/amount/document; khóa/constraint đảm bảo một version thắng khi concurrent. Scope/capability/financial grant được kiểm lại trong transaction, không dùng trạng thái UI. Không dùng sudo thay quyền caller; ORM/RPC/create/write/unlink/nested x2many đều phải guard, cấm direct state write/đổi parent/sửa nội dung submitted.
- Idempotency key scoped theo actor + company/project + action + object (T1 dùng creation key), fingerprint canonical payload **gồm expected_version**; cùng key/payload trả kết quả cũ sau recheck quyền hiện tại, không transition/audit/outbox lần hai. Cùng key khác payload trả 409. Replay được nhận diện trước stale check của mutation mới; nếu không, retry thành công cũ sẽ bị coi stale sai. Sau revoke không trả lại payload tài chính đã cache. Unique key/locking ngăn hai retry concurrent tạo hai bản; hết hạn lưu key là policy kỹ thuật phải nêu khi code, chưa tự đặt retention công ty.
- Dữ liệu/state/version/snapshot/audit/idempotency và outbox cùng transaction; audit/outbox write fail thì rollback toàn bộ. **Delivery notification sau commit lỗi thì retry outbox**, không rollback hồ sơ đã commit, không transition lại. Event/delivery ID phải ổn định; receiver có inbox/unique dedupe theo `(event_id, recipient)` khi kiểm soát được. Với kênh không hỗ trợ dedupe, ghi rõ at-least-once và không hứa exactly-once. Audit append-only có actor/time/model/id/scope/state trước–sau/version/hash/reason/request ID; financial payload/audit/outbox theo field/file policy. Chatter không thay audit.
- Snapshot, idempotency payload và audit chi tiết có thể chứa amount nhưng **không được đặt JSON tiền trên record metadata mà metadata reader có thể đọc qua ORM/RPC/export**. Tách record/field tài chính với ACL/domain tương đương các model amount của CTR-001; response/cache/audit chỉ trả amount theo grant hiện tại, decimal string và policy. Kiểm cả create/write/unlink/read/search/read_group/export/RPC của model snapshot/document mới, không chỉ redaction API.

| Ca dự kiến | Kết quả phải kiểm khi triển khai |
| --- | --- |
| T-P01 normal T1→T2→T3→T4→T5→T2→T6 bằng actor thường | R0 original giữ một bản pháp lý; S1 returned immutable; S2 in_review có hash/fix; đúng audit/outbox/receiver, không BASE/legal/cash |
| T-N01 capability/read-only/Platform, wrong P/company/department, assignment hết hiệu lực | 403/404 phù hợp, không side effect hoặc leak; title/admin nền không bypass |
| T-N02 tiền: metadata edit, financial reader-only, hết hạn/revoke, file link/export | Reader không sửa tiền; metadata không nhận amount/file/audit tiền; export không tự mở; replay sau revoke recheck quyền |
| T-N03 sai state/return thiếu reason/unknown currency/null thiếu bắt buộc | 400/409; draft null khác 0; không ép unknown thành zero; không return draft hoặc edit in_review |
| T-N04 ORM/RPC direct state, nested child, company/parent injection, sửa/xóa S1 và binary attachment S1 | Bị chặn cả ngoài API; không thay nội dung/hash lịch sử, xóa/thay binary đã gửi, hay chèn approval/authority |
| T-N05 stale T2/T3/T4/T5/T6, hai submit/rework concurrent, child đổi sau đọc | 409 cho request thua; không mất update, không hai snapshot/vòng làm việc; aggregate version bao phủ child |
| T-N06 retry T1/T3/T4/T5/T6 sau timeout, cùng key khác payload, concurrent retry | Cùng key/payload không bản/audit/outbox trùng; khác payload 409; T1 chỉ tạo một contract; retry thành công trước đó không bị stale giả |
| T-N07 CSRF thiếu/sai, cross-origin, session hết hạn | Bị chặn trước mutation; read-only GET vẫn đúng contract; không phản chiếu credential/token |
| T-N08 fail audit/idempotency/outbox write; crash sau send trước ack; fail notification delivery | Write failure rollback state/version/snapshot; delivery failure giữ commit và retry event ổn định; receiver dedupe `(event_id, recipient)` hoặc nêu at-least-once; không tạo state/audit trùng |
| T-N09 unknown field, BASE/legal/grant/cancel/payment injection | Allowlist reject; không mở action ngoài slice; negative test response/file/audit không có tiền sai scope |

**Tiêu chí hoàn tất khi được triển khai:** model/security guard và snapshot/version/idempotency/audit/outbox chạy bằng fixture; Odoo action/ACL/negative/concurrent/retry tests đạt; API/OpenAPI/type generation và UI draft-review-return có loading/error/conflict đúng; frontend typecheck/build và test liên quan đạt; kiểm regression CTR-001 và field/file policy; handoff/checker cập nhật, không quyền/dữ liệu thật. Không viết test ứng dụng trong lượt tài liệu này.

| Cổng | Đánh giá ngày 28/10/2026 / điều kiện còn lại |
| --- | --- |
| Chuẩn bị thiết kế | Đã có CTR-002a-P1 đủ phạm vi, actor, guard, version/retry/audit và ca kiểm để review/chọn triển khai test. Tất cả là đề xuất, chưa test runtime |
| Phát triển thử trên test | Có thể dùng đề xuất P1 làm đầu vào **sau yêu cầu chuyển giai đoạn rõ của người dùng**; lượt này chưa được phép code. Không đòi đóng Q1–Q14 hay bổ nhiệm quyền thật để dùng fixture |
| Người dùng thật/pilot | Chưa đạt: Q2 bổ nhiệm/scope/căn cứ, bundle thực tế và owner nghiệm thu, field/free-text redaction, export capability và grant/revoke ledger/audit liên quan chưa đủ. Chỉ những cổng Q của action pilot được chọn mới bắt buộc |
| Production | Chưa đạt: nghiệm thu pilot, bảo mật/HTTPS, migration/staging, backup ngoài máy/restore/retention và Q14; dev/test không đủ để kết luận production |

### 7.2. Phân biệt kiểm tra kỹ thuật, nghiệm thu nghiệp vụ và quyền mở code

Kết quả kỹ thuật dưới đây thuộc lượt kiểm tra `CHG-20261028-011` ngày 28/10/2026; không phải kết luận nghiệm thu của công ty.

| Lớp | Kết quả hiện tại | Ý nghĩa |
| --- | --- | --- |
| Kiểm tra kỹ thuật nền/CTR-001 | Đã chạy đạt: 53 Odoo tests, 14 frontend tests, frontend typecheck và Ruff; runtime đã dừng sau kiểm tra | Xác nhận read slice và mã hiện tại không có lỗi được phát hiện trong phạm vi test; không xác nhận quy trình công ty |
| Nghiệm thu BIZ-002/Q2 và bundles | `business_acceptance_pending`; nhật ký 7.1 ghi đề xuất Q2-P1/SIM-P1/CTR-002a-P1, chưa dòng nào accepted | Cần người có thẩm quyền review, bằng chứng khử dữ liệu và kết luận từng gap |
| Quyết định chuyển sang code | `code_phase_unauthorized` trong tài liệu này | Người dùng phải chọn mở CTR-002a; fixture test không tự tạo quyền grant, phê duyệt BASE, ký, hiệu lực hoặc thanh toán |

## 8. Thứ tự chuyển giai đoạn đề xuất

1. **Ưu tiên Q2 cho phạm vi gần nhất:** chốt người lập, soát, ghi nhận/xác minh kết quả BASE và người cấp/thu hồi grant; không cần đóng cả Q1–Q14 cùng lúc. Các Q khác vẫn được xử lý tại cổng của slice tương ứng.
2. SIM-P1 ở 7.1.2 đã chuẩn bị ba bundle mô phỏng trong khi chờ Q2/hồ sơ. Khi có đầu mối và bằng chứng, đối chiếu 2–3 bundle thực tế khử dữ liệu theo chuỗi hợp đồng → phụ lục → giao khoán → nghiệm thu → thanh toán, có ít nhất một đường trả lại và một correction/void hoặc bàn giao. Với phần chưa có runtime, chỉ review logic và gap, không tuyên bố ứng dụng đã chạy.
3. Điền nhật ký mục 7.1 cho Q2 và từng bundle; giữ hạn mức ký/duyệt, bốn mắt và căn cứ pháp lý ở `open`/`deferred` nếu chưa có văn bản. Sau đó người dùng quyết định có chuyển giai đoạn code hay chưa.
4. Chỉ khi có quyết định chuyển giai đoạn mới mở CTR-002a draft/submit/return trên test với dữ liệu giả và actor fixture. Q2 vẫn phải được xác nhận trước grant người dùng thật hoặc pilot; fixture không thay cho quyết định quyền công ty.
5. PRJ-002/ALC-001 hoặc Survey/Design theo nhu cầu, mỗi slice có owner nghiệm thu; không mở đồng loạt chín phân hệ.
6. STL-001 và accounting bridge sau khi Q4/Q6/Q8 có căn cứ; import sau mapping/reconcile/cutover; dashboard sau Q13. Pilot/production chỉ sau Q14, backup/restore ngoài máy, security/attachment, migration và nghiệm thu dữ liệu. Dev/test không là production.

