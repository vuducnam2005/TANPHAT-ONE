# tp_kd_workspace — Workspace & Trung tâm Báo cáo KH-KD

Module Odoo mở rộng cung cấp giao diện native OWL cho Khối Kế hoạch - Kinh doanh (KH-KD) trong hệ thống TANPHAT ONE.

## 1. Cấu trúc chức năng chính

1. **Tổng quan KH-KD (`tp.kd.overview`)**:
   - Menu: `tp_kd_workspace.menu_overview` -> Action `action_overview`
   - JS Class: `tp_kd_overview`
   - Mục đích: Theo dõi hoạt động hằng ngày, xử lý việc cần làm (My Work), giám sát phễu công việc, hợp đồng, dự án theo vai trò.

2. **Trung tâm Báo cáo KH-KD (`tp.kd.report.center`) — KD-REPORT-001**:
   - Menu: `tp_kd_workspace.menu_reports` -> Action `action_reports`
   - JS Class: `tp_kd_report_center`
   - Controller HTTP: `/tp_kd/report/export` (`controllers/report_export.py`)
   - Mục đích: Tổng hợp số liệu theo kỳ, đối chiếu đa chiều giữa 6 nhóm nghiệp vụ, gom nhóm dữ liệu và xuất Excel toàn diện.

## 2. 6 Nhóm Báo cáo Nghiệp vụ

* **R01**: Dự án và hợp đồng — Theo dõi phiên bản hiệu lực hiện hành (`_effective_revision`), tách bạch bản gốc và phụ lục, không cộng trùng.
* **R02**: Cơ hội và hồ sơ thầu — Quản lý trạng thái hồ sơ thầu, lọc cơ hội tiền dự án (chưa gắn dự án), hỗ trợ phân trang >100 bản ghi.
* **R03**: Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán — 4 cột độc lập cạnh nhau, tách bạch sản lượng, nghiệm thu, tiền đề nghị và tiền thực thu/chi sổ sách.
* **R04**: Giao khoán và thầu phụ — Phân tách Khoán cấp 1 (Parent) và Khoán cấp 2 (Child), tỷ lệ khoán/giá trị hợp đồng, cảnh báo vượt mức.
* **R05**: Tình trạng xử lý và trách nhiệm hồ sơ — Tổng hợp 10 nguồn nghiệp vụ, gắn nhãn SLA quá hạn/đến hạn/trong hạn, phân quyền xem việc của tôi vs phòng ban.
* **R06**: Năng lực, chứng chỉ và nghĩa vụ hồ sơ — Phân định chứng chỉ tổ chức vs cá nhân, ngưỡng 30 ngày hết hạn, đếm duy nhất, không có cột tiền.

## 3. Kiến trúc bảo mật & Kiểm thử

* Phân quyền xem tiền (`can_view_money`): Dựa trên quyền tài chính `_kd_financial_projects()`. Người dùng không có quyền (như nhân viên hỗ trợ) sẽ bị che số tiền ở mọi view, thẻ tóm tắt và file Excel tải về.
* Kiểm thử backend: `tests/test_report_center.py` (Odoo tests).
* Kiểm thử frontend: `static/tests/report_center.test.js` (HOOT unit tests).
* Kiểm thử E2E: `scripts/kd_report001_ui.cjs` (Playwright browser & openpyxl).
