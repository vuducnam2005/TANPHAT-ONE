# UI-HOME-003 — Acceptance và evidence

Ngày 07/11/2026, Asia/Saigon. CHG-20261107-006. [Thiết kế](../ui/UI_HOME_003_DESIGN.md) ·
[Hướng dẫn](UI_HOME_003_USER_GUIDE.md). Ma trận viết trước code; cột kết quả cập nhật sau khi
chạy. Đây là **tự kiểm kỹ thuật**; audit độc lập, nghiệm thu nghiệp vụ và pilot là bước riêng,
chưa thực hiện.

## Kết quả tổng

| Lớp | Clone 18689 (`tp_tanphat_home003_20261107`) | Dev 18069 (`tp_tanphat_dev`) |
| --- | --- | --- |
| Odoo `/tp_web_home` | 12/12 đạt, 0 lỗi | Không chạy test trên dev (chỉ upgrade module) |
| HOOT `tp_web_home` | 24/24, 143 assertion | — |
| Browser | 229/229 kiểm, 0 lỗi (actor admin, KH-KD, 4 fixture, portal/Home Action) | 152/152 chỉ đọc, 0 lỗi (admin, KH-KD); 38 ảnh |
| Ruff / `node --check` | `scripts/ui_home003.py` + addon: đạt; hai file `.cjs`: đạt | — |
| Bảo toàn | — | 39 bảng nghiệp vụ/user/password/Home Action/groups/grant: 0 dòng đổi; 908 dòng ACL/domain `ir_access` = dump (bỏ write_date/write_uid) và 4 bảng group action/view/field nguyên; 257 attachment ngoài asset = dump theo nội dung; 93 module installed trước = sau, chỉ `tp_web_home` 20.0.1.2.0 → 20.0.1.3.0; payload `load_menus` admin/KH-KD = trước |

Source tested = source applied: `tested-source.json`, `shots/clone-after/result.json`,
`shots/clone-hoot/result.json` cùng 22 hash file với cây `custom_addons/tp_web_home` lúc áp.

## Ma trận

| ID | Kiểm tra | Bằng chứng | Kết quả |
| --- | --- | --- | --- |
| H01 | Nhân viên KH-KD thấy workspace + công cụ cá nhân đúng quyền; không lưới nghiệp vụ, không khu quản trị | Browser: mỗi actor, mục Home dùng lại href baseline, không trùng, không `[data-group=business]`, không chữ "sắp ra mắt"/KPI, workspace có khi và chỉ khi có menu, công cụ cá nhân đúng thứ tự; HOOT catalog | **Đạt** clone 39 kiểm; dev 15 |
| H02 | Mở KH-KD đúng Tổng quan; Back/Home giữ context | Thẻ → Tổng quan (`/odoo/action-510…`), Ctrl-click mở tab mới và giữ Home; Back/Forward/refresh/Home ở H10 | **Đạt** clone 3; dev 3 |
| H03 | Từ KH-KD vào các đích (Cơ hội, Hồ sơ dự án, TP Contracts, Kế hoạch/WBS): action/domain/dataset như baseline | `kd-destinations.json` trước = sau: lá sidebar, nhãn, href, URL, tiêu đề, tổng pager, số dòng; không có lá HR/Hóa đơn | **Đạt** clone 3; dev 3 |
| H04 | User không có menu KH-KD không thấy/mở qua Home/search; empty state đúng | Nhân viên, HR/Hóa đơn: không thẻ KH-KD, `khkd` rỗng, Enter đứng yên trên Home | **Đạt** clone (8 kiểm H01/H04 + 2) |
| H05 | Quản lý kinh doanh thiếu `base.group_system` không thấy quản trị; quản trị mở đúng Tất cả ứng dụng/Cài đặt/Quản lý ứng dụng; app lạ/icon lỗi vẫn có đường vào | Fixture salesmgr (Access Rights): không khu quản trị, `cai dat` rỗng; admin: panel đóng mặc định, focus vào ô tìm, liệt kê đúng inventory trước, motion 120–200 ms, Escape hai nấc, nút Đóng, Enter trong panel mở Hóa đơn, Cài đặt/Quản lý ứng dụng mở đúng; root lạ icon lỗi ở 360 px | **Đạt** clone 44; dev 18 (không bấm Cài đặt/Quản lý ứng dụng trên dev) |
| H06 | User thường có HR/Hóa đơn vẫn mở qua switcher native desktop/mobile; payload menu không đổi | Payload `load_menus` sau = trước theo nội dung; desktop `.o_navbar_apps_menu` liệt kê đủ app theo thứ tự, mở Hóa đơn và Nhân sự; mobile 390 ☰ → Tất cả ứng dụng → app | **Đạt** clone 18; dev 10 (CRM, Khách hàng; mobile ☰ → CRM) |
| H07 | Search có/không dấu, alias, IME, Enter/Escape/clear, focus; Enter không kích hoạt mục quản trị ẩn | HOOT + browser: bảng từ khóa, `du an` không khớp "ứng dụng", Tab tới thẻ KH-KD, clear trả focus, IME bỏ qua, non-system Enter `cai dat` không điều hướng; mỗi công cụ cá nhân mở được, không rò style | **Đạt** clone 28; dev 25 |
| H08 | Menu cache actor trước, fail/retry, đổi user/company, late response/unmount | HOOT deferred/late; browser 503 → lỗi khác empty → Thử lại; tải trễ khi đã rời Home không đưa Home trở lại; logout → nhân viên không chớp KH-KD/quản trị (MutationObserver); đổi công ty tải lại đúng menu | **Đạt** clone 6 (chỉ clone, vì cần actor giả/route lỗi) |
| H09 | 360/390/768/1024/1280/1440/1920, zoom 125/150, cuộn, phím/chạm, reduced-motion, không tràn/rò style | Hình học từng bề rộng cho admin (panel mở) và KH-KD: không tràn ngang, vùng chạm ≥44 px, không autofocus, thẻ KH-KD trong viewport đầu, cuộn dọc; motion 120–200 ms, reduced-motion tắt; zoom 125/150 | **Đạt** clone 73; dev 72 |
| H10 | Dirty form, deep link/refresh/Back/Home Action, login/logout; dữ liệu/user/quyền/menu ngoài delta giữ | `/odoo` mở Home, Back/refresh/nút Home, form chưa hợp lệ giữ guard native, Home Action riêng (Discuss) giữ; preserve-before/after, ACL nội dung, payload menu | **Đạt** clone 7; dev 4 (dirty form/logout/Home Action riêng chỉ clone) |

## Áp dev và rollback

Thứ tự đã chạy: snapshot + restore rehearsal clone (`snapshot-20261107T062544Z`) → test clone →
`dev before` chỉ đọc → `preserve-before` → backup sát áp → `apply` → `dev verify` chỉ đọc →
`preserve-after`.

- Backup `.local/ui-home003/backup-pre-apply-20261107T065916Z`: verified, 112 file checksum, 576
  bảng, 269 attachment.
- `apply` qua cổng hash (tested-source, clone-after, clone-hoot, source chính chưa đổi từ
  snapshot), copy source đã test, upgrade **chỉ** `tp_web_home`: log
  `dev-apply-20261107T065941Z.log`, rc 0, 0 ERROR/CRITICAL, `changed_tables {}`; 1 WARNING có sẵn
  (`markdown2` chưa cài). Dev 18069 chạy lại, HTTP 200.
- PID: PostgreSQL 55432 = 4228; clone 18169 = 27568, 18269 = 2232, 18489 = 24164, 18589 = 23244
  không đổi. Dev đổi PID do restart có chủ đích (listener 18069 = 20044). Clone owned 18689 vẫn
  chạy để đối chiếu.
- Không ghi thử/seed/cleanup dev; `dev verify` chỉ đọc (điều hướng, tìm, mở panel, chuyển ứng
  dụng), không lưu form.

**Rollback delta** (chỉ module, giữ dữ liệu):

```powershell
.\.venv\Scripts\python.exe scripts\ui_home003.py rollback
```

Lệnh khôi phục `custom_addons/tp_web_home` từ `maintained-source.zip` của snapshot (UI-HOME-002,
20.0.1.2.0; bỏ `apps.svg`), dừng tiến trình Odoo dev (không dừng PostgreSQL), upgrade chỉ
`tp_web_home`, so rowset rồi khởi động lại. Sau đó Ctrl+F5. Nếu cần trả cả DB/filestore về trước
áp, dùng backup `backup-pre-apply-20261107T065916Z` theo runbook restore; bước này ghi đè dữ liệu
phát sinh sau áp nên chỉ làm khi người dùng yêu cầu. Chưa chủ động diễn tập rollback dev lần này.

## Giới hạn

- Chromium + mô phỏng mobile/touch; chưa Safari/WebKit hay thiết bị thật.
- Fixture fail/retry, đổi user/công ty, dirty form, Home Action riêng, root lạ/icon lỗi, bấm Cài
  đặt/Quản lý ứng dụng chỉ chạy trên clone (cần actor giả/route lỗi; dev chỉ đọc).
- Ẩn khỏi Home là trình bày, không phải thu quyền: Settings vẫn ở switcher cho người có
  `base.group_erp_manager`, đúng như server cấp.
- Kết quả trên là tự kiểm; audit độc lập, nghiệm thu nghiệp vụ và pilot chưa làm.

Evidence private trong `.local/ui-home003/` (ảnh, JSON, log, backup); không ghi credential hay
payload dữ liệu vào Git.
