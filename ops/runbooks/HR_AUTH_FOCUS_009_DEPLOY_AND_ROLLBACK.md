# HR-AUTH-FOCUS-009 — Triển khai và rollback

**Change:** CHG-20261112-014, ngày 12/11/2026. Hai addon đã áp, main smoke 4 nhóm/0 errors và HOOT 25 tests/105 assertions đạt. Hai runtime đang chạy.

Chỉ `tp_tanphat_test:18079` và `tp_tanphat_dev:18069`, PostgreSQL workspace 55432. Một writer test tại một thời điểm; không DB thứ ba, không fixture main, không restore test sang main. Không stage/commit/push.

## Bản nguồn và backup

- Source trước sửa application: `.local/hr-auth-focus009/rollback-source.zip` và `rollback-source.json`, 66 file cùng SHA256. Dùng bản này để rollback; source.zip trong backup triển khai có thể chứa source mới.
- File application mới: `custom_addons/tp_web_login/static/src/js/identitycheck.js`.
- File kiểm mới: `custom_addons/tp_hr_workspace/static/tests/account_focus.test.js` và `scripts/hr_auth_focus009.cjs`.
- Test backup: `.local/hr001/backup-tp_tanphat_test-20261112T114259236813Z`.
- Main backup: `.local/hr001/backup-tp_tanphat_dev-20261112T120334281779Z`, 600 bảng, 661 tham chiếu blob.

Evidence, backup, session và credential chỉ ở `.local/`, không đưa vào Git/log công khai. Không in mật khẩu hoặc cookie khi chạy harness.

## Triển khai

1. Đọc [acceptance](../../docs/demo/HR_AUTH_FOCUS_009_ACCEPTANCE.md), kiểm source cuối và baseline dirty worktree. HOOT cuối 25 tests/105 assertions; browser 8 nhóm/0 errors. Không tính lượt setup lỗi trước đó là pass.
2. Dùng `.local/identity-org001/runtime.ps1 stop test` trước upgrade/test cần runtime riêng; helper kiểm PID/config. Không dùng `dev.py stop` vì có thể tác động cluster. Chạy tuần tự, không chồng writer hoặc asset generation.
3. Upgrade chỉ hai addon trên test, rồi start test và chạy browser/HOOT đã chọn:

   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_hr_workspace,tp_web_login --no-http --stop-after-init --logfile .local/hr-auth-focus009/upgrade-test.log
   .\.local\identity-org001\runtime.ps1 start test
   ```

4. Sau test đạt, dừng đúng main bằng helper `stop dev`; kiểm không session main còn hoạt động và tạo backup cuối bằng `.venv/Scripts/python.exe .local/hr001/ops.py backup tp_tanphat_dev`. Bản đã tạo được ghi ở trên. Kiểm dump/blob/manifest thành công trước áp.
5. Áp source đã test; upgrade và restart:

   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace,tp_web_login --no-http --stop-after-init --logfile .local/hr-auth-focus009/upgrade-main.log
   .\.local\identity-org001\runtime.ps1 start dev
   ```

6. Mở browser sạch/Ctrl+F5, kiểm version HR 20.0.1.8.1/login 20.0.1.4.1, sidebar, mở/đóng/hủy dialog và focus; main chỉ đọc hoặc Hủy. Không tạo/reset tài khoản người thật để smoke. Đã đạt trong `main-smoke.json`; delta 9 bảng nghiệp vụ và rowset nhóm/quyền giữ nguyên so với backup. Source đã áp khớp `tested-source.json`.

## Rollback UI

Không cần restore DB cho thay đổi UI này. Backup trạng thái hiện tại trước rollback; dừng đúng runtime cần trả bằng helper. Kiểm hash manifest rồi trả **đúng các file task đã sửa** từ zip riêng, không ghi đè toàn bộ 66 file nếu có sửa ngoài scope hoặc sửa phát sinh sau snapshot. Đối chiếu diff và giữ các thay đổi người dùng không liên quan.

Gỡ đúng ba file mới nêu trên sau khi kiểm chúng vẫn thuộc task và không có sửa mới cần giữ. Kiểm manifest/assets không còn tham chiếu file mới. Upgrade lại `tp_hr_workspace,tp_web_login` trên DB tương ứng với `--no-http --stop-after-init`, restart bằng helper, tải asset mới và smoke mở/đóng/hủy dialog/sidebar. Không đổi credential, quyền, mapping, dữ liệu nhân viên hoặc DEC-040. Không restore test đè main; nếu có sự cố dữ liệu ngoài UI, dừng và đánh giá riêng thay vì tự restore DB.

Kiểm password manager hiện chỉ chứng minh Chrome157 tích hợp chạy headless trên bản Chrome cài thật; chưa bao phủ extension, mọi browser hoặc thiết bị mobile vật lý.
