# Tadic Management

Workspace khởi tạo cho hệ thống quản trị nội bộ. Tháng 1 tập trung vào đọc tài liệu nghiệp vụ, khảo sát, thiết kế khung hệ thống và chọn techstack; chưa triển khai code chức năng nghiệp vụ.

## Cấu trúc

- `frontend/`: trang mẫu ReactJS + TypeScript + Vite.
- `custom_addons/`: addon `tadic_core` mới là khung tối thiểu; chưa có nghiệp vụ hay model.
- `docs/`: biểu mẫu khảo sát và phác thảo dữ liệu cần xác nhận.
- `DESIGN.md`: quy ước giao diện dùng chung cho giai đoạn xây dựng React.
- `odoo/`: source Odoo 20 từ upstream, được giữ riêng khỏi Git của dự án.
- `venv/`: môi trường Python cục bộ, không đưa lên Git.
- `odoo.conf`: cấu hình cục bộ chứa thông tin truy cập database, không đưa lên Git.

Repository GitHub của dự án: [vuducnam2005/TadicManagement](https://github.com/vuducnam2005/TadicManagement).

## Chạy giao diện mẫu

```powershell
cd frontend
npm install
npm run dev
```

Mở URL mà Vite in ra trong terminal (mặc định `http://localhost:5173`). Kiểm tra chất lượng với `npm run lint` và `npm run build`.

## Chạy Odoo cục bộ trên Windows

1. Dùng source Odoo nhánh `20.0` trong `odoo/`, Python virtual environment trong `venv/`, và PostgreSQL đã chạy.
2. Sao chép `odoo.conf.example` thành `odoo.conf`, điền tài khoản PostgreSQL cục bộ và đổi master password. File thật được Git bỏ qua.
3. Chạy `start.bat` từ thư mục gốc. Script tự nhận đường dẫn workspace hiện tại và mở database `tadic_demo` tại `http://127.0.0.1:8069`.
4. Database `tadic_demo` đã được khởi tạo trong workspace này. Ở máy khác, tạo database thử nghiệm trước khi chạy script hoặc điều chỉnh tên database trong `start.bat`. Chỉ dùng dữ liệu giả lập cho bản thử nghiệm.

Nếu Odoo báo `password authentication failed`, cần kiểm tra mật khẩu của role PostgreSQL trong `odoo.conf`. Thông tin đăng nhập Odoo thử nghiệm trên máy này nằm trong `LOCAL-ACCESS.txt`, được Git bỏ qua.

## Kế hoạch tháng đầu

Xem [kế hoạch tổng thể điều chỉnh](docs/ke-hoach-tong-the.md), [kế hoạch tháng 1](docs/ke-hoach-thang-1.md), [checklist tuần 1](docs/tuan-1-checklist.md) và [phân tích mẫu PKH](docs/phan-tich-mau-pkh.md). Các biểu mẫu trong `docs/` là bản nháp để thu thập và xác nhận yêu cầu, chưa đại diện cho quy trình đã được phê duyệt.
