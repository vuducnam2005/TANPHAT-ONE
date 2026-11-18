# HR-ATTENDANCE-SIMPLE-002 — Acceptance

Phạm vi: `tp_hr_attendance` 20.0.1.2.0 → 20.0.2.0.0 (DEC-055/056). Viết trước khi sửa code;
cột **Kết quả** được điền khi bàn giao (PASS / FAIL / NOT_RUN kèm lý do). Không dùng tên,
giờ hoặc mã người thật trong test Git; file `bang cham cong vao ra.xlsx` chỉ đọc local.

## A. Đọc Excel máy (parser thuần)

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| A01 | File thật, chỉ đọc local | Kỳ 09/11/2026–15/11/2026 lấy từ dòng "Từ ngày … Đến ngày …", không lấy tiêu đề "THÁNG" hay ngày xuất 2017; 39 người; 150 cặp đủ giờ; 28 ngày thiếu giờ ra; 95 ô trống; 0 lỗi định dạng |
| A02 | File thật — Đi muộn | Tìm nhóm "Đi muộn" theo header 2 tầng + merged (không hardcode AC/AD); mỗi người một cặp Lần/Phút đúng bằng ô nguồn; 0 giữ là 0, trống là "Chưa có số liệu" |
| A03 | Kỳ 7 / 14 / 21 ngày (fixture ẩn danh) | Đủ cột ngày, cột Đi muộn dịch sang phải vẫn đọc đúng |
| A04 | Kỳ 28 / 29 / 30 / 31 ngày | Không chặn vì giới hạn 7 ngày; thứ đọc từ lịch thực |
| A05 | Kỳ qua tháng và qua năm | Ngày 30/12 → 05/01 gán đúng tháng/năm |
| A06 | Số ngày lặp trong kỳ (vd 15/01→15/02) mà header không đủ giải nghĩa | Báo ô lỗi cần xem lại, không đoán tháng |
| A07 | Header dịch cột (STT không ở cột A) và nhóm Đi muộn merged | Đọc định danh, ngày và Lần/Phút đúng |
| A08 | Thiếu cột Đi muộn / có cột nhưng ô trống / số âm hoặc chữ / Lần=0 mà Phút>0 | Giờ vẫn nhập; số muộn = Chưa có số liệu (thiếu/không hợp lệ) hoặc Cần kiểm tra (bất nhất); không tự sửa số |
| A09 | Nhiều sheet trong một file | Mỗi sheet có kỳ riêng; sheet lỗi không chặn sheet đọc được |
| A10 | Ô trống, ký hiệu, nhiều giờ một ô | Trống = chưa ghi nhận (không phải nghỉ); ký hiệu/nhiều giờ giữ nguồn + cảnh báo |

## B. Lưu và chống trùng (ORM)

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| B01 | Kéo-thả .xlsx → xem trước tự động → Nhập dữ liệu | Không phải gõ tên lô/kỳ/cột; preview hiện kỳ, người đã khớp, mới/trùng/thiếu giờ/chưa khớp/xung đột, số đi muộn |
| B02 | Chọn file khác / Hủy trước khi ghi | Lô xem trước bị hủy, không ghi phiên, ngày hay tổng muộn |
| B03 | Nhập lại cùng file / đổi tên file | Giờ và tổng muộn hiện Trùng; không nhân đôi |
| B04 | File tuần chồng file tháng | Hai tổng lưu riêng theo kỳ nguồn; xem tháng chỉ lấy bản phủ đúng kỳ, không cộng tuần vào tháng |
| B05 | Cùng kỳ nhưng tổng muộn khác | Xung đột, không ghi đè (không last-write-wins) |
| B06 | Kỳ đã chốt | Tổng muộn và giờ thuộc kỳ chốt không ghi; giữ correction/lịch sử |
| B07 | Mapping | Chỉ theo ID máy đã đối chiếu (mã máy + họ tên khớp); không ghép chỉ bằng tên, không tạo người, không đổi phòng/mã |
| B08 | Dữ liệu cũ (lô 1, lô 2 trên 18069) | Giữ nguyên; không xóa/nhập lại session, day, correction, chốt kỳ |

## C. Bảng chấm công tối giản

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| C01 | Chế độ Ngày | Cột: Nhân viên (tên + mã), Phòng ban, Thứ/ngày (một ô), Giờ vào, Giờ ra; thiếu giờ hiện "—", không bịa 17:00 |
| C02 | Chế độ Tuần (T2–CN) / Tháng / Kỳ theo file | Một dòng mỗi người: Nhân viên, Phòng ban, Số lần đi muộn, Tổng phút muộn; nhãn kỳ nguồn rõ |
| C03 | Xem đúng kỳ file | Hiện N lần / M phút, nhãn "Theo Excel máy" |
| C04 | Lọc một ngày hoặc phần của kỳ | Không chia/copy tổng; ghi "Số đi muộn có ở tổng kỳ 09–15/11", không hiện 0 |
| C05 | Kỳ không có nguồn phủ chính xác | "Chưa có tổng đúng kỳ" + danh sách kỳ nguồn riêng; không bịa số tháng |
| C06 | Bấm người | Chi tiết: tên/mã/phòng, kỳ, 2 chỉ số muộn, bảng Thứ/ngày – Giờ vào – Giờ ra |
| C07 | Lọc phòng/tìm/pager 10/20/50/100 | Đúng scope company và quyền; xóa lọc giữ company |
| C08 | Xuất Excel | Sheet giờ theo ngày (cột tối giản) + sheet Tổng đi muộn khi có kỳ nguồn chính xác; ghi khoảng ngày; chặn công thức; người chỉ đọc không xuất dữ liệu chung |

## D. Tổng quan chấm công (dashboard)

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| D01 | Mặc định | Ngày hôm nay thật (Asia/Ho_Chi_Minh); nút riêng "Xem ngày có dữ liệu gần nhất" |
| D02 | Dải nguồn | Excel/API, lúc cập nhật, dữ liệu đến ngày, trạng thái kết nối (API: Chưa cấu hình) |
| D03 | KPI Tổng nhân viên | Hồ sơ HR đang hoạt động trong phạm vi xem; không đếm user hoặc chỉ người có trong Excel |
| D04 | KPI Nghỉ đã xác nhận | Chưa có nguồn nghỉ → "Chưa đủ dữ liệu", không hiện 0 |
| D05 | KPI Đã ghi nhận ra | Theo lượt hợp lệ mới nhất; không khẳng định "Đã về" khi không rõ kết thúc ngày |
| D06 | Chip Đang làm / Chưa chấm công / Cần kiểm tra | Mỗi người một trạng thái chính tại mốc; ô trống ≠ nghỉ |
| D07 | Donut ngày | Tổng nhân viên là mẫu số ở giữa, không là một lát; bấm lát mở đúng danh sách |
| D08 | Cột theo ngày (tuần/tháng) | Số người theo ngày; KPI kỳ là người khác nhau (distinct) |
| D09 | Ngày chưa đến | Không coi là nghỉ, không vẽ lát |
| D10 | Màu + nhãn | Xanh dương tổng, xanh lá hợp lệ/đang làm, cam thiếu dữ liệu, tím nghỉ, xám chưa rõ; không chỉ dựa vào màu |
| D11 | Chuyển động | 150–250 ms, tôn trọng reduced-motion, không animation lặp |
| D12 | Mobile 375–390 px | KPI/chart một cột, bảng cuộn trong vùng riêng, không tràn trang |

## E. Nền API máy (chưa kết nối thật)

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| E01 | Chuẩn hóa sự kiện | Mã ngoài là chuỗi giữ số 0 đầu; timestamp + timezone; IN/OUT/UNKNOWN; received_at |
| E02 | Fingerprint | Namespace + event ID, không có event ID thì namespace + mã + giờ + chiều; retry không nhân đôi |
| E03 | Watermark | Chỉ tiến cùng transaction ghi sự kiện |
| E04 | Trạng thái hiện diện | IN chưa OUT; OUT→IN lại = đang làm; ra buổi trưa; UNKNOWN = Cần kiểm tra; không tự đặt OUT |
| E05 | Mapping mã | Theo namespace nguồn + company; chưa map = chờ xử lý, không gán theo tên |
| E06 | Trang Nguồn dữ liệu | Excel đang dùng; API "Chưa cấu hình"; adapter live tắt; checklist thông tin cần hãng |
| E07 | An toàn | Không cron, không endpoint public ghi công, không token trong source/log |

## F. Quyền, menu, vận hành

| ID | Kiểm | Kỳ vọng |
|---|---|---|
| F01 | Nhân viên thường | Chỉ đọc; không import, không raw payload/CCCD/lương; Công của tôi lấy employee từ session |
| F02 | HR / người được giao nhập công | Nhập qua action backend gốc (kiểm `can(import)`) |
| F03 | Menu thường | Chỉ Tổng quan chấm công, Bảng chấm công, Công của tôi; Nhập dữ liệu, Nguồn dữ liệu, Xử lý điều chỉnh, Chốt kỳ ở Quản trị chấm công; action/deep link giữ nguyên |
| F04 | Admin | Chỉ admin gốc cấp/thu admin (DEC-053/054); task này không grant admin |
| F05 | Backup trước upgrade | DB + filestore + source + config trên đúng môi trường |
| F06 | 18069 thật | Ngày có nguồn, hôm nay, ngày chưa đến, tuần/tháng, filter/KPI/chart→list, pager, desktop/mobile; dữ liệu cũ không hiện là realtime |

## Kết quả (`CHG-20261118-019`, 18/11/2026)

Bằng chứng: **P** = test thuần `test_logic` + `test_parser_late` + phần không-DB của `test_parser` (22 test,
0 lỗi, chạy trong `odoo-bin shell` 18069 rồi rollback); **R** = runtime 18069 (`tp_tanphat_dev`, admin, nhập
file thật qua UI; đếm tổng trước/sau bằng SQL chỉ đọc); **E** = Playwright 18069 `33/33` PASS (desktop 1440,
mobile 390/375). Ảnh và log chỉ ở `.local/hr-attendance-simple002/` (có tên thật, không commit). Test ORM
`TransactionCase` (`test_upload`, `test_access`, `test_correction`, `test_import`, `test_directory_privacy`)
**NOT_RUN**: không có DB test riêng trong phiên (không dùng 18079, không tạo clone, không chạy fixture trên
DB đang dùng).

| ID | Kết quả | Ghi chú |
|---|---|---|
| A01 | PASS (R) | Xem trước file thật: kỳ 09/11–15/11/2026, 39 người, 38 khớp hồ sơ, 178 ngày-người có giờ (150 đủ + 28 thiếu ra), 95 ô trống, 0 lỗi |
| A02 | PASS (P, R) | Nhóm Đi muộn tìm theo header; 38 người khớp: 90 lần / 6418 phút đúng ô nguồn (file 91/6612 gồm 1 người *Tên khác hồ sơ* không ghi) |
| A03 | PASS (P) | 7/14/21 ngày, cột Đi muộn dịch theo số ngày |
| A04 | PASS (P) | 28/29/30/31 ngày, năm nhuận 2028 |
| A05 | PASS (P) | 26/10→08/11 và 28/12→03/01 |
| A06 | NOT_RUN | Chưa có test riêng cho số ngày lặp mà header không giải nghĩa |
| A07 | PASS một phần (P) | Nhóm Đi muộn merged ở vị trí dịch; STT không ở cột A: NOT_RUN riêng |
| A08 | PASS (P) | Thiếu nhóm/nhóm lặp/nhóm thiếu cột/ô trống/chữ/thập phân/bất nhất: không đoán số, giờ vẫn đọc |
| A09 | PASS (P) | 2 sheet đọc riêng |
| A10 | PASS (P) | Ô trống không phải nghỉ, không bịa giờ ra; ký hiệu giữ trạng thái kiểm tra |
| B01 | PASS (E, R) | Kéo-thả → xem trước → Nhập: 117 phiên mới, 42 trùng lô cũ, 2 xung đột, 16 thiếu giờ ra, 1 tên khác; 38 tổng muộn |
| B02 | PASS (R) | 4 lô xem trước bị hủy trong e2e; số phiên tăng đúng 117 = số dòng mới đã nhập |
| B03 | PASS cùng file (E) | Nhập lại: báo đã nhập, 0 mới, 177 trùng, 38 tổng muộn trùng, nút Nhập khóa. Đổi tên file: NOT_RUN riêng |
| B04 | PASS (P) / NOT_RUN ORM | `late_cover`: tháng không cộng tuần, chỉ ghép kỳ phủ khít |
| B05 | PASS (P) / NOT_RUN ORM | Ghép kỳ mâu thuẫn báo xung đột; ORM “cùng kỳ khác số” nằm trong `test_upload` |
| B06 | NOT_RUN | 18069 không có kỳ chốt; không tạo kỳ chốt giả |
| B07 | PASS (R) | 1 người tên khác hồ sơ không được gán; hồ sơ 39, user 28 không đổi |
| B08 | PASS (R) | Phiên 182→299, ngày 252→365 chỉ thêm; 0 trùng ngày/tổng muộn; điều chỉnh 0, kỳ chốt 0 không đổi |
| C01 | PASS (E) | Chế độ Ngày mặc định của bảng; thiếu giờ hiện `—` |
| C02 | PASS (E) | Tuần/Tháng/Kỳ theo file; pager 10 |
| C03 | PASS (E) | *Theo Excel máy · kỳ 09–15/11 · 38 người có số liệu · 90 lần · 6418 phút* |
| C04 | PASS (E) | Ngày: *Số đi muộn có ở tổng kỳ 09–15/11*, không hiện 0 |
| C05 | PASS (E) | Tháng 11: *Chưa có tổng đi muộn đúng kỳ…* + nút 3 kỳ nguồn |
| C06 | PASS (E) | Hộp chi tiết người theo kỳ |
| C07 | PASS một phần (E) | Pager 10/20/50/100, tìm/lọc phòng; scope theo quyền non-admin: NOT_RUN |
| C08 | PASS một phần (E) | Tải xuất file kỳ nguồn; chặn công thức PASS (P); chặn người chỉ đọc: NOT_RUN ORM (đã có guard) |
| D01 | PASS (E) | *Hôm nay · T4 18/11/2026* + nút ngày có dữ liệu gần nhất (T7 14/11) |
| D02 | PASS (E) | Excel máy, cập nhật, dữ liệu đến 15/11/2026; API *Chưa cấu hình* |
| D03 | PASS (E, R) | 39 = hồ sơ HR đang hoạt động |
| D04 | PASS (E) | *Chưa đủ dữ liệu* |
| D05 | PASS (E) | *Đã ghi nhận ra* kèm chú thích có thể còn quay lại |
| D06 | PASS (E) | Chip Đang làm/Chưa chấm công/Cần kiểm tra/Chưa có dữ liệu, mỗi người một trạng thái |
| D07 | PASS (E) | Tổng lát 39 = mẫu số; bấm lát lọc đúng danh sách |
| D08 | PASS (E) | Tuần 7 cột T2–CN, tháng 30 cột; chip kỳ đếm người khác nhau; bấm cột lọc theo ngày |
| D09 | PASS (E) | Ngày tương lai *Chưa đến*, cột khóa |
| D10 | PASS (E, ảnh) | Màu kèm nhãn chữ |
| D11 | PASS (E) | 0.18s; reduced-motion 0s |
| D12 | PASS (E) | 390/375: 0 tràn ngang ở Tổng quan/Bảng/Nguồn dữ liệu |
| E01 | PASS (P) | Giữ số 0 đầu, đổi giờ có múi sang UTC, chiều lạ → UNKNOWN |
| E02 | PASS (P) | Fingerprint theo namespace; retry không nhân đôi |
| E03 | PASS source / NOT_RUN ORM | Watermark ghi cùng transaction với sự kiện (`test_upload`) |
| E04 | PASS (P) | IN chưa OUT, OUT→IN, ra trưa, UNKNOWN; không tự đặt giờ ra |
| E05 | NOT_RUN ORM | Mapping theo namespace + company trong `test_upload`; kiểm source |
| E06 | PASS (E) | API *Chưa cấu hình*, không nói thời gian thực/đã nối, checklist 9 mục |
| E07 | PASS (grep) | Không `ir.cron`, không `http.route` trong module; `live_enabled` khóa bằng constraint |
| F01 | NOT_RUN | Không đăng nhập trình duyệt bằng nhân viên thường (không dùng mật khẩu người thật) |
| F02 | PASS (E) | Admin nhập qua RPC kiểm `can(import)` |
| F03 | PASS (E) | Chấm công: 3 mục; Quản trị chấm công: 4 mục; Cấu hình HR: 4 mục |
| F04 | PASS | Không cấp/thu admin |
| F05 | PASS 18069 + PC server | 18069: `.local/hr-attendance-simple002/backup-has002-20261118T133410`. PC server: `C:\TANPHAT-backups\hr-attendance-simple002\has002-20261118T141006` (dump `9.587.361`B + restore-list `15.438` mục, filestore `29.827.466`B, source-config `1.845.934`B, SHA256SUMS); `-u` exit 0 / 0 ERROR; public Playwright chỉ đọc `19/19` PASS; server chưa nhập file 09–15/11 |
| F06 | PASS (E, R) | Như D/C ở trên; dữ liệu Excel cũ không hiện là thời gian thực |

## HR-ATTENDANCE-SCROLL — CHG-20261118-038

Yêu cầu18/11: cuộn Tổng quan không được kéo toàn webclient và lộ khoảng trắng.
Trước sửa: desktop1440×900 document1503px, cuộn tiếp ở đáy windowY603;
mobile390×844 document5536px, windowY4400. `.visually-hidden` absolute và
theadẩn mobile lấy body làm containing block ngoài scrollport.

Sửa tối thiểu: `.o_tp_att { position: relative }`, scroll chaining chứa trong
màn độc lập; nhúng Công của tôi vẫn để parent điều phối. Giữ label/aria,
không chặn cuộn bằng bodyoverflowhidden hoặc wheelpreventDefault.

| Kiểm | Kết quả18069 |
| --- | --- |
| 1440×900,1366×768,390×844,375×667; Ngày/Tuần/Tháng | 12/12PASS |
| Wheel đến đáy, cuộn tiếp, rồi về đầu | Contentcuộn được, documentY0 |
| Navbar/sidebar | Giữ vị trí trước/sau |
| Documentheight/width | Không vượt viewport |
| Labeltrợ năng | Offsetparent nằm trong scrollport |
| JavaScript errors | 0 |

Regression: `scripts/tests/test_hr_attendance_scroll.cjs`; dùng
`TP_SCROLL_STORAGE_STATE`, `TP_SCROLL_BASE_URL`, `TP_SCROLL_OUTPUT` trỏ
session riêng private đã có, không tự đăng nhập hoặc ghi dữ liệu công.
Ảnh/số đo riêng: `.local/attendance-scroll037/local-after/results.json`.
PCserver: chờ giao CSS đã push và kiểm asset thực. Chưa kiểm iOS/Safari thật;
mobile trên là Chromiumemulation, không là nghiệm thu hình thức của người dùng.
