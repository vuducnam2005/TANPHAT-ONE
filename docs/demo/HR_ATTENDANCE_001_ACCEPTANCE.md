# HR-ATTENDANCE-001 + HR-DIRECTORY-READONLY-001 — Nghiệm thu

Ngày 17/11/2026 · Batch `CHG-20261117-020` · Prompt
[CLAUDE_HR_ATTENDANCE_001_AND_DIRECTORY_READONLY](../prompts/CLAUDE_HR_ATTENDANCE_001_AND_DIRECTORY_READONLY.md)
· Policy [HR_ATTENDANCE_001_POLICY](../security/HR_ATTENDANCE_001_POLICY.md).

Trạng thái: **S1_DIRECTORY_VERIFIED** (S2–S4 chưa chạy). Cột kết quả ghi `NOT_RUN` tới khi
có bằng chứng thật; không ghi PASS cho bước chỉ review mã.

## 1. Môi trường và tài khoản

| Ký hiệu | Môi trường | Ghi chú |
| --- | --- | --- |
| U | Unit thuần Python (parser/tính công), không nối DB | `custom_addons/tp_hr_attendance/tests/test_parser_unit.py` |
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
| AT01-B | Nhân viên A | RPC `create/write/unlink/copy/load` trên `hr.employee.public`, `hr.employee`, `tp.hr.attendance.day/session`, `tp.hr.attendance.period/rule/code` | AccessError mọi thao tác; không có ACL ghi | OT, M (`has_access`, không ghi thật) | OT `test_viewer_cannot_change_or_read_private_records`: create/write/unlink/copy/load bị chặn, số hồ sơ không đổi; M `has_access` ghi = False với 41/42. Model công chưa có (S2) | PASS phần danh bạ; phần công NOT_RUN |
| AT01-C | Nhân viên A | Đọc `hr.employee` trực tiếp, field private (`private_phone`, `birthday`, `identification_id`, `bank_account_id`, lương) qua `hr.employee.public`/`hr.employee` | Bị từ chối hoặc field không tồn tại trong payload | OT, M | OT: đọc `private_phone`/`identification_id`/`birthday` qua `hr.employee` → AccessError; field private không có trong `hr.employee.public`; M 41/42 đọc private → DENIED | PASS |
| AT02-A | Nhân viên A | `export_data` trên `hr.employee.public`; export ngày công người khác | AccessError; export ngày công của chính mình cho phép | OT, M | OT `test_export_only_for_hr`; M 41/42 `export_data` → DENIED, admin ALLOWED. Export công chưa có (S2) | PASS phần danh bạ; phần công NOT_RUN |
| AT02-B | Nhân viên A | `search/read_group/search_count` với domain field private (`private_email`, `birthday`, lý do điều chỉnh) | Bị từ chối, không lộ qua đếm/sắp xếp | OT | OT: `search`/`search_count` theo `private_phone`, `identification_id` → AccessError/ValueError | PASS phần danh bạ; lý do điều chỉnh NOT_RUN |
| AT02-C | Nhân viên A | Đọc phiếu điều chỉnh/minh chứng/log của B | Không thấy (record rule own), file minh chứng không tải được | OT | | NOT_RUN |
| AT02-D | Ẩn danh / portal / tài khoản khóa | `/app/nhan-su`, `/app/cham-cong`, `/web/dataset/call_kw` | Về `/dang-nhap` hoặc 403; không payload nội bộ | OT, S, P | | NOT_RUN |
| AT03-A | Admin/HR manager | Mở Danh sách nhân viên, Hồ sơ cần bổ sung, Lưu trữ, Nhập đối chiếu | Giữ nguyên chức năng hiện có, không bị hạ readonly | OT, M, E2E | OT `test_hr_keeps_management_rights`; M admin: menu Tổng quan/Danh sách nhân viên/Nhập đối chiếu giữ, entry → Tổng quan HR; E2E admin `/app/nhan-su` → `/app/tp-hr`, không nhãn Chỉ xem | PASS |
| AT03-B | Admin được ủy quyền (không HR) | Mở HR | Thấy danh bạ chỉ xem + entry ủy quyền hiện có; không mở hợp đồng/lương/private | OT | | NOT_RUN |
| AT03-C | Nhân viên A | Hồ sơ cá nhân của mình | Self-service giữ allowlist hiện hành; tab **Công của tôi** chỉ dữ liệu của A | OT, E2E | | NOT_RUN |
| AT04-A | HR có quyền nhập | Xem trước file ưu tiên (2 sheet giống hệt) | Sheet thứ hai đánh dấu **Trùng**; đếm hợp lệ/trùng/xung đột/chưa mapping/thiếu giờ | U, OT, M | | NOT_RUN |
| AT04-B | HR có quyền nhập | Áp dụng 2 lần cùng file; áp file khác chứa cùng ngày/giờ | Lần sau 0 phiên mới; không nhân công | OT, S | | NOT_RUN |
| AT04-C | HR | Dòng mã máy không có hồ sơ / tên khác hồ sơ / thiếu giờ ra / giờ ra < giờ vào | Giữ chờ (Chưa mapping/Xung đột/Thiếu giờ ra/Cần kiểm tra), không tạo giờ giả | U, OT | | NOT_RUN |
| AT04-D | HR | Sau nhập | Số nhân viên, `tp_employee_code`, user, phòng ban không đổi | OT, M, S | | NOT_RUN |
| AT05-A | Hệ thống | Giờ `07:37` ngày 09/11/2026 Asia/Ho_Chi_Minh | Lưu UTC `00:37`, hiển thị lại `07:37`, ngày công 09/11 | U, OT | | NOT_RUN |
| AT05-B | Hệ thống | Ca qua đêm (ra < vào ngày hôm sau), nhiều phiên trong ngày | Giờ ghi nhận = tổng phiên, không min/max mọi punch; qua đêm chỉ khi lịch cho phép, còn lại Cần kiểm tra | U, OT | | NOT_RUN |
| AT05-C | Hệ thống | Chưa có quy tắc công đã xác nhận | Công xác nhận **Chưa xác nhận** (null), không 0, không nghỉ không phép/đi muộn/lương | U, OT, E2E | | NOT_RUN |
| AT05-D | Hệ thống | Ngày tương lai / ngày chưa có nguồn / ngày đang làm | Ô **Chưa đến**/**Chưa có nguồn** khác nhau, không tính vào KPI thiếu | U, E2E | | NOT_RUN |
| AT06-A | Nhân viên A | Gọi API Công của tôi với `employee_id` của B | Server bỏ qua tham số, luôn trả công của A | OT | | NOT_RUN |
| AT06-B | Nhân viên A | Tạo/sửa/hủy phiếu nháp của mình; sửa phiếu đã gửi; tạo phiếu cho B | Nháp OK; đã gửi bị chặn; phiếu cho B bị chặn | OT | | NOT_RUN |
| AT06-C | Người duyệt R (được phân công), A | R duyệt phiếu của A; A tự duyệt; R duyệt 2 lần | Duyệt 1 lần, công cập nhật + log; tự duyệt và duyệt lặp bị chặn | OT | | NOT_RUN |
| AT06-D | HR có quyền chốt | Chốt kỳ; sửa công trong kỳ chốt; đính chính có lý do | Sửa trực tiếp bị chặn; đính chính tăng version, giữ log gốc | OT | | NOT_RUN |
| AT07-A | Nhân viên, HR | Tổng quan công: KPI/chart/bảng/drilldown cùng kỳ/phòng | Cùng population/đơn vị; tương lai không tính; không chart 0 giả | OT, E2E | | NOT_RUN |
| AT07-B | Nhân viên | Bảng công ngày/tháng, lọc kỳ/phòng/nhân viên/trạng thái, chip, 10/20/50/100, back giữ lọc | Đúng count và đơn vị dòng | E2E | | NOT_RUN |
| AT07-C | Nhân viên | Viewport 375/390/768/1366/1440, zoom 200%, reduced-motion | Không tràn ngang trang, mobile mặc định thẻ, touch 44px | E2E | | NOT_RUN |
| AT08-A | Nhân viên | Đường ghi công native (`hr_attendance` systray/kiosk/PIN/controller) | Module `hr_attendance` không cài; không route ghi công nào cho viewer | M, S | | NOT_RUN |
| AT08-B | Nhân viên | Quyền cộng dồn group OR/rule | Không group mới nào cấp ghi `tp.hr.attendance.*` cho viewer | OT | | NOT_RUN |
| AT09-A | Vận hành | Deploy 18069 + server: backup, upgrade, restart | Exit 0, 0 ERROR, module version khớp commit | M, S | | NOT_RUN |
| AT09-B | Ẩn danh / admin | Sau restart: `/dang-nhap`, `/app`, avatar, SW, RPC | Không lỗi 5xx, không lộ dữ liệu phiên trước | S, P, E2E | | NOT_RUN |

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

## 4. Gap đã biết

- HttpCase của `tp_hr_workspace`/`tp_web_home` không chạy được khi 18069 đang phục vụ
  `tp_tanphat_dev`; prompt không cho mở cổng test khác. Phần route được kiểm bằng smoke
  ẩn danh và E2E trên 18069.
- Chưa có ảnh giao diện bằng tài khoản nhân viên thường trên 18069 (không có mật khẩu
  tài khoản thật; không tạo user giả trên main).
- `hr.employee.public` native vẫn chứa `mobile_phone`/`phone`/`email`/sơ yếu lý lịch;
  danh bạ không hiển thị, RPC đọc trực tiếp vẫn trả theo baseline native.
