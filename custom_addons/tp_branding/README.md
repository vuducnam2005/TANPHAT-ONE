# tp_branding — TANPHAT ONE identity and `/app` URLs

BRAND-WHITELABEL-002 · CHG-20261117-002 · LGPL-3

Nhận diện TANPHAT ONE cho toàn bộ giao diện người dùng và bộ đường dẫn có
thương hiệu. Module chỉ đổi URL, tiêu đề, nhãn và logo; không đổi dữ liệu,
quyền, record rule, chính sách đăng ký/đặt lại mật khẩu hay giao diện đăng
nhập đã duyệt (UI-LOGIN-002, `tp_web_login`).

## Đường dẫn

| Native | TANPHAT ONE | Ghi chú |
| --- | --- | --- |
| `/odoo`, `/odoo/...`, `/web` | `/app`, `/app/...` | webclient; `/web#...` đi qua `/app` rồi được router chuẩn hoá |
| `/web/login` | `/dang-nhap` | form POST thẳng vào `/dang-nhap` |
| `/web/login/totp` | `/dang-nhap/xac-thuc` | |
| `/web/reset_password` | `/quen-mat-khau` | vẫn theo `auth_signup.reset_password` |
| `/web/signup` | `/tao-tai-khoan` | vẫn theo `auth_signup.invitation_scope`; không tự bật |
| `/` | `/dang-nhap` · `/app` · `/my` | theo phiên: ẩn danh · nội bộ · portal |

* Chỉ **GET/HEAD** trên đường dẫn cũ nhận **302** sang đường dẫn mới; query
  giữ nguyên byte, `#fragment` do trình duyệt giữ.
* **Không bao giờ** chuyển hướng POST, JSON-RPC, upload, logout, assets,
  `/web/...` kỹ thuật, `/odoo/offline`. CSRF và ACL do lõi Odoo xử lý như cũ.
* Helper thuần (`brand_urls.py`, `static/src/brand_urls.js`) chỉ đổi tiền tố
  của URL cục bộ (`/...`, không `//...`), không tạo open redirect.

## Thành phần

* `controllers/main.py` — alias route, redirect cũ → mới, rebrand header
  `Location` cục bộ, logout về `/dang-nhap`, manifest PWA (`id` giữ `/odoo`,
  `scope`/`start_url` `/app`), header `Service-Worker-Allowed: /`.
* `static/src/router_patch.js` — router đọc/ghi `/app` (refresh, deep link,
  Back/Forward, mở tab mới, link trong app). Không iframe, không
  MutationObserver, không monkeypatch `fetch`/`history`/`location`.
* `static/src/title_patch.js` — tiêu đề tab `"<trang> | TANPHAT ONE"`.
* `static/src/webclient_patch.js` — đăng ký service worker scope `/app`, gỡ
  đúng registration cũ scope `/odoo` của chính origin (không đụng worker khác,
  không xoá storage).
* `static/src/dialog_patch.js`, `branding.xml`, `links_patch.js` — tiêu đề
  dialog/lỗi, hộp phiên hết hạn, href menu/many2one, ẩn mục thuê bao nhà cung
  cấp với người không phải quản trị hệ thống.
* `views/branding_templates.xml` — tiêu đề SSR, credit "Phát triển bởi TADIC",
  metadata chia sẻ link, trang ngoại tuyến, tiêu đề báo cáo/Discuss công khai.

## Giữ nguyên có chủ đích

Thông báo giấy phép/bản quyền nền tảng, định danh kỹ thuật (`/web/...`, model,
module, header), khoá localStorage của PWA, mục Trợ giúp (`support_url`). Danh
sách đầy đủ: `docs/ui/BRAND_WHITELABEL_002_INVENTORY.md`.

## Kiểm thử

```bash
.venv/Scripts/python.exe odoo-bin -c .local/test/odoo.conf -d <db_test> -u tp_branding --test-tags /tp_branding,/tp_web_login,/tp_web_home --stop-after-init --no-http
```

## Gỡ / rollback

Gỡ module (`button_immediate_uninstall`) hoặc khôi phục bản sao lưu theo
`ops/runbooks/BRAND_WHITELABEL_002_DEPLOY_AND_ROLLBACK.md`. Đường dẫn `/odoo`
và `/web/login` hoạt động lại ngay vì lõi không bị sửa.
