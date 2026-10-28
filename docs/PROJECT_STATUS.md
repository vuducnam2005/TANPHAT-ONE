# TANPHAT ONE — Trạng thái dự án

**Cập nhật:** 28/10/2026 (Asia/Saigon)  
**Thư mục:** `C:\TANPHAT ONE`  
**Mục tiêu hiện tại:** xây nền tảng quản trị doanh nghiệp theo module Odoo + web frontend riêng, bắt đầu từ phòng Kế hoạch Kinh doanh.
Last change: `CHG-20261028-008`

**Phase:** TP Contracts read slice → nghiệm thu nghiệp vụ và draft trên test.
**Task vừa hoàn tất:** CTR-001 — TP Contracts đọc hợp đồng, revision, dòng phạm vi, kết quả BASE và tài liệu từ Odoo đến React; quyền tiền theo grant từng project được kiểm ở ORM/RPC, API và tệp; đã kiểm chứng trên dev với dữ liệu giả lập.
**Next task:** nghiệm thu BIZ-001/CTR-001 với chủ nghiệp vụ và chốt Q2 (người cấp grant); sau đó CTR-002 draft/submit/return trên test. Chưa có action ghi/duyệt/ký/xác nhận hiệu lực.

## Trạng thái tổng quan

| Hạng mục | Trạng thái | Ghi chú |
| --- | --- | --- |
| Tên sản phẩm | Đã chốt | TANPHAT ONE |
| Tên phân hệ | Đã chốt | TP Dashboard, TP Projects, TP Survey, TP Design, TP Contracts, TP Tasks, TP HR, TP Finance, TP Documents |
| Backend nền | Đã chạy | Odoo 20, `tp_core`, `tp_organization`, `tp_project`, `tp_contract`, `tp_api`, `tp_planning_api` |
| Database dev/test | Đã chạy | PostgreSQL 18, `tp_tanphat_dev`, `tp_tanphat_test` |
| Frontend nền | Đã chạy | React/TypeScript/Vite tại `/work/`, login riêng TANPHAT ONE gọi session Odoo; MFA/passkey có native fallback |
| Vertical slice đọc dự án | Đã kiểm chứng | login → `/me` → list/detail theo quyền → logout/session expiry |
| TP Contracts read slice | Đã kiểm chứng dev | CTR-001: contract/revision/line/approval reference/document, grant `financial_read` theo project, 4 API GET, 3 màn hình React; chỉ đọc, dữ liệu giả lập |
| Giao khoán/nghiệm thu/thanh toán | Chưa triển khai | Đã có thiết kế database; ghi/duyệt hợp đồng chưa mở |
| Workflow và ma trận quyền KD | Baseline phân tích hoàn tất | BIZ-001: BASE phê duyệt chính thức, tiền theo scope, hạn mức chưa biết; model/state/capability mới là đề xuất |
| Production | Chưa triển khai | Chưa có HTTPS, backup production, staging migration hoặc dữ liệu thật |
| Git history | Đã push | `main` và `origin/main` đồng bộ đến `00d4ddc7`: `395be562` (AUTH-001 + BIZ-001), `807018b9` (CTR-001), `00d4ddc7` (CHG-20261028-007). Commit tài liệu CHG-20261028-008 push trong cùng lượt; hai ID foundation cũ không tìm thấy |
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
- `tp_contract`: `tp.contract` (danh tính), `tp.contract.revision` (bản gốc/phụ lục/đính chính với review, chữ ký, thẩm quyền ký, hiệu lực tách riêng), `tp.contract.line` (phạm vi; nguồn bản trước và change kind), `tp.contract.line.amount` và `tp.approval.reference.amount` (số tiền nằm ở model riêng), `tp.approval.reference` (kết quả BASE có declared/verified), `tp.contract.document` (tệp phân loại general/financial). Snapshot theo ngày hiệu lực thay thế, không cộng phụ lục; null/0/chưa xác nhận/khác cơ sở thuế được phân biệt.
- `tp.project.grant` trong `tp_project`: capability `financial_read` theo user + project, có lý do, thời hạn và thu hồi; chỉ superuser cấp trong khi Q2 chưa chốt. Không có grant thì ORM/RPC, `read_group`, export, API và tải tệp tài chính đều không thấy tiền; Platform Manager/admin không mặc nhiên có tiền.
- API đọc `GET /api/v1/contracts`, `/contracts/{id}?as_of=`, `/contracts/{id}/revisions/{rid}`, `/contracts/{id}/documents/{did}/content`; ngoài scope trả 404, `Cache-Control: no-store`, field tiền bị bỏ khi thiếu grant. OpenAPI và TypeScript types đã cập nhật.
- TP Contracts frontend: danh sách có tìm kiếm/lọc theo project, chi tiết với bản áp dụng theo ngày, lịch sử revision, nhãn BASE đã/chưa xác minh, tài liệu, trang phạm vi công việc; số tiền định dạng từ decimal string, không đổi sang số JavaScript.
- Dev seed có ba hợp đồng giả lập (`HD-DEV-001/002/003`) và grant dev cho admin trên DEV-001; không có hồ sơ doanh nghiệp thật.

## Kiểm chứng gần nhất

Lượt `CHG-20261028-008` chỉ đổi tài liệu: thêm mục 4.4 trong [workflow KD](architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md) ánh xạ tên trạng thái nghiệp vụ sang field/giá trị trong code, đối chiếu trực tiếp với model `tp_contract` và DTO API; ghi nhận đã push `00d4ddc7`. Không chạy lại test ứng dụng vì không đổi code.

Lượt commit (`CHG-20261028-007`) tách thay đổi chưa commit thành hai commit local; sau đó đã push lên `origin/main`. Các file dùng chung được dựng lại về trạng thái trước CTR-001 bằng cách đảo các chỉnh sửa CTR-001 đã ghi nhận; áp lại các chỉnh sửa đó cho kết quả trùng 18/18 file hiện tại. Bản export của `395be562`: frontend typecheck đạt, Vitest 10 đạt; không chạy lại Odoo tests vì commit này không đổi backend. `395be562` giữ `docs/AI_WORKFLOW_STATE.json` của `03702d24` nên `ai_workflow.py check` tại đúng commit đó báo lệch; từ `807018b9` trở đi checker đạt. Quét diff không có credential/dữ liệu thật.

Lượt CTR-001 (`CHG-20261028-006`) chạy mới trên dev, không dùng kết quả cũ:

```text
Odoo tests (dev.py test, grep log): 0 failed, 0 error(s) of 53 tests
  TestContractAccess 15, TestContractModel 16, TestContractsApi 12, TestProjectAccess 6, TestProjectsApi 4
dev.ps1 upgrade + smoke: passed (login, /me, projects, contracts theo planner/admin)
check_contract.py --live: passed
Ruff: passed
Frontend typecheck: passed; Vitest: 14 passed; build (VITE_ODOO_DATABASE=tp_tanphat_dev): passed
Playwright E2E: 11 passed (3 contracts, login/project regression)
git diff --check: passed
```

Các ca được kiểm: reader chỉ metadata không thấy tiền ở ORM read/search/`read_group`/export, API và tệp; metadata dự án A + tiền dự án B; grant hết hạn/thu hồi có hiệu lực ở request sau; Platform Manager/admin không có tiền mặc định; khác project/company trả 404; revision không thuộc hợp đồng bị từ chối; tài liệu tài chính cần grant, tài liệu chung theo scope project; phụ lục thay thế giá trị (100 → 110 triệu, không 210); bản chưa có hiệu lực, ngày trùng, BASE approved nhưng chưa ký/hiệu lực; dòng chưa xác nhận là null chứ không phải 0. E2E kiểm UI ở 390px không tràn ngang; screenshot `.local/frontend-contract-detail.png` và `.local/frontend-contract-mobile.png` ngoài Git.

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

1. **Nghiệm thu BIZ-001/CTR-001:** cho chủ nghiệp vụ xem read slice bằng dữ liệu giả lập; bổ sung 2–3 bộ hồ sơ khử dữ liệu có phụ lục, khoán cấp 2 và correction/void. Chốt Q2: ai cấp/thu hồi grant `financial_read` theo project và ai record/verify BASE. Trước khi có câu trả lời, grant chỉ do superuser tạo; không tự gán cho Trưởng ban/QT-TC/lãnh đạo.
2. **CTR-002:** phát triển draft/submit/return hợp đồng trên test (capability, CSRF, version, idempotency, audit, negative tests). Chưa mở record/verify BASE, ký hoặc xác nhận hiệu lực pháp lý khi Q1–Q3 còn mở. Dùng đúng field/giá trị ở mục 4.4 của workflow KD; trước khi viết action, chốt transition hủy revision (`review_state = cancelled`: ai hủy, lý do).
3. **Sau Q2:** màn hình/API quản trị grant có audit; trước đó không mở API ghi grant. **PRJ-002** và các task còn lại theo [roadmap](ROADMAP.md).

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

CTR-001 (`807018b9`, đã push; AUTH-001/BIZ-001 ở `395be562`): grant `financial_read` chỉ superuser cấp đến khi Q2 được chốt; grant admin trong dev chỉ là fixture. Quyền tiền bảo vệ field số tiền, tệp tài chính và tổng; văn bản tự do (tên, mô tả, lý do) không được quét số tiền, nên quy tắc nhập liệu cần cấm ghi giá trị vào các trường đó. Admin/superuser vẫn có khả năng truy cập kỹ thuật. Chưa có view/menu Odoo native cho `tp_contract`; người dùng nghiệp vụ dùng API/React. Exit code `dev.py test` không đáng tin, phải đọc dòng `0 failed, 0 error(s) of N tests` trong log; INFO filestore GC `WinError 5` trên Windows vẫn xuất hiện. Upgrade dev ghi lại mật khẩu dev từ file secrets hiện có (giá trị không đổi). MFA thật chưa kiểm.

