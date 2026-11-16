# tp_kd_workspace — Workspace & Trung tâm Báo cáo KH-KD

Module Odoo mở rộng cung cấp giao diện native OWL cho Khối Kế hoạch - Kinh doanh (KH-KD) trong hệ thống TANPHAT ONE. Từ `UI-SHELL-UNIFY-001` (14/11/2026), thanh bên KH-KD sử dụng `<TpUserAccountMenu>` dùng chung từ `tp_web_home` ở cuối sidebar thay cho nút `"Tài khoản"` cũ để hiển thị `[Avatar] Họ tên người đang đăng nhập` và dropdown 2 mục (`Thông tin cá nhân` đồng bộ HR và `Đăng xuất`).

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
* Kiểm thử backend: `tests/test_report_center.py`, `tests/test_table_filter_kd.py` (Odoo tests).
* Kiểm thử frontend: `static/tests/report_center.test.js`, `static/tests/tables007.test.js` (HOOT unit tests).
* Kiểm thử E2E: `scripts/kd_report001_ui.cjs` (Playwright browser & openpyxl).

## 4. Bộ lọc bảng toàn phân hệ (`UI-TABLE-FILTER-001` — 14/11/2026)

* Chuẩn hóa cấu hình bộ lọc theo nội dung (`static/src/table/filter_profiles.js`, `table_tools.js/xml`, `relation_tools.js`, `tables007.scss`) dùng chung `<TpTableFilterBar>` của `tp_web_home` cho danh sách KH-KD, TP Contracts và deep links (`kdEnabled`).
* Cô lập `project_search_restructure` (`priority="32"` tại `views/search_views.xml`) để `project.open_view_project_template` giữ nguyên search view native; bổ sung `kd_task_search` (`views/wbs.xml`) và search views cho các smart button KH-KD. Xem [TP_TABLE_FILTER_INVENTORY.md](../../docs/ui/TP_TABLE_FILTER_INVENTORY.md).
