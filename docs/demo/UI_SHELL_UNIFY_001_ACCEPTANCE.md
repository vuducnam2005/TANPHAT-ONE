# UI-SHELL-UNIFY-001 — Acceptance Checklist

- **Mã thay đổi**: `UI-SHELL-UNIFY-001` (`CHG-20261114-001`, `DEC-043`)
- **Trạng thái hiện tại**: `IMPLEMENTED_VERIFIED_MAIN_APPLIED` — Đã kiểm thử tự động + Playwright trên `tp_tanphat_test` (`18079`), đã sao lưu đầy đủ (`tp_tanphat_dev` DB + filestore), nâng cấp và smoke read-only trên `tp_tanphat_dev` (`18069`). Nghiệm thu trực quan, nghiệm thu nghiệp vụ và phê duyệt pilot của người dùng được ghi nhận riêng bên dưới.
- **Phạm vi addon**: `tp_web_home`, `tp_hr_workspace`, `tp_kd_workspace`, tài liệu & kiểm thử liên quan.

## 1. Trang chủ dùng chung (không tách layout `isAdmin()`)

- [x] Chỉ còn một cây template/component trang chủ cho mọi tài khoản (`#tp-unified-home` trong `home_launcher.xml`, không còn `t-if="this.isAdmin()"` chia hai bố cục).
- [x] Áp dụng phong cách trang chủ thống nhất (nền gradient sáng xanh + sóng nhẹ, navbar, chiều rộng, khoảng cách, typography, icon, bo góc, thẻ `.tp-entry`, lưới 3 cột desktop, breakpoint tablet/mobile).
- [x] Tiêu đề chung là `"Trang chủ"` và mô tả `"Không gian làm việc của TANPHAT ONE"`.
- [x] Bỏ tiêu đề `"Trang chủ quản trị"` và ghi chú `"Danh mục này chỉ dành cho quản trị hệ thống."`.
- [x] Các nhóm `Phòng ban và đơn vị`, `Nhân sự và tuyển dụng`, `Công cụ cá nhân` chỉ hiển thị khi có ít nhất 1 mục hợp lệ theo quyền.
- [x] Thẻ `KH-KD` dùng cùng tên, icon, mô tả và kiểu thẻ ở cả admin lẫn nhân viên; khi chỉ có 1 thẻ vẫn giữ kích thước ô lưới (không tự giãn thành banner lớn).
- [x] Không chừa ô trống hoặc ẩn bằng CSS các thẻ trái quyền; placeholder `"Đang phát triển"` giữ đúng phạm vi hiện hành (`user.isSystem`), không tự lộ sang nhân viên thường; bỏ fallback `hr.menu_hr_root` ở mục `Quản lý nhân sự` để người không có quyền HR không thấy thẻ HR trên Trang chủ.
- [x] Công cụ `Cài đặt`, `Quản lý ứng dụng`, `Tất cả ứng dụng` và thanh tìm kiếm chỉ hiển thị/trả về mục được cấp quyền; không rò rỉ dữ liệu tài khoản trước.

## 2. Bảo toàn quyền và bảo mật ở backend

- [x] Menu/nội dung trang chủ lấy từ menu/capability đã được Odoo server lọc (`menuService`); không phân quyền theo login, họ tên, tên chức vụ/phòng ban dạng chuỗi, `localStorage` hay payload client.
- [x] Không dùng `sudo()` để lấy danh sách ứng dụng rồi lọc ở frontend; không mở quyền HR cho nhân viên chỉ vì có hồ sơ nhân sự.
- [x] Truy cập URL/action/RPC ngoài quyền tiếp tục bị Odoo từ chối (`/odoo/settings` không hiển thị màn Settings cho `kd.thuyanh`; `kd.thanh` gọi RPC `create` trên `tp.hr.identity.wizard` nhận `AccessError`); ACL, record rule, scope công ty/phòng ban/dự án giữ nguyên.

## 3. Menu người dùng (Thông tin cá nhân & Đăng xuất)

- [x] Dropdown của menu người dùng (navbar `UserMenu`, mobile `BurgerUserMenu` và sidebar `<TpUserAccountMenu>`) có đúng 2 mục theo xác nhận của người dùng:
  1. `[icon hồ sơ] Thông tin cá nhân`: mở màn hình tự phục vụ `tp_hr_workspace.action_my_profile` (`/odoo/my-profile`) qua registry `tp_personal_profile` (tài khoản chưa gắn nhân sự hiển thị thông tin tài khoản + nút mở hộp thoại Tùy chọn & Đổi mật khẩu native `res.users.action_get`).
  2. `[icon đăng xuất] Đăng xuất`: đăng xuất thực sự qua `performNativeLogout`.
- [x] Khi mở `Thông tin cá nhân`, nhân viên xem được đầy đủ 6 tab (`Tổng quan`, `Thông tin cá nhân`, `Hồ sơ và năng lực`, `Hợp đồng lao động` ở chế độ chỉ đọc + link tải tệp/phụ lục hợp đồng của chính mình qua `/tp_hr/my_contract/<doc_id>/<file|appendix>`, `Tài khoản và phân quyền`, `Lịch sử hoạt động`), đồng thời chỉnh sửa các trường cá nhân trong allowlist + ảnh đại diện + kỹ năng/năng lực và lưu đồng bộ trực tiếp về hồ sơ `hr.employee` + chatter + live bus `tp.identity/changed` bên Admin HR; các trường tổ chức (`name`, `tp_employee_code`, `department_id`, `job_id`, `parent_id`, `work_location_id`, `company_id`), hợp đồng và vai trò bị khóa ghi/đọc nhạy cảm ở backend (`AccessError`).
- [x] Đã bỏ `"Đang đăng nhập"` + họ tên lặp lại, Hỗ trợ, Shortcuts, Online/trạng thái, `"Tài khoản và tùy chọn"`, My Subscription, đường phân cách thừa và các mục phụ khác trong danh sách trình bày.
- [x] Các service nền (presence/chat `im_status`, systray thông báo, hoạt động, chuyển công ty) vẫn giữ nguyên trong registry và hoạt động bình thường.
- [x] Giao diện dropdown gọn (~180–220px qua `.tp-logout-dropdown-menu`), nền trắng, viền nhẹ, bo góc vừa phải, mục Đăng xuất icon/chữ đỏ, hover nhẹ, focus bàn phím rõ (Enter/Escape), hiệu ứng tôn trọng `prefers-reduced-motion: reduce` (`animationName === "none"`), không tràn màn hình trên mobile.
- [x] Đăng xuất tái sử dụng cơ chế logout native (`performNativeLogout`: POST `/web/session/logout` + CSRF + `serviceWorker.controller.postMessage("user_logout")` + phản hồi lỗi khi thất bại), vô hiệu hóa session thực sự (`Back` trình duyệt / mở `/odoo` chuyển về `/web/login`), giữ xử lý `beforeunload` khi form chưa lưu.

## 4. Vị trí tên và avatar theo ngữ cảnh (mỗi màn hình một điểm truy cập)

- [x] **Trang chủ & ứng dụng native không có sidebar**: giữ `[Avatar] Tên [mũi tên]` tại góc phải navbar (`UserMenu`); mở dropdown chỉ có `Đăng xuất`.
- [x] **Workspace HR và KH-KD có sidebar**: ẩn `.o_user_menu` và `.o_mobile_menu_toggle` ở navbar qua `body.o_tp_hr_shell, body.o_tp_kd_shell` (không ẩn Home, thông báo/chat, hoạt động, chuyển công ty); thay nút `"Tài khoản"` cuối sidebar bằng `<TpUserAccountMenu>` (`[Avatar] Họ tên [mũi tên]`) mở dropdown `Đăng xuất`; xóa `identity_navbar.js` và bỏ `openAccount()`/`preferencesItem`.
- [x] **Sidebar thu gọn (`.is-rail`)**: hiển thị avatar, có tooltip/`aria-label` đầy đủ họ tên, bấm mở được dropdown `Đăng xuất`.
- [x] **Mobile (390×844 và kiểm tràn ngang 320px)**: cụm người dùng nằm ở cuối drawer/sidebar; nút mở drawer dễ thấy; dropdown `Đăng xuất` nổi trên drawer (`.o-overlay-item:has(.tp-logout-dropdown-menu)` `z-index: 1080 !important`, xác minh `elementFromPoint`); đóng dialog vẫn điều hướng bình thường.
- [x] Chuyển đổi giữa Trang chủ ↔ HR ↔ KH-KD ↔ Cài đặt, Back/Forward và reload route giữ đúng một điểm truy cập và không để sót class body cũ.

## 5. Danh tính dùng chung & cập nhật tức thì

- [x] Tên và avatar luôn lấy từ người đang đăng nhập (`tp_identity` singleton), không lẫn với hồ sơ nhân viên đang xem (Admin mở hồ sơ `Chu Thị Thuỳ Anh` vẫn hiển thị `Administrator` ở sidebar).
- [x] Tên/avatar đồng bộ giống nhau giữa Trang chủ, HR và KH-KD; hoạt động cả khi tài khoản không có hồ sơ `hr.employee`.
- [x] Có avatar chữ cái/mặc định (`computeInitials`) khi chưa có ảnh và fallback SVG chữ cái khi ảnh lỗi (`t-on-error.capture`); tên dài rút gọn hợp lý kèm tooltip đầy đủ; render text bằng OWL (escape an toàn chống XSS).
- [x] Component/service danh tính và logout dùng chung nằm tại `tp_web_home/static/src/identity/` (không trùng lặp logic giữa HR và KH-KD, không tạo dependency vòng, không truy vấn toàn bộ `hr.employee`).
- [x] Sự kiện `tp.identity/changed` cập nhật đúng người đang đăng nhập (`payload.partner_id === user.partnerId`) tại cả navbar và sidebar ngay lập tức (đã kiểm ghi `image_1920` trên `res.partner` và khôi phục), không rò listener/đăng ký bus lặp (`waitForBus` gắn một lần và hủy khi teardown).

## 6. Kiểm thử, sao lưu và áp dụng

- [x] Ruff (`0` lỗi trên `custom_addons/tp_web_home`, `tp_hr_workspace`, `tp_kd_workspace`), kiểm tra XML (`44` file hợp lệ), `git diff --check` đạt.
- [x] Odoo Python tests trên `tp_tanphat_test` (`--test-tags /tp_web_home,/tp_hr_workspace`: `80/80` đạt, `0` failed, `0` errors — gồm 5 test `TestHrSelfProfile` cho self-read/write sync/ACL/resume/skill/HTTP contract route 200 vs 403/unlinked) và HOOT unit tests trên `18079` (`tp_web_home` `35/35` — `182` assertions, `tp_hr_workspace` `41/41` — `197` assertions, `tp_kd_workspace` `22/22` — `85` assertions) đều đạt.
- [x] Playwright kiểm tra đa tài khoản & đa trạng thái (`verify_test.cjs` + `verify_extra.cjs` trên `18079`): Admin (`1440×900`, `1280×800`, Home, UserMenu 2 mục, HR, mở `Thông tin cá nhân` unlinked, xem hồ sơ `Chu Thị Thuỳ Anh` sau khi tự cập nhật xác nhận đồng bộ ngay, Settings, Back), `kd.thuyanh` (Home `1440×900`, UserMenu 2 mục, chặn `/odoo/settings`, cô lập tìm kiếm, KH-KD sidebar/rail/mobile `390×844`/mở `Thông tin cá nhân` 6 tab/kiểm tra `Hợp đồng lao động` chỉ đọc/sửa SĐT & email cá nhân/kiểm tra RPC `AccessError` trường `name`/mobile `390×844` & `320px` không tràn, BurgerUserMenu 2 mục, logout thật + Back), `kd.thanh` (từ chối RPC `tp.hr.identity.wizard`), keyboard Enter/Escape, `prefers-reduced-motion`, live `tp.identity/changed`, `beforeunload` dirty form; ảnh lưu tại `.local/ui-shell-unify001/` và đã kiểm tra trực tiếp.
- [x] Đã dừng Odoo `18069`, xác minh 0 kết nối hoạt động tới `tp_tanphat_dev`, sao lưu sạch ra `.local/ui-shell-unify001/backup-main-v2/` (`tp_tanphat_dev.dump`: `8.528.298` bytes, SHA-256 `ac5072f4d9bf5e879ff138e044d2c4889a3d148071002731c5990a0529c8d68c`, `pg_restore --list` `13.086` dòng TOC; `filestore/`: `722` tệp), nâng cấp `tp_web_home,tp_kd_workspace,tp_hr_workspace` lên `tp_tanphat_dev`, đối chiếu khớp chính xác 7 bảng cốt lõi (`res_users: 28`, `res_partner: 73`, `hr_employee: 39`, `res_groups: 57`, `ir_access: 955`, `ir_ui_menu: 360`, `ir_module_module: 694`), bật lại `18069` và kiểm smoke read-only (`smoke_main.cjs`: `MAIN 18069 SMOKE PASSED`, `0` console/page errors; đã kiểm tra trực quan ảnh `main-smoke/` gồm menu 2 mục và `Thông tin cá nhân` của `kd.thuyanh`).

- [x] Bổ sung **`UI-PERSONAL-TAB-001` (`CHG-20261114-003`)**: thiết kế lại tab `Thông tin cá nhân` trong hồ sơ nhân viên HR (`tp_hr_workspace`) thành 8 thẻ `.o_tp_hr_card` xếp 2 cột (`.o_tp_hr_personal_grid`, mobile 1 cột), bỏ khoảng trống dọc của `o_address_format`, thay `"false"` / tên mặc định giả định ở tệp nhị phân trống bằng `"Chưa có tệp"`, và Việt hóa 100% nhãn, tooltip (`help`) và selection (`sex`, `marital`, `certificate`) trên cả hồ sơ Admin HR lẫn trang tự phục vụ `Thông tin cá nhân`; đã kiểm thử `67/67` Odoo tests + `41/41` HOOT + Playwright trên `18079`, sao lưu `backup-main-v3` và áp + smoke read-only (`smoke_main_personal_tab.cjs`: `2 cols, 8 cards`, 0 lỗi) trên `18069`.
- [x] Bổ sung **`UI-HISTORY-001` (`CHG-20261114-004`)**: chặn đổ JSON thô (`before/after`, `department_transfer`) vào `mail.message` (chuyển vào `tp.hr.employee.audit`), tóm tắt sạch dữ liệu JSON cũ và Việt hóa triệt để tracking/onboarding tiếng Anh ở cả HR Chatter (`hr_history.py`) lẫn trang tự phục vụ `Thông tin cá nhân` (`my_profile`); thiết kế lại tab `Lịch sử hoạt động` với bộ lọc nhanh, badge phân loại, chip ngày hiệu lực và bảng thay đổi từng dòng; đã kiểm thử `68/68` Odoo tests + `42/42` HOOT + Playwright trên `18079`, sao lưu `backup-main-v4` và áp + smoke read-only (`smoke_main_history_tab.cjs`: `11 items`, 0 lỗi) trên `18069`.

## 7. Trạng thái các cổng chấp nhận (tách biệt theo quy trình)

- **Technical acceptance**: **PASSED** (Code, Ruff/XML44, 80 Odoo tests, 98 HOOT tests trên `18079`, Playwright `verify_test.cjs` + `verify_extra.cjs`, backup + upgrade + `verify-post` + `smoke_main.cjs` trên `18069`). *Lưu ý*: `scripts/dev.py smoke` dừng ở bước kiểm mẫu `planner.dev` vì `tp_tanphat_dev` là DB đã dọn dữ liệu mẫu theo `ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md`.
- **Visual / Business acceptance**: **PENDING_USER_REVIEW** — Cần người dùng Ctrl+F5 trên `http://127.0.0.1:18069/odoo` (hoặc xem ảnh tại `.local/ui-shell-unify001/after/` và `main-smoke/`) để xác nhận trực quan và nghiệm thu nghiệp vụ trên Admin và tài khoản nhân viên KH-KD.
- **Pilot authorization**: **PENDING_EXPLICIT_APPROVAL** — Cần phê duyệt riêng từ người dùng trước khi mở pilot / triển khai sản xuất.
