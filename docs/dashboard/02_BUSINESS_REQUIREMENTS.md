# Yêu cầu nghiệp vụ Tan Phat Executive Dashboard

## 1. Phạm vi và người dùng

Dashboard là màn hình **đọc số liệu quản trị** chạy trong Odoo. Người dùng chọn dự án rồi đọc tình hình hợp đồng, nghiệm thu, thanh toán và giao khoán. Màn hình không tạo giao dịch, không sửa sổ nhật ký và không thay macro Excel.

| Người dùng | Câu hỏi cần trả lời | Quyền trong giai đoạn frontend mẫu |
| --- | --- | --- |
| Ban Tổng Giám đốc | Dự án nào đang có giá trị, nghiệm thu, tiền về và công nợ đáng chú ý? | Xem toàn bộ fixture; tương lai lọc theo quyền công ty |
| Giám đốc dự án | Hạng mục nào chưa nghiệm thu, đã trả hoặc còn nợ? | Xem dự án được giao; drill-down sau khi có repository thật |
| Ban Kinh doanh/Kế hoạch | Hợp đồng CĐT và thầu phụ đang lệch ở đâu? | Xem chi tiết hạng mục, đối tác và giao dịch |
| Quản trị tài chính | Dòng tiền đã trả/thu, giữ lại và khoản cấp 2 có được tính đúng không? | Xem số liệu và cảnh báo; không duyệt chi |
| Người quản trị Odoo | Module có cài được và tải nhanh không? | Cài/cập nhật module; không chỉnh dữ liệu từ dashboard |

## 2. Trang bắt buộc

### 2.1 Executive Overview

Màn hình đầu tiên sau khi mở menu. Header hiển thị mã dự án, tên, CĐT và thời điểm snapshot. Khối “Với chủ đầu tư” và “Với thầu phụ/giao khoán” đặt cạnh nhau để lãnh đạo đọc cùng thang đo.

KPI tối thiểu: giá trị hợp đồng gốc/cập nhật, sản lượng, nghiệm thu, đã thanh toán, công nợ phải thu/phải trả, tỷ lệ thanh toán/hợp đồng và tỷ lệ thanh toán/nghiệm thu. Có trạng thái chưa có dữ liệu và tooltip giải thích mẫu số.

Biểu đồ: hợp đồng so với nghiệm thu theo hai phía; thanh toán so với nghiệm thu; phân bổ nghiệm thu theo hạng mục; timeline chỉ bật khi giao dịch có ngày hợp lệ. Cảnh báo đặt cạnh KPI liên quan, không biến cảnh báo thành điểm số.

### 2.2 Chủ đầu tư

Bảng mỗi dòng là một hạng mục. Cột bắt buộc: hạng mục, HĐ gốc, HĐ cập nhật, sản lượng, nghiệm thu, chưa nghiệm thu, phải xuất hóa đơn, đã thanh toán, giữ lại, còn phải thanh toán, còn phải thanh toán sau giữ lại, ba tỷ lệ và cảnh báo. Chọn dòng mở panel chi tiết giao dịch và link chứng từ nếu có.

### 2.3 Thầu phụ và giao khoán

Bảng mỗi cặp đơn vị × hạng mục là một dòng. Bộ lọc theo đơn vị, đối tượng giao dịch, cấp khoán và hạng mục. Dòng cấp 1 (thầu phụ công ty hoặc khoán nội bộ) được tính vào tổng. Dòng cấp 2 (thầu phụ của phòng) hiển thị dưới dòng cha, có thể mở chi tiết nhưng không cộng lại vào tổng cấp công ty. Khối “thầu phụ do phòng ký” được trình bày riêng.

### 2.4 Chi tiết dự án/đơn vị

Mở từ một dự án hoặc đơn vị: thông tin định danh, KPI liên quan, hạng mục, giao dịch hiệu lực, chứng từ và lịch sử sửa/hủy. Không tạo KPI mới khi nguồn không có; trường thiếu phải hiện “Chưa có dữ liệu”.

## 3. Chức năng dùng chung

- Chọn dự án; một dashboard có thể mở nhiều dự án sau này nhưng chỉ một projectId trong một view.
- Lọc hạng mục, đơn vị, đối tượng giao dịch, cấp và khoảng ngày ghi sổ khi dữ liệu hỗ trợ.
- Tìm kiếm không dấu cho danh mục; không dùng tên hiển thị làm ID.
- Sắp xếp, phân trang và mở drill-down bằng bàn phím.
- Làm mới snapshot; hiển thị thời điểm và nguồn dữ liệu.
- Loading skeleton, empty state, lỗi có thể thử lại và trạng thái dữ liệu thiếu.
- Định dạng VNĐ không làm tròn sai dữ liệu; phần trăm giữ một chữ số thập phân ở bảng và số nguyên ở KPI nếu không làm mất thông tin.
- Link chứng từ chỉ là liên kết đã được repository cho phép; không đọc file NAS từ browser.
- Responsive desktop trước, laptop/tablet sau; mobile chỉ là giai đoạn roadmap.

## 4. KPI và định nghĩa bất biến

| KPI | Công thức/ý nghĩa | Nguồn Excel hiện tại | Hiển thị |
| --- | --- | --- | --- |
| HĐ gốc | Tổng GT hợp đồng gốc của bản ghi hiệu lực | ChuDauTu C; Thauphu H; nhật ký E/F | tiền |
| HĐ cập nhật | Phụ lục mới nhất; chưa có phụ lục thì tổng HĐ gốc | ChuDauTu D; Thauphu I; NHAT_KY_TC P/NHAT_KY O | tiền |
| Sản lượng thực hiện | Phần việc làm xong theo đánh giá PKH, chưa cần NT | ChuDauTu E; Thauphu J; nhật ký R/Q | tiền; null nếu chưa khai |
| GT nghiệm thu | Phần có biên bản NT đã ký | ChuDauTu F; Thauphu K; nhật ký G/H | tiền |
| Chưa nghiệm thu | Sản lượng − nghiệm thu; Excel để trống khi sản lượng=0; xem quy tắc availability trong contract | ChuDauTu G; Thauphu L | tiền hoặc unavailable |
| GT phải xuất hóa đơn | Tổng GT hóa đơn đã ghi nhận ở giao dịch CĐT | ChuDauTu H; NHAT_KY_TC H | tiền, giữ nhãn nghiệp vụ |
| Đã thanh toán | CĐT thực trả hoặc Tấn Phát thực trả thầu phụ | ChuDauTu I; Thauphu M; nhật ký I | tiền |
| Giữ lại | Phần CĐT giữ lại theo hợp đồng | ChuDauTu J; NHAT_KY_TC J | tiền |
| Công nợ theo NT | Nghiệm thu − đã thanh toán | ChuDauTu K; Thauphu O | tiền có dấu |
| Công nợ sau giữ lại | Công nợ theo NT − giữ lại phía CĐT | ChuDauTu L | tiền có dấu |
| Công nợ theo HĐ | HĐ cập nhật − đã thanh toán thầu phụ | Thauphu N | tiền có dấu |
| % sản lượng/HĐ | Sản lượng / HĐ cập nhật | ChuDauTu M; Thauphu derived | %; trống khi mẫu số 0 hoặc sản lượng thiếu |
| % thanh toán/HĐ | Đã thanh toán / HĐ cập nhật | ChuDauTu N; Thauphu derived | %; trống khi mẫu số 0 |
| % thanh toán/NT | Đã thanh toán / nghiệm thu | ChuDauTu O; Thauphu derived | %; trống khi nghiệm thu 0 |
| Cấp khoán | 1 = công ty/khoán nội bộ; 2 = thầu phụ của phòng | Thauphu P | badge |

Số âm ở công nợ có nghĩa tiền đã trả/về vượt số NT đang có trong sổ. Có thể là tạm ứng hoặc NT chưa nhập đủ. Dashboard phải nói rõ “đã thanh toán vượt nghiệm thu theo dữ liệu hiện có”, không gọi là sai phạm.

## 5. Quy tắc nghiệp vụ bắt buộc

1. Chỉ bản ghi hiệu lực mới được cộng. Một stream cùng ID GỐC chọn bản có ID lớn nhất; nếu bản mới nhất có THAO TÁC XÓA thì toàn stream không hiệu lực.
2. Phụ lục nhập giá trị mới của cả hạng mục/hợp đồng, không nhập phần chênh lệch.
3. Một giao dịch chỉ chứa phát sinh của lần đó; không nhập số lũy kế.
4. Tổng cấp công ty chỉ gồm cấp 1. Cấp 2 hiển thị riêng và không được cộng lần nữa vào dòng cha.
5. Thầu phụ của phòng chỉ hợp lệ khi có khoán nội bộ mẹ trong cùng dự án; nếu cấp 2 vượt khoán mẹ, phát cảnh báo riêng.
6. Hạng mục phải dùng danh mục chung; nội dung đợt/giai đoạn nằm ở mô tả giao dịch.
7. Không xem chênh lệch HĐ CĐT và HĐ giao khoán là lợi nhuận thực tế. Giai đoạn này không có KPI biên lợi nhuận.
8. Bằng 0 và thiếu dữ liệu khác nhau. Zero sản lượng do macro có thể chưa xác định là số đã khai, phải giữ raw0 + ambiguous_zero; chưa NT không được suy ra là0. Mẫu số0 trả `null`/unavailable; không biến lỗi thành0.
9. Link chứng từ không biến thành dữ liệu giao dịch. Hiển thị link chỉ khi repository đánh dấu hợp lệ.
10. Dữ liệu mẫu phải gắn `fixture: true`; mọi số liệu thật chỉ đi qua repository riêng trong tương lai.

## 6. Ngoài phạm vi

Form nhập, sửa/hủy, VBA, quy trình duyệt, kế toán đầy đủ, đồng bộ NAS tự động, AI assistant, mobile offline, mô hình ORM nghiệp vụ mới, phân quyền chi tiết và thay thế Excel đều để roadmap. Dashboard chỉ chuẩn bị interface để cắm các phần đó sau.

## 7. Tiêu chí nghiệm thu nghiệp vụ

- Tổng KPI CĐT và thầu phụ khớp một bộ fixture đã được đối chiếu với Excel theo từng hạng mục.
- Bản sửa/hủy không bị cộng cùng bản cũ.
- Cấp 2 hiển thị được nhưng tổng cấp 1 không thay đổi.
- Chênh thanh toán > nghiệm thu hiển thị cảnh báo kèm giải thích tạm ứng/thiếu NT.
- Không có dữ liệu dự án, hạng mục hoặc giao dịch thì dashboard hướng dẫn người dùng thay vì hiện số 0 giả.
- Bộ lọc tài chính thay đổi đồng thời KPI, bảng, biểu đồ và cảnh báo theo cùng tập bản ghi. Search/sort/page chỉ tác động bảng; ngày ghi sổ chỉ ở tab giao dịch với nhãn scope rõ, không đổi KPI snapshot.
- Mỗi KPI hiển thị nguồn/định nghĩa trong tooltip hoặc panel “Cách tính”.
