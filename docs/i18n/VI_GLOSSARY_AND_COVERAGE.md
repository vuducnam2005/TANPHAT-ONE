# VI-001 — Thuật ngữ và độ phủ tiếng Việt

Chuẩn bị 02/11/2026 (Asia/Saigon), CHG-20261102-009, Batch B của [prompt NATIVE-DATA-002 + VI-001](../prompts/CLAUDE_NATIVE_DATA002_AND_VI001_COMPLETE_DEMO.md). Trạng thái: `VI_APPLIED_PENDING_AUDIT`. Phần đã làm là Việt hóa **nhãn giao diện** của các app đang cài trên `tp_tanphat_dev` cho admin. Việc này không phải nghiệm thu nghiệp vụ, và hệ thống chưa được Việt hóa hết: phần còn tiếng Anh được liệt kê trong [mục Gap](#4-gap-còn-lại).

## 1. Thuật ngữ

### 1.1 Giữ nguyên

| Từ | Lý do |
|---|---|
| TANPHAT ONE, TP Projects, TP Contracts, TP Survey, TP Design, TP Tasks, TP HR, TP Finance, TP Documents, TP Dashboard | Tên sản phẩm/phân hệ chuẩn ([TP_PRODUCT_NAMING](../architecture/TP_PRODUCT_NAMING.md)). |
| Odoo, BASE | Tên nền tảng và tên hệ thống tham chiếu. |
| CRM, ERP, WBS, API, URL, ID, PDF, Excel, IAP, SMS, Email | Viết tắt thông dụng. Lần đầu có thể chú giải; ví dụ “Tài khoản mua trong ứng dụng (IAP)”. |
| Mã quyền `TP_*`, `tp.*`, XML ID, route `/odoo/...`, state key, enum OpenAPI, tên module | Định danh kỹ thuật, không dịch. |

### 1.2 Tên app và menu gốc

| en_US | vi_VN | Ghi chú |
|---|---|---|
| Discuss | Trao đổi | Menu và client action `mail.action_discuss`. |
| To-do / To-dos | Việc cá nhân | Menu và action. |
| Calendar / Meetings | Lịch làm việc | Menu và action. “Calendars” (cấu hình) → Danh sách lịch. |
| Contacts | Khách hàng & đối tác | Menu và action. |
| Timesheets | Giờ làm việc | Menu và action theo dự án/nhân viên. “My Timesheets” → Giờ làm việc của tôi. |
| Employees | Nhân sự | Chỉ áp cho menu gốc `hr.menu_hr_root`. Danh sách bản ghi vẫn là “Nhân viên” vì đó là danh sách người. |
| Expenses | Chi phí | Đã có trong bản dịch native. |
| Invoicing | Hóa đơn | Đã có trong bản dịch native. Không gọi là kế toán đầy đủ hay TP Finance. |
| Dashboards | Bảng tổng hợp | Menu và client action. “Sections” → Nhóm bảng tổng hợp. |
| Settings | Cài đặt | Đã có trong bản dịch native. |
| Apps | Ứng dụng Odoo | Menu `base.menu_management` và action `base.open_module_tree`. |
| Project | Dự án | Đã có trong bản dịch native. |

### 1.3 Thao tác, trạng thái, giai đoạn To-do

| en_US | vi_VN | Cơ chế |
|---|---|---|
| New / Create | Mới / Tạo | Nút chung của web client đang hiển thị “Mới”, chưa phải “Tạo mới” (xem gap G1). |
| Edit, Save, Delete, Search, Filters, Group By | Chỉnh sửa, Lưu, Xoá, Tìm kiếm, Bộ lọc, Nhóm theo | Bản dịch native, đã khớp thuật ngữ (“Xoá” là cách viết native). |
| Draft | Nháp | Native. |
| Posted (hóa đơn, khoản chi) | Đã hạch toán | Overlay. Bản native dịch không thống nhất. |
| Submitted (khoản chi) | Đã gửi duyệt | Overlay. |
| In payment | Đang thanh toán | Overlay. |
| Done (task `1_done`) | Hoàn thành | Overlay. |
| Free (lịch, `show_as`) | Rảnh | Overlay. Bản native “Có hàng” là sai nghĩa. |
| Public / Members only (lịch) | Công khai / Chỉ thành viên lịch | Overlay. |
| Group (kênh Discuss) | Nhóm trò chuyện | Overlay. |
| In review / Returned (TP Contracts) | Đang rà soát / Trả lại | Catalog `tp_contract/i18n/vi.po`. |
| Inbox, Today, This Week, This Month, Later, Done, Cancelled | Hộp việc, Hôm nay, Tuần này, Tháng này, Để sau, Hoàn thành, Đã hủy | Bản dịch vi_VN của 7 giai đoạn cá nhân **của admin**. ID, sequence, fold và tên en_US giữ nguyên. |

## 2. Cơ chế

| Lớp | Cách làm | Nguồn trong Git |
|---|---|---|
| Ngôn ngữ | `odoo-bin i18n loadlang -l vi_VN` nạp catalog native của 88 module đã cài. Không tải gì từ mạng, không `-u all`. | Lệnh trong runbook ở mục 5. |
| Overlay native | Addon chỉ chứa bản dịch [`tp_i18n_vi`](../../custom_addons/tp_i18n_vi/README.md) với 37 mục (55 vị trí). Không có model, view, menu, ACL, rule hay asset (có test bảo đảm). Cài bằng `-i tp_i18n_vi`, rồi `-u tp_i18n_vi --i18n-overwrite`. | `custom_addons/tp_i18n_vi/i18n/vi.po` và 4 test. |
| Addon TP | `i18n/vi.po` cho `tp_core` (17), `tp_organization` (2), `tp_project` (42), `tp_contract` (193, chỉ nhãn), nạp bằng `odoo-bin i18n import -l vi_VN`. | `custom_addons/tp_*/i18n/vi.po` |
| Dữ liệu người dùng | `.local/vi001/vi_apply.py` (ngoài Git) chỉ đổi `lang` của admin và bản dịch vi_VN cho 7 giai đoạn cá nhân của admin. Có kiểm snapshot: user khác, giai đoạn của người khác và task không đổi. | — |

Nguyên tắc: không sửa `odoo/` hay `addons/`. Không thay chữ trên DOM lúc chạy. Không dịch mã quyền, tên dự án hay phòng ban (là dữ liệu). Không dịch thông báo Python của `tp_contract`/`tp_planning_api`, vì API trả thông báo đó cho React (gap G6).

Định dạng của vi_VN theo bản native: ngày `%d/%m/%Y`, giờ `%H:%M:%S`, dấu thập phân `,`, dấu nghìn `.`, tuần bắt đầu thứ Hai. VND không có số lẻ, ký hiệu đặt sau (ví dụ `310.000.000 ₫` trên hóa đơn nháp). Giá trị lưu, timezone và DTO của API không đổi.

## 3. Ma trận màn hình

Actor `admin` dùng vi_VN; `planner.dev` dùng en_US và là đối chứng. Chạy trên dev `http://127.0.0.1:18069`, DB `tp_tanphat_dev`, ở 1440px, 375px, zoom 125% và 150%. Ảnh chụp lưu tại `.local/vi001/shots/dev/` (ngoài Git). Cột “Còn tiếng Anh” liệt kê các chuỗi dò được trên màn hình, đã phân loại bằng tay.

| App / màn hình | Đường dẫn | Kết quả vi_VN | Còn tiếng Anh |
|---|---|---|---|
| Trang chủ | `/odoo` | Ô app đúng thuật ngữ. Phụ đề ô giữ tên gốc (Discuss, To-do…) theo thiết kế UI-HOME-001. | Phụ đề ô (cố ý). Ô “Project” trong gap G4. |
| Trao đổi | `/odoo/discuss` | Tên app, kênh, nút “Nhắn tin” | `Chat`, `Meetings`, `Unread`, `Search Conversation`, “Not quite…” của OdooBot (G2) |
| Việc cá nhân, kanban | `/odoo/to-do` | Hộp việc, Hôm nay, Tuần này, Tháng này, Để sau; Bộ lọc/Nhóm theo | `Save search`, nhãn aria `Kanban View` (G1) |
| Việc cá nhân, form | `/odoo/to-do/1` | Nhãn trường | Nội dung việc chào mừng native “Welcome Administrator!” (G5) |
| Lịch làm việc | `/odoo/calendar` | Tiêu đề, ngày, sự kiện | `My Calendars`, `Set Location`, `Week 45`, `Toggle Side Panel` (G2) |
| Khách hàng & đối tác | `/odoo/contacts` | List/kanban, Tác vụ: Xuất, Nhân bản, Lưu trữ, Xoá | `24 selected`, `Enrich` (G1/G2) |
| Dialog xuất | Tác vụ → Xuất | Tiêu đề, nút | `Updatable fields only`, `Save as export template` (G1) |
| Dialog xoá (chỉ mở, chưa xác nhận) | Tác vụ → Xoá | Câu xác nhận native tiếng Việt | Văn phong native mang tính đùa (“Tạm biệt, dữ liệu!”), ghi nhận để rà |
| CRM | `/odoo/crm`, `/odoo/crm/11` | Pipeline, giai đoạn, form | `Generate`, `My Opportunities`, `See AI-computed chances details` (G2) |
| Bảng tổng hợp | `/odoo/dashboards?dashboard_id=5`/`6` | Menu, nội dung dashboard TP | `Share`, `Close sidebar`; trên mobile tiêu đề là “Báo cáo tổng quan” (G3) |
| Hóa đơn | `/odoo/customer-invoices/4` | Nháp → Đã hạch toán, số tiền theo VND | `Journal Items`, `E-Invoice`, `Tax Excl./Tax Incl.`, `No messages yet.` (G2) |
| Dự án / TP Projects | `/odoo/project`, `/odoo/project/1` | Menu, tab, Trưởng dự án | `Tasks`, `Status`, `Burndown Chart`, `Select Customer`, `Select Tags`, `Project created` (G2). Tên dự án dev “Development Project - Assigned” là dữ liệu. |
| Nhiệm vụ | `/odoo/all-tasks` | Danh sách, giai đoạn | `Click to show more`, `Internal` (G2) |
| Giờ làm việc | `/odoo/timesheets` | Tên app và action | Nhãn aria loại view (G1) |
| Nhân sự | `/odoo/employees`, `/odoo/employees/13` | Tên app; danh sách “Nhân viên” | `Invited`, `New Employee Record`, `Load a Template`, `Pay Category` (G2) |
| Chi phí | `/odoo/expenses/7` | Trạng thái overlay | `Reimbursement`, `Existing Bill?`, `Yes (Match to Bill)`, `Scan`, `Action Required`; tên danh mục chi phí mẫu native (lorem) (G2/G5) |
| Ứng dụng Odoo | `/odoo/apps` | Tên app, bộ lọc | Tên module chưa cài (`Accounting`, `Helpdesk`…), là tên module nên giữ nguyên |
| Cài đặt | `/odoo/settings` | Các nhóm cài đặt chính | `Send GIFs`, `Translate Messages`, `Developer Tools`, `reCAPTCHA`, `Custom Call Servers`… (G2) |
| Hồ sơ / Tùy chọn | `/odoo/my-preferences`, menu người dùng | Tùy chọn của tôi, Đăng xuất, Hỗ trợ | `Online`, `My Subscription`, `Add Photo` (G1/G2) |

Kết quả kiểm:

| Kiểm | Kết quả |
|---|---|
| UI admin vi_VN, dev | 24 màn hình × 4 chế độ (1440, 375, zoom 125%, zoom 150%). Tất cả tải được, 0 lỗi console, 0 cuộn ngang, 0 nhãn menu/tab/statusbar bị cắt. Một lần “contacts” chưa tải được đã chạy lại đạt. |
| Mobile | Lưới app ở 375px có đủ 9 tên mới. Bảng tìm kiếm có “Bộ lọc/Nhóm theo”. Tiêu đề trên mobile lấy tên action hoặc tên JS, nên Nhân sự hiện “Nhân viên” và Bảng tổng hợp hiện “Báo cáo tổng quan” (G3). |
| en_US | `planner.dev` (en_US) thấy To-do, Project, Apps… bằng tiếng Anh, không có chuỗi overlay. Trên DB test, `vi_apply revert` đưa admin về en_US, thấy “Inbox/Today”, rồi `apply` lại. |
| Quyền | planner.dev vẫn AccessError ở Timesheets, Settings và Preferences như trước. So fingerprint với snapshot: `res_groups_users_rel`, `ir_model_access`, `ir_rule`, `res_company_users_rel`, `project_task`, `account_move`, `hr_expense`, `calendar_event`, `mail_message`, `discuss_channel` không đổi. Chỉ các cột tên đa ngôn ngữ, module, admin và log thay đổi. |
| Số liệu dashboard | `.local/vi001/dash_locale.py` chạy 10 nguồn pivot/chart của 2 dashboard TP với en_US và vi_VN. Khóa nhóm và giá trị giống hệt nhau trên cả test lẫn dev. |
| Odoo test | DB cô lập `tp_tanphat_data002_test`: `--test-tags /tp_project,/tp_i18n_vi` cho 0 failed, 0 error trên 16 test. Ruff đạt. 5 catalog có 0 mục chưa dịch, 0 fuzzy. Placeholder đã kiểm khi sinh catalog. |
| Menu | Probe 313 menu: 7 menu không có bản vi riêng, đều cố ý (Trang chủ, TANPHAT ONE, TP Projects, CRM, Email/IAP/SMS). Menu, selection và giai đoạn trên dev khớp DB test. |

## 4. Gap còn lại

| ID | Gap | Nguyên nhân | Hướng xử lý đề xuất |
|---|---|---|---|
| G1 | Nút và nhãn chung của web client: `New` hiện “Mới” (thuật ngữ là “Tạo mới”); `Cancel`, nhãn aria `Kanban/List/Pivot View`, `N selected`, `Save search`, `Updatable fields only`, `Shortcuts`, `Support`. | Odoo 20 tra chuỗi JS `_t` theo không gian tên của module `web`. Catalog của addon khác không ghi đè được nếu không sửa `addons/`. | Quyết định sản phẩm: chấp nhận “Mới”, hoặc mở một batch riêng có review để cấp bản dịch cho namespace `web`. |
| G2 | Chuỗi JS và view chưa có trong catalog native vi của mail, calendar, crm, account, project, hr, hr_expense, base_setup (danh sách theo màn hình ở mục 3). | Bản dịch upstream thiếu. Chuỗi trong view (`arch_db`) có thể overlay bằng `model_terms`, còn chuỗi JS gặp cùng giới hạn như G1. | Bổ sung `model_terms` vào `tp_i18n_vi` theo từng màn hình ưu tiên; chuỗi JS xử lý chung với G1. |
| G3 | Tiêu đề trên mobile lấy tên JS hoặc action: Bảng tổng hợp hiện “Báo cáo tổng quan” (`_t("Dashboards")` của `spreadsheet_dashboard`), Nhân sự hiện “Nhân viên”. | Như G1. “Nhân viên” cho danh sách người là đúng nghĩa. | Theo G1. |
| G4 | Ô “Project” trên Trang chủ hiện “Dự án”. Nhãn nguồn của `tp_web_home` là tiếng Việt ngay cả khi dùng en_US. | Thiết kế của UI-HOME-001, đang chờ audit. | Xử lý trong audit UI-HOME-001. Không sửa trong batch này. |
| G5 | Nội dung dữ liệu tiếng Anh: việc chào mừng To-do của OdooBot, danh mục chi phí mẫu dạng lorem, dự án dev “Development Project - Assigned”, tin OdooBot. | Là dữ liệu, không phải nhãn giao diện. | Không ghi đè tên record. Nếu cần trình diễn, xử lý bằng seeder dữ liệu giả riêng. |
| G6 | Thông báo lỗi Python và ràng buộc của `tp_contract`/`tp_planning_api`; `tp_api`/`tp_planning_api` chưa có `vi.po`. | API trả các thông báo này cho React, nên đổi ngôn ngữ sẽ làm đổi hợp đồng hiển thị lỗi. | Quyết định cùng phạm vi React/OpenAPI. Không làm trong batch này. |
| G7 | “Link Tracker” giữ bản native “Trình theo dõi Liên kết”; menu Tests (kỹ thuật) chỉ hiện cho admin. | Ngoài 14 mục trình diễn. | Giữ nguyên. |
| G9 | **Đã xử lý trong source (CHG-20261102-010, DEC-025).** `tp_demo_workspace/i18n/vi.po` từng dịch 22 lần xuất hiện (theo XML ID) của nhãn `tp_contract` khác catalog mới. Nay cả 41 lần xuất hiện khớp `tp_contract/i18n/vi.po`. Ví dụ: In Review “Đang rà soát”, Returned “Trả lại”, Effective “Có hiệu lực”. Bộ lọc cứng trong `contract_views.xml` và `TAX_BASIS_LABELS` của demo cũng đổi theo. Runtime demo18109 **chưa** nâng cấp, nên vẫn hiện nhãn cũ. | Người dùng chọn catalog mới ngày 02/11/2026. | Chủ runtime demo nâng cấp `tp_demo_workspace` (`ui_demo.py`) khi audit UI-DEMO-001. VI-002 không chạm demo18109. |
| G10 | React `frontend/src/features/contracts/` còn nhãn cũ: `format.ts` (Hợp đồng gốc, Đã rà soát xong, Đã ghi nhận ký, Gốc, Giữ nguyên, Điều chỉnh, Bổ sung, Phụ lục), `workflow.ts` (Đang chờ rà soát), `RevisionWorkflow.tsx` (Chưa gồm thuế, Đã gồm thuế). E2E `contract-workflow*.spec.ts` và `contracts.spec.ts` khẳng định các chuỗi này. | Prompt chỉ cho đổi bản dịch React trong phạm vi auth. React contracts thuộc CTR-002a, đang chờ audit. | **Người dùng chọn giữ nguyên ngày 02/11/2026** (DEC-025). React và Odoo tạm hiện hai cách viết cho cùng trạng thái. Nếu sau này đồng bộ: sửa nhãn và e2e cùng một batch, chạy typecheck, unit test và Playwright. |
| G8 | React/auth không đổi. Chưa kiểm luồng login, MFA hay hết phiên. Một lần chạy zoom 150% trên test gặp hộp “Phiên làm việc đã hết hạn”, chạy lại đạt. | Ngoài phạm vi, vì AUTH-002/C01 đang chờ audit. | Kiểm cùng AUTH-002. |

## 5. Kích hoạt, áp dụng, quay lại en_US

Đã chạy trên dev theo thứ tự sau. Snapshot `.local/vi001/snapshot-dev-20261102-121509` có 247 checksum, `verify_backup.py` đạt. Từng bước được kiểm exit code và dừng ngay khi lỗi.

```powershell
.\.venv\Scripts\python.exe .local\data002\tools\backup.py .local\vi001\snapshot-dev-<thời điểm>
.\.venv\Scripts\python.exe .local\data002\tools\verify_backup.py .local\vi001\snapshot-dev-<thời điểm>
.\.venv\Scripts\python.exe odoo-bin i18n loadlang -c .local\odoo.conf -d tp_tanphat_dev -l vi_VN
.\.venv\Scripts\python.exe odoo-bin -c .local\odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -i tp_i18n_vi --stop-after-init --no-http
.\.venv\Scripts\python.exe odoo-bin -c .local\odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -u tp_i18n_vi --i18n-overwrite --stop-after-init --no-http
.\.venv\Scripts\python.exe odoo-bin i18n import -c .local\odoo.conf -d tp_tanphat_dev -l vi_VN custom_addons\tp_core\i18n\vi.po custom_addons\tp_organization\i18n\vi.po custom_addons\tp_project\i18n\vi.po custom_addons\tp_contract\i18n\vi.po
.\.venv\Scripts\python.exe .local\vi001\vi_apply.py dev dry-run   # rồi apply, verify
```

Chạy lại các lệnh trên không tạo bản ghi mới. `vi_apply verify` trả `changes: []`.

Quay lại en_US:

- **Một người dùng tự chọn:** menu người dùng → *Tùy chọn của tôi* → *Ngôn ngữ* → English (US) hoặc Tiếng Việt, rồi lưu. Thao tác này chỉ đổi giao diện của chính người đó, không đổi quyền hay dữ liệu. User khác (planner.dev, staff.*) đang để en_US và không bị đổi hàng loạt.
- **Admin demo:** `vi_apply.py dev revert` đặt admin về en_US và xóa bản dịch vi_VN của 7 giai đoạn (đã thử trên DB test).
- **Bỏ overlay:** gỡ `tp_i18n_vi` không xóa bản dịch đã ghi. Để về bản native, chạy `odoo-bin i18n import -w -l vi_VN` với catalog native của các module liên quan, hoặc khôi phục snapshot.
- **Tắt vi_VN hoàn toàn:** khôi phục snapshot ở trên (dump và filestore), hoặc lưu trữ ngôn ngữ trong Cài đặt → Ngôn ngữ sau khi không còn user nào dùng vi_VN.

## 6. Phân biệt trạng thái

- **Đã có:** nhãn giao diện tiếng Việt cho 14 mục trình diễn và admin dùng vi_VN trên dev18069, đủ cho kịch bản trình diễn.
- **Chưa phải:** nghiệm thu nghiệp vụ, nghiệm thu thuật ngữ bởi người dùng, hay Việt hóa toàn hệ thống (còn G1–G8, G10; G9 đã xử lý trong source nhưng demo18109 chưa nâng cấp). Không đóng audit UI-HOME-001/TODO-001, UI-DEMO-001/002, AUTH-002/C01 hay các cổng pilot.
