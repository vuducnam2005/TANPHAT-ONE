# TANPHAT ONE — Nhật ký thay đổi

## CHG-20261125-001 — ATTENDANCE-APP-HOME-001: Sắp xếp Trang chủ 5 nhóm, đổi tên Yêu cầu phê duyệt và tách ứng dụng Chấm công riêng

- **Trang chủ & Đổi tên hiển thị** (`tp_web_home 20.0.1.13.0`, `tp_reporting/static/src/registration.js`, `tp_request 20.0.1.2.0`, `tp_equipment 20.0.1.7.1`): cố định thứ tự 5 nhóm (`Nhân sự và chấm công` → `Báo cáo và phê duyệt` → `Phòng ban và đơn vị` → `Công cụ cá nhân` → `Kho`) qua `registerHomeSection`/`registerHomeModule`, bổ sung icon `clock` & `bar-chart`, bỏ nhóm rỗng `Vận hành nội bộ`, đổi tên ứng dụng Request thành **Yêu cầu phê duyệt** đồng bộ trên toàn bộ điểm điều hướng.
- **Ứng dụng Chấm công độc lập & URL** (`tp_hr_attendance 20.0.4.0.0`, `tp_hr_workspace 20.0.1.24.0`, `tp_branding 20.0.2.3.0`): tạo menu gốc `tp_hr_attendance.menu_root`, chuyển toàn bộ menu chấm công khỏi sidebar TP HR, bổ sung `TpAttendanceSidebar` kế thừa `TpHrSidebar` với bộ nhớ `tp_att_ui:*` độc lập, chuyển tab `Công của tôi` trong Hồ sơ cá nhân sang ứng dụng Chấm công; chuẩn hóa 16 route `/app/cham-cong/...` kèm alias `/app/nhan-su/cham-cong/...` đồng bộ Python/JS; giữ nguyên dữ liệu, ENTI sync/ảnh/cron, xuất Excel, bridge Request và phân quyền 5 vai trò.
- **Kiểm thử:** `py_compile`/XML/`node --check`/`git diff --check` PASS; Odoo `tp_branding` 34/34, `tp_request` 13/13, `tp_hr_attendance` access/correction/export/image sync PASS; Playwright `1440×900` & `390×844` 8/8 PASS (0 console/OWL error).

## CHG-20261123-011 — ATTENDANCE-CORRECTION-003: Áp PC server và xác minh render public

- Commit `5a636d6a940d0e9d456240fdfa1808b20034fa70` đã push/áp PC server; `tp_hr_attendance 20.0.3.9.1`, `tp_request 20.0.1.1.1`, 11/11 source checksum khớp, upgrade exit 0/0 ERROR-CRITICAL. Backup `C:\TANPHAT-backups\attendance-correction003\corr003-20261123T171407`; snapshot nhân sự/tài khoản/quyền/ngày công/phiên/phiếu/request/base URL bất biến.
- Public health 200; F5 tải `/web/assets/062fa37/web.assets_web.min.js`; form điều chỉnh mở được, giờ mặc định đúng, nhập giờ/lý do giữ state, console 0 lỗi. Không gửi phiếu thử vào dữ liệu thật. DB test đạt thêm lost-response retry và race thật hai session; synthetic credentials đã hết hiệu lực, test listener dừng. Source drift trước deploy và giới hạn kiểm ghi tại `PROJECT_STATUS.md`.

## CHG-20261123-010 — ATTENDANCE-CORRECTION-003: Sửa lỗi OWL khi mở form điều chỉnh công

- `CorrectionFormDialog`/`WithdrawDialog` và các filter đối chiếu chuyển sang `t-model.proxy` theo OWL `3.0.0-alpha.50`; form giữ state ngày/giờ/lý do/minh chứng, lấy giờ hiện có của ngày được chọn, để trống phần thiếu và báo lỗi theo trường.
- Backend `tp_save_and_submit` dùng savepoint, token thao tác + fingerprint chống tạo phiếu trùng khi bấm kép/retry; lý do thu hồi giữ riêng trên phiếu, log diện rộng không nhận nội dung riêng tư. `tp_request` kiểm lại quyền đọc correction gốc và khóa correction trước request cho action liên kết.
- Kiểm thực: static `node --check`/`py_compile`/XML parse/`git diff --check`; Odoo `tp_tanphat_test` **0 failed, 0 error(s) of 23**; Playwright desktop/mobile minified bundle **0 page/console errors**, vòng đời gửi/trả/thu hồi/duyệt và F5 đạt; race owner thu hồi/admin duyệt đúng một thao tác thành công. Public trước sửa đã tái hiện `OwlError` `CorrectionFormDialog.slot2`; deployment PC server chờ sau commit.
- Đã áp PC server commit `5a636d6a940d0e9d456240fdfa1808b20034fa70`: `tp_hr_attendance 20.0.3.9.1`, `tp_request 20.0.1.1.1`, backup `C:\TANPHAT-backups\attendance-correction003\corr003-20261123T171407`, upgrade exit 0 và 0 ERROR/CRITICAL. Snapshot 39 nhân viên, 32 users, 897 ngày công, 851 phiên, 2 phiếu điều chỉnh và 3 request bất biến; public health 200, bundle `/web/assets/062fa37/web.assets_web.min.js`, mở form/nhập giờ+lý do đạt, console 0 lỗi.

## CHG-20261123-009 — ENTI-IMAGE-SYNC-001: Biên bản áp PC server & đồng bộ ảnh thật

- Commit `17970b9e` (`tp_hr_attendance` `20.0.3.9.0`) đã áp lên PC server (`192.168.1.73`, `tp_tanphat_dev`).
- Backup tại `C:\TANPHAT-backups\enti-image001\img001-20261123T155853\` (`tp_tanphat_dev.dump`, `restore-list.txt`, `filestore.tar.gz`, `pre_tp_hr_attendance.tar.gz`).
- SHA256 86/86 tệp khớp; `-u tp_hr_attendance` exit 0, 0 ERROR/CRITICAL; snapshot `employees=39`, `users=32`, `groups_hash`, `att_days=897`, `att_sessions=842`, `enti_days=897`, `enti_mapping=39`, `base_url` bất biến 100%.
- Thực chạy đồng bộ ảnh thật từ ENTI trên `tp_tanphat_dev`: `38/39` nhân viên có ảnh thật (`photo=38, generated=1`), `1` chưa có ảnh trên ENTI (`no_image`), `0` lỗi, `0` chưa đối chiếu, `PARTNER_MISMATCH=0`; lượt lặp lại xác nhận `unchanged=38, downloaded=0`. Public `https://tpone.tadic.vn/web/health` HTTP 200 và `/app/nhan-su/cham-cong/nguon-du-lieu` 303 về `/dang-nhap`. Bản ghi docs-only, không restart lại Odoo.

## CHG-20261123-008 — ENTI-IMAGE-SYNC-001: Đồng bộ ảnh hồ sơ nhân viên từ ENTI về TANPHAT ONE

- `custom_addons/tp_hr_attendance` **20.0.3.9.0** (`models/enti_client.py`, `models/enti_image.py`, `models/enti_mapping.py`, `models/attendance_source.py`, `models/enti_sync.py`, `security/ir.access.csv`, `views/enti_views.xml`, `static/src/sources.js`, `static/src/sources.xml`, `static/src/admin.scss`, `static/src/filter_profiles.js`, `tests/test_enti_image_sync.py`):
  - Kiểm chứng API ENTI thực tế: `/api/nhan-vien/get-info` trả trường `anh=""`, còn `/api/nhan-vien/search` trả `anh` dạng `data:image/jpeg;base64,...` cho 38/39 nhân viên. Bổ sung `EntiClient.get_employee_profiles()` và `download_image()` kiểm host allowlist, `Content-Type: image/*`, giới hạn dung lượng và retry có giới hạn.
  - Tạo model `tp.hr.attendance.enti.employee.image` (metadata sạch, `image_hash`, `state`, `image_url`/`raw_metadata_json` ẩn với người dùng thường), kiểm tra magic bytes + chuẩn hóa ảnh qua Pillow, cập nhật `hr.employee.image_1920` và `res.partner.image_1920` chỉ cho nhân viên đã đối chiếu 1-1 (`state == 'mapped'`), giữ ảnh cũ khi lỗi/trống và tôn trọng `prefer_manual_image`.
  - Tách đồng bộ ảnh thành bước 2 độc lập trong `enti_sync.py` (savepoint riêng từng nhân viên, không ảnh hưởng dữ liệu chấm công); bổ sung khu vực quản trị đồng bộ ảnh (metrics, Ưu tiên ảnh thủ công, Đồng bộ ảnh hồ sơ, Đồng bộ lại ảnh lỗi, bộ lọc Trạng thái/Phòng ban/Nhân viên, xem ảnh ENTI vs Odoo cạnh nhau).
  - Bổ sung bộ test `tests/test_enti_image_sync.py` phủ 12+ tình huống bắt buộc.
- Kiểm thử (`tp_tanphat_test` / 18079): `py_compile`, XML parse, `node --check`, `git diff --check` PASS; `/tp_hr_attendance` (`TestEntiImagePure`, `TestEntiImageSync`, `TestEntiClientFake`, `TestDirectoryPrivacy`, `TestAccess`) **25/25 PASS** (0 error, 0 fail); Playwright desktop `1440×900` & mobile `390×844` **0 pageErrors, 0 consoleErrors, docOverflow=false**.

## CHG-20261123-007 — ATTENDANCE-CORRECTION-002: Thiết kế lại luồng Đề nghị điều chỉnh công (gửi 1 chạm & thu hồi)

- `custom_addons/tp_hr_attendance` **20.0.3.8.0** (`models/attendance_correction.py`, `models/attendance_overview.py`, `views/correction_views.xml`, `security/ir.access.csv`, `static/src/mine.js`, `static/src/mine.xml`, `tests/test_correction.py`):
  - Bổ sung trạng thái `withdrawn` (**Đã thu hồi**), các trường `withdrawn_by_id`, `withdrawn_at`, `withdraw_reason`, `tp_can_withdraw`, RPC `tp_save_and_submit` (lưu + gửi duyệt trong 1 giao dịch), `action_withdraw`, `action_reopen_draft`, wizard `tp.hr.attendance.withdraw.wizard` và bus `tp_hr_attendance/correction_updated`.
  - Cập nhật **Công của tôi** với `CorrectionFormDialog` (nút chính **Gửi duyệt**, nút phụ **Lưu nháp**), `WithdrawDialog`, nút **Thu hồi đề nghị** / **Mở lại nháp** / **Tạo đề nghị mới** / **Sửa & Gửi duyệt** và tự động cập nhật qua bus.
  - Giới hạn hàng đợi **Xử lý điều chỉnh** (`action_review`) chỉ hiển thị `[('state', '=', 'submitted')]` và tự cập nhật danh sách qua bus khi người dùng gửi/thu hồi.
- `custom_addons/tp_request` (`models/attendance_bridge.py`, `models/request_record.py`): đồng bộ trạng thái `withdrawn`, `action_withdraw`, `action_reopen_draft` qua cầu nối 1-1.
- Kiểm thử (`tp_tanphat_test` / 18079): `py_compile`, `node --check`, XML parse, `git diff --check` PASS; `/tp_hr_attendance:TestAttendanceCorrection,/tp_request` 22/22 PASS; `/tp_hr_attendance:TestAttendanceAccess` 8/8 PASS.

## CHG-20261123-006 — ATTENDANCE-EXPORT-REPORT-001: Biên bản áp PC server

- Commit `2795fd7e` (`tp_hr_attendance` `20.0.3.7.0`) đã áp lên PC server (`192.168.1.73`, `tp_tanphat_dev`).
- Backup tại `C:\TANPHAT-backups\attendance-export001\exp001-20261123T110111\` (`tp_tanphat_dev.dump`, `restore-list.txt`, `filestore.tar.gz`, `source-config.tar.gz`).
- SHA256 84/84 tệp khớp; `-u tp_hr_attendance` exit 0, 0 ERROR/CRITICAL; snapshot 39 nhân viên / 32 tài khoản / 897 ngày công / 840 phiên / 35 mã máy / base URL giữ nguyên 100%.
- Đối chiếu chỉ đọc trên dữ liệu thật của server (`enti_att002_export_check.py`): 3 kỳ (1 tuần, 2 tuần, 1 tháng; 39 nhân viên) đạt `{"ok": true}` với 0 vấn đề; public `https://tpone.tadic.vn/web/health` HTTP 200 và `/app/nhan-su/cham-cong/tong-quan` 303 về `/dang-nhap`. Bản ghi docs-only, không restart lại Odoo.

## CHG-20261123-005 — ATTENDANCE-EXPORT-REPORT-001: Thiết kế lại file Excel xuất chấm công theo mẫu Report

- `custom_addons/tp_hr_attendance` **20.0.3.7.0**:
  - `models/attendance_export.py`: tái thiết kế toàn bộ trình sinh Excel thành 1 sheet duy nhất `Report` theo đúng bố cục file mẫu `202611_TP_Cham_cong_tuan_3.xlsx` (`BẢNG CÔNG THÁNG`, `Từ ngày dd/mm/yyyy - Đến ngày dd/mm/yyyy`, header 2 tầng `STT`, `Mã nhân viên`, `Tên nhân viên`, `ID`, `Chức vụ`, `Vào/Ra`, cột ngày + thứ `T2..CN`, `Đi muộn [Lần, Phút]`, `Số ngày`, `Ghi chú`), nhóm theo phòng ban, 2 dòng `Vào`/`Ra` cho mỗi nhân viên, viền mảnh đen trắng/xám rất nhạt, tự chỉnh độ rộng, freeze panes `G7`, khổ ngang A4 lặp lại dòng `5:6`, `print_area`, và dòng `Không có dữ liệu trong kỳ đã chọn` khi trống.
  - Quy tắc dữ liệu & tính toán: giờ hiển thị `HH:mm` (bỏ giây/datetime, trống nếu không có); `export_late_totals` giữ tổng hợp nguồn nếu `exact`, ngược lại lấy ENTI từng ngày hoặc tính từ giờ vào sau `08:30` (bỏ Chủ nhật, ngày nghỉ, ngày thiếu giờ vào; làm tròn nguyên phút; mặc định `0`); `worked_days_count` đếm ngày hợp lệ trong kỳ (bỏ Chủ nhật, không đếm trùng, mặc định `0`); `person_note` chỉ ghi thiếu vào/ra, bất thường, trùng cần đối chiếu, nghỉ hoặc không có dữ liệu (trống nếu bình thường).
  - `models/attendance_overview.py`: đồng bộ lọc `state` ngày cho `tp_export_sheet`, kiểm soát trùng ENTI (`_tp_duplicate_days`), chuẩn hóa tên file `Bang_cong_dd-mm-yyyy_den_dd-mm-yyyy.xlsx` / `Cong_cua_toi_dd-mm-yyyy_den_dd-mm-yyyy.xlsx`, giữ nguyên phạm vi quyền và lọc nhân viên/phòng ban.
  - `static/src/board/board.js`, `static/src/board/board.xml`: thêm trạng thái `exporting` chống bấm đúp khi xuất Excel.
  - `tests/test_upload.py`, `tests/test_enti_attendance_002.py`, `scripts/enti_att002_export_check.py`: cập nhật và bổ sung kiểm thử mẫu `Report`, quy tắc đi muộn/số ngày/ghi chú, lọc phòng ban/nhân viên/ngày/trống, bảo mật và đối chiếu 3 kỳ.
- Kiểm thử (`tp_tanphat_test` / 18079): `py_compile`, `ruff`, `node --check`, XML parse, `git diff --check` PASS; Odoo `TestAttendanceUpload,TestExportTemplate,TestExcelImportClosed` 15/15 PASS (21 tests), `TestAttendanceAccess,TestDirectoryPrivacy,TestLogic` 11/11 PASS (15 tests); `enti_att002_export_check.py` 3 kỳ (59 NV) 0 vấn đề; Playwright desktop `1440×900` & mobile `390×844` tải file từ Tổng quan/Bảng chấm công đạt 0 pageErrors.

## CHG-20261123-004 — WEBVIEW-ZALO-ERROR-GUARD-001: Biên bản áp PC server

- Commit `7749fdd1` (`tp_branding` `20.0.2.2.2`) đã áp lên PC server (`192.168.1.73`, `tp_tanphat_dev`).
- Backup tại `C:\TANPHAT-backups\webview-guard001\20261123T090926\` (`tp_tanphat_dev_pre.dump` 10.760.506 bytes, `restore-list.txt` 16.338 dòng, `tp_branding_pre.tar.gz`, `deploy_package.tar.gz`).
- SHA256 25/25 tệp khớp; `-u tp_branding` exit 0, 0 ERROR/CRITICAL; snapshot nhân sự/tài khoản/nhóm/base URL giữ nguyên.
- Public `https://tpone.tadic.vn`: `/web/health` 200, `/app/trang-chu` 303, bundle `/web/assets/66e5daf/web.assets_frontend_lazy.min.js` và `web.assets_backend` trên server đều đã có `tpExternalWebViewErrorHandler`. Bản ghi docs-only, không restart lại Odoo.

## CHG-20261123-003 — WEBVIEW-ZALO-ERROR-GUARD-001: Chặn popup lỗi zaloJSV2 do Zalo WebView tự chèn

- Khảo sát toàn bộ repository (`custom_addons/`, `addons/`, `odoo/`, `frontend/`, `docs/`) và HTML thực tế `/app/trang-chu`: 0 tham chiếu `zaloJSV2` hoặc script Zalo; lỗi phát sinh sau khi OWL WebClient/TitlePlugin mount do Zalo iOS `WKWebView` tự đánh giá `zaloJSV2` trong global scope của trang (`filename = document URL`, `lineno = 1`) khiến `error_service.js` không nhận diện là script ngoài.
- `tp_branding` **20.0.2.2.2**: thêm `static/src/webview_error_guard.js` đăng ký `tpExternalWebViewErrorHandler` (`sequence: 2`) trong `web.assets_backend` và `web.assets_frontend` (kèm `web.assets_unit_tests`). Không tạo stub giả `window.zaloJSV2`; chỉ bỏ qua `ReferenceError` về `zaloJSV2` không có frame/filename từ `.js` hay `/web/assets/`/`/static/`, giữ nguyên hiển thị cho mọi lỗi ứng dụng thật.
- Kiểm kỹ thuật (`tp_tanphat_test` / 18079): `node --check`, `py_compile`, `git diff --check` PASS; Odoo `/tp_branding` **30/30 PASS**; HOOT `@tp_branding` **5/5 PASS**; Playwright Chromium mobile (Zalo iOS UA) trên `/dang-nhap` và `/app/trang-chu` PASS. Chưa kiểm trực tiếp trên iPhone/Zalo app thật.

## CHG-20261123-002 — ATTENDANCE-SHEET-001 + TABLE-PAGE-100: Biên bản áp PC server

- Commit `71f9b8db` đã push/deploy; backup `C:\TANPHAT-backups\attendance-sheet001\attendance-sheet001-20261123T085039`; 44/44 checksum, upgrade 8 addon exit0, log0 ERROR/CRITICAL. Public health200 và route bảng công chuyển hướng đăng nhập sạch. Post-deploy fingerprint read-only giữ 39 nhân viên, 32 users, 897 ngày công/ENTI, 839 phiên, 35 mã máy và group hash. Pre-snapshot SQL bị lỗi dấu ngoặc thừa nên không dùng làm bằng chứng trước-sau tuyệt đối; backup/restore-list đã xác nhận. Browser authenticated chưa chạy. [Receipt](../.local/attendance-sheet001/deploy-result.json).


## CHG-20261123-001 — ATTENDANCE-SHEET-001 + TABLE-PAGE-100: Bảng công theo ma trận Excel và mặc định 100 mục

- Bảng quản trị chấm công dùng cùng dữ liệu canonical/ENTI hiện có, hiển thị theo nhóm phòng ban với STT, Mã nhân viên, Tên nhân viên, ID máy, Chức vụ, hai dòng Vào/Ra, ngày + thứ, Đi muộn (Lần/Phút) và Vắng mặt (Vắng). Xuất Excel thêm ID máy và giữ nhóm/hai dòng.
- Mặc định phân trang 100 cho native list/group và các màn TP HR, TP Projects, TP Equipment, TP Reporting, TP Request, Chấm công; khóa lưu cũ được đổi phiên bản. Không đổi quyền, domain, nguồn hay công thức vắng/đi muộn.
- Kiểm kỹ thuật: Python compile PASS; Node `--check` PASS; XML parse PASS; `git diff --check` PASS. Browser authenticated và PC server deploy chưa chạy trong checkpoint này.

## CHG-20261122-002 — HR-AUDIT-CLEANUP-001: Khôi phục kết nối và áp PC server

- Người dùng chạy installer public key trên PAC-PC/Admin. SSH laptop dùng khóa mới ở D:\TANPHAT-SSH, host fingerprint khớp; không đổi tên miền/tunnel/credential ứng dụng. Không đưa private key hoặc cấu hình SSH vào Git.
- Commit `76d2d504` đã push/deploy, 15/15 tệp checksum khớp, `-u tp_hr_workspace` exit0, 0 ERROR/CRITICAL; version20.0.1.22.0. Backup `C:\TANPHAT-backups\audit-cleanup001\audit-cleanup001-20261122T211031`, dump custom/pg_restore-list16.313 dòng, filestore638 mục, source/config.
- Fingerprint dữ liệu nghiệp vụ/tài khoản/quyền/audit trước-sau không đổi; 83/83 dòng audit còn active, không dọn dữ liệu thật. Probe read-only6/6 PASS, 24 dòng lý do kỹ thuật diễn giải được.
- Kiểm public bằng bundle thực: CSS `/web/assets/5623af7/web.assets_web.min.css`, JS `/web/assets/4622a0e/web.assets_web.min.js` có tiêu đề/hướng dẫn mới; health200. Backend7/7 + browser/HTTP password-confirmed cleanup trên synthetic test PASS. Không thử dọn log thật.
- Bàn giao docs-only; không restart lại chỉ để cập nhật biên bản. Checkpoint cũ/WIP báo cáo-sidebar giữ nguyên, workflow check chỉ xác nhận snapshot phát hành có phạm vi.

## CHG-20261122-001 — HR-AUDIT-CLEANUP-001: Diễn giải nhật ký và dọn danh sách bằng mật khẩu

- Yêu cầu trực tiếp ngày 22/11: giải thích lý do kỹ thuật và cho admin dọn nhật ký. Cột mới `reason_display` dịch nội dung tự sinh từ snapshot, không viết lại bằng chứng gốc. Bổ sung mã TP/mã nguồn cho audit thay đổi mới; tiêu đề bảng có ý nghĩa.
- Thêm action chọn nhiều dòng/form → wizard count + mật khẩu không lưu. Admin gốc/ủy quyền còn hiệu lực và công ty hợp lệ mới được xác nhận; kiểm danh tính qua password helper native/rate limit ở mỗi lần. RPC write/unlink trực tiếp audit vẫn bị chặn. Wizard chỉ thao tác hồ sơ do chính actor tạo.
- Gỡ là `active=False` kèm hidden_by/hidden_at. Giữ tombstone trong cùng bảng vì cấp mã dùng SQL lịch sử và import dùng `_tp_removed_identities`; không cho gỡ làm cấp lại mã hoặc tái tạo nhân viên. Retry xóa nhân viên tìm cả dòng đã gỡ.
- Backend 7/7 PASS; browser list/chọn/action/password/cancel/mobile và HTTP xác nhận mật khẩu → gỡ đúng một dòng synthetic PASS. Bằng chứng `.local/audit-cleanup001/`, không tạo dữ liệu thật trên server.
- Deploy bị chặn: không có `.ssh/config`, khóa id_ed25519/id_rsa hay ssh-agent identity. `192.168.1.73:22` trả SSH, nhưng `vuduc` bị từ chối publickey/password. Không đoán mật khẩu, không đổi cấu hình máy chủ hoặc credential thật.
- Giữ nguyên WIP reporting/sidebar và checkpoint của phiên trước. Seal phát hành chỉ HEAD + scope này, không nhận đã verify toàn workspace.

## CHG-20261121-010 — PASSKEY-001: Biên bản triển khai PC server

- Commit `4c106904` đã push và áp PC server (`192.168.1.73`, `tp_tanphat_dev`).
  - Preflight: 25/25 tệp khớp nền `6130456c`.
  - Backup tại `C:\TANPHAT-backups\passkey001\pk001-20261121T161846`: dump 10.669.229 bytes, `pg_restore -l` 16.313 dòng, filestore 39.697.658 bytes.
  - 25/25 tệp khớp SHA256. `-u tp_web_login` exit 0, 0 `ERROR`/`CRITICAL`, version 20.0.2.3.0.
- Fingerprint tài khoản, mật khẩu băm, khóa tài khoản, nhóm, nhân viên, ủy quyền, API key, TOTP, passkey và base URL: `DRIFT_COUNT=0`.
- Public `https://tpone.tadic.vn` 7/7 PASS: health 200; trang đăng nhập có nút, gợi ý, vùng `aria-live` và form mật khẩu; bundle frontend `757bed7` và backend `d892caf` chứa mã mới; `start-auth` trả `rpId=tpone.tadic.vn`, UV bắt buộc; client-event chỉ nhận enum.
- Không thao tác khóa, credential hay tài khoản thật. Chưa kiểm trên thiết bị sinh trắc học thật. Đồng bộ biên bản này không cần restart. [Nghiệm thu](demo/PASSKEY_001_ACCEPTANCE.md).

## CHG-20261121-009 — PASSKEY-001: Hoàn thiện đăng ký và đăng nhập bằng khóa truy cập trên tpone.tadic.vn

- 21/11/2026 (Asia/Saigon). Người dùng báo bấm “đăng nhập bằng khóa”, quét vân tay xong nhưng không vào được hệ thống.
  - Bằng chứng server (chỉ đọc): cấu hình đúng (`web.base.url=https://tpone.tadic.vn`, `rpId=tpone.tadic.vn`, UV bắt buộc); có 1 khóa đã đăng ký với `sign_count=0`.
  - Các lần thử chỉ gọi `start-auth` và **không có `POST /dang-nhap` nào kèm assertion**. Cloudflare `DYNAMIC`/`no-cache`.
  - Kết luận: ceremony phía trình duyệt không trả kết quả (hủy, hết giờ, hoặc thiết bị/hồ sơ không có khóa) và JS native nuốt lỗi. Backend native vẫn đúng.
- `tp_web_login` **20.0.2.3.0** (phụ thuộc thêm `auth_passkey`), dùng lại WebAuthn native và không nới kiểm origin/RP ID/challenge/chữ ký/UV:
  - Trang đăng nhập có nút “Đăng nhập bằng khóa truy cập” và gợi ý tiếng Việt.
  - Lỗi trình duyệt được phân loại và hiển thị dưới nút (`aria-live`), có trạng thái đang xử lý, chống bấm đúp và trở lại sau lỗi. Không còn “Đăng nhập thất bại” chung chung.
  - Thêm route chẩn đoán `/tp_web_login/passkey/client-event` chỉ nhận enum whitelist, không ghi challenge/credential/cookie.
  - Backend trả thông điệp tiếng Việt theo nguyên nhân: khóa lạ/đã thu hồi, challenge hết hạn hoặc dùng lại, sai địa chỉ, thiếu UV, bộ đếm lùi, cooldown, chữ ký/payload hỏng. Payload hỏng không còn gây 500. Trạng thái khóa tài khoản chỉ được báo sau khi assertion hợp lệ.
  - Sửa xác minh danh tính bằng khóa (trước đây nút không gọi WebAuthn).
  - Sửa form bị `d-none` che lỗi khi có ≥2 tài khoản ghi nhớ.
  - Trang Tài khoản & Bảo mật: thêm, đổi tên, thu hồi khóa; báo thành công chỉ sau khi backend xác nhận.
- Kiểm thử (DB `tp_tanphat_test`, tài khoản thử, virtual/software authenticator; origin/RP ID giả lập `https://tpone.tadic.vn`):
  - `/tp_web_login` 18/20: cả 10 test passkey mới PASS; 2 lỗi `test_native_login` đã có từ trước trên HEAD (TestCursor readonly).
  - `TestPasskeyRoles` (mới) + `TestAccountSecurity` 15/15 PASS cho nhân viên, admin ủy quyền và admin gốc. `TestAdminAccountLockHttp` 2/2 PASS.
  - E2E Playwright + CDP virtual authenticator: 29/29, 29/29, 27/27, 0 pageErrors.
- Chưa chứng minh trên sinh trắc học phần cứng thật. Không tạo, xóa hay thu hồi khóa và không đổi credential/quyền của tài khoản thật. WIP reporting/sidebar/branding của phiên khác để ngoài release. [Nghiệm thu](demo/PASSKEY_001_ACCEPTANCE.md), [runbook](../ops/runbooks/PASSKEY_001_DEPLOY_AND_ROLLBACK.md).

## CHG-20261121-008 — ACCOUNT-SECURITY-002 Hotfix: Sửa lỗi icon khiên phóng to trong menu tài khoản sidebar

- 21/11/2026 (Asia/Saigon). Sửa lỗi mục **Tài khoản & Bảo mật** trong dropdown tài khoản sidebar (`custom_addons/tp_web_home/static/src/identity/user_account_menu.xml`) bị thiếu `class="'tp-profile-menu-item'"` và `width/height` khiến icon SVG khiên phóng to chiếm toàn bộ menu và đẩy chữ sang phải:
  - Thêm `class="'tp-profile-menu-item'"` và `width="17" height="17"` cho các icon trong `user_account_menu.xml`.
  - Đồng bộ icon khiên 17×17px cho `account_security` trong `shell_navbar.xml` (`web.UserMenu` và `web.BurgerUserMenu`).
  - Cập nhật `user_account_menu.scss` (`min-width: 214px; width: max-content;` và cố định `.tp-profile-icon`/`.tp-logout-icon` `17px × 17px`).
  - Kiểm XML/libsass SCSS 0 lỗi, commit/push, backup static cũ, đồng bộ PC Server `192.168.1.73`, đóng dấu `LastWriteTime`, restart `tp-odoo` và xác minh public bundle `https://tpone.tadic.vn`.

## CHG-20261121-007 — ACCOUNT-SECURITY-002: Hoàn thiện vai trò backend, đổi mật khẩu inline, sửa lọc phiên Đã thu hồi và Việt hóa luồng 2FA/API key

- 21/11/2026 (Asia/Saigon). Nâng cấp `tp_web_login` **20.0.2.2.0** và `tp_admin_delegation` **20.0.2.3.0**:
  - Header hiển thị nhãn vai trò lấy từ backend (`_tp_account_role_label`: `Quản trị gốc`, `Quản trị viên ủy quyền`, `Quản lý nhân sự`, `Nhân viên nội bộ`) và avatar 52px có monogram fallback.
  - Mục **Mật khẩu**: bổ sung biểu mẫu đổi mật khẩu trực tiếp trong trang (`tp_change_my_password`) với 3 ô (hiện tại / mới / xác nhận), nút hiện/ẩn có `aria-label` và `aria-pressed`, báo lỗi đúng từng trường, giữ nguyên xác thực native `_check_credentials` + `_assert_can_auth` + `auth_totp._revoke_all_devices()` và làm mới session token phiên hiện tại.
  - Mục **Phiên đăng nhập**: sửa lỗi bộ lọc `Đã thu hồi` luôn trả 0 bản ghi (do `res.session` SQL view lọc `revoked IS NOT TRUE`); truy vấn khử trùng trên `res_device_log` theo đúng `self.env.uid`, tách rõ **Phiên hiện tại** (`Thiết bị này · Đang hoạt động`), **Các phiên còn hiệu lực khác** (`0 phiên hoạt động`), và **Lịch sử phiên** (`all` / `current` / `uncleaned` / `revoked`) kèm cột Trình duyệt & Nền tảng; đồng bộ dọn winner trong `ProtectedSessions._revoke()`.
  - Việt hóa toàn bộ thông báo 2FA (`auth_totp.wizard.enable`, `action_totp_disable`), nhãn thời hạn khóa API (`_selection_duration`, giữ nguyên kiểm quyền nhóm), hộp thoại hiển thị khóa API một lần (`res.users.apikeys.show`, bỏ snippet tiếng Anh `ODOO_MCP_KEY`), thêm kiểm quyền `api_keys_allowed` và trạng thái `Còn hiệu lực` / `Đã hết hạn`.
  - Kiểm thử: `/tp_admin_delegation,/tp_branding:TestBrandUrls` **46/46 PASS** (0 failed, 0 error); Playwright v2 **12/12 checks PASS, 0 pageErrors** (desktop 1440px, mobile 390px, eye toggle, field errors, wrong current password, session filters, F5, reduced-motion, single-session); libsass SCSS biên dịch sạch 0 lỗi.
  - Triển khai PC Server (`192.168.1.73`, `tp_tanphat_dev`, commit `c74460b8`): backup `C:\TANPHAT-backups\account-security002\sec007-20261121T135321`, 12/12 tệp khớp SHA256, `-u tp_web_login,tp_admin_delegation` exit `0`, `0 ERROR/CRITICAL`, `DRIFT_COUNT=0`; probe chỉ đọc 3 vai trò (`admin` 433 tổng / 149 chưa dọn / 284 đã thu hồi, `dongtp`, `anhctt` 56 tổng / 3 chưa dọn / 53 đã thu hồi) PASS; public `https://tpone.tadic.vn/web/health` HTTP 200 và bundle công khai `8f258d2/web.assets_web.min.js` + `361ddb7/web.assets_web.min.css` chứa đủ mã/CSS mới.

## CHG-20261121-006 — ACCOUNT-SECURITY-001: Xác nhận public và bàn giao

- Bản source `2bad1f45` và static `3461a34a` đã push/deploy; static005 6 tệp khớp, backup source trước static tại `C:\TANPHAT-backups\account-security001\static005-before.tar.gz`.
- Public `https://tpone.tadic.vn`: health200, deep link bảo mật chuyển đúng login; bundle CSS `/web/assets/615616f/web.assets_web.min.css` 1.703.085 bytes và JS `/web/assets/284b503/web.assets_web.min.js` 8.814.920 bytes chứa workspace/security action mới.
- Probe chỉ đọc 30 tài khoản không lỗi. 42/42 backend/route; browser responsive/F5/identity/single-session 8/8 và TOTP/API thực cho employee/delegate 8/8 PASS. Không thao tác ghi credential/quyền tài khoản thật; hai actor thử trên DB test đã thu quyền và khóa.
- Giữ nguyên WIP reporting/sidebar/tooling khác; workflow checker PASS trên snapshot phát hành có phạm vi. Không coi toàn workspace bẩn hoặc toàn bộ bảo mật hệ thống là đã được nghiệm thu.
- Không cần restart lại khi chỉ đồng bộ biên bản này.

## CHG-20261121-005 — ACCOUNT-SECURITY-001: Icon SVG và biên bản triển khai

- Đổi icon sang SVG để không phụ thuộc font/ligature; browser desktop/mobile, xác minh mật khẩu, F5 và single-session PASS sau thay đổi.
- Bản chức năng `2bad1f45` đã push và áp PC server: 34 tệp checksum khớp, upgrade exit 0, 0 ERROR/CRITICAL; backup `C:\TANPHAT-backups\account-security001\account-security004-20261121T132517`, dump 10.650.657 bytes, filestore 36.756.042 bytes, pg_restore list 16.313 dòng.
- Fingerprint tài khoản/credential/quyền, roster, thiết bị, đề nghị và ngày công không đổi. Sửa có chủ đích `web.base.url=https://tpone.tadic.vn`, freeze=True. Probe 30 tài khoản nội bộ (1 admin gốc, 4 ủy quyền, 25 nhân viên/hệ thống) không lỗi; không đăng nhập đè phiên thật. Public health 200.
- Đồng bộ static/receipt không thay schema; chờ xác minh asset public cuối. Không nhận là audit độc lập hoặc pentest toàn hệ thống.

## CHG-20261121-004 — ACCOUNT-SECURITY-001: Giao diện bảo mật và ranh giới tài khoản

- Người dùng giao triển khai và kiểm tra các vai trò. Thay modal tùy chọn bằng workspace sáng, responsive; giữ backend xác thực native và bước xác minh danh tính, thêm URL có nghĩa và lối vào từ avatar.
- Siết backend thu hồi phiên, thao tác trực tiếp API key, thiết bị TOTP và passkey để giữ DEC-062; không dùng quyền admin kỹ thuật để vượt ranh giới peer-admin. Cho phép tùy chọn múi giờ cá nhân đồng bộ qua employee/version.
- Kiểm thử: 42/42 ca phân quyền/route PASS. Trình duyệt thực: desktop1440/mobile390, đổi mật khẩu qua xác minh, hủy, F5, bộ lọc phiên, phiên mới vô hiệu hóa phiên cũ PASS. Hai HttpCase cũ của tp_web_login bị lỗi TestCursor read-only; không nhận là toàn bộ suite login PASS.
- Server đọc-only trước thay đổi: admin gốc chưa bật 2FA, 154 bản ghi phiên chưa marked revoked; URL gốc `http://tpone.tadic.vn`, freeze false. Khóa tên log có tồn tại, chưa xác định mục đích; không xóa. Chưa có bằng chứng tài khoản bị xâm nhập.
- Tìm và sửa lỗi native cập nhật bộ đếm TOTP cho admin ủy quyền khi thiết lập và trong bước MFA chưa có session.uid; chỉ cho luồng native đã kiểm mã đi qua sentinel server-side, không nhận sentinel từ RPC. Extended browser 8/8 PASS cho nhân viên/admin ủy quyền.
- Chưa deploy tại mốc tạo bản phát hành; receipt sẽ ghi sau khi áp server.

## CHG-20261121-003 — TP-REQUEST-001: Sửa OWL 3 trên màn chi tiết & quản trị đề nghị và bộ đếm Quá hạn

- 21/11/2026 (Asia/Saigon). Sửa lỗi runtime khi bấm **Xem** chi tiết hồ sơ (`Cannot read properties of undefined (reading 'data')`): chuyển `request_detail.xml` và `request_admin.xml` sang chuẩn OWL 3 (`this.*`, `t-out`), bổ sung `markup()` cho nội dung trao đổi trong `request_detail.js`; sửa `_search_is_overdue` trong `request_record.py` hỗ trợ toán tử `'in'/'not in'` chuẩn hóa bởi Odoo 20 Domain; bổ sung kiểm thử `overdue == 0` trong `test_tp_request.py` (`/tp_request` 12/12 PASS); đồng bộ lên PC Server `192.168.1.73`, restart `tp-odoo` và xác minh `https://tpone.tadic.vn/web/health` 200.

## CHG-20261121-002 — TP-REQUEST-001: Vá tương thích libsass `request.scss` và ghi nhận triển khai PC Server

- 21/11/2026 (Asia/Saigon). Đổi `width: min(980px/1040px, 100%)` thành `width: 100%; max-width: 980px/1040px;` trong `custom_addons/tp_request/static/src/styles/request.scss` để biên dịch sạch qua libsass trên container `tp-odoo` (`web.assets_backend.min.css` 1.696.919 bytes, `HAS_ERROR=False`); sửa cột snapshot `hr_employee` trong `ops/runbooks/deploy-tp-request001.ps1`; cập nhật kết quả deploy PC Server (`backup req001-20261121T113004`, `UPGRADE_EXIT=0`, `DRIFT_COUNT=0`, `https://tpone.tadic.vn/web/health` 200).

## CHG-20261121-001 — TP-REQUEST-001: Xây dựng module Đề nghị & Phê duyệt (`tp_request` 20.0.1.0.0) và chuẩn hóa đường dẫn `/app/de-nghi/...`

- 21/11/2026 (Asia/Saigon). Xây dựng hoàn chỉnh phân hệ **Đề nghị & Phê duyệt** dùng chung toàn công ty trên nền Odoo 20 native (OWL/QWeb/SCSS):
  - Module mới `custom_addons/tp_request` **20.0.1.0.0**: khung loại đề nghị & tuyến duyệt tuần tự theo phiên bản (`tp.request.type`, `tp.request.type.step`, `tp.request`, `tp.request.step`), nhật ký hệ thống bất biến (`tp.request.history`) tách biệt trao đổi (`mail.message`), guard tệp đính kèm riêng tư (`ir.attachment` + `/tp_request/attachment/*`), xuất Excel chuẩn bộ lọc (`/tp_request/export.xlsx`), cron cảnh báo quá hạn (không tự duyệt), tích hợp 1-1 Điều chỉnh công (`attendance_bridge.py` với `tp.hr.attendance.correction`) và thực hiện Thiết bị/IT (`equipment_bridge.py` với `tp_equipment`: cấp phát có lock chống cấp trùng, đổi máy nguyên tử bắt buộc tình trạng máy cũ, sửa chữa `maintenance.request`, mua sắm `tp.equipment.proposal` không tự tạo tồn kho), bảo toàn DEC-053/054/061/062.
  - Nâng cấp `custom_addons/tp_branding` **20.0.2.2.0**: bổ sung 7 đường dẫn chuẩn `/app/de-nghi/{tong-quan,cua-toi,can-duyet,can-thuc-hien,theo-doi,quan-tri,ho-so/<id>}` hỗ trợ mở trực tiếp, F5 và Back/Forward; cập nhật `test_brand_urls.py`.
  - Kiểm thử: cú pháp Python (12/12), XML (13/13), JS (10/10); Odoo automated tests trên `tp_tanphat_test`: `/tp_request` 12/12 PASS (18 tình huống), `/tp_branding` 33/33 PASS, hồi quy `/tp_admin_delegation` 37/37 PASS, biên dịch JS/CSS assets 0 lỗi. Cập nhật `TP_TABLE_FILTER_INVENTORY.md`, `TP_URL_ROUTE_INVENTORY.md`, [Hướng dẫn & Nghiệm thu](demo/TP_REQUEST_001_GUIDE_AND_ACCEPTANCE.md), [Runbook](../ops/runbooks/TP_REQUEST_001_DEPLOY_AND_ROLLBACK.md).
  - Triển khai PC Server (`192.168.1.73`, `tp_tanphat_dev`): commit `83e0d217` + vá `request.scss` tương thích libsass (`max-width` thay `min(px, 100%)`), backup `C:\TANPHAT-backups\tp-request001\req001-20261121T113004`, 42/42 tệp khớp SHA256, `-i tp_request -u tp_branding` exit 0, `0 ERROR/CRITICAL`, `DRIFT_COUNT=0`, 7 loại đề nghị sẵn có, 0 bản ghi giả; biên dịch `web.assets_backend.min.js`/`min.css` 0 lỗi; `https://tpone.tadic.vn/web/health` HTTP 200 và 7/7 route `/app/de-nghi/...` phản hồi `303 -> /dang-nhap?redirect=...`.

## CHG-20261120-017 — HR-SELF-EDIT-001 + BANK-002: Tự sửa hồ sơ của chính mình trong danh sách nhân viên; tài khoản ngân hàng không cần xác minh

- 20/11/2026 (Asia/Saigon). Yêu cầu trực tiếp của người dùng (DEC-065):
  - `tp_admin_delegation` (Python, không đổi phiên bản): `models/hr_profile.py` — hồ sơ của chính mình mở từ danh sách nhân viên có thông báo "Đây là hồ sơ của bạn…" và mở khóa đúng các trường tự phục vụ (`_tp_self_service_fields()`); họ tên, phòng ban, chức vụ, mã, tài khoản, quyền và nút quản trị vẫn khóa; hồ sơ admin ủy quyền khác vẫn chỉ đọc. `models/guards.py` — guard `hr.version` nhận `last_modified_date`/`last_modified_uid` (đúng người đang sửa) mà core tự thêm, sửa lỗi có sẵn khiến admin ủy quyền không lưu được địa chỉ, CCCD, hộ chiếu, giới tính, quốc tịch, hôn nhân.
  - `tp_hr_workspace/static/src/profile/employee_profile.js` (tệp tĩnh): nút "Sửa hồ sơ" hiện trên hồ sơ của chính mình (so `user_id` với người đăng nhập), menu hành động/in vẫn ẩn.
  - `tp_hr_bank` **20.0.1.1.0**: lưu tài khoản ngân hàng hợp lệ là dùng được ngay cho chi lương, bỏ trạng thái "Chờ Nhân sự xác minh"; migration `20.0.1.1.0/post-migrate.py` bật dùng được cho tài khoản tự khai đang chờ. Người dùng vẫn không tự ghi `allow_out_payment`.
  - Kiểm: local `/tp_hr_bank,/tp_admin_delegation` 0 failed, 0 error / 31 test, gồm Playwright desktop + di động sửa hồ sơ của mình tại chỗ.
  - PC Server: commit `538924a8`, backup `C:\TANPHAT-backups\hr-bank002\bank002-20261120T191725`; `-u tp_hr_bank` exit 0, log 0 ERROR, 1 tài khoản đang chờ được bật dùng được (`1:0:1` → `1:1:0`), 19 key snapshot không khác biệt ngoài dự kiến; view hồ sơ đúng cho 5/5 admin ủy quyền; bundle JS dựng được; `https://tpone.tadic.vn/web/health` 200.
  - Commit code `538924a8` ghi nhầm `CHG-20261120-016` trong tiêu đề (mã đó thuộc HR-ATTENDANCE-ORDER-001); mã đúng của thay đổi này là `CHG-20261120-017`. [Nghiệm thu](demo/HR_BANK_002_SELF_EDIT_ACCEPTANCE.md), [runbook](../ops/runbooks/HR_BANK_002_DEPLOY_AND_ROLLBACK.md).

## CHG-20261120-016 — HR-ATTENDANCE-ORDER-001: Đảo ngược thứ tự ngày chấm công (mới nhất/hôm nay lên đầu, cuộn xuống là ngày cũ)

- 20/11/2026 (Asia/Saigon). Thực hiện yêu cầu trực tiếp của người dùng đảo ngược thứ tự bảng giờ vào/ra trong mục Chấm công ("Công của tôi" và popup xem chi tiết nhân viên):
  - `custom_addons/tp_hr_attendance` **20.0.3.5.8**: Sửa `models/attendance_overview.py` (`_tp_mine_dataset` và `_tp_person_data`) áp dụng quy tắc sắp xếp `ordered_dates`: các ngày đã qua và ngày hiện tại (`work_date <= today`) sắp xếp giảm dần (`-d.toordinal()`), ngày mới nhất (Hôm nay/ngày 20) luôn đứng ở dòng đầu tiên (Row 1), cuộn xuống dưới là các ngày cũ hơn (19, 18, 17... lùi về 01); các ngày tương lai trong kỳ (`work_date > today`) nằm ở cuối bảng (21..30).
  - Bổ sung unit test `test_mine_rows_reverse_chronological` trong `tests/test_upload.py`.
  - Triển khai PC Server: Backup tại `C:\TANPHAT-backups\hr-attendance-sort-order\20261120T190555\`, nâng cấp module exit 0, restart container `tp-odoo`, kiểm chứng trực tiếp trên tài khoản nhân viên TP001 (Row 1 hiển thị đúng ngày 20/11/2026 kèm giờ vào và badge "Hôm nay"), LAN/Public health HTTP 200 OK (`{"status": "pass"}`). [Bản nghiệm thu](demo/HR_ATTENDANCE_ORDER_001_ACCEPTANCE.md).

## CHG-20261120-015 — BANK-001: Tài khoản ngân hàng trong "Thông tin cá nhân" và rà soát giao diện hồ sơ

- 20/11/2026 (Asia/Saigon). Mọi tài khoản tự khai tài khoản ngân hàng nhận lương trong "Hồ sơ của tôi → Thông tin cá nhân", chọn ngân hàng từ danh mục chuẩn có biểu tượng:
  - Module mới `custom_addons/tp_hr_bank` **20.0.1.0.0**: danh mục `tp.bank` 76 tổ chức theo NAPAS 247/VietQR (70 đang dùng; mã, BIN, tên viết tắt, tên đầy đủ, SWIFT, biểu tượng chữ + màu nhận diện, `noupdate`); menu "Danh mục ngân hàng" cho Quản lý Nhân sự; thẻ "Tài khoản ngân hàng" thêm/sửa/gỡ, số tài khoản nhóm 4 số, trạng thái "Chờ Nhân sự xác minh"/"Nhân sự đã xác minh"; ô chọn ngân hàng tìm không dấu theo tên/viết tắt/mã/BIN, đếm kết quả, bàn phím; form tài khoản ngân hàng của HR có ô chọn và đồng bộ `bank_name`/`bank_bic`.
  - An toàn: ghi qua `tp_save_my_bank_account`/`tp_remove_my_bank_account` có kiểm chủ sở hữu; người dùng chỉ đọc tài khoản của chính mình; `allow_out_payment` chỉ HR bật và tự tắt khi đổi ngân hàng/số; chatter chỉ hiện 4 số cuối. `tp_admin_delegation/models/guards.py` thêm hook `_tp_self_service_fields()` để mở đúng một trường `bank_account_ids`; trường HR khác vẫn bị chặn.
  - Rà soát "Hồ sơ của tôi" (`tp_hr_workspace`, chỉ tệp giao diện tĩnh): ô tìm kiếm cho quốc gia, quốc tịch, quốc gia nơi sinh, tỉnh/thành phố ("viet", "ha noi"); ngày dùng bộ chọn của Odoo cố định DD/MM/YYYY ở cả xem và sửa (ô ngày trình duyệt từng hiện MM/DD); giá trị trống nghiêng xám; gợi ý mẫu cho ô nhập; sửa mất mũi tên ô chọn và viền đôi khi chọn ô tìm kiếm.
  - Kiểm thử: `/tp_hr_bank` 9/9 PASS, gồm Playwright desktop + di động (0 lỗi console) và kiểm SCSS biên dịch được (bắt lỗi libsass `min(px, vh)` trước khi áp). Lỗi `/tp_hr_workspace` còn lại là nhóm có sẵn trước thay đổi.
  - PC Server: commit `b594f26f`, backup `C:\TANPHAT-backups\hr-bank001\bank001-20261120T182500`; `-i tp_hr_bank` exit 0, log 0 ERROR, danh mục 76:70:76, 18 key snapshot không khác biệt ngoài dự kiến; CSS/JS `web.assets_web` trên PC dựng được 0 lỗi; `https://tpone.tadic.vn/web/health` 200. [Bản nghiệm thu](demo/HR_BANK_001_ACCEPTANCE.md), [runbook](../ops/runbooks/HR_BANK_001_DEPLOY_AND_ROLLBACK.md).

## CHG-20261120-014 — ATTENDANCE-FAST-SYNC-001: Tối ưu tốc độ nhận dữ liệu chấm công thật và cập nhật giao diện trực tiếp

- 20/11/2026 (Asia/Saigon). Thực hiện nhiệm vụ ATTENDANCE-FAST-SYNC-001 tối ưu tốc độ nhận dữ liệu chấm công từ máy chấm công thật (nhà cung cấp ENTI) và cập nhật phản ứng tức thì trên giao diện người dùng:
  - Xác minh và đo lường 3 chặng độ trễ: Chặng A (Máy vật lý → Cloud ENTI: ~1–2s, đo thực tế qua lượt chấm tan ca 17:10:19 VN nhận lúc 17:10:22 VN); Chặng B (ENTI → Odoo nhận và lưu: giảm từ 15s xuống 5s/lần, thời gian gọi API 240–290ms, độ trễ nhận 0–5s, trung bình 2.5s); Chặng C (Odoo lưu → Giao diện hiển thị: WebSocket 101 qua Cloudflare Tunnel, debounce 250ms, RPC 18–40ms, render lại DOM trong ~0.35s < 1s; Fallback polling 4s khi mất WebSocket).
  - Tối ưu backend `custom_addons/tp_hr_attendance` **20.0.3.5.7**: Mặc định fast poll `today` là 5s, hỗ trợ config override tối thiểu 2s; áp dụng Lazy Evaluation cho mapping nhân viên loại bỏ quét bảng `hr.employee` trong các chu kỳ fast poll; so sánh hash digest tránh ghi database và tránh phát bus thừa khi dữ liệu không đổi; ngân sách cron 50s và re-trigger 18ms chống nghẽn scheduler.
  - Chuẩn hóa giao diện người dùng: Loại bỏ tên nhà cung cấp "ENTI" trên giao diện chung, dùng nhãn "Đồng bộ tự động: Hoạt động / Đang chậm / Mất kết nối"; cập nhật đồng bộ các thẻ trạng thái, popup chi tiết, biểu đồ và Công của tôi.
  - Kiểm thử & Triển khai PC Server (`192.168.1.73`): Unit tests `scripts/tests/test_enti_pure.py` 6/6 PASS, test case fast sync settings PASS; backup an toàn tại `C:\TANPHAT-backups\attendance-fast-sync001\20261120T172034\`; upgrade container `tp-odoo` exit 0, restart container; LAN và Public health check (`https://tpone.tadic.vn/web/health`) trả về HTTP 200 OK. [Chi tiết trạng thái](PROJECT_STATUS.md).

## CHG-20261120-013 — WEB-RELOAD-BLANK-001: Sửa lỗi tải lại trang làm trắng toàn bộ giao diện

- 20/11/2026 (Asia/Saigon). Khắc phục sự cố tải lại trang (Reload / F5) làm trắng giao diện trên các URL chuẩn hóa phân cấp:
  - Khắc phục triệt để nguyên nhân gốc `TypeError: Failed to set the 'href' property on 'URL': Invalid URL` do gán đường dẫn tương đối vào thuộc tính `.href` của `window.URL` tại top-level loader `@tp_branding/router_patch`.
  - `custom_addons/tp_branding` **20.0.2.1.0**: Cập nhật `brand_urls.js` bảo đảm `brandHref` luôn trả về URL tuyệt đối hợp lệ khi có `origin`; bọc `try ... catch` an toàn khi gán `urlObj.href` và khi khởi tạo `router.replaceState`; nâng cấp `brand_routes.js` đồng bộ `session_info` từ nhiều namespace; bổ sung cơ chế Fallback và Tự phục hồi trong `webclient_patch.js` (fallback về Trang chủ, post-boot check 500ms, emergency recovery overlay sau 8 giây).
  - Kiểm thử và nghiệm thu: Unit test `TestBrandUrls` 12/12 PASS; Playwright trên máy chủ PC Server thật (`192.168.1.73:8069`) xác thực thành công thao tác F5 trong cùng tab trên `/app/trang-chu`, `/app/nhan-su/nhan-vien`, `/app/thiet-bi/danh-sach` với 0 console/page error.
  - Triển khai PC Server: Backup tại `C:\TANPHAT-backups\web-reload-blank001\20261120T162405\`, nâng cấp module `tp_branding` trong container `tp-odoo` exit 0, restart container, LAN và Public health check (`https://tpone.tadic.vn/web/health`) trả về HTTP 200 OK. [Bản nghiệm thu](demo/WEB_RELOAD_BLANK_001_ACCEPTANCE.md).


## CHG-20261120-012 — HR-CONFIG-MENU-CLEANUP: Xóa hẳn các menu cấu hình HR cũ, chỉ giữ duy nhất "Nhãn nhân viên"

- 20/11/2026 (Asia/Saigon). Thực hiện yêu cầu trực tiếp của người dùng kèm ảnh chụp menu dropdown "Cấu hình HR" (xóa bỏ triệt để khỏi code XML và database, không dùng ẩn hay phân nhóm quyền):
  - `custom_addons/tp_hr_workspace` **20.0.1.21.0**: Xóa thẻ menuitem `Loại hồ sơ năng lực` (`tp_hr_workspace.menu_resume_types`) và `Loại kỹ năng và cấp độ` (`tp_hr_workspace.menu_skill_types`) trong `views/workspace.xml`. Giữ lại duy nhất `Nhãn nhân viên` (`tp_hr_workspace.menu_categories`, sequence 10).
  - `custom_addons/tp_hr_attendance` **20.0.3.5.6**: Xóa thẻ menuitem `Quy tắc công` (`tp_hr_attendance.menu_rules`), `Mã máy chấm công` (`tp_hr_attendance.menu_codes`), `Phân công xử lý công` (`tp_hr_attendance.menu_assignments`), `Nhật ký chấm công` (`tp_hr_attendance.menu_logs`) trong `views/menus.xml`.
  - Migration script dọn dẹp database: `custom_addons/tp_hr_workspace/migrations/20.0.1.21.0/post-migrate.py` và `custom_addons/tp_hr_attendance/migrations/20.0.3.5.6/post-migrate.py` thực hiện unlink vật lý các bản ghi `ir.ui.menu` và `ir.model.data` tương ứng.
  - Cập nhật test suites: `tp_hr_attendance/tests/test_access.py` (chuyển kiểm tra quyền sang `menu_enti_config` và assert các menu cũ đã bị gỡ hoàn toàn) và `tp_hr_workspace/tests/test_directory_readonly.py` (kiểm tra `menu_categories` là menu con duy nhất dưới `menu_group_config`).
  - Kiểm thử và triển khai: Local dev upgrade exit 0, xác nhận DB local dev chỉ còn 1 bản ghi `Nhãn nhân viên`. PC Server sao lưu đầy đủ (`C:\TANPHAT-backups\hr-remove-config-menus\20261120T154500\`), đồng bộ mã nguồn, upgrade container `tp-odoo` exit 0, restart container. Kiểm chứng DB PC Server trả về đúng 1 bản ghi `Nhãn nhân viên`, LAN và Public health check (`https://tpone.tadic.vn/web/health`) trả về HTTP 200 OK.

## CHG-20261120-011 — HR-DELETE-ASSET-RETURN-001: Tự thu hồi tài sản công ty về kho khi xóa vĩnh viễn nhân viên

- 20/11/2026 (Asia/Saigon). Giải quyết dứt điểm lỗi chặn xóa bởi 3 quan hệ trong `tp_equipment`: Dòng phiếu bàn giao (người giữ trước/sau) và Phiếu bàn giao (nhân viên nhận).
- Module `tp_equipment` **20.0.1.6.0**: Kế thừa `hr.employee` (`employee_delete.py`), override hook `_tp_delete_plan` và `_tp_permanent_unlink`:
  - Tự động tạo và hoàn tất phiếu `tp.equipment.move` (loại `return` / `loan_return`) thu hồi tài sản công ty đang được cấp phát cá nhân về kho của công ty, chuyển nơi giữ sang `stock`, gỡ người giữ (`tp_employee_id = False`).
  - Bảo toàn nguyên vẹn mã tài sản, serial, cấu hình, giá trị và tình trạng kỹ thuật (`tp_technical_state`).
  - Bảo toàn lịch sử bàn giao: Chụp snapshot thông tin (tên, mã NV, phòng ban) vào các trường chuyên dụng trên header và dòng phiếu, gỡ khóa ngoại FK (`set to NULL`) có kiểm soát bằng context nội bộ `tp_equipment_move_internal=INTERNAL`, hiển thị kèm nhãn *(Nhân viên đã xóa)*.
  - Tự động hủy các phiếu bàn giao đang ở trạng thái `pending` hoặc `draft`, giải phóng giữ chỗ cho tài sản.
  - Xử lý tài sản cá nhân (`personal`): giải phóng quyền sở hữu / trả lại chủ nhân (`retired / returned_owner`), không nhập vào kho công ty.
  - Thực thi trong 1 transaction Odoo nguyên tử, rollback 100% nếu có lỗi; kiểm soát idempotency key.
- Module `tp_hr_workspace` **20.0.1.20.0**: Thiết kế lại Dialog Xem trước xóa (Preview Dialog) gồm các nhóm A (Bảng tài sản thu hồi + chọn kho nhận), B (Phiếu lịch sử bảo toàn), C (Phân công khác), D (Sẽ xóa), E (Giữ lại), F (Blocker thực sự nếu có). Dòng xác nhận: *"Xóa vĩnh viễn hồ sơ và thu hồi các tài sản được liệt kê về kho trên hệ thống."*
- Kiểm thử tự động: `custom_addons/tp_equipment/tests/test_employee_delete_asset_return.py` (6/6 tests PASS: 0 failed, 0 errors); hồi quy `tp_hr_workspace` (3/3 tests PASS).
- Triển khai PC Server: Backup an toàn tại `C:\TANPHAT-backups\hr-delete-asset-return001\` (`tp_tanphat_dev.dump` 10.418.949 bytes, `code-pre.tar.gz` 757.946 bytes). Đồng bộ mã nguồn, upgrade trong container `tp-odoo` exit 0, restart container, LAN và Public health 200 OK.
- Kiểm chứng read-only trên hồ sơ Trần Đức Lương (ID 69, mã TP072): Blocker giảm từ 3 xuống 0, Equipment history: 3 phiếu/dòng được bảo toàn snapshot, Can submit: True. Hồ sơ thật giữ nguyên 100%. [Bản nghiệm thu](demo/HR_DELETE_ASSET_RETURN_001_ACCEPTANCE.md).

## CHG-20261120-010 — HR-EMPLOYEE-CODE-003: Mã nhân viên TP + 3 chữ số, chuyển mã cũ có audit

- 20/11/2026 (Asia/Saigon), theo yêu cầu HR-EMPLOYEE-CODE-003. Commit app `13fc1283`: `tp_organization` 20.0.2.3.0, `tp_hr_attendance` 20.0.3.5.5.
  - `code_format`: một bộ định dạng/đọc mã dùng chung cho cấp mã, import roster, ràng buộc và migration. Mã ngoài hai dạng bị báo, không cắt máy móc ba số cuối.
  - Cấp mã nối tiếp số cao nhất đã cấp (mọi công ty, hồ sơ lưu trữ, audit, cả hai dạng). Không dùng lại số đã xóa/đã đổi; hết dải thì báo và dừng, không sinh TP1000. Import giữ số nguồn đã xác minh; số nguồn trên 999 là xung đột.
  - Migration 20.0.2.3.0: lập mapping cho mọi hồ sơ; có trùng, mã ngoài quy tắc, thiếu mã, số đã thu hồi hoặc lệch mã nguồn thì dừng, không ghi. Nếu hợp lệ thì đổi qua correction nội bộ dưới advisory lock, mỗi hồ sơ 1 audit + 1 chatter. Chạy lại không đổi gì.
  - `tp_hr_attendance` 20.0.3.5.5: làm mới bản sao mã trên ngày công/đề nghị theo employee_id + company_id (giờ, công, kỳ giữ nguyên). Ghép ENTI không còn dùng mã ENTI để chọn giữa hai người cùng tên.
  - Test chỉ dùng dữ liệu giả; script áp có backup, snapshot trước/sau và danh sách key được phép đổi; runbook và tài liệu nghiệm thu.
- Áp PC 15:00 giờ VN: 40/40 mã chuyển, 0 xung đột, số tiếp theo TP073. ID, tài khoản, mật khẩu, quyền, roster, ngày công, phiên, ENTI mapping và audit cũ giữ nguyên; mail/thông báo không phát sinh. Chu kỳ ENTI sau khởi động lại gắn đúng người, không trùng, không quay về mã cũ. Backup `C:\TANPHAT-backups\hr-employee-code003\code003-20261120T150009`; mapping thật chỉ nằm trong backup trên PC.
- Script áp dừng ở key `audit_history`: phép kiểm lấy các dòng audit cũ hơn 1 phút tại thời điểm chụp, nên snapshot sau tính cả 40 dòng mới. Đã đối chiếu 32 dòng audit có trước khi áp khớp md5. Script nay chụp `audit_max` khi Odoo dừng và chỉ so các dòng đến mốc đó.

## CHG-20261120-009 — SYSTEM-URL-001: Chuẩn hóa URL phân hệ và màn hình toàn hệ thống

- 20/11/2026 (Asia/Saigon). Thực hiện chuẩn hóa URL toàn hệ thống theo 8 quy tắc vàng: Tiếng Việt không dấu (`kebab-case`), phân hệ cố định (`nhan-su`, `khkd`, `thiet-bi`, `bao-cao`, `quan-tri`, `trang-chu`), tên rõ nghiệp vụ, không dùng `action-528` hoặc model kỹ thuật làm URL chính, hỗ trợ chi tiết `/<id>` và tạo mới `/tao-moi`. Phân biệt Quản lý dự án (`/app/khkd/quan-ly-du-an`) và Quản trị dự án (`/app/khkd/quan-tri-du-an`).
- Nâng cấp `custom_addons/tp_branding` lên `20.0.2.0.0`:
  - `brand_routes.py` & `static/src/brand_routes.js`: Registry định nghĩa 46 canonical business routes, action XML IDs, tags, native slugs, chi tiết, alias, đồng bộ 100% giữa Python và Owl JS.
  - `models/ir_http.py`: Override `ir.http.session_info` query động bảng `ir_model_data` theo XML ID thực tế của database hiện hành, cung cấp bảng ánh xạ 2 chiều `xml_to_id` và `id_to_xml` chống lệch numeric action ID giữa các môi trường.
  - `static/src/router_patch.js`: Adapter 2 chiều hoàn chỉnh: `stateToUrl` sinh URL nghiệp vụ chuẩn kèm chi tiết/tạo mới; `urlToState` phân tích URL nghiệp vụ thành native action target cho core Odoo xử lý.
  - Đảm bảo tương thích ngược 100% với legacy URLs (`/app/action-528`, `/app/tp-home`, `/odoo/...`, `/web/login`).
  - Tài liệu: `docs/ui/TP_URL_NAMING_STANDARD.md` và `docs/ui/TP_URL_ROUTE_INVENTORY.md`.
- Kiểm thử và triển khai:
  - Local `tp_tanphat_test`: 31/31 Odoo test PASS (12/12 unit tests + 19/19 HttpCase tests đạt 0 failed, 0 error).
  - Local `tp_tanphat_dev`: Upgrade `-u tp_branding` thành công exit code 0.
  - PC Server `192.168.1.73`: Sao lưu an toàn tại `C:\TANPHAT-backups\system-url001\20261120T143858\` (dump DB `10.405.836` bytes, source tarball, deploy package). Đồng bộ source, đóng dấu mtime mới cho JS/XML, upgrade `-u tp_branding` trong Docker container `tp-odoo` exit 0, restart container.
  - Xác minh thực tế trên Public Domain `https://tpone.tadic.vn`: 13/13 business route anonymous deep link redirects sang `/dang-nhap?redirect=/app/...` chuẩn xác; 5/5 legacy redirects đạt; dynamic mapping nhận diện đúng action `528` cho `tp_hr_workspace.action_employees`.
  - [Bản nghiệm thu](demo/SYSTEM_URL_001_ACCEPTANCE.md).

- 20/11/2026, theo yêu cầu “Sửa luôn” sau sự cố CHG-20261120-007. `ops/runbooks/deploy-enti-attendance002.ps1`: sau khi giải nén và kiểm checksum, đặt thời gian sửa của mọi file trong `release` bằng giờ triển khai, trước khi upgrade và khởi động lại Odoo; kết quả JSON thêm `stamped_at`. Odoo tính phiên bản bundle CSS/JS theo URL + thời gian sửa, nên lần áp sau trình duyệt nhận bundle mới mà không cần khởi động lại thêm, kể cả khi tarball mang mtime 1970. Không đổi module hay dữ liệu.
- Kiểm: script parse 0 lỗi. Trên PC, trong thư mục tạm ngoài dự án, chạy đúng đoạn mã mới: file giải nén từ tarball mtime 0 mang 1970-01-01, sau bước đóng dấu mang giờ hiện tại; thư mục thử đã xóa. Bản script trên PC được thay bằng bản commit và kiểm SHA256.

## CHG-20261120-007 — Đã áp thanh ba thẻ gọn lên PC server

- 20/11/2026 13:09 giờ VN; release `f710eeec` (2 file, checksum khớp), `tp_hr_attendance` 20.0.3.5.3 → 20.0.3.5.4, upgrade exit 0/0 ERROR. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-dash004b-20261120T130940` (dump + restore-list, filestore, source, config, SHA256). Nguồn PC 81/81 trước và sau khớp commit; snapshot nghiệp vụ trước/sau giống hệt, chỉ đổi phiên bản.
- Sau upgrade, bundle CSS công khai vẫn là bản cũ: gói release ghi mtime 1970 cho file, lần trước cũng vậy, mà Odoo tính phiên bản bundle theo URL + thời gian sửa. Đã đặt thời gian sửa hiện tại cho đúng 2 file phát hành và khởi động lại container Odoo. Sau đó bundle công khai CSS `940ffac` (SHA256 `9dab29dc`) khớp PC và có quy tắc thẻ mới. Health 200/login 302 công khai; log 0 ERROR kể từ khi chạy lại (1 lỗi websocket đúng lúc tắt), cron ENTI vẫn chạy 39 nhân viên. Không đăng nhập tài khoản thật trên PC. Lần sau gói release phải mang thời gian sửa thật. [Nghiệm thu §6](demo/ATTENDANCE_DASH_004_ACCEPTANCE.md#6-thanh-ba-thẻ-gọn-hơn-chg-20261120-006).

## CHG-20261120-006 — Thanh ba thẻ chấm công gọn hơn

- 20/11/2026 theo ảnh và yêu cầu của người dùng “làm gọn lại thanh này”. `tp_hr_attendance` 20.0.3.5.4, chỉ đổi SCSS. Mỗi thẻ còn một hàng thấp: biểu tượng + tên trên “Xem danh sách” ở bên trái, số lớn ở bên phải; thẻ cao 66px trên PC (trước khoảng gấp đôi), 64px trên tablet/điện thoại; điện thoại xếp ba hàng sát nhau. Giữ màu, viền trái, hover, focus, tooltip, bấm mở danh sách và dữ liệu. Kiểm local: 10 kiểm Playwright đạt (ba thẻ bằng nhau, hover/focus, hộp thoại khớp số, Đóng giữ bộ lọc, giảm chuyển động, nhân viên thường, 4 width không tràn), 0 lỗi JS. [Nghiệm thu §6](demo/ATTENDANCE_DASH_004_ACCEPTANCE.md#6-thanh-ba-thẻ-gọn-hơn-chg-20261120-006).

## CHG-20261120-005 — Đã áp dashboard chấm công gọn lên PC server

- 20/11/2026 11:55 giờ VN; release `162bc409` (11 file, checksum khớp), `tp_hr_attendance` 20.0.3.5.2 → 20.0.3.5.3, upgrade exit 0/0 ERROR. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-dash004-20261120T115540` (dump + restore-list, filestore, source, config, SHA256). Nguồn PC 79/79 trước và 81/81 sau khớp commit; snapshot nghiệp vụ trước/sau giống hệt, chỉ đổi phiên bản.
- Kiểm chỉ đọc bằng ORM có rollback trên dữ liệu thật hôm nay: thẻ 25/4/10/0 (tổng 39) bằng tổng danh sách từng nhóm cho cả admin và nhân viên thường. Bảng gần nhất ở chế độ mốc vào đầu/ra cuối, giây thật, không có địa điểm (PC 0 sự kiện quẹt). Không lộ raw; nhân viên thường không xuất. Health 200/login 302 cục bộ và công khai; bundle công khai JS `297acd1e`/CSS `0d689c15` khớp PC và có code mới; log 0 ERROR, cron ENTI vẫn chạy. Không đăng nhập tài khoản thật trên PC. [Nghiệm thu §5](demo/ATTENDANCE_DASH_004_ACCEPTANCE.md#5-pc-server-đã-áp-dụng-chg-20261120-005).

## CHG-20261120-004 — Dashboard chấm công gọn: ba thẻ bấm mở danh sách, bảng chấm gần nhất

- 20/11/2026 Asia/Saigon; prompt hợp nhất của người dùng thay các yêu cầu còn mâu thuẫn (kể cả giữ sáu thẻ). `tp_hr_attendance` 20.0.3.5.3. Ba thẻ Đang làm/Đã về/Chưa đi làm cao bằng nhau, bấm mở hộp thoại danh sách (tab nhóm, tìm không dấu, phòng ban, 10/20/50, trạng thái tải/lỗi/trống, Đóng giữ ngày/bộ lọc/cuộn). Một phân loại backend cho thẻ, donut, biểu đồ và danh sách: mỗi người một nhóm mỗi ngày; chỉ có giờ ra vẫn là Đã về; mất nguồn/chưa ghép mã là Chưa xác định kèm lý do, không bao giờ âm thầm thành Chưa đi làm.
- Bảng gần nhất thay danh sách thẻ nhiều dòng: Mã NV · Họ và tên · Thời gian · Địa điểm, header dính. Dữ liệu thật hiện là mốc vào đầu/ra cuối (PC 0 sự kiện quẹt, không có địa điểm) nên tiêu đề “Chấm công gần nhất”; giây chỉ hiện khi đồng hồ nguồn có giây. Live bus/polling cập nhật cả hộp thoại đang mở. RPC mới `tp_overview_group` kiểm quyền backend, không trả raw.
- Kiểm thực local `tp_tanphat_test`: Odoo 98/98, Ruff sạch; Playwright admin và nhân viên thường tổng hợp lần lượt đạt (số thẻ = tổng danh sách, live khi mở hộp thoại 21→20/5→6, 4 width không tràn, 0 lỗi JS). Hai script ENTI cũ cập nhật sang bố cục mới. Delegate browser và thiết bị thật chưa chạy. [Nghiệm thu](demo/ATTENDANCE_DASH_004_ACCEPTANCE.md).

## CHG-20261120-003 — Đã giao quản trị chấm công và dashboard thu gọn lên PC server

- 20/11/2026 Asia/Saigon; app `053d7691` đã push/deploy PC20.0.3.5.2, source79/79, upgradeexit0/0ERROR. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-adminui003-20261120T101503` có dump/restore-list/filestore/source/config/SHA256. Snapshot nghiệp vụ/quyền trước-sau giống nhau, chỉ đổi version. Local18069 cũ20.0.3.3.0 giữ nguyên.
- Health/login200, public JS603526e/CSS c9f02f8 khớp SHA256 server, có nguồn quản trị/xuất mới, dashboard không legend/nhãn đồng bộ; cold asset đầu tiên timeout35s khi sinh bundle, sau đó kiểm lại PASS. Cron thật vẫn đọc15s, log0ERROR. Bộ ảnh admin final16/4width/0JSerror bằng một phiên, dashboard4width0overflow/tooltip thực, XLSX3kỳ khớp và previewHTML rõ. Delegate/employee browser NOT RUN do login403 test, ORMscope đạt; chưa MicrosoftExcel/thiết bị thật/businessacceptance. [Bàn giao](demo/ATTENDANCE_ADMIN_UI_001_ACCEPTANCE.md). Workflow seal release đúng scope PASS, foreign WIP/checkpoint giữ.

## CHG-20261120-002 — Quản trị chấm công trực quan, bỏ nhập Excel và thu gọn dashboard

- 20/11/2026 Asia/Saigon; người dùng trực tiếp giao triển khai, sau đó đính chính scope và bổ sung hai ảnh `9e79b638`/`219fe92e`. `tp_hr_attendance` 20.0.3.5.2: Quản trị chấm công hiển thị kết nối/số liệu thật, xuất `.xlsx` theo kỳ/phòng, đối chiếu và nhật ký gần nhất; bỏ khối và menu nhập/lịch sử Excel, giữ dữ liệu lịch sử. Form cấu hình, bảng đối chiếu và nhật ký native gọn hơn, có search theo ngày/kết quả/hình thức và chi tiết chỉ đọc.
- Dashboard bỏ chú giải donut và nhãn đồng bộ/giờ cập nhật; tooltip vẫn có trạng thái/số lượng/tỷ lệ, danh sách gần nhất rộng60% desktop và xuống dòng đọc đủ thông tin. Giữ sáu KPI, màu, biểu đồ dưới, bộ lọc, nguồn, công thức, exporter, Công của tôi, quyền, credential, cron và dữ liệu. Diff phạm vi rộng003 đã lưu riêng/hoàn nguyên, không ship security/migration mới. [Nghiệm thu](demo/ATTENDANCE_ADMIN_UI_001_ACCEPTANCE.md).
- Kiểm thực ban đầu: Python/Ruff/XML/SCSS/JS/diff PASS, Node hồi quy xuất/lọc/polling PASS; suite Odoo96 có2 test kỳ vọng menu nhập cũ, đã cập nhật và chạy lại2/2 đạt. Admin trước8 ảnh/sau16 ảnh cùng DB/kỳ, 0 lỗi JS; sửa Owl `t-model` không tương thích. XLSX3kỳ đối chiếu0sai lệch, previewHTML đã xem; dashboard4width0overflow, hover đúng thông tin. Delegate/employee ORM đạt nhưng browser login403, visual2role NOT RUN. Kết quả ở acceptance. Local18069 vẫn sealed20.0.3.3.0 khác PC20.0.3.5.1 nên không áp module mới lên local cũ. Workflow snapshot release tách foreign WIP, không finish thay tác vụ khác.

## CHG-20261120-001 — ATTENDANCE-WORKSPACE-003: hợp nhất ưu tiên giữ sáu thẻ, dashboard chung

- 20/11/2026 Asia/Saigon; phiên điều phối hợp nhất prompt gốc người dùng và bổ sung mới, lấy ảnh `38c53f30-9104-4127-88c9-878af3fad5c6` đã duyệt làm căn cứ hình thức. [Prompt Claude](prompts/CLAUDE_ATTENDANCE_WORKSPACE_003_SHARED_DASHBOARD.md) thay yêu cầu bốn thẻ/35–65 cũ bằng giữ sáu thẻ, màu, donut, recent, biểu đồ dưới và tất cả bộ lọc; căn tên/phòng/giờ, responsive, live và một component mọi vai trò. Công của tôi/XLSX/connector admin/nhãn trung tính vẫn trong scope gốc.
- Audit source ghi rõ phần đã có và delta: một dashboard hiện có; ellipsis gây cắt thông tin; gate cấu hình/manual sync/mapping/log còn HR/system, phải dùng original/live delegate đúng công ty và kiểm RPC; secret scope/lưu không side effect; live pending race cần tái hiện. Giữ capability chốt/xuất hiện hành, DEC-054/061/062/063 và dữ liệu thật. Không sửa application code, DB, quyền, credential hoặc runtime.
- Kiểm thực: đọc ảnh và source/callers/test; `dev.py status` local Odoo/PostgreSQL đang nghe; Node test dashboard lỗi harness `AttPager is not defined` có sẵn; `ai_workflow.py check` FAIL trước sửa vì foreign WIP. Chạy `start`, giữ checkpoint và AI_WORKFLOW_STATE cũ; không finish nhận thay foreign source. Kiểm nội dung/link và `git diff --check` cho tài liệu. Chưa browser ba vai trò/4 viewport/XLSX mới; đây là prompt sẵn giao, không nghiệm thu tính năng hoặc triển khai UI.

## CHG-20261119-032 — Đã áp sửa đồng bộ nhóm cán bộ chấm công lên PC server

- 20/11/2026 08:38 giờ VN, theo yêu cầu “Áp lên PC”: release từ `3bc55406` (3 file, checksum khớp), `tp_hr_attendance` 20.0.3.5.0 → 20.0.3.5.1, upgrade exit 0/0 ERROR. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-officer031-20261120T083838` (dump + `pg_restore -l`, filestore, source, config, SHA256). Snapshot trước/sau giống hệt, chỉ đổi phiên bản; nguồn module PC khớp commit 78/78 file trước và sau.
- Kiểm guard trên dữ liệu thật bằng transaction rollback: HR manager không phải Quản trị gốc bị chặn khi ghi thành viên từ phía nhóm, thêm/gỡ phân công nhân viên thường đồng bộ đúng nhóm, phân công cho admin bị chặn kèm thông báo; không ghi gì vào DB.
- Health 200/login 302 cục bộ và công khai, log container 0 ERROR. Lần đầu quan sát được nhịp 15 giây trên PC: 9 lượt đọc hôm nay thành công liên tiếp 08:41:55–08:43:58, lượt không đổi không ghi DB, trùng lặp 0. [Nghiệm thu §7](demo/ENTI_ATTENDANCE_002_ACCEPTANCE.md#7-pc-server--sửa-đồng-bộ-nhóm-cán-bộ-chg-20261119-032).

## CHG-20261119-031 — Sửa đồng bộ nhóm cán bộ chấm công bị guard ủy quyền admin chặn

- 20/11/2026 Asia/Saigon; người dùng chọn “Làm ở đây” cho việc tách ra từ ENTI-ATTENDANCE-002. `tp_hr_attendance` 20.0.3.5.0 → 20.0.3.5.1, không đổi dữ liệu/ACL/view.
- `_tp_sync_officers` thêm/bỏ nhóm `group_attendance_officer` từ phía tài khoản (`res.users.group_ids`, link/unlink từng người) thay vì ghi `user_ids` của nhóm — đúng đường đổi quyền thường mà guard `tp_admin_delegation` cho HR với tài khoản nhân viên (DEC-054). Không sửa `tp_admin_delegation`: ghi thành viên từ phía nhóm vẫn chỉ Quản trị gốc; tài khoản admin chỉ Quản trị gốc đổi, phân công cho admin bị từ chối cả bản ghi với thông báo “Không cập nhật được quyền Chấm công…”.
- Test mới `test_officer_sync_keeps_admin_delegation_guard`: HR ghi thành viên nhóm trực tiếp bị chặn; phân công cho admin bị chặn và không để lại bản ghi/thành viên; thêm/gỡ phân công nhân viên thường vẫn đồng bộ nhóm.
- Kiểm local `tp_tanphat_test`: `-u tp_hr_attendance,tp_admin_delegation` — attendance 96 test 0 failed/0 error (trước đó 1 error); delegation 20 test, 1 test HTTP chỉ trượt vì chạy cổng 18179 trong khi script yêu cầu 18079, chạy lại `TestAdminAccountLockHttp` ở 18079: 2/2 đạt. Ruff sạch. PC hiện 0 phân công/0 thành viên nhóm nên không cần migration; chưa áp PC server.

## CHG-20261119-030 — Đã áp ENTI-ATTENDANCE-002 lên PC server

- 20/11/2026 03:25 giờ VN: release từ `51e1421b` (51 file, 7 mới, 2 bỏ, checksum khớp), `tp_hr_attendance` 20.0.3.4.1 → 20.0.3.5.0, upgrade exit 0/0 ERROR. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-20261120T032523` (dump + `pg_restore -l`, filestore, source, config, SHA256). Snapshot dữ liệu/quyền trước/sau giống hệt, chỉ đổi phiên bản module và priority cron ENTI 5 → 10; trùng lặp ngày/phiên/ngày ENTI 0.
- Đồng bộ thật: code cũ ghi lại 234 ngày công mỗi phút; code mới chạy lượt cửa sổ 03:28 (3,1 giây, 0 thay đổi, lần đầu điền `raw_hash`) rồi 5 lượt đọc hôm nay liên tiếp 03:29–03:33 (~0,25 giây, 0 lỗi); lượt không đổi không ghi ngày công/nhật ký, `last_success_at` tiến theo từng lượt. Nhịp 15 giây (05:00–22:00) chưa quan sát trên PC vì lúc kiểm ngoài khung. Độ trễ đo được chỉ là ENTI → Odoo → màn hình; máy chấm công → ENTI không đo.
- Bundle công khai có code mới, không còn hộp thoại tải tệp; health 200, login 302. Không đăng nhập tài khoản thật trên PC. Hoàng Xuân Tiến (id 44, ENTI `TP032`) đã ghép đúng từ trước, lần này chỉ kiểm. Xuất Excel trên dữ liệu thật 3 kỳ 0 sai lệch. Phút muộn giữ nguyên ENTI: tuần 09–15/11 có 23/91 lần ≥ 2 giờ do lần chấm đầu tiên rơi vào buổi chiều — chờ nhân sự quyết định. [Nghiệm thu §6](demo/ENTI_ATTENDANCE_002_ACCEPTANCE.md#6-pc-server-chg-20261119-030).

## CHG-20261119-029 — Công lấy tự động từ ENTI gần thời gian thực; Tổng quan mới; ngừng nhập tệp Excel

- 20/11/2026 Asia/Saigon; nhiệm vụ `ENTI-ATTENDANCE-002`. `tp_hr_attendance` 20.0.3.5.0. [DEC-063](DECISIONS.md), [Nghiệm thu](demo/ENTI_ATTENDANCE_002_ACCEPTANCE.md).
- Đồng bộ: máy chủ gọi ENTI, cron canonical mỗi phút; 05:00–22:00 đọc hôm nay mỗi 15 giây trong một lượt cron rồi tự hẹn lượt sau, cửa sổ 5 ngày đọc lại 5 phút/lần, lỗi lùi 30/60/120 giây; một lượt có khóa, đủ phân trang, làm mới token, thử lại có giới hạn với mạng/timeout/429/5xx. Chỉ phát bus khi ngày công đổi; lượt không đổi không ghi DB. Lỗi/ENTI trả trống không xóa công; ưu tiên điều chỉnh đã duyệt > ENTI > Excel cũ; kỳ chốt giữ nguyên. Migration chỉ đổi priority cron ENTI 5 → 10.
- Tổng quan chấm công làm lại: tiêu đề + *Tự động đồng bộ* (giờ thật), bộ lọc giữ khi tự làm mới, 6 KPI, biểu đồ chính 2/3 + 10 nhân viên có giờ vào/ra gần nhất 1/3, xu hướng, bảng cần kiểm tra; Chart.js nạp lười, bấm donut để lọc, mobile một cột. Tách *Chưa có dữ liệu / Thiếu giờ / Chưa chấm công / Nghỉ đã xác nhận / Vắng theo lịch*; vắng không tính Chủ nhật, tương lai, ngoài thời gian làm việc, nghỉ đã duyệt; một lần chấm không phải vắng; phút muộn lấy từ ENTI.
- Xuất Excel theo mẫu *Bảng chấm công* (Vào/Ra, cột ngày thật, tổng muộn/vắng, sheet Chi tiết) cho tuần/nhiều tuần/tháng. Nguồn dữ liệu liệt kê người ENTI chưa ghép kèm lý do; ghép chỉ khi có căn cứ.
- Ngừng nhập tệp Excel: gỡ mọi đường nhập trên giao diện, RPC công khai trả “Đã ngừng nhập tệp Excel chấm công…”; giữ lô/snapshot/tổng muộn/điều chỉnh/kỳ chốt làm lịch sử xem và xuất lại; không drop bảng, giữ `openpyxl`.
- Kiểm: 95 test module — 0 failed, 1 error có sẵn liên module (`test_access` bị guard `tp_admin_delegation` chặn khi đồng bộ nhóm cán bộ chấm công); browser 9/9 PASS ở 1440/768/390/320; giờ ra mới hiện 0,7 giây sau commit không tải lại (ENTI → Odoo → màn hình, không đo máy → ENTI); xuất Excel tuần/01–19/11/tháng khớp backend 0 sai lệch. Chưa áp PC server ở change này.

## CHG-20261119-028 — Đã áp lỗi thao tác trong màn (FORM-VALIDATION-002) lên PCserver

- 19/11/2026: app `70cf30a8` đã push, backup/upgrade Home 20.0.1.11.0, HR 20.0.1.19.0, KD 20.0.1.10.0 trên PCserver exit0/0ERROR; snapshot dữ liệu/quyền trước/sau giống hệt, chỉ đổi phiên bản 3 module. Backup `C:\TANPHAT-backups\form-validation002\form-validation027-20261119T214803`; dump/filestore/source/config/SHA256.
- Public health/login 200; JS/CSS public khớp SHA256 server (e1aad712/3e5f447c), có mã lỗi trong màn và rule chiều cao khối lỗi. Nguồn 23/23 checksum. Docs-only receipt đồng bộ source, không restart thêm. [Nghiệm thu](demo/FORM_VALIDATION_002_ACCEPTANCE.md).

## CHG-20261119-027 — Lỗi xóa/sắp xếp/mở hiện trong màn thay cho toast

- 19/11/2026 Asia/Saigon; nhiệm vụ `FORM-VALIDATION-002`, người dùng chọn “Làm tiếp ở đây” cho việc chuyển các màn còn dùng toast sang khối lỗi trong màn.
- `tp_web_home` 20.0.1.11.0: `saveError` nhận `verb`/`write`/`note`, `InlineErrors` nhận `intro`/`note`, câu mở/câu cuối theo thao tác; khối lỗi dùng chung `flex: 0 0 auto; width: 100%` thay `flex: 0 0 100%` để không cao hết khung flex dọc (form native đo lại không đổi).
- `tp_hr_workspace` 20.0.1.19.0: Hồ sơ của tôi (xóa kinh nghiệm/kỹ năng, mở cài đặt bảo mật) và kéo thả sắp xếp nhân viên báo lỗi trong màn, không toast; thứ tự cũ vẫn được khôi phục. `tp_kd_workspace` 20.0.1.10.0: Tổng quan báo lỗi mở hồ sơ/thêm mới/mở dự án trong màn; kiểm trước thêm công việc/WBS khi chưa chọn Dự án, không gọi máy chủ.
- Không đổi quy định bắt buộc, quyền, dữ liệu, workflow, API; backend vẫn kiểm. HOOT Home/HR/KD PASS, full HOOT không regression; browser chặn ghi 1440/390 PASS; local18069 upgrade exit0/0ERROR, snapshot giữ. [Quy chuẩn](ui/TP_FORM_VALIDATION_STANDARD.md), [Nghiệm thu](demo/FORM_VALIDATION_002_ACCEPTANCE.md).

## CHG-20261119-026 — Hoàn thành tải, đối chiếu và áp dụng dữ liệu chấm công thật từ ENTI vào database

- 19/11/2026 Asia/Saigon; nhiệm vụ `ENTI-LIVE-001`. Đã kết nối API ENTI thật, lấy dữ liệu bảng công từ ngày 01/11/2026 đến 19/11/2026, đối chiếu định danh nhân sự và áp dụng thành công vào hệ thống database chính trên PC server (`192.168.1.73`).
- `tp_hr_attendance` 20.0.3.4.1: sửa cơ chế bọc `internal(...)` chống chặn quyền trực tiếp khi áp session/ngày công và chuẩn hóa thuật toán đối chiếu 1-1 theo họ tên NFC.
- Kết quả đối chiếu nhân viên: 38/39 nhân viên đã khớp chính xác 1-1 với hồ sơ `hr.employee` trong Odoo HR (`state='mapped'`); 1 nhân viên (`Hoàng Xuân Tiến` — `TP032`) được đưa vào danh sách **Chờ đối chiếu** (`state='unmapped'`, lý do: *Chưa tìm thấy nhân viên phù hợp trong Odoo HR*) đúng quy định bảo vệ dữ liệu Odoo HR.
- Kết quả áp dụng dữ liệu công: Nhận 741 bản ghi ngày công từ ENTI, áp dụng thành công **722 ngày công** vào bảng công chuẩn `tp.hr.attendance.day` (`source_kind='enti'`), tạo **399 phiên vào - ra** thực tế trong `tp.hr.attendance.session` (`source='enti'`). 19 ngày công của nhân viên chưa khớp được lưu trữ an toàn tại `tp.hr.attendance.enti.day` ở trạng thái `pending_map`.
- Xử lý đủ và thiếu giờ: Các ngày chỉ có giờ vào hoặc chỉ có giờ ra ghi nhận đúng `data_state='missing'`, không tự điền giả 17:00, không vi phạm ràng buộc `check_out > check_in`. Các ngày đủ giờ ghi nhận `data_state='ok'` và tính đúng số giờ làm việc thực tế.
- Tự động hóa & Runtime: Cron `ir_cron_enti_attendance_sync` quét tự động mỗi 1 phút; container `tp-odoo` đã khởi động lại sạch 0 lỗi; endpoint Cloudflare `https://eight-championships-launches-plaintiff.trycloudflare.com/web/health` trả về HTTP 200 OK.

## CHG-20261119-025 — Tích hợp chấm công ENTI thật, tự động đồng bộ theo lịch và cập nhật UI trực tiếp

- 19/11/2026 Asia/Saigon; nhiệm vụ `ENTI-LIVE-001`. Tích hợp API chấm công ENTI (`enti.vn`) trực tiếp từ backend Python (`EntiClient` qua session HTTP an toàn), tự động chọn ứng dụng công ty Tấn Phát, quản trị token và refresh token không qua trình duyệt.
- `tp_hr_attendance` 20.0.3.4.0: đối chiếu nhân viên `tp.hr.attendance.enti.mapping` bảo vệ Odoo HR là Single Source of Truth; lưu trữ bất biến dữ liệu thô `tp.hr.attendance.enti.day`; xử lý đầy đủ các ca chưa đủ giờ (in-only / out-only) không bịa 17:00 và không vi phạm ràng buộc `check_out > check_in`; phân cấp ưu tiên nghiêm ngặt (Điều chỉnh đã duyệt > Live ENTI > Excel fallback); cron tự động `ir_cron_enti_attendance_sync` quét mỗi 1 phút; bus notification `bus.bus` + polling ngầm 30s cập nhật giao diện Dashboard, Bảng công, Công của tôi và Nguồn dữ liệu mà không cần F5; wizard cấu hình bảo mật mật khẩu không lộ log/trình duyệt. Migration `20.0.3.4.0` gỡ ràng buộc `_live_off`. Unit test pure 4/4 PASS, test Odoo ORM đầy đủ. [Nghiệm thu](demo/ENTI_LIVE_001_ACCEPTANCE.md), [runbook](../ops/runbooks/ENTI_LIVE_001_DEPLOY_AND_ROLLBACK.md).



## CHG-20261119-024 — Đã áp thông báo thông tin còn thiếu và tìm tên trực tiếp lên PCserver

- 19/11/2026: app `720d7fa9` đã push, backup/upgrade HR 20.0.1.18.0 và Home 20.0.1.10.0 trên PCserver exit0/0ERROR; snapshot dữ liệu/quyền trước/sau giống hệt, chỉ đổi phiên bản module. Backup `C:\TANPHAT-backups\form-validation001\form-validation023-20261119T182936`; dump/filestore/source/config/SHA256.
- Public health/login 200; JS/CSS public khớp SHA256 server (e8b9a2c9/5b4b6a4e), có presenter validation và tìm tên. Nguồn 29/29 checksum. Không đụng 6 file JS chưa commit của phiên khác đang có trên server. Docs-only receipt đồng bộ source, không restart thêm. [Nghiệm thu](demo/FORM_VALIDATION_001_ACCEPTANCE.md).

## CHG-20261119-023 — Thông báo rõ thông tin còn thiếu khi thêm mới/lưu; khôi phục tìm tên trực tiếp

- 19/11/2026 Asia/Saigon; nhiệm vụ `FORM-VALIDATION-001` theo yêu cầu “tiếp tục … THÔNG BÁO RÕ THÔNG TIN CÒN THIẾU CHO MỌI MÀN THÊM MỚI”. `tp_web_home` 20.0.1.10.0 thêm presenter dùng chung `static/src/validation/`: khối “Chưa lưu được. Vui lòng kiểm tra N thông tin” trong form/popup/wizard/quick-create thay toast chung; mỗi dòng có nhãn đang hiển thị, tab/nhóm, cách sửa, bấm mở tab và focus đúng ô; khung đỏ, câu dưới ô, số lỗi trên tab, `*` chỉ ô bắt buộc sửa được (gỡ rule `*` cũ trong `inputs.scss`), tự cập nhật khi sửa, không nhảy focus. Bảng con báo theo dòng; popup giữ lỗi và không đóng.
- Lỗi lưu từ backend hiện trong form theo loại (`saveError`): thiếu, định dạng/dữ liệu, trùng, ngày, quyền, bản ghi không còn, nghiệp vụ, kết nối, hệ thống; giữ nguyên văn câu backend, lỗi hệ thống không lộ traceback/tên trường/giá trị. 0/False không bị coi là thiếu. Form OWL tự viết dùng `InlineErrors` + `saveError`.
- `tp_hr_workspace` 20.0.1.18.0: banner “khuyến nghị hoàn thiện hồ sơ (không chặn lưu)” cho Mã NV/Phòng ban/Chức vụ; `version_id` ẩn khi chưa lưu nên hồ sơ mới không còn đòi; Hồ sơ của tôi và hộp thoại tài khoản dùng khối lỗi. Gộp ba chiều khôi phục tìm tên trực tiếp/hồ sơ responsive CHG-020 bị `5b9910b3` gỡ, giữ phần chỉ xem của CHG-022.
- Kiểm: HOOT Home57/296, HR50/243, KD22/85, Equipment2/4 PASS; full HOOT 1429 pass/11 fail core giống HEAD (HEAD 13 fail gồm 2 test HR tìm tên, nay PASS). Odoo `/tp_hr_workspace,/tp_web_home` 103 test, 8 fail/2 error có sẵn trên HEAD; test mới về `version_id` PASS. Browser Chromium chặn mọi RPC ghi trên local18069 PASS. Local upgrade exit0/0ERROR, snapshot dữ liệu/quyền giữ, backup `.local/validation001/main-backup-20261119T181303`. Quy chuẩn [validation](ui/TP_FORM_VALIDATION_STANDARD.md), [nghiệm thu](demo/FORM_VALIDATION_001_ACCEPTANCE.md); chưa PC server ở mốc ghi này.

## CHG-20261119-022 — Đồng bộ giao diện HR chỉ xem và bảo vệ dữ liệu đồng nghiệp

- 19/11/2026 Asia/Saigon; nhiệm vụ `HR-UNIFIED-READONLY-UI-001`. Đồng bộ toàn diện giao diện quản lý nhân sự giữa Admin và Nhân viên thường: cùng ngôn ngữ thiết kế, cùng cấu trúc bảng, chiều cao hàng, avatar cạnh họ tên, nhóm phòng ban, tìm kiếm, lọc và phân trang trên cả Desktop và Mobile qua `view_mode="list,form"`.
- Bỏ tiêu đề "Danh bạ nhân viên" lặp lại và đoạn giải thích cồng kềnh; thống nhất tên "Danh sách nhân viên" kèm nhãn "Chỉ xem" nhỏ gọn.
- Bảo tồn thứ tự phòng ban (`tp_sequence, id`) và thứ tự nhân viên đã kéo thả (`sequence, id`); vô hiệu hóa kéo thả đối với người xem chỉ xem.
- Bảo vệ dữ liệu đồng nghiệp: ẩn hoàn toàn 3 tab nhạy cảm (Hợp đồng lao động, Lịch sử hoạt động, Tài khoản và phân quyền) và tab cá nhân khi mở chi tiết đồng nghiệp; không lộ tên tab, nội dung, bộ đếm hay liên kết. Bảo toàn quyền tự phục vụ khi xem hồ sơ cá nhân qua kiểm tra ID nhân viên thực tế `user._tp_main_employee().id == employee.id`.
- Màn hình Tổng quan public an toàn: chỉ trả về tổng số nhân viên và cơ cấu phòng ban được phép, ẩn mọi nút tác vụ, import, export và các chỉ số tài khoản/chất lượng hồ sơ.
- Bảo vệ backend nhiều lớp trên `hr.employee.public`: chặn mọi thao tác thêm, sửa, xóa, copy, export, RPC direct write; chuyển hướng an toàn deep link quản trị `hr.employee` sang `hr.employee.public` bằng `RedirectWarning`.
- Bộ test tự động 45/45 PASS trên `tp_tanphat_test` (0 failed, 0 error). Playwright browser test đạt 100% trên desktop và mobile cho cả Admin và Nhân viên; lưu bằng chứng hình ảnh tại `docs/demo/evidence/hr_unified_readonly_001/`. [Nghiệm thu](demo/HR_UNIFIED_READONLY_001_ACCEPTANCE.md).

## CHG-20261119-021 — Đã áp bản hồ sơ và tìm tên lên PCserver

- 19/11/2026: app `b96a4cb5` đã push, backup/upgrade HR20.0.1.17.0 và Home20.0.1.9.1 trên local18069/PCserver exit0/0ERROR; giữ snapshot dữ liệu/quyền. Server backup `C:\TANPHAT-backups\hr-profile-live001\hr-profile-live020-20261119T160823`; dump/filestore/source/config/SHA256 verified.
- Public health/login200 và actual JS/CSS SHA256 bằng server, có live-name/profile styles. Nguồn19/19checksum; browser/unit/HOOT PASS; giới hạn và evidence trong [acceptance](demo/HR_PROFILE_LIVE_SEARCH_001_ACCEPTANCE.md). Chưa business acceptance; yêu cầu validation bổ sung là batch tiếp. Docs-only receipt source sync, không restart thêm.


## CHG-20261119-020 — Hồ sơ HR responsive và tìm tên ngay khi gõ

- 19/11/2026 Asia/Saigon; người dùng giao thực thi trực tiếp “làm đi” sau prompt hợp nhất. Phần bổ sung trực tiếp giới hạn bỏ thanh search lớn tại Danh sách nhân viên và autocomplete/lọc tên từ ký tự đầu, không cần Enter; tài liệu đính kèm là tham chiếu thiết kế hồ sơ.
- HR20.0.1.17.0/Home20.0.1.9.1. Native AutoComplete/SearchModel/ORM: gợi ý chứa từ khóa theo quyền, chống stale response, composition tiếng Việt, chọn ID phân biệt người trùng tên; chỉ áp tiêu chí tên, giữ điều kiện khác. Native menu lọc/nhóm/favorite vẫn dùng được; không thay search bảng KH-KD/báo cáo.
- Profile/My Profile sửa rule gốc typography/grid/card/tabs/wrapping và popup; không đổi model/state/quyền/API hoặc ghi hồ sơ thật. [Bàn giao và kiểm](demo/HR_PROFILE_LIVE_SEARCH_001_ACCEPTANCE.md). [Ngoại lệ quy chuẩn](ui/TP_TABLE_FILTER_STANDARD.md), [inventory](ui/TP_TABLE_FILTER_INVENTORY.md).
- Đã kiểm syntax AST/XML/Node, libsass, compile7OWL template và test logic cô lập; local upgrade exit0/0ERROR và snapshot hash tài khoản/quyền/liên kết/nghiệp vụ giữ. Browser7tab9width/10behavior+10extra PASS, HOOT48test243assertion PASS; không fixturemain, không18079.
- Backup local `.local/hr-profile-live001/main-backup-20261119T153938`: dump/pg_restore-list/filestore DB-referenced/source/config/SHA256. Chưa deploy PCserver ở mốc ghi này. Giữ foreign WIP/checkpoint, seal snapshot HEAD+scope khi sẵn sàng; không finish hộ batch khác. Next: commit/push/deploy đúng scope, kiểm public và bàn giao receipt; yêu cầu validation mới sẽ triển khai batch riêng.

## CHG-20261119-019 — Giao quyền quản lý tài khoản admin lên local và PC server

- 19/11/2026 Asia/Saigon, theo quyền triển khai đã giao và DEC-051/062. App `3442143c6c23c6384a0450a1e61a361dcf8352fb` đã push origin/main và áp local18069 + PCserver; HR20.0.1.16.0/admin20.0.2.1.0, exit0/0ERROR mỗi môi trường. Các addon/session/tunnel/config khác giữ.
- Backup PC `C:\TANPHAT-backups\admin-account-policy001\admin-account018-20261119T150313`: dump10.191.206B, pg_restore-list15.790mục, filestore628mục/32.038.793B, source/config và SHA256. Local `.local/admin-account-policy001/main-backup-20261119T150023`: dump/pg_restore-list, 150.508.243B filestore DB-referenced, source/config/SHA256. Không snapshot GC orphan và không xóa dữ liệu hiện hành.
- Snapshot trước/sau giữ39employee/32user, groups/implied, login/password/active/locks/revision, company/partner/resource/roster, toàn ledger cấp quyền và nghiệp vụ; chỉ2module version đổi. Không cấp/thu/khóa/reset tài khoản người thật. Main/server không fixture test. Local không grant hiện có; PC5grant live, original capabilitymanage=true và leveldelegated, mọi peer cấm sửa/rename/manage.
- Probe READ ONLY 13/13 local, 68/68 PC server; source28/28SHA256, public health/login200, actual JS/CSS khớp server và có controller/dialog/readonly mới. Odoo40/40, race2/2 và browserdesktop/mobile đã PASS ở018. [Bằng chứng](demo/ADMIN_ACCOUNT_POLICY_001_ACCEPTANCE.md); chưa authenticated real-user public E2E hoặc iOS/Safari. Người dùng nghiệm thu hình thức/nghiệp vụ riêng.
- Snapshot HEAD+scope và private index giữ foreign checkpoint18/11/WIP; receipt chỉ tài liệu, không restart/upgrade. Next: Ctrl+F5 và nghiệm thu UI/thao tác theo quyền mới; không dùng kết quả kỹ thuật thay business acceptance/pilot authorization.

## CHG-20261119-018 — Quyền quản lý tài khoản và hồ sơ admin

- 19/11/2026 Asia/Saigon; yêu cầu trực tiếp đính kèm cho phép phiên chính triển khai. DEC-062 thay revoke-first lock, giữ DEC-053/054: chỉ admin gốc cấp/thu admin, delegate quản trị nghiệp vụ toàn hệ thống nhưng không sửa peer/original account/profile.
- Sửa nguyên nhân tại capability/wizard/backend: bỏ loại toàn bộ system-group target cho original; helper actor-target chung bảo vệ cả inactive grant/group, không tin sudo/context; chặn mọi field/CRUD/link trên user/employee/partner/resource/hr.version, preflight bulk; UI readonly/ẩn controls và nhãn loại tài khoản. Khóa native active/hr_locked/revision giữ session invalidation; ledger không đổi. Audit append-only có lý do/snapshot đã khử credential.
- Phiên bản HR20.0.1.16.0/admin20.0.2.1.0. Không core Odoo/API/React; không nghiệp vụ/reporting/equipment mới. Không bảng mới; [inventory](ui/TP_TABLE_FILTER_INVENTORY.md) ghi N/A form/wizard và tái dùng search/audit hiện có.
- Đã đạt 40/40 Odoo, HTTP/browser synthetic trên tp_tanphat_test sau dump/pg_restore-list/filestore DB-referenced/source/config/SHA256 `.local/admin-account-policy001/test-backup-20261119T143137`; không tạo DB mới hoặc sửa tài khoản thật. AST/XML/Node/Ruff/diff-check PASS; kết quả cuối và receipt sau deploy ghi [acceptance](demo/ADMIN_ACCOUNT_POLICY_001_ACCEPTANCE.md). Không coi kiểm kỹ thuật là nghiệm thu nghiệp vụ.
- Giữ checkpoint foreign18/11/index/WIP; snapshot sạch HEAD+đúng scope cho finish/check/commit, không seal code dở của phiên khác. Next: hoàn tất kiểm, commit/push scope và deploy local/PCserver sau backup, kiểm public thật.

## CHG-20261119-017 — Giao bản sửa nút đổi tên đăng nhập lên local và PC server

- 19/11/2026: app `cf4cf11411cd0d89b2e76c5d7be4723ef9817c37` đã push origin/main và áp riêng HR `20.0.1.15.1` / admin delegation `20.0.2.0.3`. Hai môi trường upgrade exit 0, 0 ERROR. Không áp WIP khác; chấm công PC giữ `20.0.3.3.0`, local giữ `20.0.3.1.0`.
- Backup local `.local/hr-login-rename-fix016/main-backup-20261119T140631`: dump 10.480.205 B, filestore 1.700.605.234 B, source/config/restore-list/SHA256. PC `C:/TANPHAT-backups/hr-login-rename-fix016/hr-login016-20261119T140905`: dump 10.182.487 B, restore-list 15.790 mục, filestore 630 mục / 33.846.814 B, source/config 2.254.942 B và SHA256. Chỉ hai module version đổi trong snapshot; login/password, nhóm, công ty, roster/resource, sequence và nghiệp vụ giữ nguyên.
- Probe READ ONLY 21/21 PASS mỗi môi trường, xuất XLSX đọc login hiện tại. Đúng employee 63 trên PC là admin được cấp: admin gốc đổi tên được (`tp_can_change_login=true`), khóa/reset vẫn chặn (`tp_can_manage_account=false`), native view có nút với điều kiện đúng. Local target là nhân viên thường nên khóa/reset vẫn theo quyền hiện hành; không cấp admin để ép dữ liệu hai môi trường giống nhau. Không đổi login người thật.
- Nguồn server 10/10 SHA256; health/login local/server/public 200. JS public `ae4c8b5`, CSS `73d8d48` khớp SHA256 server và có dialog/validation/re-login thực. Không đổi static JS trong bản sửa nên URL bundle giữ như bản attendance gần nhất là đúng. Kiểm Odoo 8/8, browser synthetic original → granted admin desktop/mobile 0 lỗi tại CHG016; không đăng nhập mới hoặc rename người thật.
- [Acceptance](demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md) ghi vị trí dưới Chức vụ nhân sự, trên Quyền bổ sung đang giữ. Cốc Cốc trực tiếp bị công cụ chặn URL policy; đã dừng, không bypass. Authenticated public E2E bằng tài khoản thật và iOS/Safari thật NOT_RUN. Receipt tài liệu dùng snapshot sạch/index riêng, giữ checkpoint 18/11 và foreign WIP; không restart Odoo khi đồng bộ tài liệu. Nghiệm thu hình thức/nghiệp vụ chờ người dùng.

## CHG-20261119-016 — Sửa nút đổi login bị ẩn với admin được ủy quyền

- 19/11/2026; tiếp tục yêu cầu triển khai và ảnh “đâu”. Probe read-only PC: admin gốc đang xem tranphuongdong (employee63), target có system/grant, không phải original; cả account/rename capabilityfalse do dùng nhầm guard khóa/reset. Đây là thiếu sót bản013/014, không phải người dùng vào sai tab hoặc thiếuCtrl+F5.
- Thêm tham số private login_rename cho guard/wizard và luồng res.users.write; chỉ admin gốc được ngoại lệ rename trên admin được cấp, sau ACL/company/system/self/original protections. Khóa/reset giữ mặc định, không mở credential của admin gốc cho delegate. Wizard capability riêng và inherited view không ẩn rename theo lock/reset; delegated form tách visibility từng thao tác. HR20.0.1.15.1/admin20.0.2.0.3, nâng riêng2addon.
- Odoo8/8PASS: rename5, HttpCase2 (Playwright1440/390px target có grant thật và actor original giả; duplicate inline/Cancel/Save/reload0pageerror), hồi quy reset1. Giữ password hash/group/company/resource/department/job/avatar bytes/grant active vàaudit; peer/self/staff/HR/sudo từ chối. Lần đầu snapshot so object BinaryValue báo khác dù cùng attachment, sửa so bytes; lần rerun dải mã test đã cạn do nextval không rollback, fixture BaseHrWorkspace reset về floor và restore sequence bằng cleanup theo mẫu test hiện có. Không sửa allocator/runtime để né test. AST/XML/Ruff/Node/diff --checkPASS; race/unique core không đổi, giữ bằng chứng013.
- Backup test mới `.local/hr-login-rename-fix016/test-backup-20261119T135937`: dump/restore/source/config/SHA256 +filestoredelta với baseZIP backup013 (content addressed, danh sách phục hồi ghi rõ), không tạo/restoreDB mới. Main/server không tạo fixture, không đổi login tài khoản thật. Cốc Cốc trực tiếp bị CUA chặn vì URL policy chưa hỗ trợ, dừng CUA; browser fixture độc lập đạt, không tuyên bố đã điều khiển cửa sổ người dùng.
- [Acceptance](demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md) ghi giới hạn vàreceipt sau deploy. Không bảng mới; inventory ghi N/A form và tái dùng audit/list. Giữ checkpoint/WIP khác, private index và workflow snapshot sạch. Technical verification khác business acceptance.

## CHG-20261119-015 — Giao PC server: admin được ủy quyền duyệt điều chỉnh công

- Giao commit ứng dụng `af72ede1` (CHG-20261119-012) lên PC server: addon `tp_hr_attendance` `20.0.3.2.0 → 20.0.3.3.0` bằng `-u tp_hr_attendance` theo [runbook](../ops/runbooks/HR_ATTENDANCE_001_DEPLOY_AND_ROLLBACK.md). Script riêng `.local/admin-approve012/deploy012.py` + `deploy-server012.ps1`; 12 tệp (1 tệp mới là migration), giữ `mtime` theo commit.
- Kiểm trước (chỉ đọc): nguồn server khớp baseline `44b0c9e2` 64/64 tệp, không có tệp lạ. Admin chính `admin` (uid 2, công ty 1). Công ty 1 có 5 grant ủy quyền đang hiệu lực: `tuanln`, `thuannv`, `thipt`, `tranphuongdong`, `namvd`. Server có 0 phiếu điều chỉnh, 0 phân công, 0 kỳ chốt. Phiên HR-LOGIN-RENAME đang nâng cấp server (container `tp-hr-login013-upgrade`). Chờ phiên đó xong và server yên rồi mới chạy, không chồng lên.
- Backup `C:\TANPHAT-backups\admin-approve012\admin-approve012-20261119T133902`: `tp_tanphat_dev.dump` `10.181.205`B (`restore-list` `15.790` mục), `filestore.tar.gz` `32.036.864`B, `source-config.tar.gz` `199.970`B, `SHA256SUMS.json`. Dừng `tp-odoo`, chạy `-u` trong container một lần, khởi động `tp-odoo` lúc 06:40:21Z; không restart tunnel.
- Kết quả: upgrade exit 0, log nâng cấp và log sau khởi động 0 ERROR, `/web/health` và `/web/login` 200. Module `20.0.3.3.0`; nguồn khớp commit 65/65. ACL chấm công `55 → 54`: đúng dòng `access_att_correction_reviewer` bị xóa. Nhân sự 39, tài khoản 32, digest nhóm, roster, phiên 384, ngày công 480, đi muộn 117, lô 5, sổ ủy quyền và `web.base.url` không đổi.
- Probe ORM chỉ đọc: `correction_admins(công ty 1)` = `admin`, `namvd`, `thipt`, `thuannv`, `tranphuongdong`, `tuanln`, tức Admin chính cộng đúng 5 grant đang hiệu lực. Menu `Xử lý điều chỉnh` hiện với cả 6. Không có phiếu chờ nên migration không phải đổi người nhận.
- Public `https://eight-championships-launches-plaintiff.trycloudflare.com`: `/web/health`, `/dang-nhap` 200. Bundle `/web/assets/73d8d48/web.assets_web.min.css` (SHA256 `3dda3b6e…cff2`) và `/web/assets/ae4c8b5/web.assets_web.min.js` (SHA256 `d4432e9a…f22e`) có chuỗi giao diện mới.
- Local `18069` chưa áp: cổng này đang chạy candidate của phiên HR-LOGIN-RENAME (`.local/hr-login-rename-impl001/main-candidate`); DB local `tp_tanphat_dev` còn `tp_hr_attendance` `20.0.3.1.0`. Không dừng hay sửa runtime của phiên khác. Áp sau bằng `-u tp_hr_attendance` có backup khi runtime đó rảnh.
- Không tạo, gửi hay duyệt phiếu nào trên server; không đổi tài khoản/quyền ngoài phạm vi. `docs/AI_WORKFLOW_STATE.json` sinh từ đúng cây commit trong thư mục tạm; checkpoint và tài liệu dở của phiên khác được giữ nguyên.

## CHG-20261119-014 — Giao local/PC server: đổi tên đăng nhập nhân viên

- App `0ba04faf88f03f34400e628968ff6624e9a5f82c` đã push origin/main và deploy riêng tp_hr_workspace20.0.1.15.0 + tp_admin_delegation20.0.2.0.2. Local dùng main-candidate giữ các addon runtime đang chạy; không tự áp chấm công/báo cáo/sidebar/branding WIP. PCserver16/16tệp đúngSHA256 vàmtimeGit, chỉ nâng2addon, không restart tp-tunnel.
- Backup local `.local/hr-login-rename-impl001/main-backup-20261119T132213` (dump10.477.809B, filestore1.692.120.615B, source/config/restore-list/SHA256). PC `C:/TANPHAT-backups/hr-login-rename-impl001/hr-login013-20261119T133244`: dump10.191.650B, restore15.789mục, filestore636entry/34.322.377B, source/config2.234.534B vàSHA256. Upgrade exit0/0ERROR cảhai môi trường.
- Snapshot trước/sau chỉ2moduleversion đổi; giữ39employee/32user, credentials digest gồm login/password/active/partner, company membership/resource links/employee roster/department/job/sequence/groups/implied, equipment/proposal/grants/days/baseURL. Không đổi login hay mật khẩu người thật. Backend chỉ đọc17/17PASS mỗi môi trường, gồm related/unique/action/audit/capability/refuse ordinary+sudo/export đúng nguồn hiện tại.
- Public https://eight-championships-launches-plaintiff.trycloudflare.com health/login200; JS `/web/assets/993d7c1/web.assets_web.min.js`8.484.470B SHA256efbc0887c4d0…7d7b819, CSS73d8d48 SHA2563dda3b6e09d9…98cff2 khớpserver; thực tải có client action/template/input/validation/re-login. Local JS6a2b665/CSS34096a9 có giao diện mới, health/login200. Source checksum không dùng thay bằng chứng asset.
- Kết quả kỹ thuật013: backend4+account5+HttpCase2 và race2PASS; browser desktop/mobile/inline/cancel/save/reload0error; HTTP tên mới với password cũ thành công, cũ/sai case từ chối, native token thay đổi, Excel sau rename đúng. Chưa authenticated public E2E hoặc iOS/Safari thật; không login mới thay phiên người thật. [Acceptance](demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md). Người dùng Ctrl+F5 và nghiệm thu nghiệp vụ/hình thức riêng.
- Receipt tài liệu dùng index riêng + workflow snapshot sạch, giữ checkpoint18/11 và foreign WIP. CHG013 rebase onto concurrent commitattendance012 trước commit, chỉ sourceHR/admin của hạng mục này được đóng gói và deploy; runtime chấm công ngoài scope giữ nguyên theo từng môi trường.

## CHG-20261119-013 — Triển khai đổi tên đăng nhập nhân viên

- 19/11/2026 Asia/Saigon; người dùng trực tiếp giao phiên chính triển khai, thay vai trò chỉ điều phối trong hạng mục009. Tiếp nhận WIP `hr_account_wizard.py`/`hr_history.py`; hoàn thiện trong custom_addons, không sửa core/API/React. HR `20.0.1.15.0`, admin delegation `20.0.2.0.2`.
- Dialog native OWL dùng account assets có sẵn: nhân viên/tên hiện tại/tên mới, Lưu/Hủy, lỗi tại ô nhập, focus/reload/390px; thông báo mật khẩu giữ nguyên và phiên cần đăng nhập lại. Giữ thao tác tạo tài khoản cho người chưa có. Backend gốc res.users.write kiểm actor không suy quyền từ sudo, ACL/phạm vi, bảo vệ admin gốc/hệ thống/self theo policy hiện hành; kiểm stale link/login sau khóa, giữ related tp_user_login, unique case-sensitive toàn DB bằng constraint res_users_login_key. Audit actor/time/userID/old/new append-only và chatter cùng savepoint, không password/token.
- Test thật trên tp_tanphat_test hiện có sau backup `.local/hr-login-rename-impl001/test-backup-20261119T125912`: 4/4 backend + 5/5 hồi quy tạo/reset/liên kết; 2/2 HttpCase gồm Playwright desktop/mobile với tài khoản giả và real HTTP password auth (mới đúng case thành công; cũ/sai case thất bại; token native đổi); 2 race độc lập đổi–đổi/tạo–đổi mỗi cặp đúng một winner, cleanup fixture. Native SQL unique errors trong race là kết quả mong đợi. Excel thật openpyxl có tên mới; snapshot synthetic giữ ID/password hash/group/company/resource/department/job/avatar. Ruff/AST/XML/Node/validator8cases và diff --check PASS. Chưa chạy full HOOT hoặc iOS/Safari thật; không thử đổi tài khoản người thật.
- Lần đầu browser dùng accessible name tab không khớp icon; sửa selector theo DOM đã quan sát. Probe JSON-RPC phiên hết hạn gặp Windows socket reset trong harness; thay bằng đối chiếu session token native trước/sau, HTTP old/new auth độc lập vẫn kiểm thật và đạt. Không sửa product để né lỗi harness. Log GC filestore test WinError5 có sẵn, không xóa blob hoặc đổi quyền ngoài scope.
- [Acceptance/cách dùng](demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md), [runbook/rollback](../ops/runbooks/HR_LOGIN_RENAME_001_DEPLOY_AND_ROLLBACK.md); không có bảng mới, inventory ghi N/A popup và tái dùng search/export. Tách technical verification với business acceptance; commit/push/deploy ghi receipt sau khi chạy. Workflow seal từ snapshot HEAD + đúng scope, giữ checkpoint18/11 và WIP/index của phiên khác.

## CHG-20261119-012 — Admin được ủy quyền duyệt điều chỉnh công

- 19/11/2026; yêu cầu trực tiếp “quyền admin là toàn quyền chừ việc tự bổ nhiệm quyền admin cho người khác thôi” ([DEC-061](DECISIONS.md)). `tp_hr_attendance` `20.0.3.2.0 → 20.0.3.3.0` (Python/view/ACL/JS + migration, **cần** `-u tp_hr_attendance`).
- Backend: `require_correction_admin` / `correction_admins` thay `require_original_admin` / `original_admins`. Người duyệt là Admin chính hoặc admin ủy quyền có grant đang hiệu lực ở công ty của phiếu. Duyệt/trả lấy khóa chia sẻ của `tp_admin_delegation` để không lẫn với thu hồi đồng thời. Menu `Xử lý điều chỉnh`, `tp_can_review` và danh sách `Admin nhận duyệt` dùng cùng kiểm tra. Logic `action_approve` / `action_return` không đổi.
- Bỏ dòng ACL `access_att_correction_reviewer` (đọc theo `reviewer_user_ids`) để admin bị thu hồi mất quyền xem ngay. Migration `20.0.3.3.0` làm mới danh sách người nhận của phiếu đã gửi. Lời nhắc và thông báo đổi thành “admin (admin gốc hoặc admin được ủy quyền)”.
- Sửa kèm hiển thị trên cùng màn hình: ô Minh chứng trống không còn in chữ `false` (widget binary chỉ đọc của Odoo).
- Kiểm `TestAttendanceCorrection` 11/11, thêm `test_admin012_delegate_returns_own_blocked_and_revoke_is_immediate`. Bộ `/tp_hr_attendance` 72 test chỉ còn 8 lỗi trùng baseline HEAD. Ruff đạt cho các tệp đã sửa.
- Kiểm lưu thật trên `tp_tanphat_test` bằng dữ liệu giả `adm012.persist.*`, 17/17 đạt:
  - Admin ủy quyền duyệt `ĐC00062` qua wizard; dữ liệu còn sau khởi động lại registry và đăng nhập lại HTTP.
  - Excel nhập lại không ghi đè; đi muộn giữ `1 lần/7 phút`.
  - Admin ủy quyền trả lại `ĐC00063`. Sau khi thu hồi grant, người đó bị từ chối và Admin chính duyệt.
- Đăng nhập lại sau thu hồi (`ĐC00064`): đọc, mở, duyệt, trả lại và wizard đều báo `AccessError`.
- Playwright 2 lượt:
  - Admin ủy quyền thấy menu, duyệt `ĐC00065`/`ĐC00080` và trả lại `ĐC00066`/`ĐC00081` (bắt buộc lý do); DB đọc lại khớp.
  - Chủ phiếu không có menu hay nút xử lý. 0 lỗi console. [Nghiệm thu](demo/HR_ATTENDANCE_ADMIN_APPROVE_012_ACCEPTANCE.md).
- Commit này chưa giao PC server hay local `18069`.

## CHG-20261119-011 — Kiểm Odoo thứ tự và quyền xuất nhân viên

- 19/11/2026; kiểm bổ sung tự chọn trên DB test hiện có, không bắt cổng 18079 và không tạo DB mới. Backup dump/restore-list + filestore 2.200 tệp/6.328.315.069B + config + SHA256 tại `.local/hr-employee-xlsx001/test-backup-20261119T122312` trước upgrade/test HR; main/server không tạo fixture.
- `TestEmployeeExport` 4/4 PASS, 0 failed/error: reorder hai nhân viên, đổi thứ tự phòng, flush database/invalidate cache, xuất lại đúng thứ tự ở cả hai sheet và không đổi sequence/write_date nhân viên; domain/selected/ID/công ty/field quyền, chống formula, non-HR, hợp đồng nhiều dòng và ngày Excel. Ruff PASS; test user fixture không còn sau rollback. Log có INFO WinError5 khi GC không đổi tên được một số blob test; không có ERROR/CRITICAL, không xóa blob thủ công. Bổ sung assertion test, không thay application/runtime version.
- Kiểm lại sau deploy chấm công của phiên khác: 13 tệp addon Excel giữ checksum; ORM server22/22PASS; public health/login200, CSS73d8d48 và JS5c1f5ad khớp SHA256 server. App2c397ffb/HR20.0.1.14.0 giữ nguyên. [Acceptance](demo/HR_EMPLOYEE_XLSX_001_ACCEPTANCE.md). Chưa browser drag/persist qua commit hoặc authenticated public E2E/real-device; workflow snapshot sạch, giữ checkpoint và WIP khác.

## CHG-20261119-010 — Giao PC server: Admin chính duyệt điều chỉnh công

- Giao commit ứng dụng `44b0c9e2` (CHG-20261119-005) lên PC server: addon `tp_hr_attendance` `20.0.3.1.0 → 20.0.3.2.0` bằng `-u tp_hr_attendance` theo [runbook](../ops/runbooks/HR_ATTENDANCE_001_DEPLOY_AND_ROLLBACK.md). Script riêng `.local/admin-approve005/deploy005.py` + `deploy-server005.ps1`, 13 tệp (1 tệp mới là migration) giữ `mtime` theo commit.
- Kiểm trước (chỉ đọc): nguồn server khớp baseline `c9892225` 63/63 tệp, không tệp lạ; Admin chính duy nhất `admin` (uid 2, công ty 1, không gắn nhân viên); 5 admin ủy quyền đang hiệu lực; server có 0 phiếu điều chỉnh, 0 phân công, 0 kỳ chốt. Lần chạy đầu dừng ở bước kiểm trước vì phiên HR-EMPLOYEE-XLSX đang giao bản (tp-odoo bị dừng). Lần đó chưa thay đổi gì; chạy lại khi server đã yên ≥ 2 phút.
- Backup `C:\TANPHAT-backups\admin-approve005\admin-approve005-20261119T121945`: `tp_tanphat_dev.dump` `10.191.235`B (`restore-list` `15.789` mục), `filestore.tar.gz` `32.272.814`B, `source-config.tar.gz` `195.339`B, `SHA256SUMS.json`. Dừng `tp-odoo`, chạy `-u` trong container một lần, khởi động `tp-odoo` lúc 05:21:03Z; không restart tunnel.
- Kết quả: upgrade exit 0, log nâng cấp và log sau khởi động 0 ERROR, `/web/health` và `/web/login` 200. Module `20.0.3.2.0`; nguồn khớp commit 64/64. Nhân sự 39, tài khoản 32, digest nhóm, roster, phiên 384, ngày công 480, đi muộn 117, lô 5, grant ủy quyền và `web.base.url` không đổi.
- Probe ORM chỉ đọc: Admin chính của công ty 1 là `admin`; field `tp_can_review` đã có; không có phiếu chờ. Menu `Xử lý điều chỉnh` hiện với `admin`, và hiện chỉ đọc với 5 admin ủy quyền vì họ có nhóm HR manager như trước. Họ không phải Admin chính nên không có nút Duyệt/Trả lại và backend từ chối.
- Public `https://eight-championships-launches-plaintiff.trycloudflare.com`: `/web/health`, `/dang-nhap` 200; bundle mới `/web/assets/73d8d48/web.assets_web.min.css` (SHA256 `3dda3b6e…cff2`) và `/web/assets/5c1f5ad/web.assets_web.min.js` (SHA256 `c65e7521…4b7e`) có chuỗi giao diện mới.
- Local `18069` chưa áp: cổng này đang chạy candidate của phiên HR-EMPLOYEE-XLSX (`.local/hr-employee-xlsx001/candidate`, `tp_hr_attendance` `20.0.3.1.0`), nên không dừng hay sửa runtime của phiên khác. Áp sau bằng `-u tp_hr_attendance` có backup khi runtime đó rảnh.
- Không tạo, gửi hay duyệt phiếu nào trên server; không đổi tài khoản/quyền ngoài phạm vi. `docs/AI_WORKFLOW_STATE.json` sinh từ đúng cây commit trong thư mục tạm; checkpoint và tài liệu dở của phiên khác được giữ nguyên.
- Provenance CHG-20261119-010: mục changelog này đã lên `origin/main` qua commit `b4a8dae1` của phiên HR-LOGIN-RENAME. Phiên đó commit index chung đúng lúc mục này đang được stage (xem ghi chú ở CHG-20261119-009). Trạng thái dự án, biên bản nghiệm thu, runbook và workflow state của lần giao này ở commit tài liệu riêng ngay sau, dùng index riêng; không có application code.

## CHG-20261119-009 — Prompt đổi tên đăng nhập nhân viên (HR-LOGIN-RENAME-001)

- Ngày 19/11/2026 Asia/Saigon; theo yêu cầu trực tiếp. Phiên chính điều phối tạo [prompt triển khai](prompts/CLAUDE_HR_LOGIN_RENAME_001_EMPLOYEE_LOGIN.md), đăng ký roadmap/index và cập nhật status; chưa sửa application hoặc áp tính năng.
- Rà luồng account wizard/related/export, guard DEC-054, native UNIQUE(login)/so sánh đúng tên và session token chứa login. Tiếp nhận rõ WIP chưa commit trong hr_account_wizard.py/hr_history.py: không tự chốt chữ thường/case-insensitive từ WIP; yêu cầu bảo vệ mọi đường ghi, duplicate inactive/archive/race, audit atomic, UI inline/reload/Excel/phiên và giữ identity/password/quyền. Claude phải hoàn thiện/kiểm đúng scope rồi commit/push/deploy PCserver theo policy17/11; không thử tài khoản người thật, không bắt18079.
- Kiểm thực lượt điều phối: đọc source/diff/caller/test, scripts/dev.py status (18069/PG đang nghe), SSH chỉ đọc xác nhận PCserver /workspace/docs và prompt chưa có; kiểm nội dung/link tài liệu và git diff --check. Workflow check FAIL từ baseline do foreignWIP, start RESUME checkpoint18/11; không finish/seal thay batch khác. Không chạy test ORM/HTTP/browser/race/Excel đổi login vì chưa có implementation được bàn giao; không gọi prompt là technical/business acceptance. Chỉ đồng bộ tài liệu, không restart/upgrade runtime.
- Giao tài liệu: commit `02399eff4beb00b6045ef8d54ad313b4e2409f28` đã push `origin/main`, đồng bộ 5/5 tệp trên PCserver `/workspace` với kiểm SHA256; backup `/workspace/.local/hr-login-rename001/docs-before-20261119T052733Z`. Chỉ chèn mục CHG/task tương ứng và prompt, giữ tài liệu/server khác; không restart/upgrade Odoo, không ghi DB hoặc áp tính năng đổi login. Kiểm 4 link/14 điều kiện nội dung và diff --check PASS; 45 tệp code có sẵn và checkpoint giữ nguyên.
- Provenance giao bản tài liệu: commit biên bản `b4a8dae1` kèm mục CHG-20261119-010 do phiên giao chấm công stage chung index trong lúc commit. Mục đó thuộc phiên chấm công, giữ nguyên và không tính là thay đổi/kiểm chứng của HR-LOGIN-RENAME-001. Các bước còn lại dùng index riêng; không có application code trong hai commit tài liệu này.

## CHG-20261119-008 — Giao Xuất Excel nhân viên lên PC server

- 19/11/2026; app`2c397ffb` (HR20.0.1.14.0) đã push/deploy16/16tệpSHA256; backup `C:/TANPHAT-backups/hr-employee-xlsx001/hr-xlsx006-20261119T120938` gồm dump/restore-list15.787entry, filestore631entry, source/config vàSHA256; upgrade chỉHR exit0/0ERROR. Giữ39employee/32user, roster/employeeSequence/groups/implied/ledger/equipment/480ngày công/baseURL, chỉversionHR đổi.
- Server ORM READ ONLY22/22PASS; kiểm assets thực trênserver và `https://eight-championships-launches-plaintiff.trycloudflare.com` khớpSHA256: CSS73d8d48 (1.632.606B,3dda3b6e09d9…), JS e1de7bf (8.480.014B,bd588a0bbc30…); health/login200. Không ra lệnh thay cấu hình/restart tunnel; quan sát container tunnel restart trong lúc origin dừng, sau đó public hồi phục. Không authenticated browserE2Epublic vì không có phiên admin hợp lệ để dùng lại, không đăng nhập mới thay phiên người đang dùng.
- Tài liệu giao bản/cột/thứ tự/test tại [acceptance](demo/HR_EMPLOYEE_XLSX_001_ACCEPTANCE.md); ảnhExcel minh họa nằmignored `.local/hr-employee-xlsx001/workbook-preview-crop.png`. Local browser8/8, download6/6, workbook5/5, order12/12 vàORM22/22PASS. Chưa chạyfixtureOdoo/dragpersist ghi thật hoặc iOS/Safari. Workflowseal đúngsourceGit trongsnapshot sạch, giữ checkpoint vàforeignWIP; cập nhật tài liệu không restartOdoo.

## CHG-20261119-006 — Xuất Excel danh sách nhân viên (HR-EMPLOYEE-XLSX-001)

- 19/11/2026; người dùng giao phiên này trực tiếp triển khai, kiểm tra và deploy. Tái sử dụng `_build_xlsx`/xlsxwriter và `/tp_hr/export`; POST tải native có CSRF, giữ GET/filter cũ. Ba scope từ SearchModel domain/context đã áp, không lấy DOM/trang/nhóm mở; server đếm đúng nhân viên, giao cắt công ty/ACL/rule/field, không sudo vượt quyền; từ chối domain lỗi/toán tử bỏ quyền/credential, chống formula injection.
- `tp_hr_workspace` `20.0.1.14.0`: sheet trình bày10 cột, chi tiết phẳng57 cột thực theo quyền và sheet hợp đồng khi có dữ liệu/quyền; màu tài khoản tách lưu trữ, mã/điện thoại text, ngày Excel, AutoFilter/freeze/in ngang. Nguồn chưa có thứ tự phòng tùy chỉnh: thêm `hr.department.tp_sequence`/native handle; migration khởi tạo theo thứ tự tên cũ. Các sheet đọc DB và sắp phòng `tp_sequence,id`, nhân viên `sequence,id`; xuất không ghi thứ tự/hồ sơ.
- Kiểm: workbook5/5 + employee-order12/12; Ruff/AST/XML/Node PASS; read-only ORM22/22 trên18069; Playwright8/8 desktop/mobile không lỗi JS, 6XLSX thật khớp tổng/thứ tự (39đầy đủ/15tìm tên/31lọc nâng cao/1đã chọn); Excel thực mở/render workbook minh họa PASS. Odoo fixture tests bổ sung nhưng NOT_RUN (không tạo fixture/đổi thứ tự người thật trên main/server). Backup local và snapshot nghiệp vụ giữ nguyên. [Acceptance](demo/HR_EMPLOYEE_XLSX_001_ACCEPTANCE.md). Checkpoint và WIP ngoài phạm vi giữ nguyên; workflow seal trên snapshot sạch đúng source.

## CHG-20261119-005 — Admin chính duyệt điều chỉnh công (HR-ATTENDANCE-ADMIN-APPROVE-005)

- Ngày 19/11/2026 Asia/Saigon; yêu cầu trực tiếp “BỔ SUNG: ADMIN CHÍNH DUYỆT ĐIỀU CHỈNH CÔNG”, theo [DEC-060](DECISIONS.md). Addon `tp_hr_attendance` `20.0.3.1.0 → 20.0.3.2.0`: đổi view/menu/ACL và thêm migration `migrations/20.0.3.2.0/post-migrate.py`, nên **cần** `-u tp_hr_attendance`.
- Người nhận/duyệt: mọi phiếu `tp.hr.attendance.correction` của mọi phòng ban chỉ chuyển đến và chỉ được Duyệt/Trả lại bởi Admin chính (admin gốc) xác định bằng `res.users._tp_is_original_admin()` của `tp_admin_delegation` (nhóm `group_original_admin`, có quyền hệ thống, không có grant ủy quyền đang hiệu lực). Không hardcode login/UID. Module chấm công tra cứu mềm (`env.ref(..., raise_if_not_found=False)`); thiếu module ủy quyền thì không ai duyệt (fail closed).
- Admin được ủy quyền (Full Admin), HR manager, trưởng phòng và phân công `can_review` không còn quyền duyệt/trả. `can_review` đổi nghĩa thành “Xuất bảng công trong phạm vi” (nhãn form, bộ lọc, ghi chú phân công).
- Backend: `_tp_check_reviewer` gọi `require_original_admin` cho Duyệt, Trả lại, mở wizard và xác nhận wizard; `tp_can_review` và menu `Quản trị chấm công → Xử lý điều chỉnh` dùng cùng kiểm tra. Giữ chặn tự duyệt, khóa hàng `FOR UPDATE` + advisory lock theo công ty, một phiếu chờ/người/ngày. Không có người duyệt thay thế: công ty chưa có Admin chính đang hoạt động thì Gửi duyệt báo lỗi, phiếu giữ nháp.
- Màn admin: list `correction_review_list` toàn công ty (mã phiếu, mã/tên nhân viên, phòng ban, ngày, giờ hiện tại, giờ đề nghị, lý do, minh chứng, gửi lúc, trạng thái, người xử lý, xử lý lúc, đính chính) với nút dòng **Duyệt** / **Trả lại**; wizard hiện nhân viên, ngày, giờ hiện tại/đề nghị; trả lại bắt buộc lý do, nhân viên sửa và gửi lại. Giờ đề nghị hiển thị dạng đồng hồ (`float_time` + `numeric`, ví dụ `8:00`), không còn `8h`. ACL thêm quyền đọc phiếu đã gửi cho `base.group_system` để hàng đợi không phụ thuộc danh sách người duyệt đã lưu (quyền ghi vẫn chỉ qua nút).
- Nhân viên: trạng thái gửi đổi nhãn **Chờ admin duyệt**; **Yêu cầu của tôi** thêm người xử lý, thời điểm xử lý, nhận xét và màu cho phiếu bị trả. Lưu nháp không đổi bảng công; ghi trạng thái/người duyệt/phiên công qua RPC vẫn bị chặn.
- Lưu dữ liệu: tái sử dụng `action_approve` (tạo phiên `correction`, phiên cũ `superseded_by_id`, `day._tp_refresh`, log `correction_approve`). Wizard chỉ trả thông báo thành công sau khi ghi xong rồi đóng hộp thoại; lỗi giữa chừng rollback toàn bộ (test chèn lỗi sau refresh). Tệp Excel nhập sau không ghi đè ngày có phiên điều chỉnh; tổng đi muộn giữ theo tệp, không tính lại. Kỳ đã chốt: Admin chính cần thêm phân công chốt (`can_lock`) và lý do đính chính.
- Migration `20.0.3.2.0` làm mới `reviewer_user_ids` (danh sách được đọc) của mọi phiếu không ở nháp sang Admin chính; không đổi trạng thái, người đã xử lý, giờ hay phiên công.
- Kiểm thử trên snapshot cách ly (`.local/admin-approve005/snapshot`) với `tp_tanphat_test`: `/tp_hr_attendance` 71 test, `TestAttendanceCorrection` 10/10 đạt (mới `admin005_*` ×4; viết lại `at02c`, `at03c`, `at06a`–`at06d`). 8 lỗi còn lại trùng baseline HEAD: `test_access` (guard nhóm của `tp_admin_delegation`), `test_directory_privacy`, `test_matrix_compare` ×4, `test_upload` ×2. Baseline HEAD 67 test có 9 lỗi, gồm `at02c` cũ dùng `datas` không còn trong Odoo 20. Ruff các tệp Python đã đổi và `git diff --check` đạt.
- Kiểm lưu thật có commit trên `tp_tanphat_test`, chỉ dữ liệu giả `Synthetic ADM005 Persist Co` (`.local/admin-approve005/persist_check.py`): phiếu `ĐC00037` 07:37–17:05 → 08:00–17:00. Chủ phiếu, HR manager và trưởng phòng bị từ chối; Admin chính giả duyệt qua wizard. Tiến trình mới (khởi động lại registry): Đã duyệt, người duyệt, thời điểm gửi/xử lý, giờ gốc; Công của tôi, Bảng công và Tổng quan đọc 08:00–17:00; đi muộn giữ `1/7`; tệp sau 07:50–17:20 không ghi đè. HTTP server mới + đăng nhập lại JSON-RPC: chủ phiếu đọc lại Đã duyệt; ghi `state` và tạo phiên bị từ chối; duyệt lần hai báo “Phiếu không còn chờ duyệt”. Không duyệt phiếu thật của nhân viên.
- Kiểm trình duyệt thật (Playwright, HTTP server mới trên `tp_tanphat_test`, `.local/admin-approve005/ui_check.py`): Admin chính giả mở `Quản trị chấm công → Xử lý điều chỉnh`, thấy dòng `ĐC00038` đủ nhân viên/phòng/ngày/giờ hiện tại `07:45–17:10`/giờ đề nghị `8:00–17:00`/lý do và nút Duyệt/Trả lại; duyệt qua wizard → “Đã duyệt ĐC00038 và lưu giờ vào/ra vào bảng công.”; Trả lại `ĐC00039` không lý do bị chặn, có lý do → “Đã trả lại”; hàng đợi về 0. Chủ phiếu đăng nhập lại thấy Đã duyệt/Trả lại, người xử lý, thời điểm và nhận xét; không thấy nút xử lý. Tiến trình shell mới đọc DB: `approved` + ngày `08:00–17:00` nguồn `correction`; `returned` giữ nguyên giờ. 0 lỗi console/5xx.
- `docs/AI_WORKFLOW_STATE.json` sinh từ đúng cây commit trong thư mục tạm; checkpoint `.local/ai-workflow/active.json` và tài liệu dở của phiên khác trong checkout được giữ nguyên, không stage.

## CHG-20261119-004 — Bàn giao PC server giao diện “Công của tôi” (HR-ATTENDANCE-MINE-UI-001)

- Ngày 19/11/2026 Asia/Saigon; triển khai app `5859a83e` (`8/8` tệp trong `custom_addons/tp_hr_attendance/`, không đổi version `20.0.3.1.0`, không cần `-u`) lên PC server sau preflight SHA256 `8/8` và backup nguồn `/workspace/.local/mine-ui001/source-before-20261119T035343Z`.
- Chỉ restart `tp-odoo` (không động `tp-tunnel`/`tp-postgres`); snapshot DB trước/sau giữ nguyên (`39` nhân sự, `32` tài khoản, `5` lô, `384` phiên, `480` ngày, digest nhóm `cd4581c4f4c47e2cfab004b6eefb3cdc`).
- Kiểm thực URL public hiện hành `https://eight-championships-launches-plaintiff.trycloudflare.com` (`/web/health` và `/dang-nhap` `200`) và tải trực tiếp bundle thực: CSS `/web/assets/9b3c839/web.assets_web.min.css` (SHA256 `de9f259b9921…`) và JS `/web/assets/e42c27e/web.assets_web.min.js` (SHA256 `df6d2838e447…`) khớp 100% server, xác nhận có `.o_tp_mine_table`, `.o_tp_mine_summary`, `overscroll-behavior-y: contain`, sticky `-20px`, `mineStatusInfo`, `applyFilters`, nhãn lọc và ghi chú không quy đổi `0`.
- Probe ORM chỉ đọc trên PC server (`uid=51`) PASS; giữ nguyên ghi nhận chưa chạy authenticated browser E2E trên URL public và chưa kiểm thiết bị iOS/Safari thật. Đồng bộ tài liệu lên PC server không restart Odoo.

## CHG-20261119-003 — Thiết kế lại giao diện “Công của tôi” (HR-ATTENDANCE-MINE-UI-001)

- Ngày 19/11/2026 Asia/Saigon; triển khai theo yêu cầu trực tiếp `HR-ATTENDANCE-MINE-UI-001`, giữ nguyên addon version `20.0.3.1.0` (không đổi schema/menu/ACL).
- Backend (`attendance_logic.py`, `attendance_overview.py`): thêm helper thuần `mine_row_status`, `filter_mine_rows`, `summarize_mine_rows`; nâng cấp `tp_mine` với lọc server theo tình trạng dữ liệu (`out_recorded`, `working`, `attention`, `missing_in`, `missing_out`, `review`, `no_punch`, `no_source`, `leave`, `future`) và ngày trong tuần (`workdays`, `weekend`, `0..6`), phân trang mặc định 50 dòng (`10/20/50/100`), trả kèm `summary` toàn kỳ, `range_display`, `sessions`/`requests`/`lock_state`/`has_detail` theo đúng ACL người đăng nhập; `tp_export_mine` xuất toàn bộ dòng khớp bộ lọc đang áp (không chỉ trang hiện tại) và giữ sheet `Tổng đi muộn` đúng kỳ Excel; luôn xác định nhân viên từ session và từ chối bộ lọc không hợp lệ bằng `UserError`.
- Giao diện (`common.js`, `mine.js`, `mine.xml`, `attendance.scss`): thiết kế lại hoàn toàn màn hình “Công của tôi” trong scope `.o_tp_att_mine` (không ảnh hưởng `PersonDetail`, Tổng quan, Bảng công Vào/Ra, hộp thoại nhân viên); bản nhúng Hồ sơ cá nhân bỏ lặp tiêu đề và thông tin nhân viên; phân cấp 3 bậc nút; thanh chọn kỳ Tuần/Tháng + popover phụ Kỳ theo file + khoảng xem rõ; 4 thẻ tóm tắt tách biệt chỉ số kỳ và nguồn Excel (giữ `—` khi không khớp kỳ nguồn); bộ lọc pending→Áp dụng + chip + Xóa bộ lọc + phân trang + bảng có đường kẻ hàng/cột, giờ vào/ra màu xanh tabular-nums, ô thiếu giờ có `—` kèm nhãn, badge tình trạng, mở rộng chi tiết theo dữ liệu thực, header sticky không tạo vùng cuộn dọc lồng nhau, mobile card gọn + panel lọc thu gọn, skeleton tĩnh không chạy animation liên tục và tôn trọng `prefers-reduced-motion`.
- Kiểm thử: Ruff/AST/XML/SCSS/Node/pure-logic PASS; read-only ORM trên `tp_tanphat_dev` (`uid=41/34/2`: lọc, phân trang, chống giả mạo `employee_id`, bộ lọc lỗi, xuất Excel toàn bộ kết quả lọc) PASS; Playwright `scripts/tests/test_hr_attendance_mine_ui.cjs` 10/10 + `test_hr_attendance_scroll.cjs` 12/12 + `test_hr_attendance_latest_ui.cjs` 2/2 PASS, 0 lỗi JS/console; ảnh trước/sau tại `.local/mine-ui001/{before,after}`. Foreign checkpoint và WIP ngoài phạm vi được giữ nguyên.

## CHG-20261119-002 — Giao chấm công Vào/Ra và ưu tiên file mới lên PCserver

- Source app`caf24a1c`20.0.3.1.0 đãpush; giao đúng18addonfiles, so sánhbaseline đãbiết/hashes, backupDB+restore-list+filestore+source/config trước-u. Không hạaddon hoặc ghi dữliệu/người giả trênmain/server, không restarttunnel. Serverbackup`/workspace/.local/attendance-ui001/backup-20261119T020340Z`.
- Cố gắngbackupđầu tiên bị chặn pg_dump15/serverPG16 trước khi thayfile; serviceđượcbậtlại. Sauđó dump/restore-list dùngchínhcontainerPG16, counts readonly giữ39employee/32user/4batch/355session/456day vàgroupdigest; version20.0.3.1.0,menuoldinactive.
- Serverinternalhealth200; publicURLtrycloudflarecũNXDOMAIN. Tunnelhiệncó node/localtunnel ởngoàiscope,cólink`https://tiny-wasp-93.loca.lt`,health200. Không tự đổi tunnel hoặc dùngcredentialadmin trênpublic.
- Kiểm actualpublicbundle: CSS`/web/assets/76ac1e0/web.assets_web.min.css`1.595.983B,SHA256`5d1d63376c4da8ab1c459c1979f0eab2b91a4b592bfc299024e06f2a97849d1e`; JS`/web/assets/a4da174/web.assets_web.min.js`8.441.668B,SHA256`5776a8632c7de2122bc3f7a0bed6d3401e11169581c771609002233d72cf4f73`; cóattentionintro/clock/matrixsubtitle/back/detail/containedscroll, hasheskhớpserver. Coldassets tốn35–56s; lượtđầutimeoutkhôngcoiPASS, warmedretryđạt.
- Browserlocal saucuốicùng2/2PASS,0JSerror; scroll12/12PASS từ001,ORM6/6PASS. No businessreplayfilethậtcũ. PublicauthenticatedE2E/thiếtbịthật/UAT cònNOT_RUN. Foreigncheckpoint/WIP giữ,workflow committedsnapshotđúngscope; giao docs khôngrestart/upgrade thêm.


## CHG-20261119-001 — Chấm công: Vào/Ra mặc định, giờ thiếu trực quan, nguồn mới nhất

- Ngày19/11/2026 Asia/Saigon; thực thi theo yêu cầu trực tiếp và steering bỏ Trùng/Khác giờ, cập nhật theo file mới nhất (DEC-059 thay phần xung đột DEC-058).
- Ẩn menu/nút Bảng chấm công, giữ XMLID/path và shared-reader fallback; importer mở matrix ở link cũ. Back về Tổng quan. Bỏ button đối chiếu ở lối chính, nhãn/màu/option Trùng/Khác giờ; snapshot/công cụ lịch sử vẫn giữ.
- Danh sách kiểm tra: giờ ghi nhận xanh, nhãn Thiếu giờ vào/ra cam, cần đối chiếu đỏ, hướng dẫn và số dòng theo bộ lọc server; Chi tiết có keyboard và mobilecards, giữ scope/pager/search/phòng/ngày.
- Upload tự áp nguồn mới trong transaction/savepoint từng tệp, company advisory lock bảo đảm thứ tự. Dùng writer hiện có giữ session cũ inactive, không nhân đôi. Cùng employee/day theo file mới, blank gỡ giờ import cũ, absentemployee/date giữ; old-source replay không thắng newer. Bảo vệ kỳ chốt/approved correction/API; mapping/giờ/duplicate rows trong file không chắc chắn không ghi. Tổng muộn giữ nguyên số kỳ từ Excel, không phân rã theo ngày. Sửa flush state tổng muộn cũ trước activate tổng mới để unique index không lỗi.
- Addon20.0.3.1.0, không thêm schema/ACL/field. Không tự reapply các file thật sẵn có. Tests tổng hợp transaction trên tp_tanphat_test, không fixturemain/server:6/6PASS (latest5+menu1), label5/5, ruff/XML/PythonPASS. Browser authenticated18069 desktop1440/mobile3902/2, detail/back/matrix/linkcũ/nhãn/overflow và0JSerrors; scroll12/12PASS. TestGC có warning Windows permission trên filestoretest, assertions0failed/0error; không dọn filestore.
- Main backup dump10MB+restore-list+filestore~1.6GB before compression; upgrade giữ counts/group digest. Private evidence `.local/attendance-ui001`. Foreign checkpoint và dirtycode/docs được giữ; workflow chạy committedsnapshot đúngscope. Pending PCserver deploy/public assetverification; không iOS/Safari thật, không độc lậpaudit hoặc UAT.


## CHG-20261118-039 — HR-ATTENDANCE-SCROLL: giao18069/PCserver và kiểm CSS thực public

- Ngày18/11/2026 Asia/Saigon. App `2b287001` đã push; PC chỉ thay `attendance.scss` cóSHA256 `027e32977c5389d648974b3d2f2fbb8bf5bff9760b374d2aba2c4d231f11dde2`, giữmtimeGit khác0, so khớp sourcecũ trước ghi và backupCSS/config/metadata tại `/workspace/.local/attendance-scroll038/source-before-20261118T131024Z`. Restarttp-odoo, khôngupgrade module/DB hoặc restarttunnel. Rollback: khôi phụcCSS+mtime từbackup vàrestartservice.
- Local12/12authenticatedviewport-modecasesPASS,0JSerror; đọc thêm3mànBảng/Công của tôi/Nguồnkhông tràn. Publichealth200,login1440/390PASS,0JSerror. CSSpublic thực `/web/assets/912111f/web.assets_web.min.css`,1.593.357B,SHA256 `a600d87da00867db5ec2ab1ab7d8c885e09b719933876d60394f50b886cf0703` chứa cả2rule; CSSlocal `b6dc736` cùng2rule. Public lần đầu compilecold bịtimeout1lần, lần sau tải200đạt, không báo lần timeout làPASS.
- ProbeSQLreadonlyserver: chấm công20.0.3.0.0,39nhân viên/32users/4lô/355phiên/456ngày; taskkhônggửiactionghinghiệpvụ. PublicauthenticatedscrollNOT_RUN: credentialkiểmcósẵnkhôngthiếtlậpsession,khôngloginadminhoặcđổipassword/quyềnđểtest;mobilelàChromiumemulation,chưaiOS/Safarithật. Không nâng kết luận asset/login thành authenticatedE2E.
- Checkpoint/WIP khác giữ; workflow snapshotcommitđúngscope. Bàn giao tài liệu/testnguồnvàpushđúngscope; đồng bộsource/docs đãcommit khôngrestartthêm. Next: người dùngCtrl+F5trangTổngquanchấmcông đểnhậnCSSmới.


## CHG-20261118-038 — HR-ATTENDANCE-SCROLL: sửa cuộn lộ trắng ở Tổng quan chấm công

- Ngày18/11/2026 Asia/Saigon; người dùng yêu cầu trực tiếp kiểm tra và fix, thực thi giới hạn lỗi này thay vai trò chỉ viết prompt.
- Tái hiện authenticated18069: kéo hết nội dung rồi cuộn tiếp làm documentY603 desktop và4400 mobile; document cao1503/5536 vượt viewport900/844. Nhãn `.visually-hidden` absolute trỏ offsetParent vềbody vì scrollport không positioned; mobilethead absolute cùng lỗi. Không do thiếu dữ liệu hoặc server lỗi.
- Sửa stylesheet chung chấm công: positionrelative giữ nhãn trong scrollport và overscroll-behavior-y:contain cho màn độc lập; giữ Công của tôi nhúng theo parent, không bodyoverflowhidden/globalCSS/core/layoutsidebar. Không đổi model/ACL/session/moduleversion/schema, không cần-u.
- Thêm regression browser dùng state riêng qua biến môi trường, không chứa cookie/password trongGit và không tự login/ghi công; kiểm 4viewport(1440/1366/390/375) × Ngày/Tuần/Tháng, rootheight/width, hiddenlabelcontainingblock, wheelđếnđáy/lênđầu và navbar/sidebar cố định. 1806912/12PASS,0JSerror. Bằng chứng private `.local/attendance-scroll037` gồm trước/sau và số đo; không đưa nhân viên/screenshot vàoGit.
- Local runtime dùng candidate của batchMATRIX003: chỉ thay đúng CSS sau đối chiếuSHA256 và backup, restart cùng config18069 để sinhasset; không đổi candidatekhác hoặc hạ addon. Giữ checkpoint/code/docs WIP khác; workflow được ghi trên committedsnapshot đúngscope. Next: push và deploy CSS lênPCserver, backup tệp/metadata, giữmtime mới và kiểmCSS thựcpublic; không upgradeDB hoặc restarttunnel.


## CHG-20261118-037 — Giao PC server bản sửa cờ snapshot chấm công (CHG-20261118-036)

- Ngày 18/11/2026 Asia/Saigon. Giao code commit `74047fbc` lên PC server, chỉ 2 tệp `custom_addons/tp_hr_attendance/models/attendance_matrix.py` và `tests/test_matrix_compare.py`, label `snapshot-ready036`. Script và bằng chứng: `.local/snapshot-ready036/` (`deploy036.py`, `deploy-server036.ps1`, `drift036.py`, `deploy-output.txt`).
- Trước khi giao, kiểm chỉ đọc: 2 tệp code trên PC khớp bản gốc `55e01926`. Chấm công `20.0.3.0.0`, 4 lô đều `ready/2`, 0 lô có snapshot mà chưa `ready`, nên bản sửa chỉ mang tính phòng ngừa trên server. Không có container bảo trì nào khác đang chạy.
- Backup `C:\TANPHAT-backups\snapshot-ready036\snapshot-ready036-20261118T200015`: `pg_dump` trực tuyến `tp_tanphat_dev.dump` `10.091.620`B, `restore-list.txt` `15.787` mục, `source-config.tar.gz` chứa 2 tệp bị thay, `before.json`, manifest, `SHA256SUMS.json`. Filestore không bị chạm nên không sao lưu.
- Giao: giải nén tar giữ `mtime` theo commit, kiểm checksum, rồi `docker restart tp-odoo` lúc 13:00:20 UTC. Không `-u`, vì không đổi schema hay version.
- Kiểm sau khi giao:
  - Health `200`; `/web/login` trong máy `200`.
  - Public `https://hybrid-send-ready-ballot.trycloudflare.com/web/health` `200`; `/web/login` chuyển `/dang-nhap` rồi `200`.
  - Token `SNAPSHOT_FIRST_PARSER_VERSION` có trong container.
  - Log sau khi khởi động 0 ERROR. Một dòng `bus.websocket: connection already closed` đúng lúc tắt tiến trình cũ.
  - Version mọi module `tp_*` và các số đếm (lô 4, dòng 945, snapshot 195/1.365, phiên 355, ngày công 456, nhân viên 39, user 32, base URL) trước và sau khớp nhau. Cờ lô `ready/2` ×4.
- Docs trong checkout PC (`CHANGELOG`, `PROJECT_STATUS`, `AI_WORKFLOW_STATE.json`, runbook) vốn đã lệch Git trước lần giao này. Không ghi đè docs; bản chuẩn nằm trong Git.
- `NOT_RUN`: thao tác UI đăng nhập thật, probe ORM trên DB server (đã probe có rollback ở local ở CHG-20261118-036), test ORM `18079`.
- Hoàn nguyên: khôi phục `source-config.tar.gz` của backup trên rồi `docker restart tp-odoo`.

## CHG-20261118-036 — HR-ATTENDANCE: snapshot đã có thì đánh dấu lô `ready`

- Ngày 18/11/2026 Asia/Saigon. Đóng mục còn mở của CHG-20261118-035. Chỉ sửa `custom_addons/tp_hr_attendance/models/attendance_matrix.py` và thêm test; không đổi schema, quyền, giao diện hay version module (`20.0.3.0.0`).
- Lỗi: `_tp_build_snapshot` thấy lô đã có `tp.hr.attendance.snapshot.person` thì `return True` ngay, không cập nhật `snapshot_state/snapshot_version`. Sau sự cố 17:14, cột cờ bị tạo lại với mặc định `pending/0`; backfill `_tp_migrate_matrix_003` gặp snapshot cũ nên thoát sớm, lô kẹt `pending`. `tp_matrix_data`, `tp_export_matrix` và `_tp_build_compare_context` thấy `pending` lại gọi dựng snapshot, mỗi lần đều lấy `pg_advisory_xact_lock` theo công ty và `FOR UPDATE` lô, nên các thao tác chỉ đọc bị tuần tự hóa mãi.
- Sửa: dòng snapshot là bất biến và đầy đủ, nên khi đã có mà cờ chưa `ready` hoặc version `0` thì ghi `snapshot_state=ready`, `snapshot_version` giữ giá trị cũ hoặc `SNAPSHOT_FIRST_PARSER_VERSION = 2` (parser MATRIX-003 đầu tiên lưu snapshot), `snapshot_note=False`. Không đọc lại tệp Excel, không dựng lại, không nhân đôi dòng. Lô đã `ready` không bị ghi.
- Test ORM mới `test_existing_snapshot_with_lost_flags_is_marked_ready_without_rebuild` (`test_matrix_compare.py`): tải tệp tổng hợp, đặt lại cờ `pending/0`, gọi dựng snapshot và `tp_matrix_data`, kiểm `ready/2`, số dòng người/ô giữ nguyên, lô `ready` không còn bị `write` (mock).
- Kiểm:
  - Test thuần không DB `test_logic`/`test_parser`/`test_parser_late`/`test_matrix_pure` `26/26` PASS. Module test ORM import được và phát hiện 4 test.
  - `ruff check custom_addons/tp_hr_attendance` sạch; `git diff --check` sạch.
  - Probe `odoo-bin shell` có rollback trên `tp_tanphat_dev`, chạy candidate `HEAD 55e01926` + bản sửa (`.local/snapshot-ready036/`). Đặt lô 1 và 2 về `pending/0` trong transaction. `tp_matrix_data` lô 1 (39 người) và `tp_compare_batches` 2↔1 (20 dòng) đưa cả hai về `ready/2`, ghi chú rỗng, số dòng snapshot không đổi. Đọc lần hai không ghi lô (`ctid` không đổi). Sau rollback cờ 7 lô như trước.
- `NOT_RUN`: test ORM trên `tp_tanphat_test`/`18079`, UI đăng nhập thật, HOOT. Local 18069 vẫn chạy tiến trình của phiên khác, chưa nạp bản này; các lô local đều đã `ready` từ CHG-20261118-035.
- Next: push, giao PC server: backup, chép tệp, khởi động lại `tp-odoo`, không `-u`. Sau đó kiểm cờ lô, health, URL public.

## CHG-20261118-035 — Phục hồi DB local 18069 sau sự cố hạ `tp_hr_attendance` lúc 17:14

- Ngày 18/11/2026 Asia/Saigon; chỉ sửa dữ liệu DB local `tp_tanphat_dev`, không sửa code ứng dụng, không đụng PC server (vẫn `20.0.3.0.0`).
- Bối cảnh: lúc 17:14, candidate cũ của phiên HR-EMPLOYEE-ORDER (CHG-20261118-031) chạy `-u tp_hr_workspace`, kéo module phụ thuộc `tp_hr_attendance` xuống `20.0.2.0.0`. Odoo xóa 106 field, 3 model metadata, 9 quyền, menu/action ma trận và các cột lô/dòng/đi muộn/phiên; bảng snapshot vẫn còn. Lúc 19:18, phiên CHG-20261118-033 chạy `-u tp_hr_attendance` lên `20.0.3.0.0` (có post-migrate), tạo lại cột và metadata.
- Đối chiếu chỉ đọc với dump `.local/hr-order-smooth/backup-20261118T171409` (`pg_restore --data-only`, so từng id/cột theo định dạng COPY): 24 bảng chấm công/quan hệ khớp (lô 7, dòng 1.206, phiên 299, đi muộn 195, snapshot người 312/ô 1.755, ngày công 365, quan hệ 268/38/330/363). Metadata cũng khớp: xmlid 739, field 456, selection 104, model 19, `ir.access` 54 (so theo nội dung), menu 434. Không có ghi nghiệp vụ nào sau sự cố cần gộp.
- Phần còn mất, đã khôi phục trong một transaction khi 18069 dừng:
  - 7 lô `snapshot_version/snapshot_state` `0/pending → 2/ready`, đúng giá trị trong dump. Backfill gặp snapshot đã có nên thoát sớm, không đặt `ready`; khi còn `pending`, mỗi lần mở ma trận/đối chiếu đều khóa lô.
  - Chèn lại 16 `ir.model.constraint` FK của resolution/snapshot, giống `_reflect_constraint`. FK thật vẫn còn trong PostgreSQL; Odoo không phản chiếu lại FK đã tồn tại.
  - Không chạy upgrade module.
- Backup `.local/attendance-repair033/backup-20261118T193700`: `tp_tanphat_dev.dump` `10.455.355`B / `15.787` mục restore, cấu hình runtime cũ, `SHA256SUMS.json`. Filestore không bị sửa nên không sao lưu.
- Cố ý không khôi phục:
  - 9 `mail.message` "Access created" (id 2018–2026), gắn với `ir.access` cũ đã bị xóa; các bản ghi quyền tạo lại đã có 9 thông báo tương đương.
  - `write_date` của 7 lô giữ mốc backfill 12:18 UTC.
- Runtime: trong lúc sửa, một agent khác đồng bộ `.local/hr-attendance-matrix003/candidate` lên `c48ac9a9` và khởi động lại 18069 (PID 20704) trước tiến trình của phiên này. Nội dung trùng với `.local/attendance-repair033/candidate-20261118T193700` (diff rỗng), nên giữ nguyên tiến trình đó, không tranh cổng.
- Kiểm sau khi sửa:
  - So sánh lại chỉ còn khác `write_date` của lô và 9 thông báo nêu trên; `ir.model.constraint` 134/134.
  - Health `200`; log 18069 `0` ERROR.
  - `test_hr_employee_order_served_assets.py` trên 18069: 12/12 (JS `eea54cd`, CSS `de3e8d2`).
  - Probe ORM uid 2, rollback: `tp_matrix_data` lô 1 `ready`, 39 người; `tp_compare_batches` 2↔1 trả payload; thao tác đọc không ghi lô.
  - Snapshot nhân sự, sequence, user, nhóm, implied, thiết bị, ngày công, base URL không đổi.
- `NOT_RUN`: thao tác UI với đăng nhập thật, HOOT, `18079`. Còn mở: sửa `_tp_build_snapshot` để đặt `ready` khi snapshot đã có.

## CHG-20261118-034 — Đồng bộ giao bản PC server & kiểm asset public CHG-20261118-033

- Deploy `c48ac9a9` (`62/62` checksum, `0` `mtime=0`) lên `PC server` sau backup `C:\TANPHAT-backups\hr-attendance-matrix003\ham003-20261118T193137` (`dump` `10.091.595`B/`15.787` restore); `-u tp_hr_attendance` `exit 0/0 ERROR`.
- Kiểm `SERVER_MENU_OK` (`id=437` dưới Chấm công, `admin=True`, `uid=34=False`); thực tải public CSS `988ded0` (`1.593.271`B) & JS `2d59368` (`8.438.086`B) `200 OK` (có `#ccf7f7`, `#e4e7ff`, `openFileMatrix`, `matrix.v2`, `onPatched`); Playwright ẩn danh public `0` lỗi console/5xx. Tài liệu đồng bộ sau giao bản.

## CHG-20261118-033 — Đưa Bảng công theo file ra menu Chấm công/nút thao tác và khớp bố cục mẫu Excel

- Di chuyển `menu_file_matrix` (*Bảng công theo file (Vào/Ra)*) ra trực tiếp dưới menu **Chấm công** (`sequence=25`, giữ nguyên gating `can('import')`), thêm nút mở nhanh **Bảng công theo file (Vào/Ra)** / **Đối chiếu A/B** trên `board.xml/js` và `dashboard.xml/js`.
- Cập nhật `matrix.js/xml/scss` (`STORE_KEY` `matrix.v2`): mặc định bật `ID`, `Chức vụ`, `Vắng mặt (Vắng)`, sắp đúng thứ tự cột và màu header/nhóm cyan `#ccf7f7`/cuối tuần `#e4e7ff` theo mẫu bảng Excel; ghim sticky `STT | Mã nhân viên | Tên nhân viên` không đè `ID`/`Chức vụ`/`Vào/Ra`.
- Kiểm thực: `ruff 0`, XML/JS OK, pure `26/26 PASS`, `18069` upgrade `exit 0/0 ERROR`, menu ACL (`uid=2=True`/`uid=34=False`), HTTP CSS `35a7749`/JS `69b87c9` `200 OK`.

## CHG-20261118-032 — Giao PC server & xác minh asset public bản thả mượt HR-EMPLOYEE-ORDER

- Ngày 18/11/2026 Asia/Saigon; biên bản giao commit `006ff458` (TP HR `20.0.1.13.2`, CHG-20261118-031), không sửa code ứng dụng.
- Gói `hr-smooth031`: 11 tệp từ `git diff f42d9e03 006ff458`, mtime theo thời gian commit (cổng 028). Kiểm drift trước khi dừng dịch vụ: 8/8 tệp code/test/hướng dẫn trên PC khớp `f42d9e03`; `CHANGELOG`, `PROJECT_STATUS`, `AI_WORKFLOW_STATE` trên PC còn bản `f27f1044` vì docs CHG-029/030 chưa đồng bộ. Lần chạy đầu dừng ở bước kiểm drift, chưa thay đổi gì; đặt baseline đúng `f27f1044` cho 3 tệp đó, gói đưa docs PC lên HEAD.
- Backup `PC server`: `C:\TANPHAT-backups\hr-smooth031\hr-smooth031-20261118T190928` (`tp_tanphat_dev.dump` `10.083.496`B / `15.787` mục restore, `filestore.tar.gz` `36.208.699`B / `623` mục, `source-config.tar.gz` `2.165.505`B, `SHA256SUMS.json`). Giải nén 11/11 khớp SHA-256.
- Upgrade `-u tp_hr_workspace` (`exit 0`, `0` ERROR): chỉ `tp_hr_workspace` `20.0.1.13.1 → 20.0.1.13.2`; `tp_hr_attendance` giữ `20.0.3.0.0` (cột `batch_code`/`snapshot_state`/`snapshot_version` đủ 3/3, log không xóa field chấm công). Snapshot trước/sau trùng: 39 nhân viên, hash `sequence`, roster, 32 user, 108 liên kết nhóm, implied, 55 thiết bị, 1 đề xuất, ledger 5, 456 ngày công, `web.base.url`; health `200`.
- Public `https://hybrid-send-ready-ballot.trycloudflare.com`: `test_hr_employee_order_served_assets.py` 12/12 PASS trên bundle mới JS `/web/assets/d89896c/web.assets_web.min.js` (`8.439.029`B, SHA-256 `2bf670d2…`) và CSS `/web/assets/b3fca4b/web.assets_web.min.css` (`1.593.002`B, SHA-256 `82dee0c8…`); `node --check` JS phục vụ đạt, không có stub lỗi transpile. Không restart tunnel.
- `NOT_RUN`: đăng nhập thật, kéo và lưu thứ tự trên DB đang dùng (người dùng tải lại trang và thử trực tiếp), HOOT, `18079`. Local `18069` chưa áp vì DB local đang lệch schema chấm công từ phiên trước (CHG-20261118-031); cần phục hồi riêng trước khi áp.

## CHG-20261118-031 — HR-EMPLOYEE-ORDER: thả là sắp xếp ngay, hàng trượt mượt vào chỗ

- Ngày 18/11/2026 Asia/Saigon. Phản hồi người dùng: kéo thả chưa mượt, thả ra bị khựng một lúc rồi mới sắp xếp. TP HR `20.0.1.13.1 → 20.0.1.13.2`, chỉ frontend `static/src/table/table.js` và `table.scss`; backend, quyền, phòng ban, bộ lọc, sắp xếp cột, phân trang giữ nguyên.
- Nguyên nhân khựng: bản đang chạy chờ RPC `tp_reorder_in_department` và tải lại danh sách rồi mới vẽ thứ tự mới. Kế thừa WIP lạc quan chưa commit (đổi `Group.list.records` native ngay, lưu nền, đồng bộ `ordered_ids`/`sequence` bằng `_applyValues`, chỉ tải lại nhóm khi trang đổi thành viên, lỗi thì khôi phục và báo lỗi, chặn kéo khi đang lưu).
- Sửa lỗi còn lại của WIP: FLIP chạy trong `requestAnimationFrame` trước lần patch của Owl nên đo vị trí cũ, làm hàng bên nhảy một hàng rồi trượt về và hàng thả bị giật. Nay đo và chạy hiệu ứng trong `onPatched` sau khi DOM đã mang thứ tự mới (khớp ô thả theo anchor trước/sau, bỏ sau 1s). Hàng thả trượt từ vị trí nhả chuột vào chỗ 220ms (`.o_tp_hr_row_settling`), hàng bên nhường chỗ 180ms cùng easing. Animation trên ô để giữ hitbox hàng, hủy khi unmount, tắt khi `prefers-reduced-motion`.
- Kiểm: `node scripts/tests/test_hr_employee_order.cjs` PASS; `node scripts/tests/test_hr_employee_order_browser.cjs` (Owl, sortable và template thật, RPC giả) PASS kèm hồi quy mới đo từng frame vẽ sau khi nhả: hàng bên lệch không quá 1.5px, hàng thả bắt đầu tại vị trí nhả (±2px), trượt đơn điệu 86→70.5px qua 36 frame, không còn lớp settling, 0 lỗi trang. Checker asset phục vụ thêm token `settleDroppedRow`/`onPatched`/`releaseRect` và CSS `.o_tp_hr_row_settling`, đồng thời cấm `_tpAnimationFrame` cũ. `git diff --check` sạch.
- `NOT_RUN`: đăng nhập thật và ghi thứ tự trên DB đang dùng, HOOT, suite DB `18079`. Checker asset trên `127.0.0.1:18069` FAIL đúng dự kiến vì 18069 đang phục vụ candidate `.local/hr-attendance-matrix003/candidate`, không phải bản này.
- Cảnh báo môi trường local 18069 (không do commit này): lần áp HR `20.0.1.13.2` lúc 17:14 của phiên `hr-order-smooth` dựng candidate từ `f27f1044` nên `-u tp_hr_workspace` kéo theo `tp_hr_attendance` (phụ thuộc HR) xuống `20.0.2.0.0` trên `tp_tanphat_dev` local: xóa 106 field metadata, mất các cột như `batch_code`, `snapshot_state`, `raw_source_code`, `source_choice`; số dòng lô/dòng/snapshot giữ. Runtime 18069 hiện chạy code `20.0.3.0.0` trên schema `20.0.2.0.0`. Backup ngay trước: `.local/hr-order-smooth/backup-20261118T171409`. Phiên này không sửa DB local; cần phục hồi riêng. PC server đã ở `20.0.3.0.0` (CHG-030), không bị ảnh hưởng.
- Next: push, deploy PC server chỉ `-u tp_hr_workspace` với backup riêng, kiểm JS/CSS phục vụ thực trên URL public.

## CHG-20261118-030 — Giao PC server & xác minh asset public HR-ATTENDANCE-MATRIX-003

- Ngày 18/11/2026 Asia/Saigon; đồng bộ tài liệu sau giao bản commit code `b7765bd1` (`tp_hr_attendance` `20.0.3.0.0`), không sửa code ứng dụng và không restart/upgrade thêm.
- Backup `PC server`: `C:\TANPHAT-backups\hr-attendance-matrix003\ham003-20261118T171946` (`tp_tanphat_dev.dump` `9.701.510`B / `15.600` mục restore, `filestore.tar.gz` `34.387.973`B, `source-config.tar.gz` `257.100`B, `SHA256SUMS.json`); drift baseline `51/51` khớp; giải nén gói release `62/62` khớp SHA-256 (`0` tệp `mtime=0`).
- Upgrade `-u tp_hr_attendance` (`exit 0`, `0` ERROR): giữ nguyên `355` phiên active, `456` ngày công, `35` mã máy, `78` bản muộn, `39` nhân viên, `12` user, nhóm quyền & `web.base.url`; migration dựng `195` `snapshot_person` (`1|39`, `2|78`, `3|39`, `4|39`) & `1.365` `snapshot_cell`, `LÔ-00003` gắn `partial`.
- Kiểm thực trên `PC server`: ORM rollback `SERVER_MATRIX_OK` (lô 4 `39` người/`18` ngày/`5` nhóm), `SERVER_COMPARE_OK` (lô 4 vs 3 = `40` dòng, `175 same`/`271 only_a`/`2 diff`/`4 unready`), `SERVER_EXPORT_OK` (`92×25`), `SERVER_ACL_OK` (`uid=34` `5/5` bị chặn). Thực tải CSS `/web/assets/9931cc6/web.assets_backend.min.css` (`1.592.899`B, SHA-256 `20a69ca1…`) & JS `/web/assets/2116504/web.assets_backend.min.js` (`8.431.465`B, SHA-256 `f535c84e…`) qua `https://hybrid-send-ready-ballot.trycloudflare.com` đạt `200 OK` (có `FileMatrix`, `tp_compare_batches`, `tp_resolve_compare_batch`, `tp_upload_files`, `o_tp_att_compare_screen`, không `tp_hr_handle`); Playwright ẩn danh public `0` lỗi console/5xx. Vẫn giữ `NOT_RUN`: login admin/importer trình duyệt & suite DB ghi `18079`.

## CHG-20261118-029 — Triển khai Bảng dữ liệu theo file & Đối chiếu A/B (HR-ATTENDANCE-MATRIX-003)

- Ngày 18/11/2026 Asia/Saigon; `tp_hr_attendance` `20.0.2.0.0 → 20.0.3.0.0` (`DEC-058`, `DEC-044`), kế thừa `SIMPLE-002` không chạy lại prompt cũ.
- Backend: parser v2 đọc đủ 39/nhiều nhân viên (gồm blank/unmapped), tách `raw_source_code`/`raw_machine_code`/`source_title`/`source_group`/`absent_raw`; model bất biến `tp.hr.attendance.snapshot.person` / `.cell`, `tp.hr.attendance.resolution`, trạng thái lô `partial`, provenance M2M `source_batch_ids` / `source_line_ids`, `superseded` trên `late`, migration `20.0.3.0.0/post-migrate.py` idempotent, guard quyền/attachment & CAS lock; RPC `tp_upload_files`, `tp_discard_batch`, `tp_matrix_data`, `tp_export_matrix`, `tp_compare_batches`, `tp_apply_compare_valid`, `tp_resolve_compare`, `tp_resolve_compare_batch`, `tp_export_compare`.
- Frontend native OWL/SCSS: đa tệp `upload.js/xml`, màn `FileMatrix` (`matrix.js/xml/scss`, 2 dòng `Vào/Ra`, header 2 tầng, nhóm đơn vị nguồn thu/mở, cột phụ, bộ lọc `DEC-044`, phân trang `10/20/50/100`, mobile toggle + reduced motion) và `AttendanceCompare` (`compare.js/xml`, chọn A/B & sheet, 5 nhóm đối chiếu, xử lý từng ô/kỳ Đi muộn kèm lý do bắt buộc).
- Kiểm thực local `18069`: `ruff` `0`, AST `32/32`, XML `16/16`, JS `10/10`, pure tests `26/26 PASS` + tệp thực `39` người/`7` ngày/`273` ô/`178` sự kiện/`95` trống; backup `.local/hr-attendance-matrix003/backup-ham003-20261118-163916` (`15.600` restore, `1.027` filestore); upgrade `0` ERROR (`post-migrate.py` `8.055s`, giữ `299` phiên/`365` ngày/`39` người); ORM rollback + SQL read-only kiểm matrix/compare/export/ACL (`uid=34` `5/5`, `uid=5` `6/6`); HTTP `web.assets_backend` (`1.592.872` CSS / `8.413.738` JS) và Playwright ẩn danh `0` lỗi console/5xx. `NOT_RUN`: login admin/importer trình duyệt & suite DB ghi `test_matrix_compare.py` (`18079`). Next: push và deploy `PC server`.

## CHG-20261118-028 — Sửa asset public vẫn chứa tay nắm và logic kéo cũ

- Ngày18/11/2026 Asia/Saigon.
- Phản hồi ảnh người dùng sau027 còn sáu chấm là đúng. Kiểm027 chỉ checksum source/compile trong bộ nhớ và trang login, không kiểm bundle mà webclient thực tải. Public `/web/bundle/web.assets_web` còn tham chiếu JS `f3195e5` SHA256 `70795505f0829c24bf72e00e935258c8faee96deca89cac44e5e21617b1311f1`, có `tp_hr_handle`, `o_tp_hr_drag_handle`, `isPointerInValidZone`, thiếu `lastPointer`; header CloudflareDYNAMIC, nên là generated asset server cũ, không chỉ browsercache.
- Packer `.local/auth-session001/package_slice.py` dùng TarInfo mặc địnhmtime0 cho cả gói trước/sau. Odoo native checksum asset dựa URL+mtime, JS gộp cả XML; restart/upgrade vẫn dùng generated attachment1445/1443 tạo09:24Z dù source026 đúng. Đã sửa packerignored đặtmtime theo Git commit gần nhất của từng file; ghi cổng kiểm trong policy/runbook để workflow tái lập được.
- Backup source+metadata trước sửa tại PC `/workspace/.local/hr-order-asset/source-before-20261118T095446Z` (host `C:/Projects/TANPHAT-ONE/.local/hr-order-asset/source-before-20261118T095446Z`); backupDB/filestore/source môi trường gần nhất vẫn `C:/TANPHAT-backups/hr-order-row/hr-row026-20261118T164222`. Chỉ cập nhậtmtime3file table.js/xml/scss, trước0 sau1794995686; SHA256 nội dung giữ khớp b9c3040c. Restarttp-odoo, khôngtunnel/upgrade/CRUDnghiệpvụ/xóa asset thủ công.
- Public sinh và phục vụ JS mới `/web/assets/c7831b0/web.assets_web.min.js` (8.351.729B, SHA256 `0bd1dc5ada62edb4aad6251b1444635a5493c0ce4d14e76c59f70f53716b89ae`) và CSS `/web/assets/e08d09c/web.assets_web.min.css` (1.580.966B, SHA256 `6d5168a812cf4d60c9820b5aebeae57e5f68e026d3c08d6ce1babac1b382f373`). Tracked `scripts/tests/test_hr_employee_order_served_assets.py`8/8PASS local vàpublic: modulethật, khônghandle/hit-testcũ, cópointerup/bounds/whole-row ignore/cursor. Checker còn được kiểm với JSpubliccũ đãlưu và từchốiđúng; RuffPASS.
- Local trước/sau đã phục vụ JS4840c2b mới đúng; không cầnrestart/upgrade local. Các502 tạm trong lúc restart đã kết thúc khi bundle public thực tảiPASS. Application vẫnb9c3040c/HR20.0.1.13.1; chỉ toolkit/docs mớicommit/push/sync, khôngrestart thêm. Full authenticated visual/browserpersist/HOOT/race vẫnchưa chạy; không dùng servedtoken checks làm chứng minh kéoDBE2E. Người dùng tải lại trang để nhận URL mới.

## CHG-20261118-027 — Giao PC server bản sửa kéo cả hàng nhân viên

- Ngày18/11/2026 Asia/Saigon.
- Application commit `b9c3040cee006af788c85b0059daf08f4c7661db` đã push `origin/main`; PC server nhận đúng15/15checksum. Runtime18069/PCserver: HR20.0.1.13.1, chỉ upgradeHR exit0/0ERROR. AUTH/admin không đổi.
- Backup local `.local/hr-order-row/backup-20261118T163542`: dump10.049.127B, filestore294.237.435B/1.027file, source-config321.909B, restore15.600mục; SHA256. PC `C:/TANPHAT-backups/hr-order-row/hr-row026-20261118T164222`: dump9.707.147B, filestore32.133.010B/614archiveentry, source-config2.158.233B, restore15.600mục; SHA256. Snapshot từng môi trường chỉ versionHR đổi; sequence, roster, user/group/ledger/equipment/days/baseURL giữ. Không so datasetlocal vớiserver.
- Native browser regression/VM/backend12/12 và realORM7checks trong rollback PASS. READONLY probe local/server6/6; candidate normalized7/7khớpcommit. Local assets561CSS/1786JS/75XML (6.443.819JSbyte); server561/1786/75 (6.443.990JSbyte), css_errors=[]; biên dịch trong bộ nhớ không lưu attachment. AnonymousHTTP/login local/public desktop1440/mobile390:11/11PASS,0JSerror. Public `https://hybrid-send-ready-ballot.trycloudflare.com`; không restarttunnel.
- Khởi động18069 bằng phiên tiến trình Odoo duy trì sau khi helper background kết thúc; listener và smoke cuối đạt. Runtimeconfig `.local/hr-order-row/candidate-20261118T163523/runtime.conf`; giữ cùng DB/filestore. Gói source cô lập không nạp WIP attendance/reporting/sidebar/branding; checkpoint gốc giữ, workflow026/027 kiểm trong snapshot sạch đúng scope.
- Full authenticated browser/HOOT/persist qua transaction commit/máy khác/race chưa chạy. Không fixture/login/đổi phòng hoặc lưu reorder thử trên DB đang dùng; realORM thử luôn rollback và freshcursor xác nhận nguyên trạng. Nghiệm thu người dùng riêng. Đây là tài liệu xác nhận giao bản, đồng bộ source không restart/upgrade tiếp.

- Next: người dùng tải lại màn danh sách để kiểm trực quan; giữ các ca chưa chạy như acceptance.

## CHG-20261118-026 — Sửa kéo nhân viên quay về cũ và kéo cả hàng

- Ngày18/11/2026 Asia/Saigon; yêu cầu trực tiếp từ ảnh và phản hồi người dùng thay yêu cầu sáu chấm ban đầu. HR20.0.1.13.1; không mở lại AUTH/admin.
- Root cause được tái hiện bằng native pointer engine: body.pe-none làm elementsFromPoint thiếu table/source row khi thả trên placeholder. Nhánh cũ tự bỏ save trước RPC (log PC server60phút không có reorder). Dùng vị trí pointerup cuối trong bounds tbody nguồn, giữ native group/parent và backend kiểm phòng/công ty/quyền. Bỏ cả cột/button sáu chấm; kéo từ cell, ignore checkbox/nút/link/input; đang edit không kéo. Click thường đi qua handler gốc, drag không mở hồ sơ/chọn checkbox.
- Kiểm thực: backend12/12; node VM; tracked browser `scripts/tests/test_hr_employee_order_browser.cjs` biên dịch3 template, dùng native draggable/sortable và sortStart/sortStop, xác nhận đúng lỗi hit-test cũ, kéo lên/xuống đúng anchors, khác phòng/ngoài bảng khôngRPC, lỗi save reload, nút/checkbox/movement/click guard;0pageerror. Browser còn mock RPC/lifecycle/model, không gọi E2E persist. HOOT source4case NOT_RUN do yêu cầu login.
- ORM thật local sau backup: originaladmin su=False, action lên/xuống, flush/invalidate và SQL đọc lại, dense sequence, anchor khác phòng bị chặn, existing viewer bị chặn. Luôn rollback; cursor mới so SHA256 toàn bảng employee/version/company/user/group-rel giữ nguyên. Không commit reorder thử, tạo actor/dữ liệu, đổi phòng, login đá phiên hoặc dùng18079. Race/multiworker và browser với session người thật chưa chạy.
- Local backup `.local/hr-order-row/backup-20261118T163542` DB/filestore/source-config+SHA256, restore15.600 mục/filestore1.027file; candidate `.local/hr-order-row/candidate-20261118T163523`, cùng DB18069. Upgrade chỉ tp_hr_workspace exit0/0ERROR; snapshot chỉ version HR đổi, sequence/roster/quyền giữ nguyên. WIP/sidebar/branding/attendance/reporting và checkpoint gốc giữ, clean workflow snapshot đúng scope.
- [Acceptance](demo/HR_EMPLOYEE_ORDER_ACCEPTANCE.md), [guide](demo/HR_EMPLOYEE_ORDER_USER_GUIDE.md), [runbook](../ops/runbooks/HR_EMPLOYEE_ORDER_DEPLOY_AND_ROLLBACK.md), inventoryHR-T01 cập nhật. PCserver pending tại commit này; next push/deploy đúng commit, backup riêng server, kiểm assets và public rồi ghi kết quả.

## CHG-20261118-025 — Xác nhận assets native sau giao bản và sửa nhãn PC pending cũ

- Ngày18/11/2026 Asia/Saigon. Kiểm trong ORM READ ONLY trên PC server: `web.assets_backend` giải manifest thực và biên dịch 561 CSS, 1.786 JS (6.445.107 ký tự đầu ra), 75 khối XML; `css_errors=[]`. Dùng `preprocess_css`, base `WebAsset._fetch_content`, JS `minify` và `xml`; không gọi lưu bundle/attachment hoặc tạo dữ liệu. Đây là kiểm biên dịch, không thay thế thực thi module/browser đầy đủ.
- Sửa hai nhãn PC pending còn sót trong acceptance HR/AUTH, giữ nguyên phần NOT_RUN thực A/B/MFA/race/fullHOOT/ghi reorder. Không đổi application/DB/quyền/runtime; code chạy vẫn `cfc1af70`, gói docs trước `2f75f68d` đã đồng bộ 7/7 checksum không restart.
- Kiểm liên kết hiện có, scoped diff và workflow snapshot sạch; giữ foreign WIP/checkpoint. Commit/push và đồng bộ riêng tài liệu lên PC server. Next: nghiệm thu người dùng như CHG-024; không tự mở batch khác.

## CHG-20261118-024 — Giao PC server và kiểm public HR-EMPLOYEE-ORDER / AUTH-SESSION-001

- Ngày18/11/2026 Asia/Saigon. Code `cfc1af70` pushorigin/main và deploy37/37checksum. Upgrade đúng3addon exit0/0ERROR; không restarttunnel. Bản chạy18069/PC: HR20.0.1.13.0/admin20.0.2.0.1/auth20.0.2.0.1; API20.0.1.2.0.
- Serverbackup `C:/TANPHAT-backups/auth-hr-finish/auth-hr023-20261118T160600`: dump9.703.292B, filestore29.880.555B/609entry, source-config2.124.283B, restore15.598, SHA256. Snapshot chỉmodules đổi, giữ39nhânviên/32user/55thiếtbị/456ngàycông/roster/groups/implied/ledger/baseURL; không giả datasetlocal bằngserver.
- ORMREADONLYserver20/20PASS; local16/16PASS. AnonymousHTTP/browser+QWeb-render19/19PASS desktop/mobile0JSerror; đây là smoke+visualmock không đăngnhậpA/B. UnitHR12/AUTH8/frontend2/native3template+mouse-sortablemockPASS trướcdeploy. [HR acceptance](demo/HR_EMPLOYEE_ORDER_ACCEPTANCE.md)/[AUTH acceptance](demo/AUTH_SESSION_001_ACCEPTANCE.md) ghi rõNOT_RUN thựcA/B/MFA/multiworker/race/HOOT/realreorderpersist, không can thiệp userđanglàmviệc.
- Driftinventoryserver đã xác minh là prefixcũ của baselineGit, chỉthiếu các mụcattendance đãcommit; đồngbộ bảnđãcommit, không mấtphầnnộidungriêng. Sidebardrift cósẵn giữ, khôngdeployattendance/reporting/brandingWIP. Checkpointgốc giữ, cleanworkflowseal023/024 chỉhash đúnggói; bàn giao source/root docs cậpnhật khôngfinishforeignbatch.
- Đây là docs-only xácnhận kếtquả, không cầnrestart/upgrade tiếp. Next: người dùng nghiệmthu2thiếtbị/HRorder thực tế; phầnchưa kiểm giữnhưacceptance.

## CHG-20261118-023 — Hoàn tất HR-EMPLOYEE-ORDER và sửa cạnh tranh AUTH-SESSION-001

- Ngày18/11/2026 Asia/Saigon. Người dùng giao trực tiếp tiếp tục phần Anti dở, triển khai cả hai hạng mục, áp18069/commit/push/PCserver, không bắt18079.
- HR20.0.1.13.0 tái sử dụng sequence/native sortable; default sequence,id ở list/danh bạ/export; migration khởi tạo theo thứ tự mã hiện có khi sequence trùng. Backend kiểm ID/department/company/active/full visibility và write ACL toàn phòng; RPC chỉ di chuyển theo anchor, không sửa dữ liệu HR khác. Khóa761101 công ty+MVCC và row locks tuần tự hóa reorder/create/transfer/version/archive/delete. Token object nội bộ chặn RPC/import ghi sequence và giới hạn ngoại lệ admin20.0.2.0.1 chỉ sequence (DEC-054 giữ).
- UI tay nắm sáu chấm, preview/marker; invalid drop trả cũ; chỉ phòng đủ điều kiện/sort tùy chỉnh; lọc phòng vẫn kéo, lọc nhân viên/sort khác hiện hướng dẫn/reset. Theo DEC-044 bổ sung inventoryHR-T01, giữ SearchModel/count/pager; backend full department+anchors giữ nhân viên ngoài trang.
- AUTH20.0.2.0.1 sửa lỗ snapshot REPEATABLE READ: fresh primary cursor sau shared transaction lock/precommit; login FOR UPDATE. Đổi màn bị thay phiên sang document độc lập server-validated no-store, dừng document/callback/cache cũ; pagehide ẩn bfcache và persisted restore reload qua xác thực. Không đổi HR lock/admin identity/MFA/quyền.
- Kiểm thực: HR12/12 + AUTH8/8 unit(mock ORM/cursor), frontend2 harnessPASS, native3 templatecompilePASS và chuột với sortable native mock up/down/crossdept/outsidePASS, Ruff/JS/XML/SCSS/diffPASS. ORM READ ONLY18069 16/16 gồm default order, distinct sequence, combined views, viewer denied và direct sequence admin denied, QWeb render. Không gọi mock là business/race integrationPASS. HOOT3 test có source nhưng NOT_RUN do route yêu cầu login; các kết quả AUTH24/24/HttpCase10 của20.0.2.0.0 là lịch sử, không chạy lại bản mới.
- 18069 backup `.local/auth-hr-finish/backup-20261118T155327`: dump10.052.120B, filestore294.236.851B/1025 tệp, restore15.598; upgrade tp_hr_workspace,tp_admin_delegation,tp_web_login exit0/0ERROR. Snapshot roster/users/groups/implied/equipment/days/grants/baseURL giữ nguyên, chỉ version đổi. Runtime dùng candidate riêng từ HEAD+reviewed slice; branding đã cài giữ baseline, không triển khai foreign attendance/reporting/branding/sidebar diffs. Checkpoint gốc giữ, workflow start/finish/check chạy trong snapshot gói sạch.
- Bàn giao: [HR acceptance](demo/HR_EMPLOYEE_ORDER_ACCEPTANCE.md), [user guide](demo/HR_EMPLOYEE_ORDER_USER_GUIDE.md), [runbook](../ops/runbooks/HR_EMPLOYEE_ORDER_DEPLOY_AND_ROLLBACK.md), [AUTH policy](security/AUTH_SESSION_001_POLICY.md). PCserver còn pending tại commit này; next: backup/deploy đúng slice/checksum rồi ghi kết quả. Real A/B/MFA/bfcache thiết bị thật, ORM ghi và race PostgreSQL NOT_RUN để không đá phiên/tạo fixture trên DB đang dùng; nghiệm thu nghiệp vụ người dùng riêng.

## CHG-20261118-022 — AUTH-SESSION-001: mỗi tài khoản một phiên web hoạt động, thông báo thay phiên & Đăng nhập lại về Trang chủ

- Ngày 18/11/2026 (Asia/Saigon). Triển khai [CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md](prompts/CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md) (DEC-057) tại `custom_addons/tp_web_login` `20.0.2.0.0` và `custom_addons/tp_api` `20.0.1.2.0`: bảng `tp_user_active_session` (`active_gen`, `session_nonce` 256-bit), khóa tư vấn `(761157, uid)` chia sẻ cho giao dịch ghi của phiên hiện hành + `precommit` chống ghi trễ và khóa độc quyền khi `_after_session_login` commit winner mới (kể cả `postrollback` khôi phục session và chỉ phát `bus.bus` `tp.auth/session_replaced` đúng đời phiên cũ). Compare-and-clear trên `/web/session/logout` và `destroy` không bao giờ xóa nhầm winner mới; phiên legacy trước nâng cấp trả `session_cutover` tách biệt với `session_replaced`, `unauthenticated` và `403 forbidden`. Màn khóa OWL `TpSessionEndedOverlay` nền sáng `#F3F7FC` làm rỗng `.o_action_manager`/ẩn navbar, đồng bộ đa tab qua `BroadcastChannel`, fallback poll nền 4s (backoff khi lỗi mạng, tạm dừng khi ẩn tab, kiểm ngay khi focus/online/bfcache) và nút **Đăng nhập lại** đưa về `/dang-nhap?redirect=%2Fapp%2Ftp-home` → **Trang chủ TANPHAT ONE**. Giữ nguyên khóa HR (`tp_lock_revision`), quyền Quản trị gốc DEC-053/054, `identitycheck` và stateless Bearer API.
- Kiểm chứng: `ruff check` `0` lỗi; unit `scripts/tests/test_auth_session_001.py` `6/6` PASS; probe đa kết nối PG `8/8` PASS; Odoo `HttpCase` `TestNativeLogin` `10/10` PASS; Playwright 4-context `24/24` PASS (`latency ~1.18s`, poll fallback `~0.83s`, desktop `1440×900` & mobile `390×844` + `reducedMotion`, `0` lỗi JS, `0` HTTP 5xx). `18069`: backup `.local/auth-session001/backup-as001-20261118T144453`, `-u tp_web_login,tp_api` exit `0` / `0` ERROR, snapshot chỉ đổi `modules`. Đồng bộ Git và deploy `PC server` + kiểm public chỉ đọc không đá phiên đang mở.

## CHG-20261118-021 — HR-ATTENDANCE-MATRIX-003: bảng công theo file và đối chiếu trước tổng hợp

- Ngày: 18/11/2026; scope điều phối/tài liệu, không sửa ứng dụng hoặc DB.
- Người dùng yêu cầu tải Excel thấy bảng đầy đủ có bộ lọc; đã chọn giữ riêng file và đối chiếu trước tổng hợp. DEC-058 ghi rõ file cùng kỳ/tên vẫn có nguồn riêng, giờ trùng nhận một lần, khác biệt do người có quyền chọn.
- Tạo [prompt003](prompts/CLAUDE_HR_ATTENDANCE_MATRIX_003_FILE_COMPARISON.md): multi-file, snapshot nguồn bất biến đủ người/ô trống, matrix hai dòng Vào/Ra, header ngày/thứ, source grouping, sticky/scroll/mobile, bộ lọc theo bảng và pager10/20/50/100 nhân viên. Compare A/B, outside-period khác blank, provenance/mapping/late totals đúng kỳ, backend ACL/version/transaction/locked-period/correction. Giữ SIMPLE00220.0.2.0.0/sharedHR/database/API-ready; không viết importer hay DB riêng.
- Kiểm thực: đọc openpyxl/parser thuần file riêng sheet Report, kỳ09–15/11/2026,39 người,178 ngày-người có giờ/95 trống/0 lỗi; đọc source upload/batch/parser/late để xác định thiếu matrix và files[0]. Đây không là import hoặc kiểm matrix runtime. Kiểm nội dung/link mới, diff whitespace và workflow trên snapshot Git sạch đúng baseline; không finish checkpoint của batch khác. Workbook/ảnh/giờ cá nhân không đưa vào Git.
- Tài liệu: status/changelog/roadmap/DEC-058/index/prompt/workflow; commit/push và đồng bộ chính các tài liệu đã commit lên PCserver theo policy. Không upgrade/restart hoặc đổi quyền/session/dữ liệu công. Chưa có matrix/compare hoạt động để kiểm browser/ORM; phần đó giao Claude.
- Next action: thực hiện prompt003 theo từng phần dùng được; acceptance trước code, không fixture trên main/server, commit/push/deploy18069/PCserver, không bắt18079.


## CHG-20261118-019 — HR-ATTENDANCE-SIMPLE-002: tải Excel máy → xem trước → nhập, tổng muộn theo kỳ, bảng công tối giản, tổng quan và nền API-ready

- Ngày 18/11/2026 (Asia/Saigon). Thực thi prompt SIMPLE-002 (DEC-055/056) trong `custom_addons/tp_hr_attendance` `20.0.2.0.0`, commit code `2b531056`: upload Excel máy chấm công với xem trước tự động và nhập một lần (`tp_upload_preview`/`tp_upload_apply`/`tp_upload_cancel`, nhận kỳ 1–3 tuần/tháng, header ngày động, mã máy qua mapping HR, dedupe/xung đột/khóa kỳ); model `tp.hr.attendance.late` lưu nguyên số lần/phút đi muộn của Excel theo kỳ nguồn; Bảng chấm công tối giản Ngày/Tuần/Tháng và xuất file kỳ nguồn; Tổng quan hôm nay/tuần/tháng với `Xem ngày có dữ liệu gần nhất`; trang `Nguồn dữ liệu chấm công` và nền API-ready (`tp.hr.attendance.source`, `source.code`, `event`, `tp_ingest`) với adapter live tắt. Giờ `08:30–17:00` chỉ là tham chiếu hiển thị. Kèm README, acceptance, hướng dẫn, policy §10, runbook phần SIMPLE-002.
- 18069 (`tp_tanphat_dev`): backup `.local/hr-attendance-simple002/backup-has002-20261118T133410`, `-u` 0 ERROR; nhập file thật qua UI: 117 phiên mới, 42 trùng, 2 xung đột, 16 thiếu giờ ra, 1 dòng chưa đối chiếu (trùng tên); tổng muộn 38 dòng = 90 lần/6.418 phút (file 91/6.612 gồm người chưa đối chiếu); phiên 182→299, ngày-người 252→365, dữ liệu tới 15/11/2026; còn 4 lô xem trước đã hủy do e2e. Test thuần 22 PASS, Playwright `33/33` PASS (1440/390/375).
- PC server: drift `58/58`; backup `C:\TANPHAT-backups\hr-attendance-simple002\has002-20261118T141006` (dump `9.587.361`B, filestore `29.827.466`B, source-config `1.845.934`B, restore-list `15.438`, filestore-list `608`, SHA256SUMS); slice 40 tệp + 3 tệp xóa, checksum khớp; `-u tp_hr_attendance` exit `0` / `0` ERROR / 0 warning module; trước/sau giữ nguyên phiên `182`, ngày `252`, nhóm, roster, user `30`, nhân viên `39`, `web.base.url`; 4 bảng mới rỗng. Playwright URL public chỉ đọc `19/19` PASS (deep link ẩn danh → đăng nhập, mặc định hôm nay, nghỉ `Chưa đủ dữ liệu`, donut = tổng nhân viên, tuần 7 cột, tháng 30 cột, API `Chưa cấu hình` + checklist 9 mục, 390px không tràn, 0 lỗi console/5xx); log runtime 0 ERROR. Không nhập Excel thật trên server (HR nhập qua UI).
- `NOT_RUN`: suite ORM `TransactionCase` (không DB test riêng, không 18079/clone/fixture), trình duyệt nhân viên thường (F01, quyền C07/C08), kỳ đã chốt B06, biến thể A06/A07/B03 đổi tên, diễn tập rollback. Chưa nối API máy thật, không realtime.

## CHG-20261118-018 — tp_web_login: bỏ slogan phụ, dịch cụm bước lên trên và thêm link by Tadic

- Ngày 18/11/2026 (Asia/Saigon). Theo yêu cầu bổ sung trực tiếp: trong `custom_addons/tp_web_login` (`20.0.1.6.2`, commit code `86f75df7`), bỏ dòng “Kết nối công việc. Vững bước cùng Tấn Phát.”; gom tiêu đề `Hệ thống quản trị điều hành` và hàng `Kế hoạch – Công việc – Báo cáo` vào `.tp-auth-main` để cụm bước dịch lên trên ngay dưới tiêu đề; giữ `copyright @by Tadic` ở cuối panel trái với `by Tadic` là liên kết `https://tanphatjsc.com/` (`target="_blank" rel="noopener noreferrer"`), màu `#E2EEFA`, gạch chân mảnh màu teal, hover `#5EEAD4`. Cập nhật `tests/test_native_login.py` và `README.md`.
- Kiểm & triển khai `PC server`: XML/AST/CSS/Ruff/`git diff --check` PASS; backup `C:\TANPHAT-backups\ui-login-copy\20261118T134311` (`tp_tanphat_dev.dump` `9.581.246`B, `tp_web_login-pre.tar.gz` `20.423`B); `-u tp_web_login` exit `0` / `0` ERROR; HTTP `200`; Playwright URL public `https://hybrid-send-ready-ballot.trycloudflare.com/dang-nhap` đạt `8/8` viewport desktop/mobile/zoom200 (`0` tràn ngang, `0` lỗi runtime, link `by Tadic` đúng `href`/`target`/`rel`/màu/gạch chân) và kiểm ảnh chụp trực tiếp. `NOT_RUN`: Odoo `TestNativeLogin` trên `18079` và local `18069` (đang tắt).

## CHG-20261118-017 — tp_web_login: cập nhật nội dung panel trái trang đăng nhập và dòng copyright

- Ngày 18/11/2026 (Asia/Saigon). Theo yêu cầu trực tiếp: trong `custom_addons/tp_web_login` (`20.0.1.6.1`, commit code `dac9e6c4`), đổi dòng dưới `TANPHAT ONE` sang `Vững Vàng Hội Nhập`, đổi tiêu đề lớn sang `Hệ thống quản trị điều hành` (2 dòng cân đối trên desktop, 1 dòng trên mobile), và thêm `copyright @by Tadic` (`12.5px`/`12px`, `#9EB8D4`) bên dưới hàng `Kế hoạch – Công việc – Báo cáo`, căn trái thẳng hàng mục `Kế hoạch` trong `.tp-auth-identity-footer`. Cập nhật `tests/test_native_login.py` và `README.md`; giữ nguyên logo, màu nền, bố cục, `tp_branding` và toàn bộ chức năng đăng nhập.
- Kiểm & triển khai `PC server`: XML/AST/CSS/Ruff/`git diff --check` PASS; backup `C:\TANPHAT-backups\ui-login-copy\20261118T133257` (`tp_tanphat_dev.dump` `9.589.335`B, `tp_web_login-pre.tar.gz` `19.828`B); `-u tp_web_login` exit `0` / `0` ERROR; HTTP `200`; Playwright URL public `https://hybrid-send-ready-ballot.trycloudflare.com/dang-nhap` đạt `8/8` viewport desktop/mobile/zoom200 (`0` tràn ngang, `0` lỗi runtime, toggle mật khẩu đạt) và kiểm ảnh chụp trực tiếp. `NOT_RUN`: Odoo `TestNativeLogin` trên `18079` và local `18069` (đang tắt).

## CHG-20261118-016 — AUTH-SESSION-001: prompt một phiên đăng nhập cho mỗi tài khoản

- Ngày18/11/2026. Yêu cầu trực tiếp: máy mới đăng nhập thì phiên máy cũ hết hiệu lực, báo tài khoản đăng nhập ở nơi khác, nút Đăng nhập lại và sau xác thực về Trang chủ.
- Đã đọc native session authenticate/finalize/SID rotation/after-session-login hook, web session routes, custom HR lock/admin revision/identity logout/API error mapping. Prompt yêu cầu server-side winner theo DB/user, atomic login/commit/cache/multiworker, old logout không xóa winner mới, ngăn RPC/file và race request ghi; không khóa theo IP hoặc sửa core.
- Cùng browser profile nhiều tab được giữ; chỉ xác thực đầy đủ/MFA mới thay, identity recheck/refresh/login sai/API-key cron không thay. Bus/fallback đúng phiên, mã nguyên nhân riêng không nhầm mất mạng/403; cache/response trễ/bfcache và không tự retry mutation. DEC-057 giữ quyền/phân hệ và quy trình giao bản liên tục.
- Chỉ prompt/status/decision/roadmap/index/workflow, không sửa application/DB hoặc thử đá phiên thật. Kiểm links/content/diff và workflow snapshot Git đúng baseline; không có runtime/security/browser acceptance mới. Giữ checkpoint/diff của phiên khác; commit/push/sync tài liệu không restart. Next: giao Claude prompt để triển khai và kiểm hai context độc lập trong phạm vi an toàn.


## CHG-20261118-015 — ADMIN-FULL-001: hoàn tất deploy/migration PC server và kiểm chứng URL public

- Ngày 18/11/2026 (Asia/Saigon). Hoàn tất triển khai commit `bec79ccb` (`tp_admin_delegation` `20.0.2.0.0`) lên `PC server` (`tp-odoo`) và đồng bộ tài liệu nghiệm thu [ADMIN_FULL_001_ACCEPTANCE.md](demo/ADMIN_FULL_001_ACCEPTANCE.md).
- Backup `PC server` tại `C:\TANPHAT-backups\admin-full001\af001-20261118T122710` (DB dump `9.580.510`B, filestore `600` mục, source/config, SHA256); chạy `-u tp_admin_delegation` (`exit 0`, `0` ERROR): nâng tự động `uid=43` (`ledger_id=2`) sang `group_full_admin`, seed `group_original_admin` cho `uid=2`, giữ nguyên chức danh/phòng ban HR và toàn bộ dữ liệu nghiệp vụ.
- Kiểm thực `PC server` & URL public: probe ORM không ghi DB đạt 100% (`uid=43` ngang quyền `uid=2` trên mọi phòng ban gồm cả phòng mình, `28/28` phép thử chặn DEC-054 PASS, `6/6` dry-run thu hồi rollback PASS, `uid=34` nhân viên thường giữ nguyên `mobile_phone` privacy); HTTP `/web/health` & `/dang-nhap` `200`; Playwright URL public `12/12` PASS (`1440×900` & `390×844`, `0` lỗi runtime, `web.base.url` và DB không đổi). Ghi rõ `NOT_RUN`: đăng nhập trình duyệt người thật `uid=43` (chờ người dùng đăng nhập lại làm mới phiên).

## CHG-20261118-014 — Khôi phục bàn giao admin đồng thời với prompt chấm công

- Trong khi chuẩn bị tài liệu013 trên baseline142535c2, phiên khác commitbec79ccb cho ADMIN-FULL-001/CHG-012. Staging từ snapshotcũ đã vô tình lùi phần012 trong status/changelog/decisions/roadmap. Đã khôi phục nguyên nội dung012 từ commit, giữ toàn bộ013/DEC-056 và prompt mới; không sửa source hoặc dữ liệu.
- Tạo workflow trên sourceGit mới nhất, kiểm diff phục hồi/links/nội dung và guardHEAD trước commit; không coi phần code đang sửa bởi phiên khác là đã kiểm. Chỉ docs, không testquyền/upgrade/restart.


## CHG-20261118-013 — HR-ATTENDANCE-SIMPLE-002: bổ sung tải Excel máy và bảng công tối giản

- Ngày18/11/2026. Người dùng chưa chạy prompt trước, yêu cầu tải thẳng báo cáo máy1–3tuần/tháng để tự gen giờ theo thứ/ngày và tổng đi muộn. Chốt cuối08:30–17:00; giữ nguyên Lần/Phút từ Excel, không tự tính lại.
- Đã đọc workbook riêng bằng bundled Python/openpyxl, kiểm parser thuần không ORM/DB: sheetReport,39người,kỳ09–15/11,150cặp/28thiếuOUT/95ôtrống/0lỗi. Header Đi muộn/Lần/Phút có nguồn tổng kỳ; parser/importhelp hiện chủ động bỏ tổng nên chỉ mới xác nhận định dạng, chưa có tính năng mới hoặc số mới trong DB.
- Cập nhật cùng prompt002, DEC-056/roadmap/index/status: upload tự preview→nhập/mappingID/dynamicdateheaders/kỳlặp/dedupe; lưu tổng kỳ có nguồn, không chia tổng tuần cho ngày/cộng chồng tuần-tháng; output ngày/chi tiết chỉ ngày-thứ/giờ, kỳ chỉ tổng muộn và nhận diện cần thiết. Giữ API-ready và dashboard003KPI, quyền/privacy/data cũ.
- Kiểm nội dung/link/diff và snapshotGit độc lập; giữ code/dữ liệu thật, checkpoint và diff phiên khác. Không test/runtime/import/migration hoặc seed công thật; subagent không khởi tạo do runtime model, không gọi là audit độc lập. Giao đúng tài liệu lênGit/PCserver, không restart; ứng dụng do Claude triển khai sau.


## CHG-20261118-012 — ADMIN-FULL-001: triển khai Quản trị viên toàn hệ thống và ngoại lệ chỉ Admin gốc cấp quyền trên 18069

- Ngày 18/11/2026 (Asia/Saigon). Nâng cấp `tp_admin_delegation` `20.0.1.4.1 → 20.0.2.0.0` theo DEC-053 và DEC-054.
- `security/admin_full_security.xml`, `security/ir.access.csv` & `models/delegation.py`: thêm nhóm nguồn `group_original_admin` (chỉ Quản trị gốc cấp/thu quyền quản trị) và nhóm vai trò `group_full_admin` (toàn quyền hệ thống và nghiệp vụ mọi phòng ban kể cả phòng mình như admin hiện tại); đọc ledger trực tiếp qua SQL (`_tp_has_live_admin_grant`) độc lập với `base.group_system`; bổ sung migration idempotent `_migrate_admin_full_001()` (`post_init_hook` & `migrations/20.0.2.0.0/post-migrate.py`); thêm `tp_admin_scope_revision` vào `_get_session_token_fields()` để kiểm lại phiên/tab mở sẵn; chặn báo thu hồi thành công khi vẫn còn quyền admin từ nguồn khác.
- `models/guards.py`, `models/business_scope.py`, `models/hr_accounts.py`, `data/full_admin_access.xml` & `views/`: thực thi ngoại lệ DEC-054 ở backend (chặn non-Original-Admin cấp/thu admin, thêm/gỡ nhóm admin trực tiếp hoặc kế thừa trên `res.users`/`res.groups`, sửa/khóa/reset Admin gốc hoặc Admin khác, sửa ACL/server action/cron/cài-gỡ-import module/XMLID/view/tham số bảo mật; chặn làm mất Admin gốc hoạt động cuối cùng); bỏ giới hạn `group_scoped_staff` khi giữ `base.group_system`; giữ nguyên bảo vệ `mobile_phone` (`HR-DELEGATE-FIX-001`) ở nhân viên thường.
- Kiểm thực `18069`: Ruff, AST (21 tệp), XML (8 tệp), CSV (2 tệp), JS, `unit_admin_full_check.py` 34/34 PASS; backup `.local/admin-full001/backup-af001-20261118T120130` (dump `9.935.007`B, filestore `1.000` mục, SHA256); `-u tp_admin_delegation` exit `0` / `0` ERROR; probe ORM chỉ đọc và Playwright `18069` `12/12` PASS (desktop `1440×900` & mobile `390×844`, `0` lỗi JS/OWL/RPC/5xx). Chuẩn bị push và deploy PC server.

## CHG-20261118-011 — HR-ATTENDANCE-SIMPLE-002: prompt chấm công gọn và chuẩn bị API máy

- Ngày18/11/2026. Yêu cầu trực tiếp: dashboard tổng nhân viên/nghỉ hôm nay/đã về; xem ngày, tuần, tháng; giữ dataExcel đã import và chuẩn bị API máy lênweb sau. DEC-055 ghi scope đơn giản, không mở payroll/GPS/datalake hoặc connector hãng chưa có thông số.
- Tạo CLAUDE_HR_ATTENDANCE_SIMPLE_002_DASHBOARD_AND_API_READY.md: lightHRlayout/KPI/chart/table/filter, menu thường gọn; nghỉ có căn cứ khác no_punch/no_source, trạng thái theo latestevent/không đếm OUTtrưa là nghỉ cảngày, nguồn cũ không realtime, người distinct khác ngày-người. Model session hiện check_in/out bắt buộc được chỉ rõ; raw/staging punch chỉ thêm tối thiểu khi cần, preserveExcel và ngày tổng hợp.
- ĐiểmAPI: normalizedevent/source/mapping/timezone/direction/cursor/retry/dedupe/lateevent, sharedingestion/rollup, config/chưakếtnối và credentialbackend; chưa mở publicwrite hoặc livepolling, không giảđã nối. Nhân viên thường vẫnchỉđọc, adminpolicy053/054 giữ; advancedbackend/action/history khôngxóa đểđơn giảnUI.
- Chỉ tài liệu/status/decision/roadmap/indexprompt; không app/data/quyền. Kiểm source và caller hiệncó, tính nhấtquán/ngàynguồn/links/diff và snapshotGit, applicationkhôngđổi; chưa testdashboard/API vìchưa triểnkhai. Giao docs đúngscope/push/sync khôngrestart; nextClaude làmSIMPLE002, cầnAPIhãng/mã/ca/network/auth vềsau đểnốithật.

## CHG-20261118-010 — ADMIN-FULL-001: chỉ admin gốc được cấp/thu quyền admin

- Ngày18/11/2026. Bổ sung trực tiếp từ người dùng: admin được cấp quản trị mọi phòng như đã chốt nhưng không cấp người khác làm admin; chỉ admin gốc quản lý quyền admin. DEC-054 thay đúng phần cấp quyền của DEC-053/CHG-009, không đưa lại giới hạn phòng mình.
- Sửa prompt hiện hành tại cùng path: ngoại lệ cấp/thu ở backend, nhận diện admin gốc riêng, chặn nhóm trực tiếp/ngụ ý/nested/import/API/sudo, bảo vệ nguồn/credential admin gốc và đường code/security có thể tự cấp admin. Giữ nghiệp vụ/phòng/HR/thiết bị/báo cáo, migration grant đã có khi giao thực thi; quyền role nghiệp vụ thường không được kéo theo admin.
- Cập nhật AGENTS/status/DECISIONS/roadmap/index cùng scope. Chỉ prompt/policy, không application, grant/DB hoặc dịch vụ. Không claim test quyền mới hoặc triển khai. Kiểm nội dung nhất quán/link/diff và source unchanged; seal snapshotGit, foreignsource/docs giữ; commit/push/sync tài liệu không restart.
- Subagent review không khởi tạo do modelruntime; không gọi review độc lập. Next: giao Claude bản prompt đã cập nhật; không dùng đoạn009 cho phép admin thứ hai cấp tiếp.

## CHG-20261118-009 — ADMIN-FULL-001: chốt admin thứ hai toàn hệ thống và prompt thay mô hình giới hạn

- Ngày18/11/2026. Yêu cầu trực tiếp mới: người được cấp admin có toàn quyền như admin hiện tại, không ràng buộc phòng ban, kể cả phòng mình. DEC-053 thay phần xung đột DEC-050, giữ vai trò nhân viên là dữ liệu riêng và workflow/admin native. Không tự thiết kế cấp Owner/Admin chức năng khác nhau.
- Tạo prompt CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md: chung quyền admin thực/native groups/capability, HR/KH-KD/Kho/Báo cáo/settings/apps; xử lý helper từng trả false khi user có system; migration các grant đang hiệu lực khi thực thi, không tự chọn thêm user; provenance quyền/implied groups, thu hồi phiên cũ và giữ quyền nghiệp vụ cập nhật hợp lệ.
- Cập nhật AGENTS/status/decisions/roadmap/index prompt để phiên khác không xây tiếp scope phòng mình cũ. Lượt này chỉ tài liệu, không grant/migration/source ứng dụng hoặc DB. Giữ bản sửa HR20.0.1.4.1 đã giao008.
- Kiểm source/caller và policy; Markdown links/diff/unchanged app và workflow trên snapshotGit đúng batch. Không test runtime/quyền mới/browser vì chưa triển khai; không fixture18079/main/server. Foreign source/docs giữ riêng; commit/push/sync đúng tài liệu, không restartOdoo. Next: giao Claude promptADMIN-FULL-001 theo DEC-053 và policy rollout17/11.

## CHG-20261118-008 — HR-DELEGATE-FIX-001: hoàn tất deploy PC server, kiểm thực quyền delegate thực và URL public

- Ngày 18/11/2026 (Asia/Saigon). Commit ứng dụng `edb717f9` (`tp_admin_delegation` `20.0.1.4.1`) đã push `origin/main` và triển khai lên PC server (`tp-odoo`).
- PC server: preflight `14/14` tệp khớp baseline; backup `C:/TANPHAT-backups/admin-delegate002/s5-hdf001-20261118T102705` (dump `9.572.310`B, filestore `29.820.900`B / `597` mục, `restore-list` `15.437` dòng, `source-config` `3.059.439`B, SHA256); `-u tp_admin_delegation` exit `0` / `0` ERROR; snapshot nghiệp vụ, `ledger 1/1` và `web.base.url` giữ nguyên tuyệt đối trước/sau nâng cấp và sau kiểm trình duyệt.
- Kiểm thực bằng quyền delegate thực trên PC server (`SET TRANSACTION READ ONLY` + `with_user`, rollback): `hr.employee` (`list` 1918, `form` 1920, `search` 1919), `tp.hr.delegated.profile.wizard`, `tp.hr.account.wizard` và `hr.employee.public` đều có `missing_field_nodes=[]` theo đúng model cha/bảng con; không còn `mobile_phone` trong XML/metadata của delegate, giữ `work_phone`; `web_search_read` trả `35` hồ sơ ngoài phòng (`0` phòng mình), `web_read_group` (`department_id`/`job_id`/`tp_account_status`/`active`) và `web_read` chi tiết đạt; chặn `read`/`search`/`export_data` trên `mobile_phone` và `default_mobile_phone` giả; Tổng quan HR `missing_contact` khớp số dòng drill-down (`work_email` + `work_phone`), chặn drill-down `mobile_phone`, XLSX không lộ điện thoại/thông tin riêng; `tp_get_my_profile` cá nhân vẫn giữ `mobile_phone` của chính mình; Admin chính và nhân viên thường giữ nguyên hành vi.
- Kiểm trình duyệt: Playwright (`admin`, desktop `1440×900` & mobile `390×844`) đạt `13/13` trên `18069` và `13/13` trên `https://hybrid-send-ready-ballot.trycloudflare.com`, `/web/health` và `/dang-nhap` `HTTP 200`, log runtime `0` ERROR. Giới hạn ghi rõ: trình duyệt bằng phiên đăng nhập của actor delegate thật `NOT_RUN` (không có mật khẩu/cookie phiên, không reset mật khẩu hoặc tạo tài khoản giả); suite Odoo `test_hr_profile.py` `NOT_RUN` trên DB đang dùng theo DEC-051.

## CHG-20261118-007 — HR-DELEGATE-FIX-001: sửa lỗi mobile_phone trên safe view HR và khóa đường wizard/drill-down của tài khoản ủy quyền

- Ngày 18/11/2026 (Asia/Saigon). `tp_admin_delegation` `20.0.1.4.0 → 20.0.1.4.1`. Xử lý lỗi `UncaughtPromiseError: "hr.employee"."mobile_phone" field is undefined` (`ListArchParser`) của tài khoản quản trị được ủy quyền không thuộc `hr.group_hr_user`.
- `views/hr_profile.xml`: bỏ `<field name="mobile_phone"/>` khỏi `delegated_employee_list` và `delegated_employee_form`, giữ `work_phone` ở list/form/search, đặt `export_xlsx="false"` trên list nhất quán với guard `export_data`, và gắn `groups="hr.group_hr_user"` trên `<field name="mobile_phone"/>` trong `delegated_hr_profile_form`.
- `models/hr_profile.py` & `models/guards.py`: gắn `groups='hr.group_hr_user'` lên `ScopedHrProfile.mobile_phone`; bổ sung `_allowed_profile_fields()` kiểm `_has_field_access` trên cả `hr.employee` và wizard; chặn truyền trường hạn chế qua `create`/`write` hoặc `default_*` context (`AccessError`); khi sửa hồ sơ ngoài phòng chỉ ghi `_allowed_profile_fields()` với context sạch để không gửi `False` làm mất `mobile_phone` sẵn có; `ProtectedEmployee` chặn ghi trường thiếu field-group trên hồ sơ người khác kể cả qua `sudo()`, giữ nguyên cập nhật hồ sơ cá nhân (`tp_save_my_profile`).
- `models/hr_overview.py` & `static/src/hr_overview_patch.js`: bỏ `mobile_phone` khỏi `PROJECTION_FIELDS` (chặn dò qua RPC `action_employees`), tính `missing_contact` và `missing_contact_domain` của Tổng quan HR ủy quyền theo `work_email` + `work_phone`; admin/HR giữ nguyên view và trường `mobile_phone`.
- Kiểm thực local `18069`: Ruff, AST (20 tệp), XML (6 tệp), `node --check`, `unit_guard_check.py` 24/24 PASS; backup `.local/admin-delegate002/backup-hdf001-20261118T100532` (dump 9.934.770B, filestore 998 mục, SHA256); `-u tp_admin_delegation` exit 0 / 0 ERROR, 26 bảng giữ nguyên fingerprint; probe ORM chỉ đọc (`SET TRANSACTION READ ONLY` + rollback) và Playwright `18069` 13/13 PASS (desktop `1440×900` & mobile `390×844`, 0 lỗi JS/OWL/5xx). Chuẩn bị push và deploy PC server.

## CHG-20261118-006 — ADMIN-DELEGATE-002: xác nhận lỗi mobile_phone ở HR native view

- Ngày18/11/2026. Người dùng báo UncaughtPromiseError/ListArchParser: hr.employee.mobile_phone undefined trên public bằng tài khoản ủy quyền.
- Probe PCserver get_views(list/form/search), with_user và READ ONLY/rollback: delegate không có hr.group_hr_user; list1918/form1920 chứa mobile_phone nhưng field metadata thiếu, search1919 không có mismatch này. Admin chính có metadata. Không lấy field của bảng con để kết luận form admin có lỗi.
- Nguyên nhân: delegated safe view gọi mobile_phone trong khi tp_hr_attendance.directory_privacy giới hạn field bằng nhóm HR. Cần scope/whitelist/group đúng, giữ bảo vệ thông tin cá nhân, không cấp HR toàn cục hoặc thêm cộtDB. Restart không sửa được source mismatch.
- Chỉ ghi nhận blocker/status/audit, chưa sửa ứng dụng, chưa grant/revoke hoặc thay dữ liệu. Evidence riêng ignored.local; không đưa danh tính/secret vàoGit. Docs-only snapshot seal, source không đổi; không fixture/test18079/browser actor hoặc code đã sửa. Commit/push/sync đúng tài liệu, không restart runtime.

## CHG-20261118-005 — ADMIN-DELEGATE-002 S4: KH-KD — tình trạng/ghi chú/lịch sử dự án và giá gói thầu ngoài phòng qua command gốc

- Ngày 18/11/2026. `tp_admin_delegation` 20.0.1.4.0. Chẩn đoán từ source: adapter 001 đã cho delegate capability KD `prepare` và capability hợp đồng/financial.read trên dự án ngoài phòng (metadata, đối tác, tạo gói thầu, WBS tạo/sửa/giao việc, workflow hợp đồng chạy thật). Riêng cổng `_kd_money_read` còn đòi phân công dự án, nên nút Tình trạng/Ghi chú bị ẩn, `_kd_apply` từ chối status/note/bid/amount, lịch sử dự án và giá gói thầu không đọc được: có capability nhưng backend chặn.
- `business_scope.py`: `_kd_money_read` cộng đúng dự án `other_project` (khóa và kiểm lại nguồn project/hợp đồng/CRM/team, ủy quyền sống); own/mixed/unknown giữ baseline. `tp.project.update`/`tp.task.update` đọc theo cùng scope dự án ngoài phòng. Không cấp assignment/grant/HEAD; ghi vẫn qua `tp.project.command`/`tp.task.command` gốc (phiên bản, mã thao tác, lịch sử actor thật).
- Ngoại lệ giữ: báo tiến độ task chỉ người được giao/HEAD; sửa gói thầu của owner khác, giao owner/tài liệu/nhận rà soát hợp đồng cần HEAD; CRM hồ sơ dự án theo owner (admin chính cũng không chạy chuẩn bị/nộp thay owner), chưa có adapter ghi CRM; hồ sơ KD (giao khoán/sản lượng/nghiệm thu/thanh toán/năng lực/nghĩa vụ/kế hoạch) baseline; ký/hiệu lực không mở.
- Kiểm: Ruff/AST đạt; 2 ca Odoo mới (status/note/lịch sử qua command, dự án phòng mình không đổi, thu hồi; WBS giao việc, tiến độ vẫn của người được giao) NOT_RUN theo chính sách. Main: backup `.local/admin-delegate002/backup-s4-20261118T020749` (dump 9.934.484B, filestore 998 mục, SHA256); `-u tp_admin_delegation` exit0/0ERROR, cảnh báo giống S3; fingerprint 26 bảng giữ, chỉ đổi version; health 200. Probe chỉ đọc: admin chính/nhân viên thường như trước; delegate trên main NOT_RUN (ledger 0). Main và server đang có 0 dự án được quản lý, 0 hợp đồng, 0 CRM gắn dự án, 0 hồ sơ KD: hành vi theo bản ghi NOT_RUN.
- PC server `f91d699c`: preflight 7/7 tệp đúng baseline; backup `C:/TANPHAT-backups/admin-delegate002/s4-20261118T050616` (dump 9.570.166B, filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng, SHA256). `-u tp_admin_delegation` exit0/0ERROR, checksum 7/7; snapshot nhân viên/tài khoản/nhóm/roster/thiết bị/đề xuất/ledger/ngày công/nhóm ngụ ý/Báo cáo/baseURL giữ, chỉ đổi version. Probe chỉ đọc (kết nối READ ONLY, delegate lấy từ ledger 1/1): trước deploy delegate không đọc lịch sử dự án/công việc; sau deploy đọc được theo scope (tổng 0/0 dòng, server 0 dự án được quản lý), command dự án/công việc và workflow hợp đồng như trước, không nhóm CRM/HEAD, không tạo CRM. Admin chính, nhân viên thường giống hệt trước deploy (ngoài tên module override). Public `/web/health` 200, `/dang-nhap` 200, `/web/login`/`/odoo` chuyển hướng như cũ. Ghi thật, race, browser phiên delegate NOT_RUN.
- Tổng kết batch ADMIN-DELEGATE-002 (S1–S4): AD2-01/02 PASS (đọc); AD2-03/04/05/06/07/09 PARTIAL; AD2-08 thu hồi và AD2-10 browser NOT_RUN. Gap còn lại: duyệt/thực hiện đề xuất Kho và ghi CRM qua ủy quyền chưa có adapter; phiếu thiết bị thiếu phòng frozen không mở; 10 ca Odoo mới/sửa trong `tp_admin_delegation/tests` NOT_RUN (không 18079/clone/fixture).

## CHG-20261118-004 — ADMIN-DELEGATE-002 S3: Kho — máy rảnh trong kho chung và Gán / Đổi máy / Trả về kho qua ủy quyền

- Ngày 18/11/2026. `tp_admin_delegation` 20.0.1.3.0. Kho dùng chung không bao giờ là "phòng khác": delegate chỉ đọc máy rảnh (trong kho, chưa có người giữ, đủ điều kiện gốc) của công ty có ủy quyền để chọn; máy thay thế mua cho người phòng mình/không rõ bị ẩn. Tệp/chatter/lịch sử/sửa/nhãn/đăng ký/tạo phiếu trên máy kho vẫn baseline.
- `equipment_handover.py`: delegate gọi đúng `tp_quick_action`/popup gốc. Capability sống dưới lock → replay chỉ của chính mình → khóa máy `FOR UPDATE NOWAIT` (race hai người chọn một máy: người sau bị từ chối) → khóa nguồn FOR SHARE → kiểm lại công ty, scope phòng mình, người nhận có phòng hiện tại ngoài phòng mình và không phải chính mình, máy trả/đổi do phòng khác giữ, máy mới còn trong kho chưa có chủ → chạy `_tp_quick_run` gốc dưới `sudo` có sentinel nội bộ, savepoint, kiểm hậu điều kiện. Đổi máy trả A + gán B nguyên tử. Phiếu ghi người thao tác là delegate. Popup: dòng ACL domain rỗng + override chỉ delegate (popup của chính mình); người nhận bỏ phòng mình/không phòng.
- Gap còn lại: duyệt/trả lại/thực hiện đề xuất của người/phòng khác qua ủy quyền chưa có adapter (chỉ đọc từ S1); lịch sử thiếu phòng frozen không mở.
- Kiểm: Ruff/AST/CSV đạt; 2 ca Odoo mới NOT_RUN theo chính sách. Main: backup `.local/admin-delegate002/backup-s3-20261118T014719` (dump 9.934.366B, filestore 998 mục, SHA256); `-u tp_admin_delegation` exit0/0ERROR; fingerprint 26 bảng giữ, chỉ đổi version. Probe chỉ đọc: admin chính 7/7 máy rảnh, popup/nhãn như cũ; nhân viên thường 0 máy, không tạo popup, `tp_quick_action` AccessError. Delegate trên main NOT_RUN (ledger 0/0); gán/đổi/trả thật và race NOT_RUN.

- PC server `1a248463`: preflight 10/10 tệp đúng baseline; backup `C:/TANPHAT-backups/admin-delegate002/s3-20261118T015400` (dump 9.570.622B, filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng, SHA256); `-u tp_admin_delegation` exit0/0ERROR, checksum 10/10. Snapshot nhân viên/tài khoản/nhóm/roster/thiết bị (55, custody không đổi)/đề xuất/ledger/ngày công/Báo cáo/baseURL giữ; chỉ đổi version. Probe chỉ đọc trước/sau (delegate lấy từ ledger 1/1): trước delegate 0 máy kho, mở popup/in nhãn/`tp_quick_action` AccessError → sau thấy 7/7 máy rảnh (0 bị ẩn), 0 quyền ghi, 0 tệp/0 chatter máy kho, tạo popup được, 35 người nhận (0 phòng mình/0 không phòng), mở Gán và `default_get` chạy, in nhãn máy kho AccessError (kho chỉ để chọn), 24 thiết bị giữ ngoài phòng như S1. `tp_quick_action` dừng ở khóa nguồn (giao dịch chỉ đọc), nên kiểm chính sách trực tiếp: người nhận phòng mình và trả máy phòng mình AccessError, người nhận ngoài phòng hợp lệ, máy đã có chủ UserError. Admin chính và nhân viên thường giống hệt trước deploy. Public: health/`/dang-nhap` 200, `/web/login` và `/odoo` chuyển hướng như cũ. Gán/đổi/trả thật, race hai phiên và browser delegate NOT_RUN.

## CHG-20261118-003 — ADMIN-DELEGATE-002 S2: Báo cáo — sửa baseline admin chính và scope đọc ủy quyền có truy nguồn

- Ngày 18/11/2026. `tp_admin_delegation` 20.0.1.2.0. Chẩn đoán trước sửa (server, chỉ đọc): admin chính có `base.group_system` nhưng không có nhóm Báo cáo nên dashboard/hồ sơ/nghĩa vụ AccessError (`dashboard.py:20`); delegate dừng ở nghĩa vụ (`dashboard.py:29`). Scope cũ mở nháp cá nhân chưa có snapshot (trái baseline riêng tư) và bỏ sót mọi hồ sơ đã gửi.
- Admin chính: `base.group_system` ngụ ý `group_reporting_config` (vai trò cấu hình đã chốt, kéo theo người dùng Báo cáo). Hàng nghiệp vụ vẫn theo `_tp_report_domain`/assignment: không thành reviewer, không thấy nháp người khác, tự cấp assignment AccessError. Không `sudo()` dashboard, không cấp nhóm cho mọi actor, không sửa core; đặt trong `tp_admin_delegation` vì `tp_reporting` đang có source dở của batch khác.
- Delegate (`reporting_scope.py`, một scope cho list/form/dashboard/export): nguồn có company/phòng/owner xác định ngoài phòng mình; hồ sơ cá nhân đã gửi và hồ sơ phòng, không tài chính; dòng, mọi payload snapshot, carry/rollup và dependency phải trỏ tới kế hoạch/dự án/task/hồ sơ cũng mở; kế hoạch mở theo cả cây quý → tháng → tuần; nghĩa vụ, chỉ đạo (cả hồ sơ gốc ngoài phòng), phản hồi `published`, lịch sử, nội dung phần mẫu theo hồ sơ. Nháp/trả lại người khác, cấp công ty, nguồn trộn/unknown giữ baseline. Ghi/nộp/rà soát/chốt/chỉ đạo/hợp nhất/tài chính/assignment giữ capability; đổi nguồn ngoài phòng bị chặn dưới lock. Dashboard có nhãn "Quản trị được ủy quyền" và ghi chú số thực hiện.
- Navigation: gốc Báo cáo mở dashboard; lá Tổng quan, Kế hoạch, Chỉ đạo và "Báo cáo ngoài phòng" (menu ẩn, chỉ đọc) theo capability sống. Settings/Apps/cấu hình Báo cáo giữ admin chính.
- Kiểm: Ruff/AST/XML đạt; logic SQL chạy đúng câu lệnh module trên CTE tổng hợp (không DDL/DML, chỉ đọc, rollback): 5/5 hồ sơ nguồn không truy được bị loại, 4 cạnh nguồn, cây bỏ nhánh khác company/mồ côi. 6 ca Odoo NOT_RUN theo chính sách. Main: backup `.local/admin-delegate002/backup-s2-20261118T011220` (dump 9.933.725B, filestore 998 mục, nguồn/config, SHA256); `-u tp_admin_delegation` exit0/0ERROR, lần hai sau khi thay dòng ACL đọc nội dung phần cho mọi nhân viên bằng override chỉ delegate; fingerprint 26 bảng chỉ đổi `res_groups_implied_rel` +1 và version. Probe chỉ đọc: admin chính có nhóm cấu hình/người dùng, 10 model và dashboard chạy, 13 menu Báo cáo, tự cấp AccessError; nhân viên thường vẫn AccessError như HEAD. Main/server có 0 hồ sơ/kế hoạch/snapshot nên nhánh dữ liệu chưa chạy thật; delegate trên main NOT_RUN (ledger 0/0).
- PC server `42682b51`: preflight 12/12 tệp đúng baseline; backup `C:/TANPHAT-backups/admin-delegate002/s2-20261118T012716` (dump 9.568.634B, filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng, SHA256); `-u tp_admin_delegation` exit0/0ERROR, checksum 12/12. Snapshot nhân viên 39/tài khoản 29/nhóm người dùng/roster/thiết bị/đề xuất/ledger/ngày công/Báo cáo (0 hồ sơ/kế hoạch/snapshot/nghĩa vụ/chỉ đạo/assignment)/baseURL giữ; chỉ đổi version và `res_groups_implied_rel` 88 → 89. Probe chỉ đọc trước/sau (`SET TRANSACTION READ ONLY` + `with_user`, rollback; delegate lấy từ ledger 1/1): admin chính trước AccessError cả 10 model/dashboard → sau có nhóm cấu hình/người dùng, 10 model và dashboard chạy, menu Báo cáo, tự cấp AccessError. Delegate trước lỗi nghĩa vụ/chỉ đạo/snapshot/dashboard → sau 9 model và dashboard chạy (nhãn ủy quyền, ghi chú), assignment vẫn AccessError, 0 dòng phòng mình/không phòng/khác company/của mình, 0 quyền ghi, menu thêm Tổng quan/Kế hoạch/Chỉ đạo/Báo cáo ngoài phòng, không Settings; không nhóm Báo cáo/system. Nhân viên thường giống hệt trước deploy. Public không đăng nhập: health/`/dang-nhap` 200, `/web/login` và `/odoo` chuyển hướng như cũ. Browser phiên delegate NOT_RUN.

## CHG-20261118-002 — ADMIN-DELEGATE-002 S1: HR overview và Kho dashboard/summary/đề xuất theo scope ủy quyền

- Ngày 18/11/2026; tiếp checkpoint 17:21:28Z, không reset batch khác. Ma trận actor/action/nguồn và bảng AD2 lập trước code trong [acceptance](demo/ADMIN_DELEGATE_002_ACCEPTANCE.md). `tp_admin_delegation` 20.0.1.1.0.
- HR: tổng quan/KPI/biểu đồ/bộ lọc/drill-down/XLSX dùng chung một tập hồ sơ do chính actor đọc được: công ty đang xem, phòng xác định và khác phòng mình; scope phòng chưa đầy đủ thì từ chối. Drill-down chỉ nhận field whitelist và `= != in not in`; không cấp nhóm HR, `can_create` theo quyền tạo thật. Hook `_tp_population_source`/`_tp_action_domain` trong `tp_hr_workspace` giữ nguyên hành vi admin/HR.
- Kho: dashboard, drill-down và `tp_main_summary` đi qua `check_admin(env, self)` tới adapter delegate; `common.is_admin` không đổi. Đếm theo quyền đọc đã scope; dòng lô nhập chờ bổ sung ẩn khi không đọc được. Đề xuất/dòng/nhật ký đọc khi người cần, người nhận và thiết bị đều xác định ngoài phòng mình, actor không phải người tạo/phụ trách/người cần; ghi, tạo và workflow đề xuất vẫn chỉ admin chính (PARTIAL).
- Navigation: lá Tổng quan HR (scope đủ) và Yêu cầu đề xuất (đọc được) theo capability sống, giữ thứ tự menu; nhãn "Quản trị được ủy quyền" trên hai dashboard. Settings/Apps giữ admin chính.
- Kiểm: AST/XML/CSV, Ruff cho file sửa (2 lỗi có sẵn ở HEAD `dashboard.py` giữ nguyên), kiểm thuần bộ lọc projection 17 ca PASS. 2 ca Odoo mới NOT_RUN (không fixture main/server, không 18079/clone). Main: backup `.local/admin-delegate002/backup-s1-20261118T003551`, chỉ `-u tp_admin_delegation` exit0/0ERROR, 20 bảng fingerprint giữ, ledger 0/0; probe chỉ đọc: admin chính như cũ, nhân viên thường không mở thêm. Delegate trên main NOT_RUN (không ledger, không grant thử).
- PC server `955c9625`: preflight 16/16 baseline, backup `C:/TANPHAT-backups/admin-delegate002/s1-20261118T004531` (dump 9.568.047B, filestore 32.054.505B/606 mục, source-config, restore-list, SHA256), `-u tp_admin_delegation` exit0/0ERROR, checksum 16/16; snapshot nhân viên/tài khoản/nhóm/roster/thiết bị/đề xuất/ledger/ngày công/baseURL giữ, chỉ đổi version. Probe chỉ đọc delegate thật lấy từ ledger 1/1: HR 35 = danh sách 35, 0 hồ sơ phòng mình, lọc private bị từ chối, XLSX chạy, không tạo; Kho 24 thiết bị, 10 ô KPI khớp danh sách, 0 dòng phòng mình; đề xuất 0/1, không ghi/tạo; không Settings/nhóm/system/nhóm HR. Admin chính và nhân viên thường như baseline. Public không đăng nhập health/login 200.
- S1b: RPC thẳng `open_ui_detail('pending_import')` còn trả action cho delegate dù dashboard đã ẩn; thêm `check_access` lô/dòng nhập và ca hồi quy. Main restart 0 ERROR, admin chính vẫn mở. Browser phiên delegate NOT_RUN (không dùng mật khẩu/phiên người thật).

## CHG-20261118-001 — ADMIN-DELEGATE-002: audit chỉ đọc và prompt hoàn thiện quyền quản trị

- Ngày18/11/2026, Asia/Saigon; kiểm runtime bắt đầu17/11. Phạm vi: rà quyền ứng dụng đã được ủy quyền, chưa sửa ứng dụng/quyền/dữ liệu. Audit và prompt mới; cập nhật status/roadmap/index prompt đúng scope.
- Main18069 ledger0/0; PCserver/public1/1 hiệu lực, actor có hồ sơ TADIC, capability delegated và scope xác định. HR20.0.1.12.0/delegation20.0.1.0.1/attendance20.0.1.2.0 hai nơi. Không lấy trạng thái lịch sử0/0 để nói chưa cấp người thật. Chi tiết danh tính nằm riêng ignored.local.
- Kiểm thực: RPC chỉ đọc module/ledger; DockerOdoo shell SET TRANSACTION READ ONLY +with_user thật và rollback. Delegate HRoverview/Khodashboard/summary/proposal bị chặn, main HR/Kho thành công. Reportingmain cũng lỗi document,delegate lỗiobligation; tách baseline admin. HRget_view thành công chưa là browserrender.27tệp delegation/helper khớp máy chủ sau chuẩn hóa xuống dòng.
- Nguồn xác nhận Project/CRM CUD, Reporting workflow/aggregate và Kho stock/quick-action còn thiếu so yêu cầu. Không coi nativehas_access là toàn bộ quyền wizard. Prompt002 hoàn thiện scopedadapter, nguyên tử đổi máy, ownbaseline/privacy/thu hồi; giữ main-only security/role/reviewerassignment. Chỉ thị push/deploy ngay, không bắt18079 vẫn áp dụng.
- Không grant/revoke/seed/CRUD phá dữ liệu, không clone/test18079 hoặc chạy fixturemain/server. Chưa browserHTTP actor thật, chưa thửwrite/revoke/multiworker. Subagent không khởi tạo do modelruntime; không gọi audit độc lập nhiều người. Prompt không phải code đã sửa.
- Kiểm tài liệu: link tương đối, diffcheck và source trước/sau; workflowseal chỉ snapshotGit của batchdocs, không nhận foreignReporting/branding/login/sidebar/docs đã kiểm. Commit/push/sync đúng blob tài liệu, không restart/upgradeOdoo. Next: giao CLAUDE_ADMIN_DELEGATE_002_COMPLETE_SCOPED_ADMIN.md để triển khai từng miền và ghi evidence thật.

## CHG-20261117-024 — HR-ATTENDANCE-001: giao S4 lên server và chốt bàn giao

- Ngày 17/11/2026. S4 `cc2bfcb60ee361931eb7a3748291004d3d560dca` đã push origin/main, deploy 37/37 tệp đúng SHA256 lên PC server; addon 20.0.1.2.0 trên cả 18069 và server, nâng cấp `-u` exit0/0ERROR. S3 `14eaf388` đã giao trước đó. Không nhập lại nguồn, cấp quyền, gửi/duyệt/chốt thật, mở 18079/clone hoặc restart tunnel.
- Backup server `C:/TANPHAT-backups/hr-attendance001/s4-20261117T221550`: dump 9.566.430B, filestore 32.030.902B, source 145.967B, config/restore-list/SHA256. Backup local cuối22:04:59: dump 9.931.764B, filestore 424.824.655B; thêm nguồn S3 đã push để hoàn nguyên. Server snapshot chỉ đổi moduleversion; nhân viên39/tài khoản29/ngày công252/phiên182 và hash roster/nhóm/baseURL giữ, mount filestore và service đúng. Local nhân viên39/tài khoản28/nhóm101/phòng13/ngày252/phiên182 giữ.
- Kiểm thực: 19 ca Python không DB, JS dashboard, Ruff, AST19/XML9 đạt; ORM chỉ đọc 61/61 mỗi môi trường. Browser main:40 dashboard+10 danh bạ/HR; public:40 dashboard+12 danh bạ/health, 20 avatar thật và CSS/JS/fonts tải, không lỗi console/JS/5xx. Public lượt đầu timeout chờ load, retry chờ DOM/element đạt. Viewport375/390/768/1366/1440, CSS zoom200%, bàn phím/focus/reduced-motion, form/back/filter/count/pager/empty/future đạt; không nhận CSS zoom là zoom trình duyệt hay thiết bị thật.
- Guide/policy/acceptance/filter inventory/runbook cập nhật. ORM fixture S3/S4, phiên browser nhân viên/xuất CSV, hộp duyệt/chốt có dữ liệu, certificate, multiworker, SW và restore vẫn NOT_RUN. Quy tắc công/người duyệt chưa được HR xác nhận; không tự chọn người thật. Ảnh và log dữ liệu thật giữ trong ignored .local. Nghiệm thu nghiệp vụ/pilot riêng.
- Resume checkpoint bàn giao S4; checker nguyên bản chạy trên snapshot index sạch để seal commit. Workspace vẫn có foreign Reporting/branding/login/sidebar/docs, không stage hoặc nhận đã kiểm các phần đó. Lần seal023 trước commit phát hiện roadmap còn nhãn pending; sửa đúng trạng thái, dùng ID024 mới theo checker. Next: người dùng xem public và HR xác nhận ca/quy tắc/phân công; các kiểm chưa chạy xem acceptance.

## CHG-20261117-022 — HR-ATTENDANCE-001 S4: tổng quan công, mobile và bảo vệ xuất/riêng tư

- Ngày17/11/2026. Tiếp tục checkpoint14:17:53Z đúng attendance, không chiếm batch khác. S3 `14eaf388` đã push/áp server31/31tệp20.0.1.1.0,backup s3-20261117T211705,public7/7. S4 manifest20.0.1.2.0 thêm dashboard `/app/cham-cong`,5KPI/donut300px/cột340px,detail ngày-người/pager10/20/50/100/thẻmobile. Chart và KPI giữ phạm vi tháng/phòng/tên-mã; nhóm không chồng, loại tương lai, chưa quy tắc hiện Chưa xác nhận.
- Filter draft tách applied; chip xóa từng điều kiện, clear giữcompany/backend; staleRPC không đè kết quả mới, namedhandler tránh lỗiOWL returnctx. CSV own BOM/whitelist/session theo tháng/chất lượng/chốt, formula guard, không attachment; native day/session export own cũng chặn nestedfield. Directory: chặn proxy employee export bypass; mobile/phone/email riêng và companionfields có HR groups trên cả employee/public, compute workphone tách riêng; resume/certificate native20 global ir.access restriction owner/HR. Nativeuser/resource IDs và kỹ năng công việc giữ để nativeconsumers hoạt động.
- Main backup S4 đầu21:44:31 dump9.928.226B/filestore413.396.968B; cuối22:04:59 dump9.931.764B/filestore424.824.655B/source-config/restore-list/SHA256. Hardening lần đầu dùng ir.rule không tồn tại bị rollback; sửa sang ir.access, retry `-u` cuối exit0/0ERROR. Snapshot39employee/28user/101grouprel/13dept/252day/182session/baseURL giữ, nativeAttendance uninstalled. Không grant/người/công/phiếu/kỳ giả hoặc thật mới.
- Kiểm thực:19Python noDB (14guard+5metricsCSV),JS regression,Ruff,AST19Python/XML9 PASS; readonlyORM uid41/42+admin61/61 (field metadata/read/domain/order/export/workphone-avatar/selfprofile/forgedownCSV/partition); resume chỉ kiểm hiện có/empty, không nhận filledcertificate. Browser40/40 sauprivacy:filterAND/chip/apply/clear/pager/state/date-lock/count/chart/empty/future/dayform-back/5viewport375/390/768/1366/1440/keyboard/focus/reducedmedia/CSSzoom200,0JSerror. `.local/hr-attendance001/e2e/s4-final-after-privacy` giữ ảnh thật ignored.
- ORMfixture AT02-C/03-C/06A-D và regressionprivacy/ownCSV đã viết nhưng NOT_RUN theo chỉ thị không18079/fixturemain; không nhận fullworkflow/race/UAT. Chưa có credentialemployee browser, reviewer/rule được chọn, filleddialog/kỳchốt/certificate, thiết bị/zoomnative, restore rehearsal. Acceptance/policy/guide/filterinventory/runbook cập nhật; không tự chọn người thật, không publicprivatefile. Foreigndiff giữunstaged; workflowseal chỉ cleanindex scope, không auditforeign. Next push/deploy exactS4 rồi kiểmpublic và ghi kết quả môi trường.


## CHG-20261117-021 — HR-ATTENDANCE-001 S3: công cá nhân và xử lý điều chỉnh

- Ngày17/11/2026; tiếp tục checkpoint attendance11:07:17Z, không reset/chiếm checkpoint khác. S1/S2 runtime/source đã xác minh. Hoàn tất UI native/list/search/form/wizard/menu và OWL Công của tôi/profile tab, bộ lọc/ngày/tháng/thẻmobile/pager. Manifest20.0.1.1.0.
- Backend: own mapping session/company; write/state/owner guards, current assignment/revoke, no self-review, row/company lock + pending unique index; duyệt giữ phiên gốc, audit không chứa giải trình/minh chứng, lock/unlock/amendment lý do/version. Tệp minh chứng không public/token/reparent và chỉ owner sửa nháp/trả. Kỳ đã chốt không tính lại do thay quy tắc. Export officers kiểm capability/scope thay vì chỉ group.
- Main backup210850 (dump9.927.107B,filestore409.988.594B,source/config), upgrade -u exit0/0ERROR,39employee/28user/101grouprel/252day/182session giữ;0assignment/phiếu/kỳ, không phân công hoặc chốt thật. XML/Python/Ruff PASS;14test guard không DB PASS; browser16/16 gồm admin màn không mapping/list/form chưa lưu/kỳ và render riêng bằng ORM employee payload ở5viewport; không gọi render đó là employee E2E. Native dialogs approve/lock chưa thử với phiếu thật.
- Odoo regression6ca AT02-C/03-C/06A-D đã viết nhưng NOT_RUN: người dùng cấm fixture trên main/server và không mở18079/clone. Giữ gap legacy privacy native-public và employee browser/race multiworker. Script deploy mới kiểm drift trước ghi và upgrade bằng -u, backupDB/filestore/source/config; server/public sẽ ghi khi chạy thật. Không sửa API/core/roster hoặc đưaPII/secret vàoGit. S4 tiếp theo. Guide/policy/acceptance/inventory cập nhật; không stage foreign batch.


## CHG-20261117-008 — VI-WEB-002: xác nhận bản cuối trên18069/PCserver/public

- Ngày17/11/2026. Source35e1c11f +73ffae56 đã pushorigin/main;đúng3addon trên18069/PCserver:delegation20.0.1.0.1,HR20.0.1.11.6,i18n20.0.1.1.1. Góiđầu90 vàdelta11tệp,union92tệp SHA256đúngcommit. Khôngbroadpull/copyworkingtreeforeign;Reporting/branding/login/sidebar vàhunkdocs khác giữunstaged. Tài liệu008 chỉ đồng bộsource,khôngrestart thêm.
- Delta dashboard upgrade0/0ERROR saubackup C:/TANPHAT-backups/vi-web002/20261117T170450:dump9.341.539B,filestore28.564.607B,source/config4.477.936B,mục lục pg_restore vàSHA256. Bảnbackupđầu164626 vẫn giữ. KhôngrollbackDB/đổiDNS/tunnel. Logs runtime saurestart0ERROR/0FileNotFoundError.
- Publiccuối:35/35 ở1440/768/390/320,đúnghồsơ35;dialog mở được,blankreasonbị chặn,ảnhdecode/giớihạn/khôngJSON/hash/khôngoverflow,Escđóng. Lịchcả2nhãnTuần47,SettingshướngdẫnBarcodeViệt;dashboardtiêuđề/cộtViệt. API dashboardmẫu200/namespaceđúng/23ôliteralđược dịch;mọigiátrịsnapshotkhác giữnguyênsofileupstream,anonymous303.14routeđãrà gồm13màn tải vàReportingtừchối doadminserver thiếunhóm cótrước;khônggrantđểtest.
- Catalog10.494/native/en_US/placeholders/idempotence và12tổhợp dashboard+denial checker khôngDB PASS;Ruff/XML/locale/2177XMLID-source/rollback backend đạt.20fingerprintbảng localgiữ;serverngaysaucả2lầncài giữ20bảng/baseURL/ledger0/0,cuốikhôngđổiuser/group/nghiệpvụ;cronởmốcđầutựtiếnlịch. KhôngfixtureOdoo/18079/clone/grant/sync thật;test mới chỉ lưu source,khôngnhậnUAT/auditđộclập.
- Filestorecuối666storedrows/169blobđủđúnghash;media83/83origin/public. ExcelHR200/9749B/2sheet/MIMEđúng;PDFnhãn200/29028B/header+EOFđúng;no-store,anonymous303. KhôngcóattachmentPDF/Word/Excelthậtđểkiểmbađịnhdạnglưusẵn,khônguploadgiả/mởprivate. Nguyênnhânảnhcũ là149blobthiếuvậtlýđãphụchồi,khôngdoACL.
- Giớihạn:cònthuậtngữ/nộidungmẫu hoặcnhậptay vàluồngchuyênsâu chưađihết;vídụgiátrịmẫu379days/NotPaidkhôngphảinhãntrongcatalog,côngthức/số/tênngườigiữ. Reportingpublicthiếunhóm làbaseline,chưađượccấpthử. QuyềnủyquyềnchưađủCRUDmọimodel/multiworker vàbusinessacceptance/pilot vẫnriêng;khôngđónggapbằngsửadialog. Xemacceptance/coveragechoNextaction.

## CHG-20261117-007 — VI-WEB-002: giao server và sửa bản dịch dashboard mẫu

- Ngày17/11/2026.35e1c11f push origin/main và deploy90/90tệp đúng checksum. PCserver backup C:/TANPHAT-backups/vi-web002/20261117T164626:dump9.293.131B/filestore30.188.646B/source-config4.076.825B/pg_restore-list/SHA256;3addon upgradeexit0/0ERROR. Wrapper đầu từ chối định dạng đường dẫn mount Windows trước mutation; đã kiểm mount thật, sửa validator và triển khai. Không đụng tunnel/DNS.
- Public hồ sơ35:35/35 ở1440/768/390/320.14route kiểm:13màn tải được, Reporting từ chối vì admin server thiếu nhómBáo cáo có trước (groups hash giữ);không tựgrant đểsmoke.0JSerror/overflow;Lịch/Bảng tổng hợp lượt đầu chụp lúc tải lạnh nên đã chờ renderer và kiểm lại, không tính ảnh loading là màn đạt. Backend2177refs vàrollback lý do/digest PASS;90sourcefile chuẩn.20bảng ngay saucài/baseURL/ledger0/0 giữ;cuối chỉcron tựtiến,0runtimeERROR/FileNotFoundError.
- Media kiểm lại83/83 origin/public;666storedrows/169blob,0thiếu/khác. ExcelHR HTTPS200/9749B/MIMEđúng/2sheet;PDFnhãn200/29028B/header+EOFđúng;no-store,anonymous303. Không có PDF/DOCX/XLSXattachment thật nên chưa kiểm tệp lưu sẵn ba loại, không upload giả/mởprivate. Kết quả này kế thừa nguyên nhân149blob thiếu vật lý đã phục hồi ởDEPLOY-MEDIA-001.
- Dashboardmẫu native trảsnapshot mà thiếutranslation_namespace nên không dùng catalog;nhãn ô tĩnh không có công thức_t. tp_i18n_vi20.0.1.1.1 kế thừa route, giữnative auth/readonly/denial, bổ sungnamespace và dịch ôliteral có đúng source trong catalog module. Không sửaDB/công thức/số/tên công ty ngoàicatalog/phản hồi en_US/dashboardthật. Checker12tổhợp vi/vi_VN/en_US×sample/thật×namespace +denial PASS;Ruff/catalog/locale đạt;áp18069 saubackupđãcó,upgrade0ERROR. DeltaPCserver chờcommit/push/deploy sau mốc này.
- Không suitefixture18079/main/server;không cấp/người thật/đối chiếu thật. Việt hóa hơn6.500nguồn bổ sung có kiểm định dạng/ràmẫu, chưa nghiệmthu mọi từ/ngữ cảnh/role. GapCRUD/multiworker củaủyquyền không bịđóng bởiUI. ForeignReporting/branding/login/sidebar giữunstaged.

## CHG-20261117-006 — VI-WEB-002: sửa hộp Lý do, đối chiếu danh tính và mở rộng tiếng Việt native

- Ngày17/11/2026. Tiếp tục yêu cầu tại public `/app/action-528/35` và ảnh người dùng. Wizard grant/revoke và edit/archive được precreate trước khi nhập lý do; bỏ required ở transient, giữ required native form và kiểm backend cả chuỗi trống/khoảng trắng trước mutation. Không thay quyền/cấp người thật.
- Đối chiếu danh tính: dialog vừa màn hình, thumbnail128px, nhãn hồ sơ/tài khoản, kết quả tiếng Việt thay JSON/hash; đồng bộ vẫn dùng ảnh gốc/digest/lock, audit giữ trước/sau. Không xác nhận đồng bộ thật.
- tp_i18n_vi20.0.1.1.0:5.247overlay+5.243namespace (6.694nguồn khác nhau),4thông báo server; hook cache native giữ bản Việt/en_US, locale FullCalendar bổ sung nhãn tuần dài. Nguồn dịch tự động chỉ UI upstream công khai, không DB/credential/hồ sơ; kiểm định dạng/rà mẫu, chưa nghiệm thu thuật ngữ/toàn bộ luồng. Không sửa core/DOM/React/ACL.
- Main18069 đã áp3addon sau backup `.local/admin-delegate001/backup-dev-vi-web002/` (dump9.646.950byte/filestore254.446.424byte/checksum). Upgrade exit0/0ERROR; checker10.494mục/Ruff/XML/locale PASS;2.177XMLID/source match; backend rollback lý do trống PASS. Browser35/35 ở1440/768/390/320 và14màn không lỗi;20bảng/baseURL/ledger0/0 giữ. Không suite fixture trên main/server hoặc18079/clone; test Odoo mới chưa chạy. Subagent không khởi tạo do modelruntime, không audit độc lập.
- PCserver chưa áp trong mốc006: source16file cũ đúng Git baseline,66file addon mới không xung đột; chuẩn bị gói commit để push/deploy, bổ sung kết quả server sau. Foreign Reporting/login/branding/sidebar/status giữ riêng. [Acceptance](demo/VI_WEB_002_ACCEPTANCE.md) ghi nguyên nhân, kiểm thực, rollback và gap. Không đóng các gap CRUD/multiworker của ADMIN-DELEGATE-001 bằng sửa dialog.

## CHG-20261117-005 — ADMIN-DELEGATE-001: push và áp PC server, kiểm public và bàn giao giới hạn

- Ngày 17/11/2026 (Asia/Saigon). Commit chức năng cffa70d6 đã push origin/main. Deploy đúng delta của task; 44 tệp khớp checksum. Home giữ 2 thay đổi branding có trước đã đối chiếu, không đưa foreign Reporting/login/branding vào commit. Server dùng Reporting Git hiện hành và cài dependency 20.0.1.1.0; tp_admin_delegation 20.0.1.0.0 cài exit0/0ERROR.
- Backup server mới C:/TANPHAT-backups/admin-delegate001/20261117T151401: dump8.955.792byte, filestore29.714.074byte, source/config3.565.619byte, pg_restore-list và SHA256. Local backup-dev-resume: dump9.601.550byte, filestore/code/config/checksum. Không restore test đè main; rollback chưa diễn tập.
- Wrapper PowerShell dừng do native stderr warning từ Docker; tiến trình upgrade vẫn chạy, docker wait trả0, log kết thúc thành công rồi mới start tp-odoo. Không restart tunnel/DNS hoặc mở private file. Hai lần public browser timeout khi dựng asset lạnh; lượt sau 4/4, không lỗi trang. Main4/4, HOOT48/48/243 assertions; R11/focused/regression/race phiên trước giữ đúng snapshot.
- So ngay sau cài: 20 bảng local và 18 bảng server giữ fingerprint; chỉ thêm hai module/schema dependency, ledger0/0. Cuối lượt user/group/nghiệp vụ vẫn giữ, cron server30dòng chỉ tự tiến lịch. Probe localhost từng đổi baseURL local; đã xác thực lại đúng127.0.0.1 và đối chiếu khôi phục hash cũ. Server baseURL hash giữ nguyên.
- Media sau deploy:83/83 origin/public;666stored rows/169blob,0thiếu/khác. Tệp xuất từ dữ liệu hiện hữu chỉ đọc: Excel HR HTTP200/9747byte/MIMEđúng, đọc2sheet; PDF nhãn HTTP200/29028byte/MIMEđúng, pdfjs xem1trang; no-store và anonymous303. Đây là export thực, không phải attachment lưu sẵn. Server không có PDF/DOCX/XLSX attachment thật; Word chưa kiểm public bằng mẫu thật, fixture test lịch sử giữ riêng. Không tạo hồ sơ/tài khoản/tài liệu giả ở main/server.
- Giới hạn triển khai: fullCRUD phòng khác chưa đủ (project/task/CRM CUD; Reporting aggregate/value/snapshot/CUD; nhiều workflow Kho/HR); multiworker và browser delegate HR bản cuối chưa kiểm. Actor test giả cũ vẫn ở DBtest, không chạm theo chỉ thị mới. Chưa cấp ai, chưa business acceptance/pilot. Acceptance/policy/coverage/user guide/runbook đã cập nhật; tiếp tục đóng gap trước khi gọi toàn phạm vi hoàn tất.
- Workflow: checkpoint tiếp tục từ lượt đóng gói; finish004 đã đạt trước sửa docs đóng gói, lần cố dùng lại004 bị checker từ chối. Bàn giao mới005 ghi đúng deploy và niêm phong lại, không coi lỗi checker là lỗi cài ứng dụng.

## CHG-20261117-004 — ADMIN-DELEGATE-001: giao quyền quản trị có giới hạn, tiếp tục phiên trước

- Ngày17/11/2026 (Asia/Saigon). Người dùng giao thực thi18069, push và deployPCserver; tiếp tục checkpoint06:07:04Z. Addon tp_admin_delegation20.0.1.0.0: ledger cấp/thu main-only, reason/re-auth native, giữ quyền nghiệp vụ phòng mình, scope theo nguồn/đa phòng; chặn self/identity/group/grant/import, thu hồi theo request/transaction; adapter HR/account, contract/project/CRM/report read và Kho trong coverage. Không cấp nhóm system/HR hoặc chọn người thật.
- 18069 cài exit0/0ERROR sau backup .local/admin-delegate001/backup-dev-resume/ (DB9.601.550byte +924filestore entries/code/config/checksum).20fingerprint bảng giữ nguyên, baseURL giữ, ledger0/0. Browseradmin4/4, HOOT48/48/243assertions; Python/XML/Ruff đạt. Probe ban đầu chọn employee admin không tồn tại nên mởlist; đã sửa probe chỉ đọc, chạy lại đạt.
- Evidence phiên trước: R11security35/35, focusedHR safe view1/1 cùng hash source cuối, regression77/77; race23/23+7/7. Không chạy thêm18079/fixture main-server. Source khácR11 chỉ3fileHR đã có focused test. Subagent review không khởi tạo được do modelruntime; review cùng phiên, không audit độc lập.
- Media đã push riêng f14bc49b: thiếu149blob tại mount thật, phục hồi add-only đúng checksum/size. Kiểm lại83/83origin/public; server665stored rows/168blob,0thiếu/khác; local661/169,0thiếu/khác. PDF/Word/Excel không có mẫu thật trênserver; giữ test lịch sử riêng, không mở private thànhpublic.
- Gói source chỉ gồm hunk/task; brandingURL có sẵn trênserver được đối chiếu và giữ nguyên. ForeignReporting/UI-login/branding giữ unstaged.
- Giới hạn: chưa fullCRUD mọi model/phòng khác; project/task/CRM CUD, reporting aggregate/value/snapshot và nhiều workflow vẫn baseline. Multiworker, browserdelegate HR cuối và nhiều caAD chưa kiểm; xem acceptance/coverage. Actor giả còn ởDBtest từ phiêntrước, lượt này không chạmDBtest. Serverrelease đang chuẩn bị; cập nhật deploy thực ở bàn giao kế tiếp.

## CHG-20261116-009 — BRAND-LOGO-001: logo công ty thay hình cây cầu trên toàn hệ thống

- Ngày 16/11/2026 (Asia/Saigon). Theo yêu cầu trực tiếp của người dùng: dùng `logo/logo.png` làm logo toàn hệ thống, cân đối, rõ ràng, thay hình cây cầu. Áp main `18069` sau backup `.local/brand-logo/backup-pre-logo/`; không commit/push.
- Asset local mới `tp_web_home/static/img/brand/`: `tp_logo_mark.png` (biểu tượng 512×512, nền trong suốt, căn giữa quang học), `tp_logo_full.png` (logo đầy đủ 900×885), `favicon.ico` (16/32/48/64), `tp_logo_touch.png` (180×180 nền trắng). Màu thương hiệu giữ nguyên `#0092DD`, tách khỏi nền trắng của ảnh gốc.
- `tp_web_home` `20.0.1.8.0 → 20.0.1.9.0`: navbar thay SVG cầu bằng logo trên ô trắng bo góc 32px (mobile 28px) để logo xanh rõ trên nền navy; giữ wordmark `TANPHAT ONE` / `TP ONE`. Template thêm favicon (`web.layout`, vẫn ưu tiên `x_icon` riêng), apple-touch-icon và theme-color `#061b40`.
- `tp_web_login` `20.0.1.4.2 → 20.0.1.5.0`: ô logo 48px (mobile 34px) cạnh wordmark; hình cầu thay bằng thẻ trắng chứa logo đầy đủ, ẩn trên mobile như trước. Giữ class `tp-native-wordmark`, form, CSRF, passkey; logo công ty native vẫn ẩn trên trang auth.
- Dữ liệu: `res.company` [1] `logo` = logo đầy đủ qua RPC admin (`uses_default_logo` = False). Đối chiếu DB trước/sau: chỉ đổi phiên bản 2 module, `ir_ui_view` +1 (`layout_brand_favicon`) và ảnh partner công ty; các bảng user/partner/HR/thiết bị/menu/attachment giữ nguyên số lượng.
- Kiểm thực: XML parse, manifest, `git diff --check`; `-u tp_web_home,tp_web_login` exit 0, 0 ERROR; Playwright trên 18069 đạt 6/6 (login 1440/390, asset 200 đúng kiểu, `/web/binary/company_logo`, navbar Home/TP HR 1440, Home 390; không tràn ngang, 0 lỗi console/page); kiểm lại các assertion của `test_native_login` trên HTML live đạt. Chưa chạy bộ test Odoo/HOOT. Giới hạn: icon PWA manifest và tiêu đề tab mặc định `Odoo` chưa đổi.
- Sự cố vận hành: khi khởi động lại có một Odoo 18069 do phiên khác chạy, không có pid file. Phiên này đã dừng tiến trình đó; PostgreSQL 55432 dừng theo và tự crash-recovery (redo xong, sẵn sàng 15:20:08), sau đó khởi động lại Odoo. Workflow: checkpoint đang mở thuộc batch CORP-REPORT-001 (CHG-008), nên không `finish` hộ. `Last change` giữ mốc đã finish; batch giữ checkpoint tích hợp mục này vào lần bàn giao tiếp.

## CHG-20261116-008 — CORP-REPORT-001: triển khai native và báo cáo cá nhân trên web

- Ngày16/11/2026 (Asia/Saigon). Theo prompt full R0–R5 và addendum trực tiếp, tiếp tục cùng checkpoint sau baseline CHG-007 PASS; boundary source/hash/diff trước sửa được giữ private. Đang triển khai và kiểm thực `tp_reporting` trên canonical `tp_tanphat_test`/18079, PostgreSQL55432; main18069 chưa áp, không commit/push, không nhập Word/Excel thật hoặc đổi tài khoản/grant người thật.
- Addon mới: cây quý→tháng→tuần, baseline/revision, báo cáo cá nhân/phòng/công ty với exact snapshots/dependencies; soạn/xem trước/gửi/nhận xét từng đầu việc/phản hồi/trả/sửa/gửi lại/chốt; rollup theo ngày/chống trùng, carry-forward cùng nguồn; finance nhập/đọc/xác nhận tách quyền; nghĩa vụ/mẫu/lịch/thông báo trong ứng dụng/chỉ đạo. Dashboard chart lớn, native SearchModel/filter/pager, list/detail/mobile/hover/reduced-motion và xuất Excel/Word/PDF. Yêu cầu sidebar đồng bộ module hiện có được tiếp nhận trong cùng batch.
- Kiểm thực đến thời điểm cập nhật: install/upgrade test; Odoo27ca đạt trong `tests8.log`; HTTP32kiểm đạt, gồm hai request gửi cùng mã trả True/False đúng một snapshot;50tổ hợp route×viewport không tràn ngang; Excel/DOCX/PDF readback và PDF render đạt. Word visual render chưa chạy được vì không có LibreOffice. Browser full workflow và lượt tests cuối vẫn đang làm; chưa chứng nhận full R0–R5 hay nghiệm thu nghiệp vụ.
- Backup/restore rehearsal canonical test:601bảng fingerprint và561blob đã lưu khớp,100.78giây, không tạoDBtask. Kết quả/evidence ở `.local/corp-report001/`; runbook chuẩn bị main/rollback riêng, chỉ áp khi có chỉ thị triển khai. Tài liệu status/acceptance/schema/UI/guide/inventory được cập nhật cùng batch; workflow finish chỉ sau ổn định source và kiểm boundary.

## CHG-20261116-007 — EQUIP-SIMPLE-003: nút lọc nhanh Máy in (gồm Máy in + Máy photocopy) trên danh sách Thiết bị

- Ngày: 16/11/2026 (Asia/Saigon). Theo yêu cầu trực tiếp của người dùng (cho phép sửa code và áp trực tiếp main `18069` trong phiên này), bổ sung nút lọc nhanh **Máy in** trên hàng bộ lọc của màn **Thiết bị** (`/odoo/kho-thiet-bi`).
- Backup trước thay đổi tại `.local/equip-simple003-printer/backup-pre-printer/` (dump `9.285.317` bytes, filestore `883` tệp, source `tp_equipment` `20.0.1.5.0` `65` tệp, `manifest.json`). Nâng cấp `tp_equipment` **20.0.1.5.0 → 20.0.1.5.1** qua `-u tp_equipment --no-http --stop-after-init` (exit `0`, `0 ERROR` tại `.local/equip-simple003-printer/upgrade.log`). Không commit/push.
- Source:
  - `custom_addons/tp_equipment/views/equipment_views.xml`: thêm `<filter name="q_printer_copier" string="Máy in" domain="[('category_id.tp_code', 'in', ('MI', 'PT'))]"/>` trong `equipment_search` (5 `Máy in` + 4 `Máy photocopy` = 9 thiết bị).
  - `custom_addons/tp_equipment/static/src/table/compact_filter_bar.js` và `.xml`: thêm nút bật/tắt nhanh **Máy in** cạnh `Phòng ban` / `Loại thiết bị` / `Bộ lọc` (chỉ trên profile `equipment_main`), điều khiển `SearchModel` (`toggleSearchItem`), không cộng nhầm vào `drawerBadgeCount` của nút `Bộ lọc`, đồng bộ chip `Máy in ×` và `Xóa lọc`.
  - `custom_addons/tp_equipment/static/src/table/table.js`: loại `q_printer_copier` khỏi danh sách quick filter drawer của `equipment_users` / `equipment_shared` để giữ nguyên hai profile cũ.
  - `custom_addons/tp_equipment/static/src/table/table.scss`: style `.tp_eq_cf_quick_toggle` đồng bộ `.tp_eq_cf_drawer_btn`, nút `44px` trên mobile và tắt transition theo `prefers-reduced-motion` / `.o_tp_eq_reduce_motion`.
  - Cập nhật `docs/ui/TP_TABLE_FILTER_INVENTORY.md` (`EQ-M00`), `docs/demo/EQUIP_001_USER_GUIDE.md`, `ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md`, `docs/PROJECT_STATUS.md`.
- Kiểm tra thực chạy: `lxml` XML (2 tệp), `node --check` (2 JS), `git diff --check` đạt; `-u tp_equipment` exit `0`; Playwright `.local/equip-simple003-printer/verify_printer_filter.mjs` trên `18069`: `Tất cả` + `Máy in` = `9 kết quả` (`TB-00014`..`TB-00022`), `Đang sử dụng` + `Máy in` = `1 kết quả`, `Trong kho` + `Máy in` = `0 kết quả`, ghép `Ban Giám đốc` + `Máy in` = `1 kết quả`, mở chi tiết + `← Quay lại` giữ lọc, `Xóa lọc` về `54 kết quả`, `/tp_equipment/export.xlsx` HTTP `200`, `1366×768` và `390×844` không tràn ngang (nút `44px`), lượt kiểm sau warm-up `0` console/page/server error (lượt đầu sau restart có 1 lỗi 500 Windows filestore bundle rename như đã biết trong runbook). Đối chiếu DB `baseline-after.json` vs `baseline-before.json`: `TOP_DIFFS: ['modules']` (`tp_equipment` `20.0.1.5.1`), 18 bảng dữ liệu giữ nguyên. Ghi chú quy trình: `ai_workflow.py start` ban đầu chạy lúc `13:46+07:00` trước khi sửa, sau đó checkpoint được `CHG-20261116-005` chốt song song lúc `06:48Z` nên đã chạy lại `start` và chốt `finish` cho `CHG-20261116-007`.
- Next: người dùng Ctrl+F5 tại [Thiết bị](http://127.0.0.1:18069/odoo/kho-thiet-bi) và dùng nút **Máy in** trên thanh lọc; luồng Gán / Đổi máy / Trả kho thật và 9 dòng nguồn chờ vẫn theo `CHG-20261116-003`.

## CHG-20261116-006 — CORP-REPORT-001: prompt full module, dashboard và UI mọi tab

- Ngày: 16/11/2026 (Asia/Saigon). Người dùng yêu cầu prompt triển khai đầy đủ Báo cáo, nhấn mạnh giao diện đẹp/sáng, chart lớn rõ, animation/hover, bảng không chồng và filter từng nội dung, đồng bộ một DB với toàn hệ thống; cho phép bổ sung tính năng hữu ích. Phiên này tiếp tục điều phối, chỉ sửa tài liệu; không code/runtime/DB/user/grant/commit/push.
- Tạo `docs/prompts/CLAUDE_CORP_REPORT_001_FULL_MODULE.md`: R0–R5 đến hoàn tất, quý→tháng→tuần, tổng hợp ngược, snapshot/version/baseline, quyền theo scope/nguồn/field/file/export, tiền có nguồn-xác nhận, chỉ đạo, cấu hình mẫu/lịch và Excel/Word/PDF. Có wireframe/token/kích thước chart, đặc tả từng tab/list/detail/popup/mobile, ma trận bộ lọc và acceptance trước code. Thông tin lịch/thẩm quyền còn thiếu làm cấu hình/role test, không tự cấp người thật. Chỉ triển khai test18079, chuẩn bị main nhưng chưa áp; ngoại lệ EQUIP không mở rộng.
- Cập nhật thiết kế, DEC-048 đúng yêu cầu mới của người dùng, ROADMAP, PROJECT_STATUS và danh mục prompt. Không thay policy quyền/thẩm quyền thật bằng default kỹ thuật.
- Kiểm thực: 7 docs UTF-8/fence hợp lệ, prompt 16 mục (0–15), 11 link mới/design có đích, ID CHG-006 duy nhất; coverage R0–R5 và 11 nhóm AT có mặt. `git diff --check` exit 0. Snapshot maintained code của workflow giữ nguyên 514 file/digest `9add1579…5fa2bb` so boundary đầu lượt; state JSON không đổi, không tạo checkpoint. Kết quả private `.local/reporting001/prompt_full006_validation.json`. Đây là kiểm tài liệu, chưa phải test module Báo cáo.
- Baseline: checker trước/sau vẫn FAIL do application/tooling source đã đổi sau CHG-20261116-005, không có active checkpoint lúc đầu; main18069/PG55432 đang listen, test18079 chưa listen. Lưu source/doc/state boundary private `.local/reporting001/prompt_full006_boundary_before.json`; không start/finish hộ batch code chưa kiểm, không sửa `AI_WORKFLOW_STATE.json`. Không chạy app test cho sửa tài liệu; không xác nhận audit độc lập.
- Next: Claude đối chiếu source/batch hiện hành rồi thực thi prompt full trên canonical test; kiểm thử/ảnh/handoff theo từng slice đến R5. Main deployment và nghiệm thu Kho vẫn tách riêng.

## CHG-20261116-005 — CORP-REPORT-001: mục tiêu quý phân rã tháng-tuần trước báo cáo kết quả

- Ngày: 16/11/2026 (Asia/Saigon). Người dùng chốt thứ tự đề ra mục tiêu quý → chia tháng → chia tuần. Chỉ điều phối/thiết kế; không code/DB/runtime/quyền, không commit/push.
- Cập nhật `TP_COMPANY_REPORTING_001_DESIGN.md`, DEC-048, PROJECT_STATUS và ROADMAP: kế hoạch đi xuống, kết quả đi lên; liên kết cha-con và task/HR dùng chung, phân công theo phòng/cá nhân độc lập loại kỳ; chỉ tiêu/đầu ra/hạn, đối chiếu phân bổ, baseline và revision. Không tự chia đều, ép phần trăm, hồi tố mục tiêu để đạt hoặc cộng trùng việc phát sinh/chuyển kỳ/tuần giao tháng. Bổ sung cây Mục tiêu và kế hoạch, ca nghiệm thu và đầu vào cần chốt.
- Đổi lộ trình hiện hành R0–R5: R1 mục tiêu/phân rã trước R2 cá nhân, R3 phòng, R4 công ty, R5 mở rộng. Các nội dung lịch sử R0–R4 ở CHG-004 giữ là kế hoạch trước bổ sung; chỉ đạo mới và tài liệu thiết kế là hiện hành.
- Kiểm thực: baseline workflow CHG-004 PASS, start trước sửa docs; 5 docs UTF-8/fence/link, 13 mục, lộ trình R0–R5 có kế hoạch trước báo cáo, 14 ca nghiệm thu và CHG không trùng đều đạt; `git diff --check` đạt; digest code `db10badc…be567`, 514 file khớp checkpoint. Workflow finish/check ghi cuối lượt. Không chạy app/Odoo/browser vì chỉ thiết kế; không sửa nguồn Word/Excel hoặc dữ liệu.
- Next: chốt chỉ tiêu/mốc quý và thẩm quyền giao/chốt/điều chỉnh, lịch nộp và quyền xem để đặc tả R0/R1; chưa mở code/grant/import/deploy. Nghiệm thu Kho vẫn riêng.

## CHG-20261116-004 — CORP-REPORT-001: phân tích mẫu Word và thiết kế báo cáo toàn công ty

- Ngày: 16/11/2026 (Asia/Saigon). Phiên điều phối chỉ phân tích/lập tài liệu. Đọc báo cáo tháng Phòng Thiết kế và SXKD 9 tháng do người dùng gửi; bản thứ hai là cấp công ty/HĐQT, có nhiều nguồn tài chính/nhân lực/điều hành, không gộp thành mẫu Thiết kế. Trích xuất và hash riêng tại `.local/reporting001/`, ignored; không đưa raw/tên/giá trị nguồn vào Git, không nhập Word vào DB.
- Người dùng chốt hai điểm trong chat: nhân viên nộp tuần, cá nhân có tháng/quý khi được yêu cầu, trưởng phòng tổng hợp/nộp tháng-quý; số tài chính thiếu được nhập tổng hợp kèm nguồn và xác nhận, chỉ người có quyền xem. Ghi DEC-048, chưa chốt lịch/người rà/chốt/tài khoản lãnh đạo cụ thể.
- Thêm `docs/architecture/TP_COMPANY_REPORTING_001_DESIGN.md`; cập nhật PROJECT_STATUS/ROADMAP/DECISIONS. Đề xuất core chung mọi phòng, mẫu đặc thù pilot Thiết kế/KH-KD, report cá nhân/trưởng phòng/phòng/công ty, live/phiên bản gửi/chốt, source và số thủ công, chống cộng trùng/overlap/kỳ/ước lượng, scope report/tiền/HR/file và chỉ đạo tiếp theo. Lộ trình R0–R4 và ca nghiệm thu; `tp_reporting` là đề xuất, chưa tạo addon/schema.
- Source đã đọc: KH-KD report_center/reporting/periodic_plan/review_document/scoped_task; project/assignment/HEAD; HR scope/role/transfer; dashboard privacy. Report center hiện có là TransientModel/6 nhóm KH-KD; periodic plan gắn dự án, không đáp ứng trọn báo cáo định kỳ cá nhân/phòng/công ty. Đây là source review, không audit runtime.
- Kiểm: baseline workflow CHG-20261116-003 PASS, start trước sửa docs; hai hash Word không đổi, OOXML 6 + 2 bảng, nguồn/analysis private ignored. 5 docs UTF-8/fence, 3 link thiết kế mới, 13 mục đặc tả, CHG/DEC không trùng, `git diff --check` đều đạt; digest source `db10badc…be567`, 514 file khớp checkpoint. Workflow finish/check ghi cuối lượt. Không chạy app/browser/Odoo hoặc thay code/runtime/DB/user/quyền/deploy; không commit/push. Ngoại lệ EQUIP main trực tiếp không mở rộng sang module mới; nghiệm thu luồng Kho vẫn riêng.
- Next: chốt thông tin mục 12 của thiết kế rồi viết prompt thực thi R0/R1; không tự giao code hay nhập tài chính thật.

## CHG-20261116-003 — EQUIP-SIMPLE-003: Kho gọn hai menu; Gán / Đổi máy / Trả về kho chỉ máy trong kho chưa có người giữ

- Ngày: 16/11/2026 (Asia/Saigon). Thực thi `docs/prompts/CLAUDE_EQUIP_SIMPLE_003.md` (DEC-047) kèm lưu ý CHG-20261116-002 của người dùng: chỉ gán/đổi sang máy trong kho, chưa có người giữ, kiểm cả giao diện và backend; backup trước, áp main 18069; không commit/push.
- Backup `.local/equip-simple003/backup-pre-simple003/` (dump 9.259.433 bytes, filestore 855 tệp, source `tp_equipment` 20.0.1.4.2 + `tp_web_home`, manifest sha256). `tp_equipment` **20.0.1.4.2 → 20.0.1.5.0** qua `-u` (exit 0, 0 ERROR); `tp_web_home` và module khác không đổi.
- Source: `models/quick_action.py` mới (TransientModel `tp.equipment.quick.action`, RPC `tp_quick_action` khóa/version/idempotency, `free_domain`, field tính toán trạng thái/nút); `move.py` (`tp_request_key`/`tp_request_hash`, guard gán/mượn máy stock còn người giữ, write guard); `proposal.py` (`need_type`, phòng ban từ HR); `common.py`, `equipment.py`, ACL `access_tp_equipment_quick_action_admin`; views `equipment_views.xml` (`equipment_main_list`, action chính), `quick_action_views.xml` mới, `menus.xml` (2 menu, 22 menu `active=False`), `proposal_views.xml`, `dashboard_views.xml`; static `table/*`, `main_list.scss` mới, `redirect.js` mới, `sidebar.js`, `back_fallbacks.js`, `home_card.js`.
- Tài liệu: README addon, hướng dẫn/acceptance Kho, schema/quyền, filter inventory, UI-BACK-001, runbook, PROJECT_STATUS/ROADMAP/prompt index. Không thêm quyết định mới; DEC-047 giữ nguyên.
- Kiểm tra thực chạy: `-u` exit 0/0 ERROR; ruff các file Python đã đổi đạt (toàn addon còn 2 lỗi cũ ở `dashboard.py` không đổi); compileall; parse 23 XML; ACL CSV; `node --check` 13 JS; `git diff --check`. Playwright `verify_simple003.mjs` trên 18069 chỉ mở/Hủy popup và form (không xác nhận, không lưu, không gửi): 2 menu, 54 / 27 / 7, picker Gán và Đổi máy 7/7 máy stock không người giữ, tìm không dấu 15 = 15, chi tiết không có chuyển trực tiếp, link cũ, tablet/mobile; probe RPC từ chối máy có người giữ, A = B, mã yêu cầu sai, ghi custody trực tiếp. DB 18 bảng giữ count/hash; `tp_equipment_move` chỉ thêm 2 cột NULL.
- Chưa: gán/đổi/trả/gửi đề xuất thật, test suite Odoo/HOOT, transaction/race; probe "B trong kho còn người giữ" và "idempotency khác nội dung" bỏ qua vì không có dữ liệu; không có ảnh trước khi sửa code; 1366/1280 có sidebar thì bảng cuộn ngang trong khung.
- Next: admin xem UI và tự xác nhận Gán / Đổi máy / Trả về kho trên một máy cụ thể.

## CHG-20261116-002 — EQUIP-SIMPLE-003: chỉ chọn máy trong kho chưa có người giữ để đổi/gán

- Ngày: 16/11/2026 (Asia/Saigon). Người dùng xác nhận chưa chạy prompt CHG-001 và bổ sung máy thay thế phải trong kho/chưa có chủ, máy có chủ không được đổi. Vai trò điều phối, chỉ sửa tài liệu.
- Cập nhật cùng prompt `CLAUDE_EQUIP_SIMPLE_003.md`, DEC-047, PROJECT_STATUS/ROADMAP/prompt index. Domain bắt buộc stock AND employee rỗng kèm guard hiện có; không lọc mặc định có thể bỏ, không chọn máy cùng người/người nghỉ việc/stock không nhất quán, không đổi chéo. Backend kiểm lại sau khóa/version, từ chối race/ID cố truyền và giữ máy cũ/phiếu nguyên trạng. Bỏ nút chuyển trực tiếp khỏi UI mới để không lách quy tắc; thu hồi thực tế về kho rồi mới gán cho người khác. Không nhầm chưa có người giữ với sở hữu pháp lý.
- Chưa sửa code/runtime/DB/thiết bị/nhân viên/quyền, không commit/push; prompt vẫn chưa triển khai. Giữ chỉ đạo main18069 sau backup, không18079/bộ test riêng/fixture.
- Kiểm tra thực chạy: workflow baseline `check` PASS, `start` trước sửa; kiểm UTF-8/fence/link/điều kiện mới và không còn hướng dẫn đổi/chuyển trực tiếp trái quy tắc, diff và đối chiếu digest code; kết quả chi tiết được ghi ở workflow cuối lượt. Không chạy Odoo/browser/giao dịch vì chỉ bổ sung prompt.
- Next: giao Claude cùng file prompt đã cập nhật, không cần chạy prompt cũ trước.

## CHG-20261116-001 — EQUIP-SIMPLE-003: prompt thu gọn Kho thành thiết bị/người giữ và yêu cầu đề xuất

- Ngày: 16/11/2026 (Asia/Saigon). Vai trò điều phối; người dùng giao viết prompt, không sửa ứng dụng. DEC-047 ghi yêu cầu mới thay UI Kho nhiều tab.
- Phân tích source: equipment/move/proposal/HR, menu/sidebar/filter/back; tái sử dụng `maintenance.equipment`, `tp.equipment.move.action_done()` và `tp.equipment.proposal`, không model kho/nhân viên bản sao. Code move đã có guard/khóa/version/chống trùng và hoàn tất draft hợp lệ, không cần bắt admin đi qua phiếu nhiều bước. Đây là đọc source, chưa audit giao dịch runtime.
- Tài liệu: thêm `docs/prompts/CLAUDE_EQUIP_SIMPLE_003.md`, cập nhật PROJECT_STATUS/ROADMAP/DECISIONS/prompt index và ghi note thay phạm vi Kho trong UI-002. Chỉ hai menu Thiết bị/Yêu cầu đề xuất; lọc đang dùng/trong kho cùng bảng; popup gán, đổi máy nguyên tử, trả kho/chuyển người; backend giữ history/company/quyền/version/retry. Giữ ngoại lệ, nguồn nhập chờ và dữ liệu cũ; không DROP/uninstall/xóa DB. Thu gọn dashboard/menu, không mở self-service/duyệt mua/kế toán.
- Môi trường giao thực thi giữ chỉ đạo EQUIP main18069 sau backup, không18079/clone/bộ test/fixture/nhập lại. Lượt lập prompt không sửa code/runtime/DB/user/quyền, không commit/push. Baseline hiện tại theo workflow CHG-20261115-005; số liệu 27 người giữ/55 hồ sơ/9 dòng chờ là bàn giao cũ, chưa đếm lại DB. PROJECT_STATUS làm rõ số liệu lịch sử 26/54.
- Kiểm tra thực chạy: workflow baseline `check` PASS và `start` trước sửa tài liệu; 7 docs UTF-8/fence, 6 link mới, 9 mục prompt, CHG/DEC không trùng và note thay phạm vi ở đầu prompt cũ đều đạt; `git diff --check` đạt. Digest code `61ab131c…515542`, 511 file khớp checkpoint, không đổi application/tooling. `finish/check` ghi kết quả vào workflow cuối lượt. Không chạy Odoo/HOOT/browser hoặc giao dịch thiết bị vì chỉ lập prompt.
- Next action: giao Claude prompt EQUIP-SIMPLE-003 để triển khai; báo đúng phần chỉ đọc source/UI hoặc chưa chạy giao dịch, không tự đổi máy thật để làm bằng chứng demo.

## CHG-20261115-005 — EQUIP-DATA-001: admin xác nhận dòng nguồn #63 → HR #57, đăng ký TB-00055

- Ngày: 15/11/2026 (Asia/Saigon). Admin xác nhận trong chat ("Đúng, gán giúp", xác nhận lại "Yes, assign #63") dòng nguồn #63 (đợt 1, sheet `thiet bi`, dòng 40, "PC B560M GAMING HD") là của nhân viên HR #57; tên nguồn khác HR chỉ ở vị trí dấu thanh. Chỉ dữ liệu, không đổi code. Áp trực tiếp `tp_tanphat_dev` (`18069`) sau backup đầy đủ `.local/equip-ui002/backup-pre-link63/` (DB dump + filestore + source + manifest); bản dừng giữa chừng trước đó đặt tên `backup-pre-link63-INCOMPLETE/`, không dùng để phục hồi. Không 18079/clone/seed/import lại, không commit/push.
- Thao tác theo luồng chuẩn của đợt nhập, với quyền admin (`su=False`): dòng #63 ghi `employee_id = 57`, `disposition = equipment` và lý do xác nhận; `action_confirm_mapping()`; `batch.action_apply()` (trước đó kiểm không có dòng xác nhận nào khác chờ áp, nên chỉ dòng #63 được tạo); `action_tp_register()` trên hồ sơ nháp mới. Kết quả: **TB-00055** đang quản lý, nơi giữ nhân viên HR #57, phân loại PC, sở hữu công ty, cấu hình theo nguồn, **Chưa kiểm tra thực tế**, 1 phiếu Ghi nhận ban đầu (PBG-2026-0055). Đợt nhập vẫn `partial`; còn 9 dòng chờ.
- Dãy số: lượt chạy thử (rollback) đã làm dãy `tp.equipment` và `tp.equipment.move` (kiểu standard, không rollback) tăng thêm 1; trước khi chạy thật đặt lại về max+1 (55) vì khoảng trống đúng bằng lượt thử, để mã không bị nhảy.
- Kiểm thực chạy: chạy thử rollback rồi chạy thật cùng kết quả (bảng người sử dụng 26 → 27, dòng chờ 10 → 9, hồ sơ 54 → 55, phiếu 54 → 55, HR #57 có 1 thiết bị, tìm `thùy anh` ra 1). Bảo toàn `preservation-after-link63.json` so `preservation-pre-link63.json`: chỉ khác thiết bị, phiếu/dòng phiếu, dòng/đợt nhập; HR employee/version/department, users, nhóm quyền, công ty giữ nguyên hash. Playwright `verify_link63.mjs` 9 PASS/0 FAIL/0 console error (27/27 một trang, tìm có/không dấu ra TB-00055, drill-down Giao nhân viên 27, Dòng nguồn chờ bổ sung 9). Chưa chạy test Python Odoo.
- Next: admin xử lý 9 dòng chờ còn lại ở **Dòng nguồn chờ bổ sung** khi đã xác minh người sử dụng; kiểm tra thực tế TB-00055 khi bàn giao.

## CHG-20261115-004 — EQUIP-UI-002 fix: bảng Thiết bị & người sử dụng hiển thị hết, không chia 20 dòng/trang

- Ngày: 15/11/2026 (Asia/Saigon). Người dùng yêu cầu bảng **Thiết bị & người sử dụng** hiển thị hết thay vì 20 dòng mỗi trang (trước đó 1-20 / 26). Áp trực tiếp `tp_tanphat_dev` (`18069`) sau backup `.local/equip-ui002/backup-pre-fix004/` (DB dump + filestore + source + manifest). Không 18079/clone/seed/import lại, không commit/push.
- `tp_equipment` 20.0.1.4.1 → **20.0.1.4.2** (`-u` + restart): bảng có `tp_filter_profile = equipment_users` (menu `/odoo/kho-thiet-bi` và drill-down dashboard) nạp một trang `ALL_ROWS_LIMIT = 1000` dòng, bỏ qua số dòng/trang đã lưu, giữ khi quay lại từ form; ô chọn 10/20/50/100 thay bằng chữ `Hiển thị tất cả N dòng` (nếu vượt 1000 thì pager vẫn phân trang). Các bảng thiết bị khác (dùng chung, tồn kho, tất cả hồ sơ, phiếu, bảng quan hệ trong form) giữ 10/20/50/100, mặc định 20. Lọc/đếm/Xuất Excel không đổi scope.
- Kiểm thực chạy: `-u` exit 0 không ERROR (`upgrade-fix004-*.log`); Playwright `verify_fix004.mjs` 11 PASS/0 FAIL/0 console error (menu 26/26 dòng một trang, pager 1-26 / 26, chữ `Hiển thị tất cả 26 dòng`; mở form rồi quay lại vẫn 26; tìm "thùy anh" ra 0 và xóa tìm về 26; drill-down Giao nhân viên 26/26; tất cả hồ sơ vẫn 20/trang, dùng chung/tồn kho còn ô chọn số dòng). Bảo toàn `preservation-after-fix004.json` so trước chỉ khác `modules.tp_equipment.latest_version`. `tp_equipment` không có bộ HOOT riêng; chưa chạy test Python Odoo.
- Dòng nguồn #63: lượt gán vào HR #57 bị người dùng dừng trong lúc backup (`.local/equip-ui002/backup-pre-link63-INCOMPLETE/`, không dùng để phục hồi); chưa đổi dữ liệu, 10 dòng chờ giữ nguyên. Checkpoint `ai_workflow.py start` của lượt đó được dùng tiếp cho thay đổi này.
- Next: Ctrl+F5 trên 18069 xem bảng; xác nhận lại việc gán dòng nguồn #63 → HR #57.

## CHG-20261115-003 — EQUIP-UI-002 fix: tìm kiếm không phân biệt dấu, màn rỗng hiển thị đúng, bỏ nút Mới khi mở từ dashboard

- Ngày: 15/11/2026 (Asia/Saigon). Người dùng báo trên **Thiết bị & người sử dụng** (mở từ dashboard): tìm một tên nhân viên có dấu ra 0 dòng, màn rỗng in nguyên thẻ HTML, có nút **Mới**, và hỏi dữ liệu có bị thiếu. Áp trực tiếp `tp_tanphat_dev` (`18069`) sau backup `.local/equip-ui002/backup-pre-fix003/` (DB dump + filestore + manifest). Không 18079/clone/seed/import lại, không commit/push.
- Nguyên nhân: (1) HR #57 ghi "Thu**ỳ**", gõ "th**ù**y" khác vị trí dấu thanh nên `ilike` không khớp, DB không có `unaccent`; (2) `openUi` của dashboard nhận action qua `orm.call` nên `help` là chuỗi thường và list in thô; (3) `ACTION_CONTEXT` của drill-down ghi đè context action nên mất `create: False`.
- Dữ liệu không mất: thiết bị "PC B560M GAMING HD" là dòng nguồn #63 (đợt 1, sheet `thiet bi`, dòng 40) đang **chờ xác minh người sử dụng** vì tên nguồn ("Thúy") khác HR ("Thuỳ") ở dấu thanh; gợi ý HR #57 nhưng không tự gán. Dòng này và 9 dòng chờ khác giữ nguyên, chờ admin xác nhận ở **Dòng nguồn chờ bổ sung**.
- `tp_equipment` 20.0.1.4.0 → **20.0.1.4.1** (`-u` + restart): `common.fold_text` (NFD, bỏ dấu, đ→d, chữ thường) chỉ dùng cho tìm kiếm; `_search_tp_search` thêm nhánh so khớp không dấu trên tên/mã nhân viên HR và tên/mã/serial/model/hãng thiết bị, giữ `not ilike`. Không dùng cho liên kết danh tính. Dashboard `markup()` help trước `doAction`; `ACTION_CONTEXT` thêm `create: False` cho bảng người sử dụng và dùng chung. Help rỗng hai bảng viết lại trung tính, chỉ tới Tồn kho, Dùng chung và Dòng nguồn chờ bổ sung.
- Kiểm thực chạy: `ast`/`lxml`, `-u` exit 0 không ERROR (`upgrade-fix003-*.log`); Odoo shell rollback: 4 cách gõ (có/không dấu, khác vị trí dấu thanh, chữ hoa) đều khớp HR #57 (0 thiết bị), `not ilike` nhất quán; Playwright `verify_fix003.mjs` 11 PASS/0 FAIL/0 console error (drill-down Giao nhân viên 26 dòng, không nút Mới, help hiển thị chữ, tìm có/không dấu ra đúng người, menu path và Dùng chung đạt). `tp_equipment` không có bộ HOOT riêng. Bảo toàn `preservation-after-fix003.json` so trước fix chỉ khác `modules.tp_equipment.latest_version`. Chưa chạy test Python Odoo.
- Quy trình: `ai_workflow.py start` chạy muộn (sau khi đã sửa code/docs) nên checkpoint lấy trạng thái đã sửa; finish/check ghi nhận sau đó.
- Next: Admin xác nhận dòng nguồn #63 (→ HR #57) và 9 dòng chờ khác ở **Dòng nguồn chờ bổ sung**; Ctrl+F5 trên 18069 để nạp JS mới.

## CHG-20261115-002 — EQUIP-UI-002 / UI-BACK-001: Bảng thiết bị theo HR, Quay lại toàn hệ thống và nâng cấp dashboard trên main 18069

- Ngày: 15/11/2026 (Asia/Saigon). Thực hiện prompt `docs/prompts/CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md` cùng đề xuất dashboard của người dùng, áp trực tiếp `tp_tanphat_dev` (`18069`) sau backup `.local/equip-ui002/backup-pre-ui002/` (DB dump + filestore + source + manifest) và baseline `baseline-before.json`. Không 18079/clone/fixture giả/seed/import lại, không commit/push.
- Phiên bản: `tp_equipment` 20.0.1.3.0 → **20.0.1.4.0**, `tp_web_home` 20.0.1.7.0 → **20.0.1.8.0**, `tp_hr_workspace` 20.0.1.11.4 → **20.0.1.11.5**; chỉ `-u` ba module + restart main. Không đổi schema lưu trữ, ACL, workflow hoặc nhóm quyền; Kho vẫn admin-only (`base.group_system`).
- **Thiết bị & người sử dụng** (`/odoo/kho-thiet-bi`): domain action chỉ còn thiết bị/linh kiện gốc đang quản lý, nơi giữ nhân viên/mượn **và** có nhân viên HR (26); không stock, dùng chung, dịch vụ hoặc chưa rõ người. Cột: Người sử dụng (avatar + tên + mã HR) · Phòng ban HR · Loại · Thiết bị (tên + mã) · Tình trạng (badge) · Ghi chú hỏng hóc (clamp 2 dòng + tooltip); bỏ cột trạng thái nơi giữ. Độ rộng theo `width="[min,max]"` để 1440/1366 không cuộn ngang; mobile/tablet cuộn trong khung bảng. Lọc, đếm, phân trang và Xuất Excel dùng cùng `root.domain` của action.
- Lối xem còn lại: menu mới **Thiết bị dùng chung & chưa xác định người** (`/odoo/thiet-bi-dung-chung`, 20) và **Tất cả hồ sơ thiết bị** (`/odoo/ho-so-thiet-bi`, 54, gồm dịch vụ/ngừng quản lý); **Thiết bị tồn kho** giữ 7. Drill-down dashboard và nút thiết bị trên hồ sơ nhân viên dùng action phù hợp với nhóm được bấm.
- **UI-BACK-001** ([chuẩn](ui/UI_BACK_001_STANDARD.md)): `tp_web_home` patch ControlPanel cho một nút `← Quay lại` trên mọi form chi tiết act_window (không dialog/list/kanban/dashboard/Cài đặt/wizard module), 40px desktop/44px mobile, tooltip `Quay lại: <màn trước>`. Trở về bằng `action.restore` (giữ lọc/trang/số dòng), deep link về list theo registry `tp_back_fallbacks` chỉ nhận xmlid (thiết bị theo nơi giữ, đọc chỉ đọc khi thiếu trường), rồi list của action, cuối cùng Trang chủ. Hộp thoại thay đổi chưa lưu `Lưu rồi quay lại`/`Bỏ thay đổi`/`Ở lại`; chống bấm kép. HR bỏ nút riêng `o_tp_hr_back` để không trùng; Hồ sơ của tôi dùng cùng helper.
- **Dashboard Kho**: header lọc + Làm mới + Xuất Excel; 4 KPI màu (Tổng 53 navy, Đang sử dụng 46 teal, Trong kho 7 xanh dương, Đề xuất đang mở 1 tím) mở đúng danh sách; donut 260px có tổng giữa + chú giải số/%, bấm lát mở thiết bị; thanh loại dày, nhãn đủ, số cuối, top N + `Khác (4 loại)`, không cuộn trong (tổng 53); thanh phòng ban tách `Trong kho`/`Dùng chung`/`Chưa xác định phòng ban`; khối đề xuất gần đây riêng; `Thiết bị cần chú ý`; `Chất lượng dữ liệu` thu gọn mặc định; hover nhẹ, animation một lần khi tải/đổi lọc, tôn trọng reduced-motion. Giữ 4 mục nghiệp vụ.
- Kiểm thực chạy: `lxml` XML, `node --check`, manifest; 4 log `-u` exit 0 không ERROR. HOOT `tp_web_home` 44/44 (+1 `tp_kd_workspace`), `tp_hr_workspace` 40/40 (+2 kd); `tp_equipment` không có bộ HOOT. Playwright `verify_ui002.mjs` 42 PASS/0 FAIL/0 console error (scope 26 không stock, KPI/thanh/donut, drill-down đúng tập, lọc/trang/số dòng giữ khi quay lại, dirty/lỗi lưu ở lại, 3 deep link, popup không nút, HR/Hồ sơ của tôi một nút, kích thước 5 viewport); `check_export.mjs` xuất 26/7/20 dòng khớp list, file người dùng 26/26 có nhân viên HR. Ảnh tại `.local/equip-ui002/screens/`.
- Bảo toàn: `preservation-final.json` so baseline chỉ khác `modules`; 18 bảng (HR employee/version/department, users, group membership, company, thiết bị, phiếu, đề xuất, nhập/dòng nguồn, kho, kiểm kê, vị trí, loại) giữ nguyên hash. Không bấm Lưu trên dữ liệu thật; 10 dòng chờ không xử lý.
- Giới hạn: KH-KD và hợp đồng có 0 bản ghi trên 18069 nên chỉ phủ theo quy tắc chung + HOOT model tổng hợp, chưa quan sát form có dữ liệu; URL chỉ có model hoặc link many2one vẫn mở form gốc `maintenance` (có sẵn từ trước, đề xuất xử lý riêng); file Excel còn vài tiêu đề tiếng Anh từ field gốc; chưa chạy test Python Odoo trên DB thật; chưa nghiệm thu nghiệp vụ.
- Next: Admin mở 18069 (Ctrl+F5) nghiệm thu trực quan list/detail/dashboard và Quay lại; quan sát lại KH-KD/hợp đồng khi có dữ liệu thật.

## CHG-20261115-001 — EQUIP-UI-002 / UI-BACK-001: Prompt bảng thiết bị theo HR và Quay lại toàn hệ thống

- Ngày: 15/11/2026 (Asia/Saigon). Người dùng yêu cầu bảng Thiết bị & người sử dụng không lẫn stock; chỉ cần loại/tình trạng/ghi chú hỏng/người dùng/phòng HR rõ, kèm nút Quay lại mọi chi tiết toàn hệ thống. Lượt này chỉ điều phối/prompt/docs, không code application/runtime/database hoặc đổi quyền.
- Tạo `docs/prompts/CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md`, gồm tách domain theo employee ID/custody employee hoặc loan, vật lý đang quản lý; list/count/filter/export giữ cùng scope; stock/dùng chung/dịch vụ/chưa rõ vẫn có lối xem. Bảng ưu tiên avatar/tên/mã HR/phòng/loại/thiết bị/tình trạng/ghi chú; không gán người hoặc sửa tên/phòng/data thật để làm đầy UI.
- Đối chiếu source action_equipment hiện list tổng không có domain riêng, tp_custody mang nhãn Trạng thái, chưa cột tp_condition_note; HR đã có backToEmployees/actionService.restore/guard chưa lưu. Prompt giao component/helper dùng chung, inventory coverage native form/custom detail/app cấu hình, không trùng nút HR; stack/filter/page/deep-link fallback/popup/dirty guards và nguồn mở sidebar. Không history.back mù/forceLeave/core hoặc quyền mới.
- Gộp nâng tiếp dashboard theo trao đổi: chữ/donut lớn, chart bỏ scroll nhỏ, phòng không gộp giả, đề xuất riêng/chất lượng dữ liệu thu gọn, giữ domain/denominator/unknown. Phạm vi chỉ UI hỗ trợ; không seed/import lại hoặc tự xử lý10dòng chờ. Claude áp main18069 sau backup theo chỉ đạo hiện hành, không18079/bộ test riêng/commit/push.
- Cập nhật status/roadmap/index và prompt cũ có chỉ dẫn supersede; DEC-046 ghi yêu cầu Quay lại thống nhất, DEC-045 làm rõ list theo nhân viên. Baseline code UI20.0.1.3.0 CHG-014 giữ; chưa triển khai hai task mới hoặc audit độc lập kết quả cũ.
- Kiểm thực chạy: baseline ai_workflow check CHG-014 đạt trước start; 6 docs UTF-8/fence, 8 link prompt mới, 7 phần/required scope, whitespace/status marker/unique DEC-046 và `git diff --check` đạt. Không browser/app tests, DB hoặc application writes. Finish/check batch docs; digest application/tooling giữ CHG-014, không coi workflow check là nghiệm thu UI.
- Next: giao Claude prompt mới, code/áp18069 rồi bàn giao ảnh list/detail/dashboard và coverage Quay lại các màn; bảo toàn HR/user/quyền/equipment/phiếu/source binding.

## CHG-20261114-014 — EQUIP-UI-001: Thiết kế lại và đơn giản hóa UI Kho thiết bị văn phòng trên main 18069

- Ngày: 14/11/2026 (Asia/Saigon). Triển khai trực tiếp `EQUIP-UI-001` lên `tp_tanphat_dev` (`18069`) sau backup tiền UI tại `.local/equip-ui001/backup-pre-ui/` (DB dump + filestore + source `20.0.1.2.0` + `manifest.json`). Không dùng `18079`, không chạy bộ test/seed dữ liệu giả, không commit/push.
- `tp_equipment` `20.0.1.2.0` → `20.0.1.3.0`: thêm helper hiển thị non-stored trên `dashboard.py`, `equipment.py`, `proposal.py`; giữ nguyên schema DB, ACL, workflow chuyển trạng thái, dữ liệu 54 thiết bị + 54 phiếu ban đầu + `DX-00001` + 2 đợt nhập, liên kết HR và admin-only (`base.group_system`).
- Giao diện mới scoped trong `.o_tp_eq_shell` (không ảnh hưởng navbar/Home/HR/KH-KD): nền `#F1F5F9` + card trắng bo góc; sidebar thu còn 4 mục chính (**Tổng quan**, **Thiết bị & người sử dụng**, **Thiết bị tồn kho** `action_equipment_stock`, **Đề xuất mua thiết bị**) + accordion **Quản trị dữ liệu** mặc định đóng; Dashboard giữ bộ lọc 1 hàng, 4 KPI và **2 biểu đồ lớn ngay dưới KPI** (`PHÂN BỔ THIẾT BỊ` donut + `CƠ CẤU LOẠI THIẾT BỊ` thanh ngang) nằm gọn màn đầu `1440×900`/`1366×768` (`bottom: 641`).
- Bảng & chi tiết: bỏ chip mặc định `search_default_not_retired` ở `action_equipment` (`searchChips: []`), thanh lọc 2 tiêu chí nhanh + `[Bộ lọc]` drawer + `Áp dụng`/`Xóa lọc` + chip áp dụng sau khi lọc (`[Đang sử dụng ×]`), tinh gọn cột bảng + nút `Xem` (`overflowBadges: 0`), form `equipment_form` & `proposal_form` dùng card rộng `o_tp_eq_form_wide`, khối HR `Ai đang sử dụng / Đang ở đâu`, 3 tab chính, bảng dòng đề xuất rõ cột `Duyệt`/`Dự toán` và chatter bên dưới sheet.
- Kiểm thực chạy: `ruff check`, `compileall`, `lxml` XML, manifest và `node --check` đạt; `-u tp_equipment --no-http --stop-after-init` exit `0`. Playwright `verify_after.mjs` trên `18069` đạt `consoleErrors: 0, pageErrors: 0, serverErrors: 0`, export XLSX HTTP 200 (`10861` bytes), ảnh trước–sau desktop/tablet/mobile tại `.local/equip-ui001/screens/`. Đối chiếu `preservation-after.json` vs `baseline-before.json`: `PRESERVATION_DIFFS: ['modules']` (`tp_equipment` `20.0.1.3.0`, `hr_maintenance` uninstalled).
- Cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, `TP_TABLE_FILTER_INVENTORY.md`, `tp_equipment/README.md`, `EQUIP_001_USER_GUIDE.md`, `EQUIP_001_ACCEPTANCE.md`, `EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md`. Technical/business/pilot acceptance tách biệt.
- Next: Admin mở [Kho thiết bị văn phòng](http://127.0.0.1:18069/odoo) (Ctrl+F5) để nghiệm thu trực quan và xem bộ ảnh trước–sau tại `.local/equip-ui001/screens/{before,after}/`.

## CHG-20261114-013 — EQUIP-UI-001: Prompt thiết kế lại Kho thiết bị, ưu tiên giao diện và bớt menu

- Ngày: 14/11/2026 (Asia/Saigon). Người dùng gửi hai ảnh và yêu cầu dashboard sáng nhiều màu, biểu đồ lớn phía trên, filter gọn/bỏ preset trong input, bảng không đè ô, nhiều thiết bị và thu gọn chức năng về thiết bị–người dùng/tồn/đề xuất. Lượt điều phối chỉ lập prompt/tài liệu, không application code/runtime/DB/role.
- Tạo `docs/prompts/CLAUDE_EQUIP_UI_001_SIMPLIFY_AND_REDESIGN.md`: bốn mục chính + quản trị/nâng cao mặc định đóng, palette có ý nghĩa, wireframe/kích thước đầu trang, hai chart dưới KPI, filter compact/drawer/SearchModel, bảng riêng từng loại và detail đồng bộ, animation/reduced-motion/responsive. Claude được backup và triển khai UI trực tiếp18069 theo chỉ đạo EQUIP, không18079/bộ test/fixture/commit/push.
- Đối chiếu source dashboard đặt Công việc đang mở trước chart; table.scss badge overflow visible/nowrap/max-width none gây tràn; action search_default_not_retired và hai lớp filter tạo vùng đầu bảng dày. Prompt chỉ ra điểm sửa, giữ backend scope và đường truy cập chức năng phụ; không CSS giấu filter thật. Không tự xóa model/phiếu/history/import hoặc mở non-admin/self-service; admin ghi nhận nhu cầu nhân viên theo HR ID.
- Số liệu UI yêu cầu rõ Trong kho khác Sẵn sàng cấp; chart cùng mẫu số/nhóm không trùng; đề xuất đang mở không bỏ nháp; không hardcode/chỉnh dữ liệu/state cho đẹp. Cập nhật PROJECT_STATUS/ROADMAP/DEC-045/index/blueprint với trạng thái prompt chưa thực thi; baseline nhập partial CHG-012 và10dòng chờ giữ là việc riêng.
- Kiểm thực chạy: baseline workflow check CHG-012 đạt trước start; 6 tài liệu UTF-8/fence, 6 liên kết prompt mới, đủ10phần và các yêu cầu scope, whitespace/new prompt/status marker đạt; `git diff --check` đạt. Không chạy app/browser tests hoặc sửa ứng dụng. Finish/check batch tài liệu, digest application/tooling phải giữ CHG-012; không coi checker là audit/ nghiệm thu UI mới.
- Next: giao prompt EQUIP-UI-001 cho Claude để code/áp18069, tự xem ảnh trước–sau dashboard/list/detail desktop/mobile và bàn giao kết quả nhìn thấy được; dữ liệu và quyền nguyên vẹn.

## CHG-20261114-012 — EQUIP-DATA-001: Nhập thật hai workbook vào Kho thiết bị main18069

- Ngày: 14/11/2026 (Asia/Saigon). Người dùng cho phép nhập hai workbook local trực tiếp vào `tp_tanphat_dev` (18069) sau backup; không 18079, không commit/push. Backup `.local/equip-data001/backup-pre-import/` (dump + filestore + source + manifest hash) trước mọi thay đổi.
- `tp_equipment` 20.0.1.2.0, chỉ `-u tp_equipment` và restart main: importer thêm đích ánh xạ (mã nguồn, phân loại, sở hữu, model, phần mềm, trạng thái, ngày, bảo hành, mô tả), trạng thái đợt `partial` giữ dòng chờ và áp dụng tiếp không tạo lại, giá trị xác nhận cho hồ sơ mới trên dòng nguồn, menu/action admin **Dòng nguồn chờ bổ sung**; đề xuất có `date_known`; phiếu ghi nhận ban đầu ghi rõ nguồn Excel chưa đối chiếu bàn giao. Sửa lỗi sẵn có của biểu đồ dashboard: template OWL gọi `String()` gây TypeError khi có dữ liệu, chuyển sang khóa tính trong JS.
- Dữ liệu đã lưu (ORM, admin, không SQL ghi nghiệp vụ/bỏ guard/`mark_verified`): 54 hồ sơ đăng ký (53 vật lý, 1 dịch vụ) + 54 phiếu ghi nhận ban đầu hoàn tất; 1 đề xuất nháp/chưa xác minh 5 dòng, tổng khớp nguồn. 9 dòng chờ xác minh HR (tên khác dấu/chữ hoặc không có trong HR — chỉ gợi ý, không tự gán) và 1 dòng thiếu thông tin thiết bị giữ trên đợt `partial`; 6 dòng N/a không tạo; 0 lỗi. 4 nhóm phân loại và 8 vị trí cấu hình mới; không tạo/sửa nhân viên, user, phòng ban hoặc quyền. Tệp đề xuất gửi lặp chỉ xử lý một lần.
- Kiểm thực chạy: Ruff/compile/parse XML cho phần sửa; upgrade log registry loaded; replay áp dụng lại/tải trùng không tạo thêm bản ghi. Đọc lại DB và giao diện 18069: dashboard, list 54 bản ghi, chi tiết (nhân viên/vị trí + phiếu ban đầu), dòng chờ, đề xuất, hai đợt nhập ở 1440×900; dashboard/list 375×812 không tràn ngang. Sổ Excel tạo lại 54 dòng/18 cột, lọc nơi giữ nhân viên 26 dòng, đề xuất 1+5 dòng. So hash trước/sau: HR employee/version/department, users, group membership, company giữ nguyên; `res_groups` chỉ đổi `write_date` nhóm HR do XML chạy lại, implied/membership không đổi. `git diff --check` đạt. Không chạy bộ Odoo/HOOT/E2E theo yêu cầu.
- Bằng chứng riêng (ignored): `.local/equip-data001/IMPORT_REPORT.md` (ánh xạ từng dòng hash/sheet/row → xử lý → ID/mã hoặc lý do), `result.json`, log, ảnh desktop/mobile, `preservation-after.json`. Tài liệu tracked chỉ ghi số tổng hợp.
- Next: admin xử lý 10 dòng chờ ở **Dòng nguồn chờ bổ sung** rồi áp dụng tiếp; nhập Excel không chứng minh đã kiểm kê, bàn giao, duyệt mua hoặc nghiệm thu nghiệp vụ.

## CHG-20261114-011 — EQUIP-DATA-001: Prompt nhập hai workbook thật vào Kho thiết bị main18069

- Ngày: 14/11/2026 (Asia/Saigon). Người dùng yêu cầu nhập hai file local vì kho còn trống; đường dẫn đề xuất được gửi lặp, chỉ có hai nguồn khác nhau. Chỉ chuẩn bị prompt trong vai trò điều phối, không sửa application code/runtime/database hoặc nhập dữ liệu trong lượt này.
- Tạo `docs/prompts/CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md`: backup mới rồi thực nhập trên main18069, dùng importer hiện có, bổ sung mapping tối thiểu còn thiếu, apply/đăng ký phần đủ điều kiện và mở list/dashboard/export có dữ liệu. Không18079/bộ test/dữ liệu giả/commit/push theo user; không xin lại quyền nhập/áp main đã được giao. Giữ admin-only/HR ID và cùng DB, không tạo người/user/phòng ban hoặc đổi quyền.
- Đối chiếu source `import_batch.py`, `equipment.py`, `move.py`, `proposal.py`, dashboard/view: importer tạo draft mới category chưa có và ownership unknown, chưa chuyển đủ trường nguồn; đăng ký cần category và sinh opening. Prompt phân biệt ghi nhận nguồn với bàn giao/kiểm kê đã xác minh, giữ unknown khác 0/ngày giả, tách dịch vụ/N/a/dòng thiếu, không đẩy người chưa rõ thành tồn stock. Đề xuất giữ nháp/chưa duyệt; không sinh hàng mua/receipt/approval/hóa đơn từ Excel.
- Cập nhật PROJECT_STATUS, DEC-045, ROADMAP, prompt index và ghi chú supersede tại prompt triển khai/blueprint/user guide/runbook. Số đếm dòng nguồn chỉ để đối chiếu, không tuyên bố số tài sản đã nhập; dữ liệu chi tiết/giá/PII giữ private ignored.
- Kiểm thực chạy: baseline workflow check CHG-010 đạt trước start; 9 tài liệu UTF-8/fence, 9 liên kết đến prompt mới, 7 phần và nội dung nhập bắt buộc đạt. Hai file local tồn tại/hash khớp bản phân tích NAS; vùng phân tích/báo cáo private được git-ignore. `git diff --check` đạt (Git có cảnh báo LF/CRLF từ thay đổi sẵn có, không lỗi whitespace). Không chạy test ứng dụng hoặc import. Chốt workflow cho batch tài liệu, digest application/tooling phải giữ CHG-010; check không thay chứng minh nghiệp vụ.
- Next: giao prompt EQUIP-DATA-001 cho Claude, thực nhập sau backup rồi báo số mới/có sẵn/đăng ký/nháp/chờ và URL xem trên18069. Nhập thành công không chứng minh đã kiểm kê/bàn giao/được duyệt mua hoặc nghiệm thu nghiệp vụ.

## CHG-20261114-010 — EQUIP-001: Hoàn tất Claude dở và nâng cấp Kho thiết bị trên 18069

- Ngày: 14/11/2026 (Asia/Saigon). Người dùng giao Codex thực thi nốt bàn giao Claude; giữ checkpoint 08:39:05 UTC. Source Phần 3 ban đầu tham chiếu model chưa nạp; hoàn tất trước restart/upgrade, không xóa hoặc làm lại checkpoint. Không commit/push, không đụng 18079.
- Addon `custom_addons/tp_equipment` 20.0.1.1.0: nối sửa chữa/bảo trì/nâng cấp, đề xuất/rà soát/căn cứ duyệt ngoài, nhận từng phần, kiểm kê/điều chỉnh và nhập XLSX preview với ACL/menu/native views/sequences. OWL dashboard SVG/KPI/drill-down, Excel theo domain và lọc/phân trang 10/20/50/100; 16 bảng con reuse native View/SearchModel và helper chung với parent domain/dirty guard. Không đổi API legacy/core Odoo.
- Sửa guard admin/company/mail/file/native, sentinel nội bộ chống context giả, lock parent/line và audit bất biến, chống nhận vượt/lặp/thực hiện dòng chưa đủ căn cứ. Unknown monetary flags giữ khác với 0 đã xác nhận trong model/view/report; sửa Odoo20 OrderedSet search và nhãn tiếng Việt. Import SHA256/company/kind, raw/cached/merge provenance đã làm sạch, không chạy công thức/giữ workbook/IP/MAC; mapping/alias cần xác nhận. Nguồn sau đối chiếu ID existing không ghi đè, dòng new cần xác nhận riêng, không tạo HR/user.
- Sao lưu: Claude pre `.local/equip001-main/backup-main-pre/`; resume `.local/equip001-main/backup-main-resume/` dump 8.894.993 bytes/770 filestore files + source/hash. Resume source là Claude chưa hoàn chỉnh, rollback cần source+DB+filestore tương thích, không coi backup là đã restore. Chỉ upgrade `-u tp_equipment` main `tp_tanphat_dev:18069`; log cuối `upgrade-final4.log` exit0/registry loaded. `hr_maintenance` uninstalled; HR20.0.1.11.4/Home20.0.1.7.0 giữ.
- Kiểm thực chạy: Ruff/compileall addon, parse20XML/35manifestpaths/node--check9JS đạt; `git diff --check`, UTF-8/fence 11 tài liệu, 38 local links trong scope và unique 18 AT đạt; link lịch sử đến prompt đã archive ngoài scope giữ nguyên. Browser chỉ đọc dashboard1440×900/390×844, các danh sách chính rỗng/form mới chưa lưu: 0 console errors/HTTP>=500/overflow; Excel sổ rỗng tải và đọc lại18cột. Snapshot hash trước/sau không đổi HR employee/version/department, users/group membership, equipment/request/move/receipt;39nhân viên28users,bốn bảng thiết bị/giao dịch đều0. Evidence ignored `.local/equip001-main/`.
- Bàn giao blueprint, schema/access, acceptance18AT, user guide, deploy/import/rollback runbook, addon README, table filter inventory và status/roadmap/prompt index. Không chạy bộ Odoo/HOOT/E2E/race/regression theo yêu cầu; không seed/nhập Excel thật/tạo giao dịch giả. Source implementation và quan sát màn trống không chứng minh nonempty flow/role/race/PDF/QR hoặc nghiệm thu nghiệp vụ/pilot. Next: người dùng xem18069; nhập nguồn thật có phạm vi/backup/mapping riêng.

## CHG-20261114-009 — EQUIP-001: Cho phép code trực tiếp 18069, bỏ cổng test theo yêu cầu

- Ngày: 14/11/2026 (Asia/Saigon). Yêu cầu trực tiếp: không kiểm thử riêng, làm ngay 18069 và sửa lỗi phát sinh; thay chỉ đạo test-only trước. Phiên điều phối chỉ cập nhật tài liệu, chưa chạy deploy/code/database.
- Sửa prompt/blueprint, DEC-045, roadmap/index/status. Claude được backup DB+filestore rồi code/install/upgrade đúng module trên main, mở menu/admin xem ngay; không chờ xác nhận deploy lần hai. Bỏ 18079, test-first, Odoo/HOOT/E2E/race suites; 18 AT giữ làm tiêu chí hành vi, không ghi giả test PASS.
- Giữ một addon riêng/admin-only/DB và HR chung, quyền backend và transaction/idempotency, bảo toàn dữ liệu/tài khoản. Lệnh deploy không tự seed giả/bulk nhập Excel thật/mở role non-admin/duyệt chi/kế toán.
- Kiểm thực chạy: baseline workflow check CHG-008 đạt trước start; 14 link mới/liên quan, fence/UTF-8, unique CHG-009/18 tiêu chí và `git diff --check` đạt. Hash 453 file application/tooling giữ `9f0d71bd0648356ee52b9e7f52da88533f7b21fc1c3bc947557b1dc1aaa9bb4a`; finish/check cho batch tài liệu khi chốt. Không Odoo/browser/app tests vì lượt này chỉ tài liệu. Next: Claude nhận prompt đã cập nhật và thực hiện trực tiếp 18069.

## CHG-20261114-008 — UI-TABLE-FILTER-001: Triển khai & kiểm thử bộ lọc toàn hệ thống trên `18079` (`DEC-044`)

- Ngày: 14/11/2026 (Asia/Saigon). Môi trường: chỉ `tp_tanphat_test` (`18079`); `tp_tanphat_dev` (`18069`) chưa áp, không commit/push.
- Phạm vi: `tp_web_home` (`static/src/search/*`, `static/tests/search/*`), `tp_hr_workspace` (`views/search_views.xml`, `hr_ui.xml`, `workspace.xml`, `employment_contract.xml`, `static/src/table/*`, `my_profile.*`, `tests/test_table_filter_hr.py`), `tp_kd_workspace` (`views/search_views.xml`, `project_restructure.xml`, `wbs.xml`, `static/src/table/*`, `overview.js`, `tests/test_table_filter_kd.py`), `tp_contract` (`views/tp_contract_search_views.xml`), `tp_core` (`views/tp_work_item_search_views.xml`, `native_search_views.xml`), `tp_crm_project_bridge` (`views/crm_tag_search_views.xml`), `tp_dashboard_privacy` (`views/dashboard_search_views.xml`), cùng `TP_TABLE_FILTER_INVENTORY.md`, `UI_TABLE_FILTER_001_ACCEPTANCE.md`, `UI_TABLE_FILTER_001_USER_GUIDE.md`, `ops/runbooks/UI_TABLE_FILTER_001_DEPLOY_AND_ROLLBACK.md`, `ROADMAP.md`, `PROJECT_STATUS.md`, `docs/prompts/README.md` và README 3 addon.
- Nội dung: xây dựng `<TpTableFilterBar>` dùng chung (Pending vs Applied, AND/OR, phân biệt `Tất cả`/`Chưa khai báo`, `name_search(domain=...)` Odoo 20, TZ VN, đồng bộ SearchModel/Favorites, chip gỡ nhanh, mobile drawer `44px`, layout ControlPanel grid không chồng lấn); phủ đủ S1 HR + bảng con popup (`tp_hr_relation` + guard `HrListModel`), S2 KH-KD/Contracts/Work Items + cô lập `project_search_restructure` (`priority="32"`), S3 search views cho các bảng native còn lại; không thêm DB mới, không đổi quyền hay workflow nghiệp vụ.
- Kiểm thử thực chạy trên `18079`: `ruff check custom_addons/` (`All checks passed!`), `git diff --check`; Odoo Python tests đạt **0 failed, 0 error(s) of 98 tests** (`tp_contract` 24, `tp_hr_workspace` 32, `tp_kd_workspace` 50, `tp_web_home` 16); HOOT đạt `tp_web_home` **39/206**, `tp_hr_workspace` **42/200**, `tp_kd_workspace` **22/85**; Playwright `verify_at_f.cjs` (`setup -> verify -> teardown`) đạt `12/12` `AT-F01`–`AT-F12` (`0` console errors, `0` HTTP >= 500) kèm kiểm tra trực quan screenshot `1440×900` và `390×844`.

## CHG-20261114-007 — EQUIP-001: Chốt một module riêng và admin-only theo người dùng

- Ngày: 14/11/2026 (Asia/Saigon). Vai trò điều phối, chỉ sửa tài liệu/prompt.
- Đối chiếu thấy bản đầu đề xuất nhiều vai trò thao tác, chưa khớp yêu cầu chỉ admin. Đã sửa `CLAUDE_EQUIP_001_OFFICE_EQUIPMENT.md`, `TP_EQUIPMENT001_BLUEPRINT.md`, DEC-045, ROADMAP, prompt index và PROJECT_STATUS.
- Một addon riêng `tp_equipment`, tên Kho thiết bị văn phòng, thẻ/icon/menu/dashboard/sidebar riêng; cùng DB và employee/department/user/partner hiện có, không gộp UI vào HR/KH-KD, không addon workspace thứ hai mặc định.
- Chỉ admin `base.group_system` trong scope được xem/quản lý; non-admin gồm HR/HEAD/kỹ thuật/staff/native equipment manager bị chặn kể cả URL/RPC/QR/read/export/file/chatter/public HR/mail; không tự subscribe/assign mở quyền. Người thực tế trên phiếu không đồng nghĩa user có quyền module. Không triển khai Thiết bị của tôi/self-service trong scope này; admin xem thiết bị gắn HR cùng ID.
- AT-E01/E13 và luồng báo hỏng/rà soát/notification đã cập nhật; quyền ký/duyệt chi bên ngoài không tự mở vì là admin hệ thống. Chưa sửa application/runtime/DB hoặc cấp role thật; giữ checkpoint batch code đang chạy, không finish thay.
- Kiểm tra thực chạy: 11 link mới/liên quan, UTF-8/fence/table, 18 AT, unique CHG-007 và nội dung một module/admin-only đạt; `git diff --check` đạt. Không chạy Odoo/browser vì chưa triển khai; không finish checkpoint của batch khác. Next: Claude dùng phiên bản prompt cập nhật và phối hợp test/source với batch filter trước code EQUIP.

## CHG-20261114-006 — EQUIP-001: Phân tích hai workbook và chuẩn bị kho thiết bị văn phòng

- Ngày: 14/11/2026 (Asia/Saigon). Vai trò điều phối, chỉ đọc nguồn/lập tài liệu/prompt; DEC-045.
- Nguồn: hai workbook NAS do người dùng cung cấp; kiểm file hash, tất cả sheet/row/cell, merged range, formula và cached values, kiểm tổng độc lập; không macro/recalc/network scan. Raw và phân tích có dữ liệu thật ở `.local/equipment001/` ignored, không chép vào Git.
- Tệp: `docs/architecture/TP_EQUIPMENT001_BLUEPRINT.md`, `docs/prompts/CLAUDE_EQUIP_001_OFFICE_EQUIPMENT.md`, DECISIONS/ROADMAP/prompt index/PROJECT_STATUS. Chuẩn bị nhận/cấp/thu hồi/chuyển/mượn, sửa/nâng cấp, đề xuất và duyệt ngoài theo căn cứ, kiểm kê, dashboard/chart, Excel/PDF/QR và scope/user/mobile/filter.
- Nền đề xuất: native Odoo dùng maintenance gốc và HR/department/user/partner chung; source có maintenance/stock/purchase nhưng chưa kiểm installed state. Nhận diện implied HR→Equipment Manager và quyền đọc company-wide trong upstream; prompt yêu cầu guard toàn native path thay vì ẩn nút.
- Phân biệt nhập dữ liệu: STT reset, merge, N/a/thiếu máy/dịch vụ/tài sản cá nhân, formula, ngày/giá chưa biết và tên khác HR cần preview/disposition/mapping có xác nhận. Không biến đề xuất thành đã mua/đã duyệt hoặc bịa số liệu dashboard.
- Phạm vi tương lai: S0 + EQUIP-001a–e, AT-E01–18, test 18079 lần lượt với batch filter; áp main và import thật giao riêng. Chưa code EQUIP, không DB/module/role/password mutation, không commit/push.
- Kiểm tra thực chạy: validator đạt 11 link mới/liên quan, UTF-8/fence/table, unique CHG-006/DEC-045/AT-E01–18, các đường dẫn input và private extraction được Git ignore; `git diff --check` đạt. Đọc lại xác nhận hash 2 workbook gốc không đổi, đếm dòng và tổng nguồn khớp kiểm độc lập, kết quả riêng `.local/equipment001/source_validation.json`. Không Odoo/HOOT/browser vì lượt này chỉ tài liệu. Checkpoint có sẵn được giữ; code filter đang đổi song song nên không finish batch đó, không tuyên bố workflow check đạt hoặc application hash giữ nguyên trong cả lượt. Biên ranh riêng ghi `.local/equipment001/planning_boundary.json`.
- Next action: phiên thực thi hoàn tất/điều phối batch filter trước ghi chung source/test, đọc prompt và viết AT cho thiết bị; giữ CHG-006 docs, lấy ID bàn giao mới cho code.

## CHG-20261114-005 — UI-TABLE-FILTER-001: Quy chuẩn, inventory và prompt bộ lọc toàn hệ thống

- Ngày: 14/11/2026 (Asia/Saigon). Vai trò điều phối; chỉ sửa tài liệu/policy/handoff, không application code hoặc runtime/DB.
- Yêu cầu người dùng: mọi bảng có bộ lọc riêng theo nội dung; lưu để phòng ban tương lai không bỏ sót. DEC-044 ghi nhận yêu cầu; trạng thái `SPEC_READY_NOT_IMPLEMENTED`, chưa phải nghiệm thu triển khai.
- Tệp chính: `docs/ui/TP_TABLE_FILTER_STANDARD.md`, `TP_TABLE_FILTER_INVENTORY.md`, `docs/prompts/CLAUDE_UI_TABLE_FILTER_001.md`; nối cổng vào AGENTS, AI_CHANGE_WORKFLOW, HANDOFF_TEMPLATE, ROADMAP, DECISIONS, prompt index và PROJECT_STATUS.
- Phân tích source: HR đã có các search view và pager; KH-KD có KD-UI-007/toolbar/relation/filter native để tái sử dụng. Inventory 07/11 chỉ là lịch sử; cần resolve view hiện hành và bổ sung HR contract/history, dự án/đấu thầu/report/native app. Không tuyên bố đã audit UI/registry thực tế trong lượt này.
- Prompt: S0–S4, AT-F01–12, filter riêng/action/parent domain/AND–OR/searchability/quyền/options/count/export/date/dirty/mobile; triển khai test 18079, áp main 18069 giao riêng. Không React/core/engine mới, không đổi dữ liệu hoặc quyền người thật, không commit/push.
- Kiểm tra thực chạy: baseline workflow check đạt CHG-20261114-004; validator tài liệu đạt 28 liên kết mới/liên quan, unique CHG/DEC/AT-F01–12, UTF-8/fence và các điểm vào quy chuẩn; `git diff --check` đạt sau sửa khoảng trắng ở dòng ngày prompt index. Snapshot 436 file application/tooling trước/sau cùng SHA-256 `84f98643caea54a5bf5e0f7e8efeb146b33abff0cdb5f9380d00f37ba1e194c5`. Không chạy Odoo/HOOT/browser vì chỉ tài liệu; workflow finish/check thực hiện khi chốt bàn giao, không thay nghiệm thu ứng dụng.
- Next action: Claude nhận prompt, inventory/AT trước code, hoàn thiện coverage trên test; phiên chính review test/ảnh trước bước áp main riêng. Visual/business/pilot và các gap cũ giữ riêng.

## CHG-20261114-004 — UI-HISTORY-001: Làm sạch dữ liệu & thiết kế lại `Lịch sử hoạt động` (HR Chatter & Thông tin cá nhân)

- Ngày: 14/11/2026 (Asia/Saigon).
- Phạm vi: `tp_hr_workspace` (`models/hr_history.py`, `models/hr_role.py`, `models/department_transfer.py`, `models/my_profile.py`, `static/src/my_profile/my_profile.js`, `my_profile.xml`, `my_profile.scss`, `static/tests/hr_profile.test.js`, `tests/test_my_profile.py`), tài liệu (`PROJECT_STATUS.md`, `CHANGELOG.md`, `UI_SHELL_UNIFY_001_ACCEPTANCE.md`, `custom_addons/tp_hr_workspace/README.md`).
- Nội dung: Chuyển toàn bộ JSON audit kỹ thuật của `hr_role.py` & `department_transfer.py` sang bảng `tp.hr.employee.audit` (`role_change`, `department_transfer`), không còn ghi JSON thô vào `mail.message`; mở rộng `hr_history.py` để tóm tắt các bản ghi JSON cũ (`{"before": ...}`, `department_transfer`, `Đối chiếu danh tính theo ID: ...`), tin onboarding tiếng Anh và Việt hóa toàn bộ nhãn/giá trị tracking (`As of ...`, `User Status`, `Job`, `Job Title`, `Sex`, `Timezone`, `Invited`/`Confirmed`, `Yes`/`No`, `None`); thiết kế lại tab `Lịch sử hoạt động` trong `Thông tin cá nhân` với thanh lọc nhanh, badge phân loại, tag ngày hiệu lực và bảng thay đổi từng dòng `Trường | Cũ → Mới`.
- Kiểm thử: `ruff check` (`0` lỗi), XML (`14` file), `git diff --check`, Odoo tests `--test-tags /tp_hr_workspace,/tp_web_home` (`68/68` pass trên `18079`), HOOT `tp_hr_workspace` (`42/42` — `200` assertions trên `18079`), Playwright `verify_history_tab.cjs` trên `18079`; backup `backup-main-v4` (`tp_tanphat_dev.dump` `8.538.341` bytes + `732` filestore files), upgrade `tp_hr_workspace` + `verify-post` (khớp 7 bảng) + `smoke_main_history_tab.cjs` & `smoke_main.cjs` read-only pass trên `18069`.

## CHG-20261114-003 — UI-PERSONAL-TAB-001: Thiết kế lại & Việt hóa 100% tab `Thông tin cá nhân` trong Hồ sơ nhân viên

- Ngày: 14/11/2026 (Asia/Saigon).
- Phạm vi: `tp_hr_workspace` (`models/hr_ui.py`, `views/workspace.xml`, `static/src/profile/employee_profile.scss`, `tests/test_hr_ui.py`), tài liệu (`PROJECT_STATUS.md`, `CHANGELOG.md`, `UI_SHELL_UNIFY_001_ACCEPTANCE.md`, `custom_addons/tp_hr_workspace/README.md`).
- Nội dung: Thiết kế lại tab `Thông tin cá nhân` của form `hr.employee` thành 8 thẻ `.o_tp_hr_card` xếp lưới 2 cột (`.o_tp_hr_personal_grid`, mobile 1 cột) đồng bộ phong cách tab `Tổng quan`; bỏ `o_address_format` gây khoảng trắng dọc và thay bằng 6 dòng địa chỉ tách bạch; xử lý fallback `"Chưa có tệp"` cho trường nhị phân trống ở chế độ chỉ đọc (thay cho `"false"`/tên giả định chưa tải); Việt hóa 100% nhãn, tooltip (`help`) và selection (`sex`, `marital`, `certificate`) qua `HrVersion` & `Employee` trong `hr_ui.py`, đồng bộ nhất quán với màn hình tự phục vụ `Thông tin cá nhân`.
- Kiểm thử: `ruff check` (`0` lỗi), XML (`14` file), `git diff --check`, Odoo tests `--test-tags /tp_hr_workspace,/tp_web_home` (`67/67` pass trên `18079`), HOOT `tp_hr_workspace` (`42/42` — `197` assertions trên `18079`), Playwright `verify_personal_tab.cjs` trên `18079`; backup `backup-main-v3` (`tp_tanphat_dev.dump` `8.534.446` bytes + `728` filestore files), upgrade `tp_hr_workspace` + `verify-post` (khớp 7 bảng) + `smoke_main.cjs` & `smoke_main_personal_tab.cjs` read-only pass trên `18069`.

## CHG-20261114-002 — UI-SHELL-UNIFY-001 (hoàn thiện theo xác nhận người dùng): Menu người dùng 2 mục & Thông tin cá nhân tự phục vụ đồng bộ HR (kèm CHG-20261114-001)

- Ngày: 14/11/2026 (Asia/Saigon). Quyết định: `DEC-043`.
- Phạm vi: `tp_web_home`, `tp_hr_workspace`, `tp_kd_workspace`, tài liệu (`UI_SHELL_UNIFY_001_ACCEPTANCE.md`, `UI_HOME_003_DESIGN.md`, `UI_HOME_004_ADMIN_DESIGN.md`, `UI_SHELL_AUTH_001_DESIGN.md`, `ROADMAP.md`, `DECISIONS.md`, `PROJECT_STATUS.md`, README 3 addon).
- Nội dung: Thống nhất Trang chủ thành một layout `#tp-unified-home` dùng chung (giữ lọc menu server + `user.isSystem`, bỏ fallback `hr.menu_hr_root` ở mục Quản lý nhân sự); tạo dịch vụ/component dùng chung `tp_identity` + `<TpUserAccountMenu>` tại `tp_web_home/static/src/identity/` (hỗ trợ live `tp.identity/changed`, fallback chữ cái, mở hồ sơ cá nhân qua registry `tp_personal_profile`, logout native); cập nhật `UserMenu`, `BurgerUserMenu` và sidebar HR/KH-KD còn đúng 2 mục **`Thông tin cá nhân`** và **`Đăng xuất`**; bổ sung màn hình tự phục vụ `tp_hr_workspace.action_my_profile` (`/odoo/my-profile`, `models/my_profile.py`, `controllers/my_profile.py`, `static/src/my_profile/`) giữ 6 tab đồng bộ trực tiếp allowlist thông tin cá nhân + ảnh đại diện về `hr.employee` của HR Admin, cho xem/tải hợp đồng của chính mình (`/tp_hr/my_contract/...`) và khóa chặt trường tổ chức/chức vụ/hợp đồng/ACL; thay `"Tài khoản"` cuối sidebar HR/KH-KD bằng `[Avatar] Họ tên` và ẩn `.o_user_menu`/`.o_mobile_menu_toggle` ở navbar khi mở workspace có sidebar; xóa `tp_hr_workspace/static/src/identity_navbar.js`.
- Kiểm thử: `ruff check` (`0` lỗi), XML (`44` file), `git diff --check`, Odoo tests (`80/80` pass trên `18079`, gồm 5 test `TestHrSelfProfile`), HOOT (`35/35` + `42/42` + `22/22` pass trên `18079`), Playwright `verify_test.cjs` + `verify_extra.cjs` trên `18079` (bao gồm E2E tự sửa hồ sơ cá nhân -> kiểm tra đồng bộ ngay bên Admin HR + RPC `AccessError`); backup mới `backup-main-v2` (`tp_tanphat_dev.dump` `8.528.298` bytes + `722` filestore files), upgrade + `verify-post` (khớp 7 bảng) + Playwright `smoke_main.cjs` read-only pass trên `18069`.

## CHG-20261113-009 — UI-INPUT-001: Chuẩn hóa ô nhập/chọn/ngày và avatar trong Danh sách nhân viên
- Phạm vi: chỉ giao diện; quyền, readonly, xác thực, guard và dữ liệu giữ nguyên.
  - Token chung `tp_web_home/static/src/inputs/input_tokens.css` (backend + `tp_web_login.assets_login`) và `inputs.scss`: khung 4 cạnh, hover/focus/lỗi/chỉ đọc/vô hiệu, mũi tên many2one luôn hiện, icon lịch, `*` theo `required`, viền trong cho dòng sửa của danh sách, khung m3 trên mobile, reduced motion.
  - 12 SCSS của HR/KD/login đổi màu cứng sang token.
  - `employee_list` dùng widget `tp_hr_identity` để hiện avatar trước tên, kèm `test_hr_ui.py`.
  - Version: `tp_web_home` 20.0.1.7.0, `tp_web_login` 20.0.1.4.2, `tp_hr_workspace` 20.0.1.11.4, `tp_kd_workspace` 20.0.1.9.1.
- Kiểm thử:
  - Odoo `/tp_hr_workspace,/tp_web_home` 0 failed/0 error of 73; HOOT HR + Home PASS; Ruff PASS; `git diff --check` exit 0.
  - Playwright 18079: trước/sau 4 viewport; bản cuối 1440/390; trạng thái lỗi/focus/dòng sửa/reduced motion; 0 lỗi mới.
  - Main: backup `backup-tp_tanphat_dev-20261113T122622455720Z` (601/656), rồi `-u` 4 module `--no-http`; smoke chỉ đọc 18069 có chặn ghi: 0 lỗi, 0 lệnh ghi.
- Tài liệu: [acceptance, danh mục màn hình, ảnh, rollback](demo/UI_INPUT_001_ACCEPTANCE.md); rollback source có kiểm tại `.local/ui-input001/rollback-source.zip`.

## CHG-20261113-008 — HR-UI-016: Bộ lọc phòng ban và thứ tự Ban Giám đốc trên Sơ đồ quản lý
- Phạm vi: `custom_addons/tp_hr_workspace` (`20.0.1.11.3`): `models/hr_ui.py` (`is_executive_department`, `_tp_role_rank`, `_tp_hierarchy_sort_key`, scoped `hierarchy_read`/`web_search_read` khi có context `tp_hr_hierarchy` để đưa Ban Giám đốc / Ban lãnh đạo, Giám đốc, Trưởng phòng lên đầu), `static/src/hierarchy/hierarchy.js`, `hierarchy.xml`, `static/src/profile/hr_ui.scss` (bổ sung dropdown `Lọc phòng ban` + nút `Xóa bộ lọc` đồng bộ 2 chiều với `SearchModel`, giữ thứ tự root trong `TpHrHierarchyModel._formatData`), `tests/test_hr_ui.py`, `static/tests/hr_mounted.test.js`.
- Kiểm thử: Ruff PASS; XML 13 files OK; `tp_tanphat_test` Odoo `/tp_hr_workspace` `61/61` PASS (`0 failed, 0 error`); HOOT `tp_hr_workspace` PASS (gồm test `tp_hr_hierarchy`); Playwright 18079 (`desktop` + `mobile` + department filter + order) PASS; backup `tp_tanphat_dev` (`601 tables, 656 blob references`) & `-u tp_hr_workspace` + khởi động lại daemon `18069` sạch; Playwright read-only smoke `HR-UI-016` & `HR-UI-015` trên `18069` PASS (`0 console/page errors`).

## CHG-20261113-007 — HR-UI-015: Giữ cố định thanh tiêu đề cột (sticky header) khi cuộn Danh sách nhân viên
- Phạm vi: `custom_addons/tp_hr_workspace` (`20.0.1.11.2`): `static/src/table/table.scss` (gim `thead` `position: sticky; top: 0; z-index: 5; background-color: #edf2f6`, hạ `.o_group_header th, td` xuống `position: static; z-index: auto;` và tạo flex scroll container `.o_list_renderer` cho cả desktop 1440px và mobile 390px).
- Kiểm thử: Ruff PASS; XML 13 files OK; `tp_tanphat_test` Odoo `/tp_hr_workspace` `60/60` PASS (`0 failed, 0 error`); HOOT `tp_hr_workspace` PASS; Playwright 18079 (`desktop` + `mobile` scroll check, 0 console/page errors) PASS; backup `tp_tanphat_dev` (`601 tables, 656 blob references`) & `-u tp_hr_workspace` main 18069 PASS; Playwright read-only smoke 18069 PASS (`0 console/page errors`).

## CHG-20261113-006 — HR-UI-015: Bỏ cột Thao tác trong Danh sách nhân viên và thanh phiên bản trên biểu mẫu hồ sơ

- Ngày 13/11/2026 Asia/Saigon, yêu cầu trực tiếp kèm hai ảnh; không commit/push; giữ nguyên các thay đổi `HR-UI-011`..`HR-EMP-014` có sẵn trong working tree. `tp_hr_workspace` 20.0.1.11.0 → 20.0.1.11.1.
- Gỡ 2 nút `action_open_account_dialog` (`Quản lý tài khoản` / `Tạo tài khoản`) khỏi `employee_list` trong `custom_addons/tp_hr_workspace/views/workspace.xml` (loại bỏ cột `Thao tác` khỏi Danh sách nhân viên, giữ nguyên trong chi tiết hồ sơ và giữ `Bổ sung hồ sơ` khi `tp_hr_missing`). Ẩn `//header/field[@name='version_id']` (`versions_timeline`) trong `employee_form` và đặt `.o_tp_hr_employee_form .o_form_statusbar { display: none !important; }` trong `employee_profile.scss` để bỏ thanh ngày phiên bản/dải trắng phía trên sheet (vẫn giữ nút `Phiên bản hồ sơ` và tab `Hợp đồng lao động`). Dọn selector `.o_tp_hr_account_btn` ở `table.scss`.
- Kiểm: Ruff `All checks passed!`, XML 13 tệp OK, Odoo `-u tp_hr_workspace --test-tags /tp_hr_workspace` trên `tp_tanphat_test` (0 failed, 0 error(s) of 60 tests, gồm test view mới ở `test_hr_ui.py`), HOOT `tp_hr_workspace` passed, Playwright 18079 và read-only smoke 18069 đạt 0 console/page errors; đã đối chiếu ảnh 1440×810 trên cả 18079 và 18069. Backup main `backup-tp_tanphat_dev-20261113T080624475611Z` → `-u tp_hr_workspace --no-http`.

## CHG-20261113-005 — HR-EMP-014: Loại hình lao động, giấy tờ hợp đồng và lịch sử HR

- Ngày 13/11/2026 Asia/Saigon; yêu cầu trực tiếp cho phép triển khai/test18079 → backup/restore → áp18069. HR 20.0.1.11.0 thêm phân loại nullable theo hr.version/employee related, giữ ngày lao động/fixed_term native. Model HR tối thiểu giữ metadata, tệp/phụ lục và ngày thuê khoán; 2 ACL HR/company/employee access, private attachment và restrict/delete preview. Phiên bản dùng chung giấy tờ đúng kỳ; link sau native create, hộp thêm validate nguyên tử. Không đổi account/password/role/mã/chuyển phòng/xóa.
- Hồ sơ sáu tab, thêm Hợp đồng lao động; current/past/future, giấy tờ và empty state, không state ký/hiệu lực/lương. Cột job → kind → phone, giữ HR-LIST-013. Ba tiêu chí hồ sơ thiếu dùng chung với KPI/drilldown/XLSX; ghi chú/lý do/nút sửa/empty rõ. Lịch sử scoped summary/i18n giữ raw body/audit; event mới dễ đọc + private audit. Menu báo cáo trùng inactive, Tổng quan giữ chart/table/Xuất Excel nhân sự. Mobile badge xuống dòng để tên rõ.
- Kiểm cuối: Odoo 86/86; HOOT HR40/190 assertions, Home31/179; browser test11 nhóm + delta past/future/filter/upload/delete/missing/empty; main6/6 chỉ đọc/Hủy và export button/drilldown/active menu cả hai cổng, 0 errors trong luồng đã thử. Bốn viewport, keyboard/reduced motion và mở ảnh tự đánh giá. XLSX đọc lại 10 cột/literal/filter/time/scope/tổng, main unknown40/missing1. Ruff/XML13/JS syntax/diff PASS; source67 seal. Lỗi default_get/copy có regression/rerun; log fail và GC WinError5/markdown2/hết phiên browser được ghi riêng.
- Restore mainA → test exact600 tables/666 refs/432 sequences + neutralize. Rollback B073121361307Z trước014; correction C074320617876Z, noHTTP upgrade sau zero DB sessions. Gate fail dừng/reapply độc quyền. Archive B600 original columns: 577 rowsets nguyên, 23 delta metadata/vận hành; policy953 ACL cũ +2 mới/57 groups/28 users gồm password/73 partners/632 nonasset blobs giữ. Main40 employee/28 user/9 active/15 phòng, 0 fixture/0 paper/new fields NULL. [Acceptance/ảnh/giới hạn](demo/HR_EMP_014_ACCEPTANCE.md), [guide](demo/HR_EMP_014_USER_GUIDE.md), [schema/quyền](security/HR_EMP_014_SCHEMA_AND_ACCESS.md), [rollback](../ops/runbooks/HR_EMP_014_DEPLOY_AND_ROLLBACK.md). Chưa người dùng nghiệm thu visual/business/pilot; không stage/commit/push, DB thứ ba, restore test đè main hoặc React/API/core.

## CHG-20261113-004 — HR-LIST-013: Cố định nhóm phòng ban, bỏ facet phòng ban mặc định

- 13/11/2026, phản hồi trực tiếp sau012 kèm2ảnh: phòng ban là cách trình bày cố định của danh sách cũ. Scoped HrListModel giữ department_id đầu groupBy trước native cache/config; bỏ default_group_by và bộ chọn group-by phòng ban. Xóa tìm kiếm/bộ lọc/nhóm phụ vẫn giữ nhóm phòng ban, ẩn cột phòng từng dòng; domain search theo đơn vị và các màn HR khác giữ.4file application/test; HR20.0.1.10.2, không backend/ACL/API/schema/data.
- Kiểm XML/JS/upgrade, Odoo3/3, HOOT HR39/Home31 PASS; browser9/9 mỗi cổng0errors/4viewport, khôngfacet/xóasearchgiữnhóm/backendpaging/detailback/isolation. HOOT callback/selector và harness paging race sửa/rerun đạt. Backupmain **backup-tp_tanphat_dev-20261113T060634715405Z**600/666; dừng đúngmain→0session→HRupgrade guard noHTTP→bảo toàn→start/smoke.588/600rowsets nguyên trướcHTTP,583sau; business/auth/953ACLpolicy/57groups/632nonassetblob giữ. Reuse restore rehearsal011 cùngschema, khôngDB/fixture mới/test→main.
- [Acceptance/ảnh/rollback4file](demo/HR_LIST_013_ACCEPTANCE.md), status/roadmap/README/guide cập nhật và ghi superseded cơ chế grouping012. Tựreview/mobilegiảlập,visual/business/pilot riêng; khôngstage/commit/push.

## CHG-20261113-003 — HR-LIST-012: Trả danh sách nhân viên về kiểu nhóm cũ

- 13/11/2026, phản hồi trực tiếp sau011 theo2ảnh: native default group phòng ban, dải #CBF3F7 và số thành viên; ẩn cột phòng ban trong từng dòng khi group. Bỏ intro/avatar/nút Xem hồ sơ dư; trả cột chữ và badge/nút native. Bấm tên mở hồ sơ; account guard/menu chung/các màn khác giữ. `tp_hr_workspace`20.0.1.10.1;8file application/test, không backend/ACL/API/schema/data.
- Kiểm: XML2/JS/upgrade, Odoo3/3, HOOT HR38/171assertions và Home31/179, browser9/9 mỗi cổng0errors tại4viewport/group/backend paging/search/detail-back/isolation; cặp ảnh main1440 đã mở tự xem. Backup main **backup-tp_tanphat_dev-20261113T043425236788Z**600/666; gate từ chối khi process main cũ còn DBsession, sau kiểm config/đóng đúngPID→0sessions→upgradeHRnoHTTP đạt. Runtime ngoài task mở sauupgrade được dùng lại, không start trùng.588/600rowsets nguyên trướcHTTP,583sau smoke; business/auth/ACLpolicy/57group/632nonassetblob giữ. Reuse restore rehearsal011 cùngschema; khôngDB/fixture mới/test→main.
- [Acceptance, ảnh và rollback riêng012](demo/HR_LIST_012_ACCEPTANCE.md), guide/README/roadmap/status cập nhật; rollback8file+upgrade1.10.0. Hoot/browser lượt cuối đạt; harness page-size race/CSS specificity đã sửa và rerun, không tính fail là pass. Tựreview/mobilegiảlập; visual/business/pilot riêng. Không stage/commit/push.

## CHG-20261113-002 — HR-UI-011: Thống nhất danh sách và thiết kế lại các màn hình TP HR

- 13/11/2026 Asia/Saigon, yêu cầu trực tiếp thiết kế/triển khai/test/backup-restore/áp 18069 trong tệp đính kèm. Ngoại lệ vai trò điều phối chỉ task này; không stage/commit/push. `tp_hr_workspace` 20.0.1.10.0, giữ dirty HR-DELETE-010/UI-HOME-005 có trước; không thay core/React/API/ACL.
- Một menu Danh sách nhân viên; inactive menu/nhóm trùng, giữ XML ID/action/dữ liệu. Bảng dùng chung scoped, backend tìm/lọc/sắp xếp/nhóm/phân trang 10/20/50/100 thật, count nhóm/clear/empty/error. Hồ sơ 5 tab, rõ chế độ xem/sửa/lưu/hủy/cảnh báo chưa lưu và nút mobile; form danh mục; count đúng active/company/rules không sudo; hierarchy theo parent/child thật; nhập 4 bước UI trên 3 state, giữ result/lock/retry; đổi tên Nhãn nhân viên. 12 file sửa, 7 mới, seal 63 file và rollback 56 file gốc.
- Kiểm: Odoo **77/77** bản cuối và **77/77** sau restore; HOOT HR 37 tests/163 assertions (HR35+KD2), Home 31/179 (Home30+KD1). Browser 16 nhóm + catalog/import 5 + protected 2 đều 0 errors; smoke bản sao sạch/main **25/25 mỗi cổng**, 0 errors/0 business write. Ruff/XML12/JS/diff đạt. 60 cặp before/after-verified cùng role/route/dataset/4 viewport đã xem; final-source có 60 ảnh bổ sung sau test import, không tuyên bố dataset khớp.
- Ops: backup main A `032204623692Z` → backup test `032901396088Z` → restore khớp 600/666/432 → neutralize → 77 tests. Backup B cuối **`backup-tp_tanphat_dev-20261113T033657607572Z`**, 600 bảng/666 blob. Main mở lại ngoài task; gate 0 sessions đầu fail nhưng lệnh upgrade vẫn chạy. Đã ghi lỗi điều phối và chạy lại exact stop → 0 sessions → upgrade HR noHTTP trong cùng guard → HTTP còn dừng → đối chiếu → start/smoke đạt. 585/600 rowsets nguyên trước HTTP, 579 sau smoke; delta chỉ metadata/vận hành. 953 ACL giữ policy, 57 group/632 nonasset blob và hồ sơ/auth/role/grant/mapping/mã/import giữ. Hai phòng mới giữa A/B được giữ. Main 40 employee/28 user/9 active/15 phòng/1 HEAD; test 40/28/9/13/1; không fixture UI011 trên runtime sạch.
- [Acceptance/URL/ảnh/test/giới hạn](demo/HR_UI_011_ACCEPTANCE.md), [design](ui/HR_UI_011_DESIGN.md), [rollback](../ops/runbooks/HR_UI_011_DEPLOY_AND_ROLLBACK.md), guide/README/roadmap/status đã cập nhật. Rollback chỉ source chưa đủ metadata; dùng backup main B sau đánh giá giao dịch mới. Tự review vì subagent model không khả dụng; mobile giả lập, chưa kiểm extension autofill; visual/business/pilot riêng. Warning GC WinError5/markdown2/icon/Image không thành test failure, blob kiểm riêng. Hai runtime đang chạy; không commit/push.

## CHG-20261113-001 — UI-HOME-005: Làm mới giao diện Trang chủ quản trị và navbar theo thiết kế mẫu

- Ngày 13/11/2026 Asia/Saigon, yêu cầu trực tiếp; không commit/push. Nâng cấp `tp_web_home` 20.0.1.5.0 → 20.0.1.6.0 (`home_launcher.xml`, `home_launcher.scss`, `shell_navbar.scss`, `__manifest__.py`, `static/tests/home/home_launcher.test.js`, `README.md`), giữ nguyên model, ACL, API, core, `UI-HOME-003` cho non-admin và các selector kiểm thử.
- Giao diện: nền gradient xanh băng toàn màn hình cùng SVG sóng chéo góc dưới-phải (`tp-bg-waves`), header với 3 nút pill nổi, thanh nhấn xanh dọc ở tiêu đề mục, bố cục thẻ ngang (icon 52×52 bên trái + tiêu đề/badge/mô tả bên phải) trong lưới 3 cột đều cho 5 phòng ban và 2 cột cho Nhân sự (`Đang hoạt động` bạc hà) & Tuyển dụng (`Đang phát triển`), nút Home viền bo góc, vạch phân cách dọc và avatar tròn ở navbar trên desktop.
- Kiểm: Ruff, XML 6 tệp, `tp_tanphat_test` `-u tp_web_home --test-tags /tp_web_home` (0 failed/0 error of 12 tests), HOOT `tp_web_home` (passed), Playwright 18079 (5 viewport, reduced-motion, panel Tất cả ứng dụng, điều hướng và non-admin 0 console/page errors). Backup `tp_tanphat_dev` (`backup-tp_tanphat_dev-20261113T020519252575Z`) → upgrade `tp_web_home` `--no-http` → khởi động lại `18069` → Playwright read-only smoke đạt 0 errors; đã đối chiếu ảnh 1440×810 trên cả 18079 và 18069.

## CHG-20261112-016 — HR-DELETE-010: Xóa vĩnh viễn nhân viên có xác minh lại mật khẩu admin

- Ngày 12/11/2026 Asia/Saigon, yêu cầu trực tiếp; không commit/push. DEC-042 thay phần xóa hồ sơ của DEC-041. `tp_organization` 20.0.2.2.0, `tp_hr_workspace` 20.0.1.9.0. Tác vụ “Xóa vĩnh viễn nhân viên” thay “Xóa hồ sơ nhập nhầm”: hộp thoại OWL trong Dialog native (Sẽ xóa/Giữ lại/Đang chặn, lý do, cảnh báo nguyên văn, mật khẩu của chính admin, nút đỏ/Hủy), bỏ wizard transient để mật khẩu không vào DB. “Lưu trữ” giữ riêng.
- Backend: kế hoạch xóa dùng chung cho xem trước và thực thi; kiểm admin/HR manager/công ty và mật khẩu native (`_check_credentials`, giới hạn thử sai) ở mọi yêu cầu; khóa advisory, `FOR UPDATE`, so digest, rollback toàn bộ, idempotent theo request ID. Xóa thật `hr.employee` cùng sidecar tự sinh qua ORM; dòng/lô/file nhập Excel giữ, nhập lại danh tính đã xóa thành xung đột; dữ liệu độc lập chặn có gợi ý; tài khoản giữ mặc định hoặc khóa (kết thúc phiên, thu hồi vai trò/nhóm phạm vi), không xóa tài khoản. Audit `permanent_delete` thêm mã nguồn/request/tài khoản/kết quả xác minh, không lưu mật khẩu.
- Kiểm: 18079 Odoo 74 tests 0 failed/0 error, Ruff/XML/diff, HOOT 33/149 + Home 30/173, Playwright dữ liệu giả 30/30 0 lỗi, DB 0 mồ côi/0 mật khẩu; lượt lỗi Odoo 1–3/HOOT 1/trình duyệt 1–2 đã sửa, không tính. Diễn tập main A→test 600/661/432, upgrade, 74 tests đạt, delta metadata. Main backup B `141836737342Z` → upgrade → smoke chỉ đọc/Hủy 8/8, 0 yêu cầu xóa; main không xóa/khóa hồ sơ hay tài khoản nào. Rollback 12 file gốc + 5 file mới. Chưa làm quy tắc hạ trưởng phòng trước khi chuyển.

## CHG-20261112-015 — SOURCE-CLEANUP-001: Kiểm kê, lưu trữ và dọn dẹp file không cần thiết

- Ngày 12/11/2026 (Asia/Saigon), task SOURCE-CLEANUP-001; không commit/push. Lập manifest kiểm kê chi tiết tại `.local/source-cleanup001/manifest.json` và `manifest.md`; chạy dry-run trước khi thực hiện.
- Lưu trữ bảo toàn 92 tệp (10.43 MB) sang `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934` (kiểm 92/92 SHA-256 và ghi `recovery-mapping.json`) trước khi đưa khỏi workspace: 35 prompt cũ đã hoàn thành (giữ 2 prompt hiệu lực và lập chỉ mục [docs/prompts/README.md](prompts/README.md)), 52 tệp render cuối/so sánh ấn bản và 5 tệp ghi chú nghiên cứu ban đầu.
- Xóa 5.907 tệp (534.26 MB) đã xác minh an toàn: `.ruff_cache`, `__pycache__` trong vùng custom/công cụ, `.tmp` (`.local-setup-output.tmp`, `.local/c1-access.tmp`), bản render/ảnh nháp trung gian/trùng lặp, và 14 browser profile/cache tạm của Playwright thuộc các task đã hoàn tất. Tổng đưa ra khỏi source 544.68 MB; dung lượng trống ổ C thực tế giải phóng 541.64 MB (16.51 GB → 17.04 GB).
- Giữ nguyên toàn bộ phần bảo vệ (`.git`, `odoo/`, `addons/`, `custom_addons/`, `.venv/`, `deliverables/`, `scripts/`, tests, `frontend/node_modules`, `.local/postgres/data`, filestore 18069/18079, logs đang mở, rollback packages gần nhất, `ops-clean001/database-archives/`, `.local/git-baselines/`). Các thư mục `.local/<task>/data`, `.local/hr001`, `.local/ops-001/rehearsals` giữ lại do đối chiếu archive có sai lệch số lượng blob hoặc có tham chiếu tài liệu.
- Kiểm chứng: `recovery-mapping.json` 92/92 SHA-256 đạt; cổng 18069 HTTP 200 `/web/login` và assets; cổng 18079 đăng nhập read-only `focus009.admin` và HTTP 200 `/odoo`; `git diff --check` đạt. Không thay đổi dữ liệu DB, tài khoản, quyền hay cấu hình.

## CHG-20261112-014 — HR-AUTH-FOCUS-009: Autofill sidebar và focus xác minh tài khoản

- Ngày12/11/2026 Asia/Saigon, yêu cầu triển khai trực tiếp, không commit/push. HR20.0.1.8.1/Login20.0.1.4.1. Chrome157 password manager thật với credential giả tái hiện trusted input/change tự điền username vào sidebar dù focus ở password; chỉ type=search chưa đủ. Form search riêng/id/name/type đúng semantic giải quyết, giữ filter rỗng/có sẵn. Không credential giả trong DOM hoặc xóa filter sau dialog.
- Tái hiện thêm focus body sau sai mật khẩu/hủy: controller native focus password enabled trước RPC để error dialog khôi phục đúng ô; UI bus trả opener; native autofocus form tạo/reset; sidebar nhường focus cho dialog. Không đổi backend/auth/600s/CSRF/session/MFA/transaction, danh tính, quyền hoặc DEC-040; hạ riêng trước chuyển là phương án đổi quy trình, không phải lỗi hiện hành.
- Kiểm: saved Chrome password8nhóm/0errors (create/reset/login, đúng/sai/retry/cancel/expiry, clipboard, Enter/Tab/Shift+Tab/Escape, filter empty/existing, desktop/rail/mobile). HOOT18079/18069 đều25tests105assertions gồm4testmới; XML13/manifest2/Node syntax/diff đạt. Không backend Odoo/React tests vì không sửa phần đó. Backup main120334281779Z600bảng661blob→upgrade2addon→main smoke4nhóm0errors chỉ đọc/Hủy;9bảng nghiệp vụ và nhóm/grant/role nguyên; source seal khớp. Hai runtime chạy, fixture giả giữ riêng test; rollback9fileđổi+3filemới từ archive66gốc có hash. Password manager mới kiểm Chrome tích hợp headless, chưa extension/browser khác/mobile thật. [Acceptance](demo/HR_AUTH_FOCUS_009_ACCEPTANCE.md), [rollback](../ops/runbooks/HR_AUTH_FOCUS_009_DEPLOY_AND_ROLLBACK.md). Next: Ctrl+F5 main, sử dụng luồng và phản hồi nếu browser/extension khác tái hiện; visual/business/pilot riêng.

## CHG-20261112-013 — HR-CORRECTION-008: Xóa hồ sơ nhập nhầm, mã nhân viên, Việt hóa, thu gọn

- Ngày 12/11/2026 Asia/Saigon, yêu cầu trực tiếp. `tp_organization` 20.0.2.1.0, `tp_hr_workspace` 20.0.1.8.0; nạp lại `tp_i18n_vi`/`tp_web_home`. “Xóa hồ sơ nhập nhầm” chỉ admin cùng công ty: backend kiểm điều kiện, lý do bắt buộc, lô tất cả-hoặc-không, audit độc lập; hồ sơ đã dùng bị chặn kèm lý do tiếng Việt và gợi ý lưu trữ. Native Delete/RPC/context bị chặn, binding xóa của `hr_timesheet` gỡ, không cascade user/partner/tài liệu.
- Mã nhân viên: nguyên nhân `employee_sequence.xml` number_next=20000 noupdate. Sửa thành mã hợp lệ cao nhất (gồm lưu trữ/audit)+1, khóa advisory, unique giữ; migration đổi mã nhập tay chưa dùng có audit, xung đột chỉ báo cáo. Main/test: id 67 `TP20000→TP10070`, mã kế tiếp TP10071. Migration HR chuyển 1 tài khoản cá nhân en_US sang vi_VN.
- Việt hóa 111 mục overlay (action HR/project, chuỗi `web` còn thiếu), bộ đếm “Đã chọn 1 hồ sơ”, xác nhận có nút cụ thể. Thu gọn bằng token SCSS: navbar 56→48, ô nhập 46→36.5/15px, chi tiết HR 1280 772→684px, dòng KH-KD 49.7→43.7; root font/zoom giữ, sidebar giống hệt (chỉ thêm mục nhật ký), mobile ≥44px.
- Kiểm: 18079 Odoo 84 tests 0 failed/0 error, Ruff/XML/diff, HOOT 30/173-21/86-22/85, browser xóa/chặn/lưu trữ bằng dữ liệu giả, người dùng thường, zoom 200%, 18 điểm Tab, layout 8 route×4 viewport, 0 lỗi console. Diễn tập backup main→test 597/653/430 khớp, neutralize, upgrade, 191 tests đạt. Main backup cuối 101939483900Z→upgrade→smoke chỉ đọc/Hủy; delta bảng/cột bằng diễn tập. Main không xóa/lưu trữ hồ sơ nào. Rollback 26 file gốc+10 file mới, zip/hash. Gap còn: hộp xóa native model khác có văn phong vui của catalog `web`. Tự review, không stage/commit/push. [Acceptance](demo/HR_CORRECTION_008_ACCEPTANCE.md), [runbook](../ops/runbooks/HR_CORRECTION_008_DEPLOY_AND_ROLLBACK.md).

## CHG-20261112-012 — IDENTITY-ORG-001: Khóa gán chéo phiên bản HR

- Ngày12/11/2026 Asia/Saigon, cùngtask011. Chặn current_version_id khác chủ hồ sơ dù cùng phòng, chặn rebind hr.version.employee_id và company sai khi tạo version; native back-link ban đầu của version chưa có owner vào employee chưa có lịch sử vẫn được giữ. Thêm regression có same-departmentforeignversion/historyrebind/company. Không schema/assets/menu/datachange, HR20.0.1.7.0 giữ.
- HRfilter41tests0failed0errors (`backend-version-final2.log`), Ruff/cleanbrowser5mỗicổng0errors/source209seal/preservation88rowsets-auth627blobPASS. Guardđầu4setUpClass fail vì chặn nativebacklink đã sửa/rerunđạt trướcmain; không tính fail là pass. Reuse restore596/653/429 và HEAD/KD109/HOOT21-29 của011 do scopekhôngđổi. Exactmainstop/backup080056033059Z(597tables653blobrefs)/restart/smoke, khôngupgrade/restore/seed/quyềnngườithật. Rollback2fileversion012→011 zip/hash riêng, khôngresetdirtyworktree; toàntask16fileđổi9mới. Status/acceptance/architecture/security/workflow/runbook cập nhật. Khôngstage/commit/push. Next: adminreview18069; visual/business/pilot riêng, selfreviewkhôngauditđộc lập.

## CHG-20261112-011 — IDENTITY-ORG-001: Danh tính chung và chuyển phòng có kiểm quyền

- Ngày12/11/2026 Asia/Saigon. Thực thi trực tiếp của người dùng; HR20.0.1.7.0: officialnameHR, ảnh2chiều/fallback/navbarbus, mappingIDduynhất/workcontactpartner/privateemailguard. Chuyển phòng ngay bằng adminpreview/lýdo/kiêmnhiệm/bàngiao/locks/freshsnapshot/savepoint/audit/sessionrevision; defaultstaff/revokeHEAD-old/assignment-grant-CRM, incumbentHEAD/multicompany/future/history/directwrite/contextguard. Servermenu/action/dashboard/report cùngscope, projectcapability data/tiền/tệp giữ; generic own-departmentworkspace, admin tools/profilecompact/sidebar giữ. DEC040/workflow/security/guide/acceptance/runbook/roadmap/status/README đã cập nhật.
- Test: baselineHR26; sourcecuối HRfilter40 và saurestoreHEAD/KD109tests0failed0errors, HOOTHR21/86-Home29/166, Ruff/XML8/diffPASS, browserfixture7/race2→1/freshcursorstale/clean5mỗicổng/profile7viewports0errors. Các lượt KDfixture cũ chưa explicit scope, outsider policy mới, fixture signed_date thiếu và harness nhãn/selector đã sửa rồi rerun; giữ failevidence, không hạguard/constraint. Mobile giảlập, tựreview do modelsubagentkhôngkhảdụng; business/visual/pilot riêng.
- Restoremain072712247123Z→test596rowsets653blobrefs429sequence khớp, neutralize/upgrade/test; fixturegiả bị loại. Gỡ đúng transient/FKtargetdepartment mới saubackup/kiểm, khôngCASCADE; lượtđầuFKblocked đã ghi. Main exactstop/backup074626870983Z→upgradechỉHRnoHTTP/reconcile/start/smoke; previewtextpolishcuối testHR40/cleanbrowser, backup075053704012Z/restartkhôngschema. Source209files6addons seal, rollback16đổi9mới. Main40employee thay39status010 đã ghi drift trước task, khôngxóa/restoreép bằng.
- Main7identity reconcile theoID đã thửtrêntest:4accountnames theoHR,1ảnh thật account→HR/6fallback,0pending/conflict/mismatch. Auth/login/MFA/ID/mapping/department/job/role/grant/snapshot thậtgiữ;88rowsets/627nonassetblobpreservation đạt với delta tên/ảnh/native-derivedname/timestamp+1adminACLmới táchrõ. Cả2DB40employees27users7mapping/1HEAD; GCWindowswarning có blobSHA/sizekiểmriêng. KhôngDBthứ3/restoretest→main/stage/commit/push. Next: adminreview18069 theo [guide](demo/IDENTITY_ORG_001_USER_GUIDE.md); [acceptance](demo/IDENTITY_ORG_001_ACCEPTANCE.md) ghi test/ảnh/giới hạn.

## CHG-20261112-010 — HR-COMPACT-007: Thu gọn chi tiết nhân viên

- Ngày12/11/2026 Asia/Saigon. Theo phản hồi trực tiếp, giảm avatar110→88px, tên tối đa40→32px, tab17→15px, thông tin17→16px và khoảng cách; sheet1672 từ852.5→715px (16.1%). Giữ sidebar006 và modal005, mobile nút chức vụ44px. Sửa min-width nhóm action native gây tràn toolbar1280px; chỉ SCSS/README, không model/quyền/API/schema/manifest change.
- Kiểm: compact2nhóm + sidebar5nhóm mỗi18079/18069,7viewport1672–320,0console/pageerror; tab/edit-cancel/account/role-cancel/mở-thu/reload/drawer đạt. Before–after main cùngrole/dataset/viewport đã xem. Asset compile thật; không chạy backend/HOOT/DBupgrade cho CSS. Một lượt cold-start session timeout, rerun tuần tự đạt; lỗi tràn trước sửa không tính pass.
- Test đạt → seal53file → exactmainstop/backup063854566975Z(596tables/643blobrefs) → restart/main smoke đạt. Main79bảng617nonassetblob khớp snapshot đầu, ACL0delta; haiDB39employee27user7mapping1HEAD giữ. Rollback2filegốc SHA256; reuse restore rehearsal005 cùngschema, không restore/fixture/DBthứ3. Status/guide/design/roadmap/runbook/[acceptance007](demo/HR_COMPACT_007_ACCEPTANCE.md) cập nhật. Chỉ tự review vì model subagent không khả dụng; mobile giả lập/visual-business-pilot riêng. Không stage/commit/push. Next: Ctrl+F5/review độ gọn18069.

## CHG-20261112-009 — HR-SIDEBAR-006: Giữ sidebar khi mở chi tiết

- Ngày12/11/2026 Asia/Saigon. Phản hồi trực tiếp sửa lựa chọn005: bỏ trạng thái/hook/bodyclass/nhánh hrProfileLayout và CSS palette/rail riêng; sidebar giữ màu/chiều rộng/mở-thu theo preference chung, chỉ vùng nội dung hồ sơ đổi. Giữ profile/modal005 và backend/HEAD004; không XML/Python/manifest/API/schema change, HR20.0.1.6.0/login20.0.1.4.0 giữ.
- Kiểm: HOOTHR filter21tests86assertions(gồm2KD)/Home29tests166assertions đạt; browser5nhóm mỗi18079/18069 exact sidebar style/list-detail-account/back/manualcollapse-expand/reload/mobile390 đạt0errors; before/after cùngadmin/employee63/1672×1040 đã xem. Không chạy backend/upgradeDB cho staticfix. Restarttest→testđạt→exactmainstop/backup062555343599Z→restart/assets/smoke; reuse restore rehearsal005 cùngschema, không restore DB/fixture/DBthứ3.
- Source53seal/main79bảng617blob khớp snapshot đầu, ACL0delta, cả2DB39employee27user7mapping1HEAD giữ. Rollback6filegốc SHA256. Status/guide/README/design005/roadmap/runbook/[acceptance006](demo/HR_SIDEBAR_006_ACCEPTANCE.md) cập nhật, private `.local/hr-sidebar006/`. Harness đầu wait visible chohidden sai đã sửa/rerun đạt; subagent modelkhông khảdụng/chỉtựreview, mobile giảlập/visual-business-pilot riêng. Không stage/commit/push. Next: Ctrl+F5/review sidebar18069.

## CHG-20261112-008 — HR-PROFILE-005: Hồ sơ và quản lý tài khoản theo ảnh mẫu

- Ngày12/11/2026 Asia/Saigon. Yêu cầu trực tiếp tiếp tục taskHR/quyền thực thi-test-backup-restore-áp main; HR20.0.1.6.0/login giữ20.0.1.4.0. Hồ sơ nền xanh băng/sheet trắng/avatar/tên lớn/metadata icon/5tab icon/2card/footer; native rail teal transient không ghi preference, reset khi unmount. Modal2cột/nhãnViệt/ô lý do/nút khóa-mở-reset-Đóng và xác nhận khóa tiếng Việt; mobile1cột/focus/reduced motion. Giữ shared native navbar/menu/version/history, backend account/identity/protected-user và mộtHEAD004. Không React/API/model/ACL/core change.
- Kiểm thực: XML10/upgrade đạt; backend sau restoreHR26/0/0, HOOTHR filter22tests90assertions (gồm2KD)/Home29-166 đạt. Browser6nhóm mỗi cổng18079/18069 desktop1672/modal1024-390-320/profile390-320 đạt0errors; fixture3nhóm khóa-mở-xác nhận khóa/unlinked-identity-credentials-cancel đạt. Browser005 không đặt mật khẩu mới; guard/backend giữ test. SQL uniqueHEAD/0duplicate2DB; ảnhmain trước-sau cùng actor/route/dataset/viewport đã mở xem.
- Rehearsal main055849147435Z/testbackup060701112831Z, restore596rowsets643blobrefs429sequences khớp/neutralize/test lại; fixture đã loại. Main exactPIDstop/backupcuối061141441037Z/upgrade chỉHRnoHTTP/start/smoke. Seal53file/617nonassetblob;79bảng khớp backupcuối trước apply, ACL chỉ2write metadata. HaiDB39employee27user8active13phòng7mapping1HEAD. Snapshotđầu task có2write_date drift employee63/resource64 trước apply, nguyên nhân chưa quy thuộc; soarchive có fingerprint khớp đầu chỉ2timestamps đổi, không báo raw equality/không sửa baseline. Sauapply79bảng kểcảwrite_date khớp backupcuối.
- Status/roadmap/guide/README/design/acceptance/runbook cập nhật, evidence private `.local/hr-profile005/`; rollback53filegốc0filemới, giữ index/policy004. Lượt backend đầu5teardown lỗi ReadOnly uploadtest, sửa thuộc tính đúngfile/rerun đạt; GCassetrename/markdown2warning còn, blobkiểm riêng. HOOT import/selector timing/fixture encoding sửa và rerun; giữ logfail. Chỉ tự review vì subagentmodel không khả dụng; mobile giả lập, visual/business/pilot chờ người dùng. Không stage/commit/push. Next: review18069 chi tiết và Quản lý tài khoản.

## CHG-20261112-007 — HR-POSITION-004: Đổi chức vụ trong chi tiết và một trưởng phòng

- Ngày12/11/2026 Asia/Saigon. Yêu cầu trực tiếp tiếp tục taskHR, quyền thực thi/test/backup-restore/áp main trong task; không stage/commit/push. Bỏ Đổi chức vụ khỏi list và CSS xếp hai nút; giữ ngay dưới tên trong chi tiết. HR20.0.1.5.0/login giữ20.0.1.4.0, không React/API/core/project source.
- Extension modelrole hiện có thêm unique index company/department WHEREactive, một HEAD chưa thu hồi giữ vị trí dù user khóa hoặc thời hạn chưa tới/hết. Preview/apply bổ nhiệm người khác báo tên trưởng phòng hiện tại và yêu cầu hạ trước; không tự thay thế. Snapshot thêm HEAD của phòng/cursor mới; chặn provisioning trực tiếp/reactivation/race, giữ scope/revocation/audit. Job HR không tự cấp quyền; không mở bộ quyền phòng khác/model/ACL mới. Preflight main0duplicate scope, không sửa người thật để upgrade.
- Test: final HR26ca0failed0errors sau restore, HEAD regression4ca0failed0errors; HOOTHR20tests83assertions/Home29tests166assertions đạt. Browser8nhóm và HTTP2session/2promotion→1success/1deny/1HEAD đạt; clean smoke4nhóm mỗi cổng18079/18069 desktop/mobile/focus/nooverflow/cancel đạt0errors. Ruff/XML10/diff đạt; unique index/0duplicate scopes xác nhận cả2DB, ảnh thật đã mở tự đánh giá.
- Rehearsal backup051846939786Z, test backup051912135070Z/restore596rowsets643blobrefs429sequences khớp rồi neutralize/test lại; fixture đã loại. Main backup cuối052315995362Z sau exactPIDstop; upgrade chỉHRnoHTTP/start/smoke. Seal53file,79bảng617nonassetblob bảo toàn; ACL policy giữ,2write_date đổi. Cả2cổng39employee27user8active13phòng7mapping1HEAD; không đổi job/account/password/role/grant thật, không DBthứ3/restore test sang main.
- Cập nhật status/roadmap/DEC039/workflow/guide/security/design/acceptance/runbook/README. Rollback53filegốc0filemới; trả policy003 cần migration gỡ đúng index mới đã review, source rollback không tự gỡ. Evidence private `.local/hr-position004/`. Fixture/selector/picker và import lỗi đã sửa/rerun; một race chồng lúc browser đang đợi được rerun tuần tự. Clean smoke cùng HOOT gặp500 asset WinError5; lượt chạy riêng sau đó đạt0errors, không tính fail là pass. GC/markdown2warning còn; chưa điện thoại thật/audit độc lập do subagent model không khả dụng. Next: người dùng review18069, visual/business/pilot riêng.

## CHG-20261112-006 — HR-POSITION-003: Đổi chức vụ và bổ nhiệm/hạ quyền dễ tìm

- Ngày12/11/2026 Asia/Saigon. Phản hồi trực tiếp tiếp tục task HR-ACCOUNT-ROLE-001 và quyền thực thi/test/áp main trong task; không stage/commit/push. HR20.0.1.4.0 native Odoo/custom addon; login giữ20.0.1.4.0, không React/API/core.
- Nút Đổi chức vụ trên từng dòng và đầu hồ sơ, tái dùng role wizard. Nhánh đổi job HR dùng được khi chưa account, job active đúng company/phòng hoặc danh mục chung, lý do/preview/xác nhận/audit; quyền giữ nguyên. Nhánh quyền có lựa chọn Bổ nhiệm Trưởng phòng / Trưởng ban KH-KD hoặc Chuyển về Nhân viên KH-KD, tùy chọn đổi cả chức vụ nguyên tử. Giữ adapter/guard/revocation staff↔HEAD; digest gồm change_kind, khóa/snapshot mới, chặn dữ liệu/lựa chọn đổi sau preview. Không thêm model/ACL/bộ quyền phòng khác.
- Test: Odoo HR24ca0failed0errors trước/sau restore; login backend không chạy lại. HOOT sau restore HR20tests83assertions/Home29tests166assertions; browser fixture6nhóm và clean smoke4nhóm mỗi cổng18079/18069 đạt0console/pageerror. Đã kiểm cấp access đúng scope/hạ quyền phiên cũ, noaccount mobile job picker không tạo user, cancel không ghi; desktop/mobile/focus/nooverflow. Ruff/XML10/diff đạt; ảnh trước–sau cùng route/role/dataset/viewport đã mở tự đánh giá.
- Rehearsal backup045025670054Z restoretest596rowsets/643blobrefs/429sequences khớp và neutralize; fixture giả đã loại. Backup main cuối050005254157Z, exactPIDstop/upgrade chỉHRnoHTTP/start/smoke. Source53file seal khớp,79bảng/617nonassetblob bảo toàn; ACL policy giữ,2write metadata đổi. Hai cổng39employee/27user/8active/13phòng/7mapping/1HEAD; không thay chức vụ/tài khoản/quyền người thật hoặc tạo DBthứ3/restore test sang main.
- Status/roadmap/DEC039/workflow/guide/security/design/acceptance/runbook/README cập nhật. Evidence private `.local/hr-position003/`, rollback53filegốc/0filemới. Sửa harness role search_count theo scope và mobile picker rồi rerun; không tính fail là pass. GCassetsWinError5/markdown2warning còn, blob kiểm riêng; subagent model không khả dụng nên chưa audit độc lập, chưa điện thoại vật lý. Next: người dùng review18069; visual/business/pilot riêng.

## CHG-20261112-005 — HR-ACCOUNT-002: Form tài khoản rõ input và thông báo tiếng Việt

- Ngày12/11/2026 Asia/Saigon. Phản hồi trực tiếp tiếp tục taskHR-ACCOUNT-ROLE-001, ngoại lệ thực thi/áp main trong task; không stage/commit/push. Native Odoo/custom addons, không React/API/core.
- HR20.0.1.3.0: xác thực admin trước → OWL dialog login/password/confirmation cùng màn hình, label/chú thích/viền46px/Hiện-Ẩn/inline error/loading/cancel/focus/reduced/mobile. Create/password/mapping/audit nguyên tử; reset cùng form loginreadonly. Password mới chỉ RAM/RPC, không transient/context/native identityrequest/chatter; submit kiểm native sessionTTL600giây, forgedcontext/noHTTP bị chặn. Native hash/policy và guard role/company/protected user giữ. Login20.0.1.4.0 Việt hóa native identity/view/wrongpassword; role preview dịch capability, giữ domain/department/projectscope.
- Test: final Odoo sau restore28ca0failed0errors; Ruff/XML10/JS đạt; HOOTHR20tests83assertions/Home29tests166assertions đạt lại sau restore. Browser8nhóm create/login/reset/oldpassworddeny/noauth/nonadmin/validation/duplicate/loading/cancel/tworaces/retry, secrets checks đạt0console/pageerror. CleanUI5nhóm mỗi cổng1440/390/320/focus/reduced/one-modal/clearlabels/cancel đạt. Ảnh main trước–sau cùng hồ sơ28/role/viewport/dataset đã mở tự đánh giá.
- Backup rehearsal041738740882Z restoretest596rowsets/643blobrefs/429sequence khớp và neutralize; fixture giả đã loại. Backup main cuối042518138326Z, exactPIDstop/upgradeHR+loginnoHTTP/start/smoke. Seal53file,79bảng nghiệp vụ/quyền và617nonassetblob giữ; ACL policy giữ,2write metadata đổi do upgrade. Bảo toàn39employee/27user/8active/13phòng/7mapping/1HEAD, đúng baseline trước sửa; số26users/6mapping/612blob trong CHG004 là lịch sử. Không đổi tài khoản/mật khẩu/quyền người thật hoặc DBthứ3.
- Cập nhật status/roadmap/DEC039/workflow/guide/security/design/acceptance/runbook/README. Evidence private`.local/hr-account002/`, rollback46filegốc+7mới. Lỗi testAPI/minlength,OWL4/modal/matcher/timing và harness baseline đã sửa rồi rerun; GCassetsWinError5/markdown2warning còn, blob kiểm riêng. Subagent lỗi model kế thừa nên chưa audit độc lập; chưa điện thoại vật lý. Việt hóa trong luồng tài khoản/quyền/xác thực; chưa kiểm kê dịch toàn bộ addon khác. Next: người dùng review18069; visual/business/pilot riêng.

## CHG-20261112-004 — HR-ACCOUNT-ROLE-001: Tài khoản cá nhân, vai trò KH-KD và hồ sơ native

- Ngày: 12/11/2026 Asia/Saigon. Yêu cầu triển khai trực tiếp file đính kèm, ngoại lệ DEC-022 trong task; DEC-039. Không stage/commit/push; giữ dirty worktree có sẵn.
- HR20.0.1.2.0 bỏ chọn/link/unlink user và chặn RPC/native/import/resource/res.users binding/email-onchange; create/map/audit nguyên tử, lock employee/login, unique native theo company, password native. Giữ mapping/account/system hợp lệ, không bulk tạo user.
- Adapter admin staff↔HEAD tái sử dụng tp.kd.department.role/CRM scope, preview+reason+snapshot/locks/snapshot đọc mới/audit actor thật; revoke HEAD, chặn nguồn quản lý riêng xung đột, giữ financial_read riêng, bump session revision. Không cấp quyền qua chức vụ hoặc tên phòng; không mở HR/Settings/ký/thanh toán cho HEAD.
- Form5tab/header/edit-save-cancel/history/light+navy/mobile/focus/reduced; labels Mở/Khóa/Chưa có tài khoản đồng bộ. Login20.0.1.3.0 giữ thông báo khóa đúng câu người dùng; feedback placeholder. API/React/core không đổi.
- Test thực chạy: Odoo source cuối sau restore26tests0failed0errors; HEAD regression14tests0failed0errors; Ruff/XML6/JS đạt; HOOT19tests78assertions HR/29tests166assertions Home; Playwright actions8, entries/status7, UI desktop/mobile/keyboard/reduced/error validation/no picker, clean test/main smoke và mobile toolbar/account modal đạt. Concurrent same employee/same login khác employee không duplicate/orphan, retry denied; stale transaction bắt grant commit; revoke chặn RPC/API/export/file/chatter và giữ quyền financial_read cấp riêng.
- Restore rehearsal backup032800001448Z595tables638blobrefs428sequences khớp, neutralize và test sạch. Main backup cuối `backup-tp_tanphat_dev-20261112T034224215080Z` sau dừng đúng runtime; upgrade HR/login không seed/tests, start/smoke18069.79bảng/612nonassetblob/source46file seal bảo toàn; cả2DB39employee26users7active13departments6mappings1HEAD. Không thay account/password/role thật, không DB thứ3/restore test sang main.
- Fail trước sửa không tính đạt: socket Windows, attachment return contract và browser harness; hai test-run chồng bị hủy rồi chạy tuần tự. GC Windows/markdown2 warning có ghi. Chưa thiết bị thật/audit độc lập, visual/business/pilot cần người dùng. Bằng chứng private `.local/hr-account001/`; [acceptance](demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md), [guide](demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md), [runbook](../ops/runbooks/HR_ACCOUNT_ROLE_001_DEPLOY_AND_ROLLBACK.md). Next: người dùng review18069, workflow finish/check.

## CHG-20261112-003 — HR-UI-006: Xóa placeholder "Ví dụ: kd.doanh..." & Thay chữ "records" thành "thành viên"

- **Ngày:** 12/11/2026 (Asia/Saigon). Theo yêu cầu trực tiếp của người dùng.
- **Phạm vi thay đổi (`custom_addons/tp_hr_workspace`):**
  + `views/workspace.xml`: Xóa bỏ thuộc tính `placeholder="Ví dụ: kd.doanh..."` trên trường `new_user_login` (Tên đăng nhập mới) trong modal Cấp tài khoản & mật khẩu (`tp.hr.account.wizard`).
  + `static/src/table/table.js`: Triển khai `HrListRenderer` kế thừa `ListRenderer` và patch `ListRenderer.prototype.getGroupText` trả về `${group.count} thành viên`, thay thế toàn bộ chữ tiếng Anh `record`/`records` trên dải tiêu đề gom nhóm danh sách bằng tiếng Việt chuẩn `thành viên` (ví dụ: `Ban Giám đốc 4 thành viên`, `Kế hoạch Kinh doanh 6 thành viên`, `TACICO 1 thành viên`).
  + `static/tests/hr_workspace.test.js`: Bổ sung HOOT unit test xác minh `getGroupText` trả về đúng chuỗi `thành viên`.
- **Kiểm thử & Áp dụng:**
  + Linter: Ruff check `custom_addons/tp_hr_workspace` đạt 100% PASS.
  + Backend Odoo tests: 15/15 PASS trên `tp_tanphat_test` (`0 failed, 0 error(s)`).
  + HOOT frontend tests: `tp_hr_workspace` và `tp_web_home` 100% PASS.
  + Playwright E2E (`.local/hr_verification/verify_ui_polish.cjs`): PASS 100% trên cả test (18079) và dev (18069); xác nhận 9/9 nhóm phòng ban hiển thị "thành viên", 0 chữ "record(s)", trường `new_user_login` sạch placeholder.
  + Backup dev DB: `.local/tp_tanphat_dev_pre_ui_polish.dump` (8.15 MB, exit code 0). Nâng cấp `tp_hr_workspace` trên `tp_tanphat_dev` (18069) thành công. Bảo toàn 100% 39 nhân sự và 6 tài khoản KD liên kết hoạt động. Không commit/push.

## CHG-20261112-002 — HR-DASH-002: sidebar giống Kinh doanh và icon nhân viên

- Ngày12/11/2026 Asia/Saigon; theo phản hồi trực tiếp, sidebar HR đổi từ trắng sang palette Kinh doanh `#17324D/#22476A/#7FB3D5`, chữ sáng/search/hover/mobile đồng bộ; dashboard giữ sáng. Icon trước “Nhân viên” đổi mapping `people` không có trong catalog sang native `group`; không thêm dependency hoặc đổi model/security/API/dữ liệu.
- Test18079 trước main18069: Playwright1440/390, glyph/font/vị trí icon, rail/drawer/search/focus/Escape/nav-list/quay dashboard, darkCSS thực/reduced-motion và0console/pageerror đạt mỗi cổng. HOOT HR17tests72assertions + Home29tests166assertions; XML/Node syntax/diff đạt. Đã mở ảnh thật. Không chạy backend Odoo/React, chưa điện thoại vật lý/audit độc lập; visual/business/pilot riêng.
- Backup trước restart main `.local/hr001/backup-tp_tanphat_dev-20261112T020356030758Z`595bảng/638blobrefs+dump/source/config/filestore/checksum; rollback scoped3file trước sửa `.local/hr-sidebar002/rollback-source/`. Đúng parent/child/config, không upgrade/migration/restore/DBthứba. Seal SCSS/JS/CJS và preservation79bảng/612nonassetblob đạt; chỉ5bảng kỹ thuật assets/bus/presence/device/login đổi. Evidence `.local/hr-sidebar002/`; guide/design/acceptance/README/roadmap/runbook cập nhật.
- Tiếp tục checkpoint có sẵn01:57UTC; giữ dirty worktree, không stage/commit/push. Verifier lỗi kỳ vọng glyph codepoint/đợi hidden và allowlist dùng nhầm tên bảng presence đã sửa theo source, rerun đạt; không tính fail là pass. Subagent không khởi tạo được với model kế thừa. Bước tiếp: người dùng review18069.

## CHG-20261112-001 — HR-DASH-002: dashboard sáng và biểu đồ trực quan

- Ngày12/11/2026 Asia/Saigon; tiếp tục yêu cầu thực thi trực tiếp đã nhận11/11. Native OWL/QWeb/SCSS: sidebar sáng/header gọn/5KPI iconSVG, donut lớn/legend14px/tooltip đồng bộ/keyboard, màu ID theo toàn catalog, thanh chức vụ18px cùng thang0 đủ nhóm; bảng tìm riêng và account Mở/Khóa thuộc linked. Xóa dark override HR, scoped light kể cả bundle Odoo dark; motion180–200ms/reduced-motion.
- Không đổi backend/model/security/API/session/login/lock; guard population/filter/catalog/race/export giữ. Không thêm framework hoặc seed/sửa dữ liệu HR thật; không commit/push.
- Kiểm thực chạy trên18079 rồi18069: HOOT HR17tests72assertions (15HR+2dependency), Home29tests166assertions; Playwright5regression+7extended/cổng,0pageerror/consoleerror,5viewport/zoom200/keyboard/touch/reduced/darkCSS thực; XLSX/filter/list/profile6tab/dialog đạt. XML/Node syntax/diff đạt; backend Odoo/React không chạy vì source tương ứng không đổi. Lượt lỗi Sassmin/OWLinlineif/test timing đã sửa và rerun, log fail không tính pass.
- Ảnh trước–sau1440/390 cùng admin/route/population; full metric/catalog/domain so với trước khớp trừ timestamp, đã mở ảnh thật. Main39hồ sơ/9đơn vị/6linked,79bảng612nonassetblob và ACL/rule/company/implied-group không đổi.6bảng kỹ thuật đổi do assets/login/device/presence/bus/transient wizard; không thao tác account write.
- Backup cuối014402981715Z595bảng636blob refs+dump/source/config/filestore+checksum; rollback scoped từ source trước sửa, seal15staticHR gồmSCSS. Không upgrade/migration/restore/DBthứba. Main được terminal khác mở08:44:46; guard start từ chối listenertrùng, đã kiểmPID/config/source/smoke, không nhận maintenance độc quyền.
- Cập nhật status/roadmap/guide/acceptance/design/README và runbook; checker không bao phủSCSS/CJS nên hash/diff/syntax riêng. Chưa điện thoại thật hoặc audit độc lập (subagent model không khả dụng); visual/business/pilot người dùng review18069. Palette có thể phân lại khi catalogID thay, filter/order giữ. Bước tiếp: review bố cục thật; không mở module mới.


## CHG-20261111-010 — HR-DASH-001 và khóa/mở tài khoản

- Người dùng yêu cầu thực thi trực tiếp trong scope này, test18079, backup/restore rồi main18069; không commit/push. Dashboard native viết lại 5KPI/donut đơn vị/bar chức vụ/bảng/checklist/link progress; backend job filter/catalog/mobile-contact/export parity, guard tải/race.
- Tình trạng Mở/Khóa/Chưa liên kết, admin lock/unlock có lý do/audit/scope/target/protected identity; giữ employee archive riêng. Native user.active + HR flag + token revision; cũ session không hồi sinh sau unlock. Chặn bypass context liên kết. Đúng password user khóa hiện thông báo; feedback placeholder không gửi network; native2FA/CSRF giữ.
- Kiểm: Ruff/XML; Odoo20ca/0failed/0errors sau restore cuối; HOOT HR/Home đạt; dashboard Playwright5nhóm mỗi cổng, 0pageerror/5viewport/dark/reduced/zoom200/filter-XLSX/list; lock E2E4nhóm trên test. Main79bảng/612nonassetblob giữ, 39hồ sơ/6liên kết/9đơn vị có người. Không test write main.
- Backup cuối092100242854Z restore test595rowsets/636blob/428sequence, neutralize và test lại; upgrade main2module sạch. Giữ15source gốc theo hash checkpoint009 để rollback scoped. Runtime main được terminal khác mở lại khi rehearsal; đã xác minh config/source/smoke/preservation; không khẳng định độc quyền runtime.
- Sự cố: socket test/restore FK schema mới/log encoding đã xử lý và rerun đạt. Windows GC asset warning ở test, main/blob verified riêng. Cặp ảnh before–after CHG010 cùng phiên còn thiếu; dùng ảnh HR trước đã có làm tham chiếu.
- Guide/acceptance/rollback: docs/demo/HR_DASH_001_USER_GUIDE.md, docs/demo/HR_DASH_001_ACCEPTANCE.md, ops/runbooks/HR_DASH_001_DEPLOY_AND_ROLLBACK.md. Technical acceptance tách user visual/business/pilot; không audit độc lập. Next: người dùng review trên18069; feedback backend để task sau.

## CHG-20261111-009 — SYS-BOT-001: Ẩn hoàn toàn OdooBot khỏi toàn bộ hệ thống (Backend, UI, Thảo luận và Cơ sở dữ liệu)

- Ngày 11/11/2026 (Asia/Saigon); thực thi yêu cầu người dùng:
  + **Triệt tiêu ở tầng Backend ORM (`mail_bot_silencer.py`):**
    * Ghi đè `mail.message._message_fetch` lọc tự động `Domain('author_id', '!=', odoobot_id)` giúp ẩn hoàn toàn mọi thông báo tự động ("Department created", v.v.) và lịch sử bot trong Chatter trên toàn bộ phân hệ.
    * Kế thừa `res.users` vô hiệu hóa tour onboarding (`odoobot_state = 'disabled'` mặc định khi tạo user mới, `_on_webclient_bootstrap` tự động kiểm tra tắt, `_init_odoobot` trả về `False`).
    * Kế thừa `discuss.channel._get_or_create_chat` chặn phát sinh kênh chat 1-1 mới với OdooBot; vô hiệu hóa `mail.bot._apply_logic`.
  + **Triệt tiêu ở tầng Frontend UI (`bot_silencer.js`, `bot_silencer.scss`):**
    * Patch `Thread.prototype.orderedMessages` loại bỏ mọi tin nhắn có `isBot` / `odoobot` khỏi luồng hiển thị.
    * Patch `SuggestionService.prototype.isPartnerSuggestionValid` ẩn hoàn toàn OdooBot khỏi danh sách gợi ý `@mention`.
    * Bổ sung SCSS ẩn triệt để các thông báo/avatar bot còn sót trên toàn giao diện.
  + **Làm sạch và chuẩn hóa cơ sở dữ liệu (trên cả `tp_tanphat_test` 18079 và `tp_tanphat_dev` 18069):**
    * Đổi tên `base.partner_root` và `base.user_root` từ `OdooBot` thành `Hệ thống`, xóa avatar robot mặc định (`image_1920 = False`), cập nhật email `hethong@tanphat.internal`.
    * Dọn dẹp 11 kênh chat OdooBot tồn đọng, xóa thông báo khởi tạo rác, loại bỏ hoàn toàn badge số đếm chưa đọc từ bot trên thanh Systray Navbar.
    * Bảo toàn 100% 39 nhân sự, 9 phòng ban và 6 tài khoản KD hoạt động.
- **Kiểm thử & Triển khai an toàn:**
  + Linter: Ruff check 100% PASS (`custom_addons/tp_hr_workspace`).
  + Backend Odoo unit tests: 12/12 tests PASS trên `tp_tanphat_test` (bổ sung `test_odoobot_silenced_and_neutralized`).
  + HOOT frontend unit tests: `tp_hr_workspace` và `tp_web_home` 100% PASS.
  + Playwright browser tests: Xác minh trên cả 18079 và 18069: 0 tin nhắn OdooBot trong Chatter (Phòng Ban Giám đốc, Hồ sơ nhân viên), 0 badge/chat OdooBot trên Systray, 0 OdooBot trong Discuss.
  + Sao lưu `tp_tanphat_dev` trước nâng cấp: `.local/tp_tanphat_dev_pre_odoobot_silencer.dump` (7.49 MB).
  + Nâng cấp `tp_hr_workspace` trên `tp_tanphat_dev` 18069 thành công (exit code 0).
  + Không commit/push theo quy tắc.

## CHG-20261111-008 — HR-DASH-001: Kế hoạch tổng quan nhân sự và bản xem trước

- Tạo [kế hoạch thiết kế/metric/lộ trình](ui/HR_DASH_001_REDESIGN_PLAN.md) và [prompt Claude](prompts/CLAUDE_HR_DASH_001_OVERVIEW_REDESIGN.md) theo yêu cầu lên kế hoạch: 5 KPI; donut đơn vị và bar chức vụ thay chart lặp; bảng tổng hợp/checklist/tài khoản trung tính; filter job/department/status, drill-down/XLSX cùng population và quyền. Giữ native Odoo/sidebar/form/nhóm tự mở, không bịa KPI lương/công/biến động hoặc cấp quyền mới.
- Source review nhận diện filter catalog/color-index/missing-contact-mobile và Reports trỏ cùng Overview; chuẩn bị hướng sửa trong scope. Lần đọc đầu có source/checkpoint batch HR chưa khép; batch kia đã finish CHG007 trong lúc làm. Đã recheck 378file/digest khớp state mới rồi start checkpoint tài liệu; không đóng batch code chưa kiểm thay bên triển khai.
- Tạo minh họa tương tác độc lập ngoài repository, gắn nhãn số liệu minh họa, không runtime Odoo/PII. Playwright11nhóm đạt/0pageerror: KPI/tổng/filter/legend/reset/empty, 5viewport, dark/reduced-motion; xem ảnh1440/390. Evidence `.local/hr-dash001-plan/`. Sourcecode/DB/account/quyền/filestore/runtime không đổi; không chạy Odoo feature tests cho kế hoạch, không gọi đây là audit độc lập.
- Cập nhật status/roadmap cùng lượt; 407link/5tài liệu không thiếu mới (2link Word private thiếu từ trước), 12HD/fences/whitespace/diff đạt; source378file giữ digest checkpoint. Checker private sửa lỗi encoding HTML thành UTF-8 rồi đạt. Workflow finish/check ghi bàn giao. Không commit/push. Giao Claude thực thi prompt trên test trước backup/restore và áp main18069; review visual/nghiệp vụ riêng.

## CHG-20261111-007 — HR-UI-005: Xóa bỏ bảng phẳng, thiết lập phân nhóm phòng ban tự mở rộng làm mặc định vĩnh viễn (0 search facet)

- Ngày 11/11/2026 (Asia/Saigon); thực thi yêu cầu người dùng:
  + **Xóa bỏ giao diện phẳng, phân nhóm mặc định vĩnh viễn:** Tạo lớp `HrRelationalModel` kế thừa `RelationalModel` trong `custom_addons/tp_hr_workspace/static/src/table/table.js`. Trong `_getNextConfig(currentConfig, params)`, khi `config.resModel === "hr.employee"` và chưa có `groupBy` tùy chọn từ người dùng, tự động gán `config.groupBy = ["department_id"]` và `config.openGroupsByDefault = true`.
  + **Làm sạch thanh tìm kiếm (không cần bộ lọc):** Gỡ bỏ `'search_default_department': 1` khỏi ngữ cảnh `action_employees` trong `views/workspace.xml`. Thanh tìm kiếm hoàn toàn sạch sẽ (0 facets), không còn thẻ `Đơn vị x`. Khi người dùng tìm kiếm theo tên hoặc mã nhân viên, hoặc xóa từ khóa tìm kiếm, danh sách vẫn giữ nguyên cấu trúc phân nhóm theo phòng ban và tự động mở rộng đầy đủ các dòng nhân viên.
  + **Bảo toàn chức năng & Quản lý chức vụ:**
    * Giữ nguyên cột "Chức vụ" (`job_id`) và "Số điện thoại" (`mobile_phone`).
    * Quản lý chức vụ (11 vị trí) trong nhóm "Tổ chức" trên sidebar và form chức vụ, gán chức vụ trên Tab 1 "Tổng quan" hồ sơ nhân sự hoạt động đồng bộ.
    * Bảo toàn 100% 39 nhân sự, 9 phòng ban và 6 tài khoản KD đang hoạt động (`kd.thuyanh`, `kd.thanh`, `kd.tuananh`, `kd.lananh`, `kd.doanh`, `kd.chauanh`).
- **Kiểm thử & Triển khai an toàn:**
  + Odoo backend tests: 11/11 tests PASS trên `tp_tanphat_test` (18079).
  + HOOT frontend unit tests: `tp_hr_workspace` và `tp_web_home` 100% PASS.
  + Playwright browser tests: Kiểm thử trên cả 18079 và 18069 xác nhận thanh tìm kiếm có 0 facet, 9 dải tiêu đề nhóm phòng ban hiển thị, 39 dòng nhân viên mở rộng tự động, menu Chức vụ và form chức vụ đạt 100%.
  + Sao lưu `tp_tanphat_dev` trước nâng cấp: `.local/tp_tanphat_dev_pre_hr_unfold_default.dump` (7.49 MB).
  + Nâng cấp module `tp_hr_workspace` trên `tp_tanphat_dev` 18069 thành công (exit code 0).
  + Không commit/push theo quy tắc.

## CHG-20261111-006 — HR-UI-004: Mở rộng mặc định toàn bộ nhóm phòng ban trên danh sách nhân viên và thêm Quản lý chức vụ tùy chỉnh

- Ngày 11/11/2026 (Asia/Saigon); thực thi yêu cầu người dùng:
  + **Mặc định mở rộng toàn bộ nhóm phòng ban:** Danh sách nhân viên (`employee_list`) cấu hình `expand="1"`, `groups_limit="50"` và thiết lập `openGroupsByDefault: true` trong `HrListController.modelParams`. Khi người dùng mở "Danh sách nhân viên", toàn bộ 9 nhóm phòng ban được tự động mở rộng (unfolded), hiển thị đầy đủ 39 nhân sự ngay lập tức mà không cần nhấp chuột vào từng phòng ban.
  + **Bổ sung cột Chức vụ:** Cột `Chức vụ` (`job_id`) hiển thị trực quan trong bảng danh sách nhân sự (`optional="show"`), nhãn chức vụ nguồn được chuyển sang chế độ tùy chọn ẩn/hiện.
  + **Quản lý chức vụ tùy chỉnh:**
    * Bổ sung menu "Chức vụ" trong nhóm "Tổ chức" trên thanh sidebar TP HR.
    * Tạo chế độ xem danh sách `tp.hr.job.list` hỗ trợ kéo thả sắp xếp thứ tự ưu tiên (`sequence` handle), sửa trực tiếp tên, đơn vị, trạng thái, xem số lượng nhân viên (`no_of_employee`), nút mở form xem chi tiết (`open_form_view="True"`).
    * Thiết kế chế độ xem form `tp.hr.job.form` chuyên nghiệp hiển thị tên chức vụ, đơn vị mặc định, thứ tự, số lượng nhân sự, trạng thái đang sử dụng, notebook tab danh sách nhân viên thực tế đang giữ chức vụ và tab mô tả công việc.
    * Chuẩn hóa 11 vị trí chức vụ thực tế của công ty (Chủ tịch, Tổng giám đốc, Phó Tổng giám đốc, Giám đốc, Trưởng phòng, Phó phòng, Kế toán trưởng, Kế toán viên, Nhân viên, Thử việc, Lái xe); ánh xạ 100% (39/39) nhân viên trên cả test (18079) và dev (18069).
    * Hiển thị trường `Chức vụ` (`job_id`) trên Tab 1 "Tổng quan" trong hồ sơ nhân viên để người dùng gán hoặc đổi chức vụ dễ dàng.
- **Kiểm thử & Triển khai an toàn:**
  + Odoo backend tests: 11/11 tests PASS trên `tp_tanphat_test` (bao gồm `test_hr_job_position_management`).
  + HOOT frontend unit tests: `tp_hr_workspace` và `tp_web_home` 100% PASS.
  + Playwright browser tests: Kiểm thử tự động mở 9 nhóm phòng ban (39 dòng), hiển thị cột Chức vụ, menu sidebar Chức vụ (11 vị trí), form chức vụ và trường chức vụ trên hồ sơ nhân sự đạt 100% trên cả 18079 và 18069.
  + Sao lưu `tp_tanphat_dev` trước nâng cấp: `.local/tp_tanphat_dev_pre_hr_job.dump` (7.49 MB).
  + Nâng cấp module `tp_hr_workspace` trên `tp_tanphat_dev` 18069 thành công.
  + Không commit/push theo quy tắc.

## CHG-20261111-005 — HR-UI-003: Phân nhóm nhân viên theo phòng ban chuẩn Excel, thêm cột SĐT, đồng bộ tài khoản KD và quản trị tài khoản trong HR

- Ngày 11/11/2026 (Asia/Saigon); thực thi yêu cầu người dùng:
  + **Giao diện danh sách nhân viên phân nhóm theo phòng ban:** Mặc định gom nhóm theo Đơn vị / Phòng ban (`search_default_department: 1`), hiển thị dải tiêu đề nhóm màu xanh ngọc `#cbf3f7` viền Teal đậm `#087f8c` và chữ đậm `#0b3846`, số lượng nhân sự từng phòng, hỗ trợ mở rộng/thu gọn trực quan theo đúng mẫu bảng tính Excel của người dùng.
  + **Thêm cột Số điện thoại:** Bổ sung trường `mobile_phone` (Số điện thoại) vào chế độ xem danh sách `employee_list` (`optional="show"`).
  + **Đồng bộ danh tính nhân sự & tài khoản xuyên suốt:** Xóa triệt để tài khoản dư thừa `kd.huong` (0 FK vi phạm). Tạo mới và cấp quyền nhóm `tp_kd_workspace.group_scoped_staff` cho 2 nhân sự: Nguyễn Thái Doanh (`TP10062` -> `kd.doanh`) và Trần Châu Anh (`TP10063` -> `kd.chauanh`). Liên kết toàn bộ 6 nhân sự Ban Kế hoạch Kinh doanh với tài khoản người dùng thật (`kd.thuyanh`, `kd.thanh`, `kd.tuananh`, `kd.lananh`, `kd.doanh`, `kd.chauanh`), trạng thái tài khoản chuyển sang badge xanh "Đang hoạt động", đồng bộ xuyên suốt toàn bộ phân hệ KH-KD, trao đổi chatter và dự án.
  + **Quản trị tài khoản & mật khẩu tích hợp trong Nhân sự:** Nâng cấp wizard `tp.hr.account.wizard` cho phép Quản trị viên hệ thống tạo mới tài khoản Odoo và mật khẩu khởi tạo trực tiếp từ hồ sơ nhân viên (`action_create_user`), hỗ trợ đặt lại mật khẩu và gỡ liên kết an toàn ngay trong phân hệ HR mà không cần rời sang Settings kỹ thuật Odoo.
- **Kiểm thử & Triển khai an toàn:**
  + Linter: Ruff check 100% PASS.
  + Kiểm thử Odoo backend: 8/8 tests PASS trên `tp_tanphat_test` (18079).
  + HOOT frontend unit tests: `tp_hr_workspace` và `tp_web_home` 100% PASS.
  + Playwright browser tests: Kiểm thử giao diện gom nhóm, cột SĐT, 6 tài khoản KD và tab tạo tài khoản đạt 100% trên cả 18079 và 18069.
  + Sao lưu an toàn `tp_tanphat_dev` (`.local/hr001/backup-tp_tanphat_dev-20261111T054041120304Z`), áp dụng nâng cấp module `tp_hr_workspace` thành công trên cổng 18069.
  + Không commit/push theo quy tắc.

## CHG-20261111-004 — HR-UI-002: Tái thiết kế hồ sơ nhân viên, quản lý tài khoản liên kết & đặt lại mật khẩu đã áp main 18069

- Ngày 11/11/2026 (Asia/Saigon); thực thi hoàn chỉnh prompt [CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md](prompts/CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md) và thiết kế [HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS_DESIGN.md](ui/HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS_DESIGN.md): kiểm thử đạt 12/12 tiêu chí nghiệm thu trên `tp_tanphat_test` 18079, sao lưu và áp dụng an toàn lên `tp_tanphat_dev` 18069.
- **Tái thiết kế giao diện hồ sơ nhân viên:**
  + Header gọn: Avatar 80px (căn giữa trên di động), tiêu đề nhân sự rõ ràng, nhãn định danh (Mã nhân viên, Đơn vị, Trạng thái quản lý, Trạng thái tài khoản). Ẩn triệt để nút `Invite` và nhãn `Not Invited` gây nhiễu của Odoo gốc.
  + 6 Tab nghiệp vụ chuẩn nhận diện Navy `#17324D` / Teal `#087F8C`: Tab `Tổng quan` là mặc định với thẻ thông tin 2 cột; Tab `Công việc` ẩn mục Giờ làm việc và nhóm Lịch trình khỏi UI (bảo toàn 100% calendar ORM); Tab `Cá nhân`; Tab `Hồ sơ & năng lực`; Tab `Tài khoản` có cảnh báo bảo mật PBKDF2/SHA512; Tab `Nguồn dữ liệu`.
  + Khung thảo luận (Chatter): Đặt gọn gàng ở đáy trang (`.o_form_renderer` xếp dọc), thu gọn và mở rộng linh hoạt, không chèn ép vùng nội dung chính.
  + Bảng danh sách nhân viên: Cột mặc định `Mã nhân viên | Họ và tên | Phòng ban/Đơn vị | Chức vụ nguồn | Tên đăng nhập | Trạng thái tài khoản | Trạng thái hồ sơ | Thao tác`. Tài khoản chưa liên kết để trống tên đăng nhập (không bịa đặt tên); nút `Xem tài khoản` (biểu tượng thẻ) mở modal độc lập trực tiếp từ danh sách.
- **Quản trị tài khoản & bảo mật mật khẩu:**
  + Model wizard `tp.hr.account.wizard` giới hạn riêng Quản trị viên hệ thống (`base.group_system`): liên kết người dùng cùng công ty, từ chối duplicate/public/portal/superuser; gỡ/thay liên kết bắt buộc nhập lý do; ghi nhận chatter không lộ bí mật; bảo vệ write trên `hr.employee` và `resource.resource` chặn bypass từ RPC non-admin.
  + Đặt lại mật khẩu: Tích hợp native `change.password.wizard` kích hoạt xác thực lại admin (`@check_identity`), tích hợp nút bật/tắt hiện mật khẩu mới đang nhập; hiển thị thông báo rõ ràng "Không thể xem mật khẩu hiện tại" do băm một chiều PBKDF2/SHA512; tuyệt đối không có 16 dấu chấm giả mật khẩu cũ; 0 bản ghi mật khẩu rõ.
- **Kiểm thử kỹ thuật toàn diện:**
  + Odoo backend tests: 8/8 PASS (`test_hr_workspace.py` bao gồm login/status fields, security bypass guards, link/unlink constraints, non-admin denial, department change group preservation, calendar ORM, no secret leakage).
  + HOOT frontend tests: 100% PASS (`tp_hr_workspace`, `tp_web_home`).
  + Playwright E2E: 9/9 kịch bản PASS (AT01–AT12) trên `18079` với actor giả `hrui002.test.actor` (đăng nhập mật khẩu mới `true`, mật khẩu cũ `false`, unlinking phục hồi sạch baseline); Responsive 5 viewports (1440, 1024, 768, 390, 320) không tràn ngang (`scrollWidth <= clientWidth + 2`).
- **Sao lưu, Rollout Main & Bảo toàn dữ liệu:**
  + Sao lưu `tp_tanphat_dev` trước nâng cấp: `.local/hr001/backup-tp_tanphat_dev-20261111T050114740529Z` (594 tables, 621 blob references, `BACKUP PASS`).
  + Nâng cấp `tp_hr_workspace` trên `tp_tanphat_dev` 18069 thành công (exit code 0, 0 warning/error).
  + Chụp toàn bộ ảnh AFTER (chỉ đọc) lưu tại `.local/hrui002/after-18069/`.
  + Bảo toàn dữ liệu 18069: 39/39 hồ sơ nhân viên, 39/39 mã TP, 25 users (các tài khoản KH-KD và quyền HEAD của Chu Thị Thuỳ Anh nguyên vẹn, 0 mật khẩu tài khoản thật bị thay đổi, 0 tài khoản tạo hàng loạt).
- Bàn giao: [Báo cáo nghiệm thu](demo/HR_UI_002_ACCEPTANCE.md), [Hướng dẫn sử dụng](demo/HR_UI_002_USER_GUIDE.md), bộ ảnh trước–sau tại `.local/hrui002/`. Không commit/push.

## CHG-20261111-003 — HR-UI-002: Prompt hồ sơ gọn, tài khoản và reset mật khẩu

- Theo ảnh/yêu cầu người dùng, soạn [prompt Claude](prompts/CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md) và [thiết kế](ui/HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS_DESIGN.md): list có login thật/trạng thái, chi tiết/link tài khoản đúng employee/company/đơn vị, admin reset password bằng wizard native; form header gọn/tab Tổng quan/chatter thu gọn, bỏ Giờ làm việc khỏi UI và giữ calendar/model.
- Đối chiếu source `employee_list.user_id`, native inherited form, resource link/unique company, related user department và password hash/wizard/check_identity/ACL. Mật khẩu hiện tại không thể xem lại; không tạo kho bản rõ. Prompt giữ native quyền/session/password policy, không cấp HR manager quyền quản trị user, không tự map alias hoặc tạo/reset tài khoản hàng loạt; chuyển đơn vị không tự đổi quyền nghiệp vụ.
- Cập nhật status/roadmap, acceptance AT01–AT12 và quy trình test18079 → backup/restore → áp source18069 trong prompt. Chỉ sửa tài liệu; không thay app, database, user link/password/quyền hoặc runtime. Đọc listener xác nhận ba cổng đang lắng nghe; workflow CHG002 đạt trước start. Kiểm 390 link/5 tài liệu không thiếu mới (2 link Word private thiếu từ trước), 12 ID/7 phần/fence/whitespace/diff đạt; source 375 file/digest giữ nguyên so checkpoint. Finish/check ghi kết quả bàn giao; không chạy feature tests vì chưa triển khai. Tự rà soát, chưa audit độc lập; không commit/push.

## CHG-20261111-002 — HR-001: Roster thật và workspace HR native đã áp main

- Ngày11/11/2026 (Asia/Saigon), thực thi toàn prompt theo yêu cầu trực tiếp: model/security/import/nativeUI/dashboard/Excel, test18079 trước backup/restore và main18069; không commit/push. Ngoại lệ vai điều phối chỉ phạm vi HR-001.
- Thêm `tp_hr_workspace`, mở rộng `tp_organization` và lối Home HR: mã TP/source/provenance/unique archived/sequence; preview/apply/audit/retry/field delta, khóa company/row bảo toàn sửa tay; guard archive cả resource, chặn demo loader và hard-delete hồ sơ nhập. Sidebar/table/form/skills/version/config và chất lượng hồ sơ; knownness gia đình/lương, lịch sử list không wage analytics. Dashboard/donut/drilldown/XLSX whitelist cùng quyền/company/domain, không sudo aggregate, chống formula injection.
- Main/test đều39employee/39version/9đơn vị có người trong14catalog;78dòng nguồn→39create rồi retry39skip,0update/0conflict. KD18/Thiết kế20 giữ; dọn3HRscenario/catalog riêng, archive16actor có provenance, giữ25identity/auth/groups/company/HEAD. Năm KD alias pending, không tự match/link/grant HR/tạo39users; không nhập giờ công/lương.
- Kiểm backend28/28 và delta lịch sử4/4,0failed0errors; HOOT10HR+28Home (dependency12/29,34/166assertions); testUI13CRUD/nhập lại, freshrestore test11 + main11readonly0pageerror,5viewport,5KD/HEAD/export403. List KD0thật nên không mở detail và không tạo fixture main. Probe đồng thời mã/unique và source/manual/mapping4checks đạt; Ruff/XML/JS/workbook2sheet render+total39 và diff/workflow kiểm ở bàn giao.
- Backup main025345789849Z restore verified592bảng/261blob/424sequence trước neutralize; fresh install/test/cleanup/import diễn tập rồi áp main bằng module+ORM. Backup sau nhập031424514095Z594bảng/621refs riêng, chưa gọi restore verified. Nội dung944ACL cũ/auth/config/HEAD giữ,4ACL import mới. Strict hash report FAIL được giữ; semantic + exact COPY reconciliation xác minh metadata-only/đúng manifest,0vi phạm và621blobhash/size trước smoke. Sau smoke final semantic/reconciliation0vi phạm,621blobrefs;4/4probe knownness mỗiDB đạt,0pageerror. Lượt restore đầu còn orphan sequence004 được phát hiện và khắc phục hẹp, gate bổ sung sequence counters; không tạo DB thứ3/restore test đè main.
- Guide/acceptance/runbook/status/roadmap/HR plans/source/workflow cập nhật cùng lượt. Nghiệm thu nghiệp vụ/visual/pilot riêng;5identitypending và backlog HR mở rộng cần dữ liệu/quy chế. PII/backup/evidence chỉ `.local/hr001/`; giữ log lỗi cũ, WinError5GC Windows theo dõi riêng. Không commit/push.

## CHG-20261111-001 — HR-001: Kế hoạch/prompt roster mới, mã TP, workspace và tổng quan nhân sự

- Người dùng yêu cầu prompt triển khai HR native, dọn mẫu/account không phù hợp, nạp roster mới và mã TP, sidebar theo KH-KD, dashboard/Excel. Xác nhận liên kết employee không cấp HR toàn nhóm; cho phép bỏ account không phù hợp nguồn. DEC-038 ghi lựa chọn, prompt giới hạn archive có audit/admin preservation, không gán alias mơ hồ hay chuyển grant sang người khác.
- Đọc file mới hai sheet 78 dòng → 39 người/9 nhóm, B/D khớp, dedup/Unicode/sourcehash giữ, XML độc lập khớp reader; so file 10/11 có 3 mã thay chức vụ. Bản private `.local/hr-plan-20261111/` giữ roster/hash/sourcecells/TP mapping và runtime/usercandidates, không đưa PII/giờ công vào Git.
- Source/SELECT hiện có 3 HR scenario employee/3 version/9 department/3 job,25 users/22 active,CRM0/contract 0/Internal 1; HR scenario bindings và cơ chế load_demo_data có forcecreate đã đối chiếu, chưa dọn. HR/version/schema và sidebar KD gắn cứng app/prefs được phản ánh trong kế hoạch/prompt; dùng 2 DBchuẩn, không clone theo task.
- Tạo [kế hoạch HR](architecture/TP_HR_001_ROSTER_WORKSPACE_PLAN.md), [prompt thực thi](prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md), cập nhật baseline nguồn/HR foundation/status/roadmap/decision. Sáu chặng cleanup → model/import → HRfeatures → UI → dashboard/Excel → verify/áp main; có acceptance/privacy/idempotency/rollback, không làm menu giả hoặc hứa payroll đã đủ đầu vào.
- Chỉ tài liệu và công cụ đọc private; không sửa app/schema/DB/quyền/mật khẩu, không import/link/archive, không commit/push. Source 350 file/digest khớp checkpoint; hash workbook giữ nguyên. Kiểm reader/XML/so sánh nguồn, SELECT inventory, 410 link/8 tài liệu không thiếu mới (2 link Word private đã thiếu từ trước), fence/11 phần prompt và `git diff --check` đạt; không chạy Odoo/HOOT/browser feature suite cho prompt chưa triển khai. Handoff finish/check ghi kết quả thực tế; đây là tự rà soát, không audit độc lập hoặc nghiệm thu HR.

## CHG-20261110-008 — OPS-CLEAN-001: Dọn nghiệp vụ mẫu, giữ quyền/cấu hình và hai database local

- **Yêu cầu:** người dùng chọn xóa dữ liệu nghiệp vụ mẫu, giữ account/quyền/cấu hình; main18069 và một test dùng trước áp dev. DEC-037 ghi chính sách, cập nhật AGENTS/database design/local runbook và chú thích HR inventory trước dọn.
- **Thực hiện:** backup toàn34DB kèm filestore; snapshot main restore592bảng/295blobrefs, diễn tập dọn có transaction/FK/fingerprint trước main. Main xóa2.807dòng ở70bảng ID, cùng quan hệ và1.519binding của mẫu;1.337entry provenance thành `unlinked`. Đối chiếu phần giữ lại590bảng, XMLbinding và provenance riêng; giữ25users/944ir.access/group-role/menu/module/config. Grant/assignment dự án mẫu đi cùng dự án. InternalID3/tasks3&4 cùng liên hệ cấu hình giữ lại.
- **Chuẩn hóa:** bỏ32DB cũ đã archive, thay test cũ bằng restore main sạch đã đối chiếu592bảng; bỏ rehearsal. Chỉ còn2DBapp và3DBhệthống trên cluster55432. Test18079 tách data dir/session, cron/SMTP/UUID/URL; main18069 đang chạy. Không xóa source/bảng/filestore lịch sử, không nhập39nhân viên thật; không commit/push hoặc sửa application code.
- **Kiểm chứng:** Playwright12checks trên diễn tập,12main và12test chuẩn (kết quả cuối);0pageerror, businessKPI0; final read-only bảo toàn account/ACL/roles/config,17bảng nghiệp vụ0 và231blobrefs còn lại khớp hash/size. Lượt main từng timeout/hết phiên sau restart, ảnh/log private; chạy lại đủ12checks đạt, chưa sửa hoặc chốt nguyên nhân auth. Không đánh đồng với nghiệm thu toàn tính năng. Source350files digest khớp checkpoint. `git diff --check`/workflow finish/check ghi kết quả ở handoff checker.
- **Artifact:** `.local/ops-clean001/` ngoài Git, có archive/current verification, before/after plans/result, final backup/clean snapshot, restore evidence, smoke ảnh/JSON, dropped journal và final verification. [Hướng dẫn và giới hạn](../ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md). Các backup đang cùng máy, chưa có bản ngoài máy.

## CHG-20261110-007 — UI-HOME-004: Sửa 3 lỗi navbar, công cụ quản trị và 7 icon đã áp dev 18069

- Ngày 10/11/2026 (Asia/Saigon), thực hiện prompt `CLAUDE_UI_HOME_004_SHELL_ICON_CORRECTION.md` khắc phục triệt để 3 lỗi hiển thị được nêu trong `UI_HOME_004_SHELL_ICON_REVIEW.md`:
  + F-HOME-01 (Navbar bị lặp): Loại bỏ `<header class="tp-nav">` và CSS dead code (`.tp-nav`, `.tp-brand`, `.tp-account`, `.tp-avatar`). Giữ nguyên duy nhất thanh điều hướng native `.o_main_navbar` của Odoo.
  + F-HOME-02 (Khôi phục công cụ quản trị & Tất cả ứng dụng): Bổ sung `.tp-admin-tools` cạnh tiêu đề Trang chủ quản trị gồm 3 nút công cụ "Cài đặt" (`base.menu_administration`), "Quản lý ứng dụng" (`base.menu_management`), "Tất cả ứng dụng" (`all-apps`). Nút "Tất cả ứng dụng" mở panel `#tp_home_all_apps` với tìm kiếm lọc nhanh app và phím tắt đóng mở. Non-admin không có các công cụ này.
  + F-HOME-03 (Icon fallback hình tròn): Sửa AdminIcon gọi bằng explicit argument `icon="item.icon"`, sửa hình học SVG nhánh `ruler` thành thước vẽ kỹ thuật. Kết quả 0/7 icon fallback, cả 7 thẻ hiển thị hình vector đặc trưng chuẩn kích thước 24–26px trong vùng 42–46px.
- Quy trình an toàn và kiểm thử:
  + Backend Odoo tests trên clone: 12/12 PASS (0 failed, 0 error).
  + HOOT browser unit tests: 28/28 PASS (100% xanh).
  + Playwright browser tests trên clone (port 19689) và dev 18069 (`tp_tanphat_dev`): PASS 100% (cả admin và non-admin `kd.thuyanh`, 5 viewports 1440/768/390/320px, deep links, panel search, HR native, KH-KD workspace).
  + Backup verified trước apply: `backup-pre-apply-20261110T082506Z` (122 files, 592 bảng, 295 attachments) phục hồi thành công.
  + Áp delta `tp_web_home` 20.0.1.5.0 lên dev cổng 18069; kiểm chứng bảo toàn `PRESERVATION PASS` 39 bảng và `SECURITY PASS` 944 ACL rows (0 dòng dữ liệu nghiệp vụ bị thay đổi). Không commit/push.

## CHG-20261110-006 — Review lỗi Home và prompt correction navbar/icon/công cụ

- Ngày10/11/2026, ảnh người dùng sau CHG005 có2navbar,7circle và thiếu lối vào
  quản trị trên Home. [Review source](reviews/UI_HOME_004_SHELL_ICON_REVIEW.md)
  xác nhận navbar copy trong client action và system/panel nằm ở nhánh non-admin;
  native switcher/catalog vẫn có source, chưa kiểm lại menu runtime account.
- OWL/Chromium cô lập với template AdminIcon thực: tái hiện7fallback ở call hiện
  tại,7icon đúng khi truyền explicit argument. Evidence `.local/ui-home004-correction-review/`.
  Harness lần đầu dùng mount API cũ lỗi, đã sửa harness rồi kiểm đạt; không
  sửa application code. Đây là source review của phiên chính, không audit độc
  lập hoặc full Odoo smoke. Dev status18069/PG lắng nghe, không login/ghi DB.
- [Prompt correction](prompts/CLAUDE_UI_HOME_004_SHELL_ICON_CORRECTION.md):1navbar
  chung,3control quản trị gọn ngoài7tile, panel/switcher theo menu thật, icon đúng
  hình/ngữ nghĩa và regression full shell. Status/roadmap/design/acceptance/guide
  ghi visual defects open, giữ kết quả test CHG005 như lịch sử. Next sửa Home
  trước HR S1. Kiểm link/nội dung, code snapshot giữ nguyên, diff/workflow;
  không application/DB/quyền/runtime changes, không commit/push.

## CHG-20261110-005 — UI-HOME-004: Triển khai Trang chủ admin 7 mục và đặc tả HR S0 đã áp dev

- Ngày 10/11/2026 (Asia/Saigon), task UI-HOME-004 theo quyết định DEC-036: triển khai hoàn tất Trang chủ Admin native Odoo trên dev cổng 18069 (`tp_tanphat_dev`) nâng cấp module `tp_web_home` lên phiên bản `20.0.1.5.0`.
- Bố cục Admin Home (`#tp-admin-home-design`) đúng 7 mục chia 2 nhóm rõ nét:
  + Nhóm "Phòng ban và đơn vị": 1) Kế hoạch Kinh doanh (span 2 cột, nổi bật, badge "Đang hoạt động", mở workspace KH-KD đang vận hành), 2) Phòng Thiết kế, 3) Phòng Kỹ Thuật, 4) Phòng BIM-QC, 5) TADIC (4 đơn vị nội bộ có badge "Đang phát triển").
  + Nhóm "Nhân sự và tuyển dụng": 6) Quản lý nhân sự (badge "Triển khai tiếp theo", mở màn hình native Odoo Employees `hr.menu_hr_root`), 7) Tuyển dụng (badge "Đang phát triển", mở placeholder).
  + Ghi chú chân trang: "Danh mục này chỉ dành cho quản trị hệ thống. Các ứng dụng khác vẫn truy cập bình thường qua menu Odoo trên thanh điều hướng."
  + 5 màn hình placeholder tái sử dụng template: hiển thị đúng tên đơn vị, badge trạng thái, thông điệp "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.", nút "Về Trang chủ", điều hướng Back/Forward và URL deep link hash (`#unit=design`, `#unit=technical`, `#unit=bim`, `#unit=tadic`, `#unit=recruitment`).
- Chỉ áp dụng cho Admin hệ thống (`base.group_system` qua `user.isSystem`). Non-admin (`!user.isSystem`, ví dụ Trưởng Ban KH-KD `kd.thuyanh`) giữ nguyên 100% giao diện Trang chủ UI-HOME-003 (Không gian làm việc KH-KD + Công cụ cá nhân), không đổi mật khẩu, quyền hạn, grant hay tài khoản người dùng thật.
- Kiểm thử kỹ thuật toàn diện:
  + Odoo backend tests trên clone: 12/12 PASS (0 failed, 0 error).
  + HOOT unit tests trên clone: 27/27 PASS (100% xanh).
  + Playwright browser tests trên clone và dev 18069: PASS 100% (13 scenarios: admin 7 thẻ, 5 viewports 1440/768/390/320px không tràn viền, zoom 200%, reduced-motion, click 5 placeholder, back/hash, HR native, KD workspace; non-admin Thùy Anh layout UI-HOME-003 nguyên vẹn).
  + Backup verified trước apply: snapshot `backup-pre-apply-20261110T071809Z` (122 files, 592 bảng, 295 attachments) restore kiểm chứng thành công.
  + Bảo toàn dữ liệu dev 18069: kiểm chứng 39 bảng và 944 ACL/security rows bảo toàn nguyên vẹn; 0 dòng dữ liệu nghiệp vụ bị thay đổi.
- Hoàn thiện kiểm kê và đặc tả HR Foundation S0 trong `docs/architecture/TP_HR_001_FOUNDATION_PLAN.md`: xác định schema Odoo 20 (`hr.employee` trỏ `hr.version`), 7 phòng ban `hr_department`, 12 nhân viên hiện có, tích hợp canonical `tp.credential`, ma trận quyền 4 vai trò HR S1. Không commit/push. Next: Sẵn sàng triển khai HR-001 S1.

## CHG-20261110-004 — Thiết kế Home admin 7 mục và lộ trình HR-001

- Ngày 10/11/2026, DEC-036: thu hẹp UI-HOME-004 còn KH-KD, Thiết kế, Kỹ Thuật,
  BIM-QC, TADIC, Quản lý nhân sự, Tuyển dụng; chỉ Home quản trị. [Thiết kế](ui/UI_HOME_004_ADMIN_DESIGN.md)
  có hai nhóm rõ ràng, 4 placeholder, responsive/hover/focus/reduced-motion;
  phân biệt admin hệ thống với HEAD KH-KD, giữ Home/quyền người thường và
  nguồn tổ chức 9 nhóm/39 người. Đây là thiết kế, chưa áp dev18069.
- Preview tương tác nằm ngoài repo trong thư mục visualization của chat;
  evidence `.local/ui-home004-design/`: 31 kiểm tra Playwright đạt, 0 pageerror,
  đủ7mục, click/back/focus, 5width320–1440, light/dark/reduced-motion. Đã xem
  ảnh1024/390. Kiểm preview không thay test native Odoo hoặc security runtime.
- [Prompt admin-only](prompts/CLAUDE_UI_HOME_004_ADMIN_ONLY.md) thay prompt
  Home9nhóm cũ đã đánh dấu lịch sử. [Kế hoạch HR-001](architecture/TP_HR_001_FOUNDATION_PLAN.md)
  tái sử dụng HR native/version/organization: inventory/spec → list/form/quyền
  test → dry-run/mapping/nhập roster khi được giao → báo cáo → recruitment.
  Không bịa email/ngày làm/lương; employee khác user; không provision account.
- Kiểm tài liệu/link/ID, snapshot code không đổi và `git diff --check`;
  workflow finish/check theo CHG004. Không sửa application, DB, module, grant,
  credential hoặc runtime, không chạy Odoo tests cho batch thiết kế. Không
  commit/push. Next: xem thiết kế/giao Home triển khai; HR S0 inventory/spec.

## CHG-20261110-003 — Nguồn nhân sự mới và prompt Home đủ phòng/đơn vị

- Ngày 10/11/2026, STAFF-REF-001/DEC-034: người dùng cấp lại bảng công tuần1tháng11 và chốt dùng file mới. [Baseline](architecture/TP_STAFF_SOURCE_BASELINE.md) ghi39dòng/9nhóm/BanKD6, nguồn cũ38/10 với1mã chỉ có mới/0chỉ cũ/5mã đổi nhóm hoặc chức vụ. Trích mã/tên/chức vụ/nhóm và ô nguồn vào `.local/staff-reference-20261110/`, giữ ngoài Git; không lưu giờ vào/ra. Đối chiếu độc lập XML, mã unique/STT1–39/tổng nhóm và hash nguồn giữ nguyên. Không kết luận biến động lao động hoặc tự mapping user/quyền.
- UI-HOME-004/DEC-035: [prompt Claude](prompts/CLAUDE_UI_HOME_004_DEPARTMENTS_HR_RECRUITMENT.md) cho Home18069 gọn/có màu/responsive, 9nhóm (KH-KD thật+8placeholder riêng), hai lối vào Nhân sự/Tuyển dụng theo module/quyền thực, phân biệt đang phát triển/chưa cấp quyền. Giữ app switcher/personal/HEAD và quyền hiện có; không cài thêm module, không HR/grant/data import. Nguồn tổ chức cũ đánh dấu lịch sử; status/roadmap cập nhật cùng lượt.
- Kiểm tài liệu/liên kết/manifest, source workbook trước–sau, snapshot code và git diff --check/workflow. Lượt này chỉ source analysis/prompt/docs, không test Odoo/browser mới, không sửa application/DB/runtime/credential/grant, không stage/commit/push. Next Claude triển khai UI-HOME-004 trên clone, backup/restore verified trước áp dev; không tự thực thi prompt báo cáo.

## CHG-20261110-002 — KD-HEAD-001: HEAD quản lý KH-KD toàn phòng đã áp dev

- Ngày10/11/2026 (Asia/Saigon), thực hiện trực tiếp prompt KD-HEAD-001: role HEAD động theo user/company/phòng; tạo/sửa dự án/WBS/công việc, nháp nhân viên,7typed domain/contract/phụ lục/CRM/gói, tiền/file/report/XLSX và phân công/reviewer có reason/version/audit. Giữ state/bốn mắt/căn cứ đã gửi;4actor khác giữ quyền, không mở admin/pháp lý/toàn V2. [Ma trận và acceptance](demo/KD_HEAD_001_ACCEPTANCE.md), [guide](demo/KD_HEAD_001_USER_GUIDE.md).
- Clone:211/211 Odoo, HOOT22tests85assertions, native11+15, browser51, HTTP54;6Excel toàn page/cell/type/tổng và revoke/expiry cùng session PASS. Ruff/AST31Python,11XML,4JS.49files3addon hash6061d667e40765433b13a61ad74686462eef047acf08c7817cc72c504ea5fe24 test=seal=applied.
- Backup045731Z/restore045742 verified586tables295attachment refs122checksums rồi áp18069: workspace20.0.1.9.0/contract20.0.1.3.0; đúng HEAD96legacy inactive+1role+1event. Preservation277table7819oldrow/auth/config/owner và295blob cũ đạt,28audit ACL chuẩn và1assetJS ref mới có journal. Sai lệch hash Decimal→float được đối chiếu SQL/restore độc lập, không sửa số liệu DB. Dev5login51checks0JSerror/6040permission parity PASS; không fixture dev.
-7CRM+1project thiếu scope giữ chờ đối chiếu; warning markdown2/WindowsGC và giới hạn staff native Send UI được ghi trong acceptance. Business/visual/pilot riêng. Checker finish/check cùng batch; không commit/push.

## CHG-20261110-001 — Prompt HEAD toàn quyền nghiệp vụ KH-KD

- Ngày 10/11/2026 (Asia/Saigon), người dùng yêu cầu Thuỳ Anh/trưởng phòng toàn quyền trong phòng Kinh doanh. DEC-033 ghi yêu cầu; [KD-HEAD-001](prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md) giao triển khai clone-test → backup/restore verified → delta HEAD dev18069. Quyền toàn phòng gồm dữ liệu mới, nháp người khác, Project/WBS, điều phối, tiền/file/báo cáo/XLSX; giữ state/audit/bốn mắt, pháp lý và scope. Chưa duyệt V2 cho bốn actor còn lại hoặc cấp admin/grant administration.
- Đối chiếu source policy hiện hữu, ma trận/V2 và trạng thái CHG014/016; `dev.py status` báo HTTP18069/Postgres lắng nghe. Lượt này chỉ prompt/DEC/status/roadmap; không cấp role/grant, sửa source ứng dụng hoặc DB/runtime, không chạy test business/action/export thật. Kiểm tài liệu/liên kết, diff và snapshot workflow; không commit/push. Next Claude thực thi prompt và bàn giao quyền thực cùng acceptance.

## CHG-20261109-016 — KD-REPORT-UI-002: kế hoạch, preview desktop/mobile và hai mẫu Excel

- Ngày 09/11/2026 (Asia/Saigon); task KD-REPORT-UI-002, `DESIGN_PREVIEW_READY_PENDING_USER_REVIEW`. [Kế hoạch](ui/KD_REPORT_UI_002_REDESIGN_PLAN.md) đánh giá 6 báo cáo, so A/B và đề xuất A, ma trận KPI/chart/cột/ngày/drilldown/Excel, token màu/contrast, filter pending/applied, workbook và lộ trình S0–S5/17 acceptance. [Prompt triển khai](prompts/CLAUDE_KD_REPORT_UI_002_IMPLEMENT.md) là tài liệu chuẩn bị, chưa giao chạy.
- Artifact local `.local/kd-report-ui002/`: preview HTML tương tác A/B và 6 báo cáo, 12 ảnh desktop/mobile cùng ảnh dialog/chooser/states; hai workbook R01/R05 dữ liệu giả lập, mỗi file Tong_quan/Tong_hop_nhom/Chi_tiet. XLSX typed number/date/text0001, tổng tách currency/basis, gốc/phụ lục/hiệu lực không cộng trùng, màu/filter/freeze/print được kiểm bằng openpyxl; artifact-tool import/render đủ 6 sheet. Renderer làm mất hiển thị số 0 đầu trong PNG, XLSX gốc đã kiểm giữ text; chưa mở Excel desktop/in giấy. Preview dùng fixture khác workbook, không nhận web–file parity đã đạt.
- Kiểm mới: `dev.py status`, SELECT read-only module20.0.1.8.0; Playwright baseline 6 report × desktop/mobile + 6 vùng bảng (18 ảnh, 0 pageerror), cùng phiên/quyền/bộ lọc; `node .local/kd-report-ui002/verify_preview.cjs` **63 checks PASS/0 JS errors** cho preview; builder/reader XLSX và render checks đạt; kiểm hash ứng dụng, links/artifacts, `git diff --check`, workflow finish/check. Không chạy lại Odoo/HOOT hoặc tải export thật từ dev. Login chỉ tạo session/log kỹ thuật; không ghi nghiệp vụ/đổi account/grant/DB/config/restart/upgrade dev. Preview HTTP riêng localhost18762 chỉ phục vụ file tĩnh; source ứng dụng trước–sau giữ nguyên; không stage/commit/push.
- Ghi nhận source gaps chưa tái hiện regression: search thu hẹp bảng nhưng KPI/chart chưa tính lại cùng tập; vài sortable header thiếu whitelist; chuyển report áp pending; metadata can_view_money thiếu key; ngày/transport khác thiết kế cũ. R02 vẫn CRM, không thống kê package/attempt; export dùng financial_read, chưa financial_export guard riêng. Giữ nguyên policy/công thức và gate; không mở lại F1–F3 restructure đã sửa. Next người dùng xem thiết kế/mẫu rồi giao S0–S4 trên clone; dev apply, visual/business/pilot riêng.

## CHG-20261109-015 — Prompt lên kế hoạch làm lại giao diện báo cáo và xuất Excel

- Ngày09/11/2026; [KD-REPORT-UI-002 plan](prompts/CLAUDE_KD_REPORT_UI_002_PLAN.md) theo ảnh người dùng: bố cục thoáng, tên tab đủ, token màu, chữ/số rõ, KPI ngắn, bảng cột tách chỉ tiêu, biểu đồ đúng6report, bộ lọc và luồng xuất Excel toàn kết quả có xác nhận phạm vi. Đã đọc source export hiện có, không nhận đang thiếu XLSX. Đầu ra giao Claude: kế hoạch/wireframe/preview, hai mẫu workbook giả3sheet có màu/kiểu ô/filter/freeze và acceptance/prompt code tiếp.
- Chỉ prompt/status/roadmap; baseline CHG014 hiện20.0.1.8.0, không sửa code/DB/account/quyền/runtime/DEC hoặc commit/push. Kiểm tham chiếu/nội dung/diff/digest và workflow; không chạy Odoo/browser/XLSX export trong lượt này, không nhận đã audit file tải thật hoặc thiết kế đã triển khai. Next Claude làm plan+preview/mẫu local trước khi nhận lệnh code.

## CHG-20261109-014 — KD-PROJECT-RESTRUCTURE-001 S4

- Ngày: 09/11/2026 (Asia/Saigon).
- Kết quả/test/giới hạn: IMPLEMENTED_VERIFIED_DEV_PENDING_BUSINESS_VISUAL_PILOT. Applied58file tp_kd_workspace20.0.1.8.0 to dev18069 after final185/1850failed0error,HOOT20/78,UI61+extra10+related25+productionpagingBack29,independentpermission110 with explicit runtime assurance. Final tree89c17f28511daceaf3f064faecad6064517756c50de04dcab8d52d827f0df927 test=seal=applied. Freshbackup131132Z/restore131138 verified122files578tables295attachments. Upgrade0error;83tables4529oldrows/account/auth/MFA/passkey/grants/assignments/owner/config/modules retained before-after-upgrade/smoke;295fileshashsizeverified;newbusinessmodels0rows. Dev53checks5existinglogin0JSerror/noUImutation;wrapper25404listener10096PG13900,clone19489stopped/evidencekept. No real-user grants/password/owner changes;14project25CRM investor/package mapping unresolved NULL, legacyowner handoff pending. Guide/9requirements16AT/migration/rollback/actualdevscreenshots documented. Warnings markdown2/WinError5GC retained; Chromium not physicaldevice; transient native reload facets require Favorites; no committed winner-loser race. V2/business/visual/pilot separate; no commit/push. Root tooling baseline unchanged; Next user walkthrough and approved mapping/grant delta only.
- Không commit/push; trạng thái dev18069 theo kết quả chặng trên; V2/người thật/business/pilot riêng.


## CHG-20261109-013 — KD-PROJECT-RESTRUCTURE-001 S3

- Ngày: 09/11/2026 (Asia/Saigon).
- Kết quả/test/giới hạn: S3_NATIVE_VERIFIED_TEST_ONLY. Hai menu/action/landing/detail native dung chung project ID; WBS/task va7nguon quan tri khac muc dich;9yeu cau/model/capability/mapping/list/detail wired. Final185/185 Odoo0failed0error, HOOT20/78, UI61/extra10, pagingBack29/29production, related25;20XML10JS/Ruff22/patchcheck. Audit110assertion PASS with final runtime comparison after public-token correction and native Back hook. Seal89c17f28511daceaf3f064faecad6064517756c50de04dcab8d52d827f0df927,58file private workspace. Root addon/dev20.0.1.7.0 still unchanged; next S4 fresh backup verified, gated apply/preservation/5login read-only. No real grants/owners/V2 approval/commit/push.
- Không commit/push; dev18069 chưa đổi; V2/người thật/business/pilot riêng.


## CHG-20261109-012 — KD-PROJECT-RESTRUCTURE-001 S2

- Ngày: 09/11/2026 (Asia/Saigon).
- Kết quả/test/giới hạn: S2_BACKEND_VERIFIED_TEST_ONLY. Model project lifecycle/investor/version; package/attempts; participation roles; separate package_total/company_offer/company_share; append-only project/task history, capability commands WBS/assignment/progress implemented only .local/kd-project-restructure001/workspace/custom_addons. Targeted8/8 and full5addon176/176 (0failed/0error). Unknown/0, A/B counterparty, 2packages/attempts, submitted note snapshot, stale/retry/reopen denial, task vs money verified. Initial ACL operation typo and wizard reason required corrected before final tests. Migration automatic schema only; 25CRM package/investor unresolved kept NULL, no inferred data/owner/grant delta. Mapping apply/rollback non-empty and security independent audit still pending; no dev apply. Next S3 native2landings/lists/details and browser.
- Không commit/push; dev18069 chưa đổi; V2/người thật/business/pilot riêng.


## CHG-20261109-011 — KD-PROJECT-RESTRUCTURE-001 S1

- Ngày: 09/11/2026 (Asia/Saigon).
- Kết quả/test/giới hạn: S1_TECHNICAL_VERIFIED_TEST_ONLY_PENDING_INDEPENDENT_AUDIT. F1-F3 tái hiện 3 failed/4 trước sửa; sau sửa 4/4 và hồi quy targeted12/12, full5addon168/168 (0failed/0error). HTTP native mới17assertion đạt: PDF/download đọc đúng quyền; update/post/upload pending/delete/thumbnail submitted bị chặn, response không chứa marker bí mật. Sửa chỉ source riêng models/native_content_security.py và controllers/native_security.py cùng test. Regression ban đầu2error automatic creation chatter đã sửa bằng mail_create_nolog trong scoped create; log markdown2/WinError5 còn. Chưa đủ hậu kiểm độc lập/race/revoke HTTP nên chưa đóng audit hoặc áp dev. Next S2 dữ liệu/action/guard trên test, giữ đường file/chatter mới đóng.
- Không commit/push; dev18069 chưa đổi; V2/người thật/business/pilot riêng.


## CHG-20261109-010 — KD-PROJECT-RESTRUCTURE-001 S0

- Ngày: 09/11/2026 (Asia/Saigon).
- Kết quả/test/giới hạn: S0_VERIFIED_TEST_ONLY. Inventory/design/16 AT trước code tại docs/ui/KD_PROJECT_RESTRUCTURE_001_DESIGN.md trong workspace riêng .local/kd-project-restructure001/workspace. Snapshot/restore exact 578 bảng/295 attachment; dry-run 14 project/25 CRM, không suy investor/gói/kết quả. Baseline Odoo 164/164 (0 failed/0 errors), có markdown2 warning và WinError5 filestore GC. Root checker CHG009 đạt, không checkpoint ngoài scope. Dev PID/source/quyền giữ. Next S1 tái hiện và sửa F1-F3 trên clone19489.
- Không commit/push; dev18069 chưa đổi; V2/người thật/business/pilot riêng.


Mỗi lượt thay đổi code hoặc quyết định kiến trúc ghi một mục ngắn. Không ghi credential, dữ liệu thật hoặc log chứa bí mật.

## CHG-20261109-009 — KD-REPORT-001: Tách Trung tâm Báo cáo KH-KD (OWL native) và xuất Excel an toàn

- Ngày 09/11/2026; theo yêu cầu người dùng và prompt [CLAUDE_KD_REPORT_001_SEPARATE_REPORT_CENTER.md](prompts/CLAUDE_KD_REPORT_001_SEPARATE_REPORT_CENTER.md), tách Báo cáo KH-KD thành phân hệ riêng biệt (`tp.kd.report.center`, `js_class="tp_kd_report_center"`), nâng cấp `tp_kd_workspace` 20.0.1.7.0 trên dev18069 (`tp_tanphat_dev`). Hai menu độc lập: Tổng quan (`action_overview`) phục vụ theo dõi hằng ngày, Báo cáo KH-KD (`action_reports`) phục vụ tổng hợp kỳ, đối chiếu và xuất Excel.
- Xây dựng đủ 6 nhóm báo cáo R01–R06: R01 Hợp đồng (không cộng trùng phụ lục, chỉ tính bản hiệu lực); R02 Cơ hội/thầu (>100 leads, phân trang 10/20/50/100, lọc unassigned); R03 Đối chiếu 4 chặng Kế hoạch – Sản lượng – Nghiệm thu – Đề nghị thanh toán (không cộng dồn chéo); R04 Giao khoán cấp 1 và cấp 2 (tách biệt tiền khoán con khỏi cha, cảnh báo vượt khoán); R05 10 nguồn hồ sơ và trách nhiệm/SLA; R06 Năng lực, chứng chỉ và nghĩa vụ (tách cá nhân/tổ chức, ngưỡng cảnh báo 30 ngày, đếm chính xác).
- Đầy đủ tính năng báo cáo chuyên nghiệp: bộ lọc kỳ/dự án/người phụ trách, pending filter notice trước khi Apply, drill-down mở bản ghi nguồn Odoo, phân trang 10/20/50/100, nhóm dữ liệu và tổng nhóm. Tích hợp controller `/tp_kd/report/export` xuất Excel định dạng chuẩn OpenPyXL với công thức chống injection ký tự rủi ro. Cơ chế bảo mật tiền: tài khoản không có quyền tài chính (`fin_pids` rỗng) được che toàn bộ số tiền trên giao diện, summary cards và metadata Excel.
- Kiểm thử & Bảo toàn: HOOT tests 14/14 PASS (57 assertions); Odoo tests 164/164 PASS; Clone Playwright 109/109 PASS; Dev Playwright 105/105 PASS. Hiệu năng dưới 1.5s cho toàn bộ 6 báo cáo và xuất Excel. Backup snapshot verified trước apply và restore kiểm chứng thành công vào `tp_tanphat_kdreport001_backup_110322` (577 bảng, 295 attachments). Bảo toàn dev database sau apply: 37 bảng/3.467 dòng (chính xác +1 dòng `ir_access` cho model mới, 0 dòng nghiệp vụ thay đổi). Dev server running trên port 18069.
- Tài liệu bàn giao: [User Guide](demo/KD_REPORT_001_USER_GUIDE.md), [Acceptance Report](demo/KD_REPORT_001_ACCEPTANCE.md), 86 ảnh kiểm chứng tại `.local/kd-report001/shots/`, 16 file Excel tại `.local/kd-report001/excel/`. Không commit/push.

## CHG-20261109-008 — Prompt tách Quản lý/Quản trị dự án và hoàn thiện các ý sau họp

- Ngày09/11/2026; theo yêu cầu trực tiếp, ghi DEC-032 tách hai khu vực chức năng cùng project ID và soạn [prompt KD-PROJECT-RESTRUCTURE-001](prompts/CLAUDE_KD_PROJECT_RESTRUCTURE_001.md): sidebar/action/landing/detail riêng,9ý và2làm rõ, dữ liệu project/gói/đối tác/giá/tình trạng-note, mapping/migration/rollback/quyền,16AT và chặng S0–S4. Bao gồm dependency F1–F3, owner/reviewer mẫu cũ và hướng dẫn nút/state; đích18069 qua test/audit/backup restore, không tự duyệt V2/TASK-001/grant người thật hoặc BASE/ký/hiệu lực/hạch toán.
- Áp dụng skill delivery/Ponytail/frontend-design để chuẩn bị prompt; subagent lỗi model nên tự kiểm tài liệu. Cập nhật status/roadmap/ghi chú phân tích; kiểm link/AT/scope/diff và digest384file trước–sau: có delta đồng thời scripts/kd_report001.py ngoài batch,383file còn lại giữ; không nhận toàn bộ code bất biến hoặc kiểm hộ delta đó. Phiên này không sửa application/DB/account/quyền/runtime, không chạy Odoo/browser tests cho lượt tài liệu, không commit/push. Checkpoint công việc khác không finish thay; Next Claude đối chiếu bàn giao report/source mới rồi thực thi đúng nguồn/test và bàn giao từng chặng.

## CHG-20261109-007 — Phân tích yêu cầu KH-KD sau cuộc họp

- Ngày09/11/2026; ghi9ý và2trả lời trực tiếp: Người phụ trách trước Hạn nộp, đối tác nhiều loại có vai trò. [Phân tích](architecture/TP_KD_MEETING_REFINEMENT_20261109.md) tách yêu cầu ghi nhận với thiết kế đề xuất: project/gói, chủ đầu tư khác bên ký, lifecycle khác thầu/rà soát, note có lịch sử, giá gói khác doanh thu/giá chào/hợp đồng, quản lý thực hiện khác quản trị KH-KD. Đối chiếu source/bridge/guard tiền, chưa duyệt model/state mới.
- Cập nhật status/roadmap; kiểm link/nội dung/diff và digest app/tooling trước–sau, không Odoo test cho tài liệu. Không code/DB/account/quyền/runtime/DEC/commit/push. F1–F3/V2/gate cũ giữ; checkpoint công việc khác không finish thay. Next đặc tả/mapping/acceptance trước prompt code.

## CHG-20261109-006 — Kiểm chứng phản ánh HEAD/SUPPORT lệch tác vụ

- Ngày09/11/2026; kiểm UI đăng nhập riêng và RPC chỉ đọc trên dev18069: SUPPORT tạo CRM/credential, HEAD chỉ CRM; cả hai không được create/write/unlink Project/Contract. Clone source ba addon khớp dev,14thử ghi/xóa và xác nhận wizard hợp đồng bị AccessError; rollback và đối chiếu giữ bản ghi. [Kết quả, nguyên nhân preset và giới hạn](reviews/KD_ROLE_UI_VERIFICATION_20261109.md). Chưa tái hiện SUPPORT lưu Project/Contract theo phản ánh; xác nhận HEAD hiện thiếu quyền chuẩn bị hồ sơ so với hướng trưởng ban quản lý toàn Ban.
- Evidence JSON/támảnh private ignored; một lỗi console encoding sau khi ghi JSON đã đọc lại, cảnh báo markdown2 giữ. Không sửa application/quyền/account/password/dữ liệu dev hoặc runtime, không commit/push. V2 vẫn chờ người dùng duyệt, chưa prompt triển khai; audit F1–F3 và các gap khác giữ mở. Không finish checkpoint công việc khác; kiểm diff/link/JSON giới hạn trong batch này.

## CHG-20261109-005 — Đề xuất V2 phân quyền KH-KD, chờ người dùng duyệt

- Ngày09/11/2026, Asia/Saigon; chỉ thiết kế theo yêu cầu, chưa viết prompt triển khai mới. Đọc lại phân công S02 snapshot/registry và workflow KD/BIZ002; NAS không truy cập được, không nhận bản trích là văn bản nhân sự hiện hành. [Đề xuất V2](security/KD_ROLE_POLICY_V2_PROPOSAL.md) có ma trận xem/ghi/tiền/tài liệu/Project–WBS/nhập-xuất/review/phân công và ví dụ5vai, tách thẩm quyền BASE/ký/kế toán và IT. HEAD mở phạm vi quản lý nghiệp vụ đề xuất, không nhận quyền đã cấp.
- Cập nhật status/roadmap và link đề xuất; không đổi ma trận runtime hoặc DEC thành đã chấp thuận. Kiểm link/nội dung/diff và source không đổi trong lượt; không cần test Odoo cho tài liệu. F1–F3 audit004 vẫn mở. Không sửa ứng dụng/database/quyền/password, không commit/push. Checkpoint công việc khác giữ, không finish thay batch code chưa bàn giao. Next user duyệt ma trận rồi mới viết prompt V2.

## CHG-20261109-004 — Hậu kiểm KD-ACCESS-002: ba lỗi quyền native cần correction

- Ngày09/11/2026, Asia/Saigon; kiểm source/runtime và chạy lại Odoo157/157, quyền dev1426/clone1426,274 assertion nghiệp vụ rollback + kiểm bảo toàn account/rights, browser dev112 và native flows clone30, source clone=seal=dev. Không sửa application code/core, không cấp quyền/password hay ghi nghiệp vụ trên dev; không restart/upgrade dev, không commit/push.
- Các kiểm tra native bổ sung xác nhận3lỗi P1: preview PDF lộ nội dung khi thiếu quyền tiền; upload/delete thay file trên CRM submitted qua nhánh nâng quyền; update chatter trả nội dung đang bị chặn đọc. Hạ kết luận KD-ACCESS-002 thành `AUDIT_FAILED_SECURITY_CORRECTION_REQUIRED`, A06 chưa đạt. [Audit](reviews/KD_ACCESS_002_INDEPENDENT_AUDIT.md), [prompt sửa](prompts/CLAUDE_KD_ACCESS_002_SECURITY_CORRECTION.md); evidence riêng `.local/kd-access002-audit-20261109/`. Cập nhật status/roadmap/acceptance/ma trận và lưu giới hạn Project/WBS, phân loại tài liệu, Q2/business/pilot. Không sửa lịch sử test CHG003 thành kết quả mới.
- Lượt Odoo có PermissionError khi dọn filestore clone và cảnh báo markdown2 dù157test0fail/error; chưa thay filesystem ACL. Không chạy lại HOOT/backup/restore/full rollback, số cũ chỉ là bằng chứng triển khai. Subagent không chạy được do lỗi model; không tính là review. Resume checkpoint có code/docs khớp baseline003, giữ checkpoint gốc; handoff chỉ tài liệu audit. Cuối lượt có delta đồng thời scripts/kd_report001.py ngoài scope; không finish/check PASS thay batch đó, giữ checkpoint và state cũ. Next sửa F1–F3 trên test cô lập, hậu kiểm lại trước áp18069 hoặc mở Project/WBS.

## CHG-20261109-003 — KD-ACCESS-002: quyền KH-KD và CRM scoped trên dev18069

- Ngày09/11/2026, Asia/Saigon; user giao thực thi toàn prompt, chờ navbar/login bàn giao rồi dùng checkpoint riêng và áp18069 sau clone/backup. Workspace20.0.1.6.0/Home20.0.1.4.1;5account nhận42grant cơ hội,1native team/5membership và export implication. Reader8/4/4/4/2 và grant/owner/reviewer cũ giữ; không sales/admin/manager. Native `sale_team_id`5user tự tính theo team mới, journal/test rollback; các cột tài khoản nội dung/bảo mật khác/password/TOTP/config giữ, tách dấu vết ORM write_uid/write_date. Bỏ nhãn công ty ở navbar, không đổi tên công ty trong data.
- CRM owner-only, prepare/submit tách; scope project/company và pre-project owner/team/đơn vị/capability; submitted freeze;6money/derived field/domain/order/group/export/related guard, money wizard kiểm lại khi lưu; attachment/chatter parent+financial, direct/token/public của actor scoped không bypass, write/file/submit row lock. Form sạch refresh5giây, dirty input giữ và backend kiểm ngay. Trước sửa tái hiện prepare-only submit/native-money leak trên clone rồi rollback.
- Clone Odoo157/157, quyền1426, mutation275rollback, browser175/5context/desktop-mobile, native write30, HOOT11+25; exact rights/source rollback/reapply và idempotency đạt. Dev1426quyền/112browser/4auth,0error, chỉ đọc nghiệp vụ. Backup122file/checksum/restore576bảng/295refs; exact17file apply/233file addon khác nguyên. Preservation244bảng/6094dòng ngoài delta,282nonasset attachments/295reference/116blob unique và password/config đạt. Tool hash default binding cũ sửa+rerun; apply đầu registry cũ làm cấp quyền rollback0grant, recovery tiến trình mới đúng42grant sau kiểm source/upgrade; không restore DB đè writer. Ruff/XML4/JS/diff/workflow checker ở handoff.
- [Ma trận](security/KD_ACCESS_002_ROLE_MATRIX.md), [inventory](security/KD_ACCESS_002_INVENTORY.md), [acceptance/rollback](demo/KD_ACCESS_002_ACCEPTANCE.md), [guide5vai](demo/KD_ACCESS_002_USER_GUIDE.md), [ảnh](../.local/kd-access002/comparison/index.html). Clone19289 dừng, dev18069/PG55432 chạy. Project/WBS scoped write chưa có, [follow-up](prompts/CLAUDE_KD_SCOPED_PROJECT_TASK_FOLLOWUP.md); file/chatter coarse, report hiện dùng Tổng quan. Chưa import CSV wizard/Safari/thiết bị thật/multi-company E2E; spawn lỗi model nên chưa audit độc lập, business/Q2/pilot riêng. Không commit/push. Next người dùng kiểm guide/ảnh5vai; chỉ mở follow-up khi được giao.

## CHG-20261109-002 — Navbar và bộ xác thực native mới trên dev18069

- Ngày09/11/2026, Asia/Saigon; người dùng giao thực thi toàn UI-SHELL-AUTH-001, clone/backup verified/áp18069; ngoại lệ vai trò giới hạn task. Home20.0.1.4.0/Login20.0.1.1.0: navbar56px navy/wordmark/app/context/user; login hai vùng, chooser/TOTP/signup/reset cùng nhận diện, mobile/hover/focus/motion180ms/reduced-motion. Giữ native NavBar/adapt/More/section/systray/Home/dirty guard và logout POST+CSRF/service-worker/PWA. Không model/controller/API/quyền/nghiệp vụ mới; Login manifest bỏ data ghi auth policy, TOTP cancel về `/web/login`.
- Clone owned19189/source/config/filestore riêng: Odoo62/62 (Home12/Login5/Workspace45), browser120, failure15, zoom200% thật5, bổ sung18, passkey virtual authenticator6bước; TOTP/trusted-device/session/CSRF/deep-link/native form đạt. Policy clone khác giữ absent-install/disabled-upgrade. Source cuối đã chỉnh placeholder4,94:1, test=seal=dev. Dev browser110+bổ sung18/sáu actor,0console/pageerror, chỉ đọc/nghiệp vụ. Timeout selector/animation/session-ready trong harness được sửa/chạy lại; không lấy report cũ làm gate.
- Backup cuối `backup-pre-apply-20261109T025630Z`:122file checksum/576bảng/295reference, restore owned verified; apply chỉ hai addon rc0/0error. Sau smoke267bảng/8.144dòng,282attachment ngoài assets, config/account/password/quyền/HomeAction giữ;295reference/116blob unique checksum+size và blob cũ còn;213file addon khác nguyên. Một native profile writer trong apply đầu thay5ảnh avatar đã được phát hiện/đối chiếu/giữ, backup cuối chứa ảnh mới; không restore DB đè writer. Dev18948/PG55432 listener13900 chạy, clone dừng, DB/evidence giữ.
- [Thiết kế](ui/UI_SHELL_AUTH_001_DESIGN.md), [acceptance A01–A12](demo/UI_SHELL_AUTH_001_ACCEPTANCE.md), [guide5bước/rollback](demo/UI_SHELL_AUTH_001_USER_GUIDE.md), [ảnh trước–sau](../.local/ui-shell-auth001/comparison/index.html), scripts `ui_shell_auth001*`; Ruff/JS/XML8/diff/workflow checker. Không React/core/dev.py/commit/push. Subagent không chạy được do model kế thừa: tự kiểm, visual acceptance/audit độc lập/business/pilot vẫn riêng. Chưa thiết bị thật/Safari/scoped PWA/full multi-company/password-manager UI; OAuth uninstalled, signup/reset giữ native GET/form không gửi mail test. Next người dùng Ctrl+F5/kiểm5bước và phản hồi thiết kế.

## CHG-20261109-001 — Prompt làm lại navbar và bộ giao diện xác thực native

- Ngày09/11/2026, Asia/Saigon; phiên điều phối soạn [UI-SHELL-AUTH-001](prompts/CLAUDE_UI_SHELL_AUTH_001_NAVBAR_LOGIN_LOGOUT.md) theo ba ảnh: navbar navy đồng bộ sidebar, login hai vùng, chooser/TOTP/logout cùng nhận diện, mobile/hover/focus/motion. Skill frontend-design và delivery của repo; A01–A12, clone/test/backup/apply18069 và evidence trước–sau cho Claude. Chưa sửa giao diện hoặc triển khai.
- Đối chiếu native NavBar/UserSwitch/UserMenu/templates và addon: login custom còn uninstalled trên dev; data lần cài mới có tác dụng đổi signup/reset policy, TOTP cancel còn `/work/`. Prompt xử lý bảo toàn config và đường native, giữ logout POST/CSRF/service-worker/PWA, nguồn remembered-user native và quyền/dữ liệu hiện hữu; không mở business gate hoặc nghiệm thu AUTH-002 lịch sử.
- Chỉ đọc source/runtime/SELECT và sửa prompt/status/changelog/roadmap; không application code, DB mutation, setup/upgrade/seed/restart, tài khoản/quyền hoặc commit/push. Kiểm nội dung/link/fence/ID, source digest bằng checkpoint, diff và workflow finish/check; không application tests cho tài liệu. Spawn subagent lỗi model kế thừa nên không có audit độc lập. Next: giao Claude prompt, nhận ảnh/diff/log rồi audit delta và visual feedback.

## CHG-20261108-005 — Word trình bày và hướng dẫn sử dụng KH-KD với ảnh giao diện thật

- Ngày08/11/2026, Asia/Saigon; tạo [Word local](../.local/khkd-word-manual/TANPHAT_ONE_Huong_dan_trinh_bay_va_su_dung_KHKD.docx)29trang/25hình, kịch bản20phút, luồng/phân quyền/phạm vi năm vai trò, từng nhóm hồ sơ, thêm/sửa/gửi/trả/gửi lại, bộ lọc/phân trang, tài khoản/mobile, xóa và lỗi thường gặp. Danh tính/login nằm ignored `.local/`, không mật khẩu, không nhân sự vào tracked fixture. Dùng skills documents, playwright-cli và delivery của repo; giữ native Odoo, không sửa application code hoặc quyền. Không coi dữ liệu tổng hợp hoặc quyền kỹ thuật là phân công thật/duyệt ký/pilot.
- Dev36ảnh mới/năm phiên vai trò+actor CRM kỹ thuật,0pageerror; clone owned19089 minh họa credential draft→in_review→returned→draft→in_review/version6 bằng hai tài khoản. Ghi rõ Xóa/Nhân bản đang ẩn ở typed dossier/TP Contracts, dấu X là discard. Một nháp thử riêng trên clone được xóa qua backend guarded, hồ sơ có lịch sử giữ; dev chỉ đọc/mở-hủy, không seed. Evidence/scripts/Word private `.local/khkd-word-manual/`.
- Khởi động PG hiện hữu sau crash recovery và start dev bằng helper có sẵn, không setup/upgrade/reset/config; clone19089 dừng cuối lượt, dev18069/PG55432 chạy. Code digest306file bằng checkpoint; renderer thường thiếu LibreOffice, dùng Word COM chỉ tài liệu task-owned rồi rasterize bằng renderer đóng gói;29trang kiểm ảnh,25inline/no title border/password scan đạt. Kiểm link/ignore/diff/workflow finish/check, không test lại cả ứng dụng cho lượt tài liệu, không commit/push. Spawn subagent không khả dụng do model kế thừa, không gọi kiểm này là audit độc lập. Next người dùng tập trình bày từ trang3, đối chiếu quyền trang6 và ghi góp ý; các gate nghiệp vụ/audit UI/Q2/pilot và gap CRM/handoff hỗ trợ giữ riêng.

## CHG-20261108-004 — Thêm Tài khoản trong thanh bên KH-KD

- Ngày08/11/2026, Asia/Saigon; theo yêu cầu trực tiếp và ảnh, thêm **Tài khoản** trên **Tùy chọn hiển thị**. Workspace20.0.1.5.2 reuse native `preferencesItem()` cho đúng user; profile ảnh/tên/email/điện thoại/tùy chọn/lịch/bảo mật, giữ style/rail/keyboard và đóng mobile drawer trước modal. Không backend/security/API/schema hoặc password/grant mới; không commit/push. [Cách dùng và acceptance](demo/KD_ACCOUNT_001_ACCEPTANCE.md); tooling clone/backup/apply tái sử dụng có exact hash/fresh backup/baseline guard, lỗi browser redact password.
- Clone19089 restore576table/294reference; Odoo45/45, browser107/6actor/0error ở lượt cuối, save/restore phone và dirty dossier chỉ clone. Backup verified116file rồi apply riêng workspace lên18069 rc0/0error/changed_tables{}; dev browser103/6actor/0error chỉ mở/hủy. Sau browser37table3.416row/282nonassetattachment/93module/5group tables nguyên,294reference/110blob checksum/kích thước đạt,181file addon khác nguyên và source=seal; clone19089 dừng, dev18069/PG55432 chạy. Subagent review source/tooling không còn finding; native session transient, lỗi catch harness và thử chặn serviceworker ở lượt thăm dò không là gate. Giữ audit UI cũ/business/Q2/pilot riêng, chưa thiết bị thật/rollback dev. Ruff/JS/XML/diff/workflow và status/roadmap/handoff cùng lượt; Next người dùng Ctrl+F5 kiểm Tài khoản.

## CHG-20261108-003 — Provision năm tài khoản KH-KD trên dev sau clone và backup

- Bổ sung60kiểm file HTTP/RPC trên clone cho5role: normal/revoked/expired/unassigned, hai URL binary/attachment và direct RPC; checksum actor đúng quyền, support/ngoài scope/mất quyền bị chặn; quyền restore trong finally. File probe chỉ clone, journal private, không business-write dev.

- Ngày08/11/2026, Asia/Saigon; KD-ACCESS-001, thực hiện prompt theo yêu cầu trực tiếp, không commit/push. Clone18989/source riêng rồi backup verified112file/576table/269attachmentreference; áp riêng `tp_kd_workspace`20.0.1.5.1 và5user/22reader assignment/64project grant/258typed grant lên `tp_tanphat_dev`18069/55432. Password riêng dev/clone, không reset/adopt account mẫu, gửi thư hoặc tạo HR employee; danh tính/credential/delta private ACL hạn chế, tracked chỉ role alias.
- Security nhỏ: nhóm scoped staff implies TP reader, hai restriction đọc Project/Task theo active assignment/company; giữ actor cũ. CRM/cơ hội giữ chưa cấp vì prepare gộp khai báo nộp và thiếu owner/tiền guard; không manager/all-leads hoặc mở project-create/WBS-write. Workflow/schema/API/UI assets giữ. [Acceptance](demo/KD_ACCESS_001_ACCEPTANCE.md), [guide](demo/KD_ACCESS_001_USER_GUIDE.md), native workflow/status/roadmap cập nhật; tooling `scripts/kd_access001*` reuse clone/backup/ORM hiện có, rollback archive/revoke exact delta.
- Test cuối: Odoo118/118 (45workspace+73contract), clone/dev audit1426 mỗi môi trường, mutation/rollback clone276, browser98 mỗi môi trường/5session/25ảnh/0error. Ca lỗi export test đầu và browser timeout được sửa/chạy lại, không dùng lượt fail để apply. Dev upgrade rc0/0error/changed_tables{};93table4.165→4.574row/0oldmissing-changed ngoài write metadata; account/password/group/grant cũ giữ nội bộ,106unique blob/269reference/source/module registry giữ đúng đối chiếu.5welcome task+35personal stage+5relation do Odoo hooks giống clone, journal và giữ, không tính hồ sơ KH-KD. Normalize riêng5timezone sau first-login alias, password giữ. Ruff/JS/XML/diff/workflow checker; không React/core. Tự kiểm, subagent lỗi model; audit độc lập/business/Q2/pilot riêng. Next: người dùng đổi5vai theo guide; CRM còn gap rõ.

## CHG-20261108-002 — Kiểm kê tài khoản KH-KD và prompt phân quyền năm vai trò

- Ngày08/11/2026, Asia/Saigon; đáp ứng yêu cầu kiểm tra tài khoản riêng cho năm nhân sự và viết prompt nếu thiếu. SELECT read-only trên dev `tp_tanphat_dev`/55432 xác nhận20user, bốn actor KH-KD tổng hợp, chưa có năm login đề xuất; actor mẫu tên gần không được coi là danh tính nhân sự thực. Không tạo/đổi account, password, group, assignment/grant hoặc dữ liệu nghiệp vụ.
- Thêm [KD-ACCESS-001](prompts/CLAUDE_KD_ACCESS_001_STAFF_ACCOUNTS.md): ma trận năm role, quyền tiền/capability/owner/reviewer riêng, scope minh họa có provenance, không copy quyền quản trị fixture; clone/test/backup rồi áp delta18069, credential private/idempotency/rollback và hướng dẫn đăng nhập. Mapping nhân sự và evidence chỉ lưu ignored `.local/kd-access001/`, không fixture tên thật vào Git; phân công dev không là bổ nhiệm thực tế hoặc đóng Q2/pilot. Status/roadmap cập nhật, UI audit pending giữ riêng.
- Kiểm source/caller, link/fence/mapping/ignore/digest/diff và workflow finish/check. Không application test vì không sửa app; không restart/upgrade/seed/commit/push. Subagent lỗi model kế thừa, tự kiểm tài liệu, không gọi audit độc lập. Next: Claude thực hiện prompt, bàn giao5account/quyền thực tế và cách đổi vai sau kiểm chứng dev.

## CHG-20261108-001 — Tổng hợp nghiệp vụ KH-KD, vai trò và thông tin còn thiếu

- Ngày08/11/2026, Asia/Saigon; theo yêu cầu người dùng phân tích lại tài liệu đã gửi, thêm [bản tổng hợp có căn cứ](architecture/TP_KD_BUSINESS_RECAP_AND_GAPS.md):4mảng/8chặng vận hành,5vị trí theo phân công tháng4/2026, bên phối hợp, dữ liệu/nguyên tắc đã có và gap theo Q1–Q14. Không đổi workflow master/DEC hoặc coi đề xuất/fixture là bổ nhiệm quyền thật. Nêu rõ NAS chưa truy cập được, nhân sự hiện hành cần xác nhận và PKH snapshot khác bản tham khảo sau; không đưa dữ liệu nhân sự thô vào Git.
- Đọc lại S01/S02 extract và ảnh phân công;5hash local sources khớp manifest lịch sử, không chạy macro/refresh link hoặc import. Link/fence/diff/digest và workflow finish/check; không sửa app hoặc chạy application test, không DB/runtime/commit/push. Bàn giao UI KD-UI-007 giữ pending audit/visual/business/pilot riêng. Next nghiệp vụ: cập nhật phân công/quyền và kiểm2–3chuỗi hồ sơ thực tế khử dữ liệu, ghi owner/evidence/kết luận/gap.

## CHG-20261107-012 — Triển khai tất cả bảng KH-KD: lọc, phân trang và trạng thái

- Ngày07/11/2026, Asia/Saigon; KD-UI-007 theo yêu cầu trực tiếp thực hiện đủ [prompt](prompts/CLAUDE_KD_UI_007_ALL_TABLES_FILTERS_STATUS.md), clone-test rồi áp18069; quyền triển khai riêng cho lượt này. Native `tp_kd_workspace`20.0.1.5.0:36resolvedview/41tablepositions (15list+26relation), đủ11nhóm hồ sơ +Tổng quan/Báo cáo/smart/dialog/history/audit/snapshot. Shared SearchModel/filter/facet thật, server10/20/50/100/default20/prefs riêng/grouped, relation toàncurrentIds và dirty guard; badge semantic/returned không đỏ cả dòng, ngày có năm, mobile search full row. Giữ sidebar/Tổng quan/controller/version/save/beacon/quyền và businessdata; backend chỉ PAGE_MAX50→100 có test, MERGE_MAX500 giữ. Ngoại lệ cấu trúc10nguồn/preview12plan/5credential ghi rõ và có drilldown; [inventory](ui/KD_UI_007_TABLE_INVENTORY.md), [design](ui/KD_UI_007_DESIGN.md), [acceptance](demo/KD_UI_007_ACCEPTANCE.md), [guide](demo/KD_UI_007_USER_GUIDE.md). Thay hướng4màn KD-UI-006; chưa nghiệm thu mockup.
- Kiểm thực source cuối clone18889: Odoo117/117 (44workspace+73contract, log `20261107T103648592721Z`), HOOT11/40assertions, UI353, hồi quy332, zoom thật24, race/error/recovery3;0failure/error trong kết quả cuối; Ruff/nodecheck/XML/assets và157XMLpresentationchanges/0unexpected đạt. Đã mở ảnh từng nhóm và sửa clipping nhãn/mobile search thật; các lượt timeout/lỗi trước được chạy lại, không dùng gate fail để apply. Backup `backup-pre-apply-20261107T104300Z`112file/576table/269blob verified; seal exacthash rồi apply riêng workspace rc0/0error/`changed_tables {}`, SQL installed20.0.1.5.0, dev18069 restart wrapper16896/listener20112. Dev chỉ đọc verify329 +regression325/0error;63table/3.602row gồm history, quyền/accounts/modules257nonassetattachments/269blob/181otheraddonfiles giữ; PG/clone khác PID giữ. Ảnh dev-before/dev-verify cùng actor/dataset/viewport; evidence private `.local/kd-ui007/`, rollback delta giữ. Workflow finish/check và diff cuối lượt.
- Nghiệp vụ/quyền/API/schema không đổi; không sửa core/React, không fixture/cleanup/devbusinesswrite/commit/push. Đã triển khai và tự kiểm kỹ thuật, multi-agent lỗi model nên không gọi audit độc lập; Chromium/emulation chưa Safari/thiết bị thật. Visual acceptance/user, business/Q2/G7/pilot riêng. Next: Ctrl+F5, kiểm5bước theo guide và phản hồi thị giác/audit độc lập.

## CHG-20261107-011 — Prompt bộ lọc, số dòng và màu cho mọi bảng KH-KD

- Ngày07/11/2026, Asia/Saigon; KD-UI-007 theo phản hồi3ảnh và yêu cầu người dùng. Thêm [prompt Claude](prompts/CLAUDE_KD_UI_007_ALL_TABLES_FILTERS_STATUS.md): inventory toàn workspace/list/form/x2many/report, toolbar/filter native dễ thấy,10/20/50/100record/trang, màu trạng thái/action có ngữ nghĩa, ảnh thật từng tab trước–sau; clone/test/backup trước áp18069. Hướng mới thay phạm vi4màn KD-UI-006, giữ mockup và chưa xác nhận visual acceptance.
- Source read xác nhận search views typed có filter, toolbar chỉ density/reset, prefs OWL10/20/50 và backend PAGE_MAX50/MERGE_MAX500; prompt xử lý tích hợp limit100 có test, giữ nhóm/unsaved/context/quyền/công thức. Không đổi app/DB/runtime hoặc làm UI trong lượt điều phối này. Kiểm link/fence/ID/diff/digest và workflow finish/check; không application test vì chỉ tài liệu; multi-agent lỗi model, tự kiểm tài liệu. Không commit/push. Next: Claude thực thi KD-UI-007, bàn giao đủ bảng thay vì chỉ hai list.

## CHG-20261107-010 — Áp dụng bộ công cụ và skill AI vào dự án

- Ngày07/11/2026, Asia/Saigon; AI-TOOLING-001 theo yêu cầu người dùng. Thêm [skill dự án](../.agents/skills/tanphat-odoo-delivery/SKILL.md), metadata, Claude entrypoint/adapter, [playbook](AI_TOOLING_PLAYBOOK.md) có revision/nguồn và lệnh; AGENTS/workflow liên kết cùng quy tắc; gitignore chỉ mở đúng skill đã review. Cài skill Codex Playwright CLI/Ponytail/Ponytail Review/Anthropic webapp-testing bằng helper pin revision, không cài hooks hoặc thay core/business. OmniRoute là hướng adapter/provider đề xuất, chưa tích hợp runtime.
- Kiểm thực tế: PlaywrightCLI0.1.23 login18069 chỉ đọc desktop1440/mobile390/input/submit visible/nooverflow/toggle mật khẩu rỗng đạt,0pageerror/0consolewarning-error, emulation reduced motion hoạt động; không đăng nhập/submit, phiên đã đóng. Graphify0.9.101 local AST150code/1.547node/3.039edge, query seed/treeHTML đạt; không semantic/cloud/DBscan; ghi rõ thiếu XML/SCSS/ORM động. Hai skill dự án validate đạt; kiểm link/ignore/diff, hash246file addon+mockup và digest296file nguyên, PID18069/55432 giữ; workflow finish/check. Không Odoo suite vì không sửa app. Multi-agent review không khả dụng do lỗi model kế thừa; chỉ self-review, không gọi audit độc lập. Bằng chứng `.local/ai-tooling/`, không commit/push. Next sản phẩm vẫn review KD-UI-006, không tự coi mẫu đã được duyệt.

## CHG-20261107-009 — Bản mẫu đề xuất lại giao diện KH-KD (KD-UI-006)

- Ngày07/11/2026, Asia/Saigon; theo yêu cầu đề xuất của người dùng sau khi không ưng KD-UI-005. Dùng frontend-design, lập [hướng thiết kế](ui/KD_UI_006_VISUAL_PROPOSAL.md) trước dựng [HTML4màn và8ảnh](../deliverables/kd-ui006-proposal/index.html): tiêu đề/tìm-lọc tách rõ, tên+khách hàng hai tầng, nhãn tình trạng, form2/3nội dung+1/3metadata; chỉ dữ liệu minh họa, không nghiệp vụ mới.
- Prototype Playwright14kiểm đạt,8layout1440/390không tràn trang, tìm tiếng Việt/lọc/row/tab/7link/Escape; review ảnh desktop/mobile. Chỉ mockup, chưa Odoo tests/visual acceptance/deploy. Source addon bằng sealed CHG007, không query/ghi DB/upgrade/restart hoặc đổi18069; không commit/push. Cập nhật status/roadmap; links/diff/workflow checker cho handoff. Next: review thị giác rồi triển khai native theo scope đã giao; business/pilot riêng.

## CHG-20261107-008 — Đính chính mức hoàn thiện thị giác KD-UI-005

- Ngày07/11/2026, Asia/Saigon; người dùng phản hồi danh sách Cơ hội18069 gần như không khác. Đối chiếu ảnh `shots/dev-before/list-opportunities-1440.png` / `shots/dev-verify/list-opportunities-1440.png` và XML baseline/as-applied: Cơ hội chỉ đổi width2cột/date numeric/search/hover/target; Dự án chỉ thêm scope class. Bố cục bảng/toolbar/sidebar giữ. Hai form chi tiết có thay đổi lớn hơn. Đính chính báo cáo “làm lại cả bốn màn”; trạng thái `TECHNICALLY_VERIFIED_VISUAL_REWORK_REQUIRED`, người dùng chưa chấp nhận phần thiết kế danh sách.
- Giữ nguyên kết quả test chức năng CHG007 nhưng không dùng làm bằng chứng nghiệm thu thị giác. Cập nhật PROJECT_STATUS/ROADMAP/acceptance; next action là redesign2list có ảnh trước–sau cùng viewport/dataset rồi clone-test/backup/apply. Chỉ tài liệu, không applicationcode/DB/runtime/restart/commit/push; kiểm XML diff/ảnh/link/nội dung/diff và workflow finish/check. Không chạy lại bộ test ứng dụng cho đính chính tài liệu.

## CHG-20261107-007 — Bốn màn Kinh doanh và dự án (KD-UI-005)

- Ngày07/11/2026, Asia/Saigon; thực thi [prompt](prompts/CLAUDE_KD_UI_005_BUSINESS_PROJECT.md) tuần tự A–D sau Home003 CHG006/checkerPASS, áp dụng frontend-design. `tp_kd_workspace`20.0.1.4.0: hai list/hai form Cơ hội và hồ sơ thầu/Hồ sơ dự án có scope riêng, search cơ hội, nhãn trên ô/tên wrap, disclosure many2one native/không RPC,3action chính+7action trong Dropdown native. Giữ ProjectListController, FormController/save/discard/dirty/validation, anchor7inherit,10object action/private credential; backend chỉ thêm search_view_id ở helper, không đổi ACL/rule/state/model/API.
- Clone owned18789: Odoo116/116 (workspace43+contract73), HOOT5/5/15assertions, browser161/161+session/unique4/4, scope3/3 rollback, hồi quy270/270; Ruff/XML/JS/signatures đạt. Source hash55file test=áp. `scripts/kd_ui005.py`, `kd_ui005_ui.cjs`, `kd_ui005_checks.cjs`; regression driver `kd_ui003_ui_after.cjs` mở action bằng numeric ID để kiểm điều hướng lặp. [Design/as-built](ui/KD_UI_005_BUSINESS_PROJECT_DESIGN.md), [acceptance/ảnh/log/rollback](demo/KD_UI_005_ACCEPTANCE.md), [guide](demo/KD_UI_005_USER_GUIDE.md); kế hoạch cập nhật link trạng thái thực thi.
- Backup `backup-pre-apply-20261107T075325Z`verified112file/576bảng/269attachment; apply chỉ workspace rc0/0error/changed_tables{}, dev b,c,d,h chỉ đọc130/130;37bảng/3.050dòng,257attachment ngoài asset,93module và nhóm quyền giữ,269blob kiểm checksum/kích thước;181file addon khác bằng snapshot. Hồi quy dev269/269, tổng399/399chỉ đọc; đối chiếu lại37bảng/3.050dòng và attachment/module/groups giữ. PG/clone khác giữ PID, chỉ restart Odoo dev có chủ đích. Không seed/cleanup dữ liệu dev, không commit/push. Tự kiểm; audit độc lập/business/pilot vẫn pending.

## CHG-20261107-006 — Trang chủ KH-KD trước, quản trị có Tất cả ứng dụng (UI-HOME-003)

- Ngày 07/11/2026, Asia/Saigon; thực thi [prompt UI-HOME-003](prompts/CLAUDE_UI_HOME_003_KD_FIRST.md) theo DEC-031. `tp_web_home` 20.0.1.3.0: Home còn Không gian làm việc (KH-KD), Công cụ cá nhân và Quản trị hệ thống chỉ cho `base.group_system` (Tất cả ứng dụng trong trang, Cài đặt, Quản lý ứng dụng); bỏ lưới Ứng dụng nghiệp vụ, app khác qua switcher native. Search chỉ mục hiển thị, khớp đầu từ. Không sửa `tp_kd_workspace`, không đổi menu/action/quyền/dữ liệu, chỉ depends `web`.
- Test: clone 18689 Odoo 12/12, HOOT 24/24 (143 assertion), browser 229/229, Ruff/`node --check` đạt; dev 18069 backup verify `backup-pre-apply-20261107T065916Z`, apply upgrade chỉ `tp_web_home` rc 0/0 error/`changed_tables {}`, verify chỉ đọc 152/152, 39 bảng + 908 ACL + 257 attachment + 93 module = trước. [Acceptance](demo/UI_HOME_003_ACCEPTANCE.md), [hướng dẫn](demo/UI_HOME_003_USER_GUIDE.md), [thiết kế](ui/UI_HOME_003_DESIGN.md). Tooling `scripts/ui_home003.py`, `scripts/ui_home003_ui.cjs`, `scripts/ui_home003_checks.cjs`. Tự kiểm; audit/business/pilot riêng. Không commit/push.

## CHG-20261107-005 — Prompt Trang chủ logic, tập trung KH-KD

- Ngày07/11/2026, Asia/Saigon; vai trò điều phối, tiếp tục frontend-design. Theo yêu cầu đã làm rõ, ghi DEC-031 và [prompt UI-HOME-003](prompts/CLAUDE_UI_HOME_003_KD_FIRST.md): Home workspace KH-KD/cá nhân, quản trị có Tất cả ứng dụng; app ngoài KH-KD vẫn có lối native. Chưa dựng workspace/nghiệp vụ phòng khác; quay lại hoàn thiện KH-KD sau sửa Home.
- Đối chiếu catalog/launcher/button/burger patch/sidebar và baseline004; giữ dữ liệu/quyền/workflow/path/Home Action/reload actor. Inventory/acceptance H01–H10, search/catalog/admin gates, responsive/guard/coverage và clone/backup/apply18069 cho Claude thực thi. [10 nhãn tổ chức nguồn](architecture/TP_ORGANIZATION_SOURCE_BASELINE.md) lưu ô/hash, không có dữ liệu nhân viên; không tự đổi tên hoặc cây tổ chức.
- Chỉ tài liệu; checkpoint tài liệu của lượt này giữ nguyên từ start, source291file/digest bằng checkpoint. Kiểm hash nguồn Excel, nội dung/link/fence/diff, finish/check; không test ứng dụng/ghi DB/restart/upgrade/seed/cleanup/commit/push. Các UI đã triển khai vẫn pending audit độc lập; business/pilot/gate nghiệp vụ giữ. Next: Claude thực thi UI-HOME-003 rồi quay lại audit/hoàn thiện KH-KD.

## CHG-20261107-004 — Trang chủ bốn khu theo workspace (UI-HOME-002)

- Ngày 07/11/2026, Asia/Saigon; thực thi theo [prompt](prompts/CLAUDE_UI_HOME_002_WORKSPACE_ORGANIZATION.md) sau khi KD-UI-004 đóng checkpoint/checker 003 PASS. Áp dụng frontend-design, thiết kế/acceptance trước code. `tp_web_home`20.0.1.1.0→20.0.1.2.0: catalog 4 khu theo menu server, thẻ KH-KD nổi bật, TP Projects/TP Contracts/Công việc dự án rõ mô tả; 4 SVG local, responsive, search/IME, loading/error/retry. Không đổi menu/action/XMLID/path/ACL/rule/grant/Home Action/schema/API/nghiệp vụ, không thêm depends/module hoặc workspace giả.
- Source chỉ `home_catalog.js`, `home_launcher.js/xml/scss`, 4 SVG, manifest, test HOOT và README; giữ home_button/burger_menu/mobile viewport. Tooling `scripts/ui_home002.py`, `scripts/ui_home002_ui.cjs`, `scripts/ui_home002_checks.cjs`; [thiết kế](ui/UI_HOME_002_DESIGN.md), [acceptance/ảnh](demo/UI_HOME_002_ACCEPTANCE.md), [hướng dẫn](demo/UI_HOME_002_USER_GUIDE.md); status/roadmap/runbook cũ cập nhật.
- Test clone 18589: Odoo 11/11, HOOT 19/19(84 assertions), browser 90/90, 0 console error; 7 viewport, zoom thật 125/150, 4 actor, cached menu/error/retry/user/company/Home Action/guard/native menu/unknown icon. Ruff/XML/SVG/JS đạt. Sass incompatibility và test HOOT setup lần đầu đã sửa/chạy xanh. Không React/core changes.
- Dev 18069: backup verified `backup-pre-apply-20261107T050542Z`112 file / 576 table/269 attachment; apply rc 0 `changed_tables {}`; smoke đọc 73/73, 0 error. 34 bảng 1.402 dòng giữ, 908 ACL/domain so backup giữ nội dung và 4 bảng group relation nguyên; 93 module installed trước=sau, menu payload admin/KH-KD trước=sau. Chỉ Odoo dev restart, PG/clone khác giữ PID; không seed/cleanup dev/commit/push. Chromium emulation chưa thiết bị thật; audit/business/pilot riêng. Next: Ctrl+F5 Trang chủ và kiểm 7 bước trong guide.

## CHG-20261107-003 — Làm lại Tổng quan KH-KD (KD-UI-004)

- Ngày 07/11/2026, Asia/Saigon; phiên Claude thực thi [prompt KD-UI-004](prompts/CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md) lô A–D. `tp_kd_workspace` 20.0.1.2.1 → 20.0.1.3.0, chỉ `overview.js/.xml/.scss`, `models/dashboard.py` (3 khóa đọc `kpis.due_window`, credential `bounds`, plan `currency`/`basis_label`), `tests/test_dashboard.py`. Đầu trang gọn + dải quy mô, một hàng lọc, 4 KPI cá nhân, vòng khuyên ↔ thanh 7 nhóm (hover không RPC, chọn giữ mẫu số + khung chọn nhóm, bàn phím/chạm), công việc, cơ hội/hồ sơ thầu, tab kế hoạch/chứng chỉ tải khi mở; motion một lần + giảm chuyển động; gen/seq, stale khi lỗi mạng, xóa số khi lỗi quyền. Không đổi domain/quyền/công thức/state/drilldown, không API/CDN/framework mới.
- Tooling `scripts/kd_ui004.py`, `scripts/kd_ui004_ui.cjs`, `scripts/kd_ui004_ui_overview.cjs`; tài liệu [thiết kế + §11](ui/KD_UI_004_OVERVIEW_DESIGN.md), [acceptance + evidence](demo/KD_UI_004_ACCEPTANCE.md), [hướng dẫn](demo/KD_UI_004_USER_GUIDE.md).
- Test: clone 18489 Odoo 114/114, Ruff sạch, browser 823/823 0 lỗi console (Tổng quan 489 + hồi quy KD-UI-003 334). Dev 18069: backup `backup-pre-apply-20261107T042737Z` verify, apply rc 0 `changed_tables {}`, verify chỉ đọc 806/806 0 lỗi console, rowset 30 bảng/1118 dòng không đổi. Không seed/cleanup dev, không commit/push; audit/business acceptance/pilot vẫn pending.

## CHG-20261107-002 — Kế hoạch và prompt làm lại Tổng quan KH-KD

- Ngày07/11/2026, Asia/Saigon; phiên điều phối áp dụng frontend-design. Tạo [kế hoạch KD-UI-004](ui/KD_UI_004_OVERVIEW_REDESIGN_PLAN.md) và [prompt Claude](prompts/CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md): D01 vòng khuyên + D02 thanh ngang cùng nguồn, bố cục gọn, tách cá nhân/phạm vi, D03–D06 chuyên đề và motion/reduced-mode.
- Đối chiếu dashboard/domain/overview và web.chartjs_lib/chart_hook thực: tránh recreate mỗi patch, stale main/lazy/partial, multi-model drilldown, filter/date/owner khác nhau, tiền/unknown/topN/ngày. Giữ table/form KD-UI-003 và fix scroll CHG001; không sửa nghiệp vụ/quyền/dữ liệu hoặc khép audit/business/pilot.
- Checker001 đạt trước start; TCP chỉ đọc18069/18169/18269/18389/55432 listen. Chỉ kế hoạch/prompt/status/roadmap/changelog, kiểm link/fence/ma trận/hash/diff/checker; không test ứng dụng hoặc restart/upgrade/seed/cleanup/commit/push. Next: Claude A–D, clone-test/visual QA/backup trước áp18069.

## CHG-20261107-001 — Sửa lăn chuột ở Tổng quan KH-KD

- Ngày 07/11/2026, Asia/Saigon; phản hồi người dùng trên dev 18069 "ở phần tổng quan tôi k thể kéo lăn chuột được". Nguyên nhân: gốc `.o_tp_kd_ov` cũng là `.o_action`, rule layout desktop của Odoo (`.o_action { overflow: hidden }`, 0-3-1) đè `overflow: auto` của Tổng quan; lỗi có từ KD-UI-002, <992px không bị. Sửa một selector trong `custom_addons/tp_kd_workspace/static/src/overview/overview.scss` (chỉ phần tử Tổng quan: `overflow: auto`, `overscroll-behavior-y: contain`, scrollbar mảnh), module 20.0.1.2.1; thêm check lăn chuột và bề rộng 1600 vào B19 `scripts/kd_ui003_ui_after.cjs`. Không đổi model/ACL/rule/state/công thức/API.
- Test: clone 18389 Odoo 114/114, archdiff ok, browser 326/326 (bỏ chuỗi ghi hợp đồng/dossier), 0 lỗi console; lăn chuột 1440/1600/390 cuộn 600px. Dev 18069: backup `backup-pre-apply-20261107T021338Z` verify 112 tệp; apply rc 0, `changed_tables {}`; verify chỉ đọc 324/324, 0 lỗi; số bản ghi/registry bằng baseline. Không commit/push.

## CHG-20261106-022 — Bảng có đường kẻ và màn hình chi tiết theo từng tab KH-KD (KD-UI-003)

- Ngày 06–07/11/2026, Asia/Saigon; phiên Claude thực thi prompt KD-UI-003. Chỉ sửa `custom_addons/tp_kd_workspace` (20.0.1.2.0: `static/src/table/*`, view list/form 12 nhóm màn, `views/contracts.xml` inherit chỉ thêm class cho TP Contracts, hint `tp_kd_leaf` cho sidebar, `test_ui_layout`), script `scripts/kd_ui003*.{py,cjs}` và tài liệu; không sửa odoo/addons/React, model dữ liệu, ACL/rule, state/transition hay công thức.
- Bảng native kẻ ô kiểu Ant Design (scope `body.o_tp_kd_shell` + `tp_kd_table`/`tp_kd_form`), header wrap, cột chính/tùy chọn theo nghiệp vụ, Thoáng/Gọn và Khôi phục cột, pager 20 server, sticky header; form có khối tiêu đề/separator/notebook, ô trống chỉ đọc "—", bảng con kẻ như bảng chính; sidebar tô đúng lá. Sửa sau kiểm: "——" ở ô Char trống chỉ đọc; script chờ mọi hộp thoại, SelectMenu, drawer mobile, B18 đo đường kẻ.
- Test clone 18389: Odoo 114/114 (41 + 73), archdiff ok, Ruff sạch, browser 328/328, 0 lỗi console (chuỗi hợp đồng, dossier, quyền, responsive 360–1920/zoom, không rò style, Tổng quan). Dev 18069: backup `backup-pre-apply-20261107T013632Z` 112 tệp đã verify; apply rc 0, 0 lỗi, rowset 30 bảng 1118 dòng không đổi; verify chỉ đọc 320/320, 0 lỗi console; số bản ghi sau verify bằng baseline, không ghi nghiệp vụ. Không commit/push.

## CHG-20261106-021 — Prompt bảng và màn hình chi tiết theo từng tab KH-KD

- Ngày 06/11/2026, Asia/Saigon; vai trò điều phối, áp dụng frontend-design. Gộp phản hồi bảng dày/khó đọc, form chi tiết thiếu phân vùng và yêu cầu phù hợp từng tab vào [KD-UI-003](prompts/CLAUDE_KD_UI_003_TABLES_AND_DETAILS.md); chỉ tài liệu, không sửa application/data/runtime.
- Thiết kế bảng có viền theo cách trình bày Ant Design Table bằng native Odoo; cột chính/tùy chọn, wrap, header/status đọc đủ, density/resize/sticky/pager theo ngữ cảnh. Ma trận 12 nhóm màn, form riêng theo nghiệp vụ, bảng con/wizard/OWL và menu active cần tái hiện; giữ controller/version/quyền/nghiệp vụ và Tổng quan G01–G05.
- Checker020 đạt trước start; đọc source/style/controller và runtime TCP, không restart/upgrade/seed. Cập nhật status/roadmap, kiểm link/fence/ma trận/source hash/diff và finish/check; không test ứng dụng cho batch prompt, không commit/push. Next: Claude inventory/acceptance, triển khai A–D, snapshot/clone-test rồi áp dev18069; audit nghiệp vụ và audit KD-UI-002 còn pending.

## CHG-20261106-020 — Triển khai sidebar và Tổng quan KH-KD (KD-UI-002)

- Ngày06/11/2026, Asia/Saigon; phiên Claude thực thi prompt KD-UI-002 (CHG018 + mục5A CHG019), skill frontend-design. Start checkpoint trước sửa; chỉ sửa `custom_addons/tp_kd_workspace`, script `scripts/kd_ui002*.{py,cjs}` và tài liệu; không sửa odoo/addons/React/core.
- Sidebar5nhóm + Tổng quan, tìm/thu gọn/active/deep link/mobile drawer, prefs cá nhân, hover/animation reduced-motion. Tổng quan: toolbar, KPI, G01–G05, bảng dự án có Thao tác ▾, Việc của tôi, bảng nguồn cũ; helper report read-only theo quyền, chưa đủ căn cứ khác0, không vẽ tiền thực thu/lợi nhuận/công nợ. Sửa sau test clone: `props.className`, `withViews` cho action từ `orm.call`, layout1760px, wait patch async.
- Test clone: Odoo33/33 + tp_contract73/73, browser231/231, chart193/193; dev18069 sau snapshot112/112: apply rc0, rowset31bảng không đổi, verify230/230, chart193/193. 254seed+14UI/quyền/state giữ. Ảnh trước–sau, hướng dẫn, acceptance; cập nhật status/roadmap/presentation. Không commit/push.

## CHG-20261106-019 — Bổ sung biểu đồ và bảng điều hành Tổng quan KH-KD

- Ngày06/11/2026, Asia/Saigon; vai trò điều phối, tiếp tục frontend-design. User yêu cầu Tổng quan đẹp nhất trong phạm vi KH-KD, biểu đồ tổng thể/chi tiết dễ hiểu, cột bảng rõ, nhiều thao tác với nút gọn. Checker018PASS, start trước sửa; chỉ tài liệu.
- Bổ sung5A vào [prompt KD-UI-002](prompts/CLAUDE_KD_UI_002_SIDEBAR_POLISH.md): G01typed-state/G02WBS-project/G03CRM/G04plan-production/G05credential-expiry;3chart chính và tabchi tiết, bảng dự án/việc cá nhân, toolbar/create dropdown/row action, search/sort/pagination/column picker và drilldown. Không thêm chức năng ký/duyệt/tiền thật để đủ nút.
- Report helper read-only được phép khi có guard/test; metric catalog xác định grain/domain/ngày/đơn vị/source/action. Không sudo aggregate, leak tiền/cache, đếm trùng, cộng tháng-quý-năm, biến unknown thành0hoặc gọi tỷ lệtask là tiến độ dự án. Không đổi254seed/14UI, policy hoặc đóng audit nghiệp vụ. Yêu cầu testreport/phân quyền/biênngày/async/UI cùng ảnh Tổng quan thực tế.
- Cập nhật status/roadmap, kiểm link/fence/5chartID/hash/diff/checker; không chạy applicationtest hoặc DBwrites cho batchprompt. Next: Claude tiếp tục chính prompt đã cập nhật, testclone rồi tích hợp18069. Không codeapp/upgrade/restart/seed/commit/push ở lượt019.

## CHG-20261106-018 — Prompt sidebar và hoàn thiện giao diện KH-KD

- Ngày06/11/2026, Asia/Saigon; vai trò điều phối DEC-022, skill frontend-design. Người dùng yêu cầu sidebar trái có tab con xổ ra, giao diện KH-KD đẹp hơn cùng hover/animation. Baseline checker017 đạt, start trước sửa; không application code/runtime/data.
- Tạo [prompt KD-UI-002](prompts/CLAUDE_KD_UI_002_SIDEBAR_POLISH.md): sidebar mọi màn KH-KD,5nhóm+Tổng quan từ cây menu native theo quyền, thu gọn/tìm/active/deep link/unsaved guard; Tổng quan/list/form nhất quán, prefs cá nhân, hover/animation có reduced-motion và mobile drawer. Đối chiếu source WebClient/NavBar/menu service thực tế, lưu ý2menu dùng chung action; chỉ custom assets/view có scope, không core/theme ngoài/React mới.
- Giữ254seed+14UI, mọi policy/workflow/quyền/công thức và6phụ lục còn thiếu; không đổi audit nghiệp vụ pending. Prompt yêu cầu backup/clone-test trước áp18069, kiểm menu/form/quyền/mobile/baseline và rollback delta; chưa tạo sidebar hoặc hai tài liệu thiết kế/acceptance của phiên thực thi.
- Kiểm link/fence/nội dung/diff và hash maintained source không đổi, finish/check. TCP chỉ đọc18069/18269/55432 hoạt động,18109 không listen. Không test ứng dụng cho batch tài liệu, không restart/upgrade/seed/commit/push. Next: Claude thực thi prompt mới, tránh sửa chồng cùng checkout.

## CHG-20261106-017 — KD-NATIVE-001 tích hợp dev18069 và bàn giao

- Ngày06/11/2026. A–D/DATA254đã lên dev sau backup/restore538rowsets/249blob; tái sử dụng UI001a. Sửa import test runtime và context view/default khi action đổi model, thêm test tái hiện.254seed +14UI riêng, thiếu6phụ lục theo user; registry/manifest/dry-run và hướng dẫn đăng nhập/3tình huống.
- Kiểm: clone133/133, fresh install98/98, dev159/159browser + restart/fresh login; seedlặp0, preservation22bảng/249blob, Ruff/XML/assets/diff. Đối chiếu source clone/main không lệch, liên kết/ảnh bàn giao tồn tại, HTTP dev200.3assetcache tái tạo là delta dự kiến; không dữ liệu nghiệp vụ cũ mất/đổi.
- Sự cố đã xử lý: CLI dev stop vô tình dừngPG khi kiểm restart; khởi động lại và đối chiếu config/secrets/DB/blob, ghi đầy đủ acceptance. Không tuyên bố không restartPG. Session-expired chập chờn là giới hạn còn mở; không sửa core/session.
- Dev giữ chạy; không cleanup, commit/push, business/pilot hoặc mở gate pháp lý/tiền thật/grant thật/TASK-001. Next review trình diễn/audit độc lập; không tự tạo6phụ lục ngoài gate.

## CHG-20261106-016 — KD-NATIVE-001 DATA254 trên clone

- Ngày06/11/2026. Registry operator-only, ORM seed254, manifest/dependency/drift, cleanup dry-run/apply clone guards; user chọn thiếu6phụ lục, không vượt gate workflow.
- Test: Odoo132/132; browser26/26 + relogin/restart; rehearsal13check,15unlink/0archive/1117retained/3referenced đã rollback; seed2lần không trùng/reset password/overwrite. Ruff/XML/diff đạt.
- Copy addon đã kiểm về main; dev18069 chưa tích hợp. Next backup/restore mới, migration/seed/UI dev. Không cleanup dev/commit/push/business/pilot.

## CHG-20261106-015 — KD-NATIVE-001 D3

- Ngày: 06/11/2026, Asia/Saigon. Nghĩa vụ có lịch sử checklist; hộp việc/report count và drilldown cùng quyền; form WBS manager tạo/sửa/giao/cha-con, staff deny; regression131 và browserWBS5.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend131/131, browser18/18 `d3-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: Dataset260 registry/seed/inventory/verify/cleanup rehearsal; rồi tích hợp dev sau backup.

## CHG-20261106-014 — KD-NATIVE-001 D2

- Ngày: 06/11/2026, Asia/Saigon. Hồ sơ năng lực tổ chức/cá nhân với private restriction, ngày/hạn minh họa, liên kết cơ hội đã kiểm quyền và drilldown native.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend21/21, browser15/15 `d2-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: D3 nghĩa vụ/báo cáo và hoàn thiện tổng quan; dataset260/dev.

## CHG-20261106-013 — KD-NATIVE-001 D1

- Ngày: 06/11/2026, Asia/Saigon. Kế hoạch tháng/quý/năm với hai chỉ tiêu riêng, đối chiếu sản lượng cùng kỳ/state/currency/basis và drilldown; doanh thu chưa có chứng từ.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend19/19, browser12/12 `d1-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: D2 năng lực/chứng chỉ; D3 nghĩa vụ/báo cáo; dataset260/dev.

## CHG-20261106-012 — KD-NATIVE-001 C4

- Ngày: 06/11/2026, Asia/Saigon. Đề nghị thu/chi theo đợt hoặc tạm ứng, căn cứ/checklist/đối chiếu và tiền riêng; không paid/posting.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend17/17, browser12/12 `c4-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: D1 kế hoạch định kỳ; D2 chứng chỉ; D3 nghĩa vụ/báo cáo; dataset260/dev.

## CHG-20261106-011 — KD-NATIVE-001 C3

- Ngày: 06/11/2026, Asia/Saigon. Hồ sơ nghiệm thu nội bộ theo đợt, phạm vi/khối lượng/kỳ thuộc sản lượng nguồn và guard hai chiều.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend15/15, browser12/12 `c3-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: C4 đề nghị thanh toán/đối chiếu; D/dataset260/dev còn tiếp tục.

## CHG-20261106-010 — KD-NATIVE-001 C2

- Ngày: 06/11/2026, Asia/Saigon. Sản lượng theo kỳ, nguồn khoán/hợp đồng có guard hai chiều, metadata/tiền riêng và workflow hai actor.
- Model/action/security/native; không API/React/core. Spec/test trước implementation.
- Test: backend13/13, browser12/12 `c2-browser.json`, Ruff/XML/diff; clone18269. Không dev/business/pilot hoặc commit/push.
- Next: C3 nghiệm thu theo nguồn; C4/D/dataset260/dev còn tiếp tục.

## CHG-20261106-009 — KD-NATIVE-001 C1 giao khoán trên clone

- Ngày: 06/11/2026, Asia/Saigon. Scope model/action/security/native trong `tp_kd_workspace`, không API/React/core.
- Typed allocation/amount/event; workflow gửi/trả/mở sửa/gửi lại, scope/cycle/version/replay và snapshot bất biến. Adapter form gửi phiên bản đã đọc, không bỏ concurrency guard.
- Test: Odoo10/10 log061214047444Z; browser12/12 `c1-browser.json`, gồm stale hai tab và responsive390/768/1440; Ruff/XML/diff. Chỉ clone18269, không dev/business/pilot. Không commit/push.
- Next: C2 theo spec/test trước implementation, rồi C3/C4/D/dataset260 và tích hợp dev có backup.

## CHG-20261106-008 — KD-NATIVE-001 lô B, dùng lại hợp đồng native đã audit

- Ngày06/11/2026 Asia/Saigon; start riêng sau handoff007. Không thay source001a hoặc mở lại correction D1/D2. Clone18269 chạy regression111 ở007 (contracts73/project12/planning22/workspace4) và browser42/42 bằng script001a đổi đúng target/path trong bản private.
- Browser đầy đủ nháp→sửa→gửi→reviewer trả→mở sửa→gửi lại; metadata/stale/retry/files/scope/responsive5viewport/zoom125/150 thật,0 console/network error. Task manager fixture thao tác theo quyền hiện hành; staff deny TASK-001. Evidence `.local/kd-native001/ctr-native001/` riêng, không ghi đè audit003.
- Chỉ bàn giao test, chưa upgrade/seed dev hoặc tạo dataset260. C1–C4/D và tích hợp dev còn mở. Không BASE/ký/hiệu lực/tiền thật/grant người thật/pilot/commit/push. Next C1 theo workflow đã viết.

## CHG-20261106-007 — KD-NATIVE-001 lô A, workspace trên clone riêng

- Ngày06/11/2026 Asia/Saigon; yêu cầu trực tiếp chuyển phiên chính sang thực thi KD-NATIVE-001 gồm7A–7C/CHG006. Start trước sửa, giữ toàn bộ dirty baseline; không commit/push. Thêm addon workspace native/CRM/checklist/target guards/task source và tooling owned clone; thiết kế, acceptance, workflow fixture. Source được phát triển trong bản custom riêng trước copy delta addon mới vào checkout; chưa cài dev.
- Snapshot DB/filestore/private config/source dirty/upstream/frontend có checksum; restore538 bảng/249blob exact, clone18269/source riêng, cron0/SMTPloopback. Backend111/111, browserA10/10, Ruff/XML/compile đạt. Lượt77 không được runner chấp nhận vì tag project0; probe lỗi chờ save/tab đã giữ evidence và chạy lại đạt. Snapshot có password private nhưng không in/Git; tài liệu chỉ nêu đường dẫn.
- Dev18069 PID23452 và audit18169 giữ nguyên, chưa upgrade/seed dev. C1–C4/D/dataset260 chưa triển khai, chưa nghiệm thu toàn task. TASK-001/Q2/pháp lý/BASE/ký/hiệu lực/tiền thật/pilot giữ gate riêng. Next B regression 001a rồi C1.

## CHG-20261106-006 — Sửa cơ cấu và kiểm lại mục tiêu260record

- Ngày06/11/2026, Asia/Saigon; chỉ tài liệu. Assertion tổng của005 fail vì cơ cấu thực là240; shell tiếp tục finish/check nên checker005 chỉ xác nhận hash/handoff, không chứng minh kiểm cơ cấu đạt. Ghi nhận sai lệch thay vì giữ lời báo cáo kiểm đã đạt.
- Tăng mục tiêu WBS/công việc trong prompt từ80 lên100, tổng12nhóm là260. Cập nhật status/roadmap; không sửa code hoặc DB. Chạy lại validation links/fences/tổng12nhóm260 và maintained-code equality, diff trước finish riêng006; không chạy test ứng dụng.
- Next: Claude thực thi cùng prompt7A–7C với cơ cấu đã sửa, bàn giao số record thực tế. Số260 vẫn là mục tiêu, không phải dữ liệu đã được tạo.

## CHG-20261106-005 — Bổ sung bộ dữ liệu KH-KD sát thực tế lưu database

- Ngày06/11/2026, Asia/Saigon; DEC-022 điều phối; checker004 đạt, start trước sửa. Người dùng yêu cầu nhiều bản ghi tự tạo giống thật, lưu DB để thao tác và có thể dọn sau. Chỉ cập nhật tài liệu giao việc, không tuyên bố đã seed.
- [Prompt KH-KD](../deliverables/PROMPT_KHKD_NATIVE_18069.md) thêm7A–7C: cơ cấu mục tiêu260 record gồm12đối tác/12cơ hội/8dự án/16hợp đồng-phụ lục/80task/16khoán/24sản lượng/16nghiệm thu/20đề nghị/16kế hoạch/12năng lực-chứng chỉ/8checklist. Tên tiếng Việt tự nhiên, dữ liệu tổng hợp và ngày tương đối, ít nhất3 chuỗi liên thông; trạng thái hợp lệ, không giả chứng từ pháp lý/tiền thật.
- Bổ sung persistence qua phiên/restart, provenance/external key trong DB và manifest private, seed lặp không trùng/không ghi đè sửa đổi/không đổi password, không gửi ra ngoài. Dọn riêng có dry-run/ownership/reference guards; hồ sơ đã trình/audit theo policy archive/retained, không hứa xóa vật lý tất cả. Không cho phép cleanup apply dev trong task tạo dữ liệu.
- Cập nhật status/roadmap; kiểm liên kết/fence/cơ cấu số lượng/diff/checker và maintained code không đổi. Không chạy application test cho batch tài liệu; không ghi/xóa DB, không sửa application/security/core/React, không restart/upgrade/commit/push. Next: đưa yêu cầu bổ sung vào chính phiên Claude đang triển khai; báo số thực và runbook dataset sau khi hoàn thành.

## CHG-20261106-004 — Cụ thể hóa prompt giao diện và thao tác KH-KD trên18069

- Ngày06/11/2026, Asia/Saigon; vai trò điều phối DEC-022, baseline checker003 PASS và start trước sửa. Người dùng yêu cầu dựng nghiệp vụ KH-KD trực quan, thao tác như thực trên dữ liệu giả, trình bày trực tiếp dev18069.
- Bổ sung [prompt KD-NATIVE-001](../deliverables/PROMPT_KHKD_NATIVE_18069.md): baseline hợp đồng đã audit003, thiết kế Tổng quan/hồ sơ dự án/list/form/mobile, ma trận12 nhóm nghiệp vụ và acceptance theo actor/action/môi trường. Chia C1–C4 và D theo phụ thuộc; phải làm action persist và hồ sơ tự tạo ngoài seed, không chỉ menu/ảnh hoặc đường bấm hardcode. Yêu cầu hai đầu ra thiết kế/acceptance và kịch bản12–15phút; chưa tạo các đầu ra của phiên thực thi.
- Cập nhật PROJECT_STATUS/ROADMAP và đồng bộ tài liệu hướng native với audit003. Không đặt policy/thẩm quyền mới, không đóng Q2/G7 hoặc business/pilot. Áp dev chỉ sau snapshot khớp dirty/untracked source và restore/clone-test; quyền trình diễn18069 đã có, không mở BASE/ký/hiệu lực/tiền thật/upload ngoài gate/grant thật hoặc TASK-001.
- Kiểm nội dung/ma trận/liên kết, diff và workflow checker; không chạy Odoo/browser test cho batch tài liệu. TCP chỉ đọc:18069/18169/55432 đang listen,18109 không listen. Không sửa application/test/security/API/core/React, không thao tác database/process, không commit/push. Next: Claude thực thi từng lô theo prompt; verdict hiện tại chỉ `PROMPT_READY_FOR_EXECUTION`.

## CHG-20261106-003 — Audit độc lập UI-CTR-NATIVE-001a trên DB test

- Ngày06/11/2026, Asia/Saigon; vai trò điều phối DEC-022, start checkpoint riêng sau checker002 PASS. Verdict `TECHNICAL_ACCEPTED_TEST_ONLY` cho001a; [báo cáo](reviews/UI_CTR_NATIVE_001A_INDEPENDENT_AUDIT.md). Không có finding cần correction trong scope đã kiểm; business/pilot/G7 không đóng.
- Chạy lại owned clone18169: Odoo107/107 (`run-20261106T045827388402Z`), runner18/18, native browser42/42 cùng full flow/stale/retry/metadata/file/quyền/responsive/zoom; ảnh đã xem. Ruff/XML/manifest/Node/OpenAPI/diff đạt. D1/D2/owner/group/đối chứng và AT-17 đạt; AT-17 mô phỏng request bằng env.clear, không write grant lúc chuyển ngày. React9+6 giữ evidence CHG002, không chạy lại.
- Source238 file/digest `ac21fef5…bbe25af` và hash riêng browser/vi.po giữ nguyên. Không sửa application/tooling test/core/API/React/ACL; chỉ audit/status/roadmap/spec và evidence/helper local, không ghi đè evidence thực thi.
- Dev chỉ probe SQL read-only:1.1.0,0 model native/0 actor test,3contract/0submission trước-sau; không claim fingerprint mọi bảng. Clone1.2.0 giữ10 model/5 actor, browser thêm1 contract/2 submission giả; clone cuối chạy phục vụ review. Không upgrade/restart/seed/apply dev18069, không mở demo18109, không commit/push. Next tích hợp KH-KD tái sử dụng001a, apply dev là batch riêng có backup/test; BASE/ký/hiệu lực/thanh toán/upload/grant thật/TASK-001 vẫn ngoài audit.

## CHG-20261106-002 — Tiếp tục Claude: UI native TP Contracts trên DB test

- Ngày06/11/2026, Asia/Saigon; người dùng giao trực tiếp ngoại lệ thực thi UI001a. Resume checkpoint Claude, giữ mọi thay đổi sẵn có; baseline code234/digest audit001, delta có sẵn là test native/import. Không commit/push.
- Thêm 5 header transient, draft.line/return.issue/amount.input, global owner/company/project restrictions (D1), guard tiền bằng capability hiện tại (D2), target/key/result do server quản lý, Decimal validation, cleanup/retry, error tiếng Việt. Gọi lại sáu action CTR-002a bằng user; không mở ACL hợp đồng gốc hoặc sửa API/OpenAPI/React/core.
- Menu TP Contracts/Home, list/search/form chỉ đọc, wizard create/edit/amendment/submit/return/rework; số tiền/tệp theo grant, lần trình/BASE read-only/audit. Phiên bản addon20.0.1.2.0, chỉ upgrade owned test clone18169. Dữ liệu và 5 credential actor giả ở `.local/native-stabilize001/ctr-native001`, ngoài Git.
- Test trước implementation: RED mới22 failed/0 errors do thiếu chức năng; hai GREEN cuối107/107 (`run-20261106T035229356222Z`, `run-20261106T035740655789Z`), native22/runner18/React contracts9 unit+6 mock E2E, Ruff/XML/manifest/OpenAPI/diff đạt. Ma trận24 AT/evidence trong [báo cáo](reviews/UI_CTR_NATIVE_001A_IMPLEMENTATION.md). Fixture admin chỉ xét project giả mới; cấp export group test để thật sự kiểm restriction. Các lượt N07 WinError10054 được giữ; test guard kiểm trước body dùng zero-byte body để tránh socket reset, giữ status/code/no-store và ca malformed JSON, không retry write/nới security/đổi API.
- Browser42/42: đầy đủ luồng, metadata-only/stale/retry/binary,5 viewport và zoom Chromium thật125/150; ảnh đã xem,0 console/network lỗi. Sửa reviewer virtual form, recompute theo project, readonly version web_save (force_save), version context khi mở wizard và action kết quả để tránh đọc cache cũ. G8/AT-17 đạt kỹ thuật không write grant khi đổi ngày; G7/Q2/business/pilot giữ mở. Clone18169 để review; dev18069/PG55432 có sẵn không khởi động/chỉnh, không snapshot dev mới. Next: audit implementation bởi phiên khác; không stage/commit/push.

## CHG-20261106-001 — Audit đạt đặc tả D1/D2 và phát prompt code UI-CTR-NATIVE-001a

- Ngày06/11/2026, Asia/Saigon. Vai trò điều phối DEC-022; baseline checker CHG006 đạt, start trước sửa bàn giao. Chỉ audit đúng D1/D2, không mở lại toàn batch nền.
- **Kết luận:** D1/D2 `PASS_SPEC`, UI-CTR-NATIVE-001a `READY_FOR_TEST_CODE`; 24 AT chưa chạy trên wizard thật vì chưa implementation. [Audit](reviews/NATIVE_STABILIZE_001_D1_D2_ACCEPTANCE_AUDIT.md), [prompt code test/AT trước](prompts/CLAUDE_UI_CTR_NATIVE_001A.md). Cập nhật status/roadmap/spec và ghi kết luận vào correction report; giữ các báo cáo audit lịch sử.
- **Kiểm thực:** source helper/rule khớp restriction scope child và guard assignment/grant; evidence rollback005 được đối chiếu, không chạy lại. Code digest `6abcc74a…d957d`234 file giữ nguyên; 24 ID không trùng; link/format/diff và workflow checker được kiểm trước bàn giao. Không chạy test ứng dụng cho batch tài liệu.
- **Runtime:** TCP18069/18169/18109/55432 không mở tại lần kiểm, ghi sai lệch so handoff ngày05/11; không khởi động dịch vụ. Không sửa application/tooling/ACL/core/React, cấu hình/tài khoản/DB; không upgrade/seed/apply dev, commit/push.
- **Next:** Claude code UI001a trên DB test với fixture; AT-17/G8 phải kiểm trước nghiệm thu chức năng tiền. G7 policy gốc và Q2 người thật/pilot còn mở; BASE/ký/hiệu lực/thanh toán/upload/grant thật/TASK-001 và apply F-DASH dev ngoài scope.

## CHG-20261105-006 — Correction delta D1/D2 đặc tả UI-CTR-NATIVE-001a

- Ngày 05/11/2026, Asia/Saigon. Baseline checker CHG-20261105-005 đạt; `start` trước khi sửa. Chỉ sửa tài liệu.
- **D1** ([spec](architecture/TP_UI_CTR_NATIVE_001_SPEC.md) mục 9.2, AT-18):
  - thêm restriction `crud` `[('wizard_id', 'access', 'read')]` cho `draft.line`/`return.issue`, giữ owner/company;
  - AT-18 kiểm owner mất project access, có đối chứng gỡ riêng restriction.
- **D2** (mục 9.3 bước 2–3, mục 12, AT-10a..AT-10d, AT-10g, AT-17, G7, mục 16):
  - guard `_tp_amount_display_allowed()` (project readable + `financial_read` trong `_tp_capabilities`) trước khi tính `current_amount_text`;
  - tách AT-10 thành revoke, expiry, staff mất assignment, manager mất assignment (tiền gốc theo baseline G7);
  - ca metadata đổi ID thành AT-10g.
- **Kiểm:**
  - code digest `6abcc74a…57d` (234 file) khớp CHG-005;
  - ID acceptance không trùng, link không hỏng, `git diff --check` đạt.
  - Không chạy test ứng dụng/Odoo vì batch chỉ sửa tài liệu.
- **Giữ nguyên:** không sửa `custom_addons`/runner/API/ACL; không apply dev; không commit/push.
- **Trạng thái:** `CORRECTED_PENDING_AUDIT_DELTA_D1_D2`; chờ audit hai delta. [Báo cáo](reviews/NATIVE_STABILIZE_001_CORRECTION.md) mục 7.

## CHG-20261105-005 — Audit delta correction NATIVE-STABILIZE-001

- Ngày05/11/2026, Asia/Saigon. Baseline CHG004 checker đạt; `start` trước sửa bàn giao. Không sửa application/tooling/ACL/core/React, không apply dev hoặc commit/push.
- **Kết luận:** A3 đạt; A1/A2 còn D1/P2 (dòng con thiếu restriction scope) và D2/P2 (compute tiền/AT-10 mâu thuẫn quyền tiền gốc của manager sau mất assignment). Spec001a `NEEDS_FIX`; không phát prompt code trước khi hai delta đạt. [Audit](reviews/NATIVE_STABILIZE_001_DELTA_AUDIT.md), [prompt correction hẹp](prompts/CLAUDE_NATIVE_STABILIZE_001_DELTA_CORRECTION.md).
- **Kiểm thực chạy:** unit18/18, Ruff; runner clone Odoo29/29 exit0; tag không có test → exit1 dù Odoo process exit0. Probe dữ liệu giả/rollback: parent deny nhưng child read/search vẫn được, thêm access restriction thì deny; manager mất assignment vẫn đọc tiền gốc nhưng không còn workflow capability. Evidence `.local/native-stabilize001-delta-audit/`, log runner mới riêng từng lượt.
- **Bàn giao:** cập nhật status/roadmap/spec/correction report, giữ lịch sử. Code234 file/digest nguyên so CHG004; dev18069 vẫn chạy, clone18169/demo18109 không listen. G7/G8, business/pilot và toàn DASH/MOBILE/DATA003 chưa được nghiệm thu. Next correction D1/D2 chỉ tài liệu, audit delta rồi mới giao code test/AT trước; F-DASH áp dev cần yêu cầu riêng.

## CHG-20261105-004 — Correction NATIVE-STABILIZE-001 A1/A2/A3

- Ngày 05/11/2026, Asia/Saigon. Baseline checker CHG-20261105-003 đạt; `start` trước khi sửa. Không đổi F-DASH-01/02, application/ACL/core/React hay user/grant.
- **A1** ([spec](architecture/TP_UI_CTR_NATIVE_001_SPEC.md) mục 9.1/9.2/9.4/9.5, AT-09/14/15/16):
  - restriction owner, company và project tường minh cho wizard/wizard-line;
  - target do server xác định; `action_confirm()` không tham số, kiểm owner/target/payload.
- **A2** (mục 8/9.3/10/12, AT-03/10..10f/17, G7/G8):
  - không lưu baseline; tiền hiện tại qua compute không lưu bằng quyền user;
  - tiền mới chỉ ở `amount.input` với restriction grant + assignment, xóa khi thành công;
  - target bất biến; luồng metadata giữ nguyên.
- **A3:** `scripts/native_stabilize001.py` thêm `evaluate_test_run`, kiểm identity clone, log/verdict riêng cho mỗi lần chạy, exit nonzero, `--expect-tests`. Test mới `scripts/tests/test_native_stabilize001.py`.
- **Test:**
  - unit 18/18, tooling 63/63, mutation 14/14, Ruff và `git diff --check` đạt;
  - clone 18169: pass EXIT 0 với 29/29 (`run-20261105T125703971580Z.log`); tag không có test → EXIT 1;
  - log thật cũ run1/run2 → `tests_errored`.
- **Trạng thái:** dev 18069 không apply, demo 18109 không dựng, clone đã dừng. Chờ audit delta; không ghi acceptance, không mở pilot, không commit/push. [Báo cáo](reviews/NATIVE_STABILIZE_001_CORRECTION.md).

## CHG-20261105-003 — Audit độc lập NATIVE-STABILIZE-001

- Ngày05/11/2026, Asia/Saigon. Baseline checker CHG-20261105-002 đạt; không sửa application/tooling code. Snapshot107 checksum khớp, diff bốn file khớp hai sửa dashboard và một regression test.
- Chạy độc lập clone18169: Odoo29/29 bằng lệnh trực tiếp/log riêng; browser78/78 (chỉ đổi output trong bộ nhớ); ORM9 actor×2 dashboard và assertion số liệu/denial; Ruff/XML5/Node syntax/diff đạt. Evidence `.local/native-stabilize001-independent-audit/`; giữ evidence Claude.
- Verdict: F-DASH-01/02 đạt kiểm chứng hẹp; toàn batch/đặc tả `NEEDS_FIX`. A1/P1 sai giả định owner rule transient (rollback probe xác nhận); A2/P2 thiếu bảo vệ bản sao tiền wizard sau revoke; A3/P2 runner không fail khi process/summary lỗi,0 test hoặc thiếu summary (fault injection4 ca). Không kết luận có lỗ hổng wizard hợp đồng hiện hữu vì chưa triển khai.
- Thêm audit report/prompt correction, override READY ở spec/báo cáo tự kiểm, cập nhật status/roadmap. Clone đã dừng, revocations `{}`, ACL/wizard thử rollback. Dev18069 vẫn chạy, read-only538 bảng so snapshot chỉ3 bảng phiên khác; không apply/upgrade dev, commit/push hoặc mở pilot. Giới hạn Chromium emulation, không test timeout thật/full login form hoặc audit toàn bộ batch cũ. Next correction A1/A2/A3 rồi audit delta.

## CHG-20261105-002 — NATIVE-STABILIZE-001: audit/ổn định nền Odoo native, đặc tả UI native TP Contracts

- Ngày 05/11/2026, Asia/Saigon; theo yêu cầu trực tiếp của người dùng. Start checkpoint trước sửa; không nhận thay đổi chưa commit của các batch trước là của lượt này.
- Môi trường: snapshot dev có sha256 (`snapshot-20261105T095544Z`), clone sở hữu `tp_tanphat_stab001_20261105`/18169, data_dir riêng, cron/SMTP/list_db tắt; restore evidence 538 bảng/249 blob. Dev 18069 chỉ đọc, không upgrade/seed/apply.
- `tp_dashboard_privacy` (chỉ clone): F-DASH-01 thêm `detail` phạm vi trạng thái cho hai thẻ chi phí (không đổi tên/công thức/giá trị); F-DASH-02 trạng thái lỗi khi đang lọc dự án hiện “Dự án đã chọn” thay vì “Tất cả dự án được phép”; thêm test hồi quy expense draft/approved/refused.
- Tooling `scripts/native_stabilize001.py` + `native_stabilize001_ui.cjs`; RFC TASK-001 thêm đề xuất action hẹp + 7 câu hỏi (deny giữ nguyên); đặc tả `TP_UI_CTR_NATIVE_001_SPEC.md` READY_FOR_TEST_CODE cho 001a; báo cáo `docs/reviews/NATIVE_STABILIZE_001_REPORT.md`; runbook dashboard ghi nhãn mới.
- Kiểm: Ruff đạt; XML 5 file; `node --check` probe + dashboard.js ESM; Odoo clone 29/29 (2 lần fail trước do fixture test mới, đã sửa); UI probe 78/78 (Chromium emulation); ORM audit 9 actor; TASK-001 deny; dev drift chỉ `bus_bus`/`mail_presence`/`res_device_log`; `git diff --check` đạt. Không React build (không đổi legacy). Không commit/push/deploy dev.

## CHG-20261105-001 — Chốt giao diện chính native Odoo, làm rõ hiện trạng

- Ngày05/11/2026, Asia/Saigon: người dùng xác nhận không phát triển FE tách riêng; DEC-030 thay hướng frontend của DEC-001/012, giữ backend/data/session/quyền/BASE và workspace theo vai trò.
- Cập nhật AGENTS, status/roadmap, hướng source, quy trình AI, tên phân hệ, database và README legacy React; thêm bản hiện trạng/kế hoạch chuyển native. Không xóa React/API/test, đổi route/login, cài/gỡ module, sửa application code hoặc thao tác dữ liệu.
- Baseline checker đạt CHG-20261104-005 dù working tree có thay đổi application của các batch trước; không nhận các thay đổi đó là của lượt này. Start checkpoint mới trước sửa tài liệu. SQL read-only kiểm module installed và4 invoice draft801 triệu; dev18069/PG55432 đang chạy. Không chạy lại application tests vì không đổi code/runtime; kiểm tài liệu/diff và handoff riêng, không nghiệm thu DASH/MOBILE hoặc mở pilot.
- Next: đặc tả UI-CTR-NATIVE-001 cho backend hợp đồng đã có; giữ TASK-001 và các gate nghiệp vụ, audit riêng. Không commit/push.
- Kiểm tài liệu: 184 đích liên kết file local tồn tại (không kiểm nội dung anchor); DEC-030 có đúng một heading; `git diff --check` đạt. Snapshot 232 file application/tooling khớp checkpoint đầu lượt: không đổi code từ baseline đã bàn giao; kết quả này không audit lại nội dung DASH/MOBILE. Handoff bằng `finish/check` riêng CHG-20261105-001.

## CHG-20261104-005 — MOBILE-001: Giao diện mobile/tablet/desktop cho TANPHAT ONE native

- Ngày 04/11/2026, Asia/Saigon; theo yêu cầu trực tiếp của người dùng.
- `tp_web_home` 20.0.1.1.0:
  - view viewport cho phép phóng to;
  - Home 2 cột thẻ trên điện thoại;
  - nút ≥44 px; drawer Escape/focus.
- `tp_dashboard_privacy` (chỉ static):
  - bộ lọc gập có đếm/Xóa lọc; input 16/44 px; chỉ số 2/1 cột;
  - bảng cuộn trong vùng riêng, cột dự án dính trái;
  - chống chạm kép; bộ chọn bảng toàn màn hình; `fa` → `oi`; giảm chuyển động.
- Thêm `scripts/mobile001*.{py,cjs}`.
- Không đổi backend, quyền, công thức, workflow, API, React, prototype hoặc core; không PWA/offline.
- Kiểm:
  - Odoo tests clone 28/28;
  - luồng clone 20/20 (dữ liệu giả) và dev 20/20 chỉ đọc;
  - khảo sát 252 ô mỗi môi trường, 0 tràn trang;
  - zoom thật 125/150% 12/12 mỗi môi trường;
  - ruff, `node --check`, XML parse, SCSS compile.
- Dev chỉ `-u tp_web_home`, PostgreSQL vẫn chạy; bảo toàn 522/538 bảng nguyên, delta upgrade/asset/telemetry đã đối chiếu.
- Chỉ Chromium; chưa kiểm WebKit hoặc thiết bị thật.
- [Nghiệm thu](ui/MOBILE_001_ACCEPTANCE.md). Không commit/push.

## CHG-20261104-004 — DASH-UI-001: Biểu đồ trực quan và hover/focus

- Ngày04/11/2026, Asia/Saigon; yêu cầu tiếp nối trong scope thực thi DEC-028. Chỉ sửa JS/XML/SCSS custom dashboard và probe: thanh25px/lưới5 mốc, vòng chi phí ba trạng thái, đồng bộ hover/chú giải/tâm vòng, tooltip exact backend, focus/Tab/Escape, tap nguồn, giảm chuyển động. Tỷ trọng/độ dài/tick chỉ là hình học hiển thị; tiền và tổng vẫn từ backend. Không đổi backend/quyền/công thức/filter/workbook/React/core; không commit/push.
- Backup3 source và hash538 bảng trước sửa, thử clone owned18159 trước dev; dev chỉ restart riêng Odoo để nạp asset, không upgrade/seed. UI/RPC60 + probe biểu đồ43 mỗi môi trường;1440/1280/390, zoom125/150 thật, SCSS compile/XML parse/Node syntax đạt. Probe không console error; ma trận hồi quy vẫn1 network error cố ý mỗi môi trường. Ảnh thật desktop/mobile/hover đã xem, GIF ghép hai trạng thái thật tại `.local/dash-hover001/finance-hover.gif`.
- Bảo toàn527/538 bảng nguyên; chứng từ/workbook/user/password/group/ACL/rule/assignment nguyên,249 blob gốc/reference hiện kiểm đạt.3 asset regeneration và telemetry tách khỏi Settings từ phiên Odoo khác lúc13:35:44 (30 config parameter mới/settings/company write_date/cron29/signaling), giữ nguyên thao tác đồng thời. Lỗi SCSS min/calc được bắt/sửa ở clone trước dev; một probe dev cold-load timeout khi kiểm song song đã chạy tuần tự lại đạt.
- [Bàn giao](demo/DASH_UI_001_HANDOFF.md#bổ-sung-biểu-đồ-và-hover-chg-20261104-004). Next action: audit độc lập DASH-UI-001; không đổi gate nghiệp vụ/pilot.

## CHG-20261104-003 — Hiệu chỉnh mốc Git trong bàn giao DASH-UI-001

- Ngày04/11/2026, Asia/Saigon; kiểm `git log/reflog` cuối cho thấy HEAD là `e1dacf4d` từ03/11 16:07:01+07:00, sau commit nguồn `f54fd83f`. Sửa nhầm lẫn baseline trong handoff, không sửa lịch sử hoặc tạo commit.
- Giữ nguyên tài liệu CHG-20261104-002 từ phiên khác trong workspace. Bàn giao/checker chụp trạng thái tài liệu hiện tại, không tự nghiệm thu nhánh tổ chức. Không đổi application code/runtime, không chạy lại test ứng dụng; kết quả DASH-UI-001 vẫn theo CHG-20261104-001.
- Kiểm: log/reflog, diff, local Markdown link/fence và workflow finish/check. Next action: audit độc lập DASH-UI-001; không commit/push.

## CHG-20261104-002 — Xác nhận TADIC/TACICO cùng công ty

- Ngày 04/11/2026, Asia/Saigon: người dùng xác nhận hai nhóm là đơn vị nội bộ cùng công ty. Ghi DEC-029, bổ sung thiết kế database và ghi chú status; không tự suy cây cấp trên, người quản lý hoặc quyền duyệt.
- Giữ một database mỗi môi trường, cùng company và workspace/phạm vi theo quyền; không tạo company/database/khách hàng/dự án trùng. Không đổi application code, schema, dữ liệu, credential hoặc quyền runtime; không commit/push.
- Kiểm tra tài liệu: đối chiếu DEC-002/023 và mô hình tổ chức hiện có; kiểm diff/đường dẫn liên kết. Không chạy lại application tests vì chỉ cập nhật quyết định. Checkpoint DASH-UI-001 đã có từ trước; `start` trả RESUME, giữ nguyên checkpoint và không chạy `finish` thay batch code chưa audit. `ai_workflow.py check` trước sửa đã báo application/tooling code lệch bàn giao; không coi ghi nhận này là nghiệm thu dashboard hoặc làm checker đạt.

## CHG-20261104-001 — DASH-UI-001: Dashboard native rõ số liệu, bộ lọc và thao tác

- Ngày04/11/2026, Asia/Saigon; người dùng cho thực thi riêng task (DEC-028), không commit/push. Baseline Git sạch/check CHG-20261103-001 đạt; start checkpoint trước sửa, snapshot130 checksum/clone18159 restore538 bảng249 blob reference exact trước neutralize.
- Chênh chart xác minh bằng nguồn và tracking: expense11/An Hòa1.850.000 được Administrator duyệt08:44:55 trước task; cơ cấu hiện810.000/1.250.000/5.100.000, tổng7.160.000. Giữ nguyên dữ liệu người dùng;4 invoice nháp801 triệu.
- Addon privacy20.0.1.1.0 thêm report read-only theo ORM/quyền actor, phân bổ analytic từng dòng/currency Odoo/unique count, bộ lọc project/ngày và native source action recheck scope. OWL chỉ2 binding hiện có,4 chỉ số, chart thanh ngang từ0/triệu đồng/tên đầy đủ, bảng dự án, refresh/timestamp thật, lỗi/empty/denied/retry. Share nội bộ ẩn + backend guard cũ; standard Share giữ native. Không sudo nguồn nghiệp vụ, thêm ACL/group/allowlist, đổi workflow/schema nguồn, React/prototype/core hoặc seed chứng từ/user/password.
- Generator/templates và renderer dùng chung; guarded apply/verify giữ ID/quyền, từ chối user drift; DATA003 links chỉ verify, không overwrite dashboard. Upgrade đúng privacy và apply2 dashboard lên18069; chạy lại0 create/update, links verify0 drift.
- Kiểm: Odoo17 test0 failed/0 error, guard5+9/Ruff/Node syntax; UI/RPC clone/dev60 mỗi môi trường1440/1280/390, zoom Chromium thật125/150% không overflow;0 console lỗi không mong đợi,1 network fault cố ý mỗi ma trận. Clone refresh nguồn84→84,5→84 và810.000→820.000→810.000, restore; clone revoke dashboard/project/raw/drilldown/cache thử rồi khôi phục. Smoke native/API/contract/financial scope đạt. Ảnh trước/sau cả hai/bảng đã xem; [runbook](demo/dashboards/README.md), [handoff](demo/DASH_UI_001_HANDOFF.md).
- Vận hành: một lần CLI dev.py stop dừng cảPG làm upgrade không kết nối DB; đã bật lại, kiểm538/538 bảng/config/credential/catalog/roles nguyên, sau đó dùng stop_server chỉ dừng Odoo để nâng cấp. Audit bảo toàn cuối đạt:528/538 bảng nguyên,10 delta dashboard/asset/module metadata/telemetry đã đối chiếu;249 blob gốc/249 reference hiện kiểm đạt, chứng từ/quyền/config nguyên. Clone18159 đã dừng, dev18069/PG55432 chạy; không dựng demo18109/18119.
- Giới hạn: drilldown nguyên chứng từ khác phần phân bổ, chưa multi-currency conversion, Edit spreadsheet không sửa OWL; Windows filestore GC WinError5 cũ vẫn còn. Implementation verified dev/chờ audit độc lập, không business/pilot acceptance. Next: audit DASH-UI-001; giữ TASK-001/DATA003/Q2 và audit khác riêng.

## CHG-20261103-001 — Commit và push các lượt CHG-20261028-016..CHG-20261102-014

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `f54fd83f` gồm 196 đường dẫn (33 sửa, 163 mới) của CHG-20261028-016..CHG-20261102-014: AUTH-002, CTR-002a.1, VI-001/VI-002, các addon demo native và NATIVE-DATA-001..003, tài liệu thiết kế/tham khảo/prompt, 3 báo cáo Word. Một commit vì tài liệu dùng chung bị nhiều phiên sửa xen kẽ. Stage theo danh sách đường dẫn, không `git add .`; status ghi hash; push `main` lên `origin` trong cùng lượt.
- Kiểm tra: quét tên file và nội dung không thấy credential, dump, filestore hoặc Excel thật; actor/contact demo dùng `example.invalid`; ảnh trong file Word là sơ đồ kiến trúc; `git diff --cached --check` chỉ báo dấu cách xuống dòng Markdown/dòng trống cuối file ở 7 tài liệu kiến trúc, giữ nguyên; sau commit working tree sạch, `ai_workflow.py check` đạt; `main` = `origin/main` = `f54fd83f`.
- Giới hạn: không chạy lại test ứng dụng vì không đổi code; kết quả test là của lượt gốc. NATIVE-DATA-003 và AUTH-002 slice 2 vẫn chờ audit như status ghi.
- Next: giữ Next action hiện hành (audit NATIVE-DATA-003 và quyết định policy TASK-001).

## CHG-20261102-014 — Thực thi dữ liệu mẫu liên thông NATIVE-DATA-003

- Ngày:02/11/2026 (Asia/Saigon). Người dùng chuyển vai trò trực tiếp “Chuyển vai trò: thực thi trong phiên này” (DEC-027); checkpoint start riêng từ baseline CHG-013, giữ195 file maintained cũ và mọi thay đổi có sẵn. Không stage/commit/push/production.
- Snapshot private127 checksum; restore clone owned `tp_tanphat_data003_20261102` đạt538 rowset/244 attachment reference exact trước neutralize. Dev18069 giữ188 binding/ID và các tổng gốc; bật8 actor giả, tái dùng employee Bảo22/thêm user29, hierarchy/approver,5 assignment,20 attendee và10 nhóm member. Không đổi admin/planner password/group/assignment.
- B3 application: addon `tp_crm_project_bridge` có FK4 lead→project đúng customer/company/native CRM giao project scope; `tp_timesheet_scope` chặn native own-timesheet ngoài managed project (global rule + explicit create/write/default target checks, constraint Odoo20 chạy sudo); `tp_dashboard_privacy` chặn public share/token của đúng2 bảng nội bộ. Không sửa core/React/OpenAPI/managed-task policy; module/schema install tách khỏi data transaction.
-6 action expense native bằng actor thật:2 draft810.000/2 submitted3.100.000/2 approved3.250.000, tổng7.160.000;2 receipt13/14 vẫn draft, invoice4 vẫn draft801 triệu, không posting/payment. Dashboard nguồn sống theo actor/domain, không ép admin có expense. Native security/expense tạo10 mail `exception`,0 sent/outgoing mới/notification mới; tool cô lập SMTP loopback chỉ trong process. Ghi đầy đủ onboarding To-do115/7 stage, General/digest auto membership,8 OdooBot chat/8 welcome message, chatter/activity và recompute manager của18 dòng giờ.
- Test: Odoo integration27 không fail/error;9 unit guards/Ruff; clone ORM74/dev71,8/8 HTTP actor mỗi môi trường; clone UI58/dev UI/RPC63 ở1440/375 và CSS content zoom125/150%,0 console error/overflow trong ma trận. Ảnh thực đã xem; clone dashboard refresh84→84,5→84; failure-injection bootstrap/native submit rollback538 rowset exact. Reapply dev0 create/update/action và verify0 drift; sửa cumulative journal giữ before đầu/after cuối, không đổi password. Dry-run linkage serialization do chồng bước phụ thuộc đã rollback/chạy tuần tự; thêm3-attempt fresh-transaction retry.
- Preservation audit:486/538 bảng không đổi,52 delta phân loại/allowlist, không xóa row/relation cũ;195 source cũ nguyên,244 blob cũ nguyên/249 ref hiện đạt; dashboard attachment405 đổi riêng. Shared config/credential/cluster roles/database catalog/owner nguyên; không fingerprint nội dung DB khác. Clone18149 dừng, dev/PG chạy,18109/18119 đóng. [Runbook](demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md), [RFC TASK-001](architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md); status/roadmap/decision/workflow/source-map cùng cập nhật.
- Kết quả `PARTIAL_WITH_GAPS`, chờ audit độc lập: managed-task progress của Long vẫn AccessError, không assignee-all-write bypass. Native refuse/reset/correction chỉ clone; chưa business acceptance/pilot, chưa mở TP workflow/BASE/FIN-001. Next: audit phần áp dụng và quyết định policy TASK-001; workflow finish/check chỉ xác nhận handoff theo bằng chứng, không thay nghiệm thu nghiệp vụ.
- Kiểm cuối: dev.py smoke đạt admin/planner session/API/project/contract/financial scope;14 tài liệu/168 link tương đối và fence/CHG marker đạt, Node syntax/Ruff/unit9 và git diff --check đạt. Runtime dev18069/PG55432 mở; clone18149/demo18109/18119 đóng. Giữ staging rỗng, upstream sạch và checkpoint đúng task để finish/check.

## CHG-20261102-013 — Prompt chuẩn hóa bộ dữ liệu mẫu liên thông NATIVE-DATA-003

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu viết prompt để dữ liệu đã thêm liên kết như một tình huống vận hành; phiên chính giữ vai trò điều phối, chỉ soạn tài liệu, không thực thi migrator/đổi DB/quyền/password. Không commit/push.
- Thêm [prompt Claude](prompts/CLAUDE_NATIVE_DATA003_CONNECTED_OPERATIONS.md) có inventory188 binding, backup/clone/restore rehearsal,3 kịch bản, mapping actor/user/employee/project/customer/analytic, bật login có kiểm soát cho actor giả khi được giao, bridge CRM→Project tối thiểu, action chi phí native, dashboard nguồn sống, ma trận quyền/UI/RPC/idempotency/rollback và bàn giao từng batch.
- Phát hiện/kiểm đọc: admin không có employee nên header Expense trả 0; 6 expense draft/tổng 7.160.000 VND thuộc nhân viên khác. Source xác nhận dashboard có employee hierarchy/domain; approve có thể tạo chứng từ; scope managed task hiện chỉ cho user thường đọc. Prompt không cho sudo/manager grant đại trà, ép state, chuyển project unmanaged hoặc gán lại hợp đồng cũ để che gap. Native posting/payment chỉ clone; dev invoice giữ draft, policy managed-task và nghiệp vụ chưa mở trả RFC riêng.
- Baseline: workflow check CHG-012 đạt, không checkpoint khác; start checkpoint tài liệu riêng. Runtime đọc xác nhận dev 18069/PostgreSQL 55432 chạy, 18109/18119 trống; 188 binding và các module native/Home/VI hiện có. Không chạy app suite/build vì không sửa code/runtime.
- Cập nhật PROJECT_STATUS/ROADMAP/DECISIONS (DEC-026: yêu cầu prompt, chưa triển khai). Kiểm link/nội dung, prompt guards, maintained source/runtime baseline, git diff --check và workflow finish/check theo kết quả thực trong handoff.
- Next action: người dùng giao prompt cho phiên Claude triển khai; chưa tuyên bố dữ liệu liên thông/end-to-end hoàn tất, không đóng audit hoặc cổng business/pilot.

## CHG-20261102-012 — Ngừng và lưu trữ môi trường UI-DEMO-001/002 cũ

- Ngày: 02/11/2026 (Asia/Saigon). Task vận hành theo yêu cầu trực tiếp; không commit/push. Checkpoint trước lượt không tồn tại, `check` khớp CHG-011; `start` tạo checkpoint riêng, không finish task khác. Giữ mọi thay đổi chưa commit, không sửa application code.
- Xác minh owner.json/workspace/config/PID/DB token demo; DB test không có token nhưng đăng ký owner, log khởi tạo/test, thời điểm DB và attachment/filestore khớp. Dừng đúng PID 22840/22852 và console con; 18119 đã dừng sẵn. Drop đúng `tp_tanphat_demo_ui001`, `tp_tanphat_demo_ui001_test`; không cần ngắt kết nối nào. Lần gọi DROP đầu bị PostgreSQL từ chối vì transaction context (chưa drop DB nào); thực hiện lại bằng kết nối autocommit độc lập thành công.
- Archive local ACL riêng: `C:\TANPHAT ONE\.local\demo-retirement\20261102-ui001\`; hai dump, runtime ZIP, source TP/tooling, config/metadata/credential riêng ngoài Git. Manifest 18 file SHA-256, hai `pg_restore --list` và đọc toàn dump ra SQL không thực thi, ZIP CRC/source checksum và toàn bộ attachment SHA-1/kích thước đạt. Listing/đọc dump **không phải diễn tập restore**. Runbook đã ghi cách phục hồi, không dùng prepare/seed để tái tạo snapshot.
- Policy công cụ từ chối recursive delete. Thay bằng chuyển nguyên `data`, `logs`, config/owner/credential vào `retired-originals` trong archive (PowerShell LiteralPath, kiểm đường dẫn tuyệt đối/reparse, byte/checksum nguyên). Runtime path cũ chỉ còn screenshots; không giải phóng dung lượng của các bản gốc lưu trữ. Giữ bằng chứng UI-DEMO-001/002 và source addon; không xóa backup cũ.
- Dev 18069/PID14812 và PostgreSQL55432/PID19028 giữ nguyên. Hai DB demo vắng; OID/owner/cấu hình các DB còn lại, roles, dev credential/config, source/Git metadata và 239 blob dev đều khớp. 188 binding fixture/toàn bộ ID nghiệp vụ nguyên, không mất/trùng dữ liệu; 534/538 bảng raw bằng hash. Bốn bảng telemetry thay đổi do smoke: res_users_log +7, res_device_log +7, bus_bus +68, mail_presence timestamp (2 dòng); không sửa lại telemetry.
- Kiểm mới: HTTP login/count/ngôn ngữ admin/planner trước/sau bằng nhau; UI admin 14/14 màn hình desktop (0 console error/overflow, nhãn VI mong đợi); Home 26/26 admin/planner × 1440/375. Đã xem ảnh Home/dashboard. Không chạy Odoo suite/build vì không đổi code/schema dev. `git diff --check`, kiểm link/nội dung và `ai_workflow finish/check` ghi tại handoff.
- Tài liệu: PROJECT_STATUS, ROADMAP, runbook demo. Demo runtime `RUNTIME_RETIRED_ARCHIVED`; các kết quả lịch sử vẫn giữ nguyên, không biến pending audit thành nghiệm thu. Next action: audit các batch Home/To-do/NATIVE-DATA-002/VI-001 trên dev hiện tại theo scope riêng; không tự khôi phục demo cũ.

## CHG-20261102-011 — Giữ nguyên nhãn React contracts (G10)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: chỉ tài liệu. Người dùng chọn “Leave React as is”, nên nhãn React contracts không đổi.
- Đã ghi vào DEC-025, glossary (G10) và status. Không sửa code, không chạy lại test.

## CHG-20261102-010 — Một bộ nhãn tiếng Việt cho `tp_contract` (VI-002)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bản dịch và chuỗi hiển thị của `tp_demo_workspace`. Người dùng chọn catalog mới (DEC-025).
- Đã sửa:
  - `tp_demo_workspace/i18n/vi.po`: 22 lần xuất hiện theo XML ID. Cả 41 lần nay khớp `tp_contract/i18n/vi.po`.
  - 4 bộ lọc cứng trong `contract_views.xml`.
  - `TAX_BASIS_LABELS`.
  - Một dòng trong `docs/demo/UI_DEMO_001_PRESENTATION.md`.
  - Glossary: G9 đã xử lý trong source, thêm G10 cho nhãn React contracts.
- Không đổi state key, XML ID, domain, dữ liệu, React hay quyền.
- Test trên DB tạm `tp_tanphat_demo_vi002_test`, đã drop sau khi chạy:
  - Cài với vi_VN, chạy `/tp_demo_workspace,/tp_contract`: 0 failed, 0 error trên 74 test.
  - 42/42 nhãn vi_VN khớp catalog. Không view demo nào còn chữ lọc cũ. Ruff đạt.
- Không chạm demo18109, dev hay `tp_tanphat_data002_test`. Không commit/push.

## CHG-20261102-009 — Việt hóa giao diện Odoo native và addon TP (VI-001)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bản dịch, dữ liệu ngôn ngữ dev và tài liệu. Batch B của prompt CHG-090.
- Thêm:
  - Addon mới `custom_addons/tp_i18n_vi/`: chỉ có `i18n/vi.po` với 37 mục overlay, README và 4 test (catalog khớp nguồn en_US, overlay thắng khi overwrite, nạp sau module gốc, không sở hữu `ir.model.data`).
  - `i18n/vi.po` cho `tp_core` (17), `tp_organization` (2), `tp_project` (42) và `tp_contract` (193, chỉ nhãn).
  - Tài liệu [docs/i18n/VI_GLOSSARY_AND_COVERAGE.md](i18n/VI_GLOSSARY_AND_COVERAGE.md).
- Không sửa `odoo/` hay `addons/`, React, API, quyền.
- Test trên DB cô lập `tp_tanphat_data002_test`:
  - `--test-tags /tp_i18n_vi` cho 0 lỗi trên 4 test; `/tp_project,/tp_i18n_vi` cho 0 lỗi trên 16 test.
  - Ruff đạt. 5 catalog có 0 mục chưa dịch, 0 fuzzy.
  - Probe 313 menu: 7 menu cố ý giữ nguyên.
  - Revert về en_US rồi apply lại đạt. Số liệu dashboard giống nhau giữa en_US và vi_VN.
- Dev `tp_tanphat_dev`:
  - Snapshot `.local/vi001/snapshot-dev-20261102-121509` (247 checksum, verify đạt).
  - loadlang vi_VN, `-i tp_i18n_vi`, `-u tp_i18n_vi --i18n-overwrite`, import 4 catalog TP, `vi_apply` dry-run/apply/verify: tất cả exit 0.
  - Chỉ admin chuyển sang vi_VN.
  - UI admin 24 màn hình × (1440, 375, zoom 125%, zoom 150%) và dialog xuất/xoá (chưa xác nhận) đạt. planner.dev en_US đạt.
  - Fingerprint group/ACL/rule/bảng nghiệp vụ không đổi.
- Còn gap G1–G9 (G9: nhãn `tp_contract` dịch khác giữa `tp_demo_workspace` và catalog mới). Giao diện đủ cho trình diễn, chưa phải nghiệm thu. Không commit/push.

## CHG-20261102-008 — Bổ sung lịch, nhóm trao đổi, bảng tổng hợp mẫu (NATIVE-DATA-002)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: dữ liệu mẫu dev + tài liệu. Batch A của prompt CHG-090: 8 lịch riêng tư admin, 3 nhóm Discuss riêng/12 tin, 2 dashboard native chỉ admin (công thức PIVOT theo quyền người xem), 6 mục Danh mục công việc; tổng 31 bản ghi, namespace `tp_native_data002_20261102`. Git: template + generator `docs/demo/dashboards/`, bảng phủ 14 menu/runbook trong `docs/demo/ODOO_NATIVE_SAMPLE_DATA.md`. Seeder ngoài Git `.local/data002/`.
- Test: DB cô lập `tp_tanphat_data002_test`: dry-run 31 (0 dòng cũ đổi trên 22 bảng), fail-test rollback (0 binding/0 event), apply 31 → verify 0, cập nhật template updated=2 → verify 0; HTTP/UI admin và planner.dev 1440/375 đạt; Ruff `build_templates.py` đạt.
- Dev `tp_tanphat_dev`: snapshot `.local/data002/snapshot-batchA-20261102T044155Z` (241 checksum), apply 31 → verify created=0/updated=0; planner.dev: lịch “Busy”, nhóm/tin/dashboard/hóa đơn AccessError hoặc rỗng. Dữ liệu đủ cho trình diễn, chưa phải nghiệm thu nghiệp vụ. Không commit/push.

## CHG-20261102-007 — Sửa quyền To-do native và nạp 14 việc cá nhân mẫu (TODO-001)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bảo mật `tp_project` + dữ liệu mẫu dev. `custom_addons/tp_project/security/ir.access.csv`: `task_platform_scope` và `task_platform_write_scope` (nhánh user không là TP manager) thêm `('project_id', '=', False)`; giữ global rule, company scope, assignment/grant và rule native.
- Test: 6 regression `TestPrivateTodoAccess` trong `tp_project/tests/test_project_access.py`; DB cô lập `tp_tanphat_data002_test`: rule cũ `0 failed, 3 error(s) of 6`, rule mới `--test-tags /tp_project` `0 failed, 0 error(s) of 12`; `-u project_todo,tp_project` tích hợp 23/25 (2 test at_install native lỗi thứ tự nạp `tp_project`, không do thay đổi này); Ruff đạt.
- Dev `tp_tanphat_dev`: snapshot `.local/data002/snapshot-20261102T041428Z` (241 checksum), `-u tp_project` exit 0; `seed_todo.py` dry-run → apply 14 → verify created=0; live admin Open 13 (12 + onboarding native có sẵn), planner.dev AccessError khi gọi trực tiếp. Không commit/push.

## CHG-20261102-006 — Trang chủ native TANPHAT ONE dạng lưới ứng dụng (UI-HOME-001)

- Ngày: 02/11/2026 (Asia/Saigon). Triển khai prompt CHG-005: addon mới `custom_addons/tp_web_home/` (depends `web`; client action `tp_web_home.home`/path `tp-home`, root menu “Trang chủ” `base.group_user` sequence 1, systray nút Trang chủ, lưới ô/tìm có-không dấu/alias, nhóm “Công việc & nghiệp vụ”/“Công cụ hệ thống”, SCSS scoped `o_tp_web_home`). Ô từ menu service native theo quyền, chờ `load_menus` mới trước lần render đầu; không model/ACL/controller, không ghi `res.users.action_id`, không patch WebClient/router, không sửa `odoo/`, `addons/`, React, OpenAPI, auth hoặc `tp_demo_workspace`.
- Test cô lập DB `tp_tanphat_home001_test`/18129, user và công ty giả, secret `.local/home001/` ngoài Git: Odoo `--test-tags /tp_web_home` 0 failed/0 error of 10; HOOT 15/15; Playwright 66/66 (quyền, route, back/forward/reload, deep link, Ctrl-click, tìm, Escape/Enter/Tab, guard form chưa hợp lệ, đổi công ty, logout/login không lộ menu cũ, Home Action riêng, 1440/1366/1024/768/375, zoom 125/150%, reduced motion, không lỗi console); gỡ cài sạch (0 xmlid/action/menu, `/odoo` về Discuss, Home Action giữ) rồi cài lại; Ruff đạt. Icon mobile nâng 64→68px theo spec trong lượt kiểm.
- Dev: snapshot `.local/home001/dev-snapshot/` (dump + filestore + config/source manifest, 233 checksum, verify đạt; chưa diễn tập restore) rồi chỉ `-i tp_web_home` lên `tp_tanphat_dev`, exit 0, không dừng dev18069/demo18109. So fingerprint: chỉ bảng menu/action/module/attachment/signaling đổi, `tp_*`/user/nhóm/ACL/rule/project/partner không đổi, 0 user có Home Action = Trang chủ. Live admin/planner.dev 1440/375: 26/26. [Runbook](demo/UI_HOME_001_RUNBOOK.md).
- Trạng thái `IMPLEMENTED_PENDING_AUDIT`; chưa vào `dev.py` MODULES. Không commit/push; TODO-001, NATIVE-DATA-002/VI-001, UI-DEMO-001/002, AUTH-002/C01 và cổng nghiệp vụ/pilot giữ nguyên.

## CHG-20261102-090 — Prompt bổ sung dữ liệu toàn menu và Việt hóa (chờ tích hợp handoff)

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu prompt bổ sung phần dữ liệu còn thiếu, sau đó thêm Việt hóa toàn hệ thống trừ từ đặc thù. Tạo [prompt NATIVE-DATA-002 + VI-001](prompts/CLAUDE_NATIVE_DATA002_AND_VI001_COMPLETE_DEMO.md), hai batch triển khai riêng; chỉ chuẩn bị prompt, chưa seed/cài/chỉnh ngôn ngữ.
- Đối chiếu coverage dữ liệu read-only trước đó; đọc source notification Calendar/Discuss và quyền dashboard để đặt yêu cầu tránh gửi tới người khác/lộ cached money. Kiểm HTTP admin res.lang/res.users chỉ có en_US active, admin en_US; source base có vi_VN, upstream có catalog vi.po. Không suy việc có catalog nghĩa là UI đã dịch. Evidence .local/native-data-20261102/language-coverage-audit.json ngoài Git.
- Quy định target dữ liệu thiếu: To-do tái dùng TODO-001, 8 lịch riêng, 3 nhóm riêng/12 tin admin, 2 dashboard đọc domain fixture và hạn chế người xem. Bảo toàn 4 project/28 task/8 partner/10 lead/12 employee/20 timesheet/6 expense/4 invoice. Apps/Settings không thêm cấu hình giả. Việt hóa bề mặt app/luồng hiện có, glossary, locale/catalog chuẩn, không đổi identifiers hoặc dịch thay DOM toàn cục.
- Preflight phát hiện tp_web_home đang được tạo và checkpoint ACTIVE (03:15:28Z); checker fail code changed after handoff. Giữ checkpoint và AI_WORKFLOW_STATE của batch đó, không start/finish thay. Thêm ghi chú status, giữ Last change mốc đã finish; ID 090 dành cho prompt để giảm xung đột batch implementation đang chạy, chưa được workflow finish độc lập. Chủ batch tiếp theo tích hợp ghi chú vào bàn giao khi phù hợp.
- Kiểm local links/fence/nội dung và git diff --check cho tài liệu mới; không test ứng dụng hoặc tuyên bố maintained code unchanged vì agent khác đang sửa. Không sửa application code/runtime/DB/quyền, không commit/push; Next action audit khác giữ nguyên.

## CHG-20261102-005 — Chuẩn bị trang Home native dạng lưới ứng dụng

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng đồng ý dựng Home theo ảnh. Phiên chính giữ vai trò điều phối: tạo [prompt UI-HOME-001](prompts/CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md), có thiết kế icon/nền/tìm kiếm, mapping XML ID, native action/root menu/Home button, test quyền/route/unsaved form và điều kiện cài dev sau test. Chưa phải UI đã triển khai.
- Áp dụng skill frontend-design và guideline Odoo web local. Đọc source menuService/WebClient/action plugin/NavBar, kiểm Home Action native và HTTP cây menu admin/planner.dev (14/9 root apps, admin chưa đặt Home Action), lưu evidence `.local/home001-preparation/runtime-menus.json` ngoài Git. Không suy cài module từ tên trong roadmap; tách native Project/TP Projects và Invoicing/TP Finance.
- Đối chiếu HTTP 200 README/manifest/template/source OCA web_responsive20, commit 6ac74409cd559529374236476353d453d5568c5e (29/10 UTC): có fullscreen app menu nhưng phạm vi còn chạm form/list/chatter/user settings; chưa compatibility-tested. Chọn thiết kế addon Home riêng, không tải/cài cả OCA hoặc sao chép Enterprise. Link raw filename JS ban đầu trả 404; đã xác định tên apps_menu.esm.js và đọc thành công, không coi 404 là module thiếu.
- Cập nhật status/roadmap, kiểm local links/fence/mapping, git diff --check và workflow finish/check; maintained application code không đổi. Không chạy Odoo/HOOT/browser E2E vì chỉ chuẩn bị prompt; chúng là acceptance bắt buộc của Claude. Không đổi DB/runtime/quyền/code/schema, không commit/push; TODO-001 và các audit tồn đọng giữ riêng.

## CHG-20261102-004 — Phát hiện lỗi quyền To-do và chuẩn bị correction cho Claude

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu thêm dữ liệu To-do; khi phát hiện cần sửa app, người dùng chọn viết prompt cho Claude, giữ vai trò phiên chính điều phối. [Prompt TODO-001](prompts/CLAUDE_TODO001_NATIVE_PRIVATE_TASK_FIX_AND_SAMPLE.md) giao sửa domain tối thiểu, regression quyền riêng tư/company/project và nạp 14 việc giả sau test đạt.
- Snapshot dev trước thử `.local/native-data-20261102/backup-20261102T025223Z/`: dump/filestore chuẩn/manifest SHA256, pg_restore listing đạt; chỉ restart đúng dev18069, không đổi demo18109/PostgreSQL. Chưa restore rehearsal snapshot mới.
- Helper local seed_todo.py chuẩn bị 12 open và 2 done, namespace riêng và guard/transaction/idempotence. Dry-run thất bại ở bản đầu: admin read=False, write/unlink=True; env.flush_all vẫn lỗi, rollback toàn bộ. Nghi phạm task_platform_scope thiếu nhánh project_id=False; không dùng sudo hoặc mở rule để nạp qua lỗi. Registry read-only xác nhận namespace 0 binding, 28 task dự án giả còn nguyên; evidence todo-dry-run.log/todo-blocked-verification.json ngoài Git.
- Không sửa application code/core/security/schema, không lưu To-do mới, không đổi user/grant/approval/payment; không commit/push. Cập nhật status, tài liệu dữ liệu và prompt; kiểm local links, git diff --check, workflow finish/check. Không tuyên bố seed hoặc regression tests đạt. Các Next action audit UI-DEMO-001/002, AUTH-002/C01 giữ nguyên.

## CHG-20261102-003 — Hiệu chỉnh kết quả kiểm liên kết bàn giao

- Ngày: 02/11/2026 (Asia/Saigon). Kiểm link tổng ba tài liệu ở cuối CHG-002 phát hiện hai tham chiếu lịch sử cùng trỏ tới DOCX so sánh edition không còn trong deliverables. Shell đã tiếp tục finish dù bước assert link lỗi, nên reported_checks CHG-002 ghi link đạt là không chính xác. Ghi đính chính tại đây, không sửa JSON checker bằng tay hoặc tái sử dụng ID.
- Bỏ hai link chết, giữ tên file và ghi rõ tình trạng thiếu DOCX; còn PDF ở `.local/edition-comparison-report/render/`. Không tái tạo báo cáo ngoài scope. Các kiểm dữ liệu/HTTP/phân quyền CHG-002 đã chạy đạt riêng, không bị ảnh hưởng.
- Chạy lại kiểm local links ba tài liệu và git diff --check; workflow finish/check. Chỉ thay tài liệu, không đổi application code/runtime/DB, không commit/push hoặc đổi Next action audit.

## CHG-20261102-002 — Liên kết dữ liệu giả giữa TP Projects và các ứng dụng chuẩn

- Ngày: 02/11/2026 (Asia/Saigon). Theo yêu cầu làm dữ liệu khớp giữa các module, dùng nguyên bốn project ID đã nạp ở CHG-001; đánh dấu managed, mã DA-2026-001…004, phòng chủ trì, 27 assignment reader/coordinator và nhóm Platform User chỉ cho 10 user giả không password. Không cấp TP manager/grant hoặc thay user thật. [Mapping, thao tác và evidence](demo/ODOO_NATIVE_SAMPLE_DATA.md).
- Bốn cơ hội CRM dùng cùng khách hàng, tag mã dự án và tham chiếu trong mô tả; không tuyên bố có CRM → Project tự động. Task/nhân sự/timesheet/chi phí giữ ID và phân bổ tương ứng. Ba hóa đơn cũ bổ sung Origin/Reference; thêm một nháp An Hòa 185 triệu và phân bổ analytic, không posted/payment hoặc hợp đồng TP. Giữ provenance giả lập trong mô tả/namespace; không thêm project/task trùng.
- Snapshot trước sửa `.local/native-data-20261102/backup-20261102T023505Z/`: dump + canonical filestore + manifest SHA256, pg_restore listing đạt; chưa diễn tập restore snapshot mới. Dry-run ban đầu rollback vì write_date của partner user giả; xác định ownership đúng ID và kiểm business fields giữ nguyên, không nới hash bảo vệ dữ liệu khác.
- Kiểm thực chạy: helper local dry-run/apply/verify qua registry mới, verify created={}; hash ngoài fixture không đổi, không tăng project/task/grant/mail/posted. HTTP hai action Project/TP Projects cùng model/cùng bốn ID, CRM/customer/tag/reference, task/giờ làm/invoice khớp; link chuẩn mở được. API admin có bốn dự án; planner.dev giữ một dự án cũ và 404 khi truy cập bốn ID mới; ORM chặn dự án/task ngoài assignment. Admin native ACL/form và project CRUD savepoint rollback đạt. git diff --check và workflow finish/check; không chạy toàn bộ app tests do không đổi application code/schema.
- Cập nhật status và tài liệu dữ liệu; helper/evidence ngoài Git. Không sửa application code/core, module/schema, mật khẩu, grant người thật, demo18109 hoặc Next action audit UI-DEMO-001/002, AUTH-002/C01; không commit/push, BASE approval/ký/hiệu lực/thanh toán/pilot.

## CHG-20261102-001 — Thêm dữ liệu trải nghiệm trên giao diện Odoo chuẩn

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu thêm dữ liệu vào native Odoo đang xem và bỏ dấu DEMO trên tên. Đã thêm bộ dữ liệu giả tên tự nhiên trên dev 18069; vẫn giữ provenance/nhận diện môi trường. [Danh mục, hướng dẫn và kiểm chứng](demo/ODOO_NATIVE_SAMPLE_DATA.md).
- Thêm bằng ORM, transaction nguyên tử, XML ID namespace riêng: 8 đối tác, 10 cơ hội CRM, 4 project không TP managed, 28 task, 5 phòng ban/12 nhân sự, 20 timesheet, 6 chi phí nháp, 3 hóa đơn nháp và 1 sản phẩm. Thêm 10 user giả không mật khẩu để gắn người phụ trách, không TP grant/lời mời. Email giả dùng example.invalid, mô tả phù hợp ghi nguồn giả lập; không chứng từ posted/thanh toán hoặc hồ sơ thật.
- Snapshot dữ liệu trước nạp `.local/native-data-20261102/backup-20261102T015925Z/`: pg_dump + canonical filestore, manifest SHA-256, pg_restore --list đạt; dừng/khởi động lại đúng dev Odoo sở hữu, giữ PostgreSQL/demo18109. Không tuyên bố đã restore snapshot này; không dùng OPS backup committed-source vì checkout có thay đổi chưa commit.
- Kiểm thực chạy: dry-run sửa lỗi tương thích helper Odoo 20 rồi rollback đạt; commit thành công; registry mới verify binding/count, new_records={} và hash dòng TP/user/grant cũ không đổi. HTTP admin đọc đủ dữ liệu tám nhóm, tiền/nháp và người phụ trách đúng; API TP không lẫn project mới. ACL/form native sáu model cho phép thao tác; project create/edit/delete probe savepoint rollback đạt. 0 mail mới, 0 posted mới; kiểm user giả không password. Helper/log/báo cáo local ngoài Git. git diff --check, workflow finish/check; không chạy toàn bộ app tests vì không đổi code ứng dụng.
- Không sửa application code, core, database schema, quyền có sẵn, cấu hình gửi mail, UI-DEMO-001/002 hoặc Next action audit. Không commit/push, không phê duyệt pilot/BASE/ký/hiệu lực hoặc cấp quyền người thật.

## CHG-20261031-002 — Báo cáo Word so sánh Community và Enterprise

- Ngày: 31/10/2026 (Asia/Saigon). Theo yêu cầu người dùng tạo một file Word tổng hợp tính năng, tùy biến và chi phí. Ghi nhận xuất báo cáo 4 trang `deliverables/TANPHAT_ONE_So_sanh_Odoo_Community_Enterprise.docx` dựa trên nguồn chính thức đã kiểm ở CHG-001; giải thích thuật ngữ và đề xuất cho TANPHAT ONE, không phải quyết định mua hoặc báo giá. Bổ sung kiểm chứng CHG-20261102-003: DOCX hiện thiếu tại đường dẫn này, còn PDF local; bỏ link chết, chưa tái tạo báo cáo.
- Phân biệt Standard Online/Custom self-host hoặc Odoo.sh, mã nguồn mở Community/điều khoản Enterprise, API và web riêng, thuê bao/tổng chi phí, User/Light User; ví dụ 30/50/100 người dùng, không tự bịa chi phí triển khai hoặc giá gia hạn. Không thay đổi nguồn nghiên cứu, application code, runtime hoặc database.
- Kiểm chứng: bundled Python python-docx; render_docx.py lần đầu báo thiếu soffice.exe trên Windows, dùng Microsoft Word xuất PDF rồi adapter local gọi rasterizer canonical với bundled Poppler; 4 trang PNG đã xem toàn bộ và sửa đường viền Title trước render cuối. Word COM mất kết nối lúc Quit sau xuất PDF thành công; đã xử lý cleanup ở script local và render cuối thành công. Kiểm cấu trúc DOCX, nội dung, số liệu, link tài liệu và git diff --check; workflow finish/check. Không chạy application tests vì chỉ xuất báo cáo; helper/PDF/PNG ở .local ngoài Git.
- Giữ nguyên Next action audit độc lập UI-DEMO-001/002 và AUTH-002/C01; không commit/push, cài app, mua license hoặc mở scope nghiệp vụ.

## CHG-20261031-001 — So sánh Odoo Community/Enterprise, tùy biến và chi phí

- Ngày: 31/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, tạo [bản so sánh edition](architecture/TP_ODOO_COMMUNITY_ENTERPRISE_COMPARISON.md): tính năng, deployment, quyền tùy biến, Studio/addon/API/React, phí thuê bao và tổng chi phí sở hữu; không phải báo giá hoặc quyết định mua.
- Đọc nội dung nguồn chính thức Editions/Pricing/Enterprise Agreement/External API và đối chiếu inventory/source LGPL-3 local; giữ snapshot công khai ngoài Git tại `.local/edition-comparison-research/`. Giá USD theo phiên tra cứu (Custom trả năm ưu đãi 13,40, niêm yết hiện tại 16,40/user/tháng); không mặc định áp dụng thị trường TP hoặc giá gia hạn. Tách phí hạ tầng, lập trình, bảo trì, thuế và dịch vụ; ghi lưu ý User/Light User theo Agreement v13.
- Khuyến nghị tiếp tục Community trong giai đoạn hiện tại, làm fit-gap/quote/TCO 3 năm trước quyết định Enterprise; đây là đề xuất, không mở scope/mua hàng. Cập nhật status/index; Next action UI-DEMO-001/002, AUTH-002/C01 và các cổng nghiệp vụ giữ nguyên.
- Kiểm chứng: đọc nguồn HTML và biểu tượng edition có/không, số liệu giá/thuê bao, local links/fence/UTF-8, snapshot code trước/sau và git diff --check; workflow finish/check. Không chạy application tests do chỉ nghiên cứu/tài liệu; không cài module, đổi database/runtime, code, commit hoặc push.

## CHG-20261030-005 — Triển khai điều hướng demo theo công việc (UI-DEMO-002)

- Ngày: triển khai 30/10/2026, tiếp tục checkpoint và chốt bàn giao 31/10/2026 (Asia/Saigon). Yêu cầu trực tiếp triển khai bản chạy được theo prompt UI-DEMO-002; trạng thái `IMPLEMENTED_PENDING_AUDIT`, không tự nghiệm thu UI-DEMO-001/AUTH-002/C01.
- Thay hàng tab dài/dấu cộng trong app Demo bằng hai tầng desktop và sáu nhóm Việt; “Tất cả phân hệ”/“Phân hệ” mở dialog tìm không dấu/alias, tên TP chuẩn, mô tả và nhãn minh họa. Toàn bộ 17 leaf giữ action/XML ID; kỹ sư chỉ 15 leaf, không CRM/Bid. Thay menu XML, thêm `static/src/navigation/`, HOOT và hai test server menu; đăng ký assets trong manifest.
- Native extension: QWeb inheritance theo `menu_demo_root`, patch tĩnh tối thiểu đăng ký `NavBar.components`; menu service là nguồn cây quyền, `selectMenu(actualMenu)` là đường điều hướng. Active theo action/controller native, không `doAction` bổ sung, không patch router/service/core. SCSS portal riêng, focus/Esc và cleanup dùng lifecycle/component native.
- Snapshot trước/sau xác nhận code ngoài addon, 25 tracked diff ngoài handoff và sáu SCSS cũ không đổi; giữ nghiệp vụ/model/ACL/grant/seed, React/API, app khác và cảnh báo môi trường. Chỉ upgrade/rebuild runtime demo sở hữu riêng trong lượt triển khai, không sửa DB dev/test; lượt tiếp tục chỉ start demo và chạy test DB demo test.
- Kiểm cuối: `ui_demo.py test` **21 passed, 0 failed/error, không skip được báo** trên `tp_tanphat_demo_ui001_test`; HOOT **6/6**; Ruff đạt. Live Chromium hai actor **17/17 + 15/15** leaf, tìm/active/deep link/reload/history/chuyển app, context dự án, bàn phím/logout đạt. Mười cấu hình viewport 1440/1366/1024/768/375 và bốn ca zoom thật 125%/150% đạt; focus không bị che, reduced motion hoạt động, không lỗi console/network. Log Odoo có cảnh báo markdown2/filestore GC Windows đã biết và test quyền âm mong đợi; không chạy React checks vì không đổi React.
- Cập nhật status/roadmap/spec/README/runbook/kịch bản và [bàn giao file, mapping, ảnh, lệnh/log](demo/UI_DEMO_002_HANDOFF.md). Đã áp dụng skill `C:/Users/vuduc/.codex/skills/frontend-design/SKILL.md` và `skills/odoo-web-guidelines/SKILL.md`. Demo để chạy tại `http://127.0.0.1:18109/odoo`; không commit/push/deploy. Next action: phiên điều phối audit độc lập UI-DEMO-001/002 và quyết định phạm vi trình diễn; business acceptance/pilot vẫn riêng.

## CHG-20261030-004 — Prompt cải tiến điều hướng demo (UI-DEMO-002)

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng gửi ảnh thanh tab native Odoo và yêu cầu prompt làm dễ nhìn, dễ hiểu, đầy đủ hơn. Phiên chính chỉ chuẩn bị prompt; trạng thái `PROMPT_READY`, chưa có code navigation mới.
- Tạo [prompt UI-DEMO-002](prompts/CLAUDE_UI002_DEMO_NAVIGATION.md): sáu nhóm nghiệp vụ, nhãn Việt kèm tên TP chuẩn, selector “Tất cả phân hệ” có tìm nhanh, đủ điểm đến hiện có theo quyền. Nêu cụ thể native menu service/template extension và bẫy overflow More 46px của NavBar Odoo 20, namespace theo app, keyboard/responsive và kiểm hai actor.
- Yêu cầu mới thay lựa chọn UX giữ menu của CHG-003 trong phạm vi demo; giữ SCSS hiện tại, các app khác, React/API, workflow, quyền và runtime. Không triển khai nghiệp vụ mới hoặc tự nghiệm thu UI-DEMO-001/AUTH-002/C01; không commit/push.
- Kiểm chứng: đọc cây menu/action/NavBar local, skill frontend-design và guideline Odoo web; checker baseline CHG-003 đạt. Đối chiếu snapshot maintained và SCSS trước/sau, kiểm mapping 12 phân hệ/action, liên kết/fence/UTF-8 và git diff --check; không chạy lại application tests cho lượt prompt/tài liệu. Kết quả cuối ghi trong workflow handoff.
- Next action: Claude thực hiện prompt; phiên chính audit navigation và phần demo còn pending sau bàn giao.

## CHG-20261030-003 — Ghi chú menu demo và làm mới giao diện UI-DEMO-001

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng hỏi vì sao menu có hai app “TANPHAT ONE” và chọn **giữ nguyên menu**; sau đó yêu cầu “chỉnh lại giao diện bản demo cho đẹp hơn”. Trạng thái demo vẫn `IMPLEMENTED_PENDING_AUDIT`.
- Menu: ghi vào [runbook](../ops/runbooks/UI_DEMO_001.md), [kịch bản trình bày](demo/UI_DEMO_001_PRESENTATION.md) và [đặc tả §7](architecture/TP_UI_DEMO_001_SPEC.md) rằng app “TANPHAT ONE” là `tp_core.menu_platform` hiện do nhóm demo kế thừa `tp_core.group_user`, “Ứng dụng” do `base_install_request`; người trình bày chỉ dùng app Demo. Không đổi menu, nhóm hay quyền.
- Giao diện: chỉ năm file SCSS của `tp_demo_workspace` (namespace `.o_tp_demo`): dải đầu trang dạng bản vẽ, KPI/panel bo góc có bóng nhẹ và nhấc khi hover, chuỗi dự án dạng viên thuốc, làn phân hệ có viền trái theo bản chất dữ liệu, ô “Góc nhìn” nền trắng, dải cảnh báo gọn trên điện thoại, hiện dần tắt theo reduced motion. Đặc tả §8 cập nhật bảng màu/bo góc/chuyển động. Không đổi template, JS, Python, ACL/rule, seed, tooling, React/API hay `odoo/`/`addons/`.
- Test: `scripts\ui_demo.py test` 0 failed, 0 error(s) of 19 tests; `python -m unittest scripts.tests.test_ui_demo` 10/10; kiểm trình duyệt thủ công `demo.lanhdao` ở 1440/1366/375 không cuộn ngang, tương phản màu WCAG ≥ 5,3:1 cho chữ. Demo chạy lại tại `127.0.0.1:18109` (build lại asset bằng stop/prepare/start). Không commit/push.
- Next action: phiên điều phối audit UI-DEMO-001 gồm cả lượt này; nếu cần, chụp lại đủ 12 màn hình và xem bằng `demo.kysu` trước buổi trình bày.

## CHG-20261030-002 — Triển khai demo native Odoo toàn hệ thống (UI-DEMO-001)

- Ngày: 30/10/2026 (Asia/Saigon). Phiên Claude thực thi theo [prompt UI-DEMO-001](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md) và DEC-024. Trạng thái `IMPLEMENTED_PENDING_AUDIT`, không phải technical/business acceptance.
- Thêm addon `custom_addons/tp_demo_workspace/` (nhóm demo, app “TANPHAT ONE – Demo”, 12 màn hình A–L, projection đọc `tp.demo.workspace` theo quyền người xem không `sudo`, view native chỉ đọc, catalog minh họa trong Python, seed idempotent `demo_seed.py`, 19 Odoo tests), tooling `scripts/ui_demo.py` + `scripts/tests/test_ui_demo.py`, [đặc tả](architecture/TP_UI_DEMO_001_SPEC.md), [runbook](../ops/runbooks/UI_DEMO_001.md), [kịch bản trình bày](demo/UI_DEMO_001_PRESENTATION.md). Một ACL mới chỉ đọc `crm.lead` cho nhóm demo kinh doanh; không đổi ACL/rule/workflow TP hiện có.
- Runtime riêng: DB `tp_tanphat_demo_ui001` (+ `_test`), `127.0.0.1:18109`, `.local/ui-demo-001/` ignored, cron tắt, DB neutralize, SMTP cổng đóng; dữ liệu và tệp giả, hai actor `demo.lanhdao`/`demo.kysu`, mật khẩu sinh local không vào Git.
- Test: `ruff check` đạt; tool guard 10/10; Odoo **0 failed, 0 error(s) of 19 tests** (ORM, read_group, export, `/web/content`, ghi trực tiếp bị chặn, phủ định actor không grant); kiểm trình duyệt hai actor ở 1440/1366/375, focus, reduced motion, RPC và tải tệp trực tiếp phủ định. Không đổi React/OpenAPI/API, DB dev/test, `scripts/dev.py`, `odoo/`/`addons/`; không cài `tp_web_login`; không commit/push.
- Next action: phiên điều phối audit demo trước khi trình lãnh đạo; audit AUTH-002 slice 2 vẫn là việc riêng.

## CHG-20261030-001 — Prompt dựng demo native Odoo toàn hệ thống

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng chọn trực tiếp native Odoo để demo trước và khung toàn hệ thống cho lãnh đạo; phiên chính tiếp tục điều phối, không trực tiếp sửa application code.
- Task: UI-DEMO-001. Ghi DEC-024; tạo [prompt Claude triển khai](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md), cập nhật PROJECT_STATUS/ROADMAP/index kiến trúc. Phạm vi gồm common workspace, chín phân hệ hiện hành + CRM/Request/Bid giới thiệu; tận dụng native read views, phần chưa có là minh họa có nhãn.
- Prompt yêu cầu DB/config/data-dir/port riêng, dữ liệu/actor giả, seeder/tooling có ownership guard, scope/grant backend kể cả read_group/export/file, test native/live và ảnh/kịch bản trình bày. Không đổi React/API, core, DB dev/test, BASE/ký/hiệu lực/thanh toán hoặc grant người thật; AUTH-002 audit và C01 giữ là việc riêng.
- Kiểm chứng thực: snapshot maintained trước/sau bằng nhau (139 file, digest `46eff2f307c6e3a1260b635889c840899ae91cb49c85a02001ab6f93df77562e`); kiểm UTF-8/fence/bảng/link của 6 tài liệu, 70 link local và 0 lỗi; `git diff --check` đạt (chỉ cảnh báo LF/CRLF có sẵn). Không chạy test ứng dụng cho lượt tài liệu. Trạng thái PROMPT_READY, chưa triển khai addon hoặc runtime demo; không commit/push.
- Next action: Claude triển khai theo prompt; phiên điều phối audit kết quả và phân biệt khả năng runtime với minh họa trước khi dùng trình lãnh đạo.

## CHG-20261029-052 — Kiểm kê module Odoo 20 và trạng thái cài đặt

- Ngày: 29/10/2026 (Asia/Saigon). Người dùng yêu cầu danh sách module nghiệp vụ toàn Odoo 20, chức năng và module đã cài trong TANPHAT ONE.
- Tạo [TP_ODOO20_MODULE_INVENTORY.md](architecture/TP_ODOO20_MODULE_INVENTORY.md): 643 manifest `addons/` + core `base`, 7 custom addon, 34 ứng dụng chuẩn; danh mục ứng dụng với chức năng tiếng Việt và toàn bộ 651 manifest local thuộc phạm vi (không gồm 15 test framework trong `odoo/addons/`). Bảng chi tiết giữ tên/summary/category theo manifest, không coi đó là nghiệm thu runtime.
- SELECT `ir_module_module` read-only trên dev/test xác nhận 87/85 installed; chỉ dev có thêm `l10n_vn` và `account_qr_code_emv`. `tp_web_login` có source nhưng chưa cài trên hai database này; không dùng trạng thái verify DB thay dev/test.
- Đọc HTTP 200 danh mục All Apps, tài liệu Odoo 20 và Editions; phân biệt app được giới thiệu với addon kỹ thuật, source có sẵn với installed, accounting nền với Enterprise, các ứng dụng ngoài checkout với chức năng đã chạy. Snapshot metadata/trạng thái ở `.local/module_inventory/` ngoài Git; không lưu credential hoặc dữ liệu nghiệp vụ.
- Không cài module, không start/stop/upgrade/seed, không sửa application code, OpenAPI, database/schema hoặc quy chế nghiệp vụ. Không commit/push.
- Kiểm tra: đối chiếu source manifest và database read-only; kiểm bảng/link và count/status; maintained code snapshot không đổi; `git diff --check`; workflow finish/check. Không chạy application tests vì đây là inventory/tài liệu.
- Next action: giữ audit độc lập AUTH-002 slice 2; danh mục này là nguồn tra cứu, không tự mở task hay cho phép cài module.

## CHG-20261029-051 — Làm rõ phạm vi quyết định UX DEC-023

- Ngày: 29/10/2026 (Asia/Saigon). Rà soát lại cách ghi DEC-023 sau khi người dùng xác nhận nguyên tắc giao diện chung.
- Làm rõ phần người dùng đã chốt: một nền/common shell chung, trải nghiệm thay đổi theo phòng ban/vai trò/quyền và không tạo frontend lặp theo phòng. Các workspace/menu/dashboard/field/route/action cụ thể, shared detail và DTO `allowed_actions` được đánh dấu là hướng thiết kế đề xuất cần owner/spec theo domain.
- Cập nhật `docs/DECISIONS.md`, `docs/PROJECT_STATUS.md` và `docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md`. Không đổi code, API, database, module, runtime hoặc Next task AUTH-002 audit.
- Kiểm tra: `git diff --check`; maintained code unchanged; `ai_workflow.py finish/check`; không chạy application tests vì chỉ hiệu chỉnh phân loại quyết định UX.
- Next action: giữ audit độc lập AUTH-002 slice 2; chỉ lập spec workspace cụ thể khi có task/domain owner.

## CHG-20261029-050 — Chốt mô hình giao diện chung và workspace theo phòng ban

- Ngày: 29/10/2026 (Asia/Saigon). Người dùng xác nhận: một nền giao diện/common shell cho toàn hệ thống; mỗi phòng ban có workspace, menu, dashboard, trường dữ liệu và nút thao tác khác nhau theo vai trò và quyền.
- Ghi quyết định **DEC-023**: một frontend/common shell dùng chung; trải nghiệm phòng ban/vai trò thay đổi theo quyền. Shared detail, capability/scope/state DTO và `allowed_actions` là hướng triển khai đề xuất cần đặc tả theo domain, không phải danh mục đã mở. Không tạo frontend/addon riêng lặp lại theo phòng ban; ẩn nút chỉ là UX.
- Cập nhật [TP_PLATFORM_SOURCE_STRUCTURE.md](architecture/TP_PLATFORM_SOURCE_STRUCTURE.md) và `PROJECT_STATUS.md`. Không sửa application code, OpenAPI, database, module hoặc runtime; chưa mở workspace nghiệp vụ mới.
- Kiểm tra: `git diff --check`; `ai_workflow.py finish/check`; không chạy application tests vì lượt này chỉ ghi quyết định kiến trúc.
- Next action: giữ audit độc lập AUTH-002 slice 2; khi xây UI workspace phải lập đặc tả từng workspace, route, field policy, capability, scope và test trước khi giao Claude code.

## CHG-20261029-049 — Phân tích chọn lọc Excel ERP tham khảo

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, rà soát read-only toàn bộ Excel trong thư mục ERP để chọn kiến thức áp dụng cho TANPHAT ONE.
- Kiểm tra 8 workbook có giá trị nghiệp vụ: quỹ/ngân hàng, dư nợ vay, dự kiến thu–chi, Master tổng hợp, PKH/DA Temp, công trình dở dang và mẫu kế toán lịch sử. Loại khỏi nội dung đọc 3 file danh sách/tài khoản dùng thử và file khóa; không lưu raw values, credential, PII hoặc số tiền thật.
- Tạo [TP_EXCEL_REFERENCE_ANALYSIS.md](architecture/TP_EXCEL_REFERENCE_ANALYSIS.md) và manifest provenance ngoài Git tại `.local/excel_reference_review/`. Kết luận chính: tách production–acceptance–invoice–cash; actual–forecast–obligation; facility/drawdown/repayment/allocation; snapshot/as-of; staging/provenance; reconcile; append-only correction/audit; parent–child subcontractor.
- XL02 có external links và cached `#REF!`; XL08 chỉ đọc được cached structure; không coi formula/tổng workbook là authoritative. Không chạy macro, refresh link, recalculation, import Excel hoặc mở module Finance/Import/Data Lake.
- Phát hiện source drift: XL05/PKH hiện hash `e34052d2986f…`, trong khi registry BIZ-001 dùng `4ee0ff275058…`. Chỉ các bằng chứng phụ thuộc trực tiếp S03 chuyển thành `legacy/pending re-baseline`; không vô hiệu hóa S01/S02/S04/S05 hoặc các DEC đã xác nhận. Cần re-hash và đối chiếu cấu trúc XL05 trước khi tái xác nhận.
- Kiểm tra: inventory NAS, manifest/hash, review độc lập XL01–XL08, `git diff --check`; không chạy application tests vì chỉ bổ sung tài liệu tham khảo. Checker `finish/check` sẽ ghi handoff cho batch này.
- Next action: giữ nguyên audit độc lập AUTH-002 slice 2; khi mở Finance/Import phải có owner, mapping, policy, evidence và decision riêng.

## CHG-20261029-048 — Bóc tách chi tiết màn hình, biểu mẫu và quy tắc nghiệp vụ 16 tài liệu IMIS2

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu trực tiếp của người dùng ("phải đọc từng trang", "viết thành tài liệu đi"), bóc tách chuyên sâu toàn bộ 16 tài liệu HDSD IMIS2 Web/Mobile năm 2021 của EVN/EVNICT thành sổ tay đặc tả tham chiếu chi tiết.
- Tạo [TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md](architecture/TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md): bóc tách chi tiết từng màn hình (screens), biểu mẫu (forms), danh mục trường dữ liệu (fields), quy trình từng bước (Step-by-step) và các quy tắc kiểm tra ràng buộc (validation rules / edge cases).
- Bổ sung chi tiết: cấu hình phân cấp context mobile (IMISONSITE), form nhật ký thi công điện tử (ca, thời tiết, HSE, ảnh bắt buộc tọa độ GPS/thời gian thực, Sim CA), quy trình nghiệm thu 2 tầng (kiểm tra hồ sơ -> kiểm tra hiện trường/khối lượng thực đo -> ký số), quy tắc gói thầu phân lô/chỉ định thầu/tự thực hiện, hợp đồng đa tiền tệ, bảo lãnh ngân hàng, phụ lục/phạt hợp đồng, luồng thẩm định thiết kế 3 bên Submittal -> Review -> Approval, 4 chuyên mục khảo sát địa chất (khoan, hố đào, địa vật lý, hầm), phiếu giá thanh toán Phụ lục 03a và khóa cứng sau giải ngân, thuật toán chấm điểm nhà thầu 3 cấp có chặn trần điểm trừ, và kho dữ liệu nhà thầu/liên danh.
- Tổng hợp bản đồ ánh xạ chi tiết các thực thể dữ liệu và quy tắc nghiệp vụ vào 9 phân hệ của TANPHAT ONE (TP Survey, TP Design, TP Contracts, TP Finance/STL-001, TP Documents, TP Tasks/TVGS Mobile, TP Dashboard/Partner Rating).
- Cập nhật liên kết trong docs/architecture/README.md và docs/architecture/TP_IMIS2_REFERENCE_ANALYSIS.md.
- Tuyệt đối tuân thủ nguyên tắc an toàn: Không sửa application code, OpenAPI, database, runtime hoặc cấu hình dev/test; không mở module rỗng; tài liệu đóng vai trò tham chiếu thiết kế cho roadmap tương lai.
- Kiểm tra: git diff --check, validator liên kết/bảng, checker start/finish/check; không chạy application tests vì chỉ bổ sung tài liệu kiến trúc.
- Next action: giữ nguyên task hiện hành trong PROJECT_STATUS.md (audit AUTH-002 slice 2); khi triển khai phân hệ mới sẽ sử dụng đặc tả tham chiếu này làm đầu vào thiết kế.

## CHG-20261029-047 — Hiệu chỉnh phản biện và provenance cho phân tích IMIS2

- Ngày: 29/10/2026 (Asia/Saigon). Phản biện độc lập bản phân tích CHG-046 bằng hash nguồn, text extraction và locator của đủ 16 manual; xác nhận 16/16 SHA-256 khớp nguồn, 250.023 ký tự trích xuất và 974 media được kiểm kê (ảnh chưa được coi là bằng chứng API/quyền).
- Sửa các điểm có thể gây hiểu nhầm: `tp.project.grant` tách khỏi `tp_contract`; Bid chỉ chứng minh hồ sơ/kết quả lựa chọn, không tự có scoring/authority; giá tham khảo 13 không tự có currency/source/effective semantics; appendix/penalty/revision/audit là thiết kế TP; `account.move` là bridge đích có điều kiện, chưa phải Finance runtime.
- Đổi sơ đồ từ chuỗi bắt buộc thành bản đồ node/branch/parallel/iterative; bổ sung case direct award, nhiều đợt nghiệm thu, tạm ứng trước nghiệm thu theo điều khoản, handover/closeout độc lập với cash; thêm negative cases Bid và bộ khoảng trống/ca thiết kế cho TP.
- Đổi bảng hướng đi thành `Candidate / proposed`, giữ `DEFER` của Data Lake là recommendation chưa phải DEC, không thay đổi Next task AUTH-002 audit hoặc roadmap/master plan. Bổ sung chỉ mục SHA-12/locator để AI sau tìm lại nguồn; không đưa UNC, file gốc, dữ liệu thật hoặc credential vào Git.
- Không sửa application code, OpenAPI, database, runtime, module hoặc quyết định business; không import dữ liệu EVN và không mở Request/Bid/Survey/Design/Documents/mobile/Finance bridge/Data Lake.
- Kiểm tra: đối chiếu source/hash/extraction, phản biện 3 nhóm manual độc lập, `git diff --check`, checker `start/finish/check`; không chạy application tests vì đây là hiệu chỉnh tài liệu tham khảo.
- Next action: giữ task hiện hành trong `PROJECT_STATUS.md`; khi mở miền mới phải lập task/owner/decision/acceptance riêng và không dùng manual EVN làm cổng code.

## CHG-20261029-046 — Phân tích chọn lọc 16 manual IMIS2 EVN

- Ngày: 29/10/2026 (Asia/Saigon). Đọc toàn bộ 16 tài liệu DOCX IMIS2 Web/Mobile năm 2021 trong thư mục tham khảo do người dùng cung cấp; đối chiếu manifest SHA-256 và bản text extraction ngoài Git tại `.local/imis2_review/`.
- Tạo [TP_IMIS2_REFERENCE_ANALYSIS.md](architecture/TP_IMIS2_REFERENCE_ANALYSIS.md): phân loại từng manual thành tiếp thu/điều chỉnh/chỉ tham khảo/không áp dụng; rút ra project scope, work breakdown, bid package/lot, contract revision, evidence/version, diary/issue/acceptance, documents, handover, closeout và contractor master.
- Giữ ranh giới EVN–Tấn Phát: không copy cơ cấu, hạn mức, quyền, chữ ký, giải ngân, scoring 100 điểm hoặc thao tác xóa; “Kho dữ liệu nhà thầu” không phải Data Lake; BASE approval, ký, hiệu lực, nghiệm thu, thanh toán và Accounting vẫn tách.
- Không sửa application code, OpenAPI, database hoặc runtime; không import dữ liệu EVN và không mở module/connector/mobile/Data Lake. Cập nhật `TP_REFERENCE_RESEARCH_AND_HANDOFF.md`, architecture README và status để AI phiên sau tìm được kết quả.
- Kiểm tra: đọc/extract 16 manual, provenance/hash manifest, link/table review, `git diff --check`; không chạy application test vì batch chỉ nghiên cứu tài liệu.
- Next action: giữ nguyên task hiện hành trong `PROJECT_STATUS.md` (audit AUTH-002 slice 2); các miền IMIS2 chỉ mở qua task/owner/acceptance riêng.

## CHG-20261029-045 — Đối chiếu sơ đồ kiến trúc TP.ONE với nền TANPHAT ONE

- Ngày: 29/10/2026 (Asia/Saigon). Đọc và render kiểm tra `TP_ONE_So_do_kien_truc.pdf` (1 trang A4, provenance `REF-ARCH-PDF-20261029`) do người dùng cung cấp.
- Ghi vào `TP_REFERENCE_RESEARCH_AND_HANDOFF.md`: sơ đồ là target architecture L1 Frontend → API → L2 Odoo 20 → CSDL; Projects là trục liên kết; “Căn cứ” là nguồn xác định scope/quyền/workflow; QL91 chỉ là ví dụ.
- Đối chiếu nhãn PDF với TP Dashboard/Projects/Survey/Design/Contracts/Tasks/HR/Finance/Documents và các miền Bid/Request/AI; phân biệt target scope với module/runtime đã có. Ghi rõ mobile native, cardinality, actor/transition, workflow engine, API write/sync và mapping addon chưa được chốt từ hình.
- Không đổi application code, OpenAPI, database, runtime hoặc quyết định BASE/Request mới. Không coi hình là lệnh cài module; BASE vẫn official approval, Request/AI vẫn có boundary và gate riêng.
- Kiểm tra: `pdfinfo`, text extraction, render PNG, đọc trực quan; link/bảng/provenance và `git diff --check`; không chạy application test vì batch tài liệu-only.
- Next action: giữ Next task hiện hành trong `PROJECT_STATUS.md`; khi mở miền Bid/Request/AI hoặc mobile phải lập task/owner/acceptance riêng.

## CHG-20261029-044 — Lưu riêng kiến thức nghiệp vụ Request trên BASE

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, thêm `docs/architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md`: nguồn `REF-BASE-REQUEST-20261029`, group/tab/form đã quan sát, actor chưa xác minh, vòng đời Proposed-TP, return/reject/disputed, reference/evidence/version và các gap trước connector.
- Tách rõ UI BASE khỏi state/API Odoo; không suy quyền từ người duyệt/follower, không biến approved thành signed/effective/paid, không coi nghiệp vụ kế toán TP đã nghiệm thu. Workflow chi tiết vẫn tham chiếu BIZ-002 H/I; không chốt owner/hạn mức hoặc quyết định nghiệp vụ mới.
- Liên kết từ AGENTS, sổ nghiên cứu, architecture README, quy trình điều phối và status. Giữ Next task hiện hành. Chỉ sửa Markdown, không sửa application code, database/runtime, credential, commit/push.
- Checkpoint CHG-043 của phiên khác được giữ nguyên đến khi tự đóng; tài liệu riêng được soạn trước, `ai_workflow.py start` chạy trước các sửa đổi bàn giao dùng chung sau đó. Không finish thay code batch khác.
- Kiểm tra: đối chiếu nguồn BIZ-002 H/I và DEC-013; kiểm liên kết/bảng/nội dung; `git diff --check`; so snapshot maintained code với checkpoint của batch này. Không chạy application tests vì chỉ bổ sung tài liệu; kết quả `finish/check` ghi trong workflow state.

## CHG-20261029-043 — Cài hr_timesheet, hr_expense, project_hr_expense trên test và dev; thêm vào MODULES

- Ngày: 29/10/2026 (Asia/Saigon). Theo lựa chọn người dùng "Timesheet + chi phí" sau khi rà sơ đồ kiến trúc TP.ONE. Backup trước cài `.local/module-install-20261029-160204/` (ngoài Git, 408 checksum, verify đạt, `REPORT.md`).
- Cài `hr_timesheet`, `hr_expense`, `project_hr_expense` (+ auto `spreadsheet_dashboard_hr_timesheet`) không demo trên `tp_tanphat_test` (85 module) rồi `tp_tanphat_dev` (87 module); không ERROR/Traceback. Odoo tự tạo tài khoản phân tích cho từng project, project "Internal" không `tp_managed` và 6 sản phẩm chi phí; giá trị dữ liệu TP không đổi (chỉ `write_date`).
- `scripts/dev.py`: `STANDARD_MODULES = 'crm,account,hr_timesheet,hr_expense,project_hr_expense'`. Không sửa `odoo/`, `addons/`, `custom_addons/`, `frontend/`, `contracts/`; không commit.
- Kiểm tra: Odoo tests trên test 0 failed/0 error of 79 (trước và sau đổi MODULES); `dev.py smoke` PASS; logout/session lạ 401; API project không lộ "Internal"; `ruff check scripts/dev.py` đạt.

## CHG-20261029-042 — Lưu sổ kiến thức tham khảo A1/Base và bàn giao điều phối

- Ngày: 29/10/2026 (Asia/Saigon). Tạo `docs/architecture/TP_REFERENCE_RESEARCH_AND_HANDOFF.md` để phiên AI mới đọc lại được nguồn A1 Consulting, quan sát Base Request, giới hạn bằng chứng, mapping với kiến trúc TANPHAT ONE và các giả thuyết Request/Bid.
- Phân loại rõ user-confirmed/observed/runtime-evidence/proposed/open; không biến bài marketing, ảnh/UI Base hoặc tên module thành quy chế, API, hạn mức hay quyết định schema. Ghi rõ BASE vẫn là authority theo DEC-013, Data Platform vẫn là recommendation `DEFER`, và module chuẩn CRM/Account đã cài theo CHG-039/041 nhưng workflow TP chưa mở.
- Thêm liên kết trong `docs/architecture/README.md`, `docs/AI_COORDINATION_WORKFLOW.md` và status. Không sửa application code, OpenAPI, database, runtime, credential hoặc quyết định nghiệp vụ mới.
- Kiểm tra: đọc-only source/status trước khi ghi; kiểm tra checkpoint đã đóng; sẽ chạy `git diff --check` và `ai_workflow.py finish/check`. Không chạy application test vì batch chỉ thêm tài liệu.
- Next action: audit độc lập AUTH-002 slice 2 CHG-038 theo `PROJECT_STATUS.md`; đọc sổ này khi task chạm A1/Base/Request/Bid/Data Platform.

## CHG-20261029-041 — Cài crm, account trên dev (chart VN) và thêm vào MODULES

- Ngày: 29/10/2026 (Asia/Saigon). Theo lựa chọn người dùng chấp nhận `l10n_vn`. Backup `.local/module-install-20261029-154126/` (327 checksum, verify đạt; ngoài Git). Dev: `--init crm,account --without-demo=True --stop-after-init` exit 0, 28 module mới (26 như test + `l10n_vn`, `account_qr_code_emv`), không ERROR; TP không đổi version; không sale/purchase*/`tp_web_login`/Request/Bid.
- Dữ liệu: chart `vn` tự nạp (301 tài khoản, 31 thuế, 8 journal), công ty giữ VN/VND; 0 chứng từ/thanh toán/lead; không bảng tp_*/project_*/hr_* nào đổi; không nhập dữ liệu thật.
- `scripts/dev.py`: `MODULES` = `STANDARD_MODULES` `crm,account` + `CUSTOM_MODULES` sáu module TP, ghi chú chart và giới hạn setup mới (generic chart do cài trước khi seed VN).
- Kiểm tra: `dev.py smoke` PASS; logout CSRF → `/me` 401, session lạ 401; log 0 ERROR; Vite `/work/` 200; `ruff check scripts/dev.py` đạt; `dev.py test` với MODULES mới 0 failed/0 error of 79 tests. Không ghi TECHNICAL_ACCEPTED; không commit.

## CHG-20261029-040 — Upgrade TP trên dev lên 20.0.1.1.0

- Ngày: 29/10/2026 (Asia/Saigon). Vận hành theo lựa chọn người dùng sau CHG-039; không đổi source. Backup `.local/module-install-20261029-153658/` (327 checksum, verify đạt; ngoài Git) trước khi chạy `scripts/dev.py upgrade` với Odoo đã dừng.
- Kết quả: tp_project/tp_contract/tp_api/tp_planning_api 20.0.1.0.0 → 20.0.1.1.0; 5 bảng và 3 cột CTR-002a có trên dev, khớp test; post-migrate gán phòng ban cho HD-DEV-001/003, HD-DEV-002 giữ NULL (project chưa có phòng chủ trì). Không module mới; `crm`/`account`/`l10n_vn` vẫn uninstalled. Không bảng tp_*/project_*/hr_* nào đổi trên cột cũ; `seed_dev` ghi lại mật khẩu dev từ dev-secrets (2 mail thông báo `exception`, không có mail server).
- Kiểm tra: upgrade exit 0, không ERROR/Traceback; `dev.py start` + `dev.py smoke` PASS (login, `/me` 401, project/contract scope, grant tài chính); log sau khởi động 0 ERROR, `/api/v1/contracts` 200; Vite `/work/` 200.
- Next: người dùng quyết định hệ thống tài khoản VN trước khi cài `crm`/`account` trên dev; MODULES chưa đổi. Không ghi TECHNICAL_ACCEPTED.

## CHG-20261029-039 — Cài module chuẩn Odoo crm, account trên test; dev BLOCKED

- Ngày: 29/10/2026 (Asia/Saigon). Vận hành theo yêu cầu trực tiếp người dùng; không đổi `odoo/`, `addons/`, `custom_addons/`, `frontend/`, `contracts/`, `scripts/dev.py`. Backup `.local/module-install-20261029-151435/` (dump/filestore/conf/revision/diff/module state/fingerprint, 257 checksum, verify đạt; ngoài Git).
- Test `tp_tanphat_test`: `--init crm,account --without-demo=True --stop-after-init` exit 0, không ERROR/Traceback; crm 20.0.1.9, account 20.0.1.6 + 24 module phụ thuộc/auto-install chuẩn; TP không upgrade; không `l10n_vn`/sale/purchase*/`tp_web_login`/Request/Bid. Odoo tự nạp `generic_coa` (country test → US). `dev.py test` 0 failed/0 error of 79 tests; smoke anonymous `/web/login` 200, `/api/v1/me|projects|contracts` 401 JSON.
- Dev `tp_tanphat_dev`: BLOCKED, không cài — schema TP dev 20.0.1.0.0 thấp hơn source 20.0.1.1.0 (install sẽ tạo một phần schema ngoài migration) và công ty VN sẽ kéo `l10n_vn` tự tạo tài khoản/thuế/journal. DB dev không đổi (0/322 bảng); Odoo dev khởi động lại, smoke đạt login/me/projects, `/api/v1/contracts` 500 có sẵn do chưa upgrade.
- Next: người dùng quyết định upgrade dev TP và chart VN trước khi cài dev; chưa thêm module vào MODULES. Không ghi TECHNICAL_ACCEPTED.

## CHG-20261029-038 — AUTH-002 slice 2: handoff 2FA và trang xác thực native

- Ngày: 29/10/2026 (Asia/Saigon). Task AUTH-002 slice 2, lane F, scope AUTH-002-SPEC v0.6; gate đầu vào đạt, status `IMPLEMENTED_PENDING_AUDIT`. Thêm `custom_addons/tp_web_login/**` (QWeb/CSS bundle riêng/data noupdate D6-a/HttpCase/README), đổi `session.tsx`, `LoginPage.tsx`, `login.spec.ts`, thêm `auth002-live.spec.ts`; cập nhật status/roadmap/đặc tả. Font hệ thống để hỗ trợ tiếng Việt/offline, không CDN. Không model/controller/API/route mới, không sửa core hoặc D1–D6.
- Kết quả: React handoff `/web/login/totp?redirect=<path /work/>` cùng origin, giữ deep link/query/hash; link passkey vẫn `/web/login`. Native dùng monogram TANPHAT ONE, màu đã chốt, chữ Việt cố định và lỗi che chuỗi server; Hủy POST/CSRF về `/work/`. D6-a đặt invitation_scope=b2b/reset_password=False khi cài trên verify DB; giữ captcha/passkey/CSRF/cooldown/session native và Manage Databases theo list_db.
- Test thực chạy: typecheck PASS; Vitest 4 file/29 PASS; build `VITE_ODOO_DATABASE=tp_tanphat_dev` PASS; Ruff/compileall/XML/E2E TypeScript compile PASS; mock `login.spec.ts` 5/5 PASS (T07); Odoo HttpCase T10 summary 3 test/0 failed/0 errors/0 skip trên verify DB; live opt-in T05/T08/T09/T12 3/3 PASS/0 skip, browser en-US. Đã sửa ParseError xpath class động rồi rerun; sửa T07 cần mở details, sửa false positive cấm mọi storage; correction cuối chuyển CSS static sang bundle `/web/assets` để đi qua proxy Vite sẵn có, T10/live chạy lại sau correction. Không coi exit code hoặc collection/skip là test live đạt.
- Môi trường: `tp_tanphat_auth002_verify`, origin `http://127.0.0.1:18099`, PG55432, fixture `auth002.verify.*`, helper `.local/auth002-verify/` ngoài Git vì C01 chưa bàn giao. Dev Odoo18069/PG55432/Vite4173 có sẵn giữ nguyên; test Vite4174 và Odoo18099 đã dừng sau kiểm, không dừng process không sở hữu, giữ verify DB. Dev addon chưa cài và auth config digest không đổi; không cài/upgrade/seed dev/test chuẩn, không commit/push/deploy.
- Giới hạn/next: passkey ceremony và nhớ thiết bị chưa kiểm bằng trình duyệt thật; header trang mã/HTTPS/proxy/list_db/staging thuộc C06, addon chưa vào dev. Phiên điều phối audit độc lập CHG-038; không tự ghi TECHNICAL_ACCEPTED/business acceptance/pilot. Workflow finish/check ghi ở snapshot bàn giao, không thay test nghiệp vụ.

## CHG-20261029-037 — AUTH-002 slice 1: tiếp quản audit, sửa mutation 401 và chốt kiểm chứng

- Phạm vi: theo yêu cầu trực tiếp tiếp quản phần Claude, phát hiện và sửa P2 của L02: query 401 đã về login nhưng mutation 401 chỉ hiện lỗi trong form. Implementation subagent sửa `frontend/src/app/providers.tsx` dùng handler 401 chung cho QueryCache/MutationCache và thêm `frontend/tests/e2e/session-mutation-401.spec.ts`; phiên chính review patch và chạy kiểm tra độc lập. Không backend/OpenAPI/state/capability mới; không setup/upgrade/seed, không cài addon lên dev, không commit/push. Mô hình điều phối dài hạn giữ nguyên.
- Kiểm tra: regression mutation 401 đã fail trước sửa; sau sửa, phiên chính chạy typecheck/build đạt, Vitest 4 file/29 test đạt, mock E2E 16/16 đạt (POST/PATCH 401, deep link query/hash, đăng nhập lại refetch dữ liệu mới, không tự gửi lại mutation; 403/409/422/503 giữ workspace; login-notices và contract workflow). Hồi quy live login/projects sau correction 8/8 đạt; ca live expiry notice local 1/1 đạt (cookie bị xóa → projects 401 → câu expired nguyên văn, xóa card, giữ deep link, storage trống → đăng nhập lại). Runtime dev ban đầu và cuối cùng đều dừng; chỉ start/stop để kiểm, không upgrade/seed. Kiểm snapshot chỉ hai file code nói trên đổi trong batch; validator tài liệu, `git diff --check`, workflow finish/check ghi ở handoff.
- Workflow/handoff: cập nhật status, đặc tả mục 10.5/10.6, roadmap, architecture README, master plan (nhánh F AUTH-002 và diễn đạt tracked đúng thực tế), quy trình kiểm frontend bắt cả query/mutation 401. R5 đã có live evidence; R1–R4 giữ giới hạn cũ. Slice 1 `TECHNICAL_ACCEPTED` phạm vi test; chưa business acceptance/pilot.
- Next: giao [prompt AUTH-002 slice 2](prompts/CLAUDE_AUTH002_S2_NATIVE_LOGIN.md) khi người dùng mở batch đó; slice 2 chưa code, cài addon chỉ trên database test cô lập.

## CHG-20261029-036 — AUTH-002 slice 1: phiên điều phối review, TECHNICAL_ACCEPTED phạm vi test

- Phạm vi: phiên điều phối đọc diff CHG-035 theo prompt slice 1 và đặc tả v0.6, chạy lại test độc lập. Kết luận slice 1 `TECHNICAL_ACCEPTED` cho phạm vi test (mock và runtime dev, không người dùng thật), không có finding P1/P2; năm ghi nhận P3 R1–R5 ở mục 10.4 đặc tả (L03 nối `navigate` với `history.replaceState`; thông báo `role="status"` lúc mount; Caps Lock chỉ kiểm sự kiện tổng hợp; L01 dựa chuỗi mặc định `Access Denied`; `expired` chỉ kiểm mock). Cập nhật đặc tả (dòng trạng thái, mục 10.4, mục 14), roadmap, architecture README, status. Không sửa application code, DECISIONS, `custom_addons/` hoặc OpenAPI; không setup/upgrade/seed; không commit/push. Chưa phải business acceptance hay pilot.
- Kiểm tra: typecheck đạt; Vitest 4 file/29 test đạt; build `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; `login-notices.spec.ts` 7/7 khi không có Odoo; runtime dev ban đầu dừng, `dev.ps1 start` rồi `login-notices` + `login.spec.ts` + `projects.spec.ts` 15/15 đạt, `dev.ps1 stop`, `status` xác nhận đã dừng; validator tài liệu, `git diff --check`, workflow finish/check.
- Next: người dùng giao prompt slice 2 cho một phiên Claude.

## CHG-20261029-035 — AUTH-002 slice 1: React báo khóa tạm, hết phiên, đã đăng xuất và chi tiết nhỏ

- Phạm vi: phiên Claude thực thi prompt slice 1 (đặc tả v0.6). L01 `client.ts` phân loại `AccessDenied` theo V-B (chỉ `["Access Denied"]` là `credentials`, còn lại `cooldown`) với câu chữ cố định; L02 cờ hết phiên trong bộ nhớ (`features/auth/sessionNotice.ts`, nối QueryCache ở `providers.tsx`); L03 đăng xuất gửi `redirect=/work/?signed_out=1`, `LoginPage` hiện thông báo rồi xóa tham số không thêm mục history; L05 Caps Lock qua `aria-live`; L06 focus ô tên đăng nhập; L07 nhãn ngôn ngữ chữ tĩnh; L08 cho `cooldown`, `credentials`, `expired`, `signed_out`, `caps_lock`. Handoff 2FA giữ `/web/login` và câu chữ cũ. Test mới `sessionNotice.test.ts`, `login-notices.spec.ts`; T01 trong `client.test.ts`; ca MFA `login.spec.ts` kiểm thêm `/web/login` và câu chữ cũ; `projects.spec.ts` kiểm thông báo đăng xuất và URL `/work/`. Bàn giao ở mục 10.3 đặc tả. Không sửa `custom_addons/`, OpenAPI, `odoo/`/`addons/`; không setup/upgrade/seed; không commit/push.
- Kiểm tra: typecheck đạt; Vitest 29/29; build `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; mock E2E 7/7; T11 trên runtime dev (ban đầu dừng, start rồi stop) 15/15 (`login-notices`, `login.spec.ts`, `projects.spec.ts`); `git diff --check`; workflow finish/check.
- Next: phiên điều phối review slice 1 (`IMPLEMENTED_PENDING_AUDIT` → `TECHNICAL_ACCEPTED` hoặc `NEEDS_FIX`) rồi mới giao slice 2.

## CHG-20261029-034 — AUTH-002 v0.6: chuyển cả hai slice sang READY_FOR_TEST_CODE, soạn prompt

- Phạm vi: người dùng trả lời “Move both slices”. Đặc tả AUTH-002 lên v0.6: slice 1 và slice 2 ở `READY_FOR_TEST_CODE`; mục 10.2 làm rõ thứ tự (slice 1 trước), câu chữ `mfa_*` đi cùng L04 ở slice 2, L04 chỉ đổi link handoff (link passkey F8 giữ `/web/login`), T11 cần runtime dev cho `projects.spec.ts`, T10 chạy trên database test cô lập và không thêm addon vào `dev.MODULES`. Tạo prompt `docs/prompts/CLAUDE_AUTH002_S1_REACT_LOGIN.md` và `CLAUDE_AUTH002_S2_NATIVE_LOGIN.md`. Cập nhật roadmap, architecture README, status. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng giao prompt slice 1; sau bàn giao, phiên điều phối review rồi giao prompt slice 2.

## CHG-20261029-033 — AUTH-002 v0.5: người dùng duyệt câu chữ 6.1

- Phạm vi: người dùng trả lời “Approve 6.1”. Đặc tả AUTH-002 lên v0.5: `totp_placeholder` và `totp_error` mục 6.1 chuyển thành câu chữ đã duyệt; kế hoạch slice 2 bỏ điều kiện chờ duyệt; mục 10.1 đối chiếu cổng Ready for Code cho cả hai slice, không còn quyết định mở. Cập nhật roadmap, architecture README, status. Không ghi chuyển `READY_FOR_TEST_CODE`; không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng chọn chuyển slice 1, slice 2 hoặc cả hai sang `READY_FOR_TEST_CODE`.

## CHG-20261029-032 — AUTH-002 v0.4: người dùng chọn D6-a

- Phạm vi: người dùng chọn “Disable both (D6-a)”. Đặc tả AUTH-002 lên v0.4: D6 chuyển vào bảng đã chốt; mục 3.1 ghi cách áp dụng (dữ liệu `noupdate` của `tp_web_login` đặt `auth_signup.invitation_scope = b2b`, `auth_signup.reset_password = False`; không gỡ module, không xóa link bằng template; dev/pilot/production theo checklist C06). Cập nhật L12, T10, kế hoạch slice 2, rollback, rủi ro G7, truy vết, roadmap, architecture README, status. Câu chữ 6.1 vẫn `proposed`. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: đối chiếu tĩnh `auth_signup` data/controller/template; validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng duyệt câu chữ 6.1 và chọn có chuyển slice 1 sang `READY_FOR_TEST_CODE` không.

## CHG-20261029-031 — AUTH-002 v0.3: kết quả V-A…V-C trên database test cô lập

- Phạm vi: theo cho phép của người dùng, chạy Odoo trên database mới `tp_tanphat_auth002_verify` (cổng 18099, `dbfilter` riêng, actor fixture tổng hợp; không đụng `tp_tanphat_dev`) bằng helper `.local/auth002-verify/` ngoài Git. Kết quả: V-A đạt (mở thẳng `/web/login/totp` sau authenticate, không nhập lại mật khẩu); V-B phân biệt khóa tạm với sai mật khẩu qua `AccessDenied.arguments`; V-C chỉ `en_US`, không `website`/`auth_oauth`, `auth_signup` mở đăng ký/đặt lại mật khẩu. Đặc tả lên v0.3: mục 8.2 kết quả, quy tắc L01, L04 đổi link, L10 chữ tiếng Việt cố định, L11/L12 theo kết quả, thêm G7, D6 (`decision-needed`), câu chữ 6.1 (`proposed`), đối chiếu cổng slice 1 (10.1), rủi ro header khung trang mã và `dbfilter`. Cập nhật roadmap, architecture README, status. Không sửa application code hoặc DECISIONS; không commit/push.
- Kiểm tra: request HTTP thật trên database test (report không chứa secret); dừng Odoo và PostgreSQL, `server.log` không có `ERROR`; validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng chọn D6, duyệt câu chữ 6.1 và chọn có chuyển slice 1 sang `READY_FOR_TEST_CODE` không.

## CHG-20261029-030 — AUTH-002 v0.2: người dùng chốt D1–D5 theo mặc định

- Phạm vi: người dùng trả lời “Chốt mặc định”. Đặc tả AUTH-002 lên v0.2: D1 (a) liên hệ quản trị viên, D2 (a) giữ nhớ thiết bị 2FA của Odoo và chỉ Việt hóa, D3 (a) monogram hiện có, D4 (a) nút bấm sang 2FA nên DEC-012 giữ nguyên, D5 bảng câu chữ mục 6 nguyên văn; L07 chốt chữ tĩnh. Cập nhật roadmap, architecture README, status. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng có file đặc tả, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: V-A…V-C trên database test cô lập khi người dùng cho phép runtime test → `READY_FOR_TEST_CODE`.

## CHG-20261029-029 — Đặc tả AUTH-002 hoàn thiện luồng đăng nhập (spec-only)

- Phạm vi: thêm `docs/architecture/TP_AUTH002_LOGIN_SPEC.md` v0.1 theo yêu cầu người dùng làm chỉn chu trang đăng nhập; thêm dòng AUTH-002 vào roadmap, link ở architecture README, cập nhật status. Không sửa application code, OpenAPI, test, DECISIONS hoặc runtime; không commit/push.
- Nội dung: sáu khoảng trống `observed-static` G1–G6 (2FA nhập mật khẩu hai lần, trang native thương hiệu Odoo/tiếng Anh, hủy 2FA rơi ra Odoo, khóa tạm báo nhầm sai mật khẩu, không thông báo hết phiên/đăng xuất, Caps Lock/focus/nhãn ngôn ngữ); yêu cầu L01–L12 (React + addon template đề xuất `tp_web_login`); quyết định D1–D5; kiểm trước V-A…V-C; ca nghiệm thu T01–T12; ràng buộc giữ DEC-012.
- Kiểm tra: validator link/anchor/bảng có thêm file mới, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code; chưa start Odoo hay thử tài khoản 2FA.
- Next: người dùng chọn D1–D5 → v0.2 → V-A…V-C trên database test cô lập → `READY_FOR_TEST_CODE` và prompt triển khai.

## CHG-20261029-028 — Sửa liên kết bàn giao re-audit DP-001

- Phạm vi: hai link heading trong `PROJECT_STATUS.md` trỏ sai vì heading audit có hậu tố CHG-027; đổi sang link file. Không đổi discovery, application code, verdict hoặc các cổng.
- Kiểm tra: validator sau CHG-027 phát hiện đúng hai anchor thiếu; đã sửa và chạy lại validator UTF-8, `git diff --check`, workflow finish/check. Kết quả cuối ghi ở handoff CHG-028; không coi checker hash là test link.
- Next: giữ `TECHNICAL_ACCEPTED` cho DP-DISC-v1.1/spec-only; C01 là code batch độc lập khi người dùng giao; không mở Data Lake hay dữ liệu thật.

## CHG-20261029-027 — Audit lại DP-001 correction v1.1

- Phạm vi: audit độc lập bản DP-DISC-v1.1 do Claude bàn giao CHG-026; chỉ ghi verdict vào status/roadmap/báo cáo audit, không sửa discovery, application code, OpenAPI, frontend, scripts, runtime hoặc database; không commit/push.
- Kết luận: `TECHNICAL_ACCEPTED` cho discovery/spec-only, `DESIGN_COMPLETE` đạt ở phạm vi tài liệu chuẩn bị. Bốn finding DP-F01…DP-F04 đã được xử lý: snapshot consistency, ma trận version/hash, source/policy tax basis tách riêng, retry/observation/payload và materialization version. Không còn P1/P2 trong correction. P3 không chặn: RFC implementation cần làm rõ response/attempt khác accepted observation và retry cùng batch khác snapshot mới ở V34.
- Kiểm tra thực chạy: đọc source `_amount_summary`, `_tp_submission_problems`, version guard; kiểm 34 ca V01–V34 duy nhất/đủ dải và đều `NOT_RUN`; validator mở rộng trước ghi audit đạt 28 file, 213 link, 49 anchor, 156 bảng, 0 lỗi/0 cảnh báo; exact snapshot 127 file khớp before/after correction và state CHG-026; `git diff --check` đạt. Kiểm cuối sau ghi audit được báo trong handoff `finish/check`.
- Gate: recommendation `DEFER` vẫn là đề xuất, không là DEC; PoC lake `NOT_APPLICABLE`, O0 UC-01 `NOT_READY`, `REAL_DATA_APPROVAL=BLOCKED`. Không chạy application tests vì spec-only, không start Odoo/PostgreSQL, không đọc hồ sơ thật.
- Next: không cần correction mới cho bốn finding cũ. C01/FND-002 là batch code độc lập có prompt sẵn; nhánh C17/RPT-001 cần use case/owner/công thức/scope và task riêng. Không mở BASE/ký/hiệu lực/thanh toán/grant người thật.

## CHG-20261029-026 — DP-001 correction DP-DISC-v1.1 (spec-only)

- Phạm vi: sửa `docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md` lên DP-DISC-v1.1 theo prompt correction sau audit CHG-024; cập nhật status/roadmap/changelog. Không sửa application code, OpenAPI, frontend, scripts trong Git, ops/config, schema hoặc database; không start/upgrade/seed Odoo; không đọc database/NAS/Excel/filestore/secrets; không PoC/pipeline/bucket/connector; không sửa DECISIONS, báo cáo audit CHG-024 hay kế hoạch chuẩn bị; không commit/push.
- Mapping finding → mục → ca kiểm chứng (tất cả `NOT_RUN`):
  - DP-F01 → 4.4.1, envelope 4.1, 5.1, 6.4, R05, 9.1 → V19, V21, V22, V23. Phân trang tách khỏi tính nhất quán; API hiện tại tối đa `best_effort`; `consistent_proven` chỉ với export materialized có snapshot token không mang quyền hoặc change log đặc tả đủ; quyền đổi giữa trang thì fail closed.
  - DP-F02 → 4.4.2, DC-02, 4.7, R19 → V14, V24, V25, V26, V30, V31. Ma trận version × hash; cùng version khác hash phải đọc xác minh hoặc quarantine; không quyết theo `ingested_at`/`write_date`/thứ tự response; snapshot có thẩm quyền mới thay hiện trạng trong coverage, giữ observation.
  - DP-F03 → F06, 3.3, 4.3, DC-06, 4.7, R08, Q4/Q13 → V02, V03, V04, V17, V27, V28, V29. Lớp nguồn khớp `_amount_summary` (mọi dòng `unknown` vẫn `confirmed` có value; `mixed_basis` chỉ khi nhiều basis); lớp policy `basis_unknown` là proposed và kiểm riêng.
  - DP-F04 → 4.5.1, envelope, DC-06, 4.7, R20 → V12, V15, V32, V33, V34. Tách retry trong batch, observation bất biến theo snapshot và payload content-addressed; materialization gắn snapshot + schema/transform/formula.
- Kiểm tra thực chạy:
  - Exact snapshot `scripts.ai_workflow.snapshot` trước/sau: 127/127 file, digest `056ae25bced60c72acae70507533e78377d8bd8a9839e0bc194027c05bc392ca` không đổi, 0 file thêm/xóa/đổi; bằng chứng `.local/dp001-correction/before.json`, `after.json`, `code_comparison.json`.
  - Docs validator `.local/ctr002a-verify/docs_validation.py` mở rộng `NAMES` tại runtime qua `.local/dp001-correction/run_docs_validation.py` (thêm discovery, audit CHG-024, prompt correction): PASS 28 file, 213 link nội bộ, 49 anchor, 156 bảng, 0 lỗi, 0 cảnh báo. Validator scratch (UTF-8/BOM, fence, cột bảng, link/anchor) trên discovery/status/roadmap/audit/prompt/changelog: 0 lỗi.
  - `git diff --check` đạt; discovery (untracked) không có trailing whitespace.
  - Không chạy application tests vì spec-only; Odoo/PostgreSQL không được khởi động.
- Giới hạn bằng chứng: artifact 119 file của DP-001 không phải exact checker scope; 117 file giao với scope 127 được chứng minh không đổi từ đầu DP-001; 10 file chỉ có trong checker scope không tái chứng minh được trước DP-001 vì digest CHG-022 không còn lưu, không dựng bằng chứng hồi tố. Checker không hash tự động tài liệu architecture/prompt mới.
- Next: phiên chính audit lại DP-DISC-v1.1; verdict CHG-024 giữ nguyên cho v1. `DEFER` vẫn là đề xuất; lake PoC `NOT_APPLICABLE`; O0 UC-01 chưa mở; `REAL_DATA_APPROVAL` `BLOCKED`; C01 độc lập.
## CHG-20261029-025 — Chốt bằng chứng bàn giao audit DP-001

- Phạm vi: hoàn tất bản ghi kiểm chứng tài liệu/audit/prompt của CHG-024; không sửa code/runtime/database và không đổi verdict `NEEDS_FIX`.
- Kiểm tra thực chạy: validator mở rộng bao gồm discovery, báo cáo audit và prompt correction đạt 28 file, 182 link nội bộ, 149 bảng, 0 lỗi; đối chiếu exact snapshot theo `scripts.ai_workflow.snapshot` trước/sau đạt 127 file, 0 file thêm/xóa/đổi; whitespace hai file mới đạt. Báo cáo local tại `.local/dp001-audit/code_comparison.json`. Không chạy application tests vì spec-only.
- Bàn giao: số 26 là kết quả kiểm bộ tài liệu trước khi thêm audit/prompt, số cuối là 28; sửa tham chiếu keyset ở status thành mục 4.4/R05. Không sửa lịch sử discovery để tự đóng finding; không commit/push.
- Next: Claude sửa DP-F01…DP-F04 bằng prompt correction rồi phiên chính audit lại. C01/FND-002 vẫn độc lập; lake PoC không áp dụng và dữ liệu thật vẫn bị chặn.

## CHG-20261029-024 — Audit DP-001 Data Platform discovery

- Phạm vi: audit độc lập tài liệu `docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md`; không sửa application code, OpenAPI, frontend, schema, runtime hoặc database; không tạo Data Lake/connector/bucket/pipeline.
- Kết quả: recommendation `DEFER` có cơ sở, nhưng `DESIGN_COMPLETE=NEEDS_FIX` vì bốn điểm cần sửa: keyset cursor không tự tạo point-in-time snapshot; chưa có rule same-version/different-hash; diễn giải `tax_basis=unknown` không khớp `_amount_summary`; replay/dedup toàn cục có thể làm mất lịch sử A→B→A và bỏ qua `transform_version`.
- Kiểm tra: `scripts/ai_workflow.py check` đạt; exact maintained-code snapshot theo cùng checker là 127 file và không đổi trong lượt audit; docs validator mở rộng cho discovery đạt 26 file, 175 link nội bộ, 147 bảng, 0 lỗi; `git diff --check` đạt; Odoo/PostgreSQL không chạy.
- Bằng chứng: findings tại mục 4.3–4.5, 6.3, 7 của discovery; source `_amount_summary` tại `custom_addons/tp_contract/models/tp_contract_revision.py` xác nhận hành vi tax basis. Bản DP-001 khai báo snapshot 119 file nên không được dùng làm bằng chứng exact scope; audit đã lưu snapshot 127 file ngoài Git tại `.local/dp001-audit/before.json`.
- Next: giao Claude correction tài liệu chỉ cho bốn finding trên, rồi audit lại trước khi chọn UC-01/C17/RPT-001 hoặc bất kỳ PoC nào. `REAL_DATA_APPROVAL` vẫn `BLOCKED`; không mở runtime Data Lake.

## CHG-20261029-023 — DP-001 Data Platform discovery (spec-only)

- Phạm vi: khảo sát source tĩnh và viết tài liệu thiết kế theo prompt DP-001. Không sửa application code, OpenAPI, frontend, scripts runtime hoặc database. Không đọc dữ liệu thật/NAS/Excel/filestore, không tạo `tp_datalake`, không chọn vendor/cloud, không dựng pipeline/bucket/connector và không chạy PoC.
- Đã thêm `TP_DATA_PLATFORM_DISCOVERY.md`:
  - inventory 20 model/dataset và API/DTO, 9 phát hiện ảnh hưởng thiết kế dữ liệu;
  - 9 nguồn tương lai đánh dấu observed/proposed/unknown;
  - ba use case: UC-01 giá trị hợp đồng áp dụng theo project là ưu tiên **đề xuất**, UC-02 sổ hồ sơ là candidate, UC-03 AI tra cứu bị defer;
  - data contract envelope và DC-01…DC-08, quy tắc null/0/âm/unconfirmed/currency, thời gian/version, tombstone/replay, join J1–J7, lineage/reconcile;
  - ma trận quyền/retention theo lớp dữ liệu và theo kênh;
  - so sánh O0 report trong Odoo, analytics-first và lakehouse-lite; CDC/Kafka/Spark `NOT_EVALUATED`; đánh giá outbox/audit không phải change feed;
  - đặc tả kiểm chứng V01–V20 đều `NOT_RUN`, risk/gap R01–R18 và 5 câu hỏi ưu tiên.
- Recommendation: `DEFER` (đề xuất, không phải DEC). `DESIGN_COMPLETE` tự đánh giá đủ để review; PoC lake `NOT_APPLICABLE`; `REAL_DATA_APPROVAL` `BLOCKED` bởi Q2/Q4/Q6/Q8/Q11/Q13/Q14. Kế hoạch chuẩn bị không đổi vì không phát hiện gap buộc sửa. Không có Data Lake nào được triển khai.
- Kiểm tra:
  - Validator scratch trên discovery/status/roadmap/changelog/kế hoạch: UTF-8 không BOM, fence đóng, số cột bảng khớp header, link tương đối và heading anchor tồn tại; 0 lỗi.
  - Snapshot SHA-256 119 file `custom_addons`, `frontend/src`, `frontend/tests`, `contracts` và `scripts` không đổi so với trước khi sửa.
  - `git diff --check` đạt; file mới không có khoảng trắng cuối dòng.
  - Không chạy application tests vì không đổi code; không start/upgrade/seed Odoo. Không commit/push.
- Next: phiên chính audit tài liệu và recommendation. Người dùng chọn use case/KPI owner (Q13) và trả lời các câu hỏi mục 10. Nếu chọn UC-01, giao C17/RPT-001 riêng; không mở analytics store/lake khi chưa có trigger mục 9.1.

## CHG-20261029-022 — Kế hoạch chuẩn bị Data Platform/Data Lake

- Phạm vi: chỉ thiết kế discovery/spec-only; không sửa application code, schema, API, frontend, runtime hoặc database; không chọn nhà cung cấp hay triển khai bucket/connector/pipeline.
- Đã thêm `TP_DATA_PLATFORM_PREPARATION_PLAN.md`: ranh giới Odoo là nguồn sự thật, raw/validated/curated, inventory/use case/data contract, quyền và retention, lựa chọn ingestion, PoC dữ liệu giả, cổng và điều không làm.
- Đã thêm prompt `CLAUDE_DATA_PLATFORM_DISCOVERY.md` cho Claude. Đầu ra bắt buộc gồm source inventory, tối đa ba use case, data contracts, security/retention matrix, analytics-first so với lakehouse-lite, PoC plan, risk/gap và recommendation `DEFER`/`ANALYTICS_FIRST`/`LAKEHOUSE_LITE`.
- Data Lake hiện chỉ là đề xuất; Odoo vẫn là nguồn giao dịch/quyền/trạng thái. Không dùng dữ liệu thật, Excel/NAS/filestore thật hoặc tạo `tp_datalake`. Q2/Q4/Q6/Q8/Q11/Q12/Q13/Q14 tiếp tục là cổng tùy use case.
- Kiểm tra: maintained application code không đổi; kiểm cấu trúc tài liệu dự kiến và `git diff --check`; không chạy application tests vì không đổi code/runtime. Không commit/push.
- Next: giao DP-001 cho Claude nếu muốn khảo sát; phiên chính audit tài liệu rồi mới quyết định có PoC hay không.

## CHG-20261028-021 — Kế hoạch điều phối giai đoạn lập trình

- Phạm vi: chỉ lập kế hoạch và tài liệu điều phối; không sửa application code, schema, API, frontend, runtime hoặc database.
- Đã tạo `docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md`: bốn làn maintenance/tính năng test/pilot/operations; C00–C17 theo G0–G7, đầu vào/kết quả/test từng batch và pilot draft-review giới hạn trước các module downstream. Inbox là feature mới, không gộp maintenance.
- Đã thêm `AI_COORDINATION_WORKFLOW.md` và prompt C01/FND-002: môi trường test live/race tái lập được, không phụ thuộc helper riêng `.local`. Phiên chính giữ vai trò phân tích, tổng hợp ý tưởng, review/test và phát correction/next prompt; Claude code theo task được giao. DEC-022 ghi nhận phương thức làm việc người dùng đã chỉ định; không chốt thêm quy chế nghiệp vụ.
- Kiểm tra: start checkpoint trước tài liệu; kiểm link/bảng/fence và maintained source so checkpoint; `git diff --check`, `finish/check` ở cuối batch. Không chạy application tests vì không đổi code; kết quả 79/22/3/2 là lịch sử CHG-020, không nhận là mới chạy. Q2-A/Q2-B, bundle thực tế, owner/evidence/sign-off vẫn mở.
- Next: người dùng có thể giao prompt C01 cho Claude; phiên chính audit kết quả và phát prompt sửa hoặc C02 khi scope đủ. Song song chốt cổng pilot. Không mở BASE/legal/payment/grant người thật, không commit/push trong lượt này.

## CHG-20261028-020 — Hoàn tất technical acceptance CTR-002a.1 trên test

- Phạm vi: maintenance của CTR-002a-P1 theo DEC-020/DEC-021. Sửa validation V01/V02, chặn self-review ở reviewer picker/submit/resubmit/return pending cũ, thêm HTTP regression và kiểm tích hợp live trên instance test cô lập. Không thêm state, capability, action nghiệp vụ hoặc quyền người thật.
- Backend/API: enum sai kiểu trả `400 invalid_request`; currency blank/whitespace/null trả 400, unknown currency đúng kiểu trả `422 unknown_currency`; self-review trả `422 reviewer_ineligible`; giữ request ID, rollback, version, idempotency, audit/outbox và lịch sử bất biến. OpenAPI sửa mô tả YAML lỗi inline và TypeScript types được sinh lại.
- Frontend/test: live spec opt-in dùng dữ liệu giả, database `tp_tanphat_ctr002a_verify`, origin `127.0.0.1:18089`; flow create → edit → submit → return → rework → edit → resubmit và race hai HTTP session độc lập.
- Kiểm tra: Odoo `tp_tanphat_test` **0 failed, 0 error(s) of 79 tests**; Ruff, OpenAPI validator, api:types, typecheck, build đạt; Vitest 22; mock E2E 3; live E2E 2. Race khác key `200 + 409 stale_version`, cùng key `200 + 200 replay`; mỗi trường hợp version/audit/outbox/idempotency tăng đúng một lần. Log/report nằm trong `.local/`, ngoài Git. INFO filestore GC `WinError 5` vẫn còn trên Windows.
- Bàn giao: cập nhật PROJECT_STATUS, ROADMAP, readiness/gate, workflow KD và frontend README; readiness 7.1.6 đánh dấu technical acceptance **chỉ cho test fixture**. Q2-A/Q2-B, bundle thực tế, owner/evidence/sign-off, pilot và người dùng thật vẫn pending. BASE approval, ký, hiệu lực, thanh toán, giao khoán/nghiệm thu và grant thật chưa mở. Không commit/push.

## CHG-20261028-019 — Đối chiếu lần cuối cổng test và pilot

- Phạm vi: hiệu chỉnh bàn giao/tài liệu sau CHG-018; không sửa code ứng dụng, runtime, database hoặc quyết định nghiệp vụ mới.
- Đã làm: đồng bộ `Next action` ở cuối PROJECT_STATUS với phần đầu, thêm self-review vào backlog; bỏ yêu cầu Q2/hồ sơ thật trước maintenance test và giữ chúng trước pilot. Sửa tham chiếu mục trong gate và câu chữ để công nhận phạm vi thiết kế người dùng đã giao AI ở DEC-021.
- Kiểm tra: validator tài liệu BIZ-002 và gate (liên kết, heading, bảng, fence, source snapshot), `git diff --check`, workflow `finish/check`; không chạy test ứng dụng vì chỉ tài liệu. Bộ kiểm scratch được cập nhật để hiểu mục KD 7.5 và dòng CTR gate accepted chỉ trên test.
- Next: khi được giao lượt code, triển khai CTR-002a.1 theo Ready for Code mục 2.2–2.3; trước pilot còn Q2-A/Q2-B, bundle thực tế và owner/evidence/sign-off.

## CHG-20261028-018 — Chốt chính sách thiết kế giới hạn cho CTR-002a-P1

- Phạm vi: tài liệu/handoff, theo việc người dùng giao AI tự phân tích và quyết định hợp lý; không sửa source, runtime hoặc database.
- Quyết định DEC-021: preparer KD có assignment được draft/edit/submit; commercial reviewer phải khác người gửi ở từng submission/resubmit; vì review có kiểm tra số tiền nên sender/reviewer cần `financial_read`, còn sửa tiền cần thêm `financial_draft_edit`. Không suy quyền từ chức danh; không mở legal/BASE/payment/grant người thật.
- Đã cập nhật: cổng Ready for Code phân biệt maintenance test-slice với implementation/pilot; readiness mục 7.1.5 ghi policy, giới hạn và đề xuất partner/project picker/amount; status/roadmap/decision/changelog đồng bộ. Self-review backend/picker là maintenance cần làm; V01/V02 vẫn mở.
- Phân loại: đây là **AI-design accepted for CTR-002a test**, không phải bổ nhiệm Q2-A/Q2-B, quy tắc bốn mắt toàn công ty hay thẩm quyền ký pháp lý. Q2, bundle thực tế, owner/evidence và traceability của nghiệp vụ thật vẫn là cổng.
- Kiểm tra: link/bảng/fence/handoff và `git diff --check`; application source/runtime/database không đổi; không chạy app tests vì chỉ tài liệu.
- Next: khi người dùng giao code kỹ thuật, thực hiện maintenance CTR-002a.1 (V01/V02/self-review/HTTP/live/race) đúng handoff 2.2–2.3; Q2/owner/evidence/bundle thực tế tiếp tục là cổng trước pilot/real-users.
- Rà soát lại cổng: RFC-02/Q2 và RFC-06 bundle thực tế được deferred cho pilot/real-users; CTR-002a-test-maintenance có handoff/traceability riêng trong `TP_READY_FOR_CODE_GATE.md` mục 2.2–2.3. V02 chốt blank currency 400, unknown currency 422; pending tự gán cũ bị chặn return mà không sửa lịch sử. Workflow KD đồng bộ DEC-021, reason bắt buộc/issue optional. Không hỏi lại DEC-021; chưa có lệnh code trong lượt này.
## CHG-20261028-017 — Cổng Ready for Code theo yêu cầu chuẩn bị nghiệp vụ trước lập trình

- Phạm vi: chỉ tài liệu và handoff; người dùng yêu cầu kiểm tra/chuẩn bị rõ để lúc code chỉ triển khai nghiệp vụ đã chốt. Không sửa source, runtime/database hoặc xử lý V01/V02 trong lượt này.
- Đã làm: thêm `TP_READY_FOR_CODE_GATE.md` với RFC-01…10: scope, Q2/RACI, state/action, data/validation, record/field/file/export, bundle thực tế, UI, API, traceability/acceptance và gap/sign-off; phân biệt phần AI tự chuẩn bị với phần công ty phải cung cấp/xác nhận. Status chuyển ưu tiên sang chuẩn bị/nghiệm thu, không tự tiếp tục code kỹ thuật.
- Trạng thái: TP Contracts chưa Ready for Code theo cổng nghiệp vụ; Q2 và bundle thực tế chưa đạt, owner/traceability còn thiếu. CTR-002a code trên test giữ nguyên; test xanh không thay xác nhận công ty. Hai lỗi validation vẫn mở.
- Kiểm tra: kiểm link/bảng/nội dung và `git diff --check`; maintained code không đổi; handoff `finish/check`. Không chạy lại application tests vì chỉ tài liệu.
- Next: scope TP Contracts + Q2-A, thu thập hồ sơ khử dữ liệu, hoàn thiện từng RFC và ghi kết luận; chỉ mở code sau owner/người dùng xác nhận cổng của slice.
## CHG-20261028-016 — Review CTR-002a, tái kiểm test và ghi hai lỗi validation

- Phạm vi: review theo yêu cầu người dùng; cập nhật status/readiness/roadmap/changelog và handoff, không sửa code ứng dụng hoặc mở slice mới. Baseline HEAD `95bfc3f4`, working tree sạch, checker CHG-015 đạt; không commit/push/fetch.
- Source: đúng chuỗi draft/phụ lục nháp/edit/submit/return/rework/resubmit, backend kiểm capability/company/project/department/state/version/idempotency, snapshot/audit/outbox; không thấy bypass quyền hoặc action BASE/legal/payment ngoài allowlist trong phạm vi review.
- Findings P2: (1) `_choice` thiếu kiểm kiểu trước lookup frozenset, JSON list/object ở contract_type/tax_basis gây TypeError; (2) currency whitespace được parse thành None nhưng `_tp_currency` gọi `.upper()`, gây AttributeError. Đã tái hiện bằng stateless AST probe lấy hàm source, không gửi HTTP hoặc ghi DB; controller không map hai exception thành ContractWorkflowError/400/422. Hai lỗi **chưa sửa** và bộ test xanh chưa bao phủ; ghi reproduction/tiêu chí regression tại readiness 7.1.4.
- Kiểm thực chạy: Odoo `dev.ps1 test` trên `tp_tanphat_test` báo **0 failed, 0 error(s) of 72 tests**; frontend typecheck, Vitest 22, build (`VITE_ODOO_DATABASE=tp_tanphat_test`), Playwright workflow 3 bằng mock API và Ruff `custom_addons scripts/dev.py scripts/check_contract.py` đạt. Không kiểm UI với Odoo live, không test race song song mới; vẫn có INFO filestore GC `WinError 5`.
- Runtime: Odoo/PostgreSQL ban đầu dừng; test khởi động PostgreSQL, đã stop/status cả hai dừng lại. Không upgrade/seed dev, đổi credential hoặc cấp grant người dùng thật. Maintained code không sửa; docs được kiểm link/bảng và handoff riêng trước finish/check.
- Nghiệp vụ: Q2-A/Q2-B và B01–B03 vẫn proposed/mô phỏng, chưa có xác nhận công ty hoặc bundle thực tế đủ điều kiện. DEC-020 chỉ mở phát triển test; không thay bằng chấp thuận pilot.
- Next: CTR-002a.1 sửa validation + HTTP regression rồi kiểm UI→API→Odoo thật trên test riêng; song song chốt Q2-A/Q2-B và hồ sơ thực tế khử dữ liệu. Chưa mở review_complete, BASE, ký, hiệu lực, thanh toán hoặc grant người thật.

## CHG-20261028-015 — Commit và push BIZ-002 và CTR-002a

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `02c9e18a` gồm tài liệu BIZ-002 (CHG-009..013) ở trạng thái trước CHG-014; `a2f29f2e` gồm CTR-002a (CHG-014). Stage theo từng đường dẫn, không `git add .`; status/roadmap ghi hash; push `main` lên `origin` trong cùng lượt.
- Kiểm tra: dựng lại file dùng chung bằng cách đảo chỉnh sửa CHG-014, 0 lỗi, `frontend/README.md` trùng HEAD cũ; link/bảng tài liệu của `02c9e18a` đạt; `git diff --cached --check` của `a2f29f2e` đạt; sau `a2f29f2e` working tree sạch, `ai_workflow.py check` đạt.
- Giới hạn: `02c9e18a` giữ `AI_WORKFLOW_STATE.json` của CHG-008 (state CHG-013 bị `finish` CHG-014 ghi đè trước khi commit) nên checker tại commit đó lệch. `git diff --check` của commit đó báo hai dấu cách xuống dòng Markdown và dòng trống cuối file trong tài liệu BIZ-002, giữ nguyên. Không chạy lại test ứng dụng vì không đổi code.
- Next: người dùng review nghiệp vụ CTR-002a; Q2-A/Q2-B và bundle thực tế trước pilot.

## CHG-20261028-014 — CTR-002a: draft → gửi rà soát → trả lại → sửa → gửi lại (chỉ test)

- Phạm vi: code CTR-002a-P1 theo DEC-020, chỉ trên `tp_tanphat_test` với dữ liệu giả và actor fixture. Không upgrade/seed `tp_tanphat_dev`, không cấp grant cho người dùng thật, không đổi credential. Ngoài phạm vi và vẫn đóng: complete_review, cancel revision, record/verify BASE, chữ ký/thẩm quyền ký, hiệu lực, giao khoán/nghiệm thu/thanh toán, quản trị grant người dùng thật.
- Model/security (`tp_contract` 20.0.1.1.0, `tp_project`): `tp.project.grant` thêm capability `financial.draft_edit`, `contract.draft_edit`, `contract.submit`, `contract.review_commercial` theo project + phòng ban (`financial.read` giữ theo project); `tp.contract` thêm `department_id` lấy từ phòng chủ trì project và `aggregate_version` khóa `FOR UPDATE`. Model mới `tp.contract.submission` (S1/S2 bất biến, metadata snapshot + hash), `tp.contract.submission.amount` (snapshot tiền tách riêng, ACL như amount CTR-001), `tp.contract.audit` (append-only), `tp.contract.outbox` (một event/người nhận, retry giữ event), `tp.contract.idempotency`. Guard ORM chặn ghi state/version/BASE/legal ngoài workflow, sửa nội dung đã gửi, thay/xóa binary S1 qua `tp.contract.document` và `ir.attachment`. Migration post-migrate gán phòng chủ trì project cho hợp đồng cũ; project chưa có phòng chủ trì thì action trả `scope_incomplete`.
- Action T1–T6: `create_draft`, `create_amendment` (draft phụ lục, mang phạm vi bản trước), `edit_draft`, `submit_review` (draft → `in_review`, reviewer phải có assignment + capability trong cùng project/phòng), `return_review` (`in_review` → `returned`, lý do bắt buộc, issue theo dòng), `begin_rework` (`returned` → `draft`, giữ S1). Mỗi action một transaction: scope/capability kiểm lại, `expected_version`, idempotency theo actor + action + object + fingerprint (gồm version), audit + outbox; replay trả kết quả cũ sau khi kiểm lại quyền; khác payload 409.
- API (`tp_api`, `tp_planning_api`): `GET /contracts/{id}/reviewers`, `POST /contracts`, `POST /contracts/{id}/amendments`, `PATCH /contracts/{id}/revisions/{rid}`, `POST …/submit|return|rework`. Ghi bắt buộc Fetch Metadata/Origin same-origin, `X-CSRF-Token` gắn session, JSON object, `Idempotency-Key`; lỗi 400/401/403/404/409/415/422 có code và `request_id`, `no-store`. DTO thêm `version`, `allowed_actions`, `working_revision_id`, `submissions`; tiền vẫn decimal string và chỉ khi có `financial_read`. OpenAPI cập nhật trước frontend, types sinh lại.
- Frontend: form tạo hợp đồng nháp và phụ lục nháp; trình sửa bản nháp (header, revision, dòng phạm vi; cột tiền chỉ khi có `financial_read` + `financial_draft_edit`, chỉ gửi số tiền đã sửa, chưa xác nhận gửi `null`); gửi rà soát chọn reviewer từ API, tóm tắt sửa bắt buộc từ lần gửi thứ hai; trả lại có lý do và issue theo dòng; mở lại để sửa; lịch sử các lần gửi. Nút lấy từ `allowed_actions`; mỗi intent giữ một Idempotency-Key khi retry lỗi mạng/5xx; 409 stale hiện “Tải lại bản mới nhất”.
- Test: Odoo `dev.py test` trên `tp_tanphat_test` **0 failed, 0 error(s) of 72 tests** (16 test workflow ORM + 3 HttpCase: T-P01, T-N01…T-N09, cùng regression CTR-001); Ruff `tp_api tp_contract tp_planning_api tp_project` đạt; `npm run api:types` + typecheck đạt; Vitest 22 đạt; build với `VITE_ODOO_DATABASE=tp_tanphat_test` đạt; Playwright `contract-workflow.spec.ts` 3 đạt (mock `/api/v1/**`, không Odoo/DB). Không có race song song thật; UI chưa chạy với Odoo live.
- Giới hạn: một grant hiệu lực cho mỗi (project, user, capability); đổi phòng chủ trì project không đổi scope hợp đồng cũ; outbox chưa có cron/kênh gửi/inbox; idempotency chưa có retention; chưa chọn đối tác trong UI; danh sách project ở form tạo lấy 20 bản đầu; xóa dòng có tiền cần quyền sửa tiền. Business acceptance pending; Q2 chặn người dùng thật/pilot.
- Next: người dùng review và quyết định commit; nếu cần xem UI trên Odoo thật thì cần cho phép upgrade database dev hoặc dựng instance test. Q2-A/Q2-B và bundle thực tế vẫn là cổng trước pilot.

## CHG-20261028-013 — Q2-P1, walkthrough mô phỏng và cổng CTR-002a trước code

- Phạm vi: chỉ tài liệu và handoff BIZ-002; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không triển khai CTR-002a, grant admin, record/verify BASE, ký, hiệu lực hay thanh toán.
- Đã làm: bổ sung ma trận Q2-P1 11 hành động tại `TP_KD_WORKFLOW_AND_PERMISSIONS.md` mục 7.4; tách `financial.read`, sửa hồ sơ, xuất dữ liệu và `grant.manage`; tách người quyết định grant/revoke khỏi người thao tác kỹ thuật; giữ cùng/khác người, hạn mức và bốn mắt ở trạng thái chưa xác nhận.
- Bổ sung readiness mục 7.1: ghi phản hồi người dùng cho phép tiếp tục phân tích nhưng chưa bổ nhiệm vai trò; cập nhật Q2-A/Q2-B; inventory nói rõ chưa có bundle thực tế khử dữ liệu đủ chuỗi; chuẩn bị SIM-P1 B01 bình thường, B02 trả–sửa–gửi lại, B03 correction/void và bàn giao/revoke. Đây là mô phỏng logic, không phải UAT/test/nghiệm thu.
- Bổ sung CTR-002a-P1: snapshot vòng gửi bất biến trong revision nháp, rework/resubmit không tạo correction pháp lý; actor fixture/scope; CSRF, optimistic aggregate version, idempotency, transaction/audit/outbox, negative/concurrent/retry cases và tiêu chí cổng. Đối chiếu source tĩnh xác nhận CTR-001 chỉ GET/read, chưa có action ghi/version/audit/idempotency; không mở ACL ghi.
- Cập nhật dictionary/workflow K/design package/evidence/status/roadmap để không gộp state handover với grant, không coi hash bản sao nguồn là hồ sơ thực tế và giữ thứ tự Q2 → bundle → quyết định chuyển code → CTR-002a test. Q1/Q3/Q4/Q6/Q8/Q9–Q14 tiếp tục mở theo cổng.
- Kiểm tra trong lượt: `.local/biz-002/review_q2.py` đạt 19 tài liệu/134 link/104 bảng, 9 link heading, 11 action Q2, 6 dòng log proposed, 19 chặng SIM và 10 phép tính Decimal giả lập. Đối chiếu source tĩnh; 5 hash bản sao S01–S05 khớp manifest, không kiểm NAS hiện hành; maintained code 108 file không đổi so checkpoint; `git diff --check` đạt. Báo cáo `.local/biz-002/q2_review_validation.json` ngoài Git. Không chạy Odoo/frontend/app tests vì chỉ tài liệu; `ai_workflow.py finish/check` ghi handoff sau kiểm nội dung; checker không xác nhận nghiệp vụ.
- Next: chủ nghiệp vụ xác nhận vai trò/căn cứ Q2 và cung cấp 2–3 bundle khử dữ liệu; sau yêu cầu chuyển giai đoạn rõ ràng mới cân nhắc code CTR-002a-P1 trên test.

## CHG-20261028-012 — Kiểm tra lại toàn bộ tài liệu BIZ-002 và giới hạn bằng chứng nguồn

- Phạm vi: kiểm tra tài liệu/handoff; không đổi source ứng dụng, schema, API, database, runtime hoặc quyền. Không có quyết định nghiệp vụ mới.
- Hiệu chỉnh dòng `reported_checks` của handoff CHG-011: bộ kiểm BIZ-001/NAS chưa có báo cáo mới để xác nhận, nên không dùng dòng “passed” đó làm bằng chứng kiểm NAS/Decimal trong lượt này; state mới chỉ ghi các kiểm tra vừa xác minh được.
- Kết quả: 19 tài liệu, 121 link tương đối, 95 bảng có header/fence nhất quán; walkthrough normal/rejected 13 cặp, correction A–M 13 ca, Q1–Q14 đủ trong readiness. Hash năm bản sao nguồn S01–S05 trong `.local/biz-001` khớp registry; lượt này **không** xác nhận hash trực tiếp trên NAS và ghi rõ giới hạn trong `.local/biz-002/review_validation.json` ngoài Git.
- Maintained code vẫn 108 file không đổi; business acceptance pending, nhật ký Q2/bundle/CTR-002a còn `open`. Đây là kiểm tra handoff/tài liệu, không phải UAT hay phê duyệt công ty.
- Next: giữ thứ tự Q2 → 2–3 bundle khử dữ liệu → ghi quyết định/gap → người dùng chọn giai đoạn; chỉ sau đó mới xem xét CTR-002a test.

## CHG-20261028-011 — Kiểm tra CTR-001 và chuẩn bị xác nhận BIZ-002 theo Q2

- Phạm vi: review source/quyền/API/test và tài liệu; chỉ sửa readiness, status, roadmap, changelog và state bàn giao. Không phát triển CTR-002a, không thay code ứng dụng, schema/API hoặc credential; không commit/push.
- Kết quả review: chưa phát hiện lỗi chặn trong CTR-001 read slice. BIZ-002 đủ cấu trúc để review nghiệp vụ; chưa có xác nhận công ty, Q1–Q14 vẫn mở. Các giới hạn đã ghi giữ nguyên: metadata BASE text tự do có thể chứa tiền, grant thiếu ledger revoke/delegation bất biến, chưa có capability export tiền riêng; phải xử lý trước pilot dữ liệu thật.
- Đã bổ sung: nhật ký quyết định/nghiệm thu tại readiness mục 7.1, có scope/môi trường, RACI/người xác nhận bằng mã nội bộ, kết luận/trạng thái, evidence/hash, ngày/phiên bản và gap/next action. Các dòng Q2/bundle/CTR-002a đều `open`; không điền giả tên, bằng chứng hoặc chấp thuận. Mục 7.2 tách kiểm tra kỹ thuật khỏi nghiệm thu và quyết định mở code. Làm rõ thứ tự Q2 → 2–3 bundle → ghi kết luận → quyết định người dùng → CTR-002a test; không chờ đóng đồng loạt Q1–Q14.
- Kiểm tra source thực chạy: frontend typecheck đạt; Vitest 14 tests đạt; Ruff `custom_addons scripts/dev.py scripts/check_contract.py` đạt; `dev.ps1 test` trên `tp_tanphat_test` báo **0 failed, 0 error(s) of 53 tests**. Còn INFO filestore GC `WinError 5` như đã ghi. Không chạy lại build/E2E; không nhận kết quả lịch sử thành mới.
- Runtime: ban đầu Odoo/PostgreSQL dừng; test khởi động PostgreSQL, dùng DB test riêng; đã dừng và kiểm status cả hai dừng sau kiểm tra. Không upgrade/seed database dev. Maintained code được đối chiếu checkpoint cuối lượt; không thay source trong batch này.
- Kiểm tài liệu/handoff: kết quả kiểm link/bảng/fence/bao phủ, `git diff --check` và `ai_workflow.py finish/check` được ghi trong state bàn giao sau khi hoàn tất kiểm tra; checker không thay bằng chứng nghiệp vụ.
- Next: Q2 trách nhiệm/quyền Ban KD và walkthrough hợp đồng với hồ sơ khử dữ liệu, ghi nhật ký; chỉ người dùng quyết định chuyển sang CTR-002a test. Chưa mở action BASE/legal/tiền thật hoặc grant admin.

## CHG-20261028-010 — Đồng bộ state, ngoại lệ và công thức trong gói BIZ-002

- Phạm vi: chỉ tài liệu; không đổi code ứng dụng, schema, API, frontend, runtime, dữ liệu hoặc credential.
- Đã làm: đồng bộ state/transition giữa workflow F–M và dictionary (returned/resubmit, BASE rejected vs verification disputed, acceptance signature, lifecycle); thống nhất mã allocation theo company; bổ sung handover/revoke/restore/share và đường correction; bổ sung công thức kiểm soát hợp đồng, cấp 1/2, khối lượng, payment allocation, tạm ứng, giữ lại, aging/freshness và known-at. Cập nhật readiness walkthrough để dùng basis/case `null`/`0`/unknown đúng nghĩa.
- Quyết định/workflow: vẫn Proposed/Unconfirmed theo BIZ-002; BASE official, chữ ký/hiệu lực/posting tách lớp; Q1–Q14 chưa đóng. Không biến công thức giả lập thành công thức tài chính doanh nghiệp hoặc mở action.
- Kiểm tra: `git diff --check` đạt; validation riêng đạt 19 tài liệu duy nhất, 119 link tương đối, 94 bảng có header/fence đúng, 13 cặp walkthrough normal/rejected và 13 ca correction A–M, Q1–Q14 có đầu mối/cổng; 10 phép tính Decimal kiểm công thức bổ sung đạt. `.local/biz-001/verify_baseline.py` đạt (5 hash khớp, 48 link/28 bảng baseline, 10 Decimal checks riêng, 108 file maintained code không đổi); không chạy Odoo/frontend test vì code/runtime không đổi. Báo cáo kiểm tài liệu `.local/biz-002/validation.json` ngoài Git; không nhận walkthrough là UAT. `ai_workflow.py finish/check` ghi handoff CHG-010.
- Next: chủ nghiệp vụ review bộ BIZ-002 và hồ sơ khử dữ liệu, trả lời Q theo slice; người dùng quyết định khi nào chuyển sang code.

## CHG-20261028-009 — BIZ-002: bộ thiết kế nghiệp vụ toàn công ty trước code

- Phạm vi: chỉ tài liệu/workflow handoff; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không setup/upgrade/seed và không gửi message sang task khác.
- Đã làm: rà soát khoảng trống và baseline; kiểm hash năm nguồn S01–S05 với `.local/biz-001/manifest.json`; bổ sung [bản đồ A–M/RACI](architecture/TP_ENTERPRISE_PROCESS_MAP.md), [workflow A–E](architecture/TP_PROCESS_WORKFLOWS_A_E.md), [workflow F–M](architecture/TP_PROCESS_WORKFLOWS_F_M.md), [từ điển dữ liệu/ERD/ma trận quyền](architecture/TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md), [tích hợp/KPI/màn hình/API thiết kế](architecture/TP_BIZ002_INTEGRATION_AND_REPORTING.md), [kịch bản/readiness/Q1–Q14](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md) và [chỉ mục/gap analysis](architecture/TP_BIZ002_DESIGN_PACKAGE.md). Cập nhật `TP_BUSINESS_WORKFLOW`, database/source architecture, architecture README, `PROJECT_STATUS`, `ROADMAP`, `DECISIONS`, `AI_CHANGE_WORKFLOW`.
- Phân loại: quyết định người dùng (BASE official, Odoo + React riêng, một DB/môi trường, scope tiền) tách khỏi quan sát E01–E18, đề xuất RACI/capability/transition/KPI và điểm chưa xác nhận Q1–Q14. Ghi rõ grant runtime hiện thiếu ledger revoke/delegation/audit riêng và `financial.export` capability; không tự coi policy mục tiêu là đã enforce.
- Kiểm tra: `scripts/ai_workflow.py start` trước sửa; `.\.venv\Scripts\python.exe .local/biz-001/verify_baseline.py` đạt (5 source hash khớp, 29 link/27 bảng trước sửa, 10 Decimal synthetic checks, 0 cell kế toán thực tế; application/business acceptance tests not run); kiểm tra Markdown link/table/fence/nội dung A–M riêng đạt; `git diff --check` đạt trước finish; Odoo/PostgreSQL status đang listening. Không chạy app tests vì không đổi code/runtime.
- Giới hạn: đây là baseline thiết kế để chủ nghiệp vụ review, chưa là quy chế/UAT/Odoo test. Q1–Q14, 2–3 hồ sơ khử dữ liệu và owner xác nhận còn chờ; CTR-001 read giữ nguyên, CTR-002/PRJ/ALC/STL/FIN/IMP chỉ mở sau người dùng chọn chuyển giai đoạn.
- Next: review BIZ-002 walkthrough A–M, chốt câu hỏi theo slice và hồ sơ đại diện; sau đó người dùng quyết định phạm vi code. Giữ Q2: chỉ superuser cấp grant cho đến khi người cấp/thu hồi và record/verify BASE được xác nhận.

## CHG-20261028-008 — Ánh xạ trạng thái hợp đồng và ghi nhận push

- Phạm vi: tài liệu; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: thêm mục 4.4 trong `TP_KD_WORKFLOW_AND_PERMISSIONS.md` ánh xạ tên trạng thái ở 4.1–4.3 sang field/giá trị trong code (`review_state`, `decision`, `verification_state`, `authority_status`, `signature_status`, `signature_authority_status`, `effectivity_status`, `lifecycle_state`) kèm constraint hiện có; liên kết từ `TP_BUSINESS_WORKFLOW.md`. Status ghi nhận `main` đã push đến `00d4ddc7`.
- Điểm cần chốt cho CTR-002: transition hủy revision (`cancelled` có trong code, 4.1 chưa có); cách confirm_effectivity cập nhật `effectivity_status` và `lifecycle_state` cùng lúc; thứ tự review → BASE reference chưa có constraint ở model.
- Kiểm tra: đối chiếu giá trị với model `tp_contract`, DTO `tp_planning_api` và nhãn frontend; kiểm liên kết Markdown; `git diff --check`; `ai_workflow.py finish/check`.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002.

## CHG-20261028-007 — Commit local AUTH-001, BIZ-001 và CTR-001

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `395be562` gồm login AUTH-001 (CHG-004) và baseline BIZ-001 (CHG-005) ở đúng trạng thái trước CTR-001; `807018b9` gồm CTR-001 (CHG-006). Stage theo từng đường dẫn, không `git add .`; chưa push.
- Kiểm tra: dựng lại file dùng chung bằng cách đảo chỉnh sửa CTR-001, áp lại khớp 18/18 file; export `395be562` typecheck đạt, Vitest 10 đạt; sau `807018b9` `git diff HEAD` rỗng, `ai_workflow.py check` đạt; quét diff không có credential/dữ liệu thật.
- Giới hạn: `395be562` giữ `AI_WORKFLOW_STATE.json` của `03702d24` nên checker tại commit đó báo lệch; không chạy lại Odoo tests cho commit này vì không đổi backend. Hai tài liệu TP_KD có xuống dòng Markdown bằng hai dấu cách như các tài liệu sẵn có.
- Next: push khi người dùng yêu cầu; nghiệm thu BIZ-001/CTR-001 và chốt Q2.

## CHG-20261028-006 — CTR-001: TP Contracts read slice

- Phạm vi: addon mới `tp_contract`, grant `financial_read` trong `tp_project`, API đọc trong `tp_planning_api`, OpenAPI, frontend TP Contracts, dev seed/smoke/checker và tài liệu. Không sửa `odoo/`/`addons/`, không mở API ghi/duyệt/ký/xác nhận hiệu lực, không đổi xác thực.
- Model: `tp.contract`, `tp.contract.revision`, `tp.contract.line`, `tp.contract.line.amount`, `tp.approval.reference`, `tp.approval.reference.amount`, `tp.contract.document`; review, chữ ký, thẩm quyền ký, hiệu lực và kết quả BASE là các trường riêng; snapshot theo ngày hiệu lực thay thế bản trước; tổng chỉ có giá trị khi mọi dòng đã xác nhận và cùng cơ sở thuế.
- Quyền: đọc metadata theo assignment project + company; số tiền và tài liệu `financial` thêm điều kiện grant `tp.project.grant` còn hiệu lực cho đúng project. Grant có lý do/thời hạn/thu hồi, không tự cấp, chỉ superuser tạo khi Q2 chưa chốt. Không group nào được ghi dữ liệu hợp đồng qua ORM/RPC.
- API: `GET /api/v1/contracts`, `/contracts/{id}?as_of=`, `/contracts/{id}/revisions/{revision_id}`, `/contracts/{id}/documents/{document_id}/content`; 404 ngoài scope, 400 `invalid_request`, `no-store`, bỏ field tiền khi thiếu grant.
- Frontend: route `/contracts`, chi tiết hợp đồng, trang phạm vi revision; nhãn BASE đã/chưa xác minh, ghi chú BASE approved không đồng nghĩa đã ký/hiệu lực, định dạng tiền từ decimal string, mobile 390px.
- Dữ liệu dev: ba hợp đồng giả lập `HD-DEV-001/002/003` và grant dev cho admin trên DEV-001. Không có hồ sơ thật.
- Quyết định: DEC-017.
- Kiểm thử thực chạy: Odoo `0 failed, 0 error(s) of 53 tests` (contract access 15, model 16, contracts API 12, project 10); upgrade + smoke đạt; `check_contract.py --live` đạt; Ruff đạt; frontend typecheck đạt, Vitest 14 đạt, build đạt, Playwright 11 đạt; `git diff --check` đạt.
- Giới hạn: Q1–Q3 còn mở; chưa có quản trị grant ngoài superuser; văn bản tự do không được quét số tiền; chưa có view Odoo native cho hợp đồng; exit code `dev.py test` không đáng tin. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002 draft/submit/return trên test.

## CHG-20261028-005 — BIZ-001: baseline workflow và ma trận quyền Ban Kinh doanh

- Phạm vi: phân tích năm nguồn S01–S05 và cập nhật tài liệu workflow/database/status/roadmap/decision; không sửa model, API, frontend, runtime hoặc import dữ liệu.
- Đã chốt theo yêu cầu người dùng: BASE là nơi phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận kết quả; quyền xem tiền mặc định cho người quản trị dự án đúng scope, Trưởng ban, QT-TC và lãnh đạo, hỗ trợ cần cấp riêng; hạn mức ký/duyệt chưa biết nên không đặt giả.
- Đã làm rõ: review nội bộ, BASE decision/evidence verification, chữ ký/hiệu lực pháp lý, revision snapshot và trạng thái thực hiện là các lớp riêng; contract/production/acceptance/invoice/cash/retention là domain record riêng; khoán cấp 2 không cộng trùng cấp 1; nhãn “GT phải xuất hóa đơn” trong mẫu được map là invoice issued thực tế.
- Tài liệu: `docs/architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md`, `docs/architecture/TP_KD_EVIDENCE_AND_ACCEPTANCE.md`; cập nhật `TP_BUSINESS_WORKFLOW.md`, `TP_DATABASE_DESIGN.md`, `TP_PLATFORM_SOURCE_STRUCTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `PROJECT_STATUS.md` và architecture index.
- Kiểm tra: đọc/đối chiếu source snapshot và hash manifest; hash bản NAS hiện tại vẫn khớp cả 5 source; đọc các range S03/S05 liên quan, xem trang phân công S02; `verify_baseline.py` đạt 27 link tương đối, 26 bảng Markdown nhất quán, 0 cell dữ liệu kế toán thực tế trong bản S05 đọc, 10 phép tính Decimal giả lập; `git diff --check` đạt. Không chạy macro/external link và không chạy bộ ứng dụng vì lượt này chỉ thay tài liệu.
- Giới hạn: chưa có 2–3 hồ sơ thật đã khử dữ liệu, văn bản hạn mức/bốn mắt/ủy quyền, BASE ID/evidence chuẩn hoặc feed kế toán thực tế; state/capability/ca nghiệm thu là thiết kế, chưa chạy Odoo. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: `CTR-001` read-only contract/revision/line + approval reference, field/attachment security và negative tests bằng dữ liệu giả; thu thập Q1–Q3 trước action ghi/chốt pháp lý.

## CHG-20261028-004 — Giao diện đăng nhập riêng TANPHAT ONE

- Phạm vi: `frontend/src/features/auth`, transport session frontend, visual design, E2E và tài liệu; không sửa Odoo core, model nghiệp vụ hoặc database.
- Đã thay đổi: `/work/` hiển thị cổng login React hai cột với minh họa cầu dây văng SVG, Be Vietnam Pro, hover/focus, animation vẽ cáp, reduced-motion, responsive mobile, hiện/ẩn mật khẩu, trạng thái pending/error và hướng dẫn hỗ trợ. Form gọi `/web/session/authenticate` same-origin, sau đó đọc `/api/v1/me`; không lưu password/token vào storage. MFA trả `uid: null` được giữ là bước xác thực bổ sung và có link native Odoo với redirect hiện tại.
- Quyết định: DEC-012. Database login không hardcode production: dev có fallback `tp_tanphat_dev`, production build yêu cầu `VITE_ODOO_DATABASE` khớp dbfilter.
- Kiểm thử thực chạy: `npm.cmd run typecheck --prefix frontend` đạt; `npm.cmd test --prefix frontend` đạt 10 tests; `VITE_ODOO_DATABASE=tp_tanphat_dev npm.cmd run build --prefix frontend` đạt; `npm.cmd run test:e2e --prefix frontend` đạt 8 tests (login, invalid credential, MFA handoff, gateway error, deep link, responsive, reduced-motion, permission/session regression); `git diff --check` đạt.
- Giới hạn: build production cần CI/release cung cấp `VITE_ODOO_DATABASE`; MFA code/passkey vẫn do native Odoo xử lý. Chưa đổi logo/branding ở native `/web/login`.
- Next: quay lại BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt state/role matrix.

## CHG-20261028-003 — OPS-001: backup và phục hồi dev cô lập

- Phạm vi: script backup/restore, hướng dẫn vận hành và bằng chứng thực chạy; không sửa model/API/frontend hoặc seed dữ liệu vào dev.
- Backup: snapshot nhất quán khi tạm dừng Odoo dev 18,95 giây, 314 bảng public, 37 tham chiếu attachment/27 blob, database dump 3.043.333 byte; source archive tại commit `d9e8ccdc`. Backup và credential giới hạn quyền, nằm ngoài Git.
- Kết quả: giải nén source từ backup; restore vào cluster mới cổng 55442, Odoo 18089, database/filestore riêng; 314 bảng/fingerprint và 37 attachment khớp trước neutralize; probe 2 attachment chỉ tồn tại ở bản sao; cluster/Odoo cô lập đã dừng; dev gốc smoke lại đạt.
- Kiểm thử tooling/tích hợp: 21 unit tests đạt, Ruff đạt; anonymous 401, planner/admin login + `/me` + list/detail DTO + query validation, 37 lượt tải tệp khớp SHA1/size và kiểm attachment theo scope đạt. Báo cáo cuối ở `.local/ops-001/rehearsals/20261028T064405723351Z/report.json`.
- Hướng dẫn: `ops/runbooks/BACKUP_RESTORE.md`. Chưa có lịch backup, backup ngoài máy hoặc phục hồi trên host khác.
- Next: BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt ma trận quyền/trạng thái.

## CHG-20261028-002 — Chốt baseline Git và publish handoff

- Phạm vi: kiểm chứng local `main` với `origin/main`, rà soát các file handoff đang chờ commit và chuẩn bị publish toàn bộ thay đổi hiện tại.
- Đã thay đổi: cập nhật trạng thái GIT-001 đã hoàn tất, chuyển Next action sang OPS-001, chốt DEC-010 và cập nhật roadmap; không sửa model/API/giao diện/database.
- Kiểm tra: `git fetch --prune origin`; local/remote cùng ở `a25a0182`; `git status`; kiểm tra credential-like patterns trong file dự kiến commit; checker trước lượt đạt.
- Publish: commit/push lên `origin/main` sẽ là baseline handoff mới của source hiện tại; xác nhận sau push bằng `git status` và `git rev-list`.
- Giới hạn: chưa diễn tập backup/restore, chưa xác minh production hoặc khôi phục hai commit ID cũ không tồn tại.
- Next: OPS-001.

## CHG-20261028-001 — AI handoff và workflow nghiệp vụ

- Phạm vi: tạo `AGENTS.md`, trạng thái dự án, quy trình bàn giao, workflow nghiệp vụ, changelog và checker local.
- Đã thay đổi: mọi phiên AI có thứ tự đọc bắt buộc; mỗi phiên code phải cập nhật status/changelog; state/role/transition của các phân hệ được phân biệt giữa thiết kế và đã triển khai.
- Kiểm chứng trạng thái: local hiện có baseline `82e9ea27`/`a25a0182`; bổ sung DEC-010 để phiên sau không thực hiện lại phục hồi Git theo ghi chú cũ. Không sửa metadata hoặc tạo commit trong lượt này.
- Kiểm thử: checker unit test 11/11 đạt; Ruff đạt; `git diff --check` đạt; kiểm tra `start`/`finish`/`check` đạt.
- Giới hạn: checker không thay thế Git, review nghiệp vụ, security test hoặc phê duyệt của người dùng.
- Next: xử lý Git baseline, rồi chốt state/role matrix cho TP Projects và TP Contracts.

## 2026-10-28 — Foundation và naming

- **Phạm vi:** Odoo foundation, project access, API v1, React workspace, naming TANPHAT ONE, chín tên phân hệ.
- **Đã có:** `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`; frontend đọc project theo session Odoo.
- **Kiểm thử:** Odoo 10 tests đạt; OpenAPI live đạt; frontend typecheck/build/unit/prototype/E2E đạt; smoke đạt.
- **Quyết định:** một PostgreSQL database cho mỗi môi trường; quyền dùng company/project/assignment; technical addon identifiers giữ ổn định.
- **Giới hạn:** chưa có contracts, allocations, settlements, import hoặc production; Git metadata cần baseline sạch.
- **Next:** chốt state/role matrix và triển khai `tp_contract` read vertical slice.

## Mẫu mục nhập

```text
## CHG-YYYYMMDD-NNN — <tên thay đổi>
- Phạm vi:
- Đã thay đổi:
- Workflow/model/API bị ảnh hưởng:
- Kiểm thử:
- Giới hạn:
- Next:
```

