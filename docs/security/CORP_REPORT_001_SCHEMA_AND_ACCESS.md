# CORP-REPORT-001 — Schema và quyền triển khai

Ngày 16/11/2026 · CHG-20261116-008. Phạm vi `custom_addons/tp_reporting`, test18079 / `tp_tanphat_test`; chưa áp main18069. Đây là mô tả source và bằng chứng kỹ thuật, không phải quyết định thẩm quyền hoặc nghiệm thu nghiệp vụ.

## Mô hình và nguồn

Identity dùng `res.users`, HR/phòng dùng `hr.employee`/`hr.department`, dự án/công việc dùng `project.project`/`project.task`. Không có database, tài khoản hoặc danh mục nhân viên riêng cho báo cáo. Link nguồn kiểm quyền đọc hiện hành và company; không sửa workflow nguồn, không phụ thuộc quyền KH-KD.

| Model | Nội dung thực tế |
| --- | --- |
| `tp.report.assignment` | User, capability, company, department tùy chọn, subject tùy chọn, level `all/personal/department/company`, ngày hiệu lực, active và lý do. `plan_issue` tách khỏi quyền đề xuất/giao kế hoạch. |
| `tp.report.plan` | Cây quarter→month→week, owner/phòng/project/task, mục tiêu định lượng hoặc đầu ra định tính, allocation/remaining, baseline đầu tiên và baseline_history. Tuần T2–CN được giao tháng nhưng kết quả từng ngày phải nằm phần tháng cha. |
| `tp.report.document` | Hồ sơ unique theo company/cấp/đối tượng/loại kỳ/ngày từ–đến; scope và kỳ khóa sau create. Personal, department, company có cùng cấu trúc nhưng quyền khác. Reviewer được phân công là điều kiện gửi. |
| `tp.report.line` | Nguồn/task/plan, ngày kết quả, contribution_key và stable_key, phần kế hoạch, actual, expected_output, hạn việc, priority, collaborator, work_status, vướng mắc/xử lý và minh chứng. `quantity_known`/`planned_quantity_known` giữ thiếu khác zero; variance chỉ khi cả hai xác định. |
| `tp.report.snapshot` | JSON thường không chứa finance; tên/scope/kỳ/phiên bản, nội dung, mẫu và section, facts, đúng ID/version dependency, reviewer và liên kết bản nhận xét. Chỉ tạo qua workflow; write/unlink bị chặn. |
| `tp.report.event` | Actor, resource/model/id, action, version, lý do, request_key/hash; append only qua workflow. |
| `tp.report.review` | Nhận xét chung/từng line gắn exact snapshot/version/line_key, actor; assessment riêng work_status; published/internal; reply parent và correction_of. Không sửa/xóa nhận xét đã tạo. |
| `tp.report.obligation` / `schedule` | Mẫu số nghĩa vụ, hạn/gia hạn/miễn có lý do; không xóa nghĩa vụ. Lịch có user/kỳ/ngày/timezone/deadline_days, explicit generate và remind; chưa bật cron. |
| `tp.report.template` / `section` / `section.content` | Mẫu versioned, section thứ tự/required/audience, nội dung nhập web; mẫu kỹ thuật chung/Thiết kế/KH-KD/công ty. Nội dung chuyên môn chưa được doanh nghiệp duyệt không thành policy. |
| `tp.report.metric` / `value` | Tiền ở model riêng: definition, unit, flow/stock/milestone, currency/tax, coverage_key, source/evidence, provider/confirmer/status. Không suy receipts/revenue từ payment request. |
| `tp.report.directive` | Report/snapshot/line nguồn, issuer, recipient, hạn, result/evidence, version, request identity và lịch sử; open→in_progress→done. Tạo task project là hành động riêng, không đổi state nguồn. |
| Transient | `tp.report.reason`, `tp.report.copy.plan`, `tp.report.carry.work`: lý do workflow, sao chép cây kỳ mới và chuyển phần việc còn lại; không sao chép actual/xác nhận/trạng thái chốt. |

## ACL Odoo20 và audience

Source workspace dùng **`ir.access`**, không dùng `ir.model.access` hoặc `ir.rule`. `security/ir.access.csv` tách permission theo group và restriction domain toàn cục. `group_reporting_user` là internal user; config và finance là các nhóm bổ sung, không thay assignment nghiệp vụ.

- Quyền đọc company/phòng/subject lấy từ assignment còn hiệu lực trong allowed companies **đang chọn**. Domain nhận rõ `company_ids` từ ir.access, không suy lại company mặc định của user khi safe-eval reset context. Báo cáo company luôn `department_id=False`; assignment có department không mở company dù deep link. Assignment `level` tránh quyền xem bản công ty tự mở báo cáo cá nhân.
- Tác giả đọc hồ sơ mình. Nháp/returned cá nhân không mở cho quản lý ngoài owner; snapshot đã gửi vẫn giữ scope lịch sử và kiểm assignment hiện hành. Line và nội dung section giữ quyền parent. Nháp phòng/công ty chỉ đọc bởi scope được giao; quyền sửa vẫn thuộc người lập.
- Nhân viên đọc kế hoạch mình và tổ tiên **đã ban hành** của việc đã giao, không mở sibling/private plan. Menu phòng/công ty lọc assignment hiện hành; ẩn menu không thay backend restriction.
- Reviewer phải khác tác giả, active, có `review` đúng company/phòng/subject/level và hiệu lực. Review/return chỉ người reviewer được chỉ định. Finalize cần capability riêng; không tự chốt báo cáo personal.
- `published` cho tác giả; `internal` chỉ reviewer được chỉ định trong scope. Reply của tác giả chỉ vào published, không tự đặt assessment hoặc sửa actor/version. Correction giữ tác giả và audience ban đầu.
- Config được quản lý mẫu/lịch/grant. User config thường không tự cấp/sửa grant cho chính mình; superuser kỹ thuật vẫn là ngoại lệ quản trị Odoo, không được mô tả là người duyệt nghiệp vụ. Quyền cấp cho người khác là trách nhiệm cấu hình được giao, chưa có danh sách người thật được cho phép.

Restriction áp trên search/read/count/read_group/name_search và native drill-down; dữ liệu bị cấm không được tải rồi ẩn CSS. Assignment/permission đọc lại khi thao tác, không dùng quyền snapshot làm quyền hiện hành. Snapshot có thể tồn tại sau khi scope bị thu hồi nhưng việc đọc vẫn bị chặn.

## Trường bảo vệ và command boundary

Workflow thông thường chặn state/version/current_snapshot/dependency/baseline/history do RPC ghi trực tiếp. Create chặn state/version và liên kết lịch sử do caller cấp; identity_key được server tính. Owner/company/department/level và ngày/loại kỳ không đổi qua write. Snapshot/event/review bất biến. Source/provenance của rollup/carry giữ sentinel riêng; `readonly` trên view không phải kiểm quyền.

Internal writes dùng **object sentinel** so sánh identity, không nhận được từ JSON/context của người dùng. Provenance sentinel tách khỏi batch x2many, tránh payload nested tự giả origin/stable_key/rollup. Backend không dùng business sudo; SQL chỉ dùng khóa, kiểm tồn tại/quyền membership, batch nghĩa vụ và đóng relation snapshot finance, không đưa restricted value vào JSON chung.

Draft doc/plan và line standalone yêu cầu `tp_reporting_expected_version` đối với user thường. Scoped form controller gửi version đã tải; write khóa row, so phiên bản rồi tăng version. Nested x2many cùng lần save dùng batch nội bộ; line tạo/xóa khóa parent để không vượt thao tác gửi đồng thời. Transition khóa row, kiểm actor/scope/state/version và tăng version. `request_key` cùng actor/payload trả kết quả đã xử lý; cùng key khác payload bị từ chối. Native reason dialog mang version khi mở. Không thể phát hiện ý định stale của client nếu chính client cố ý gửi phiên bản mới cùng payload cũ; đây không phải bảo đảm merge nội dung tự động.

## Snapshot, tổng hợp và coverage

Lần submit/finalize chụp exact nội dung/mẫu/facts/dependency. Return mở phần dữ liệu nháp hiện hành, không sửa snapshot cũ. Reissue kế hoạch giữ baseline đầu tiên và thêm baseline_history. So sánh hai snapshot gần nhất render HTML đã escape; không đọc finance vào so sánh chung.

Tổng hợp dùng child header giao kỳ, rồi lọc **fact theo ngày thực tế**. Key contribution/date/unit khử trùng; số khác nhau trên cùng key yêu cầu đối chiếu. Không cộng % tùy ý; không cộng quantity khác unit. `_report_actual` dùng eligible immutable personal facts thuộc cây plan, không lấy draft. Personal month/quarter cần nghĩa vụ/yêu cầu đúng kỳ; không bắt mọi người nộp ba loại. Coverage lấy nghĩa vụ, không lấy toàn bộ account active. `_submission_ids()` trả tồn tại submission theo batch trên tập obligation đã được kiểm quyền, không đọc nội dung private draft để tính count.

## Finance và tệp

Finance model riêng, general snapshot không chứa số tiền. `finance_enter` đọc nguồn do mình cung cấp; `finance_confirm` chỉ nguồn pending trong scope; full view/export cần `finance_read` riêng. Không tự xác nhận số mình cung cấp. Confirm cần nguồn/ngày/evidence, currency và tax_basis khớp định nghĩa; khóa metric chống xác nhận chồng coverage giao kỳ. Nguồn confirmed/snapshot-linked không sửa/xóa; definition metric đã dùng snapshot không đổi. Relation `value↔snapshot` đóng tại snapshot bằng SQL chỉ ID để owner không có quyền tiền vẫn chụp đúng lịch sử; export đọc relation dưới quyền finance hiện hành.

Minh chứng báo cáo phải private, không public/token; nguồn tài chính phải gắn **`tp.report.value`** để không rò qua quyền đọc document chung. Upload chưa gắn của chính user được bind tới dòng/directive hợp lệ. Source link khác vẫn kiểm quyền nguồn, không nhân bản file bằng sudo. `ir.attachment` extension kiểm parent hiện hành khi tải nội dung, kể cả URL token/public; tệp report đã có snapshot không đổi byte/xóa/đổi binding, directive đã done tương tự. Thu hồi quyền parent làm link cũ không còn quyền tải. Đây là bảo vệ ứng dụng, không thay ACL filesystem/backup của quản trị máy.

## Chỉ đạo, thông báo và export

Directive create khóa source report, kiểm `direct`, ghi issuer/source snapshot; request identity chống tạo trùng. Người nhận cập nhật trạng thái/kết quả; done cần result và không sửa lại kết quả đã hoàn thành. Lịch sử riêng append-only và HTML escaped. Tạo task chỉ trên project được quyền và giữ task ID để retry không tạo lần hai.

Thông báo dùng Odoo bus **trong ứng dụng**, nội dung chung không chứa tiền/nhận xét internal; submit/return/finalize/review/reply/directive gửi đúng recipient. Schedule nhắc chỉ khi `reminders_enabled`, explicit action và scope nghĩa vụ; chưa bật cron, email/chat ngoài ứng dụng. Bus là thông báo phiên, không được mô tả là email/persistent inbox; inbox công việc chính là danh sách báo cáo/chỉ đạo có scope.

Export Excel/Word/PDF chạy server và kiểm quyền hiện hành cả build/download. Bản đã gửi/chốt dùng snapshot; general export chỉ published reviews thuộc exact submission lineage. Finance chỉ khi `finance_read`; không dùng cache chung user, response no-store, text Excel chống formula injection. Source mutable chưa được tích hợp tự động phải mang nhãn thủ công/chưa tích hợp, không coi fixture là số thật.

## Bằng chứng và phần cần kiểm tiếp

Root chạy canonical test: `.local/corp-report001/tests7.log` ghi **25 tests executed, 0 failed, 0 errors**, khoảng 6s/2164 queries. Đây là bằng chứng tới source thời điểm tests7; **không bao phủ các hardening về directive history/evidence, token bắt buộc/line locking, provenance/batch và thay đổi sau đó**. Ruff/compile/diff-check là kiểm tĩnh, không thay business test. Tests8 và browser/HTTP/export evidence phải ghi tiếp ở acceptance khi thực sự chạy.

Các ca đa công ty selected/unselected, company-level chống department grant và tải attachment sau revoke đã bổ sung trong source test nhưng cần kết quả canonical mới. Các rủi ro cần ca thực còn lại: assignment hết hạn/thu hồi ngay khi URL tải cũ đã mở; hai transaction submit/line-write/reviewer và directive retry cùng lúc; rollback transaction liên quan filestore/evidence; attachment token/public/raw paths; finance overlap/currency/tax/null-zero qua export; lịch/nhắc scope; tổ tiên plan không mở sibling. Nghiệm thu nghiệp vụ, authority thật, main authorization và điện thoại thật vẫn tách khỏi kiểm kỹ thuật.
