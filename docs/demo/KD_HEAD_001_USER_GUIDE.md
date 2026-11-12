# KH-KD — Hướng dẫn HEAD quản lý nghiệp vụ trong phòng

Ngày10/11/2026. **Đã áp KD-HEAD-001 lên18069**: workspace20.0.1.9.0,
contract20.0.1.3.0. Dùng tài khoản HEAD hiện có; Ctrl+F5 một lần để nạp asset mới.
Bảng quyền và bằng chứng ở [acceptance](KD_HEAD_001_ACCEPTANCE.md).

Vào [TANPHAT ONE](http://127.0.0.1:18069/odoo) bằng tài khoản hiện có của HEAD.
Giữ mật khẩu/MFA/passkey; danh tính và credential do người vận hành giữ private.
Chọn **Kế hoạch Kinh doanh**. Hai mục **Quản lý dự án** và **Quản trị dự án** dùng
cùng project ID: mục đầu phục vụ WBS/công việc/tiến độ, mục sau phục vụ hồ sơ
thương mại/hợp đồng/khoán/kế hoạch/sản lượng/nghiệm thu/đề nghị thanh toán/nghĩa vụ.

## Dự án, người phụ trách và công việc

1. Mở danh sách Dự án, chọn **Tạo dự án KH-KD**. Dự án mới phải đúng mã,
   công ty và phòng KH-KD đã provision. HEAD có scope động, không cần thêm grant
   cho chính mình mỗi khi có dự án mới thuộc phòng.
2. Trong chi tiết, dùng **Cập nhật thông tin**, **Cập nhật tình trạng**,
   **Thêm ghi chú** theo nút thực tế được cấp. Ghi lý do; dừng/mở lại qua action,
   không sửa trực tiếp state hoặc coi Kết thúc là hiệu lực pháp lý.
3. Dùng **Phân công chủ trì** để đổi người phụ trách. Người nhận phải đang có
   quyền đọc hợp lệ trên hồ sơ/dự án và thuộc tập nghiệp vụ phù hợp. Chọn một
   người trong phòng không tự cấp cho họ quyền dự án mới; cần người vận hành
   xử lý quyền riêng nếu danh sách chưa có người cần giao.
4. Vào WBS/công việc: **Sửa hạng mục**, **Giao việc**, **Cập nhật tiến độ**.
   HEAD được cập nhật thay người thực hiện trong scope, ghi lý do; lịch sử giữ
   riêng người làm và người cập nhật. Xem **Xem lịch sử thực hiện** để đối chiếu.

## Hồ sơ, hợp đồng và tiền

- Mở nhóm hồ sơ cần làm, chọn **Mới**; chọn dự án/phòng/công ty đúng scope.
  Bản nháp/returned được sửa theo workflow. Can thiệp hồ sơ của nhân viên cần
  lý do; giữ owner và audit, không đổi owner chỉ để có nút sửa.
- Gửi hoặc gửi lại qua nút workflow, điền reviewer/căn cứ/tóm tắt sửa theo form.
  HEAD được rà soát/trả lại hồ sơ người khác toàn phòng qua action có lý do.
  Bản đang rà soát hoặc đã chốt phải theo luồng trả lại/mở sửa hợp lệ.
- HEAD không tự rà soát hồ sơ do mình gửi hoặc cùng phiên bản mình đã can thiệp
  khi workflow yêu cầu người khác kiểm. Chọn reviewer hợp lệ khác; hệ thống
  không auto-pass điều kiện bốn mắt.
- Với hợp đồng, mở **Bản gốc/phụ lục** rồi chọn phiên bản. Dùng **Chỉnh sửa nháp**,
  **Trình rà soát** hoặc **Trình rà soát lại**; chọn reviewer khác và ghi tóm tắt sửa
  khi gửi lại. Muốn xử lý hồ sơ khác reviewer cũ, dùng **Nhận rà soát** có lý do,
  rồi **Trả lại** khi cần bổ sung. Người đã gửi/can thiệp cùng vòng không tự review.
- Hợp đồng dùng form native để lập/sửa tiền nháp/gửi. Hộp **Điều phối và tài
  liệu hợp đồng** phục vụ phân công/tài liệu/trả lại theo thao tác chọn trên form.
  Việc rà soát KH-KD chưa là ký kết, hiệu lực, duyệt BASE hoặc hạch toán.
- Phân biệt giá cả gói, giá công ty chào và phần tham gia; tiền chưa xác định
  khác số0. Kế hoạch/sản lượng/nghiệm thu/đề nghị không là thu/chi thực.

## Đấu thầu, cơ hội trước dự án và đối tác

Hồ sơ trước dự án dùng team KH-KD được giao; chưa cần project hoặc gói giả.
HEAD quản lý hồ sơ trong team/phòng, kể cả hồ sơ người khác. Dùng **Phân công hồ
sơ** để điều phối; nhập lý do cập nhật trước khi lưu hồ sơ đã có. Gói thầu cũng
cần lý do trước khi lưu sửa. Chuẩn
bị/khai báo đã nộp phải đủ căn cứ; `submitted` chưa là trúng thầu hoặc duyệt BASE.

Mục Đấu thầu tách gói và lần tham gia; kết quả một gói không tự lan sang gói
khác. **Đối tác nghiệp vụ** chỉ phục vụ các trường nghiệp vụ và liên kết trong
scope; không mở quyền sửa danh bạ liên phòng, ngân hàng/thuế hoặc xóa đối tác.

## Tài liệu và báo cáo

CRM có nút **Thêm tài liệu**, **Lưu trữ tài liệu**, **Ghi trao đổi**; nhập lý do
và xem kết quả ở tab **Tài liệu và trao đổi**. Chatter chuẩn chỉ đọc đối với HEAD.
Hồ sơ typed dùng **Thêm tài liệu nháp**, **Gỡ tài liệu nháp**, **Tài liệu**.

Trong bản nháp được phép, thêm/sửa/gỡ tài liệu qua action trên hồ sơ và ghi lý do
khi yêu cầu. Hồ sơ đã khóa giữ căn cứ/audit; không xóa file để làm sạch màn hình.
Preview/download phải còn đúng quyền parent và tiền ở thời điểm truy cập; link
cũ/public/token không thay thế quyền đang có.

Mở **Báo cáo KH-KD**, chọn R01–R06 và áp bộ lọc. Đọc phạm vi/đơn vị/nghĩa tiền,
mở hồ sơ nguồn để đối chiếu. Xuất Excel theo toàn bộ tập kết quả đã lọc được
phép, không chỉ trang bảng đang xem. Bản thiết kế UI báo cáo riêng đang chờ duyệt
không thuộc batch quyền HEAD này.

## Khi không thấy hồ sơ hoặc thao tác bị chặn

Đối chiếu công ty/phòng, state, reviewer, lý do/version và hiệu lực role. HEAD
chỉ quản lý đúng đơn vị được provision; cùng công ty không có nghĩa mọi phòng.
7CRM và1managed project thiếu scope đã được ghi riêng để đối chiếu; không suy
scope từ tên hoặc đổi phòng/owner để mở quyền.

Thu hồi/hết hạn role chặn ngay request backend tiếp theo, kể cả tab đang mở.
96 quyền legacy HEAD được vô hiệu khi áp role mới để không còn fallback.
Liên hệ người vận hành để khôi phục đúng scope có lý do, không xin cấp admin.

Deputy/project_lead/planning/support giữ quyền hiện hữu. HEAD không có quyền
Settings, cấp nhóm/grant cho người khác, HR nhạy cảm hoặc kế toán toàn công ty.
Business acceptance và pilot vẫn cần xác nhận riêng.
