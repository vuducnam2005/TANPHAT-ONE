# Backend riêng Tấn Phát

Vertical slice nền đầu tiên có các addon cài được: `tp_core`, `tp_organization`, `tp_project`, `tp_contract`, `tp_api`, `tp_planning_api`. `tp_contract` là read slice hợp đồng (CTR-001), chưa có action ghi/duyệt; giao khoán và nghiệm thu chưa triển khai.

Chạy và kiểm thử: [LOCAL_DEVELOPMENT.md](../ops/runbooks/LOCAL_DEVELOPMENT.md).

Thiết kế và thứ tự dựng nền: [Cấu trúc source](../docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md).

- Kế thừa model Odoo khi phù hợp; không sao chép model chuẩn.
- Không sửa `odoo/` hoặc `addons/` cho nghiệp vụ Tấn Phát.
- Model, action và constraint giữ nghiệp vụ; API controller chỉ làm transport.
- Tạo security và test cùng với model được triển khai.
- Khai báo dependency trực tiếp thực dùng trong manifest; không đưa module tương lai vào trước.
- Dùng guideline trong `skills/odoo-guidelines/` và source Odoo 20 hiện tại khi triển khai.
