# NATIVE-DATA-003 — Bộ dữ liệu mẫu liên thông

Ngày thực hiện: 02/11/2026, Asia/Saigon. Change `CHG-20261102-014`, quyết định `DEC-027`. Người dùng chuyển phiên chính sang thực thi riêng task này. Trạng thái **PARTIAL_WITH_GAPS — IMPLEMENTED_PENDING_AUDIT**: phần liên kết/actor/chi phí đã áp dụng dev; nhân viên vẫn không đổi được tiến độ managed task theo policy hiện hành. Không gọi đây là end-to-end, nghiệm thu doanh nghiệp hay pilot.

## 1. Môi trường và cách bắt đầu

- Dev: [Home TANPHAT ONE](http://127.0.0.1:18069/odoo/tp-home), DB `tp_tanphat_dev`, PostgreSQL local 55432. `tp_web_home`/`tp_i18n_vi` giữ nguyên.
- Mật khẩu ngẫu nhiên riêng từng actor ở `C:\TANPHAT ONE\.local\native-data003\actor-secrets.json`, ACL private, ngoài Git. Không in mật khẩu, không dùng reset/invitation. Chạy lại không xoay mật khẩu. Admin/planner.dev giữ credential cũ.
- Snapshot private: `.local/native-data003/snapshot-20261102T080241Z/`: dump, filestore, config/secret, source đang sửa và manifest 127 checksum. Restore thực vào DB `tp_tanphat_data003_20261102` đạt **538 rowset/244 tham chiếu blob khớp** trước neutralize; không chỉ kiểm listing.
- Clone có UUID/owner token/data-dir/config riêng, cron/outgoing server tắt, SMTP loopback9, HTTP18149. Clone đã dừng sau kiểm; DB và evidence giữ lại. Dev tiếp tục chạy. Demo18109/18119 vẫn ngừng, không phục hồi DB demo cũ.
- Toàn bộ số liệu và danh tính dưới đây là giả lập. Công ty vẫn `Tan Phat Development`, company1/VND; không phải hồ sơ hoặc phân công nhân sự thật.

## 2. Actor và phạm vi

Các login có dạng `staff.<khóa>@example.invalid`. Tám actor được bật đăng nhập; Linh/Tuấn/Phúc giữ user cũ chưa bật password, Hà vẫn employee không user. Bảo dùng employee22 đã có vì inventory chưa có kế toán phù hợp có user; chỉ thêm user29 dev (clone30), không thêm employee trùng.

| Khóa / tên | UID dev / employee / phòng | Quản lý chi phí | Assignment dự án (hậu tố mã) | Quyền và thao tác chính |
| --- | --- | --- | --- | --- |
| long / Phạm Đức Long | 21 / 16 / Khảo sát | Khoa | 001,003,004 | Native employee + TP user/project user; xem task, nhập own timesheet hợp lệ, chi phí của mình |
| son / Vũ Hoàng Sơn | 22 / 17 / Khảo sát | Khoa | 001–004 | Như Long; khoản vật tư còn draft |
| huong / Lê Thu Hương | 19 / 14 / Kế hoạch Kinh doanh | Nam | 001,002,004 | Nhân viên điều phối; chi phí chuyển phát draft, nhóm KD riêng |
| khoa / Trần Đăng Khoa | 20 / 15 / Khảo sát | Nam | 001–004 | Thêm native Expense Team Approver; duyệt chi phí Long/Sơn/Phúc trong đội, không tự duyệt |
| lan / Bùi Ngọc Lan | 24 / 19 / Thiết kế | Nam | 002,003,004 | Project manager theo quan hệ project đã có; không cấp native manager group để né managed rule |
| nam / Đỗ Hải Nam | 23 / 18 / Thiết kế | Không có khoản của mình | 001–004 | Expense Team Approver + CRM All Leads native; điều phối bốn lead có FK và dashboard điều phối |
| khang / Nguyễn Minh Khang | 18 / 13 / Kế hoạch Kinh doanh | Không có khoản của mình | 003 | Actor âm: ngoài scope Sông Xanh; không CRM/accounting/finance dashboard |
| bao / Lê Quốc Bảo | 29 / 22 / Tài chính Kế toán | Không có khoản của mình | 001–004 (reader) | Native `account.group_account_user`, TP user/project user; đọc hóa đơn/chi phí và dashboard tiền |

Tất cả vi_VN/Asia/Ho_Chi_Minh/inbox. Không actor nào có System Administrator hoặc Platform Manager; không cấp TP workflow/financial grants. Nhóm kế toán native có phạm vi company theo native accounting, **không** suy ra project-scoped accounting hay quyền tiền TP Contracts. Việc không post/payment trong task là giới hạn vận hành của task, không phải một ACL read-only mới cho kế toán.

Cây nhân sự giả: Nam → Khoa/Lan/Hương; Khoa → Long/Sơn/Phúc; Lan → Linh/Tuấn. Manager/coach/expense_manager dùng native fields; không đổi chức danh/phòng ban cũ. Bổ sung5 assignment reader: Bảo4 dự án, Nam dự án002. Không chuyển project sang unmanaged.

## 3. Bản đồ toàn bộ fixture

Nguồn chi tiết private: `.local/native-data003/inventory-dev.json` có **188 binding cũ**, mỗi XML ID → model/ID/fields/quan hệ/nội dung/ngày/state/UI hint/disposition và `actor_record_access` read/write từng actor + admin/planner.dev. Đây là cổng ACL/record rule, không thay điều kiện field/action/state; việc `write=true` không có nghĩa được duyệt/post mọi action. Báo cáo `checks-dev.json`, UI và test action bổ sung bằng chứng. Không suy ownership từ tên hoặc ID đứng riêng.

Namespace gốc giữ nguyên: `tp_native_sample_20261102`, `tp_native_link_20261102`, `tp_native_todo_20261102`, `tp_native_data002_20261102`. Phần thêm có `tp_native_data003_20261102`; trường sửa có journal trước/sau, side effect native có phân loại tại §7.

| Mã / dự án | Project / customer / lead FK / analytic | Task / giờ | Expense / hóa đơn draft |
| --- | --- | --- | --- |
| DA-2026-001 / Cầu Sông Xanh | 8 / 46 / 11 / 8 | 8 task54–61; 33,5 giờ/8 dòng | Expense7,8; invoice4:310.000.000 |
| DA-2026-002 / Đường kết nối KCN Bình Minh | 9 / 47 / 13 / 9 | 7 task62–68; 29,5 giờ/7 dòng | Expense9,12; invoice5:210.000.000 |
| DA-2026-003 / Nút giao Đồi Cát | 10 / 48 / 15 / 10 | 6 task69–74; 21 giờ/5 dòng | Expense10; invoice6:96.000.000 |
| DA-2026-004 / Tuyến đường ven biển An Hòa | 11 / 49 / 18 / 11 | 7 task75–81; **0 giờ/0 dòng** | Expense11; invoice10:185.000.000 |

Project và TP Projects là cùng4 record. Timesheet20 dòng/84 giờ giữ user↔employee↔assignee↔task↔project↔analytic đúng; amount/ngày cũ không đổi. An Hòa đang chuẩn bị/khảo sát dự kiến; 0 giờ nghĩa chưa có dòng xác nhận, không bịa giờ để lấp dashboard. Task từng dự án có trạng thái khác nhau đã có từ trước; không sửa tiến độ lịch sử.

CRM có FK mới tùy chọn `tp_project_id`, nhãn **Dự án thực hiện**, chỉ gắn4 cơ hội tương ứng, cùng customer thương mại/company. Nam phụ trách bốn cơ hội này;6 lead còn lại giữ pipeline/null, không tạo project cho chúng. Thay salesperson phát sinh native `date_open`/duration tracking/chatter, không sửa ngày nghiệp vụ bằng fixture. FK không phải action conversion hoặc tạo project. Xem [bridge spec](../architecture/TP_NATIVE_DATA003_BRIDGE_SPEC.md).

Bốn invoice giữ `draft`, VND, cùng customer và invoice-line analytic distribution dự án; số trước thuế và tổng cùng801.000.000 vì không có thuế trên bốn chứng từ giả này. `invoice_origin` là chuỗi tham chiếu; quan hệ phân bổ là analytic native, **không có FK invoice→project mới**. Giá trị dự kiến bằng10% CRM trước đây là giả định fixture, không phải quy định tạm ứng. Không cộng CRM/hợp đồng/invoice/expense thành một tổng doanh thu.

Các nhóm còn lại đều có vai trò rõ:

| Nhóm giữ nguyên | Vai trò / quan hệ / giới hạn |
| --- | --- |
| 8 partner,5 phòng,12 employee,1 service product | Danh tính/customer/nhân sự/master data dùng chung; không nhân bản để thêm actor |
| 14 To-do admin, `project_id=False` | Việc cá nhân điều phối, link/mô tả tham chiếu hồ sơ; không phải FK và không biến thành28 task dự án |
| 8 event9–16 | Private, không alarm; thêm20 attendee đúng bối cảnh, giữ agenda/ngày. Actor timezone+7: event02 là03/11 09:00, event06 là10/11 09:00. Không dời lịch sử về hôm nay |
| 3 nhóm40–42 /12 tin cũ | Điều phối: Nam/Khoa/Lan; KD: Nam/Hương; phối hợp KS–TK: Nam/Khoa/Lan/Long/Sơn (ngoài admin cũ). Giữ author/date/body12 tin; chỉ thêm10 member fixture |
| 2 dashboard5,6 |5 cho admin/Nam/Khoa;6 cho admin/Bảo; user allowlist, không group toàn công ty; dữ liệu pivot/chart trực tiếp theo quyền người xem |
| 6 `tp.work.item`7–12 | Catalog khảo sát/thiết kế/rà soát/họp/báo cáo/tài liệu. Model hiện chưa có FK task→work item, nên không tuyên bố quan hệ tự động hoặc mở workflow mới |

Hợp đồng HD-DEV, grant TP, onboarding cũ, General và dashboard chuẩn được inventory/bảo toàn riêng, không repoint để nối giả bốn dự án mới.

## 4. Chi phí và số0 theo actor/domain

| Expense / chủ | Phân bổ | VND | State dev | Người duyệt / side effect |
| --- | --- | ---: | --- | --- |
|7 / Khoa | analytic8 100% |1.250.000|submitted|Nam; activity chờ duyệt |
|8 / Long | analytic8 100% |2.400.000|approved|Khoa; purchase receipt13 **draft** |
|9 / Lan | analytic9 100% |850.000|approved|Nam; purchase receipt14 **draft** |
|10 / Sơn | analytic10 100% |630.000|draft|Khoa; chưa submit |
|11 / Khoa | analytic11 100% |1.850.000|submitted|Nam; activity chờ duyệt |
|12 / Hương | analytic9 100% |180.000|draft|Nam; chưa submit |

Sáu action native (submit4, approve2) chạy bằng `with_user` nhân viên/người duyệt, không sudo, không ghi state trực tiếp. Tổng vẫn7.160.000. Approve own-account tạo2 receipt nháp/6 dòng kế toán và tax/tag relations native; không post/payment/analytic accounting entry mới. Bốn invoice cũ giữ nguyên toàn dòng dữ liệu. Approved là chờ hoàn trả, không phải đã chi tiền.

Các số sau dùng domain `id in [7,8,9,10,11,12]` và hierarchy của actor, thứ tự **đang soạn / chờ duyệt / chờ hoàn trả**, VND:

| Actor | Đang soạn | Chờ duyệt | Chờ hoàn trả |
| --- | ---: | ---: | ---: |
| Long |0|0|2.400.000|
| Sơn |630.000|0|0|
| Hương |180.000|0|0|
| Khoa (cả đội) |630.000|3.100.000|2.400.000|
| Lan |0|0|850.000|
| Nam (cây nhân sự) |810.000|3.100.000|3.250.000|
| Khang / Bảo / admin |0|0|0|

`get_expense_dashboard` giao domain tìm kiếm với employee `child_of` của actor. Bảo vẫn đọc được6 expense qua native accounting nhưng không có con trong hierarchy, nên header0; admin không có employee nên0. Không tạo employee cho admin hoặc đổi chủ expense. Bộ lọc **Chi phí của tôi**/**Cần xử lý** có thể ẩn các giai đoạn khác; dùng Nam và bỏ bộ lọc đó để đối chiếu toàn cây nhân sự. Bảng tài chính của Bảo dùng nguồn6 ID, không dùng header cá nhân và không hardcode kết quả.

## 5. Ba kịch bản kiểm lại

**S1 — nhân viên/duyệt:** login Long → Home → Project/All Tasks, lọc người được giao → mở task Cầu Sông Xanh → Timesheets nhập own hours đúng project/task/employee (kiểm tạo0,5 giờ trong rollback, không lưu dòng thử dev). Expense8 của Long đã submit bằng Long và approve bằng Khoa; có lịch sử, receipt nháp và tổng theo nguồn. Sơn có expense10 draft để trải nghiệm soạn; Khoa/Nam xem đúng đội và action native. Đổi `project.task.state` sang `1_done` bằng Long trả AccessError dù đọc được task: **S1 chưa end-to-end**; xem [RFC TASK-001](../architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md).

**S2 — điều phối/kế toán:** login Nam → CRM mở lead11/13/15/18 → “Dự án thực hiện” mở đúng canonical project; task/nhân sự/giờ/expense đối chiếu bảng §3. Dashboard điều phối28 task/84 giờ. Login Bảo → Customer Invoices lọc Draft, nhận4 invoice801 triệu; dashboard tiền6 expense7,16 triệu, ba giai đoạn đúng §4. Nam/Khoa/Long tham gia event/nhóm phù hợp, đọc12 tin cũ đúng author/date. Chỉ clone: Nam refuse expense7 qua wizard có lý do → Nam reset (nhân viên không có quyền reset native) → Khoa sửa/gửi lại; savepoint rollback. Không diễn tập post/payment vì không cần chứng minh phần được giao trên dev.

**S3 — ngoài scope:** login Khang → không đọc/ghi project8/task của Long; create/repoint timesheet sang đó bị chặn; không đọc expense7/invoice4/To-do admin/nhóm và tin riêng/dashboard tiền. Native Calendar có thể trả “Busy/Bận” và thời gian, không lộ tên/description riêng; không khẳng định event biến mất. Kiểm cả ORM/read/search/group/export, actor HTTP/RPC thật và public share. Bảo dù đọc dashboard tiền cũng không tạo được snapshot public; token cũ của dashboard protected bị chặn. Nhóm/accounting của actor khác không phát sinh chỉ vì biết project ID.

## 6. Application batch riêng

| Addon mới | Lý do / ranh giới | Kiểm clone |
| --- | --- | --- |
|`tp_crm_project_bridge`|FK restrict/check_company/copy=False; company/customer integrity hai chiều; CRM native giao project read; explicit create/write target check, không chỉ constraint|7 test |
|`tp_timesheet_scope`|Native own-timesheet từng cho Khang tạo dòng của project ngoài scope do sudo target lookup. Global rule + explicit create/write/default target check + task/project constraint; không mở task write|5 test |
|`tp_dashboard_privacy`|Native share là snapshot public dùng quyền creator. Cờ protected trên đúng2 dashboard, chặn create/repoint/token cũ; bảng chuẩn mặc định false|3 test |

Odoo20 chạy constraint bằng sudo, vì vậy security target check phải ở create/write, constraint chỉ giữ integrity. Không sửa core, OpenAPI, React hay `tp_project` policy trong lượt này; không có capability/state mới. Chi tiết [timesheet](../architecture/TP_NATIVE_DATA003_TIMESHEET_SCOPE.md) và [dashboard](../architecture/TP_NATIVE_DATA003_DASHBOARD_PRIVACY.md). Share button native còn hiện, server trả lỗi giải thích; chưa tùy biến JS nút đó.

## 7. Bảo toàn và side effect đã phân loại

`preserve-before-dev.json` → `preserve-diff-before-dev-audited.json` private: **486/538 bảng không đổi**,52 bảng có thay đổi đã review; không xóa row/relation cũ. Script audit kiểm table/ID/field allowlist, file config/credential, cluster catalog/roles, blob và195 file maintained source trước task. Các bảng thay đổi thuộc:

| Loại | Bảng / thay đổi |
| --- | --- |
| Module metadata | `ir_access`+2 global rules, `ir_model_fields`+2, group relation+1, constraint+1, view+1, module+3/dependency+5/XML IDs mới;669 module cũ chỉ `write_date` khi Odoo scan catalog |
| Actor/link fixture | `res_users`7 password/notification và onboarding state, user29 mới; partner67 mới/locale7 fake + employee flag partner63; employee9 dòng và resource23/hr_version22;5 assignment,14 group membership additions, company-user relation;4 CRM links/owners (6 lead còn lại chỉ có cột FK null);20 attendee và event timestamps; dashboard allowlist+3/cờ2 và default false trên bảng chuẩn |
| Timesheet |18/20 dòng chỉ recompute `manager_id`/write_date theo hierarchy; không đổi giờ/user/employee/project/task/analytic/ngày |
| Expense/receipt |6 expense manager/action fields đúng journal; move13,14/line31–36 mới và tax/tag relations;4 approval activity native (kể cả dòng completed); không payment hoặc posting mới |
| Lịch sử/thành viên |10 nhóm member fixture, followers10/subtype relations; các message tracking/action mới đúng actor, không sửa message cũ;10 mail exception; không thêm mail.notification |
| User onboarding native |To-do115 “Chào mừng Lê Quốc Bảo!”,7 stage cá nhân233–239/assignee/followers; calendar26/settings25; auto join General member77/digest relation cho Bảo. Đây là hook native tạo user, không phải đổi nội dung/kênh dùng chung hoặc nhân bản14 To-do mẫu |
| Login/Discuss native |8 OdooBot private chat43–50/16 member và8 welcome message1010–1017, tự sinh khi actor mở Discuss lần đầu; author OdooBot nguyên gốc, không phải tin fixture do AI mạo danh |
| Attachment |5 avatar attachment412–416 của partner Bảo; dashboard405 thay template live ba giai đoạn.244 blob cũ vẫn khớp checksum/kích thước,243 tham chiếu cũ không đổi;405 đổi có chủ đích.249 tham chiếu hiện tại đều kiểm blob đạt |
| Telemetry |`bus_bus`, `mail_presence`, `res_users_log`, `res_device_log`, ba `orm_signaling_*`, một auto-vacuum trigger69. Số tăng phụ thuộc lượt login/test, không reset telemetry |

Native password write vẫn phát cảnh báo bảo mật dù `no_reset_password=True`: mail21–28 đều `exception`, không lời mời/reset email. Expense submit phát trực tiếp2 mail31,32, cũng `exception`. Không thư sent/outgoing mới hoặc người nhận thật. Tool cuối kiểm không có SMTP server cấu hình, loopback9 không listener và đặt fallback SMTP chỉ trong process; không đổi config/cron dev. Các lần rollback có thể tiêu sequence ID hoặc tạo blob tạm, không hứa sequence/filestore GC rollback cùng DB. Không xóa exception mail để che dấu.

Admin/planner password/group/assignment cũ khớp baseline; các bảng contract/grant/project/task cũ/invoice cũ không đổi. Database OID/owner/catalog/roles và shared PostgreSQL/config/credential không đổi. **Không fingerprint toàn nội dung các database test/backup khác trong lượt này**, nên không tuyên bố checksum dữ liệu bên trong chúng; tool không nhắm ghi vào đó. Archive demo cũ giữ nguyên.

## 8. Tái lập và rollback có kiểm soát

Tooling trong Git: `scripts/native_data003.py`, `_checks.py`, `_preserve.py`, `_rollback_probe.py`, `_ui.cjs`, `_dashboard_probe.cjs`, guard tests và dashboard builder. Evidence/credentials/dump nằm `.local/native-data003/`, không Git. Preflight xác minh workspace/config/cluster/source UUID/clone token/restore rehearsal; advisory lock và retry SerializationFailure bằng transaction mới tối đa3 lần. Không chạy lại seeder cũ.

```powershell
# Trên workspace/owned clone đã có: inventory + verify, không seed/password reset.
.\.venv\Scripts\python.exe scripts/native_data003.py inventory --target dev
.\.venv\Scripts\python.exe scripts/native_data003.py actors --target dev --mode verify
.\.venv\Scripts\python.exe scripts/native_data003.py links --target dev --mode verify
.\.venv\Scripts\python.exe scripts/native_data003.py actions --target dev --mode verify
.\.venv\Scripts\python.exe scripts/native_data003_checks.py --target dev
.\.venv\Scripts\python.exe scripts/native_data003_checks.py --target dev --http
node scripts/native_data003_ui.cjs dev
```

Khi diễn tập lại từ snapshot mới theo scope riêng: `snapshot` một lần → `clone` (restore exact, neutralize) → cài đúng3 addon trên clone, không cài `tp_demo_workspace` → actors dry-run/apply → links dry-run/apply → actions dry-run/apply → checks/UI → đối chiếu → cài đúng addon dev và apply tuần tự. Snapshot/clone tool cố ý từ chối owner/DB đang có khác baseline, không tự drop/reseed clone. DDL/install là transaction riêng, không được coi savepoint migrator đảo mọi thay đổi module.

Giữ bản apply đầu `*-dev-apply-initial-evidence.json`; các lần sau có thể ghi đè file kết quả CLI nhưng journal trong `ir.config_parameter` giữ trước/sau và ledger từng action. Reapply actor/link/action cuối: **created0/updated0/action0**, verify không drift, password hash không đổi. Lượt dry-run linkage từng serialization do hai bước phụ thuộc chạy chồng; đã rollback, chạy tuần tự lại và thêm bounded fresh-transaction retry. Không chạy batch phụ thuộc song song.

Rollback field chưa chốt: đọc journal bootstrap/linkage bằng actor vận hành có quyền, xác minh ownership và giá trị hiện tại còn bằng `after`, đảo theo thứ tự phụ thuộc bằng ORM, dùng `before` đầu tiên/final `after`; drift thì dừng để reconcile. Không xóa record đã có từ trước, không tự unlink native side effect có lịch sử. Chi phí đã submit/approve dùng refuse/reset/correction/cancel native có lý do, kiểm side effect trên clone trước; **không write lùi state**. Addon timesheet/privacy đang đóng lỗ hổng nên không tự uninstall trong khi tài khoản giả còn bật. Clear4 FK trước uninstall bridge nếu có kế hoạch rollback riêng, không xóa project/lead.

Full restore dev chỉ được điều phối riêng khi đã chứng minh không có ghi mới sau snapshot và bảo toàn công việc khác; không đè database để đảo một batch. Cleanup hiện tại chỉ `native_data003.py stop` đúng PID/config owner clone, không dừng PostgreSQL/dev hoặc drop database. Có thể `start` owned clone18149 để audit rồi `stop`; không dùng demo18109/18119.

## 9. Kiểm thử và giới hạn nghiệm thu

| Kiểm | Kết quả / evidence private |
| --- | --- |
| Restore rehearsal |538 rowset/244 blob refs exact; `restore-evidence.json`, manifest127 checksum |
| Odoo integration |0 failed,0 errors of27 tests:3 addon mới + `tp_project`; `integration-tests.log` |
| Tool guards/lint |9 unit tests đạt, Ruff đạt các addon/tool mới/dashboard builder |
| ORM actor |clone74, dev71 assertion đạt, `gaps=[]` cho security đã sửa; managed-task denial được assert như policy gap, không coi đã mở chức năng |
| HTTP actor |8/8 clone và dev đăng nhập thật; credential không log |
| UI/RPC |clone58/58 (ma trận trước RPC bổ sung), dev63/63;8 actor,1440/375,6 lần CSS content zoom125%/150% của Expense;0 console error/overflow trong ma trận. Zoom là CSS content scaling, không tuyên bố browser chrome zoom |
| Dashboard live |clone Long sửa0,5 giờ, Nam refresh thật:84→84,5→84; native chart/pivot RPC và3 screenshot đã xem, `dashboard-live-probe.json`; không mutate dev để thử chart |
| Failure rollback |clone bootstrap và native submit injected failure:538 rowset khớp; `rollback-probe.json`. Sequence/SMTP attempts/temporary blobs ngoài cam kết DB transaction |
| Preservation |52 table delta review,195 code cũ không đổi,244 blob cũ giữ/249 refs hiện kiểm đạt; private audit ở §7 |

Ảnh dev Home375, CRM FK375, finance1440 và clone dashboard delta đã tự xem. Không chạy React build/typecheck/HOOT vì không sửa React/app JS. Test browser harness là CLI Playwright, không phải nghiệm thu thủ công của người dùng. Log có cảnh báo thiếu `markdown2`; negative FK/security test có lỗi SQL/AccessError mong đợi, summary Odoo27 không fail.

**Đã áp dụng dev:**8 login, hierarchy/scope, CRM FK4, calendar/Discuss memberships, dashboard domain/privacy, expense native3 giai đoạn và2 receipt draft. **Chỉ clone:**refuse/reset/correction/resubmit, nguồn dashboard đổi/khôi phục, failure injection và Odoo integration. **Chưa có/cần quyết định:**policy managed-task progress ([TASK-001](../architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md)), task↔catalog/TP workflow/Survey/Design/FIN-001/BASE/ký/hiệu lực/thu chi chính thức. Không mở thêm các phân hệ dưới tên liên kết dữ liệu.

Technical: kiểm triển khai đạt phạm vi ghi trên, **chờ audit độc lập**. Business acceptance: chưa có. Pilot authorization: chưa có, Q2/owner/evidence và các gate khác vẫn mở. Bước tiếp: audit phần đã áp dụng và quyết định policy TASK-001; giữ Home/To-do/NATIVE-DATA-002/VI-001/AUTH-002 audit riêng.

Kiểm bàn giao cuối: `dev.py smoke` đạt admin/planner native session/API/project/contract/financial scope;14 tài liệu/168 link tương đối/fence/CHG marker đạt, Node syntax/Ruff/unit9 và `git diff --check` đạt. `ai_workflow finish/check` chỉ xác nhận snapshot bàn giao, không chạy lại business tests hoặc cấp phép pilot.
