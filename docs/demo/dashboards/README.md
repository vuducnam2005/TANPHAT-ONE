# Bảng tổng hợp mẫu — NATIVE-DATA-002

Cấu hình tái lập cho hai bảng tổng hợp native trong app Dashboards (`spreadsheet.dashboard`), CHG-20261102-008. Không chứa số liệu: mọi ô là công thức `PIVOT`/`PIVOT.VALUE`/`PIVOT.HEADER`, khi mở thì Odoo truy vấn trực tiếp theo quyền của người xem.

| File | Bảng | Nguồn dữ liệu |
| --- | --- | --- |
| `tp_project_coordination.template.json` | Điều phối dự án (nhóm Services) | `project.task`, `account.analytic.line` của bốn dự án mẫu |
| `tp_invoice_expense_draft.template.json` | Hóa đơn và chi phí dự kiến (nhóm Finance) | `account.move` nháp, `hr.expense` nháp thuộc fixture |
| `build_templates.py` | Sinh lại hai file trên | — |

Token được seeder thay bằng ID thật tra theo XML ID fixture, không dùng tên hiển thị:

- `"__PROJECT_IDS__"`, `"__INVOICE_IDS__"`, `"__EXPENSE_IDS__"` thành mảng ID.
- `__PID_CAU__`, `__PID_DUONG__`, `__PID_NUT__`, `__PID_VENBIEN__`, `__CID__` thành số nguyên.

Mọi domain đều có `company_id`; dashboard tài chính chỉ lấy `state = draft`.

Quyền: seeder tạo dashboard với `group_ids` rỗng, `allowed_user_ids = admin`, `company_ids = công ty 1`. Mặc định `base.group_user` không được dùng. Không có sudo, không có snapshot tiền, không tạo link Share. Nút Share native vẫn hiện trên mọi dashboard; với dữ liệu demo không dùng nút này.

Sửa template: chỉnh `build_templates.py`, chạy lại, rồi chạy seeder ở chế độ `apply`. Seeder ghi đè `spreadsheet_data` của đúng hai dashboard thuộc namespace `tp_native_data002_20261102`, còn chế độ `verify` báo lỗi nếu DB khác template. Seeder và runbook: xem [ODOO_NATIVE_SAMPLE_DATA.md](../ODOO_NATIVE_SAMPLE_DATA.md#native-data-002--lịch-trao-đổi-bảng-tổng-hợp-chg-20261102-008).
