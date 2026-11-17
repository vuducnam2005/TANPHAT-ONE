# HR — Danh bạ chỉ xem và bảng công dùng chung (thiết kế17/11/2026)

**IDEA_DRAFT_NOT_IMPLEMENTED.** Người dùng muốn quản lý công trong Nhân sự,
nhân viên xem công ngày của mình tại Hồ sơ cá nhân; bổ sung mọi nhân viên
được vào module Nhân sự chỉ xem, xem thông tin đồng nghiệp và bảng công của
đồng nghiệp, nhưng ẩn hợp đồng và thông tin quan trọng. Chưa giao code phần này.

## Quyền hiển thị được yêu cầu

- Mọi tài khoản nhân viên nội bộ đang hoạt động có workspace Nhân sự trong
  công ty được phép. Đây là chia sẻ nội bộ có xác thực, không mở public/portal.
- Nhân viên thường chỉ đọc: không tạo/sửa/xóa nhân viên/công/ca/danh mục,
  không cấp user/quyền hoặc chốt kỳ. Vai trò HR/admin đã cấp vẫn có thẩm
  quyền chuyên môn riêng; cho nhân viên xem không thu hồi quyền HR hợp lệ.
- Không cấp nhóm HRmanager/HRofficer chỉ để hiện menu; xây tập trường đọc
  rõ ràng, ưu tiên danh bạ public-employee native và nguồn công đã lọc.
- Nhân viên xem thông tin công khai nội bộ của đồng nghiệp; không tự sửa
  thông tin mình trong module HR nếu chỉ có vai trò đọc. Luồng đề nghị chỉnh
  công riêng không phải quyền ghi trực tiếp bản công. Quyền tự sửa Hồ sơ cá
  nhân hiện có cần được chốt riêng trước khi thay, không âm thầm mở thêm.

## Phân loại trường đề xuất, chưa là whitelist đã duyệt

| Mức chia sẻ | Trường/nội dung |
| --- | --- |
| Danh bạ đồng nghiệp | MãTP, họ tên, ảnh, phòng/đơn vị, chức vụ, quản lý trực tiếp, email/điện thoại công việc, nơi làm việc |
| Bảng công đồng nghiệp | Ngày, ca, giờ vào/ra, giờ/công theo quy tắc đã cấu hình, trạng thái dữ liệu/chờ xử lý/đã chốt, ngày cập nhật nguồn |
| Chỉ bản thân và HR/admin đúng quyền | Thông tin liên hệ cá nhân/hồ sơ cá nhân khác theo whitelist được chọn; nhân viên khác không mặc định được xem |
| Riêng tư, không mở cho nhân viên khác | Hợp đồng lao động và file, lương/phụ cấp/thưởng/phạt, ngân hàng, CCCD/thuế/BHXH, địa chỉ nhà, sức khỏe, tài liệu kỷ luật/đánh giá nội bộ, mật khẩu/token/nhóm quyền |
| Nội dung kèm công không chia sẻ rộng | Lý do nghỉ chi tiết, chứng từ y tế, minh chứng/nhận xét của yêu cầu điều chỉnh, ảnh khuôn mặt/vân tay/GPS/dữ liệu máy thô |

Người dùng nói "thông tin cá nhân thì xem được" nhưng chưa chỉ định từng
trường; bảng này là đề xuất phân loại, cần chốt trước khi code. Không suy ra
được xem mọi field hr.employee. Ngày sinh/liên hệ riêng nếu công ty muốn chia
sẻ cần chọn rõ; không mở mặc định toàn bộ thông tin riêng của đồng nghiệp.
Trên bảng công chung, hiển thị nghỉ đã duyệt mà không lộ chẩn đoán/lý do riêng.

Backend phải bảo vệ field/read/search/filter/options/count/read_group/
export/file/chatter/notifications/directRPC; không chỉ ẩn tab/cột. Tệp đính
kèm giữ quyền nguồn; không lộ hợp đồng qua preview/token/download/history.

## Hai cách xem, một nguồn dữ liệu

Quản lý nhân sự → Chấm công: Tổng quan, Bảng công, Điều chỉnh, Nhập dữ liệu;
nhân viên chỉ thấy phần đọc được phép. Hồ sơ cá nhân → Công của tôi: lịch
tháng và từng ngày lọc employeeID của user đăng nhập, không copy bảng riêng.
Bảng công chung có phòng/nhân viên/kỳ/trạng thái và dạng ngày/tháng; detail
chỉ dữ liệu được chia sẻ. Bộ lọc/count/pager/export cùng scope theo DEC-044.

Dashboard nền sáng, KPI nguồn cập nhật, chart lớn/drill-down đúng tập. Donut
dùng nhóm không giao nhau như đủ dữ liệu/cần kiểm tra/chưa có dữ liệu;
đi muộn là chỉ số riêng, không cộng trùng với thiếu giờ. Hover/reduced-motion,
mobile và trạng thái rỗng rõ; không nhân đôi dashboard ở nhiều tab.

## Dữ liệu và xử lý công đề xuất

Nhập Excel trước, mapping mã máy → employee hiện có theo khóa đã xác minh;
không tạo nhân viên/match chỉ theo tên. Lưu nguồn/lần nhập/chống trùng,
preview trước ghi, các lần vào-ra gốc và điều chỉnh có lịch sử. Không lấy
giờ sớm nhất/muộn nhất mọi ca; cần quy tắc nghỉ trưa/ca đêm/nhiều ca/múi giờ.
Danh sách nhân sự nhập trước đây chỉ đọc các cột roster, không nhập ô công.
Chấm công vào-ra độc lập với timesheet giờ theo dự án hiện có.

Nguồn vào-ra → xử lý theo ca/lịch → nhân viên xem → yêu cầu điều chỉnh riêng
→ người phụ trách khác duyệt/trả → bản công cập nhật → chốt kỳ. Thiếu dữ liệu
không tự thành nghỉ không phép; ngày đang làm/nghỉ theo lịch/tương lai giữ
khác nhau. Sau chốt, điều chỉnh có version/lý do. Công chưa là tiền lương.
Nếu nguồn chỉ nhập mỗi tuần thì không hứa công realtime hằng ngày; hiện
thời điểm đồng bộ gần nhất. Kết nối máy tự động là chặng sau, tùy thiết bị/API.

## Các đầu vào chưa chốt và bước kế tiếp

Nguồn công thật và định dạng; lịch/ca/nghỉ trưa/đi muộn/công tác/tăng ca;
người duyệt/chốt/mở kỳ; trường cá nhân nào chia sẻ; export bảng công của
đồng nghiệp có cho tải không hay chỉ xem; chính sách sửa Hồ sơ cá nhân của
bản thân. Đây là các điểm cần chốt để viết prompt, không chặn trao đổi ý tưởng.

Quy trình rollout theo [chỉ thị17/11](../operations/TP_CONTINUOUS_DELIVERY_POLICY.md):
hạng mục được giao code hoàn tất thì commit/push/deploy PCserver, không
bắt buộc18079; backup và kiểm nhanh vẫn giữ. Chưa mở payroll/bảo hiểm/GPS/
nhận diện khuôn mặt hoặc nhập dữ liệu công thật trong lượt thiết kế này.
