# KH-KD — Hướng dẫn quyền năm vai trò

Dev: [TANPHAT ONE](http://127.0.0.1:18069/odoo). Dùng tài khoản/mật khẩu hiện có
trong `.local/kd-access001/dev-credentials.json`; mapping người–alias vẫn private
ở `staff-map.json`. Không reset mật khẩu để đổi vai. Chọn tài khoản remembered
chỉ hiển thị những tài khoản browser đã nhớ, không phải danh bạ nhân sự.

| Vai trò | Scope | Cơ hội/thầu mới | Các hồ sơ khác |
| --- | --- | --- | --- |
| Trưởng ban / head | 8dự án | Lập/sửa của mình, chuẩn bị, khai báo nộp; đọc tiền | Đọc và trả hồ sơ người khác khi đúng reviewer; không tự có quyền lập mọi typed dossier |
| Phó phòng / deputy | 4dự án | Như head; sửa tiền nháp của mình | Lập/gửi/trả/sửa/gửi lại chuỗi hồ sơ, đúng owner/reviewer |
| Chủ trì / project_lead | 4dự án khác | Như deputy | Như deputy, theo4dự án của mình |
| Dự toán–Kế hoạch / planning | 4dự án giao | Chuẩn bị/khai báo nộp của mình; đọc/sửa tiền nháp | Lập/gửi giao khoán, sản lượng, kế hoạch, năng lực; không nghiệm thu/thanh toán/review/hợp đồng submit |
| Hỗ trợ hồ sơ / support | 2dự án | Lập/sửa/chuẩn bị của mình; không khai báo nộp, tiền/file/chatter CRM | Lập/sửa năng lực của mình; không gửi/rà soát/tiền |

[Ma trận chi tiết](../security/KD_ACCESS_002_ROLE_MATRIX.md) giải thích từng model,
state, reviewer, tiền và export. Phân công dự án vẫn là scope minh họa dev.

## Kiểm cơ hội và hồ sơ thầu

1. Đăng nhập → Kế hoạch Kinh doanh → **Cơ hội và hồ sơ thầu**. Danh sách chỉ có
   hồ sơ thuộc scope; người xem có thể đọc hồ sơ cũ nhưng không được sửa thay owner.
2. Chọn **Mới**, nhập tên, khách hàng trùng khách hàng của dự án, công ty, dự án đúng scope, nguồn, phạm vi,
   hạn và checklist. Owner là chính mình. Hồ sơ chưa có dự án dùng nhóm
   **KH-KD — Cơ hội được giao**, owner của chính mình; không cần dự án giả.
3. Lưu → **Chuẩn bị hồ sơ**. Chưa đủ nguồn/phạm vi/hạn/checklist sẽ được báo thiếu.
4. Bốn vai trò có submit riêng nhập căn cứ khai báo nội bộ → **Khai báo đã nộp**.
   Support không có nút này. Hình thức Giao trực tiếp không dùng thao tác nộp thầu.
5. Sau khai báo nộp, căn cứ/phạm vi/tiền/file được giữ nguyên. Trạng thái này
   chưa xác minh, không là trúng thầu, ký kết, duyệt BASE hoặc hiệu lực.

Giá trị cơ hội hiện số tiền khi có quyền; thiếu quyền hiện **Không có quyền xem
tiền**, không hiển thị0 thay dữ liệu bị chặn. Deputy/lead/planning ở bản chuẩn bị
của mình có **Sửa giá trị dự kiến**; hộp native kiểm lại quyền lúc lưu. Head chỉ
đọc tiền theo grant cũ. Query tiền/order/group/export chỉ dùng dự án có quyền tiền.
Trước dự án chưa được cấp tiền. Export metadata dùng tính năng native; trường tiền
và bản ghi ngoài scope vẫn bị chặn. File/chatter CRM hiện mở cho người có parent
read và quyền tiền; chưa có tự động phân loại/redaction mọi free text/file chung.
Tài khoản scoped vẫn phải đủ quyền parent khi URL file có token hoặc file public;
không dùng link chia sẻ để vượt quyền vừa bị thu hồi.

## Kiểm theo vai trò

- Head: xem đủ8dự án và các báo cáo; chỉ trả hồ sơ được chỉ định mình, có lý do;
  lập cơ hội mới của chính mình để thửprepare/submit trên clone.
- Deputy/lead: tạo hồ sơ typed được giao → lưu → gửi đúng reviewer → nhận trả
  → mở sửa với lý do → lưu thay đổi → gửi lại với tóm tắt sửa. Không tự rà soát.
- Planning: thử giao khoán/sản lượng/kế hoạch/năng lực trong4dự án; các nút lập
  nghiệm thu/đề nghị thanh toán hoặc review không xuất hiện là đúng quyền.
- Support: thử cơ hội/năng lực của mình trong2dự án; không có tiền/submit/review.
  Hồ sơ năng lực cá nhân còn giới hạn owner/reviewer; trống không luôn có nghĩa lỗi quyền.

Các luồng ghi thực hành dùng clone19289 và dữ liệu giả, không tạo giao dịch thử trên
dev. Trên dev chỉ mở danh sách/chi tiết/báo cáo và kiểm quyền. Tạo/sửa dự án và
WBS scoped chưa triển khai; không dùng account manager để vượt lỗi này.

## Khi thiếu nút hoặc bị từ chối

Đối chiếu scope, owner/reviewer, state và capability còn hạn trước. Nhãn chức danh
không tự cấp quyền. Không đổi owner/project/team của hồ sơ cũ để có nút; cần action
phân công riêng đã được kiểm backend. Lưu ý chỉnh sửa chưa lưu khi thu hồi quyền:
form CRM sạch tự cập nhật quyền trong khoảng5giây; bản đang sửa giữ nội dung để
không ghi đè công việc, backend chặn ngay lần lưu/action tiếp theo.

**Tài khoản** trong thanh bên mở hồ sơ native của chính mình; tùy chọn hiển thị vẫn
riêng. Muốn đổi vai: menu tài khoản góc phải → Đăng xuất → đăng nhập tiếp; nhiều tab
cùng browser chia sẻ session. Icon công ty trên navbar giữ tooltip/chuyển công ty,
nhãn “Tan Phat Development” đã được bỏ khỏi thanh ngang, dữ liệu tên công ty giữ nguyên.

Nhật ký delta, backup và hướng dẫn cá nhân: `.local/kd-access002/`.
Không gửi credential cho người khác trong batch này. Business/Q2/pilot riêng.
