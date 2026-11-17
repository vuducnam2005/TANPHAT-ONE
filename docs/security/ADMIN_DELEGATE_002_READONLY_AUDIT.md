# ADMIN-DELEGATE-002 — Rà soát quyền quản trị được ủy quyền

CHG-20261118-001. Kiểm runtime bắt đầu 17/11/2026, lập bàn giao 18/11/2026
(Asia/Saigon). Đây là kiểm chỉ đọc và đối chiếu source; chưa sửa ứng dụng.

**Kết luận: quyền ủy quyền đã có hiệu lực trên PC server, nhưng chưa đủ khả
năng quản trị nghiệp vụ ngoài phòng như yêu cầu.** Không được diễn giải thành
chưa có ai được cấp quyền. Tình trạng ledger 0/0 trong bàn giao trước là lịch sử.

## 1. Nguồn và cách kiểm

- Đọc policy, coverage, acceptance ADMIN-DELEGATE-001 và source đang chạy.
- Đăng nhập admin qua RPC local18069 và public HTTPS để đọc module/ledger.
  Đăng nhập máy chủ qua origin public, không dùng host LAN để tránh đổi baseURL.
- Docker PC server: Odoo shell trên đúng database, transaction
  `SET TRANSACTION READ ONLY`, dùng `with_user` tài khoản thực đang được cấp và
  admin chính; cuối lượt rollback. Không gọi mutation nghiệp vụ hoặc grant/revoke.
- So sánh 27 tệp của addon delegation và các helper liên quan với máy chủ:
  không có chênh lệch nội dung sau chuẩn hóa xuống dòng.
- Evidence ignored: `.local/admin-delegate-audit-20261117/`, gồm
  `runtime-readonly.json`, `server-actor-readonly.json`,
  `server-main-compare.json`, `source-compare.json`. Danh tính thật/cookie/secret
  không đưa vào Git. Skill rà soát không thay bằng chứng runtime.

Không thử đăng nhập bằng mật khẩu của người nhận quyền, không thử create/write/
delete, không cấp hoặc thu quyền, không chạy fixture trên main/server/test18079.
Kết quả `has_access` cấp model không chứng minh mutation trên record cụ thể;
wizard nghiệp vụ có thể cung cấp đường ghi khác. Không dùng count bằng 0 làm
bằng chứng thiếu quyền nếu chưa có hồ sơ phù hợp.

## 2. Trạng thái thực tế

| Mục | Local18069 | PC server/public |
| --- | --- | --- |
| `tp_admin_delegation` | installed20.0.1.0.1 | installed20.0.1.0.1 |
| `tp_hr_workspace` | installed20.0.1.12.0 | installed20.0.1.12.0 |
| `tp_hr_attendance` | installed20.0.1.2.0 | installed20.0.1.2.0 |
| Ledger tổng / hiệu lực | 0 / 0 | 1 / 1 |
| Người dùng gồm inactive / nhân viên | 28 / 39 | 29 / 39 |

Actor thực trên server đang hoạt động, có hồ sơ nhân viên ở TADIC. Capability
trả `level=delegated`, `delegated=true`, `can_manage_delegation=false`;
scope phòng được xác định đầy đủ. Không có nhóm system/HR user/HR manager.
Không hardcode actor hoặc ID này trong implementation/policy.

## 3. Kết quả và ý nghĩa

| Kiểm thực | Tài khoản ủy quyền | Admin chính | Kết luận |
| --- | --- | --- | --- |
| `tp.hr.workspace.get_overview()` | AccessError: chỉ nhân sự được giao | Thành công | Tổng quan HR chưa có đường quản trị ngoài phòng cho delegate. |
| `tp.equipment.dashboard.get_dashboard()` | AccessError Kho | Thành công | Menu Kho không đồng nghĩa mở được Tổng quan Kho. |
| `maintenance.equipment.tp_main_summary()` | AccessError Kho | Thành công | Luồng thiết bị đơn giản vẫn bị cổng admin toàn cục chặn. |
| Đọc `tp.equipment.proposal` | AccessError | Không kiểm ở lượt này | Đề xuất thiết bị chưa được mở cho delegate; source giữ baseline. |
| `tp.report.dashboard.get_data()` kỳ tháng11/2026 | AccessError ở obligation | AccessError ở document | Báo cáo còn thiếu coverage delegate và lỗi baseline admin riêng. Không gọi đây chỉ là lỗi delegate. |
| `hr.employee.get_view(view_type='list')` | Trả arch/models thành công | Không so sánh | Chưa kiểm renderer/browser; không còn đủ căn cứ gọi lỗi ListArchParser cũ là lỗi hiện hành. |
| Menu backend | Có HR/KH-KD/Báo cáo/Kho; không Settings/Apps | Bộ menu admin hiện hành | Chặn Settings/Apps là có chủ ý; không phải lỗi cần mở. |

Actor đọc được35 nhân viên/24 thiết bị/1 dự án/3 task/252 ngày công; admin chính
đọc39 nhân viên/55 thiết bị/1 dự án. Chênh lệch có thể đúng scope phòng mình,
nguồn chung hoặc quyền gốc; không đặt tiêu chí hai bên phải cùng count.

Source xác nhận các giới hạn chưa đáp ứng quản trị nghiệp vụ ngoài phòng:

- `business_scope.Project/Task/Opportunity._access_domain` chỉ cộng quyền đọc;
  Project/CRM CUD không được cộng theo scope. Contract có adapter wizard riêng,
  vì vậy không suy rằng false ở native create đồng nghĩa mọi đường lập hợp đồng đều hỏng.
- `ReportScope` chỉ mở đọc một số report/plan/line đơn giản, chưa có quản trị
  kế hoạch, nghĩa vụ, tổng hợp, snapshot và workflow ngoài phòng đầy đủ.
- Kho chỉ mở thiết bị có người/phòng giữ được chứng minh ngoài phòng; stock,
  proposal và quick assign/swap/return vẫn giữ baseline. Chưa có policy nguồn
  dùng chung để xử lý kho an toàn mà không tăng quyền tại phòng actor.
- HR có wizard metadata/account ngoài phòng, không phải toàn bộ CRUD hồ sơ.
  Trường riêng tư, chức vụ/phòng ban và security vẫn có ranh giới riêng.
- Chấm công252 ngày có thể đọc theo quyền danh bạ hiện hành. Actor không có
  assignment import/review/lock; đây không tự động là lỗi vì phân công duyệt/chốt
  và cấm tự duyệt là workflow đã chốt, không phải quyền suy từ chữ admin.

Nguồn: [coverage](ADMIN_DELEGATE_001_COVERAGE.md),
[policy](ADMIN_DELEGATE_001_POLICY.md),
[business adapter](../../custom_addons/tp_admin_delegation/models/business_scope.py),
[navigation](../../custom_addons/tp_admin_delegation/models/navigation.py),
[Kho guard](../../custom_addons/tp_equipment/models/common.py),
[HR dashboard](../../custom_addons/tp_hr_workspace/models/hr_workspace.py),
[report dashboard](../../custom_addons/tp_reporting/models/dashboard.py).

## 4. Phần chưa xác minh và bước tiếp

Chưa thử CRUD/duyệt/chốt/file/export bằng phiên HTTP của actor thật, chưa cấp/
thu hồi cùng cookie, chưa kiểm nhiều worker hoặc browser HR bản cuối. Các test
cũ trong acceptance001 chỉ có hiệu lực cho source/fixture/lát cắt đã ghi.
Subagent rà soát không khởi tạo được do model runtime; không gọi đây là audit
độc lập nhiều người. Không mở hoặc tải tài liệu HR riêng để làm evidence.

Giao [prompt ADMIN-DELEGATE-002](../prompts/CLAUDE_ADMIN_DELEGATE_002_COMPLETE_SCOPED_ADMIN.md)
để hoàn thiện theo model/action, xử lý Reporting admin baseline riêng, bảo toàn
phòng mình/quyền gốc và thu hồi. Prompt không tự chỉ định thêm người nhận quyền;
không sửa grant người thật hiện có để thử. Phiên này chỉ giao tài liệu, không
khẳng định các gap đã được sửa hoặc đã nghiệm thu.
