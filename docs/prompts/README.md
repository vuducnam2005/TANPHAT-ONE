# TANPHAT ONE — Danh mục Prompt và Kho lưu trữ

**Cập nhật:** 12/11/2026 (Task SOURCE-CLEANUP-001)  
**Kho lưu trữ an toàn ngoài source:** `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934\docs\prompts`  
**File mapping khôi phục:** `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934\recovery-mapping.json`

Thư mục này quản lý các prompt giao việc cho các phiên AI thực thi (Claude/Codex). Theo quy tắc dọn dẹp source:
- Các prompt đang hoạt động hoặc chuẩn bị cho các bước tiếp theo được giữ trực tiếp trong thư mục này.
- Các prompt của các task đã hoàn thành, đã kiểm thử và bàn giao vào hệ thống chính thức được lưu trữ an toàn trong kho lưu trữ ngoài source và được lập chỉ mục tại tài liệu này để tra cứu khi cần.

---

## 1. Prompt đang hiệu lực trong thư mục source

| Tệp prompt | Nhiệm vụ | Mô tả | Trạng thái | Tài liệu đặc tả / Kế hoạch |
| --- | --- | --- | --- | --- |
| [`CLAUDE_C01_ISOLATED_TEST_RUNTIME.md`](CLAUDE_C01_ISOLATED_TEST_RUNTIME.md) | **FND-002 / C01** | Thiết lập môi trường kiểm thử cô lập tái lập được | `READY_FOR_TEST_CODE` | [Kế hoạch thực thi](../architecture/TP_CODE_EXECUTION_MASTER_PLAN.md), [Quy trình điều phối](../AI_COORDINATION_WORKFLOW.md) |
| [`CLAUDE_KD_REPORT_UI_002_IMPLEMENT.md`](CLAUDE_KD_REPORT_UI_002_IMPLEMENT.md) | **KD-REPORT-UI-002** | Triển khai thiết kế lại 6 báo cáo KH-KD (S0–S5) | `DESIGN_PREVIEW_READY_PENDING_USER_REVIEW` | [Kế hoạch thiết kế lại](../ui/KD_REPORT_UI_002_REDESIGN_PLAN.md) |

---

## 2. Chỉ mục các Prompt đã hoàn thành (Lưu trữ an toàn)

Tất cả 35 prompt dưới đây đã hoàn thành mục tiêu, có tài liệu nghiệm thu (Acceptance), hướng dẫn sử dụng (User Guide) hoặc báo cáo kiểm thử tương ứng. Bản gốc từng tệp được lưu trữ tại `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934\docs\prompts\`.

| Tệp prompt | Mã nhiệm vụ | Tiêu đề / Nội dung chính | Trạng thái hoàn thành | Tài liệu nghiệm thu / Bàn giao |
| --- | --- | --- | --- | --- |
| `CLAUDE_AUTH002_S1_REACT_LOGIN.md` | AUTH-002 Slice 1 | Thông báo đăng nhập trên React | `TECHNICAL_ACCEPTED` | [Đặc tả Login](../architecture/TP_AUTH002_LOGIN_SPEC.md) |
| `CLAUDE_AUTH002_S2_NATIVE_LOGIN.md` | AUTH-002 Slice 2 | Trang xác thực native và handoff 2FA | `IMPLEMENTED_PENDING_AUDIT` | [Đặc tả Login](../architecture/TP_AUTH002_LOGIN_SPEC.md) |
| `CLAUDE_DATA_PLATFORM_DISCOVERY.md` | DP-001 | Chuẩn bị Data Platform / Data Lake | `TECHNICAL_ACCEPTED` | [Discovery DP-001](../architecture/TP_DATA_PLATFORM_DISCOVERY.md) |
| `CLAUDE_DP001_CORRECTION.md` | DP-001 Correction | Sửa đặc tả DP-001 sau audit | `TECHNICAL_ACCEPTED` | [Audit DP-001](../architecture/TP_DATA_PLATFORM_DP001_AUDIT.md) |
| `CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md` | HR-001 | Dữ liệu nhân sự thật, mã TP và workspace native | `IMPLEMENTED_VERIFIED_MAIN_APPLIED` | [Nghiệm thu HR-001](../demo/HR_001_ACCEPTANCE.md) |
| `CLAUDE_HR_DASH_001_OVERVIEW_REDESIGN.md` | HR-DASH-001 | Viết lại dashboard Quản lý nhân sự | `IMPLEMENTED_VERIFIED_MAIN_APPLIED` | [Hướng dẫn HR-DASH-001](../demo/HR_DASH_001_USER_GUIDE.md) |
| `CLAUDE_HR_UI_002_EMPLOYEE_PROFILE_ACCOUNTS.md` | HR-UI-002 | Hồ sơ nhân viên, tài khoản liên kết và reset mật khẩu | `IMPLEMENTED_VERIFIED_MAIN_APPLIED` | [Nghiệm thu HR-UI-002](../demo/HR_UI_002_ACCEPTANCE.md) |
| `CLAUDE_KD_ACCESS_001_STAFF_ACCOUNTS.md` | KD-ACCESS-001 | Tài khoản và quyền riêng cho 5 vai trò KH-KD | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-ACCESS-001](../demo/KD_ACCESS_001_ACCEPTANCE.md) |
| `CLAUDE_KD_ACCESS_002_COMPLETE_ROLE_PERMISSIONS.md` | KD-ACCESS-002 | Hoàn thiện quyền của toàn bộ tài khoản KH-KD | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-ACCESS-002](../demo/KD_ACCESS_002_ACCEPTANCE.md) |
| `CLAUDE_KD_ACCESS_002_SECURITY_CORRECTION.md` | KD-ACCESS-002 Correction | Sửa bảo mật quyền 5 vai KH-KD | `CORRECTION_VERIFIED_DEV_SCOPE_ONLY` | [Nghiệm thu KD-ACCESS-002](../demo/KD_ACCESS_002_ACCEPTANCE.md) |
| `CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md` | KD-HEAD-001 | Thuỳ Anh quản lý nghiệp vụ toàn scope KH-KD | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-HEAD-001](../demo/KD_HEAD_001_ACCEPTANCE.md) |
| `CLAUDE_KD_PROJECT_RESTRUCTURE_001.md` | KD-PROJECT-RESTRUCTURE-001 | Tách Quản lý/Quản trị dự án | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Restructure](../demo/KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md) |
| `CLAUDE_KD_REPORT_001_SEPARATE_REPORT_CENTER.md` | KD-REPORT-001 | Tách Báo cáo KH-KD thành phân hệ riêng biệt | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Báo cáo](../demo/KD_REPORT_001_ACCEPTANCE.md) |
| `CLAUDE_KD_REPORT_UI_002_PLAN.md` | KD-REPORT-UI-002 Plan | Kế hoạch thiết kế lại 6 báo cáo KH-KD | `COMPLETED_PLAN_PHASE` | [Kế hoạch Báo cáo](../ui/KD_REPORT_UI_002_REDESIGN_PLAN.md) |
| `CLAUDE_KD_SCOPED_PROJECT_TASK_FOLLOWUP.md` | KD-SCOPED-TASK | Phân công công việc dự án theo quyền | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Restructure](../demo/KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md) |
| `CLAUDE_KD_UI_002_SIDEBAR_POLISH.md` | KD-UI-002 | Sidebar và Tổng quan KH-KD có biểu đồ/bảng | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-UI-002](../demo/KD_UI_002_ACCEPTANCE.md) |
| `CLAUDE_KD_UI_003_TABLES_AND_DETAILS.md` | KD-UI-003 | Chuẩn hóa bảng viền và form chi tiết KH-KD | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-UI-003](../demo/KD_UI_003_ACCEPTANCE.md) |
| `CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md` | KD-UI-004 | Làm lại Tổng quan: vòng khuyên, số liệu rõ | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-UI-004](../demo/KD_UI_004_ACCEPTANCE.md) |
| `CLAUDE_KD_UI_005_BUSINESS_PROJECT.md` | KD-UI-005 | Bốn màn Kinh doanh và dự án | `TECHNICALLY_VERIFIED` | [Nghiệm thu KD-UI-005](../demo/KD_UI_005_ACCEPTANCE.md) |
| `CLAUDE_KD_UI_007_ALL_TABLES_FILTERS_STATUS.md` | KD-UI-007 | Toàn bộ bảng KH-KD: bộ lọc, phân trang, trạng thái | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu KD-UI-007](../demo/KD_UI_007_ACCEPTANCE.md) |
| `CLAUDE_NATIVE_DATA002_AND_VI001_COMPLETE_DEMO.md` | NATIVE-DATA-002 / VI-001 | Dữ liệu demo và Việt hóa nhãn | `IMPLEMENTED_VERIFIED_DEV` | [Báo cáo Việt hóa](../i18n/VI_GLOSSARY_AND_COVERAGE.md) |
| `CLAUDE_NATIVE_DATA003_CONNECTED_OPERATIONS.md` | NATIVE-DATA-003 | Bộ dữ liệu mẫu liên thông theo quy trình | `PARTIAL_WITH_GAPS` | [Runbook DATA-003](../demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md) |
| `CLAUDE_NATIVE_STABILIZE_001_CORRECTION.md` | NATIVE-STABILIZE-001 | Khắc phục nền Odoo native | `SPEC_CORRECTION_ACCEPTED` | [Correction Audit](../reviews/NATIVE_STABILIZE_001_CORRECTION.md) |
| `CLAUDE_NATIVE_STABILIZE_001_DELTA_CORRECTION.md` | NATIVE-STABILIZE-001 Delta | Delta correction cho native stabilize | `DELTA_CORRECTION_ACCEPTED` | [Delta Audit](../reviews/NATIVE_STABILIZE_001_DELTA_AUDIT.md) |
| `CLAUDE_TODO001_NATIVE_PRIVATE_TASK_FIX_AND_SAMPLE.md` | TODO-001 | Private task fix and sample data | `IMPLEMENTED_VERIFIED_DEV` | [Runbook DATA-003](../demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md) |
| `CLAUDE_UI001_NATIVE_ODOO_DEMO.md` | UI-DEMO-001 | Khung trình diễn native Odoo toàn hệ thống | `RUNTIME_RETIRED_ARCHIVED` | [Handoff Demo 002](../demo/UI_DEMO_002_HANDOFF.md) |
| `CLAUDE_UI002_DEMO_NAVIGATION.md` | UI-DEMO-002 | Điều hướng demo dễ hiểu theo quyền | `RUNTIME_RETIRED_ARCHIVED` | [Handoff Demo 002](../demo/UI_DEMO_002_HANDOFF.md) |
| `CLAUDE_UI_CTR_NATIVE_001A.md` | UI-CTR-NATIVE-001 | Giao diện native TP Contracts tái sử dụng | `TECHNICAL_ACCEPTED_TEST_ONLY` | [Audit Hợp đồng](../reviews/UI_CTR_NATIVE_001A_IMPLEMENTATION.md) |
| `CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md` | UI-HOME-001 | Home native TANPHAT ONE dạng lưới ứng dụng | `IMPLEMENTED_PENDING_AUDIT` | [Runbook Home 001](../demo/UI_HOME_001_RUNBOOK.md) |
| `CLAUDE_UI_HOME_002_WORKSPACE_ORGANIZATION.md` | UI-HOME-002 | Trang chủ theo workspace, cá nhân, quản trị | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Home 002](../demo/UI_HOME_002_ACCEPTANCE.md) |
| `CLAUDE_UI_HOME_003_KD_FIRST.md` | UI-HOME-003 | Trang chủ logic, ưu tiên hoàn thành KH-KD | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Home 003](../demo/UI_HOME_003_ACCEPTANCE.md) |
| `CLAUDE_UI_HOME_004_ADMIN_ONLY.md` | UI-HOME-004 Admin | Home admin đúng 7 mục | `VERIFIED_DEV_APPLIED` | [Nghiệm thu Home 004](../demo/UI_HOME_004_ACCEPTANCE.md) |
| `CLAUDE_UI_HOME_004_DEPARTMENTS_HR_RECRUITMENT.md` | UI-HOME-004 Depts | Trang chủ đầy đủ phòng/ban (đã thay thế) | `SUPERSEDED_BY_DEC-036` | [Nghiệm thu Home 004](../demo/UI_HOME_004_ACCEPTANCE.md) |
| `CLAUDE_UI_HOME_004_SHELL_ICON_CORRECTION.md` | UI-HOME-004 Icons | Một navbar, đủ công cụ, đúng icon | `VERIFIED_DEV_APPLIED` | [Nghiệm thu Home 004](../demo/UI_HOME_004_ACCEPTANCE.md) |
| `CLAUDE_UI_SHELL_AUTH_001_NAVBAR_LOGIN_LOGOUT.md` | UI-SHELL-AUTH-001 | Navbar toàn hệ thống và login/logout native | `IMPLEMENTED_VERIFIED_DEV` | [Nghiệm thu Shell Auth](../demo/UI_SHELL_AUTH_001_ACCEPTANCE.md) |
