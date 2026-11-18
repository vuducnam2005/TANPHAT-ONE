# HR-ATTENDANCE-SIMPLE-002 — Tổng quan chấm công gọn, chuẩn bị API máy

Làm việc trong `C:\TANPHAT ONE`. Triển khai yêu cầu18/11/2026, DEC-055/056; bản hợp nhất đã cập nhật Excel.
**Đơn giản hóa chấm công hiện có, giữ dữ liệu Excel đã nhập, chuẩn bị nền
tích hợp máy chấm công sau này.** Chưa có tài liệu API/loại máy/credential;
không giả lập đang kết nối thật và không mở live connector theo suy đoán.

## 1. Mục tiêu và phạm vi

Người dùng chỉ cần một nơi dễ nhìn để biết:

- Công ty/phạm vi được xem có bao nhiêu nhân viên.
- Hôm nay có bao nhiêu người nghỉ, bao nhiêu người đã về.
- Xem danh sách và thống kê theo **ngày, tuần, tháng**.
- Tải thẳng Excel xuất từ máy, tự nhận diện và lập bảng; giờ làm08:30–17:00,
  số lần/phút đi muộn giữ nguyên tổng kỳ Excel theo mục2A.
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

## 2A. Bổ sung đã chốt: tải Excel máy và tự tạo bảng công

**Bản cập nhật18/11/2026 này đã gồm yêu cầu mới; người dùng chưa chạy prompt
cũ, hãy thực hiện một bản hợp nhất này.** Giờ làm tham chiếu người dùng đã
chốt cuối cùng: **08:30–17:00**, thay thông tin17:30 trước đó. **Số lần và tổng
phút đi muộn giữ nguyên số xuất từ Excel, không tự tính lại bằng giờ vào.**
Giờ làm không tự xác nhận/thay thế lịch HR cũ ngoài scope, không dùng làm
căn cứ suy nghỉ không phép hoặc làm mất correction/chốt kỳ.

### File thực tế đã đọc và khả năng tái sử dụng

- File riêng của người dùng: `C:\Users\vuduc\Downloads\bang cham cong vao ra.xlsx`.
  Đây là đường dẫn local để triển khai đọc khi có, **không phải đường dẫn
  runtime trên PCserver**. Trên web, admin/HR tải file từ máy của mình lên.
  Không commit file nguồn hoặc danh sách nhân viên vào Git.
- Workbook có sheet `Report`, tiêu đề `BẢNG CÔNG THÁNG`, kỳ tại dòng
  `Từ ngày09/11/2026 - Đến ngày15/11/2026`,39 người. Tên báo cáo có chữ tháng
  nhưng kỳ thực tế chỉ7 ngày; ngày xuất và nhãn năm2017 cũ không là kỳ công.
- Hai hàng header: STT, Mã nhân viên, Tên nhân viên, **ID máy**, Chức vụ;
  cột ngày có9..15 và T2..CN; mỗi người hai dòng Vào/Ra; giữa các nhóm có
  dòng tên đơn vị. `Mã nhân viên` dạngTP00x trong file khác ID máy và mãTP100xx
  của HR. Dùng mapping ID máy đã có, giữ nguyên guard kiểm tra nhân viên;
  không lấy số thứ tự hoặc vị trí hàng làm employee ID, không ghép chỉ bằng tên.
- `Đi muộn` có hai cột con **Lần/Phút** (file nàyAC/AD). Phải dò hai tầng
  header và merged cell để đọc ngữ nghĩa, không hardcodeAC/AD: file2–3 tuần/
  tháng sẽ có nhiều cột ngày hơn và vị trí tổng hợp dịch sang phải.
- Chạy bộ parser thuần hiện tại trên file thấy150 cặp đủ giờ,28 ngày có giờ
  vào thiếu giờ ra,95 ô ngày-người trống, không lỗi định dạng. Đây là kết quả
  phân tích file, **không phải bằng chứng dữ liệu đã nhập vào DB**. Không bỏ
 28 dòng thiếu giờ khi lên bảng chỉ vì chúng chưa tạo được session đóng.
- Parser hiện đọc giờ nhưng chủ động bỏ cột tổng hợp; import view cũng có
  câu giải thích tương ứng. Muốn đọc Đi muộn phải sửa parser/contract/lưu
  nguồn/import/UI/test/help/README/policy/guide đồng bộ, không chỉ thay nhãn.
  Tái sử dụng batch/preview/apply/mapping/dedupe hiện có, không viết importer
  thứ hai hoặc yêu cầu người dùng chuyển đổi sang template của hệ thống.

### Luồng thao tác mong muốn: tải file → xem trước → nhập

1. Nút nổi bật **Nhập Excel máy chấm công** ở Bảng chấm công/Tổng quan cho
   người có quyền. Hộp tải kéo-thả hoặc chọn tệp `.xlsx`; không phải gõ tên
   lô, nhập từng người, kỳ công hoặc map từng cột với định dạng đã nhận diện.
2. Chọn file xong tự đọc và tạo bản xem trước: kỳ ngày thực tế, nhân viên
   đã khớp, dòng mới/trùng/thiếu giờ/chưa khớp/xung đột, số đi muộn từ file.
   Nút **Nhập dữ liệu** ghi các dòng hợp lệ; không phải nhập lại bằng tay.
   Có thể chọn file khác/hủy trước khi ghi. HR chỉ xử lý các ngoại lệ.
3. Sau nhập, bảng công và dashboard đọc cùng dữ liệu đã lưu PostgreSQL;
   refresh/đăng nhập máy khác không mất kết quả. Mở đúng kỳ vừa nhập với
   nhãn ngày rõ, không thay ngày lịch sử thành hôm nay. Công cá nhân cập nhật
   từ cùng nguồn. Lịch sử nhập gọn ghi file/người/giờ/kỳ/kết quả/nguồn.
4. Không giới hạn đúng7 ngày hoặc cố định số cột. Nhận1 tuần,2 tuần,3 tuần,
   cả tháng hoặc khoảng ngày trong phạm vi được hỗ trợ hiện có, gồm28/29/30/31
   ngày, khác tháng/năm, nhiều sheet khi định dạng đủ căn cứ. Đọc thứ từ lịch
   thực và đối chiếu header; tên file/tiêu đề không quyết định ngày tháng.
   Nếu số ngày lặp giữa hai tháng mà header không đủ giải nghĩa, báo vị trí
   lỗi cần xem lại, không đoán tháng. Không tự chặn cả tháng vì validation7 ngày.
5. Ô trống = chưa có ghi nhận; thiếu Vào/Ra hiện riêng giờ còn lại và dấu—
   ở giờ thiếu; không tự tạo giờ17:00, không mặc định nghỉ. Ký hiệu nghỉ hoặc
   nhiều giờ trong cùng ô chưa hiểu thì giữ nguồn và gắn cảnh báo, không bịa.
6. Nhập lại cùng file, đổi tên file hoặc tuần chồng với file tháng không nhân
   đôi giờ và không cộng tổng Đi muộn hai lần. Sửa giờ/tổng khác cho kỳ đã
   nhập phải phân loại xung đột, không âm thầm last-write-wins. Giữ ngày đã
   chốt và correction có lịch sử; không clear nguồn cũ để làm lại giao diện.

### Số đi muộn: giữ nguyên nguồn máy và đúng kỳ

- Lưu số lần/phút **ở cấp nhân viên + kỳ nguồn + batch/provenance**, riêng
  với giờ theo từng ngày. Chỉ đọc nhóm Đi muộn/Lần/Phút; bỏ nhóm Về sớm,
  Tổng công, công ngày/đêm, tăng ca, tổng giờ, vắng mặt khỏi UI/import contract
  mới nếu không còn được dùng; dữ liệu/model lịch sử vẫn giữ để không phá hệ thống.
- Không tính lại số phút từ08:30, không trừ khoảng cho phép, không suy ca
  chiều, không dùng default08:00 của rule cũ thay số máy. Cấu hình08:30–17:00
  là giờ tham chiếu hiển thị; chưa xây engine tính muộn mới trong task này.
- Tổng máy là tổng **cả kỳ của file**, không có phân bổ từng ngày. Khi xem
  đúng kỳ: hiện N lần/M phút, nhãn **Theo Excel máy**. Khi lọc một ngày hoặc
  phần của kỳ: không lấy/copy/chia đều tổng này cho ngày, không hiển thị0 như
  đã xác nhận không muộn. Chỉ hiện giờ ngày đang xem và ghi ngắn **Số đi muộn
  có ở tổng kỳ09–15/11**; mở panel tổng kỳ riêng, giữ bộ lọc ngày hiện tại.
- File không có cột Đi muộn, có cột mà ô trống, hoặc số không hợp lệ: vẫn
  nhập được giờ hợp lệ, số muộn hiện **Chưa có số liệu**, cảnh báo HR xem lại.
  Phân biệt thiếu với số0; số lần phải nguyên không âm, số phút không âm;
  không tự sửa số nguồn bất nhất để làm báo cáo đẹp. Không tính0 cho người
  có phút chưa rõ hoặc chỉ map thành công một phần danh sách.
- Bộ lọc phòng ban/nhân viên vẫn áp đúng scope. Tổng từ nhiều kỳ chỉ cộng
  các khoảng **không chồng, phủ đủ kỳ đang xem và cùng nghĩa nguồn**. Trùng
  kỳ chọn một bản được áp dụng hợp lệ; tuần chồng tháng không cộng hai bản,
  không trừ để đoán phần còn lại. Nếu không có nguồn phủ chính xác thì hiện
  các kỳ nguồn riêng/Chưa có tổng đúng kỳ, không bịa số tháng hoặc số từng ngày.
- API sau này có thể chỉ gửi giờ vào/ra, không gửi tổng muộn của máy. Giữ
  khả năng nhận cả sự kiện và tổng kỳ có nguồn, không buộc API tương lai có
  cột Excel. Chưa có dữ liệu muộn/API rule thì báo thiếu; việc tính muộn tự
  động về sau là quyết định riêng, không âm thầm thay số Excel đã lưu.

### Bảng đầu ra tối giản theo yêu cầu mới

- **Ngày/toàn bộ nhân viên:** Nhân viên (tên + mã chung), Phòng ban, Thứ/ngày,
  Giờ vào, Giờ ra. Thứ và ngày chung một ô; không lặp7 cột tổng hợp máy.
  Nguồn/lần nhập/cảnh báo nằm tooltip hoặc chi tiết có quyền, không ép thành
  nhiều cột. Không thêm giờ công/OT/về sớm/lương/công ngày-đêm.
- **Kỳ tuần/tháng/khoảng ngày:** một dòng mỗi nhân viên, chỉ Nhân viên,
  Phòng ban, Số lần đi muộn, Tổng phút muộn. Nhãn kỳ số nguồn đặt rõ trên
  bảng; chưa có tổng đúng kỳ thì không gán số khác kỳ. Bấm người mở giờ theo
  ngày. Có nút **Kỳ theo file** để xem đúng khoảng của file2–3 tuần.
- **Chi tiết một người/Công của tôi:** tiêu đề tên/mã/phòng, kỳ; hai chỉ số
  nhỏ Số lần đi muộn/Tổng phút muộn theo đúng kỳ nguồn; bảng chỉ **Thứ/ngày,
  Giờ vào, Giờ ra**. Cảnh báo thiếu giờ nhỏ ngay tại ô, không nhồi field raw.
  Không tạo cột Muộn(phút) theo ngày vì file này không cung cấp số đó.
- Xuất Excel gọn theo đúng quyền/bộ lọc: sheet giờ từng ngày với các cột
  tối giản, sheet Tổng đi muộn khi có kỳ nguồn chính xác; ghi rõ khoảng ngày
  của mỗi bảng. Tổng kỳ nguồn khác khoảng ngày chọn thì không trộn vào như
  tổng của phạm vi xuất. Không xuất cả file/raw HR riêng cho người chỉ đọc.
- Dashboard ba KPI theo mục3/4 vẫn giữ. Có chip nhỏ tổng muộn khi đúng kỳ
  nguồn; không tăng thành dashboard chằng chịt. Biểu đồ tổng hợp/chỉ số chỉ
  dựa nguồn đủ nghĩa; không vẽ xu hướng muộn từng ngày từ tổng tuần.

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
5. Bảng rõ đường phân cách, **dùng bộ cột tối giản theo mục2A** cho từng
   chế độ; không giữ nguyên bảng nhiều cột cũ. Nguồn/cập nhật vẫn có ở dải
   thông tin chung và chi tiết theo quyền, không cần lặp từng cột. Dữ liệu
   thiếu hiện—/Chưa có số liệu đúng nghĩa; mở chi tiết chỉ xem giờ từng ngày.

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

Acceptance bắt buộc cho bổ sungExcel: đọc đúng file thực tế chỉ đọc; tự
nhận kỳ9–15/11 dù nhãnTHÁNG/ngàyxuất2017; mappingID đúng;150cặp và28thiếu
giờ vẫn hiển thị đúng; tổngLần/Phút khớp từng ô nguồn, giữ0khác thiếu. Dùng
fixture ẩn danh trong bộ nhớ cho7/14/21/ngày28–31, khác tháng/năm, header
merged/dịch cột, lặp/chồng/đổi tên file, tổng máy xung đột/thiếu cột, lọc
ngày không mang tổng tuần sang. Không ghi tên/giờ người thật vào testGit.
Giữ08:30–17:00 và không tự tính lại muộn; UI tối giản ngày/kỳ/chi tiết/export
và thao tác kéo-thả→preview→nhập cần ảnh/evidence khi triển khai.

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
