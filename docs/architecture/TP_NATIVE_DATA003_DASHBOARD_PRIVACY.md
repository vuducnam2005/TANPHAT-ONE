# NATIVE-DATA-003 — bảng tổng hợp nội bộ

02/11/2026. Native `spreadsheet.dashboard.share` tạo bản sao công khai bằng token; `_check_dashboard_access` kiểm quyền của người tạo link, không bắt người mở đăng nhập. Vì hai dashboard mẫu có dữ liệu/phạm vi nội bộ, không được chỉ kiểm menu/allowed_user_ids rồi coi link share có cùng bảo vệ.

Batch security riêng `tp_dashboard_privacy`: cờ `tp_internal_only` mặc định False trên dashboard, chỉ Dashboard Manager cấu hình; chỉ bật trên hai fixture DATA002. Cấm tạo/repoint bản share tới dashboard đó, kiểm quyền đọc dashboard nguồn với actor thực trước create/write, và chặn cả token cũ khi cờ đang bật. Bảng chuẩn khác giữ native behavior. Không tạo endpoint, không chia sẻ/export bản số liệu, không thay quyền Odoo toàn công ty. Nút Share native còn hiện nhưng action trả thông báo chỉ truy cập nội bộ; chưa có JS tùy biến.

Test gồm người được đọc vẫn không tạo public snapshot, người ngoài không đọc nguồn, không repoint share, token cũ bị chặn và bảng native không cờ vẫn dùng được. Test clone trước dev, không coi link token là phiên actor. Rollback cờ/addon phải cân nhắc bật lại public share; không tự rollback nếu còn số liệu nội bộ.
