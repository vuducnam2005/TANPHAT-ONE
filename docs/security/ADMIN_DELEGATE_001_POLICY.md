# ADMIN-FULL-001 (thay thế ADMIN-DELEGATE-001/002) — Chính sách Quản trị viên toàn hệ thống & Ngoại lệ chỉ Admin gốc cấp quyền

Cập nhật: 18/11/2026 (`tp_admin_delegation` **20.0.2.0.0**).
Nguồn quyết định: [DEC-053](../DECISIONS.md), [DEC-054](../DECISIONS.md), [prompt ADMIN-FULL-001](../prompts/CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md).
Kết quả kiểm thực runtime và giới hạn nằm tại [ADMIN_FULL_001_ACCEPTANCE.md](../demo/ADMIN_FULL_001_ACCEPTANCE.md).

> **Lưu ý quan trọng cho mọi phiên AI:** Từ ngày 18/11/2026 (`DEC-053` / `DEC-054`), mô hình *"phòng mình giữ quyền nhân viên, chỉ quản trị phòng khác"* của `DEC-050` / `ADMIN-DELEGATE-001/002` **đã ngừng sử dụng**. Tài khoản được cấp quản trị là **Quản trị viên toàn hệ thống** trên mọi phòng ban (gồm cả phòng của chính họ), với **ngoại lệ duy nhất ở backend (DEC-054): chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên**.

## 1. Tách biệt hai trục thẩm quyền ở Backend

1. **Quản trị gốc (`_tp_is_original_admin`):**
   - Là tài khoản nội bộ đang hoạt động (`active=True`, `share=False`), có `base.group_system`, không có grant đang hiệu lực trong `tp.admin.delegation`, và thuộc nhóm nguồn độc lập `tp_admin_delegation.group_original_admin` (`noupdate="1"`, seed cho `base.user_admin` và các admin hệ thống gốc trước migration; **không bao giờ** nằm trong `implied_ids` của `base.group_system` hay `group_full_admin`).
   - Không suy luận từ login, tên hiển thị hay UID cứng.
   - Là actor **duy nhất** được phép:
     - Cấp hoặc thu hồi quyền Quản trị viên toàn hệ thống (`tp.admin.delegation`, `tp.admin.delegation.wizard`, `action_tp_grant_admin`, `action_tp_revoke_admin`).
     - Quản lý nhóm quyền bảo mật/quản trị (`res.groups`, `res.groups.privilege`), ACL (`ir.access`), server action Python (`ir.actions.server`), lịch tự động (`ir.cron`), cài/nâng cấp/gỡ/nhập module (`ir.module.module`, `base.module.*`, `base.import.module`), metadata/view hệ thống (`ir.model*`, `ir.ui.view`, `ir.asset`, `ir.ui.menu`), và tham số bảo mật cốt lõi (`database.secret`, `web.base.url*`, `auth_*`, `tp_admin*`).

2. **Quản trị viên toàn hệ thống được cấp (`_tp_is_granted_admin`):**
   - Được Quản trị gốc cấp qua sổ `tp.admin.delegation` (`state='active'`) có lý do và xác thực lại danh tính (`@check_identity`).
   - Nhận duy nhất một nhóm vai trò được quản lý `tp_admin_delegation.group_full_admin`, nhóm này kế thừa (`implied_ids`) đầy đủ bộ nhóm quản trị hệ thống và phân hệ giống hệt admin hiện tại:
     - `base.group_system` (kéo theo `base.group_erp_manager`, `base.group_allow_export`, `base.group_partner_manager`, `product.group_product_manager`, `tp_reporting.group_reporting_config` → `tp_reporting.group_reporting_user`, v.v.)
     - `tp_core.group_manager`
     - `hr.group_hr_manager` (kéo theo `hr.group_hr_user`)
     - `project.group_project_manager`
     - `sales_team.group_sale_manager`
     - `hr_timesheet.group_timesheet_manager`
     - `maintenance.group_equipment_manager`
     - Cùng các nhóm quản trị phân hệ đã cài (`account.group_account_manager`, `spreadsheet_dashboard.group_dashboard_manager`, `hr_expense.group_hr_expense_manager`).
   - **Toàn quyền quản trị nghiệp vụ trên mọi phòng ban, kể cả phòng của chính mình:** Trang chủ thống nhất, TP HR (tổng quan, danh sách/chi tiết gốc, `mobile_phone`/trường riêng/hợp đồng/tài liệu, tạo/khóa/mở/reset tài khoản thường, đổi chức vụ, bổ nhiệm/hạ quyền KH-KD, chuyển phòng ban, xóa vĩnh viễn có xác minh mật khẩu), KH-KD / Dự án / WBS / Đấu thầu / Hợp đồng, Kho thiết bị (toàn bộ 55 thiết bị, kho chung, gán/đổi/trả, đề xuất, lô nhập, nhãn QR), Báo cáo, Chấm công, Cài đặt nghiệp vụ (`res.config.settings`) và xem danh mục Ứng dụng.
   - **Giữ nguyên dữ liệu nhân sự cá nhân:** Cấp admin không đổi phòng ban hay chức vụ HR của người nhận; đồng thời 6 rule `group_scoped_staff` và `crm.lead._kd_scoped()` tự động bỏ giới hạn nhân viên cũ khi tài khoản đang giữ `base.group_system`.

## 2. Bảo vệ ngoại lệ DEC-054 và Admin gốc ở Backend

`models/guards.py` thực thi kiểm tra theo đúng người gọi thật (`env.uid`), **kể cả khi đi qua `.sudo()`, import CSV/Excel (`load`), `copy`, `default_*` context, `role='group_system'`, `in_group_*` hay lệnh quan hệ lồng**:

- Chặn mọi tài khoản không phải Quản trị gốc tạo/sửa/xóa `tp.admin.delegation` hoặc `tp.admin.delegation.wizard`, và ẩn nút Cấp/Thu trên giao diện nhân sự (`groups="tp_admin_delegation.group_original_admin"` + `invisible="not tp_can_manage_delegation"`).
- Kiểm tra bất biến trước–sau trên cả `user.group_ids` (nhóm trực tiếp) và `user.all_group_ids` (nhóm hiệu lực) đối với tập nhóm quản trị bảo vệ (`group_original_admin`, `group_full_admin`, `base.group_system`, `base.group_erp_manager` và mọi nhóm kế thừa chúng): Admin được cấp không thể cấp admin cho người khác, không thể tạo user mới kèm quyền admin, và không thể tự gắn `base.group_system` / `group_original_admin` trực tiếp cho chính mình; trong khi vẫn gán được các nhóm nghiệp vụ thường cho nhân viên.
- Bảo vệ tuyệt đối tài khoản Quản trị gốc (`res.users`, `res.partner`, `hr.employee`, mật khẩu, link reset, API key, TOTP, trạng thái khóa/xóa) và bảo vệ các Quản trị viên khác khỏi bị thao túng chéo; giữ nguyên đổi mật khẩu/TOTP tự phục vụ của chính người đang đăng nhập.
- Khóa dòng (`FOR UPDATE`) và kiểm tra bất biến cuối giao dịch để **không bao giờ làm mất Quản trị gốc đang hoạt động cuối cùng** (kể cả khi chính Quản trị gốc thao tác nhầm).

## 3. Thu hồi sạch nguồn gốc quyền và kiểm lại phiên đang mở

- Trong Odoo 20, `user.group_ids` chỉ lưu nhóm gán trực tiếp, còn `all_group_ids` tính động theo đồ thị kế thừa. Nhờ cấp quyền qua duy nhất `group_full_admin`, khi thu hồi (và không còn dòng `active` nào của user đó), hệ thống gỡ `group_full_admin` khỏi `user.group_ids`: toàn bộ quyền admin kế thừa biến mất ngay lập tức mà **không ghi đè hay làm mất bất kỳ nhóm/vai trò nghiệp vụ hợp lệ nào** (kể cả vai trò nghiệp vụ được cập nhật trong thời gian làm admin).
- Ngay trong giao dịch thu hồi, hệ thống kiểm tra lại `has_group('base.group_system')`, `has_group('base.group_erp_manager')`, `group_original_admin` và `group_full_admin`: nếu còn bất kỳ nguồn admin nào khác khiến quyền hiệu lực chưa mất, hệ thống `raise UserError` (rollback savepoint), tuyệt đối không báo thu hồi thành công giả.
- `tp_admin_scope_revision` được đưa vào `_get_session_token_fields()` và tăng dưới khóa độc quyền khi cấp, thu hồi hoặc migration: mọi phiên đăng nhập và tab trình duyệt đang mở sẵn của tài khoản đích lập tức đổi session token và buộc xác thực/tải lại quyền ở ngay request kế tiếp.

## 4. Bảo toàn quyền riêng tư nhân viên thường (`HR-DELEGATE-FIX-001`)

- Nhân viên thường (không có `hr.group_hr_user`, không phải admin) giữ nguyên quyền cũ: chỉ xem Danh bạ đồng nghiệp (`hr.employee.public`) với `0` trường thiếu metadata, không đọc/tìm/ghi/xuất được `mobile_phone` hay thông tin riêng tư của người khác (kể cả qua `default_mobile_phone` hay `.sudo()`), đồng thời giữ nguyên tự cập nhật `mobile_phone` của chính mình trong `Thông tin cá nhân`.
