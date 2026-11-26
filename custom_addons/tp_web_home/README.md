# TANPHAT ONE — Trang chủ (`tp_web_home`)

Addon giao diện Trang chủ native Odoo 20 của **TANPHAT ONE** tại `/app/trang-chu` (`20.0.2.3.0`, `UI-HOME-006`..`UI-HOME-009`).

## Kiến trúc 5 tầng dùng chung một thiết kế cho Admin & Nhân viên

Phụ thuộc manifest được giữ tối giản (`web`, `tp_web_login`) để không phát sinh vòng lặp phụ thuộc. Các phân hệ nghiệp vụ được phát hiện động qua `self.env` trong `models/home_dashboard.py` và kiểm quyền nghiêm ngặt ở backend ở mỗi lần đọc / mở danh sách.

### Hai chế độ xác thực từ Backend (`home_mode`)

1. **Chế độ Quản trị (`home_mode = "admin"`):**
   - Chỉ dành cho **Admin gốc** (`tp_admin_delegation.group_original_admin`) hoặc **Admin được ủy quyền đang có hiệu lực** (`tp.admin.delegation` trạng thái `active` tại công ty đang chọn).
   - Bốn chỉ số điều hành: **Nhân sự**, **Yêu cầu phê duyệt**, **Công việc**, **Tồn kho**.
   - Lưới 10 ô **Ứng dụng theo phòng ban** theo đúng thứ tự ảnh tham chiếu.
   - Hai biểu đồ: **Tình hình công việc** (cột chồng theo phòng ban) và **Tỷ lệ công việc** (Donut theo trạng thái), mặc định kỳ *Trong tháng này*.

2. **Chế độ Nhân viên (`home_mode = "employee"`):**
   - Áp dụng cho toàn bộ tài khoản nội bộ còn lại (bao gồm trưởng phòng / người duyệt nghiệp vụ, vẫn giữ truy cập đầy đủ các ứng dụng được cấp).
   - Tuyệt đối không truy vấn hay trả dữ liệu **Tồn kho** của công ty.
   - Bốn ô thông tin cá nhân thực chất:
     1. **Việc chưa hoàn thành** (`emp_tasks`): đếm distinct `project.task` chưa hoàn thành trong phạm vi cá nhân (tự tạo, dự án, cuộc họp, yêu cầu, trao đổi); việc đã báo xong chờ xác nhận vẫn tính chưa hoàn thành; không suy từ cột Kanban cá nhân.
     2. **Yêu cầu của tôi chờ duyệt** (`emp_requests`): đếm phiếu `tp.request` đã gửi của chính tài khoản đang ở bước chờ phê duyệt (`approval_state = 'pending'`), khử trùng lặp cầu nối điều chỉnh công.
     3. **Lịch hẹn hôm nay** (`emp_calendar`): sự kiện `calendar.event` hôm nay theo múi giờ người dùng mà tài khoản là người chủ trì hoặc tham gia hợp lệ (xử lý sự kiện cả ngày, sự kiện qua nửa đêm và lịch lặp).
     4. **Chấm công hôm nay** (`emp_attendance`): ô trạng thái tái sử dụng `tp.hr.attendance.day._tp_presence` (`Đang làm` / `Đã về` kèm giờ vào–ra thật, `Nghỉ theo lịch`, `Nghỉ đã xác nhận`, `Chưa chấm công`, `Chưa có dữ liệu`, hoặc thông báo rõ khi tài khoản chưa gắn hồ sơ nhân viên).
   - Lưới **Ứng dụng của bạn**: tổng hợp tự động các phân hệ hằng ngày được cấp quyền (`Nhân sự`, `Chấm công`, `Yêu cầu phê duyệt`, `Báo cáo`, `Việc cá nhân`, `Lịch làm việc`, `Trao đổi`, không gian phòng ban…), dồn gọn không tạo ô trống giả.
   - Hai biểu đồ cá nhân: **Công việc của tôi theo ngày** (mặc định *Trong tuần này*, việc chưa đặt hạn tách riêng cột *Chưa đặt hạn*) và **Tỷ lệ công việc của tôi** (Donut tổng cả hoàn thành và chưa hoàn thành trong kỳ).

### Tỷ lệ hiển thị trọn 1 màn hình Desktop

Trên màn hình Desktop (`>= 1201 × 650`), bố cục CSS Grid tự động cân đối kích thước nút, thẻ và biểu đồ (`clamp(...)` theo `vh`/`vw`) để cả 5 tầng hiển thị trọn vẹn trong một khung nhìn mà không cần cuộn dọc trang.
