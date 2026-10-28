# TANPHAT ONE

Tên hệ thống và chín phân hệ tuân theo [quy ước TANPHAT ONE](docs/architecture/TP_PRODUCT_NAMING.md). Source chính nằm tại `C:\TANPHAT ONE`.

Backend Odoo 20, addon riêng tại `custom_addons/`, frontend React/TypeScript/Vite gọi API nghiệp vụ Odoo. PostgreSQL dùng chung theo môi trường; quyền công ty và phân công dự án được kiểm tại backend.

Đã dựng luồng đầu tiên: đăng nhập Odoo → web riêng → danh sách/chi tiết dự án theo quyền → đăng xuất và xử lý phiên hết hạn. Catalog hạng mục, mã phòng ban và dự án sử dụng các addon `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`.

## Chạy trên Windows

Yêu cầu Python 3.12, PostgreSQL 16+ (dev đang kiểm chứng với 18), Node.js 24 LTS và npm.

```powershell
.\scripts\dev.ps1 setup
.\scripts\dev.ps1 start
npm.cmd ci --prefix frontend
npm.cmd run dev --prefix frontend
```

Web riêng: <http://127.0.0.1:4173/work/>. Odoo quản trị: <http://127.0.0.1:18069/odoo>.

Tài khoản dev `planner.dev` và `admin` có mật khẩu tương ứng trong `.local/dev-secrets.json`. Không dùng credential hoặc cluster dev làm production. Hiện chỉ có dữ liệu seed giả lập.

- [Hướng dẫn chạy và nâng cấp](ops/runbooks/LOCAL_DEVELOPMENT.md)
- [Thiết kế database](docs/architecture/TP_DATABASE_DESIGN.md)
- [Cấu trúc source](docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md)
- [OpenAPI v1](contracts/openapi/tanphat-v1.yaml)
- [Frontend và kiểm thử browser](frontend/README.md)
- [Trạng thái dự án](docs/PROJECT_STATUS.md)
- [Quy trình bàn giao cho AI](docs/AI_CHANGE_WORKFLOW.md)
- [Workflow nghiệp vụ](docs/architecture/TP_BUSINESS_WORKFLOW.md)
- [Roadmap và cổng nghiệm thu](docs/ROADMAP.md)
- [Sổ quyết định](docs/DECISIONS.md)
- [Mẫu bàn giao AI](docs/HANDOFF_TEMPLATE.md)

Hợp đồng, giao khoán, nghiệm thu, import Excel, tích hợp kế toán và triển khai production là các giai đoạn tiếp theo. Nền hiện tại chưa thay thế quy trình vận hành doanh nghiệp.
