# TANPHAT ONE web workspace

Tên phân hệ dùng chung trong `src/shared/config/product.ts`, theo [quy ước sản phẩm](../docs/architecture/TP_PRODUCT_NAMING.md). Menu dự án dùng tên **TP Projects**.

Frontend React/TypeScript/Vite độc lập gọi API nghiệp vụ `/api/v1` của Odoo bằng session native. Backend quản lý dữ liệu, phân quyền và tính toán nghiệp vụ.

## Chạy local

Từ `C:\TANPHAT ONE`:

```powershell
npm.cmd ci --prefix frontend
npm.cmd run dev --prefix frontend
```

Mở <http://127.0.0.1:4173/work/>. Vite proxy `/api`, `/web` và `/odoo` tới Odoo dev ở `127.0.0.1:18069`. Đặt biến môi trường `TP_ODOO_ORIGIN` nếu cần đổi địa chỉ backend. Không mở CORS hoặc nhúng API key vào browser.

Bấm Đăng nhập để mở trang native Odoo trên cùng origin. Tài khoản `planner.dev` dùng giá trị `planner` trong `.local/dev-secrets.json`; quản trị `admin` dùng giá trị `admin`. Xem [runbook](../ops/runbooks/LOCAL_DEVELOPMENT.md) để dựng backend trước.

## Cấu trúc đang dùng

```text
frontend/
├── src/
│   ├── app/                     # routing, provider, shell, workspace registry
│   ├── features/projects/       # danh sách, tìm kiếm, phân trang và chi tiết
│   ├── shared/api/              # transport, session, query keys, OpenAPI types
│   ├── shared/ui/               # trạng thái lỗi, trống và chưa có quyền
│   └── styles/                  # token và layout dùng chung
├── tests/e2e/                   # browser tests với Odoo dev thật
├── prototype/                   # giữ dashboard vanilla JS và fixture cũ
└── vite.config.ts               # SPA ở /work/, proxy native Odoo routes
```

`features` chia theo nghiệp vụ. Workspace ghép các feature cho từng phòng. `shared` không import ngược từ feature hoặc app. Chỉ `shared/api/client.ts` gọi fetch; UI không phụ thuộc model/field ORM và không tính số tiền chính thức.

Query key tách theo API version, user, company hiện tại, tập company đang được phép và tham số truy vấn. Response bị hủy khi query đổi scope. Khi API báo 401, cache dự án bị bỏ và ứng dụng quay về trạng thái đăng nhập. Logout dùng form POST native có CSRF và xóa cache. Chưa có company switcher hoặc thao tác ghi nghiệp vụ.

Types trong `src/shared/api/openapi.generated.ts` được sinh từ OpenAPI. Khi đổi contract:

```powershell
npm.cmd run api:types --prefix frontend
npm.cmd run typecheck --prefix frontend
npm.cmd run build --prefix frontend
```

## Kiểm tra

```powershell
npm.cmd test --prefix frontend
npm.cmd run test:prototype --prefix frontend
npm.cmd exec --prefix frontend -- playwright install chromium
npm.cmd run test:e2e --prefix frontend
```

Browser tests cần Odoo dev và hai project seed của `scripts/dev.ps1 setup`. Test kiểm đăng nhập native, quyền khác nhau giữa manager/reader, project 404, URL ID không hợp lệ, search, reload detail, CSRF logout, session hết hạn và mobile overflow. Credential và kết quả browser nằm trong `.local/`, ngoài Git; không lưu trace, video hoặc password.

Prototype cũ chạy riêng bằng `npm.cmd run prototype --prefix frontend`, mặc định cổng 4173; cần dừng Vite hoặc đặt `PORT=4174` trước. Đây là fixture để tham khảo UI, chưa phải nghiệp vụ backend đã phê duyệt.

## Phát hành sau này

`npm run build` sinh `frontend/dist/`. Production cần reverse proxy HTTPS: `/work/` phục vụ SPA với fallback `/work/index.html`, `/api/`, `/web/`, `/odoo/` chuyển tới Odoo. Không dùng Vite dev/preview làm production server. Chưa triển khai production trong giai đoạn này.
