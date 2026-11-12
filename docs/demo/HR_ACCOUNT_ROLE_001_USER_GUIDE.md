# HR-ACCOUNT-ROLE-001 — Hướng dẫn hồ sơ, tài khoản và vai trò

Cập nhật 12/11/2026. Hướng dẫn này thay các bước chọn/liên kết/gỡ tài khoản
trong hướng dẫn HR trước đây. Mở TP HR → Nhân viên → Danh sách nhân viên → hồ sơ.

## Giao diện hồ sơ và quản lý tài khoản

Từ CHG-20261112-008, hồ sơ dùng nền xanh nhạt, ảnh/tên lớn, năm tab có biểu
tượng và hai khối **Thông tin công việc / Liên hệ công việc** theo ảnh mẫu.
Từ CHG-20261112-009, thanh menu bên trái giữ nguyên màu, chiều rộng và trạng
thái mở/thu gọn khi vào hoặc rời chi tiết. Chỉ nút thu/mở do người dùng bấm
mới đổi lựa chọn hiển thị; các breakpoint tablet/mobile vẫn theo giao diện chung.

Từ CHG-20261112-010, ảnh đại diện, tên, tab, nút và khoảng cách trong chi tiết
được thu gọn để nhìn được nhiều thông tin hơn. Sidebar và cửa sổ quản lý tài
khoản/đổi chức vụ giữ cách dùng hiện tại. Nhấn **Ctrl+F5** nếu còn thấy bản cũ.

Cuối tab **Tổng quan**, bấm **Quản lý tài khoản**. Cửa sổ hiển thị hai cột:
nhân viên/mã/phòng/chức vụ và tên đăng nhập/tình trạng. Mỗi thông tin có nhãn
riêng bằng tiếng Việt; ô **Lý do thao tác** nằm dưới. Tài khoản Mở có nút
**Khóa tài khoản** màu đỏ; tài khoản Khóa có nút **Mở tài khoản**. **Đặt lại
mật khẩu** và **Đóng** được tách riêng. Trên điện thoại các khối xếp một cột.
Hồ sơ chưa có tài khoản đi vào xác thực quản trị viên và form tạo tài khoản.
Các tài khoản quản trị/hệ thống vẫn được backend bảo vệ.

Từ CHG-20261112-014, xác minh tài khoản giữ nguyên bộ lọc “Tìm chức năng” đã
nhập. Gõ/dán mật khẩu trong hộp xác minh; nếu sai, đóng thông báo tiếng Việt
để nhập lại trong chính ô mật khẩu. Hủy/Escape/nút đóng trả về nút mở còn tồn
tại. Sau xác minh đúng, form tạo tập trung ô tên đăng nhập, form reset tập
trung ô mật khẩu mới. Tải lại Ctrl+F5 nếu còn asset cũ. Kiểm password manager
đã thực hiện trên Chrome tích hợp; [bằng chứng và giới hạn](HR_AUTH_FOCUS_009_ACCEPTANCE.md).

## Hồ sơ và tình trạng

Header có ảnh, họ tên, mã TP, phòng ban, chức vụ HR và tình trạng tài khoản:
**Mở** xanh lá, **Khóa** đỏ, **Chưa có tài khoản** xám. Có chữ kèm màu.
Lưu trữ hồ sơ và tình trạng tài khoản là hai khái niệm riêng.

Năm tab: Tổng quan; Công việc & hồ sơ; Thông tin cá nhân; Tài khoản & phân quyền;
Lịch sử. Dữ liệu cá nhân vẫn theo quyền HR Odoo. Nguồn đối chiếu nằm trong vùng
thu gọn ở Công việc & hồ sơ. Bấm Sửa hồ sơ → Lưu hoặc Hủy; validation và cảnh
báo dữ liệu chưa lưu do Odoo xử lý. Lịch sử giữ chatter và phiên bản native.

## Xóa hồ sơ nhập nhầm hoặc lưu trữ

Từ CHG-20261112-013. Trong Danh sách nhân viên, tick hồ sơ (thanh trên hiện
**Đã chọn 1 hồ sơ**) → **Tác vụ** → **Xóa hồ sơ nhập nhầm** (chỉ Quản trị viên
hệ thống). Không còn nút Xóa thường cho nhân viên.

- Hồ sơ đủ điều kiện: cửa sổ hiện họ tên, mã và cảnh báo xóa vĩnh viễn. Nhập
  **Lý do** rồi bấm **Xác nhận xóa**. Thao tác được ghi ở Nhân viên → **Nhật ký
  xóa hồ sơ và sửa mã**.
- Chỉ xóa được hồ sơ nhập tay chưa dùng. Hồ sơ từ danh sách nhân sự, đã có tài
  khoản, vai trò, phân công, tài liệu, trao đổi, lịch sử hoặc liên kết khác sẽ
  hiện **Không xóa được** kèm lý do từng hồ sơ. Khi đó bấm **Lưu trữ nhân viên**
  để ẩn hồ sơ và giữ lịch sử, hoặc **Hủy**.
- Chọn nhiều hồ sơ: chỉ cần một hồ sơ bị chặn là không hồ sơ nào bị xóa.
- Lưu trữ không khóa tài khoản. Muốn chặn đăng nhập, khóa ở tab Tài khoản &
  phân quyền như mục “Khóa, mở và mật khẩu”.

## Mã nhân viên

Mã có dạng TP + số. Hồ sơ mới nhận số kế tiếp sau mã hợp lệ cao nhất từng cấp
(kể cả hồ sơ lưu trữ hoặc đã xóa); mã đã dùng không cấp lại, có thể có khoảng
trống. Mã từ danh sách nhân sự giữ nguyên. Ngày 12/11/2026 mã kế tiếp trên main
là TP10071; hồ sơ nhập tay từng nhận nhầm `TP20000` đã được sửa thành `TP10070`
và ghi nhật ký.

## Tạo tài khoản riêng

Chỉ Quản trị viên hệ thống đúng công ty được thao tác tài khoản và vai trò.

1. Mở tab **Tài khoản & phân quyền** của hồ sơ chưa có tài khoản.
2. Bấm **Tạo tài khoản riêng**. Nếu được yêu cầu xác nhận danh tính, nhập
   **mật khẩu của quản trị viên đang đăng nhập**, rồi xác nhận.
3. Trong cùng form, nhập **Tên đăng nhập**, **Mật khẩu mới** và **Nhập lại mật khẩu**.
   Mỗi ô có nhãn/chú thích riêng; nút **Hiện/Ẩn** giúp kiểm tra mật khẩu khi cần.
4. Bấm **Tạo tài khoản**. User mới, mật khẩu, hồ sơ và lịch sử được lưu trong
   một transaction. Thành công mới hiện thông báo; lỗi hiển thị bằng tiếng Việt.

Login trùng, hồ sơ đã có user hoặc thao tác bấm lại bị từ chối. **Hủy** trước
khi lưu không tạo tài khoản. Xác thực quản trị viên có hiệu lực 10 phút theo Odoo;
hết hạn thì đóng/mở lại form để xác thực, thông tin chưa được lưu. Mật khẩu mới
không lưu trong bản nháp hoặc lịch sử. Hệ thống không gửi email hoặc phản hồi ra ngoài.
User mới chỉ có quyền nội bộ cơ bản; admin giao vai trò nghiệp vụ sau.

Không có thao tác chọn, liên kết hoặc gỡ user có sẵn. Không đổi mapping, login,
mật khẩu hoặc quyền của các tài khoản hợp lệ chỉ để đổi nhãn. Chưa có tài khoản
là trạng thái hợp lệ; không cần cấp đồng loạt. Mỗi user chỉ gắn một hồ sơ trong
một công ty, giữ mô hình nhiều công ty native của Odoo.

## Thay đổi vai trò KH-KD

**Từ CHG-20261112-007:** trên danh sách, bấm tên/dòng nhân viên để mở chi tiết.
Nút **Đổi chức vụ** nằm ngay dưới tên trong hồ sơ; danh sách không còn nút này.

Trong cửa sổ, xem chức vụ/quyền hiện tại rồi chọn:

- **Đổi chức vụ trong hồ sơ:** chọn chức vụ mới, nhập lý do → **Xem trước thay
  đổi → Xác nhận đổi chức vụ**. Dùng cho bổ nhiệm, hạ chức vụ hoặc điều chuyển
  theo danh mục chức vụ; quyền sử dụng hệ thống giữ nguyên. Nhân viên chưa có
  tài khoản vẫn đổi chức vụ được.
- **Bổ nhiệm / hạ quyền KH-KD:** chọn **Bổ nhiệm Trưởng phòng / Trưởng ban
  KH-KD** hoặc **Chuyển về Nhân viên KH-KD**. Nếu cần đổi cả chức vụ hiển thị,
  tích **Đổi cả chức vụ ghi trong hồ sơ** rồi chọn chức vụ mới. Nhập lý do →
  **Xem trước thay đổi** → đọc quyền thêm/thu hồi/giữ → **Xác nhận bổ nhiệm**
  hoặc **Xác nhận chuyển về nhân viên**. Chức vụ và quyền được áp cùng lúc khi
  chọn đổi cả hai. Quyền KH-KD cần có tài khoản và phòng đã có bộ quyền.

**Hủy** không áp thay đổi. Nếu thông tin đã đổi từ phiên khác hoặc bạn sửa
lựa chọn/lý do sau xem trước, phải xem trước lại. Lịch sử giữ người thực hiện,
chức vụ trước/sau và lý do. Ngoài bộ quyền KH-KD hiện hành, hệ thống chưa cấp
quyền quản lý tự động cho chức vụ của phòng khác.

**Mỗi công ty/phòng ban chỉ có một trưởng phòng nghiệp vụ.** Nếu phòng đã có
người giữ vai trò, bổ nhiệm người khác sẽ bị chặn và thông báo nêu tên trưởng
phòng hiện tại. Mở hồ sơ người đó → Đổi chức vụ → Bổ nhiệm / hạ quyền KH-KD →
Chuyển về Nhân viên KH-KD → lý do → xem trước → xác nhận. Sau khi hạ cấp thành
công, mở hồ sơ nhân viên mới để bổ nhiệm. Hệ thống không tự hạ/thay người cũ.
Nếu muốn đổi cả chức vụ ghi trong hồ sơ, chọn rõ tùy chọn đó ở mỗi bước.
Khóa tài khoản hoặc ngày hết hạn không thay thao tác thu hồi vai trò; role chưa
thu hồi vẫn giữ vị trí. Đổi tên chức vụ HR riêng không tạo vai trò nghiệp vụ.

Đường trong tab tài khoản vẫn dùng được; nút hiện có tên **Bổ nhiệm / hạ quyền
KH-KD**. Các nguyên tắc quyền bên dưới giữ nguyên.

1. Mở **Tài khoản & phân quyền → Bổ nhiệm / hạ quyền KH-KD**.
2. Chọn **Chuyển về Nhân viên KH-KD** hoặc **Bổ nhiệm Trưởng phòng / Trưởng ban KH-KD**.
3. Kiểm tra công ty/phòng/phạm vi và nhập lý do.
4. Có thể chọn đồng thời cập nhật chức vụ HR; nếu không chọn, chức vụ giữ nguyên.
5. Bấm **Xem trước thay đổi**: đọc quyền thêm, thu hồi và quyền cấp riêng còn giữ.
6. Bấm nút xác nhận đúng thao tác. Nếu dữ liệu/quyền thay đổi sau xem trước, xem lại
   bản mới; hệ thống không tự gửi lại thao tác ghi.

HEAD dùng `tp.kd.department.role` theo [policy hiện hành](../security/KD_ACCESS_002_ROLE_MATRIX.md),
toàn phạm vi phòng KH-KD được cấu hình bằng CRM team/company/department.
HEAD không cấp Settings, HR toàn công ty, phòng khác, ký/hiệu lực/thanh toán.
Đổi chức vụ HR đơn thuần không cấp quyền. Phòng chưa có bộ vai trò sẽ báo rõ
chưa triển khai. Không dùng chuỗi tên phòng để suy quyền.

Hạ HEAD thu hồi trách nhiệm động và quyền tiền/file/quản lý phát sinh từ HEAD.
Nhóm scoped được giữ cho nhân viên; không thay toàn bộ groups. Quyền đọc tiền
cấp riêng hợp lệ có thể còn, được liệt kê cùng ngày hết hạn. Khi còn coordinator,
grant quản lý hoặc nhóm trực tiếp/kế thừa xung đột, hệ thống **chặn hạ** và nêu
nguồn quyền cần xử lý; không báo đã hạ đầy đủ. Cấp/thu hồi grant riêng vẫn theo
quy trình được kiểm soát hiện có, không có giao diện cấp grant rộng mới.

Sau đổi role, phiên cũ hết hiệu lực; người dùng đăng nhập lại. Backend áp quyền
mới với native RPC, API, export, file và chatter. Tài khoản hệ thống/admin và
chính admin thao tác được bảo vệ. Lịch sử ghi admin thật, lý do và quyền trước/sau.

## Khóa, mở và mật khẩu

Trong tab tài khoản, bấm **Khóa / mở tài khoản**, nhập lý do rồi chọn nút phù
hợp. Khóa chặn đăng nhập và phiên đang có. Mở không hồi sinh phiên cũ.
Thông báo với đúng mật khẩu của tài khoản khóa:
**“Tài khoản đã bị khóa. Vui lòng gửi phản hồi.”**
Gửi phản hồi hiện chỉ là thông báo chưa triển khai, không gửi dữ liệu.

**Đặt lại mật khẩu** dùng cùng form, giữ nguyên tên đăng nhập ở chế độ chỉ đọc.
Xác thực quản trị viên khi Odoo yêu cầu, nhập mật khẩu mới và nhập lại rồi bấm
**Lưu mật khẩu mới**. Không hiển thị mật khẩu hiện tại. Không đưa mật khẩu vào
ghi chú hoặc lý do. Cơ chế kiểm tra và mã hóa mật khẩu vẫn do Odoo xử lý.

Chi tiết kỹ thuật, bằng chứng và giới hạn: [acceptance](HR_ACCOUNT_ROLE_001_ACCEPTANCE.md).
