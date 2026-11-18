# ADMIN-FULL-001 — Admin toàn hệ thống, bỏ giới hạn phòng ban

Làm việc trong `C:\TANPHAT ONE`. Prompt triển khai theo yêu cầu trực tiếp
18/11/2026, DEC-053/054. **Admin được cấp quản trị mọi phòng; chỉ admin gốc cấp/thu admin.**

## 1. Yêu cầu mới có ưu tiên

Người dùng chốt: tài khoản được cấp admin phải được coi là admin thứ hai,
toàn quyền như admin hiện tại, không bị giới hạn bởi phòng ban của họ.

- Khi được cấp admin: xem và quản trị mọi phòng ban, gồm cả phòng của chính
  họ; cùng chức năng, dữ liệu, field, menu và thao tác như admin hiện tại.
- Vai trò/chức danh HR vẫn là dữ liệu riêng, không tự đổi thành Trưởng phòng
  khi cấp admin. Tuy nhiên, **không dùng vai trò nhân viên cũ để chặn admin**.
- Admin được cấp quản trị người dùng và nghiệp vụ trên mọi phòng, kể cả phòng
  mình. **Ngoại lệ duy nhất về thẩm quyền admin: chỉ admin gốc cấp/thu quyền
  admin; admin được cấp không được cấp admin cho ai, kể cả bản thân hoặc cấp
  gián tiếp qua người/nhóm khác.** Quản lý vai trò nghiệp vụ thông thường vẫn
  theo quyền admin ứng dụng, không được làm phát sinh quyền admin.
- Chỉ admin gốc được cấp/thu admin và sửa nguồn xác định admin gốc. Thu hồi
  xong người nhận trở về quyền nghiệp vụ hợp lệ, không còn đặc quyền đã cấp.
- Các đường sửa chính sách/nhóm quản trị hoặc chạy code có thể vòng qua ngoại
  lệ này phải dành admin gốc; không mở chúng chỉ để giao diện giống admin.
- Yêu cầu này thay quy tắc DEC-050 và prompt001/002: phòng mình giữ baseline,
  chỉ mở phòng khác và nguồn mixed/stock bị hạn chế vì delegation. Riêng
  cấm cấp tiếp admin được người dùng xác nhận lại tại DEC-054; phải giữ ở
  backend. Nhân viên thường vẫn theo quyền cũ.

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
  Giữ nguồn gốc quyền được thêm để thu hồi chính xác. Không cấp nhóm system
  theo cách vô tình mở quản lý nhóm, security hoặc native cấp admin.
- Tách capability quản trị nghiệp vụ toàn hệ thống khỏi capability cấp/thu
  admin. `_tp_is_main_admin` chỉ kiểm `base.group_system` hiện tại không đủ
  xác định admin gốc; nguồn admin gốc phải được kiểm chứng, được bảo vệ và
  không tự tạo/cấp từ luồng admin thứ hai. Không hardcode login/tên/UID suy đoán.
- Rà `_tp_is_main_admin`, `_tp_has_admin_delegation`, `delegate_actor`,
  `deny_authority`, guard target/wizard và capability/menu. Full admin phải đi
  đường quyền admin nghiệp vụ đầy đủ, không tiếp tục bị giới hạn phòng ban;
  nhưng cấp/thu admin phải kiểm riêng đúng actor admin gốc.
- Phải đọc ledger độc lập khi quản lý grant/revoke: hiện helper có thể trả
  false ngay khi user có nhóm system. Không để vừa cấp full-admin thì mất
  khả năng nhận diện và thu hồi chính grant đó.
- Không hardcode ngoại lệ cho một tài khoản để demo, không patch core hoặc
  global has_group, không dùng context frontend làm bằng chứng quyền admin.

## 4. Phạm vi quản trị phải hoạt động

So sánh admin hiện tại và admin được cấp trên cùng company/data:

1. Trang chủ và mọi workspace/menu nghiệp vụ đã triển khai, cùng bố cục
   chung, khác tên/avatar của từng tài khoản. Cài đặt nghiệp vụ mở theo quyền;
   chức năng quản trị quyền/security, cài module/chạy code tùy ý có thể cấp
   admin phải chỉ dành admin gốc, không mở bằng native group không kiểm soát.
2. HR: tổng quan, danh sách, chi tiết, liên hệ/trường riêng/hợp đồng/tài liệu,
   quản lý tài khoản thường, khóa/mở/reset, phòng ban/chức vụ/vai trò nghiệp
   vụ và thao tác xóa đã được admin hiện tại cho phép. Bỏ trạng thái Chỉ xem
   do vai trò cũ. Tài khoản/credential admin gốc và quyền admin được bảo vệ
   theo mục 5; không đổi email reset/group/identity để chiếm admin gốc.
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
- Cấp/thu phải xác thực **admin gốc đang thao tác**, lý do và nhật ký, kiểm
  lại actor/quyền ngay trong transaction trước ghi ledger/nhóm. Không nhận
  cờ owner/is_admin từ client hoặc caller `.sudo()` làm thẩm quyền admin gốc.
- Thu hồi chỉ bỏ
  quyền admin được quản lý, xử lý cả implied groups/quyền còn sót; không restore
  toàn bộ group snapshot cũ đè thay đổi nghiệp vụ hợp lệ trong thời gian đó.
- Nếu còn nguồn cấp admin khác khiến quyền hiệu lực chưa mất, phải phát hiện
  và xử lý/báo rõ, không trả Thu hồi thành công khi người đó vẫn là admin.
- Invalidate access/menu/field/view/session cache đúng cơ chế Odoo20: phiên và
  tab mở sẵn không tiếp tục chạy request mới bằng đặc quyền đã thu hồi.
- Giữ bảo vệ native cho user hệ thống và chặn làm mất admin hoạt động cuối
  cùng, gồm cập nhật nhóm/khóa/archive/xóa đồng thời. Ngoại lệ admin gốc và
  admin được cấp phải hiện rõ, không khôi phục ranh giới phòng mình.

### Bảo vệ ngoại lệ cấp admin ở backend

- Admin được cấp không tạo/cập nhật/xóa ledger hoặc wizard cấp/thu admin;
  không sửa protected group/implied group, memberships hoặc quyền user để
  biến mình/người khác thành admin hay admin gốc.
- Kiểm cả `res.users`, `res.groups`, lệnh quan hệ lồng, copy/default/context,
  HR role wizard, import, API/RPC và các action dùng sudo. Chặn cấp quyền kỹ
  thuật tương đương admin dù không ghi vào ledger ứng dụng.
- Không cho thay nguồn admin gốc, mật khẩu/API key/MFA/reset email/partner
  hoặc khóa/xóa/hạ admin gốc để chiếm quyền. Self-service đổi mật khẩu của
  chính mình theo native được giữ, không trở thành đường quản lý admin gốc.
- Security ACL, server action Python, cấu hình cho chạy code/import module
  hoặc đường admin kỹ thuật có thể sửa guard phải dành admin gốc. Chặn đường
  vòng này là thực thi ngoại lệ cấp admin, không hạn chế nghiệp vụ phòng ban.
- Ẩn nút Cấp/Thu admin cho admin được cấp; kiểm server vẫn bắt buộc khi gọi
  trực tiếp. Nhãn nêu rõ Quản trị viên (không được cấp quyền admin).
- Log người/thời gian/đích/lý do cấp/thu; không lưu mật khẩu hoặc secret.


## 6. Kiểm chứng trước bàn giao

Lập bảng actor trước/cấp/thu và capability thực. Tối thiểu:

- Người được cấp mở được dữ liệu/chức năng như admin hiện tại ở **chính phòng
  mình, phòng khác và dữ liệu chung**. Không còn domain department cũ.
- HR list/detail/search không có field thiếu metadata; mobile_phone/private
  fields theo quyền HR admin thực, giữ bản vá metadata ở nhóm người thường.
- Admin được cấp quản lý tài khoản thường/vai trò nghiệp vụ trên mọi phòng,
  nhưng không thấy nút và không gọi được cấp/thu admin. Admin gốc vẫn cấp/thu
  được, không chặn nhầm bởi guard mới. Không thay chức vụ thật để smoke.
- Ca âm bắt buộc: direct RPC/ledger, `res.users` group write, `res.groups`
  membership/implied group, HR wizard/import/context/sudo; không cấp được admin
  hoặc sửa nguồn/credential admin gốc. Chặn cả tạo tài khoản mới có admin group.
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
implied-group, ngoại lệ chỉ-admin-gốc và chặn mất admin cuối; không tự chạy
suite fixture trên DB chính.

## 7. Triển khai và bàn giao ngay

Áp18069 và PCserver theo policy17/11; **không bắt qua18079 hoặc tạo clone**.
Backup DB/filestore/source/config đúng môi trường trước migration; kiểm gói,
dependency, upgrade/restart cần thiết và rollback dữ liệu/quyền đúng phạm vi.

Commit/push đúng phần hoàn tất, deploy chính commit lên `server-pc`, Docker
`tp-odoo`, source `C:\Projects\TANPHAT-ONE`, config `/workspace/docker.odoo.conf`.
Kiểm lại topology trước dùng; giữ tunnel/filestore/domain. Public:
`https://hybrid-send-ready-ballot.trycloudflare.com`.

Không chép working tree chứa code dở/foreign diff. Cập nhật AGENTS nếu cần,
DEC-053/054/status/coverage/guide/acceptance/roadmap và luồng cấp quyền để mọi AI
khác không tiếp tục xây giới hạn DEC-050 đã thay. Hướng dẫn cách cấp/thu và
người dùng đăng nhập lại; báo commitSHA/version/backup/grant đã chuyển/kiểm
thực/phần chưa kiểm. Không tuyên bố đã chuyển người thật nếu mới chỉ code.
