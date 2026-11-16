# TP HR — Loại hình lao động và hồ sơ hợp đồng

HR-EMP-014, 13/11/2026. Dùng cùng hồ sơ nhân viên, quyền và phiên đăng nhập
Odoo hiện có. Kết quả triển khai xem [acceptance](HR_EMP_014_ACCEPTANCE.md).

## Danh sách và loại hình lao động

Vào **TP HR → Nhân viên → Danh sách nhân viên**. Phòng ban luôn là nhóm đầu
tiên, kể cả sau khi xóa tìm kiếm. Chức vụ đứng trước Loại hình lao động và Số
điện thoại. Dùng menu tìm kiếm để lọc Ngắn hạn, Dài hạn, Thuê khoán hoặc Loại
hình chưa khai báo; chọn 10/20/50/100 nhóm mỗi trang và tùy chọn cột như trước.

Người được sửa hồ sơ chọn **Sửa hồ sơ**, nhập Loại hình lao động ở Tổng quan
hoặc tab Hợp đồng lao động, rồi **Lưu**. **Hủy** bỏ thay đổi chưa lưu sau xác
nhận. Trống nghĩa là **Chưa khai báo**. Đây là phân loại quản trị có lịch sử
theo phiên bản, không xác nhận thời hạn pháp lý hoặc trạng thái tài khoản.
Tình trạng tài khoản vẫn là **Mở / Khóa / Chưa có tài khoản**.

## Tab Hợp đồng lao động

Hồ sơ có sáu tab. Tab Hợp đồng lao động gồm tóm tắt phiên bản đang xem, loại hình, ngày lao động
đã khai báo, giấy tờ và các phiên bản liên quan. Nhãn Hiện tại/Quá khứ/Tương
lai và dòng thời gian cho biết bạn đang xem bản nào. **Phiên bản hồ sơ** mở
danh sách phiên bản; số đếm là số phiên bản hồ sơ.

Ngày bắt đầu/kết thúc và cờ có thời hạn của hợp đồng lao động dùng dữ liệu
Odoo hiện có. Khi sửa ngày, cơ chế Odoo có thể cập nhật các phiên bản thuộc
cùng hợp đồng; kiểm lại thời hạn và bản đang xem trước khi lưu. Không suy
hợp đồng vô thời hạn từ ngày kết thúc trống hoặc từ nhãn Dài hạn.

Chọn **Bổ sung hồ sơ hợp đồng** để mở hộp thoại: nhập loại giấy tờ, số hợp
đồng, tên/trích yếu, ngày ký có căn cứ, ghi chú, tệp và phụ lục. Lưu sẽ liên
kết giấy tờ vào phiên bản đang xem; Hủy không tạo giấy tờ. **Xem hồ sơ giấy
tờ** mở danh sách của cùng nhân viên để xem/sửa theo quyền. Các phiên bản có
thể cùng dùng một giấy tờ; không đếm chúng thành nhiều hợp đồng. Giấy tờ đã
lưu không chuyển sang nhân viên/loại khác và không xóa vật lý.

Với **Thuê khoán**, chọn giấy tờ Hợp đồng thuê khoán và nhập thời hạn thuê
khoán trong giấy tờ. Không điền thời hạn này vào ngày lao động. Ngày kết thúc
trước ngày bắt đầu bị từ chối. Chưa có dữ liệu sẽ hiện **Chưa có thông tin
hợp đồng** cùng hướng dẫn bổ sung.

Tải tệp không xác nhận đã ký hoặc đang có hiệu lực. HR được đọc giấy tờ có
thể tải tệp trong phạm vi được giao; không có liên kết công khai. Quyền lương
vẫn riêng: chỉ đưa tài liệu có nội dung phù hợp với người được quyền đọc.
Task này chưa có duyệt/ký điện tử, lương, bảo hiểm, chấm công hay thanh toán.

## Hồ sơ cần bổ sung

Mục này là danh sách công việc rà soát cùng hồ sơ, không tạo bản sao. Một
hồ sơ xuất hiện nếu thiếu mã nhân viên, thiếu phòng ban, hoặc đồng thời
thiếu chức vụ và chức vụ nguồn. Nhãn **Cần bổ sung** nêu từng mục thiếu.

Chọn **Bổ sung hồ sơ** để mở đúng nhân viên ở chế độ sửa. Mã, phòng ban và
chức vụ vẫn theo luồng có kiểm soát hiện hành: không sửa mã tùy ý; admin dùng
**Chuyển phòng ban** hoặc **Đổi chức vụ** khi cần. Sau khi hoàn tất, tải lại
danh sách; hồ sơ đủ ba tiêu chí sẽ rời danh sách này. Thông báo đủ tiêu chí
chỉ nói về thông tin cơ bản, không xác nhận đầy đủ pháp lý. Không có tài
khoản hoặc hợp đồng vẫn là trạng thái hợp lệ.

## Lịch sử và Excel

**Lịch sử hoạt động** chứa trao đổi/thay đổi với người thực hiện, thời điểm
và lý do của sự kiện. Sự kiện đối chiếu danh tính cũ được tóm tắt dễ đọc;
bằng chứng gốc vẫn được giữ. Nhật ký quản trị riêng giữ metadata theo quyền.
**Có hiệu lực từ** và **Trạng thái tài khoản** được Việt hóa trong sự kiện
HR tương ứng; trạng thái native **Được mời** vẫn giữ nguyên.

Sidebar chỉ còn **Tổng quan** cho dashboard. Chọn bộ lọc rồi **Xuất Excel
nhân sự** trên Tổng quan. File có phạm vi, thời điểm xuất, loại hình và các
mục cần bổ sung; Chưa khai báo được giữ rõ. Tổng số lấy từ dữ liệu backend
trong quyền hiện tại. Không xuất lương, mật khẩu hoặc hash ảnh.
