# NATIVE-STABILIZE-001 — Audit độc lập

Ngày 05/11/2026, Asia/Saigon. CHG-20261105-003. Audit source/bằng chứng và chạy lại trên clone; không sửa application code, không apply dev, commit hoặc push.

## Kết luận

**NEEDS_FIX cho toàn batch và đặc tả UI-CTR-NATIVE-001a.** Hai bản sửa F-DASH-01/02 đạt kiểm chứng kỹ thuật độc lập trong phạm vi của chúng. Chưa chuyển kết luận này thành nghiệm thu toàn DASH/MOBILE/DATA003 hoặc chấp thuận triển khai dev/pilot. Công cụ test cần fail đúng và đặc tả wizard cần sửa trước khi bàn giao bước code hợp đồng.

## Finding bắt buộc

### A1 — P1: Đặc tả dựa vào bảo vệ chủ sở hữu wizard không tồn tại mặc định

- Vị trí: `docs/architecture/TP_UI_CTR_NATIVE_001_SPEC.md`, mục 9 (dòng 163–164 trước audit override).
- Tài liệu cấp `crud` cho `tp_core.group_user`, rồi khẳng định transient mặc định chỉ cho người tạo đọc. Source Odoo 20 checkout này dùng ACL/rule thông thường cho TransientModel (`odoo/orm/models_transient.py:10`, `odoo/orm/models.py:3603`); không tự thêm domain `create_uid`.
- Tái hiện độc lập trên clone: dùng transient chuẩn `project.task.type.delete.wizard`, thêm permission tương đương đề xuất trong một transaction rollback, Long tạo wizard, Sơn đọc được `create_uid` và sửa được wizard đó. Thêm restriction global `create_uid = user.id` thì lần đọc của Sơn bị AccessError. Không gọi action xóa/đổi task, không commit ACL/wizard thử.
- Rủi ro nếu code đúng nguyên văn đặc tả: người khác có thể đọc/sửa wizard chứa payload hợp đồng hoặc tiền; bảo vệ model hợp đồng không bảo vệ bản sao ở transient.
- Sửa đặc tả: ownership restriction tường minh cho wizard và wizard-line, scope company/project hiện hành, kiểm access/owner trước public action; chặn target/payload relink trái quyền; không coi `readonly`/ẩn nút là bảo vệ. Thêm test hai user qua read/search/export/write/unlink và RPC public action với ID wizard của người khác; kiểm tổ hợp group.
- Đây là finding thiết kế trước code, **không phải bằng chứng đã có lỗ hổng wizard hợp đồng trên dev**: wizard đó chưa được triển khai.

### A2 — P2: Chưa bảo vệ bản sao tiền trong wizard sau thu hồi quyền

- Vị trí: cùng đặc tả, mục 8–10, mục 12 và AT-10.
- Wizard edit được thiết kế nạp giá trị tiền thành Char để sửa, nhưng chưa chỉ rõ quyền trên bản sao transient/wizard-line/payload/baseline dùng để so sánh thay đổi. Ownership riêng không giải quyết người tạo đã mất grant hoặc assignment.
- Tình huống cần ngăn: mở wizard khi có grant → dữ liệu tiền được lưu trong transient → revoke/expire grant hoặc assignment → cùng user đọc/export lại transient vẫn lấy được tiền dù model gốc đã chặn. Không thể thu lại dữ liệu đã gửi về browser trước revoke; yêu cầu áp dụng cho request mới.
- Sửa đặc tả: chọn rõ thiết kế kiểm quyền hiện hành trên mọi kênh server đọc/lưu payload tài chính, kể cả default_get, onchange, web_read, wizard-line, export và retry; không dùng `compute_sudo` hoặc readonly để giữ bản sao có thể đọc. Tách metadata khỏi dữ liệu tài chính để người soạn metadata vẫn dùng đúng quyền cũ. Thêm acceptance trước/sau revoke/expiry và relink project/contract. Đây là thiếu sót đặc tả, chưa phải exploit code hợp đồng đã tồn tại.

### A3 — P2: Runner Odoo test không trả thất bại khi test fail hoặc không chạy

- Vị trí: `scripts/native_stabilize001.py:425–439`.
- `odoo_tests()` chỉ in `returncode`, summary và errors rồi return bình thường. `main()` không kiểm kết quả, nên CLI trả 0 khi subprocess trả 1, khi summary báo fail dù exit 0, khi 0 tests hoặc thiếu summary. Log được đọc toàn bộ và dùng lại tên, nên còn có nguy cơ đọc summary lần cũ.
- Tái hiện bằng fault injection vào subprocess, không chạy test giả trên database: bốn ca trên đều return bình thường. Evidence giữ local `runner-failure-reproduction.json`.
- Sửa runner: chỉ đọc log của lần chạy mới, kiểm process exit + summary của database đúng + số test dương + 0 failed/0 errors; fail nonzero khi thiếu bằng chứng. Định nghĩa số test theo tags, không hardcode29 cho mọi suite. Unit test fail/0/missing/stale-log và pass thật.
- Finding không phủ nhận 29 bài test đã chạy thực và đạt; audit chạy độc lập với log riêng, kiểm exit và summary bằng assertion ngoài runner.

## Kiểm tra thực chạy

| Kiểm | Kết quả audit |
| --- | --- |
| Baseline | `ai_workflow check` đạt CHG-20261105-002 trước audit; source chưa commit được giữ nguyên |
| Snapshot | 107 đích checksum khớp manifest; diff source zip trước batch với bốn file sửa xác nhận chỉ thêm nhãn phạm vi, fallback project và một test expense |
| Odoo tests | Chạy trực tiếp clone đã dừng: `-u tp_dashboard_privacy,tp_web_home --test-enable --test-tags /tp_dashboard_privacy,/tp_web_home --stop-after-init --no-http`; exit0, `0 failed, 0 error(s) of 29 tests` |
| Browser | Chạy lại probe đã review, chỉ đổi output trong bộ nhớ để giữ evidence cũ:78/78; Home22/dashboard8/revocation3/session1/responsive30/zoom14 |
| ORM | Chạy lại9 actor×2 dashboard; assertion độc lập so invoice/count/expense-state và task/hour với truth; drilldown đúng quyền; thu hồi dashboard/project bị chặn hoặc thu hẹp theo nguồn |
| Kiểm tĩnh | Ruff đạt;5 XML parse đạt; Node syntax probe/dashboard ESM đạt; `git diff --check` đạt |
| Ảnh | Đã xem ảnh mới dashboard1440, đối chiếu ảnh lỗi có lọc và mobile390; scope text và fallback đúng |
| Dev | SQL REPEATABLE READ/read-only:538 bảng, so snapshot Claude chỉ `bus_bus`, `mail_presence`, `res_device_log` khác; không delta bảng nghiệp vụ. Không quy toàn bộ delta phiên cho riêng audit |
| Cleanup | Clone18169 đã dừng như đầu audit; revocations `{}`; ACL/wizard thử rollback; dev18069 vẫn chạy |

Evidence riêng ngoài Git: `.local/native-stabilize001-independent-audit/`. Không in credential/token/config secret. Probe dùng session authenticate, chưa gõ login form; logout mất hiệu lực cookie không thay test timeout thật. Chỉ Chromium emulation/zoom, không thiết bị thật/WebKit. `finance_truth` không tính riêng tổng chưa thuế; không overclaim kiểm mọi công thức/phân bổ/kỳ ngày. Không chạy lại toàn bộ contract backend, triển khai production hay audit sâu tất cả các batch cũ.

## Bước sau

1. Giao Claude sửa A1/A2 ở đặc tả và A3 ở tooling; không code native Contracts trong correction này. [Prompt correction](../prompts/CLAUDE_NATIVE_STABILIZE_001_CORRECTION.md).
2. Audit delta correction. Hai sửa dashboard có thể được xét apply dev riêng nếu người dùng yêu cầu, kèm snapshot/recovery, nạp Python/assets và smoke; audit này không tự apply.
3. Khi đặc tả đạt mới giao UI-CTR-NATIVE-001a trên test bằng actor/dữ liệu giả. TASK-001 vẫn PROPOSED/deny; upload/BASE/ký/hiệu lực/thanh toán/grant thật/pilot không mở.
