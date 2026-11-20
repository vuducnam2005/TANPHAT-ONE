# BIÊN BẢN NGHIỆM THU KỸ THUẬT: SỬA LỖI TẢI LẠI TRANG LÀM TRẮNG TOÀN BỘ GIAO DIỆN (WEB-RELOAD-BLANK-001)

- **Mã hạng mục:** `CHG-20261120-013` / `WEB-RELOAD-BLANK-001`
- **Ngày thực hiện:** 20/11/2026
- **Phân hệ:** `custom_addons/tp_branding` (phiên bản `20.0.2.1.0`)
- **Trạng thái:** `PC_SERVER_APPLIED` & `VERIFIED`

---

## 1. MÔ TẢ VẤN ĐỀ & HIỆN TƯỢNG QUAN SÁT

### Hiện tượng thực tế:
- Người dùng đăng nhập hệ thống TANPHAT ONE tại domain `https://tpone.tadic.vn`, điều hướng bình thường trên các đường dẫn nghiệp vụ chuẩn hóa (như `/app/trang-chu`, `/app/nhan-su/nhan-vien`, `/app/thiet-bi/danh-sach`).
- Khi bấm nút **Tải lại (Reload / F5)** trên trình duyệt trong **cùng tab**, toàn bộ màn hình chuyển sang màu xám trắng trơn (`#f8f9fa`), mất sạch thanh điều hướng (`o_navbar`), thanh công cụ (`sidebar`) và khung nội dung (`o_action_manager`).
- Bấm F5 tiếp tục vẫn bị trắng; người dùng buộc phải đóng hẳn tab hoặc mở cửa sổ ẩn danh mới có thể vào lại.

### Nguyên nhân gốc (Root Cause):
Qua kiểm tra và thu thập log trực tiếp trên trình duyệt qua Playwright:
- Ngoại lệ bắt gặp:
  ```text
  TypeError: Failed to set the 'href' property on 'URL': Invalid URL
      at router.urlToState (router_patch.js:166)
      at router_patch.js:257
  ```
- Điểm chết cụ thể:
  Trong `@tp_branding/router_patch`, tại thời điểm boot-time (lúc nạp module JS top-level):
  ```javascript
  if (isAppPath(browser.location.pathname)) {
      const url = new URL(browser.location.href);
      router.replaceState(router.urlToState(url), { replace: true, sync: true });
  }
  ```
  Hàm `urlToState(urlObj)` thực hiện:
  ```javascript
  urlObj.href = brandHref(parsed.canonicalUrl + searchAndHash, browser.location.origin);
  ```
  Do `parsed.canonicalUrl` là đường dẫn tương đối (ví dụ `"/app/trang-chu"`), hàm `brandHref(href, origin)` trong `brand_urls.js` trước đây chỉ kiểm tra `if (!href.startsWith(origin + "/")) return brandUrl(href);` nên trả về chuỗi tương đối `"/app/trang-chu"`.
  Khi gán một chuỗi tương đối cho thuộc tính `.href` của đối tượng native `window.URL`, đặc tả WHATWG URL của trình duyệt lập tức ném ra ngoại lệ `TypeError: Failed to set the 'href' property on 'URL': Invalid URL`. Ngoại lệ này không được bắt, làm dừng toàn bộ tiến trình khởi động của Odoo JavaScript Loader, khiến component `WebClient` không bao giờ được mount, để lại màn hình trắng trơn.

---

## 2. GIẢI PHÁP KỸ THUẬT ĐÃ TRIỂN KHAI

### 2.1. Sửa triệt để hàm chuẩn hóa URL (`brand_urls.js`)
- Cập nhật `brandHref(href, origin)`: Khi có tham số `origin`, nếu `href` bắt đầu bằng `"/"` (relative path), hàm luôn ghép `origin + brandUrl(href)` để đảm bảo trả về URL tuyệt đối hợp lệ 100% (ví dụ: `https://tpone.tadic.vn/app/trang-chu`).

### 2.2. Phòng vệ đa tầng trong Router Patch (`router_patch.js`)
- **Gia cố `urlToState`:** Bọc xử lý gán `urlObj.href` trong khối `try ... catch`. Trước khi gán, kiểm tra `brandedHref` có phải là URL tuyệt đối hợp lệ hay không; nếu xảy ra lỗi thì giữ nguyên URL gốc và ghi log cảnh báo thay vì để crash.
- **Bảo vệ boot-time:** Bọc khối `router.replaceState(parsedState, ...)` trong `try ... catch`, chỉ thực hiện replaceState khi `parsedState` thực sự chứa action/model hợp lệ.

### 2.3. Nâng cấp đồng bộ Session (`brand_routes.js`)
- Cập nhật hàm `syncFromSession()` đọc từ cả 3 namespace: `session?.tp_action_routes`, `window.odoo?.session_info?.tp_action_routes`, và `window.odoo?.__session_info__?.tp_action_routes`.

### 2.4. Cơ chế Fallback & Tự phục hồi giao diện (`webclient_patch.js`)
- **Override `loadRouterState()`:** Bọc quá trình nạp action ban đầu trong `try ... catch`. Nếu xảy ra lỗi nạp action/state từ router, hệ thống tự động fallback nạp Trang chủ (`tp_web_home.action_home`) hoặc `this._loadDefaultApp()`.
- **Post-boot check (500ms):** Kiểm tra phần tử `.o_action_manager`, nếu rỗng không có view con nào được mount, tự động kích hoạt nạp Trang chủ mặc định.
- **Emergency Recovery Banner (Cứu hộ khẩn cấp sau 8 giây):** Nếu sau 8 giây ở đường dẫn `/app` mà WebClient chưa mount được navbar hoặc action manager, tự động hiển thị bảng thông báo thân thiện kèm 3 nút thao tác: *"Tải lại trang"*, *"Về Trang chủ"*, *"Đăng nhập lại"*. Banner này tự động hủy ngay khi WebClient khởi động thành công.

---

## 3. KẾT QUẢ KIỂM THỬ THỰC TẾ

### 3.1. Kiểm thử cục bộ (Unit Tests)
- `custom_addons/tp_branding/tests/test_brand_urls.py`: 12/12 test PASS 100%.
- Kiểm tra các trường hợp gán `urlObj.href` trên Node.js WHATWG URL: Đạt yêu cầu tuyệt đối, không còn phát sinh `TypeError`.

### 3.2. Kiểm thử tự động trên máy chủ PC Server thật (`192.168.1.73:8069`) qua Playwright
Chạy script kiểm tra thực tế với session admin đang hoạt động:
1. **`/app/trang-chu`:**
   - Tải ban đầu: `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Trang chủ | TANPHAT ONE'`.
   - **Tải lại (F5) trong cùng tab:** `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Trang chủ | TANPHAT ONE'`.
   - Lỗi trang (Page errors): **0 lỗi** -> `SUCCESS`.
2. **`/app/nhan-su/nhan-vien`:**
   - Tải ban đầu: `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Danh sách nhân viên | TANPHAT ONE'`.
   - **Tải lại (F5) trong cùng tab:** `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Danh sách nhân viên | TANPHAT ONE'`.
   - Lỗi trang (Page errors): **0 lỗi** -> `SUCCESS`.
3. **`/app/thiet-bi/danh-sach`:**
   - Tải ban đầu: `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Thiết bị | TANPHAT ONE'`.
   - **Tải lại (F5) trong cùng tab:** `navbar: true`, `actionManager: true`, `actionChildren: 1`, `title: 'Thiết bị | TANPHAT ONE'`.
   - Lỗi trang (Page errors): **0 lỗi** -> `SUCCESS`.

Ảnh chụp bằng chứng sau khi F5 thành công được lưu tại:
`C:\Users\vuduc\.gemini\antigravity\brain\74fd717a-0461-478e-aa7f-37dd8b13d877\evidence_live_server_verified.png`.

---

## 4. QUÁ TRÌNH TRIỂN KHAI MÁY CHỦ PC SERVER

- **Vị trí triển khai:** PC Server (`192.168.1.73`), thư mục `C:\Projects\TANPHAT-ONE\custom_addons\tp_branding`.
- **Sao lưu trước khi áp dụng:**
  - Thư mục backup: `C:\TANPHAT-backups\web-reload-blank001\20261120T162405\`
  - Database dump: `tp_tanphat_dev_pre.dump` (10.427.007 bytes).
  - Code tarball: `tp_branding_pre.tar.gz` (72.472 bytes).
- **Quy trình áp dụng:**
  1. Đồng bộ mã nguồn đã vá từ local sang server qua SSH/SCP.
  2. Cập nhật LastWriteTime cho toàn bộ tệp assets JS/CSS/XML.
  3. Chạy `odoo-bin -u tp_branding` nâng cấp module lên `20.0.2.1.0` trên database `tp_tanphat_dev` trong container `tp-odoo` (Modules loaded OK, 0 errors).
  4. Khởi động lại container `tp-odoo`.
  5. Kiểm tra health check:
     - LAN: `http://192.168.1.73:8069/web/health` -> HTTP 200 OK (`{"status": "pass"}`).
     - Public: `https://tpone.tadic.vn/web/health` -> HTTP 200 OK (`{"status": "pass"}`).

---

## 5. KẾT LUẬN & BÀN GIAO
- Lỗi trắng toàn bộ giao diện khi reload (F5) trên URL chuẩn hóa đã được khắc phục triệt để tận gốc và có thêm cơ chế bảo vệ cứu hộ dự phòng.
- Người dùng có thể F5, mở link trực tiếp, bấm Back/Forward hoặc phục hồi tab trên bất kỳ màn hình nào thuộc domain `https://tpone.tadic.vn` mà không gặp lỗi màn hình trắng.
