# HR-DASH-001 — Kế hoạch thiết kế lại tổng quan nhân sự

**12/11/2026:** [HR-DASH-002](HR_DASH_002_LIGHT_CHART_DESIGN.md) đã áp18069,
thay hình thức bằng dashboard sáng cố định, sidebar navy theo phản hồi CHG002, donut lớn và thanh chức vụ
dễ đọc. Hướng dark tự động trong thiết kế/lượt CHG010 cũ đã được bỏ theo yêu
cầu người dùng; metric/backend/lock không đổi.

Ngày 11/11/2026 (Asia/Saigon). Kế hoạch gốc CHG008; thực thi tại CHG010: IMPLEMENTED_VERIFIED_MAIN_APPLIED.

Cập nhật: đã áp dashboard và yêu cầu bổ sung khóa/mở lên18069 sau test/restore. [Kết quả](../demo/HR_DASH_001_ACCEPTANCE.md), [hướng dẫn](../demo/HR_DASH_001_USER_GUIDE.md). Các mô tả “chưa triển khai” bên dưới là hiện trạng tại lúc lập kế hoạch, không phải trạng thái runtime mới. Cột trạng thái hồ sơ trên list đã đổi Tình trạng tài khoản theo yêu cầu mới; archive vẫn riêng.
[Prompt thực thi](../prompts/CLAUDE_HR_DASH_001_OVERVIEW_REDESIGN.md).

## 1. Mục tiêu và căn cứ hiện tại

Màn Tổng quan cần giúp người phụ trách trả lời nhanh: đang quản lý bao nhiêu
hồ sơ; phân bố ở đơn vị/chức vụ nào; dữ liệu nào cần bổ sung; đi tới thao tác
ở đâu. Đây là dashboard hồ sơ và tổ chức hiện tại, chưa là báo cáo chấm công,
lương hoặc quyết định nhân sự pháp lý.

Đã đọc source OWL/QWeb/SCSS, backend `tp.hr.workspace`, export và test liên quan.
Chưa chụp lại dashboard live hoặc truy vấn số liệu runtime trong lượt này.
Các kết quả HR-UI-003/004 trong status là bàn giao trước, chưa audit lại ở đây.
Bản xem trước tương tác dùng dữ liệu minh họa có nhãn, không PII và không
gọi Odoo; đặt tại thư mục visualization của chat. Kiểm Playwright 11 nhóm,
0 pageerror, 5 viewport và dark/reduced-motion; ảnh1440/390 đã xem. Bằng chứng
private `.local/hr-dash001-plan/`; đây là kiểm bản thiết kế, không test Odoo.

| Hiện có trong source | Hướng cải thiện |
| --- | --- |
| Header TP HR, 3 nút làm mới/thêm/xuất Excel | Tiêu đề Tổng quan nhân sự, thời điểm cập nhật rõ; nút chính có thứ bậc |
| Lọc đơn vị và trạng thái hồ sơ | Thêm lọc chức vụ, chỉ giữ lọc có dữ liệu; nhãn bộ lọc đang áp dụng |
| 4 khối KPI, liên kết/chờ liên kết nằm chung một khối | 5 chỉ số tách nghĩa, click mở đúng danh sách, không làm người xem đoán hai số |
| Donut và thanh ngang cùng đếm theo đơn vị | Donut theo đơn vị; thanh ngang theo chức vụ, hai góc nhìn khác nhau |
| Đoạn văn chất lượng hồ sơ, chưa khai thác missing_job/contact | Checklist có số lượng, định nghĩa và lối xử lý; giữ ghi chú ngắn |
| Donut màu theo index danh sách | Màu gắn ổn định với ID đơn vị, không đổi ý nghĩa khi lọc/sắp xếp |
| `missing_contact` chỉ xét work_email/work_phone | Nếu dùng chỉ số thiếu liên hệ, tính cả mobile_phone và test đúng domain |
| Reports và Overview cùng client action | Không gọi hai màn là hai chức năng khác nhau; chỉ tách report action gọn nếu cần giữ lối Báo cáo riêng |

Ở lần đọc đầu, source còn active checkpoint từ lượt trước; table/table.js và
views/workspace.xml khác snapshot, checker báo lệch CHG-20261111-006. Trong
lượt lập kế hoạch, tác vụ đó đã bàn giao CHG-20261111-007 (HR-UI-005). Đã kiểm
lại 378 file/digest `f8df05b6de557d5319c68984ce3ebc3c6a16899d23f5cf69e4af9bb44ab7785d`
khớp state mới và checkpoint tài liệu của phiên này. Không finish thay batch
cũ hoặc gọi việc đối chiếu hash là audit ứng dụng HR-UI-005.

## 2. Bố cục được đề xuất

Giữ navbar/sidebar TP HR. Không thêm thanh điều hướng hoặc banner lớn mới.
Trên màn desktop 1440px, phần đầu thấy trọn tiêu đề, bộ lọc và hàng KPI; hai
biểu đồ bắt đầu ngay phía dưới. Mỗi vùng phục vụ một câu hỏi rõ.

```text
Sidebar | Tổng quan nhân sự                 [+ Thêm nhân viên] [Xuất Excel]
        | Cập nhật: ...                     [Làm mới]
        | Đơn vị [Tất cả]  Chức vụ [Tất cả]  Hồ sơ [Đang quản lý]  [Xóa bộ lọc]
        |
        | Hồ sơ | Đơn vị có người | Đã liên kết | Chưa liên kết | Thiếu cơ bản
        |
        | Cơ cấu theo đơn vị                | Cơ cấu theo chức vụ
        | Donut + tổng ở tâm                | Thanh ngang có số lượng
        | Chú giải: tên / số / %             | Tên chức vụ đầy đủ, click xem
        |
        | Tổng hợp theo đơn vị (2/3)        | Cần bổ sung (1/3)
        | Đơn vị | Hồ sơ | Liên kết | Thiếu  | Thiếu mã/đơn vị/chức vụ/liên hệ
        | [Xem nhân viên]                   | [Mở danh sách tương ứng]
        |
        | Tài khoản: Có liên kết / Chưa liên kết; vô hiệu hóa nếu đủ quyền
```

Không nhồi thêm biểu đồ chỉ để đầy màn hình. Không lặp donut và bar cùng
một chiều dữ liệu. Tài khoản dùng thanh tỷ lệ đơn giản, không thêm donut thứ
hai. Bảng tổng hợp giúp đối chiếu và làm việc, không thay danh sách nhân viên.

## 3. Định nghĩa số liệu

Population P là tập employee người xem được đọc, trong company hiện hành và
bộ lọc đơn vị/chức vụ/trạng thái hồ sơ. Mọi KPI/chart/table/drill-down/export
cùng P. Thời điểm cập nhật là lúc đọc hiện trạng, không phải kỳ chốt nhân sự.

| Chỉ số | Định nghĩa và hành động |
| --- | --- |
| Hồ sơ nhân viên | Count(P). Nếu lọc active ghi “Hồ sơ đang quản lý”; không gọi tất cả là nhân viên chính thức |
| Đơn vị có nhân viên | Số department khác rỗng trong P; không đếm toàn catalog hoặc đơn vị không có người |
| Đã liên kết tài khoản | User_id có giá trị trong P; không suy rằng tài khoản đó còn active/được quyền vào mọi phòng |
| Chưa liên kết tài khoản | User_id rỗng; là trạng thái trung tính, không mặc định là lỗi hoặc cần tạo user cho mọi người |
| Cần bổ sung cơ bản | Thiếu mã TP hoặc đơn vị hoặc cả chức vụ nguồn và job_id; mỗi người đếm một lần |
| Cơ cấu chức vụ | Group theo job_id trong P; thiếu thì có nhóm Chưa khai báo. Chuẩn hóa job trước đó không tự xác nhận thẩm quyền/quyền |
| Thiếu chức vụ đã khai báo | job_id rỗng; có thể khác thiếu cơ bản vì chức vụ nguồn vẫn có. Nhãn phải nêu rõ sự khác nhau |
| Thiếu liên hệ | Cả work_email, work_phone và mobile_phone đều thiếu; là mục tùy chọn, không gộp vào checklist cơ bản âm thầm |

Đã liên kết + chưa liên kết = tổng P; đủ cơ bản + thiếu cơ bản = tổng P.
Các lý do thiếu dữ liệu có thể chồng lặp, không cộng chúng thành tổng người.
Chưa liên kết không có nghĩa người lao động không tồn tại hoặc không làm việc.

Donut theo đơn vị phải gồm nhóm Chưa khai báo nếu có, tổng bằng P. 9 đơn vị
hiện tại là số tham chiếu từ bàn giao, không hard-code số 9/39 trong runtime.
Giữ nhãn/tỷ lệ/số đếm; có nhiều hơn 12 nhóm thì legend cuộn trong vùng rõ,
không xóa nhóm khỏi thống kê hoặc gom Khác mà mất drill-down.

Thanh chức vụ sắp xếp theo số hồ sơ giảm dần, tie-break ổn định; click mở đúng
job_id. Màu thanh cùng một measure, không tô 11 màu vô nghĩa; mỗi thanh có
nhãn và số. Tên dài xuống dòng hoặc xem đầy đủ, không chỉ cắt dấu ba chấm.

Chi tiết account active/disabled chỉ hiện nếu actor có quyền đọc tương ứng.
Tổng hợp account không trả login, password, group, email cá nhân hoặc thông tin
riêng tư ra dashboard. Không dùng sudo để lấy số người/user ngoài phạm vi.

## 4. Phong cách giao diện

- Navy `#17324D`: tiêu đề/nhận diện; teal `#087F8C`: thao tác chính;
  nền `#F5F7FA`; chữ `#233549`; đường chia `#DCE3EB`; amber `#9A6700`:
  cần đối chiếu. Màu trạng thái theo semantic token sẵn có.
- Giữ font đã cài hỗ trợ tiếng Việt. Tên trang 26–30px; KPI 28–34px;
  body 14–16px; label 13–14px. Số dùng tabular figures, căn phải trong bảng.
- Grid 8/12/16/24px; page padding 24px desktop, 16px mobile. KPI nền nhẹ,
  icon có nghĩa, không gradient mỗi ô hoặc shadow đậm. Biểu đồ là trọng tâm.
- Donut có tooltip tên/số/% và legend bấm được. Hover/focus làm rõ nhóm,
  dữ liệu vẫn hiểu bằng chữ, số và bảng; không chỉ dựa màu.
- 150–220ms cho hover/focus/filter/panel; chart update có transition nhẹ,
  tôn trọng reduced-motion. Không counter chạy từ 0 hoặc animation lặp.
- Loading skeleton cùng chiều cao, empty có xóa filter, lỗi có thử lại,
  không quyền có nhãn rõ. Không giữ số stale như thể vừa refresh thành công.
- Desktop: hai biểu đồ cân tỷ lệ, bảng 2/3 + việc cần bổ sung 1/3. Tablet:
  KPI 2–3 cột, chart xếp dọc. Mobile: KPI 2 cột rồi 1 nếu cần, filter dạng
  panel gọn, nút đủ lớn; không tràn ngang toàn trang hoặc thu chữ quá nhỏ.

Đánh giá lại brief: bỏ banner chào hỏi và thông tin ngày trang trí vì không
giúp quản lý hồ sơ; bỏ bar theo đơn vị trùng donut; bỏ điểm “hoàn thiện hồ sơ”
không có checklist xác định. Khoảng trống dành cho tên đơn vị/chức vụ dễ đọc.

## 5. Tương tác và báo cáo

- Filter đơn vị/chức vụ/status; Xóa bộ lọc về trạng thái mặc định. Không thêm
  filter tháng/năm khi chưa có snapshot/history phù hợp. Company theo Odoo.
- Danh mục filter ổn định từ backend có scope, không lấy duy nhất từ group
  đang lọc khiến mất lựa chọn khi count=0. Không nhớ filter sang account/company.
- Click KPI/slice/legend/bar/row mở employee list cùng P + điều kiện mục đã
  chọn; nút quay lại giữ filter. Không auto-filter rồi drill-down khác nghĩa.
- Bảng tổng hợp: Đơn vị, số hồ sơ, đã link, chưa link, thiếu cơ bản, xem danh
  sách; sort có ý nghĩa. Có search/chọn 10/20/50/100 nếu thành bảng phân trang;
  tổng KPI/chart không phụ thuộc trang hiện tại của bảng.
- Mở hồ sơ dùng form mới hiện hành; thêm nhân viên chỉ hiển thị nếu có quyền,
  backend vẫn enforce. Không đưa reset mật khẩu/thay quyền vào dashboard.
- Excel dùng chính filter; metadata ghi company/phạm vi/thời điểm, tổng và
  worksheet có style/format rõ. Giữ danh sách đầy đủ được đọc, không chỉ trang.
  Mở rộng job filter ở controller/export/backend cùng lượt, không chỉ UI.
- Menu Báo cáo hiện dùng cùng client action: giữ khả năng xuất, không thêm
  bản dashboard thứ hai. Nếu cần tách entry để không lặp màn, dùng context/mode
  hoặc report action nhỏ mở bảng tổng hợp/Excel; không mở dự án report lớn.

## 6. Lộ trình giao Claude và điều kiện hoàn tất

| Chặng | Công việc | Đầu ra |
| --- | --- | --- |
| S0 | Khép batch HR đang mở; đối chiếu source/runtime/quyền và metric contract; ảnh trước | Baseline rõ, không ghi đè checkpoint hoặc tự nhận thay đổi cũ đã đạt |
| S1 | Wireframe + tokens và dữ liệu chart/KPI/table/filter thống nhất | Spec/acceptance; nhóm và số liệu có định nghĩa, trạng thái thiếu dữ liệu rõ |
| S2 | Backend aggregate theo job/account/quality, filter/export parity, tests | DTO có scope và domain đồng nhất; không đọc lương hoặc bí mật tài khoản |
| S3 | OWL/QWeb/SCSS bố cục mới, hover/motion, filter và drill-down | Dashboard đổi rõ bố cục, responsive; profile/sidebar cũ không regression |
| S4 | Odoo/HOOT/Playwright, ảnh cùng role/viewport, Excel đối chiếu | Kiểm count/tổng/domain/race/error/empty/quyền/reduced-motion đạt trên test |
| S5 | Backup/restore kiểm chứng, áp source đã test lên main theo prompt được giao | Main18069 dùng được, 39 hồ sơ/quyền hiện hữu giữ, guide và rollback |

S0 kiểm lại trạng thái ngay khi giao thực thi; không triển khai ứng dụng chồng
lên batch đang ghi. Lần này không code/đổi DB/chạy upgrade/deploy. Prompt thực thi là bước
tiếp theo khi giao Claude; nghiệm thu hình thức/nghiệp vụ vẫn riêng.

## 7. Dữ liệu chưa đủ, không đưa lên dashboard lần này

Không có căn cứ để đưa mức lương/quỹ lương, công/đi muộn, tỷ lệ nghỉ việc,
biến động theo tháng, tuổi/giới tính, phép, headcount kế hoạch hoặc năng suất.
Không bịa ngày vào làm từ ngày import/version. Khi bổ sung nghiệp vụ và nguồn,
thiết kế riêng các chỉ số đó; không để widget trống “Đang phát triển” chiếm chỗ.

