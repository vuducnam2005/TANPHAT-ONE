# Tổng quan nhân sự và khóa tài khoản

**Hiện hành từ HR-ACCOUNT-ROLE-001 (12/11/2026):** dùng [hướng dẫn hồ sơ, tài khoản và vai trò](HR_ACCOUNT_ROLE_001_USER_GUIDE.md). Các bước chọn/liên kết/gỡ user và bố cục sáu tab bên dưới là lịch sử, đã được thay thế. Tình trạng hiện dùng Mở/Khóa/Chưa có tài khoản.

Cập nhật 12/11/2026 — HR-DASH-002, CHG-20261112-002.
Dashboard đã làm mới trên18069; chức năng khóa tài khoản của CHG010 giữ nguyên.

## Xem tổng quan

Đăng nhập TANPHAT ONE → Quản lý nhân sự → Tổng quan.
Chọn đơn vị, chức vụ và phạm vi hồ sơ (đang quản lý/lưu trữ/tất cả).
“Xóa bộ lọc” về hồ sơ đang quản lý trong công ty hiện hành.

- 5 chỉ số: tổng hồ sơ, đơn vị có nhân viên, đã/chưa liên kết tài khoản,
  hồ sơ thiếu thông tin cơ bản.
- Biểu đồ tròn: phân bố theo đơn vị, chú giải có số và tỷ lệ.
- Biểu đồ thanh: phân bố theo chức vụ; tên chưa khai báo là một nhóm riêng.
- Nội dung dashboard luôn sáng, kể cả khi hệ điều hành/Odoo dùng dark mode.
  Sidebar xanh đậm giống Kinh doanh; mục “Nhân viên” có icon nhóm người phía trước.
  Donut lớn có tổng ở tâm; màu đơn vị giữ nguyên khi lọc/thay thứ tự.
  Di chuột hoặc dùng Tab để xem tên/số/tỷ lệ và làm nổi nhóm tương ứng;
  Escape ẩn tooltip. Enter/Space hoặc chạm mở danh sách của nhóm.
- Thanh chức vụ dùng cùng thang từ0, xếp số hồ sơ giảm dần; trên desktop
  hiện đủ các chức vụ hiện có. Mobile xếp biểu đồ/chú giải thành một cột.
- Bấm chỉ số, biểu đồ, chú giải hoặc tên đơn vị để mở danh sách tương ứng.
  Chỉ số đơn vị cuộn tới bảng tổng hợp. Quay lại giữ bộ lọc.
- Bảng tổng hợp có tìm tên đơn vị và số dòng 10/20/50/100. Tìm trong bảng
  chỉ thu hẹp bảng, không thay các chỉ số hoặc phạm vi xuất.
- “Xuất Excel” xuất toàn bộ hồ sơ theo **ba bộ lọc đầu trang**, kèm tổng hợp
  đơn vị và thời điểm xuất; không chỉ xuất một trang bảng.

Thông tin cơ bản: mã TP, đơn vị và chức vụ nguồn hoặc chức vụ đã khai báo.
Thiếu liên hệ nghĩa là chưa có cả email công việc, điện thoại cơ quan và
di động. Các mục thiếu có thể trùng người; không cộng các mục thành tổng người.
Chưa có tài khoản là bình thường khi nhân viên chưa cần dùng hệ thống.
Mở (xanh lá) và Khóa (đỏ) đều thuộc số **Đã liên kết**, không cộng thêm
vào tổng hồ sơ. **Chưa liên kết** dùng xám và chữ để phân biệt.
Menu “Báo cáo cơ cấu và Excel” tiếp tục mở cùng dashboard này.

## Khóa / mở tài khoản

Chỉ Quản trị viên hệ thống đúng phạm vi công ty:

1. Nhân viên → Danh sách nhân viên → **Xem tài khoản** ở dòng cần xử lý.
2. Nhập **Lý do thao tác**.
3. Bấm **Khóa tài khoản** hoặc **Mở tài khoản**, rồi xác nhận.
4. Kiểm cột **Tình trạng**: **Mở**, **Khóa**, hoặc **Chưa liên kết**.

Khóa giữ hồ sơ nhân viên, liên kết, mật khẩu và nhóm quyền; user chuyển sang
trạng thái vô hiệu của Odoo. Phiên đã mở bị từ chối ở yêu cầu xác thực kế tiếp;
mở lại tài khoản không làm phiên cũ sống lại. Người dùng cần đăng nhập mới.
Lịch sử trên hồ sơ ghi người thao tác, thời điểm và lý do.

Không khóa/mở chính mình, tài khoản gốc/admin/public/template hoặc portal
qua chức năng này. User đa công ty cần admin có phạm vi mọi công ty bị ảnh hưởng.
Hồ sơ lưu trữ là một khái niệm riêng, không tự khóa tài khoản.

Tài khoản bị khóa qua chức năng HR, khi nhập đúng mật khẩu, hiện:
**Tài khoản đã bị khóa, vui lòng gửi phản hồi**.
Sai mật khẩu/tài khoản không tồn tại tiếp tục báo lỗi thông thường.
“Gửi phản hồi” chỉ mở dòng **Tính năng gửi phản hồi đang phát triển**,
chưa gửi đơn, email hoặc tạo yêu cầu.

Không xem được mật khẩu hiện tại; đặt lại mật khẩu vẫn dùng cơ chế Odoo.
Sau nâng cấp bảo vệ phiên, các phiên đăng nhập cũ có thể yêu cầu đăng nhập lại.
