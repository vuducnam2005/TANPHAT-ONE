# Prompt Claude — DP-001: chuẩn bị Data Platform / Data Lake

Đây là prompt **phân tích và thiết kế, không code ứng dụng**. Chỉ giao prompt này khi muốn Claude lập bộ đặc tả Data Platform.

```text
Làm việc trong C:\TANPHAT ONE. Task DP-001/Data Platform Discovery, change ID mới theo CHANGELOG. Đây là làn tài liệu/spec-only: không sửa application code, không tạo addon, không sửa schema/runtime/database, không start/upgrade/seed Odoo, không đọc database/NAS/Excel/filestore thật, không commit/push.

Đọc trước: AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/CHANGELOG.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/architecture/TP_DATABASE_DESIGN.md, docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md, docs/architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md, docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md và docs/architecture/TP_DATA_PLATFORM_PREPARATION_PLAN.md. Chạy git status và ai_workflow.py check. Nếu có checkpoint khác đang làm dở, source/status lệch, hoặc không xác định được baseline, trả BLOCKED và không sửa.

Mục tiêu: khảo sát khả năng chuẩn bị Data Platform/Data Lake cho TANPHAT ONE trong khi Odoo vẫn là nguồn sự thật. Không được tự kết luận phải dùng lake, không chốt công nghệ, không mở pilot và không biến tài liệu mẫu thành dữ liệu production.

Phạm vi được phép: chỉ các tài liệu architecture/analysis, prompt/spec được nêu trong kế hoạch và PROJECT_STATUS/CHANGELOG/ROADMAP nếu cần bàn giao. Không đổi custom_addons, frontend/src, OpenAPI, scripts runtime hoặc database. Nếu cần minh họa, dùng dữ liệu giả và ví dụ đã khử; không in credential, file path nhạy cảm, giá trị hợp đồng thật hoặc UNC/NAS path.

Thực hiện lần lượt:
1. Inventory source hiện có bằng cách đọc model, field, relation, API/DTO, capability và test trong repository; ghi source-of-truth, dataset grain/business key/Odoo ID, update/delete/correction semantics, owner theo vai trò, sensitivity, freshness và gap. Không kết nối DB để lấy dữ liệu. Đọc code không chứng minh runtime/module đã cài; không ghi volume/performance/chi phí hay owner là sự thật khi chỉ có giả định. Odoo quản lý giao dịch, BASE là nguồn quyết định chính thức, nguồn kế toán đã xác nhận giữ posting/payment/reconciliation.
2. Inventory nguồn tương lai (BASE, Accounting, Excel/NAS/DMS, Survey, Design, HR), đánh dấu observed/proposed/unknown; không giả định connector hoặc module Odoo đã cài.
3. Lập tối đa 3 use case/data products ứng viên có actor/owner vai trò đề xuất, câu hỏi, KPI/công thức, dataset, freshness/latency, scope quyền, acceptance sample và cách xử lý missing/disputed. Ưu tiên báo cáo/hồ sơ/AI chưa được người dùng chọn: so sánh và đề xuất, không tự ghi accepted. Đánh giá DMS/search/report hiện có nếu chúng đủ mục tiêu. Không dùng “dashboard toàn công ty” làm use case.
4. Lập data contract: grain, identifiers/source environment/batch/snapshot/schema/transform versions và hash, company/project/department scope, event_time/known_at/ingested_at/effective dates, version, decimal/currency/rounding, null/0/negative/unconfirmed/missing, snapshot/pagination consistency, late/out-of-order, tombstone/delete/correction/replay, lineage, schema evolution và reconciliation. Chặn join nhân tiền/nhầm revision; không cộng nhiều currency khi chưa có policy.
5. Lập security/retention matrix cho metadata/financial/personal/legal/file; tách data freshness khỏi authorization freshness, Odoo grant/revoke/expiry phải được kiểm khi query; quyền không lấy được thì fail closed với dữ liệu nhạy cảm. Áp scope trước join/aggregate/grouping; kiểm ca user xem metadata project A nhưng chỉ có tiền project B, không để tổng tiền A lộ qua aggregate. `financial_read` không suy ra `financial.export`, share hoặc download; export/share là policy/capability riêng. Raw không truy cập trực tiếp. Xét cache/export/share/AI index và retention/deletion/legal hold ở mọi lớp và backup; không hứa thu hồi bản đã tải. Encryption, service account, audit, backup/restore và residency là gap nếu chưa có căn cứ. Không coi lake là backup Odoo.
6. So sánh tối thiểu: (A) API/export theo lịch → analytics Postgres/replica/curated marts; (B) lakehouse-lite raw object storage/Parquet → validated → curated. Chỉ đánh giá Kafka/Spark/CDC nếu use case chứng minh. Đối với outbox hiện có, kiểm coverage action/entity/delete, payload/reference, bootstrap snapshot, cursor/offset handoff, ordering, retry/replay; không coi outbox là change feed mặc định. Ghi chi phí, vận hành, freshness, scale, replay, delete, security, backup, rollback và skill.
7. Lập kế hoạch PoC dữ liệu giả theo recommendation: analytics-first dùng staging/export → curated/report; lakehouse-lite mới dùng raw→validated→curated; DEFER hoặc report hiện có đủ thì đánh dấu PoC lake NOT_APPLICABLE. Một dataset hợp đồng/project, một KPI, replay/dedup/correction, lineage/checksum/freshness/reconciliation, scope reader/financial reader/revoke; không thực thi PoC, chỉ đặc tả kiểm chứng.
8. Lập risk/gap register và recommendation đúng một trong DEFER, ANALYTICS_FIRST hoặc LAKEHOUSE_LITE với scope/giả định; có thể defer triển khai và vẫn hoàn tất thiết kế. Nêu riêng DESIGN_COMPLETE, READY_FOR_SYNTHETIC_POC và REAL_DATA_APPROVAL. Recommendation là đề xuất, không là DEC đã được người dùng xác nhận. Gom tối đa 5 câu hỏi ưu tiên cho người dùng; không dừng phần độc lập chỉ vì thiếu volume/budget chưa khảo sát.

Tạo/cập nhật đúng các file bàn giao được phép:
- docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md (inventory, use cases, data contracts, options, recommendation, risks/gates);
- docs/architecture/TP_DATA_PLATFORM_PREPARATION_PLAN.md chỉ khi phát hiện gap cần hiệu chỉnh, không xóa quyết định người dùng;
- docs/PROJECT_STATUS.md, docs/CHANGELOG.md, docs/ROADMAP.md nếu trạng thái kế hoạch thay đổi.

Không tạo `tp_datalake`, không chọn nhà cung cấp/cloud, không thêm pipeline, bucket, connector, model hoặc API, không chạy OCR/embedding/upload tài liệu hoặc PoC. Mỗi bảng có cột nguồn/căn cứ và trạng thái observed-static/runtime-evidence/proposed/unknown. Điền đủ các bảng tối thiểu trong mục 7 của kế hoạch; test cases ghi NOT_RUN. Giữ Q2/Q4/Q6/Q8/Q11/Q12/Q13/Q14 làm cổng nếu liên quan. Phân biệt technical/data design với business acceptance.

Kiểm tra cuối: link heading/file, bảng Markdown, fence, UTF-8, git diff --check; xác nhận maintained application code không đổi bằng snapshot. Dùng ai_workflow.py start trước sửa tài liệu, finish/check với CHG-ID mới. Không chạy application tests vì không đổi code; không báo “Data Lake đã triển khai”.

Báo cáo cuối: baseline; files/docs; nguồn và use case; phương án đã so sánh; recommendation; gate/blocker; kiểm tra thực chạy; maintained code/runtime/database unchanged; next action. Nếu thiếu căn cứ, ghi UNKNOWN/BLOCKED và không tự đặt mặc định.
```
