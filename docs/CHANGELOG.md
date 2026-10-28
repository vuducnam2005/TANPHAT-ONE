# TANPHAT ONE — Nhật ký thay đổi

Mỗi lượt thay đổi code hoặc quyết định kiến trúc ghi một mục ngắn. Không ghi credential, dữ liệu thật hoặc log chứa bí mật.

## CHG-20261028-008 — Ánh xạ trạng thái hợp đồng và ghi nhận push

- Phạm vi: tài liệu; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: thêm mục 4.4 trong `TP_KD_WORKFLOW_AND_PERMISSIONS.md` ánh xạ tên trạng thái ở 4.1–4.3 sang field/giá trị trong code (`review_state`, `decision`, `verification_state`, `authority_status`, `signature_status`, `signature_authority_status`, `effectivity_status`, `lifecycle_state`) kèm constraint hiện có; liên kết từ `TP_BUSINESS_WORKFLOW.md`. Status ghi nhận `main` đã push đến `00d4ddc7`.
- Điểm cần chốt cho CTR-002: transition hủy revision (`cancelled` có trong code, 4.1 chưa có); cách confirm_effectivity cập nhật `effectivity_status` và `lifecycle_state` cùng lúc; thứ tự review → BASE reference chưa có constraint ở model.
- Kiểm tra: đối chiếu giá trị với model `tp_contract`, DTO `tp_planning_api` và nhãn frontend; kiểm liên kết Markdown; `git diff --check`; `ai_workflow.py finish/check`.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002.

## CHG-20261028-007 — Commit local AUTH-001, BIZ-001 và CTR-001

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `395be562` gồm login AUTH-001 (CHG-004) và baseline BIZ-001 (CHG-005) ở đúng trạng thái trước CTR-001; `807018b9` gồm CTR-001 (CHG-006). Stage theo từng đường dẫn, không `git add .`; chưa push.
- Kiểm tra: dựng lại file dùng chung bằng cách đảo chỉnh sửa CTR-001, áp lại khớp 18/18 file; export `395be562` typecheck đạt, Vitest 10 đạt; sau `807018b9` `git diff HEAD` rỗng, `ai_workflow.py check` đạt; quét diff không có credential/dữ liệu thật.
- Giới hạn: `395be562` giữ `AI_WORKFLOW_STATE.json` của `03702d24` nên checker tại commit đó báo lệch; không chạy lại Odoo tests cho commit này vì không đổi backend. Hai tài liệu TP_KD có xuống dòng Markdown bằng hai dấu cách như các tài liệu sẵn có.
- Next: push khi người dùng yêu cầu; nghiệm thu BIZ-001/CTR-001 và chốt Q2.

## CHG-20261028-006 — CTR-001: TP Contracts read slice

- Phạm vi: addon mới `tp_contract`, grant `financial_read` trong `tp_project`, API đọc trong `tp_planning_api`, OpenAPI, frontend TP Contracts, dev seed/smoke/checker và tài liệu. Không sửa `odoo/`/`addons/`, không mở API ghi/duyệt/ký/xác nhận hiệu lực, không đổi xác thực.
- Model: `tp.contract`, `tp.contract.revision`, `tp.contract.line`, `tp.contract.line.amount`, `tp.approval.reference`, `tp.approval.reference.amount`, `tp.contract.document`; review, chữ ký, thẩm quyền ký, hiệu lực và kết quả BASE là các trường riêng; snapshot theo ngày hiệu lực thay thế bản trước; tổng chỉ có giá trị khi mọi dòng đã xác nhận và cùng cơ sở thuế.
- Quyền: đọc metadata theo assignment project + company; số tiền và tài liệu `financial` thêm điều kiện grant `tp.project.grant` còn hiệu lực cho đúng project. Grant có lý do/thời hạn/thu hồi, không tự cấp, chỉ superuser tạo khi Q2 chưa chốt. Không group nào được ghi dữ liệu hợp đồng qua ORM/RPC.
- API: `GET /api/v1/contracts`, `/contracts/{id}?as_of=`, `/contracts/{id}/revisions/{revision_id}`, `/contracts/{id}/documents/{document_id}/content`; 404 ngoài scope, 400 `invalid_request`, `no-store`, bỏ field tiền khi thiếu grant.
- Frontend: route `/contracts`, chi tiết hợp đồng, trang phạm vi revision; nhãn BASE đã/chưa xác minh, ghi chú BASE approved không đồng nghĩa đã ký/hiệu lực, định dạng tiền từ decimal string, mobile 390px.
- Dữ liệu dev: ba hợp đồng giả lập `HD-DEV-001/002/003` và grant dev cho admin trên DEV-001. Không có hồ sơ thật.
- Quyết định: DEC-017.
- Kiểm thử thực chạy: Odoo `0 failed, 0 error(s) of 53 tests` (contract access 15, model 16, contracts API 12, project 10); upgrade + smoke đạt; `check_contract.py --live` đạt; Ruff đạt; frontend typecheck đạt, Vitest 14 đạt, build đạt, Playwright 11 đạt; `git diff --check` đạt.
- Giới hạn: Q1–Q3 còn mở; chưa có quản trị grant ngoài superuser; văn bản tự do không được quét số tiền; chưa có view Odoo native cho hợp đồng; exit code `dev.py test` không đáng tin. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002 draft/submit/return trên test.

## CHG-20261028-005 — BIZ-001: baseline workflow và ma trận quyền Ban Kinh doanh

- Phạm vi: phân tích năm nguồn S01–S05 và cập nhật tài liệu workflow/database/status/roadmap/decision; không sửa model, API, frontend, runtime hoặc import dữ liệu.
- Đã chốt theo yêu cầu người dùng: BASE là nơi phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận kết quả; quyền xem tiền mặc định cho người quản trị dự án đúng scope, Trưởng ban, QT-TC và lãnh đạo, hỗ trợ cần cấp riêng; hạn mức ký/duyệt chưa biết nên không đặt giả.
- Đã làm rõ: review nội bộ, BASE decision/evidence verification, chữ ký/hiệu lực pháp lý, revision snapshot và trạng thái thực hiện là các lớp riêng; contract/production/acceptance/invoice/cash/retention là domain record riêng; khoán cấp 2 không cộng trùng cấp 1; nhãn “GT phải xuất hóa đơn” trong mẫu được map là invoice issued thực tế.
- Tài liệu: `docs/architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md`, `docs/architecture/TP_KD_EVIDENCE_AND_ACCEPTANCE.md`; cập nhật `TP_BUSINESS_WORKFLOW.md`, `TP_DATABASE_DESIGN.md`, `TP_PLATFORM_SOURCE_STRUCTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `PROJECT_STATUS.md` và architecture index.
- Kiểm tra: đọc/đối chiếu source snapshot và hash manifest; hash bản NAS hiện tại vẫn khớp cả 5 source; đọc các range S03/S05 liên quan, xem trang phân công S02; `verify_baseline.py` đạt 27 link tương đối, 26 bảng Markdown nhất quán, 0 cell dữ liệu kế toán thực tế trong bản S05 đọc, 10 phép tính Decimal giả lập; `git diff --check` đạt. Không chạy macro/external link và không chạy bộ ứng dụng vì lượt này chỉ thay tài liệu.
- Giới hạn: chưa có 2–3 hồ sơ thật đã khử dữ liệu, văn bản hạn mức/bốn mắt/ủy quyền, BASE ID/evidence chuẩn hoặc feed kế toán thực tế; state/capability/ca nghiệm thu là thiết kế, chưa chạy Odoo. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: `CTR-001` read-only contract/revision/line + approval reference, field/attachment security và negative tests bằng dữ liệu giả; thu thập Q1–Q3 trước action ghi/chốt pháp lý.

## CHG-20261028-004 — Giao diện đăng nhập riêng TANPHAT ONE

- Phạm vi: `frontend/src/features/auth`, transport session frontend, visual design, E2E và tài liệu; không sửa Odoo core, model nghiệp vụ hoặc database.
- Đã thay đổi: `/work/` hiển thị cổng login React hai cột với minh họa cầu dây văng SVG, Be Vietnam Pro, hover/focus, animation vẽ cáp, reduced-motion, responsive mobile, hiện/ẩn mật khẩu, trạng thái pending/error và hướng dẫn hỗ trợ. Form gọi `/web/session/authenticate` same-origin, sau đó đọc `/api/v1/me`; không lưu password/token vào storage. MFA trả `uid: null` được giữ là bước xác thực bổ sung và có link native Odoo với redirect hiện tại.
- Quyết định: DEC-012. Database login không hardcode production: dev có fallback `tp_tanphat_dev`, production build yêu cầu `VITE_ODOO_DATABASE` khớp dbfilter.
- Kiểm thử thực chạy: `npm.cmd run typecheck --prefix frontend` đạt; `npm.cmd test --prefix frontend` đạt 10 tests; `VITE_ODOO_DATABASE=tp_tanphat_dev npm.cmd run build --prefix frontend` đạt; `npm.cmd run test:e2e --prefix frontend` đạt 8 tests (login, invalid credential, MFA handoff, gateway error, deep link, responsive, reduced-motion, permission/session regression); `git diff --check` đạt.
- Giới hạn: build production cần CI/release cung cấp `VITE_ODOO_DATABASE`; MFA code/passkey vẫn do native Odoo xử lý. Chưa đổi logo/branding ở native `/web/login`.
- Next: quay lại BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt state/role matrix.

## CHG-20261028-003 — OPS-001: backup và phục hồi dev cô lập

- Phạm vi: script backup/restore, hướng dẫn vận hành và bằng chứng thực chạy; không sửa model/API/frontend hoặc seed dữ liệu vào dev.
- Backup: snapshot nhất quán khi tạm dừng Odoo dev 18,95 giây, 314 bảng public, 37 tham chiếu attachment/27 blob, database dump 3.043.333 byte; source archive tại commit `d9e8ccdc`. Backup và credential giới hạn quyền, nằm ngoài Git.
- Kết quả: giải nén source từ backup; restore vào cluster mới cổng 55442, Odoo 18089, database/filestore riêng; 314 bảng/fingerprint và 37 attachment khớp trước neutralize; probe 2 attachment chỉ tồn tại ở bản sao; cluster/Odoo cô lập đã dừng; dev gốc smoke lại đạt.
- Kiểm thử tooling/tích hợp: 21 unit tests đạt, Ruff đạt; anonymous 401, planner/admin login + `/me` + list/detail DTO + query validation, 37 lượt tải tệp khớp SHA1/size và kiểm attachment theo scope đạt. Báo cáo cuối ở `.local/ops-001/rehearsals/20261028T064405723351Z/report.json`.
- Hướng dẫn: `ops/runbooks/BACKUP_RESTORE.md`. Chưa có lịch backup, backup ngoài máy hoặc phục hồi trên host khác.
- Next: BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt ma trận quyền/trạng thái.

## CHG-20261028-002 — Chốt baseline Git và publish handoff

- Phạm vi: kiểm chứng local `main` với `origin/main`, rà soát các file handoff đang chờ commit và chuẩn bị publish toàn bộ thay đổi hiện tại.
- Đã thay đổi: cập nhật trạng thái GIT-001 đã hoàn tất, chuyển Next action sang OPS-001, chốt DEC-010 và cập nhật roadmap; không sửa model/API/giao diện/database.
- Kiểm tra: `git fetch --prune origin`; local/remote cùng ở `a25a0182`; `git status`; kiểm tra credential-like patterns trong file dự kiến commit; checker trước lượt đạt.
- Publish: commit/push lên `origin/main` sẽ là baseline handoff mới của source hiện tại; xác nhận sau push bằng `git status` và `git rev-list`.
- Giới hạn: chưa diễn tập backup/restore, chưa xác minh production hoặc khôi phục hai commit ID cũ không tồn tại.
- Next: OPS-001.

## CHG-20261028-001 — AI handoff và workflow nghiệp vụ

- Phạm vi: tạo `AGENTS.md`, trạng thái dự án, quy trình bàn giao, workflow nghiệp vụ, changelog và checker local.
- Đã thay đổi: mọi phiên AI có thứ tự đọc bắt buộc; mỗi phiên code phải cập nhật status/changelog; state/role/transition của các phân hệ được phân biệt giữa thiết kế và đã triển khai.
- Kiểm chứng trạng thái: local hiện có baseline `82e9ea27`/`a25a0182`; bổ sung DEC-010 để phiên sau không thực hiện lại phục hồi Git theo ghi chú cũ. Không sửa metadata hoặc tạo commit trong lượt này.
- Kiểm thử: checker unit test 11/11 đạt; Ruff đạt; `git diff --check` đạt; kiểm tra `start`/`finish`/`check` đạt.
- Giới hạn: checker không thay thế Git, review nghiệp vụ, security test hoặc phê duyệt của người dùng.
- Next: xử lý Git baseline, rồi chốt state/role matrix cho TP Projects và TP Contracts.

## 2026-10-28 — Foundation và naming

- **Phạm vi:** Odoo foundation, project access, API v1, React workspace, naming TANPHAT ONE, chín tên phân hệ.
- **Đã có:** `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`; frontend đọc project theo session Odoo.
- **Kiểm thử:** Odoo 10 tests đạt; OpenAPI live đạt; frontend typecheck/build/unit/prototype/E2E đạt; smoke đạt.
- **Quyết định:** một PostgreSQL database cho mỗi môi trường; quyền dùng company/project/assignment; technical addon identifiers giữ ổn định.
- **Giới hạn:** chưa có contracts, allocations, settlements, import hoặc production; Git metadata cần baseline sạch.
- **Next:** chốt state/role matrix và triển khai `tp_contract` read vertical slice.

## Mẫu mục nhập

```text
## CHG-YYYYMMDD-NNN — <tên thay đổi>
- Phạm vi:
- Đã thay đổi:
- Workflow/model/API bị ảnh hưởng:
- Kiểm thử:
- Giới hạn:
- Next:
```
