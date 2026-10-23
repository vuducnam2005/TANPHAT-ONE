# Phác thảo dữ liệu và phân quyền ban đầu

Bản này chỉ nêu cấu trúc tối thiểu để thảo luận; tên trường và quy tắc quyền cần đối chiếu quy trình thực tế trước khi viết addon Odoo.

## Thực thể dự kiến

| Thực thể | Trường tối thiểu dự kiến | Quan hệ | Cần xác nhận |
| --- | --- | --- | --- |
| Phòng ban | Mã, tên, người quản lý, trạng thái | Có nhiều nhân viên | Cơ cấu phòng ban, phòng ban kiêm nhiệm |
| Nhân viên | Mã, họ tên, tài khoản Odoo, phòng ban, trạng thái | Thuộc phòng ban; có thể mang nhiều vai trò | Nguồn danh sách nhân viên, ai được quản lý |
| Vai trò/nhóm quyền | Mã, tên, mô tả | Gán cho người dùng | Danh sách vai trò nghiệp vụ thực tế |
| Bản ghi nghiệp vụ | Mã, loại, trạng thái, người tạo, phòng ban, thời điểm | Thuộc module và phòng ban | Từng loại hồ sơ và các trường bắt buộc |

Liên kết dự kiến: `Phòng ban 1–n Nhân viên`; `Người dùng n–n Nhóm quyền`; `Phòng ban 1–n Bản ghi nghiệp vụ`. Không tạo model tùy chỉnh cho thông tin đã có sẵn trong Odoo trước khi xác nhận cách tái sử dụng.

## Ma trận quyền để xác nhận

`Có điều kiện` nghĩa là phải xác định phạm vi phòng ban/bản ghi trước khi cấu hình ACL và record rules.

| Vai trò dự kiến | Xem dữ liệu của mình | Tạo/sửa dữ liệu của mình | Xem dữ liệu phòng ban | Duyệt | Cấu hình hệ thống |
| --- | --- | --- | --- | --- | --- |
| Nhân viên | Dự kiến có | Dự kiến có | Cần xác nhận | Cần xác nhận | Không |
| Quản lý phòng ban | Dự kiến có | Dự kiến có | Có điều kiện | Cần xác nhận | Không |
| Quản trị hệ thống | Cần xác nhận | Cần xác nhận | Cần xác nhận | Cần xác nhận | Có điều kiện |

## Quyết định cần hỏi trong buổi khảo sát

- Một người có thể thuộc nhiều phòng ban hay chỉ một phòng ban?
- Quản lý được xem toàn bộ phòng ban hay chỉ hồ sơ được giao?
- Khi chuyển phòng ban, hồ sơ cũ do ai sở hữu và ai còn quyền xem?
- Bản ghi ở trạng thái đã duyệt có được sửa không, và ai được mở lại?
- Có vai trò nào chỉ xem báo cáo mà không xem chi tiết cá nhân?

Sau khi chốt, triển khai phân quyền Odoo theo nhóm người dùng, ACL và record rules rồi kiểm tra bằng tài khoản mẫu của từng vai trò.
