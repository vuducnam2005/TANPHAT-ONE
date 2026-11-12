# KD-ACCESS-002 — Acceptance A01–A12

**Hậu kiểm09/11/2026 — CHG-20261109-004: `AUDIT_FAILED_SECURITY_CORRECTION_REQUIRED`.**
A06 chưa đạt:3lỗi native F1–F3 được tái hiện (preview PDF, upload/delete sau nộp,
update chatter trả nội dung bị chặn). Bảng PASS bên dưới giữ nguyên kết quả
tự kiểm tại thời điểm triển khai; không thay kết luận hậu kiểm mới nhất tại
[báo cáo audit](../reviews/KD_ACCESS_002_INDEPENDENT_AUDIT.md).
A04 chưa bao phủ mutation native file/chatter; A12 chỉ xác nhận phạm vi kiểm
dev đã chạy, không chứng minh đã kín toàn bộ quyền. Cần
[correction và hậu kiểm lại](../prompts/CLAUDE_KD_ACCESS_002_SECURITY_CORRECTION.md).

09/11/2026, Asia/Saigon. `IMPLEMENTED_VERIFIED_DEV_WITH_DOCUMENTED_GAPS`.
Kế hoạch A01–A12 đã được ghi trước sửa application source; bảng này cập nhật
kết quả thực. Người dùng trực tiếp giao thực thi và áp dev sau clone/backup,
đồng thời bỏ nhãn “Tan Phat Development” ở navbar. Baseline navbar/login
CHG-20261109-002 đã bàn giao trước khi checkpoint batch003 bắt đầu.

| ID | Actor / thao tác / expected | Trạng thái |
| --- | --- | --- |
| A01 | Inventory5role, provenance/company/groups/assignment/grant, account khác không đổi | PASS —5mapped user;4actor/operator lịch sử giữ nguyên; inventory và preservation |
| A02 | CRM list/detail/search/name_search đúng project và scope trước dự án | PASS —Odoo scope/pre-project/company/đơn vị; browser5vai; không tạo project giả |
| A03 | Năm role tạo/sửa own draft/prepare;4role submit riêng, support bị chặn | PASS —30kiểm native flows, gồm3money wizard; UI và RPC persist;42grant riêng |
| A04 | Wrong owner/state/project/company/context/default/import/copy/batch/archive/unlink bị chặn | PASS —Odoo negative guards, multi-record read/export và fake context; ORM create/write là đường import. Chưa chạy import wizard CSV riêng |
| A05 | Native tiền/read/domain/order/group/export/derived/report/related không leak | PASS —6money/derived field, mixed money grant, NOT/OR/order/aggregate, cached/related descriptor và native report restriction; support không trả0 thay quyền |
| A06 | File/chatter parent scope/phân loại; revoke/expiry/assignment trong phiên mở | PASS —direct URL/RPC/token/public, message body, attachment mutation; revoke/expiry/unassigned trong cùng browser session. Không redaction mọi free text/file |
| A07 | Typed7domain prepare/submit/return/rework/resubmit và ca âm từng role | PASS —275rehearsal assertions toàn vai; rollback rowsets account/quyền khớp. Head review, deputy/lead workflow7domain, planning4domain, support credential prepare |
| A08 | Contract owner/reviewer/self-review/version/reason/tiền giữ guard | PASS —73Odoo contract + hai chuỗi deputy/lead→head→rework/resubmit trong rehearsal |
| A09 | Project/Task đọc; create/WBS scoped chưa có action, không manager | PASS đọc; NOT_IMPLEMENTED tạo/sửa/WBS scoped —giữ reader8/4/4/4/2; [follow-up](../prompts/CLAUDE_KD_SCOPED_PROJECT_TASK_FOLLOWUP.md) |
| A10 | Năm browser session thật desktop/mobile, Tổng quan/Báo cáo/CRM/export/file/account | PASS —clone175checks, native flows30, HOOT11+25test;5context riêng;1440×1000/390×844. Báo cáo hiện dùng lại Tổng quan |
| A11 | Delta idempotent/rollback; backup mới DB+blob+source/config/hash+restore; exact apply | PASS —grant rerun/dev no duplicate; exact rights rollback + full source rollback/reapply clone; backup122file/576table/295reference verified/restore |
| A12 | Dev5role chỉ đọc, preservation/password/TOTP/grant/rowset/blob; label công ty bỏ | PASS —dev1426rights/112browser/4auth;244table/6094baseline rows,282nonasset attachment; chỉ delta mô tả dưới đây |

## Nguồn, môi trường và bằng chứng

- Clone owned `tp_tanphat_kdaccess002_20261109`, HTTP19289/PG55432;
  source/config/filestore riêng. Restore ban đầu576bảng/295reference khớp.
- Dev `tp_tanphat_dev`, HTTP18069/PG55432. Upgrade chỉ `tp_kd_workspace`
 20.0.1.6.0 và `tp_web_home`20.0.1.4.1; login20.0.1.1.0 giữ.17file application/
  regression delta; mọi addon khác bằng snapshot. Không core/legacy frontend.
- Source test=seal=dev kiểm hash toàn cây custom addon; test lần cuối
 `odoo-tests/20261109T040811401536Z`:157/157,0fail/error; Workspace53,
 Contract73, CRM bridge7, Project12, Home12. `final-tests.json`,
 `sealed-source.json`, `sealed-all-source.json` lưu private.
- `clone-audit.json`1426, `clone-rehearsal.json`275, `clone-browser.json`175,
 `native-flows.json`30, `hoot-result.json`11+25test (40+145assertion);
 `dev-audit.json`1426, `dev-browser.json`112, `dev-auth-smoke.json`4.
 Ruff, XML4 và JS syntax kiểm theo delta; `git diff --check` và workflow checker
 thực hiện ở bàn giao. Kết quả checker không thay test nghiệp vụ.
- Evidence private tại [thư mục batch](../../.local/kd-access002/),
 [ảnh trước–sau5vai và ảnh dev](../../.local/kd-access002/comparison/index.html),
 [navbar trước–sau](../../.local/kd-access002/comparison/navbar-before-after.png).
 Năm ảnh Home trước/sau cùng alias/route/viewport; CRM/mobile và luồng ghi có
 ảnh sau riêng vì trước batch chưa được truy cập CRM. Danh tính/login không ở docs.

## Quyền đã áp và dữ liệu giữ

Audit và áp đúng5account. Scope assignment reader giữ8/4/4/4/2; project grant
16/20/20/8/0 giữ nguyên. Opportunity grant0→16/8/8/8/2 (42), typed grant cũ
56/84/84/32/2 giữ nguyên. Một native CRM team,5membership và1group implication
`base.group_allow_export` được thêm; không sales/all-leads/admin/manager.
Native Odoo tự tính `res.users.sale_team_id` từ trống sang team mới cho đúng5user;
journal ghi rõ và rehearsal thu hồi membership trả default team về trống.
Các cột tài khoản còn lại, password/hash/TOTP/passkey, group trực tiếp, company,
phân công, quyền cũ, owner/reviewer và hồ sơ cũ đối chiếu nguyên.
Dấu vết ORM `write_uid/write_date` được tách khỏi so sánh nội dung; cột password,
session policy và toàn bộ các cột nội dung/bảo mật vẫn được đối chiếu.

Trước đây head không có ACL/capability CRM chuyên môn, trong khi guard backend
còn gộp prepare với submit và chưa đủ bảo vệ tiền. Sau sửa, menu/list/form
hiện theo scope; head tự lập/sửa/chuẩn bị/nộp hồ sơ của mình, đọc tiền hiện có,
không sửa nháp người khác hoặc sửa tiền khi thiếu draft-edit.
[Ma trận từng nghiệp vụ](../security/KD_ACCESS_002_ROLE_MATRIX.md) và
[hướng dẫn5vai](KD_ACCESS_002_USER_GUIDE.md) là căn cứ sử dụng.

Backup cuối `.local/kd-access002/backup-pre-apply-20261109T042019Z`:
122file checksum; dump/filestore/source/config; restore576table/295reference.
Trước source apply, rowsets bảo toàn được so lại với backup sau khi dừng riêng
Odoo dev; không writer chen giữa. `preservation-final-result.json` xác nhận
244table/6094dòng baseline ngoài delta, config nguyên,282attachment ngoài assets
nguyên và295reference/116blob unique gốc còn đúng checksum/size. Upgrade chỉ2addon.
`dev-delta.json` journal IDs/private identity; chạy grant lại không nhân quyền.

## Chạy lại và hoàn tác

Các lệnh triển khai đã thực chạy:

```powershell
.\.venv\Scripts\python.exe scripts/kd_access002.py test
.\.venv\Scripts\python.exe scripts/kd_access002.py audit
.\.venv\Scripts\python.exe scripts/kd_access002.py rehearse
.\.venv\Scripts\python.exe scripts/kd_access002.py delta-rehearse
node scripts/kd_access002_flows.cjs
node scripts/kd_access002_ui.cjs clone
node scripts/kd_access002_hoot.cjs
.\.venv\Scripts\python.exe scripts/kd_access002.py seal
.\.venv\Scripts\python.exe scripts/kd_access002.py backup
.\.venv\Scripts\python.exe scripts/kd_access002.py apply --target dev
.\.venv\Scripts\python.exe scripts/kd_access002.py audit --target dev
node scripts/kd_access002_ui.cjs dev
node scripts/kd_access002_auth_smoke.cjs
.\.venv\Scripts\python.exe scripts/kd_access002.py preserve --target dev --label final
```

Apply đầu upgrade/source đạt nhưng pre-source ORM inventory đã nạp registry cũ
trong tiến trình tooling: tạo team thiếu field, transaction rollback,0grant dở.
Đã sửa preflight dùng SELECT, kiểm source/upgrade/zero grant rồi dùng tiến trình
mới `grant --target dev`, đạt42grant và preservation. Không phục hồi DB hoặc
đổi dữ liệu để che lỗi. Journal `apply-result.json` ghi recovery này.
Native browser có lúc trả session-ready/expired trong điều hướng; harness chụp
lỗi và reload cùng session rồi kiểm lại. Test native flow đầu thiếu khách hàng
đúng dự án, selector Save hidden và chờ dropdown đã sửa/chạy lại. Các Odoo fail
trong phát triển giữ log; chỉ157test và các report source cuối dùng làm gate.

Hoàn tác khi cần: đối chiếu source và journal chưa có writer khác, chạy
`python scripts/kd_access002.py rollback --target dev`. Helper kiểm exact source,
thu hồi42grant/team và5membership, bỏ đúng export implication, khôi phục17file
delta từ snapshot, upgrade2addon và start dev. Không restore DB, không xóa user/
hồ sơ hoặc quyền cũ. Source thay đổi sau batch thì helper từ chối; phải phân tách
delta trước. `full-rollback-rehearsal.json` chứng minh rollback/reapply trên clone;
`delta-rehearsal.json` bổ sung kiểm native default team về trống và rowsets exact.

## Giới hạn và bàn giao

Không có chức năng ghi Project/WBS scoped; không gọi phần này hoàn thiện quyền ghi.
CRM file/chatter dùng coarse parent+financial_read, chưa phân loại/redaction mọi
file/free text. Token/public guard của batch áp cho actor scoped hiện tại;
không thu hồi các liên kết công khai đã chia sẻ ngoài hệ thống. Import CSV wizard,
thiết bị thật/Safari và nghiệp vụ nhiều công ty end-to-end chưa kiểm riêng;
cross-company/department backend đã có negative tests. Báo cáo KH-KD còn dùng lại
Tổng quan; trung tâm báo cáo riêng là batch khác.

Spawn audit độc lập không khả dụng do lỗi model kế thừa; đây là tự kiểm kỹ thuật,
không phải audit độc lập/business acceptance/Q2/pilot. Không BASE/ký/hiệu lực/
posting/paid/grant-admin mới. Không commit/push. Clone19289 dừng; dev18069 và
PostgreSQL55432 tiếp tục chạy; DB/source/evidence clone giữ để tái kiểm.
