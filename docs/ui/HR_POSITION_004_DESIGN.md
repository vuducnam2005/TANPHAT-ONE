# HR-POSITION-004 — Chỉ đổi chức vụ trong chi tiết, một trưởng phòng

12/11/2026, CHG-20261112-007. Phản hồi trực tiếp thay cách bố trí CHG006.

Danh sách giữ Xem tài khoản, bỏ Đổi chức vụ và CSS xếp hai nút. Bấm dòng
nhân viên mở chi tiết; Đổi chức vụ giữ ngay dưới tên, trước các tab. Màu/font/
spacing/focus/mobile theo thiết kế003; không thêm component hoặc navigation.

```text
Danh sách → bấm nhân viên → Chi tiết nhân viên
  [Tên / mã / phòng / chức vụ]
  [Đổi chức vụ]
    ( ) Đổi chức vụ trong hồ sơ — không cấp quyền
    ( ) Bổ nhiệm / hạ quyền KH-KD
        Mỗi phòng chỉ một trưởng phòng.
        Nếu có: báo tên người đang giữ vai trò; hạ người đó trước.
        Không tự hạ hoặc thay thế người đang giữ vai trò.
```

Backend: chỉ một role active cho mỗi company/department, kể cả khi user bị
khóa hoặc role chờ/hết hạn nhưng chưa thu hồi; cần hạ cấp rõ ràng với lý do.
Tái dùng model role hiện có, guard superuser/audit và unique index để chặn
hai yêu cầu đồng thời hoặc provisioning trực tiếp. Preview/apply kiểm người
đang giữ vai trò, không suy quyền từ tên chức vụ HR. Job-only vẫn không cấp quyền.

Acceptance: list không còn nút; row mở chi tiết, profile có nút desktop/mobile;
phòng có trưởng phòng → preview/apply bổ nhiệm người khác bị chặn bằng tiếng Việt;
trưởng phòng cũ giữ nguyên, hạ trước rồi bổ nhiệm được; phòng/company khác không
bị chặn nhầm; reactivation/provisioning trực tiếp và race không tạo hai HEAD.
Fixture giả chỉ test, không thay quyền/chức vụ người thật; backup/restore trước main.
