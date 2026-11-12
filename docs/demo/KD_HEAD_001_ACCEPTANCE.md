# KD-HEAD-001 — Kiểm chứng quyền HEAD toàn phòng KH-KD

Ngày 10/11/2026 (Asia/Saigon). Batch `CHG-20261110-002`.
Căn cứ: DEC-033 và [prompt KD-HEAD-001](../prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md).

**Trạng thái: `IMPLEMENTED_VERIFIED_DEV_PENDING_BUSINESS_VISUAL_PILOT`.**
Đã áp riêng delta HEAD lên Odoo18069/`tp_tanphat_dev` ngày10/11/2026, sau clone,
211/211 test và backup/restore verified. HEAD dùng tài khoản hiện có, quản lý
scope KH-KD động đúng company/phòng; bốn vai khác giữ quyền hiện hữu. Business
acceptance, visual acceptance, BASE/ký/hiệu lực, kế toán/thực chi và pilot là
các cổng riêng. Không commit/push.

## Baseline đã quan sát

- Dev `tp_tanphat_dev`, Odoo loopback18069/PostgreSQL55432. Trước triển khai:
  `tp_kd_workspace`20.0.1.8.0, `tp_project`20.0.1.1.0,
  `tp_contract`20.0.1.2.0, `tp_web_home`20.0.1.4.1.
- HEAD dùng tài khoản hiện hữu, company1/department18/team4; danh tính exact và
  credential giữ trong mapping private, không sao chép vào tài liệu này.
- Quyền HEAD cũ:8 reader assignments,16 project grants (financial_read và
  contract_review_commercial),72 KD grants (review7 domain, opportunity
  prepare/submit). Tất cả đang active/không expiry trong inventory ban đầu.
- 5 actor được quan sát bằng transaction PostgreSQL `READ ONLY`: 6040 quan sát ACL,
  record scope, capability, tiền, UI permission/action, menu/dashboard. Lặp lại
  baseline xác nhận deputy/project_lead/planning/support không đổi.
- Fingerprint baseline277 bảng/7819 hàng/295 attachment references; đối chiếu
  không đổi đạt auth/config/blob/PG PID. Có fingerprint riêng account/auth/group/
  assignment/grant từng actor và snapshot owner/reviewer17 bảng. Đây là baseline
  đọc, không là bằng chứng các thao tác ghi HEAD mới đã đạt.
- Clone ban đầu: `tp_tanphat_kdhead001_20261110`, port19589; snapshot/restore
  586 bảng exact rowsets,295 attachment references; dev tiếp tục chạy. Source
  riêng tại `.local/kd-head001/workspace/custom_addons`.

Evidence private nằm dưới `.local/kd-head001/`: `inventory-dev-before.json`,
`dev-capabilities-before.json`, `dev-capabilities-baseline-check-parity.json`,
`inventory-security-baseline.json`, `actor-auth-rights-owners-before.json`,
`restore-evidence.json`. Không đưa credential, dump hoặc filestore vào Git.

## Ma trận quyền trước → sau

Cột sau đã áp trên dev; điều kiện state/scope và bằng chứng nằm trong bảng chi tiết cùng kết quả phía dưới.

| Phạm vi/hành vi | HEAD trước batch | Sau KD-HEAD-001 trên18069 |
| --- | --- | --- |
| Scope dự án |8 dự án được seed reader/grant riêng | Mọi managed project đúng company/department đã provision, kể cả phát sinh mới; không seed lại |
| CRM trước project | Team4 được provision; owner guard cũ | Toàn team đúng company/department; giữ hồ sơ chưa có project, không tạo project/gói giả |
| Tạo/sửa dự án, WBS, task | Chưa cấp capability ghi thật | Tạo/sửa/điều phối/progress qua action có audit trong phòng |
| Hồ sơ typed | Chủ yếu review, đúng reviewer từng hồ sơ | Lập/sửa/gửi/trả lại hồ sơ mình/người khác đúng state, lý do/version và kiểm người can thiệp |
| Hợp đồng | Đọc tiền và commercial review; chưa draft edit/submit | Lập/sửa tiền nháp/gửi/điều phối/rà soát hồ sơ người khác, giữ self-review và bốn mắt |
| Gói/lần tham gia | Có code CHG014 nhưng chưa HEAD grant mới | Quản lý gói/lần tham gia/tình trạng/ghi chú/tiền đúng workflow |
| Tiền/file/báo cáo | Tiền8 dự án; giới hạn theo grants/owner | Đọc/sửa tiền nháp, file và R01–R06/XLSX toàn scope động; unknown/0 và các nghĩa tiền giữ riêng |
| Người nhận phân công | Không tự tăng grant | Người nhận phải có current authorized reader scope và điều kiện nghiệp vụ; không đổi quyền bốn actor còn lại |
| Thu hồi/hết hạn | Quyền dựa trên96 hàng legacy | Vô hiệu96 hàng cũ, tạo1department role+1creation event; revoke/expiry role mất quyền ở request tiếp theo, không có fallback legacy |
| Ngoài phòng/admin/pháp lý | Bị giới hạn | Tiếp tục chặn; không Settings/admin/HR nhạy cảm/kế toán toàn công ty/duyệt pháp lý/cấp quyền người khác |

### Ma trận chi tiết model/action và bằng chứng trên clone

“Sau” dưới đây là hành vi source bản riêng đã xây dựng trên clone, **chưa là
xác nhận đã áp dev**. Mọi dòng cần role HEAD đang hiệu lực đúng company/phòng;
project phải managed, CRM trước project cần team active đúng company/phòng.
Version/reason/row lock/retry và kiểm scope backend vẫn áp dụng. Người nhận
phân công phải có quyền hiện hành; command không tạo grant cho người nhận.

Các ký hiệu bằng chứng HEAD dùng chung:

- **H1:** `TestHeadDossiers.test_head_edit_other_draft_reason_snapshot_and_revoke`
  — sửa nháp người khác, lý do/version/actor/owner/snapshot và thu hồi.
- **H2:** `TestHeadDossiers.test_head_typed_takeover_and_contributor_cannot_review`
  — nhận reviewer/trả/mở sửa, chặn người can thiệp cùng vòng, cho review vòng mới độc lập.
- **H3:** `TestHeadDossiers.test_head_owner_reassignment_requires_valid_scope_and_audit`
  — phân công có audit, giữ dấu owner cũ, từ chối actor không có quyền.
- **H4 — PASS trong full211/211:**
  `TestHeadDossiers.test_head_management_across_remaining_six_typed_models`
  — parametric integration cho sáu model còn lại: HEAD thường tạo với owner
  nhân viên, sửa có lý do/tiền nháp, gửi và bị chặn tự nhận review; reviewer khác
  trả, nhân viên mở sửa/gửi vòng độc lập, HEAD nhận reviewer rồi trả.

H1–H3 trực tiếp tạo `tp.allocation` và kiểm helper kế thừa chung
`tp.kd.review.document`; các dòng typed khác bổ sung test đặc thù domain dưới
đây. H4 đạt với cả sáu model; cùng H1–H3 bao phủ HEAD ghi trên đủ bảy typed model.
Native UI đã trực tiếp thao tác project/WBS/CRM, sửa/gửi contract và allocation;
không coi đây là bảy luồng ghi UI độc lập.

| Model/action | HEAD trước batch | HEAD sau trên dev18069 | State và điều kiện giữ | Test class/method hoặc evidence cụ thể |
| --- | --- | --- | --- | --- |
| `tp.kd.department.role` — scope/read/search/revoke/expiry | 8 assignment +16 project grant +72 KD grant; scope cố định | Scope động mọi project managed trong phòng và team CRM trước project; thu hồi/hết hạn không dùng legacy fallback | User active, allowed company, role active/date_start/date_end, đúng company/phòng; ngừng active 96 dòng legacy riêng HEAD, tạo 1 role +1 event theo journal | `TestDepartmentRole.test_dynamic_projects_and_exact_department`; `test_revoke_and_expiry_close_cached_access_and_money`; `test_role_company_user_activity_and_start_date_are_live`; `TestDepartmentHeadScope.test_legacy_assignment_and_grants_are_preserved_for_other_staff` |
| `project.project` — `project_create`, metadata/status/note/reopen, chủ trì | Reader; có code scoped nhưng chưa được cấp ghi thật | Tạo và quản lý project trong phòng, hai góc nhìn cùng ID; phân công chủ trì hợp lệ | Mã unique/company/phòng; lifecycle tracking/executing/paused/ended là theo dõi; ended cần reopen có lý do; project mới không cấp quyền người nhận | `TestHeadOperations.test_new_project_command_and_dynamic_staff_project`; `test_command_context_defaults_are_checked_and_retries_do_not_duplicate`; `test_new_project_assignment_requires_existing_security_scope`; `TestProjectRestructure.test_status_reason_version_retry_and_reopen`; native `native_flow.cjs`: tạo project và đổi góc nhìn |
| `project.task`/WBS — create/edit/assign/progress | Đọc theo assignment; không có HEAD capability ghi | Tạo/cấu trúc/giao lại/đổi hạn, đầu ra và progress thay nhân viên; giữ assignee khác actor | Command scoped; parent/recipient hợp lệ; version/write_date/lock/retry; chỉ `01_in_progress`, `04_waiting_normal`, `1_done`; generic write không mở | `TestHeadOperations.test_task_progress_on_behalf_preserves_assignee`; `test_new_project_assignment_requires_existing_security_scope`; `TestProjectRestructure.test_task_capabilities_are_separate_from_money_and_generic_write`; `test_task_stale_foreign_parent_and_recipient_without_assignment`; native `native_flow.cjs`: tạo WBS |
| `crm.lead` — create/write/prepare/record_submission/money/lead_assign | Own draft theo prepare/submit grants; trước project owner trong team; tiền theo grant project | Tạo/sửa nháp và tiền của nhân viên, phân công; xử lý toàn scope project/team | `identified`/`preparation` được sửa; chỉ `preparation` đủ căn cứ/route bid mới nộp; `submitted` khóa; can thiệp cần reason/current version; receiver có current scope, team membership riêng lẻ chưa đủ | `TestHeadOperations.test_preproject_other_owner_money_files_and_live_revoke`; `test_other_draft_reason_stale_and_transfer_audit`; `test_create_recipients_require_existing_project_or_preproject_scope`; `TestOpportunityAccess.test_prepare_is_not_submit_and_owner_is_required`; native `native_flow.cjs`: sửa nháp người khác và kiểm owner giữ nguyên |
| `tp.bid.package`, `tp.bid.package.amount`, `tp.project.participation` — package/party/bid commands | Có code CHG014 nhưng HEAD chưa có capability ghi | Tạo/sửa gói, các bên, theo dõi tình trạng/kết quả, ba loại giá theo source | Owner có scope hiện hành; version do server quản lý; tracking/participating/awaiting_result khác outcome; không tự sinh contract; unknown khác estimated0; nguồn/đích cùng project/company | `TestHeadOperations.test_create_recipients_require_existing_project_or_preproject_scope`; `TestProjectRestructure.test_multiple_packages_attempts_direct_and_outcome_isolation`; `test_partners_many_roles_and_duplicate_scope`; `test_money_unknown_zero_separate_meanings_and_revocation` |
| `res.partner`/bank — command đối tác dự án | Không có quyền quản lý nghiệp vụ mới từ HEAD | Tạo/cập nhật trường nghiệp vụ qua command; chặn sửa đối tác dùng ngoài scope | Shared-use được kiểm; không CRUD danh bạ/bank/tax toàn hệ thống; retry không tạo trùng; own safe preferences giữ native | `TestHeadOperations.test_partner_update_respects_shared_uses_and_create_retry`; `TestDepartmentHeadScope.test_head_contact_guard_preserves_own_profile_and_business_command` |
| `tp.contract`, `tp.contract.revision` — create_contract/create_amendment/edit_draft/submit_review/begin_rework | Đọc tiền và commercial review; chưa draft_edit/submit | Lập/sửa metadata/tiền và gửi nháp mình/người khác; business owner khác actor sửa | Edit/submit chỉ `draft`; `returned→draft` qua begin_rework có lý do; gửi lại cần fix_summary; in_review/đã khóa không sửa đè; audit metadata/tiền trước–sau; REST contract giữ nguyên | `TestHeadDossiers.test_contract_intervention_money_snapshot_and_four_eyes`; `test_head_contract_files_are_versioned_audited_and_frozen`; `TestContractWorkflow.test_p01_draft_submit_return_rework_resubmit`; `test_n03_state_reason_and_amount_validation`; `test_n05_stale_versions_are_rejected`; `test_n06_retries_replay_without_duplicates` |
| `tp.contract.submission` — take_review/return_review/assign_owner | Chỉ reviewer được chỉ định cũ; không HEAD takeover | Nhận reviewer/trả bản khác qua action; giữ reviewer gốc và business owner/audit riêng | take/return chỉ `in_review`; assign_owner ở `draft`/`returned`; reviewer hiện hành đủ quyền, không người gửi/HEAD can thiệp nội dung cùng vòng; R01/R05/inbox chuyển theo assigned reviewer | `TestHeadDossiers.test_contract_takeover_preserves_original_and_blocks_author`; `test_contract_intervention_money_snapshot_and_four_eyes`; `TestContractWorkflow.test_n01_self_review_is_excluded_and_rechecked_on_every_submission`; `test_n01_legacy_self_assigned_pending_cannot_return_or_rewrite_history` |
| `tp.allocation` — create/write/submit/return/rework/assign/take_review | Chủ yếu R/V/M, cần đúng reviewer; chưa prepare/submit/edit money | Đầy đủ hồ sơ khoán mình/người khác, tiền nháp và điều phối | Edit `draft`; submit `draft→in_review`; return `in_review→returned`; rework `returned→draft`; source/cấp1–2/cycle, reviewer độc lập; không cộng con vào tổng công ty | H1–H3; `TestAllocation.test_allocation_review_rounds_snapshot_and_version`; `test_allocation_scope_reason_stale_and_no_direct_state`; `test_allocation_parent_cycle_and_money_isolation` |
| `tp.production` — cùng action typed | Chủ yếu review trong scope được seed | Lập/sửa/gửi/trả/mở sửa/điều phối và tiền nháp toàn scope HEAD | Cùng ba state/action typed; hợp đồng/khoán/task nguồn đúng scope; kỳ/đơn vị/khối lượng hợp lệ; không tự là nghiệm thu | H1–H3 kiểm helper chung; H4 PASS; `TestProduction.test_production_workflow_snapshot`; `test_production_invalid_quantity_period_scope`; `test_production_source_mutation_and_scope` |
| `tp.acceptance` — cùng action typed | Chủ yếu review trong scope được seed | Quản lý đầy đủ hồ sơ đợt nghiệm thu KH-KD, tiền nháp và reviewer | Cùng ba state/action typed; nguồn sản lượng/contract/project cùng phạm vi, kỳ/ngày/đơn vị/khối lượng hợp lệ; không xác nhận chuyên môn/bản ký ngoài | H1–H3 kiểm helper chung; H4 PASS; `TestAcceptance.test_acceptance_workflow`; `test_acceptance_scope_quantity_chronology` |
| `tp.payment.request` — cùng action typed | Chủ yếu review trong scope được seed | Lập/sửa/gửi/trả/mở sửa đề nghị thu/chi, tiền nháp và điều phối | Cùng ba state/action typed; tạm ứng có căn cứ, không đòi nghiệm thu giả; theo đợt cần acceptance hợp lệ; không paid/posting | H1–H3 kiểm helper chung; H4 PASS; `TestPayment.test_payment_advance_workflow`; `test_payment_acceptance_source_and_basis` |
| `tp.periodic.plan` — cùng action typed | Chủ yếu review trong scope được seed | Lập/sửa/gửi/rà soát kế hoạch và hai measure tiền toàn scope | Cùng ba state/action typed; lịch month/quarter/year/unique; production/revenue riêng; nguồn/currency/basis/unknown giữ khác nhau | H1–H3 kiểm helper chung; H4 PASS; `TestPeriodicPlan.test_plan_calendar_and_guard`; `test_plan_comparison_source_and_snapshot` |
| `tp.credential` — cùng action typed/liên kết CRM | Review theo scope/owner/reviewer; không mở HR gốc | Quản lý hồ sơ năng lực/chứng chỉ nghiệp vụ đúng scope, điều phối và rà soát | Cùng ba state/action typed; restriction parent theo tổ chức/cá nhân vẫn ở backend; ngày hiệu lực hợp lệ; không tự phát hành/chứng thực pháp lý hoặc mở dữ liệu HR gốc | H1–H3 kiểm helper chung; H4 PASS; `TestCredential.test_credential_person_and_dates`; `test_credential_bid_usage_and_forged_command`; `test_edit_visible_links_preserves_hidden_person_credential` |
| `tp.obligation` — cùng action typed/checklist | Review theo scope được seed | Lập/sửa/gửi/trả/mở sửa và phân công hồ sơ nghĩa vụ | Cùng ba state/action typed; checklist có lý do/history; không tự xác nhận thanh lý/công nợ hết hoặc nghĩa vụ pháp lý hoàn thành | H1–H3 kiểm helper chung; H4 PASS; `TestKdReporting.test_obligation_history_and_no_legal_clearance` |
| `tp.kd.document`, `tp.contract.document`, `ir.attachment`/`ir.binary` — add/archive/read/download | File đọc theo parent/phân loại; chưa có HEAD command typed mới | Thêm/lưu trữ file nháp có audit, đọc/tải/preview đúng scope; giữ bytes/checksum/actor/version | Add/archive chỉ nháp, reason/version, tối đa20MB; file đã thuộc submission/frozen revision vẫn khóa sau rework; file mới nháp rework chưa gửi có thể archive; financial riêng; cấm public/token/relink/direct mutation | `TestHeadDossiers.test_typed_files_live_scope_stale_archive_and_submitted_evidence`; `test_head_contract_files_are_versioned_audited_and_frozen`; `test_contract_new_rework_document_can_archive_without_altering_prior_evidence`; `TestContractWorkflow.test_n04_submitted_documents_and_binaries_are_immutable` |
| CRM `ir.attachment`/`mail.message` — lead_document_add/remove/lead_comment | File/chatter coarse theo parent+quyền tiền/own draft; không journal command HEAD | Command thêm/lưu trữ file trực tiếp hoặc qua chatter, trao đổi actor thật; native chatter HEAD chỉ đọc | Lead chưa `submitted`, current version/reason/live HEAD; lưu bytes/audit; escape comment, không follower notification; direct mutate bị chặn | `TestHeadOperations.test_crm_content_commands_reason_version_replay_and_archive`; `test_native_chatter_head_flags_preserve_staff_and_recheck_revoke`; native `native_flow.cjs`: upload/comment/archive; HOOT `head_chatter.test.js` |
| `tp.kd.overview`, `tp.kd.report.center` — R01–R06/get_kd_report/export/inbox | Đọc scope8 project/tiền theo grant cũ | Toàn scope HEAD động, reviewer hiện hành, metadata/tiền/XLSX theo lọc | Không cộng chung stage/cấp khoán/currency/basis; R02 xuất toàn kết quả hơn100 dòng; file export guard cùng scope; revoke áp dụng query tiếp theo | `TestKdReportCenter.test_02_r01_contract_revision_traps_and_money_security`; `test_03_r03_stages_never_summed_together_and_plan_compare`; `test_04_r04_parent_child_allocation_never_summed_together`; `test_05_r05_and_r06_non_duplication_and_person_credential_scope`; `test_06_r02_pagination_over_100_excel_export_and_formula_injection_protection`; `test_07_validation_and_mid_session_grant_revocation`; `TestHeadDossiers.test_contract_takeover_preserves_original_and_blocks_author`; `browser.cjs`: R01–R06 render/download HEAD và support |
| `res.users`/group/grant/role admin, BASE/HR/accounting | Không cấp admin hoặc thẩm quyền pháp lý | Giữ chặn; phân công nghiệp vụ không mở grant editor | Chỉ vận hành được ủy quyền provision/revoke role; không password/MFA/passkey/Settings/HR nhạy cảm/ký/hiệu lực/posting/paid | `TestDepartmentRole.test_role_does_not_allow_generic_project_write_or_security_administration`; `TestDepartmentHeadScope.test_legacy_assignment_and_grants_are_preserved_for_other_staff`; parity6040 quan sát bốn actor trước fixture |

Bằng chứng cuối: **211/211 Odoo tests PASS,0failed/0error**; HEAD sáu typed
model còn lại đã qua H4. HOOT22tests/85assertions PASS; native project/WBS/CRM11
checks, contract/typed/HEAD chatter15checks, clone5login51checks, dev5login51checks
và HTTP/XLSX/lifecycle54checks PASS,0JSerror. Không cộng các đơn vị này thành
một tổng nghiệm thu. Technical verification không thay business/pilot.

Scope company/department phải khớp đồng thời; cùng company không có nghĩa thuộc
KH-KD. Có8 managed projects department18; dự án department2/19/20 và managed
project chưa có department không tự vào HEAD. CRM cũ có13 liên kết project
department18,4 liên kết department19/20;1 preproject thuộc team4; **7CRM thiếu
scope và1managed project thiếu department** giữ danh sách đối chiếu riêng,
không suy từ tên, đổi company/department hoặc public để mở quyền.

## Acceptance và kết quả hiện hành

| Nhóm kiểm | Yêu cầu bằng chứng | Kết quả |
| --- | --- | --- |
| Scope động | HEAD thật, dự án mới do HEAD/người khác thêm, hai góc nhìn cùng ID | PASS Odoo; native tạo dự án/WBS. Clone13project→0 khi revoke/expiry→13 khi restore; không seed lại |
| Ghi nghiệp vụ | Project/WBS/task, typed7domain, contract, bid/CRM; actor thường; audit/version/lý do | PASS full211, gồm H4 sáu model và allocation riêng; native11+15 checks |
| State/bốn mắt | Chặn self-review, sửa bản đã gửi/chốt, stale retry, xóa audit/căn cứ | PASS Odoo; native hợp đồng/allocation gửi reviewer khác và khóa sửa/tự review |
| Phân công | Giữ owner/reviewer cũ; receiver current authorized scope; không cấp grant tự động | PASS reason/version/recipient/reviewer takeover/original reviewer/audit |
| Tiền/R01–R06/XLSX | Tải thật, đọc workbook, toàn bộ dòng/tổng/bộ lọc và chặn ngoài scope | PASS HTTP54; từng cell/type, footer, summary, group khớp mọi RPC page |
| File/chatter | Upload/download nháp; khóa state; public/token/revoke không lọt | PASS Odoo/native/HTTP typed financial file; HEAD CRM command có audit, native chatter chỉ đọc |
| Revoke/expiry | Cùng session, không legacy fallback, restore có lý do | PASS cùng cookie; read/create/file bị chặn, Excel0dòng, restore đúng scope |
| Hồi quy bốn actor | Effective permission/account/group/grant/owner không đổi | PASS6040observations trước fixture và sau dev; deputy/project_lead/planning/support parity exact |
| Odoo/static/browser cuối | Source test=seal=applied; không failed/error | PASS211; Ruff/AST31Python,11XML,4JS; HOOT22/85; clone/dev51+51 |
| Backup/restore mới, áp dev | Fresh snapshot, restore exact, delta HEAD và preserve trước/sau | PASS586tables/295attachment refs/122checksums;49files; exact journal96+1role+1event |
| Dev smoke |5existing logins chỉ đọc, không fixture nghiệp vụ | PASS51checks,0JSerror; cổng18069 hoạt động |

## Source, backup và bảo toàn sau áp

- `tp_kd_workspace`20.0.1.9.0, `tp_contract`20.0.1.3.0; `tp_project` vẫn
  version20.0.1.1.0, đã upgrade tường minh để nạp role/ACL additive. Chỉ3addon này.
- Source49files test=seal=root, SHA256
  `6061d667e40765433b13a61ad74686462eef047acf08c7817cc72c504ea5fe24`.
  Final log: `.local/kd-head001/tests-20261110T045737886806Z.log`.
- Fresh backup `.local/kd-head001/backup-pre-apply-20261110T045731Z`, restore thử
  `tp_tanphat_kdhead001_backup_20261110T045742`:586bảng exact rowsets,
  295attachment references,122checksum. Dump/config/source/filestore private,
  không đưa vào Git. Upgrade log `dev-upgrade-20261110t050057z.log` rc0/0error.
- Journal `dev-head-delta.json`: riêng HEAD96legacy inactive (8assignment,
  16project grant,72KD grant),1role user/company1/department18,1creation event.
  User/group/password/MFA/passkey và bốn actor khác giữ nguyên.
- So277bảng/7819hàng cũ, auth/config/owner/reviewer và toàn bộ original business
  columns đạt; không tạo fixture dev. `business_owner_id` mới chỉ backfill từ
  unique explicit creation audit, không đoán owner. 295blob gốc còn nguyên
  SHA1/kích thước,0business file-reference đổi. Một assetJS native được tạo lại:
  attachment517→518, journal riêng `after-smoke-asset-blob-delta.json`.
- Có28message audit `ir.access` chuẩn:11ACL mới+17domain đổi, khớp1:1;0business
  chatter/0mail_notification. Không xóa để làm sạch màn hình. Các ACL mới và
  domain đổi được kiểm bằng source cùng parity bốn actor.
- Preservation lần đầu dừng dịch vụ: import Odoo đổi psycopg numeric caster
  Decimal→float làm hash khác. Đã chứng minh tất cả277table baseline bằng restore;
  kiểm độc lập23bảng/77cột số giữ SQLtype/text/value/ID exact; chuyển trong bộ nhớ
  tái tạo đúng sai lệch. Không sửa số liệu DB. Giữ artifact gốc và
  `preservation-baseline-normalization-proof.json`, chỉ cho phép exact ACL audit
  và asset IDs đã kiểm. Final `preservation-after-smoke-diff.json` PASS.
- Dev cuối: wrapper26792/listener29372, PostgreSQL55432 PID5708 giữ nguyên;
  clone19589 đã dừng. `final-readiness-result.json` lưu verdict cuối.

R01–R06 trên clone có12/130/81/19/370/22dòng. R02 gồm112preproject giả để vượt
pagination; tổng cell detail được đối chiếu168/1430/1296/266/3700/220, gồm type,
unknown/0, footer tổng theo currency/basis, summary và group. Workbook thực
`head-R01.xlsx`…`head-R06.xlsx`; số này là dữ liệu clone, không là số dev.

## Giới hạn và bước sử dụng tiếp

- 7CRM thiếu scope và1managed project thiếu phòng cần người có căn cứ đối chiếu;
  không tự gán KH-KD, đổi owner/phòng hoặc public. HEAD toàn quyền trong scope
  đã xác định; đây không là cấp toàn công ty.
- Recipient phải có quyền hiện hữu. Dự án mới chưa có staff scope thì chỉ HEAD
  đủ điều kiện; phân công không tự cấp quyền cho bốn actor khác.
- Dữ liệu dev không có contract document trong department18;2file contract hiện
  hữu đều department2 ngoài scope và tiếp tục bị loại. HTTP tải/revoke dùng file
  tài chính typed giả; Odoo tests có contract upload/archive/freeze/binary guard.
- Standard CRM HEAD Send/Note/Upload/bulk-delete được kiểm bị khóa. Deputy Send
  cũng bị khóa khi quan sát, chưa có baseline UI để kết luận nút đó từng bật;
  không nhận là ca so sánh UI staff đã đạt. Store test/6040permission parity và
  workflow staff riêng vẫn đạt, không sửa policy để làm nút bật.
- Có warning markdown2 optional và WinError5 filestoreGC trên Windows trong log;
  Odoo211 đạt và toàn bộ295blob gốc kiểm hash/kích thước đạt. Browser là Chromium
  desktop, không là test thiết bị thật. Không diễn tập restore đè dev đang có writer.
- Người dùng xem [hướng dẫn](KD_HEAD_001_USER_GUIDE.md), đối chiếu hồ sơ thiếu scope;
  business/visual acceptance và pilot giữ riêng. Không commit/push.

## Runbook vận hành và rollback chọn lọc

Các operator private `.local/kd-head001/run.py`, `provision.py`, `preservation.py`,
`backup_apply.py` tái sử dụng snapshot/restore, runtime ownership và ORM hiện có.
Chỉ task-owned clone được tạo dữ liệu giả. Source root phải còn đúng baseline;
source test=seal=applied, chỉ delta3addon tp_project/tp_contract/tp_kd_workspace.

1. Dừng clone trước Odoo tests. Seal source sau test/browser và xác nhận không
   còn writer. Fresh backup dùng exported repeatable-read snapshot, DB dump,
   filestore/config/source; hash manifest và restore vào DB verify task-owned.
2. Parent gate phải cho phép source digest và đúng delta HEAD trước apply.
   Chụp preservation fresh ngay trước apply; mọi drift từ inventory ban đầu
   ghi `external-before-apply-delta.json`, giữ bằng baseline mới, không tự hoàn tác.
3. Chỉ dừng Odoo dev đã xác minh source/config/PID; giữ PostgreSQL. Áp đúng
   delta đã seal, upgrade3addon, ORM provision HEAD, preservation trước restart
   rồi smoke chỉ đọc. Không seed password/fixture, đổi team hoặc bốn actor khác.
4. `dev-head-delta.json` lưu identity DB, all-column before/after exact96 hàng
   legacy,1role và1event. Preservation chỉ cho phép đúng các hàng journal này;
   auth/group/bốnactor/business/owner/blob/config ngoài delta giữ exact.
5. Rollback quyền: `provision.rollback(env, 'dev', restore_former_policy=False,
   commit=True)` chỉ revoke role đúng journal với lý do; kiểm conflict trước ghi.
   Khôi phục chính sách cũ phải được yêu cầu rõ qua `restore_former_policy=True`;
   khi đó mới reactivate96 hàng gốc. Không xóa role/event hoặc restore cả DB đè
   writer mới. Thay đổi role/hàng legacy sau apply làm rollback dừng để đối chiếu.
6. Rollback source phải kiểm source hiện hành, dùng maintained-source backup
   của batch và upgrade bản tương thích; giữ schema additive/audit. Có writer
   hoặc nghiệp vụ mới phải đối chiếu chọn lọc, không chép đè toàn repository/DB.

Tài liệu hướng dẫn thao tác: [HEAD user guide](KD_HEAD_001_USER_GUIDE.md).
Không commit/push trong batch này.
