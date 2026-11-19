# ENTI-ATTENDANCE-002 — Nghiệm thu kỹ thuật

Change: `CHG-20261119-029` (code) · Quyết định: [DEC-063](../DECISIONS.md) · Module `tp_hr_attendance` `20.0.3.5.0`
· Kế thừa [ENTI-LIVE-001](ENTI_LIVE_001_ACCEPTANCE.md) (`CHG-20261119-025/026`).

Trạng thái: **VERIFIED_RELEASE_READY** trên DB kiểm thử cục bộ `tp_tanphat_test` (cổng 18179). Phần PC server
ghi ở mục 6 sau khi áp. Đây là nghiệm thu kỹ thuật, chưa phải nghiệm thu nghiệp vụ của phòng nhân sự.

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

## 6. PC server

Chưa áp ở commit code này; kết quả triển khai, đồng bộ tự động thật và đối chiếu ghi ở change kế tiếp.
