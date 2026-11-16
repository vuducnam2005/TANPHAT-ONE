# HR-ACCOUNT-ROLE-001 — Hướng dẫn hồ sơ, tài khoản và vai trò

**HR-EMP-014 (13/11/2026):** Hồ sơ hiện có sáu tab, bổ sung Hợp đồng lao động; xem [hướng dẫn loại hình, hợp đồng, hồ sơ cần bổ sung và Excel](HR_EMP_014_USER_GUIDE.md). Tài khoản/role/password vẫn theo luồng bên dưới.

**HR-LIST-013 (13/11/2026):** Danh sách nhân viên luôn chia thành các nhóm
phòng ban có dải xanh. Không có thẻ “Phòng ban ×” cần giữ trên thanh tìm kiếm;
xóa tìm kiếm/bộ lọc vẫn giữ các nhóm. Tên phòng ban chỉ hiện ở đầu nhóm,
không lặp trước từng tên nhân viên. Vẫn có thể tìm theo đơn vị để thu hẹp
kết quả. Bấm tên/dòng để mở hồ sơ hiện có. [Bằng chứng013](HR_LIST_013_ACCEPTANCE.md).

Cập nhật 13/11/2026. Hướng dẫn này thay các bước chọn/liên kết/gỡ tài khoản
trong hướng dẫn HR trước đây. Mở TP HR → Nhân viên → Danh sách nhân viên → hồ sơ.

## Giao diện hồ sơ và quản lý tài khoản

Từ HR-UI-011, chỉ còn một menu **Danh sách nhân viên**. Bấm tên/dòng để mở chi tiết; **Quay lại** giữ bộ lọc/trang của danh sách vừa mở. Từ HR-LIST-013, bảng luôn chia theo phòng ban với dải tên nhóm xanh nhạt;
không lặp cột Đơn vị/Phòng ban trong từng dòng và tên nhân viên là chữ như trước.
Bảng cho chọn 10/20/50/100 dòng; khi nhóm theo phòng ban, đơn vị phân trang là
**nhóm**, số hồ sơ nằm cạnh từng nhóm. Có thể xóa tìm kiếm/bộ lọc thật bằng
các thẻ ở phía trên bảng; các nhóm phòng ban vẫn giữ cố định. Có thể cuộn ngang bảng và bật/tắt cột bằng nút tùy chọn cột.

Chi tiết mở ở chế độ xem. **Sửa hồ sơ → Lưu / Hủy** cũng có trên điện thoại.
Hủy khi đã sửa sẽ hỏi trước khi bỏ thay đổi; rời trang khi còn thay đổi sẽ hỏi
lưu hoặc tiếp tục chỉnh sửa. Năm tab là **Tổng quan**, **Thông tin cá nhân**,
**Hồ sơ và năng lực**, **Tài khoản và phân quyền**, **Lịch sử**. Thông tin công
việc bổ sung, sơ đồ native, phiên bản và chứng chỉ/tệp vẫn được giữ trong hồ sơ.

Phòng ban, chức vụ, nơi làm việc và nhãn có trang chi tiết riêng. Bấm số nhân
viên để mở hồ sơ đang sử dụng đúng phạm vi quyền. **Nhãn nhân viên** là tên
mới của **Thẻ nhân viên**, dùng phân loại hồ sơ. Sơ đồ quản lý chỉ nối quan hệ
quản lý trực tiếp đã khai báo; mở/thu nhánh bằng số cấp dưới. Lọc phòng ban
chọn hồ sơ phù hợp, mở nhánh có thể lấy cấp dưới ngoài kết quả lọc. Màu tổ
chức khác với trạng thái tài khoản. Nhập Excel có bốn bước hiển thị, giữ ba
trạng thái backend và lịch sử sau áp dụng. Xem [acceptance HR-UI-011](HR_UI_011_ACCEPTANCE.md).

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

## Xóa vĩnh viễn nhân viên hoặc lưu trữ

Từ CHG-20261112-016 (thay “Xóa hồ sơ nhập nhầm”). Chỉ Quản trị viên hệ thống có
quyền quản lý nhân sự. **Lưu trữ** chỉ ẩn hồ sơ, giữ lịch sử và có thể Bỏ lưu trữ;
**Xóa vĩnh viễn** gỡ hồ sơ khỏi hệ thống, kể cả danh sách lưu trữ, tìm kiếm và
xuất dữ liệu, không thể khôi phục bằng Bỏ lưu trữ.

1. Trong Danh sách nhân viên (hoặc chi tiết hồ sơ), tick một hay nhiều hồ sơ →
   **Tác vụ** → **Xóa vĩnh viễn nhân viên**. Hồ sơ đã lưu trữ hoặc nhập từ Excel
   vẫn xóa được.
2. Cửa sổ hiện họ tên, mã, phòng ban, tài khoản, số hồ sơ và ba khối:
   **Sẽ xóa** (phiên bản hồ sơ, kỹ năng, trao đổi, tệp... của chính hồ sơ),
   **Giữ lại** (dòng/lô/file Excel gốc, tài khoản, liên hệ còn dùng) và
   **Đang chặn — chưa thể xóa** (dữ liệu nghiệp vụ độc lập, ví dụ đang là quản lý
   trực tiếp hoặc quản lý phòng ban, kèm cách xử lý). Khi còn khối chặn, nút đỏ bị
   tắt: xử lý theo gợi ý rồi bấm **Xem trước lại**, hoặc Hủy và dùng Lưu trữ.
3. Tài khoản mặc định được giữ nguyên. Tick **Xóa hồ sơ và khóa tài khoản** nếu muốn
   khóa đăng nhập, kết thúc phiên và thu hồi vai trò/phân công/quyền dự án,
   KH-KD trong công ty. Tài khoản quản trị/hệ thống hoặc của chính bạn không bị
   khóa từ đây; nếu tài khoản còn quyền mà không chọn khóa thì phải hạ quyền trước.
4. Nhập **Lý do** và **mật khẩu của chính bạn** (tài khoản đang đăng nhập; mỗi lần
   xóa đều hỏi lại). Bấm **Xác nhận xóa vĩnh viễn** hoặc **Hủy** (không ghi gì).
5. Sai mật khẩu: không có gì bị xóa, ô mật khẩu được xóa trắng để nhập lại. Sai
   nhiều lần sẽ phải chờ ít phút như khi đăng nhập. Nếu dữ liệu đổi sau khi xem
   trước, hệ thống từ chối cả lô và yêu cầu xem trước lại.

Chọn nhiều hồ sơ là một lần xác nhận, tất cả-hoặc-không. Mỗi lần xóa được ghi ở
Nhân viên → **Nhật ký xóa hồ sơ và sửa mã** (người làm, lý do, mã, tài khoản, phần
đã xóa/giữ; không có mật khẩu). Mã TP của hồ sơ đã xóa không bao giờ cấp lại;
nhập lại cùng người từ Excel sẽ báo xung đột để xử lý tay. Lưu trữ không khóa tài
khoản; muốn chặn đăng nhập mà vẫn giữ hồ sơ, khóa ở tab Tài khoản & phân quyền.

## Mã nhân viên

Mã có dạng TP + số. Hồ sơ mới nhận số kế tiếp sau mã hợp lệ cao nhất từng cấp
(kể cả hồ sơ lưu trữ hoặc đã xóa vĩnh viễn); mã đã dùng không cấp lại, có thể có khoảng
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
