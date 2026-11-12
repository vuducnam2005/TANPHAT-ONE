# HR-ACCOUNT-ROLE-001 — Hồ sơ và tài khoản cá nhân

12/11/2026. Yêu cầu đính kèm là lệnh triển khai trực tiếp trong task này.
Native Odoo, tái sử dụng form validation/save/discard/dirty guard và chatter.

## Wireframe trước triển khai

```text
Sidebar navy | Quay lại / Sửa hồ sơ / Lưu / Hủy (native)
             | Avatar  Họ tên                  [Mở / Khóa / Chưa có tài khoản]
             |         TPxxxxx   Phòng ban — Chức vụ HR
             | Tổng quan | Công việc & hồ sơ | Thông tin cá nhân | Tài khoản & phân quyền | Lịch sử
             | Công việc (2/3)                | Liên hệ (1/3)
             | Login — Vai trò nghiệp vụ — Phạm vi (dải gọn)
```

Trong tab tài khoản: chưa có user → giải thích ngắn + Tạo tài khoản riêng;
đã có user → login chỉ đọc, tình trạng, phòng/chức vụ, role/scope và quyền
cấp riêng. Admin mở hộp quản trị hoặc Thay đổi vai trò → chọn → nhập lý do
→ xem trước thêm/thu hồi/giữ → xác nhận. Không picker user khác.
Lịch sử chứa chatter native; nguồn và thông tin kỹ thuật trong vùng thu gọn.
Thông tin cá nhân giữ group HR, HEAD không nhận quyền HR.

## Tokens và kiểm brief

- Sidebar navy #17324D; nền #F4F7FB; vùng trắng #FFFFFF; chữ #233549;
  accent #087F8C; đường phân cách #DCE3EB.
- Font hệ thống đang dùng Odoo, không tải font ngoài. Tên26px/600,
  tiêu đề16px/600, dữ liệu14–16px, nhãn13px; căn trái.
- Spacing8/16/24px, avatar72px, chiều rộng nội dung1180px; desktop2cột,
  dưới768px1cột. Badge xanh/đỏ/xám có chữ.
- Hover180ms, focus2px; reduced-motion tắt transition. Không animation lặp.
- Đã so brief: bỏ các card bằng nhau và cảnh báo nguồn cố định; danh tính,
  chức vụ HR và role backend phân tách, không chart trang trí hoặc lặp login
  trong nhiều khối lớn. CSS giới hạn form/dialog HR.

## Acceptance

Admin đúng công ty tạo user mới nguyên tử; duplicate/retry/concurrent không
tạo user mồ côi; link/unlink RPC cũ bị từ chối. Native/import/resource không
chuyển danh tính. Giữ unique(user_id,company_id) Odoo, không global unique.
HEAD/staff KH-KD hai chiều dùng tp.kd.department.role và policy HEAD hiện hành;
xem trước nguồn quyền, chặn hạ khi quyền quản lý cấp riêng còn xung đột.
Đổi chức vụ không cấp quyền; mọi thay đổi role có lý do/snapshot/audit/version.
Test giả chỉ18079; browser desktop/mobile/keyboard/reduced-motion và ảnh cùng
route/viewport/data. Backup DB+filestore+source/config, restore test kiểm chứng
trước main18069; main chỉ upgrade/smoke đọc, không thao tác account người thật.
