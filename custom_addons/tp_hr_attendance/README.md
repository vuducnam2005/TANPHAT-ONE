# TANPHAT ONE — Chấm công (`tp_hr_attendance`)

Batch `CHG-20261117-020` · HR-ATTENDANCE-001. Policy:
[HR_ATTENDANCE_001_POLICY.md](../../docs/security/HR_ATTENDANCE_001_POLICY.md) ·
nghiệm thu: [HR_ATTENDANCE_001_ACCEPTANCE.md](../../docs/demo/HR_ATTENDANCE_001_ACCEPTANCE.md).

Module nhỏ cùng DB, dùng hồ sơ `hr.employee`, tài khoản và phòng ban hiện có. Không cài
`hr_attendance` native (route token, systray check-in, cron vắng mặt/tăng ca — xem policy §6).

## Mô hình

| Model | Vai trò | Ghi |
| --- | --- | --- |
| `tp.hr.attendance.session` | Phiên vào-ra (UTC), field tương thích `hr.attendance` | Chỉ server (import/đính chính) |
| `tp.hr.attendance.day` | Tổng hợp ngày: giờ vào/ra, giờ ghi nhận, công, tình trạng dữ liệu/kỳ | Chỉ server |
| `tp.hr.attendance.batch` / `.line` | Lô nhập Excel: xem trước → áp dụng, staging từng ô nguồn | HR manager / người được phân công nhập |
| `tp.hr.attendance.code` | Mã máy (cột ID) → hồ sơ | HR manager |
| `tp.hr.attendance.rule` | Quy tắc công đã xác nhận (khung giờ, nghỉ trưa, giờ chuẩn) | HR manager |
| `tp.hr.attendance.assignment` | Phân công nhập/duyệt/chốt theo phạm vi phòng | HR manager |
| `tp.hr.attendance.period` | Kỳ công đang mở/đã chốt | Người có phân công chốt |
| `tp.hr.attendance.log` | Nhật ký chỉ thêm | Chỉ server |

Nhóm mới duy nhất `group_attendance_officer` được đồng bộ tự động từ phân công đang hiệu lực
(chỉ mở ACL đọc staging/nhật ký); không cấp nhóm HR cho mọi người.

## Nhập báo cáo máy chấm công

1. **Nhân sự → Chấm công → Nhập dữ liệu → Mới**, chọn `.xlsx` (≤ 5 MB, ≤ 20 trang). Hệ thống
   từ chối tệp có macro, chỉ đọc giá trị (không công thức, không liên kết ngoài).
2. **Đọc tệp và xem trước**: mỗi ô ngày (Vào/Ra) thành một dòng staging với vị trí trang/ô.
   Đối chiếu: bảng Mã máy → nếu chưa có, mã nguồn `tp_source_code` trùng **và** họ tên (bỏ dấu)
   khớp. Tên khác → *Mã máy khớp nhưng tên khác*; không có hồ sơ → *Chưa đối chiếu*.
   Không tạo/sửa nhân viên.
3. Chống trùng theo chữ ký `(nhân viên, ngày, giờ vào, giờ ra)` trên toàn công ty, mọi tệp/trang/lần
   nhập: trang lặp lại hay nhập lại cùng tệp → *Trùng*. Cùng ngày nhưng giờ khác → *Xung đột*,
   không ghi đè. Thiếu giờ ra/vào, ký hiệu thay giờ, ô gộp → giữ staging (*Thiếu giờ vào/ra* /
   *Cần kiểm tra*), không điền giờ giả; nếu lô sau có cặp giờ khớp nửa đã biết thì tự hoàn thiện.
4. **Áp dụng dòng hợp lệ**: chỉ dòng *Hợp lệ* thành phiên; khóa hàng + advisory lock theo công ty
   nên bấm lặp/2 người cùng lúc không ghi đôi. Kỳ đã chốt → *Kỳ đã chốt*, không ghi.

Giờ lưu UTC; ngày công và giờ hiển thị theo `Asia/Ho_Chi_Minh`. Cột tổng hợp của máy
(đi muộn, vắng, tổng công, ghi chú) không được nhập.

## Bảng công (`/odoo/bang-cong`)

Client action `tp_hr_attendance.board`, RPC `tp.hr.attendance.day.tp_board`: chế độ tháng (ma trận
nhân viên × ngày, cột Mã TP/Nhân viên và tiêu đề cố định, cuộn trong bảng, tổng theo loại) và
ngày (bảng; thẻ trên mobile, mặc định trên màn hình < 768 px). Bộ lọc kỳ/phòng/nhân viên-mã
TP/tình trạng/kỳ chốt (+ lô nhập cho người xử lý), chip, xóa lọc, 10/20/50/100 dòng; bộ lọc,
trang và chế độ được giữ khi mở ngày công rồi quay lại. Ô không có bản ghi: *Không có giờ vào/ra*
(lô đã áp dụng có người đó trong kỳ) hoặc *Chưa có nguồn*; ngày tương lai *Chưa đến*.

Công xác nhận chỉ có khi **Quy tắc công đã xác nhận** phủ ngày đó; nếu không, hiển thị
**Chưa xác nhận** — không phải nghỉ không phép, không trừ lương.

## Kiểm thử

Version20.0.1.2.0 bổ sung **Tổng quan công** (`/app/cham-cong`), **Công của tôi**
(`/app/cong-cua-toi`, cùng tab profile), phiếu điều chỉnh riêng/duyệt/trả và chốt kỳ.
Dashboard tái sử dụng bộ dựng bảng công, loại tương lai, count ngày-người; mobile cards.
CSV own lấy owner session và whitelist. Bổ sung bảo vệ mobile/contact, export proxy
employee và resume/certificate theo owner/HR. Xem guide và acceptance để phân biệt
kiểm source/in-memory/read-only browser với các ORM/transition/race chưa chạy.

```bash
.venv/Scripts/python.exe odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -i tp_hr_attendance --test-tags /tp_hr_attendance --stop-after-init --no-http
```

Chỉ dùng workbook và hồ sơ tổng hợp (synthetic); không đưa tên, giờ công hay tệp thật vào Git.
