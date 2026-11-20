# tp_hr_bank — Tài khoản ngân hàng (BANK-001)

Mỗi tài khoản đăng nhập tự khai báo tài khoản ngân hàng nhận lương ngay trong
**Thông tin cá nhân**, chọn ngân hàng từ danh mục chuẩn có biểu tượng.

## Phạm vi

- **Danh mục ngân hàng** (`tp.bank`): 76 tổ chức theo danh sách thành viên
  NAPAS 247 / VietQR. Mỗi tổ chức có mã, BIN 6 số, tên viết tắt, tên đầy đủ,
  SWIFT (nếu có), biểu tượng chữ và màu nhận diện. Ví điện tử và công ty tài
  chính có sẵn trong danh mục nhưng đang ẩn.
- **Menu danh mục**: Nhân sự → Tổ chức → Danh mục ngân hàng (chỉ Quản lý Nhân
  sự). Dữ liệu nạp với `noupdate="1"`, nên nâng cấp module không ghi đè phần
  HR đã sửa (tên, màu, ẩn/hiện).
- **Thông tin cá nhân**: thẻ "Tài khoản ngân hàng" gồm thêm, sửa, gỡ, ô tìm
  ngân hàng không dấu (bàn phím, màn hình đọc), số tài khoản nhóm 4 số và
  trạng thái "Nhân sự đã xác minh" hoặc "Chờ Nhân sự xác minh".
- **Nhân viên**: tài khoản gắn vào hồ sơ nhân viên (`bank_account_ids`, liên
  hệ công việc). HR và bảng lương dùng chính danh sách này.
- **Tài khoản không có hồ sơ nhân viên**: tài khoản gắn vào liên hệ của chính
  người dùng.
- **Form tài khoản ngân hàng của HR**: thêm trường "Ngân hàng" (ô chọn có
  biểu tượng). `bank_name` và `bank_bic` (BIN, dùng cho VietQR) tự đồng bộ.

## Quy tắc an toàn

- Người dùng chỉ đọc được tài khoản ngân hàng của chính mình. Quy tắc
  `tp_hr_bank_own_account_read` mở quyền đọc theo `partner_id` của chính họ.
  Người dùng không có quyền ghi `res.partner.bank`.
- Mọi thao tác ghi đi qua `res.users.tp_save_my_bank_account` và
  `tp_remove_my_bank_account`, chạy sudo sau khi kiểm tra quyền sở hữu.
- Guard hồ sơ của `tp_admin_delegation` chỉ cho tự sửa trường trong danh sách
  cho phép. Module mở rộng `hr.employee._tp_self_service_fields()` thêm đúng
  một trường `bank_account_ids`; các trường HR khác vẫn bị chặn.
  Các trường cho phép: `bank_id`, `account_number`, `holder_name`. Gửi trường
  khác, hoặc id tài khoản của người khác, thì bị từ chối (`AccessError`).
- `allow_out_payment` (đã xác minh, được chi lương) chỉ HR bật. Tài khoản mới
  luôn ở trạng thái chưa xác minh. Đổi ngân hàng hoặc số tài khoản sẽ tắt xác
  minh; chỉ sửa tên chủ tài khoản thì giữ nguyên.
- Gỡ tài khoản: bỏ liên kết khỏi hồ sơ, rồi lưu trữ (không xóa cứng) nếu
  không còn nhân viên nào dùng. Thêm lại cùng số thì dùng lại bản ghi cũ và
  cần xác minh lại.
- Ghi chú chatter trên hồ sơ nhân viên chỉ hiện 4 số cuối (`••••1234`).
- Mỗi người tối đa 5 tài khoản. Số tài khoản 6–20 chữ số. Tên chủ tài khoản
  viết hoa không dấu.

## Rà soát giao diện "Thông tin cá nhân"

Cùng đợt BANK-001, màn hình "Hồ sơ của tôi" (`tp_hr_workspace`, chỉ tệp giao
diện tĩnh, không đổi dữ liệu) được rà soát:

- Ô chọn ngân hàng: kính lúp khi mở, đếm kết quả ("Tìm thấy 1 ngân hàng"),
  tìm theo tên, tên viết tắt, mã hoặc BIN, không dấu. Khi đóng, ô hiện tên
  viết tắt; dòng dưới hiện tên đầy đủ và BIN NAPAS.
- Quốc gia, quốc gia nơi sinh, quốc tịch và tỉnh/thành phố dùng cùng kiểu ô
  tìm kiếm (`TpSearchSelect`): gõ không dấu ("ha noi"), có đếm kết quả, chọn
  bằng chuột hoặc phím mũi tên/Enter/Esc, nút xóa lựa chọn. Tỉnh/thành phố
  báo "Chọn quốc gia trước" khi chưa có quốc gia.
- Ngày sinh, hết hạn hộ chiếu, ngày sinh vợ/chồng và ngày trong "Hồ sơ và
  năng lực" dùng bộ chọn ngày của Odoo, cố định DD/MM/YYYY ở cả chế độ xem và
  sửa (ô ngày của trình duyệt từng hiện MM/DD theo ngôn ngữ máy).
- Giá trị trống ("Chưa khai báo") hiện chữ nghiêng màu xám, khác hẳn dữ liệu
  thật. Các ô nhập có gợi ý mẫu (vd: email, số điện thoại, CCCD 12 số).
- Sửa lỗi hiển thị: ô chọn Giới tính/Tình trạng hôn nhân/Trình độ học vấn mất
  mũi tên; viền đôi khi ô tìm kiếm được chọn.

## Biểu tượng

Biểu tượng là ô chữ viết tắt trên màu nhận diện, do module tự dựng. Module
không tải logo chính thức của ngân hàng, nên không có tệp nhãn hiệu bên thứ ba
trong repo. Màu chữ trắng hoặc đen được chọn theo độ tương phản WCAG.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local\odoo.conf -d tp_tanphat_test --db-filter '^tp_tanphat_test$' -i tp_hr_bank --test-enable --test-tags '/tp_hr_bank' --stop-after-init --http-port 18079 --max-cron-threads=0
```

Test chỉ dùng dữ liệu giả (công ty, người dùng, nhân viên "Synthetic").
Test trình duyệt (`test_profile_bank_card_in_browser`) gọi
`scripts/tests/test_hr_bank_profile.cjs` (Playwright, desktop 1440 px và di
động 390 px): thẻ ngân hàng, tìm ngân hàng bằng chuột và bàn phím, bộ chọn
ngày DD/MM/YYYY, tìm quốc gia "viet" và tỉnh "ha noi", rồi bỏ thay đổi. Không
lưu gì. Ảnh chụp nằm trong `.local/hr-bank001/browser/` (không đưa lên Git).
