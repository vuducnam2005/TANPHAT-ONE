# UI-HOME-001 — Trang Home dạng lưới ứng dụng cho Odoo native

Ngày chuẩn bị: 02/11/2026 (Asia/Saigon). Trạng thái: `PROMPT_READY`, chưa triển khai. Người dùng đồng ý dựng trang Home native theo ảnh lưới ứng dụng; phiên chính giữ vai trò điều phối, Claude thực thi. Đây là trang chọn ứng dụng, không phải dashboard KPI hoặc một hệ thống nghiệp vụ mới.

## Căn cứ đã kiểm

- Native dev: `http://127.0.0.1:18069/odoo`, DB `tp_tanphat_dev`. Demo cũ trên 18109 là môi trường khác, không cài Home lên đó trong task này.
- HTTP đăng nhập admin và planner.dev, đọc `/web/webclient/load_menus` ngày 02/11: admin có 14 root apps, planner có 9; Home chưa tồn tại. Kết quả read-only ở `.local/home001-preparation/runtime-menus.json`; phải kiểm lại lúc triển khai, không hardcode số lượng/menu ID theo snapshot.
- Admin chưa có `res.users.action_id`. Home Action của người dùng khác chưa được audit; không được ghi đè hàng loạt.
- Source Odoo hiện tại dùng `@odoo/owl` với `proxy`, `signal`, `computed`, `useProps`; không copy nguyên mẫu Owl từ bản cũ. `menuService.getApps()/getAll()/getMenuAsTree()` đọc cây quyền, `selectMenu(menu)` gọi action và đặt current app. `WebClient._loadDefaultApp()` chọn root đầu tiên khi không có action; action plugin ưu tiên `user.homeActionId` nếu có. Phải kiểm hành vi history/default bằng test thực.
- Cây TP dev hiện chỉ có TANPHAT ONE → TP Projects và Work Item Catalog; chưa có menu native Contracts/Bid/Request/Survey/Design riêng trong dev. Không dựng ô giả trỏ về cùng một màn hình để làm đầy Home.
- Đã kiểm README/manifest/template/source của [OCA web_responsive 20.0](https://github.com/OCA/web/tree/6ac74409cd559529374236476353d453d5568c5e/web_responsive): có fullscreen app menu, tìm kiếm, thiết lập Redirect to Home; đồng thời tác động WebClient/NavBar, chatter, form/list/mobile, thêm trường user, dependency web_tour/mail, excludes web_enterprise. Kho khai báo LGPL-3/installable, chưa chạy compatibility test trên checkout này. Vì phạm vi hiện tại chỉ Home, phương án triển khai là addon riêng gọn; không cài OCA hoặc sao chép code Enterprise trong batch này.

## Prompt giao Claude

```text
Làm việc trong C:\TANPHAT ONE. Task UI-HOME-001: triển khai trang Home dạng lưới ứng dụng cho native Odoo Community, gần bố cục ảnh người dùng đã chọn. Làm bản chạy được trên test, kiểm đạt rồi cài dev18069. Không commit/push/deploy production.

1. Preflight và phạm vi

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/DECISIONS.md, docs/ROADMAP.md, docs/architecture/TP_PRODUCT_NAMING.md, docs/AI_COORDINATION_WORKFLOW.md và prompt này. Đọc skill C:/Users/vuduc/.codex/skills/frontend-design/SKILL.md và skills/odoo-web-guidelines/SKILL.md cùng guidelines phù hợp, thông báo đã áp dụng. Nếu đường dẫn skill thay đổi thì tìm lại.

Kiểm git status/diff, checkpoint, runtime và menu thực trước sửa. Giữ thay đổi chưa commit của người khác, nhất là TODO-001 có thể đang chạy song song. Chọn CHG-ID chưa dùng, chạy scripts/ai_workflow.py start. Nếu có batch khác đang dùng checkpoint, không finish thay họ; phối hợp bàn giao, không ghi đè file/status đang được sửa đồng thời. TODO-001 không phải phụ thuộc để code Home; To-do có menu nhưng lỗi quyền chưa sửa thì vẫn là blocker riêng của To-do, không sửa hoặc che lỗi đó ở task Home.

Được tạo addon custom_addons/tp_web_home/ (tên kỹ thuật đề xuất, kiểm không trùng), test, runbook, config tooling cần để chạy addon và handoff. Ưu tiên depends=['web']; không thêm model dữ liệu nghiệp vụ hoặc dependency addon TP/OCA chỉ để lấy tên/icon. Không sửa odoo/, addons/, frontend React, OpenAPI, API nghiệp vụ, auth/session/login hoặc source tp_demo_workspace. Không cài web_responsive, web_enterprise hoặc thêm theme pack. Không đổi grant/ACL của module nghiệp vụ, mật khẩu/user group, công ty hay số liệu giả đã nạp.

2. Thiết kế cần làm

- Home là màn hình chọn ứng dụng kiểu ảnh: nền toàn vùng nội dung, lưới icon có nhãn phía dưới, khoảng cách thoáng, thanh native phía trên vẫn có chọn công ty, thông báo và user menu. Không chuyển thành màn hình nhiều thẻ KPI hoặc landing page quảng cáo.
- Đầu nội dung gọn: TANPHAT ONE, dòng 'Không gian làm việc', ô 'Tìm ứng dụng…'. Nếu chưa có logo được duyệt, dùng wordmark chữ, không tự nhận icon tự vẽ là logo chính thức.
- Palette đề xuất theo ảnh: nền lavender xám #EEEAF4, bề mặt trắng #FFFFFF, chữ #25334B, nhấn tím #71639E, viền #DDD7E8. Đây là màu giao diện, không tự đổi thương hiệu công ty. Có thể dùng mảng chéo nền rất nhẹ bằng CSS; tránh trang trí gây khó đọc.
- Dùng font native hiện có hỗ trợ tiếng Việt; không tải font/CDN hoặc ảnh ngoài khi runtime. Icon dùng tài nguyên Community đã có/ảnh menu được server cung cấp; fallback SVG do dự án tự vẽ hoặc chữ viết tắt nếu không có icon. Không lấy icon Enterprise từ screenshot.
- Icon tile khoảng 68–80px, radius 10–14px và bóng nhẹ, vùng bấm tối thiểu 44px; nhãn 14–16px đọc rõ, tối đa hai dòng, giữ tên TP chuẩn khi dùng. Desktop 6–8 cột tùy width; tablet 4; mobile 2–3 tùy không gian. Không có cuộn ngang ở 375px hoặc zoom 150%.
- Hover nâng 2–3px/đổi bóng trong 120–180ms, focus rõ bằng bàn phím; không hiệu ứng chạy liên tục. Tắt chuyển động khi prefers-reduced-motion. Không dùng màu làm dấu hiệu duy nhất.
- Tìm theo tiếng Việt có/không dấu (bao gồm đ/Đ), tên native và alias tiếng Anh; tìm chỉ trong các ứng dụng actor được thấy. Có nút xóa tìm, thông báo 'Không tìm thấy ứng dụng phù hợp' và cách xóa từ khóa. Không đổi quyền để làm kết quả đầy hơn.
- Nhóm nhẹ tùy cần: 'Công việc & nghiệp vụ' và 'Công cụ hệ thống'; giữ hình thức lưới của ảnh. Không thêm trang cấu hình bố cục/pin/kéo thả trong slice này.

3. Nguồn menu và nội dung ô

Lấy catalog từ menu service native đã lọc quyền cho actor hiện tại. Không đọc ir.ui.menu bằng sudo, không hardcode action/menu numeric ID và không giữ cây menu một user trong global/localStorage dùng chung user khác. Không gọi API để tải dữ liệu tiền/KPI chỉ để hiển thị Home.

Mapping nhãn chỉ áp dụng sau khi XML ID thực sự có trong cây quyền; dữ liệu label/alias tập trung, không giả định module cài rồi mọi user đều nhìn thấy:

XML ID hiện đã kiểm → nhãn gợi ý:
- mail.menu_root_discuss → Trao đổi (Discuss).
- project_todo.menu_todo_todos → Việc cá nhân (To-do).
- calendar.mail_menu_calendar → Lịch làm việc.
- contacts.menu_contacts → Khách hàng & đối tác.
- crm.crm_menu_root → CRM · Cơ hội kinh doanh.
- project.menu_main_pm → Project · Công việc dự án; mô tả ngắn 'Công việc & tiến độ'.
- tp_project.menu_tp_projects → TP Projects · Hồ sơ dự án; mô tả ngắn 'Hồ sơ & phân công'.
- tp_core.menu_work_items → Danh mục công việc, nếu hiển thị shortcut này.
- hr.menu_hr_root → Nhân sự (Employees).
- hr_timesheet.timesheet_menu_root → Giờ làm việc (Timesheets).
- hr_expense.menu_hr_expense_root → Chi phí (Expenses).
- account.menu_finance → Hóa đơn (Invoicing), không gọi là đầy đủ TP Finance/Accounting Enterprise.
- spreadsheet_dashboard.spreadsheet_dashboard_menu_root → Bảng tổng hợp (Dashboards), không ngụ ý đã có KPI điều hành Tấn Phát.
- base.menu_management → Ứng dụng Odoo; base.menu_administration → Cài đặt. Chỉ hiện khi cây server có, không tự suy từ chức danh/admin. Snapshot planner hiện vẫn có Apps; không thay security để làm khác snapshot.

Với tp_core.menu_platform (root TANPHAT ONE), ưu tiên một ô TP Projects trỏ đúng leaf tp_project.menu_tp_projects khi leaf có trong cây quyền, tránh thêm ô root lặp cùng action. Nếu chọn hiển thị thêm Work Item Catalog, đó là shortcut đến leaf thật. Nếu root không có leaf phù hợp thì giữ nhãn native/fallback, không invent destination.

Các root app khác có thật mà không nằm trong mapping vẫn hiển thị tên/icon native, không whitelist cứng làm mất ứng dụng người dùng được cấp. Exclude chính Home khỏi catalog để không tạo vòng lặp. App demo nếu được cài ở môi trường nào trong tương lai phải giữ tên/nhãn Demo; không đổi thành phân hệ production.

Không tạo ô Bid, Request, TP Contracts, TP Survey, TP Design, TP Documents hoặc TP Dashboard chỉ dựa vào tên trong roadmap. Khi chưa có menu native thật thì không hiện. Không đổi nhãn ứng dụng 'Surveys' thành khảo sát hiện trường hoặc đổi native Invoicing thành toàn bộ TP Finance. Home không phải bằng chứng nghiệp vụ hoàn thiện.

4. Tích hợp kỹ thuật native

- Tạo ir.actions.client tag riêng (ví dụ tp_web_home.home), client action đăng ký registry.category('actions'), path duy nhất ví dụ tp-home nếu Odoo hiện tại hỗ trợ. Root menu Home/Trang chủ cho base.group_user, sequence đứng trước app mặc định. Không ghi đè action tag 'home' của Odoo.
- Native /odoo không chứa action/deep link và user không có Home Action cụ thể phải vào trang Home mới qua cơ chế fallback native. Tận dụng root menu order, tránh patch WebClient._loadDefaultApp hoặc rewrite router. Giữ user.homeActionId đã cấu hình; không mass-write res.users.action_id. Nếu nguồn hiện tại khiến fallback không đạt thì ghi rõ bằng test và tìm extension tối thiểu có căn cứ, không tự monkey-patch vòng đời toàn app.
- Có nút Trang chủ với icon ngôi nhà/lưới, accessible label, trong native navbar trên desktop/mobile. Ưu tiên registry systray với component riêng, dùng menu service tìm Home XML ID và selectMenu. Không thay AppsMenu dropdown hiện có hoặc phá nút chín chấm native.
- Click tile qua menu.selectMenu(menu thực). Anchor có href native đúng actionPath/actionID lấy từ menu server để Ctrl/Cmd-click mở tab mới được. Tôn trọng modified click; không dùng href='#' hoặc window.location điều hướng chính. Native action service phải giữ cảnh báo form chưa lưu, breadcrumb, back/forward và current app.
- Nếu root thiếu action, resolve leaf có action theo thứ tự cây quyền; không tự gán action ID từ module khác. Quản lý catalog theo menu service reactive hiện có; nghe/recompute menu reload, company switch, session mới. Không tạo router hoặc menu state song song.
- Namespace JS/template/SCSS o_tp_web_home..., tổ chức file theo feature home. CSS chỉ ở Home; nút navbar phạm vi nhỏ. Không reset .o_web_client/.o_action_manager/global buttons/fonts của app khác. Không sửa registry/service/core bằng patch rộng.
- Không endpoint hay password/session riêng. Native menu/action RPC trong Owl webclient được phép theo cơ chế Odoo; giới hạn không generic RPC của React không có nghĩa tự tạo API public cho Home. Portal/public không được vào backend Home.

5. Test trên DB test tách biệt

Không cài addon vào database test dùng chung đang có nếu thiếu owner/guard. Tạo môi trường test riêng theo tooling/runbook đã có, secrets ngoài Git; dùng dữ liệu giả, không clone hồ sơ thật. Ghi lệnh thật, log và cleanup process đúng ownership.

Server/Odoo:
- Install và upgrade addon mới trên DB cô lập, registry/menu/action/assets hợp lệ, internal được thấy Home, portal/public không được vào backend.
- Action/menu cũ giữ domain, groups và ID/XML ID; không tăng grant/assignment hoặc đổi user group.
- Hai actor có quyền khác nhau nhận đúng app/leaf từ server; quyền đọc record trực tiếp vẫn bị backend chặn. Không ghi hardcoded số app của snapshot vào test.

JS/HOOT phù hợp phiên bản hiện tại:
- Catalog từ root/leaf, app chưa biết vẫn xuất hiện, Home bị loại, TP root/leaf không lặp, không có link khi thiếu action.
- Tìm không dấu/đ/Đ, alias, empty, clear; các ứng dụng không có quyền không xuất hiện trong kết quả.
- Icon thiếu/hỏng có fallback; menu reload không giữ ứng dụng bị thu hồi; không đăng ký listener/hotkey lặp hoặc rò sau unmount.
- Click đúng selectMenu, modified click mở URL native, Home button không bypass guard form chưa lưu; không dùng mock thay live acceptance cho routing.

Browser E2E trên môi trường test:
- /odoo trống action → Home; tile → đúng app; nút Home → Home; reload và back/forward không loop.
- Deep link project/CRM/form giữ điểm đến sau đăng nhập, không bị Home chặn. User có Home Action cụ thể vẫn giữ lựa chọn; logout/login user khác không lộ catalog cũ.
- Form có thay đổi chưa lưu: bấm Home xử lý theo cảnh báo native và không mất dữ liệu khi chọn ở lại.
- Company switch tải đúng cây quyền; không flash catalog của user/công ty trước sau logout/login/switch.
- Bàn phím Tab/Shift+Tab/Enter, focus, tìm/xóa tìm; mobile chạm mở tile và Home. Giữ chức năng chọn công ty, user menu/logout, thông báo/chín chấm và menu từng app.
- Viewport 1440, 1366, 1024, 768, 375px; zoom thật 125%/150%; reduced motion; chụp ảnh và tự xem sửa bố cục. Không console error/unhandled promise/missing assets do addon.
- Nếu test môi trường có tp_demo_workspace, kiểm menu demo vẫn nguyên. Không cần cài Home vào demo18109 để chứng minh; kiểm chung trên DB test hoặc so source/snapshot.

Chạy Ruff cho Python có thêm/sửa; không chạy React suite khi React không đổi. Không viết unit test chỉ lặp hằng số; ưu tiên test catalog/quyền/điều hướng thực. Khi test bắt buộc chưa chạy được, giữ IMPLEMENTED_PENDING_VERIFICATION và không tự nói đã đạt.

6. Cài dev sau test đạt

Yêu cầu người dùng đã cho phép làm trang Home trên native dev; sau khi test đạt có thể cài đúng addon mới vào tp_tanphat_dev tại 18069. Trước cài chụp DB+canonical filestore và cấu hình/runtime metadata cần quay lại, kiểm dump/listing và lưu ngoài Git. Nếu dùng snapshot helper cũ phải đọc guard/ownership trước, không restart server do task khác đang sở hữu.

Không -u all, không install cả repo OCA, không đổi login addon chưa audit hoặc chạy bootstrap seed. Chỉ cài/upgrade tp_web_home; dependency chuẩn xử lý theo manifest, báo rõ phát sinh nếu có. Giữ demo18109/PostgreSQL, dữ liệu bốn dự án/28 task/CRM/invoice/chi phí/To-do (nếu Claude khác đã nạp) và quyền hiện có.

Xác nhận dev live với admin/planner.dev bằng credential sẵn có ngoài Git, không in mật khẩu. Home actor nào chỉ thấy app theo cây quyền actor đó; thiếu CRM/Invoicing ở planner là đúng quyền, không mở group để làm đầy. Native Project và TP Projects vẫn cùng bốn project ID đã liên kết; Home không nhân bản dữ liệu.

7. Bàn giao

Tạo runbook ngắn gồm URL Home thực kiểm, cách đăng nhập hiện có (không mật khẩu), bấm tile/quay Home/tìm kiếm, cài-upgrade và cách gỡ/quay lại native. Menu/action mới phải gỡ sạch khi uninstall trên test; không để Home Action người dùng trỏ tới record bị xóa vì không mass-write field này.

Cập nhật docs/PROJECT_STATUS.md, docs/CHANGELOG.md, docs/ROADMAP.md và runbook/spec bị ảnh hưởng. Ghi source/schema/menu/assets nào đổi, snapshot, test pass/fail/skip, ảnh desktop/mobile, URL dev và giới hạn. Trạng thái IMPLEMENTED_PENDING_AUDIT trước phiên chính kiểm độc lập; không tự đóng TODO-001, UI-DEMO-001/002, AUTH-002/C01 hoặc cổng nghiệp vụ/pilot.

Chạy git diff --check; scripts/ai_workflow.py finish --change-id CHG mới --check "kết quả thực chạy"; scripts/ai_workflow.py check. Không ghi pass nếu shell chạy bước sau mặc dù bước trước đã fail. Không commit/push. Báo cuối cho người dùng ngắn, mở được Home và nêu điều đã test, không chỉ liệt kê file.
```

## Kết quả cần nhìn thấy khi nghiệm thu

Một trang Home có icon/nhãn dễ đọc như ảnh, số ô khác nhau đúng quyền; mỗi ô mở chức năng native hiện hữu. Admin thấy CRM/Project/nhân sự/hóa đơn… theo quyền của admin; planner có ít ô hơn. Trang Home có thương hiệu TANPHAT ONE và nút quay lại từ app khác. Đây là phần điều hướng native tạm thời; định hướng Odoo backend + React riêng, nghiệp vụ và dữ liệu hiện có không đổi.
