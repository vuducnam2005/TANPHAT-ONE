# HR-POSITION-003 — Tìm và hiểu thao tác nâng/hạ chức vụ

12/11/2026. Người dùng chỉ danh sách HR và không tìm thấy nơi nâng/hạ chức vụ.
Tiếp tục phạm vi HR-ACCOUNT-ROLE-001; không tự đổi chức vụ/quyền người thật.

## Thiết kế trước sửa

Danh sách: mỗi dòng admin có **Đổi chức vụ** bên cạnh **Xem tài khoản**.
Hồ sơ: nút **Đổi chức vụ** ở ngay dưới thông tin định danh, không cần tìm tab.

```text
Đổi chức vụ / Bổ nhiệm và hạ quyền
  Nhân viên · phòng ban
  Chức vụ hiện tại       Quyền hiện tại

  Bạn muốn thay đổi gì?
  (o) Đổi chức vụ trong hồ sơ
  ( ) Bổ nhiệm / hạ quyền KH-KD [khi có account và bộ quyền]

  Chức vụ mới [danh mục]       hoặc
  Thao tác quyền (Bổ nhiệm trưởng phòng / Chuyển về nhân viên)
  [ ] Đổi cả chức vụ ghi trong hồ sơ
  Lý do [textarea có nhãn/chú thích]

  Xem trước thay đổi → chức vụ trước/sau, quyền thêm/thu hồi/giữ
  Xác nhận thay đổi / Hủy
```

Tái sử dụng `tp.hr.role.wizard`, action preview/digest/locks/audit và HEAD
hiện hành, không thêm role engine. Chức vụ là dữ liệu HR riêng: đổi lên/xuống
theo danh mục không tự cấp hoặc thu hồi quyền. Quyền KH-KD chỉ có staff↔HEAD
đã triển khai. Phòng khác/chưa account có giải thích, vẫn đổi chức vụ HR được.

Palette theo HR: navy#17324D/chữ#233549/phụ#526477, nền#FFF/#F4F7FB,
teal#087F8C, border#9FB0C0, danger#AC2525. Font hệ thống; heading20px600,
label14px600/input16px tối thiểu44px; khoảng8/16/24. Form căn trái, tóm tắt
desktop2cột/mobile1cột; ô nhập riêng hàng, chú thích sát ô, preview có tiêu đề.
Không đổi navigation/dashboard hoặc thêm đồ họa. Focus2px,hover180ms,reduced.

Acceptance: admin tìm được từ list và hồ sơ; đổijob có lý do/preview/audit,
quyền không đổi; staff→HEAD→staff giữ scope/revocation và optionaljob nguyên tử;
no-account/unsupported rõ; nonadmin/outsidecompany/stale/invalidjob/forgedpreview
bị chặn; cancel không ghi; desktop/mobile/keyboard/console/ảnh trước–sau.
