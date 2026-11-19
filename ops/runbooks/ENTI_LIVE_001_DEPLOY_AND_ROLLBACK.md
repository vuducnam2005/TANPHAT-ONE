# Quy trình Giao bản và Hoàn nguyên ENTI-LIVE-001 (20.0.3.4.0)

- **Mã thay đổi:** `CHG-20261119-025`
- **Addon:** `tp_hr_attendance` `20.0.3.4.0`
- **Mục tiêu:** Tích hợp dữ liệu chấm công ENTI thật, tự động đồng bộ theo lịch 1 phút và cập nhật giao diện không cần F5.

---

## 1. Nguyên tắc triển khai

1. Chỉ deploy code đã kiểm tra cú pháp, lint và unit test.
2. Không ghi đè hoặc stage diff của các phân hệ khác (`tp_equipment`, `tp_hr_workspace`, `tp_reporting`, `tp_web_home`, `tp_branding`).
3. Backup đầy đủ database trên PC server trước khi nâng cấp module:
   - Dùng `docker exec tp-postgres pg_dump -U tp_odoo -Fc tp_tanphat_dev > C:\TANPHAT-backups\enti-live001\...`
4. Chạy nâng cấp addon qua lệnh Odoo CLI `-u tp_hr_attendance --stop-after-init`.
5. Migration `migrations/20.0.3.4.0/post-migrate.py` sẽ tự động xóa bỏ ràng buộc DB `tp_hr_attendance_source_live_off`.
6. Khởi động lại container `tp-odoo` và kiểm tra endpoint `/web/health` cùng các URL public.

---

## 2. Các bước triển khai chi tiết

### Bước 1: Commit & Push Git từ máy local
```powershell
git add custom_addons/tp_hr_attendance/
git add scripts/tests/test_enti_pure.py
git add docs/demo/ENTI_LIVE_001_ACCEPTANCE.md
git add ops/runbooks/ENTI_LIVE_001_DEPLOY_AND_ROLLBACK.md
git add docs/PROJECT_STATUS.md docs/CHANGELOG.md

git commit -m "feat(attendance): ENTI-LIVE-001 live ENTI attendance sync, auto-cron & dynamic UI (20.0.3.4.0)"
git push origin main
```

### Bước 2: Tạo bản sao lưu dự phòng trên PC Server
```powershell
ssh server-pc "powershell -Command New-Item -ItemType Directory -Force -Path C:\TANPHAT-backups\enti-live001"
ssh server-pc "docker exec tp-postgres pg_dump -U tp_odoo -Fc tp_tanphat_dev > C:\TANPHAT-backups\enti-live001\tp_tanphat_dev_pre_enti_live001.dump"
```

### Bước 3: Đồng bộ mã nguồn lên PC Server
```powershell
# Chép mã nguồn custom_addons/tp_hr_attendance lên server-pc (hoặc git pull nếu server-pc dùng git tracking)
scp -r custom_addons/tp_hr_attendance/* server-pc:C:/Projects/TANPHAT-ONE/custom_addons/tp_hr_attendance/
```

### Bước 4: Nâng cấp module trên PC Server
```powershell
ssh server-pc "docker exec tp-odoo python3 odoo-bin -c /workspace/docker.odoo.conf -u tp_hr_attendance --stop-after-init"
```

### Bước 5: Khởi động lại dịch vụ Odoo
```powershell
ssh server-pc "docker restart tp-odoo"
```

### Bước 6: Kiểm tra sức khỏe hệ thống
```powershell
# Kiểm tra health cục bộ trên server
ssh server-pc "curl.exe -s -o NUL -w '%{http_code}' http://127.0.0.1:8069/web/health"

# Kiểm tra URL Cloudflare Public
curl.exe -I https://eight-championships-launches-plaintiff.trycloudflare.com/web/health
```

---

## 3. Quy trình cấu hình tài khoản ENTI sau triển khai

1. Đăng nhập Odoo bằng tài khoản Quản trị viên (Admin) hoặc Quản lý nhân sự.
2. Điều hướng tới menu: **Quản trị chấm công → Cấu hình kết nối ENTI**.
3. Điền **Số điện thoại** và **Mật khẩu** tài khoản ENTI được cung cấp.
4. Bấm **"Kiểm tra kết nối"**:
   - Hệ thống sẽ gọi API login và lấy danh sách ứng dụng.
   - Nếu hiển thị: `Kết nối thành công! Tìm thấy ứng dụng: Công ty Cổ phần Tấn Phát...`, kết nối mạng và tài khoản hoàn toàn chính xác.
5. Bấm **"Lưu cấu hình bảo mật"**:
   - Mật khẩu được ghi vào file cấu hình bảo mật trên server hoặc hệ thống thông số bí mật.
   - Trạng thái chuyển sang: **Đã cấu hình**.
6. Để chạy ngay:
   - Trong wizard, chọn khoảng ngày (mặc định từ đầu tháng đến hiện tại) và bấm **"Đồng bộ ngay khoảng ngày này"**.
   - Hoặc tại trang **"Nguồn dữ liệu"**, bấm nút **"Đồng bộ ngay"**.
7. Kiểm tra đối chiếu nhân sự:
   - Vào menu **"Quản trị chấm công → Đối chiếu nhân viên ENTI"**.
   - Xem danh sách nhân viên Odoo được hệ thống tự động gợi ý.
   - Bấm **"Xác nhận"** để đưa ngày công vào hồ sơ nhân viên chuẩn.

---

## 4. Kế hoạch Hoàn nguyên (Rollback Plan)

Nếu có bất kỳ sự cố không tương thích:
1. Dừng container Odoo:
   `ssh server-pc "docker stop tp-odoo"`
2. Phục hồi lại mã nguồn `tp_hr_attendance` bản trước từ commit hoặc backup.
3. Nếu cần khôi phục dữ liệu:
   `ssh server-pc "docker exec -i tp-postgres pg_restore -U tp_odoo -d tp_tanphat_dev --clean < C:\TANPHAT-backups\enti-live001\tp_tanphat_dev_pre_enti_live001.dump"`
4. Khởi động lại container Odoo:
   `ssh server-pc "docker start tp-odoo"`
5. Xác minh lại `/web/health` trả về 200 OK.
