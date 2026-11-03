# NATIVE-DATA-002 + VI-001 — Hoàn thiện dữ liệu mẫu và Việt hóa Odoo native

Chuẩn bị ngày 02/11/2026 (Asia/Saigon). Đây là prompt triển khai cho Claude, chưa phải xác nhận đã nạp dữ liệu hoặc Việt hóa. Người dùng yêu cầu bổ sung các mục còn thiếu trong menu và Việt hóa hệ thống, giữ các từ tiếng Anh đặc thù.

## Prompt giao Claude

```text
Làm việc trong C:\TANPHAT ONE.

Mục tiêu sử dụng:
Người dùng đăng nhập Odoo dev tại http://127.0.0.1:18069/odoo, mở các ứng dụng đã cài để xem một kịch bản dữ liệu giả thống nhất, đọc được nhãn/thông báo bằng tiếng Việt, thao tác được theo quyền hiện có. Giữ TANPHAT ONE/Odoo/BASE và thuật ngữ tiếng Anh đặc thù khi dịch làm mất nghĩa.

Làm tuần tự hai batch, mỗi batch CHG-ID/checkpoint/handoff riêng:
A. NATIVE-DATA-002 — kiểm đủ dữ liệu các app, chỉ thêm phần thiếu.
B. VI-001 — Việt hóa giao diện toàn bộ các app đã cài và các luồng người dùng hiện có.

Không commit/push, không triển khai production. Không sửa odoo/ hoặc addons/. Không tự mở nghiệp vụ chưa có, phê duyệt BASE, ký, hiệu lực, posted/payment hoặc cấp grant người dùng thật.

1. Đọc và phối hợp trước khi làm

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/DECISIONS.md, docs/ROADMAP.md, docs/demo/ODOO_NATIVE_SAMPLE_DATA.md và:
- docs/prompts/CLAUDE_TODO001_NATIVE_PRIVATE_TASK_FIX_AND_SAMPLE.md
- docs/prompts/CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md

Kiểm git status/diff, runtime, scripts/ai_workflow.py check và checkpoint. Tại lúc soạn prompt, custom_addons/tp_web_home đang được một batch khác tạo, checkpoint ACTIVE từ 02/11/2026T03:15:28Z; checker báo code thay đổi sau handoff. Đây là dấu hiệu batch đang làm, không phải cho phép finish thay nó.

Nếu Home/TODO đang được agent khác thực thi, không sửa trùng file, không restart/upgrade cùng dev hoặc ghi đè handoff. Hoàn tất/nhận bàn giao batch đó trước các thao tác phụ thuộc. Có thể tiếp tục đọc/phân tích phần độc lập. Nếu cùng một Claude tiếp quản thì đọc log/checkpoint, xác nhận phần source/test còn dở, chốt đúng batch đó rồi mới start batch mới; không xóa checkpoint hoặc sửa AI_WORKFLOW_STATE.json bằng tay để làm xanh.

Chỉ làm trên tp_tanphat_dev, dev18069 và DB test cô lập có ownership rõ ràng. Không sửa demo18109, dữ liệu doanh nghiệp thật/NAS hoặc cài module chỉ vì muốn menu đầy hơn. Kiểm trạng thái hiện tại, không tin tuyệt đối số lượng dưới đây nếu task khác đã bổ sung hợp lệ.

2. Baseline để đối chiếu, không seed lại từ đầu

Kết quả HTTP admin trước lượt này:
- Contacts: 8 đối tác giả.
- CRM: 10 cơ hội giả; 4 cơ hội cùng khách hàng/mã/tham chiếu với dự án.
- TANPHAT ONE / TP Projects và Project dùng cùng 4 project ID, mã DA-2026-001…004.
- Project: 28 task dự án, không bao gồm To-do.
- Employees: 12 nhân viên, 5 phòng ban; 10 user giả không mật khẩu để giao task/giờ làm.
- Timesheets: 20 dòng gắn nhân viên/task/project.
- Expenses: 6 khoản nháp, analytic allocation đúng dự án.
- Invoicing: 4 hóa đơn nháp, tổng lần lượt 310.000.000 / 210.000.000 / 96.000.000 / 185.000.000 VND; tổng cộng 801.000.000 VND, không phải doanh thu hạch toán hoặc tiền đã thu.
- To-do: chưa nạp thành công; 0 binding tp_native_todo_20261102, admin không thấy open To-do. Có lỗi quyền đã giao TODO-001.
- Calendar: 0 event hiển thị cho admin.
- Discuss: 3 kênh sẵn, chưa có bộ trao đổi mẫu thuộc fixture dự án.
- Dashboards: có Invoicing và Project chuẩn; chưa có bảng điều phối dự án Tấn Phát riêng.
- Apps/Settings là công cụ quản trị, không có yêu cầu tạo bản ghi nghiệp vụ giả để lấp đầy.
- Ngôn ngữ đang active chỉ en_US; admin en_US. Source có ngôn ngữ vi_VN và nhiều catalog vi.po, nhưng chưa kích hoạt trên dev tại lần kiểm.

Fixture đã có: namespace tp_native_sample_20261102 và tp_native_link_20261102 trong ir.model.data. Ánh xạ theo XML ID/record ID, không dựa vào tên hiển thị. Evidence local ở .local/native-data-20261102/menu-data-coverage-audit.json và language-coverage-audit.json nếu còn; source hiện tại mới là căn cứ cần kiểm lại.

Không chạy seed_native.py cũ sau khi project đã managed. Không tạo project/customer/user thứ hai để làm dữ liệu trông đồng nhất.

3. Batch A — Hoàn thiện dữ liệu mẫu

Trước nạp: lập bảng hiện có/còn thiếu/tạo thêm, chụp database+canonical filestore+manifest, kiểm listing/checksum bằng tooling có guard target/ownership. Snapshot local trước đã có không thay snapshot mới nếu dữ liệu đã thay đổi; không nhầm listing với restore rehearsal. Không print secrets, không dùng committed-source-only backup để tuyên bố đã giữ mọi code chưa commit.

Seeder cần dry-run rollback, apply nguyên tử theo batch và verify registry mới; XML ID/idempotent, chạy lại created=0. Nếu Odoo có tác dụng bus/mail không rollback cùng transaction, ngăn đường gửi đó trước khi dry-run, không giả định rollback ngăn được mọi thông báo. Dữ liệu mới vẫn có provenance giả lập trong mô tả/technical namespace/tài liệu; tên danh sách tự nhiên, không thêm DEMO vào mọi tên. Không trình bày dữ liệu giả như kết quả vận hành thật.

A1. To-do
- Kiểm TODO-001 đã sửa và test đạt chưa. Nếu chưa, thực hiện đúng prompt TODO-001 trên DB cô lập rồi áp dụng correction tối thiểu trước seed; không dùng sudo để che lỗi hoặc mở rộng quyền toàn bộ task.
- Đích: 14 việc cho admin, gồm 12 open: Inbox 3, Today 3, This Week 2, This Month 2, Later 2; Done 2.
- Dùng namespace tp_native_todo_20261102 hiện có, helper local seed_todo.py chỉ làm tham khảo. Nếu task khác đã nạp thì verify, không tạo lại; không sửa việc người dùng đã bắt đầu sử dụng chỉ để khớp số mặc định.
- project_id=False, không nhân bản 28 task dự án. Tham chiếu mã/link dự án trong mô tả khi phù hợp; private admin, không chia sẻ người thật. Ngày cơ sở theo ngày thực chạy Asia/Saigon, để Today/tuần hiện tại nhìn thấy được.

A2. Calendar
- Thêm 8 lịch cho admin, rải tuần hiện tại và tuần kế tiếp, ít nhất 4 lịch tham chiếu đủ bốn dự án. Ví dụ họp phối hợp, chuẩn bị trao đổi hồ sơ, rà danh mục tài liệu, tổng hợp công việc tuần.
- Có tiêu đề tự nhiên, ngày/giờ bắt đầu-kết thúc hợp lệ, agenda, mã/link dự án và provenance; không biến nội dung lịch thành bằng chứng nghiệm thu/duyệt.
- Chỉ organizer/attendee là admin, privacy private, không mời khách hàng hoặc user khác, không reminder/alarm, không lặp, không video/link ngoài hoặc Google/Outlook sync. Không sửa cấu hình SMTP/global notification để đạt điều này.
- Kiểm source calendar hiện tại: no_mail_to_attendees/dont_notify là các context đã thấy, cần kiểm lại đúng đường thực thi; assert không phát sinh mail/push/invitation tới người khác. Không chỉ đặt mail_notify_force_send=False vì có thể vẫn tạo hàng đợi.
- Native tuần/tháng đang mở phải hiển thị đủ lịch phù hợp thời gian; lưu UTC, trình bày đúng Asia/Saigon, không tự đổi timezone toàn bộ nhân sự thật.

A3. Discuss
- Tạo 3 kênh/nhóm trao đổi riêng dùng mẫu: Điều phối dự án, Kế hoạch Kinh doanh, Phối hợp Khảo sát – Thiết kế. Mỗi nhóm ít nhất 4 tin nhắn ngắn có bối cảnh, tổng 12 tin.
- Ví dụ chủ đề: chuẩn bị lịch họp, các đầu mục cần trao đổi, nhắc nơi xem công việc, danh mục hồ sơ còn cần kiểm. Tham chiếu đúng bốn mã/link dự án, không đăng tiền/hồ sơ tài chính hoặc bịa trạng thái đã ký/duyệt/nghiệm thu.
- Không đăng vào 3 kênh sẵn hoặc thêm thành viên thật. Nhóm mới chỉ có admin; dùng native private group phù hợp source hiện tại, không group_public_id auto-subscribe toàn nhân viên. Không mention người khác hoặc gửi email/push cho họ.
- Tin mẫu do admin đăng, giữ creator/author thật của thao tác, không giả mạo phát ngôn của nhân sự khác. Dùng đường ORM/native message_post phù hợp, kiểm silent/notification behavior trên test; không tự insert SQL vào mail tables.
- Nội dung hiển thị được trong Discuss admin. Tài khoản không phải thành viên không đọc được ngay cả qua ORM/native RPC; không chỉ dựa vào việc sidebar không hiện.

A4. Dashboards
- Giữ nguyên hai dashboard chuẩn và kiểm chúng mở được. Bổ sung 2 bảng tổng hợp native trong app Dashboards, dùng spreadsheet dashboard/data source chuẩn nếu khả dụng, không dựng app dashboard riêng hoặc tĩnh giả số.
- Bảng 'Điều phối dự án': bốn dự án, task theo dự án/trạng thái, giờ làm theo dự án và phòng/nhân sự trong đúng phạm vi fake. An Hòa chưa có timesheet thì hiển thị 0 dòng/0 giờ, không tự tạo giờ làm cho đủ.
- Bảng 'Hóa đơn và chi phí dự kiến': bốn hóa đơn nháp theo dự án, 6 khoản chi nháp; ghi rõ nháp/chưa hạch toán. Không gộp doanh thu kỳ vọng CRM, giá trị hợp đồng, hóa đơn, doanh thu kế toán và tiền thực thu thành một chỉ tiêu.
- Tất cả bảng/biểu đồ đọc dữ liệu nguồn bằng domain ID/XML ID fixture và company; khi refresh phải đối chiếu lại được. Không hardcode 4/28/801 triệu làm ô kết quả để trông giống dashboard động. Các con số này là expected assertions của baseline giả, không phải công thức tính.
- Kiểm native spreadsheet/dashboard permission: record dashboard được phép đọc không có nghĩa data source được sudo. Không dùng sudo hoặc dữ liệu tài chính precomputed chung để vượt quyền người xem. Kiểm cả snapshot/cached cells/export/share; không tạo public share.
- Bảng mới chỉ cấp cho admin để trình diễn, không cấp financial_read/group_dashboard_manager hoặc quyền kế toán cho người khác. group_ids mặc định có thể là base.group_user; không để default này phát hành dashboard tài chính cho toàn công ty. Dùng allowed_user_ids/company restriction đúng source và kiểm hiệu lực các rule OR/AND; quyền quản trị kỹ thuật vốn có không được mô tả thành cơ chế riêng tư tuyệt đối.
- Nếu tạo spreadsheet native cần catalog/data file thì lưu artifact cấu hình tái lập trong Git theo convention dự án và không đưa DB dump/secret vào Git. Không copy snapshot tài chính ra file public/static. Nếu thật sự cần app code ngoài tooling để vượt hạn chế công cụ chuẩn, ghi rõ gap và tách batch triển khai tối thiểu; không phát sinh reporting engine mới trong seed.

A5. Các app đã có và phần quản trị
- Verify 8 Contacts, 10 CRM, 4 project/28 task, 12 employee/5 department, 20 timesheet, 6 expense/4 invoice; bổ sung chỉ khi có gap đã xác minh, giữ provenance/ownership. Không sửa/xóa hồ sơ ngoài fixture hoặc hồi sinh bản người dùng đã xóa/đổi có chủ đích.
- Apps: danh mục module thực có; Settings: cấu hình thực đang dùng, không tạo cấu hình giả, mở module mới, đổi tên pháp nhân, thuế, tài khoản ngân hàng hoặc mail để làm demo đẹp.
- Work Item Catalog trong TANPHAT ONE: kiểm dữ liệu hiện có, nếu trống và cần trình diễn thì thêm một số danh mục tư vấn khảo sát/thiết kế trung tính đúng field/constraint, namespace riêng; không áp hạn mức/quy trình công ty chưa chốt. Các nhánh nghiệp vụ chưa có menu không thuộc yêu cầu thêm dữ liệu.
- Mọi chỗ đang lọc 'của tôi', 'đang mở', 'tuần này' hoặc 'đã hạch toán' phải có hướng dẫn xem đúng dữ liệu; không đổi state pháp lý/tài chính chỉ để vượt bộ lọc.

A6. Kiểm và bàn giao batch A
- Odoo/HTTP admin đọc đủ số mới, mở record/link; native To-do theo cột, lịch theo tuần, kênh/12 tin và 2 dashboard đều dùng được. Chụp ảnh thực và tự xem, không lấy screenshot static làm bằng chứng live.
- planner.dev không thấy private To-do/calendar/channel hoặc dashboard tài chính mới; kiểm direct RPC/ORM lẫn UI. Scope bốn dự án giả và hồ sơ cũ giữ nguyên theo policy. Không tạo mail/push cho người khác.
- Hash/field compare dữ liệu ngoài fixture, invoice còn draft, expenses còn draft, user/grant/password không đổi; công thức/analytic allocation đúng. Phân biệt mail.message mẫu với mail.mail gửi đi: 12 tin mẫu không đồng nghĩa 12 email.
- Verify chạy lại không thêm trùng; test rollback/failed partial import không để dữ liệu nửa bộ. Không dùng 'ON CONFLICT bỏ qua' để che mismatch ownership/field.
- Ghi docs/demo/ODOO_NATIVE_SAMPLE_DATA.md và bảng coverage đủ 14 mục menu gồm kết quả thực, hướng dẫn mở, số lượng, actor, evidence/gap. Cập nhật status/changelog, finish/check đúng batch sau test thực; thiếu mục phải ghi PARTIAL, không tuyên bố đã đủ.

4. Batch B — Việt hóa toàn bộ giao diện đang sử dụng

B1. Phạm vi và thuật ngữ
- Bao phủ tất cả app đã cài trong menu hiện tại, Home mới nếu đã bàn giao, menu con/tab/form/list/kanban/search/filter/action/state, validation/notification/empty/loading/error messages, tooltip/placeholder, dialog tạo/sửa/xóa/xuất, tên cột/biểu đồ/báo cáo thường dùng.
- Bao gồm giao diện native TP Projects/danh mục, dashboard mới, To-do/Calendar/Discuss và các phần auth native/React đã có nếu còn chuỗi hiển thị chưa dịch. Với auth/React chỉ đổi bản dịch/nội dung, không thay luồng đăng nhập/MFA/session/API, không tự cài addon login đang chờ audit.
- 'Toàn bộ' ở đây là toàn bộ bề mặt người dùng của các app đang cài và luồng hiện có; không dịch source code của 644 module chưa cài, log/traceback/debug kỹ thuật, tài liệu upstream hoặc tên riêng dữ liệu thật. Apps/Settings dịch nhãn công cụ, không đổi technical module name/dependency key.
- Giữ TANPHAT ONE, Odoo, BASE, tên TP chuẩn (TP Projects, TP Contracts, TP Survey, TP Design, TP Tasks, TP HR, TP Finance, TP Documents, TP Dashboard); có thể thêm chú giải Việt đúng màn hình thật. Giữ ERP, CRM, WBS, API, URL, ID, UUID, PDF, Excel, PostgreSQL, OAuth, MFA/2FA khi phù hợp; lần xuất hiện đầu có giải thích Việt ngắn nếu người dùng cần.
- Không coi Home/Save/New/Delete/Submit/Review/Reject/Draft là từ đặc thù để bỏ qua. Dịch theo ngữ cảnh và nhất quán; không dùng một bản dịch cho mọi nghĩa của 'Post', 'Return', 'Done' hoặc 'Request'.
- Viết bảng thuật ngữ trước khi dịch; ví dụ To-do → Việc cá nhân; Discuss → Trao đổi; Calendar → Lịch làm việc; Contacts → Khách hàng & đối tác; Timesheets → Giờ làm việc; Employees → Nhân sự; Expenses → Chi phí; Invoicing → Hóa đơn; Dashboards → Bảng tổng hợp; Settings → Cài đặt; Apps → Ứng dụng Odoo. Không đổi Invoicing thành kế toán đầy đủ hoặc TP Finance đã hoàn thiện.
- New/Create → Tạo mới; Edit → Chỉnh sửa; Save → Lưu; Delete → Xóa; Search → Tìm kiếm; Filter → Bộ lọc; Group By → Nhóm theo; Draft → Nháp; In review → Đang rà soát; Returned → Trả lại; Posted invoice → Hóa đơn đã hạch toán. Chốt từ theo ngữ cảnh, giữ distinction review/approval/sign/effectivity đã có.
- Giai đoạn To-do: Inbox → Hộp việc, Today → Hôm nay, This Week → Tuần này, This Month → Tháng này, Later → Để sau, Done → Hoàn thành, Cancelled → Đã hủy. Dịch nhãn hiển thị; không tự thay state key hoặc stage ID.

B2. Cơ chế bản dịch và cấu hình
- Kiểm vi_VN active chưa; kích hoạt và nạp bộ dịch native của các module đã cài bằng tooling Odoo đúng phiên bản. Không download/cài ứng dụng mới để lấy ngôn ngữ, không -u all. Kích hoạt ngôn ngữ và import terms là thao tác được yêu cầu trong batch này, phải backup trước.
- Đặt admin của môi trường demo dùng vi_VN để người dùng nhìn thấy kết quả ngay. Test actors/fixture có thể dùng vi_VN. Không mass-write user ngôn ngữ/timezone của người thật khác hoặc default portal; ghi cách tự chọn ngôn ngữ trong hồ sơ cho họ. Không đổi mật khẩu/group/grant.
- Custom addon dùng i18n/vi.po, Python _()/env._(), JS _t/native translation API và QWeb translatable strings đúng source hiện tại. Nếu chuỗi chưa được trích xuất, sửa tối thiểu để hỗ trợ dịch, không đổi logic. Giữ placeholder/tham số/plural/HTML/escaping và msgctxt chính xác.
- Không sửa catalog trong odoo/ hoặc addons/. Khoảng thiếu native phải có cơ chế override/delivery tương thích Odoo20 trong custom_addons hoặc tooling import translation có kiểm soát, idempotent và có file nguồn catalog trong Git. Phân biệt code terms JS/Python được nạp từ addon với DB field/menu/view translations: test thực đường tải, không giả định import PO chéo module là đủ cho mọi chuỗi.
- Không runtime replaceText/MutationObserver thay chữ toàn DOM, không regex đổi toàn repo, không dịch technical identifier, action tag, route, model/field/XML ID, database name, state key, Excel header mapping hoặc JSON key/OpenAPI enum.
- Dịch menu/view/selection/display-name có translatable field bằng locale, giữ en_US nguyên vẹn. Không đổi hàng loạt tên record để dịch stage; field không translate thì phân tích phạm vi ảnh hưởng, chỉ xử lý dữ liệu giả riêng khi an toàn và ghi nhận. Không ghi đè tên công ty/đối tác/dự án thật hoặc bản gốc toàn hệ thống.
- Tên bản ghi cũ dùng en_US làm baseline không được khiến seeder hiểu là mất record; lookup XML ID, test invariants theo ID/state và ngữ cảnh en_US khi đối chiếu tên gốc.
- Giữ định dạng số/tiền/ngày theo locale/currency: 1.234.567,89, ngày dd/mm/yyyy và VND theo chuẩn hiện hành; không thay stored amount/rate, timezone hoặc datetime chỉ vì đổi cách hiển thị. API/DTO giữ machine format, FE không parse ngược chuỗi đã dịch làm số nghiệp vụ.
- Không đưa thuật ngữ CNTT vào nhãn người dùng nếu không giúp thao tác. Nội dung hồ sơ giả mới nên viết tiếng Việt tự nhiên; giữ provenance rõ ràng.

B3. Kiểm thử Việt hóa
- Lập ma trận coverage từng ứng dụng và luồng, gồm chính xác nhãn còn tiếng Anh, vị trí, quyết định giữ/dịch/lý do. Không lấy số dòng PO hoặc grep hết tiếng Anh để tuyên bố 100%.
- Kiểm cả vi_VN và en_US: menu/action/state IDs và record scope không đổi; chuyển lại English đọc được bản gốc, không mất nội dung user nhập. Chọn ngôn ngữ không mở thêm quyền.
- Kiểm UI desktop/mobile, zoom 125%/150%, tiếng Việt có dấu, nhãn dài/tab/button không bị cắt, search có/không dấu khi đã có chức năng đó. Icon không thay thế lời giải thích cần thiết.
- Mở ít nhất list/form/kanban phù hợp của từng app; dialog tạo/sửa/xóa, filter/groupby/export, dashboard chart/header và profile menu. Apps/Settings phải kiểm bằng actor có quyền, không cấp admin cho người thường để chụp đủ ảnh.
- Auth: nếu đổi chuỗi React/native, chạy typecheck/build/unit và E2E login/expiry/logout/MFA liên quan; không tự mở scope sửa session. Phân biệt thông báo lỗi người dùng cần dịch với server traceback/log phải giữ để debug; không hiển thị stacktrace mới ra UI.
- Python/JS/PO lint/check placeholders/catalog theo phần thay đổi; Odoo install/upgrade test DB cô lập, HOOT hoặc browser smoke phù hợp; React checks chỉ khi React đổi. Test số liệu dashboard không đổi trước/sau locale và record/key vẫn khớp seeder.
- Hết lượt kiểm mọi màn hình còn tiếng Anh thông thường chưa xử lý phải ghi gap cụ thể, không nói Việt hóa xong toàn hệ thống khi mới đổi menu chính. Từ đặc thù được giữ có glossary kèm lý do.

5. Bàn giao cuối cùng

Sau mỗi batch cập nhật status/changelog và tài liệu liên quan. Cuối hai batch có:
1) Bảng coverage đủ Discuss/To-do/Calendar/TANPHAT ONE/Contacts/CRM/Dashboards/Invoicing/Project/Timesheets/Employees/Expenses/Apps/Settings: có gì, thêm gì, còn gap, actor và cách xem.
2) Runbook dữ liệu và seed/verify tái lập, snapshot, dữ liệu cũ được bảo toàn, không có email/push tới người khác; 4 project dùng chung, không thêm trùng.
3) docs/i18n/VI_GLOSSARY_AND_COVERAGE.md (hoặc tên tương đương đã có): thuật ngữ giữ nguyên, bản dịch, ma trận màn hình, gap; config kích hoạt ngôn ngữ và cách quay lại en_US.
4) Ảnh thực từ các app và Home nếu đã có, test pass/fail/skip, URL dev và tài khoản hiện có; không mật khẩu/log nhạy cảm.

Chạy git diff --check, scripts/ai_workflow.py finish đúng CHG-ID/batch sau khi kiểm thực, rồi check. Shell phải dừng nếu bước bắt buộc lỗi, không ghi pass chỉ vì lệnh cuối trả 0. Không finish checkpoint của agent khác.

Báo cáo kết quả ngắn, phân biệt 'dữ liệu đã đủ cho kịch bản trình diễn' và 'chức năng nghiệp vụ đã nghiệm thu'. Không tự đóng UI-HOME-001/TODO-001 nếu chỉ tái sử dụng mà chưa audit đủ; các audit UI-DEMO-001/002, AUTH-002/C01 và cổng pilot vẫn riêng. Không commit/push hoặc mở duyệt BASE/ký/hiệu lực/thanh toán/grant người dùng thật.
```

## Hướng dẫn giao việc

Gửi prompt này cho Claude sau khi lượt Home/TODO đang chạy bàn giao, hoặc cho chính Claude đó tiếp tục tuần tự. Không chạy hai agent cùng sửa translation/Home/task security hoặc cùng upgrade dev/checkpoint. Prompt đã cho phép thực hiện hai batch trong phạm vi trên; không cần hỏi lại chỉ để thêm từng việc/lịch/nhãn đã mô tả.
