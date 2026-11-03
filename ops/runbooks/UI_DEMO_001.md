# Runbook — UI-DEMO-001 (TANPHAT ONE native Odoo demo)

## Trạng thái hiện hành — CHG-20261102-012

**02/11/2026 (Asia/Saigon): `RUNTIME_RETIRED_ARCHIVED`.** Người dùng yêu cầu ngừng môi trường UI-DEMO-001/002 cũ. Hai DB `tp_tanphat_demo_ui001` và `tp_tanphat_demo_ui001_test` đã drop; cổng 18109/18119 không còn listener. Không tự chạy lại các lệnh prepare/start/seed/test bên dưới. Phần sau mục phục hồi là runbook lịch sử, không mô tả runtime đang chạy.

Odoo dev **18069 vẫn chạy và đăng nhập được; toàn bộ dữ liệu mới còn nguyên**, Home/tiếng Việt vẫn hoạt động. Không uninstall module trên dev, không xóa source `tp_demo_workspace`, không thay credential, PostgreSQL/roles hoặc backup cũ. Không commit/push.

### Ownership và phạm vi thực hiện

| Tài nguyên | Bằng chứng | Kết quả |
| --- | --- | --- |
| Odoo demo | owner workspace, PID file 22840, child Odoo 22852 dùng đúng odoo-bin/config, listener 18109 thuộc 22852 | Dừng wrapper/Odoo/console con đúng cây process; không dừng dev |
| `tp_tanphat_demo_ui001` | owner.json đăng ký, DB owner token khớp | Archive rồi drop đúng tên |
| `tp_tanphat_demo_ui001_test` | owner.json đăng ký; log khởi tạo 30/10 02:45:07 UTC/config18119; DB create_date 02:45:19; tp_demo_workspace installed, log test PID24712 và filestore khớp | Archive rồi drop đúng tên; không có token vì lệnh test không seed; 18119 đã dừng, không kill process khác |
| `data/` | config trỏ đúng data-dir riêng; chỉ có hai filestore; 53 session demo + 36 session test, 0 file không đọc được; data/addons rỗng; không reparse, không runtime khác dùng chung | Chuyển bản gốc vào archive sau khi kiểm checksum |
| `logs/`, config, credential, owner | đường dẫn từ tooling/config/process và log thực tế | Chuyển vào archive; PID file được stop gỡ |
| screenshots/UI-DEMO-002 evidence | bằng chứng lịch sử cần giữ | Giữ nguyên tại chỗ, hash trước/sau khớp |

Lệnh `Remove-Item -LiteralPath ... -Recurse -Force` bị công cụ từ chối (`blocked by policy`). Đã dùng phương án có thể hoàn tác: PowerShell `Move-Item -LiteralPath` sau kiểm đường dẫn nguồn/đích tuyệt đối và không có reparse. Không chuyển danh sách sang shell khác. Các file runtime không còn tại vị trí cũ nhưng bản gốc còn trong archive, **không tuyên bố đã giải phóng dung lượng đó**. Không có tài nguyên ownership chưa rõ nào bị xóa.

### Bản lưu trữ và kiểm chứng

Đường dẫn ngoài vùng dọn: `C:\TANPHAT ONE\.local\demo-retirement\20261102-ui001\`.

ACL của thư mục chỉ cho user hiện tại, SYSTEM và Administrators. Đây là lưu trữ local ngoài Git, chưa mã hóa/chưa có bản ngoài máy. Không đưa credential hoặc payload vào Git.

- `tp_tanphat_demo_ui001.dump`, `tp_tanphat_demo_ui001_test.dump`: PostgreSQL custom format; có `*.toc.txt`.
- `runtime-data-logs.zip`: toàn bộ data (filestore/assets/session), logs và bản config/metadata cần thiết trong `private/`.
- `private/`: config gốc có credential, credentials.json, owner.json, PID lịch sử; không in nội dung vào chat/log. `retired-originals/`: nguyên bản data/log/config/owner/credential đã chuyển khỏi runtime.
- `source-tp-tooling.zip`: source TP và runtime helpers hiện tại; upstream/runtime Python/PG dùng bản hiện có trên máy, không thay đổi trong lượt này.
- `manifest.json`: SHA-256 18 file; hash manifest `eb49d8b4b85d6e2976cb9fee5f4e645bf2212e5a83dd43c99ede25193151e87c`. `inventory.json`, `archive-evidence.json`, `pre-delete-tree.json` ghi bằng chứng ownership/dump/table/filestore; báo cáo sau dọn nằm riêng và không sửa manifest snapshot.

Hai dump qua `pg_restore --list` và đọc/giải nén toàn nội dung ra SQL vào null, không thực thi SQL. ZIP CRC và SHA-256 từng file so với nguồn đã dừng đạt; 192/77 attachment tham chiếu có SHA-1/kích thước đúng (62/70 blob duy nhất). **Listing, đọc dump và checksum chưa phải diễn tập restore**. Bản dump được lấy sau khi dừng đúng demo; dev không bị dừng.

Baseline dev gồm fingerprint 538 bảng, toàn bộ ID các bảng nghiệp vụ, 188 XML ID binding fixture, 239 blob/244 tham chiếu attachment, config/credential/Git/source và catalog DB/roles. Sau dọn 534 bảng giống hệt; chỉ login/device log (+7 mỗi bảng), bus (+68) và mail_presence (2 dòng, timestamp) thay đổi do kiểm HTTP/UI. Toàn bộ nghiệp vụ, ACL/rule/nhóm/ngôn ngữ/installed module giống baseline; không mất/trùng fixture. Catalog các DB còn lại giữ cùng OID/owner/config. Giữ dev PID14812/wrapper21996, PostgreSQL PID19028 và runtime test data002.

HTTP admin/planner login/count/lang trước/sau giống nhau; admin vi_VN, planner en_US. UI admin 14/14 màn hình desktop và Home 26/26 kiểm admin/planner × desktop1440/mobile375 đạt, không console error/overflow; đã xem ảnh Home/dashboard. Evidence ở `final-comparison.json`, `ui-admin-1440.json`, `home-check/dev-live-results.json`, ảnh trong `screens/`, `home-check/screens/`. Không chạy suite ứng dụng vì không đổi application code/schema dev.

### Phục hồi bản lưu CHG-20261102-012

Đây là hướng dẫn cho một yêu cầu phục hồi sau này, **chưa thực thi/diễn tập**. Không phục hồi vào dev, không ghi đè database/thư mục/port đang có.

1. Kiểm manifest SHA-256 bằng `Get-FileHash -LiteralPath 'C:\TANPHAT ONE\.local\demo-retirement\20261102-ui001\manifest.json' -Algorithm SHA256`, đối chiếu hash ở trên. Kiểm toàn snapshot bằng `.\.venv\Scripts\python.exe .local\demo-retirement\20261102-ui001\retire.py verify`. Công cụ này chỉ đọc archive và credential dev hiện có; không tạo/nâng cấp database. Nếu đường dẫn/runtime/secret thay đổi, cập nhật kế hoạch phục hồi riêng và không ghi đè snapshot.
2. Xác nhận PostgreSQL cluster 55432/workspace đúng marker, roles `tp_odoo`/`tp_dev_admin` hiện có; dev18069 tiếp tục chạy. Kiểm **hai tên chính xác** `tp_tanphat_demo_ui001`, `tp_tanphat_demo_ui001_test` đều chưa tồn tại, 18109/18119 trống. Không drop/reset DB đang có để phục hồi và không tạo/đổi role, password hoặc config chung.
3. Từ hai dump trong archive, tạo lần lượt **đúng hai DB đó** `OWNER tp_odoo TEMPLATE template0 ENCODING UTF8`, dùng kết nối quản trị autocommit độc lập (không đặt trong transaction context). Nạp mỗi dump bằng `pg_restore.exe --exit-on-error --host 127.0.0.1 --port 55432 --username tp_dev_admin --dbname <đúng DB tương ứng> <đúng dump tương ứng>`. Dùng bin trong runtime-owner.json và credential hiện có qua môi trường riêng của child process/PGPASSFILE private, không đặt password lên command line/Git. Không `--clean`, không đổi tên thành dev/test khác.
4. Kiểm `.local/ui-demo-001` chỉ còn screenshots; giữ thư mục đó. Khôi phục bằng **copy**, không move bản archive: lấy `retired-originals/data`, `retired-originals/logs`, và `private/odoo.conf`, `private/owner.json`, `private/credentials.json` vào các đường dẫn gốc. Nếu bản gốc thiếu, dùng ZIP đã kiểm: kiểm từng entry không absolute/traversal/reparse, giải nén vào staging riêng rồi đối chiếu SHA-256 trước khi copy. Không chép đè screenshots, không phục hồi `odoo.pid` lịch sử. Config phải vẫn chỉ dùng demo DB/18109/data-dir demo. Nếu shared PostgreSQL password đã đổi, chỉ cập nhật bản config demo mới bằng secret hiện hành, không đổi credential/cluster dev.
5. Đối chiếu từng DB với `archive-evidence.json`: table row hash/count, database UUID, 192/77 attachment SHA-1/kích thước. Demo owner token phải khớp private/owner.json; test token vắng như snapshot, ownership dựa đăng ký và bằng chứng lịch sử. Kiểm data-dir không liên quan dev. Không chạy prepare/seed/test để thay nội dung snapshot.
6. Chỉ khi được giao mở lại demo: `scripts/ui_demo.py start` với source/helper hiện có đã review; không prepare/upgrade. Kiểm PID/config/listener đúng18109, quyền hai actor và neutralized/outgoing/cron off. So baseline dev18069 trước/sau một lần nữa. Ghi kết quả restore thực tế ở batch mới; không coi các bước trên là bằng chứng restore đạt.

## Runbook lịch sử trước khi ngừng

Isolated leadership demo on synthetic data. It shares the local PostgreSQL cluster of the dev runtime
(`.local/postgres`, port 55432) but owns only its own databases, config, data dir, credentials and Odoo process.
It never installs, upgrades or seeds `tp_tanphat_dev` / `tp_tanphat_test`, never changes `MODULES` in
`scripts/dev.py` and never touches the React frontend or the public API.

| Item | Value |
|---|---|
| URL (this machine only) | `http://127.0.0.1:18109/odoo` |
| Database | `tp_tanphat_demo_ui001` (tests: `tp_tanphat_demo_ui001_test`, HTTP 18119) |
| Runtime folder (ignored) | `.local/ui-demo-001/` — `odoo.conf`, `data/`, `logs/`, `owner.json`, `credentials.json`, `odoo.pid`, `screenshots/` |
| Modules | `tp_demo_workspace` and its dependencies only (`tp_project`, `tp_contract`, `project`, `hr`, `crm`) |
| Accounts | `demo.lanhdao` (overview, financial read on 3 projects), `demo.kysu` (one project, no financial read) |

## Commands

```powershell
.\.venv\Scripts\python.exe scripts\ui_demo.py prepare   # create/upgrade DB, seed, neutralize (Odoo must be stopped)
.\.venv\Scripts\python.exe scripts\ui_demo.py start     # start the demo Odoo on 127.0.0.1:18109
.\.venv\Scripts\python.exe scripts\ui_demo.py status    # JSON: URL, PID, port ownership, PostgreSQL
.\.venv\Scripts\python.exe scripts\ui_demo.py stop      # stop only the Odoo process this tool started
.\.venv\Scripts\python.exe scripts\ui_demo.py seed      # re-run fixtures only (idempotent, Odoo stopped)
.\.venv\Scripts\python.exe scripts\ui_demo.py test      # Odoo tests of tp_demo_workspace on the test DB
.\.venv\Scripts\python.exe -m unittest scripts.tests.test_ui_demo   # tool guard tests, no database
```

Credentials: open `.local/ui-demo-001/credentials.json` on this machine (keys `demo.lanhdao`, `demo.kysu`,
`admin`). Do not paste them into chat, tickets or Git. `prepare`/`seed` re-apply the same values.

## Guards

- Database names must start with `tp_tanphat_demo_`; dev, test, restore and system databases are refused.
- `owner.json` records the workspace, a random owner token and the databases the tool created. An existing
  database not listed there, or one tagged with another token (`ir.config_parameter`
  `tp_demo_workspace.owner_token`), is refused. Nothing is ever dropped or reset.
- `start` refuses a port 18109 that is held by any process the tool did not start; `stop` checks that the saved
  PID runs `odoo-bin` with `.local/ui-demo-001/odoo.conf` before terminating it.
- PostgreSQL is started only through `scripts/dev.py`'s ownership-checked `ensure_postgres`; `stop` leaves it
  running because the dev runtime shares it. Stop it with `scripts/dev.py stop` only when the dev Odoo may stop too.

## Outgoing services

- Config: `max_cron_threads = 0`, `list_db = False`, `dbfilter = ^tp_tanphat_demo_ui001$`, bind `127.0.0.1`,
  `smtp_server = 127.0.0.1:9` (closed port).
- After seeding, all crons are deactivated and Odoo's own `neutralize_database` runs (mail servers off,
  webhooks and push keys cleared, neutralized banner on). TP Contracts notifications stay in `tp.contract.outbox`.
- No BASE connection, payment, SMS or webhook is configured. Do not open the firewall or publish the port.

## Before showing it

1. `status` shows `odoo_listening: true` and a PID owned by the tool.
2. Sign in as `demo.lanhdao`: Dashboard KPIs, Projects overview, Contract flow, Finance with amounts.
3. Sign in as `demo.kysu` in a private window: one project, no CRM/Bid, Finance locked, no financial file.
4. The coordinator audits the demo before leadership sees it (status `IMPLEMENTED_PENDING_AUDIT`).

## Navigation from UI-DEMO-002

- Open **TANPHAT ONE – Demo** in the native application switcher. Its header shows
  TANPHAT ONE + Demo; the adjacent **TANPHAT ONE** app still uses its original navigation.
- Desktop: **Tổng quan** opens the dashboard; **Dự án & công việc** opens project,
  survey, design and task screens; **Hợp đồng & hồ sơ** opens contracts, revisions,
  review flow and documents. **Nguồn lực** opens HR and Finance. **Kinh doanh** is
  present only for the business actor; **Đề nghị** opens the BASE illustration.
- **Tất cả phân hệ** opens all permitted existing destinations with Vietnamese names,
  standard TP names, descriptions and illustration labels. Search accepts `hop dong`,
  `contract`, `du an`, `dau thau`, `request`; it searches navigation only. Clear with
  “Xóa tìm kiếm”. Escape closes the dialog and returns focus to the launcher.
- Below 992px use **Phân hệ**. The catalog becomes a scrollable native dialog; the
  mobile app button remains an application switcher. Notifications/account/company
  remain native. Small screens place utilities on their own row to prevent overflow.
- Native breadcrumb, deep links, reload and browser back/forward retain Odoo action
  identity/context. Selecting a menu resets breadcrumbs exactly as native Odoo does;
  the custom navigation does not dispatch a second action to synchronize selection.
- Native JS tests: after authentication visit `/web/tests?filter=tp_demo_workspace`.
  Browser evidence and screenshots: `.local/ui-demo-002/review/` (no secrets in reports).
- CHG-20261030-005 is implemented and remains `IMPLEMENTED_PENDING_AUDIT` after the
  31 October 2026 final checks. See [UI-DEMO-002 handoff](../../docs/demo/UI_DEMO_002_HANDOFF.md)
  for all 17/15 leaf mappings, actual test results, viewport/zoom and screenshot evidence.

## Known native behaviour (not demo data)

- The messaging icon shows the OdooBot welcome chat and the general channel; `project_todo` also creates private
  "Chào mừng" to-dos for each new user (no project, so no TP Tasks KPI counts them).
- The app menu of both demo actors lists two similar names: **"TANPHAT ONE – Demo"** (this addon, all screens A–L,
  the one to present) and **"TANPHAT ONE"** (the existing `tp_core.menu_platform` app with the native TP Projects
  list and Work Item Catalog). The second shows because the demo group implies `tp_core.group_user`, which the
  existing project scope rules require. UI-DEMO-002 changes only the Demo app's work navigation by direct
  user request on 30/10/2026; the application switcher and the other TANPHAT ONE app remain. The other apps
  (Thảo luận, Lịch, Việc cần làm, Liên hệ, Nhân viên, Ứng dụng) come from dependencies; "Ứng dụng" is opened to
  regular users by `base_install_request` and only lets them ask an admin to install an app.
- Demo actors have no `base.group_allow_export`, so Odoo's Export action is refused; the tests also prove that a
  user who had it would still export only rows allowed by the record rules.
- `prepare`/`seed` keep e-mail off: password hashes are stored without the mail module's "password changed" e-mail.
  The first seed of `tp_tanphat_demo_ui001` (before that fix) left 20 `mail.mail` rows in state `exception`; none was
  delivered (closed SMTP port, neutralized server, crons off) and they are left in place, not deleted.
- C1 `DEMO-HD-CAU-01` is a legacy import (`legacy_unverified`, signed/effective recorded), created like the
  synthetic CTR-001 dev seed in `scripts/dev.py`; its lifecycle is set by the fixture, not by a demo actor.
- After a code change, assets are rebuilt only by `stop` → `prepare` → `start`; a running server keeps the old bundle.

## Troubleshooting

| Symptom | Action |
|---|---|
| `Port 18109 is occupied by a process this tool did not start` | Find the other program; do not kill it from this tool |
| `already exists but was not created by the demo tool` | Choose another `tp_tanphat_demo_*` name in a reviewed change; never reuse a foreign DB |
| `Odoo stopped during startup` | Read `.local/ui-demo-001/logs/odoo.log` |
| Install/test failure | Read `.local/ui-demo-001/logs/install.log` or `test.log` |
| Pages stay on the grey skeleton for 10–20 s | The browser window or tab is hidden/throttled; bring it to the front. Server calls take ~0.05 s |
| First page after `start` is slow | Odoo builds the asset bundle on the first request; reload once before presenting |
