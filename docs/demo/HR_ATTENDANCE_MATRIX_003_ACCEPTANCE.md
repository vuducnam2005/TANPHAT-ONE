# HR-ATTENDANCE-MATRIX-003 — Tiêu chí nghiệm thu và bằng chứng

Phạm vi: `custom_addons/tp_hr_attendance` `20.0.2.0.0 → 20.0.3.0.0` (`DEC-058`, kế thừa `SIMPLE-002` `20.0.2.0.0` / `DEC-055` / `DEC-056` và chuẩn bộ lọc `DEC-044`).
Mọi kết quả dưới đây phân tách rõ **kiểm kỹ thuật tự động / READ-ONLY ORM**, **kiểm trình duyệt chưa đăng nhập / assets**, và các mục **`NOT_RUN`** hoặc **chờ người dùng nghiệm thu trực quan & nghiệp vụ**. Không đưa tệp Excel thật, họ tên hoặc giờ chấm công cá nhân vào Git; bằng chứng màn hình giữ cục bộ tại `.local/hr-attendance-matrix003/`.

## Tóm tắt xác nhận kỹ thuật vs Khoảng trống

- **Kiểm tĩnh & cú pháp**: `ruff check custom_addons/tp_hr_attendance` `0` lỗi; Python AST `32/32`; XML `16/16`; JS `node --check` `10/10`.
- **Unit test thuần (`DB-free`)**: `26/26 PASS` (`test_logic` `12`, `test_parser` `3`, `test_parser_late` `7`, `test_matrix_pure` `4`) + parse read-only tệp thực tế `09–15/11/2026` (`39` nhân viên, `7` ngày, `273` ô, `178` sự kiện, `95` ô trống, `0` lỗi).
- **Local `18069` (`tp_tanphat_dev`)**: nâng cấp `-u tp_hr_attendance` `20.0.2.0.0 → 20.0.3.0.0` (`post-migrate.py` `8.055s`, `exit 0`, `0 ERROR`); `LÔ-00001/00002/00005..00009` giữ nguyên `299` phiên, `365` ngày, `39` nhân viên; `LÔ-00005` tự chuyển `partial` do còn xung đột mở. ORM rollback + SQL read-only xác nhận `tp_matrix_data` (trang 1 `20`, trang 2 `19`, tổng `39`, lọc khoảng ngày `3` ngày vẫn giữ kỳ muộn `09–15/11`), `tp_compare_batches` (lô 5 vs lô 2 = `40` dòng gồm `1` `name_conflict` tách riêng, `42` `same`, `113` `only_a`, `22` `diff`, `1` `unready`), `tp_export_matrix` + `tp_export_compare` mở sạch bằng `openpyxl`, và chặn `AccessError` trên tài khoản thường đang hoạt động (`uid=34`, `5/5`) và `uid=5` (`6/6`). Bundle HTTP `web.assets_backend` phục vụ `matrix.scss`, `compare.js`, `matrix.js`, `upload.js` `200 OK`; Playwright ẩn danh `/web/health` `200`, `/dang-nhap`, `/app/bang-cong-theo-file` chuyển hướng đăng nhập, `0` lỗi console/page/5xx.
- **PC server (`tp_tanphat_dev`)**: deploy từ đúng archive commit `b7765bd1` (`62/62` tệp khớp SHA-256, `0` mtime bằng 0); backup đầy đủ `C:\TANPHAT-backups\hr-attendance-matrix003\ham003-20261118T171946` (`tp_tanphat_dev.dump` `9.701.510`B / `15.600` mục restore, `filestore.tar.gz` `34.387.973`B, `source-config.tar.gz` `257.100`B); `-u tp_hr_attendance` `exit 0`, `0 ERROR`. Snapshot sau áp giữ nguyên `355` phiên active, `456` ngày công, `35` mã máy, `78` bản muộn, `39` nhân viên, `12` user, nhóm quyền & `web.base.url`; migration dựng `195` `snapshot_person` (`1|39`, `2|78`, `3|39`, `4|39`) & `1.365` `snapshot_cell`, `LÔ-00003` gắn `partial`. ORM rollback trên `tp-odoo` xác nhận `SERVER_MATRIX_OK` (lô 4 `39` người/`18` ngày/`5` nhóm), `SERVER_COMPARE_OK` (lô 4 vs 3 = `40` dòng, `175 same`/`271 only_a`/`2 diff`/`4 unready`), `SERVER_EXPORT_OK` (`92×25`), `SERVER_ACL_OK` (`uid=34` `5/5` bị chặn). Thực tải CSS `/web/assets/9931cc6/web.assets_backend.min.css` (`1.592.899`B, SHA-256 `20a69ca1…`) và JS `/web/assets/2116504/web.assets_backend.min.js` (`8.431.465`B, SHA-256 `f535c84e…`) trực tiếp qua `https://hybrid-send-ready-ballot.trycloudflare.com` đạt `200 OK`, có `FileMatrix`, `tp_compare_batches`, `tp_resolve_compare_batch`, `tp_upload_files`, `o_tp_att_compare_screen`, không hồi quy `tp_hr_handle`; Playwright ẩn danh public `0` lỗi console/page/5xx.
- **`NOT_RUN` bắt buộc ghi rõ**:
  - Playwright đăng nhập thật bằng admin / importer trên `18069` và `PC server` (`admin` đã đổi mật khẩu lúc `07:24 UTC`, `planner.dev` đã archived; không đổi/mượn mật khẩu tài khoản thật theo quy tắc).
  - Bộ test ORM ghi/race `test_matrix_compare.py` trên DB test `18079` (không chạy suite tạo fixture trên DB đang dùng và không bắt buộc `18079` theo chỉ thị `17/11/2026`; logic ghi/lock/CAS kiểm bằng đọc code + `test_matrix_pure` + `test_matrix_compare.py` sẵn sàng cho lần chạy `tp_tanphat_test`).
  - Phản hồi trực quan của người dùng, nghiệm thu nghiệp vụ và cho phép pilot: `PENDING` người dùng đăng nhập kiểm thực tế sau khi tải lại trang.

## A. Đọc tệp nguồn & Snapshot bất biến (`M01–M07`)

| ID | Actor / Môi trường | Đầu vào / Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| `M01` | Parser v2 / Read-only local | Tệp máy chấm công thực tế (sheet `Report`, kỳ `09/11–15/11/2026`) | Đủ `39` nhân viên (gồm cả người trống cả kỳ), `7` cột ngày + thứ, `9` nhóm đơn vị nguồn, `178` ngày có giờ, `95` ô trống, `0` lỗi | `PASS` (đọc read-only parser v2 + kiểm `LÔ-00005` sau migration: `39` người, `273` ô = `178` + `95` trống) |
| `M02` | Parser v2 + Shell ORM | Mã NV Excel (`TP0xx`), ID máy (`11`, …), Chức vụ, Vắng mặt | Tách bạch `raw_source_code` (`TP037`), `raw_machine_code` (`11`), `hr_code` (`TP10011`), `source_title`, `absent_raw` | `PASS` (`test_matrix_pure` + shell `18069` `sample_code=TP037/11/TP10011`) |
| `M03` | Parser v2 (`test_matrix_pure`) | Kỳ `7 / 14 / 21 / 31` ngày, qua tháng và qua năm | Dò header động, lấy kỳ từ `Từ ngày … Đến ngày …` | `PASS` (`test_parser_v2_long_periods_14_21_31_days_and_merged_symbol`, `test_parser_v2_matrix_snapshot_and_codes`) |
| `M04` | Parser v2 (`test_matrix_pure` + `test_parser_late`) | Nhiều sheet, missing header | Mỗi sheet kỳ & snapshot riêng; từ chối bảng sai cấu trúc | `PASS` (`26/26` pure tests) |
| `M05` | Parser v2 (`test_matrix_pure`) | Blank, `missing_out`, `missing_in`, `code`, `multi`, `reversed`, `merged`, formula, late `inconsistent` | Giữ đúng trạng thái & raw, không tự bịa `17:00`, từ chối công thức chưa tính | `PASS` (`test_matrix_pure`) |
| `M06` | ORM Snapshot | Tính bất biến của `tp.hr.attendance.snapshot.person` / `.cell` | Khóa sửa/xóa trực tiếp; không đổi theo HR | `PARTIAL` (đảm bảo bằng `attendance_source_guard.py`; runtime ghi ORM chưa chạy suite `18079`) |
| `M07` | Migration `20.0.2.0.0 → 20.0.3.0.0` | Các lô cũ trên `18069` & `PC server` | Tự dựng snapshot có `snapshot_version=2` từ `file_data`, không đụng `session`/`day`/`employee` | `PASS` (`18069` `post-migrate.py` `8.055s`, `0` lỗi; `sessions=299`, `days=365`, `emps=39` nguyên vẹn) |

## B. Tải nhiều file & Quản lý lô nguồn riêng (`U01–U05`)

| ID | Actor / Môi trường | Đầu vào / Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| `U01` | `tp_upload_files` / `upload.js` | Nhiều `.xlsx` cùng lúc + tệp lỗi xen kẽ | Mỗi tệp đọc độc lập; tệp hợp lệ vẫn được lưu `preview` | `PARTIAL` (cài đặt & bundle JS `upload.js` verified qua HTTP asset; test DB ghi `test_matrix_compare.py` `NOT_RUN` trên main) |
| `U02` | ORM / Migration | Mã lô `LÔ-xxxxx`, tên gốc, checksum, sheet, người/giờ tải | Giữ tách từng bản tải | `PASS` (đã xác nhận `LÔ-00001..LÔ-00009` + cột bảng DB thật) |
| `U03` | Browser / OWL (`FileMatrix`) | Điều hướng sau tải -> bảng rộng toàn vùng | Chuyển thẳng `tp_hr_attendance.file_matrix`, CSS/JS biên dịch sạch | `PARTIAL` (assets HTTP CSS/JS chứa `FileMatrix` verified `0` lỗi; kiểm bấm tải file đã đăng nhập thật `NOT_RUN`) |
| `U04` | Server DB (`tp.hr.attendance.batch`) | Lưu bền vững qua `F5` / đóng hộp thoại | Lô vẫn nằm trong danh sách theo công ty | `PASS` (verified bảng & truy vấn `tp_matrix_batches`/`tp_matrix_data`) |
| `U05` | `tp_discard_batch` | Hủy lô `preview` có lý do vs từ chối hủy `partial`/`applied` | Giữ bản ghi audit `cancelled`, không cho hủy lô đã áp dụng | `PARTIAL` (logic cài đặt + viết trong `test_matrix_compare.py`, chưa chạy DB ghi `18079`) |

## C. Bảng công ma trận theo file, Bộ lọc & Xuất Excel (`T01–T08`)

| ID | Actor / Môi trường | Đầu vào / Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| `T01` | Shell ORM + `matrix.xml` | Mở `LÔ-00005` (`39` người / `7` ngày / `9` nhóm đơn vị) | 2 dòng `Vào/Ra`, header 2 tầng, nhóm đơn vị nguồn tách biệt | `PASS` (backend data `39` người / `7` ngày verified; HTML layout Desktop `NOT_RUN` do không login admin) |
| `T02` | Shell ORM `tp_matrix_data` | Phân trang `10/20/50/100` | Trang 1 = `20`, trang 2 = `19`, đủ `39` người kể cả ô trống/chưa map | `PASS` (`MATRIX_B5_OK` trên `18069`) |
| `T03` | `matrix.xml` / `matrix.js` / `matrix.scss` | Ẩn/hiện `Mã HR`, `ID máy`, `Chức vụ`, `Vắng mặt (Theo Excel)` | Sticky cột định danh trái không đè cột phụ | `PASS` (tĩnh + CSS biên dịch; kiểm hiển thị thực tế khi login `PENDING` user) |
| `T04` | `tp_matrix_data` + `matrix.xml` | Bộ lọc `DEC-044` + chip + `Xóa bộ lọc` | Khớp server & reset sạch | `PARTIAL` (filter ngày trên backend verified; thao tác UI thực `NOT_RUN`) |
| `T05` | Shell ORM `tp_matrix_data` | Lọc khoảng `10–12/11` trong kỳ `09–15/11` | `3` cột ngày, nhãn `sheet.period_label` giữ nguyên `09–15/11` | `PASS` (`MATRIX_SUB_OK` trên `18069`) |
| `T06` | `matrix.scss` / HTTP CSS bundle | Sticky 2 tầng, weekend tint, badge chữ | Biên dịch `matrix.scss` sạch, selector có mặt trong bundle | `PASS` (CSS HTTP bundle `1.592.872` bytes verified) |
| `T07` | `matrix.scss` / Playwright mobile | Responsive `390×844` + `prefers-reduced-motion` | Chế độ thẻ + bảng bật tắt, un-stick mobile | `PARTIAL` (quy tắc CSS có trong bundle; kiểm UI đã đăng nhập mobile `NOT_RUN`) |
| `T08` | Shell ORM `tp_export_matrix` | Xuất Excel từ Bảng dữ liệu theo file | Workbook `.xlsx` hợp lệ (`92×14`), chống formula injection | `PASS` (`EXPORT_OK` trên `18069` + `test_export_is_formula_safe`) |

## D. Đối chiếu hai file A/B & Chọn nguồn áp dụng (`C01–C10`)

| ID | Actor / Môi trường | Đầu vào / Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| `C01` | Shell ORM `tp_compare_batches` | Đối chiếu `LÔ-00005` (`09–15/11`) vs `LÔ-00002` (`09–10/11`) | Tách `Ngoài phạm vi file` vs `Ô trống trong kỳ`, `same_period=False` | `PASS` (`COMPARE_5_VS_2_OK` trên `18069`: `42 same`, `113 only_a`, `22 diff`, `1 unready`) |
| `C02` | Pure + Shell ORM | Phân 5 nhóm đối chiếu & lọc `Chỉ xem khác biệt` | Đếm đúng phạm vi theo từng nhóm | `PASS` (`test_compare_pure_classification_matrix` + `tp_compare_batches`) |
| `C03` | Pure + Shell ORM | Chưa map / `name_conflict` (`Hoàng Xuân Tiến` / `TP032`) | Không gộp theo tên, xếp `unready` | `PASS` (`total=40`, tách riêng `('Hoàng Xuân Tiến', 'name_conflict', 'TP032')`) |
| `C04` | Pure + `test_matrix_compare` | `missing_out` bên A vs `missing_in` bên B | Xếp `diff`, không tự nối Vào A + Ra B | `PASS` (pure classification; ORM ghi giữ ở `test_matrix_compare.py` `NOT_RUN` trên main) |
| `C05` | ORM `source_batch_ids` / `source_line_ids` | Hai file cùng giờ | 1 canonical session gắn đủ chứng từ đa lô | `PARTIAL` (schema + migration OK; chạy test ghi ở `test_matrix_compare.py` `NOT_RUN`) |
| `C06` | Pure + `tp_compare_batches` | Đối chiếu tổng Đi muộn đúng kỳ | Cùng kỳ so trực tiếp; khác kỳ báo không cộng chồng | `PASS` (`late_counts={'same': 0, 'only_a': 38, 'only_b': 0, 'diff': 0, 'unready': 1}` + `tp_export_compare` sheet 2) |
| `C07` | `tp_apply_compare_valid` | Áp dụng hợp lệ trước, giữ lại xung đột | Cập nhật `partial` khi còn xung đột mở | `PASS` phần trạng thái (`LÔ-00005` tự gắn `partial` từ xung đột hiện có); bước bấm `tp_apply_compare_valid` `NOT_RUN` trên DB chính |
| `C08` | `tp_resolve_compare_batch` + `resolution` | Chọn `use_a/use_b/keep_current/defer`, bắt buộc lý do, audit log + `superseded` | JS + Python verified cú pháp & live asset bundle | `PARTIAL` (`compare.js` + `tp_resolve_compare_batch` có mặt trong bundle & code; chưa chạy transaction ghi trên DB chính) |
| `C09` | Guard kỳ chốt & phiếu điều chỉnh | Chặn ghi đè kỳ `locked` & `source='correction'` | `blocked_reason` + `UserError` ở backend | `PARTIAL` (cài đặt ở backend & trong `test_matrix_compare.py`; DB test `NOT_RUN`) |
| `C10` | Advisory/row lock + CAS `expected_digest` | Chống stale snapshot & ghi đồng thời | Từ chối nếu `target_digest` lệch | `PARTIAL` (cài đặt trong backend; kiểm race đa phiên `NOT_RUN`) |

## E. Phân quyền, Đồng bộ & Bảo toàn môi trường (`S01–S04`)

| ID | Actor / Môi trường | Đầu vào / Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| `S01` | Nhân viên thường (`uid=34` active & `uid=5`) | Gọi `tp_matrix_data`, `tp_compare_batches`, `tp_upload_files`, `tp_export_matrix`, `.snapshot.person`, `.resolution` | `100% AccessError`; ẩn danh vào `/app/bang-cong-theo-file` về `/dang-nhap` | `PASS` (`uid=34`: `5/5`, `uid=5`: `6/6`, Playwright anonymous redirect verified) |
| `S02` | Bảng chấm công / Tổng quan / Công của tôi | Giữ nguyên số liệu hiệu lực, không cộng raw từ lô `preview`/`cancelled` | `sessions=299`, `days=365` (`18069`) & số liệu server nguyên vẹn | `PASS` (xác nhận trước/sau nâng cấp) |
| `S03` | `tp_admin_delegation` & foreign WIP | Không sửa `admin`, `groups`, `hr.employee`, foreign diff | Giữ nguyên 100% | `PASS` |
| `S04` | Vận hành `18069` & `PC server` | Backup + `-u tp_hr_attendance` + asset/health/public smoke | Backup đầy đủ từng môi trường, `0 ERROR`, public OK | `PASS` (`18069` & `PC server` commit `b7765bd1`, public bundle `9931cc6`/`2116504` `200 OK`, `0` lỗi console/5xx) |
