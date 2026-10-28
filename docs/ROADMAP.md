# TANPHAT ONE — Backlog và cổng nghiệm thu

Đây là bản đồ công việc; `PROJECT_STATUS.md` là nơi xác định việc hiện tại và việc tiếp theo. Không đánh dấu xong chỉ vì đã tạo thư mục hoặc viết thiết kế. Mỗi mã việc phải có bằng chứng nghiệm thu.

| ID | Công việc | Trạng thái | Đầu vào/phụ thuộc | Điều kiện hoàn tất |
| --- | --- | --- | --- | --- |
| FND-001 | Addon nền, database dev/test, API đọc project, React shell | Đã kiểm chứng phạm vi dev | Source hiện tại | Login, scope, list/detail, expiry, CSRF logout; các test đã ghi ở status |
| NAME-001 | TANPHAT ONE và chín tên phân hệ | Đã áp dụng | Quyết định trực tiếp của người dùng | Tên tập trung, menu TP Projects, technical IDs giữ nguyên |
| AI-001 | Bộ nhớ dự án và quy trình cập nhật AI | Hoàn tất | Source và bằng chứng hiện có | AGENTS + status + changelog + blueprint + checker; 11 unit tests, Ruff và handoff check đạt (CHG-20261028-001) |
| GIT-001 | Đối chiếu baseline Git sau sự cố | Hoàn tất | Local/remote đã đối chiếu, xem DEC-010 | `main` và `origin/main` cùng ở `a25a0182` trước publish; source inventory sạch theo phạm vi; handoff hiện tại được commit/push; không giả lập hai ID cũ, không reset/clean |
| OPS-001 | Backup/restore rehearsal | Chưa hoàn tất | Source/runtime nhận diện được; dữ liệu dev | Dump DB + filestore + config/source manifest; restore vào môi trường tách biệt và đối chiếu; không chỉ tạo file backup |
| BIZ-001 | Chốt quy trình Kế hoạch Kinh doanh và ma trận quyền | Đề xuất cần xác minh | 2–3 hồ sơ đại diện, người phụ trách nghiệp vụ | Phân biệt hợp đồng/điều chỉnh/giao khoán/sản lượng/nghiệm thu/tiền; actor và approval source rõ |
| PRJ-002 | Workflow vòng đời project | Chưa triển khai | BIZ-001; không thay thế assignment nền | Model extension + action + quyền + history + API + test transition; trạng thái ngoài Odoo active flag |
| CTR-001 | TP Contracts: đọc hồ sơ hợp đồng/phiên bản/phạm vi | Chưa triển khai | BIZ-001, Git đủ tin cậy | `tp_contract`, constraints, security, contract DTO, API read và màn hình read hoạt động |
| CTR-002 | Ghi draft, submit/review và kiểm soát revision | Chưa triển khai | CTR-001 và ma trận quyền | Atomic actions, CSRF, stale version, idempotency khi cần, history và invalid-transition tests |
| ALC-001 | Giao khoán nội bộ/bên ngoài, cấp 1/cấp 2 | Chưa triển khai | Phạm vi hợp đồng và quy tắc đã chốt | Parent-child hợp lệ, cùng project/company, không cộng trùng cấp 2 |
| STL-001 | Sản lượng, nghiệm thu, đề nghị thanh toán, báo cáo | Chưa triển khai | CTR/ALC và cách đối chiếu được xác minh | Các khái niệm tách riêng; tổng hợp cùng scope; đối chiếu dự án mẫu |
| IMP-001 | Staging import Excel | Chưa triển khai | Model mục tiêu ổn định | Provenance, mapping, lỗi dòng, reconcile, phát hành ORM và import lặp không trùng |
| FIN-001 | Bridge TP Finance | Chưa triển khai | Nghiệm thu/hợp đồng và cấu hình kế toán thực tế | Liên kết `account.move`/payment theo chứng từ; accounting giữ posting/reconcile |
| EXT-001 | TP Survey, TP Design, TP Tasks, TP HR, TP Documents | Chưa triển khai ngoài phần Odoo nền | Case nghiệp vụ và owner từng phân hệ | Mở từng vertical slice theo nhu cầu; không làm đồng loạt cho đủ tên |
| PILOT-001 | Nghiệm thu pilot và production | Chưa triển khai | Backup/restore, migration, quyền, đối chiếu dữ liệu, HTTPS | Checklist vận hành và nghiệm thu thực tế; tuyệt đối không dùng dev cluster làm production |

Thứ tự có thể thay đổi theo yêu cầu trực tiếp của người dùng. Khi đổi thứ tự, cập nhật status, decision và changelog trong cùng lượt; giữ rõ phụ thuộc nghiệp vụ thực tế, không coi bảng này là lịch triển khai đã cam kết.
