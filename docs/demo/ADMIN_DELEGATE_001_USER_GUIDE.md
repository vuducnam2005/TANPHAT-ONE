# Quản trị được ủy quyền — hướng dẫn sử dụng

Ngày 17/11/2026, CHG-20261117-004. Đọc cùng
[phạm vi chức năng](../security/ADMIN_DELEGATE_001_COVERAGE.md) và
[kết quả kiểm chứng](ADMIN_DELEGATE_001_ACCEPTANCE.md).

## Cấp và thu hồi

Quản trị chính mở **Quản lý nhân sự → Nhân viên → hồ sơ → Tài khoản**.
Phần **Quyền quản trị** tách riêng với chức vụ, vai trò nghiệp vụ và trạng thái
tài khoản. Nhân viên cần có tài khoản nội bộ riêng đang mở trước khi cấp.

1. Chọn **Cấp quyền quản trị**. Đọc các phòng nghiệp vụ được bảo vệ trong bản
   xem trước. Nếu chưa xác định được phòng, hệ thống không mở thêm nghiệp vụ.
2. Nhập lý do và xác thực lại bằng hộp xác thực native khi hệ thống yêu cầu.
3. Xác nhận. Badge đổi thành **Quản trị được ủy quyền**. Chức vụ, nhóm, quyền
   tiền, phân công và các quyền nghiệp vụ không đổi.
4. Thu hồi tại cùng vị trí bằng **Thu hồi quyền quản trị**, nhập lý do và xác
   thực. Lịch sử cấp/thu được giữ; tài khoản vẫn mở và dùng quyền nghiệp vụ gốc.

Không có tài khoản thật nào được tự chọn để cấp trong lần triển khai này.
Người được ủy quyền không có nút cấp tiếp hoặc tự bổ nhiệm. Khóa tài khoản và
thu hồi ủy quyền là hai thao tác riêng.

## Phạm vi thực tế

Home dùng cùng bố cục hiện hành và capability backend. Các mục chưa triển khai
vẫn ghi **Đang phát triển**. Không có quyền Cài đặt, module, security rules hoặc
server action từ ủy quyền. Mở link trực tiếp vẫn kiểm quyền ở server.

Phòng mình gồm mọi trách nhiệm nghiệp vụ đang hiệu lực: nhân sự, trưởng phòng,
phân công dự án, grant, CRM và phân quyền Báo cáo. Dữ liệu giao thoa, chưa rõ
phòng hoặc ngoài công ty được phép giữ quyền nghiệp vụ gốc. Chuyển nguồn hồ sơ,
chuyển phòng và quản trị phân quyền dùng quy trình của Quản trị chính.

Ví dụ nhân viên KH-KD có một dự án được giao và một dự án cùng phòng chưa được
giao: sau cấp, chỉ dự án được giao vẫn đọc/sửa theo quyền gốc; dự án còn lại và
tiền chưa được cấp vẫn bị chặn. Dự án có nguồn rõ ở phòng khác được mở theo
chức năng đã rà soát, gồm workflow hợp đồng native. Sau thu hồi, quyền thêm
biến mất ở request tiếp theo, kể cả tab đang mở; quyền dự án KH-KD gốc còn nguyên.

Các chức năng chưa mở được liệt kê trong coverage: không coi badge quản trị là
quyền superuser hoặc đã triển khai mọi chức năng nhân sự, Báo cáo và Kho.
Dữ liệu đã tải xuống trước thu hồi không thể bị xóa khỏi máy người nhận.

## Tệp và hình ảnh

Ảnh và tài liệu riêng dùng quyền hồ sơ nguồn. Không cần và không được bật
`public` để sửa lỗi tải. Nếu gặp ảnh trống hoặc file lỗi, ghi môi trường, mã hồ
sơ, thời điểm và loại tệp; người vận hành đối chiếu filestore/checksum theo
[runbook media](../../ops/runbooks/DEPLOY_MEDIA_001_DEPLOY_AND_ROLLBACK.md).
Word/Excel tải ở định dạng gốc; không gửi hồ sơ nội bộ sang viewer bên ngoài.
