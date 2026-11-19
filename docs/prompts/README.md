# TANPHAT ONE — Danh mục Prompt và Kho lưu trữ

**Cập nhật:** 18/11/2026 (thêm ADMIN-DELEGATE-002; metadata kho SOURCE-CLEANUP-001 giữ nguyên)
**Kho lưu trữ an toàn ngoài source:** `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934\docs\prompts`  
**File mapping khôi phục:** `C:\TANPHAT ONE ARCHIVE\SOURCE-CLEANUP-001\20261112T194934\recovery-mapping.json`

Thư mục này quản lý các prompt giao việc cho các phiên AI thực thi (Claude/Codex). Theo quy tắc dọn dẹp source:
- Các prompt đang hoạt động hoặc chuẩn bị cho các bước tiếp theo được giữ trực tiếp trong thư mục này.
- Các prompt của các task đã hoàn thành, đã kiểm thử và bàn giao vào hệ thống chính thức được lưu trữ an toàn trong kho lưu trữ ngoài source và được lập chỉ mục tại tài liệu này để tra cứu khi cần.

---

## 1. Prompt đang hiệu lực trong thư mục source

**HR-LOGIN-RENAME-001 — 19/11/2026:** [Đổi tên đăng nhập nhân viên](CLAUDE_HR_LOGIN_RENAME_001_EMPLOYEE_LOGIN.md). CHG013/014 triển khai gốc; CHG016/017 sửa nút bị ẩn khi admin gốc xem admin được cấp và đã áp local18069/PC server, app cf4cf114, HR20.0.1.15.1/admin20.0.2.0.3. [Cách dùng và kiểm chứng](../demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md). Prompt009 là lịch sử điều phối.

**Yêu cầu mới18/11 — MATRIX003:** dùng prompt003 để hoàn thiện xem bảng theo file và đối chiếu trước tổng hợp. SIMPLE002 đã giao20.0.2.0.0/CHG-019; không chạy lại002. Các trạng thái PROMPT_READY của002 bên dưới là mốc lịch sử chưa cập nhật runtime, xem [bàn giao mới](../demo/HR_ATTENDANCE_SIMPLE_002_ACCEPTANCE.md).



**Cập nhậtExcel CHG-20261118-013:** người dùng chưa chạy bản cũ; giao cùng HR-ATTENDANCE-SIMPLE-002 đã hợp nhất tải Excel máy→tự tạo bảng,08:30–17:00 và giữ tổng Đi muộn/Lần/Phút nguyên nguồn đúng kỳ.

**Chấm công từ18/11/2026:** dùng HR-ATTENDANCE-SIMPLE-002 cho UI gọn và API-ready; giữ nguồn Excel/backend hiện có, không chạy lại prompt001 để mở lại scope phức tạp.

**Quyền admin từ18/11/2026:** dùng ADMIN-FULL-001 theo DEC-053/054. Chỉ admin gốc cấp/thu admin. Các prompt
ADMIN-DELEGATE-001/002 giữ lịch sử; không áp lại giới hạn phòng mình cũ.

**Kho thiết bị:** dùng EQUIP-SIMPLE-003 cho yêu cầu UI/thao tác hiện hành.
EQUIP-UI-001/002 bên dưới giữ để tra cứu lịch sử, không giao chạy lại giao diện cũ.

| Tệp prompt | Nhiệm vụ | Mô tả | Trạng thái | Tài liệu đặc tả / Kế hoạch |
| --- | --- | --- | --- | --- |
| [`CLAUDE_HR_ATTENDANCE_MATRIX_003_FILE_COMPARISON.md`](CLAUDE_HR_ATTENDANCE_MATRIX_003_FILE_COMPARISON.md) | **HR-ATTENDANCE-MATRIX-003** | Bảng công ma trận theo file; nhiều file độc lập, đối chiếu A/B trước tổng hợp | `PROMPT_READY_NOT_IMPLEMENTED` CHG-20261118-021 | DEC-058; source đủ người/blank, filter/pager; giữ giờ/tổng Excel đúng kỳ, không đếm đôi, quyền/correction/kỳ chốt; kế thừa SIMPLE002 đã giao |

| [`CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md`](CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md) | **AUTH-SESSION-001** | Một phiên/tài khoản; login mới thay cũ, thông báo và Đăng nhập lại về Trang chủ | `PROMPT_READY_NOT_IMPLEMENTED` CHG-20261118-016 | DEC-057; native auth/MFA/winner/backend/bus/fallback; giữ HR lock/admin/quyền, chưa thu hồi phiên thật |
| [`CLAUDE_HR_ATTENDANCE_SIMPLE_002_DASHBOARD_AND_API_READY.md`](CLAUDE_HR_ATTENDANCE_SIMPLE_002_DASHBOARD_AND_API_READY.md) | **HR-ATTENDANCE-SIMPLE-002** | Upload Excel máy tự lập bảng gọn; giữ tổngmuộn theo kỳ, Ngày/Tuần/Tháng và API-ready | `PROMPT_READY_NOT_IMPLEMENTED` CHG-20261118-011/013 | DEC-055/056;08:30–17:00, nguồnLần/Phút không tựtính/khôngchiangày/cộngchồng; sharedHR/DB, rollout18069/PCserver |
| [`CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md`](CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md) | **ADMIN-FULL-001** | Người được cấp admin có toàn quyền như admin hiện tại, kể cả phòng mình; chỉ admin gốc cấp/thu admin; chuyển grant hiện hiệu lực và thu hồi đúng | `POLICY_CONFIRMED_PROMPT_READY_NOT_IMPLEMENTED` CHG-20261118-009/010 | DEC-053/054 thay giới hạn DEC-050; giữ native/workflow/quyền người thường; push/deploy18069/PCserver, không bắt18079; lượt viết prompt chưa migration |
| [`CLAUDE_ADMIN_DELEGATE_002_COMPLETE_SCOPED_ADMIN.md`](CLAUDE_ADMIN_DELEGATE_002_COMPLETE_SCOPED_ADMIN.md) | **ADMIN-DELEGATE-002** | Hoàn thiện quản trị ngoài phòng, giữ baseline tại phòng mình; HR/Kho dashboard, CRUD theo nguồn và Reporting admin baseline | `AUDITED_PARTIAL_PROMPT_READY` CHG-20261118-001 | Server có1delegation hiệu lực; [audit chỉ đọc](../security/ADMIN_DELEGATE_002_READONLY_AUDIT.md); push/deploy18069/PCserver từng slice, không bắt18079, không tự grant/revoke người thật |
| [`CLAUDE_ADMIN_DELEGATE_001_AND_PUBLIC_FILES.md`](CLAUDE_ADMIN_DELEGATE_001_AND_PUBLIC_FILES.md) | **ADMIN-DELEGATE-001 / DEPLOY-MEDIA-001** | Lịch sử triển khai delegation/media; không chạy lại để hoàn thiện quyền | `APPLIED_WITH_GAPS; CONTINUE_002` | [Acceptance001](../demo/ADMIN_DELEGATE_001_ACCEPTANCE.md); bản runtime20.0.1.0.1, server đã có1grant hiệu lực tại audit17/11; dùng prompt002 cho sửa tiếp, policy17/11 thay yêu cầu test18079 cũ |
| [`CLAUDE_CORP_REPORT_001_FULL_MODULE.md`](CLAUDE_CORP_REPORT_001_FULL_MODULE.md) | **CORP-REPORT-001** | Full quý→tháng→tuần và báo cáo ngược; dashboard sáng/chart lớn, UI/filter/detail/mobile mọi tab, nguồn/quyền/version, chỉ đạo và Excel/Word/PDF | `FULL_MODULE_PROMPT_READY_NOT_IMPLEMENTED` CHG-20261116-006 | [Thiết kế](../architecture/TP_COMPANY_REPORTING_001_DESIGN.md), DEC-048; R0–R5 trên18079, cấu hình lịch/role test, không grant/nhập thật/main/commit/push. Đối chiếu baseline workflow FAIL trước code; không finish hộ source chưa kiểm |
| [`CLAUDE_EQUIP_SIMPLE_003.md`](CLAUDE_EQUIP_SIMPLE_003.md) | **EQUIP-SIMPLE-003** | Hai menu Thiết bị/Yêu cầu đề xuất; gán/đổi chỉ máy stock chưa có người giữ; trả kho, bỏ tab dư/chuyển trực tiếp | `IMPLEMENTED_RUNTIME_OBSERVED_MAIN_PENDING_ADMIN_FLOW_CHECK` CHG-20261116-003 (prompt CHG-20261116-001/002) | Đã áp main18069 `tp_equipment` 20.0.1.5.0; mức bằng chứng ở [acceptance](../demo/EQUIP_001_ACCEPTANCE.md). DEC-047 bổ sung trước code: cấm chọn máy có chủ/cấm đổi chéo, backend kiểm lại sau khóa; cùng DB/HR/admin-only/data/history; main18069 sau backup, không18079/bộ test riêng/fixture |
| [`CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md`](CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md) | **EQUIP-UI-002 / UI-BACK-001** | Bảng thiết bị gắn HR/người dùng, stock riêng; Quay lại dùng chung toàn hệ thống; nâng dashboard theo phản hồi | `IMPLEMENTED_RUNTIME_VERIFIED_MAIN_PENDING_VISUAL_REVIEW` CHG-20261115-002 (prompt CHG-20261115-001) | DEC-045/046; [chuẩn Quay lại](../ui/UI_BACK_001_STANDARD.md), [acceptance](../demo/EQUIP_001_ACCEPTANCE.md); main18069 sau backup; dữ liệu/HR/quyền giữ |
| [`CLAUDE_EQUIP_UI_001_SIMPLIFY_AND_REDESIGN.md`](CLAUDE_EQUIP_UI_001_SIMPLIFY_AND_REDESIGN.md) | **EQUIP-UI-001** | Dashboard sáng/nhiều màu/chart lớn ở đầu, sidebar4mục, bảng/filter/detail gọn theo thiết bị/tồn/đề xuất; giữ data/admin-only | `PROMPT_READY_UI_NOT_IMPLEMENTED` CHG-20261114-013 | Wireframe/palette/responsive/scope trong prompt; [DEC-045](../DECISIONS.md), [chuẩn filter](../ui/TP_TABLE_FILTER_STANDARD.md); main18069 sau backup, không18079/bộ test |
| [`CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md`](CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md) | **EQUIP-DATA-001** | Nhập thật hai workbook local lên18069 sau backup; bổ sung mapping còn thiếu; apply/đăng ký/hiển thị, đề xuất không thành tồn | `PROMPT_READY_REAL_IMPORT_AUTHORIZED_NOT_EXECUTED` CHG-20261114-011 | [Runbook](../../ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md), phân tích nguồn private `.local/equipment001/`; giữ admin-only/DB và HR chung, không18079/bộ test |
| [`CLAUDE_EQUIP_001_OFFICE_EQUIPMENT.md`](CLAUDE_EQUIP_001_OFFICE_EQUIPMENT.md) | **EQUIP-001** | Codex hoàn tất Claude dở; module20.0.1.1.0 chạy18069 sau backup; không suites/18079/nhập thật | `SOURCE_IMPLEMENTED_RUNTIME_OBSERVED_EMPTY` CHG-20261114-010 | [Blueprint](../architecture/TP_EQUIPMENT001_BLUEPRINT.md), [acceptance và giới hạn](../demo/EQUIP_001_ACCEPTANCE.md), [hướng dẫn](../demo/EQUIP_001_USER_GUIDE.md), [runbook](../../ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md); giữ prompt để đối chiếu scope |
| [`CLAUDE_UI_TABLE_FILTER_001.md`](CLAUDE_UI_TABLE_FILTER_001.md) | **UI-TABLE-FILTER-001** | Bộ lọc đúng nội dung cho mọi bảng HR/KH-KD/native và checklist phòng ban mới; test 18079, không tự áp main | `IMPLEMENTED_VERIFIED_TEST_ONLY` CHG-20261114-008 | [Nghiệm thu](../demo/UI_TABLE_FILTER_001_ACCEPTANCE.md), [hướng dẫn](../demo/UI_TABLE_FILTER_001_USER_GUIDE.md), [inventory](../ui/TP_TABLE_FILTER_INVENTORY.md), [runbook](../../ops/runbooks/UI_TABLE_FILTER_001_DEPLOY_AND_ROLLBACK.md) |
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
