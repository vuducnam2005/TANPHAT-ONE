# Danh tính và chuyển phòng ban

Admin mở **TP HR → Nhân viên → hồ sơ → Thông tin công việc → Chuyển phòng ban**.
Chọn phòng đích, vai trò, chức vụ nếu cần, nhập lý do rồi **Xem trước thay đổi**.
Rà phòng cũ/mới, các quyền thu hồi, phân công/grant/CRM và việc cần bàn giao.
Xác nhận bàn giao sau khi đã xử lý các mục được liệt kê; hệ thống không đổi hàng
loạt người phụ trách. Bấm **Xác nhận chuyển phòng ban** một lần. Nếu bản xem trước
hết hiệu lực, mở lại để kiểm dữ liệu mới. Hủy không chuyển phòng.

Mặc định vào KH-KD là nhân viên. Workspace chỉ là cửa vào; dữ liệu theo phân công
và grant riêng. Không có phân công thì danh sách rỗng; không tự có quyền tiền,
HEAD, HR hoặc Settings. Muốn bổ nhiệm HEAD phải chọn rõ; phòng có HEAD đang active
sẽ chặn và báo tên người đang giữ vai trò. Chuyển HEAD ra luôn thu hồi vai trò cũ.

Mặc định chuyển ra kết thúc mọi phân công, grant nghiệp vụ/dự án và thành viên CRM
đang active trong công ty; giữ bản ghi lịch sử. Chỉ chọn **Giữ kiêm nhiệm đã đối
chiếu** khi toàn bộ quyền cấp riêng được liệt kê vẫn được cho phép. Lựa chọn này
giữ các quyền đã liệt kê và đánh dấu phân công kiêm nhiệm; không giữ HEAD cũ.
Không tự coi grant còn sót là kiêm nhiệm. Quyền quản lý cấp riêng xung đột phải
được giải quyết trước khi chuyển.

Tài khoản, login, mật khẩu và MFA giữ nguyên. Người chưa có tài khoản vẫn chuyển
được; không tự tạo user. Tạo tài khoản riêng sau đó dùng phòng hiện hành. Phiên
đăng nhập cũ hết hiệu lực; người dùng đăng nhập lại để nhận menu mới. Backend kiểm
quyền ở request kế tiếp, không cần xóa cache hoặc restart cho mỗi lần chuyển.

Tên chính thức sửa tại HR; tài khoản/navbar hiển thị cùng tên. Ảnh sửa tại HR
hoặc tùy chọn cá nhân theo quyền native sẽ cập nhật hai chiều. Tại tab **Tài khoản**,
admin dùng **Đối chiếu tên và ảnh** để xem ID/hash/ảnh hai bên. Một phía có ảnh thật
thì giữ ảnh thật đó; hai ảnh thật khác nhau cần chọn rõ rồi xem trước lại. Mapping
không duy nhất hoặc work contact khác partner tài khoản bị chặn để đối chiếu.
Không ghép người cùng tên, đổi login hoặc sửa partner khách hàng.

Email/điện thoại công việc dùng work contact đã xác minh; email cá nhân không
được làm fallback công khai. Phòng/chức vụ dùng phiên bản HR hiện hành. Bản lịch
sử không đổi quyền hiện tại; chuyển có hiệu lực ngay. Tài khoản đa công ty và
phiên bản tương lai khác phòng bị chặn để HR rà riêng, chưa có điều chuyển hẹn ngày.

Sau chuyển, kiểm bằng tài khoản của nhân viên trên môi trường test: home/app
switcher chỉ có phòng được cấp, dữ liệu đúng phân công; URL/RPC/export/tệp cũ
không mở được sau thu hồi. Phòng chưa có nghiệp vụ hiện tên phòng và **Đang phát
triển**. Admin vẫn giữ công cụ quản trị. Không dùng người thật trên main để thử
thăng/hạ/chuyển phòng.

Nguồn/thiết kế: [identity](../architecture/TP_IDENTITY_ORG_001.md).
Kết quả và giới hạn: [acceptance](IDENTITY_ORG_001_ACCEPTANCE.md).
