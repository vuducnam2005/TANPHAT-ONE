# Hướng dẫn sử dụng: Bố cục hồ sơ nhân viên, Quản trị tài khoản & Đặt lại mật khẩu (HR-UI-002)

**Hiện hành từ HR-ACCOUNT-ROLE-001 (12/11/2026):** dùng [hướng dẫn hồ sơ, tài khoản và vai trò](HR_ACCOUNT_ROLE_001_USER_GUIDE.md). Các bước chọn/liên kết/gỡ user và bố cục sáu tab bên dưới là lịch sử, đã được thay thế. Tình trạng hiện dùng Mở/Khóa/Chưa có tài khoản.

Tài liệu hướng dẫn dành cho Quản trị viên hệ thống (`base.group_system`), Cán bộ Nhân sự (HR Officer / Manager) và Người dùng TANPHAT ONE.

---

## 1. Nguyên tắc bảo mật mật khẩu trong TANPHAT ONE

> [!IMPORTANT]
> **Không thể xem mật khẩu hiện tại/cũ của bất kỳ tài khoản nào.**
> 
> Mật khẩu người dùng trong TANPHAT ONE được mã hóa một chiều an toàn bằng thuật toán mã hóa tiêu chuẩn **PBKDF2 với SHA-512** (kèm salt ngẫu nhiên) ngay trong lõi Odoo.
> - Hệ thống **không bao giờ lưu trữ mật khẩu ở dạng văn bản rõ (plain text)**.
> - Không có bất kỳ quản trị viên, lập trình viên hay công cụ nào có thể giải mã hoặc đọc lại mật khẩu hiện tại của người dùng.
> - Giao diện của TANPHAT ONE **tuyệt đối không hiển thị các chuỗi dấu chấm tròn giả (ví dụ: `••••••••••••`)** như thể hệ thống biết mật khẩu hiện tại.
> - Khi người dùng quên mật khẩu hoặc cần cấp lại, Quản trị viên hệ thống sử dụng chức năng **Đặt lại mật khẩu mới**.

---

## 2. Bố cục mới của hồ sơ nhân viên (Employee Profile)

Hồ sơ nhân viên đã được tái cấu trúc hoàn toàn theo bộ nhận diện thương hiệu TANPHAT ONE (màu chủ đạo Xanh Navy `#17324D` và Xanh Mòng két / Teal `#087F8C`):

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Avatar 80px]  Họ và tên nhân viên                                     │
│                [TP10039] [Phòng ban] [Đang quản lý] [Chưa liên kết]   │
├────────────────────────────────────────────────────────────────────────┤
│ [Alert] Hồ sơ còn thông tin cần bổ sung theo dữ liệu nguồn...          │
├────────────────────────────────────────────────────────────────────────┤
│ [Tổng quan]  [Công việc]  [Hồ sơ & năng lực]  [Cá nhân]  [Tài khoản]  [Nguồn dữ liệu] │
├────────────────────────────────────────────────────────────────────────┤
│  ┌─ Thông tin công việc ────────┐  ┌─ Thông tin liên hệ ────────────┐  │
│  │ Đơn vị / Phòng ban           │  │ Email công việc                │  │
│  │ Chức vụ nguồn                │  │ Điện thoại cơ quan             │  │
│  │ Chức danh đối chiếu          │  │ Địa điểm làm việc              │  │
│  └──────────────────────────────┘  └────────────────────────────────┘  │
│  ┌─ Tài khoản người dùng ───────────────────────────────────────────┐  │
│  │ Trạng thái: [Chưa liên kết]                   [Xem tài khoản ↗]  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────┤
│ [Chatter / Lịch sử trao đổi & ghi chú đặt ở đáy trang]                 │
└────────────────────────────────────────────────────────────────────────┘
```

### Các điểm cải tiến chính:
1. **Header gọn gàng**:
   - Ảnh đại diện kích thước chuẩn 80px (căn giữa trên di động).
   - Họ và tên rõ ràng, thanh thoát.
   - Nhãn huy hiệu (badges) trực quan: Mã nhân viên (ví dụ `TP10039`), Đơn vị, Trạng thái quản lý, và Trạng thái tài khoản.
   - Loại bỏ hoàn toàn nút `Invite` và nhãn `Not Invited` gây nhiễu của giao diện mặc định.
2. **6 Tab nghiệp vụ rõ ràng**:
   - **Tổng quan** (Tab mặc định): Trình bày dạng 2 cột thẻ thông tin: Thẻ công việc, Thẻ liên hệ, và Thẻ tài khoản kèm nút thao tác nhanh.
   - **Công việc**: Chứa thông tin vị trí chuyên môn, quản lý trực tiếp. Các mục lịch trình và giờ làm việc đã được ẩn khỏi giao diện người dùng.
   - **Hồ sơ & năng lực**: Kỹ năng chuyên môn, chứng chỉ hành nghề, bằng cấp.
   - **Cá nhân**: Quốc tịch, CCCD, ngày sinh, tình trạng gia đình.
   - **Tài khoản**: Khu vực quản trị liên kết tài khoản Odoo và đặt lại mật khẩu cho quản trị viên.
   - **Nguồn dữ liệu**: Thông tin đối chiếu với hồ sơ nguồn (mã nguồn, phòng ban nguồn, ghi chú dữ liệu ban đầu).
3. **Chatter đặt ở đáy**: Khu vực trao đổi, ghi chú nội bộ và lịch sử hoạt động được đặt gọn gàng ở phía dưới trang hồ sơ, không lấn chiếm không gian hiển thị thông tin chính.

---

## 3. Xem thông tin tài khoản từ Danh sách nhân viên

1. Truy cập phân hệ **TP HR → Nhân viên → Danh sách nhân viên**.
2. Trên bảng danh sách, các cột hiển thị bao gồm:
   - **Mã nhân viên**: Mã định danh chuẩn TANPHAT ONE (ví dụ: `TP10012`, `TP10060`).
   - **Họ và tên**: Tên đầy đủ của nhân sự.
   - **Đơn vị / Phòng ban**: Tên phòng ban hiện tại.
   - **Chức vụ nguồn**: Chức vụ theo dữ liệu tuyển dụng/nguồn.
   - **Tên đăng nhập**: Tên đăng nhập thực tế của tài khoản Odoo đã liên kết. Đối với nhân sự chưa liên kết tài khoản, ô này để trống (hệ thống không bao giờ tự tạo tên đăng nhập giả định).
   - **Trạng thái tài khoản**: Huy hiệu `Chưa liên kết` (màu cam nhạt), `Đang hoạt động` (xanh lục), hoặc `Đã vô hiệu hóa` (xám).
   - **Trạng thái hồ sơ**: Đang làm việc hoặc Đã lưu trữ.
   - **Nút Xem tài khoản**: Nút thao tác nhanh với biểu tượng thẻ nhân viên.
3. Bấm vào nút **Xem tài khoản** trên bất kỳ dòng nhân viên nào để mở ngay hộp thoại quản trị tài khoản mà không cần rời khỏi danh sách.

---

## 4. Quản trị liên kết tài khoản (Dành cho Quản trị viên hệ thống)

> [!NOTE]
> Chỉ người dùng thuộc nhóm **Quản trị hệ thống (`base.group_system`)** mới có quyền thực hiện thao tác liên kết, thay đổi hoặc gỡ liên kết tài khoản. Các vai trò khác chỉ có quyền xem thông tin.

### 4.1. Liên kết tài khoản cho nhân viên
1. Mở hộp thoại tài khoản từ nút **Xem tài khoản** trên danh sách, hoặc từ tab **Tài khoản** trong form hồ sơ.
2. Tại mục **Quản trị liên kết**:
   - Chọn tài khoản người dùng nội bộ tại ô **Tài khoản người dùng**.
   - *Lưu ý*: Hệ thống tự động lọc các tài khoản hợp lệ (chỉ hiển thị người dùng nội bộ cùng công ty; tự động chặn tài khoản công cộng, tài khoản siêu quản trị hoặc tài khoản đã được liên kết với nhân sự khác).
   - Nhập lý do liên kết vào ô **Lý do thao tác** (ví dụ: *Cấp tài khoản làm việc cho nhân sự mới*).
3. Bấm nút **Lưu liên kết tài khoản** (màu xanh mòng két).
4. Hệ thống ghi nhận lịch sử vào sổ theo dõi (chatter) và cập nhật huy hiệu trạng thái tài khoản ngay lập tức.

### 4.2. Gỡ bỏ liên kết tài khoản
1. Mở hộp thoại tài khoản của nhân sự đang có tài khoản liên kết.
2. Tại mục **Quản trị liên kết**, nhập lý do gỡ bỏ vào ô **Lý do thao tác** (bắt buộc nhập lý do).
3. Bấm nút **Gỡ liên kết tài khoản**.
4. Xác nhận thông báo trên hộp thoại.
5. Khi gỡ liên kết:
   - Hồ sơ nhân viên trở về trạng thái `Chưa liên kết`.
   - Tài khoản người dùng Odoo vẫn được bảo toàn nguyên vẹn trong hệ thống (không bị xóa vật lý).
   - Các quyền hạn dự án, phòng ban và lịch sử công việc của người dùng vẫn được bảo lưu theo quy định an toàn dữ liệu.

---

## 5. Quy trình Đặt lại mật khẩu (Dành cho Quản trị viên hệ thống)

Khi người dùng cần cấp lại mật khẩu mới, Quản trị viên hệ thống thực hiện theo các bước sau:

1. Mở form hồ sơ của nhân sự đã liên kết tài khoản, chuyển đến tab **Tài khoản** (hoặc mở qua hộp thoại tài khoản).
2. Bấm nút **Đặt lại mật khẩu**.
3. Hệ thống mở cửa sổ **Đặt lại mật khẩu** của Odoo:
   - Thông tin tài khoản được điền sẵn chính xác.
   - Bấm vào ô **Mật khẩu mới** để nhập mật khẩu cần cấp.
4. **Sử dụng nút bật/tắt hiện mật khẩu**:
   - Mặc định, mật khẩu nhập vào sẽ hiển thị dưới dạng dấu chấm để chống nhìn trộm trên màn hình.
   - Quản trị viên có thể bấm vào biểu tượng con mắt ở góc phải ô nhập để **hiển thị mật khẩu rõ ràng**, giúp kiểm tra tính chính xác của mật khẩu trước khi lưu.
   - Bấm lại biểu tượng con mắt để ẩn mật khẩu về dạng bảo mật.
5. Bấm nút **Thay đổi mật khẩu** (Change Password).
6. **Xác thực danh tính Quản trị viên (`@check_identity`)**:
   - Nhằm bảo đảm an ninh tối đa, hệ thống sẽ yêu cầu Quản trị viên nhập lại chính mật khẩu của mình để xác nhận thẩm quyền.
   - Nhập mật khẩu của Quản trị viên và bấm **Xác nhận**.
7. Mật khẩu mới được băm và cập nhật vào cơ sở dữ liệu. Quản trị viên có thể bàn giao mật khẩu mới cho nhân sự một cách an toàn.

---

## 6. Khả năng tương thích trên thiết bị di động (Responsive)

Hệ thống hỗ trợ toàn diện trên mọi kích thước màn hình:
- **Màn hình lớn (Desktop 1440px / Laptop 1024px)**: Bố cục 2 cột thẻ thông tin rộng rãi, rõ ràng.
- **Máy tính bảng (Tablet 768px)**: Tự động co giãn hợp lý, giữ trọn vẹn các nút thao tác.
- **Điện thoại di động (Mobile 390px / 320px)**:
  - Khối định danh và avatar tự động căn giữa.
  - Các cột thẻ chuyển sang dạng xếp chồng 1 cột dọc (stacked).
  - Không xuất hiện thanh cuộn ngang gây khó khăn khi thao tác.
  - Hỗ trợ chế độ giảm chuyển động (`prefers-reduced-motion`) cho các thiết bị cần tối ưu hiệu năng.
