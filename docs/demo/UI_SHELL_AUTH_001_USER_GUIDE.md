# Navbar và đăng nhập TANPHAT ONE

UI-SHELL-AUTH-001 / CHG-20261109-002. Địa chỉ dev:
<http://127.0.0.1:18069>. Dùng tài khoản đã được cấp; mật khẩu nằm ở hướng dẫn
private hiện có, không có trong tài liệu này. Kết quả triển khai xem
[acceptance](UI_SHELL_AUTH_001_ACCEPTANCE.md).

1. Mở Trang chủ, nhấn Ctrl+F5 nếu trình duyệt còn cache. Navbar navy có nút
   ứng dụng ở trái, TANPHAT ONE, tên không gian hiện tại; Home, tin nhắn,
   hoạt động, công ty theo quyền và tài khoản ở phải. Nút Home về trang chủ
   qua action native. Tên dài có tooltip; menu mục dài vẫn vào More native.
2. Nhấn avatar/tên tài khoản, chọn **Đăng xuất** ở cuối. Đợi trang xác thực
   xuất hiện. Trên điện thoại, avatar mở menu native; chọn đăng xuất tại đó.
   Nếu có hồ sơ đang sửa, xử lý cảnh báo chưa lưu trước khi chuyển trang.
3. Nếu có tài khoản đã dùng, chọn một hàng rồi nhập mật khẩu. **Bỏ khỏi thiết
   bị này** chỉ bỏ một mục ghi nhớ trên trình duyệt. **Dùng tài khoản khác**
   mở form trống. Có thể dùng Enter, paste/autofill và nút hiện/ẩn mật khẩu.
   Nếu được yêu cầu mã xác thực, dùng ứng dụng xác thực của mình; Hủy về login.
   Passkey, signup/reset chỉ theo chức năng và chính sách hiện có.
4. Mở KH-KD, kiểm Tổng quan, một danh sách và một hồ sơ được cấp. Menu bên
   trái có thể mở/thu; Tài khoản và Tùy chọn hiển thị ở cuối giữ nguyên.
   Không nhìn thấy một mục do quyền không phải lý do để tự cấp thêm quyền.
5. Thử ở điện thoại hoặc cửa sổ hẹp: form một cột, navbar gọn, Menu KH-KD
   mở drawer; Escape đóng và trả focus. Có thể tăng zoom, dùng Tab/Enter và
   tùy chọn giảm chuyển động của hệ điều hành.

## Phạm vi và khôi phục

Thay navbar và auth native trong hai addon Home/Login. Không đổi account,
hash mật khẩu, company, Home Action, grant, assignment, dữ liệu nghiệp vụ,
trusted device/captcha/list_db/cookie hoặc chính sách signup/reset. Không thay
API contract, React legacy, BASE/ký/hiệu lực/thanh toán/pilot.

Evidence, backup DB+filestore+source/config và owner nằm ignored tại
`.local/ui-shell-auth001/`. Rollback chỉ áp delta UI sau khi đối chiếu writer:
dừng đúng Odoo dev; giữ PostgreSQL; gỡ riêng Login mới cài (không model nghiệp
vụ, từ chối nếu có addon installed phụ thuộc); khôi phục hai addon từ snapshot
và upgrade riêng Home. Helper: `.venv/Scripts/python.exe -X utf8
scripts/ui_shell_auth001.py rollback --target dev`. Helper từ chối nếu source
khác seal; đối chiếu writer/delta trước khi gọi. Không chạy lại data policy
AUTH-002 cũ, không uninstall dependency hoặc restore cả DB đè thay đổi khác.
Sau rollback phải so config/quyền/account/business/blob và smoke native
login/logout lại. Chỉ thực hiện khi apply/smoke lỗi, có journal và đối chiếu.
Lượt triển khai không diễn tập rollback dev nếu không cần.

Tự kiểm kỹ thuật không thay người dùng chấp nhận hình thức, audit độc lập hoặc
nghiệm thu nghiệp vụ. Mobile trên Chromium là mô phỏng, không là thiết bị thật.

Bản hiện hành đã áp dev18069: Home20.0.1.4.0/Login20.0.1.1.0.
[Xem ảnh trước–sau](../../.local/ui-shell-auth001/comparison/index.html).
Trên mobile, avatar mở menu tài khoản dạng drawer native. Backup cuối đã giữ
ảnh đại diện được thay bởi một phiên khác trong lúc kiểm; rollback phải giữ
thay đổi đồng thời đó. Không restore cả DB để lùi một thay đổi giao diện.
