# HR-ACCOUNT-ROLE-001 — Acceptance và bằng chứng

**Hiện hành từ CHG-20261112-005:** luồng mật khẩu riêng bên dưới được thay bằng
form login/mật khẩu/nhập lại cùng màn hình, reauth admin trước và lưu nguyên tử.
Xem [acceptance follow-up](HR_ACCOUNT_002_ACCEPTANCE.md). CHG004 bên dưới giữ
làm lịch sử; thao tác hiện hành theo guide đã cập nhật.

12/11/2026 — CHG-20261112-004. Yêu cầu đính kèm của người dùng cho phép thực thi
trực tiếp, test trước rồi backup/restore và áp main; không commit/push.
Technical verification tách khỏi visual/business acceptance/pilot authorization.

## Thay đổi và phạm vi

- `tp_hr_workspace`20.0.1.2.0: bỏ picker/link/unlink; chặn RPC cũ và transfer qua
  employee/resource/native/import. Tạo user mới nguyên tử; giữ unique native
  theo company, không global unique. Password qua change.password.wizard.
- Admin tại tab Tài khoản & phân quyền quản trị staff ↔ HEAD KH-KD, scope bằng
  CRM team/company/department; không suy theo tên phòng/chức vụ. Tái sử dụng
  tp.kd.department.role và scoped groups, giữ guard superuser và actor thật.
- Preview lý do/nguồn quyền, digest/row+table locks/snapshot đọc mới; chặn stale
  hoặc management grants/groups/assignment xung đột khi hạ. Quyền cấp riêng
  hợp lệ được liệt kê/giữ. Không set toàn bộ groups.
- Native form năm tab, header định danh, edit/save/cancel/dirty validation,
  chatter trong Lịch sử, thông tin nguồn thu gọn, navy/light/two columns/mobile.
  Trạng thái tài khoản Mở/Khóa/Chưa có tài khoản tách profile archive.
- `tp_web_login`20.0.1.3.0: giữ lock/session và đúng thông báo
  “Tài khoản đã bị khóa. Vui lòng gửi phản hồi.” Feedback chưa gửi gì.

## Test thực chạy trên 18079

| Gate | Kết quả và bằng chứng private |
| --- | --- |
| Odoo HR/login | `backend-final-source.log`: 0 failed,0 errors of26tests sau restore và source cuối; cả account creation/rollback/login duplicate/retry/identity/role/money/export/attachment/chatter/audit/job/stale/lock/password/TOTP/CSRF |
| HEAD regression | `head-regression.log`: 0 failed,0 errors of14tests, TestDepartmentRole + TestHeadOperations, upgrade tp_project,tp_kd_workspace trên test |
| Tạo concurrent HTTP | `concurrent2.cjs`/`concurrent-result.json`: cùng employee và hai employee cùng login; mỗi race1success/1deny/1user/1mapping, retry denied |
| Concurrent quyền | `stale_concurrency.py`/`stale-concurrency-result.json`: transaction snapshot cũ, phiên khác commit financial grant, apply bị chặn bằng snapshot mới |
| Browser actions | `actions-result.json`:8checks đạt; tạo account + native password reauth, promote UI, scoped HEAD/outside deny, demote UI/old RPC+API401, fresh export/HR deny, lock invalidates, save persists, old link RPC deny |
| UI + entries | `ui-18079.json`, `entries-synthetic.json`, `entries-18079.json`: desktop1440×1100/mobile390×1100,5tabs/no picker/edit-cancel/history, list/search/dashboard/deep link,3badges,validation/focus/reduced,0console/pageerror |
| HOOT | `.local/hr001/hoot-18079/`: HR17+2dependency=19tests/78assertions; Home28+1dependency=29tests/166assertions; cả2suite đạt |
| Static | Ruff HR+login models/tests, XML6files, JS syntax đạt; diff và workflow checker ghi ở handoff cuối |

Test luôn dùng actor/dữ liệu giả trên canonical test. Log stats có subclass
inheritance nên tổng per-module khác dòng suite tổng; báo theo dòng result.
Attachment `raw` trong Odoo20 trả object content base64; assertion đã sửa cho
đúng contract rồi test đạt. Một lượt HTTP lock-session bị ConnectionResetError
Windows; rerun cả HR/login đạt. Các lần harness fail (selection input, masked
cell password, chờ modal, chờ data badge, focus) được sửa; không tính là pass.
GC assets WinError5 và markdown2 warning có trong test, không làm suite fail;
filestore main và restore kiểm độc lập. Không sửa Odoo core để xử lý warning.

## Bằng chứng thu hồi

Model test cùng actor trước/sau: HEAD đọc project đúng phòng, financial_read,
export/file/chatter được; ngoài scope không được. Sau revoke HEAD, cùng object
không có access, HEAD false, financial false, export/file/chatter AccessError.
Browser tab đang đăng nhập bị từ chối RPC và `/api/v1/me`401 ngay yêu cầu sau;
fresh staff session không export scope cũ và không vào HR private. Các session
không được tự replay ghi. HEAD không nhận base.group_system/hr.group_hr_user.

Grant quản lý riêng và group project manager chặn hạ và role còn nguyên; preview
liệt kê grant. Staff giữ scoped group; không nhận quyền chỉ từ chức vụ HR.

## Inventory, backup và triển khai

Baseline main:39employees,26users,7activeusers,13departments,6mappings hợp lệ;
không duplicate user/company. Một HEAD hiện hành và CRM team đúng scope đã
đối chiếu; không suy tài khoản dùng chung từ giao diện cũ.

Backup main dùng rehearsal:
`.local/hr001/backup-tp_tanphat_dev-20261112T032800001448Z`:
595tables/638blobrefs, dump+filestore+source/config/checksum. Restore canonical
test đã đối chiếu toàn bộ rowsets/blob/sequence rồi neutralize. Backup test
trước restore tại `backup-tp_tanphat_test-20261112T033340910479Z` giữ fixture cũ.
Không tạo database thứ ba. Kết quả sau restore và main được bổ sung trong mục
trạng thái cuối bên dưới. [Runbook](../../ops/runbooks/HR_ACCOUNT_ROLE_001_DEPLOY_AND_ROLLBACK.md).

Rollback source trước task riêng tại `.local/hr-account001/rollback-source.zip`
+SHA JSON và danh sách5file mới; không dùng source mới trong snapshot cuối để
rollback. Bảo toàn main so79bảng nghiệp vụ/quyền và nonasset blobs, source seal.

## Ảnh và giới hạn

Ảnh chứa dữ liệu HR ở `.local/hr-account001/`, Git ignored:
`before-desktop.png` ↔ `after-desktop-18079.png`,
`before-mobile.png` ↔ `after-mobile-18079.png`; cùng admin/route/hồ sơ/viewport.
`role-preview.png`, `status-open.png`, `status-locked.png`, account-empty và
main screenshots bổ sung. Đã mở ảnh để tự đánh giá, không chỉ so mã CSS.

Chưa kiểm điện thoại vật lý, chưa có audit độc lập (subagent không khởi tạo
được với model kế thừa). Phòng ngoài bộ KH-KD chưa có role selector thực thi;
báo chưa triển khai. Visual/business acceptance/pilot vẫn do người dùng quyết
định. Feedback tiếp tục chưa triển khai; dữ liệu đã tải trước thu hồi không
thể thu lại. Không chạy React legacy vì không thay React/API contract.

## Trạng thái cuối

**IMPLEMENTED_VERIFIED_MAIN_APPLIED.** Restore595tables/638blobrefs/428sequences
đạt và neutralize; test tuần tự source cuối26tests0failed0errors. Có hai lượt
test bị khởi chạy chồng lúc pregen assets; đã dừng đúng PID, bỏ kết quả và chạy
lại tuần tự. Sau test sạch, HOOT và desktop/mobile smoke đạt. Inventory không
còn actor/employee/project giả của task.

Main backup cuối sau dừng runtime: `.local/hr001/backup-tp_tanphat_dev-20261112T034224215080Z`,
595tables/638blobrefs; rehearsal dùng bản032800001448Z cùng dữ liệu main đã
kiểm. Upgrade main chỉ HR/login20.0.1.2.0/20.0.1.3.0, không tests/seed; start
18069, UI desktop/mobile và list/search/dashboard/deep-link smoke đạt. Mobile
native bottom sheet cần chạm ngoài để đóng sau edit/cancel; test đã dùng thao
tác đó. Browser UI/entries không console/pageerror.

Main preservation79business/security tables và612nonassetblobs khớp, source
seal46file khớp. Cả2cổng39employees/26users/7activeusers/13departments/9đơn vị
có người/6mappings/1HEAD. **Không thay user/login/password/mapping/groups/HEAD/
assignment/grant người thật.** Các ghi main là module metadata/views/ACL mới,
assets và transient/login/session khi smoke. Rollback chưa cần thực hiện.
Groups/implied/company-memberships hash giữ nguyên. Odoo20 dùng bảng `ir_access`;
so dump từng cột: thêm duy nhất ACL950 cho role wizard admin, ACL949 chỉ đổi
write_date, không đổi policy ACL cũ. Message mới duy nhất là notification
“Access created” của ACL950; ID lịch sử cũ còn đủ. Evidence `acl-delta.json`,
`security-preservation.json`, `message-delta.json` private.
`git diff --check`, links/fences/static và workflow finish/check được kiểm
ở bàn giao CHG004. Không commit/push. Visual/business/pilot vẫn chưa tự nhận.

