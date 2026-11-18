# HR-DELEGATE-FIX-001 — Nghiệm thu sửa lỗi mở danh sách và chi tiết nhân viên bằng tài khoản ủy quyền

Ngày lập: 18/11/2026 (Asia/Saigon) — **lập trước khi sửa application code**, cập nhật bằng chứng sau khi kiểm thực trên `18069` và PC server / URL public.

Liên quan:
- [Audit chỉ đọc ADMIN-DELEGATE-002](../security/ADMIN_DELEGATE_002_READONLY_AUDIT.md) (§5 — CHG-20261118-006)
- [Acceptance ADMIN-DELEGATE-002](ADMIN_DELEGATE_002_ACCEPTANCE.md)
- [Quy trình giao bản liên tục](../operations/TP_CONTINUOUS_DELIVERY_POLICY.md)

## 1. Tóm tắt nguyên nhân gốc và phạm vi sửa

- **Triệu chứng trên PC server / URL public:** Tài khoản quản trị được ủy quyền (ledger hiệu lực, không thuộc `hr.group_hr_user`) mở **Nhân sự → Danh sách nhân viên** gặp lỗi trình duyệt `UncaughtPromiseError: "hr.employee"."mobile_phone" field is undefined` tại `ListArchParser`.
- **Nguyên nhân kỹ thuật:**
  1. `tp_hr_attendance/models/directory_privacy.py` giới hạn `mobile_phone` (cùng `mobile_phone_sanitized`, `mobile_phone_formatted`, `phone`, `phone_sanitized`, `phone_formatted`, `email`) cho `hr.group_hr_user`.
  2. `tp_admin_delegation/views/hr_profile.xml` (`delegated_employee_list`, `delegated_employee_form`) vẫn khai báo `<field name="mobile_phone" .../>` mà không có `groups` trên node, dẫn đến `get_views` trả XML có trường `mobile_phone` nhưng `models['hr.employee']['fields']` không có metadata.
  3. Các đường liên quan cần khóa đồng bộ để không phát sinh lỗi kế tiếp hoặc rò rỉ/mất dữ liệu:
     - Wizard `tp.hr.delegated.profile.wizard` (`ScopedHrProfile` + `delegated_hr_profile_form`): trường `mobile_phone` chưa gắn `groups='hr.group_hr_user'`, `create()` chép `source['mobile_phone']` qua `sudo()`, và `action_apply()` gom toàn bộ `PROFILE_FIELDS` có nguy cơ chặn lỗi hoặc gửi `False` ghi đè mất `mobile_phone` hiện có trên hồ sơ nhân viên.
     - Guard `ProtectedEmployee` (`guards.py`): cần chặn ghi hoặc truyền `default_<field>` context cho trường `hr.employee` bị hạn chế field-group trên hồ sơ người khác ngay cả khi đi qua `sudo()`, nhưng vẫn giữ nguyên cập nhật hồ sơ cá nhân (`tp_save_my_profile`) của chính actor.
     - Tổng quan HR ủy quyền (`hr_overview.py` + `overview.js`): `PROJECTION_FIELDS` còn chứa `mobile_phone` (cho phép dò qua RPC `action_employees`), và mục `missing_contact` đếm/drill-down cả `mobile_phone` gây lệch hoặc lỗi `ValidationError` khi bấm từ giao diện delegate.

## 2. Tiêu chí nghiệm thu (lập trước khi sửa)

Phân tách rõ: **Kiểm kỹ thuật (ORM/tĩnh)**, **Kiểm trình duyệt (Playwright)**, **Nghiệm thu hình thức người dùng**, **Nghiệm thu nghiệp vụ** và **Cho phép pilot**. Không dùng kết quả `get_view` đơn lẻ làm bằng chứng giao diện trình duyệt đã chạy.

| Mã | Actor | Môi trường | Đầu vào / Thao tác | Kết quả kỳ vọng | Trạng thái | Bằng chứng / Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| HDF-01 | Delegate thực (ledger 1/1, không `hr.group_hr_user`) | PC server (`SET TRANSACTION READ ONLY` + `with_user`, rollback) | Gọi `get_views` cho `hr.employee` (`list`, `form`, `search`, `hierarchy`), `tp.hr.delegated.profile.wizard` (`form`), `tp.hr.account.wizard` (`form`), `hr.employee.public` (`list`, `kanban`, `form`, `search`); duyệt đệ quy cây XML theo đúng model cha/bảng con | 0 field thiếu metadata trên đúng model tương ứng; XML `list`/`form`/`search`/wizard của delegate không còn node `mobile_phone`; vẫn có `work_phone` ở danh sách, chi tiết, tìm kiếm và wizard | PENDING | Sẽ chạy sau deploy PC server |
| HDF-02 | Delegate thực (ledger 1/1) | PC server (`SET TRANSACTION READ ONLY` + `with_user`, rollback) | Gọi `web_search_read`, `web_read_group` (nhóm `department_id`, `job_id`, `tp_account_status`, `active`), `web_read` chi tiết và tìm kiếm theo tên/mã/`work_phone`/`work_email` | Trả đúng tập hồ sơ ngoài phòng trong quyền đọc, 0 dòng phòng mình, không `AccessError` hoặc lỗi thiếu trường | PENDING | Sẽ chạy sau deploy PC server |
| HDF-03 | Delegate không có `hr.group_hr_user` | Kiểm logic/ORM hồi quy + PC server chỉ đọc | Mở/tạo/ghi `tp.hr.delegated.profile.wizard` và `hr.employee`: kiểm `fields_get`, truyền `mobile_phone` qua `create`/`write` RPC hoặc `default_mobile_phone` trong `context`, và áp cập nhật hồ sơ đang có sẵn `mobile_phone` | Actor không nhận được `mobile_phone` qua wizard/digest; mọi nỗ lực ghi `mobile_phone` qua RPC/context giả trên hồ sơ người khác bị chặn (`AccessError`); cập nhật `name`/`job_title`/`work_phone`/`work_email` **giữ nguyên** giá trị `mobile_phone` sẵn có (không ghi đè `False`/rỗng) | PARTIAL (đã PASS unit 24/24 + `18069`; chờ probe server) | `unit_guard_check.py` 24/24 PASS; `18069` `wizard_missing_fields=[]`, `wizard_has_mobile_in_xml=false` |
| HDF-04 | Delegate & Nhân viên thường | Kiểm logic/ORM + `18069` / PC server chỉ đọc | Gọi `res.users.tp_get_my_profile()` và kiểm đường `tp_save_my_profile` trên hồ sơ của chính mình | Chức năng xem/cập nhật hồ sơ cá nhân của chính actor (bao gồm `mobile_phone` của bản thân trong allowlist `SELF_EDITABLE_SCALAR_FIELDS`) vẫn hoạt động bình thường | PARTIAL (`18069` PASS; chờ probe server) | `18069`: `self_profile_has_employee=true`, `self_profile_own_mobile_key_present=true` |
| HDF-05 | Delegate thực (ledger 1/1) | PC server (`SET TRANSACTION READ ONLY` + `with_user`, rollback) | Gọi `tp.hr.workspace.get_overview()`, drill-down `action_employees` với `missing_contact_domain`, thử drill-down `[['mobile_phone', '!=', False]]` / `[['private_email', '!=', False]]`, xuất `_build_xlsx` và thử `hr.employee.export_data` | `get_overview` tính `missing_contact` theo `work_email` + `work_phone` khớp số dòng drill-down; drill-down `mobile_phone` và `private_email` bị từ chối (`ValidationError`); XLSX không chứa cột/giá trị `mobile_phone` hay thông tin riêng tư; `export_data` vẫn bị chặn (`AccessError`) | PENDING | Unit check `PROJECTION_FIELDS` PASS; chuẩn bị kiểm thực trên PC server |
| HDF-06 | Admin chính (`base.group_system` + `hr.group_hr_manager`) | `18069` và URL public (Playwright desktop `1440×900` & mobile `390×844` + ORM chỉ đọc) | Mở Tổng quan HR, Danh sách nhân viên, tìm kiếm/lọc/phân trang, mở Chi tiết nhân viên và Quay lại | Vẫn dùng view HR gốc (`tp_hr_workspace.employee_list`/`employee_form`), vẫn thấy và có metadata `mobile_phone` + `work_phone`, 0 lỗi `ListArchParser`/`field undefined`/OWL/console/HTTP 5xx trên cả desktop và mobile | PARTIAL (`18069` 13/13 PASS; chờ URL public) | `18069`: Playwright 13/13 PASS (desktop & mobile), ORM `missing_field_nodes=[]` trên cả list/form/search |
| HDF-07 | Nhân viên thường (không `hr.group_hr_user`, không ủy quyền) | `18069` và PC server (`SET TRANSACTION READ ONLY` + `with_user`, rollback) | Kiểm `fields_get`, `read`, `search`, `export_data` trên `hr.employee` / `hr.employee.public`, `tp.hr.workspace.get_overview`, `tp.hr.delegated.profile.wizard` | Không đọc được `mobile_phone`, `phone`, `email`, `private_*`, hợp đồng/lương của người khác; wizard ủy quyền và tổng quan HR vẫn bị chặn (`AccessError`) | PARTIAL (`18069` PASS; chờ PC server) | `18069`: toàn bộ truy cập hạn chế bị chặn (`AccessError`), danh bạ công việc 0 field thiếu metadata |
| HDF-08 | Delegate thực (trình duyệt E2E) | URL public (`https://hybrid-send-ready-ballot.trycloudflare.com`), desktop & mobile | Mở Danh sách nhân viên, tìm kiếm/lọc/phân trang, mở chi tiết & quay lại, mở wizard cập nhật rồi Hủy | Không còn lỗi `ListArchParser` / `mobile_phone undefined` / OWL | NOT_RUN | Không có mật khẩu/cookie phiên của actor thật; giữ đúng quy tắc không reset mật khẩu, tạo user giả hoặc grant/revoke người thật |

## 3. Ranh giới bảo toàn bắt buộc

- Không cấp `hr.group_hr_user`, `hr.group_hr_manager` hoặc `base.group_system` cho tài khoản được ủy quyền.
- Không gỡ `groups='hr.group_hr_user'` khỏi `tp_hr_attendance/models/directory_privacy.py`.
- Không giả `fields_get` hoặc khai báo field ảo ở JavaScript; không thêm cột DB; không sửa `odoo/` hay `addons/`.
- Giữ nguyên quyền nghiệp vụ tại phòng của actor, phạm vi quản trị ngoài phòng, bảo vệ tài khoản đặc quyền, cấm tự nâng quyền/cấp tiếp admin và cơ chế thu hồi delegation.
- Giữ nguyên toàn bộ foreign diff của các phiên khác trong working tree; chỉ commit/push và deploy đúng các tệp thuộc phạm vi `HR-DELEGATE-FIX-001`.
