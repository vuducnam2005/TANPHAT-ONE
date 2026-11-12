# KD-ACCESS-002 — Quyền trước và sau

**Bổ sung HR-ACCOUNT-ROLE-001, 12/11/2026:** admin đúng company có adapter
staff ↔ HEAD KH-KD tại hồ sơ HR, tái sử dụng model trách nhiệm và policy HEAD
bên dưới; không nới quyền nghiệp vụ. Preview/lý do/audit/snapshot, guard hạ role
và session revocation xem [quy tắc HR](HR_ACCOUNT_ROLE_001_SECURITY.md).

## KD-HEAD-001 — Delta HEAD đã xây dựng, 10/11/2026

DEC-033 và [prompt KD-HEAD-001](../prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md)
cho phép thay riêng quyền HEAD. Phần này mô tả delta đã áp dev18069 sau kiểm thử;
**technical verification đạt và dev đã hoạt động**, xem
[acceptance KD-HEAD-001](../demo/KD_HEAD_001_ACCEPTANCE.md). Verdict dựa trên full211, source seal và preservation của batch này. Bốn vai còn lại giữ policy hiện hữu;
toàn bộ V2, business acceptance và pilot chưa được duyệt bởi delta này.

HEAD được xác định bằng `tp.kd.department.role`: user ID, company, department,
active, ngày bắt đầu/kết thúc và lý do. Backend tính scope động cho mọi project
`tp_managed` cùng company/phòng, kể cả phát sinh mới; CRM trước project theo
team KH-KD active đúng company/phòng. Không suy scope từ tên, chức danh, cùng
pháp nhân hoặc danh sách tám dự án mẫu. Hồ sơ thiếu scope không tự được mở.
Thu hồi/hết hạn role được kiểm lại khi đọc/query/export/file và xác nhận action.

| Nghiệp vụ | HEAD trong scope động | Guard còn giữ |
| --- | --- | --- |
| Tổng quan, R01–R06, Excel | Đọc metadata/tiền, lọc/nhóm/mở nguồn/xuất theo nguồn được cấp | ORM cùng scope; unknown khác0; không cộng lẫn currency/basis hoặc phụ lục vào giá trị hiệu lực |
| Project, gói/lần tham gia | Tạo dự án; sửa thông tin, các bên, trạng thái/ghi chú và phân công qua action | Mã/company/phòng, lý do, version/row lock/retry; trạng thái theo dõi không là BASE/trúng thầu/hiệu lực |
| WBS/task | Tạo/sửa/cấu trúc/giao lại/cập nhật tiến độ thay người thực hiện | Người thực hiện giữ riêng actor; chỉ trạng thái backend hỗ trợ, audit trước/sau; không generic write rộng |
| CRM gắn project hoặc trước project | Lập/sửa nháp của mình/người khác, tiền nháp, khai báo nộp, phân công | Lý do và phiên bản khi can thiệp; submitted khóa căn cứ/phạm vi; receiver trước project phải có scope owner/team hiện hành |
| Contract/revision | Lập/sửa tiền và metadata nháp, gửi/gửi lại, phân công trách nhiệm, nhận reviewer/trả bản khác | Giữ workflow draft/in_review/returned, optimistic version/idempotency và bốn mắt cùng vòng gửi; không BASE/ký/hiệu lực |
| Bảy typed dossier | Lập/sửa/gửi/mở sửa, phân công owner/reviewer, nhận reviewer/trả hồ sơ người khác | Scope/capability/state/source; owner khác reviewer; người gửi/người can thiệp nội dung cùng vòng không tự review |
| Tài liệu/trao đổi | Đọc/tải/preview, thêm hoặc lưu trữ file nháp, ghi trao đổi CRM bằng command | Lý do/version, actor/checksum/audit; giữ bytes; file thuộc lần gửi khóa cả sau mở sửa; public/token/relink/direct mutation bị chặn |
| Đối tác nghiệp vụ | Tạo/cập nhật trường nghiệp vụ qua command dự án | Không CRUD danh bạ toàn hệ thống hoặc ngân hàng/thuế; tùy chọn cá nhân an toàn giữ theo native |
| Quản trị quyền/HR/kế toán/pháp lý | Không mở từ role HEAD | Không Settings/admin, HR nhạy cảm, posting/paid, duyệt BASE, ký/hiệu lực hay tự cấp grant |

Can thiệp nháp lưu actor/thời gian/lý do/version và snapshot trước–sau; tiền
lưu ở model riêng theo quyền tài chính. Contract có `business_owner_id`, khác
`create_uid`; backfill chỉ khi có duy nhất actor audit tạo hợp đồng/phụ lục,
legacy không đủ căn cứ giữ trống. Nhận reviewer dùng action có audit: contract
giữ `submission.reviewer_id` gốc, dùng `assigned_reviewer_id` hiện hành cho
action/hộp việc/R01/R05; typed giữ reviewer cũ trong snapshot. Sau `begin_rework`
hoặc typed `rework`, lượt nội dung mới được xét riêng; chuyển owner không xóa
dấu người đã can thiệp của cùng lượt.

Picker chỉ hiển thị người nhận hợp lệ và backend kiểm lại lúc xác nhận. Giao
owner/reviewer/assignee không tạo assignment/grant mới cho người nhận. Đặc biệt,
membership team không tự làm nhân viên có quyền nhận CRM trước project nếu
policy owner/team hiện hành chưa cho phép.

Delta provisioning được định danh và journal private: **ngừng active96dòng
legacy của riêng HEAD** (8assignment +16project grant +72KD grant), tạo **1role
phòng +1event tạo role**, giữ dòng cũ để đối chiếu/hoàn tác. Đây là delta dự kiến
cho apply đã được giao; số thực clone/dev và kiểm bảo toàn bốn tài khoản còn lại
phải đối chiếu acceptance, không nhận mô tả này là bằng chứng đã provision dev.
Không đổi mật khẩu/MFA/passkey hoặc owner/reviewer hồ sơ hàng loạt để mở quyền.

## Baseline lịch sử KD-ACCESS-002 và KD-PROJECT-RESTRUCTURE-001

Các số liệu và test dưới đây được giữ làm lịch sử. Cột HEAD/phạm vi8dự án và
các dòng NI không mô tả delta HEAD ở phần trên; bốn cột vai khác không được
delta này thay quyền.

**Cập nhật CHG-20261109-014:** F1–F3 và public/token-default correction đã hậu kiểm độc lập110assertion trên runtime trước áp; source exact20.0.1.8.0 đã lên dev. Xem acceptance của KD-PROJECT-RESTRUCTURE-001. Policy người thật/V2 vẫn giữ. Đoạn dưới là cảnh báo lịch sử trước correction.

**Hậu kiểm CHG-20261109-004:** ma trận dưới đây mô tả policy dự kiến/cấu hình.
Các dòng CRM file/chatter chưa được enforce đầy đủ trên mọi đường native:
F1–F3 đã xác nhận ở [báo cáo audit](../reviews/KD_ACCESS_002_INDEPENDENT_AUDIT.md).
Không hiểu M/P hoặc chữ Khóa là bảo đảm bảo mật đã nghiệm thu; phải correction
và hậu kiểm lại. Project/WBS NI vẫn đúng, không phải lỗi thiếu group manager.

Scope giữ nguyên: head8, deputy4, project_lead4, planning4, support2 dự án registry
KD_NATIVE_001_REALISTIC_V1. Đây là cấu hình dev minh họa theo yêu cầu trực tiếp,
không là bổ nhiệm nhân sự/Q2/pilot hoặc thẩm quyền ký của doanh nghiệp.

R: đọc theo scope; P: lập/sửa nháp của chính mình; S: gửi riêng; V: trả hồ sơ
của người khác khi chính mình được chỉ định reviewer; M: đọc tiền; E: sửa tiền
nháp cần grant riêng. Không có nghĩa một chữ bao hàm các chữ khác.

| Model / thao tác | head | deputy | project_lead | planning | support | Điều kiện / phân loại |
| --- | --- | --- | --- | --- | --- | --- |
| CRM trước batch | Không | Không | Không | Không | Không | Thiếu ACL/capability chuyên môn; guard cũ chưa đủ |
| crm.lead list/detail/search/name_search | R | R | R | R | R | Company và project assignment; trước dự án chỉ owner trong team KD được giao, cùng đơn vị có capability |
| crm.lead create/write/prepare | P | P | P | P | P | Owner hiện tại, grant prepare còn hạn; identified/preparation; fields cho phép. Không sửa draft người khác |
| crm.lead action_kd_record_submission | S | S | S | S | Không | Submit tách prepare; owner, preparation, route bid, căn cứ; direct không nộp thầu |
| crm.lead submitted evidence/scope | Khóa | Khóa | Khóa | Khóa | Khóa | Không đổi trực tiếp state/import/context; action có row lock/history native |
| crm.lead owner/company/team/project transfer | Không | Không | Không | Không | Không | Cần action phân công riêng; không clear project/owner để thoát scope |
| CRM native money/derived/export/query | M | M/E | M/E | M/E | Không | financial_read + assignment; E thêm financial_draft_edit + own draft; trước dự án chưa cấp tiền |
| CRM money domain/order/group | M | M | M | M | Không | Query tiền chỉ tính project có financial_read; metadata của scope khác không bị dùng suy tiền |
| CRM file/chatter nội dung | M | M | M | M | Không | Parent read + quyền tiền; hiện chưa có phân loại/redaction granular CRM. Không hứa lọc free text |
| CRM file mutate/delete/share | P* | P* | P* | P* | Không | *Owner + prepare + financial_read, chưa submitted; không relink/public/token |
| crm.activity.report | Không | Không | Không | Không | Không | Native report cũ không chứng minh exact scope, cố ý chặn; báo cáo metadata KH-KD dùng nguồn ORM scoped |
| project.project read | R | R | R | R | R | Assignment reader đúng company; ngoài scope bị chặn cả relation/export |
| project.project create/edit | NI | NI | NI | NI | NI | NOT_IMPLEMENTED action ghi scoped; không cấp manager |
| project.task read/subtasks | R | R | R | R | R | Project assignment; task không project không tự public cho staff |
| project.task create/edit/assign/WBS | NI | NI | NI | NI | NI | NOT_IMPLEMENTED actor/field/action scoped; TASK-001 riêng |
| tp.contract/revision metadata | R/V | R/P/S/V | R/P/S/V | R | R | V đúng reviewer khác owner; P own draft; optimistic version/idempotency/reason giữ |
| tp.contract amount/snapshot/document | M | M/E | M/E | M/E* | Không | *planning giữ grant tiền cũ, không tự có contract_submit; general file theo phân loại cũ |
| tp.allocation | R/V/M | R/P/S/V/M/E | R/P/S/V/M/E | R/P/S/M/E | R | Giao khoán; exact owner/reviewer/version/reason |
| tp.production | R/V/M | R/P/S/V/M/E | R/P/S/V/M/E | R/P/S/M/E | R | Sản lượng; nguồn/scope/amount guard cũ |
| tp.acceptance | R/V/M | R/P/S/V/M/E | R/P/S/V/M/E | R/M | R | planning/support không prepare/submit/review |
| tp.payment.request | R/V/M | R/P/S/V/M/E | R/P/S/V/M/E | R/M | R | Không posting/paid/thực chi |
| tp.periodic.plan | R/V/M | R/P/S/V/M/E | R/P/S/V/M/E | R/P/S/M/E | R | Kỳ/nguồn/đối chiếu cũ giữ |
| tp.credential | R/V | R/P/S/V | R/P/S/V | R/P/S | R/P | Organization trong scope; person còn owner/reviewer restriction; support không S/V |
| tp.obligation | R/V | R/P/S/V | R/P/S/V | R | R | Không tự cấp ký/hiệu lực/BASE |
| Tổng quan/Báo cáo KH-KD | R/M | R/M | R/M | R/M | R | KPI/query scope theo ORM; nút create phản ánh capability |
| Metadata export | R | R | R | R | R | Bổ sung chức năng export native cho nhóm scoped; field/record/file guards vẫn áp dụng |
| Tài khoản/Tùy chọn | Chính mình | Chính mình | Chính mình | Chính mình | Chính mình | Native preferences; không editor group/Settings |
| User/grant/HR/accounting admin | Không | Không | Không | Không | Không | Cố ý không cấp, không là gap |

Delta đã áp dev:42grant opportunity (head16, deputy8, lead8, planning8, support2),
1team native gồm đúng5user để owner chuẩn bị trước dự án, và export capability
native cho group scoped. Native membership tự tính `sale_team_id` từ trống sang
team mới cho đúng5user; đã journal và kiểm hoàn tác. Mọi cột tài khoản khác,
password/TOTP và project grant/assignment/owner/reviewer hồ sơ cũ giữ nguyên.
Dấu vết kỹ thuật `write_uid/write_date` do ORM có thể đổi và được tách khỏi
đối chiếu nội dung; không bỏ qua cột password hoặc cấu hình bảo mật.
Kết quả thực ở [acceptance](../demo/KD_ACCESS_002_ACCEPTANCE.md).


## Capability triển khai trên test — KD-PROJECT-RESTRUCTURE-001

Bản riêng20.0.1.8.0 bổ sung project_metadata/project_status/project_note/project_reopen/bid/wbs/task_assignment/task_progress. Tất cả cần assignment và grant prepare còn hiệu lực, đúng company/department; task_progress còn là assignee. Tiền vẫn financial_read/financial_draft_edit riêng; note thương mại cần đọc tiền. Không suy quyền từ chức danh hoặc task. Project create chung chưa mở. WBS/task dùng command/version/lock/retry/snapshot, không generic assignee write.

Đây là implementation được kiểm bằng fixture; các dòng NI và quyền người thật trên dev ở ma trận trên chưa được thay. V2/TASK-001 vẫn chưa được tự duyệt; không đổi grant/password/owner/reviewer5actor để làm UI xanh. F1–F3 đã có correction/hậu kiểm110assertion trên clone và áp exact source lên dev, kết luận theo scope phải xem [acceptance](../demo/KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md), không nhận test clone là sửa dev.
