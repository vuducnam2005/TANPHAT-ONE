# HR-SIDEBAR-006 — Giữ nguyên sidebar khi xem chi tiết

12/11/2026, CHG-20261112-009. Đã áp static assets lên18079/18069; technical
verification đạt. Phản hồi trực tiếp của người dùng thay hành vi rail/palette
riêng của HR-PROFILE-005: chỉ thay vùng nội dung nhân viên, giữ sidebar chung.

Đã bỏ `hrProfileLayout`, hook mount/unmount của profile, nhánh thu/mở và body
class phụ trong sidebar, CSS màu/chiều cao rail riêng theo profile. Sidebar dùng
lại `hrPrefs.collapsed` và responsive native hiện có. Đang mở thì giữ mở; người
dùng tự thu thì giữ thu khi vào/ra hồ sơ hoặc tải lại. Màu, nền, border và chiều
rộng sidebar không phụ thuộc trang chi tiết. Giữ toàn bộ nội dung hồ sơ/modal,
quyền/backend, một trưởng phòng, navbar và breakpoint tablet/mobile.

File chính trong `custom_addons/tp_hr_workspace/`: `static/src/prefs.js`,
`static/src/sidebar/sidebar.js`, `static/src/profile/employee_profile.js/scss`.
Bỏ test cho hành vi transient đã bị yêu cầu loại; giữ test save/validation và
compiler icon. README và hướng dẫn phản ánh quy tắc mới.

## Kiểm chứng thực chạy

- Before main: sidebar list264px/navy, detail68px/gradient teal; evidence JSON
  và ảnh cùng actor/admin, employee63, viewport1672×1040 trong private
  `.local/hr-sidebar006/`.
- `check.cjs`: 5 nhóm đạt mỗi cổng18079/18069, 0 console/pageerror. So sánh exact
  computed width/backgroundColor/backgroundImage/border/rail giữa list/detail;
  modal không đổi sidebar; tự thu rồi vào/ra giữ thu; tự mở và reload giữ mở;
  mobile390 drawer mở/đóng và palette giữ. Ảnh sau main đã mở tự đánh giá.
- HOOT: HR filter21tests86assertions (gồm2KD), Home29tests166assertions đạt.
  `rg` không còn `hrProfileLayout`/`o_tp_hr_profile_layout` trong addon.
- Source seal53file, main79bảng nghiệp vụ/quyền và617nonassetblob khớp tuyệt đối
  snapshot đầu lượt; ACL0delta. Cả2DB39employees27users8active13phòng7mapping1HEAD.
- Chỉ JS/SCSS/test/README đổi; không XML/model/Python/manifest/schema/API change.
  Giữ HR20.0.1.6.0/login20.0.1.4.0. Không chạy lại Odoo backend suite hay upgrade
  database cho sửa static này. Restart exact test → browser/HOOT đạt → stop
  exact main → backup main062555343599Z → restart/assets/smoke main đạt.
  Restore rehearsal005596rowsets/643blobrefs/429sequences còn cùng schema; không
  restore lại database cho sửa static, không fixture hoặc DB thứ ba.

Rollback:6file gốc có SHA256 trong `rollback-source.zip/json`; dùng đúng file,
restart/assets rồi kiểm sidebar. Không thay dữ liệu/quyền hoặc gỡ indexHEAD.
Backup DB/config/source trước apply nằm trong `.local/hr001/`, không Git.

Browser harness đầu chờ phần tử `.is-hidden` ở trạng thái visible nên timeout;
đổi thành wait hidden rồi chạy lại cả5nhóm đạt, không sửa app để làm test pass.
Subagent model kế thừa không khả dụng, chỉ tự review scope/caller; mobile giả
lập, chưa thiết bị thật. Visual/business/pilot vẫn do người dùng quyết định.
Không stage/commit/push. Next: Ctrl+F5 trên18069, mở nhân viên và xem sidebar.
