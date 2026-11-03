# Prompt Claude — AUTH-002 slice 1: thông báo đăng nhập trên React

Copy nguyên prompt dưới đây vào phiên Claude khi người dùng giao AUTH-002 slice 1. Slice này chỉ sửa frontend React; không cài addon, không đổi Odoo, không mở người dùng thật.

```text
Làm việc trong C:\TANPHAT ONE. Task AUTH-002 slice 1 (React), làn F, scope version AUTH-002-SPEC v0.6, trạng thái READY_FOR_TEST_CODE do người dùng chuyển ngày 29/10/2026. Đọc CHANGELOG để chọn CHG-YYYYMMDD-NNN mới chưa dùng theo ngày hiện tại; không ghi đè change ID cũ. Không commit, không push, không deploy, không sửa odoo/ hoặc addons/, không dùng dữ liệu hay người dùng thật.

Đọc trước: AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, mục mới nhất của docs/CHANGELOG.md, docs/ROADMAP.md, docs/DECISIONS.md (DEC-012), docs/AI_COORDINATION_WORKFLOW.md, docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md, docs/architecture/TP_READY_FOR_CODE_GATE.md và toàn bộ docs/architecture/TP_AUTH002_LOGIN_SPEC.md, nhất là mục 2, 4, 5.1, 6, 7, 9, 10 và 10.2. Đọc source frontend/src/features/auth/, frontend/src/shared/api/client.ts, client.test.ts, session.tsx, frontend/src/app/providers.tsx, frontend/src/app/shell/AppShell.tsx, frontend/tests/e2e/login.spec.ts và projects.spec.ts. Chạy git status, scripts/ai_workflow.py check và scripts/dev.ps1 status. Working tree đang có thay đổi chưa commit của các batch trước: giữ nguyên, không reset/clean/stash, không stage. Nếu source lệch đặc tả (dòng hoặc hàm được trích đã đổi) hoặc còn checkpoint của batch khác, báo sai lệch trước khi sửa.

Mục tiêu duy nhất: trang React /work/ báo đúng tình huống — bị khóa tạm khác với sai mật khẩu, hết phiên, đã đăng xuất — và hoàn thiện các chi tiết nhỏ, theo L01–L03, L05–L07 và L08 cho năm khóa cooldown, credentials, expired, signed_out, caps_lock. Session, quyền và 2FA vẫn do Odoo xử lý theo DEC-012.

Phải theo đặc tả:
- L01: error.data.name === 'odoo.exceptions.AccessDenied' và error.data.arguments đúng bằng ['Access Denied'] → credentials; AccessDenied với arguments khác → cooldown; mọi trường hợp khác giữ xử lý hiện có (HTTP 429 → rate_limit, còn lại → connection). Không so khớp câu cooldown. Không hiển thị hay log data.message, data.arguments, data.debug.
- L02: thông báo expired chỉ hiện khi tab này đã có session hợp lệ rồi nhận 401. Cờ lý do chỉ giữ trong bộ nhớ ứng dụng, không localStorage/sessionStorage/cookie/URL. Tải lại trang thì mất thông báo — đã chấp nhận.
- L03: form đăng xuất gửi redirect cố định /work/?signed_out=1. React hiện signed_out rồi xóa tham số bằng history.replaceState, không ảnh hưởng deep link, không đưa dữ liệu khác vào URL. signed_out=1 là tham số URL duy nhất được thêm.
- L05: cảnh báo Caps Lock chỉ khi ô mật khẩu đang focus, dựa vào trạng thái phím (getModifierState), không đọc/ghi giá trị mật khẩu, thông báo qua vùng aria-live="polite".
- L06: đặt con trỏ vào ô tên đăng nhập khi mở trang; không cướp focus khi đang có thông báo lỗi.
- L07: nhãn “Tiếng Việt” thành chữ tĩnh, bỏ viền/nền/hiệu ứng như nút; không thêm chuyển ngôn ngữ.
- L08: câu chữ nguyên văn bảng mục 6 cho năm khóa trên.

Được sửa: frontend/src/features/auth/**, frontend/src/shared/api/client.ts và client.test.ts, frontend/src/app/providers.tsx, frontend/src/app/shell/AppShell.tsx (chỉ giá trị redirect của form đăng xuất và phần nối cờ hết phiên nếu cần), test Vitest mới cạnh code, frontend/tests/e2e/login.spec.ts hoặc một spec mock mới, kỳ vọng logout trong projects.spec.ts nếu thông báo mới làm đổi, và docs handoff (PROJECT_STATUS, CHANGELOG, ROADMAP, mục bàn giao trong đặc tả).

Ngoài phạm vi: L04 và link handoff 2FA — giữ loginUrl() với đích /web/login như hiện tại; câu chữ mfa_title, mfa_body, mfa_link — giữ nguyên, thuộc slice 2 (mục 10.2); addon tp_web_login, template Odoo, tham số auth_signup; custom_addons/, contracts/openapi/; endpoint xác thực mới; giữ dữ liệu form khi hết phiên; đa ngôn ngữ; đổi bố cục hoặc hình minh họa. Không cài addon, không setup/upgrade/seed tp_tanphat_dev, không đổi credential.

Gate: đặc tả v0.6 ghi slice 1 ở READY_FOR_TEST_CODE; D1–D6 và câu chữ mục 6 đã chốt. Nếu gate không đúng như vậy, nếu cần quyết định ngoài đặc tả (câu chữ mới, tham số URL khác, lưu trạng thái ra ngoài bộ nhớ) hoặc source hiện tại khiến L01–L03 không làm được đúng đặc tả, dừng và báo BLOCKED kèm lý do; không tự chọn thay người dùng. Khi gate đạt, chạy scripts/ai_workflow.py start trước lần sửa đầu tiên.

Test bắt buộc, chỉ nhận test thực đã chạy:
1. npm.cmd run typecheck --prefix frontend và npm.cmd test --prefix frontend. T01 phủ: sai mật khẩu, login không tồn tại, khóa tạm, 429, 502, lỗi mạng, JSON hỏng; kết quả không chứa message server.
2. Build với VITE_ODOO_DATABASE=tp_tanphat_dev, chỉ để build, không gọi database.
3. Mock E2E bằng page.route, không cần Odoo: T02 khóa tạm (cooldown hiện, credentials không hiện, mật khẩu bị xóa); T03 đang ở trang dự án thì request kế tiếp nhận 401 → expired, đăng nhập lại về đúng trang; T04 mở lần đầu không có expired/signed_out và con trỏ ở ô tên đăng nhập; T06 Caps Lock hiện/ẩn đúng, không có giá trị mật khẩu trong DOM ngoài input; mở /work/?signed_out=1 hiện thông báo và URL sạch sau replaceState.
4. T11 hồi quy: toàn bộ login.spec.ts (ca MFA vẫn kiểm link /web/login và câu chữ handoff cũ), 320/390/1440 không tràn ngang, reduced-motion. projects.spec.ts là live trên runtime dev (.local/dev-secrets.json, Odoo cổng 18069): nếu runtime ban đầu dừng thì được dev.ps1 start để chạy rồi dev.ps1 stop; nếu ban đầu đang chạy thì dùng nguyên, không stop. Không setup/upgrade/seed. Không chạy được thì ghi rõ T11 chưa đủ, không coi là đạt.
5. Không cần Ruff/Odoo tests nếu không đụng Python. Chạy scripts/ai_workflow.py check.

Sau khi đạt: cập nhật PROJECT_STATUS (AUTH-002 slice 1 → IMPLEMENTED_PENDING_AUDIT, chưa phải TECHNICAL_ACCEPTED), CHANGELOG, ROADMAP, mục bàn giao trong đặc tả; chạy git diff --check, scripts/ai_workflow.py finish --change-id <CHG> --check "<lệnh và kết quả>" rồi check.

Báo cáo cuối: gate, CHG-ID, file đã đổi, lệnh và kết quả thực (số pass/fail/skip), T01–T04/T06/T11 đã phủ bằng test nào, trạng thái runtime dev ban đầu và sau cùng, giới hạn còn lại, next action (phiên điều phối review rồi mới giao slice 2). Không commit/push.
```
