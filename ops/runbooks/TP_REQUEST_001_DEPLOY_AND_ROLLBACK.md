# Runbook triển khai & Rollback — TP-REQUEST-001 (`tp_request` 20.0.1.0.0 + `tp_branding` 20.0.2.2.0)

## 1. Phạm vi triển khai
- Cài đặt mới module `custom_addons/tp_request` (`20.0.1.0.0`).
- Nâng cấp module `custom_addons/tp_branding` (`20.0.2.1.0` → `20.0.2.2.0`) để bổ sung 7 route `/app/de-nghi/...`.
- Môi trường đích: PC Server `192.168.1.73`, workspace `C:\Projects\TANPHAT-ONE`, container `tp-odoo` + `tp-postgres`, database `tp_tanphat_dev`, public URL `https://tpone.tadic.vn`.
- **Không** khởi động lại `tp-tunnel`; **không** tạo dữ liệu giả/tài khoản test trên `tp_tanphat_dev`; **không** chạm vào `tp.equipment.proposal` hay `hr.employee` đang có.

## 2. Quy trình sao lưu bắt buộc trước khi triển khai
Thực thi tự động bởi `ops/runbooks/deploy-tp-request001.ps1` vào thư mục `C:\TANPHAT-backups\tp-request001\req001-<timestamp>\`:
1. Dừng container `tp-odoo` để đóng băng ghi dữ liệu.
2. Chụp snapshot định lượng trước deploy (`before.txt`): số lượng và MD5 tổng hợp của `hr_employee`, `res_users`, `res_groups_users_rel`, `maintenance_equipment`, `tp_equipment_proposal`, `tp_hr_attendance_correction`, `ir_module_module`.
3. `pg_dump -U tp_odoo -F c tp_tanphat_dev` → kiểm chứng bằng `pg_restore -l` → lưu `tp_tanphat_dev.dump` + `restore-list.txt`.
4. Sao lưu filestore (`filestore.tar.gz`), mã nguồn bị ghi đè (`source.tar.gz`) và `docker.odoo.conf`.

## 3. Triển khai & Kiểm chứng
1. Giải nén đúng danh sách tệp của bản phát hành (`custom_addons/tp_request/` và `custom_addons/tp_branding/`), kiểm tra khớp 100% SHA256.
2. Cập nhật `LastWriteTime` của toàn bộ tệp phát hành theo thời điểm triển khai để Odoo tự làm mới bundle CSS/JS.
3. Chạy container nâng cấp độc lập:
   ```text
   python3 odoo-bin -c /workspace/docker.odoo.conf -d tp_tanphat_dev -i tp_request -u tp_branding --no-http --stop-after-init --max-cron-threads=0
   ```
   Xác nhận exit code `0` và `0 ERROR/CRITICAL` trong log nâng cấp.
4. Chụp snapshot sau deploy (`after.txt`), xác nhận toàn bộ dữ liệu hiện hữu (`hr_employee`, `res_users`, `res_groups_users_rel`, `maintenance_equipment`, `tp_equipment_proposal`, `tp_hr_attendance_correction`) giữ nguyên 100% và `tp_request` đã cài ở `20.0.1.0.0` (7 loại đề nghị mặc định).
5. Khởi động lại `tp-odoo`, kiểm tra `https://tpone.tadic.vn/web/health` trả `200 {"status":"pass"}` và các đường dẫn `/app/de-nghi/tong-quan`, `/app/de-nghi/cua-toi`, `/app/de-nghi/can-duyet`, `/app/de-nghi/can-thuc-hien`, `/app/de-nghi/theo-doi`, `/app/de-nghi/quan-tri` phản hồi đúng (redirect sạch về `/dang-nhap?redirect=/app/de-nghi/...`).

## 4. Quy trình Rollback (khi gặp sự cố)
1. `docker stop tp-odoo`
2. Khôi phục mã nguồn `tp_branding` từ `source.tar.gz` và gỡ thư mục `custom_addons\tp_request`.
3. Khôi phục database `tp_tanphat_dev` từ `tp_tanphat_dev.dump` bằng `pg_restore --clean --if-exists -U tp_odoo -d tp_tanphat_dev` và khôi phục `filestore.tar.gz`.
4. `docker start tp-odoo` và xác minh lại `https://tpone.tadic.vn/web/health` trả HTTP 200.
