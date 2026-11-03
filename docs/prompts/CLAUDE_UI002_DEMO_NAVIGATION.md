# UI-DEMO-002 — Làm rõ thanh điều hướng native Odoo

Copy toàn bộ nội dung bên dưới cho Claude, hoặc yêu cầu Claude đọc và thực thi file này.

```text
Làm việc trong C:\TANPHAT ONE.
Task: UI-DEMO-002 — Thiết kế và triển khai thanh điều hướng dễ hiểu, đầy đủ cho bản demo native Odoo TANPHAT ONE.
Chọn CHG-YYYYMMDD-NNN mới chưa dùng. Không commit/push/deploy.

1. Mục tiêu và quyền triển khai

Hãy triển khai đến bản chạy được trên trình duyệt, không dừng ở đề xuất hoặc ảnh mockup.

Thanh hiện tại là một hàng tím gồm “TANPHAT ONE – Demo”, TP Dashboard, TP Projects, TP Survey, TP Design, TP Contracts, TP Tasks, TP HR và dấu “+”. Người dùng khó hiểu tên tiếng Anh, không biết còn phân hệ nào và phải tìm dưới dấu cộng.

Kết quả cần đạt: người lần đầu dùng biết hệ thống có những mảng nào, mỗi mảng dùng làm gì, đang đứng ở đâu và mở được các chức năng hiện có với ít bước. “Đầy đủ” nghĩa là điều hướng đủ các màn hình hiện có theo quyền, không phải phát triển thêm nghiệp vụ chỉ để làm nhiều menu.

Yêu cầu mới này cho phép cải tiến điều hướng demo, thay lựa chọn UX “giữ nguyên menu” được ghi tại CHG-20261030-003 trong đúng phạm vi này. Giữ phần làm mới giao diện SCSS của CHG-003; không xây lại dashboard, nội dung nghiệp vụ hay app switcher toàn Odoo. Không cần hỏi lại màu/layout thường lệ.

Đây vẫn là demo native theo DEC-024, không thay hướng sản phẩm React + API Odoo theo DEC-001/023. Không mở production/pilot hoặc tự nghiệm thu UI-DEMO-001, AUTH-002, C01.

2. Đọc source và preflight

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/CHANGELOG.md (các mục mới nhất), docs/AI_CHANGE_WORKFLOW.md, docs/AI_COORDINATION_WORKFLOW.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/architecture/TP_PRODUCT_NAMING.md, docs/architecture/TP_UI_DEMO_001_SPEC.md, ops/runbooks/UI_DEMO_001.md, docs/demo/UI_DEMO_001_PRESENTATION.md và README addon demo.

Áp dụng skill frontend-design tại C:\Users\vuduc\.codex\skills\frontend-design\SKILL.md; nếu đường dẫn thay đổi thì tìm và đọc skill tương ứng. Báo nguồn skill đã dùng. Đọc skills/odoo-web-guidelines/SKILL.md và các guideline JavaScript/SCSS/assets liên quan. Nếu bổ sung test Odoo, đọc hướng dẫn test/security tương ứng.

Kiểm git status/diff, checkpoint, ai_workflow.py check, runtime ownership và source hiện tại. Lấy snapshot trước thay đổi gồm cả .scss; checker hiện tại không thay kiểm diff đầy đủ. Không reset/clean/stash, xóa checkpoint hoặc ghi đè thay đổi phiên khác. Nếu batch khác đang sửa cùng file, báo rõ phần xung đột, không finish thay.

Đọc chính source Odoo 20 local trước khi tích hợp:
- custom_addons/tp_demo_workspace/views/tp_demo_menus.xml và các action/view.
- custom_addons/tp_demo_workspace/static/src/shared/ và __manifest__.py.
- addons/web/static/src/webclient/navbar/navbar.js, navbar.xml, navbar.scss.
- addons/web/static/src/webclient/menus/menu_service.js và component dropdown/dialog phù hợp.

Khi preflight đạt, chạy .\.venv\Scripts\python.exe scripts\ai_workflow.py start trước lần sửa đầu tiên.

3. Thiết kế điều hướng

Ưu tiên thanh đầu trang hai tầng trên desktop nếu cần để đọc thoải mái:
- Tầng nhận diện: nút ứng dụng native, TANPHAT ONE – Demo hoặc TANPHAT ONE + badge Demo rõ ràng, nút “Tất cả phân hệ”, các tiện ích native, công ty và tài khoản.
- Tầng nghiệp vụ: sáu nhóm ngắn gọn bên dưới. Không chen 12 tên dài vào một hàng rồi thu nhỏ chữ.

Wireframe mục tiêu, không bắt buộc chính xác số pixel:

[Ứng dụng] TANPHAT ONE [Demo]   [Tất cả phân hệ]     [Thông báo] [Công ty] [Tài khoản]
[Tổng quan] [Dự án & công việc ▾] [Hợp đồng & hồ sơ ▾] [Kinh doanh ▾] [Nguồn lực ▾] [Đề nghị]
Trang hiện tại / ngữ cảnh phân hệ theo breadcrumb native

Sáu nhóm:
A. Tổng quan: TP Dashboard.
B. Dự án & công việc: TP Projects, TP Survey, TP Design, TP Tasks.
C. Hợp đồng & hồ sơ: TP Contracts, TP Documents.
D. Kinh doanh: CRM, Bid; chỉ xuất hiện khi cây menu server có quyền tương ứng.
E. Nguồn lực: TP HR, TP Finance.
F. Đề nghị: Request/Đề nghị BASE.

Đây là nhóm điều hướng theo công việc, không phải thứ tự phê duyệt, phòng ban hoặc nhóm bảo mật. Hợp đồng phải vẫn mở được cho kỹ sư theo quyền hiện có; không nhét Hợp đồng vào nhóm chỉ business mới thấy.

Nhãn menu chính ưu tiên tiếng Việt. Giữ chín tên TP đã chốt trong phụ đề/mô tả/tooltip và bảng phân hệ; không đổi technical name, XML ID, action path, model hoặc API chỉ để đổi nhãn.

“Tất cả phân hệ” mở panel/dialog rộng có tìm nhanh và chia nhóm, trình bày cho mỗi mục:
- Icon đơn giản, nhất quán, dùng asset/icon local sẵn có.
- Tên tiếng Việt nổi bật.
- Tên phân hệ chuẩn nhỏ hơn.
- Một câu mô tả ngắn theo công việc người dùng.
- Mục con hiện có, có thể bấm trực tiếp.
- Nhãn “Minh họa” ở đúng phần minh họa; phần hỗn hợp ghi rõ phần nào minh họa.

Tìm nhanh CHỈ tìm tên/mô tả menu mà tài khoản được thấy, không tìm hồ sơ nghiệp vụ. Không phân biệt hoa/thường hoặc dấu tiếng Việt; hỗ trợ các từ quen thuộc như project/dự án, contract/hợp đồng, bid/đấu thầu, request/đề nghị/yêu cầu, hồ sơ/tài liệu. Có nút xóa và trạng thái không có kết quả dễ hiểu. Kết quả tìm kiếm không mở link ngoài quyền.

Mục đang chọn có nền/đường nhấn và trạng thái active rõ; nhóm cha vẫn được nhận diện khi mở mục con. Dropdown có tiêu đề nhóm, mục con và mô tả; mở bằng click/chạm và bàn phím, không bắt buộc hover. Hover chỉ hỗ trợ nhận diện.

Desktop tối đa hai tầng điều hướng; không tạo ba hệ menu trùng nhau. Nếu thêm navigation mới thì phần section native trong app Demo phải được tích hợp/ẩn có điều kiện cho đúng app, không để hai thanh cùng chức năng. Giữ nguyên navigation các app khác.

4. Danh mục đầy đủ phải ánh xạ

Đối chiếu ID thực trong source trước khi code. Các điểm đến hiện tại:

- Tổng quan / TP Dashboard: action_demo_dashboard.
- Dự án / TP Projects: Danh sách dự án (action_demo_projects), Tổng quan dự án (action_demo_project_overview).
- Khảo sát hiện trường / TP Survey: action_demo_survey — Minh họa.
- Hồ sơ thiết kế / TP Design: action_demo_design — Minh họa.
- Hợp đồng / TP Contracts: Hợp đồng (action_demo_contracts), Phiên bản rà soát (action_demo_revisions), Luồng rà soát (action_demo_contract_flow).
- Công việc & tiến độ / TP Tasks: action_demo_tasks.
- Nhân sự / TP HR: Danh bạ nhân sự (action_demo_employees), Năng lực và phân bổ (action_demo_staffing — Minh họa).
- Tài chính & chi phí / TP Finance: Tổng hợp tài chính (action_demo_finance), Số tiền dòng hợp đồng (action_demo_line_amounts). Tổng hợp có cả nguồn Odoo và số minh họa; không mô tả là kế toán/thanh toán đã hoàn thiện.
- Tài liệu & hồ sơ / TP Documents: action_demo_documents.
- Cơ hội kinh doanh / CRM: action_demo_crm.
- Dự thầu / Bid: action_demo_bid — Minh họa.
- Đề nghị nội bộ / Request: action_demo_request — Minh họa; BASE vẫn là nơi phê duyệt chính thức.

Các ID trên thuộc namespace tp_demo_workspace. Không hardcode numeric database ID hoặc tự tạo route mới khi action đã có. Không đưa Settings, Apps quản trị, AI, Data Lake, bảng lương, nghiệm thu, thanh toán hoặc ký duyệt thành phân hệ hoạt động trong task này.

Lập bảng toàn bộ leaf menu trước/sau theo actor để chứng minh không mất điểm đến. Nhóm không có action chỉ mở/đóng danh sách; không báo thành công giả. Giữ XML ID và action hiện có; được thêm menu nhóm trong addon demo và điều chỉnh parent/sequence của menu demo nếu cần, giữ groups đúng ở mọi nhánh.

5. Tích hợp native Odoo và phạm vi sửa

Chỉ sửa custom_addons/tp_demo_workspace/, test cùng addon, tài liệu bàn giao liên quan. Tổ chức feature mới trong static/src/navigation/ (JS/XML/SCSS), đọc cây menu/selection qua service native. Được thêm asset/test khai báo trong manifest khi cần.

Nguồn quyền/menu là cây server trả từ /web/webclient/load_menus, qua menu service hiện có. Metadata static theo XML ID chỉ cung cấp nhãn/icon/mô tả, không tạo thêm action link không tồn tại trong cây menu được phép. Không suy quyền từ login, tên chức danh, góc nhìn hoặc frontend flag. Không thêm sudo/ACL/grant để hiện đủ 12 mục cho mọi tài khoản.

Giữ cơ chế action/menu native như menuService.selectMenu(actualMenu), URL deep link, action context/domain, breadcrumb, back/forward và lịch sử. Không điều hướng bằng URL tự bịa, iframe, frontend React hoặc generic RPC để né quyền.

Ưu tiên template inheritance QWeb/OWL và extension point sẵn có. Không sửa addons/web, odoo/ hoặc cài theme Enterprise. Nếu bắt buộc dùng patch trong custom addon để gắn component/behavior, chỉ patch tối thiểu, giải thích lý do, có điều kiện app Demo và regression khi rời app. Không monkey-patch router/service toàn cục hay copy toàn bộ WebClient/NavBar upstream.

App gốc demo là tp_demo_workspace.menu_demo_root. Scope customization theo app hiện tại, không chỉ theo URL /odoo hoặc có module cài trong database. Tất cả page native được mở trong app Demo cũng phải có cùng điều hướng; chuyển sang app “TANPHAT ONE” khác phải giữ giao diện native của app đó. Không xóa/ẩn app còn lại hoặc đổi tài khoản/quyền để tránh nhầm.

Lưu ý source thực: NavBar.adapt() dùng phép đo kích thước, appSubMenus, currentAppSectionsExtra, .o_menu_sections_more, data-section và giả định nút More rộng 46px. Không chỉ đổi dấu “+” thành chữ dài rồi làm vỡ overflow. Nếu giữ vùng overflow native, bảo toàn contract này; selector “Tất cả phân hệ” đặt ngoài vùng đo hoặc cập nhật logic đo đúng trong phạm vi demo. Odoo 20 checkout hiện dùng Owl API riêng; không chép pattern phiên bản cũ chưa kiểm.

SCSS scope bằng class riêng chỉ khi active demo. Dropdown/dialog portal phải có namespace riêng vì có thể render ngoài navbar. Dọn listener/class khi unmount/rời app, không dùng setInterval để sửa DOM. Không dùng CSS global để recolor/ẩn mọi .o_main_navbar, .dropdown-menu hoặc app switcher.

Giữ thông báo, chọn công ty, tài khoản, đăng xuất, menu ứng dụng, huy hiệu “Dữ liệu trình diễn” và banner neutralized database. Không xóa cảnh báo môi trường để chụp ảnh đẹp. Giữ dữ liệu, state, workflow, business projection, read-only và grant như hiện tại. Không sửa login/AUTH-002, React, API/OpenAPI, seed hay tooling chung nếu không cần cho navigation.

6. Thiết kế hình ảnh và responsive

Phong cách doanh nghiệp tư vấn cầu đường: rõ, gọn, dễ trình bày cho người không chuyên CNTT. Kế thừa màu của CHG-003: xanh đậm #17324F, xanh tương tác #2F6DB3, nền trắng/sáng, chữ phụ đủ tương phản. Tự chọn token chi tiết nhất quán; không dùng rainbow icon, gradient trang trí dày hoặc hiệu ứng liên tục.

Chữ menu desktop khoảng 14–16px, chiều cao vùng bấm 40–44px; cỡ chữ không bị ép xuống để nhét menu. Icon luôn đi với chữ; tooltip chỉ bổ sung thông tin. Tương phản chữ thường ít nhất 4.5:1; active/hover/focus có tín hiệu khác màu đơn thuần.

Animation mở/đóng khoảng 120–180ms, tôn trọng prefers-reduced-motion. Dùng font local/sẵn có hỗ trợ tiếng Việt, không CDN. Căn chỉnh badge demo và tiện ích gọn; không để brand dài chiếm hết hàng.

Ở laptop/tablet, thu gọn nhóm hợp lý vào nút có chữ rõ nghĩa như “Phân hệ”, luôn có đường xem đầy đủ. Không dùng mỗi dấu “+”/“...” không giải thích. Mobile dùng drawer/panel có nhóm lồng, tìm nhanh, vùng bấm đủ lớn; nội dung dài cuộn trong panel, trang không bị tràn ngang.

Keyboard: mở bằng Enter/Space, di chuyển theo semantics component native, Tab/Shift+Tab được, Esc đóng, focus trả về nút mở; dialog/drawer có focus management đúng. Navigation tới trang dùng semantics link/menu phù hợp, không gán role=tablist nếu không phải tab panel.

7. Thiết kế ngắn rồi triển khai liên tục

Bổ sung đặc tả mục navigation trong TP_UI_DEMO_001_SPEC.md: sơ đồ nhóm, mapping nhãn Việt/tên chuẩn/XML ID/action, quyền, wireframe, tokens, responsive và tiêu chí nghiệm thu. Phân biệt thiết kế mới với phần runtime đã có.

Tự review theo frontend-design, sau đó triển khai và test, không dừng chờ phê duyệt wireframe/màu. Không mở feature ngoài scope khi thấy menu còn thiếu nghiệp vụ. Không dùng trạng thái pending audit của bản demo làm lý do chặn cải tiến UI đã được người dùng yêu cầu; giữ nguyên các cổng nghiệp vụ thật.

8. Kiểm thử và bằng chứng

Chạy trên tp_tanphat_demo_ui001 và DB test demo sở hữu riêng theo scripts/ui_demo.py/runbook; không cài/upgrade/seed tp_tanphat_dev hoặc tp_tanphat_test. Không drop/reset database hoặc kill process khác. Chỉ rebuild/restart demo theo tool có ownership guard, giữ nguyên credential, không in mật khẩu/session vào output.

Kiểm browser live cho cả hai actor:
- demo.lanhdao: thấy đủ 12 phân hệ hiện có và toàn bộ leaf menu ở mục 4. Mở từng leaf action đúng đích, gồm CRM/Bid/Request, nhóm native và client actions. Active state/breadcrumb đúng.
- demo.kysu: chỉ scope dự án hiện có; không có Kinh doanh/CRM/Bid trong menu, panel hoặc kết quả tìm. Finance vẫn mở đúng màn hình giới hạn, không có tiền/tệp tài chính. Không sửa policy để làm navigation “đầy đủ”.
- Link trực tiếp và reload vào project/contract/action minh họa giữ app/menu active đúng; back/forward hoạt động. Không làm mất context dự án do thêm một doAction rỗng để đồng bộ menu.
- Rời app Demo sang app native khác rồi quay lại: không còn class/handler/theme demo rò sang app khác; các tiện ích, menu người dùng và logout vẫn hoạt động.
- Tìm “hop dong”, “hợp đồng”, “contract”, “du an”, “dau thau”, “request” cho kết quả đúng theo quyền; kết quả rỗng có lời dẫn.
- 1440x900, 1366x768, 1024x768, 768 và 375px; kiểm resize và zoom 125%/150%. Không chồng brand/menu/systray, mất mục cuối, bị cắt dropdown, tràn ngang toàn trang hoặc focus bị che.
- Chụp và TỰ XEM ít nhất desktop toàn thanh, panel đầy đủ, dropdown Hợp đồng, kết quả tìm, tài khoản kỹ sư, mobile và app khác sau khi rời Demo. Sửa layout rồi chụp lại.
- Không lỗi console/network không giải thích được.

Thêm test JS/OWL phù hợp tooling checkout cho logic mapping/filter/active và trường hợp không có menu quyền; thêm test service/menu Odoo nếu thay cấu trúc nhóm. Không viết test chỉ so chuỗi CSS. Browser mock không thay live Odoo.

Chạy test native assets/XML và Odoo tests tp_demo_workspace hiện có trên DB test demo, vì task chạm menu/routing/asset; báo đúng số pass/fail/skip và target. Ruff cho Python nếu thực sự thay Python. React typecheck/build chỉ khi React bị ảnh hưởng; không dùng chúng thay kiểm assets OWL.

9. Bàn giao

Cập nhật PROJECT_STATUS.md, CHANGELOG.md, ROADMAP.md, TP_UI_DEMO_001_SPEC.md, README addon; runbook và kịch bản trình bày nếu đường click thay đổi. Không tự ghi DEC mới cho lựa chọn màu/layout hoặc mở nghiệp vụ. Ghi UI-DEMO-002 IMPLEMENTED_PENDING_AUDIT sau khi triển khai, không tự TECHNICAL_ACCEPTED.

Chạy git diff --check; ai_workflow.py finish --change-id CHG-ID-moi --check với lệnh/kết quả thực, rồi ai_workflow.py check. Không finish thay batch khác, không commit/push.

Báo cuối ngắn, dễ hiểu:
1) Trước/sau: nhóm menu, tên Việt và cách tìm phân hệ.
2) Danh sách file sửa, phương án native extension, snapshot phần ngoài scope không đổi.
3) Bảng mapping đủ leaf action và khác biệt theo hai actor.
4) Ảnh desktop/mobile/panel và đường dẫn local; mật khẩu không đưa vào ảnh/chat/Git.
5) Test thực chạy, số lượng, target/log và hạn chế còn lại.
6) URL http://127.0.0.1:18109/odoo, runtime đang chạy hay đã dừng, cách mở lại. Nếu không có lỗi vận hành thì để demo local sẵn cho người dùng xem.

Kết quả cuối phải là thanh điều hướng đã thay đổi trên bản demo thật, dễ hiểu với lãnh đạo, đủ điểm đến theo quyền và giữ nguyên chức năng nghiệp vụ hiện có.
```
