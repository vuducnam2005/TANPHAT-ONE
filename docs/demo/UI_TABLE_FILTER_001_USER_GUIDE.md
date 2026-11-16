# Hướng dẫn sử dụng bộ lọc bảng TANPHAT ONE (`UI-TABLE-FILTER-001`)

Tài liệu hướng dẫn thao tác bộ lọc thống nhất theo chuẩn `DEC-044` áp dụng trên TP HR, KH-KD, TP Contracts, TP Core và các danh sách Odoo native đang mở (kiểm thử trên `tp_tanphat_test`, cổng `18079`).

---

## 1. Cách dùng thanh lọc thống nhất (`Lọc theo` / `Bộ lọc bảng`)

Hầu hết bảng danh sách trong **TP HR**, **KH-KD** và **TP Contracts** đều hiển thị thanh công cụ lọc ngay bên dưới thanh tìm kiếm:

1. **Chọn giá trị ở các ô tiêu chí (`Pending` — Đang chọn):**
   - **Chọn một / nhiều giá trị (`OR` trong cùng tiêu chí):** chọn nhiều phòng ban, trạng thái hoặc loại hình cùng lúc; kết quả trả về khớp bất kỳ giá trị nào trong nhóm đó.
   - **Kết hợp giữa nhiều tiêu chí (`AND`):** chọn thêm tiêu chí khác (vd. *Phòng ban = Thiết kế* **VÀ** *Loại hình = Dài hạn*), kết quả sẽ thu hẹp theo giao của cả hai nhóm.
   - **Phân biệt `Tất cả` và `Chưa khai báo`:** `Tất cả` không áp điều kiện; chọn `Chưa khai báo` sẽ lọc đúng các hồ sơ có giá trị trống (`False`/`NULL`), không gộp nhầm với `0`.
   - **Ô tìm đối tượng (`Many2one` — Dự án, Phòng ban, Khách hàng, Người phụ trách…):** gõ từ khóa để tìm trực tiếp từ máy chủ theo quyền của bạn, sau đó chọn bản ghi cụ thể trong danh sách gợi ý.
   - **Khoảng ngày (`Từ ngày` – `Đến ngày`):** hệ thống kiểm tra `Từ ngày <= Đến ngày` và quy đổi hết ngày (`23:59:59`) theo giờ Việt Nam (`Asia/Ho_Chi_Minh`).
   - Khi bạn vừa thay đổi giá trị nhưng chưa nhấn nút, nhãn **`Chưa áp dụng`** sẽ hiện để phân biệt với dữ liệu đang hiển thị.
2. **Nhấn `Áp dụng`:**
   - Hệ thống gửi truy vấn máy chủ, luôn đưa danh sách về **trang 1** (`offset = 0`) và cập nhật số đếm kết quả (`N kết quả`) cũng như bộ đếm phân trang.
   - Mỗi tiêu chí đang lọc hiển thị thành một **chip** (`Bộ lọc đang áp dụng`) có nút `×` để gỡ nhanh từng điều kiện.
3. **Kết hợp với `Bộ lọc nâng cao` và `Yêu thích (Favorites)` của Odoo:**
   - Nhấn **`Bộ lọc nâng cao`** để mở bảng `SearchModel` chuẩn Odoo (thêm điều kiện tùy biến, `Gom nhóm theo` hoặc lưu bộ lọc `Yêu thích`).
   - Điều kiện từ thanh lọc nhanh và `Bộ lọc nâng cao` / ô tìm kiếm trên cùng **đồng bộ hai chiều**: chỉnh một bên không làm mất điều kiện nâng cao của bên kia.
4. **Nhấn `Xóa bộ lọc`:**
   - Xóa các tiêu chí bạn vừa chọn trên thanh lọc, đồng thời **luôn giữ nguyên phạm vi gốc bắt buộc** của màn hình đang mở (vd. `Hồ sơ cần bổ sung`, `Lưu trữ`, `Chưa có tài khoản`, `Cần đối chiếu`, dự án quản trị bởi TP) và **giữ nguyên nhóm `Phòng ban`** ở **Danh sách nhân viên** (`HR-LIST-013`).

---

## 2. Hướng dẫn theo từng phân hệ

### 2.1. TP HR (`tp_hr_workspace`)
- **Danh sách nhân viên / Hồ sơ cần bổ sung / Lưu trữ / Chưa có tài khoản:** lọc theo Phòng ban (`department_id`), Chức vụ (`job_id`), Loại hình lao động (`tp_employment_kind`), Trạng thái tài khoản (`tp_account_status`), từ khóa tên/mã (`TP...`) và tiêu chí thiếu cơ bản.
- **Phòng ban, Chức vụ, Nơi làm việc, Nhãn, Loại kỹ năng, Loại hồ sơ năng lực, Nhập & đối chiếu, Nhật ký xóa & sửa mã, Hợp đồng nhân sự, Phiên bản hồ sơ:** dùng đúng bộ tiêu chí của từng bảng; **Nhật ký** và **Hợp đồng nhân sự** dùng quyền riêng theo `HR Manager` / `System Admin`.
- **Sơ đồ quản lý:** dùng bộ lọc `Phòng ban` và nút `Xóa bộ lọc`; vị trí **Ban Giám đốc / Ban lãnh đạo** luôn giữ ở đầu sơ đồ theo quy tắc hiển thị.
- **Tổng quan HR & Xuất Excel:** bộ lọc `Phòng ban`, `Chức vụ`, `Loại hình lao động`, `Trạng thái` áp dụng đồng bộ cho KPI, biểu đồ, bảng đơn vị và file Excel tải từ **`Xuất Excel nhân sự`** (`/tp_hr/export`).
- **Thông tin cá nhân (`My Profile`):** tab **Lịch sử hoạt động** hỗ trợ lọc nhanh theo nhóm sự kiện (`Tất cả`, `Hồ sơ & Cá nhân`, `Vai trò & Phòng ban`, `Tài khoản`) và ô tìm nội dung thay đổi; tab **Hợp đồng lao động** hỗ trợ lọc hợp đồng của chính bạn ở chế độ chỉ đọc.

### 2.2. KH-KD, TP Contracts & TP Core (`tp_kd_workspace`, `tp_contract`, `tp_core`)
- **Các bảng chính** (*Dự án*, *Đấu thầu*, *Hồ sơ dự án & thầu*, *Cần đối chiếu*, *Hạng mục/WBS*, *Công việc*, *Hợp đồng*, *Giao khoán*, *Sản lượng*, *Nghiệm thu*, *Kế hoạch định kỳ*, *Đề nghị thanh toán*, *Nghĩa vụ*, *Chứng chỉ*, *Danh mục công việc*): sử dụng dải nút lọc nhanh theo trạng thái + các ô tiêu chí `TpTableFilterBar`.
- **Phân trang & cỡ trang:** chọn `10 / 20 / 50 / 100` dòng (hoặc nhóm) mỗi trang ở góc phải thanh điều khiển; hệ thống đếm tổng bản ghi ở server theo đúng quyền dự án và quyền xem tiền của tài khoản.
- **Tổng quan & Trung tâm Báo cáo KH-KD (`R01–R06`):**
  - Sau khi chọn kỳ báo cáo, `Từ ngày / Đến ngày`, dự án, người phụ trách, trạng thái hoặc nhóm hiển thị, nhấn **`Áp dụng bộ lọc`** để làm mới bảng/biểu đồ.
  - Nhấn **`Xuất Excel (.xlsx)`**: tệp tải về khớp 100% tập đang lọc trên màn hình (kể cả tìm kiếm/sắp xếp), công thức nguy hiểm được vô hiệu hóa và người dùng không có quyền tài chính sẽ không thấy số tiền.

### 2.3. Các phân hệ Odoo native đang mở (`NAT-01` – `NAT-10`)
- Các màn hình **Training Attendances**, **Work Locations**, **Employee Types**, **Departure Reasons**, **Companies**, **Country Group**, **Calendar / Event Tags**, **Sales Tags**, **Dashboards Configuration Sections** và **Work Item Catalog** dùng thanh tìm kiếm chuẩn Odoo đã được bổ sung `<search>` view phù hợp nội dung thay cho tìm kiếm mặc định đơn lẻ.
- **Project Templates** của module Project gốc giữ đúng bộ lọc native, không bị trộn bộ lọc KH-KD.

---

## 3. Bảng con trong Form, giới hạn `Dirty Guard` và trên Mobile

- **Mở bảng con ở chế độ đầy đủ (`Tìm / lọc toàn bộ bảng`):** ở các form đã lưu (như *Phòng ban*, *Hồ sơ hợp đồng*, *Giao khoán*, *Sản lượng*, *Nghiệm thu*, *Kế hoạch*, *Thanh toán*…), khi form **sạch (chưa có thay đổi dở)**, nhấn **`Tìm / lọc toàn bộ bảng`** để mở hộp thoại danh sách đầy đủ có thanh lọc và tìm kiếm nâng cao.
- **Giới hạn an toàn khi đang sửa (`Dirty Guard`):** nếu bạn đang tạo bản ghi mới (`chưa lưu`) hoặc đã sửa dữ liệu trên form nhưng chưa nhấn **Lưu**, nút lọc bảng con và nút đổi kích thước trang sẽ tự khóa (kèm thông báo **`Lưu thay đổi để lọc`** / **`Lưu hoặc hủy thay đổi để lọc bảng này`**) để tránh làm mất các dòng bạn đang nhập dở. Hãy **Lưu** hoặc **Hủy** thay đổi trước khi lọc.
- **Giới hạn tìm kiếm `Many2one`:** mỗi lần gõ chỉ tải danh sách gợi ý giới hạn ở server theo quyền truy cập; nếu không thấy bản ghi mong muốn, hãy gõ thêm từ khóa chính xác hơn (tên hoặc mã).
- **Trên điện thoại (`<= 767px`) / Zoom `200%`:** thanh lọc tự thu gọn sau nút **`Bộ lọc`** (hiển thị số lượng bộ lọc đang bật) để không che bảng dữ liệu; chạm để mở hoặc đóng ngăn kéo lọc, kích thước nút đạt tối thiểu `44px`.
