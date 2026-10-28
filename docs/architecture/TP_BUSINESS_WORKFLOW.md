# TANPHAT ONE — Workflow nghiệp vụ và quy tắc chuyển trạng thái

Đây là blueprint trước khi tạo model/action, không phải danh sách chức năng đã triển khai. Nền hiện tại kiểm chứng đọc project theo quyền; workflow hợp đồng/giao khoán chưa có runtime.

Baseline chi tiết hiện hành cho Ban Kinh doanh/Kế hoạch:

- [BIZ-001: workflow, BASE, state, ma trận quyền và cổng triển khai](TP_KD_WORKFLOW_AND_PERMISSIONS.md).
- [Bằng chứng nguồn và ca nghiệm thu giả lập](TP_KD_EVIDENCE_AND_ACCEPTANCE.md).

Khi code phần KD/Contracts, đọc hai tài liệu này cùng database design. Các đề xuất tuyến tính cũ về hợp đồng bị thay bằng baseline BIZ-001; không lấy chữ approved làm bằng chứng đã ký/có hiệu lực.

## 1. Luồng tổng thể

~~~mermaid
flowchart LR
    A[Cơ hội / dự thầu] --> B[Hợp đồng / phụ lục]
    B --> C[Kế hoạch / giao việc / giao khoán]
    C --> D[Khảo sát / thiết kế / BIM / KCS]
    D --> E[Nghiệm thu]
    E --> F[Hóa đơn / thu chi / đối chiếu]
    F --> G[Hoàn thành / thanh lý / lưu]
~~~

Project có thể mở từ cơ hội/dự thầu; có đường giao trực tiếp, nhiều đợt thực hiện và tạm ứng. Đây không phải dependency bắt buộc giữa addon theo thứ tự menu. TP Documents liên kết hồ sơ xuyên suốt; TP Dashboard chỉ tổng hợp trong scope, không tạo quyết định phê duyệt.

**BASE giữ phê duyệt chính thức trong giai đoạn đầu.** TANPHAT ONE quản trị hồ sơ/rà soát và ghi nhận kết quả. Chưa có tích hợp BASE; không nhận approved từ frontend rồi tự coi là quyết định có thẩm quyền.

## 2. Nguyên tắc chung

- Mỗi đối tượng có workflow riêng. Review, quyết định BASE, chữ ký/hiệu lực và revision là các chiều khác nhau.
- Transition ở backend Odoo, transaction nguyên tử; frontend gọi command, không ghi state tùy ý.
- Kiểm actor/capability, company/project và department scope áp dụng, state trước, field/evidence và điều kiện sau.
- Nhật ký có actor/time/reason/request ID/version; người không có quyền tiền không thấy before/after tiền.
- Draft sửa theo quyền. Hồ sơ gửi đi/chốt giữ bất biến; correction/revision/void có lý do, không xóa bản cũ.
- Thu hồi bằng chứng BASE không tự đảo kế toán posted; cần quy trình xử lý tác động.
- Retry phải có idempotency hoặc được chứng minh an toàn; command nhạy cảm có version/concurrency check.
- Metadata/task không cấp quyền xem tiền hoặc tải bản hợp đồng có giá trị. Scope áp dụng cho RPC/native Odoo/API/export/attachment.
- Authority chưa biết thì lưu unconfirmed; không phát minh hạn mức hay quy chế bốn mắt. 1.000 VND trong Master chỉ là ngưỡng đối chiếu.
- Chứng từ kế toán/hóa đơn/tiền theo Odoo accounting; request/BASE approved không tạo tiền đã thu/chi.

## 3. Quyền hiện có và thiết kế mới

| Phần | Trạng thái |
| --- | --- |
| Project Reader và assignment reader/coordinator | Đã triển khai đọc project được phân công; coordinator hiện vẫn chỉ đọc |
| Platform Manager | Quản lý project metadata/catalog/assignment nền; không ngầm là reviewer/approver hợp đồng |
| KD_HEAD, PROJECT_OWNER, PLANNING, SUPPORT, TECHNICAL, FINANCE, EXECUTIVE | Preset đề xuất của BIZ-001, chưa thành group/XML ID |
| financial.read | Đã triển khai cho TP Contracts (CTR-001): `tp.project.grant` theo user + project, superuser cấp khi Q2 chưa chốt; Platform Manager/admin không có tiền mặc định |
| financial.draft_edit, base_result.record/verify và các capability khác | Thiết kế, phải triển khai/test trong domain tương ứng |
| Người duyệt chính thức | Trên BASE theo văn bản thẩm quyền; không có quyền duyệt song song trong Odoo |

ACL/group rules Odoo có tính cộng quyền, global rules giới hạn giao nhau; không giả định role hạn chế tự thắng. Kiểm quyền theo capability/scope của record. Admin/superuser có khả năng truy cập kỹ thuật; dùng quản trị riêng/audit, API nghiệp vụ không sudo để né scope.

## 4. Project, contract và các đối tượng tiếp theo

- Project dự kiến draft → review → active/on_hold → completed/cancelled; chưa triển khai ngoài active flag chuẩn/tp_managed và assignment. Không thêm state chỉ để mở CTR-001.
- Hợp đồng giữ danh tính ổn định; version hồ sơ/review, approval reference, chữ ký, lifecycle và snapshot revision hiệu lực liên kết rõ. CTR-001 đã có các trường này ở dạng chỉ đọc; chưa có transition submit/review/sign/make_effective. Ánh xạ tên trạng thái nghiệp vụ sang field/giá trị trong code nằm ở mục 4.4 của [workflow KD](TP_KD_WORKFLOW_AND_PERMISSIONS.md).
- Phụ lục PKH là tổng giá trị mới ở phạm vi hạng mục/đơn vị được cập nhật; thiết kế snapshot đầy đủ phải ghép với phạm vi không đổi. Không cộng như delta.
- Giao khoán cấp 1 gồm thầu phụ công ty và khoán nội bộ; cấp 2 thuộc khoán nội bộ cha, cùng company/project, không cộng tổng lần hai.
- Sản lượng, nghiệm thu, hóa đơn, tiền và giữ lại tách riêng. Nghiệm thu cần căn cứ chuyên môn/bên ký; không mặc định mọi biên bản đều phải có một quyết định BASE riêng.
- Đề nghị thanh toán có workflow review/BASE riêng; thực trả/đối chiếu từ chứng từ tiền được phân bổ, gồm tạm ứng và trả nhiều đợt.
- Xem ma trận action/guard và quyền chi tiết tại tài liệu BIZ-001, không duy trì thêm bảng trạng thái cạnh tranh ở đây.

## 5. Cổng triển khai

| Phạm vi | Đầu vào tối thiểu |
| --- | --- |
| CTR-001 đọc | Baseline BIZ-001, typed schema, field/scope/attachment policy, test dữ liệu giả, API DTO — đạt trên dev (CHG-20261028-006) |
| Draft/submit/return trên test | Action matrix, capability, CSRF/version/idempotency/audit và negative tests |
| Xác minh BASE/hiệu lực pháp lý trên pilot | Văn bản thẩm quyền, phân công record/verify, hồ sơ BASE thực tế, quy tắc ngày và correction liên quan |
| Allocation/acceptance/finance/import | Quy chế và hồ sơ đại diện đúng domain; mapping/reconcile, owner nghiệp vụ nghiệm thu |

BIZ-001 hoàn tất phần phân tích, còn nghiệm thu chủ nghiệp vụ và Q1–Q8 theo cổng. Có thể làm read slice trước; không dùng việc còn thiếu hạn mức làm lý do ngừng mọi thiết kế/draft development độc lập.

Thứ tự: tp_contract → tp_allocation → settlement/reporting → staging import → accounting bridge → các phòng tiếp theo theo nhu cầu. Không tạo engine tổng quát hoặc reporting database trước khi có nhu cầu đã kiểm chứng.

