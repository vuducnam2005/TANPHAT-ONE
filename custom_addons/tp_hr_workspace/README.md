# TP HR — HR-001 implementation spec

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
# HR-CORRECTION-008 — 12/11/2026

CHG-20261112-013, HR 20.0.1.8.0 with `tp_organization` 20.0.2.1.0. Employees are
deleted only through **Xóa hồ sơ nhập nhầm** (`tp.hr.employee.delete.wizard`,
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

