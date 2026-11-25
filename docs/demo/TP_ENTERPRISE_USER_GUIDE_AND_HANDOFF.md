# TANPHAT ONE — Hướng dẫn vận hành theo vai trò & Nghiệm thu kỹ thuật Đề án Quản trị Doanh nghiệp

Tài liệu hướng dẫn ngắn gọn theo vai trò và tổng hợp kết quả triển khai thực tế toàn bộ phạm vi Đề án Quản trị Doanh nghiệp trên nền tảng **TANPHAT ONE** (Odoo 20 Native + OWL/QWeb/SCSS, dùng chung 1 CSDL PostgreSQL, tài khoản, nhân sự, phòng ban, đối tác, dự án và session).

---

## 1. Hướng dẫn sử dụng nhanh theo vai trò

### 1.1. Cán bộ / Kỹ sư Thiết kế – Khảo sát (Nhân viên nội bộ)
- **Công việc của tôi (`/app/ca-nhan/cong-viec`):**
  - Xem hợp nhất trên một màn hình duy nhất: việc tự tạo, việc dự án/WBS được giao, đầu việc từ Biên bản họp, việc từ Yêu cầu phê duyệt và việc chuyển từ tin nhắn Trao đổi (**0 bản sao trùng**).
  - Dùng dải nút lọc nguồn (`Tất cả nguồn`, `Tự tạo`, `Dự án`, `Cuộc họp`, `Yêu cầu`, `Trao đổi`); kéo thả thẻ giữa các giai đoạn cá nhân của riêng mình mà không làm xáo trộn giai đoạn dự án hay bảng của đồng nghiệp.
  - Bấm **Báo hoàn thành** kèm kết quả đầu ra (`tp_reported_result`); công việc dự án/cuộc họp chỉ khóa nghiệm thu nội bộ khi người giao bấm **Xác nhận kết quả**.
- **Lịch làm việc & Đặt phòng họp (`/app/ca-nhan/lich-lam-viec`):**
  - Chọn loại lịch (`Cá nhân`, `Họp`, `Công tác / Hiện trường`, `Lịch phòng / Công ty`), gắn Dự án và chọn **Phòng họp nội bộ** (hệ thống khóa chống đặt trùng giờ đồng thời).
- **Trao đổi (`/app/ca-nhan/trao-doi`):**
  - Nhắn tin trực tiếp 1–1, nhóm theo Dự án/Phòng ban; bấm **Tạo công việc** ngay trên tin nhắn để giao việc có liên kết ngược về tin nhắn gốc; kiểm tra thanh tệp chờ gửi trước khi bấm Gửi.
- **Thông báo nội bộ (`/app/van-phong-so/thong-bao`):**
  - Đọc các quyết định/thông báo trong phạm vi nhận và bấm nút tường minh **`✓ Xác nhận đã đọc (vN)`** (chỉ mở trang sẽ không tự đánh dấu đã đọc; khi văn bản nâng phiên bản lớn cần xác nhận lại).
- **Yêu cầu phê duyệt (`/app/de-nghi/cua-toi`):**
  - Gửi đề nghị **Nghỉ phép**, **Công tác hiện trường**, **Tạm ứng / Thanh toán chi phí**, **Thiết bị**, **Hỗ trợ IT** hoặc **Điều chỉnh công** với xem trước tuyến duyệt trực tiếp.

### 1.2. Chủ nhiệm Dự án (PM) & Trưởng bộ phận Kỹ thuật
- **Tiến độ WBS & Đường găng CPM (`/app/du-an/wbs-tien-do`):**
  - Áp dụng tùy chọn **Mẫu WBS Cầu Đường** (`Khảo sát → BCNCKT → TKKT → TKBVTC → Thẩm tra/GSTG`), khai báo tiền nhiệm DAG + thời lượng và bấm **Tính lại Đường găng CPM** (`ES/EF/LS/LF/Float` thực tế).
  - Bấm **Đóng băng Baseline** khi chốt kế hoạch; mọi điều chỉnh mốc tiến độ sau đó đều bắt buộc nhập lý do vào nhật ký kiểm toán.
  - Theo dõi tách bạch **4 trạng thái sản phẩm**: *1. Báo xong* → *2. Xác nhận kết quả* → *3. Phát hành hồ sơ* → *4. Nghiệm thu khối lượng* (báo xong công việc không bao giờ tự sinh giá trị nghiệm thu/thanh toán).
- **Hồ sơ dự án & NAS (`/app/du-an/ho-so-nas`):**
  - Khởi tạo cây thư mục chuẩn theo **Mã dự án cố định** (ký hợp đồng thứ 2 không tạo trùng thư mục gốc), tải phiên bản bản vẽ/thuyết minh kèm mã kiểm tra SHA-256 và tải tệp qua đường dẫn kiểm quyền `/tp/dossier/download/<id>`.
- **Biên bản họp (`/app/van-phong-so/bien-ban-hop`):**
  - Mở trực tiếp từ nút **Biên bản họp** trên Lịch họp (tự động điền thành phần & dự án), nhập kết luận và bấm **Phát hành & Sinh đầu việc** (sinh công việc đúng 1 lần; hiệu chỉnh sau phát hành bắt buộc ghi lý do và không xóa việc đã giao).
- **Kế hoạch & Báo cáo (`/app/bao-cao`):**
  - Lập kế hoạch theo chuỗi **Năm → Quý → Tháng → Tuần**; nạp kết quả công việc vào báo cáo nháp mà không làm biến đổi snapshot của các kỳ báo cáo đã nộp trước đó.

### 1.3. Quản trị Nhân sự, Tuyển dụng & Thiết bị
- **Tuyển dụng (`/app/tuyen-dung`, thẻ Trang chủ `Tuyển dụng`):**
  - Quản lý nhu cầu tuyển dụng phòng ban, kéo/chuyển vòng ứng viên (không tự sinh nhân viên), lập lịch phỏng vấn và bấm **Tiếp nhận** qua bước kiểm trùng CCCD/Email/SĐT (chỉ tạo `hr.employee`, không tự tạo tài khoản hay quyền Admin).
- **Chứng chỉ hành nghề thống nhất & Chấm công (`/app/nhan-su`, `/app/cham-cong`):**
  - Khai báo chứng chỉ hành nghề cá nhân ngay trên hồ sơ kỹ năng/chứng chỉ nhân sự (`hr.employee.skill`) kèm cảnh báo sắp hết hạn và đồng bộ sang Hồ sơ năng lực đấu thầu (`tp.credential`) không trùng bảng.
  - Đơn **Nghỉ phép / Công tác** đã duyệt tự động cập nhật căn cứ nghỉ trên bảng công mà không giả tạo punch; nếu ngày nghỉ vẫn có punch máy sẽ tự bật cờ **`Cần kiểm tra`**.
- **Thiết bị khảo sát (`/app/thiet-bi/khao-sat`) & Đối soát lương (`/app/nhan-su/doi-soat-luong`):**
  - Theo dõi hạn kiểm định máy toàn đạc/RTK/thủy chuẩn và tự động chặn xuất dùng hiện trường khi máy hỏng hoặc quá hạn kiểm định.
  - Tổng hợp bảng đối soát đầu vào lương (công xác nhận + nghỉ phép + công tác); khóa tính lương thực lĩnh cho đến khi Quy chế tiền lương chính thức được phê duyệt.

### 1.4. Ban Giám đốc & Tài chính Quản trị
- **Dashboard Điều hành Lãnh đạo (`/app/dieu-hanh/tong-quan`):**
  - Theo dõi điểm nghẽn phê duyệt, tiến độ trọng số & việc găng của danh mục dự án, tải công việc nhân sự trung thực, và **11 chỉ tiêu tài chính quản trị tách biệt** có nguồn chứng từ gốc (hiển thị rõ `Chưa đủ dữ liệu` khi thiếu nguồn, không giả lập số `0`).
- **Trợ lý AI Nội bộ có RBAC (`/app/dieu-hanh/tro-ly-ai`):**
  - Tra cứu có trích dẫn nguồn tuân thủ tuyệt đối quyền ORM của người đang đăng nhập; loại trừ lương và hợp đồng mật; mọi thao tác tạo nháp luôn qua bước xem trước & xác nhận.

---

## 2. Tổng hợp 5 Cổng quy chế / Hạ tầng chờ xác nhận trước khi bật tự động hóa sâu

1. **Quy chế Tiền lương, BHXH & Thuế TNCN (`tp.payroll.policy`):** Hiện đang để trạng thái `pending_approval`; bảng đối soát đầu vào lương đã hoạt động, công thức tính lương thực trả sẽ mở ngay khi Ban Giám đốc phê duyệt tham số chính thức.
2. **Thu thập GPS / Selfie chấm công hiện trường (`tp.field.checkin`):** Đã chuẩn bị schema tách biệt khỏi ảnh hồ sơ HR và sinh trắc học; mặc định tắt (`tp_attendance.field_gps_enabled = 0`) cho đến khi ban hành quy chế quyền riêng tư & thời hạn lưu trữ.
3. **Đồng bộ SMB trực tiếp lên ổ NAS vật lý (`tp.nas.folder.job`):** Hàng đợi cấu trúc thư mục chuẩn idempotent theo `project_id` và kho phiên bản ACL trên Odoo đã vận hành; kết nối ghi file SMB trực tiếp chờ cấu hình thông số mạng NAS (`tp_nas.smb_enabled`).
4. **Kết nối LLM bên ngoài cho Trợ lý AI (`tp.ai.assistant`):** Chế độ tra cứu nội bộ có trích dẫn theo RBAC đã hoạt động đầy đủ; kết nối API LLM đám mây tắt mặc định (`tp_ai.external_llm_enabled = 0`) chờ chốt nhà cung cấp, ngân sách và chính sách dữ liệu.
5. **Tài khoản đăng nhập & Quyền Admin (`DEC-053/054/062`):** Mọi luồng nghiệp vụ giữ nguyên tắc chỉ **Admin gốc** được cấp/thu quyền Admin; tiếp nhận ứng viên không tự sinh `res.users`.
