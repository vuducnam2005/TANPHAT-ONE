# TANPHAT ONE — Trạng thái dự án

**Cập nhật:** 28/10/2026 (Asia/Saigon)  
**Thư mục:** `C:\TANPHAT ONE`  
**Mục tiêu hiện tại:** BIZ-002 — chuẩn bị và nghiệm thu thiết kế nghiệp vụ toàn công ty trước khi tiếp tục code; bắt đầu chi tiết từ Kế hoạch Kinh doanh. Odoo + React/TypeScript riêng giữ nguyên.
Last change: `CHG-20261028-013`

**Phase:** thiết kế và nghiệm thu nghiệp vụ, chưa chuyển sang phát triển ứng dụng.
**Task hiện tại:** BIZ-002 — đã lập bộ thiết kế A–M, RACI, workflow, dữ liệu/quyền, tích hợp/KPI, kịch bản giả lập và checklist theo slice; đây là baseline đề xuất để công ty review, chưa phải quy chế/UAT được duyệt. [Điểm vào bộ tài liệu](architecture/TP_BIZ002_DESIGN_PACKAGE.md).
**Next task:** tiếp tục Q2 theo ma trận đề xuất Q2-P1, thu thập vai trò/căn cứ công ty và bundle thực tế khử dữ liệu; sau đó điền nhật ký 7.1. SIM-P1 đã chuẩn bị ba bundle mô phỏng và đặc tả CTR-002a-P1 để review, không phải UAT/test. Người dùng quyết định khi nào chuyển sang code; không cần đóng cả Q1–Q14 cùng lúc. CTR-001 read slice giữ nguyên; CTR-002 và mở rộng CTR-001 chờ chuyển giai đoạn, chưa có action ghi/duyệt/ký/xác nhận hiệu lực.

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
| Bộ thiết kế nghiệp vụ toàn công ty | BIZ-002 Q2-P1/SIM-P1/CTR-002a-P1; chờ công ty review | Ma trận 11 hành động Q2; inventory thiếu bundle thực tế; 3 bundle mô phỏng có đường bình thường/trả-sửa-gửi lại/correction-bàn giao; action/version/actor/test gate CTR-002a. Không triển khai chức năng hoặc chốt quy chế |
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

Lượt `CHG-20261028-013` chỉ phân tích/tài liệu: baseline giữ 18 đường dẫn đã sửa/chưa tracked từ các lượt trước tại HEAD `0c3083fb`, không checkpoint cũ, checker CHG-012 đạt; Odoo/PostgreSQL đều dừng. Đối chiếu tĩnh source xác nhận API hợp đồng chỉ có GET và ACL chỉ đọc, chưa có action ghi, aggregate version, snapshot submit, idempotency hay audit transition. Chưa phát hiện sai lệch runtime mới ngoài các giới hạn đã ghi; không setup/upgrade/seed hoặc chạy lại app tests.

Đã lập Q2-P1 (11 action), SIM-P1 (3 bundle/19 chặng mô phỏng), CTR-002a-P1 (6 action + actor fixture + CSRF/version/idempotency/audit/outbox + ca kiểm). Phản hồi người dùng chỉ giao tiếp tục phân tích, không chốt quyền công ty; nhật ký 7.1 đều `proposed`, business acceptance pending. Kiểm tài liệu bằng `.local/biz-002/review_q2.py`: 19 tài liệu, 134 link tương đối, 104 bảng nhất quán, 9 liên kết heading, 6 dòng log proposed, 19 chặng SIM và 10 phép tính Decimal giả lập đạt; 5 hash bản sao S01–S05 khớp registry, không xác minh NAS hiện hành. Maintained code 108 file không đổi so checkpoint; `git diff --check` đạt. Báo cáo `.local/biz-002/q2_review_validation.json` ngoài Git; handoff cuối lượt theo CHG-013, không dùng checker hoặc mô phỏng làm nghiệm thu nghiệp vụ.

Lượt `CHG-20261028-012` rà soát lại toàn bộ handoff BIZ-002 bằng validator riêng: 19 tài liệu, 121 liên kết tương đối, 95 bảng có header/fence đúng, 13 cặp walkthrough normal/rejected, 13 ca correction A–M và Q1–Q14 đều có trong readiness; hash bản sao nguồn S01–S05 trong `.local/biz-001` vẫn khớp registry. Lượt này không xác nhận lại hash trực tiếp trên NAS; báo cáo nói rõ giới hạn đó tại `.local/biz-002/review_validation.json` (ngoài Git). Maintained code vẫn 108 file không đổi; business acceptance vẫn pending và các dòng nhật ký còn `open`. Đây là kiểm tra tài liệu/handoff, không phải UAT.

Lượt `CHG-20261028-011` theo yêu cầu kiểm tra source và bước tiếp theo: rà soát read slice CTR-001, model/quyền/API/test và BIZ-002; chưa phát hiện lỗi chặn trong phạm vi đọc hiện tại. Kiểm tra thực chạy: `npm.cmd run typecheck --prefix frontend` đạt; `npm.cmd test --prefix frontend` đạt 14 tests; Ruff trên `custom_addons`, `scripts/dev.py`, `scripts/check_contract.py` đạt; `dev.ps1 test` chạy trên DB tách biệt `tp_tanphat_test`, summary **0 failed, 0 error(s) of 53 tests**. Vẫn có INFO filestore GC `WinError 5`; không coi test đạt là đã xử lý ổn định filestore production. Không chạy lại build/E2E trong lượt này; các kết quả đó ở CHG-006 là lịch sử. Odoo/PostgreSQL ban đầu đều dừng; test có khởi động PostgreSQL và đã `dev.ps1 stop`/`status` xác nhận cả hai dừng lại sau kiểm tra. Không upgrade/seed dev hoặc đổi credential.

Lượt CHG-011 bổ sung nhật ký kết luận thực tế theo Q/slice/bundle trong [readiness mục 7.1](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md): RACI/người xác nhận bằng mã nội bộ, scope/môi trường, trạng thái, bằng chứng/hash, ngày/phiên bản, gap và bước tiếp theo; khi đó tất cả dòng nghiệp vụ vẫn `open`. Làm rõ thứ tự Q2 → walkthrough 2–3 bundle → ghi kết luận/gap → người dùng quyết định chuyển code → CTR-002a test. Phân biệt technical check với business acceptance và quyền mở code; phần giao khoán/nghiệm thu/thanh toán chưa runtime chỉ review tài liệu. Code ứng dụng không đổi; kiểm tài liệu và handoff cuối lượt ghi tại CHG-011.

Lượt `CHG-20261028-009` (BIZ-002) chỉ tài liệu. Baseline trước sửa: Git sạch tại `0c3083fb` (CHG-008), không checkpoint cũ; `ai_workflow.py check` đạt; `dev.ps1 status` xác nhận Odoo/PostgreSQL dev đang lắng nghe. Không có draft code `tp_contract`/`tp.project.grant` chưa bàn giao; không đóng thay batch code nào. Đã start checkpoint tài liệu riêng. Hash 5 nguồn NAS + bản sao khớp registry; tái sử dụng trích xuất BIZ-001, không chạy macro/external link hoặc đưa dữ liệu thật vào Git.

BIZ-002 bổ sung 7 tài liệu: bản đồ A–M, workflow A–E/F–M, dictionary/ERD/quyền, tích hợp/KPI/màn hình/API thiết kế, kịch bản/readiness và chỉ mục/gap analysis. Sửa mô tả cũ nói hợp đồng chưa có runtime và `verification_state declared/verified` thành read slice đã có và `pending/verified/disputed` đúng code. Q1–Q8 giữ nguyên; Q9–Q14 bổ sung project/task, kỹ thuật/KCS, HR/hồ sơ, import, KPI và vận hành. Kết quả kiểm tài liệu lượt này được ghi tại CHANGELOG CHG-009; không chạy bộ ứng dụng vì không đổi code, schema hoặc runtime, không nhận walkthrough giả lập là UAT/Odoo tests.

Lượt `CHG-20261028-010` tiếp tục chỉ tài liệu: đồng bộ enum/state giữa workflow và dictionary (task return, payment request, acceptance signature, lifecycle A–M), thống nhất unique key allocation theo company, bổ sung đường returned → revision → resubmit/handover/revoke, tách BASE rejected khỏi verification disputed, và ghi các công thức kiểm soát Decimal/known-at/aging/advance/retention/phân bổ nhiều payment ở mức đề xuất. Không đổi source/runtime; chỉ cập nhật sau rà soát consistency, chưa chạy application tests.

Kiểm cuối CHG-010: 19 tài liệu duy nhất, 119 link/94 bảng có header và fence đúng; đủ walkthrough normal/rejected + correction A–M và Q1–Q14; 10 phép tính Decimal bổ sung đạt. Validator BIZ-001 riêng đạt 5 source hash, 48 link/28 bảng, 10 Decimal checks; 108 file maintained code so checkpoint không đổi. `git diff --check` đạt; handoff `finish/check` theo CHG-010. Báo cáo kiểm tài liệu ở `.local/biz-002/validation.json` ngoài Git; chưa UAT công ty hoặc chạy Odoo/frontend tests trong lượt tài liệu này.

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

1. **Bước kế tiếp cụ thể — Q2-A:** chủ nghiệp vụ KD/chủ nguồn BASE review 5 action hồ sơ/BASE trong Q2-P1, cung cấp vai trò theo scope và căn cứ phân công; ghi accepted/rejected/gap riêng từng nội dung vào [nhật ký readiness 7.1](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md). Xong khi có người xác nhận được ủy quyền, phạm vi, bằng chứng, ngày/phiên bản; không cần đóng toàn Q1–Q14. Q2-B quyền/grant/bàn giao tiếp nhận theo nhóm sau, không gán quyền người thật từ chức danh.
2. **Đối chiếu thực tế thay SIM-P1:** theo danh sách 7.1.2, KD-OWNER tập hợp B01/B02 và HR/owner quyền tập hợp B03 khử dữ liệu; đi từng chặng contract→phụ lục→khoán→NT→request→chứng từ nếu có căn cứ, ghi thiếu nếu chưa có. Chưa bundle thực tế đủ điều kiện; 3 bundle mô phỏng/19 chặng hiện không thay UAT. F/G/J/K/M vẫn chờ chủ chuyên môn; khi chỉ nói “tiếp tục”, tiếp tục review/gap, không mở module/action.
3. **Chỉ sau yêu cầu chuyển giai đoạn rõ của người dùng:** CTR-002a-P1 tại readiness 7.1.3 là đầu vào phát triển thử test giả lập; thực thi snapshot S1/S2 riêng với revision pháp lý, guard backend/CSRF/version/idempotency/audit/outbox và test hợp lệ/sai quyền/sai state/stale/retry. Không BASE/legal/payment/cancel/grant admin; Q2 trước người dùng thật/pilot, Q1–Q4/Q8 theo action phụ thuộc. Không mở đồng loạt các slice.

## Không được làm ở bước hiện tại

- Không import toàn bộ Excel thật.
- Không xây đủ chín phân hệ cùng lúc.
- Không tạo workflow engine tổng quát hoặc reporting database khi chưa có hai workflow mẫu đã kiểm chứng.
- Không cho frontend tự tính/ghi state, tiền, quyền hoặc tổng hợp tài chính.
- Không triển khai production từ database dev.

## Blocker/rủi ro

**BIZ-002:** hoàn tất baseline tài liệu không có nghĩa công ty chốt toàn bộ quy trình. Q1–Q14 có đầu mối theo vai trò, chưa có tên người chịu trách nhiệm được bổ nhiệm hoặc văn bản xác nhận. Q2 chặn pilot cấp quyền/ghi; Q1/Q3 chặn pháp lý/evidence; Q4/Q6/Q8 chặn số tài chính chính thức; Q9–Q14 chặn các slice mở rộng/vận hành tương ứng.

Lượt CHG-013 giữ Q2 ở `proposed/open`: phản hồi của người dùng cho phép tiếp tục phân tích nhưng chưa bổ nhiệm vai trò, chưa xác nhận căn cứ ủy quyền hoặc quy tắc cùng/khác người. `TP_BIZ002_ACCEPTANCE_AND_READINESS.md` mục 7.1 ghi Q2-A/Q2-B, SIM-P1 B01–B03 và CTR-002a-P1; không có bundle thực tế khử dữ liệu đủ chuỗi trong inventory lượt này. Đây là gap đầu vào, không phải bằng chứng công ty không có hồ sơ.

CTR-002a-P1 hiện đủ làm tài liệu chuẩn bị cho development test sau khi người dùng mở giai đoạn: create/edit draft, submit/return/rework/resubmit, actor fixture, scope/capability, version/snapshot, CSRF, idempotency, transaction/audit/outbox và ca negative/concurrent/retry. Chưa code, chưa chạy test action ghi, chưa mở grant admin/BASE/legal/payment/pilot.

**Sai lệch policy mục tiêu so với runtime đọc hiện có:** grant có reason/date_end/active/granted_by nhưng chưa có date_start/revoked_by/at/reason, delegation hay audit action riêng; superuser có thể unlink grant, không phải ledger bất biến. `financial.export` chưa là capability runtime: export group chuẩn + grant đọc có thể export trong scope. DTO metadata BASE vẫn trả provenance/decision_reason/authority_source/tên người quyết định/hash cho project reader; text tự do chưa quét tiền. BIZ-002 yêu cầu review allowlist/redaction/field policy và audit trước pilot; không sửa code hoặc tự nhận các đề xuất đã được enforce.

Checker dùng danh sách policy cố định; các tài liệu BIZ-002 mới được kiểm riêng link/bảng/bao phủ/nội dung, không tự hash mọi Markdown liên kết. `finish/check` chỉ chứng minh maintained code/handoff trong phạm vi checker, không thay kiểm thiết kế hoặc chấp thuận công ty. Không commit/push trong lượt này.

Git metadata từng bị tách trong lần đổi thư mục trước. Ghi chú phục hồi cũ trong `.local/git-recovery/STATUS.txt` mô tả thời điểm chỉ có `ea975fb`; không dùng ghi chú đó thay cho trạng thái kiểm chứng hiện tại.

Kiểm tra chỉ đọc trong lượt AI-001/GIT-001 xác nhận `main` và `origin/main` đều có `a25a0182` trước khi publish; remote là `https://github.com/vuducnam2005/TANPHAT-ONE.git`. Diff model/API/frontend nền với HEAD rỗng; working tree chỉ có tài liệu/tooling handoff đang sửa/thêm. `git cat-file -e` không tìm thấy `fbad3686`/`4e47fddb`, nên không dựng lại hai ID này. Commit/push CHG-20261028-002 tạo mốc publish cho source hiện tại; điều đó không thay thế backup/restore hoặc bảo đảm production.

Lượt AI-001 không sửa Git metadata, không stage hoặc commit và không xử lý migration thư mục. Checker bàn giao dùng hash source độc lập; không dùng kết quả hash để kết luận Git đã đồng bộ hoặc production đã sẵn sàng.

Đã xác nhận nơi duyệt chính thức là BASE và phạm vi xem tiền; chưa xác minh văn bản ký/duyệt/hạn mức, bốn mắt, BASE ID/evidence thực tế, cơ sở thuế/ngày hiệu lực và nghiệm thu ma trận với chủ nghiệp vụ. S05 bản đọc chưa có hàng import kế toán thực tế, không dùng làm chứng cứ reconcile đạt. Các điểm vận hành còn thiếu: backup ngoài máy, mã hóa/retention/RPO/RTO, host khác, staging/production. Backup local chưa mã hóa; credential nằm ngoài Git. Odoo test Windows từng có INFO filestore GC `WinError 5`; kiểm tra dự án/API không chứng minh toàn bộ hồ sơ tệp vận hành ổn định.

Lượt BIZ-001 giữ nguyên các thay đổi login chưa commit từ AUTH-001, không commit/push hoặc sửa Git metadata. Hai tài liệu chi tiết BIZ mới được kiểm riêng về liên kết/nội dung; checker hiện dùng danh sách policy cố định, không tự hash mọi Markdown được liên kết.

CTR-001 (`807018b9`, đã push; AUTH-001/BIZ-001 ở `395be562`): grant `financial_read` chỉ superuser cấp đến khi Q2 được chốt; grant admin trong dev chỉ là fixture. Quyền tiền bảo vệ field số tiền, tệp tài chính và tổng; văn bản tự do (tên, mô tả, lý do) không được quét số tiền, nên quy tắc nhập liệu cần cấm ghi giá trị vào các trường đó. Admin/superuser vẫn có khả năng truy cập kỹ thuật. Chưa có view/menu Odoo native cho `tp_contract`; người dùng nghiệp vụ dùng API/React. Exit code `dev.py test` không đáng tin, phải đọc dòng `0 failed, 0 error(s) of N tests` trong log; INFO filestore GC `WinError 5` trên Windows vẫn xuất hiện. Upgrade dev ghi lại mật khẩu dev từ file secrets hiện có (giá trị không đổi). MFA thật chưa kiểm.

