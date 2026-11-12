# HR-UI-002 — Thiết kế hồ sơ nhân viên và tài khoản

Ngày 11/11/2026 (Asia/Saigon). Trạng thái `PROMPT_READY_NOT_IMPLEMENTED`.
[Prompt triển khai](../prompts/CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md).

## Căn cứ và kết quả mong muốn

Ảnh người dùng: hồ sơ HR có ảnh đại diện lớn, banner nhiều chữ, Payroll đứng
trước, Lịch trình/Giờ làm việc và chatter chiếm nhiều chiều ngang; mã TP/phòng
ban/tên tách rời. Source hiện có cột `user_id`, form kế thừa native và thông
báo nguồn; chưa có bố cục mới hoặc khu vực reset mật khẩu theo yêu cầu này.
Source/runtime đã kiểm chỉ đọc; không phải audit độc lập toàn HR-001.

Quyết định bố cục: lấy **hồ sơ nhân viên** làm trọng tâm, thông tin nhận diện
cùng một header; tác vụ tài khoản là nhóm riêng, chatter hỗ trợ ở dưới.
Không thêm KPI/cards/trang trí vào từng hồ sơ, không làm lại dashboard HR.

## Tokens và bố cục

- Giữ font hệ thống đang có, hỗ trợ tiếng Việt; body 14–16px, label 13–14px,
  tên nhân viên 24–28px/semibold; căn trái, label gần dữ liệu.
- Navy `#17324D`: header/tiêu đề; teal `#087F8C`: tác vụ chính; ink `#233549`:
  chữ; nền `#F5F7FA`; line `#DCE3EB`; amber `#9A6700`: chờ đối chiếu.
  Account active dùng semantic success sẵn có và nhãn, không chỉ dựa màu.
- Grid 8/12/16/24px. Avatar 72–88px; hai cột nội dung trên desktop, một cột
  mobile; bảng và tabs cuộn trong vùng của chúng khi cần.
- Chuyển tab/panel/dialog 150–220ms; hover nhẹ và focus rõ; tắt chuyển động
  khi giảm motion. Không animate toàn bộ nội dung mỗi lần đổi field.

```text
Sidebar | Hồ sơ nhân viên / <Tên>              <tác vụ native>
        | [Ảnh] Họ và tên             [Đang quản lý]
        |       Mã TP | Đơn vị | Chức vụ
        | Tổng quan | Công việc | Cá nhân | Hồ sơ | Tài khoản | Nguồn
        | -----------------------------------------------
        | Thông tin công việc      | Liên hệ
        | Đơn vị, chức danh        | Email, điện thoại
        | Quản lý đã khai báo      | Địa điểm có dữ liệu
        | -----------------------------------------------
        | Tài khoản: <login/chưa liên kết>  [Xem tài khoản]
        | [Thông tin cần bổ sung: xem chi tiết]
        | Trao đổi và lịch sử                         [Mở]
```

Form Cá nhân, tài liệu, lương giữ quyền hiện hành. Không đưa thông tin riêng
tư vào tab tổng quan hoặc account summary để bù khoảng trống. Các field chưa
được xác nhận giữ knownness; banner gọn không đồng nghĩa xóa cảnh báo nguồn.

## Tài khoản và phòng ban

Tên đăng nhập lấy `res.users.login` qua `hr.employee.user_id` hiện hữu, không
thay bằng display_name. Native link qua `resource.resource.user_id`, unique
theo user/company. Phòng ban dựa employee/version hiện hành; không có bản
phòng ban nhập tay khác trên user. Hiển thị đơn vị không quyết định quyền.

Dialog tài khoản: họ tên/mã TP/đơn vị/login/trạng thái, tác vụ liên kết cho
admin và reset mật khẩu qua wizard native có xác thực lại. HR manager không
tự thành quản trị tài khoản. Chưa có bằng chứng nối alias thì giữ pending.
Không mass provision user hoặc đổi quyền/grant khi đổi phòng ban/link.

Mật khẩu Odoo lưu hash. **Không xem được mật khẩu hiện tại**, không tạo field
lưu bản rõ. Đặt lại mật khẩu là thao tác thay thế phù hợp; hiện/ẩn chỉ dành
cho nội dung mới đang nhập. Giữ ACL, password policy, check_identity và session
native. Không mở endpoint reset `sudo` hoặc ghi bí mật vào lịch sử/export.

## Phạm vi bỏ giờ làm và giới hạn triển khai

Ẩn mục Giờ làm việc và nhóm Lịch trình rỗng trong form TP HR, giữ field,
calendar và logic native. Chatter thu gọn nhưng giữ đủ lịch sử/tệp/hoạt động.
Việt hóa phần tùy chỉnh, không xóa dữ liệu chatter cũ. Giữ một navbar/sidebar
và scope stylesheet HR; mọi entry vào hồ sơ dùng cùng bố cục được kiểm.

Phiên hiện tại chỉ soạn thiết kế/prompt và cập nhật handoff. Chưa thay ứng
dụng, mật khẩu, liên kết tài khoản, quyền hoặc dữ liệu main/test. Test18079
và main18069 đang lắng nghe khi kiểm; không boot/upgrade/restore trong lượt này.
Claude được giao prompt sẽ test trước, backup/restore rồi áp đúng source lên
main; không đổi mật khẩu người thật để demo và không tự suy danh tính alias.

