# HR-DELETE-010 — Triển khai và khôi phục

Chỉ `tp_tanphat_test:18079` và `tp_tanphat_dev:18069` (cluster 55432). Không DB
thứ ba, không restore test sang main, chỉ một writer trên test. Dừng/khởi động
runtime bằng `.local/identity-org001/runtime.ps1 stop|start test|dev`. Evidence,
backup, ảnh và mật khẩu test ở `.local/hr-delete010/`, không vào Git; không chụp
ảnh/trace/video có mật khẩu thật.

## Phạm vi nguồn

`tp_organization` 20.0.2.1.0 → 20.0.2.2.0, `tp_hr_workspace` 20.0.1.8.1 → 20.0.1.9.0.

12 file sửa: `tp_organization` (manifest, `models/__init__.py`,
`models/employee_audit.py`, `models/hr_employee.py`, `models/hr_import.py`,
`tests/test_employee_correction.py`, `tests/test_hr_roster.py`), `tp_hr_workspace`
(manifest, `models/employee_delete.py`, `security/ir.access.csv`,
`views/employee_delete.xml`, `tests/test_employee_delete.py`).

5 file mới (xóa khi rollback source):
`tp_organization/models/employee_delete_plan.py`,
`tp_hr_workspace/static/src/delete/employee_delete.js|.xml|.scss`,
`tp_hr_workspace/static/tests/employee_delete.test.js`.

Bản gốc: `.local/hr-delete010/rollback-source-010.zip` và
`rollback-source-010.json` (SHA256 từng file, khớp nội dung git HEAD `c62377a2`
vì worktree sạch lúc bắt đầu task).

Tài liệu cũng đổi nhưng không thuộc gói rollback code: README HR, DECISIONS
(DEC-042), guide/security HR, PROJECT_STATUS/CHANGELOG/ROADMAP, acceptance và
runbook này. Khi rollback, giữ chúng làm lịch sử và ghi thêm mục rollback; bản cũ có
ở git `c62377a2` và `source.zip` của backup main.

Schema: bảng `tp_hr_employee_audit` thêm cột `source_code`, `request_id`,
`account_action`, `account_ref`, `account_login`, `verification` (cột `snapshot`
đã có từ 008) và ràng buộc duy nhất `(request_id, employee_ref)`; lựa chọn `action` thêm
`permanent_delete`. Model wizard `tp.hr.employee.delete.wizard` (dữ liệu tạm) bị
bỏ cùng ACL và metadata; Odoo **không** tự gỡ bảng `tp_hr_employee_delete_wizard`
và `hr_employee_tp_hr_employee_delete_wizard_rel` (diễn tập: còn 1 dòng tạm từ lần mở
hộp thoại 008). Giữ nguyên, không DROP thủ công; rollback về 008 dùng lại hai bảng
này. Không đổi dữ liệu nghiệp vụ (đối chiếu từng bảng trong acceptance).

## Triển khai

1. Test 18079 (dừng runtime test, không tác vụ khác dùng DB test):
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_organization,tp_hr_workspace --test-tags /tp_organization,/tp_hr_workspace --stop-after-init
   ```
   Đọc dòng `0 failed, 0 error(s) of N tests`, không chỉ exit code. Dòng ERROR
   “bad query” đến từ test ràng buộc duy nhất cố ý. Sau đó Ruff, `git diff --check`,
   HOOT `@tp_hr_workspace` và kiểm trình duyệt bằng tài khoản giả theo acceptance.
2. Backup main: dừng đúng runtime dev, kiểm 0 session main,
   `.local/hr001/ops.py backup tp_tanphat_dev` (dump, blob+SHA, source/config,
   rowsets, sequence). Diễn tập restore bản đó vào **test** (không DB thứ ba),
   neutralize trước khi mở HTTP, upgrade và test lại.
3. Main: backup cuối, rồi:
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_organization,tp_hr_workspace --no-http --stop-after-init
   ```
   Không seed, không fixture, không xóa/khóa nhân viên hoặc tài khoản thật.
4. Start main, Ctrl+F5, smoke chỉ mở/đọc/Hủy: chọn hồ sơ → Tác vụ → “Xóa vĩnh
   viễn nhân viên” → xem danh sách/khối Xóa-Giữ-Chặn → **Hủy**. Không nhập mật
   khẩu, không bấm nút đỏ. So số nhân viên/tài khoản/audit trước-sau.

## Rollback

1. Backup trạng thái hiện tại của DB cần rollback trước.
2. Kiểm SHA256 zip/manifest, trả đúng 12 file gốc, xóa đúng 5 file mới; giữ file
   dirty ngoài scope.
3. Upgrade lại `tp_organization,tp_hr_workspace` (về 20.0.2.1.0/20.0.1.8.1:
   luồng “Xóa hồ sơ nhập nhầm” của DEC-041 hoạt động lại, có lại wizard/ACL).
4. Cột audit mới Odoo không tự gỡ; **giữ** `tp_hr_employee_audit` cùng các cột/bản
   ghi `permanent_delete` làm bằng chứng. Không xóa audit, backup hoặc can thiệp
   PostgreSQL/WAL để xóa dấu vết.
5. Dữ liệu không đảo tự động:
   - Hồ sơ đã xóa vĩnh viễn không tự khôi phục. Nhập lại thủ công từ snapshot
     audit/dòng nhập Excel còn giữ, với **mã TP mới** (mã cũ không tái dùng).
   - Tài khoản đã khóa qua tùy chọn “Xóa hồ sơ và khóa tài khoản” giữ khóa; mở lại
     bằng luồng mở khóa tài khoản hiện có, cấp lại vai trò/quyền theo snapshot
     `revoked` trong audit nếu có quyết định.
   - Dòng nhập Excel đã bỏ liên kết giữ nguyên mã nguồn; nhập lại danh tính đó báo
     xung đột cho tới khi xử lý tay.
6. Restart, Ctrl+F5, smoke. Full restore chỉ từ backup **main** ngay trước upgrade
   sau khi đánh giá giao dịch phát sinh sau backup.

## Backup đã dùng (12/11/2026)

Thư mục `.local/hr001/` (dump, blob+SHA, source/config, rowsets, sequence):

- Main A (diễn tập): `backup-tp_tanphat_dev-20261112T141132721082Z`.
- Test trước khi restore A đè lên test:
  `backup-tp_tanphat_test-20261112T141211113291Z`.
- **Main B, ngay trước upgrade, dùng cho full restore:**
  `backup-tp_tanphat_dev-20261112T141836737342Z` (600 bảng, 661 blob ref; so dòng
  với A: 0 thay đổi).

Diễn tập restore phải vào **test** (`ops.py restore-test <thư mục>`, rồi
`neutralize_test.py` trước khi mở HTTP), không restore test đè main, không DB thứ ba.

Kết quả thực, bằng chứng và giới hạn:
[acceptance](../../docs/demo/HR_DELETE_010_ACCEPTANCE.md).
