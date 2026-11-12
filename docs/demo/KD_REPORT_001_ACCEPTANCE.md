# KD-REPORT-001 — Tiêu chí Nghiệm thu Trung tâm Báo cáo KH-KD (`A01`–`A12`)

Tài liệu này định nghĩa 12 tiêu chí nghiệm thu quan sát được (`A01`–`A12`) và kết quả kiểm chứng thực tế cho batch **KD-REPORT-001 — Tách Báo cáo KH-KD thành chức năng riêng** (`CHG-20261109-004`).

---

## 1. Bảng tiêu chí nghiệm thu (`A01`–`A12`)

| Mã | Tiêu chí nghiệm thu | Cách kiểm chứng quan sát được | Trạng thái |
|---|---|---|---|
| **A01** | `Tổng quan` và `Báo cáo KH-KD` mở hai action/màn khác nhau, mục đích rõ ràng. | Bấm `Tổng quan` (`menu_overview`) mở `action_overview` (`.o_tp_kd_ov`, tiêu đề `Tổng quan KH-KD`); bấm `Báo cáo KH-KD` (`menu_reports`) mở `action_reports` (`.o_tp_kd_rc`, tiêu đề `Báo cáo KH-KD`). Sidebar highlight đúng từng mục. | **ĐẠT (PASS)** |
| **A02** | Đủ 6 nhóm báo cáo `R01`–`R06`, chuyển qua lại mượt, dữ liệu khớp nguồn. | Chuyển lần lượt `R01` → `R06` trên trình duyệt và qua RPC `get_kd_report`; kiểm tra số lượng bản ghi, cột, nhóm và tổng đối chiếu khớp hoàn toàn với truy vấn độc lập trên model nguồn. | **ĐẠT (PASS)** |
| **A03** | Bộ lọc kỳ/ngày/dự án/người phụ trách/trạng thái hoạt động đúng; chip bộ lọc đang áp dụng rõ ràng. | Chọn kỳ (`Tháng này`/`Quý này`/`Năm nay`/`Tùy chọn`), dự án, người phụ trách, trạng thái; kiểm tra trạng thái pending trước khi bấm `Áp dụng bộ lọc` và chip `Đang áp dụng` sau khi bấm; kiểm tra lỗi `date_from > date_to`. | **ĐẠT (PASS)** |
| **A04** | Bảng dữ liệu rõ ràng, có chọn số dòng `10/20/50/100`, sắp xếp, nhóm và dòng tổng hợp hợp lệ. | Đổi `page_size` (`10/20/50/100`), chuyển trang trên tập > 100 bản ghi, đổi `group_by` và `sort_by`, ẩn/hiện cột tùy chọn; dòng tổng tính trên toàn bộ kết quả đã lọc. | **ĐẠT (PASS)** |
| **A05** | Không cộng trùng revision hợp đồng, giao khoán cha/con, hoặc các giai đoạn sản lượng/nghiệm thu/thanh toán. | Test bẫy dữ liệu trên clone: hợp đồng có `original` + `amendment` + `correction` + `draft`; giao khoán có cấp 1 + cấp 2; dự án có kế hoạch + sản lượng + nghiệm thu + đề nghị thu/chi; chứng chỉ gắn nhiều cơ hội thầu. Không trường hợp nào bị cộng gộp sai. | **ĐẠT (PASS)** |
| **A06** | Không lộ tiền với vai trò không có quyền; không biến chưa xác nhận/không quyền thành `0`. | Kiểm tra với `support` (0 `financial_read`) và user bị thu hồi grant: mọi cột tiền, thẻ tổng hợp, biểu đồ và file Excel hiển thị `"Không có quyền xem tiền"`; dòng `unconfirmed` hiển thị `"Chưa xác nhận"`, không cộng vào tổng bằng `0`. | **ĐẠT (PASS)** |
| **A07** | Mở được hồ sơ/danh sách nguồn từ báo cáo và quay lại giữ ngữ cảnh. | Bấm mở hồ sơ nguồn hoặc nhóm dữ liệu từ bảng báo cáo sang form/list Odoo native, sau đó quay lại `Báo cáo KH-KD` (breadcrumb/history): giữ nguyên `report_key`, bộ lọc đã áp dụng, nhóm, sắp xếp và trang. | **ĐẠT (PASS)** |
| **A08** | Xuất Excel `.xlsx` mở được, đúng bộ lọc, đúng quyền, đủ kết quả đã lọc (không chỉ trang đang nhìn), chống formula injection. | Tải file `.xlsx` qua HTTP cho cả 6 báo cáo; dùng `openpyxl` đọc lại kiểm tra tiêu đề, bộ lọc, tổng số dòng (> `page_size` khi phân trang), quyền tiền theo vai trò, và chuỗi độc hại `=SUM(1,2)`, `+cmd`, `-cmd`, `@cmd` được escape bằng `'`. | **ĐẠT (PASS)** |
| **A09** | Desktop (`1440×1000`) và Mobile (`390×844`), zoom `200%`, bàn phím hoạt động tốt, không vỡ bố cục. | Kiểm tra Playwright ở `1440×1000`, `390×844` và zoom `200%`: không tràn ngang toàn trang (`scrollWidth <= innerWidth + 1`), điều hướng tab bằng bàn phím, `:focus-visible` rõ. | **ĐẠT (PASS)** |
| **A10** | Hover/animation nhẹ, không nhấp nháy khi đổi bộ lọc, tôn trọng `prefers-reduced-motion`. | Kiểm tra CSS transition 140–220ms trên thẻ/hàng/nút, không chạy lại intro sweep khi đổi trang/sắp xếp, và tắt toàn bộ animation khi bật `prefers-reduced-motion: reduce` hoặc `is-reduced`. | **ĐẠT (PASS)** |
| **A11** | `Tổng quan` hiện hữu vẫn hoạt động đúng, không gãy test cũ. | Toàn bộ suite `test_dashboard`, `test_reporting`, `test_ui_layout`, `test_workspace`, `tp_contract`, `tp_crm_project_bridge`, `tp_project`, `tp_web_home` và HOOT unit tests đều PASS. | **ĐẠT (PASS)** |
| **A12** | Dev `18069` được áp từ clone đã pass sau backup verified, giữ nguyên 100% dữ liệu và phân quyền. | Đối chiếu `preservation-before.json`, `preservation-after.json` và `preservation-final.json`: 0 thay đổi bản ghi nghiệp vụ, tài khoản, mật khẩu, phân quyền, dự án, đính kèm. | **ĐẠT (PASS)** |

---

## 2. Kết quả kiểm chứng thực tế

### 2.1. Kiểm thử Odoo Backend & HOOT Unit Tests
* **Odoo Test Suite (`scripts/kd_report001.py test`)**:
  - Kết quả: **164/164 tests PASS (0 failed, 0 errors)** trên clone DB `tp_tanphat_kdreport001_20261109`.
  - Phân bổ: `tp_kd_workspace`: 60, `tp_contract`: 73, `tp_crm_project_bridge`: 7, `tp_project`: 12, `tp_web_home`: 12.
* **HOOT Unit Tests (`scripts/kd_report001_hoot.cjs`)**:
  - Kết quả: **14/14 tests PASS (57 assertions, 0 failed, 0 errors)**.
  - Kiểm chứng: mounting view, catalog 6 tab, URL parameter restoration, pending vs applied filters, race condition sequence guard, access error recovery.

### 2.2. Kiểm thử Playwright Browser & Excel Export trên Clone (`19389`)
* Lệnh chạy: `node scripts/kd_report001_ui.cjs clone`
* Kết quả: **109/109 checks PASS, 0 failures, 0 errors**.
* Thời gian phản hồi (Performance SLA < 1.5s):
  - `head_R01_ms`: 37 ms
  - `head_R02_ms`: 922 ms (>100 cơ hội test)
  - `head_R03_ms`: 312 ms
  - `head_R04_ms`: 149 ms
  - `head_R05_ms`: 242 ms
  - `head_R06_ms`: 116 ms
  - Xuất Excel R01–R06: 57 ms – 942 ms.
* Xác minh Excel: Kiểm tra bằng thư viện `openpyxl`, tiêu đề chuẩn hóa, cấu trúc 3 phần (I. Chỉ tiêu, II. Nhóm, III. Chi tiết), phân trang không làm cắt ngắn dữ liệu xuất, và chống formula injection với dấu nháy `'`.

### 2.3. Sao lưu & Kiểm chứng phục hồi độc lập (Backup & Restore Verification)
* **Bản sao lưu**: `.local/kd-report001/backup-pre-apply-20261109T110311Z`
* **Cơ sở dữ liệu kiểm chứng**: `tp_tanphat_kdreport001_backup_110322`
* **Kết quả**: Khôi phục 100% thành công, số bảng: 577, số file đính kèm: 295, khớp hoàn toàn với snapshot gốc trước khi apply.

### 2.4. Áp dụng & Kiểm chứng trên Máy chủ Dev (`18069`)
* Lệnh chạy: `node scripts/kd_report001_ui.cjs dev`
* Kết quả: **105/105 checks PASS, 0 failures, 0 errors**.
* Bảo toàn dữ liệu (`scripts/kd_report001.py preserve --label final`):
  - Số bảng theo dõi: 37 bảng.
  - Số dòng: 3,467 dòng (chỉ tăng đúng 1 dòng trong `ir_access` cho model `tp.kd.report.center`, 0 dòng nghiệp vụ bị thay đổi hoặc mất mát).
  - Phân quyền & menu: Giữ nguyên 100% phân quyền, menu `menu_reports` cập nhật action sang `action_reports` phục vụ phân tách.
  - Đính kèm ngoài asset: 282 (khớp 100% trước và sau).
  - Module đã cài: 94 module (khớp 100% trước và sau).

### 2.5. Bằng chứng Hình ảnh Đã Thu thập (86 ảnh)
* Đường dẫn thư mục: `.local/kd-report001/shots/`
  - Ảnh dev trước thay đổi: `.local/kd-report001/shots/dev/before/`
  - Ảnh dev sau khi áp dụng: `.local/kd-report001/shots/dev/after/`
  - Ảnh kiểm thử clone: `.local/kd-report001/shots/clone/after/`
* Bao gồm ảnh màn hình của cả 5 vai trò (Trưởng phòng, Phó phòng, Chủ trì dự án, Kế hoạch, Hỗ trợ), đầy đủ 6 tab R01–R06, form drill-down, mobile viewport 390x844 và zoom 200%.
