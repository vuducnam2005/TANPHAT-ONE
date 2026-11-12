# Hướng dẫn sử dụng: Trang chủ quản trị TANPHAT ONE (UI-HOME-004)

Tài liệu hướng dẫn dành cho Quản trị viên hệ thống và người dùng nghiệp vụ về cách truy cập, bố cục và thao tác trên Trang chủ TANPHAT ONE sau đợt cập nhật UI-HOME-004 (theo quyết định DEC-036).

**Cập nhật sau CHG-20261110-006:**
Đã xử lý triệt để 3 lỗi hiển thị:
1. Duy nhất một thanh điều hướng `.o_main_navbar` native của Odoo; không còn header giả `.tp-nav`.
2. Khôi phục 3 công cụ quản trị bên cạnh tiêu đề: "Cài đặt", "Quản lý ứng dụng", "Tất cả ứng dụng" (mở panel tìm kiếm mọi module được cấp quyền).
3. 7 module có icon vector SVG riêng biệt, chuẩn kích thước 24–26px, không rơi vào hình tròn fallback.

---

## 1. Dành cho Quản trị viên hệ thống (Admin)

### 1.1. Cách truy cập
- **Địa chỉ:** `http://127.0.0.1:18069/odoo` (hoặc bấm biểu tượng **Trang chủ** trên thanh điều hướng Odoo).
- **Tài khoản:** Tài khoản có quyền quản trị hệ thống (`base.group_system`, ví dụ: `admin`).

### 1.2. Bố cục Trang chủ quản trị
Giao diện được thiết kế chuyên biệt theo tiêu chuẩn TANPHAT ONE với đúng **7 mục** chia làm 2 nhóm:

1. **Nhóm "Phòng ban và đơn vị":**
   - **Kế hoạch Kinh doanh (nổi bật, chiếm 2 cột trên desktop):** Trạng thái *"Đang hoạt động"*. Bấm vào mở trực tiếp workspace KH-KD đang vận hành với đầy đủ hồ sơ dự án, đấu thầu, hợp đồng và báo cáo.
   - **Phòng Thiết kế:** Trạng thái *"Đang phát triển"*. Bấm vào mở trang thông tin chuẩn bị.
   - **Phòng Kỹ Thuật:** Trạng thái *"Đang phát triển"*. Bấm vào mở trang thông tin chuẩn bị.
   - **Phòng BIM-QC:** Trạng thái *"Đang phát triển"*. Bấm vào mở trang thông tin chuẩn bị.
   - **TADIC:** Trạng thái *"Đang phát triển"*. Bấm vào mở không gian đơn vị nội bộ.

2. **Nhóm "Nhân sự và tuyển dụng":**
   - **Quản lý nhân sự:** Trạng thái *"Triển khai tiếp theo"*. Bấm vào mở màn hình native Quản lý nhân sự của Odoo (`hr.menu_hr_root`) để xem danh bạ nhân viên hiện có.
   - **Tuyển dụng:** Trạng thái *"Đang phát triển"*. Bấm vào mở trang thông tin chuẩn bị.

3. **Ghi chú chân trang:**
   *"Danh mục này chỉ dành cho quản trị hệ thống. Các ứng dụng khác vẫn truy cập bình thường qua menu Odoo trên thanh điều hướng."*

### 1.3. Thao tác trên các trang Placeholder ("Đang phát triển")
- Khi bấm vào các đơn vị đang phát triển (Thiết kế, Kỹ Thuật, BIM-QC, TADIC, Tuyển dụng), hệ thống hiển thị trang chi tiết:
  - Tiêu đề đơn vị tương ứng.
  - Huy hiệu trạng thái *"Đang phát triển"*.
  - Thông báo: *"Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau."*
  - Nút **"Về Trang chủ"**: Bấm vào để quay lại màn hình 7 thẻ quản trị.
- **Phím tắt & Điều hướng trình duyệt:**
  - Hỗ trợ nút Back / Forward trên trình duyệt web.
  - Hỗ trợ deep-link URL (ví dụ: `#unit=design`, `#unit=technical`, `#unit=bim`, `#unit=tadic`, `#unit=recruitment`).
  - Khi quay về Trang chủ, tiêu điểm bàn phím tự động quay lại thẻ vừa được bấm.

### 1.4. Công cụ quản trị và Danh sách Tất cả ứng dụng
Bên cạnh tiêu đề *"Trang chủ quản trị"*, quản trị viên có 3 nút công cụ nhanh:
- **Cài đặt:** Mở trực tiếp màn hình Thiết lập hệ thống Odoo (`base.menu_administration`).
- **Quản lý ứng dụng:** Mở trực tiếp màn hình Quản lý module/Apps Odoo (`base.menu_management`).
- **Tất cả ứng dụng:** Mở bảng trượt `#tp_home_all_apps` ngay trên trang:
  - Hiển thị danh sách toàn bộ các ứng dụng tài khoản admin được phân quyền truy cập.
  - Tích hợp ô tìm kiếm lọc nhanh ứng dụng theo tên hoặc từ khóa.
  - Bấm nút đóng `×` hoặc phím `Esc` để đóng panel và quay về giao diện Trang chủ 7 thẻ.
  - App switcher (nút 9 chấm) trên thanh điều hướng Odoo native vẫn hoạt động song song bình thường.

---

## 2. Dành cho Người dùng nghiệp vụ (Non-Admin)

### 2.1. Quyền hạn và giao diện
- Người dùng không có nhóm Quản trị hệ thống (ví dụ: Trưởng Ban KH-KD `kd.thuyanh`, Phó Ban `kd.tuananh`, các chuyên viên KH-KD `kd.thanh`, `kd.huong`, `kd.lananh`):
  - **Giữ nguyên 100% giao diện Trang chủ UI-HOME-003 hiện hành.**
  - **Không hiển thị** khung 7 thẻ quản trị hay các trang placeholder của admin.
  - Mọi quyền truy cập, mật khẩu, phân công dự án và thao tác nghiệp vụ KH-KD được bảo toàn nguyên vẹn.

### 2.2. Bố cục Trang chủ người dùng thường
- **Thanh tìm kiếm:** Tìm nhanh các lối vào được cấp quyền trên Trang chủ.
- **Không gian làm việc:** Thẻ *"Kế hoạch Kinh doanh"* mở trực tiếp workspace nghiệp vụ KH-KD.
- **Công cụ cá nhân:** Các tiện ích được cấp như *"Việc cá nhân"*, *"Lịch làm việc"*, *"Trao đổi"*.
- Các ứng dụng khác được mở từ menu native ở góc trái thanh điều hướng.

---

## 3. Khả năng tương thích thiết bị

- **Desktop (1440px):** Bố cục lưới 3 cột cân đối, thẻ Kế hoạch Kinh doanh span 2 cột nổi bật.
- **Tablet (768px):** Bố cục lưới 2 cột tự động co giãn.
- **Mobile (390px / 320px):** Bố cục lưới 1 cột, không bị tràn ngang màn hình, nút bấm và chữ hiển thị rõ ràng.
- **Khả năng tiếp cận:** Hỗ trợ điều hướng hoàn toàn bằng bàn phím (Tab/Enter), hỗ trợ chế độ giảm chuyển động (`prefers-reduced-motion`).
