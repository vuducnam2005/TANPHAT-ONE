# HR-UI-011 — Giao diện quản lý nhân sự

**Cập nhật sau phản hồi người dùng:** [HR-LIST-012](HR_LIST_012_ACCEPTANCE.md)
thay phần danh sách nhân viên bằng kiểu nhóm cũ, bỏ cột phòng ban lặp. Các kết
quả011 bên dưới là lịch sử trước correction; màn khác giữ nguyên.


13/11/2026 Asia/Saigon · CHG-20261113-002 · **IMPLEMENTED_VERIFIED_MAIN_APPLIED**.
Yêu cầu trực tiếp trong tệp người dùng đính kèm; ngoại lệ triển khai chỉ cho task này.
`tp_hr_workspace` 20.0.1.9.0 → **20.0.1.10.0**; `tp_organization` giữ 20.0.2.2.0.
Không stage/commit/push. Giữ các thay đổi HR-DELETE-010 và UI-HOME-005 có sẵn.
Thiết kế và A01–A12 đã ghi trước code trong [thiết kế](../ui/HR_UI_011_DESIGN.md).

## Màn hình và truy cập

| Màn hình | Đường dẫn main | Kết quả |
| --- | --- | --- |
| Nhân viên và hồ sơ | [Danh sách nhân viên](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_employees) → tên hoặc Xem hồ sơ | Bảng phẳng; nhóm phòng tùy chọn; avatar/mã/công việc/login/trạng thái; thao tác tài khoản theo quyền và tình trạng. Hồ sơ chỉ đọc mặc định, 5 tab, desktop 2 cột/mobile 1 cột; Sửa/Lưu/Hủy/Quay lại và cảnh báo chưa lưu |
| Phòng ban và đơn vị | [Phòng ban](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_departments) → dòng | Điểm màu/icon, quản lý thật hoặc Chưa khai báo, số nhân viên cùng domain drilldown; form tổ chức/quản lý, nhân viên và cấp trên/dưới |
| Chức vụ | [Chức vụ](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_jobs) → dòng | Phòng áp dụng, số nhân viên, badge sử dụng; form thông tin/mô tả/nhân viên; không suy quyền từ tên chức vụ |
| Nơi làm việc | [Nơi làm việc](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_locations) → dòng khi có dữ liệu | Form địa điểm theo nhóm, empty state và CTA đúng quyền. Main đang trống; không tạo địa chỉ mẫu |
| Sơ đồ quản lý | [Sơ đồ](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_hierarchy) | Hierarchy Odoo thật theo parent_id/child_ids, mở/thu nhánh, avatar/chức vụ/phòng, ghi thiếu quản lý; không kéo thả đổi quan hệ, không suy từ phòng/chức danh |
| Nhập và đối chiếu | [Lô nhập](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_import) → dòng | Tên lô/tệp/người/thời gian đầy đủ; 4 bước UI trên 3 state cũ; tổng hợp create/update/skip/conflict, khóa nguồn sau áp dụng |
| Nhãn nhân viên | [Nhãn](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_categories) → dòng khi có dữ liệu | Đổi tên hiển thị từ Thẻ nhân viên; chip màu, count theo quyền, form tên/màu/nhân viên. Main đang trống; không tạo nhãn mẫu |

Chỉ giữ một menu chính **Danh sách nhân viên**. `menu_records` và nhóm rỗng
`menu_group_records` chuyển inactive bằng XML; giữ XML ID/action cũ. Không xóa
hồ sơ, phiên bản, kỹ năng, chứng chỉ, tệp, chatter hay lịch sử. Các menu lọc
Hồ sơ cần bổ sung/Lưu trữ/Chưa có tài khoản tiếp tục phục vụ chức năng riêng.

## Chức năng, quyền và nguồn

Tái sử dụng `tp_hr_table`: SearchModel và paging/sort/domain backend, tùy chọn
cột, native facets + Xóa bộ lọc, 10/20/50/100 thật, ghi rõ dòng hay nhóm và số
bản ghi trong từng nhóm. Không patch toàn cục ListRenderer, không có hàng trắng
giả; empty/loading/lỗi tải trang/retry có hành vi thực. CSS giới hạn HR; sidebar
264px/rail68px, navbar và session chung giữ nguyên.

Count phòng/chức vụ/nhãn là trường compute không lưu, **không sudo**, cùng
active/company/record rules với action drilldown. Tám field mới chỉ phục vụ
hiển thị (7 count và manager label); không có stored business field/migration
dữ liệu, ACL mới, REST/OpenAPI hoặc React. Tạo/khóa/mở/reset tài khoản, chuyển
phòng, vai trò và HR-DELETE-010 giữ backend/guard cũ. Hộp xác minh giữ focus,
không hiển thị mật khẩu hiện tại.

Scope riêng: 12 file sửa (11 application/test + README), 7 file mới, 0 file xóa;
seal 63 file tại `.local/hr-ui011/source-scope.json`. Rollback archive chứa 56
file gốc, bao gồm thay đổi HR-DELETE-010 có trước; không dùng Git HEAD để thay
bản gốc dirty. File chính: [views](../../custom_addons/tp_hr_workspace/views/hr_ui.xml),
[counts/actions](../../custom_addons/tp_hr_workspace/models/hr_ui.py),
[table](../../custom_addons/tp_hr_workspace/static/src/table/table.js),
[profile](../../custom_addons/tp_hr_workspace/static/src/profile/employee_profile.js),
[tests](../../custom_addons/tp_hr_workspace/tests/test_hr_ui.py).

## Kết quả kiểm thực tế

| Nhóm | Kết quả và bằng chứng |
| --- | --- |
| Odoo trên test với fixture giả | `-u tp_organization,tp_hr_workspace --test-tags /tp_organization,/tp_hr_workspace --no-http --stop-after-init`: **77 tests, 0 failed/0 error**; [log bản cuối](../../.local/hr-ui011/tests-final.log) |
| Odoo sau restore main→test | Cùng command/source, **77 tests, 0 failed/0 error**; [tests-restored.log](../../.local/hr-ui011/tests-restored.log). Có transaction tests count/rules/company/archived/action/menu, và regression account/identity/delete/import/organization; không dùng React tests |
| HOOT | HR35 tests +2KD = **37/163 assertions**, Home30 +1KD = **31/179 assertions**, đều PASS; [HR](../../.local/hr-ui011/hoot-hr.txt), [Home](../../.local/hr-ui011/hoot-home.txt), [report](../../.local/hr-ui011/hoot-result.json) |
| Browser hành vi trên fixture giả | **16/16 nhóm**, 0 console/page errors; backend limit/domain/order/offset, group/count/clear/back, 3 trạng thái account, 5 tab/skills/chatter, save/cancel/dirty warning, 320px/mobile actions, count/drilldown, label CRUD/cancel, hierarchy 3 tầng/collapse, import lock/retry/datetime, empty/focus/reduced-motion, officer/staff deny, Home/KD; [report](../../.local/hr-ui011/acceptance-result.json) |
| Browser catalog/import | **5/5 nhóm**, 0 errors: UI tạo/đọc/sửa phòng/chức vụ/nơi làm việc, chỉ ORM xóa fixture mới; Excel hợp lệ preview→apply một employee, mã TP đúng, không tạo account, retry giữ kết quả, nhập lặp skip không trùng; [report](../../.local/hr-ui011/catalog-import-result.json) |
| Password/focus và delete entry | **2/2**, 0 errors: gõ mật khẩu giả sai vào modal, search sidebar giữ, error đóng trả focus; preview xóa mở từ Tác vụ rồi Hủy, không execute; [report](../../.local/hr-ui011/protected-result.json). Không ghi giá trị mật khẩu trong ảnh/report |
| Smoke bản sao sạch/main | **25/25 nhóm mỗi cổng**, 0 console/page errors, 0 yêu cầu ghi nghiệp vụ. 1440/390/320px, 6 list + detail khi có dữ liệu, hierarchy, edit không sửa field→Hủy, identity focus→Hủy, permanent-delete preview→Hủy, Home/KD; [test](../../.local/hr-ui011/smoke-test/report.json), [main](../../.local/hr-ui011/smoke-main/report.json). Locations/categories trống nên không có detail main; detail đã kiểm bằng fixture trên test |
| Static/handoff | Ruff 2 Python file PASS; XML12 hợp lệ; JS syntax table/profile PASS; source seal63 khớp; `git diff --check` PASS. Workflow finish/check ghi riêng trong state/status, không dùng nó thay nghiệm thu nghiệp vụ |

Các lượt Odoo/HOOT/browser lỗi ban đầu đã sửa và chạy lại, không tính là pass.
Odoo còn cảnh báo thiếu markdown2, icon thiếu title/field Image trùng nhãn và
filestore GC WinError5 Windows; không có test failure. Blobs được kiểm SHA riêng.

## Ảnh trước/sau và tự đánh giá

Hai bộ **before** và **after-verified** có 15 màn × 4 viewport = 60 cặp, cùng
admin/test, route/ID, viewport và dataset fixture gốc. Desktop 1440×900/1280×800,
mobile390×844/320×844. Đã đối chiếu route/viewport bằng report, mở contact sheet
và ảnh riêng để tự xem. Bảng dưới có link từng ảnh.

**final-source** bổ sung 60 ảnh của source cuối: đổi nhãn số cấp dưới và empty
detail sublist. Bộ này chụp sau test import nên có thêm lô/1employee giả trên
test; **không gọi đây là dataset khớp before**. Một lượt capture dính session
expired đã loại và chụp lại cả 60; report cuối không modal/0 errors.
Các bộ `after`, `after2` và ảnh lỗi không dùng làm bằng chứng đạt.

| Màn hình | Trước (1440 / 1280 / 390 / 320) | Sau cùng dataset (1440 / 1280 / 390 / 320) | Source cuối (1440 / 1280 / 390 / 320) |
| --- | --- | --- | --- |
| Danh sách nhân viên | [1440](../../.local/hr-ui011/before/employees-1440.png) · [1280](../../.local/hr-ui011/before/employees-1280.png) · [390](../../.local/hr-ui011/before/employees-390.png) · [320](../../.local/hr-ui011/before/employees-320.png) | [1440](../../.local/hr-ui011/after-verified/employees-1440.png) · [1280](../../.local/hr-ui011/after-verified/employees-1280.png) · [390](../../.local/hr-ui011/after-verified/employees-390.png) · [320](../../.local/hr-ui011/after-verified/employees-320.png) | [1440](../../.local/hr-ui011/final-source/employees-1440.png) · [1280](../../.local/hr-ui011/final-source/employees-1280.png) · [390](../../.local/hr-ui011/final-source/employees-390.png) · [320](../../.local/hr-ui011/final-source/employees-320.png) |
| Hồ sơ nhân viên | [1440](../../.local/hr-ui011/before/employee-1440.png) · [1280](../../.local/hr-ui011/before/employee-1280.png) · [390](../../.local/hr-ui011/before/employee-390.png) · [320](../../.local/hr-ui011/before/employee-320.png) | [1440](../../.local/hr-ui011/after-verified/employee-1440.png) · [1280](../../.local/hr-ui011/after-verified/employee-1280.png) · [390](../../.local/hr-ui011/after-verified/employee-390.png) · [320](../../.local/hr-ui011/after-verified/employee-320.png) | [1440](../../.local/hr-ui011/final-source/employee-1440.png) · [1280](../../.local/hr-ui011/final-source/employee-1280.png) · [390](../../.local/hr-ui011/final-source/employee-390.png) · [320](../../.local/hr-ui011/final-source/employee-320.png) |
| Danh sách phòng ban | [1440](../../.local/hr-ui011/before/departments-1440.png) · [1280](../../.local/hr-ui011/before/departments-1280.png) · [390](../../.local/hr-ui011/before/departments-390.png) · [320](../../.local/hr-ui011/before/departments-320.png) | [1440](../../.local/hr-ui011/after-verified/departments-1440.png) · [1280](../../.local/hr-ui011/after-verified/departments-1280.png) · [390](../../.local/hr-ui011/after-verified/departments-390.png) · [320](../../.local/hr-ui011/after-verified/departments-320.png) | [1440](../../.local/hr-ui011/final-source/departments-1440.png) · [1280](../../.local/hr-ui011/final-source/departments-1280.png) · [390](../../.local/hr-ui011/final-source/departments-390.png) · [320](../../.local/hr-ui011/final-source/departments-320.png) |
| Chi tiết phòng ban | [1440](../../.local/hr-ui011/before/department-1440.png) · [1280](../../.local/hr-ui011/before/department-1280.png) · [390](../../.local/hr-ui011/before/department-390.png) · [320](../../.local/hr-ui011/before/department-320.png) | [1440](../../.local/hr-ui011/after-verified/department-1440.png) · [1280](../../.local/hr-ui011/after-verified/department-1280.png) · [390](../../.local/hr-ui011/after-verified/department-390.png) · [320](../../.local/hr-ui011/after-verified/department-320.png) | [1440](../../.local/hr-ui011/final-source/department-1440.png) · [1280](../../.local/hr-ui011/final-source/department-1280.png) · [390](../../.local/hr-ui011/final-source/department-390.png) · [320](../../.local/hr-ui011/final-source/department-320.png) |
| Danh sách chức vụ | [1440](../../.local/hr-ui011/before/jobs-1440.png) · [1280](../../.local/hr-ui011/before/jobs-1280.png) · [390](../../.local/hr-ui011/before/jobs-390.png) · [320](../../.local/hr-ui011/before/jobs-320.png) | [1440](../../.local/hr-ui011/after-verified/jobs-1440.png) · [1280](../../.local/hr-ui011/after-verified/jobs-1280.png) · [390](../../.local/hr-ui011/after-verified/jobs-390.png) · [320](../../.local/hr-ui011/after-verified/jobs-320.png) | [1440](../../.local/hr-ui011/final-source/jobs-1440.png) · [1280](../../.local/hr-ui011/final-source/jobs-1280.png) · [390](../../.local/hr-ui011/final-source/jobs-390.png) · [320](../../.local/hr-ui011/final-source/jobs-320.png) |
| Chi tiết chức vụ | [1440](../../.local/hr-ui011/before/job-1440.png) · [1280](../../.local/hr-ui011/before/job-1280.png) · [390](../../.local/hr-ui011/before/job-390.png) · [320](../../.local/hr-ui011/before/job-320.png) | [1440](../../.local/hr-ui011/after-verified/job-1440.png) · [1280](../../.local/hr-ui011/after-verified/job-1280.png) · [390](../../.local/hr-ui011/after-verified/job-390.png) · [320](../../.local/hr-ui011/after-verified/job-320.png) | [1440](../../.local/hr-ui011/final-source/job-1440.png) · [1280](../../.local/hr-ui011/final-source/job-1280.png) · [390](../../.local/hr-ui011/final-source/job-390.png) · [320](../../.local/hr-ui011/final-source/job-320.png) |
| Danh sách nơi làm việc | [1440](../../.local/hr-ui011/before/locations-1440.png) · [1280](../../.local/hr-ui011/before/locations-1280.png) · [390](../../.local/hr-ui011/before/locations-390.png) · [320](../../.local/hr-ui011/before/locations-320.png) | [1440](../../.local/hr-ui011/after-verified/locations-1440.png) · [1280](../../.local/hr-ui011/after-verified/locations-1280.png) · [390](../../.local/hr-ui011/after-verified/locations-390.png) · [320](../../.local/hr-ui011/after-verified/locations-320.png) | [1440](../../.local/hr-ui011/final-source/locations-1440.png) · [1280](../../.local/hr-ui011/final-source/locations-1280.png) · [390](../../.local/hr-ui011/final-source/locations-390.png) · [320](../../.local/hr-ui011/final-source/locations-320.png) |
| Chi tiết nơi làm việc | [1440](../../.local/hr-ui011/before/location-1440.png) · [1280](../../.local/hr-ui011/before/location-1280.png) · [390](../../.local/hr-ui011/before/location-390.png) · [320](../../.local/hr-ui011/before/location-320.png) | [1440](../../.local/hr-ui011/after-verified/location-1440.png) · [1280](../../.local/hr-ui011/after-verified/location-1280.png) · [390](../../.local/hr-ui011/after-verified/location-390.png) · [320](../../.local/hr-ui011/after-verified/location-320.png) | [1440](../../.local/hr-ui011/final-source/location-1440.png) · [1280](../../.local/hr-ui011/final-source/location-1280.png) · [390](../../.local/hr-ui011/final-source/location-390.png) · [320](../../.local/hr-ui011/final-source/location-320.png) |
| Sơ đồ quản lý | [1440](../../.local/hr-ui011/before/hierarchy-1440.png) · [1280](../../.local/hr-ui011/before/hierarchy-1280.png) · [390](../../.local/hr-ui011/before/hierarchy-390.png) · [320](../../.local/hr-ui011/before/hierarchy-320.png) | [1440](../../.local/hr-ui011/after-verified/hierarchy-1440.png) · [1280](../../.local/hr-ui011/after-verified/hierarchy-1280.png) · [390](../../.local/hr-ui011/after-verified/hierarchy-390.png) · [320](../../.local/hr-ui011/after-verified/hierarchy-320.png) | [1440](../../.local/hr-ui011/final-source/hierarchy-1440.png) · [1280](../../.local/hr-ui011/final-source/hierarchy-1280.png) · [390](../../.local/hr-ui011/final-source/hierarchy-390.png) · [320](../../.local/hr-ui011/final-source/hierarchy-320.png) |
| Danh sách lô nhập | [1440](../../.local/hr-ui011/before/imports-1440.png) · [1280](../../.local/hr-ui011/before/imports-1280.png) · [390](../../.local/hr-ui011/before/imports-390.png) · [320](../../.local/hr-ui011/before/imports-320.png) | [1440](../../.local/hr-ui011/after-verified/imports-1440.png) · [1280](../../.local/hr-ui011/after-verified/imports-1280.png) · [390](../../.local/hr-ui011/after-verified/imports-390.png) · [320](../../.local/hr-ui011/after-verified/imports-320.png) | [1440](../../.local/hr-ui011/final-source/imports-1440.png) · [1280](../../.local/hr-ui011/final-source/imports-1280.png) · [390](../../.local/hr-ui011/final-source/imports-390.png) · [320](../../.local/hr-ui011/final-source/imports-320.png) |
| Lô nhập — chọn tệp | [1440](../../.local/hr-ui011/before/import-draft-1440.png) · [1280](../../.local/hr-ui011/before/import-draft-1280.png) · [390](../../.local/hr-ui011/before/import-draft-390.png) · [320](../../.local/hr-ui011/before/import-draft-320.png) | [1440](../../.local/hr-ui011/after-verified/import-draft-1440.png) · [1280](../../.local/hr-ui011/after-verified/import-draft-1280.png) · [390](../../.local/hr-ui011/after-verified/import-draft-390.png) · [320](../../.local/hr-ui011/after-verified/import-draft-320.png) | [1440](../../.local/hr-ui011/final-source/import-draft-1440.png) · [1280](../../.local/hr-ui011/final-source/import-draft-1280.png) · [390](../../.local/hr-ui011/final-source/import-draft-390.png) · [320](../../.local/hr-ui011/final-source/import-draft-320.png) |
| Lô nhập — đối chiếu | [1440](../../.local/hr-ui011/before/import-preview-1440.png) · [1280](../../.local/hr-ui011/before/import-preview-1280.png) · [390](../../.local/hr-ui011/before/import-preview-390.png) · [320](../../.local/hr-ui011/before/import-preview-320.png) | [1440](../../.local/hr-ui011/after-verified/import-preview-1440.png) · [1280](../../.local/hr-ui011/after-verified/import-preview-1280.png) · [390](../../.local/hr-ui011/after-verified/import-preview-390.png) · [320](../../.local/hr-ui011/after-verified/import-preview-320.png) | [1440](../../.local/hr-ui011/final-source/import-preview-1440.png) · [1280](../../.local/hr-ui011/final-source/import-preview-1280.png) · [390](../../.local/hr-ui011/final-source/import-preview-390.png) · [320](../../.local/hr-ui011/final-source/import-preview-320.png) |
| Lô nhập — kết quả | [1440](../../.local/hr-ui011/before/import-applied-1440.png) · [1280](../../.local/hr-ui011/before/import-applied-1280.png) · [390](../../.local/hr-ui011/before/import-applied-390.png) · [320](../../.local/hr-ui011/before/import-applied-320.png) | [1440](../../.local/hr-ui011/after-verified/import-applied-1440.png) · [1280](../../.local/hr-ui011/after-verified/import-applied-1280.png) · [390](../../.local/hr-ui011/after-verified/import-applied-390.png) · [320](../../.local/hr-ui011/after-verified/import-applied-320.png) | [1440](../../.local/hr-ui011/final-source/import-applied-1440.png) · [1280](../../.local/hr-ui011/final-source/import-applied-1280.png) · [390](../../.local/hr-ui011/final-source/import-applied-390.png) · [320](../../.local/hr-ui011/final-source/import-applied-320.png) |
| Danh sách nhãn | [1440](../../.local/hr-ui011/before/categories-1440.png) · [1280](../../.local/hr-ui011/before/categories-1280.png) · [390](../../.local/hr-ui011/before/categories-390.png) · [320](../../.local/hr-ui011/before/categories-320.png) | [1440](../../.local/hr-ui011/after-verified/categories-1440.png) · [1280](../../.local/hr-ui011/after-verified/categories-1280.png) · [390](../../.local/hr-ui011/after-verified/categories-390.png) · [320](../../.local/hr-ui011/after-verified/categories-320.png) | [1440](../../.local/hr-ui011/final-source/categories-1440.png) · [1280](../../.local/hr-ui011/final-source/categories-1280.png) · [390](../../.local/hr-ui011/final-source/categories-390.png) · [320](../../.local/hr-ui011/final-source/categories-320.png) |
| Chi tiết nhãn | [1440](../../.local/hr-ui011/before/category-1440.png) · [1280](../../.local/hr-ui011/before/category-1280.png) · [390](../../.local/hr-ui011/before/category-390.png) · [320](../../.local/hr-ui011/before/category-320.png) | [1440](../../.local/hr-ui011/after-verified/category-1440.png) · [1280](../../.local/hr-ui011/after-verified/category-1280.png) · [390](../../.local/hr-ui011/after-verified/category-390.png) · [320](../../.local/hr-ui011/after-verified/category-320.png) | [1440](../../.local/hr-ui011/final-source/category-1440.png) · [1280](../../.local/hr-ui011/final-source/category-1280.png) · [390](../../.local/hr-ui011/final-source/category-390.png) · [320](../../.local/hr-ui011/final-source/category-320.png) |

[Contact sheet bản cuối](../../.local/hr-ui011/final-source/contact.jpg),
[sơ đồ 3 tầng](../../.local/hr-ui011/hierarchy-three-levels.png),
[nút mobile](../../.local/hr-ui011/mobile-actions.png),
[preview Excel](../../.local/hr-ui011/valid-import-preview.png),
[kết quả import](../../.local/hr-ui011/valid-import-applied.png).
Ảnh/report nằm ignored `.local/`, không chứa mật khẩu/session; không đưa vào Git.

Tự đánh giá: bảng và form đã thay bố cục thực; tiêu đề/phân cấp thông tin rõ,
form danh mục có nội dung riêng, các empty state giải thích mục đích. Bảng nhiều
cột cuộn ngang trong vùng nội dung trên màn hẹp để giữ cỡ chữ, không tràn toàn
trang. Sơ đồ có thể còn nhiều node gốc vì dữ liệu chưa khai báo manager; UI ghi
rõ thay vì tự tạo quan hệ. Main chỉ có empty locations/categories nên không
tạo dữ liệu để lấp khoảng trống. Đây là tự review, chưa là duyệt hình thức.

## Backup, restore, áp main và bảo toàn

1. Backup A: `backup-tp_tanphat_dev-20261113T032204623692Z`, **600 bảng/666 blob**.
   Helper sao lưu test trước restore tại `backup-tp_tanphat_test-20261113T032901396088Z`.
   Restore vào đúng canonical test: khớp **600 rowsets/666 blob/432 sequence**,
   neutralize cron/mail/UUID/baseURL trước HTTP; [evidence](../../.local/hr-ui011/restore-evidence.json).
   Không DB thứ ba, không test→main. Test fixture trước đó còn trong backup test,
   không trong runtime sạch sau restore.
2. Diễn tập nâng cấp trên bản sao main bằng HR+organization regression: 77/77.
   So600 bảng: 580 rowsets giữ tuyệt đối,20 delta metadata/assets/bus/trigger;
   account/password/nhân viên/version/resource/phòng/job/mapping/role/grant/
   sequence nghiệp vụ giữ. ACL953 chỉ171 write_date, group57 chỉ2 write_date;
   632 nonasset attachment rows và checksum blobs giữ. [preservation rehearsal](../../.local/hr-ui011/preservation-rehearsal.json).
3. Main từng mở lại ngoài lệnh start của task ở10:22 và10:37 local. Không quy
   thuộc người/phiên. Giữa A và backup cuối có **2 phòng ban mới**,2 mail_message,
   assets/bus/presence; giữ thay đổi có sẵn này, không đồng bộ test đè main.
   [A→B](../../.local/hr-ui011/rowdiff-main-A-to-B.json). Test sạch có13 phòng,
   main có15 phòng; cả hai40 employees/28 users/9 active/1 HEAD.
4. Backup B cuối: **`backup-tp_tanphat_dev-20261113T033657607572Z`**,
   600 bảng/666 blob. Snapshot preupgrade khớp cả 600 rowsets của backup B.
   Lượt upgrade đầu chạy sau khi gate không còn sessions thất bại do server
   mở lại; đây là lỗi điều phối lệnh, không ghi là độc quyền. Upgrade kết thúc
   exit0, đối chiếu không đổi nghiệp vụ. Đã dừng đúng runtime, kiểm **0 sessions**,
   chạy lại `-u tp_hr_workspace --no-http --stop-after-init` trong cùng lệnh có
   guard; cuối lệnh xác nhận HTTP vẫn dừng. [log cuối](../../.local/hr-ui011/main-upgrade-exclusive.log).
   Không chạy test nghiệp vụ hoặc ghi fixture trên main.
5. Trước mở HTTP: **585/600 bảng giữ tuyệt đối**;15 delta chỉ metadata/view/
   action/menu/field/module và2 cron triggers/signaling do2 lượt upgrade. ACL953
   giữ policy, chỉ3 write_date;57 group nguyên;632 nonasset row/blob nguyên.
   Sau smoke **579/600 rowsets nguyên**, thêm bus/presence/login/device và
   wizard tạm do mở/hủy identity/account. Không đổi res_users/password,
   employee/version/resource/phòng/job/import/role/grant/mapping/mã TP/audit
   nghiệp vụ. Không có employee/user UI011 trên runtime sạch.
   [đối chiếu600 bảng](../../.local/hr-ui011/preservation-summary.json),
   [blob/ACL sau smoke](../../.local/hr-ui011/preservation-main-smoke.json),
   [delta sau smoke](../../.local/hr-ui011/rowdiff-main-smoke.json).
6. Main và test đang chạy. Main smoke25/25/0 errors và ảnh thật đã mở kiểm;
   chỉ đọc/mở/Hủy. Chưa thử xóa/khóa/đổi quyền/reset password người thật.

Backup riêng ở `.local/hr001/`; đầy đủ dump/filestore/SHA/source/config/sequence.
[Runbook triển khai/rollback](../../ops/runbooks/HR_UI_011_DEPLOY_AND_ROLLBACK.md)
ghi đúng scope. Source-only rollback rồi upgrade1.9.0 **chưa đủ** vì metadata
binding mới; rollback an toàn dùng backup main B sau đánh giá giao dịch sau
triển khai, tuyệt đối không restore test lên main.

## Cổng còn lại và bước tiếp

Technical verification và áp18069 đã đạt theo bằng chứng trên. Chưa có audit
độc lập: subagent không khởi chạy được vì model kế thừa không khả dụng; các
ảnh/logic được tự review. Mobile là giả lập, chưa thiết bị thật; chưa kiểm
extension quản lý mật khẩu/autofill trong lượt này (giữ guard/coverage009).

Người dùng Ctrl+F5 và xem các đường dẫn main ở đầu tài liệu, góp ý bố cục,
màu và thao tác. **Visual feedback, business acceptance và pilot authorization
chưa được xác nhận**; test kỹ thuật không thay các cổng đó. Không mở module hay
thay chính sách nghiệp vụ mới. Ngoài task này trở về vai trò điều phối mặc định.
