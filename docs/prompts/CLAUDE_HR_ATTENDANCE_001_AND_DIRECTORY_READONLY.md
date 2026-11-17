# HR-ATTENDANCE-001 + HR-DIRECTORY-READONLY-001

Ngày17/11/2026, CHG-20261117-091, theo DEC-051/052. **PROMPT_READY_NOT_IMPLEMENTED.**

## 1. Nhiệm vụ, kiến trúc và quyền triển khai

Làm việc trong `C:\TANPHAT ONE`, vai trò thực thi. Xây chấm công tích hợp
vào TP HR. Mọi nhân viên nội bộ đang hoạt động được vào Nhân sự xem danh
bạ và bảng công của mình/đồng nghiệp, **không tạo/sửa/xóa nhân viên hoặc
giờ công**. Hợp đồng và thông tin riêng tư của người khác bảo vệ ở backend.
Hồ sơ cá nhân có tab **Công của tôi**, cùng nguồn dữ liệu bảng công chung.

Giữ một DB/môi trường, employee/user/phòng ban/mãTP hiện có, native Odoo/
OWL/QWeb/SCSS, một layout/session. Không tạo FE/DB/roster/account thứ hai,
không Excel làm runtime, không sửa core `odoo/`, `addons/`.

**Rollout đã được giao:** mỗi hạng mục hoàn tất thì commit/push đúng scope
và deploy PCserver ngay; áp18069 khi cần đồng bộ local. Không bắt buộc qua
18079, không tạo clone/cổngtest thay thế hoặc hỏi lại quyền deploy cùng scope.
Theo [quy trình](../operations/TP_CONTINUOUS_DELIVERY_POLICY.md), vẫn kiểm
cú pháp/build/quyền phù hợp, backup trước đổi schema/dữ liệu/quyền và kiểm
nhanh sau deploy; không suite/fixture phá dữ liệu main/server. Không dừng
ở kế hoạch/skeleton, làm tới kết quả dùng được và bàn giao từng hạng mục.

## 2. Đọc baseline và source

Đọc AGENTS, PROJECT_STATUS/CHANGELOG/ROADMAP/DECISIONS, AI_CHANGE_WORKFLOW,
AI_COORDINATION_WORKFLOW và skill `.agents/skills/tanphat-odoo-delivery/SKILL.md`;
[thiết kế HR](../architecture/TP_HR_ATTENDANCE_AND_DIRECTORY_DRAFT.md),
[chuẩn bảng](../ui/TP_TABLE_FILTER_STANDARD.md) và inventory hiện hành.

Kiểm git/checkpoint/dependency/runtime. Nếu batch ADMIN-DELEGATE/MEDIA
hoặc batch khác đang ghi: không chiếm/reset/finish checkpoint, stage/deploy
foreign diff hoặc code dở; làm phần độc lập rồi tích hợp tại điểm chốt.
Không nhận source chưa bàn giao là baseline đã nghiệm thu.

Local18069 `tp_tanphat_dev`/PG55432. Server theo bàn giao: `192.168.1.73`,
Docker `tp-odoo`, source `C:\Projects\TANPHAT-ONE`, runtime
`/workspace/docker.odoo.conf`; kiểm lại trước chạy. Giữ `/app`, `/dang-nhap`,
logo/title TANPHAT ONE, credit TADIC/tunnel/session. PublicURL từ runtime/
runbook, không hardcode QuickTunnel hostname vào source.

Đọc `tp_hr_workspace` (my_profile/identity/workspace_scope/account/role/
transfer/views/menu/shell), `tp_organization` (roster/employee/version),
Home và `tp_admin_delegation` nếu đã bàn giao. Native `hr.employee.public`
và `addons/hr_attendance` chỉ đọc. Source có `hr_timesheet` không có nghĩa
đã có công vào-ra; roster_parser cũ chỉ lấy5 cột nhân sự, không đọc ô công.
Kiểm module cài runtime, không suy từ manifest/module có trong thư mục.

## 3. Quyền người dùng và thông tin được chia sẻ

Áp mặc định dưới đây, ghi whitelist trong policy; không chờ hỏi từng field
để code phần độc lập. Không suy "xem thông tin cá nhân" là đọc mọi field HR.

| Vai trò | Phạm vi |
| --- | --- |
| Nhân viên nội bộ có hồ sơ hợp lệ | HR/danh bạ/chi tiết công việc/bảng công chung chỉ đọc; Công của tôi; phiếu đề nghị điều chỉnh của mình |
| Người phụ trách công được cấp quyền | Nhập/đối chiếu nguồn/xử lý công; duyệt/chốt theo capability/company/department được cấp, không tự duyệt |
| Trưởng phòng | Baseline nghiệp vụ hiện có; xử lý công chỉ khi có phân công riêng, không suy từ chức danh hoặc HEAD KH-KD |
| Admin chính/HR có quyền hiện tại | Giữ CRUD và quyền chuyên môn đã có; cấu hình người phụ trách/ca/lịch trong scope, không tự thành superuser/người ký |
| Admin được ủy quyền | Có baseline đọc nội bộ mới; quyền quản trị thêm theo policy hiện hành, không lách giới hạn phòng mình/private HR |
| Anonymous/portal/tài khoản khóa | Không vào danh bạ/bảng công nội bộ hoặc dùng direct link mở dữ liệu riêng |

Chia sẻ trong công ty được phép của user; không tự mở cross-company. TADIC
là đơn vị nội bộ, không tạo company/DB mới. Thiếu user–employee mapping thì
báo cần admin xử lý, không ghép theo tên hoặc tạo lại hồ sơ.
Áp cho tài khoản nhân viên hiện tại và tạo sau này theo điều kiện backend,
không chỉ thêm quyền thủ công cho một danh sách user cố định. Tạo account
mới không được kế thừa nhóm HR quản lý chỉ vì có menu Nhân sự.

**Cho xem đồng nghiệp:** mãTP, họ tên, avatar hợp lệ, phòng/đơn vị, chức vụ,
quản lý trực tiếp, email/điện thoại **công việc**, nơi làm việc. Ngày sinh
chỉ ngày/tháng khi có cờ chia sẻ hiện có; số riêng/năm sinh không mặc định
công khai. Không suy mobile_phone là công việc khi chưa phân loại rõ.
Danh bạ không hiện login/tình trạng bảo mật/APIkey/grant/nhóm quyền.

**Công được chia sẻ:** ngày, ca nếu có, giờ vào/ra, thời gian làm đã ghi nhận,
công đã xác nhận nếu có policy, trạng thái dữ liệu/chốt, cập nhật nguồn.
Nhân viên xem được công người khác theo ngày/tháng/phòng, không chỉ own.

**Ẩn với nhân viên khác:** hợp đồng và file; lương/phụ cấp/thưởng/phạt/
chi phí nhân sự; CCCD/hộ chiếu/thuế/BHXH/ngân hàng/địa chỉ nhà/liên hệ khẩn
cấp/gia đình/sức khỏe/kỷ luật/đánh giá nội bộ; password/token/groups; lý do
nghỉ, ghi chú HR, nội dung/minh chứng điều chỉnh, chứng từ y tế, GPS/ảnh
thiết bị/sinh trắc. Công chung dùng nhãn **Nghỉ đã duyệt**, không nêu bệnh.

Nhân viên thường không CRUD employee/công/ca/cấu hình/user/role qua module
HR; readonly này không vô hiệu self-service **Hồ sơ cá nhân của chính mình**
đã có: giữ đúng allowlist hiện hành, không mở thêm field hoặc sửa người khác.
Phiếu điều chỉnh riêng không là quyền write bản công; không tự đổi chức vụ/
phòng/user/company/group để lách. Admin/HR hợp lệ không bị hạ về readonly.

## 4. Backend và tích hợp native

- Ưu tiên `hr.employee.public` hoặc projection/read API có whitelist. Không
  cấp hr.group_hr_user/manager cho mọi người chỉ để hiện menu, không sudo
  full hr.employee rồi giấu tab hợp đồng ở XML. UI phản ánh quyền server.
- Kiểm ACL cộng quyền/rule OR/field groups: create/write/unlink/import/copy/
  bulk/action/wizard/directRPC/URL khác cũng chặn. Không patch toàn cục
  has_group/check_access. Sudo chỉ sau kiểm actor/scope/field/operation thật.
- Search/filter/name_search/options/count/read_group/drilldown/payload phải
  đúng whitelist/tập công ty. Không leak private field qua sắp xếp/lọc lỗi.
- File/preview/download/chatter/history/notifications đi theo quyền nguồn;
  không lộ hợp đồng qua smartbutton/tên file/token/attachment hoặc HTML ẩn.
  Không public hóa attachment. Token tải hợp lệ vẫn đúng native policy.
- Mặc định nhân viên không xuất danh bạ/công **người khác**; Công của tôi
  được xuất whitelist, HR xuất theo scope. Chặn native export/API, không chỉ
  bỏ nút. Không hứa ngăn copy/chụp màn dữ liệu đã cho xem.
- Ưu tiên reuse hr.attendance cho phiên vào-ra hợp lệ trên build20, thêm
  staging nguồn/import/daily summary/correction/period nhỏ khi cần. Summary
  có lineage/tính lại, không database công thứ hai hoặc engine tính lương.
- Nếu cài native Attendance, rà self-checkin/systray/kiosk/PIN/barcode/token/
  controller sudo và `_attendance_action_change`: mở quyền xem không tự
  cho viewer ghi công qua đường native khác. Không tự bật kiosk/geolocation/
  chụp ảnh/auto-checkout/overtime; không tắt route/cron khác chưa đánh giá.

## 5. Import Excel và một nguồn nhân sự

Nguồn người dùng đã gửi, còn tồn tại khi soạn prompt: ưu tiên
`C:\Zalo Received Files\bang cham cong vao ra (1).xlsx`; tham khảo
`C:\Zalo Received Files\202611_tanphat_chamcong_tuan1.xlsx` theo kỳ thật.
Đọc skill spreadsheet khi phân tích. Xác minh hash/header/ngày/sheet giờ;
roster snapshot cũ không chứng minh công. Không chạy macro/external link
hoặc đưa tên/giờ công/file raw vào Git.

- Mapping mã máy/mã nguồn → employeeID/company hiện có, giữ mãTP. Không
  dùng STT theo nhóm/OdooID làm mã máy hoặc match chỉ theo tên; không tạo
  lại roster/user/cập nhật chức vụ/phòng ban từ file công.
- File → preview người/ngày/giờ, đếm hợp lệ/trùng/xung đột/chưa mapping →
  áp dòng có căn cứ → báo kết quả/truy vết. Chống trùng cả file/sheet khác
  chứa cùng sự kiện/ngày; không chỉ file hash. Retry không nhân công, nguồn
  sửa nội dung thành correction, không xóa kỳ cũ rồi import lại.
- Lưu log nguồn/row/event/timestamp đầy đủ; nhiều lần vào-ra có thứ tự.
  Thiếu giờ ra/không rõ chiều ở staging, không điền giờ giả để qua constraint.
- UTC trong DB, ngày công theo timezone lịch làm (mặc định Asia/Ho_Chi_Minh);
  xử lý ô giờ Excel số/text/ngày, merged header, ca đêm/nhiều ca/nghỉ trưa.
  Không lấy min/max mọi punch rồi coi là một ca đầy đủ.
- Được nhập các dòng thật mapping/ngày/giờ chắc chắn sau backup/preview vào
  kỳ nguồn đúng, không đưa vào hôm nay hoặc tự chốt/duyệt tăng ca/chấm đủ.
  Dòng mơ hồ giữ chờ, không chặn toàn module. Không có file/giờ thì hoàn
  tất importer/UI rỗng thật và báo thiếu, không seed công giả main/server.
- Nhập mỗi tuần không là realtime: luôn hiện **Dữ liệu cập nhật đến…**.

## 6. Lịch, công và điều chỉnh/chốt

Reuse resource.calendar/lịch nhân viên và nghỉ đã duyệt nếu có; cấu hình
theo hiệu lực, không mặc định ai cũng8 giờ/nghỉ thứ Bảy. Lưu lịch/phòng tại
ngày công; đổi lịch/phòng hiện tại không viết lại kỳ lịch sử đã chốt.
Archive/nghỉ việc giữ lịch sử theo HR policy, không mở archive vào danh bạ chung.

Tách giờ ghi nhận/giờ theo lịch/công dự kiến-công xác nhận/tăng ca duyệt;
thiếu policy là **Chưa cấu hình/Chưa xác nhận**, không0. Không tự suy đi
muộn/phạt/nghỉ không phép/tăng ca hoặc tính lương. Ngày đang làm/tương lai/
nghỉ theo lịch/thiếu nguồn/thiếu giờ khác nhau; tăng ca chưa duyệt không cộng công.

Luồng: nguồn vào-ra → đối chiếu lịch → nhân viên xem → đề nghị bổ sung →
người được phân công duyệt/trả có lý do → cập nhật công+audit → HR rà/chốt.
Không suy người duyệt từ chức danh. Chưa reviewer thì chỉ dẫn cấu hình,
không giả phê duyệt. Nhân viên tạo/sửa/hủy phiếu nháp của mình, không xem
phiếu đồng nghiệp hoặc tự duyệt; đã gửi/duyệt đi qua action transition backend.
Duyệt/công/audit trong transaction, chống retry/race/duyệt2 lần. Kỳ chốt
không sửa/xóa trực tiếp; mở/đính chính có quyền/lý do/version, giữ log gốc.

## 7. Giao diện sáng, rõ và đẹp

Reuse navbar/sidebar/identity/back/input/filter hiện có; không navbar thứ hai
hoặc giả user.isSystem. HR của viewer có nhãn **Chỉ xem**; detail đồng nghiệp
là trang đọc whitelist, không full HR form disable input. Avatar dùng identity
thực; giữ sửa filestore của task media, không ảnh giả che dữ liệu thất lạc.

Sidebar: **Nhân viên → Danh sách**; **Chấm công → Tổng quan công/Bảng công/
Công của tôi/Yêu cầu của tôi**. HR được giao có thêm Xử lý điều chỉnh/Nhập
dữ liệu/Chốt kỳ; cấu hình trong nhóm quản trị hiện có. Viewer không thấy
Tài khoản&phân quyền/Lưu trữ/Xóa/Đợt nhập/Hồ sơ thiếu riêng tư; không tạo
sidebar duplicate hoặc công cụ làm fake "Đang phát triển" cho scope đã giao.

Hồ sơ cá nhân → **Công của tôi**: lịch tháng+bảng ngày, chuyển tháng, trạng
thái chốt, nguồn cập nhật; click ngày xem giờ/ca/kết quả và yêu cầu riêng.
EmployeeID lấy từ session backend; mở đồng nghiệp không đổi owner của tab này.

Dashboard: filter kỳ/phòng ở đầu,4–5 KPI có định nghĩa, **chart lớn ở trên**,
danh sách cần chú ý bên dưới. Donut chất lượng dữ liệu dùng nhóm không
chồng; bar theo ngày/phòng. Đi muộn và thiếu giờ có thể giao nhau nên là
KPI riêng. Chart/KPI/table/drilldown cùng population/đơn vị/ngày nguồn;
loại ngày tương lai đúng định nghĩa, không chart 0 giả khi thiếu dữ liệu.

Bảng ngày: MãTP · Nhân viên · Phòng · Ngày/ca · Vào · Ra · Giờ ghi nhận ·
Công xác nhận · Tình trạng. Bảng tháng: một người/dòng, cột ngày, tổng theo
loại; sticky nhân viên/header, scroll trong bảng không ép31 cột nhỏ. Mobile
mặc định ngày/card; click ô mở đúng ngày, back giữ lọc/trang/chế độ.

Filter riêng mọi bảng/modal/bảng con: kỳ, phòng, nhân viên/mãTP, trạng thái
dữ liệu/chốt; HR thêm nguồn/lần nhập/xung đột/người xử lý nếu phù hợp. Reuse
SearchModel/helper, chip đã áp, clear giữ company/owner/security, count/
10/20/50/100 đúng đơn vị nhóm/dòng; inventory DEC-044 có coverage hoặc N/A rõ.

Thiết kế: nền gần #F3F7FC, nội dung trắng/border #D7E2EF, chữ navy #17324D,
nhấn xanh thương hiệu; xanh lá hợp lệ, cam cần kiểm tra, đỏ lỗi, xanh dương
nghỉ đã duyệt, xám chưa nguồn. Reuse font/token hiện có; chart 300–360 px
desktop, tooltip đơn vị/legend rõ, không private data. Zebra nhẹ/border rõ,
badge chữ+icon, cột không chồng, nút chính/phụ gọn; hover/panel 150–200 ms,
focus/keyboard/reduced-motion/touch 44 px, không animate mọi hàng hoặc sửa login.

## 8. Chia phần dùng được, push và deploy ngay

| Phần | Đầu ra bắt buộc trước push/deploy |
| --- | --- |
| S1 — HR chỉ xem | Nhân viên vào HR/danh bạ/detail an toàn; backend cấm CRUD/private/export/file, HR/admin không mất chức năng |
| S2 — Nguồn/bảng công | Import preview-apply chống trùng, lịch/ngày-tháng/detail, nguồn thiếu rõ; nhập dòng thật đủ căn cứ đúng kỳ, không giả công |
| S3 — Công của tôi/xử lý | Tab profile cùng nguồn, đề nghị/duyệt/trả/chốt/đính chính đúng actor/scope/history; reviewer cấu hình nếu thiếu |
| S4 — Dashboard/hoàn thiện | KPI/chart/drilldown/filter/mobile/empty/export hợp quyền, ảnh desktop/mobile, guide và handoff đầy đủ |

Viết acceptance/policy trước code; không để lộ action/menu dở giữa các phần.
Thiếu policy công thì hoàn tất xem/import/điều chỉnh với trạng thái chưa
xác nhận, không giả số hoặc dừng toàn task. Không framework BI/workflow/
filter mới hoặc tính năng AI/GPS/khuôn mặt/payroll không được yêu cầu.

## 9. Kiểm tra và bằng chứng, không mở18079

Tạo `docs/demo/HR_ATTENDANCE_001_ACCEPTANCE.md` trước code; mỗi ca có actor/
input/expected/env/evidence/PASS-FAIL-NOT_RUN. Tối thiểu:

- AT01: hai nhân viên hai phòng xem HR/công đồng nghiệp nhưng không CRUD
  qua UI/RPC/import/copy/bulk/wizard hoặc lấy private fields/files.
- AT02: private không lộ qua metadata/search/filter/count/export/chatter/
  history/token; anonymous/portal/khóa/cross-company bị chặn.
- AT03: admin/HR/delegation/self-profile đúng policy; không vô tình mở
  hợp đồng/lương/quyền hoặc bypass own-department guard.
- AT04: import trùng file/sheet/ngày/retry chống nhân công, sai mapping/
  ngày/giờ/thiếu giờ ra giữ chờ, roster/user/mã TP giữ nguyên.
- AT05: UTC/local/ca đêm/nhiều ca/nghỉ trưa/ngày nghỉ/ngày đang làm/tương lai/
  chưa cấu hình đúng; null khác0, không tự tính lương/nghỉ không phép.
- AT06: Công của tôi không đổi người bằng sửaID; correction self-only,
  reviewer khác, retry/race/lock/chốt/đính chính giữ lịch sử.
- AT07: KPI/chart/day-month/filter/count/page/export cùng tập/đơn vị;
  viewport375/390/768/1366/1440, zoom/reduced-motion/back dùng được.
- AT08: native self-checkin/kiosk/systray/controller/groupOR không mở đường
  ghi cho viewer, không tự thu GPS/ảnh/biometric.
- AT09: deploy/restart public auth/HR/avatar/file/SW/RPC ổn; source/commit/
  moduleversion khớp, không cache phiên trước lộ private data.

Chạy XML/manifest/Python/JS/Ruff, logic in-memory không nối DB đang dùng khi
phù hợp. Viết regression cho quyền/import/tính công; không chạy suite có
fixture hoặc tạo user/công giả trên main/server, không mở18079/cổngtest khác.
Smoke account hợp lệ sẵn có/đọc/denied phù hợp; không thử xóa/sửa nhân viên
thật để chứng minh bị chặn. Không ghi Odoo suite/UAT/audit PASS nếu chưa chạy.
Giữ web.base.url bằng public origin cho admin nếu LAN login thay cấu hình;
không in credential/cookie. Dùng Playwright ảnh và assert payload/quyền,
không chỉ screenshot hoặc HTTP200. Check docs không thay test security.

## 10. Rollout, tài liệu và báo cáo

Mỗi S hoàn tất: cập nhật source/tests/docs, review diff, backup đúng DB/
filestore/source/config bị ảnh hưởng; commit/push và deploy chính release
đó lên PCserver/18069 theo task, upgrade/restart đúng module/service, kiểm
public và sửa/rollback nếu lỗi. Không hỏi lại quyền đã giao, không restore
test/localDB đè server, không restart tunnel hoặc dùng workingtree dở.

Nếu dependency/batch khác chưa bàn giao/push, tích hợp ở điểm chốt và báo
đúng, không `git add .`/forcepush/finish hộ hoặc coi code của phiên khác đã kiểm.
Thiếu SSH/Git access thì hoàn tất phần độc lập và báo bước chưa làm thật.

Bàn giao policy field/role/route/export/file; schema/source/mapping/lịch/
formula; acceptance; filter inventory; userguide nhân viên/HR; runbook nhập/
deploy/rollback. Cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP đúng kết quả,
start/finish/check đúng batch. Logs/HAR/ảnh/hash nguồn private trong
`.local/hr-attendance001/` ignored; không rawExcel/PII/secret/dump/filestore lên Git.

Báo cuối tiếng Việt: link HR/Công của tôi, role thấy gì/trường đã ẩn, nguồn/
kỳ/dòng nhập-dòng chờ, cách đề nghị/duyệt/chốt, ảnh desktop/mobile, commitSHA/
push/release/version/backup/kiểm thật/gap. Không báo máy realtime khi chỉ
Excel, không nhận chỉ có source/dữ liệu giả là tính năng thật đã hoàn tất.
