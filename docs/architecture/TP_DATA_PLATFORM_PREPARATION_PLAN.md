# TANPHAT ONE — Kế hoạch chuẩn bị Data Platform / Data Lake

**Phiên bản:** DP-PLAN-v1 — 29/10/2026

**Trạng thái:** đề xuất chuẩn bị, chưa phê duyệt triển khai Data Lake và chưa thay đổi source/runtime/database.
**Mục đích:** cho Claude khảo sát, lập đặc tả và kiểm tra điều kiện; quyết định triển khai sẽ được đưa ra sau khi có use case, owner, chất lượng dữ liệu và chi phí vận hành rõ.

## 1. Kết luận định hướng

Nên **thiết kế khả năng mở rộng dữ liệu từ bây giờ** và chọn giải pháp sau discovery. Odoo giữ giao dịch và quyền đang quản lý; BASE vẫn là nguồn quyết định phê duyệt chính thức, còn posting/payment/reconciliation thuộc nguồn kế toán được xác nhận. Data platform chỉ lưu bản dẫn xuất cho phân tích, đối chiếu, lịch sử và AI khi được cấp phép; không ghi ngược trạng thái nghiệp vụ hoặc tạo nguồn kế toán/phê duyệt thứ hai.

Một phương án cần so sánh là **lakehouse-lite** dưới đây. Discovery cũng phải đánh giá giải pháp báo cáo hiện tại hoặc analytics nhỏ hơn; chưa mặc định cần lake hay PoC lake:

```text
Odoo / nguồn được phép
      │  API/export/outbox có kiểm soát, chỉ đọc
      ▼
Landing/Raw bất biến (source, batch, hash, received_at)
      ▼
Validated (mapping, chất lượng, quyền, lineage, reconciliation)
      ▼
Curated data products / marts theo use case
      ▼
TP Dashboard / BI / AI query qua lớp API có kiểm quyền
```

Object storage, Parquet, catalog, warehouse/query engine là **phương án cần đánh giá**, chưa phải quyết định công nghệ. Không thêm Kafka, Spark, Airflow, lakehouse catalog hoặc service riêng chỉ vì tên “Data Lake”.

## 2. Ranh giới với hệ thống hiện tại

| Thành phần | Vai trò | Không được làm |
| --- | --- | --- |
| Odoo/PostgreSQL vận hành | Nguồn giao dịch và quyền; xử lý action/transaction | Không biến lake thành nguồn ghi hoặc nguồn quyết định thay Odoo |
| Filestore/TP Documents | Tệp/hồ sơ gốc và metadata kiểm quyền | Không copy file nhạy cảm vào raw khi chưa có classification/retention/owner |
| Landing/Raw | Bản trích xuất có version/hash và nguồn | Không gọi dữ liệu raw là số liệu chính thức; không cho người dùng query trực tiếp |
| Validated | Chuẩn hóa mã, thời gian, tiền, trạng thái, scope và lỗi | Không âm thầm sửa dữ liệu hoặc biến thiếu thành 0 |
| Curated/mart | Dataset theo KPI/use case, có công thức/as-of/known-at/freshness | Không tạo KPI chưa có owner/công thức hoặc bỏ qua quyền project/company |
| React/API | Trình bày và truy vấn được cấp phép | Không gọi thẳng object storage/raw hoặc tính tiền trong browser |

`BASE`, kế toán, Excel, NAS, Survey, Design, HR và nguồn ngoài hiện là **nguồn cần xác minh**, không được coi là đã có connector. Tài liệu mẫu/fixture không phải dữ liệu production.

## 3. Giai đoạn chuẩn bị không code

### DP-01 — Discovery và inventory

Claude lập inventory từ source hiện có, không kết nối/đọc dữ liệu thật:

- Odoo models/fields/relations hiện có: company, user, department, project, assignment, contract, revision, line, amount, approval reference, submission, audit, outbox, document/attachment.
- API/DTO/query hiện có và field nào bị che theo `financial_read`, company/project/department.
- Các nguồn tương lai: BASE, kế toán Odoo, Excel, NAS/DMS, Survey, Design, HR; đánh dấu `observed`, `proposed` hoặc `unknown`.
- Chủ dữ liệu theo vai trò, độ mới kỳ vọng, kích thước/tốc độ tăng ước tính và tính nhạy cảm.

Dung lượng, số file/record, tần suất thay đổi, ngân sách, người vận hành và mục tiêu ưu tiên hiện chưa có số liệu xác nhận. Ghi `unknown` kèm cách đo/người cung cấp; không crawl NAS hoặc lấy số đếm từ database thật trong batch này. Kết quả đọc source chỉ là quan sát tĩnh, không chứng minh module đã cài hay luồng đã chạy.

**Đầu ra:** data source inventory có source-of-truth, owner, identifier, update/delete semantics, sensitivity, retention cần xác minh và blocker.

### DP-02 — Use case và data product catalogue

Không bắt đầu bằng công nghệ. Lập tối đa ba use case ứng viên; phân biệt actor/owner theo vai trò đề xuất với người được công ty chỉ định. Ví dụ:

1. Tiến độ dự án theo project/WBS và thời điểm biết dữ liệu.
2. Hợp đồng, phạm vi và thay đổi theo revision/as-of.
3. Đối chiếu request–acceptance–accounting khi các module đó đã có dữ liệu hợp lệ.

Mỗi use case phải ghi actor, câu hỏi, dataset, KPI/công thức, tần suất, độ trễ chấp nhận, quyền, nguồn, acceptance sample và cách xử lý thiếu dữ liệu. Không lấy “dashboard toàn công ty” làm use case đủ cụ thể.

Người dùng chưa chọn giữa báo cáo liên nguồn, hồ sơ/bản vẽ và AI tra cứu. Claude phải so sánh ba mục tiêu này, đề xuất một use case nhỏ có giá trị; không ghi đã được người dùng ưu tiên. Nếu chọn hồ sơ/AI, đánh giá TP Documents/DMS/search trước: lưu nhiều file hoặc có vector index không tự thành Data Lake. Chưa OCR/embedding/upload tài liệu trong bước chuẩn bị.

### DP-03 — Data contract và semantics

Chốt đề xuất cho từng dataset:

- business key và Odoo ID; mapping external code có provenance;
- `event_time`, `known_at`, `ingested_at`, `effective_from/to`, `source_version`, `record_version`;
- `company_id`, `project_id`, `department_id`, scope grant;
- decimal/currency/rounding; `null`, `0`, negative, unconfirmed, disputed và missing source giữ khác nhau;
- insert/update/delete/correction/reversal semantics; snapshot theo ngày vs event lịch sử;
- lineage source → raw → validated → curated → metric; quality rules và reconciliation;
- schema evolution/versioning, backfill và replay.

Ghi rõ grain của dataset (mỗi dòng đại diện project, contract, revision, line hay event), `source_system/source_env/entity/source_id`, extract batch/snapshot/schema/transform version, content hash và cursor/watermark. Đặc tả snapshot nhất quán, pagination ổn định, late/out-of-order events, tombstone/delete, retry/replay không trùng và reconciliation theo đúng grain; không lấy thời điểm ingest mới hơn làm bằng chứng bản nguồn mới hơn. Không join lệch revision hoặc nhân tổng tiền do quan hệ một-nhiều. Không cộng nhiều currency khi chưa có conversion policy đã xác nhận.

### DP-04 — Quyền, bảo mật và vòng đời

Đặc tả riêng cho data platform:

- classification: public/internal/confidential/financial/personal/legal;
- row/column/file access theo company/project/department và grant hiện hành;
- áp scope **trước** join/aggregate/grouping và kiểm actor metadata project A nhưng financial project B; tổng hợp không được suy scope từ một record đã lọc thiếu;
- `financial_read` không tự cấp `financial.export`, share, download hoặc quyền xem raw; export/share là capability/policy riêng có audit;
- Odoo revoke/expiry phản ánh vào lớp truy vấn; không cấp lake access rộng hơn nguồn;
- encryption at rest/in transit, service accounts, secret rotation, audit query/export;
- retention, deletion, legal hold, backup/restore và xử lý bản sao raw;
- không chứa credential, cookie, token, UNC path hoặc số tiền trong log/error không được phép;
- data residency và nơi đặt object storage/replica là câu hỏi cần owner xác nhận.

Tách **độ mới dữ liệu** khỏi **độ mới quyền**. Refresh dữ liệu mỗi ngày không được làm revoke tài chính trễ một ngày: lớp truy vấn phải kiểm quyền hiện tại hoặc có cơ chế invalidation được chứng minh; chưa lấy được quyền thì từ chối truy cập dữ liệu nhạy cảm. Xét cả cache, export link, share, audit và bản dẫn xuất AI. Không tuyên bố thu hồi được bản người dùng đã tải xuống; kiểm soát xuất/lưu theo policy riêng.

Raw có lịch sử/bất biến trong khoảng lưu được phép, không đồng nghĩa giữ vô thời hạn. Đặc tả xử lý deletion/legal hold/expiry trên raw, validated, curated, index, cache và backup, giữ audit hợp lệ. Data Lake không thay backup có khả năng phục hồi Odoo; mỗi hệ thống cần runbook phục hồi riêng.

### DP-05 — Đánh giá đường nạp dữ liệu

So sánh theo tải và độ mới, không chọn trước:

| Cách nạp | Khi dùng | Rủi ro cần kiểm |
| --- | --- | --- |
| Scheduled API/export | Ít nguồn, nhu cầu giờ/ngày | phân trang, cập nhật/xóa, retry, đối soát, không làm tải Odoo |
| Read replica/snapshot | Query lớn, cần tách tải | replica lag, quyền bản sao, backup và chi phí |
| Outbox/event | Cần lịch sử action gần thời gian thực | event schema, delivery/replay, ordering, retention |
| CDC | Nhiều bảng/tải lớn và cần thay đổi đầy đủ | delete semantics, schema migration, quyền DB và vận hành phức tạp |

Ban đầu đánh giá API/export có kiểm soát và outbox hiện có; **không coi outbox hiện có là change feed đầy đủ** vì phải kiểm coverage action/entity/delete, payload hay reference, bootstrap snapshot, cursor/offset handoff, ordering, retry và replay. Không đọc PostgreSQL production trực tiếp bằng script tự phát. `write_date` đơn lẻ không đủ chứng minh đồng bộ đầy đủ khi có delete/correction/hồi tố.

### DP-06 — Lập kế hoạch PoC dữ liệu giả, chưa thực thi

Đặc tả PoC tương lai chỉ dùng actor/project/contract fixture và dữ liệu tổng hợp. PoC phải theo phương án được chọn: analytics-first dùng staging/export → curated/report; chỉ lakehouse-lite mới dùng raw object storage → validated → curated. Nếu recommendation là `DEFER` hoặc report hiện có đủ, ghi rõ PoC lake là `NOT_APPLICABLE`. Mỗi ca có input, expected output, kiểm quyền, cách đo và cleanup; không tạo pipeline/bucket hoặc chạy PoC trong DP-001:

- đẩy một dataset từ Odoo test vào raw/validated/curated;
- chạy một KPI có công thức rõ;
- kiểm replay không trùng, correction không xóa lịch sử, null/0/unknown không biến dạng;
- kiểm source lineage, checksum, freshness, reconciliation và scope reader/financial reader;
- mô phỏng revoke/expiry, không lộ số tiền/file sau request kế tiếp;
- hỏng một batch phải quarantine/retry, không ghi ngược Odoo.

PoC không phải pilot, không import Excel thật và không chứng minh dữ liệu công ty đã đúng.

## 4. Kiến trúc tối thiểu nên đánh giá

Claude phải so sánh ít nhất hai phương án:

1. **Analytics-first:** Odoo API/export → PostgreSQL analytics hoặc read replica → curated marts. Phù hợp khi dữ liệu có cấu trúc, ít nguồn, cần triển khai nhanh.
2. **Lakehouse-lite:** Odoo/API + nguồn được phép → object storage raw Parquet → catalog/validated → query/curated marts. Phù hợp khi cần lịch sử, nhiều nguồn, file lớn hoặc replay.

Đánh giá theo chi phí lưu trữ/query, độ mới, vận hành Windows/Linux, backup/restore, quyền project/finance, schema evolution, backfill, observability, team skill và khả năng bỏ phương án mà không khóa Odoo. Chỉ khuyến nghị full lakehouse khi analytics-first không đáp ứng use case đã chứng minh.

## 5. Cổng phê duyệt trước khi triển khai

Tách ba cổng để chuẩn bị không bị hiểu là đã được triển khai:

| Cổng | Đủ khi | Ý nghĩa |
| --- | --- | --- |
| DESIGN_COMPLETE | Inventory/nguồn, use case ứng viên, contracts, security/options, gap và kế hoạch PoC có truy vết; unknown có owner/impact | Chỉ xác nhận tài liệu đủ để review; không phải đã chốt nhu cầu/công nghệ |
| READY_FOR_SYNTHETIC_POC | Scope/data giả, expected tests, target/ownership, no-writeback, quyền và cleanup đủ rõ; người dùng giao task PoC riêng | Cho phép một thử nghiệm cô lập theo task; không chờ các Q công ty không liên quan |
| REAL_DATA_APPROVAL | Owner/use case/quyền/retention/source và business/ops tương ứng được xác nhận; PoC đạt | Mới xem xét dữ liệu thật và môi trường theo phạm vi được giao |

Các điều kiện cần xem xét trước thử nghiệm/vận hành có dữ liệu thật:

1. use case cụ thể, owner sử dụng và quyết định giá trị;
2. source inventory và source-of-truth được xác nhận;
3. data contract, KPI, freshness và reconciliation sample;
4. classification, row/column/file policy, retention/deletion/legal hold;
5. phương án ingestion/stack, chi phí và người vận hành;
6. PoC dữ liệu giả đạt, không ghi ngược Odoo và không lộ tiền/file;
7. backup/restore, monitoring, retry/quarantine, incident và rollback;
8. business owner/Q2/Q14 xác nhận phần chạm quyền, hồ sơ và vận hành.

## 6. Điều không làm trong bước chuẩn bị

- Không tạo addon `tp_datalake` rỗng hoặc bảng lake trong database Odoo.
- Không cài Spark/Kafka/Airflow/MinIO/ClickHouse chỉ để “đặt nền” khi chưa có PoC và owner.
- Không đọc trực tiếp PostgreSQL production, NAS, Excel thật hoặc filestore thật.
- Không copy toàn bộ financial/HR/legal data sang một bucket chung.
- Không cho React truy cập raw bucket hoặc query engine không qua API/policy.
- Không dùng Data Lake để che thiếu owner, workflow, Q2, Q4/Q6/Q8 hoặc dữ liệu nguồn chưa đối soát.

## 7. Kết quả cần bàn giao sau DP-01…DP-06

Claude phải bàn giao `source_inventory`, `use_case_catalogue`, `data_contracts`, `security/retention matrix`, `architecture options`, `PoC plan`, `risk/gap register` và recommendation `DEFER / ANALYTICS_FIRST / LAKEHOUSE_LITE`. Mỗi kết luận phải ghi căn cứ `observed static`, `runtime evidence` (chỉ khi có log đã kiểm), `proposed` hoặc `unknown`; không ghi “đã sẵn sàng Data Lake” nếu mới có tài liệu. Recommendation có phạm vi và giả định; `DEFER` nghĩa trì hoãn triển khai, vẫn có thể hoàn tất thiết kế.

Các bảng tối thiểu phải có:

| Đầu ra | Cột/nội dung bắt buộc |
| --- | --- |
| Source inventory | ID, source/model/API/file tham chiếu, source-of-truth, đã có/dự kiến, grain/key/scope, owner vai trò, sensitivity, volume/freshness unknown, update/delete/correction, evidence và gap |
| Use case | ID, actor/owner, câu hỏi/quyết định, nguồn đã có/còn thiếu, metric/công thức, latency mục tiêu, quyền, giá trị/cost giả định, acceptance và trạng thái đề xuất |
| Contract | Dataset/grain/key, field/type/nullable/decimal/currency, scope, version/time, change/correction/delete/replay, lineage và quality/reconcile rules |
| Options | Report hiện có/analytics/lakehouse-lite, nguồn/budget/latency/skill giả định, chi phí storage/compute/egress/ops/backup, lợi/hại, nguồn chứng cứ và điều kiện chọn |
| PoC cases | ID, input giả, thao tác dự kiến, expected output/metrics, ca âm và bằng chứng sẽ thu; ghi NOT_RUN |
| Risk/gap | ID, severity, owner đề xuất, câu hỏi/giả định, phần bị chặn, điều kiện xử lý và gate liên quan |

Không tự báo giá vendor hoặc hứa hiệu năng. Có thể lập low/base/high scenario nhưng phải ghi rõ số giả định và mục cần đo. Cuối báo cáo gom tối đa năm câu hỏi quan trọng nhất cho người dùng, xếp theo ảnh hưởng; tiếp tục phần độc lập khi còn thiếu đáp án.

Prompt thực hiện bước chuẩn bị nằm ở [CLAUDE_DATA_PLATFORM_DISCOVERY.md](../prompts/CLAUDE_DATA_PLATFORM_DISCOVERY.md). Phiên chính sẽ review diff/tài liệu, kiểm link/bảng, đối chiếu model/API/security và kết luận trước khi cho phép PoC hoặc code ingestion.
