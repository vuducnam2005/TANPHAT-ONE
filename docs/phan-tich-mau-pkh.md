# Phân tích mẫu PKH — Quản trị dự án v10_5

Nguồn đọc: file mẫu của Phòng Kế hoạch Kinh doanh. Tài liệu này là bản phân tích để chuẩn bị khảo sát, không thay thế quy trình được phòng ban xác nhận.

## Hệ thống hiện tại

Mẫu Excel mô tả ba lớp file:

1. File Phòng Kế hoạch theo từng dự án.
2. File Phòng Kế toán theo từng dự án.
3. File tổng hợp cho lãnh đạo, đọc dữ liệu từ các file phòng ban theo lịch.

File Phòng Kế hoạch có một nơi nhập liệu chính là sheet DATA. Dữ liệu được ghi vào nhật ký, sau đó các bảng ChuDauTu, Thauphu và Dashboard tự tổng hợp.

## Hai luồng nghiệp vụ chính

### Giao dịch với chủ đầu tư

Mỗi sự kiện là một giao dịch riêng: ký hợp đồng, phụ lục, sản lượng thực hiện, nghiệm thu, xuất hóa đơn, nhận tiền và khoản giữ lại. Hệ thống tổng hợp theo hạng mục.

Các nhóm dữ liệu chính: mã dự án, tên dự án/gói thầu, chủ đầu tư, hạng mục, giá trị hợp đồng gốc/cập nhật, sản lượng thực hiện, nghiệm thu, hóa đơn, thanh toán, giữ lại, ngày phát sinh và link hồ sơ.

### Giao dịch với thầu phụ và khoán nội bộ

Form A phân biệt ba đối tượng: thầu phụ công ty, khoán nội bộ và thầu phụ do phòng ký từ phần khoán. Hệ thống cần tránh tính trùng phần thầu phụ của phòng vào tổng chi phí.

Các nhóm dữ liệu chính: đơn vị hoặc phòng/đội nhận khoán, loại giao dịch, phòng cấp khoán, hạng mục, hợp đồng, sản lượng, nghiệm thu, thanh toán, khoán được giao, phần thuê ngoài và khoán còn lại.

## Quy tắc cần bảo toàn khi thiết kế hệ thống mới

- Nhật ký là sổ gốc chỉ ghi thêm; không xóa hoặc ghi đè dòng cũ.
- Sửa và hủy phải tạo bản ghi mới, giữ ID gốc, người thao tác và thời điểm.
- Chỉ tính giao dịch còn hiệu lực vào báo cáo.
- Mã dự án phải thống nhất giữa Phòng Kế hoạch và Phòng Kế toán.
- Giá trị hợp đồng cập nhật là giá trị mới nhất, không cộng dồn phụ lục.
- Sản lượng thực hiện khác giá trị nghiệm thu.
- Thầu phụ của phòng nằm trong khoán và không cộng lại vào tổng thầu phụ.
- Tài liệu phải mở được từ nơi lưu trữ chung, không phụ thuộc máy cá nhân.

## Đối tượng dữ liệu cần kiểm chứng

Dự án, Chủ đầu tư, Hạng mục, Phòng ban, Nhân viên, Thầu phụ, Khoán nội bộ, Giao dịch, Nghiệm thu, Thanh toán, Tài liệu, Nhật ký thay đổi và Báo cáo.

Đây là danh sách khởi đầu. Không tạo model chính thức trước khi xác nhận phòng ban và kiểm tra khả năng tái sử dụng model chuẩn của Odoo.

## Báo cáo/đầu ra cần hiểu

- Tổng quan theo dự án cho lãnh đạo.
- Hợp đồng và tiến độ theo từng hạng mục.
- Sản lượng, nghiệm thu, hóa đơn và thanh toán.
- Công nợ phải thu và phải trả.
- Tổng hợp thầu phụ, khoán nội bộ và khoán còn lại.
- Cảnh báo thanh toán vượt nghiệm thu, chưa nghiệm thu và vượt khoán.

## Câu hỏi cần hỏi Phòng Kế hoạch

1. Mẫu v10_5 đang được dùng đầy đủ hay chỉ dùng một phần?
2. Những cột nào là bắt buộc trong công việc thực tế?
3. Ai được nhập Form A và Form B? Ai duyệt?
4. Có cần giữ toàn bộ lịch sử sửa/hủy như file hiện tại không?
5. Phòng Kế toán ghép dữ liệu bằng mã dự án và quy ước nào?
6. File tổng hợp hiện chạy bằng công cụ nào, ai xử lý khi lỗi?
7. Tài liệu lưu ở NAS hay hệ thống khác? Ai được xem?
8. Báo cáo nào lãnh đạo thực sự sử dụng?
9. Luồng nào nên làm MVP đầu tiên?
10. Dữ liệu cũ có cần chuyển vào hệ thống mới không?
