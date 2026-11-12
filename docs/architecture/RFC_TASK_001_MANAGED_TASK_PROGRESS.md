# RFC TASK-001 — Nhân viên cập nhật tiến độ task có quản lý

02/11/2026, phát hiện trong NATIVE-DATA-003 / CHG-20261102-014. **PROPOSED — chưa có quyết định policy hoặc implementation.** Đây là giới hạn còn lại của S1, không phải yêu cầu bỏ scope managed.

## Tái hiện đã kiểm

Dev `tp_tanphat_dev`, native18069; user giả Long21/employee16, assignment Cầu Sông Xanh/project8, assignee task trong54–61. `task.with_user(long).read(['name'])` thành công. `task.with_user(long).write({'state': '1_done'})` trả `AccessError` từ policy managed task hiện hành. Actor nhập own timesheet đúng project/task/employee được phép (rollback probe), expense submit theo native được phép. Không dùng sudo/Platform Manager, không chuyển project unmanaged. `scripts/native_data003_checks.py` giữ regression cho denial này.

## Quyết định cần có

Owner/điều phối xác nhận actor nào được cập nhật tiến độ ở state nào, scope company/project/department/assignment/assignee, trường được sửa, transition/reason/history/notification và concurrent-update policy. Cần phân biệt cập nhật tiến độ với đổi project, người được giao, company, liên kết tài chính, nội dung gốc hoặc xóa task. Assignment reader không tự trở thành quyền ghi; chức danh project manager không tự cấp capability.

Đề xuất để review: action backend hẹp cho một transition đã chốt, field allowlist và kiểm actor/scope/version; chưa chọn API hoặc capability mới ở lượt này. Không triển khai generic assignee-write trên mọi field. Giữ global scope và quyền hợp đồng/tiền/attachment tách riêng.

## Kiểm trước khi chấp thuận batch code

- Assigned actor hợp lệ làm đúng transition; actor không assigned/assignment hết hạn/khác project/company bị từ chối qua ORM, direct RPC và API nếu có.
- Không lách bằng create/write/import/context/default hoặc gộp `state` với project/assignee/company/financial fields; không bỏ global rule bằng group OR.
- Invalid transition, thiếu lý do hoặc version cũ rollback không side effect; history đúng actor, retry không trùng.
- Reader khác vẫn chỉ đọc; quản lý và nhân viên có action khác nhau nếu policy yêu cầu; name_search/read_group/export/attachment không mở thêm dữ liệu.
- Test clone trước dev, migration/rollback có version, giữ task/time/expense hiện có; UI chỉ trình bày `allowed_actions` backend khi API được chốt.

## Đề xuất cụ thể để quyết định (NATIVE-STABILIZE-001, 05/11/2026)

**Trạng thái không đổi: PROPOSED.** Batch CHG-20261105-002 kiểm lại trên clone cô lập `tp_tanphat_stab001_20261105` rằng denial vẫn đúng; không mở quyền, không đổi test denial thành allow, không sửa source `tp_project`.

Nguồn hiện hành được đọc: `custom_addons/tp_project/security/ir.access.csv` chỉ cho `tp_core.group_manager` ghi task thuộc project managed (`task_platform_write_scope`); `tp.project.assignment.role` có `reader`/`coordinator` nhưng chưa role nào cấp quyền ghi; `tp.project.grant` chỉ có capability tài chính/hợp đồng. `project.task.state` native có `01_in_progress`, `02_changes_requested`, `03_approved`, `04_waiting_normal`, `1_done`, `1_canceled`.

Phương án đề xuất (chỉ để review, chưa triển khai):

| Hạng mục | Đề xuất | Lý do |
|---|---|---|
| Hình thức | Một method backend hẹp trên `project.task`, ví dụ `action_tp_report_progress(target_state, expected_write_date, reason=None)`; không mở rule `cud` cho assignee | Giữ global write scope; mọi kiểm nằm ở backend, UI chỉ gọi action |
| Actor | User nằm trong `task.user_ids` **và** có `tp.project.assignment` active trên `task.project_id` (role bất kỳ), cùng company | Assignment là phạm vi đọc hiện có; việc "được giao task" là điều kiện ghi tối thiểu |
| Transition | `01_in_progress`/`02_changes_requested`/`04_waiting_normal` → `1_done`; tùy quyết định thêm `1_done` → `01_in_progress` (mở lại, bắt buộc lý do) | Không chạm `03_approved` (bước duyệt) và `1_canceled` (hủy) |
| Field | Chỉ `state` (và message lý do). Cấm đổi project, assignee, company, stage, deadline, mô tả, liên kết tài chính, xóa | Phân biệt cập nhật tiến độ với sửa nội dung task |
| Ghi | Sau khi kiểm actor/scope/state/version trong method, ghi đúng một field `state` với quyền nâng có giới hạn; `message_post` ghi actor thật và lý do | Mẫu workflow Odoo: kiểm tường minh rồi ghi hẹp; không `sudo` cho đọc/search |
| Đồng thời | So `expected_write_date` với bản ghi; lệch thì `UserError`, không ghi | Tránh ghi đè cập nhật của quản lý |
| Idempotent | Gọi lại cùng `target_state` khi task đã ở state đó: không ghi, không thêm history | Retry an toàn |
| Thông báo | Chỉ chatter của task (follower hiện có); chưa thêm email/activity mới | Email ngoài cần quyết định riêng |
| Ý nghĩa | "Hoàn tất công việc" ≠ nghiệm thu/thanh toán (đúng caveat dashboard điều phối) | Không suy ra bước BASE/hợp đồng |

Câu hỏi mở cần owner/điều phối trả lời trước khi viết test-code:

1. Assignee có được tự đánh dấu `1_done` hay chỉ chuyển sang chờ duyệt (`04_waiting_normal`) để quản lý chốt?
2. Role `coordinator` có được cập nhật task của người khác trong cùng project không? Nếu có, phạm vi department nào?
3. Có cho mở lại (`1_done` → `01_in_progress`) không, ai được mở, lý do có bắt buộc không?
4. Có cần khóa nhập timesheet sau khi task `1_done` không?
5. Assignment hết hạn/inactive giữa chừng: chặn ngay (đề xuất) hay cho phép hoàn tất việc đang làm?
6. Ai nhận thông báo (người giao, quản lý project, follower) và qua kênh nào?
7. Có cần API REST cho action này hay chỉ native UI (DEC-030 ưu tiên native)?

Khi có trả lời, batch code phải viết test denial/allow theo danh sách kiểm bên dưới trước khi sửa rule; `scripts/native_data003_checks.py` giữ regression denial cho đến khi policy được chốt và thay bằng test của transition mới.

Phê duyệt technical độc lập, business acceptance và pilot vẫn riêng. NATIVE-DATA-003 phải giữ **PARTIAL_WITH_GAPS** khi transition bắt buộc này chưa được mở và kiểm đúng scope.
