# NATIVE-DATA-003 — bảng tổng hợp nội bộ

02/11/2026. Native `spreadsheet.dashboard.share` tạo bản sao công khai bằng token; `_check_dashboard_access` kiểm quyền của người tạo link, không bắt người mở đăng nhập. Vì hai dashboard mẫu có dữ liệu/phạm vi nội bộ, không được chỉ kiểm menu/allowed_user_ids rồi coi link share có cùng bảo vệ.

Batch security riêng `tp_dashboard_privacy`: cờ `tp_internal_only` mặc định False trên dashboard, chỉ Dashboard Manager cấu hình; chỉ bật trên hai fixture DATA002. Cấm tạo/repoint bản share tới dashboard đó, kiểm quyền đọc dashboard nguồn với actor thực trước create/write, và chặn cả token cũ khi cờ đang bật. Bảng chuẩn khác giữ native behavior. Không chia sẻ/export bản số liệu, không thay quyền Odoo toàn công ty. Ở CHG-20261102-014 nút Share còn hiện; DASH-UI-001 CHG-20261104-001 đã ẩn nút theo metadata và hiện Chỉ truy cập nội bộ, backend guard giữ nguyên.

Test gồm người được đọc vẫn không tạo public snapshot, người ngoài không đọc nguồn, không repoint share, token cũ bị chặn và bảng native không cờ vẫn dùng được. Test clone trước dev, không coi link token là phiên actor. Rollback cờ/addon phải cân nhắc bật lại public share; không tự rollback nếu còn số liệu nội bộ.

## DASH-UI-001 — Live report read-only

Hai method ORM công khai trên `spreadsheet.dashboard`: `tp_dashboard_report(filters)` và `tp_dashboard_action(source, filters, project_id, state)`. Mỗi request ensure singleton/check_access(read), xác minh đúng XML ID/kind/version trong workbook, kiểm công ty trong env.companies, search project theo record rule, từ chối ID chọn ngoài scope, validate ngày/source/state. Sau đó search/read nguồn bằng actor thực; không sudo/business cache/bảng tổng runtime. Field ACL/record rules của từng nguồn vẫn quyết định dữ liệu; lỗi không thành0. Action source tính lại scope rồi trả native window domain theo ID có đóng góp, không nhận domain client. Không mở action ghi nghiệp vụ hoặc capability/group/schema mới.

Readonly dashboard payload thêm `tp_dashboard.kind/internal`. Chỉ cờ privacy có restricted-field sudo giống guard đã có; không lấy nguồn nghiệp vụ bằng sudo. OWL/SCSS chỉ render custom với2 binding; chuẩn khác giữ native. Template/cấu hình không chứa kết quả tiền, global native pivot không thay filter của view OWL. Nguồn/công thức/analytic split/currency/date/filter và giới hạn whole-document drilldown: [README](../demo/dashboards/README.md).

Đã kiểm clone trước dev:17 Odoo (privacy+report), actor UI/RPC, negative source/company/project, split60/40/rounding/0%/ambiguous key/currency; clone revoke dashboard/assignment rồi refresh cùng phiên xóa số cũ, report/raw/action chặn hoặc loại scope; cuối restore exact quyền. Đây là regression kỹ thuật của task, không nghiệm thu độc lập/pilot. Không uninstall privacy để rollback UI.
