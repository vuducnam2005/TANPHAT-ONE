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

Bản đầu ở trạng thái release-ready. Receipt sẽ bổ sung sau backup/upgrade và probe read-only server/public.
