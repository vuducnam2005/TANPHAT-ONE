# UI-BACK-001 — Chuẩn nút "← Quay lại" toàn hệ thống

Ngày 15/11/2026 · `CHG-20261115-002` · Quyết định [DEC-046](../DECISIONS.md) ·
áp trên main `tp_tanphat_dev` (`18069`) với `tp_web_home` **20.0.1.8.0**,
`tp_equipment` **20.0.1.4.0**, `tp_hr_workspace` **20.0.1.11.5**.

Cập nhật 16/11/2026 (`CHG-20261116-003`, `tp_equipment` **20.0.1.5.0**): fallback deep link thiết bị đang quản lý, chưa gắn máy khác (device/component) về danh sách **Thiết bị**; nháp, ngừng quản lý, dịch vụ và linh kiện đã gắn về **Tất cả hồ sơ thiết bị**. Client action cũ `tp_equipment.dashboard` (path `tong-quan-thiet-bi`) chuyển sang danh sách Thiết bị (`static/src/redirect.js`). Leaf hoặc last-leaf trỏ menu đã ẩn rơi về **Thiết bị** (hoặc **Yêu cầu đề xuất** với model đề xuất). Quan sát: form máy Đang sử dụng có 1 nút Quay lại và quay về giữ segment Đang sử dụng; `tong-quan-thiet-bi` về `kho-thiet-bi`, `ton-kho-thiet-bi` vẫn mở list tồn kho, sidebar sáng **Thiết bị**, 0 dialog lỗi.

Tài liệu này là quy ước cho mọi màn chi tiết hiện có và màn/phòng ban mới. Nó ghi
cách hoạt động, phạm vi phủ và lý do N/A; không thay cho nghiệm thu nghiệp vụ.

## 1. Quy tắc hiển thị

- **Đúng một** nút `← Quay lại` trên mỗi màn chi tiết bản ghi trong luồng chính
  (act_window, `viewType = form`, không ở dialog, không thuộc model cấu hình bị loại).
- Nút nằm đầu control panel, cao **40px** (desktop/tablet) và **44px** khi màn hẹp
  (mobile), có tooltip/aria-label `Quay lại: <tên màn trước>` hoặc
  `Quay lại danh sách` khi màn trước không có tên, có focus ring khi dùng bàn phím.
- **Không có nút** trên: Trang chủ, dashboard/client action tổng quan, list/kanban,
  trang đăng nhập/đăng xuất, `res.config.settings` và wizard nâng/gỡ module.
- **Popup/wizard/dialog** giữ `Đóng`/`Hủy` theo ngữ cảnh, không thêm Quay lại.
- Màn custom không dùng control panel (ví dụ **Hồ sơ của tôi**) dùng cùng class
  `o_tp_back_button`, cùng hàm `navigateBack` và cùng quy tắc trở về.

## 2. Quy tắc trở về

1. Có màn trước trong action stack → `action.restore(jsId)` của breadcrumb trước.
   Odoo khôi phục controller cũ, nên bộ lọc, trang, số dòng/trang và nhóm được giữ.
   Không dùng `window.history.back()`.
2. Không có màn trước (deep link, mở URL trực tiếp, F5 trên form) → fallback đăng
   ký theo model trong registry `tp_back_fallbacks` (chỉ nhận **xmlid** hợp lệ,
   mọi giá trị khác bị từ chối):
   - `maintenance.equipment`: theo nơi giữ hiện tại — nhân viên/mượn có người
     → **Thiết bị & người sử dụng**; trong kho → **Thiết bị tồn kho**; dùng chung/
     chưa rõ người → **Thiết bị dùng chung & chưa xác định người**; ngừng quản lý
     hoặc khác → **Tất cả hồ sơ thiết bị**. Nếu form mở bằng URL model thiếu trường
     nơi giữ, helper đọc **chỉ đọc** 3 trường (`tp_custody`, `tp_lifecycle`,
     `tp_employee_id`) rồi mới quyết định.
   - Phiếu bàn giao, sửa chữa, đề xuất, phiếu nhập, kiểm kê, đợt nhập, loại, vị trí
     của Kho → list tương ứng; `hr.employee`/phòng ban/chức danh/địa điểm/nhóm/đợt
     nhập HR → list HR tương ứng.
3. Không có fallback đăng ký → list của chính action nếu action có list/kanban.
4. Cuối cùng → Trang chủ. Fallback luôn mở với `clearBreadcrumbs`.

## 3. Bảo vệ thay đổi chưa lưu và an toàn

- Form đang có thay đổi → hộp thoại **Thay đổi chưa lưu**: `Lưu rồi quay lại`,
  `Bỏ thay đổi`, `Ở lại`. Lưu lỗi (bắt buộc/ràng buộc) thì ở lại form, giữ dữ liệu
  đang nhập; không tự lưu, không `forceLeave`.
- Chống bấm kép (nút tắt khi đang xử lý, `aria-busy`); nút không tự ghi dữ liệu và
  không lưu bản ghi vào bộ nhớ đệm riêng.
- Không MutationObserver, không sửa core `odoo/`/`addons/`, không router mới.

## 4. Vị trí source

| Phần | File |
| --- | --- |
| Nút và patch control panel | `custom_addons/tp_web_home/static/src/back/back_button.{js,xml,scss}` |
| Helper dùng chung | `custom_addons/tp_web_home/static/src/back/back_navigation.js` (`navigateBack`, `resolveBackTarget`, `resolveBackFallback`, `backTooltip`, `leaveRecordAndGoBack`, `TpUnsavedBackDialog`) |
| Fallback Kho | `custom_addons/tp_equipment/static/src/back_fallbacks.js` |
| Fallback HR, Hồ sơ của tôi | `custom_addons/tp_hr_workspace/static/src/profile/employee_profile.js`, `my_profile/my_profile.{js,xml}` |
| Test HOOT | `custom_addons/tp_web_home/static/tests/back/back_button.test.js` |

**Màn mới:** không tự vẽ nút Quay lại. Form act_window tự có nút; chỉ đăng ký
`registry.category("tp_back_fallbacks").add("<model>", "<module>.<action_xmlid>")`
(hoặc hàm trả xmlid) để deep link về đúng list. Client action có màn chi tiết
riêng thì gọi `navigateBack(env, actionService)` và dùng class `o_tp_back_button`.

## 5. Inventory phủ màn hình (18069, 15/11/2026)

| Nhóm màn | Trạng thái | Bằng chứng / lý do |
| --- | --- | --- |
| Kho — form thiết bị từ danh sách **Thiết bị** (segment Tất cả / Đang sử dụng / Trong kho, CHG-20261116-003) | PHỦ, quan sát dữ liệu thật | 1 nút; quay lại giữ segment Đang sử dụng; popup Gán / Đổi máy / Trả về kho và form ngắn Thêm / Sửa giữ `Hủy`/`Đóng`, 0 nút Quay lại |
| Kho — form thiết bị từ **Thiết bị & người sử dụng**, **Tồn kho**, **Dùng chung**, **Tất cả hồ sơ**, drill-down dashboard | PHỦ, quan sát dữ liệu thật | 1 nút; về đúng list giữ lọc/trang/số dòng (trang 2, 10 dòng/trang, lọc loại); 3 deep link về đúng list theo nơi giữ |
| Kho — form đề xuất `DX-00001` | PHỦ, quan sát | 1 nút, tooltip `Quay lại: Đề xuất thiết bị`, về list |
| Kho — phiếu bàn giao/sửa/nhập/kiểm kê/đợt nhập/loại/vị trí | PHỦ theo cùng quy tắc | Dùng chung patch control panel và fallback đăng ký; list phần lớn rỗng nên chưa mở form có dữ liệu |
| HR — form nhân viên, bản ghi liên quan (thiết bị của nhân viên) | PHỦ, quan sát | Nút HR cũ `o_tp_hr_back` đã bỏ, còn đúng 1 nút; bản ghi liên quan về danh sách thiết bị của nhân viên; nhân viên về danh sách nhân viên |
| HR — Hồ sơ của tôi (client action) | PHỦ, quan sát | 1 nút cùng class/helper |
| KH-KD — cơ hội, dự án, công việc/WBS, gói thầu, nghĩa vụ, thanh toán, nghiệm thu… | PHỦ theo cùng quy tắc, **chưa quan sát có dữ liệu** | DB 18069 có 0 `crm.lead`, 0 dự án `tp_managed`, 0 task, 0 gói thầu; không tạo dữ liệu giả để chụp |
| Hợp đồng `tp.contract` | PHỦ theo cùng quy tắc, **chưa quan sát có dữ liệu** | DB 18069 có 0 hợp đồng |
| Form native khác đang cài (người dùng, công ty…) | PHỦ theo cùng quy tắc | Cùng patch control panel; không mở từng màn trong lượt này |
| Popup form / wizard / dialog | N/A có chủ đích | Giữ `Đóng`/`Hủy`; quan sát popup form: 0 nút Quay lại |
| Trang chủ, dashboard Kho, tổng quan HR, landing KD (`Tổng quan`, `Tổng quan thực hiện`, `Tổng quan quản trị`) | N/A có chủ đích | Không phải màn chi tiết; quan sát 0 nút |
| List/kanban | N/A có chủ đích | Điều hướng bằng menu/breadcrumb; quan sát 0 nút |
| `res.config.settings` (Cài đặt), wizard nâng/gỡ module | N/A có chủ đích | Model bị loại trong `BACK_EXCLUDED_MODELS`; quan sát Cài đặt: 0 nút |
| Đăng nhập/đăng xuất, đặt lại mật khẩu | N/A có chủ đích | Trang ngoài web client; link `Quay lại đăng nhập` là luồng đăng nhập riêng |
| Quét mã thiết bị (client action công cụ) | N/A có chủ đích | Trang công cụ, không phải chi tiết bản ghi; quan sát 0 nút |
| `tp_dashboard_privacy` — nút `Quay lại` của panel tìm kiếm mobile | N/A (khác chức năng) | Đóng panel tìm kiếm, không điều hướng màn |

## 6. Kiểm thực đã chạy

- HOOT `tp_web_home` 44/44 (gồm fallback đồng bộ/bất đồng bộ chỉ đọc, đúng 1 nút,
  tooltip có/không tên, dirty stay/discard, popup không có nút), `tp_hr_workspace`
  40/40. `tp_equipment` không có bộ HOOT riêng; fallback Kho được kiểm bằng
  trình duyệt trên dữ liệu thật.
- Playwright `.local/equip-ui002/verify_ui002.mjs`: 42 PASS, 0 FAIL, 0 console error;
  `.local/equip-ui002/check_coverage.mjs` cho inventory ở mục 5.
- Chưa chạy test Python Odoo trên DB thật; chưa quan sát KH-KD/hợp đồng có dữ liệu.
