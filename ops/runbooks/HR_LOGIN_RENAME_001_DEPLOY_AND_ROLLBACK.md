# HR-LOGIN-RENAME-001 — Deploy và rollback

Phạm vi: HR20.0.1.15.1 và admin delegation20.0.2.0.3. Theo policy17/11, commit/push đúng scope rồi giao PCserver; không cần xin lại quyền. Không đổi login người thật để test.

1. Kiểm source baseline từng file và runtime hiện tại; không áp WIP chấm công/báo cáo/sidebar/branding của phiên khác. Đóng gói đúng commit đã push, SHA256 chuẩn newline và mtime từ Git cho assets.
2. Backup đúng DB/môi trường: dump định dạng custom + pg_restore-list, filestore, source/config và SHA256. Private config/dump chỉ ở ignored .local hoặc thư mục backup server, không Git. Snapshot hash-only credentials/IDs/links/groups/companies và số liệu nghiệp vụ trước/sau.
3. Local18069 dùng candidate giữ các addon runtime hiện có và chỉ overlay scope HR/admin. PCserver `C:/Projects/TANPHAT-ONE`, tp-odoo/tp-postgres/tp_tanphat_dev. Dừng riêng runtime Odoo khi nâng, không restart tp-tunnel. Nâng `-u tp_hr_workspace,tp_admin_delegation --no-http --stop-after-init --max-cron-threads=0`, rồi mở lại runtime.
4. Chỉ chấp nhận exit0, không ERROR/CRITICAL, đúng2version; digest nghiệp vụ/credential/nhóm/liên kết không đổi. Probe ORM read-only: button/capability/audit selection/related/constraint/export hiện tại và từ chối actor thường; không ghi login.
5. Kiểm health/login local/server/public; tải JS/CSS thực, đối chiếu SHA256 server/public và chuỗi dialog/client action. Source hash không thay bằng chứng asset. Nếu không có session admin hợp lệ sẵn, không đăng nhập mới đá phiên người dùng; ghi authenticated public E2E NOT_RUN.
6. Nếu lỗi upgrade/health, giữ dump và source backup, dừng ghi, khôi phục source/config và DB+filestore đúng môi trường từ backup dưới đây; khởi động và kiểm lại. Không restore test đè main, không xóa DB hoặc tự đặt lại password. Bản rollback dùng phiên bản trước của cả HR/admin. Ghi rõ nếu cần restore DB do schema đã thay.

Helper ignored của batch: `.local/hr-login-rename-impl001/apply_local.py`, prepare_server.py, deploy-server.ps1, deploy_server.py, verify_release.py. Kết quả/backup/commit thực ghi trong [acceptance](../../docs/demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md). Runtime đổi source cùng scope, không git reset/pull đè checkout server khác batch.
