# TANPHAT ONE — Hướng dẫn sử dụng Phân hệ Báo cáo KH-KD (KD-REPORT-001)

Tài liệu hướng dẫn thao tác chi tiết dành cho người dùng nghiệp vụ thuộc Khối Kế hoạch - Kinh doanh (KH-KD) và các phòng ban liên quan trong TANPHAT ONE.

---

## 1. Tổng quan & Sự khác biệt giữa hai màn hình

Theo kiến trúc chuẩn hóa sau phân tách **KD-REPORT-001**:
* **Tổng quan KH-KD (`menu_overview`)**:
  - **Mục tiêu**: Điều hành, giám sát hoạt động hằng ngày, theo dõi phễu công việc, các việc cần xử lý gấp (SLA, việc của tôi) và các chỉ tiêu nhanh.
  - **Dữ liệu**: Tập trung vào trạng thái tức thời (real-time workspace).
* **Báo cáo KH-KD (`menu_reports`)**:
  - **Mục tiêu**: Tổng hợp định kỳ (tháng, quý, năm hoặc tùy chọn), đối chiếu số liệu đa chiều, gom nhóm dữ liệu và xuất file Excel chuẩn báo cáo quản trị.
  - **Dữ liệu**: Báo cáo tổng thể toàn bộ phạm vi được phân quyền, hỗ trợ phân trang (10, 20, 50, 100 dòng), tìm kiếm không dấu và tải toàn bộ dữ liệu ra Excel.

---

## 2. Truy cập màn hình Báo cáo KH-KD

1. Đăng nhập vào hệ thống TANPHAT ONE.
2. Từ menu ứng dụng chính, chọn **TP Projects** (hoặc phân hệ KH-KD).
3. Trên thanh điều hướng bên trái (Sidebar), nhấn vào mục **Báo cáo KH-KD**:
   - Biểu tượng: `table_chart`
   - Đường dẫn menu: `tp_kd_workspace.menu_reports`
   - Giao diện mở ra: **Trung tâm Báo cáo KH-KD** (`tp.kd.report.center`).

---

## 3. Cấu trúc 6 Nhóm Báo cáo Chuyên sâu (R01 – R06)

Người dùng chuyển đổi giữa các nhóm báo cáo bằng cách click vào các tab ở thanh trên cùng hoặc dùng phím tắt (`ArrowLeft`, `ArrowRight`, `Home`, `End`):

### 3.1. R01: Dự án và hợp đồng
* **Câu hỏi nghiệp vụ**: Mỗi dự án có bao nhiêu hợp đồng/phiên bản, trạng thái hiệu lực và giá trị hợp đồng hiệu lực là bao nhiêu?
* **Quy tắc tính tiền**:
  - Chỉ tính giá trị tại **phiên bản hiệu lực hiện hành (`_effective_revision`)** đã xác nhận tiền.
  - Tách riêng giá trị HĐ gốc (`Original`) và phụ lục (`Amendment`).
  - **Tuyệt đối không cộng gộp** bản gốc + phụ lục + đính chính nhằm tránh tính trùng lặp.
  - Các bản nháp, đang rà soát hoặc bị trả lại được tách thành chỉ tiêu "Phiên bản đang xử lý" và không cộng vào giá trị hiệu lực.

### 3.2. R02: Cơ hội và hồ sơ thầu
* **Câu hỏi nghiệp vụ**: Có bao nhiêu cơ hội/hồ sơ thầu theo từng trạng thái chuẩn bị và nộp thầu; cơ hội nào chưa gắn dự án?
* **Đặc điểm nổi bật**:
  - Hỗ trợ xem danh sách lớn (>100 cơ hội) với phân trang mượt mà (10/20/50/100).
  - Bộ lọc dự án hỗ trợ tùy chọn: **"Chưa gắn dự án (tiền dự án)"**.
  - Cột tiến độ nộp thầu và hạn nộp (`kd_deadline`) cảnh báo rõ các hồ sơ quá hạn nộp.

### 3.3. R03: Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán
* **Câu hỏi nghiệp vụ**: Tiến độ thực hiện và dòng tiền giữa 4 giai đoạn đang lệch nhau như thế nào?
* **Quy tắc cốt lõi**:
  - **4 cột độc lập đặt cạnh nhau**: Kế hoạch kỳ, Sản lượng thi công, Nghiệm thu kỹ thuật, Đề nghị thanh toán.
  - **Tuyệt đối không cộng dồn** các giai đoạn này với nhau.
  - Tách bạch rõ giữa tiền đề nghị thanh toán và dòng tiền thực thu/thực chi từ sổ kế toán.

### 3.4. R04: Giao khoán và thầu phụ
* **Câu hỏi nghiệp vụ**: Tỷ lệ giao khoán nội bộ và thầu phụ so với giá trị hợp đồng là bao nhiêu; có vượt mức cho phép không?
* **Quy tắc phân cấp**:
  - Tách bạch rõ ràng giữa **Khoán cấp 1 (Parent)** và **Khoán cấp 2 (Child)**.
  - Hiển thị tỷ lệ khoán / giá trị hợp đồng hiệu lực.
  - Cảnh báo trạng thái vượt mức (`overrun`) khi tỷ lệ giao khoán chạm ngưỡng cảnh báo.

### 3.5. R05: Tình trạng xử lý và trách nhiệm hồ sơ
* **Câu hỏi nghiệp vụ**: Hồ sơ, tờ trình, công việc nào đang chậm xử lý, quá hạn hoặc đến hạn; ai chịu trách nhiệm?
* **Phạm vi tổng hợp**: Quét qua 10 nguồn nghiệp vụ (Hợp đồng, Phụ lục, Đính chính, Kế hoạch, Sản lượng, Nghiệm thu, Đề nghị thanh toán, Cơ hội, Công việc, Hồ sơ rà soát).
* **Nhãn SLA**:
  - `Quá hạn xử lý` (Đỏ): Quá ngày hạn mốc quy định.
  - `Đến hạn ≤ 3 ngày` (Vàng): Cần ưu tiên xử lý gấp.
  - `Trong hạn` (Xanh): Đang tiến hành bình thường.
  - `Chưa đặt hạn` (Xám): Cần bổ sung thời hạn xử lý.

### 3.6. R06: Năng lực, chứng chỉ và nghĩa vụ hồ sơ
* **Câu hỏi nghiệp vụ**: Doanh nghiệp và nhân sự có những chứng chỉ/hồ sơ nào sắp hết hạn (≤ 30 ngày); nghĩa vụ hồ sơ nào còn thiếu?
* **Quy tắc bảo mật & phân định**:
  - Phân loại rõ **Chứng chỉ tổ chức** (công ty) và **Chứng chỉ cá nhân** (nhân sự).
  - Chứng chỉ cá nhân được phân quyền nghiêm ngặt: chỉ người sở hữu, người rà soát hoặc Quản trị viên mới xem được.
  - Đếm số lượng chứng chỉ duy nhất, không nhân bản khi gắn với nhiều cơ hội thầu.
  - Báo cáo này không có cột tiền (`money_keys = ()`).

---

## 4. Hướng dẫn Lọc, Gom nhóm, Sắp xếp & Phân trang

### 4.1. Bộ lọc cơ chế Hai Pha (Pending vs Applied)
Nhằm tránh tình trạng gửi request liên tục khi người dùng đang chọn nhiều điều kiện lọc:
1. Khi thay đổi bộ lọc (Preset kỳ, Ngày từ - đến, Dự án, Người phụ trách, Trạng thái, Phân loại):
   - Thanh cảnh báo **"Bộ lọc đang chọn đã thay đổi — bấm Áp dụng bộ lọc để cập nhật bảng và xuất Excel"** sẽ xuất hiện.
2. Nhấn nút xanh **Áp dụng bộ lọc** (phím nóng Enter trong form lọc) để tải dữ liệu mới.
3. Nhấn **Đặt lại** để quay về bộ lọc mặc định.

### 4.2. Gom nhóm dữ liệu (Group By)
* Dropdown **Nhóm theo**: Hỗ trợ gom nhóm linh hoạt theo Dự án, Trạng thái, Người phụ trách, Loại hồ sơ...
* Dòng nhóm hiển thị tổng số bản ghi và tổng giá trị tiền riêng biệt của từng nhóm.

### 4.3. Chọn số dòng hiển thị (Page Size) & Phân trang
* Phía dưới chân bảng, chọn số dòng: **10 dòng/trang, 20 dòng/trang, 50 dòng/trang, 100 dòng/trang**.
* Sử dụng các nút điều hướng trang: `Trang đầu`, `Trước`, các số trang và `Trang cuối`.

### 4.4. Mở hồ sơ nguồn (Drill-down)
* Mọi tên hợp đồng, tên cơ hội, mã công việc, số đề nghị thanh toán đều là **liên kết clickable (màu xanh)**.
* Click vào liên kết để mở trực tiếp Form View của hồ sơ gốc để xử lý.
* Khi nhấn nút quay lại (Breadcrumbs), trạng thái tab báo cáo và bộ lọc trước đó được bảo lưu nguyên vẹn.

---

## 5. Xuất Báo cáo Excel Chuẩn Quản trị

1. Thiết lập bộ lọc và nhóm dữ liệu mong muốn.
2. Nhấn nút **Xuất Excel toàn bộ** trên thanh công cụ.
3. File Excel tải về có cấu trúc 3 phần chuẩn hóa:
   - **Phần Header**: Tiêu đề hệ thống TANPHAT ONE, câu hỏi nghiệp vụ, ngày giờ xuất, người xuất, kỳ lọc, dự án lọc, ghi chú cơ sở thuế và loại trừ.
   - **Phần I — Chỉ tiêu tổng hợp**: Bảng tóm tắt các KPI toàn phạm vi lọc.
   - **Phần II — Tổng hợp theo nhóm**: Bảng số liệu tổng hợp theo tiêu chí gom nhóm.
   - **Phần III — Chi tiết toàn bộ**: Danh sách đầy đủ toàn bộ kết quả lọc (không bị giới hạn bởi phân trang hiển thị trên màn hình).
4. **An toàn công thức (Formula Injection Protection)**:
   - Toàn bộ dữ liệu text bắt đầu bằng `=`, `+`, `-`, `@` đều được hệ thống tự động escape bằng dấu `'` để ngăn chặn rủi ro mã độc macro khi mở file trong Microsoft Excel.
5. **Tuân thủ phân quyền**:
   - Người dùng không có quyền xem tiền (ví dụ Nhân viên hỗ trợ) khi xuất Excel sẽ nhận file có nhãn ghi chú bảo mật và toàn bộ số tiền được thay thế bằng chuỗi `"Không có quyền xem tiền"`.
