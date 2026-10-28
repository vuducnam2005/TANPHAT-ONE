# Ngôn ngữ giao diện TANPHAT ONE

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
