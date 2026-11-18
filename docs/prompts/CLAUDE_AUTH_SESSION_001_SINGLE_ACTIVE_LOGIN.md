# AUTH-SESSION-001 — Một phiên đăng nhập hoạt động cho mỗi tài khoản

Làm việc trong `C:\TANPHAT ONE`. Đây là prompt triển khai yêu cầu18/11/2026:
**lần đăng nhập mới thành công thay phiên cũ; máy cũ thông báo đã đăng nhập
ở nơi khác và có nút Đăng nhập lại để đăng nhập rồi về Trang chủ.**

Đọc AGENTS/status/changelog/AI_CHANGE_WORKFLOW, policy giao bản liên tục,
quyết định admin hiện hành, skill tanphat-odoo-delivery/Ponytail nếu có.
Viết acceptance trước sửa code; không đụng phần chấm công hoặc diff đang dở.

## 1. Quy tắc sản phẩm đã yêu cầu và cách thực hiện

- Mỗi user có tối đa **một phiên web/PWA được xác thực hoàn chỉnh đang hợp
  lệ trong cùng môi trường/database**. Áp cả admin gốc, admin được cấp và
  nhân viên; không miễn trừ admin để người dùng có thể dùng chung tài khoản.
- Máy A đăng nhập, máy B đăng nhập thành công cùng tài khoản: B tiếp tục
  vào hệ thống; A hết quyền truy cập ngay sau khi giao dịch đăng nhập B commit.
  A đăng nhập lại thành công thì A thay B theo cùng quy tắc.
- Nhiều tab trong cùng browser profile, cùng session cookie vẫn dùng bình
  thường, không tự đá nhau. Trình duyệt khác/ẩn danh/điện thoại có session
  khác thì coi là đăng nhập mới, kể cả cùng phần cứng. Không tuyên bố phát
  hiện chính xác thiết bị vật lý, không khóa theo IP/MAC/User-Agent/fingerprint.
- Cùng database qua domain public/alias khác vẫn có một nguồn sự thật;
  không tạo winner riêng theo hostname. Dev và PCserver có DB riêng thì
  không gộp tài khoản bằng tên để làm khóa phân tán giữa hai môi trường.
- Chỉ thay winner **sau xác thực hoàn chỉnh**, gồm MFA nếu đang bật. Nhập sai
  mật khẩu/OTP, bỏ ngang MFA, refresh, mở tab, heartbeat, xác minh lại mật
  khẩu admin hoặc chạy cron không thay winner. Tài khoản bị khóa không thể
  lấy lại phiên; khóa/đổi mật khẩu/thu quyền admin vẫn giữ tác dụng native.
- API key/integration máy chấm công/cron không là phiên trình duyệt và không
  bị browser login làm mất tích hợp. Không tự xây API key hoặc cấp ngoại lệ
  qua tham số client; kiểm lại auth flow thực tế và ghi rõ phạm vi triển khai.

## 2. Tái sử dụng source hiện có

Source đã được đọc để viết prompt, phải đối chiếu lại bản mới trước triển khai:

- `custom_addons/tp_web_login/models/res_users.py`: khóa HR,
  `tp_lock_revision`, native credential checks/session-token extension.
- `custom_addons/tp_admin_delegation/models/delegation.py`:
  `tp_admin_scope_revision`, invalidation khi cấp/thu admin. Giữ bản
  ADMIN-FULL-001 và ngoại lệ chỉ admin gốc cấp/thu admin; không đổi quyền.
- `custom_addons/tp_web_home/static/src/identity/identity_service.js`:
  logout native/PWA, identity và menu dùng chung. Dùng một service thông báo
  phiên cho mọi workspace, không patch riêng HR/KH-KD/Kho/Báo cáo.
- `custom_addons/tp_api/models/ir_http.py`: mapping lỗi API hiện trả
  `unauthenticated` cho SessionExpiredException/AccessDenied. Muốn báo đúng
  `session_replaced` phải giữ được nguyên nhân, không map mọi401/403 thành nó.
- Core để tham khảo **chỉ đọc**: `odoo/http/session.py` tách
  `authenticate`/`finalize`; `finalize` sau MFA gọi hook
  `res.users._after_session_login()`. Session cookie có cơ chế xoaySID tự
  động, vì vậy không so sánh nguyênSID cố định rồi đá chính phiên đang dùng.
  Đối chiếu `addons/web/controllers/session.py`, `addons/web/controllers/home.py`,
  `addons/auth_totp/controllers/home.py` và `ir.http` auth trước chọn hook.
- Ưu tiên kế thừa hook/model/action trong addon có trách nhiệm auth hiện có;
  không sửa core, không monkey-patch toàn cục hoặc tạo hệ đăng nhập thứ hai.
  SSO/passkey chỉ bao phủ nếu có trên runtime; ghi điểm vào đã/chưa kiểm.

## 3. Bảo đảm ở backend, hoạt động nhiều worker

- Lưu winner/generation hoặc nonce ngẫu nhiên do server phát ở PostgreSQL
  của user và trong session đã xác thực. Chọn phương án nhỏ nhất theo native
  hook hiện có, không cần database/Redis/service mới nếu chưa cần.
- Token phiên là nội bộ, không phải trường HR được sửa/import/export; client
  không chọn user/winner/generation để giành quyền. Không lộ cookie, rawSID,
  nonce bí mật, mật khẩu hoặc token trong URL/log/notification/session_info.
- Đăng nhập cùng user được tuần tự hóa bằng lock/CAS/transaction đúng phạm
  vi: sau hai login cạnh tranh chỉ một winner đã commit; không hai worker
  cùng giữ quyền hoặc cả hai mất phiên. Nếu login rollback/fail, phiên cũ
  vẫn hợp lệ. Phải xử lý thứ tự commit/cache, không dựa cache Python một worker.
- Kiểm winner trước dispatch action/RPC/read/write/export/upload/download
  dùng session, kể cả request trực tiếp không có JS. Phiên cũ không thể
  tiếp tục sửa/xem dữ liệu bằng cookie cũ, gọi lại RPC hoặc tải file riêng.
  Route công khai chỉ trả phần công khai như native, không biến thành user cũ.
- Không chỉ chặn request bắt đầu sau lần thu hồi: phân tích race với request
  ghi đang chạy. Có cơ chế cùng khóa/thứ tự commit để lệnh từ phiên cũ không
  được commit như còn hợp lệ sau khi phiên mới đã thay thế. Giao dịch đã
  hoàn tất trước cutover giữ nguyên; không hứa thu hồi dữ liệu đã tải từ trước.
- Không tạo re-login vô hạn bởi SID rotation, session-token recompute,
  identity recheck, MFA, PWA hoặc extension admin/HR lock. Dùng `super()` và
  giữ các session-token field hiện hành; refresh/poll không tự giành winner.
- Logout của phiên cũ chỉ dọn phiên/cookie cũ; **không xóa winner của B**.
  Khi logout winner cũng phải compare-and-clear để không xóa winner mới do race.
  Không xóa toàn bộ session file hoặc gọi global reset/password change để đá A.
- Thay winner và thông báo chỉ được phát sau commit; rollback không được
  làm UI phiên A báo bị thay. Thu hồi phiên không thay active/password/groups,
  vai trò HR, quyền phòng ban hoặc dữ liệu nghiệp vụ.
- Session cũ không có generation sau deploy: xác định cutover rõ. Phương án
  tối thiểu là yêu cầu đăng nhập lại một lần với lý do **Hệ thống vừa cập nhật
  phiên đăng nhập**, không giả lý do Đăng nhập ở nơi khác. Không cho legacy
  session tự trở thành winner mỗi lần request hoặc tạo đường miễn trừ lâu dài.

## 4. Thông báo máy cũ và nút Đăng nhập lại

**Thông báo bắt buộc:**

> Tài khoản của bạn đang được đăng nhập ở nơi khác.
> Phiên làm việc trên thiết bị này đã kết thúc. Vui lòng đăng nhập lại để tiếp tục.

Nút chính duy nhất: **Đăng nhập lại**.

- Dùng service OWL/toàn webclient và bus/websocket native đang có để đẩy tới
  **phiên bị thay**, không broadcast rồi đá cả phiên B. Channel kiểm quyền và
  payload tối thiểu; nhận event phải đối chiếu đúng đời phiên, event trễ của
  A không được đá A/B đã đăng nhập lại. Cookie/generation không công khai.
- Backend invalidation có hiệu lực ngay khi B commit. Trong điều kiện online
  bình thường thông báo A hiện trong khoảng1–2giây qua bus. Có kiểm tra nền
  nhẹ3–5giây khi tab đang hiển thị nếu bus không hoạt động; dừng poll tab ẩn,
  backoff khi lỗi, kiểm ngay khi focus/visibility/online. Không hứa máy offline
  nhận thông báo tức thì; khi online/focus lại phải kiểm trước tiếp tục thao tác.
- Nhiều tab cùng session xử lý đồng bộ nhưng mỗi tab chỉ một overlay; không
  popup chồng hoặc gửi logout liên tục. Không tạo nhiều timer/request chồng.
- Overlay/màn hết phiên sáng, gọn, icon cảnh báo, màu phù hợp TANPHAT ONE,
  responsive/focus/keyboard/reduced-motion. Không cho đóng để dùng tiếp, không
  để dữ liệu HR/tài chính còn nhìn phía sau overlay; không chỉ blur CSS.
- Dừng tác vụ frontend/polling/response của phiên cũ, bỏ dữ liệu/query/cache
  nhạy cảm có thể tái dùng của user cũ. Response trễ không được render lại màn
  cũ; không render lại dữ liệu nhạy cảm từ bfcache khi bấm Back/focus/reconnect.
  Giữ cache public an toàn như native, không broad-clear mọi dữ liệu trình duyệt.
- Bấm Đăng nhập lại: dọn đúng phiên cũ theo native, tới **trang đăng nhập
  thương hiệu đang có** trên cùng origin (hiện có `/dang-nhap`, xác minh lại),
  sau thành công vào Trang chủ TANPHAT ONE. Không hardcode domain tunnel,
  không quay về form chỉnh dở, không tự đăng nhập hoặc lưu mật khẩu.
- Form dở không tự lưu khi bị thay; không retry tự động mutation/upload sau
  login và không giữ payload HR nhạy cảm ở localStorage. Thông báo ngắn dữ
  liệu chưa lưu có thể mất nếu cần, không bật vòng dirty-form cản re-login.
- Dùng mã nguyên nhân riêng như `session_replaced`; HTTP native/JSON-RPC/API
  phải giữ contract đúng loại request. Không coi HTTP200 của JSON-RPC error là
  thành công. Mất mạng/timeout/403 thiếu quyền/409/422/500 không được đổi thành
  thông báo Đăng nhập ở nơi khác; khóa tài khoản/hết hạn thường/đổi mật khẩu có
  thông báo đúng nguyên nhân. Không thêm public endpoint tra user hoặc phiên.

## 5. Acceptance và bàn giao

Viết acceptance trước code, gồm backend lẫn hai browser context độc lập:

1. A đăng nhập, B đăng nhập cùng tài khoản: B vào được, A có đúng thông báo
   và nút; cookie cũ của A bị chặn đọc/ghi/file trực tiếp không phụ thuộc JS.
2. A đăng nhập lại bằng nút: về Trang chủ; B bị thay theo đúng cơ chế.
3. Sai mật khẩu/sai OTP/chưa hoàn tấtMFA không đá A; hoàn tấtMFA mới thay.
4. Nhiều tab cùng profile không đá nhau; browser/ẩn danh/điện thoại session
   khác thay nhau đúng; hai user khác nhau không ảnh hưởng nhau.
5. Login đồng thời/multiworker, SID rotation, logout A sau B, B tiếp tục dùng,
   login rollback, request ghi in-flight, event/response đến trễ đều kiểm đúng.
6. Bus mất kết nối/fallback, offline→online, tab ẩn→hiện, Back/bfcache/PWA,
   desktop/mobile; thông báo không lặp và không còn dữ liệu riêng hiển thị.
7. Phân biệt replaced/mất mạng/hết hạn/khóa/thiếu quyền; không replay mutation.
8. Khóa/đổi mật khẩu/cấp-thu admin, identity recheck, chỉ admin gốc cấp/thu
   admin và API integration hiện có không bị suy giảm bởi cơ chế phiên mới.

Không dùng tài khoản admin thật hoặc đang có người làm việc để thử đá phiên;
không reset/grant/tạo user hoặc fixture trên main/server chỉ để chạy test.
Không dùng cùng session trình duyệt người dùng đang mở cho automation.
Kiểm thuần logic/mock/browser phù hợp không phá dữ liệu; ca cần fixture/ORM
ghi/race chưa có môi trường phù hợp thì ghi NOT_RUN, không gọi staticscan là PASS.
Không bắt18079 hoặc tạo clone. Ca thực hai thiết bị cho người dùng tự kiểm
cuối bằng tài khoản họ chọn, giải thích lần login mới sẽ thay phiên đang dùng.

Backup đúng DB/filestore/source/config trước upgrade/migration; triển khai
18069 và PCserver theo policy17/11, commit/push/deploy từng phần hoàn tất.
Không kéo/copy dirty tree, không restart/upgrade addon không liên quan. Rollout
có thể yêu cầu người dùng đăng nhập lại một lần; giữ đường đăng nhập admin
hoạt động và có rollback đã mô tả, không bỏ guard để chữa loop.

Cập nhật version/status/changelog/decision/security policy/guide/acceptance
và workflow đúng batch. Bàn giao commit/version/backup, source auth hooks đã
bao phủ, ảnh A/B/màn thông báo, kiểm đã chạy/chưa chạy, độ trễ thực quan sát.
Không tuyên bố một thiết bị vật lý hoặc tức thì khi offline. Phiên viết prompt
này chưa triển khai, chưa thay/thu hồi phiên thật hoặc cập nhật database.
