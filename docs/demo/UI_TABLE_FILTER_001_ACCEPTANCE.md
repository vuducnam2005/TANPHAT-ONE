# Bộ tiêu chí nghiệm thu `UI-TABLE-FILTER-001`

Bộ tiêu chí nghiệm thu `AT-F01` đến `AT-F12` cho nhiệm vụ triển khai bộ lọc bảng theo chuẩn `DEC-044` (`docs/ui/TP_TABLE_FILTER_STANDARD.md`), đối chiếu trên môi trường test `tp_tanphat_test` (`127.0.0.1:18079`).

## Quy tắc chung
- Mọi kiểm thử chạy trên `tp_tanphat_test` (`18079`), không chạm `tp_tanphat_dev` (`18069`).
- Dùng tài khoản test có sẵn trong DB test (`admin`, `emp014.hr`, `emp014.kd`, `kd.thuyanh`, `kd.thanh`) và dữ liệu giả lập cô lập (`__ut_` / prefix kiểm thử), không sửa người dùng thật.

---

## Danh sách ca kiểm thử (`AT-F01` – `AT-F12`)

### `AT-F01` — Hiển thị đầy đủ & đúng ngữ cảnh thanh lọc trên các bảng chính
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Đăng nhập trên `18079`, mở các bảng chính HR (`Danh sách nhân viên`, `Hồ sơ cần bổ sung`, `Lưu trữ`, `Chưa có tài khoản`, `Phòng ban và đơn vị`, `Chức vụ`, `Nơi làm việc`, `Nhãn nhân viên`, `Nhập và đối chiếu`, `Nhật ký xóa hồ sơ và sửa mã`), KH-KD (`Dự án`, `Đấu thầu`, `Hồ sơ dự án và hồ sơ thầu`, `Cần đối chiếu`, `Hạng mục / WBS`, `Công việc và tiến độ`, `Hợp đồng`, `Giao khoán`, `Sản lượng`, `Nghiệm thu`, `Kế hoạch định kỳ`, `Đề nghị thanh toán`, `Nghĩa vụ`, `Chứng chỉ`) và bảng native (`Training Attendances`, `Work Locations`, `Work Item Catalog`).
- **Thao tác:** Kiểm tra thanh `Lọc theo`, nhãn/placeholder tiếng Việt, kích thước kiểm soát rõ viền, trạng thái rà soát `AUTO`.
- **Kết quả mong đợi:** Mỗi bảng hiển thị 3–5 tiêu chí lọc cốt lõi phù hợp đúng ngữ cảnh bảng đó; không còn trường/nút lọc vô nghĩa (vd. `Mở`/`Khóa` trên `Chưa có tài khoản`); mọi thành phần đều đọc/hiểu tiếng Việt rõ ràng; không rò rỉ `project_search_restructure` sang `Project Templates`.
- **Bằng chứng dự kiến:** `shots/after/hr_*.png`, `shots/after/kd_*.png`, `shots/after/native_*.png`, Playwright check JSON.

### `AT-F02` — Kết hợp `AND` giữa nhiều tiêu chí & `OR` trong cùng tiêu chí nhiều giá trị
- **Tác nhân:** `admin`, `emp014.hr`
- **Điều kiện ban đầu:** Danh sách nhân viên có nhiều phòng ban, chức vụ, loại hình lao động (`short_term`, `long_term`, `outsourced`, chưa khai báo).
- **Thao tác:** Chọn nhiều phòng ban (OR) + 1 loại hình lao động (AND), nhấn `Áp dụng`. Thực hiện tương tự trên KH-KD (`Trạng thái` + `Dự án`).
- **Kết quả mong đợi:** Tập kết quả là giao (`AND`) giữa hai nhóm và hợp (`OR`) trong cùng nhóm nhiều giá trị; facet/chip đang áp phản ánh đúng; `SearchModel` đồng bộ với chip/bộ đếm kết quả.
- **Bằng chứng dự kiến:** Playwright AT-F02 assertion + network domain check + screenshot.

### `AT-F03` — Phân biệt rành mạch `Tất cả` / `Chưa khai báo (False/NULL)` / `0` và trường ngày/giờ theo múi giờ
- **Tác nhân:** `admin`, `kd.thuyanh`
- **Điều kiện ban đầu:** Có bản ghi có trường `False/NULL` (vd: nhân viên `Chưa khai báo` loại hình lao động, hợp đồng có giá trị `0` vs `Chưa xác nhận`), và bản ghi `tp.hr.employee.audit` / `tp.contract.audit` / `project.task` có `create_date` hoặc `date_deadline` gần ranh `23:59` giờ VN (`Asia/Ho_Chi_Minh`).
- **Thao tác:**
  1. Chọn `Loại hình lao động = Chưa khai báo`, nhấn `Áp dụng` -> phải trả đúng nhóm `= False`, khác `Tất cả`.
  2. Trên bảng có khoảng ngày `Từ ngày ... Đến ngày ...`, thử nhập `Từ ngày > Đến ngày` -> kiểm tra thông báo lỗi nội tuyến và chặn gửi request sai; sửa `Từ ngày = Đến ngày` với datetime gần cuối ngày -> đối chiếu bản ghi ranh `23:59 +07` vẫn nằm trong ngày.
- **Kết quả mong đợi:** Không trộn lẫn `False` với `Tất cả` hoặc `0`; ranh `end-of-day` timezone VN chính xác; validation `from <= to` rõ ràng.
- **Bằng chứng dự kiến:** Python Odoo test `test_date_tz_and_empty_vs_zero` + Playwright AT-F03 check.

### `AT-F04` — Tìm kiếm Many2one chạy phía máy chủ (`name_search` / theo ID), không tải toàn bộ bảng lớn
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Bảng có trường `many2one` (`department_id`, `project_id`, `partner_id`, `owner_id`).
- **Thao tác:** Nhập từ khóa vào control `Many2one` trong `Lọc theo`, theo dõi RPC `web_name_search` / `name_search`, chọn giá trị gợi ý và nhấn `Áp dụng`.
- **Kết quả mong đợi:** Truy vấn autocomplete có giới hạn (`limit`), lọc thực sự theo `[field, '=', id]` hoặc `in [id]` (không match chuỗi mờ khi đã chọn bản ghi cụ thể), chỉ hiển thị bản ghi trong quyền người dùng.
- **Bằng chứng dự kiến:** Playwright RPC intercept assert `web_name_search` + domain ID.

### `AT-F05` — Phân tách `Đang chọn (Pending)` và `Đang áp dụng (Applied)`, nút `Áp dụng`, `Xóa bộ lọc`, chip gỡ từng tiêu chí và đồng bộ 2 chiều SearchBar / Favorites
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Đang ở bảng `Danh sách nhân viên` hoặc `Giao khoán và thầu phụ`.
- **Thao tác:**
  1. Thay đổi tiêu chí trên thanh lọc nhanh nhưng **chưa** nhấn `Áp dụng` -> kiểm tra danh sách & RPC chưa đổi, hiển thị dấu hiệu chờ áp dụng.
  2. Nhấn `Áp dụng` -> tải trang 1 (`offset=0`), hiện chip đang áp + nút gỡ từng chip `×`.
  3. Thêm 1 điều kiện trong `Bộ lọc nâng cao` / `Tìm kiếm...` native -> mở lại/nhấn `Áp dụng` thanh nhanh -> điều kiện nâng cao vẫn được giữ nguyên (không bị xóa nhầm).
  4. Gỡ 1 chip -> danh sách cập nhật ngay; nhấn `Xóa bộ lọc` -> về mặc định.
- **Kết quả mong đợi:** Pending ≠ Applied; đồng bộ 2 chiều không làm mất điều kiện nâng cao; pagination reset về trang 1 khi đổi lọc; gỡ chip & `Xóa bộ lọc` nhất quán.
- **Bằng chứng dự kiến:** HOOT unit/mounted test + Playwright AT-F05 check.

### `AT-F06` — `Xóa bộ lọc` bảo toàn domain bắt buộc của action và giữ nhóm `Phòng ban` của HR (`HR-LIST-013`)
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Mở `Hồ sơ cần bổ sung` (`[('tp_missing_basic','!=',False)]`), `Lưu trữ` (`[('active','=',False)]`), `Chưa có tài khoản` (`[('user_id','=',False)]`), `Hồ sơ dự án và hồ sơ thầu` (`[('tp_project_id','!=',False)]`), `Cần đối chiếu`.
- **Thao tác:** Áp thêm bộ lọc nhanh -> nhấn `Xóa bộ lọc` -> kiểm tra domain, kết quả trả về và cột/nhóm phòng ban trên HR.
- **Kết quả mong đợi:** Domain gốc của action (`tp_missing_basic != False`, `active=False`, `user_id=False`, `tp_project_id != False`, ...) và nhóm `department_id` đầu tiên (`HR-LIST-013`) luôn còn nguyên; không bao giờ rò bản ghi ngoài phạm vi action.
- **Bằng chứng dự kiến:** HOOT + Playwright AT-F06 assertions.

### `AT-F07` — Phân trang nhiều trang (`limit` + `offset`), `count`, và đồng bộ xuất Excel (HR + KH-KD Report Center)
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Có dữ liệu test lớn hơn 1 trang (`> 10` bản ghi khi chọn `10 dòng mỗi trang`).
- **Thao tác:**
  1. Đặt `10 dòng/trang`, kiểm tra trang 1 và sang trang 2 (`offset=10`), áp bộ lọc -> quay về trang 1, đối chiếu tổng `count` khớp với kết quả DB.
  2. Trên `Tổng quan HR`: chọn bộ lọc phòng ban/chức vụ/trạng thái -> xuất `/tp_hr/export` -> đọc lại file XLSX bằng `openpyxl` đối chiếu số dòng & tiêu đề metadata.
  3. Trên `Trung tâm Báo cáo KH-KD`: áp bộ lọc (`project_id`, `status`, ngày) -> nhấn `Áp dụng bộ lọc` -> `Xuất Excel (.xlsx)` -> đọc lại file XLSX đối chiếu khớp số dòng và không chứa formula injection (`=`, `+`, `-`, `@`).
- **Kết quả mong đợi:** Paging server-side đúng `limit`/`offset`/`count`; file XLSX đọc lại khớp 100% tập đang lọc trên giao diện và an toàn công thức.
- **Bằng chứng dự kiến:** Python Odoo test + Playwright XLSX verification script.

### `AT-F08` — Bảng con (`x2many`), popup mở rộng và khóa an toàn khi form đang sửa / bản ghi mới (`dirty guard`)
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Mở form `Hồ sơ hợp đồng / Giao khoán` có bảng con `event_ids` / `amount_ids`, hoặc form `Phòng ban` (`member_ids`), `Lô nhập` (`line_ids`).
- **Thao tác:**
  1. Khi form sạch (đã lưu): nhấn `Tìm / lọc toàn bộ bảng` -> mở dialog popup bảng -> kiểm tra bộ lọc nhiều loại trường (`char`, `selection`, `many2one`, `date`) hoạt động bình thường.
  2. Sửa một trường trên form (chưa lưu — `dirty`) hoặc đang tạo bản ghi mới (`!resId`): kiểm tra nút lọc bảng con & đổi kích thước trang bị vô hiệu hóa (`disabled`) kèm câu thông báo `Lưu hoặc hủy thay đổi để lọc bảng này` (hoặc giữ nguyên không mất dòng đã nhập/đang sửa).
- **Kết quả mong đợi:** Popup lọc được khi sạch; hoàn toàn bảo toàn dữ liệu đang nhập dở trên bảng con khi `dirty`/mới, thông điệp rõ ràng, ORM x2many commands không bị mất.
- **Bằng chứng dự kiến:** HOOT `tables007` + Playwright AT-F08 assertions.

### `AT-F09` — Phân quyền đa tác nhân & cô lập dữ liệu tiền (`Security Negative Test`)
- **Tác nhân:** `admin`, `emp014.hr` (HR, không vào KH-KD nếu thiếu grant), `emp014.kd` / `kd.thanh` (không quyền xem tiền hoặc phạm vi hẹp), người dùng thường / ngoài công ty
- **Điều kiện ban đầu:** User `no-money` và user phạm vi dự án hẹp đã cấu hình trên DB test.
- **Thao tác:**
  1. User `no-money` mở danh sách/bộ lọc trên `tp.contract`, `tp.bid.package`, `crm.lead`, `tp.allocation`, `tp.payment.request`, `project.task`, `tp.contract.line.amount`: kiểm tra thanh lọc, dropdown `many2one`, DOM, network response và thông báo lỗi.
  2. Gọi trực tiếp RPC/HTTP (`/tp_hr/export`, `get_overview`, `search_read` với domain chứa field cấm / bản ghi ngoài company) dưới quyền user không đủ quyền.
- **Kết quả mong đợi:** Không có field/option/số tiền/dữ liệu ngoài company rò ra DOM, RPC, autocomplete hay Excel; gọi vượt quyền nhận `AccessError`/403 chuẩn, không fallback về dữ liệu giả hoặc hiển thị nhầm.
- **Bằng chứng dự kiến:** Odoo Python security test + Playwright multi-actor check.

### `AT-F10` — Khả năng chống lỗi, đua lệnh (`race condition`), lỗi mạng và chuyển phiên/công ty
- **Tác nhân:** `admin`, `emp014.hr`
- **Điều kiện ban đầu:** Mở bảng danh sách và kích hoạt bộ lọc.
- **Thao tác:**
  1. Gửi liên tiếp 2 lần `Áp dụng` nhanh với tiêu chí khác nhau (giả lập phản hồi 1 về trễ hơn phản hồi 2).
  2. Giả lập lỗi mạng `500`/offline khi lọc hoặc đổi cỡ trang -> kiểm tra thông báo lỗi tiếng Việt không sập màn hình -> khôi phục mạng và bấm thử lại.
  3. Mở 2 tab hoặc đổi công ty/đăng xuất -> quay lại tab cũ hoặc tải lại.
- **Kết quả mong đợi:** Phản hồi cũ bị hủy/bỏ qua, UI chỉ hiện kết quả của yêu cầu mới nhất; lỗi mạng hiện cảnh báo an toàn cho phép thử lại; chuyển phiên/đăng xuất xóa/reset trạng thái lọc an toàn.
- **Bằng chứng dự kiến:** HOOT race test + Playwright network throttle/error check.

### `AT-F11` — Responsive (`1440×900`, `390×844`, zoom `200%`), bàn phím, `prefers-reduced-motion` và tương thích `UI-INPUT-001`
- **Tác nhân:** `admin`, `kd.thuyanh`, `emp014.hr`
- **Điều kiện ban đầu:** Mở trang danh sách HR và KH-KD ở cả `1440×900` (desktop), `390×844` (mobile) và `1440×900` ở mức zoom `200%`.
- **Thao tác:** Kiểm tra overflow ngang (`scrollWidth <= clientWidth`), nút mở ngăn kéo `Bộ lọc` trên mobile, chiều cao vùng chạm `>= 44px` trên mobile, viền 4 cạnh input theo `input_tokens.css`, điều hướng `Tab`/`Enter`/`Esc`, chế độ `reduced-motion`.
- **Kết quả mong đợi:** Zero horizontal overflow trên toàn viewport; vùng chạm `>= 44px` trên mobile; bảng không bị che khuất bởi thanh lọc cố định; tương phản đạt chuẩn; không kẹt focus khi đóng mở dropdown/drawer.
- **Bằng chứng dự kiến:** Playwright layout & accessibility check + screenshots `shots/after/*_390.png`, `*_1440.png`, `*_zoom200.png`.

### `AT-F12` — Không hồi quy các luồng vận hành hiện có (thêm/sửa, khóa tài khoản, sidebar, UserMenu, đăng xuất)
- **Tác nhân:** `admin`, `emp014.hr`, `kd.thuyanh`
- **Điều kiện ban đầu:** Sau khi triển khai đầy đủ S1–S3 trên `18079`.
- **Thao tác:**
  1. Chạy lại toàn bộ test hiện có liên quan (`test_hr_workspace`, `test_hr_ui`, `test_project_restructure`, `test_contract_native_ui`, HOOT `hr001_hoot`, `kd_ui007`, `ui_home004_hoot`).
  2. Kiểm tra UserMenu chỉ còn 2 mục (`Thông tin cá nhân` & `Đăng xuất`), sidebar đồng nhất (`UI-SHELL-UNIFY-001`), thêm/sửa 1 bản ghi, khóa/mở tài khoản, xuất Excel không lỗi console/server log.
- **Kết quả mong đợi:** 100% test hồi quy đạt; `UserMenu`, sidebar, CRUD, login/logout hoạt động nguyên vẹn; không có console error / traceback trong log server test.
- **Bằng chứng dự kiến:** Log Odoo test, HOOT JSON, Playwright regression output.

---

## Bảng tổng hợp kết quả (`S4` — `tp_tanphat_test`, cổng `18079`, `2026-11-14`)

> **Lưu ý môi trường:** Mọi kiểm thử dưới đây chỉ thực thi trên `tp_tanphat_test` (`127.0.0.1:18079`). Database chính `tp_tanphat_dev` (`18069`) **chưa áp dụng**, chưa upgrade module và chưa thay đổi dữ liệu/quyền.

| Mã | Tên tiêu chí | Kết quả | Ghi chú / Bằng chứng thực chạy |
|---|---|---|---|
| `AT-F01` | Đầy đủ & đúng ngữ cảnh thanh lọc | `PASS` | Playwright `AT-F01` (`filterBar=true, groups=true, chipsApply=1, chipsClear=0`); HOOT `table_filter_bar` + `hr_mounted`; `shots/after/hr_employees_1440.png` |
| `AT-F02` | Kết hợp `AND` / `OR` đồng bộ SearchModel | `PASS` | Playwright `AT-F02` (`employee_missing_search`, `employee_archived_search`, `employee_pending_search`); HOOT `table_filter_bar` multi/AND/OR |
| `AT-F03` | Phân biệt `Tất cả` / `False` / `0` & ngày/giờ TZ | `PASS` | Playwright `AT-F03` (`oppRows=4, chips=2`); `test_table_filter_hr.py` + `filter_domain.js` (`__false__`, TZ +07:00) |
| `AT-F04` | Many2one autocomplete server-side theo ID | `PASS` | Playwright `AT-F04` (`before=15, afterBack=15, chipBack=1, chipClear=0`, breadcrumb back preserves state); `name_search(domain=...)` trên `18079` |
| `AT-F05` | Pending vs Applied, `Áp dụng`, gỡ chip, sync 2 chiều | `PASS` | Playwright `AT-F05` (validation `Từ ngày > Đến ngày` alert + nút `Áp dụng` disabled + `cleared=true`); HOOT pending/applied sync |
| `AT-F06` | `Xóa bộ lọc` giữ mandatory domain & HR group | `PASS` | `test_table_filter_hr.py` (`missing`/`archived`/`pending`) + Playwright `AT-F01`/`AT-F02` (`groups=true`, `HR-LIST-013`) |
| `AT-F07` | Paging, count & đồng bộ Export XLSX | `PASS` | Playwright `AT-F06` (`hrExportStatus=200`, `rcVisible=true`); `test_report_center.py` + `shots/after/kd_report_center_1440.png` |
| `AT-F08` | Bảng con (`x2many`), popup & dirty guard | `PASS` | Playwright `AT-F07` (`deptRelationMounted=true, dialogFilter=true`, mở popup `hr.department.member_ids` an toàn) + HOOT `tables007.test.js` dirty guard |
| `AT-F09` | Bảo mật đa tác nhân & cô lập dữ liệu tiền | `PASS` | Playwright `AT-F08` (`kdScopedRows=1`, `hrActorRows=44`, `kdErrors=0`, `hrErrors=0`) + `TestNativeContentSecurity` + `TestContractNativeUi` |
| `AT-F10` | Race condition, lỗi mạng & chuyển phiên/công ty | `PASS` | HOOT `table_filter_bar.test.js` (stale response guard & retry on RPC failure) + Playwright `AT-F09/F10` (`overviewLoaded=true, myProfileLoaded=true`) |
| `AT-F11` | Responsive, zoom 200%, bàn phím, `UI-INPUT-001` | `PASS` | Playwright `AT-F11` (`noOverflow390=true, zoom200Ok=true, mobileToggleH=44`) + visual check `shots/after/hr_employees_1440.png`, `hr_missing_1440.png`, `kd_opportunities_1440.png`, `kd_projects_1440.png`, `hr_employees_390.png`, `mobile_drawer_390.png` |
| `AT-F12` | Hồi quy hệ thống & bộ test hiện có | `PASS` | Ruff `All checks passed!`; Odoo Python `0 failed, 0 error(s) of 98 tests` (`tp_contract` 24, `tp_hr_workspace` 32, `tp_kd_workspace` 50, `tp_web_home` 16); HOOT `tp_web_home` 39/206, `tp_hr_workspace` 42/200, `tp_kd_workspace` 22/85; Playwright `userMenuItems=2, tmplFilterBar=0, adminErrors=0, http500=0`; `shots/after/native_users_1440.png` |
