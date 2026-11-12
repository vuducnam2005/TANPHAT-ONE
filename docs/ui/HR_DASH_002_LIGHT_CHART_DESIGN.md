# HR-DASH-002 — Tổng quan nhân sự sáng cố định

Thiết kế xác lập trước triển khai trong commentary ngày 11/11/2026;
tiếp tục và ghi hồ sơ ngày 12/11/2026 (Asia/Saigon). Scope theo yêu cầu
trực tiếp: thực thi native Odoo, test18079 trước backup/apply18069,
không commit/push. Kết quả tại [acceptance](../demo/HR_DASH_002_ACCEPTANCE.md).

## Bố cục và hình thức

- Header gọn: tiêu đề, thời điểm cập nhật, thêm/xuất/làm mới.
- Thanh lọc đơn vị/chức vụ/hồ sơ; năm KPI có số lớn và icon SVG thật.
- Desktop1440: vùng biểu đồ khoảng60/40, donut khoảng297px, chú giải cạnh
  biểu đồ, thanh chức vụ18px; thấy đủ danh mục hiện hữu. Màn hẹp xếp dọc,
  donut tối đa280–300px, chú giải xuống dưới; bảng có vùng cuộn riêng.
- Nền `#F4F7FB`, vùng trắng `#FFFFFF`, chữ `#1E293B`, chữ phụ `#526277`,
  thao tác teal `#087F8C`; giữ font tiếng Việt hiện có, body14px,
  heading17/28px, số KPI34px. Giữ navbar chung. Theo phản hồi trực tiếp
  CHG-20261112-002, sidebar dùng palette Kinh doanh: nền `#17324D`, mục chọn
  `#22476A`, accent `#7FB3D5`, chữ `#DCE6F0`, chữ phụ `#9FB3C8`;
  search/hover/mobile đồng bộ. Icon native `group` trước “Nhân viên” thay
  tên `people` không được catalog Odoo hỗ trợ. Đây là cập nhật yêu cầu
  sidebar trắng ban đầu; phần nội dung dashboard giữ sáng.
- Bảng tổng hợp, checklist và liên kết tài khoản nằm sau biểu đồ. Tìm
  trong bảng có nhãn riêng; số dòng10/20/50/100 và phân trang giữ nguyên.

## Biểu đồ và tương tác

Donut SVG dùng sector có diện tích đúng tỷ lệ, vòng dày, phân cách trắng
mảnh, tổng/nhãn trong tâm. Phân màu theo ID trong toàn catalog được sắp
ổn định, không phân lại theo tập đang lọc và không dùng modulo palette.
Catalog hiện tại nằm trong14 màu riêng; ngoài palette có hue theo ID,
không bỏ nhóm. Thêm/bớt ID trong catalog có thể đổi phân bổ palette;
đổi bộ lọc/thứ tự hiện tại giữ màu. Nhóm chưa khai báo dùng xám riêng.

Hover/focus liên kết sector và legend, tooltip tên/số/tỷ lệ nằm fixed để
không bị cắt bởi khung. Escape/scroll/blur ẩn tooltip. Enter/Space và touch
mở danh sách đúng scope, không ẩn nhóm hoặc đổi tổng. Thanh chức vụ xếp
giảm dần, tie theo tên tiếng Việt rồi ID, cùng thang0, một màu teal. Vùng
cuộn chỉ giới hạn khi danh mục vượt760px, có scrollbar và nhãn tiếp cận.

Hiệu ứng180–200ms, fade nhẹ vùng biểu đồ sau tải lại, không đếm giả/quay
lặp; reduced-motion tắt hiệu ứng. Dashboard sáng cố định, sidebar navy
cố định; light color-scheme cho control, không còn dark override của
overview; không ép theme global.

## Hợp đồng dữ liệu và giới hạn

Tái sử dụng `get_overview`, `action_employees` và export hiện có; không
đổi Python/model/quyền/API/schema. Tài khoản khóa thuộc tập đã liên kết,
không là phần thứ ba của thanh tỷ lệ. Mở xanh lá, khóa đỏ, chưa liên kết
xám kèm chữ. Guard tải/response cũ/export theo loadedFilters giữ nguyên.
Không ghi roster, khóa/mở hoặc sửa mật khẩu thật để kiểm thử.

Technical verification, đánh giá hình thức/nghiệp vụ và pilot là các kết
luận riêng. Chưa có audit độc lập hay kiểm điện thoại vật lý.
