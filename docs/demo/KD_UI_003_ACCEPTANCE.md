# KD-UI-003 — Acceptance bảng và màn hình chi tiết KH-KD

Viết trước code ngày 06/11/2026 (CHG-20261106-022). Thiết kế: [KD_UI_003_TABLES_AND_DETAILS_DESIGN.md](../ui/KD_UI_003_TABLES_AND_DETAILS_DESIGN.md).

Thứ tự chạy:

1. Clone cô lập `tp_tanphat_kdui003_20261106`, cổng 18389, source copy riêng tại `.local/kd-ui003/source`.
2. Sau khi clone đạt mới backup và áp dev 18069.

Đây là technical acceptance. Không phải audit độc lập, business acceptance hay pilot.

Actor dùng dữ liệu tổng hợp có sẵn (`.local/kd-native001/dataset/dev/credentials.json`, không in mật khẩu):

- `editor`: lập hồ sơ.
- `reviewer`: rà soát, có quyền tài chính theo dataset.
- `planner`: kế hoạch.
- `metadata`: chỉ metadata, không tiền.
- Admin chỉ dùng cho kiểm tra kỹ thuật trên clone.

## A. Arch và backend (Odoo tests, `tp_kd_workspace` + `tp_contract`)

| ID | Kiểm | Kỳ vọng |
| --- | --- | --- |
| A1 | Bảo toàn arch | Mỗi view KH-KD đã sửa giữ nguyên tập field/button và mọi thuộc tính hành vi (`invisible`, `readonly`, `required`, `domain`, `context`, `groups`, `options`, `widget` trừ `state` task chuyển sang badge readonly, `force_save`, `column_invisible`). So bằng script với bản baseline lưu ở `.local/kd-ui003/baseline_views`. |
| A2 | List chính | Có `class="tp_kd_table"` và `limit="20"`. `js_class` KH-KD giữ (`tp_kd_list`) hoặc kế thừa (`tp_kd_table`, `tp_kd_project_list`). |
| A3 | Không cột tiền | List KH-KD và list TP Contracts không chứa field tiền (`amount_ids`, `value`, `source_value`, các RAW_MONEY_FIELDS của test contract). |
| A4 | Optional | Cột phụ theo ma trận có `optional="hide"`; cột chính không optional. Không cột required editable nào bị ẩn. |
| A5 | `open_records` | Project/task/opportunity trả `views` KH-KD và context có `tp_kd_leaf` đúng XMLID lá. Domain và context cũ không đổi. |
| A6 | `_kd_form` / nguồn / `action_project` / `action_kd_create` | Trả `tp_kd_leaf` đúng lá; `res_model`, `res_id`, `views` như cũ. |
| A7 | `action_projects` | `view_id` = `kd_project_list`; domain `tp_managed` và `default_tp_managed` giữ. |
| A8 | Regression | Toàn bộ test `tp_kd_workspace` và `tp_contract` hiện có xanh, gồm `test_contract_native_ui` (create/edit/delete=0, không field tiền). |
| A9 | Ruff | Python đã đổi sạch Ruff. |

## B. Trình duyệt (Playwright, `scripts/kd_ui003_ui.cjs`, clone)

| ID | Kiểm | Kỳ vọng |
| --- | --- | --- |
| B1 | Đường kẻ | Mọi list trong inventory có `td` kẻ phải/dưới 1px `rgb(217, 226, 236)`, header nền `rgb(238, 243, 248)`, bảng có viền ngoài và bo góc. Checkbox, filler và "Thêm dòng" không bị kẻ dọc. |
| B2 | Không cắt chữ | Nhãn header không có ellipsis (`scrollWidth <= clientWidth` hoặc wrap). Ô `tp_kd_wrap` không bị cắt. Badge trạng thái đọc đủ ở 1280/1440/1920. |
| B3 | Bề rộng | WBS ở 1440 không nhỏ hơn min của arch đã tinh chỉnh khi làm mẫu: Tiêu đề ≥240, Dự án ≥220, Chịu trách nhiệm ≥190, Thời hạn ≥130, Trạng thái ≥130px (Odoo cộng thêm khoảng 24px padding/icon). Con số ban đầu 280/240/160/150/140 làm cột Trạng thái tràn khỏi vùng 1142px khi sidebar mở, nên Tiêu đề/Dự án được hạ; Chịu trách nhiệm nâng lên 190 để tên người không bị Odoo co đều xuống hai dòng ở mọi dòng (mật độ Gọn mất tác dụng). Thiếu chỗ thì `.o_list_renderer` cuộn ngang, `document.scrollingElement` không cuộn ngang. |
| B4 | Sticky header | Cuộn dọc vùng list, header vẫn ở đỉnh vùng cuộn; không che dòng đầu khi về đầu. |
| B5 | Chọn cột / khôi phục | Bật cột tùy chọn (vd. Đầu ra bàn giao), reload thì vẫn hiện. "Khôi phục cột" trả về mặc định. Key CRM/Project ngoài KH-KD không đổi. |
| B6 | Mật độ | "Gọn" làm dòng 36–40px; "Thoáng" 44–52px. Đồng bộ với ⚙ sidebar, lưu sau reload. |
| B7 | Pager server | Nguồn hơn 20 dòng (vd. WBS hoặc hồ sơ): pager hiện `1-20 / N`, N = `search_count` cùng domain. Trang 2 khác trang 1. Sort theo header đổi thứ tự từ server. |
| B8 | Filter / group | Filter và group by native còn chạy; nhóm có header nhóm kẻ đúng, không vỡ. Chọn dòng bằng checkbox không mở form. |
| B9 | Mở / lưu / quay lại | Bấm dòng mở đúng form. Sửa → Bỏ → giữ giá trị cũ. Breadcrumb quay lại đúng list, trang và bộ lọc. Form chưa lưu khi bấm lá khác vẫn theo guard native. |
| B10 | Sidebar active | Mở Cơ hội từ Tổng quan → lá Cơ hội được tô. Mở hồ sơ dự án từ bảng dự án → Hồ sơ dự án. Breadcrumb về Tổng quan → Tổng quan. Refresh form giữ lá. Menu Hợp đồng → lá Hợp đồng. |
| B11 | Form | WBS, Cơ hội, Dự án, 7 dossier: có hai khối tiêu đề, khối nghiệp vụ và notebook đúng ma trận. Field rỗng ở read mode hiện "—", không ghi DB. Không có nút Lưu thứ hai. |
| B12 | TP Contracts chuỗi ghi (clone) | Tạo nháp → sửa → trình → trả lại có lý do → mở sửa → sửa → trình lại. Stale version báo xung đột. Thứ tự và kết quả như test hiện hành. Wizard có class `tp_kd_form` khi mở trong KH-KD. |
| B13 | Dossier chuỗi ghi (clone) | Một loại hồ sơ: gửi rà soát → trả lại có lý do → mở bản sửa qua wizard `tp.kd.transition`. Version tăng như baseline. |
| B14 | Quyền âm | `metadata`: tab "Giá trị minh họa" không render trong DOM; list không có cột tiền; RPC `amount_ids` theo quyền như baseline. `editor` không thấy nút Trả lại. Actor chỉ đọc không có nút Mới khi `get_kd_ui_permissions.create` = false. Năng lực private không đọc được khi không có quyền. |
| B15 | Khác project/company | Actor không có assignment không thấy dòng dự án khác trong list và tổng pager. |
| B16 | Responsive | 360/390/768/1280/1440/1920, zoom 125%/150%, sidebar thu gọn và drawer: không cuộn ngang trang; bảng cuộn trong vùng; form một cột dưới 768px. |
| B17 | Bàn phím / touch / motion | Tab tới header, dòng và nút. Enter mở dòng. Touch emulation bấm dòng mở form. Reduced-motion không có transition. |
| B18 | Không rò style | Home, CRM, Project, Finance native ngoài KH-KD: không có `o_tp_kd_shell`; `td` list không có kẻ dọc KH-KD; form không có separator KH-KD. Wizard TP Contracts mở từ app TP Contracts không có style KH-KD. |
| B19 | Tổng quan | Bảng dự án và bảng nguồn có kẻ; sort, chọn cột, phân trang và Thao tác ▾ vẫn chạy. G01–G05 clickthrough mở list KH-KD có style. |
| B20 | Console | Không lỗi console/asset mới trên mọi màn đã mở. |

## C. Ảnh trước/sau (phải xem, không chỉ tạo)

WBS list/detail; Cơ hội list/detail; Hợp đồng list/form và wizard; một bảng tiền theo quyền (Giá trị minh họa của reviewer) cùng trường hợp metadata; Tổng quan; mobile 390 (list và form).

## D. Áp dev 18069

1. Snapshot DB, filestore, config private và source module kèm checksum, rồi verify.
2. Clone-test xanh, hash source đã test bằng source áp.
3. Dừng đúng process Odoo dev theo `.local/odoo.pid`; không dùng `scripts/dev.py stop`.
4. Upgrade chỉ `tp_kd_workspace`.
5. Rowset hash bảng nghiệp vụ, user, grant và state trước/sau phải bằng nhau.
6. Dev chỉ smoke đọc/điều hướng: mở từng lá, mở một form, đổi mật độ. Không chuỗi ghi.
7. Rollback: `scripts/kd_ui003.py rollback` khôi phục source module từ snapshot rồi upgrade; không restore DB trừ khi rowset lệch.

## Evidence

Ghi ngày 07/11/2026. Ảnh và log ở `.local/kd-ui003/` (local, không đưa vào Git).

### A. Arch và backend (clone 18389)

| ID | Kết quả |
| --- | --- |
| A1 | `kd_ui003.py archdiff`: `ok true`, 0 view đổi field/button hoặc thuộc tính hành vi. Cột thêm là field có sẵn của model (opportunity 2, allocation 5, production 4, acceptance 3, payment 3, credential 3, obligation 1), không field tiền. View mới: `kd_project_list` và 18 inherit chỉ thêm class trong `views/contracts.xml`. |
| A2–A8 | Odoo `-u tp_kd_workspace,tp_contract --test-tags /tp_kd_workspace,/tp_contract`: 114/114, 0 failed, 0 error (`tp_kd_workspace` 41, `tp_contract` 73), log `odoo-tests/20261107T005430989054Z.log`. Gồm `test_ui_layout` (A2–A7) và `test_contract_native_ui`. |
| A9 | `ruff check scripts/kd_ui003.py custom_addons/tp_kd_workspace`: sạch. |

### B. Trình duyệt (clone, `KD_STAGE=all`)

Chạy cuối: **328 check đạt, 0 lỗi console, `failures []`**. Ảnh `shots/clone-after/` (69 ảnh), evidence `shots/clone-after/evidence-final.json`, danh sách check `shots/clone-after/result.json`. Ảnh trước ở `shots/clone-before/` (31 ảnh; `failure.txt` là lần chạy trước bị crash trang lúc 23:07, lần chạy lại 23:15 đạt).

| ID | Số check | Ghi chú |
| --- | --- | --- |
| B1 kẻ ô | 66 | 12 list chính + bảng con: `td` kẻ phải/dưới `1px rgb(217, 226, 236)`, header `rgb(238, 243, 248)`, khung bo 8px. |
| B2 không cắt chữ | 53 | Header không ellipsis; ô `tp_kd_wrap` đọc đủ; badge ở 1280/1440/1920. |
| B3 bề rộng | 12 | WBS ở 1440 đạt min 240/220/190/130/130; 11 check "B3/B16" đo cuộn ngang trong khung ở từng bề rộng. |
| B4 sticky | 12 | Đo `thead` sticky ở ≥768px. |
| B5–B9 | 35 | Chọn cột lưu qua reload và khôi phục; Gọn ~38px/Thoáng ~48px; pager `1-20 / N` = `search_count`; filter/group; trang 2 → form → breadcrumb về trang 2; sửa → Bỏ giữ giá trị. |
| B10 sidebar | 28 | Lá đúng khi mở từ Tổng quan, bảng dự án, smart button, refresh, breadcrumb. |
| B11 form | 59 | Khối tiêu đề, separator, notebook theo ma trận; ô trống chỉ đọc hiện một dấu "—" (có kiểm không lặp "——"); một nút Lưu. |
| B12 TP Contracts | 4 | Tạo nháp → sửa → trình → trả lại (lý do) → mở sửa → sửa → trình lại; nhập giá trị dòng đã xác nhận trên clone vì backend đòi `amounts_not_confirmed`. Bản cũ lưu đè báo xung đột. Kết quả: hợp đồng 529, revision 571, lần trình `[1 returned, 2 pending]`. Wizard có `tp_kd_form`. |
| B13 dossier | 3 | KD26-TT-20: gửi rà soát → trả lại → mở bản sửa; version 5 → 6 → 7 → 8. |
| B14/B15 quyền | 7 | Pager = `search_count` 21 cho editor/reviewer/planner/metadata; metadata không có tab Giá trị minh họa, `amount_ids` không nằm trong DOM. |
| B16 responsive | 31 | 360/390/768/1280/1440/1920 và zoom 125/150%: `docOverflow` 0; bảng cuộn trong khung khi hẹp; form một cột <768px. |
| B17 | 3 | Tab/Enter mở dòng, touch mở form, reduced-motion 0s. |
| B18 không rò | 6 | Home/Project/CRM/TP Contracts app: không `o_tp_kd_shell`, `td` 0px; wizard trong app TP Contracts giữ separator gốc. |
| B19 Tổng quan | 7 | 1440 và 390: khung `1px rgb(217, 226, 236) 8px`, `td` kẻ, header `rgb(238, 243, 248)`, sort/cột/pager/Thao tác ▾ chạy, `docOverflow` 0. |
| B20 | 2 | 0 lỗi console/asset (gồm check tổng kết). |

Số check theo tab: Cơ hội 24, Dự án 19, WBS 36, Hợp đồng 23, Giao khoán 21, Sản lượng 21, Nghiệm thu 21, Đề nghị thanh toán 44, Kế hoạch định kỳ 21, Năng lực 21, Nghĩa vụ 21, Tổng quan 6; còn lại là check chung (sidebar, responsive, rò style).

Sửa sau khi kiểm: (1) "——" ở ô Char trống chỉ đọc (vd. "Số văn bản" trên revision hợp đồng) do cả widget `o_field_empty` và `span` rỗng cùng vẽ dấu; selector đã tách. (2) Script: hộp thoại xác nhận chờ mọi `.modal` đóng; chọn SelectMenu Odoo 20 thay `<select>`; mở drawer "Menu KH-KD" trước khi bấm lá ở 390px; B18 đo đường kẻ KH-KD thay chữ hoa (separator native vốn đã uppercase).

Stage `contract` mất 1683 giây ở lần chạy cuối: server log không có request nào từ 01:01:00 đến 01:27:48 UTC rồi hai websocket cùng đóng, tức máy tạm dừng/ngủ, không phải độ trễ ứng dụng.

### D. Áp dev 18069 (07/11/2026, UTC)

| Bước | Kết quả |
| --- | --- |
| Baseline | Đếm chỉ đọc trước áp lưu `.local/kd-ui003/dev-baseline-pre-apply.json`: hợp đồng 14, revision 15, giao khoán 18, sản lượng 25, nghiệm thu 17, đề nghị thanh toán 21, kế hoạch 18, năng lực 13, nghĩa vụ 9, cơ hội 24, dự án 15, task 163, KD grant 320, user 20; registry dataset `KD_NATIVE_001_REALISTIC_V1` 1450 owned + 3 tham chiếu, `KD_NATIVE_001_UI_PROBES_V1` 362, tất cả `present`. |
| 1. Backup | `kd_ui003.py backup` lúc 01:36:32 khi dev đang chạy: `pg_dump -Fc` trên snapshot REPEATABLE READ đã export, 269 attachment (sha1), config private, `maintained-source.zip`. 112 tệp re-hash khớp `manifest.json`, `pg_restore --list` đọc được; dev PID 26508 không đổi trong lúc backup. Thư mục `backup-pre-apply-20261107T013632Z`. Snapshot prepare cũ (`snapshot-20261106T155541Z`) giữ cho rollback. |
| 2. Hash source | `apply` chép đúng `tp_kd_workspace` đã test sang `custom_addons/`, so tree hash bằng nhau. Các module khác giống hệt source clone. |
| 3–4. Upgrade | Dừng đúng Odoo theo `.local/odoo.pid` (không `dev.py stop`), `-u tp_kd_workspace --stop-after-init`: rc 0, 0 dòng ERROR/CRITICAL (1 WARNING `markdown2` có sẵn của mail). Log `dev-apply-20261107T013653Z.log`. Module 20.0.1.1.0 → 20.0.1.2.0. |
| 5. Rowset | 30 bảng nghiệp vụ, user (gồm password hash), group, grant, state: 1118 dòng trước = sau, `changed_tables {}` (`tp_contract_event` trong danh sách không có bảng). |
| Runtime | Dev PID 20232, `/web/login` HTTP 200. Clone 18169 (PID 27568), 18269 (PID 2232), PostgreSQL 55432 (PID 4228) giữ nguyên PID. |
| 6. Verify | `node scripts/kd_ui003_ui.cjs dev verify`, chỉ đọc (`write = target === 'clone'`: bỏ chuỗi hợp đồng/dossier, bỏ sửa → Bỏ, không mở wizard): **320/320, 0 lỗi console, `failures []`**. Số theo tab giống clone (Cơ hội 24, Dự án 19, WBS 36, Hợp đồng 23, 7 hồ sơ 21–44, Tổng quan 6). Responsive `docOverflow` 0 ở mọi bề rộng/zoom; rò style: Home/Project/CRM/app TP Contracts không có shell và đường kẻ KH-KD; Tổng quan 1440/390 đạt. Ảnh `shots/dev-verify/` (59 ảnh), evidence `shots/dev-verify/evidence-dev-verify.json`. |
| Sau verify | Đếm lại: mọi số và registry bằng baseline; `write_date` mới nhất trên các bảng nghiệp vụ là 06/11/2026 08:10 UTC, trước lúc áp. |
| 7. Rollback | Chưa cần. Nếu cần: `scripts/kd_ui003.py rollback` (source module từ snapshot + upgrade); restore DB từ backup chỉ khi rowset lệch. |

### E. Sửa lăn chuột Tổng quan — CHG-20261107-001 (07/11/2026, UTC)

Phản hồi người dùng trên dev 18069: ở Tổng quan không lăn chuột được. Probe chỉ đọc ở 1280/1440/1600/1920 tái hiện: `.o_tp_kd_ov` cao bằng khung (vd. 814px) nhưng nội dung 3686px, `overflow-y` tính ra `hidden`, `mouse.wheel` không đổi `scrollTop`. Nguyên nhân: gốc Tổng quan cũng là `.o_action`; rule gốc Odoo `html .o_web_client > .o_action_manager > .o_action { overflow: hidden }` (desktop ≥992px, ẩn scrollbar) mạnh hơn `overflow: auto` của `.o_tp_kd_ov`. Lỗi có từ KD-UI-002; <992px không bị.

| Bước | Kết quả |
| --- | --- |
| Sửa | `overview.scss`: `.o_web_client > .o_action_manager > .o_tp_kd_ov.o_action { overflow: auto; overscroll-behavior-y: contain; scrollbar-width: thin }`, chỉ phần tử Tổng quan; action/view khác giữ layout Odoo. Module 20.0.1.2.0 → 20.0.1.2.1. |
| Test mới | B19 thêm 1600×900 (gần màn hình người dùng) và check "mouse wheel scrolls" ở 1440/1600/390: `overflowY auto`, `scrollTop` 600 sau một lần lăn 600px. |
| Clone 18389 | Odoo `tp_kd_workspace` 41 + `tp_contract` 73 = 114/114 (log `20261107T015956354423Z`), `archdiff` ok. Browser stage tables/behaviour/sidebar/roles/responsive/leak/overview: **326/326**, 0 lỗi console (`ui-after-chg20261107-001.log`). Bỏ stage `contract`/`dossier` (chuỗi ghi, không chạm Tổng quan); kết quả đủ 328 của CHG-20261106-022 lưu ở `shots/clone-after-chg022/`. |
| Backup | `backup-pre-apply-20261107T021338Z`: 112 tệp re-hash khớp, 269 attachment, `pg_restore --list` đọc được; dev PID 20232 không đổi trong lúc backup. |
| Áp dev 18069 | `dev-apply-20261107T021354Z.log` rc 0, 0 dòng ERROR/CRITICAL, `changed_tables {}`; source `custom_addons/tp_kd_workspace` = source clone; module `installed` 20.0.1.2.1. Dev PID mới 23320, `/web/login` 200. Clone 18169 (27568), 18269 (2232), PostgreSQL 55432 (4228) giữ PID. |
| Verify dev | `kd_ui003_ui.cjs dev verify` chỉ đọc: **324/324**, 0 lỗi console, `failures []`; lăn chuột 1440/1600/390 đều `scrollTop` 600. Ảnh `shots/dev-verify/overview-1600.png`, `overview-1600-after-wheel.png` (lăn 4 lần → `scrollTop` 2000, thấy bảng dự án và Việc của tôi). Evidence CHG-20261106-022 lưu ở `shots/dev-verify-chg022/`. |
| Sau verify | Đếm chỉ đọc: số bản ghi 15 bảng và registry dataset bằng `dev-baseline-pre-apply.json`; `write_date` nghiệp vụ mới nhất vẫn 06/11/2026 08:10 UTC. |
