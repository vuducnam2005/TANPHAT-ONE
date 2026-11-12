# KD-UI-007 — Tự kiểm bảng KH-KD

Mở [TANPHAT ONE dev](http://127.0.0.1:18069), đăng nhập bằng tài khoản hiện có và nhấn **Ctrl+F5** để lấy assets mới. Vào Kế hoạch Kinh doanh. Các nút, bảng tiền và hồ sơ nhìn thấy phụ thuộc quyền backend hiện có.

1. Mở từng mục trong sidebar: Cơ hội, Dự án, Hợp đồng, Công việc, Giao khoán, Sản lượng, Nghiệm thu, Kế hoạch định kỳ, Thanh toán, Chứng chỉ và Nghĩa vụ. Quan sát hàng Bộ lọc, lựa chọn Trường lọc và nút Bộ lọc nâng cao. Trên điện thoại, nhấn **Bộ lọc** để mở vùng nhập.
2. Chọn một trạng thái hoặc chọn trường phù hợp rồi nhập giá trị và Enter/Áp dụng. Điều kiện xuất hiện thành chip của Odoo; gỡ chip hoặc nhấn **Xóa bộ lọc**. Search chính tìm các trường mà search view của bảng cho phép. Tất cả trong quyền vẫn giữ ràng buộc action/dự án/công ty.
3. Chọn **Hiển thị 10 dòng mỗi trang**, dùng mũi tên Trước/Sau để xem tiếp; thử 20/50/100. Số dòng tối đa là mức đã chọn. Khi nhóm dữ liệu, nhãn đổi thành **nhóm mỗi trang**; pager của từng nhóm vẫn do Odoo quản lý. Lựa chọn được nhớ riêng cho database, người dùng và action/view. Tùy chọn bảng chứa mật độ và khôi phục cột.
4. Mở chi tiết, xem các notebook và smart button. Ở bảng con đã lưu, chọn số dòng hoặc **Tìm / lọc toàn bộ bảng**: hộp lọc tìm trên toàn quan hệ, không chỉ trang đang tải. Khi tạo mới/đang sửa, control bị khóa và ghi **Lưu thay đổi để lọc**; dùng Lưu/Hủy native trước. Lịch sử, audit và snapshot giá trị vẫn chỉ đọc; tiền chỉ hiện theo grant.
5. Vào Tổng quan/Báo cáo, thử lọc chung, bảng dự án và Việc của tôi với 10/20/50/100. Bảng nguồn là 10 nhóm cấu trúc cố định. So sánh kế hoạch xem trước tối đa 12, chứng chỉ gần hạn tối đa 5; dùng liên kết mở danh sách đầy đủ để tìm/lọc/phân trang. Việc của tôi hợp nhất tối đa 500 dòng theo giới hạn hiện có, cần thu hẹp bộ lọc hoặc mở nguồn khi chạm giới hạn.

Màu có chữ đi kèm: xám nháp/hủy, xanh dương đang tìm hiểu/rà soát, tím chuẩn bị/thực hiện, vàng chờ bổ sung/chưa xác minh, đỏ trả lại/quá hạn, xanh lá cho giá trị hoàn thành/kiểm nội bộ thực có trong field. **Đã khai báo nộp — chưa xác minh** không có nghĩa trúng thầu; còn hạn không có nghĩa năng lực đã xác minh; đề nghị thanh toán không có nghĩa đã thu/chi tiền. Ngưỡng chứng chỉ 30 ngày vẫn là minh họa.

Đây là hướng dẫn kiểm kỹ thuật giao diện dev. Người dùng quyết định nghiệm thu hình thức; nghiệm thu nghiệp vụ, audit độc lập và cho phép pilot là các cổng riêng. Phạm vi tất cả bảng KD-UI-007 thay hướng bốn màn KD-UI-006; mockup cũ chưa được coi là đã duyệt.
