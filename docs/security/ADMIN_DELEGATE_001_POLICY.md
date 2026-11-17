# ADMIN-DELEGATE-001 — Quyền quản trị được ủy quyền

Ngày 17/11/2026. Source: [prompt](../prompts/CLAUDE_ADMIN_DELEGATE_001_AND_PUBLIC_FILES.md),
DEC-050. Phân loại: bảo mật, workflow quản trị, giao diện native. Kết quả runtime
và rollout nằm trong [acceptance](../demo/ADMIN_DELEGATE_001_ACCEPTANCE.md);
tài liệu này mô tả phạm vi source, không tự xác nhận PASS nghiệp vụ hoặc quyền pilot.

## Hai trục quyền độc lập

Quản trị chính là người nội bộ đang hoạt động có `base.group_system` hiện có.
Không suy luận từ login, tên hoặc UID; không cấp thêm superuser. Một tài khoản
bị khóa vẫn hiện nhãn quyền đã cấp nhưng không được thực thi request quản trị.

`tp.admin.delegation` là sổ cấp/thu riêng theo user và company. Cài addon không
cấp ủy quyền cho người thật, không thêm nhóm Odoo, vai trò HEAD, assignment,
grant tiền hoặc công ty. Chỉ Quản trị chính dùng nút Cấp/Thu hồi trong trang
Tài khoản & phân quyền của nhân viên. Modal bắt lý do và tái xác thực bằng
`check_identity` native; mật khẩu không đi vào ledger/chatter/source.

Ledger giữ user/company, trạng thái, người/thời điểm/lý do cấp và thu. Một
company chỉ có một dòng đang hiệu lực cho mỗi user. Không sửa danh tính ledger,
không xóa lịch sử; cấp lại tạo dòng mới. Public RPC không gọi được `_change`
hoặc dựng Python sentinel để ghi trực tiếp. Wizard chốt user đích lúc mở và
kiểm lại dưới khóa trước khi áp; audit và thay đổi nằm cùng savepoint.

## Nguồn phòng ban và quyền cộng thêm

Baseline là quyền Odoo đang hiệu lực, cộng thêm các nguồn **đã rà soát** ở
phòng khác. Không snapshot hoặc đóng băng quyền nghiệp vụ khi cấp. Các phòng
được bảo vệ được tính lại từ tất cả employee liên kết (kể cả alternate/archive,
phiên bản hiệu lực theo ngày), HEAD còn hiệu lực, assignment, project grant,
KD grant còn hạn, CRM team membership/team leader và reporting assignment còn hiệu lực.
Reporting responsibility toàn công ty/subject-only không rõ phòng đóng phần
thêm tại company đó. Không dùng `limit=1`, tên phòng,
tab/URL hoặc context frontend để chọn phòng.

Scope chưa có phòng, thiếu company, có responsibility không xác định được
phòng, giao thoa một trong các phòng của actor, hoặc công ty không có grant:
giữ baseline. Mọi department trong nguồn phải thuộc đúng company. Một record
mở từ reporting/HR không đổi nguồn sở hữu project/KH-KD của nó.

Ví dụ nhân viên KH-KD chỉ được hồ sơ đã phân công: trước cấp dùng baseline;
sau cấp vẫn dùng baseline cho toàn bộ hồ sơ KH-KD và trường tiền tại KH-KD.
Các adapter đã rà soát có thể mở dữ liệu ở phòng khác trong company được cấp.
Thu hồi bỏ phần thêm và giữ nguyên group/assignment/grant KH-KD gốc.

## Coverage và giới hạn source

| Miền | Nguồn kiểm phạm vi | Phần mở thêm / phần giữ baseline |
| --- | --- | --- |
| HR metadata native | `hr.employee.current_version_id.department_id`, company | Thêm đọc hồ sơ ngoài phòng; field groups HR/private/wage giữ nguyên. Không cấp nhóm HR để làm form hiện đủ trường. |
| HR account dialog | Employee/version hiệu lực, mọi identity của target, mọi company của target | Tạo tài khoản riêng, khóa/mở, reset qua wizard có kiểm scope và recent identity; không link user có sẵn, không sửa group tùy ý. |
| HR hồ sơ ngoài phòng | Cùng checker target và snapshot employee/version/resource | Modal gắn tại chi tiết cũ: tạo hồ sơ không tài khoản, sửa tên/contact/chức danh mô tả, lưu trữ hồ sơ chưa có tài khoản; lý do và chatter. Không cấp role, đổi phòng hoặc xóa vật lý. |
| HR role/transfer/identity/import | User/employee/version/resource và cơ cấu phòng | Quy trình thay chức vụ, chuyển phòng, cấp vai trò và import vẫn Quản trị chính; delegate không được dùng sudo để vượt guard. |
| Projects/tasks/KH-KD/contracts | Project và department trên header/source/parent | Adapter trong `models/business_scope.py`; từng thao tác phải giữ workflow/state/version. Xem acceptance cho ca đã chạy; không mặc định mọi CRUD được mở. |
| Reporting | Department và toàn bộ nguồn tổng hợp | Các nguồn chưa chứng minh độc lập với phòng của actor giữ baseline; company consolidation và xác nhận tài chính không tự mở. |
| Kho | Custody/source/target của thiết bị và chứng từ | Adapter cụ thể trong `models/equipment_scope.py`; stock/shared/unknown/import và thao tác chưa rà soát giữ baseline. Không đổi `common.is_admin` thành delegate toàn cục. |
| Chatter/files/export/count/search/read_group | Quyền nguồn thực | Native quyền nguồn và adapter theo miền; không public hóa attachment, không mở generic sudo file route. Các đường chưa có bằng chứng ghi NOT_RUN. |
| Model khác | Không có adapter rõ | Giữ nguyên baseline; không có global `has_group`, `_check_access` hoặc core patch. |

HR field groups là ranh giới có chủ ý: không cấp `hr.group_hr_user/manager`
cho delegate vì như vậy có thể mở dữ liệu riêng hoặc lương ngay trong phòng
của actor. Chức năng chưa được adapter hóa/kiểm thử không được ghi là quản
trị toàn hệ thống. Danh sách cụ thể và kết quả từng model/route theo acceptance.
Delegate chưa có nhóm HR dùng list/form/search native an toàn trên cùng action
và model nhân viên; người đã có nhóm HR giữ view gốc. Bộ view chỉ yêu cầu metadata,
liên hệ công việc, tình trạng tài khoản và nhãn quản trị mà caller được đọc;
không yêu cầu loại hình lao động, lương hoặc thông tin riêng tư. List tái sử dụng
`tp_hr_table`/SearchModel, count/pager/export và tiêu chí lọc theo field được cấp.

## Chặn nâng quyền

Guard backend áp dụng cả khi custom caller `.sudo()` vì actor vẫn là `env.uid`.
Mọi delegate bị chặn ghi user/group/company/employee/resource link; tự nâng chức vụ,
phòng, manager, phiên bản hiện hành/tương lai; lệnh quan hệ lồng; create/clone
identity; assignment/project grant/KD grant/HEAD/team membership; cơ cấu phòng;
security ACL, server action và system config. Thao tác qua HR role/import
không nhận sentinel tài khoản. Client context boolean không giả được object
Python nội bộ. Thông tin cá nhân của chính mình vẫn theo allowlist sẵn có
trong `tp_hr_workspace.models.my_profile`; password/MFA self-service native
giữ baseline, không cho quản lý credential của tài khoản khác qua đường này.

Home lấy capability live mỗi lần tải menu khi addon được cài, chỉ mở các
placeholder Đang phát triển cho delegate. Không đổi `user.isSystem`; Cài đặt
và Quản lý ứng dụng không tự xuất hiện. Menu backend bổ sung đúng whitelist
HR danh sách nhân viên, KH-KD danh sách dự án, Báo cáo của tôi, và danh sách
thiết bị có quyền đọc. Không tự mở dashboard admin, import hoặc config;
khi model không có phạm vi đọc thì không thêm entry đó. Các nút tài khoản
trên form cũ dùng capability theo record, giữ các nút role/transfer admin-only.

Adapter tài khoản kiểm target lại ngay trước thao tác. Cấm actor tự quản lý,
user hệ thống qua XMLID, portal, system/ERP/platform/HR manager, HEAD, delegate
khác và user có ACL ghi security/system (trừ ACL native chỉ sửa chính mình).
Mọi employee/alternate identity và company của target phải ngoài phòng được
bảo vệ và có grant. Không cho A cấp quyền cho B để B đổi quyền trở lại cho A.
Reset qua `action_reset_password/get_reset_password_link` thông thường không
là đường thay thế cho dialog đã kiểm. Partner mapping/token signup cũng được
chặn; chỉnh partner của tài khoản đặc quyền không vượt được guard.

## Thu hồi và đồng thời

Quyền thêm đọc ledger bằng SQL mỗi request, ngoài cache baseline của
`_access_domain`. Các override chỉ trên model đã rà soát; quyền Odoo bình thường
vẫn lấy từ `super()`. Không dựa vào một deny group (ACL cộng quyền và global
restriction là AND trên Odoo20).

Request ghi dùng shared PostgreSQL transaction advisory lock theo user,
đồng thời khóa đọc ledger/user row. Cấp/thu và thay nguồn scope do Quản trị
chính dùng khóa exclusive cùng namespace, tăng `tp_admin_scope_revision`
trên user. Nếu request chờ giữ snapshot REPEATABLE READ cũ, khóa row phát sinh
serialization failure để cơ chế retry Odoo đọc lại quyền đã commit. Request
ghi đã commit trước thu hồi không tự đảo; dữ liệu đã tải về không thể thu hồi.
Đổi phòng/công ty/cơ cấu team CRM khóa các user chịu ảnh hưởng; đổi công ty,
lưu trữ hoặc xóa phòng ban khóa mọi delegate đang có ledger hiệu lực vì nhiều
nguồn trách nhiệm cùng tham chiếu cơ cấu này.

Thu hồi invalidate local access/record/menu cache và registry signaling; raw
ledger vẫn là điều kiện backend ở request tiếp theo trên worker khác. Không
xóa nhóm, assignment, grant nghiệp vụ; không thay mật khẩu hoặc khóa tài khoản
để giả làm thu hồi. Kiểm multiworker/race phải có runtime evidence riêng, không
dùng mô tả khóa hoặc static scan làm kết quả test.

## Kiểm thử

`tests/test_delegation.py`: cấp hai phòng, baseline nhóm/danh tính giữ nguyên,
ledger append-only, main-only provisioning, phòng kiêm nhiệm và unknown scope,
direct/sudo/context/relational/version/import escalation, reauth bắt buộc,
target account được bảo vệ, khóa/reset/thu hồi ở wizard đã mở.

`tests/test_hr_profile.py` thêm ca create/edit/archive ngoài phòng, giữ identity,
chặn self/đổi phòng/thu hồi/target đã có account khi archive và snapshot lỗi thời.
Context từ client không được tái sử dụng partner/group/resource/contact khi
tạo tài khoản hoặc hồ sơ. Native tạo resource/version/work contact chỉ nhận
ngoại lệ Python nội bộ cho lần liên kết ban đầu của hồ sơ mới, không có account.
Guard kiểm giá trị sau `default_get`, gồm `default_employee_id`, `default_user_id`
và các link danh tính; không chỉ kiểm các khóa xuất hiện trong `vals`. Cấp nguồn
trách nhiệm qua user mặc định cũng khóa và tăng revision của đúng user đích.
Test chỉ actor giả trên `tp_tanphat_test`/18079 do một runtime writer điều phối.

Static Python compile/Ruff và Odoo tests/native browser được ghi riêng trong
acceptance. Chưa có kết quả runtime hoặc browser thì ghi NOT_RUN; không dùng
workflow hash checker để kết luận quyền nghiệp vụ đúng. Main/server không cấp
cho người thật nếu người dùng chưa chỉ rõ tài khoản đích.
