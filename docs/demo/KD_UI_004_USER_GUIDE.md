# KD-UI-004 — Hướng dẫn đọc Tổng quan KH-KD

Áp dụng trên dev `http://127.0.0.1:18069/odoo`, app **Kế hoạch Kinh doanh** → **Tổng quan**, từ ngày 07/11/2026. Đây là hướng dẫn đọc và kiểm tra giao diện, không phải xác nhận nghiệp vụ, audit hay pilot. Thiết kế: [KD_UI_004_OVERVIEW_DESIGN.md](../ui/KD_UI_004_OVERVIEW_DESIGN.md); tiêu chí: [KD_UI_004_ACCEPTANCE.md](KD_UI_004_ACCEPTANCE.md).

Mọi số trên Tổng quan do máy chủ đếm trong phạm vi quyền của tài khoản đang đăng nhập. Hai người khác quyền có thể thấy số khác nhau trên cùng dữ liệu; đó là đúng. Tổng quan không thể hiện dòng tiền, lợi nhuận, công nợ, quyết định BASE, bản ký hay nghiệm thu bên ngoài.

## 1. Đầu trang

| Bạn thấy | Ý nghĩa |
| --- | --- |
| "Dữ liệu lúc 11:09 07/11/2026" | Thời điểm máy chủ trả số đang hiện. Khi làm mới thất bại, dòng này thêm "— chưa làm mới được" và giữ giờ cũ. |
| Ba chip **Dự án / Hợp đồng / Phiên bản** | Quy mô dữ liệu bạn được xem. Rê chuột hoặc focus để đọc chip đếm gì và bộ lọc nào áp dụng. Bấm để mở danh sách tương ứng. |
| **Tạo hồ sơ** (nút xanh, chỉ khi có quyền tạo) | Menu chọn loại hồ sơ cần tạo. Là nút chính duy nhất. |
| **Làm mới**, **Xem dữ liệu ▾**, ⚙ | Tải lại số; menu mở danh sách theo loại hồ sơ bạn được xem; tùy chọn hiển thị (mật độ, giảm chuyển động). |

Chip quy mô **không cùng bộ lọc** với các biểu đồ:

- Dự án: chỉ áp bộ lọc Dự án; không áp ngày và người phụ trách.
- Hợp đồng: áp Dự án; Người phụ trách = người tạo hợp đồng; không áp ngày.
- Phiên bản: áp Dự án; lọc ngày theo ngày ghi nhận phiên bản; không áp người phụ trách.

## 2. Bộ lọc

Một hàng: **Dự án**, **Người phụ trách**, **Từ ngày**, **Đến ngày**, **Xóa lọc**. Mỗi nguồn hồ sơ lọc ngày theo ngày riêng của nó — rê vào "ⓘ Ngày lọc tùy nguồn" để xem chi tiết (chứng từ, kỳ kế hoạch, hạn chứng chỉ, hạn công việc, hạn hồ sơ thầu, ngày ghi nhận phiên bản). "Đến ngày" trước "Từ ngày" bị chặn và có thông báo dưới hàng lọc.

Trên điện thoại, bộ lọc thu thành nút **Bộ lọc** có chip "N đang áp"; bấm để mở.

Đổi bộ lọc liên tục: màn hình luôn theo bộ lọc **mới nhất**; kết quả về muộn của lần lọc cũ bị bỏ qua.

## 3. Việc của tôi — 4 ô KPI

| Ô | Đếm |
| --- | --- |
| Chờ rà soát | Hồ sơ đang chờ chính bạn rà soát. |
| Bị trả lại | Hồ sơ của bạn bị trả lại. |
| Quá hạn | Hồ sơ bạn phụ trách có hạn trước hôm nay (ngày ghi trong ô). |
| Đến hạn trong 3 ngày | Hồ sơ bạn phụ trách có hạn từ hôm nay đến hôm nay + 3 (khoảng ngày ghi trong ô). |

Các ô có thể trùng nhau, **không cộng lại**. Bấm một ô để chuyển tab tương ứng trong khung **Việc của tôi** phía dưới và cuộn tới đó. KPI bằng 0 trong khi các biểu đồ có số là bình thường nếu bạn không được giao hồ sơ nào.

## 4. Hồ sơ đang xử lý — vòng khuyên và thanh 7 nhóm

- **Vòng khuyên** (1/3 bề ngang): tâm là tổng hồ sơ Nháp + Đang rà soát + Trả lại. Ba ô chú giải ghi số và % trên tổng (một chữ số thập phân; % có thể không cộng đúng 100 do làm tròn).
- **Thanh 7 nhóm** (2/3 bề ngang): Giao khoán, Sản lượng, Nghiệm thu, Đề nghị thanh toán, Kế hoạch định kỳ, Năng lực/chứng chỉ, Nghĩa vụ. Cùng một thang cho mọi nhóm; số cuối dòng là tổng nhóm.
- Đối chiếu: cộng cùng màu trên 7 thanh = số ở chú giải; cộng 7 tổng = số ở tâm.

Thao tác:

1. **Rê chuột / Tab tới** một trạng thái: màu đó nổi lên ở cả hai biểu đồ, màu khác mờ. Không tải thêm gì từ máy chủ.
2. **Bấm / Enter / chạm** một trạng thái: giữ nguyên tổng, hiện khung "Đang chọn: … trên N hồ sơ — chọn loại hồ sơ để mở" với nút từng nhóm có hồ sơ ở trạng thái đó. Nhóm 0 hồ sơ hiện mờ, nhóm không có quyền ghi "không có quyền xem".
3. Bấm một nút nhóm → mở đúng danh sách nhóm đó, đúng trạng thái và bộ lọc đang chọn. Sidebar tô đúng mục.
4. **Esc** hoặc **Bỏ chọn** để thôi chọn.
5. Bấm thẳng một đoạn màu trên thanh → mở danh sách nhóm + trạng thái đó. Bấm tên nhóm → mở toàn bộ nhóm. Đoạn 0 không có nút.

Trường hợp đặc biệt: không có hồ sơ trong phạm vi lọc → "Chưa có hồ sơ nháp, đang rà soát hoặc trả lại trong phạm vi lọc"; không có quyền xem nhóm nào → "Bạn chưa có quyền xem các loại hồ sơ này"; một số nhóm không có quyền → "N nhóm không có quyền xem, không tính vào tổng".

## 5. Công việc và cơ hội

- **Công việc theo dự án**: ba nhóm rời nhau Hoàn thành / Đang mở quá hạn / Đang mở còn lại. Đây là **số công việc**, không phải tiến độ khối lượng. Mặc định xem 8 dự án nhiều việc quá hạn nhất ("Đang xem 8/Y dự án", nút xem toàn bộ). Ghi chú cuối khung cho biết bao nhiêu việc chưa có hạn. Bấm đoạn màu mở đúng nhóm việc của dự án.
- **Cơ hội và chuẩn bị hồ sơ thầu**: khối **Đấu thầu** theo bước nội bộ (Đã xác định, Đang chuẩn bị, Đã khai báo nộp — chưa xác minh) và khối **Chỉ định thầu** riêng. "Đã khai báo nộp" là khai báo nội bộ, chưa phải xác minh đã nộp hay kết quả trúng thầu.

## 6. Tab chi tiết (tải khi mở)

- **Kế hoạch sản lượng**: chọn Tháng/Quý/Năm. Mỗi dòng một kế hoạch, ghi tiền tệ và căn cứ thuế riêng; hai thanh "Mục tiêu đã xác nhận" và "Sản lượng nguồn" dùng thang riêng của dòng — không so chéo dòng, không cộng kỳ/tiền. Mục tiêu chưa xác nhận hiện chữ, **không hiện 0**. Nhãn bên phải là tỷ lệ máy chủ tính (ví dụ 17%) hoặc "Chưa so sánh". Bấm tên mở kế hoạch; bấm thanh nguồn mở các hồ sơ sản lượng nguồn.
- **Hạn năng lực / chứng chỉ**: vòng khuyên nhỏ ba nhóm Đã hết hạn / Hôm nay – 30 ngày / Sau 30 ngày, có mốc ngày cụ thể; bấm chú giải mở đúng nhóm. Danh sách 5 hồ sơ sắp hết hạn gần nhất. Không tính hồ sơ chưa có ngày hết hạn, không suy tình trạng pháp lý.

## 7. Bảng điều hành dự án, Việc của tôi, bảng nguồn

Giữ chuẩn KD-UI-003: kẻ bảng, sắp xếp (máy chủ), chọn cột, pager, menu **Thao tác** từng dự án. **Việc của tôi** có 3 tab (Chờ rà soát, Bị trả lại, Quá hạn/đến hạn) và pager. **Bảng tổng hợp theo nguồn hồ sơ** đóng sẵn, bấm để mở.

## 8. Khi có lỗi

| Bạn thấy | Ý nghĩa / làm gì |
| --- | --- |
| Khung vàng "Chưa làm mới được — đang hiện dữ liệu lúc …" | Mạng/máy chủ lỗi lúc làm mới. Số đang hiện là của lần trước (giờ ghi rõ). Bấm **Thử lại**. |
| Khung đỏ "Không hiển thị số liệu" | Phiên hết hạn hoặc quyền bị thu hồi. Mọi số đã bị ẩn. Đăng nhập lại hoặc liên hệ quản trị; **Thử lại** sau khi có quyền. |

## 9. Chuyển động

Lần đầu mở: vòng khuyên vẽ một vòng (~0,7 giây), thanh mọc từ trái (< 0,8 giây). Đổi bộ lọc, sắp xếp, rê chuột không chạy lại hiệu ứng mở đầu. Bật "Giảm chuyển động" trong ⚙ (lưu trên trình duyệt này) hoặc trong cài đặt hệ điều hành để tắt hiệu ứng; số và nút dùng được ngay.

## 10. Tự kiểm tra nhanh trên 18069

1. Đăng nhập tài khoản rà soát KH-KD, mở **Kế hoạch Kinh doanh → Tổng quan**. Ở 1440×900 thấy đầu trang, bộ lọc, 4 KPI và cặp vòng khuyên + thanh 7 nhóm không cần cuộn.
2. Cộng 3 số chú giải = số ở tâm; cộng số cùng màu trên 7 thanh = số chú giải.
3. Bấm "Đang rà soát": tâm giữ nguyên, khung chọn nhóm hiện ra; bấm một nhóm → số dòng ở pager danh sách = số trên nút. Quay lại bằng breadcrumb "Tổng quan KH-KD".
4. Chọn một dự án ở bộ lọc → chip Dự án = 1, các biểu đồ đổi theo; bấm **Xóa lọc** → số về như bước 2.
5. Mở tab **Hạn năng lực / chứng chỉ**: ba số chú giải cộng bằng số ở tâm; bấm "Đã hết hạn" → pager danh sách bằng số đó.
6. Thu sidebar và mở trên điện thoại (hoặc cửa sổ hẹp 390px): không cuộn ngang; bộ lọc thu thành nút; lăn chuột/vuốt cuộn được trang.
7. Bật ⚙ → "Giảm chuyển động", tải lại: không còn hiệu ứng vẽ vòng/mọc thanh.
