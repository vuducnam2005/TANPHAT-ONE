# TANPHAT ONE — Kết quả audit DP-001

**Ngày:** 29/10/2026 (Asia/Saigon). **Change:** `CHG-20261029-024`.

**Verdict:** `NEEDS_FIX` cho cổng `DESIGN_COMPLETE`. Recommendation `DEFER` có cơ sở: hiện chưa có use case được xác nhận buộc phải sao chép dữ liệu ra hệ thống khác. Đây là kết luận review kỹ thuật, không phải quyết định công nghệ, business acceptance hoặc cho phép triển khai.

## 1. Phạm vi và baseline

- Đối chiếu [discovery DP-DISC-v1](TP_DATA_PLATFORM_DISCOVERY.md), [prompt DP-001](../prompts/CLAUDE_DATA_PLATFORM_DISCOVERY.md), [kế hoạch chuẩn bị](TP_DATA_PLATFORM_PREPARATION_PLAN.md), status, changelog và source Odoo/API liên quan.
- HEAD `95bfc3f4`, branch `main`; thay đổi chưa commit CHG-016…023 đã có trước audit. Không nhận các thay đổi code đang có trong working tree là sản phẩm của DP-001 hoặc lượt audit.
- Preflight `scripts/ai_workflow.py check` đạt CHG-023. Không có checkpoint trước lượt này. Snapshot trước audit dùng đúng `scripts.ai_workflow.snapshot`: 127 file, digest `056ae25bced60c72acae70507533e78377d8bd8a9839e0bc194027c05bc392ca`; lưu ngoài Git tại `.local/dp001-audit/before.json`.
- Chỉ sửa tài liệu bàn giao/audit/prompt. Không sửa application code, OpenAPI, toolchain hoặc runtime scripts; không kết nối database, đọc NAS/Excel/filestore thật, start/upgrade/seed Odoo, triển khai PoC, commit hoặc push.

## 2. Phần đạt

Discovery có đủ inventory 20 model/dataset, API/DTO, nguồn tương lai, ba use case ứng viên, tám data contract, ma trận quyền/retention, phương án O0/O-A/O-B, đặc tả V01–V20 và risk/gap register.

Các ranh giới chính đúng: Odoo giữ giao dịch/quyền; BASE giữ quyết định phê duyệt; kế toán giữ posting/payment/reconciliation. Outbox thông báo không được coi là change feed. Tài liệu nhận diện thiếu bulk export/cursor/tombstone, delete vật lý trước submit và thiếu grant ledger. Scope trước join/aggregate, quyền hiện hành khi query, fail closed và export capability riêng đã được nêu. Các ca giả đều `NOT_RUN`.

Với dữ kiện hiện có, ưu tiên report có kiểm quyền ngay trong Odoo khi UC-01 được chọn là đề xuất hợp lý. Chưa có căn cứ dựng lake, bucket, connector, Spark hoặc Kafka.

## 3. Finding cần sửa

Các số dòng dưới đây tham chiếu DP-DISC-v1 trước correction.

### DP-F01 — P2: Keyset cursor không bảo đảm point-in-time snapshot

**Vị trí:** discovery dòng 222–228, R05 dòng 438 và tiền đề dòng 464.

Tài liệu coi export trong một transaction hoặc keyset cursor là cách giải quyết snapshot nhất quán. Keyset giúp phân trang ổn định theo khóa, nhưng nội dung, quan hệ, quyền hoặc bản ghi có thể thay đổi giữa hai request. Liệt kê lại cùng ID cũng không chứng minh toàn bộ dataset thuộc cùng một thời điểm.

**Cần sửa:** tách pagination khỏi consistency. Bản xuất được publish như snapshot nhất quán phải có cơ chế xác định rõ như export materialized trong một transaction đọc nhất quán với snapshot token dùng xuyên trang. Nếu chọn watermark/change log thì phải đặc tả bootstrap, delete, ordering, handoff và reconciliation trước khi tuyên bố tương đương. API hiện tại chỉ là đọc best effort; không tự gắn `consistent=true`.

**Ca đặc tả bổ sung:** ID không đổi nhưng amount/reference/relation đổi giữa hai trang; keyset không được làm ca này tự đạt. Thay đổi quyền trong lúc đọc vẫn phải fail closed.

### DP-F02 — P2: Chưa xử lý cùng version nhưng khác nội dung

**Vị trí:** DC-02 dòng 189; mục 4.4 dòng 220–221; V14 chỉ kiểm version 5/4.

DC-02 chỉ nhận version cao hơn. Chính discovery thừa nhận lifecycle, reference hoặc document có thể đổi ngoài workflow mà không tăng `aggregate_version`. So hash phát hiện thay đổi nhưng chưa quy định chấp nhận, xác minh hay quarantine; consumer có thể bỏ thay đổi hợp lệ hoặc dùng phản hồi đến muộn để ghi đè hiện trạng.

**Cần sửa:** có ma trận cho higher/lower/equal version × same/different hash. Equal version/different hash phải được đọc xác minh bằng nguồn/snapshot có thẩm quyền; khi chưa có thứ tự tin cậy thì quarantine, không tự ghi đè theo `ingested_at`, `write_date` hoặc thứ tự response. Dữ liệu không có version cũng cần quy tắc riêng. Cập nhật DC-02, phần version/reconcile, risk và ca kiểm chứng đồng bộ.

### DP-F03 — P2: `tax_basis=unknown` mô tả không khớp source

**Vị trí:** mục 4.3 dòng 207; DC-06 dòng 193; reconciliation dòng 269 và V17 dòng 417.

Tài liệu ghi unknown hoặc lẫn basis đều thành `mixed_basis`, không cộng, và gắn nhãn `observed-static`. Source [tp_contract_revision.py](../../custom_addons/tp_contract/models/tp_contract_revision.py) tại `_amount_summary` dòng 145–158 chỉ trả `mixed_basis` khi có nhiều basis. Một dòng confirmed, value 100, basis unknown vẫn trả `status=confirmed`, `value=100`, `tax_basis=unknown`. Giá trị unknown hợp lệ theo `TAX_BASES` tại [tp_contract_line.py](../../custom_addons/tp_contract/models/tp_contract_line.py).

**Cần sửa:** mô tả đúng nguồn. Nếu báo cáo đề xuất không công bố tổng chính thức khi basis unknown, tách `source_status/source_value` khỏi `report_status/policy_value`, đánh dấu policy là `proposed` và giữ Q4/Q13. Reconcile giá trị nguồn với API riêng; kiểm policy riêng. Không sửa source để làm đúng một mô tả tài liệu sai.

**Ca đặc tả bổ sung:** một/mọi dòng confirmed cùng unknown, unknown + một basis đã biết, known basis thống nhất, 0 và missing/unconfirmed. Kết quả nguồn và kết quả policy phải phân biệt.

### DP-F04 — P2: Dedupe toàn cục làm mất lần quan sát A→B→A

**Vị trí:** mục 4.5 dòng 243; envelope dòng 169–174; lineage và V12/V15.

Khóa `(source_env, entity, source_id, content_sha256)` chống trùng toàn cục không phân biệt lần quan sát mới. Khi nội dung đổi A→B→A, lần A thứ hai có hash đã gặp nhưng thuộc snapshot/thời điểm khác. Bỏ nó làm sai lịch sử known-at. Nếu dùng cùng khóa cho curated, đổi `transform_version` cũng có thể tái dùng output cũ.

**Cần sửa:** tách retry cùng batch, immutable observation theo snapshot/batch và content-addressed payload dùng lại được. Hai observation cùng payload ở hai snapshot vẫn được giữ; không cần copy binary/payload lần hai. Khóa/materialization cho kết quả dẫn xuất phải gắn version schema/transform/formula phù hợp. Replay cùng batch không nhân bản; transform mới tạo output version mới hoặc rebuild có kiểm soát, không bỏ qua.

**Ca đặc tả bổ sung:** A→B→A giữ đủ ba observation; retry A trong cùng batch không tăng số bản; cùng input với transform v1/v2 cho hai materialization có lineage riêng.

## 4. Bằng chứng và giới hạn kiểm tra

| Kiểm tra | Kết quả | Giới hạn |
| --- | --- | --- |
| Workflow preflight | PASS CHG-023; current count 127 và digest khớp state | State sau handoff không tự chứng minh snapshot trước DP-001 |
| Docs validator gốc | PASS 25 file | Danh sách mặc định chưa có discovery |
| Docs validator mở rộng tại runtime, thêm discovery vào `NAMES` | PASS 26 file, 175 link nội bộ, 147 bảng, 0 lỗi trước khi thêm báo cáo/prompt; kết quả bàn giao cuối gồm cả hai file mới: PASS 28 file, 182 link, 149 bảng, 0 lỗi | Kiểm cấu trúc, không xác nhận semantic/business hoặc chạy V01–V20 |
| `git diff --check` trước sửa tài liệu audit | PASS | Git không bao phủ file untracked; cần kiểm whitespace riêng file mới |
| `scripts/dev.py status` | Odoo/PostgreSQL đều không listening | Không kết nối DB; không kiểm dữ liệu/module runtime |
| Application tests | NOT_RUN | Audit/spec-only, không đổi code |

Đối chiếu exact snapshot trước/sau audit đạt 127/127 file, 0 file thêm/xóa/đổi; digest giữ nguyên. Whitespace hai file mới đạt. Kết quả tại `.local/dp001-audit/code_comparison.json`; bản ghi bằng chứng cuối là CHG-025, verdict audit CHG-024 giữ nguyên.

DP-001 khai báo snapshot 119 file trong các thư mục code; checker hiện theo dõi 127 file gồm cả config/toolchain được liệt kê. Chưa có danh sách/hash trước DP-001 được tham chiếu đủ rõ để đối chiếu exact scope. Đây là khoảng trống bằng chứng, không phải bằng chứng code đã bị đổi. Correction cần giải trình scope bằng artifact thực có; nếu không còn thì ghi giới hạn, không dựng lại baseline quá khứ. Snapshot 127 file trong CHG-024 chỉ chứng minh phạm vi lượt audit và là baseline thực cho correction tiếp theo.

Checker không hash tự động mọi tài liệu architecture/prompt mới. Việc mở rộng validator ở lượt này không sửa script và không tạo bảo đảm cho những lần chạy mặc định sau. Mỗi batch tài liệu phải liệt kê đúng file mới trong kiểm cấu trúc và lưu kết quả.

## 5. Trạng thái cổng và bước tiếp theo

| Cổng | Kết luận audit | Điều kiện tiếp theo |
| --- | --- | --- |
| Recommendation | `DEFER` có cơ sở, vẫn là đề xuất | Người dùng chọn nhu cầu/owner trước task triển khai |
| `DESIGN_COMPLETE` | `NEEDS_FIX` | Sửa DP-F01…04 và audit lại tính nhất quán contract/test/reconcile |
| `READY_FOR_SYNTHETIC_POC` | Lake `NOT_APPLICABLE`; O0 UC-01 `NOT_READY` | Chọn UC-01, scope/công thức test và giao task riêng; C01 cho runtime cô lập |
| `REAL_DATA_APPROVAL` | `BLOCKED` | Q/owner/source/policy/ops tương ứng và bằng chứng kỹ thuật, nghiệp vụ đúng phạm vi |

Bước gần nhất là [prompt correction DP-001](../prompts/CLAUDE_DP001_CORRECTION.md). Không cần người dùng trả lời cả năm câu hỏi để sửa bốn lỗi thiết kế này. Sau correction, ưu tiên application code độc lập vẫn là C01/FND-002 theo master plan; Data Lake không chặn C01. C17/RPT-001 chỉ mở khi use case/công thức/scope được chọn và giao task riêng. BASE approval, ký, hiệu lực, thanh toán và grant người thật giữ ngoài phạm vi.

## 6. Audit lại correction DP-DISC-v1.1 (CHG-027)

**Verdict:** `TECHNICAL_ACCEPTED` cho discovery/spec-only; `DESIGN_COMPLETE` đạt ở phạm vi bộ tài liệu chuẩn bị. `NEEDS_FIX` của CHG-024 chỉ áp dụng cho DP-DISC-v1. Recommendation `DEFER` vẫn là đề xuất, không phải DEC.

- **DP-F01 — đạt:** mục 4.4.1 tách pagination khỏi consistency; API hiện tại chỉ `best_effort`; M2/M3 và snapshot token không mang quyền được nêu rõ; quyền đổi giữa các trang fail closed. V19, V21–V23 bao phủ drift, quyền và export nhất quán, đều `NOT_RUN`.
- **DP-F02 — đạt:** mục 4.4.2 và DC-02 có ma trận version × hash, xác minh/quarantine cho equal-version/different-hash, entity không version, response đến muộn và snapshot có thẩm quyền theo coverage. Không dùng `ingested_at`, `write_date` hoặc thứ tự response làm thứ tự sự thật. V14, V24–V26, V30–V31, đều `NOT_RUN`.
- **DP-F03 — đạt:** source/policy được tách. `_amount_summary` xác nhận unknown-only là `confirmed` có source value; mixed basis là nhiều basis; policy `basis_unknown` giữ riêng. Fixture HD-SIM-07…10 và V27–V29 bổ sung unknown-only, unknown+known, known basis, zero và incomplete. V02–V04/V17/V27–V29 đều `NOT_RUN`.
- **DP-F04 — đạt:** mục 4.5.1 tách L1 retry, L2 immutable observation và L3 content-addressed payload; A→B→A giữ ba observation/hai payload; materialization gắn snapshot/schema/transform/formula. V12, V15, V32–V34 đều `NOT_RUN`.

Kiểm tra độc lập đọc source `_amount_summary`, `_tp_submission_problems`, `_tp_bump`/version guard và đối chiếu 34 dòng V01–V34: đủ dải 1–34, không trùng, tất cả trạng thái `NOT_RUN`. Validator mở rộng trước khi ghi verdict đạt 28 file, 213 link nội bộ, 49 anchor, 156 bảng, 0 lỗi/0 cảnh báo. Snapshot correction 127/127 file giữ cùng digest; không có application code/runtime/database thay đổi.

Một lưu ý **P3, không chặn**: câu “mỗi lần đọc” ở ma trận observation và V34 có thể đọc lẫn response/attempt với accepted observation. RFC triển khai phải ghi rõ retry cùng `extract_batch_id` không tạo observation thứ hai; batch/snapshot mới tạo observation mới theo L2, dù payload dùng lại theo hash. Đây là việc làm rõ implementation contract, không mở lại DP-F01…DP-F04.

Sau audit: lake PoC `NOT_APPLICABLE`, O0 UC-01 `NOT_READY`, `REAL_DATA_APPROVAL` `BLOCKED`; không tạo connector/bucket/pipeline, không đọc dữ liệu thật. C01/FND-002 có thể tiến hành độc lập khi người dùng giao task; C17/RPT-001 cần use case, owner, công thức và scope riêng.
