# ATTENDANCE-WORKSPACE-003 — Giữ dashboard sáu thẻ, dùng chung mọi vai trò

> **Phạm vi đã được người dùng đính chính ở CHG-20261120-002:** chỉ làm lại khu
> Quản trị chấm công, bỏ giao diện nhập/lịch sử Excel và ưu tiên xuất đúng mẫu.
> Dashboard chỉ bổ sung bỏ chú giải donut/nhãn đồng bộ/giờ cập nhật, nới10 người
> gần nhất; giữ sáu KPI và Công của tôi. Không chạy lại phần credential/security/
> migration/Công của tôi bên dưới. Xem [bàn giao phạm vi cuối](../demo/ATTENDANCE_ADMIN_UI_001_ACCEPTANCE.md).

Ngày chốt yêu cầu: **20/11/2026 Asia/Saigon**. Phiên điều phối: `CHG-20261120-001`.
Trạng thái: **PROMPT_READY_NOT_IMPLEMENTED**. Đây là prompt hợp nhất để giao Claude triển khai;
không phải bằng chứng đã sửa ứng dụng, đã kiểm UI hoặc đã nghiệm thu nghiệp vụ.

## 1. Lệnh thực thi và thứ tự ưu tiên

Làm việc trong `C:\TANPHAT ONE`. Triển khai **ATTENDANCE-WORKSPACE-003** bằng
Odoo native OWL/QWeb/SCSS, ORM/session và database chung đang có.
Đọc `AGENTS.md`, `docs/PROJECT_STATUS.md`, workflow, skill TANPHAT và source/runtime
trước khi sửa. Chọn CHG-ID mới cho batch triển khai; giữ đúng vai trò thực thi Claude.

**Quyết định mới nhất của người dùng thay toàn bộ phần xung đột trong prompt cũ:**
giữ dashboard tài khoản thường đã được duyệt, gồm **sáu thẻ chỉ số**, màu hiện tại,
biểu đồ vòng và chú giải, 10 nhân viên gần nhất, các biểu đồ phía dưới và các bộ lọc
hiện có. Chỉ tinh chỉnh bố cục, kích thước, khoảng cách và trình bày.
Không áp yêu cầu bốn thẻ hoặc tỷ lệ cột cố định 35%/65% của ảnh cũ.
Không xây dashboard độc lập theo vai trò.

Ảnh người dùng đã đồng ý, là căn cứ hình thức ưu tiên:

```text
C:\Users\vuduc\AppData\Local\Temp\codex-clipboard-38c53f30-9104-4127-88c9-878af3fad5c6.png
```

Bản sao dự phòng trên máy điều phối: `.local/attendance-workspace003/reference-approved.png`.
Ảnh có dữ liệu thật: chỉ dùng làm tham chiếu/evidence riêng, không đưa vào Git.
Hai ảnh cũ `1ccff8ea-47e9-4ee4-9785-f244313169f9` và
`5ba7e2af-feca-4160-8b9a-384a2f9582a7` không còn là yêu cầu xây lại dashboard.
Không hardcode người, số lượng hoặc ngày giờ trong ảnh.

Giữ navbar, sidebar, font tiếng Việt và nhận diện TANPHAT ONE/TP HR hiện tại.
Không thêm navbar thứ hai hoặc thay kích thước sidebar toàn hệ thống để nhồi nội dung.
Sau mỗi hạng mục hoàn tất, commit/push đúng scope và đồng bộ/deploy PC server
theo `docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md`; không xin lại quyền rollout,
không bắt buộc qua 18079 và không đổi sang cổng/DB khác để lách chỉ thị.

## 2. Baseline phải xác minh, không triển khai lại phần đã có

Tại mốc điều phối, HEAD là `ccea8e00`; addon chấm công **20.0.3.5.1**.
PROJECT_STATUS ghi đã áp PC server ở CHG-20261119-032; `scripts/dev.py status`
cho thấy local Odoo/PostgreSQL đang nghe, DB `tp_tanphat_dev`, cổng 18069.
Đó không thay kiểm lại runtime/version PC trước release.

- Đã có một `AttendanceDashboard`, một client action `cham-cong` và `tp_overview`
  cho mọi vai trò. Tái sử dụng trực tiếp, không tạo component/admin dashboard mới.
- Sáu KPI, donut, 10 người khác nhau gần nhất, biểu đồ xu hướng/phút muộn,
  Công của tôi và bộ xuất XLSX đều đã có. Giữ phần đạt; làm delta còn thiếu.
- ENTI là nguồn tự động đã áp, cron/bus đang hoạt động. Nhập Excel mới đã ngừng
  cả UI/RPC theo DEC-063; giữ trạng thái ngừng nhập và lịch sử, không bật lại fallback.
- Có foreign WIP ở Reporting, sidebar, Home, policy docs và các tệp chưa track.
  `ai_workflow.py check` đã FAIL **trước** lượt này vì source khác handoff.
  Đọc checkpoint hiện có, không xóa/ghi đè, không `finish` để nhận source chưa audit.
  Tách đúng phạm vi và phối hợp chủ batch nếu chưa thể chốt workflow sạch.
- CHG-20261120-001 chỉ thêm prompt và cập nhật status/changelog; không đổi code
  ứng dụng, DB, tài khoản, quyền, lịch đồng bộ hoặc phiên bản runtime.

Các điểm source để đọc, số dòng cần kiểm lại sau mọi thay đổi:

| Phạm vi | Tệp hiện có và quan sát từ audit source |
| --- | --- |
| Dashboard chung | `static/src/dashboard.js`, `dashboard.xml`, `dashboard.scss` trong `custom_addons/tp_hr_attendance`; đăng ký action ở JS, menu/action trong `views/menus.xml`, `views/correction_views.xml` |
| Chữ/giờ bị cắt | `dashboard.scss:114–118` áp nowrap/ellipsis cho tên và dòng phụ; QWeb đã có tên, phòng, ngày, giờ vào/ra |
| Đọc số liệu | `models/attendance_overview.py:537` (`tp_overview`), `:513` (`_tp_recent`); thời gian thực tế, tối đa 10 người khác nhau |
| Công cá nhân/XLSX | `static/src/mine.js`, `mine.xml`; `attendance_overview.py:799` (`tp_mine`), `:929` (`tp_export_mine`); owner từ phiên, không từ ID trình duyệt |
| Cập nhật trực tiếp | `static/src/live.js`, `charts.js`; bus debounce, polling khi tab hiện, dọn timer/listener |
| Admin có grant thật | `models/attendance_common.py`: `is_correction_admin`, `_is_correction_admin_user`, helper `res.users` của `tp_admin_delegation`; dùng lại logic original/live grant/company, không sao chép một chính sách admin khác |
| Cấu hình và đường vòng | `enti_wizard.py`, `enti_sync.py`, `enti_mapping.py`, `enti_day.py`, `attendance_source.py`, `attendance_menu.py`, `security/ir.access.csv`, `security/security.xml`, `views/enti_views.xml`, `views/menus.xml` |

## 3. Dashboard được giữ và căn chỉnh

Giữ sáu thẻ theo đúng thứ tự và màu hiện tại:

1. Tổng nhân viên.
2. Có giờ vào.
3. Có giờ ra.
4. Thiếu giờ / cần kiểm tra.
5. Đi muộn.
6. Vắng theo lịch.

Giữ công thức, đơn vị, giải thích và dữ liệu thật; số 0 khác chưa đủ căn cứ.
Các thẻ cùng chiều cao theo hàng, vị trí icon/tiêu đề/số/chú thích thẳng hàng.
Chừa vùng tiêu đề đủ cho nhãn dài xuống dòng; không đẩy số liệu lệch hàng.
Thống nhất padding, gap, bo góc, đường viền theo token hiện có, CSS scoped addon.

Giữ toàn bộ bộ lọc **Ngày / Tuần / Tháng / Khoảng ngày**, chọn ngày/chuyển kỳ,
Hôm nay, Phòng ban, Nhân viên theo tên/mã, Tình trạng và Đặt lại.
Ô nhập rõ, nút cùng chiều cao, toolbar tự xuống hàng khi thiếu chỗ.
Tái sử dụng filter/profile/SearchModel hiện có, không tạo filter engine mới.
Không đổi ngầm ý nghĩa lọc: source hiện dùng tình trạng để lọc bảng cần kiểm tra,
còn KPI/donut/recent dùng kỳ/phòng/tìm kiếm. Làm rõ phạm vi hiển thị của từng vùng;
không tự đổi công thức hoặc hợp đồng xuất dữ liệu trong một lần căn giao diện.

Giữ tiêu đề Tổng quan chấm công, kỳ đang xem và lần cập nhật thành công thật.
Cân kích thước donut với chú giải, giảm vùng trống thừa; chú giải căn cột tên,
số lượng và tỷ lệ, có tooltip và thao tác lọc bằng chuột/bàn phím.
Các nhóm donut loại trừ nhau, tổng khớp cùng scope.

Desktop: donut/chú giải và danh sách gần nhất cạnh nhau khi đủ rộng, mép trên/dưới
cân đối, không cố định chiều cao làm cắt chữ hoặc phình khoảng trắng.
Giữ các biểu đồ phía dưới và bảng cần kiểm tra hiện có.
Tablet/mobile: KPI xuống hàng theo chiều rộng thực tế, hai khối chính xếp dọc
khi thiếu chỗ. Không giảm cỡ chữ để nhồi, chồng chữ, tràn ngang toàn trang hoặc
lộ vùng trắng khi cuộn. Bảng rộng được cuộn riêng hoặc dùng trình bày thích hợp.

Hover/animation nhẹ 180–300ms cho tương tác; có focus rõ, tương phản tốt và
`prefers-reduced-motion`. Polling không dựng lại toàn bộ màn, nhấp nháy,
chạy lại animation hoặc làm nhảy chiều cao/vị trí nội dung đang đọc.

## 4. Danh sách gần nhất đọc đủ thông tin

Tên chính xác: **10 nhân viên có giờ vào/ra gần nhất** vì nguồn hiện có giờ vào đầu
và giờ ra cuối theo ngày, chưa chứng minh có nhật ký mọi lượt quẹt.

- Tối đa 10 nhân viên khác nhau, một người một mục; ít hơn thì hiện đúng số thật.
- Sắp theo mốc chấm công thực tế giảm dần, không theo received_at/write_date.
- Avatar/họ tên/mã/phòng lấy hồ sơ HR chung; không dựng danh sách riêng.
- Hiện đủ tên, mã, phòng, ngày; **Vào** và **Ra** thành hai dòng/nhóm rõ, giữ mốc
  gần nhất và loại Vào/Ra. Không dùng dấu “…” che tên, phòng hoặc giờ; tooltip
  không phải cách thay thế nội dung bị cắt trên mobile.
- Có giây thì HH:mm:ss, chỉ có phút thì HH:mm; thiếu ghi “Chưa ghi nhận”.
- Vùng cuộn danh sách riêng, header không che hàng; touch/wheel chuyển cuộn tự
  nhiên khi đến đầu/cuối, không tạo nhiều lớp cuộn trong cùng danh sách.
- Dashboard không mở đường sang hồ sơ HR riêng tư hoặc xuất công người khác.

Không gọi có giờ vào là bằng chứng đang ở văn phòng, có giờ ra là đã kết thúc ngày,
không dữ liệu là nghỉ/vắng. Giữ/giải thích chính xác nhãn trạng thái hiện tại;
ngày lịch sử không gọi “đang làm”. Không dựng số thiết bị hoặc Online/Offline từ
kết quả API; chỉ nói đồng bộ hoạt động theo trạng thái kết nối thật.

## 5. Cùng dashboard, menu theo quyền

Admin gốc, admin ủy quyền có grant còn hiệu lực đúng công ty, nhân viên thường
đều dùng **cùng component, QWeb, SCSS, layout, sáu KPI, màu, biểu đồ, bộ lọc và cách
trình bày dữ liệu**. Cùng kỳ/bộ lọc/phạm vi dữ liệu được phép thì kết quả phải khớp.
Không tăng ACL dữ liệu, dùng sudo tràn scope hoặc cấp nhóm HR để làm màn giống nhau.
Người nội bộ đang hoạt động mở Tổng quan công ty mình theo quyền đọc cơ bản hiện có.

Nhóm **Chấm công** cho mọi người: Tổng quan chấm công, Công của tôi.
Nút **Xuất Excel công của tôi** nằm trong Công của tôi, không thành tab riêng.

Admin có thêm **Quản trị chấm công**:

- Cấu hình kết nối.
- Đối chiếu nhân viên.
- Nhật ký đồng bộ.
- Xử lý điều chỉnh.
- Chốt kỳ khi có capability nghiệp vụ tương ứng.
- Xuất báo cáo tổng hợp khi có capability nghiệp vụ tương ứng.

Lịch sử nguồn/Excel cũ cần truy vết đặt gọn trong quản trị, không chiếm luồng thường.
Không đưa credential form, bảng mapping, raw payload, log kỹ thuật vào dashboard chung.
Nhân viên không thấy các mục này, nhập Excel, điều chỉnh người khác hoặc xuất toàn công ty.
Chốt kỳ, đính chính kỳ khóa và xuất tổng hợp tiếp tục theo capability nghiệp vụ hiện có;
việc có nhóm quản trị không tự cấp `can_lock`, mở kỳ hoặc mở rộng export.
Giữ backend nghiệp vụ hợp lệ của phân công cũ; chỉ hạn chế quyền connector theo mục 6.

## 6. Cấu hình connector chỉ admin thật, không lộ secret

Chỉ original admin hoặc delegated admin có grant còn hiệu lực ở đúng công ty được
mở/sửa kết nối, kiểm tra kết nối, chạy đồng bộ thủ công, xem/xác nhận mapping,
xem nhật ký đồng bộ. Không suy từ chức danh, phòng, login, UID, `base.group_system`
đơn lẻ, cờ frontend, context giả hoặc `sudo`.

Tái sử dụng nhận diện original/live grant của `tp_admin_delegation` và khóa thu hồi
đã dùng cho điều chỉnh. Kiểm cả model/wizard CRUD, search/read/export/read_group,
phương thức công khai, direct URL/RPC, source detail, record công ty đích,
đổi liên kết/công ty trong write/batch và request đồng thời revoke.
ACL/menu theo group chỉ là lớp ứng viên; gate động backend vẫn quyết định.
Thu hồi/hết hạn/khóa tài khoản mất quyền ở request kế tiếp, tab cũ không giữ quyền.
Cron nội bộ tiếp tục đồng bộ qua đường nội bộ được bảo vệ; không vì chặn RPC
mapping/sync mà làm chết cron, và không để public helper sudo-write thành đường vòng.

Form gồm tài khoản, mật khẩu mới che ký tự, trạng thái đã cấu hình,
Kiểm tra kết nối, Lưu, Đồng bộ ngay, lần thành công gần nhất và lỗi dễ hiểu.
Mật khẩu trống khi sửa **giữ mật khẩu cũ ở server**; lần đầu chưa có phải báo thiếu.
Không preload/đọc trả secret, không log token/cookie/password hoặc nguyên ngoại lệ
có thể chứa chúng; xóa giá trị mật khẩu tạm khi không còn cần, giữ dữ liệu nhập khi lỗi an toàn.
Lỗi native dùng presenter chung; OWL dùng InlineErrors/saveError, không toast danger cho lỗi lưu.

Các gap source đã thấy, phải tái hiện và sửa nhỏ nhất phù hợp:

- Wizard/manual sync còn chấp nhận HR manager hoặc env.su; mapping/log/raw-day ACL
  còn mở cho HR/officer. Menu ENTI chưa qua gate động, nhánh manager có bypass.
  Rà cả stale ACL sau upgrade, không chỉ sửa XML rồi để ACL cũ trong database.
- `tp_suggest_mapping` là public và có sudo-write/project; đọc tất cả callers trước
  khi đóng đường RPC, giữ caller cron nội bộ đúng.
- Credential resolver hiện có global file/env/parameter fallback; không được dùng
  credential của công ty A khi giả `company_id` B. Ràng buộc với source/công ty
  đã xác minh, từ chối scope khác; không nhân bản credential hoặc tự chọn công ty
  theo tên. Không xây hệ cấu hình đa công ty mới nếu chưa cần.
- Kiểm giao dịch lưu credential/source: hiện có đường ghi file trước thao tác DB
  có thể bị guard admin từ chối. Lỗi quyền/DB phải không để thay đổi secret dở dang.
  Rà secret nằm ở storage có thể bị generic RPC đọc; tận dụng storage được bảo vệ
  hiện có hoặc sửa phạm vi nhỏ, không bypass guard cấp quyền bằng sudo/context.

Giữ DEC-054/062: chỉ original cấp/thu admin; delegated không sửa account/hồ sơ
delegated khác. Cấu hình connector không phải thay đổi tài khoản đăng nhập hệ thống.

## 7. Bỏ tên nhà cung cấp ở nhãn sản phẩm, giữ kết nối

Đổi chữ ENTI trên menu, title, nút, tooltip/ARIA, nhãn nguồn, thông báo và báo cáo
thành tên trung tính: Chấm công, Kết nối chấm công, Đối chiếu nhân viên,
Nhật ký đồng bộ, Dữ liệu máy chấm công, Cập nhật gần nhất.
“Nhân viên Odoo” đổi thành “Nhân viên trong hệ thống”.
Giữ model/XML ID, endpoint, namespace, mapping và connector đang chạy.
Không global replace định danh kỹ thuật hoặc sửa core; thông tin chẩn đoán
có thể giữ trong log quản trị đúng quyền, không đưa vào dashboard nhân viên.
Rà cả SourceStrip dùng chung, Công của tôi và XLSX, không chỉ menu/dashboard.

## 8. Công của tôi và Excel

Tái sử dụng màn hiện có (kể cả nhúng ở hồ sơ cá nhân), không xây lại phần đạt.
Owner từ quan hệ user–employee đã xác minh trong công ty phiên hiện tại.
Không tin employee_id/user_id trình duyệt, không chọn người khác hoặc hồ sơ đầu tiên,
không ghép tên. Chưa có hồ sơ thì hướng dẫn rõ, không lộ dữ liệu người khác.

Giữ avatar, tên, mã, phòng và chọn Tuần/Tháng hiện có; bổ sung Khoảng ngày theo
yêu cầu gốc bằng helper kỳ hiện có. Giữ tóm tắt ngày có dữ liệu,
số lần muộn khi có căn cứ, tổng phút muộn, buổi vắng xác định không tính Chủ nhật,
ngày thiếu giờ. Bảng có ngày/thứ/vào/ra/muộn/tình trạng/ghi chú đúng quyền.
Giữ gửi đề nghị điều chỉnh của mình, không cho ghi giờ chuẩn trực tiếp;
admin duyệt theo DEC-061, giữ chống tự duyệt và kỳ khóa.
Giữ lọc tình trạng, phân trang 10/20/50 khi cần; xuất toàn bộ kết quả lọc, không chỉ trang.

Tái sử dụng dataset và bộ xuất chung, không tạo công thức Excel khác.
Mẫu tham khảo riêng: `C:\Users\vuduc\Downloads\bang cham cong vao ra.xlsx`.
Workbook cá nhân có công ty/tiêu đề/tên/mã/phòng/kỳ/thời điểm xuất, ngày/thứ/vào/ra,
lần/phút muộn, vắng đã xác định và thiếu giờ/ghi chú; không có dữ liệu người khác,
cấu hình hoặc credential. Giữ ma trận/chi tiết đang có nếu đáp ứng, chỉ chỉnh phần thiếu.
Nếu ma trận giữ cả kỳ còn sheet Chi tiết theo lọc, nhãn/scope phải nói rõ,
không đánh số tổng cả kỳ thành tổng của riêng tập lọc.

Header xanh đậm chữ trắng, viền/nền xen kẽ; Chủ nhật xám, muộn cam, thiếu giờ vàng,
vắng xác định đỏ nhạt. Freeze tiêu đề, độ rộng/wrap/in hợp lý; giờ/ngày/số dùng
kiểu Excel đúng, không cắt chữ/####; giữ chống công thức từ dữ liệu văn bản.
Phân biệt ngày muộn và lần muộn; nguồn chỉ có phút theo ngày không tự suy số lần theo ca.
Không coi thiếu công là vắng, không tính Chủ nhật/ngày tương lai/buổi chưa kết thúc.
Chưa có lịch ca/mốc sáng–chiều đủ căn cứ thì ghi chưa xác định, không bịa số buổi
hoặc đổi công thức backend chỉ để lấp ô Excel.

## 9. Bảo toàn dữ liệu và tự cập nhật

Tất cả màn/XLSX đọc bảng công chuẩn chung. Giữ điều chỉnh đã duyệt > máy > Excel cũ,
mapping theo định danh nguồn–hr.employee, kỳ khóa, lịch sử, thiếu giờ nguyên trạng,
retry có giới hạn và đồng bộ lặp không trùng. Không seed hay xóa dữ liệu thật.
Xác minh Hoàng Xuân Tiến, mã TP10065/liên kết nguồn TP032 hiện có; không tạo lại,
không trả tên sai Tuyến và không hardcode tổng 39 người.

Tái sử dụng bus/polling hiện có; không F5, không trình duyệt gọi API nguồn.
Giữ bộ lọc, trang/page size, scroll trang/danh sách, focus và nội dung đang nhập;
debounce hợp lý, tab ẩn giảm/ngừng poll, quay lại cập nhật và dọn listener/timer khi rời.
Bus không chứa dữ liệu vượt quyền. Rà race `live.loaded()` xóa pending trong khi
RPC đang chạy và một notification khác vừa tới; tái hiện bằng deferred request,
không coi giữ lọc trên happy path là đã kiểm mọi cập nhật.

## 10. Nghiệm thu bắt buộc, ghi kết quả thực chạy

| Nhóm kiểm | Đầu vào/thao tác | Kết quả và evidence cần có |
| --- | --- | --- |
| Giữ thiết kế | Ảnh đã duyệt và ảnh trước/sau cùng actor, viewport, kỳ, bộ lọc, dữ liệu | Sáu thẻ/màu/donut/chú giải/recent/biểu đồ dưới/bộ lọc còn đủ; chỉ căn trình bày |
| Chung ba vai trò | Original, live delegate đúng công ty, nhân viên; cùng phạm vi được phép | Một action/component/template/CSS; cùng bố cục/số liệu; chỉ quản trị khác theo quyền |
| Responsive | 1440, 768, 390, 320px trong shell TP HR | Tên/phòng/vào-ra đầy đủ, không ellipsis/overlap/tràn trang, cuộn dễ dùng; keyboard/reduced motion |
| Live | Đang lọc/trang khác/đã cuộn/đang nhập; nhiều thông báo khi RPC chậm; tab ẩn/hiện/rời màn | Dữ liệu cập nhật, không mất lọc/trang/scroll/focus/input, không nhấp nháy hoặc bỏ sót pending |
| Connector chỉ admin | Nhân viên, HR-only, officer-only, system-only không grant; original/live delegate; sai công ty; expired/revoked/locked | Chặn UI/direct URL/ORM/RPC/export/mapping/manual sync/credential/status/log chi tiết sai quyền; cron vẫn chạy |
| Revoke và sửa scope | Revoke khi thao tác, giả company/context, write/batch đổi company/liên kết, tab cũ | Kiểm quyền hiện tại và công ty thực trước ghi, từ chối toàn bộ batch sai; không side effect secret/source |
| Công cá nhân | Sửa employee_id/user_id/company params; tài khoản chưa liên kết | Owner luôn từ phiên; không lộ công người khác; không fallback hồ sơ đầu |
| Excel | Xuất thực tế kỳ có muộn/thiếu giờ/Chủ nhật và lọc nhiều trang | Mở/render file, đối chiếu dataset/tổng/kiểu ô/phạm vi, không dữ liệu khác hoặc secret; không cắt chữ/#### |
| Trạng thái | Loading, rỗng, mất mạng, thiếu mapping, thiếu vào/ra | Thông báo rõ, không dữ liệu giả, không đánh offline máy từ kết quả API |
| Bảo toàn | Snapshot trước/sau và cron thật | HR/user/grant/mapping/historical/correction/period/config/cron giữ đúng; khác biệt dự kiến ghi rõ |

Không đăng nhập tài khoản thật theo cách làm văng phiên người dùng. Dùng phương án
kiểm cô lập đã được phép hoặc phiên sẵn có phù hợp; chưa đủ actor/evidence thì ghi NOT RUN.
Không tạo actor giả/gán quyền hoặc chạy suite tạo fixture trên main/server.
Kiểm device emulation không gọi là kiểm thiết bị thật. Không dùng ảnh mock thay evidence runtime.

Đọc và mở rộng test phù hợp, không chạy cả ứng dụng vì sửa tài liệu:

- `tests/test_access.py`, `test_correction.py`, `test_enti_attendance_002.py`,
  `test_enti_sync.py`, `test_directory_privacy.py`, `test_matrix_compare.py` theo delta.
  Với xuất chung theo phân công phòng ban, kiểm cả tập có nhân viên chưa thuộc phòng;
  không để việc bỏ department rỗng khỏi tập kiểm làm lọt dữ liệu ngoài quyền.
- `scripts/tests/test_hr_attendance_dashboard.cjs` hiện dừng ở `AttPager is not defined`
  và còn assertion handler cũ: sửa harness theo source thật, không bỏ assertion để báo xanh.
- Tận dụng browser script hiện có `test_hr_attendance_latest_ui.cjs`,
  `test_hr_attendance_scroll.cjs` và công cụ Playwright; thêm coverage 768/320 và actor còn thiếu.
- XML/JS/SCSS/assets, Python/Ruff phù hợp, targeted backend test khi đổi security;
  kết quả ghi đúng DB/cổng/log/lệnh, pass/fail/skip. Không lấy workflow checker thay test.

## 11. Triển khai và bàn giao

Làm slice nhỏ nhưng hoàn chỉnh; chốt và giao từng hạng mục dùng được, không push code dở.
Không sửa `odoo/`, `addons/`, React legacy, policy cấp admin, tài khoản/hồ sơ peer admin,
sidebar toàn cục hoặc các diff Reporting/Home không thuộc phạm vi.
Không đổi grant người thật hoặc model/XML ID để né lỗi quyền.

Chạy `ai_workflow.py start` trước sửa hoặc resume checkpoint đang có. Cập nhật
PROJECT_STATUS, CHANGELOG, chính sách quyền chấm công và inventory bộ lọc đúng delta;
form validation coverage nếu đổi form. Kiểm `git diff --check`, review callers và source
có kết nối, không chỉ diff. Chốt workflow khi đúng scope đã được audit; không nhận foreign WIP.

Backup đúng DB/filestore/source/config PC trước migration/quyền; snapshot không lộ secret.
Commit/push đúng file/hunk, deploy đúng commit đã push; giữ mtime/cache assets theo runbook.
Không copy cả working tree, dump/secret/filestore/ảnh dữ liệu thật vào Git.
Kiểm health, log, menu/action/link public và JS/CSS mới thực sự được phục vụ;
lỗi do release phải sửa hoặc rollback. Không hardcode URL tunnel tạm.

Bàn giao: ảnh Dashboard/Công của tôi desktop/mobile, menu ba vai trò,
kết quả kiểm quyền backend, Excel thực tế đã kiểm, trạng thái đồng bộ thật,
snapshot/backup, commit SHA/push, version/source đã deploy và public smoke.
Ghi riêng phần chưa kiểm, technical acceptance, phản hồi hình thức người dùng,
business acceptance và pilot authorization. Không kết luận xong chỉ từ việc đổi màu/menu.
