# ADMIN-ACCOUNT-POLICY-001 — Quản lý tài khoản admin

Ngày 19/11/2026. Yêu cầu trực tiếp trong tệp người dùng đính kèm; DEC-062 thay quy tắc thu hồi admin trước khi khóa. Phiên chính được giao triển khai hạng mục này.

## Hành vi

- Admin gốc khóa/mở và quản lý tài khoản admin ủy quyền theo chức năng hiện có, giữ bảo vệ tài khoản hệ thống/chính mình và admin gốc cuối cùng.
- Admin ủy quyền A chỉ đọc tài khoản/hồ sơ của admin ủy quyền B, kể cả khi B đã khóa. Chỉ admin gốc cấp/thu hồi admin. A tiếp tục quản trị nghiệp vụ và nhân viên thường theo quyền hiện hành.
- Backend kiểm người thực hiện thực tế, không lấy quyền từ `sudo` hoặc context client. Cùng helper phân loại admin gốc, admin ủy quyền và nhân viên cho capability và guard.
- Guard kiểm cả user, employee, partner, resource, phiên bản HR, liên kết trực tiếp/default/commands, unlink/archive và batch. Hồ sơ tương ứng được bảo vệ; tham chiếu trong dự án/thiết bị/báo cáo không làm nghiệp vụ bị khóa theo.
- UI có loại tài khoản rõ ràng; peer profile chỉ đọc và giải thích: “Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.” Đổi tên đăng nhập, khóa/mở/reset/sửa hồ sơ không hiện cho peer.
- Khóa dùng `active`, `tp_hr_locked`, `tp_lock_revision` hiện có. Session cũ không được khôi phục sau mở khóa. Không sửa sổ cấp quyền; mở lại giữ grant còn hiệu lực, không tạo grant mới.
- Nhật ký append-only có actor, target, thời gian, lý do và trước/sau phù hợp. Chỉ metadata cho credential/avatar, không lưu mật khẩu hoặc token.

## Phạm vi và nghiệm thu

Phiên bản đã kiểm: `tp_admin_delegation` **20.0.2.1.0**, `tp_hr_workspace` **20.0.1.16.0**. Không đổi API/React/core Odoo. Không tạo bảng nghiệp vụ mới; bộ lọc không đổi, form/popup là N/A, audit dùng model và search hiện có.

Test thực hiện trên `tp_tanphat_test` hiện có sau backup tại `.local/admin-account-policy001/test-backup-20261119T143137`. Backup gồm dump custom đã đọc bằng pg_restore-list, filestore được DB tham chiếu + manifest SHA256, source/config; không sao tệp GC dư không được DB tham chiếu. Tài khoản thử có tiền tố Synthetic, rollback sau test; không khóa/reset/cấp quyền người thật.

Kết quả kiểm thực, commit và receipt triển khai được bổ sung sau khi chạy. Technical verification, nghiệm thu hình thức/nghiệp vụ và pilot authorization là các kết luận riêng. Không tuyên bố authenticated public E2E bằng người thật hoặc iOS/Safari thật nếu chưa chạy.

## Kết quả kiểm thực

Odoo 40/40 PASS, 0 failed / 0 errors (tests-5.log): toàn addon admin delegation, login rename backend/HTTP/browser và account-role regression. Tag mới gồm 7 TransactionCase + 2 HttpCase; kiểm lock/unlock ledger/groups không đổi, audit reason/actor/target/revision, phiên cũ bị từ chối, login mới khóa có thông báo và mở lại đăng nhập được; peer writes mọi trường/sudo/context/inactive/bulk/profile/contact/resource/hr.version/link/unlink bị chặn; ordinary management/self service và original-only grant/revoke giữ.

Race 2/2 PASS (race.log), PostgreSQL hai giao dịch độc lập: rename+rename và create+rename cùng login có đúng một winner; fixture đã cleanup. Lệnh python -m scripts.tests.test_hr_login_rename_race --config .local/admin-account-policy001/runtime-test.conf; không chạy trên main/server.

Playwright 1440x900 và 390x844 PASS: original khóa/mở qua lý do + xác nhận, trạng thái DB/reload đúng và 3 nhãn loại tài khoản; peer employee profile và native res.users chỉ đọc, không rename/reset/lock/edit/menu thao tác, 0 pageerror. Hồi quy rename dialog/unique/inline/cancel/save/reload/mobile PASS. Screenshot/result ignored .local/admin-account-policy/browser và .local/hr-login-rename-impl001/browser.

Ruff, AST Python, XML parse, Node syntax và scoped git diff --check PASS. Review chéo phát hiện/sửa self-rule áp rộng nhầm ordinary HR và menu mobile native vẫn hiện; khóa target dùng exclusive advisory theo namespace grant, không đổi scope revision. Các lần đầu lỗi fixture cookie/HR role/sequence/config API và selector icon đã sửa, không giảm guard để làm test xanh. Chưa authenticated public E2E bằng người thật/iOS/Safari thật; không khóa/reset/cấp quyền người thật. Kiểm kỹ thuật không thay nghiệm thu nghiệp vụ.
