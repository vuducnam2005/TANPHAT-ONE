# TANPHAT ONE — Trạng thái dự án

**Cập nhật:** 28/10/2026 (Asia/Saigon)  
**Thư mục:** `C:\TANPHAT ONE`  
**Mục tiêu hiện tại:** xây nền tảng quản trị doanh nghiệp theo module Odoo + web frontend riêng, bắt đầu từ phòng Kế hoạch Kinh doanh.
Last change: `CHG-20261028-002`

**Phase:** Foundation hardening.
**Task vừa hoàn tất:** GIT-001 — kiểm chứng baseline Git local/remote và chuẩn bị publish handoff.
**Next task:** OPS-001 — diễn tập backup/restore database, filestore và source/config.

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
| Git history | Đã chốt baseline publish | `main` và `origin/main` đã đối chiếu ở `a25a0182`; các thay đổi handoff hiện tại được gom vào commit/push của CHG-20261028-002; hai ID foundation cũ không tìm thấy |
| AI handoff workflow | Đã thiết lập | `AGENTS.md`, status, changelog, business workflow và local checker |

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
- Quy trình bàn giao AI bắt buộc đọc status trước khi làm và cập nhật status/changelog sau mỗi code change.

## Kiểm chứng gần nhất

Các kiểm tra nền sau được ghi nhận từ các lượt trước trong ngày 28/10/2026, không được hiểu là vừa chạy lại trong lượt AI-001:

```text
Odoo tests: 0 failed, 0 error(s) of 10 tests
OpenAPI live validation: passed
Frontend typecheck/build: passed
Frontend unit tests: 3 passed
Prototype tests: 6 passed
Browser E2E: 3 passed
Smoke login/API: passed
```

Trong lượt AI-001 chỉ thay đổi tài liệu và tooling bàn giao, không đổi model/API/giao diện hoặc dữ liệu. Checker unit test đã đạt 11/11, Ruff và `git diff --check` đã đạt. GIT-001 đã fetch `origin`, xác nhận `main` và `origin/main` cùng ở `a25a0182` trước khi publish; commit/push CHG-20261028-002 là baseline handoff mới. Test ứng dụng sẽ chạy lại khi phạm vi code tương ứng thay đổi, không tự nhận kết quả cũ là kết quả mới.

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

1. **OPS-001:** lập và kiểm chứng backup/restore DB + filestore + phiên bản source/config trong môi trường tách biệt.
2. **BIZ-001:** đối chiếu blueprint với 2–3 hồ sơ đại diện; quyết định quyền, trạng thái, nguồn duyệt BASE/Odoo, giá thay thế/delta và sửa/hủy.
3. **CTR-001:** làm `tp_contract` theo vertical slice: model → security → test → API read → frontend read. **PRJ-002** được triển khai khi vòng đời project đã chốt, không bắt buộc phát minh thêm state để mở hợp đồng.
4. **CTR-002** và các task sau theo [roadmap](ROADMAP.md). Không mở action ghi trước khi backend kiểm quyền, transition và lịch sử.

## Không được làm ở bước hiện tại

- Không import toàn bộ Excel thật.
- Không xây đủ chín phân hệ cùng lúc.
- Không tạo workflow engine tổng quát hoặc reporting database khi chưa có hai workflow mẫu đã kiểm chứng.
- Không cho frontend tự tính/ghi state, tiền, quyền hoặc tổng hợp tài chính.
- Không triển khai production từ database dev.

## Blocker/rủi ro

Git metadata từng bị tách trong lần đổi thư mục trước. Ghi chú phục hồi cũ trong `.local/git-recovery/STATUS.txt` mô tả thời điểm chỉ có `ea975fb`; không dùng ghi chú đó thay cho trạng thái kiểm chứng hiện tại.

Kiểm tra chỉ đọc trong lượt AI-001/GIT-001 xác nhận `main` và `origin/main` đều có `a25a0182` trước khi publish; remote là `https://github.com/vuducnam2005/TANPHAT-ONE.git`. Diff model/API/frontend nền với HEAD rỗng; working tree chỉ có tài liệu/tooling handoff đang sửa/thêm. `git cat-file -e` không tìm thấy `fbad3686`/`4e47fddb`, nên không dựng lại hai ID này. Commit/push CHG-20261028-002 tạo mốc publish cho source hiện tại; điều đó không thay thế backup/restore hoặc bảo đảm production.

Lượt AI-001 không sửa Git metadata, không stage hoặc commit và không xử lý migration thư mục. Checker bàn giao dùng hash source độc lập; không dùng kết quả hash để kết luận Git đã đồng bộ hoặc production đã sẵn sàng.

Các điểm chưa xác minh: workflow duyệt chính thức, bốn mắt/ngưỡng duyệt, backup/restore thực tế, staging và production. Odoo test trên Windows từng có log INFO về filestore GC `WinError 5`; chưa coi kiểm tra dự án/API là bằng chứng toàn bộ hồ sơ tệp vận hành ổn định.

