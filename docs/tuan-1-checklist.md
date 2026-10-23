# Checklist tuần 1 (26/10–01/11/2026)

Nguồn: tab `KH&BC_Tuan 1` của kế hoạch công việc. Chỉ đánh dấu hoàn thành khi có đầu ra kiểm tra được; không cập nhật trạng thái trong workbook thay người phụ trách.

| Đầu việc | Đầu ra để kiểm tra | Tình hình trong workspace |
| --- | --- | --- |
| 1. Khảo sát P.KHKD và Ban quản trị | Danh sách nghiệp vụ, người dùng, yêu cầu chuyển đổi đã xác nhận | Có [mẫu khảo sát](mau-khao-sat.md); cần làm việc với phòng ban |
| 2. Thu biểu mẫu và dữ liệu mẫu | Danh mục biểu mẫu, trường dữ liệu, tài liệu đầu vào | Có mẫu danh mục; cần tài liệu thực tế |
| 3. Xác định phạm vi demo | Danh sách chức năng MVP, làm trước/làm sau được chốt | Có khung ghi nhận trong mẫu khảo sát; cần quyết định của người phụ trách |
| 4. Odoo + PostgreSQL | Đăng nhập Odoo và tạo được database thử nghiệm | Đã tạo `tadic_demo`, chạy và thử đăng nhập thành công trên máy này |
| 5. Công cụ và Git | Python, Node.js, Git; repository dự án | Đã có công cụ, repository cục bộ và remote GitHub; kiểm tra đồng bộ bằng `git status` |
| 6. Tổ chức source và React | Cấu trúc Odoo/custom_addons; React chạy trang mẫu | Đã có cấu trúc, addon khung và trang mẫu responsive; `npm run build` và `npm run lint` đạt |
| 7. Dữ liệu và phân quyền | Sơ đồ dữ liệu, bảng vai trò/quyền dự kiến | Có [bản phác thảo](phac-thao-du-lieu-va-quyen.md); cần xác nhận |
| 8. Tổng hợp cho tuần 2 | Tài liệu yêu cầu rút gọn, danh sách việc kế tiếp | Đã có [mẫu tổng hợp yêu cầu/MVP](tom-tat-yeu-cau-va-mvp.md); chưa thể điền nội dung thực tế trước khảo sát và quyết định MVP |

## Phần tự chuẩn bị bổ sung

- [Quy ước thiết kế giao diện](../DESIGN.md) và khung React dùng chung đã được tạo; đây là bản mẫu, không phải màn hình nghiệp vụ đã duyệt.
- Đã thử giao diện trên desktop và điện thoại, tìm kiếm danh sách, trạng thái không có kết quả và nút xóa tìm kiếm. Giao diện chưa kết nối Odoo hay workbook.

## Bằng chứng nên lưu khi hoàn thành

- Việc 1–3: biên bản khảo sát, danh mục tài liệu được cung cấp, danh sách MVP có người xác nhận.
- Việc 4: URL Odoo hoạt động, đăng nhập và tên database thử nghiệm; không ghi mật khẩu vào tài liệu.
- Việc 5–6: link repository, lệnh chạy thành công và ảnh trang mẫu React.
- Việc 7–8: bản sơ đồ dữ liệu/quyền đã góp ý và tài liệu yêu cầu rút gọn.
