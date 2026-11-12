# UI-HOME-004 — Review navbar, công cụ quản trị và icon

**Ngày:** 10/11/2026. **Trạng thái:** RESOLVED_DEV_APPLIED (CHG-20261110-006).
Phạm vi: ảnh người dùng `codex-clipboard-1fdb408b-80f7-495d-9541-a05ba52378e0.png`
và source `tp_web_home` 20.0.1.5.0 sau CHG-20261110-005. Đây là review source
của phiên điều phối và tái hiện OWL cô lập, không phải audit độc lập của agent
khác hoặc kiểm lại toàn bộ Odoo runtime/quyền. Không sửa application code.

## F-HOME-01 — Navbar bị lặp

`home_launcher.xml:43–53` thêm `<header class="tp-nav">` chứa thương hiệu,
Trang chủ và account tĩnh vào client action. Webclient đã render navbar chung,
được mở rộng tại `shell_navbar.xml`. Ảnh người dùng thể hiện hai thanh xếp chồng.

Sửa nhỏ nhất: bỏ navbar bên trong Home và CSS không còn dùng. Giữ nguyên
navbar native, app switcher, tài khoản thật, company, thông báo và nút Home.
Phần nội dung Home bắt đầu bằng tiêu đề; không ẩn navbar native bằng CSS.

## F-HOME-02 — Mất lối vào quản trị trên Home admin

`buildCatalog()` vẫn tạo `system` với Tất cả ứng dụng/Cài đặt/Quản lý ứng dụng
theo menu server trả. Nhưng trong `HomeLauncher`, phần `sections()` và panel
`#tp_home_all_apps` nằm trong nhánh `t-else` dành cho non-admin, còn admin đi
nhánh mới. Vì vậy catalog có dữ liệu nhưng không render các lối vào này cho
admin. Các unit test catalog cũ vẫn xanh không chứng minh control xuất hiện.

Native `web.NavBar.AppsMenu` vẫn dùng `menuService.getApps()`; nút 9 chấm còn
trên ảnh. Source không cho thấy việc gỡ module/menu. Chưa đăng nhập kiểm danh
sách thực tế của phiên người dùng, nên không khẳng định mọi menu runtime còn
có quyền. Cần kiểm trực tiếp Settings/Apps trên clone/dev trong correction.

Sửa nhỏ nhất: cạnh tiêu đề Home thêm hàng công cụ gọn, không thành navbar thứ
hai: Cài đặt, Quản lý ứng dụng, Tất cả ứng dụng. Reuse menu/catalog/panel hiện
hữu theo quyền thực; giữ đúng 7 thẻ phòng/chức năng, không biến ba công cụ
thành phòng mới. Panel phải ở nơi admin render được, tránh lặp template.

## F-HOME-03 — Cả 7 icon rơi vào hình tròn dự phòng

`home_launcher.xml:75,103` gọi AdminIcon bằng child `t-set="icon"` bên trong
`t-call`. Trong OWL hiện tại, nội dung child được truyền như lazy call body,
không tự trở thành tham số dùng trong điều kiện của template được gọi.
AdminIcon nhận icon chưa xác định nên rơi vào nhánh `t-else` vẽ circle.

Đã tái hiện với chính `addons/web/static/lib/owl/owl.js` và template AdminIcon
trong source, trên Chromium cô lập không đăng nhập/không kết nối Odoo:
7/7 icon hiện tại là circle fallback; truyền tham số trực tiếp
`<t t-call="tp_web_home.AdminIcon" icon="item.icon"/>` cho 7/7 icon đúng nhánh.
Harness `.local/ui-home004-correction-review/icon_repro.cjs` và kết quả
`icon-reproduction.json`. Đây là minh chứng cách sửa trong harness, chưa sửa
template ứng dụng. Lần đầu harness dùng mount API cũ bị lỗi, đã đổi sang
`owl.mount` đúng runtime trước lần kiểm đạt cuối cùng.

Sửa mapping hình cho đúng nghĩa: KH-KD cặp hồ sơ; Thiết kế thước/bản vẽ;
Kỹ thuật mũ bảo hộ; BIM-QC khối mô hình; TADIC tòa nhà; HR nhóm người;
Tuyển dụng người có dấu cộng. Nhánh `ruler` hiện vẽ cân nên cũng cần chỉnh
để không gán sai ý nghĩa. Ưu tiên asset/vector native hiện có, không nạp
Lucide runtime hoặc CDN chỉ vì mockup conversation dùng Lucide.

## Kiểm tra và bước tiếp

- Ảnh xác nhận lỗi trình bày; source xác nhận nhánh admin/call site.
- Harness OWL đạt: current 7 circle, explicit argument 0 circle fallback,
  không pageerror. Đây không phải full Odoo browser test.
- `dev.py status`: Odoo18069 và PostgreSQL đang lắng nghe; không đổi runtime.
- Workflow CHG005 khớp source trước review. Không chạy lại backend/HOOT toàn
  bộ hoặc ghi nghiệp vụ/DB; kết quả CHG005 giữ lịch sử, không coi đã nghiệm thu
  hình thức hoặc mọi điều hướng chỉ vì test cũ xanh.

Giao [prompt correction](../prompts/CLAUDE_UI_HOME_004_SHELL_ICON_CORRECTION.md).
Kiểm 1 navbar, 7 icon đúng hình, 3 công cụ mở đúng, app switcher còn đủ menu
theo quyền; regression admin/staff/HEAD và responsive. Chốt correction Home
trước khi chuyển sang HR-001 S1. Không tự áp code hoặc triển khai HR ở review này.

## Kết quả xử lý — CHG-20261110-006 (Đã khắc phục 100%)

- **F-HOME-01 (Navbar bị lặp):** ĐÃ KHẮC PHỤC. Đã xóa toàn bộ `<header class="tp-nav">` và CSS dead code (`.tp-nav`, `.tp-brand`, `.tp-account`, `.tp-avatar`). Giữ nguyên duy nhất `.o_main_navbar` native của Odoo.
- **F-HOME-02 (Mất lối vào quản trị):** ĐÃ KHẮC PHỤC. Đã thêm `.tp-admin-tools` gồm 3 nút công cụ gọn bên cạnh tiêu đề Trang chủ quản trị: Cài đặt (`base.menu_administration`), Quản lý ứng dụng (`base.menu_management`), Tất cả ứng dụng (`all-apps`). Panel `#tp_home_all_apps` được tích hợp cho admin với tìm kiếm và đóng mở đầy đủ.
- **F-HOME-03 (Cả 7 icon rơi vào hình tròn dự phòng):** ĐÃ KHẮC PHỤC. Truyền explicit argument `icon="item.icon"` cho `<t t-call="tp_web_home.AdminIcon">`, sửa hình học SVG nhánh `ruler` thành thước kẻ kỹ thuật. Kết quả kiểm tra Playwright và HOOT: 0/7 icon fallback, cả 7 module hiển thị đúng hình học SVG riêng biệt.
- **Kiểm chứng:**
  * Odoo backend tests: 12/12 PASS.
  * HOOT browser tests: 28/28 PASS (100%).
  * Playwright verification trên clone (19689) và dev (18069): PASS 100% (cả admin và non-admin).
  * PRESERVATION PASS: 39 tables, no changed rows.
  * SECURITY PASS: 944 ACL/domain rows và 4 action/view/field group tables giữ nguyên 100%.
