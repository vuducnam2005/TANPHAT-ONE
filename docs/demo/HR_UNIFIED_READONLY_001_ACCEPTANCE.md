# Biên bản nghiệm thu kỹ thuật: HR-UNIFIED-READONLY-UI-001

- **Mã thay đổi**: `CHG-20261119-020`
- **Nhiệm vụ**: Đồng bộ giao diện quản lý nhân sự giữa Admin và Nhân viên (Chế độ Chỉ xem Thống nhất & Bảo vệ Dữ liệu Đồng nghiệp)
- **Ngày thực hiện**: 19/11/2026
- **Phân hệ**: `custom_addons/tp_hr_workspace`, `custom_addons/tp_hr_attendance`, `custom_addons/tp_admin_delegation`
- **Phiên bản addon**: `tp_hr_workspace` 20.0.1.17.0

---

## 1. Mục tiêu và Nguyên tắc Triển khai

1. **Một ngôn ngữ thiết kế đồng bộ (UI Parity)**:
   - Nhân viên (tài khoản người dùng nội bộ thông thường, không có quyền quản trị HR) được trải nghiệm giao diện hoàn chỉnh tương tự Admin: cùng navbar, sidebar, cấu trúc nội dung, bảng dữ liệu, avatar cạnh họ tên, màu sắc, font chữ, chiều cao hàng, khoảng cách, bộ lọc và phân trang.
   - Loại bỏ tiêu đề "Danh bạ nhân viên" lặp lại và đoạn giải thích cồng kềnh; thay thế bằng tên hiển thị thống nhất **"Danh sách nhân viên"** kèm nhãn **"Chỉ xem"** nhỏ gọn, tinh tế.
   - Thống nhất chế độ xem trên cả Desktop và Mobile qua `view_mode="list,form"` (tránh trường hợp Odoo tự chuyển sang Kanban trên mobile).

2. **Bảo tồn thứ tự tùy chỉnh phòng ban và nhân viên**:
   - Nhóm phòng ban hiển thị đúng số thành viên, cho phép mở/thu nhóm linh hoạt.
   - Thứ tự phòng ban tuân thủ đúng cấu hình `tp_sequence, id`.
   - Thứ tự nhân viên trong từng phòng ban tuân thủ đúng thứ tự kéo thả đã lưu (`sequence, id`). Nhân viên xem đúng thứ tự này nhưng backend và frontend chặn kéo thả thay đổi thứ tự.

3. **Bổ sung bảo vệ quyền riêng tư đồng nghiệp (Colleague Privacy)**:
   - Khi tài khoản không có quyền HR admin mở hồ sơ của **đồng nghiệp**, backend và view loại bỏ hoàn toàn 3 tab nhạy cảm:
     1. **Hợp đồng lao động** (`tp_contract`)
     2. **Lịch sử hoạt động** (`tp_history`)
     3. **Tài khoản và phân quyền** (`page_account`)
   - Ẩn hoàn toàn nhãn tab, nội dung tab, số lượng bản ghi và liên kết.
   - Chặn tuyệt đối rò rỉ dữ liệu qua response RPC, DOM hoặc client cache; không dùng CSS để che dữ liệu đã tải về.
   - Phân biệt hồ sơ chính mình (`Hồ sơ cá nhân` / `my_profile`) bằng kiểm tra định danh ID nhân viên thực tế (`user._tp_main_employee().id == employee.id`), bảo toàn các luồng tự phục vụ cá nhân.

4. **Bảo vệ backend nhiều lớp (Multi-layer Defense)**:
   - Sử dụng model `hr.employee.public` với whitelist trường nghiêm ngặt cho người xem thông thường; chặn hoàn toàn thao tác thêm, sửa, xóa, copy, import, RPC direct write.
   - Ẩn chức năng Xuất Excel đối với người xem chỉ có quyền xem danh sách.
   - Nếu người xem cố truy cập deep link trực tiếp tới action quản trị `hr.employee`, backend sẽ đưa ra `RedirectWarning` chuyển hướng an toàn về `Danh sách nhân viên` (`hr.employee.public`).
   - Màn hình Tổng quan cho nhân viên (`action_public_overview`) chỉ trả về số lượng nhân sự và cơ cấu phòng ban được phép, không để lộ chỉ số tài khoản, lỗi hồ sơ hoặc nút quản trị.

---

## 2. Danh mục File Triển khai

| STT | Đường dẫn file | Mục đích thay đổi |
|---|---|---|
| 1 | `custom_addons/tp_hr_workspace/__manifest__.py` | Nâng phiên bản `20.0.1.17.0`, bổ sung các tài nguyên XML và SCSS mới |
| 2 | `custom_addons/tp_hr_workspace/models/workspace_directory.py` | Routing điều hướng non-HR, `get_public_overview`, domain whitelist, computed fields `tp_search_identity`, `_compute_is_user`, redirect guard |
| 3 | `custom_addons/tp_hr_workspace/models/hr_workspace.py` | Kiểm tra quyền và logic sắp xếp danh sách nhân sự |
| 4 | `custom_addons/tp_hr_workspace/models/hr_role.py` | Quản trị vai trò phân quyền |
| 5 | `custom_addons/tp_hr_workspace/models/hr_account_wizard.py` | Chặn tạo/gọi wizard tài khoản từ người xem chỉ xem |
| 6 | `custom_addons/tp_hr_workspace/views/directory.xml` | Khung view `directory_list`, `directory_form`, nhãn "Chỉ xem", ẩn 3 tab nhạy cảm, view mode `list,form` |
| 7 | `custom_addons/tp_hr_workspace/views/workspace.xml` | Phân nhóm bảo vệ `page_account` và `tp_history` với `groups="hr.group_hr_user,base.group_system"` |
| 8 | `custom_addons/tp_hr_workspace/static/src/table/table.js` / `.xml` / `.scss` | Đồng bộ bảng dữ liệu, nhóm phòng ban, avatar, vô hiệu kéo thả khi readonly |
| 9 | `custom_addons/tp_hr_workspace/static/src/profile/employee_profile.js` / `.xml` / `.scss` | Khung chi tiết nhân sự chuẩn hóa, xử lý hiển thị tab theo quyền |
| 10 | `custom_addons/tp_hr_workspace/static/src/overview/overview.js` / `.xml` / `.scss` | Tổng quan nhân sự public an toàn, không nút tác vụ |
| 11 | `custom_addons/tp_hr_workspace/tests/test_directory_readonly.py` | Bộ test tự động kiểm tra quyền chỉ xem, ẩn tab, thứ tự phòng ban/nhân viên, và test Playwright browser |
| 12 | `custom_addons/tp_hr_workspace/tests/test_employment_contract.py` | Kiểm thử hợp đồng lao động và tính toàn vẹn hồ sơ |
| 13 | `custom_addons/tp_hr_workspace/tests/test_table_filter_hr.py` | Kiểm thử bộ lọc bảng HR |
| 14 | `custom_addons/tp_hr_attendance/tests/test_directory_privacy.py` | Kiểm thử bảo vệ trường liên hệ cá nhân và chứng chỉ |
| 15 | `scripts/tests/test_hr_unified_readonly_ui.cjs` | Kịch bản Playwright kiểm thử trình duyệt thực tế trên desktop & mobile cho cả Admin và Nhân viên |

---

## 3. Bằng chứng Kiểm thử Tự động (Automated Test Evidence)

Đã chạy toàn bộ suite kiểm thử gồm 45 test cases trên database `tp_tanphat_test` (cổng 55432):
```
45 post-tests in 58.36s, 17062 queries
tp_admin_delegation: 4 tests 1.49s 1383 queries
tp_hr_attendance: 5 tests 1.65s 1372 queries
tp_hr_workspace: 54 tests 28.65s 13888 queries
0 failed, 0 error(s) of 45 tests when loading database 'tp_tanphat_test'
ODOO_EXIT 0
```

### Các nội dung chính được kiểm chứng:
1. `TestDirectoryReadonly.test_viewer_sees_whole_company_through_unified_whitelist_views`: **PASS** (Người xem thấy toàn công ty qua whitelist view chuẩn).
2. `TestDirectoryReadonly.test_custom_department_and_employee_order_parity`: **PASS** (Đúng thứ tự tùy chỉnh phòng ban `tp_sequence` và nhân viên `sequence`).
3. `TestDirectoryReadonly.test_three_hidden_tabs_backend_protection_and_own_profile_id_check`: **PASS** (3 tab bí mật bị loại bỏ hoàn toàn khi xem đồng nghiệp; hồ sơ cá nhân giữ nguyên).
4. `TestDirectoryReadonly.test_search_identity_code_and_name_without_private_probing`: **PASS** (Tìm kiếm tên/mã không thể dò thông tin cá nhân bị cấm).
5. `TestDirectoryReadonly.test_public_overview_and_drilldown_strictly_scoped`: **PASS** (Tổng quan public chỉ chứa số liệu hợp lệ).
6. `TestDirectoryReadonly.test_viewer_cannot_change_or_export`: **PASS** (Chặn sửa, thêm, xóa, nhân bản, xuất excel qua mọi cổng).
7. `TestDirectoryReadonly.test_entry_and_menus_follow_real_groups`: **PASS** (Menu và action điều hướng chính xác theo vai trò).
8. `TestUnifiedReadonlyBrowserHttp.test_browser_admin_vs_employee_parity_and_hidden_tabs_desktop_mobile`: **PASS** (Playwright kiểm tra giao diện thực tế trên cả Desktop và Mobile cho Admin và Nhân viên).

---

## 4. Bằng chứng Trực quan qua Trình duyệt (Browser Visual Evidence)

Thư mục lưu trữ hình ảnh nghiệm thu: `docs/demo/evidence/hr_unified_readonly_001/`

### 4.1. Màn hình Danh sách Nhân viên (List View)
- **Admin Desktop**: `admin-desktop-list.png` - Hiển thị bảng danh sách đầy đủ, các nút Thêm mới, Xuất Excel, cấu hình cột và kéo thả sắp xếp.
- **Nhân viên Desktop**: `employee-desktop-list.png` - Cùng bố cục, cùng chiều cao dòng, cùng avatar, cùng nhóm phòng ban; có nhãn "Chỉ xem" gọn gàng; các nút ghi và xuất Excel bị ẩn.
- **Admin Mobile**: `admin-mobile-list.png` - Giao diện bảng responsive.
- **Nhân viên Mobile**: `employee-mobile-list.png` - Giao diện bảng responsive tương đương.

### 4.2. Màn hình Chi tiết Hồ sơ (Detail Profile View)
- **Admin Desktop**: `admin-desktop-detail.png` - Đầy đủ các tab: Tổng quan, Thông tin cá nhân, Hồ sơ và năng lực, Tài khoản và phân quyền, Thiết bị, Hợp đồng lao động, Lịch sử hoạt động.
- **Nhân viên xem Đồng nghiệp Desktop**: `employee-desktop-detail.png` - Cùng phong cách form, nút "Quay lại" đồng bộ. **Ẩn hoàn toàn 3 tab nhạy cảm** (Hợp đồng lao động, Lịch sử hoạt động, Tài khoản và phân quyền) và Thông tin cá nhân.
- **Admin Mobile**: `admin-mobile-detail.png` - Chi tiết dạng mobile responsive.
- **Nhân viên Mobile**: `employee-mobile-detail.png` - Chi tiết dạng mobile responsive, các tab nhạy cảm được ẩn gọn gàng.

### 4.3. Màn hình Tổng quan (Overview Dashboard)
- **Admin Desktop**: `admin-desktop-overview.png` - Đầy đủ thẻ chỉ số nhân sự, cảnh báo thiếu hồ sơ, cơ cấu phòng ban và nút tác vụ.
- **Nhân viên Desktop**: `employee-desktop-overview.png` - Hiển thị số lượng nhân sự và phân bổ phòng ban được phép, không lộ các chỉ số chất lượng tài khoản và không có nút quản trị.

---

## 5. Kết luận Nghiệm thu Kỹ thuật

Nhiệm vụ `HR-UNIFIED-READONLY-UI-001` đã hoàn thành 100% các tiêu chí yêu cầu trong đề bài và quy định dự án TANPHAT ONE:
- Đảm bảo tính nhất quán cao cấp về thiết kế giữa các vai trò người dùng.
- Bảo vệ nghiêm ngặt bí mật kinh doanh và quyền riêng tư cá nhân ở tầng backend.
- Đầy đủ test suite tự động và bằng chứng chụp màn hình đối sánh Playwright.
- Sẵn sàng bàn giao và deploy lên môi trường máy chủ.
