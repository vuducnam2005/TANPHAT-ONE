# UI-HOME-002 — Trang chủ theo không gian làm việc

Ngày 07/11/2026, Asia/Saigon. CHG-20261107-004. Căn cứ: [prompt](../prompts/CLAUDE_UI_HOME_002_WORKSPACE_ORGANIZATION.md), DEC-030, bàn giao KD-UI-004 CHG-20261107-003 (checker PASS, checkpoint đã đóng).

## 1. Phạm vi và nguồn

Chỉ thay trình bày/catalog/tìm kiếm của `tp_web_home`; menu service native là nguồn duy nhất. Không đổi model, quyền, menu/action XML, thứ tự root Odoo, Home Action, dữ liệu hoặc phụ thuộc addon (`web`). Mapping không sinh menu. Clone riêng: `tp_tanphat_home002_20261107`, cổng 18589, source/config/data trong `.local/ui-home002`; không dùng clone KD-UI-004.

## 2. Inventory trước triển khai

| XMLID menu | Nhãn Trang chủ | Khu | Đích đến giữ nguyên |
| --- | --- | --- | --- |
| `tp_kd_workspace.menu_kd` | Kế hoạch Kinh doanh | Không gian làm việc | Action Tổng quan KH-KD của root menu; không mở rộng thành tile các lá |
| `project_todo.menu_todo_todos` | Việc cá nhân | Công việc cá nhân | Action/path runtime To-do |
| `calendar.mail_menu_calendar` | Lịch làm việc | Công việc cá nhân | Action/path runtime Calendar |
| `mail.menu_root_discuss` | Trao đổi | Công việc cá nhân | Action/path runtime Discuss |
| `tp_project.menu_tp_projects` | TP Projects | Ứng dụng nghiệp vụ | `tp_project.action_tp_projects`, lá của `tp_core.menu_platform` |
| `tp_contract.menu_tp_contracts` | TP Contracts | Ứng dụng nghiệp vụ | `tp_contract.action_tp_contracts`, lá của cùng root |
| `project.menu_main_pm` | Công việc dự án | Ứng dụng nghiệp vụ | Action/path runtime Project, alias Project giữ lại |
| `crm.crm_menu_root` | CRM | Ứng dụng nghiệp vụ | Action/path runtime CRM |
| `contacts.menu_contacts` | Khách hàng và đối tác | Ứng dụng nghiệp vụ | Action/path runtime Contacts |
| `tp_core.menu_work_items` | Danh mục công việc | Ứng dụng nghiệp vụ | `tp_core.action_work_items`, lá của cùng root |
| `spreadsheet_dashboard.spreadsheet_dashboard_menu_root` | Bảng tổng hợp | Ứng dụng nghiệp vụ | Action/path runtime Dashboard |
| `account.menu_finance` | Hóa đơn | Ứng dụng nghiệp vụ | Action/path runtime Invoicing |
| `hr_timesheet.timesheet_menu_root` | Giờ làm việc | Ứng dụng nghiệp vụ | Action/path runtime Timesheets; không gọi là chấm công vào-ra |
| `hr.menu_hr_root` | Nhân sự | Ứng dụng nghiệp vụ | Action/path runtime HR; không dựng workspace phòng ban |
| `hr_expense.menu_hr_expense_root` | Chi phí | Ứng dụng nghiệp vụ | Action/path runtime Expenses |
| `base.menu_administration` | Cài đặt | Quản trị hệ thống | Action/path runtime Settings |
| `base.menu_management` | Ứng dụng Odoo | Quản trị hệ thống | Action/path runtime Apps |
| `base.menu_tests`, `utm.menu_link_tracker_root` | Tên native | Quản trị hệ thống | Chỉ khi có trong menu user |
| App chưa biết | Tên native | Ứng dụng nghiệp vụ | Giữ nguyên menu/action/path/icon; không dedup theo action |

Mọi hàng đều có điều kiện: tồn tại trong cây menu đã lọc quyền, có `actionID`. ID và URL lấy runtime, không hardcode ID số. Chỉ `tp_core.menu_platform` mở rộng lá; dedup bằng menu ID. Portal/public theo guard backend hiện hành. Inventory runtime của admin/KH-KD/internal bổ sung vào acceptance sau khi chạy clone.

## 3. Bố cục

Desktop: vùng nội dung tối đa 1360px; header thấp, thương hiệu trái và tìm kiếm phải. KH-KD là một thẻ ngang xanh than rộng khoảng 560px, không kéo kín màn hình. Cá nhân có ba shortcut gọn. Nghiệp vụ là lưới 5–6 ô tùy bề rộng; quản trị gọn cuối trang. Mỗi khu có tiêu đề, khu rỗng ẩn.

```text
TANPHAT ONE                         [Tìm không gian, ứng dụng…]
Không gian làm việc

Không gian làm việc
[biểu tượng  Kế hoạch Kinh doanh                          ]
[            Hồ sơ, kế hoạch và điều hành KH-KD          ]

Công việc cá nhân
[Việc cá nhân] [Lịch làm việc] [Trao đổi]

Ứng dụng nghiệp vụ
[TP Projects] [TP Contracts] [Công việc dự án] [CRM] [...]
[…          ] […          ] […               ] […] [...]

Quản trị hệ thống
[Cài đặt] [Ứng dụng Odoo]
```

Mobile: header xếp dọc; ô tìm full width, không autofocus; KH-KD một hàng đủ nhãn/mô tả. App hai cột với icon trên nhãn để không bóp tiếng Việt; dưới 340px hoặc khi zoom cần thì một cột. Tablet 3–4 cột. Cuộn dọc thực trên `.o_tp_web_home.o_action`; không che tràn ngang bằng `overflow-x:hidden`.

## 4. Token, icon và motion

- Nền `#F4F6F8`, mặt `#FFFFFF`, workspace `#17324D`, action `#255F85`, chữ `#1F2937`, phụ `#607287`, viền `#D9E2EC`.
- Font Odoo hiện có hỗ trợ tiếng Việt; không tải font. Brand 28px, khu 17px, app 15px, mô tả 13px. Nhịp 8/12/16/24, bo 10px.
- SVG cục bộ cho KH-KD (kế hoạch/hồ sơ), TP Projects (hồ sơ/cầu đường), TP Contracts (tập hợp đồng), danh mục (danh sách). App native dùng icon gốc trong khung 48–56px, fallback chữ viết tắt một lần khi lỗi.
- Hover 150ms đổi nền/viền, không animation lặp/đợt bay vào. Focus ring rõ, target >=44px. Reduced motion tắt transition.

Đã đối chiếu brief: ưu tiên một workspace có thật, tránh hero cao và ô trống; không tạo màu/icon ngẫu nhiên. Không đổi navbar/theme ngoài Trang chủ.

## 5. Tải menu, tìm và điều hướng

Chưa có response menu mới thì không dựng catalog. Loading/error/Thử lại riêng với empty. Lỗi fresh-menu không được dùng cây IndexedDB cũ. Retry gọi menu service reload; không lưu catalog localStorage. Khi load lại menu, catalog phản ứng theo service.

Thứ tự group và thứ tự tile được quyết định trước filter, để Enter bằng kết quả đầu hiển thị. Tìm không dấu/có dấu, brand/alias; Escape và nút xóa; Enter khi IME composing hoặc keyCode229 không mở app. Anchor native giữ Ctrl/Cmd/Shift/middle click, click thường dùng `menu.selectMenu`; không ghi `res.users.action_id` hay ép reload.

## 6. Kiểm thử và bàn giao

[Acceptance](../demo/UI_HOME_002_ACCEPTANCE.md) ghi kết quả thực. Baseline ảnh trước sửa trên clone; Odoo/HOOT/browser với actor khác nhau, search/error/IME/navigation/guard, 7 viewport và zoom 125/150%. Upgrade chỉ `tp_web_home` sau backup verify; fingerprint dữ liệu/user/password/Home Action/groups/ACL/rule/grant trước-sau. Dev chỉ smoke đọc/điều hướng. Không commit/push; audit và business/pilot task khác giữ riêng.

## 7. As-built và inventory runtime

Đã áp `tp_web_home` 20.0.1.2.0 lên dev 18069, 07/11/2026. Group order: `workspace → personal → business → system`; thứ tự tile theo catalog, app chưa biết giữ thứ tự server. Lưới desktop 6/5/4/3 cột theo breakpoint; mobile 2 (1 dưới 340px). Mỗi lần mount Home gọi `menu.reload()` và chỉ mở catalog sau response được áp, không dùng lại danh sách quyền riêng. Retry có sequence guard khi component bị hủy; không autofocus cả desktop và mobile. CSS dùng `unquote` cho hàm CSS min để tương thích compiler Sass hiện có.

| Lối vào | XMLID | URL admin đã kiểm | Ghi chú |
| --- | --- | --- | --- |
| KH-KD | `tp_kd_workspace.menu_kd` | `/odoo/action-510` | Giữ root và sidebar/Tổng quan KD-UI-004 |
| TP Projects | `tp_project.menu_tp_projects` | `/odoo/action-289` | Hồ sơ dự án và phân công |
| TP Contracts | `tp_contract.menu_tp_contracts` | `/odoo/action-509` | Hợp đồng và phiên bản hồ sơ |
| Công việc dự án | `project.menu_main_pm` | `/odoo/project` | Project native; actor KH-KD editor không có menu này và không được dựng thêm |
| Danh mục công việc | `tp_core.menu_work_items` | `/odoo/action-79` | Giữ lá, không tile root TP trùng |
| Cá nhân | `project_todo.menu_todo_todos`, `calendar.mail_menu_calendar`, `mail.menu_root_discuss` | `/odoo/to-do`, `/odoo/calendar`, `/odoo/discuss` | Đúng thứ tự này |
| Quản trị | `base.menu_administration`, `base.menu_management` | `/odoo/settings`, `/odoo/apps` | KH-KD editor có Apps nhưng không Settings theo menu server; không tự ẩn theo tên vai trò |

Các số ID trên là evidence runtime ngày kiểm, không hardcode vào catalog. Admin17 tile, KH-KD editor 13 tile; nội dung menu HTTP trước/sau bằng nhau. Nhân sự có URL khác nhau theo actor (`/odoo/employees` admin; `/odoo/action-207` KH-KD), được giữ nguyên. Fixture internal không workspace thấy2 app; không mở quyền cho fixture để thêm tile. Chỉ fixture clone có thêm công ty/test accounts; không đưa sang dev.
