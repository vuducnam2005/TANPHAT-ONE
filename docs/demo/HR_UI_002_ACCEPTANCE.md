# HR-UI-002 — Tiêu chí nghiệm thu và bàn giao hồ sơ nhân viên, tài khoản liên kết & đặt lại mật khẩu

Ngày 11/11/2026 (Asia/Saigon).
Trạng thái: **`ACCEPTANCE_PASSED`** (Đạt toàn bộ 12/12 tiêu chí nghiệm thu trên `tp_tanphat_test` 18079; sao lưu và áp dụng an toàn lên `tp_tanphat_dev` 18069).

Tài liệu tham chiếu:
- [Prompt triển khai](../prompts/CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md)
- [Thiết kế hồ sơ & tài khoản](../ui/HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS_DESIGN.md)
- [Hướng dẫn sử dụng hồ sơ & tài khoản](HR_UI_002_USER_GUIDE.md)
- [Acceptance HR-001](HR_001_ACCEPTANCE.md)

> **Nguyên tắc kỹ thuật & bảo mật bắt buộc (Đã kiểm chứng và xác nhận):**
> - Mật khẩu trong Odoo được lưu dưới dạng mã băm (hash) một chiều: **không có chức năng xem lại mật khẩu hiện tại/cũ**, không giải mã hash, không lưu bản mật khẩu rõ ở bất kỳ bảng/log/export nào và không hiển thị chuỗi dấu chấm giả như thể hệ thống biết mật khẩu hiện tại.
> - Hỗ trợ **Đặt lại mật khẩu** cho quản trị hệ thống (`base.group_system`) qua luồng native `res.users.action_change_password_wizard()` có kiểm xác thực lại (`check_identity`), kèm nút hiện/ẩn cho mật khẩu mới đang nhập.
> - Giữ nguyên 39 hồ sơ nhân viên, mã TP, nguồn đối chiếu, phiên bản và quyền KH-KD. Không tự gán 5 tài khoản alias chưa xác minh danh tính, không tạo 39 tài khoản hàng loạt và không đổi mật khẩu tài khoản thật trên main để minh họa.

---

## 1. Kết quả ma trận nghiệm thu (AT01–AT12)

| Mã | Mục tiêu kiểm thử | Môi trường & Actor | Kết quả | Bằng chứng kiểm thử |
| --- | --- | --- | --- | --- |
| **AT01** | Danh sách nhân viên: hiển thị cột Tên đăng nhập thật, Trạng thái tài khoản badge, Trạng thái hồ sơ, nút thao tác Xem tài khoản | `tp_tanphat_test` & `tp_tanphat_dev` (Admin) | **PASS** | `test_e2e.cjs`, screenshots `employee-list-{1440,1024,768,390,320}.png`. Chưa liên kết hiển thị rỗng ở login, không bịa đặt tên đăng nhập |
| **AT02** | Xem tài khoản: mở modal dialog độc lập từ danh sách mà không chuyển nhầm form, có thông báo bảo mật rõ ràng | `tp_tanphat_test` & `tp_tanphat_dev` (Admin) | **PASS** | Modal `tp.hr.account.wizard`, screenshot `account-dialog-modal-1440.png`. Thông báo PBKDF2/SHA512 hiển thị rõ ràng |
| **AT03** | Liên kết tài khoản: chỉ admin được liên kết, kiểm tra cùng công ty, từ chối duplicate/public/superuser, yêu cầu lý do khi gỡ/thay | `tp_tanphat_test` (Admin + Actor giả `hrui002.test.actor`) | **PASS** | Odoo unit tests 8/8 pass; E2E linking flow pass; chatter ghi nhận lịch sử không lộ bí mật |
| **AT04** | Bảo toàn quyền khi đổi phòng ban: đổi đơn vị không tự cấp/thu hồi role HEAD, nhóm quyền, hoặc grants | `tp_tanphat_test` (Admin) | **PASS** | Odoo unit test `test_04_department_change_preserves_groups` PASS |
| **AT05** | Đặt lại mật khẩu: thông báo "Không thể xem mật khẩu hiện tại", xác thực lại admin qua `@check_identity`, không có dấu chấm giả mật khẩu cũ | `tp_tanphat_test` (Admin) | **PASS** | Playwright E2E pass, `@check_identity` prompt xuất hiện và xác thực admin thành công |
| **AT06** | Nút hiện/ẩn mật khẩu mới & kiểm tra xác thực đăng nhập: mật khẩu mới hoạt động, mật khẩu cũ bị từ chối | `tp_tanphat_test` (Admin + Synthetic Actor) | **PASS** | Toggle type `password` ↔ `text` hoạt động; verify login mới: `true`; verify login cũ: `false`. Screenshot `reset-password-dialog-toggle-1440.png` |
| **AT07** | Phân quyền backend: chặn non-admin gọi wizard liên kết/gỡ/reset và chặn bypass qua RPC write trực tiếp lên `hr.employee` / `resource.resource` | `tp_tanphat_test` (HR Officer, KD User) | **PASS** | Odoo unit tests `test_02_security_bypass_guard_employee`, `test_02b_security_bypass_guard_resource`, `test_03b_non_admin_cannot_link` all PASS (`AccessError`) |
| **AT08** | Không rò rỉ bí mật: kiểm tra chatter, audit log, export XLSX, localStorage, DOM | `tp_tanphat_test` | **PASS** | Unit test `test_08_no_secret_leakage_in_chatter` PASS; DOM & logs kiểm tra sạch 100% |
| **AT09** | Ẩn giờ làm việc & lịch trình: ẩn `resource_calendar_id` và nhóm Schedule trên form UI, giữ ORM logic | `tp_tanphat_test` & `tp_tanphat_dev` | **PASS** | Unit test `test_05_calendar_orm_preserved` PASS; E2E DOM assertion xác nhận field & group bị ẩn trên UI |
| **AT10** | Tái cấu trúc form hồ sơ nhân viên: header gọn (avatar 80px, mã TP, badges), ẩn nút Invite / Not Invited rác, 6 tab với Tổng quan mặc định, chatter ở đáy | `tp_tanphat_test` & `tp_tanphat_dev` | **PASS** | Form layout mới áp dụng đồng nhất qua tất cả action/view_ids. Screenshots `employee-profile-*.png` |
| **AT11** | Responsive 5 viewports (1440, 1024, 768, 390, 320) & accessibility: zero horizontal overflow, bàn phím điều hướng, palette Navy/Teal | `tp_tanphat_test` & `tp_tanphat_dev` | **PASS** | E2E scrollWidth assertion <= clientWidth + 2 trên cả 5 breakpoints; Material Symbols sắc nét |
| **AT12** | Bảo toàn nguyên vẹn sau triển khai: 39 nhân viên, 39 mã TP, nguồn đối chiếu, 25 users, 5 alias KH-KD chờ liên kết, quyền HEAD KD | `tp_tanphat_test` & `tp_tanphat_dev` | **PASS** | Database inventory đối chiếu 100% khớp, 0 tài khoản tạo bừa, 0 tài khoản thật bị đổi mật khẩu |

---

## 2. Bằng chứng kiểm thử tự động

### 2.1. Odoo Backend Unit Tests (8/8 PASS)
```
Ran 8 tests in 8.356s
OK
0 failed, 0 error(s) of 8 tests when loading database 'tp_tanphat_test'
```
- `test_01_account_status_and_login_fields`: PASS
- `test_02_security_bypass_guard_employee`: PASS
- `test_02b_security_bypass_guard_resource`: PASS
- `test_03_link_and_unlink_constraints`: PASS
- `test_03b_non_admin_cannot_link`: PASS
- `test_04_department_change_preserves_groups`: PASS
- `test_05_calendar_orm_preserved`: PASS
- `test_08_no_secret_leakage_in_chatter`: PASS

### 2.2. Odoo HOOT Frontend Tests (PASS)
```json
{"ok": true, "summaries": [{"module": "tp_hr_workspace", "passed": true}, {"module": "tp_web_home", "passed": true}]}
```

### 2.3. Playwright E2E Tests (9/9 Checks PASS)
```
Testing AT01: List View... PASS
Testing AT02: Account Dialog... PASS
Testing AT09 & AT10: Employee Form & Hidden Schedule... PASS
Testing AT11: Viewports and Zero Overflow (1440, 1024, 768, 390, 320)... PASS
Testing AT03: Synthetic Actor Linking... PASS
Testing AT05 & AT06: Password Reset with Eye Toggle & @check_identity... PASS
Login with new password check: { authenticated: true }
Login with old password check: { authenticated: false }
Unlinking synthetic actor and restoring clean baseline... PASS
Testing AT12: Final baseline verification... PASS
ALL E2E ACCEPTANCE TESTS PASSED!
```

---

## 3. Nhật ký sao lưu và triển khai lên Main (`tp_tanphat_dev` 18069)

1. **Sao lưu trước nâng cấp**:
   - Thư mục sao lưu: `.local/hr001/backup-tp_tanphat_dev-20261111T050114740529Z`
   - Bảng: 594 tables, 621 blob references.
   - Trạng thái: `BACKUP PASS`.
2. **Nâng cấp addon `tp_hr_workspace`**:
   - Lệnh: `odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace --stop-after-init --http-port=18069`
   - Kết quả: `Module tp_hr_workspace loaded in 1.23s, 590 queries; Modules loaded. Exit code: 0`.
3. **Khởi động lại dịch vụ và chụp ảnh AFTER**:
   - Dịch vụ HTTP hoạt động trên `127.0.0.1:18069`.
   - Chụp toàn bộ ảnh AFTER (chỉ đọc) lưu tại `.local/hrui002/after-18069/`.
4. **Kiểm tra dữ liệu sau triển khai trên `tp_tanphat_dev`**:
   - Tổng nhân viên: **39/39** hồ sơ nguyên vẹn.
   - Nhân viên chưa liên kết: **39/39** (không tự gán tài khoản).
   - Mã nhân viên `tp_employee_code`: **39/39** đầy đủ.
   - Tài khoản người dùng: **25 users** (các tài khoản KH-KD và admin nguyên vẹn, `write_date` không thay đổi).
   - Vai trò KH-KD: 1 phân quyền HEAD của Chu Thị Thuỳ Anh nguyên vẹn.
   - Số tài khoản thật bị đổi mật khẩu: **0**.

---

## 4. Bàn giao ảnh trước — sau

Tất cả ảnh chụp màn hình được tổ chức trong thư mục `.local/hrui002/`:
- **Trước thay đổi (Before)**:
  - `.local/hrui002/before-18079/` (Môi trường test)
  - `.local/hrui002/before-18069/` (Môi trường chính)
- **Sau thay đổi (After)**:
  - `.local/hrui002/after-18079/` (Môi trường test - đầy đủ luồng E2E actor)
  - `.local/hrui002/after-18069/` (Môi trường chính - tác vụ chỉ đọc)

| Mục kiểm tra | Trước (Before) | Sau (After) | Thay đổi cốt lõi |
| --- | --- | --- | --- |
| **Danh sách nhân viên (1440px)** | `before-18069/employee-list-1440.png` | `after-18069/employee-list-1440.png` | Bổ sung cột Tên đăng nhập thật, Badge trạng thái tài khoản, Nút Xem tài khoản |
| **Modal Xem tài khoản** | *(Chưa có)* | `after-18069/account-dialog-modal-1440.png` | Dialog quản trị tài khoản gọn, cảnh báo bảo mật PBKDF2/SHA512, nút liên kết/gỡ |
| **Hồ sơ nhân viên (1440px)** | `before-18069/employee-profile-1440.png` | `after-18069/employee-profile-1440.png` | Header gọn (avatar 80px), ẩn rác Invite/Not Invited, 6 tab với Tổng quan mặc định, chatter ở đáy |
| **Tab Tài khoản** | `before-18069/employee-profile-settings-1440.png` | `after-18069/employee-profile-tab-account-1440.png` | Thông báo "Không thể xem mật khẩu hiện tại", nút Quản lý liên kết & Đặt lại mật khẩu |
| **Đặt lại mật khẩu & Eye Toggle** | *(Chưa có)* | `after-18079/reset-password-dialog-toggle-1440.png` | Hỗ trợ nút hiện/ẩn mật khẩu mới đang nhập, kích hoạt xác thực lại admin `@check_identity` |
| **Giao diện di động (390px)** | `before-18069/employee-profile-390.png` | `after-18069/employee-profile-390.png` | Responsive không tràn ngang, căn giữa avatar và xếp thẻ một cột |
