# TANPHAT ONE — Trạng thái dự án

**Cập nhật:** 28/10/2026 (Asia/Saigon)  
**Thư mục:** `C:\TANPHAT ONE`  
**Mục tiêu hiện tại:** xây nền tảng quản trị doanh nghiệp theo module Odoo + web frontend riêng, bắt đầu từ phòng Kế hoạch Kinh doanh.

## Trạng thái tổng quan

| Hạng mục | Trạng thái | Ghi chú |
| --- | --- | --- |
| Tên sản phẩm | Đã chốt | TANPHAT ONE |
| Tên phân hệ | Đã chốt | TP Dashboard, TP Projects, TP Survey, TP Design, TP Contracts, TP Tasks, TP HR, TP Finance, TP Documents |
| Backend nền | Đã chạy | Odoo 20, `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api` |
| Database dev/test | Đã chạy | PostgreSQL 18, `tp_tanphat_dev`, `tp_tanphat_test` |
| Frontend nền | Đã chạy | React/TypeScript/Vite tại `/work/`, gọi API session Odoo |
| Vertical slice đọc dự án | Đã kiểm chứng | login → `/me` → list/detail theo quyền → logout/session expiry |
| Hợp đồng/giao khoán/nghiệm thu | Chưa triển khai | Đã có thiết kế database, chưa có model nghiệp vụ |
| Production | Chưa triển khai | Chưa có HTTPS, backup production, staging migration hoặc dữ liệu thật |
| Git history | Cần xử lý | Metadata hiện khôi phục từ baseline cũ; không được coi là lịch sử đầy đủ của foundation commit |

## Đã triển khai

- Odoo custom addons nằm trong `custom_addons/`, không sửa core.
- `hr.department` có mã phòng ban `tp_code`.
- `project.project` có mã, company, phòng chủ trì và cờ managed.
- `tp.project.assignment` giới hạn người dùng theo dự án, company và role.
- API JSON có request ID, lỗi có cấu trúc, session Odoo và query allowlist.
- OpenAPI ở `contracts/openapi/tanphat-v1.yaml`; TypeScript types được sinh vào frontend.
- Frontend có project list/detail, search, pagination, loading/empty/error/permission state.
- Browser test kiểm tra reader/manager scope, 404, reload, search, CSRF logout, session hết hạn và mobile overflow.
- Tên sản phẩm/phân hệ và đường dẫn runtime đã đổi sang `C:\TANPHAT ONE`.

## Kiểm chứng gần nhất

Các kiểm tra nền đã đạt ở phiên trước:

```text
Odoo tests: 0 failed, 0 error(s) of 10 tests
OpenAPI live validation: passed
Frontend typecheck/build: passed
Frontend unit tests: 3 passed
Prototype tests: 6 passed
Browser E2E: 3 passed
Smoke login/API: passed
```

Lệnh kiểm tra nhanh:

```powershell
.\scripts\dev.ps1 status
.\scripts\dev.ps1 smoke
.\.venv\Scripts\python.exe scripts\check_contract.py --live
npm.cmd run typecheck --prefix frontend
npm.cmd run build --prefix frontend
npm.cmd test --prefix frontend
npm.cmd run test:e2e --prefix frontend
```

## Next action bắt buộc

1. Giữ nguyên tên kỹ thuật và hoàn thiện baseline Git trước khi có nhiều thay đổi mới.
2. Đọc `docs/architecture/TP_BUSINESS_WORKFLOW.md` và đối chiếu với hồ sơ nghiệp vụ thật/đã khử dữ liệu.
3. Chốt ma trận role/capability và state/transition cho TP Projects, TP Contracts.
4. Tạo addon `tp_contract` theo vertical slice: model → security → test → API read → frontend read.
5. Sau khi read flow ổn định, mới mở các action ghi `submit`, `approve`, `reject`, `cancel`.

## Không được làm ở bước hiện tại

- Không import toàn bộ Excel thật.
- Không xây đủ chín phân hệ cùng lúc.
- Không tạo workflow engine tổng quát hoặc reporting database khi chưa có hai workflow mẫu đã kiểm chứng.
- Không cho frontend tự tính/ghi state, tiền, quyền hoặc tổng hợp tài chính.
- Không triển khai production từ database dev.

## Blocker/rủi ro

Git metadata bị tách trong lần đổi thư mục trước. Source, database dev/test và runtime đã được kiểm tra nhưng lịch sử foundation gần nhất chưa được khôi phục đầy đủ. Trước khi bắt đầu chuỗi thay đổi lớn cần tạo bản snapshot Git sạch hoặc khôi phục đúng repository baseline; mọi phiên AI phải ghi rõ nếu blocker này chưa xử lý.

