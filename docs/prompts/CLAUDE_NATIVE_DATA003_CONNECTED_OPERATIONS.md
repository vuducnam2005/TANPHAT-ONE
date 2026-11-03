# Prompt Claude — NATIVE-DATA-003: dữ liệu mẫu liên thông theo người dùng và quy trình

Người dùng yêu cầu ngày 02/11/2026: biến toàn bộ dữ liệu mẫu đã thêm trên dev 18069 thành bộ dữ liệu liên kết và dùng được như một tình huống vận hành thực tế. Phiên điều phối chỉ soạn prompt ở CHG-20261102-013; **chưa thực hiện thay đổi dữ liệu hoặc quyền**. Các batch bên dưới dùng change ID mới khi thực thi.

Sao chép toàn bộ nội dung trong khối dưới đây vào phiên Claude triển khai:

```text
Làm việc trong C:\TANPHAT ONE.
Task: NATIVE-DATA-003 — Chuẩn hóa bộ dữ liệu mẫu liên thông theo người dùng, dự án và quy trình.
Không commit/push/deploy production. Không sửa odoo/, addons/, Git metadata hoặc thay đổi chưa commit ngoài scope.

1. Kết quả người dùng cần

Tôi muốn dùng bộ dữ liệu hiện có như một tình huống công ty giả lập có liên hệ xuyên suốt, thay vì phải mở từng menu bằng admin và bỏ bộ lọc mới thấy dữ liệu.

- Đăng nhập một nhân viên mẫu: thấy đúng dự án/task/giờ làm/chi phí/lịch/trao đổi được giao; tự thực hiện các thao tác đã được backend cho phép.
- Đăng nhập người quản lý mẫu: thấy đúng đội/dự án, làm được các action duyệt native trong scope fake và đối chiếu được với dữ liệu nhân viên.
- Đăng nhập kế toán mẫu: xem đúng hóa đơn/chi phí và phân bổ dự án theo quyền native; không biến người này thành System Administrator.
- Đăng nhập admin: quản trị/kiểm đối chiếu, có hướng dẫn mở đúng dữ liệu; không ép mọi bản ghi thuộc admin để dashboard cá nhân hết số 0.
- Đi được một kịch bản có bối cảnh nhất quán từ khách hàng/cơ hội → dự án → nhân sự → task → timesheet/chi phí → hóa đơn dự kiến/bảng tổng hợp. Lịch, To-do và trao đổi nhắc đúng hồ sơ này.

“Như thật” nghĩa là quan hệ, phạm vi quyền, hành động, lịch sử và công thức đúng trên dữ liệu GIẢ. Không có nghĩa hồ sơ công ty thật, chữ ký/BASE approval thật, tiền thu/chi thật hoặc production/pilot đã được phép.

Thực hiện các batch tuần tự bên dưới; không kết thúc ở báo cáo inventory nếu các bước độc lập đã có đủ căn cứ. Chỗ thiếu chức năng phải chỉ rõ, không dùng số tĩnh/mô tả để giả vờ đã tích hợp. Không hỏi lại từng thay đổi fixture/actor đã được cho phép rõ trong prompt này.

2. Đọc và xác minh trước khi sửa

Đọc theo AGENTS.md và thứ tự bắt buộc, đặc biệt:
- docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, mục CHANGELOG mới nhất, ROADMAP, DECISIONS, HANDOFF_TEMPLATE.
- docs/AI_COORDINATION_WORKFLOW.md; docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md.
- docs/architecture/TP_PRODUCT_NAMING.md; TP_BUSINESS_WORKFLOW.md; TP_DATABASE_DESIGN.md.
- docs/demo/ODOO_NATIVE_SAMPLE_DATA.md; docs/demo/UI_HOME_001_RUNBOOK.md; docs/i18n/VI_GLOSSARY_AND_COVERAGE.md.
- Source model/security/action của crm, project, project_todo, hr, hr_timesheet, hr_expense, project_hr_expense, account, calendar, mail/discuss, spreadsheet dashboard và addon TP liên quan; chỉ đọc upstream.
- Tool guard scripts/dev.py, scripts/backup_restore.py, scripts/ai_workflow.py. Helper .local/native-data-20261102, .local/data002, .local/vi001 chỉ là tham khảo, kiểm lại source/runtime trước khi dùng.

Kiểm git status/diff, workflow check/checkpoint và runtime. Không ghi đè, xóa hoặc finish checkpoint của task khác. Chưa có checkpoint thì chạy start trước lần sửa đầu tiên. Ghi kế hoạch/nguy cơ và change ID mới; không tái dùng CHG-013 của prompt.

Môi trường đích: Odoo native http://127.0.0.1:18069/odoo, DB tp_tanphat_dev, PostgreSQL chung 55432. Xác minh bằng owner marker/config/PID/database identity, không chỉ tên/cổng. Không đổi mật khẩu/config dev để mở phiên.

UI-DEMO-001/002 cũ đã ngừng/lưu trữ CHG-012. Không khôi phục hai DB demo, không mở 18109/18119, không chạy ui_demo.py prepare/seed/start, không cài tp_demo_workspace để giải quyết task này. Giữ nguyên archive và lịch sử/evidence.

3. Baseline và phạm vi dữ liệu

Kiểm thực tế, không coi các con số sau là target cần tạo lại:
- 4 project DA-2026-001…004, cùng record trong Project và TP Projects; 28 task dự án.
- 8 partner, 10 CRM lead, 5 department, 12 employee, 10 user giả; 20 timesheet, 6 expense, 4 invoice nháp; 1 service product.
- 27 assignment, 4 CRM tag liên kết dự án; 14 To-do riêng của admin.
- 8 lịch, 3 nhóm Discuss/12 tin, 2 dashboard mẫu, 6 work item.
- Namespace ownership: tp_native_sample_20261102, tp_native_link_20261102, tp_native_todo_20261102, tp_native_data002_20261102; baseline gần nhất có 188 binding. Tra ID/XML ID và provenance, không suy ownership từ tên/mã/tiền tố đơn lẻ.
- Các bản ghi TP/dev có sẵn từ trước, hợp đồng HD-DEV, To-do onboarding, kênh General và dashboard chuẩn phải được inventory nhưng không mặc nhiên thuộc quyền sửa của task này.

Bằng chứng vấn đề đã kiểm trên dev ngày 02/11:
- Admin uid 2 không có hr.employee. Sáu expense ID 7…12 thuộc 5 nhân viên mẫu khác; tất cả draft, tổng7.160.000 VND.
- get_expense_dashboard trong Odoo hiện tại trả 0 nếu user không có employee_ids; nếu có thì lọc employee_id child_of employee_ids và domain tìm kiếm. Vì vậy bỏ “Chi phí của tôi” không biến ba ô thành tổng toàn công ty.
- User giả chưa có password. Bốn project đã tp_managed=True; rule hiện tại chặn user thường ghi project/task managed ngay cả khi có assignment. Không thể cho nhân viên sửa task bằng cách chỉ thêm native Project User.
- CRM→Project hiện chủ yếu là customer chung/tag/mô tả/link, chưa có quan hệ dữ liệu trực tiếp/chuyển đổi tự động.
- Cả bốn invoice đều draft. An Hòa hiện chưa có timesheet; không được bịa giờ chỉ để làm dashboard đầy.

Đo lại tất cả trước khi dùng; nếu khác, ghi chênh lệch và nguyên nhân thay vì chạy seed cũ để “sửa” về baseline lịch sử.

Trước bất kỳ ghi dev: snapshot mới gồm DB+filestore+config/metadata và source đang sửa, credential riêng ngoài Git; manifest/checksum. Restore snapshot vào DB/data-dir/config/port cô lập có ownership mới để diễn tập và kiểm count/ID/blob. Không clone đè test/restore cũ. Listing không phải restore rehearsal. Không tạo user/role PostgreSQL chung mới hoặc đổi shared cluster. Neutralize clone trước khi chạy action; không gửi mail/push/webhook/bank/e-invoice ra ngoài. Ghi rõ PID/DB/đường dẫn task sở hữu để cleanup sau.

4. Batch A — Bản đồ liên kết và kịch bản có thể kiểm

Tạo bản đồ cho TOÀN BỘ dữ liệu thuộc bốn namespace, gồm:
XML ID → model/ID → người dùng/nhân viên/phòng ban → company → partner/lead/project/task/analytic account → chứng từ hoặc nội dung tham chiếu → state → actor được xem/ghi → cách mở trong UI → dự kiến giữ/sửa/thêm và lý do.

Không bắt mọi hồ sơ phải có cùng một project: sáu lead chưa chuyển đổi có thể ở pipeline; To-do cá nhân có thể chỉ là việc điều phối; danh mục work item là master data dùng chung. Mỗi trường hợp phải có vai trò hợp lý trong bối cảnh, không phải record mồ côi để lấp số lượng.

Chọn tối thiểu3 kịch bản có expected assertions:
S1. Nhân viên mẫu của một dự án: đăng nhập → Home → task được giao → xem/nhập giờ hợp lệ → khai chi phí → gửi cho người duyệt mẫu khác → quản lý đọc/duyệt → dashboard đối chiếu đúng nguồn.
S2. Quản lý dự án/đội: khách hàng/cơ hội liên hệ đúng project, task/nhân sự/giờ làm/chi phí, invoice draft dự kiến, lịch/trao đổi; thêm case trả lại/sửa/gửi lại nếu action native đã có.
S3. Người ngoài scope: không đọc/ghi được project/task/chứng từ, lịch private, nhóm hoặc dashboard tài chính không được phép; kiểm cả link trực tiếp/RPC, không chỉ menu.

Bao phủ đủ bốn project: giữ tiến độ khác nhau hợp lý. Một dự án giai đoạn chuẩn bị có 0 giờ là hợp lệ; giải thích zero theo nguồn, không tạo giờ khống. Ngày/agenda/due date nhất quán theo ngày thực chạy Asia/Saigon và timezone actor, không sửa ngày lịch sử/chứng từ đã chốt để “hôm nay có dữ liệu”.

5. Batch B — Tài khoản và liên kết dữ liệu

B1. Actor thật trong bộ giả lập
- Tái sử dụng user/employee giả có ownership đã chứng minh; chọn số actor tối thiểu cho nhân viên, quản lý/duyệt, kế toán và người ngoài scope. Lập bảng login → employee → department → manager → company → project assignment → group/capability chính xác → tác vụ được phép. Không suy TP capability từ chức danh.
- Prompt này cho phép bật đăng nhập cho các user GIẢ được chọn (thay giới hạn “không password” của lượt seed cũ): đặt password ngẫu nhiên vào file local ACL private ngoài Git, không in ra chat/log, không invitation/reset email. Verify không thay password khi chạy lại. Không đổi admin/planner.dev hoặc user thật, không đặt chung một password mặc định.
- Chỉ bổ sung employee/user giả mới nếu inventory chứng minh không có actor phù hợp; ghi lý do/ID/provenance, không tạo bản sao cùng người. Không tạo employee giả cho admin chỉ để đổi số dashboard.
- Mối quan hệ user/employee/manager và scope dùng đúng native fields. Không tự bổ nhiệm chủ nghiệp vụ thật hoặc đổi cơ cấu nhân sự công ty. Nhóm tối thiểu đúng chức năng, không grant System Administrator/Platform Manager đại trà, không sudo trong thao tác/kiểm chứng actor.
- Giữ Home/tiếng Việt; có thể đặt vi_VN/timezone cho các actor giả được chọn. Không đổi locale/timezone hàng loạt user khác.

B2. Quan hệ nghiệp vụ
- Project và TP Projects dùng cùng 4 ID hiện có; task/customer/employee/analytic account/company phải thống nhất.
- Task ↔ assignee ↔ employee ↔ timesheet.user_id/employee_id/project_id/task_id khớp; không phát sinh duplicate timesheet do thay user. Lập quan hệ có ý nghĩa giữa6work item và công việc khi model hiện có hỗ trợ; không dùng catalog để tự mở workflow mới.
- Expense gắn đúng employee/project analytic distribution; manager là actor khác, quyền native thật. Invoice cùng customer/project/company/currency, dòng phân bổ đúng analytic account; tổng/cơ sở thuế được giữ và giải thích, không đồng nhất10% expected_revenue với quy định tạm ứng.
- CRM liên kết các cơ hội tương ứng với cùng customer/project. Nếu thiếu FK native, được làm một batch bridge tối thiểu theo B3 bên dưới, không coi tag/mô tả là FK hoặc conversion tự động. Lead chưa thành dự án giữ đúng pipeline; không tạo project cho cả 10 lead để đủ liên kết.
- To-do vẫn là việc cá nhân (project_id=False), không biến14 To-do thành task dự án trùng28 task. Dùng related-record field native nếu có; nếu chỉ hỗ trợ link/mô tả thì ghi rõ đó là tham chiếu. Có thể giữ admin là người điều phối các việc đó; không chuyển toàn bộ việc sang actor mới chỉ để màn hình của họ đầy.
- Calendar/Discuss: giữ8 lịch/3 nhóm/12 tin, agenda/link đúng người và dự án. Có thể thêm các actor GIẢ được chọn vào cuộc họp/nhóm phù hợp để họ có trải nghiệm, vẫn private và không public/toàn công ty. Không gửi email/push/reminder/calendar sync, không mention người thật. Giữ author/date của12 tin cũ; tin bổ sung phải do đúng actor giả thực hiện action native, không giả mạo lịch sử. Không sửa kênh dùng chung.
- Dashboard lấy nguồn sống, domain/ID fixture chính xác và theo quyền người xem; không hardcode kết quả. Giữ dashboard quản trị hiện có; chia sẻ cho actor giả chỉ sau test quyền (data source/cached cells/export/share). Không phát hành bảng tiền cho toàn base.group_user.

B3. Khoảng thiếu quan hệ hoặc quyền ứng dụng
- Data patch không sửa ACL/rule để cho chạy tắt. Khi cần application code, làm thành batch riêng: ghi đặc tả nhỏ, actor/scope/state không đổi, test tái hiện và test âm, schema/API/UI ảnh hưởng, rollback/migration; sau đó triển khai/test clone trước khi áp dụng đúng module lên dev.
- Cho phép bridge CRM→Project tối thiểu trong custom_addons, ưu tiên native relation nếu đã có. Nếu phải thêm field, đặt trong addon tích hợp trách nhiệm rõ, dùng Many2one/Many2many đúng cardinality, check_company/constraint/ondelete thích hợp; có UI điều hướng phù hợp và quyền đọc/ghi theo model liên quan. Không auto-create project, không copy khách hàng/dự án, không kéo ORM/technical field ra nhãn UI. Không tạo app/menu rỗng hoặc một bảng scenario làm database thứ hai.
- Không thêm quan hệ hoặc smart button làm lộ tên/count/tiền hợp đồng/hóa đơn cho người không có quyền. Đọc được project không đồng nghĩa đọc được CRM/hóa đơn. Test lựa chọn relational field, name_search, read_group, direct RPC và response view, không chỉ nút bấm.
- Với task managed: không bỏ global scope, không thêm nhánh “assignee” mở mọi trường ghi. Batch này không tự tạo policy giao việc mới: giữ rule TP hiện hành, chứng minh thao tác đã được phép; nếu S1 nhập giờ/đổi tiến độ bị rule chặn thì ghi chính xác operation/field/actor bị chặn và tách RFC quyền tối thiểu chờ phiên điều phối. Hoàn thành các liên kết/actor/chi phí khác độc lập, không giả vờ S1 end-to-end đã đạt hoặc cấp Platform Manager để né gap. Không chuyển4 project về unmanaged để vượt rule.
- TP Contracts/BASE/Survey/Design/giao khoán/nghiệm thu/thanh toán TP chưa có đầy đủ runtime. Giữ hợp đồng mẫu cũ đúng project của nó; không repoint hồ sơ có lịch sử sang4 project để làm cầu nối giả. Không gán effective/approved/verified bằng fixture, không phát sinh grant workflow TP trên dev trái DEC-020/021 vốn chỉ mở trên test. Nếu cần thêm TP workflow/model, trả gap/RFC riêng, không triển khai cả phân hệ dưới tên “liên kết dữ liệu”.

6. Batch C — Các giai đoạn native có bằng chứng

C1. Chi phí: sửa đúng nguyên nhân ba ô 0
- Dùng6 expense hiện có, giữ ID, số tiền/currency/employee/project và tổng7.160.000 VND trừ khi phát hiện lỗi thực sự có bằng chứng. Không làm sáu khoản cùng thuộc admin.
- Trên clone, đi action native bằng session/with_user của actor được phép, không viết trực tiếp state/approval_state, không superuser/sudo để duyệt thay. Kiểm self-approval, khác nhân viên/khác công ty, draft→submit→approve/refuse/correction và lịch sử.
- Xây ma trận phần lớn6 khoản ở các bước khác nhau, ví dụ2 draft/2 submitted/2 approved chờ hoàn trả; đây là ví dụ, chỉ dùng nếu quy trình native/dữ liệu thực đáp ứng. Không chia đều để đạt số đẹp. Actor quản lý có employee/nhánh nhân sự và quyền hợp lệ để xem các tổng tương ứng.
- Kiểm source Odoo 20: approve có thể tạo account.move/account.payment và analytic lines. Lập inventory side effect trước khi apply. Trên dev chỉ cho submit/approve fixture nếu đường thực thi đã test không tự post/payment hoặc gửi ra ngoài; draft move phát sinh hợp lệ phải có ownership và nằm trong baseline diff dự kiến. Nếu native action bắt buộc post/payment, chỉ thực hiện case đó trên clone và ghi giới hạn dev; không patch upstream/compute để ép approved.
- get_expense_dashboard so với tổng read_group/ORM theo đúng actor + hierarchy + domain, không so với toàn DB. Nhân viên thấy chi phí của mình, quản lý đúng đội, người khác không thấy; admin không có employee có thể0 đúng thiết kế. Viết hướng dẫn đăng nhập role nào để xem từng giai đoạn. Ô0 phải giải thích được, không bị xóa/đổi thành null để che gap.

C2. Hóa đơn/kế toán native
- Giữ4 invoice dự kiến hiện có cùng tổng/partner/analytic; đủ link dự án và state draft rõ ràng. Không coi dự kiến là doanh thu kế toán/tiền đã thu, không cộng trùng invoice/expense/CRM/hợp đồng.
- Prompt này KHÔNG cho phép post hóa đơn, tạo thanh toán/hoàn trả, bank reconcile hoặc e-invoice trên dev 18069. Có thể diễn tập các action native đó CHỈ trên clone neutralized của dữ liệu GIẢ nếu cần chứng minh phần cuối chuỗi; không kết nối ngân hàng/thuế/đối tác và không tự quyết định chart/thuế pháp lý. Báo test-only rõ ràng, không nói dev đã hoàn thành thu/chi.
- Không thêm module sales/purchase/payroll/enterprise hoặc mở integration mới để nối các mục chưa triển khai. Chỉ dùng chức năng đang có; thiếu cầu nối nghiệp vụ thì RFC cụ thể.

7. Cơ chế áp dụng và bảo toàn

- Thực hiện trên clone trước, rồi apply đúng các batch dev đã có kiểm chứng và nằm trong scope trên. Không dùng kết quả clone thay bằng chứng dev.
- Seeder/migrator có preflight target/config/DB identity/ownership, advisory lock, dry-run rollback, apply atomic cho từng batch dữ liệu, verify bằng registry mới, log thay đổi trước/sau an toàn. Ghi rõ DDL/module install và side effect ngoài transaction không được bảo đảm rollback chỉ bằng savepoint.
- Mapping chỉ rõ những field fixture được đổi, record được thêm, quyền fake được cấp. Namespace mới tp_native_data003_YYYYMMDD (theo ngày thực chạy) cho phần bổ sung; tiếp tục dùng XML ID cũ cho record tái sử dụng. Không seed_native.py cũ để dựng lại cả tập.
- Mỗi bước state/action có ledger riêng trong journal migrator: apply lại không submit/approve/message_post/payment lần 2; verify không thay dữ liệu. Với action không idempotent phải có precondition và đối chiếu event/history, không chỉ kiểm tên bản ghi.
- Không ghi SQL trực tiếp vào bảng nghiệp vụ/quyền/state. Không dùng global monkeypatch/sudo để actor “được phép”. Bootstrap quản trị tối thiểu cho fake user/group/ownership phải tách khỏi chứng cứ actor tự thao tác.
- Không gửi thông báo ra ngoài hoặc đến user thật. Context ngăn mail/calendar notification phải kiểm đúng source, đo mail.mail/notification/outbox trước/sau. Không sửa SMTP/cron/credential chung hoặc tắt notification cả hệ thống để làm test xanh. Chatter/in-app chỉ giữa actor giả theo scope có thể phát sinh có chủ đích và phải inventory, không giả định rollback ngăn được mọi notification.
- Credential/filestore/dump/private report ngoài Git; data/config không chứa tên/email/số tài khoản người thật. Mọi tên tự nhiên vẫn có provenance giả lập trong metadata/mô tả/runbook.
- Giữ bản ghi ngoài fixture, Home, vi_VN/en_US, session/login hiện có, React, OpenAPI, test/restore/backup khác. Nếu cần restart/upgrade đúng addon dev, phải có kế hoạch riêng trong batch, đúng PID và rollback đã test; không stop toàn bộ Python/Odoo/PostgreSQL, không -u all.
- Rollback dữ liệu chưa chốt bằng journal field trước/sau/ownership; bản đã chốt không unlink hoặc ghi lùi state. Reversal/cancel có lý do dùng action native trên clone. Phục hồi full DB chỉ là phương án được điều phối riêng nếu không có ghi mới kể từ snapshot; không overwrite dev để đảo một batch rồi làm mất công việc khác.

8. Kiểm nghiệm thu bắt buộc

T1 Inventory/ownership: mọi binding cũ có mặt trong mapping; không mất/thêm trùng partner/project/task/employee/expense/invoice cũ. Các bổ sung có lý do và ID mới, không kết luận bằng count tổng đơn lẻ.
T2 Integrity: FK/company/user-employee-manager/task-timesheet/partner/analytic/currency khớp; customer của lead/project/invoice hợp lý; không dùng display name làm khóa; null/0/chưa xác nhận giữ khác nhau.
T3 Roles: login thật từng actor giả, quyền dương và âm; menu/Home “của tôi” hiển thị đúng vai trò. Admin/planner.dev giữ password/groups/assignment/quyền như baseline, ngoại trừ cập nhật fixture đã ghi rõ không đụng user này.
T4 S1/S2: thao tác qua UI/native RPC dưới actor thật, có lịch sử đúng người; hạn chế managed task được báo tách riêng. Không gắn nhãn END_TO_END nếu có bước bắt buộc bị chặn hoặc chỉ dùng sudo/bootstrap.
T5 Expenses:6 khoản/tổng tiền/analytic không đổi, state native đúng, ba ô dashboard khớp actor/domain. Có case chờ duyệt/chờ hoàn trả khi native an toàn cho dev; mọi bước clone-only ghi riêng.
T6 Finance: invoice totals/currency/tax basis/analytic khớp; không posted/payment dev mới; side effect move nháp của approve nằm đúng fixture. Không gộp số dự kiến/giá trị hợp đồng/doanh thu/tiền thực thu.
T7 Privacy: To-do private, event Busy không lộ chi tiết khi không có quyền, channel/message/member/dashboard không truy cập được bằng direct RPC/URL nếu không thuộc scope; không tiền qua link/count/cache/export/share.
T8 Dashboards: tính lại từ dữ liệu nguồn backend, đối chiếu theo từng project/actor/locale. Trên clone thay đổi có kiểm soát một fixture rồi refresh phải đổi đúng số; rollback lại. Không mutate dev chỉ để thử chart động.
T9 Idempotency/rollback: apply lần 2 created=0/updated=0 (ngoài telemetry), không action/chatter trùng; fail giữa batch rollback sạch hoặc journal nhận diện chính xác phần đã thực hiện, không giả vờ toàn transaction atomic nếu có side effect ngoài DB.
T10 UI: Home/nhãn VI, list/form/filter/role switch/link ngược đúng hồ sơ; desktop 1440/mobile 375, zoom 125/150%, 0 lỗi console/không tràn ngang. Ảnh thực tự xem; không chỉ HTTP200.
T11 Preservation/runtime: hash/field compare ngoài fixture và ACL/rule ngoài batch được phép không đổi, count/ID cũ còn nguyên; dev 18069 truy cập/đăng nhập được,18109/18119 không tái mở, PostgreSQL và test/backup khác nguyên. Phân loại telemetry hợp lệ riêng.
T12 Code: nếu thay code thì chạy Odoo tests/security/upgrade trên clone, ruff; UI JS/route thì HOOT/browser; React typecheck/build/unit/E2E chỉ nếu có thay đổi React được giao riêng. Đọc log summary/test DB thật, exit nonzero khi assertion fail. Không coi workflow checker là test nghiệp vụ.

9. Bàn giao từng batch và kết quả cuối

- Cập nhật docs/demo/ODOO_NATIVE_SAMPLE_DATA.md theo version mới, giữ lịch sử cũ. Tạo docs/demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md: sơ đồ/ma trận quan hệ,3 kịch bản, bảng actor không password, cách mở/filter, state/zero đúng nghĩa, side effect, rollback, evidence và gap.
- Tooling/bridge code tái lập được trong Git theo convention; data/credentials/report chi tiết ngoài Git. Không chỉ để một script local không thể tái lập rồi nói đã hoàn tất.
- PROJECT_STATUS/CHANGELOG/ROADMAP phản ánh đúng thực tế từng batch; docs quyền/workflow/decision cập nhật nếu có thay đổi, không tự sửa business policy từ kết quả test.
- Chạy git diff --check, ai_workflow finish đúng change ID và check; không finish checkpoint task khác. Không stage/commit/push.
- Kết quả cuối tách rõ: đã áp dụng dev / chỉ kiểm trên clone / chưa có chức năng / cần quyết định; technical acceptance / business acceptance / pilot authorization riêng.
- Báo chính xác đã liên kết được những chuỗi nào, tài khoản nào dùng để xem/thao tác, số tiền nào nguồn nào, gap nào còn lại, nguồn/DB ngoài fixture có giữ nguyên không. Không ghi “toàn bộ như thật” nếu còn đường bắt buộc chỉ là mô tả hoặc actor không thao tác được.

Chỉ đánh dấu NATIVE-DATA-003 COMPLETE cho scope dev khi các chuỗi bắt buộc theo actor đã có bằng chứng và các giới hạn clone-only công bố rõ. Nếu managed-task policy/bridge nghiệp vụ còn chặn một chuỗi bắt buộc, ghi PARTIAL_WITH_GAPS với RFC nhỏ có reproduction/expected/security tests; vẫn bàn giao phần liên kết an toàn đã hoàn thành. Không tự mở toàn bộ ERP hoặc bịa quy trình để đóng task.
```

Prompt đã cho phép bật tài khoản giả và thực hiện action native an toàn trong phạm vi mô tả khi người dùng giao cho phiên triển khai; không yêu cầu xác nhận lại từng record. Đây chưa phải quyền ghi dữ liệu từ phiên chỉ đang đọc/soạn prompt. Các bước kế toán đã chốt/thu chi trên dev và thay đổi policy managed-task vẫn nằm ngoài batch này; cần phạm vi triển khai riêng nếu muốn mở tiếp.
