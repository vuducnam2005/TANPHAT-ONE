# TANPHAT ONE — Backup và diễn tập phục hồi dev

Phạm vi OPS-001: Windows dev trên máy này, PostgreSQL 18 và Odoo 20. Source gốc, database `tp_tanphat_dev`, database test và filestore dev giữ nguyên; Odoo dev tạm dừng trong lúc chụp DB/filestore. Script chỉ nhận runtime đúng ownership và cấu hình hiện có, không gọi setup/upgrade/seed.

## Tạo backup

Từ `C:\TANPHAT ONE`, khi runtime dev đang chạy:

```powershell
.\.venv\Scripts\python.exe scripts\backup_restore.py backup
```

Lệnh in đường dẫn backup riêng theo timestamp dưới `.local/ops-001/backups/`. Bộ backup gồm:

- `database.dump`: PostgreSQL custom format, không mang ownership/ACL máy cũ.
- `filestore/`: các blob nội dung chuẩn của Odoo; không sao chép session, upload đang dở hoặc checklist GC.
- `source.tar.gz`: source đã commit tại `source_revision` trong manifest, gồm addon, dependency lock và cấu hình mẫu. Thay đổi runtime chưa commit sẽ bị từ chối; tài liệu/tooling chưa commit không tự nằm trong archive.
- `private/odoo.conf`, `private/dev-secrets.json`: cấu hình và credential phục hồi, chỉ ở máy local. Đây là dữ liệu nhạy cảm; không đưa bộ backup lên Git/GitHub.
- `snapshot.json`: số dòng/fingerprint từng bảng public, tham chiếu attachment và danh sách/chi tiết dự án theo scope admin/reader.
- `manifest.json`: phiên bản source/Python/PostgreSQL, thời gian tạm dừng dev, SHA256 của từng payload. Manifest hoàn chỉnh chỉ được tạo khi backup và bật lại dev thành công.

Script giới hạn quyền thư mục cho tài khoản Windows hiện tại, SYSTEM và Administrators. Backup local chưa mã hóa và chưa bảo vệ khỏi việc mất cả máy; khi chuyển ra thiết bị/kho riêng phải dùng kênh và kho được mã hóa, quản lý khóa tách biệt. Chưa thiết lập lịch backup hoặc retention tự xóa.

Tính nhất quán: chốt source đã commit, đọc scope, tạm dừng đúng process Odoo dev theo PID/config, kiểm tra không còn client DB khác, dump DB và sao chép filestore rồi bật lại Odoo trong `finally`. PostgreSQL dev không dừng. Nếu lỗi, giữ artifact để điều tra và không ghi manifest thành công; không dùng backup thiếu manifest/không đúng checksum để phục hồi.

## Diễn tập từ bộ backup

Thay đường dẫn bằng kết quả lệnh backup:

```powershell
.\.venv\Scripts\python.exe scripts\backup_restore.py rehearse "C:\TANPHAT ONE\.local\ops-001\backups\<timestamp>"
```

Lệnh kiểm checksum trước khi khởi tạo môi trường. Mỗi lượt tạo thư mục mới dưới `.local/ops-001/rehearsals/`, không ghi đè lượt cũ, không drop database dev/test:

| Thành phần | Môi trường phục hồi |
| --- | --- |
| Source | giải nén từ `source.tar.gz` vào `source/` riêng |
| PostgreSQL | cluster mới tại `postgres/`, `127.0.0.1:55442` |
| Database | `tp_tanphat_restore`, owner/app không có quyền superuser |
| Odoo | `127.0.0.1:18089`, dùng source đã giải nén |
| Filestore/session | `runtime/` riêng; filestore đổi tên theo database restore |
| Credential cluster | sinh mới trong `restore-secrets.json`, không dùng role/password cluster gốc |
| Cron/email | neutralize bản sao bằng CLI Odoo; cron = 0, SMTP loopback cổng 1 |

Python/dependency dùng `.venv` hiện tại; đây là phục hồi trên cùng máy với source/config/data cô lập, chưa chứng minh cài mới trên máy hoặc hệ điều hành khác. Dependency lock nằm trong source archive để chuẩn bị diễn tập đó.

## Điều kiện nghiệm thu

`report.json` chỉ đạt sau các kiểm tra:

1. So sánh số dòng và fingerprint toàn bộ bảng public ngay sau `pg_restore`, trước neutralization/khởi chạy Odoo.
2. Đọc từng blob được `ir.attachment` tham chiếu, so sánh SHA1 và kích thước với DB/source backup.
3. Mở trang login, đăng nhập native Odoo bằng credential trong bộ backup, `/me`, list/detail project trả DTO giống snapshot cho reader và admin.
4. Anonymous nhận 401, tham số query sai nhận 400, project ngoài quyền reader nhận 404.
5. Admin tải các attachment đã restore, byte/checksum giống backup.
6. Tạo hai attachment mẫu **chỉ trong bản restore** để kiểm người đọc được tải tệp của project được giao và bị chặn tệp của project ngoài scope.
7. Tắt process Odoo và cluster PostgreSQL của lượt diễn tập; smoke login/API lại trên dev gốc.

Kết quả, log và các probe nằm ngoài Git. Hai cổng phục hồi được trả lại sau lượt chạy; source/DB/filestore restore vẫn được giữ để xem xét. Muốn chạy lại thì dùng lệnh `rehearse` để tạo lượt mới. Không xóa cả `.local` để dọn môi trường.

## Khi lỗi hoặc bị ngắt

- Đọc `operation.log`, `odoo.log`, `postgres.log` trong đúng thư mục lượt chạy; không đưa credential hoặc log thô lên Git/chat.
- Nếu backup bị ngắt trước `finally`, kiểm `.local/odoo.pid`/cổng 18069 và ownership trước khi bật lại. Có thể gọi `scripts/dev.py start` khi cấu hình dev đã được xác nhận, không chạy setup/upgrade để chữa lỗi backup.
- Nếu cổng 55442/18089 còn bị chiếm, kiểm PID/cmdline và đúng thư mục `postgres/`/`restore.conf` của lượt đó trước khi dừng; không dừng tất cả process Python/PostgreSQL trên máy.
- Nếu checksum/fingerprint sai, giữ nguyên artifact, điều tra và tạo bộ backup mới; không sửa manifest để biến kiểm tra lỗi thành đạt.
- Nếu backup thiếu credential, filestore hoặc source revision phù hợp thì chưa đủ để phục hồi. Chưa dùng dữ liệu production với script dev này.

## Lượt đã kiểm chứng ngày 28/10/2026

| Bằng chứng | Kết quả |
| --- | --- |
| Change ID | `CHG-20261028-003` |
| Source phục hồi | `d9e8ccdc83157624d84bde72a494072a82a8abde`, source archive 208.319.903 byte |
| Backup | `.local/ops-001/backups/20261028T062821364112Z` |
| Database dump | 3.043.333 byte; checksum toàn bộ 32 payload đạt |
| Bảng DB | 314 bảng public khớp số dòng và fingerprint trước neutralize |
| Tệp | 37 tham chiếu attachment, 27 blob; tải 37 tệp qua HTTP khớp SHA1/kích thước |
| API/quyền | planner/admin login, `/me`, list/detail DTO; 401/400/404 và 2 probe attachment theo project scope đạt |
| Gián đoạn dev | 18,95 giây; Odoo được bật lại, smoke dev và hash nghiệp vụ/config đạt |
| Report private | `.local/ops-001/rehearsals/20261028T064405723351Z/report.json` |
| Kết thúc | Odoo/PostgreSQL restore đã dừng, hai cổng 18089/55442 không còn listener |
| Tooling | 21 unit tests và Ruff đạt; test gồm corrupt/missing payload, traversal/link và chặn báo đạt khi kiểm tra dev/cleanup thất bại |

Đăng nhập có thể ghi lịch sử xác thực/session như hành vi bình thường của Odoo. Việc giữ nguyên được kiểm chứng với các bảng nghiệp vụ dự án/phân công/hạng mục/phòng ban/attachment và hash cấu hình/credential, không tuyên bố mọi byte của toàn bộ DB dev bất biến sau login.

## Việc tiếp theo trước production

Chốt RPO/RTO, vị trí backup ngoài máy, mã hóa/quyền truy cập, lịch/retention, cảnh báo backup lỗi; thử phục hồi trên host tách biệt và kiểm chứng kết nối tích hợp/HTTPS. Những việc này không được coi là hoàn tất chỉ từ OPS-001 local.
