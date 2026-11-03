# Prompt Claude — C01/FND-002: môi trường test cô lập tái lập được

Copy nguyên prompt dưới đây vào phiên Claude khi người dùng giao batch C01. Prompt này chỉ tạo tooling test cô lập; không mở nghiệp vụ hay người dùng thật.

```text
Làm việc trong C:\TANPHAT ONE. Đây là C01/FND-002, làn F: tooling test-only. Đọc CHANGELOG để chọn CHG-YYYYMMDD-NNN mới chưa dùng theo ngày hiện tại; không ghi đè change ID cũ. Không commit, không push, không sửa odoo/ hoặc addons/, không dùng dữ liệu thật và không nâng cấp/seed tp_tanphat_dev.

Đọc trước: AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/CHANGELOG.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md, docs/architecture/TP_READY_FOR_CODE_GATE.md, frontend/tests/e2e/contract-workflow-live.spec.ts, scripts/dev.py và các test workflow hiện có. Chạy git status, ai_workflow.py check và runtime status. Lấy handoff mới nhất làm baseline, đối chiếu baseline kỹ thuật CHG-020 và các delta sau đó. Nếu code hiện có lệch handoff hoặc có batch khác chưa bàn giao, báo sai lệch và không sửa. Nếu checkpoint thuộc chính C01 bị ngắt thì tiếp tục đúng checkpoint đó, không xóa hoặc tạo baseline giả.

Mục tiêu duy nhất: chuyển helper test live/race hiện chỉ nằm ở .local/ctr002a-verify thành tooling/runbook tái lập được cho checkout khác, giữ nguyên workflow nghiệp vụ. Không tạo inbox, state/capability nghiệp vụ, API route hoặc màn hình mới. Được seed actor/project/grant giả với các capability hiện có trong database test của tool; không cấp grant cho user thật. Nếu gate đạt, chạy scripts/ai_workflow.py start trước lần sửa đầu tiên.

Phạm vi được phép: scripts/ test tooling, config example không secret, runbook, test harness và docs handoff cần thiết. Có thể dùng PostgreSQL/Odoo local nếu nhận diện đúng; phải có ownership marker và data-dir/config/database/origin riêng. Không drop/reset database hoặc xóa đệ quy trong batch này. Không sao chép helper local chưa review hoặc credential vào Git. Không chạm database dev.

Yêu cầu an toàn:
1. Prepare/start/status/stop rõ ràng; mỗi instance có marker, process id và target allowlist.
2. Refuse tp_tanphat_dev, wrong origin/port, foreign marker, port conflict, thiếu credential và cleanup nhầm process.
3. Fixture fake-only, idempotent; lần chạy lại không tạo duplicate actor/project/contract, không đổi password dev, không in secret.
4. Live spec giữ guard database/origin/credentials distinct; race dùng hai HTTP session độc lập và chứng minh cả hai request cùng chờ row lock trước khi release.
5. Report chỉ ghi metadata không nhạy cảm: source fingerprint, target database/origin, lệnh, assertions thật đã chạy, HTTP statuses, version/audit/outbox/idempotency deltas, start/stop status. Failed assertion phải trả exit code khác 0.
6. Không ghi credential, cookie, dump, filestore, trace, video hay hồ sơ doanh nghiệp vào Git; .local phải ignored.

Test bắt buộc: refuses dev/wrong target/foreign marker/port conflict; prepare twice không reset; start/stop ownership; live flow create→edit→submit→return→rework→edit→resubmit; different idempotency keys 200+409 stale_version; same key 200+200 replay; counters version/audit/outbox/idempotency +1; workflow source, dev DB/config/secret/filestore không bị tool sửa; services restore về trạng thái ban đầu. Nếu PostgreSQL vốn đang chạy thì không dừng của người khác. Không reuse Vite server có proxy hoặc database khác mục tiêu; báo conflict thay vì kill process không sở hữu.

Kiểm chứng tooling bằng unit tests hành vi guard/lifecycle/failure status, Ruff và real isolated live/race. Chạy frontend typecheck/test/build nếu đổi harness TypeScript; dùng đúng VITE_ODOO_DATABASE của test. Odoo regression theo thay đổi nếu có ảnh hưởng bootstrap/module loading; đọc summary thực trong log. Không mặc định test đạt khi runner exit 0 hoặc khi live spec bị skip vì thiếu env. Báo rõ skip/blocked.

Nếu helper hiện tại có logic nguy hiểm hoặc phụ thuộc máy cá nhân không thể chuyển an toàn, không workaround; trả BLOCKED và ghi gap. Sau khi đạt, cập nhật PROJECT_STATUS/CHANGELOG/runbook, chạy git diff --check và ai_workflow.py finish/check.

Báo cáo cuối: gate, files, commands, target environment, assertions/results, cleanup, source/dev integrity, limits, next action. Không commit/push.
```
