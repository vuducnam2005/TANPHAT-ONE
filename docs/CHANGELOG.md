# TANPHAT ONE — Nhật ký thay đổi

Mỗi lượt thay đổi code hoặc quyết định kiến trúc ghi một mục ngắn. Không ghi credential, dữ liệu thật hoặc log chứa bí mật.

## CHG-20261028-014 — CTR-002a: draft → gửi rà soát → trả lại → sửa → gửi lại (chỉ test)

- Phạm vi: code CTR-002a-P1 theo DEC-020, chỉ trên `tp_tanphat_test` với dữ liệu giả và actor fixture. Không upgrade/seed `tp_tanphat_dev`, không cấp grant cho người dùng thật, không đổi credential. Ngoài phạm vi và vẫn đóng: complete_review, cancel revision, record/verify BASE, chữ ký/thẩm quyền ký, hiệu lực, giao khoán/nghiệm thu/thanh toán, quản trị grant người dùng thật.
- Model/security (`tp_contract` 20.0.1.1.0, `tp_project`): `tp.project.grant` thêm capability `financial.draft_edit`, `contract.draft_edit`, `contract.submit`, `contract.review_commercial` theo project + phòng ban (`financial.read` giữ theo project); `tp.contract` thêm `department_id` lấy từ phòng chủ trì project và `aggregate_version` khóa `FOR UPDATE`. Model mới `tp.contract.submission` (S1/S2 bất biến, metadata snapshot + hash), `tp.contract.submission.amount` (snapshot tiền tách riêng, ACL như amount CTR-001), `tp.contract.audit` (append-only), `tp.contract.outbox` (một event/người nhận, retry giữ event), `tp.contract.idempotency`. Guard ORM chặn ghi state/version/BASE/legal ngoài workflow, sửa nội dung đã gửi, thay/xóa binary S1 qua `tp.contract.document` và `ir.attachment`. Migration post-migrate gán phòng chủ trì project cho hợp đồng cũ; project chưa có phòng chủ trì thì action trả `scope_incomplete`.
- Action T1–T6: `create_draft`, `create_amendment` (draft phụ lục, mang phạm vi bản trước), `edit_draft`, `submit_review` (draft → `in_review`, reviewer phải có assignment + capability trong cùng project/phòng), `return_review` (`in_review` → `returned`, lý do bắt buộc, issue theo dòng), `begin_rework` (`returned` → `draft`, giữ S1). Mỗi action một transaction: scope/capability kiểm lại, `expected_version`, idempotency theo actor + action + object + fingerprint (gồm version), audit + outbox; replay trả kết quả cũ sau khi kiểm lại quyền; khác payload 409.
- API (`tp_api`, `tp_planning_api`): `GET /contracts/{id}/reviewers`, `POST /contracts`, `POST /contracts/{id}/amendments`, `PATCH /contracts/{id}/revisions/{rid}`, `POST …/submit|return|rework`. Ghi bắt buộc Fetch Metadata/Origin same-origin, `X-CSRF-Token` gắn session, JSON object, `Idempotency-Key`; lỗi 400/401/403/404/409/415/422 có code và `request_id`, `no-store`. DTO thêm `version`, `allowed_actions`, `working_revision_id`, `submissions`; tiền vẫn decimal string và chỉ khi có `financial_read`. OpenAPI cập nhật trước frontend, types sinh lại.
- Frontend: form tạo hợp đồng nháp và phụ lục nháp; trình sửa bản nháp (header, revision, dòng phạm vi; cột tiền chỉ khi có `financial_read` + `financial_draft_edit`, chỉ gửi số tiền đã sửa, chưa xác nhận gửi `null`); gửi rà soát chọn reviewer từ API, tóm tắt sửa bắt buộc từ lần gửi thứ hai; trả lại có lý do và issue theo dòng; mở lại để sửa; lịch sử các lần gửi. Nút lấy từ `allowed_actions`; mỗi intent giữ một Idempotency-Key khi retry lỗi mạng/5xx; 409 stale hiện “Tải lại bản mới nhất”.
- Test: Odoo `dev.py test` trên `tp_tanphat_test` **0 failed, 0 error(s) of 72 tests** (16 test workflow ORM + 3 HttpCase: T-P01, T-N01…T-N09, cùng regression CTR-001); Ruff `tp_api tp_contract tp_planning_api tp_project` đạt; `npm run api:types` + typecheck đạt; Vitest 22 đạt; build với `VITE_ODOO_DATABASE=tp_tanphat_test` đạt; Playwright `contract-workflow.spec.ts` 3 đạt (mock `/api/v1/**`, không Odoo/DB). Không có race song song thật; UI chưa chạy với Odoo live.
- Giới hạn: một grant hiệu lực cho mỗi (project, user, capability); đổi phòng chủ trì project không đổi scope hợp đồng cũ; outbox chưa có cron/kênh gửi/inbox; idempotency chưa có retention; chưa chọn đối tác trong UI; danh sách project ở form tạo lấy 20 bản đầu; xóa dòng có tiền cần quyền sửa tiền. Business acceptance pending; Q2 chặn người dùng thật/pilot.
- Next: người dùng review và quyết định commit; nếu cần xem UI trên Odoo thật thì cần cho phép upgrade database dev hoặc dựng instance test. Q2-A/Q2-B và bundle thực tế vẫn là cổng trước pilot.

## CHG-20261028-013 — Q2-P1, walkthrough mô phỏng và cổng CTR-002a trước code

- Phạm vi: chỉ tài liệu và handoff BIZ-002; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không triển khai CTR-002a, grant admin, record/verify BASE, ký, hiệu lực hay thanh toán.
- Đã làm: bổ sung ma trận Q2-P1 11 hành động tại `TP_KD_WORKFLOW_AND_PERMISSIONS.md` mục 7.4; tách `financial.read`, sửa hồ sơ, xuất dữ liệu và `grant.manage`; tách người quyết định grant/revoke khỏi người thao tác kỹ thuật; giữ cùng/khác người, hạn mức và bốn mắt ở trạng thái chưa xác nhận.
- Bổ sung readiness mục 7.1: ghi phản hồi người dùng cho phép tiếp tục phân tích nhưng chưa bổ nhiệm vai trò; cập nhật Q2-A/Q2-B; inventory nói rõ chưa có bundle thực tế khử dữ liệu đủ chuỗi; chuẩn bị SIM-P1 B01 bình thường, B02 trả–sửa–gửi lại, B03 correction/void và bàn giao/revoke. Đây là mô phỏng logic, không phải UAT/test/nghiệm thu.
- Bổ sung CTR-002a-P1: snapshot vòng gửi bất biến trong revision nháp, rework/resubmit không tạo correction pháp lý; actor fixture/scope; CSRF, optimistic aggregate version, idempotency, transaction/audit/outbox, negative/concurrent/retry cases và tiêu chí cổng. Đối chiếu source tĩnh xác nhận CTR-001 chỉ GET/read, chưa có action ghi/version/audit/idempotency; không mở ACL ghi.
- Cập nhật dictionary/workflow K/design package/evidence/status/roadmap để không gộp state handover với grant, không coi hash bản sao nguồn là hồ sơ thực tế và giữ thứ tự Q2 → bundle → quyết định chuyển code → CTR-002a test. Q1/Q3/Q4/Q6/Q8/Q9–Q14 tiếp tục mở theo cổng.
- Kiểm tra trong lượt: `.local/biz-002/review_q2.py` đạt 19 tài liệu/134 link/104 bảng, 9 link heading, 11 action Q2, 6 dòng log proposed, 19 chặng SIM và 10 phép tính Decimal giả lập. Đối chiếu source tĩnh; 5 hash bản sao S01–S05 khớp manifest, không kiểm NAS hiện hành; maintained code 108 file không đổi so checkpoint; `git diff --check` đạt. Báo cáo `.local/biz-002/q2_review_validation.json` ngoài Git. Không chạy Odoo/frontend/app tests vì chỉ tài liệu; `ai_workflow.py finish/check` ghi handoff sau kiểm nội dung; checker không xác nhận nghiệp vụ.
- Next: chủ nghiệp vụ xác nhận vai trò/căn cứ Q2 và cung cấp 2–3 bundle khử dữ liệu; sau yêu cầu chuyển giai đoạn rõ ràng mới cân nhắc code CTR-002a-P1 trên test.

## CHG-20261028-012 — Kiểm tra lại toàn bộ tài liệu BIZ-002 và giới hạn bằng chứng nguồn

- Phạm vi: kiểm tra tài liệu/handoff; không đổi source ứng dụng, schema, API, database, runtime hoặc quyền. Không có quyết định nghiệp vụ mới.
- Hiệu chỉnh dòng `reported_checks` của handoff CHG-011: bộ kiểm BIZ-001/NAS chưa có báo cáo mới để xác nhận, nên không dùng dòng “passed” đó làm bằng chứng kiểm NAS/Decimal trong lượt này; state mới chỉ ghi các kiểm tra vừa xác minh được.
- Kết quả: 19 tài liệu, 121 link tương đối, 95 bảng có header/fence nhất quán; walkthrough normal/rejected 13 cặp, correction A–M 13 ca, Q1–Q14 đủ trong readiness. Hash năm bản sao nguồn S01–S05 trong `.local/biz-001` khớp registry; lượt này **không** xác nhận hash trực tiếp trên NAS và ghi rõ giới hạn trong `.local/biz-002/review_validation.json` ngoài Git.
- Maintained code vẫn 108 file không đổi; business acceptance pending, nhật ký Q2/bundle/CTR-002a còn `open`. Đây là kiểm tra handoff/tài liệu, không phải UAT hay phê duyệt công ty.
- Next: giữ thứ tự Q2 → 2–3 bundle khử dữ liệu → ghi quyết định/gap → người dùng chọn giai đoạn; chỉ sau đó mới xem xét CTR-002a test.

## CHG-20261028-011 — Kiểm tra CTR-001 và chuẩn bị xác nhận BIZ-002 theo Q2

- Phạm vi: review source/quyền/API/test và tài liệu; chỉ sửa readiness, status, roadmap, changelog và state bàn giao. Không phát triển CTR-002a, không thay code ứng dụng, schema/API hoặc credential; không commit/push.
- Kết quả review: chưa phát hiện lỗi chặn trong CTR-001 read slice. BIZ-002 đủ cấu trúc để review nghiệp vụ; chưa có xác nhận công ty, Q1–Q14 vẫn mở. Các giới hạn đã ghi giữ nguyên: metadata BASE text tự do có thể chứa tiền, grant thiếu ledger revoke/delegation bất biến, chưa có capability export tiền riêng; phải xử lý trước pilot dữ liệu thật.
- Đã bổ sung: nhật ký quyết định/nghiệm thu tại readiness mục 7.1, có scope/môi trường, RACI/người xác nhận bằng mã nội bộ, kết luận/trạng thái, evidence/hash, ngày/phiên bản và gap/next action. Các dòng Q2/bundle/CTR-002a đều `open`; không điền giả tên, bằng chứng hoặc chấp thuận. Mục 7.2 tách kiểm tra kỹ thuật khỏi nghiệm thu và quyết định mở code. Làm rõ thứ tự Q2 → 2–3 bundle → ghi kết luận → quyết định người dùng → CTR-002a test; không chờ đóng đồng loạt Q1–Q14.
- Kiểm tra source thực chạy: frontend typecheck đạt; Vitest 14 tests đạt; Ruff `custom_addons scripts/dev.py scripts/check_contract.py` đạt; `dev.ps1 test` trên `tp_tanphat_test` báo **0 failed, 0 error(s) of 53 tests**. Còn INFO filestore GC `WinError 5` như đã ghi. Không chạy lại build/E2E; không nhận kết quả lịch sử thành mới.
- Runtime: ban đầu Odoo/PostgreSQL dừng; test khởi động PostgreSQL, dùng DB test riêng; đã dừng và kiểm status cả hai dừng sau kiểm tra. Không upgrade/seed database dev. Maintained code được đối chiếu checkpoint cuối lượt; không thay source trong batch này.
- Kiểm tài liệu/handoff: kết quả kiểm link/bảng/fence/bao phủ, `git diff --check` và `ai_workflow.py finish/check` được ghi trong state bàn giao sau khi hoàn tất kiểm tra; checker không thay bằng chứng nghiệp vụ.
- Next: Q2 trách nhiệm/quyền Ban KD và walkthrough hợp đồng với hồ sơ khử dữ liệu, ghi nhật ký; chỉ người dùng quyết định chuyển sang CTR-002a test. Chưa mở action BASE/legal/tiền thật hoặc grant admin.

## CHG-20261028-010 — Đồng bộ state, ngoại lệ và công thức trong gói BIZ-002

- Phạm vi: chỉ tài liệu; không đổi code ứng dụng, schema, API, frontend, runtime, dữ liệu hoặc credential.
- Đã làm: đồng bộ state/transition giữa workflow F–M và dictionary (returned/resubmit, BASE rejected vs verification disputed, acceptance signature, lifecycle); thống nhất mã allocation theo company; bổ sung handover/revoke/restore/share và đường correction; bổ sung công thức kiểm soát hợp đồng, cấp 1/2, khối lượng, payment allocation, tạm ứng, giữ lại, aging/freshness và known-at. Cập nhật readiness walkthrough để dùng basis/case `null`/`0`/unknown đúng nghĩa.
- Quyết định/workflow: vẫn Proposed/Unconfirmed theo BIZ-002; BASE official, chữ ký/hiệu lực/posting tách lớp; Q1–Q14 chưa đóng. Không biến công thức giả lập thành công thức tài chính doanh nghiệp hoặc mở action.
- Kiểm tra: `git diff --check` đạt; validation riêng đạt 19 tài liệu duy nhất, 119 link tương đối, 94 bảng có header/fence đúng, 13 cặp walkthrough normal/rejected và 13 ca correction A–M, Q1–Q14 có đầu mối/cổng; 10 phép tính Decimal kiểm công thức bổ sung đạt. `.local/biz-001/verify_baseline.py` đạt (5 hash khớp, 48 link/28 bảng baseline, 10 Decimal checks riêng, 108 file maintained code không đổi); không chạy Odoo/frontend test vì code/runtime không đổi. Báo cáo kiểm tài liệu `.local/biz-002/validation.json` ngoài Git; không nhận walkthrough là UAT. `ai_workflow.py finish/check` ghi handoff CHG-010.
- Next: chủ nghiệp vụ review bộ BIZ-002 và hồ sơ khử dữ liệu, trả lời Q theo slice; người dùng quyết định khi nào chuyển sang code.

## CHG-20261028-009 — BIZ-002: bộ thiết kế nghiệp vụ toàn công ty trước code

- Phạm vi: chỉ tài liệu/workflow handoff; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không setup/upgrade/seed và không gửi message sang task khác.
- Đã làm: rà soát khoảng trống và baseline; kiểm hash năm nguồn S01–S05 với `.local/biz-001/manifest.json`; bổ sung [bản đồ A–M/RACI](architecture/TP_ENTERPRISE_PROCESS_MAP.md), [workflow A–E](architecture/TP_PROCESS_WORKFLOWS_A_E.md), [workflow F–M](architecture/TP_PROCESS_WORKFLOWS_F_M.md), [từ điển dữ liệu/ERD/ma trận quyền](architecture/TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md), [tích hợp/KPI/màn hình/API thiết kế](architecture/TP_BIZ002_INTEGRATION_AND_REPORTING.md), [kịch bản/readiness/Q1–Q14](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md) và [chỉ mục/gap analysis](architecture/TP_BIZ002_DESIGN_PACKAGE.md). Cập nhật `TP_BUSINESS_WORKFLOW`, database/source architecture, architecture README, `PROJECT_STATUS`, `ROADMAP`, `DECISIONS`, `AI_CHANGE_WORKFLOW`.
- Phân loại: quyết định người dùng (BASE official, Odoo + React riêng, một DB/môi trường, scope tiền) tách khỏi quan sát E01–E18, đề xuất RACI/capability/transition/KPI và điểm chưa xác nhận Q1–Q14. Ghi rõ grant runtime hiện thiếu ledger revoke/delegation/audit riêng và `financial.export` capability; không tự coi policy mục tiêu là đã enforce.
- Kiểm tra: `scripts/ai_workflow.py start` trước sửa; `.\.venv\Scripts\python.exe .local/biz-001/verify_baseline.py` đạt (5 source hash khớp, 29 link/27 bảng trước sửa, 10 Decimal synthetic checks, 0 cell kế toán thực tế; application/business acceptance tests not run); kiểm tra Markdown link/table/fence/nội dung A–M riêng đạt; `git diff --check` đạt trước finish; Odoo/PostgreSQL status đang listening. Không chạy app tests vì không đổi code/runtime.
- Giới hạn: đây là baseline thiết kế để chủ nghiệp vụ review, chưa là quy chế/UAT/Odoo test. Q1–Q14, 2–3 hồ sơ khử dữ liệu và owner xác nhận còn chờ; CTR-001 read giữ nguyên, CTR-002/PRJ/ALC/STL/FIN/IMP chỉ mở sau người dùng chọn chuyển giai đoạn.
- Next: review BIZ-002 walkthrough A–M, chốt câu hỏi theo slice và hồ sơ đại diện; sau đó người dùng quyết định phạm vi code. Giữ Q2: chỉ superuser cấp grant cho đến khi người cấp/thu hồi và record/verify BASE được xác nhận.

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
