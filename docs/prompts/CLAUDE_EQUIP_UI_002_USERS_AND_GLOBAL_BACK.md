# EQUIP-UI-002 / UI-BACK-001 — Bảng thiết bị theo nhân viên và Quay lại toàn hệ thống

**Phạm vi Kho đã được thay thế — 16/11/2026.** Yêu cầu mới nhất dùng
[EQUIP-SIMPLE-003](CLAUDE_EQUIP_SIMPLE_003.md) / DEC-047: hai menu Thiết bị/Yêu
cầu đề xuất, một bảng có stock/đang dùng, gán/đổi/trả/chuyển trực tiếp. Không
tiếp tục dựng lại dashboard/menu Kho theo prompt cũ này. Phần Quay lại dùng
chung (UI-BACK-001 / DEC-046) đã triển khai vẫn giữ hiệu lực. Nội dung dưới
là lịch sử triển khai EQUIP-UI-002.

Làm việc trong `C:\TANPHAT ONE`. Thực hiện code và áp main **18069** sau
backup, database `tp_tanphat_dev`. Không commit/push.

## 1. Kết quả người dùng cần

1. **Thiết bị & người sử dụng** chỉ hiển thị thiết bị thực sự gắn nhân viên;
   thiết bị stock chỉ ở **Thiết bị tồn kho**, không lẫn trong bảng nhân viên.
2. Bảng đơn giản: loại/thiết bị, tình trạng, ghi chú hỏng hóc, người đang dùng
   và phòng ban rõ ràng, đọc tên/mã nhân viên từ HR đang có.
3. Có nút **← Quay lại** thống nhất ở mọi màn chi tiết trong hệ thống đang cài,
   trở về đúng nơi mở, không mất bộ lọc/trang hoặc bỏ qua bảo vệ chưa lưu.
4. Nâng tiếp dashboard theo trao đổi: chữ dễ đọc, donut lớn, biểu đồ loại
   thiết bị không có thanh cuộn nhỏ, đề xuất riêng và dữ liệu thiếu thu gọn.

Đây là bổ sung sau EQUIP-UI-001 CHG-20261114-014. Tái sử dụng giao diện sáng,
native Odoo20/OWL/QWeb/SCSS hiện có; không làm lại app/framework hoặc thêm module
nghiệp vụ. Yêu cầu mới **thay phạm vi danh sách tổng** của menu Thiết bị & người
sử dụng trong prompt UI cũ. Cùng DB/session/employee ID, giữ quyền hiện hành.

## 2. Đọc và chuẩn bị

Đọc AGENTS, PROJECT_STATUS, AI_CHANGE_WORKFLOW, ROADMAP, DECISIONS, skill chung
`.agents/skills/tanphat-odoo-delivery/SKILL.md`, chuẩn lọc DEC-044 và inventory.
Đọc source/caller trước thiết kế:

- `custom_addons/tp_equipment/views/equipment_views.xml`, `menus.xml`.
- `custom_addons/tp_equipment/models/equipment.py`, `dashboard.py`, export controller.
- `custom_addons/tp_equipment/static/src/{table,form,dashboard,sidebar}/`.
- Shell/navigation chung trong `tp_web_home`, các form/client action của HR,
  KH-KD, Contracts, CRM/Projects và app/cấu hình hiện đang có quyền truy cập.
- `custom_addons/tp_hr_workspace/static/src/profile/employee_profile.{js,xml}`:
  đã có Quay lại/backToEmployees/restore và guard riêng, không tạo nút trùng.
- Odoo20 thực tế `addons/web/static/src/webclient/actions/action_plugin.js`,
  `views/form/form_controller.{js,xml}`, control panel. Chỉ đọc core, không sửa.

Quan sát source hiện tại: `action_equipment` là list tổng chưa có domain riêng
cho người sử dụng; cột `tp_custody` bị đặt tên “Trạng thái” bên cạnh cột tình
trạng kỹ thuật; không có cột ghi chú tình trạng trong bảng. Vì vậy stock/người
trống cùng xuất hiện. Sửa domain/action/view đúng chỗ, không chỉ CSS che dòng.

Kiểm git/checkpoint/workflow trước sửa, start đúng batch; không xóa hoặc finish
batch khác. Backup DB+filestore+source/config metadata private, không in secret.
Ghi baseline ID/hash của thiết bị/phiếu/nguồn nhập/HR/user/quyền. Theo chỉ đạo
hiện hành làm trực tiếp18069, không18079/clone/bộ test riêng/fixture giả; vẫn
lint/parse theo scope và đối chiếu browser thật, không báo test PASS khi bỏ test.

## 3. Tách dữ liệu màn nhân viên và màn tồn kho

### Thiết bị & người sử dụng

Phạm vi mặc định: thiết bị vật lý/linh kiện độc lập đang quản lý, không là
service, có `tp_employee_id` xác định và `tp_custody` thuộc employee/loan.
Đối chiếu enum/field thực tế trước viết domain. Dùng domain action/helper backend
nhất quán với count/filter/export, không lọc JS trên trang vừa tải.

- Không có dòng stock/vendor/department/location/none hoặc không có người rõ
  ràng trong bảng nhân viên. Không chỉ thêm điều kiện `!= stock` vì vẫn còn
  các trường hợp không ai giữ. Draft/ngừng quản lý ở lối xem riêng thích hợp.
- Không yêu cầu nhân viên phải có tài khoản res.users mới được hiện thiết bị.
  Người đã archive HR nhưng còn giữ máy vẫn phải truy vết được, có dấu hiệu
  “Hồ sơ nhân viên đã lưu trữ”, không âm thầm lọc mất thiết bị chưa thu hồi.
- Tên, mã nhân viên TP…, avatar và phòng ban hiện tại lấy từ **employee ID đã
  liên kết**. Không so tên tài khoản, fuzzy-match tên Excel hoặc dựng bảng người
  riêng. HR đổi tên/phòng thì hiển thị hiện tại đổi theo ID; lịch sử giao nhận
  cũ vẫn giữ snapshot đúng thời điểm. Không cập nhật phòng ban hoặc user thật.
- HR chưa có phòng thì ghi “Chưa có phòng ban”; thiếu mapping giữ chờ, không
  gán phòng/người giả vì “có tên gần giống”. Không tạo lại nhân viên/phòng ban.

### Thiết bị tồn kho và dùng chung

Giữ màn Tồn kho: vật lý đang quản lý + custody stock, có thể tốt/hỏng/chưa kiểm
tra; không đồng nhất tồn kho với availability available. Không xóa hay đổi
người giữ của thiết bị để làm hai danh sách khớp ý muốn.

Thiết bị dùng chung/đặt tại vị trí và chưa xác định người vẫn được bảo toàn,
truy cập qua mục phụ **Thiết bị dùng chung & chưa xác định người** hoặc quản
trị tất cả hồ sơ, không mở thêm nhóm menu chính rườm rà. Dịch vụ/nháp/ngừng
quản lý cũng còn đường truy cập phù hợp; dòng nguồn chờ không tự áp mapping.

Giữ dashboard **Đang sử dụng** tổng quát theo định nghĩa hiện có nếu còn gồm
dùng chung; drill-down phải tới đúng tập. Không đổi số tổng này bằng số nhân
viên giữ rồi làm phần dùng chung biến mất. Thẻ/legend phải ghi rõ “gồm thiết
bị giao nhân viên và dùng chung”; khi cần mở danh sách tổng quát dùng action
phụ đúng domain. Tên “Giao nhân viên” dùng cho tập cá nhân nếu tạo chỉ tiêu đó.

## 4. Bảng mới: lấy người sử dụng làm trọng tâm

Thiết kế cột mặc định như sau:

| Cột | Trình bày |
| --- | --- |
| Người sử dụng | Avatar HR + họ tên đầy đủ, mã nhân viên dòng phụ; không nhét thông tin riêng tư |
| Phòng ban | Tên đầy đủ theo HR, không viết tắt khó hiểu |
| Loại thiết bị | Laptop, máy tính để bàn, màn hình… từ category |
| Thiết bị | Tên/model ngắn để phân biệt, mã TB ở dòng phụ; nguyên văn xem trong chi tiết |
| Tình trạng | Một badge tình trạng kỹ thuật; bỏ cột Nơi giữ mang tên “Trạng thái” ở bảng này |
| Ghi chú hỏng hóc / tình trạng | `tp_condition_note` và field liên quan có căn cứ; trống ghi “Chưa có ghi chú” |
| Thao tác | Nút Xem gọn hoặc mở chi tiết từ tên thiết bị |

Người dùng chỉ cần những thông tin trên; serial/giá/bảo hành/nguồn/quyền sở hữu/
QR/khả dụng đưa vào chi tiết hoặc chọn cột, không bật cả loạt mặc định.
Ghi chú trống không có nghĩa “Không hỏng”; trạng thái nguồn tốt cũng không
đồng nghĩa đã kiểm tra thực tế. Có dấu hiệu nhỏ/tooltip về xác minh khi cần.

Header nền xanh nhạt, chữ14–15px, hàng56–64px khi nội dung ngắn, avatar32px,
padding12–16px, phân cách rõ, zebra/hover nhẹ. Badge xanh tốt, cam hạn chế/chờ
kiểm tra, đỏ hỏng, xám chưa rõ; màu không thay nhãn state backend.

Tên/ghi chú tối đa2dòng với mở rộng/tooltip dùng được cả touch, không ép hàng
cao200px hoặc giấu mất nội dung. Badge giới hạn trong ô, không overflow visible
đè cột kế bên. Ưu tiên độ rộng ghi chú/người/phòng. Tablet/mobile đổi độ ưu
tiên cột/card phù hợp hoặc cuộn trong vùng bảng, không tràn toàn trang.

Giữ filter compact: **Phòng ban, Loại thiết bị**, nút Bộ lọc mở Người sử dụng/
Tình trạng và tiêu chí phù hợp. Bỏ “Nơi giữ: Tất cả” khỏi hàng nhanh vì phạm vi
này đã cố định nhân viên giữ. Một ô search tên/mã nhân viên/mã TB/model; backend
search đúng field và quyền, không tìm trên trang hiện tại. Giữ paging10/20/50/100,
sort/count/XLSX theo đúng domain. Xóa lọc không làm stock quay lại màn này.

Detail thiết bị ưu tiên **Người đang dùng + Phòng ban + Loại + Tình trạng +
Ghi chú** ngay trên đầu; thông số sâu/history nằm dưới. Trường người giữ trên
thiết bị đã đăng ký vẫn đi qua action/wizard giao–thu hồi, không write trực tiếp.

## 5. Nút Quay lại thống nhất trên toàn hệ thống

Đây là yêu cầu toàn hệ thống đã cài, gồm mọi màn **chi tiết bản ghi** và
client-detail của HR/KH-KD/Kho/CRM/Projects/Contracts và cấu hình có quyền.
Không chỉ thêm nút riêng vào form thiết bị. Không cài app mới để làm đủ tên.

### Hình thức và vị trí

- Một nút **← Quay lại** tại đầu vùng nội dung/control panel, trước tên bản
  ghi hoặc cùng hàng tiêu đề. Cùng icon/nhãn/màu/chiều cao40px, vùng chạm44px
  trên mobile, hover/focus rõ. Có thể ghi tooltip “Quay lại danh sách nhân viên”
  theo ngữ cảnh. Nút không chèn thêm navbar và không mất khi toolbar xuống dòng.
- Mỗi chi tiết đúng **một** nút. Reuse/thống nhất nút HR đã có; không render
  chồng nút cũ/mới khi primary template kế thừa form chung.
- Trong popup/wizard, hành vi là đóng về màn cha, tôn trọng nút Đóng/Hủy sẵn
  có; không thêm nút đưa cả trang về danh sách trong lúc wizard chưa đóng.
- Không xuất hiện nút giả ở Home/dashboard/list/login/logout vì các màn đó
  không phải chi tiết. Nút Back trình duyệt và breadcrumb cũ vẫn hoạt động.

### Hành vi

1. Đi từ list → detail: quay về đúng list với filter/sort/group/page/page size,
   cột và vị trí cuộn còn nguyên trong khả năng native. Không doAction mở lại
   list mặc định và làm mất state nếu action stack còn khôi phục được.
2. Dashboard → detail: về dashboard giữ filter. Chi tiết A → related B: B về A,
   rồi A về nơi mở ban đầu. Các nút Xem, click dòng/tên, smart button phải cùng
   nguyên tắc, không mỗi cách mở tạo đường về khác nhau.
3. Deep link/reload/new tab không còn stack: fallback action có quyền tương
   ứng model/ngữ cảnh; thiết bị nguồn Tồn kho về Tồn kho, nguồn Người sử dụng
   về Người sử dụng. Không mặc định mọi detail quay về employee hoặc kho.
   Nếu không có fallback hợp lệ, về workspace/Home có quyền, tránh nút chết.
   Các nút Xem giữ action/leaf nguồn mở trong context phù hợp; không suy nguồn
   chỉ từ custody rồi đổi active sidebar sang Tồn kho khi stack còn nguồn khác.
4. Không `window.history.back()` mù vì có thể thoát website/quay lại login.
   Tái dùng action service/breadcrumb stack Odoo20 (`restore` hoặc API thực
   tế) và lifecycle hooks; không tự viết router/history engine thứ hai.
5. Khi form chưa lưu: đi qua guard native/custom hiện có. Hủy quay lại thì
   ở nguyên form và giữ dữ liệu vừa nhập; bỏ thay đổi phải qua xác nhận; nếu
   người dùng chọn lưu thì chỉ rời sau lưu thành công. Validation/RPC lỗi vẫn
   ở lại, không báo lưu xong giả. Không bypass bằng forceLeave/clear stack.
6. Back không tạo record, không tự ghi dữ liệu hoặc tự cấp quyền. Bấm nhanh
   nhiều lần không gây hai transition/restore vào action lỗi; loading hợp lý.
7. Không cache record/PII để khôi phục sau logout/đổi người dùng; không lưu
   secret hoặc URL bên ngoài tùy ý làm return target. Quyền action/record
   vẫn kiểm server, không sudo để quay về một màn user không còn được thấy.

Đặt helper/component dùng chung trong addon chung đã có, ưu tiên `tp_web_home`
nếu dependency phù hợp; form native tích hợp qua extension/template được hỗ
trợ. Các custom client-detail gọi cùng helper. Không sao chép từng hàm back ở
mỗi form, không patch DOM bằng MutationObserver để chèn nút. Không sửa core.

Trước sửa lập inventory mọi form/custom-detail đang hoạt động và cơ chế back
sẵn có. Ghi màn được phủ, màn không phù hợp (wizard/list) và lý do; màn chưa
phủ phải ghi còn thiếu, không tuyên bố “toàn hệ thống xong” từ một form kho.
Lưu quy ước trong tài liệu UI để các màn/phòng ban mới dùng cùng component.

## 6. Nâng dashboard theo phần đã trao đổi

Giữ bốn KPI và biểu đồ trên đầu. Tăng font nội dung14–16px, số KPI30–36px,
donut khoảng240–280px desktop và legend có số/tỷ lệ. Chart theo loại dùng thanh
dày/nhãn rõ, bỏ scroll nhỏ trong chart: hiển thị đủ nếu vừa hoặc top nhóm +
“Khác” với drill-down hợp lệ, tổng/denominator không đổi. Màu theo key cố định.

Theo phòng ban không gộp “Chưa khai báo / trong kho…” thành một phòng giả.
Phân biệt đúng dữ liệu HR hiện tại, dùng chung, tồn và chưa rõ; nếu chưa đủ
mapping thì ghi chưa rõ, không tự điền department bằng đoán vị trí.

Đề xuất gần đây thành khu riêng; phần thiếu ngày/chưa kiểm tra/import chờ vào
**Chất lượng dữ liệu** thu gọn, vẫn có nhãn gọn nhắc trạng thái nguồn. Giữ
unknown khác0, không thêm số tăng trưởng giả hoặc đồng nhất tồn với sẵn sàng.
Hover150–200ms, animation chart/cập nhật một lần250–450ms, reduced-motion;
không animation liên tục hoặc đổi số liệu cho đẹp. Không thêm nghiệp vụ mới.

## 7. Thực hiện, quan sát và bàn giao

Sửa lần lượt: domain/view/filter/export theo nhân viên → helper Quay lại
chung và các detail → dashboard. Backup mới rồi upgrade đúng addon thay đổi,
restart/apply assets trên18069. Không chạy setup/seed hoặc import nguồn lại.

Đối chiếu kết quả thật bằng browser (không tạo fixture hay lưu sửa người thật):

- Màn Người sử dụng không stock/người trống; tên/mã/avatar/phòng khớp HR; ghi
  chú đọc được. Màn Tồn kho giữ đủ số/ID trước đó; các máy dùng chung còn thấy.
- Tìm/lọc/clear/paging/XLSX không đưa stock vào tập nhân viên. Tập kết quả được
  backend giới hạn nhất quán, không chỉ DOM ẩn. Detail ghi đúng nguồn mở.
- Quay lại từ page2 đã lọc, dashboard drill-down, related record, deep link,
  popup, form chưa lưu và lỗi lưu; không dùng nút Lưu trên dữ liệu thật chỉ
  để chứng minh. Ca chưa thực hiện được phải ghi rõ, không ghi test PASS giả.
- Phủ HR/KH-KD/Kho và các app/cấu hình đang có detail; dùng tài khoản đúng
  quyền hiện có, không reset/cấp quyền thật để chụp ảnh. Không console/asset500.
- Ảnh trước/sau cùng role/viewport/dataset1440×900,1366×768, tablet và mobile
 390×844/375×812; nội dung không chồng/tràn, focus/touch/reduced-motion dùng được.

Ảnh/DOM/báo cáo mapping/snapshot dữ liệu giữ `.local/equip-ui002/` ignored.
Ghi rõ phạm vi quan sát; đây không tự là audit độc lập/nghiệm thu nghiệp vụ.

Cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP, guide/acceptance EQUIP, inventory
bảng và quy chuẩn back UI toàn hệ thống. Lint/parse/XML/JS/manifest theo phần
đổi, git diff --check, workflow finish/check bằng ID mới; không commit/push.

Bàn giao URL/menu18069, ảnh list/detail/dashboard, danh sách màn được phủ back,
version đã áp, kiểm thực chạy và giới hạn. Xác nhận equipment/phiếu/HR/user/
quyền/source binding không đổi do UI; không tự xử lý10dòng chờ bằng đoán tên.
Hoàn thành khi code đã áp và thấy kết quả thật, không dừng ở mockup/kế hoạch.
