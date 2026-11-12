# Kiến trúc nền tảng TANPHAT ONE

Ngày thiết kế và triển khai nền: 28/10/2026, Asia/Saigon. Tài liệu ghi ranh giới kiến trúc và lộ trình; các module nghiệp vụ tương lai được phân biệt với nền đã chạy.

**Trạng thái hiện tại:** đã có addon nền, database dev/test, API đọc dự án và frontend React/TypeScript/Vite tại `/work/`; CTR-001 có TP Contracts read slice; CTR-002a/2a.1 có draft → submit → return → rework → resubmit và technical acceptance trên test fixture. Dashboard cũ nằm trong `frontend/prototype/`. Đã kiểm thử login native, scope, logout CSRF, session hết hạn, validation, self-review, live workflow và race/replay. Xem [hướng dẫn chạy nền](../../ops/runbooks/LOCAL_DEVELOPMENT.md), [thiết kế database](TP_DATABASE_DESIGN.md), [bộ thiết kế BIZ-002](TP_BIZ002_DESIGN_PACKAGE.md) và [kế hoạch điều phối code](TP_CODE_EXECUTION_MASTER_PLAN.md). Action BASE/ký/hiệu lực, nghiệm thu, import dữ liệu thật và production vẫn là giai đoạn sau.

## 1. Hướng đã xác nhận và kiến trúc đề xuất

**Cập nhật có hiệu lực 05/11/2026 — DEC-030:** giao diện chính phát triển trong Odoo, ưu tiên view/action chuẩn và bổ sung OWL/QWeb/SCSS trong custom addon. Hướng React/TypeScript/Vite riêng trước đây được thay thế; source/API/test cũ được giữ cho tương thích và hồi quy. Xem [hiện trạng và kế hoạch chuyển giao diện](TP_NATIVE_ODOO_DIRECTION.md). Backend vẫn tổ chức thành các addon nghiệp vụ dùng chung một nền Odoo. Các addon tương lai dưới đây là thiết kế, chưa phải danh sách đã cài.

Theo DEC-023 và DEC-030, dùng một nền giao diện Odoo chung; mỗi phòng có workspace, menu, dashboard, trường và nút theo vai trò/quyền. Đặc tả view/action theo từng domain và owner; backend vẫn enforce quyền. Không nhân bản addon/model theo phòng ban chỉ vì màn hình khác nhau.

```text
Browser
  |
  | same HTTPS origin qua reverse proxy
  v
Odoo native: Home + view/action chuẩn + OWL/QWeb/SCSS
  |
  | session Odoo; gọi action/model có kiểm quyền
  v
Odoo domain actions + security + ORM; API giữ cho tích hợp
  |
  +-- Odoo chuẩn: CRM, Project, Sale, Purchase, Account, Analytic, HR, Mail
  +-- Addon Tấn Phát: tổ chức, dự án, hợp đồng, giao khoán, nghiệm thu, báo cáo
  |
  v
PostgreSQL + filestore; adapter NAS/DMS khi được thiết kế
```

Odoo là nguồn sự thật cho dữ liệu, tính tiền, trạng thái, lịch sử và phân quyền. Native UI gọi model/action đã kiểm quyền; không ghi trực tiếp state hoặc bỏ guard workflow bằng RPC. API ngoài giao diện native vẫn theo DTO/OpenAPI. Không đưa quyết định tài chính, quyền hoặc hiệu lực giao dịch vào JavaScript.

Không sửa `odoo/` hoặc `addons/`. Mọi code riêng đặt trong `custom_addons/`. Repository hiện là Odoo 20.0, vì vậy manifest, ORM, route và security phải bám source phiên bản này.

Tận dụng form/list/search và session Odoo để giảm phần giao diện phải xây riêng; Home/dashboard/mobile đã có tùy biến native. Hợp đồng có backend/test và UI React cũ; CHG-20261106-002 thêm `tp_contract_native.py`, XML view/menu và transient adapter trong addon `tp_contract`, gọi sáu action có sẵn bằng user hiện tại. Chỉ upgrade owned clone18169, đã tự kiểm Odoo107/browser42, chờ audit implementation, chưa áp dev. [Bàn giao](../reviews/UI_CTR_NATIVE_001A_IMPLEMENTATION.md). Không cần backend Node, microservices hoặc hệ đăng nhập thứ hai cho hướng này.

## 2. Cấu trúc source mục tiêu

```text
C:\TANPHAT ONE\
├── odoo/                         # framework upstream, giữ nguyên
├── addons/                       # addon chuẩn upstream, giữ nguyên
├── custom_addons/                # addon riêng, tạo tăng dần theo vertical slice
│   ├── tp_core/                  # catalog, reference, cấu hình chung
│   ├── tp_organization/          # mở rộng hr.department và phân công
│   ├── tp_project/               # mở rộng project.project/task, WBS
│   ├── tp_bid/                   # cơ hội/gói thầu, làm sau nền dự án
│   ├── tp_contract/              # hợp đồng pháp lý và phụ lục
│   ├── tp_allocation/            # giao việc/giao khoán nội bộ cấp 1, cấp 2
│   ├── tp_settlement/            # sản lượng, nghiệm thu, đề nghị thanh toán
│   ├── tp_reporting/             # read service và aggregate có kiểm quyền
│   ├── tp_api/                   # transport/session/error/pagination dùng chung
│   ├── tp_planning_api/          # endpoint của workspace Kế hoạch Kinh doanh
│   ├── tp_documents/             # metadata/version attachment, làm sau
│   ├── tp_import/                # staging Excel, mapping, quarantine, làm sau
│   ├── tp_account_bridge/        # nối Account/Analytic, làm sau đối chiếu
│   ├── tp_sale_bridge/           # nối hợp đồng với Sale khi nghiệp vụ cần
│   └── tp_purchase_bridge/       # nối hợp đồng thầu phụ với Purchase khi cần
├── frontend/                     # React legacy; giữ source/test, không là FE chính
├── contracts/openapi/            # tanphat-v1.yaml khi endpoint đầu tiên có thật
├── docs/
│   ├── architecture/             # quyết định kiến trúc và quy tắc phát triển
│   ├── business/                 # từ điển dữ liệu, vòng đời, quyền, owner KPI
│   ├── migration/                # mapping và quy trình đối chiếu; không file mật
│   └── dashboard/                # khảo sát/prototype cũ để tham khảo
├── scripts/                      # công cụ offline/check/import, không chứa dữ liệu mật
├── ops/
│   ├── config/                   # cấu hình mẫu, secrets ngoài Git
│   ├── proxy/                    # routing cùng origin
│   └── runbooks/                 # deploy, nâng cấp, backup/restore
└── .github/workflows/            # CI của custom addon/frontend khi triển khai
```

Đây là cấu trúc mục tiêu, không phải danh sách phải tạo ngay. Chỉ tạo addon khi có mô hình và ca sử dụng thật; không tạo 15 thư mục rỗng để giả lập microservices. Không chuyển `odoo/` và `addons/` vào thư mục `backend/` chỉ để đẹp cây source.

Giao diện chính đặt cùng addon nghiệp vụ trong `views/` và `static/src/`; Home/dashboard hiện ở `tp_web_home`/`tp_dashboard_privacy`. React trong `frontend/src/` và prototype trong `frontend/prototype/` được giữ; không tự xóa route/test hoặc đổi runtime. Secrets, `node_modules`, dist và kết quả browser vẫn ngoài Git.

## 3. Tái sử dụng Odoo và phần phát triển riêng

| Nhu cầu | Dùng Odoo chuẩn | Phần Tấn Phát |
| --- | --- | --- |
| Công ty, người dùng, đối tác | `res.company`, `res.users`, `res.partner` | chỉ bổ sung mã/thuộc tính cần thiết |
| Phòng ban | `hr.department` | `tp_organization` mở rộng và phân công có thời hạn |
| Cơ hội | `crm.lead` | `tp_bid` bổ sung gói thầu và bước riêng |
| Dự án/công việc | `project.project`, `project.task`, analytic | `tp_project` thêm mã, WBS, vai trò và liên kết nghiệp vụ |
| Bán hàng/mua hàng/kế toán | `sale`, `purchase`, `account`, `analytic` | bridge và đối chiếu, không chép lại sổ kế toán |
| Hợp đồng doanh nghiệp | chưa đủ khái niệm hồ sơ/phụ lục Tấn Phát | `tp_contract` |
| Giao khoán nội bộ | không dùng sale/purchase để giả lập | `tp_allocation` |
| Sản lượng/nghiệm thu/thanh toán dự án | native accounting chỉ bao phủ phần kế toán | `tp_settlement`, sau đó link bằng bridge |

Phân module theo **nghiệp vụ và nguồn dữ liệu**, không tạo một module riêng cho mỗi phòng ban. Phòng ban được biểu diễn bằng workspace, menu, role và phạm vi dữ liệu; các feature dự án/hợp đồng/nghiệm thu có thể được nhiều phòng dùng với quyền khác nhau. Cấu hình workspace không thay thế ma trận capability × scope × state ở backend.

## 4. Ranh giới addon backend

### `tp_core` và `tp_organization`

`tp_core` giữ catalog hạng mục `tp.work.item`, alias được duyệt và cấu hình chung. Nó không giữ toàn bộ workflow hoặc tiền của hệ thống. Mã dự án thuộc `tp_project`; binding từ dòng nguồn sang bản ghi nghiệp vụ thuộc `tp_import`. Đối tác dùng `res.partner`; tài khoản truy cập dùng `res.users`, hồ sơ nhân viên dùng `hr.employee` khi cần. Không sao chép các model này sang bộ bảng riêng.

`tp_organization` phụ thuộc `hr` và `tp_core`, mở rộng `hr.department` và phân công vào đơn vị có thời hạn. HR-001 bổ sung mã TP/source metadata trên `hr.employee`, cờ xác nhận dữ liệu mặc định trên `hr.version`, parser và lịch sử `tp.hr.import.batch/line`; không có model nhân viên song song. Role và thành viên trên một dự án thuộc `tp_project`. Không tạo `tp.department` để sao chép `hr.department`, cũng không hardcode tên nhân viên trong rule.

`tp_hr_workspace` phụ thuộc `tp_organization`, `hr_skills`, `tp_web_home`; chứa view/action/sidebar/table/OWL của TP HR và `tp.hr.workspace` tổng hợp theo quyền/current company. Không phụ thuộc workflow tiền KH-KD để dùng CSS. Dashboard, drill-down và XLSX `/tp_hr/export` dùng cùng population backend không sudo; export whitelist chỉ hồ sơ công việc. Nút chứng chỉ kiểm quyền caller và contact identity trên canonical `tp.credential` nếu có, không cấp thêm quyền KH-KD. [Đặc tả/acceptance HR-001](../demo/HR_001_ACCEPTANCE.md).

Alias đồng nghĩa một-một khác với crosswalk phân bổ một-nhiều. “Khảo sát” và “Khảo sát địa hình” phải được người phụ trách duyệt mapping, không tự gộp bằng so khớp tên. Năm trong mã dự án không tự quyết định kỳ phát sinh giao dịch.

### `tp_project`

Mở rộng `project.project`/`project.task` bằng mã dự án ổn định, chủ đầu tư, phòng chủ trì, năm nghiệp vụ, WBS và `tp.project.assignment` (người, vai trò, dự án, thời hạn). Catalog `tp.work.item` khác dòng phạm vi cụ thể của dự án/hợp đồng. Một tên dự án giống nhau không được tự động gộp nếu khác gói, hợp đồng hoặc nguồn.

### `tp_bid`

Phụ thuộc `crm` và nền dự án khi liên kết đã được chốt. `crm.lead` là cơ hội gốc; `tp.bid.package` chỉ bổ sung gói thầu, hạn nộp, quyết định tham gia, liên danh và kết quả. Không tạo CRM thứ hai.

### `tp_contract`

Hợp đồng pháp lý bên ngoài là model riêng (`tp.contract`, scope line, amendment), vì không phải hợp đồng nào cũng là `sale.order` hoặc `purchase.order`. Loại hợp đồng ban đầu gồm chủ đầu tư, tổng thầu và thầu phụ. **Giao khoán nội bộ không phải loại hợp đồng pháp lý**; nó nằm ở `tp_allocation` và không tự tạo PO/vendor bill giả.

Phụ lục lưu giá trị, loại điều chỉnh, ngày ký/hiệu lực, lý do và chứng từ. BIZ-001 xác định giá cập nhật PKH thay thế giá trị ở phạm vi hạng mục/đơn vị được cập nhật; không coi một giá trị hạng mục là tổng hợp đồng hoặc cộng như delta. Đề xuất snapshot revision đầy đủ dựng từ bản trước + thay đổi có provenance; điều kiện hiệu lực/hồi tố cần hồ sơ pháp lý xác nhận. BASE giữ phê duyệt chính thức; reference đúng version/evidence tách khỏi review, chữ ký và hiệu lực. Xem [baseline BIZ-001](TP_KD_WORKFLOW_AND_PERMISSIONS.md). Không dùng “dòng dương cuối cùng” làm quy tắc chung. Nhiều hợp đồng cùng dự án, đối tác/hạng mục vẫn có ID riêng.

### `tp_allocation`

Ghi `tp.allocation` và các dòng theo project, contract scope, đơn vị/người nhận, giá trị, thời hạn và quan hệ cha-con bằng ID. Cấp 1 là phân bổ từ công ty cho đơn vị/phạm vi chính; cấp 2 là phân bổ tiếp, thường từ đơn vị cho thầu phụ. Liên kết sang hợp đồng pháp lý thầu phụ khi có. Tổng công ty chỉ tính cấp 1; cấp 2 dùng để theo dõi và đối chiếu, không cộng lần nữa. Kiểm tra company/project, parent scope, vòng lặp và vượt khoán tại backend.

### `tp_settlement`

Các model khởi điểm dự kiến: `tp.production.entry` (sản lượng), `tp.acceptance`/line (nghiệm thu), `tp.payment.request` (đề nghị thanh toán). Chúng liên kết project, scope, contract hoặc allocation tương ứng. Phân biệt sản lượng, nghiệm thu, hóa đơn đã xuất, tiền thu/chi và giữ lại; không gộp thành một bảng sự kiện có nhiều cột tiền.

Bản nháp được sửa theo quyền. Bản đã chốt giữ payload lịch sử; sửa/hủy qua action có revision hoặc cancellation, lý do, người thực hiện, thời điểm và liên kết bản trước. Báo cáo tổng hợp từ bản còn hiệu lực. Lịch sử có cấu trúc thuộc từng model nghiệp vụ, không chỉ dựa vào chatter. Chưa cần xây framework event sourcing chung.

Kế toán vẫn là nguồn cuối cho `account.move`, `account.payment` và reconciliation. `tp_account_bridge` chỉ link/đối chiếu, không dựng thêm ledger tiền cạnh `account`.

Trước khi bridge hoàn tất, số hóa đơn/tiền thu từ Excel phải mang provenance và trạng thái chưa đối chiếu; không trình bày như chứng từ kế toán đã ghi sổ. “GT phải xuất hóa đơn” trong nguồn đã phân tích có nghĩa là giá trị đã xuất; tên API mới phải phản ánh nghĩa đã xác nhận.

### `tp_reporting`

Là lớp đọc có kiểm quyền, gồm overview dự án, investor/contractor summary, reconciliation và cảnh báo. Chỉ aggregate trên bản ghi user được phép đọc, kể cả quyền xem giá trị tài chính. SQL view, query raw hoặc cache không tự thừa hưởng đầy đủ bảo vệ của ORM, nên phải kiểm tra scope trước khi trả kết quả. Có thể thêm snapshot khi đo được nhu cầu hiệu năng; cache phải tách company và phạm vi quyền, có invalidation, không trở thành nguồn ghi độc lập.

KPI phải công bố kỳ báo cáo, công thức, currency, nguồn, ngày chốt và dữ liệu còn thiếu. Chỉ số thuộc Kế toán được bổ sung ở bridge hoặc API Kế toán; không làm addon báo cáo nền phụ thuộc cứng vào mọi module tương lai.

### `tp_documents` và `tp_import` (giai đoạn sau)

Source checkout hiện không có `documents`/`approvals` chuẩn dưới `addons/`; không giả định chúng đã cài trong database. Trước mắt dùng `ir.attachment` và metadata/version riêng nếu thật sự cần. API chỉ trả URL tải đã kiểm quyền hoặc token ngắn hạn; không đưa đường dẫn UNC NAS vào browser.

`tp_import` lưu file/hash/schema/batch, đọc Excel ở staging hoặc worker offline, kiểm tra mapping và quarantine dòng lỗi. Import lặp không được cộng trùng và luôn có báo cáo đối chiếu. API web không đọc trực tiếp file Excel trên NAS.

Mỗi addon chỉ tạo các thư mục dùng thật. `tp_contract` sau CTR-001 (read slice) và CTR-002a (workflow nháp, chỉ test) hiện có:

```text
tp_contract/
├── __init__.py
├── __manifest__.py                # depends tp_core, tp_project
├── exceptions.py                  # lỗi nghiệp vụ workflow, API ánh xạ sang HTTP status
├── migrations/20.0.1.1.0/         # gán phòng chủ trì project cho hợp đồng cũ
├── models/
│   ├── __init__.py
│   ├── tp_contract.py             # danh tính, phòng ban, aggregate_version, snapshot theo ngày, tổng
│   ├── tp_contract_revision.py    # gốc/phụ lục/đính chính, review/ký/hiệu lực
│   ├── tp_contract_line.py        # dòng phạm vi + tp.contract.line.amount
│   ├── tp_approval_reference.py   # kết quả BASE + tp.approval.reference.amount
│   ├── tp_contract_document.py    # tệp general/financial, khóa sau khi gửi
│   ├── ir_attachment.py           # chặn thay/xóa binary của tài liệu đã gửi
│   ├── tp_contract_submission.py  # lần gửi rà soát bất biến + snapshot tiền tách riêng
│   ├── tp_contract_audit.py       # audit append-only, outbox, idempotency
│   └── tp_contract_workflow.py    # action T1–T6, scope/capability, version, snapshot
├── security/
│   └── ir.access.csv              # access domain theo project, company, grant
└── tests/
    ├── __init__.py
    ├── common.py
    ├── test_contract_access.py
    ├── test_contract_model.py
    └── test_contract_workflow.py  # T-P01, T-N01…T-N06, T-N08, T-N09
```

Chưa có `views/` hoặc menu native cho hợp đồng; UI/API React là triển khai cũ. Theo DEC-030, UI-CTR-NATIVE-001 sẽ đặc tả menu/list/form nghiệp vụ native, tái sử dụng action/backend; chưa triển khai trong lượt chốt hướng. Grant `financial_read` (`tp.project.grant`) nằm ở `tp_project` để domain khác dùng lại.

Model/action/constraint giữ nghiệp vụ; route chỉ parse input, gọi action và serialize. Dùng action chuẩn như `sale.order.action_confirm`, `purchase.order.button_confirm`, `account.move.action_post` thay cho ghi thẳng state. Các ràng buộc SQL theo API `models.Constraint`/`Index` của source hiện tại; không sao mẫu `_sql_constraints` cũ. Khai báo dependency trực tiếp thật sự dùng trong manifest.

## 5. API và bảo mật

`tp_api` chỉ là lớp transport dùng chung: chuẩn hóa response/error, session, pagination, request id và helper DTO. `tp_planning_api` mới phụ thuộc các domain module cần cho workspace đầu tiên. Các API domain khác được thêm độc lập, tránh một API addon phụ thuộc toàn bộ hệ thống.

```text
tp_api/
├── controllers/       # route mỏng, không tính KPI
├── services/          # errors, DTO, pagination, session
└── tests/

tp_planning_api/
├── controllers/       # projects, contracts, allocations, overview
├── serializers/       # DTO theo OpenAPI
└── tests/             # quyền + response contract + nghiệp vụ
```

API đầu tiên đã có `GET /api/v1/me`, `GET /api/v1/projects`, `GET /api/v1/projects/{id}`; overview theo giai đoạn nghiệp vụ tương ứng. Client ngoài native phải theo API contract, không dùng RPC tùy ý để né contract. Native view/OWL được dùng ORM/RPC Odoo nhưng backend phải kiểm field, action, scope, state và quyền; không dựa vào ẩn nút. Filter/sort/field projection của API phải whitelist tại backend.

OpenAPI tại `contracts/openapi/tanphat-v1.yaml` mô tả endpoint, input, DTO, error, pagination và security; type TypeScript sinh vào `frontend/src/shared/api/openapi.generated.ts`. DTO không phải bản dump field của ORM: money là decimal string kèm currency/precision, date và datetime có quy ước riêng, thiếu dữ liệu trả `null` với trạng thái nguồn. API không trả field nhạy cảm chỉ vì frontend đang ẩn cột. Thay đổi phá vỡ contract đi qua version mới hoặc lộ trình chuyển đổi; CI kiểm schema và generated client.

Theo DEC-030, giao diện chính và session do Odoo phục vụ cùng origin; HTTPS/reverse proxy được thiết kế khi triển khai. Route React cũ chỉ giữ cho tương thích, chưa bị tắt hoặc chuyển hướng trong lượt tài liệu này:

```text
/api/v1/    -> custom HTTP JSON routes trong Odoo
/work/      -> React legacy, không là giao diện chính
/web/login  -> đăng nhập native Odoo, MFA/passkey theo cấu hình
/odoo/      -> giao diện nghiệp vụ Odoo theo quyền
```

Proxy tiếp tục chuyển các route native/assets cần thiết sang Odoo; SPA fallback chỉ áp dụng trong `/work/`, không bắt nhầm API hoặc asset. Khi dev, Vite proxy các route cần thiết để kiểm thử cùng cơ chế session; port dev không trở thành kiến trúc production.

Browser dùng session và login native Odoo; React legacy giữ cách gọi endpoint session/MFA cũ. `GET /api/v1/me` phục vụ client API với user/company/capability và bootstrap/CSRF; response session không cache công khai. Quyền phải kiểm lại mỗi action. Cookie Secure/SameSite/path và proxy headers cần cấu hình/kiểm tra khi triển khai HTTPS; dev hiện loopback HTTP. Không nhúng service key hoặc token dùng chung vào bundle/localStorage.

Custom route chọn `type='http'`, `auth='user'` và response JSON. Cần lớp xử lý lỗi giới hạn trong `/api/v1/` để session hết hạn trả 401 JSON thay vì redirect HTML; kiểm thử các lỗi phát sinh trước khi controller được gọi. Trường hợp bearer server-to-server tách route/scope riêng, khai báo `bearer_scope`; không mở CORS rộng cho SPA.

Đối với HTTP write, source hiện lấy CSRF từ HTTP form params, không tự đọc `X-CSRF-Token` hay token trong JSON body tùy ý. Khởi điểm dùng form-urlencoded với `csrf_token` và payload JSON trong field `payload`; upload dùng multipart. Bootstrap trả token từ session đã xác thực; OpenAPI ghi đúng media type và schema. Nếu chọn JSON request thuần sau này, phải thiết kế adapter xác thực CSRF tương ứng và có integration test; không tắt CSRF toàn bộ để cho request chạy.

Odoo 20 trong checkout này gộp ACL/record rule vào `ir.access`, khai báo ở `security/ir.access.csv` với operation/domain. Permission có group được OR; restriction không có group áp dụng AND cho mọi user. Cần restriction company và phạm vi dự án phù hợp, kiểm tra cả tổ hợp nhiều group để tránh mở rộng ngoài ý muốn. API không dùng `sudo()` để vượt quyền; kiểm cả attachment, export, aggregate và quyền xem trường tiền.

Ma trận quyền được chốt trước model ghi dữ liệu: mỗi dòng là capability (xem dự án, sửa draft hợp đồng, chốt giao khoán, xem tiền, duyệt nghiệm thu, xuất dữ liệu...), mỗi cột là role theo công việc, kèm scope company/project/department và trạng thái bản ghi. Một người có thể giữ nhiều role. Người nhập, người chốt và người quản trị là các capability riêng; thẩm quyền phê duyệt phải khớp quy trình doanh nghiệp. Nếu BASE đang là nơi duyệt chính thức thì cần chỉ rõ nguồn quyết định và cách ghi nhận kết quả vào Odoo, tránh hai luồng phê duyệt có quyền ngang nhau.

Một business operation chạy trong một transaction Odoo; nhiều request liên tiếp từ browser không bảo đảm atomic. Action chốt/duyệt dùng idempotency key khi cần và version token để phát hiện sửa đồng thời; retry chỉ an toàn sau khi xác định tính lặp. Lỗi chuẩn có `{code, message, details, request_id}` và HTTP status phù hợp, không trả traceback cho browser.

## 6. Cấu trúc React lịch sử — giữ tham khảo và hồi quy

DEC-030 thay hướng triển khai chính của mục này bằng native view/action/OWL trong custom addon. Cây và các thư viện dưới đây mô tả frontend cũ; không giao batch mở rộng React dựa vào mục này. Màn hình native mới cần đặc tả riêng, dùng backend đã có.

Lúc đầu chỉ có **một app** trong `frontend/`, dùng React + TypeScript + Vite. Chưa cần microfrontend, workspace package hay BFF Node.

```text
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   ├── providers.tsx
│   │   ├── shell/                 # navigation, project/company context
│   │   └── workspaces/
│   │       ├── registry.ts
│   │       └── planning_business.ts
│   ├── features/                  # theo nghiệp vụ, dùng chung giữa phòng
│   │   ├── projects/
│   │   ├── contracts/
│   │   ├── allocations/
│   │   ├── settlements/
│   │   ├── reports/
│   │   └── documents/             # thêm khi backend có
│   ├── shared/
│   │   ├── api/                   # client, session, errors, generated types
│   │   ├── ui/                    # primitive và trạng thái chung
│   │   ├── lib/                   # format tiền/ngày, không tính nghiệp vụ
│   │   └── config/
│   └── main.tsx
├── mocks/                         # fixture dev/test, không có dữ liệu thật
└── tests/                         # unit, API contract, e2e trọng yếu
```

`app` điều phối routing/workspace; `features` sở hữu màn hình theo nghiệp vụ; `shared` không import ngược feature. Các feature không import sâu vào implementation của nhau; `app` ghép màn hình qua public export khi cần. Component không gọi `fetch` trực tiếp. React Router xử lý route, TanStack Query xử lý server state; chưa cần Redux nếu chưa có state toàn app phức tạp. API client quản lý timeout, request id, auth/error và retry an toàn; query cache tách user/company/project/filter/API version và xóa khi logout. Hủy/loại response cũ khi đổi dự án để tránh hiển thị nhầm scope. Frontend format decimal string theo currency/precision do backend trả, không làm phép tính tiền độc lập.

Mỗi feature có thể gồm `pages/`, `components/`, `queries.ts`, `mutations.ts`, `schemas.ts` và public export; chỉ tạo khi dùng. Validation frontend giúp người nhập sửa lỗi sớm; backend vẫn kiểm tra toàn bộ trước khi ghi. Design token, bảng, form, dialog và loading/empty/error/permission state dùng chung trong `shared/ui`.

Workspace Kế hoạch Kinh doanh chỉ đăng ký các feature được cấp quyền. Kế toán, Kỹ thuật và các phòng sau này tái sử dụng feature dự án/hợp đồng nhưng có route, menu, field và action theo role; không nhân bản toàn bộ code thành `features/ke_toan`, `features/ky_thuat`.

Prototype `frontend/prototype/src/modules/planning-business` được giữ để tham khảo UI/fixture. Khi nối dữ liệu thật, các quy tắc hiệu lực, phụ lục thay thế, cấp 1/cấp 2 và tổng tiền phải chuyển sang backend.

## 7. Quan hệ phụ thuộc

Dependency đích cho phần nghiệp vụ đầu tiên:

| Addon | Phụ thuộc nghiệp vụ/chuẩn dự kiến |
| --- | --- |
| `tp_core` | `base`; thêm `mail` chỉ nếu dùng mixin tương ứng |
| `tp_organization` | `tp_core`, `hr` |
| `tp_project` | `tp_core`, `tp_organization`, `project` |
| `tp_contract` | `tp_core`, `tp_project` |
| `tp_allocation` | `tp_core`, `tp_organization`, `tp_project`, `tp_contract` |
| `tp_settlement` | `tp_project`, `tp_contract`, `tp_allocation` |
| `tp_reporting` | `tp_project`, `tp_contract`, `tp_allocation`, `tp_settlement` |
| `tp_api` | `web`; không phụ thuộc các domain trên |
| `tp_planning_api` | `tp_api`, `tp_project`, `tp_contract` (đã thêm cho API đọc hợp đồng CTR-001); thêm allocation/settlement/reporting khi endpoint tương ứng xuất hiện |
| `tp_bid` (sau) | `crm`, `tp_project` khi liên kết cơ hội-dự án được dùng |
| `tp_sale_bridge` (sau) | `tp_contract`, `sale` |
| `tp_purchase_bridge` (sau) | `tp_contract`, `purchase`; thêm allocation nếu dùng liên kết đó |
| `tp_account_bridge` (sau) | các domain trực tiếp đối chiếu, `account`, `analytic` |

Đây là hướng dependency, không phải manifest đã tồn tại. Mọi addon trực tiếp dùng model/mixin chuẩn như `mail.thread`, `hr.department`, `analytic.account` phải khai báo module cung cấp trong manifest dù đã được kéo vào gián tiếp. `tp_core` không phụ thuộc ngược nghiệp vụ; `tp_api` không phụ thuộc mọi addon tương lai; API addon phụ thuộc domain, domain không phụ thuộc API. Bridge phụ thuộc hai phía, hai phía không phụ thuộc bridge. Nếu liên kết tạo chu trình thì đưa liên kết vào module tích hợp ở phía trên. Documents/import/quality được xác định dependency theo ca sử dụng khi bắt đầu làm.

## 8. Lộ trình dựng nền chính xác

Các giai đoạn dưới đây lưu kế hoạch dựng nền ban đầu. Phần React ở giai đoạn 1 đã thành legacy theo DEC-030; bước hiện hành theo `PROJECT_STATUS.md` và UI-CTR-NATIVE-001, không dựng lại nền từ đầu.

**Giai đoạn 0 - chốt mô hình dữ liệu và baseline.** Khóa commit Odoo, Python/PostgreSQL dev, quy ước ID, mã dự án, work item/crosswalk, ma trận quyền, quy tắc revision và DTO. Chọn 2-3 dự án đại diện; chưa import toàn bộ Excel.

**Giai đoạn 1 - một luồng đọc xuyên suốt.** Tạo `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`; làm session, `/me`, danh sách/chi tiết dự án theo quyền với dữ liệu seed. Dựng frontend shell, project selector, loading/error/permission states và client thật theo OpenAPI. Chưa tạo addon contract/reporting rỗng để đủ cây thư mục.

**Giai đoạn 2 - nghiệp vụ kế hoạch.** Thêm `tp_contract` và `tp_allocation`; xử lý hợp đồng/phụ lục và giao khoán cấp 1/cấp 2. Mọi action chốt/sửa/hủy có history và test.

**Giai đoạn 3 - nghiệm thu và báo cáo.** Thêm `tp_settlement`, `tp_reporting`; phân biệt production, acceptance, invoice, cash và retention. So sánh output backend với dữ liệu mẫu/prototype trên dự án thí điểm.

**Giai đoạn 4 - import có kiểm soát.** Dựng `tp_import` staging, mapping đối tác/hạng mục, provenance và reconciliation; chỉ phát hành sau khi dòng lỗi được xử lý. Không để Master Excel trở thành runtime database.

**Giai đoạn 5 - accounting bridge và mở rộng phòng.** Nối `account`/`analytic`, đối chiếu hóa đơn/thanh toán, rồi mới mở workspace cho Kế toán, Kỹ thuật, KCS, hồ sơ và các nghiệp vụ khác. `tp_bid`, documents, sale/purchase bridge được thêm theo ca sử dụng đã chứng minh.

## 9. Quy tắc bất biến và cổng nghiệm thu

1. Core Odoo không bị sửa; schema riêng có version/migration.
2. Backend là nguồn sự thật; KPI có công thức, nguồn và owner.
3. Draft được sửa theo quyền; posted không xóa vật lý; revise/cancel có lịch sử.
4. Tách business date, effective date và recorded timestamp.
5. Không dùng tên làm khóa; không tự gộp dự án/hợp đồng trùng tên.
6. Cấp 2 không cộng vào tổng cấp 1; các bên của một nghiệp vụ không bị đếm hai lần.
7. `null`, `0`, số âm và “chưa xác nhận” giữ khác biệt.
8. Tiền dùng precision/currency của Odoo; DTO trả decimal rõ ràng, frontend không dùng JS float để quyết định nghiệp vụ.
9. Dữ liệu và file thật không nằm trong frontend bundle/Git; document luôn kiểm quyền ở backend.
10. Mỗi addon có security và test trước khi nối vào module kế tiếp.

**Cổng nền kỹ thuật:** Odoo chạy được với `custom_addons`; cài/nâng cấp addon trên dev DB thành công; frontend đăng nhập/đọc danh sách và chi tiết dự án theo OpenAPI; session hết hạn, CSRF và hai user khác scope được kiểm thử; database và filestore backup/restore được xác nhận trước pilot có dữ liệu thật.

**Cổng nghiệp vụ Kế hoạch:** phụ lục, giao khoán cấp 1/cấp 2, revision/cancellation, import lặp và dữ liệu thiếu có test; overview khớp nguồn trên dự án thí điểm sau đối chiếu. Đạt nền kỹ thuật không đồng nghĩa đủ nghiệp vụ để triển khai toàn công ty.

Kiểm tra theo scope: addon install/upgrade, security/transaction tests, native XML/assets/OWL và luồng trình duyệt trọng yếu; React typecheck/build khi sửa legacy. Giữ dev/staging/production tách dữ liệu; chỉ config mẫu ở Git. Pin commit Odoo và dependency; nâng cấp qua staging/migration, không kéo upstream trực tiếp vào production.

## 10. Phạm vi lượt thiết kế này

Lượt dựng nền triển khai tổ chức/hạng mục/dự án, phân công và API đọc, kèm React workspace nối Odoo thật trên database dev/test. CTR-001 sau đó thêm `tp_contract` read slice (hợp đồng/revision/dòng phạm vi/BASE/tài liệu, grant tiền theo project) với dữ liệu giả lập. Giao khoán, nghiệm thu, reporting và import trong tài liệu vẫn là thiết kế cho giai đoạn tiếp theo; chưa có dữ liệu nghiệp vụ thật. OPS-001 đã diễn tập backup/restore local theo status; chưa triển khai production/backup ngoài máy. BIZ-002 hiện ưu tiên review thiết kế toàn công ty trước code, không tự thực hiện tiếp giai đoạn 2–5 từ lộ trình mục 8; ngoại lệ đã được người dùng mở là CTR-002a trên test (DEC-020, CHG-20261028-014).

## 11. Cơ sở kiểm tra và phần cần xác minh khi triển khai

Thiết kế được đối chiếu với source hiện tại, không phải kết quả kiểm thử một Odoo server đang chạy:

- [release.py](../../odoo/release.py): khai báo 20.0, Python 3.12-3.14, PostgreSQL tối thiểu 16. Cần khóa commit/runtime thực tế ở giai đoạn 0.
- [ir_access.py](../../odoo/addons/base/models/ir_access.py) và security guideline của repository: quyền hợp nhất `ir.access`, operation/domain và semantics group.
- [HTTP dispatcher](../../odoo/http/dispatcher.py): CSRF HTTP params và redirect khi session hết hạn. Adapter lỗi/CSRF của API mới phải được kiểm thử thực tế.
- [session controllers](../../addons/web/controllers/session.py), [home controllers](../../addons/web/controllers/home.py): session/login native và route `/odoo`.
- [hr.department](../../addons/hr/models/hr_department.py): model phòng ban có sẵn để kế thừa.
- [.gitignore](../../.gitignore): có exception cho tooling frontend; secrets/runtime không được đưa vào Git.

Có source `account`, `analytic`, `l10n_vn`, `crm`, `project`, `sale`, `purchase`, `hr`, `mail`, `portal`, `auth_oauth` không chứng minh chúng đã cài hoặc đáp ứng đủ kế toán/phê duyệt/hóa đơn điện tử Việt Nam. Edition, license, module cài thực tế và tích hợp liên quan phải được kiểm tra trước khi chọn phạm vi production. Các mô tả trong tài liệu nguồn là bằng chứng nghiệp vụ để phân tích, không phải lệnh triển khai tự động.

## 12. Integration/security addon NATIVE-DATA-003

CHG-20261102-014: `custom_addons/tp_crm_project_bridge` giữ FK optional `crm.lead.tp_project_id` với company/customer integrity và CRM native giao project scope; `tp_timesheet_scope` áp scope managed project lên analytic-line CRUD và create/write target lookup; `tp_dashboard_privacy` chặn public snapshot/token theo cờ nội bộ của dashboard. Ba addon đã clone-test rồi cài dev, không sửa upstream/React/OpenAPI hoặc managed-task write policy. Tooling có ownership/journal/private snapshot tại `scripts/native_data003*`; [runbook](../demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md) và [TASK-001](RFC_TASK_001_MANAGED_TASK_PROGRESS.md) giữ ranh giới partial/gate nghiệp vụ. Tên kỹ thuật mới không tạo app/menu hoặc phân hệ rỗng.

## KD-NATIVE-001 — Runtime dev18069 (CHG-20261106-017)

`custom_addons/tp_kd_workspace` dùng CRM/project/task/partner/tp_contract canonical, thêm typed allocation/production/acceptance/payment.request/periodic.plan/credential/obligation và helper review/money/event. View/list/form/search, OWL native save-version và SCSS nằm trong addon; quyền/transition ở backend. Registry dataset chỉ operator, seed/inventory/verify/cleanup guarded tại `scripts/kd_native001_dataset.py`. Đã clone-test và cài dev cùng `tp_contract`20.0.1.2.0; không đổi REST/OpenAPI/React. [Workflow](TP_KD_NATIVE_001_WORKFLOW.md), [bàn giao dev](../demo/KD_NATIVE_001_ACCEPTANCE.md). Các đoạn “chưa dev” ở trên là lịch sử trước lô tích hợp.
