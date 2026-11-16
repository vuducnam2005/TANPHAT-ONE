# TANPHAT ONE — Trung tâm Báo cáo

CORP-REPORT-001, native Odoo20. Dùng chung HR/user/company/project/task và session; scope backend bằng `ir.access` Odoo20 cùng assignment còn hiệu lực. Dữ liệu Báo cáo nằm trong DB của môi trường, không cần Excel đầu vào.

Luồng: mục tiêu quý → tháng → tuần; nhân viên tải việc vào nháp, nhập kết quả, xem trước/gửi; người rà nhận xét từng dòng, trả lại/chốt; nhân viên phản hồi/sửa/gửi lại. Báo cáo phòng/công ty tổng hợp exact snapshot, theo kỳ/ngày/đơn vị và nguồn đóng góp; directive có owner/hạn. State công việc độc lập state báo cáo.

Snapshots/events/reviews bất biến; action có transaction/version/request key. Tiền tách model, enter/confirm/read riêng, thiếu nguồn khác0; không suy payment request thành thực thu. Native SearchModel/filter/pager/favorite và shell/back/identity chung. Dashboard cùng layout theo phạm vi quyền, donut/planactual không sinh dữ liệu giả. Export Excel/Word/PDF chạy server, no-store, snapshot đúng phiên bản và quyền hiện hành.

Mẫu/lịch mặc định là cấu hình kỹ thuật/chưa ban hành. Không bật email/cron ra người thật. Fixture chỉ test có marker, không cài qua module data. Không dùng technical admin làm người có thẩm quyền doanh nghiệp.

- [Acceptance](../../docs/demo/CORP_REPORT_001_ACCEPTANCE.md)
- [Schema/quyền](../../docs/security/CORP_REPORT_001_SCHEMA_AND_ACCESS.md)
- [Thiết kế UI](../../docs/ui/CORP_REPORT_001_DESIGN.md)
- [Triển khai/rollback](../../ops/runbooks/CORP_REPORT_001_DEPLOY_AND_ROLLBACK.md)

Trạng thái nghiệm thu và giới hạn thực tế nằm ở PROJECT_STATUS/acceptance; README mô tả mục tiêu triển khai, không thay log test. Main18069 chưa áp.
