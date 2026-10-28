# Thiết kế UI UX dashboard quản trị Tấn Phát

Ngày thiết kế: 27/10/2026. Áp dụng frontend-design và guideline frontend trong skills/odoo-web-guidelines của repo. Đây là đặc tả để triển khai sau; không phải giao diện đã được xây hoặc kiểm thử.

## 1. Hướng thiết kế

Giao diện dành cho lãnh đạo công ty tư vấn khảo sát và thiết kế hạ tầng: người đọc phải phân biệt được **giá trị công việc được nghiệm thu** và **tiền đã thu/chi** trong vài giây. Điểm nhận diện chính là hai luồng CĐT và giao khoán được trình bày cùng hệ đơn vị, cùng nhãn, cùng trục so sánh. Dùng bảng có phân cấp để diễn đạt khoán mẹ/con; không dùng trang trí thay cho thông tin tài chính.

Odoo giữ navbar và vùng thông báo của nó. Dashboard có sidebar nằm bên trong action content, không tạo navbar cạnh tranh với Odoo. Khung chính nền sáng, đường kẻ mảnh, vùng số liệu thoáng. Không dùng ảnh hero, gradient, hiệu ứng cuộn hoặc bóng đổ trên mọi ô.

### Token thiết kế đề xuất

| Token | Giá trị | Vai trò |
| --- | --- | --- |
| ink | #17324D | Tiêu đề, sidebar, luồng CĐT |
| canvas | #F3F6F8 | Nền vùng content |
| surface | #FFFFFF | Bảng, KPI và panel |
| grid | #D6DFE6 | Đường phân vùng và lưới chart |
| contract | #2F6A76 | Luồng thầu phụ/giao khoán |
| attention | #8A5700 | Cần giải thích/tạm ứng/vượt nghiệm thu |

Lỗi kỹ thuật dùng màu danger của theme Odoo, thành công dùng success của theme. Tất cả trạng thái đều có chữ và icon có nhãn; không dùng màu đơn độc. Kiểm tra contrast tối thiểu 4,5:1 với chữ thường và 3:1 với vùng điều khiển/chữ lớn trước nghiệm thu.

Font: kế thừa font sans-serif đã có trong Web Client; không tải Google Fonts/CDN. Typography tạo phân cấp bằng kích thước và độ đậm: tiêu đề 24/32 px, section 18/26, số KPI 28/34, thân/bảng 14/20, ghi chú 12/18. Dùng tabular-nums cho tiền, không dùng monospace cho nhãn. Mọi số căn phải, tên căn trái.

Spacing theo bội 4 px: content padding 24, gap 16–24; đường biên 1 px; radius 6 px ở panel và 4 px ở control. KPI trọng yếu được nhấn bằng độ lớn, không tăng màu trang trí. Các token được scope dưới .o_tanphat_dashboard; không ghi vào :root hoặc ghi đè Bootstrap global.

## 2. Khung chung và responsive

| Viewport | Sidebar | KPI | Biểu đồ/bảng |
| --- | --- | --- | --- |
| >=1440 px | 224 px, luôn hiện | Hai cột theo hai phía; mỗi cột 2 thẻ/row | Chart 2 cột; bảng đủ cột chính |
| 1024–1439 px | 184 px hoặc thu gọn 64 px | 2–4 thẻ/row tùy nhãn | Chart 2 cột; bảng cuộn ngang trong panel |
| 768–1023 px | Drawer mở bằng nút có nhãn | 2 thẻ/row | Chart 1 cột; ẩn cột phụ qua bộ chọn cột |
| <768 px | Không phải mục tiêu nghiệm thu chính, vẫn không vỡ layout | 1–2 thẻ/row | Nội dung xếp dọc, bảng cuộn ngang có dấu chỉ dẫn |

Tên dự án dài tối đa hai dòng ở header; có nút mở đủ tên. Tiền không được cắt bằng dấu ba chấm. Nếu dùng đơn vị triệu/tỷ ở chart thì ghi rõ ở axis và tooltip hiện VNĐ đầy đủ. Màn hình 200% zoom không che điều khiển hoặc làm bảng tràn ra ngoài content.

```text
[Navbar Odoo: Apps / Quản trị Tấn Phát / User]
+---------------------+-----------------------------------------------+
| Quản trị dự án      | Mã và tên dự án              [Chọn dự án v] |
| Tổng quan           | Chủ đầu tư              Snapshot: ...       |
| Chủ đầu tư          | [Nguồn dữ liệu mẫu]        [Làm mới]         |
| Thầu phụ/giao khoán |-----------------------------------------------|
| Chi tiết dự án      | Breadcrumb và bộ lọc theo trang             |
|                     | Content                                     |
+---------------------+-----------------------------------------------+
```

Sidebar dùng tên trang đầy đủ, active có dấu chỉ thị và aria-current. “Chi tiết dự án” luôn có thể mở; “Chi tiết đơn vị” xuất hiện trong breadcrumb khi drill-down. Chọn dự án mới xóa contractorId/itemId không còn thuộc dự án đó, đưa route về trang tương ứng hợp lệ.

## 3. Wireframe trang Tổng quan

```text
Tổng quan dự án                           [Hạng mục: Tất cả*]
Lũy kế đến snapshot ...                    [Xem cách tính]

+--------------------------------+--------------------------------+
| Với chủ đầu tư                 | Với thầu phụ và khoán cấp 1     |
| [HĐ cập nhật] [Nghiệm thu]      | [HĐ cập nhật] [Nghiệm thu]      |
| [Đã nhận tiền] [Còn theo NT]    | [Đã trả tiền] [Còn theo NT]     |
| % tiền/HĐ      % tiền/NT       | % tiền/HĐ      % tiền/NT        |
+--------------------------------+--------------------------------+
| Cần chú ý: tiền về vượt NT...   | Khoán cấp 2: xem riêng ...      |
+--------------------------------+--------------------------------+
| HĐ và NT theo hai phía         | NT và thanh toán theo hai phía |
| Grouped bar, cùng đơn vị VNĐ   | Grouped bar; có bảng thay thế  |
+--------------------------------+--------------------------------+
| Nghiệm thu theo hạng mục       | Giao dịch theo tháng ghi sổ    |
| Horizontal bar                | Dữ liệu hiệu lực, nếu có ngày |
+--------------------------------+--------------------------------+
| Cảnh báo theo hạng mục [Xem]                                    |
| Bảng số phụ: HĐ gốc / sản lượng / hóa đơn / giữ lại / số lượng   |
+----------------------------------------------------------------+
```

*Bộ lọc hạng mục xuyên hai phía chỉ bật sau khi có crosswalk được BA xác nhận. Hiện mẫu có “Khảo sát” ở CĐT và “Khảo sát địa hình” ở thầu phụ, nên không ghép tự động. Trước đó, tổng quan chỉ lọc dự án; chart hạng mục hiển thị hai nhóm riêng có nhãn nguồn.

Tám KPI chính trình bày số snapshot đã đối chiếu. Số dư âm giữ dấu âm và chú thích “Đã nhận/trả vượt nghiệm thu; có thể gồm tạm ứng hoặc NT chưa cập nhật”. Số này không được gắn nhãn “nợ xấu”. KPI công nợ ghi rõ “theo nghiệm thu”; công nợ theo hợp đồng nằm ở chi tiết thầu phụ.

Tỷ lệ không dùng gauge giả hoặc ép trần 100%. Nếu 116,8% thì hiển thị đủ 116,8% và giải thích. Không có dữ liệu đủ để vẽ chart thì thay bằng thông báo và bảng nguồn có sẵn.

## 4. Wireframe trang Chủ đầu tư

```text
Chủ đầu tư > Dự án ...
[Hạng mục v] [Tìm hạng mục ...] [Cột hiển thị v] [Xóa lọc]

[HĐ cập nhật] [Nghiệm thu] [Đã thanh toán] [Còn sau giữ lại]
+----------------------------------------------------------------+
| HĐ cập nhật và NT theo hạng mục; bấm thanh để xem giao dịch      |
+----------------------------------------------------------------+
| Hạng mục | HĐ cập nhật | NT | Đã thu | Giữ lại | Còn NT | ...    |
| ...      | ...        |... | ...    | ...     | ...    | [Xem]  |
| Tổng phạm vi lọc, không chỉ trang hiện tại                      |
+----------------------------------------------------------------+
[Pager Odoo]                    [Số dòng / tổng dòng]

Panel chi tiết bên phải hoặc dialog lớn trên tablet:
[Tên hạng mục] [Đóng]
KPI + nguồn + định nghĩa + cảnh báo
[Giao dịch hiệu lực] [Lịch sử] [Chứng từ]
Ngày | Nội dung | HĐ/Phụ lục | NT | Hóa đơn | Tiền | ID
```

Cột ưu tiên luôn thấy: hạng mục, HĐ cập nhật, NT, đã thu, còn NT và trạng thái. Các cột HĐ gốc, sản lượng, chưa NT, hóa đơn, giữ lại và tỷ lệ bật qua bộ chọn cột nhưng nằm trong cùng dataset. Sort số dùng giá trị số, không sort chuỗi tiền đã format.

## 5. Wireframe trang Thầu phụ và giao khoán

```text
Thầu phụ và giao khoán
[Đơn vị v] [Đối tượng v] [Hạng mục v] [Cấp v] [Tìm ...] [Xóa lọc]

[HĐ cấp 1] [NT cấp 1] [Đã trả cấp 1] [Còn theo NT cấp 1]
Trong đó, cấp 2: ... (thông tin riêng, không cộng vào cấp 1)
+----------------------------------------------------------------+
| Đơn vị / Hạng mục | Loại | Tính tổng | HĐ | NT | TT | Nợ | Xem  |
| v Phòng A        | Khoán nội bộ | Có | ... | ... | ... | ...    |
|   1.1 Đơn vị B   | Của phòng    | Không | ... | ... | ...       |
| 2. Đơn vị C      | Cty          | Có | ... | ... | ... | ...    |
+----------------------------------------------------------------+
| Khoán của phòng được chọn: Được giao / Ký cấp 2 / Còn lại       |
| Phạm vi cấp phòng; không lặp tổng khoản này trên từng hạng mục |
+----------------------------------------------------------------+
```

Dòng con thụt vào, có nhãn “Cấp 2”, không chỉ dùng chữ nghiêng/màu xám. Parent được giữ làm ngữ cảnh khi lọc ra con; parent ngữ cảnh không bị cộng thêm vào kết quả lọc. Khi chỉ chọn cấp 2, khối tổng ghi “Cấp 2, không cộng tổng công ty”; KPI cấp 1 vẫn là 0 trong **phạm vi chọn**, có nhãn rõ hoặc được thay bằng khối cấp 2, không đổi thuật toán tổng để cho số khác 0.

Không vẽ stacked bar cộng cha + con. Biểu đồ khoán nếu cần có hai thanh “Khoán phòng” và “Phòng ký cấp 2” để so sánh, không chồng tổng.

## 6. Wireframe trang Chi tiết

```text
Tổng quan / Dự án / Đơn vị ...                 [Quay lại]
Tên, mã danh bạ nếu có, loại và khoán mẹ
[HĐ cập nhật] [Nghiệm thu] [Đã thanh toán] [Còn theo NT]

[Hạng mục] [Giao dịch] [Lịch sử] [Chứng từ]
+--------------------------------------+-------------------------+
| Bảng hạng mục / giao dịch             | NT và thanh toán        |
| Ngày | Nội dung | NT | TT | ID        | theo tháng ghi sổ       |
| ...                                  | hoặc empty state        |
+--------------------------------------+-------------------------+
Lọc trong tab giao dịch: [Ngày từ/đến] [Hiệu lực/Lịch sử] [Tìm]
Phạm vi tab: ... ; KPI bên trên là lũy kế snapshot, không đổi bởi
bộ lọc lịch sử trong tab (nhãn được hiển thị ngay cạnh control).
```

Chi tiết dự án dùng cùng layout nhưng không có đơn vị/khoán mẹ; có bảng hai phía và danh sách đơn vị. Chứng từ chỉ hiện khi có URL được phép. Mẫu hiện tại không có link chứng từ tài chính ngoài workbook; phải hiển thị empty state, không tạo link demo giả.

## 7. Quy ước tương tác và bộ lọc

| Thao tác | Tác động đã chốt |
| --- | --- |
| Chọn dự án | Nạp một snapshot thống nhất; hủy kết quả request cũ; xóa lựa chọn con không hợp lệ |
| Lọc hạng mục/đơn vị/loại/cấp | Repository tính lại KPI, chart, cảnh báo và bảng trên cùng tập bản ghi; caption nêu phạm vi |
| Tìm kiếm bảng | Chỉ thu hẹp dòng hiển thị; ghi “Tìm trong N dòng”, tổng KPI giữ phạm vi bộ lọc; không gọi là filter tài chính |
| Sort/phân trang | Không thay tổng KPI; tổng footer bao phủ toàn phạm vi lọc |
| Lọc ngày trong giao dịch | Chỉ tab giao dịch và chart trong tab; KPI snapshot được ghi rõ không phải số dư tại ngày |
| Bấm KPI/biểu đồ | Mở đúng danh sách góp vào KPI, mang theo projectId/itemId/side và cùng snapshotId |
| Quay lại | Khôi phục bộ lọc/sort/trang và scroll khi vẫn cùng snapshot |
| Làm mới | Tạo request mới; giữ view cũ kèm trạng thái cập nhật; không gộp hai snapshot |

Không có chức năng xem số dư lịch sử “tại ngày” trong đợt đầu vì ngày ghi sổ/sửa chưa chứng minh được ngày hiệu lực nghiệp vụ. Không dùng chỉ bộ lọc startDate để cắt mất giao dịch HĐ gốc rồi tính HĐ hiện tại.

## 8. Nội dung trạng thái

| Trạng thái | Nội dung hiển thị | Hành động |
| --- | --- | --- |
| Loading | Skeleton khung KPI/bảng; aria-busy | Không lặp thông báo toast |
| Không có dự án | “Chưa có dự án trong nguồn dữ liệu này.” | Chọn nguồn khác chỉ khi app đã có tính năng đó |
| Không có giao dịch | “Dự án chưa có giao dịch được ghi nhận.” | Xem thông tin dự án; không hiện chart 0 giả |
| Không có kết quả lọc | “Không có dòng phù hợp bộ lọc.” | Xóa lọc |
| Dữ liệu thiếu | “Chưa có sản lượng được khai báo”, “Chưa có nghiệm thu để tính tỷ lệ” | Tooltip nguồn thiếu |
| Lỗi tải | “Không tải được dữ liệu dự án. Thử lại.” | Nút Thử lại, giữ projectId |
| Dữ liệu cũ | “Đang xem snapshot lúc ...” | Làm mới |
| Mẫu | “Dữ liệu mẫu đã ẩn danh và biến đổi để minh họa” | Luôn có nhãn trong header |

Null dùng dấu “—” cùng nội dung giải thích truy cập được. Số 0 hợp lệ hiển thị 0 ₫. Âm hiển thị dấu −, không đổi thành 0. Cảnh báo nghiệp vụ không dùng thông báo “có lỗi” của ứng dụng.

## 9. Khả năng tiếp cận và tiêu chí thiết kế

- Mọi filter có label, mọi icon-only button có accessible name; focus thấy rõ.
- Tab/Enter/Escape mở và đóng drill-down; đóng panel trả focus về dòng/KPI đã kích hoạt.
- Bảng có header, aria-sort và pager; hierarchy có nút expand với aria-expanded. Tránh tự triển khai grid keyboard phức tạp nếu HTML table đáp ứng.
- Canvas chart có mô tả và bảng số liệu thay thế. Người dùng không cần hover để biết số chính.
- Tôn trọng prefers-reduced-motion; mặc định animation chart ngắn hoặc tắt khi đổi dữ liệu nhiều.
- KPI không có link khi không có drill-down hợp lệ. Không đặt thêm nút sửa/duyệt/nhập trong bất kỳ wireframe nào.

Trước khi viết component, review token/wireframe với số liệu mẫu dài nhất: tên dự án hai dòng, tên hạng mục dài, số VNĐ lớn, tỷ lệ trên 100%, số âm và null. Thiết kế đã giảm card đồng dạng: chỉ tám KPI chính, số phụ tập trung ở bảng, phần khoán dùng hierarchy có nghĩa thay vì trang trí. Đây là điều chỉnh từ review frontend-design để bố cục phục vụ đúng cách lãnh đạo đọc dữ liệu.
