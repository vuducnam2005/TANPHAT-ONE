# UI-HOME-004 — Thiết kế Trang chủ quản trị

> [!NOTE]
> **Cập nhật UI-SHELL-UNIFY-001 (14/11/2026 — DEC-043 / CHG-20261114-001):** Thiết kế Trang chủ quản trị đã được nâng cấp thành mẫu Trang chủ dùng chung (`#tp-unified-home`) cho mọi tài khoản: tiêu đề chung `"Trang chủ"`, mô tả `"Không gian làm việc của TANPHAT ONE"`, bỏ cách gọi `"Trang chủ quản trị"` và ghi chú chỉ dành cho quản trị; quyền quyết định danh sách thẻ/nhóm hiển thị (gồm placeholder đang phát triển và cụm công cụ `Cài đặt` / `Quản lý ứng dụng` / `Tất cả ứng dụng` vẫn giữ ở `user.isSystem`). Xem [UI_SHELL_UNIFY_001_ACCEPTANCE.md](../demo/UI_SHELL_UNIFY_001_ACCEPTANCE.md).

**Ngày:** 10/11/2026 (cập nhật giao diện `UI-HOME-005` ngày 13/11/2026). **Trạng thái:** AS_BUILT_VERIFIED (CHG-20261113-001: UI-HOME-005 đồng bộ giao diện mẫu `tp_web_home` 20.0.1.6.0 trên test 18079 và dev 18069; giữ nguyên hợp đồng 7 mục/quyền của UI-HOME-004).
Yêu cầu DEC-036: đúng 7 mục và chỉ trên Trang chủ của quản trị hệ thống (`base.group_system`). Đã triển khai và kiểm chứng trên test 18079 và dev 18069 (`tp_web_home` 20.0.1.6.0).

**Làm mới giao diện UI-HOME-005 (CHG-20261113-001):** giữ nguyên 7 mục, 3 công cụ quản trị, gate `user.isSystem`, `UI-HOME-003` cho non-admin và toàn bộ hành vi/selector; nâng cấp trực quan: nền gradient xanh băng toàn màn hình với sóng chéo góc dưới-phải, thanh điều hướng navy phân cách dọc trước avatar tròn, 3 nút công cụ dạng pill trắng nổi, thanh nhấn xanh dọc ở tiêu đề nhóm, thẻ ngang (icon 52×52 bên trái + tiêu đề/badge/mô tả bên phải), lưới 3 cột đều cho 5 đơn vị (KH-KD nổi bật xanh đậm + `↗`) và lưới 2 cột cho Nhân sự (`Đang hoạt động` xanh bạc hà) & Tuyển dụng (`Đang phát triển`).

**Correction CHG-20261110-006:** khi nhúng thiết kế vào Odoo phải dùng navbar
native chung, bỏ navbar nằm trong client action. Giữ7tile; Cài đặt/Quản lý
ứng dụng/Tất cả ứng dụng là3control gọn cạnh tiêu đề, không thẻ phòng mới.
Sửa icon đang rơi circle fallback và mapping hình Thiết kế. Xem [review](../reviews/UI_HOME_004_SHELL_ICON_REVIEW.md).
Preview trước đây có shell để trình bày toàn cảnh, không yêu cầu lồng shell
đó dưới navbar Odoo. Source/runtime ứng dụng chưa sửa trong lượt review này.

## Nội dung đã chốt

| Nhóm giao diện | Mục | Hành vi dự kiến khi triển khai |
| --- | --- | --- |
| Phòng ban và đơn vị | Kế hoạch Kinh doanh | Mở workspace KH-KD hiện hữu theo quyền |
| Phòng ban và đơn vị | Phòng Thiết kế | Trang Đang phát triển có đúng tên |
| Phòng ban và đơn vị | Phòng Kỹ Thuật | Trang Đang phát triển có đúng tên |
| Phòng ban và đơn vị | Phòng BIM-QC | Trang Đang phát triển có đúng tên |
| Phòng ban và đơn vị | TADIC | Trang Đang phát triển có đúng tên |
| Nhân sự và tuyển dụng | Quản lý nhân sự | Lối vào HR native theo module/quyền; bước phát triển tiếp |
| Nhân sự và tuyển dụng | Tuyển dụng | Lối vào recruitment native theo module/quyền; chưa giả đã hoàn thiện |

Không thêm Ban Giám đốc, Ban quản trị - Tài chính, TACICO hoặc Văn Phòng vào
khung admin này. Đó là lựa chọn điều hướng, không xóa 4 nhóm hoặc nhân viên
tương ứng khỏi danh mục tổ chức 9 nhóm/39 người trong nguồn.

## Bố cục và token

- Navbar navy, thương hiệu TANPHAT ONE; nội dung Trang chủ quản trị, không
  sửa login/logout. Hai nhóm nội dung rõ ràng, không trộn phòng với chức năng HR.
- Grid 3 cột desktop: KH-KD chiếm 2 ô ở hàng đầu, Thiết kế 1 ô; hàng sau
  Kỹ Thuật/BIM-QC/TADIC. Hai thẻ Nhân sự/Tuyển dụng nằm ở hàng riêng chia đôi.
- Tablet 2 cột; mobile 1 cột. Nội dung không có KPI hoặc số thông báo giả,
  không thêm công cụ cá nhân vào 7 thẻ. Native switcher/menu hợp lệ vẫn giữ.
- Navy `#22344e`, điểm nhấn KH-KD `#223b59`; nền sáng `#f3f6fa`, panel trắng,
  chữ `#24344c`, phụ `#64748b`, viền `#dfe6ef`. Preview có palette tối riêng
  theo giao diện host. Giữ màu native sản phẩm khi triển khai thực tế.
- Trạng thái: đang hoạt động xanh lá nhẹ, đang phát triển amber, bước HR kế
  tiếp xanh dương. Có chữ đi kèm; không tô màu thành công cho chức năng chưa có.
- Font Segoe UI/Arial hỗ trợ tiếng Việt, nội dung 14–15px, tiêu đề 26px;
  khoảng cách 13px, card 120–140px tùy nội dung, radius 14px có thể chỉnh.
- Hover 180ms, focus rõ và reduced-motion; bố cục tự tăng chiều cao khi chữ
  xuống dòng, không dùng zoom để ép thẻ vừa khung.

## Định nghĩa admin và quyền

- Đề xuất thực thi admin = `base.group_system` từ backend, tương ứng session
  `user.isSystem` hiện có để trình bày. Không suy từ tên/login, user ID hoặc
  group custom Platform Manager; không bật superuser để render Home.
- Thuỳ Anh là HEAD nghiệp vụ theo DEC-033, không tự là admin. Chỉ hiện khung
  7 mục khi account có quyền quản trị hệ thống thực sự.
- Người thường giữ Home/menu theo role đang có, đặc biệt KH-KD và công cụ cá
  nhân; không làm mất lối vào KH-KD chỉ vì khung 7 mục admin-only.
- Ẩn card không cấp/thu hồi quyền dữ liệu. Route/client action placeholder
  của catalog admin phải kiểm nhóm phía máy chủ; module HR thực vẫn theo ACL
  native của HR, không tự cấp HR manager cho hệ thống hoặc HEAD từ thay đổi Home.
- Khi chuyển user hoặc thu hồi nhóm phải reload quyền, không dùng cache Home
  admin của phiên trước. Kiểm app switcher không hiển thị thêm entry giả cho staff.

## Bản xem trước và kiểm tra

Inline source: `C:\Users\vuduc\.codex\visualizations\2026\10\28\01a18039-277f-7690-8dc5-f7a79ce1080d\tanphat-admin-home.html`.
Evidence local: `.local/ui-home004-design/` gồm preview wrapper, screenshot
desktop/mobile và trang HR dự kiến, `verify_preview.cjs`, `verification.json`.

Preview có đúng 7 card, bấm các mục thấy đúng tiêu đề/trạng thái, Về Trang chủ
trả focus về card. HR thể hiện 4 nhóm nền tảng dự kiến, không chứa dữ liệu
nhân viên thật hoặc mô phỏng ghi vào Odoo. 31 kiểm tra Playwright đạt, không
pageerror; kiểm 1440/1024/768/390/320px, light/dark và reduced-motion. Đã xem ảnh
1024px/390px. Kiểm chứng as-built thực tế trên dev 18069: Playwright 13 kịch bản đạt 100%, Odoo tests 12/12, HOOT 27/27, bảo toàn 39 bảng và 944 ACL rows.

## Trạng thái thực tế và Thứ tự tiếp theo

1. UI-HOME-004 đã hoàn thành và áp dụng lên dev 18069 (`tp_web_home` 20.0.1.5.0).
   Xem [Acceptance](../demo/UI_HOME_004_ACCEPTANCE.md) và [Hướng dẫn](../demo/UI_HOME_004_USER_GUIDE.md).
2. Chuẩn bị triển khai HR-001 S1 theo [kế hoạch nền nhân sự](../architecture/TP_HR_001_FOUNDATION_PLAN.md),
   tái sử dụng `hr`, `hr.department`, `hr.job` và private roster; không xây lại
   hồ sơ nhân viên hoặc account song song.
3. Tuyển dụng là chặng tiếp sau nền HR, tích hợp module chuẩn khi được giao;
   payroll/chấm công/nghỉ phép có quy tắc riêng, không gộp vào đợt Home.
