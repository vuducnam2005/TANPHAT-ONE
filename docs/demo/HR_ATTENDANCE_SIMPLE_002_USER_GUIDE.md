# Hướng dẫn chấm công gọn — HR-ATTENDANCE-SIMPLE-002

Áp dụng `tp_hr_attendance` `20.0.2.0.0` (`CHG-20261118-019`). Nghiệm thu:
[HR_ATTENDANCE_SIMPLE_002_ACCEPTANCE.md](HR_ATTENDANCE_SIMPLE_002_ACCEPTANCE.md). Phiếu điều chỉnh và
chốt kỳ giữ như [hướng dẫn 001](HR_ATTENDANCE_001_USER_GUIDE.md).

## 1. Nguồn dữ liệu — hiện là Excel, không phải thời gian thực

- Nguồn duy nhất đang dùng: **file Excel xuất từ máy chấm công** do HR nhập. Dải trên đầu Tổng quan ghi
  *Excel máy chấm công*, lúc cập nhật và **dữ liệu đến ngày nào**. Số liệu chỉ mới đến ngày đó; ngày sau
  hiện *Chưa có dữ liệu*, không phải nghỉ.
- **API máy chấm công: Chưa cấu hình.** Hệ thống đã có nền để nhận dữ liệu máy (mục 6) nhưng **chưa nối
  máy thật** và không cập nhật tự động.
- Giờ làm tham chiếu `08:30–17:00` chỉ để hiển thị. **Số lần/phút đi muộn lấy nguyên từ cột "Đi muộn" của
  file máy**, đúng kỳ của file; hệ thống không tự tính đi muộn từ giờ vào.

## 2. Nhập Excel máy chấm công (HR hoặc người được giao nhập công)

1. **Nhân sự → Chấm công → Tổng quan chấm công** (hoặc Bảng chấm công) → nút **Nhập Excel máy chấm công**.
2. Kéo-thả hoặc chọn file `.xlsx` xuất từ máy. Hệ thống **tự đọc và hiện xem trước — chưa ghi gì**:
   kỳ trong tệp (vd *09/11/2026 – 15/11/2026, 7 ngày*), số người trong tệp/đã khớp hồ sơ, dòng mới/trùng/
   thiếu giờ/tên khác hồ sơ/xung đột, và tổng đi muộn đọc được.
3. Kiểm phần cần chú ý rồi bấm **Nhập dữ liệu**. Muốn bỏ: **Hủy** hoặc chọn file khác — lô xem trước bị
   hủy, không ghi gì.
4. Nhập lại cùng file: hệ thống báo *đã nhập trước đó*, mọi dòng là *Trùng* và nút Nhập bị khóa.

Quy tắc an toàn: chỉ khớp người theo **mã máy + họ tên**; tên khác hồ sơ → *Tên khác hồ sơ*, không tự gán.
Không tạo người, không đổi phòng/mã. Cùng ngày nhưng giờ khác dữ liệu cũ → *Xung đột*, không ghi đè.
Kỳ đã chốt không ghi. Lịch sử lô ở **Quản trị chấm công → Nhập dữ liệu**.

## 3. Tổng quan chấm công — xem ngày / tuần / tháng

- Mặc định là **Hôm nay**. Nếu hôm nay chưa có dữ liệu, bấm **Xem ngày có dữ liệu gần nhất**.
- Nút **Ngày / Tuần / Tháng** đổi chế độ; mũi tên ‹ › lùi/tiến một ngày/tuần/tháng; ô ngày (tháng ở chế độ Tháng) để chọn mốc; **Hôm nay** quay về hôm nay.
  Tuần luôn từ **Thứ 2 đến Chủ nhật**.
- **Ngày**: donut trạng thái, mẫu số ở giữa là **Tổng nhân viên**. Bấm một lát → danh sách đúng nhóm đó.
- **Tuần / Tháng**: biểu đồ cột theo từng ngày; bấm cột → danh sách người của ngày đó. Các chip đếm
  **người khác nhau** trong kỳ (vd *Người có ngày cần kiểm tra*), không cộng ngày-người.
- Danh sách có tìm/lọc phòng và chọn 10/20/50/100 dòng mỗi trang.

## 4. Định nghĩa trạng thái

| Trạng thái | Nghĩa | Không có nghĩa |
|---|---|---|
| **Tổng nhân viên** | Hồ sơ HR đang hoạt động trong phạm vi bạn được xem | Không đếm tài khoản đăng nhập, không chỉ người có trong Excel |
| **Nghỉ đã xác nhận** | Chỉ khi có nguồn nghỉ đã duyệt. Hiện chưa có nguồn này → **Chưa đủ dữ liệu** | Ô trống trong Excel **không phải** nghỉ |
| **Đã ghi nhận ra** | Có lượt ra hợp lệ mới nhất của ngày (đủ giờ vào và ra). Với hôm nay: *có thể còn quay lại* | Không khẳng định "đã về hẳn" khi chưa hết ngày |
| **Đang làm (theo mốc nguồn)** | Lượt cuối là vào, chưa có ra, **của hôm nay** | Không dùng cho ngày đã qua (ngày cũ thiếu giờ ra → *Thiếu giờ vào/ra*) |
| **Thiếu giờ vào/ra** | Có giờ vào nhưng thiếu giờ ra (hoặc ngược lại) | Hệ thống không tự điền 17:00 |
| **Cần kiểm tra** | Ký hiệu thay giờ, chiều không rõ, xung đột | — |
| **Chưa chấm công** | Ngày có nguồn nhưng người đó không có lượt nào | Không phải nghỉ |
| **Chưa có dữ liệu** | Chưa có file/nguồn phủ ngày đó cho người đó | Không phải nghỉ |
| **Chưa đến** | Ngày tương lai | Không tính nghỉ, không vẽ trên biểu đồ |

## 5. Bảng chấm công tối giản

- **Ngày**: Nhân viên (tên + mã), Phòng ban, Thứ/ngày, Giờ vào, Giờ ra. Thiếu giờ hiện `—`.
- **Tuần / Tháng / Kỳ theo file**: mỗi người một dòng — Số lần đi muộn, Tổng phút muộn.
  - Chọn **đúng kỳ của file** (nút kỳ trong menu *Kỳ theo file*, vd *09–15/11*) → hiện số kèm nhãn
    *Theo Excel máy · kỳ 09–15/11*.
  - Xem một ngày hoặc một phần kỳ → *Số đi muộn có ở tổng kỳ 09–15/11* + nút xem tổng kỳ; **không chia**
    tổng cho từng ngày và không hiện 0.
  - Xem tháng mà chưa có file tháng → *Chưa có tổng đi muộn đúng kỳ Tháng …*; hệ thống **không cộng các
    tuần** để ra tháng.
- Bấm tên người → chi tiết kỳ: 2 chỉ số đi muộn và bảng Thứ/ngày – Giờ vào – Giờ ra.
- **Xuất Excel**: sheet giờ theo ngày; thêm sheet Tổng đi muộn khi đang xem đúng kỳ nguồn.
- **Công của tôi**: nhân viên xem và xuất phần của chính mình (lấy theo tài khoản đăng nhập).

## 6. Nền API máy — đã chuẩn bị gì, còn cần gì

Đã có (chưa kết nối): bảng sự kiện thô bất biến; chuẩn hóa mã trên máy (giữ số 0 đầu), thời điểm + múi
giờ, chiều Vào/Ra/Chưa rõ; chống trùng khi máy gửi lại; gắn nhân viên chỉ qua bảng mã của đúng nguồn;
mốc đã nhận chỉ tiến khi đã ghi. Kết nối trực tiếp bị khóa; không có lịch tự chạy, không có địa chỉ web
nhận công, không lưu mật khẩu/khóa trong mã nguồn.

Cần HR/IT lấy từ hãng máy (trang **Quản trị chấm công → Nguồn dữ liệu** liệt kê đủ 9 mục): hãng/model/
firmware; có API/SDK hay chỉ xuất file + tài liệu; máy gửi chiều Vào/Ra hay chỉ lượt quẹt; mã sự kiện/con
trỏ đọc tiếp; múi giờ và định dạng thời điểm; mạng của máy và chiều kéo/đẩy; cách xác thực; tần suất đồng
bộ; ca làm/ca qua đêm và cách chốt ngày. Có đủ thông tin mới viết adapter và kiểm trên máy thật.
