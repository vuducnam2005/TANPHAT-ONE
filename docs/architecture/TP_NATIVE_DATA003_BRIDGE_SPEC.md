# NATIVE-DATA-003 — bridge CRM → TP Projects

02/11/2026. Đặc tả batch B3, theo prompt đã được người dùng giao thực thi trực tiếp.

Một cơ hội có tối đa một dự án thực hiện; nhiều cơ hội có thể tham chiếu cùng dự án. `crm.lead.tp_project_id` là FK tùy chọn tới canonical `project.project`, `copy=False`, `ondelete=restrict`, `check_company=True`. Không chuyển đổi, tạo dự án, sao chép khách hàng, đổi state hay thêm capability. Lead pipeline chưa có dự án giữ null. Khách hàng thương mại và company phải trùng; sửa project cũng phải bảo toàn điều kiện này.

Quyền là giao của CRM native và project hiện hành: lead có liên kết chỉ được đọc/ghi khi actor có quyền tương ứng trên CRM và quyền đọc project; lead chưa liên kết giữ native scope. Global rule có điều kiện quan hệ áp dụng CRUD. Explicit create/write kiểm quyền đọc target, gồm default context; constraint chỉ giữ integrity company/customer/managed vì Odoo20 chạy constraint sudo. Domain lựa chọn không thay backend security. Nhãn UI “Dự án thực hiện”, không có smart button/ngược từ project tới CRM, invoice hoặc hợp đồng. Việc đọc project không cấp quyền CRM hay tiền.

Kiểm bắt buộc: actor CRM có/không assignment; project reader không CRM; đọc trực tiếp, search/name_search/read_group, view/field selection; ghi/xóa FK; company/customer khác; thay customer project; copy không nhân liên kết; không tự phát sinh project/grant. Model/API React/OpenAPI, managed-task policy và state nghiệp vụ không đổi.

Cài/upgrade đúng addon trên clone trước; schema DDL/module install là transaction riêng với batch dữ liệu. Rollback an toàn là clear đúng bốn FK fixture còn hợp lệ rồi uninstall addon (clone đã kiểm); không xóa lead/project. Không full-restore dev nếu đã có ghi mới. Bằng chứng và trạng thái thực tế nằm trong runbook NATIVE-DATA-003, không xem tài liệu này là kết quả test.
