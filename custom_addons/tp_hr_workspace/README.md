# TP HR — HR-001 implementation spec

## HR-EMPLOYEE-XLSX-001 — 19/11/2026

`20.0.1.14.0` thêm nút **Xuất Excel** trên thanh Danh sách nhân viên (desktop cạnh Thêm nhân viên; mobile trong thanh điều hướng). Dialog đếm nhân viên phía server và cho xuất toàn bộ kết quả đang lọc, toàn bộ trong quyền quản lý gồm lưu trữ, hoặc dòng đã chọn. Dùng domain/context đã áp của SearchModel, gồm bộ lọc nâng cao; không giới hạn trang hoặc nhóm đang mở.

Exporter hiện có tạo sheet **Danh sách nhân viên**, **Dữ liệu chi tiết** và **Hợp đồng lao động** khi được phép/có dữ liệu. Danh sách cột thực, quyền, cách dùng và kiểm chứng tại [bàn giao](../../docs/demo/HR_EMPLOYEE_XLSX_001_ACCEPTANCE.md). Dữ liệu riêng tư chỉ theo field/record/company access của HR; không xuất lương, credential hoặc nội dung đính kèm.

Thứ tự chung: `department.tp_sequence,id`, rồi `employee.sequence,id`; phòng chưa khai báo đứng cuối. Phòng ban và đơn vị dùng handle chuẩn Odoo; migration khởi tạo thứ tự theo `name,id` cũ. Nhân viên giữ cơ chế kéo cả hàng hiện hành. Xuất chỉ đọc, không ghi lại thứ tự.

## UI-TABLE-FILTER-001 — 14/11/2026

Implemented content-appropriate table filtering (`DEC-044`, verified on `tp_tanphat_test` `18079`) via shared `<TpTableFilterBar>` (`static/src/table/filter_profiles.js`, `table.js/xml/scss`), action-specific `<search>` views (`views/search_views.xml`, `employment_contract.xml`) isolating `Hồ sơ cần bổ sung` / `Lưu trữ` / `Chưa có tài khoản` / `Training Attendances` / `Nơi làm việc` / `Nhãn` / `Bảng đối chiếu` / `Nhật ký` / `Loại hồ sơ năng lực` / `Hợp đồng nhân sự`, relation search widgets (`hr_ui.xml`, `tp_hr_relation` guard in `HrListModel._getNextConfig` preserving `HR-LIST-013` department grouping), self-profile filters (`my_profile.js/xml`), and `tests/test_table_filter_hr.py`. See [TP_TABLE_FILTER_INVENTORY.md](../../docs/ui/TP_TABLE_FILTER_INVENTORY.md) and [UI_TABLE_FILTER_001_ACCEPTANCE.md](../../docs/demo/UI_TABLE_FILTER_001_ACCEPTANCE.md).

## UI-HISTORY-001 — 14/11/2026

Cleaned up **Lịch sử hoạt động** across both HR Chatter and the self-service **Thông tin cá nhân** page without altering stored DB history: moved future role-change and department-transfer JSON snapshots out of `mail.message` into private `tp.hr.employee.audit` (`role_change`, `department_transfer`) while keeping human-readable Vietnamese business notes in Chatter (`hr_role.py`, `department_transfer.py`); expanded `hr_history.py` (`format_hr_message_body`, `extract_history_item`) to summarize legacy raw JSON envelopes/onboarding banners and fully translate English tracking labels/values; and redesigned the `history` tab in `my_profile` (`my_profile.py`, `my_profile.js`, `my_profile.xml`, `my_profile.scss`) with category badges, filter pills (`Tất cả`, `Hồ sơ & Cá nhân`, `Vai trò & Phòng ban`, `Tài khoản`), effective-date chips, and line-by-line diff rows (`Trường | Cũ → Mới`). Verified by `test_history_hides_raw_json_localizes_tracking_and_cleans_legacy_entries` (`tests/test_my_profile.py`) and HOOT (`static/tests/hr_profile.test.js`).

## UI-PERSONAL-TAB-001 — 14/11/2026

Redesigned `hr.employee` form tab **Thông tin cá nhân** (`views/workspace.xml`, `static/src/profile/employee_profile.scss`) into a balanced 2-column (`.o_tp_hr_personal_grid`, 1 column on `<= 991px`) layout of 8 `.o_tp_hr_card` sections matching **Tổng quan**, replaced `.o_address_format` vertical blank spacing with 6 crisp address rows, added readonly empty-binary fallback `"Chưa có tệp"` via `.o_tp_hr_binary_cell` (`"Tải tệp lên"` in edit mode), and localized all field labels, tooltips (`help`), and selections (`sex`, `marital`, `certificate`) into Vietnamese on `HrVersion` and `Employee` (`models/hr_ui.py`), matching the self-service **Thông tin cá nhân** view (`my_profile`). Covered by `test_employee_personal_information_tab_is_card_structured_and_vietnamese` in `tests/test_hr_ui.py`.

## UI-SHELL-UNIFY-001 — 14/11/2026

Replaced the sidebar `"Tài khoản"` item and `openAccount()` callback with `<TpUserAccountMenu>` from `tp_web_home` (logged-in user's `[Avatar] Full Name [chevron]` opening a 2-item dropdown: **Thông tin cá nhân** and **Đăng xuất**, keeping `is-rail` tooltip/access and mobile drawer support). Removed `static/src/identity_navbar.js` (navbar synchronization and `tp.identity/changed` bus listener are handled centrally by `tp_identity` in `tp_web_home`; `tp_hr_workspace` depends on `tp_web_home`).

Added self-service **Thông tin cá nhân** (`tp_hr_workspace.action_my_profile`, route `/odoo/my-profile`, OWL `TpHrMyProfile`, `models/my_profile.py`, `controllers/my_profile.py`, `static/src/my_profile/`): registered `tp_personal_profile` handler so every user clicking **Thông tin cá nhân** views all 6 profile tabs (including read-only employment contracts and strict own-employee file download `/tp_hr/my_contract/<doc_id>/<file|appendix>`) and can update allowlisted personal/contact/address/ID/family/resume/skills/avatar fields, syncing immediately to HR Admin's `hr.employee`, chatter, and `tp.identity/changed` while blocking writes to official `name`/org/job/contract/ACL fields. See [UI_SHELL_UNIFY_001_ACCEPTANCE.md](../../docs/demo/UI_SHELL_UNIFY_001_ACCEPTANCE.md).

## HR-EMP-014 — 13/11/2026

Version20.0.1.11.0 adds **Hợp đồng lao động**, bringing the profile to six tabs. Internal employment
classification lives on `hr.version` and is inherited by employee: nullable
Ngắn hạn/Dài hạn/Thuê khoán, tracked and guarded by employee write access.
Native contract dates/fixed_term remain the only labor-date source. Minimal
`tp.hr.contract.document` stores paper metadata/private files and outsourced
service dates; versions can share one document. Company/HR ACLs, attachment
guards and restrict dependencies preserve HR-DELETE-010.

The compact list retains013's fixed department grouping and account actions,
with job → classification → phone columns. Shared basic-missing criteria power
row reasons, overview/drilldown and XLSX. Chatter is **Lịch sử hoạt động**;
the smart button is **Phiên bản hồ sơ**. Recognized legacy identity events are
summarized during serialization without changing stored bodies. New events
use business text and a private audit. The duplicate reports menu is inactive;
**Xuất Excel nhân sự** remains in Tổng quan with scope/time/filter metadata.

See [guide](../../docs/demo/HR_EMP_014_USER_GUIDE.md),
[schema/access](../../docs/security/HR_EMP_014_SCHEMA_AND_ACCESS.md),
[acceptance](../../docs/demo/HR_EMP_014_ACCEPTANCE.md) and
[deploy/rollback](../../ops/runbooks/HR_EMP_014_DEPLOY_AND_ROLLBACK.md).
The five-tab descriptions below are historical;014 has six tabs.


## HR-LIST-013 — 13/11/2026

Version20.0.1.10.2 makes department sections a fixed employee-list layout.
The scoped `HrListModel` always prepends `department_id` before native config
normalization; SearchModel has no default department facet. Clearing search
or secondary grouping keeps the department sections and hidden department
column. Actual department domain searches remain available. Other HR lists
and native forms keep their existing behavior; no global model patch.
See [acceptance and rollback](../../docs/demo/HR_LIST_013_ACCEPTANCE.md).

## HR-LIST-012 — 13/11/2026 (grouping superseded by013)

Version20.0.1.10.1 restores the compact employee table requested after011:
native default department grouping with light cyan headers, plain text names,
no repeated department column while grouped, no large intro block or avatars.
Clicking a row still opens the existing profile. Other HR lists keep011 layouts;
account actions and backend guards remain. The removable grouping from012 is superseded by013.
See [acceptance and rollback](../../docs/demo/HR_LIST_012_ACCEPTANCE.md).

## HR-UI-011 — 13/11/2026

`tp_hr_workspace` 20.0.1.10.0 replaces the duplicate employee navigation with
one **Danh sách nhân viên** entry, preserving old action/XML IDs and all data.
The scoped `tp_hr_table` uses native backend search, sort and grouping, actual
10/20/50/100 limits, group units, optional columns and actionable empty/error
states. Only its own renderer changes; the global ListRenderer is untouched.

Employee detail opens readonly, with explicit Edit/Save/Cancel on desktop and
mobile. Dirty cancellation/navigation asks before discarding or saving. Its five
tabs preserve personal field groups, work details, resume/skills/certifications,
versions, account workflows and chatter history. Department/job/tag counts and
drilldowns use the same active, company-scoped, record-rule-visible population
without sudo. Catalog forms, location empty states, declared employee hierarchy
and the four import UI steps reuse native views and existing backend states.
Employee labels remain `hr.employee.category`, with no access-grant semantics.

Shared shell widths and password/focus/delete guards remain. No API contract,
stored business fields, account data or business state machine changes.
See [design](../../docs/ui/HR_UI_011_DESIGN.md),
[acceptance/evidence](../../docs/demo/HR_UI_011_ACCEPTANCE.md) and
[deploy/rollback](../../ops/runbooks/HR_UI_011_DEPLOY_AND_ROLLBACK.md).
The historical profile sizes below are superseded by HR-UI-011.

HR-COMPACT-007 (CHG-20261112-010) reduces profile spacing and typography:
88px desktop avatar, name up to 32px, 15px tabs and 16px information fields.
The native toolbar fits the available content width without moving the sidebar.
Sidebar and account/position dialogs keep their existing size and behavior.

HR-PROFILE-005 (CHG-20261112-008): employee detail and account management follow
user reference images: ice-blue background, teal actions, large identity,
icon tabs, outlined work/contact cards and account summary. The native account
wizard has explicit Vietnamese labels, two columns, reason input and lock/reset
controls, stacking on mobile. Existing Odoo navigation, identity checks, access
rules and one-head policy remain. HR-SIDEBAR-006 (CHG-20261112-009) removes the profile-specific rail and palette:
opening employee detail keeps the same sidebar color, width and saved collapsed
state as the employee list. Only employee content changes.

HR-POSITION-004 (CHG-20261112-007) moves “Đổi chức vụ” into the employee detail
only and reserves one active HEAD per company/department. Existing holders must
be demoted before another appointment; the database index also protects races.

HR-POSITION-003 (CHG-20261112-006; row entry superseded by004): the role wizard separates an HR
job change (reason/preview/audit, no account required, access unchanged) from
KH-KD staff↔HEAD commands (same backend guards and optional atomic job update).
Job selections must be active and within company/department or shared catalog;
preview includes the operation kind and current version so stale changes fail.

HR-ACCOUNT-002 (CHG-20261112-005): account creation now reauthenticates the
administrator first, then collects login/password/confirmation in one labeled
OWL dialog with Vietnamese validation. Cancellation creates nothing; creation,
password, employee mapping and audit are atomic. Reset reuses the dialog with
a read-only login. New passwords are never stored in transient fields or the
native identity replay payload; submit requires the native session identity
check within 10 minutes. Odoo hashing/policy and backend scope guards remain.

Native Odoo roster workspace for authorized HR users. Public employees retain the native public directory; this app never grants HR rights. The HR navigation has its own namespace and menu identity. HR-ACCOUNT-ROLE-001 reuses tp_kd_workspace scoped groups and tp.kd.department.role through a guarded admin action.

HR-DASH-002: one native navbar; 264px navy HR navigation matching the Kinh doanh palette, with a native employee group icon before “Nhân viên” (68px rail/tablet; modal drawer on mobile); compact header with unit/job/profile filters and create/export/refresh; five measures; large department donut and legend; horizontal job bars using one zero-based scale; summary table, data-quality checklist and linking status. The HR dashboard stays light under OS/Odoo dark themes. Native employee lists/forms preserve Odoo search, optional columns, group, archive, version timeline, private field groups, skills and chatter.

Population: backend visible employee domain plus selected unit/job and active/archived/all profile filter. Active means an unarchived profile, not a legal employment status. All chart totals, drilldowns and export use that population. Basic completeness means code + department + (source title or verified canonical job), without claiming payroll/contract completeness. No salary, attendance or employment trend is inferred. Missing information stays unknown.

Acceptance: HR/admin can navigate real native actions, edit/create/archive with native guards, inspect history and skills, use 10/20/50/100 page limits (20 default) scoped to database/user/company/app/action/view. Dashboard has loading/error/retry/empty states and keyboard-accessible chart drilldown. Screens fit 1440/1024/768/390/320 and respect reduced motion. HR menus use the server-filtered Odoo menu service. Browser and backend verification belong to the coordinated test run, not this specification.


Unknownness: HR/version keeps native defaults for compatibility but does not present default single/children/distance or wage as confirmed source facts. HR users explicitly confirm personal defaults; HR managers explicitly confirm wage. Until confirmation, those fields show “Chưa có thông tin”; a confirmed wage of zero remains a valid zero. These flags do not create payroll or legal contract workflow.

Configuration links are real scoped native actions for skill types/levels, resume sections and employee tags, with HR-manager menus. Account administration creates a dedicated new user for one employee; existing identity mapping cannot be transferred through native/import/resource writes or legacy link/unlink RPC. Native company uniqueness remains. No automatic username matching or bulk account creation is introduced.

Version history stays a native list with HR pagination. Unconfirmed wage cells remain blank; this action does not expose native wage graph/pivot analytics from technical defaults. Confirmed zero wages remain a valid zero.

The redesigned employee form has five tabs, readonly initial mode, native edit/save/discard/dirty handling, a compact identity header, light two-column content and mobile stacking. Account status is Mở / Khóa / Chưa có tài khoản across list, form, dashboard and XLSX; profile archive is separate. Account/password/role controls require system admin in the employee company. Password reset uses Odoo's native identity verification.

Staff ↔ HEAD KH-KD uses a reason and server preview of direct/implied groups, assignments and grants. Demotion revokes the department responsibility and blocks conflicting separate management rights, retaining listed independent financial_read grants. Session revision invalidates old sessions. Job titles never grant rights; unsupported departments are explicit. See [admin guide](../../docs/demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md), [security](../../docs/security/HR_ACCOUNT_ROLE_001_SECURITY.md) and [acceptance](../../docs/demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md).
# HR-DELETE-010 — 12/11/2026

CHG-20261112-016, HR 20.0.1.9.0 with `tp_organization` 20.0.2.2.0 (DEC-042,
replaces the mistaken-entry-only rule of 008). **Tác vụ → Xóa vĩnh viễn nhân
viên** opens the `tp_hr_workspace.employee_delete` OWL dialog (native Dialog):
identity table, Sẽ xóa / Giữ lại / Đang chặn sections, required reason, optional
**Xóa hồ sơ và khóa tài khoản**, the admin's own password and a red confirm
button. `tp_permanent_delete_execute` re-checks system admin + HR manager, company
and HTTP session, verifies the freshly typed password with native
`_check_credentials` inside `_assert_can_auth` on every request, locks, compares
the plan digest with the preview and committed data, then locks/keeps accounts,
deletes owned rows, sweeps chatter/files/xmlids and writes the audit in one
transaction. Import lines/batches/files stay; independent business links block
with a hint; deleted TP codes are never reissued. See
[acceptance](../../docs/demo/HR_DELETE_010_ACCEPTANCE.md) and
[rollback](../../ops/runbooks/HR_DELETE_010_DEPLOY_AND_ROLLBACK.md).

# HR-CORRECTION-008 — 12/11/2026

CHG-20261112-013, HR 20.0.1.8.0 with `tp_organization` 20.0.2.1.0 (deletion part
superseded by HR-DELETE-010 above). Employees were deleted only through **Xóa hồ sơ nhập nhầm** (`tp.hr.employee.delete.wizard`,
server action bound to employee list/form): system admin in the same company,
backend eligibility per record, required reason, all-or-nothing batch and a
durable `tp.hr.employee.audit` row without FK to the deleted record. Only unused
manual entries qualify; any roster source, account, role, assignment, grant,
document, user message, activity, later version or stored reference blocks with
a Vietnamese reason and the dialog offers **Lưu trữ nhân viên** instead. Native
Delete is hidden and `unlink` is refused outside the internal sentinel; the
`hr_timesheet` delete action is unbound. Archiving never locks the account.
Employee codes follow the highest valid issued code + 1 (archived and audited
codes included, never reused); migration 20.0.2.1.0 fixed the legacy 20000
sequence. Migration 20.0.1.8.0 sets vi_VN on wizard-created personal accounts
that kept en_US. See [guide](../../docs/demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md),
[acceptance](../../docs/demo/HR_CORRECTION_008_ACCEPTANCE.md) and
[rollback](../../ops/runbooks/HR_CORRECTION_008_DEPLOY_AND_ROLLBACK.md).

# HR-POSITION-004 — 12/11/2026

HR-AUTH-FOCUS-009 (CHG-20261112-014, 20.0.1.8.1): navigation search owns a
semantic search form so Chrome does not pair it with native identity passwords.
Native dialog ownership protects pending sidebar focus; account dialogs restore
their opener, autofocus employee login on create and new password on reset.
Filters are preserved. See [acceptance](../../docs/demo/HR_AUTH_FOCUS_009_ACCEPTANCE.md).

IDENTITY-ORG-001 (CHG-20261112-011, HR20.0.1.7.0): official HR names and account
partner photos share a verified identity; no private-email fallback. Immediate
department transfer is in Work information, with admin preview/reason/handover,
scope revocation, optional reviewed cross assignments, native version history and
atomic audit/session invalidation. Current/head/cross scope controls server menus,
native actions and KD dashboard/report access; project capabilities still control
data/money/files. Unsupported departments have their own minimal workspace.
See [admin guide](../../docs/demo/IDENTITY_ORG_001_USER_GUIDE.md) and
[verified results/limits](../../docs/demo/IDENTITY_ORG_001_ACCEPTANCE.md).

Đổi chức vụ chỉ nằm trong chi tiết nhân viên, không còn nút trên từng dòng.
Mỗi công ty/phòng chỉ có một trách nhiệm trưởng phòng active. Muốn bổ nhiệm
người khác phải hạ cấp người đang giữ vai trò trước, có lý do và lịch sử;
không tự thay thế. Preview/apply báo tên người hiện tại, unique index chặn cả
provisioning trực tiếp và yêu cầu đồng thời. Role active dù user khóa hoặc đã
hết hạn vẫn cần thu hồi rõ ràng. Đổi chức vụ HR không tự cấp quyền nghiệp vụ.

