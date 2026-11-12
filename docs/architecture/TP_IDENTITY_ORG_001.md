# IDENTITY-ORG-001 — Danh tính và chuyển phòng ban

12/11/2026, yêu cầu triển khai trực tiếp của người dùng. Baseline CHG-20261112-010;
giữ hồ sơ/sidebar/compact007, tài khoản cá nhân và policy một HEAD chưa thu hồi.
Native Odoo/custom addons; không commit/push. Technical, business, visual và pilot riêng.

## Nguồn dữ liệu trước triển khai

| Thông tin | Model/field nguồn | Nơi hiển thị | Ai sửa | Cập nhật |
| --- | --- | --- | --- | --- |
| Mã/danh tính | hr.employee.id/tp_employee_code/resource_id/user_id | HR, đối chiếu | Quy trình tài khoản admin | Mapping ID, không ghép theo tên |
| Tên chính thức | hr.employee.name → resource.resource.name | HR/user/partner/navbar/KH-KD | HR/admin; self-service không đổi tên chính thức | Đồng bộ đúng partner của user đã liên kết |
| Ảnh | hr.employee.image_1920 và res.users.partner_id.image_1920 | HR/preferences/navbar/assignee | HR hoặc chính user theo quyền native | Hai chiều; sentinel nội bộ tránh vòng lặp; xung đột cũ cần chọn |
| Phòng/chức vụ | hr.employee.current_version_id → hr.version.department_id/job_id | HR/home/workspace | Admin qua preview chuyển phòng | Hiệu lực ngay, giữ version lịch sử, không dùng context lịch sử làm quyền |
| Email/phone công việc | hr.employee.work_email/work_phone ↔ work_contact_id theo native | HR/profile | HR/admin hoặc quyền native cho công việc | Không đổi login; không chép private_email/private_phone |
| Tài khoản/auth | res.users.id/login/password/MFA | Login/preferences/HR | Admin qua luồng đã có | Giữ ID/login/password/MFA khi đổi tên/phòng |
| Quyền | group_ids, tp.kd.department.role, tp.project.assignment/grant, tp.kd.grant, crm.team | Native/data/export/file | Admin đúng company | Thu hồi theo scope, giữ lịch sử, preview quyền riêng |

Quan sát source: employee.name related resource.name; native user write đồng bộ name/email
và chỉ image khi employee chưa có image. Native tạo employee có thể lưu SVG fallback
vào image_1920; không coi mọi giá trị image là ảnh thật. work_contact khác user.partner
phải được đối chiếu, không ghi partner khách hàng. Menu KH-KD hiện dùng group nền.

## Acceptance đã lập trước code

Tất cả thao tác thay quyền dùng fixture giả trên tp_tanphat_test/18079, một writer.

1. Cùng employee/resource/user/partner ID; HR rename cập nhật user/navbar, giữ login/auth;
   self-service không đổi tên chính thức; ảnh hai chiều và cache; trùng tên không ghép,
   partner khách hàng giữ nguyên, không mở HR private.
2. Admin tại Thông tin công việc → Chuyển phòng ban: chọn đích/role/job/lý do,
   preview đầy đủ phòng/workspace/role/assignment/grant/CRM/quyền riêng/công việc,
   xác nhận nguyên tử. Nhân viên thường không tự chuyển hoặc tự cấp quyền.
3. Vào KH-KD default staff, không HEAD/tiền/HR/Settings, chỉ assignment/grant được cấp;
   không assignment là rỗng. Ra KH-KD thu hồi HEAD/scope/grants/team theo preview,
   giữ owner/reviewer/creator và lịch sử; việc cần bàn giao được nêu rõ/giải quyết.
4. Không account vẫn chuyển, không tạo user; tạo account sau áp đúng workspace.
   HEAD đích có incumbent thì chặn có tên, không tự thay. Kiêm nhiệm phải có nguồn
   cấp riêng được xác nhận rõ; grant sót không tự được coi là kiêm nhiệm.
5. Home/app switcher/menu/sidebar/action trực tiếp cùng scope; admin giữ công cụ;
   phòng chưa triển khai hiển thị tên đúng và Đang phát triển, không cấp KH-KD.
6. Current/historical/future hr.version khác nhau; direct/import/self-service/context
   không bypass chuyển phòng. Không xóa lịch sử công tác hoặc đổi công ty.
7. Stale preview, thay lựa chọn, race 2 admin, retry/double click và lỗi giữa luồng:
   reject/rollback, không duplicate role/audit. Audit actor/reason/before/after.
8. Request kế tiếp của tab cũ enforce quyền mới; reload/relogin rõ ràng, không replay
   mutation; menu/avatar cache đúng và không lẫn tài khoản.
9. Odoo relevant tests/Ruff/XML/assets/HOOT và Playwright desktop/mobile, sidebar007
   giữ, console0; ảnh trước–sau cùng actor/profile/viewport. Không nhận mobile giả lập
   là thiết bị thật hoặc tự review là audit độc lập.
10. Backup DB+filestore+source/config, restore canonical test kiểm chứng; chỉ áp source/
    migration đã kiểm lên18069 khi test/restore đạt. Không DB thứ3/restoretest→main;
    reconciliation người thật chỉ preview theo ID, xung đột giữ nguyên chờ admin.

## Bằng chứng và trạng thái

CHG-20261112-011: đã kiểm và áp18079/18069, HR20.0.1.7.0. HR source cuối40tests,
HEAD/KH-KD sau restore109tests0failed0errors; HOOT21/29, browserfixture7nhóm và
smokesạch5nhóm mỗi cổng đạt0errors. Restore596rowsets/653blobrefs/429sequence.
Main40employee/27user/7mapping;7identity reconciliation theo ID,4account rename,
1ảnh thật account→HR và6fallback thống nhất;0mismatch/conflict/pending. Auth,
department/role/grant thật giữ;88rowsets và627nonassetblob bảo toàn với delta
danh tính có phép tách rõ. Source209file seal, rollback16fileđổi/9filemới.

Historical department edits không thay current scope; current version có lịch
sử khác phòng không được xóa/đổi ngày/active để làm hồi scope cũ. Future khác
phòng và account đa công ty bị block để review riêng. Transfer giữ short table
locks trên nguồn quyền/việc chờ để chặn phantom; có thể chờ writer khác, chưa
load test. Mapping nhiều employee cho một user hoặc shared partner khác chưa
tự reconciliation. Không đồng bộ private_email vào work contact.

[Acceptance/evidence](../demo/IDENTITY_ORG_001_ACCEPTANCE.md),
[guide admin](../demo/IDENTITY_ORG_001_USER_GUIDE.md),
[deploy/rollback](../../ops/runbooks/IDENTITY_ORG_001_DEPLOY_AND_ROLLBACK.md).
Evidence private `.local/identity-org001/`; status/changelog là trạng thái bàn giao.
Tự review do subagent model không khả dụng; visual/business/pilot do người dùng,
mobile giả lập. Không commit/push hoặc restoretest→main.


CHG-20261112-012: thêm owner guard cho current_version_id, cấm rebind lịch sử giữa nhân viên/company sai khi tạo version. Chỉ giữ native back-link lúc tạo employee từ version chưa có owner, không dùng context client. HRfilter41tests0failed0errors/clean5mỗi cổng/preservation đạt, source209seal và restartmain sau backup080056033059Z. Không schema hoặc datachange; kết quả011 vẫn giữ.
