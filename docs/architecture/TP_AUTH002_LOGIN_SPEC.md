# AUTH-002 — Đặc tả hoàn thiện luồng đăng nhập TANPHAT ONE

**Phiên bản:** AUTH-002-SPEC v0.6, 29/10/2026 (Asia/Saigon), `CHG-20261029-034` — ghi người dùng chuyển cả hai slice sang `READY_FOR_TEST_CODE`, làm rõ ranh giới slice và thứ tự chạy (mục 10.2), phát prompt triển khai. v0.5 (`CHG-20261029-033`) ghi duyệt câu chữ 6.1; v0.4 (`CHG-20261029-032`) ghi D6-a; v0.3 (`CHG-20261029-031`) ghi kết quả V-A…V-C và thêm D6; v0.2 (`CHG-20261029-030`) ghi D1–D5; v0.1 (`CHG-20261029-029`) là bản đầu.
**Loại:** đặc tả trước code; không sửa application code. Runtime chỉ dùng cho V-A…V-C trên database test cô lập theo cho phép của người dùng (mục 8).
**Làn:** F theo [master plan](TP_CODE_EXECUTION_MASTER_PLAN.md#2-phân-loại-công-việc-và-cổng-thực-thi): giao diện React và template Odoo trên test. Phân loại thay đổi: giao diện + bảo mật xác thực.
**Trạng thái batch:** slice 1 `TECHNICAL_ACCEPTED` cho phạm vi test sau audit/correction `CHG-20261029-037` (mục 10.5/10.6; code gốc CHG-035, review trước CHG-036), slice 2 `IMPLEMENTED_PENDING_AUDIT` sau triển khai/test `CHG-20261029-038` (mục 10.7). Ngày 29/10/2026 người dùng chuyển cả hai slice sau đối chiếu mục 10.1; D1–D6 và câu chữ đã chốt, V-A…V-C đã kiểm. Slice 2 chỉ bắt đầu sau bàn giao/review slice 1 và khi người dùng giao batch; không mở dev/pilot/người dùng thật.
**Nguồn yêu cầu:** người dùng chọn ưu tiên làm chỉn chu trang đăng nhập vì đây là luồng đầu tiên của hệ thống (29/10/2026). AI soạn đặc tả; người dùng quyết định phạm vi và câu chữ.

AUTH-002 kế thừa [AUTH-001/DEC-012](../DECISIONS.md): React chỉ thu credential và gọi endpoint session native của Odoo; session, quyền, 2FA và passkey vẫn do Odoo xử lý. D4 đã chốt (a) nên DEC-012 giữ nguyên, không cần DEC mới.

## 0. Nhãn trạng thái

| Nhãn | Nghĩa |
| --- | --- |
| `observed-static` | Đọc từ source trong checkout hiện tại; chưa chạy runtime để xác nhận |
| `proposed` | Đề xuất của AI, chưa được người dùng chọn |
| `decision-needed` | Cần người dùng hoặc công ty quyết định trước khi code phần liên quan |
| `verify-first` | Phải kiểm trên database test trước khi code phần phụ thuộc |
| `verified-test` | Đã xác nhận bằng request HTTP thật trên database test cô lập `tp_tanphat_auth002_verify` (mục 8); chưa phải dev hay production |

## 1. Mục tiêu và phạm vi

**Mục tiêu:** từ lúc mở `/work/` đến khi vào không gian làm việc — kể cả 2FA, bị khóa tạm, hết phiên và đăng xuất — người dùng thấy cùng thương hiệu TANPHAT ONE, tiếng Việt, thông báo đúng tình huống và không phải nhập lại mật khẩu không cần thiết. Không giảm bất kỳ lớp bảo mật nào Odoo đang có.

**Điểm bắt đầu:** người dùng mở `/work/` hoặc một deep link trong `/work/` khi chưa có session. **Điểm kết thúc:** session đầy đủ (`uid` khác null) và người dùng đứng đúng trang đã yêu cầu; hoặc người dùng chủ động hủy/đăng xuất và quay về `/work/`.

**Trong phạm vi:** trang React `/work/` (login, thông báo, handoff 2FA); thông báo khi hết phiên và sau đăng xuất; giao diện các trang xác thực native của Odoo được dùng trong luồng (`/web/login`, `/web/login/totp`) bằng kế thừa template trong `custom_addons/`.

**Ngoài phạm vi:** xem mục 11.

## 2. Hiện trạng và khoảng trống (`observed-static`)

Đã có và **giữ nguyên** (AUTH-001, CHG-20261028-004): bố cục hai cột với minh họa cầu dây văng, Be Vietnam Pro, animation có reduced-motion, responsive 320–1440px; hiện/ẩn mật khẩu; khóa nút khi đang gửi; xóa mật khẩu khỏi form sau mỗi lần gửi; không lưu credential/session vào browser storage; giữ deep link; lỗi credential/gateway không lộ chi tiết server; 5 E2E trong `frontend/tests/e2e/login.spec.ts` và logout/expiry trong `projects.spec.ts`.

| Mã | Khoảng trống | Bằng chứng trong source | Ảnh hưởng người dùng |
| --- | --- | --- | --- |
| G1 | Tài khoản bật 2FA phải nhập mật khẩu **hai lần** | React gửi `/web/session/authenticate`; Odoo đặt `pre_uid`, để `uid` null khi cần MFA (`odoo/http/session.py` 245–256) và controller trả `{'uid': None}` (`addons/web/controllers/session.py` 53–56); session bẩn được lưu cuối request (`odoo/http/dispatcher.py` 213). Link handoff trỏ `/web/login?redirect=…` (`frontend/src/shared/api/session.tsx` 17–22); GET `/web/login` khi `uid` null hiển thị lại form mật khẩu (`addons/web/controllers/home.py` 110–173). Trang nhập mã `/web/login/totp` chỉ cần `pre_uid` (`addons/auth_totp/controllers/home.py` 17–27) | Nhập mật khẩu ở React, rồi nhập lại ở trang Odoo, rồi mới tới mã 2FA |
| G2 | Trang xác thực native mang thương hiệu Odoo, tiếng Anh | `web.login_layout` có “Manage Databases” và “Powered by Odoo” (`addons/web/views/webclient_templates.xml` 125–130); form 2FA “Enter verification code”, “Don't ask again on this device” (`addons/auth_totp/views/templates.xml` 3–46) | Bước bảo mật trông như một hệ thống khác; dễ nghi ngờ trang giả mạo |
| G3 | Hủy ở bước 2FA rơi về trang login gốc của Odoo | Form Cancel POST `/web/session/logout` không có `redirect` (`addons/auth_totp/views/templates.xml` 36–43); logout mặc định chuyển `/odoo` (`addons/web/controllers/session.py` 87–90) | Người dùng ra khỏi TANPHAT ONE, gặp form Odoo tiếng Anh |
| G4 | Bị khóa tạm do sai nhiều lần nhưng React báo “sai mật khẩu” | Odoo đếm lần sai theo IP và chặn mọi lần thử trong thời gian khóa bằng `AccessDenied` với thông điệp riêng (`odoo/addons/base/models/res_users.py` 1362–1391; tham số khởi tạo 10 lần/60 giây ở `ir_config_parameter.py` 28–29). React đổi mọi `AccessDenied` thành lỗi credential (`frontend/src/shared/api/client.ts` 125–127) | Người nhập **đúng** mật khẩu trong lúc bị khóa vẫn thấy “chưa đúng”, tiếp tục thử và bị khóa tiếp |
| G5 | Hết phiên và đăng xuất không có thông báo | 401 bất kỳ đặt session về null và thay toàn bộ app bằng trang login (`frontend/src/app/providers.tsx` 7–12); đăng xuất chuyển về `/work/` (`frontend/src/app/shell/AppShell.tsx` 41–45) | Người dùng không biết vì sao bị đưa về trang đăng nhập |
| G6 | Chi tiết nhỏ | Không có cảnh báo Caps Lock (trang Odoo gốc có `o_caps_lock_warning`); nhãn “Tiếng Việt” ở góc trông như nút chọn ngôn ngữ nhưng không bấm được (`LoginPage.tsx` 97); không tự đặt con trỏ vào ô tên đăng nhập | Gõ sai mật khẩu vì Caps Lock; bấm thử nhãn ngôn ngữ không có tác dụng |
| G7 | Tự đăng ký tài khoản và tự đặt lại mật khẩu đang mở trên trang native (`verified-test`, phát hiện ở V-C) | Cài `dev.MODULES` kéo theo `auth_signup` với `auth_signup.invitation_scope = b2c` và `auth_signup.reset_password = True`; `/web/login` có link đăng ký và đặt lại mật khẩu; `/web/signup` và `/web/reset_password` trả 200 kèm form (mục 8.2) | Người ngoài có thể tự tạo tài khoản portal; luồng đặt lại mật khẩu qua email trái D1-a và chưa có máy chủ mail |

G1, G3 và G4 đã được xác nhận bằng request thật trên database test (`verified-test`, mục 8.2). G2 xác nhận một phần: trang nhập mã không có “Powered by Odoo” nhưng vẫn tiếng Anh; `/web/login` có “Powered by Odoo”.

Giới hạn đã biết, **không** xử lý trong AUTH-002: khi phiên hết hạn lúc đang nhập form, app được thay bằng trang login nên dữ liệu chưa lưu bị mất. Lưu nháp vào browser storage trái nguyên tắc không lưu dữ liệu nghiệp vụ ở frontend; ghi nhận để xem xét trong C02.

## 3. Quyết định của người dùng (D1–D5 chốt v0.2, D6 chốt v0.4)

Ngày 29/10/2026 người dùng trả lời “Chốt mặc định” cho câu hỏi chốt D1–D5 theo đề xuất mặc định của v0.1, rồi chọn “Disable both (D6-a)” cho D6 phát sinh từ V-C. Các lựa chọn dưới đây là phạm vi AUTH-002; đổi lựa chọn sau này phải cập nhật đặc tả và test liên quan trước khi code.

| Mã | Câu hỏi | Các lựa chọn đã xét | Đã chốt 29/10/2026 | Hệ quả cho triển khai |
| --- | --- | --- | --- | --- |
| D1 | Quên mật khẩu xử lý thế nào? | (a) Giữ “liên hệ quản trị viên”. (b) Bật tự đặt lại qua email bằng `auth_signup` — cần máy chủ gửi mail, mẫu email và chính sách công ty | (a) | Giữ nội dung hỗ trợ hiện có; không cấu hình mail, không bật tự đặt lại mật khẩu (`auth_signup` chỉ bị tắt theo D6-a). (b) nếu cần sau này là batch riêng |
| D2 | Ô “Không hỏi lại trên thiết bị này” ở bước 2FA (Odoo mặc định nhớ thiết bị 90 ngày, tham số `auth_totp.trusted_device_age`) | (a) Giữ hành vi Odoo, chỉ Việt hóa. (b) Ẩn ô. (c) Đổi số ngày | (a) | Giữ field `remember` và thời hạn mặc định; chỉ dịch nhãn. Đổi thời hạn là chính sách bảo mật cần công ty quyết định riêng |
| D3 | Logo trên trang login và trang native | (a) Giữ monogram SVG hiện tại. (b) Người dùng cung cấp logo chính thức (file vector, có quyền sử dụng) | (a) | Trang native dùng cùng monogram/wordmark với React; thay khi người dùng cung cấp logo chính thức |
| D4 | Sang bước 2FA bằng nút bấm hay tự chuyển trang? | (a) Giữ nút bấm rõ ràng như DEC-012. (b) Tự chuyển ngay khi Odoo báo cần 2FA | (a) | DEC-012 giữ nguyên; ca E2E handoff hiện có chỉ đổi đích link theo V-A |
| D5 | Câu chữ hiển thị | Duyệt bảng mục 6, sửa trực tiếp nếu muốn | Bảng mục 6 nguyên văn | Câu chữ mục 6 là nguồn cho test. V-A đạt nên `mfa_body` dùng câu chính, không thêm câu nhập lại mật khẩu |
| D6 | Tắt tự đăng ký và tự đặt lại mật khẩu trên trang native (G7)? | (a) Tắt cả hai: `auth_signup.invitation_scope = b2b`, `auth_signup.reset_password = False`. (b) Giữ mặc định Odoo (đăng ký b2c, đặt lại mật khẩu qua email) | (a) | Khớp D1-a; cách áp dụng ở mục 3.1 |

### 3.1. Cách áp dụng D6-a (`observed-static` từ source `auth_signup`)

- `auth_signup` đặt hai tham số mặc định bằng `<function>` trong khối `noupdate` khi cài (`addons/auth_signup/data/ir_config_parameter_data.xml`). `tp_web_login` phụ thuộc `auth_signup` nên được nạp sau, và đặt lại `auth_signup.invitation_scope = b2b` bằng `set_str`, `auth_signup.reset_password = False` bằng `set_bool` trong khối `noupdate="1"`: chỉ chạy khi cài addon, không ghi đè lựa chọn quản trị viên đổi sau đó trong Settings.
- Khi hai tham số tắt, controller trả 404 cho `/web/signup` và `/web/reset_password` không kèm token (`addons/auth_signup/controllers/main.py` 44–45, 100–101), và template login không hiện link (`signup_enabled`, `reset_password_enabled`). Link có token do quản trị viên chủ động gửi vẫn là luồng của Odoo; không dùng trong AUTH-002 vì chưa có máy chủ mail.
- Không gỡ module `auth_signup` (module khác như `auth_totp_portal` phụ thuộc nó), không xóa link bằng template và không sửa `addons/`.
- Database chưa cài `tp_web_login` (dev, pilot, production) giữ mặc định cho đến khi cài addon hoặc đặt tham số theo checklist cấu hình C06; AUTH-002 không tự đổi `tp_tanphat_dev`.
- Link “Cần hỗ trợ đăng nhập?” trên React giữ nội dung D1-a.

## 4. Luồng đích

| Mã | Tình huống | Hành vi đích | Thay đổi so với hiện tại |
| --- | --- | --- | --- |
| F1 | Mở `/work/` lần đầu | Form đăng nhập, con trỏ ở ô tên đăng nhập | Thêm focus |
| F2 | Đăng nhập thường | Vào đúng deep link đã yêu cầu | Giữ nguyên |
| F3 | Sai tên đăng nhập hoặc mật khẩu | Một thông báo chung, không cho biết tài khoản có tồn tại hay không; xóa mật khẩu | Giữ nguyên |
| F4 | Đang bị khóa tạm do thử sai nhiều lần | Thông báo chờ rồi thử lại; **không** nói sai mật khẩu | Mới (G4) |
| F5 | Tài khoản cần 2FA | Panel giải thích → nút sang trang nhập mã mang thương hiệu TANPHAT ONE, tiếng Việt → nhập mã → về đúng deep link. Hủy → về `/work/` | Không nhập lại mật khẩu (G1, V-A đạt); thương hiệu (G2); hủy về `/work/` (G3) |
| F6 | Phiên hết hạn khi đang dùng | Trang login có thông báo “phiên đã hết hạn”; đăng nhập lại về trang đang mở | Mới (G5) |
| F7 | Bấm Đăng xuất | Trang login có thông báo “đã đăng xuất” | Mới (G5) |
| F8 | Passkey hoặc phương thức khác | Link trong “Cần hỗ trợ đăng nhập?” mở `/web/login` native, nay cùng thương hiệu | Giao diện (G2); luồng giữ native |

## 5. Yêu cầu chi tiết

### 5.1. Lớp React (`frontend/src/features/auth`, `frontend/src/app`, `frontend/src/shared/api`)

| Mã | Yêu cầu | Ràng buộc |
| --- | --- | --- |
| L01 | Phân biệt ba loại lỗi khi `/web/session/authenticate` trả lỗi: sai thông tin, bị khóa tạm, lỗi khác | Quy tắc theo V-B (mục 8.2): `error.data.name === 'odoo.exceptions.AccessDenied'` **và** `error.data.arguments` đúng bằng `['Access Denied']` → `credentials`; `AccessDenied` với `arguments` khác → `cooldown`; mọi trường hợp còn lại giữ xử lý lỗi hiện có. So khớp chuỗi mặc định không dịch của `AccessDenied` (Odoo không dịch chuỗi này), không dò câu cooldown vì câu này có thể được dịch. Không hiển thị `data.message`, `data.arguments` hay `data.debug`. Giữ thông báo 429 hiện có cho trường hợp proxy trả 429 |
| L02 | Thông báo hết phiên (F6) | Chỉ hiện khi tab này đã có session hợp lệ rồi nhận 401. Cờ lý do giữ trong bộ nhớ ứng dụng, không ghi localStorage/sessionStorage/cookie. Tải lại trang sau khi hết phiên thì không còn thông báo — chấp nhận |
| L03 | Thông báo đã đăng xuất (F7) | Form đăng xuất gửi `redirect=/work/?signed_out=1` (giá trị cố định). React hiện thông báo rồi xóa tham số bằng `history.replaceState`; không ảnh hưởng deep link và không đưa dữ liệu khác vào URL |
| L04 | Handoff 2FA không bắt nhập lại mật khẩu (F5) | V-A đạt: link đổi thành `/web/login/totp?redirect=<deep link>`. `redirect` chỉ là path cùng origin bắt đầu `/work/`, lấy từ `window.location` như hiện tại. Cần `dbfilter` chọn đúng một database (mục 12); không áp dụng nếu môi trường cho chọn database |
| L05 | Cảnh báo Caps Lock | Chỉ khi ô mật khẩu đang focus; dùng trạng thái phím, không đọc/ghi giá trị mật khẩu; thông báo qua vùng `aria-live="polite"` |
| L06 | Con trỏ vào ô tên đăng nhập khi mở trang (F1) | Không cướp focus khi đang có thông báo lỗi (lỗi vẫn nhận focus như hiện tại) |
| L07 | Nhãn “Tiếng Việt” không còn trông như nút | Đổi thành chữ tĩnh: bỏ viền, nền và hiệu ứng như nút; không thêm chuyển ngôn ngữ |
| L08 | Áp dụng câu chữ mục 6 | Nguyên văn bảng đã chốt (D5) |

### 5.2. Lớp Odoo template (addon đề xuất `tp_web_login`)

Addon mới chỉ chứa QWeb/CSS và dữ liệu đặt hai tham số `auth_signup` theo D6-a (mục 3.1); không model, không controller. `depends` gồm `web`, `auth_totp` (các module có template được kế thừa) và `auth_signup` (để dữ liệu D6-a nạp sau dữ liệu mặc định). Đặt riêng để gỡ được độc lập và `tp_core` không phải phụ thuộc module xác thực. Đây là `proposed`; người code không tự đổi vị trí nếu chưa ghi lý do.

| Mã | Yêu cầu | Ràng buộc |
| --- | --- | --- |
| L09 | Kế thừa `web.login_layout`: monogram/wordmark TANPHAT ONE như trang React (D3-a), màu theo token của login React (`--login-navy` `#15384e`, `--login-cyan` `#087386`, `--login-gold` `#e7bd79`), bỏ link “Powered by Odoo” | CSS đặt trong một class gốc riêng, không ảnh hưởng portal/website khác. Font: Be Vietnam Pro (giấy phép OFL) đóng gói trong addon hoặc dùng font hệ thống; không tải từ CDN ngoài. “Manage Databases” tắt bằng cấu hình `list_db = False` ở môi trường pilot/production (C06), không xóa bằng template |
| L10 | Trang nhập mã 2FA tiếng Việt | Theo V-A/V-C, ngôn ngữ trang đi theo trình duyệt (cookie `frontend_lang` hoặc `Accept-Language`), không theo ngôn ngữ của người dùng, và bản dịch `vi_VN` của Odoo thiếu tiêu đề và gợi ý. Vì vậy override ghi **chữ tiếng Việt cố định** theo mục 6 cho tiêu đề, gợi ý, placeholder, nhãn nhớ thiết bị, nút xác nhận và nút hủy; không phụ thuộc gói `vi_VN` hay ngôn ngữ trình duyệt. Thông báo lỗi hiển thị câu `totp_error` cố định thay cho chuỗi server (server có thể trả lỗi sai mã, sai định dạng hoặc khóa tạm, bằng tiếng Anh hay tiếng Việt tùy trình duyệt). Giữ nguyên tên field `totp_token`, `remember`, `csrf_token`, `redirect` và thuộc tính `autocomplete="one-time-code"`, `inputmode="numeric"` |
| L11 | Hủy ở bước 2FA về `/work/` (G3) | Thêm `redirect` cố định `/work/` vào form Cancel; vẫn là POST logout có CSRF. Đã kiểm ở V-A: có `redirect=/work/` thì về `/work/`, CSRF sai trả 400 |
| L12 | `/web/login` native (passkey, quản trị) cùng thương hiệu | Không thêm/bớt field; giữ `csrf_token`, `data-captcha`, nút passkey (`auth_passkey` kế thừa `web.login` với priority 32). V-C: `auth_oauth` và `website` không cài nên không có nút OAuth và không phải xét priority với template website. Link đăng ký/đặt lại mật khẩu biến mất nhờ tham số D6-a, không xóa bằng template |

## 6. Bảng câu chữ đã chốt (D5)

| Khóa | Hiện tại | Đã chốt |
| --- | --- | --- |
| `cooldown` | (đang hiện nhầm lỗi sai mật khẩu) | Tạm thời chưa thể đăng nhập vì đã thử sai nhiều lần. Vui lòng chờ ít phút rồi thử lại. |
| `credentials` | Tên đăng nhập hoặc mật khẩu chưa đúng. Vui lòng kiểm tra và thử lại. | Giữ nguyên |
| `expired` | (không có) | Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại để tiếp tục. |
| `signed_out` | (không có) | Bạn đã đăng xuất khỏi TANPHAT ONE. |
| `caps_lock` | (không có) | Caps Lock đang bật. |
| `mfa_title` | Tài khoản cần xác thực bổ sung. | Tài khoản cần xác thực hai lớp. |
| `mfa_body` | Tiếp tục bằng phương thức bảo mật đã thiết lập, sau đó quay lại không gian làm việc. | Mở ứng dụng xác thực trên điện thoại để lấy mã, rồi nhập ở bước tiếp theo. (V-A đạt nên không thêm câu nhập lại mật khẩu.) |
| `mfa_link` | Tiếp tục xác thực bảo mật | Tiếp tục nhập mã xác thực |
| `totp_title` | Enter verification code | Nhập mã xác thực |
| `totp_hint` | Check your Authenticator app for your code. | Mở ứng dụng xác thực để xem mã gồm 6 chữ số. |
| `totp_remember` | Don't ask again on this device | Không hỏi lại trên thiết bị này |
| `totp_submit` | Log in | Xác nhận |
| `totp_cancel` | Cancel | Hủy và quay lại |

Thời gian khóa phụ thuộc tham số `base.login_cooldown_duration` của từng database nên câu chữ không ghi số giây cụ thể.

### 6.1. Câu chữ bổ sung sau V-A (đã duyệt v0.5)

V-A cho thấy trang nhập mã còn hai chuỗi chưa có trong bảng trên: placeholder ô nhập và thông báo lỗi do server tạo. Ngày 29/10/2026 người dùng trả lời “Approve 6.1”, duyệt nguyên văn hai câu dưới đây; chúng là nguồn cho L10 và T08 như bảng mục 6.

| Khóa | Hiện tại (Odoo) | Đã duyệt 29/10/2026 |
| --- | --- | --- |
| `totp_placeholder` | Enter code | Mã 6 chữ số |
| `totp_error` | Lỗi server, ví dụ “Verification failed, please double-check the 6-digit code”, “Invalid authentication code format.” hoặc câu khóa tạm; tiếng Anh hay tiếng Việt tùy trình duyệt | Chưa xác thực được mã. Vui lòng nhập mã mới nhất trên ứng dụng xác thực; nếu đã thử nhiều lần, chờ ít phút rồi thử lại. |

Một câu chung cho mọi lỗi ở bước nhập mã giữ nguyên tắc không hiển thị message server, và vẫn đúng khi người dùng bị khóa tạm ngay ở bước này (`_assert_can_auth` cũng chạy khi kiểm mã).

## 7. Ràng buộc bảo mật bắt buộc

1. Không tạo endpoint xác thực mới; không xử lý mã TOTP, passkey hoặc mật khẩu ngoài endpoint native của Odoo (DEC-012).
2. Không lưu mật khẩu, mã, cookie hoặc payload session vào localStorage/sessionStorage/IndexedDB, URL hay log. Tham số URL duy nhất được thêm là `signed_out=1`.
3. `redirect` chỉ nhận path cùng origin bắt đầu bằng `/work/`; không lấy redirect từ query tùy ý của người dùng để dựng link 2FA.
4. Thông báo sai thông tin không phân biệt tài khoản tồn tại hay không. Thông báo khóa tạm không nêu số lần còn lại.
5. Không tắt hoặc nới cooldown, captcha, CSRF, header `X-Frame-Options`/CSP của trang login, cũng không đổi thời hạn nhớ thiết bị (D2-a). Trang `/web/login/totp` của Odoo hiện không gửi `X-Frame-Options`/CSP (V-A); bổ sung ở reverse proxy theo C06, không thêm controller vào `tp_web_login` (mục 12).
6. Không sửa `odoo/` hoặc `addons/`; mọi thay đổi trang native là kế thừa template trong `custom_addons/`.
7. Handoff 2FA giữ nút bấm (D4-a). Nếu sau này đổi sang tự chuyển trang, phải ghi DEC mới thay phần handoff của DEC-012 trước khi code.

## 8. Kiểm chứng trước code (`verify-first`)

Chạy trên database test cô lập với actor fixture; không dùng `tp_tanphat_dev` hay người dùng thật. Môi trường tái lập được nên dùng tooling C01 khi đã có; nếu chưa, chỉ dùng helper local đã được audit và ghi rõ.

### 8.1. Câu hỏi kiểm chứng

| Mã | Câu hỏi | Cách kiểm | Nếu không đạt |
| --- | --- | --- | --- |
| V-A | Sau `/web/session/authenticate` trả `uid: null`, cookie session có giữ `pre_uid` để mở thẳng `/web/login/totp` không? | Actor fixture bật TOTP; POST authenticate rồi GET `/web/login/totp?redirect=/work/projects` cùng cookie: phải trả form nhập mã (200), không chuyển về `/web/login` | L04 giữ `/web/login`, đổi câu chữ `mfa_body`; G1 ghi là giới hạn còn lại |
| V-B | Lỗi JSON-RPC khi bị khóa tạm khác lỗi sai mật khẩu ở field nào? | Ghi lại `error.data` (name, arguments/message) cho: sai mật khẩu, tài khoản không tồn tại, đang khóa tạm (giảm `base.login_cooldown_after` chỉ trên database test) | Nếu không phân biệt ổn định được: L01 dùng một thông báo chung “chưa đúng hoặc tạm khóa” và ghi gap |
| V-C | Database test có module và ngôn ngữ nào? | Đọc trạng thái `auth_totp`, `auth_passkey`, `auth_signup`, `website` và ngôn ngữ `vi_VN`. `website` nếu cài cũng kế thừa `web.login_layout` (`addons/website/views/website_templates.xml` 1765) nên phải xét priority | Điều chỉnh L09/L10/L12 theo module thực có; không cài thêm module chỉ để làm đẹp nếu người dùng chưa đồng ý |

### 8.2. Kết quả (29/10/2026, `verified-test`)

**Môi trường.** Người dùng cho phép khởi động Odoo trên database test cô lập, không đụng `tp_tanphat_dev`. Database `tp_tanphat_auth002_verify` tạo mới trên PostgreSQL local của dự án (cổng 55432), có file đánh dấu sở hữu; Odoo của checkout hiện tại chạy riêng ở `127.0.0.1:18099` với config riêng (`dbfilter` chỉ khớp database này, `list_db = False`, `workers = 0`, `proxy_mode = False`, data dir riêng). Cài `dev.MODULES` không demo, ghi trạng thái gốc, rồi mới nạp `vi_VN` để kiểm ngôn ngữ. Actor fixture: ba user tổng hợp `auth002.verify.*` thuộc `tp_core.group_user` (một bật TOTP ngôn ngữ `en_US`, một bật TOTP ngôn ngữ `vi_VN`, một không bật 2FA); mật khẩu và secret TOTP sinh ngẫu nhiên, chỉ nằm trong `.local/`. Chỉ trên database này đặt `base.login_cooldown_after = 3` và `base.login_cooldown_duration = 20` để kiểm khóa tạm. C01 chưa có nên dùng helper local mới viết theo mẫu `.local/ctr002a-verify`, nằm ngoài Git: `.local/auth002-verify/runtime.py` (chuẩn bị, seed, start/stop có kiểm PID), `verify.py` và `probe_lang.py` (request HTTP thật). Report JSON không chứa mật khẩu, secret hay cookie; script từ chối ghi report nếu phát hiện secret. Sau khi kiểm đã dừng Odoo và PostgreSQL; `server.log` không có dòng `ERROR`. Database test còn giữ để chạy lại, chỉ xóa khi người dùng yêu cầu.

| Mã | Kết luận | Bằng chứng | Hệ quả cho đặc tả |
| --- | --- | --- | --- |
| V-A | **Đạt** | Actor TOTP gọi `/web/session/authenticate` → HTTP 200, `uid: null`, `/api/v1/me` 401. Cùng cookie, GET `/web/login/totp?redirect=/work/projects?q=DEV-001` → 200, có `totp_token`, `csrf_token`, giữ nguyên `redirect`, không có ô mật khẩu. Mã sai → 200 kèm thông báo lỗi. Mã đúng → 303 về `/work/projects?q=DEV-001`, sau đó `/api/v1/me` 200. Link hiện tại `/web/login?redirect=…` → 200 hiện lại form mật khẩu (xác nhận G1). Không có `pre_uid` → 303 về `/web/login` | L04 đổi link sang `/web/login/totp`; `mfa_body` dùng câu chính |
| V-A hủy | Xác nhận G3, L11 khả thi | Form Cancel hiện tại (không `redirect`) → 303 `/odoo`. Thêm `redirect=/work/` → 303 `/work/`. Sau khi hủy, `/web/login/totp` → 303 `/web/login` (`pre_uid` đã bị xóa). CSRF sai → 400 | L11 giữ như đặc tả |
| V-A ngôn ngữ | Trang mã theo ngôn ngữ **trình duyệt**, không theo user | User `vi_VN`, trình duyệt không gửi tiếng Việt → toàn tiếng Anh. User `en_US` với cookie `frontend_lang=vi_VN` hoặc chỉ `Accept-Language: vi-VN` → nhãn nhớ thiết bị, nút đăng nhập, Hủy và lỗi sai mã thành tiếng Việt, nhưng tiêu đề “Enter verification code” và gợi ý “Check your Authenticator app…” vẫn tiếng Anh (thiếu trong bản dịch Odoo). Không có cookie/header tiếng Việt → toàn tiếng Anh | L10 dùng chữ tiếng Việt cố định; thêm `totp_placeholder`, `totp_error` (6.1) |
| V-A header | Trang mã thiếu header chống nhúng khung | `/web/login` trả `X-Frame-Options: SAMEORIGIN` và `Content-Security-Policy: frame-ancestors 'self'`; `/web/login/totp` không trả header nào trong hai header này (controller `auth_totp` render trực tiếp) | Rủi ro mục 12; bổ sung ở reverse proxy (C06) |
| V-B | **Phân biệt được ổn định** | Sai mật khẩu và login không tồn tại cho lỗi giống hệt: `data.name = odoo.exceptions.AccessDenied`, `arguments = ["Access Denied"]` — không lộ tài khoản có tồn tại. Sau 3 lần sai cộng dồn trên hai tài khoản cùng IP, cả mật khẩu đúng lẫn sai đều nhận `AccessDenied` với `arguments = ["Too many login failures, please wait a bit before trying again."]`, vẫn tiếng Anh khi có cookie `frontend_lang=vi_VN`. Mọi phản hồi là HTTP 200 kiểu JSON-RPC, không phải 429; `data.debug` không chứa traceback. Sau 22 giây (> 20 giây khóa) mật khẩu đúng đăng nhập được. Chuỗi mặc định `Access Denied` không bọc dịch trong `odoo/exceptions.py`; câu khóa tạm có bản dịch trong `vi.po` nên không dùng để so khớp | Quy tắc L01 ở mục 5.1; xác nhận G4 và rủi ro đếm theo IP |
| V-C | **Có kết luận** | Cài mới: `web`, `auth_totp`, `auth_totp_mail`, `auth_totp_portal`, `auth_passkey`, `auth_signup`, `portal`, `mail`, `base_setup` đã cài; `auth_oauth` và `website` không cài. Chỉ `en_US` hoạt động. Cooldown mặc định 10 lần/60 giây; `auth_totp.trusted_device_age` chưa đặt (mặc định 90 ngày). `auth_signup.reset_password = True`, `auth_signup.invitation_scope = b2c`: `/web/login` có link đăng ký và đặt lại mật khẩu, `/web/signup` và `/web/reset_password` trả 200 kèm form. `/web/login` có “Powered by Odoo”, nút passkey, `data-captcha`; không có “Manage Databases” nhờ `list_db = False` | L10 không dựa vào gói `vi_VN`; L12 không phải xét template website hay nút OAuth; G7 → D6 |

**Giới hạn của kết quả.** Kết quả lấy trên database cài mới từ `dev.MODULES`. Chưa đọc module, ngôn ngữ và tham số thực của `tp_tanphat_dev` (ngoài phạm vi cho phép của lượt này), nên trước khi đưa addon vào dev phải kiểm lại các điểm V-C ở đó. Chưa kiểm ô nhớ thiết bị (D2 giữ hành vi Odoo), passkey, reverse proxy và HTTPS. Thao tác hủy và mã sai kiểm bằng HTTP, chưa qua trình duyệt thật; T08 sẽ phủ phần này.

## 9. Ca nghiệm thu

| Mã | Loại | Ca | Kết quả mong đợi |
| --- | --- | --- | --- |
| T01 | Vitest | Phân loại lỗi authenticate: sai thông tin, khóa tạm, 429, 502, lỗi mạng | Đúng loại theo L01; không có message server trong kết quả |
| T02 | Mock E2E | Khóa tạm | Hiện `cooldown`, không hiện `credentials`; mật khẩu bị xóa khỏi form |
| T03 | Mock E2E | Đang ở trang dự án, request kế tiếp nhận 401 | Trang login hiện `expired`; đăng nhập lại về đúng trang |
| T04 | Mock E2E | Lần đầu mở `/work/` | Không có thông báo `expired`/`signed_out`; con trỏ ở ô tên đăng nhập |
| T05 | Live E2E | Bấm Đăng xuất | Trang login hiện `signed_out`; URL không còn `signed_out=1`; `/api/v1/me` trả 401; deep link sau đó vẫn hoạt động |
| T06 | Mock E2E | Caps Lock khi focus ô mật khẩu | Hiện/ẩn đúng; không có giá trị mật khẩu trong DOM ngoài input |
| T07 | Mock E2E | Handoff 2FA (sửa ca hiện có trong `login.spec.ts`) | Link là `/web/login/totp?redirect=<deep link>` (V-A đạt), `redirect` là path `/work/…` cùng origin; mật khẩu đã bị xóa |
| T08 | Live E2E | 2FA trọn luồng với actor fixture có TOTP | Không nhập lại mật khẩu; trang mã thương hiệu TANPHAT ONE, tiếng Việt theo mục 6/6.1 **dù trình duyệt đặt tiếng Anh**; mã sai hiện `totp_error`, không hiện chuỗi server; mã đúng về deep link; Hủy về `/work/` và `/api/v1/me` 401 |
| T09 | Live E2E | Khóa tạm thật trên database test | Sau N lần sai, mật khẩu đúng vẫn bị chặn và hiện `cooldown`; hết thời gian khóa thì đăng nhập được |
| T10 | Odoo HttpCase | Render `/web/login` và `/web/login/totp` (có `pre_uid`) | Có dấu hiệu thương hiệu TANPHAT ONE, không có “Powered by Odoo”; còn `csrf_token`, `totp_token`, `redirect`, `data-captcha`, nút passkey; POST logout với CSRF sai vẫn 400. D6-a: sau khi cài addon, `/web/login` không có link `/web/signup`, `/web/reset_password`; GET hai route này không kèm token trả 404; hai tham số `auth_signup` có giá trị `b2b`/`False` |
| T11 | Hồi quy | Toàn bộ `login.spec.ts`, logout/expiry trong `projects.spec.ts`, kích thước 320/390/1440, reduced-motion | Đạt; không tràn ngang |
| T12 | Bảo mật | Sau mỗi luồng F2–F8 | Không có mật khẩu/mã/session trong storage hoặc URL; link 2FA không bao giờ trỏ ra ngoài origin |

Mã TOTP trong T08 sinh từ secret của actor fixture chỉ trên database test; không đưa secret vào Git, log hoặc report.

## 10. Kế hoạch triển khai đề xuất

1. **Slice 1 — React:** L01–L03, L05–L07 và L08 cho các khóa `cooldown`, `credentials`, `expired`, `signed_out`, `caps_lock`. L01 đã có quy tắc từ V-B. Kiểm: typecheck, Vitest, build, mock E2E T01–T04, T06, T11. L04 là một dòng đổi link nhưng chỉ đúng khi trang mã đã Việt hóa, nên giao cùng slice 2 cùng sửa T07; ba khóa `mfa_title`, `mfa_body`, `mfa_link` đi cùng L04 (mục 10.2).
2. **Slice 2 — template Odoo và handoff:** L04, L09–L12, L08 cho ba khóa `mfa_*` và dữ liệu D6-a; câu chữ mục 6 và 6.1 đã duyệt. Cài addon chỉ trên database test cô lập; Odoo test T10; live E2E T05, T07–T09, T12 cần runtime test có actor TOTP (tooling C01 nếu đã có, nếu chưa thì helper local kiểu `.local/auth002-verify` và ghi rõ).
3. Không cài addon hay upgrade `tp_tanphat_dev` trong batch; việc đưa vào dev là yêu cầu riêng của người dùng.
4. Rollback: addon chỉ có template/CSS và dữ liệu tham số D6, không schema; gỡ addon trả lại giao diện gốc nhưng không tự đổi lại tham số D6-a (muốn mở lại đăng ký/đặt lại mật khẩu phải là quyết định mới và đặt trong Settings). Thay đổi React đảo ngược bằng diff.

### 10.1. Đối chiếu cổng Ready for Code

AUTH-002 là làn F, không có dữ liệu nghiệp vụ, tiền hay quyền record mới; các tiêu chí RFC viết cho slice nghiệp vụ được đối chiếu như sau. Theo [cổng Ready for Code](TP_READY_FOR_CODE_GATE.md), chỉ người dùng chọn chuyển giai đoạn. Bảng do AI đối chiếu ở v0.5; người dùng dựa vào đó chuyển cả hai slice ngày 29/10/2026 (v0.6).

| RFC | Slice 1 — React | Slice 2 — template Odoo và handoff |
| --- | --- | --- |
| RFC-01 scope | Có: mục 1, 4, 10, 10.2, 11; version v0.6 | Có: mục 1, 4, 5.2, 10, 10.2, 11; version v0.6 |
| RFC-02 actor/BASE | Không áp dụng: không có vai trò nghiệp vụ | Không áp dụng |
| RFC-03 state/transition | Không áp dụng: không thêm state; session do Odoo quản lý (DEC-012) | Không áp dụng: dùng nguyên luồng `pre_uid` → `finalize` của Odoo (V-A) |
| RFC-04 dữ liệu | Không áp dụng: chỉ cờ trong bộ nhớ (L02) và tham số `signed_out=1` (L03) | Có: không model/field; chỉ hai tham số `auth_signup` theo D6-a (mục 3.1) |
| RFC-05 quyền | Có: mục 7, không endpoint mới, không lưu credential, redirect cùng origin | Có: mục 7, giữ CSRF/captcha/cooldown/passkey; tắt đăng ký và đặt lại mật khẩu (D6-a). Header khung trang mã thuộc C06, ngoài slice |
| RFC-06 hồ sơ đại diện | Không áp dụng | Không áp dụng |
| RFC-07 màn hình/thông báo | Có: F1–F7, L01–L08, câu chữ mục 6 (D5) | Có: F5, F8, L04, L09–L12, câu chữ mục 6 và 6.1 đã duyệt |
| RFC-08 API | Có: không đổi API; lỗi JSON-RPC đã ghi ở V-B | Có: không đổi API; route native giữ nguyên field và CSRF (V-A) |
| RFC-09 ca nghiệm thu | Có: T01–T04, T06, T11, truy vết mục 13 | Có: T05, T07–T10, T12, truy vết mục 13; live E2E cần runtime test cô lập |
| RFC-10 quyết định còn mở | Không còn: D1–D6 đã chốt | Không còn: D1–D6 đã chốt, 6.1 đã duyệt. Lựa chọn kỹ thuật trong L09 (đóng gói font hay dùng font hệ thống) để người code chọn và ghi lý do |

### 10.2. Ranh giới slice, thứ tự chạy và prompt (v0.6)

Người dùng chuyển cả hai slice ngày 29/10/2026. Phiên điều phối làm rõ các điểm dưới đây khi soạn prompt; không đổi quyết định D1–D6 hay câu chữ đã duyệt.

- **Thứ tự:** chạy slice 1 trước. Slice 2 chỉ bắt đầu khi slice 1 đã bàn giao (status, changelog, `ai_workflow.py finish`) và phiên điều phối đã review. Hai slice cùng sửa `LoginPage.tsx` và `login.spec.ts`, và T05 của slice 2 cần L03 của slice 1; không chạy song song trên cùng checkout.
- **Câu chữ handoff 2FA:** `mfa_title`, `mfa_body`, `mfa_link` áp dụng ở slice 2 cùng L04. `mfa_body` nói nhập mã “ở bước tiếp theo”, chỉ đúng khi link đã trỏ trang nhập mã; áp dụng ở slice 1 thì trong khoảng giữa hai slice người dùng đọc câu đó rồi vẫn bị hỏi lại mật khẩu. Slice 1 giữ câu chữ handoff hiện có.
- **Link handoff (`observed-static`):** `loginUrl()` trong `frontend/src/shared/api/session.tsx` đang dựng cả hai link của `LoginPage.tsx`: link handoff 2FA và link “Dùng xác thực hai bước hoặc khóa bảo mật” (F8). L04 chỉ đổi link handoff sang `/web/login/totp?redirect=…`; link F8 vẫn mở `/web/login` vì luồng passkey không có `pre_uid`.
- **Hồi quy live hiện có:** `projects.spec.ts` không phải mock; spec đọc `.local/dev-secrets.json` và chạy trên runtime dev (Odoo cổng 18069). T11 cần runtime này. Slice 1 chỉ được `dev.ps1 start`/`stop` để chạy hồi quy và phải trả runtime về trạng thái ban đầu; không setup, upgrade, seed hay cài addon. Không chạy được thì báo T11 chưa đủ, không coi là đạt.
- **Odoo test T10:** không thêm `tp_web_login` vào `MODULES` của `scripts/dev.py` trong AUTH-002, vì lần `setup`/`upgrade` dev kế tiếp sẽ cài addon lên dev. Chạy T10 bằng cài addon với `--test-enable` trên database test cô lập có marker sở hữu (ưu tiên `tp_tanphat_auth002_verify` của mục 8.2); không dùng `tp_tanphat_dev` hay `tp_tanphat_test`. Lệnh chạy ghi vào handoff để lặp lại được.
- **Live E2E:** spec mới chạy theo opt-in, có guard database/origin như `contract-workflow-live.spec.ts`; credential và secret TOTP đọc từ biến môi trường hoặc `.local/`, không vào Git, log hay report. Playwright dùng lại Vite đang chạy ở cổng 4173 (`reuseExistingServer`), nên trước khi chạy phải kiểm cổng trống hoặc server đúng `TP_ODOO_ORIGIN`/`VITE_ODOO_DATABASE` của database test.
- **Prompt:** [slice 1 — React](../prompts/CLAUDE_AUTH002_S1_REACT_LOGIN.md), [slice 2 — trang native và handoff](../prompts/CLAUDE_AUTH002_S2_NATIVE_LOGIN.md).

### 10.3. Bàn giao slice 1 (`CHG-20261029-035`, `IMPLEMENTED_PENDING_AUDIT`)

Phiên Claude thực thi theo prompt slice 1; chưa phải `TECHNICAL_ACCEPTED`. Phiên điều phối review rồi mới giao slice 2.

| Yêu cầu | Cách làm | Test |
| --- | --- | --- |
| L01 | `client.ts`: `AccessDenied` có `arguments` đúng `["Access Denied"]` → `credentials`; mọi `AccessDenied` khác, kể cả thiếu `arguments` → `cooldown`; lỗi JSON-RPC khác, HTTP lỗi, JSON hỏng, lỗi mạng → `connection`; 429 → `rate_limit`. Không đọc `message`/`debug` | T01 `client.test.ts`; T02 `login-notices.spec.ts` |
| L02 | `features/auth/sessionNotice.ts` theo dõi QueryCache: query `session` đi từ có người dùng sang `null` (401 của request nghiệp vụ hoặc của `/me`) thì bật cờ trong bộ nhớ; lần đầu mở không có session và đăng xuất (`clear`) không bật; có session lại thì tắt. Nối ở `app/providers.tsx` | `sessionNotice.test.ts`; T03 (request nghiệp vụ 401, `/me` 401 khi focus lại; tải lại thì mất thông báo) |
| L03 | `AppShell.tsx` gửi `redirect=/work/?signed_out=1`. `LoginPage` đọc tham số khi mount, gọi `navigate(..., { replace: true })` để router đồng bộ rồi `history.replaceState` giữ đúng đường dẫn đang mở (router ghi gốc thành `/work`, không có `/` cuối). Phần còn lại của deep link giữ nguyên; không thêm mục history | `login-notices.spec.ts` (`/work/` và `/work/projects?q=DEV-001&signed_out=1`); `projects.spec.ts` live (đăng xuất thật hiện thông báo, URL `/work/`) |
| L05 | `onKeyDown`/`onKeyUp` của ô mật khẩu đọc `getModifierState('CapsLock')`, `onBlur` ẩn; vùng `aria-live="polite"` luôn có trong DOM | T06 |
| L06 | Khi mount, focus ô tên đăng nhập nếu chưa có phần tử nào giữ focus; lỗi vẫn nhận focus như cũ | T04; T02 (alert giữ focus) |
| L07 | `.tp-login-language` bỏ viền trái, màu riêng và padding; chỉ còn chữ tĩnh | T04 |
| L08 | `cooldown`, `credentials`, `expired`, `signed_out`, `caps_lock` nguyên văn mục 6 | T01–T04, T06 |

Kết quả: typecheck đạt; Vitest 29/29; build `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; mock E2E 7/7; T11 15/15 trên runtime dev (ban đầu dừng; `dev.ps1 start` rồi `stop`, không setup/upgrade/seed). Giữ nguyên ngoài phạm vi: L04, `loginUrl()` trỏ `/web/login`, câu chữ `mfa_*`. Giới hạn: Caps Lock kiểm bằng sự kiện bàn phím tổng hợp; thông báo `role="status"` có sẵn khi trang login vừa hiện có thể không được trình đọc màn hình đọc; thông báo `expired` chỉ kiểm trên mock.

### 10.4. Review của phiên điều phối (`CHG-20261029-036`)

**Kết luận:** slice 1 `TECHNICAL_ACCEPTED` cho phạm vi test (mock và runtime dev, không người dùng thật). Không có finding P1/P2. Chưa phải business acceptance hay pilot.

**Đọc diff.** Chỉ đổi file được phép trong prompt slice 1. `custom_addons/`, OpenAPI, `odoo/`/`addons/` không bị slice này sửa; `frontend/README.md` và `openapi.generated.ts` có diff từ CTR-002a.1 trước đó. L01 so khớp đúng mảng `["Access Denied"]`, câu chữ cố định, không đọc `message`/`debug`. L02 cờ chỉ ở biến module, bật khi query `session` đi từ có người dùng sang `null`, tắt khi `clear` hoặc có session lại. L03 giá trị `redirect` cố định, chỉ xóa `signed_out` và giữ phần còn lại của URL. L05 chỉ đọc `getModifierState`, vùng `aria-live` luôn có trong DOM. L06, L07 đúng đặc tả. L04 và câu chữ `mfa_*` giữ nguyên cho slice 2.

**Chạy lại độc lập.** `npm.cmd run typecheck --prefix frontend` đạt; `npm.cmd test --prefix frontend` 4 file/29 test đạt; build với `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; `login-notices.spec.ts` 7/7 đạt khi không có Odoo. Ba ca cũ trong `login.spec.ts` (`:4`, `:55`, `:82`) không chạy được khi thiếu Odoo vì `/api/v1/me` lỗi kết nối nên app hiện màn “Chưa kết nối được hệ thống” thay vì form; đây là phụ thuộc môi trường có từ AUTH-001, không phải hồi quy. Runtime dev ban đầu dừng; `dev.ps1 start` (không setup/upgrade/seed), chạy `login-notices`, `login.spec.ts`, `projects.spec.ts`: 15/15 đạt; `dev.ps1 stop`, `status` xác nhận Odoo và PostgreSQL đã dừng.

| Mã | Mức | Ghi nhận | Xử lý |
| --- | --- | --- | --- |
| R1 | P3 | L03 gọi `navigate(..., { replace: true })` rồi `history.replaceState` thủ công để giữ `/work/` có `/` cuối; phụ thuộc cách React Router ghi URL gốc | Chấp nhận; `login-notices.spec.ts` và `projects.spec.ts` bắt nếu nâng React Router làm đổi hành vi |
| R2 | P3 | Thông báo `expired`/`signed_out` (`role="status"`) có sẵn khi trang vừa hiện nên trình đọc màn hình có thể không đọc | Theo dõi khi kiểm accessibility; không chặn slice 2 |
| R3 | P3 | Caps Lock chỉ cập nhật khi có phím trong ô mật khẩu và chỉ kiểm bằng sự kiện tổng hợp | Đúng L05; kiểm tay trên máy thật khi nghiệm thu giao diện |
| R4 | P3 | L01 dựa vào chuỗi mặc định không dịch `Access Denied` của Odoo; T01 chỉ kiểm bằng mock | T09 live ở slice 2 kiểm lại với Odoo thật; nâng cấp Odoo phải chạy lại T01/T09 |
| R5 | P3 | Thông báo `expired` trước đây chỉ kiểm trên mock; ca kiểm bổ sung CHG-037 đã xác nhận câu chữ và deep link trên runtime dev với cookie bị xóa | Đã xử lý trong phạm vi test; T05 đầy đủ và live 2FA vẫn thuộc slice 2 |

### 10.5. Kiểm bổ sung live expiry notice (`CHG-20261029-037`)

Phiên điều phối không sửa application code. Trên runtime dev bật tạm cho kiểm tra, ca Playwright cô lập đăng nhập actor fixture, xóa cookie rồi gọi làm mới danh sách dự án: request `/api/v1/projects` trả `401`; trang login hiện nguyên văn `Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.`, xóa card dự án, giữ deep link `/work/projects?q=DEV-001`, storage vẫn trống, `/api/v1/me` trả `401`; đăng nhập lại quay về đúng deep link. Kết quả **1/1 đạt**. Runtime được dừng sau ca kiểm tra. Đây là bằng chứng kỹ thuật bổ sung cho R5, không thay business acceptance/pilot và không mở slice 2.

Audit bổ sung trong CHG-037 phát hiện P2 của L02: callback `QueryCache.onError` chỉ nhận 401 từ query; các action POST/PATCH qua `useWorkflowAction` giữ màn hình hồ sơ và chỉ hiện lỗi form. Regression đã tái hiện fail trước sửa. Correction trong cùng batch đã xử lý, xem mục 10.6; kết luận `NEEDS_FIX` tạm thời được thay bằng `TECHNICAL_ACCEPTED` phạm vi test sau kiểm lại.

### 10.6. Correction và kiểm lại L02 (`CHG-20261029-037`)

Người dùng trực tiếp yêu cầu tiếp quản kiểm tra và hoàn thiện phần Claude đang làm. Trong batch này, implementation subagent chỉ sửa `frontend/src/app/providers.tsx` và thêm `frontend/tests/e2e/session-mutation-401.spec.ts`; phiên chính review diff/test, không đổi vai trò dài hạn hoặc mở slice 2.

- Handler chung chỉ nhận `ApiError` có `status === 401`: hủy query đang chạy, xóa query nghiệp vụ, đặt query session về `null`. QueryCache và MutationCache cùng dùng handler; cờ `expired` tiếp tục chỉ nằm trong bộ nhớ. Không tự retry/replay mutation.
- POST và PATCH 401 được kiểm qua UI: hiện login/expired, bỏ nội dung hồ sơ cũ, giữ deep link gồm query/hash, đăng nhập lại refetch revision mới; mutation chỉ gọi một lần. Các lỗi 403/409/422/503 giữ workspace và lỗi hiện có.
- Regression mới đã fail trước sửa. Sau sửa, phiên chính chạy lại typecheck, build và 29 Vitest đạt; 16 mock E2E (6 ca mutation, 7 login-notices, 3 contract-workflow) đạt; 8 hồi quy live login/projects đạt. Ca live query expiry mục 10.5 đạt 1/1. Runtime dev ban đầu/cuối cùng đều dừng; không setup/upgrade/seed, không cài addon. Odoo tests không chạy vì không sửa Python/backend.

**Kết luận:** P2 đã sửa, slice 1 `TECHNICAL_ACCEPTED` phạm vi test; R5 có bằng chứng live trên dev, R1–R4 vẫn theo dõi. T05 đầy đủ, T07–T10/T12 và native 2FA vẫn thuộc slice 2; không suy từ correction này thành business acceptance/pilot.

### 10.7. Bàn giao slice 2 (`CHG-20261029-038`, `IMPLEMENTED_PENDING_AUDIT`)

Lượt `CHG-20261029-038` (AUTH-002 slice 2, `IMPLEMENTED_PENDING_AUDIT`, AUTH-002-SPEC v0.6): gate đầu vào đạt — slice 1 đã bàn giao/review CHG-037, checker PASS, không checkpoint mở; người dùng giao batch slice 2. Addon `custom_addons/tp_web_login/` có manifest Odoo 20/LGPL-3 (depends web/auth_totp/auth_signup), QWeb, CSS bundle riêng `tp_web_login.assets_login`, dữ liệu `noupdate` D6-a và 3 HttpCase; không model/controller/route mới. Layout chỉ áp thương hiệu/asset khi path là `/web/login` hoặc `/web/login/totp`, giữ Manage Databases theo cấu hình, captcha/passkey/CSRF/cooldown/session native. TOTP dùng chữ Việt cố định cả khi Accept-Language tiếng Anh, lỗi cố định thay chuỗi server, Hủy POST có CSRF và `redirect=/work/`. Font hệ thống (`system-ui`, Segoe UI, sans-serif) hỗ trợ tiếng Việt, không CDN/không thêm font asset. `frontend/src/shared/api/session.tsx` thêm `totpLoginUrl()`, chỉ dùng redirect từ location có path `/work/`, giữ query/hash và link native/passkey `/web/login`; `LoginPage.tsx` dùng đúng câu `mfa_*`. `frontend/tests/e2e/login.spec.ts` chuyển toàn bộ 5 ca sang mock giả lập, không đọc credential dev; thêm `frontend/tests/e2e/auth002-live.spec.ts` opt-in kiểm T05/T08/T09/T12 với guard database/origin/marker, TOTP sinh trong test, trace/video/screenshot tắt.

**Test thực chạy CHG-038:** `npm.cmd run typecheck --prefix frontend` PASS; `npm.cmd test --prefix frontend` PASS 4 file/29 test; build với `VITE_ODOO_DATABASE=tp_tanphat_dev` PASS (chỉ build frontend); Ruff addon PASS; compileall/XML PASS; E2E TypeScript compile và Playwright collection PASS. T07: toàn bộ `login.spec.ts` mock 5/5 đạt, kiểm cùng origin, redirect `/work/`, deep link, F8 vẫn `/web/login` và xóa mật khẩu. T10: Odoo HttpCase trên `tp_tanphat_auth002_verify` có HTTP, summary thật `0 failed, 0 error(s) of 3 tests`, không skip; stats phụ có setup/teardown không tính thành 5 test. Live opt-in `auth002-live.spec.ts` 3/3 đạt, không skip: T05 đăng xuất/notice/URL sạch/me401/đăng nhập lại deep link; T08 browser en-US, mã sai/lỗi cố định/mã đúng/deep link/Hủy/me401; T09 sai 3 lần, mật khẩu đúng bị cooldown, hết 20 giây đăng nhập được; T12 credential/mã/session không có trong URL/storage. Native Odoo có key storage không nhạy cảm, test chỉ cấm secret/session theo yêu cầu. Lần đầu gặp ParseError xpath class động, đã correction và chạy lại; T07 thêm mở details trước kiểm F8, live storage assertion ban đầu quá rộng đã sửa. Phát hiện asset static không được Vite mặc định proxy đã sửa bằng bundle `/web/assets`, chạy lại T10/live sau correction cuối, không sửa vite.config.

**Môi trường/runtime CHG-038:** C01/FND-002 chưa bàn giao/technical accepted, dùng helper `.local/auth002-verify/` ngoài Git. Test DB `tp_tanphat_auth002_verify`, Odoo origin `http://127.0.0.1:18099`, PostgreSQL `55432`, dbfilter khớp duy nhất và list_db=False; fixture `auth002.verify.*`. Runtime đầu: dev Odoo 18069 (PID18416), PostgreSQL55432 (PID12340) và Vite4173 (PID23008) đã chạy; không sở hữu nên không dừng. Frontend test dùng Vite4174/config local riêng; cấu hình cuối chỉ đổi cổng, không thêm proxy static. Runtime sau: Odoo verify18099 và Vite4174 do batch khởi động đã dừng; dev18069/PG55432/Vite4173 giữ nguyên. Không drop/reset DB; DB verify còn để chạy lại. Không cài/upgrade/seed `tp_tanphat_dev` hoặc `tp_tanphat_test`; đối chiếu dev xác nhận `tp_web_login` chưa cài và digest tham số auth không đổi. Không commit/push/deploy.

**Giới hạn CHG-038:** passkey và nhớ thiết bị mới kiểm bảo toàn DOM/field, chưa kiểm ceremony passkey/trusted-device bằng trình duyệt thật. Header chống nhúng trang mã, HTTPS/proxy_mode/list_db/staging thuộc C06; addon chưa vào dev.MODULES và chưa cài trên dev. Không thay quyết định D1–D6, endpoint hoặc quyền/state nghiệp vụ. Next action: phiên điều phối audit độc lập diff và bằng chứng CHG-038, kết luận cho slice 2; chưa tự ghi TECHNICAL_ACCEPTED/business acceptance/pilot.

## 11. Ngoài phạm vi

- Tự đặt lại mật khẩu qua email (D1-b), đăng ký tài khoản, SSO/OAuth Google/Microsoft.
- Tự xây màn hình nhập mã 2FA hoặc passkey trong React; “ghi nhớ mật khẩu” tự làm; lưu token ở frontend.
- Thiết lập 2FA cho người dùng, chính sách bắt buộc 2FA, đổi thời hạn nhớ thiết bị (D2-b/c).
- Đa ngôn ngữ cho trang React; thiết kế lại bố cục hoặc hình minh họa.
- HTTPS, `proxy_mode`, `list_db`, cookie Secure/SameSite ở môi trường thật — thuộc C06/OPS-002.
- Giữ dữ liệu form chưa lưu khi hết phiên (xem mục 2).

## 12. Rủi ro và giới hạn

| Rủi ro | Ảnh hưởng | Xử lý |
| --- | --- | --- |
| Cooldown của Odoo đếm theo IP trong bộ nhớ từng worker (đã xác nhận ở V-B: lần sai của hai tài khoản cộng dồn cùng IP) | Sau reverse proxy chưa bật `proxy_mode`, mọi người dùng chung IP proxy: một người gõ sai có thể làm cả công ty bị khóa tạm. Odoo tự cảnh báo khi IP bị khóa là IP nội bộ (`res_users.py` 1373–1381) | Ghi vào C06: bật `proxy_mode` và cấu hình header proxy đúng; kiểm lại T09 trên staging |
| Trang `/web/login/totp` không có `X-Frame-Options`/CSP (V-A) | Trang nhập mã có thể bị nhúng khung (clickjacking); mức thấp vì chỉ hiện khi trình duyệt đã có `pre_uid` | C06: reverse proxy thêm `frame-ancestors 'self'` hoặc `X-Frame-Options: SAMEORIGIN` cho mọi trang `/web/login*`; T10 trên staging kiểm header. Không thêm controller vào `tp_web_login` nếu người dùng chưa chọn |
| Link 2FA trực tiếp cần session biết database trước `finalize` | Odoo chưa ghi `session.db` khi trả `uid: null`; V-A đạt vì `dbfilter` chọn đúng một database. Môi trường cho chọn nhiều database sẽ không mở được trang mã | Giữ một database/`dbfilter` cho mỗi môi trường (đúng nguyên tắc AGENTS.md mục 3); ghi vào C06 |
| Tự đăng ký và đặt lại mật khẩu đang bật mặc định (G7) | Người ngoài tạo tài khoản portal; luồng email không có máy chủ mail | D6-a tắt bằng tham số khi cài `tp_web_login`. Quản trị viên vẫn bật lại được trong Settings và database chưa cài addon vẫn mở, nên checklist C06 phải kiểm hai tham số trên từng môi trường |
| Nâng cấp Odoo đổi template login/2FA | Override vỡ hoặc mất field | T10 bắt hồi quy; kế thừa bằng xpath tối thiểu |
| Bản dịch `vi_VN` của Odoo thiếu và trang theo ngôn ngữ trình duyệt (V-A/V-C) | Trang 2FA lẫn tiếng Anh nếu dựa vào bản dịch | L10 viết chữ cố định; T08 kiểm với trình duyệt tiếng Anh |
| Đóng gói font | Tăng kích thước asset | Chỉ các weight đang dùng (400/600/700) hoặc font hệ thống |

## 13. Truy vết

| Khoảng trống | Yêu cầu | Ca nghiệm thu |
| --- | --- | --- |
| G1 nhập mật khẩu hai lần | L04 (V-A) | T07, T08 |
| G2 thương hiệu Odoo, tiếng Anh | L09, L10, L12 (V-C) | T08, T10 |
| G3 hủy 2FA rơi ra Odoo | L11 | T08 |
| G4 khóa tạm báo nhầm sai mật khẩu | L01 (V-B) | T01, T02, T09 |
| G5 hết phiên/đăng xuất không thông báo | L02, L03 | T03, T05 |
| G6 Caps Lock, focus, nhãn ngôn ngữ | L05, L06, L07 | T04, T06, T11 |
| G7 tự đăng ký/đặt lại mật khẩu mở | D6-a (mục 3.1), L12 | T10 |
| Bảo mật chung | Mục 7 | T10, T12 |

## 14. Bước tiếp theo

1. ~~Người dùng chọn D1–D5~~ — xong 29/10/2026 (v0.2, `CHG-20261029-030`): chốt toàn bộ mặc định.
2. ~~Chạy V-A…V-C~~ — xong 29/10/2026 (v0.3, `CHG-20261029-031`): V-A đạt, V-B phân biệt được, V-C có kết luận (mục 8.2).
3. ~~Người dùng chọn D6 và duyệt câu chữ 6.1~~ — xong 29/10/2026: D6-a (v0.4, `CHG-20261029-032`), 6.1 nguyên văn (v0.5, `CHG-20261029-033`).
4. ~~Người dùng chọn chuyển slice sang `READY_FOR_TEST_CODE`~~ — xong 29/10/2026 (v0.6, `CHG-20261029-034`): chuyển cả hai; prompt ở mục 10.2.
5. ~~Người dùng giao prompt slice 1 cho một phiên Claude~~ — xong 29/10/2026 (`CHG-20261029-035`, mục 10.3); review CHG-036 và audit/correction CHG-037 giữ `TECHNICAL_ACCEPTED` phạm vi test. P2 mutation 401 và gap R5 đã xử lý; R1–R4 còn theo dõi.
6. ~~Người dùng giao [prompt slice 2](../prompts/CLAUDE_AUTH002_S2_NATIVE_LOGIN.md)~~ — đã triển khai/test CHG-038 trên database test cô lập (mục 10.7), `IMPLEMENTED_PENDING_AUDIT`. Phiên điều phối audit độc lập rồi ghi verdict cho slice 2.
7. AUTH-002 độc lập với Q1–Q14 và có thể chạy song song C01; không mở pilot hay người dùng thật.
