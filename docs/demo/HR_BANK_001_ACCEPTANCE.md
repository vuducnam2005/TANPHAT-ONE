# BANK-001 — Nghiệm thu tài khoản ngân hàng và rà soát "Thông tin cá nhân"

Phạm vi: module mới `tp_hr_bank` 20.0.1.0.0, hook guard trong
`tp_admin_delegation/models/guards.py` (không nâng phiên bản), và tệp giao diện
tĩnh `tp_hr_workspace/static/src/my_profile/my_profile.{js,xml,scss}`.
Mô tả chức năng và quy tắc an toàn: [README tp_hr_bank](../../custom_addons/tp_hr_bank/README.md).
Áp và hoàn nguyên: [runbook](../../ops/runbooks/HR_BANK_001_DEPLOY_AND_ROLLBACK.md).

## 1. Người dùng thấy gì

| Màn hình | Kết quả |
| --- | --- |
| Hồ sơ của tôi → Thông tin cá nhân | Thẻ "Tài khoản ngân hàng": biểu tượng ngân hàng, số tài khoản nhóm 4 số, tên chủ tài khoản, trạng thái "Chờ Nhân sự xác minh" / "Nhân sự đã xác minh"; nút Thêm, Sửa, Gỡ |
| Thêm/Sửa tài khoản | Ô chọn ngân hàng có kính lúp, đếm kết quả, tìm không dấu theo tên, tên viết tắt, mã, BIN; chọn bằng chuột hoặc phím; khi đóng hiện tên viết tắt + dòng tên đầy đủ · BIN |
| Quốc gia, quốc tịch, quốc gia nơi sinh, tỉnh/thành phố | Ô tìm kiếm cùng kiểu: "viet" → Việt Nam, "ha noi" → Hà Nội, có đếm kết quả, nút xóa; tỉnh báo "Chọn quốc gia trước" |
| Ngày (ngày sinh, hết hạn hộ chiếu, ngày sinh vợ/chồng, quá trình công tác) | Bộ chọn ngày Odoo, DD/MM/YYYY ở cả xem và sửa |
| Giá trị trống | "Chưa khai báo" nghiêng xám; ô nhập có gợi ý mẫu |
| Nhân sự → Tổ chức → Danh mục ngân hàng (Quản lý Nhân sự) | 76 tổ chức NAPAS/VietQR, 70 đang dùng, tìm theo tên/mã/BIN |
| Form tài khoản ngân hàng của HR | Trường "Ngân hàng" có biểu tượng; `bank_name`, `bank_bic` tự đồng bộ |

Biểu tượng là chữ viết tắt trên màu nhận diện do module tự dựng, không phải logo
chính thức của ngân hàng.

## 2. Kiểm tự động (local `tp_tanphat_test`, dữ liệu giả)

| Kiểm | Test |
| --- | --- |
| Danh mục 76 tổ chức, mã/BIN duy nhất, 70 đang dùng | `test_catalogue_is_the_napas_list` |
| Nhân viên thêm, sửa, gỡ tài khoản của chính mình; đổi số tắt xác minh; ghi chú chỉ 4 số cuối | `test_employee_adds_updates_and_removes_own_account` |
| Tài khoản không có hồ sơ nhân viên | `test_account_without_employee_profile` |
| Từ chối tài khoản của người khác, trường ngoài danh sách | `test_other_people_accounts_are_refused` |
| Số 6–20 chữ số, tối đa 5 tài khoản, tên chủ tài khoản | `test_validation_rules` |
| Quy tắc đọc `res.partner.bank` theo chủ sở hữu | `test_access_rules_on_bank_accounts` |
| SCSS biên dịch được (libsass) | `test_web_styles_compile` |
| Trình duyệt desktop 1440 px và di động 390 px (Playwright): thẻ, tìm ngân hàng bằng chuột/bàn phím, ngày DD/MM/YYYY, tìm "viet" và "ha noi", bỏ thay đổi, 0 lỗi console | `test_profile_bank_card_in_browser` |
| Form HR đồng bộ `bank_name`/`bank_bic` | `test_hr_form_syncs_bank_fields` |

Chạy `/tp_hr_bank,/tp_hr_workspace` trên bản commit `b594f26f`: 103 test, 9/9 test
BANK-001 đạt (2 kiểm trình duyệt × 2 kích thước, 0 lỗi console). 6 fail + 3 error
còn lại đều thuộc nhóm lỗi có sẵn trước thay đổi (đã ghi trong
[HR-EMPLOYEE-CODE-003](HR_EMPLOYEE_CODE_003_ACCEPTANCE.md)), nằm ở form nhân viên,
không phải "Hồ sơ của tôi":

- `TestEmployeeDeleteHttp` ×5;
- `TestEmployeeLoginRename.test_rename_preserves_identity_password_permissions_and_export`
  và `TestEmployeeLoginRenameHttp.test_browser_dialog_validation_save_reload_and_mobile`;
- `TestUnifiedReadonlyBrowserHttp.test_browser_admin_vs_employee_parity_and_hidden_tabs_desktop_mobile`;
- `TestDashboardLock.test_job_filter_quality_catalog_export`.

Ảnh chụp rà soát (desktop 1440 px, di động 390 px; 6 tab, chế độ sửa, bộ chọn
ngày, ô tìm quốc gia/tỉnh, hộp thoại ngân hàng) nằm trong
`.local/hr-bank001/browser/`, không đưa lên Git.

Lỗi bắt được trước khi áp: `min(320px, 50vh)` trong SCSS làm libsass báo lỗi, cả
database sẽ dùng CSS cũ kèm thông báo "Style error". Đã sửa bằng `unquote(...)`
và thêm `test_web_styles_compile`.

## 3. PC server (`tp_tanphat_dev`, https://tpone.tadic.vn)

Áp 20/11/2026 18:25 giờ VN, commit `b594f26f`, script
[deploy-hr-bank001.ps1](../../ops/runbooks/deploy-hr-bank001.ps1). Trước khi áp đã
xác minh: PC chỉ có DB `tp_tanphat_dev`, `dbfilter = ^tp_tanphat_dev$`,
`tp_hr_workspace` 20.0.1.21.0 và `tp_admin_delegation` 20.0.2.1.0 đã cài,
`tp_hr_bank` chưa có; 25 tệp nguồn khớp baseline (commit cha `2af6d6d7`), tệp phụ
thuộc khớp bản đã kiểm. Chỉ ghi số lượng, không ghi số tài khoản hay tên.

| Kiểm | Kết quả |
| --- | --- |
| Cài `-i tp_hr_bank` | exit 0, log 0 ERROR, 25/25 tệp khớp checksum release |
| Module | `tp_hr_bank` 20.0.1.0.0 installed; không module nào khác được nâng |
| Danh mục ngân hàng | 76 tổ chức, 70 đang dùng, 76 BIN khác nhau |
| Quyền | 4 dòng truy cập của `tp_hr_bank`; 1 menu "Danh mục ngân hàng" (Quản lý Nhân sự) |
| Giữ nguyên (18 key snapshot) | nhân viên, phân bổ lương, `res_partner_bank` (0 → 0), liên kết nhân viên–tài khoản, users (login + hash), nhóm quyền, partner, quyền khác, base URL; 0 khác biệt ngoài dự kiến |
| Thông báo | hàng đợi mail 83 → 83, thông báo 0 → 0 |
| CSS `web.assets_web` trên PC | biên dịch 0 lỗi |
| JS `web.assets_web` trên PC | dựng được; có 7 tệp `tp_hr_bank`, 6 tệp `my_profile`, ô tìm kiếm và ngày DD/MM/YYYY |
| Log `tp-odoo` sau khởi động lại | 0 ERROR / Traceback |
| https://tpone.tadic.vn/web/health | 200 |

Backup `C:\TANPHAT-backups\hr-bank001\bank001-20261120T182500`: dump (10,4 MB) +
restore-list, filestore, nguồn bị ghi đè (`guards.py`, ba tệp `my_profile`),
config, manifest, snapshot trước/sau, log cài, SHA256.

Chưa xem giao diện trên PC bằng trình duyệt đã đăng nhập: không tạo tài khoản thử
trên server, và pane trình duyệt chưa đăng nhập. Giao diện đã kiểm bằng trình duyệt
trên bản local cùng commit; trên PC đã kiểm gói CSS/JS phía server như bảng trên.
Người dùng nên mở "Hồ sơ của tôi → Thông tin cá nhân" một lần (Ctrl+F5 nếu trình
duyệt còn giữ bản cũ) để xác nhận.
