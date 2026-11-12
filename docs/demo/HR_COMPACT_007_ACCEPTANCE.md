# HR-COMPACT-007 — Thu gọn chi tiết nhân viên

12/11/2026, CHG-20261112-010. Đã kiểm kỹ thuật và áp assets lên18079/18069.
Yêu cầu trực tiếp: chi tiết đang quá lớn, thu nhỏ một chút; sidebar giữ nguyên.

Chỉ sửa `employee_profile.scss` và README trong `custom_addons/tp_hr_workspace`.
Avatar desktop110→88px, tên tối đa40→32px, tab17→15px, thông tin17→16px;
giảm header, nút, padding và khoảng cách. Native toolbar bỏ min-width thừa ở
nhóm action để phân trang nằm trong màn hình1280px. Không ẩn control hoặc đổi
sidebar. Mobile avatar64/tên25 giữ, nút đổi chức vụ tối thiểu44px. Giữ màu sắc,
năm tab, modal tài khoản/chức vụ, backend/quyền và một trưởng phòng.

## Bằng chứng thực chạy

- Browser `check.cjs` mỗi18079/18069 đạt2nhóm: profile vừa7viewport
  1672×1040/1440×900/1280×900/1024×900/768×1024/390×1040/320×1040;
  tabs/account modal/edit-cancel không sửa field/role modal-cancel hoạt động.
  Không tràn ngang form; tabs cuộn ở768/mobile. Không console/pageerror.
- `sidebar-regression.cjs` mỗi cổng đạt5nhóm: exact width/color/gradient/border
  từ list sang detail; modal giữ sidebar; tự thu rồi vào/ra giữ thu; mở/reload
  giữ mở; mobile drawer mở/đóng giữ palette. Không console/pageerror.
- Ảnh before/after main cùngadmin/employee63(TP10001)/route/viewport được mở
  tự đánh giá. 1672px: sheet852.5→715px (giảm16.1%), avatar110→88px,
  tên40→32px, tab17→15px. Desktop1280 không còn tràn toolbar/tabs.
- Asset SCSS compile thật cả2runtime. Không chạy lại Odoo backend/HOOT/XML
  hoặc upgrade database vì không sửa Python/JS/XML/manifest/schema.
- Main79bảng nghiệp vụ/quyền và617nonassetblob khớp tuyệt đối snapshot đầu;
  ACL0delta; source53file seal giữ. Cả2DB39employees/27users/8active/
  13phòng/7mappings/1HEAD; HR20.0.1.6.0/login20.0.1.4.0 giữ.

Exact test restart/test → seal → exact main stop → backup
`backup-tp_tanphat_dev-20261112T063854566975Z` (596tables/643blobrefs) → restart
main/assets/smoke đạt. Không seed/fixture/DBthứ3/restore test sang main.
Restore rehearsal005 còn cùng schema; không restore lạiDB cho thay đổi CSS.

Rollback:2filegốc trong private `rollback-source.zip/json`,0filemới, SHA256;
trả đúng file rồi restart/assets, giữ dữ liệu/quyền/indexHEAD. Evidence riêng
`.local/hr-compact007/`; không Git credential/backup/screenshot thật.

Lượt đầu phát hiện toolbar1280 tràn72px do min-width action, đã sửa nguyên
nhân và rerun đạt. Sau cold restart test có một lượt timeout session khi chờ
list, lượt tuần tự sau đạt; không tính fail là pass. Subagent model kế thừa
không khả dụng nên đây là tự review. Mobile giả lập, chưa kiểm thiết bị thật.
Visual feedback, business acceptance và pilot authorization vẫn tách riêng.
Không stage/commit/push. Next: Ctrl+F5 trên18069, mở nhân viên và review độ gọn.
