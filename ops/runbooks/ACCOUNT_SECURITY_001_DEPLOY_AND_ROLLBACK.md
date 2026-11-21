# ACCOUNT-SECURITY-001 — Triển khai và phục hồi

Phạm vi: `tp_web_login` 20.0.2.1.0, `tp_web_home` 20.0.1.11.1, `tp_hr_workspace` 20.0.1.21.1, `tp_admin_delegation` 20.0.2.2.0, `tp_branding` 20.0.2.2.1. Chỉ gói các tệp thuộc batch, giữ phần reporting/sidebar đang dở ngoài release.

1. So SHA256 từng tệp code trên PC server với HEAD nền trước thay đổi. Nếu lệch thì dừng để đối chiếu; không ghi đè source khác.
2. Dừng `tp-odoo`, giữ PostgreSQL và tunnel. Backup DB `tp_tanphat_dev` bằng pg_dump custom; kiểm `pg_restore -l`. Backup filestore, source liên quan và cấu hình vào `C:\TANPHAT-backups\account-security001\<release>-<timestamp>`.
3. Chụp fingerprint tài khoản, mật khẩu đã băm (chỉ hash tổng hợp, không xuất credential), quyền, HR, thiết bị, chấm công và ledger admin trước/sau. Không nhập người giả hoặc đổi credential người thật.
4. Giải nén release từ commit đã push, giữ mtime; so checksum. Upgrade đúng năm module trên bằng container cùng image/network/mount, `--no-http --stop-after-init --max-cron-threads=0`.
5. Sửa `web.base.url` từ HTTP sang `https://tpone.tadic.vn`, `web.base.url.freeze=True` để WebAuthn và liên kết dùng đúng public origin. Không đổi DNS/tunnel; không xóa passkey có sẵn. Lưu cấu hình trước trong backup.
6. Khởi động Odoo, kiểm upgrade log, checksum, version và fingerprint. Kiểm public health/login/route; xác minh asset phục vụ thực tế có template/account-security và CSS mới. Probe ORM chỉ đọc, không đăng nhập đè phiên admin thật.

## Rollback

- Nếu lỗi do asset/source, dừng Odoo, phục hồi các tệp đã ghi đè từ source-config backup; gỡ **chỉ** tệp mới trong manifest dưới đúng workspace đã xác minh; upgrade lại các module về phiên bản source trước rồi khởi động, kiểm route/login.
- Chưa xóa model nghiệp vụ hay di chuyển credential. Không tự restore toàn DB sau khi hệ thống đã nhận dữ liệu mới. Nếu cần phục hồi DB/filestore phải đánh giá dữ liệu phát sinh và dùng đúng cặp backup cùng thời điểm.
- Không tự thu hồi khóa API, bật/tắt TOTP hoặc reset mật khẩu để xử lý lỗi giao diện.

## Phạm vi chứng minh

Health 200 không chứng minh bảo mật. Xem `docs/demo/ACCOUNT_SECURITY_001_ACCEPTANCE.md` và receipt sau triển khai; phân biệt regression test trên DB test, browser thực và probe read-only server.
