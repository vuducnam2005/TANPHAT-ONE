# CORP-REPORT-001 — Cài test, áp main và rollback

Ngày 16/11/2026 · CHG-20261116-008. Main18069 **chưa được phép áp**. Không restore test đè main; không mang fixture/account/grant giả sang main.

## 1. Boundary và điều kiện

Source riêng `custom_addons/tp_reporting`, dependency `hr`, `project`, `tp_web_home`, `tp_organization`, `tp_hr_workspace`; export dùng xlsxwriter/reportlab có sẵn. Không sửa upstream, REST/OpenAPI/React, workflow nguồn hay grant thật. Source nền dirty có từ trước: boundary/hash/patch ở `.local/corp-report001/`; phải kiểm lại trước mọi áp.

Test chuẩn `.local/test/odoo.conf`, `tp_tanphat_test`, PostgreSQL55432, localhost18079; main `.local/odoo.conf`, `tp_tanphat_dev`,127.0.0.1:18069. Cookie tách hostname. Cron0, SMTP loopback9 trên test. Chỉ một phiên ghi test; marker private `test-writer.json` và kiểm pg_stat_activity/listener trước lệnh.

## 2. Test đã diễn tập backup/restore

Backup private `.local/corp-report001/backup-test-pre/`: database.dump, filestore, source-boundary.zip, config riêng và manifest SHA256. Snapshot source gồm working tree tại baseline, không chỉ HEAD. Rehearsal ngày16/11 phục hồi vào chính canonical test khi HTTP dừng, so fingerprint601bảng không khác và561blob đã lưu khớp; `.local/corp-report001/restore-rehearsal.json`,100.78giây. Không tạo database task mới; main không tham gia. Archive source đầu `source.zip` chưa hoàn tất được giữ để điều tra, **chỉ dùng source-boundary.zip có trong manifest**.

## 3. Lệnh test/install

Kiểm process đúng config trước khi dừng test; không `dev.py stop` vì dừng cluster chung. Không chạy setup/seed legacy.

```powershell
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -i tp_reporting --no-http --stop-after-init --max-cron-threads=0 --http-port=18079 --logfile=.local/corp-report001/install.log
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_reporting --test-enable --test-tags=/tp_reporting --no-http --stop-after-init --max-cron-threads=0 --http-port=18079 --logfile=.local/corp-report001/tests.log
```

Đọc summary `0 failed, 0 error(s) of N tests`, không chỉ exit0. Test fixtures chỉ database test, marker CORP-REPORT-001; credentials chỉ file private. Không tự gửi email/chat. Sau migration mở HTTP test config riêng; smoke login/home/7tab/author-review-return-resubmit/finalize/chart/filter/export và regression nguồn.

## 4. Gói áp 18069 — chỉ sau chỉ thị riêng

1. Người dùng xác nhận scope source/version và quyền áp; chốt lịch/assignment/thẩm quyền thật riêng, không lấy default kỹ thuật làm quy chế.
2. Lưu fingerprint main trước áp: HR/users/group/company/project/task/business/attachments/modules. Sao lưu đầy đủ DB+filestore+source working tree/config/credential bên ngoài Git và checksum; tạm dừng đúng Odoo main để nhất quán. Giữ cluster chạy, không đụng test.
3. Seal hash addon/dependencies đã test; đối chiếu boundary trước áp. Chuẩn bị source rollback từ working tree trước áp, không `git reset` dirty checkout.
4. Kiểm package runtime xlsxwriter/reportlab/font Unicode. Cài duy nhất `tp_reporting` bằng config main và `-d tp_tanphat_dev` trong cửa sổ được phép; cập nhật dependency chỉ khi đã xác định schema/version cần và đã test. Không chạy fixture, không tự tạo authority.
5. Khởi động lại đúng main, rebuild native asset qua module update, smoke read-only trước. So fingerprint ngoài module/config mới; login/cookie/version/menus/HR/KH-KD/Kho phải đúng. Assignment thật tạo sau quyết định có căn cứ qua luồng cấu hình được kiểm.
6. Ghi deployment evidence/status, business acceptance và pilot authorization riêng. Không commit/push nếu chưa được yêu cầu.

## 5. Rollback

Trước rollback lưu snapshot trạng thái lỗi, dừng đúng HTTP môi trường đích. Kiểm SHA256 backup, source/config compatibility và tham chiếu blob. Phục hồi **đồng bộ source trước áp + dump của chính môi trường + filestore tương ứng**, không dùng test dump cho main, không uninstall addon/xóa chéo bảng để giả rollback. Không phục hồi vào DB đang có client ghi. Khởi động đúng config, kiểm fingerprint/table/blob/session/login/quyền/export rồi mới mở lại. Nếu có dữ liệu mới sau áp phải chốt cách giữ/chuyển dữ liệu trước khi ghi đè.

Backup cùng máy chưa thay backup ngoài máy/RPO/RTO/production; kết quả test kỹ thuật không tự cho phép main hoặc pilot.
