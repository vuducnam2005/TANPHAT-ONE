# HR-ATTENDANCE-001 + HR-DIRECTORY-READONLY-001 — Nghiệm thu

Ngày 17/11/2026 · Batch `CHG-20261117-020` · Prompt
[CLAUDE_HR_ATTENDANCE_001_AND_DIRECTORY_READONLY](../prompts/CLAUDE_HR_ATTENDANCE_001_AND_DIRECTORY_READONLY.md)
· Policy [HR_ATTENDANCE_001_POLICY](../security/HR_ATTENDANCE_001_POLICY.md).

Trạng thái: **S1_DIRECTORY_VERIFIED** (S2–S4 chưa chạy). Cột kết quả ghi `NOT_RUN` tới khi
có bằng chứng thật; không ghi PASS cho bước chỉ review mã.

## 1. Môi trường và tài khoản

| Ký hiệu | Môi trường | Ghi chú |
| --- | --- | --- |
| U | Unit thuần Python (parser/tính công), không nối DB | `custom_addons/tp_hr_attendance/tests/test_parser.py` (`BaseCase`, không ghi DB) |
| OT | Odoo `TransactionCase` trên DB kiểm thử `tp_tanphat_test`, `--no-http`, user/fixture tạo trong transaction và rollback | Không chạy trên `tp_tanphat_dev`/server; không mở cổng 18079 |
| M | Local 18069 `tp_tanphat_dev` sau backup | Chỉ đọc/denied bằng tài khoản có sẵn; `env(user=…)` trong transaction rollback; không sửa/xóa nhân viên thật |
| S | Server `192.168.1.73` Docker `tp-odoo` | Smoke ẩn danh + kiểm module/version; không đăng nhập admin qua LAN |
| P | Public origin theo runbook | Smoke ẩn danh `/dang-nhap`, `/app` |
| E2E | Playwright trên 18069 | Ảnh desktop/mobile, assert payload/quyền, không chỉ HTTP 200 |

Tài khoản smoke: admin hiện có (HR manager + system), nhân viên nội bộ có hồ sơ
(không nhóm HR, hai phòng khác nhau), tài khoản KD scoped hiện có. Không in
mật khẩu/cookie; không tạo user/công giả trên M/S.

## 2. Ca nghiệm thu

| Mã | Actor | Input | Kỳ vọng | Env | Bằng chứng | Kết quả |
| --- | --- | --- | --- | --- | --- | --- |
| AT01-A | Nhân viên A (phòng X), nhân viên B (phòng Y), không nhóm HR | Mở TP HR → Nhân viên → Danh sách; mở chi tiết đồng nghiệp | Thấy danh bạ cả công ty (company được phép), chi tiết chỉ whitelist; nhãn **Chỉ xem**; không nút Tạo/Sửa/Lưu trữ/Xóa | OT, M, E2E | OT `test_viewer_sees_whole_company_through_whitelist_views`, `test_entry_and_menus_follow_real_groups`; M ORM user 41/42: 39/39 hồ sơ, menu TP HR + Danh sách, entry → Danh bạ; E2E admin 1440/390: list 20/39 dòng, cột whitelist, không nút Tạo, form có nhãn Chỉ xem, không ô sửa. Ảnh viewer thật chưa chụp (không có mật khẩu tài khoản viewer trên 18069) | PASS (OT, M); E2E viewer NOT_RUN |
| AT01-B | Nhân viên A | RPC `create/write/unlink/copy/load` trên `hr.employee.public`, `hr.employee`, `tp.hr.attendance.day/session`, `tp.hr.attendance.period/rule/code` | AccessError mọi thao tác; không có ACL ghi | OT, M (`has_access`, không ghi thật) | OT `test_viewer_cannot_change_or_read_private_records` (danh bạ: create/write/unlink/copy/load bị chặn, số hồ sơ không đổi); OT `test_viewer_reads_shared_board_but_cannot_change_hours`: viewer `has_access` create/write/unlink = False trên ngày công/phiên, `write`/`unlink`/`create` → AccessError; `test_viewer_cannot_import_or_tamper_with_batches`: viewer không tạo lô, log chỉ thêm, manager không ghi field hệ thống. M `has_access` ghi = False với 41/42 | PASS (OT danh bạ + công S2, M danh bạ); kỳ/phiếu S3 NOT_RUN |
| AT01-C | Nhân viên A | Đọc `hr.employee` trực tiếp, field private (`private_phone`, `birthday`, `identification_id`, `bank_account_id`, lương) qua `hr.employee.public`/`hr.employee` | Bị từ chối hoặc field không tồn tại trong payload | OT, M | OT: đọc `private_phone`/`identification_id`/`birthday` qua `hr.employee` → AccessError; field private không có trong `hr.employee.public`; M 41/42 đọc private → DENIED | PASS |
| AT02-A | Nhân viên A | `export_data` trên `hr.employee.public`; export ngày công người khác | AccessError; export ngày công của chính mình cho phép | OT, M | OT `test_export_only_for_hr`; M 41/42 `export_data` danh bạ → DENIED, admin ALLOWED. OT `test_export_only_own_rows_for_viewer`: viewer (có `base.group_allow_export`) xuất ngày công của mình OK, xuất ngày/phiên của đồng nghiệp → AccessError; HR manager xuất cả hai | PASS (OT); M công NOT_RUN |
| AT02-B | Nhân viên A | `search/read_group/search_count` với domain field private (`private_email`, `birthday`, lý do điều chỉnh) | Bị từ chối, không lộ qua đếm/sắp xếp | OT | OT: `search`/`search_count` theo `private_phone`, `identification_id` → AccessError/ValueError | PASS phần danh bạ; lý do điều chỉnh NOT_RUN |
| AT02-C | Nhân viên A | Đọc phiếu điều chỉnh/minh chứng/log của B | Không thấy (record rule own), file minh chứng không tải được | OT | | NOT_RUN |
| AT02-D | Ẩn danh / portal / tài khoản khóa | `/app/nhan-su`, `/app/cham-cong`, `/web/dataset/call_kw` | Về `/dang-nhap` hoặc 403; không payload nội bộ | OT, S, P | | NOT_RUN |
| AT03-A | Admin/HR manager | Mở Danh sách nhân viên, Hồ sơ cần bổ sung, Lưu trữ, Nhập đối chiếu | Giữ nguyên chức năng hiện có, không bị hạ readonly | OT, M, E2E | OT `test_hr_keeps_management_rights`; M admin: menu Tổng quan/Danh sách nhân viên/Nhập đối chiếu giữ, entry → Tổng quan HR; E2E admin `/app/nhan-su` → `/app/tp-hr`, không nhãn Chỉ xem | PASS |
| AT03-B | Admin được ủy quyền (không HR) | Mở HR | Thấy danh bạ chỉ xem + entry ủy quyền hiện có; không mở hợp đồng/lương/private | OT | | NOT_RUN |
| AT03-C | Nhân viên A | Hồ sơ cá nhân của mình | Self-service giữ allowlist hiện hành; tab **Công của tôi** chỉ dữ liệu của A | OT, E2E | | NOT_RUN |
| AT04-A | HR có quyền nhập | Xem trước file ưu tiên (2 sheet giống hệt) | Sheet thứ hai đánh dấu **Trùng**; đếm hợp lệ/trùng/xung đột/chưa mapping/thiếu giờ | OT `test_duplicate_sheets_and_reimport_never_double_count`: workbook synthetic 2 sheet giống hệt → 6 dòng: 3 hợp lệ, 3 Trùng, 2 ô trống, mã máy tự lập bảng mapping; parser `test_parse_report_kinds_and_dates`. M 18069 hai tệp đã gửi: tệp tuần 188 dòng (149 ghi nhận, 33 thiếu giờ, 6 cần kiểm tra, 46 ô trống); tệp 09–10/11 128 dòng, sheet thứ hai 64 dòng **Trùng**, 33 ghi nhận, 31 thiếu giờ; 0 chưa đối chiếu, 0 tên khác hồ sơ | PASS (U, OT, M) |
| AT04-B | HR có quyền nhập | Áp dụng 2 lần cùng file; áp file khác chứa cùng ngày/giờ | Lần sau 0 phiên mới; không nhân công | OT cùng test: áp lại cùng tệp → `same_file_batch_id` cảnh báo, 0 phiên mới; `test_half_punch_waits_then_completes_with_matching_pair`: tệp sau bổ sung giờ ra → ngày từ Thiếu giờ ra sang Đủ, `resolved_by_line_id`, version tăng | PASS (OT); S NOT_RUN |
| AT04-C | HR | Dòng mã máy không có hồ sơ / tên khác hồ sơ / thiếu giờ ra / giờ ra < giờ vào | Giữ chờ (Chưa mapping/Xung đột/Thiếu giờ ra/Cần kiểm tra), không tạo giờ giả | OT `test_unmapped_and_name_mismatch_never_create_employees` (Chưa mapping/Xung đột tên, không tạo hồ sơ), `test_conflict_is_kept_for_correction_not_overwritten` (giờ khác cùng ngày → Cần kiểm tra, giờ cũ giữ), `test_code_cells_stay_private_and_need_review` (ô mã ký hiệu → Cần kiểm tra, không lộ mã, không giờ); parser: thiếu giờ ra/ra trước vào/giờ `25:99` | PASS (U, OT) |
| AT04-D | HR | Sau nhập | Số nhân viên, `tp_employee_code`, user, phòng ban không đổi | OT unmapped/name-mismatch: số `hr.employee` không đổi sau áp dụng; parser không có đường ghi `hr.employee`; M snapshot trước/sau cài + nhập (`s2-dev-before.txt`/`s2-dev-after.txt`): hồ sơ 39, user 28, group_rels 101, phòng ban 13, hash nhân viên–phòng–user giữ nguyên, chỉ thêm dòng module; S snapshot trước/sau cài (`s2-server-before/after.json`): user 29, hồ sơ 39, mã 39, group_rels 100, phòng ban 13, md5 nhân viên–phòng–user và `web.base.url` giữ nguyên; sau nhập hồ sơ 39/39 | PASS (OT, M, S) |
| AT05-A | Hệ thống | Giờ `07:37` ngày 09/11/2026 Asia/Ho_Chi_Minh | Lưu UTC `00:37`, hiển thị lại `07:37`, ngày công 09/11 | OT `test_times_are_utc_and_workday_is_local`: `07:37` 09/11 → `check_in` UTC `00:37`, `in_time` `07:37`, giờ ghi nhận 9,47 | PASS (OT) |
| AT05-B | Hệ thống | Ca qua đêm (ra < vào ngày hôm sau), nhiều phiên trong ngày | Giờ ghi nhận = tổng phiên, không min/max mọi punch; qua đêm chỉ khi lịch cho phép, còn lại Cần kiểm tra | U, OT | | NOT_RUN |
| AT05-C | Hệ thống | Chưa có quy tắc công đã xác nhận | Công xác nhận **Chưa xác nhận** (null), không 0, không nghỉ không phép/đi muộn/lương | OT `test_units_need_a_confirmed_rule`: chưa quy tắc → `units_state` Chưa xác nhận, `units` null; quy tắc xác nhận 8–17 nghỉ 12–13 → 8,0 giờ = 1,00 công; thứ Ba 08:30–12:30 → 3,5 giờ = 0,44; đưa quy tắc về nháp → Chưa xác nhận. `test_board_month_and_day`: tổng dòng `units` null khi chưa xác nhận; E2E 18069: ma trận tháng và bảng ngày hiện **Chưa xác nhận** kèm ghi chú không phải nghỉ không phép/không trừ lương | PASS (OT, E2E) |
| AT05-D | Hệ thống | Ngày tương lai / ngày chưa có nguồn / ngày đang làm | Ô **Chưa đến**/**Chưa có nguồn** khác nhau, không tính vào KPI thiếu | OT `test_board_month_and_day`: ô không bản ghi có lô phủ → Không có giờ vào/ra, ngoài lô → Chưa có nguồn, ngày sau hôm nay → Chưa đến | PASS (OT bảng công); KPI S4 NOT_RUN |
| AT06-A | Nhân viên A | Gọi API Công của tôi với `employee_id` của B | Server bỏ qua tham số, luôn trả công của A | OT | | NOT_RUN |
| AT06-B | Nhân viên A | Tạo/sửa/hủy phiếu nháp của mình; sửa phiếu đã gửi; tạo phiếu cho B | Nháp OK; đã gửi bị chặn; phiếu cho B bị chặn | OT | | NOT_RUN |
| AT06-C | Người duyệt R (được phân công), A | R duyệt phiếu của A; A tự duyệt; R duyệt 2 lần | Duyệt 1 lần, công cập nhật + log; tự duyệt và duyệt lặp bị chặn | OT | | NOT_RUN |
| AT06-D | HR có quyền chốt | Chốt kỳ; sửa công trong kỳ chốt; đính chính có lý do | Sửa trực tiếp bị chặn; đính chính tăng version, giữ log gốc | OT | | NOT_RUN |
| AT07-A | Nhân viên, HR | Tổng quan công: KPI/chart/bảng/drilldown cùng kỳ/phòng | Cùng population/đơn vị; tương lai không tính; không chart 0 giả | OT, E2E | | NOT_RUN |
| AT07-B | Nhân viên | Bảng công ngày/tháng, lọc kỳ/phòng/nhân viên/trạng thái, chip, 10/20/50/100, back giữ lọc | Đúng count và đơn vị dòng | E2E | E2E admin 18069 (`e2e_s2.cjs`, 23/23): tháng 20/39 dòng, 30 cột ngày, cột Mã TP/tên sticky, tổng Đủ/Thiếu/Cần KT/Giờ/Công; chú giải đếm Đủ 182 · Thiếu 64 · Cần kiểm tra 6 · Không có giờ 60 · Chưa có nguồn 351 · Chưa đến 507; lọc tình trạng → chip, bấm ô mở ngày chỉ đọc, Back giữ chip/dòng/chế độ; bảng ngày đủ 9 cột; 10 dòng/trang; dòng “Dữ liệu cập nhật đến 10/11/2026” | PASS (E2E admin); E2E viewer NOT_RUN |
| AT07-C | Nhân viên | Viewport 375/390/768/1366/1440, zoom 200%, reduced-motion | Không tràn ngang trang, mobile mặc định thẻ, touch 44px | E2E | | NOT_RUN |
| AT08-A | Nhân viên | Đường ghi công native (`hr_attendance` systray/kiosk/PIN/controller) | Module `hr_attendance` không cài; không route ghi công nào cho viewer | M, S | M snapshot sau S2: `hr_attendance` uninstalled; `tp_hr_attendance` không phụ thuộc `hr_attendance`, không controller; S sau cài: `hr_attendance` uninstalled | PASS (M, S) |
| AT08-B | Nhân viên | Quyền cộng dồn group OR/rule | Không group mới nào cấp ghi `tp.hr.attendance.*` cho viewer | OT `test_assignments_drive_officer_group_and_capabilities`: nhóm `group_attendance_officer` chỉ đồng bộ theo phân công còn hiệu lực, ACL nhóm này chỉ đọc lô/dòng/log và tạo/sửa lô; không ACL ghi ngày công/phiên/kỳ/quy tắc cho viewer (`ir.access.csv`) | PASS (OT) |
| AT09-A | Vận hành | Deploy 18069 + server: backup, upgrade, restart | Exit 0, 0 ERROR, module version khớp commit | M, S | S1 `8fe067dc`: 18069 và server đều `tp_hr_workspace 20.0.1.12.0`, 0 ERROR; server 12/12 file khớp commit, snapshot trước/sau chỉ đổi version (user 29, hồ sơ 39, group_rels 100, `web.base.url` giữ nguyên); S2 M: backup `backup-s2-20261117T192301` → `-i tp_hr_attendance` exit 0, 0 ERROR; backup `backup-s2b-20261117T195054` → `-u tp_hr_attendance` exit 0, 0 ERROR ; S2 S `dc3c4c58`: backup `s2-20261117T200445` → 25/25 file khớp commit → `-i tp_hr_attendance` container tạm exit 0, 0 ERROR/CRITICAL → `docker start tp-odoo`, `tp-tunnel` vẫn chạy | PASS (S1, S2); S3–S4 NOT_RUN |
| AT09-B | Ẩn danh / admin | Sau restart: `/dang-nhap`, `/app`, avatar, SW, RPC | Không lỗi 5xx, không lộ dữ liệu phiên trước | S, P, E2E | S1: LAN + public `/dang-nhap` 200; `/odoo/danh-ba`, `/odoo/nhan-su` → `/app/...`; `/app/danh-ba` ẩn danh → `/dang-nhap?redirect=…`; E2E admin 18069 10/10. S2: LAN `/dang-nhap` 200, `/app/bang-cong` và `/app/nhap-cong` ẩn danh → `/dang-nhap?redirect=…`, `/odoo/bang-cong` → `/app/bang-cong`; public `/dang-nhap` 200, `/app/bang-cong` → `/dang-nhap`; bundle `web.assets_backend` server 200 có template bảng công; E2E admin 18069 23/23 | PASS phần ẩn danh S1, S2; admin server NOT_RUN |

## 3. Lệnh và kết quả thực tế

Log trong `.local/hr-attendance001/` (ignored).

**S1 — danh bạ chỉ xem (17/11/2026)**

| Bước | Lệnh / bằng chứng | Kết quả |
| --- | --- | --- |
| Lint | `ruff check custom_addons/tp_hr_workspace/models custom_addons/tp_hr_workspace/tests` | Đạt |
| OT | `odoo-bin -d tp_tanphat_test --test-tags /tp_hr_workspace:TestDirectoryReadonly --no-http --stop-after-init` (`s1-test.log`) | 0 failed, 0 error of 5 |
| OT hồi quy | `--test-tags /tp_hr_workspace,/tp_web_home,/tp_admin_delegation` (`s1-suite.log`) | 127 test: 118 đạt; 8 lỗi HttpCase do cổng 18069 đang chạy server dev (request bị dbfilter `^tp_tanphat_dev$` từ chối, kiểm DB dev không có bản ghi giả/ghi mới); 1 lỗi `TestDelegatedHrProfile.test_native_hr_views_only_request_allowed_fields…` (AccessError `hr.version`, batch ADMIN-DELEGATE/VI-WEB, không chạm bởi S1) |
| Backup M | `pg_dump -Fc` + zip filestore + `git archive HEAD custom_addons/tp_hr_workspace` (`backup-s1-20261117T182402/`, SHA256SUMS) | dump 9.713.850 byte, filestore 255.553.898 byte |
| Upgrade M | dừng 18069 → `-u tp_hr_workspace --no-http --stop-after-init` (`s1-upgrade-dev.log`) → khởi động lại | exit 0, 0 ERROR; cảnh báo icon cũ của `tp.hr.employee.form` |
| ORM M | `odoo-bin shell` user 41, 42, 2 rồi rollback (`s1_orm_check.py`) | 41/42: 39/39, export DENIED, private DENIED, menu Danh sách, entry Danh bạ; admin: giữ HR |
| E2E M | `node e2e_s1.cjs http://127.0.0.1:18069` admin (`e2e/s1-results.json`, ảnh) | 10/10 đạt, 0 lỗi console/5xx, 390px không tràn |
| Backup S | `docker stop tp-odoo` → `pg_dump -Fc` trong `tp-postgres` + `pg_restore -l` + tar filestore + tar nguồn `tp_hr_workspace` (`C:\TANPHAT-backups\hr-attendance001\s1-20261117T183334`, `SHA256SUMS.json`) | dump 9.344.454 byte, filestore 28.564.607 byte, restore-list đọc được |
| Release S | Gói 12 file từ `8fe067dc`; lần 1 dừng ở kiểm hash do `git archive` Windows đổi LF→CRLF; chuẩn hóa về LF rồi kiểm lại (`deploy-s1-resume.ps1`) | 12/12 khớp commit |
| Upgrade S | container tạm cùng image/network/volume: `-u tp_hr_workspace --no-http --stop-after-init` (`s1-upgrade-server.log`) → `docker start tp-odoo` (`deploy-s1-finish.ps1`) | 0 ERROR/CRITICAL; chỉ cảnh báo icon cũ; `tp-tunnel` tự kết nối lại `tanphatone.loca.lt` khi Odoo chạy lại (không restart tay) |
| Smoke S | curl ẩn danh LAN `192.168.1.73:8069` + public | xem AT09-B |

**S2 — nhập Excel và bảng công ngày/tháng (17/11/2026)**

| Bước | Lệnh / bằng chứng | Kết quả |
| --- | --- | --- |
| Lint | `ruff check custom_addons/tp_hr_attendance` | Đạt |
| U + OT | `odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_hr_attendance --test-tags /tp_hr_attendance --no-http --stop-after-init` (`test-s2-10.log`) | 0 failed, 0 error of 18 |
| Bundle | tải `web.assets_backend` sau restart (`bundle-check.log`) | Biên dịch được; OWL 3 không dùng `static props` |
| Backup M | `backup-dev.ps1 -Label s2` (`backup-s2-20261117T192301/`, `SHA256SUMS.txt`) | dump + restore-list + zip filestore + HEAD |
| Install M | dừng 18069 → `-i tp_hr_attendance --no-http --stop-after-init` (`s2-install-dev.log`) → khởi động lại | exit 0, 0 ERROR |
| Nhập M | `odoo-bin shell` admin, `import_dev.py` (xem trước → áp dụng; tệp trùng checksum bị bỏ qua) (`s2-import-dev.log`) | 252 ngày công (Đủ 182 / Thiếu 64 / Cần kiểm tra 6), 182 phiên, 34 mã máy, 0 chưa đối chiếu, hồ sơ 39 không đổi |
| Upgrade M | `backup-dev.ps1 -Label s2b` → `-u tp_hr_attendance` (`s2b-upgrade-dev.log`); tab “Dòng cần chú ý” chỉ lấy dòng chưa xử lý, biểu tượng `oi` thay Font Awesome | exit 0, 0 ERROR |
| E2E M | `node e2e_s2.cjs http://127.0.0.1:18069` admin (`e2e/s2-results.json`, 6 ảnh 1440/390) | 23/23 đạt, 0 lỗi console/5xx, 1440 và 390 không tràn ngang |
| Backup S | `deploy-s2.ps1`: `docker stop tp-odoo` → `pg_dump -Fc` + `pg_restore -l` + tar filestore (`C:\TANPHAT-backups\hr-attendance001\s2-20261117T200445`, `SHA256SUMS.json`) | dump 9.360.372 byte, filestore 27.994.481 byte |
| Release S | `git -c core.autocrlf=false archive dc3c4c58 custom_addons/tp_hr_attendance` (LF), từ chối nếu thư mục đã tồn tại | 25/25 file khớp hash commit |
| Install S | container tạm cùng image/network/volume `-i tp_hr_attendance --no-http --stop-after-init` (`s2-install-server.log`) → `docker start tp-odoo` | exit 0, 0 ERROR/CRITICAL (chỉ cảnh báo `Redundant default` của `tp_reporting` có sẵn) |
| Nhập S | `import-s2.ps1`: chép tạm 2 tệp đã gửi vào container, `odoo-bin shell` admin, xóa bản tạm host + container sau khi chạy (`s2-import-server.log`) | Giống 18069: 252 ngày công (182/64/6), 182 phiên, 34 mã máy, 0 chưa đối chiếu, hồ sơ 39 → 39 |
| Smoke S | curl ẩn danh LAN `192.168.1.73:8069` + public, tải bundle backend | xem AT09-B |

## 4. Gap đã biết

- HttpCase của `tp_hr_workspace`/`tp_web_home` không chạy được khi 18069 đang phục vụ
  `tp_tanphat_dev`; prompt không cho mở cổng test khác. Phần route được kiểm bằng smoke
  ẩn danh và E2E trên 18069.
- Chưa có ảnh giao diện bằng tài khoản nhân viên thường trên 18069 (không có mật khẩu
  tài khoản thật; không tạo user giả trên main).
- `hr.employee.public` native vẫn chứa `mobile_phone`/`phone`/`email`/sơ yếu lý lịch;
  danh bạ không hiển thị, RPC đọc trực tiếp vẫn trả theo baseline native.
