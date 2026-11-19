# HR-ATTENDANCE-MINE-UI-001 — Nghiệm thu kỹ thuật giao diện “Công của tôi”

- Mã thay đổi: `CHG-20261119-003` (local verified) / addon `tp_hr_attendance` `20.0.3.1.0` (không thay schema/menu/ACL, không cần `-u`).
- Phạm vi: Thiết kế lại giao diện **Công của tôi** ở cả menu độc lập (`/app/cong-cua-toi`) và tab nhúng trong **Thông tin cá nhân** (`/app/my-profile`), bổ sung lọc/phân trang/xuất Excel theo bộ lọc ở backend `tp_mine` và `tp_export_mine`.

## Kết quả kiểm tra kỹ thuật

| Tiêu chí | Bằng chứng | Kết quả |
| --- | --- | --- |
| Độc lập và bản nhúng Hồ sơ cá nhân | `test_hr_attendance_mine_ui.cjs`: bản độc lập hiển thị tên/mã/phòng đúng 1 lần; bản nhúng ẩn `h1` và bỏ lặp thông tin nhân viên | PASS |
| Kỳ Tuần / Tháng / Kỳ theo file | Popover phụ `Kỳ theo file`, nút kỳ trước/sau/Hôm nay, nhãn khoảng ngày rõ; kiểm chuyển Tháng ↔ Kỳ `09–15/11/2026` | PASS |
| Tóm tắt 4 chỉ số & đi muộn kỳ nguồn Excel | Nhóm 1 (Ngày có ghi nhận vào/ra, Ngày cần kiểm tra) tách biệt nhóm 2 (Kỳ nguồn Excel: `3 lần · 356 phút` ở `09–15/11`, `—` ở tháng lệch kỳ, không quy đổi 0) | PASS |
| Bảng công 4 cột + màu sắc + ô thiếu giờ | `Thứ / Ngày`, `Giờ vào`, `Giờ ra`, `Tình trạng`; giờ xanh `tabular-nums`, ô thiếu hiển thị `— Thiếu giờ ra/vào`, hôm nay nhấn xanh + nhãn `Hôm nay`, cuối tuần nền dịu, ngày tương lai xám nhẹ | PASS |
| Chi tiết mở rộng theo dữ liệu thực | Chỉ dòng có dữ liệu backend mới có nút mở rộng (`sessions`, `requests`, nguồn, trạng thái kỳ, nút đề nghị điều chỉnh ngày); dòng tương lai/trống không có nút giả | PASS |
| Bộ lọc server, phân trang & xuất Excel | Pending vs Áp dụng, chip xóa điều kiện, Xóa bộ lọc, mặc định 50 dòng (`10/20/50/100`); `tp_export_mine` xuất toàn bộ dòng khớp bộ lọc (không chỉ trang đang xem), giữ sheet Tổng đi muộn đúng kỳ nguồn | PASS |
| Quyền cá nhân & bảo mật | Read-only ORM `uid=41/34/2`: bỏ qua `employee_id` giả mạo, từ chối bộ lọc không hợp lệ (`UserError`), không mở rộng quyền nguồn, không dùng cache chung cho dữ liệu công | PASS |
| Responsive, cuộn & hiệu ứng | Desktop `1440×900` & mobile `390×844`: `scrollWidth <= innerWidth`, không vùng cuộn dọc lồng nhau (`overflow-y: clip`), sticky header sát đỉnh, navbar/sidebar cố định, không lộ trắng, mobile panel lọc đóng bằng `Esc`, `prefers-reduced-motion` trả `transitionDuration: 0s`, 0 animation liên tục | PASS |
| Không làm hỏng màn khác | `PersonDetail` giữ nguyên; `test_hr_attendance_scroll.cjs` 12/12 + `test_hr_attendance_latest_ui.cjs` 2/2 PASS; 0 lỗi JS/console | PASS |
| Kiểm tra tĩnh & pure logic | AST, XML, libsass SCSS, Ruff, Node JS syntax + `mineStatusInfo`, pure Python `mine_row_status`/`filter_mine_rows`/`summarize_mine_rows` | PASS |

## Ảnh trước / sau (cùng kỳ & kích thước màn hình)

- Lưu tại `.local/mine-ui001/before/` và `.local/mine-ui001/after/`:
  - Desktop `1440×900` Tháng 11/2026: `before-1440-month.png` vs `after-1440-month.png`, `after-1440-today-future.png`, `after-1440-filtered.png`
  - Desktop `1440×900` Kỳ theo file `09–15/11/2026`: `before-1440-week.png` vs `after-1440-week.png`
  - Desktop `1440×900` Tab nhúng Hồ sơ cá nhân: `before-1440-embedded.png` vs `after-1440-embedded.png`
  - Mobile `390×844`: `before-390-month.png` vs `after-390-month.png`, `after-390-table.png`, `after-390-embedded.png`

## Giới hạn còn lại

- Trình duyệt trên local `18069` dùng session hiện có kết hợp payload ORM chỉ đọc thật của nhân viên `uid=41` (do tài khoản `admin` local chưa gắn hồ sơ nhân viên, không reset mật khẩu hay tạo user giả).
- Chưa chạy kiểm thử trình duyệt có đăng nhập trực tiếp bằng mật khẩu nhân viên trên URL public để tránh thay đổi phiên người đang sử dụng; chưa kiểm trên iOS/Safari thiết bị thật.
- Nghiệm thu hình thức và nghiệp vụ thuộc quyền người dùng sau khi xem trực tiếp trên server.

## Giao bản PC server — CHG-20261119-004

- Commit ứng dụng: `5859a83e2a28f3c201dce2d8e5ea86baacd9bc4a` (addon `tp_hr_attendance` `20.0.3.1.0`, không thay schema/menu, chỉ `docker restart tp-odoo`).
- Backup nguồn trước deploy trên PC server: `/workspace/.local/mine-ui001/source-before-20261119T035343Z`.
- Snapshot DB trước/sau không đổi: `39` nhân sự, `32` tài khoản, `5` lô, `384` phiên, `480` ngày công, group digest `cd4581c4f4c47e2cfab004b6eefb3cdc`.
- Link public thực tế đã kiểm: `https://eight-championships-launches-plaintiff.trycloudflare.com` (`/web/health` và `/dang-nhap` `200`; không hardcode hostname cũ, không restart tunnel).
- Bundle thực phục vụ (khớp 100% giữa nội bộ server và public):
  - CSS: `/web/assets/9b3c839/web.assets_web.min.css` (1631612 bytes, SHA256 `de9f259b9921044534fe20ab08e70788b9cf678b888b28139b36f3188a5f8ebe`)
  - JS: `/web/assets/e42c27e/web.assets_web.min.js` (8474198 bytes, SHA256 `df6d2838e44789c0c1b68e604815b57b55e5f25eb3f31e147a6472950738ddd1`)
- Probe ORM chỉ đọc trên PC server (`uid=51`): `tp_mine` / `tp_export_mine` chống giả mạo `employee_id`, lọc + xuất toàn bộ kết quả lọc + từ chối bộ lọc lỗi đạt PASS.
