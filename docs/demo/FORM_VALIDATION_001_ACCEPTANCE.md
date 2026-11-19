# Thông báo rõ thông tin còn thiếu cho mọi màn thêm mới

Task FORM-VALIDATION-001, CHG-20261119-023; 19/11/2026.

Người dùng giao “tiếp tục là đi và bổ sung thêm: THÔNG BÁO RÕ THÔNG TIN CÒN THIẾU
CHO MỌI MÀN THÊM MỚI”. Quy chuẩn và bảng màn đã áp/chưa áp:
[TP_FORM_VALIDATION_STANDARD](../ui/TP_FORM_VALIDATION_STANDARD.md).

## Hành vi

- Bấm Lưu khi thiếu: không còn toast “Thiếu thông tin bắt buộc” tự biến mất. Khối
  “Chưa lưu được. Vui lòng kiểm tra N thông tin” nằm đầu form/popup, mỗi dòng là
  `Nhãn — Tab / Nhóm` và cách sửa; bấm vào mở tab, mở nhóm, cuộn và focus đúng ô.
- Ô lỗi khung đỏ, câu lỗi ngay dưới ô; tab có số lỗi; `*` chỉ ở ô thực sự bắt buộc
  và sửa được. Sửa ô nào thì dòng lỗi đó mất ngay. Dữ liệu đã nhập giữ nguyên.
- Bảng con: `Chứng chỉ — dòng 2: Tên chứng chỉ`, bấm vào đưa dòng vào chế độ sửa.
- Lỗi khi lưu từ backend hiện trong form theo loại: thiếu, sai định dạng/dữ liệu,
  trùng, ngày, không có quyền, bản ghi không còn, nghiệp vụ, kết nối, hệ thống. Câu
  backend giữ nguyên văn; lỗi hệ thống không lộ traceback/tên trường/giá trị.
- Popup/wizard/quick-create giữ lỗi bên trong và không đóng khi lỗi.
- Hồ sơ nhân viên: banner “khuyến nghị hoàn thiện (không chặn lưu)” chỉ liệt kê Mã
  nhân viên (khi đã lưu mà vẫn thiếu), Phòng ban, Chức vụ còn thiếu. Form mới không
  còn đòi “Hợp đồng/phiên bản” (`version_id` là field tính, ẩn khi chưa lưu).
- Hồ sơ của tôi (lưu hồ sơ, popup kinh nghiệm/học vấn, popup kỹ năng) và hộp thoại
  tài khoản đăng nhập dùng cùng khối lỗi (`InlineErrors`).

Không đổi quy định bắt buộc, quyền, dữ liệu, workflow hoặc API; không thêm giá trị giả;
backend vẫn kiểm mọi lần lưu.

## File

- Mới: `tp_web_home/static/src/validation/` (validation.js/xml/scss, inline_errors.js/xml),
  `tp_web_home/static/tests/validation/validation.test.js`.
- Sửa: `tp_web_home/static/src/inputs/inputs.scss` (gỡ rule `*` cũ), manifest Home
  20.0.1.10.0; `tp_hr_workspace` my_profile.js/xml, account_credentials.js/xml,
  views/workspace.xml (banner), views/employment_contract.xml (`version_id`), tests HOOT/
  Python, manifest HR 20.0.1.18.0.
- Docs: quy chuẩn validation, mục chỉ dẫn trong AGENTS.md, file này.

## Khôi phục CHG-020 bị ghi đè

Commit `5b9910b3` (CHG-20261119-022, tác vụ khác) dựng trên bản trước CHG-020 nên vô
tình gỡ tìm tên trực tiếp (`live_name_filter`) khỏi manifest/table.js/table.xml và phần
SCSS hồ sơ responsive; bản đó đã chạy trên PC server. Bản này gộp ba chiều
(base/CHG-020/CHG-022) cho 5 file `tp_hr_workspace`: `__manifest__.py`, table.js,
table.xml, employee_profile.scss, workspace.xml; giữ cả phần chỉ xem/bảo vệ dữ liệu của
CHG-022 lẫn tìm tên/hồ sơ của CHG-020.

## Kiểm thực

Bản kiểm: HEAD `5b9910b3` + 23 file scope (ghi trong commit này). Không ghi dữ liệu thật: mọi
kịch bản browser chạy với guard chặn toàn bộ RPC ghi (`web_save`, `create`, `write`,
`name_create`, `action_*`, `tp_save_*`…) và trả lỗi mô phỏng; không tạo hồ sơ, không
đổi quyền/khóa tài khoản.

| Hạng mục | Kết quả |
|---|---|
| HOOT `@tp_web_home` (gồm `validation.test.js` mới) | 57 test / 296 assertion PASS |
| HOOT `@tp_hr_workspace` | 50 test / 243 assertion PASS |
| HOOT `@tp_kd_workspace`, `@tp_equipment` | 22/85 và 2/4 PASS |
| HOOT toàn bộ module đã cài | 1429 PASS, 11 FAIL; cả 11 (`@web` tooltip/mobile, `@mail`, `@resource`) cũng fail trên HEAD. HEAD có 13 fail, thêm 2 test HR “department sections” hỏng do CHG-022 gỡ tìm tên; bản này PASS lại |
| Odoo `--test-tags /tp_hr_workspace,/tp_web_home` trên `tp_tanphat_test` | HEAD 102 test, bản này 103 test (thêm `test_new_employee_form_never_asks_for_the_computed_version` PASS); cùng 8 fail + 2 error có sẵn trên HEAD: `TestDashboardLock.test_job_filter_quality_catalog_export`, `TestUnifiedReadonlyBrowserHttp` (chờ KPI overview), `TestEmployeeDeleteHttp` ×5, `TestEmployeeLoginRename` (AccessError `tp_can_change_login`), `TestEmployeeLoginRenameHttp` (chờ `.o_form_view`), `TestHomeMenu.test_module_owns_only_the_home_action_and_menu`. Không regression; chưa sửa các lỗi có sẵn này |
| Browser — hồ sơ nhân viên mới 1440/768/390 | Lưu khi trống: khối lỗi chỉ có “Tên nhân viên — Thông tin chung / Vui lòng nhập Tên nhân viên.”; 0 toast; câu dưới ô; 1 dấu `*` + dòng giải thích; khối nằm trong tầm nhìn; bấm lỗi focus ô `name`; nhập tên thì khối và câu dưới ô mất ngay; không tràn ngang; 0 lỗi console |
| Browser — 6 loại lỗi lưu từ server (form Phòng ban) | trùng/ngày/quyền/nghiệp vụ/hệ thống hiện đúng tiêu đề và câu backend trong form; lỗi hệ thống chỉ câu chung; mất kết nối không hiện sai; không lộ tên trường; dữ liệu đã nhập giữ nguyên; hộp thoại native vẫn giữ |
| Browser — bảng con và popup dòng 1440/390 | “Thiết bị nhập — dòng 1: Phân loại / Tên thiết bị / Tình trạng khi nhận”, tab có số 3, bấm focus `category_id` trong dòng; popup dòng giữ khối lỗi bên trong, không bị footer che, focus đúng ô; 0 toast; không tràn ngang |
| Browser — quick-create Phòng ban | lỗi trùng: popup “Tạo Phòng ban” vẫn mở, khối lỗi trong popup, giữ tên đã nhập |
| Browser — tìm tên trực tiếp 1440/390 | không còn thanh tìm kiếm lớn; gõ “N” lọc 37/39, “Na” còn 1, chip “Họ tên: Na”; mobile mở qua nút “Bộ lọc”; không tràn ngang; 0 lỗi console |

Kết quả và ảnh: `.local/validation001/browser-receipt/*.json`, `.local/validation001/shots/`
(`employee-*-main-*.png`, `live-search-Na-main-*.png`, `server-*.png`, `rows-*`, `popup-*`, `quick-create-*`).

## Môi trường

| Môi trường | Trạng thái ở mốc ghi này |
|---|---|
| Local `tp_tanphat_dev` (18069) | Đã upgrade `tp_hr_workspace` 20.0.1.17.0 → 20.0.1.18.0, `tp_web_home` 20.0.1.9.1 → 20.0.1.10.0; exit 0, 0 ERROR. `tp_hr_attendance` 20.0.3.1.0 → 20.0.3.3.0 do là module phụ thuộc: DB local còn chậm so với HEAD (CHG-005/012 đã chạy trên PC). Snapshot nhân viên/user/nhóm/roster/phiên bản/thiết bị/ledger/công/khóa/tài khoản/công ty/resource/base_url không đổi |
| Backup local | `.local/validation001/main-backup-20261119T181303`: dump + `pg_restore -l`, filestore các file DB tham chiếu (0 thiếu), config riêng, source cũ, SHA256 |
| Test `tp_tanphat_test` (18079) | Chỉ chạy test; backup trước mỗi lần `.local/validation001/backup-test-db-20261119-180209.dump`, `-180704.dump`. `tp_branding` (chưa track, không nằm trong addons path kiểm thử) bị đánh dấu `to upgrade` trong DB test |
| PC server | Đã áp `720d7fa9` (CHG-20261119-024): HR 20.0.1.17.0 → 20.0.1.18.0, Home 20.0.1.9.1 → 20.0.1.10.0, exit 0 / 0 ERROR; trước deploy nguồn 23 file khớp HEAD `5b9910b3`. Xem receipt dưới |

## Giới hạn

- Hồ sơ của tôi và hộp thoại tài khoản chỉ kiểm bằng HOOT (tài khoản admin không có
  hồ sơ nhân viên); chưa kiểm bằng người dùng thật.
- Chưa physical device/iOS/Safari; kiểm desktop/tablet/mobile bằng viewport.
- Các màn ghi ở mục 7 của quy chuẩn chưa chuyển sang khối lỗi trong form.
- Hộp thoại lỗi RPC native của Odoo vẫn xuất hiện cùng khối lỗi trong form.
- Ảnh chụp và log chỉ lưu trong `.local/validation001/` (bị ignore) để không đưa dữ
  liệu nhân viên vào Git. Technical verification khác nghiệm thu nghiệp vụ.

## Receipt PC server — CHG-20261119-024

- Commit app `720d7fa9192e3349c0fd5845a3a0d232d2f685cf`; gói `form-validation023`, 29 file, checksum từng file khớp sau giải nén.
- Trước deploy: kiểm drift nguồn 23 file = HEAD `5b9910b3`; mọi module `tp_*` có phiên bản nguồn = DB.
- Backup `C:\TANPHAT-backups\form-validation001\form-validation023-20261119T182936`: `tp_tanphat_dev.dump` + `restore-list.txt` (15790 mục), `filestore.tar.gz` (634 mục), source/config, SHA256SUMS.
- Upgrade `-u tp_hr_workspace,tp_web_home` exit 0, 0 ERROR; snapshot trước/sau giống hệt ngoài phiên bản 2 module.
- Public `https://eight-championships-launches-plaintiff.trycloudflare.com`: `/web/health` 200, `/dang-nhap` 200; bundle JS `e8b9a2c9…`, CSS `5b4b6a4e…` bằng SHA256 bản server, có `tp_web_home.ValidationSummary`, `InlineErrors`, `HrEmployeeFilterBar`, `.tp_validation_summary`.
- Server còn 6 file JS chưa commit của phiên khác và `tp_branding` chưa track (đã có trước bản này); bản này không thay đổi chúng.
- Người dùng bấm Ctrl+F5 để tải bundle mới.
