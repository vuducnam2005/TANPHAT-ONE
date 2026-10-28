# Hợp đồng API Tấn Phát

Hợp đồng API frontend/backend được quản lý bằng [OpenAPI](openapi/tanphat-v1.yaml). Bản đầu tiên mô tả session, danh sách và chi tiết dự án; endpoint ghi dữ liệu và nghiệp vụ tài chính chưa được mở.

- OpenAPI là nguồn định nghĩa DTO, input, lỗi, pagination và version.
- TypeScript types được sinh từ schema bằng `npm.cmd run api:types --prefix frontend` và lưu ở `frontend/src/shared/api/openapi.generated.ts`.
- API có kiểm thử HTTP và quyền trên Odoo thật; validation schema bổ sung ở công cụ kiểm chứng contract.
- Frontend không phụ thuộc tên model/field hoặc generic RPC của Odoo.

Phương án session, CSRF và endpoint đầu tiên nằm trong [thiết kế nền tảng](../docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md).
