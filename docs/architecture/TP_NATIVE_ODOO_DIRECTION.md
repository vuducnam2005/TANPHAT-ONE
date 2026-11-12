# TANPHAT ONE — Hiện trạng và hướng giao diện Odoo

Ngày xác nhận hướng: 05/11/2026. Cập nhật audit TP Contracts và kế hoạch KH-KD06/11/2026, CHG-20261106-004. Căn cứ: DEC-030, người dùng quyết định phát triển giao diện dựa trên Odoo, không tách frontend riêng làm giao diện chính.

## 1. Hiện tại có gì?

| Nhóm | Đã có | Giới hạn cần hiểu |
| --- | --- | --- |
| Nền vận hành local | Odoo 18069, PostgreSQL 55432, database dev, session, phân quyền; tooling backup/restore local | Chưa phải production; backup ngoài máy và vận hành chính thức còn cổng riêng |
| Giao diện native | Home, tìm ứng dụng, menu, tiếng Việt, dashboard tùy biến, điều chỉnh mobile | DASH/MOBILE có handoff kỹ thuật; lượt này không audit lại code hoặc xác nhận thiết bị thật |
| Odoo chuẩn đã cài | CRM, hồ sơ nhân viên, dự án/công việc, timesheet, chi phí nhân viên, nền hóa đơn/kế toán | Cài addon không đồng nghĩa hoàn tất nghiệp vụ toàn công ty; Attendance/Leave/Purchase chưa cài |
| TP Projects | Mở rộng cùng `project.project`, mã dự án, phân công, scope và quyền tiền riêng | Không tạo một kho dự án độc lập cạnh Project; quyền cập nhật tiến độ task còn gap TASK-001 |
| TP Contracts | Model/backend cũ; đã thêm menu/list/form chỉ đọc và wizard native gọi sáu action trên owned clone18169; audit độc lập Odoo107/browser42/runner18 đạt, CHG-20261106-003 | `TECHNICAL_ACCEPTED_TEST_ONLY`, chưa áp dev/người thật; G7/Q2/business/pilot giữ mở. [Audit](../reviews/UI_CTR_NATIVE_001A_INDEPENDENT_AUDIT.md) |
| Liên kết dữ liệu | Cơ hội nối dự án; task, giờ làm, chi phí và hóa đơn mẫu có liên kết | Dữ liệu giả; 4 hóa đơn khách hàng hiện đều nháp, không phải doanh thu ghi sổ hoặc tiền đã thu |
| Thiết kế tương lai | Hồ sơ BASE, Bid, giao khoán, sản lượng/nghiệm thu, thanh toán, chuyên môn khảo sát/thiết kế, dữ liệu/báo cáo | Tài liệu, tên phân hệ và prompt không chứng minh chức năng đã triển khai |

Nguồn hiện trạng: `PROJECT_STATUS.md`, source addon, handoff NATIVE-DATA-003/DASH/MOBILE và kiểm runtime/SQL chỉ đọc ngày 05/11/2026. Không chạy lại application tests trong lượt chốt hướng tài liệu này. `tp_web_login` chưa cài trên dev: đăng nhập native hiện không tự nhận giao diện login React cũ. `tp_demo_workspace` không cài trên dev; các môi trường demo cũ đã ngừng theo status.

## 2. Kiến trúc chính từ nay

```text
Người dùng trên máy tính / trình duyệt điện thoại
                         |
                         v
Odoo: Home chung → workspace/menu/dashboard theo quyền
         view/form/list chuẩn + OWL/QWeb/SCSS khi cần
                         |
                         v
Action/model Odoo: nghiệp vụ, quyền, phiên bản, lịch sử
                         |
                         v
PostgreSQL + filestore dùng chung theo môi trường

API hiện có → giữ cho tích hợp / tương thích / kiểm thử
React cũ   → giữ source và test; không mở rộng làm FE chính
```

OWL là bộ công cụ giao diện của Odoo; QWeb là công cụ template; SCSS dùng định dạng giao diện. Ưu tiên màn hình Odoo chuẩn cho nhập liệu, bảng và tìm kiếm; chỉ tùy biến sâu khi có nhu cầu rõ. Giao diện có thể mang nhận diện TANPHAT ONE, không bắt buộc giữ nguyên hình thức mặc định.

Một nền giao diện chung toàn công ty; mỗi phòng có workspace, menu, dashboard, trường và nút theo quyền. Đây là hướng tổ chức, không phải tất cả workspace đã được dựng. Quyền phải được bảo vệ ở backend, kể cả truy cập ORM/RPC/export/file trực tiếp. Không tự ghi state, dùng `sudo` hoặc thêm nút làm mất guard workflow/version/idempotency/audit. Custom code chỉ đặt trong `custom_addons/`.

## 3. Giữ lại và chuyển tiếp

- Giữ model, dữ liệu, phân quyền, session và action nghiệp vụ đã có; không xây lại backend/database vì đổi giao diện.
- Giữ `frontend/`, API, OpenAPI và test để tham khảo/hồi quy. Chỉ sửa phần này khi có phạm vi tương thích rõ; chưa xóa, tắt route hoặc đổi đăng nhập.
- Native UI gọi backend theo cơ chế Odoo; không bắt mọi màn hình đi qua REST. Khi đổi API vẫn phải cập nhật OpenAPI và kiểm tương thích.
- BASE tiếp tục là nơi phê duyệt chính thức giai đoạn đầu. Đổi UI không mở quyền ký, hiệu lực, thu/chi hoặc grant người thật.
- DEC-030 là quyết định hướng phát triển. Lượt này chỉ sửa tài liệu, không migration runtime, schema, cấu hình, tài khoản hoặc module.

## 4. Thứ tự đề xuất

1. Đặc tả UI-CTR-NATIVE-001: đối chiếu action backend hiện có, lập menu/list/form/tài liệu hợp đồng, ma trận trường/nút theo quyền, cách giữ version/idempotency và tiêu chí test. Chưa gọi là sẵn sàng code khi chưa có đặc tả này. **Đã viết** ở CHG-20261105-002: [đặc tả](TP_UI_CTR_NATIVE_001_SPEC.md) `READY_FOR_TEST_CODE` cho 001a; upload tệp và các bước BASE/ký/hiệu lực chưa sẵn sàng.
2. Batch001a đã đạt audit kỹ thuật trên test bằng dữ liệu giả, CHG-20261106-003: tạo/sửa nháp, gửi, trả lại có lý do, mở sửa và gửi lại. Next: dùng lại trong [KD-NATIVE-001](../../deliverables/PROMPT_KHKD_NATIVE_18069.md), dựng workspace/liên kết và các hồ sơ KH-KD theo từng lô. Người dùng đã yêu cầu trình diễn dev18069; chỉ tích hợp sau snapshot/restore/clone-test của batch đó. Không tạo state trùng hoặc mở action BASE/ký/hiệu lực; không suy đã áp dev từ kết quả test001a.
3. Xử lý TASK-001 theo policy đã xác nhận, để người được giao cập nhật tiến độ đúng phạm vi. Audit DASH/MOBILE độc lập theo handoff; không tự nâng kết quả thành business acceptance.
4. Mở từng workflow giao khoán → sản lượng/nghiệm thu → đề nghị thanh toán → đối chiếu kế toán khi gate tương ứng đạt. Dashboard tiền phải phân biệt kế hoạch, đề nghị, hóa đơn và tiền thực thu/chi.

Xem [quyết định](../DECISIONS.md), [trạng thái](../PROJECT_STATUS.md), [kiến trúc source](TP_PLATFORM_SOURCE_STRUCTURE.md), [lộ trình](../ROADMAP.md) và [quy trình điều phối](../AI_COORDINATION_WORKFLOW.md).
