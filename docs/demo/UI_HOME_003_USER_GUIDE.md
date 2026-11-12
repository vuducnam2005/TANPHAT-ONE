# UI-HOME-003 — Dùng Trang chủ TANPHAT ONE (KH-KD trước)

Ngày 07/11/2026. [Kết quả kiểm thử và trạng thái áp dụng](UI_HOME_003_ACCEPTANCE.md) ·
[Thiết kế](../ui/UI_HOME_003_DESIGN.md).

Trang chủ giờ là trang vào việc ngắn: một workspace, ba công cụ cá nhân và, chỉ với quản trị
hệ thống, một khu quản trị. Ứng dụng khác vẫn còn nguyên quyền và mở từ trình chuyển ứng dụng
của Odoo.

## Ba khu

| Khu | Gồm | Ai thấy |
| --- | --- | --- |
| Không gian làm việc | **Kế hoạch Kinh doanh** — vào hồ sơ, kế hoạch và Tổng quan KH-KD | Tài khoản có menu KH-KD |
| Công cụ cá nhân | Việc cá nhân, Lịch làm việc, Trao đổi | Theo quyền từng ứng dụng |
| Quản trị hệ thống | Tất cả ứng dụng, Cài đặt, Quản lý ứng dụng | Chỉ tài khoản thuộc nhóm Quản trị hệ thống (Settings) |

Khu không có mục nào sẽ ẩn. Trang chủ không có lưới "Ứng dụng nghiệp vụ", không có ô "sắp ra
mắt", không có KPI và không có Nhân sự/Hóa đơn trong KH-KD. Phòng ban khác chưa có workspace.

## Mở ứng dụng khác

- **Máy tính:** bấm nút lưới ứng dụng ở góc trái thanh trên cùng, chọn CRM, Dự án, TP Projects,
  TP Contracts, Nhân sự, Hóa đơn… Danh sách này là của Odoo, đã lọc theo quyền.
- **Điện thoại:** bấm ☰ → **Tất cả ứng dụng** (All Apps nếu giao diện tiếng Anh) → chọn ứng dụng.
- Dòng ghi chú cuối Trang chủ nhắc cách này khi tài khoản có ứng dụng ngoài Trang chủ.
- Quản trị hệ thống còn có **Tất cả ứng dụng** ngay trên Trang chủ: bảng liệt kê đúng các ứng
  dụng tài khoản được cấp, có ô tìm riêng. Escape lần đầu xóa từ khóa, lần hai đóng bảng.

## Kiểm tra nhanh trong 7 bước

1. Mở `http://127.0.0.1:18069/odoo/tp-home`, đăng nhập bằng tài khoản hiện có; Ctrl+F5 nếu còn
   bố cục cũ (lưới Ứng dụng nghiệp vụ).
2. Nếu có quyền KH-KD, bấm thẻ **Kế hoạch Kinh doanh**; kiểm tra sidebar và Tổng quan. Bấm biểu
   tượng ngôi nhà trên thanh trên cùng để trở lại.
3. Mở lần lượt Việc cá nhân, Lịch làm việc, Trao đổi; mỗi mục mở đúng ứng dụng native.
4. Tìm `khkd`, `ke hoach`, `lich`, `chat`, `todo` (có hay không dấu đều được). Enter mở kết quả
   đầu. Escape hoặc nút × trả lại toàn bộ Trang chủ. Từ khóa của ứng dụng không nằm trên Trang
   chủ (ví dụ `hoa don`) sẽ báo **Không có lối vào phù hợp trên Trang chủ** — hãy dùng trình chuyển ứng dụng.
5. Mở một ứng dụng khác bằng trình chuyển ứng dụng (máy tính) hoặc ☰ → Tất cả ứng dụng (điện thoại).
6. Tab/Enter mở mục; Ctrl/Cmd-click hoặc chuột giữa mở tab mới. Back/Forward, tải lại và nút
   Home vẫn theo Odoo. Home Action riêng của tài khoản vẫn có hiệu lực khi mở `/odoo`.
7. Nếu thấy **Chưa tải được Trang chủ**, kiểm tra kết nối rồi bấm **Thử lại**. Đây
   là lỗi tải menu, khác với tài khoản không có mục nào hoặc từ khóa không có kết quả.

## Lưu ý

- Dữ liệu, menu, quyền và Home Action được giữ nguyên; Trang chủ không cấp thêm quyền. Ẩn khỏi
  Trang chủ không phải là thu quyền: server vẫn lọc mọi menu và bản ghi.
- Khu Quản trị hệ thống theo nhóm Quản trị hệ thống (`base.group_system`), không theo tên đăng
  nhập. Người chỉ có quyền Access Rights vẫn mở Cài đặt từ trình chuyển ứng dụng.
- Form chưa hợp lệ/chưa lưu vẫn do Odoo kiểm tra trước khi rời.
- Hỗ trợ màn hình 360–1920 px và phóng to 125%/150%; mô phỏng Chromium không thay kiểm trên mọi
  thiết bị thật.
