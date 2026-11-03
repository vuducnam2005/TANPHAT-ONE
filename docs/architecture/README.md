# Kiến trúc nền tảng TANPHAT ONE

[Tên hệ thống và phân hệ TANPHAT ONE](TP_PRODUCT_NAMING.md) là quy ước hiện hành cho tên hiển thị.

[So sánh Odoo Community/Enterprise](TP_ODOO_COMMUNITY_ENTERPRISE_COMPARISON.md) (31/10/2026) tổng hợp chức năng, tùy biến, deployment và chi phí/TCO cho TANPHAT ONE. Đây là nghiên cứu/đề xuất, chưa phải quyết định mua hoặc chuyển edition.

Từ quyết định ngày 28/10/2026, frontend chính là web riêng gọi API Odoo. Backend sử dụng addon chuẩn Odoo và addon Tấn Phát theo nghiệp vụ.

Ngày 30/10/2026, người dùng chọn bản **demo native Odoo khung toàn hệ thống** cho lãnh đạo xem (DEC-024), độc lập với frontend chính. [Prompt UI-DEMO-001](../prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md) đã triển khai ở CHG-20261030-002, trạng thái `IMPLEMENTED_PENDING_AUDIT`: [đặc tả demo](TP_UI_DEMO_001_SPEC.md), addon `custom_addons/tp_demo_workspace/`, [runbook](../../ops/runbooks/UI_DEMO_001.md). Demo dùng môi trường riêng, dữ liệu giả và nhãn phân biệt phần hoạt động với phần minh họa; không mở nghiệp vụ thật hoặc thay kiến trúc sản phẩm.

Lộ trình code và cách kiểm kết quả Claude nằm ở [kế hoạch điều phối giai đoạn lập trình](TP_CODE_EXECUTION_MASTER_PLAN.md). Đây là nguồn điều phối sau CHG-020; `PROJECT_STATUS.md` vẫn là trạng thái hiện hành.

Kiến thức tham khảo A1 Consulting, quan sát Base Request và nguyên tắc phân biệt quyết định/đề xuất/runtime được lưu ở [sổ kiến thức tham khảo và bàn giao](TP_REFERENCE_RESEARCH_AND_HANDOFF.md). Đây là tài liệu tham khảo có provenance, không thay `DECISIONS.md` hoặc quy chế nghiệp vụ.

Phân tích chọn lọc 16 manual IMIS2 EVN nằm ở [TP_IMIS2_REFERENCE_ANALYSIS.md](TP_IMIS2_REFERENCE_ANALYSIS.md) (chính sách và ranh giới chọn lọc) và [TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md](TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md) (bóc tách chi tiết từng trang, màn hình, biểu mẫu và quy tắc validation của 16 tài liệu). Manual chỉ cung cấp ý tưởng về hồ sơ/lifecycle; không tự mở module, quyền hoặc Data Lake.

Riêng Request: [kiến thức nghiệp vụ Request trên BASE](TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md) lưu nhóm, form, vai trò, vòng đời tham chiếu, cách ghi nhận kết quả và các gap cần kiểm chứng; không coi tab/filter là state API.

Phân tích chọn lọc các workbook ERP tham khảo nằm ở [TP_EXCEL_REFERENCE_ANALYSIS.md](TP_EXCEL_REFERENCE_ANALYSIS.md). Đây là bằng chứng cấu trúc/ý nghĩa nghiệp vụ đọc-only; không phải dữ liệu runtime, chính sách kế toán hoặc quyết định mở Finance/Import/Data Lake.

Thiết kế hiện hành: [Cấu trúc source nền tảng Tấn Phát](TP_PLATFORM_SOURCE_STRUCTURE.md).

Native fake-only NATIVE-DATA-003 đã áp dụng phần an toàn lên dev18069 (CHG-20261102-014), trạng thái `PARTIAL_WITH_GAPS`: [runbook](../demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md), [CRM bridge](TP_NATIVE_DATA003_BRIDGE_SPEC.md), [timesheet scope](TP_NATIVE_DATA003_TIMESHEET_SCOPE.md), [dashboard privacy](TP_NATIVE_DATA003_DASHBOARD_PRIVACY.md) và [RFC TASK-001](RFC_TASK_001_MANAGED_TASK_PROGRESS.md). Clone18149 đã dừng; demo18109/18119 tiếp tục ngừng. Không thay kiến trúc React/API, quyền nghiệp vụ thật hoặc cổng pilot.

Danh sách ứng dụng và trạng thái module đã đối chiếu source/database ngày 29/10/2026 nằm tại [TP_ODOO20_MODULE_INVENTORY.md](TP_ODOO20_MODULE_INVENTORY.md). Source có module không đồng nghĩa đã cài; module installed không đồng nghĩa nghiệp vụ đã cấu hình hoặc có frontend riêng. Danh mục không cho phép cài thêm module hoặc thay Next task.

Đăng nhập: [AUTH-002 — đặc tả hoàn thiện luồng đăng nhập](TP_AUTH002_LOGIN_SPEC.md) v0.6, giữ DEC-012; D1–D6 đã chốt (D6-a tắt tự đăng ký/đặt lại mật khẩu), câu chữ đã duyệt, V-A…V-C đã kiểm trên database test cô lập. Người dùng đã chuyển slice 1 và slice 2 sang `READY_FOR_TEST_CODE`; prompt [slice 1](../prompts/CLAUDE_AUTH002_S1_REACT_LOGIN.md) và [slice 2](../prompts/CLAUDE_AUTH002_S2_NATIVE_LOGIN.md) chạy lần lượt. Slice 1 đã code (CHG-035), audit/correction `TECHNICAL_ACCEPTED` phạm vi test (CHG-036/037): cả query/mutation 401 về login, R5 đã có live evidence; slice 2 chưa code.

Baseline nghiệp vụ KD: [BIZ-001 — workflow và ma trận quyền KD](TP_KD_WORKFLOW_AND_PERMISSIONS.md), kèm [bằng chứng nguồn và ca nghiệm thu](TP_KD_EVIDENCE_AND_ACCEPTANCE.md). Phần phân tích hoàn tất; thẩm quyền ký/duyệt và nghiệm thu chủ nghiệp vụ còn chờ. BASE giữ phê duyệt chính thức, TANPHAT ONE ghi nhận hồ sơ/kết quả. TP Contracts read slice (CTR-001) đã kiểm chứng trên dev; hiện ưu tiên review BIZ-002 trước code, gồm chốt người cấp grant Q2 và hồ sơ nghiệm thu; CTR-002 draft trên test chỉ sau người dùng quyết định chuyển giai đoạn.

- `odoo/` và `addons/` giữ layout upstream.
- `custom_addons/` dành cho backend riêng.
- `frontend/` là app React/TypeScript/Vite gọi API thật; `frontend/prototype/` giữ dashboard mẫu cũ.
- `contracts/openapi/` dành cho hợp đồng API.
- Phân chia addon theo nghiệp vụ, workspace frontend theo nhu cầu phòng ban.

Các tài liệu `docs/dashboard/` giữ giá trị khảo sát dữ liệu và prototype. Phương án OWL client action trong các tài liệu đó là định hướng cũ cho phạm vi dashboard, đã được thay bằng thiết kế hiện hành cho toàn nền tảng.

Vertical slice nền đầu tiên có addon cài được (`tp_core`, `tp_organization`, `tp_project`, `tp_contract`, `tp_api`, `tp_planning_api`) và app React đọc dự án, hợp đồng trên database dev. Login React riêng dùng session Odoo, native MFA fallback, phân quyền, search/detail, logout/session hết hạn đã có browser tests. TP Contracts chỉ đọc: hợp đồng, revision, phạm vi, kết quả BASE và tài liệu; số tiền theo grant `financial_read` từng project (DEC-017). Chưa triển khai production, ghi/duyệt hợp đồng, giao khoán/nghiệm thu, import Excel hoặc dữ liệu doanh nghiệp thật.

Thiết kế database: [TP_DATABASE_DESIGN.md](TP_DATABASE_DESIGN.md). Cách chạy nền: [LOCAL_DEVELOPMENT.md](../../ops/runbooks/LOCAL_DEVELOPMENT.md).

Data Platform đang ở giai đoạn discovery: [kế hoạch chuẩn bị](TP_DATA_PLATFORM_PREPARATION_PLAN.md), [DP-001 discovery](TP_DATA_PLATFORM_DISCOVERY.md) và [kết quả audit/re-audit](TP_DATA_PLATFORM_DP001_AUDIT.md). Re-audit CHG-027 đã `TECHNICAL_ACCEPTED` cho discovery/spec-only; recommendation `DEFER` vẫn chưa là DEC và chưa có lake, analytics store, connector hoặc pipeline.

Ưu tiên hiện tại là dùng [kế hoạch điều phối giai đoạn lập trình](TP_CODE_EXECUTION_MASTER_PLAN.md) để tách test-only maintenance khỏi cổng pilot. [BIZ-002 — bộ thiết kế toàn công ty](TP_BIZ002_DESIGN_PACKAGE.md) vẫn liên kết bản đồ A–M, RACI, hai bộ workflow, dữ liệu/quyền, tích hợp/KPI và kịch bản/readiness; Proposed/Unconfirmed theo từng phần, chưa phải quy chế hoặc runtime.
