# BANK-001 — Áp và hoàn nguyên tài khoản ngân hàng trong "Thông tin cá nhân"

Phạm vi:

- cài module mới `tp_hr_bank` 20.0.1.0.0 (`-i tp_hr_bank`, không nâng module khác);
- hook `_tp_self_service_fields` trong `tp_admin_delegation/models/guards.py`
  (Python, nạp khi Odoo khởi động lại; không đổi phiên bản module);
- giao diện tĩnh `tp_hr_workspace/static/src/my_profile/my_profile.{js,xml,scss}`
  (ô tìm quốc gia/tỉnh, ngày DD/MM/YYYY, sửa mũi tên ô chọn). Odoo đọc tệp tĩnh lúc
  chạy, nên không cần `-u tp_hr_workspace`.

Không sửa core Odoo. Không tạo, xóa hay đổi nhân viên, tài khoản, mật khẩu hay
quyền có sẵn. Không nhập tài khoản ngân hàng thay người dùng.

## Áp lên PC server

1. **Đóng gói** từ commit đã đẩy: `git archive` các đường dẫn release (toàn bộ
   `custom_addons/tp_hr_bank`, `guards.py`, ba tệp `my_profile`). Manifest ghi
   `commit`, `parent`, hash baseline (nội dung của parent, `MISSING` cho tệp mới),
   hash release, và hash các tệp phụ thuộc phải khớp bản đã kiểm
   (`tp_hr_workspace/models/my_profile.py`, `workspace_scope.py`,
   `tp_web_home/static/src/validation/validation.js`). Hash chuẩn hóa CRLF→LF.
2. **Chép lên PC** vào `C:\Projects\TANPHAT-ONE\.local\hr-bank001\`
   (`<label>-release.tar.gz`, `<label>-manifest.json`), rồi chạy
   `powershell -File ops\runbooks\deploy-hr-bank001.ps1 -Label bank001`.
3. **Script từ chối trước khi đổi gì** nếu nguồn lệch baseline, tệp phụ thuộc
   khác bản đã kiểm, `tp_hr_bank` đã cài, hoặc `tp_hr_workspace` /
   `tp_admin_delegation` chưa cài.
4. **Script thực hiện:**
   - dừng `tp-odoo`, snapshot `before`;
   - backup dump + restore-list, filestore, nguồn bị ghi đè (`guards.py`, ba tệp
     `my_profile`), config vào `C:\TANPHAT-backups\hr-bank001\<label>-<time>\`;
   - giải nén, kiểm checksum từng tệp, đóng dấu thời gian để Odoo dựng lại bundle;
   - `-i tp_hr_bank` trong container tạm; snapshot `after`;
   - luôn khởi động lại `tp-odoo`.
5. **Snapshot** (chỉ số lượng và md5, không in số tài khoản, tên, login): module,
   danh sách module đã cài, nhân viên, phân bổ lương, `res_partner_bank`, liên kết
   nhân viên–tài khoản, users (login + hash), nhóm quyền, partner, quy tắc truy cập
   khác, hàng đợi mail, thông báo, base URL. Chỉ được đổi: `module:tp_hr_bank`,
   `access_bank`, `tp_bank` (phải là `76:70:76`). Log cài phải 0 ERROR.
6. **Nghiệm thu** trên https://tpone.tadic.vn: trang trả 200, không có thông báo
   "Style error"; "Hồ sơ của tôi → Thông tin cá nhân" có thẻ "Tài khoản ngân hàng";
   menu "Danh mục ngân hàng" chỉ hiện với Quản lý Nhân sự.

## Hoàn nguyên

Chỉ dùng khi nghiệm thu thất bại:

1. Dừng `tp-odoo`.
2. `pg_restore --clean --if-exists` dump trong thư mục backup vào `tp_tanphat_dev`.
3. Giải nén `source.tar.gz` đè `guards.py` và ba tệp `my_profile`; xóa thư mục
   `custom_addons/tp_hr_bank`. Nếu cần, khôi phục filestore từ `filestore.tar.gz`.
4. Khởi động `tp-odoo` và so snapshot với `before`.

Tài khoản ngân hàng người dùng khai sau khi áp sẽ mất khi khôi phục dump: xuất
danh sách cho Nhân sự trước khi hoàn nguyên.
