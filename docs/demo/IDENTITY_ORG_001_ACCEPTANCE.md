# IDENTITY-ORG-001 — Kết quả kỹ thuật và bàn giao

12/11/2026, CHG-20261112-011. **IMPLEMENTED_VERIFIED_MAIN_APPLIED**.
Người dùng giao thực thi trực tiếp, test→backup/restore→áp main; không commit/push.
Baseline thực CHG010/compact007, giữ sidebar006/profile005 và policy một HEAD.
Đây là tự review; nghiệm thu hình thức/nghiệp vụ/pilot chưa được người dùng xác nhận.

## Nguyên nhân và kết quả

Native name của employee đi qua resource, user name đi qua partner; native user
write không bảo đảm đồng bộ hai chiều, image chỉ chép về employee khi employee
chưa có ảnh. Roster có thể giữ SVG mặc định như image thật trong storage nên
avatar HR không nhận ảnh tài khoản. Đầu task main40employee/test39, mỗi bên7mapping;
số39main trong CHG010 đã cũ, không tự quy thuộc nguyên nhân hoặc xóa dữ liệu.
Main có4name mismatch,0xung đột hai ảnh thật. Menu KH-KD dựa group nền chưa đủ
phân biệt phòng chính, phân công và nguồn quyền liên phòng. Native work contact
có fallback private_email; đã bỏ fallback này trong custom addon.

Nguồn chính/acceptance trước code ở [thiết kế](../architecture/TP_IDENTITY_ORG_001.md).
HR quản lý tên/phòng/chức vụ; user/partner xác minh theo ID; ảnh sync hai chiều,
fallback thống nhất; không public HR private. Chuyển phòng nằm ở Thông tin công
việc, preview/lý do/bàn giao/kiêm nhiệm, khóa/snapshot/savepoint/audit. Default
staff, quyền theo assignment/grant, revoke HEAD cũ, chặn incumbent/multi-company/
future khác phòng. Current/history/future và mọi đường ghi đều có guard. Home/
server menu/action/dashboard/report cùng scope; old session hết hiệu lực.

## Kiểm thực chạy

| Cổng kiểm | Kết quả và evidence private |
| --- | --- |
| Baseline | HR26/26, `backend-baseline.log` |
| Backend source trước restore | HR38/38 `backend-final2.log`; combined144/145 ban đầu tìm fixture signed_date cũ thiếu, đã bổ sung bằng chứng ngày ký rồi case đó1/1 |
| Backend sau restore | HR38/38 `backend-restored.log`; HEAD/KH-KD109/109 `kd-restored.log`,0failed0errors |
| Bản text preview cuối | HR filter40tests0failed0errors `backend-display-final.log`; không đổi quyền/schema sau lượt regression109 |
| Lint/XML | Ruff toàn HR và5fixture KD đã đổi PASS, XML8 PASS, diff check PASS |
| HOOT | HR filter21tests86assertions (gồm2KD), Home29tests166assertions; `.local/hr001/hoot-18079/` |
| Browser fixture test |7nhóm `browser-result.json`: vào KD, rỗng theo assignment, không tiền/HR/admin, grant đúng scope; ra KD từ tab cũ/RPC/action, race2phiên→1success; modal/sidebar/mobile; live name/avatar navbar.0console/pageerrors |
| Stale transaction | `stale-result.json`: transaction cũ phát hiện grant đã commit từ cursor khác |
| Backend bổ sung | authhash/MFA/login/ID giữ khi rename; same-name/customer/private; ảnh hai chiều/conflict/retry; revoke export/attachment; handover giữ task owner; privilege/version/date/active/unlink/context guard; rollback audit |
| UI sạch | `clean-18079.json`, `clean-18069.json`:5nhóm admin home, transfer desktop/mobile/cancel, preview/cancel, identity modal/cancel,7mapping;0errors |
| Profile regression |2nhóm mỗi cổng,1672/1440/1280/1024/768/390/320; font/avatar/tab compact giữ, sidebar không đổi,0errors. Sheet1672 tăng715→748px do thêm nút chuyển phòng |

Các lượt lỗi được giữ riêng, không gộp thành PASS. KD fixtures cũ chỉ có group/
assignment được cập nhật scope liên phòng rõ ràng khi HR extension được cài;
outsider dưới policy mới bị deny workspace thay vì trả rỗng. HEAD có role hợp lệ
vẫn vào workspace độc lập phòng chính; không nới data rule để làm test xanh.
Fixture report cũ thiếu signed_date chỉ lộ khi context assert flush DB; sửa fixture,
không hạ constraint hợp đồng. Harness sạch ban đầu dùng nhãn home/department dịch
không đúng đã sửa selector rồi rerun. Preview text cuối dùng tên nghiệp vụ và
liệt kê việc chờ, không đưa raw model JSON lên màn chuyển phòng.

## Backup, restore và main

Evidence `.local/identity-org001/`, dump dưới `.local/hr001/`, đều Git-ignore.
Rehearsal main `backup-tp_tanphat_dev-20261112T072712247123Z`→canonical test:
**596rowsets/653blobrefs/429sequence khớp**. Test đã backup trước gỡ đúng transient
mới và FK target_department mới. Lượt đầu bị FK chặn; gỡ đúng constraint sau kiểm
source/target/column, không CASCADE, retry đạt. Restore helper log có lịch sử append,
kết luận dựa `restore-evidence.json` và neutralize kiểm lại, không dựa tail log cũ.
Test neutralize UUID/baseURL/cron/SMTP, upgrade HR rồi chạy tests lại. Fixture giả
đã bị loại bằng restore; cuối hai DB đều40employee/7mapping. Không DB thứ ba.

Main exactPIDstop/backupcuối `backup-tp_tanphat_dev-20261112T074626870983Z`
(596tables/653blobrefs)→upgrade HR20.0.1.7.0 noHTTP→reconciliation→start/smoke.
Chỉ text preview được làm rõ sau đó: kiểm HR40 và cleanbrowser test rồi exactmain
stop/backup `backup-tp_tanphat_dev-20261112T075053704012Z` (597tables/653blobrefs),
restart source cuối; không upgrade/schema/restore lần hai. Login20.0.1.4.0 giữ.
Source seal209file của6addon; rollback16fileđổi/9filemới so baseline trong JSON.

Reconciliation test trước rồi main theo preview ID/hash, qua wizard admin/reason/
audit, **7danh tính**, trong đó **4tên tài khoản** chuẩn hóa theo HR. Một ảnh thật
phía tài khoản được đưa về HR; sáu cặp fallback thống nhất theo HR. Không còn name
mismatch/photo conflict,0mappingpending. Không đổi phòng/chức vụ/role người thật,
login/password/MFA/userID/mapping hoặc snapshot hợp đồng. Preview/applied log riêng
cho từng DB, không merge account hoặc thay partner khách hàng.

Bảo toàn `preservation-result.json`: **88rowsets** theo cột baseline, auth giữ;
toàn bộ blob refs kiểm SHA/size, **627nonassetblob** trước/sau. Ngoài delta danh
tính được phép chỉ metadata write_date/write_uid và native complete_name/
commercial_company_name theo tên chính thức; ACL949/950 chỉ timestamps, thêm
1ACLcrud đối chiếu transient chỉ system admin. Assignments/grants/HEAD/company/
groups và toàn bộ nghiệp vụ giữ. Không gọi đây là raw equality toànDB.

## Ảnh và giới hạn

Cặp main cùng admin/hồ sơ TP10012/1672×1040 và390×1040:
`identity-before-{1672,390}-18069.png` ↔ `identity-after-{1672,390}-18069.png`.
Ảnh thật account trước đó đã được giữ và hiện ở HR sau reconciliation; đây không
phải ảnh tạo mới. Profile TP10001 có cặp before/after tương tự. Các cặp ảnh đã mở
tự đánh giá. Fixture cùng account ở home có before-staff-home/after-staff-home-kd/
after-staff-home-other; desktop1440×1000. Transfer/identity modal sạch của cả2cổng
và ảnh live navbar trong cùng thư mục. Ảnh HR không đưa vào Git.

Chưa thiết bị điện thoại thật, load test hoặc audit độc lập: subagent khởi tạo lỗi
model kế thừa không khả dụng, không có kết luận từ reviewer thứ hai. Transfer dùng
short table locks cho nguồn scope/việc đang xử lý để chặn phantom/concurrent write;
có thể chờ các writer khác trong transaction, cần đo lại khi tải thực lớn. Tài
khoản đa công ty/future khác phòng cần review riêng; không thêm migration đó.
Windows GC có WinError5 và markdown2 warning; referenced blobs đã kiểm độc lập.
Không chạy React/API tests vì không sửa legacyReact/API. Nội dung đã tải trước
thu hồi không thể thu lại. Visual/business/pilot vẫn do người dùng.

Next: mở18069, admin review chuyển phòng và đối chiếu theo
[guide](IDENTITY_ORG_001_USER_GUIDE.md). [Runbook rollback](../../ops/runbooks/IDENTITY_ORG_001_DEPLOY_AND_ROLLBACK.md).

## Follow-up cùng task — CHG-20261112-012

Rà cuối sau checkpoint011 phát hiện direct current_version_id có thể trỏ phiên
bản người khác cùng phòng; hr.version.employee_id cũng có thể chuyển lịch sử giữa
hai người. Đã chặn cả hai và chặn company sai khi tạo version. Native tạo employee
cần gắn lại phiên bản được tạo trước employee row: chỉ cho back-link ban đầu khi
version chưa có owner và target chưa có lịch sử, không dùng context client bypass.
Lượt guard đầu chặn cả native back-link nên4setUpClass lỗi, chưa áp main; sửa đúng
ngoại lệ native rồi rerun **41tests0failed0errors** `backend-version-final2.log`.
Giữ lượt fail, không coi pass. Không thay schema/menu/assets hoặc dữ liệu thật;
reuse restore596/653/429 và regression109 của011. Cleanbrowser cả2cổng, Ruff,
source seal và88rowsets/auth627blob preservation kiểm lại; exactmainbackup/restart
source guard cuối ghi trong status012. Đây vẫn là self-review, không audit độc lập.
