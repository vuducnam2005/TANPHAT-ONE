# `UI-TABLE-FILTER-001` — Runbook triển khai & rollback (`tp_tanphat_dev` / `18069`)

Runbook này chuẩn bị cho lần áp dụng `UI-TABLE-FILTER-001` lên database chính `tp_tanphat_dev` (`18069`, PostgreSQL port `55432`) **chỉ khi có lệnh giao riêng của người dùng**. Hiện tại chỉ mới triển khai và kiểm thử xong trên `tp_tanphat_test` (`18079`); tuyệt đối không restore `tp_tanphat_test` đè lên `tp_tanphat_dev` hoặc tạo thêm DB ngoài `tp_tanphat_dev` và `tp_tanphat_test` (`DEC-037`).

---

## 1. Danh sách source chính xác (`custom_addons/`)

- `tp_web_home`: `static/src/search/*`, `static/tests/search/*`, `__manifest__.py`, `README.md`.
- `tp_hr_workspace`: `views/search_views.xml`, `views/hr_ui.xml`, `views/workspace.xml`, `views/employment_contract.xml`, `static/src/table/filter_profiles.js`, `table.js`, `table.xml`, `table.scss`, `static/src/my_profile/my_profile.js`, `my_profile.xml`, `tests/test_table_filter_hr.py`, `__manifest__.py`, `README.md`.
- `tp_kd_workspace`: `views/search_views.xml`, `views/project_restructure.xml`, `views/wbs.xml`, `static/src/table/filter_profiles.js`, `table_tools.js`, `table_tools.xml`, `relation_tools.js`, `tables007.scss`, `static/src/overview/overview.js`, `tests/test_table_filter_kd.py`, `__manifest__.py`, `README.md`.
- `tp_contract`: `views/tp_contract_search_views.xml`, `__manifest__.py`.
- `tp_core`: `views/tp_work_item_search_views.xml`, `views/native_search_views.xml`, `__manifest__.py`.
- `tp_crm_project_bridge`: `views/crm_tag_search_views.xml`, `__manifest__.py`.
- `tp_dashboard_privacy`: `views/dashboard_search_views.xml`, `__manifest__.py`.

---

## 2. Quy trình sao lưu & diễn tập khôi phục trước khi áp main

1. **Chốt danh sách nguồn & kiểm trước:** xác nhận `git status`, `git diff --check`, `ruff check custom_addons/` và `scripts/ai_workflow.py check` sạch; đóng gói hoặc ghi nhận SHA-256 snapshot source trước khi nâng cấp.
2. **Dừng tiến trình trên `18069` & kiểm phiên DB:** dừng dịch vụ `tp_tanphat_dev` đúng PID/config; kiểm tra `pg_stat_activity` bảo đảm 0 phiên kết nối ghi vào `tp_tanphat_dev`.
3. **Sao lưu DB + Filestore `main`:** dùng `pg_dump -Fc` xuất `tp_tanphat_dev.dump` kèm bản sao nguyên vẹn thư mục filestore của `tp_tanphat_dev` vào thư mục backup riêng (ví dụ `.local/ui-table-filter001/backup-main/`), ghi SHA-256, `pg_restore --list` (TOC count) và số lượng tệp filestore.
4. **Restore verification trên `tp_tanphat_test` (`18079`):** khôi phục bản backup `main` vào DB test `tp_tanphat_test` (sau khi neutralize cron/email), chạy `-u tp_core,tp_contract,tp_crm_project_bridge,tp_web_home,tp_dashboard_privacy,tp_kd_workspace,tp_hr_workspace --stop-after-init`, đối chiếu số bảng/dòng/blob và chạy kiểm thử hồi quy xác nhận nâng cấp sạch từ trạng thái `main` thực tế.

---

## 3. Lệnh nâng cấp trên `tp_tanphat_dev` (`18069` — chỉ chạy khi được giao riêng)

```powershell
# Bảo đảm server 18069 đã dừng và backup hoàn tất trước khi chạy
.\.venv\Scripts\python.exe -m odoo -c .local\dev\odoo.conf `
  -u tp_core,tp_contract,tp_crm_project_bridge,tp_web_home,tp_dashboard_privacy,tp_kd_workspace,tp_hr_workspace `
  --no-http --stop-after-init --logfile .local\ui-table-filter001\upgrade-main.log
```

Sau nâng cấp `--no-http`:
1. Kiểm tra log `upgrade-main.log` có `Modules loaded.` và 0 `ERROR`/`CRITICAL`.
2. Đối chiếu row count các bảng cốt lõi (`res_users`, `res_partner`, `hr_employee`, `res_groups`, `ir_access`, `ir_ui_menu`, `project_project`, `crm_lead`, `tp_contract`) khớp với snapshot trước nâng cấp.
3. Khởi động lại daemon `18069` và chạy **Playwright read-only smoke** (mở Danh sách nhân viên, Hồ sơ cần bổ sung, Dự án KH-KD, Cơ hội, Báo cáo R01, Project Templates, UserMenu 2 mục — chỉ thao tác đọc/lọc/xem, 0 tạo/sửa/xóa bản ghi và kiểm tra 0 lỗi console/HTTP >= 500).

---

## 4. Quy trình Rollback nếu có sự cố sau khi áp main

`UI-TABLE-FILTER-001` chỉ bổ sung XML `<search>` views và asset JS/SCSS (không thêm bảng SQL nghiệp vụ hay thay đổi schema dữ liệu cốt lõi), tuy nhiên các `ir.ui.view` và `ir.attachment` asset bundle đã được cập nhật trong PostgreSQL DB của `main`:

1. Dừng dịch vụ `18069` ngay lập tức, chụp bản sao hiện trạng trước rollback nếu đã phát sinh giao dịch nghiệp vụ mới trên `main` (để đánh giá giữ dữ liệu giao dịch trước khi phục hồi).
2. Khôi phục source `custom_addons/` về snapshot trước `UI-TABLE-FILTER-001` (hoặc gỡ các view/file mới theo mục §1, không dùng `git reset --hard` phá các task trước đó và không sửa `odoo/`/`addons/`/`frontend/`).
3. Nếu chưa phát sinh giao dịch mới (hoặc đã có phương án bảo toàn giao dịch): phục hồi **chính xác `tp_tanphat_dev.dump` + filestore từ bản backup `main` đã chụp ở bước 2** (tuyệt đối không dùng DB test), kiểm tra lại row counts, khởi động lại `18069` và chạy smoke read-only xác nhận hệ thống trở về nguyên trạng trước nâng cấp.
