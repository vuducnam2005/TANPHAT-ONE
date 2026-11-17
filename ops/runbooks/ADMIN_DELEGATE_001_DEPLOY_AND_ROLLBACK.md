# ADMIN-DELEGATE-001 — triển khai và khôi phục

Ngày 17/11/2026, CHG-20261117-004. Người dùng đã giao áp main18069, push Git và
deploy PCserver; không tự cấp cho người thật. Theo
[policy giao bản](../../docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md), chỉ
giao phần đã hoàn chỉnh, giữ diff và dữ liệu ngoài scope.

## Thành phần và điều kiện

- Addon `tp_admin_delegation` 20.0.1.0.0 phụ thuộc `tp_hr_workspace`,
  `tp_equipment`, `tp_reporting`; dependency nghiệp vụ giữ bản hiện có.
- Hook nhỏ ở workflow hợp đồng, guard/caller Kho và Home. Gói triển khai phải
  có đủ các file trong manifest release; không copy cả cây working tree.
- Không sửa core Odoo, proxy, tunnel, DNS, cấu hình DB, nhóm hoặc assignment
  của người dùng thật. Không seed actor/credential lên main/server.
- Backup đúng DB + filestore + source/config trước cài. Kiểm `pg_restore -l`
  và checksum. Snapshot user/group/identity/assignment/nghiệp vụ trước/sau.
- Xem [acceptance](../../docs/demo/ADMIN_DELEGATE_001_ACCEPTANCE.md) để biết
  ca đã chạy và giới hạn; không dùng handoff checker thay test bảo mật.

## Local main

Main là `tp_tanphat_dev`, `.local/odoo.conf`, cổng18069, PG55432. Dừng đúng
tiến trình có config/DB này, không dừng PostgreSQL hoặc Odoo của phiên khác.
Backup ở `.local/admin-delegate001/backup-dev/`. Bản sao cấu hình chỉ ở thư
mục private; không in hoặc stage lên Git.

```powershell
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -i tp_admin_delegation --no-http --stop-after-init --max-cron-threads=0 --logfile=.local/admin-delegate001/install-dev.log
```

Khởi động lại đúng runtime18069. Kiểm health/login/Home/HR detail bằng phiên
có sẵn, chỉ đọc. Đối chiếu fingerprint; không có dòng ledger và không thay
user/group/phòng ban. Browser smoke không tạo nhân viên hoặc cấp thử ở main.

## PCserver

Xác minh `server-pc`, Docker `tp-odoo`, `tp-postgres`, workdir `/workspace`,
config `/workspace/docker.odoo.conf`, bind source `C:\Projects\TANPHAT-ONE`
và filestore `docker_data\filestore` → `/var/lib/odoo/filestore`.
Không dùng cấu hình container cũ `/etc/odoo/odoo.conf`.

1. Gói source lấy đúng file/hunk đã commit/push, kèm SHA256 từng file.
   So hash file cũ với baseline dự kiến; có sai lệch thì kiểm trước khi ghi.
2. Dừng riêng Odoo, backup mới trên server: DB dump, filestore, source/config.
   Không dùng backup local thay backup server hoặc backup trước khôi phục media.
3. Chép gói đúng phạm vi, kiểm checksum; chạy một tiến trình upgrade khi
   web runtime đã dừng, cùng image/mount/network và config thực. Chỉ cài
   `tp_admin_delegation`; không chạy test hoặc đưa fixture lên máy chủ.
4. Khởi động lại `tp-odoo`, giữ `tp-tunnel`. Kiểm registry/log/health, fingerprint,
   ledger0 và inventory mọi blob. Asset build có thể tạo attachment kỹ thuật;
   mọi blob nghiệp vụ có trước phải còn và hash đúng.
5. Kiểm public login/session/Home/HR detail/ảnh và file đã có quyền.
   Admin đăng nhập qua public để giữ `web.base.url`; không login admin qua LAN.
   Public: `https://hybrid-send-ready-ballot.trycloudflare.com`.

## Khôi phục

Nếu còn runtime nhưng cần thu quyền thêm: Quản trị chính thu hồi qua action có
lý do. Không xóa ledger hoặc đổi user/group để giả thu hồi. Không uninstall
addon bảo mật trong khi còn quyền đang hiệu lực.

Nếu cài/upgrade hỏng, giữ Odoo dừng; giữ log và snapshot lỗi, khôi phục source
cũ từ backup đúng môi trường. Nếu schema đã thay và registry không tải được,
khôi phục DB dump cùng filestore của chính backup đó trong maintenance có
kiểm soát; không restore test đè main/server. Giữ bản hiện tại trước restore,
không xóa dữ liệu phát sinh sau backup mà chưa đối chiếu. Khởi động lại đúng
Odoo rồi kiểm quyền, file và public; không restart tunnel.

Media có runbook riêng: restore blob là add-only theo checksum; code rollback
không tự xóa149 blob đã khôi phục hợp lệ.

## Kết quả lần áp

Đang cập nhật theo log thực tại `.local/admin-delegate001/`; bảng acceptance
là nguồn kết luận môi trường đã áp/chưa áp. Chưa ghi PASS từ lệnh chuẩn bị.
