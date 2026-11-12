# HR-PROFILE-005 — Hồ sơ và quản lý tài khoản theo ảnh người dùng

Cập nhật007/CHG-20261112-010: hồ sơ gọn hơn vừa phải, avatar desktop88px,
tên26–32px, tab15px, thông tin16px, title18px; sheet padding24×28px,
gaps20–24px, nút toolbar/chức vụ40px (chức vụ mobile tối thiểu44px).
Mobile avatar64px/tên25px giữ. Thay các kích thước hồ sơ005 bên dưới;
modal tài khoản/chức vụ và sidebar giữ nguyên. Sheet cùng1672px giảm16.1%.

Cập nhật006/CHG-20261112-009: sidebar giữ nguyên màu/chiều rộng/trạng thái như
list; bỏ rail/palette riêng của profile. Chỉ phần hồ sơ/modal theo thiết kế dưới.

12/11/2026, CHG-20261112-008. Hai ảnh là tham chiếu hình thức theo yêu cầu trực
tiếp; chữ/dữ liệu minh họa không phải lệnh đổi người thật. Việt hóa nhãn English.

```text
Thanh native: Quay lại | Sửa hồ sơ | Hồ sơ nhân viên | Lịch sử | phân trang
Nền xanh băng, khối hồ sơ trắng bo góc
  Avatar lớn | Tên đậm | badge Mở/Khóa/Chưa có tài khoản
               Mã TP | phòng | chức vụ, có biểu tượng
  [Đổi chức vụ] | chú thích
  Tabs có icon, Tổng quan được tô xanh nhạt
  [Thông tin công việc]   [Liên hệ công việc]
  icon / Tài khoản cá nhân | icon / Vai trò nghiệp vụ | Quản lý tài khoản

Tài khoản nhân viên — Tên                         [x]
  Nhân viên / Mã / Phòng / Chức vụ | Login / Tình trạng
  Lý do thao tác [input dài]
  [Khóa tài khoản đỏ] [Đặt lại mật khẩu]
  -----------------------------------------------
  [Đóng]
```

Palette ảnh: navy#0E2038, teal#008395/#006C7C, ice#E5F4FC/#F3FAFE,
white#FFFFFF, line#D8E6EF, red#D62F36. Font system-ui trong vùng hồ sơ/modal, giữ font Odoo ngoài scope; tên36–40px700,
title20px600, labels16px/input16px. Sheet max1510px, padding32–40px, gaps24–32;
hai khối có header xanh nhạt và các hàng phân cách. Header có sóng nhẹ bằng
CSS, không bitmap hoặc thư viện mới. Nút44px, hover180ms/focus rõ/reduced motion.

Giữ shared native navbar/menu thay vì thêm icon menu giả theo ảnh. Sidebar
native có chế độ rail sẵn; không thay preference hoặc điều hướng ngoài scope.
Mobile xếp1cột, tabs cuộn ngang, modal co trong viewport, footer luôn truy cập.
Native form validation/save/cancel/version/history, check_identity/password/
lock/scope và unique HEAD giữ nguyên. Không sao chép chữ English hoặc dữ liệu
người trong ảnh vào database. Không thêm state nghiệp vụ/model/ACL/API. Không có trạng thái rail riêng cho profile từ006.

Acceptance: cùng bố cục/card/header/buttons/icons/badge/modal như ảnh; đủ3trạng
thái account, nhãn Việt; native edit/cancel/validation và các tab/history hoạt
động; dialog lock/unlock/reset/create giữ guard; desktop/mobile/focus/reduced/
console/nooverflow; ảnh trước–sau cùng actor/route/dataset/viewport. Technical
verification riêng visual/business/pilot. Fixture giả chỉ test, main đọc/hủy.
