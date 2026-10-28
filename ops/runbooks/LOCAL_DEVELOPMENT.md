# Chạy nền Odoo TANPHAT ONE trên Windows

Nền dùng Python 3.12 trong `.venv`, PostgreSQL 18 cluster riêng trong `.local`, Odoo 20 và 5 addon Tấn Phát. Không dùng service PostgreSQL khác trên máy và không thay đổi Python global. Đây là môi trường dev dùng loopback.

Chạy từ `C:\TANPHAT ONE`:

```powershell
.\scripts\dev.ps1 setup
.\scripts\dev.ps1 start
.\scripts\dev.ps1 smoke
.\scripts\dev.ps1 status
```

Nếu PostgreSQL được cài ở đường dẫn khác:

```powershell
.\scripts\dev.ps1 setup -PgBin 'D:\PostgreSQL\18\bin'
```

Mở `http://127.0.0.1:18069/odoo` hoặc `/web/login`. Tài khoản `admin` dùng giá trị `admin` trong `.local/dev-secrets.json`; `planner.dev` dùng giá trị `planner`. Mật khẩu được tạo ngẫu nhiên, script không in ra console hoặc lưu trong Git. Seed chỉ tạo dữ liệu giả lập lần đầu: phòng KHKD, hai dự án DEV-001/DEV-002 và phân công reader cho DEV-001. Setup/upgrade đồng bộ password hai tài khoản dev từ file credential; không dùng các tài khoản này cho production. Không có dữ liệu Excel thật.

Native menu Tan Phat cho phép manager cấu hình catalog/dự án/phân công. Reader dùng API chỉ thấy dự án được phân công. API có `/api/v1/me`, `/api/v1/projects`, `/api/v1/projects/{id}`; contract ở `contracts/openapi/tanphat-v1.yaml`. Đây là API đọc, chưa có các thao tác ghi nghiệp vụ. Frontend React đã nối session và API dự án thật.

## Kiểm thử và nâng cấp

```powershell
.\scripts\dev.ps1 test
```

Test chạy trên `tp_tanphat_test`, cổng HTTP 18079, không ghi vào dev DB. Log kiểm thử có thể chuyển vào `.local/logs/tests.log`. Test Odoo kiểm scope ORM, self-assignment, quyền từ group native, company, API 401/403/404 và validation. Smoke dùng đăng nhập native thật trên dev và kiểm tra project scope. Prototype JavaScript vẫn chạy bằng `npm.cmd run test:prototype --prefix frontend` từ root.

Kiểm OpenAPI và response API thật (công cụ riêng cho phát triển):

```powershell
.\.venv\Scripts\python.exe -m pip install -r ops\requirements-tools.txt
.\.venv\Scripts\python.exe scripts\check_contract.py --live
.\.venv\Scripts\python.exe -m ruff check custom_addons scripts\dev.py scripts\check_contract.py
```

Dừng runtime rồi nâng cấp khi thay model/security/schema:

```powershell
.\scripts\dev.ps1 stop
.\scripts\dev.ps1 upgrade
.\scripts\dev.ps1 start
```

`stop` dừng Odoo dev và cluster dev thuộc workspace này; script kiểm tra PID/cấu hình/ownership, không dừng service PostgreSQL khác. Không xóa database khi setup/upgrade/test. Frontend React và prototype chạy riêng, xem phần bên dưới.

## Cấu hình và khả năng tái lập

- `.local/odoo.conf`: cấu hình thật, password riêng, ngoài Git.
- `.local/dev-secrets.json`: credential dev, ngoài Git.
- `.local/postgres/data`: cluster dev/test, ngoài Git.
- `.local/odoo`: session/filestore dev/test, ngoài Git.
- `.local/logs`: log, ngoài Git.
- `ops/config/odoo-dev.conf.example`: cấu hình mẫu không có credential.
- `ops/requirements-windows-py312.lock.txt`: snapshot dependency đã cài và kiểm chứng trên Windows/Python 3.12; không dùng lock Windows cho Linux production.
- `ops/runtime-baseline.json`: Odoo upstream/tree và runtime đã khóa.

HTTP dev chỉ chọn `tp_tanphat_dev` bằng dbfilter cố định. Lệnh test override cả database và dbfilter thành `tp_tanphat_test`; server dev không phục vụ database test.

Nếu PowerShell chặn script local, có thể chạy `.venv\Scripts\python.exe scripts\dev.py <action>` sau khi đã cài environment/dependency. Bootstrap tự động yêu cầu PostgreSQL 16+ được cài; mặc định tìm 18, 17, 16. Dev port 55432/18069 hoặc test port 18079 bị chiếm thì script dừng để tránh kết nối nhầm dịch vụ.

## Phạm vi production

Chưa triển khai production, lịch backup, HTTPS reverse proxy, import Excel hoặc kế toán. Trước pilot cần thử backup/restore database + filestore, kiểm migration trên staging và chọn RPO/RTO. Xem `docs/architecture/TP_DATABASE_DESIGN.md` cho phương án dữ liệu và mở rộng.

Trong lần test Windows, Odoo upstream có log INFO về filestore GC không xóa được một số file `.__gc` do Windows giữ handle (WinError 5). Các test nền vẫn hoàn thành; chưa sửa core để tránh thay đổi upstream. Cần kiểm chứng lưu/xóa/backup/restore hồ sơ trong môi trường triển khai trước khi đưa dữ liệu thật vào.


## Web riêng React/TypeScript

Yêu cầu Node.js 24 LTS và npm. Sau khi Odoo dev chạy:

```powershell
npm.cmd ci --prefix frontend
npm.cmd run dev --prefix frontend
```

Mở <http://127.0.0.1:4173/work/>. Vite proxy native login/logout và API tới cổng 18069 trên cùng origin. Frontend không giữ password hoặc API key. Tài khoản reader chỉ thấy DEV-001; admin thấy DEV-001 và DEV-002.

```powershell
npm.cmd run build --prefix frontend
npm.cmd test --prefix frontend
npm.cmd run test:prototype --prefix frontend
npm.cmd exec --prefix frontend -- playwright install chromium
npm.cmd run test:e2e --prefix frontend
```

Browser test dùng credential trong `.local/dev-secrets.json`, không lưu trace/video. Test kiểm quyền manager/reader, reload detail, search, 404, logout CSRF, session hết hạn và mobile overflow. Kết quả và ảnh QA nằm ngoài Git trong `.local/`.

Dashboard mẫu cũ nằm ở `frontend/prototype/`; chạy bằng `npm.cmd run prototype --prefix frontend`. Cả prototype và Vite mặc định chọn 4173, nên chỉ chạy một hoặc đặt `PORT=4174` khi chạy prototype.
