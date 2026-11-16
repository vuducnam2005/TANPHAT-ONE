# HR-UI-011 — Danh sách và hồ sơ HR thống nhất

Ngày 13/11/2026, yêu cầu trực tiếp triển khai và áp main sau test/backup/restore.
CHG-20261113-002. Ngoại lệ vai trò điều phối chỉ trong task này; không commit/push.

## Khảo sát source và thiết kế trước code

| Màn hình | Model / action / view (namespace tp_hr_workspace) | Hiện có / vấn đề | Cách sửa |
| --- | --- | --- | --- |
| Nhân viên | hr.employee / action_employees / employee_list, employee_form | Hai menu cùng action; model JS ép nhóm; nút tài khoản không phân biệt | Một menu chính; danh sách phẳng, native group tùy chọn; avatar/tên, trạng thái và nút theo quyền |
| Hồ sơ | hr.employee / employee_form, employee_identity_org_form / tp_hr_profile | Có 5 tab, nhưng công việc/hồ sơ lặp; gradients và nhiều rule chồng | Header thông tin + bố cục 2 cột; 5 tab đúng tên; chuyển các khối hiện có, giữ guard và trường |
| Phòng ban | hr.department / action_departments / department_list | Màu thành cột chính; count core sudo; detail chưa thống nhất | Icon/điểm màu; count theo quyền + drilldown; form tổ chức và nhân viên, cấp trên/dưới |
| Chức vụ | hr.job / action_jobs / job_list, job_form | Sửa trực tiếp tại dòng; trạng thái checkbox; detail sơ sài | Form riêng; badge, count theo quyền; nhân viên và mô tả/trách nhiệm |
| Nơi làm việc | hr.work.location / action_locations / location_list | Form core, empty state thiếu hướng dẫn | Thông tin địa điểm có nhóm; empty state và CTA theo ACL |
| Sơ đồ | hr.employee / action_hierarchy / hierarchy core | Node rời khi thiếu parent; không giải thích | Hierarchy Odoo parent_id/child_ids, cấm kéo đổi manager; tên/chức vụ/phòng; ghi thiếu manager; search giữ quan hệ thật |
| Nhập | tp.hr.import.batch,line / action_import / import_list,form,lines | Thiếu tên lô/số dòng/applied; detail dồn một khối | Metadata + 4 bước UI tương ứng 3 state; badge kết quả từng dòng, tổng hợp xung đột |
| Nhãn | hr.employee.category / action_categories / categories_list | Tên cũ Thẻ; chỉ có tên | Đổi Nhãn; chip màu/count scope; form tên/màu và danh sách đang dùng |

Kiến trúc: native action/list/search/form/hierarchy; tái sử dụng tp_hr_table,
không thêm framework, không patch ListRenderer toàn cục, không đổi ACL/API.

## Ngôn ngữ thiết kế

Navy #183153 cho tiêu đề, Blue #2563EB cho thao tác/chọn, Teal #0F766E cho tổ
chức; nền #F4F7FB, nội dung trắng, viền #DCE4EF. Badge success #15803D,
warning #B45309, danger #B91C1C và neutral xám có nền nhạt tương ứng.
Giữ font của shell, bảng 14px, tiêu đề 24px, khoảng cách desktop 20px.
Sidebar 264px/rail 68px và navbar giữ nguyên. Không thêm navbar/sidebar.

Danh sách tập trung vào quét dữ liệu: tiêu đề/mô tả → search native và CTA cụ
thể → bảng có header xanh xám, hàng 44–48px → số kết quả/pager native. Native
facets và nút xóa bộ lọc dùng search model; backend giữ sort/domain/paging.
10/20/50/100 ghi rõ dòng hay nhóm; từng nhóm hiện số bản ghi và pager con.

```text
Danh sách nhân viên                     [Thêm nhân viên]
Mã, công việc và tài khoản trong phạm vi được xem
[Tìm kiếm + facets Odoo] [Lọc / Nhóm] [Xóa bộ lọc] [20 dòng] [1–20 / N]
Mã      Nhân viên      Phòng     Chức vụ     Login   Tình trạng   Thao tác
```

```text
[Quay lại] [Sửa hồ sơ / Lưu / Hủy]                  [Tác vụ]
Avatar  Họ tên                 Mã / Phòng / Chức vụ        Badge
Tổng quan | Cá nhân | Hồ sơ và năng lực | Tài khoản | Lịch sử
Thông tin công việc (cột 1)    Liên hệ (cột 2)
```

Form danh mục dùng header icon/tên + nhóm thông tin tổ chức, liên kết count và
notebook danh sách nhân viên. Import dùng tiến trình 4 bước có số thứ tự vì là
chuỗi thao tác thực; statusbar vẫn draft/preview/applied. Hierarchy dùng cạnh
native, chỉ vẽ khi có parent_id; node gốc thiếu manager được ghi rõ.

Đã so lại brief: không dùng bộ thẻ giống dashboard cho mọi trang; bảng là cấu
trúc chính, form là phân cấp thông tin. Điểm màu tổ chức tách badge trạng thái.
Hover 150ms, tab/drawer 200ms; focus rõ, reduced motion và tùy chọn shell giữ.

## Acceptance trước code

| ID | Actor / môi trường / thao tác | Kết quả cần kiểm |
| --- | --- | --- |
| A01 | Admin test mở các menu HR | Một Danh sách; không nhóm Hồ sơ rỗng; XML ID/action cũ còn |
| A02 | Admin test chọn 10/20/50/100, search/sort/group | Backend limit/domain/order đúng; clear group thật; group label/pager không đếm nhầm người |
| A03 | Admin test mở nhân viên rồi quay lại | Đúng ID, 5 tab, filter/page được giữ, readonly/edit/save/discard/dirty native |
| A04 | Admin/HR officer/staff giả | Trạng thái 3 loại thống nhất; account controls đúng quyền; RPC admin từ chối officer/staff |
| A05 | Admin test mở danh mục/list/detail | Count và drilldown cùng active/company/rules; không suy manager; label không cấp quyền |
| A06 | Admin test hierarchy fixture 3 tầng | parent/child thật, branch expand/collapse, mở detail, search không vẽ cạnh giả |
| A07 | Admin test import draft/preview/applied | 4 bước UI, 3 state, số dòng và kết quả; khóa sau áp dụng; không tự cấp account/quyền |
| A08 | Test empty/filter/no-match | Không có hàng trắng giả; CTA đúng đối tượng và ACL; lỗi native/loading có thể phục hồi |
| A09 | 1440×900,1280×800,390×844,320px | Mọi list/detail có before/after cùng role/dataset/route; không tràn trang; bảng có cuộn; keyboard/reduced motion |
| A10 | HR-DELETE-010 và account reauth | Giữ Tác vụ/password mỗi lần; sidebar không nhận autofill; không tác vụ xóa nổi ở dòng |
| A11 | Home/KH-KD smoke | Sidebar/navbar/list ngoài HR không bị CSS/patch ảnh hưởng |
| A12 | Main sau test | Backup DB+filestore, restore main→test verified, upgrade đúng addon; smoke read/open/Cancel; không ghi nghiệp vụ thật |

Evidence riêng tư: `.local/hr-ui011/`; không ghi password/session vào ảnh/log.
Technical verification, visual feedback, business acceptance và pilot tách riêng.
