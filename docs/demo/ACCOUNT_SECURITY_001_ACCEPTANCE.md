# ACCOUNT-SECURITY-001 — Kiểm chứng tài khoản và bảo mật

Ngày 21/11/2026. Phạm vi: source native, các vai trò nhân viên/admin ủy quyền/admin gốc; dữ liệu thử ở tp_tanphat_test. Không thay credential/2FA/khóa của tài khoản thật.

## Thay đổi

- `/app/tai-khoan/bao-mat`: workspace sáng, desktop/mobile; cùng dữ liệu tài khoản, không phụ thuộc có hồ sơ nhân viên.
- Mật khẩu/TOTP/passkey/API key gọi action native với check_identity; không triển khai thuật toán xác thực riêng.
- Endpoint self-service chỉ nhận danh tính từ session; giới hạn trường trả về, không trả session identifier, nonce, secret/key.
- Backend chặn thu hồi phiên, xóa trực tiếp API key/trusted device và sửa/xóa/chuyển chủ passkey của peer-admin/admin gốc. Admin gốc giữ quyền theo chính sách hiện hành.
- Lịch sử phiên phân trang/lọc theo owner, không suy 154 bản ghi là 154 phiên còn hoạt động. Không xóa lịch sử để giảm số.
- Tùy chọn cá nhân có ảnh/ngôn ngữ/múi giờ; ảnh của nhân viên đi qua API hồ sơ dùng chung.

## Kiểm đã chạy

- `.local/account-security001/tests-release.log`: 42 tests, 0 failed, 0 errors (tp_admin_delegation và TestBrandUrls).
- `.local/account-security001/browser-result.json`: 8 tình huống trình duyệt thực, 0 pageErrors; ảnh desktop/mobile nằm trong cùng thư mục ignored.
- Ruff mới, AST/XML và build asset qua Odoo PASS.
- Test negative bao gồm đổi ID, quyền peer-admin, sudo nội bộ không biến actor, privilege injection, session revoke trước side effect, passkey unlink/write/owner, API unlink.

## Giới hạn cần nói rõ

- Không thử sinh trắc học trên phần cứng thật của người dùng.
- Không tự bật 2FA hoặc thay mật khẩu thật trên server. Admin gốc hiện chưa bật 2FA.
- Không xác định được chủ đích khóa API tên log chỉ từ metadata; giữ nguyên.
- Hai HttpCase login cũ gặp lỗi TestCursor read-only ở đường xác minh winner; kiểm single-session thực ngoài HttpCase đã PASS. Không gọi toàn bộ suite login là PASS.
- Đã kiểm bật/tắt TOTP, đăng nhập bằng mã thật và tạo/thu hồi API key cho nhân viên và admin ủy quyền ở DB test (extended-result.json: 8/8). Không phải pentest toàn hệ thống; chưa có bằng chứng cho thấy các điểm quyền tìm được đã bị khai thác.

## Triển khai

Bản chức năng `2bad1f45` đã áp PC server; nâng 5 module đúng phiên bản, 0 lỗi upgrade, 34 tệp khớp checksum. Backup: `C:\TANPHAT-backups\account-security001\account-security004-20261121T132517`, DB dump 10.650.657 bytes và filestore 36.756.042 bytes; kiểm danh sách restore 16.313 dòng.

Fingerprint trước/sau cho tài khoản, credential, quyền, ledger, nhân sự, thiết bị, đề xuất và công giữ nguyên. Chỉ chuẩn hóa URL công khai sang HTTPS và freeze. Probe ORM chỉ đọc đủ 30 tài khoản nội bộ, gồm 1 gốc, 4 ủy quyền, 25 nhân viên/hệ thống: 0 lỗi. Public health 200. 2FA của admin gốc chưa bật; không tự thay đổi.

Icon SVG và browser bản cuối đã kiểm trên DB test. Static `3461a34a` đã đồng bộ 6/6 tệp checksum khớp; bundle public JS/CSS đã tải và xác nhận workspace/security action mới. Health200, login200, deep link bảo mật chuyển đúng login. Hai actor thử đã thu grant và khóa trên DB test. Bộ kiểm này không chứng minh không còn lỗ hổng ngoài phạm vi đã rà soát.

## Bổ sung hoàn thiện (CHG-20261121-007 — `tp_web_login` 20.0.2.2.0, `tp_admin_delegation` 20.0.2.3.0)

- Sửa lỗi bộ lọc phiên `Đã thu hồi` luôn trả 0 bản ghi (truy vấn `res_device_log` khử trùng theo `session_identifier` cho `self.env.uid`, tách rõ **Phiên hiện tại**, **Các phiên còn hiệu lực khác** và **Lịch sử phiên**, không trả `session_identifier`/nonce/cookie/token).
- Bổ sung nhãn vai trò thật từ backend ở Header (`Quản trị gốc`, `Quản trị viên ủy quyền`, `Quản lý nhân sự`, `Nhân viên nội bộ`), avatar 52px có fallback monogram.
- Bổ sung biểu mẫu đổi mật khẩu inline (`tp_change_my_password`) gồm 3 ô nhập, nút hiện/ẩn có `aria-label`/`aria-pressed`, báo lỗi từng trường, gọi native `change_password` dưới `_assert_can_auth` và làm mới `session_token` phiên hiện tại.
- Việt hóa thông báo bật/tắt 2FA, thời hạn tạo khóa API (giữ nguyên quyền theo nhóm), hộp thoại hiển thị khóa API một lần (bỏ snippet tiếng Anh `ODOO_MCP_KEY`), hiển thị trạng thái `Còn hiệu lực` / `Đã hết hạn` và kiểm quyền `api_keys_allowed`.
- Kiểm thử: `/tp_admin_delegation,/tp_branding:TestBrandUrls` **46/46 PASS** (0 failed, 0 error); Playwright v2 **12/12 checks PASS, 0 pageErrors** (desktop 1440px + mobile 390px, không tràn ngang, tôn trọng `prefers-reduced-motion`).
- Triển khai PC Server (`c74460b8`): backup `C:\TANPHAT-backups\account-security002\sec007-20261121T135321`, 12/12 tệp khớp SHA256, upgrade exit `0`, `0 ERROR/CRITICAL`, `DRIFT_COUNT=0`; probe chỉ đọc xác nhận `Quản trị gốc` (284 đã thu hồi / 149 chưa dọn), `Quản trị viên ủy quyền`, `Nhân viên nội bộ` (53 đã thu hồi / 3 chưa dọn); public bundle `8f258d2/web.assets_web.min.js` và `361ddb7/web.assets_web.min.css` đã phục vụ mã/CSS mới trên `https://tpone.tadic.vn`.
