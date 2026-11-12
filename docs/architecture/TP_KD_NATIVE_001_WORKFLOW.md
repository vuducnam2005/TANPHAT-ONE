# KD-NATIVE-001 — Phạm vi quản trị hồ sơ tổng hợp

## Delta HEAD KD-HEAD-001 — source bản riêng ngày10/11/2026

DEC-033 cho phép HEAD quản lý nghiệp vụ toàn phòng. Đoạn này thay giới hạn
owner-only/assignment cố định của **riêng HEAD** trong các baseline lịch sử
bên dưới. Bốn vai còn lại giữ nguyên quyền. **Full211/211 và áp dev18069/preservation đã đạt**, xem [acceptance](../demo/KD_HEAD_001_ACCEPTANCE.md)
và [ma trận](../security/KD_ACCESS_002_ROLE_MATRIX.md). Source/test không tự là
nghiệm thu nghiệp vụ/pilot hoặc thẩm quyền BASE/ký/hiệu lực/thực trả.

`tp.kd.department.role` xác định user/company/phòng, active, thời hạn và lý do.
Project managed hiện tại/phát sinh mới đúng company/phòng thuộc scope động;
CRM trước project theo team active đúng company/phòng, không dùng project giả.
Backend kiểm role hiện hành ở query/tiền/file/export và action, kể cả sau thu
hồi trong phiên đang mở. Bộ chọn chỉ lọc ứng viên, không thay kiểm tra backend.
Phân công không cấp grant: người nhận vẫn phải có quyền hiện hành đúng scope.
Team membership riêng lẻ không đủ cho nhân viên nhận lead trước project.

### Typed dossier và contract

Áp dụng bảy model `tp.allocation`, `tp.production`, `tp.acceptance`,
`tp.payment.request`, `tp.periodic.plan`, `tp.credential`, `tp.obligation` và
contract/revision hiện có; không thêm state chung hoặc action duyệt pháp lý.

| Thao tác HEAD | Điều kiện và kết quả |
| --- | --- |
| Sửa/gửi/mở sửa nháp người khác | Đúng scope/capability/state; reason khi can thiệp nháp của owner khác; giữ owner, actor thật, thời gian, version, metadata và tiền trước–sau |
| Phân công owner/reviewer | Command có reason/version/row lock/audit; người nhận active, cùng scope, có capability; không đổi company/project hoặc tạo grant để qua kiểm tra |
| Nhận vai reviewer | HEAD đủ quyền và độc lập nội dung; command audit reviewer trước–sau, không mạo danh reviewer cũ |
| Trả hồ sơ | Chỉ reviewer hiện hành, đúng version, lý do bắt buộc; không sửa snapshot lần gửi |
| Gửi lại sau mở sửa | Giữ submission/event cũ; tạo snapshot lần gửi mới và fix summary theo workflow hiện có |

Typed giữ owner khác reviewer; người gửi và người HEAD đã sửa nội dung/tài liệu
của vòng hiện tại không tự review. Dấu người can thiệp và owner cũ được giữ khi
phân công. Ranh giới vòng mới là event `rework` gần nhất. Contract chặn người
gửi và HEAD can thiệp nội dung cùng vòng; sau bàn giao vẫn giữ dấu owner cũ và
actor nội dung theo audit. Ranh giới là `begin_rework`; việc
chuyển trách nhiệm đơn thuần không xóa audit nội dung trước đó. Mở vòng mới
cho phép người đủ quyền độc lập với nội dung vòng mới nhận rà soát.

Contract có `business_owner_id` trên revision; bản mới lấy actor nghiệp vụ.
Migration chỉ backfill khi duy nhất actor từ audit `create_contract`/
`create_amendment`, legacy thiếu căn cứ giữ NULL; không lấy `create_uid` làm
owner. `submission.reviewer_id` vẫn là reviewer gốc bất biến;
`assigned_reviewer_id` là người hiện hành sau nhận reviewer có audit. Action,
R01/R05 và inbox dùng người hiện hành; item rời inbox reviewer cũ. Typed lưu
reviewer cũ trong snapshot event. Không thêm REST route hoặc đổi contract API
để mở các command native này.

### File và trao đổi nháp

Typed dùng `tp.kd.document`, contract dùng `tp.contract.document`, đều phân
general/financial và giữ file/name/checksum/actor/time/version/reason. Thêm và
lưu trữ qua command có reason, expected version, row lock và audit; tối đa20MB.
Lưu trữ ngừng hiển thị hiện hành, giữ bytes/căn cứ; không unlink để làm sạch.
File đã thuộc lần gửi hoặc bản khóa tiếp tục bất biến sau trả/mở sửa. File mới
thêm vào nháp rework được lưu trữ khi chưa thuộc lần gửi tiếp theo. Tiền và file
financial vẫn dùng guard riêng; parent access gồm restriction của chứng chỉ.
Read/export/binary/token/public/mutation/relink đều kiểm backend, không nhận
context bool của RPC làm đường nội bộ.

CRM đọc tài liệu cả trực tiếp trên lead và qua `mail.message`; HEAD thêm/lưu
trữ qua command có reason/version, actor/checksum/audit, giữ bytes. Ghi trao đổi
lưu actor partner thật, escape nội dung và không gửi follower notification.
Form/chatter của HEAD chỉ đọc nội dung, dùng nút command để ghi; submitted
khóa file/trao đổi như căn cứ hiện có. CRM còn coarse theo parent+quyền tiền,
không cam kết phân loại free text bằng từ khóa.

Provisioning được journal riêng, dự kiến ngừng active96dòng legacy chỉ HEAD
(8assignment+16project grant+72KD grant), thêm1role phòng+1event tạo role;
không xóa lịch sử hoặc đổi bốn actor khác. Kết quả clone/dev phải ghi theo
acceptance và đối chiếu auth/config/owner/reviewer; không suy apply từ tài liệu.

## Baseline và kết quả lịch sử KD-NATIVE-001/KD-ACCESS-002

**KD-ACCESS-002, 09/11/2026:** batch quyền theo yêu cầu trực tiếp thay giới hạn
CRM của KD-ACCESS-001; [ma trận](../security/KD_ACCESS_002_ROLE_MATRIX.md) và
[kết quả thực](../demo/KD_ACCESS_002_ACCEPTANCE.md). Read theo assignment/company;
prepare/submit độc lập và owner-only, submitted khóa căn cứ/phạm vi; pre-project
dùng team KD cùng đơn vị và owner, có capability hiện hành, không dự án giả.
Tiền CRM native/derived/query/export kiểm financial_read; sửa cần thêm draft-edit;
file/chatter CRM còn coarse theo quyền tiền+parent. Không tự redaction free text.
Download token/public cũng kiểm parent của actor scoped trước native sudo;
write/file mutation khóa cùng row cơ hội với action khai báo nộp. Native team
cho trước dự án tự tính main team của5user; delta được journal và hoàn tác
membership cùng grant, không đổi password hoặc quyền sales.
Không mở Project-create/WBS-write/BASE/ký/hiệu lực/posting/paid/grant-admin.

**KD-ACCESS-001, 08/11/2026 — CHG-20261108-003:** theo yêu cầu trực tiếp,
năm tài khoản dev phân vai được provision trên đúng dataset minh họa, sau clone
và backup. Nhóm `group_scoped_staff` có restriction Project/Task riêng theo active
assignment/company; không cấp manager/all-leads. Head8/deputy4/project_lead4/
planning4/support2 dự án; grant chuẩn hiện có, owner/reviewer không đổi. CRM bị giữ
chưa mở vì prepare gộp khai báo nộp và chưa enforce owner/tiền theo ma trận;
project creation/WBS write vẫn chưa cấp. Đây là quyền demo dev, không thay Q2/
bổ nhiệm người thật/BASE/ký/hiệu lực/pilot. [Acceptance](../demo/KD_ACCESS_001_ACCEPTANCE.md)
và [hướng dẫn](../demo/KD_ACCESS_001_USER_GUIDE.md) là bàn giao của batch.

Ngày 06/11/2026. Người dùng trực tiếp cho thực thi prompt CHG-006, thử clone trước dev18069. Quyền này cho hồ sơ tổng hợp/actor fixture; không xác nhận Q2 người thật, policy ký/BASE/hiệu lực/thanh toán hoặc pilot. Không thay TASK-001.

## A/B — Nguồn hiện có

CRM dùng `crm.lead`, cùng khách hàng và dự án qua `tp_crm_project_bridge`. Trạng thái bổ sung là tình trạng chuẩn bị hồ sơ: `identified` → `preparation` → `submitted` (đã khai báo nộp, chưa xác minh). Giao trực tiếp dừng ở chuẩn bị, không có receipt đấu thầu giả. Chuẩn bị cần nguồn/phạm vi/hạn/checklist; khai báo nộp cần căn cứ ghi chú nội bộ. Không phát sinh kết quả trúng thầu, ký hoặc hiệu lực.

Hợp đồng dùng nguyên sáu action của UI001a/CTR002a và grant cũ. WBS dùng `project.task`; chỉ manager hiện hành có quyền ghi managed-task, thêm liên kết hợp đồng và đầu ra, không cấp write cho assignee.

## Quyền fixture cho hồ sơ mới

`tp.kd.grant` là capability kỹ thuật theo project + phòng chủ trì + domain + user; `prepare`, `submit`, `review` riêng, có active/date_end/reason. Chỉ superuser vận hành fixture được cấp; không menu quản trị quyền. Mọi lần dùng quyền kiểm project readable, allowed company, assignment active và grant hiện tại. Không suy từ owner, title hoặc group manager. Grant tiền tiếp tục dùng `tp.project.grant` hiện hành; metadata và số tiền lưu tách.

## C1 — Hồ sơ giao khoán (đặc tả triển khai)

Model `tp.allocation` riêng cho khoán nội bộ/thầu phụ, không tạo sale/purchase hoặc pháp nhân mới. Mã unique theo company, project, owner, department, ngày/kỳ/hạn, phạm vi, hợp đồng nguồn, task, bên nhận nội bộ/đối tác, cấp1/cấp2 qua parent. Parent cùng project/company/contract; cấm vòng lặp, scope con phải thuộc nguồn; vượt giá trị cha chỉ cảnh báo khi cùng currency/basis đã xác nhận, chưa hard-block Q7. Tổng công ty chỉ lấy cấp1; phụ lục là snapshot hợp đồng, không cộng lại vào tổng giá trị.

| Từ → đến | Actor | Guard / kết quả |
| --- | --- | --- |
| Mới / sửa → draft | prepare đúng scope, owner được giao | Target/source FK readable; company/project nhất quán, ngày hợp lệ; không nhận state/version/history client |
| draft → in_review | submit, người lập/owner | Nội dung/phạm vi/nguồn/owner/reviewer khác sender đủ quyền; snapshot lần trình và version bất biến; thông báo nội bộ không email |
| in_review → returned | reviewer được chỉ định + review hiện tại | Reason bắt buộc; version đúng; snapshot giữ nguyên, actor/time/outcome append-only |
| returned → draft | owner + prepare | Reason bắt buộc; mở bản sửa giữ lần trình cũ; không sửa bản đã gửi bằng write |
| draft (đã sửa) → in_review | owner + submit | Fix summary bắt buộc khi đã bị trả; snapshot mới; lần trình trước không đổi |

Action không cho target/state/payload tùy ý từ RPC; UI mang expected version và key của wizard do server tạo. Lock row trong transaction; key/payload đã dùng trả kết quả cũ, key khác payload từ chối, stale version không ghi/audit một phần. Direct write state/owner/project/company/version lịch sử bị chặn theo state và capability. Nháp chỉ unlink khi policy cho và không có lịch sử/tham chiếu; bản đã gửi giữ lại, archive nếu được triển khai rõ semantics.

Tiền ở model riêng theo đúng domain; quyền đọc đòi project readable + assignment + grant financial_read hiện tại. Sửa tiền thêm financial_draft_edit; không related/compute/store/chatter lộ tiền cho metadata-only. Unknown có trạng thái riêng, không đổi thành0. Snapshot tiền nằm ở model có cùng restriction; revoke/expiry áp dụng cả lịch sử/count/export. Không có upload/file tài chính mới trong slice.

Test C1 trước bàn giao: dương nháp/gửi/trả/mở sửa/gửi lại; actor thiếu grant/self-review/mất assignment/revoke/expiry/cross-company/FK/scope/cycle; reason/stale/replay; snapshot không đổi; metadata không đọc/search/count/export tiền; cấp2 không cộng tổng. Browser create ngoài seed và persistence/390/768/1440 riêng test/dev.

## C2/C3/C4/D

Các đặc tả C2–D3 bên dưới được bổ sung trước từng lô triển khai. Đến CHG-20261106-017, các lô đã được kiểm trên clone và tích hợp dev18069; kết quả theo từng nhóm nằm trong [ma trận nghiệm thu](../demo/KD_NATIVE_001_ACCEPTANCE.md), chưa phải audit độc lập. Sản lượng không là nghiệm thu; hồ sơ nghiệm thu nội bộ không là biên bản ngoài; đề nghị khác paid/posting, tạm ứng không bắt nghiệm thu giả. Kế hoạch không là doanh thu kế toán; chứng chỉ tổng hợp không là chứng chỉ pháp lý. Báo cáo chỉ từ nguồn và quyền thật, thiếu nguồn giữ unknown.

## C2 — Sản lượng theo kỳ (đặc tả trước triển khai)

`tp.production` dùng helper review C1, state riêng draft/in_review/returned; cùng guard scope/owner/reviewer/version/lịch sử/tiền. Nguồn hợp đồng bắt buộc, khoán/task tùy chọn nhưng cùng project/contract. Kỳ bắt buộc, khối lượng không âm, đơn vị rõ, tỷ lệ hoàn thành0–100; tình trạng đối chiếu chỉ chưa đối chiếu/cần bổ sung. Không action xác nhận nghiệm thu. Snapshot giữ nguồn, kỳ, đơn vị, khối lượng và tình trạng đối chiếu tại lần trình; tiền riêng. Từ hồ sơ mở khoán/hợp đồng/dự án theo quyền; project có action tạo/mở sản lượng. Test workflow hai actor, stale/retry/return reason kế thừa và bổ sung sai nguồn/kỳ/khối lượng/snapshot/metadata-money.

## C3 — Hồ sơ đợt nghiệm thu (đặc tả trước triển khai)

`tp.acceptance` có state riêng draft/in_review/returned và workflow2actor/version/snapshot C1. Hợp đồng, sản lượng nguồn, mã đợt, bên nhận hồ sơ, đơn vị và khối lượng/phạm vi/kiểm kê căn cứ bắt buộc. Nguồn cùng company/project/contract; kỳ nằm trong kỳ sản lượng, ngày hồ sơ không trước nguồn; đơn vị trùng, khối lượng0–nguồn. Không kết luận biên bản ngoài hoặc chuyên môn đã xác nhận. Mở nguồn sản lượng/project theo quyền; chặn đổi nguồn sản lượng làm sai hồ sơ downstream. Tiền tách riêng; test hai vòng trình, stale/retry/guard source/kỳ/khối lượng, reader không tiền.

## C4 — Đề nghị thanh toán/đối chiếu (đặc tả trước triển khai)

`tp.payment.request` typed, cùng workflow C1 với state riêng. Chiều thu/chi và căn cứ tạm ứng/nghiệm thu tách biệt. Tạm ứng bắt buộc mô tả căn cứ, không đòi nghiệm thu; theo đợt bắt buộc acceptance cùng contract/project và ngày không trước nguồn. Đối tác, hợp đồng, hạn dự kiến, checklist hồ sơ và đối chiếu chưa đủ/cần bổ sung/đã kiểm nội bộ rõ ràng. Tiền đề nghị nằm model riêng, không có paid/approved/posting. Mở nghiệm thu/hợp đồng và tài liệu nguồn qua quyền hiện có; không thêm upload. Bảo vệ thay nguồn downstream, snapshot cả căn cứ/checklist; test luồng hai actor, source sai/thiếu, tạm ứng không nghiệm thu, phiên cũ và quyền tiền.

## D1 — Kế hoạch định kỳ (đặc tả trước triển khai)

`tp.periodic.plan`: cùng scope/actor review C1, state riêng draft/in_review/returned; kỳ month/quarter/year đúng ngày đầu-cuối lịch, unique project/kind/kỳ. Một hồ sơ có hai mục tiêu tiền tách measure production/revenue, unique(record,measure), snapshot giữ measure và quyền tiền. Không cộng tháng/quý/năm chung. Đối chiếu sản lượng chỉ lấy hồ sơ in_review cùng project có kỳ nằm trọn kỳ kế hoạch; unknown/mixed currency/basis/không nguồn phải hiện chữ khác0. Drilldown cùng domain của compute. Chưa có bridge chứng từ ghi sổ được xác minh thì doanh thu thực hiện là chưa có chứng từ, không lấy đề nghị hay nghiệm thu làm revenue. Test kỳ/duplicate, snapshot2measure, quyền và tổng/drilldown đúng state/currency/basis/unknown.

## D2 — Năng lực/chứng chỉ (đặc tả trước triển khai)

`tp.credential`: metadata hồ sơ năng lực tổng hợp của tổ chức/cá nhân, project/owner/reviewer và workflow riêng draft/in_review/returned. Subject giả qua res.partner, loại/phạm vi, thời gian hiệu lực/hết hạn và ghi chú nguồn chưa xác minh; không phát hành file chứng chỉ hoặc chữ ký. Tổ chức theo project reader; cá nhân chỉ owner/reviewer trong project theo restriction backend. Theo dõi quá hạn/còn30ngày minh họa bằng ngày hiện hành. CRM chọn nhiều hồ sơ có quyền và cùng project; backend kiểm IDs trong command, không cho create/unlink hồ sơ qua field M2M. Credential mở cơ hội đang sử dụng bằng action source có quyền. Test phạm vi/cá nhân/liên kết M2M giả mạo/ngày, browser tạo/sửa và mở nguồn.

## D3 — Nghĩa vụ, báo cáo và hộp việc (đặc tả trước triển khai)

`tp.obligation` theo project/hợp đồng, loại nghĩa vụ và checklist; trạng thái checklist missing/collecting/internal_checked không xác nhận thanh lý. Cập nhật checklist nháp cần lý do và append event, gửi/rà soát dùng workflow C1. Giữ lại/công nợ không có căn cứ giữ chưa xác nhận, không suy ra số tiền. Báo cáo/Tổng quan dùng cùng transient query helper, count/search/action cùng scope user không sudo; ưu tiên reviewer hiện tại, hồ sơ trả lại của tôi, quá hạn/đến3ngày và chứng chỉ30ngày minh họa. Hợp đồng chỉ đếm revision draft/in_review/returned, không cộng phụ lục vào tiền hiệu lực; nguồn tiền ở từng hồ sơ bảo vệ riêng. Thêm nguồn các domain/project smart buttons và báo cáo tháng cùng bộ lọc. WBS/truyền thông vẫn project.task manager chuẩn; không sửa TASK-001. UI typed ẩn New khi không có prepare grant hợp lệ, readonly khi không phải owner+prepare; backend vẫn là nguồn kiểm quyền. Test count/drilldown đúng nguồn/scope, reason/history và policy staff.

## DATA — Registry và công cụ dữ liệu (đặc tả trước triển khai)

Dataset `KD_NATIVE_001_REALISTIC_V1`, external namespace riêng; registry `tp.kd.dataset`/`tp.kd.dataset.entry` chỉ superuser tooling, không menu cho người dùng. Mỗi stable key ghi owned/referenced, model/id/externalID, category nghiệp vụ hoặc support, checksum và dependency. Reuse công ty, tiền tệ và phòng KH-KD hiện có bằng referenced, không nhận ownership. Seed ORM/action trong một transaction với mail/tracking/enrichment không gửi ra ngoài; actor fixture mới4vai trò, không sửa password hiện có. Lặp chỉ thêm key thiếu nếu externalID/registry đều nhất quán, giữ và báo drift khi người dùng đổi.

Inventory/verify xuất manifest private theo DB,12nhóm/tổng254 theo quyết định người dùng, thiếu6phụ lục do gate review_complete; không tính original revisions/log/grant/support. Cleanup mặc định dry-run, không có SQL write/truncate/cascade hoặc resetstate. Scan các FK/M2M từ model ngoài lô; record drift hoặc ngoại phụ thuộc bị giữ, các upstream liên quan bị chặn. Chỉ unlink draft chưa history theo model policy, không tự archive tài chính hoặc xóa actor/audit; phần có history retained vì các typed dossier chưa có archive semantics. Apply yêu cầu DB+dataset chính xác và chỉ clone trong task này; dev cleanup luôn từ chối. Rehearsal apply trong savepoint clone rồi rollback, đếm unlink/retained thực và kiểm baseline nguyên. Unit/integration kiểm seed2lần, sửa sau seed, password không đổi, registry/manifest/FK, dry-run readonly, external dependency và ownership guard.


## Tích hợp và context điều hướng

Action đổi model phải bỏ form/list/search view reference, default/search_default và active_model/active_id(s) của màn hình cha; chỉ giữ context session/company và default con được action đặt rõ. Nếu giữ form_view_ref dự án, tạo hồ sơ con có thể nạp nhầm form project trên model typed. Kiểm hồi quy từ project context cho10action gồm hợp đồng; không đổi workflow/quyền/API. Tests không import trong addon init khi chạy ứng dụng thường; Odoo tự nạp tests ở test mode.
