# HR-ATTENDANCE-SIMPLE-002 — Tổng quan chấm công gọn, chuẩn bị API máy

Làm việc trong `C:\TANPHAT ONE`. Triển khai yêu cầu18/11/2026, DEC-055.
**Đơn giản hóa chấm công hiện có, giữ dữ liệu Excel đã nhập, chuẩn bị nền
tích hợp máy chấm công sau này.** Chưa có tài liệu API/loại máy/credential;
không giả lập đang kết nối thật và không mở live connector theo suy đoán.

## 1. Mục tiêu và phạm vi

Người dùng chỉ cần một nơi dễ nhìn để biết:

- Công ty/phạm vi được xem có bao nhiêu nhân viên.
- Hôm nay có bao nhiêu người nghỉ, bao nhiêu người đã về.
- Xem danh sách và thống kê theo **ngày, tuần, tháng**.
- Hiện tại sử dụng Excel đã import; sau này máy chấm công cập nhật cùng dữ
  liệu và dashboard trên web, không phải xây lại hoặc nhập nhân viên lần nữa.

Không mở thêm payroll, GPS, face recognition, KPI nhân sự hoặc quy trình
nghỉ phép nhiều bước. Không thiết kế thành một hệ thống quản trị công phức tạp.

Đọc AGENTS/status/changelog/AI_CHANGE_WORKFLOW/roadmap/decisions, skill giao
bản Odoo, frontend-design/Ponytail nếu có và chuẩn bảng/bộ lọc dùng chung.
Viết acceptance trước sửa code. Phiên triển khai được code trong scope này;
phiên điều phối đã viết prompt chưa thay source/data.

## 2. Tái sử dụng nguồn đang có

Rà `custom_addons/tp_hr_attendance/`: attendance_day/session/import/parser/
metrics/config, dashboard/board/mine, menu/security và test. Đọc policy/guide/
acceptance HR-ATTENDANCE-001 và HR-DELEGATE-FIX-001. Baseline đã giao attendance
20.0.1.2.0; kiểm lại source/runtime trước dùng, không coi bàn giao là test mới.

- Một PostgreSQL database mỗi môi trường, chung employee/department/user
  với HR và các phân hệ khác. Không tạo nhân viên/bảng công riêng ở frontend.
- Nhân viên lấy bằng ID và mã nguồn máy đã đối chiếu; TP100xx là mã hiển thị.
  Không match bằng tên, tự tạo người, đổi phòng hoặc đổi mã khi nhận công.
- Giữ dữ liệu Excel/lô nhập/lineage/snapshot lịch sử hiện có. Không clear,
  nhập lại toàn bộ hoặc xóa session/day/phiếu điều chỉnh/chốt kỳ để làm UI.
- Hiện session yêu cầu cả `check_in` và `check_out`. **Không dùng riêng các
  phiên đã đóng để tính ai đang làm/đã về.** Điểm tích hợp phải lưu/chuẩn hóa
  được lượt IN chưa có OUT; không tự đặt OUT bằng giờ hiện tại.

## 3. Định nghĩa số liệu trước khi vẽ biểu đồ

Tất cả dùng cùng employee scope, company, ngày và mốc dữ liệu; timezone
Asia/Ho_Chi_Minh. Chọn ngày mặc định là **ngày hôm nay thực**, không tự đổi
ngày lịch sử gần nhất thành hôm nay. Có nút Xem ngày có dữ liệu gần nhất riêng.

### Tổng nhân viên

Đếm nhân viên trong phạm vi được xem và còn làm tại ngày tham chiếu theo
nguồn HR hiện có. Không đếm user/login hoặc chỉ những người xuất hiện trong
Excel. Không coi người nghỉ việc/ngoài đối tượng chấm công là nghỉ hôm nay.
Nếu chưa có roster/lịch đủ căn cứ, hiển thị giới hạn, không mặc định toàn bộ
nhân viên đều có ca làm việc hôm nay.

### Nghỉ hôm nay

- Đếm nghỉ đã có căn cứ: nguồn nghỉ/xác nhận HR hoặc mã nghỉ Excel đã được
  ánh xạ xác nhận; nêu rõ nguồn, ngày và trạng thái. Tái sử dụng dữ liệu sẵn có.
- **Không đồng nhất chưa chấm công = nghỉ.** Tách Chưa ghi nhận chấm công và
  Chưa có dữ liệu; ô Excel trống, ký hiệu chưa hiểu hoặc mất kết nối không là nghỉ.
- Ngày nghỉ theo lịch/ngoài ca khác nghỉ cá nhân. Chưa có lịch thì chưa kết
  luận nghỉ không phép/đi muộn/về sớm. Chưa có nguồn nghỉ thì KPI hiện Chưa đủ
  dữ liệu, không dùng0 như đã xác nhận không ai nghỉ.
- Nếu thực sự chưa có nguồn nghỉ nào, có thể thêm xác nhận nghỉ theo ngày
  tối thiểu cho HR/admin có lý do/nguồn/audit; không xây module xin phép mới,
  không tự tạo xác nhận nghỉ người thật và không sửa raw punch để giả nghỉ.

### Đã về và đang làm

- Tính từ chuỗi sự kiện theo thời gian, theo ca/ngày và **lượt hợp lệ mới
  nhất tại mốc thống kê**. OUT rồi IN lại phải trở về trạng thái đang làm.
  Không đếm chỉ vì từng có OUT buổi trưa hoặc chỉ nhìn last_out của phiên cũ.
- Chỉ dùng nhãn Đã về khi nguồn/quy tắc đủ xác định đã kết thúc ca/ngày làm.
  Nếu máy/Excel chỉ chứng minh một lượt ra mà không rõ kết thúc ngày thì dùng
  Đã ghi nhận ra, có giải thích ngắn; không khẳng định đã về cả ngày.
- Excel lịch sử chỉ là trạng thái theo bản dữ liệu đã nhập, không là hiện
  diện live. IN/OUT không rõ chiều hoặc thiếu cặp phải hiện Cần kiểm tra,
  không tự đảo chiều từng lượt để tạo kết quả trông đầy đủ.
- Giữ timestamp gốc, nhận sự kiện đến trễ/sai thứ tự; ca qua đêm theo cấu
  hình/lịch có thật, không cắt cứng UTC hoặc tự đoán ngày làm việc.

### Không cộng các số khác đơn vị

- Chế độ Ngày: KPI người, mỗi người chỉ một trạng thái hiện diện chính tại
  cùng mốc. Tổng nhân viên là mẫu số, không là một lát của donut trạng thái.
  Tình trạng thiếu dữ liệu là cờ riêng nếu có thể chồng với hiện diện.
- Tuần/tháng: số người là **distinct employee** trong kỳ. Đổi nhãn rõ như
  Người có ngày nghỉ xác nhận/Người có ghi nhận ra trong kỳ; không ghi Đã về
  hôm nay cho tổng của tháng. Số ngày nghỉ/ngày-người/giờ là chỉ số phụ có
  đơn vị riêng; không cộng cùng người. Biểu đồ xu hướng theo từng ngày.
- Donut chỉ dùng các nhóm cùng phạm vi/đơn vị và không chồng; nếu nguồn
  không đủ để phân nhóm thì hiển thị trạng thái thiếu nguồn, không bịa lát0.

## 4. Giao diện gọn, đẹp và đồng bộ TP HR

Giao diện sáng; giữ navbar/sidebar/font/nút Quay lại chung, không tạo navbar
thứ hai hoặc frontend độc lập. OWL/QWeb/SCSS/native action trong addon hiện có.

**Bố cục desktop:**

1. Tiêu đề Chấm công, segmented Ngày/Tuần/Tháng, chọn kỳ, Hôm nay, trước/sau,
   lọc phòng ban và tìm tên/mã nhân viên. Tuần từ thứ Hai đến Chủ nhật.
2. Dải nguồn nhỏ: Excel/API/nguồn hỗn hợp, thời điểm cập nhật, dữ liệu đến
   ngày/mốc nào và trạng thái kết nối. Không giấu việc nguồn cũ/thiếu ngày.
3. Ba KPI lớn: Tổng nhân viên, Nghỉ đã xác nhận, Đã về/Đã ghi nhận ra theo
   nghĩa nguồn. Ngày hôm nay dùng nhãn hôm nay; ngày/kỳ khác ghi ngày/kỳ rõ.
   Có thể thêm chip nhỏ Đang làm, Chưa chấm công, Cần kiểm tra khi đủ căn cứ.
4. Biểu đồ đặt ngay phía trên bảng: donut lớn cho phân bố trạng thái ngày;
   biểu đồ cột xu hướng ngày cho tuần/tháng. Chú giải, tooltip số/đơn vị/ngày/
   nguồn; bấm KPI/lát/cột mở đúng tập dữ liệu cùng bộ lọc. Không vẽ đồ trang trí.
5. Bảng rõ đường phân cách: Mã NV, Họ tên, Phòng ban, Ngày, Giờ vào, Giờ ra,
   Trạng thái, Nguồn/Cập nhật. Thông tin không có hiển thị dấu —/Chưa có nguồn
   đúng nghĩa. Chi tiết chỉ cần chuỗi vào-ra/nguồn/lưu ý, không nhồi phiếu HR.

Màu nhất quán: xanh dương cho tổng/nhấn chính, xanh lá cho đang làm/đã ghi
nhận hợp lệ, cam cho thiếu dữ liệu, tím cho nghỉ xác nhận, xám cho chưa rõ.
Nhãn/icon đi kèm màu, không truyền nghĩa bằng màu đơn độc. Tooltip rõ, hover
nhẹ và chuyển trạng thái khoảng150–250ms; tôn trọng reduced-motion, không
nhấp nháy số hoặc chạy animation vòng lặp. Tái sử dụng thư viện chart đang có.

Table có filter đúng nội dung, clear giữ quyền/company, pager10/20/50/100,
header dễ đọc, không chồng cột. Mobile375–390px chuyển KPI/chart thành một
cột, bảng thẻ hoặc cuộn ngang trong vùng riêng; bộ lọc gọn, không tràn cả trang.

**Menu thường chỉ giữ:** Tổng quan chấm công, Bảng chấm công (Ngày/Tuần/Tháng),
Công của tôi. Nhập dữ liệu và Nguồn dữ liệu nằm trong khu quản trị HR/admin,
không nhồi sidebar nhân viên. Các luồng điều chỉnh/chốt/quy tắc đã có chuyển
khỏi điều hướng chính nếu cần, giữ action/deep link/quyền/dữ liệu; không xóa
backend, table hoặc nghiệp vụ đang có chỉ để giảm tab. Phần xin nghỉ không
tự phát triển thêm. Giữ tab công cá nhân dùng cùng nguồn.

## 5. Chuẩn bị tích hợp API máy chấm công

Mục tiêu là adapter/contract nhỏ tái sử dụng ingestion và model Odoo hiện có,
không Kafka/data lake/database riêng hoặc viết connector hãng chưa biết.

- Khai báo điểm vào backend chung có kiểm quyền cho nguồn đã chuẩn hóa.
  Tách parsing Excel, adapter máy tương lai, lưu nguồn và dựng trạng thái/KPI.
  Không để UI tự gọi máy hoặc giữ API key của thiết bị.
- Contract sự kiện tối thiểu: source/device ID, source event ID nếu có,
  employee machine code, timestamp+timezone, direction IN/OUT/UNKNOWN,
  received_at và thông tin nguồn cần truy vết. Mã ngoài là chuỗi, không mặc
  định API mọi hãng dùng số hoặc tự bỏ số0 đầu như parser Excel cũ.
- Đối chiếu mã theo đúng namespace nguồn/máy/company và mapping HR hiện có;
  chưa map hoặc trùng mã thì chờ xử lý, không gán nhầm tên. Chưa biết hãng
  có thể chia sẻ cùng mã giữa các máy thì ghi rõ giả định để xác nhận.
- Chỉ thêm raw/staging model nhỏ nếu model hiện có không lưu được punch đơn,
  nguồn hoặc khóa chống trùng; không ép sửa parser/import lớn khi không cần.
  Giữ raw event bất biến, dữ liệu tổng hợp có thể dựng lại, correction không
  xóa nguồn gốc. Không lưu ảnh/sinh trắc/credential trong payload hiển thị.
- Chống trùng theo source identity/fingerprint và semantic event/session
  hợp lệ, gồm import Excel lặp, API retry và Excel/API chứa cùng lượt công.
  Không chỉ hash tên tệp; eventID máy khác nhau có namespace riêng.
- Xử lý batch nguyên tử thích hợp, cursor/watermark chỉ tiến khi dữ liệu đã
  commit, retry không mất hoặc nhân đôi; sự kiện đến muộn phải tính lại đúng
  ngày/người nếu kỳ cho phép. Kỳ đã chốt giữ workflow/audit, không âm thầm sửa.
- Trang Nguồn dữ liệu tối thiểu: Excel đang dùng; API máy Chưa cấu hình,
  thiết bị/nhà cung cấp khi có, lần sync thành công/lỗi cuối, dữ liệu mới nhất.
  Chưa có thông số máy thì adapter live mặc định tắt, không chạy cron gọi URL
  giả, không mở endpoint public ghi công và không lưu token vào source/log.
- Chuẩn bị nơi cấu hình bảo mật cho endpoint/credential/cơ chế xác thực
  theo môi trường. Chưa chốt hãng thì chỉ contract/service và điểm mở rộng,
  checklist cần cung cấp: model máy, API/SDK, chiều sự kiện, eventID/cursor,
  timezone, network, auth, tần suất, ca làm. Không bắt người dùng cung cấp ngay
  để chặn phần dashboard/Excel đã được giao.
- Khi nguồn live được bật về sau, web có thể tự refresh nhẹ30–60giây hoặc dùng
  bus đã có; dừng khi tab ẩn, không request chồng, giữ bộ lọc/scroll và kết quả
  mới không bị response cũ đè. Refresh web không đồng nghĩa máy đã đồng bộ.

## 6. Quyền và bảo toàn hệ thống

Giữ quyền danh bạ/công hiện hành: nhân viên có thể xem công theo policy được
giao, không được sửa/xóa/import hoặc xem hợp đồng/CCCD/lương/raw payload máy.
Công của tôi lấy employee từ session, không tin owner_id phía client.

HR/người được giao nhập công dùng action backend gốc. Admin gốc và admin được
cấp quản trị nghiệp vụ theo DEC-053/054 khi ADMIN-FULL-001 được triển khai;
**chỉ admin gốc cấp/thu admin**. Không tự triển khai hoặc tự grant admin trong
task chấm công để mở màn. Nếu task admin đang chạy, phối hợp giữ checkpoint/
diff và dùng capability chung, không hardcode UID hoặc giả đã có policy runtime.

Filter/search/chart/count/export/drilldown/file cùng scope backend và cùng
mốc dữ liệu. Không mở public/token hoặc broad sudo chỉ để dashboard chạy.
Không thay tên/avatar/phòng ban/roster hoặc làm mất bản vá private-field HR.

## 7. Acceptance, áp dụng và bàn giao

Viết kiểm có ý nghĩa cho: Excel cũ, nguồn thiếu hôm nay, chưa có dữ liệu nghỉ,
IN chưa OUT, OUT→IN lại, ra buổi trưa, direction unknown, trùng/retry/đa nguồn,
sự kiện trễ, ranh ngày/ca qua đêm, tuần/tháng distinct-person, phạm vi quyền.
Không tạo fixture hoặc ghi fake punch vào main/server để test. Test thuần
normalizer/metrics bằng dữ liệu trong bộ nhớ; test ORM ghi/race chưa chạy
được theo môi trường cho phép thì ghi NOT_RUN, không coi static scan là PASS.

Trên dữ liệu thật đang có, kiểm chỉ đọc + browser: ngày có nguồn, hôm nay,
ngày chưa đến, tuần/tháng, filter/KPI/chart→list, pager, desktop/mobile, field
metadata theo model cha/con, file riêng không rò. Không dùng data cũ hiển thị
là realtime, không lấy ngày tương lai làm người nghỉ, không điền giờ giả.

Backup DB/filestore/source/config đúng môi trường trước upgrade/migration.
Áp18069 và PCserver, commit/push/deploy từng phần hoàn tất theo policy17/11;
không bắt18079, không tạo clone và không broad copy dirty tree. Server hiện có
`server-pc`/`tp-odoo`, source `C:\Projects\TANPHAT-ONE`, config
`/workspace/docker.odoo.conf`, public URL hiện hành; kiểm lại trước dùng.
Lỗi release thì sửa hoặc rollback đúng phần, giữ tunnel và dữ liệu thật.

Cập nhật version/status/changelog/guide/policy/filter inventory/acceptance,
start/finish/check đúng batch. Bàn giao: ảnh UI, cách xem ngày/tuần/tháng,
định nghĩa nghỉ/đã về, nguồn và dữ liệu đến ngày nào, phần API đã chuẩn bị
và thông tin còn cần để kết nối thật; commitSHA/version/backup, kiểm thực và
phần chưa kiểm. Không nói đã tích hợp API hoặc đang realtime khi chưa có máy.
