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

TANPHAT ONE có trang đăng nhập React riêng ở `/work/`. Form gửi credential trực tiếp tới `/web/session/authenticate` của Odoo. MFA cần link **Tiếp tục xác thực bảo mật**; passkey hoặc phương thức khác dùng link trong **Cần hỗ trợ đăng nhập?**, đều giữ luồng native Odoo. Tài khoản `planner.dev` dùng giá trị `planner` trong `.local/dev-secrets.json`; quản trị `admin` dùng giá trị `admin`. Xem [runbook](../ops/runbooks/LOCAL_DEVELOPMENT.md) để dựng backend trước.

Tên database là cấu hình public của build, không phải credential. Dev server mặc định dùng `tp_tanphat_dev`; build phải khai báo rõ database khớp `dbfilter`:

```powershell
$env:VITE_ODOO_DATABASE = 'tp_tanphat_dev'
npm.cmd run build --prefix frontend
```

## Cấu trúc đang dùng

```text
frontend/
├── src/
│   ├── app/                     # routing, provider, shell, workspace registry
│   ├── features/auth/           # TANPHAT ONE login, MFA handoff, visual language
│   ├── features/projects/       # danh sách, tìm kiếm, phân trang và chi tiết
│   ├── features/contracts/      # TP Contracts: danh sách, chi tiết theo ngày, phạm vi revision
│   ├── shared/api/              # transport, session, query keys, OpenAPI types
│   ├── shared/ui/               # trạng thái lỗi, trống và chưa có quyền
│   └── styles/                  # token và layout dùng chung
├── tests/e2e/                   # browser tests với Odoo dev thật
├── prototype/                   # giữ dashboard vanilla JS và fixture cũ
└── vite.config.ts               # SPA ở /work/, proxy native Odoo routes
```

`features` chia theo nghiệp vụ. Workspace ghép các feature cho từng phòng. `shared` không import ngược từ feature hoặc app. Chỉ `shared/api/client.ts` gọi fetch; UI không phụ thuộc model/field ORM và không tính số tiền chính thức.

Query key tách theo API version, user, company hiện tại, tập company đang được phép và tham số truy vấn. Response bị hủy khi query đổi scope. Khi API báo 401, cache dự án bị bỏ và ứng dụng quay về trạng thái đăng nhập. Logout dùng form POST native có CSRF và xóa cache. Chưa có company switcher hoặc thao tác ghi nghiệp vụ. Login chỉ giữ credential trong request đang chạy; không lưu password, token hay session payload vào localStorage.

TP Contracts có route `/contracts` (lọc `?project_id=`), `/contracts/:id` (`?as_of=YYYY-MM-DD`) và `/contracts/:id/revisions/:revisionId`. Số tiền là decimal string từ API, chỉ nhóm chữ số để hiển thị, không chuyển sang `Number`; `null`, `0`, chưa xác nhận, chưa đủ và khác cơ sở thuế hiển thị khác nhau. Khi API không trả field tiền vì thiếu grant, màn hình ẩn cột/giá trị và báo chưa được cấp quyền; việc chặn thật nằm ở Odoo. Tải tài liệu là link same-origin tới API, backend kiểm lại quyền.

Types trong `src/shared/api/openapi.generated.ts` được sinh từ OpenAPI. Khi đổi contract:

```powershell
npm.cmd run api:types --prefix frontend
npm.cmd run typecheck --prefix frontend
$env:VITE_ODOO_DATABASE = 'tp_tanphat_dev' # thay bằng database môi trường đích khi phát hành
npm.cmd run build --prefix frontend
```

## Kiểm tra

```powershell
npm.cmd test --prefix frontend
npm.cmd run test:prototype --prefix frontend
npm.cmd exec --prefix frontend -- playwright install chromium
npm.cmd run test:e2e --prefix frontend
```

Browser tests cần Odoo dev, hai project và ba hợp đồng giả lập của `scripts/dev.ps1 setup`/`upgrade`. Test kiểm trang login riêng, sai credential, MFA handoff, lỗi gateway không lộ chi tiết, responsive/reduced-motion, deep link, quyền khác nhau giữa manager/reader, project 404, URL ID không hợp lệ, search, reload detail, CSRF logout, session hết hạn và mobile overflow; TP Contracts kiểm reader không thấy số tiền/tài liệu tài chính, admin có grant thấy phụ lục thay thế giá trị, BASE đã xác minh nhưng chưa ký/hiệu lực, dòng chưa xác nhận, hợp đồng ngoài scope 404 và màn hình 390px. Credential và kết quả browser nằm trong `.local/`, ngoài Git; không lưu trace, video hoặc password.

Prototype cũ chạy riêng bằng `npm.cmd run prototype --prefix frontend`, mặc định cổng 4173; cần dừng Vite hoặc đặt `PORT=4174` trước. Đây là fixture để tham khảo UI, chưa phải nghiệp vụ backend đã phê duyệt.

## Phát hành sau này

`npm run build` sinh `frontend/dist/`. Production cần reverse proxy HTTPS: `/work/` phục vụ SPA với fallback `/work/index.html`, `/api/`, `/web/`, `/odoo/` chuyển tới Odoo. Không dùng Vite dev/preview làm production server. Chưa triển khai production trong giai đoạn này.
