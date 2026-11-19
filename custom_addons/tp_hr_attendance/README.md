# TANPHAT ONE — Chấm công (`tp_hr_attendance`)

Version `20.0.3.5.0` · ENTI-ATTENDANCE-002 (`CHG-20261119-029`): ENTI là nguồn công tự động duy nhất, đã ngừng nhập
tệp Excel; kế thừa HR-ATTENDANCE-MATRIX-003 (DEC-058) và HR-ATTENDANCE-SIMPLE-002 (DEC-055/056).
Hướng dẫn Matrix & Đối chiếu: [HR_ATTENDANCE_MATRIX_003_USER_GUIDE.md](../../docs/demo/HR_ATTENDANCE_MATRIX_003_USER_GUIDE.md) ·
nghiệm thu Matrix: [HR_ATTENDANCE_MATRIX_003_ACCEPTANCE.md](../../docs/demo/HR_ATTENDANCE_MATRIX_003_ACCEPTANCE.md) ·
hướng dẫn 002: [HR_ATTENDANCE_SIMPLE_002_USER_GUIDE.md](../../docs/demo/HR_ATTENDANCE_SIMPLE_002_USER_GUIDE.md) ·
policy: [HR_ATTENDANCE_001_POLICY.md](../../docs/security/HR_ATTENDANCE_001_POLICY.md) (§10).
Lịch sử HR-ATTENDANCE-001 (S1–S4, `20.0.1.2.0`): [acceptance 001](../../docs/demo/HR_ATTENDANCE_001_ACCEPTANCE.md).

Module nhỏ cùng DB, dùng hồ sơ `hr.employee`, tài khoản và phòng ban hiện có. Không cài
`hr_attendance` native (route token, systray check-in, cron vắng mặt/tăng ca — xem policy §6).

## Mô hình

| Model | Vai trò | Ghi |
| --- | --- | --- |
| `tp.hr.attendance.session` | Phiên vào-ra (UTC) kèm `source_batch_ids` / `source_line_ids` | Chỉ server (import/đối chiếu/đính chính) |
| `tp.hr.attendance.day` | Ngày công: giờ vào/ra, tình trạng dữ liệu/kỳ; RPC tổng quan/bảng công | Chỉ server |
| `tp.hr.attendance.batch` / `.line` | Lô nhập Excel cũ (`LÔ-xxxxx`) — **chỉ còn lịch sử**: xem, ma trận, đối chiếu chỉ đọc, xuất lại | Không tạo mới qua RPC/giao diện |
| `tp.hr.attendance.snapshot.person` / `.cell` | Snapshot bất biến nguyên gốc từ Excel (tách `raw_source_code`, `raw_machine_code`, `source_group`, `absent_raw`, 2 dòng Vào/Ra) | Chỉ server; khóa sửa/xóa trực tiếp |
| `tp.hr.attendance.resolution` | Nhật ký quyết định đối chiếu A/B (`keep_current`/`use_a`/`use_b`/`defer`, snapshot trước/sau, version, lý do) | Chỉ server; khóa sửa/xóa |
| `tp.hr.attendance.late` | **Tổng đi muộn của máy** (Lần/Phút) theo nhân viên + kỳ nguồn + lô (`superseded` giữ lịch sử khi thay nguồn) | Chỉ server; một bản `applied` mỗi người/kỳ |
| `tp.hr.attendance.source` / `.source.code` / `.event` | Nền nguồn máy: nguồn, mã trên máy theo namespace, sự kiện thô bất biến | Chỉ server |
| `tp.hr.attendance.enti.*` (config / mapping / day / log) | Kết nối ENTI, ghép nhân viên ENTI ↔ hồ sơ, ngày công ENTI đã chuẩn hóa, nhật ký đồng bộ | Cron/server; cấu hình: HR manager |
| `tp.hr.attendance.code` | Mã máy Excel (cột ID) → hồ sơ | HR manager |
| `tp.hr.attendance.rule` / `.assignment` / `.period` / `.correction` / `.log` | Quy tắc công, phân công, kỳ chốt, phiếu điều chỉnh, nhật ký (giữ từ 001) | Như 001 |

Giờ tham chiếu `08:30–17:00` (`ir.config_parameter` `tp_hr_attendance.reference_hours`) **chỉ để
hiển thị**; số phút đi muộn lấy nguyên từ ENTI, module không tự tính đi muộn từ giờ vào.
Thứ tự ưu tiên khi ghi ngày công: điều chỉnh đã duyệt > ENTI > Excel cũ; kỳ đã chốt không bị ghi đè;
lỗi đồng bộ không xóa dữ liệu công đã có.

## Excel máy chấm công — đã ngừng nhập (lịch sử)

Từ ENTI-ATTENDANCE-002 dữ liệu công lấy tự động từ ENTI; **không còn nhập tệp Excel**. Đã gỡ nút/menu
nhập, kéo-thả, hộp thoại tải tệp, nút Nhập dữ liệu trên lô và các nút áp dụng/quyết định ở màn đối chiếu.
Mọi đường ghi công khai đều bị chặn ở server với thông báo *Đã ngừng nhập tệp Excel chấm công…*:
`tp.hr.attendance.batch.create` (ngoài ngữ cảnh nội bộ), `action_preview`, `action_apply`,
`tp_upload_preview`, `tp_upload_apply`, `tp_upload_files`, `tp_apply_compare_valid`, `tp_resolve_compare`,
`tp_resolve_compare_batch`. Logic cũ giữ ở hàm riêng `_tp_*` (không gọi được qua RPC) cho test và dữ liệu
lịch sử.

Giữ nguyên: bảng, lô, dòng staging, snapshot, tổng đi muộn theo kỳ nguồn, nhật ký quyết định, điều chỉnh
đã duyệt và kỳ chốt; `openpyxl` vẫn dùng cho xuất Excel. Quản trị chấm công → **Lịch sử nhập Excel**
(`/odoo/nhap-cong`) xem lô cũ, mở ma trận/đối chiếu **chỉ đọc**, xuất lại; nút *Bỏ qua nguồn chưa áp
dụng* chỉ hủy lô xem trước cũ. Quyền xem lịch sử không đổi (`can(import)`).

## Tổng quan chấm công (`/odoo/cham-cong`)

Thứ tự: tiêu đề + trạng thái *Tự động đồng bộ* (giờ đồng bộ thành công thật) → bộ lọc (Ngày/Tuần/Tháng,
phòng ban, tìm) → 6 KPI (Tổng nhân viên · Có giờ vào · Có giờ ra · Thiếu giờ/cần kiểm tra · Đi muộn: số
người + tổng phút · Vắng) → biểu đồ chính (2/3) + **10 nhân viên có giờ vào/ra gần nhất** (1/3) → xu hướng
→ bảng cần kiểm tra. Biểu đồ Chart.js nạp lười, bấm lát donut để lọc, tôn trọng giảm chuyển động; mobile
một cột. Phân biệt *Chưa có dữ liệu* / *Thiếu giờ* / *Chưa chấm công* / *Nghỉ đã xác nhận* / *Vắng theo
lịch*. Vắng không tính Chủ nhật, ngày tương lai, ngoài thời gian làm việc, nghỉ đã duyệt; chỉ một lần chấm
không phải vắng. Màn hình tự làm mới qua bus `tp_hr_attendance/updated` khi đồng bộ có thay đổi (bộ lọc giữ
nguyên). RPC `tp.hr.attendance.day.tp_overview`.

## Bảng chấm công (`/odoo/bang-cong`)

- **Ngày**: Nhân viên (tên + mã), Phòng ban, Thứ/ngày, Giờ vào, Giờ ra; thiếu giờ hiện `—`.
- **Tuần / Tháng / Khoảng ngày**: mỗi người một dòng với Số lần đi muộn, Tổng phút muộn (ENTI; hoặc tổng
  Excel cũ **phủ đúng kỳ**, nhãn *Theo Excel máy · kỳ …*). Bảng luôn dùng dữ liệu công chuẩn, không còn bảng theo file. Ngày lẻ hoặc một phần kỳ → *Số đi muộn có ở tổng
  kỳ 09–15/11*; tháng không có tổng đúng kỳ → *Chưa có tổng đi muộn đúng kỳ …* + danh sách kỳ nguồn.
- Bấm người → chi tiết kỳ, 2 chỉ số muộn và bảng Thứ/ngày – Giờ vào – Giờ ra. Lọc phòng/tìm, pager
  10/20/50/100, xuất Excel theo mẫu *Bảng chấm công* (2 dòng Vào/Ra mỗi người, cột ngày thật của kỳ, tổng
  đi muộn/vắng, sheet *Chi tiết*; giờ là kiểu thời gian thật; chặn công thức).

RPC `tp_sheet / tp_person / tp_export_sheet`; **Công của tôi** (`/odoo/cong-cua-toi`) dùng `tp_mine /
tp_export_mine`, nhân viên lấy từ session.

## Nguồn dữ liệu & ENTI (`/odoo/nguon-cham-cong`)

Máy chủ Odoo (không phải trình duyệt) gọi ENTI: cron *Đồng bộ chấm công ENTI tự động* mỗi 1 phút, một
lượt đồng bộ có khóa, đủ phân trang, làm mới token, thử lại khi mạng/timeout/429/5xx; chỉ phát bus khi dữ
liệu thật sự đổi. Không trả `raw_json`, token hay cookie cho giao diện. Trang Nguồn dữ liệu hiện tình
trạng kết nối, lần đồng bộ thành công cuối, dữ liệu đến ngày, số người đã/ chưa ghép, **danh sách nhân
viên ENTI chưa ghép kèm lý do**, nút Đồng bộ ngay (HR/admin), và lịch sử Excel cũ. Ghép nhân viên chỉ khi
có căn cứ (mã, họ tên khớp đúng một hồ sơ, hoặc nhân sự xác nhận); không tự ghép theo tên gần giống.
Độ trễ chỉ đo được ENTI → Odoo → màn hình; độ trễ máy chấm công → ENTI do ENTI quyết định.

`tp.hr.attendance.source.tp_ingest(events, watermark)` vẫn là điểm vào chung cho adapter máy khác (gọi từ
code server).

## Menu

- Chấm công: Tổng quan chấm công · Bảng chấm công · Công của tôi.
- Quản trị chấm công (theo capability): Nguồn dữ liệu · Đối chiếu nhân viên ENTI · Cấu hình kết nối ENTI ·
  Nhật ký đồng bộ ENTI · Xử lý điều chỉnh · Chốt kỳ · Lịch sử nhập Excel.
- Cấu hình HR: Quy tắc công · Mã máy chấm công · Phân công xử lý công · Nhật ký chấm công.

## Kiểm thử

Test thuần (không ORM): `test_logic`, `test_parser`, `test_parser_late`, `test_matrix_pure`. Test ORM:
`test_upload`, `test_access`, `test_correction`, `test_import`, `test_directory_privacy`, `test_matrix_compare` — chỉ chạy trên DB
test riêng, không chạy trên DB đang dùng:

```bash
.venv/Scripts/python.exe odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -i tp_hr_attendance --test-tags /tp_hr_attendance --stop-after-init --no-http
```

Chỉ dùng workbook và hồ sơ tổng hợp (synthetic); không đưa tên, giờ công hay tệp thật vào Git.
