# UI-HOME-002 — Acceptance và evidence

Ngày 07/11/2026, Asia/Saigon. CHG-20261107-004. [Thiết kế](../ui/UI_HOME_002_DESIGN.md). Trạng thái: `IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT`; `tp_web_home` 20.0.1.2.0 trên dev 18069. Đây là kết quả tự kiểm kỹ thuật; audit độc lập, nghiệp vụ và pilot riêng.

## Ma trận trước implementation

| ID | Kiểm tra | Bằng chứng/kết quả |
| --- | --- | --- |
| H01 | Bốn khu theo menu quyền; KH-KD chỉ hiện khi có; không app giả/trùng; app chưa biết được giữ | PASS: admin 17, KH-KD 13; fixture internal 2 app không workspace. HOOT kiểm 4 khu, shared action giữ menu riêng, dedup menu ID và unknown; browser route fixture tên dài/app lạ giữ URL Contacts. |
| H02 | TP Projects / TP Contracts / Công việc dự án có mô tả, action/path/context đúng | PASS: href từng actor trước=sau, mở3 native view, toàn bộ payload menu admin/KH-KD trước=sau; action definitions không sửa. KH-KD sidebar/Tổng quan giữ mở qua tile/Enter. |
| H03 | Admin, manager fixture, KH-KD, internal không workspace, portal/public | PASS: browser 4 actor clone, admin/KH-KD dev; Odoo guard public→login, portal không backend, internal được Home. Fixture riêng chỉ trên clone, không sửa nhóm user sẵn có. |
| H04 | Search có/không dấu/alias; Enter theo thứ tự hiển thị; Escape/xóa/empty/IME | PASS:12 từ khóa (`du an`, `dự án`, `project`, `hop dong`, `contracts`, `crm`, `invoice`, `nhan su`, `hr`, `khkd`, `lich`, `todo`), empty/xóa/Escape, Enter đầu KH-KD và composition Enter không điều hướng. |
| H05 | Session mới chờ fresh menu; lỗi khác empty; retry; đổi user cùng browser/công ty | PASS: HOOT deferred/reject không tile cached; browser 503 ở refresh Home→error/retry; admin logout→internal cùng cache không flash admin/KH-KD; manager đổi công ty fixture giữ menu đúng. |
| H06 | Click/keyboard/Ctrl/tab mới; Home/app switcher/history/deep link/refresh/Home Action | PASS: click/native service; Tab/Enter; Ctrl-click tab mới; app switcher/Home; Back/Forward/refresh; Home Action Discuss của fixture giữ khi vào `/odoo`. Cmd/Shift/middle được giữ qua nhánh native modified-click, không có máy macOS để kiểm thực tế. |
| H07 | Form chưa hợp lệ giữ native guard trước rời; thao tác ghi test chỉ clone | PASS: Contacts new form nhập email nhưng thiếu tên→Home vẫn giữ form và báo invalid; không lưu hồ sơ. Không chạy bước này trên dev. |
| H08 | 360/390/768/1024/1280/1440/1920, zoom125/150, touch/keyboard/reduced motion; không tràn ngang | PASS:7 viewport clone + dev; Chromium page zoom thật qua settings, DPR 1.25/1.5 (CSS width 1131/943); Home/page không tràn ngang; target >=44px; reduced transition 0s. |
| H09 | Cuộn tới khu cuối; không autofocus mobile; không style leak KH-KD/list/form/native navbar | PASS: cuộn chạm khu system mọi viewport; không autofocus; token Home không xuất hiện ở3 app native; drawer mobile Escape/focus giữ; ảnh KH-KD và navbar nguyên. |
| H10 | Icon/assets không 404 mới, fallback không lặp, không console error mới; ảnh admin/KH-KD desktop/mobile | PASS:4 SVG local và icon native; HOOT + route fixture broken image→monogram; tên dài360không tràn.0 lỗi ngoài tình huống chủ động HTTP 503. Ảnh trước/sau/admin/KH-KD đủ. |
| H11 | Odoo/HOOT/XML/JS/SCSS/Ruff và regression KH-KD | PASS:Odoo 11/11; HOOT 19/19, 84 assertions; browser clone 90/90,dev 73/73; Ruff/XML/SVG/JSparse đạt. Không chạy lại toàn bộ nghiệp vụ KD do Home không sửa addon đó. |
| H12 | Clone isolated + snapshot restore; backup verify trước áp; dữ liệu/quyền/Home Action giữ nguyên | PASS:576 table exact restore/269 blob ref; backup112 checksum; apply rc 0; 34 bảng 1.402 dòng nghiệp vụ/user/groups/Home Action giữ; 908 ACL/domain và 4 bảng group relation kiểm riêng; 93 module installed trước=sau. |
| H13 | Dev chỉ smoke đọc; HTTP 200; status/changelog/roadmap/guide/checker đầy đủ | PASS:dev 73read/navigationchecks; HTTP 200, Odoo riêng được restart, PG/clone khác không đổi PID. Tài liệu/status/roadmap/changelog cập nhật cùng CHG004; checker trong AI_WORKFLOW_STATE. |

Evidence private ở `.local/ui-home002/`. Không ghi credential hoặc payload dữ liệu vào Git. Kết quả tự kiểm kỹ thuật không thay audit độc lập/nghiệp vụ/pilot.

## Lệnh và evidence

| Lệnh | Kết quả / log trong `.local/ui-home002/` |
| --- | --- |
| `.venv/Scripts/python.exe scripts/ui_home002.py prepare` | `snapshot-20261107T044513Z`; source/config/data/DB riêng cổng 18589; restore576 table và 269 blob reference bằng nguồn |
| `scripts/ui_home002.py test` (chạy bằng Python venv) | Baseline11/11 `20261107T044639952672Z`; bản cuối11/11 `odoo-tests/20261107T050148959050Z.log` |
| `node scripts/ui_home002_ui.cjs clone hoot` | `shots/clone-hoot/console.txt`:19 tests, 84 assertions,Test suite succeeded; result có source hash |
| `node scripts/ui_home002_ui.cjs clone after` | `shots/clone-after/result.json`:90/90,errors=[]; source hash bằng Odoo-tested-source và bản áp dev |
| `scripts/ui_home002.py backup` | `backup-pre-apply-20261107T050542Z`:112 file checksum, 576 table, 269 attachment,pg_restorelist đạt,dev không dừng khi backup |
| `scripts/ui_home002.py apply` | `dev-apply-20261107T050559Z.log`;rc 0, 0 error,changed_tables={}; chỉ -u tp_web_home. Source main so snapshot để chặn ghi đè sửa đồng thời; app/module không cài thêm |
| `node scripts/ui_home002_ui.cjs dev verify` | `shots/dev-verify/result.json`:73/73,errors=[]; chỉ đọc/điều hướng, 0 fixture/seed/cleanup dev |
| `scripts/ui_home002.py preserve-before / preserve-after` | `preservation-result.json`:34 bảng 1.402 dòng giữ; loại write_uid/write_date do metadata upgrade. `security-preservation.json`:908 dòng ir_access và 4 bảng group relation giữ; ACL chỉ đổi metadata ghi, không đổi domain/group/operation |
| Module/menu comparison | `modules-after.json`:93 installed,states bằng trước,Home 20.0.1.2.0; toàn bộHTTP menu payload admin/KH-KD trước=sau |

Odoo 20 dùng `ir_access` (ACL kèm domain), không có `ir_model_access`/`ir_rule` trong database này. Đã đối chiếu trực tiếp nội dung COPY `ir_access` trong dump backup với runtime sau áp (bỏ write_uid/write_date); không suy quyền bảo toàn chỉ từ số dòng. Các bảng group action/view/field so fingerprint nguyên bảng với backup.

Runtime cuối: dev 18069 wrapperPID 20044/listener 28732; PG 55432 PID 4228; clone 18169PID 27568, 18269PID 2232, 18489PID 24164 giữ nguyên. Clone18589 dành riêng UI-HOME-002 (listener 23244). Không dùng `dev.py stop`, không commit/push.

## Ảnh

| Vai trò / màn | Trước | Sau trên dev |
| --- | --- | --- |
| Admin desktop | [Ảnh trước](../../.local/ui-home002/shots/clone-before/admin-desktop-1440.png) | [Đủ bốn khu](../../.local/ui-home002/shots/dev-verify/admin-desktop-full.png) |
| Admin mobile | [Ảnh trước](../../.local/ui-home002/shots/clone-before/admin-mobile-full.png) | [Ảnh sau](../../.local/ui-home002/shots/dev-verify/admin-mobile-full.png) |
| KH-KD desktop | [Ảnh trước](../../.local/ui-home002/shots/clone-before/kd-desktop-1440.png) | [Ảnh sau](../../.local/ui-home002/shots/dev-verify/kd-desktop-full.png) |
| KH-KD mobile | [Ảnh trước](../../.local/ui-home002/shots/clone-before/kd-mobile-full.png) | [Ảnh sau](../../.local/ui-home002/shots/dev-verify/kd-mobile-full.png) |

Ảnh khác: `shots/clone-after/employee-desktop.png` (không workspace), `manager-desktop.png`, `menu-error.png`, `unknown-long-name-fallback-360.png`, `unsaved-native-guard.png`, `admin-top-*`, `admin-bottom-*`, `admin-zoom-125/150.png`. Đã xem trực tiếp ảnh desktop/mobile, cuối trang360 và userkhông workspace. Ảnh private ngoàiGit, chỉ có trên máy bàn giao.

## Sửa trong kiểm thử và giới hạn

- Lần Odoo đầu của bản sửa fail1 test vì Sass nội bộ đánh giá `min(px,%)`; sửa thành CSSmin giữ nguyên bằng `unquote`, chạy lại xanh. Không áp bản lỗi lên dev.
- HOOT lần đầu18 pass/1 fail vì test mới gọi service trước khi tạo test app; thêm `makeTestApp`, 19 pass. Browser harness sửa chờ reactive render/tab mới và selector drawer đúng; bản cuối90 pass.
- Log Odoo có INFO filestoreGC `WinError5` với blobread-only trong clone như baseline Windows; không lỗi test ở bản cuối. Không xóa blob nghiệp vụ.
- Browser Chromium:mobile/touch là emulation, chưa Safari/macOS/thiết bị thật. Không đổi dark theme toàn hệ thống. Không coi UI-HOME-002 là audit độc lập/nghiệp vụ/pilot của KD hay module khác.

## Rollback và dùng

Đã giữ source/cấu hình/DB/filestore backup. Rollback delta giao diện: `.venv/Scripts/python.exe scripts/ui_home002.py rollback` khôi phục riêng `tp_web_home` từ snapshot trước sửa và upgrade module; giữ các dữ liệu hiện có, không gỡ addon hoặc restore toàn DB. Tooling kế thừa ownership guard Odoo riêng. Chưa chủ động chạy rollback trêndev sau bàn giao vì sẽ gỡ kết quả vừa áp; không tuyên bố đã diễn tập thao tác rollback delta lần này.

Người dùng kiểm theo [7 bước](UI_HOME_002_USER_GUIDE.md#kiểm-tra-nhanh-trong-7-bước). Next: Ctrl+F5 Trang chủ, kiểm theo vai trò và phản hồi trong batch riêng; audit độc lập/business/pilot tiếp tục riêng.
