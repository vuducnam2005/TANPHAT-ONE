# Hướng dẫn Nhân sự chỉ xem và chấm công

Trong **TP HR → Chấm công**, chọn Bảng công để xem ngày/tháng của đồng nghiệp trong công ty được phép. Có bộ lọc phòng, tên/mã TP, chất lượng dữ liệu, kỳ chốt; chọn ô ngày để xem giờ. Công chưa có quy tắc hiển thị **Chưa xác nhận**, không được hiểu là 0 công, nghỉ không phép hoặc trừ lương. Nguồn hiện cập nhật đến **10/11/2026**.

**Tổng quan công** là màn mở đầu của Chấm công. Chọn kỳ/phòng/tên hoặc mãTP rồi bấm
**Áp dụng**; chip cho biết điều kiện đang dùng. KPI và biểu đồ tính theo ngày-người
đã đến, không gồm tương lai. Chọn nhóm màu/KPI hoặc cột ngày để lọc chi tiết bên dưới;
bộ lọc chất lượng/ngày/chốt chỉ đổi chi tiết, không đổi tổng kỳ phía trên. Mở ngày công
rồi quay lại giữ bộ lọc và trang. Trên điện thoại chi tiết hiển thị thẻ.

**Công của tôi** ở menu Chấm công và trong **Thông tin cá nhân → Công của tôi** dùng cùng nguồn. Hồ sơ được xác định từ tài khoản đang đăng nhập; thiếu liên kết thì liên hệ HR/admin. Chọn tháng, ngày để xem phiên vào/ra; bảng ngày có lọc chất lượng/kỳ và phân trang 10/20/50/100. Trên điện thoại mặc định xem thẻ ngày; có nút mở lịch tháng.

Nút **Xuất CSV của tôi** tải các ngày đúng tháng/chất lượng/kỳ đang lọc. Mở bằng Excel
với UTF-8; file chỉ có dữ liệu công của bạn, không chứa giải trình hoặc minh chứng.

Để bổ sung giờ, chọn ngày → **Đề nghị điều chỉnh**, nhập giờ vào/ra cùng ngày và giải trình, đính kèm minh chứng nếu có. **Lưu** chỉ lưu nháp; **Gửi duyệt** chuyển người được phân công. Chưa có người duyệt thì giữ nháp và báo HR cấu hình. **Yêu cầu của tôi** cho xem kết quả, bổ sung phiếu bị trả hoặc hủy phiếu chưa hoàn tất. Giải trình, minh chứng và ý kiến xử lý không hiện trên bảng công chung.

HR vào **Cấu hình HR → Phân công xử lý công** để giao quyền theo công ty/phòng: nhập dữ liệu, duyệt/trả điều chỉnh, chốt/mở kỳ. Không suy quyền từ chức danh. Chưa tự phân công người thật trong lần triển khai này. Quyền nhập và chốt cả kỳ cần phạm vi toàn công ty; duyệt có thể giới hạn phòng. Người duyệt không tự duyệt phiếu của mình.

Người được giao mở **Xử lý điều chỉnh**, chọn phiếu → **Duyệt** hoặc **Trả lại**. Trả lại bắt buộc lý do. Duyệt cập nhật giờ và tổng hợp trong cùng giao dịch, giữ phiên gốc đã thay thế. Nội dung riêng chỉ người đề nghị, người đang được phân công duyệt đúng phạm vi và HR quản lý có quyền được xem sau khi gửi.

**Chốt kỳ**: HR/người có phân công chốt tạo kỳ không chồng ngày, rà số ngày và đề nghị còn chờ. Phải xử lý hết phiếu đang chờ; nếu còn thiếu giờ/cần kiểm tra, phải có ghi chú khi chốt. Chốt không xác nhận quy tắc công hay lương. Mở lại cần lý do. Duyệt điều chỉnh trong kỳ chốt cần đồng thời quyền duyệt, quyền chốt và lý do đính chính; giữ lịch sử và tăng phiên bản kỳ/ngày. Chưa chốt/duyệt kỳ nghiệp vụ thật trong lần triển khai.

Nhân viên thường chỉ xem danh bạ công việc, không sửa hồ sơ/quyền/giờ và không xuất hàng loạt công đồng nghiệp. Quyền tự sửa thông tin cá nhân giữ allowlist cũ. Admin/HR giữ quyền chuyên môn hợp lệ; admin không gắn nhân viên thì không có bảng công cá nhân.

Link tương đối theo host đang dùng: [Tổng quan công](/app/cham-cong), [Bảng công](/app/bang-cong), [Công của tôi](/app/cong-cua-toi), [Hồ sơ cá nhân](/app/my-profile). Public hostname có thể đổi khi QuickTunnel đổi; dùng đường dẫn này trên host hiện hành. Sau nâng cấp, Ctrl+F5 một lần nếu còn giao diện cũ.
