# Kế hoạch tháng 1 — khảo sát, khung hệ thống và techstack

## Mục tiêu tháng

Trong tháng đầu, Tadic Management chưa triển khai code chức năng nghiệp vụ. Mục tiêu là hiểu cách các phòng ban đang làm việc, mô tả khung hệ thống cần xây, xác định dữ liệu và quyền, rồi đề xuất techstack có căn cứ.

## Đầu ra bắt buộc cuối tháng

- Bản đồ nghiệp vụ hiện tại của P.KHKD và các phòng liên quan.
- Danh mục biểu mẫu, dữ liệu, báo cáo và tài liệu cần quản lý.
- Danh sách vai trò, quyền và luồng phê duyệt cần xác nhận.
- Sơ đồ khung hệ thống: module, dữ liệu, luồng xử lý, nhật ký và tài liệu đính kèm.
- Đề xuất techstack và lý do chọn.
- Danh sách MVP và roadmap bắt đầu từ tháng 2.
- Danh sách câu hỏi còn mở, người phụ trách và hạn trả lời.

## Tuần 1 — Đọc và lập bản đồ hệ thống hiện tại

Mục tiêu: hiểu file mẫu của Phòng Kế hoạch Kinh doanh và cách dữ liệu đi từ nhập liệu đến báo cáo.

1. Đọc HDSD phần I, III, IV, V, VI và VII.
2. Đọc sheet DATA, Dashboard, ChuDauTu, Thauphu, NHAT_KY_TC và NHAT_KY.
3. Ghi lại hai luồng chính: giao dịch với chủ đầu tư và giao dịch với thầu phụ/khoán nội bộ.
4. Ghi lại các quy tắc không được làm mất khi chuyển hệ thống: nhật ký chỉ ghi thêm, sửa/hủy phải truy vết, không tính trùng thầu phụ của phòng, tổng hợp theo mã dự án.
5. Lập danh sách điểm chưa hiểu để hỏi Phòng Kế hoạch.

Đầu ra: sơ đồ hệ thống Excel hiện tại, bảng thuật ngữ và chỉ tiêu, danh sách câu hỏi khảo sát, bản phân tích mẫu PKH.

## Tuần 2 — Khảo sát và xác nhận nghiệp vụ

Mục tiêu: xác nhận quy trình thật, không suy đoán từ file mẫu.

1. Làm việc với Phòng Kế hoạch Kinh doanh.
2. Làm rõ người dùng, người nhập, người duyệt và người xem báo cáo.
3. Thu biểu mẫu, dữ liệu mẫu đã ẩn thông tin nhạy cảm và tài liệu đầu vào.
4. Đối chiếu file Excel với cách làm thực tế: phần nào đang dùng, phần nào là quy ước cũ, phần nào cần bỏ.
5. Làm rõ liên hệ với Phòng Kế toán và báo cáo lãnh đạo.

Đầu ra: biên bản khảo sát được xác nhận, danh mục biểu mẫu và trường dữ liệu, danh sách vai trò và quyền sơ bộ, danh sách vấn đề và ưu tiên xử lý.

## Tuần 3 — Thiết kế khung hệ thống

Mục tiêu: mô tả hệ thống tương lai ở mức đủ để chọn công nghệ và lập backlog, chưa viết module.

1. Chia hệ thống thành các mảng: dự án, hạng mục, chủ đầu tư, thầu phụ/khoán, giao dịch, nghiệm thu, thanh toán, tài liệu, báo cáo và quản trị người dùng.
2. Vẽ sơ đồ dữ liệu và quan hệ giữa các thực thể.
3. Mô tả trạng thái và luồng của một giao dịch.
4. Thiết kế nguyên tắc nhật ký: tạo, sửa, hủy, người thực hiện, thời điểm và bản ghi gốc.
5. Xác định cách lưu link hợp đồng, biên bản, hóa đơn và chứng từ.
6. Xác định báo cáo cần có cho phòng ban và lãnh đạo.

Đầu ra: sơ đồ kiến trúc khái niệm, sơ đồ dữ liệu mức nghiệp vụ, ma trận quyền dự kiến, mô tả luồng chính, yêu cầu phi chức năng.

## Tuần 4 — Đề xuất techstack và bàn giao tháng 2

Mục tiêu: đưa ra quyết định công nghệ và phạm vi triển khai có thể bắt đầu sau khi được duyệt.

Đề xuất ban đầu:

- Odoo 20: nền tảng quản trị, người dùng, nhóm quyền, workflow và giao diện nội bộ.
- PostgreSQL: cơ sở dữ liệu chính.
- Python/XML/JavaScript: phát triển module Odoo khi yêu cầu đã được chốt.
- Git/GitHub: quản lý mã nguồn và lịch sử thay đổi.
- Odoo Scheduled Actions hoặc job nền: thay thế việc tổng hợp thủ công/hằng đêm nếu cần.
- ir.attachment hoặc kho lưu trữ dùng chung: quản lý tài liệu đính kèm, tùy quy định công ty.
- React: chỉ dùng khi có nhu cầu giao diện riêng đã được chứng minh; không mặc định xây song song với giao diện Odoo.

Việc cần làm:

1. So sánh Odoo thuần với Odoo kết hợp React.
2. Đánh giá khả năng thay thế từng phần của file Excel hiện tại.
3. Xác định dữ liệu cần nhập ban đầu và dữ liệu chỉ phát sinh mới.
4. Chọn một luồng MVP có thể nghiệm thu từ đầu đến cuối.
5. Lập backlog tháng 2 và tiêu chí nghiệm thu.
6. Trình bày khung hệ thống và techstack để người phụ trách duyệt.

Đầu ra: tài liệu đề xuất techstack, khung kiến trúc hệ thống, backlog MVP tháng 2, roadmap và danh sách rủi ro/phụ thuộc.

## Những việc không làm trong tháng 1

- Không viết model Odoo nghiệp vụ chính thức.
- Không viết API React–Odoo.
- Không cài hàng loạt ứng dụng Odoo khi chưa có yêu cầu.
- Không di chuyển dữ liệu thật.
- Không tự chốt quyền hoặc quy trình thay phòng ban.
- Không coi giao diện React hiện tại là màn hình nghiệp vụ đã duyệt.

Odoo, PostgreSQL, Git và React đã dựng trước đó chỉ là môi trường kiểm tra kỹ thuật. Có thể giữ lại, nhưng không tính là sản phẩm nghiệp vụ của tháng 1.

## Điều kiện chuyển sang tháng 2

Chỉ bắt đầu code khi đã có người xác nhận: quy trình ưu tiên, biểu mẫu/trường dữ liệu, vai trò/quyền, phạm vi MVP và tiêu chí nghiệm thu.
