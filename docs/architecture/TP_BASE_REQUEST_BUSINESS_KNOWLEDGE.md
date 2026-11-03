# TANPHAT ONE — Kiến thức nghiệp vụ Request trên BASE

**Mục đích:** ghi lại điều đã quan sát và cách diễn giải an toàn về Request trên BASE để các phiên AI sau không phải suy đoán lại. Tài liệu này không phải quy chế phê duyệt của công ty, không tạo quyền và không cho phép xây connector khi API/chủ sở hữu chưa được xác nhận.

**Ngày ghi nhận:** 29/10/2026 (Asia/Saigon)  
**Phạm vi:** một phiên đăng nhập, một tài khoản/filter, đọc-only trên `home.base.vn` và `request.base.vn` do người dùng mở  
**Mã provenance:** `REF-BASE-REQUEST-20261029` — `observed-static`; không phải kiểm chứng toàn công ty  
**Nguồn liên quan:** [sổ nghiên cứu và bàn giao](TP_REFERENCE_RESEARCH_AND_HANDOFF.md), [workflow BIZ-002 F–M](TP_PROCESS_WORKFLOWS_F_M.md), [tích hợp và KPI](TP_BIZ002_INTEGRATION_AND_REPORTING.md), [quyết định](../DECISIONS.md)

## 1. Nhãn bằng chứng

- **Observed-static:** nhãn, nhóm, trường và nút nhìn thấy trên giao diện; chưa thực hiện thao tác gửi/duyệt.
- **User-confirmed:** người dùng đã chốt BASE là nơi phê duyệt chính thức giai đoạn đầu (DEC-013).
- **Proposed-TP:** cách TANPHAT ONE dự kiến lưu hồ sơ/kết quả để làm việc cùng BASE; chưa phải state của BASE và chưa phải code.
- **Open:** cần hồ sơ, owner, căn cứ thẩm quyền, kiểm tra runtime hoặc API của BASE.

Không lưu credential, cookie, ID cá nhân, số tiền thật, nội dung hồ sơ thật hay ảnh có dữ liệu nhạy cảm trong tài liệu này.

## 2. Điều đã quan sát trên BASE

### 2.1 Ứng dụng và khu vực Request

Trang home hiển thị các ứng dụng Platform, XSpace, Message, Drive, Wework, Request và Account. Trong Request đã nhìn thấy các nhóm/khu vực:

- đề xuất trực tiếp;
- IT help desk;
- tạm ứng/thanh toán của TADIC và Tấn Phát;
- công tác;
- văn phòng phẩm;
- photocopy/in ấn/chuyển phát;
- phần mềm/thiết bị điện tử;
- mượn xe;
- đơn/biểu mẫu;
- duyệt công văn;
- phiếu giao việc;
- mượn dấu;
- một số nhóm thanh toán khác.

Các tab/lọc đã nhìn thấy gồm: tất cả, đến lượt tôi duyệt, quá hạn, chờ xử lý, đã chấp nhận, từ chối, trả lại, đánh dấu và bản nháp. Đây là các tab giao diện; chưa được coi là tên state API hoặc thứ tự chuyển state.

### 2.2 Form đã mở

Form nhóm **[Tấn Phát] Đề xuất tạm ứng, thanh toán** hiển thị:

| Thành phần | Quan sát | Ý nghĩa an toàn |
| --- | --- | --- |
| Tiêu đề | Bắt buộc | Request cần tiêu đề để nhận diện |
| Nhóm | Bắt buộc | Chọn quy trình/nhóm Request trên BASE |
| Nội dung | Vùng nhập tự do | Không coi là trường số tiền, dự án hay hợp đồng có cấu trúc |
| Người duyệt | Một số người duyệt cố định được hiển thị | Chỉ chứng minh cấu hình của nhóm/tài khoản quan sát; chưa chứng minh hạn mức, thứ tự hay thẩm quyền pháp lý |
| Người theo dõi | Có thể thêm | Người nhận thông tin, không mặc nhiên là người duyệt |
| Tệp đính kèm | Giao diện ghi tối đa 10 tệp | Cần kiểm thêm dung lượng, loại tệp, version, tải xuống và retention |
| Thao tác | Tạo và lưu nháp | Có khả năng lưu nháp; chưa thực hiện để tránh tạo hồ sơ thật |

Trong form này không nhìn thấy trường có cấu trúc cho project, contract hoặc amount. Điều đó chỉ áp dụng cho form đã mở; không kết luận các nhóm khác cũng thiếu trường. Không có Request hiển thị trong filter hiện tại; điều đó không chứng minh hệ thống không có hồ sơ. Các lần mở thêm nhóm/template ở tab mới bị chuyển về login nên không được coi là đã khảo sát template đó.

## 3. Mô hình nghiệp vụ cần nhớ

**Diễn giải Proposed-TP:** Request trên BASE có thể được xem là **hồ sơ đề nghị**: một chủ thể gửi yêu cầu thực hiện/chi/việc tới một nhóm xử lý và người duyệt. Đây là diễn giải kiến trúc để thiết kế liên kết; phiên quan sát chưa xác minh creator, submitter, requester, beneficiary và owner có phải cùng một người hay không. Request không được xem là sổ cái, chứng từ kế toán, hợp đồng hoặc bằng chứng tự động về chữ ký/hiệu lực.

TANPHAT ONE phải giữ riêng các lớp sau:

1. **Request đề nghị:** ai đề nghị, nội dung, nhóm, đối tượng liên quan, phiên bản và bằng chứng.
2. **Review nội bộ:** rà soát dữ liệu, điều kiện và phạm vi; có thể trả lại để sửa.
3. **BASE decision:** kết quả phê duyệt chính thức bên ngoài; phải có reference và evidence.
4. **Ký/hiệu lực:** lớp pháp lý riêng; BASE approved không tự trở thành signed/effective.
5. **Invoice/payment:** lớp thực hiện kế toán riêng; approved/request không tự thành posted hoặc paid.

Các tài liệu nội bộ BIZ-002 đang mô tả những lớp này tách nhau. Các state `finance_review`, `ready_for_base`, `awaiting_base`, `externally_approved` là **Proposed-TP** để TANPHAT quản trị hồ sơ, không khẳng định BASE dùng đúng các tên đó.

## 4. Vòng đời tham chiếu

### 4.1 Những gì có thể suy ra ở mức giao diện

| Nhãn giao diện | Diễn giải tối thiểu | Không được suy ra |
| --- | --- | --- |
| Bản nháp | Hồ sơ đang soạn hoặc lưu chưa gửi | Chưa biết actor nào có quyền sửa, hoặc bản nháp có khóa số liệu, version hay audit đầy đủ không |
| Chờ xử lý/đến lượt tôi duyệt | Có hồ sơ đang chờ một bước xử lý hoặc đến lượt tài khoản | Chưa biết thứ tự, quorum, người thay thế hay hạn mức |
| Trả lại | BASE có nhãn hồ sơ trả lại | Chưa xác minh đây là internal return hay một trạng thái khác, reason bắt buộc, người sửa và cách gửi lại |
| Đã chấp nhận | BASE hiển thị nhãn chấp nhận | Không đồng nghĩa ký, hiệu lực, invoice, payment hay cash |
| Từ chối | BASE hiển thị nhãn từ chối | Chưa xác minh đây là external reject, reason, quyền mở lại hoặc tạo request mới |
| Quá hạn | Nhãn theo dõi quá hạn | Không tự là một quyết định nghiệp vụ |
| Đánh dấu | Cờ cá nhân/giao diện | Không phải state của hồ sơ |

### 4.2 Luồng TANPHAT đề xuất để ghi nhận kết quả BASE

Đây là luồng tham chiếu để thiết kế tích hợp sau này, chưa mở code:

```text
TP draft
  → finance_review (nếu là request tài chính)
  → returned để sửa, hoặc ready_for_base
  → awaiting_base (ghi ID/link/version/hash hồ sơ đã gửi BASE)
  → declared approved/rejected/cancelled (ghi kết quả BASE)
  → verified/disputed (đối chiếu actor, thời điểm, evidence, authority)
```

Luồng này không cho phép TANPHAT tự `approve` thay BASE. `externally_approved` chỉ là projection đọc khi decision đã approved, evidence đã verified, authority đúng scope và hồ sơ không đổi. Nếu thiếu nguồn, dùng `pending`, `unknown`, `disputed` hoặc `missing_source`, không thay bằng `0` hay “đã thanh toán”.

### 4.3 Trả lại, từ chối và sửa sai

Các quy tắc dưới đây là **Proposed-TP** từ workflow BIZ-002 H/I, chưa xác minh nghĩa và transition của các nhãn UI BASE:

- **Returned:** yêu cầu sửa nội bộ; phải giữ lý do, ý kiến và liên kết bản cũ/bản mới. Bản cũ không bị xóa.
- **Rejected:** quyết định từ chối của BASE hoặc reviewer theo đúng lớp; không đổi tên thành returned.
- **Withdrawn/cancelled:** chưa quan sát trên BASE; chỉ thiết kế khi có bằng chứng và owner.
- **Disputed:** trạng thái chưa thống nhất bằng chứng khi TANPHAT xác minh; không tự trở thành quyết định rejected của BASE.
- **Sửa số tiền hoặc nội dung sau khi gửi:** tạo version/request mới, không dùng lại BASE reference của bản có nội dung khác.
- **Một request nhiều payment hoặc nhiều request một payment:** chỉ liên kết và đối chiếu theo ID/currency; không nhân tổng khi báo cáo.

## 5. Vai trò và quyền tham chiếu

| Vai trò | Trách nhiệm tham chiếu | Tình trạng |
| --- | --- | --- |
| Requester/creator/submitter/beneficiary | Có thể là các actor lập, gửi hoặc thụ hưởng hồ sơ | Chưa có request thực để xác minh các vai trò này là một hay nhiều người; không suy từ form |
| Reviewer/approver | Có thể xem và xử lý hồ sơ trên BASE | Có nhãn/người duyệt hiển thị ở form; thứ tự, quorum, delegation, capability và thẩm quyền chưa kiểm |
| Follower | Có trường/người theo dõi trong form | Chức năng notification/watch, quyền đọc file/tiền và quyền xử lý vẫn `Open`; không tự cấp quyền |
| BASE recorder | Ghi ID/link, version, hash, kết quả và evidence vào TANPHAT | Proposed-TP; chưa có API, owner hay quy trình được xác nhận |
| Finance reviewer | Rà soát request tài chính ở TANPHAT trước khi gửi BASE | Proposed-TP theo BIZ-002; chưa phải quyền BASE |
| Accountant | Post/reconcile chứng từ native Odoo khi đủ căn cứ | Quy trình TP/Q4/Q6 còn mở; không phát sinh từ request tự động |

Không suy quyền từ chức danh. Quyền phải kiểm company/project/department scope, capability, field tiền và attachment grant. Người có quyền sửa request không mặc nhiên được xem số tiền hoặc cấp grant.

## 6. Dữ liệu TANPHAT cần liên kết khi chưa có API

Giai đoạn đầu, reference thủ công là phương án an toàn:

- loại request và nhóm BASE;
- request/version ID nội bộ;
- project/contract/allocation nếu có;
- requester, owner và scope company/department/project;
- currency, amount và basis theo quyền đọc/ghi tiền riêng; việc nhìn thấy form hoặc là follower không tự tạo financial grant;
- BASE ID hoặc manual reference, URL nếu được phép, trạng thái quyết định;
- version/hash của hồ sơ đã gửi và tệp bằng chứng;
- decided_by/decided_at, recorded_by/recorded_at, verification/authority source;
- reason khi returned/rejected/cancelled/withdrawn;
- correlation/request ID, expected version và audit actor/state trước–sau.

Các trường trên là yêu cầu thiết kế có điều kiện, không phải tuyên bố BASE đã cung cấp API tương ứng. Không lưu token/credential BASE trong Git hoặc trong DTO frontend.

## 7. Những điều chưa được kiểm chứng

Trước khi xây connector hoặc mở workflow Request thật, phải kiểm tra:

1. API, export, webhook hoặc cách lấy ID/link/version từ BASE.
2. State thật và transition thật: gửi, duyệt, trả lại, gửi lại, từ chối, thu hồi, quá hạn.
3. Reason bắt buộc, lịch sử đầy đủ, timestamp, actor, thứ tự/quorum và delegation.
4. Hạn mức, căn cứ ủy quyền, người thay thế và phân quyền theo nhóm.
5. Quyền xem số tiền, tệp đính kèm, dữ liệu dự án và dữ liệu nhạy cảm.
6. Dung lượng/loại tệp, version, retention, tải xuống và audit attachment.
7. Cách liên kết request với hợp đồng, project, nghiệm thu, invoice và payment.
8. Quy tắc correction sau BASE approved hoặc sau khi đã post/reconcile.
9. Owner chịu trách nhiệm ghi nhận/xác minh kết quả và hồ sơ 2–3 case khử dữ liệu.

Không có các bằng chứng này thì chỉ được làm discovery, mapping thủ công hoặc test fixture; không tự nhập hồ sơ thật, không bật approval/payment thật và không tạo engine duyệt thay BASE.

## 8. Quy tắc cho phiên AI sau

Khi task chạm Request, AI phải đọc tài liệu này cùng [TP_REFERENCE_RESEARCH_AND_HANDOFF.md](TP_REFERENCE_RESEARCH_AND_HANDOFF.md), `PROJECT_STATUS.md`, `DECISIONS.md` và BIZ-002 F–M. AI phải nêu rõ mỗi đề xuất là `User-confirmed`, `Observed-static`, `Runtime-evidence`, `Proposed-TP` hay `Open`.

Không dùng tên tab BASE làm enum Odoo, không suy Request/Bid từ `purchase_requisition`, không map “đã chấp nhận” thành “đã trả tiền”, và không tạo code/API chỉ vì thấy form có nút tạo/lưu nháp. Mọi batch code phải có owner, scope, acceptance, security, audit, version/idempotency và test theo `AI_CHANGE_WORKFLOW.md`.

