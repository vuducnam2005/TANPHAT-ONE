# Prompt Claude — Sửa đặc tả DP-001 sau audit

Copy nội dung sau vào phiên Claude thực hiện. Đây là task tài liệu, không phải prompt triển khai Data Lake.

```text
Làm việc trong C:\TANPHAT ONE. Task DP-001 correction/spec-only sau audit CHG-20261029-024. Chọn CHG-ID mới theo CHANGELOG; không tái dùng ID. Phiên chính đã audit recommendation DEFER là có cơ sở, nhưng DESIGN_COMPLETE=NEEDS_FIX. Chỉ sửa đặc tả; không mở feature hoặc runtime.

Đọc theo AGENTS.md: PROJECT_STATUS, AI_CHANGE_WORKFLOW, CHANGELOG mục mới nhất, ROADMAP, DECISIONS; sau đó đọc:
- docs/architecture/TP_DATA_PLATFORM_DP001_AUDIT.md
- docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md
- docs/architecture/TP_DATA_PLATFORM_PREPARATION_PLAN.md
- docs/prompts/CLAUDE_DATA_PLATFORM_DISCOVERY.md

Preflight: git status, ai_workflow.py check và checkpoint. Giữ nguyên thay đổi đang có, không reset/clean/stash. Nếu checkpoint khác còn dở thì resume/đánh giá theo workflow, không xóa. Dùng scripts.ai_workflow.snapshot đúng phạm vi maintained trước và sau lượt; không tự dựng tập 119 file rồi gọi đó là exact checker scope. Không đọc secrets hoặc data runtime.

Được sửa:
- docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md
- docs/PROJECT_STATUS.md, docs/CHANGELOG.md, docs/ROADMAP.md
- kế hoạch chuẩn bị chỉ khi thật sự cần sửa mâu thuẫn, giải thích lý do
Giữ báo cáo audit CHG-024 làm bằng chứng của phiên chính; không tự sửa verdict của phiên chính thành accepted. Không sửa DECISIONS để tự ghi người dùng đã phê chuẩn recommendation/use case/công nghệ.

Ngoài phạm vi: custom_addons, frontend, OpenAPI, scripts trong Git, ops/config, schema, DB, application code/test. Không start/upgrade/seed Odoo, không đọc database/NAS/Excel/filestore thật, không dựng pipeline/bucket/connector/addon, không OCR/embedding/upload, không chạy PoC hoặc application tests, không commit/push/deploy.

Sau preflight chạy ai_workflow.py start trước lần sửa đầu.

Sửa đúng bốn finding DP-F01…DP-F04; đọc nguồn để tái kiểm, không chỉ sửa câu chữ rời rạc:

1) Snapshot nhất quán:
- Keyset chỉ giải quyết pagination; không đủ để bảo đảm point-in-time snapshot xuyên request.
- Đặc tả rõ snapshot token/materialized export từ một transaction đọc nhất quán hoặc cơ chế khác có bảo đảm được chứng minh. Không mặc định keyset tương đương snapshot.
- Liệt kê lại ID/version/hash chỉ là best effort nếu nguồn còn đổi ngoài version. Không publish một batch như consistent khi chưa đủ bằng chứng.
- Đồng bộ mục 4.4, R05, tiền đề 9.1 và ca kiểm chứng: cùng ID nhưng value/relation thay đổi giữa các trang; assignment/grant đổi khi đang đọc. Không thiết kế cơ chế cấp quyền bypass Odoo.

2) Same-version/different-hash:
- Bảng hành vi higher/lower/equal version × same/different hash; bao gồm entity không có version, thay đổi ngoài workflow và response đến muộn.
- Dùng nguồn/snapshot có thẩm quyền để xác minh; chưa có thứ tự tin cậy thì quarantine, không cập nhật theo ingested_at/write_date/thứ tự response.
- Bản authoritative snapshot mới có thể thay hiện trạng dù version không tăng, nếu điều kiện/source coverage được xác định; không bỏ thay đổi hợp lệ. Giữ lịch sử quan sát.
- Đồng bộ DC-02, temporal/version rules, reconcile, risk và test specs. Không sửa model để tăng version trong lượt này.

3) tax_basis=unknown:
- Đọc _amount_summary ở custom_addons/tp_contract/models/tp_contract_revision.py và TAX_BASES ở tp_contract_line.py.
- Mô tả observed-static đúng: all confirmed cùng unknown vẫn có source status confirmed và source value; mixed_basis khi nhiều basis; missing/unconfirmed khác zero.
- Nếu đề xuất chặn tổng báo cáo chính thức khi basis unknown, tách source_status/source_value với report_status/policy_value và ghi proposed, gate Q4/Q13. Không tự chốt policy công ty.
- Reconcile source với API; acceptance policy kiểm riêng, không bắt một giá trị vừa bằng API vừa null do policy.
- Thêm ca fake-only vào đặc tả: unknown-only, unknown+known, known thống nhất, confirmed zero, missing/unconfirmed. Giữ NOT_RUN.

4) Replay/dedup:
- Tách retry trong batch, immutable observation và payload storage có thể tái sử dụng theo hash.
- Khóa env/entity/id/hash toàn cục không được làm mất observation A→B→A ở snapshot/thời điểm mới.
- Curated materialization gắn snapshot và schema/transform/formula version thích hợp; transform v2 phải tạo/rebuild output có lineage, không dùng output v1 chỉ vì input hash giống.
- Bổ sung ca cùng batch retry, A→B→A khác batch, transform v1/v2, lỗi/quarantine/replay có kiểm soát. Đồng bộ envelope/DC-06/lineage/reconciliation và V12/V15. Tất cả NOT_RUN.

Giải trình bằng chứng:
- Discovery cũ ghi snapshot 119 file, checker exact hiện là 127 file. Nếu artifact trước DP-001 còn thì so exact scope/list/hash và giải thích file chênh lệch; nếu không có, ghi rõ không tái chứng minh được toàn bộ scope trước DP-001. Không tạo bằng chứng hồi tố.
- Dùng snapshot trước correction 127 file (hoặc count thực tế do checker trả) để chứng minh chính lượt correction không đổi code. Giới hạn checker: architecture/prompt mới không được hash tự động.
- Validator tài liệu mặc định .local/ctr002a-verify/docs_validation.py chưa chứa discovery. Khi kiểm, mở rộng NAMES tại runtime (không sửa scripts trong Git) cho mọi file mới/bị ảnh hưởng, kể cả discovery và audit/prompt. Ghi danh sách/số file, tables/links, errors và output thật. Nếu helper không còn, dùng kiểm tra scratch tương đương và nêu rõ.

Bàn giao:
- Giữ DEFER là recommendation đề xuất; không gọi là DEC, không tự chọn use case/owner/vendor/cloud.
- Sau sửa chỉ tự đánh giá PROPOSED_COMPLETE chờ phiên chính audit; không ghi technical/business acceptance đã đạt.
- Lake PoC vẫn NOT_APPLICABLE; O0 UC-01 chưa tự mở; REAL_DATA_APPROVAL vẫn BLOCKED. C01 độc lập không bị chặn bởi Data Lake.
- Cập nhật status/changelog/roadmap đúng scope và version discovery; mapping từng finding → mục sửa → ca expected → trạng thái NOT_RUN.
- Kiểm UTF-8, fence, bảng, file link/anchor, whitespace file untracked và git diff --check.
- So exact maintained snapshot trước/sau. Chạy finish --change-id CHG-ID-mới với lệnh/kết quả thực đã chạy rồi check.
- Báo baseline, file sửa, cách đóng từng finding, số kiểm chứng tài liệu, hash/count maintained, giới hạn bằng chứng lịch sử, runtime/database không đụng và next action là audit lại. Không báo V01… hoặc các ca mới đã pass vì chưa chạy ứng dụng.
```
