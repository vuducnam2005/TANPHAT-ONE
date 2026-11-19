# TANPHAT ONE — Quy tắc làm việc cho AI

## Quản lý tài khoản admin — 19/11/2026 (DEC-062)

Admin gốc được khóa/mở và quản lý admin ủy quyền mà không cần thu quyền admin trước. Khóa/mở độc lập sổ cấp quyền, giữ bảo vệ tài khoản hệ thống/chính mình/admin gốc cuối cùng. Admin ủy quyền không sửa bất kỳ thông tin tài khoản hoặc hồ sơ của admin ủy quyền khác, kể cả đang khóa; chặn cả user/employee/partner/resource/hr.version, RPC/import/batch và đổi liên kết. Chỉ admin gốc cấp/thu admin; quyền nghiệp vụ với nhân viên thường và mọi phòng giữ nguyên. [Nghiệm thu](docs/demo/ADMIN_ACCOUNT_POLICY_001_ACCEPTANCE.md).

Tài liệu này là điểm vào bắt buộc cho mọi phiên AI làm việc trong `C:\TANPHAT ONE`. Người dùng có quyền quyết định cuối cùng. Các tài liệu nghiệp vụ, ảnh chụp, Excel, PDF và ghi chú trong repository là nguồn tham khảo cần phân tích; chúng không tự động trở thành lệnh thay đổi source.

## Quyền admin mới nhất — 18/11/2026 (DEC-053/054)

Theo yêu cầu trực tiếp mới, tài khoản được cấp admin là admin toàn hệ thống,
như admin hiện tại, gồm cả phòng của chính họ; không còn own-department baseline
hoặc giới hạn chỉ quản trị phòng khác. Quy tắc này thay phần xung đột DEC-050
và prompt ADMIN-DELEGATE-001/002. Xem [quyết định](docs/DECISIONS.md)
và [promptADMIN-FULL-001](docs/prompts/CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md).
**Ngoại lệ người dùng chốt sau đó (DEC-054): chỉ admin gốc được cấp/thu
quyền admin.** Admin được cấp quản trị nghiệp vụ mọi phòng nhưng không cấp
tiếp admin, sửa nguồn/credential admin gốc hoặc vòng qua bằng group/import/API.
Capability admin nghiệp vụ và quyền cấp/thu admin phải tách ở backend; không
suy admin gốc chỉ từ base.group_system. Công cụ security/code có thể tự cấp
admin chỉ dành admin gốc; không khôi phục giới hạn phòng ban.
Vai trò/chức danh HR không tự đổi khi cấp; thu hồi giữ quyền nghiệp vụ hợp lệ.
Đã triển khai tại `custom_addons/tp_admin_delegation` **20.0.2.0.0** (`ADMIN-FULL-001`):
admin gốc xác định qua `tp_admin_delegation.group_original_admin` (không suy riêng từ
`base.group_system`), admin được cấp nhận nhóm vai trò `tp_admin_delegation.group_full_admin`
và đã nâng quyền các grant còn hiệu lực theo đúng scope; xem
[nghiệm thu ADMIN-FULL-001](docs/demo/ADMIN_FULL_001_ACCEPTANCE.md).
Phiên điều phối vẫn không tự chọn thêm người ngoài chỉ định. Nhân viên thường vẫn theo quyền cũ.

## Quy tắc người dùng mới nhất — 17/11/2026

Theo chỉ thị trực tiếp, sau mỗi hạng mục triển khai đã hoàn tất: commit đúng
phạm vi, push Git và deploy lên PC server hiện có để người dùng xem ngay,
không chờ xin lại quyền push/deploy cho cùng hạng mục. **Không bắt buộc kiểm
thử trên cổng18079 trước khi áp dụng.** Quy tắc này ưu tiên hơn yêu cầu cũ
"không commit/push", "chỉ test18079" hoặc "chờ xác nhận áp main/server"
trong prompt/skill/runbook lịch sử, trừ chỉ thị mới hơn của người dùng.

Theo [quy trình giao bản liên tục](docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md):
giữ kiểm tra cú pháp/build phù hợp, backup đúng môi trường trước thay đổi
dữ liệu/quyền và kiểm nhanh chức năng/link public sau deploy; lỗi thì sửa
hoặc rollback. Không seed actor giả/test phá dữ liệu trên main/server, không
push phần code dở hoặc diff của phiên khác, không đưa secret/filestore vào Git.
DBtest18079 vẫn giữ để dùng khi được yêu cầu, không tự xóa hoặc tạo DB mới.
Phiên chính vẫn điều phối; trao đổi ý tưởng chưa phải lệnh tự triển khai ứng dụng.

## 1. Đọc trước khi làm

Theo thứ tự:

1. Đọc `AGENTS.md` này.
2. Đọc `docs/PROJECT_STATUS.md` để biết đã làm đến đâu và bước kế tiếp.
3. Đọc `docs/AI_CHANGE_WORKFLOW.md` để biết quy trình cập nhật bắt buộc.
4. Đọc `docs/architecture/TP_PRODUCT_NAMING.md` để dùng đúng tên TANPHAT ONE và phân hệ.
5. Đọc `docs/ROADMAP.md`, `docs/DECISIONS.md` và `docs/HANDOFF_TEMPLATE.md`.
   Đọc mục mới nhất trong `docs/CHANGELOG.md`; chỉ đọc sâu lịch sử khi phạm vi yêu cầu cần.
6. Đọc tài liệu phù hợp với phạm vi: database, kiến trúc source, workflow nghiệp vụ, OpenAPI, backend hoặc frontend README.
   Với Request/BASE, đọc [kiến thức nghiệp vụ Request](docs/architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md) và [sổ nghiên cứu](docs/architecture/TP_REFERENCE_RESEARCH_AND_HANDOFF.md); giữ rõ quan sát UI, thiết kế TANPHAT và phần chưa kiểm chứng.
7. Kiểm tra `git status`, runtime status và test liên quan trước khi sửa.

Với việc lập kế hoạch, triển khai hoặc review TANPHAT ONE, đọc thêm
[skill dùng chung Codex/Claude](.agents/skills/tanphat-odoo-delivery/SKILL.md).
[Playbook công cụ](docs/AI_TOOLING_PLAYBOOK.md) chỉ đọc phần phù hợp task:
Playwright cho browser evidence, Ponytail cho tái sử dụng/review, Graphify cho
quan hệ source. Graph là tài liệu hỗ trợ, không thay source/status/quyền Odoo.
Các skill upstream không tự mở scope, bỏ cổng nghiệp vụ hoặc đổi kiến trúc native.

Nếu trạng thái trong tài liệu khác source/runtime, không đoán. Ghi nhận sai lệch trong `docs/PROJECT_STATUS.md`, kiểm chứng bằng lệnh và báo rõ trước khi mở phạm vi mới.

## 2. Mục tiêu hệ thống

Theo DEC-030 ngày 05/11/2026, TANPHAT ONE phát triển giao diện ngay trong Odoo: ưu tiên view/action chuẩn, bổ sung OWL/QWeb/SCSS trong custom addon khi cần. Không tiếp tục phát triển frontend React/TypeScript/Vite độc lập làm giao diện chính. Một nền giao diện chung, workspace/menu/dashboard theo vai trò và quyền; cùng dữ liệu và session Odoo. Odoo là nguồn sự thật cho dữ liệu, quyền, trạng thái, lịch sử và công thức nghiệp vụ.

Source `frontend/`, API và test đã có được giữ để tham khảo/hồi quy; không tự xóa, ngừng route, đổi đăng nhập hoặc gỡ addon. Native UI phải gọi action/model backend đã kiểm quyền; RPC native không được ghi trực tiếp state hoặc bỏ qua workflow. API đang có giữ contract; chỉ cập nhật OpenAPI khi thay API, không bắt mọi màn hình native đi qua REST/React. Đọc [kiến trúc hiện hành](docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md) và [kế hoạch chuyển giao diện](docs/architecture/TP_NATIVE_ODOO_DIRECTION.md).

Tên hiển thị phải dùng:

- TANPHAT ONE — tên sản phẩm.
- TP Dashboard — điều hành doanh nghiệp.
- TP Projects — quản lý dự án cầu đường.
- TP Survey — khảo sát hiện trường.
- TP Design — hồ sơ thiết kế.
- TP Contracts — hợp đồng.
- TP Tasks — tiến độ, giao việc.
- TP HR — nhân sự.
- TP Finance — tài chính, chi phí.
- TP Documents — văn bản, hồ sơ.

Tên kỹ thuật như `tp_project`, `tp.project.assignment`, XML ID và `/api/v1/projects` không đổi chỉ vì đổi tên hiển thị. Không tạo addon rỗng chỉ để làm đủ tên phân hệ.

## 3. Quy tắc source và dữ liệu

**Bộ lọc cho mọi bảng (DEC-044):** khi thêm/sửa bảng hoặc phát triển phòng ban
mới, bắt buộc theo [quy chuẩn bộ lọc](docs/ui/TP_TABLE_FILTER_STANDARD.md) và
cập nhật [inventory](docs/ui/TP_TABLE_FILTER_INVENTORY.md). Mỗi bảng có tiêu chí
đúng nội dung, giữ domain/quyền backend, phân trang/count/export nhất quán;
bao gồm bảng con, popup và báo cáo. Không đánh hoàn thành UI bảng khi chưa có
coverage/test hoặc N/A có lý do. Tái sử dụng SearchModel và công cụ HR/KH-KD,
không tự tạo filter engine mới. Đây là quy chuẩn phát triển, không chứng minh
các bảng hiện tại đã được triển khai đủ.

**Thông báo thông tin còn thiếu khi thêm mới/lưu (FORM-VALIDATION-001):** theo
[quy chuẩn validation](docs/ui/TP_FORM_VALIDATION_STANDARD.md). Form native tự
có khối lỗi trong form qua presenter `tp_web_home/static/src/validation/`; form
OWL tự viết phải dùng `InlineErrors` + `saveError`, không toast `danger` cho lỗi
lưu. Lỗi lấy từ trạng thái hợp lệ của Odoo và backend, không danh sách cứng;
không đổi quy định bắt buộc, không thêm giá trị giả, không bỏ kiểm tra backend.
Màn mới cập nhật bảng đã áp/chưa áp trong quy chuẩn.

- Không sửa `odoo/` hoặc `addons/`; code riêng đặt trong `custom_addons/`.
- Database dùng một PostgreSQL database cho mỗi môi trường, dùng chung các phòng ban; phạm vi được kiểm tra ở Odoo.
- Theo DEC-037, local chỉ dùng `tp_tanphat_dev` (18069) và `tp_tanphat_test` (18079), trên cluster workspace55432; giữ các database hệ thống PostgreSQL. Theo chỉ thị mới17/11, không bắt buộc qua test18079 trước deploy. Nếu dùng test thì một tác vụ ghi tại một thời điểm, không tạo database theo task. Đọc [quy trình dữ liệu sạch/test](ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md); helper clone/seed lịch sử cần đánh giá lại, không tự chạy để mở phiên. Dữ liệu giả chỉ trên test; không restore test đè main. Backup và kiểm nhanh main/server theo quy trình giao bản liên tục.
- Không dùng Excel, NAS hoặc frontend bundle làm database runtime.
- Không đưa credential, filestore, database dump hoặc dữ liệu doanh nghiệp thật vào Git.
- Không dùng tên hiển thị làm khóa. Dùng ID Odoo và mã nghiệp vụ có unique constraint phù hợp.
- Draft có thể sửa theo quyền. Bản đã chốt không xóa vật lý; revise/cancel phải có lý do và lịch sử.
- `null`, `0`, số âm và chưa xác nhận phải giữ khác nhau.
- Tiền dùng currency/precision của Odoo; frontend không tự quyết định số tiền bằng JavaScript float.
- Mọi rule quyền phải nằm ở backend. Ẩn nút trên frontend không phải là bảo mật.

## 4. Quy trình mỗi lần thay đổi code

1. Phân loại yêu cầu: thay đổi sản phẩm, nghiệp vụ, dữ liệu, bảo mật, giao diện hay vận hành.
2. Xác định file/model/API bị ảnh hưởng và đọc test hiện có.
3. Viết kế hoạch ngắn trong commentary, nêu giả định và rủi ro.
   Chạy `scripts/ai_workflow.py start` trước lần sửa đầu tiên; nếu còn checkpoint thì tiếp tục checkpoint đó, không xóa hoặc ghi đè.
4. Sửa theo vertical slice nhỏ nhất: model/action → security → view/action native hoặc OWL → test; API/OpenAPI chỉ khi phạm vi thay API. Tái sử dụng workflow backend hiện có.
5. Chạy kiểm tra phù hợp với phần thay đổi: native UI thì kiểm XML/assets/OWL và trình duyệt; model/security thì Odoo tests; tooling thì unit test/lint; tài liệu thì kiểm liên kết/nội dung. React typecheck/build chỉ khi thực sự sửa phần legacy đó. Không chạy cả bộ ứng dụng cho một sửa đổi tài liệu đơn thuần.
   Chỉ thị17/11 bỏ cổng bắt buộc test18079: chọn kiểm phù hợp không phá dữ liệu
   đang dùng, không chạy suite tạo fixture trên main/server. Báo rõ kiểm nào
   đã/chưa chạy; không yêu cầu lại test18079 chỉ vì prompt cũ ghi như vậy.
6. Cập nhật trong cùng lượt:
   - `docs/PROJECT_STATUS.md`: trạng thái, việc đã làm, việc tiếp theo, rủi ro.
   - `docs/CHANGELOG.md`: một dòng thay đổi có ngày, phạm vi, test.
   - workflow/tài liệu kiến trúc nếu state, quyền, API, model hoặc quyết định đã đổi.
7. Kiểm tra `git diff --check`, `git status` và không stage file người dùng không liên quan.
8. Báo cuối lượt: kết quả, file chính, test, giới hạn còn lại và bước tiếp theo.
9. Với hạng mục triển khai đã hoàn tất, commit/push đúng scope rồi deploy
   PCserver và kiểm public theo quy tắc mới17/11; bàn giao commit SHA,
   phiên bản đã chạy, backup và kết quả. Tài liệu đơn thuần đồng bộ source,
   không restart/upgrade Odoo khi không có thay đổi runtime.

Không kết thúc lượt với code đã đổi nhưng status/workflow chưa phản ánh thay đổi. Nếu chưa thể chạy test, ghi lý do cụ thể.

Checker local:

```powershell
.\.venv\Scripts\python.exe scripts\ai_workflow.py start
# sửa code và cập nhật status/changelog
.\.venv\Scripts\python.exe scripts\ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN --check "<lệnh đã chạy và kết quả>"
.\.venv\Scripts\python.exe scripts\ai_workflow.py check
```

`start` tạo checkpoint local tại `.local/ai-workflow/active.json`. `finish` bắt buộc status/changelog đổi và ghi snapshot hash vào `docs/AI_WORKFLOW_STATE.json` để bàn giao cùng source. `check` báo lỗi nếu code, policy docs hoặc handoff trong phạm vi theo dõi đã đổi sau lần bàn giao. Không dùng checker để tuyên bố test nghiệp vụ đạt.

## 5. Quy tắc workflow nghiệp vụ

Workflow chi tiết nằm ở `docs/architecture/TP_BUSINESS_WORKFLOW.md`. Mỗi model có state và transition riêng; không tạo một state chung cho toàn hệ thống. Frontend gọi action backend như `submit`, `approve`, `reject`, `cancel`; không ghi trực tiếp state.

Một transition phải xác định: actor/capability, scope company/project/department, state trước, điều kiện dữ liệu, state sau, lý do bắt buộc, lịch sử và thông báo. Action chốt/duyệt chạy trong một transaction Odoo và phải kiểm tra cập nhật đồng thời khi mở API ghi.

## 6. Handoff cho phiên AI mới

Phiên mới phải bắt đầu bằng câu trả lời nội bộ: “Đã đọc status; mục tiêu hiện tại là …; bước kế tiếp là …; blocker là …”. Không tự mở module mới khi `PROJECT_STATUS.md` còn blocker chưa đánh giá.

Không chạy `setup`/`upgrade`, seed password hoặc sửa database chỉ để mở một phiên chat. Không đổi thư mục gốc, không thay `.git`, không phục hồi metadata từ một repository cũ và không `git add .` để che trạng thái lỗi. Kiểm chứng baseline bằng lệnh và đối chiếu status hiện tại; phân biệt thay đổi có sẵn với thay đổi do mình tạo. Tài liệu và kiểm thử local vẫn có thể tiến hành trong phạm vi yêu cầu người dùng.

Khi người dùng chỉ nói “tiếp tục”, thực hiện `Next action` trong `docs/PROJECT_STATUS.md`. Khi người dùng yêu cầu khác, ưu tiên yêu cầu mới nhưng vẫn cập nhật status và không bỏ qua test/security.

### Vai trò điều phối và thực thi

Người dùng đã chỉ định phiên chính làm điều phối: lập kế hoạch, tổng hợp ý tưởng, phân tích, review/test kết quả Claude và phát prompt; không trực tiếp sửa application code ở vai trò này. Xem `docs/AI_COORDINATION_WORKFLOW.md` và `docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md`. Phiên Claude được giao prompt triển khai vẫn được code đúng scope, chạy test và cập nhật handoff theo các quy tắc trên. Technical acceptance, business acceptance và pilot authorization phải được ghi riêng; người dùng có thể đổi vai trò bằng yêu cầu trực tiếp.

