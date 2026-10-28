# Khảo sát source cho Tan Phat Executive Dashboard

Ngày khảo sát: 27/10/2026, múi giờ Asia/Saigon. Phạm vi lượt này: khảo sát và lập kế hoạch; chưa tạo module, sửa core, cài dependency hoặc thay đổi database.

## Kết luận kiến trúc

Xây một addon riêng tên tanphat_dashboard trong custom_addons, mở bằng ir.actions.client trong Web Client hiện có. Dùng OWL đang được đóng gói trong source, XML, SCSS và Chart.js có sẵn. Tầng repository trả DTO chuẩn hóa; các trang không biết cấu trúc Excel. Giai đoạn đầu không cần React, ứng dụng web riêng, controller hoặc model nghiệp vụ mới.

**Điểm tương thích quyết định:** source này khai báo Odoo 20.0 nhưng OWL thực tế là 3.0.0-alpha.50. Không sao chép nguyên mẫu OWL 2 của Odoo 16–19. Lớp tương thích trong repo sẽ ném lỗi nếu component khai báo static props hoặc static defaultProps. Phải làm một spike nhỏ theo API của commit hiện tại trước khi xây các trang.

## Vị trí và trạng thái source

| Thuộc tính | Bằng chứng đã kiểm tra |
| --- | --- |
| Thư mục ban đầu | C:\odoo; C:\TanPhatManagement chưa tồn tại khi bắt đầu |
| Thư mục hiện tại | C:\TanPhatManagement; đã đổi tên theo chỉ dẫn trực tiếp của người dùng, sau khi người dùng lưu và đóng VS Code |
| Git branch | 20.0 |
| Commit | f03f160f13cc86364161f79182ba18fc19a134ed |
| Commit date | 2026-09-18 03:32:39 +0000 |
| Commit subject | [FIX] mail: remove misleading company name from public welcome page |
| Trạng thái trước viết tài liệu | git status --short rỗng; chưa có thay đổi tracked |
| Phiên bản | odoo/release.py:15: version_info = (20, 0, 0, FINAL, 0, '') |
| Yêu cầu runtime trong source | Python 3.12–3.14 theo MIN_PY_VERSION/MAX_PY_VERSION; PostgreSQL >=16 |
| Addon | addons có 644 thư mục, 643 manifest; odoo/addons có 16 manifest |
| Ngoại lệ cấu trúc | addons/mrp_subcontracting_repair không có manifest; cần kiểm tra nếu cài module này, không liên quan dependency của dashboard |
| Custom/Enterprise | Không thấy thư mục custom_addons, enterprise hoặc virtualenv ở root đã khảo sát; không suy ra danh sách module đã cài trong DB |
| Hosting | Không thấy .openai/hosting.json; đây là kế hoạch addon nội bộ Odoo |
| Chỉ dẫn repo | Không tìm thấy AGENTS.md bằng rg --files; có skills/odoo-guidelines và skills/odoo-web-guidelines |

Phiên bản trên là **phiên bản source checkout**, chưa phải bằng chứng server đang chạy hoặc bản phát hành upstream đã được triển khai. Không kết luận edition, tính ổn định production hay module đã cài từ tên branch. Tài liệu tổng thể trên NAS gọi nền tảng là Community, nhưng đó là thông tin tham khảo cần xác nhận khi triển khai.

## Bằng chứng frontend và khả năng tái sử dụng

Các liên kết dưới đây trỏ tới file source thực tế, tương đối với thư mục tài liệu này.

| Nhu cầu | Source đã đọc | Kết luận sử dụng |
| --- | --- | --- |
| Assets backend | [web manifest](../../addons/web/__manifest__.py) | Khai báo JS/XML/SCSS trong web.assets_backend của addon mới |
| OWL | [owl.js](../../addons/web/static/lib/owl/owl.js), biến version; [module alias](../../addons/web/static/lib/owl/odoo_module.js) | import từ @odoo/owl; dùng signal/proxy, computed và useProps theo mẫu repo |
| Tương thích OWL | [compatibility layer](../../addons/web/static/src/owl2/owl3_compatibility_layer.js) | Tránh mẫu static props cũ; không sửa hoặc dựa vào shim để viết code mới |
| Client Action | [mysubscription dashboard](../../addons/mysubscription/static/src/dashboard.js), [action XML](../../addons/mysubscription/views/menus.xml) | registry.category("actions").add với tag riêng; record XML tag phải khớp tuyệt đối |
| Model kỹ thuật action | [ir_actions.py](../../odoo/addons/base/models/ir_actions.py), class IrActionsClient | target=current để giữ navbar Odoo; không cần res_model nghiệp vụ |
| Menu | [mail menus](../../addons/mail/views/mail_menus.xml) | menuitem mở action; demo chỉ cho nhóm quản trị base.group_system |
| Chart.js | [Chart.js](../../addons/web/static/lib/Chart/Chart.js) | Đã có v4.5.0; không cài npm/CDN bản thứ hai |
| Chart lifecycle | [useChart](../../addons/web/static/src/core/utils/chart_hook.js) | Hook tự load web.chartjs_lib, dựng chart, destroy trước patch và unmount |
| Biểu đồ chuẩn | [graph renderer](../../addons/web/static/src/views/graph/graph_renderer.js) | Tham khảo cấu hình/chart hook; không dùng GraphView vốn yêu cầu ORM/model cho mock |
| Bộ chọn | [Dropdown](../../addons/web/static/src/core/dropdown/dropdown.js) | Tái sử dụng dropdown và tương tác bàn phím; wrapper dự án/hạng mục do addon quản lý |
| Phân trang | [Pager](../../addons/web/static/src/core/pager/pager.js) | Tái sử dụng pager trên bảng DTO; không kéo theo ListView/ORM |
| Service | [hooks](../../addons/web/static/src/core/utils/hooks.js), [registry](../../addons/web/static/src/core/registry.js) | useService cho repository, action, dialog, notification; root sở hữu query state |
| Test frontend | [webclient test helpers](../../addons/web/static/tests/_framework/webclient_test_helpers.js), web.assets_unit_tests | Dùng HOOT và mountWebClient cho client action; không thêm test framework |
| Dashboard chuẩn | [board manifest](../../addons/board/__manifest__.py) | board phụ thuộc spreadsheet_dashboard; không thêm dependency này chỉ để vẽ KPI từ mock |

### Cách cài đặt được đề xuất cho lượt triển khai sau

1. Tạo custom_addons/tanphat_dashboard, giữ addons/ và odoo/ nguyên trạng.
2. Manifest version đề xuất 20.0.1.0.0, depends=['web'], license=LGPL-3, application=True, auto_install=False, installable=True. Không thêm base hoặc project/account khi chưa dùng tính năng trực tiếp của chúng.
3. Data XML nạp action trước menu; tag tanphat_dashboard.dashboard. Menu ứng dụng tên “Quản trị Tấn Phát”; màn hình mở trong content area Odoo, có sidebar nội bộ.
4. Assets khai báo feature JS/XML/SCSS trong web.assets_backend; test chỉ nằm trong web.assets_unit_tests. Không đưa file hợp đồng, snapshot thật hoặc tài chính thật vào static.
5. Addons path gồm C:\TanPhatManagement\addons và C:\TanPhatManagement\custom_addons, đồng thời giữ path base của Odoo nếu cấu hình hiện tại yêu cầu. Xác nhận path được server nạp qua log.
6. Cài trên database phát triển mới. Cập nhật Apps List rồi cài addon, hoặc dùng -i tanphat_dashboard --stop-after-init. Khi cập nhật dùng -u đúng DB; không chạy lệnh này trên DB chưa xác định.

Đây là hướng dẫn kế hoạch. Chưa có manifest, menu hay module nào được tạo trong lượt hiện tại.

## Môi trường đã xác minh và khoảng trống

| Hạng mục | Hiện trạng | Hệ quả/việc cần làm |
| --- | --- | --- |
| Python mặc định | 3.12.6 tại C:\Users\vuduc\AppData\Local\Programs\Python\Python312\python.exe | Đúng mức tối thiểu; cần venv riêng cho repo |
| Dependency | pip check báo không có yêu cầu bị hỏng trong môi trường đang cài; import probe thiếu lxml, sass, cbor2 | pip check không chứng minh đã cài đầy đủ requirements của Odoo |
| Khởi động thử | python odoo-bin --version thất bại với ModuleNotFoundError: passlib | Chưa chạy được server; chưa xác nhận asset build, cài addon hay test browser |
| PostgreSQL | Service postgresql-x64-18 Running; có thư mục binary 17 và 18; psql 18.1 | Không suy ra DB sử dụng phiên bản nào chỉ từ binary |
| Kết nối | Probe TCP 127.0.0.1:5432 bị từ chối | Cần kiểm tra port/listen thực tế, host, quyền kết nối; chưa đọc DB/schema/module đã cài |
| Cấu hình Odoo | Chỉ thấy debian/odoo.conf mẫu: db_host=False, db_port=False, db_user=odoo; addons_path Linux bị comment | Chưa có cấu hình chạy local xác nhận; không dùng file Debian làm cấu hình Windows |
| Cấu hình khác | Không thấy root odoo.conf hoặc C:\Users\vuduc\.odoorc; .vscode/settings.json chỉ có DockerRun.DisableDockerrc | Cần tạo cấu hình local ngoài tracked secrets khi triển khai |
| Sau đổi tên | .vscode không có launch.json chứa path cũ | Kiểm tra lại terminal, shortcut và cấu hình ngoài repo nếu có; chưa sửa cấu hình ngoài repo |

Không cài package, khởi động lại dịch vụ hay tạo DB trong lượt lập kế hoạch. Các giá trị mật khẩu không được thu thập hoặc ghi vào tài liệu.

## Đầu vào nghiệp vụ đã đọc

| Tài liệu | Tình trạng và cách dùng |
| --- | --- |
| Yêu cầu người dùng | Văn bản đã dán là yêu cầu điều khiển phạm vi: chỉ frontend, không backend mới, không code lượt này |
| DA Temp.xlsm | Đọc trực tiếp tại \\192.168.1.2\6.3 Tadic_Thu viec\ERP\Ban KD\DA Temp.xlsm; 381.570 bytes; last modified 23/10/2026 17:08:18 theo metadata máy |
| Dấu vân tay workbook | SHA-256 b09872dd439f199e5f80818d6f91e79d54966728c93b10792a50d126bd173db7 |
| DA Temp(6).xlsm | Chưa thấy đúng tên này; không coi đồng nhất với DA Temp.xlsm chỉ vì tên gần giống |
| Phan_tich_nghiep_vu.docx | Chưa tìm thấy trong workspace và các vị trí NAS trực tiếp đã khảo sát; cần bổ sung đúng file/phiên bản. Không kết luận đã rà hết NAS |
| Quy trinh nghiep vu TanPhat JSC_V1.0.docx | Tìm thấy tại thư mục ERP trên NAS; bản 1.0 tháng 7/2026; đã đọc nội dung và bảng để xác nhận vai trò Ban KD/Kế hoạch, QT-TC và lãnh đạo |
| Thiet_ke_tong_the_phan_mem_quan_tri_Tan_Phat_Odoo20_Thuan Drafft.docx | Cùng thư mục ERP; bản nháp ngày 27/10/2026; tham khảo mô hình dài hạn, không lấy chỉ dẫn mở rộng thành phạm vi hiện tại |

Đã phân biệt **nội dung tham khảo** trong workbook/DOCX với **chỉ dẫn trực tiếp** của người dùng. Hướng dẫn bật macro, nhập liệu, đồng bộ NAS, duyệt chi, tạo backend tp_* và mobile trong các tài liệu là dữ liệu bối cảnh, không được thực thi trong lượt này. “Biên dự án” trong bản nháp không được đưa vào dashboard như lợi nhuận. Nhận định bản Community không có một số app trong bản nháp phải kiểm tra lại theo source, không dùng làm kết luận kỹ thuật mặc định.

## Workbook thực tế

| Sheet | Kích thước khai báo | Vai trò |
| --- | --- | --- |
| HDSD | 420 x 7, hidden | Hướng dẫn và quy tắc nghiệp vụ; không chạy macro |
| TU_DIEN | 112 x 5, hidden | Định nghĩa KPI, hiệu lực và khoán hai cấp |
| Dashboard | 40 x 12 | Công thức tham chiếu tổng CĐT/thầu phụ |
| DATA | 48 x 14 | D6 mã, D7 tên, D8 CĐT; các form A/B chỉ là đầu nhập |
| ChuDauTu | 110 x 20 | Header dòng 10; dữ liệu 11–110; tổng dòng 9 |
| Thauphu | 206 x 24 | Header dòng 6; dữ liệu 7–206; tổng cấp 1 dòng 4, cấp 2 dòng 5 |
| DM_HangMuc | 103 x 4 | Header dòng 3, danh mục A4:A103 |
| DanhBa_ThauPhu | 305 x 10 | Header dòng 4, danh bạ A5:F305; cột tìm kiếm không phải master key |
| NHAT_KY_TC | 504 x 18 | 5 bản ghi có ID; 3 bản đang hiệu lực theo quy tắc ID gốc |
| NHAT_KY | 504 x 19 | 3 bản ghi có ID, đều còn hiệu lực trong snapshot |
| TEMPLATE_TP | 6 x 14, hidden | Mẫu dựng sheet, không phải sổ giao dịch bổ sung |
| TP_TAFCO | 306 x 14 | 2 giao dịch; đối chiếu NHAT_KY ID 1,2 |
| TP_Phòng Thiết kế (nội bộ) | 306 x 14 | 1 giao dịch; đối chiếu NHAT_KY ID 3 |

Kích thước sheet bao gồm vùng công thức dự phòng. Không coi 500 dòng có công thức là 500 giao dịch. Workbook có xl/vbaProject.bin, fullCalcOnLoad=True; chỉ kiểm tra sự tồn tại, chưa phân tích mã VBA hoặc chạy macro. Dữ liệu cache và công thức được đọc riêng; không sửa/lưu lại workbook và không tuyên bố đã recalculation bằng Excel.

## Rủi ro cần giải quyết trước khi xây

| ID | Mức | Rủi ro | Cách xử lý |
| --- | --- | --- | --- |
| A01 | P0 | OWL alpha và compatibility layer khác mẫu cũ | Pin commit; spike action/props/state/chart; HOOT lifecycle |
| A02 | P0 | Runtime chưa chạy, PostgreSQL chưa kết nối | Venv theo requirements; xác minh DB dev/port trước cài module |
| A03 | P0 | Snapshot có sửa giao dịch | Deduplicate theo stream + ID GỐC, chọn ID lớn nhất rồi xét XÓA |
| A04 | P0 | Trùng khoán hai cấp | Tổng công ty chỉ cấp 1; cột tổng cấp 2 riêng |
| A05 | P0 | Dữ liệu thật bị public qua static | Chỉ fixture ẩn danh và biến đổi số tiền; raw snapshot riêng ngoài assets/repo công khai |
| A06 | P0 | “Khảo sát” CĐT khác “Khảo sát địa hình” thầu phụ; DM_HangMuc cột D có nội dung không khớp cột A ở một số dòng | Không tự ghép theo gần nghĩa hoặc dùng cột không dấu làm mã; BA chốt crosswalk trước so cùng hạng mục |
| A07 | P0 | Sản lượng 0 khiến chênh chưa NT để trống nhưng dòng tổng Excel thành 0 | Giữ provenance/availability; không diễn giải 0 tổng thành đã đủ sản lượng |
| A08 | P1 | Khoán mẹ có nhiều hạng mục; SUMIFS R theo tên mẹ không lọc hạng mục | Tạm tổng hợp cấp phòng duy nhất, không cộng lặp R/S trên nhiều dòng; chốt phạm vi phân bổ với BA |
| A09 | P1 | Cột hóa đơn mang tên “phải xuất” nhưng định nghĩa là tổng hóa đơn đã ghi nhận | Giữ nhãn tương thích và thêm giải thích; không tính NT trừ hóa đơn thành số đã xuất |
| A10 | P1 | Ngày ghi sổ, ngày sửa và ngày nghiệp vụ chưa tách | Chỉ lịch sử theo ngày ghi sổ hiện có; chưa công bố số dư lịch sử “tại ngày” |

Các quyết định triển khai và danh sách việc tiếp theo nằm trong [06_IMPLEMENTATION_PLAN.md](06_IMPLEMENTATION_PLAN.md). Hợp đồng dữ liệu và quy tắc nghiệp vụ chi tiết nằm trong [05_DATA_CONTRACT.md](05_DATA_CONTRACT.md).
