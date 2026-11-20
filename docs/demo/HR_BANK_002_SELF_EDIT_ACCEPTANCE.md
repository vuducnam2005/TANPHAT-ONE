# HR-SELF-EDIT-001 + BANK-002 — Nghiệm thu tự sửa hồ sơ và tài khoản ngân hàng không cần xác minh

Quyết định: [DEC-065](../DECISIONS.md). Mã thay đổi: `CHG-20261120-017` (commit
`538924a8` ghi nhầm `CHG-20261120-016` trong tiêu đề; mã đó thuộc
HR-ATTENDANCE-ORDER-001).
Áp và hoàn nguyên: [runbook](../../ops/runbooks/HR_BANK_002_DEPLOY_AND_ROLLBACK.md).

## 1. Vấn đề người dùng báo

- Admin ủy quyền (ví dụ tài khoản Vũ Đức Nam) mở hồ sơ của chính mình từ
  "Danh sách nhân viên" thì toàn bộ form bị khóa như hồ sơ của admin khác, phải
  vào "Hồ sơ của tôi" ở góc dưới bên trái mới sửa được.
- Tài khoản ngân hàng tự khai phải chờ Nhân sự xác minh mới dùng được.

## 2. Thay đổi

| Phần | Kết quả |
| --- | --- |
| Hồ sơ của chính mình trong danh sách nhân viên | Thông báo "Đây là hồ sơ của bạn…", có nút "Sửa hồ sơ"; sửa tại chỗ các trường tự phục vụ (ảnh, email, điện thoại, địa chỉ, ngày sinh, giấy tờ, liên hệ khẩn cấp, gia đình, học vấn, tài khoản ngân hàng) |
| Trên hồ sơ của chính mình vẫn khóa | Họ tên, phòng ban, chức vụ, mã nhân viên, tài khoản đăng nhập, quyền, nút quản trị tài khoản, menu hành động/in |
| Hồ sơ admin ủy quyền khác | Vẫn chỉ đọc như DEC-062 |
| Guard `hr.version` | Nhận hai dấu ghi nhận core tự thêm (`last_modified_date`, `last_modified_uid` đúng người đang sửa). Trước đây admin ủy quyền không lưu được địa chỉ, CCCD, hộ chiếu, giới tính, quốc tịch, hôn nhân ở cả form và "Hồ sơ của tôi" |
| Tài khoản ngân hàng | Lưu đủ thông tin hợp lệ là dùng được ngay cho chi lương; không còn trạng thái "Chờ Nhân sự xác minh"; đổi ngân hàng/số cũng có hiệu lực ngay |
| Nâng cấp `tp_hr_bank` 20.0.1.1.0 | Migration bật dùng được cho tài khoản tự khai đang chờ (có ngân hàng trong danh mục, gắn hồ sơ nhân viên hoặc liên hệ của người dùng, đang hoạt động) |

Người dùng vẫn không tự ghi được cờ `allow_out_payment`, tài khoản của người
khác hay trường HR ngoài danh sách; mọi lần thêm/sửa/gỡ tài khoản ngân hàng ghi
chatter hồ sơ nhân viên, chỉ 4 số cuối.

## 3. Kiểm tự động (local `tp_tanphat_test`, dữ liệu giả)

| Kiểm | Test |
| --- | --- |
| Admin ủy quyền tự ghi điện thoại, email, liên hệ khẩn cấp, hôn nhân, địa chỉ, CCCD, giới tính trên form và qua "Hồ sơ của tôi"; `last_modified_uid` là chính mình | `test_own_record_personal_fields_editable_in_place` |
| Từ chối tự đổi họ tên, chức vụ, phòng ban, mã; giả mạo `last_modified_uid`; ghi `wage`; sửa hồ sơ admin khác | như trên |
| View: trường tự phục vụ chỉ khóa khi `user_id != uid`, trường khác luôn khóa, thông báo hồ sơ của mình | như trên |
| Trình duyệt desktop 1440 px + di động 390 px: mở hồ sơ của mình, thấy thông báo, không có nút quản trị tài khoản, "Sửa hồ sơ" → đổi điện thoại cá nhân → Lưu; họ tên/chức vụ/phòng ban không có ô nhập; 0 lỗi console | `test_browser_original_lock_unlock_and_peer_readonly_desktop_mobile` |
| Tự thêm tài khoản → dùng được ngay; đổi tên chủ, đổi ngân hàng + số vẫn dùng được; chatter chỉ 4 số cuối, không chữ "xác minh"; gỡ thì tắt dùng được; thêm lại dùng lại bản ghi | `test_employee_adds_updates_and_removes_own_account` |
| Người dùng không tự ghi `allow_out_payment`, số tài khoản hay tên chủ qua ORM | `test_access_rules_on_bank_accounts` |
| Migration chỉ bật tài khoản tự khai đang chờ; tài khoản đã gỡ, của nhà cung cấp, không có ngân hàng trong danh mục giữ nguyên | `test_upgrade_trusts_self_declared_accounts` |
| Thẻ ngân hàng trên trình duyệt không còn trạng thái xác minh | `test_profile_bank_card_in_browser` |

Kết quả: `-u tp_hr_bank,tp_admin_delegation --test-tags /tp_hr_bank,/tp_admin_delegation`
→ 0 failed, 0 error / 31 test (tp_admin_delegation 37 lượt, tp_hr_bank 12 lượt
theo thống kê), ảnh chụp `peer-{desktop,mobile}-own-edit.png` trong
`.local/admin-account-policy/browser/` (không đưa lên Git).

## 4. PC server

| Kiểm | Kết quả |
| --- | --- |
| Gói release | commit `538924a8`, 26 tệp, baseline và tệp phụ thuộc khớp trước khi áp |
| Backup | `C:\TANPHAT-backups\hr-bank002\bank002-20261120T191725` (dump + restore-list, filestore, nguồn bị ghi đè, config, SHA256SUMS) |
| Nâng cấp `-u tp_hr_bank` | exit 0, log 0 ERROR, `tp_hr_bank` 20.0.1.1.0 installed |
| Migration | 1 tài khoản tự khai đang chờ được bật dùng được; tài khoản hoạt động/dùng được/đang chờ `1:0:1` → `1:1:0` |
| Snapshot 19 key | không khác biệt ngoài `module:tp_hr_bank`, `bank_accounts`, `bank_trust`; hàng đợi mail 83 → 83, thông báo 0 → 0 |
| Sau khởi động lại | `https://tpone.tadic.vn/web/health` 200; log `tp-odoo` 10 phút 0 ERROR |
| View hồ sơ (kiểm chỉ đọc, rollback) | 5/5 admin ủy quyền có hồ sơ nhân viên: hồ sơ của mình có thông báo, điện thoại cá nhân mở khi `user_id = uid`, họ tên khóa |
| Bundle JS `web.assets_web` | dựng được; có `employee_profile.js` mới (`isOwnProfile`), không còn `o_tp_bank_status` |

Chưa xem trên PC bằng trình duyệt đã đăng nhập (không tạo tài khoản thử trên
server).

## 5. Người dùng tự kiểm

1. Đăng nhập tài khoản admin ủy quyền, vào Nhân sự → Danh sách nhân viên, mở hồ
   sơ của chính mình: thấy dòng "Đây là hồ sơ của bạn…" và nút "Sửa hồ sơ".
2. Bấm "Sửa hồ sơ", đổi một trường cá nhân (ví dụ điện thoại cá nhân), Lưu.
   Họ tên, phòng ban, chức vụ không sửa được ở đây.
3. Hồ sơ của tôi → Thông tin cá nhân → Tài khoản ngân hàng: thêm hoặc sửa, bấm
   Lưu; thẻ không còn dòng "Chờ Nhân sự xác minh".
