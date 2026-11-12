# TANPHAT ONE

Tên hệ thống và chín phân hệ tuân theo [quy ước TANPHAT ONE](docs/architecture/TP_PRODUCT_NAMING.md). Source chính nằm tại `C:\TANPHAT ONE`.

HR-ACCOUNT-ROLE-001: [hướng dẫn tài khoản/vai trò](docs/demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md), [acceptance](docs/demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md). Admin quản trị tài khoản riêng và staff↔HEAD KH-KD trong hồ sơ native; chức vụ HR không cấp quyền.


KD-ACCESS-002: [quyền trước–sau](docs/security/KD_ACCESS_002_ROLE_MATRIX.md),
[acceptance](docs/demo/KD_ACCESS_002_ACCEPTANCE.md) và [hướng dẫn5vai](docs/demo/KD_ACCESS_002_USER_GUIDE.md).
Phạm vi dev minh họa; Project/WBS scoped write và business/Q2/pilot còn riêng.

Theo DEC-030 ngày 05/11/2026, dùng giao diện Odoo native, tùy biến view/action/OWL trong `custom_addons/`; backend Odoo 20 và PostgreSQL dùng chung theo môi trường. Quyền công ty/phân công được kiểm tại backend. React/API cũ giữ lại để tham khảo và hồi quy; không phát triển React làm FE chính. Xem [hiện trạng và hướng phát triển](docs/architecture/TP_NATIVE_ODOO_DIRECTION.md).

Đã có Home/dashboard native, các app chuẩn và dữ liệu giả có liên kết. TP Projects mở rộng dự án chuẩn; hợp đồng có backend/API/UI React nháp–rà soát đã kiểm thử trên fixture, còn thiếu UI native. Catalog/phòng ban/dự án dùng `tp_core`, `tp_organization`, `tp_project`; API cũ ở `tp_api`, `tp_planning_api`.

## Chạy trên Windows

Yêu cầu Python 3.12, PostgreSQL 16+ (dev đang kiểm chứng với 18). Node.js/npm dùng cho tooling và React legacy khi cần. Workspace hiện tại đã setup; chạy status/start, không setup/upgrade chỉ để mở ứng dụng.

```powershell
.\scripts\dev.ps1 status
.\scripts\dev.ps1 start
```

Giao diện chính Odoo: <http://127.0.0.1:18069/odoo>. Không cần chạy Vite để dùng native. Hướng dẫn React legacy giữ ở `frontend/README.md`.

Tài khoản dev `planner.dev` và `admin` có mật khẩu tương ứng trong `.local/dev-secrets.json`. Không dùng credential hoặc cluster dev làm production. Hiện chỉ có dữ liệu seed giả lập.

- [Hướng dẫn chạy và nâng cấp](ops/runbooks/LOCAL_DEVELOPMENT.md)
- [Backup và diễn tập phục hồi](ops/runbooks/BACKUP_RESTORE.md)
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

Bước đề xuất gần nhất là đặc tả UI hợp đồng native trên backend hiện có. Giao khoán, nghiệm thu, import Excel, đối chiếu kế toán và production là giai đoạn sau, theo gate riêng. Nền hiện tại chưa thay thế toàn bộ quy trình doanh nghiệp.


IDENTITY-ORG-001 (CHG-20261112-011): danh tính HR/account thống nhất và chuyển phòng admin có preview/audit đã kiểm, áp18079/18069. [Hướng dẫn admin](docs/demo/IDENTITY_ORG_001_USER_GUIDE.md), [acceptance và giới hạn](docs/demo/IDENTITY_ORG_001_ACCEPTANCE.md). Không đổi auth/role người thật; visual/business/pilot riêng.
