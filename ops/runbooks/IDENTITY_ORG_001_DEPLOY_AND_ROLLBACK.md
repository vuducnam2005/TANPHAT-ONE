# IDENTITY-ORG-001 — Triển khai và khôi phục

Chỉ `tp_tanphat_test:18079` và `tp_tanphat_dev:18069`, cluster55432. Không DB thứ
ba, không restore test sang main. Chỉ một writer test; kiểm PID/config và session
trước restore. Dừng runtime theo `.local/identity-org001/runtime.ps1 stop test|dev`;
không dùng `dev.py stop` vì dừng cả cluster.

Source trước task của sáu addon ở `.local/identity-org001/rollback-source.zip`
và JSON SHA256; source trong backup DB được chụp lúc triển khai có thể là source
mới. Dùng zip riêng để trả source trước task, giữ dirty worktree ngoài scope.
Evidence/dump/config/filestore và inventory chứa danh tính/auth hash ở `.local/`,
không stage hoặc đưa vào Git.

1. Kiểm HR/HEAD/KH-KD, Ruff/XML/assets/HOOT/browser và seal cuối của sáu addon.
2. `.local/identity-org001/ops.py backup tp_tanphat_dev` dùng snapshot PostgreSQL,
   dump, từng blob+SHA, source/config, toàn bộ rowsets và sequence archive.
3. Backup test rồi restore đúng canonical test. Helper `rehearse.py` chỉ gỡ bảng
   transient mới `tp_hr_identity_wizard` sau kiểm không FK ngoài; gỡ đúng FK mới
   `tp_hr_role_wizard_target_department_id_fkey` sau kiểm source/target/column.
   Không DROP CASCADE. Bản test trước gỡ được lưu riêng. FK mới không có trong dump
   main cũ sẽ cản pg_restore --clean nếu không gỡ trước.
4. Helper cũ `.local/hr001/ops.py restore-test` đối chiếu toàn bộ rowsets/blob refs/
   sequence; chỉ PASS khi khớp. `.local/hr001/neutralize_test.py` kiểm lại trước khi
   đổi UUID/baseURL test, tắt cron/SMTP. Không mở HTTP test trước neutralize.
5. Upgrade/test lại source cuối trên test, kiểm reconciliation theo mapping ID với
   preview/log; không chuyển phòng/role thật. Fixture giả chỉ test và phải loại
   khỏi test bằng restore trước bàn giao sạch.
6. Dừng đúng main, backup cuối và đối chiếu drift so inventory; upgrade duy nhất
   HR trên main (`-u tp_hr_workspace --no-http --stop-after-init`), không chạy test,
   seed password hoặc thay role main. Home static asset được tải theo source seal.
7. Reconciliation đã kiểm trên test: preview main phải khớp snapshot hiện tại;
   qua wizard admin có lý do/audit. Chỉ tên và ảnh tại các mapping duy nhất. Không
   merge account, đổi auth/department/quyền hoặc sửa snapshot hợp đồng.
8. Start main, smoke chỉ đọc, so source seal/88 rowsets theo cột baseline/auth và
   blob. Ghi riêng delta danh tính có phép và metadata upgrade. Lỗi filestore GC
   Windows không thay kiểm SHA/size từng blob có tham chiếu.

```powershell
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_hr_workspace --test-enable --test-tags /tp_hr_workspace,/tp_project:TestDepartmentRole,/tp_kd_workspace --stop-after-init --no-http --logfile .local/identity-org001/backend-restored.log
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace --no-http --stop-after-init --logfile .local/identity-org001/upgrade-main.log
```

Đọc tổng tests `0 failed, 0 error(s)`, không chỉ exit code. Khi chỉ upgrade HR,
test-tags vẫn chạy post-install regression của module đã cài. Không nâng module
khác trên main chỉ để chạy test. Kết quả thực và backup cuối xem
[acceptance](../../docs/demo/IDENTITY_ORG_001_ACCEPTANCE.md).

Rollback: backup trạng thái hiện tại, kiểm zip/hash và danh sách file mới
`rollback-new-files.json`; trả đúng file đã đổi của task và gỡ đúng file mới,
upgrade HR rồi restart/assets/smoke. Các field/bảng transient có thể còn nhưng
không tự xóa audit/role events. Nếu chức năng đã được dùng, đảo chuyển phòng qua
action có preview/lý do; không restore cũ làm mất giao dịch phát sinh. Full restore
chỉ từ backup **main** đã chọn sau đánh giá dữ liệu sau backup, theo runbook sạch.
Danh tính đã reconciliation cần kế hoạch đảo từng field từ preview/applied log;
không tự đổi tên/ảnh hoặc quyền người thật ngoài scope rollback được xác nhận.


Follow-up CHG-20261112-012 chỉ2file Python versionguard/tests: HR41 và cleanbrowser đạt, exactmainbackup080056033059Z/restart; không schema/upgrade/restore. Rollback riêng về011: kiểm SHA256 trong `.local/identity-org001/rollback-version-012.json` và restore đúng2file từ zip cùng tên, restart/smoke; không đảo reconciliation hoặc dữ liệu. Đây là rollbacksource011, không source trước toàntask.
