# BIÊN BẢN NGHIỆM THU KỸ THUẬT: ĐẢO NGƯỢC THỨ TỰ NGÀY CHẤM CÔNG (HR-ATTENDANCE-ORDER-001)

- **Mã hạng mục:** `CHG-20261120-014` / `HR-ATTENDANCE-ORDER-001`
- **Ngày thực hiện:** 20/11/2026
- **Phân hệ:** `custom_addons/tp_hr_attendance` (phiên bản `20.0.3.5.8`)
- **Trạng thái:** `PC_SERVER_APPLIED` & `VERIFIED`

---

## 1. MỤC TIÊU & YÊU CẦU NGHIỆP VỤ

### Yêu cầu trực tiếp từ người dùng:
- Trước đây, trong mục **Chấm công** ("Công của tôi"), bảng giờ vào/ra đang sắp xếp theo thứ tự ngày cũ nhất lên đầu (từ ngày 01 đến ngày 30).
- Khi nhân viên muốn xem ngày công hiện tại (ví dụ: hôm nay ngày 20), họ buộc phải cuộn chuột xuống gần đáy bảng.
- **Yêu cầu:** Đảo ngược thứ tự hiển thị để ngày mới nhất (hôm nay) nằm ngay trên đầu danh sách; bấm vào màn hình là thấy ngay ngày hôm nay (ngày 20), cuộn xuống dưới là các ngày cũ hơn (ngày 19, 18, 17...).

---

## 2. GIẢI PHÁP KỸ THUẬT TRIỂN KHAI

### 2.1. Nâng cấp Backend (`attendance_overview.py`)
- Cập nhật logic sắp xếp ngày trong 2 hàm cốt lõi:
  1. `_tp_mine_dataset`: Nguồn cấp dữ liệu cho màn hình "Công của tôi" (`/app/nhan-su/cham-cong/cua-toi` và tab Chấm công trong Hồ sơ cá nhân).
  2. `_tp_person_data`: Nguồn cấp dữ liệu khi cấp quản lý/HR mở xem chi tiết công của một nhân viên (`PersonDialog`).
- **Quy tắc sắp xếp mới:**
  ```python
  ordered_dates = sorted(
      dates_between(start, end),
      key=lambda d: (d > today, -d.toordinal() if d <= today else d.toordinal()),
  )
  ```
  - **Nhóm 1 — Ngày đã qua và ngày hiện tại (`work_date <= today`):** Sắp xếp giảm dần (`-d.toordinal()`). Ngày mới nhất (Hôm nay/ngày 20) luôn đứng ở **VỊ TRÍ ĐẦU TIÊN (Row 1)**. Cuộn chuột xuống là các ngày hôm qua (19), hôm kia (18)... lùi dần về ngày đầu tháng (01).
  - **Nhóm 2 — Ngày tương lai (`work_date > today`):** Nằm ở phần dưới của bảng, sắp xếp theo trình tự thời gian tới (21, 22... 30) với nhãn trạng thái *"Chưa đến"*.
  - **Khi xem các tháng đã qua (ví dụ tháng 10):** Toàn bộ ngày trong tháng là ngày quá khứ, ngày cuối tháng (31/10) đứng đầu tiên, cuộn xuống lùi dần về ngày 01/10.

### 2.2. Bảo toàn tính toàn vẹn nghiệp vụ
- Tổng hợp số liệu kỳ (`summary = summarize_mine_rows(all_rows)`): Số lượng ngày có công, ngày đủ vào/ra, ngày thiếu giờ, ngày đi muộn giữ nguyên 100% độ chính xác.
- Bộ lọc tình trạng & thứ trong tuần (`filter_mine_rows`): Hoạt động chuẩn xác, giữ nguyên thứ tự giảm dần mới nhất lên đầu.
- Xuất file Excel (`tp_export_mine`): Sử dụng tập hợp ngày hợp lệ, bảo toàn định dạng báo cáo.

---

## 3. KẾT QUẢ KIỂM THỬ THỰC TẾ TRÊN MÁY CHỦ PC SERVER

Truy vấn trực tiếp backend trên môi trường máy chủ PC Server thật (`192.168.1.73:8069`) cho tài khoản nhân viên (Trần Phương Đông - TP001):
```text
Employee: Trần Phương Đông (Mã: TP001)
Today: 2026-11-20
Total rows: 30

--- 5 DÒNG ĐẦU TIÊN (NẰM TRÊN ĐẦU BẢNG) ---
Row 1: 2026-11-20 (Thứ 6) | In: 08:45 | Out: — | is_today: True  | status: Chờ ghi nhận giờ ra
Row 2: 2026-11-19 (Thứ 5) | In: —     | Out: — | is_today: False | status: Vắng theo lịch
Row 3: 2026-11-18 (Thứ 4) | In: 09:07 | Out: — | is_today: False | status: Thiếu giờ ra
Row 4: 2026-11-17 (Thứ 3) | In: 09:20 | Out: — | is_today: False | status: Thiếu giờ ra
Row 5: 2026-11-16 (Thứ 2) | In: —     | Out: — | is_today: False | status: Vắng theo lịch

--- CÁC DÒNG TIẾP NỐI & RANH GIỚI NGÀY TƯƠNG LAI ---
Row 18: 2026-11-03 (Thứ 3)   | is_today: False | future: False | status: Vắng theo lịch
Row 19: 2026-11-02 (Thứ 2)   | is_today: False | future: False | status: Thiếu giờ ra
Row 20: 2026-11-01 (Chủ nhật)| is_today: False | future: False | status: Nghỉ theo lịch
Row 21: 2026-11-21 (Thứ 7)   | is_today: False | future: True  | status: Chưa đến
Row 22: 2026-11-22 (Chủ nhật)| is_today: False | future: True  | status: Chưa đến
Row 23: 2026-11-23 (Thứ 2)   | is_today: False | future: True  | status: Chưa đến
```

**Đánh giá:**
- Row 1 hiển thị ngay ngày `20/11/2026` (Hôm nay), có giờ vào `08:45` và nhãn *"Chờ ghi nhận giờ ra"*.
- Người dùng bấm vào mục Chấm công là nhìn thấy ngay ngày hôm nay mà không cần cuộn chuột.
- Cuộn xuống dưới là các ngày cũ (19, 18, 17... lùi về 01).

---

## 4. QUÁ TRÌNH TRIỂN KHAI & SAO LƯU

1. **Sao lưu trước áp dụng:**
   - Thư mục backup trên PC Server: `C:\TANPHAT-backups\hr-attendance-sort-order\20261120T190555\`
   - Database dump: `tp_tanphat_dev_pre.dump`
   - Code package: `tp_hr_attendance_pre.tar.gz`
2. **Nâng cấp:**
   - Module `tp_hr_attendance` nâng cấp lên phiên bản **`20.0.3.5.8`** trong container `tp-odoo` (Modules loaded exit 0).
   - Container `tp-odoo` đã khởi động lại an toàn.
3. **Health Check:**
   - LAN: `http://192.168.1.73:8069/web/health` -> HTTP 200 OK (`{"status": "pass"}`).
   - Public: `https://tpone.tadic.vn/web/health` -> HTTP 200 OK (`{"status": "pass"}`).
