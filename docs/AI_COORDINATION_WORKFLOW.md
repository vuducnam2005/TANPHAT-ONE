# TANPHAT ONE — Quy trình phiên điều phối và phiên Claude

Tài liệu này bổ sung `AGENTS.md`: phiên hiện tại giữ vai trò điều phối, còn Claude là implementation agent. Không dùng nó để bỏ qua cổng nghiệp vụ hoặc thay `PROJECT_STATUS.md`.

## 1. Vai trò

**Phiên chính:** đọc status/decision/readiness, chọn batch, phát prompt, nhận diff/log, audit source/test/security/scope, kết luận `TECHNICAL_ACCEPTED`, `NEEDS_FIX` hoặc `BLOCKED`, cập nhật kế hoạch và quyết định bước sau. Phiên chính không tự sửa application code trong mô hình làm việc này.

Khi yêu cầu liên quan CRM, Request, Bid, Base, xây dựng hoặc Data Platform, đọc thêm [sổ kiến thức tham khảo và bàn giao](architecture/TP_REFERENCE_RESEARCH_AND_HANDOFF.md). Sổ này chỉ lưu provenance, quan sát và giả thuyết; `PROJECT_STATUS.md` và `DECISIONS.md` vẫn là nguồn trạng thái/quyết định.

Với Request/BASE, đọc [kiến thức nghiệp vụ Request](architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md): phân biệt group/tab/form đã quan sát, actor/quyền chưa xác minh và workflow Proposed-TP theo BIZ-002 H/I. Không map nhãn “đã chấp nhận” thành ký, hiệu lực hoặc tiền đã chi.

**Claude:** làm đúng task/change ID trong prompt, đọc repository instructions, sửa code trong scope, chạy test thật, cập nhật handoff, không commit/push. Claude không tự chốt owner, hạn mức, thuế, ký, hiệu lực, grant người thật hoặc quyết định business chưa được ghi.

**Chủ nghiệp vụ/người dùng:** xác nhận business acceptance, owner/evidence, pilot charter và yêu cầu commit/push/deploy khi cần. Technical test không thay chữ ký hoặc ủy quyền.

## 2. Quy trình một vòng

1. Phiên chính xác định trạng thái hiện tại trong `PROJECT_STATUS.md` và plan; nếu chưa có scope/acceptance thì làm audit/spec-only.
2. Phiên chính gửi một prompt có task ID, change ID, lane, scope, ngoài phạm vi, gate, test và đầu ra.
3. Claude preflight đọc `AGENTS.md`, status, changelog, decisions, architecture; nếu gate thiếu thì trả `BLOCKED` trước khi sửa.
4. Claude chạy `scripts/ai_workflow.py start`, sửa theo model/security/API/frontend/test, cập nhật handoff và chạy `finish/check`.
5. Phiên chính kiểm `git status`, `git diff`, `git diff --check`, test/log, OpenAPI, security, migration và tài liệu. Không xem `finish` là bằng chứng test; không xem Claude tự nhận là nghiệm thu.
6. Phiên chính ghi verdict. `NEEDS_FIX` thì gửi prompt correction chỉ chứa finding; `BLOCKED` thì yêu cầu decision/evidence; `TECHNICAL_ACCEPTED` mới cho phép chọn batch độc lập tiếp.
7. Khi business owner ký đúng scope và ops gate đạt, chuyển trạng thái riêng sang `BUSINESS_ACCEPTED`/`PILOT_READY`. Commit/push/deploy là bước riêng theo chỉ thị người dùng.

## 3. Mẫu prompt triển khai

Đây là khung; phiên điều phối phải thay hết ô trống và gắn đặc tả đủ chi tiết trước khi giao. C01 có [prompt đầy đủ](prompts/CLAUDE_C01_ISOLATED_TEST_RUNTIME.md).

```text
Làm việc trong C:\TANPHAT ONE. Task [TASK-ID], batch [Cxx], lane [M/F/P/O], scope version [VERSION]. Chọn CHG-ID mới chưa dùng. Không commit/push/deploy hoặc sửa odoo/ và addons/.
Đọc AGENTS, status/changelog/workflow/decision, master plan và đặc tả [PATH/SECTION]. Kiểm git status/diff, handoff/checkpoint, runtime. Không setup/upgrade/seed dev để lấy baseline.

Mục tiêu sử dụng: [ACTOR làm được GÌ trong SCOPE].
Quyết định làm căn cứ: [DEC/owner/evidence; phân biệt đã chốt và đề xuất].
State/action/capability/field/file/API/UI phải theo: [SPEC].
Được sửa: [FILES/MODELS/API/ROUTES]. Ngoài phạm vi: [LIST].
Gate: [INPUTS]. Acceptance: [CA DƯƠNG/ÂM/SCOPE/RETRY/RACE cụ thể].
Dữ liệu/môi trường: [FAKE DB/ORIGIN/DATA DIR/ownership].

Nếu thiếu policy bắt buộc hoặc baseline chưa bàn giao, báo BLOCKED cho phần phụ thuộc; không tự đặt default nghiệp vụ. Khi gate đạt, chạy ai_workflow.py start rồi triển khai model/security/API OpenAPI/types/frontend/test. Giữ transaction/version/idempotency/audit; frontend không tự ghi state/tiền/quyền. Không generic RPC bypass API.

Chạy test [LỆNH/TARGET], chỉ nhận test thực đã chạy. Báo pass/fail/skip và log an toàn. Sửa fail trong scope; không mở feature khác. Cập nhật status/changelog/spec bị ảnh hưởng, diff --check, ai_workflow.py finish đúng CHG-ID và check. Báo output dùng được, files/schema/API/security, migration, test evidence, runtime cleanup, giới hạn và next action.
```

## 4. Mẫu prompt audit/spec-only

```text
Làm việc trong C:\TANPHAT ONE nhưng KHÔNG sửa code, không sửa database, không start/upgrade runtime và không commit/push.

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/CHANGELOG.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md và tài liệu của [TASK-ID].

Audit/spec-only cho [CHANGE-ID/TASK-ID]: [mục tiêu]. Kiểm tra source hiện tại, diff chưa bàn giao, model/state/capability/API/frontend/test và gate RFC. Không tự chốt nghiệp vụ còn thiếu.

Đầu ra bắt buộc:
1) baseline và file/model/API đã có;
2) hành vi hiện tại có bằng chứng file/test;
3) gap với mục tiêu, severity, reproduction/expected;
4) RFC ngắn cho batch tiếp theo: scope, state/action, actor/capability/scope, field/file policy, OpenAPI, UI, migration, test và ngoài phạm vi;
5) điều kiện Ready for Test Code hoặc lý do BLOCKED;
6) prompt triển khai tiếp theo, không chứa việc ngoài scope.

Chỉ dùng dữ liệu giả trong mô tả; không in secret. Nếu phát hiện source/status lệch, dừng và ghi rõ.
```

## 5. Mẫu prompt correction

```text
Làm việc trong C:\TANPHAT ONE. Không mở feature mới và không commit/push.
Đọc lại AGENTS.md, status, handoff của [CHANGE-ID] và diff hiện tại.

Sửa đúng các finding sau, giữ nguyên scope/state/capability/API ngoài phạm vi:
- [FINDING: file/dòng, cách tái hiện, hành vi mong đợi]

Trước khi sửa phải tái hiện bằng test. Sau khi sửa thêm regression có ý nghĩa, kiểm rollback/no-side-effect, scope company/project/department, audit/version/idempotency/retry và DTO/file không lộ dữ liệu nếu finding liên quan. Chạy lại test liên quan, cập nhật handoff/status/changelog và báo file, lệnh, kết quả, gap. Nếu finding cần quyết định nghiệp vụ, trả BLOCKED thay vì tự đặt default.
```

## 6. Phiên chính không nhận thay thế

- Ảnh chụp UI không thay test API/ORM/security.
- `0 failed` không thay kiểm tra log có đúng database và đúng test scope.
- File report tự tạo không thay assertion đã chạy.
- Mock E2E không thay live Odoo; live fixture không thay UAT.
- Technical acceptance không thay business acceptance, thẩm quyền ký hoặc pilot charter.
- Claude báo “đã hoàn tất” không thay diff, test và review độc lập.
