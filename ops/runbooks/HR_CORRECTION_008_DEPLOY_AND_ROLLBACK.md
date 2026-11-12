# HR-CORRECTION-008 — Triển khai và khôi phục

Chỉ `tp_tanphat_test:18079` và `tp_tanphat_dev:18069` (cluster 55432). Không DB
thứ ba, không restore test sang main, chỉ một writer trên test. Dừng/khởi động
runtime bằng `.local/identity-org001/runtime.ps1 stop|start test|dev`; không dùng
`dev.py stop`. Evidence, backup, ảnh và mật khẩu test ở `.local/`, không vào Git.

## Phạm vi nguồn

26 file sửa: `tp_organization` (manifest, `data/employee_sequence.xml`,
`models/hr_employee.py`, `models/hr_import.py`, `models/__init__.py`, ACL, `i18n/vi.po`,
tests), `tp_hr_workspace` (manifest, `models/hr_account_wizard.py`,
`models/__init__.py`, ACL, `views/workspace.xml`, SCSS overview/profile, tests),
`tp_i18n_vi` (`i18n/vi.po`, test catalog), SCSS `tp_kd_workspace` (overview,
report center, table, tables007) và `tp_web_home` (home launcher, shell navbar).

10 file mới (xóa khi rollback source):
`tp_hr_workspace/migrations/20.0.1.8.0/post-migrate.py`,
`tp_hr_workspace/models/employee_delete.py`, `tp_hr_workspace/views/employee_delete.xml`,
`tp_hr_workspace/tests/test_employee_delete.py`,
`tp_organization/migrations/20.0.2.1.0/post-migrate.py`,
`tp_organization/models/employee_audit.py`, `tp_organization/tests/test_employee_correction.py`,
`tp_web_home/static/src/views/selection_box.xml`,
`tp_web_home/static/tests/selection_box.test.js`,
`tp_web_home/static/src/density/density.scss`.

Bản gốc trước task: `.local/hr-correction008/rollback-source-008.zip` và
`rollback-source-008.json` (SHA256 từng file, đã kiểm lại sau khi nén), manifest
`rollback-manifest.json` ghi nguồn chứng minh từng bản gốc (hash lúc
`ai_workflow start`, git HEAD hoặc seal IDENTITY-ORG-001/HR-COMPACT-007).

## Triển khai

1. Test: chạy Odoo test, Ruff, XML, HOOT, browser theo acceptance.
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_organization,tp_hr_workspace,tp_i18n_vi,tp_web_home --i18n-overwrite --test-enable --test-tags /tp_organization,/tp_hr_workspace,/tp_i18n_vi,/tp_web_home --stop-after-init --no-http
   ```
   Đọc dòng `0 failed, 0 error(s) of N tests`, không chỉ exit code. 4 dòng ERROR
   “bad query” đến từ test unique constraint cố ý.
2. Backup main: dừng đúng runtime dev, kiểm 0 session main,
   `.local/hr001/ops.py backup tp_tanphat_dev` (dump, blob+SHA, source/config,
   rowsets, sequence).
3. Diễn tập: `.local/hr-correction008/rehearse008.py <backup main>` kiểm test đã
   dừng/không session, backup test, chỉ gỡ 3 bảng mới của task
   (`hr_employee_tp_hr_employee_delete_wizard_rel`, `tp_hr_employee_delete_wizard`,
   `tp_hr_employee_audit`) sau khi kiểm không FK ngoài, không CASCADE, rồi restore
   có đối chiếu rowsets/blob/sequence. Neutralize trước khi mở HTTP test; upgrade
   và test lại (thêm `/tp_project:TestDepartmentRole,/tp_kd_workspace`).
4. Main: backup cuối, so drift với backup diễn tập (chỉ được khác bảng phiên/log
   đăng nhập), rồi:
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_organization,tp_hr_workspace,tp_i18n_vi,tp_web_home --i18n-overwrite --no-http --stop-after-init
   ```
   Log phải có mapping mã giống diễn tập và `next employee code`. Không seed, không
   xóa nhân viên thật, không fixture.
5. Start main, smoke chỉ đọc hoặc chỉ Hủy; so `rowsnap.py`/`dumpcmp.py` với delta
   diễn tập.

## Rollback

1. Backup trạng thái hiện tại của DB cần rollback trước.
2. Kiểm SHA256 zip/manifest, trả đúng 26 file gốc, xóa đúng 10 file mới; giữ các
   file dirty ngoài scope.
3. Upgrade lại 4 addon (`--i18n-overwrite`) và `hr_timesheet`
   (`-u hr_timesheet`) để gắn lại binding action native “Delete employee” vào menu
   Tác vụ; gỡ source không tự gắn lại binding này.
4. Sau khi bỏ model, Odoo không tự xóa bảng: `tp_hr_employee_audit` được **giữ**
   làm bằng chứng xóa/sửa mã; bảng wizard tạm có thể gỡ sau khi kiểm không FK
   ngoài, không CASCADE.
5. Dữ liệu không đảo tự động:
   - Mã `TP10070` của id 67 giữ nguyên. Chỉ trả về `TP20000` khi có quyết định
     riêng, qua thao tác có lý do/audit; không đổi mã người khác.
   - Sequence giữ 10071; không đặt lại 20000.
   - Tài khoản `tranphuongdong` đã chuyển vi_VN giữ nguyên; đổi lại ngôn ngữ cá
     nhân nếu người dùng yêu cầu.
   - Hồ sơ đã xóa qua chức năng không tự khôi phục; dùng snapshot trong audit để
     nhập lại thủ công nếu cần.
6. Restart, Ctrl+F5, smoke. Full restore chỉ từ backup **main** đã chọn
   (`backup-tp_tanphat_dev-20261112T101939483900Z` là bản ngay trước upgrade) sau
   khi đánh giá giao dịch phát sinh sau backup.

Kết quả thực, bằng chứng và giới hạn:
[acceptance](../../docs/demo/HR_CORRECTION_008_ACCEPTANCE.md).
