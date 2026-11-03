# TANPHAT ONE — Nhật ký thay đổi

Mỗi lượt thay đổi code hoặc quyết định kiến trúc ghi một mục ngắn. Không ghi credential, dữ liệu thật hoặc log chứa bí mật.

## CHG-20261102-014 — Thực thi dữ liệu mẫu liên thông NATIVE-DATA-003

- Ngày:02/11/2026 (Asia/Saigon). Người dùng chuyển vai trò trực tiếp “Chuyển vai trò: thực thi trong phiên này” (DEC-027); checkpoint start riêng từ baseline CHG-013, giữ195 file maintained cũ và mọi thay đổi có sẵn. Không stage/commit/push/production.
- Snapshot private127 checksum; restore clone owned `tp_tanphat_data003_20261102` đạt538 rowset/244 attachment reference exact trước neutralize. Dev18069 giữ188 binding/ID và các tổng gốc; bật8 actor giả, tái dùng employee Bảo22/thêm user29, hierarchy/approver,5 assignment,20 attendee và10 nhóm member. Không đổi admin/planner password/group/assignment.
- B3 application: addon `tp_crm_project_bridge` có FK4 lead→project đúng customer/company/native CRM giao project scope; `tp_timesheet_scope` chặn native own-timesheet ngoài managed project (global rule + explicit create/write/default target checks, constraint Odoo20 chạy sudo); `tp_dashboard_privacy` chặn public share/token của đúng2 bảng nội bộ. Không sửa core/React/OpenAPI/managed-task policy; module/schema install tách khỏi data transaction.
-6 action expense native bằng actor thật:2 draft810.000/2 submitted3.100.000/2 approved3.250.000, tổng7.160.000;2 receipt13/14 vẫn draft, invoice4 vẫn draft801 triệu, không posting/payment. Dashboard nguồn sống theo actor/domain, không ép admin có expense. Native security/expense tạo10 mail `exception`,0 sent/outgoing mới/notification mới; tool cô lập SMTP loopback chỉ trong process. Ghi đầy đủ onboarding To-do115/7 stage, General/digest auto membership,8 OdooBot chat/8 welcome message, chatter/activity và recompute manager của18 dòng giờ.
- Test: Odoo integration27 không fail/error;9 unit guards/Ruff; clone ORM74/dev71,8/8 HTTP actor mỗi môi trường; clone UI58/dev UI/RPC63 ở1440/375 và CSS content zoom125/150%,0 console error/overflow trong ma trận. Ảnh thực đã xem; clone dashboard refresh84→84,5→84; failure-injection bootstrap/native submit rollback538 rowset exact. Reapply dev0 create/update/action và verify0 drift; sửa cumulative journal giữ before đầu/after cuối, không đổi password. Dry-run linkage serialization do chồng bước phụ thuộc đã rollback/chạy tuần tự; thêm3-attempt fresh-transaction retry.
- Preservation audit:486/538 bảng không đổi,52 delta phân loại/allowlist, không xóa row/relation cũ;195 source cũ nguyên,244 blob cũ nguyên/249 ref hiện đạt; dashboard attachment405 đổi riêng. Shared config/credential/cluster roles/database catalog/owner nguyên; không fingerprint nội dung DB khác. Clone18149 dừng, dev/PG chạy,18109/18119 đóng. [Runbook](demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md), [RFC TASK-001](architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md); status/roadmap/decision/workflow/source-map cùng cập nhật.
- Kết quả `PARTIAL_WITH_GAPS`, chờ audit độc lập: managed-task progress của Long vẫn AccessError, không assignee-all-write bypass. Native refuse/reset/correction chỉ clone; chưa business acceptance/pilot, chưa mở TP workflow/BASE/FIN-001. Next: audit phần áp dụng và quyết định policy TASK-001; workflow finish/check chỉ xác nhận handoff theo bằng chứng, không thay nghiệm thu nghiệp vụ.
- Kiểm cuối: dev.py smoke đạt admin/planner session/API/project/contract/financial scope;14 tài liệu/168 link tương đối và fence/CHG marker đạt, Node syntax/Ruff/unit9 và git diff --check đạt. Runtime dev18069/PG55432 mở; clone18149/demo18109/18119 đóng. Giữ staging rỗng, upstream sạch và checkpoint đúng task để finish/check.

## CHG-20261102-013 — Prompt chuẩn hóa bộ dữ liệu mẫu liên thông NATIVE-DATA-003

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu viết prompt để dữ liệu đã thêm liên kết như một tình huống vận hành; phiên chính giữ vai trò điều phối, chỉ soạn tài liệu, không thực thi migrator/đổi DB/quyền/password. Không commit/push.
- Thêm [prompt Claude](prompts/CLAUDE_NATIVE_DATA003_CONNECTED_OPERATIONS.md) có inventory188 binding, backup/clone/restore rehearsal,3 kịch bản, mapping actor/user/employee/project/customer/analytic, bật login có kiểm soát cho actor giả khi được giao, bridge CRM→Project tối thiểu, action chi phí native, dashboard nguồn sống, ma trận quyền/UI/RPC/idempotency/rollback và bàn giao từng batch.
- Phát hiện/kiểm đọc: admin không có employee nên header Expense trả 0; 6 expense draft/tổng 7.160.000 VND thuộc nhân viên khác. Source xác nhận dashboard có employee hierarchy/domain; approve có thể tạo chứng từ; scope managed task hiện chỉ cho user thường đọc. Prompt không cho sudo/manager grant đại trà, ép state, chuyển project unmanaged hoặc gán lại hợp đồng cũ để che gap. Native posting/payment chỉ clone; dev invoice giữ draft, policy managed-task và nghiệp vụ chưa mở trả RFC riêng.
- Baseline: workflow check CHG-012 đạt, không checkpoint khác; start checkpoint tài liệu riêng. Runtime đọc xác nhận dev 18069/PostgreSQL 55432 chạy, 18109/18119 trống; 188 binding và các module native/Home/VI hiện có. Không chạy app suite/build vì không sửa code/runtime.
- Cập nhật PROJECT_STATUS/ROADMAP/DECISIONS (DEC-026: yêu cầu prompt, chưa triển khai). Kiểm link/nội dung, prompt guards, maintained source/runtime baseline, git diff --check và workflow finish/check theo kết quả thực trong handoff.
- Next action: người dùng giao prompt cho phiên Claude triển khai; chưa tuyên bố dữ liệu liên thông/end-to-end hoàn tất, không đóng audit hoặc cổng business/pilot.

## CHG-20261102-012 — Ngừng và lưu trữ môi trường UI-DEMO-001/002 cũ

- Ngày: 02/11/2026 (Asia/Saigon). Task vận hành theo yêu cầu trực tiếp; không commit/push. Checkpoint trước lượt không tồn tại, `check` khớp CHG-011; `start` tạo checkpoint riêng, không finish task khác. Giữ mọi thay đổi chưa commit, không sửa application code.
- Xác minh owner.json/workspace/config/PID/DB token demo; DB test không có token nhưng đăng ký owner, log khởi tạo/test, thời điểm DB và attachment/filestore khớp. Dừng đúng PID 22840/22852 và console con; 18119 đã dừng sẵn. Drop đúng `tp_tanphat_demo_ui001`, `tp_tanphat_demo_ui001_test`; không cần ngắt kết nối nào. Lần gọi DROP đầu bị PostgreSQL từ chối vì transaction context (chưa drop DB nào); thực hiện lại bằng kết nối autocommit độc lập thành công.
- Archive local ACL riêng: `C:\TANPHAT ONE\.local\demo-retirement\20261102-ui001\`; hai dump, runtime ZIP, source TP/tooling, config/metadata/credential riêng ngoài Git. Manifest 18 file SHA-256, hai `pg_restore --list` và đọc toàn dump ra SQL không thực thi, ZIP CRC/source checksum và toàn bộ attachment SHA-1/kích thước đạt. Listing/đọc dump **không phải diễn tập restore**. Runbook đã ghi cách phục hồi, không dùng prepare/seed để tái tạo snapshot.
- Policy công cụ từ chối recursive delete. Thay bằng chuyển nguyên `data`, `logs`, config/owner/credential vào `retired-originals` trong archive (PowerShell LiteralPath, kiểm đường dẫn tuyệt đối/reparse, byte/checksum nguyên). Runtime path cũ chỉ còn screenshots; không giải phóng dung lượng của các bản gốc lưu trữ. Giữ bằng chứng UI-DEMO-001/002 và source addon; không xóa backup cũ.
- Dev 18069/PID14812 và PostgreSQL55432/PID19028 giữ nguyên. Hai DB demo vắng; OID/owner/cấu hình các DB còn lại, roles, dev credential/config, source/Git metadata và 239 blob dev đều khớp. 188 binding fixture/toàn bộ ID nghiệp vụ nguyên, không mất/trùng dữ liệu; 534/538 bảng raw bằng hash. Bốn bảng telemetry thay đổi do smoke: res_users_log +7, res_device_log +7, bus_bus +68, mail_presence timestamp (2 dòng); không sửa lại telemetry.
- Kiểm mới: HTTP login/count/ngôn ngữ admin/planner trước/sau bằng nhau; UI admin 14/14 màn hình desktop (0 console error/overflow, nhãn VI mong đợi); Home 26/26 admin/planner × 1440/375. Đã xem ảnh Home/dashboard. Không chạy Odoo suite/build vì không đổi code/schema dev. `git diff --check`, kiểm link/nội dung và `ai_workflow finish/check` ghi tại handoff.
- Tài liệu: PROJECT_STATUS, ROADMAP, runbook demo. Demo runtime `RUNTIME_RETIRED_ARCHIVED`; các kết quả lịch sử vẫn giữ nguyên, không biến pending audit thành nghiệm thu. Next action: audit các batch Home/To-do/NATIVE-DATA-002/VI-001 trên dev hiện tại theo scope riêng; không tự khôi phục demo cũ.

## CHG-20261102-011 — Giữ nguyên nhãn React contracts (G10)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: chỉ tài liệu. Người dùng chọn “Leave React as is”, nên nhãn React contracts không đổi.
- Đã ghi vào DEC-025, glossary (G10) và status. Không sửa code, không chạy lại test.

## CHG-20261102-010 — Một bộ nhãn tiếng Việt cho `tp_contract` (VI-002)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bản dịch và chuỗi hiển thị của `tp_demo_workspace`. Người dùng chọn catalog mới (DEC-025).
- Đã sửa:
  - `tp_demo_workspace/i18n/vi.po`: 22 lần xuất hiện theo XML ID. Cả 41 lần nay khớp `tp_contract/i18n/vi.po`.
  - 4 bộ lọc cứng trong `contract_views.xml`.
  - `TAX_BASIS_LABELS`.
  - Một dòng trong `docs/demo/UI_DEMO_001_PRESENTATION.md`.
  - Glossary: G9 đã xử lý trong source, thêm G10 cho nhãn React contracts.
- Không đổi state key, XML ID, domain, dữ liệu, React hay quyền.
- Test trên DB tạm `tp_tanphat_demo_vi002_test`, đã drop sau khi chạy:
  - Cài với vi_VN, chạy `/tp_demo_workspace,/tp_contract`: 0 failed, 0 error trên 74 test.
  - 41/41 nhãn vi_VN khớp catalog. Không view demo nào còn chữ lọc cũ. Ruff đạt.
- Không chạm demo18109, dev hay `tp_tanphat_data002_test`. Không commit/push.

## CHG-20261102-009 — Việt hóa giao diện Odoo native và addon TP (VI-001)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bản dịch, dữ liệu ngôn ngữ dev và tài liệu. Batch B của prompt CHG-090.
- Thêm:
  - Addon mới `custom_addons/tp_i18n_vi/`: chỉ có `i18n/vi.po` với 37 mục overlay, README và 4 test (catalog khớp nguồn en_US, overlay thắng khi overwrite, nạp sau module gốc, không sở hữu `ir.model.data`).
  - `i18n/vi.po` cho `tp_core` (17), `tp_organization` (2), `tp_project` (42) và `tp_contract` (193, chỉ nhãn).
  - Tài liệu [docs/i18n/VI_GLOSSARY_AND_COVERAGE.md](i18n/VI_GLOSSARY_AND_COVERAGE.md).
- Không sửa `odoo/` hay `addons/`, React, API, quyền.
- Test trên DB cô lập `tp_tanphat_data002_test`:
  - `--test-tags /tp_i18n_vi` cho 0 lỗi trên 4 test; `/tp_project,/tp_i18n_vi` cho 0 lỗi trên 16 test.
  - Ruff đạt. 5 catalog có 0 mục chưa dịch, 0 fuzzy.
  - Probe 313 menu: 7 menu cố ý giữ nguyên.
  - Revert về en_US rồi apply lại đạt. Số liệu dashboard giống nhau giữa en_US và vi_VN.
- Dev `tp_tanphat_dev`:
  - Snapshot `.local/vi001/snapshot-dev-20261102-121509` (247 checksum, verify đạt).
  - loadlang vi_VN, `-i tp_i18n_vi`, `-u tp_i18n_vi --i18n-overwrite`, import 4 catalog TP, `vi_apply` dry-run/apply/verify: tất cả exit 0.
  - Chỉ admin chuyển sang vi_VN.
  - UI admin 24 màn hình × (1440, 375, zoom 125%, zoom 150%) và dialog xuất/xoá (chưa xác nhận) đạt. planner.dev en_US đạt.
  - Fingerprint group/ACL/rule/bảng nghiệp vụ không đổi.
- Còn gap G1–G9 (G9: nhãn `tp_contract` dịch khác giữa `tp_demo_workspace` và catalog mới). Giao diện đủ cho trình diễn, chưa phải nghiệm thu. Không commit/push.

## CHG-20261102-008 — Bổ sung lịch, nhóm trao đổi, bảng tổng hợp mẫu (NATIVE-DATA-002)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: dữ liệu mẫu dev + tài liệu. Batch A của prompt CHG-090: 8 lịch riêng tư admin, 3 nhóm Discuss riêng/12 tin, 2 dashboard native chỉ admin (công thức PIVOT theo quyền người xem), 6 mục Danh mục công việc; tổng 31 bản ghi, namespace `tp_native_data002_20261102`. Git: template + generator `docs/demo/dashboards/`, bảng phủ 14 menu/runbook trong `docs/demo/ODOO_NATIVE_SAMPLE_DATA.md`. Seeder ngoài Git `.local/data002/`.
- Test: DB cô lập `tp_tanphat_data002_test`: dry-run 31 (0 dòng cũ đổi trên 22 bảng), fail-test rollback (0 binding/0 event), apply 31 → verify 0, cập nhật template updated=2 → verify 0; HTTP/UI admin và planner.dev 1440/375 đạt; Ruff `build_templates.py` đạt.
- Dev `tp_tanphat_dev`: snapshot `.local/data002/snapshot-batchA-20261102T044155Z` (241 checksum), apply 31 → verify created=0/updated=0; planner.dev: lịch “Busy”, nhóm/tin/dashboard/hóa đơn AccessError hoặc rỗng. Dữ liệu đủ cho trình diễn, chưa phải nghiệm thu nghiệp vụ. Không commit/push.

## CHG-20261102-007 — Sửa quyền To-do native và nạp 14 việc cá nhân mẫu (TODO-001)

- Ngày: 02/11/2026 (Asia/Saigon). Phạm vi: bảo mật `tp_project` + dữ liệu mẫu dev. `custom_addons/tp_project/security/ir.access.csv`: `task_platform_scope` và `task_platform_write_scope` (nhánh user không là TP manager) thêm `('project_id', '=', False)`; giữ global rule, company scope, assignment/grant và rule native.
- Test: 6 regression `TestPrivateTodoAccess` trong `tp_project/tests/test_project_access.py`; DB cô lập `tp_tanphat_data002_test`: rule cũ `0 failed, 3 error(s) of 6`, rule mới `--test-tags /tp_project` `0 failed, 0 error(s) of 12`; `-u project_todo,tp_project` tích hợp 23/25 (2 test at_install native lỗi thứ tự nạp `tp_project`, không do thay đổi này); Ruff đạt.
- Dev `tp_tanphat_dev`: snapshot `.local/data002/snapshot-20261102T041428Z` (241 checksum), `-u tp_project` exit 0; `seed_todo.py` dry-run → apply 14 → verify created=0; live admin Open 13 (12 + onboarding native có sẵn), planner.dev AccessError khi gọi trực tiếp. Không commit/push.

## CHG-20261102-006 — Trang chủ native TANPHAT ONE dạng lưới ứng dụng (UI-HOME-001)

- Ngày: 02/11/2026 (Asia/Saigon). Triển khai prompt CHG-005: addon mới `custom_addons/tp_web_home/` (depends `web`; client action `tp_web_home.home`/path `tp-home`, root menu “Trang chủ” `base.group_user` sequence 1, systray nút Trang chủ, lưới ô/tìm có-không dấu/alias, nhóm “Công việc & nghiệp vụ”/“Công cụ hệ thống”, SCSS scoped `o_tp_web_home`). Ô từ menu service native theo quyền, chờ `load_menus` mới trước lần render đầu; không model/ACL/controller, không ghi `res.users.action_id`, không patch WebClient/router, không sửa `odoo/`, `addons/`, React, OpenAPI, auth hoặc `tp_demo_workspace`.
- Test cô lập DB `tp_tanphat_home001_test`/18129, user và công ty giả, secret `.local/home001/` ngoài Git: Odoo `--test-tags /tp_web_home` 0 failed/0 error of 10; HOOT 15/15; Playwright 66/66 (quyền, route, back/forward/reload, deep link, Ctrl-click, tìm, Escape/Enter/Tab, guard form chưa hợp lệ, đổi công ty, logout/login không lộ menu cũ, Home Action riêng, 1440/1366/1024/768/375, zoom 125/150%, reduced motion, không lỗi console); gỡ cài sạch (0 xmlid/action/menu, `/odoo` về Discuss, Home Action giữ) rồi cài lại; Ruff đạt. Icon mobile nâng 64→68px theo spec trong lượt kiểm.
- Dev: snapshot `.local/home001/dev-snapshot/` (dump + filestore + config/source manifest, 233 checksum, verify đạt; chưa diễn tập restore) rồi chỉ `-i tp_web_home` lên `tp_tanphat_dev`, exit 0, không dừng dev18069/demo18109. So fingerprint: chỉ bảng menu/action/module/attachment/signaling đổi, `tp_*`/user/nhóm/ACL/rule/project/partner không đổi, 0 user có Home Action = Trang chủ. Live admin/planner.dev 1440/375: 26/26. [Runbook](demo/UI_HOME_001_RUNBOOK.md).
- Trạng thái `IMPLEMENTED_PENDING_AUDIT`; chưa vào `dev.py` MODULES. Không commit/push; TODO-001, NATIVE-DATA-002/VI-001, UI-DEMO-001/002, AUTH-002/C01 và cổng nghiệp vụ/pilot giữ nguyên.

## CHG-20261102-090 — Prompt bổ sung dữ liệu toàn menu và Việt hóa (chờ tích hợp handoff)

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu prompt bổ sung phần dữ liệu còn thiếu, sau đó thêm Việt hóa toàn hệ thống trừ từ đặc thù. Tạo [prompt NATIVE-DATA-002 + VI-001](prompts/CLAUDE_NATIVE_DATA002_AND_VI001_COMPLETE_DEMO.md), hai batch triển khai riêng; chỉ chuẩn bị prompt, chưa seed/cài/chỉnh ngôn ngữ.
- Đối chiếu coverage dữ liệu read-only trước đó; đọc source notification Calendar/Discuss và quyền dashboard để đặt yêu cầu tránh gửi tới người khác/lộ cached money. Kiểm HTTP admin res.lang/res.users chỉ có en_US active, admin en_US; source base có vi_VN, upstream có catalog vi.po. Không suy việc có catalog nghĩa là UI đã dịch. Evidence .local/native-data-20261102/language-coverage-audit.json ngoài Git.
- Quy định target dữ liệu thiếu: To-do tái dùng TODO-001, 8 lịch riêng, 3 nhóm riêng/12 tin admin, 2 dashboard đọc domain fixture và hạn chế người xem. Bảo toàn 4 project/28 task/8 partner/10 lead/12 employee/20 timesheet/6 expense/4 invoice. Apps/Settings không thêm cấu hình giả. Việt hóa bề mặt app/luồng hiện có, glossary, locale/catalog chuẩn, không đổi identifiers hoặc dịch thay DOM toàn cục.
- Preflight phát hiện tp_web_home đang được tạo và checkpoint ACTIVE (03:15:28Z); checker fail code changed after handoff. Giữ checkpoint và AI_WORKFLOW_STATE của batch đó, không start/finish thay. Thêm ghi chú status, giữ Last change mốc đã finish; ID 090 dành cho prompt để giảm xung đột batch implementation đang chạy, chưa được workflow finish độc lập. Chủ batch tiếp theo tích hợp ghi chú vào bàn giao khi phù hợp.
- Kiểm local links/fence/nội dung và git diff --check cho tài liệu mới; không test ứng dụng hoặc tuyên bố maintained code unchanged vì agent khác đang sửa. Không sửa application code/runtime/DB/quyền, không commit/push; Next action audit khác giữ nguyên.

## CHG-20261102-005 — Chuẩn bị trang Home native dạng lưới ứng dụng

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng đồng ý dựng Home theo ảnh. Phiên chính giữ vai trò điều phối: tạo [prompt UI-HOME-001](prompts/CLAUDE_UI_HOME001_NATIVE_APP_LAUNCHER.md), có thiết kế icon/nền/tìm kiếm, mapping XML ID, native action/root menu/Home button, test quyền/route/unsaved form và điều kiện cài dev sau test. Chưa phải UI đã triển khai.
- Áp dụng skill frontend-design và guideline Odoo web local. Đọc source menuService/WebClient/action plugin/NavBar, kiểm Home Action native và HTTP cây menu admin/planner.dev (14/9 root apps, admin chưa đặt Home Action), lưu evidence `.local/home001-preparation/runtime-menus.json` ngoài Git. Không suy cài module từ tên trong roadmap; tách native Project/TP Projects và Invoicing/TP Finance.
- Đối chiếu HTTP 200 README/manifest/template/source OCA web_responsive20, commit 6ac74409cd559529374236476353d453d5568c5e (29/10 UTC): có fullscreen app menu nhưng phạm vi còn chạm form/list/chatter/user settings; chưa compatibility-tested. Chọn thiết kế addon Home riêng, không tải/cài cả OCA hoặc sao chép Enterprise. Link raw filename JS ban đầu trả 404; đã xác định tên apps_menu.esm.js và đọc thành công, không coi 404 là module thiếu.
- Cập nhật status/roadmap, kiểm local links/fence/mapping, git diff --check và workflow finish/check; maintained application code không đổi. Không chạy Odoo/HOOT/browser E2E vì chỉ chuẩn bị prompt; chúng là acceptance bắt buộc của Claude. Không đổi DB/runtime/quyền/code/schema, không commit/push; TODO-001 và các audit tồn đọng giữ riêng.

## CHG-20261102-004 — Phát hiện lỗi quyền To-do và chuẩn bị correction cho Claude

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu thêm dữ liệu To-do; khi phát hiện cần sửa app, người dùng chọn viết prompt cho Claude, giữ vai trò phiên chính điều phối. [Prompt TODO-001](prompts/CLAUDE_TODO001_NATIVE_PRIVATE_TASK_FIX_AND_SAMPLE.md) giao sửa domain tối thiểu, regression quyền riêng tư/company/project và nạp 14 việc giả sau test đạt.
- Snapshot dev trước thử `.local/native-data-20261102/backup-20261102T025223Z/`: dump/filestore chuẩn/manifest SHA256, pg_restore listing đạt; chỉ restart đúng dev18069, không đổi demo18109/PostgreSQL. Chưa restore rehearsal snapshot mới.
- Helper local seed_todo.py chuẩn bị 12 open và 2 done, namespace riêng và guard/transaction/idempotence. Dry-run thất bại ở bản đầu: admin read=False, write/unlink=True; env.flush_all vẫn lỗi, rollback toàn bộ. Nghi phạm task_platform_scope thiếu nhánh project_id=False; không dùng sudo hoặc mở rule để nạp qua lỗi. Registry read-only xác nhận namespace 0 binding, 28 task dự án giả còn nguyên; evidence todo-dry-run.log/todo-blocked-verification.json ngoài Git.
- Không sửa application code/core/security/schema, không lưu To-do mới, không đổi user/grant/approval/payment; không commit/push. Cập nhật status, tài liệu dữ liệu và prompt; kiểm local links, git diff --check, workflow finish/check. Không tuyên bố seed hoặc regression tests đạt. Các Next action audit UI-DEMO-001/002, AUTH-002/C01 giữ nguyên.

## CHG-20261102-003 — Hiệu chỉnh kết quả kiểm liên kết bàn giao

- Ngày: 02/11/2026 (Asia/Saigon). Kiểm link tổng ba tài liệu ở cuối CHG-002 phát hiện hai tham chiếu lịch sử cùng trỏ tới DOCX so sánh edition không còn trong deliverables. Shell đã tiếp tục finish dù bước assert link lỗi, nên reported_checks CHG-002 ghi link đạt là không chính xác. Ghi đính chính tại đây, không sửa JSON checker bằng tay hoặc tái sử dụng ID.
- Bỏ hai link chết, giữ tên file và ghi rõ tình trạng thiếu DOCX; còn PDF ở `.local/edition-comparison-report/render/`. Không tái tạo báo cáo ngoài scope. Các kiểm dữ liệu/HTTP/phân quyền CHG-002 đã chạy đạt riêng, không bị ảnh hưởng.
- Chạy lại kiểm local links ba tài liệu và git diff --check; workflow finish/check. Chỉ thay tài liệu, không đổi application code/runtime/DB, không commit/push hoặc đổi Next action audit.

## CHG-20261102-002 — Liên kết dữ liệu giả giữa TP Projects và các ứng dụng chuẩn

- Ngày: 02/11/2026 (Asia/Saigon). Theo yêu cầu làm dữ liệu khớp giữa các module, dùng nguyên bốn project ID đã nạp ở CHG-001; đánh dấu managed, mã DA-2026-001…004, phòng chủ trì, 27 assignment reader/coordinator và nhóm Platform User chỉ cho 10 user giả không password. Không cấp TP manager/grant hoặc thay user thật. [Mapping, thao tác và evidence](demo/ODOO_NATIVE_SAMPLE_DATA.md).
- Bốn cơ hội CRM dùng cùng khách hàng, tag mã dự án và tham chiếu trong mô tả; không tuyên bố có CRM → Project tự động. Task/nhân sự/timesheet/chi phí giữ ID và phân bổ tương ứng. Ba hóa đơn cũ bổ sung Origin/Reference; thêm một nháp An Hòa 185 triệu và phân bổ analytic, không posted/payment hoặc hợp đồng TP. Giữ provenance giả lập trong mô tả/namespace; không thêm project/task trùng.
- Snapshot trước sửa `.local/native-data-20261102/backup-20261102T023505Z/`: dump + canonical filestore + manifest SHA256, pg_restore listing đạt; chưa diễn tập restore snapshot mới. Dry-run ban đầu rollback vì write_date của partner user giả; xác định ownership đúng ID và kiểm business fields giữ nguyên, không nới hash bảo vệ dữ liệu khác.
- Kiểm thực chạy: helper local dry-run/apply/verify qua registry mới, verify created={}; hash ngoài fixture không đổi, không tăng project/task/grant/mail/posted. HTTP hai action Project/TP Projects cùng model/cùng bốn ID, CRM/customer/tag/reference, task/giờ làm/invoice khớp; link chuẩn mở được. API admin có bốn dự án; planner.dev giữ một dự án cũ và 404 khi truy cập bốn ID mới; ORM chặn dự án/task ngoài assignment. Admin native ACL/form và project CRUD savepoint rollback đạt. git diff --check và workflow finish/check; không chạy toàn bộ app tests do không đổi application code/schema.
- Cập nhật status và tài liệu dữ liệu; helper/evidence ngoài Git. Không sửa application code/core, module/schema, mật khẩu, grant người thật, demo18109 hoặc Next action audit UI-DEMO-001/002, AUTH-002/C01; không commit/push, BASE approval/ký/hiệu lực/thanh toán/pilot.

## CHG-20261102-001 — Thêm dữ liệu trải nghiệm trên giao diện Odoo chuẩn

- Ngày: 02/11/2026 (Asia/Saigon). Người dùng yêu cầu thêm dữ liệu vào native Odoo đang xem và bỏ dấu DEMO trên tên. Đã thêm bộ dữ liệu giả tên tự nhiên trên dev 18069; vẫn giữ provenance/nhận diện môi trường. [Danh mục, hướng dẫn và kiểm chứng](demo/ODOO_NATIVE_SAMPLE_DATA.md).
- Thêm bằng ORM, transaction nguyên tử, XML ID namespace riêng: 8 đối tác, 10 cơ hội CRM, 4 project không TP managed, 28 task, 5 phòng ban/12 nhân sự, 20 timesheet, 6 chi phí nháp, 3 hóa đơn nháp và 1 sản phẩm. Thêm 10 user giả không mật khẩu để gắn người phụ trách, không TP grant/lời mời. Email giả dùng example.invalid, mô tả phù hợp ghi nguồn giả lập; không chứng từ posted/thanh toán hoặc hồ sơ thật.
- Snapshot dữ liệu trước nạp `.local/native-data-20261102/backup-20261102T015925Z/`: pg_dump + canonical filestore, manifest SHA-256, pg_restore --list đạt; dừng/khởi động lại đúng dev Odoo sở hữu, giữ PostgreSQL/demo18109. Không tuyên bố đã restore snapshot này; không dùng OPS backup committed-source vì checkout có thay đổi chưa commit.
- Kiểm thực chạy: dry-run sửa lỗi tương thích helper Odoo 20 rồi rollback đạt; commit thành công; registry mới verify binding/count, new_records={} và hash dòng TP/user/grant cũ không đổi. HTTP admin đọc đủ dữ liệu tám nhóm, tiền/nháp và người phụ trách đúng; API TP không lẫn project mới. ACL/form native sáu model cho phép thao tác; project create/edit/delete probe savepoint rollback đạt. 0 mail mới, 0 posted mới; kiểm user giả không password. Helper/log/báo cáo local ngoài Git. git diff --check, workflow finish/check; không chạy toàn bộ app tests vì không đổi code ứng dụng.
- Không sửa application code, core, database schema, quyền có sẵn, cấu hình gửi mail, UI-DEMO-001/002 hoặc Next action audit. Không commit/push, không phê duyệt pilot/BASE/ký/hiệu lực hoặc cấp quyền người thật.

## CHG-20261031-002 — Báo cáo Word so sánh Community và Enterprise

- Ngày: 31/10/2026 (Asia/Saigon). Theo yêu cầu người dùng tạo một file Word tổng hợp tính năng, tùy biến và chi phí. Ghi nhận xuất báo cáo 4 trang `deliverables/TANPHAT_ONE_So_sanh_Odoo_Community_Enterprise.docx` dựa trên nguồn chính thức đã kiểm ở CHG-001; giải thích thuật ngữ và đề xuất cho TANPHAT ONE, không phải quyết định mua hoặc báo giá. Bổ sung kiểm chứng CHG-20261102-003: DOCX hiện thiếu tại đường dẫn này, còn PDF local; bỏ link chết, chưa tái tạo báo cáo.
- Phân biệt Standard Online/Custom self-host hoặc Odoo.sh, mã nguồn mở Community/điều khoản Enterprise, API và web riêng, thuê bao/tổng chi phí, User/Light User; ví dụ 30/50/100 người dùng, không tự bịa chi phí triển khai hoặc giá gia hạn. Không thay đổi nguồn nghiên cứu, application code, runtime hoặc database.
- Kiểm chứng: bundled Python python-docx; render_docx.py lần đầu báo thiếu soffice.exe trên Windows, dùng Microsoft Word xuất PDF rồi adapter local gọi rasterizer canonical với bundled Poppler; 4 trang PNG đã xem toàn bộ và sửa đường viền Title trước render cuối. Word COM mất kết nối lúc Quit sau xuất PDF thành công; đã xử lý cleanup ở script local và render cuối thành công. Kiểm cấu trúc DOCX, nội dung, số liệu, link tài liệu và git diff --check; workflow finish/check. Không chạy application tests vì chỉ xuất báo cáo; helper/PDF/PNG ở .local ngoài Git.
- Giữ nguyên Next action audit độc lập UI-DEMO-001/002 và AUTH-002/C01; không commit/push, cài app, mua license hoặc mở scope nghiệp vụ.

## CHG-20261031-001 — So sánh Odoo Community/Enterprise, tùy biến và chi phí

- Ngày: 31/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, tạo [bản so sánh edition](architecture/TP_ODOO_COMMUNITY_ENTERPRISE_COMPARISON.md): tính năng, deployment, quyền tùy biến, Studio/addon/API/React, phí thuê bao và tổng chi phí sở hữu; không phải báo giá hoặc quyết định mua.
- Đọc nội dung nguồn chính thức Editions/Pricing/Enterprise Agreement/External API và đối chiếu inventory/source LGPL-3 local; giữ snapshot công khai ngoài Git tại `.local/edition-comparison-research/`. Giá USD theo phiên tra cứu (Custom trả năm ưu đãi 13,40, niêm yết hiện tại 16,40/user/tháng); không mặc định áp dụng thị trường TP hoặc giá gia hạn. Tách phí hạ tầng, lập trình, bảo trì, thuế và dịch vụ; ghi lưu ý User/Light User theo Agreement v13.
- Khuyến nghị tiếp tục Community trong giai đoạn hiện tại, làm fit-gap/quote/TCO 3 năm trước quyết định Enterprise; đây là đề xuất, không mở scope/mua hàng. Cập nhật status/index; Next action UI-DEMO-001/002, AUTH-002/C01 và các cổng nghiệp vụ giữ nguyên.
- Kiểm chứng: đọc nguồn HTML và biểu tượng edition có/không, số liệu giá/thuê bao, local links/fence/UTF-8, snapshot code trước/sau và git diff --check; workflow finish/check. Không chạy application tests do chỉ nghiên cứu/tài liệu; không cài module, đổi database/runtime, code, commit hoặc push.

## CHG-20261030-005 — Triển khai điều hướng demo theo công việc (UI-DEMO-002)

- Ngày: triển khai 30/10/2026, tiếp tục checkpoint và chốt bàn giao 31/10/2026 (Asia/Saigon). Yêu cầu trực tiếp triển khai bản chạy được theo prompt UI-DEMO-002; trạng thái `IMPLEMENTED_PENDING_AUDIT`, không tự nghiệm thu UI-DEMO-001/AUTH-002/C01.
- Thay hàng tab dài/dấu cộng trong app Demo bằng hai tầng desktop và sáu nhóm Việt; “Tất cả phân hệ”/“Phân hệ” mở dialog tìm không dấu/alias, tên TP chuẩn, mô tả và nhãn minh họa. Toàn bộ 17 leaf giữ action/XML ID; kỹ sư chỉ 15 leaf, không CRM/Bid. Thay menu XML, thêm `static/src/navigation/`, HOOT và hai test server menu; đăng ký assets trong manifest.
- Native extension: QWeb inheritance theo `menu_demo_root`, patch tĩnh tối thiểu đăng ký `NavBar.components`; menu service là nguồn cây quyền, `selectMenu(actualMenu)` là đường điều hướng. Active theo action/controller native, không `doAction` bổ sung, không patch router/service/core. SCSS portal riêng, focus/Esc và cleanup dùng lifecycle/component native.
- Snapshot trước/sau xác nhận code ngoài addon, 25 tracked diff ngoài handoff và sáu SCSS cũ không đổi; giữ nghiệp vụ/model/ACL/grant/seed, React/API, app khác và cảnh báo môi trường. Chỉ upgrade/rebuild runtime demo sở hữu riêng trong lượt triển khai, không sửa DB dev/test; lượt tiếp tục chỉ start demo và chạy test DB demo test.
- Kiểm cuối: `ui_demo.py test` **21 passed, 0 failed/error, không skip được báo** trên `tp_tanphat_demo_ui001_test`; HOOT **6/6**; Ruff đạt. Live Chromium hai actor **17/17 + 15/15** leaf, tìm/active/deep link/reload/history/chuyển app, context dự án, bàn phím/logout đạt. Mười cấu hình viewport 1440/1366/1024/768/375 và bốn ca zoom thật 125%/150% đạt; focus không bị che, reduced motion hoạt động, không lỗi console/network. Log Odoo có cảnh báo markdown2/filestore GC Windows đã biết và test quyền âm mong đợi; không chạy React checks vì không đổi React.
- Cập nhật status/roadmap/spec/README/runbook/kịch bản và [bàn giao file, mapping, ảnh, lệnh/log](demo/UI_DEMO_002_HANDOFF.md). Đã áp dụng skill `C:/Users/vuduc/.codex/skills/frontend-design/SKILL.md` và `skills/odoo-web-guidelines/SKILL.md`. Demo để chạy tại `http://127.0.0.1:18109/odoo`; không commit/push/deploy. Next action: phiên điều phối audit độc lập UI-DEMO-001/002 và quyết định phạm vi trình diễn; business acceptance/pilot vẫn riêng.

## CHG-20261030-004 — Prompt cải tiến điều hướng demo (UI-DEMO-002)

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng gửi ảnh thanh tab native Odoo và yêu cầu prompt làm dễ nhìn, dễ hiểu, đầy đủ hơn. Phiên chính chỉ chuẩn bị prompt; trạng thái `PROMPT_READY`, chưa có code navigation mới.
- Tạo [prompt UI-DEMO-002](prompts/CLAUDE_UI002_DEMO_NAVIGATION.md): sáu nhóm nghiệp vụ, nhãn Việt kèm tên TP chuẩn, selector “Tất cả phân hệ” có tìm nhanh, đủ điểm đến hiện có theo quyền. Nêu cụ thể native menu service/template extension và bẫy overflow More 46px của NavBar Odoo 20, namespace theo app, keyboard/responsive và kiểm hai actor.
- Yêu cầu mới thay lựa chọn UX giữ menu của CHG-003 trong phạm vi demo; giữ SCSS hiện tại, các app khác, React/API, workflow, quyền và runtime. Không triển khai nghiệp vụ mới hoặc tự nghiệm thu UI-DEMO-001/AUTH-002/C01; không commit/push.
- Kiểm chứng: đọc cây menu/action/NavBar local, skill frontend-design và guideline Odoo web; checker baseline CHG-003 đạt. Đối chiếu snapshot maintained và SCSS trước/sau, kiểm mapping 12 phân hệ/action, liên kết/fence/UTF-8 và git diff --check; không chạy lại application tests cho lượt prompt/tài liệu. Kết quả cuối ghi trong workflow handoff.
- Next action: Claude thực hiện prompt; phiên chính audit navigation và phần demo còn pending sau bàn giao.

## CHG-20261030-003 — Ghi chú menu demo và làm mới giao diện UI-DEMO-001

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng hỏi vì sao menu có hai app “TANPHAT ONE” và chọn **giữ nguyên menu**; sau đó yêu cầu “chỉnh lại giao diện bản demo cho đẹp hơn”. Trạng thái demo vẫn `IMPLEMENTED_PENDING_AUDIT`.
- Menu: ghi vào [runbook](../ops/runbooks/UI_DEMO_001.md), [kịch bản trình bày](demo/UI_DEMO_001_PRESENTATION.md) và [đặc tả §7](architecture/TP_UI_DEMO_001_SPEC.md) rằng app “TANPHAT ONE” là `tp_core.menu_platform` hiện do nhóm demo kế thừa `tp_core.group_user`, “Ứng dụng” do `base_install_request`; người trình bày chỉ dùng app Demo. Không đổi menu, nhóm hay quyền.
- Giao diện: chỉ năm file SCSS của `tp_demo_workspace` (namespace `.o_tp_demo`): dải đầu trang dạng bản vẽ, KPI/panel bo góc có bóng nhẹ và nhấc khi hover, chuỗi dự án dạng viên thuốc, làn phân hệ có viền trái theo bản chất dữ liệu, ô “Góc nhìn” nền trắng, dải cảnh báo gọn trên điện thoại, hiện dần tắt theo reduced motion. Đặc tả §8 cập nhật bảng màu/bo góc/chuyển động. Không đổi template, JS, Python, ACL/rule, seed, tooling, React/API hay `odoo/`/`addons/`.
- Test: `scripts\ui_demo.py test` 0 failed, 0 error(s) of 19 tests; `python -m unittest scripts.tests.test_ui_demo` 10/10; kiểm trình duyệt thủ công `demo.lanhdao` ở 1440/1366/375 không cuộn ngang, tương phản màu WCAG ≥ 5,3:1 cho chữ. Demo chạy lại tại `127.0.0.1:18109` (build lại asset bằng stop/prepare/start). Không commit/push.
- Next action: phiên điều phối audit UI-DEMO-001 gồm cả lượt này; nếu cần, chụp lại đủ 12 màn hình và xem bằng `demo.kysu` trước buổi trình bày.

## CHG-20261030-002 — Triển khai demo native Odoo toàn hệ thống (UI-DEMO-001)

- Ngày: 30/10/2026 (Asia/Saigon). Phiên Claude thực thi theo [prompt UI-DEMO-001](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md) và DEC-024. Trạng thái `IMPLEMENTED_PENDING_AUDIT`, không phải technical/business acceptance.
- Thêm addon `custom_addons/tp_demo_workspace/` (nhóm demo, app “TANPHAT ONE – Demo”, 12 màn hình A–L, projection đọc `tp.demo.workspace` theo quyền người xem không `sudo`, view native chỉ đọc, catalog minh họa trong Python, seed idempotent `demo_seed.py`, 19 Odoo tests), tooling `scripts/ui_demo.py` + `scripts/tests/test_ui_demo.py`, [đặc tả](architecture/TP_UI_DEMO_001_SPEC.md), [runbook](../ops/runbooks/UI_DEMO_001.md), [kịch bản trình bày](demo/UI_DEMO_001_PRESENTATION.md). Một ACL mới chỉ đọc `crm.lead` cho nhóm demo kinh doanh; không đổi ACL/rule/workflow TP hiện có.
- Runtime riêng: DB `tp_tanphat_demo_ui001` (+ `_test`), `127.0.0.1:18109`, `.local/ui-demo-001/` ignored, cron tắt, DB neutralize, SMTP cổng đóng; dữ liệu và tệp giả, hai actor `demo.lanhdao`/`demo.kysu`, mật khẩu sinh local không vào Git.
- Test: `ruff check` đạt; tool guard 10/10; Odoo **0 failed, 0 error(s) of 19 tests** (ORM, read_group, export, `/web/content`, ghi trực tiếp bị chặn, phủ định actor không grant); kiểm trình duyệt hai actor ở 1440/1366/375, focus, reduced motion, RPC và tải tệp trực tiếp phủ định. Không đổi React/OpenAPI/API, DB dev/test, `scripts/dev.py`, `odoo/`/`addons/`; không cài `tp_web_login`; không commit/push.
- Next action: phiên điều phối audit demo trước khi trình lãnh đạo; audit AUTH-002 slice 2 vẫn là việc riêng.

## CHG-20261030-001 — Prompt dựng demo native Odoo toàn hệ thống

- Ngày: 30/10/2026 (Asia/Saigon). Người dùng chọn trực tiếp native Odoo để demo trước và khung toàn hệ thống cho lãnh đạo; phiên chính tiếp tục điều phối, không trực tiếp sửa application code.
- Task: UI-DEMO-001. Ghi DEC-024; tạo [prompt Claude triển khai](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md), cập nhật PROJECT_STATUS/ROADMAP/index kiến trúc. Phạm vi gồm common workspace, chín phân hệ hiện hành + CRM/Request/Bid giới thiệu; tận dụng native read views, phần chưa có là minh họa có nhãn.
- Prompt yêu cầu DB/config/data-dir/port riêng, dữ liệu/actor giả, seeder/tooling có ownership guard, scope/grant backend kể cả read_group/export/file, test native/live và ảnh/kịch bản trình bày. Không đổi React/API, core, DB dev/test, BASE/ký/hiệu lực/thanh toán hoặc grant người thật; AUTH-002 audit và C01 giữ là việc riêng.
- Kiểm chứng thực: snapshot maintained trước/sau bằng nhau (139 file, digest `46eff2f307c6e3a1260b635889c840899ae91cb49c85a02001ab6f93df77562e`); kiểm UTF-8/fence/bảng/link của 6 tài liệu, 70 link local và 0 lỗi; `git diff --check` đạt (chỉ cảnh báo LF/CRLF có sẵn). Không chạy test ứng dụng cho lượt tài liệu. Trạng thái PROMPT_READY, chưa triển khai addon hoặc runtime demo; không commit/push.
- Next action: Claude triển khai theo prompt; phiên điều phối audit kết quả và phân biệt khả năng runtime với minh họa trước khi dùng trình lãnh đạo.

## CHG-20261029-052 — Kiểm kê module Odoo 20 và trạng thái cài đặt

- Ngày: 29/10/2026 (Asia/Saigon). Người dùng yêu cầu danh sách module nghiệp vụ toàn Odoo 20, chức năng và module đã cài trong TANPHAT ONE.
- Tạo [TP_ODOO20_MODULE_INVENTORY.md](architecture/TP_ODOO20_MODULE_INVENTORY.md): 643 manifest `addons/` + core `base`, 7 custom addon, 34 ứng dụng chuẩn; danh mục ứng dụng với chức năng tiếng Việt và toàn bộ 651 manifest local thuộc phạm vi (không gồm 15 test framework trong `odoo/addons/`). Bảng chi tiết giữ tên/summary/category theo manifest, không coi đó là nghiệm thu runtime.
- SELECT `ir_module_module` read-only trên dev/test xác nhận 87/85 installed; chỉ dev có thêm `l10n_vn` và `account_qr_code_emv`. `tp_web_login` có source nhưng chưa cài trên hai database này; không dùng trạng thái verify DB thay dev/test.
- Đọc HTTP 200 danh mục All Apps, tài liệu Odoo 20 và Editions; phân biệt app được giới thiệu với addon kỹ thuật, source có sẵn với installed, accounting nền với Enterprise, các ứng dụng ngoài checkout với chức năng đã chạy. Snapshot metadata/trạng thái ở `.local/module_inventory/` ngoài Git; không lưu credential hoặc dữ liệu nghiệp vụ.
- Không cài module, không start/stop/upgrade/seed, không sửa application code, OpenAPI, database/schema hoặc quy chế nghiệp vụ. Không commit/push.
- Kiểm tra: đối chiếu source manifest và database read-only; kiểm bảng/link và count/status; maintained code snapshot không đổi; `git diff --check`; workflow finish/check. Không chạy application tests vì đây là inventory/tài liệu.
- Next action: giữ audit độc lập AUTH-002 slice 2; danh mục này là nguồn tra cứu, không tự mở task hay cho phép cài module.

## CHG-20261029-051 — Làm rõ phạm vi quyết định UX DEC-023

- Ngày: 29/10/2026 (Asia/Saigon). Rà soát lại cách ghi DEC-023 sau khi người dùng xác nhận nguyên tắc giao diện chung.
- Làm rõ phần người dùng đã chốt: một nền/common shell chung, trải nghiệm thay đổi theo phòng ban/vai trò/quyền và không tạo frontend lặp theo phòng. Các workspace/menu/dashboard/field/route/action cụ thể, shared detail và DTO `allowed_actions` được đánh dấu là hướng thiết kế đề xuất cần owner/spec theo domain.
- Cập nhật `docs/DECISIONS.md`, `docs/PROJECT_STATUS.md` và `docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md`. Không đổi code, API, database, module, runtime hoặc Next task AUTH-002 audit.
- Kiểm tra: `git diff --check`; maintained code unchanged; `ai_workflow.py finish/check`; không chạy application tests vì chỉ hiệu chỉnh phân loại quyết định UX.
- Next action: giữ audit độc lập AUTH-002 slice 2; chỉ lập spec workspace cụ thể khi có task/domain owner.

## CHG-20261029-050 — Chốt mô hình giao diện chung và workspace theo phòng ban

- Ngày: 29/10/2026 (Asia/Saigon). Người dùng xác nhận: một nền giao diện/common shell cho toàn hệ thống; mỗi phòng ban có workspace, menu, dashboard, trường dữ liệu và nút thao tác khác nhau theo vai trò và quyền.
- Ghi quyết định **DEC-023**: một frontend/common shell dùng chung; trải nghiệm phòng ban/vai trò thay đổi theo quyền. Shared detail, capability/scope/state DTO và `allowed_actions` là hướng triển khai đề xuất cần đặc tả theo domain, không phải danh mục đã mở. Không tạo frontend/addon riêng lặp lại theo phòng ban; ẩn nút chỉ là UX.
- Cập nhật [TP_PLATFORM_SOURCE_STRUCTURE.md](architecture/TP_PLATFORM_SOURCE_STRUCTURE.md) và `PROJECT_STATUS.md`. Không sửa application code, OpenAPI, database, module hoặc runtime; chưa mở workspace nghiệp vụ mới.
- Kiểm tra: `git diff --check`; `ai_workflow.py finish/check`; không chạy application tests vì lượt này chỉ ghi quyết định kiến trúc.
- Next action: giữ audit độc lập AUTH-002 slice 2; khi xây UI workspace phải lập đặc tả từng workspace, route, field policy, capability, scope và test trước khi giao Claude code.

## CHG-20261029-049 — Phân tích chọn lọc Excel ERP tham khảo

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, rà soát read-only toàn bộ Excel trong thư mục ERP để chọn kiến thức áp dụng cho TANPHAT ONE.
- Kiểm tra 8 workbook có giá trị nghiệp vụ: quỹ/ngân hàng, dư nợ vay, dự kiến thu–chi, Master tổng hợp, PKH/DA Temp, công trình dở dang và mẫu kế toán lịch sử. Loại khỏi nội dung đọc 3 file danh sách/tài khoản dùng thử và file khóa; không lưu raw values, credential, PII hoặc số tiền thật.
- Tạo [TP_EXCEL_REFERENCE_ANALYSIS.md](architecture/TP_EXCEL_REFERENCE_ANALYSIS.md) và manifest provenance ngoài Git tại `.local/excel_reference_review/`. Kết luận chính: tách production–acceptance–invoice–cash; actual–forecast–obligation; facility/drawdown/repayment/allocation; snapshot/as-of; staging/provenance; reconcile; append-only correction/audit; parent–child subcontractor.
- XL02 có external links và cached `#REF!`; XL08 chỉ đọc được cached structure; không coi formula/tổng workbook là authoritative. Không chạy macro, refresh link, recalculation, import Excel hoặc mở module Finance/Import/Data Lake.
- Phát hiện source drift: XL05/PKH hiện hash `e34052d2986f…`, trong khi registry BIZ-001 dùng `4ee0ff275058…`. Chỉ các bằng chứng phụ thuộc trực tiếp S03 chuyển thành `legacy/pending re-baseline`; không vô hiệu hóa S01/S02/S04/S05 hoặc các DEC đã xác nhận. Cần re-hash và đối chiếu cấu trúc XL05 trước khi tái xác nhận.
- Kiểm tra: inventory NAS, manifest/hash, review độc lập XL01–XL08, `git diff --check`; không chạy application tests vì chỉ bổ sung tài liệu tham khảo. Checker `finish/check` sẽ ghi handoff cho batch này.
- Next action: giữ nguyên audit độc lập AUTH-002 slice 2; khi mở Finance/Import phải có owner, mapping, policy, evidence và decision riêng.

## CHG-20261029-048 — Bóc tách chi tiết màn hình, biểu mẫu và quy tắc nghiệp vụ 16 tài liệu IMIS2

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu trực tiếp của người dùng ("phải đọc từng trang", "viết thành tài liệu đi"), bóc tách chuyên sâu toàn bộ 16 tài liệu HDSD IMIS2 Web/Mobile năm 2021 của EVN/EVNICT thành sổ tay đặc tả tham chiếu chi tiết.
- Tạo [TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md](architecture/TP_IMIS2_DETAILED_MANUAL_ANALYSIS.md): bóc tách chi tiết từng màn hình (screens), biểu mẫu (forms), danh mục trường dữ liệu (fields), quy trình từng bước (Step-by-step) và các quy tắc kiểm tra ràng buộc (validation rules / edge cases).
- Bổ sung chi tiết: cấu hình phân cấp context mobile (IMISONSITE), form nhật ký thi công điện tử (ca, thời tiết, HSE, ảnh bắt buộc tọa độ GPS/thời gian thực, Sim CA), quy trình nghiệm thu 2 tầng (kiểm tra hồ sơ -> kiểm tra hiện trường/khối lượng thực đo -> ký số), quy tắc gói thầu phân lô/chỉ định thầu/tự thực hiện, hợp đồng đa tiền tệ, bảo lãnh ngân hàng, phụ lục/phạt hợp đồng, luồng thẩm định thiết kế 3 bên Submittal -> Review -> Approval, 4 chuyên mục khảo sát địa chất (khoan, hố đào, địa vật lý, hầm), phiếu giá thanh toán Phụ lục 03a và khóa cứng sau giải ngân, thuật toán chấm điểm nhà thầu 3 cấp có chặn trần điểm trừ, và kho dữ liệu nhà thầu/liên danh.
- Tổng hợp bản đồ ánh xạ chi tiết các thực thể dữ liệu và quy tắc nghiệp vụ vào 9 phân hệ của TANPHAT ONE (TP Survey, TP Design, TP Contracts, TP Finance/STL-001, TP Documents, TP Tasks/TVGS Mobile, TP Dashboard/Partner Rating).
- Cập nhật liên kết trong docs/architecture/README.md và docs/architecture/TP_IMIS2_REFERENCE_ANALYSIS.md.
- Tuyệt đối tuân thủ nguyên tắc an toàn: Không sửa application code, OpenAPI, database, runtime hoặc cấu hình dev/test; không mở module rỗng; tài liệu đóng vai trò tham chiếu thiết kế cho roadmap tương lai.
- Kiểm tra: git diff --check, validator liên kết/bảng, checker start/finish/check; không chạy application tests vì chỉ bổ sung tài liệu kiến trúc.
- Next action: giữ nguyên task hiện hành trong PROJECT_STATUS.md (audit AUTH-002 slice 2); khi triển khai phân hệ mới sẽ sử dụng đặc tả tham chiếu này làm đầu vào thiết kế.

## CHG-20261029-047 — Hiệu chỉnh phản biện và provenance cho phân tích IMIS2

- Ngày: 29/10/2026 (Asia/Saigon). Phản biện độc lập bản phân tích CHG-046 bằng hash nguồn, text extraction và locator của đủ 16 manual; xác nhận 16/16 SHA-256 khớp nguồn, 250.023 ký tự trích xuất và 974 media được kiểm kê (ảnh chưa được coi là bằng chứng API/quyền).
- Sửa các điểm có thể gây hiểu nhầm: `tp.project.grant` tách khỏi `tp_contract`; Bid chỉ chứng minh hồ sơ/kết quả lựa chọn, không tự có scoring/authority; giá tham khảo 13 không tự có currency/source/effective semantics; appendix/penalty/revision/audit là thiết kế TP; `account.move` là bridge đích có điều kiện, chưa phải Finance runtime.
- Đổi sơ đồ từ chuỗi bắt buộc thành bản đồ node/branch/parallel/iterative; bổ sung case direct award, nhiều đợt nghiệm thu, tạm ứng trước nghiệm thu theo điều khoản, handover/closeout độc lập với cash; thêm negative cases Bid và bộ khoảng trống/ca thiết kế cho TP.
- Đổi bảng hướng đi thành `Candidate / proposed`, giữ `DEFER` của Data Lake là recommendation chưa phải DEC, không thay đổi Next task AUTH-002 audit hoặc roadmap/master plan. Bổ sung chỉ mục SHA-12/locator để AI sau tìm lại nguồn; không đưa UNC, file gốc, dữ liệu thật hoặc credential vào Git.
- Không sửa application code, OpenAPI, database, runtime, module hoặc quyết định business; không import dữ liệu EVN và không mở Request/Bid/Survey/Design/Documents/mobile/Finance bridge/Data Lake.
- Kiểm tra: đối chiếu source/hash/extraction, phản biện 3 nhóm manual độc lập, `git diff --check`, checker `start/finish/check`; không chạy application tests vì đây là hiệu chỉnh tài liệu tham khảo.
- Next action: giữ task hiện hành trong `PROJECT_STATUS.md`; khi mở miền mới phải lập task/owner/decision/acceptance riêng và không dùng manual EVN làm cổng code.

## CHG-20261029-046 — Phân tích chọn lọc 16 manual IMIS2 EVN

- Ngày: 29/10/2026 (Asia/Saigon). Đọc toàn bộ 16 tài liệu DOCX IMIS2 Web/Mobile năm 2021 trong thư mục tham khảo do người dùng cung cấp; đối chiếu manifest SHA-256 và bản text extraction ngoài Git tại `.local/imis2_review/`.
- Tạo [TP_IMIS2_REFERENCE_ANALYSIS.md](architecture/TP_IMIS2_REFERENCE_ANALYSIS.md): phân loại từng manual thành tiếp thu/điều chỉnh/chỉ tham khảo/không áp dụng; rút ra project scope, work breakdown, bid package/lot, contract revision, evidence/version, diary/issue/acceptance, documents, handover, closeout và contractor master.
- Giữ ranh giới EVN–Tấn Phát: không copy cơ cấu, hạn mức, quyền, chữ ký, giải ngân, scoring 100 điểm hoặc thao tác xóa; “Kho dữ liệu nhà thầu” không phải Data Lake; BASE approval, ký, hiệu lực, nghiệm thu, thanh toán và Accounting vẫn tách.
- Không sửa application code, OpenAPI, database hoặc runtime; không import dữ liệu EVN và không mở module/connector/mobile/Data Lake. Cập nhật `TP_REFERENCE_RESEARCH_AND_HANDOFF.md`, architecture README và status để AI phiên sau tìm được kết quả.
- Kiểm tra: đọc/extract 16 manual, provenance/hash manifest, link/table review, `git diff --check`; không chạy application test vì batch chỉ nghiên cứu tài liệu.
- Next action: giữ nguyên task hiện hành trong `PROJECT_STATUS.md` (audit AUTH-002 slice 2); các miền IMIS2 chỉ mở qua task/owner/acceptance riêng.

## CHG-20261029-045 — Đối chiếu sơ đồ kiến trúc TP.ONE với nền TANPHAT ONE

- Ngày: 29/10/2026 (Asia/Saigon). Đọc và render kiểm tra `TP_ONE_So_do_kien_truc.pdf` (1 trang A4, provenance `REF-ARCH-PDF-20261029`) do người dùng cung cấp.
- Ghi vào `TP_REFERENCE_RESEARCH_AND_HANDOFF.md`: sơ đồ là target architecture L1 Frontend → API → L2 Odoo 20 → CSDL; Projects là trục liên kết; “Căn cứ” là nguồn xác định scope/quyền/workflow; QL91 chỉ là ví dụ.
- Đối chiếu nhãn PDF với TP Dashboard/Projects/Survey/Design/Contracts/Tasks/HR/Finance/Documents và các miền Bid/Request/AI; phân biệt target scope với module/runtime đã có. Ghi rõ mobile native, cardinality, actor/transition, workflow engine, API write/sync và mapping addon chưa được chốt từ hình.
- Không đổi application code, OpenAPI, database, runtime hoặc quyết định BASE/Request mới. Không coi hình là lệnh cài module; BASE vẫn official approval, Request/AI vẫn có boundary và gate riêng.
- Kiểm tra: `pdfinfo`, text extraction, render PNG, đọc trực quan; link/bảng/provenance và `git diff --check`; không chạy application test vì batch tài liệu-only.
- Next action: giữ Next task hiện hành trong `PROJECT_STATUS.md`; khi mở miền Bid/Request/AI hoặc mobile phải lập task/owner/acceptance riêng.

## CHG-20261029-044 — Lưu riêng kiến thức nghiệp vụ Request trên BASE

- Ngày: 29/10/2026 (Asia/Saigon). Theo yêu cầu người dùng, thêm `docs/architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md`: nguồn `REF-BASE-REQUEST-20261029`, group/tab/form đã quan sát, actor chưa xác minh, vòng đời Proposed-TP, return/reject/disputed, reference/evidence/version và các gap trước connector.
- Tách rõ UI BASE khỏi state/API Odoo; không suy quyền từ người duyệt/follower, không biến approved thành signed/effective/paid, không coi nghiệp vụ kế toán TP đã nghiệm thu. Workflow chi tiết vẫn tham chiếu BIZ-002 H/I; không chốt owner/hạn mức hoặc quyết định nghiệp vụ mới.
- Liên kết từ AGENTS, sổ nghiên cứu, architecture README, quy trình điều phối và status. Giữ Next task hiện hành. Chỉ sửa Markdown, không sửa application code, database/runtime, credential, commit/push.
- Checkpoint CHG-043 của phiên khác được giữ nguyên đến khi tự đóng; tài liệu riêng được soạn trước, `ai_workflow.py start` chạy trước các sửa đổi bàn giao dùng chung sau đó. Không finish thay code batch khác.
- Kiểm tra: đối chiếu nguồn BIZ-002 H/I và DEC-013; kiểm liên kết/bảng/nội dung; `git diff --check`; so snapshot maintained code với checkpoint của batch này. Không chạy application tests vì chỉ bổ sung tài liệu; kết quả `finish/check` ghi trong workflow state.

## CHG-20261029-043 — Cài hr_timesheet, hr_expense, project_hr_expense trên test và dev; thêm vào MODULES

- Ngày: 29/10/2026 (Asia/Saigon). Theo lựa chọn người dùng "Timesheet + chi phí" sau khi rà sơ đồ kiến trúc TP.ONE. Backup trước cài `.local/module-install-20261029-160204/` (ngoài Git, 408 checksum, verify đạt, `REPORT.md`).
- Cài `hr_timesheet`, `hr_expense`, `project_hr_expense` (+ auto `spreadsheet_dashboard_hr_timesheet`) không demo trên `tp_tanphat_test` (85 module) rồi `tp_tanphat_dev` (87 module); không ERROR/Traceback. Odoo tự tạo tài khoản phân tích cho từng project, project "Internal" không `tp_managed` và 6 sản phẩm chi phí; giá trị dữ liệu TP không đổi (chỉ `write_date`).
- `scripts/dev.py`: `STANDARD_MODULES = 'crm,account,hr_timesheet,hr_expense,project_hr_expense'`. Không sửa `odoo/`, `addons/`, `custom_addons/`, `frontend/`, `contracts/`; không commit.
- Kiểm tra: Odoo tests trên test 0 failed/0 error of 79 (trước và sau đổi MODULES); `dev.py smoke` PASS; logout/session lạ 401; API project không lộ "Internal"; `ruff check scripts/dev.py` đạt.

## CHG-20261029-042 — Lưu sổ kiến thức tham khảo A1/Base và bàn giao điều phối

- Ngày: 29/10/2026 (Asia/Saigon). Tạo `docs/architecture/TP_REFERENCE_RESEARCH_AND_HANDOFF.md` để phiên AI mới đọc lại được nguồn A1 Consulting, quan sát Base Request, giới hạn bằng chứng, mapping với kiến trúc TANPHAT ONE và các giả thuyết Request/Bid.
- Phân loại rõ user-confirmed/observed/runtime-evidence/proposed/open; không biến bài marketing, ảnh/UI Base hoặc tên module thành quy chế, API, hạn mức hay quyết định schema. Ghi rõ BASE vẫn là authority theo DEC-013, Data Platform vẫn là recommendation `DEFER`, và module chuẩn CRM/Account đã cài theo CHG-039/041 nhưng workflow TP chưa mở.
- Thêm liên kết trong `docs/architecture/README.md`, `docs/AI_COORDINATION_WORKFLOW.md` và status. Không sửa application code, OpenAPI, database, runtime, credential hoặc quyết định nghiệp vụ mới.
- Kiểm tra: đọc-only source/status trước khi ghi; kiểm tra checkpoint đã đóng; sẽ chạy `git diff --check` và `ai_workflow.py finish/check`. Không chạy application test vì batch chỉ thêm tài liệu.
- Next action: audit độc lập AUTH-002 slice 2 CHG-038 theo `PROJECT_STATUS.md`; đọc sổ này khi task chạm A1/Base/Request/Bid/Data Platform.

## CHG-20261029-041 — Cài crm, account trên dev (chart VN) và thêm vào MODULES

- Ngày: 29/10/2026 (Asia/Saigon). Theo lựa chọn người dùng chấp nhận `l10n_vn`. Backup `.local/module-install-20261029-154126/` (327 checksum, verify đạt; ngoài Git). Dev: `--init crm,account --without-demo=True --stop-after-init` exit 0, 28 module mới (26 như test + `l10n_vn`, `account_qr_code_emv`), không ERROR; TP không đổi version; không sale/purchase*/`tp_web_login`/Request/Bid.
- Dữ liệu: chart `vn` tự nạp (301 tài khoản, 31 thuế, 8 journal), công ty giữ VN/VND; 0 chứng từ/thanh toán/lead; không bảng tp_*/project_*/hr_* nào đổi; không nhập dữ liệu thật.
- `scripts/dev.py`: `MODULES` = `STANDARD_MODULES` `crm,account` + `CUSTOM_MODULES` sáu module TP, ghi chú chart và giới hạn setup mới (generic chart do cài trước khi seed VN).
- Kiểm tra: `dev.py smoke` PASS; logout CSRF → `/me` 401, session lạ 401; log 0 ERROR; Vite `/work/` 200; `ruff check scripts/dev.py` đạt; `dev.py test` với MODULES mới 0 failed/0 error of 79 tests. Không ghi TECHNICAL_ACCEPTED; không commit.

## CHG-20261029-040 — Upgrade TP trên dev lên 20.0.1.1.0

- Ngày: 29/10/2026 (Asia/Saigon). Vận hành theo lựa chọn người dùng sau CHG-039; không đổi source. Backup `.local/module-install-20261029-153658/` (327 checksum, verify đạt; ngoài Git) trước khi chạy `scripts/dev.py upgrade` với Odoo đã dừng.
- Kết quả: tp_project/tp_contract/tp_api/tp_planning_api 20.0.1.0.0 → 20.0.1.1.0; 5 bảng và 3 cột CTR-002a có trên dev, khớp test; post-migrate gán phòng ban cho HD-DEV-001/003, HD-DEV-002 giữ NULL (project chưa có phòng chủ trì). Không module mới; `crm`/`account`/`l10n_vn` vẫn uninstalled. Không bảng tp_*/project_*/hr_* nào đổi trên cột cũ; `seed_dev` ghi lại mật khẩu dev từ dev-secrets (2 mail thông báo `exception`, không có mail server).
- Kiểm tra: upgrade exit 0, không ERROR/Traceback; `dev.py start` + `dev.py smoke` PASS (login, `/me` 401, project/contract scope, grant tài chính); log sau khởi động 0 ERROR, `/api/v1/contracts` 200; Vite `/work/` 200.
- Next: người dùng quyết định hệ thống tài khoản VN trước khi cài `crm`/`account` trên dev; MODULES chưa đổi. Không ghi TECHNICAL_ACCEPTED.

## CHG-20261029-039 — Cài module chuẩn Odoo crm, account trên test; dev BLOCKED

- Ngày: 29/10/2026 (Asia/Saigon). Vận hành theo yêu cầu trực tiếp người dùng; không đổi `odoo/`, `addons/`, `custom_addons/`, `frontend/`, `contracts/`, `scripts/dev.py`. Backup `.local/module-install-20261029-151435/` (dump/filestore/conf/revision/diff/module state/fingerprint, 257 checksum, verify đạt; ngoài Git).
- Test `tp_tanphat_test`: `--init crm,account --without-demo=True --stop-after-init` exit 0, không ERROR/Traceback; crm 20.0.1.9, account 20.0.1.6 + 24 module phụ thuộc/auto-install chuẩn; TP không upgrade; không `l10n_vn`/sale/purchase*/`tp_web_login`/Request/Bid. Odoo tự nạp `generic_coa` (country test → US). `dev.py test` 0 failed/0 error of 79 tests; smoke anonymous `/web/login` 200, `/api/v1/me|projects|contracts` 401 JSON.
- Dev `tp_tanphat_dev`: BLOCKED, không cài — schema TP dev 20.0.1.0.0 thấp hơn source 20.0.1.1.0 (install sẽ tạo một phần schema ngoài migration) và công ty VN sẽ kéo `l10n_vn` tự tạo tài khoản/thuế/journal. DB dev không đổi (0/322 bảng); Odoo dev khởi động lại, smoke đạt login/me/projects, `/api/v1/contracts` 500 có sẵn do chưa upgrade.
- Next: người dùng quyết định upgrade dev TP và chart VN trước khi cài dev; chưa thêm module vào MODULES. Không ghi TECHNICAL_ACCEPTED.

## CHG-20261029-038 — AUTH-002 slice 2: handoff 2FA và trang xác thực native

- Ngày: 29/10/2026 (Asia/Saigon). Task AUTH-002 slice 2, lane F, scope AUTH-002-SPEC v0.6; gate đầu vào đạt, status `IMPLEMENTED_PENDING_AUDIT`. Thêm `custom_addons/tp_web_login/**` (QWeb/CSS bundle riêng/data noupdate D6-a/HttpCase/README), đổi `session.tsx`, `LoginPage.tsx`, `login.spec.ts`, thêm `auth002-live.spec.ts`; cập nhật status/roadmap/đặc tả. Font hệ thống để hỗ trợ tiếng Việt/offline, không CDN. Không model/controller/API/route mới, không sửa core hoặc D1–D6.
- Kết quả: React handoff `/web/login/totp?redirect=<path /work/>` cùng origin, giữ deep link/query/hash; link passkey vẫn `/web/login`. Native dùng monogram TANPHAT ONE, màu đã chốt, chữ Việt cố định và lỗi che chuỗi server; Hủy POST/CSRF về `/work/`. D6-a đặt invitation_scope=b2b/reset_password=False khi cài trên verify DB; giữ captcha/passkey/CSRF/cooldown/session native và Manage Databases theo list_db.
- Test thực chạy: typecheck PASS; Vitest 4 file/29 PASS; build `VITE_ODOO_DATABASE=tp_tanphat_dev` PASS; Ruff/compileall/XML/E2E TypeScript compile PASS; mock `login.spec.ts` 5/5 PASS (T07); Odoo HttpCase T10 summary 3 test/0 failed/0 errors/0 skip trên verify DB; live opt-in T05/T08/T09/T12 3/3 PASS/0 skip, browser en-US. Đã sửa ParseError xpath class động rồi rerun; sửa T07 cần mở details, sửa false positive cấm mọi storage; correction cuối chuyển CSS static sang bundle `/web/assets` để đi qua proxy Vite sẵn có, T10/live chạy lại sau correction. Không coi exit code hoặc collection/skip là test live đạt.
- Môi trường: `tp_tanphat_auth002_verify`, origin `http://127.0.0.1:18099`, PG55432, fixture `auth002.verify.*`, helper `.local/auth002-verify/` ngoài Git vì C01 chưa bàn giao. Dev Odoo18069/PG55432/Vite4173 có sẵn giữ nguyên; test Vite4174 và Odoo18099 đã dừng sau kiểm, không dừng process không sở hữu, giữ verify DB. Dev addon chưa cài và auth config digest không đổi; không cài/upgrade/seed dev/test chuẩn, không commit/push/deploy.
- Giới hạn/next: passkey ceremony và nhớ thiết bị chưa kiểm bằng trình duyệt thật; header trang mã/HTTPS/proxy/list_db/staging thuộc C06, addon chưa vào dev. Phiên điều phối audit độc lập CHG-038; không tự ghi TECHNICAL_ACCEPTED/business acceptance/pilot. Workflow finish/check ghi ở snapshot bàn giao, không thay test nghiệp vụ.

## CHG-20261029-037 — AUTH-002 slice 1: tiếp quản audit, sửa mutation 401 và chốt kiểm chứng

- Phạm vi: theo yêu cầu trực tiếp tiếp quản phần Claude, phát hiện và sửa P2 của L02: query 401 đã về login nhưng mutation 401 chỉ hiện lỗi trong form. Implementation subagent sửa `frontend/src/app/providers.tsx` dùng handler 401 chung cho QueryCache/MutationCache và thêm `frontend/tests/e2e/session-mutation-401.spec.ts`; phiên chính review patch và chạy kiểm tra độc lập. Không backend/OpenAPI/state/capability mới; không setup/upgrade/seed, không cài addon lên dev, không commit/push. Mô hình điều phối dài hạn giữ nguyên.
- Kiểm tra: regression mutation 401 đã fail trước sửa; sau sửa, phiên chính chạy typecheck/build đạt, Vitest 4 file/29 test đạt, mock E2E 16/16 đạt (POST/PATCH 401, deep link query/hash, đăng nhập lại refetch dữ liệu mới, không tự gửi lại mutation; 403/409/422/503 giữ workspace; login-notices và contract workflow). Hồi quy live login/projects sau correction 8/8 đạt; ca live expiry notice local 1/1 đạt (cookie bị xóa → projects 401 → câu expired nguyên văn, xóa card, giữ deep link, storage trống → đăng nhập lại). Runtime dev ban đầu và cuối cùng đều dừng; chỉ start/stop để kiểm, không upgrade/seed. Kiểm snapshot chỉ hai file code nói trên đổi trong batch; validator tài liệu, `git diff --check`, workflow finish/check ghi ở handoff.
- Workflow/handoff: cập nhật status, đặc tả mục 10.5/10.6, roadmap, architecture README, master plan (nhánh F AUTH-002 và diễn đạt tracked đúng thực tế), quy trình kiểm frontend bắt cả query/mutation 401. R5 đã có live evidence; R1–R4 giữ giới hạn cũ. Slice 1 `TECHNICAL_ACCEPTED` phạm vi test; chưa business acceptance/pilot.
- Next: giao [prompt AUTH-002 slice 2](prompts/CLAUDE_AUTH002_S2_NATIVE_LOGIN.md) khi người dùng mở batch đó; slice 2 chưa code, cài addon chỉ trên database test cô lập.

## CHG-20261029-036 — AUTH-002 slice 1: phiên điều phối review, TECHNICAL_ACCEPTED phạm vi test

- Phạm vi: phiên điều phối đọc diff CHG-035 theo prompt slice 1 và đặc tả v0.6, chạy lại test độc lập. Kết luận slice 1 `TECHNICAL_ACCEPTED` cho phạm vi test (mock và runtime dev, không người dùng thật), không có finding P1/P2; năm ghi nhận P3 R1–R5 ở mục 10.4 đặc tả (L03 nối `navigate` với `history.replaceState`; thông báo `role="status"` lúc mount; Caps Lock chỉ kiểm sự kiện tổng hợp; L01 dựa chuỗi mặc định `Access Denied`; `expired` chỉ kiểm mock). Cập nhật đặc tả (dòng trạng thái, mục 10.4, mục 14), roadmap, architecture README, status. Không sửa application code, DECISIONS, `custom_addons/` hoặc OpenAPI; không setup/upgrade/seed; không commit/push. Chưa phải business acceptance hay pilot.
- Kiểm tra: typecheck đạt; Vitest 4 file/29 test đạt; build `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; `login-notices.spec.ts` 7/7 khi không có Odoo; runtime dev ban đầu dừng, `dev.ps1 start` rồi `login-notices` + `login.spec.ts` + `projects.spec.ts` 15/15 đạt, `dev.ps1 stop`, `status` xác nhận đã dừng; validator tài liệu, `git diff --check`, workflow finish/check.
- Next: người dùng giao prompt slice 2 cho một phiên Claude.

## CHG-20261029-035 — AUTH-002 slice 1: React báo khóa tạm, hết phiên, đã đăng xuất và chi tiết nhỏ

- Phạm vi: phiên Claude thực thi prompt slice 1 (đặc tả v0.6). L01 `client.ts` phân loại `AccessDenied` theo V-B (chỉ `["Access Denied"]` là `credentials`, còn lại `cooldown`) với câu chữ cố định; L02 cờ hết phiên trong bộ nhớ (`features/auth/sessionNotice.ts`, nối QueryCache ở `providers.tsx`); L03 đăng xuất gửi `redirect=/work/?signed_out=1`, `LoginPage` hiện thông báo rồi xóa tham số không thêm mục history; L05 Caps Lock qua `aria-live`; L06 focus ô tên đăng nhập; L07 nhãn ngôn ngữ chữ tĩnh; L08 cho `cooldown`, `credentials`, `expired`, `signed_out`, `caps_lock`. Handoff 2FA giữ `/web/login` và câu chữ cũ. Test mới `sessionNotice.test.ts`, `login-notices.spec.ts`; T01 trong `client.test.ts`; ca MFA `login.spec.ts` kiểm thêm `/web/login` và câu chữ cũ; `projects.spec.ts` kiểm thông báo đăng xuất và URL `/work/`. Bàn giao ở mục 10.3 đặc tả. Không sửa `custom_addons/`, OpenAPI, `odoo/`/`addons/`; không setup/upgrade/seed; không commit/push.
- Kiểm tra: typecheck đạt; Vitest 29/29; build `VITE_ODOO_DATABASE=tp_tanphat_dev` đạt; mock E2E 7/7; T11 trên runtime dev (ban đầu dừng, start rồi stop) 15/15 (`login-notices`, `login.spec.ts`, `projects.spec.ts`); `git diff --check`; workflow finish/check.
- Next: phiên điều phối review slice 1 (`IMPLEMENTED_PENDING_AUDIT` → `TECHNICAL_ACCEPTED` hoặc `NEEDS_FIX`) rồi mới giao slice 2.

## CHG-20261029-034 — AUTH-002 v0.6: chuyển cả hai slice sang READY_FOR_TEST_CODE, soạn prompt

- Phạm vi: người dùng trả lời “Move both slices”. Đặc tả AUTH-002 lên v0.6: slice 1 và slice 2 ở `READY_FOR_TEST_CODE`; mục 10.2 làm rõ thứ tự (slice 1 trước), câu chữ `mfa_*` đi cùng L04 ở slice 2, L04 chỉ đổi link handoff (link passkey F8 giữ `/web/login`), T11 cần runtime dev cho `projects.spec.ts`, T10 chạy trên database test cô lập và không thêm addon vào `dev.MODULES`. Tạo prompt `docs/prompts/CLAUDE_AUTH002_S1_REACT_LOGIN.md` và `CLAUDE_AUTH002_S2_NATIVE_LOGIN.md`. Cập nhật roadmap, architecture README, status. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng giao prompt slice 1; sau bàn giao, phiên điều phối review rồi giao prompt slice 2.

## CHG-20261029-033 — AUTH-002 v0.5: người dùng duyệt câu chữ 6.1

- Phạm vi: người dùng trả lời “Approve 6.1”. Đặc tả AUTH-002 lên v0.5: `totp_placeholder` và `totp_error` mục 6.1 chuyển thành câu chữ đã duyệt; kế hoạch slice 2 bỏ điều kiện chờ duyệt; mục 10.1 đối chiếu cổng Ready for Code cho cả hai slice, không còn quyết định mở. Cập nhật roadmap, architecture README, status. Không ghi chuyển `READY_FOR_TEST_CODE`; không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng chọn chuyển slice 1, slice 2 hoặc cả hai sang `READY_FOR_TEST_CODE`.

## CHG-20261029-032 — AUTH-002 v0.4: người dùng chọn D6-a

- Phạm vi: người dùng chọn “Disable both (D6-a)”. Đặc tả AUTH-002 lên v0.4: D6 chuyển vào bảng đã chốt; mục 3.1 ghi cách áp dụng (dữ liệu `noupdate` của `tp_web_login` đặt `auth_signup.invitation_scope = b2b`, `auth_signup.reset_password = False`; không gỡ module, không xóa link bằng template; dev/pilot/production theo checklist C06). Cập nhật L12, T10, kế hoạch slice 2, rollback, rủi ro G7, truy vết, roadmap, architecture README, status. Câu chữ 6.1 vẫn `proposed`. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: đối chiếu tĩnh `auth_signup` data/controller/template; validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng duyệt câu chữ 6.1 và chọn có chuyển slice 1 sang `READY_FOR_TEST_CODE` không.

## CHG-20261029-031 — AUTH-002 v0.3: kết quả V-A…V-C trên database test cô lập

- Phạm vi: theo cho phép của người dùng, chạy Odoo trên database mới `tp_tanphat_auth002_verify` (cổng 18099, `dbfilter` riêng, actor fixture tổng hợp; không đụng `tp_tanphat_dev`) bằng helper `.local/auth002-verify/` ngoài Git. Kết quả: V-A đạt (mở thẳng `/web/login/totp` sau authenticate, không nhập lại mật khẩu); V-B phân biệt khóa tạm với sai mật khẩu qua `AccessDenied.arguments`; V-C chỉ `en_US`, không `website`/`auth_oauth`, `auth_signup` mở đăng ký/đặt lại mật khẩu. Đặc tả lên v0.3: mục 8.2 kết quả, quy tắc L01, L04 đổi link, L10 chữ tiếng Việt cố định, L11/L12 theo kết quả, thêm G7, D6 (`decision-needed`), câu chữ 6.1 (`proposed`), đối chiếu cổng slice 1 (10.1), rủi ro header khung trang mã và `dbfilter`. Cập nhật roadmap, architecture README, status. Không sửa application code hoặc DECISIONS; không commit/push.
- Kiểm tra: request HTTP thật trên database test (report không chứa secret); dừng Odoo và PostgreSQL, `server.log` không có `ERROR`; validator link/anchor/bảng, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: người dùng chọn D6, duyệt câu chữ 6.1 và chọn có chuyển slice 1 sang `READY_FOR_TEST_CODE` không.

## CHG-20261029-030 — AUTH-002 v0.2: người dùng chốt D1–D5 theo mặc định

- Phạm vi: người dùng trả lời “Chốt mặc định”. Đặc tả AUTH-002 lên v0.2: D1 (a) liên hệ quản trị viên, D2 (a) giữ nhớ thiết bị 2FA của Odoo và chỉ Việt hóa, D3 (a) monogram hiện có, D4 (a) nút bấm sang 2FA nên DEC-012 giữ nguyên, D5 bảng câu chữ mục 6 nguyên văn; L07 chốt chữ tĩnh. Cập nhật roadmap, architecture README, status. Không sửa application code, DECISIONS hoặc runtime; không commit/push.
- Kiểm tra: validator link/anchor/bảng có file đặc tả, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code.
- Next: V-A…V-C trên database test cô lập khi người dùng cho phép runtime test → `READY_FOR_TEST_CODE`.

## CHG-20261029-029 — Đặc tả AUTH-002 hoàn thiện luồng đăng nhập (spec-only)

- Phạm vi: thêm `docs/architecture/TP_AUTH002_LOGIN_SPEC.md` v0.1 theo yêu cầu người dùng làm chỉn chu trang đăng nhập; thêm dòng AUTH-002 vào roadmap, link ở architecture README, cập nhật status. Không sửa application code, OpenAPI, test, DECISIONS hoặc runtime; không commit/push.
- Nội dung: sáu khoảng trống `observed-static` G1–G6 (2FA nhập mật khẩu hai lần, trang native thương hiệu Odoo/tiếng Anh, hủy 2FA rơi ra Odoo, khóa tạm báo nhầm sai mật khẩu, không thông báo hết phiên/đăng xuất, Caps Lock/focus/nhãn ngôn ngữ); yêu cầu L01–L12 (React + addon template đề xuất `tp_web_login`); quyết định D1–D5; kiểm trước V-A…V-C; ca nghiệm thu T01–T12; ràng buộc giữ DEC-012.
- Kiểm tra: validator link/anchor/bảng có thêm file mới, `git diff --check`, workflow finish/check. Không chạy application tests vì không đổi code; chưa start Odoo hay thử tài khoản 2FA.
- Next: người dùng chọn D1–D5 → v0.2 → V-A…V-C trên database test cô lập → `READY_FOR_TEST_CODE` và prompt triển khai.

## CHG-20261029-028 — Sửa liên kết bàn giao re-audit DP-001

- Phạm vi: hai link heading trong `PROJECT_STATUS.md` trỏ sai vì heading audit có hậu tố CHG-027; đổi sang link file. Không đổi discovery, application code, verdict hoặc các cổng.
- Kiểm tra: validator sau CHG-027 phát hiện đúng hai anchor thiếu; đã sửa và chạy lại validator UTF-8, `git diff --check`, workflow finish/check. Kết quả cuối ghi ở handoff CHG-028; không coi checker hash là test link.
- Next: giữ `TECHNICAL_ACCEPTED` cho DP-DISC-v1.1/spec-only; C01 là code batch độc lập khi người dùng giao; không mở Data Lake hay dữ liệu thật.

## CHG-20261029-027 — Audit lại DP-001 correction v1.1

- Phạm vi: audit độc lập bản DP-DISC-v1.1 do Claude bàn giao CHG-026; chỉ ghi verdict vào status/roadmap/báo cáo audit, không sửa discovery, application code, OpenAPI, frontend, scripts, runtime hoặc database; không commit/push.
- Kết luận: `TECHNICAL_ACCEPTED` cho discovery/spec-only, `DESIGN_COMPLETE` đạt ở phạm vi tài liệu chuẩn bị. Bốn finding DP-F01…DP-F04 đã được xử lý: snapshot consistency, ma trận version/hash, source/policy tax basis tách riêng, retry/observation/payload và materialization version. Không còn P1/P2 trong correction. P3 không chặn: RFC implementation cần làm rõ response/attempt khác accepted observation và retry cùng batch khác snapshot mới ở V34.
- Kiểm tra thực chạy: đọc source `_amount_summary`, `_tp_submission_problems`, version guard; kiểm 34 ca V01–V34 duy nhất/đủ dải và đều `NOT_RUN`; validator mở rộng trước ghi audit đạt 28 file, 213 link, 49 anchor, 156 bảng, 0 lỗi/0 cảnh báo; exact snapshot 127 file khớp before/after correction và state CHG-026; `git diff --check` đạt. Kiểm cuối sau ghi audit được báo trong handoff `finish/check`.
- Gate: recommendation `DEFER` vẫn là đề xuất, không là DEC; PoC lake `NOT_APPLICABLE`, O0 UC-01 `NOT_READY`, `REAL_DATA_APPROVAL=BLOCKED`. Không chạy application tests vì spec-only, không start Odoo/PostgreSQL, không đọc hồ sơ thật.
- Next: không cần correction mới cho bốn finding cũ. C01/FND-002 là batch code độc lập có prompt sẵn; nhánh C17/RPT-001 cần use case/owner/công thức/scope và task riêng. Không mở BASE/ký/hiệu lực/thanh toán/grant người thật.

## CHG-20261029-026 — DP-001 correction DP-DISC-v1.1 (spec-only)

- Phạm vi: sửa `docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md` lên DP-DISC-v1.1 theo prompt correction sau audit CHG-024; cập nhật status/roadmap/changelog. Không sửa application code, OpenAPI, frontend, scripts trong Git, ops/config, schema hoặc database; không start/upgrade/seed Odoo; không đọc database/NAS/Excel/filestore/secrets; không PoC/pipeline/bucket/connector; không sửa DECISIONS, báo cáo audit CHG-024 hay kế hoạch chuẩn bị; không commit/push.
- Mapping finding → mục → ca kiểm chứng (tất cả `NOT_RUN`):
  - DP-F01 → 4.4.1, envelope 4.1, 5.1, 6.4, R05, 9.1 → V19, V21, V22, V23. Phân trang tách khỏi tính nhất quán; API hiện tại tối đa `best_effort`; `consistent_proven` chỉ với export materialized có snapshot token không mang quyền hoặc change log đặc tả đủ; quyền đổi giữa trang thì fail closed.
  - DP-F02 → 4.4.2, DC-02, 4.7, R19 → V14, V24, V25, V26, V30, V31. Ma trận version × hash; cùng version khác hash phải đọc xác minh hoặc quarantine; không quyết theo `ingested_at`/`write_date`/thứ tự response; snapshot có thẩm quyền mới thay hiện trạng trong coverage, giữ observation.
  - DP-F03 → F06, 3.3, 4.3, DC-06, 4.7, R08, Q4/Q13 → V02, V03, V04, V17, V27, V28, V29. Lớp nguồn khớp `_amount_summary` (mọi dòng `unknown` vẫn `confirmed` có value; `mixed_basis` chỉ khi nhiều basis); lớp policy `basis_unknown` là proposed và kiểm riêng.
  - DP-F04 → 4.5.1, envelope, DC-06, 4.7, R20 → V12, V15, V32, V33, V34. Tách retry trong batch, observation bất biến theo snapshot và payload content-addressed; materialization gắn snapshot + schema/transform/formula.
- Kiểm tra thực chạy:
  - Exact snapshot `scripts.ai_workflow.snapshot` trước/sau: 127/127 file, digest `056ae25bced60c72acae70507533e78377d8bd8a9839e0bc194027c05bc392ca` không đổi, 0 file thêm/xóa/đổi; bằng chứng `.local/dp001-correction/before.json`, `after.json`, `code_comparison.json`.
  - Docs validator `.local/ctr002a-verify/docs_validation.py` mở rộng `NAMES` tại runtime qua `.local/dp001-correction/run_docs_validation.py` (thêm discovery, audit CHG-024, prompt correction): PASS 28 file, 213 link nội bộ, 49 anchor, 156 bảng, 0 lỗi, 0 cảnh báo. Validator scratch (UTF-8/BOM, fence, cột bảng, link/anchor) trên discovery/status/roadmap/audit/prompt/changelog: 0 lỗi.
  - `git diff --check` đạt; discovery (untracked) không có trailing whitespace.
  - Không chạy application tests vì spec-only; Odoo/PostgreSQL không được khởi động.
- Giới hạn bằng chứng: artifact 119 file của DP-001 không phải exact checker scope; 117 file giao với scope 127 được chứng minh không đổi từ đầu DP-001; 10 file chỉ có trong checker scope không tái chứng minh được trước DP-001 vì digest CHG-022 không còn lưu, không dựng bằng chứng hồi tố. Checker không hash tự động tài liệu architecture/prompt mới.
- Next: phiên chính audit lại DP-DISC-v1.1; verdict CHG-024 giữ nguyên cho v1. `DEFER` vẫn là đề xuất; lake PoC `NOT_APPLICABLE`; O0 UC-01 chưa mở; `REAL_DATA_APPROVAL` `BLOCKED`; C01 độc lập.
## CHG-20261029-025 — Chốt bằng chứng bàn giao audit DP-001

- Phạm vi: hoàn tất bản ghi kiểm chứng tài liệu/audit/prompt của CHG-024; không sửa code/runtime/database và không đổi verdict `NEEDS_FIX`.
- Kiểm tra thực chạy: validator mở rộng bao gồm discovery, báo cáo audit và prompt correction đạt 28 file, 182 link nội bộ, 149 bảng, 0 lỗi; đối chiếu exact snapshot theo `scripts.ai_workflow.snapshot` trước/sau đạt 127 file, 0 file thêm/xóa/đổi; whitespace hai file mới đạt. Báo cáo local tại `.local/dp001-audit/code_comparison.json`. Không chạy application tests vì spec-only.
- Bàn giao: số 26 là kết quả kiểm bộ tài liệu trước khi thêm audit/prompt, số cuối là 28; sửa tham chiếu keyset ở status thành mục 4.4/R05. Không sửa lịch sử discovery để tự đóng finding; không commit/push.
- Next: Claude sửa DP-F01…DP-F04 bằng prompt correction rồi phiên chính audit lại. C01/FND-002 vẫn độc lập; lake PoC không áp dụng và dữ liệu thật vẫn bị chặn.

## CHG-20261029-024 — Audit DP-001 Data Platform discovery

- Phạm vi: audit độc lập tài liệu `docs/architecture/TP_DATA_PLATFORM_DISCOVERY.md`; không sửa application code, OpenAPI, frontend, schema, runtime hoặc database; không tạo Data Lake/connector/bucket/pipeline.
- Kết quả: recommendation `DEFER` có cơ sở, nhưng `DESIGN_COMPLETE=NEEDS_FIX` vì bốn điểm cần sửa: keyset cursor không tự tạo point-in-time snapshot; chưa có rule same-version/different-hash; diễn giải `tax_basis=unknown` không khớp `_amount_summary`; replay/dedup toàn cục có thể làm mất lịch sử A→B→A và bỏ qua `transform_version`.
- Kiểm tra: `scripts/ai_workflow.py check` đạt; exact maintained-code snapshot theo cùng checker là 127 file và không đổi trong lượt audit; docs validator mở rộng cho discovery đạt 26 file, 175 link nội bộ, 147 bảng, 0 lỗi; `git diff --check` đạt; Odoo/PostgreSQL không chạy.
- Bằng chứng: findings tại mục 4.3–4.5, 6.3, 7 của discovery; source `_amount_summary` tại `custom_addons/tp_contract/models/tp_contract_revision.py` xác nhận hành vi tax basis. Bản DP-001 khai báo snapshot 119 file nên không được dùng làm bằng chứng exact scope; audit đã lưu snapshot 127 file ngoài Git tại `.local/dp001-audit/before.json`.
- Next: giao Claude correction tài liệu chỉ cho bốn finding trên, rồi audit lại trước khi chọn UC-01/C17/RPT-001 hoặc bất kỳ PoC nào. `REAL_DATA_APPROVAL` vẫn `BLOCKED`; không mở runtime Data Lake.

## CHG-20261029-023 — DP-001 Data Platform discovery (spec-only)

- Phạm vi: khảo sát source tĩnh và viết tài liệu thiết kế theo prompt DP-001. Không sửa application code, OpenAPI, frontend, scripts runtime hoặc database. Không đọc dữ liệu thật/NAS/Excel/filestore, không tạo `tp_datalake`, không chọn vendor/cloud, không dựng pipeline/bucket/connector và không chạy PoC.
- Đã thêm `TP_DATA_PLATFORM_DISCOVERY.md`:
  - inventory 20 model/dataset và API/DTO, 9 phát hiện ảnh hưởng thiết kế dữ liệu;
  - 9 nguồn tương lai đánh dấu observed/proposed/unknown;
  - ba use case: UC-01 giá trị hợp đồng áp dụng theo project là ưu tiên **đề xuất**, UC-02 sổ hồ sơ là candidate, UC-03 AI tra cứu bị defer;
  - data contract envelope và DC-01…DC-08, quy tắc null/0/âm/unconfirmed/currency, thời gian/version, tombstone/replay, join J1–J7, lineage/reconcile;
  - ma trận quyền/retention theo lớp dữ liệu và theo kênh;
  - so sánh O0 report trong Odoo, analytics-first và lakehouse-lite; CDC/Kafka/Spark `NOT_EVALUATED`; đánh giá outbox/audit không phải change feed;
  - đặc tả kiểm chứng V01–V20 đều `NOT_RUN`, risk/gap R01–R18 và 5 câu hỏi ưu tiên.
- Recommendation: `DEFER` (đề xuất, không phải DEC). `DESIGN_COMPLETE` tự đánh giá đủ để review; PoC lake `NOT_APPLICABLE`; `REAL_DATA_APPROVAL` `BLOCKED` bởi Q2/Q4/Q6/Q8/Q11/Q13/Q14. Kế hoạch chuẩn bị không đổi vì không phát hiện gap buộc sửa. Không có Data Lake nào được triển khai.
- Kiểm tra:
  - Validator scratch trên discovery/status/roadmap/changelog/kế hoạch: UTF-8 không BOM, fence đóng, số cột bảng khớp header, link tương đối và heading anchor tồn tại; 0 lỗi.
  - Snapshot SHA-256 119 file `custom_addons`, `frontend/src`, `frontend/tests`, `contracts` và `scripts` không đổi so với trước khi sửa.
  - `git diff --check` đạt; file mới không có khoảng trắng cuối dòng.
  - Không chạy application tests vì không đổi code; không start/upgrade/seed Odoo. Không commit/push.
- Next: phiên chính audit tài liệu và recommendation. Người dùng chọn use case/KPI owner (Q13) và trả lời các câu hỏi mục 10. Nếu chọn UC-01, giao C17/RPT-001 riêng; không mở analytics store/lake khi chưa có trigger mục 9.1.

## CHG-20261029-022 — Kế hoạch chuẩn bị Data Platform/Data Lake

- Phạm vi: chỉ thiết kế discovery/spec-only; không sửa application code, schema, API, frontend, runtime hoặc database; không chọn nhà cung cấp hay triển khai bucket/connector/pipeline.
- Đã thêm `TP_DATA_PLATFORM_PREPARATION_PLAN.md`: ranh giới Odoo là nguồn sự thật, raw/validated/curated, inventory/use case/data contract, quyền và retention, lựa chọn ingestion, PoC dữ liệu giả, cổng và điều không làm.
- Đã thêm prompt `CLAUDE_DATA_PLATFORM_DISCOVERY.md` cho Claude. Đầu ra bắt buộc gồm source inventory, tối đa ba use case, data contracts, security/retention matrix, analytics-first so với lakehouse-lite, PoC plan, risk/gap và recommendation `DEFER`/`ANALYTICS_FIRST`/`LAKEHOUSE_LITE`.
- Data Lake hiện chỉ là đề xuất; Odoo vẫn là nguồn giao dịch/quyền/trạng thái. Không dùng dữ liệu thật, Excel/NAS/filestore thật hoặc tạo `tp_datalake`. Q2/Q4/Q6/Q8/Q11/Q12/Q13/Q14 tiếp tục là cổng tùy use case.
- Kiểm tra: maintained application code không đổi; kiểm cấu trúc tài liệu dự kiến và `git diff --check`; không chạy application tests vì không đổi code/runtime. Không commit/push.
- Next: giao DP-001 cho Claude nếu muốn khảo sát; phiên chính audit tài liệu rồi mới quyết định có PoC hay không.

## CHG-20261028-021 — Kế hoạch điều phối giai đoạn lập trình

- Phạm vi: chỉ lập kế hoạch và tài liệu điều phối; không sửa application code, schema, API, frontend, runtime hoặc database.
- Đã tạo `docs/architecture/TP_CODE_EXECUTION_MASTER_PLAN.md`: bốn làn maintenance/tính năng test/pilot/operations; C00–C17 theo G0–G7, đầu vào/kết quả/test từng batch và pilot draft-review giới hạn trước các module downstream. Inbox là feature mới, không gộp maintenance.
- Đã thêm `AI_COORDINATION_WORKFLOW.md` và prompt C01/FND-002: môi trường test live/race tái lập được, không phụ thuộc helper riêng `.local`. Phiên chính giữ vai trò phân tích, tổng hợp ý tưởng, review/test và phát correction/next prompt; Claude code theo task được giao. DEC-022 ghi nhận phương thức làm việc người dùng đã chỉ định; không chốt thêm quy chế nghiệp vụ.
- Kiểm tra: start checkpoint trước tài liệu; kiểm link/bảng/fence và maintained source so checkpoint; `git diff --check`, `finish/check` ở cuối batch. Không chạy application tests vì không đổi code; kết quả 79/22/3/2 là lịch sử CHG-020, không nhận là mới chạy. Q2-A/Q2-B, bundle thực tế, owner/evidence/sign-off vẫn mở.
- Next: người dùng có thể giao prompt C01 cho Claude; phiên chính audit kết quả và phát prompt sửa hoặc C02 khi scope đủ. Song song chốt cổng pilot. Không mở BASE/legal/payment/grant người thật, không commit/push trong lượt này.

## CHG-20261028-020 — Hoàn tất technical acceptance CTR-002a.1 trên test

- Phạm vi: maintenance của CTR-002a-P1 theo DEC-020/DEC-021. Sửa validation V01/V02, chặn self-review ở reviewer picker/submit/resubmit/return pending cũ, thêm HTTP regression và kiểm tích hợp live trên instance test cô lập. Không thêm state, capability, action nghiệp vụ hoặc quyền người thật.
- Backend/API: enum sai kiểu trả `400 invalid_request`; currency blank/whitespace/null trả 400, unknown currency đúng kiểu trả `422 unknown_currency`; self-review trả `422 reviewer_ineligible`; giữ request ID, rollback, version, idempotency, audit/outbox và lịch sử bất biến. OpenAPI sửa mô tả YAML lỗi inline và TypeScript types được sinh lại.
- Frontend/test: live spec opt-in dùng dữ liệu giả, database `tp_tanphat_ctr002a_verify`, origin `127.0.0.1:18089`; flow create → edit → submit → return → rework → edit → resubmit và race hai HTTP session độc lập.
- Kiểm tra: Odoo `tp_tanphat_test` **0 failed, 0 error(s) of 79 tests**; Ruff, OpenAPI validator, api:types, typecheck, build đạt; Vitest 22; mock E2E 3; live E2E 2. Race khác key `200 + 409 stale_version`, cùng key `200 + 200 replay`; mỗi trường hợp version/audit/outbox/idempotency tăng đúng một lần. Log/report nằm trong `.local/`, ngoài Git. INFO filestore GC `WinError 5` vẫn còn trên Windows.
- Bàn giao: cập nhật PROJECT_STATUS, ROADMAP, readiness/gate, workflow KD và frontend README; readiness 7.1.6 đánh dấu technical acceptance **chỉ cho test fixture**. Q2-A/Q2-B, bundle thực tế, owner/evidence/sign-off, pilot và người dùng thật vẫn pending. BASE approval, ký, hiệu lực, thanh toán, giao khoán/nghiệm thu và grant thật chưa mở. Không commit/push.

## CHG-20261028-019 — Đối chiếu lần cuối cổng test và pilot

- Phạm vi: hiệu chỉnh bàn giao/tài liệu sau CHG-018; không sửa code ứng dụng, runtime, database hoặc quyết định nghiệp vụ mới.
- Đã làm: đồng bộ `Next action` ở cuối PROJECT_STATUS với phần đầu, thêm self-review vào backlog; bỏ yêu cầu Q2/hồ sơ thật trước maintenance test và giữ chúng trước pilot. Sửa tham chiếu mục trong gate và câu chữ để công nhận phạm vi thiết kế người dùng đã giao AI ở DEC-021.
- Kiểm tra: validator tài liệu BIZ-002 và gate (liên kết, heading, bảng, fence, source snapshot), `git diff --check`, workflow `finish/check`; không chạy test ứng dụng vì chỉ tài liệu. Bộ kiểm scratch được cập nhật để hiểu mục KD 7.5 và dòng CTR gate accepted chỉ trên test.
- Next: khi được giao lượt code, triển khai CTR-002a.1 theo Ready for Code mục 2.2–2.3; trước pilot còn Q2-A/Q2-B, bundle thực tế và owner/evidence/sign-off.

## CHG-20261028-018 — Chốt chính sách thiết kế giới hạn cho CTR-002a-P1

- Phạm vi: tài liệu/handoff, theo việc người dùng giao AI tự phân tích và quyết định hợp lý; không sửa source, runtime hoặc database.
- Quyết định DEC-021: preparer KD có assignment được draft/edit/submit; commercial reviewer phải khác người gửi ở từng submission/resubmit; vì review có kiểm tra số tiền nên sender/reviewer cần `financial_read`, còn sửa tiền cần thêm `financial_draft_edit`. Không suy quyền từ chức danh; không mở legal/BASE/payment/grant người thật.
- Đã cập nhật: cổng Ready for Code phân biệt maintenance test-slice với implementation/pilot; readiness mục 7.1.5 ghi policy, giới hạn và đề xuất partner/project picker/amount; status/roadmap/decision/changelog đồng bộ. Self-review backend/picker là maintenance cần làm; V01/V02 vẫn mở.
- Phân loại: đây là **AI-design accepted for CTR-002a test**, không phải bổ nhiệm Q2-A/Q2-B, quy tắc bốn mắt toàn công ty hay thẩm quyền ký pháp lý. Q2, bundle thực tế, owner/evidence và traceability của nghiệp vụ thật vẫn là cổng.
- Kiểm tra: link/bảng/fence/handoff và `git diff --check`; application source/runtime/database không đổi; không chạy app tests vì chỉ tài liệu.
- Next: khi người dùng giao code kỹ thuật, thực hiện maintenance CTR-002a.1 (V01/V02/self-review/HTTP/live/race) đúng handoff 2.2–2.3; Q2/owner/evidence/bundle thực tế tiếp tục là cổng trước pilot/real-users.
- Rà soát lại cổng: RFC-02/Q2 và RFC-06 bundle thực tế được deferred cho pilot/real-users; CTR-002a-test-maintenance có handoff/traceability riêng trong `TP_READY_FOR_CODE_GATE.md` mục 2.2–2.3. V02 chốt blank currency 400, unknown currency 422; pending tự gán cũ bị chặn return mà không sửa lịch sử. Workflow KD đồng bộ DEC-021, reason bắt buộc/issue optional. Không hỏi lại DEC-021; chưa có lệnh code trong lượt này.
## CHG-20261028-017 — Cổng Ready for Code theo yêu cầu chuẩn bị nghiệp vụ trước lập trình

- Phạm vi: chỉ tài liệu và handoff; người dùng yêu cầu kiểm tra/chuẩn bị rõ để lúc code chỉ triển khai nghiệp vụ đã chốt. Không sửa source, runtime/database hoặc xử lý V01/V02 trong lượt này.
- Đã làm: thêm `TP_READY_FOR_CODE_GATE.md` với RFC-01…10: scope, Q2/RACI, state/action, data/validation, record/field/file/export, bundle thực tế, UI, API, traceability/acceptance và gap/sign-off; phân biệt phần AI tự chuẩn bị với phần công ty phải cung cấp/xác nhận. Status chuyển ưu tiên sang chuẩn bị/nghiệm thu, không tự tiếp tục code kỹ thuật.
- Trạng thái: TP Contracts chưa Ready for Code theo cổng nghiệp vụ; Q2 và bundle thực tế chưa đạt, owner/traceability còn thiếu. CTR-002a code trên test giữ nguyên; test xanh không thay xác nhận công ty. Hai lỗi validation vẫn mở.
- Kiểm tra: kiểm link/bảng/nội dung và `git diff --check`; maintained code không đổi; handoff `finish/check`. Không chạy lại application tests vì chỉ tài liệu.
- Next: scope TP Contracts + Q2-A, thu thập hồ sơ khử dữ liệu, hoàn thiện từng RFC và ghi kết luận; chỉ mở code sau owner/người dùng xác nhận cổng của slice.
## CHG-20261028-016 — Review CTR-002a, tái kiểm test và ghi hai lỗi validation

- Phạm vi: review theo yêu cầu người dùng; cập nhật status/readiness/roadmap/changelog và handoff, không sửa code ứng dụng hoặc mở slice mới. Baseline HEAD `95bfc3f4`, working tree sạch, checker CHG-015 đạt; không commit/push/fetch.
- Source: đúng chuỗi draft/phụ lục nháp/edit/submit/return/rework/resubmit, backend kiểm capability/company/project/department/state/version/idempotency, snapshot/audit/outbox; không thấy bypass quyền hoặc action BASE/legal/payment ngoài allowlist trong phạm vi review.
- Findings P2: (1) `_choice` thiếu kiểm kiểu trước lookup frozenset, JSON list/object ở contract_type/tax_basis gây TypeError; (2) currency whitespace được parse thành None nhưng `_tp_currency` gọi `.upper()`, gây AttributeError. Đã tái hiện bằng stateless AST probe lấy hàm source, không gửi HTTP hoặc ghi DB; controller không map hai exception thành ContractWorkflowError/400/422. Hai lỗi **chưa sửa** và bộ test xanh chưa bao phủ; ghi reproduction/tiêu chí regression tại readiness 7.1.4.
- Kiểm thực chạy: Odoo `dev.ps1 test` trên `tp_tanphat_test` báo **0 failed, 0 error(s) of 72 tests**; frontend typecheck, Vitest 22, build (`VITE_ODOO_DATABASE=tp_tanphat_test`), Playwright workflow 3 bằng mock API và Ruff `custom_addons scripts/dev.py scripts/check_contract.py` đạt. Không kiểm UI với Odoo live, không test race song song mới; vẫn có INFO filestore GC `WinError 5`.
- Runtime: Odoo/PostgreSQL ban đầu dừng; test khởi động PostgreSQL, đã stop/status cả hai dừng lại. Không upgrade/seed dev, đổi credential hoặc cấp grant người dùng thật. Maintained code không sửa; docs được kiểm link/bảng và handoff riêng trước finish/check.
- Nghiệp vụ: Q2-A/Q2-B và B01–B03 vẫn proposed/mô phỏng, chưa có xác nhận công ty hoặc bundle thực tế đủ điều kiện. DEC-020 chỉ mở phát triển test; không thay bằng chấp thuận pilot.
- Next: CTR-002a.1 sửa validation + HTTP regression rồi kiểm UI→API→Odoo thật trên test riêng; song song chốt Q2-A/Q2-B và hồ sơ thực tế khử dữ liệu. Chưa mở review_complete, BASE, ký, hiệu lực, thanh toán hoặc grant người thật.

## CHG-20261028-015 — Commit và push BIZ-002 và CTR-002a

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `02c9e18a` gồm tài liệu BIZ-002 (CHG-009..013) ở trạng thái trước CHG-014; `a2f29f2e` gồm CTR-002a (CHG-014). Stage theo từng đường dẫn, không `git add .`; status/roadmap ghi hash; push `main` lên `origin` trong cùng lượt.
- Kiểm tra: dựng lại file dùng chung bằng cách đảo chỉnh sửa CHG-014, 0 lỗi, `frontend/README.md` trùng HEAD cũ; link/bảng tài liệu của `02c9e18a` đạt; `git diff --cached --check` của `a2f29f2e` đạt; sau `a2f29f2e` working tree sạch, `ai_workflow.py check` đạt.
- Giới hạn: `02c9e18a` giữ `AI_WORKFLOW_STATE.json` của CHG-008 (state CHG-013 bị `finish` CHG-014 ghi đè trước khi commit) nên checker tại commit đó lệch. `git diff --check` của commit đó báo hai dấu cách xuống dòng Markdown và dòng trống cuối file trong tài liệu BIZ-002, giữ nguyên. Không chạy lại test ứng dụng vì không đổi code.
- Next: người dùng review nghiệp vụ CTR-002a; Q2-A/Q2-B và bundle thực tế trước pilot.

## CHG-20261028-014 — CTR-002a: draft → gửi rà soát → trả lại → sửa → gửi lại (chỉ test)

- Phạm vi: code CTR-002a-P1 theo DEC-020, chỉ trên `tp_tanphat_test` với dữ liệu giả và actor fixture. Không upgrade/seed `tp_tanphat_dev`, không cấp grant cho người dùng thật, không đổi credential. Ngoài phạm vi và vẫn đóng: complete_review, cancel revision, record/verify BASE, chữ ký/thẩm quyền ký, hiệu lực, giao khoán/nghiệm thu/thanh toán, quản trị grant người dùng thật.
- Model/security (`tp_contract` 20.0.1.1.0, `tp_project`): `tp.project.grant` thêm capability `financial.draft_edit`, `contract.draft_edit`, `contract.submit`, `contract.review_commercial` theo project + phòng ban (`financial.read` giữ theo project); `tp.contract` thêm `department_id` lấy từ phòng chủ trì project và `aggregate_version` khóa `FOR UPDATE`. Model mới `tp.contract.submission` (S1/S2 bất biến, metadata snapshot + hash), `tp.contract.submission.amount` (snapshot tiền tách riêng, ACL như amount CTR-001), `tp.contract.audit` (append-only), `tp.contract.outbox` (một event/người nhận, retry giữ event), `tp.contract.idempotency`. Guard ORM chặn ghi state/version/BASE/legal ngoài workflow, sửa nội dung đã gửi, thay/xóa binary S1 qua `tp.contract.document` và `ir.attachment`. Migration post-migrate gán phòng chủ trì project cho hợp đồng cũ; project chưa có phòng chủ trì thì action trả `scope_incomplete`.
- Action T1–T6: `create_draft`, `create_amendment` (draft phụ lục, mang phạm vi bản trước), `edit_draft`, `submit_review` (draft → `in_review`, reviewer phải có assignment + capability trong cùng project/phòng), `return_review` (`in_review` → `returned`, lý do bắt buộc, issue theo dòng), `begin_rework` (`returned` → `draft`, giữ S1). Mỗi action một transaction: scope/capability kiểm lại, `expected_version`, idempotency theo actor + action + object + fingerprint (gồm version), audit + outbox; replay trả kết quả cũ sau khi kiểm lại quyền; khác payload 409.
- API (`tp_api`, `tp_planning_api`): `GET /contracts/{id}/reviewers`, `POST /contracts`, `POST /contracts/{id}/amendments`, `PATCH /contracts/{id}/revisions/{rid}`, `POST …/submit|return|rework`. Ghi bắt buộc Fetch Metadata/Origin same-origin, `X-CSRF-Token` gắn session, JSON object, `Idempotency-Key`; lỗi 400/401/403/404/409/415/422 có code và `request_id`, `no-store`. DTO thêm `version`, `allowed_actions`, `working_revision_id`, `submissions`; tiền vẫn decimal string và chỉ khi có `financial_read`. OpenAPI cập nhật trước frontend, types sinh lại.
- Frontend: form tạo hợp đồng nháp và phụ lục nháp; trình sửa bản nháp (header, revision, dòng phạm vi; cột tiền chỉ khi có `financial_read` + `financial_draft_edit`, chỉ gửi số tiền đã sửa, chưa xác nhận gửi `null`); gửi rà soát chọn reviewer từ API, tóm tắt sửa bắt buộc từ lần gửi thứ hai; trả lại có lý do và issue theo dòng; mở lại để sửa; lịch sử các lần gửi. Nút lấy từ `allowed_actions`; mỗi intent giữ một Idempotency-Key khi retry lỗi mạng/5xx; 409 stale hiện “Tải lại bản mới nhất”.
- Test: Odoo `dev.py test` trên `tp_tanphat_test` **0 failed, 0 error(s) of 72 tests** (16 test workflow ORM + 3 HttpCase: T-P01, T-N01…T-N09, cùng regression CTR-001); Ruff `tp_api tp_contract tp_planning_api tp_project` đạt; `npm run api:types` + typecheck đạt; Vitest 22 đạt; build với `VITE_ODOO_DATABASE=tp_tanphat_test` đạt; Playwright `contract-workflow.spec.ts` 3 đạt (mock `/api/v1/**`, không Odoo/DB). Không có race song song thật; UI chưa chạy với Odoo live.
- Giới hạn: một grant hiệu lực cho mỗi (project, user, capability); đổi phòng chủ trì project không đổi scope hợp đồng cũ; outbox chưa có cron/kênh gửi/inbox; idempotency chưa có retention; chưa chọn đối tác trong UI; danh sách project ở form tạo lấy 20 bản đầu; xóa dòng có tiền cần quyền sửa tiền. Business acceptance pending; Q2 chặn người dùng thật/pilot.
- Next: người dùng review và quyết định commit; nếu cần xem UI trên Odoo thật thì cần cho phép upgrade database dev hoặc dựng instance test. Q2-A/Q2-B và bundle thực tế vẫn là cổng trước pilot.

## CHG-20261028-013 — Q2-P1, walkthrough mô phỏng và cổng CTR-002a trước code

- Phạm vi: chỉ tài liệu và handoff BIZ-002; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không triển khai CTR-002a, grant admin, record/verify BASE, ký, hiệu lực hay thanh toán.
- Đã làm: bổ sung ma trận Q2-P1 11 hành động tại `TP_KD_WORKFLOW_AND_PERMISSIONS.md` mục 7.4; tách `financial.read`, sửa hồ sơ, xuất dữ liệu và `grant.manage`; tách người quyết định grant/revoke khỏi người thao tác kỹ thuật; giữ cùng/khác người, hạn mức và bốn mắt ở trạng thái chưa xác nhận.
- Bổ sung readiness mục 7.1: ghi phản hồi người dùng cho phép tiếp tục phân tích nhưng chưa bổ nhiệm vai trò; cập nhật Q2-A/Q2-B; inventory nói rõ chưa có bundle thực tế khử dữ liệu đủ chuỗi; chuẩn bị SIM-P1 B01 bình thường, B02 trả–sửa–gửi lại, B03 correction/void và bàn giao/revoke. Đây là mô phỏng logic, không phải UAT/test/nghiệm thu.
- Bổ sung CTR-002a-P1: snapshot vòng gửi bất biến trong revision nháp, rework/resubmit không tạo correction pháp lý; actor fixture/scope; CSRF, optimistic aggregate version, idempotency, transaction/audit/outbox, negative/concurrent/retry cases và tiêu chí cổng. Đối chiếu source tĩnh xác nhận CTR-001 chỉ GET/read, chưa có action ghi/version/audit/idempotency; không mở ACL ghi.
- Cập nhật dictionary/workflow K/design package/evidence/status/roadmap để không gộp state handover với grant, không coi hash bản sao nguồn là hồ sơ thực tế và giữ thứ tự Q2 → bundle → quyết định chuyển code → CTR-002a test. Q1/Q3/Q4/Q6/Q8/Q9–Q14 tiếp tục mở theo cổng.
- Kiểm tra trong lượt: `.local/biz-002/review_q2.py` đạt 19 tài liệu/134 link/104 bảng, 9 link heading, 11 action Q2, 6 dòng log proposed, 19 chặng SIM và 10 phép tính Decimal giả lập. Đối chiếu source tĩnh; 5 hash bản sao S01–S05 khớp manifest, không kiểm NAS hiện hành; maintained code 108 file không đổi so checkpoint; `git diff --check` đạt. Báo cáo `.local/biz-002/q2_review_validation.json` ngoài Git. Không chạy Odoo/frontend/app tests vì chỉ tài liệu; `ai_workflow.py finish/check` ghi handoff sau kiểm nội dung; checker không xác nhận nghiệp vụ.
- Next: chủ nghiệp vụ xác nhận vai trò/căn cứ Q2 và cung cấp 2–3 bundle khử dữ liệu; sau yêu cầu chuyển giai đoạn rõ ràng mới cân nhắc code CTR-002a-P1 trên test.

## CHG-20261028-012 — Kiểm tra lại toàn bộ tài liệu BIZ-002 và giới hạn bằng chứng nguồn

- Phạm vi: kiểm tra tài liệu/handoff; không đổi source ứng dụng, schema, API, database, runtime hoặc quyền. Không có quyết định nghiệp vụ mới.
- Hiệu chỉnh dòng `reported_checks` của handoff CHG-011: bộ kiểm BIZ-001/NAS chưa có báo cáo mới để xác nhận, nên không dùng dòng “passed” đó làm bằng chứng kiểm NAS/Decimal trong lượt này; state mới chỉ ghi các kiểm tra vừa xác minh được.
- Kết quả: 19 tài liệu, 121 link tương đối, 95 bảng có header/fence nhất quán; walkthrough normal/rejected 13 cặp, correction A–M 13 ca, Q1–Q14 đủ trong readiness. Hash năm bản sao nguồn S01–S05 trong `.local/biz-001` khớp registry; lượt này **không** xác nhận hash trực tiếp trên NAS và ghi rõ giới hạn trong `.local/biz-002/review_validation.json` ngoài Git.
- Maintained code vẫn 108 file không đổi; business acceptance pending, nhật ký Q2/bundle/CTR-002a còn `open`. Đây là kiểm tra handoff/tài liệu, không phải UAT hay phê duyệt công ty.
- Next: giữ thứ tự Q2 → 2–3 bundle khử dữ liệu → ghi quyết định/gap → người dùng chọn giai đoạn; chỉ sau đó mới xem xét CTR-002a test.

## CHG-20261028-011 — Kiểm tra CTR-001 và chuẩn bị xác nhận BIZ-002 theo Q2

- Phạm vi: review source/quyền/API/test và tài liệu; chỉ sửa readiness, status, roadmap, changelog và state bàn giao. Không phát triển CTR-002a, không thay code ứng dụng, schema/API hoặc credential; không commit/push.
- Kết quả review: chưa phát hiện lỗi chặn trong CTR-001 read slice. BIZ-002 đủ cấu trúc để review nghiệp vụ; chưa có xác nhận công ty, Q1–Q14 vẫn mở. Các giới hạn đã ghi giữ nguyên: metadata BASE text tự do có thể chứa tiền, grant thiếu ledger revoke/delegation bất biến, chưa có capability export tiền riêng; phải xử lý trước pilot dữ liệu thật.
- Đã bổ sung: nhật ký quyết định/nghiệm thu tại readiness mục 7.1, có scope/môi trường, RACI/người xác nhận bằng mã nội bộ, kết luận/trạng thái, evidence/hash, ngày/phiên bản và gap/next action. Các dòng Q2/bundle/CTR-002a đều `open`; không điền giả tên, bằng chứng hoặc chấp thuận. Mục 7.2 tách kiểm tra kỹ thuật khỏi nghiệm thu và quyết định mở code. Làm rõ thứ tự Q2 → 2–3 bundle → ghi kết luận → quyết định người dùng → CTR-002a test; không chờ đóng đồng loạt Q1–Q14.
- Kiểm tra source thực chạy: frontend typecheck đạt; Vitest 14 tests đạt; Ruff `custom_addons scripts/dev.py scripts/check_contract.py` đạt; `dev.ps1 test` trên `tp_tanphat_test` báo **0 failed, 0 error(s) of 53 tests**. Còn INFO filestore GC `WinError 5` như đã ghi. Không chạy lại build/E2E; không nhận kết quả lịch sử thành mới.
- Runtime: ban đầu Odoo/PostgreSQL dừng; test khởi động PostgreSQL, dùng DB test riêng; đã dừng và kiểm status cả hai dừng sau kiểm tra. Không upgrade/seed database dev. Maintained code được đối chiếu checkpoint cuối lượt; không thay source trong batch này.
- Kiểm tài liệu/handoff: kết quả kiểm link/bảng/fence/bao phủ, `git diff --check` và `ai_workflow.py finish/check` được ghi trong state bàn giao sau khi hoàn tất kiểm tra; checker không thay bằng chứng nghiệp vụ.
- Next: Q2 trách nhiệm/quyền Ban KD và walkthrough hợp đồng với hồ sơ khử dữ liệu, ghi nhật ký; chỉ người dùng quyết định chuyển sang CTR-002a test. Chưa mở action BASE/legal/tiền thật hoặc grant admin.

## CHG-20261028-010 — Đồng bộ state, ngoại lệ và công thức trong gói BIZ-002

- Phạm vi: chỉ tài liệu; không đổi code ứng dụng, schema, API, frontend, runtime, dữ liệu hoặc credential.
- Đã làm: đồng bộ state/transition giữa workflow F–M và dictionary (returned/resubmit, BASE rejected vs verification disputed, acceptance signature, lifecycle); thống nhất mã allocation theo company; bổ sung handover/revoke/restore/share và đường correction; bổ sung công thức kiểm soát hợp đồng, cấp 1/2, khối lượng, payment allocation, tạm ứng, giữ lại, aging/freshness và known-at. Cập nhật readiness walkthrough để dùng basis/case `null`/`0`/unknown đúng nghĩa.
- Quyết định/workflow: vẫn Proposed/Unconfirmed theo BIZ-002; BASE official, chữ ký/hiệu lực/posting tách lớp; Q1–Q14 chưa đóng. Không biến công thức giả lập thành công thức tài chính doanh nghiệp hoặc mở action.
- Kiểm tra: `git diff --check` đạt; validation riêng đạt 19 tài liệu duy nhất, 119 link tương đối, 94 bảng có header/fence đúng, 13 cặp walkthrough normal/rejected và 13 ca correction A–M, Q1–Q14 có đầu mối/cổng; 10 phép tính Decimal kiểm công thức bổ sung đạt. `.local/biz-001/verify_baseline.py` đạt (5 hash khớp, 48 link/28 bảng baseline, 10 Decimal checks riêng, 108 file maintained code không đổi); không chạy Odoo/frontend test vì code/runtime không đổi. Báo cáo kiểm tài liệu `.local/biz-002/validation.json` ngoài Git; không nhận walkthrough là UAT. `ai_workflow.py finish/check` ghi handoff CHG-010.
- Next: chủ nghiệp vụ review bộ BIZ-002 và hồ sơ khử dữ liệu, trả lời Q theo slice; người dùng quyết định khi nào chuyển sang code.

## CHG-20261028-009 — BIZ-002: bộ thiết kế nghiệp vụ toàn công ty trước code

- Phạm vi: chỉ tài liệu/workflow handoff; không đổi `custom_addons`, `frontend`, OpenAPI, database, runtime, credential hoặc Git metadata. Không setup/upgrade/seed và không gửi message sang task khác.
- Đã làm: rà soát khoảng trống và baseline; kiểm hash năm nguồn S01–S05 với `.local/biz-001/manifest.json`; bổ sung [bản đồ A–M/RACI](architecture/TP_ENTERPRISE_PROCESS_MAP.md), [workflow A–E](architecture/TP_PROCESS_WORKFLOWS_A_E.md), [workflow F–M](architecture/TP_PROCESS_WORKFLOWS_F_M.md), [từ điển dữ liệu/ERD/ma trận quyền](architecture/TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md), [tích hợp/KPI/màn hình/API thiết kế](architecture/TP_BIZ002_INTEGRATION_AND_REPORTING.md), [kịch bản/readiness/Q1–Q14](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md) và [chỉ mục/gap analysis](architecture/TP_BIZ002_DESIGN_PACKAGE.md). Cập nhật `TP_BUSINESS_WORKFLOW`, database/source architecture, architecture README, `PROJECT_STATUS`, `ROADMAP`, `DECISIONS`, `AI_CHANGE_WORKFLOW`.
- Phân loại: quyết định người dùng (BASE official, Odoo + React riêng, một DB/môi trường, scope tiền) tách khỏi quan sát E01–E18, đề xuất RACI/capability/transition/KPI và điểm chưa xác nhận Q1–Q14. Ghi rõ grant runtime hiện thiếu ledger revoke/delegation/audit riêng và `financial.export` capability; không tự coi policy mục tiêu là đã enforce.
- Kiểm tra: `scripts/ai_workflow.py start` trước sửa; `.\.venv\Scripts\python.exe .local/biz-001/verify_baseline.py` đạt (5 source hash khớp, 29 link/27 bảng trước sửa, 10 Decimal synthetic checks, 0 cell kế toán thực tế; application/business acceptance tests not run); kiểm tra Markdown link/table/fence/nội dung A–M riêng đạt; `git diff --check` đạt trước finish; Odoo/PostgreSQL status đang listening. Không chạy app tests vì không đổi code/runtime.
- Giới hạn: đây là baseline thiết kế để chủ nghiệp vụ review, chưa là quy chế/UAT/Odoo test. Q1–Q14, 2–3 hồ sơ khử dữ liệu và owner xác nhận còn chờ; CTR-001 read giữ nguyên, CTR-002/PRJ/ALC/STL/FIN/IMP chỉ mở sau người dùng chọn chuyển giai đoạn.
- Next: review BIZ-002 walkthrough A–M, chốt câu hỏi theo slice và hồ sơ đại diện; sau đó người dùng quyết định phạm vi code. Giữ Q2: chỉ superuser cấp grant cho đến khi người cấp/thu hồi và record/verify BASE được xác nhận.

## CHG-20261028-008 — Ánh xạ trạng thái hợp đồng và ghi nhận push

- Phạm vi: tài liệu; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: thêm mục 4.4 trong `TP_KD_WORKFLOW_AND_PERMISSIONS.md` ánh xạ tên trạng thái ở 4.1–4.3 sang field/giá trị trong code (`review_state`, `decision`, `verification_state`, `authority_status`, `signature_status`, `signature_authority_status`, `effectivity_status`, `lifecycle_state`) kèm constraint hiện có; liên kết từ `TP_BUSINESS_WORKFLOW.md`. Status ghi nhận `main` đã push đến `00d4ddc7`.
- Điểm cần chốt cho CTR-002: transition hủy revision (`cancelled` có trong code, 4.1 chưa có); cách confirm_effectivity cập nhật `effectivity_status` và `lifecycle_state` cùng lúc; thứ tự review → BASE reference chưa có constraint ở model.
- Kiểm tra: đối chiếu giá trị với model `tp_contract`, DTO `tp_planning_api` và nhãn frontend; kiểm liên kết Markdown; `git diff --check`; `ai_workflow.py finish/check`.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002.

## CHG-20261028-007 — Commit local AUTH-001, BIZ-001 và CTR-001

- Phạm vi: Git history và tài liệu bàn giao; không đổi model, API, frontend, runtime hoặc database.
- Đã làm: `395be562` gồm login AUTH-001 (CHG-004) và baseline BIZ-001 (CHG-005) ở đúng trạng thái trước CTR-001; `807018b9` gồm CTR-001 (CHG-006). Stage theo từng đường dẫn, không `git add .`; chưa push.
- Kiểm tra: dựng lại file dùng chung bằng cách đảo chỉnh sửa CTR-001, áp lại khớp 18/18 file; export `395be562` typecheck đạt, Vitest 10 đạt; sau `807018b9` `git diff HEAD` rỗng, `ai_workflow.py check` đạt; quét diff không có credential/dữ liệu thật.
- Giới hạn: `395be562` giữ `AI_WORKFLOW_STATE.json` của `03702d24` nên checker tại commit đó báo lệch; không chạy lại Odoo tests cho commit này vì không đổi backend. Hai tài liệu TP_KD có xuống dòng Markdown bằng hai dấu cách như các tài liệu sẵn có.
- Next: push khi người dùng yêu cầu; nghiệm thu BIZ-001/CTR-001 và chốt Q2.

## CHG-20261028-006 — CTR-001: TP Contracts read slice

- Phạm vi: addon mới `tp_contract`, grant `financial_read` trong `tp_project`, API đọc trong `tp_planning_api`, OpenAPI, frontend TP Contracts, dev seed/smoke/checker và tài liệu. Không sửa `odoo/`/`addons/`, không mở API ghi/duyệt/ký/xác nhận hiệu lực, không đổi xác thực.
- Model: `tp.contract`, `tp.contract.revision`, `tp.contract.line`, `tp.contract.line.amount`, `tp.approval.reference`, `tp.approval.reference.amount`, `tp.contract.document`; review, chữ ký, thẩm quyền ký, hiệu lực và kết quả BASE là các trường riêng; snapshot theo ngày hiệu lực thay thế bản trước; tổng chỉ có giá trị khi mọi dòng đã xác nhận và cùng cơ sở thuế.
- Quyền: đọc metadata theo assignment project + company; số tiền và tài liệu `financial` thêm điều kiện grant `tp.project.grant` còn hiệu lực cho đúng project. Grant có lý do/thời hạn/thu hồi, không tự cấp, chỉ superuser tạo khi Q2 chưa chốt. Không group nào được ghi dữ liệu hợp đồng qua ORM/RPC.
- API: `GET /api/v1/contracts`, `/contracts/{id}?as_of=`, `/contracts/{id}/revisions/{revision_id}`, `/contracts/{id}/documents/{document_id}/content`; 404 ngoài scope, 400 `invalid_request`, `no-store`, bỏ field tiền khi thiếu grant.
- Frontend: route `/contracts`, chi tiết hợp đồng, trang phạm vi revision; nhãn BASE đã/chưa xác minh, ghi chú BASE approved không đồng nghĩa đã ký/hiệu lực, định dạng tiền từ decimal string, mobile 390px.
- Dữ liệu dev: ba hợp đồng giả lập `HD-DEV-001/002/003` và grant dev cho admin trên DEV-001. Không có hồ sơ thật.
- Quyết định: DEC-017.
- Kiểm thử thực chạy: Odoo `0 failed, 0 error(s) of 53 tests` (contract access 15, model 16, contracts API 12, project 10); upgrade + smoke đạt; `check_contract.py --live` đạt; Ruff đạt; frontend typecheck đạt, Vitest 14 đạt, build đạt, Playwright 11 đạt; `git diff --check` đạt.
- Giới hạn: Q1–Q3 còn mở; chưa có quản trị grant ngoài superuser; văn bản tự do không được quét số tiền; chưa có view Odoo native cho hợp đồng; exit code `dev.py test` không đáng tin. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: nghiệm thu BIZ-001/CTR-001 và chốt Q2; CTR-002 draft/submit/return trên test.

## CHG-20261028-005 — BIZ-001: baseline workflow và ma trận quyền Ban Kinh doanh

- Phạm vi: phân tích năm nguồn S01–S05 và cập nhật tài liệu workflow/database/status/roadmap/decision; không sửa model, API, frontend, runtime hoặc import dữ liệu.
- Đã chốt theo yêu cầu người dùng: BASE là nơi phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận kết quả; quyền xem tiền mặc định cho người quản trị dự án đúng scope, Trưởng ban, QT-TC và lãnh đạo, hỗ trợ cần cấp riêng; hạn mức ký/duyệt chưa biết nên không đặt giả.
- Đã làm rõ: review nội bộ, BASE decision/evidence verification, chữ ký/hiệu lực pháp lý, revision snapshot và trạng thái thực hiện là các lớp riêng; contract/production/acceptance/invoice/cash/retention là domain record riêng; khoán cấp 2 không cộng trùng cấp 1; nhãn “GT phải xuất hóa đơn” trong mẫu được map là invoice issued thực tế.
- Tài liệu: `docs/architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md`, `docs/architecture/TP_KD_EVIDENCE_AND_ACCEPTANCE.md`; cập nhật `TP_BUSINESS_WORKFLOW.md`, `TP_DATABASE_DESIGN.md`, `TP_PLATFORM_SOURCE_STRUCTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `PROJECT_STATUS.md` và architecture index.
- Kiểm tra: đọc/đối chiếu source snapshot và hash manifest; hash bản NAS hiện tại vẫn khớp cả 5 source; đọc các range S03/S05 liên quan, xem trang phân công S02; `verify_baseline.py` đạt 27 link tương đối, 26 bảng Markdown nhất quán, 0 cell dữ liệu kế toán thực tế trong bản S05 đọc, 10 phép tính Decimal giả lập; `git diff --check` đạt. Không chạy macro/external link và không chạy bộ ứng dụng vì lượt này chỉ thay tài liệu.
- Giới hạn: chưa có 2–3 hồ sơ thật đã khử dữ liệu, văn bản hạn mức/bốn mắt/ủy quyền, BASE ID/evidence chuẩn hoặc feed kế toán thực tế; state/capability/ca nghiệm thu là thiết kế, chưa chạy Odoo. Chưa commit/push; giữ nguyên thay đổi login AUTH-001.
- Next: `CTR-001` read-only contract/revision/line + approval reference, field/attachment security và negative tests bằng dữ liệu giả; thu thập Q1–Q3 trước action ghi/chốt pháp lý.

## CHG-20261028-004 — Giao diện đăng nhập riêng TANPHAT ONE

- Phạm vi: `frontend/src/features/auth`, transport session frontend, visual design, E2E và tài liệu; không sửa Odoo core, model nghiệp vụ hoặc database.
- Đã thay đổi: `/work/` hiển thị cổng login React hai cột với minh họa cầu dây văng SVG, Be Vietnam Pro, hover/focus, animation vẽ cáp, reduced-motion, responsive mobile, hiện/ẩn mật khẩu, trạng thái pending/error và hướng dẫn hỗ trợ. Form gọi `/web/session/authenticate` same-origin, sau đó đọc `/api/v1/me`; không lưu password/token vào storage. MFA trả `uid: null` được giữ là bước xác thực bổ sung và có link native Odoo với redirect hiện tại.
- Quyết định: DEC-012. Database login không hardcode production: dev có fallback `tp_tanphat_dev`, production build yêu cầu `VITE_ODOO_DATABASE` khớp dbfilter.
- Kiểm thử thực chạy: `npm.cmd run typecheck --prefix frontend` đạt; `npm.cmd test --prefix frontend` đạt 10 tests; `VITE_ODOO_DATABASE=tp_tanphat_dev npm.cmd run build --prefix frontend` đạt; `npm.cmd run test:e2e --prefix frontend` đạt 8 tests (login, invalid credential, MFA handoff, gateway error, deep link, responsive, reduced-motion, permission/session regression); `git diff --check` đạt.
- Giới hạn: build production cần CI/release cung cấp `VITE_ODOO_DATABASE`; MFA code/passkey vẫn do native Odoo xử lý. Chưa đổi logo/branding ở native `/web/login`.
- Next: quay lại BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt state/role matrix.

## CHG-20261028-003 — OPS-001: backup và phục hồi dev cô lập

- Phạm vi: script backup/restore, hướng dẫn vận hành và bằng chứng thực chạy; không sửa model/API/frontend hoặc seed dữ liệu vào dev.
- Backup: snapshot nhất quán khi tạm dừng Odoo dev 18,95 giây, 314 bảng public, 37 tham chiếu attachment/27 blob, database dump 3.043.333 byte; source archive tại commit `d9e8ccdc`. Backup và credential giới hạn quyền, nằm ngoài Git.
- Kết quả: giải nén source từ backup; restore vào cluster mới cổng 55442, Odoo 18089, database/filestore riêng; 314 bảng/fingerprint và 37 attachment khớp trước neutralize; probe 2 attachment chỉ tồn tại ở bản sao; cluster/Odoo cô lập đã dừng; dev gốc smoke lại đạt.
- Kiểm thử tooling/tích hợp: 21 unit tests đạt, Ruff đạt; anonymous 401, planner/admin login + `/me` + list/detail DTO + query validation, 37 lượt tải tệp khớp SHA1/size và kiểm attachment theo scope đạt. Báo cáo cuối ở `.local/ops-001/rehearsals/20261028T064405723351Z/report.json`.
- Hướng dẫn: `ops/runbooks/BACKUP_RESTORE.md`. Chưa có lịch backup, backup ngoài máy hoặc phục hồi trên host khác.
- Next: BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt ma trận quyền/trạng thái.

## CHG-20261028-002 — Chốt baseline Git và publish handoff

- Phạm vi: kiểm chứng local `main` với `origin/main`, rà soát các file handoff đang chờ commit và chuẩn bị publish toàn bộ thay đổi hiện tại.
- Đã thay đổi: cập nhật trạng thái GIT-001 đã hoàn tất, chuyển Next action sang OPS-001, chốt DEC-010 và cập nhật roadmap; không sửa model/API/giao diện/database.
- Kiểm tra: `git fetch --prune origin`; local/remote cùng ở `a25a0182`; `git status`; kiểm tra credential-like patterns trong file dự kiến commit; checker trước lượt đạt.
- Publish: commit/push lên `origin/main` sẽ là baseline handoff mới của source hiện tại; xác nhận sau push bằng `git status` và `git rev-list`.
- Giới hạn: chưa diễn tập backup/restore, chưa xác minh production hoặc khôi phục hai commit ID cũ không tồn tại.
- Next: OPS-001.

## CHG-20261028-001 — AI handoff và workflow nghiệp vụ

- Phạm vi: tạo `AGENTS.md`, trạng thái dự án, quy trình bàn giao, workflow nghiệp vụ, changelog và checker local.
- Đã thay đổi: mọi phiên AI có thứ tự đọc bắt buộc; mỗi phiên code phải cập nhật status/changelog; state/role/transition của các phân hệ được phân biệt giữa thiết kế và đã triển khai.
- Kiểm chứng trạng thái: local hiện có baseline `82e9ea27`/`a25a0182`; bổ sung DEC-010 để phiên sau không thực hiện lại phục hồi Git theo ghi chú cũ. Không sửa metadata hoặc tạo commit trong lượt này.
- Kiểm thử: checker unit test 11/11 đạt; Ruff đạt; `git diff --check` đạt; kiểm tra `start`/`finish`/`check` đạt.
- Giới hạn: checker không thay thế Git, review nghiệp vụ, security test hoặc phê duyệt của người dùng.
- Next: xử lý Git baseline, rồi chốt state/role matrix cho TP Projects và TP Contracts.

## 2026-10-28 — Foundation và naming

- **Phạm vi:** Odoo foundation, project access, API v1, React workspace, naming TANPHAT ONE, chín tên phân hệ.
- **Đã có:** `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`; frontend đọc project theo session Odoo.
- **Kiểm thử:** Odoo 10 tests đạt; OpenAPI live đạt; frontend typecheck/build/unit/prototype/E2E đạt; smoke đạt.
- **Quyết định:** một PostgreSQL database cho mỗi môi trường; quyền dùng company/project/assignment; technical addon identifiers giữ ổn định.
- **Giới hạn:** chưa có contracts, allocations, settlements, import hoặc production; Git metadata cần baseline sạch.
- **Next:** chốt state/role matrix và triển khai `tp_contract` read vertical slice.

## Mẫu mục nhập

```text
## CHG-YYYYMMDD-NNN — <tên thay đổi>
- Phạm vi:
- Đã thay đổi:
- Workflow/model/API bị ảnh hưởng:
- Kiểm thử:
- Giới hạn:
- Next:
```
