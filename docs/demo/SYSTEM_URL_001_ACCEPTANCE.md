# SYSTEM-URL-001 — Tiêu chí nghiệm thu chuẩn hóa URL phân hệ và màn hình TANPHAT ONE

- **Mã nhiệm vụ:** `SYSTEM-URL-001`
- **Mã thay đổi:** `CHG-20261120-009`
- **Ngày thực hiện:** 20/11/2026 (Asia/Saigon).
- **Trạng thái:** `ACCEPTANCE_RUN_PASS` (Kiểm thử 31/31 Odoo test PASS trên local test `tp_tanphat_test`, đã nâng cấp `tp_tanphat_dev` local, đã sao lưu và deploy lên PC Server Docker `192.168.1.73`, đã xác minh toàn diện trên public domain `https://tpone.tadic.vn`).
- **Tài liệu quy chuẩn:**
  - [Quy chuẩn đặt tên URL](../../docs/ui/TP_URL_NAMING_STANDARD.md)
  - [Bảng kiểm kê 46 URL toàn hệ thống](../../docs/ui/TP_URL_ROUTE_INVENTORY.md)
- **Môi trường:**
  - `tp_tanphat_test` (Local 18179, DB 55432): Chạy toàn bộ 31 Odoo tests (12 unit test + 19 HTTP test).
  - `tp_tanphat_dev` (Local 18069, DB 55432): Nâng cấp module `tp_branding` `20.0.2.0.0` thành công.
  - `PC server` (192.168.1.73, container `tp-odoo`, `tp-postgres`, `tp-tunnel`): Đã backup, upgrade module, restart và verify.
  - Public Domain: `https://tpone.tadic.vn`

---

## 1. 8 Quy tắc vàng URL TANPHAT ONE

1. **Tiếng Việt không dấu**, chữ thường (`kebab-case`).
2. **Dấu gạch ngang** (`-`) phân cách giữa các từ.
3. **Phân hệ cố định:** `nhan-su`, `khkd` (tuyệt đối không viết nhầm `khkh`), `thiet-bi`, `bao-cao`, `quan-tri`, `trang-chu`.
4. **Tên ngắn gọn, đúng nghiệp vụ:** không dùng tên kỹ thuật model Odoo hay tên component làm đường dẫn chính.
5. **Không dùng `action-ID` (như `action-528`) làm URL chính** cho người dùng.
6. **Bảo mật:** Tuyệt đối không đưa họ tên, mật khẩu hoặc token vào URL.
7. **Chi tiết hồ sơ:** Dùng ID số nguyên nguyên thủy (`/app/nhan-su/nhan-vien/44`); tạo mới dùng `/tao-moi`.
8. **Phân biệt rõ ràng:** Quản lý dự án (`/app/khkd/quan-ly-du-an`) và Quản trị dự án (`/app/khkd/quan-tri-du-an`).

---

## 2. Bảng kết quả kiểm chứng thực tế

### 2.1. Kiểm thử tự động Odoo (`tp_branding` 20.0.2.0.0)

Lệnh chạy:
```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test --http-port 18179 --test-tags /tp_branding --stop-after-init --max-cron-threads=0
```

| Nhóm Test | Số lượng ca | Kết quả | Chi tiết |
| --- | --- | --- | --- |
| `TestBrandUrls` (Unit Tests) | 12 tests | **PASS (100%)** | Regex, prefix, canonical_app_path, XML ID integrity, registry parity Python & JS |
| `TestBrandingHttp` (HttpCase) | 19 tests | **PASS (100%)** | Deep link phân cấp, anonymous redirect login, session_info dynamic route map, login branding layout |
| **Tổng cộng** | **31 tests** | **0 failed, 0 error(s)** | Thời gian chạy: 31.30s |

### 2.2. Kiểm chứng trực tiếp trên Public Domain (`https://tpone.tadic.vn`)

Lệnh chạy:
```powershell
.\.venv\Scripts\python.exe scripts/verify_public_urls.py
```

| STT | Endpoint / URL kiểm tra | Loại URL | Kỳ vọng | Thực tế | Đánh giá |
| --- | --- | --- | --- | --- | --- |
| 1 | `https://tpone.tadic.vn/web/health` | Healthcheck | HTTP 200 OK | HTTP 200 | **PASS** |
| 2 | `https://tpone.tadic.vn/dang-nhap` | Đăng nhập | HTTP 200 OK, thương hiệu TANPHAT ONE, copyright by Tadic | HTTP 200, TANPHAT ONE, by Tadic | **PASS** |
| 3 | `/app/nhan-su/nhan-vien/44` | Chi tiết nhân viên | Redirect 303 -> `/dang-nhap?redirect=/app/nhan-su/nhan-vien/44` | Redirect 303 đúng redirect param | **PASS** |
| 4 | `/app/nhan-su/nhan-vien/tao-moi` | Tạo mới nhân viên | Redirect 303 -> `/dang-nhap?redirect=/app/nhan-su/nhan-vien/tao-moi` | Redirect 303 đúng redirect param | **PASS** |
| 5 | `/app/nhan-su/nhan-vien` | Danh sách nhân viên | Redirect 303 -> `/dang-nhap?redirect=/app/nhan-su/nhan-vien` | Redirect 303 đúng redirect param | **PASS** |
| 6 | `/app/nhan-su/phong-ban` | Phòng ban | Redirect 303 -> `/dang-nhap?redirect=/app/nhan-su/phong-ban` | Redirect 303 đúng redirect param | **PASS** |
| 7 | `/app/nhan-su/cham-cong/tong-quan` | Chấm công | Redirect 303 -> `/dang-nhap?redirect=/app/nhan-su/cham-cong/tong-quan` | Redirect 303 đúng redirect param | **PASS** |
| 8 | `/app/khkd/tong-quan` | KH-KD Tổng quan | Redirect 303 -> `/dang-nhap?redirect=/app/khkd/tong-quan` | Redirect 303 đúng redirect param | **PASS** |
| 9 | `/app/khkd/du-an-tiem-nang` | Dự án tiềm năng | Redirect 303 -> `/dang-nhap?redirect=/app/khkd/du-an-tiem-nang` | Redirect 303 đúng redirect param | **PASS** |
| 10 | `/app/khkd/quan-ly-du-an` | Quản lý dự án | Redirect 303 -> `/dang-nhap?redirect=/app/khkd/quan-ly-du-an` | Redirect 303 đúng redirect param | **PASS** |
| 11 | `/app/khkd/quan-tri-du-an` | Quản trị dự án | Redirect 303 -> `/dang-nhap?redirect=/app/khkd/quan-tri-du-an` | Redirect 303 đúng redirect param | **PASS** |
| 12 | `/app/thiet-bi/danh-sach` | Danh sách thiết bị | Redirect 303 -> `/dang-nhap?redirect=/app/thiet-bi/danh-sach` | Redirect 303 đúng redirect param | **PASS** |
| 13 | `/app/thiet-bi/danh-sach/5` | Chi tiết thiết bị | Redirect 303 -> `/dang-nhap?redirect=/app/thiet-bi/danh-sach/5` | Redirect 303 đúng redirect param | **PASS** |
| 14 | `/app/bao-cao/tong-quan` | Báo cáo điều hành | Redirect 303 -> `/dang-nhap?redirect=/app/bao-cao/tong-quan` | Redirect 303 đúng redirect param | **PASS** |
| 15 | `/app/quan-tri/tai-khoan` | Quản trị tài khoản | Redirect 303 -> `/dang-nhap?redirect=/app/quan-tri/tai-khoan` | Redirect 303 đúng redirect param | **PASS** |
| 16 | `/odoo` | Legacy URL | 302 -> `/app` | 302 -> `/app` | **PASS** |
| 17 | `/odoo/action-528` | Legacy Action URL | 302 -> `/app/action-528` | 302 -> `/app/action-528` | **PASS** |
| 18 | `/odoo/tp-home` | Legacy Home URL | 302 -> `/app/tp-home` | 302 -> `/app/tp-home` | **PASS** |
| 19 | `/web` | Legacy Web URL | 302 -> `/app` | 302 -> `/app` | **PASS** |
| 20 | `/web/login` | Legacy Login URL | 302 -> `/dang-nhap` | 302 -> `/dang-nhap` | **PASS** |

### 2.3. Kiểm chứng ánh xạ động backend (Dynamic Action ID Mapping)

Trên PC Server `tp_tanphat_dev`, hàm `_tp_get_url_route_map()` truy vấn động bảng `ir_model_data` theo XML ID:
- Tổng số action đã ánh xạ thành công: **45 actions**
- Action nhân viên: `tp_hr_workspace.action_employees` -> **ID 528** (trùng khớp chính xác với `action-528` mà người dùng đang thấy).
- Cơ chế không phụ thuộc vào ID cứng, tự động tương thích giữa local dev và server PC.

---

## 3. Bản sao lưu trước khi áp (Backup Evidence)

Được lưu trữ an toàn trên PC Server tại:
`C:\TANPHAT-backups\system-url001\20261120T143858\`

Bao gồm:
1. `tp_tanphat_dev_pre.dump` (Kích thước: `10.405.836` bytes, dump định dạng custom `-F c`).
2. `tp_branding_pre.tar.gz` (Mã nguồn `tp_branding` phiên bản trước khi triển khai).
3. `deploy_package.tar.gz` (Gói triển khai đã giải nén).
