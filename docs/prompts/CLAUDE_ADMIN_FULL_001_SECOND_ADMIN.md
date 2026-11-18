# ADMIN-FULL-001 — Admin toàn hệ thống, bỏ giới hạn phòng ban

Làm việc trong `C:\TANPHAT ONE`. Prompt triển khai theo yêu cầu trực tiếp
18/11/2026, DEC-053. **Thay mô hình ủy quyền giới hạn bằng admin toàn hệ thống.**

## 1. Yêu cầu mới có ưu tiên

Người dùng chốt: tài khoản được cấp admin phải được coi là admin thứ hai,
toàn quyền như admin hiện tại, không bị giới hạn bởi phòng ban của họ.

- Khi được cấp admin: xem và quản trị mọi phòng ban, gồm cả phòng của chính
  họ; cùng chức năng, dữ liệu, field, menu và thao tác như admin hiện tại.
- Vai trò/chức danh HR vẫn là dữ liệu riêng, không tự đổi thành Trưởng phòng
  khi cấp admin. Tuy nhiên, **không dùng vai trò nhân viên cũ để chặn admin**.
- Admin được cấp có quyền quản lý người dùng/phân quyền và công cụ quản trị
  như admin hiện tại. Không giữ cơ chế chỉ admin gốc mới quản trị còn admin thứ
  hai phải đi qua adapter hạn chế. Mọi tài khoản admin có cùng năng lực quản trị
  ứng dụng; không tự thiết kế thêm cấp Owner và Admin có quyền khác nhau.
- Admin hiện tại có thể cấp/thu quyền admin; thu hồi xong người đó trở về
  quyền nghiệp vụ hợp lệ, không còn đặc quyền admin từ lần cấp này.
- Yêu cầu này thay quy tắc DEC-050 và prompt001/002: phòng mình giữ baseline,
  chỉ mở phòng khác, nguồn mixed/stock bị hạn chế vì delegation, không cấp
  nhóm admin, không được cấp tiếp admin. Không áp những yêu cầu cũ này cho
  người đã là full admin. Nhân viên thường vẫn theo quyền cũ.

Đây là admin **ứng dụng như tài khoản admin hiện tại**, không biến thành UID1,
không cấp quyền máy chủ/SSH/PostgreSQL, không bỏ đăng nhập hoặc dùng sudo cho
mọi người. Validation nghiệp vụ, trạng thái đã chốt và workflow mà admin hiện
tại cũng phải tuân thủ vẫn giữ; không biến admin thành quyền ghi state tùy ý.

## 2. Đọc và kiểm baseline trước sửa

Đọc AGENTS, PROJECT_STATUS/CHANGELOG/ROADMAP/DECISIONS, AI_CHANGE_WORKFLOW,
skill `.agents/skills/tanphat-odoo-delivery/SKILL.md` và delivery policy17/11.
Viết acceptance trước sửa code; giữ diff/checkpoint của phiên khác.

Source cần rà:

- `custom_addons/tp_admin_delegation/`: delegation, guards, navigation,
  HR/account/profile/overview, Reporting và Equipment/business adapters.
- Quyền/nhóm native Odoo20 và custom group hiện có; wizard phân quyền HR,
  Home/sidebar, API/RPC, field-group, file/export và cache/session.
- `docs/security/ADMIN_DELEGATE_001_POLICY.md`, coverage001, acceptance002,
  `docs/demo/HR_DELEGATE_FIX_001_ACCEPTANCE.md`.

Baseline theo bàn giao mới: delegation20.0.1.4.1, app `edb717f9`, bàn giao
`462d63c9`; lỗi mobile_phone đã sửa trên18069/PCserver. Server trước đó có1
grant hiệu lực, local0. Đọc lại thực tế, không hardcode tên, UID, số grant
hoặc ID phòng ban. Không triển khai lại bản cũ làm mất bản vá HR.

## 3. Dùng quyền native, không chỉ đổi nhãn

- Tái sử dụng addon và luồng cấp/thu đang có. Đặt nhãn **Quản trị viên** hoặc
  **Admin toàn hệ thống** thay cho Quản trị được ủy quyền có giới hạn.
- Dùng nhóm admin native và các nhóm quản trị ứng dụng cần thiết theo cấu
  hình hiện có để quyền hiệu lực tương đương admin hiện tại. `base.group_system`
  là điểm phải rà, không mặc định riêng nhóm này đã đủ mọi phân hệ/field.
- Có thể dùng một group vai trò full-admin để gom các nhóm cần thiết; không
  chép toàn bộ nhóm cá nhân/phân công của user admin vào từng người một cách mù.
  Giữ nguồn gốc quyền được thêm để thu hồi chính xác.
- Rà `_tp_is_main_admin`, `_tp_has_admin_delegation`, `delegate_actor`,
  `deny_authority`, guard target/wizard và capability/menu. Full admin phải đi
  đường quyền admin thực, không tiếp tục bị phân loại delegate giới hạn.
- Phải đọc ledger độc lập khi quản lý grant/revoke: hiện helper có thể trả
  false ngay khi user có nhóm system. Không để vừa cấp full-admin thì mất
  khả năng nhận diện và thu hồi chính grant đó.
- Không hardcode ngoại lệ cho một tài khoản để demo, không patch core hoặc
  global has_group, không dùng context frontend làm bằng chứng quyền admin.

## 4. Phạm vi quản trị phải hoạt động

So sánh admin hiện tại và admin được cấp trên cùng company/data:

1. Trang chủ, mọi workspace/menu đã triển khai, Cài đặt và Ứng dụng nếu admin
   hiện tại có quyền. Cùng bố cục chung, khác tên/avatar của từng tài khoản.
2. HR: tổng quan, danh sách, chi tiết, liên hệ/trường riêng/hợp đồng/tài liệu,
   quản lý tài khoản, khóa/mở/reset, phòng ban/chức vụ/phân quyền và thao tác
   xóa đã được admin hiện tại cho phép. Bỏ trạng thái Chỉ xem do vai trò cũ.
3. KH-KD/CRM/dự án/WBS/đấu thầu/hợp đồng và các nghiệp vụ hiện có: không loại
   hồ sơ cùng phòng, khác owner hoặc mixed chỉ vì người đó được cấp admin.
4. Kho: toàn bộ thiết bị, tồn kho, người dùng, gán/đổi/trả, đề xuất và lịch sử
   theo luồng admin hiện tại; giữ quy tắc chỉ gán máy chưa có chủ và tính nguyên tử.
5. Báo cáo: dashboard, kế hoạch quý/tháng/tuần, báo cáo/nguồn/tài chính/tệp và
   chức năng quản trị hiện có như admin hiện tại; không còn projection phòng khác.
6. Chấm công: quyền quản lý giống admin hiện tại. Assignment duyệt/chốt hoặc
   cấm tự duyệt nếu là điều kiện workflow áp cho cả admin thì giữ và giải thích;
   không tự bổ nhiệm reviewer hoặc sửa công thật để chứng minh full admin.
7. Tất cả đường search/count/read_group/filter/options/detail/file/chatter/
   export/API phải khớp quyền backend. Không chỉ hiện nút admin rồi bấm bị chặn.

Giữ multi-company native theo các công ty được phép; không dùng phòng ban làm
ranh giới full admin. Không tự tạo pháp nhân hoặc sửa company_ids ngoài nhu cầu
được giải thích trong kế hoạch triển khai. Báo riêng lỗi đã có ở admin hiện tại,
không coi lỗi đó là lý do cho phép bỏ kiểm soát nghiệp vụ toàn hệ thống.

## 5. Chuyển tài khoản hiện có và thu hồi

**Yêu cầu mới cho phép chuyển các tài khoản đang có grant admin hiệu lực sang
full admin khi thực thi prompt này**, gồm tài khoản thật đã được cấp trước đó.
Không chỉ sửa cho các lần cấp trong tương lai. Đây là ngoại lệ đúng scope so
quy tắc cũ không thay quyền người thật khi chưa chỉ định.

- Trước migration: đọc danh sách grant thực, trạng thái user và các nhóm gốc,
  backup đúng môi trường; evidence danh tính/nhóm để trong ignored.local.
- Migration idempotent, transaction/audit rõ; chỉ những người đã có grant còn
  hiệu lực. Không tạo người giả, không cấp thêm người chưa được chọn, không
  chuyển portal thành internal hoặc tự mở khóa user đang bị khóa.
- Giữ tên/avatar/mật khẩu, hồ sơ nhân viên, chức danh, phòng ban và dữ liệu.
  Cấp admin không tự sửa roster, grant tài chính hoặc assignment cá nhân.
- Cấp/thu có xác thực admin đang thao tác, lý do và nhật ký. Thu hồi chỉ bỏ
  quyền admin được quản lý, xử lý cả implied groups/quyền còn sót; không restore
  toàn bộ group snapshot cũ đè thay đổi nghiệp vụ hợp lệ trong thời gian đó.
- Nếu còn nguồn cấp admin khác khiến quyền hiệu lực chưa mất, phải phát hiện
  và xử lý/báo rõ, không trả Thu hồi thành công khi người đó vẫn là admin.
- Invalidate access/menu/field/view/session cache đúng cơ chế Odoo20: phiên và
  tab mở sẵn không tiếp tục chạy request mới bằng đặc quyền đã thu hồi.
- Giữ bảo vệ native cho user hệ thống và chặn làm mất admin hoạt động cuối
  cùng, gồm cập nhật nhóm/khóa/archive/xóa đồng thời. Không đặt thêm ranh giới
  phòng mình hoặc thứ bậc quyền bí mật giữa hai admin.

## 6. Kiểm chứng trước bàn giao

Lập bảng actor trước/cấp/thu và capability thực. Tối thiểu:

- Người được cấp mở được dữ liệu/chức năng như admin hiện tại ở **chính phòng
  mình, phòng khác và dữ liệu chung**. Không còn domain department cũ.
- HR list/detail/search không có field thiếu metadata; mobile_phone/private
  fields theo quyền HR admin thực, giữ bản vá metadata ở nhóm người thường.
- Full admin quản lý user/quyền như admin hiện tại; không còn guard delegate
  vô tình chặn thao tác này. Không thay chức vụ thực của ai chỉ để smoke.
- Thu hồi loại bỏ đặc quyền; group/vai trò nghiệp vụ hợp lệ còn đúng, phiên cũ
  bị kiểm lại. Cấp lại/migration chạy lại không nhân đôi grant hoặc làm mất quyền.
- Nhân viên thường không nhận quyền admin, không được đọc thêm private/file.
- Không admin được đổi máy sang thiết bị đã có chủ hoặc sửa trạng thái đã chốt
  trái workflow chỉ vì bỏ giới hạn phòng ban.

Kiểm static/unit phù hợp và probe chỉ đọc bằng quyền actor thực; kiểm browser
desktop/mobile qua phiên hợp lệ sẵn có, không reset mật khẩu để đăng nhập hộ.
Không seed fixture/CRUD phá dữ liệu trên main/server. Chỉ migration người đã
có grant là thay quyền thật được giao; không thu/cấp thử để quay video hoặc test.
Ca ghi/race/browser/thu hồi chưa chạy được phải ghi NOT_RUN, không gọi PASS từ
get_view hoặc has_access cấp model. Viết test hồi quy có ý nghĩa cho cấp/thu/
implied-group và chặn mất admin cuối; không tự chạy suite fixture trên DB chính.

## 7. Triển khai và bàn giao ngay

Áp18069 và PCserver theo policy17/11; **không bắt qua18079 hoặc tạo clone**.
Backup DB/filestore/source/config đúng môi trường trước migration; kiểm gói,
dependency, upgrade/restart cần thiết và rollback dữ liệu/quyền đúng phạm vi.

Commit/push đúng phần hoàn tất, deploy chính commit lên `server-pc`, Docker
`tp-odoo`, source `C:\Projects\TANPHAT-ONE`, config `/workspace/docker.odoo.conf`.
Kiểm lại topology trước dùng; giữ tunnel/filestore/domain. Public:
`https://hybrid-send-ready-ballot.trycloudflare.com`.

Không chép working tree chứa code dở/foreign diff. Cập nhật AGENTS nếu cần,
DEC-053/status/coverage/guide/acceptance/roadmap và luồng cấp quyền để mọi AI
khác không tiếp tục xây giới hạn DEC-050 đã thay. Hướng dẫn cách cấp/thu và
người dùng đăng nhập lại; báo commitSHA/version/backup/grant đã chuyển/kiểm
thực/phần chưa kiểm. Không tuyên bố đã chuyển người thật nếu mới chỉ code.
