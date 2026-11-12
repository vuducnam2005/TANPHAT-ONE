# KD-PROJECT-RESTRUCTURE-001 — Hướng dẫn sử dụng

Ngày09/11/2026. Bản20.0.1.8.0 đã chạy trên **[dev18069](http://127.0.0.1:18069/odoo)**,
database tp_tanphat_dev sau test/audit/backup+restore. Nhấn Ctrl+F5 nếu còn menu cũ.
Clone19489 chỉ phục vụ thử nghiệm; dữ liệu và credential synthetic nằm private.

**Năm tài khoản thật giữ nguyên quyền/owner. Chưa cấp capability ghi mới**, nên các nút
Cập nhật tình trạng/Thêm ghi chú/WBS mới chỉ hiện khi có grant được duyệt. Fixture HEAD
trên clone đã chứng minh action hoạt động đủ; không lấy fixture làm quyền người thật.
Đấu thầu trên dev chưa có gói mới vì14project/25CRM chưa có mapping gói/investor được
xác minh; dùng Cần đối chiếu, không nhập gói giả hoặc đổi owner để có nút.

## Chọn đúng khu vực

Trong Kế hoạch Kinh doanh, mở **Quản lý dự án → Tổng quan thực hiện** để xem
công việc, ai phụ trách, hạn và đầu ra. Chọn Dự án rồi **Mở chi tiết dự án**.
Mở **Hạng mục / WBS** để xem cấu trúc cha-con; **Công việc và tiến độ** xem theo
người/hạn trên cùng task ID. Hai màn không tạo bản sao công việc.

Mở **Quản trị dự án → Tổng quan quản trị** để đối chiếu hợp đồng/phụ lục,
giao khoán, sản lượng, nghiệm thu, kế hoạch, đề nghị thanh toán và nghĩa vụ.
Bấm **Mở hồ sơ** để đọc nguồn đã kiểm quyền. Số hồ sơ không là tổng tiền.
Hoàn tất task không là nghiệm thu; đề nghị thanh toán không là đã trả tiền.

Chọn dự án ở tổng quan, dùng **Sang quản trị / Sang quản lý** để giữ cùng project
ID. Chi tiết mỗi góc nhìn có nút chuyển tương ứng. Cùng mã/ID, cùng dữ liệu nguồn;
quyền thao tác kiểm lại ở backend. Nếu phân công bị thu hồi, chọn lại dự án trong quyền.

## Danh mục dự án và đấu thầu

**Kinh doanh và dự án → Dự án** có mã, tên, Chủ đầu tư, Đối tác theo vai,
Người phụ trách, Tình trạng dự án và Ghi chú gần nhất. Chủ đầu tư khác bên ký
thương mại: A là chủ đầu tư, B là tổng thầu ký với công ty vẫn dùng một project.
Chủ đầu tư chưa được xác minh giữ trống; không suy từ partner_id cũ.

**Đấu thầu** liệt kê gói, dự án, chủ đầu tư, đối tác, phụ trách trước hạn,
tiến trình, dự kiến giá gói và ghi chú. Một dự án nhiều gói; trong gói, chọn
**Mở / tạo lần tham gia** để mở CRM đã có. Một gói nhiều lần tham gia; ghi nhận
kết quả một gói không tự đổi project hoặc gói khác. Nhánh giao trực tiếp không
cần gói giả. Submitted chỉ là khai báo nộp chưa xác minh.

Các bảng native có tìm/lọc/nhóm, sort header, lựa chọn cột, mật độ và
10/20/50/100 dòng theo thanh công cụ hiện hành. Bảng lớn cuộn ngang trong vùng
bảng trên mobile. Xóa bộ lọc trước khi kết luận thiếu hồ sơ. Để trở lại đúng trang và thứ tự sau khi mở chi tiết, bấm breadcrumb **Dự án / Đấu thầu** phía trên. Browser Back trên bản sửa giữ đúng trang/bộ lọc/sắp xếp bằng native action state; reload bỏ tìm kiếm tạm, nên lưu Favorites nếu cần dùng lại bộ lọc.

**Cần đối chiếu** giữ CRM chưa có project hoặc hồ sơ thầu chưa biết gói.
Mapping phải có ID/nguồn/người xác minh. Người vận hành chạy dry-run rồi áp
ORM/journal; không ghép tên, đoán chủ đầu tư hoặc suy giá từ expected_revenue.
Tạo mới project/phân công người thật vẫn cần luồng vận hành/policy hiện hành,
chưa mở quyền tạo project chung cho năm tài khoản chỉ để có nút.

## Cập nhật tình trạng, ghi chú và các bên

Ở chi tiết **Quản trị dự án**, bấm **Cập nhật tình trạng**, chọn tình trạng mới,
ghi căn cứ và **Lưu cập nhật**. Thanh tình trạng chỉ hiển thị. Bốn tình trạng:
Đang theo dõi, Đang thực hiện, Tạm dừng, Kết thúc. Mở lại từ Kết thúc cần quyền
riêng. Đây là thông tin theo dõi; không ký hoặc mở hiệu lực hợp đồng.

**Thêm ghi chú** tạo sự kiện mới. Muốn sửa lời ghi cũ, chọn mục **Đính chính**
trong wizard; không overwrite/xóa nhật ký. **Xem lịch sử** cho thấy actor, thời
gian, phiên bản, trước/sau và căn cứ. Ghi chú sau submitted không thay snapshot
CRM đã nộp; không gửi email/mention ra ngoài. Nhật ký thương mại chưa phân loại
cần quyền đọc tiền hiện hành. Không ghi giá trị tiền vào metadata/task/text công khai.

Tab **Các bên tham gia → Mở các bên và vai trò** dùng danh bạ res.partner đã có.
Chọn đúng project, gói (nếu có), partner, vai trò và căn cứ. Một bên nhiều vai,
một vai nhiều bên; trùng cùng project/gói/partner/vai bị chặn. Sai quan hệ:
**Ngừng quan hệ**, ghi lý do, sau đó thêm quan hệ đúng; bản cũ được giữ.

## Giá trị gói và công việc

Trong gói, tab **Giá trị và nguồn → Mở giá gói / giá chào / phần công ty**.
Ba nghĩa tiền riêng: tổng dự kiến giá gói, giá công ty chào, phần công ty dự kiến
nhận. Ghi currency, cơ sở thuế, nguồn và ngày. Chọn Chưa xác định khi thiếu căn cứ;
0 có nguồn là ước tính bằng0. Không cộng ba loại, khác currency hoặc khác cơ sở thuế.
Sửa tiền cần quyền riêng, đúng owner, version và lịch sử trước/sau.

Trong chi tiết **Quản lý dự án**, **Thêm hạng mục / công việc** mở wizard tạo
WBS. Ghi tên, hạng mục cha cùng dự án, phụ trách đã được phân công, hạn, đầu ra
và lý do rồi **Lưu công việc**. Mở task để **Sửa hạng mục**, **Giao việc** hoặc
**Cập nhật tiến độ**. Từng action có capability riêng; progress còn cần là assignee.
Chỉ Đang thực hiện/Chờ xử lý/Hoàn tất công việc; không duyệt/hủy task bằng tiến độ.
Nút tạo Công việc/WBS từ Tổng quan KH-KD yêu cầu chọn dự án trước.

## Vì sao không có nút hoặc thao tác bị từ chối

Chức danh HEAD/DEPUTY/PLANNING/SUPPORT không tự tạo quyền. Năm tài khoản thật,
grant/owner/reviewer cũ được giữ; HEAD trên dev có thể vẫn đọc nếu chưa được cấp
capability theo policy đã duyệt. Fixture HEAD trên clone có đủ quyền mục tiêu
để kiểm; không dùng fixture đó làm bằng chứng người thật đã được cấp.

Thông báo Bạn đang xem hồ sơ: đối chiếu người phụ trách, assignment còn hiệu lực,
company/project/department và capability cần thiết. Người lập/rà soát tổng hợp cũ
có thể khác người đang đăng nhập; Administrator kỹ thuật không tự là owner.
Liên hệ người có thẩm quyền để bàn giao theo danh sách mapping, không tự đổi owner.

Lỗi hồ sơ vừa thay đổi: tải lại và mở wizard mới, không cố lưu đè. Cùng mã thao tác
cùng nội dung được xử lý idempotent; đổi nội dung sau thao tác đã ghi cần action mới.
Lỗi ngoài scope/thu hồi/hết hạn: không đổi tài khoản hay dùng đường file/chatter để né.

Ảnh thật và kết quả kiểm: xem [báo cáo nghiệm thu](KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md).
Technical verification, business acceptance và pilot authorization là ba kết luận riêng.


## Kiểm nhanh trên bản dev

1. Đăng nhập tài khoản KH-KD hiện có, mở Quản lý dự án → Tổng quan thực hiện.
2. Chọn dự án trong quyền, đọc người/hạn/đầu ra; Mở chi tiết dự án.
3. Sang quản trị, kiểm cùng mã/tên/ID; mở hồ sơ nguồn của một trong7nhóm.
4. Kinh doanh và dự án → Dự án / Đấu thầu / Cần đối chiếu để xem các danh mục.
5. Đối chiếu nút với quyền thực tế. Thiếu nút ghi mới là policy/grant/owner còn chờ,
   không dùng Administrator hoặc đổi quyền để thử. Gửi phản hồi giao diện/nghiệp vụ
   riêng, technical pass không tự là business acceptance/pilot.

[Ảnh thật dev quản lý](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-management.png>)
— [quản trị](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-governance.png>).
