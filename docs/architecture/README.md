# Kiến trúc nền tảng TANPHAT ONE

[Tên hệ thống và phân hệ TANPHAT ONE](TP_PRODUCT_NAMING.md) là quy ước hiện hành cho tên hiển thị.

Từ quyết định ngày 28/10/2026, frontend chính là web riêng gọi API Odoo. Backend sử dụng addon chuẩn Odoo và addon Tấn Phát theo nghiệp vụ.

Thiết kế hiện hành: [Cấu trúc source nền tảng Tấn Phát](TP_PLATFORM_SOURCE_STRUCTURE.md).

- `odoo/` và `addons/` giữ layout upstream.
- `custom_addons/` dành cho backend riêng.
- `frontend/` là app React/TypeScript/Vite gọi API thật; `frontend/prototype/` giữ dashboard mẫu cũ.
- `contracts/openapi/` dành cho hợp đồng API.
- Phân chia addon theo nghiệp vụ, workspace frontend theo nhu cầu phòng ban.

Các tài liệu `docs/dashboard/` giữ giá trị khảo sát dữ liệu và prototype. Phương án OWL client action trong các tài liệu đó là định hướng cũ cho phạm vi dashboard, đã được thay bằng thiết kế hiện hành cho toàn nền tảng.

Vertical slice nền đầu tiên có addon cài được (`tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`) và app React đọc dự án trên database dev. Login native, phân quyền, search, detail, logout và session hết hạn đã có browser tests. Chưa triển khai production, hợp đồng/nghiệm thu, import Excel hoặc dữ liệu doanh nghiệp thật.

Thiết kế database: [TP_DATABASE_DESIGN.md](TP_DATABASE_DESIGN.md). Cách chạy nền: [LOCAL_DEVELOPMENT.md](../../ops/runbooks/LOCAL_DEVELOPMENT.md).
