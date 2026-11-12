# KD-UI-005 — Cơ hội, hồ sơ thầu và hồ sơ dự án

Ngày 07/11/2026. TANPHAT ONE, workspace Kế hoạch Kinh doanh; CHG-20261107-007. Thao tác theo quyền được cấp. Dữ liệu đang thấy trên dev được giữ nguyên.

## Mở bốn màn

Từ [Trang chủ 18069](http://127.0.0.1:18069/odoo/tp-home), chọn **Kế hoạch Kinh doanh**, mở nhóm **Kinh doanh và dự án**. Trên điện thoại, mở **Menu KH-KD** trước.

| Màn | Đường mở | Thao tác chính |
| --- | --- | --- |
| Danh sách cơ hội | [Cơ hội và hồ sơ thầu](http://127.0.0.1:18069/odoo/action-tp_kd_workspace.action_opportunities) | Tìm tên/khách hàng/dự án, lọc tình trạng hoặc hình thức, nhóm, sắp xếp, chọn cột, Thoáng/Gọn, phân trang |
| Chi tiết cơ hội | Bấm một dòng; **Mới** để tạo nếu có quyền | Đọc tên đầy đủ, thông tin khách hàng/dự án và kế hoạch; tab Phạm vi, Checklist hồ sơ, Năng lực sử dụng |
| Danh sách dự án | [Hồ sơ dự án](http://127.0.0.1:18069/odoo/action-tp_kd_workspace.action_projects) | Mã, tên, khách hàng, quản lý và mốc bàn giao; các tùy chọn và Xem nhiệm vụ native |
| Chi tiết dự án | Bấm một dòng; **Mới** theo quyền | Thông tin nhận diện/chủ trì, Phạm vi/đầu ra; Phân công chỉ hiện cho nhóm được cấp |

## Kiểm tra nhanh

1. Ctrl+F5 rồi mở hai danh sách. Chọn **Gọn**, **Thoáng** và một cột phụ; cuộn ngang trong bảng khi cần.
2. Ở danh sách cơ hội, mở bộ lọc **Đang tìm hiểu**, **Đang chuẩn bị** hoặc **Đã khai báo nộp — chưa xác minh**. Có thể nhóm theo tình trạng, hình thức, người phụ trách hoặc dự án.
3. Mở một cơ hội. Khi đang sửa mà tên khách hàng/dự án trong ô bị ngắn, bấm **Đọc tên đầy đủ** bên dưới; dùng Tab rồi Enter cũng mở được. Nút mũi tên của ô vẫn mở hồ sơ liên quan theo quyền.
4. Chuyển ba tab để đọc nội dung. Checklist là văn bản; căn cứ khai báo là ô văn bản ngắn; Năng lực chọn hồ sơ có sẵn trong quyền. Phần liên kết riêng tư không hiển thị cho người không có quyền.
5. Nếu được cấp quyền, dùng Lưu/Hủy native khi sửa. **Chuẩn bị hồ sơ** cần đủ nguồn, phạm vi, hạn và checklist; **Khai báo đã nộp** cần căn cứ. Giao trực tiếp không có bước khai báo nộp thầu. Chữ **chưa xác minh** luôn giữ sau khai báo.
6. Mở một dự án. Ba đường chính là **Cơ hội / thầu**, **Hợp đồng**, **Kế hoạch / WBS**. **Hồ sơ liên quan** chứa bảy đường: giao khoán, sản lượng, nghiệm thu, đề nghị thanh toán, kế hoạch định kỳ, năng lực và nghĩa vụ; mỗi đường giữ phạm vi dự án hiện tại.
7. Thử trên màn hình hẹp hoặc zoom 125/150%. Trong **Tùy chọn hiển thị**, chọn **Giảm chuyển động** nếu muốn. Khi gặp lỗi dữ liệu/quyền, đọc thông báo, giữ form để sửa hoặc Hủy; không dùng đổi tình trạng trực tiếp để bỏ qua bước.

Tự kiểm kỹ thuật và ảnh/log nằm trong [acceptance](KD_UI_005_ACCEPTANCE.md). Audit độc lập, xác nhận nghiệp vụ và cho phép pilot được ghi riêng. Không dùng dữ liệu thật để chạy chuỗi thử tạo/sửa trên dev.
