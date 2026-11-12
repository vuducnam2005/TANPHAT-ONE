# OPS-CLEAN-001 — Dữ liệu sạch và hai database local

Ngày 10/11/2026. Phạm vi do người dùng xác nhận: xóa dữ liệu nghiệp vụ mẫu,
giữ tài khoản, quyền nhóm/vai trò và cấu hình; giữ một database chính và một
database kiểm thử. Kết quả vận hành cuối cùng ghi tại `docs/PROJECT_STATUS.md`.

## Môi trường chuẩn

| Mục đích | Database | Giao diện | Cấu hình riêng |
| --- | --- | --- | --- |
| Bản chính trên máy phát triển | `tp_tanphat_dev` | <http://127.0.0.1:18069/odoo> | `.local/odoo.conf` |
| Kiểm thử trước khi áp bản chính | `tp_tanphat_test` | <http://localhost:18079/odoo> | `.local/test/odoo.conf` |

Hai môi trường dùng cluster do workspace sở hữu tại `127.0.0.1:55432`, nhưng
tách database, filestore và session. Test tắt cron, SMTP chuyển loopback cổng9,
UUID khác và URL riêng. Tài khoản/mật khẩu test được sao từ bản chính tại thời
điểm chuẩn hóa; về sau thay đổi ở một bên không tự đồng bộ sang bên kia.
Main mở bằng `127.0.0.1`, test mở bằng `localhost` để trình duyệt giữ cookie
khác nhau. Cookie không phân biệt cổng; nếu mở cả hai bằng cùng hostname thì
dùng hai browser profile riêng để tránh phiên đăng nhập ghi đè nhau.
`postgres`, `template0`, `template1` là database hệ thống PostgreSQL, phải giữ.
Các bảng Odoo trong từng database vẫn đầy đủ; không thu gọn còn hai bảng.

Mở lại bản chính khi PostgreSQL đã sẵn sàng:

```powershell
Set-Location 'C:\TANPHAT ONE'
.\.venv\Scripts\python.exe scripts\dev.py status
.\.venv\Scripts\python.exe scripts\dev.py start
```

Chỉ chạy `start` khi cổng tương ứng đang dừng. Mở test trong terminal riêng:

```powershell
Set-Location 'C:\TANPHAT ONE'
.\.venv\Scripts\python.exe odoo-bin -c .local\test\odoo.conf -d tp_tanphat_test
```

Terminal test dùng Ctrl+C để dừng. Runtime đã mở nền bởi lần dọn này được ghi
PID ở `.local/test/odoo.pid`; trước khi dừng theo PID phải đối chiếu command line
đúng `odoo-bin`, đường dẫn workspace và `.local/test/odoo.conf`. Không dừng toàn
bộ Python/PostgreSQL. `dev.py stop` dừng cả cluster, vì vậy không dùng khi test
hoặc tác vụ khác còn cần PostgreSQL.

## Dữ liệu được dọn và phần phải giữ

- Dọn theo namespace/binding mẫu đã đối chiếu source, sau đó mở rộng các quan
  hệ phụ thuộc: dự án/WBS, CRM, hợp đồng/phụ lục, giao khoán, sản lượng, nghiệm
  thu, đề nghị thanh toán, kế hoạch, chứng chỉ, nghĩa vụ, nhân viên/chi phí mẫu,
  bút toán nháp mẫu, lịch, thảo luận, tệp và dashboard mẫu liên quan.
- Giữ tài khoản, mật khẩu, nhóm, ACL/rule, quyền công ty và vai trò HEAD của
  phòng ban. Assignment/grant riêng của dự án bị xóa phải dọn theo dự án đó;
  không chuyển các quyền này sang dự án mới hoặc tự cấp lại quyền tiền.
- Giữ công ty, phòng ban, danh mục, thuế, hệ thống tài khoản/journal, sequence,
  module, menu/view, lịch sử bảo mật và cấu hình. Nhân viên mẫu khác tài khoản:
  xóa 12 hồ sơ nhân viên mẫu không xóa 25 tài khoản đang giữ.
- Giữ dự án kỹ thuật Internal (ID3), hai loại công việc Training/Meeting
  (ID3/4) phục vụ timesheet chuẩn. Đây không phải dự án kinh doanh còn sót.
- Giữ liên hệ của tài khoản/công ty cùng cha và commercial partner bắt buộc.
  Có thể còn tên mang chữ DEV trong danh mục/cấu hình; không tự đổi dữ liệu
  định danh để làm giao diện trông trống hoàn toàn.
- Giữ provenance `tp.kd.dataset*`; các entry trỏ dữ liệu đã dọn được đánh dấu
  `unlinked`. Giữ nguồn nhân sự thật 39 dòng ngoài database/Git, chưa nhập HR.
- Không reset sequence, không gỡ addon, không xóa bảng hoặc tắt ràng buộc FK.
  Việc xóa lịch sử của hồ sơ mẫu trong lần bảo trì này không mở quyền xóa hồ
  sơ đã chốt cho người dùng ứng dụng.

## Bằng chứng và bản sao lưu riêng tư

Thư mục `.local/ops-clean001/` bị Git ignore và hạn chế ACL Windows.

| Artifact | Vai trò |
| --- | --- |
| `inventory-before.json`, `business-before.json` | Kiểm kê nguồn trước dọn |
| `snapshot-20261110T090532Z/` | Source đang làm, cấu hình riêng, dump và filestore; đã restore khớp 592 bảng/295 tham chiếu blob |
| `database-archives/`, `final-database-archives/` nếu có | Dump và filestore từng database cũ |
| `final-archive-verification.json` | Đường dẫn/hash bản sao lưu khớp lần cuối trước bỏ database |
| `final-precleanup-main/` | Database và filestore chính ngay trước transaction dọn |
| `clean-main/` | Database chính sau dọn, làm nguồn dựng test sạch |
| `cleanup-plan-*.json`, `cleanup-result-*.json` | ID, phạm vi, số lượng, fingerprint phần giữ lại |
| `restore-evidence.json`, `canonical-test-result.json` | Kiểm chứng phục hồi và cách ly test |
| `smoke-*.json`, `smoke-*.png` | Kiểm tra đăng nhập, màn hình sau dọn |
| `dropped-databases.json`, `final-result.json` | Nhật ký database thực sự đã bỏ và danh sách cuối |

Các script thao tác một lần cũng nằm trong thư mục private này. Không tự chạy
lại: chúng khóa đúng manifest/ID trước dọn và được thiết kế để dừng khi dữ liệu
khác. Chúng không phải công cụ xóa dữ liệu cho người dùng nghiệp vụ.

Kết quả ngày10/11: bỏ32database phụ, thay test cũ và bỏ bản diễn tập tạm;
giữ25users/944quy tắc `ir.access`, main/test sạch đã smoke12checks mỗi bên.
Main từng có timeout/dialog hết phiên sau khởi động; lần đăng nhập lại đủ12
checks đạt. Chưa chốt nguyên nhân hoặc sửa code auth; giữ ảnh/log private để
theo dõi riêng, không xem smoke này là kiểm thử đầy đủ toàn bộ ứng dụng.

Transaction dọn giữ FK hoạt động, khóa ghi khi kiểm chứng, chỉ commit nếu dữ
liệu ngoài phạm vi giữ nguyên. Đã diễn tập trên bản phục hồi trước khi áp main.
Archive database cũ được kiểm checksum dump, danh sách restore và tất cả blob;
không tuyên bố đã khởi động HTTP/restore đầy đủ cả 34 database cũ. Bản main và
test chuẩn có kiểm chứng phục hồi thực tế riêng.

Rollback: chọn đúng manifest/database, kiểm SHA256 và blob; giữ lại trạng thái
hiện tại trước mọi ghi đè; dừng Odoo đúng môi trường, phục hồi cả dump và
filestore đồng bộ. Ưu tiên diễn tập trên test chuẩn sau khi sao lưu test, đối
chiếu fingerprint/đăng nhập rồi mới quyết định phục hồi bản chính. Không ghi đè
database đang chạy hoặc dùng SQL xóa chéo các bảng để hoàn tác.

Backup hiện nằm cùng máy: phải sao chép có kiểm checksum sang vị trí sao lưu
riêng trước khi cần chống mất ổ đĩa. Không đưa credential/dump/filestore lên Git.
Chưa xóa các thư mục filestore/log/config lịch sử trên ổ đĩa; đây là backup và
artifact vận hành, không còn là database hiển thị trong pgAdmin.

## Quy trình phát triển sau dọn

1. Đọc status/workflow, nhận quyền sử dụng test; mỗi thời điểm chỉ một tác vụ
   ghi/migrate test. Các AI không chạy test/module-upgrade đồng thời.
2. Test dùng `tp_tanphat_test`; dữ liệu giả chỉ tạo tại đó. Chuẩn bị acceptance
   và backup test trước schema migration. Không tự tạo database theo tên task.
3. Dừng HTTP test trước lệnh Odoo `--stop-after-init`/module test. Cấu hình phải
   chỉ đúng `.local/test/odoo.conf`, `-d tp_tanphat_test`, dbfilter test, data dir
   test và `--http-port=18079` nếu công cụ yêu cầu override.
4. Không chạy lại `setup`, `upgrade`, `seed_dev` hoặc script dữ liệu cũ để mở
   môi trường: helper lịch sử có thể tạo lại fixture hoặc đồng bộ mật khẩu.
   `dev.py test` là helper nền lịch sử; chỉ dùng sau khi kiểm cấu hình/ownership,
   dừng listener test và đánh giá cách dùng data dir, không coi là lệnh chuẩn
   cho mọi addon hiện hành.
5. Khi test đạt và có phạm vi áp dev được giao: backup main, áp đúng source và
   module migration đã kiểm thử. **Không restore test đè main**; không đưa test
   fixture, account hoặc grant giả sang main.
6. Đối chiếu dữ liệu/quyền sau áp, smoke giao diện và cập nhật workflow. Muốn
   reset test phải backup rồi phục hồi lại main sạch/có kiểm chứng; không dọn
   dữ liệu main định kỳ theo script bảo trì lần này.

HR-001 S1 tiếp tục từ schema/list/form và tài khoản giả trên test; kiểm kê HR
S0 ghi 12 nhân viên là số liệu lịch sử trước dọn. Main sau dọn chưa có roster
thật, chưa phải môi trường production hoặc nghiệm thu nghiệp vụ.
