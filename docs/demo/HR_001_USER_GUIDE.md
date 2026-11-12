# TP HR — Hướng dẫn hồ sơ nhân viên và roster HR-001

**Hiện hành từ HR-ACCOUNT-ROLE-001 (12/11/2026):** dùng [hướng dẫn hồ sơ, tài khoản và vai trò](HR_ACCOUNT_ROLE_001_USER_GUIDE.md). Các bước chọn/liên kết/gỡ user và bố cục sáu tab bên dưới là lịch sử, đã được thay thế. Tình trạng hiện dùng Mở/Khóa/Chưa có tài khoản.

Ngày 11/11/2026. Hướng dẫn mô tả chức năng trong source HR-001. Môi trường đã
áp dụng, kết quả kiểm thử và các cổng nghiệm thu xem
[PROJECT_STATUS](../PROJECT_STATUS.md); tài liệu này không tự xác nhận rollout
hoặc nghiệm thu nghiệp vụ. Dữ liệu lương, tuyển dụng và chấm công không thuộc
luồng nhập roster này.

## Mở không gian nhân sự

1. Mở [TANPHAT ONE chính](http://127.0.0.1:18069/odoo), đăng nhập bằng tài khoản
   hiện có. Trên Trang chủ quản trị gồm bảy mục, chọn **Quản lý nhân sự** để mở
   TP HR. Người có quyền được giao cũng có thể mở ứng dụng **TP HR** từ menu Odoo.
2. Sidebar trái có Tổng quan; Nhân viên; Tổ chức; Hồ sơ và năng lực; Nhập và đối
   chiếu; Báo cáo. Mục nhập chỉ dành cho HR manager. Đóng/mở nhóm menu, tìm tên
   mục, thu sidebar hoặc mở ngăn điều hướng trên điện thoại.
3. Menu và dữ liệu phụ thuộc quyền backend. Main dùng admin hiện có cho quản
   trị HR; HR-001 không tự cấp quyền HR cho năm tài khoản KH-KD hoặc suy quyền
   từ chức vụ trong Excel.

## Danh sách và hồ sơ

1. Chọn **Nhân viên → Danh sách nhân viên**. Tìm bằng mã TP hoặc họ tên; lọc đơn
   vị, chức danh, hồ sơ cần bổ sung hoặc chờ liên kết; nhóm theo đơn vị/chức
   danh/trạng thái. Dùng menu cột để chọn thông tin cần xem.
2. Chọn 10/20/50/100 dòng mỗi trang, mặc định 20. Đây là giới hạn trang hiện
   tại; tổng số kết quả và các trang còn lại vẫn giữ. Preference tách theo tài
   khoản/công ty/bảng, không thay phạm vi quyền.
3. Mở một dòng để xem hồ sơ native, thông tin công việc, thông tin riêng tư
   theo quyền, kỹ năng và lịch sử. Tab **Nguồn và đối chiếu** giữ mã nguồn,
   đơn vị gốc, nguyên văn chức vụ nguồn và batch nhập.
4. **Chức vụ nguồn** không tự xác nhận chức danh đã đối chiếu hoặc tình trạng
   hợp đồng. Nhãn “TV”, “Thử việc” và thông tin thiếu được giữ để rà soát;
   không suy lương, ngày vào làm, giới tính hoặc người quản lý.

## Thêm, sửa, phiên bản và lưu trữ

1. Chọn **Mới** trong danh sách hoặc **Thêm nhân viên** trên Tổng quan. Nhập họ
   tên và các dữ liệu có căn cứ; chọn đúng công ty/đơn vị. Mã TP được cấp bởi
   backend. Ví dụ mã nguồn 60 tương ứng TP10060; không sửa ID Odoo, barcode/PIN
   hoặc CCCD để thay mã nhân viên.
2. Bấm điều khiển **Lưu** của form Odoo để ghi; dùng **Hủy bỏ thay đổi** nếu
   không muốn lưu. Khi rời form còn thay đổi, xử lý hộp thoại native trước khi
   chuyển menu. Không dùng đóng trình duyệt làm thao tác lưu.
3. Dùng dòng thời gian phiên bản hoặc nút phiên bản trên form native để xem
   các phiên bản được phép truy cập. Ngày phiên bản kỹ thuật không thay ngày
   vào làm; sửa dữ liệu qua form/action chuẩn để employee/version đồng bộ.
   Bảng phiên bản có bộ chọn 10/20/50/100 dòng như các bảng HR. Luồng này chỉ mở bảng lịch sử; ô lương chưa xác nhận để trống, không dùng biểu đồ lương mặc định. Thông tin gia
   đình/số con/quãng đường chỉ hiện khi người có quyền đánh dấu đã xác nhận;
   lương cần HR manager xác nhận mức lương. Giá trị mặc định chưa xác minh
   hiện “Chưa có thông tin”, không được dùng làm dữ liệu nghiệp vụ đã chốt.
4. HR manager dùng menu thao tác **Lưu trữ** và xác nhận. Vào **Nhân viên → Lưu
   trữ**, mở hồ sơ và chọn **Bỏ lưu trữ/Khôi phục** để đưa lại vào danh sách.
   Lưu trữ hồ sơ không tự khóa tài khoản đăng nhập và không chuyển quyền KH-KD.
   Hồ sơ đã nhập giữ lịch sử; không xóa vật lý bằng luồng người dùng.
5. Nút **Chứng chỉ được phép** mở sổ chứng chỉ canonical nếu addon và quyền
   hiện có cho phép. Liên kết dựa contact công việc, không dò tên. Quyền HR
   không tự cấp quyền hồ sơ/chứng chỉ KH-KD; thiếu quyền có thể nhận thông báo
   từ chối. Kỹ năng/hồ sơ native vẫn theo quyền riêng tương ứng.

## Nhập và đối chiếu Excel

Chỉ HR manager thực hiện. File thật và bảng mapping danh tính giữ private;
không đưa danh sách người hoặc credential vào tài liệu tracked.

1. Chọn **Nhập và đối chiếu → Mới**, tải workbook được chỉ định, chọn **Phân
   tích và xem trước**. Preview tạo dòng đối chiếu, chưa tạo employee.
2. Rà số dòng và từng hành động **Tạo / Thay đổi nguồn / Bỏ qua / Cần đối chiếu**,
   chi tiết lỗi, mã nguồn và đơn vị. Nguồn HR-001 có 78 dòng hai sheet, gộp
   thành 39 người thuộc chín nhóm; STT không phải khóa nhân viên. Không nhập
   hàng giờ công.
   Dùng **Mở bảng đối chiếu đầy đủ** để rà/filter/group toàn bộ dòng và chọn
   10/20/50/100 dòng/trang, thay vì chỉ xem trang dòng nhúng trên form batch.
3. Trước áp dụng nguồn HR-001, ánh xạ **Ban Kinh Doanh → Kế hoạch Kinh doanh**
   (department ID18), **Phòng Thiết kế → Thiết kế** (ID20). Xác minh ID/tên/công
   ty theo manifest hiện tại; giữ phòng ban đang mang HEAD scope. Các nhóm khác
   theo nguồn và đối chiếu, không gộp Văn Phòng/HCNS/Tài chính theo phỏng đoán.
4. Khi nguồn thay đổi, đọc delta trước/sau; chỉ đánh dấu **Đã rà soát thay đổi
   nguồn** khi đã kiểm. Chỉnh tay trên employee được giữ và có thể khiến dòng
   chuyển thành conflict; không ghi đè để làm đủ số lượng.
5. Chọn **Áp dụng đối chiếu**, đọc kết quả create/update/skip/conflict. Các dòng
   độc lập hợp lệ có thể được áp dụng khi còn dòng conflict; số conflict phải
   được đọc và xử lý, không hiểu trạng thái “Đã áp dụng” là mọi người đã nhập
   thành công. Batch đã áp dụng là lịch sử bất biến. Sửa nguồn/đối chiếu rồi tạo
   batch mới để thử lại; không sửa file của batch đã preview.
6. Nhập lại cùng nguồn hợp lệ bỏ qua người đã có, không nhân đôi employee hay
   version. Không tự nối tài khoản bằng tên rút gọn hoặc vị trí dòng. Năm alias
   KH-KD chưa xác minh giữ **Chờ liên kết**; không tạo 39 user hoặc đổi người
   đứng tên account để đạt tỷ lệ liên kết.

## Tổng quan và Excel

1. Chọn **Tổng quan** hoặc **Báo cáo cơ cấu và Excel**. Lọc đơn vị/trạng thái hồ
   sơ; **Làm mới** để tải số liệu tại thời điểm ghi trên màn hình.
2. KPI, donut và thanh ngang cùng tập hồ sơ backend. **Đang quản lý** là cờ
   active hồ sơ, không xác nhận “nhân viên chính thức”. Bảng số liệu dưới donut
   cung cấp tên đơn vị/số lượng/tỷ lệ; chọn tên đơn vị hoặc KPI để mở danh sách
   theo bộ lọc và quyền.
3. Checklist cơ bản là mã nhân viên, đơn vị và (nhãn chức vụ nguồn hoặc chức danh đã khai báo); một hồ sơ
   thiếu nhiều trường chỉ đếm một lần. Lương, hợp đồng, thâm niên/chuyên cần
   thiếu nguồn hiện “Chưa đủ dữ liệu”.
4. Chọn **Xuất Excel** để tải hai sheet tổng hợp đơn vị/danh sách nhân viên.
   Báo cáo gồm toàn bộ tập lọc có quyền, không chỉ 20 dòng trang hiện tại;
   metadata ghi công ty, bộ lọc và thời điểm xuất. Đối chiếu tổng báo cáo với
   Tổng quan cùng bộ lọc. Báo cáo không xuất lương, CCCD hoặc tài khoản ngân hàng.

Quy trình vận hành, backup và rollback nằm trong
[runbook HR-001](../../ops/runbooks/HR_001_IMPORT_AND_ROLLBACK.md).
