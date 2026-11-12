# UI-SHELL-AUTH-001 — Thiết kế và inventory

CHG-20261109-002, 09/11/2026. Người dùng giao trực tiếp thực thi prompt, test
clone, backup verified và áp dev18069; phạm vi này chuyển từ điều phối sang thực
thi. Baseline checker CHG-20261109-001 PASS; thay đổi Git có sẵn được giữ.

## Thiết kế trước code

Navbar dùng navy #17324D, hành động #255F85, nền #F4F6F8, chữ #1F2937,
chữ phụ #607287, đường chia #D9E2EC. Font Segoe UI/system local. Thanh cao56px,
app switch native → wordmark TANPHAT ONE → app hiện tại → sections/More native
→ Home có sẵn → systray native → avatar/tên tài khoản. Thu nhãn trước trên
mobile; giữ user menu trực tiếp, burger và sidebar KH-KD. Company ellipsis/title.
Không copy NavBar/adapt, logout callback hay thay wrapper grid.

Login desktop là mặt phẳng hai vùng45/55: navy bên trái với wordmark, câu
“Không gian làm việc chung”, hình nhịp cầu SVG local; vùng phải nền nhạt, form
440px và tiêu đề theo bước. Mobile nhận diện gọn phía trên, form một cột,
không banner lớn. Đây là thay đổi bố cục, không chỉ đổi màu card cũ.

Chooser dùng dữ liệu remembered users native, hàng chọn và nút bỏ riêng,
fallback chữ cái khi avatar lỗi; Portal về label native. Login/TOTP/signup/reset
giữ form và handler native, CSRF/redirect/captcha/passkey/OAuth. Nhãn tiếng Việt,
hiện/ẩn mật khẩu có ARIA, submit phản hồi tức thì và phục hồi. Motion180ms chỉ
hover/menu và một reveal; reduced-motion tắt motion. Focus rõ, target44px.

## Inventory và rủi ro

- Dev18069 / tp_tanphat_dev, PG55432 đang chạy. Home20.0.1.3.0 installed;
  login20.0.1.0.0 chưa cài (cần kiểm SQL trong evidence trước apply).
- Login addon cũ có data set hai auth_signup policy ở lần cài; bỏ data mutation
  khỏi manifest, giữ file lịch sử không tải. Snapshot gồm key vắng mặt và giá
  trị config để so install/upgrade. Không default setup MODULES.
- Hủy TOTP cũ về /work/; đổi hidden redirect sang /web/login, giữ POST+CSRF.
- Native UserSwitch dùng get/setLastConnectedUsers, không public danh bạ.
- Native logout gửi service worker user_logout, POST+CSRF và redirect/PWA;
  giữ callback nguyên vẹn. Không thêm auth controller hoặc JS lưu credential.
- NavBar sections đo direct children; chỉ thêm sibling wordmark và scoped CSS.
  User menu mở trên mobile cần tránh trùng menu burger nhưng giữ truy cập.

## Phạm vi file và kiểm chứng

Hai addon tp_web_home (navbar XML/SCSS) và tp_web_login (QWeb/public assets,
tests); scripts/ui_shell_auth001.py và browser harness; docs thiết kế,
acceptance, user guide, status/changelog/roadmap. Application source sửa trong
clone isolated trước, chỉ copy hai addon đúng hash đã test khi apply.

Clone riêng19189 / tp_tanphat_shellauth001_20261109, neutralized, source/config/
filestore riêng. Chụp before dev cùng role/route/viewport; chạy Odoo HTTP,
browser1440/1280/768/390/320, keyboard/reduced-motion/zoom, role và session.
Backup mới được checksum, pg_restore --list và restore vào DB riêng trước apply.
Giữ account/hash/quyền/HomeAction/assignment/business/blob/auth policy; module
delta chỉ Home upgrade + Login install. Không business writes dev.

Technical self-verification, visual acceptance, audit độc lập và business/pilot
là các kết luận riêng. Passkey nếu không thực test thì ghi NOT_TESTED.

## As-built và bảo toàn

Đã áp Home20.0.1.4.0/Login20.0.1.1.0 lên dev18069; [actual A01–A12](../demo/UI_SHELL_AUTH_001_ACCEPTANCE.md), [ảnh trước–sau](../../.local/ui-shell-auth001/comparison/index.html). Mobile dùng avatar/burger account menu native; không ép desktop UserMenu hiển thị thêm. Không thay NavBar/adapt hoặc logout callback. Auth public Interaction reuse ShowPassword với ARIA và phục hồi submit bị treo; remembered chooser chỉ extend template native, không JS đọc danh bạ. Placeholder cuối dùng #607287 trên trắng4,94:1. Form/route/token/captcha/passkey/OAuth hook giữ; signup/reset theo policy đang có. Passkey đã đăng ký/đăng nhập thật bằng virtual authenticator, TOTP/trusted-device đúng/sai/hủy đạt trên clone.

Clone62Odoo/120browser +15failure/5zoom thật/18bổ sung; dev110+18/0error. Test Home sửa assertion không cấm người quản trị đã gán Home Action từ trước; không thay Home logic hoặc user action. Exact source, fresh backup/restore và267bảng/8.144dòng/282nonasset attachment được đối chiếu sau smoke. Concurrent profile avatar trong apply đầu được giữ, backup cuối chứa ảnh mới; không business write hoặc policy/account/quyền mới. Tự kiểm và giới hạn browser/PWA/multi-company theo acceptance; không audit độc lập/business/pilot.
