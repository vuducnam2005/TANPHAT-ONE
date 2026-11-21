# PASSKEY-001 — Đăng ký và đăng nhập bằng khóa truy cập trên tpone.tadic.vn

Ngày 21/11/2026 (Asia/Saigon). Phạm vi: `tp_web_login` 20.0.2.3.0 (mã), test mới trong `tp_admin_delegation`. Dùng lại WebAuthn native của Odoo (`auth_passkey`, py_webauthn vendored); không tự viết thuật toán xác thực, không nới kiểm origin, RP ID, challenge, chữ ký, bộ đếm hay user verification.

## 1. Bằng chứng ban đầu (server thật, chỉ đọc)

- Cấu hình đúng: `web.base.url=https://tpone.tadic.vn`, freeze bật. `/auth/passkey/start-auth` trả `rpId=tpone.tadic.vn`, `userVerification=required`, timeout 60 s, `allowCredentials` rỗng (khóa discoverable).
- Đăng ký thành công: có một khóa của một tài khoản nội bộ, được tạo bằng luồng native. Bộ đếm `sign_count=0` cho thấy khóa chưa từng đăng nhập thành công.
- Đăng nhập: các phiên ẩn danh mới gọi `POST /auth/passkey/start-auth`, nhiều lần theo cặp cách nhau 1,3–1,6 s. Sau đó **không có `POST /dang-nhap` nào kèm assertion**, tức backend chưa từng nhận kết quả WebAuthn. Phiên của trình duyệt đã đăng ký khóa vẫn đăng nhập suốt thời gian đó, nên các lần thử đến từ cửa sổ, trình duyệt hoặc hồ sơ khác.
- Đường mạng ổn: một POST thử với credential giả qua Cloudflare vẫn đến Odoo và bị từ chối đúng. Trang đăng nhập có `cf-cache-status: DYNAMIC` và `no-cache`; challenge do POST JSON-RPC sinh ra, không bị cache.
- **Kết luận có bằng chứng:** lỗi nằm ở phía trình duyệt, trong khoảng từ `navigator.credentials.get` tới lúc gửi form. JS native nuốt lỗi (`console.error`) nên người dùng thấy "đã quét vân tay" mà không có thông báo gì.
  - Log server không đủ để xác định lý do cụ thể: người dùng hủy, hết thời gian, hay thiết bị/trình quản lý mật khẩu đang dùng không có khóa. Trình duyệt trả chung `NotAllowedError` cho cả ba trường hợp, nên hệ thống không kết luận là "chưa có khóa".
- Backend native hoạt động: với virtual authenticator trên code HEAD, chuỗi đăng ký → đăng xuất → đăng nhập bằng khóa đều thành công.

## 2. Lỗi thật đã sửa

1. **Đăng nhập bằng khóa:** lỗi trình duyệt không còn bị nuốt.
   - Lỗi được phân loại và hiển thị bằng tiếng Việt ngay dưới nút (`aria-live`).
   - Nút có trạng thái đang xử lý, chống bấm đúp (chỉ một `start-auth`) và trở lại bình thường sau lỗi.
   - Gửi sự kiện chẩn đoán `/tp_web_login/passkey/client-event` chỉ với enum trong whitelist. Không gửi challenge, credential hay cookie.
2. **Xác minh danh tính bằng khóa** (trước khi thêm, đổi tên hoặc thu hồi khóa): view của `tp_web_login` từng thay js_class native nên nút “Dùng khóa truy cập” không bao giờ gọi WebAuthn. Nay controller chạy lại nhánh native: `start-auth` → assertion → `run_check`.
3. **Form bị ẩn khi có ≥2 tài khoản ghi nhớ:** form `d-none` từng giấu cả lỗi server lẫn nút khóa truy cập. Nay form luôn hiện khi có lỗi.
4. **Lỗi backend:** thay chuỗi tiếng Anh/kỹ thuật (`Unknown passkey`…) bằng thông điệp tiếng Việt theo nguyên nhân. Payload hỏng không còn gây lỗi 500.
5. **Tài khoản bị khóa:** chỉ báo “Tài khoản đã bị khóa” sau khi assertion hợp lệ. Assertion giả không làm lộ trạng thái khóa.
6. **Cooldown native** (nhiều lần sai từ cùng địa chỉ): giữ nguyên cơ chế, chỉ thêm thông điệp riêng.
7. **Trang Tài khoản & Bảo mật:** danh sách khóa có tên, đổi tên và thu hồi (có hộp xác nhận). Thông báo thành công chỉ hiện sau khi backend xác nhận.
8. **Trang đăng nhập:** nút “Đăng nhập bằng khóa truy cập” và gợi ý “Dùng khóa truy cập đã đăng ký cho tài khoản trên thiết bị hoặc trình quản lý mật khẩu của bạn.” Đăng nhập bằng mật khẩu vẫn giữ nguyên.

Thông điệp backend khi đăng nhập:

| Nguyên nhân | Thông điệp (rút gọn) |
| --- | --- |
| Khóa đã thu hồi, hoặc tạo ở địa chỉ khác | Khóa không còn hiệu lực… đăng nhập bằng mật khẩu rồi đăng ký khóa mới |
| Challenge hết hạn, dùng lại hoặc thiếu | Phiên xác thực đã hết hạn hoặc đã được dùng… bấm lại |
| Origin/RP ID sai (localhost, trycloudflare cũ) | Khóa không khớp với địa chỉ hệ thống hiện tại… |
| Thiết bị không xác minh người dùng (UV) | Thiết bị chưa xác minh được bạn (vân tay/khuôn mặt/PIN) |
| Bộ đếm lùi | Bộ đếm xác thực bất thường… thu hồi và đăng ký lại |
| Nhiều lần sai | Vui lòng chờ ít phút rồi thử lại |
| Chữ ký sai, payload hỏng | Không đăng nhập được bằng khóa này… |

Phía trình duyệt có thông điệp riêng cho: hủy/hết giờ/thiết bị không có khóa (một thông điệp chung, không khẳng định “chưa có khóa”), dừng giữa chừng, sai địa chỉ, thiết bị không đáp ứng, trình duyệt không hỗ trợ, lỗi mạng, lỗi máy chủ. Không còn dòng chung chung “Đăng nhập thất bại”.

## 3. Phân quyền và phiên (đã đọc mã và có test)

- Ghi `sign_count` khi đăng nhập: native chạy `with_user(owner).sudo()`, guard `allow_self` cho phép. Đăng nhập của cả admin ủy quyền và admin gốc đều qua.
- Chủ khóa luôn là người dùng của session: native `make_key` ghi qua `env.user`. ORM bỏ `create_uid` do client gửi; context `default_create_uid`/`create_uid` giả mạo không có tác dụng.
- Trang tài khoản chỉ thao tác trên khóa của chính mình; với khóa người khác trả “Không có quyền thao tác dữ liệu bảo mật này.”
- Admin ủy quyền không xóa, sửa hay chuyển được khóa của admin gốc hoặc admin ủy quyền khác, kể cả qua RPC trực tiếp hoặc `res.users.write`.
  - Admin vẫn thu hồi được khóa của nhân viên trên form người dùng như native; thay đổi này không đụng tới quyền đó.
- Khóa đã thu hồi không đăng nhập được. Tài khoản bị khóa không đăng nhập được bằng khóa.
- Single-session: phiên cũ chỉ bị thay sau khi khóa hợp lệ hoàn tất đăng nhập; lần thử thất bại không làm mất phiên đang dùng.
- Không thêm context Boolean nào nhận từ RPC.
- Cookie phiên native là `HttpOnly`, không đặt `Secure`/`SameSite`; trình duyệt mặc định coi là `Lax`. Cả luồng passkey cùng origin nên không bị ảnh hưởng. Đây là hành vi native, không đổi trong lượt này.

## 4. Kiểm thử đã chạy (DB tách biệt `tp_tanphat_test`, tài khoản thử, origin/RP ID giả lập `https://tpone.tadic.vn`)

- `/tp_web_login`: **18/20 PASS**. Cả 10 test passkey mới (`test_passkey_flow.py`) đều PASS:
  - gợi ý và nút trên trang đăng nhập;
  - đăng ký → đăng nhập → đổi tên → thu hồi → đăng nhập lại bị từ chối;
  - không chọn được chủ khóa khác;
  - từng lỗi riêng: challenge thiếu, challenge dùng lại, origin trycloudflare cũ, RP ID localhost, UV, bộ đếm, chữ ký sai, khóa lạ, 4 payload hỏng; mỗi lỗi không để lại phiên và không đổi bộ đếm;
  - cooldown; tài khoản bị khóa; single-session;
  - lỗi đăng ký và chủ khóa; xác minh danh tính bằng khóa sai; whitelist client-event.
  - 2 test cũ `test_native_login` FAIL. Lỗi đã có từ trước trên HEAD: HttpCase không mở được cursor ghi từ route readonly. Đã tái hiện bằng mã HEAD; không liên quan passkey.
- `/tp_admin_delegation:TestPasskeyRoles` (mới) và `TestAccountSecurity`: **15/15 PASS**.
  - Nhân viên, admin ủy quyền và admin gốc: tự đăng ký, đăng nhập bằng khóa đúng `uid`/vai trò/nhóm quyền như trước, tự thu hồi, sau đó khóa bị từ chối.
  - Admin ủy quyền bị chặn trên khóa của admin gốc, của peer và (qua trang tài khoản) của nhân viên.
- Toàn bộ `/tp_admin_delegation` + `/tp_web_home`: 47/50 PASS, 3 lỗi đều ngoài phạm vi passkey:
  - `TestAdminAccountLockHttp` cần cổng 18079; chạy lại trên 18079: **2/2 PASS**.
  - 2 test `tp_web_home` trên HEAD còn kỳ vọng cũ từ trước BRAND-WHITELABEL-002 (favicon, chuyển hướng `/app/tp-home`). WIP của phiên khác đang sửa; bản phát hành này không đụng tới.
- Lượt chạy lại trên mã phát hành cuối (sau chỉnh ruff, tách helper khóa tài khoản), cùng lệnh `-u tp_web_login` trên cổng 18079:
  - 35 ca, 33 PASS: `TestPasskeyFlow` 10, `TestPasskeyRoles` 2, `TestAccountSecurity` 13, `TestAdminAccountLockHttp` 2, `TestNativeLogin` 6/8.
  - 2 FAIL đúng là 2 test cũ `test_native_login` nêu trên.
  - ruff, cú pháp XML và JS (ES module) đều PASS.
- E2E Playwright + virtual authenticator CDP (`.local/passkey001/e2e.cjs`) cho 3 vai trò: nhân viên 29/29, admin ủy quyền 29/29, admin gốc 27/27, 0 pageErrors.
  - Các bước: đăng ký qua xác minh mật khẩu; đăng xuất; UV=false báo lỗi tiếng Việt, không POST, nút trở lại, phiên khác còn nguyên; bấm đúp chỉ một `start-auth`; đăng nhập đúng `uid`/`is_admin`/`is_system`; phiên cũ bị thay; đổi tên qua hộp xác minh bằng khóa; khóa tài khoản rồi mở khóa (trừ admin gốc); thu hồi; đăng nhập bằng khóa đã thu hồi bị từ chối.

**Giới hạn:** virtual/software authenticator chỉ chứng minh luồng phần mềm, không thay cho sinh trắc học trên phần cứng thật. Chưa thử trên thiết bị thật của người dùng và chưa đụng tới khóa hay tài khoản thật.

## 5. Hướng dẫn kiểm trên thiết bị thật (người dùng tự làm)

Khóa tạo trên `localhost` hoặc trên địa chỉ trycloudflare cũ **không dùng được** trên `https://tpone.tadic.vn`, vì khóa gắn với tên miền. Không cần xóa khóa cũ.

1. Mở đúng `https://tpone.tadic.vn` trên trình duyệt sẽ dùng hằng ngày (Chrome, Edge hoặc Safari bản mới). Đăng nhập bằng **mật khẩu**.
2. Vào **Tài khoản & Bảo mật → Khóa truy cập → Thêm khóa truy cập**, xác minh danh tính, rồi quét vân tay/khuôn mặt/PIN. Chỉ coi là xong khi thấy thông báo xanh “Đã thêm khóa truy cập …” và khóa có trong danh sách.
3. Đăng xuất. Ở trang đăng nhập, bấm **Đăng nhập bằng khóa truy cập** và chọn đúng khóa của tài khoản trong hộp chọn của trình duyệt hoặc trình quản lý mật khẩu.
4. Thành công nghĩa là vào thẳng hệ thống với đúng tên tài khoản. Nếu chỉ quét vân tay xong mà vẫn ở trang đăng nhập, đọc thông báo dưới nút:
   - “Chưa hoàn tất xác thực…”: đã hủy, hết giờ, hoặc thiết bị/trình duyệt/hồ sơ này không lưu khóa. Thử lại trên đúng trình duyệt và hồ sơ đã đăng ký. Cửa sổ ẩn danh hoặc hồ sơ Chrome khác thường không thấy khóa, trừ khi khóa được đồng bộ qua trình quản lý mật khẩu.
   - “Khóa … không còn hiệu lực…”: khóa đã thu hồi hoặc tạo ở địa chỉ khác. Đăng nhập bằng mật khẩu rồi đăng ký khóa mới.
5. Thử thu hồi: trong danh sách khóa, bấm **Thu hồi → Tiếp tục**. Đăng xuất, đăng nhập lại bằng khóa đó: hệ thống phải từ chối với thông báo tiếng Việt.
6. Trên điện thoại: nếu khóa nằm trên máy tính, dùng tùy chọn quét mã QR của trình duyệt (thiết bị khác), hoặc đăng ký thêm một khóa riêng trên điện thoại.

## 6. Triển khai

Xem [runbook](../../ops/runbooks/PASSKEY_001_DEPLOY_AND_ROLLBACK.md). Kết quả triển khai ghi ở mục dưới sau khi áp PC server.
