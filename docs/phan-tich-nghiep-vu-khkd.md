# Phân tích nghiệp vụ Phòng Kế hoạch Kinh doanh

## 1. Phạm vi và mức độ tin cậy

Nguồn chính là workbook `Mẫu PKH - Quản trị dự án v10_5.xlsm` trên ổ dùng chung. Workbook ghi rõ bản v10.5 ngày 08/10/2026 và dành cho nhân viên Phòng Kế hoạch nhập liệu, lãnh đạo đọc số liệu.

Phân tích này mô tả **nghiệp vụ được thể hiện trong file**, chưa phải quy trình chính thức đã được phòng ban ký xác nhận.

| Mức độ | Nội dung |
| --- | --- |
| Tin cậy cao | Tên trường nhập, hai luồng giao dịch, cách tổng hợp, công thức chỉ tiêu, quy tắc sửa/hủy và phân loại thầu phụ |
| Tin cậy trung bình | Ai thực tế nhập/kiểm tra/duyệt, tần suất cập nhật, cách phối hợp với Kế toán và mức độ sử dụng từng báo cáo |
| Chưa xác định | Quy trình phê duyệt chính thức, SLA, quyền chi tiết, quy định lưu trữ, ngoại lệ nghiệp vụ và phạm vi dữ liệu lịch sử cần chuyển |

## 2. Mục đích nghiệp vụ

Phòng Kế hoạch theo dõi tình hình thực hiện từng dự án tư vấn xây dựng, gồm:

1. Giá trị và tiến độ hợp đồng với chủ đầu tư.
2. Sản lượng thực hiện, nghiệm thu, xuất hóa đơn, tiền nhận và khoản giữ lại.
3. Chi phí và nghĩa vụ thanh toán với thầu phụ, phòng/đội nhận khoán nội bộ.
4. Khoản khoán đã giao, phần phòng tự thuê ngoài và khoán còn lại.
5. Hồ sơ/chứng từ liên quan và lịch sử thay đổi để đối chiếu.

Đơn vị theo dõi chính là **một dự án**, trong đó hợp đồng được chia thành nhiều **hạng mục/nhóm công việc**.

## 3. Các bên liên quan được thể hiện trong file

| Bên | Vai trò thể hiện trong workbook | Cần xác nhận thêm |
| --- | --- | --- |
| Nhân viên Phòng Kế hoạch | Nhập giao dịch và theo dõi tổng hợp dự án | Có phân người nhập theo dự án/hạng mục không |
| Trưởng/phụ trách Phòng Kế hoạch | Kiểm tra số liệu và báo cáo | Có quyền duyệt trước khi số liệu được dùng không |
| Lãnh đạo công ty | Đọc Dashboard và file tổng hợp | Chỉ xem tổng quan hay cần xem chi tiết |
| Phòng Kế toán | Có file riêng theo dự án về hóa đơn và tiền về | Cách đối chiếu mã dự án, giao dịch và số tiền |
| Quản trị file/hệ thống | Cài macro, bảo vệ file, tổng hợp dữ liệu | Ai chịu trách nhiệm vận hành và xử lý lỗi |

## 4. Mô hình dữ liệu nghiệp vụ

### 4.1. Các đối tượng chính

| Đối tượng | Ý nghĩa |
| --- | --- |
| Dự án | Hồ sơ cấp cao nhất, có mã dự án, tên/gói thầu và chủ đầu tư |
| Chủ đầu tư | Bên trả tiền cho Tadic theo hợp đồng |
| Hạng mục/nhóm công việc | Đơn vị theo dõi hợp đồng và tiến độ, dùng chung tên ở cả hai phía |
| Giao dịch chủ đầu tư | Một sự kiện phát sinh với chủ đầu tư |
| Thầu phụ/đơn vị nhận khoán | Đơn vị bên ngoài hoặc phòng/đội/cá nhân nội bộ nhận việc |
| Giao dịch thầu phụ/khoán | Một sự kiện phát sinh với đơn vị thực hiện |
| Khoán nội bộ | Phần giá trị giao cho phòng/đội nội bộ |
| Thầu phụ của phòng | Đơn vị ngoài do phòng nhận khoán tự thuê, chi phí đã nằm trong khoán mẹ |
| Tài liệu/chứng từ | Link hợp đồng, phụ lục, nghiệm thu, hóa đơn, ủy nhiệm chi hoặc giấy báo có |
| Nhật ký thay đổi | Sổ gốc ghi mọi lần nhập, sửa và hủy |
| Báo cáo | Dashboard, tổng hợp chủ đầu tư, tổng hợp thầu phụ và sheet chi tiết từng đơn vị |

### 4.2. Quan hệ chính

```text
Dự án
├── 1 Chủ đầu tư
├── N Hạng mục
│   ├── N Giao dịch chủ đầu tư
│   └── N Giao dịch thầu phụ/khoán
└── N Thầu phụ/đơn vị nhận khoán
    └── Có thể có N hạng mục
```

Một đơn vị làm hai hạng mục phải được theo dõi thành hai dòng tổng hợp riêng. Tên hạng mục phải thống nhất giữa hai phía để so sánh doanh thu và chi phí.

## 5. Quy trình nghiệp vụ hiện tại

### 5.1. Khởi tạo hồ sơ dự án

1. Tạo một file cho mỗi dự án.
2. Nhập mã dự án, tên dự án/gói thầu và chủ đầu tư một lần.
3. Lưu file đúng thư mục dự án trên ổ chung.
4. Các giao dịch sau đó được nhập ở sheet `DATA`; người dùng không nhập trực tiếp vào các bảng tổng hợp hoặc nhật ký.

Điều kiện vận hành: file phải chạy được macro v10, mã dự án không được trống và mỗi mã dự án chỉ có một file Phòng Kế hoạch trong thư mục được tổng hợp.

### 5.2. Giao dịch với chủ đầu tư — Form B

Mỗi sự việc là một giao dịch riêng. Các sự việc được nêu trong file gồm ký hợp đồng, phụ lục, nghiệm thu, xuất hóa đơn và nhận tiền.

Trường nhập chính:

| Trường | Quy tắc |
| --- | --- |
| Ngày ghi sổ | Để trống thì lấy ngày hiện tại |
| Hạng mục | Bắt buộc; chọn từ danh mục dùng chung |
| Nội dung giao dịch/đợt | Mô tả sự kiện, ví dụ phụ lục hoặc nghiệm thu đợt 1 |
| Giá trị hợp đồng gốc | Chỉ nhập khi ký hợp đồng; là giá trị ban đầu |
| Giá trị hợp đồng điều chỉnh | Chỉ nhập khi có phụ lục; nhập giá trị mới của cả hạng mục, không nhập phần chênh lệch |
| Sản lượng thực hiện | Phần việc hoàn thành thêm trong đợt, chưa nhất thiết đã nghiệm thu |
| Giá trị nghiệm thu | Giá trị biên bản nghiệm thu của đợt |
| Giá trị phải xuất hóa đơn | Giá trị hóa đơn VAT xuất lần này |
| Giá trị được thanh toán | Tiền chủ đầu tư thực trả lần này |
| Giữ lại theo quy định | Phần bị giữ lại theo hợp đồng trong lần này |
| Ghi chú | Số hồ sơ, chứng từ hoặc thông tin bổ sung |

Kết quả được tổng hợp theo hạng mục ở `ChuDauTu` và lên `Dashboard`.

### 5.3. Giao dịch với thầu phụ và khoán nội bộ — Form A

Form A theo dõi chi phí dự án. Có ba loại đối tượng và cách tính khác nhau:

| Đối tượng | Có cộng vào tổng chi phí? | Ý nghĩa |
| --- | --- | --- |
| Thầu phụ công ty | Có | Đơn vị bên ngoài ký trực tiếp với công ty |
| Khoán nội bộ | Có | Phòng/đội/cá nhân nội bộ nhận khoán |
| Thầu phụ của phòng | Không cộng thêm | Đơn vị bên ngoài do phòng nhận khoán tự thuê; tiền đã nằm trong khoán của phòng |

Trường nhập chính:

| Trường | Quy tắc |
| --- | --- |
| Ngày ghi sổ | Để trống thì lấy ngày hiện tại |
| Thầu phụ/đơn vị nhận khoán | Bắt buộc; nên chọn từ danh bạ |
| Đối tượng giao dịch | Bắt buộc chọn một trong ba loại |
| Thuộc khoán của | Chỉ bắt buộc với thầu phụ của phòng; phải chọn phòng đã có giao dịch khoán nội bộ trong cùng dự án |
| Hạng mục | Bắt buộc ở giao dịch đầu tiên; có thể tự lấy nếu đơn vị chỉ có một hạng mục, nhưng phải chọn khi có nhiều hạng mục |
| Nội dung giao dịch/đợt | Ví dụ ký hợp đồng, nghiệm thu hoặc thanh toán đợt |
| Giá trị hợp đồng gốc | Nhập ở lần ký hợp đồng hoặc giao khoán |
| Giá trị hợp đồng điều chỉnh | Nhập giá trị mới nhất của toàn bộ hợp đồng sau phụ lục |
| Sản lượng thực hiện | Phần việc hoàn thành thêm trong đợt |
| Giá trị nghiệm thu | Giá trị biên bản nghiệm thu của đợt |
| Giá trị được thanh toán | Số tiền công ty thực trả lần này |
| Ghi chú | Số hợp đồng, ủy nhiệm chi hoặc thông tin bổ sung |

Ví dụ quy tắc phân cấp: giao khoán 500 triệu cho Phòng Thiết kế, phòng thuê ngoài 120 triệu. Tổng chi phí chỉ tính 500 triệu; 120 triệu hiện dưới dạng dòng con và khoán còn lại của phòng là 380 triệu.

### 5.4. Sửa và hủy giao dịch

Đây là quy tắc kiểm soát dữ liệu quan trọng:

1. Nhật ký là sổ gốc chỉ ghi thêm, không sửa hoặc xóa trực tiếp dòng cũ.
2. Sửa tạo một dòng mới trỏ về `ID GỐC`; dòng cũ vẫn giữ lại để truy vết.
3. Hủy tạo một dòng `XÓA` trỏ về `ID GỐC`.
4. Chỉ bản ghi mới nhất và chưa bị hủy có `HIỆU LỰC = 1` được đưa vào báo cáo.
5. Người dùng phải sửa/hủy qua lệnh hệ thống, không gõ trực tiếp vào nhật ký.

### 5.5. Báo cáo và cảnh báo

`Dashboard` có hai khối: với chủ đầu tư và với thầu phụ. Các bảng chi tiết gồm:

- `ChuDauTu`: mỗi hạng mục một dòng.
- `Thauphu`: mỗi cặp đơn vị × hạng mục một dòng; thầu phụ của phòng là dòng con.
- `TP_<tên đơn vị>`: chi tiết các giao dịch còn hiệu lực của từng đơn vị.

Các chỉ tiêu được thể hiện:

- Hợp đồng gốc và hợp đồng cập nhật.
- Sản lượng thực hiện.
- Giá trị nghiệm thu.
- Khối lượng chưa nghiệm thu = sản lượng thực hiện − giá trị nghiệm thu.
- Giá trị phải xuất hóa đơn.
- Giá trị được thanh toán.
- Giữ lại theo quy định.
- Còn phải thanh toán theo nghiệm thu = giá trị nghiệm thu − đã thanh toán.
- Còn phải thanh toán theo hợp đồng = hợp đồng cập nhật − đã thanh toán.
- Các tỷ lệ thực hiện/hợp đồng, thanh toán/hợp đồng và thanh toán/nghiệm thu.

Cảnh báo chính gồm thanh toán vượt nghiệm thu, chưa nghiệm thu, còn phải thanh toán, chỉ còn phần giữ lại, đã thanh toán đủ và khoán con vượt khoán mẹ.

### 5.6. Tài liệu và tổng hợp toàn công ty

File yêu cầu link tới tài liệu trên ổ chung, không phụ thuộc máy cá nhân. Link được gắn ở giao dịch, hồ sơ hợp đồng theo hạng mục và chứng từ thanh toán của từng đơn vị.

Mô hình hiện tại có ba loại file:

1. File Phòng Kế hoạch theo từng dự án.
2. File Phòng Kế toán theo từng dự án.
3. File Master quản trị chung, tự quét và tổng hợp theo lịch hằng đêm.

Việc đối chiếu giữa file Kế hoạch và Kế toán bằng mã dự án, cũng như cách xử lý khi số liệu khác nhau, chưa được workbook mô tả đủ và phải khảo sát thêm.

## 6. Quy tắc nghiệp vụ cần bảo toàn khi xây hệ thống mới

1. Một mã dự án phải thống nhất giữa các phòng.
2. Tên hạng mục dùng chung cho cả phía chủ đầu tư và phía thầu phụ.
3. Giá trị hợp đồng cập nhật là giá trị mới nhất, không cộng dồn các phụ lục.
4. Sản lượng thực hiện khác giá trị nghiệm thu.
5. Thầu phụ của phòng nằm trong khoán của phòng và không được cộng trùng.
6. Báo cáo chỉ tính các giao dịch còn hiệu lực.
7. Sửa/hủy phải giữ lịch sử và người/thời điểm thao tác.
8. Tài liệu phải nằm ở nơi người có quyền có thể mở được.
9. Giao dịch phải được theo dõi riêng theo từng hạng mục khi một đơn vị làm nhiều hạng mục.
10. Dữ liệu nhập một lần ở form, bảng tổng hợp tự sinh từ sổ gốc.

## 7. Phạm vi nên đưa vào module `tadic_khkd`

Sau khi nghiệp vụ được xác nhận, module KHKD có thể bao gồm:

- Hồ sơ dự án và hạng mục KHKD.
- Chủ đầu tư và hợp đồng theo hạng mục.
- Giao dịch Form B.
- Danh bạ thầu phụ/đơn vị nhận khoán.
- Giao dịch Form A và quan hệ khoán mẹ/con.
- Nghiệm thu, thanh toán, giữ lại và các chỉ tiêu tổng hợp.
- Tài liệu liên quan.
- Nhật ký bất biến và luồng sửa/hủy.
- Dashboard và cảnh báo KHKD.

Không nên đưa logic đặc thù của KHKD vào `tadic_core`. `tadic_core` chỉ giữ đối tượng thật sự dùng chung như dự án, phòng ban, người dùng, tài liệu, nhật ký nền và phân quyền cơ bản.

## 8. Các điểm bắt buộc phải hỏi Phòng Kế hoạch

1. Workbook v10.5 đang được dùng toàn bộ hay chỉ dùng một phần?
2. Ai nhập Form A, ai nhập Form B, ai kiểm tra và ai duyệt?
3. Có cần khóa giao dịch sau khi duyệt không? Ai được mở lại?
4. Có những loại giao dịch nào ngoài các loại đã nêu trong file?
5. Quy tắc xác định sản lượng thực hiện là gì và ai chịu trách nhiệm xác nhận?
6. Giá trị nghiệm thu, hóa đơn và thanh toán lấy từ nguồn nào?
7. Phòng Kế hoạch có nhập tiền/chứng từ hay chờ Phòng Kế toán đối chiếu?
8. Quy tắc giữ lại, tạm ứng và thanh toán vượt nghiệm thu có ngoại lệ nào không?
9. Một dự án có thể có nhiều chủ đầu tư, liên danh hoặc nhiều hợp đồng không?
10. Một hạng mục có thể đổi tên không? Nếu đổi, có giữ lịch sử tên cũ không?
11. Thầu phụ của phòng có cần theo dõi hợp đồng và chứng từ riêng không?
12. Ai được xem dữ liệu từng dự án và dữ liệu của phòng khác?
13. Báo cáo nào thực sự được lãnh đạo sử dụng hàng tuần/tháng?
14. File Master đang chạy bằng cơ chế nào và ai xử lý khi tổng hợp lỗi?
15. Có cần nhập dữ liệu lịch sử không? Nếu có, lấy từ năm nào?
16. Dữ liệu và tài liệu được phép lưu ở Odoo hay bắt buộc giữ trên NAS?

## 9. Kết luận

Có thể phân tích nghiệp vụ KHKD khá chính xác từ workbook này. Phần chắc chắn nhất là **cấu trúc dữ liệu, hai luồng giao dịch, quy tắc tính và nhật ký**. Phần chưa thể kết luận chỉ bằng Excel là **quy trình tổ chức thực tế, quyền phê duyệt, ngoại lệ và mức độ sử dụng**.

Do đó, tài liệu này đủ để dựng khung hệ thống và đề xuất techstack trong tháng 1, nhưng chưa đủ để tự động hóa chính thức. Chỉ chuyển sang thiết kế model và code khi các câu hỏi ở mục 8 được người phụ trách xác nhận.
