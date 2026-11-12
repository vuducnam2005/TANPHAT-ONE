# UI-SHELL-AUTH-001 — Navbar và xác thực native

CHG-20261109-002, 09/11/2026 (Asia/Saigon). Trạng thái:
`IMPLEMENTED_VERIFIED_DEV_PENDING_VISUAL_FEEDBACK`.
Đã áp dev18069 / `tp_tanphat_dev`: Home **20.0.1.4.0**, Login **20.0.1.1.0**.
Đây là tự kiểm kỹ thuật; chưa phải audit độc lập, người dùng chấp nhận hình thức,
nghiệm thu AUTH-002/C01 hoặc business/pilot.

[Thiết kế/inventory](../ui/UI_SHELL_AUTH_001_DESIGN.md),
[hướng dẫn5bước và rollback](UI_SHELL_AUTH_001_USER_GUIDE.md),
[gallery trước–sau local](../../.local/ui-shell-auth001/comparison/index.html).
Ảnh/session/danh tính/backup/log giữ trong `.local/ui-shell-auth001/` ignored,
ACL owner/SYSTEM/Administrators; không credential vào Git. Source cuối có hash
trong `sealed-source.json`; Odoo và browser clone cùng hash, dev bằng seal.

## Kết quả A01–A12

| ID | Actual result và phạm vi | Evidence private |
| --- | --- | --- |
| A01 | Đạt: navbar navy56px, wordmark/nhịp cầu local, app hiện tại theo native, Home duy nhất. Sáu actor admin/head/deputy/project_lead/planning/support. | `clone-browser.json`, `dev-browser.json`; `shots/before` / `shots/dev/home-1440.png`, `overview-1440.png` |
| A02 | Đạt: apps dropdown, sections Project và More Settings768, systray tin nhắn/hoạt động mở–đóng, user preferences/logout native. Company một công ty theo dữ liệu hiện hữu, title đầy đủ/ellipsis; không tạo công ty để test. Dirty form clone vẫn bị native validation chặn rời Home; discard được. | `zoom-result.json`, `extra-result.json`, `details-clone.json`, `details-dev.json`; `settings-more.png`, `dirty-home.png`, `*-user-menu.png` |
| A03 | Đạt: Home, KH-KD overview/list/form, rail/drawer, Project native. Sáu actor giữ menu và scope hiện có; burger/drawer Escape trả focus. Không đổi grant để đủ menu. | Hai browser reports; `rail.png`, `list-1440.png`, `form-1440.png`, `native-project.png` |
| A04 | Đạt: desktop45/55, form440px với nhãn ngoài; mobile một cột/nhận diện gọn. Tiếng Việt/branding cho login/chooser/TOTP và signup/reset khi policy đang bật. | `login-1440/1280/768/390/320.png`, `signup-1440/390.png`, `reset-1440/390.png` |
| A05 | Đạt:0/1/nhiều remembered account native; chọn chỉ điền login, mật khẩu trống; xóa một/hết/đổi tài khoản; tên dài wrap, avatar hỏng lộ fallback, remove là button riêng/keyboard. Synthetic remembered entries chỉ trong browser test riêng, không tạo user dev. | Browser reports + `details-*.json`, `chooser-1440/390/320.png` |
| A06 | Đạt: form POST/CSRF/redirect/captcha/required/autocomplete giữ; Enter, show/hide+ARIA, sai mật khẩu generic, retry/loading, lỗi mạng/phục hồi, chặn submit trùng. Password manager hook giữ theo source/DOM; chưa kiểm UI của phần mềm quản lý mật khẩu cụ thể. | Odoo Login5; `extra-result.json`15kiểm; browser reports; `login-error.png` |
| A07 | Đạt trên clone: TOTP đúng/sai/hủy, đúngUID/deep link; remember giữ HttpOnly/SameSite trusted-device cookie và lần sau không hỏi mã. Hủy POST+CSRF về `/web/login`. Passkey đăng ký và đăng nhập native thật bằng Chromium CDP virtual authenticator, đúngUID. | `clone-browser.json`, `passkey-result.json`6bước/1credential; `totp-1440/390.png`, `totp-error.png`; actor synthetic chỉ clone |
| A08 | Đạt: sáu actor login/logout thật, native POST logout; `/api/v1/me`401, Back/refresh/deep link không có phiên bảo vệ. Phiên bị kết thúc giữa chừng trở về auth. Mobile avatar mở burger account menu và logout native401. Service-worker/PWA callback source giữ nguyên; chưa chạy scoped PWA cài độc lập. | Browser reports, `extra-result.json`, `details-*.json`; `logout.png`, `mobile-user-menu.png` |
| A09 | Đạt phạm vi UI: install/upgrade giữ toàn config, cả key signup/reset vắng và giá trị disabled. Native CSRF sai400, redirect nội bộ giữ, domain ngoài không trở thành redirect ngoài. Signup/reset GET thật trên clone/dev, native forms giữ; không gửi mail/đăng ký account trên dev. `auth_oauth` và `website` uninstalled: OAuth N/A, chưa kiểm provider. Rate-limit/captcha/cookie/headers/list_db không đổi; không gọi đây là audit các cơ chế đó. | `policy-result.json`, Odoo HttpCase, `final-preservation-result.json`; AUTH-002 cũ giữ riêng |
| A10 | Đạt:1440×900/1280×800/768×1024/390×844/320px, Tab/Enter/Escape, hover rõ, animation180ms và reduced motion, không tràn ngang. Chromium zoom thật200% tại login/Home/KH-KD/Project, menu More thật. Text phụ4,56:1 trên nền; placeholder cuối4,94:1 trắng; nút trắng/xanh6,88:1. Lượt cuối không console/pageerror hoặc lỗi asset. | `zoom-result.json`5kiểm; `details-*.json`18kiểm mỗi môi trường; `*-real-zoom200.png` |
| A11 | Đạt: clone owned19189 neutralized/source/config/filestore riêng; restore ban đầu576bảng/294reference. Backup mới nhất122file checksum, dump đọc được, restore576bảng/295reference trước apply cuối. Source test=seal=dev;267bảng/8.144dòng business/security/account/history nguyên, config nguyên,213file addon khác nguyên, toàn blob cũ giữ/295reference hiện tại checksum+size hợp lệ. | `restore-evidence.json`, `backup-restore-result.json`, `dev-odoo-result.json`, `preservation-dev-after-browser-result.json`, `final-preservation-result.json`; giải thích concurrent avatar bên dưới |
| A12 | Đạt: UI hiện trên18069; ảnh trước–sau cùng admin/route/dataset/viewport cho navbar/login/chooser/mobile; guide5bước. Dev chạy, PG55432 giữ listenerPID13900; clone19189 đã dừng khi bàn giao, DB/source giữ để audit. | `comparison/index.html`,4ảnh so sánh; `shots/before`, `shots/dev`; guide liên kết trên |

## Test và bản source cuối

- Odoo **62/62**: Home12, Login5, Workspace45; log
  `clone-odoo-20261109T025329689307Z.log`,0failed/0error.
- Browser clone **120/120**, thêm failure/network/dirty/security15,
  zoom thật200%5, chi tiết hover/avatar/signup/reset/systray/mobile18;
  passkey6bước và policy install/upgrade riêng đạt.
- Browser dev **110/110 +18/18**, sáu actor, chỉ đọc/nghiệp vụ; lỗi mật khẩu,
  MFA fixture, dirty-form và failure injection chỉ clone. Không console/pageerror
  trong reports cuối. Dùng service worker bình thường.
- Ruff, JS syntax, XML8file, `git diff --check`, workflow finish/check theo
  CHG002. Không sửa React/core Odoo nên không chạy build React. Logic Home
  không đổi ngoài EOL; HOOT Home cũ không chạy lại cho CSS/XML shell. Logic JS
  auth mới được kiểm qua browser native/failure probes và HTTP tests.

Lệnh chính: `.venv/Scripts/python.exe -X utf8 scripts/ui_shell_auth001.py
test|start|seal|backup`, `apply --target dev`; `node
scripts/ui_shell_auth001_ui.cjs clone|dev`, `ui_shell_auth001_extra.cjs`,
`ui_shell_auth001_zoom.cjs`, `ui_shell_auth001_details.cjs clone|dev`.
Các file policy/fixture có owner guards; không chạy lại để ghi đè evidence.
Passkey probe và verifier bảo toàn mở rộng nằm private trong thư mục task.

## Backup, concurrent writer và những lượt không dùng làm gate

Apply đầu: backup `backup-pre-apply-20261109T024346Z`, Home upgrade/Login install
rc0,0error; config/accounts/quyền/business/nonasset attachments giữ ngay sau
upgrade. Sau đó một phiên khác lưu ảnh đại diện của chính tài khoản qua native
preferences lúc09:47:45;5attachment image1920/1024/512/256/128 thay storage bytes,
không đổi owner/link/field. Strict checker phát hiện và từ chối kết luận tất cả
attachment metadata nguyên. Đã đối chiếu delta riêng, giữ ảnh mới và blob cũ,
không restore hoặc ghi đè thao tác phiên đó. Journal private
`concurrent-profile-delta.json`, `apply1-evidence/final-preservation-result.json`.

Tự kiểm cuối phát hiện placeholder3,98:1; chỉnh duy nhất màu thành
`#607287`4,94:1, chạy lại Odoo62/browser120/zoom5 trên clone. Backup mới
`backup-pre-apply-20261109T025630Z` đã chứa ảnh mới:122file/576bảng/295reference,
restore DB owned riêng (ID thực trong `backup-restore-result.json`).
Apply cuối chỉ upgrade hai addon, rc0/0error/module delta rỗng; smoke và so
baseline mới có282nonasset attachment metadata nguyên, mọi blob cũ còn.
Source cuối khóa bằng seal; không đổi password/hash/grant/Home Action/policy.

Các lượt thăm dò ban đầu có lỗi selector trang Settings, assert menu trước khi
animation mở xong, và gọi session-info khi webclient chưa khởi tạo navbar.
Harness đã chờ đúng thành phần native và chạy lại đầy đủ xanh; không dùng lượt
đỏ làm bằng chứng. Probe bổ sung đóng menu tin nhắn bằng nút native sau khi
Escape bị input tìm kiếm của menu giữ. Không sửa application code cho các lỗi
harness. Không claim source browser cũ là source cuối.

## Giới hạn và bước tiếp theo

Chưa Safari/thiết bị vật lý, scoped PWA cài độc lập, OAuth provider, mật khẩu
manager UI hoặc full multi-company switching (dev chỉ một company). Không có
audit độc lập vì spawn subagent bị lỗi model kế thừa. Chưa diễn tập rollback
dev; [runbook](UI_SHELL_AUTH_001_USER_GUIDE.md) giữ delta UI, phải đối chiếu writer.
Không commit/push, đổi API/model/security/workflow nghiệp vụ hoặc đóng gate
AUTH-002/C01/Q2/pilot. Next: người dùng Ctrl+F5 và kiểm5bước, phản hồi hình thức
navbar/login/chooser; audit độc lập tách riêng.
