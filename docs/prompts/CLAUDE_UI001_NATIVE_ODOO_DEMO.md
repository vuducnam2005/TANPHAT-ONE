# Prompt Claude — UI-DEMO-001: khung trình diễn toàn hệ thống bằng giao diện Odoo

Người dùng xác nhận ngày 30/10/2026: dựng **native Odoo để demo trước**, phạm vi **khung toàn hệ thống** cho lãnh đạo xem. Quyết định DEC-024 chỉ mở bản trình diễn với dữ liệu giả trên môi trường riêng; kiến trúc sản phẩm React + API Odoo theo DEC-001/023 giữ nguyên.

Copy phần trong khối dưới đây vào Claude. Đây là prompt triển khai, không phải yêu cầu chỉ lập thêm kế hoạch.

```text
Làm việc trong C:\TANPHAT ONE.
Task: UI-DEMO-001 — Dựng giao diện trình diễn TANPHAT ONE ngay trong Odoo, khung toàn hệ thống để lãnh đạo xem.
Chọn CHG-YYYYMMDD-NNN mới chưa dùng theo ngày thực hiện. Không commit/push/deploy.

1. Mục tiêu và quyền triển khai

Người dùng đã chọn native Odoo để demo trước và khung toàn hệ thống. Hãy triển khai, chạy thử và bàn giao bản demo mở được trên trình duyệt; không dừng ở báo cáo phân tích hoặc mockup ảnh.

Lãnh đạo cần nhìn thấy:
- TANPHAT ONE quản lý những mảng nào, giao diện thống nhất ra sao.
- Dự án liên kết cơ hội, hợp đồng, công việc và hồ sơ như thế nào.
- Các phòng ban dùng chung nền nhưng có workspace/menu/dữ liệu theo quyền.
- Phần nào dùng được từ Odoo/source hiện tại; phần nào mới là minh họa định hướng.

Đây là demo trên môi trường riêng, dữ liệu giả, ưu tiên xem và điều hướng. Không triển khai toàn bộ nghiệp vụ thật chỉ để làm demo. Không thay frontend React chính thức, API hiện hành, quyền người thật hoặc các cổng nghiệp vụ đang mở.
DEC-024 là căn cứ mở scope demo; không yêu cầu người dùng xác nhận lại lựa chọn này.

2. Đọc source và preflight

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/AI_COORDINATION_WORKFLOW.md, docs/CHANGELOG.md, docs/ROADMAP.md, docs/DECISIONS.md; sau đó:
- docs/architecture/TP_PRODUCT_NAMING.md
- docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md
- docs/architecture/TP_ODOO20_MODULE_INVENTORY.md
- docs/architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md
- docs/architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md
- docs/architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md
- docs/architecture/TP_REFERENCE_RESEARCH_AND_HANDOFF.md
- docs/architecture/TP_IMIS2_REFERENCE_ANALYSIS.md
- scripts/dev.py, ops/runbooks/LOCAL_DEVELOPMENT.md và manifest/security/model hiện có liên quan.

Áp dụng skill frontend-design nếu có; trên máy hiện tại: C:\Users\vuduc\.codex\skills\frontend-design\SKILL.md. Nếu đường dẫn khác, tìm skill tương ứng và báo nguồn đã dùng. Đọc skills/odoo-web-guidelines/SKILL.md và các hướng dẫn JS/SCSS/assets liên quan; đọc skills/odoo-guidelines/SKILL.md và skills/odoo-security/SKILL.md cho phần backend/security.

Kiểm tra git status/diff, ai_workflow.py check, checkpoint, phiên bản Odoo, module thực có, runtime/port và DB đích. Không reset/clean/stash hoặc ghi đè thay đổi có sẵn. Nếu checkpoint của batch khác chưa bàn giao thì báo xung đột, không finish thay. Nếu source khác handoff phải xác định trước khi sửa.

AUTH-002 slice 2 còn chờ audit không tự trở thành đã nghiệm thu. Demo dùng luồng đăng nhập native sẵn có; không sửa AUTH-002, không tự cài tp_web_login để xử lý login trong batch này. Các cổng Q2/owner/evidence vẫn chặn người dùng thật và nghiệp vụ tương ứng; không chặn màn hình minh họa bằng dữ liệu giả thuộc DEC-024.

Khi preflight đạt, chạy .\.venv\Scripts\python.exe scripts\ai_workflow.py start trước lần sửa đầu tiên.

3. Môi trường trình diễn

- Database mới riêng, tên gợi ý tp_tanphat_demo_ui001, config/data-dir/filestore/HTTP port riêng dưới .local/ui-demo-001/.
- Chỉ bind localhost mặc định; bàn giao URL mở trên máy này. Không tự xuất bản ra Internet hoặc mở firewall.
- Kiểm tra DB/port đã tồn tại và ownership trước khi dùng. Không drop/reset DB, không ghi đè môi trường không sở hữu, không kill process khác.
- Có thể dùng PostgreSQL local hiện có nếu đã nhận diện đúng; chỉ tạo/sửa DB demo. Nếu cluster chưa chạy, dùng cách khởi động đã có sau khi kiểm ownership; không chạy scripts/dev.py setup/upgrade để bootstrap demo.
- Khởi tạo DB từ source, không clone/import database dev hay hồ sơ thật. Chọn module/dependency thật sự cần, không cài mọi module trong checkout.
- Không cài/upgrade/seed tp_tanphat_dev, tp_tanphat_test hoặc thay MODULES trong scripts/dev.py chỉ để demo.
- Tắt cron và mọi gửi email/SMS/payment/webhook ra ngoài trên demo; không kết nối BASE thật.
- Dùng fixture giả riêng, tên/mã có dấu hiệu DEMO; chuẩn bị 2–3 dự án cầu đường giả, đối tác giả, nhân sự giả, task, hợp đồng và tệp giả. Dữ liệu liên quan phải nhất quán.
- Fixture có thể chạy lại mà không tạo trùng; không đổi mật khẩu dev/test. Credential sinh riêng và chỉ lưu local ignored; không in mật khẩu/cookie vào log hoặc đưa vào Git.
- Tool prepare/start/status/stop có target/ownership guard; chỉ dừng đúng Odoo process do tool tạo. Không tự mở thêm C01/FND-002 hoặc refactor toàn bộ tooling.

4. Tổ chức source

Tạo một addon trình diễn có nội dung thực, ví dụ custom_addons/tp_demo_workspace/:
- Manifest, menu/action, security và native views thực sự dùng.
- OWL client action cho trang tổng quan và màn hình minh họa khi cần.
- JS/XML/SCSS tổ chức theo tính năng; dùng asset bundle Odoo chuẩn.
- Dịch/nhãn tiếng Việt dễ hiểu.
- README hướng dẫn chạy và bảng màn hình thật/minh họa.

Được thêm tooling demo tối thiểu trong scripts/, runbook trong ops/runbooks/, test và tài liệu bàn giao cần thiết.
Không sửa odoo/, addons/, frontend/React, OpenAPI hoặc logic workflow/quyền trong addon TP hiện có. Nếu gặp thiếu native view, thêm view trong addon demo, tham chiếu model canonical; không nhân bản model nghiệp vụ.

Giữ Odoo web client/session/navigation. Không iframe một website khác, không tạo login thứ hai, không thay toàn bộ webclient. Có thể có navigation trong client action demo; mở native action bằng action service và có đường quay về tổng quan.

Native Odoo được đọc qua ORM/view/action chuẩn với quyền người hiện tại. Đây là tích hợp native, không phải React gọi generic RPC bỏ qua API. Không dùng RPC, sudo hoặc direct state write để né workflow/protected fields. Không tạo API công khai mới nếu không cần.

5. Thiết kế trước khi code UI

Tạo docs/architecture/TP_UI_DEMO_001_SPEC.md ngắn gọn, đủ để đối chiếu:
- Sơ đồ menu/workspace và luồng demo.
- Mỗi màn hình: mục tiêu, actor, nguồn dữ liệu, là chức năng thật hay minh họa, trạng thái loading/empty/error/denied.
- Những field/số liệu/tệp nào yêu cầu grant tiền.
- Bảng màu 4–6 màu, font hỗ trợ tiếng Việt, spacing và wireframe.

Tự rà lại thiết kế theo skill rồi triển khai tiếp, không chờ thêm phê duyệt cho lựa chọn màu/layout thường lệ. Ưu tiên phong cách điều hành doanh nghiệp xây dựng: dễ đọc, bố cục gọn, bảng dữ liệu rõ, xanh đậm/xanh kỹ thuật phối nền sáng nếu phù hợp thương hiệu đang có. Tái sử dụng logo/asset có sẵn, không bịa logo pháp nhân.

Một shell dùng chung, workspace thay đổi theo tài khoản/assignment. Chuyển workspace không được nâng quyền; không tạo một app/addon riêng cho từng phòng. Dropdown nếu chỉ đổi bố cục thì không được giả lập việc đổi vai trò bảo mật.

Hover/focus rõ; animation ngắn cho mở/đóng/chuyển nội dung, tôn trọng prefers-reduced-motion. Không dùng animation liên tục hoặc hiệu ứng làm chậm xem số liệu. Font/asset ưu tiên local, không phụ thuộc CDN để chạy demo. CSS chỉ áp dụng trong namespace addon, không ghi đè giao diện Odoo toàn cục.

6. Phạm vi màn hình bắt buộc

Giữ chín tên phân hệ đã chốt; CRM/Request/Bid là mục bổ sung để giới thiệu, không đổi tên sản phẩm hoặc tự coi chúng đã được nghiệm thu nghiệp vụ.

A. TP Dashboard
- Trang vào sau khi mở ứng dụng TANPHAT ONE – Demo.
- Tổng quan dự án, công việc, hồ sơ hợp đồng và các việc cần chú ý.
- Một phần trực quan cho thấy các hồ sơ liên quan theo dự án. Quan hệ dữ liệu không tự trở thành trình tự duyệt bắt buộc.
- Chỉ số tính từ dữ liệu fixture đúng scope; click vào chỉ số mở danh sách cùng bộ lọc. Không hardcode KPI hoạt động thật; KPI định hướng phải ghi rõ minh họa.

B. TP Projects
- List/kanban và chi tiết dự án giả từ project.project/tp_project hiện có.
- Thể hiện mã, khách hàng, phòng chủ trì, người được giao, công việc và hợp đồng liên quan nếu nguồn hỗ trợ.
- Trang tổng quan dự án giữ ngữ cảnh dự án đang xem.
- Không tự thêm lifecycle/state, công thức tiến độ hoặc liên kết chưa có; phần đề xuất để trong màn hình minh họa.

C. TP Survey
- Màn hình minh họa kế hoạch khảo sát, vị trí/hạng mục, nhân sự/thiết bị, nhật ký và hồ sơ kết quả.
- Có danh sách mẫu và mở chi tiết mẫu; không chỉ là ô Coming soon.
- Không cài survey rồi gọi đó là khảo sát hiện trường. Không tạo workflow khảo sát thật.

D. TP Design
- Màn hình minh họa danh sách hồ sơ/bản vẽ, revision, phản hồi rà soát và gói bàn giao.
- Có xem bản mẫu và lịch sử minh họa; không sinh phê duyệt/chữ ký/hiệu lực thật.

E. TP Contracts
- List/detail read-only trên tp.contract, revision và các model hiện có.
- Xem mã, dự án, đối tác, phạm vi, lịch sử gửi/trả lại và tệp giả theo quyền.
- Các trạng thái review nằm đúng model/field đã có. Không nhầm review state của revision với lifecycle của contract.
- Ưu tiên fixture draft/in_review/returned tạo đúng cơ chế hiện có; không ghi state trái workflow để dựng ảnh.
- Batch demo không thêm nút ghi/duyệt hoặc mở rộng CTR-002a. Thể hiện luồng draft → rà soát → trả lại bằng sơ đồ và dữ liệu đọc; hành vi sửa/gửi thật để slice riêng.

F. TP Tasks
- List/kanban/chi tiết task giả bằng project.task và tính năng Odoo thật có.
- Người được giao, hạn, nhóm/giai đoạn công việc; timesheet nếu fixture và scope đã được kiểm.
- Không dùng Gantt/Planning Enterprise hoặc thư viện thương mại khi source hiện tại không có.

G. TP HR
- Danh bạ nhân sự/phòng ban giả; chỉ field thích hợp với quyền demo.
- Dùng hr.employee.public hoặc nguồn đã giới hạn thay vì cấp HR Manager cho mọi người chỉ để mở trang.
- Có phần định hướng năng lực/phân bổ nếu chưa có source, gắn nhãn minh họa. Không làm payroll.

H. TP Finance
- Giới thiệu nguồn chi phí/time expense có thật và khả năng xem tổng hợp theo project khi đúng scope.
- account đã cài không có nghĩa TP Finance bridge hoàn chỉnh. Không tạo/hạch toán invoice, payment, bút toán posted hoặc đối soát chỉ để có số trên dashboard.
- Phân biệt giá trị hợp đồng, giá trị nghiệm thu và tiền thu/chi. Không cộng số khác tiền tệ hoặc dựng lợi nhuận khi thiếu công thức.
- Nếu chưa có nguồn/công thức đã chốt, hiển thị màn hình định hướng với số giả có nhãn minh họa, chỉ trả về tài khoản demo được grant. Không mô tả số minh họa là KPI đã triển khai.

I. TP Documents
- Xem tệp giả gắn hồ sơ hiện có, ví dụ tp.contract.document, đúng policy general/financial.
- Cây hồ sơ toàn dự án, quản lý revision ngoài chức năng hiện có là phần minh họa.
- Không mở danh sách ir.attachment chung hoặc tạo DMS đầy đủ trong batch này.

J. CRM
- Dùng crm.lead và pipeline giả; mở chi tiết cơ hội/khách hàng bằng khả năng Odoo hiện có.
- Không tự mở liên kết CRM → Bid → ký hợp đồng hoặc thêm field nghiệp vụ vào model nền nếu chưa có đặc tả.

K. Request
- Màn hình minh họa danh sách đề nghị, form mẫu và tiến trình xử lý theo kiến thức BASE đã ghi.
- BASE vẫn là nơi phê duyệt chính thức. Nhãn tiến trình là minh họa, không giả định tab UI BASE là state API.
- Không có nút phê duyệt thật, connector BASE, ký hoặc chi tiền. Link BASE nếu có chỉ là điều hướng, không chứa token/credential.

L. Bid
- Màn hình minh họa cơ hội/gói thầu, hạn nộp, hồ sơ dự thầu, liên danh, kết quả dự kiến.
- Định hướng phù hợp Tấn Phát đi dự thầu/tư vấn; không mặc định Tấn Phát là chủ đầu tư như EVN.
- Không cài purchase_requisition rồi coi là TP Bid; không tự tạo hợp đồng hiệu lực khi có kết quả trúng mẫu.

Các màn hình minh họa phải xem danh sách, mở chi tiết mẫu, lọc/chọn dự án trong phạm vi minh họa; nút chưa có xử lý không được giả báo thành công. Dùng nhãn ngắn “Minh họa định hướng” trên chính màn hình. Toàn môi trường có nhãn “Dữ liệu trình diễn”. Bảng khả năng chi tiết để trong README và tài liệu demo.

7. Dữ liệu, quyền và giới hạn

- Bộ dữ liệu liên kết 2–3 dự án giả, khoảng 8–12 cơ hội, 3–5 hợp đồng và 15–25 task; số nhân sự/hồ sơ mẫu vừa đủ kể câu chuyện. Không tạo hàng trăm bản ghi không cần thiết.
- Tài khoản trình diễn không dùng admin/superuser: tối thiểu một tài khoản tổng quan có assignment/grant rõ cho dự án giả, một tài khoản chỉ xem dự án được giao và không có financial_read.
- Tên vai trò demo không phải bổ nhiệm thật. Seeder được tạo grant fixture theo policy hiện có trong DB demo; không mở UI quản trị grant hoặc cấp quyền cho người thật.
- Native view/read_group/search/export/chatter/file đều giữ company/project/assignment/financial policy. Không chỉ ẩn nút/field ở UI hoặc lọc JS. Không cấp nhóm quản trị module rộng chỉ để hết AccessError.
- Không thay ACL/rules/model hiện có. Nếu standard view đòi quyền quá rộng hoặc không an toàn, dùng projection đọc trong addon demo với kiểm group/scope/grant ở backend và DTO field allowlist; không sudo để gom dữ liệu. Không tạo bản sao canonical của project/contract/employee/partner.
- Phần minh họa có thể dùng fixture chỉ đọc phía server, không tạo hàng loạt model nghiệp vụ rỗng. Dữ liệu tiền/tệp hạn chế không đặt trong static JS, HTML hoặc JSON asset tải cho mọi tài khoản; backend kiểm trước khi trả, kể cả mock data.
- Tài khoản không có grant không thấy tiền/tệp tài chính trong response, biểu đồ, tổng, tooltip, export hoặc tải trực tiếp. Tổng và drilldown phải có cùng phạm vi, không tính từ record ngoài quyền.
- Chế độ xem chỉ đọc phải được đảm bảo ở backend cho dữ liệu demo được phục vụ; không gọi form readonly là biện pháp bảo mật. Nếu nhóm chuẩn Odoo làm phát sinh quyền ghi quá rộng, chuyển sang read projection hoặc thiết kế demo actor khác thay vì nới scope.
- Fixture tệp tạo tại local, tên giả, nội dung giả; tải file qua cơ chế đã kiểm quyền. Không đưa dữ liệu NAS/Excel EVN/Tấn Phát vào runtime hoặc Git.
- Không sửa/chạy phê duyệt BASE, ký, hiệu lực, giao khoán, nghiệm thu, thanh toán, Data Lake, tích hợp ngoài hoặc grant người thật.

8. Triển khai theo thứ tự và tự kiểm

Thực hiện liên tục: spec ngắn → addon/menu/common workspace → màn hình thật read-only → màn hình minh họa → fixture + runtime → test + chụp ảnh → sửa lỗi → bàn giao.

Không làm riêng React trong task này, không cài Enterprise hoặc mua theme. Nếu một phần cần nghiệp vụ chưa chốt, giữ ở mức minh họa và hoàn thành phần độc lập; không lấy gap đó làm lý do dừng toàn bộ bản demo.

9. Kiểm thử phải chạy thật

- Install và upgrade chính addon demo trên DB cô lập; assets compile, XML/view/action hợp lệ, không missing external ID.
- Tool từ chối DB dev/test, wrong target/foreign ownership, port conflict; seed hai lần không trùng, stop chỉ đúng process.
- Odoo tests cho read service/projection và scope thực có: đúng assignment/company, sai project/company, không grant tiền, tài khoản thường; native ORM/read_group/export/direct file có ca âm tương ứng nếu được mở.
- Rà quyền ghi trực tiếp bằng actor demo, không chỉ kiểm nút bị ẩn; không sửa nghiệp vụ thật để vượt test.
- UI tests bằng browser thật: login demo, mở dashboard, đi vào đủ các menu, lọc/mở dự án và hợp đồng, quay lại tổng quan, kiểm tài khoản không tiền và direct URL/file. Mock E2E không thay live Odoo.
- Kiểm desktop 1440x900 và laptop 1366x768; responsive nhỏ hơn không tràn toàn trang, bảng có scroll thích hợp, keyboard/focus/reduced-motion dùng được. Không lỗi console/network không giải thích được.
- Chụp và tự xem tối thiểu dashboard, dự án, hợp đồng, một màn hình minh họa và màn hình người không có quyền tiền. Sửa layout sau khi xem ảnh.
- Ruff cho Python mới, test JS/OWL thích hợp theo tooling thực tế của checkout; frontend React typecheck/build chỉ khi thật sự bị ảnh hưởng, không chạy để thay test native assets.
- Chạy regression TP liên quan trong DB test demo riêng nếu dependency/seed/view chạm đường đọc đó. Báo test count, pass/fail/skip, DB đích và log; không nhận exit 0 là đủ nếu test thực bị skip.

10. Bàn giao

Tạo/cập nhật:
- docs/architecture/TP_UI_DEMO_001_SPEC.md: spec và mapping thật/minh họa, actor/scope, kết quả kiểm.
- ops/runbooks/UI_DEMO_001.md: prepare/start/status/stop, DB/port/URL, credential file local, lưu ý mở bản demo đúng môi trường.
- docs/demo/UI_DEMO_001_PRESENTATION.md: kịch bản trình bày 5–7 phút, thứ tự click và điều người thuyết trình cần nói; tách hiện trạng tính năng với định hướng.
- README addon; docs/PROJECT_STATUS.md, docs/CHANGELOG.md và docs/ROADMAP.md đúng tiến độ.
- DECISIONS chỉ khi có quyết định mới từ người dùng; DEC-024 không cho tự thay DEC-001/013/017/023.

Ảnh, trace, credential và log runtime để .local/ui-demo-001/ ignored. Giữ source/fixture generator/runbook không secret trong Git. Không thêm ảnh chụp có dữ liệu thật.

Chạy git diff --check; scripts/ai_workflow.py finish --change-id CHG-ID-moi --check với lệnh/kết quả thực và scripts/ai_workflow.py check. Không finish thay batch khác hoặc tự ghi TECHNICAL_ACCEPTED; giao kết quả IMPLEMENTED_PENDING_AUDIT cho phiên điều phối kiểm lại.

Báo cáo cuối phải có:
1) URL mở bản demo và cách lấy tài khoản từ file local, không dán mật khẩu.
2) Ảnh các màn hình chính và đường dẫn runbook/kịch bản trình bày.
3) Bảng mỗi phân hệ: dùng thật từ model nào / phần minh họa / giới hạn.
4) Test đã chạy, kết quả, target và kiểm quyền âm.
5) Xác nhận dev/test/React và các chức năng ngoài phạm vi không bị thay đổi.
6) Runtime demo đang chạy hay đã dừng, lệnh mở lại rõ ràng. Nếu được chạy, giữ demo Odoo local sẵn để người dùng xem và bàn giao ownership; không để service phụ không rõ chủ.
7) Gap còn lại và Next action là phiên điều phối audit demo trước khi trình lãnh đạo; AUTH-002 audit vẫn là việc tồn đọng riêng.

Không commit/push, không triển khai production, không mở quyền người dùng thật.
```
