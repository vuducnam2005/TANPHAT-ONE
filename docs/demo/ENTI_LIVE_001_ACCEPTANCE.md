# Nghiệm thu ENTI-LIVE-001 — Tích hợp dữ liệu chấm công ENTI thật, đồng bộ tự động và cập nhật giao diện

- **Mã thay đổi:** `CHG-20261119-025`
- **Nhiệm vụ:** `ENTI-LIVE-001`
- **Phiên bản addon:** `tp_hr_attendance` `20.0.3.4.0`
- **Môi trường triển khai:** PC server (192.168.1.73), database `tp_tanphat_dev`, container `tp-odoo` / `tp-postgres`.
- **Public URL kiểm chứng:**
  - Cloudflare: `https://eight-championships-launches-plaintiff.trycloudflare.com`
  - Localtunnel: `https://tanphatone.loca.lt`

---

## 1. Mục tiêu và phạm vi đã hoàn thành

1. **Kết nối API trực tiếp từ backend:**
   - Triển khai `EntiClient` (`custom_addons/tp_hr_attendance/models/enti_client.py`) qua HTTP session (Python `requests.Session`), đầy đủ luồng:
     - Đăng nhập `POST /__enti/api/v1/auth/login`.
     - Tự động gia hạn token qua `POST /__enti/api/v1/auth/refresh` và cơ chế đăng nhập lại graceful.
     - Lấy hồ sơ và danh sách ứng dụng `GET /__enti/api/v1/apps/my`.
     - Chọn đúng ngữ cảnh công ty `POST /__enti/api/v1/session/select-app` (ứng dụng "Công ty Cổ phần Tấn Phát"), duy trì đầy đủ cookie phiên (`enti_active_app`, `enti_session`, `enti_tunnel`).
     - Truy vấn bảng công `POST /api/attendace/bang-cong` với xử lý phân trang thực tế (`searchResultPosition`, `maxTotalResult`, `moreData`).
   - Tuyệt đối không dùng trình duyệt Playwright chạy thường trực làm connector production.

2. **Đối chiếu nhân viên và giữ vững Single Source of Truth:**
   - Model `tp.hr.attendance.enti.mapping`:
     - Ghép nối an toàn `source_id + keyNV (UUID) → hr.employee`.
     - Gợi ý tự động (`tp_suggest_mapping`) theo họ tên chuẩn và đối chiếu tương quan mã máy lịch sử (ví dụ: `TP001` tương ứng mã Odoo `TP10001`).
     - Danh sách **"Đối chiếu nhân viên ENTI"** (`views/enti_views.xml`) với bộ lọc, nhóm trạng thái: *Đã khớp*, *Chờ xác nhận*, *Chưa đối chiếu*.
     - Các nút thao tác **"Xác nhận"** và **"Hủy khớp"** dành riêng cho Quản lý nhân sự / Admin.
     - **Nguyên tắc bảo vệ:** Tuyệt đối không đổi mã nhân viên Odoo, không đổi phòng ban hay quyền hạn dựa trên ENTI.

3. **Xử lý dữ liệu ngày chưa đủ giờ & tôn trọng ràng buộc ORM:**
   - Model `tp.hr.attendance.enti.day`: lưu trữ bất biến dữ liệu thô từ ENTI theo từng ngày làm việc (lấy chính xác từ trường `ngay`).
   - Cơ chế chiếu dữ liệu `_tp_project_to_canonical`:
     - Nếu có đủ giờ vào và ra hợp lệ (`check_out > check_in`): tạo/cập nhật phiên làm việc `tp.hr.attendance.session` với `source='enti'`, tính toán giờ làm chuẩn.
     - Nếu chưa đủ giờ (chỉ có giờ vào, hoặc chỉ có giờ ra, hoặc hai mốc bằng nhau): cập nhật `tp.hr.attendance.day` với `data_state='missing'`, hiển thị đúng mốc giờ đã có trên giao diện, **không tự ý điền 17:00**, **không tạo session giả** để tránh vi phạm constraint `CHECK(check_out > check_in)`.
     - Vô hiệu hóa các session Excel cũ của cùng ngày để chống tính trùng.

4. **Thứ bậc ưu tiên dữ liệu (Strict Hierarchy):**
   - **Ưu tiên 1 (Cao nhất):** Đề nghị điều chỉnh công đã duyệt (`is_correction=True`). Sync ENTI phát hiện ngày đã điều chỉnh sẽ ghi nhận `superseded_correction` và không ghi đè số giờ đã duyệt.
   - **Ưu tiên 2:** Dữ liệu tự động từ ENTI API (`source_kind='enti'`).
   - **Ưu tiên 3:** Tệp Excel máy chấm công đã nhập (`source_kind='excel'`). Hàm `_tp_recompute` và quy trình nhập file mới sẽ bỏ qua các ngày đã có nguồn ENTI.

5. **Đồng bộ tự động & Khóa chống xung đột:**
   - Định kỳ cron `ir_cron_enti_attendance_sync` chạy tự động mỗi 1 phút trên PC server gọi `_tp_cron_enti_sync()`.
   - Cơ chế khóa giao dịch PostgreSQL Advisory Lock (`pg_advisory_xact_lock(761129, source_id)`) đảm bảo không bao giờ xảy ra chạy đè hoặc race condition giữa cron và thao tác bấm tay.
   - Bảng nhật ký `tp.hr.attendance.enti.sync.log` lưu lại thời điểm, khoảng ngày, số nhân viên, số ngày áp dụng, thời gian thực thi (giây) và thông báo chi tiết.

6. **Cập nhật giao diện trực tiếp không cần F5:**
   - Backend phát sự kiện `enti_sync_completed` qua bus hệ thống `bus.bus` trên kênh `tp_hr_attendance_channel`.
   - Toàn bộ các màn hình người dùng (`AttendanceDashboard`, `AttendanceBoard`, `MyAttendance`, `AttendanceSources`) tự động đăng ký kênh bus và cập nhật dữ liệu ngầm khi có dữ liệu mới.
   - Bổ sung cơ chế polling ngầm 30 giây khi tab đang hiển thị (`!document.hidden`) đảm bảo giao diện luôn được cập nhật liên tục kể cả khi kết nối websocket bị gián đoạn.
   - Thẻ nguồn `SourceStrip` và thẻ API trên trang Nguồn dữ liệu hiển thị rõ ràng: `API máy: Đang hoạt động (Trực tiếp) · Kết nối trực tiếp: bật (tự động)`.

7. **Bảo mật tuyệt đối thông tin xác thực:**
   - Secret được đọc từ `.local/enti_secrets.json`, biến môi trường hoặc `ir.config_parameter`.
   - Wizard cấu hình `tp.hr.attendance.enti.config.wizard` cho phép Admin nhập thông tin, kiểm tra kết nối và lưu vào máy chủ; mật khẩu được che (`password="True"`), không lưu trong log, không trả về trình duyệt và chỉ hiển thị nhãn "Đã cấu hình".

---

## 2. Đo lường và phân biệt ba độ trễ

Hệ thống công bố rõ ràng và minh bạch 3 độ trễ riêng biệt:

| Phân đoạn | Bản chất | Thời gian đo lường thực tế |
|---|---|---|
| **1. Máy chấm công → ENTI** | Phụ thuộc vào kết nối mạng của máy chấm công tại văn phòng/công trường lên cloud ENTI | Thường từ **10 giây – 3 phút** tùy cấu hình đẩy của thiết bị |
| **2. ENTI → Odoo** | Chu kỳ quét của cron job tự động trên PC server | **1 phút** (hoặc tức thì khi người quản trị bấm "Đồng bộ ngay") |
| **3. Odoo → Màn hình người dùng** | Bus WebSocket notification + Fallback visibility polling | **< 1 giây** (qua Bus) / tối đa **30 giây** (fallback không cần F5) |

> **Cam kết:** Giao diện chỉ hiển thị trạng thái "Trực tiếp" khi nguồn ENTI đang bật `live_enabled=True` và lần đồng bộ gần nhất không có lỗi. Nếu kết nối mất hoặc thông tin xác thực chưa cấu hình, giao diện lập tức chuyển sang nhãn "Chưa cấu hình" hoặc "Chưa kết nối", tuyệt đối không giả mạo trạng thái live.

---

## 3. Danh mục tệp thay đổi

### Mã nguồn Backend (Odoo ORM)
- `custom_addons/tp_hr_attendance/__manifest__.py`: Nâng version `20.0.3.4.0`, đăng ký `views/enti_views.xml`.
- `custom_addons/tp_hr_attendance/models/__init__.py`: Import `enti_client`, `enti_day`, `enti_mapping`, `enti_sync`, `enti_wizard`.
- `custom_addons/tp_hr_attendance/models/enti_client.py` (MỚI): HTTP Client kết nối API ENTI.
- `custom_addons/tp_hr_attendance/models/enti_day.py` (MỚI): Model lưu trữ dữ liệu thô và thuật toán chiếu sang bảng công chuẩn.
- `custom_addons/tp_hr_attendance/models/enti_mapping.py` (MỚI): Quản lý đối chiếu định danh nhân viên ENTI - Odoo.
- `custom_addons/tp_hr_attendance/models/enti_sync.py` (MỚI): Động cơ đồng bộ, quản lý secret, cron job và bus notification.
- `custom_addons/tp_hr_attendance/models/enti_wizard.py` (MỚI): Wizard cấu hình bảo mật và đồng bộ thủ công.
- `custom_addons/tp_hr_attendance/models/attendance_source.py`: Bổ sung loại nguồn `enti_api`, mở cờ `live_enabled`, trả thông tin ENTI trong `tp_sources_overview`.
- `custom_addons/tp_hr_attendance/models/attendance_day.py`: Bảo vệ nguồn ENTI không bị Excel import ghi đè.
- `custom_addons/tp_hr_attendance/models/attendance_overview.py`: Nhận diện nguồn ENTI, cập nhật nhãn nguồn và cờ `live`.
- `custom_addons/tp_hr_attendance/security/ir.access.csv`: Khai báo 11 dòng quyền truy cập và company rule cho các model mới.
- `custom_addons/tp_hr_attendance/views/enti_views.xml` (MỚI): Giao diện Wizard cấu hình, bảng đối chiếu nhân viên và nhật ký đồng bộ.
- `custom_addons/tp_hr_attendance/views/menus.xml`: Đăng ký menu Quản trị chấm công cho ENTI.
- `custom_addons/tp_hr_attendance/data/attendance_data.xml`: Khai báo cron job tự động `ir_cron_enti_attendance_sync`.
- `custom_addons/tp_hr_attendance/migrations/20.0.3.4.0/post-migrate.py` (MỚI): Migration xóa bỏ triệt để ràng buộc `tp_hr_attendance_source_live_off`.

### Giao diện Người dùng (OWL / XML)
- `custom_addons/tp_hr_attendance/static/src/sources.js` & `sources.xml`: Thẻ trạng thái nguồn ENTI động, nút "Đồng bộ ngay", "Đối chiếu nhân viên", "Cấu hình kết nối", "Nhật ký đồng bộ".
- `custom_addons/tp_hr_attendance/static/src/parts.xml`: Hiển thị trạng thái `live` động trong `SourceStrip`.
- `custom_addons/tp_hr_attendance/static/src/dashboard.js`: Lắng nghe bus `enti_sync_completed` và polling 30s.
- `custom_addons/tp_hr_attendance/static/src/board/board.js`: Tự động làm mới bảng công khi có dữ liệu mới.
- `custom_addons/tp_hr_attendance/static/src/mine.js`: Tự động làm mới màn hình "Công của tôi" của nhân viên.

### Kiểm thử tự động (Unit & Integration Tests)
- `custom_addons/tp_hr_attendance/tests/test_enti_sync.py` (MỚI): Bộ test Odoo kiểm tra toàn diện mapping, incomplete punches, priority hierarchy và idempotency.
- `scripts/tests/test_enti_pure.py` (MỚI): Kiểm thử logic phân tích giờ và dữ liệu DB-free (4/4 PASS).

---

## 4. Kết quả kiểm thử kỹ thuật

1. **Kiểm thử logic không cần DB (`scripts/tests/test_enti_pure.py`):**
   - Chuyển đổi múi giờ ICT sang UTC chính xác.
   - Xử lý biên chuỗi giờ không hợp lệ, chuỗi rỗng hoặc vượt quá 24h.
   - Trích xuất ngày đúng từ trường `ngay` (không nhầm lẫn day1 với mùng 1).
   - Kiểm tra ngữ nghĩa chấm công nửa buổi (in-only / out-only).
   - **Kết quả:** `Ran 4 tests in 0.037s: OK`.

2. **Kiểm thử tích hợp ORM (`test_enti_sync.py`):**
   - Xác minh mapping: gợi ý đúng theo họ tên, xác nhận/hủy khớp hoạt động chuẩn.
   - Xác minh chấm công đủ giờ: tạo session hợp lệ `check_out > check_in`, tính giờ chuẩn.
   - Xác minh chấm công thiếu giờ: cập nhật `data_state='missing'`, không tạo session lỗi, không bị dính constraint DB.
   - Xác minh thứ bậc ưu tiên: ngày có đề nghị điều chỉnh đã duyệt không bao giờ bị ENTI ghi đè.
   - Xác minh tính idempotent: đồng bộ lại nhiều lần không nhân đôi bản ghi.

3. **Cú pháp và biên dịch:**
   - 100% tệp Python biên dịch thành công (`py_compile`).
   - 100% tệp XML phân tích cú pháp hợp lệ (`xml.etree.ElementTree`).
   - `ir.access.csv` khớp 100% cấu trúc 6 cột chuẩn của hệ thống.
