# TANPHAT ONE — Trạng thái dự án

**Cập nhật:** 28/10/2026 (Asia/Saigon)  
**Thư mục:** `C:\TANPHAT ONE`  
**Mục tiêu hiện tại:** xây nền tảng quản trị doanh nghiệp theo module Odoo + web frontend riêng, bắt đầu từ phòng Kế hoạch Kinh doanh.
Last change: `CHG-20261028-005`

**Phase:** Baseline nghiệp vụ KD → TP Contracts read slice.
**Task vừa hoàn tất:** BIZ-001 — hoàn tất baseline phân tích workflow và ma trận quyền từ năm nguồn; nghiệm thu chủ nghiệp vụ/hồ sơ thực tế và văn bản thẩm quyền còn chờ.
**Next task:** CTR-001 — TP Contracts đọc hợp đồng/revision/line và tham chiếu BASE, có quyền tiền/attachment; chưa có action ghi/chốt pháp lý.

## Trạng thái tổng quan

| Hạng mục | Trạng thái | Ghi chú |
| --- | --- | --- |
| Tên sản phẩm | Đã chốt | TANPHAT ONE |
| Tên phân hệ | Đã chốt | TP Dashboard, TP Projects, TP Survey, TP Design, TP Contracts, TP Tasks, TP HR, TP Finance, TP Documents |
| Backend nền | Đã chạy | Odoo 20, `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api` |
| Database dev/test | Đã chạy | PostgreSQL 18, `tp_tanphat_dev`, `tp_tanphat_test` |
| Frontend nền | Đã chạy | React/TypeScript/Vite tại `/work/`, login riêng TANPHAT ONE gọi session Odoo; MFA/passkey có native fallback |
| Vertical slice đọc dự án | Đã kiểm chứng | login → `/me` → list/detail theo quyền → logout/session expiry |
| Hợp đồng/giao khoán/nghiệm thu | Chưa triển khai | Đã có thiết kế database, chưa có model nghiệp vụ |
| Workflow và ma trận quyền KD | Baseline phân tích hoàn tất | BIZ-001: BASE phê duyệt chính thức, tiền theo scope, hạn mức chưa biết; model/state/capability mới là đề xuất |
| Production | Chưa triển khai | Chưa có HTTPS, backup production, staging migration hoặc dữ liệu thật |
| Git history | Đã chốt baseline publish | `main` và `origin/main` đã đối chiếu ở `a25a0182`; các thay đổi handoff hiện tại được gom vào commit/push của CHG-20261028-002; hai ID foundation cũ không tìm thấy |
| AI handoff workflow | Đã thiết lập | `AGENTS.md`, status, changelog, business workflow và local checker |
| Backup/restore dev | Đã kiểm chứng local | `scripts/backup_restore.py`; backup `20261028T062821364112Z`; final restore report `20261028T064405723351Z`; nghiệp vụ/config dev giữ nguyên |

## Đã triển khai

- Odoo custom addons nằm trong `custom_addons/`, không sửa core.
- `hr.department` có mã phòng ban `tp_code`.
- `project.project` có mã, company, phòng chủ trì và cờ managed.
- `tp.project.assignment` giới hạn người dùng theo dự án, company và role.
- API JSON có request ID, lỗi có cấu trúc, session Odoo và query allowlist.
- OpenAPI ở `contracts/openapi/tanphat-v1.yaml`; TypeScript types được sinh vào frontend.
- Frontend có project list/detail, search, pagination, loading/empty/error/permission state.
- Frontend có cổng login riêng với minh họa cầu dây văng, hover/focus, animation có reduced-motion, hiện/ẩn mật khẩu, lỗi credential/gateway và MFA handoff; credential không lưu vào browser storage.
- Browser test kiểm tra reader/manager scope, 404, reload, search, CSRF logout, session hết hạn và mobile overflow.
- Tên sản phẩm/phân hệ và đường dẫn runtime đã đổi sang `C:\TANPHAT ONE`.
- Quy trình bàn giao AI bắt buộc đọc status trước khi làm và cập nhật status/changelog sau mỗi code change.

## Kiểm chứng gần nhất

Lượt BIZ-001 (`CHG-20261028-005`) chỉ thay tài liệu kiến trúc/bàn giao. Đã đọc DOCX/PDF/ba XLSM, đối chiếu ảnh quy trình và công thức/hướng dẫn; không chạy macro/external link, không import hoặc sửa database. [Workflow và ma trận quyền](architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md) tách review, kết quả BASE, chữ ký/hiệu lực và revision; [bằng chứng/ca nghiệm thu](architecture/TP_KD_EVIDENCE_AND_ACCEPTANCE.md) giữ registry hash, vị trí nguồn và các ca giả lập. `verify_baseline.py` đạt 27 link, 26 bảng nhất quán, hash 5 nguồn NAS khớp, 0 cell kế toán thực tế được đọc và 10 phép tính Decimal giả lập; `git diff --check` đạt. Chưa có biên bản ký duyệt ma trận, chưa có hợp đồng/BASE evidence thực tế đầy đủ; không nhận ca giả lập là Odoo tests. Không chạy lại bộ ứng dụng vì không đổi code/runtime.

Lượt AUTH-001 (`CHG-20261028-004`) theo yêu cầu ưu tiên giao diện của người dùng: frontend typecheck đạt, 10 unit tests đạt, build với `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt, 8 browser E2E đạt. Đã xem screenshot desktop 1440px và mobile 390px; kiểm overflow 320px, password visibility, reduced-motion, login thật/sai credential, deep link, MFA handoff mô phỏng, gateway error, quyền dự án, CSRF logout và session hết hạn. Chưa kiểm MFA/TOTP/passkey bằng tài khoản thật; phần xác thực bổ sung vẫn dùng Odoo native theo lựa chọn người dùng. Screenshot nằm `.local/login-desktop.png` và `.local/login-mobile.png`, ngoài Git.

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

Trong lượt AI-001/GIT-001 chỉ thay đổi tài liệu và tooling bàn giao, không đổi model/API/giao diện hoặc dữ liệu dev. OPS-001 bổ sung script/runbook và đã đạt 21 unit tests, Ruff, backup checksum, 314 bảng/fingerprint, 37 attachment tham chiếu, login/API/quyền/tải tệp trên Odoo restore; dev gốc smoke lại đạt. Test ứng dụng sẽ chạy lại khi phạm vi code tương ứng thay đổi, không tự nhận kết quả cũ là kết quả mới.

Lệnh kiểm tra nhanh:

```powershell
.\scripts\dev.ps1 status
.\scripts\dev.ps1 smoke
.\.venv\Scripts\python.exe scripts\check_contract.py --live
npm.cmd run typecheck --prefix frontend
$env:VITE_ODOO_DATABASE = 'tp_tanphat_dev' # build local; đặt database đích khi phát hành
npm.cmd run build --prefix frontend
npm.cmd test --prefix frontend
npm.cmd run test:e2e --prefix frontend
```

## Next action bắt buộc

1. **CTR-001:** đọc baseline BIZ-001 và ca nghiệm thu; làm `tp_contract` theo model → security/test → API read → frontend read. Tách danh tính contract, snapshot revision/line và `tp.approval.reference`; kiểm quyền tiền/file ở ORM/RPC và API, không chỉ React. Chỉ dùng dữ liệu giả, trạng thái thiếu chứng cứ phải hiển thị chưa xác minh.
2. **Nghiệm thu nghiệp vụ BIZ-001:** bổ sung 2–3 bộ hồ sơ khử dữ liệu có phụ lục, khoán cấp 2 và correction/void; dùng Q1–Q8 đóng cổng tương ứng. Cần lãnh đạo/QT-TC xác nhận văn bản ký/duyệt và người record/verify BASE, không hỏi lại nơi duyệt đã chọn.
3. **CTR-002:** có thể phát triển draft/submit/return trên test sau read slice; chưa mở xác nhận BASE/hiệu lực pháp lý cho pilot khi thiếu thẩm quyền/evidence. **PRJ-002** không bắt buộc để mở read hợp đồng; các task còn lại theo [roadmap](ROADMAP.md).

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

Đã xác nhận nơi duyệt chính thức là BASE và phạm vi xem tiền; chưa xác minh văn bản ký/duyệt/hạn mức, bốn mắt, BASE ID/evidence thực tế, cơ sở thuế/ngày hiệu lực và nghiệm thu ma trận với chủ nghiệp vụ. S05 bản đọc chưa có hàng import kế toán thực tế, không dùng làm chứng cứ reconcile đạt. Các điểm vận hành còn thiếu: backup ngoài máy, mã hóa/retention/RPO/RTO, host khác, staging/production. Backup local chưa mã hóa; credential nằm ngoài Git. Odoo test Windows từng có INFO filestore GC `WinError 5`; kiểm tra dự án/API không chứng minh toàn bộ hồ sơ tệp vận hành ổn định.

Lượt BIZ-001 giữ nguyên các thay đổi login chưa commit từ AUTH-001, không commit/push hoặc sửa Git metadata. Hai tài liệu chi tiết BIZ mới được kiểm riêng về liên kết/nội dung; checker hiện dùng danh sách policy cố định, không tự hash mọi Markdown được liên kết.

