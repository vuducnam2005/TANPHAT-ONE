# BIZ-002 — Workflow A–E: Kế hoạch Kinh doanh và bàn giao

**Ngày:** 28/10/2026. **Trạng thái:** D — đề xuất để nghiệm thu; không triển khai action. Đọc [bộ thiết kế](TP_BIZ002_DESIGN_PACKAGE.md), [bản đồ/RACI](TP_ENTERPRISE_PROCESS_MAP.md), [dữ liệu/quyền](TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md) và [nguồn BIZ-001](TP_KD_EVIDENCE_AND_ACCEPTANCE.md).

## 0. Hợp đồng chung cho mọi transition

Mỗi dòng bảng là command backend dự kiến, không phải lệnh PATCH state. `C/P/Dp` lần lượt là company đang được phép, project được phân công và department được giao. Khi có nhiều chiều, phải thỏa giao phạm vi áp dụng; cùng phòng/cùng company không tự cấp quyền mọi project. Trước khi có project, A dùng opportunity/package scope gắn company + phòng phụ trách; không cấp scope bằng tên.

Tất cả action cần actor từ session, capability đúng domain, state/version trước, liên kết cùng company/project, field/evidence hợp lệ; transaction nguyên tử; version conflict không ghi một phần. Retry cùng key/payload trả cùng kết quả; key khác payload bị từ chối. Audit actor/time/trước-sau/reason/evidence hash/request ID/version; nội dung tiền chỉ vào audit có quyền tiền. Thông báo gửi owner/người nhận được phân công, chỉ nhãn/ID/link đã kiểm quyền; không chép tiền/file đính kèm vào thông báo. Đây là D cần kiểm bằng tests khi code, chưa phải runtime hiện có.

Lý do bắt buộc cho return/reject/withdraw/cancel/hold/reopen/correction/delegation; approve/review phải lưu kết luận/checklist và căn cứ. Deadline do hồ sơ/hợp đồng/kế hoạch đã chấp thuận cung cấp; chưa có SLA thì không tự đặt số ngày. Khi quá hạn, tạo cờ cảnh báo, không tự đổi trạng thái thành rejected hoặc completed. Owner nghỉ việc dùng quy trình K và action handover có biên nhận; không đổi tác giả lịch sử, không tự chuyển quyền tiền.

Mỗi hồ sơ có các chiều riêng: review nội bộ; decision/evidence BASE nếu áp dụng; bản ký và thẩm quyền; hiệu lực/phạm vi thực hiện; revision. Người duyệt BASE/người ký không đồng nhất với R/A trong RACI. Không hợp thức hóa dữ liệu thiếu, hồ sơ trùng hoặc hồi tố bằng việc bỏ guard. Các ca thiết kế xuyên suốt ở [nghiệm thu](TP_BIZ002_ACCEPTANCE_AND_READINESS.md).

## A. Cơ hội, quyết định tham gia, đấu thầu và kết quả

**Căn cứ:** O/E02–E04 (S01, trách nhiệm KD); chi tiết state/action dưới đây là D. **Mục đích/phạm vi:** theo dõi từ phát hiện nhu cầu hoặc nhận mời thầu/giao trực tiếp đến kết quả có chứng cứ; không quản trị thay cổng đấu thầu. **Bắt đầu:** có nguồn tin/hồ sơ mời. **Kết thúc:** won/lost/withdrawn/cancelled được ghi nhận; won bàn giao B/C. Review hoàn tất không có nghĩa được phép tham gia.

**RACI:** KD phụ trách R chuẩn bị; Trưởng ban KD A chịu trách nhiệm chất lượng/điều phối; chuyên môn, QT-TC C; lãnh đạo/người được giao I hoặc quyết định trên BASE theo văn bản (Q1). Đối tác không có quyền session nội bộ mặc định. **Đầu vào bắt buộc khi gửi:** mã gói/cơ hội nội bộ, company, đầu mối, nguồn/mời thầu, phạm vi, thời hạn theo hồ sơ, checklist năng lực/rủi ro, đề xuất tham gia, người nhận rà soát. Thông tin giá/bảo lãnh là financial. **Đầu ra:** bộ hồ sơ nộp theo version/hash, chứng cứ nộp, kết quả; handoff gồm phạm vi và điều kiện thương thảo còn mở, không chỉ link cơ hội.

| Từ → đến | Action; actor/capability; scope | Guard/field/evidence và nơi quyết định | Hậu điều kiện; audit/thông báo |
| --- | --- | --- | --- |
| Mới → identified | create_opportunity; KD/opportunity.prepare; C/Dp | Nguồn, owner, loại thầu/giao trực tiếp; kiểm trùng mã bên mời + gói, không gộp theo tên | ID/mã nội bộ; notify owner |
| identified → assessing | start_assessment; KD/opportunity.assess; C/Dp | Checklist phạm vi, năng lực, thời hạn; giá chưa biết giữ unknown | Version đánh giá; notify chuyên môn/QT-TC theo phần được giao |
| assessing → assessment_returned hoặc assessment_ready | return/complete_assessment; reviewer/opportunity.review; C/Dp | Kết luận theo chuyên môn/thương mại/tài chính, reason mục thiếu khi trả; chưa quyết định tham gia | Checklist bất biến ở bản review; notify KD |
| assessment_returned → assessing | resubmit_assessment; KD/opportunity.prepare; C/Dp | Version mới, danh sách xử lý ý kiến | Giữ bản đã trả; notify reviewer |
| assessment_ready → bid_preparation hoặc closed_no_bid | register_participation_result; designated/base_result.record; C/Dp | BASE tham chiếu đúng version + decision, evidence và authority theo Q1–Q3 khi quyết định yêu cầu; xác minh tách khai báo | Chỉ được coi đủ căn cứ thực hiện khi verified/authority phù hợp; lý do no-bid; notify owner |
| bid_preparation → ready_to_submit | complete_bid_check; reviewer/bid.review; C/Dp | Đủ bộ hồ sơ/checklist, phiên bản nộp, người nộp; bảo lãnh/giá phải đúng quyền và thẩm quyền | Khóa bộ nộp; review không thay chữ ký; notify người nộp |
| ready_to_submit → submitted | record_submission; designated/bid.submission_record; C/Dp | Chứng cứ nộp, thời điểm, nơi nộp, version/hash; chữ ký/thẩm quyền theo hồ sơ, chưa đủ giữ pending evidence | Receipt bất biến; notify KD; quá hạn cảnh báo không sửa receipt |
| submitted → won/lost | record_award; KD/bid.result_record; C/Dp | Văn bản kết quả, ngày, bên phát hành; kết quả chưa kiểm chứng chỉ declared, không đủ kích hoạt contract | Lưu kết quả + trạng thái xác minh; won phát gói bàn giao B/C, lost giữ lý do |
| identified/assessing/bid_preparation/ready_to_submit/submitted → withdrawn/cancelled | record_withdrawal/cancellation; designated/bid.close; C/Dp | Lý do, quyền/căn cứ rút hoặc văn bản hủy của bên mời; chứng cứ ảnh hưởng bảo lãnh | Không xóa hồ sơ nộp; notify KD/QT-TC và xử lý bảo lãnh riêng |
| won/lost/withdrawn/cancelled → correction mới | correct_result; designated/bid.result_correct; C/Dp | Chứng cứ đính chính, reason, tác động bàn giao; không đổi lịch sử cũ | Kết quả thay thế có ngày nghiệp vụ/ghi nhận; B/C nhận cảnh báo xử lý |

**Ngoại lệ/nghiệm thu:** giao trực tiếp có căn cứ giao việc thì đi nhánh đánh giá → thương thảo B/C, không tạo chứng cứ nộp thầu giả. Hồ sơ thiếu hạn nộp không gửi check, không bịa ngày. Cơ hội trùng giữ candidate liên kết để owner quyết định merge có audit; khác gói không gộp. Nguồn công bố bị đính chính phải giữ cả hai bản; reopen một gói đã hủy cần văn bản mới, thường tạo đợt/gói mới liên kết. A-N: bộ giả lập đủ căn cứ đi identified → won và B nhận handoff. A-X: BASE chỉ có ảnh chưa verified hoặc sai hash thì không đủ căn cứ tham gia/kích hoạt dù nội bộ đã review.

**Q:** chủ nghiệp vụ KD xác nhận catalog loại thầu/giao trực tiếp, checklist ký/nộp/bảo lãnh và mức quyết định cần BASE; pháp lý/lãnh đạo xác nhận Q1, vận hành BASE xác nhận Q3. Chưa cho auto-routing hoặc SLA.

## B. Khởi tạo, phân công, kế hoạch và vòng đời dự án

**Căn cứ:** U phân quyền theo scope; O/E01–E04; R `project.project` metadata/assignment chỉ đọc đã có. State sau đây là D, khác `active` chuẩn dùng archive. **Mục đích:** một hồ sơ project dùng chung phòng, tách dự án dự thầu/chuẩn bị với dự án thực hiện. **Bắt đầu:** bàn giao A hoặc quyết định mở dự án độc lập. **Kết thúc:** completed/cancelled kèm hồ sơ lưu và nghĩa vụ còn tồn; hold chưa kết thúc.

**RACI:** KD/project owner R; Trưởng ban/phụ trách dự án được chỉ định A về điều phối; trưởng phòng nhận việc, QT-TC, chuyên môn C; người thực hiện I. Người được quyền mở/đóng dự án còn Q1/Q2. **Đầu vào:** company/mã duy nhất, tên, loại/giai đoạn, nguồn mở, phòng chủ trì, owner, phạm vi, mốc, kế hoạch version, danh sách phân công; hợp đồng có thể chưa tồn tại khi dự thầu. **Đầu ra bàn giao:** project ID + baseline kế hoạch/phạm vi + assignments, các điểm chưa xác nhận, hồ sơ nguồn và người nhận có xác nhận; không tự cấp quyền tiền từ task/owner label.

| Từ → đến | Action; capability; scope | Guard/evidence, nơi quyết định | Kết quả/audit/thông báo |
| --- | --- | --- | --- |
| Mới → draft | create_project; project.prepare; C/Dp | Code unique C, nguồn mở, phòng/owner; duplicate check | Hồ sơ draft, không mặc định active thực hiện; notify owner |
| draft → review | submit_project_plan; project.submit; C/P/Dp | Phạm vi, kế hoạch/mốc/đơn vị, owner còn làm việc; version/checklist | Baseline gửi bất biến; notify reviewers |
| review → draft hoặc active | return/activate_project; project.review/lifecycle_manage; C/P/Dp | Return cần reason/version mới; activate cần kết luận và căn cứ cho phép giai đoạn tương ứng, BASE nếu quy trình yêu cầu | Chốt baseline; notify các phòng; không tạo ký/hiệu lực contract |
| active → on_hold | hold_project; project.lifecycle_manage; C/P/Dp | Lý do, ngày, quyết định nguồn, danh sách task/chi phí/phạm vi vẫn được phép | Lưu hold scope; chặn action mới ngoài ngoại lệ đã cho; notify các owner |
| on_hold → active | resume_project; project.lifecycle_manage; C/P/Dp | Căn cứ tiếp tục, kế hoạch/mốc cập nhật, rà soát hồ sơ/thẩm quyền | Kế hoạch mới có version; notify phòng nhận |
| active/on_hold → completed | complete_project; project.lifecycle_manage; C/P/Dp | Checklist đầu ra/bàn giao, mọi việc tồn có owner/hạn/căn cứ; QT-TC đối chiếu nghĩa vụ còn tồn, không buộc cash=0 giả | Ghi hoàn thành thực hiện và register nghĩa vụ; không tự thanh lý/đóng sổ; notify KD/Finance/Docs |
| draft/review/active/on_hold → cancelled | cancel_project; project.lifecycle_manage; C/P/Dp | Lý do/căn cứ, ảnh hưởng hợp đồng/task/chi phí/công nợ; hủy dự án không hủy chứng từ con hàng loạt | Giữ hồ sơ/audit, tạo việc xử lý tác động riêng |
| completed/cancelled → review mở lại | reopen_project; project.reopen; C/P/Dp | Lý do, người có thẩm quyền, checklist tác động và kế hoạch mới; không phục hồi grant cũ tự động | Bản mở lại và căn cứ riêng; notify owner/các phòng |
| Không đổi state → handover/plan_revision | handover_project/revise_plan; project.scope_manage/work_plan.prepare; C/P/Dp | Owner cũ/mới, ngày, việc tồn, biên nhận; grant có quy trình riêng K; plan revision cần thay đổi/ảnh hưởng | Lịch sử phân công/kế hoạch; notify người nhận, rà soát quyền |

**Ngoại lệ/nghiệm thu:** thiếu owner hoặc project trùng company/code phải bị chặn; tên giống chỉ cảnh báo. Phòng khác cần access theo assignment được cấp; giao phòng không cấp toàn bộ company. Hold phải định nghĩa phần bảo quản hồ sơ/nhận tiền được tiếp tục, không đóng băng dữ liệu kế toán thật. B-N: mở dự án dự thầu không hợp đồng rồi chuyển thực hiện bằng căn cứ mới. B-X: người nghỉ không có người nhận hoặc caller ngoài project không được activate/handover; version cũ trả conflict, không mất kế hoạch mới. Hồi tố kế hoạch giữ ngày hiệu lực lẫn ngày ghi; không sửa baseline từng dùng nghiệm thu.

**Q:** KD/lãnh đạo chốt điều kiện mở/hold/complete/reopen và nghĩa vụ có thể còn sau complete; các phòng chốt baseline/mốc và người nhận handoff (Q9 trong readiness).

## C. Hợp đồng chính/thầu phụ, phụ lục, chữ ký, hiệu lực và thanh lý

**Căn cứ:** U BASE chính thức; O/E04–E08/E10; R CTR-001 có model/read/constraint, chưa có action. Bảng field/enum chủ nằm ở [KD mục 4.4](TP_KD_WORKFLOW_AND_PERMISSIONS.md), không thay enum bằng các từ nghiệp vụ trong bảng này. Cũng dùng các guard KD 4.1–4.3/5/8. **Mục đích:** quản trị danh tính + version hồ sơ có phạm vi/giá trị/bằng chứng tách khỏi quyết định. **Bắt đầu:** có yêu cầu thương thảo/hợp đồng thầu phụ thuộc project. **Kết thúc:** liquidated/terminated kèm nghĩa vụ còn lại và hồ sơ; revision cũ giữ nguyên.

**RACI:** project owner KD R hồ sơ; Trưởng ban A chất lượng thương mại/điều phối; QT-TC C tài chính, chuyên môn C phạm vi; người record/verify BASE, ghi bản ký và xác nhận hiệu lực được chỉ định riêng Q1–Q3. Người ký dựa văn bản, không suy từ RACI. **Đầu vào:** company/project, đối tác, code/type/currency, phạm vi/scope_key, bản gốc/phụ lục, basis/amount_state, điều khoản/ngày, review checklist và tài liệu phân loại. **Đầu ra:** version/hash, phạm vi áp dụng theo ngày, BASE declared/verified, bản ký/thẩm quyền/hiệu lực tách nhau; bàn giao E/H/I có currency/basis và các điều kiện còn mở.

| Chuyển/action | Actor/capability; scope | Guard và hậu điều kiện bổ sung | Lịch sử/thông báo |
| --- | --- | --- | --- |
| Tạo/sửa draft → submit → return/complete_review | KD contract.draft_edit/submit, reviewer commercial/technical/finance tương ứng; C/P/Dp áp dụng | Theo KD 4.1; gửi đóng băng version/hash; tiền cần financial.read + draft_edit. Return không sửa đè bản gửi, tạo version sửa có liên kết | Checklist/ý kiến người review; notify owner/reviewer |
| draft/in_review/returned/review_complete → review_state cancelled (D bổ sung) | contract.revision_cancel được chỉ định; C/P | Chỉ bản chưa signed_recorded/effective_recorded; reason và tác động BASE reference, hồ sơ đã gửi phải có căn cứ rút. Chưa chốt ai có quyền nên chưa được mở command | Giữ version, thông báo người review/record BASE; không đổi decision BASE tự động |
| review_complete → đăng ký gửi/ghi kết quả BASE → verify/dispute | base_reference.record/base_result.record/base_result.verify; C/P | Theo KD 4.1–4.2; reference đúng version/hash/mục đích/tiền; evidence pending khác verified; quyền tiền áp dụng cả tệp. Tách người lập/soát là đề xuất Q2, chưa quy chế | Actor trên BASE khác actor nhập; người verify cần nguồn; notify owner khi rejected/disputed/revoked |
| Ghi bản ký | legal_evidence.record; C/P | signed_recorded cần ngày/bản ký/bên ký; authority pending/confirmed riêng, không tự tạo thẩm quyền | Bản ký bất biến, notify owner; hợp đồng chưa hiệu lực vẫn không tính vào snapshot |
| Xác nhận ghi nhận hiệu lực | contract.effectivity_confirm; C/P | Căn cứ chữ ký/authority/điều kiện/ngày hiệu lực và BASE khi áp dụng; đề xuất transaction cập nhật revision.effectivity_status + contract.lifecycle_state, kiểm conflict/overlap. Chưa mở khi Q1–Q4/Q8 chưa đủ | Snapshot chọn đúng bản theo ngày, không cộng phụ lục; audit trước/sau và căn cứ |
| Amend/correct | revision.propose; C/P | Bản trước + tài liệu/phạm vi thay; phụ lục pháp lý khác lỗi nhập. Dựng snapshot đầy đủ có previous_line; approved cũ không cho đổi giá/phạm vi mới | Giữ baseline cũ; version mới theo lại review/BASE/ký/hiệu lực áp dụng; notify E/H/I về thay đổi |
| Suspend/resume/complete_execution/liquidate/terminate | contract.lifecycle_manage; C/P | Theo KD 4.3; căn cứ/thời điểm/lý do; liquidate cần đối chiếu nghĩa vụ/giữ lại và hồ sơ, không tự đặt hết nợ | Không đổi dòng tiền/posted; notify project/Finance/Docs; action tác động chứng từ riêng |
| Correction/revocation sau hiệu lực hoặc thanh lý | revision.confirm/record.void theo domain, người có thẩm quyền chỉ định; C/P | Q8: giữ hồ sơ cũ, ngày nghiệp vụ và ngày biết; phân tích affected reports/payment; không dùng cancelled review để xóa hiệu lực pháp lý đã ghi | Mở case xử lý, khóa action phụ thuộc evidence disputed; kế toán dùng reversal riêng |

**Ngoại lệ/nghiệm thu:** hợp đồng thầu phụ là danh tính riêng liên kết E; không tạo thêm nghĩa vụ hai lần. Thiếu basis/currency/ngày/ủy quyền giữ unknown/pending/legacy_unverified và chặn action liên quan; đọc metadata có nhãn được phép. Hai bản trùng ngày hiệu lực không tự chọn ID lớn nhất. C-N: bản giả 60+40=100, phụ lục đổi 60→70 thành 110 tại ngày hiệu lực; BASE approved nhưng chưa ký vẫn không effective. C-X: hủy draft phụ lục giữ nguyên bản gốc; caller thiếu grant không đọc/ghi tiền hoặc file tài chính kể cả native/export; không sửa amount/hash sau submit. Chưa có runtime action cancel/verify/effectivity trong lượt này.

**Q:** giữ Q1–Q4/Q8. Chủ nghiệp vụ phải xác nhận quyền hủy bản gửi, cách xác nhận hiệu lực đồng thời hai field và correction/void sau chốt; không dùng D bổ sung này để tuyên bố đã đóng Q.

**Chuẩn bị CTR-002a-P1:** [readiness mục 7.1.3](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#713-đặc-tả-chuẩn-bị-ctr-002a-p1--đã-code-trên-test) chi tiết create/edit draft, submit/return/rework/resubmit bằng fixture, CSRF/version/idempotency/audit và ca kiểm. Đề xuất giữ snapshot mỗi vòng gửi review bất biến trong cùng revision chưa ký/hiệu lực; vòng sửa do bị trả không tự tạo amendment/correction pháp lý. Còn Q2 theo [KD 7.4](TP_KD_WORKFLOW_AND_PERMISSIONS.md#74-ma-trận-q2-p1--trách-nhiệm-và-quyền-cần-xác-nhận). CHG-20261028-014 đã triển khai các action này trên database test với actor fixture (DEC-020); chưa mở pilot hoặc người dùng thật.

## D. Kế hoạch công việc, giao/nhận, phối hợp và nghiệm thu kết quả

**Căn cứ:** O/E01 một owner/task và BASE điều phối; phần còn lại D. **Mục đích:** quản lý trách nhiệm/đầu ra, khác nghiệm thu có giá trị tiền H. **Bắt đầu:** nhiệm vụ từ kế hoạch/hợp đồng/yêu cầu xử lý. **Kết thúc:** completed/cancelled với kết quả/biên nhận; quá hạn là cờ, không state độc lập.

**RACI:** người giao/chủ kế hoạch A về đầu ra; owner nhận việc R duy nhất; người phối hợp C theo phần việc, người nhận handoff I và xác nhận theo phân công. KCS/chuyên môn có quyền riêng khi đầu ra yêu cầu. **Input:** project/phạm vi, một owner, mô tả đầu ra, người nhận nghiệm thu, deadline có căn cứ hoặc nhãn chưa chốt, phụ thuộc và tài liệu được cấp. **Output:** kết quả/version, checklist, biên nhận, issue còn tồn; chuyển F/G/H theo loại, không tự tạo acceptance tiền.

| Từ → đến | Action; capability/actor; scope | Guard/đầu ra | Audit/thông báo |
| --- | --- | --- | --- |
| Mới → draft → assigned | prepare/assign_task; work_plan.prepare/task.assign; C/P/Dp | Owner đang làm việc, phạm vi/đầu ra/người nhận và hạn hoặc explicit chưa chốt; link BASE nếu nhiệm vụ thuộc luồng chính thức | Bản giao; notify owner/phối hợp, không grant financial |
| assigned → in_progress hoặc returned_to_assigner | accept_task/return_assignment; task.accept; C/P + own task | Xác nhận nhận hoặc lý do thiếu nguồn lực/phạm vi; trả không thành reject tài chính | Receipt/time; notify người giao |
| returned_to_assigner → assigned | reassign/rescope_task; task.assign; C/P/Dp | Owner/phạm vi/hạn mới có version; giữ người giao cũ/ý kiến | Notify owner mới và cũ |
| in_progress → result_submitted | submit_result; task.result_submit; C/P + own task | Đầu ra/version, checklist, tài liệu được phân loại, liệt kê issue; đồng thời update conflict bị chặn | Đóng băng bản gửi; notify người nhận/reviewer |
| result_submitted → returned hoặc completed | return_result/accept_result; task.result_review; C/P + nhận đúng task | Return có reason/mục thiếu; completed có checklist và biên nhận; KCS/bên ngoài khi yêu cầu vẫn là record riêng | Kết quả nghiệm thu công việc, không tạo tiền; notify owner/người giao |
| returned → in_progress → result_submitted | revise_result; task.result_submit; C/P + own task | Version mới giải trình từng ý kiến, không sửa đè bản bị trả | Giữ chuỗi result; notify reviewer khi gửi lại |
| draft/assigned/in_progress/returned → cancelled | cancel_task; task.cancel; C/P/Dp | Reason/căn cứ, rà soát phụ thuộc/việc đã làm; bản đã nghiệm thu không xóa bằng cancel | Notify owner/người nhận; kết quả cũ còn truy xuất |
| completed → in_progress (bản mở lại) | reopen_task; task.reopen; C/P/Dp | Lý do/issue, người giao có quyền, tác động hồ sơ đã phát hành; không rút phiên bản G/H đã ký tự động | Lịch sử reopen/result mới; notify các nhận handoff |
| Không đổi state: deadline/handover | revise_deadline/handover_task; task.assign; C/P/Dp | Căn cứ/hạn cũ-mới, owner mới nhận, việc tồn; người nghỉ theo K | Notify đúng owner; giữ lịch sử quá hạn theo baseline cũ |

**Ngoại lệ/nghiệm thu:** người phối hợp không thay owner bằng việc upload; phát sinh task con có owner riêng, không nhiều người chịu trách nhiệm duy nhất cùng task. File chứa tiền không hạ mức qua task. D-N: owner nhận → gửi bản 1 → bị trả → gửi bản 2 → người nhận chấp nhận, history đủ. D-X: người giao thiếu scope hoặc reviewer không được chỉ định không được complete; owner nghỉ chưa bàn giao giữ unresolved và cảnh báo, không giả biên nhận. Reopen sau issue tài liệu tạo revision G/J riêng. Deadline lấy từ hồ sơ, chưa có căn cứ không tự cảnh báo vi phạm SLA.

**Q:** KD/trưởng phòng xác nhận công cụ giao việc chính thức giai đoạn đầu, nhận việc/accept kết quả, phụ thuộc và cách thống kê quá hạn (Q9/Q10); không mặc định TANPHAT ONE thay BASE.

## E. Giao khoán nội bộ, thầu phụ cấp 1/2, điều chỉnh và quyết toán

**Căn cứ:** O/E09, U không tạo ledger song song; R chưa có model allocation. **Mục đích:** phân phạm vi/trách nhiệm/giá trị nhận khoán; không biến khoán nội bộ thành mua hàng pháp lý. **Bắt đầu:** có phạm vi nguồn và đề nghị giao khoán. **Kết thúc:** completed hoặc terminated với bảng quyết toán/ngoại lệ và nghĩa vụ chuyển H/I.

**RACI:** KD/project owner R; Trưởng ban A về điều phối; phòng nhận R thực hiện phạm vi được nhận, QT-TC/chuyên môn C; lãnh đạo/người có thẩm quyền quyết định theo BASE/văn bản. **Input:** company/project, nguồn contract/revision/line, loại `external_subcontract`/`internal_allocation` cấp 1 hoặc `department_subcontract` cấp 2, phòng/đối tác nhận, cha, scope, giá trị/currency/basis, mốc, điều khoản nghiệm thu/tạm ứng/giữ lại, căn cứ cho phép. **Output:** baseline khoán, parent-child và scope/version; giao D/F/G, H nhận phạm vi nghiệm thu; I chỉ nhận nghĩa vụ pháp lý đúng đối tác.

| Từ → đến | Action; capability/actor; scope | Guard/field/evidence, nơi quyết định | Audit/thông báo |
| --- | --- | --- | --- |
| Mới → draft | prepare_allocation; allocation.prepare; C/P/Dp | Cấp 2 bắt buộc cha internal cùng company/project/phòng nhận, không cycle; nguồn line đúng revision, unique mã company | Lưu binding nguồn; notify phòng nhận |
| draft → in_review | submit_allocation; allocation.submit; C/P/Dp | Scope/đơn vị/người nhận/mốc, amount/basis/currency, điều khoản, tệp; tiền cần grant + draft_edit | Freeze version; notify KD/QT-TC/chuyên môn |
| in_review → returned hoặc ready_for_execution | return/record_ready; allocation.review/lifecycle_manage; C/P/Dp | Review checklist, căn cứ BASE/ủy quyền khi áp dụng; legal subcontract phải có C và điều kiện hiệu lực. Vượt mẹ cảnh báo và cần policy Q7, chưa tự hard block hay tự cho qua pilot | Return có reason; ready khác decision/ký và chỉ khi đủ căn cứ; notify phòng nhận |
| returned → in_review | revise_resubmit; allocation.prepare/submit; C/P/Dp | Version mới, xử lý ý kiến; không sửa bản trình | Giữ bản trước; notify reviewer |
| ready_for_execution → executing | acknowledge_start; allocation.execute; C/P + đúng phòng/đối tác nội bộ được chỉ định | Phòng nhận xác nhận phạm vi/mốc, evidence cho phép đã đủ; đối tác ngoài chưa có portal tự nhận | Biên nhận triển khai; notify KD/owner task |
| executing → executing với baseline mới | propose_adjustment/confirm_revision; allocation.revise; C/P/Dp | Scope/giá trị/mốc trước-sau và ảnh hưởng con/NT; review/BASE/ký lại nếu áp dụng; không sửa hồi tố silently | Version mới/ngày hiệu lực; notify con/H/I; không double-count |
| executing → settlement_review → completed | submit/confirm_settlement; allocation.settle; C/P/Dp | Phạm vi thực hiện/NT, bản đối chiếu với phòng/đối tác, phần chưa làm/giữ lại, lý do chênh; authority Q7/Q8 | Chốt kết quả quản trị, nghĩa vụ tiền còn tồn rõ; notify QT-TC/KD, không auto-paid |
| draft/in_review/returned → cancelled; ready/executing/settlement_review → terminated | cancel/terminate_allocation; allocation.cancel/lifecycle_manage; C/P/Dp | Lý do/căn cứ, task/NT/contract/cash chịu ảnh hưởng, bảo toàn phần đã thực hiện | History; mở việc xử lý từng chứng từ, không xóa dòng con/posted |
| completed/terminated → correction case | reopen_settlement; allocation.reopen; C/P/Dp | Q8, authority/reason, đối chiếu ảnh hưởng; tạo bản mới không xóa quyết toán | Notify phòng nhận/QT-TC, giữ báo cáo tại thời điểm trước |

**Quy tắc quyết định/tính:** tổng công ty chỉ cấp 1; con cấp 2 phục vụ phân tích phòng. Contract thầu phụ liên kết allocation không đếm hai nghĩa vụ. Con 30+45, mẹ 70 thì vượt 5, phần giữ lại -5; không clamp zero. Phân bổ đổi phạm vi không hợp thức hóa NT sai phạm vi cũ. Khoán nội bộ không tạo PO/vendor bill giả, khoán cá nhân/lương chờ HR/Finance (Q11).

**Ngoại lệ/nghiệm thu:** thiếu cha/currency/basis/nguồn phải trả về bổ sung; trùng mã nguồn cần mapping owner xác nhận. Owner nghỉ không xóa allocation hoặc tự đổi phòng nhận. E-N: mẹ 70 và con 30+45 cho tổng company=70, cảnh báo vượt 5; thêm thầu phụ company 20 thành tổng cấp 1=90. E-X: caller phòng khác gắn cha khác project hoặc cycle bị từ chối, BASE của version cũ không cho ready version đổi giá. Hoàn thành khoán vẫn có công nợ/giữ lại, không tự kết thúc I.

**Q:** KD/phòng nhận/QT-TC xác nhận Q7 vượt mẹ, Q8 correction/quyết toán; lãnh đạo/pháp lý Q1/Q2 thẩm quyền; Q4/Q5 basis/danh mục và hồ sơ nguồn trước import/pilot. Chưa có policy đó thì chỉ thiết kế/giả lập, không tuyên bố sẵn sàng mở khoán thật.
