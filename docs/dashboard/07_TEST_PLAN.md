# Kế hoạch kiểm thử và đối chiếu số liệu

## 1. Phạm vi và tình trạng hiện tại

Tài liệu này đặc tả các test cần thực hiện khi xây addon. Lượt khảo sát đã đọc raw values, formula và cached result của workbook, đồng thời tính độc lập các tổng chính từ bản ghi hiệu lực. Chưa chạy test module, HOOT, asset build hoặc kiểm thử browser vì module chưa được tạo và runtime Odoo chưa khởi động được.

Không thay đổi workbook gốc để test. Test tổng hợp dùng fixture synthetic; đối chiếu thực tế dùng bản snapshot riêng có cùng SHA-256 và được lưu ngoài static/public repository. Không chạy VBA trong lượt này.

## 2. Snapshot đối chiếu đã đọc

Nguồn: DA Temp.xlsm tại \\192.168.1.2\6.3 Tadic_Thu viec\ERP\Ban KD. SHA-256: b09872dd439f199e5f80818d6f91e79d54966728c93b10792a50d126bd173db7. Các số tiền và tên đối tác được che khỏi tài liệu kế hoạch; đối chiếu chi tiết giữ trong report riêng có quyền. Không chuyển số liệu thật thành fixture public.

| KPI | Ô Excel/cache | Giá trị VNĐ/số | Phép kiểm độc lập từ nhật ký |
| --- | --- | --- | --- |
| CĐT HĐ gốc | ChuDauTu!C9; Dashboard!D8 | **Khớp cache (đã che giá trị)** | Tổng amount gốc của ID hiệu lực 4 và 5 |
| CĐT HĐ cập nhật | ChuDauTu!D9; Dashboard!D9 | **Khớp cache (đã che giá trị)** | Chưa có phụ lục hiệu lực >0; bằng HĐ gốc |
| CĐT nghiệm thu | ChuDauTu!F9; Dashboard!D11 | **Khớp cache (đã che giá trị)** | NHAT_KY_TC ID 3 cột G |
| CĐT hóa đơn đã ghi nhận | ChuDauTu!H9; Dashboard!D13 | **Khớp cache (đã che giá trị)** | NHAT_KY_TC ID 3 cột H |
| CĐT đã thu | ChuDauTu!I9; Dashboard!D14 | **Khớp cache (đã che giá trị)** | Tổng paid của ID hiệu lực 3 và 4 |
| CĐT giữ lại | ChuDauTu!J9 | **Khớp cache** | Tổng cột J các bản hiệu lực (giá trị không phát tán) |
| CĐT số dư NT | ChuDauTu!K9; Dashboard!D16 | **Khớp cache (âm; đã che giá trị)** | accepted − paid |
| CĐT số dư sau giữ lại | ChuDauTu!L9; Dashboard!D17 | **Khớp cache (âm; đã che giá trị)** | số dư NT − retention |
| Thầu phụ HĐ cấp 1 | Thauphu!H4:I4; Dashboard!H9 | **Khớp cache (đã che giá trị)** | Tổng hai dòng cấp 1 trong snapshot |
| Thầu phụ NT cấp 1 | Thauphu!K4; Dashboard!H11 | **Khớp cache (đã che giá trị)** | NHAT_KY ID 2 cột H |
| Thầu phụ đã trả cấp 1 | Thauphu!M4; Dashboard!H14 | **Khớp cache (đã che giá trị)** | NHAT_KY ID 2 cột I |
| Thầu phụ số dư NT cấp 1 | Thauphu!O4; Dashboard!H16 | **Khớp cache (đã che giá trị)** | accepted − paid |
| Thầu phụ số dư HĐ cấp 1 | Thauphu!N4; Dashboard!H17 | **Khớp cache (đã che giá trị)** | HĐ cập nhật − paid |
| Thầu phụ cấp 2 | Thauphu!I5; Dashboard!H22 | 0 | Không có bản ghi cấp 2 trong snapshot này |
| Số hạng mục CĐT | Dashboard!D7 | 2 | Hai tên khác nhau trên ChuDauTu |
| Số đơn vị cấp 1 | Dashboard!H7 | 2 | Hai đơn vị, không đếm số giao dịch/hạng mục |
| Bản ghi CĐT hiệu lực | NHAT_KY_TC!L5:O9 | 3 | Stream root 1 → ID4; root2 → ID5; root3 → ID3 |
| Bản ghi thầu phụ hiệu lực | NHAT_KY!K5:N7 | 3 | ID1,2,3 có root riêng, không XÓA |

Tỷ lệ CĐT và thầu phụ đều được tính lại từ tổng tiền nguyên, rồi so cache với tolerance 1e-12; cả bốn tỷ lệ khớp. Tài liệu này không ghi giá trị tỷ lệ nội bộ; report reconciliation có quyền giữ số chi tiết.

Các số sản lượng tại E9/J4 và “chưa NT” G9/L4 đang bằng 0 trong cache nhưng các dòng chưa NT được để trống khi sản lượng bằng 0. Không dùng các số 0 tổng này để khẳng định không còn việc chưa nghiệm thu. Trường hợp này phải giữ availability/ghi chú và được BA xác nhận.

## 3. Bộ tình huống nghiệp vụ bắt buộc

Các số ở bảng này là **số giả lập cho test**, không phải số dự án thực tế.

| ID | Input/điều kiện | Kết quả bắt buộc | Cấp test |
| --- | --- | --- | --- |
| B01 | NT 100, paid 120 | Số dư −20; tỷ lệ 1,2; alert attention giải thích có thể tạm ứng | unit + UI |
| B02 | HĐ gốc 100; phụ lục lần lượt 130 rồi 90 | HĐ gốc 100; HĐ cập nhật 90, không 320/220 | unit |
| B03 | Root1 ID1 paid10; ID9 sửa paid15 | Tổng15, không25; history còn ID1 | unit + repository |
| B04 | Root1 ID1; ID9 sửa; ID10 XÓA | Không bản nào góp vào totals; history hiển thị cả chuỗi | unit |
| B05 | Danh sách ID2, ID10, ID3 ở thứ tự bất kỳ | So thứ tự số, ID10 thắng; không sort lexical hoặc sort ngày | unit |
| B06 | Một đơn vị nhận hai hạng mục 40+60 | HĐ100, bảng2 dòng; đếm đơn vị1, không2 | unit + UI |
| B07 | Cty trực tiếp50; khoán phòng100; con40 | Tổng cấp 1=150; cấp 2 riêng40; không190 | unit + UI |
| B08 | Khoán mẹ100; con120 | Tổng cấp1 vẫn100; khoán còn lại−20; cảnh báo vượt20 | unit |
| B09 | Filter cấp2 con40 | Hiển thị40 cấp2; total company phạm vi lọc không cộng40 vào cấp1 | repository + UI |
| B10 | Con thiếu mẹ/khác dự án | Validation error rõ; không tự tạo parent hoặc bỏ vào cấp1 | contract |
| B11 | HĐ100, NT0, paid0 | NOT_ACCEPTED; paid/NT=null; không infinity/NaN | unit + UI |
| B12 | Thiếu production, accepted20 | unaccepted=null; không tự tính−20; thiếu dữ liệu được giải thích | unit |
| B13 | production0 được khai rõ | Giữ0; phân biệt unknown zero của Excel; công thức chưa NT theo quyết định BA | contract + UI |
| B14 | Dự án có metadata nhưng không giao dịch | Empty transaction state; không no-project state; không chart tiền giả | UI |
| B15 | Tiền 9.000.000.000.000 và tổng nhiều dòng | Cộng chính xác trong safe integer; VNĐ không clipping | unit + visual |
| B16 | Tổng vượt Number.MAX_SAFE_INTEGER | Validation lỗi out_of_range hoặc dùng Money V2 theo contract; không làm tròn âm thầm | contract |
| B17 | Tỷ lệ: 10/20 và 90/100 | Tổng100/120, không trung bình(50%,90%) | unit |
| B18 | Ngày Excel serial, ngày trống và ngày sai | ISO ngày đúng theo workbook epoch; ngày sai unavailable, không tự gán hôm nay | adapter |
| B19 | CĐT “Khảo sát”, TP “Khảo sát địa hình” | Không tự join; global filter/charts so cùng item chỉ bật sau crosswalk | contract + UI |
| B20 | Khoán mẹ có hai hạng mục; con gắn tên mẹ | Không SUM lặp R/S mẹ ở cả hai dòng; scope allocation cấp phòng | unit + BA |
| B21 | Bản phụ lục mới nhất bị XÓA | Loại stream đó rồi chọn phụ lục hiệu lực trước; không giữ phụ lục đã xóa | unit |
| B22 | Phụ lục 0 hoặc âm | Báo chưa được hỗ trợ/chờ BA vì Excel xét >0; không tự xem là không có phụ lục hợp lệ | contract |
| B23 | Cùng ID GỐC=1 ở NHAT_KY và NHAT_KY_TC | Hai stream riêng theo project+side+root; không ghi đè nhau | unit |
| B24 | Link thiếu hoặc target javascript/file UNC | Không link hoặc disabled explanation; không mở URL không được phép | contract + UI |

## 4. Bộ lọc và tính nhất quán

| ID | Thao tác | Kiểm chứng |
| --- | --- | --- |
| F01 | Chọn dự án B khi request A chưa xong | Response A bị bỏ qua; mọi vùng hiện B |
| F02 | Lọc hạng mục/đơn vị/loại | KPI, chart, table, alert cùng scope và snapshotId |
| F03 | Pagination 25/100 rows | Footer và KPI tổng đủ100, không chỉ25 |
| F04 | Search một phần tên | Chỉ dòng hiển thị thay đổi; label nêu tìm kiếm bảng; KPI giữ scope bộ lọc |
| F05 | Sort tiền, null, số âm | Sort raw integer; null cuối; kết quả deterministic khi bằng nhau bằng stable ID |
| F06 | Filter ngày ở tab history | Không cắt HĐ gốc khỏi snapshot KPI; chart tab ghi ngày ghi sổ |
| F07 | Reset và chuyển dự án | Xóa item/contractor không hợp lệ; không gửi filter của A sang B |
| F08 | Click KPI rồi Back | Danh sách góp vào KPI đúng; trở về giữ filter/sort/page |
| F09 | Reload lỗi | Dữ liệu cũ có nhãn stale; nút retry; không biến lỗi thành tổng0 |
| F10 | SnapshotId khác giữa 2 response | Không gộp; reload đồng nhất hoặc lỗi snapshot_mismatch |

## 5. Kiểm thử Odoo và frontend

- [ ] Cài module mới trên DB dev; manifest chỉ phụ thuộc web; menu mở tag action đúng.
- [ ] Upgrade module chỉ cập nhật addon; không sửa asset core; uninstall gỡ menu/action.
- [ ] `/web?debug=assets` không báo missing module/template hoặc lỗi OWL props.
- [ ] HOOT ở `/web/tests?mod=tanphat_dashboard` nạp đúng bộ test; route /web/tests đã xác minh trong addons/web/controllers/webclient.py.
- [ ] Các test chỉ nằm web.assets_unit_tests, không trong production src glob.
- [ ] Chuyển trang 30 lần: Chart instance được destroy, không listener/ResizeObserver còn treo.
- [ ] Loading/empty/error/retry/stale có nội dung đúng cho mỗi trang.
- [ ] Browser không fetch workbook thật, raw snapshot, số tài khoản, path NAS hoặc tên người liên hệ.
- [ ] Chỉ một Chart.js v4.5; không request CDN/font ngoài.
- [ ] JSON schema/money/scope invalid hiển thị lỗi có thể hiểu; không console spam hoặc nuốt lỗi.

## 6. Kiểm tra giao diện và khả năng tiếp cận

- [ ] Review 1440×900, 1366×768, 1024×768 và 768×1024; 200% zoom.
- [ ] Tên dự án dài không che selector; sidebar không chen navbar Odoo.
- [ ] Bảng cuộn ngang trong panel; số VNĐ lớn không cắt/clipping; tên dài đọc đủ qua panel.
- [ ] Null/0/âm/>100% nhìn khác nhau và có giải thích.
- [ ] Header/table/canvas có contrast đạt mục tiêu; màu không là dấu hiệu duy nhất.
- [ ] Tab/Enter/Escape hoạt động; focus trở về phần tử mở detail.
- [ ] Screen reader nhận label filter, sort, loading và nội dung empty/error.
- [ ] Mỗi chart có bảng thay thế; reduced-motion tắt animation.
- [ ] Tablet dùng drawer sidebar; đóng panel không khóa scroll nền sai.

## 7. Hiệu năng mục tiêu và cách đo

Đo trên một máy dev đã ghi cấu hình, browser hiện đại và asset production warm cache. Mục tiêu đề xuất cho fixture 5.000 giao dịch, 500 dòng tổng hợp: render view đầu sau khi asset sẵn <1 giây; đổi filter <300 ms; trang bảng25/50 dòng phản hồi <200 ms. Đây là ngân sách thiết kế chưa đo, không phải cam kết hiệu năng đạt sẵn.

Record Performance trace để tìm render/aggregate đắt; benchmark 10 lần sau warm-up, báo median/p95 và số row. Không tối ưu bằng cách bỏ effective filter hoặc round tiền. Khi vượt ngân sách, memo theo snapshot/query hoặc chuyển aggregate server ở roadmap; chưa thêm virtual grid nếu Pager đáp ứng.

## 8. Quy trình reconciliation và điều kiện phát hành

1. Đóng băng snapshot copy và hash; ghi workbook version, epoch, calcId và timestamp.
2. Đọc raw nhật ký và cache thành hai dataset riêng. Tính độc lập bằng quy tắc hiệu lực và phụ lục; không lấy tổng cache làm expected cho chính implementation cùng logic.
3. So từng item/đơn vị → tổng cấp1/cấp2 → Dashboard references. Kiểm ID/count chính xác; tiền integer tolerance0; tỷ lệ tolerance1e-12.
4. Với cache thiếu/stale, ghi mismatch và yêu cầu owner mở/recalculate một bản sao bằng Excel. Không tự cập nhật file NAS; không coi cache là kết quả vừa tính lại.
5. Với khác biệt do UI availability (ví dụ G9=0 do SUM các blank), ghi khác biệt diễn giải và BA duyệt. Không sửa số âm/công thức để “khớp hình”.
6. Báo cáo mỗi mismatch gồm metricId, scope, nguồn ô/ID, expected, actual, delta, lý do, owner và trạng thái. Che dữ liệu thật trong test report public.

Release mock chỉ đạt khi B01–B24 có kết quả rõ, F01–F10 pass, không sai tổng tiền, không double count, test Odoo và visual review đạt. Phát hành dữ liệu thật còn phải đạt permission test và reconciliation API ở roadmap. Không đánh dấu pass cho test chưa chạy; trường hợp chờ BA ghi blocked riêng theo chức năng bị ảnh hưởng.
