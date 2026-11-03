# TANPHAT ONE — DP-001 Data Platform discovery

**Phiên bản:** DP-DISC-v1.1 — 29/10/2026. **Change:** `CHG-20261029-026` (correction của DP-DISC-v1, `CHG-20261029-023`). **Task:** DP-001, làn tài liệu/spec-only theo [prompt DP-001](../prompts/CLAUDE_DATA_PLATFORM_DISCOVERY.md), [prompt correction](../prompts/CLAUDE_DP001_CORRECTION.md) và [kế hoạch chuẩn bị](TP_DATA_PLATFORM_PREPARATION_PLAN.md).

| Phiên bản | Change | Nội dung | Kết luận review |
| --- | --- | --- | --- |
| DP-DISC-v1 | `CHG-20261029-023` | Bản discovery đầu tiên | [Audit CHG-024](TP_DATA_PLATFORM_DP001_AUDIT.md): `DEFER` có cơ sở; `DESIGN_COMPLETE=NEEDS_FIX` vì DP-F01…DP-F04 |
| DP-DISC-v1.1 | `CHG-20261029-026` | Sửa DP-F01…DP-F04 và giải trình bằng chứng snapshot ([mục 0.1](#01-correction-sau-audit-chg-024), [mục 0.2](#02-giải-trình-bằng-chứng-snapshot)) | Tự đánh giá `PROPOSED_COMPLETE`; **chờ phiên chính audit lại**. Verdict CHG-024 giữ nguyên làm bằng chứng của phiên chính |

**Trạng thái:** bản khảo sát và thiết kế để phiên điều phối audit. Không phải quyết định công nghệ, không phải DEC, không mở PoC/pilot và không có Data Lake/analytics store nào được triển khai. Odoo vẫn là nguồn sự thật cho giao dịch, trạng thái, quyền và công thức; BASE là nguồn quyết định phê duyệt chính thức; posting/payment/reconciliation thuộc nguồn kế toán được xác nhận.

**Tóm tắt:** recommendation đề xuất là **`DEFER`**. Nhu cầu duy nhất có dữ liệu runtime hôm nay là hợp đồng trong một project. Use case đề xuất, UC-01, đáp ứng được bằng báo cáo có kiểm quyền ngay trong Odoo/API mà không cần sao chép dữ liệu. Vì vậy PoC lake là `NOT_APPLICABLE`. Sau correction v1.1, cổng `DESIGN_COMPLETE` được tự đánh giá `PROPOSED_COMPLETE` và chờ audit lại. `READY_FOR_SYNTHETIC_POC` không áp dụng cho lake. `REAL_DATA_APPROVAL` bị `BLOCKED` ([mục 9](#9-recommendation-và-cổng)).

## 0. Cách đọc, phạm vi và baseline

| Nhãn | Nghĩa trong tài liệu này |
| --- | --- |
| `observed-static` | Đọc trực tiếp từ source/tài liệu trong repository ở baseline dưới đây; không chứng minh module đã cài hay luồng đã chạy. So sánh hash file ở mục 0.2 cũng là quan sát tĩnh nội dung file |
| `runtime-evidence` | Có log/kết quả chạy đã được kiểm trong lượt này. **Không dòng nào dùng nhãn này**: DP-001 không khởi động Odoo/PostgreSQL. Kết quả test lịch sử ở `PROJECT_STATUS` chỉ được trích là lịch sử |
| `proposed` | Đề xuất thiết kế của DP-001, chưa được người dùng/chủ nghiệp vụ xác nhận |
| `unknown` | Thiếu căn cứ; ghi người/vai trò cần cung cấp và tác động, không tự đặt mặc định |

Baseline v1 đã kiểm trước khi sửa (CHG-023, giữ làm lịch sử):

- `main` tại HEAD `95bfc3f4`. Working tree đã có thay đổi chưa commit của CHG-016…022 từ các lượt trước: 17 file sửa và 6 đường dẫn chưa tracked. Đây là thay đổi có sẵn, không do DP-001 tạo.
- `ai_workflow.py check` báo `PASS` cho handoff `CHG-20261029-022`. Không có checkpoint đang dở. Checkpoint DP-001 được `start` trước khi viết tài liệu.
- Snapshot SHA-256 thô của 119 file theo `git ls-files -co --exclude-standard` trên `custom_addons`, `frontend/src`, `frontend/tests`, `contracts` và `scripts` được lưu ngoài Git trước khi sửa. Tập này **không** phải phạm vi exact của checker; giải trình ở [mục 0.2](#02-giải-trình-bằng-chứng-snapshot).
- Không kết nối database, không đọc NAS/Excel/filestore thật, không start/upgrade/seed Odoo, không chạy application tests.

Baseline v1.1 (CHG-026): HEAD `95bfc3f4`; `ai_workflow.py check` `PASS` cho `CHG-20261029-025`; không có checkpoint dở. Working tree giữ nguyên thay đổi chưa commit của CHG-016…025, không reset/clean/stash. Checkpoint correction được `start` trước lần sửa đầu.

Đối chiếu [kế hoạch chuẩn bị](TP_DATA_PLATFORM_PREPARATION_PLAN.md): không phát hiện gap buộc sửa kế hoạch. Kế hoạch đã yêu cầu tách snapshot nhất quán, pagination ổn định và retry/replay không trùng; correction v1.1 chỉ làm rõ cách đáp ứng các yêu cầu đó, nên kế hoạch không đổi.

### 0.1 Correction sau audit CHG-024

Mỗi finding được tái kiểm bằng source, không chỉ sửa câu chữ. Mọi ca kiểm chứng mới đều chỉ là đặc tả trên dữ liệu giả và `NOT_RUN`.

| Finding | Tái kiểm | Mục đã sửa | Ca kiểm chứng expected | Trạng thái |
| --- | --- | --- | --- | --- |
| DP-F01 — keyset không bảo đảm point-in-time snapshot | `_page_params` và `search(... offset ...)` trong `contracts.py`/`projects.py`: mỗi request là một transaction riêng; không có snapshot token | [4.4.1](#441-phân-trang-khác-tính-nhất-quán), envelope 4.1, R05, tiền đề 9.1, nguyên tắc 5.1 | V19, V21, V22, V23 | NOT_RUN |
| DP-F02 — cùng version khác hash | DC-02 cũ chỉ nhận version cao hơn; lifecycle/reference/document đổi ngoài workflow không tăng `aggregate_version` | [4.4.2](#442-ma-trận-version--hash), DC-02, 4.7, R19 | V14, V24, V25, V26, V30, V31 | NOT_RUN |
| DP-F03 — `tax_basis=unknown` | `_amount_summary` (`tp_contract_revision.py` dòng 130–160) chỉ trả `mixed_basis` khi có nhiều basis; `TAX_BASES` (`tp_contract_line.py` dòng 4–8) coi `unknown` là giá trị hợp lệ; `_tp_submission_problems` chỉ chặn `incomplete`/`mixed_basis`; test `test_contract_workflow.py` dòng 144–153 cho tổng 120 khi mọi dòng `unknown` | F06, 3.2, [3.3](#33-uc-01-đề-xuất--giá-trị-hợp-đồng-áp-dụng-theo-project), 4.3, DC-06, 4.7, R08 | V02, V03, V04, V17, V27, V28, V29 | NOT_RUN |
| DP-F04 — dedupe toàn cục mất A→B→A | Khóa `(source_env, entity, source_id, content_sha256)` cũ dùng chung cho payload, observation và output | [4.5.1](#451-retry-observation-và-payload), envelope 4.1, DC-06, 4.7, R20 | V12, V15, V32, V33, V34 | NOT_RUN |

### 0.2 Giải trình bằng chứng snapshot

| Bằng chứng | Phạm vi | Kết quả | Giới hạn | Trạng thái |
| --- | --- | --- | --- | --- |
| Artifact DP-001 (CHG-023), ngoài Git trong scratchpad của phiên Claude | 119 file, SHA-256 thô theo `git ls-files -co --exclude-standard custom_addons frontend/src frontend/tests contracts scripts` | Trước correction: 119/119 file vẫn trùng byte với lúc bắt đầu DP-001 | Không phải phạm vi `scripts.ai_workflow.snapshot`: có thêm `contracts/README.md`, `custom_addons/README.md`; thiếu 10 file checker theo dõi | observed-static |
| Đối chiếu artifact 119 với scope checker 127 | Giao nhau 117 file | 103 file có hash thô bằng hash checker; 14 file khác hash chỉ vì checker chuẩn hóa CRLF/BOM, còn byte thô không đổi. Vậy 117/117 file giao nhau không đổi từ đầu DP-001 | Chỉ chứng minh cho 117 file giao nhau | observed-static |
| 10 file chỉ có trong scope checker | `frontend/index.html`, `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `playwright.config.ts`, `ops/config/odoo-dev.conf.example`, `ops/requirements-tools.txt`, `ops/requirements-windows-py312.lock.txt`, `ops/runtime-baseline.json` | Không có hash trước DP-001 trong artifact. `check` lúc bắt đầu DP-001 báo PASS cho CHG-022, nhưng digest CHG-022 không còn được lưu nên không đối chiếu lại được | **Không tái chứng minh được** toàn bộ scope 127 trước DP-001. Không dựng bằng chứng hồi tố. Đây là khoảng trống bằng chứng, không phải bằng chứng code đã đổi | unknown |
| Snapshot trước audit (CHG-024, phiên chính) | `scripts.ai_workflow.snapshot`, 127 file | Digest `056ae25b…c392ca`, không đổi qua audit | Bằng chứng của phiên chính | observed-static (phiên chính) |
| Snapshot trước correction (CHG-026) | `scripts.ai_workflow.snapshot`, 127 file, lưu `.local/dp001-correction/before.json` | Digest `056ae25b…c392ca`, khớp state CHG-025 | Đối chiếu sau correction ghi ở CHANGELOG CHG-026 | observed-static |

Checker không hash tự động tài liệu architecture/prompt mới. Kiểm cấu trúc tài liệu của từng batch phải liệt kê đúng file mới hoặc bị ảnh hưởng.

## 1. Source inventory hiện có (DP-01)

### 1.1 Model và dataset

Owner ở các bảng dưới là **vai trò đề xuất** theo [ma trận capability](TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md#61-capability-theo-vai-trò). Chưa có người được công ty chỉ định. Volume và freshness đều `unknown`: dev seed chỉ có ba hợp đồng giả lập, không phản ánh quy mô thật. Cách đo đúng là chủ nghiệp vụ cung cấp số ước lượng, hoặc đếm trên môi trường được phép; không đọc database thật trong batch này.

| ID | Source/model/API | Source-of-truth | Đã có/dự kiến | Grain / key / scope | Owner vai trò (đề xuất) | Sensitivity | Volume/freshness | Update/delete/correction | Evidence | Gap | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | `res.company` | Odoo core | Đã có | 1 company / `id` / gốc mọi scope | Platform Manager | Internal | unknown | Core Odoo; archive thay xóa | Rule `company_id in company_ids` trong các `ir.access.csv` của `tp_*` | Chưa biết có dùng nhiều company không | observed-static |
| E02 | `res.users` + group `tp_core.group_user/group_manager` | Odoo identity | Đã có | 1 user / `id` (login là dữ liệu cá nhân) / company | Platform/HR owner | Personal | unknown | Archive (`active`); group đổi không có lịch sử TP | `tp_core` security; `_tp_run` kiểm `tp_core.group_user` | Không có service account cho trích xuất; không có lịch sử membership | observed-static |
| E03 | `hr.department` + `tp_code` | Odoo (`tp_organization`, phụ thuộc `hr`) | Đã có | 1 phòng / unique `(company, tp_code)` / company | HR owner | Internal | unknown | Ghi đè tại chỗ, không version | `tp_organization/models/hr_department.py` | Đổi tên/gộp phòng không có lịch sử, nên báo cáo theo phòng tại thời điểm cũ không tái dựng được | observed-static |
| E04 | `project.project` + `tp_managed`, `tp_code`, `tp_department_id` | Odoo | Đã có | 1 project / unique `(company, tp_code)` + `id` / company | Project owner/KD | Internal | unknown | Ghi đè tại chỗ; chỉ `tp_core.group_manager` cấu hình managed; contract `ondelete=restrict` | `tp_project/models/project_project.py` | Chưa có lifecycle state (PRJ-002, Q9); đổi phòng chủ trì không đổi scope hợp đồng đã có | observed-static |
| E05 | `tp.project.assignment` | Odoo | Đã có | `(project, user, role)` unique / company | Project owner (Q2) | Internal + Personal | unknown | `active=False` thu hồi; không ledger; `ondelete=cascade` theo project | `tp_project/models/tp_project_assignment.py`; test `test_revoked_assignment_removes_access` | Không tái dựng được ai có scope tại thời điểm T | observed-static |
| E06 | `tp.project.grant` (`financial_read`, `financial_draft_edit`, `contract_draft_edit`, `contract_submit`, `contract_review_commercial`) | Odoo, nguồn quyết định quyền runtime | Đã có | 1 grant active / unique `(project, user, capability)` active / project, có thêm department cho 4 capability workflow | ACCESS-DEC/ACCESS-OPS (Q2) | Confidential (dữ liệu quyền) | unknown | `active`/`date_end`; invalidate cache theo request; superuser `unlink` được, nên không có ledger | `tp_project/models/tp_project_grant.py`; test revoke/expired | Thiếu `date_start`, `revoked_by/at/reason`; không sao chép làm nguồn quyền thứ hai | observed-static |
| E07 | `tp.work.item` | Odoo | Đã có | 1 hạng mục / unique `(company, code)` | Chủ catalog (Q5) | Internal | unknown | Archive (`active`) | `tp_core/models/tp_work_item.py` | Mapping catalog thật chưa có (Q5) | observed-static |
| E08 | `tp.contract` | Odoo | Đã có | 1 hợp đồng / unique `(company, code)` viết hoa + `id` / company/project/department | KD-OWNER | Internal; counterparty Confidential | unknown | Chỉ ghi qua workflow service (ORM ngoài workflow bị chặn); `aggregate_version` tăng mỗi action sau create; không group nào unlink | `tp_contract.py`; test `test_n04_orm_writes_outside_the_workflow_are_blocked`, `test_no_group_can_write_contract_data` | `lifecycle_state`/`legacy_unverified` đổi ngoài workflow (setup) không tăng version | observed-static |
| E09 | `tp.contract.revision` | Odoo; ký/hiệu lực cần evidence pháp lý | Đã có | 1 revision / unique `(contract, sequence)` / như contract | KD-OWNER; legal (Q1) | Internal + Legal | unknown | Draft sửa qua workflow; chỉ draft chưa ký, chưa submit mới xóa được (xóa vật lý); correction là revision mới `revision_kind=correction` | `_unlink_only_drafts`; `_effective_revision` | Signed/effective chưa có action workflow, hiện chỉ setup/seed ghi | observed-static |
| E10 | `tp.contract.line` | Odoo | Đã có | 1 dòng phạm vi / unique `(revision, scope_key)` | KD-OWNER | Internal | unknown | `edit_draft` thay cả tập dòng: dòng không còn trong payload bị **xóa vật lý**; khóa sau submit | `_tp_apply_lines`; `_unlink_except_submitted` | Không tombstone; audit `edit_draft` không có diff | observed-static |
| E11 | `tp.contract.line.amount` | Odoo | Đã có | 1 amount / unique `line_id` / project + `financial_read` | KD-OWNER + Finance | Financial | unknown | Draft qua workflow + `financial_draft_edit`; gửi `amount=null` thì **xóa record**; constraint chưa xác nhận thì rỗng, không âm | `_tp_set_amount`; `tp_contract_line.py` | Lưu `Monetary` dạng float; chỉ API decimal string là đại diện an toàn | observed-static |
| E12 | `tp.approval.reference` | BASE giữ quyết định; Odoo giữ bản ghi tham chiếu/evidence | Đã có | 1 reference / chuỗi `previous_reference_id` / project | Người ghi BASE (Q2/Q3) | Legal; tên người quyết định là Personal | unknown | Chưa có API ghi; chỉ setup/seed | `tp_approval_reference.py`; `_approval_dto` | DTO trả provenance/decision_reason/authority_source/decided_by_name/hash cho metadata reader | observed-static |
| E13 | `tp.approval.reference.amount` | BASE (số được duyệt) ghi nhận ở Odoo | Đã có | 1 amount / unique `reference_id` | Finance | Financial | unknown | Như E12 | test `test_metadata_on_a_and_financial_on_b_only` | Chưa có quy tắc đối chiếu với BASE thật (Q3) | observed-static |
| E14 | `tp.contract.document` + `ir.attachment` (binary trong filestore) | Odoo filestore cho bản đã tải lên; bản gốc NAS `unknown` | Đã có | 1 tài liệu / `id`; checksum attachment / project + confidentiality | Document steward (Q11) | `financial` mặc định cho bản ký/phụ lục/evidence BASE; `general` cho phạm vi kỹ thuật | unknown | Xóa vật lý được trước submit; sau submit khóa cả file | `tp_contract_document.py`; `ir_attachment.py` | Tên file có thể chứa thông tin nhạy cảm; chưa có retention/legal hold | observed-static |
| E15 | `tp.contract.submission` + `.amount` | Odoo | Đã có (test-only, DEC-020) | 1 vòng gửi / unique `(revision, sequence)` | KD-OWNER/reviewer | Metadata Internal; snapshot tiền Financial | unknown | Bất biến, không unlink; metadata JSON + SHA-256; snapshot tiền tách riêng có salt + SHA-256 | `tp_contract_submission.py`; `_tp_snapshot`, `_tp_submit_review` | Nguồn lịch sử "đã biết tại thời điểm gửi" duy nhất; dev DB chưa upgrade | observed-static |
| E16 | `tp.contract.audit` | Odoo, lịch sử workflow | Đã có (test-only) | 1 event / unique `event_id` (UUID) / project | Audit/security | Internal; `reason` là text tự do có thể chứa tiền | unknown | Append-only; mọi action workflow; `version_before/after` | `_tp_audit`; `tp_contract_audit.py` | Không bao phủ thay đổi ngoài workflow; không có field diff | observed-static |
| E17 | `tp.contract.outbox` | Odoo, hàng đợi thông báo | Đã có (test-only) | 1 dòng mỗi event × recipient / unique `(event_id, recipient)` | Platform | Internal | unknown | `pending` → `delivered`; không xóa; `_tp_send` no-op; không cron | `_tp_notify`; test `test_n08_delivery_failure_keeps_the_event_and_dedupes` | Không phải change feed ([mục 6.4](#64-outbox-và-audit-hiện-có-có-dùng-làm-change-feed-được-không)) | observed-static |
| E18 | `tp.contract.idempotency` | Odoo, kỹ thuật | Đã có (test-only) | `(user, action, key)` unique | Platform | Restricted technical | unknown | Không có hạn lưu | ACL chỉ `base.group_system` | Không phải nguồn phân tích; loại khỏi mọi dataset | observed-static |
| E19 | `res.partner` (counterparty) | Odoo core | Đã có | 1 đối tác / `id` / company | KD-OWNER | Confidential/Personal | unknown | Core Odoo | `_tp_partner` kiểm company | Đối tác cá nhân là dữ liệu cá nhân, cần tối thiểu hóa | observed-static |
| E20 | `res.currency` | Odoo core | Đã có | 1 tiền tệ / ISO code | Finance | Internal | unknown | Core | `_tp_currency`; `decimal_places` dùng khi format | Không có rate source/policy quy đổi (Q4) | observed-static |

### 1.2 API/DTO và khả năng trích xuất

| Endpoint | Grain trả về | Phân trang/lọc | Tiền và quyền | Trường thời gian/version | Phù hợp để trích xuất? | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /api/v1/me` | user hiện tại | Không | Không tiền | Không | Không phải dataset | OpenAPI `tanphat-v1.yaml` | observed-static |
| `GET /api/v1/projects`, `/projects/{id}` | project managed trong scope | `limit` 1–100, `offset` 0–10000, `q`; order `tp_code, id`; `has_more` | Không tiền | Không có `updated_since` | Chỉ đủ cho số project nhỏ; offset tối đa 10.000 | `tp_planning_api/controllers/projects.py` | observed-static |
| `GET /api/v1/contracts` | contract summary + trạng thái revision mới nhất | Như trên, thêm `project_id`; order `code, id` | Không tiền ở list | `updated_at` = `write_date` của contract | Danh sách ID; không có cursor/watermark đáng tin | `contracts.py` `_contract_summary` | observed-static |
| `GET /api/v1/contracts/{id}?as_of=` | 1 contract + revisions + documents + `effective_snapshot` | Không | `total` chỉ có khi `tp_financial_read_granted` | `version`, `as_of`, `known_at` = **thời điểm request**, `basis=recorded_effectivity`, `warnings` | Đủ cho UC-01 từng hợp đồng; N+1 nếu cần nhiều hợp đồng | `_contract_detail` | observed-static |
| `GET /api/v1/contracts/{id}/revisions/{rid}` | revision + lines + submissions (metadata) | Không | `amount` từng dòng và `total` chỉ khi có grant | `contract_version`, `recorded_at`, `submitted_at` | Có thể dựng snapshot dòng; submission không trả tiền | `_revision_detail`, `_submission_dto` | observed-static |
| `GET .../documents/{did}/content` | binary | Không | File `financial` cần grant; `Cache-Control: no-store` | Không | Không nên sao chép file trước khi có policy Q11 | `contracts.py` route content | observed-static |
| POST/PATCH workflow routes | command | Không | Ghi qua CSRF + same-origin + `Idempotency-Key` | `expected_version` | **Không dùng** trong mọi phương án dữ liệu: no-writeback | `_run_workflow` | observed-static |

Mọi response API đều có `Cache-Control: no-store` và `meta.request_id` (`tp_api/services/response.py`). Xác thực là session người dùng (`auth='user'`). Không có token cho service, không có endpoint export hàng loạt, không có `updated_since`/cursor và không có tombstone.

### 1.3 Phát hiện chính ảnh hưởng thiết kế dữ liệu

| ID | Phát hiện | Hệ quả | Evidence | Trạng thái |
| --- | --- | --- | --- | --- |
| F01 | Chỉ domain Contracts và scope project có dữ liệu runtime. CTR-002a chỉ chạy trên test; dev DB chưa upgrade | Chưa thể làm báo cáo liên nguồn; mọi PoC phải dùng DB giả tách biệt | `PROJECT_STATUS` (blocker CTR-002a); DEC-020 | observed-static |
| F02 | Không có bulk export/change feed; offset pagination tối đa 10.000 và không nhất quán snapshot khi có ghi đồng thời | Trích xuất bằng API chỉ phù hợp quy mô nhỏ và tối đa `best_effort`; phát hiện drift không chứng minh snapshot nhất quán ([mục 4.4.1](#441-phân-trang-khác-tính-nhất-quán)) | `_page_params`; order `code, id` | observed-static |
| F03 | Draft xóa vật lý dòng, amount, revision nháp và tài liệu chưa gửi; audit `edit_draft` chỉ ghi version, không ghi diff | Đồng bộ tăng dần không biết bản ghi nào biến mất; phải snapshot đầy đủ theo hợp đồng | `_tp_apply_lines`, `_tp_set_amount`, `_unlink_only_drafts` | observed-static |
| F04 | Submission là snapshot bất biến có hash | Nguồn "đã biết tại thời điểm gửi" tốt cho bản đã gửi; không bao phủ ký/hiệu lực | `_tp_submit_review` | observed-static |
| F05 | Outbox chỉ có ở submit/resubmit/return và chỉ chứa tham chiếu | Không dùng làm change feed | `_tp_notify` | observed-static |
| F06 | Tiền lưu `Monetary` (float); API trả decimal string đã round theo currency; chưa xác nhận thì `null`. Tổng nguồn là `null` khi revision rỗng, có dòng thiếu/chưa xác nhận amount, hoặc các dòng confirmed có từ hai basis trở lên. Mọi dòng confirmed cùng `tax_basis=unknown` vẫn cho `status=confirmed`, có `value`, `tax_basis=unknown`, và vẫn được submit | Dữ liệu dẫn xuất phải lấy decimal string/Decimal, không cộng float. Chặn tổng khi basis `unknown` chỉ có thể là policy báo cáo riêng ([mục 4.3](#43-quy-tắc-giá-trị)) | `_amount_money`, `_amount_summary`, `_tp_submission_problems`; test `test_contract_workflow.py` dòng 144–153 | observed-static |
| F07 | Quyền được tính ở mỗi request ORM, có invalidation; grant không có ledger thu hồi | Bản sao không tự biết revoke; quyền phải kiểm tại thời điểm query | `_invalidate_grant_access`; test `test_revoked_grant_hides_money_on_next_request` | observed-static |
| F08 | Metadata BASE và text tự do (lý do, fix summary, issue) không được quét số tiền | Sao chép metadata có thể nhân rộng rò rỉ | `PROJECT_STATUS` (sai lệch policy); data dictionary 6.2 | observed-static |
| F09 | `known_at` trong API là thời điểm request; chưa có lịch sử "đã biết tại Y" | Báo cáo hai mốc X/Y chỉ làm được với submission snapshot hoặc bản sao có lịch sử | `_contract_detail`; BIZ-002 3.1 | observed-static |

## 2. Nguồn tương lai

Không giả định connector hay module đã cài. "Có trong source" không có nghĩa đã cài/cấu hình.

| ID | Nguồn | Giữ gì (source-of-truth) | Hiện trạng | Kênh tích hợp khả dĩ | Sensitivity | Owner vai trò (đề xuất) | Gate | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FS01 | BASE | Quyết định/phê duyệt chính thức | Là hệ thống chính thức (DEC-013); TANPHAT ONE chỉ ghi reference thủ công | Reference + hash + verify; API/ID thật chưa biết | Legal + Financial | Chủ nguồn BASE | Q1–Q3 | [Integration mục 1](TP_BIZ002_INTEGRATION_AND_REPORTING.md#1-ranh-giới-nguồn-sự-thật) | observed (vai trò nghiệp vụ); connector `unknown` |
| FS02 | Kế toán Odoo (`account`, `analytic`, `l10n_vn`) | Posting, invoice, payment, reconciliation, tax | Addon có trong source checkout; chưa chứng minh cài/cấu hình; FIN-001 chưa triển khai | Link domain → move/payment; đối chiếu, không ledger song song | Financial | Kế toán/QT-TC | Q4, Q6 | Thư mục `addons/account` tồn tại; [source structure](TP_PLATFORM_SOURCE_STRUCTURE.md) | unknown |
| FS03 | Excel/legacy | Snapshot lịch sử, không phải runtime | Bản sao S01–S05 đã phân tích có hash (BIZ-001); cấm dùng làm database | Staging `tp_import` (IMP-001/C16): hash, mapping, quarantine, release ORM | Financial + Personal | Data steward | Q12 | [Database design mục 5](TP_DATABASE_DESIGN.md#5-excel-và-hồ-sơ) | observed (bản sao); pipeline `proposed` |
| FS04 | NAS | Binary gốc | Nguồn tham chiếu có registry hash; không adapter; browser không nhận UNC | Metadata/hash/version qua backend kiểm quyền | Mọi lớp | Document steward/IT | Q11, Q14 | Integration mục 2 | observed (nguồn); adapter `unknown` |
| FS05 | DMS / TP Documents | Metadata, version, share, archive tài liệu | Chưa triển khai; addon `documents` không có trong source checkout | Chưa xác định | Mọi lớp | Document owner | Q11 | `addons/documents` không tồn tại; data dictionary J | unknown |
| FS06 | TP Survey | Kế hoạch, dữ liệu, bàn giao khảo sát | Chưa có model (luồng F) | Chưa xác định | Internal/Restricted IP | Survey lead/KCS | Q10 | Data dictionary F | proposed |
| FS07 | TP Design / bản vẽ / BIM | Hồ sơ thiết kế, revision, release | Chưa có model (luồng G); file lớn | Chưa xác định | Restricted/IP | Chủ trì thiết kế/KCS | Q10, Q11 | Data dictionary G | proposed |
| FS08 | HR | Nhân sự, nghỉ việc, ủy quyền | Chỉ dùng `hr.department`; chưa có model nhân sự TP | Chưa xác định | Personal | HR owner | Q2, Q11 | Manifest `tp_organization` phụ thuộc `hr` | proposed |
| FS09 | TP Tasks (`project.task`) | Giao việc, tiến độ | Module `project` là dependency; workflow TP chưa triển khai | Chưa xác định | Internal | Planning/project owner | Q9 | Manifest `tp_project` | proposed |

## 3. Use case ứng viên (DP-02)

### 3.1 So sánh ba mục tiêu người dùng chưa chọn

| Mục tiêu | Câu hỏi điển hình | Nguồn cần | Nguồn có hôm nay | Rủi ro chính | Công cụ hiện có đủ chưa | Đánh giá |
| --- | --- | --- | --- | --- | --- | --- |
| Báo cáo liên nguồn | Hợp đồng ↔ nghiệm thu ↔ hóa đơn ↔ tiền theo project/kỳ | Contracts, settlement, accounting, BASE | Chỉ Contracts (một nguồn) | Nhân tiền khi join; sai basis/currency; revoke trễ | API có `as_of` từng hợp đồng; chưa có aggregate theo project | Phần liên nguồn bị chặn bởi Q4/Q6/Q8; phần một nguồn làm được trong Odoo |
| Hồ sơ/bản vẽ | Hồ sơ nào đã có/thiếu, bản nào đã gửi review, hash nào | TP Documents/DMS, NAS registry, Design | Tài liệu hợp đồng theo từng hợp đồng + checksum | Phân loại sai, tên file nhạy cảm, retention | Không có DMS/search liên hợp đồng | Là bài toán DMS/registry, không phải lake; chờ Q11 |
| AI tra cứu | Hỏi đáp tự nhiên trên hồ sơ được phép | Text đã trích, index, classification | Không có | Lộ dữ liệu qua index/answer; quyền lệch; không thu hồi được câu trả lời | Không có | Rủi ro cao nhất; chưa có tiền đề Q11/Q14 |

### 3.2 Catalogue

| ID | Actor/owner (vai trò đề xuất) | Câu hỏi/quyết định | Nguồn đã có / còn thiếu | Metric/công thức | Latency mục tiêu | Quyền | Giá trị/cost giả định | Acceptance | Trạng thái đề xuất | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-01 | Actor: KD_HEAD, FINANCE theo scope. KPI owner: chưa chỉ định (Q13) | Tại ngày nghiệp vụ X, trong các project tôi được cấp, giá trị hợp đồng đang áp dụng là bao nhiêu theo currency/tax basis, và hợp đồng nào chưa đủ căn cứ để tính? | Có: E08–E11, `_effective_revision`, `_amount_summary`. Thiếu: dữ liệu thật đã đối chiếu, policy VAT/currency (Q4), action ghi nhận hiệu lực | Xem [mục 3.3](#33-uc-01-đề-xuất--giá-trị-hợp-đồng-áp-dụng-theo-project) | Đọc trực tiếp tại request (độ trễ dữ liệu ≈ 0); ngưỡng hiển thị do Q13 | Metadata theo assignment; tiền chỉ project có `financial_read`; scope trước aggregate; không export | Giả định giảm tổng hợp thủ công, **chưa đo**. Cost: một read service trong Odoo, không thêm hạ tầng | Bộ V01–V11, V16, V17, V20, V22, V27–V29 ở [mục 7](#7-kế-hoạch-poc--kiểm-chứng-dữ-liệu-giả-dp-06); kết quả nguồn và kết quả policy kiểm riêng | `PROPOSED` (ưu tiên đề xuất, **chưa accepted**) | Integration 3.1 "Giá trị hợp đồng"; KPI "Contract exposure" |
| UC-02 | Document steward, KD-OWNER | Revision nào thiếu bản ký/phụ lục/evidence BASE; bản đã gửi review có khớp checksum không? | Có: E14, checksum attachment, `sha1` trong submission metadata. Thiếu: TP Documents, checklist hồ sơ bắt buộc, NAS registry, bản vẽ | `missing_required = required_kinds(revision) − present_kinds`; `hash_match = snapshot.sha1 == attachment.checksum` | Tại request | `general` theo project scope; `financial` cần grant; che tên file | Cost phụ thuộc thiết kế DMS (`unknown`) | Ca thiếu bản ký, ca hash lệch, ca file financial ẩn với metadata reader | `CANDIDATE`, chờ Q11 và TP Documents | Data dictionary 6.3, J |
| UC-03 | KD/PM; owner AI/data: chưa có | Hỏi đáp tự nhiên trên hợp đồng/hồ sơ được phép, có trích dẫn version/hash | Có: không. Thiếu: classification, policy index/retention, trích text/OCR (chưa được phép), kiểm quyền khi trả lời | Tỷ lệ câu trả lời có trích dẫn đúng trên bộ câu hỏi giả | Tại request | Kiểm quyền ở thời điểm truy vấn và trích dẫn; index tách theo classification | Cost `unknown`; rủi ro cao | Ca user A hỏi số tiền project B, kết quả phải từ chối | `DEFERRED` | Kế hoạch DP-02 |

Không dùng "dashboard toàn công ty" làm use case. UC-01 là KPI "Contract exposure" thu hẹp về một câu hỏi, một dataset và một công thức.

### 3.3 UC-01 đề xuất — giá trị hợp đồng áp dụng theo project

Công thức dùng Decimal và precision currency của Odoo. Hai lớp kết quả được tách riêng:

```text
Lớp nguồn (observed-static; tái dùng logic Odoo hiện có, không sửa):
Với mỗi contract c mà user đọc được và mỗi ngày nghiệp vụ X:
  (rev, warnings) = tp.contract._effective_revision(c, X)
  nếu không có rev:
    source_status(c) ∈ {no_effective_revision, effective_date_conflict}   # lấy từ warnings
    source_value(c) = null                                                # API trả total = null
  ngược lại (source_value, source_status, source_basis) = rev._amount_summary():
    source_status ∈ {confirmed, incomplete, mixed_basis, empty}
    source_value  = Σ amount các dòng, chỉ khi source_status = confirmed; ngược lại null
    source_basis  = basis chung của các dòng confirmed (có thể là unknown)
                    | mixed khi có từ hai basis | unknown khi chưa có dòng confirmed

Lớp policy báo cáo (proposed; gate Q4/Q13; chưa phải policy công ty):
  report_status(c) = basis_unknown  nếu source_status = confirmed và source_basis = unknown
                   = source_status   trong mọi trường hợp khác
  policy_value(c)  = source_value nếu report_status = confirmed; ngược lại null

Với mỗi project p có financial_read của user, mỗi currency k, mỗi basis đã biết b:
  confirmed_subtotal(p,k,b) = Σ policy_value(c) với c ∈ p, report_status = confirmed,
                              currency = k, source_basis = b
  project_total(p,k,b)      = confirmed_subtotal nếu mọi c ∈ p có report_status = confirmed,
                              ngược lại null
  kèm số lượng và danh sách c bị loại theo report_status; basis_unknown được liệt kê riêng
Với project chỉ có metadata: chỉ trả số lượng contract theo report_status,
không trả value/subtotal/total.
```

- **Lớp nguồn** phản ánh đúng Odoo: một hợp đồng có mọi dòng confirmed cùng basis `unknown` có `source_status=confirmed` và `source_value` khác null. Lớp nguồn được reconcile với `effective_snapshot.total` của API.
- **Lớp policy** chỉ là đề xuất. Q4 (VAT/gross-net) và Q13 (KPI owner) quyết định có đưa hợp đồng basis `unknown` vào tổng chính thức, tách bucket riêng hay chỉ liệt kê. Trước khi có quyết định, `basis_unknown` được hiển thị riêng, có nhãn, không trộn vào tổng chính thức. Policy được kiểm bằng expected riêng, không bắt cùng một field vừa bằng API vừa `null`.
- Phụ lục thay toàn bộ snapshot: 100 → 110 cho kết quả 110, không cộng 210.
- `future_revision_recorded` là cảnh báo, không đổi bản áp dụng.
- Trùng ngày hiệu lực trả conflict, không tự chọn ID lớn nhất.
- `confirmed_subtotal` luôn gắn nhãn "một phần" khi còn hợp đồng bị loại. Không được trình bày như tổng chính thức. Q13 phải chốt có hiển thị subtotal hay không.
- Header báo cáo gồm `as_of_business`, `known_at` (thời điểm query), `company`, `project_scope`, `currency`, `tax_basis`, `data_freshness` ("live Odoo") và `dataset_status` (trạng thái nạp của từng nguồn, ví dụ `missing_source`; khác `source_status` cấp hợp đồng).
- Missing/disputed: không có amount record hoặc chưa xác nhận thì `null`/`incomplete`. Reference BASE `disputed` không làm hợp đồng "đã duyệt". Nguồn kế toán vắng không ảnh hưởng UC-01 vì UC-01 không đọc kế toán.

### 3.4 Báo cáo/search/DMS hiện có có đủ không?

| Năng lực hiện có | UC-01 | UC-02 | UC-03 | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| `GET /contracts/{id}?as_of=` + `_amount_summary` | Đủ cho từng hợp đồng; thiếu aggregate theo project | Không | Không | `_contract_detail` | observed-static |
| ORM `read_group` có ACL amount | Có thể làm aggregate đúng scope trong Odoo; test chứng minh metadata A/tiền B không lộ | Không | Không | `test_metadata_on_a_and_financial_on_b_only` | observed-static |
| Tìm kiếm `q` trên list | Chỉ code/name trong scope | Không tìm tài liệu | Không | `contracts()` | observed-static |
| DMS/TP Documents | Không | Chưa có | Chưa có | FS05 | observed-static (vắng) |

Kết luận: với UC-01, một read service có kiểm quyền trong Odoo (C17/RPT-001, `tp_reporting` đã lên kế hoạch) là đủ. Không cần sao chép dữ liệu ra store khác. UC-02 cần DMS/registry. UC-03 chưa có tiền đề.

## 4. Data contract (DP-03)

Các contract dưới đây là chuẩn đề xuất cho **mọi** đường dữ liệu dẫn xuất trong tương lai: read service Odoo, analytics-first hoặc lakehouse-lite. Với `DEFER`, phần O0 chỉ cần header/kiểu giá trị/join rules. Phần envelope/batch/tombstone chỉ dùng khi một phương án sao chép được mở.

### 4.1 Envelope chung

| Field | Kiểu | Bắt buộc | Ý nghĩa | Nguồn hiện có | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| `source_system` | enum (`odoo`, sau này `base`, `accounting`, `excel`…) | Có | Hệ thống nguồn | — | proposed |
| `source_env` | enum (`test`, `dev`, `staging`, `prod`) | Có | Môi trường; PoC chỉ `test` giả | — | proposed |
| `entity` | string (tên model) | Có | Ví dụ `tp.contract.revision` | Odoo `_name` | proposed |
| `source_id` | integer | Có | Odoo ID; không dùng tên hiển thị làm khóa | Odoo `id` | observed-static |
| `business_key` | string có cấu trúc | Có | Ví dụ `company_id/code`, `contract_id/sequence`, `revision_id/scope_key` | Unique constraint mục 1.1 | observed-static |
| `extract_batch_id` | UUID | Có | Mỗi lần trích xuất; retry trong cùng batch giữ nguyên giá trị | — | proposed |
| `attempt_no` | integer | Có | Lần thử trong batch; chỉ để vận hành, không thuộc khóa observation ([mục 4.5.1](#451-retry-observation-và-payload)) | — | proposed |
| `snapshot_id` | UUID | Có | Nhóm bản ghi đọc cho cùng một lần chụp. Chỉ được coi là nhất quán khi `snapshot_consistency=consistent_proven` | — | proposed |
| `snapshot_consistency` | enum (`consistent_proven`, `best_effort`, `inconsistent`) | Có | Mức nhất quán đã chứng minh của batch ([mục 4.4.1](#441-phân-trang-khác-tính-nhất-quán)); API hiện tại tối đa chỉ `best_effort` | — | proposed |
| `source_snapshot_token` | string, nullable | Theo cơ chế | Token do nguồn cấp cho export đọc nhất quán; hiện **không có** nên luôn `null` | — | proposed (cần code) |
| `observation_id` | UUID | Có | Một lần quan sát bất biến của `(entity, source_id)` trong một `snapshot_id`; không dedupe giữa các snapshot | — | proposed |
| `schema_version` | semver | Có | Phiên bản data contract | — | proposed |
| `source_api_version` | string | Có | `v1` + SHA-256 của OpenAPI | `contracts/openapi/tanphat-v1.yaml` | proposed |
| `transform_version` | string | Có | Hash/commit của transform | — | proposed |
| `formula_version` | string, nullable | Với curated/metric | Phiên bản công thức/policy (ví dụ công thức 3.3 và policy `basis_unknown`) | — | proposed |
| `materialization_id` | UUID | Với curated/metric | Một lần dựng kết quả dẫn xuất từ `(snapshot_id, schema_version, transform_version, formula_version)` | — | proposed |
| `content_sha256` | hex | Có | Hash canonical JSON các field nghiệp vụ, không gồm envelope. Là khóa của payload content-addressed, **không** phải khóa observation | Mẫu `_canonical` + `_sha256` | proposed |
| `record_version` | integer, nullable | Theo entity | `aggregate_version` cho dữ liệu thuộc contract; `null` với entity không có version ở nguồn. Xử lý theo [ma trận 4.4.2](#442-ma-trận-version--hash) | `tp.contract.aggregate_version` | observed-static |
| `event_time` | datetime UTC, nullable | Theo entity | Thời điểm sự kiện nghiệp vụ, ví dụ `acted_at`, `submitted_at` | Audit/submission | observed-static |
| `known_at` | datetime UTC | Có | Thời điểm nguồn biết fact: `recorded_at`/`acted_at`; với snapshot hiện trạng là thời điểm đọc, kèm cảnh báo | Revision `recorded_at`; API `known_at` | observed-static + proposed |
| `ingested_at` | datetime UTC | Có | Thời điểm lớp dẫn xuất nhận; **không** dùng để quyết định bản mới hơn | — | proposed |
| `effective_from` / `effective_to` | date, nullable | Theo entity | Ngày nghiệp vụ, không đổi timezone | Revision `effective_date` | observed-static |
| `is_tombstone`, `tombstone_reason` | bool, enum | Có | Ghi nhận biến mất ở nguồn (`draft_deleted`, `out_of_scope`, `unexpected_missing`) | — | proposed |
| `company_id`, `project_id`, `department_id` | integer | Có (department nullable) | Scope cho kiểm quyền | Stored related fields | observed-static |
| `sensitivity` | enum | Có | `internal`, `personal`, `legal`, `financial`, `restricted_technical` | Data dictionary | proposed |

### 4.2 Contract theo dataset

| Dataset / grain / key | Field / type / nullable / decimal / currency | Scope | Version / time | Change / correction / delete / replay | Lineage | Quality / reconcile rules | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DC-01 `dim_project` / 1 project / `(company_id, tp_code)` + `source_id` | `tp_code` str not null; `name` str; `department_id` int null | company | Không version ở nguồn; giữ lịch sử bằng snapshot | Ghi đè tại chỗ; vắng trong full snapshot → tombstone `out_of_scope` hoặc `unexpected_missing` | `project.project` → `/projects` | Unique `(company, tp_code)`; chỉ `tp_managed` | E04 | proposed |
| DC-02 `dim_contract` / 1 contract / `(company_id, code)` + `source_id` | `code` str; `contract_type`, `lifecycle_state` enum; `currency` ISO not null; `partner_ref` tối thiểu hóa; `legacy_unverified`, `active` bool | company/project/department | `record_version` = `aggregate_version` | Mọi lần đọc được lưu thành observation. Cập nhật hiện trạng theo [ma trận version × hash 4.4.2](#442-ma-trận-version--hash): version cao hơn và hash khác thì nhận; cùng version nhưng hash khác thì đọc xác minh từ nguồn/snapshot có thẩm quyền, chưa xác minh được thì quarantine; không quyết theo `ingested_at`, `write_date` hoặc thứ tự response. Vắng mặt → `unexpected_missing` và quarantine, không xóa | `tp.contract` → `/contracts/{id}` | Unique code; enum lạ → quarantine; currency tồn tại | E08 | proposed |
| DC-03 `fact_contract_revision` / 1 revision / `(contract_id, sequence)` | `revision_kind`, `review_state`, `signature_status`, `effectivity_status` enum; `signed_date`, `effective_date` date null; `recorded_at` UTC null; `previous_revision_id` int null | như contract | `record_version` của contract; `known_at` = `recorded_at` hoặc thời điểm đọc | Draft biến mất → tombstone `draft_deleted`; non-draft biến mất → incident; correction là revision mới | `/contracts/{id}` revisions | `sequence` liên tục theo contract; previous cùng contract và nhỏ hơn | E09 | proposed |
| DC-04 `fact_contract_line` / 1 dòng / `(revision_id, scope_key)` | `name` str; `work_item_code` str null; `change_kind` enum; `previous_line_id` int null; **không tiền** | như contract | theo revision | Draft: snapshot cả tập dòng theo revision; dòng thiếu → tombstone | `/revisions/{rid}` lines | Unique `(revision, scope_key)`; provenance khớp revision trước | E10 | proposed |
| DC-05 `fact_contract_line_amount` (vùng financial) / 1 dòng / `line_id` | `amount_state` enum; `value` decimal string → NUMERIC scale = `currency.decimal_places`, null khi chưa xác nhận; `currency` ISO; `tax_basis` enum | project + `financial_read` | theo revision | Amount record biến mất → `null`/unconfirmed, không phải 0 | `/revisions/{rid}` `lines[].amount` | Không nạp từ float; không âm; confirmed bắt buộc có value; 1:1 với DC-04 | E11; F06 | proposed |
| DC-06 `fact_contract_effective_value` (curated UC-01) / contract × `as_of_business` × `materialization_id` | `revision_id` int null; lớp nguồn: `source_status`, `source_value` NUMERIC null, `source_basis`; lớp policy (proposed, Q4/Q13): `report_status`, `policy_value` NUMERIC null; `currency`; `warnings` list | như DC-05 cho value; metadata cho status/count | `as_of_business`, `known_at` của snapshot; khóa materialization gồm `snapshot_id`, `schema_version`, `transform_version`, `formula_version` | Tính lại hoàn toàn từ DC-03/04/05 cùng `snapshot_id`; không update tại chỗ. Đổi transform/formula tạo `materialization_id` mới, không tái dùng output cũ ([mục 4.5.1](#451-retry-observation-và-payload)) | DC-03/04/05 → công thức 3.3 | Lớp nguồn: `source_status`/`source_value`/`source_basis` bằng chuỗi với `effective_snapshot.total.status/value/tax_basis` của API cùng `as_of`. Lớp policy: so với expected riêng của fixture, không so với API | Integration 3.1; `_amount_summary` | proposed |
| DC-07 `fact_contract_workflow_event` / 1 event / `event_id` | `action` enum; `actor_ref` (pseudonym khi ra ngoài Odoo); `acted_at` UTC; `state_before/after`; `version_before/after` int; `submission_id`; `payload_sha256`; `reason` text Confidential | project | `event_time` = `acted_at`; thứ tự theo `version_after` trong contract | Append-only; dedupe theo `event_id`; không delete | `tp.contract.audit` (chưa có API đọc) | Chuỗi version liên tục; event không có contract → quarantine | E16 | proposed (cần API mới) |
| DC-08 `fact_submission_snapshot` / 1 submission / `(revision_id, sequence)` | `metadata_sha256`, `payload_sha256`; phần tiền ở vùng financial với `financial_sha256` có salt | metadata: project; tiền: + grant | `submitted_at`, `contract_version` | Bất biến; không delete | `/revisions/{rid}` submissions (hiện không trả tiền) | Hash khớp nguồn; salt không ra ngoài Odoo nên kiểm hash tiền chỉ làm được trong Odoo | E15 | proposed |

### 4.3 Quy tắc giá trị

| Trường hợp | Ở nguồn | Trong contract dữ liệu | Khi aggregate | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| Nguồn/dataset chưa nạp | — | `dataset_status=missing_source` | Không tính, hiển thị nhãn riêng | Integration 1 | proposed |
| Dòng không có amount record | Không record | `value=null`, `amount_state=unconfirmed`, `tax_basis=unknown` | Contract `incomplete` | `_amount_money` | observed-static |
| Chưa xác nhận | `amount_state=unconfirmed`, amount 0/rỗng | `value=null` | Contract `incomplete` | Constraint `_unconfirmed_is_empty` | observed-static |
| Đã xác nhận bằng 0 | `confirmed`, 0 | `"0.00"` (theo decimal_places) | Tính là 0 | test `test_c5_unconfirmed_amount_is_null_and_zero_is_zero` | observed-static |
| Số âm | Bị chặn ở snapshot dòng | Xuất hiện thì quarantine; điều chỉnh âm cần dataset typed riêng sau này | Không tự clamp | Constraint `_non_negative` | observed-static |
| Disputed | `verification_state=disputed` | Giữ nguyên trạng thái | Không coi là verified | `tp_approval_reference.py` | observed-static |
| Mọi dòng confirmed cùng basis `unknown` | `tax_basis=unknown` hợp lệ trong `TAX_BASES` | `source_status=confirmed`, `source_value` khác null, `source_basis=unknown` | Lớp nguồn: có tổng. Lớp policy: `report_status=basis_unknown`, `policy_value=null`, liệt kê riêng | `_amount_summary` dòng 145–158; `tp_contract_line.py` | nguồn: observed-static; policy: proposed (Q4/Q13) |
| Mọi dòng confirmed nhưng có từ hai basis trở lên (kể cả `unknown` + một basis đã biết) | — | `source_status=mixed_basis`, `source_value=null`, `source_basis=mixed` | Không cộng ở cả hai lớp | `_amount_summary`; `_tp_submission_problems` chặn submit (`tax_basis_mixed`) | observed-static |
| Mọi dòng confirmed cùng một basis đã biết | Ví dụ `excluding_tax` | `source_status=confirmed`, `source_value`, `source_basis` = basis đó | Cộng trong bucket `(currency, basis)` | `_amount_summary` | observed-static |
| Có dòng thiếu amount hoặc chưa xác nhận | — | `source_status=incomplete`, `source_value=null` (`incomplete` được ưu tiên hơn `mixed_basis`); `source_basis` không mang ý nghĩa báo cáo | Không cộng ở cả hai lớp | `_amount_summary`; submit bị chặn `amounts_not_confirmed` | observed-static |
| Revision không có dòng | — | `source_status=empty`, `source_value=null` | Không cộng; khác confirmed 0 | `_amount_summary`; submit bị chặn `no_lines` | observed-static |
| Nhiều currency | Currency theo contract | Bucket riêng theo ISO | Không quy đổi khi chưa có policy Q4 | Data dictionary 5.2 | observed-static + gate Q4 |
| Rounding | Odoo round theo currency | Không round lại trong transform; cộng bằng NUMERIC/Decimal | So sánh tổng bằng chuỗi chính xác | `float_repr(currency.round(...))` | observed-static |

### 4.4 Thời gian, version và tính nhất quán

- **Bốn mốc tách riêng:**
  - `event_time`: khi việc xảy ra.
  - `known_at`: khi nguồn ghi nhận.
  - `ingested_at`: khi lớp dẫn xuất nhận.
  - `effective_from/to`: ngày nghiệp vụ.

  Sửa record không reset ngày nghiệp vụ. Không dùng `ingested_at`, `write_date` hoặc thứ tự response làm bằng chứng bản mới hơn.
- **Thứ tự theo aggregate:** dữ liệu thuộc một contract có thứ tự tin cậy duy nhất là `aggregate_version`, và chỉ cho thay đổi đi qua workflow. Version nhảy cách quãng thì gắn `version_gap` và lấy lại toàn bộ contract. Các trường hợp còn lại theo [ma trận 4.4.2](#442-ma-trận-version--hash).
- **Thay đổi ngoài workflow:** setup/superuser có thể đổi lifecycle, legacy, reference hoặc document mà không tăng version. Vì vậy mỗi lần trích xuất phải so cả `record_version` và `content_sha256`.
- **Hai mốc báo cáo X/Y:** API hiện chỉ cho "áp dụng tại X, biết tại bây giờ". "Biết tại Y" trong quá khứ chỉ làm được với submission snapshot, hoặc với bản sao lưu lịch sử snapshot (R14).

#### 4.4.1 Phân trang khác tính nhất quán

**Phân trang** chỉ giải quyết việc lấy đủ và không trùng các khóa. **Tính nhất quán** đòi hỏi mọi bản ghi, quan hệ và quyền thuộc cùng một thời điểm đọc. Keyset cursor ổn định thứ tự theo khóa nhưng không giữ nội dung: giữa hai request, cùng ID vẫn có thể đổi amount, reference, revision/relation hoặc quyền. Vì vậy keyset **không** được coi là snapshot nhất quán.

Hiện trạng (observed-static): `_page_params` chỉ có `limit` 1–100 và `offset` 0–10000; mỗi request API là một transaction Odoo riêng; không có snapshot token xuyên trang; `known_at` của `effective_snapshot` là thời điểm từng request.

| Cơ chế | Cách làm | Mức nhất quán được phép gắn | Điều kiện | Trạng thái |
| --- | --- | --- | --- | --- |
| M1 — Đọc API hiện có | Liệt kê theo trang, đọc detail, ghi `version`/`contract_version`/`content_sha256`; đọc lại khi version lệch; liệt kê lại ID/version/hash cuối batch | Tối đa `best_effort`. Phát hiện drift thì `inconsistent`, không publish | Liệt kê lại chỉ phát hiện được một phần drift; không chứng minh mọi bản ghi cùng thời điểm | observed-static (API) + proposed (quy trình) |
| M2 — Export materialized phía server | Một request Odoo mở **một** transaction đọc nhất quán (PostgreSQL `REPEATABLE READ` hoặc snapshot tương đương), kiểm quyền bằng ORM của user, ghi toàn bộ kết quả vào một export bất biến có `source_snapshot_token`. Các trang sau chỉ đọc từ export đó | `consistent_proven` cho dữ liệu trong export | Token chỉ định danh export, **không mang quyền**; mỗi request đọc trang vẫn kiểm user/scope hiện hành của Odoo; export có TTL và bị vô hiệu nếu quyền đổi | proposed (cần code, R05) |
| M3 — Change log/watermark | Bootstrap bằng M2, sau đó đọc change log có thứ tự tin cậy, tombstone và cursor | Chỉ `consistent_proven` sau khi đặc tả và test đủ bootstrap, delete, ordering, handoff bootstrap→log và reconciliation | Outbox hiện có không phải change log ([mục 6.4](#64-outbox-và-audit-hiện-có-có-dùng-làm-change-feed-được-không)) | proposed (cần code) |

Quy tắc chung:

1. Không tự gắn `snapshot_consistency=consistent_proven` khi chưa có M2 hoặc M3 được chứng minh. API hiện tại chỉ cho `best_effort`.
2. Batch `best_effort` chỉ dùng cho kiểm chứng nội bộ có nhãn. Không publish như tổng nhất quán.
3. **Quyền đổi trong lúc đọc** (assignment/grant/expiry/active đổi giữa hai trang): fail closed. Không ghép các trang đọc dưới hai trạng thái quyền khác nhau. Batch bị đánh `inconsistent`, và phần tiền đọc trước khi bị thu hồi không được publish cho user đó.
4. Không thiết kế cơ chế nào đọc dữ liệu bằng `sudo` rồi tự lọc quyền bên ngoài Odoo. Scope luôn do Odoo kiểm tại thời điểm đọc và tại thời điểm query ([mục 5.1](#51-nguyên-tắc)).

#### 4.4.2 Ma trận version × hash

Mỗi lần đọc luôn được lưu thành observation bất biến ([mục 4.5.1](#451-retry-observation-và-payload)). Ma trận dưới đây chỉ quyết định **hiện trạng** (current state) có được cập nhật hay không. So sánh với hiện trạng đã nhận của cùng `(source_env, entity, source_id)`.

| Version quan sát mới so với hiện trạng | Hash giống | Hash khác |
| --- | --- | --- |
| Cao hơn | Ghi observation; cập nhật `record_version`, không đổi payload. Ghi cảnh báo nhẹ vì version tăng mà nội dung trong phạm vi hash không đổi | Nhận làm hiện trạng mới. Nếu nhảy nhiều hơn 1 thì `version_gap` và đọc lại toàn contract |
| Thấp hơn (response đến muộn) | Ghi observation; không đổi hiện trạng | Ghi observation làm lịch sử; **không** ghi đè hiện trạng |
| Bằng nhau | Ghi observation; không đổi hiện trạng, không tạo payload mới | Không tự chọn bản nào. Đọc xác minh từ nguồn có thẩm quyền: một lần đọc detail Odoo bắt đầu **sau khi** đã nhận cả hai observation, hoặc export M2 mới hơn. Kết quả xác minh trùng một trong hai hash → nhận bản đó làm hiện trạng. Ra hash thứ ba → dữ liệu còn đang đổi; đọc lại trong giới hạn số lần đã cấu hình. Không xác minh được hoặc vẫn không ổn định → quarantine `same_version_conflict`, hiện trạng giữ nguyên và có cảnh báo |

Trường hợp đặc biệt:

| Trường hợp | Quy tắc |
| --- | --- |
| Entity không có version ở nguồn (`record_version=null`, ví dụ `project.project`, document metadata, reference) | Không có thứ tự tin cậy giữa hai response. Hash khác nhau giữa hai observation trong cùng batch `best_effort` → đọc xác minh; không xác minh được thì quarantine. Giữa hai snapshot, chỉ snapshot mới hơn có thẩm quyền mới được thay hiện trạng |
| Thay đổi ngoài workflow (version không tăng, hash đổi) | Là ca "bằng nhau + hash khác". Không tự coi là lỗi nguồn, cũng không tự nhận. Nếu xác minh xác nhận thì nhận và ghi `out_of_workflow_change` để reconcile |
| Response đến muộn trong cùng batch | Thứ tự response, `ingested_at` và `write_date` không phải bằng chứng. Áp ma trận theo version; entity không version thì như dòng đầu bảng này |
| Snapshot có thẩm quyền mới | Một snapshot `consistent_proven` (M2) mới hơn snapshot đang làm hiện trạng được thay toàn bộ hiện trạng **trong phạm vi coverage của nó** (entity + scope đã đọc đủ), kể cả khi version không tăng. "Mới hơn" xác định theo thời điểm đọc nhất quán do nguồn ghi vào export, không theo `ingested_at`. Bản ghi ngoài coverage giữ nguyên. Mọi observation cũ được giữ lại |
| Batch `best_effort` mâu thuẫn với snapshot `consistent_proven` cùng thời điểm | Snapshot có thẩm quyền thắng; observation `best_effort` vẫn lưu, gắn cảnh báo |

Ma trận này là đặc tả cho lớp dẫn xuất tương lai, không đổi model Odoo.

### 4.5 Delete, tombstone, correction và replay

| Entity | Xóa vật lý ở nguồn? | Khi nào | Phát hiện ở lớp dẫn xuất | Xử lý đề xuất | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| Contract | Không group nào; superuser có thể | Setup/sự cố | Vắng trong list/detail | `unexpected_missing` → quarantine + incident, không xóa | `test_no_group_can_write_contract_data` | observed-static |
| Revision | Có | Draft chưa ký, chưa submit | Vắng trong revisions của contract | Tombstone `draft_deleted` nếu bản cuối là draft; ngược lại incident | `_unlink_only_drafts` | observed-static |
| Line / amount | Có | `edit_draft` bỏ dòng hoặc gửi `amount=null` | Vắng trong revision | Tombstone theo `(revision_id, scope_key)`; amount → `null` | `_tp_apply_lines`, `_tp_set_amount` | observed-static |
| Document | Có | Trước submit | Vắng trong documents | Tombstone metadata; không lưu file đã xóa | `_unlink_except_submitted` | observed-static |
| Submission, audit, outbox | Không | — | — | Append-only | `tp_contract_submission.py`, `tp_contract_audit.py` | observed-static |
| Grant/assignment | `active=False`; superuser có thể unlink grant | Thu hồi | Không sao chép làm nguồn quyền | Kiểm trực tiếp Odoo khi query ([mục 5](#5-security-và-retention-dp-04)) | E05, E06 | observed-static |

- **Correction:** correction/amendment tạo revision mới và giữ bản cũ. Lớp dẫn xuất không update lịch sử tại chỗ mà thêm phiên bản mới.
- **Replay:** tách thành ba lớp ở [mục 4.5.1](#451-retry-observation-và-payload). Không có khóa dedupe toàn cục theo `(source_env, entity, source_id, content_sha256)`.
- **Hạn chế khi trích lại:** trích lại từ Odoo chỉ cho hiện trạng, không cho quá khứ. Replay lịch sử chỉ có khi lưu extract bất biến (lakehouse-lite) hoặc lịch sử snapshot (analytics-first có SCD).

#### 4.5.1 Retry, observation và payload

| Lớp | Khóa | Hành vi | Mục đích |
| --- | --- | --- | --- |
| L1 — Retry trong batch | `(extract_batch_id, entity, source_id)` | Retry do lỗi mạng/timeout trong cùng batch thay lần thử **chưa hoàn tất** của chính batch đó; `attempt_no` chỉ để vận hành. Không tạo observation thứ hai. Nếu hai lần thử đều hoàn tất với hash khác nhau thì không lấy lần sau làm đúng; áp [ma trận 4.4.2](#442-ma-trận-version--hash) | Chạy lại cùng batch không nhân bản |
| L2 — Observation bất biến | `observation_id`, unique `(snapshot_id, entity, source_id)` | Mỗi snapshot có đúng một observation cho mỗi bản ghi đọc được, trỏ tới payload bằng `content_sha256`. Không dedupe giữa các snapshot; không update, không delete trừ theo retention đã duyệt | Giữ lịch sử known-at, kể cả A→B→A |
| L3 — Payload content-addressed | `content_sha256` (kèm `schema_version` canonical) | Payload giống nhau chỉ lưu một lần; observation sau trỏ tới payload đã có. Không copy binary/payload lần hai | Tiết kiệm lưu trữ mà không mất observation |

Ví dụ A→B→A qua ba snapshot S1, S2, S3: có **ba** observation (S1→A, S2→B, S3→A) và **hai** payload (A, B). Lần A thứ hai không bị bỏ vì hash đã gặp.

**Materialization dẫn xuất:**

- Khóa materialization = `(snapshot_id, schema_version, transform_version, formula_version)`; mỗi tổ hợp có một `materialization_id`.
- Chạy lại cùng khóa (cùng input, cùng transform/formula) trả cùng materialization; không nhân bản. Transform tất định nên kết quả phải giống từng byte theo canonical.
- Đổi `transform_version` hoặc `formula_version` (ví dụ v1 → v2) **bắt buộc** dựng materialization mới có lineage riêng, kể cả khi input y hệt. Không tái dùng output v1 cho v2. Bản v1 được giữ đến khi retention cho phép.
- Batch lỗi giữa chừng: các observation đã ghi được đánh dấu batch `failed`; không materialize, không publish. Dữ liệu quarantine không vào curated. Replay có kiểm soát = chạy lại batch mới hoặc retry cùng batch theo L1, có người duyệt khi đụng dữ liệu đã quarantine.

### 4.6 Join và aggregate an toàn

| Rule | Nội dung | Lý do | Trạng thái |
| --- | --- | --- | --- |
| J1 | Join line ↔ amount chỉ theo `line_id` trong cùng `snapshot_id`; assert 1:1 | Tránh nhân tiền | proposed |
| J2 | Chọn **một** revision áp dụng cho mỗi contract trước khi đọc dòng; không join contract → mọi revision → dòng rồi cộng | Phụ lục thay thế, không cộng (100 → 110, không 210) | proposed |
| J3 | Không join amount với submission/audit/document/reference (1:N) trước khi gom về grain contract | Tránh nhân tiền | proposed |
| J4 | Mọi dòng trong một tổng phải cùng `revision_id`; assert | Tránh lẫn revision | proposed |
| J5 | Bắt buộc group theo `currency` và `tax_basis`; không cộng chéo | Q4 chưa có policy | proposed |
| J6 | Áp scope quyền lên **từng** dataset đầu vào trước join/aggregate/group; tổng chỉ tính trên dòng đã lọc | Chặn lộ tiền project A qua tổng | proposed |
| J7 | Báo số dòng/hợp đồng bị loại theo lý do | Tránh tổng "đẹp" che thiếu dữ liệu | proposed |

### 4.7 Lineage, schema evolution và reconciliation

- **Lineage:** nguồn (model/ID, API path, `source_api_version`) → `extract_batch_id` + `snapshot_id` (kèm `snapshot_consistency`) → `observation_id` → payload (`content_sha256`) → validated (phiên bản rule) → curated (`materialization_id` gồm `transform_version`) → metric (`formula_version`). Mỗi số trên báo cáo truy ngược được đến observation, dòng nguồn và batch. Hai materialization từ cùng input nhưng khác transform/formula có lineage riêng.
- **Schema evolution:**
  - `schema_version` theo semver. Thêm field không bắt buộc là minor.
  - Enum mới chưa khai báo thì đưa vào quarantine cho đến khi contract được cập nhật.
  - OpenAPI đổi hash thì chặn publish cho đến khi review.
  - Breaking change tạo dataset version mới và chạy song song.
- **Reconciliation:**
  - Số contract theo project/trạng thái khớp list API cùng scope.
  - `aggregate_version` từng contract khớp nguồn; observation `same_version_conflict` và `out_of_workflow_change` được liệt kê riêng.
  - Lớp nguồn DC-06: `source_status`, `source_value`, `source_basis` bằng chuỗi với `effective_snapshot.total.status/value/tax_basis` cùng `as_of`. Contract không có revision áp dụng: API trả `total=null` và warning tương ứng.
  - Lớp policy DC-06: `report_status`, `policy_value` so với expected riêng của fixture theo `formula_version`, không so với API. Policy chưa được Q4/Q13 duyệt thì kết quả chỉ là kiểm chứng kỹ thuật.
  - `payload_sha256` submission khớp nguồn.
  - Chuỗi `version_before → version_after` của audit liên tục.
  - Số observation theo snapshot khớp số bản ghi đọc được; số payload ≤ số observation.
  - Batch có `snapshot_consistency` khác `consistent_proven` không được reconcile như tổng nhất quán.
  - Lệch thì quarantine, không publish một phần như thể đủ.

## 5. Security và retention (DP-04)

### 5.1 Nguyên tắc

1. **Tách độ mới dữ liệu khỏi độ mới quyền.** Refresh dữ liệu theo ngày không được làm revoke tài chính trễ một ngày. Lớp truy vấn kiểm grant/assignment/expiry hiện hành của Odoo tại thời điểm query. Nếu không lấy được quyền, từ chối dữ liệu tài chính/cá nhân/pháp lý (fail closed).
2. **Scope trước join/aggregate/grouping** (J6). Phải kiểm ca user xem metadata project A nhưng chỉ có tiền project B.
3. **`financial_read` không suy ra quyền khác.** Nó không cấp `financial.export`, share, download hay quyền xem raw. `financial.export` hiện chỉ là `proposed` (chưa có ở runtime).
4. **Raw/staging không truy cập trực tiếp.** Người dùng và React chỉ đi qua API có kiểm quyền.
5. **Không sao chép grant/assignment làm nguồn quyền thứ hai.** Nếu cần cache quyền thì cache theo actor + scope + TTL ngắn và invalidate khi Odoo thay đổi. Cơ chế này phải được chứng minh bằng test V08/V20.
6. **Lake/analytics store không phải backup Odoo.** Mỗi hệ thống cần runbook phục hồi riêng. Không hứa thu hồi bản người dùng đã tải xuống.
7. **Snapshot token không mang quyền.** Export nhất quán (M2, [mục 4.4.1](#441-phân-trang-khác-tính-nhất-quán)) chỉ định danh dữ liệu đã chụp; mỗi lần đọc vẫn kiểm user/scope hiện hành trong Odoo. Quyền đổi trong lúc đọc thì fail closed và không ghép các trang đọc dưới hai trạng thái quyền.

### 5.2 Ma trận theo lớp dữ liệu

| Lớp | Ví dụ hiện có | Đọc ở nguồn (runtime) | Bản dẫn xuất (staging/raw → validated → curated) | Query/cache | Export/share/download | AI index | Retention / deletion / legal hold | Backup | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Metadata | code, name, state, revision, line name, work item | Assignment + company | Được phép sau review redaction C03; tách khỏi tiền | Cache key gồm actor + scope + `as_of`; không cache toàn cục | Theo policy L `report.export` (proposed) | Chưa | Theo nguồn; tombstone khi nguồn xóa draft | Theo store, không thay backup Odoo | Data dictionary 8 | metadata: observed-static; dẫn xuất: proposed |
| Financial | line amount, approval amount, submission financial snapshot, file `financial` | Assignment + `financial_read` theo project | Vùng tách riêng; mã hóa bắt buộc; không vào raw chung khi chưa có Q14 | Kiểm grant hiện hành mỗi query; fail closed | Cần `financial.export` riêng (chưa có); không share link | Không | Q11/Q14; legal hold theo hợp đồng | Mã hóa + hạn lưu (gap) | `ir.access.csv` amount; test export/read_group | nguồn: observed-static; còn lại: proposed |
| Personal | login, tên người quyết định, actor, reviewer, counterparty cá nhân | Theo record scope | Pseudonym `actor_ref` khi ra ngoài Odoo; tối thiểu hóa | Như metadata | Không xuất danh tính khi không cần | Không | Theo HR/privacy (Q11); xóa theo yêu cầu hợp lệ | Như trên | DTO `_ref`, `decided_by_name` | proposed |
| Legal/BASE | reference, decision, evidence hash, authority, signed/effective | Project scope (DTO hiện trả nhiều field cho metadata reader) | Chỉ field đã qua allowlist C03 | Như financial nếu chứa căn cứ pháp lý | Theo Q1/Q11 | Không | Legal hold ưu tiên trên deletion | Như trên | F08 | proposed |
| File/binary | attachment tài liệu hợp đồng | Document + project + confidentiality + grant | **Không sao chép** file khi chưa có classification/retention/owner; chỉ metadata + checksum | Stream qua backend, `no-store` | Download hiện kiểm grant; share/public link chưa có | Không | Q11 | Filestore Odoo theo OPS-001 | `documents/{did}/content` | observed-static + proposed |
| Authorization | grant, assignment, group | ORM/ACL | Không sao chép làm quyền; chỉ log quyết định truy cập | Query Odoo/invalidate | — | — | Ledger chưa có (R17) | — | E05, E06 | observed-static |
| Technical | idempotency, request_id, salt, fingerprint | `base.group_system` | Loại khỏi dataset | — | — | — | Hạn lưu idempotency chưa có | — | E18 | observed-static |

### 5.3 Ma trận theo lớp/kênh của Data Platform

| Lớp/kênh | Truy cập trực tiếp | Kiểm quyền | Freshness quyền | Retention/deletion | Backup | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Odoo nguồn | Qua ORM/API | ACL + rule + grant | Mỗi request | Theo Odoo | OPS-001 local, chưa mã hóa/offsite | `PROJECT_STATUS` | observed-static |
| Extract/staging (O-A) hoặc raw (O-B) | Không ai ngoài service ingest | Service identity tối thiểu, có audit | Không phục vụ query | Hạn lưu ngắn có cấu hình; xóa khi hết hạn trừ legal hold | Có thể tái tạo từ nguồn với hiện trạng; lịch sử thì không | — | proposed |
| Validated | Data steward qua công cụ có audit | Theo vai trò steward + scope | Như dưới | Như raw | Như raw | — | proposed |
| Curated/mart | Chỉ qua API | Scope + grant kiểm tại query | Tại query | Theo KPI (Q13) | Tái tạo được từ validated | — | proposed |
| Query API | Người dùng | Odoo session/actor | Tại query; fail closed | — | — | Mẫu `tp_planning_api` | proposed |
| Cache | Không | Key gồm actor + scope + `as_of` + version quyền | Invalidate khi grant/assignment đổi; TTL ngắn | Không lưu lâu | Không backup | Data dictionary 8 | proposed |
| Export file | Người có capability riêng | `financial.export`/`report.export` | Kiểm tại thời điểm export | Không thu hồi được bản đã tải; ghi audit | — | — | proposed |
| Share link | Không có hôm nay | Không hạ classification | — | — | — | Data dictionary 6.3 | proposed |
| AI index | Không có hôm nay | Index tách theo classification; kiểm quyền khi trả lời | Tại query | Xóa khỏi index khi nguồn xóa/hết hạn | Không coi là backup | — | proposed (UC-03 defer) |
| Log/error | Ops | Không chứa tiền, credential, cookie, UNC | — | Hạn lưu ops | — | `ir_http.py` lỗi có cấu trúc | proposed |

### 5.4 Ca kiểm quyền bắt buộc

Mọi phương án đều phải đạt các ca V07–V11, V20 và V22 ở [mục 7](#7-kế-hoạch-poc--kiểm-chứng-dữ-liệu-giả-dp-06). Nguồn hiện đã có test cùng tinh thần ở ORM/API (`test_metadata_on_a_and_financial_on_b_only`, `test_revoked_grant_applies_to_next_read`, `test_expired_grant_is_ignored`, `test_native_aggregates_and_export_hide_amounts`). Lớp dẫn xuất phải tự chứng minh lại, không được thừa hưởng kết luận từ nguồn.

### 5.5 Gap vận hành chưa có căn cứ

Mã hóa at-rest cho bản sao hiện là gap: backup local chưa mã hóa. Mã hóa in-transit cũng là gap vì chưa có HTTPS production. Các gap còn lại:

- service account/token cho trích xuất (API chỉ có session người dùng);
- audit truy vấn/export;
- backup/restore cho store dẫn xuất;
- residency/nơi đặt dữ liệu;
- secret rotation;
- incident runbook.

Tất cả là `unknown`/gap, gắn Q14 (R03, R11).

## 6. Phương án (DP-05)

### 6.1 Bảng phương án

| Phương án | Nguồn/budget/latency/skill giả định | Chi phí storage/compute/egress/ops/backup | Lợi | Hại | Nguồn chứng cứ | Điều kiện chọn | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O0 — Report/read service có kiểm quyền trong Odoo (C17/RPT-001, `tp_reporting`) | Một nguồn Odoo; budget hạ tầng 0; latency tại request; skill Odoo/Python hiện có | Không thêm storage. Compute dùng chung Odoo (cần đo khi có volume). Egress 0. Ops/backup theo Odoo | Không sao chép; quyền và revoke đúng ngay; tái dùng `_effective_revision`, `_amount_summary`, ACL đã test | Tải query vào Odoo; không có lịch sử "biết tại Y" ngoài submission; khó join nguồn ngoài | Mục 3.4; master plan C17 | Use case một nguồn, volume nhỏ/vừa, cần quyền tức thời | proposed (đề xuất dùng khi UC-01 được chọn) |
| O-A — Analytics-first: API/export theo lịch → staging → PostgreSQL analytics/read replica → curated marts | 1–3 nguồn có cấu trúc; latency giờ/ngày; skill SQL/Python | Thêm 1 database và job lịch. Replica cần thêm host. Ops: lịch, giám sát, retry, backup riêng. Egress tùy nơi đặt (Q14) | Tách tải khỏi Odoo; SCD/lịch sử snapshot; SQL quen thuộc; dễ bỏ | Phải tự dựng kiểm quyền tại query; API hiện thiếu export/cursor/tombstone; replica sao chép **toàn bộ** dữ liệu gồm tiền | Mục 1.2, 4.4, 4.5 | ≥ 2 nguồn đã xác nhận cần join, hoặc tải đo được ảnh hưởng Odoo, hoặc cần lịch sử X/Y; Q13/Q14 xong | proposed (chưa đủ điều kiện) |
| O-B — Lakehouse-lite: raw object storage/Parquet → validated → curated | Nhiều nguồn/file lớn, replay lịch sử; skill data engineering | Object storage + catalog + query engine + orchestration. Vận hành Windows/Linux, retention, xóa trên file bất biến. Backup/versioning riêng | Raw bất biến cho replay; chứa file/bản vẽ; mở rộng tốt | Nhiều thành phần nhất; xóa/legal hold trên Parquet bất biến khó; kiểm quyền hàng/cột cần thêm lớp; skill chưa có | Kế hoạch mục 4 | Corpus file/bản vẽ lớn hoặc replay đa nguồn mà O-A không đáp ứng, chứng minh bằng use case | proposed (không đề xuất) |
| O-C — CDC/Kafka/Spark | Tải lớn, nhiều bảng, cần thay đổi gần thời gian thực | Cao nhất; quyền DB trực tiếp | Đầy đủ thay đổi | Bỏ qua ORM/ACL; delete/schema migration phức tạp | Không có use case chứng minh | Chỉ khi use case chứng minh | NOT_EVALUATED |

### 6.2 So sánh theo tiêu chí

| Tiêu chí | O0 Odoo report | O-A analytics-first | O-B lakehouse-lite | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| Chi phí | Thấp nhất | Trung bình | Cao | Không báo giá vendor | proposed |
| Vận hành | Không thêm hệ thống | +1 DB + job | +storage/catalog/engine/orchestration | — | proposed |
| Freshness dữ liệu | Live | Theo lịch | Theo lịch | — | proposed |
| Freshness quyền | Live (ACL Odoo) | Phải gọi Odoo hoặc invalidation | Như O-A, khó hơn với engine ngoài | F07 | proposed |
| Scale | Giới hạn bởi Odoo; cần đo | Tốt cho có cấu trúc | Tốt nhất cho file/khối lớn | Volume `unknown` | unknown |
| Replay/lịch sử | Chỉ submission snapshot | Có nếu lưu SCD | Có (raw bất biến) | F04, F09 | proposed |
| Delete/tombstone | Không cần (đọc nguồn) | Phải phát hiện bằng full snapshot | Phải xóa trên file bất biến + legal hold | Mục 4.5 | proposed |
| Bề mặt bảo mật | Nhỏ nhất | Thêm bản sao tiền | Lớn nhất | Mục 5 | proposed |
| Backup/restore | Theo Odoo | Riêng | Riêng + versioning | OPS-001 | proposed |
| Rollback/thoát | Gỡ endpoint | Xóa DB/job | Phức tạp hơn | — | proposed |
| Skill | Đã có | SQL/Python | Data engineering | `unknown` về nhân sự | unknown |

### 6.3 Kịch bản low/base/high (giả định, cần đo)

Số dưới đây là **giả định minh họa** để thấy điểm chuyển phương án, không phải quy mô công ty. Cần chủ nghiệp vụ cung cấp hoặc đo trên môi trường được phép (Q2 trong mục 10).

| Kịch bản | Giả định | Phương án phù hợp | Cần đo |
| --- | --- | --- | --- |
| Low | ≤ vài trăm hợp đồng, 1 nguồn, báo cáo tại request | O0 | Số hợp đồng/revision/dòng; thời gian query aggregate |
| Base | Vài nghìn hợp đồng, 2 nguồn (Contracts + kế toán), báo cáo ngày | O0 nếu aggregate trong Odoo đạt; nếu không, O-A | Tải Odoo khi chạy báo cáo; cadence kế toán (Q6) |
| High | Hàng chục nghìn hợp đồng hoặc corpus bản vẽ/hồ sơ lớn, nhiều nguồn, cần replay lịch sử | O-A cho có cấu trúc; O-B chỉ khi file/replay chứng minh | Dung lượng file, tốc độ tăng, yêu cầu replay |

### 6.4 Outbox và audit hiện có có dùng làm change feed được không?

| Tiêu chí | Outbox (`tp.contract.outbox`) | Audit (`tp.contract.audit`) | Yêu cầu của change feed | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| Coverage action | Chỉ submit/resubmit/return | Mọi action workflow: create, amendment, edit, submit, resubmit, return, rework | Mọi thay đổi | `_tp_notify`, `_tp_audit` | observed-static |
| Coverage entity | Tham chiếu contract/revision | Contract/revision/submission | Mọi entity, gồm document/reference/grant/project | — | observed-static |
| Thay đổi ngoài workflow | Không | Không (setup/superuser) | Có | F03 | observed-static |
| Delete | Không | Không có diff | Tombstone rõ | `_tp_apply_lines` | observed-static |
| Payload | Chỉ reference | Version/state/hash, không diff, không tiền | Payload hoặc reference đọc được trạng thái **tại event** | — | observed-static |
| Bootstrap snapshot | Không | Không | Có | — | observed-static |
| Cursor/offset handoff | Không có API; theo recipient | Không có API đọc | Cursor bền | OpenAPI | observed-static |
| Ordering | Theo `id` (không bảo đảm theo commit) | `version_before/after` trong contract | Thứ tự theo aggregate | `_tp_lock` | observed-static |
| Retry/replay | Retry `_tp_deliver_pending`; không replay cho consumer mới | Append-only, có thể đọc lại | Replay từ offset | test n08 | observed-static |
| Retention | Không xóa | Không xóa | Có policy | — | observed-static |

Kết luận: outbox là hàng đợi thông báo theo người nhận, **không** phải change feed. Audit gần change feed hơn cho phạm vi workflow, nhưng vẫn thiếu thay đổi ngoài workflow, diff và delete. Nếu sau này mở O-A, cần thay đổi code riêng theo [mục 4.4.1](#441-phân-trang-khác-tính-nhất-quán): (a) export materialized nhất quán phía server có `source_snapshot_token` (M2), hoặc (b) change log có tombstone, ordering và cursor, bootstrap bằng M2 (M3). Cursor/keyset một mình chỉ giải quyết phân trang, không phải tính nhất quán. Không tái dùng outbox.

### 6.5 Kafka/Spark/CDC

`NOT_EVALUATED`: không use case nào trong mục 3 cần thay đổi gần thời gian thực, khối lượng lớn hay xử lý phân tán. CDC đọc thẳng PostgreSQL còn bỏ qua ACL/rule Odoo, trái nguyên tắc DP-04. Chỉ đánh giá lại khi có use case đo được nhu cầu.

## 7. Kế hoạch PoC / kiểm chứng dữ liệu giả (DP-06)

**PoC lake: `NOT_APPLICABLE`**, vì recommendation là `DEFER`. Dưới đây chỉ là **đặc tả kiểm chứng** cho UC-01, áp dụng cho O0 (C17/RPT-001 khi được giao) và tái dùng nếu sau này O-A được mở. Không có ca nào được thực thi trong DP-001.

Dữ liệu giả đề xuất (không phải dữ liệu công ty, không lấy từ dev seed thật):

| Fixture | Nội dung giả |
| --- | --- |
| Project | `P-SIM-A`, `P-SIM-B` cùng company giả; mỗi project có phòng chủ trì giả |
| Hợp đồng | `HD-SIM-01` (P-SIM-A, VND): gốc 100 hiệu lực 2026-01-10; phụ lục 110 hiệu lực 2026-03-01. `HD-SIM-02` (P-SIM-A, VND): một dòng chưa xác nhận. `HD-SIM-03` (P-SIM-B, USD): 25 confirmed. `HD-SIM-04` (P-SIM-B, VND): hai revision cùng ngày hiệu lực. `HD-SIM-05` (P-SIM-B, VND): một dòng excluding_tax, một dòng including_tax. `HD-SIM-06` (P-SIM-B, VND): dòng confirmed 0, basis `excluding_tax`. `HD-SIM-07` (P-SIM-B, VND): hai dòng confirmed 30 + 20 cùng basis `unknown`. `HD-SIM-08` (P-SIM-B, VND): một dòng confirmed `unknown` 30, một dòng confirmed `excluding_tax` 20. `HD-SIM-09` (P-SIM-B, VND): hai dòng confirmed 30 + 20 cùng `excluding_tax`. `HD-SIM-10` (P-SIM-A, VND): một dòng không có amount record, một dòng `unconfirmed` |
| Observation giả | Payload A/B của cùng một contract giả dùng cho V12, V14, V24–V26, V30–V34; chỉ là JSON giả trong test, không lấy từ runtime |
| User | `U-META-A`: assignment A, không grant. `U-FIN-A`: assignment A + `financial_read` A. `U-MIX`: assignment A và B, `financial_read` chỉ B. `U-NOASSIGN`: grant B nhưng không assignment |

| ID | Input giả | Thao tác dự kiến | Expected output/metrics | Ca âm | Bằng chứng sẽ thu | Áp dụng | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V01 | HD-SIM-01 | Báo cáo P-SIM-A `as_of` 2026-02-01 và 2026-03-15 | 100 rồi 110 | Không bao giờ ra 210 | Response + assertion | O0, O-A | NOT_RUN |
| V02 | HD-SIM-02, HD-SIM-10 | Báo cáo P-SIM-A | Lớp nguồn: `source_status=incomplete`, `source_value=null` cho cả dòng thiếu amount record và dòng `unconfirmed`. Lớp policy giữ `incomplete`; `project_total` null; liệt kê bị loại | Không thay null bằng 0; thiếu amount khác confirmed 0 | Response | O0, O-A | NOT_RUN |
| V03 | HD-SIM-06 | Báo cáo P-SIM-B | Lớp nguồn: `confirmed`, `source_value` = `"0"` theo decimal_places, basis `excluding_tax`. Lớp policy: `confirmed`, đóng góp 0 vào bucket (VND, `excluding_tax`) | 0 không thành incomplete/null | Response | O0, O-A | NOT_RUN |
| V04 | HD-SIM-05 | Báo cáo P-SIM-B | Lớp nguồn: `mixed_basis`, `source_value=null`, `source_basis=mixed`. Lớp policy giữ `mixed_basis`, không cộng | Không cộng gross với net | Response | O0, O-A | NOT_RUN |
| V05 | HD-SIM-03 + HD-SIM-06 | Báo cáo P-SIM-B | Hai bucket USD/VND | Không quy đổi | Response | O0, O-A | NOT_RUN |
| V06 | HD-SIM-04 | Báo cáo tại ngày trùng | `effective_date_conflict`; không chọn ID lớn | — | Response + warnings | O0, O-A | NOT_RUN |
| V07 | U-MIX | Báo cáo A+B, group theo project, drilldown A | A chỉ có số lượng; B có giá trị; tổng toàn scope chỉ từ B | Không suy được tiền A qua tổng/group/hiệu số | Response + so sánh tổng | O0, O-A | NOT_RUN |
| V08 | U-FIN-A | Request 1 có tiền; thu hồi grant; request 2 | Request 2 không có tiền, kể cả từ cache | Cache cũ không trả tiền | Hai response + cache key | O0, O-A | NOT_RUN |
| V09 | U-FIN-A, grant `date_end` hôm qua | Báo cáo | Không có tiền | — | Response | O0, O-A | NOT_RUN |
| V10 | U-NOASSIGN | Báo cáo B | Không thấy hợp đồng/tiền (404 hoặc rỗng) | Grant không thay assignment | Response | O0, O-A | NOT_RUN |
| V11 | U-FIN-A | Thử export số liệu tài chính | Bị từ chối cho đến khi có `financial.export` | `financial_read` không đủ | Response 403 | O0, O-A | NOT_RUN (capability chưa có) |
| V12 | Một batch extract; observation giả | Lần thử 1 timeout giữa chừng, retry cùng `extract_batch_id`; sau đó chạy lại cùng khóa materialization | Mỗi `(snapshot_id, entity, source_id)` có đúng một observation; payload không nhân bản; materialization chạy lại giống từng byte | Retry không tạo observation thứ hai | Số observation/payload, hash output | O-A | NOT_RUN |
| V13 | Draft bỏ một dòng rồi gửi | Extract trước/sau | Tombstone `draft_deleted`; hiện trạng không còn dòng; lịch sử giữ | Không cộng dòng đã xóa | Diff snapshot | O-A | NOT_RUN |
| V14 | Hai observation version 5 và 4, hash khác, đến ngược thứ tự | Nạp | Hiện trạng = version 5; observation version 4 được giữ làm lịch sử | Không lùi version theo thứ tự response | Log + bảng observation | O-A | NOT_RUN |
| V15 | Batch bất kỳ | Truy ngược một số trên báo cáo | Ra `materialization_id` (transform/formula), `observation_id`, `content_sha256`, `snapshot_id` + `snapshot_consistency`, batch và nguồn ID; hash tính lại khớp | Thiếu một mắt lineage là fail | Lineage record | O-A | NOT_RUN |
| V16 | Báo cáo bất kỳ | Kiểm header | Có `as_of_business`, `known_at`, `data_freshness`, `dataset_status` | Thiếu header là fail | Response | O0, O-A | NOT_RUN |
| V17 | HD-SIM-01..10 | Reconcile lớp nguồn với API detail cùng `as_of`; kiểm lớp policy với expected fixture | Lớp nguồn: `source_status`/`source_value`/`source_basis` bằng chuỗi với `effective_snapshot.total.status/value/tax_basis` từng hợp đồng. Lớp policy: khớp expected riêng theo `formula_version` | Lệch lớp nguồn thì quarantine; khác biệt policy so với API không bị tính là lỗi reconcile | Báo cáo reconcile hai phần | O0, O-A | NOT_RUN |
| V18 | Trang dữ liệu hỏng | Nạp | Batch quarantine; không publish; không ghi gì vào Odoo | Không writeback | Log + kiểm audit Odoo không đổi | O-A | NOT_RUN |
| V19 | Thêm hợp đồng giữa hai trang (M1) | Extract | Liệt kê lại phát hiện drift; batch `inconsistent`, không publish | Không mất/trùng dòng; không bao giờ `consistent_proven` | Log + `snapshot_consistency` | O-A | NOT_RUN |
| V20 | Odoo không phản hồi kiểm quyền | Báo cáo tài chính | Từ chối (fail closed) | Không trả từ cache | Response | O0, O-A | NOT_RUN |
| V21 | HD-SIM-01 cùng ID; giữa trang 1 và trang 2 đổi amount, reference và revision áp dụng | Extract bằng offset, rồi bằng keyset | Cả hai cách đều tối đa `best_effort`; phát hiện thay đổi thì `inconsistent`, không publish | Keyset không làm ca này tự đạt `consistent_proven` | Log + `snapshot_consistency` | O-A | NOT_RUN |
| V22 | U-FIN-A; thu hồi grant `financial_read` hoặc assignment A giữa hai trang | Báo cáo/extract nhiều trang | Fail closed: trang sau không có tiền; không ghép trang đọc dưới hai trạng thái quyền; batch `inconsistent`; tiền đọc trước khi thu hồi không được publish cho user | Không dùng quyền đọc ở trang đầu cho cả batch | Response từng trang + log | O0, O-A | NOT_RUN |
| V23 | Export M2 có `source_snapshot_token` | Đổi dữ liệu sau khi tạo export; đọc các trang; dùng token với user khác và sau khi thu hồi quyền | Các trang cùng thời điểm export, `consistent_proven`; user khác hoặc user đã bị thu hồi bị từ chối | Token không mang quyền | Response + log export | O-A | NOT_RUN (cơ chế chưa có, cần code) |
| V24 | Observation giả: version 7 hash A là hiện trạng; đến observation version 7 hash B (setup đổi reference ngoài workflow) | Nạp + đọc xác minh | Xác minh ra hash B → nhận B, ghi `out_of_workflow_change`; observation A giữ | Không tự nhận B khi chưa xác minh | Log + bảng observation | O-A | NOT_RUN |
| V25 | Như V24 nhưng xác minh ra hash C, hoặc không đọc được nguồn | Nạp + xác minh trong giới hạn lần đọc | Quarantine `same_version_conflict`; hiện trạng giữ A có cảnh báo. Đảo thứ tự đến của A/B cho cùng kết quả | Không quyết theo `ingested_at`, `write_date` hoặc thứ tự response | Log + bảng observation | O-A | NOT_RUN |
| V26 | Hiện trạng từ batch `best_effort`; sau đó có snapshot M2 `consistent_proven` mới hơn, cùng version nhưng hash khác cho một phần entity | Nạp | Thay hiện trạng trong coverage của snapshot mới; bản ghi ngoài coverage giữ nguyên; observation cũ giữ | Không thay ngoài coverage | Bảng hiện trạng trước/sau | O-A | NOT_RUN |
| V27 | HD-SIM-07 (mọi dòng `unknown`) | Báo cáo P-SIM-B | Lớp nguồn: `confirmed`, `source_value` = 50 theo decimal_places, `source_basis=unknown`, khớp API. Lớp policy (proposed): `basis_unknown`, `policy_value=null`, liệt kê riêng, không vào tổng chính thức | Không ghi source là `mixed_basis`; không coi policy là kết quả nguồn | Response + reconcile hai lớp | O0, O-A | NOT_RUN |
| V28 | HD-SIM-08 (`unknown` + `excluding_tax`) | Báo cáo P-SIM-B | Lớp nguồn: `mixed_basis`, `source_value=null`, `source_basis=mixed`. Lớp policy giữ `mixed_basis` | Không cộng 30 + 20 | Response | O0, O-A | NOT_RUN |
| V29 | HD-SIM-09 (cùng `excluding_tax`) | Báo cáo P-SIM-B | Lớp nguồn và policy: `confirmed`, 50, cộng vào bucket (VND, `excluding_tax`) | Không lẫn với bucket basis khác | Response | O0, O-A | NOT_RUN |
| V30 | Observation giả: cùng version, cùng hash ở hai snapshot; và version cao hơn cùng hash | Nạp | Cùng version/hash: thêm observation, không thêm payload, hiện trạng giữ. Version cao hơn/cùng hash: cập nhật `record_version`, cảnh báo, không thêm payload | Không bỏ observation vì hash trùng | Số observation/payload | O-A | NOT_RUN |
| V31 | Entity không version (project/document metadata), hai response hash khác đến ngược thứ tự trong cùng batch `best_effort` | Nạp | Đọc xác minh; không xác minh được thì quarantine | Không lấy response đến sau làm đúng | Log | O-A | NOT_RUN |
| V32 | Observation giả: payload A ở S1, B ở S2, A ở S3 | Nạp ba snapshot | Ba observation, hai payload; tra known-at tại S1/S2/S3 ra A/B/A | Lần A thứ hai không bị dedupe | Bảng observation + payload | O-A | NOT_RUN |
| V33 | Cùng `snapshot_id`, transform hoặc formula v1 rồi v2 | Materialize hai lần | Hai `materialization_id` với lineage riêng; v2 không tái dùng output v1; chạy lại v1 cho cùng output v1 | Không bỏ qua rebuild vì input trùng | Lineage + hash output | O-A | NOT_RUN |
| V34 | Batch lỗi giữa chừng có một trang quarantine | Nạp, rồi replay có kiểm soát (retry L1 hoặc batch mới) | Batch lỗi không materialize/publish; replay hoàn tất không nhân bản observation; dữ liệu quarantine không vào curated khi chưa duyệt | Không publish một phần như đủ | Log batch + số observation | O-A | NOT_RUN |

Điều kiện chạy (khi được giao task riêng):

- Dùng runtime test cô lập theo C01/FND-002, database giả riêng. Không dùng dev/production.
- Không writeback.
- Cleanup database/process sau khi chạy.
- Bằng chứng nằm ngoài Git nếu chứa log runtime.
- PoC không phải pilot và không chứng minh dữ liệu công ty đúng.

## 8. Risk/gap register

| ID | Severity | Owner đề xuất (vai trò) | Câu hỏi/giả định | Phần bị chặn | Điều kiện xử lý | Gate | Evidence | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | High | Người dùng + KPI owner | Chưa chọn use case, chưa có KPI owner/công thức/ngưỡng | Mọi triển khai báo cáo/dữ liệu | Người dùng chọn UC; Q13 chốt owner/công thức/cadence | Q13 | Mục 3 | open |
| R02 | High | Platform/security | Bản sao không tự biết revoke/expiry | O-A/O-B cho dữ liệu tài chính | Thiết kế kiểm quyền tại query; V08/V09/V20 đạt | Q2 | F07 | open |
| R03 | High | Platform + ACCESS-DEC | Chưa có service identity; dùng user có grant rộng tạo superset quyền | Trích xuất O-A | Định nghĩa service identity tối thiểu, scope, audit, rotation | Q2, Q14 | Mục 1.2 | open |
| R04 | High | Tech lead | Delete vật lý ở draft, thay đổi ngoài workflow không có audit | Đồng bộ tăng dần | Full snapshot theo contract, hoặc change log có tombstone (code riêng) | — | F03 | open |
| R05 | Medium | Tech lead | Offset tối đa 10.000; mỗi request một transaction; không có snapshot token. Keyset chỉ giải quyết phân trang, không phải snapshot nhất quán | Bulk extract quy mô lớn; mọi batch muốn gắn `consistent_proven` | Export materialized M2 trong một transaction đọc nhất quán có `source_snapshot_token` không mang quyền, hoặc M3 đặc tả đủ bootstrap/delete/ordering/handoff/reconcile (code riêng, [mục 4.4.1](#441-phân-trang-khác-tính-nhất-quán)). Trước đó API hiện tại chỉ `best_effort`; V19, V21–V23 | — | F02 | open |
| R06 | High | Security + KD-OWNER | Text tự do và metadata BASE có thể chứa dữ liệu nhạy cảm | Mọi bản sao metadata | Review allowlist/redaction C03 trước khi sao chép | Q11 | F08 | open |
| R07 | High | ACCESS-DEC | `financial.export` chưa ở runtime | Export dữ liệu dẫn xuất | Capability + audit export | Q2, Q13 | Data dictionary 7.1 | open |
| R08 | Medium | Finance + KPI owner | VAT/currency/rounding chưa có policy; hợp đồng mọi dòng basis `unknown` có tổng nguồn `confirmed` nhưng chưa có policy có vào tổng chính thức hay không | Tổng chính thức, quy đổi, xử lý `basis_unknown` | Q4/Q13 chốt; trước đó bucket riêng, không quy đổi, `basis_unknown` liệt kê riêng có nhãn (policy proposed, [mục 3.3](#33-uc-01-đề-xuất--giá-trị-hợp-đồng-áp-dụng-theo-project)); V27–V29 | Q4, Q13 | Mục 4.3 | open |
| R09 | High | Kế toán | Nguồn kế toán chưa xác nhận cài/cấu hình/cadence | Báo cáo liên nguồn | Q6 + FIN-001 | Q6 | FS02 | open |
| R10 | Medium | Chủ nghiệp vụ | Volume/tăng trưởng/freshness chưa biết | Chọn/kích thước phương án | Ước lượng từ owner hoặc đo trên môi trường được phép | Q13, Q14 | Mục 6.3 | open |
| R11 | High | Operations | Chưa có mã hóa, offsite, RPO/RTO, residency | `REAL_DATA_APPROVAL` | Q14 chốt và runbook | Q14 | Mục 5.5 | open |
| R12 | Medium | Document owner | Retention/legal hold/deletion cho bản dẫn xuất và AI index chưa có | UC-02, UC-03 | Q11 chốt | Q11 | Mục 5.2 | open |
| R13 | Medium | Data steward | Mapping/cutover Excel chưa có | Backfill lịch sử | Q12 + IMP-001 | Q12 | FS03 | open |
| R14 | Medium | Tech lead | Chưa có lịch sử "biết tại Y" ngoài submission | Báo cáo hai mốc X/Y | Thiết kế history snapshot khi có use case | Q4, Q8 | F09 | open |
| R15 | Medium | Finance + legal | Correction/void sau thanh lý chưa có policy | Dataset lịch sử tài chính | Q8 | Q8 | Integration 3.1 | open |
| R16 | Medium | ACCESS-DEC | Grant không có ledger thu hồi, nên không audit được quyền lịch sử | Audit truy cập dữ liệu thật | Ledger grant (data dictionary 7.1) | Q2 | E06 | open |
| R17 | Low | Platform | Skill/người vận hành store thứ hai chưa biết | O-A/O-B | Người dùng xác nhận nguồn lực | Q14 | — | unknown |
| R18 | Low | Tech lead | Dev DB chưa upgrade; CTR-002a chỉ test | Bất kỳ kiểm chứng live nào | Dùng runtime cô lập C01/FND-002 | — | F01 | open |
| R19 | Medium | Tech lead + data steward | Thay đổi ngoài workflow không tăng version; response đến muộn; entity không version | Cập nhật hiện trạng ở lớp dẫn xuất | Áp [ma trận 4.4.2](#442-ma-trận-version--hash): xác minh từ nguồn có thẩm quyền hoặc quarantine; không quyết theo `ingested_at`/`write_date`/thứ tự response; V14, V24–V26, V30, V31 | — | Mục 4.4; audit DP-F02 | open |
| R20 | Medium | Tech lead | Dedupe toàn cục theo hash làm mất observation A→B→A và có thể tái dùng output của transform/formula cũ | Lịch sử known-at, replay, curated | Tách L1 retry / L2 observation / L3 payload và khóa materialization theo snapshot + schema/transform/formula ([mục 4.5.1](#451-retry-observation-và-payload)); V12, V15, V32–V34 | — | Mục 4.5; audit DP-F04 | open |

## 9. Recommendation và cổng

### 9.1 Recommendation: `DEFER` (đề xuất, không phải DEC)

**Phạm vi:** trì hoãn triển khai mọi Data Platform runtime, gồm analytics store, replica, lake, bucket, connector và pipeline. DP-001 vẫn hoàn tất phần thiết kế.

Trong thời gian defer:

1. Nếu người dùng chọn UC-01, hiện thực bằng read service có kiểm quyền trong Odoo (O0, thuộc C17/RPT-001, gate Q13). Không sao chép dữ liệu.
2. Dùng data contract mục 4 làm chuẩn cho API báo cáo mới: header `as_of`/`known_at`, decimal string, version, status thay vì 0.
3. Ghi nhận các tiền đề kỹ thuật chỉ mở khi có task riêng:
   - export materialized nhất quán có snapshot token (M2) hoặc change log đặc tả đủ (M3); cursor/keyset một mình không đủ (R05);
   - change log có tombstone (R04);
   - service identity (R03);
   - `financial.export` (R07);
   - quy tắc version × hash và observation/payload/materialization cho mọi bản sao (R19, R20).

**Giả định:**

- A1: volume hiện nhỏ. Đây là giả định, chưa đo.
- A2: chỉ Contracts có dữ liệu runtime.
- A3: chưa có feed BASE/kế toán.
- A4: nhu cầu freshness được đáp ứng bằng đọc live Odoo.
- A5: chưa có ngân sách/người vận hành store thứ hai.

**Điều kiện đánh giá lại:**

- Mở lại `ANALYTICS_FIRST` khi có:
  - T1: ít nhất hai nguồn đã xác nhận cần join, có owner. Ví dụ Contracts + kế toán sau Q6.
  - T2: tải báo cáo đo được ảnh hưởng Odoo, hoặc cần lịch sử "biết tại Y" ngoài submission.
  - T3: Q13/Q14 đã chốt.
- Chỉ xét `LAKEHOUSE_LITE` khi có:
  - T4: corpus file/bản vẽ lớn hoặc replay đa nguồn mà analytics-first không đáp ứng, chứng minh bằng use case.

### 9.2 Trạng thái ba cổng

| Cổng | Trạng thái | Căn cứ | Còn thiếu |
| --- | --- | --- | --- |
| `DESIGN_COMPLETE` | v1: `NEEDS_FIX` theo [audit CHG-024](TP_DATA_PLATFORM_DP001_AUDIT.md). v1.1: tự đánh giá `PROPOSED_COMPLETE`, **chờ phiên chính audit lại** | Mục 1–8 đủ bảng tối thiểu của kế hoạch mục 7; DP-F01…F04 được sửa theo [mục 0.1](#01-correction-sau-audit-chg-024); mỗi unknown có owner vai trò/tác động | Re-audit độc lập; không phải chốt nhu cầu/công nghệ |
| `READY_FOR_SYNTHETIC_POC` | `NOT_APPLICABLE` cho PoC lake (DEFER). Kiểm chứng UC-01 trên O0 là `NOT_READY` | Mục 7 đã đặc tả V01–V34, tất cả `NOT_RUN` | Người dùng chọn UC-01 và giao task C17 riêng; runtime cô lập C01. Không chờ Q công ty không liên quan |
| `REAL_DATA_APPROVAL` | `BLOCKED` | Mục 8 | Q13 owner/KPI, Q2 quyền/ledger, Q11 classification/retention, Q14 vận hành; Q4/Q6/Q8 cho số tài chính chính thức; PoC/kiểm chứng chưa chạy |

### 9.3 Cổng Q liên quan

| Q | Liên quan Data Platform | Chặn gì | Trạng thái |
| --- | --- | --- | --- |
| Q2 | Ai cấp/thu hồi quyền; ledger; service identity | Truy cập dữ liệu thật, export, cache quyền | open |
| Q4 | VAT/gross-net, currency, rounding, hồi tố; xử lý hợp đồng basis `unknown` | Tổng chính thức, quy đổi, policy `basis_unknown` | open |
| Q6 | Feed invoice/payment/reconcile và cadence | Báo cáo liên nguồn, KPI tiền mặt | open |
| Q8 | Correction/void sau thanh lý | Lịch sử tài chính | open |
| Q11 | Classification, share, retention, privacy | Sao chép metadata/file, UC-02, UC-03 | open |
| Q12 | Mapping legacy, cutover, owner đối chiếu | Backfill lịch sử từ Excel | open |
| Q13 | KPI owner, công thức, cadence, ngưỡng, phạm vi export; cách hiển thị bucket `basis_unknown` | Mọi báo cáo/KPI | open |
| Q14 | RPO/RTO, retention, mã hóa, host backup, incident | Mọi store dẫn xuất và dữ liệu thật | open |

Q1/Q3 (thẩm quyền, BASE ID) chỉ chạm DP khi dữ liệu BASE thật được đưa vào; Q5/Q9/Q10 chạm khi các domain đó có dữ liệu.

### 9.4 Thiết kế kỹ thuật khác nghiệm thu nghiệp vụ

Tài liệu này là thiết kế kỹ thuật/dữ liệu. Nó không thay business acceptance và không xác nhận KPI, owner hay quyền người thật. Kiểm chứng V01–V34, kể cả khi đạt trong tương lai, chỉ là technical evidence trên dữ liệu giả. Business acceptance cần chủ nghiệp vụ xác nhận use case, công thức, mẫu đối chiếu khử dữ liệu và quyền. Mở dữ liệu thật cần `REAL_DATA_APPROVAL` riêng.

## 10. Câu hỏi ưu tiên cho người dùng

Xếp theo ảnh hưởng, tối đa năm câu:

1. **Mục tiêu và owner (Q13):** chọn UC-01 (giá trị hợp đồng áp dụng theo project), UC-02 (sổ hồ sơ) hay UC-03 (AI tra cứu), hoặc chưa cần? Vai trò nào chịu trách nhiệm công thức, ngưỡng và cadence?
2. **Quy mô và độ trễ:** ước lượng số project, hợp đồng và hồ sơ hiện có và mỗi năm, cùng độ trễ chấp nhận (tức thời/ngày/tuần). Ai cung cấp? Không đọc database thật để lấy số.
3. **Nơi đặt và vận hành bản dẫn xuất (Q14):** có cho phép bản sao dữ liệu tài chính ngoài Odoo không? Đặt ở đâu (máy chủ nội bộ/cloud, residency), RPO/RTO, mã hóa, ai vận hành?
4. **Export, share và retention (Q11, `financial.export`, Q2):** ai được xuất số liệu tài chính? Bản dẫn xuất/index giữ bao lâu, legal hold thế nào?
5. **Kế toán và thuế (Q6/Q4):** báo cáo liên nguồn có cần trong 6–12 tháng không? Kế toán ở hệ thống nào, cadence ra sao, chính sách VAT/currency thế nào? Hợp đồng có mọi dòng basis `unknown` (Odoo vẫn cho tổng `confirmed`) có được đưa vào tổng chính thức, tách bucket riêng hay chỉ liệt kê?

Phần thiết kế độc lập đã hoàn tất; thiếu đáp án không chặn việc review tài liệu này.
