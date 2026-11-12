# HR-001 — Bàn giao roster và workspace nhân sự native

Ngày 11/11/2026 (Asia/Saigon), `CHG-20261111-002`.
Trạng thái: `IMPLEMENTED_VERIFIED_MAIN_PENDING_BUSINESS_VISUAL_PILOT`.
[Prompt phạm vi](../prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md), DEC-038.
Đây là kiểm chứng kỹ thuật của phiên triển khai; phản hồi giao diện, nghiệm
thu nghiệp vụ và cho phép pilot do người dùng quyết định riêng.

## Kết quả trên hai môi trường

Main `tp_tanphat_dev`/18069 và test `tp_tanphat_test`/18079 đều đang chạy:

| Chỉ tiêu | Kết quả mỗi DB |
| --- | --- |
| Hồ sơ/phiên bản | 39 employee / 39 version, không có fixture test trên main |
| Cơ cấu | 9 đơn vị có nhân viên trong 14 danh mục giữ/tạo có căn cứ |
| Lần nhập đầu | 39 create / 0 update / 0 skip / 0 conflict |
| Nhập lại | 0 create / 0 update / 39 skip / 0 conflict, không thêm version |
| Mã/mapping | TP10060 đúng; Ban KD→department18, Thiết kế→department20 giữ FK |
| Danh tính/quyền | Giữ25users; admin và5KD còn active;16actor mẫu archive |
| Liên kết | 39employee chưa gán user;5aliasKD chờ bằng chứng danh tính |

Nguồn SHA256 `8b1ed1f254ac56288da30b53a2fe3bb9858c18b995743c7d45fb686129b5f8ff`
không đổi;78dòng hai sheet gộp39người/9nhóm. Chỉ đọc danh mục A:E, không nhập
vào-ra. `TP + (10000 + mã nguồn)` là mã nghiệp vụ, không đổi ID/FK/barcode/CCCD.
Giữ đơn vị nguồn cùng mapping; không bịa hierarchy hoặc pháp nhân.

## Sáu chặng đã thực hiện

| Chặng | Chức năng và bằng chứng |
| --- | --- |
| A — sạch/đối chiếu | Backup, manifest binding+provenance; dọn đúng3HRscenario/catalog/contact riêng; archive16actor, giữ auth/group/company/HEAD và alias pending; backend chặn demo loader |
| B — model/import | Dùng hr.employee/version/public; TP unique gồm archived, sequence/company lock; upload→preview→mapping→apply→kết quả, checksum/sheet/row/actor, field delta/manual preservation, retry/rollback, audit bất biến |
| C — HR thực | CRUD/cancel/archive/restore native, manager-only kể cả resource path; giữ lịch sử, private fields/version/file/chatter; skills/hồ sơ native, canonical credential theo contact và quyền caller |
| D — workspace | Home giữ7thẻ/1navbar; sidebar riêng theo menu service lọc quyền, search/collapse/drawer/focus; bảng/config/history10/20/50/100,20mặc định, preference riêng DB/user/company/app/action/view |
| E — tổng quan/Excel | KPI/donut/bars/bảng thay thế và chất lượng hồ sơ có drilldown; filter/domain backend chung XLSX2sheet; literal text, whitelist, freeze/autofilter/tổng/format; không sudo aggregate/lộ lương/CCCD/ngân hàng |
| F — triển khai | Fresh backup main→restore test chuẩn→neutralize→fresh install/tests/cleanup/import/retry→áp module/ORM main→smoke/quyền/bảo toàn; không restore test đè main hoặc DB thứ3 |

Checklist cơ bản: mã TP + đơn vị + (chức vụ nguồn hoặc chức danh đã khai báo).
Thiếu liên hệ/chức danh canonical/tài khoản là chỉ tiêu riêng. Active chỉ là
hồ sơ đang quản lý. Cờ xác nhận gia đình/lương giữ mặc định khác dữ liệu đã
kiểm chứng; lương0đã xác nhận vẫn hợp lệ. Lịch sử TP HR dùng list, ô lương chưa
xác nhận để trống; không mở graph/pivot lương từ ngày/default kỹ thuật.

## Kiểm thử đã đạt

Bằng chứng private `.local/hr001/`:

| Kiểm tra | Kết quả |
| --- | --- |
| Backend đầy đủ | 28tests,0failed/0errors: backend-final-secured.log; fresh install rehearsal-upgrade-tests2.log; backend-packaging-final.log |
| Delta lịch sử/knownness cuối | 4tests,0failed/0errors: backend-version-knownness-final.log; main view upgrade thành công |
| HOOT | HR10+2dependency=12tests/34assertions; Home28+1dependency=29tests/166assertions; hoot-18079/ |
| UI ghi test | 13nhóm đạt trước fresh restore: CRUD/cancel/archive/restore; upload→preview78dòng/39line→fulltable100→apply39skip; fixture archive và loại khi restore |
| UI sau restore/main | Test11/11,main11/11,0pageerror; ui-18079/result-last-pass.json,ui-18069/result-last-pass.json; history/config,5width1440/1024/768/390/320,keyboard/reducedmotion,group/sort/cột/paging/Excel |
| Delta UI lương chưa rõ | 4/4mỗi DB,0pageerror,không ghi nghiệp vụ; version-probe-18069/ và version-probe-18079/: chỉlist,khônggraph/pivot,bật cột lương vẫn trống |
| Đồng thời | concurrency-result.json:2transaction cấp mã khác/duplicate chỉ1create; source-concurrency-result.json:4checks manual-first/source-first/mapping-race/cleanup đạt, có serialization retry boundary |
| Quyền | Native read/search/aggregate/export,source/wage/version/file/chatter/company,officer/manager/staff synthetic; export403 ở5KD thật; không cấp HR cho KD |
| XLSX/tĩnh | Openpyxl2sheet/tổng39,artifact render summary/detail private; Ruff2addon,XML/assets/JS syntax,diff và workflow kiểm ở bàn giao |

Năm actor KD đều đăng nhập/Home/sidebar/overview được, mở hai list native
Dự án/Đấu thầu; HEAD capability đúng chỉ HEAD. List thật hiện rỗng nên không
mở được detail nghiệp vụ thật; không tạo fixture main để lấp chỗ trống.
Mẫu preview native nhận diện riêng, không tính thành bản ghi thật.

Lệnh fresh install khi HTTP test dừng:

```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local/test/odoo.conf -d tp_tanphat_test -u tp_organization,tp_web_home -i tp_hr_workspace --test-enable --test-tags /tp_organization,/tp_hr_workspace,/tp_web_home --stop-after-init --http-port=18079 --max-cron-threads=0 --logfile=.local/hr001/rehearsal-upgrade-tests2.log
```

Upgrade tiếp theo dùng `-u tp_organization,tp_hr_workspace,tp_web_home`;
delta cuối chỉ action/view HR dùng `-u tp_hr_workspace`,kiểm4ca liên quan.
Không dùng exit0 thay log kết quả. Các lỗi parser/Binary/OWL/runner trước sửa
được giữ để truy vết. Startup thường không import test framework.

## Backup, restore và bảo toàn

Backup trước rollout đã kiểm restore:
`.local/hr001/backup-tp_tanphat_dev-20261111T025345789849Z`.
Dump nhất quán+filestore+config/source+manifest; restore khớp592bảng/261blobrefs/
424sequence names+counters trước neutralize. Test trước reset cũng được backup.
Extra2bảngHR/1orphansequence cũ trên test được kiểm phụ thuộc và reset hẹp,
không CASCADE; lỗi sequence ở diễn tập đầu sửa trước main. Cluster chỉ2DBapp+
3DBhệthống. Main áp module/ORM,không restore test đè main.

Backup sau nhập,trước delta view cuối:
`.local/hr001/backup-tp_tanphat_dev-20261111T031424514095Z`,594bảng/621refs;
có manifest/sequence inventory,chưa tuyên bố đã restore bản này. Seal34file
source cuối; mapping/dump/ảnhPII chỉ private,không Git.

Giữ auth/login/partner/group/company/HEAD/config và nội dung944ACL cũ;
thêm đúng4ACL batch/lineHR. Strict report gốc giữ **FAIL** vì hash write
metadata và phụ thuộc/audit/cache; không sửa report thành PASS. Đối chiếu bổ
sung từ COPY của finaldump kiểm từng dòng/nguyên nhân:

- 16partner chỉ đổi write metadata,name/active/identity giữ;3contact mẫu dọn.
- 16channel membership đúng actor archive,6categoryrelation/7resumeline đúng
3employee mẫu dọn; không mất dòng của người khác.
- 30attachment đúng3scenarioemployee/contact dọn;390imageattachment native
thuộc39employee/39workcontact mới;3bundleweb được thay bởi asset mới.
- Signaling chỉ thêm; device audit cũ giữ,7log mới đúng admin+5KD của smoke.

`final-semantic-preservation-result.json` và `final-reconciliation-gate.json`
đều PASS,0vi phạm;621blobrefs hiện tại đúng SHA1/size,attachment giữ nguyên ngoài
mẫu/assets đã phân loại. Đây là đối chiếu kỹ thuật,không thay audit/nghiệm thu
của người dùng. Backup cùng máy,chưa có backup ngoài máy. Windows OdooGC có
WinError5 trên file read-only; sửa metadata có kiểm bytes,không sửa upstream;
log cũ giữ và hạn chế vận hành được ghi rõ.

## Sử dụng và cổng còn mở

[Mở TP HR trên main](http://127.0.0.1:18069/odoo/tp-hr),dùng admin hiện có.
[Hướng dẫn người dùng](HR_001_USER_GUIDE.md) và
[runbook nhập/rollback](../../ops/runbooks/HR_001_IMPORT_AND_ROLLBACK.md).

Chưa có whitelist danh tính5alias hoặc người thật được giao HR officer/manager;
thiếu hierarchy,ngày vào/nghỉ,hợp đồng/chứng chỉ và thông tin riêng. Không suy
quyền từ chức vụ. Chấm công/ca/tăng ca,nghỉ phép,lương/BHXH/thuế,tuyển dụng/đánh
giá cần quy chế/dữ liệu riêng;không cài module/tạo nút giả cho backlog. Nghiệm
thu nghiệp vụ/visual/pilot riêng. Không commit/push.
