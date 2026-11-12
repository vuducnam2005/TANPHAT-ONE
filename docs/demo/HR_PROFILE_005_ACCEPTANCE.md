# HR-PROFILE-005 — Chi tiết nhân viên và quản lý tài khoản theo ảnh mẫu

Ngày 12/11/2026, CHG-20261112-008. Technical verification: **đạt, đã áp local
18069 và 18079**. Visual/business acceptance và pilot authorization do người
dùng quyết định. Không commit/push. Tiếp tục quyền thực thi/test/backup-restore/
áp main trong task HR-ACCOUNT-ROLE-001 được người dùng giao trực tiếp.

## Kết quả và phạm vi

Ảnh người dùng là tham chiếu hình thức. Không lấy chữ/dữ liệu minh họa làm lệnh
đổi dữ liệu thật. Trang chi tiết có nền xanh băng, sheet trắng bo góc, ảnh/tên
lớn, metadata có icon, badge Mở/Khóa/Chưa có tài khoản, Đổi chức vụ màu teal
ngay dưới tên, năm tab có icon, hai khối công việc/liên hệ và tóm tắt tài khoản.
Modal tài khoản có hai cột, nhãn Việt rõ ràng, ô lý do dài, nút khóa đỏ, mở teal,
đặt lại mật khẩu riêng và Đóng; mobile xếp một cột. Xác nhận khóa có tiêu đề/
nút tiếng Việt. SVG nét cho icon lớp dữ liệu, dùng icon native ở các chỗ còn lại.

Giữ navbar, menu có quyền và chức năng phiên bản/lịch sử Odoo. Vì vậy toàn bộ
application chrome không trùng từng pixel ảnh minh họa. Sidebar native thu
thành rail teal khi vào hồ sơ, có thể mở lại; trạng thái này chỉ trong bộ nhớ,
không ghi đè preference thu gọn của người dùng và reset khi unmount. Không thêm
menu giả, model, ACL, API, thư viện hoặc chỉnh core/React/login addon.

HR **20.0.1.6.0**, login giữ **20.0.1.4.0**. Backend account/identity/password/
scope/protected-user và unique HEAD giữ nguyên. Đổi chức vụ vẫn chỉ trong chi
tiết; mỗi công ty/phòng chỉ một HEAD active, phải hạ người cũ trước. Chức vụ HR
không tự cấp quyền. File chính: `views/workspace.xml`, `static/src/profile/`,
`static/src/sidebar/sidebar.js`, `static/src/prefs.js`, test `hr_profile.test.js`
trong `custom_addons/tp_hr_workspace/`.

## Kiểm thực chạy

| Kiểm tra | Kết quả/evidence private |
| --- | --- |
| XML, upgrade test/main | 10 XML parse; upgrade chỉ HR noHTTP/stop-after-init đạt |
| Odoo backend | Sau restore: 26 tests, 0 failed/0 errors, `backend-restored.log`; trước restore lượt sửa lỗi môi trường 28 tests, 0 failed/0 errors |
| HOOT source cuối sau restore | HR filter 22 tests/90 assertions (gồm 2 KD), Home 29/166 đạt; `hoot-hr.txt`, `hoot-home.txt` |
| Browser nguồn cuối | `smoke.cjs`: 6 nhóm đạt mỗi cổng 18079/18069, 0 console/pageerror |
| Profile native | readonly ban đầu; 5 tab/icon; chuyển đủ tab; edit/cancel giữ dữ liệu; test kiểm required name; mở role wizard/hủy; rời form trả layout; mở/thu rail không đổi preference |
| Account UI | nhãn Việt; nút đúng account mở; modal ở 1672/1024/390/320 không tràn; focus ô lý do; profile mobile390/320 và reduced motion đạt |
| Account trạng thái | `states.cjs`: fixture test khóa → mở, mở → xác nhận khóa thành công; chưa account → native identity → login/password/confirmation cùng form → hủy; 3 nhóm, 0 errors |
| Quyền/một trưởng phòng | Backend HR regression giữ đạt; SQL cả hai DB có unique index, 0 scope trùng; không chạy lại race004 vì không đổi backend |
| Main dữ liệu | 39 employees, 27 users/8 active, 13 departments/9 occupied, 7 mappings, 1 HEAD; test sạch cùng số lượng |
| Bảo toàn | 79 bảng nghiệp vụ/quyền khớp tuyệt đối backup cuối trước apply, 617 nonasset blobs và source seal53file khớp; ACL chỉ 2 write metadata đổi do upgrade |

Không ghi chức vụ, tài khoản, mật khẩu hay quyền người thật để test. Main chỉ
mở, sửa nháp rồi hủy, xem dialog và hủy. Không test save thành công trên người
thật; HOOT kiểm nhánh save và backend tests dùng fixture. Password-reset browser
trong lượt này kiểm sự hiện diện nút; không đặt mật khẩu mới. Guard/backend reset
giữ test HR hiện có. Mobile là giả lập Chromium, chưa thiết bị thật.

## Restore, apply và dữ liệu

Evidence nằm trong `.local/hr-profile005/` bị Git ignore. Rollback source trước
task: 53 file có SHA256 trong `rollback-source.zip/json`, 0 file mới.

- Rehearsal nguồn main `backup-tp_tanphat_dev-20261112T055849147435Z`; backup test
  trước restore `backup-tp_tanphat_test-20261112T060701112831Z`. Restore canonical
  test khớp 596 rowsets, 643 blob references, 429 sequences; neutralize cron/mail/
  UUID/URL rồi upgrade và kiểm lại source cuối. Fixture đã loại bằng restore.
- Dừng đúng PID/config main, backup cuối
  `backup-tp_tanphat_dev-20261112T061141441037Z`, upgrade chỉ HR, start/smoke đạt.
  Không tạo DB thứ ba; không restore test sang main.
- Đối chiếu snapshot đầu task phát hiện `write_date` của employee63/resource64
  đã đổi trước apply; nguyên nhân chưa quy thuộc. Không gọi raw snapshot equal.
  `preserve_final.py` dùng archive trước có fingerprint khớp snapshot đầu để
  kiểm byte từng cột: chỉ đúng hai `write_date` đổi, giá trị nghiệp vụ còn lại
  giữ. `preservation-apply-strict.json` xác nhận 79 bảng khớp backup cuối trước
  apply, kể cả write_date; không sửa baseline hay trả lại thời gian cũ.

Rollback chỉ UI005: dùng zip nguồn trước task, upgrade HR bằng quy trình exact
runtime/backup, giữ dữ liệu/quyền/index004 và kiểm lại; không cần gỡ index HEAD.
Full restore chỉ từ backup main được chọn sau đánh giá dữ liệu mới. Xem
[runbook](../../ops/runbooks/HR_ACCOUNT_ROLE_001_DEPLOY_AND_ROLLBACK.md).

## Sự cố và giới hạn

Lượt backend đầu 5 teardown errors do tệp upload test có ReadOnly trên Windows;
đã kiểm đúng path và mở thuộc tính writable cho đúng tệp tạm, giữ nội dung, chạy
lại đạt. Warning GC rename một số asset và markdown2 còn trong log sau restore;
backend kết quả26/0/0, blob kiểm độc lập. Không tính lượt fail là pass.

HOOT mới ban đầu dùng dynamic import không được bundle native resolve; đổi sang
static import rồi chạy lại đạt. Browser harness cần chờ render rail và selector
xác nhận native; đã sửa/rerun đạt. Tên fixture đầu lỗi encoding pipe, đã sửa
UTF-8 và chụp lại; không ảnh hưởng dữ liệu thật. Các lượt lỗi giữ evidence.

Không có audit độc lập: spawn subagent thất bại do model kế thừa không khả dụng.
Source được tự review so rollback zip và caller native. Link docx lịch sử thiếu
file ngoài scope vẫn giữ ghi nhận cũ. Visual/business/pilot chưa được thay bằng
kết quả test. Người dùng mở TP HR → Nhân viên → bấm nhân viên → xem chi tiết và
Quản lý tài khoản để review.

Tham chiếu: [design](../ui/HR_PROFILE_005_DESIGN.md),
[hướng dẫn](HR_ACCOUNT_ROLE_001_USER_GUIDE.md),
[policy004](HR_POSITION_004_ACCEPTANCE.md).
