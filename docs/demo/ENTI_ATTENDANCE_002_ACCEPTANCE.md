# ENTI-ATTENDANCE-002 — Nghiệm thu kỹ thuật

Change: `CHG-20261119-029` (code) · `CHG-20261119-030` (áp PC server) · Quyết định: [DEC-063](../DECISIONS.md)
· Module `tp_hr_attendance` `20.0.3.5.0` · Kế thừa [ENTI-LIVE-001](ENTI_LIVE_001_ACCEPTANCE.md) (`CHG-20261119-025/026`).

Trạng thái: **MAIN_AND_PC_SERVER_APPLIED**. Kiểm kỹ thuật trên DB kiểm thử cục bộ `tp_tanphat_test` (cổng 18179, mục 2–4)
và áp PC server ngày 20/11/2026 (mục 6). Đây là nghiệm thu kỹ thuật, chưa phải nghiệm thu nghiệp vụ của phòng nhân sự.

## 1. Phạm vi đã làm

| Hạng mục | Kết quả |
| --- | --- |
| Kết nối ENTI | Máy chủ Odoo gọi ENTI (không gọi từ trình duyệt). Cron canonical `ir_cron_enti_attendance_sync` mỗi 1 phút; trong 05:00–22:00 giờ VN một lượt cron đọc **hôm nay** mỗi 15 giây (tối thiểu 10 giây) trong ~50 giây rồi tự hẹn lượt sau; cửa sổ 5 ngày gần nhất đọc lại 5 phút/lần (giờ ra hôm qua, ENTI sửa muộn). Lỗi lùi 30/60/120 giây. Một lượt đồng bộ có khóa advisory, đủ phân trang, làm mới token, thử lại có giới hạn khi mạng/timeout/429/5xx. |
| Cập nhật không tải lại | Bus `tp_hr_attendance/updated` chỉ phát khi có ngày công thật sự đổi; Tổng quan, Bảng công, Công của tôi, Nguồn dữ liệu tự làm mới, giữ bộ lọc. Lượt đọc không đổi gì thì không ghi DB, không đánh thức màn hình. |
| An toàn dữ liệu | Thứ tự ưu tiên: điều chỉnh đã duyệt > ENTI > Excel cũ; kỳ đã chốt không bị ghi đè; lỗi hoặc ENTI trả trống **không xóa** giờ đã có (ghi “giữ giờ cũ, cần kiểm tra”). Không trả `raw_json`, token, cookie cho giao diện. |
| Ghép nhân viên | Chỉ ghép khi có căn cứ: mã/họ tên khớp đúng một hồ sơ, hoặc nhân sự xác nhận kèm lý do; mỗi khóa ENTI một nhân viên. Trang Nguồn dữ liệu liệt kê người ENTI **chưa ghép kèm lý do**. Không tạo nhân viên, không ghép theo tên gần giống. |
| Tổng quan chấm công | Tiêu đề + *Tự động đồng bộ* (giờ thành công thật) → bộ lọc → 6 KPI → biểu đồ chính 2/3 + **10 nhân viên có giờ vào/ra gần nhất** 1/3 → xu hướng → bảng cần kiểm tra. Chart.js nạp lười, màu theo chuẩn, bấm lát donut để lọc, cao 300–360px, chuyển động 180–300ms, tôn trọng giảm chuyển động; mobile một cột. |
| Trạng thái tách bạch | *Chưa có dữ liệu* / *Thiếu giờ* / *Chưa chấm công* / *Nghỉ đã xác nhận* / *Vắng theo lịch*. Vắng không tính Chủ nhật, ngày tương lai, ngoài thời gian làm việc, nghỉ đã duyệt; một lần chấm không phải vắng. Giờ tham chiếu 08:30–17:00 chỉ để hiển thị; phút đi muộn lấy từ ENTI. |
| Xuất Excel | Theo mẫu *Bảng chấm công*: 2 dòng Vào/Ra mỗi người, cột ngày thật của kỳ, tổng đi muộn/vắng, sheet *Chi tiết*, giờ là kiểu thời gian, chặn công thức; tuần/nhiều tuần/tháng. |
| Ngừng nhập tệp Excel | Gỡ nút/menu/kéo-thả/hộp thoại tải tệp, nút Nhập dữ liệu và nút áp dụng/quyết định ở đối chiếu. RPC công khai (`batch.create` ngoài ngữ cảnh nội bộ, `action_preview`, `action_apply`, `tp_upload_preview/apply/files`, `tp_apply_compare_valid`, `tp_resolve_compare(_batch)`) trả *Đã ngừng nhập tệp Excel chấm công…*. Giữ bảng, lô, snapshot, tổng muộn, nhật ký quyết định, điều chỉnh, kỳ chốt; lịch sử vẫn xem/đối chiếu chỉ đọc/xuất lại. Không drop bảng, giữ `openpyxl`. Cờ `can_import` còn dùng trên Bảng công nghĩa là “được mở trang Nguồn dữ liệu/lịch sử”. |

## 2. Kiểm thử tự động (DB `tp_tanphat_test`)

- `odoo-bin -u tp_hr_attendance --test-tags /tp_hr_attendance`: **95 test, 0 failed, 1 error**. Lỗi duy nhất là
  `test_access.test_assignments_drive_officer_group_and_capabilities`: `attendance_config._tp_sync_officers` ghi thành viên
  nhóm cán bộ chấm công và bị guard `tp_admin_delegation/models/guards.py:418` chặn (“Sửa cấu trúc hoặc thành viên nhóm
  quyền chỉ dành cho Quản trị gốc.”). Lỗi liên module có sẵn, không do thay đổi này; không sửa `tp_admin_delegation`,
  không che test — tách thành việc riêng.
- Test mới `tests/test_enti_attendance_002.py`: client ENTI giả (token lồng, làm mới trước hạn, 401 làm mới một lần, 429/5xx
  chờ có giới hạn, lỗi mạng, phân trang + từ chối bảng thiếu trang); đồng bộ giả (ghép tên đúng, lượt không đổi không ghi/không
  phát bus, lỗi/trả trống không xóa công, kỳ chốt giữ nguyên, ghép cần căn cứ); RPC nhập Excel bị chặn và lịch sử vẫn đọc/xuất
  được; bố cục xuất Excel, sheet Chi tiết, ghi chú người, 10 người gần nhất (khác nhau, mới nhất trước, tối đa 10).
- Các test cũ đã lỗi thời từ trước (payload `file_name`/`data`, `created_ids`, ghi lô qua `internal`, nguồn phiên `import`)
  được sửa theo hành vi hiện tại, không nới điều kiện kiểm.
- `ruff check` sạch cho thư mục test và script mới.

## 3. Kiểm trên trình duyệt (Playwright, cục bộ 18179)

`node scripts/enti_att002_ui.cjs` — **9/9 PASS**: Tổng quan đủ tiêu đề/bộ lọc/6 KPI/biểu đồ/≤10 người gần nhất, biểu tượng
đều có glyph; 1440/768/390/320px không tràn trang, donut nằm trong thẻ; Bảng công, Công của tôi, Nguồn dữ liệu mở không lỗi
ở 1440 và 390; Bảng công và Nguồn dữ liệu không còn ô chọn tệp/nút tải lên, có thông báo đã ngừng nhập, thẻ Excel ghi
*Đã ngừng nhập · Lịch sử*, có danh sách người ENTI chưa ghép. Ảnh ở `.local/enti-att002/ui/` (không commit).

`node scripts/enti_att002_live.cjs` — **PASS**: mở Tổng quan, đẩy một giờ ra mới qua đường áp dụng thật (client ENTI giả, DB
kiểm thử), màn hình hiện người đó đầu danh sách *gần nhất* với giờ ra mới **0,7 giây sau commit**, không tải lại trang,
KPI *Có giờ ra* 4 → 5. Đây là độ trễ ENTI → Odoo → màn hình; khoảng máy chấm công → ENTI nằm ngoài Odoo và **không đo**.

## 4. Đối chiếu file Excel xuất

`odoo-bin shell < scripts/enti_att002_export_check.py` (chỉ đọc, rollback): mở file xuất và so với số backend.

| Kỳ | Người | Ô ngày | Ô có giờ | Lần muộn | Phút muộn | Vắng | Dòng Chi tiết | Sai lệch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tuần 09–15/11 | 57 | 399 | 270 | 42 | 551 | 17 | 399 | 0 |
| 01–19/11 (nhiều tuần) | 57 | 1083 | 726 | 127 | 1567 | 35 | 1083 | 0 |
| Tháng 11 | 57 | 1710 | 757 | 137 | 1681 | 35 | 1140 | 0 |

Dữ liệu kiểm thử cục bộ là dữ liệu dạng ENTI do script tạo trên `tp_tanphat_test`; không ghi gì vào database chính.

## 5. Triển khai và hoàn tác (PC server)

Script [`ops/runbooks/deploy-enti-attendance002.ps1`](../../ops/runbooks/deploy-enti-attendance002.ps1) chạy trên PC sau khi
chép tarball release + manifest (sinh từ commit, chỉ `custom_addons/tp_hr_attendance/`) vào `.local\enti-attendance002`:
kiểm runtime `tp-odoo`, dừng nếu nguồn trên PC lệch baseline, chụp snapshot số liệu nghiệp vụ/quyền (không in bí mật), dừng
Odoo, backup dump (+ `pg_restore -l`), filestore, source module, config, giải nén release, xóa file đã bỏ, kiểm checksum từng
file, upgrade bằng container một lần, luôn khởi động lại Odoo, ghi SHA256 của backup và snapshot sau.

Hoàn tác: dừng `tp-odoo`; khôi phục `source.tar.gz` vào `custom_addons/tp_hr_attendance`; `pg_restore --clean` dump vào
`tp_tanphat_dev` và giải nén `filestore.tar.gz` nếu cần; khởi động lại. Migration `20.0.3.5.0` chỉ đổi priority cron ENTI
5 → 10, không sửa dữ liệu.

## 6. PC server (`CHG-20261119-030`)

Giờ dưới đây là giờ Việt Nam (UTC+7), ngày 20/11/2026.

**Triển khai.** Release từ commit `51e1421b` (51 file, 7 file mới, 2 file bỏ; checksum từng file khớp) chép vào
`.local\enti-attendance002` rồi chạy script ở mục 5. `tp_hr_attendance` 20.0.3.4.1 → 20.0.3.5.0, upgrade exit 0, log upgrade
0 ERROR; Odoo dừng 03:25:23, chạy lại 03:26:37. Backup `C:\TANPHAT-backups\enti-attendance002\enti002-20261120T032523`
(dump + `pg_restore -l`, filestore, source module, config, SHA256).

**Snapshot trước/sau** giống hệt, chỉ đổi phiên bản module và priority cron ENTI 5 → 10: 39 nhân viên, 32 user, nhóm quyền,
roster, 780 ngày công, 787 phiên, 780 ngày ENTI, 39 người ENTI đã ghép, 5 lô Excel cũ, 0 điều chỉnh, 0 kỳ chốt, `base_url`.
Trùng lặp ngày công / phiên / ngày ENTI theo khóa duy nhất: 0 / 0 / 0.

**Truy cập.** Trên PC `/web/health` 200, `/web/login` 302; qua URL công khai health 200 (0,55 giây), login 302. Bundle
`web.assets_web` công khai (JS 7556850, CSS 6f82a6b, sinh lại sau nâng cấp) có kênh bus `tp_hr_attendance/updated`, khối
*10 nhân viên gần nhất*, 6 KPI và thông báo *Đã ngừng nhập tệp Excel*; không còn mã của luồng tải tệp. Không đăng nhập
tài khoản thật trên PC (tránh làm văng phiên người dùng), nên chưa xem giao diện PC bằng mắt.

**Đồng bộ tự động thật** (cron `ir_cron_enti_attendance_sync`, nguồn ENTI id 3, chỉ đọc DB và log):

| Lúc | Lượt | Kết quả |
| --- | --- | --- |
| 03:17–03:25 | Code cũ, 8 lượt | Mỗi phút ghi lại **234 ngày công** dù ENTI không đổi. |
| 03:28:18 | Code mới, cửa sổ 15–20/11 (đăng nhập ENTI, token 900 giây) | Thành công 3,1 giây, `changed 0`, nhật ký `scope=window`, `polls=1`; lần đầu điền `raw_hash` (cột mới) cho 234 dòng ngày ENTI, không ghi ngày công. |
| 03:29:22 → 03:33:23 | Code mới, hôm nay, mỗi phút | 5 lượt thành công liên tiếp, mỗi lượt ~0,25 giây, 0 lỗi; `last_success_at` tiến theo từng lượt (giờ *Tự động đồng bộ* lấy từ đây). |

Trong 6 lượt mới: `write_date` lớn nhất của ngày công đứng yên ở 03:25:07 (lượt cuối của code cũ), ngày ENTI không ghi gì
sau 03:28:18, nhật ký đồng bộ không thêm dòng (lượt không đổi chỉ ghi nhịp tim 30 phút/lần), số ngày công/phiên giữ
780/787, log container 0 ERROR. Lúc kiểm là 03:28–03:34, ngoài khung 05:00–22:00, nên cron đọc mỗi phút; nhịp đọc 15 giây
trong giờ làm **đã kiểm trên DB kiểm thử, chưa quan sát trên PC**.

**Độ trễ.** Đo được phần ENTI → Odoo → màn hình: cục bộ 0,7 giây sau commit. Trên PC, giờ mới có ở ENTI được đọc trong
tối đa ~15 giây (05:00–22:00) hoặc ~60 giây (ngoài khung), cộng ~0,3 giây một lượt đọc hôm nay. Khoảng máy chấm công →
ENTI nằm ngoài Odoo và **không đo**.

**Hoàng Xuân Tiến.** Hồ sơ id 44 (`TP10065`, phòng Thiết kế) đã mang tên đúng *Hoàng Xuân Tiến*; người ENTI `TP032` đã ghép
vào hồ sơ này (trạng thái *đã ghép*, lý do: người dùng xác nhận đổi tên Tuyến → Tiến và cùng một người), có 20 ngày ENTI
→ 20 ngày công. Việc này đã làm trước khi áp bản này; lần này chỉ kiểm, không sửa. Không còn người ENTI chưa ghép.

**Xuất Excel trên dữ liệu thật** (`scripts/enti_att002_export_check.py` chạy trong container, chỉ đọc, rollback):

| Kỳ | Người | Ô ngày | Ô có giờ | Lần muộn | Phút muộn | Vắng | Dòng Chi tiết | Sai lệch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tuần 09–15/11 | 39 | 273 | 329 | 91 | 6612 | 56 | 273 | 0 |
| 01–19/11 (nhiều tuần) | 39 | 741 | 888 | 220 | 13938 | 142 | 739 | 0 |
| Tháng 11 | 39 | 1170 | 888 | 220 | 13938 | 142 | 778 | 0 |

*Ô có giờ* đếm riêng ô Vào và ô Ra. Dòng Chi tiết bỏ ô ngoài thời gian làm việc và ngày tương lai; tháng 11 có thêm
39 dòng của 20/11. KPI Tổng quan cùng phạm vi khớp file.

**Điểm cần phòng nhân sự xem.** Phút muộn lấy nguyên từ ENTI (ca `HC`). Tuần 09–15/11: 71/91 lần muộn bằng đúng số phút sau
08:30; các lần còn lại ENTI trừ 90 phút nghỉ trưa vì lần chấm đầu tiên rơi vào buổi chiều. 23/91 lần muộn từ 2 giờ trở lên,
ví dụ chỉ chấm một lần lúc 18:08 → ENTI tính muộn 488 phút. Odoo hiển thị đúng như ENTI tính; cần nhân sự quyết định các
ngày này là đi muộn, nghỉ nửa buổi hay quên chấm.

**Chưa làm.** Xem giao diện trên PC bằng tài khoản thật; quan sát nhịp 15 giây trong giờ làm trên PC; nghiệm thu nghiệp vụ.
