# HR-ACCOUNT-002 — Ô nhập tài khoản và thông báo tiếng Việt

12/11/2026. Phản hồi trực tiếp sau HR-ACCOUNT-ROLE-001: nhập login và mật khẩu
trên cùng màn hình, input/nhãn/chú thích rõ, Việt hóa thông báo. Ảnh người dùng
cho thấy câu xác thực admin còn tiếng Anh. Đây là yêu cầu thực thi tiếp task HR.

## Thiết kế trước triển khai

```text
Xác nhận danh tính quản trị viên (Odoo native, tiếng Việt)
  Mật khẩu của bạn — giải thích đây là admin đang thao tác
  Xác nhận / Hủy

Tạo tài khoản riêng
  Nhân viên · mã TP · phòng ban (tóm tắt)
  Tên đăng nhập      [input cao44px, viền rõ]
  Dùng để đăng nhập TANPHAT ONE. Không chứa khoảng trắng.
  Mật khẩu mới       [input ẩn + Hiện mật khẩu]
  Độ dài tối thiểu hiển thị nếu policy Odoo hiện hành có quy định.
  Nhập lại mật khẩu  [input ẩn]
  Nhập giống mật khẩu mới để tránh nhầm.
  [lỗi rõ ràng ở đây]
  Tạo tài khoản / Hủy
```

Nền trắng, chữ navy#17324D, chữ phụ#526477, input border#9FB0C0,
accent teal#087F8C, lỗi#AC2525; hệ thống font Segoe/system hiện hành.
Tiêu đề20px600, nhãn14px600, input16px, chú thích13px; spacing8/16/24,
form rộng tối đa560px, một cột, mobile padding16px và footer co giãn.
Focus2px/hover180ms/reduced-motion; không trang trí dư hoặc font ngoài.

Xác thực admin trước nhập password mới; password mới chỉ ở RAM component,
không model field/context/native identity request/localStorage. Submit kiểm
native identity TTL phía server, không tự replay khi hết hạn. Backend giữ
permission/company/protected user/login/mapping/atomic create và dùng native
password hashing/policy. Đặt lại mật khẩu dùng cùng form với login readonly.

Acceptance: tạo/reset giả đúng password; empty/mismatch/short/duplicate/stale/
nonadmin/no-reauth không ghi; hủy không tạo user; pending identity request không
chứa password mới; show/hide/keyboard/mobile/error loading và Vietnamese messages.
Rà toàn bộ thông báo của luồng tài khoản/role và native confirm-password; không
tuyên bố đã dịch mọi màn hình của các addon Odoo ngoài phạm vi đã kiểm.

Kiểm cuối CHG005: input thực cao46px, Hiện/Ẩn bằng chữ rõ;3viewport1440/390/320 và focus/reduced-motion đạt cả18079/18069. Cặp ảnh cùng main/hồ sơ28 tại `.local/hr-account002/before-main-{desktop,mobile}.png` và `after-{desktop,mobile}-18069.png`. Tạo/reset/login/race chỉ trên fixture test đã loại bằng restore; người dùng duyệt hình thức riêng.
