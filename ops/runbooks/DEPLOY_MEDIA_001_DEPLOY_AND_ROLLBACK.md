# DEPLOY-MEDIA-001 — Triển khai và rollback filestore

Ngày 17/11/2026. Đã áp server-pc trong quyền người dùng giao trực tiếp. [Acceptance](../../docs/demo/DEPLOY_MEDIA_001_ACCEPTANCE.md). Không sửa application code, database nghiệp vụ, quyền, tunnel hay DNS.

Topology đã kiểm qua `docker inspect`: `server-pc`, Docker `tp-odoo`, workdir `/workspace`, command `python3 odoo-bin -c /workspace/docker.odoo.conf`, DB `tp_tanphat_dev`; bind `C:\Projects\TANPHAT-ONE` → `/workspace` và `C:\Projects\TANPHAT-ONE\docker_data\filestore` → `/var/lib/odoo/filestore`. `data_dir=/var/lib/odoo`, đường blob `/var/lib/odoo/filestore/tp_tanphat_dev/<2hex>/<40hex>`. Không dùng config `/etc/odoo/odoo.conf` của runbook cũ.

Trước thay đổi đã lưu inventory metadata + tồn tại/SHA1/size, kiểm nguồn local cùng database canonical từng checksum. Origin có149blob thiếu/641rows ảnh và attachment,0mismatch; local có đủ149blob khớp chính xác metadata server. HTTP origin và public cùng trả0byte trước sửa, log origin báo file thiếu. Mount đúng nhưng nội dung chưa đủ; không cần sửa mount hoặc bypass ACL.

Backup server trước phục hồi tại `C:\TANPHAT-backups\deploy-media001\20261117\`:

| Artifact | Kích thước / kiểm |
| --- | --- |
| `tp_tanphat_dev-pre.dump` |8.953.006byte, `pg_restore -l` thành công; danh sách tại `restore-list.txt` |
| `filestore-pre.tar.gz` |4.654.250byte, filestore hiện có của đúng DB |
| `code-config-pre.tar.gz` |2.009.710byte, toàn `custom_addons` và `docker.odoo.conf` riêng tư |
| `origin-before.json` |296.510byte, metadata và tình trạng blob trước sửa |
| `SHA256SUMS.json` |SHA256 các artifact; bản sao private tại `.local/deploy-media001/backup-SHA256SUMS.json` |

Config backup có credential nên chỉ lưu ngoài Git. Không in credential/cookie/token hoặc nội dung ảnh thật vào log public. Backup này không thay backup mới trước deployment addon tiếp theo.

Quy trình đã chạy bằng script private `.local/deploy-media001/`:

1. `inventory.py` kết nối SQL read-only lấy metadata `ir_attachment`, kiểm file/hash và chỉ lưu hash của `web.base.url`. Chạy riêng với `.local/odoo.conf` tại local và `/workspace/docker.odoo.conf` trong container; không khởi tạo/upgrade Odoo.
2. `build_restore.py` lấy **chỉ target thiếu**, kiểm SHA1+size từ metadata server với file local, xuất `restore-manifest.json` và `verified-blobs.tar.gz`.149blob,125.365.887byte;0nguồn thiếu. Không đưa blob riêng chỉ có local lên server.
3. `backup.ps1` dump/verify DB, archive filestore và code/config như bảng trên. Không restore DB.
4. `restore.py` trong container recheck metadata live, đường dẫn regex2hex/40hex và toàn bộ archive trước ghi. Nếu target đã xuất hiện hoặc blob tốt bị drift thì dừng. Ghi bằng `open('xb')`, không overwrite; hash/size mỗi file sau ghi và lưu tiến độ `restore-result.json`. Script nằm server `/workspace/.local/deploy-media001/`; các script dùng config để đọc secret, không nhận secret trên CLI.
5. Inventory sau phục hồi660/660rows và168/168blob đúng;19blob đã tốt giữ nguyên,149blob thêm. `http_after.py`126download cùng ID local/origin/public đúng hash/size, private/auth/cache/Range smoke đạt.
6. `docker restart tp-odoo`, không restart tunnel/postgres. Health200; inventory sau restart vẫn0missing0mismatch; public browser giải mã ảnh thật và SVG hợp lệ. `verify_restart.py` xác nhận base.url hash giữ,0FileNotFoundError từ lúc restart tới smoke.

Không authenticate admin bằng LAN. Probe origin dùng session lấy qua public và header Host public; không đổi `web.base.url`. Local18069 đã có đủ blob nên không phục hồi gì.

Rollback chọn mức nhỏ nhất: đợt này chỉ thêm blob, không thay code/config/DB. Khi thực sự cần hoàn tác, khóa phối hợp tác vụ ghi, chụp inventory mới, đối chiếu `restore-result.json` và chỉ xóa **chính149đường được tạo trong manifest**, sau khi xác nhận file hiện vẫn SHA1+size khớp và không có tham chiếu mới cần giữ. Giữ backup và nguồn local để phục hồi lại. Không xóa prefix directory hoặc cả filestore; không xóa blob khác dù trùng tên theo suy đoán. Nếu file drift, dừng để đánh giá. Không restore DB để hoàn tác ảnh. Xóa các blob này sẽ làm mất ảnh hiện được tham chiếu nên **chưa chạy rollback trên server**; không gọi đây là rollback đã diễn tập.

Giới hạn chuyển giao: nguồn149blob đã xác minh đủ cho metadata server hiện tại; không chứng minh backup/deploy tương lai tự mang filestore đúng. Mỗi lần chuyển DB phải inventory và kiểm blob cùng DB; dump PostgreSQL không chứa file filestore. PDF/DOCX/XLSX đã test fixture riêng trên18079 nhưng server chưa có mẫu thật, ghi NOT_RUN qua tunnel. Test fixtures đã cleanup; acceptance riêng lưu chi tiết.
