# TANPHAT ONE — Sổ kiến thức tham khảo và bàn giao điều phối

**Mục đích:** lưu các kết quả nghiên cứu bên ngoài và quan sát đọc-only để phiên AI mới tiếp tục đúng hướng. Tài liệu này là sổ tham khảo và điều phối; nó không tự tạo quy chế nghiệp vụ, không cấp quyền và không cho phép triển khai chức năng.

**Cập nhật:** 29/10/2026 (Asia/Saigon)  
**Sản phẩm:** TANPHAT ONE  
**Nguồn trạng thái chính:** [`PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
**Nguồn quyết định:** [`DECISIONS.md`](../DECISIONS.md)  
**Quy trình điều phối:** [`AI_COORDINATION_WORKFLOW.md`](../AI_COORDINATION_WORKFLOW.md)

## 1. Cách đọc và phân loại

Mỗi thông tin trong sổ này thuộc một trong năm loại:

- **Quyết định đã xác nhận (User-confirmed):** có quyết định người dùng ghi tại DEC hoặc đặc tả tương ứng; không suy từ test fixture.
- **Quan sát nguồn (Observed):** điều nhìn thấy trong tài liệu/web/ứng dụng tại thời điểm ghi; không suy ra chính sách hoặc sự đầy đủ của hệ thống.
- **Bằng chứng kỹ thuật (Runtime-evidence):** có lệnh, log/test và môi trường cụ thể; technical acceptance không thay business acceptance. Khi chỉ đọc lại handoff phải ghi `reported`, không tự nhận đã chạy lại.
- **Đề xuất (Proposed):** hướng thiết kế để thảo luận; chỉ trở thành yêu cầu code khi có task, scope và cổng chấp nhận.
- **Chưa kiểm chứng (Open):** cần chủ nghiệp vụ, owner, hồ sơ hoặc kiểm tra kỹ thuật bổ sung.

Không dùng bài marketing, ảnh chụp giao diện, tên menu hay một lần đăng nhập Base để kết luận về hạn mức, thẩm quyền ký, số bước duyệt, API, tính pháp lý hoặc quyền dữ liệu.

Mỗi mục phải giữ được bốn phần provenance: nguồn/locator, ngày hoặc phiên bản, loại bằng chứng và phạm vi môi trường. Sổ này không lưu credential, cookie, số tiền thật, PII, database dump hay đường dẫn NAS/UNC.

## 2. Nguồn đã đọc

| Mã | Nguồn | Thời điểm/phạm vi | Phân loại bằng chứng |
| --- | --- | --- | --- |
| REF-A1-20261029 | [Giải pháp Odoo ERP cho ngành xây dựng — A1 Consulting](https://www.a1consulting.vn/giai-phap-odoo-nganh-xay-dung) | Đọc HTTP 200, nội dung HTML phía máy chủ, 29/10/2026 (Asia/Saigon) | Bài giới thiệu/marketing; dùng để gợi ý capability, không phải đặc tả sản phẩm |
| REF-BASE-REQUEST-20261029 | Base home và Request trong phiên đăng nhập do người dùng mở | Đọc-only, 29/10/2026; không tạo/lưu/gửi request, không upload, không lấy credential/cookie | Quan sát UI của tài khoản/filter hiện tại; không đại diện cho toàn công ty |
| REF-TP-RUNTIME-20261029 | `docs/PROJECT_STATUS.md`, `docs/CHANGELOG.md`, các handoff CHG-039/040/041 | 29/10/2026; test/dev theo từng CHG, ghi theo handoff hiện có | Runtime claim historical/report-only trong sổ này; chưa độc lập audit |
| REF-TP-DESIGN-20261029 | `AGENTS.md` mục 2, `docs/architecture/TP_PRODUCT_NAMING.md`, bộ thiết kế BIZ-002 | Đối chiếu source docs 29/10/2026 | Phạm vi sản phẩm đang chuẩn bị; không tự xác nhận mô hình tổ chức hay chức năng đã vận hành |
| REF-ARCH-PDF-20261029 | `TP_ONE_So_do_kien_truc.pdf`, tiêu đề “TP.ONE — SƠ ĐỒ KIẾN TRÚC HỆ THỐNG” | 1 trang A4; đọc text và render kiểm tra ngày 29/10/2026; nguồn UNC do người dùng cung cấp | Sơ đồ kiến trúc mục tiêu/ý tưởng; không phải inventory module, schema, quyền hoặc runtime evidence |
| REF-IMIS2-20261029 | 16 manual IMIS2 Web/Mobile trong thư mục tham khảo EVN do người dùng cung cấp | DOCX năm 2021; manifest SHA-256 và text extraction ngoài Git tại `.local/imis2_review/`; đọc chọn lọc toàn bộ 16 file | Hướng dẫn sử dụng EVN; tham khảo cấu trúc nghiệp vụ/UX, không phải quy chế, API, quyền hoặc dữ liệu Tấn Phát |
| REF-ERP-EXCEL-20261029 | 8 workbook nghiệp vụ trong thư mục ERP do người dùng cung cấp | Đọc cấu trúc/header/hướng dẫn và công thức/cache có giới hạn, gồm sheet ẩn; manifest/hash ở `.local/excel_reference_review/`; không chạy macro/link/recalculation | Quan sát nguồn và đề xuất thiết kế; không phải kiểm toán số tiền, phê duyệt kế toán hoặc nghiệm thu quyền/pilot |

Phân tích chọn lọc 16 manual và bản đồ adopt/adapt/defer/reject nằm tại [TP_IMIS2_REFERENCE_ANALYSIS.md](TP_IMIS2_REFERENCE_ANALYSIS.md). Tài liệu này giữ riêng ranh giới EVN–Tấn Phát; “Kho dữ liệu nhà thầu” trong IMIS2 là registry/master dữ liệu nhà thầu, không phải Data Lake.

Phân tích [Excel ERP tham khảo](TP_EXCEL_REFERENCE_ANALYSIS.md) bổ sung dòng tiền thực tế/dự kiến, khoản vay, snapshot theo kỳ, nhật ký append-only, đối chiếu PKH–KT và staging. XL05/PKH đã đổi hash so S03 BIZ-001; phải re-baseline phần bằng chứng phụ thuộc trước khi coi là biểu mẫu hiện hành. Số tiền thật và file tài khoản dùng thử không được lưu vào sổ này.

## 3. Bài học từ A1 Consulting và cách áp dụng

### 3.1 Điều có thể tiếp thu

A1 nêu các điểm đau thường gặp của doanh nghiệp xây dựng: chênh lệch dự toán–thực tế, tiến độ thay đổi, vật tư/thiết bị, kiểm soát nhà thầu, thay đổi/phê duyệt khó truy vết và thiếu góc nhìn dòng tiền. Các capability được giới thiệu gồm CRM/Sales, ngân sách theo dự án, giai đoạn/công việc, mua hàng/kho, nhà thầu–khối lượng–nghiệm thu–thanh toán, lịch sử phê duyệt, kế toán và báo cáo hiệu quả dự án.

Đối với TANPHAT ONE, các bài học phù hợp là:

1. **Project là trục liên kết:** cơ hội/hồ sơ → hợp đồng → dự án → công việc/phát sinh → nghiệm thu/chứng từ → báo cáo. Mỗi liên kết phải có company/project/assignment scope và provenance.
2. **Tách ba lớp kiểm soát:** kế hoạch hoặc cam kết; thực tế phát sinh; kết quả được kiểm chứng. Không cộng lẫn dự toán, sản lượng, nghiệm thu, invoice và tiền đã thu/chi.
3. **Theo dõi thay đổi:** revision, lý do, người thao tác, thời điểm, phiên bản và bằng chứng phải truy được; bản chốt không sửa đè.
4. **Tài chính là miền có quyền riêng:** xem/sửa hồ sơ không đồng nghĩa được xem số tiền. Kiến trúc dự kiến dùng Odoo Accounting làm nguồn posting/reconciliation; tích hợp TP, owner, cấu hình thuế/kỳ và nghiệm thu theo Q4/Q6 vẫn mở.
5. **Triển khai theo nút thắt:** không cài hoặc xây toàn bộ module chỉ vì danh sách tính năng. Chọn vertical slice có owner, dữ liệu giả/thật phù hợp và tiêu chí nghiệm thu.

Phạm vi sản phẩm đang chuẩn bị cho TANPHAT ONE có khảo sát, thiết kế và quản lý dự án cầu đường (REF-TP-DESIGN-20261029). Bài giới thiệu chung về nhà thầu xây dựng không đủ căn cứ để đưa mua hàng, kho công trường hay thiết bị vào scope trước các mảng đó. Chuỗi trên là bản đồ liên kết nghiệp vụ, không phải thứ tự bắt buộc tạo project sau hợp đồng.

### 3.2 Điều không được suy ra từ bài viết

- Bài viết không chứng minh các capability đều có trong Odoo Community 20 hoặc trong source hiện tại; một số phần có thể cần Enterprise/customization.
- `Sales`/quotation không thay thế miền hợp đồng xây dựng `tp_contract`; milestone invoice không phải nghiệm thu hay tiền đã thanh toán.
- `purchase_requisition` không mặc nhiên là Bid phía kinh doanh; HR employee không đồng nghĩa đủ payroll/chấm công/thiết bị.
- “Realtime”, “lợi nhuận” hay “dòng tiền” chỉ có ý nghĩa sau khi chốt công thức, kỳ, nguồn dữ liệu, phân bổ chi phí và quyền xem.
- Bài viết có đoạn nội dung không nhất quán khi gợi ý POS/E-Commerce/Inventory như điểm bắt đầu; không dùng đoạn đó để đổi roadmap.
- Phần case study động không cung cấp bằng chứng đủ để coi là kết quả triển khai của một doanh nghiệp cụ thể.

### 3.3 Đối chiếu với TANPHAT ONE

| Chủ đề | Hướng hiện hành | Trạng thái |
| --- | --- | --- |
| CRM/cơ hội | Có thể dùng CRM chuẩn làm nguồn opportunity; Bid là miền riêng nếu có quy trình mời thầu | CRM đã cài test/dev theo CHG-039/041; workflow TP chưa mở |
| Hợp đồng | `tp_contract` giữ revision, scope, BASE reference; quyền tiền dùng `tp.project.grant` theo user/project | CTR-001 đọc đã kiểm; CTR-002a test-only; business/pilot còn chờ |
| Project/công việc | Odoo project và addon TP làm trục scope; không tạo workflow engine tổng quát | Nền đã có; PRJ-002/TP Tasks chưa triển khai |
| Mua hàng/kho/nhà thầu | Chỉ mở khi hồ sơ Tấn Phát chứng minh nhu cầu và owner; không mặc định làm trước | Chưa có quyết định mở scope |
| Kế toán/dòng tiền | Dự kiến bridge tới `account.move`/payment của Odoo; request không tạo tiền | `account` đã cài; chưa cấu hình nghiệp vụ TP, chưa có nguồn posting/reconcile TP được nghiệm thu hay dữ liệu thật |
| BASE approval | BASE giữ phê duyệt chính thức; TANPHAT lưu hồ sơ, reference và kết quả xác minh | Đã xác nhận ở DEC-013; connector/API chưa kiểm chứng |

Ảnh chụp trạng thái theo CHG-039/041: `crm` và `account` đã cài test/dev; dev tự nạp chart VN, test dùng generic chart. Đây là cấu hình mặc định chưa được kế toán xác nhận, chưa có workflow/API/quyền TP cho CRM/kế toán hay dữ liệu CRM/kế toán thật. Sổ này chỉ đọc lại handoff, không audit lại database hoặc xác nhận production readiness.

## 4. Quan sát Base Request và giới hạn bằng chứng

### 4.1 Đã quan sát

Trang Base hiện hiển thị các ứng dụng Platform, XSpace, Message, Drive, Wework, Request và Account. Request có các nhóm như đề xuất trực tiếp, IT help desk, tạm ứng/thanh toán Tấn Phát, công tác, văn phòng phẩm, thiết bị, xe, biểu mẫu, công văn, phiếu giao việc, mượn dấu và nhóm thanh toán khác. Các tab gồm tất cả, chờ tôi duyệt, quá hạn, chờ xử lý, đã chấp nhận, từ chối, trả lại, đánh dấu và bản nháp.

Form nhóm **[Tấn Phát] Đề xuất tạm ứng, thanh toán** hiển thị tiêu đề bắt buộc, nhóm bắt buộc, nội dung, người duyệt cố định, người theo dõi, tệp đính kèm (giao diện ghi tối đa 10), cùng nút tạo và lưu nháp. Trong form đã mở không thấy trường có cấu trúc cho project/contract/amount; không được suy ra rằng các form khác cũng thiếu các trường này.

Chi tiết diễn giải actor, nhãn giao diện, vòng đời tham chiếu và các gap của Request được lưu tại [TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md](TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md). Tài liệu riêng giữ rõ giới hạn `observed-static` và không map nhãn BASE thành state Odoo.

Không có request hiển thị trong filter tài khoản được quan sát. Điều đó không chứng minh công ty không có hồ sơ. Không quan sát được đầy đủ lịch sử, thứ tự/quorum, hạn mức, ủy quyền, delegation, API/export/webhook hay bằng chứng pháp lý của người duyệt. Không thấy Bid trên trang home trong lần quan sát này, nhưng không thể kết luận toàn hệ thống không có Bid.

Các lần mở thêm nhóm/template ở tab mới bị chuyển về login không được tính là đã khảo sát được nội dung các template đó. Quan sát UI hiện có chưa đủ để chốt workflow Request hoặc cách chia addon.

### 4.2 Nguyên tắc đưa Base vào kiến trúc

Trong tài liệu này, **BASE** là dịch vụ bên ngoài đang được công ty dùng để phê duyệt. Nó không phải addon Odoo `base`, không phải model Request/Bid của Odoo và không phải bằng chứng rằng một cầu nối đã tồn tại.

- Base là **authority phê duyệt** theo DEC-013; TANPHAT không tạo approval song song để thay thế Base.
- Giai đoạn đầu dùng reference thủ công có ID/link, version hồ sơ, hash/evidence và trạng thái xác minh; chỉ xây connector khi API/export/webhook và owner được kiểm chứng.
- **Diễn giải Proposed-TP:** Request có thể là hồ sơ đề xuất liên phòng ban; không phải ledger và không biến thành invoice/cash. Miền chính vẫn nằm ở TP Finance/Tasks/Documents/Contracts; request chỉ liên kết bằng provenance. Chưa có request thực/API để xác minh actor, state hoặc mapping.
- Request và Bid là hai khái niệm: Request là đề nghị thực hiện/chi/việc; Bid là cơ hội hoặc gói thầu, phiên bản hồ sơ dự thầu, nộp và kết quả. Không dùng tên module đề xuất làm quyết định schema.

Các dòng UI trên là `observed-static` của một phiên/tài khoản/filter; không phải `runtime-evidence` của toàn công ty. Không có kết luận rằng Odoo đã có Request/Bid hoặc bridge BASE.

## 5. Nền kiến trúc và trạng thái cần giữ khi bàn giao

- Web React/TypeScript/Vite độc lập gọi API Odoo; Odoo giữ dữ liệu, quyền, state, audit và công thức.
- Một PostgreSQL database cho mỗi môi trường; các phòng dùng chung database và scope company/project/assignment.
- Giữ Odoo core/upstream nguyên vẹn; custom code ở `custom_addons/`.
- Dùng model chuẩn khi phù hợp; functional area và số addon không bắt buộc 1:1. Không tạo addon rỗng chỉ để đủ chín tên TP.
- Tên sản phẩm và phân hệ theo [`TP_PRODUCT_NAMING.md`](TP_PRODUCT_NAMING.md).
- Data Lake mới ở discovery/spec-only, recommendation `DEFER`; chưa có lake, analytics store, connector hoặc ingestion runtime. Không dùng Data Lake để thay nguồn sự thật Odoo hoặc che gap nghiệp vụ.
- Grant xem tiền tách khỏi quyền sửa/gửi; không suy quyền từ chức danh; chưa mở grant người dùng thật.

Các ma trận role/capability, KPI, DMS/lake, retention, import và workflow C07–C17 trong tài liệu khác vẫn là `proposed`/`unconfirmed` cho đến khi Q2–Q14 có owner, evidence và quyết định tương ứng. Không suy “lưu trữ tập trung” thành Data Lake.

Các gap chính đang mở gồm: Q1 thẩm quyền/hạn mức; Q2 owner và cấp/thu hồi grant; Q3 BASE ID/evidence; Q4 thuế, gross/net, currency và kỳ; Q6 feed kế toán/lịch đối chiếu; Q8 sửa/void sau thanh lý; Q11 retention/privacy; Q12 import/cutover; Q13 KPI/threshold/export; Q14 backup/RPO/RTO/incident. Đây là danh sách cần xác minh, không phải danh sách tính năng đã được duyệt.

Các nguyên tắc đã xác nhận và trạng thái/đề xuất phải giữ đúng nhãn riêng. Khi có khác biệt, đọc [`DECISIONS.md`](../DECISIONS.md) và [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) làm nguồn chính.

## 6. Đề xuất còn mở: Request và Bid

Đây là giả thuyết để làm discovery, chưa phải quyết định code:

Đọc lại workflow Request/Finance đã chuẩn bị trong [BIZ-002 F–M, mục H/I](TP_PROCESS_WORKFLOWS_F_M.md) và [tích hợp/KPI](TP_BIZ002_INTEGRATION_AND_REPORTING.md) trước khi thiết kế thêm. Không dựng miền/state/ledger song song chỉ vì có một giao diện Base mới được quan sát.

- Có thể bắt đầu bằng một `tp_request` lõi chứa loại yêu cầu, source/reference Base, company/project/department scope, owner, version, evidence và liên kết tới miền chính. Các màn hình Finance/Tasks/Documents/Procurement chỉ mở khi use case và owner cụ thể.
- `tp_bid` nên quản lý opportunity/tender package, phiên bản hồ sơ, deadline, người phụ trách, submission và outcome; có thể liên kết `crm.lead` và tạo draft project/contract reference, nhưng không tự làm hợp đồng hiệu lực hoặc thanh toán.
- Trước khi chốt schema cần thêm 2–3 hồ sơ khử dữ liệu, xác định owner, state/transition, quyền field/file, SLA, retention, mapping Base và test trả lại/sửa sai.

## 7. Việc còn mở và cách phiên AI tiếp tục

1. Đọc `PROJECT_STATUS.md` trước; **Next action hiện hành** là audit độc lập AUTH-002 slice 2 CHG-038 theo status hiện tại, không tự mở module mới.
2. Với BIZ-002, chờ Q2-A/Q2-B, owner, evidence và 2–3 bundle thực tế khử dữ liệu; mô phỏng không thay UAT.
3. Với Base, xác minh API/export/webhook, authority/evidence và chính sách version trước connector.
4. Với CRM/Account/Request/Bid, chọn từng vertical slice theo nhu cầu đã được owner xác nhận; không nhập dữ liệu thật hoặc bật approval/payment thật.
5. Với Data Platform, chọn use case/KPI/owner và decision riêng trước C17/RPT-001; không triển khai lake theo bài A1.

Mọi thay đổi application phải theo [`AI_CHANGE_WORKFLOW.md`](../AI_CHANGE_WORKFLOW.md) và [`AI_COORDINATION_WORKFLOW.md`](../AI_COORDINATION_WORKFLOW.md). Mỗi phiên mới cần báo cáo lại mục tiêu, bằng chứng và blocker; không dựa vào trí nhớ của chat.

## 8. Đọc sơ đồ kiến trúc TP.ONE trong PDF

### 8.1 Ý nghĩa tổng thể

Sơ đồ là một **target architecture** gồm hai lớp:

- **L1 / Frontend:** User → Web/Mobile → Dashboard → các workspace nghiệp vụ. “Mobile” mới là hướng mục tiêu; hiện đã xác nhận web React/TypeScript/Vite riêng, chưa chốt ứng dụng native hay responsive mobile riêng.
- **L2 / Backend:** Odoo 20 điều phối các miền CRM, nhân sự, hợp đồng, dự án (DA), kế toán, Request, Bid và AI; dữ liệu được lưu qua backend vào CSDL. Frontend không truy cập PostgreSQL trực tiếp.
- **API hai chiều:** được hiểu là frontend truy vấn DTO và gửi action tới API theo quyền. Nó không có nghĩa mọi action ghi/duyệt đã chạy, đồng bộ tự động với mọi hệ thống hay frontend được tự ghi state.
- **Căn cứ:** quy chế, sơ đồ tổ chức và phòng ban là nguồn để xác định scope, owner, quyền và workflow; không phải bảng dữ liệu tự do để frontend tự suy quyền.

Ví dụ **Dự án Quốc lộ 91** minh họa một dự án có đối tượng/quan hệ/flow và dẫn tới nhiệm vụ. Đây chỉ là ví dụ trên sơ đồ, chưa được coi là dữ liệu runtime hay hồ sơ để import.

### 8.2 Đối chiếu nhãn trên sơ đồ với TANPHAT ONE

| Nhãn PDF | Cách hiểu trong TANPHAT ONE | Trạng thái |
| --- | --- | --- |
| Dashboard | TP Dashboard, lớp tổng hợp theo scope/quyền | Tên đã chốt; reporting đầy đủ chưa triển khai |
| Projects / Dự án | TP Projects, `tp_project` và `project.project` làm trục liên kết | Nền đã có; không khẳng định mọi miền đã gắn đầy đủ |
| Đấu thầu / BID | Miền đấu thầu (`tp_bid` dự kiến), mở rộng `crm.lead` bằng gói thầu, phiên bản, nộp và kết quả | Đề xuất; chưa có workflow runtime; không tự bổ sung tên phân hệ thứ mười |
| QL HĐ / Hợp đồng | TP Contracts, `tp_contract` với revision, scope và BASE reference | CTR-001 read đã kiểm; CTR-002a test-only; pilot/business còn chờ |
| Khảo sát | TP Survey | Tên đã chốt; chưa triển khai vertical slice |
| Thiết kế | TP Design | Tên đã chốt; chưa triển khai vertical slice |
| Thầu phụ | Liên kết hợp đồng thầu phụ và purchase bridge khi nghiệp vụ cần | Không tự tạo module/PO từ ô trên sơ đồ |
| Khoán | `tp_allocation` cho giao khoán nội bộ/cấp 1–2 | Thiết kế mục tiêu; chưa triển khai |
| Thanh toán | TP Finance / `tp_settlement` và bridge Account sau khi Q4/Q6/owner đủ căn cứ | `account` đã cài; workflow TP và nguồn posting/reconcile chưa nghiệm thu |
| Nghiệm thu | TP settlement/acceptance, tách khỏi sản lượng, invoice và cash | Thiết kế BIZ-002; chưa triển khai |
| Nhiệm vụ | TP Tasks, dựa trên `project.task`, liên kết project và assignment | Odoo nền có task; TP workflow mở theo slice riêng |
| CRM / Nhân sự / Kế toán | Model Odoo chuẩn có thể tái sử dụng | Đã có nền module theo status; không đồng nghĩa nghiệp vụ TP đã chốt |
| Request / AI | Request là record/reference theo thiết kế; AI là lớp hỗ trợ có kiểm soát | Request/Bid/AI chưa phải bridge hoặc engine đã nghiệm thu; AI use case đang defer |
| CSDL | PostgreSQL và filestore theo từng môi trường | Đã có dev/test; không cho frontend truy cập trực tiếp |

### 8.3 Điều sơ đồ chưa đủ để chốt

Sơ đồ chưa xác định dashboard có bắt buộc là menu cha của Projects; “Đối tượng/Relation/Flow” là metadata, ERD hay workflow engine; cardinality; actor/capability; transition/guard; granularity của task; policy field/file/export; authentication; hoặc mapping một workspace frontend với một addon Odoo. Không biến sơ đồ thành workflow engine tổng quát hay bảng giao dịch dùng chung.

BASE vẫn là nơi phê duyệt chính thức theo DEC-013. Request trong Odoo/TANPHAT chỉ được lưu reference/kết quả khi có task và mapping được duyệt; `approved` không đồng nghĩa ký, hiệu lực, nghiệm thu, invoice hoặc paid/cash.

### 8.4 Kết luận điều phối

Sơ đồ phù hợp với hướng nền hiện tại: **Dự án là trục nhìn tổng thể; frontend riêng là nơi thao tác; Odoo 20 là nơi thi hành nghiệp vụ; PostgreSQL/filestore là nền lưu trữ; API là ranh giới bảo mật.** Các ô nghiệp vụ là phạm vi mục tiêu, phải mở theo vertical slice có owner, dữ liệu, capability, state, API và ca nghiệm thu; không coi hình là bằng chứng module đã cài hoặc quy trình đã được công ty phê duyệt.

