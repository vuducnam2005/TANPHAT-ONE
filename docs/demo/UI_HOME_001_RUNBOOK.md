# UI-HOME-001 — Trang chủ TANPHAT ONE (runbook)

Trạng thái: `IMPLEMENTED_PENDING_AUDIT` (CHG-20261102-006). Addon: [`custom_addons/tp_web_home/`](../../custom_addons/tp_web_home/README.md). Prompt: [CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md](../prompts/CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md).

## 1. Mở Trang chủ

| Môi trường | URL | Ghi chú |
| --- | --- | --- |
| Dev | `http://127.0.0.1:18069/odoo` → tự mở `/odoo/tp-home` | Chỉ localhost; DB `tp_tanphat_dev` |
| Dev (trực tiếp) | `http://127.0.0.1:18069/odoo/tp-home` | Deep link khác (`/odoo/contacts`, `/odoo/action-…`) giữ nguyên |

Đăng nhập bằng tài khoản dev có sẵn (`admin`, `planner.dev`). Mật khẩu nằm trong `.local/dev-secrets.json` (ngoài Git, khóa `admin`/`planner`); không chép mật khẩu vào chat, log hoặc tài liệu.

## 2. Dùng

- **Ô ứng dụng:** chỉ các app mà menu Odoo của chính user trả về (đã lọc theo nhóm quyền ở server). `tp_core.menu_platform` được tách thành TP Projects và Danh mục công việc; Trang chủ không tự hiện thành ô. Ứng dụng chưa có trong bảng nhãn giữ tên/biểu tượng gốc của Odoo hoặc chữ viết tắt.
- **Mở:** bấm ô → `menu.selectMenu` như menu ứng dụng gốc. Ctrl/Cmd/Shift/chuột giữa → trình duyệt mở URL `/odoo/…` ở tab mới.
- **Tìm:** gõ có dấu, không dấu hoặc tên tiếng Anh (`du an`, `khách hàng`, `contacts`, `invoice`…). Enter mở kết quả đầu; Escape hoặc nút × xóa từ khóa; không có kết quả → “Không tìm thấy ứng dụng phù hợp”. Tìm không bao giờ hiện app user không được cấp.
- **Nút Trang chủ** (biểu tượng nhà trên thanh điều hướng): về Trang chủ; nếu form đang sửa chưa hợp lệ, Odoo giữ form và báo trường bắt buộc như mọi lần chuyển menu.
- **Home Action riêng của user** (`Preferences → Home Action`, `res.users.action_id`) vẫn được ưu tiên khi mở `/odoo`; addon không ghi trường này.

## 3. Cài / nâng cấp (chỉ `tp_web_home`)

Trước khi cài lên DB có dữ liệu: snapshot DB + filestore + cấu hình ngoài Git (mẫu: `.local/home001/dev-snapshot/tools/backup.py`, kiểm bằng `verify_backup.py`).

```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local/odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -i tp_web_home --stop-after-init --no-http
.\.venv\Scripts\python.exe odoo-bin -c .local/odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -u tp_web_home --stop-after-init --no-http
```

- Chạy từ PowerShell (Git Bash đổi `/tp_web_home` trong `--test-tags` thành đường dẫn Windows).
- Server dev đang chạy không cần khởi động lại: Odoo báo đổi registry và lần request kế tiếp nạp lại menu/asset. Nếu trình duyệt còn bundle cũ, tải lại trang.
- Không dùng `-u all`, không cài `web_responsive`/theme, không chạy `dev.py setup`/seed để cài addon này.
- `tp_web_home` **chưa** nằm trong `MODULES` của `scripts/dev.py`: một DB dựng mới bằng `dev.py setup` sẽ không có Trang chủ cho tới khi có quyết định thêm vào.

## 4. Gỡ / rollback

1. **Gỡ addon** (đủ cho hầu hết trường hợp): Apps → “TANPHAT ONE – Trang chủ” → Uninstall, hoặc trong `odoo-bin shell`:
   `env['ir.module.module'].search([('name', '=', 'tp_web_home')]).button_immediate_uninstall(); env.cr.commit()`
   Kết quả đã kiểm trên DB test: 0 `ir.model.data` của module, 0 client action `tp_web_home.home`, 0 root menu của addon; `/odoo` quay về app gốc đầu tiên (Discuss); Home Action riêng của user giữ nguyên.
2. **Khôi phục toàn bộ dev** (chỉ khi gỡ không đủ, cần chủ runtime đồng ý vì phải dừng dev Odoo): restore `.local/home001/dev-snapshot/dumps/tp_tanphat_dev.dump` (`pg_restore`) và filestore `.local/home001/dev-snapshot/filestore/tp_tanphat_dev/`; snapshot lúc 2026-11-02T04:07:49Z, 233 checksum, `verify_backup.py` đạt; chưa diễn tập restore snapshot này.

## 5. Bằng chứng kiểm chứng (02/11/2026)

Môi trường cô lập: DB `tp_tanphat_home001_test`, data dir `.local/home001/odoo-data`, cổng 18129 (đã dừng), user giả `home.employee`/`home.manager`/`home.actionuser`, công ty giả “Công ty thử nghiệm B (HOME001)”, secret sinh ngẫu nhiên trong `.local/home001/secrets.json`. Log/ảnh trong `.local/home001/` (ngoài Git).

| Kiểm | Kết quả |
| --- | --- |
| Odoo server tests `--test-tags /tp_web_home` | `0 failed, 0 error(s) of 10 tests` (record/menu/group, employee/manager/portal, không ghi `action_id`, giữ Home Action, HTTP public/portal/internal, asset bundle) |
| HOOT `web.assets_unit_tests`, filter `tp_web_home` | 15/15 |
| Playwright E2E cô lập | 66/66: `/odoo`→Home, quyền theo user, ô→app, nút Home/active, back/forward/reload, deep link, Ctrl-click, tìm có/không dấu/alias, Escape/Enter/Tab focus, form chưa hợp lệ chặn rời, đổi công ty, logout/login cùng trình duyệt không lộ menu cũ, Home Action riêng, 1440/1366/1024/768/375, zoom 125/150% (kể cả 375@150%), reduced motion, hover −3px, không lỗi console |
| Gỡ/cài lại trên DB test | Gỡ sạch như mục 4; cài lại exit 0 |
| Ruff `custom_addons/tp_web_home` | All checks passed |
| Cài dev | `-i tp_web_home` exit 0, 88 module; chỉ đổi bảng menu/action/module/attachment/signaling; bảng `tp_*`, user, nhóm, ACL, rule, project, partner không đổi; 0 user có `action_id` = Trang chủ |
| Live dev 18069 | 26/26: admin và `planner.dev` ở 1440/375 mở Home, planner không có CRM/Invoicing, ô→app, nút Home, tìm “du an”, không cuộn ngang, không lỗi console |

Demo `tp_tanphat_demo_ui001` (18109) dùng DB riêng, không cài/không khởi động lại. Dev Odoo 18069 không bị dừng.

## 6. Giới hạn còn lại

- Chưa audit độc lập/nghiệm thu nghiệp vụ; trạng thái là `IMPLEMENTED_PENDING_AUDIT`.
- TP Contracts/Bid/Request/Survey/Design chưa có menu native nên không có ô; không tạo ô giả.
- Ô TP Projects/Danh mục công việc dùng chữ viết tắt (TP/DM) vì chưa có icon riêng.
- Nhãn tiếng Việt chỉ áp dụng trên Trang chủ; menu Odoo gốc vẫn theo ngôn ngữ user (VI-001 riêng).
- Lỗi quyền To-do (TODO-001) không thuộc batch này; ô “Việc cá nhân” chỉ hiện khi menu Odoo cho phép.
