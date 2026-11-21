# PASSKEY-001 — Triển khai và phục hồi

Phạm vi: `tp_web_login` 20.0.2.2.0 → **20.0.2.3.0**, thêm phụ thuộc `auth_passkey` (đã cài trên server). Có thêm test mới trong `tp_admin_delegation`, nhưng module này không cần upgrade. Không đổi schema, quyền, credential hay cấu hình. Chỉ đóng gói tệp của batch; WIP reporting/sidebar/branding/tooling của phiên khác để ngoài release.

1. So SHA256 (chuẩn hóa LF) của từng tệp sẽ ghi đè trên PC server với commit nền `6130456c`. Lệch thì dừng lại để đối chiếu, không ghi đè.
2. Dừng `tp-odoo`; PostgreSQL và tunnel vẫn chạy.
   - Backup DB `tp_tanphat_dev` bằng `pg_dump -F c` và kiểm bằng `pg_restore -l`.
   - Backup filestore, source `tp_web_login`/`tp_admin_delegation` và `docker.odoo.conf` vào `C:\TANPHAT-backups\passkey001\pk001-<timestamp>`.
3. Chụp fingerprint trước và sau (chỉ md5 tổng hợp, không xuất credential): phiên bản module, users/mật khẩu băm, nhóm, nhân viên, API key, passkey (`id, name, create_uid, sign_count`), `web.base.url` và freeze.
4. Giải nén release từ commit đã push, so checksum và đặt lại `LastWriteTime` để asset bundle sinh lại.
   - Chạy `-u tp_web_login` bằng container cùng image/network/mount, với `--no-http --stop-after-init --max-cron-threads=0`.
   - Không cần chạy lại khi chỉ đồng bộ tài liệu.
5. Khởi động `tp-odoo`. Kiểm upgrade log (0 `ERROR`/`CRITICAL`), version và `DRIFT_COUNT=0`.
6. Kiểm public `https://tpone.tadic.vn` (không đăng nhập tài khoản thật):
   - `/web/health` 200.
   - `/dang-nhap` có nút “Đăng nhập bằng khóa truy cập”, gợi ý và vùng thông báo `aria-live`.
   - `POST /auth/passkey/start-auth` trả `rpId=tpone.tadic.vn` và `userVerification=required`.
   - `POST /tp_web_login/passkey/client-event` nhận enum hợp lệ và từ chối enum lạ.
   - Bundle frontend/backend đang phục vụ có mã mới, ví dụ `classList.add("alert","alert-"+tone)` và `tp_passkey_create`.

## Rollback

- Nếu lỗi nằm ở source hoặc asset:
  - Dừng Odoo và khôi phục `custom_addons/tp_web_login`, `custom_addons/tp_admin_delegation/tests` từ `source-pre.tar.gz`.
  - Chỉ xóa các tệp mới có trong manifest: `controllers/passkey.py`, 3 tệp `static/src/js/passkey_*.js`, 2 tệp test passkey.
  - Chạy `-u tp_web_login` về bản 20.0.2.2.0, khởi động lại, kiểm đăng nhập bằng mật khẩu và trang bảo mật.
- Không restore toàn DB chỉ vì lỗi giao diện. Bản phát hành không ghi dữ liệu. Nếu thật sự cần restore DB/filestore, phải đánh giá dữ liệu phát sinh và dùng đúng cặp backup cùng thời điểm.
- Không xóa, thu hồi hay tạo passkey của người dùng thật, không đổi `web.base.url`/RP ID và không tắt kiểm WebAuthn để xử lý sự cố.

## Phạm vi chứng minh

Health 200 hay nút hiển thị chưa chứng minh passkey hoạt động. Bằng chứng luồng phần mềm (virtual authenticator, 3 vai trò) và giới hạn phần cứng thật nằm trong [nghiệm thu](../../docs/demo/PASSKEY_001_ACCEPTANCE.md). Người dùng cần tự kiểm trên thiết bị thật theo mục 5 của tài liệu đó.
