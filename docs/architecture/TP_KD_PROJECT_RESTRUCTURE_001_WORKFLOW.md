# KD-PROJECT-RESTRUCTURE-001 — Workflow từ test đến dev

## Delta riêng HEAD — KD-HEAD-001, 10/11/2026

DEC-033 mở riêng HEAD điều hành KH-KD toàn phòng bằng role phòng có thời hạn,
không lặp grant cho tám dự án mẫu. Delta đã áp dev18069;
**full211/211 và source/preservation đã đạt**, xem
[KD-HEAD-001 acceptance](../demo/KD_HEAD_001_ACCEPTANCE.md). Không thay policy
bốn vai khác, không duyệt toàn V2/TASK-001 hoặc pilot. Phần S2–S4 bên dưới giữ
nguyên số test/kết quả lịch sử, không mô tả quyền HEAD sau delta.

`tp.kd.department.role` theo user/company/phòng, active/ngày/reason mở scope
động project managed đúng phòng, gồm dự án tạo sau provisioning; CRM trước
project theo team active đúng company/phòng. Action/query/export/tiền/file
kiểm role hiện hành, thu hồi/hết hạn không còn grant legacy dự phòng. Delta
vận hành được journal: ngừng active96dòng riêng HEAD (8assignment/16project
grant/72KD grant), tạo1role+1event; số thực clone/dev đã được acceptance xác nhận; bốn actor khác giữ nguyên.

HEAD dùng command tạo project đúng mã/company/phòng; phân công chủ trì,
quản lý các bên, metadata/lifecycle/reopen/ghi chú và gói/lần tham gia theo
workflow hiện có. Người nhận phải còn scope/capability; project mới chỉ nhận
chủ trì HEAD hợp lệ trong phòng vì phân công không tự cấp assignment/grant.
Không đổi owner/company/phòng hàng loạt để mở quyền.

WBS/task dùng command/backend hiện có để tạo/cấu trúc/giao lại/tiến độ; HEAD
cập nhật thay assignee có reason/version/lock/retry và snapshot trước–sau.
Actor cập nhật khác người thực hiện; không biến HEAD thành assignee và không
mở generic write toàn model. CRM/package có version, lý do can thiệp, scoped
picker và kiểm người nhận lúc xác nhận; team membership không tự cấp quyền
nhận CRM trước project. Submitted vẫn là khai báo nộp và khóa căn cứ.

HEAD không CRUD danh bạ/ngân hàng/thuế toàn hệ thống; command đối tác dự án
chỉ cập nhật trường nghiệp vụ cho phép. Không mở admin/Settings/HR/paid/BASE/
ký/hiệu lực. Quy tắc contract/typed bốn mắt, reviewer hiện hành và file rework
ở [delta workflow hồ sơ](TP_KD_NATIVE_001_WORKFLOW.md#delta-head-kd-head-001--source-bản-riêng-ngày10112026).

## Baseline S2–S4 ngày09/11/2026

Chặng S2–S4, 09/11/2026. Đây là capability/action triển khai kiểm thử theo prompt,
không duyệt toàn V2/TASK-001, không provision tài khoản thật.

`project.project` giữ ID/partner (bên ký thương mại) cũ; `kd_investor_id` riêng.
`tp.bid.package` nhiều gói/project; `crm.lead.kd_package_id` nhiều lần tham gia/gói.
CRM identified/preparation/submitted và hợp đồng/revision không đổi nghĩa.
Quan hệ các bên `tp.project.participation`: project, gói optional, res.partner,
vai trò, căn cứ; unique quan hệ active đúng scope/partner/vai kể cả gói NULL. Ngừng quan hệ cần lý do qua command, giữ dòng cũ và nhật ký; có thể thêm lại quan hệ đúng sau đó. Không suy role từ tên.

`tp.kd.grant.domain` bổ sung project_metadata/project_status/project_note/
project_reopen/bid/wbs/task_assignment/task_progress. Từng quyền dùng prepare
và phải còn company/department/assignment; quyền ghi người thật không được cấp.
Tất cả action recheck backend khi xác nhận. Đọc task không tự mở tiền/hợp đồng.
Fixture có thể cấp rõ HEAD các capability mục tiêu; title/group không tự sinh quyền.

Lifecycle tracking/executing/paused/ended là thông tin quản trị. Đổi cần status
grant, reason, expected version, key; từ ended cần reopen riêng. Không tác động
hợp đồng/BASE/hiệu lực. Tiến trình gói tracking→participating→awaiting_result,
có thể điều chỉnh từng bước với lý do. Outcome unknown/won/lost/cancelled/
not_participating độc lập; không đổi gói khác hoặc project và không sinh contract.
Giữ nguyên submitted = khai báo nộp chưa xác minh.

Nhật ký `tp.project.update`: append-only actor/time/project/package/before/after/
reason/version/key/hash/correction. Khoá project trước kiểm version và retry.
Cùng key/cùng payload trả event cũ; payload khác hoặc stale bị chặn. Không gửi mail.
Ghi chú sau submitted là event riêng; không sửa CRM căn cứ. Vì chưa có classification
nội dung granular, nhật ký thương mại đọc/ghi theo financial_read và assignment;
metadata status không chứa reason khi actor thiếu tiền. Đây là giới hạn có chủ ý,
không cấp tiền support để mở nút. Ghi chú tự do vẫn cần quy tắc không ghi số tiền
vào metadata hoặc task; hệ thống không quét để cam kết an toàn văn bản tự do.

Giá riêng `tp.bid.package.amount`: package_total/company_offer/company_share,
amount_state unknown/estimated, currency/tax_basis/source/estimate_date. Không đổi
expected_revenue thành giá gói; không có tổng cộng khác currency/basis. Zero ước tính
khác unknown. Domain read/search/group/export giữ financial_read + assignment;
ghi cần bid prepare + owner + financial_draft_edit. Khóa dòng và kiểm version trước sửa, lưu before/after vào nhật ký project. Unknown xóa giá trị số về0 nhưng hiển thị Chưa xác định; estimated0 vẫn có nghĩa riêng. Descriptor recheck cached value.

Task/WBS giữ `project.task` và native keys. Wizard tạo/sửa cấu trúc dùng wbs;
giao người dùng task_assignment; progress đòi task_progress và chính assignee.
Chỉ các key 01_in_progress/04_waiting_normal/1_done; không duyệt/hủy/NT/thanh toán.
Generic write/create rule hiện hành không mở. Source/target parent/project và
assignee active kiểm riêng, expected write_date+version, row lock, event/retry.
Không notification cho follower ngoài scope. Mỗi task chỉ một ID ở hai góc nhìn. Event task giữ JSON trước/sau name, parent, assignees, responsible, deadline, deliverable, description, state; snapshot bất biến sau thay đổi tiếp theo.

Migration tự động chỉ thêm schema/default tracking (thông tin theo dõi, không suy
đang thực hiện/kết thúc); giữ link/owner/reviewer/file/grant/account cũ.
Không đủ căn cứ gói/investor: giữ NULL và đưa CRM chưa gắn gói vào Cần đối chiếu.
Mapping operator-only tại migration_mapping.py theo ID/source/verifier explicit; chưa có mapping dữ liệu thật được duyệt nên delta thật rỗng. Utility hỗ trợ project-only/giao trực tiếp không gói giả, chặn thiếu bên ký/cross-company/khác commercial partner hoặc thay link cũ. Dry-run không ghi; apply khóa CRM, revalidate rồi journal đúng field delta; rollback chỉ field delta nếu giá trị còn khớp after, từ chối xung đột. Odoo tests đã kiểm nonempty apply lặp, rollback chính xác/lặp và direct không sinh gói. Xem [migration/rollback](../demo/KD_PROJECT_RESTRUCTURE_001_MIGRATION_RUNBOOK.md).


## Native UI và guard cuối

`action_management`/`action_governance` và management_form/governance_form cùng
project.project ID. Bộ chọn dùng key theo database/user; chuyển góc nhìn giữ ID.
Management chỉ query task/hạn/đầu ra, governance đối chiếu7nguồn và gói/cần đối
chiếu. Không tổng tiền giả hoặc tỷ lệ hoàn thành dự án. Old project_form/action
vẫn có đường chuyển; dashboard/review_document/open_records mở đúng góc quản trị.

Message.create resolve cả context defaults và kiểm actor parent CRM; attachment
lần về CRM trực tiếp hoặc qua mail.message ở ORM/search/export/binary/thumbnail.
Relink kiểm nguồn và đích. Submitted và thiếu quyền tiền bị chặn; server tracking
chỉ dùng sentinel object nội bộ từ private _message_log_batch, không phải flag RPC.
Package.create kiểm cả default_stage/default_outcome trước ghi, không nhập kết quả
qua context để né command. Xem [acceptance](../demo/KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md)
để biết test thực và tình trạng hậu kiểm độc lập. Source clone không tự là source dev.


Correction hậu kiểm cuối: attachment.create kiểm effective public/access_token
kể cả context default; public/portal không đọc nội dung CRM trực tiếp hoặc qua
mail.message bằng public/token cũ. Test tái hiện trước sửa3fail/1, sau sửa1/1;
independent29sharing+A06 thêm7assertion chứng minh denied/allowed/no side effect.
Không đổi quyền của model ngoài CRM. Trong list native, breadcrumb giữ trang/sort;
browserBack nay cũng giữ trang/sort qua hook globalState của action (key/limit/offset/orderBy), không lưu domain/nội dung riêng. Reload bỏ facet tạm; dùng Favorites để lưu filter.


## S4 — đã áp exact source trên dev

CHG-20261109-014: source20.0.1.8.0 đã áp dev18069 sau full185/HOOT20,
UI61+extra10+native pagingBack29, audit quyền độc lập110 và backup mới131132Z/
restore131138578table295attachment. Source test=seal=applied89c17f…f927.
83table4529oldrow/auth/config/module giữ qua upgrade và smoke53checks/5login.
Không mapping thật, các model nghiệp vụ mới0row; không cấp grant hoặc đổi owner
người thật. Technical verified không tự là business/visual/pilot hoặc duyệt V2.
