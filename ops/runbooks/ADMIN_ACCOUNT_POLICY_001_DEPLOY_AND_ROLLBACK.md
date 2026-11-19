# ADMIN-ACCOUNT-POLICY-001 — Deploy và rollback

Ngày 19/11/2026; theo DEC-051/062, user đã cho phép commit/push/deploy đúng hạng mục. Không áp diff reporting/branding/sidebar dở của phiên khác.

1. Chốt source và kiểm Odoo/backend/HTTP/browser trên DB test hiện có, không tạo DB mới. Chỉ đóng gói file của commit đã push, kiểm baseline từng file server và SHA256 source. Giữ mtime mới đúng cho assets.
2. Dừng riêng Odoo đúng môi trường trước upgrade; giữ PostgreSQL/tunnel. Sao lưu dump custom và pg_restore-list, filestore DB đang dùng, source/config và checksum. Lấy snapshot hash-only login/password/active/locks/groups/grants/employee-resource-partner links và số liệu nghiệp vụ.
3. Upgrade riêng `tp_hr_workspace,tp_admin_delegation` bằng `--no-http --stop-after-init --max-cron-threads=0`. Runtime local18069 dùng candidate của runtime đang chạy, overlay đúng source hạng mục; PCserver giữ `/workspace`/container/config/volume hiện có. Không đổi credential hay cấp/thu/khóa tài khoản người thật.
4. Chỉ nhận exit0, không ERROR/CRITICAL, HR20.0.1.16.0/admin20.0.2.1.0. Snapshot tài khoản/quyền/liên kết/nghiệp vụ phải giữ; chỉ version đổi. Khởi động lại Odoo và probe ORM READ ONLY các capability/nhãn/audit/guard, không thử ghi người thật.
5. Kiểm health/login local/server/public, JS/CSS bundle thực và hash server/public; private session không vào Git. Authenticated public E2E chỉ chạy khi có session hợp lệ và thao tác được phép; thiếu thì ghi NOT_RUN.
6. Nếu upgrade/health hoặc snapshot sai, dừng ghi; phục hồi đúng source/config trước thay đổi. Nếu đã thay schema/data, phục hồi dump và filestore cùng backup môi trường, không restore test đè main. Khởi động lại, kiểm health/source/snapshot và ghi rollback. Không tự xóa DB hoặc reset password.

Helper và log riêng nằm ignored `.local/admin-account-policy001/`; commit, backup và kết quả thực ở [acceptance](../../docs/demo/ADMIN_ACCOUNT_POLICY_001_ACCEPTANCE.md).
