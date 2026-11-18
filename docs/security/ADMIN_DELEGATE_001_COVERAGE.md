# ADMIN-FULL-001 — Bản đồ phân quyền, phạm vi và điểm kiểm soát Backend

Cập nhật: 18/11/2026 (`tp_admin_delegation` **20.0.2.0.0**, thay thế bản đồ giới hạn phòng ban của `ADMIN-DELEGATE-001/002` theo [DEC-053](../DECISIONS.md) và [DEC-054](../DECISIONS.md)).
Đọc cùng [chính sách](ADMIN_DELEGATE_001_POLICY.md) và [nghiệm thu](../demo/ADMIN_FULL_001_ACCEPTANCE.md).

## 1. Kiến trúc nhóm và nguồn thẩm quyền

| Thành phần | Định danh kỹ thuật | Vai trò trong `20.0.2.0.0` |
| --- | --- | --- |
| Nhóm Quản trị gốc | `tp_admin_delegation.group_original_admin` | Seed `noupdate="1"` cho `base.user_admin` (và admin hệ thống gốc trước migration, không thuộc `tp.admin.delegation`). Không nằm trong `implied_ids` của bất kỳ nhóm nào. Nguồn xác thực `_tp_is_original_admin()`. |
| Nhóm Quản trị viên toàn hệ thống | `tp_admin_delegation.group_full_admin` | Gán/gỡ nguyên tử theo sổ `tp.admin.delegation`. Kế thừa `base.group_system`, `tp_core.group_manager`, `hr.group_hr_manager`, `project.group_project_manager`, `sales_team.group_sale_manager`, `hr_timesheet.group_timesheet_manager`, `maintenance.group_equipment_manager` và các nhóm quản trị phân hệ đã cài (`account`, `spreadsheet_dashboard`, `hr_expense`, `product`). |
| Sổ cấp/thu & Migration | `tp.admin.delegation` (`models/delegation.py`) | Đọc trực tiếp qua SQL (`_tp_has_live_admin_grant`) độc lập với `base.group_system`. Lưu người cấp, thời điểm, lý do cấp/thu và mốc `migrated_at`. Hỗ trợ migration idempotent `_migrate_admin_full_001()`. |
| Kiểm soát phiên mở sẵn | `res.users.tp_admin_scope_revision` | Thuộc `_get_session_token_fields()`; tăng mỗi lần cấp, thu hồi hoặc nâng cấp quyền, làm hết hạn ngay session token cũ trên mọi tab đang mở. |

## 2. Bản đồ phân hệ cho Quản trị viên được cấp (`group_full_admin`) so với Quản trị gốc

| Phân hệ / Model | Quyền của Quản trị viên được cấp | Ranh giới / Workflow được giữ |
| --- | --- | --- |
| Trang chủ & Điều hướng (`tp_web_home`, `ir.ui.menu`) | `is_system=True`, `delegated=False`; thấy đầy đủ toàn bộ thẻ phòng ban, Nhân sự, Kho, Báo cáo, Công cụ cá nhân và thanh công cụ `Cài đặt` / `Quản lý ứng dụng` / `Tất cả ứng dụng` giống Quản trị gốc | `can_manage_delegation=False` |
| TP HR (`hr.employee`, `tp.hr.workspace`, `tp.hr.account.wizard`, `tp.hr.role.wizard`) | Toàn quyền xem/tạo/sửa/lưu trữ/xóa vĩnh viễn (có xác minh mật khẩu) trên **mọi phòng ban kể cả phòng mình**; dùng view gốc (`1631`/`1633`/`1632`), đọc/ghi `mobile_phone`/trường riêng/hợp đồng, xuất XLSX; quản lý tài khoản thường, đổi chức vụ, chuyển phòng ban, bổ nhiệm/hạ quyền KH-KD | Ẩn và chặn nút `Cấp/Thu hồi quyền quản trị viên`; chặn sửa/khóa/reset tài khoản Quản trị gốc và Quản trị viên khác; giữ nguyên chức danh/phòng ban HR cá nhân của người nhận |
| KH-KD / Dự án / Hợp đồng (`project.project`, `project.task`, `crm.lead`, `tp.contract`, hồ sơ KD) | Toàn quyền ngang Quản trị gốc trên mọi phòng ban; 6 rule `group_scoped_staff` (`data/full_admin_access.xml`) và `crm.lead._kd_scoped()` (`models/business_scope.py`) tự bỏ giới hạn nhân viên cũ khi giữ `base.group_system` | Giữ nguyên state machine, kiểm tra phiên bản và điều kiện nghiệp vụ áp cho cả Quản trị gốc |
| Kho thiết bị (`tp_equipment`) | Toàn quyền trên cả 55 hồ sơ thiết bị (gồm phòng mình, phòng khác, kho chung, dùng chung), đề xuất mua, phiếu bàn giao, kiểm kê, lô nhập, nhãn QR, xuất Excel | Giữ nguyên quy tắc DEC-047 chỉ gán/đổi máy rảnh trong kho chưa có người giữ và khóa `FOR UPDATE NOWAIT` |
| Báo cáo (`tp_reporting`) & Chấm công (`tp_hr_attendance`) | Cùng quyền cấu hình và quản lý như Quản trị gốc (`group_reporting_config`, `hr.group_hr_manager`) | Giữ nguyên quy tắc cấm tự cấp assignment báo cáo hoặc tự duyệt công cho chính mình |
| Cài đặt & Ứng dụng (`res.config.settings`, `ir.module.module`) | Mở và lưu Cài đặt nghiệp vụ; xem danh sách và chi tiết các Ứng dụng đã cài | Chặn cài/nâng cấp/gỡ/nhập module, sửa tham số bảo mật cốt lõi, sửa nhóm quản trị/ACL/server action/cron/XMLID/view (chỉ dành cho Quản trị gốc theo DEC-054) |
| Nhân viên thường (`base.group_user`) | Không thay đổi | Giữ nguyên `HR-DELEGATE-FIX-001`: ẩn và chặn `mobile_phone`/thông tin riêng của người khác trên cả `hr.employee` và `hr.employee.public`; giữ tự sửa Hồ sơ cá nhân |
