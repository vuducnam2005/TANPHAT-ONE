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

Để bổ sung giờ, chọn ngày → **Đề nghị điều chỉnh**, nhập giờ vào/ra cùng ngày và giải trình, đính kèm minh chứng nếu có. **Lưu** chỉ lưu nháp, chưa đổi bảng công; **Gửi duyệt** chuyển phiếu sang **Chờ admin duyệt** và gửi Admin chính (admin gốc) của công ty. Chưa có Admin chính đang hoạt động thì phiếu giữ nháp; liên hệ quản trị hệ thống. **Yêu cầu của tôi** hiện trạng thái, người xử lý, thời điểm xử lý và nhận xét; cho bổ sung phiếu bị trả hoặc hủy phiếu chưa hoàn tất. Giải trình, minh chứng và ý kiến xử lý không hiện trên bảng công chung.

HR vào **Cấu hình HR → Phân công xử lý công** để giao quyền theo công ty/phòng: nhập dữ liệu, xuất bảng công trong phạm vi, chốt/mở kỳ. Không suy quyền từ chức danh. Chưa tự phân công người thật trong lần triển khai này. Quyền nhập và chốt cả kỳ cần phạm vi toàn công ty; xuất bảng công có thể giới hạn phòng. Phân công không cho quyền duyệt/trả điều chỉnh công.

Admin mở **Quản trị chấm công → Xử lý điều chỉnh**. Admin ở đây là Admin chính (admin gốc) và admin được ủy quyền đang hiệu lực ở công ty đó. Danh sách toàn công ty có nhân viên, phòng ban, ngày, giờ hiện tại, giờ đề nghị, lý do và minh chứng. Bấm **Duyệt** hoặc **Trả lại** trên dòng hoặc trong phiếu; trả lại bắt buộc lý do, nhân viên sửa rồi gửi lại. Trưởng phòng, HR và người được phân công không có quyền admin thì không duyệt được; không ai tự duyệt phiếu của mình. Admin bị thu hồi quyền mất quyền xem và duyệt ngay; cấp/thu hồi quyền admin vẫn chỉ Admin chính làm. Duyệt cập nhật giờ và tổng hợp trong cùng giao dịch, chỉ báo thành công sau khi lưu xong, giữ phiên gốc đã thay thế. Tệp Excel nhập sau không ghi đè ngày đã điều chỉnh. Nội dung riêng chỉ người đề nghị, admin nhận duyệt và HR quản lý xem được sau khi gửi.

**Chốt kỳ**: HR/người có phân công chốt tạo kỳ không chồng ngày, rà số ngày và đề nghị còn chờ. Phải xử lý hết phiếu đang chờ; nếu còn thiếu giờ/cần kiểm tra, phải có ghi chú khi chốt. Chốt không xác nhận quy tắc công hay lương. Mở lại cần lý do. Duyệt điều chỉnh trong kỳ chốt cần admin (gốc hoặc được ủy quyền) có thêm phân công chốt và lý do đính chính; giữ lịch sử và tăng phiên bản kỳ/ngày. Chưa chốt/duyệt kỳ nghiệp vụ thật trong lần triển khai.

Nhân viên thường chỉ xem danh bạ công việc, không sửa hồ sơ/quyền/giờ và không xuất hàng loạt công đồng nghiệp. Quyền tự sửa thông tin cá nhân giữ allowlist cũ. Admin/HR giữ quyền chuyên môn hợp lệ; admin không gắn nhân viên thì không có bảng công cá nhân.

Link tương đối theo host đang dùng: [Tổng quan công](/app/cham-cong), [Bảng công](/app/bang-cong), [Công của tôi](/app/cong-cua-toi), [Hồ sơ cá nhân](/app/my-profile). Public hostname có thể đổi khi QuickTunnel đổi; dùng đường dẫn này trên host hiện hành. Sau nâng cấp, Ctrl+F5 một lần nếu còn giao diện cũ.
