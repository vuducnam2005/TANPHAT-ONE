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

Phê duyệt technical độc lập, business acceptance và pilot vẫn riêng. NATIVE-DATA-003 phải giữ **PARTIAL_WITH_GAPS** khi transition bắt buộc này chưa được mở và kiểm đúng scope.
