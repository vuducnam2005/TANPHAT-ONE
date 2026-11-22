# HR-AUDIT-CLEANUP-001

Ngày 22/11/2026. Trạng thái: đã sửa và kiểm local test, chưa áp PC server.

## Giao diện và cách dùng

Trong Nhật ký xóa hồ sơ và sửa mã: chọn các ô đầu dòng → Tác vụ → Xóa nhật ký khỏi danh sách → nhập mật khẩu tài khoản đang đăng nhập → Xóa khỏi danh sách. Trang chi tiết cũng có nút cùng chức năng.

Cột Nội dung/Lý do diễn giải các dòng kỹ thuật cũ theo snapshot (ví dụ Cập nhật phòng ban, ảnh đại diện). Lý do người dùng nhập được giữ nguyên; raw reason/model/id nằm trong dữ liệu kỹ thuật gốc. Một lần sửa có thể tạo nhiều dòng do đồng bộ model; chưa tự gộp/xóa hàng loạt vì có thể làm mất sự kiện độc lập.

## Ngữ nghĩa dữ liệu

Gỡ khỏi danh sách bằng active=False, giữ hidden_by_id/hidden_at; không xóa vật lý audit hoặc tác động nhân viên/tài khoản/thiết bị. Tombstone còn phục vụ giữ mã đã dùng và ngăn import tạo lại nhân viên đã xóa. Import và retry đọc active_test=False; SQL lịch sử mã không đổi.

## Quyền

Admin gốc hoặc admin ủy quyền còn hiệu lực, trong công ty được phép. Nhân viên không được xem/dọn qua endpoint. Truy cập wizard khác actor, thiếu/sai mật khẩu, grant đã thu bị chặn. Không mở quyền unlink/write audit chung. Mật khẩu store=False và chỉ đi qua context hành động native để xác minh mỗi lần; không vào snapshot/audit/git.

## Kiểm đã chạy

- Backend tests-final.log: 7/7 PASS, nội dung dễ đọc/lý do gốc, deny staff/direct-write/unlink, fresh password, tombstone, revoke grant.
- browser-result.json: 5 checks PASS (heading/list, chọn một dòng mở action, wizard mật khẩu, cancel, mobile), 0 pageErrors.
- http-result.json: nhập mật khẩu qua giao diện, xác nhận và backend gỡ đúng dòng synthetic khỏi danh sách PASS.
- Ruff file mới + AST/XML PASS.
- Không thử dọn nhật ký thật trên server.

## Deploy

SSH trực tiếp tới 192.168.1.73 có phản hồi, nhưng mất alias/khóa cũ và authentication bị từ chối. Người dùng đã chạy script cài public key trên PC server; SSH PAC-PC/Admin khôi phục và fingerprint khớp. Chưa backup/upgrade/deploy trên server; không tuyên bố public thay đổi. Khi có kết nối, dùng scope release manifest, backup DB/filestore/source, -u tp_hr_workspace, restart, checksum asset và so audit count/active_count trước-sau (upgrade không tự ẩn dòng).
