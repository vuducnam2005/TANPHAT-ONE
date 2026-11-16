# HR-ACCOUNT-ROLE-001 — Danh tính và quản trị vai trò

12/11/2026. Quyết định trực tiếp của người dùng; bổ sung policy HEAD hiện hành,
không thay thẩm quyền nghiệp vụ của [ma trận KH-KD](KD_ACCESS_002_ROLE_MATRIX.md).

CHG-20261112-007: thao tác Đổi chức vụ chỉ có trong chi tiết nhân viên. Extension
trên `tp.kd.department.role` trong addon HR thêm unique index
`(company_id,department_id) WHERE active IS TRUE`; một vai trò chưa thu hồi giữ
vị trí dù account bị khóa hoặc ngày hiệu lực chưa tới/đã hết. Muốn bổ nhiệm
người khác phải hạ role cũ với reason/audit trước. Không sửa dữ liệu lịch sử
hoặc tự chọn người để hạ. Preflight phải không có scope active trùng trước upgrade.
Wizard preview/apply kiểm incumbent bằng ID công ty/phòng và báo tên bằng tiếng
Việt; snapshot nguồn quyền thêm các HEAD của phòng, fresh snapshot dùng đúng
environment/cursor mới. Unique index chặn direct provisioning/reactivation/race
kể cả khi snapshot cũ; superuser guard/audit hiện hành giữ. Job-only không cấp
role, không suy quyền từ tên chức vụ. Không cấp quyền nghiệp vụ phòng khác.

| Đường thao tác | Kiểm backend |
| --- | --- |
| Tạo user riêng | Admin có write HR, đúng công ty; khóa employee/resource; kiểm expected mapping; advisory login lock, kiểm cả inactive; create/map/audit trong savepoint |
| Mapping native/import/resource | Admin/HR thường không gán, gỡ, chuyển user hoặc đổi resource; không tin context RPC; chỉ sentinel Python nội bộ của action được phép |
| Link/unlink/invite native cũ | Bị AccessError; không chỉ ẩn UI |
| Tạo/đặt lại mật khẩu | Kiểm admin, company, tài khoản bảo vệ và expected mapping; xác thực native check_identity trước khi nhập thông tin mới; submit kiểm session identity TTL 600 giây phía server |
| Khóa/mở | Lý do, expected user, row locks, native active + HR flag + session revision; không hồi sinh phiên khi mở |
| Đổi vai trò | Admin đúng company, CRM team xác định bộ vai trò, lý do; preview digest gồm groups/implied/roles/assignment/grants và HR scope |
| Xác nhận | Row locks employee/resource/user; table locks nguồn quyền; so digest và snapshot đọc mới để bắt commit bị REPEATABLE READ che; atomic role/job/revision/audit |
| Hạ HEAD | Revoke role cùng scope; chặn HEAD ngoài scope, coordinator, live management grants, nhóm quản lý trực tiếp/kế thừa xung đột; giữ/liệt kê financial_read riêng |
| Đổi chức vụ hồ sơ (CHG006) | Cùng wizard hiện có, nhánh job; admin/write HR/đúng company; chức vụ active đúng company/phòng hoặc danh mục chung, lý do/preview digest/row locks employee-resource-user-version và snapshot mới; job+audit nguyên tử; không tạo account hoặc thay quyền |

CHG-20261112-006 đưa nút Đổi chức vụ ra list/đầu hồ sơ, tách job và quyền KH-KD
bằng lựa chọn rõ. `change_kind` được đưa vào digest; đổi nhánh/lựa chọn sau
preview không vượt qua xác nhận. Nhánh job không cần account và không sử dụng
sudo để sửa HR. Nhánh role vẫn dùng `_tp_account_admin(existing=True)` và mọi
guard HEAD trước đây; thêm/thu hồi quyền chỉ qua adapter cũ. Field khả dụng
chỉ phục vụ giao diện; RPC trực tiếp vẫn phải qua `_validate` phía backend.

Guard superuser của `tp.kd.department.role` giữ nguyên. Adapter admin chỉ sudo
hẹp bước role provisioning/audit; actor vẫn uid admin thật. Không tạo role
system song song, global unique user hoặc suy role từ chức vụ/tên phòng.
Native unique(user_id,company_id) bảo vệ nhiều công ty; superuser maintenance
vẫn có thể sửa mapping cho migration có kiểm chứng, không phải quyền RPC thường.

User mới chỉ `base.group_user`; chọn staff/head thêm duy nhất scoped group bằng
Command.link, không set toàn bộ groups. Staff chỉ nhận phân công/grant hiện có;
HEAD theo trách nhiệm động và policy hiện hành. Thăng/hạ không tự cấp ký, hiệu
lực, thanh toán, HR hoặc Settings. Chức vụ HR là dữ liệu riêng, đổi không cấp quyền.

Audit append-only role events + HR chatter trước/sau; không ghi mật khẩu. Quyền
đọc HR/private giữ native groups/rules. HEAD không được cấp HR để vào hồ sơ này.
Reset/role/lock bảo vệ admin/self/root/public/template/portal và user ngoài công ty.

CHG-20261112-005: form OWL nhập login/password/confirmation cùng màn hình;
password chỉ giữ trong bộ nhớ component và truyền qua RPC submit. Không có
field mật khẩu trên transient, không truyền password mới qua context hay
decorator `check_identity` (decorator native lưu tham số vào yêu cầu chờ).
Chỉ bước chuẩn bị với wizard ID và cờ đặt lại đi qua decorator. Submit không
tin dấu xác thực từ context RPC; phải có session HTTP vừa xác thực native.
Tạo user/password/mapping/audit và reset password/audit cùng savepoint; lỗi
lịch sử rollback cả mật khẩu. Hash và policy mật khẩu dùng native Odoo;
không thay cấu hình độ dài hiện hành. Hủy form không tạo user. Thông báo xác
thực, sai mật khẩu, validation và quyền thuộc luồng tài khoản dùng tiếng Việt.

Test fixture chỉ trên test; main không đổi user, password, mapping, groups,
role, assignment hoặc grant để chứng minh chức năng. Bằng chứng revocation trong
[acceptance](../demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md). Truy cập mới bị enforce;
file đã tải hoặc nội dung người dùng đã đọc trước thu hồi không thể thu lại.

## IDENTITY-ORG-001 — 12/11/2026

Tên chính thức dùng HR/resource; account partner phải là work_contact, mapping
user/employee duy nhất kể cả archived. Sync chỉ chạm partner đã xác minh; context
RPC không giả được sentinel Python. Self-service không đổi tên HR; ảnh theo quyền
native sync hai chiều. Customer partner và snapshot/audit cũ giữ nguyên. Không
fallback private_email. DTO workspace chỉ trả phòng caller, không HR private.

Chuyển phòng chỉ admin đúng company, preview/lý do/digest/locks/fresh snapshot/
savepoint/audit; revision kết thúc phiên cũ. Mặc định kết thúc active assignment,
project/KD grant, CRM member trong company; HEAD cũ luôn revoke có event. Kiêm
nhiệm phải chọn rõ, phân công được đánh dấu/lưu lý do. Nhóm quản lý riêng hoặc
tài khoản đa công ty gây block. Không tự cấp HEAD/tiền/HR/Settings; chức vụ không
cấp quyền. Việc chờ cần xác nhận bàn giao; owner/reviewer lịch sử giữ nguyên.

Write/import/version/context không đổi phòng current/future ngoài action; lịch
sử không trở lại scope current qua đổi ngày/active/xóa. Workspace KH-KD theo HR
primary có CRM mapping, HEAD hoặc kiêm nhiệm đã xác nhận; admin/platform manager
giữ quyền cũ. Backend lọc menu, kiểm action load native, overview/report; project/
export/attachment tiếp tục rule/capability hiện hữu. Grant tồn dư không mở
workspace. Xem [guide](../demo/IDENTITY_ORG_001_USER_GUIDE.md),
[acceptance](../demo/IDENTITY_ORG_001_ACCEPTANCE.md).


## HR-CORRECTION-008 — 12/11/2026

`hr.employee.unlink` chỉ chạy khi gọi từ `_tp_delete_mistaken` với sentinel
Python nội bộ; native Delete, RPC trực tiếp hay context do client gửi đều bị chặn.
Wizard/server action yêu cầu `base.group_system` cùng công ty, khóa advisory theo
công ty và `FOR UPDATE`, kiểm lại điều kiện ngay trước khi xóa, lô tất cả-hoặc-
không. Audit `tp.hr.employee.audit` chỉ ghi qua sentinel, người dùng chỉ đọc,
không FK tới hồ sơ nên còn sau khi xóa. Không xóa user/partner/tài liệu/nghiệp vụ;
binding “Delete employee” của `hr_timesheet` được gỡ. Mã nhân viên chỉ đổi qua
correction nội bộ có audit; cấp mã dưới khóa advisory, unique constraint giữ.
Xem [acceptance](../demo/HR_CORRECTION_008_ACCEPTANCE.md).

## HR-DELETE-010 — 12/11/2026 (DEC-042)

Thay luồng 008: `hr.employee.unlink` chỉ chạy khi context mang đúng đối tượng
sentinel Python nội bộ (so `is`, không phải giá trị client gửi được); native
Delete/RPC/`sudo()`/context giả đều bị chặn. Entry “Xóa vĩnh viễn nhân viên” chỉ
mở hộp thoại; quyết định nằm ở `tp_permanent_delete_execute`:

| Kiểm tra | Cách làm |
| --- | --- |
| Quyền | `base.group_system` và `hr.group_hr_manager`, mọi hồ sơ thuộc công ty đang chọn; không có cờ admin từ frontend |
| Phiên | `request.session.uid` phải trùng uid gọi; gọi ngoài HTTP bị AccessError |
| Mật khẩu | Mỗi yêu cầu cuối: native `_check_credentials` của chính admin trong native `_assert_can_auth` (đếm sai/cooldown chung của đăng nhập); không dùng 10 phút `check_identity`, không ghi `identity-check-last` |
| Bí mật | Mật khẩu chỉ trong state OWL và tham số RPC cuối; xóa khỏi state trước khi gửi/khi đóng; không transient/context/decorator/log/audit/URL; ô `current-password` ẩn mặc định |
| Đồng thời | Khóa advisory theo công ty, `FOR UPDATE` hồ sơ/resource/tài khoản; digest kế hoạch phải bằng preview và bằng dữ liệu commit (cursor read-only mới) |
| Toàn vẹn | Một transaction: khóa tài khoản (tùy chọn) → unlink → dọn chatter/tệp/xmlid qua ORM → audit; lỗi giữa chừng rollback toàn bộ; `request_id` + unique `(request_id, employee_ref)` chống xóa lặp |
| Quan hệ | Không gỡ FK, không cascade dữ liệu độc lập, không đổi owner/reviewer; dữ liệu độc lập chặn với model/số lượng/gợi ý; dòng nhập Excel chỉ bỏ liên kết |
| Tài khoản | Mặc định giữ; khóa chỉ khi admin chọn: inactive + cờ HR + tăng revision kết thúc phiên, tắt role/assignment/grant/CRM member trong công ty, gỡ scoped group. Không khóa/xóa root/admin/hệ thống/portal/chính mình/đa công ty ngoài phạm vi; không xóa user |

Audit `tp.hr.employee.audit` không FK, append-only (create/write/unlink chỉ qua
sentinel), lưu snapshot tối thiểu (mã, mã nguồn, phòng/chức vụ, tài khoản, phần
xóa/giữ, quyền thu hồi), không lưu mật khẩu hoặc toàn bộ hồ sơ cá nhân. Mã TP đã
xóa bị ValidationError nếu cấp/gán lại. Blob vật lý chỉ do GC native xử lý khi
không còn tham chiếu. Xem [acceptance](../demo/HR_DELETE_010_ACCEPTANCE.md).

CHG-20261112-012: current_version_id phải thuộc chính employee dù cùng phòng; hr.version.employee_id không được chuyển lịch sử sang người khác, createversion không kháccompany. Native initialbacklink chỉ khi version chưaowner/employee chưahistory; không contextflag. RegressionHR41 đạt trướcrestartmain; không đổi quyền/data thật.
