# Danh mục module Odoo 20 và trạng thái TANPHAT ONE

**Ngày kiểm tra:** 29/10/2026 (Asia/Saigon)
**Phạm vi source:** các manifest trong `addons/`, `custom_addons/` và core `odoo/addons/base`. Đây là inventory của checkout local, không phải cam kết toàn bộ module Enterprise/Odoo Online.

## 1. Kết luận nhanh

- **Module chuẩn:** 643 trong `addons/` + `base` trong `odoo/addons/` = 644. Không bao gồm 15 module test framework trong `odoo/addons/`.
- **Addon TANPHAT ONE có manifest:** 7.
- **Module ứng dụng chuẩn (`application=True`):** 34.
- **Đã cài trên cả dev và test:** 85 module.
- **Chỉ dev:** 2 module (chủ yếu bản địa hóa Việt Nam/QR).
- **Không cài module nào tự động chỉ vì nó nằm trong thư mục `addons/`**; trạng thái cài lấy trực tiếp từ `ir_module_module` của hai database.

## 2. Danh mục ứng dụng Odoo và các chức năng bổ sung

Bảng này gồm các ứng dụng nghiệp vụ và capability hỗ trợ mà lãnh đạo thường cần quyết định; con số 34 ở phần trên chỉ đếm manifest có `application=True`. “Không có trong checkout” nghĩa là bộ mã hiện tại chưa có module tương ứng; không tự khẳng định module đó không tồn tại ở Odoo Enterprise.

| Nhóm | Module kỹ thuật | Chức năng | Dev | Test |
|---|---|---|---|---|
| Invoicing / kế toán nền | `account` | Hóa đơn, bút toán, thanh toán, thuế và nền kế toán; không khẳng định đầy đủ bộ tính năng Accounting Enterprise. | Đã cài | Đã cài |
| Expenses | `hr_expense` | Đề nghị chi phí, duyệt, hoàn ứng/tái xuất hóa đơn chi phí. | Đã cài | Đã cài |
| Sign | `sign` | Gửi và ký điện tử tài liệu. | Không có checkout | Không có checkout |
| Spreadsheet/Dashboards | `spreadsheet` | Bảng tính và dashboard liên kết dữ liệu Odoo. | Đã cài | Đã cài |
| ESG | `esg` | Theo dõi chỉ số môi trường–xã hội–quản trị; không có trong checkout. | Không có checkout | Không có checkout |
| CRM | `crm` | Lead, opportunity, pipeline và hoạt động bán hàng. | Đã cài | Đã cài |
| Sales | `sale_management` | Báo giá, đơn bán hàng, giao hàng/hóa đơn qua các bridge. | Chưa cài (có source) | Chưa cài (có source) |
| Subscriptions | `sale_subscription` | Gói thuê bao và chu kỳ gia hạn; không có trong checkout. | Không có checkout | Không có checkout |
| Point of Sale | `point_of_sale` | Bán hàng tại quầy, ca POS, thanh toán. | Chưa cài (có source) | Chưa cài (có source) |
| Rental | `sale_renting` | Cho thuê tài sản/sản phẩm; không có trong checkout. | Không có checkout | Không có checkout |
| Website | `website` | Website builder; không phải frontend nội bộ React của TANPHAT. | Chưa cài (có source) | Chưa cài (có source) |
| eCommerce | `website_sale` | Bán hàng trực tuyến. | Chưa cài (có source) | Chưa cài (có source) |
| Events | `event` | Sự kiện, đăng ký và vé. | Chưa cài (có source) | Chưa cài (có source) |
| Blog | `website_blog` | Viết và xuất bản bài blog trên website. | Chưa cài (có source) | Chưa cài (có source) |
| eLearning | `website_slides` | Khóa học, bài học và nền tảng đào tạo trực tuyến. | Chưa cài (có source) | Chưa cài (có source) |
| Forum | `website_forum` | Diễn đàn hỏi đáp và trao đổi cộng đồng. | Chưa cài (có source) | Chưa cài (có source) |
| Inventory | `stock` | Kho, nhập–xuất, điều chuyển, tồn kho. | Chưa cài (có source) | Chưa cài (có source) |
| Manufacturing | `mrp` | Lệnh sản xuất, định mức/BOM, công đoạn. | Chưa cài (có source) | Chưa cài (có source) |
| Maintenance | `maintenance` | Thiết bị và yêu cầu bảo trì. | Chưa cài (có source) | Chưa cài (có source) |
| Repairs | `repair` | Phiếu sửa chữa sản phẩm/thiết bị. | Chưa cài (có source) | Chưa cài (có source) |
| Events | `website_event` | Xuất bản sự kiện, đăng ký và bán vé trên website. | Chưa cài (có source) | Chưa cài (có source) |
| Online Jobs | `website_hr_recruitment` | Đăng tin tuyển dụng và nhận hồ sơ online. | Chưa cài (có source) | Chưa cài (có source) |
| PLM | `mrp_plm` | Quản lý vòng đời sản phẩm; không có trong checkout. | Không có checkout | Không có checkout |
| Quality | `quality` | Điểm kiểm tra/chất lượng; không có trong checkout. | Không có checkout | Không có checkout |
| Purchase | `purchase` | Yêu cầu mua, đơn mua, nhà cung cấp; chưa cài. | Chưa cài (có source) | Chưa cài (có source) |
| Employees | `hr` | Hồ sơ nhân viên, phòng ban và tổ chức. | Đã cài | Đã cài |
| Payroll | `hr_payroll` | Hợp đồng, bảng lương; không có trong checkout. | Không có checkout | Không có checkout |
| Recruitment | `hr_recruitment` | Tuyển dụng và pipeline ứng viên. | Chưa cài (có source) | Chưa cài (có source) |
| Time Off | `hr_holidays` | Nghỉ phép và phân bổ ngày nghỉ. | Chưa cài (có source) | Chưa cài (có source) |
| Appraisals | `hr_appraisal` | Đánh giá nhân viên; không có trong checkout. | Không có checkout | Không có checkout |
| Fleet | `fleet` | Xe, hợp đồng, chi phí và bảo dưỡng đội xe. | Chưa cài (có source) | Chưa cài (có source) |
| Social Marketing | `social` | Lập lịch/quản lý mạng xã hội; không có app social trong checkout. social_media chỉ là cấu hình hỗ trợ. | Không có checkout | Không có checkout |
| Email Marketing | `mass_mailing` | Chiến dịch email, mailing list, đo lường. | Chưa cài (có source) | Chưa cài (có source) |
| SMS Marketing | `mass_mailing_sms` | Chiến dịch SMS; cần nhà cung cấp SMS. | Chưa cài (có source) | Chưa cài (có source) |
| Marketing Automation | `marketing_automation` | Luồng tự động hóa marketing; không có trong checkout. | Không có checkout | Không có checkout |
| WhatsApp | `whatsapp` | Kết nối WhatsApp; không có trong checkout. | Không có checkout | Không có checkout |
| Surveys | `survey` | Bảng hỏi và khảo sát online; không phải khảo sát hiện trường TP Survey. | Chưa cài (có source) | Chưa cài (có source) |
| Project | `project` | Dự án, task, stage, cộng tác. | Đã cài | Đã cài |
| Timesheets | `hr_timesheet` | Ghi nhận thời gian trên task/dự án. | Đã cài | Đã cài |
| Planning | `planning` | Lập lịch/phân ca/phân bổ nguồn lực; không có trong checkout. | Không có checkout | Không có checkout |
| Appointments | `appointment` | Đặt lịch; không có trong checkout. | Không có checkout | Không có checkout |
| Live Chat | `im_livechat` | Chat với khách trên website. | Chưa cài (có source) | Chưa cài (có source) |
| Helpdesk | `helpdesk` | Ticket hỗ trợ; không có trong checkout. | Không có checkout | Không có checkout |
| AI | `ai` | Tính năng AI; không có trong checkout. | Không có checkout | Không có checkout |
| Discuss | `mail` | Trao đổi nội bộ, mail gateway, channel. | Đã cài | Đã cài |
| VoIP | `voip` | Điện thoại VoIP; không có trong checkout. | Không có checkout | Không có checkout |
| IoT | `iot` | Thiết bị IoT; không có trong checkout. | Không có checkout | Không có checkout |
| Documents | `documents` | Quản lý hồ sơ/tệp; không có trong checkout. | Không có checkout | Không có checkout |
| Knowledge | `knowledge` | Kho tri thức nội bộ; không có trong checkout. | Không có checkout | Không có checkout |
| Studio | `web_studio` | Tùy biến không code; thường Enterprise, không có trong checkout. | Không có checkout | Không có checkout |
| Accounting nâng cao | `account_accountant` | Bộ tính năng kế toán nâng cao; chưa có addon này trong checkout, không suy đã có từ account. | Không có checkout | Không có checkout |
| Assets | `account_asset` | Quản lý tài sản và lịch khấu hao; không có addon này trong checkout. | Không có checkout | Không có checkout |
| Budgets | `account_budget` | Quản lý ngân sách tài chính; không có addon này trong checkout. | Không có checkout | Không có checkout |
| Barcode nghiệp vụ kho | `stock_barcode` | Thao tác kho bằng mã vạch; khác thư viện barcodes nền. | Không có checkout | Không có checkout |
| Attendances | `hr_attendance` | Chấm vào/ra và theo dõi thời gian hiện diện. | Chưa cài (có source) | Chưa cài (có source) |
| Skills Management | `hr_skills` | Kỹ năng, kiến thức và hồ sơ năng lực nhân viên. | Đã cài | Đã cài |
| Lunch | `lunch` | Đặt và quản lý suất ăn nhân viên. | Chưa cài (có source) | Chưa cài (có source) |
| Referrals | `hr_referral` | Chương trình giới thiệu ứng viên nội bộ. | Không có checkout | Không có checkout |
| Frontdesk | `frontdesk` | Tiếp đón khách và thông báo cho người tiếp khách. | Không có checkout | Không có checkout |
| Calendar | `calendar` | Lịch họp và lịch hẹn nội bộ. | Đã cài | Đã cài |
| Contacts | `contacts` | Danh bạ khách hàng, nhà cung cấp và đối tác. | Đã cài | Đã cài |
| To-Do | `project_todo` | Ghi chú và danh sách công việc cá nhân. | Đã cài | Đã cài |
| Marketing Card | `marketing_card` | Tạo thẻ nội dung động để chia sẻ. | Chưa cài (có source) | Chưa cài (có source) |
| POS Restaurant | `pos_restaurant` | Mở rộng POS cho nhà hàng/bàn/phục vụ. | Chưa cài (có source) | Chưa cài (có source) |
| Approvals | `approvals` | Đề nghị/phê duyệt nội bộ; chưa có addon, không thay BASE theo DEC-013. | Không có checkout | Không có checkout |
| Field Service | `industry_fsm` | Lệnh công việc và điều phối dịch vụ tại hiện trường. | Không có checkout | Không có checkout |
| Data Recycle | `data_recycle` | Tìm hồ sơ cũ để đề xuất lưu trữ/xóa theo rule. | Chưa cài (có source) | Chưa cài (có source) |
| Data Cleaning | `data_cleaning` | Làm sạch và hợp nhất dữ liệu; khác app Data Recycle. | Không có checkout | Không có checkout |

## 3. Addon TANPHAT ONE

| Module | Chức năng hiện tại | Dev | Test |
|---|---|---|---|
| `tp_api` | Transport API: session, response, lỗi và request ID. | Đã cài | Đã cài |
| `tp_contract` | TP Contracts: hợp đồng, revision, hồ sơ, workflow draft/review. | Đã cài | Đã cài |
| `tp_core` | Nền dùng chung, work item/catalog và cấu hình lõi. | Đã cài | Đã cài |
| `tp_organization` | Mở rộng phòng ban và tổ chức. | Đã cài | Đã cài |
| `tp_planning_api` | API workspace kế hoạch: dự án/hợp đồng và các endpoint planning. | Đã cài | Đã cài |
| `tp_project` | TP Projects: project, mã dự án, assignment, scope/grant. | Đã cài | Đã cài |
| `tp_web_login` | Trang login native TANPHAT ONE; có source nhưng chưa đưa vào danh sách cài dev/test. | Chưa cài | Chưa cài |

## 4. Các module hỗ trợ nghiệp vụ quan trọng

Các module này có thể không hiện như một “ứng dụng” độc lập nhưng tạo chức năng cho ứng dụng chính. Trạng thái được lấy từ database.

| Module | Vai trò | Trạng thái dev/test |
|---|---|---|
| `analytic` | Sổ phân tích theo project/chi phí. | Đã cài dev + test |
| `account_payment` | Thanh toán và phương thức thanh toán. | Đã cài dev + test |
| `account_edi_ubl_cii` | EDI hóa đơn theo UBL/CII. | Đã cài dev + test |
| `l10n_vn` | Bản địa hóa kế toán Việt Nam. | Đã cài dev; chưa cài test |
| `account_qr_code_emv` | QR thanh toán EMV. | Đã cài dev; chưa cài test |
| `account_qr_code_sepa` | QR thanh toán SEPA. | Đã cài dev + test |
| `sale` | Đối tượng bán hàng nền. | Có trong source; chưa cài |
| `sale_management` | Báo giá/đơn bán hàng. | Có trong source; chưa cài |
| `sale_project` | Liên kết bán hàng–dự án. | Có trong source; chưa cài |
| `sale_stock` | Liên kết bán hàng–kho. | Có trong source; chưa cài |
| `purchase` | Mua hàng. | Có trong source; chưa cài |
| `purchase_stock` | Mua hàng–nhập kho. | Có trong source; chưa cài |
| `purchase_requisition` | Thỏa thuận/yêu cầu mua. | Có trong source; chưa cài |
| `purchase_requisition_stock` | Yêu cầu mua–tồn kho. | Có trong source; chưa cài |
| `stock` | Kho và logistics. | Có trong source; chưa cài |
| `stock_account` | Hạch toán kho. | Có trong source; chưa cài |
| `stock_landed_costs` | Phân bổ chi phí mua vào giá vốn kho. | Có trong source; chưa cài |
| `stock_delivery` | Giao hàng. | Có trong source; chưa cài |
| `product` | Danh mục sản phẩm. | Đã cài dev + test |
| `uom` | Đơn vị tính. | Đã cài dev + test |
| `maintenance` | Bảo trì thiết bị. | Có trong source; chưa cài |
| `fleet` | Đội xe. | Có trong source; chưa cài |
| `hr_attendance` | Chấm công. | Có trong source; chưa cài |
| `hr_holidays` | Nghỉ phép. | Có trong source; chưa cài |
| `hr_recruitment` | Tuyển dụng. | Có trong source; chưa cài |
| `hr_skills` | Kỹ năng nhân viên. | Đã cài dev + test |
| `hr_calendar` | Lịch làm việc nhân sự. | Đã cài dev + test |
| `hr_expense` | Chi phí nhân viên. | Đã cài dev + test |
| `hr_timesheet` | Chấm công theo task. | Đã cài dev + test |
| `project_hr_expense` | Cầu nối chi phí–dự án. | Đã cài dev + test |
| `project_account` | Cầu nối project–kế toán phân tích. | Đã cài dev + test |
| `project_sms` | SMS liên quan project. | Đã cài dev + test |
| `survey` | Khảo sát online tổng quát, không phải TP Survey hiện trường. | Có trong source; chưa cài |
| `spreadsheet` | Bảng tính Odoo. | Đã cài dev + test |
| `spreadsheet_account` | Dashboard/bảng tính kế toán. | Đã cài dev + test |
| `spreadsheet_dashboard` | Dashboard bảng tính. | Đã cài dev + test |
| `spreadsheet_dashboard_account` | Dashboard kế toán. | Đã cài dev + test |
| `spreadsheet_dashboard_hr_timesheet` | Dashboard timesheet. | Đã cài dev + test |
| `calendar` | Lịch. | Đã cài dev + test |
| `contacts` | Danh bạ đối tác. | Đã cài dev + test |
| `mail` | Trao đổi nội bộ/chatter. | Đã cài dev + test |
| `portal` | Cổng người dùng ngoài. | Đã cài dev + test |
| `auth_totp` | MFA TOTP. | Đã cài dev + test |
| `auth_passkey` | Passkey. | Đã cài dev + test |
| `base_import` | Import dữ liệu cơ bản. | Đã cài dev + test |
| `base_automation` | Tự động hóa server. | Có trong source; chưa cài |
| `base_geolocalize` | Địa chỉ/tọa độ. | Có trong source; chưa cài |
| `cloud_storage` | Lưu tệp cloud; chưa cài. | Có trong source; chưa cài |
| `documents` | DMS; không có trong checkout. | Không có trong checkout |
| `approvals` | Phê duyệt; không có trong checkout. | Không có trong checkout |
| `planning` | Lập lịch nguồn lực; không có trong checkout. | Không có trong checkout |
| `helpdesk` | Ticket hỗ trợ; không có trong checkout. | Không có trong checkout |
| `hr_payroll` | Bảng lương; không có trong checkout. | Không có trong checkout |

## 5. Module chuẩn và custom đã cài thực tế

Danh sách dưới lấy trực tiếp từ `ir_module_module` và gồm cả module tự cài theo dependency. Nó không đồng nghĩa tất cả chức năng đã được cấu hình hoặc có dữ liệu.

### Dev `tp_tanphat_dev`

`account, account_edi_ubl_cii, account_payment, account_qr_code_emv, account_qr_code_sepa, analytic, api_doc, auth_passkey, auth_passkey_portal, auth_signup, auth_totp, auth_totp_mail, auth_totp_portal, base, base_address_extended, base_import, base_import_module, base_install_request, base_report_wkhtmltox, base_setup, bus, calendar, calendar_sms, contacts, crm, crm_iap_enrich, crm_iap_mine, crm_mail_plugin, crm_sms, digest, google_gmail, hr, hr_calendar, hr_expense, hr_skills, hr_timesheet, html_editor, http_routing, iap, iap_crm, iap_mail, l10n_vn, mail, mail_bot, mail_bot_hr, mail_plugin, microsoft_outlook, mysubscription, onboarding, partner_autocomplete, payment, phone_validation, portal, portal_discuss, portal_rating, privacy_lookup, product, project, project_account, project_hr_expense, project_hr_skills, project_mail_plugin, project_sms, project_todo, rating, resource, resource_mail, rpc, sales_team, sms, spreadsheet, spreadsheet_account, spreadsheet_dashboard, spreadsheet_dashboard_account, spreadsheet_dashboard_hr_timesheet, tp_api, tp_contract, tp_core, tp_organization, tp_planning_api, tp_project, uom, utm, web, web_hierarchy, web_tour, web_unsplash`

### Test `tp_tanphat_test`

`account, account_edi_ubl_cii, account_payment, account_qr_code_sepa, analytic, api_doc, auth_passkey, auth_passkey_portal, auth_signup, auth_totp, auth_totp_mail, auth_totp_portal, base, base_address_extended, base_import, base_import_module, base_install_request, base_report_wkhtmltox, base_setup, bus, calendar, calendar_sms, contacts, crm, crm_iap_enrich, crm_iap_mine, crm_mail_plugin, crm_sms, digest, google_gmail, hr, hr_calendar, hr_expense, hr_skills, hr_timesheet, html_editor, http_routing, iap, iap_crm, iap_mail, mail, mail_bot, mail_bot_hr, mail_plugin, microsoft_outlook, mysubscription, onboarding, partner_autocomplete, payment, phone_validation, portal, portal_discuss, portal_rating, privacy_lookup, product, project, project_account, project_hr_expense, project_hr_skills, project_mail_plugin, project_sms, project_todo, rating, resource, resource_mail, rpc, sales_team, sms, spreadsheet, spreadsheet_account, spreadsheet_dashboard, spreadsheet_dashboard_account, spreadsheet_dashboard_hr_timesheet, tp_api, tp_contract, tp_core, tp_organization, tp_planning_api, tp_project, uom, utm, web, web_hierarchy, web_tour, web_unsplash`

## 6. Toàn bộ module có trong checkout

Đây là inventory đầy đủ của 651 manifest thuộc phạm vi trên; không tính 15 module test framework trong `odoo/addons/`. Module có `application=False` thường là phụ trợ/integration; module `l10n_*` là bản địa hóa từng quốc gia; `test_*` là module kiểm thử. Không nên cài hàng loạt.

| Source | Module | Tên hiển thị | Summary/chức năng từ manifest | Category | App? | Dev/Test |
|---|---|---|---|---|---|---|
| custom | `tp_api` | TANPHAT ONE API | Module hỗ trợ cho TANPHAT ONE API |  | Không | Đã cài dev + test |
| custom | `tp_contract` | TP Contracts | Module hỗ trợ cho TP Contracts |  | Không | Đã cài dev + test |
| custom | `tp_core` | TANPHAT ONE Core | Module hỗ trợ cho TANPHAT ONE Core |  | Không | Đã cài dev + test |
| custom | `tp_organization` | TANPHAT ONE Organization | Module hỗ trợ cho TANPHAT ONE Organization |  | Không | Đã cài dev + test |
| custom | `tp_planning_api` | TANPHAT ONE Planning API | Module hỗ trợ cho TANPHAT ONE Planning API |  | Không | Đã cài dev + test |
| custom | `tp_project` | TP Projects | Module hỗ trợ cho TP Projects |  | Không | Đã cài dev + test |
| custom | `tp_web_login` | TANPHAT ONE Login | Module hỗ trợ cho TANPHAT ONE Login |  | Không | Có trong source; chưa cài |
| standard | `account` | Invoicing | Invoices & Payments | Accounting/Accounting | Có | Đã cài dev + test |
| standard | `account_check_printing` | Check Printing Base | Check printing basic features | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_debit_note` | Debit Notes | Debit Notes | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_edi` | Import/Export Invoices From XML/PDF | Electronic Data Interchange | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_edi_proxy_client` | Proxy features for account_edi | This module adds generic features to register an Odoo DB on the proxy responsible for receiving data (via requests from web-services). | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_edi_ubl_cii` | Import/Export electronic invoices with UBL/CII | Electronic invoicing module | Accounting/Accounting | Không | Đã cài dev + test |
| standard | `account_fleet` | Accounting/Fleet bridge | Manage accounting with fleets | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_payment` | Payment - Account | Enable customers to pay invoices on the portal and post payments when transactions are processed. | Accounting/Accounting | Không | Đã cài dev + test |
| standard | `account_payment_custom` | Payment Custom / Account Payment | Bridge between payment_custom and account_payment. | Accounting/Payment Custom | Không | Có trong source; chưa cài |
| standard | `account_payment_interco` | Intercompany Payment - Account | Enable Intercompany payments to reconcile with their invoices on post. | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_peppol` | Peppol | This module is used to send/receive documents with Peppol | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_qr_code_emv` | account_qr_code_emv | Bridge module addings support for EMV Merchant-Presented QR-code generation for Payment System. | Accounting/Payment | Không | Đã cài dev; chưa cài test |
| standard | `account_qr_code_sepa` | Account SEPA QR Code | This module adds support for SEPA Credit Transfer QR-code generation. | Accounting/Payment | Không | Đã cài dev + test |
| standard | `account_tax_python` | Define Taxes as Python Code | Use python code to define taxes | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_test` | Accounting Consistency Tests | Asserts on accounting. | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `account_update_tax_tags` | Account - Allow updating tax grids | Allow updating tax grids on existing entries | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `analytic` | Analytic Accounting | Module for defining analytic accounting object. | Accounting/Accounting | Không | Đã cài dev + test |
| standard | `api_doc` | API Documentation | Odoo Dynamic API Documentation | Hidden | Không | Đã cài dev + test |
| standard | `attachment_indexation` | Attachments List and Document Indexation | Attachments list and document indexation | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_ldap` | Authentication via LDAP | Module hỗ trợ cho Authentication via LDAP | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_oauth` | OAuth2 Authentication | Allow users to login through OAuth2 Provider. | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_passkey` | Passkeys | Log in with a Passkey | Hidden/Tools | Không | Đã cài dev + test |
| standard | `auth_passkey_portal` | Passkeys Portal | Passkeys for portal users | Hidden/Tools | Không | Đã cài dev + test |
| standard | `auth_password_policy` | Password Policy | Implement basic password policy configuration & check | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_password_policy_portal` | Password Policy support for Signup | Module hỗ trợ cho Password Policy support for Signup | Tools | Không | Có trong source; chưa cài |
| standard | `auth_password_policy_signup` | Password Policy support for Signup | Module hỗ trợ cho Password Policy support for Signup | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_signup` | Signup | Allow users to sign up and reset their password | Hidden/Tools | Không | Đã cài dev + test |
| standard | `auth_timeout` | Auth Timeout | Ask for authentication after user inactivity | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `auth_totp` | Two-Factor Authentication (TOTP) | Two-Factor Authentication (TOTP) | Extra Tools | Không | Đã cài dev + test |
| standard | `auth_totp_mail` | 2FA Invite mail | 2FA Invite mail | Extra Tools | Không | Đã cài dev + test |
| standard | `auth_totp_portal` | TOTPortal | Module hỗ trợ cho TOTPortal | Hidden | Không | Đã cài dev + test |
| standard | `barcodes` | Barcode | Scan and Parse Barcodes | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `barcodes_gs1_nomenclature` | Barcode - GS1 Nomenclature | Parse barcodes according to the GS1-128 specifications | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `base` | Base | The kernel of Odoo, needed for all installation. | Hidden | Không | Đã cài dev + test |
| standard | `base_address_extended` | Extended Addresses | Add extra fields on addresses | Sales/Sales | Không | Đã cài dev + test |
| standard | `base_automation` | Automation Rules | This module allows to implement automation rules for any object. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `base_geolocalize` | Partners Geolocation | Partners Geolocation | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `base_import` | Base import | New extensible file import for Odoo | Hidden/Tools | Không | Đã cài dev + test |
| standard | `base_import_module` | Base import module | Import a custom data module | Hidden/Tools | Không | Đã cài dev + test |
| standard | `base_install_request` | Base - Module Install Request | Allow internal users requesting a module installation | Hidden | Không | Đã cài dev + test |
| standard | `base_report_paper_muncher` | Report Engine: Paper Muncher | Paper Muncher Engine | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `base_report_wkhtmltox` | Report Engine: wkhtmltopdf/wkhtmltoimage | wkhtmltopdf rendering engine | Hidden/Tools | Không | Đã cài dev + test |
| standard | `base_setup` | Initial Setup Tools | This module helps to configure the system at the installation of a new database. | Hidden | Không | Đã cài dev + test |
| standard | `base_sparse_field` | Sparse Fields | Implementation of sparse fields. | Hidden | Không | Có trong source; chưa cài |
| standard | `board` | Dashboards | Build your own dashboards | Productivity | Không | Có trong source; chưa cài |
| standard | `bus` | IM Bus | Instant Messaging Bus allow you to send messages to users, in live. | Hidden | Không | Đã cài dev + test |
| standard | `calendar` | Calendar | Schedule employees' meetings | Productivity/Calendar | Có | Đã cài dev + test |
| standard | `calendar_sms` | Calendar - SMS | Send text messages as event reminders | Productivity/Calendar | Không | Đã cài dev + test |
| standard | `certificate` | Certificate | Manage certificate | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `cloud_storage` | Cloud Storage | Store chatter attachments in the cloud | Technical Settings | Không | Có trong source; chưa cài |
| standard | `cloud_storage_azure` | Cloud Storage Azure | Store chatter attachments in the Azure cloud | Technical Settings | Không | Có trong source; chưa cài |
| standard | `cloud_storage_google` | Cloud Storage Google | Store chatter attachments in the Google cloud | Technical Settings | Không | Có trong source; chưa cài |
| standard | `cloud_storage_migration` | Cloud Storage Migration | Migrate local attachments to cloud storage | Technical Settings | Không | Có trong source; chưa cài |
| standard | `contacts` | Contacts | Centralize your address book | Sales/CRM | Có | Đã cài dev + test |
| standard | `crm` | CRM | Track leads and close opportunities | Sales/CRM | Có | Đã cài dev + test |
| standard | `crm_iap_enrich` | Lead Enrichment | Enrich Leads/Opportunities using email address domain | Sales/CRM | Không | Đã cài dev + test |
| standard | `crm_iap_mine` | Lead Generation | Generate Leads/Opportunities based on country, industries, size, etc. | Sales/CRM | Không | Đã cài dev + test |
| standard | `crm_livechat` | CRM Livechat | Create lead from livechat conversation | Sales/CRM | Không | Có trong source; chưa cài |
| standard | `crm_mail_plugin` | CRM Mail Plugin | Turn emails received in your mailbox into leads and log their content as internal notes. | Sales/CRM | Không | Đã cài dev + test |
| standard | `crm_sale_project` | CRM - Project | Project Generation from Opportunities | Sales/CRM | Không | Có trong source; chưa cài |
| standard | `crm_sms` | SMS in CRM | Add SMS capabilities to CRM | Sales/CRM | Không | Đã cài dev + test |
| standard | `data_recycle` | Data Recycle | Find old records and archive/delete them | Productivity/Data Cleaning | Có | Có trong source; chưa cài |
| standard | `delivery` | Delivery Costs | Allows you to add delivery methods in sale orders. | Sales/Delivery | Không | Có trong source; chưa cài |
| standard | `digest` | KPI Digests | Send KPI Digests periodically | Marketing | Không | Đã cài dev + test |
| standard | `event` | Events Organization | Trainings, Conferences, Meetings, Exhibitions, Registrations | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_booth` | Events Booths | Manage event booths | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_booth_sale` | Events Booths Sales | Manage event booths sale | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_crm` | Event CRM | Create leads from event registrations. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_crm_sale` | Event CRM Sale | Add information of sale order linked to the registration for the creation of the lead. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_product` | Events Product | Module hỗ trợ cho Events Product | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_sale` | Events Sales | Creating registration with sales orders. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `event_sms` | SMS on Events | Schedule SMS in event management | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `fleet` | Fleet | Manage your fleet and track car costs | Human Resources/Fleet | Có | Có trong source; chưa cài |
| standard | `fleet_maintenance` | Maintenance - Fleet | Integrates Fleet and Maintenance | Human Resources | Không | Có trong source; chưa cài |
| standard | `gamification` | Gamification | Gamification process | Human Resources | Không | Có trong source; chưa cài |
| standard | `gamification_sale_crm` | CRM Gamification | Example of goal definitions and challenges that can be used related to the usage of the CRM Sale module. | Sales/CRM | Không | Có trong source; chưa cài |
| standard | `google_account` | Google Users | The module adds google user in res user. | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `google_address_autocomplete` | Google Address Autocomplete | Assist with automatic completion & suggestions when filling address | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `google_calendar` | Google Calendar | Module hỗ trợ cho Google Calendar | Productivity | Không | Có trong source; chưa cài |
| standard | `google_gmail` | Google Gmail | Gmail support for incoming / outgoing mail servers | Hidden | Không | Đã cài dev + test |
| standard | `google_recaptcha` | Google reCAPTCHA integration | This module implements reCaptchaV3 so that you can prevent bot spam on your public modules. | Hidden | Không | Có trong source; chưa cài |
| standard | `hr` | Employees | Centralize employee information | Human Resources/Employees | Có | Đã cài dev + test |
| standard | `hr_address_extended` | HR Address Extended | Centralize employee information | Human Resources/Employees | Không | Có trong source; chưa cài |
| standard | `hr_attendance` | Attendances | Track employee attendance | Human Resources/Attendances | Có | Có trong source; chưa cài |
| standard | `hr_calendar` | Display Working Hours in Calendar | Module hỗ trợ cho Display Working Hours in Calendar | Human Resources/Employees | Không | Đã cài dev + test |
| standard | `hr_calendar_google` | HR Calendar with Google Calendar | Module hỗ trợ cho HR Calendar with Google Calendar | Human Resources/Remote Work | Không | Có trong source; chưa cài |
| standard | `hr_expense` | Expenses | Submit, validate and reinvoice employee expenses | Human Resources/Expenses | Có | Đã cài dev + test |
| standard | `hr_fleet` | Fleet History | Get history of driven cars by employees | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_gamification` | HR Gamification | Use the HR resources for the gamification process. | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_holidays` | Time Off | Allocate time off and follow leave requests | Human Resources/Time Off | Có | Có trong source; chưa cài |
| standard | `hr_holidays_attendance` | HR Attendance Holidays | Attendance Holidays | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_livechat` | HR - Livechat | Bridge between HR and Livechat. | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_maintenance` | Maintenance - HR | Equipment, Assets, Internal Hardware, Allocation Tracking | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_presence` | Employee Presence Control | Control Employees Presence | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_recruitment` | Recruitment | Track your recruitment pipeline | Human Resources/Recruitment | Có | Có trong source; chưa cài |
| standard | `hr_recruitment_skills` | Recruitment - Skills Management | Manage skills of your employees | Human Resources/Recruitment | Không | Có trong source; chưa cài |
| standard | `hr_recruitment_sms` | Recruitment - SMS | Mass mailing sms to job applicants | Human Resources/Recruitment | Không | Có trong source; chưa cài |
| standard | `hr_recruitment_survey` | Hr Recruitment Interview Forms | Surveys | Human Resources | Không | Có trong source; chưa cài |
| standard | `hr_skills` | Skills Management | Manage skills, knowledge and resume of your employees | Human Resources/Employees | Có | Đã cài dev + test |
| standard | `hr_skills_event` | Skills Events | Link training events to resume of your employees | Hidden | Không | Có trong source; chưa cài |
| standard | `hr_skills_slides` | Skills e-learning | Add completed courses to resume of your employees | Human Resources/Employees | Không | Có trong source; chưa cài |
| standard | `hr_skills_survey` | Skills Certification | Add certification to resume of your employees | Human Resources/Employees | Không | Có trong source; chưa cài |
| standard | `hr_timesheet` | Task Logs | Track employee time on tasks | Services/Timesheets | Không | Đã cài dev + test |
| standard | `hr_timesheet_attendance` | Timesheets/attendances reporting | Module linking the attendance module to the timesheet app. | Human Resources/Attendances | Không | Có trong source; chưa cài |
| standard | `hr_work_entry` | Work Entries | Manage work entries | Human Resources/Employees | Không | Có trong source; chưa cài |
| standard | `html_builder` | HTML Builder | Generic html builder |  | Không | Có trong source; chưa cài |
| standard | `html_editor` | HTML Editor | A Html Editor component and plugin system. | Hidden | Không | Đã cài dev + test |
| standard | `http_routing` | Web Routing | Web Routing | Hidden | Không | Đã cài dev + test |
| standard | `iap` | In-App Purchase | Basic models and helpers to support In-App Purchase. | Hidden/Tools | Không | Đã cài dev + test |
| standard | `iap_crm` | IAP / CRM | Bridge between IAP and CRM | Hidden/Tools | Không | Đã cài dev + test |
| standard | `iap_mail` | IAP / Mail | Bridge between IAP and mail | Hidden/Tools | Không | Đã cài dev + test |
| standard | `im_livechat` | Live Chat | Chat with your website visitors | Website/Live Chat | Có | Có trong source; chưa cài |
| standard | `iot_drivers` | Hardware Proxy | Connect the Web Client to Hardware Peripherals | Hidden | Không | Có trong source; chưa cài |
| standard | `iot_webserial` | Web Serial IoT devices | Interface with serial devices directly via the browser using Web Serial. | Administration/IoT | Không | Có trong source; chưa cài |
| standard | `l10n_account_edi_ubl_cii_tests` | Testing the Import/Export invoices with UBL/CII | This module tests the module 'account_edi_ubl_cii', it is separated since dependencies to some | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `l10n_account_withholding_tax` | Withholding Tax | Allows users to manage withholding taxes on invoices, bills, and payments. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_account_withholding_tax_pos` | Withholding Tax on Payment - PoS | Add support for the withholding tax module in the PoS. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_ae` | United Arab Emirates - Accounting | United Arab Emirates Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ae_pos` | United Arab Emirates - Point of Sale | United Arab Emirates POS Localization | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_anz_ubl_pint` | Australia & New Zealand - UBL PINT | The UBL PINT e-invoicing format for Australia & New Zealand is based on the Peppol International (PINT) model for Billing. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_ar` | Argentina - Accounting | Functional | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ar_pos` | Argentinean - Point of Sale with AR Doc | This module brings the technical requirement for the Argentinean regulation. | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ar_stock` | Argentinean - Stock | Argentinean - Stock | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_ar_website_sale` | Argentinean eCommerce | Bridge Website Sale for Argentina | Accounting/Localizations/Website | Không | Có trong source; chưa cài |
| standard | `l10n_ar_withholding` | Argentina - Payment Withholdings | Allows to register withholdings during the payment of an invoice. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_at` | Austria - Accounting | Austrian Standardized Charts & Tax | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_au` | Australia - Accounting | Australian Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bd` | Bangladesh - Accounting | This is the base module to manage the accounting chart for Bangladesh in Odoo | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_be` | Belgium - Accounting | This is the base module to manage the accounting chart for Belgium in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_be_pos` | BE POS Localization | Link module between point_of_sale and l10n_be | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_be_pos_restaurant` | Belgian POS Restaurant Localization | Module hỗ trợ cho Belgian POS Restaurant Localization | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_be_pos_sale` | l10n_be_pos_sale | Link module between pos_sale and l10n_be | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_bf` | Burkina Faso - Accounting | This module implements the tax for Burkina Faso. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bg` | Bulgaria - Accounting | Chart accounting and taxes for Bulgaria | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bg_ledger` | Bulgaria - Report ledger | Report ledger for Bulgaria | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bh` | Bahrain - Accounting | This is the base module to manage the accounting chart for Bahrain in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bj` | Benin - Accounting | This module implements the tax for Benin. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_bo` | Bolivia - Accounting | Bolivian accounting chart and tax localization. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_br` | Brazilian - Accounting | Base module for the Brazilian localization | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_br_sales` | Brazil - Sale | Sale modifications for Brazil | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `l10n_br_website_sale` | Brazil - Website Sale | Bridge Website Sale for Brazil | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `l10n_ca` | Canada - Accounting | This is the module to manage the Canadian accounting chart in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cd` | Democratic Republic of the Congo - Accounting | This module implements the tax for the Democratic Republic of the Congo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cf` | Central African Republic - Accounting | This module implements the tax for Central African Republic. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cg` | Congo - Accounting | This module implements the tax for Congo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ch` | Switzerland - Accounting | Swiss localization | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ch_pos` | Swiss - Point of Sale | Swiss POS Localization | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ci` | Ivory Coast - Accounting | This module implements the taxes for Ivory Coast. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cl` | Chile - Accounting | Chilean accounting chart and tax localization. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cm` | Cameroon - Accounting | This module implements the tax for Cameroon. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cn` | China - Accounting | Includes the following data for the Chinese localization | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_co` | Colombia - Accounting | Colombian Accounting and Tax Preconfiguration | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_co_pos` | Colombian - Point of Sale | Colombian - Point of Sale | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_cr` | Costa Rica - Accounting | Chart of accounts for Costa Rica. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cy` | Cyprus - Accounting | Basic package for Cyprus that contains the chart of accounts, taxes, tax reports,... | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_cz` | Czech - Accounting | Czech accounting chart and localization.  With Chart of Accounts with taxes and basic fiscal positions. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_de` | Germany - Accounting | Dieses  Modul beinhaltet einen deutschen Kontenrahmen basierend auf dem SKR03 oder SKR04. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_din5008` | DIN 5008 | This is the base module that defines the DIN 5008 standard in Odoo. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_din5008_expense` | DIN 5008 - Expenses | Module hỗ trợ cho DIN 5008 - Expenses | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_din5008_purchase` | DIN 5008 - Purchase | Module hỗ trợ cho DIN 5008 - Purchase | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_din5008_repair` | DIN 5008 - Repair | Module hỗ trợ cho DIN 5008 - Repair | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_din5008_sale` | DIN 5008 - Sale | Module hỗ trợ cho DIN 5008 - Sale | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_din5008_stock` | DIN 5008 - Stock | Module hỗ trợ cho DIN 5008 - Stock | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_dk` | Denmark - Accounting | Localization Module for Denmark | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_dk_fik` | Denmark - FIK Number | Use FIK Number as Payment reference | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_do` | Dominican Republic - Accounting | Localization Module for Dominican Republic | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_dz` | Algeria - Accounting | This is the module to manage the accounting chart for Algeria in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ec` | Ecuadorian Accounting | Functional | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ec_sale` | Ecuador - Sale | Ecuador Sale | Accounting/Localizations/Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ee` | Estonia - Accounting | This is the base module to manage the accounting chart for Estonia in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_eg` | Egypt - Accounting | Egypt Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_eg_edi_eta` | Egypt E-Invoicing | Egypt Tax Authority Invoice Integration | account | Không | Có trong source; chưa cài |
| standard | `l10n_eg_edi_pos` | Egypt E-Receipts (POS) | Submit POS receipts to the Egyptian Tax Authority | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_es` | Spain - Accounting (PGCE 2008) | Spanish charts of accounts (PGCE 2008). | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_facturae` | Spain - Facturae EDI | This module create the Facturae file required to send the invoices information to the General State Administrations. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_sii` | Spain - SII EDI Suministro de Libros | This module sends the taxes information (mostly VAT) of the | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_tbai` | Spain - TicketBAI | This module sends invoices and vendor bills to the "Diputaciones | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_tbai_pos` | Spain - Point of Sale + TicketBAI | Module hỗ trợ cho Spain - Point of Sale + TicketBAI | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_verifactu` | Spain - Veri*Factu | Module for sending Spanish Veri*Factu XML to the AEAT | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_es_edi_verifactu_pos` | Spain - Veri*Factu for Point of Sale | Add Veri*Factu support to Point of Sale | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_es_pos` | [Deprecated] Spain - Point of Sale | Spanish localization for Point of Sale | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_es_website_sale` | Spain - ECommerce | Module hỗ trợ cho Spain - ECommerce | Accounting/Localizations/Website | Không | Có trong source; chưa cài |
| standard | `l10n_et` | Ethiopia - Accounting | Base Module for Ethiopian Localization | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_eu_account_vies` | VAT VIES Validation | VAT validation for Partner's VAT numbers. | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `l10n_eu_oss` | EU One Stop Shop (OSS) | EU One Stop Shop (OSS) VAT | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_fi` | Finland - Accounting | This is the Odoo module to manage the accounting in Finland. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_fi_sale` | Finland - Sale | Finland Sale | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `l10n_fr` | France - Localizations | Module hỗ trợ cho France - Localizations | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_fr_account` | France - Accounting | This is the module to manage the accounting chart for France in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_fr_facturx_chorus_pro` | France - BIS3 integration for Chorus Pro | Add support to fill three fields used when using Chorus Pro, especially when invoicing public services. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_fr_hr_holidays` | France - Time Off | Management of leaves for part-time workers in France | Human Resources/Time Off | Không | Có trong source; chưa cài |
| standard | `l10n_fr_payment` | France - Worldline Payment Branding | Applies CAWL/Worldline branding rules for French companies. |  | Không | Có trong source; chưa cài |
| standard | `l10n_fr_pdp` | France - E-Invoicing (Approved Platform) | - Support for the mandatory electronic invoicing in France | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_fr_pdp_pos` | France - E-reporting for POS | Flux 10 e-reporting for POS | Accounting/Localizations/Reporting | Không | Có trong source; chưa cài |
| standard | `l10n_fr_pos_cert` | France - VAT Anti-Fraud Certification for Point of Sale (CGI 286 I-3 bis) | This add-on brings the technical requirements of the French regulation CGI art. 286, I. 3° bis that stipulates certain criteria concerning the inalterability, security, storage and archiving of data related to sales to private individuals (B2C). | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ga` | Gabon - Accounting | This module implements the tax for Gabon. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gcc_invoice` | Gulf Cooperation Council - Invoice | Adds Arabic as a secondary language on your invoice, credit note, debit note, vendor bill, and refund bill | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_gcc_invoice_stock_account` | Gulf Cooperation Council WMS Accounting | Adds Arabic as a secondary language for the lots and serial numbers | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_gcc_pos` | Gulf Cooperation Council - Point of Sale | Adds Arabic as a secondary language on your receipt | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ge` | Georgia - Accounting | Georgian accounting localization package | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gf` | Guyana - Accounting | This is the base module to manage the accounting chart for Guiana. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gn` | Guinea - Accounting | This module implements the tax for Guinea. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gp` | Guadeloupe - Accounting | This is the base module to manage the accounting chart for Guadeloupe. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gq` | Guinea Equatorial - Accounting | This module implements the tax for Guinea Equatorial. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gr` | Greece - Accounting | This is the base module to manage the accounting chart for Greece. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gr_edi` | Greece - myDATA | Connect to myDATA API implementation for Greece | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_gr_edi_delivery_note` | Greece - myDATA Delivery Note | Transmit Greece myDATA EDI for Delivery Notes | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_gr_edi_e_invoo` | Greece - myDATA E-invoicing through e-invoo | Module hỗ trợ cho Greece - myDATA E-invoicing through e-invoo | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_gr_edi_e_invoo_bridge` | Greece - myDATA E-invoicing through e-invoo (direct API) | Module hỗ trợ cho Greece - myDATA E-invoicing through e-invoo (direct API) | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_gt` | Guatemala - Accounting | This is the base module to manage the accounting chart for Guatemala. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_gw` | Guinea-Bissau - Accounting | This module implements the tax for Guinea-Bissau. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hk` | Hong Kong - Accounting | This is the base module to manage chart of accounting and localization for Hong Kong | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hn` | Honduras - Accounting | This is the base module to manage the accounting chart for Honduras. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hr` | Croatia - Accounting (Euro) | Croatian Chart of Accounts updated (RRIF ver.2021) | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hr_edi` | Croatia - e-invoicing | e-invoicing for Croatia | Accounting/Localizations/Reporting | Không | Có trong source; chưa cài |
| standard | `l10n_hr_kuna` | Croatia - Accounting (Kuna) | Croatian localisation. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hu` | Hungary - Accounting | Accounting chart and localization for Hungary | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_hu_edi` | Hungary - E-invoicing | * Electronically report invoices to the NAV (Hungarian Tax Agency) when issuing physical (paper) invoices. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_id` | Indonesian - Accounting | This is the latest Indonesian Odoo localisation necessary to run Odoo accounting for SMEs with: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_id_efaktur_coretax` | Indonesia E-faktur (Coretax) | E-invoicing feature provided by DJP (Indonesian Tax Office). As of January 1st 2025, | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_id_pos` | Indonesia - Point of Sale | Indonesian Point of Sale | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_id_pos_self_order_qris` | Indonesia - POS Self Order QRIS | Accept QRIS QR code payments in a kiosk. | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ie` | Ireland - Accounting | This is the base module to manage the accounting chart for Republic of Ireland in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_il` | Israel - Accounting | This is the latest basic Israelian localisation necessary to run Odoo in Israel: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_in` | Indian - Accounting | Indian Accounting: Chart of Account. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_in_boe` | Indian - Bill Of Entry | - Adds Bill of Entry (BOE) support for the Indian localization. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_in_edi` | Indian - E-invoicing | Indian - E-invoicing | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_in_ewaybill` | Indian - E-waybill | Indian - E-waybill | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_in_ewaybill_irn` | Indian - E-waybill thru IRN | Indian - E-waybill thru IRN | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_in_ewaybill_stock` | Indian - E-waybill Stock | Indian E-waybill for Stock | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_in_hr_holidays` | India - Time Off | Leave Management of Indian Localization | Human Resources/Time Off | Không | Có trong source; chưa cài |
| standard | `l10n_in_pos` | Indian - Point of Sale | GST Point of Sale | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_in_purchase_stock` | India Purchase and Warehouse Management | Get warehouse address if the bill is created from Purchase Order | Accounting/Localizations/Purchase | Không | Có trong source; chưa cài |
| standard | `l10n_in_sale` | Indian - Sale Report(GST) | GST Sale Report | Accounting/Localizations/Sale | Không | Có trong source; chưa cài |
| standard | `l10n_in_sale_stock` | India Sales and Warehouse Management | Get warehouse address if the invoice is created from Sale Order | Accounting/Localizations/Sale | Không | Có trong source; chưa cài |
| standard | `l10n_in_stock` | Indian - Stock Report(GST) | GST Stock Report | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_iq` | Iraq - Accounting | This is the base module to manage the accounting chart for Iraq in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_it` | Italy - Accounting | Piano dei conti italiano di un'impresa generica. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_it_edi` | Italy - E-invoicing | E-invoice implementation | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_it_edi_doi` | Italy - Declaration of Intent | Add support for the Declaration of Intent (Dichiarazione di Intento) to the Italian localization. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_it_edi_sale` | Italy - Sale E-invoicing | Sale modifications for Italy E-invoicing | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_it_stock_ddt` | Italy - Stock DDT | Documento di Trasporto (DDT) | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_jo` | Jordan - Accounting | This is the base module to manage the accounting chart for Jordan in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_jo_edi` | Jordan E-Invoicing | Electronic Invoicing for Jordan UBL 2.1 | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_jo_edi_pos` | Jordan Accounting EDI for POS | Jordan Accounting EDI for POS | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_jp` | Japan - Accounting | Overview: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_jp_ubl_pint` | Japan - UBL PINT | The UBL PINT e-invoicing format for Japan is based on the Peppol International (PINT) model for Billing. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_ke` | Kenya - Accounting | This provides a base chart of accounts and taxes template for use in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ke_edi_tremol` | Kenya Tremol Device EDI Integration | Kenya Tremol Device EDI Integration | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_kh` | Cambodia - Accounting | Chart Of Account and Taxes for Cambodia. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_km` | Comoros - Accounting | This module implements the tax for Comoros. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_kr` | Republic of Korea - Accounting | Accounting Module for the Republic of Korea | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_kr_sale` | Republic of Korea - Sales | Bridge module between the Korean localization and Sales, exposing the proof of issuance | Accounting/Localizations/Sale | Không | Có trong source; chưa cài |
| standard | `l10n_kw` | Kuwait - Accounting | This is the base module to manage the accounting chart for Kuwait in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_kz` | Kazakhstan - Accounting | This provides a base chart of accounts and taxes template for use in Odoo for Kazakhstan. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_latam_check` | Third Party and Deferred/Electronic Checks Management | Checks Management | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_latam_invoice_document` | LATAM Document | LATAM Document Types | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_lb_account` | Lebanon - Accounting | This is the base module to manage the accounting chart for Lebanon in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_lk` | Sri Lanka - Accounting | Provides accounting localizations for Sri Lanka. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_lt` | Lithuania - Accounting | Chart of Accounts (COA) Template for Lithuania's Accounting. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_lu` | Luxembourg - Accounting | This is the base module to manage the accounting chart for Luxembourg. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_lv` | Latvia - Accounting | Chart of Accounts (COA) Template for Latvia's Accounting. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ma` | Morocco - Accounting | This is the base module to manage the accounting chart for Morocco. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mc` | Monaco - Accounting | This is the base module to manage the accounting chart for Monaco. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mk` | North Macedonia - Accounting | Chart Of Account and Taxes for North Macedonia. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ml` | Mali - Accounting | This module implements the tax for Mali. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mm` | Myanmar - Accounting | Chart Of Account and Taxes for Myanmar. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mn` | Mongolia - Accounting | This is the module to manage the accounting chart for Mongolia. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mq` | Martinique - Accounting | This is the base module to manage the accounting chart for Martinique. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mr` | Mauritania - Accounting | Mauritania basic package that contains the chart of accounts, the taxes, tax reports, etc. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mt` | Malta - Accounting | Malta basic package that contains the chart of accounts, the taxes, tax reports, etc. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mt_pos` | Malta - Point of Sale | Malta Compliance Letter for EXO Number | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_mu_account` | Mauritius - Accounting | This is the base module to manage the accounting chart for the Republic of Mauritius in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_mx` | Mexico - Accounting | Minimal accounting configuration for Mexico. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_my` | Malaysia - Accounting | This is the base module to manage the accounting chart for Malaysia in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_my_edi` | Malaysia - E-invoicing | E-invoicing using MyInvois | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_my_edi_pos` | Malaysia - E-invoicing (POS) | Consolidated E-invoicing using MyInvois | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_my_ubl_pint` | Malaysia - UBL PINT | The UBL PINT e-invoicing format for Malaysia is based on the Peppol International (PINT) model for Billing. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_mz` | Mozambique - Accounting | Mozambican Accounting localization | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ne` | Niger - Accounting | This module implements the tax for Niger. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ng` | Nigeria - Accounting | Nigerian localization. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_nl` | Netherlands - Accounting | Module hỗ trợ cho Netherlands - Accounting | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_no` | Norway - Accounting | This is the module to manage the accounting chart for Norway in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_nz` | New Zealand - Accounting | New Zealand Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_om` | Oman - Accounting | Oman Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_pa` | Panama - Accounting | Panamenian accounting chart and tax localization. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_pe` | Peru - Accounting | Module hỗ trợ cho Peru - Accounting | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_pe_pos` | Peruvian - Point of Sale with Pe Doc | This module brings the technical requirement for the Peruvian regulation. | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_ph` | Philippines - Accounting | This is the module to manage the accounting chart for The Philippines. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ph_invoice` | Philippines - Discount Privileges on Invoice | Apply Philippine SC/PWD discount privileges on customer invoices and credit notes. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_ph_sale` | Philippines - Discount Privileges on Sale Orders | Apply Philippine SC/PWD discount privileges on quotations and sale orders. | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_pk` | Pakistan - Accounting | Pakistan Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_pk_edi` | Pakistan - E-invoicing | Electronic Invoicing for Pakistan FBR(v1.12) | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_pk_edi_pos` | Pakistan - Point of Sale | This module brings the technical requirement for the Pakistan regulation. | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_pl` | Poland - Accounting | This is the module to manage the accounting chart and taxes for Poland in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_pl_edi` | Polish E-Invoicing FA(3) | Support for FA(3) electronic invoices in Poland via KSeF | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_pl_edi_jst` | Polish E-Invoicing FA(3) LGU support | Support for Local Government Unit (LGU) in the FA(3) format | Accounting/Localizations | Không | Có trong source; chưa cài |
| standard | `l10n_pt` | Portugal - Accounting | Portugal - Accounting | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_qa` | Qatar - Accounting | This is the base module to manage the accounting chart for Qatar in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_re` | Reunion - Accounting | This is the base module to manage the accounting chart for Réunion. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ro` | Romania - Accounting | This is the module to manage the Accounting Chart, VAT structure, Fiscal Position and Tax Mapping. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ro_edi` | Romania - E-invoicing | E-Invoice implementation for Romania | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_ro_edi_stock` | Romania - E-Transport | E-Transport implementation for Romania | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_rs` | Serbia - Accounting | This is the base module of the Serbian localization. It manages chart of accounts and taxes. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_rs_edi` | Serbia - eFaktura E-invoicing | E-Invoice implementation for Serbia | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_rw` | Rwanda - Accounting | Rwandan localisation containing: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sa` | Saudi Arabia - Accounting | Saudi Arabia Accounting Module | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sa_edi` | Saudi Arabia - E-invoicing | E-Invoicing, Universal Business Language | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_sa_edi_pos` | Saudi Arabia - E-invoicing (Simplified) | ZATCA E-Invoicing, support for PoS | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_sa_pos` | Saudi Arabia - Point of Sale | Saudi Arabia POS Localization | Accounting/Localizations/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_se` | Sweden - Accounting | Swedish Accounting | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sg` | Singapore - Accounting | Singapore accounting chart and localization. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sg_ubl_pint` | Singapore - UBL PINT | The UBL PINT e-invoicing format for Singapore is based on the Peppol International (PINT) model for Billing. | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_si` | Slovenian - Accounting | Chart of accounts and taxes for Slovenia. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sk` | Slovak - Accounting | Slovakia accounting chart and localization: Chart of Accounts 2020, basic VAT rates + | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_sn` | Sénégal - Accounting | This module implements the taxes for Sénégal. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_syscohada` | OHADA - Accounting | This module implements the accounting chart for OHADA area. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_td` | Tchad - Accounting | This module implements the tax for Tchad. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_test_pos_qr_payment` | POS QR Tests | This module contains tests related to point of sale QR code payment. | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `l10n_tg` | Togo - Accounting | This module implements the tax for Togo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_th` | Thailand - Accounting | Chart of Accounts for Thailand. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_tn` | Tunisia - Accounting | This is the module to manage the accounting chart for Tunisia in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_tr` | Türkiye - Accounting | This is the base module to manage the accounting chart for Türkiye in Odoo | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_tw` | Taiwan - Accounting | This is the base module to manage the accounting chart for Taiwan in Odoo. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_tw_edi_ecpay` | Taiwan - E-invoicing | E-invoicing using ECpay | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_tw_edi_ecpay_pos` | Taiwan - E-invoicing Pos | ECpay E-invoice bridge module for POS | Point of sale/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_tw_edi_ecpay_sale` | Taiwan - E-invoicing Sales | ECPay E-invoice bridge module for Sales | Website Sale/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_tw_edi_ecpay_website_sale` | Taiwan - E-invoicing Ecommerce | ECpay E-invoice bridge module for Ecommerce | Website Sale/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_tz_account` | Tanzania - Accounting | Tanzanian localisation containing: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ua` | Ukraine - Accounting | Ukraine - Chart of accounts. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ug` | Uganda - Accounting | This is the basic Ugandian localisation necessary to run Odoo in UG: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_uk` | United Kingdom - Accounting | This is the latest UK Odoo localisation necessary to run Odoo accounting for UK SME's with: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_us` | United States - Localizations | Module hỗ trợ cho United States - Localizations | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_us_account` | United States - Accounting | Module hỗ trợ cho United States - Accounting | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_uy` | Uruguay - Accounting | General Chart of Accounts. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_uz` | Uzbekistan - Accounting | Uzbekistan Accounting: Chart of Account. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_ve` | Venezuela - Accounting | Chart of Account for Venezuela. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_vn` | Vietnam - Accounting | This is the module to manage the accounting chart, bank information for Vietnam in Odoo. | Accounting/Localizations/Account Charts | Không | Đã cài dev; chưa cài test |
| standard | `l10n_vn_edi_viettel` | Vietnam - E-invoicing | E-invoicing using SInvoice by Viettel | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_vn_edi_viettel_pos` | Vietnam - POS E-invoicing | POS E-invoicing using SInvoice by Viettel | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_vn_edi_viettel_stock` | Vietnam - Delivery E-invoicing | Delivery E-invoicing using SInvoice by Viettel | Accounting/Localizations/EDI | Không | Có trong source; chưa cài |
| standard | `l10n_yt` | Mayotte - Accounting | This is the base module to manage the accounting chart for Mayotte. | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_za` | South Africa - Accounting | This is the latest basic South African localisation necessary to run Odoo in ZA: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `l10n_zm_account` | Zambia - Accounting | This is the basic Zambian localization necessary to run Odoo in ZM: | Accounting/Localizations/Account Charts | Không | Có trong source; chưa cài |
| standard | `link_tracker` | Link Tracker | Shorten URLs and use them to track clicks and UTMs | Marketing | Không | Có trong source; chưa cài |
| standard | `loyalty` | Coupons & Loyalty | Use discounts, gift cards, eWallets and loyalty programs in your sales channels | Sales | Không | Có trong source; chưa cài |
| standard | `lunch` | Lunch | Handle lunch orders of your employees | Human Resources/Lunch | Có | Có trong source; chưa cài |
| standard | `mail` | Discuss | Chat, mail gateway and private channels | Productivity/Discuss | Có | Đã cài dev + test |
| standard | `mail_bot` | OdooBot | Add OdooBot in discussions | Productivity/Discuss | Không | Đã cài dev + test |
| standard | `mail_bot_hr` | OdooBot - HR | Bridge module between hr and mailbot. | Productivity/Discuss | Không | Đã cài dev + test |
| standard | `mail_group` | Mail Group | Manage your mailing lists |  | Không | Có trong source; chưa cài |
| standard | `mail_plugin` | Mail Plugin | Allows integration with mail plugins. | Sales/CRM | Không | Đã cài dev + test |
| standard | `mail_tracking` | Discuss Tracking | Technical tracking of discussion and message-related data | Productivity/Discuss | Không | Có trong source; chưa cài |
| standard | `mail_tracking_mass_mailing` | Mass Mailing Tracking | Track source of messages by mass mailing | Productivity/Discuss | Không | Có trong source; chưa cài |
| standard | `mail_tracking_sms` | SMS Message Tracking | Track source of messages by sms | Productivity/Discuss | Không | Có trong source; chưa cài |
| standard | `maintenance` | Maintenance | Track equipment and manage maintenance requests | Supply Chain/Maintenance | Có | Có trong source; chưa cài |
| standard | `marketing_card` | Marketing Card | Generate dynamic shareable cards | Marketing/Marketing Card | Có | Có trong source; chưa cài |
| standard | `marketing_card_event` | Marketing Card For Events | Generate dynamic shareable cards for entities linked to events. | Marketing/Marketing Card | Không | Có trong source; chưa cài |
| standard | `mass_mailing` | Email Marketing | Design, send and track emails | Marketing/Email Marketing | Có | Có trong source; chưa cài |
| standard | `mass_mailing_crm` | Mass mailing on lead / opportunities | Add lead / opportunities UTM info on mass mailing | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_crm_sms` | Mass mailing sms on lead / opportunities | Add lead / opportunities info on mass mailing sms | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_event` | Mass mailing on attendees | Mass mail event attendees | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_event_sms` | Event Attendees SMS Marketing | SMS Marketing on event attendees | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_event_track` | Mass mailing on track speakers | Mass mail event track speakers | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_event_track_sms` | Track Speakers SMS Marketing | SMS Marketing on event track speakers | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_sale` | Mass mailing on sale orders | Add sale order UTM info on mass mailing | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_sale_sms` | Mass mailing sms on sale orders | Add sale order info on mass mailing sms | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_slides` | Mass mailing on course members | Mass mail course members | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `mass_mailing_sms` | SMS Marketing | Design, send and track SMS | Marketing/Email Marketing | Có | Có trong source; chưa cài |
| standard | `mass_mailing_themes` | Mass Mailing Themes | Design gorgeous mails | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `microsoft_account` | Microsoft Users | The module adds Microsoft user in res user. | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `microsoft_calendar` | Outlook Calendar | Module hỗ trợ cho Outlook Calendar | Productivity | Không | Có trong source; chưa cài |
| standard | `microsoft_outlook` | Microsoft Outlook | Outlook support for incoming / outgoing mail servers | Hidden | Không | Đã cài dev + test |
| standard | `mrp` | Manufacturing | Manufacturing Orders & BOMs | Supply Chain/Manufacturing | Có | Có trong source; chưa cài |
| standard | `mrp_account` | Accounting - MRP | Analytic accounting in Manufacturing | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_delivery` | Delivery and MRP Management | Carrier with kits | Shipping Connectors | Không | Có trong source; chưa cài |
| standard | `mrp_landed_costs` | Landed Costs On MO | Landed Costs on Manufacturing Order | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_product_expiry` | Manufacturing Expiry | Manufacturing Expiry | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_repair` | Mrp Repairs | Module hỗ trợ cho Mrp Repairs | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `mrp_subcontracting` | MRP Subcontracting | Subcontract Productions | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_subcontracting_account` | Subcontracting Management with Stock Valuation | This bridge module allows to manage subcontracting with valuation. | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_subcontracting_dropshipping` | Dropship and Subcontracting Management | This bridge module allows to manage subcontracting with the dropshipping module. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `mrp_subcontracting_landed_costs` | Landed Costs With Subcontracting order | Advanced views to manage landed cost for subcontracting orders | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `mrp_subcontracting_purchase` | Purchase and Subcontracting Management | This bridge module adds some smart buttons between Purchase and Subcontracting | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `mysubscription` | My Subscription | Backend Subscription App | Sales | Không | Đã cài dev + test |
| standard | `onboarding` | Onboarding Toolbox | This module allows to manage onboardings and their progress | Hidden | Không | Đã cài dev + test |
| standard | `partner_autocomplete` | Partner Autocomplete | Auto-complete partner companies' data | Hidden/Tools | Không | Đã cài dev + test |
| standard | `partnership` | Partnership / Membership | This module allows you to manage all operations for managing memberships and partnerships. | Sales/CRM | Không | Có trong source; chưa cài |
| standard | `payment` | Payment Engine | The payment engine used by payment provider modules. | Hidden | Không | Đã cài dev + test |
| standard | `payment_adyen` | Payment Provider: Adyen | A Dutch payment provider covering Europe and the US. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_aps` | Payment Provider: Amazon Payment Services | An Amazon payment provider covering the MENA region. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_asiapay` | Payment Provider: AsiaPay | An payment provider based in Hong Kong covering most Asian countries. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_authorize` | Payment Provider: Authorize.Net | An payment provider covering the US, Australia, and Canada. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_buckaroo` | Payment Provider: Buckaroo | A Dutch payment provider covering several countries in Europe. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_custom` | Payment Provider: Custom Payment Modes | A payment provider for custom flows like wire transfers. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_demo` | Payment Provider: Demo | A payment provider for running fake payment flows for demo purposes. | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `payment_dpo` | Payment Provider: DPO | A Kenyan payment provider covering several African countries. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_ecpay` | Payment Provider: ECPay | A payment provider covering the Taiwanese market. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_flutterwave` | Payment Provider: Flutterwave | A Nigerian payment provider covering several African countries. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_iyzico` | Payment Provider: Iyzico | A payment provider covering Turkey. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_mercado_pago` | Payment Provider: Mercado Pago | A payment provider covering several countries in Latin America. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_mollie` | Payment Provider: Mollie | A Dutch payment provider covering several European countries. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_nuvei` | Payment Provider: Nuvei | A payment provider covering Latin America. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_paymob` | Payment Provider: Paymob | An Egyptian payment provider for the Middle East. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_paypal` | Payment Provider: Paypal | An American payment provider for online payments all over the world. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_payu` | Payment Provider: PayU | A payment provider covering India. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_razorpay` | Payment Provider: Razorpay | A payment provider covering India. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_redsys` | Payment Provider: Redsys | A payment provider covering the Spanish market. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_stripe` | Payment Provider: Stripe | An Irish-American payment provider covering the US and many others. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_toss_payments` | Payment Provider: Toss Payments | A payment provider covering the South Korea market | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_worldline` | Payment Provider: Worldline | A French payment provider covering several European countries. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `payment_xendit` | Payment Provider: Xendit | A payment provider for Indonesian and the Philippines. | Accounting/Payment Providers | Không | Có trong source; chưa cài |
| standard | `phone_validation` | Phone Numbers Validation | Validate and format phone numbers | Hidden | Không | Đã cài dev + test |
| standard | `point_of_sale` | Point of Sale | Handle checkouts and payments for shops and restaurants. | Sales/Point of Sale | Có | Có trong source; chưa cài |
| standard | `populate` | Populate | Generate synthetic data for an Odoo database | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `portal` | Customer Portal | Customer Portal | Hidden | Không | Đã cài dev + test |
| standard | `portal_discuss` | Portal Discuss | Bridge module adding Discuss access from portal. | Services | Không | Đã cài dev + test |
| standard | `portal_rating` | Portal Rating | Bridge module adding rating capabilities on portal. It includes notably | Services | Không | Đã cài dev + test |
| standard | `pos_account_tax_python` | Allow custom taxes in POS | Add code to manage custom taxes to the POS assets bundle | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `pos_adyen` | POS Adyen | Integrate your POS with an Adyen payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_bancontact_pay` | POS Bancontact Pay & Wero | Accept Bancontact Pay and Wero QR code payments in POS (Payconiq). | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_cashdro` | POS Cashdro Cash Machines | Integrate your POS with a Cashdro automatic cash payment device | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_cashmatic` | POS Cashmatic Cash Machines | Integrate your POS with a cash matic automatic cash payment device | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_discount` | Point of Sale Discounts | Simple Discounts in the Point of Sale | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_dpopay` | PoS DPO Pay | Integrate your POS with DPO payment terminal. | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_edi_ubl` | Point of Sale UBL | UBL in the Point of Sale | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_event` | POS - Event | Link module between Point of Sale and Event | Technical | Không | Có trong source; chưa cài |
| standard | `pos_event_sale` | PoS - Event Sale | Link module between pos_sale and pos_event | Technical | Không | Có trong source; chưa cài |
| standard | `pos_glory_cash` | POS Glory Cash Machines | Integrate your POS with a Glory automatic cash payment device | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_hr` | POS - HR | Link module between Point of Sale and HR | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_hr_restaurant` | POS HR Restaurant | Link module between pos_hr and pos_restaurant | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_imin` | POS iMin | iMin ePOS Printers in PoS | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_loyalty` | Point of Sale - Coupons & Loyalty | Use Coupons, Gift Cards and Loyalty programs in Point of Sale | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_mercado_pago` | POS Mercado Pago | Integrate your POS with the Mercado Pago Smart Point terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_mollie` | POS Mollie | Integrate your POS with a Mollie payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_mrp` | pos_mrp | Link module between Point of Sale and Mrp | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_online_payment` | Point of Sale online payment | Module hỗ trợ cho Point of Sale online payment |  | Không | Có trong source; chưa cài |
| standard | `pos_online_payment_self_order` | POS Self-Order / Online Payment | Support online payment in self-order | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_partner_autocomplete` | POS Partner Autocomplete | Link module between Partner Autocomplete and Point of Sale | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_pine_labs` | POS Pine Labs | Integrate your POS with Pine Labs payment terminals | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_qfpay` | POS QFPay | Integrate your POS with the QFPay terminal in Hong Kong | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_razorpay` | POS Razorpay | Integrate your POS with a Razorpay payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_repair` | POS - Repair | Link module between Point of Sale and Repair | Technical | Không | Có trong source; chưa cài |
| standard | `pos_restaurant` | Restaurant | Restaurant extensions for the Point of Sale | Sales/Point of Sale | Có | Có trong source; chưa cài |
| standard | `pos_restaurant_loyalty` | POS - Restaurant Loyalty | Link module between pos_restaurant and pos_loyalty | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_safaricom` | POS Safaricom | Integrate your POS with the Safaricom Payment Provider | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sale` | POS - Sales | Link module between Point of Sale and Sales | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sale_delivery` | POS - Sales Delivery | Link module between Point of Sale and Delivery | Hidden | Không | Có trong source; chưa cài |
| standard | `pos_sale_loyalty` | POS - Sales Loyalty | Link module between pos_sale and pos_loyalty | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sale_margin` | POS - Sale Margin | Link module between Point of Sale and Sales Margin | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sale_stock` | POS - Sales Stock | Link module between PoS Stock and Sales | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order` | POS Self Order | Addon for the POS App that allows customers to view the menu on their smartphone. | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_bancontact_pay` | POS Self Order Bancontact Pay & Wero | Accept Bancontact Pay and Wero QR code payments in a kiosk (Payconiq). | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_event` | POS Self Order - Event | Link module between PoS Self Order and PoS Event | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_pine_labs` | POS Self Order Pine Labs | An addon for the Self Order App (KIOSK) that allows customers to pay using the Pine Labs POS Terminal. | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_qfpay` | POS Self Order QFPay | Addon for the Self Order App that allows customers to pay by QFPay. | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_razorpay` | POS Self Order Razorpay | Addon for the Self Order App that allows customers to pay by Razorpay POS Terminal. | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_sale` | POS Self Order Sale | Module hỗ trợ cho POS Self Order Sale | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_self_order_sms` | POS Self Order SMS | Integrates POS Self Order with SMS to send customers order confirmation via SMS. | Sales/Point Of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sms` | POS - SMS | This module integrates the Point of Sale with SMS | Send sms to customer for order confirmation | Không | Có trong source; chưa cài |
| standard | `pos_stock` | PoS - Stock | Stock integration for PoS | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_stripe` | POS Stripe | Integrate your POS with a Stripe payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_sumup` | POS SumUp | Integrate your POS with a SumUp payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `pos_viva_com` | PoS Viva.com | Integrate your PoS with a Viva.com payment terminal | Sales/Point of Sale | Không | Có trong source; chưa cài |
| standard | `printer` | Printer | Base module to manage external printers (e.g. ePOS, ZPL) |  | Không | Có trong source; chưa cài |
| standard | `privacy_lookup` | Privacy | Module hỗ trợ cho Privacy | Hidden | Không | Đã cài dev + test |
| standard | `product` | Products & Pricelists | This is the base module for managing products and pricelists in Odoo. | Sales/Sales | Không | Đã cài dev + test |
| standard | `product_email_template` | Product Email Template | Add email templates to products to be sent on invoice confirmation | Accounting/Accounting | Không | Có trong source; chưa cài |
| standard | `product_expiry` | Products Expiration Date | Track different dates on products and production lots. | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `product_margin` | Margins by Products | Adds a reporting menu in products that computes sales, purchases, margins and other interesting indicators based on invoices. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `product_matrix` | Product Matrix | Technical module: Matrix Implementation | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `project` | Project | Manage tasks and collaborate on projects | Services/Project | Có | Đã cài dev + test |
| standard | `project_account` | Project - Account | project profitability items computation | Accounting/Accounting | Không | Đã cài dev + test |
| standard | `project_hr_expense` | Project Expenses | Project expenses | Services/expenses | Không | Đã cài dev + test |
| standard | `project_hr_skills` | Project - Skills | Project skills | Services/Project | Không | Đã cài dev + test |
| standard | `project_mail_plugin` | Project Mail Plugin | Integrate your inbox with projects | Services/Project | Không | Đã cài dev + test |
| standard | `project_mrp` | MRP Project | Monitor MRP using project | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_mrp_account` | MRP Account Project | Monitor MRP account using project | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_mrp_sale` | MRP Project Sale | Technical Bridge | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_mrp_stock_landed_costs` | Project MRP Landed Costs | Technical Bridge | Supply Chain/Manufacturing | Không | Có trong source; chưa cài |
| standard | `project_purchase` | Project Purchase | Monitor purchase in project | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_purchase_stock` | Project - Purchase - Stock | Add a project link between POs and their generated stock pickings. | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_sale_expense` | Project - Sale - Expense | Adds a full traceability of reinvoice expenses on the profitability report. | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_sms` | Project - SMS | Send text messages when project/task stage move | Services/Project | Không | Đã cài dev + test |
| standard | `project_stock` | Project Stock | Link Stock pickings to Project | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_stock_account` | Project Stock Account | Handle analytics in Stock pickings with Project | Services/Project | Không | Có trong source; chưa cài |
| standard | `project_stock_landed_costs` | Project Stock Landed Costs | Technical Bridge | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `project_timesheet_holidays` | Timesheet when on Time Off | Schedule timesheet when on time off | Human Resources | Không | Có trong source; chưa cài |
| standard | `project_todo` | To-Do | Organize your work with memos and to-do lists | Productivity/To-Do | Có | Đã cài dev + test |
| standard | `purchase` | Purchase | Purchase orders, tenders and agreements | Supply Chain/Purchase | Có | Có trong source; chưa cài |
| standard | `purchase_alternative` | Purchase Alternative | This module allows you to manage your Purchase Alternative. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_alternative_sale` | Purchase Alternative Sale | Bridge module for Purchase Alternative and Sales. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_alternative_stock` | Purchase Alternative Stock | Module hỗ trợ cho Purchase Alternative Stock | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_edi_ubl_bis3` | Import/Export electronic orders with UBL | Allows to export and import formats: UBL Bis 3. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_mrp` | Purchase and MRP Management | This module provides facility to the user to install mrp and purchase modules at a time. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_product_matrix` | Purchase Matrix | Add variants to your purchase orders through an Order Grid Entry. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_repair` | Purchase Repair | Keep track of linked purchase and repair orders | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_requisition` | Purchase Agreements | This module allows you to manage your Purchase Agreements. | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_requisition_stock` | Purchase Requisition Stock | Module hỗ trợ cho Purchase Requisition Stock | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `purchase_stock` | Purchase Stock | Purchase Orders, Receipts, Vendor Bills for Stock | Supply Chain/Purchase | Không | Có trong source; chưa cài |
| standard | `rating` | Customer Rating | This module allows a customer to give rating. | Productivity | Không | Đã cài dev + test |
| standard | `repair` | Repairs | Repair damaged products | Supply Chain/Inventory | Có | Có trong source; chưa cài |
| standard | `resource` | Resource | Module for resource management. | Hidden | Không | Đã cài dev + test |
| standard | `resource_mail` | Resource Mail | Integrate features developped in Mail in use case involving resources instead of users | Hidden | Không | Đã cài dev + test |
| standard | `rpc` | RPC endpoints | Standard Odoo RPC endpoints to models | Extra Tools | Không | Đã cài dev + test |
| standard | `sale` | Sales | Sales internal machinery | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_crm` | Opportunity to Quotation | This module adds a shortcut on one or several opportunity cases in the CRM. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_edi_ubl` | Import electronic orders with UBL | Electronic ordering module | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_expense` | Sales Expense | Quotation, Sales Orders, Delivery & Invoicing Control | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_expense_margin` | Sales Expense Margin | When re-invoicing the expense on the SO, set the cost to the total untaxed amount of the expense. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_gelato` | Gelato | Place orders through Gelato's print-on-demand service | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_gelato_stock` | Gelato/Stock bridge | Module hỗ trợ cho Gelato/Stock bridge | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_loyalty` | Sale Loyalty | Use discounts and loyalty programs in sales orders | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_loyalty_delivery` | Sale Loyalty - Delivery | Adds free shipping mechanism in sales orders | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_management` | Sales | From quotations to invoices | Sales/Sales | Có | Có trong source; chưa cài |
| standard | `sale_margin` | Margins in Sales Orders | This module adds the 'Margin' on sales order. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_mrp` | Sales and MRP Management | This module provides facility to the user to install mrp and sales modulesat a time. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_mrp_margin` | Sale Mrp Margin | Handle BoM prices to compute sale margin. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_pdf_quote_builder` | Sales PDF Quotation Builder | Build nice quotations | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_product_matrix` | Sale Matrix | Add variants to Sales Order through a grid entry. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_project` | Sales - Project | Task Generation from Sales Orders | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_project_margin` | Sales Margins in Projects | Bridge module between Sales Margin and Project | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_project_stock` | Sale Project - Sale Stock | Adds a full traceability of inventory operations on the profitability report. | Sales | Không | Có trong source; chưa cài |
| standard | `sale_project_stock_account` | Sale Project Stock Account | Technical Bridge | Hidden | Không | Có trong source; chưa cài |
| standard | `sale_purchase` | Sale Purchase | Sale based on service outsourcing. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_purchase_project` | Sale Purchase Project | Technical Bridge | Sales | Không | Có trong source; chưa cài |
| standard | `sale_purchase_stock` | MTO Sale <-> Purchase | SO/PO relation in case of MTO | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_service` | Sales - Service | Interaction between Sales and services apps (project and planning) | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_sms` | Sale - SMS | Ease SMS integration with sales capabilities | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_stock` | Sales and Warehouse Management | Quotation, Sales Orders, Delivery & Invoicing Control | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_stock_margin` | Sale Stock Margin | Once the delivery is validated, update the cost on the SO to have an exact margin computation. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_stock_product_expiry` | Sale Stock Product Expiry | Modifications to the forecast widget on SO lines to show fresh stock, i.e. ignoring stock to be removed due to expiration. | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_timesheet` | Sales Timesheet | Sell based on timesheets | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sale_timesheet_margin` | Service Margins in Sales Orders | Bridge module between Sales Margin and Sales Timesheet | Sales/Sales | Không | Có trong source; chưa cài |
| standard | `sales_team` | Sales Teams | Sales Teams | Sales/Sales | Không | Đã cài dev + test |
| standard | `sms` | SMS gateway | SMS Text Messaging | Sales/Sales | Không | Đã cài dev + test |
| standard | `sms_twilio` | Twilio SMS | Send SMS messages using Twilio | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `snailmail` | Snail Mail | Allows users to send documents by post | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `snailmail_account` | Snail Mail - Account | Allows users to send invoices by post | Hidden/Tools | Không | Có trong source; chưa cài |
| standard | `social_media` | Social Media | Social media connectors for company settings. | Marketing/Social Marketing | Không | Có trong source; chưa cài |
| standard | `spreadsheet` | Spreadsheet | Spreadsheet | Productivity/Dashboard | Không | Đã cài dev + test |
| standard | `spreadsheet_account` | Spreadsheet Accounting Formulas | Spreadsheet Accounting formulas | Accounting | Không | Đã cài dev + test |
| standard | `spreadsheet_dashboard` | Spreadsheet dashboard | Spreadsheet | Productivity/Dashboard | Không | Đã cài dev + test |
| standard | `spreadsheet_dashboard_account` | Spreadsheet dashboard for accounting | Spreadsheet | Productivity/Dashboard | Không | Đã cài dev + test |
| standard | `spreadsheet_dashboard_event_sale` | Spreadsheet dashboard for events | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_hr_expense` | Spreadsheet dashboard for expenses | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_hr_timesheet` | Spreadsheet dashboard for time sheets | Spreadsheet | Productivity/Dashboard | Không | Đã cài dev + test |
| standard | `spreadsheet_dashboard_im_livechat` | Spreadsheet dashboard for live chat | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_pos_hr` | Spreadsheet dashboard for point of sale | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_pos_restaurant` | Spreadsheet dashboard for restaurants | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_sale` | Spreadsheet dashboard for sales | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_sale_timesheet` | Spreadsheet dashboard for time sheets | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_stock_account` | Spreadsheet dashboard for stock | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_website_sale` | Spreadsheet dashboard for eCommerce | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `spreadsheet_dashboard_website_sale_slides` | Spreadsheet dashboard for eLearning | Spreadsheet | Productivity/Dashboard | Không | Có trong source; chưa cài |
| standard | `stock` | Inventory | Manage your stock and logistics activities | Supply Chain/Inventory | Có | Có trong source; chưa cài |
| standard | `stock_account` | WMS Accounting | Inventory, Logistic, Valuation, Accounting | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `stock_delivery` | Delivery - Stock | Allows you to add delivery methods in pickings. | Shipping Connectors | Không | Có trong source; chưa cài |
| standard | `stock_dropshipping` | Drop Shipping | Drop Shipping | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `stock_fleet` | Stock Transport | Stock Transport Management |  | Không | Có trong source; chưa cài |
| standard | `stock_landed_costs` | WMS Landed Costs | Landed Costs | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `stock_maintenance` | Stock - Maintenance | See lots used in maintenance | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `stock_sms` | Stock - SMS | Send text messages when final stock move | Supply Chain/Inventory | Không | Có trong source; chưa cài |
| standard | `survey` | Surveys | Send your surveys or share them live. | Marketing/Surveys | Có | Có trong source; chưa cài |
| standard | `survey_crm` | Survey CRM | Generate leads from surveys | Marketing/Surveys | Không | Có trong source; chưa cài |
| standard | `test_base_automation` | Test - Base Automation | Base Automation Tests: Ensure Flow Robustness | Hidden | Không | Có trong source; chưa cài |
| standard | `test_crm_full` | Test Full Crm Flow | This module is intended to test the main crm flows of Odoo, both frontend and | Hidden/Tests | Không | Có trong source; chưa cài |
| standard | `test_discuss_full` | Test Discuss (full) | Test of Discuss with all possible overrides installed. | Productivity/Discuss | Không | Có trong source; chưa cài |
| standard | `test_event_full` | Test Full Event Flow | This module will test the main event flows of Odoo, both frontend and backend. | Hidden/Tests | Không | Có trong source; chưa cài |
| standard | `test_html_field_history` | Test - html_field_history | Module hỗ trợ cho Test - html_field_history | Hidden | Không | Có trong source; chưa cài |
| standard | `test_import_export` | Test - Import & Export | Base Import & Export Tests: Ensure Flow Robustness | Hidden | Không | Có trong source; chưa cài |
| standard | `test_mail` | Mail Tests | Mail Tests: performances and tests specific to mail | Hidden | Không | Có trong source; chưa cài |
| standard | `test_mail_full` | Mail Tests (Full) | Mail Tests: performances and tests specific to mail with all sub-modules | Hidden | Không | Có trong source; chưa cài |
| standard | `test_mail_sms` | SMS Tests | SMS Tests: performances and tests specific to SMS | Hidden | Không | Có trong source; chưa cài |
| standard | `test_mass_mailing` | Mass Mail Tests | Mass Mail Tests: feature and performance tests for mass mailing | Marketing/Email Marketing | Không | Có trong source; chưa cài |
| standard | `test_populate` | Odoo Populate Tests | Test module for Odoo's Populate | Hidden/Tests | Không | Có trong source; chưa cài |
| standard | `test_resource` | Test - Resource | Module hỗ trợ cho Test - Resource | Hidden | Không | Có trong source; chưa cài |
| standard | `test_sale_product_configurators` | Sale Product Configurators Tests | Test Suite for Sale Product Configurator | Hidden | Không | Có trong source; chưa cài |
| standard | `test_sale_purchase_edi_ubl` | Test - Sale & Purchase Order EDI | Sale & Purchase Order EDI Tests: Ensure Flow Robustness | Hidden | Không | Có trong source; chưa cài |
| standard | `test_spreadsheet` | Spreadsheet Test | Spreadsheet Test, mainly to test the mixin behavior | Hidden | Không | Có trong source; chưa cài |
| standard | `test_translation_mode` | Translation Mode | In-context and interactive translation mode to streamline the module translation process using Weblate | Hidden | Không | Có trong source; chưa cài |
| standard | `test_utm` | UTM Tests | UTM Tests: tests specific to the UTM module | Hidden | Không | Có trong source; chưa cài |
| standard | `test_website` | Website Test | Website Test, mainly for module install/uninstall tests | Hidden | Không | Có trong source; chưa cài |
| standard | `test_website_modules` | Website Modules Test | This module contains tests related to website modules. | Hidden | Không | Có trong source; chưa cài |
| standard | `test_website_slides_full` | Test Full eLearning Flow | This module will test the main certification flow of Odoo. | Hidden/Tests | Không | Có trong source; chưa cài |
| standard | `theme_default` | Default Theme | Default website theme | Theme | Không | Có trong source; chưa cài |
| standard | `uom` | Units of measure | This is the base module for managing Units of measure. | Sales/Sales | Không | Đã cài dev + test |
| standard | `utm` | UTM Trackers | Enable management of UTM trackers: campaign, medium, source. | Marketing | Không | Đã cài dev + test |
| standard | `web` | Web | Odoo Web core module. | Hidden | Không | Đã cài dev + test |
| standard | `web_hierarchy` | Web Hierarchy | Odoo Web Hierarchy view | Hidden | Không | Đã cài dev + test |
| standard | `web_tour` | Tours | Odoo Web tours. | Hidden | Không | Đã cài dev + test |
| standard | `web_unsplash` | Unsplash Image Library | Find free high-resolution images from Unsplash | Hidden | Không | Đã cài dev + test |
| standard | `website` | Website | Enterprise website builder | Website/Website | Có | Có trong source; chưa cài |
| standard | `website_address_autocomplete` | Website Address Autocomplete | Assist your users with automatic completion & suggestions when filling their address | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_blog` | Blog | Publish blog posts, announces, news | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_cf_turnstile` | Cloudflare Turnstile | This module implements Cloudflare Turnstile so that you can prevent bot spam on your forms. | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_crm` | Contact Form | Generate leads from a contact form | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_crm_iap_reveal` | Lead Generation From Website Visits | Generate Leads/Opportunities from your website's traffic | Sales/CRM | Không | Có trong source; chưa cài |
| standard | `website_crm_livechat` | Lead Livechat Sessions | View livechat sessions for leads | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_crm_partner_assign` | Resellers | Publish your resellers/partners and forward leads to them | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_crm_sms` | Send SMS to Visitor with leads | Allows to send sms to website visitor that have lead | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_customer` | Customer References | Publish your customer references | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_event` | Events | Publish events, sell tickets | Marketing/Events | Có | Có trong source; chưa cài |
| standard | `website_event_booth` | Online Event Booths | Events, display your booths on your website | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_booth_exhibitor` | Booths/Exhibitors Bridge | Event Booths, automatically create a sponsor. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_booth_sale` | Online Event Booth Sale | Events, sell your booths online | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_booth_sale_exhibitor` | Booths Sale/Exhibitors Bridge | Bridge module between website_event_booth_exhibitor and website_event_booth_sale. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_crm` | Website Events CRM | Allow per-order lead creation mode | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_event_exhibitor` | Event Exhibitors | Event: manage sponsors and exhibitors | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_sale` | Online Event Ticketing | Sell event tickets online | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_event_track` | Advanced Events | Sponsors, Tracks, Agenda, Event News | Marketing | Không | Có trong source; chưa cài |
| standard | `website_event_track_live` | Live Event Tracks | Support live tracks: streaming, participation, youtube | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_track_live_quiz` | Quiz on Live Event Tracks | Bridge module to support quiz features during "live" tracks. | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_event_track_quiz` | Quizzes on Tracks | Quizzes on tracks | Marketing/Events | Không | Có trong source; chưa cài |
| standard | `website_forum` | Forum | Manage a forum with FAQ and Q&A | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_google_map` | Google Maps | Show your company address on Google Maps | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_hr_recruitment` | Online Jobs | Manage your online hiring process | Website/Website | Có | Có trong source; chưa cài |
| standard | `website_hr_recruitment_livechat` | Website IM Livechat HR Recruitment | Chatbot for the HR Recruitment | Website/Live Chat | Không | Có trong source; chưa cài |
| standard | `website_links` | Link Tracker | Generate trackable & short URLs | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_livechat` | Website Live Chat | Chat with your website visitors | Website/Live Chat | Không | Có trong source; chưa cài |
| standard | `website_mail` | Website Mail | Website Module for Mail | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_mail_group` | Website Mail Group | Add a website snippet for the mail groups. |  | Không | Có trong source; chưa cài |
| standard | `website_mass_mailing` | Newsletter Subscribe Button | Attract visitors to subscribe to mailing lists | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_mass_mailing_event` | Mass mailing on website events | Add pre-filled snippets in mass_mailing with an event snapshot | Marketing/Email Marketing/Website | Không | Có trong source; chưa cài |
| standard | `website_mass_mailing_sms` | Newsletter Subscribe SMS Template | Attract visitors to subscribe to mailing lists | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_partner` | Website Partner | Partner module for website | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_partnership` | Website Partnership | Publish your partners on your website | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_payment` | Website Payment | Payment integration with website | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_profile` | Website profile | Access the website profile of the users | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_project` | Online Task Submission | Add a task suggestion form to your website | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale` | eCommerce | Sell your products online | Website/Website | Có | Có trong source; chưa cài |
| standard | `website_sale_collect` | Click & Collect | Allows customers to check in-store stock, pay on site, and pick up their orders at the shop. | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_gelato` | eCommerce/Gelato bridge | Module hỗ trợ cho eCommerce/Gelato bridge | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_loyalty` | Coupons, Promotions, Gift Card and Loyalty for eCommerce | Use coupon, promotion, gift cards and loyalty programs in your eCommerce store | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_mass_mailing` | Checkout Newsletter | Let new customers sign up for a newsletter during checkout | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_mrp` | Kit Availability | Manage Kit product inventory & availability | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_project` | Website Sale - Project | Bridge module between website_sale and project | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_sale_slides` | Sell Courses | Sell your courses online | Website/eLearning | Không | Có trong source; chưa cài |
| standard | `website_sale_stock` | Product Availability | Manage product inventory & availability | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_slides` | eLearning | Manage and publish an eLearning platform | Website/eLearning | Có | Có trong source; chưa cài |
| standard | `website_slides_forum` | Forum on Courses | Allows to link forum on a course | Website/eLearning | Không | Có trong source; chưa cài |
| standard | `website_slides_survey` | Course Certifications | Add certification capabilities to your courses | Website/eLearning | Không | Có trong source; chưa cài |
| standard | `website_sms` | Send SMS to Visitor | Allows to send sms to website visitor | Website/Website | Không | Có trong source; chưa cài |
| standard | `website_timesheet` | Hide Portal Timesheet Information | Allow hiding timesheet information in the portal | Website/Website | Không | Có trong source; chưa cài |

## 7. Kết luận cho TANPHAT ONE

- Đã có nền: `crm`, `account`, `hr`, `hr_timesheet`, `hr_expense`, `project` và các bridge/phụ trợ cần thiết; custom `tp_core`, `tp_organization`, `tp_project`, `tp_contract`, `tp_api`, `tp_planning_api` đã cài trên dev/test.
- `tp_web_login` có trong source nhưng hiện chưa cài theo `scripts/dev.py`; không kết luận đã triển khai native login vào dev chỉ vì source tồn tại.
- Chưa có trong checkout các nhóm Odoo thường được gọi là Documents, Approvals, Planning, Helpdesk, Payroll, Sign, Quality, PLM, Rental, Subscriptions và Field Service. Nếu cần, phải xác định edition/license và tạo task riêng.
- `survey` chỉ là khảo sát biểu mẫu chung; không thay TP Survey khảo sát hiện trường. `purchase_requisition` là thỏa thuận/yêu cầu mua; không thay TP Bid. `hr` là nhân sự nền; không phải payroll. `account` là kế toán Odoo; chưa phải TP Finance hoàn chỉnh.
- Không cài module mới chỉ để làm đủ danh sách. Chọn theo vertical slice, nghiệp vụ, quyền, migration, backup/restore và test.

## 8. Nguồn và giới hạn kiểm tra

- Metadata local đọc AST từ manifest; không chạy mã addon. Trạng thái cài đặt truy vấn SELECT trên dev/test, transaction read-only; không start/stop/upgrade/seed hay thay đổi cấu hình. Chỉ trạng thái cài module được đối chiếu; chưa nghiệm thu tính năng hoặc kiểm từng màn hình.
- [Odoo 20 User Docs](https://www.odoo.com/documentation/20.0/applications.html), [All Apps](https://www.odoo.com/page/all-apps), [Editions](https://www.odoo.com/page/editions): HTTP 200 ngày 29/10/2026. Các trang giới thiệu không thay inventory module Enterprise; technical name ngoài checkout là tên tham chiếu cần xác nhận khi có edition tương ứng.
- Khái niệm ứng dụng được giới thiệu có thể tương ứng nhiều addon; application=True chỉ là cờ menu/app, không phải toàn bộ nghiệp vụ. Một app source chưa cài không có nghĩa là chưa có quyền bản quyền, và app đã cài không đồng nghĩa dịch vụ ngoài đã được kích hoạt.
