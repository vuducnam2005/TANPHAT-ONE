# Kế hoạch tổng thể Tadic Management — bản điều chỉnh

## 1. Mục tiêu mới

Trong tháng đầu, mục tiêu chính không phải là viết chức năng. Mục tiêu là:

1. Hiểu cách Phòng Kế hoạch Kinh doanh và các phòng liên quan đang làm việc.
2. Chuyển cách làm hiện tại trong file Excel thành bản mô tả nghiệp vụ rõ ràng.
3. Dựng khung hệ thống tương lai: module, dữ liệu, quy trình, quyền, nhật ký và báo cáo.
4. Đề xuất techstack có căn cứ.
5. Chốt một phạm vi MVP đủ nhỏ để bắt đầu code từ tháng 2.

File `Mẫu PKH - Quản trị dự án v10_5.xlsm` là tài liệu tham khảo để khảo sát, không phải đặc tả cuối cùng. Những gì đang có trong file phải được phòng ban xác nhận trước khi biến thành chức năng.

## 2. Lộ trình theo tháng

### Tháng 1 — Khảo sát và thiết kế

| Giai đoạn | Trọng tâm | Việc chính | Đầu ra |
| --- | --- | --- | --- |
| Tuần 1 | Tự đọc và lập bản đồ hiện trạng | Đọc workbook, ghi nhận luồng dữ liệu, thuật ngữ, quy tắc và câu hỏi | Bản đồ Excel hiện tại, phân tích mẫu PKH, danh sách câu hỏi |
| Tuần 2 | Xác nhận với phòng ban | Hỏi người dùng thực tế, đối chiếu file với cách làm thật, xin biểu mẫu mẫu đã ẩn dữ liệu nhạy cảm | Biên bản khảo sát, danh mục biểu mẫu, vai trò và vấn đề ưu tiên |
| Tuần 3 | Dựng khung hệ thống | Mô tả module, thực thể, trạng thái, luồng, quyền, nhật ký, tài liệu và báo cáo | Sơ đồ kiến trúc khái niệm, sơ đồ dữ liệu nghiệp vụ, ma trận quyền |
| Tuần 4 | Chọn hướng triển khai | So sánh techstack, chọn MVP, lập backlog và tiêu chí nghiệm thu tháng 2 | Đề xuất techstack, backlog MVP, roadmap, rủi ro và điều kiện bắt đầu code |

### Tháng 2 — Xây MVP sau khi được duyệt

Chỉ bắt đầu khi quy trình, trường dữ liệu, vai trò, phạm vi MVP và tiêu chí nghiệm thu đã có người xác nhận.

1. Tạo module và cấu trúc dữ liệu cho đúng phạm vi MVP.
2. Xây một luồng nghiệp vụ từ đầu đến cuối.
3. Cấu hình người dùng, phân quyền và nhật ký thay đổi.
4. Nhập dữ liệu giả lập hoặc dữ liệu đã được cho phép.
5. Kiểm thử với người dùng đại diện và sửa theo phản hồi.

### Các tháng tiếp theo — Mở rộng có kiểm soát

Mở rộng các luồng còn lại, báo cáo, tài liệu, tích hợp và chuyển dữ liệu theo từng đợt. Mỗi đợt phải có phạm vi, người duyệt và tiêu chí nghiệm thu riêng.

## 3. Việc có thể tự làm ngay

- Đọc các sheet và phần hướng dẫn trong workbook.
- Lập bảng thuật ngữ, trường dữ liệu, chỉ tiêu và quy tắc tính.
- Vẽ hai luồng chính: chủ đầu tư và thầu phụ/khoán nội bộ.
- Ghi lại những điểm cần giữ như nhật ký chỉ ghi thêm, sửa/hủy phải truy vết và không tính trùng thầu phụ.
- Soạn câu hỏi khảo sát và sắp xếp theo nhóm: quy trình, dữ liệu, quyền, báo cáo, tài liệu.
- Dựng bản nháp kiến trúc khái niệm, chưa coi là thiết kế đã chốt.
- So sánh Odoo thuần với phương án Odoo kết hợp React.
- Lập danh sách MVP và tiêu chí nghiệm thu dự kiến.

## 4. Việc bắt buộc phải trao đổi với người khác

- Quy trình thực tế có giống file mẫu hay không.
- Ai nhập, ai kiểm tra, ai duyệt và ai chỉ xem.
- Trường nào bắt buộc, trường nào có thể bỏ.
- Quy tắc tính giá trị, nghiệm thu, thanh toán, khoán và công nợ.
- Báo cáo nào đang được dùng để ra quyết định.
- Dữ liệu cũ, tài liệu đính kèm và quyền truy cập được quản lý ở đâu.
- Luồng nào cần làm trước trong MVP.

Không tự suy đoán hoặc tự chốt các nội dung này thay cho phòng ban.

## 5. Định hướng công nghệ dự kiến

- Odoo 20: nền tảng người dùng, nhóm quyền, workflow và giao diện nội bộ.
- PostgreSQL: cơ sở dữ liệu chính.
- Python/XML/JavaScript: phát triển module Odoo sau khi nghiệp vụ được duyệt.
- Git/GitHub: quản lý mã nguồn, nhánh và lịch sử thay đổi.
- Scheduled Actions hoặc job nền: xử lý tổng hợp định kỳ nếu nghiệp vụ cần.
- `ir.attachment` hoặc kho lưu trữ dùng chung: lưu tài liệu theo quy định công ty.
- React: chỉ dùng cho giao diện riêng khi có nhu cầu đã được chứng minh; không xây song song mặc định.

Đây là đề xuất ban đầu, chưa phải quyết định cuối cùng.

## 6. Điều kiện hoàn thành tháng 1

Tháng 1 được xem là hoàn thành khi có đủ:

- Bản đồ nghiệp vụ hiện tại đã được đối chiếu.
- Danh mục biểu mẫu, dữ liệu, báo cáo và tài liệu.
- Danh sách vai trò, quyền và luồng duyệt.
- Khung hệ thống gồm module, dữ liệu, workflow, nhật ký và tài liệu.
- Đề xuất techstack kèm lý do lựa chọn.
- MVP tháng 2 và tiêu chí nghiệm thu.
- Các điểm chưa rõ có người phụ trách và hạn trả lời.

## 7. Trạng thái hiện tại

Đã có: phân tích ban đầu file PKH, checklist tuần 1, mẫu khảo sát, phác thảo dữ liệu/quyền, kế hoạch tháng 1 và môi trường Odoo/Git/React tham khảo.

Còn thiếu: xác nhận từ Phòng Kế hoạch Kinh doanh, khung hệ thống được duyệt, quyết định techstack cuối cùng và phạm vi MVP có tiêu chí nghiệm thu.

Vì vậy, trạng thái hiện tại là **đã chuẩn bị tốt phần tự làm, chưa đủ điều kiện bắt đầu code nghiệp vụ**.
