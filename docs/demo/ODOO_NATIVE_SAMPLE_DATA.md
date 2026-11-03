# Bộ dữ liệu trải nghiệm Odoo chuẩn

Ngày tạo: 02/11/2026 (Asia/Saigon). Batch nạp `CHG-20261102-001`; liên kết liên phân hệ `CHG-20261102-002`; To-do `CHG-20261102-007`; lịch/trao đổi/bảng tổng hợp `CHG-20261102-008`.

## Phiên bản liên thông NATIVE-DATA-003 — CHG-20261102-014

Người dùng chuyển vai trò và giao thực thi ngày02/11/2026 (DEC-027). Xem [runbook hiện hành](NATIVE_DATA_003_CONNECTED_OPERATIONS.md): bật8 actor giả, giữ188 binding/ID/84 giờ/7.160.000 chi phí/801 triệu invoice draft; thêm user Bảo trên employee đã có, hierarchy/approver và scope/membership đúng người. CRM4 cơ hội có FK mới “Dự án thực hiện”, không auto conversion;6 lead khác giữ pipeline. Addon timesheet scope và dashboard privacy đóng hai lỗ hổng đã tái hiện/test clone trước dev. Hai bảng mẫu giới hạn actor, không public snapshot.

Chi phí nay có2 draft/2 submitted/2 approved bằng action native, hai receipt phát sinh vẫn draft; không posting/payment. Admin không có employee nên header0 đúng native; đăng nhập Nam để xem cây nhân sự, Bảo để xem invoice/dashboard tiền. Credential actor ở `.local/native-data003/actor-secrets.json` private ngoài Git. Admin/planner credential/quyền cũ giữ nguyên. Clone restore-rehearsed538 rowset/244 blob ref, đã dừng18149; dev18069 chạy, demo18109/18119 giữ ngừng.

Trạng thái **PARTIAL_WITH_GAPS**, chờ audit độc lập: actor nhập own hours được nhưng cập nhật progress managed task còn bị chặn, [RFC TASK-001](../architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md) chưa mở policy. Không nghiệm thu business/pilot/TP workflow. Các đoạn dưới mô tả **lịch sử batch001/002/007/008**, gồm “user chưa password”, “expense tất cả draft”, “chỉ admin” và “chưa FK”; chúng được phiên bản003 thay thế ở đúng phần nêu trên, không phải lệnh dựng lại baseline cũ.

## Mục đích và môi trường

Người dùng yêu cầu thêm dữ liệu mẫu vào giao diện native đang mở sau khi xem menu ứng dụng Odoo. Tên bản ghi mới dùng tên tự nhiên, không gắn chữ DEMO. Đây vẫn là dữ liệu giả lập, không phải hồ sơ hoặc nhân sự Tấn Phát thực tế; không đổi định nghĩa này để trình bày như số liệu đã vận hành.

- URL: `http://127.0.0.1:18069/odoo`, database `tp_tanphat_dev`, công ty hiện có `Tan Phat Development`.
- Sử dụng tài khoản `admin` và credential hiện có tại `.local/dev-secrets.json`; không đổi mật khẩu.
- Các bản ghi đã có giữ nguyên tên và giá trị. Không sửa ứng dụng read-only UI-DEMO-001/002 trên cổng 18109.
- Không cài/nâng cấp module, đổi code ứng dụng, workflow TP, quyền/grant hiện có, BASE, ký/hiệu lực hoặc pilot.

## Dữ liệu được thêm

| Ứng dụng hoặc nhóm | Số lượng | Nội dung |
| --- | ---: | --- |
| Contacts | 8 | Chủ đầu tư, đơn vị tư vấn, xây dựng, thiết bị và dịch vụ với danh tính giả; email `example.invalid` |
| CRM | 10 | Cơ hội khảo sát, thiết kế, thẩm tra, giám sát ở các giai đoạn New/Qualified/Proposition; doanh thu kỳ vọng là giả lập |
| Project | 4 | Cầu Sông Xanh, đường kết nối KCN Bình Minh, nút giao Đồi Cát, tuyến đường ven biển An Hòa |
| Project Tasks | 28 | Công việc có người phụ trách, hạn xử lý, bốn giai đoạn và một số việc hoàn thành |
| Phòng ban | 5 | Kế hoạch Kinh doanh, Khảo sát, Thiết kế, Tài chính Kế toán, Hành chính Nhân sự |
| Employees | 12 | Nhân sự giả có chức danh/phòng ban; không dùng hồ sơ cá nhân thật |
| Timesheets | 20 | Dòng thời gian làm việc gắn nhân sự, công việc và dự án mới |
| Expenses | 6 | Chi phí đi lại, lưu trú, in hồ sơ, vật tư, công tác và chuyển phát; tất cả còn nháp |
| Invoicing | 4 | Hóa đơn khách hàng nháp; tổng 310.000.000, 210.000.000, 96.000.000 và 185.000.000 VND, chưa thuế; hóa đơn thứ tư thêm ở CHG-002 |
| Sản phẩm dịch vụ | 1 | Dịch vụ tư vấn khảo sát và thiết kế |

Có thêm 10 user giả để gắn người phụ trách/giờ làm. Các user không có mật khẩu, không gửi lời mời và không được cấp TP grant. CHG-002 bổ sung nhóm Platform User và 27 assignment reader/coordinator đúng dự án cho các user giả này; không cấp Platform Manager hoặc quyền tiền/workflow. Không đại diện cho quy chế quyền nhân sự thật. Không bật tài khoản này bằng reset password hoặc dùng làm người dùng pilot.

## Cách xem và thao tác

1. Đăng nhập `admin`, mở app Odoo chuẩn, không chọn app Demo ở 18109.
2. Project: mở bốn dự án mới, vào Tasks xem cột Chuẩn bị/Đang thực hiện/Chờ kiểm tra/Hoàn thành. Từ CHG-002, cùng bốn record được đánh dấu `tp_managed=True`, có mã/phòng chủ trì và xuất hiện trong TANPHAT ONE → TP Projects. Đây không phải nghiệm thu nghiệp vụ. Admin vẫn thao tác native; nhân sự giả được assignment chỉ đọc managed project/task theo policy hiện có.
3. CRM: mở Pipeline để xem cơ hội và doanh thu kỳ vọng.
4. Employees: xem nhân viên và phòng ban. Contacts: xem tám đối tác mới.
5. Timesheets: chọn màn hình tất cả thời gian hoặc bỏ bộ lọc My Timesheets để thấy giờ của các nhân sự. Expenses: bỏ bộ lọc của tôi/Submitted nếu có, dùng chế độ danh sách hoặc phân tích để thấy nháp của cả nhóm.
6. Invoicing: mở Customer Invoices và lọc Draft. Không bấm Confirm/Post/Send/Register Payment cho dữ liệu giả lập.

## Bảo toàn và truy vết

- Seeder chỉ thêm bản ghi qua ORM, thực hiện trong một transaction, ràng buộc XML ID dưới namespace `tp_native_sample_20261102`; namespace này là dấu vết dữ liệu, không phải module cần cài.
- Tên tự nhiên trên danh sách; mô tả/ghi chú ở bản ghi có trường phù hợp ghi rõ nguồn gốc giả lập. Namespace, báo cáo local và tài liệu này tiếp tục giữ provenance.
- Tại thời điểm CHG-001, bốn dự án mới chưa có mã/assignment TP và không xuất hiện trong API managed. CHG-002 thay thế trạng thái này bằng mapping bên dưới; không thêm grant.
- Không phát sinh mail gửi đi, chứng từ posted hoặc thanh toán; không thay cấu hình gửi mail, công ty, tài khoản hiện có hoặc dữ liệu hợp đồng TP.
- Trước khi thêm đã dừng đúng Odoo dev do script sở hữu, chụp database và các blob filestore chuẩn rồi khởi động lại. Demo 18109 và PostgreSQL dùng chung không bị dừng.
- Bản chụp: `.local/native-data-20261102/backup-20261102T015925Z/` gồm dump, filestore, SHA-256 manifest; `pg_restore --list` đạt. Đây là snapshot dữ liệu trước lượt thêm, chưa diễn tập restore cho snapshot này và không phải backup source hoàn chỉnh.
- Helper, schema probe, log và báo cáo ở `.local/native-data-20261102/`, ngoài Git. Không đưa credential hoặc dump vào repository.

## Kiểm tra thực chạy

- Lượt dry-run ban đầu phát hiện khác biệt Odoo 20 về password/field nhân sự, rollback và sửa helper local; lượt chạy thành công mới commit.
- Dry-run transaction rollback đạt; lượt `--commit` thành công. `--verify` qua registry mới đạt, `new_records={}`, kiểm đủ binding/count và không thêm trùng.
- Đối chiếu hash các dòng cũ: TP managed projects, contract/revision, assignment/grant và user hiện có không đổi. Số grant, mail và chứng từ posted không tăng.
- HTTP đăng nhập admin, native search/read cho tám nhóm model đúng số lượng; hóa đơn đúng tổng và còn draft; cả 28 task có người phụ trách. `/odoo` trả 200 và API TP không lẫn dự án mới.
- Admin có ACL read/create/write/unlink trên project/task/CRM/employee/expense/invoice; form native không khóa create/edit. Thử tạo/sửa/xóa một project trong savepoint rồi rollback đạt, không giữ bản ghi thử. Không khẳng định mọi chứng từ đều xóa được ở mọi trạng thái.
- Không chạy toàn bộ test ứng dụng vì không đổi application code. Đây là kiểm dữ liệu và thao tác native, không phải nghiệm thu nghiệp vụ hoặc pilot.

Next action phát triển vẫn là audit UI-DEMO-001/002, AUTH-002 slice 2 và C01 theo PROJECT_STATUS; lượt nạp này không đóng các cổng đó.

## Liên kết liên phân hệ — CHG-20261102-002

Theo yêu cầu người dùng, giữ nguyên ID bốn dự án, khách hàng, task và timesheet; bổ sung mã/phòng chủ trì để Project và TP Projects hiển thị cùng hồ sơ. Không tạo một tập dự án thứ hai.

| Mã | Dự án | Phòng chủ trì | Task | Giờ làm (dòng) | Chi phí nháp | Hóa đơn nháp (VND) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| DA-2026-001 | Cầu Sông Xanh và đường dẫn hai đầu cầu | Thiết kế | 8 | 8 | 2 | 310.000.000 |
| DA-2026-002 | Đường kết nối Khu công nghiệp Bình Minh | Thiết kế | 7 | 7 | 2 | 210.000.000 |
| DA-2026-003 | Nút giao Đồi Cát và các tuyến nhánh | Khảo sát | 6 | 5 | 1 | 96.000.000 |
| DA-2026-004 | Tuyến đường ven biển An Hòa | Khảo sát | 7 | 0 | 1 | 185.000.000 |

- Bốn cơ hội CRM tương ứng dùng cùng customer ID, gắn tag mã dự án và tham chiếu bấm mở dự án trong mô tả. Sáu cơ hội khác giữ nguyên. Cấu hình hiện tại chưa có trường quan hệ trực tiếp CRM → Project; đây là đối chiếu dữ liệu và tham chiếu, chưa phải chuyển đổi tự động hoặc đồng bộ vòng đời.
- Nhân sự được giao task/giờ làm khớp nhân viên và phòng ban. Project manager và người tham gia có assignment tương ứng. Tổng 28 task, 20 timesheet và 6 chi phí nháp giữ nguyên; An Hòa chưa có timesheet, không tạo giờ làm chỉ để đủ số.
- Cả bốn hóa đơn cùng khách hàng với dự án, có mã trong Origin/Reference và phân bổ 100% vào analytic account của dự án. Các chi phí cũng phân bổ đúng analytic account. Hóa đơn An Hòa là bản nháp mới; ba bản nháp ban đầu giữ nguyên tổng. Kịch bản đặt số nháp bằng 10% doanh thu kỳ vọng giả của CRM để dễ đối chiếu, không phải quy định tạm ứng/hợp đồng.
- Mô tả Project/CRM/Contacts/Invoice có tham chiếu và nguồn gốc giả lập. Tham chiếu không bỏ qua quyền Odoo. Không đưa số tiền vào mô tả dự án dùng chung. Chưa tạo hợp đồng TP, duyệt BASE, ký/hiệu lực, posted/payment hoặc grant người dùng thật.
- Cách mở: đăng nhập admin ở 18069; Project xem task/mô tả hoặc TANPHAT ONE → TP Projects xem mã/phòng/phân công. Hai menu có cùng bốn project ID 8–11. CRM tìm tag DA-2026-001…004; Invoicing lọc Draft và tìm mã trong Origin/Reference. Nhấn F5 sau cập nhật. Tài khoản planner.dev không được thêm phạm vi và sẽ không thấy bốn dự án này.

### Kiểm chứng và bảo toàn CHG-002

- Snapshot trước liên kết: `.local/native-data-20261102/backup-20261102T023505Z/`, database dump + canonical filestore và manifest SHA-256; `pg_restore --list` đạt, chưa diễn tập restore snapshot mới. Chỉ dừng/khởi động đúng Odoo dev sở hữu, giữ demo18109 và PostgreSQL.
- Local helper `align_modules.py`: dry-run rollback, apply nguyên tử, verify registry mới đạt với `created={}`. Namespace liên kết `tp_native_link_20261102`: 4 tag CRM, 27 assignment giả và 1 invoice nháp; không thêm project/task/grant/mail hoặc posted invoice. Không chạy lại seeder CHG-001 với giả định cũ về unmanaged.
- Lượt dry-run đầu dừng vì partner gắn user giả đổi write_date khi thêm group. Xác định đúng partner ID thuộc fixture; kiểm business fields của chúng giữ nguyên, chỉ cho write_date thay đổi. Hash tất cả dòng ngoài bộ giả lập của project/user/partner/CRM/employee/department/contract/revision/assignment/grant giữ nguyên.
- HTTP native đăng nhập admin: hai action cùng model và đúng domain, cùng bốn ID; mã/phòng/customer, CRM/tag/reference, task/người phụ trách, timesheet và bốn invoice nháp khớp. Link chuẩn Odoo mở được; API TP admin thấy bốn dự án.
- HTTP planner.dev vẫn chỉ thấy một dự án cũ, gọi trực tiếp bốn ID mới nhận 404. ORM từ chối nhân sự không có assignment đọc dự án/task khác; người tham gia đọc được nhưng không được ghi managed project. Mười user giả vẫn không có password.
- Admin ACL/form và thử project create/edit/delete trong savepoint rollback đạt sau liên kết. Không giữ record thử. Không chạy toàn bộ app tests do không đổi application code/schema; đây không phải UAT/pilot.
- Evidence local: `align-apply.json`, `align-verify.json`, `alignment-http-verification.json`, `editability.json` và log trong `.local/native-data-20261102/`. Không commit/push hoặc đưa dump/secret vào Git.

## To-do cá nhân — TODO-001 / CHG-20261102-007 (đã sửa quyền và nạp, chờ audit)

Lỗi gốc (CHG-004): global rule `tp_project.task_platform_scope` dùng `('project_id.tp_managed', '=', False)`; với To-do (`project_id=False`) đường quan hệ không khớp nên read bị từ chối, trong khi write/unlink của admin đi qua nhánh TP manager. User thường còn bị chặn cả cud do `task_platform_write_scope`.

Correction tối thiểu trong `custom_addons/tp_project/security/ir.access.csv` (không đổi manifest/version, không thêm dependency):

- read: `['|', ('project_id', '=', False), '|', ('project_id.tp_managed', '=', False), ('project_id', 'access', 'read')]`
- cud cho user không là TP manager: `['|', ('project_id', '=', False), ('project_id.tp_managed', '=', False)]`; nhánh TP manager giữ `[]`.

`project_id=False` chỉ cho task đi qua lớp giới hạn TP; quyền riêng tư vẫn do rule native (`Full access to own private task only`, multi-company, project manager chỉ thấy task có project hoặc của chính mình). Không bỏ global rule, không sudo, không cấp nhóm/grant.

Kiểm thử trên DB cô lập `tp_tanphat_data002_test` (clone snapshot `.local/data002/snapshot-20261102T041428Z`, neutralize, cổng 18139):

- Regression `TestPrivateTodoAccess` (6 test) trong `custom_addons/tp_project/tests/test_project_access.py`: chủ sở hữu CRUD + chuyển personal stage; user khác và TP manager + Project manager không read/search/write/unlink; chia sẻ bằng `user_ids` mở cho B, không mở cho C; cách ly công ty; managed task theo assignment, user thường không ghi; unmanaged task giữ quyền native.
- Với rule cũ: `0 failed, 3 error(s) of 6 tests`; với correction: `--test-tags /tp_project` `0 failed, 0 error(s) of 12 tests`. Ruff `custom_addons/tp_project` đạt.
- Tích hợp `-u project_todo,tp_project --test-tags /tp_project,/project_todo` (chỉ trên DB test): 23/25; 2 lỗi `TestProjectTodoTagsSecurity`/`TestProjectTodoTaskTypeSecurity.test_security` là test at_install của `project_todo` chạy khi `tp_project` chưa nạp vào registry nên rule `project.project` (`tp_managed`, không thuộc thay đổi này) không dựng được thông báo lỗi. Đây là giới hạn thứ tự nạp module khi chạy test native trên DB đã cài TP, không phải lỗi runtime; ghi rõ để audit.
- Dòng `PermissionError [WinError 5]` trong log là GC filestore (file attachment read-only trên Windows) ở mức INFO, không phải test fail.

Áp dụng dev `tp_tanphat_dev` (dev18069 đang chạy, không dừng): `-u tp_project --stop-after-init --no-http` exit 0. Helper `seed_todo.py`: dry-run rollback đạt → apply `created=14` → verify registry mới `created=0`. Namespace `tp_native_todo_20261102`, task ID 99–112, `project_id=False`, chỉ gán admin, personal stage sẵn có của admin (Inbox/Today/This Week/This Month/Later/Done), mô tả ghi chú giả lập và tham chiếu DA-2026-001…004. Hash các dòng có sẵn của task/stage/project/user/assignment/grant/contract/invoice/expense giữ nguyên, task thuộc dự án không đổi (28), không mail mới.

Kiểm live dev18069 (phiên admin, không sudo): action To-do thấy 15 = 14 fixture + 1 To-do onboarding native “Welcome Administrator!” do OdooBot tạo 28/10 (dữ liệu có sẵn, giữ nguyên); Open thấy 13 (12 fixture + 1), cột Inbox 4 / Today 3 / This Week 2 / This Month 2 / Later 2, Done 2. Thử chuyển cột → hoàn tất → mở lại trên ID 104 rồi trả đúng stage/state, 0 tin nhắn mới. Form mở được, không lỗi console. planner.dev: search fixture rỗng, read/write/unlink trực tiếp qua RPC đều `AccessError`, giao diện To-do không thấy việc của admin. Evidence ngoài Git: `.local/data002/` (`logs-todo-tests*.log`, `todo-live.json`, `todo-roundtrip.json`, ảnh `shots/a1-*`) và `.local/native-data-20261102/todo-{dry-run,apply,verify}.json`.

Mở: `http://127.0.0.1:18069/odoo/to-do` bằng `admin` (mật khẩu ở `.local/dev-secrets.json`), F5 nếu trình duyệt còn phiên cũ. Rollback dữ liệu: xóa đúng 14 record theo namespace; rollback toàn bộ: snapshot `.local/data002/snapshot-20261102T041428Z/` (241 checksum, verify đạt, chưa diễn tập restore lên dev).

## NATIVE-DATA-002 — Lịch, trao đổi, bảng tổng hợp (CHG-20261102-008)

Bổ sung các mục còn trống cho admin ở dev18069, toàn bộ là dữ liệu giả lập: 8 lịch riêng tư, 3 nhóm trao đổi với 12 tin, 2 bảng tổng hợp sống và 6 mục danh mục công việc trung tính. Không thêm project/khách hàng/user thứ hai. Không đổi dữ liệu fixture cũ, invoice/expense vẫn nháp. Không cấp quyền, không gửi mail, không gửi push. Namespace `tp_native_data002_20261102`, 31 binding.

| Mục | Nội dung | Quyền / riêng tư |
| --- | --- | --- |
| Calendar | 8 cuộc họp từ 02/11 đến 13/11 (5 trong tuần 45, 3 trong tuần 46), giờ Asia/Saigon, lưu UTC. 5 lịch có link dự án DA-2026-001…004; mô tả gồm nội dung họp và ghi chú nguồn gốc giả lập | `privacy=private`, chỉ admin là organizer/attendee. Không alarm, không lặp, không video/địa điểm/đồng bộ. Tạo với `no_mail_to_attendees`/`dont_notify` |
| Discuss | 3 nhóm riêng: “Điều phối dự án”, “Kế hoạch Kinh doanh”, “Phối hợp Khảo sát – Thiết kế”. Mỗi nhóm 4 tin do admin đăng bằng `message_post`, có link dự án; không có số tiền, không có trạng thái ký/duyệt, không mention | `channel_type=group`, admin là thành viên duy nhất. Không đăng vào kênh General/Administrators có sẵn |
| Dashboards | “Điều phối dự án”: task theo dự án/trạng thái/giai đoạn, giờ làm theo dự án và phòng ban/nhân sự. “Hóa đơn và chi phí dự kiến”: 4 hóa đơn nháp và 6 khoản chi nháp, ghi rõ chưa hạch toán và không gộp với CRM/hợp đồng | `group_ids` rỗng, `allowed_user_ids=admin`, `company_ids=1`. Số liệu tính trực tiếp theo quyền người xem; cấu hình ở [`docs/demo/dashboards/`](dashboards/README.md) |
| TANPHAT ONE → Work Item Catalog | 6 mục trung tính `DEMO-WI-01…06` (khảo sát hiện trường, lập hồ sơ thiết kế, rà soát hồ sơ, họp phối hợp, tổng hợp báo cáo, quản lý tài liệu dự án). Chỉ thêm vì danh mục đang trống | Theo ACL `tp.work.item` hiện có; không gắn hạn mức hay quy trình |

### Bảng coverage 14 mục menu (live dev18069, 02/11/2026)

Actor mặc định là `admin`. Planner nghĩa là `planner.dev`, phạm vi đã có, không được cấp thêm. Số liệu đếm qua phiên HTTP của chính user; evidence ở `.local/data002/coverage-facts.json` và `data002-dev-http.json`.

| Menu | Kết quả hiện có | Bổ sung trong batch | Cách mở / bộ lọc | Gap / ghi chú |
| --- | --- | --- | --- | --- |
| Discuss | Admin là thành viên của 6 hội thoại: General, Administrators, chat OdooBot và 3 nhóm mới (12 tin) | 3 nhóm, 12 tin | Discuss → các nhóm nằm trong mục tin nhắn trực tiếp/nhóm ở thanh bên | Planner không thấy nhóm/tin; RPC trả `AccessError`. 12 `mail.message` không phải 12 email: `mail.mail` không tăng, 0 `mail.notification`, 0 push |
| To-do | 14 việc cá nhân của admin + 1 To-do onboarding có sẵn (CHG-007) | — | To-do; bộ lọc Open ẩn 2 việc Done, bỏ lọc để xem đủ 15 | Chờ audit TODO-001 |
| Calendar | 8 lịch của admin | 8 lịch | Calendar → Week → Today (tuần 45), mũi tên sang tuần 46 | Planner thấy khối “Busy” nếu thêm admin vào “Meet with”; tên/mô tả/người tham dự bị che, không ghi được. Đây là hành vi native của lịch private, không phải quyền riêng tư tuyệt đối với quản trị viên kỹ thuật |
| TANPHAT ONE | TP Projects: 4 dự án DA-2026-001…004 (managed); Work Item Catalog: 6 mục | 6 mục catalog | TANPHAT ONE → TP Projects / Work Item Catalog | TP Contracts/Survey/Design… chưa có menu native nên không thêm dữ liệu |
| Contacts | 24 liên hệ, trong đó 8 đối tác giả lập | — | Contacts; tìm tên đối tác hoặc mã DA trong ghi chú | — |
| CRM | 10 cơ hội, 4 cơ hội gắn tag DA-2026-001…004 | — | CRM → Pipeline; bỏ lọc “My Pipeline” để thấy cả 10 | Doanh thu kỳ vọng là giả lập; planner không có quyền CRM |
| Dashboards | Admin thấy 4: Invoicing, Project (chuẩn) + 2 bảng mới | 2 dashboard | Dashboards → Services/Finance | Planner thấy “No available dashboard”. Trên mobile Odoo chỉ hiện biểu đồ, bảng số liệu cần desktop. Không dùng nút Share |
| Invoicing | 4 hóa đơn khách hàng nháp, tổng 801.000.000 VND, phân bổ analytic 100% vào dự án | — | Invoicing → Customers → Invoices, lọc Draft | Lọc “Posted” trả 0 là đúng, không post để lấp bộ lọc |
| Project | 7 dự án / 30 task, trong đó 4 dự án mẫu / 28 task | — | Project; trong dự án bỏ lọc “My Tasks” nếu có | — |
| Timesheets | 20 dòng / 84 giờ (33,5 / 29,5 / 21 / 0) | — | Timesheets → All Timesheets (không phải My Timesheets) | An Hòa 0 giờ là chủ ý, không tạo giờ để đủ số |
| Employees | 12 nhân sự giả / 5 phòng ban mẫu (tổng 7 phòng ban) | — | Employees; Departments trong Configuration hoặc nhóm theo phòng ban | — |
| Expenses | 6 khoản chi nháp, tổng 7.160.000 VND, phân bổ analytic đúng dự án | — | Expenses → bỏ lọc “My Expenses”, xem danh sách | Không submit/approve/post |
| Apps | 88 module đã cài / 688 trong danh mục | — | Apps (admin) | Không cài module mới để làm đầy menu |
| Settings | Cấu hình thực đang dùng: công ty “Tan Phat Development”, VND, ngôn ngữ đang bật: en_US + vi_VN (VI-001, admin vi_VN; xem [VI_GLOSSARY_AND_COVERAGE](../i18n/VI_GLOSSARY_AND_COVERAGE.md)) | — | Settings (admin) | Không tạo cấu hình giả |

Kết luận batch A: **dữ liệu đủ cho kịch bản trình diễn** ở cả 14 mục. Đây **không** phải chức năng nghiệp vụ đã nghiệm thu, không phải UAT hay pilot. Ngoài 14 mục, admin còn thấy menu Link Tracker và Tests (module có sẵn); batch không thêm dữ liệu cho hai menu này.

### Runbook seed / verify

Seeder `.local/data002/seed_data002.py` (ngoài Git, như các helper trước). Template dashboard trong Git: `docs/demo/dashboards/`.

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe .local\data002\seed_data002.py test dry-run   # DB cô lập tp_tanphat_data002_test
.\.venv\Scripts\python.exe .local\data002\seed_data002.py test fail-test # lỗi giữa chừng phải rollback sạch
.\.venv\Scripts\python.exe .local\data002\seed_data002.py dev dry-run
.\.venv\Scripts\python.exe .local\data002\seed_data002.py dev apply
.\.venv\Scripts\python.exe .local\data002\seed_data002.py dev verify     # created=0, updated=0
```

- Seeder ghi bằng môi trường admin, không sudo; SUPERUSER chỉ dùng để tra XML ID. Có advisory lock và một transaction cho mỗi lần chạy. Mọi bản ghi được ràng buộc XML ID nên chạy lại không thêm trùng.
- Các assert chặn commit:
  - md5 dòng có sẵn của 22 bảng không đổi, trừ chính bản ghi của namespace (calendar, discuss, mail, dashboard, project/task, timesheet, invoice/line, expense, employee/department, CRM, user, user-group, TP assignment/grant/contract).
  - `mail.mail` và `mail.push` không tăng, 0 `mail.notification` cho tin mẫu.
  - Alarm rỗng, attendee chỉ admin.
  - Planner bị chặn qua ORM, có xóa cache trước khi kiểm.
  - Đếm fixture 8/10/4/28/12/5/20/6/4, invoice/expense đều draft.
- Rollback dữ liệu: xóa đúng 31 bản ghi theo binding `tp_native_data002_20261102`. Rollback toàn bộ: snapshot `.local/data002/snapshot-batchA-20261102T044155Z/` (dump + filestore, 241 checksum, `verify_backup.py` đạt), chưa diễn tập restore lên dev.

### Kiểm chứng

- **DB test cô lập** (`tp_tanphat_data002_test`, cổng 18139, đã neutralize):
  - dry-run tạo 31 bản ghi, 0 dòng có sẵn đổi.
  - fail-test: 8 binding được tạo trước lỗi cài sẵn; sau rollback còn 0 binding và 0 lịch.
  - apply 31, chạy lại `created=0`.
  - Template sửa giao diện cập nhật đúng 2 dashboard sở hữu; verify `updated=0`.
- **Dev18069:**
  - Snapshot trước, rồi dry-run, apply (`created=31`) và verify (`created=0`, `updated=0`, `existing_rows_changed={}`).
- **HTTP với phiên riêng từng user:**
  - Admin đọc đủ 8 lịch (private, alarm rỗng, 1 attendee), 3 nhóm (1 thành viên), 12 tin, 4 dashboard.
  - Planner:
    - Lịch: đọc thấy `Busy` và mô tả rỗng; ghi bị `AccessError`.
    - Nhóm, tin, dashboard: search rỗng, read `AccessError`.
    - Invoice: `AccessError`; expense: thấy 0.
    - To-do của admin: thấy 0.
- **UI Playwright:**
  - Admin, 1440 và 375: lịch tuần, Discuss, 2 dashboard mới và 2 dashboard chuẩn. Không lỗi console, không cuộn ngang.
  - Planner, 1440 và 375: không thấy lịch, nhóm, dashboard hay To-do của admin.
  - Đã tự xem ảnh. Dashboard hiện số sống: 28 task, 84 giờ, An Hòa 0; 4 hóa đơn nháp 801.000.000; 6 khoản chi 7.160.000.
- Evidence ngoài Git trong `.local/data002/`:
  - `data002-{test,dev}-*.json`, `data002-dev-http.json`, `coverage-facts.json`, `ui-*.json`
  - ảnh `shots/test/`, `shots/dev/`
