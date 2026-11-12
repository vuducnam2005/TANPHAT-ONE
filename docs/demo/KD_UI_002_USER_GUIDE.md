# KD-UI-002 — Hướng dẫn thao tác sidebar và Tổng quan KH-KD

Áp dụng trên dev `http://127.0.0.1:18069/odoo`, app **Kế hoạch Kinh doanh**, từ ngày 06/11/2026. Dữ liệu là bộ tổng hợp (254 hồ sơ seed + 14 hồ sơ UI). Đây là hướng dẫn thao tác, không phải xác nhận nghiệp vụ hay pilot.

Ai thấy gì do quyền backend quyết định. Nút, nhóm menu hoặc biểu đồ không hiện là do tài khoản không có quyền với nguồn đó, không phải lỗi.

## 1. Sidebar

| Việc | Cách làm |
| --- | --- |
| Mở/đóng nhóm | Bấm tên nhóm hoặc dùng Tab rồi Enter/Space. Mũi tên xoay khi nhóm mở. Bấm nhóm không chuyển trang. |
| Mở chức năng | Bấm mục con. Mục đang mở có nền đậm và vạch xanh bên trái. Ctrl/Cmd-click mở tab mới. |
| Tìm chức năng | Gõ vào "Tìm chức năng…", có thể gõ không dấu (vd. `nghiem thu`). Nhóm chứa kết quả tự mở. Escape xóa ô tìm. |
| Thu gọn | Nút ở góc trên sidebar. Thanh còn lại các biểu tượng, rê chuột để xem tên. Trạng thái được nhớ sau khi tải lại trang. |
| Tùy chọn hiển thị | Bánh răng cuối sidebar hoặc nút ⚙ trên Tổng quan: mật độ Thoáng/Gọn, Giảm chuyển động, thu gọn sidebar trên màn hình rộng, Khôi phục mặc định. Chỉ lưu trên trình duyệt này, không đổi dữ liệu hay quyền. |
| Màn hình 768–1199px | Sidebar dạng thanh biểu tượng. Bấm nút mở rộng để hiện dạng ngăn kéo. |
| Điện thoại (<768px) | Bấm **Menu KH-KD** dưới thanh trên cùng. Đóng bằng X, Escape, bấm ra ngoài hoặc sau khi chọn chức năng. |

Rời KH-KD (về Home hoặc app khác) thì sidebar biến mất, giao diện Odoo trở lại như cũ.

## 2. Tổng quan

### Thanh công cụ

- **Tạo hồ sơ ▾**: chỉ liệt kê loại bạn được tạo. Nếu đang lọc một dự án, form mới điền sẵn dự án đó. Đóng form mà không lưu thì không tạo hồ sơ.
- **Làm mới**: tải lại số liệu. Nếu lỗi, số cũ được giữ, có nhãn "Dữ liệu có thể đã cũ" và nút "Thử lại".
- **Xóa bộ lọc**: chỉ bật khi đang có bộ lọc.
- **Xem dữ liệu ▾**: mở danh sách native của dự án, cơ hội, hợp đồng, phiên bản, công việc. Muốn xuất thì dùng chức năng xuất native ở danh sách đó.
- **⚙**: tùy chọn hiển thị.

### Bộ lọc

Dự án, người phụ trách, từ ngày, đến ngày. Mỗi nguồn lọc theo ngày riêng: hồ sơ theo ngày hồ sơ, kế hoạch theo đầu kỳ, chứng chỉ theo ngày hết hạn, công việc theo hạn, cơ hội theo hạn hồ sơ.

### Ô số (KPI)

| Ô | Bấm vào |
| --- | --- |
| Chờ tôi rà soát | Chuyển xuống "Việc của tôi", tab Chờ tôi rà soát. |
| Trả lại cho tôi | Chuyển xuống tab Trả lại cho tôi. |
| Quá hạn / Còn hạn của tôi | Chuyển xuống tab Sắp đến hạn / quá hạn. |
| Dự án quản lý, Hợp đồng, Phiên bản hợp đồng | Mở danh sách nguồn. Ô bị mờ nếu bạn không đọc được nguồn đó. |

### Biểu đồ

- **G01 Hồ sơ đang xử lý theo loại**: mỗi loại có 3 đoạn rời nhau là Nháp (xám), Đang rà soát (xanh), Trả lại (đỏ). Bấm một đoạn mở đúng danh sách hồ sơ đó. Bấm tên loại mở toàn bộ loại.
- **G02 Công việc theo dự án**: Hoàn thành / Quá hạn / Đang mở. Mỗi việc chỉ nằm trong một nhóm. Mặc định hiện 8 dự án nhiều việc nhất, có nút xem tất cả.
- **G03 Cơ hội và hồ sơ thầu**: theo hình thức (đấu thầu, chỉ định) và bước chuẩn bị nội bộ. Đây không phải kết quả trúng thầu.
- **G04 Kế hoạch sản lượng** (tab): chọn Tháng/Quý/Năm. Chỉ hiện giá trị khi mục tiêu đã xác nhận và nguồn so sánh được. Ngược lại hiện nhãn "Chưa đủ căn cứ so sánh" / "Chưa có dữ liệu nguồn", không vẽ số 0 giả. Người không có quyền tài chính chỉ thấy số kế hoạch bị ẩn.
- **G05 Hạn năng lực/chứng chỉ** (tab): Đã hết hạn / Trong 30 ngày / Sau 30 ngày. Đây là ngưỡng minh họa, không phải xác minh pháp lý.

Số trên mỗi đoạn bằng đúng số dòng của danh sách mở ra khi bấm. Đã đối chiếu từng đoạn cho 4 vai trò; xem [acceptance](KD_UI_002_ACCEPTANCE.md).

### Bảng điều hành dự án

- Ô tìm theo mã, tên, khách hàng.
- Bấm tiêu đề cột để sắp xếp tăng/giảm.
- Nút 👁 để chọn cột hiển thị.
- Phân trang ở cuối bảng.
- **Thao tác ▾** ở từng dòng: Mở hồ sơ dự án, Cơ hội / hồ sơ thầu, Hợp đồng, Kế hoạch / WBS, Giao khoán, Sản lượng, Nghiệm thu nội bộ, Đề nghị thanh toán, Kế hoạch định kỳ, Nghĩa vụ / hồ sơ thiếu. Mục nào bạn không đọc được thì không hiện.

### Việc của tôi

Ba tab: Chờ tôi rà soát, Trả lại cho tôi, Sắp đến hạn / quá hạn. Số trên tab là tổng thật, không phải số dòng trên trang. Bấm một dòng mở đúng hồ sơ. Trên màn hình rộng ≥1760px khối này nằm cạnh bảng dự án; màn hình nhỏ hơn thì nằm dưới.

### Bảng nguồn hồ sơ

Khối mở rộng ở cuối trang, giữ đầy đủ bảng nguồn cũ (tất cả / chờ rà soát / trả lại / quá hạn / đến hạn theo phạm vi). Vào bằng mục "Báo cáo KH-KD" thì khối này mở sẵn.

## 3. Danh sách và form

Danh sách và form KH-KD giữ nguyên nút, trạng thái và quyền native. Thay đổi chỉ ở khoảng cách, tiêu đề và hover. Nếu đang nhập form mà bấm sang mục khác trong sidebar, Odoo vẫn kiểm tra và lưu như bình thường. Thiếu trường bắt buộc thì form được giữ lại kèm cảnh báo, dữ liệu đã nhập không mất.

## 4. Không có trong bản này

Không có dòng tiền, lợi nhuận, công nợ, tiền đã trả, xuất báo cáo tổng hợp, duyệt hàng loạt hay ký. Audit nghiệp vụ KD-NATIVE-001, Q2, G7 và pilot vẫn chưa đóng.
