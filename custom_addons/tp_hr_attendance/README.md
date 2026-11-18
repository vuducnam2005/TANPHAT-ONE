# TANPHAT ONE — Chấm công (`tp_hr_attendance`)

Version `20.0.2.0.0` · HR-ATTENDANCE-SIMPLE-002 (DEC-055/056, `CHG-20261118-019`).
Hướng dẫn: [HR_ATTENDANCE_SIMPLE_002_USER_GUIDE.md](../../docs/demo/HR_ATTENDANCE_SIMPLE_002_USER_GUIDE.md) ·
nghiệm thu: [HR_ATTENDANCE_SIMPLE_002_ACCEPTANCE.md](../../docs/demo/HR_ATTENDANCE_SIMPLE_002_ACCEPTANCE.md) ·
policy: [HR_ATTENDANCE_001_POLICY.md](../../docs/security/HR_ATTENDANCE_001_POLICY.md) (§10).
Lịch sử HR-ATTENDANCE-001 (S1–S4, `20.0.1.2.0`): [acceptance 001](../../docs/demo/HR_ATTENDANCE_001_ACCEPTANCE.md).

Module nhỏ cùng DB, dùng hồ sơ `hr.employee`, tài khoản và phòng ban hiện có. Không cài
`hr_attendance` native (route token, systray check-in, cron vắng mặt/tăng ca — xem policy §6).

## Mô hình

| Model | Vai trò | Ghi |
| --- | --- | --- |
| `tp.hr.attendance.session` | Phiên vào-ra (UTC) | Chỉ server (import/đính chính) |
| `tp.hr.attendance.day` | Ngày công: giờ vào/ra, tình trạng dữ liệu/kỳ; RPC tổng quan/bảng công | Chỉ server |
| `tp.hr.attendance.batch` / `.line` | Lô nhập Excel: xem trước → nhập, staging từng ô nguồn | HR manager / người được phân công nhập |
| `tp.hr.attendance.late` | **Tổng đi muộn của máy** (Lần/Phút) theo nhân viên + kỳ nguồn + lô | Chỉ server; một bản `applied` mỗi người/kỳ |
| `tp.hr.attendance.source` / `.source.code` / `.event` | Nền API máy: nguồn, mã trên máy theo namespace, sự kiện thô bất biến | Chưa kết nối máy thật |
| `tp.hr.attendance.code` | Mã máy Excel (cột ID) → hồ sơ | HR manager |
| `tp.hr.attendance.rule` / `.assignment` / `.period` / `.correction` / `.log` | Quy tắc công, phân công, kỳ chốt, phiếu điều chỉnh, nhật ký (giữ từ 001) | Như 001 |

Giờ tham chiếu `08:30–17:00` (`ir.config_parameter` `tp_hr_attendance.reference_hours`) **chỉ để
hiển thị**; module không tính đi muộn từ giờ vào.

## Nhập Excel máy chấm công

Nút **Nhập Excel máy chấm công** trên Tổng quan và Bảng chấm công (chỉ hiện khi có quyền nhập): kéo-thả
hoặc chọn `.xlsx` → hệ thống tự đọc và hiện **xem trước** (chưa ghi gì) → bấm **Nhập dữ liệu**. Không phải
gõ tên lô, kỳ hay cột. Lịch sử lô và dòng staging ở Quản trị chấm công → Nhập dữ liệu (`/odoo/nhap-cong`).

- Kỳ lấy từ dòng `Từ ngày … Đến ngày …`; cột ngày sinh động theo kỳ (7/14/21 ngày, 28–31 ngày, qua
  tháng/năm). Ngày lặp mà header không giải nghĩa được → báo ô cần xem lại, không đoán.
- Nhóm **Đi muộn** (Lần/Phút) tìm theo header 2 tầng + ô gộp, không cố định cột. Số được giữ **đúng như
  ô nguồn** cho đúng kỳ của file: `0` là 0; ô trống là *Chưa có số liệu*; chữ/số âm/thập phân là *không hợp
  lệ*; `Lần=0` mà `Phút>0` là *Cần kiểm tra*. Không tự sửa số, không chia cho ngày.
- Đối chiếu người chỉ theo mã máy đã gán hoặc mã nguồn **và** họ tên khớp; tên khác → *Mã máy khớp nhưng
  tên khác*. Không ghép chỉ bằng tên, không tạo người, không đổi phòng/mã.
- Chống trùng: phiên theo `(nhân viên, giờ vào, giờ ra)`; tổng muộn theo `(công ty, nhân viên, từ, đến)`.
  Nhập lại cùng file → *Trùng*, nút Nhập bị khóa khi không còn gì mới. Cùng kỳ nhưng tổng khác → *Xung
  đột*, không ghi đè. Kỳ đã chốt → *Kỳ đã chốt*, không ghi. Hủy/chọn file khác trước khi nhập → lô xem
  trước bị hủy, không ghi phiên/ngày/tổng muộn.
- File tuần và file tháng chồng nhau được lưu riêng theo kỳ nguồn; không cộng tuần vào tháng.

RPC: `tp.hr.attendance.batch.tp_upload_preview / tp_upload_apply / tp_upload_cancel` (kiểm `can(import)`).

## Tổng quan chấm công (`/odoo/cham-cong`)

Mặc định **hôm nay** (Asia/Ho_Chi_Minh) + nút **Xem ngày có dữ liệu gần nhất**; chế độ Ngày / Tuần (T2–CN) /
Tháng. Dải nguồn ghi rõ Excel/API, lúc cập nhật và **dữ liệu đến ngày nào** — dữ liệu Excel không phải
thời gian thực. KPI: Tổng nhân viên (hồ sơ HR đang hoạt động), Nghỉ đã xác nhận (*Chưa đủ dữ liệu* khi
chưa có nguồn nghỉ đã duyệt; ô trống không phải nghỉ), Đã ghi nhận ra. Donut theo ngày lấy tổng nhân viên
làm mẫu số; cột theo ngày cho tuần/tháng; bấm lát/cột mở đúng danh sách. Ngày chưa đến không tính nghỉ.
RPC `tp.hr.attendance.day.tp_overview`.

## Bảng chấm công (`/odoo/bang-cong`)

- **Ngày**: Nhân viên (tên + mã), Phòng ban, Thứ/ngày, Giờ vào, Giờ ra; thiếu giờ hiện `—`.
- **Tuần / Tháng / Kỳ theo file**: mỗi người một dòng với Số lần đi muộn, Tổng phút muộn. Chỉ hiện số khi
  có tổng **phủ đúng kỳ** (nhãn *Theo Excel máy · kỳ …*). Ngày lẻ hoặc một phần kỳ → *Số đi muộn có ở tổng
  kỳ 09–15/11*; tháng không có tổng đúng kỳ → *Chưa có tổng đi muộn đúng kỳ …* + danh sách kỳ nguồn.
- Bấm người → chi tiết kỳ, 2 chỉ số muộn và bảng Thứ/ngày – Giờ vào – Giờ ra. Lọc phòng/tìm, pager
  10/20/50/100, xuất Excel (sheet giờ theo ngày + sheet Tổng đi muộn khi có kỳ đúng; chặn công thức).

RPC `tp_sheet / tp_person / tp_export_sheet`; **Công của tôi** (`/odoo/cong-cua-toi`) dùng `tp_mine /
tp_export_mine`, nhân viên lấy từ session.

## Nền API máy (`/odoo/nguon-cham-cong`) — chưa kết nối

`tp.hr.attendance.source.tp_ingest(events, watermark)` là điểm vào duy nhất cho adapter tương lai (gọi từ
code server): chuẩn hóa sự kiện (mã ngoài giữ chuỗi/số 0 đầu, thời điểm + múi giờ → UTC, chiều IN/OUT/
UNKNOWN, `received_at`), fingerprint theo namespace + mã sự kiện (hoặc mã + giờ + chiều) để retry không nhân
đôi, gắn nhân viên chỉ qua bảng mã của đúng nguồn, watermark tiến cùng transaction. `live_enabled` bị khóa
bằng constraint; **không có cron, không có HTTP route, không lưu token** (chỉ tên biến môi trường).
Trang Nguồn dữ liệu hiện *API: Chưa cấu hình* và checklist 9 thông tin cần lấy từ hãng máy.

## Menu

- Chấm công: Tổng quan chấm công · Bảng chấm công · Công của tôi.
- Quản trị chấm công (theo capability): Nhập dữ liệu · Nguồn dữ liệu · Xử lý điều chỉnh · Chốt kỳ.
- Cấu hình HR: Quy tắc công · Mã máy chấm công · Phân công xử lý công · Nhật ký chấm công.

## Kiểm thử

Test thuần (không ORM): `test_logic`, `test_parser_late`, phần không-DB của `test_parser`. Test ORM:
`test_upload`, `test_access`, `test_correction`, `test_import`, `test_directory_privacy` — chỉ chạy trên DB
test riêng, không chạy trên DB đang dùng:

```bash
.venv/Scripts/python.exe odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -i tp_hr_attendance --test-tags /tp_hr_attendance --stop-after-init --no-http
```

Chỉ dùng workbook và hồ sơ tổng hợp (synthetic); không đưa tên, giờ công hay tệp thật vào Git.
