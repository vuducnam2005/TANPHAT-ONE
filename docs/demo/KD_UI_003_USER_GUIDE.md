# KD-UI-003 — Hướng dẫn đọc bảng và màn hình chi tiết KH-KD

Áp dụng trên dev `http://127.0.0.1:18069/odoo`, app **Kế hoạch Kinh doanh**, từ ngày 07/11/2026. Dữ liệu là bộ tổng hợp (254 hồ sơ seed + 14 hồ sơ UI). Đây là hướng dẫn thao tác và kiểm tra giao diện, không phải xác nhận nghiệp vụ, audit hay pilot.

Ai thấy dòng, cột, tab hoặc nút nào vẫn do quyền backend quyết định. Bản này chỉ đổi cách trình bày: không thêm nút nghiệp vụ, không đổi trạng thái, công thức hay quyền.

## 1. Bảng danh sách

Mọi danh sách mở từ sidebar KH-KD có cùng chuẩn:

| Bạn thấy | Ý nghĩa / cách dùng |
| --- | --- |
| Khung bo góc, đường kẻ dọc và ngang giữa các ô | Đọc theo hàng và cột như bảng tính. Cột chọn (checkbox) không có vạch dọc. |
| Header nền xanh xám nhạt, chữ đậm | Tên cột dài được xuống dòng, không bị "…". Bấm tên cột để sắp xếp (máy chủ sắp xếp, không chỉ trang đang xem). |
| Tên, dự án, mã hồ sơ xuống dòng | Đọc đủ chữ, dòng cao hơn khi tên dài. |
| Trạng thái dạng nhãn màu | Đọc đủ chữ; màu chỉ hỗ trợ, chữ mới là trạng thái. |
| Pager `1-20 / tổng` | Mỗi trang 20 dòng, tổng là số bản ghi bạn được xem theo quyền. Mũi tên ‹ › chuyển trang. |
| Header đứng yên khi cuộn | Cuộn trong khung bảng; tiêu đề cột luôn ở trên. |
| Bảng rộng hơn màn hình | Cuộn ngang **trong khung bảng**; trang không bị trượt ngang. |
| Ô ngày/giá trị trống | Có thể để trống; trong form chỉ đọc sẽ hiện "—". |

Danh sách không có cột tiền. Giá trị minh họa chỉ nằm trong tab riêng của form và chỉ hiện với người có quyền đọc.

### Thanh công cụ của bảng

- **Thoáng | Gọn**: mật độ dòng (khoảng 48px hoặc 38px). Lựa chọn được nhớ trên trình duyệt này và dùng chung với ⚙ "Tùy chọn hiển thị".
- **Khôi phục cột**: trả các cột về mặc định của màn đang mở. Không đụng cấu hình cột của app khác.
- **Chọn cột**: biểu tượng điều chỉnh ở cuối hàng tiêu đề. Cột phụ (ví dụ "Nhiệm vụ cha", "Đầu ra bàn giao", "Nguồn thông tin") ẩn sẵn, bật khi cần.
- Tìm kiếm, bộ lọc, nhóm theo, xuất dữ liệu (theo quyền xuất) và chọn nhiều dòng giữ như Odoo. Khi đang chọn dòng, hai nút Thoáng/Gọn và Khôi phục cột tạm ẩn để nhường chỗ cho thao tác hàng loạt native.

Danh sách **Hợp đồng và phụ lục — TP Contracts** dùng view của TP Contracts: có kẻ bảng khi mở trong KH-KD, mật độ đổi bằng ⚙ ở sidebar. Mở từ app TP Contracts thì giữ giao diện gốc.

## 2. Cột chính theo từng màn

| Màn | Cột hiện sẵn | Cột tùy chọn (ẩn sẵn) |
| --- | --- | --- |
| Cơ hội và hồ sơ thầu | Cơ hội, Khách hàng / chủ đầu tư, Tình trạng hồ sơ, Hạn, Người phụ trách, Hình thức | Dự án liên quan, Nguồn thông tin, Phạm vi / gói thầu |
| Hồ sơ dự án | Mã dự án, Tên, Khách hàng, Người quản lý, … | Phòng chủ trì, Công ty, Trạng thái cập nhật, Giai đoạn |
| Kế hoạch và công việc | Tiêu đề, Dự án, Chịu trách nhiệm chính, Thời hạn, Trạng thái | Nhiệm vụ cha, Đầu ra bàn giao |
| Giao khoán, Sản lượng, Nghiệm thu, Đề nghị thanh toán, Kế hoạch định kỳ, Năng lực, Nghĩa vụ | Mã hồ sơ, Tên, Dự án, các cột nghiệp vụ chính, Trạng thái, Hạn | Người lập/phụ trách, nguồn liên kết, kỳ, đối chiếu |

Ma trận đầy đủ: [thiết kế KD-UI-003](../ui/KD_UI_003_TABLES_AND_DETAILS_DESIGN.md#6-ma-trận-từng-màn).

## 3. Màn hình chi tiết

- Tiêu đề lớn là tên hồ sơ. Thanh trạng thái ở góc phải trên.
- Thông tin chia khối có tiêu đề: **Căn cứ và dự án**, **Phụ trách và hạn**, rồi khối nghiệp vụ riêng của từng loại (ví dụ "Loại đề nghị và căn cứ", "Đối tượng và kỳ").
- Tab xếp theo thứ tự đọc: nội dung/phạm vi → chứng từ, kiểm kê hoặc danh mục → **Giá trị minh họa** (chỉ khi có quyền) → **Lịch sử lần trình**.
- Bảng con (giá trị minh họa, lịch sử lần trình, khoán cấp 2) có kẻ như bảng chính.
- Tên dự án, hợp đồng nguồn dài được xuống dòng; ô trống chỉ đọc hiện "—".
- Chỉ có một nút Lưu/Bỏ của Odoo. Nút nghiệp vụ trên header (**Gửi rà soát**, **Trả lại**, **Mở bản sửa**) chỉ hiện khi đúng trạng thái và đúng vai trò. Mỗi nút mở hộp thoại có ô lý do; thiếu lý do thì không xác nhận được.
- Điện thoại: một cột, tab cuộn ngang, nút ‹ › giữa các hồ sơ vẫn giữ.

## 4. Sidebar

Mục đang mở luôn tô đúng nghiệp vụ: mở từ Tổng quan (biểu đồ, bảng dự án), từ smart button hay tải lại trang thì sidebar vẫn tô mục của danh sách/hồ sơ đang xem. Quay lại breadcrumb Tổng quan thì Tổng quan được tô.

## 5. Kiểm tra nhanh trong 7 bước

1. Đăng nhập dev 18069, mở app **Kế hoạch Kinh doanh** → **Kế hoạch và công việc**. Kiểm tra: khung bảng có kẻ ô, tiêu đề không có "…", pager `1-20 / …`.
2. Cuộn xuống trong bảng: hàng tiêu đề đứng yên. Bấm **Gọn** rồi tải lại trang (F5): bảng vẫn Gọn. Bấm **Thoáng** để trả lại.
3. Mở chọn cột (biểu tượng cuối tiêu đề), bật **Đầu ra bàn giao**, tải lại trang: cột vẫn hiện. Bấm **Khôi phục cột**: cột ẩn lại.
4. Bấm ‹ › sang trang 2, mở một dòng, rồi bấm breadcrumb quay lại: vẫn ở trang 2. Sidebar vẫn tô "Kế hoạch và công việc".
5. Mở **Đề nghị thanh toán** → một hồ sơ: thấy các khối có tiêu đề, tab theo thứ tự; ô "Từ kỳ/Đến kỳ" trống hiện "—". Đăng nhập vai trò không có quyền tiền thì không có tab **Giá trị minh họa**.
6. Ở **Tổng quan**, đặt chuột lên thẻ số liệu hoặc biểu đồ và lăn chuột (hoặc vuốt touchpad): trang cuộn xuống tới bảng dự án và "Việc của tôi". Bấm tổng cơ hội (G03) rồi tên một dự án trong bảng điều hành: sidebar tô "Cơ hội và hồ sơ thầu", rồi "Hồ sơ dự án".
7. Mở app CRM hoặc Project ngoài KH-KD: bảng giữ giao diện Odoo gốc, không có đường kẻ KH-KD. Trên điện thoại (hoặc thu nhỏ cửa sổ <768px), dùng **Menu KH-KD**; bảng cuộn ngang trong khung, trang không trượt ngang.

## 6. Không có trong bản này

Không có cột/tổng tiền trong danh sách, không duyệt hàng loạt, không ký, không hạch toán, không xác nhận tiền đã trả, không giao việc mới. Sáu phụ lục chưa tạo, BASE approval, TASK-001, audit KD-NATIVE-001 và pilot vẫn ngoài phạm vi.
