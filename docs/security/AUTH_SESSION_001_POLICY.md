# AUTH-SESSION-001 — Chính sách bảo mật và vận hành một phiên đăng nhập

Ngày áp dụng: 18/11/2026 (Asia/Saigon). Quyết định: [DEC-057](../DECISIONS.md).

## 1. Phạm vi và nguyên tắc

- Mỗi tài khoản người dùng (`res.users`) trong cùng một database Odoo chỉ có tối đa **một phiên trình duyệt / PWA đã xác thực hoàn chỉnh đang hoạt động** tại một thời điểm, áp dụng thống nhất cho Quản trị gốc, Quản trị viên toàn hệ thống được cấp và nhân viên nghiệp vụ.
- Nhiều tab trong cùng một hồ sơ trình duyệt (dùng chung cookie `session_id`) là **cùng một phiên** và làm việc song song bình thường. Trình duyệt khác, cửa sổ ẩn danh hoặc thiết bị khác tạo phiên mới; hệ thống xác định theo phiên xác thực ở server, không nhận diện phần cứng vật lý qua IP/MAC/User-Agent.
- Chỉ thay phiên chiến thắng (winner) trong hook native `res.users._after_session_login()` — tức sau khi hoàn tất xác thực mật khẩu/passkey **và** hoàn tất bước MFA/TOTP (nếu tài khoản bật xác thực 2 bước). Nhập sai mật khẩu, sai mã TOTP, hủy giữa chừng MFA, mở tab mới, xoay SID tự động 3 giờ, hoặc xác minh lại mật khẩu quản trị (`res.users.identitycheck`) không thay đổi winner.
- Xác thực tích hợp không dùng phiên trình duyệt (`Authorization: Bearer <API key>` có `request.session.uid is None`, tác vụ cron/CLI không có HTTP session) hoàn toàn độc lập và không bị đăng nhập trình duyệt làm mất quyền.

## 2. Lưu trữ, đồng bộ đa worker và chống tranh chấp

- Bảng SQL nội bộ `tp_user_active_session` (`user_id PRIMARY KEY`, `session_gen BIGINT`, `session_nonce VARCHAR(86)`, `updated_at TIMESTAMP`) lưu trực tiếp trong PostgreSQL của môi trường, tách khỏi ORM field của `res.users` (không thể đọc/sửa/nhập/xuất qua giao diện hoặc RPC, không làm đổi `write_date` hay kích hoạt nhầm guard bảo mật tài khoản).
- Mỗi phiên thắng nhận cặp `(tp_session_gen, tp_session_nonce)` lưu trong tệp session phía server (`request.session`). `tp_session_nonce` (256-bit ngẫu nhiên) và `session_id` không bao giờ xuất hiện trong `session_info`, URL, thông báo bus hay nhật ký. `session_info` chỉ nhận thẻ công khai một chiều `tp_session_tag = HMAC-SHA256(database.secret, (uid, gen))[:32]` để đối chiếu đời phiên ở giao diện.
- **Khóa giao dịch PostgreSQL (`AUTH_SESSION_LOCK_NS = 761157`):**
  - Đăng nhập hoàn tất và đăng xuất của winner dùng khóa độc quyền `pg_advisory_xact_lock(761157, uid)`. Hai lần đăng nhập đồng thời trên nhiều worker được tuần tự hóa chặt chẽ, chỉ để lại đúng một winner sau commit.
  - Các yêu cầu ghi (`not env.cr.readonly`) từ phiên trình duyệt giữ khóa chia sẻ `pg_advisory_xact_lock_shared(761157, uid)` (không chặn các tab cùng phiên) và kiểm tra lại trong `cr.precommit`, bảo đảm thao tác ghi từ phiên cũ không thể commit sau thời điểm phiên mới đã thay thế.
  - Bản `20.0.2.0.1` đọc winner bằng cursor primary mới **sau khi lấy khóa**, kể cả kiểm precommit; không dùng snapshot `REPEATABLE READ` cũ của request. Route chỉ đọc cũng kiểm trên primary mới. Login khóa dòng winner bằng `FOR UPDATE`; snapshot cạnh tranh cũ dùng retry giao dịch native.
  - Nếu giao dịch đăng nhập mới bị rollback, callback `cr.postrollback` khôi phục trạng thái session trên bộ nhớ và thông báo `bus.bus` (gắn với `cr.precommit`/`cr.postcommit`) tự động hủy, giữ nguyên phiên đang dùng.
  - Đăng xuất sử dụng **compare-and-clear** (`WHERE user_id=%s AND session_gen=%s AND session_nonce=%s`): phiên cũ gọi `/web/session/logout` không bao giờ xóa nhầm winner của phiên mới.

## 3. Cutover phiên cũ và phương án Rollback

- Khi nhận nguyên nhân kết thúc phiên, webclient ẩn và điều hướng ngay sang `/tp/session-ended`. Route xác minh tombstone server, trả trang thông báo độc lập `no-store`, một nút Đăng nhập lại về Trang chủ; document cũ và callback/cache/polling được bỏ. `pagehide` ẩn trang trước bfcache, `pageshow.persisted` tải lại qua xác thực backend trước hiển thị.

- **Cutover sau nâng cấp:** các phiên trình duyệt tạo trước thời điểm triển khai chưa có `tp_session_nonce` sẽ được yêu cầu đăng nhập lại đúng một lần với mã nguyên nhân riêng `session_cutover` (*“Hệ thống vừa cập nhật phiên đăng nhập”*), không báo nhầm thành *“đăng nhập ở nơi khác”* và không tự nâng phiên cũ thành winner.
- **Rollback khẩn cấp (nếu cần):**
  1. Dừng dịch vụ `tp-odoo` (hoặc tiến trình `18069`), khôi phục gói mã nguồn `tp_web_login` / `tp_api` từ bản sao lưu trước nâng cấp (`source-config.tar.gz` / `pre-source.zip`).
  2. Chạy nâng cấp lại `-u tp_web_login,tp_api --no-http --stop-after-init --max-cron-threads=0` (bảng phụ `tp_user_active_session` không khóa ngoại ngược vào bảng nghiệp vụ nên hoàn toàn vô hại, hoặc khôi phục từ `tp_tanphat_dev.dump` nếu cần quay lui toàn phần).
  3. Khởi động lại dịch vụ Odoo và kiểm tra `/web/health` + `/dang-nhap` trả `HTTP 200`.
