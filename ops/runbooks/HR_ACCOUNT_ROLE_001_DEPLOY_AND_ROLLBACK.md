# HR-ACCOUNT-ROLE-001 — Áp dụng và rollback

12/11/2026. Chỉ `tp_tanphat_test:18079` và `tp_tanphat_dev:18069`, cluster55432.
Theo [runbook hai database](SAMPLE_DATA_CLEANUP_AND_TEST.md); không restore test
sang main. Không seed, reset mật khẩu, cấp/hạ HEAD hoặc đổi mapping người thật.

## Gate và lệnh đã dùng

**Follow-up HR-COMPACT-007 / CHG-20261112-010:** chỉ CSS sizing/README,
giữ HR20.0.1.6.0/login20.0.1.4.0, không upgrade database. Private helper/evidence
`.local/hr-compact007/`; rollback2filegốc SHA256, seal53file. Restart exact test
18079 → compact7viewport/sidebar5nhóm đạt → stop exact main → backup
`backup-tp_tanphat_dev-20261112T063854566975Z` (596tables/643blobrefs) → start
main18069/assets/smoke đạt. Main79bảng/617nonassetblob khớp snapshot đầu,
ACL0delta. Reuse restore rehearsal005 cùng schema; không restoreDB/fixture.
Rollback007 chỉ trả hai file trong `rollback-source.zip/json` rồi restart đúng
runtime và kiểm assets; không đổi dữ liệu/quyền/index HEAD. Xem
[acceptance007](../../docs/demo/HR_COMPACT_007_ACCEPTANCE.md).

**Follow-up HR-POSITION-004 / CHG-20261112-007:** evidence/helper riêng tại
`.local/hr-position004/`;53file rollback gốc SHA256,0filemới,seal53file.
Preflight main không có duplicate active HEAD theo company/department. Unique
index mới `tp_kd_department_role_unique_department_head` nằm trong extension HR
trên model cũ, không thêm bảng/ACL hoặc sửa policy bằng tên job. Role chưa thu
hồi giữ vị trí; hạ trước rồi mới bổ nhiệm người khác. Không tự hạ người thật.
Rehearsal backup `backup-tp_tanphat_dev-20261112T051846939786Z`, restore test
596rowsets/643blobrefs/429sequences khớp rồi neutralize; fixture giả đã loại.
Final OdooHR26 và HEAD regression4 đạt, HOOT20/29 đạt, browser8nhóm/race2→1
đạt. Clean smoke chạy riêng sau500 asset Windows đã đạt. Main backup cuối
`backup-tp_tanphat_dev-20261112T052315995362Z`; upgrade chỉHR20.0.1.5.0
noHTTP/stop-after-init, login giữ20.0.1.4.0; main smoke/preservation theo status.

Rollback004: source zip trả về003 nhưng index SQL có thể còn; không giả định
upgrade tự xóa index. Nếu cần trả **cả policy**003, dừng đúng main, backup trạng
thái hiện tại, rà giao dịch/role mới và đối chiếu `pg_get_indexdef` đúng index
`tp_kd_department_role_unique_department_head` trên `tp_kd_department_role`
với `(company_id,department_id) WHERE active IS TRUE`; chỉ gỡ đúng index này
trong migration rollback đã review, giữ unique user/company/department cũ.
Sau đó source rollback004 và upgradeHR/start/smoke. Không dùng rollback001–003
để lùi riêng004; full restore chỉ từ backup main sau khi đánh giá dữ liệu mới.
Không xóa role/audit hoặc restore test sang main để rollback.

**Follow-up HR-POSITION-003 / CHG-20261112-006:** helper/evidence riêng tại
`.local/hr-position003/`, rollback53filegốc SHA256 và0filemới, seal53file.
Tái dùng role wizard cho job-only và quyền KH-KD; không thêm model/ACL.
Rehearsal backup `backup-tp_tanphat_dev-20261112T045025670054Z` restore canonical
test596rowsets/643blobrefs/429sequences khớp rồi neutralize; fixture giả đã loại.
Backend sau restore24ca HR đạt (login backend không chạy lại), HOOT20/29 và
clean smoke4nhóm mỗi cổng đạt. Main dừng đúng PID/config; backup cuối
`backup-tp_tanphat_dev-20261112T050005254157Z`, upgrade **chỉ** `tp_hr_workspace`
20.0.1.4.0 noHTTP/stop-after-init, login giữ20.0.1.4.0; start/smoke18069 đạt.
Source seal/79bảng/617nonassetblob bảo toàn; ACL policy giữ,2write_date đổi.
Inventory cả2cổng39employee/27users/8active/13phòng/7mappings/1HEAD, theo baseline
trước follow-up, không theo số lịch sử26/6. Không sửa job/quyền/account người thật.
Rollback riêng003 dùng `ops.py rollback` trong thư mục003 rồi upgrade chỉHR
để trả views/assets; không dùng rollback001/002 để lùi riêng003. Khi đã có
giao dịch mới, đánh giá dữ liệu trước khi cân nhắc full restore từ backup main.
Xem [acceptance003](../../docs/demo/HR_POSITION_003_ACCEPTANCE.md).

**Follow-up HR-ACCOUNT-002 / CHG-20261112-005:** helper/evidence riêng tại
`.local/hr-account002/`. Source rollback46file gốc +7file mới, seal53file;
không dùng rollback42file của CHG004 để lùi riêng follow-up này. Upgrade
`tp_hr_workspace`20.0.1.3.0 và `tp_web_login`20.0.1.4.0 trên cả hai cổng.
Backup rehearsal `backup-tp_tanphat_dev-20261112T041738740882Z` trong
`.local/hr001/`: restore canonical test bằng `ops.py restore-test`,596rowsets,
643blobrefs,429sequence khớp; đã neutralize UUID/baseURL/cron/SMTP rồi test lại
28ca0failed0errors trên source cuối (`backend-restored.log`). Fixture giả tạo/
reset/race đã bị loại bằng restore, không đưa sang main. Password mới qua RAM
OWL/RPC submit, xác thực admin trước và không nằm trong yêu cầu identity chờ.
Main backup cuối `backup-tp_tanphat_dev-20261112T042518138326Z`; upgrade và smoke cả2cổng đạt. Bảo toàn79bảng/617nonassetblob,39nhân viên/27users/7mapping theo baseline trước sửa;2ACLwrite metadata đổi do upgrade, policy giữ nguyên.
Không restore database chỉ để rollback UI sau khi đã có giao dịch mới; xem
phần rollback bên dưới và [acceptance follow-up](../../docs/demo/HR_ACCOUNT_002_ACCEPTANCE.md).

1. Đọc status/source/current HEAD policy, inventory main, giữ dirty worktree;
   `ai_workflow.py start` tiếp tục checkpoint. Backup source trước task riêng.
2. Test source trên test, fixture giả, Odoo/HOOT/Playwright; kiểm revocation
   RPC/API/export/attachment/chatter và tạo đồng thời/retry.
3. Backup main bằng helper private `.local/hr-account001/ops.py backup`:
   dump + filestore + config/source + baseline rowsets/sequences + checksum.
   Bản backup cuối dùng để restore được ghi trong acceptance.
4. Dừng đúng runtime test bằng `.local/hr-account001/runtime.ps1 stop test`;
   kiểm không còn session DB. Không dùng `dev.py stop` vì nó dừng cả PostgreSQL.
5. `.venv/Scripts/python.exe .local/hr001/ops_hr_account001.py restore-test <backup>`
   chỉ restore canonical test, backup test trước, kiểm checksum/rowsets/blob/
   sequence. Helper chỉ cho gỡ bảng transient mới `tp_hr_role_wizard` và sequence
   owned đã đối chiếu; không DROP CASCADE hoặc tạo database khác.
6. Chạy `.local/hr001/neutralize_test.py`; nó kiểm lại restore trước khi đổi
   UUID/baseURL, tắt cron/SMTP test. Upgrade và Odoo tests lại trên source cuối.
7. Test sạch + seal source + smoke đạt mới dừng đúng main; backup cuối khi main
   dừng nếu cần; upgrade cùng source bằng lệnh dưới, không test hoặc seed main.
8. Start main, đợi listener rồi read-only smoke; so fingerprint79bảng nghiệp vụ/
   quyền và nonasset blobs với baseline, inventory39employee/26users/6mappings.

```powershell
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_hr_workspace,tp_web_login --test-tags /tp_hr_workspace,/tp_web_login --stop-after-init --logfile .local/hr-account001/backend-restored.log
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace,tp_web_login --no-http --stop-after-init --logfile .local/hr-account001/upgrade-main.log
```

Đọc dòng tổng `0 failed, 0 error(s)`; exit code không đủ. Windows có thể reset
socket HTTP test; lưu lượt fail và rerun khi runtime/socket đã dừng. Không đổi
app auth hoặc nới assertion để che lỗi. GC asset WinError5 là giới hạn Windows
đã thấy; blob restore/main phải kiểm riêng.

## Rollback cụ thể

Chặn thao tác trong thời gian bảo trì, kiểm PID/config trước khi dừng. Backup
trạng thái hiện tại trước rollback. `.local/hr-account001/rollback-source.zip`
và JSON giữ từng file có trước task, SHA256; `rollback-new-files.json` chỉ rõ
5file mới. Helper `ops.py rollback` kiểm path/hash, khôi phục đúng file và gỡ
đúng5file mới, giữ thay đổi khác. Không reset Git, không xóa cả addon.

Rollback source rồi upgrade HR/login theo lệnh main trên để trả views/assets.
Bảng transient role còn lại có thể giữ; dữ liệu role/audit đã phát sinh phải
được rà riêng, không xóa lịch sử. Nếu đã dùng chức năng mới, không tự đảo role,
mapping hoặc password bằng restore cũ. Full DB+filestore rollback chỉ từ backup
**main** được chọn, theo runbook khi đã đánh giá dữ liệu ghi sau backup; tuyệt
đối không restore test đè main. Kiểm smoke và preservation sau phục hồi.

Snapshot source trong backup cuối chứa source mới đang kiểm thử; dùng zip
rollback riêng để về source trước task. Evidence chứa dữ liệu riêng nằm trong
`.local/` bị Git ignore, không đưa credential/dump/filestore/ảnh HR vào Git.


## HR-PROFILE-005 — 12/11/2026, CHG-20261112-008

UI refinement HR20.0.1.6.0, login giữ20.0.1.4.0. Không đổi backend/schema/ACL
hoặc gỡ indexHEAD004. Test restore main055849147435Z→canonical test, neutralize,
upgrade/test lại; main exactPIDstop/backupcuối061141441037Z/upgrade chỉHRnoHTTP/
start/smoke. Backup dưới `.local/hr001/`, evidence dưới `.local/hr-profile005/`.

Rollback UI005: kiểm SHA256 và restore53file trong rollback-source.zip/json,
upgrade chỉHR theo exact-runtime/backup process rồi kiểm browser/bảo toàn.
Không tự gỡ index HEAD hoặc đảo tài khoản/role; full restore chỉ từ backup main
được chọn sau đánh giá dữ liệu ghi mới. Không restore test đè main.

Đối chiếu đầu task có2write_date drift trước apply (employee63/resource64),
nguyên nhân chưa quy thuộc; không ghi raw equality. Archive052315995362Z khớp
fingerprint đầu xác nhận chỉ timestamps đổi. Sau apply79bảng khớp tuyệt đối
backupcuối061141441037Z,617nonassetblob/source53 giữ; ACL2write metadata đổi.
Xem [acceptance005](../../docs/demo/HR_PROFILE_005_ACCEPTANCE.md) cho test và giới hạn.


## HR-SIDEBAR-006 — 12/11/2026, CHG-20261112-009

Static-only correction: bỏ profile sidebar rail/palette, giữ menu chung.
HR20.0.1.6.0/login20.0.1.4.0, không migration/DBupgrade/XML/Python change.
Restart exact test và kiểm HOOT/browser; exact main stop, backup062555343599Z,
restart để sinh asset mới và kiểm browser. Không restore database cho staticfix;
restore rehearsal005 cùng schema đã kiểm chứng. Source53seal/main79bảng617blob/
ACL0delta giữ. Evidence private `.local/hr-sidebar006/`, rollback6filegốc SHA256
và restart/assets; không đảo dữ liệu, quyền hoặc indexHEAD. Xem
[acceptance006](../../docs/demo/HR_SIDEBAR_006_ACCEPTANCE.md).
