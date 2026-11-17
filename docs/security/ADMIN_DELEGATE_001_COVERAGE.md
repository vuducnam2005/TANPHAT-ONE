# ADMIN-DELEGATE-001 — Bản đồ nguồn và phạm vi đã rà soát

Ngày 17/11/2026. Đọc cùng [policy](ADMIN_DELEGATE_001_POLICY.md),
[acceptance](../demo/ADMIN_DELEGATE_001_ACCEPTANCE.md) và
[prompt](../prompts/CLAUDE_ADMIN_DELEGATE_001_AND_PUBLIC_FILES.md).
Đây là bản đồ source và giới hạn kỹ thuật; kết quả runtime từng ca nằm ở acceptance.
Không suy từ một menu mở được rằng mọi chức năng trong phân hệ đã được ủy quyền.

## 1. Cách cộng quyền

Odoo 20 của repository dùng `ir.access`: các dòng có group là permission được OR;
các dòng không có group là restriction được AND. Thêm một group permission không
vượt được restriction hiện có. Field có `groups` và action kiểm capability riêng
vẫn là những cổng độc lập. Addon riêng mở thêm domain trên từng model đã rà soát;
không cấp `base.group_system`, không giả `has_group`/`isSystem` và không thay
`check_access` toàn cục. Quyền nghiệp vụ hiện hành luôn được đánh giá riêng.

Phòng được bảo vệ lấy từ toàn bộ danh tính HR/phiên bản hiệu lực, trách nhiệm
trưởng phòng, phân công/grant dự án, thành viên CRM và phân quyền Báo cáo còn
hiệu lực. Quan hệ không rõ, trách nhiệm toàn công ty hoặc nguồn giao thoa được
xử lý theo baseline; không lấy một nhân viên `limit=1`, tab hoặc context UI.

## 2. Bản đồ model/action/field/caller

| Nhóm/model | Nguồn công ty/phòng thật | Caller và cổng hiện hữu cần giữ | Phạm vi thêm / giới hạn |
| --- | --- | --- | --- |
| `hr.employee` | `company_id`, `_get_version().department_id`, context `version_id=False`; xét mọi employee nối user | `hr_workspace._population`/HR export; `_tp_account_admin`; `identity._tp_sync_identity`; native read/write và groups HR | Read ngoài phòng qua domain; field riêng tư HR vẫn theo groups. Adapter hồ sơ chỉ có allowlist metadata, tạo hồ sơ và lưu trữ hồ sơ chưa nối tài khoản; không tự coi là full CRUD hồ sơ HR. |
| `tp.hr.delegated.profile.wizard` | employee/company/phòng hiện hành cố định; digest employee/version/resource kiểm lại dưới lock | native modal → `action_apply`; Python sentinel riêng cho create/metadata/archive | Tên, email/điện thoại công việc, di động và chức danh mô tả. Tạo chỉ ở phòng khác với company/phòng đã kiểm, không nhận link/group/phiên bản lồng. Archive chỉ hồ sơ chưa có tài khoản. Không chuyển phòng, sửa chức vụ `job_id`, khôi phục tùy ý hoặc xóa vật lý. |
| `hr.version` | `employee_id`, company và phiên bản thực có ngày hiệu lực | `department_transfer.TransferVersion.create/write/unlink`; delegated fields từ employee | Chặn clone/reparent/kích hoạt lịch sử để đổi scope; baseline phiên bản giữ. |
| `resource.resource`, `res.users`, `res.partner` | employee/resource/user/partner nối bằng ID, không đối tên | personal-account sentinel, identity sentinel; `my_profile` allowlist; account wizard | Chặn thay link, company/groups/credential trái phạm vi. Thông tin cá nhân của chính user theo allowlist. |
| `tp.hr.account.wizard` | employee đã kiểm, user kỳ vọng, mọi identity của target, company user | `_employee` khóa employee/resource; `check_identity`; `_require_recent_identity`; create/lock/reset | Adapter chỉ target thường ngoài phòng; không reset/khóa main, delegate khác, HEAD hoặc tài khoản có khả năng sửa security. Không nhận groups tùy ý. |
| `tp.hr.role.wizard`, transfer/identity/import | employee, current-version và snapshot quyền | `action_preview/action_apply`, digest, object sentinel và SQL locks | Bổ nhiệm/chuyển phòng/nhập danh tính không được mở bằng delegation. |
| `project.project`/`project.task` | `project.company_id`, `tp_department_id`; task qua project; xét cả contract/CRM con đã archive | `_tp_granted_project_ids`; project/KD global restriction; capability runtime | Read và capability trên dự án ngoài mọi phòng được bảo vệ. Project có contract/CRM nguồn phòng mình hoặc chưa rõ giữ baseline. Tạo/sửa/xóa project/task, cấu hình và chuyển phòng giữ baseline. Không đưa tập delegation vào search callback/boolean quyền native có cache. ADMIN-DELEGATE-002 S4: `_kd_money_read` cộng dự án `other_project(lock=True)` để tình trạng/ghi chú/lịch sử dự án và giá gói thầu chạy qua command gốc; `tp.project.update`/`tp.task.update` đọc theo cùng scope; tiến độ task vẫn người được giao/HEAD, không cấp assignment/HEAD. |
| `tp.project.assignment`, `tp.project.grant`, `tp.kd.grant`, `tp.kd.department.role`, `crm.team.member` | company + department và project department; ngày hiệu lực | project scope/financial scope; `_tp_has_capability`, `_has`, `_roles`, invalidation | Nguồn xác định phòng được bảo vệ; không cho delegate tự/sửa hộ quyền hoặc cấp tiếp. |
| `crm.lead` | `tp_project_id.tp_department_id` cùng `team_id.kd_department_id`; pre-project không có project giữ baseline | `_kd_project_scope` baseline, `_kd_require`, `OpportunityMoney`, `_kd_financial_projects`, native content security | Chỉ thêm read có project và nguồn rõ; CRM create/write/delete cùng owner/action guard giữ baseline. CRM khác context/URL vẫn cùng nguồn; file/money cần qua guard gốc, không mặc định mở theo read. |
| `tp.contract` và revision/line/amount/submission/audit/document | company/project + contract.department; dòng con theo parent thật | native wizard → `_tp_run` → `_tp_capabilities/_tp_guard` → workflow sudo; version/idempotency/state guard | Thêm scope read/capability ngoài phòng; tạo/sửa nháp, trình và các action đúng state/actor gốc. `assign_owner`, `document_add/remove`, `take_review` vẫn cần HEAD; không mở ký/hiệu lực/BASE, xóa hợp đồng hoặc sửa trạng thái trực tiếp. |
| Contract/KD file/chatter | attachment → typed document/revision/contract/project hoặc CRM parent; message parent | `ir.binary._find_record`, guarded binary/read/export; `native_content_security.actor_leads` giữ caller `sudo(False)` | Bảo vệ file theo nguồn. Mở một project không tự bỏ financial/personal/snapshot restriction. |
| KD dossiers (`tp.bid.package`, participation; allocation/production/acceptance/payment/credential/obligation) | project, parent record, nguồn hợp đồng/subject và owner/reviewer | `tp.kd.review.document._kd_require/_kd_check_targets/_kd_transition`, amount guard, credential person restriction | Chỉ những model được extension cụ thể có phần thêm; các model còn lại baseline. Dòng tiền, subject riêng tư, revision và source nghiệp vụ không được suy từ tên phòng. |
| `tp.report.document/plan/line` | company/department/owner và mọi employee của owner; project/task/plan/dependencies/provenance | `_tp_report_domain`, `_has_capability`, `_locked/_transition`; no self-review; selection/export/dashboard | ADMIN-DELEGATE-002 S2: đọc hồ sơ cá nhân đã gửi và hồ sơ phòng ngoài phòng khi dòng, payload snapshot, carry/rollup và dependency đều trỏ tới kế hoạch/dự án/task/hồ sơ đang mở; kế hoạch mở theo cả cây quý → tháng → tuần; nghĩa vụ, chỉ đạo (cả hồ sơ gốc ngoài phòng), phản hồi `published`, lịch sử, nội dung phần mẫu theo cùng scope. Nháp/trả lại của người khác giữ riêng. CUD/review/chốt giữ capability/write/actor/workflow baseline; đổi nguồn bị chặn. |
| Report value/snapshot/aggregate/catalog/schedule | financial provider/confirmer, payload lịch sử và dependency thực; company của cấu hình | finance group/assignment; snapshot bất biến; config ACL/action | S2: snapshot chỉ đọc khi hồ sơ mở và header payload khớp hồ sơ; không ghi. Value tài chính, tổng hợp công ty và config không mở thêm; assignment phân quyền vẫn bị chặn cho delegate. Admin chính: `base.group_system` ngụ ý vai trò cấu hình Báo cáo, không cấp thẩm quyền nghiệp vụ. |
| `maintenance.equipment` | company, custody có employee → HR version thực; department-held → department; parent/replaces cũng phải ngoài phòng | original `write`, `lock_records`, version/state/custody guards; native search/read/group/export | Thêm read và sửa metadata của thiết bị giữ tại phòng khác đã rõ nguồn. ADMIN-DELEGATE-002 S3: máy rảnh trong kho chung chỉ đọc để chọn; Gán/Đổi máy/Trả về kho qua `equipment_handover.py` (khóa, kiểm lại người nhận/máy ngoài phòng, chạy RPC gốc nguyên tử). Không đăng ký thiết bị, sửa/tệp/chatter/nhãn máy kho, đổi parent/company/custody trực tiếp hoặc chuyển phòng qua delegation. |
| `maintenance.request` | equipment + reporter HR; proposal-linked chưa rà soát giữ baseline | original new/start/done/cancel, state/result/cost và equipment-version guards | Thêm read/create/edit/delete đúng state và start/finish tại chỗ; không đổi equipment/reporter/company/native employee, gửi vendor/nhận kho hoặc nguồn proposal. Native employee mặc định của actor được bỏ để không biến delegate thành owner admin. Lịch activity vẫn theo assignee admin gốc. |
| `tp.equipment.software` / `meter` | parent equipment | original company/value/evidence constraints, nested commands | CRUD đúng nguồn ngoài phòng; cấm reparent. |
| `tp.equipment.move` / move.line | company, mọi equipment; mọi người/phòng trước và sau, target | snapshot/from-to/current equipment và original move workflow | Chỉ read history khi tất cả nguồn/đích rõ và ngoài phòng được bảo vệ. Employee custody thiếu department snapshot gốc giữ baseline vì HR có thể ghi đè phiên bản cùng ngày. Phiếu stock/vendor/location/unknown, proposal/inventory/reversal hoặc dòng phòng mình giữ baseline. Không mở move CRUD. |
| Equipment category/location/stage | Chỉ danh mục đang được thiết bị/repair cho phép tham chiếu | native many2one/reference rendering | Chỉ read phục vụ hồ sơ, không mở quản trị danh mục chung. |
| Equipment receipt/proposal/inventory/import/quick-action/dashboard | company-common, đa dòng, source/destination, HR/stock | original `is_admin/check_admin`; dashboard có query proposals/import; inventory/apply/import có write hàng loạt | Receipt/inventory/import giữ baseline; không cho helper chỉ có `env` nhận quyền delegate. S1: dashboard/summary qua adapter scope; đề xuất ngoài phòng chỉ đọc (duyệt/trả/thực hiện chưa có adapter). S3: quick-action có adapter riêng, popup chỉ của chính delegate. |

Nguồn chính:
[HR account](../../custom_addons/tp_hr_workspace/models/hr_account_wizard.py),
[HR identity](../../custom_addons/tp_hr_workspace/models/identity.py),
[HR version transfer](../../custom_addons/tp_hr_workspace/models/department_transfer.py),
[project scope](../../custom_addons/tp_project/models/project_project.py),
[KD permissions](../../custom_addons/tp_kd_workspace/models/workspace.py),
[contract workflow](../../custom_addons/tp_contract/models/tp_contract_workflow.py),
[reporting](../../custom_addons/tp_reporting/models/reporting.py),
[equipment original guards](../../custom_addons/tp_equipment/models/common.py),
[delegation sources](../../custom_addons/tp_admin_delegation/models/delegation.py),
[HR profile adapter](../../custom_addons/tp_admin_delegation/models/hr_profile.py),
[business extension](../../custom_addons/tp_admin_delegation/models/business_scope.py),
[equipment extension](../../custom_addons/tp_admin_delegation/models/equipment_scope.py).

## 3. File và đường đọc Kho

Native `search/read/search_count/read_group/export_data`, custom XLSX,
QR lookup và PDF labels lấy cùng domain source. `check_admin(env, records)` chỉ
chấp nhận model đã có extension và kiểm quyền caller; `is_admin(env)` giữ nghĩa
admin chính. Những caller không truyền nguồn vẫn bị từ chối như trước.

`ir.attachment`/`mail.message` được cộng read theo parent cụ thể; `ir.binary`
kiểm quyền parent bằng actor trước native token/sudo shortcut. Anonymous hoặc
actor bị thu hồi không lấy được file riêng qua đường đọc trực tiếp. Tệp công
khai của Kho bị chặn; token không thay cho quyền parent. Chưa mở upload/di chuyển
tệp hoặc cấp follower/assignee delegate; không suy rằng đã kiểm tải qua public
chỉ từ test model.

Ghi nhật ký thiết bị đi qua `message_post` của model cụ thể, kiểm actor có quyền
write trên parent và khóa thẩm quyền trước khi mở create message bằng Python
sentinel. Recipient filter admin gốc giữ nguyên. Không nhận author khác, tệp lồng
hoặc mở `mail.message.create` trực tiếp bằng context client. Không mở sửa/xóa
message lịch sử bằng delegation.

Trước mutation, adapter khóa thẩm quyền actor và các nguồn equipment/parent/
replacement, holder/reporter HR cùng version, department/company bằng row lock;
đọc lại cache trước kiểm actor. Chuyển phòng của người giữ đã commit trước làm
request cũ phải retry hoặc bị từ chối, không dùng snapshot phòng cũ để ghi tiếp.

## 4. Kiểm chứng và phần chưa chứng minh

Test mới `tests/test_equipment_scope.py` gồm baseline/cấp/thu, search/count/export,
own/stock denied, mixed bulk và sudo write denied, mixed parent, child reparent,
repair start/finish, native chatter create, private binary stream sau revoke và
đổi phòng holder sau khi đã đọc hồ sơ; S3 thêm kho rảnh chỉ đọc (không ghi/tệp/
chatter/nhãn/đổi máy từ kho) và gán/đổi/trả chỉ ngoài phòng (người nhận phòng
mình, máy phòng mình, version cũ, máy đã có chủ, đổi hỏng không đổi gì, replay,
thu hồi). Ruff/compile/diff là
kiểm source; kết quả Odoo/trình duyệt/multiworker/race/deploy phải ghi riêng trong
acceptance khi runner hoàn tất. Không dùng tài liệu này để tuyên bố AD01–AD09
đều PASS hoặc toàn bộ phân hệ đã có CRUD delegate.

`tests/test_guards_review.py` kiểm quyền HR đã có trước cấp vẫn sửa được chức danh
mô tả của đồng nghiệp cùng phòng trong và sau ủy quyền; self promotion vẫn bị
chặn. Test schedule chứng minh cấu hình nghiệp vụ có quyền từ trước vẫn CRUD
được; không cộng quyền config mới. Export test Kho dùng user đã có nhóm export
từ trước; delegation không tự cấp nhóm export.

`tests/test_reporting_scope.py` (S2) kiểm hồ sơ đã gửi ngoài phòng đọc được
còn nháp riêng, own baseline qua cấp/thu, không write/review/finalize thêm;
cây kế hoạch đóng khi có nhánh phòng mình; nghĩa vụ/chỉ đạo/dashboard cùng
scope; admin chính có vai trò cấu hình nhưng không thẩm quyền và không tự
cấp; task source, value tài chính và provenance carry không được cộng quyền
đọc; snapshot truy được chỉ đọc. Dữ liệu thử là synthetic; các ca NOT_RUN theo
chính sách không fixture trên main/server.
