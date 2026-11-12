# HR-001 — Nhập roster, áp main và rollback

Ngày 11/11/2026. Runbook cho người vận hành đã được giao phạm vi HR-001; không
phải lệnh tự động chạy khi mở phiên. Kết quả thực tế và cổng còn mở ghi tại
[PROJECT_STATUS](../../docs/PROJECT_STATUS.md), cùng acceptance HR-001 được bàn
giao. Không suy “PASS” hoặc “đã áp main” từ sự tồn tại của script/runbook.

## Môi trường và điều kiện

- Chỉ `tp_tanphat_dev`/18069 (`.local/odoo.conf`) và
  `tp_tanphat_test`/18079 (`.local/test/odoo.conf`) trên cluster workspace55432.
  Không tạo DB thứ ba; giữ database hệ thống. Không restore test đè main.
- Một người/tác vụ ghi test tại một thời điểm. Dừng đúng process/config test
  trước restore, upgrade hoặc Odoo tests; không dùng `dev.py stop` làm dừng
  cluster mà main đang sử dụng. Không reset password, seed hoặc load demo.
- Main mở `127.0.0.1`, test mở `localhost` hoặc profile trình duyệt riêng để
  tránh cookie Odoo cùng hostname. Test giữ data dir/filestore/session riêng,
  cron tắt và SMTP loopback cổng9.
- Đọc [quy tắc dữ liệu sạch](SAMPLE_DATA_CLEANUP_AND_TEST.md), prompt và manifest
  hiện hành; kiểm status Git/runtime/checkpoint trước thao tác. Không commit/push.

## Artifact riêng tư

`.local/hr001/` bị Git ignore và ACL hạn chế. File nguồn thật nằm ngoài Git;
checksum chuẩn trong prompt HR-001 và `import_orm.py`. Khi checksum đổi phải
đối chiếu lại, không dùng manifest cũ.

| Artifact | Công dụng |
| --- | --- |
| `ops.py` | Inventory, backup nhất quán, restore vào test chuẩn |
| `*-inventory.json` | Identity/binding/FK và kết quả kiểm blob riêng tư |
| `account-manifest.json`, `department-manifest.json` | Giữ/archive/pending và scope phòng ban |
| `scenario-catalog-bindings.json` | XMLID mẫu đối chiếu source và ID runtime |
| `cleanup_orm.py` | Preview hoặc cleanup ORM có cờ áp dụng riêng |
| `import_orm.py` | Preview hoặc nhập nguồn/hash và mapping đã khóa |
| `backup-*/manifest.json`, `baseline.json` | Hash payload, fingerprint tất cả bảng, blob refs |
| `restore-evidence.json` | Kiểm phục hồi trước neutralize và trạng thái cách ly |
| `neutralize_test.py` | Bước cách ly test có guard sau restore đã kiểm |
| `*-cleanup-result.json`, `*-import-*.json` | Kết quả thao tác, ID private và số create/update/skip/conflict |

Không chép PII, dump, cấu hình chứa bí mật hoặc ảnh tên thật vào Git. Thư mục
backup lỗi/chưa có manifest hoàn chỉnh không phải bản rollback hợp lệ. Backup
cùng máy không bảo vệ mất ổ đĩa; sao chép sang vị trí backup riêng có checksum
khi cần bảo vệ rủi ro đó.

## Backup và diễn tập restore trên test

Từ `C:\TANPHAT ONE`, kiểm script hiện tại trước dùng. Hai lệnh đầu đọc DB và
ghi artifact private, không sửa nghiệp vụ:

```powershell
.\.venv\Scripts\python.exe .local\hr001\ops.py inventory tp_tanphat_dev
.\.venv\Scripts\python.exe .local\hr001\ops.py backup tp_tanphat_dev
```

Backup export một PostgreSQL REPEATABLE READ snapshot cho dump và fingerprint
tất cả bảng; kiểm attachment SHA1/size, chép filestore, config và source đang
làm, ghi SHA256 payload và kiểm restore TOC. Main HTTP có thể chạy trong bước
đọc nhất quán; giữ các blob nguồn cho tới khi chép xong. Ghi đường dẫn backup
thực tế trả về, không đoán timestamp.

1. Nhận quyền ghi test, dừng đúng HTTP test và bảo đảm không còn session DB test.
2. Chạy `ops.py restore-test` với đường dẫn backup main đã chọn. Đây là thao
   tác ghi đè **test hiện có**; script tự backup test trước reset, từ chối khi
   còn listener/session và không tạo DB mới.
3. Restore phải đạt kiểm hash dump/payload, fingerprint mọi bảng và SHA1/size
   mọi blob trước neutralize. Script dùng `--transaction-size=100` để tránh
   giới hạn lock của cluster, không tự tăng cấu hình PostgreSQL. Nếu lỗi giữa
   các transaction, test có thể dở dang: giữ HTTP dừng, xem log và phục hồi
   bản test đã lưu; không tiếp tục migration trên trạng thái chưa xác minh.
   Nếu test đã có schema HR mới hơn snapshot main, helper chỉ cho phép đúng
   hai bảng thừa đã review `tp_hr_import_line`/`tp_hr_import_batch`: sau backup,
   bỏ FK `hr_employee.tp_import_batch_id` đã xác minh rồi drop line trước batch,
   không CASCADE. Extra sequence `ir_sequence_004` chỉ được bỏ khi không có phụ thuộc và không nằm trong archive; gate kiểm toàn bộ sequence names/counters theo TOC/SEQUENCE SET. Bảng/sequence/FK ngoài tập review làm dừng thao tác.
4. Sau đối chiếu đúng, neutralize test: UUID mới; `database.is_neutralized=True`;
   `web.base.url=http://localhost:18079`; freeze URL; tắt cron và mail server.
   Kiểm lại config test riêng/SMTP9. `restore-test` ghi yêu cầu neutralize,
   **không tự hoàn tất bước này**; ghi evidence sau thực hiện. Không thay auth,
   group/company hoặc tạo account trong neutralize.
   Chạy `.\.venv\Scripts\python.exe .local\hr001\neutralize_test.py` khi có
   fresh restore evidence. Helper kiểm lại toàn bộ rowsets/blob trước ghi;
   nếu test đã drift thì dừng, không đánh dấu đã neutralize.
5. Giữ HTTP test dừng cho upgrade/tests kế tiếp. Bàn giao quyền ghi rõ ràng;
   không gọi helper clone/restore lịch sử tạo database theo task.

Ví dụ cấu trúc lệnh (thay đường dẫn bằng backup đã kiểm, không chạy placeholder):

```powershell
.\.venv\Scripts\python.exe .local\hr001\ops.py restore-test '<backup-main-thuc-te>'
```

## Cleanup, migration và nhập có kiểm soát

1. Đọc manifest và runtime mới; preview `cleanup_orm.py` trong Odoo shell đúng
   test. Không đặt cờ `HR001_APPLY` khi chỉ preview. Script kiểm binding mẫu
   cộng provenance login, chặn employee có `tp_source_code`, giữ system/admin
   và năm alias KH-KD pending. Chỉ áp dụng sau rà manifest/backup.
2. Khi áp cleanup, dùng cờ `HR001_APPLY=True` rồi thực thi helper trong shell
   đúng môi trường. Employee mẫu dùng ORM native để dọn version/resource;
   catalog/contact có liên kết dùng chung được giữ. Archive user mẫu giữ
   login/password/group/company và lịch sử. Nếu actor có HEAD động, revoke
   bằng `write(active=False, reason=...)` hiện hữu để tạo audit; không chuyển
   HEAD sang người khác. Giữ audit riêng kết quả và kiểm blob/FK sau dọn.
3. Upgrade đúng addon đã kiểm theo lệnh giao trong acceptance trên test, không
   chạy setup/seed. Odoo model/view/assets/backend suite và các kiểm bảo mật
   phải đạt trước nhập/rollout; backend demo loader bị guard cả RPC.
4. Preview `import_orm.py` trong shell đúng test, mặc định rollback. Helper
   kiểm hash nguồn, 78 dòng/39 identity/chín nhóm, mapping Ban Kinh Doanh→ID18,
   Phòng Thiết kế→ID20 và đúng công ty. Preview không ghi employee.
5. Chỉ khi preview và mapping đúng, đặt `HR001_IMPORT_APPLY=True` rồi thực thi
   helper. Helper ghi evidence private, kiểm 39 employee/chín nhóm, version,
   TP10060, không tự link user hoặc tạo lương/ngày hợp đồng từ nguồn thiếu.
   Luồng UI chung có thể áp dòng hợp lệ và trả conflict; không bỏ qua conflict
   count. Helper rollout nguồn chốt yêu cầu conflict0 trước commit.
6. Kiểm nhập lại không tạo trùng/version rác; delta nguồn phải review, sửa tay
   được giữ. Batch preview/applied không thay file; tạo batch mới khi cần sửa
   nguồn hoặc thử lại dòng lỗi. Không gán danh tính cho năm alias pending.
7. Kiểm browser desktop/mobile, CRUD/archive/restore, bản thân/người khác,
   private version/file/chatter/export/company; dashboard/filter/drilldown/XLSX
   cùng domain; KH-KD admin/account được giữ hoạt động. Fake actor chỉ trên test.

Lưu trữ employee và archive user là hai thao tác khác nhau. Luồng người dùng
lưu trữ employee không tự vô hiệu tài khoản; cleanup mẫu được ủy quyền có
manifest riêng. Không cấp HR manager cho account thật chỉ để mở workspace.

## Seal cuối và áp main

1. Chốt source/test logs/ảnh/evidence, kiểm Git diff và workflow. Nếu source đổi
   sau backup trước đó, backup main mới gồm source/config cuối; giữ test trước
   mọi reset và diễn tập phục hồi snapshot trên test chuẩn. So khớp fingerprint
   và blob **trước** neutralize. Không coi snapshot ban đầu là seal cuối.
2. Chỉ khi các cổng kỹ thuật/test/backup-restore đạt và phạm vi áp main đã được
   giao, kiểm main không drift ngoài manifest, dừng đúng PID/config main18069.
3. Áp code/module migration đã kiểm lên main; cleanup theo manifest rồi import
   roster bằng luồng/helper đã diễn tập. Không restore database test có fixture
   đè main. Không mời email hoặc tạo39users.
4. Restart main đúng config18069, smoke admin, account KH-KD giữ lại, HR39/chín
   nhóm, code/mapping/dashboard/export và quyền. Kiểm auth/config/FK/blob sau
   thay đổi. Test18079 giữ cách ly. Ghi kết quả thực tế vào status/acceptance;
   tách technical acceptance, business acceptance và pilot authorization.

## Rollback và giữ phát sinh mới

Khi upgrade/import/quyền lệch, dừng rollout, giữ main/test tương ứng không nhận
ghi mới nếu chưa an toàn. Trước phục hồi main, backup cả trạng thái lỗi và mọi
ghi mới sau snapshot (DB+filestore+config/source), ghi mốc thời gian và phạm vi
cần giữ; không làm mất phát sinh bằng restore im lặng.

Chọn backup main hợp lệ, kiểm SHA256/tables/blob và diễn tập lại trên test
chuẩn sau backup test. Phục hồi main chỉ bằng quy trình vận hành được giao,
khi HTTP main đã dừng, database và filestore đồng bộ, kèm source/config tương
ứng. `ops.py restore-test` cố ý không có nhánh restore main; không sửa tên DB
trong helper để vượt guard. Khôi phục hoặc nhập bù phát sinh mới phải có đối
chiếu riêng; không SQL delete chéo bảng, tắt FK, chuyển test fixture/grant vào
main hoặc reset sequence để “trở về” dữ liệu cũ.

Sau rollback, kiểm fingerprint/auth/config/blob, đăng nhập và smoke KH-KD/HR,
ghi rõ dữ liệu nào đã phục hồi và dữ liệu nào còn chờ đối chiếu trong status.
Không tuyên bố hoàn tất nghiệp vụ chỉ vì restore hoặc tests trả exit0.
