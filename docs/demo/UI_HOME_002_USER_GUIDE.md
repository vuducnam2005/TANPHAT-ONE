# UI-HOME-002 — Dùng Trang chủ TANPHAT ONE

Ngày 07/11/2026. [Kết quả kiểm thử và trạng thái áp dụng](UI_HOME_002_ACCEPTANCE.md).

## Bốn khu

| Khu | Dùng khi |
| --- | --- |
| Không gian làm việc | Mở **Kế hoạch Kinh doanh** để vào hồ sơ, kế hoạch và Tổng quan KH-KD. Thẻ chỉ hiện khi tài khoản có menu này. |
| Công việc cá nhân | Mở Việc cá nhân, Lịch làm việc hoặc Trao đổi theo quyền hiện có. |
| Ứng dụng nghiệp vụ | Mở ứng dụng làm việc chung. **TP Projects** là hồ sơ dự án và phân công; **TP Contracts** là hợp đồng và phiên bản hồ sơ; **Công việc dự án** là công việc và tiến độ trong Project native. |
| Quản trị hệ thống | Cài đặt, Ứng dụng Odoo và công cụ quản trị được cấp cho tài khoản. |

Khu không có ứng dụng được phép mở sẽ ẩn. Nhân sự/Hóa đơn là ứng dụng, không tự trở thành workspace phòng ban. Số lượng ô khác nhau theo tài khoản là bình thường; Trang chủ không cấp thêm quyền.

## Kiểm tra nhanh trong 7 bước

1. Mở `http://127.0.0.1:18069/odoo/tp-home`, đăng nhập bằng tài khoản hiện có; Ctrl+F5 nếu còn bố cục cũ.
2. Nếu có quyền KH-KD, bấm thẻ xanh **Kế hoạch Kinh doanh** và kiểm tra sidebar/Tổng quan; bấm biểu tượng ngôi nhà để trở lại.
3. Trong **Ứng dụng nghiệp vụ**, mở lần lượt TP Projects, TP Contracts và Công việc dự án nếu tài khoản có các ô này. Đọc mô tả dưới tên để chọn đúng mục.
4. Tìm `khkd`, `du an`, `project`, `hop dong`, `contracts`, `lich` hoặc `todo`. Kết quả giữ tiêu đề khu; Enter mở kết quả đầu. Escape hoặc nút xóa trả lại toàn bộ ô.
5. Dùng Tab và Enter để mở ô; Ctrl/Cmd-click hoặc chuột giữa mở tab mới. Nút Home, Back/Forward và tải lại vẫn theo điều hướng Odoo. Home Action riêng vẫn có hiệu lực khi mở `/odoo`.
6. Trên điện thoại, cuộn xuống các ứng dụng và quản trị. Trang chủ không tự bật bàn phím. Có thể phóng to 125%/150% trên trình duyệt máy tính.
7. Nếu thấy **Chưa tải được không gian và ứng dụng**, kiểm tra kết nối rồi bấm **Thử lại**. Đây là lỗi tải menu, khác với việc tài khoản không có menu hoặc từ khóa không có kết quả.

## Lưu ý

- Dữ liệu, menu và quyền cũ được giữ. Các màn hợp đồng không tự có thêm ký, hiệu lực hay thanh toán.
- Form chưa hợp lệ/chưa lưu vẫn do Odoo kiểm tra trước khi rời. Không dùng tải lại tab để thay thao tác Lưu/Hủy.
- Ảnh desktop/mobile và giới hạn kiểm chứng nằm trong acceptance; mô phỏng Chromium không thay kiểm trên mọi thiết bị thật.
