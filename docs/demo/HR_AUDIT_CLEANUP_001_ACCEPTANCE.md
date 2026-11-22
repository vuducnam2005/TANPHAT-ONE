# HR-AUDIT-CLEANUP-001

Ngày 22/11/2026. Trạng thái: đã kiểm local test và áp PC server ngày22/11/2026.

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


## Receipt PC server — CHG-20261122-002

SSH mới PAC-PC/Admin đã xác minh fingerprint và đăng nhập được. Commit `76d2d504` push/deploy; 15 tệp khớp SHA256; upgrade HR20.0.1.22.0 exit0/log0. Backup tại `C:\TANPHAT-backups\audit-cleanup001\audit-cleanup001-20261122T211031`; pg_restore list16.313 dòng, filestore638 mục.

Fingerprint tài khoản/quyền/nhân viên/thiết bị/công/audit không đổi. Probe6/6 PASS:83/83 audit active,24 lý do kỹ thuật được diễn giải; wizard password store=False, bulk action và cột đúng. Không tự gỡ bất kỳ dòng thật. Public health200; JS/CSS actual bundle có tiêu đề/hướng dẫn mới. Không đăng nhập đè phiên admin thật.

Người dùng: mở `/app/nhan-su/nhat-ky-ho-so`, chọn dòng → Tác vụ → Xóa nhật ký khỏi danh sách → nhập mật khẩu của mình. Đây là gỡ khỏi danh sách, không xóa vật lý bằng chứng mã đã dùng.
