# BANK-002 + HR-SELF-EDIT-001 — Áp và hoàn nguyên

Phạm vi:

- nâng `tp_hr_bank` 20.0.1.0.0 → **20.0.1.1.0** (`-u tp_hr_bank`, không nâng
  module khác): lưu tài khoản ngân hàng là dùng được ngay, bỏ trạng thái "Chờ
  Nhân sự xác minh"; migration `migrations/20.0.1.1.0/post-migrate.py` bật dùng
  được cho tài khoản tự khai đang chờ;
- `tp_admin_delegation/models/hr_profile.py` và `guards.py` (Python, nạp khi
  Odoo khởi động lại; không đổi phiên bản module): hồ sơ của chính mình mở từ
  danh sách nhân viên sửa được các trường cá nhân ngay tại chỗ; guard
  `hr.version` nhận hai dấu ghi nhận core tự thêm nên admin ủy quyền lưu được
  địa chỉ, CCCD, hộ chiếu, giới tính, quốc tịch, hôn nhân;
- `tp_hr_workspace/static/src/profile/employee_profile.js` (tệp tĩnh, không cần
  `-u tp_hr_workspace`): hiện nút "Sửa hồ sơ" trên hồ sơ của chính mình.

Không sửa core Odoo. Không tạo, xóa hay đổi nhân viên, tài khoản đăng nhập, mật
khẩu hay quyền. Không nhập tài khoản ngân hàng thay người dùng.

## Áp lên PC server

1. **Đóng gói** từ commit đã đẩy: `git archive` các đường dẫn release (toàn bộ
   `custom_addons/tp_hr_bank`, `guards.py`, `hr_profile.py`, test chính sách
   admin, `employee_profile.js`). Manifest ghi `commit`, `parent`, hash baseline
   (nội dung của parent, `MISSING` cho tệp mới), hash release, và hash các tệp
   phụ thuộc phải khớp bản đã kiểm (`tp_hr_workspace/models/my_profile.py`,
   `tp_hr_workspace/static/src/profile/employee_profile.xml`,
   `tp_hr_workspace/views/workspace.xml`). Hash chuẩn hóa CRLF→LF.
2. **Chép lên PC** vào `C:\Projects\TANPHAT-ONE\.local\hr-bank002\`
   (`<label>-release.tar.gz`, `<label>-manifest.json`), rồi chạy
   `powershell -File ops\runbooks\deploy-hr-bank002.ps1 -Label bank002`.
3. **Script từ chối trước khi đổi gì** nếu nguồn lệch baseline, tệp phụ thuộc
   khác bản đã kiểm, `tp_hr_bank` không ở trạng thái `installed` 20.0.1.0.0, hoặc
   `tp_hr_workspace` / `tp_admin_delegation` chưa cài.
4. **Script thực hiện:**
   - dừng `tp-odoo`, snapshot `before`;
   - backup dump + restore-list, filestore, nguồn bị ghi đè, config vào
     `C:\TANPHAT-backups\hr-bank002\<label>-<time>\`;
   - giải nén, kiểm checksum từng tệp, đóng dấu thời gian để Odoo dựng lại bundle;
   - `-u tp_hr_bank` trong container tạm; snapshot `after`;
   - luôn khởi động lại `tp-odoo`.
5. **Snapshot** (chỉ số lượng và md5, không in số tài khoản, tên, login): module,
   module đã cài, nhân viên, phân bổ lương, `res_partner_bank` (đủ trường và
   riêng phần không gồm `allow_out_payment`), số tài khoản đang dùng/dùng được/
   đang chờ, liên kết nhân viên–tài khoản, users (login + hash), nhóm quyền,
   partner, quy tắc truy cập, danh mục ngân hàng, tin nhắn hồ sơ nhân viên, hàng
   đợi mail, thông báo, base URL. Chỉ được đổi: `module:tp_hr_bank`
   (`20.0.1.1.0:installed`), `bank_accounts` và `bank_trust` (chỉ cờ dùng được;
   `bank_accounts_except_trust` phải giữ nguyên). Sau khi áp không còn tài khoản
   tự khai nào ở trạng thái chờ. Log nâng cấp phải 0 ERROR.
6. **Nghiệm thu** trên https://tpone.tadic.vn: trang trả 200; admin ủy quyền mở
   hồ sơ của chính mình từ danh sách nhân viên thấy thông báo "Đây là hồ sơ của
   bạn" và nút "Sửa hồ sơ"; thẻ "Tài khoản ngân hàng" không còn trạng thái xác minh.

## Hoàn nguyên

Chỉ dùng khi nghiệm thu thất bại:

1. Dừng `tp-odoo`.
2. `pg_restore --clean --if-exists` dump trong thư mục backup vào `tp_tanphat_dev`.
3. Giải nén `source.tar.gz` đè các tệp đã ghi đè; xóa
   `custom_addons/tp_hr_bank/migrations/20.0.1.1.0`. Nếu cần, khôi phục filestore
   từ `filestore.tar.gz`.
4. Khởi động `tp-odoo` và so snapshot với `before`.

Hoàn nguyên đưa tài khoản ngân hàng về trạng thái "Chờ Nhân sự xác minh" như
trước và làm mất các thay đổi hồ sơ, tài khoản ngân hàng người dùng nhập sau khi
áp: xuất danh sách cho Nhân sự trước khi hoàn nguyên.
