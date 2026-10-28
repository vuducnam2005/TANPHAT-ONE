# Ngôn ngữ giao diện TANPHAT ONE

## Màn hình đăng nhập chung

Kế hoạch thiết kế được rà theo skill `frontend-design` trước khi dựng: ưu tiên một hình cầu đặc trưng cho nghiệp vụ cầu đường, bỏ dãy card/KPI mẫu và không dựng danh sách chín phân hệ chưa triển khai. Các màu chính: navy `#15384e`, ink `#18384c`, cyan `#087386`, giấy lạnh `#f6f8fa`, vàng đồng `#e7bd79`, đường biên `#ccd7df`. Logo Tấn Phát chính thức chưa được cung cấp; biểu tượng hiện tại là monogram hình cầu của giao diện.

Trang đăng nhập `/work/` là cổng vào thống nhất cho các phân hệ TANPHAT ONE. Thiết kế dành cho nhân viên Tấn Phát, lấy hình cầu dây văng làm hình ảnh chủ đạo: nhịp cầu biểu đạt kết nối giữa kế hoạch, thiết kế và công trường; đường cáp được vẽ vào khi trang mở để tạo một chuyển động có chủ đích. Form dùng Be Vietnam Pro đóng gói trong bundle, nền giấy lạnh, navy công trường, cyan cho tương tác và vàng đồng cho điểm nhấn.

Desktop chia hai vùng: câu chuyện thương hiệu và minh họa ở bên trái, form xác thực ở bên phải. Mobile xếp phần nhận diện lên trên và giữ form đủ rộng cho thao tác bằng một tay. Nút, ô nhập, nút hiện mật khẩu và khối hỗ trợ có hover/focus rõ; `prefers-reduced-motion` tắt animation vẽ cầu và các chuyển động chuyển trạng thái. Các lỗi nói người dùng cần sửa gì, không lộ thông báo/HTML nội bộ của Odoo.

Xác thực vẫn thuộc Odoo: React gọi `/web/session/authenticate` cùng origin, rồi đọc `/api/v1/me` để bootstrap workspace. Nếu Odoo trả `uid: null` do MFA, trang yêu cầu người dùng bấm tiếp tục xác thực ở `/web/login`, giữ redirect hiện tại. Mật khẩu chỉ sống trong form và request đang chạy, không đi vào storage hoặc log.

## Không gian làm việc

Giao diện phục vụ nhân viên phòng Kế hoạch Kinh doanh theo dõi hồ sơ dự án. Giữ bảng màu đã có của prototype để các màn hình sau nhất quán.

- Navy `#16384e`: điều hướng và nhận diện Tấn Phát.
- Ink `#132f45`: tiêu đề, văn bản chính.
- Cyan `#087386`: liên kết, mã dự án và lựa chọn đang hoạt động.
- Canvas `#eaf0f2`: nền; trắng `#ffffff`: vùng làm việc.
- Border `#cbd9df`: ranh giới bảng/form; xanh `#246850`: trạng thái hoạt động.
- Segoe UI với Noto Sans dự phòng: đọc tiếng Việt, không phụ thuộc tải font ngoài.

Bố cục desktop có điều hướng trái, tài khoản trên cùng và danh sách hồ sơ ở giữa. Mobile chuyển sidebar thành thanh điều hướng phía trên. Mã dự án, phòng chủ trì và trạng thái có phân cấp rõ; không thêm KPI tài chính khi backend chưa cung cấp.

```text
Điều hướng | Tài khoản / công ty
           | Tên trang + mô tả ngắn
           | Tìm dự án / làm mới
           | Hồ sơ dự án → chi tiết
           | Phân trang
```

Các điều chỉnh so với mẫu dashboard phổ thông: dùng hồ sơ dự án thực tế thay dãy KPI mẫu, palette công trường đã có thay palette mới, giữ form và tên nghiệp vụ tiếng Việt. Màn hình không đưa tên API, model, ID nội bộ hay thuật ngữ lập trình vào nội dung làm việc.

Kiểm tra trực quan desktop 1440px và mobile 390px bằng browser test. Focus bàn phím hiển thị rõ, có skip link, reduced-motion và các trạng thái loading/empty/error/permission/session. Prototype thiết kế cũ vẫn nằm ở `prototype/` để tham khảo.
