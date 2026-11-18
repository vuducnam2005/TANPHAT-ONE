# Quản trị viên toàn hệ thống (ADMIN-FULL-001) — Hướng dẫn cấp, thu hồi và sử dụng

Cập nhật: 18/11/2026 (`tp_admin_delegation` **20.0.2.0.0**).
Đọc cùng [chính sách bảo mật](../security/ADMIN_DELEGATE_001_POLICY.md), [bản đồ phân quyền](../security/ADMIN_DELEGATE_001_COVERAGE.md) và [nghiệm thu ADMIN-FULL-001](ADMIN_FULL_001_ACCEPTANCE.md).

## 1. Ai được cấp và thu hồi quyền Quản trị viên? (DEC-054)

- **Chỉ Quản trị gốc (`admin` / nhóm `tp_admin_delegation.group_original_admin`)** mới thấy nút và có quyền thực hiện **Cấp quyền quản trị viên** hoặc **Thu hồi quyền quản trị viên**.
- Tài khoản **Quản trị viên toàn hệ thống được cấp** có toàn quyền quản trị nghiệp vụ trên mọi phòng ban nhưng **không được cấp hoặc thu hồi quyền quản trị viên** cho bất kỳ ai (kể cả qua sửa nhóm quyền, import CSV/Excel hay API).

## 2. Cách Cấp quyền Quản trị viên toàn hệ thống

1. Đăng nhập bằng tài khoản **Quản trị gốc**.
2. Mở **Nhân sự (TP HR) → Danh sách nhân viên → chọn hồ sơ nhân viên → tab Tài khoản và phân quyền**.
   *(Lưu ý: nhân viên cần được tạo tài khoản nội bộ đang mở trước khi cấp quyền quản trị).*
3. Tại mục **Quyền quản trị hệ thống**, bấm **Cấp quyền quản trị viên**.
4. Kiểm tra phần **Xem trước phạm vi áp dụng**, nhập **Lý do** và xác nhận danh tính (mật khẩu tài khoản Quản trị gốc đang đăng nhập) khi hộp thoại bảo mật yêu cầu.
5. Sau khi xác nhận:
   - Nhãn quyền đổi sang **`Quản trị viên (toàn hệ thống)`**.
   - Chức vụ và phòng ban ghi trong hồ sơ nhân sự của người đó **được giữ nguyên**.
   - Người nhận cần **đăng nhập lại** (hoặc tải lại phiên sau khi hệ thống tự yêu cầu đăng nhập lại) để nhận đầy đủ giao diện, menu, Cài đặt, Ứng dụng và quyền Quản trị viên toàn hệ thống.

## 3. Cách Thu hồi quyền Quản trị viên

1. Đăng nhập bằng tài khoản **Quản trị gốc**.
2. Mở **Nhân sự (TP HR) → Danh sách nhân viên → chọn hồ sơ đang là Quản trị viên → tab Tài khoản và phân quyền**.
3. Bấm **Thu hồi quyền quản trị viên**, nhập **Lý do** và xác thực lại danh tính.
4. Sau khi xác nhận:
   - Nhóm `Quản trị viên toàn hệ thống` và toàn bộ quyền quản trị kế thừa được gỡ sạch.
   - Các nhóm, vai trò và phân công nghiệp vụ hợp lệ của người đó **được giữ nguyên 100%** (tài khoản vẫn mở để làm việc theo đúng vai trò nhân viên/trưởng phòng hiện có).
   - Mọi phiên đăng nhập và tab trình duyệt đang mở của tài khoản bị thu hồi lập tức hết hiệu lực session quản trị và được kiểm tra lại quyền ngay ở thao tác kế tiếp.
   - Nếu tài khoản còn bất kỳ nguồn nhóm quản trị trực tiếp nào khác, hệ thống sẽ báo rõ để xử lý trước và **không bao giờ báo thu hồi thành công giả**.

## 4. Hướng dẫn đăng nhập lại cho tài khoản đã được nâng quyền sẵn

- Với tài khoản đã có grant hiệu lực từ trước và vừa được nâng cấp tự động lên **Quản trị viên toàn hệ thống** khi triển khai `20.0.2.0.0`:
  1. Mở đường dẫn hệ thống (ví dụ `https://hybrid-send-ready-ballot.trycloudflare.com/dang-nhap`), bấm `Ctrl + F5` nếu đang mở tab cũ.
  2. Đăng nhập lại bằng tên đăng nhập và mật khẩu hiện có của chính mình (mật khẩu không thay đổi).
  3. Kiểm tra Trang chủ, Nhân sự (gồm cả phòng của chính mình), KH-KD, Dự án, Kho thiết bị, Báo cáo, Chấm công, Cài đặt và Ứng dụng.
