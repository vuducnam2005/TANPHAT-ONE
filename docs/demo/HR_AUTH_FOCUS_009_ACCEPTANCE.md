# HR-AUTH-FOCUS-009 — Kiểm chứng tập trung ô nhập và trình quản lý mật khẩu

**Change:** CHG-20261112-014, ngày 12/11/2026. **Trạng thái:** IMPLEMENTED_VERIFIED_MAIN_APPLIED. Không stage/commit/push.

## Phạm vi và nguyên nhân đã quan sát

Chrome 157.0.8103.51, bản Chrome cài trên máy chạy headless, đã lưu mật khẩu của tài khoản giả trên 18079. Khi mở xác thực native, trình quản lý mật khẩu tích hợp tự điền tên đăng nhập giả vào ô tìm sidebar trong khi focus vẫn ở ô mật khẩu. Evidence `.local/hr-auth-focus009/password-manager-before.json` ghi input/change trusted ở cả sidebar và mật khẩu. Đây là autofill thật, không phải kết luận suy từ focus hoặc giả lập gán value. Chỉ đổi `type="search"` không giải quyết; tách tìm kiếm thành form search riêng giải quyết trong lần kiểm này.

## Kết quả source

- `tp_hr_workspace` 20.0.1.8.1 và `tp_web_login` 20.0.1.4.1. Controller của form xác thực native đưa focus về ô mật khẩu đang enabled trước RPC nút native, để đóng lỗi trả về đúng ô nhập.
- Hook `useDialogOpener` dùng `ui.bus` trả focus về nút mở thực tế trên hồ sơ/hộp tài khoản sau đóng dialog. Form cấp tài khoản dùng native `useAutofocus`: tạo mới vào tên đăng nhập, đặt lại vào mật khẩu mới.
- Form search độc lập ngăn Chrome nhận ô tìm sidebar làm username của form xác thực; guard `onPatched` giữ quyền sở hữu focus của dialog.

Không đổi source backend/auth/nghiệp vụ, chính sách DEC-040 hoặc quyền người thật. Native check_identity, thời hạn xác thực, kiểm quyền và các action tạo/đặt lại mật khẩu giữ nguyên.

## Kiểm thực chạy

Evidence private trong `.local/hr-auth-focus009/`:

- `hoot-tp_hr_workspace.txt`: **25 tests, 105 assertions đạt**, gồm 4 test mới; tổng gồm 23 HR và 2 KH-KD được runner chọn.
- `browser-result.json`: **8 nhóm đạt, 0 console/page errors**. Có mật khẩu Chrome đã lưu; sidebar rỗng/có bộ lọc; sai mật khẩu/thử lại; đóng lỗi/Escape/mở lại; xác thực đúng; tạo tài khoản bằng Enter và đăng nhập bằng mật khẩu vừa chọn.
- Clipboard paste thật vào ô mật khẩu xác thực; phiên xác thực hết hạn chặn ghi mật khẩu. Tab/Shift+Tab 24 vòng, hủy/lưu/reset và sidebar dùng tiếp được trên desktop, rail, viewport mobile. Mật khẩu reset đăng nhập được trên nhân viên giả.

Các lượt đầu lỗi setup đã được sửa và chạy lại; chỉ lượt cuối đạt được tính vào kết quả. Fixture và thao tác tạo/reset tài khoản chỉ dùng dữ liệu giả trên `tp_tanphat_test:18079`; không đổi credential người thật.

## Backup, triển khai và giới hạn

Test backup: `.local/hr001/backup-tp_tanphat_test-20261112T114259236813Z`. Main backup trước áp: `.local/hr001/backup-tp_tanphat_dev-20261112T120334281779Z`, 600 bảng và 661 tham chiếu blob. Source trước sửa application được lưu riêng trong `.local/hr-auth-focus009/rollback-source.zip` và manifest SHA256 `rollback-source.json` (66 file). Xem [runbook](../../ops/runbooks/HR_AUTH_FOCUS_009_DEPLOY_AND_ROLLBACK.md).

**Main 18069 đã áp:** `upgrade-main.log` nạp hai addon thành công; source đối chiếu `tested-source.json` khớp. HOOT main cũng 25 tests/105 assertions đạt. `main-smoke.json` có 4 nhóm đạt/0 errors: mở/hủy/đóng xác minh ở desktop, rail, mobile; giữ bộ lọc có sẵn và trả focus; reset hủy về nút hồ sơ vì native action thay dialog quản lý. Không nhập mật khẩu xác minh hoặc tạo/reset tài khoản trên main.

`main-business-delta.json`: 9 bảng nhân viên/version/phòng/chức vụ/user/partner/role/grant/audit giữ nguyên từng cột so với backup trước áp (40 employee, 27 users). `main-grants-preservation.json`: nhóm user, grant KH-KD/dự án và role giữ nguyên rowset. Chỉ có ghi kỹ thuật phiên đăng nhập, wizard tạm, view/module/assets. Hai runtime đang nghe 18079/18069.

XML 13 file và hai manifest đạt; `node --check` các JS đổi và harness đạt; `git diff --check` đạt. Không chạy backend Odoo/React tests vì không sửa Python nghiệp vụ, auth server, REST hoặc legacy React. Fixture giả của task được giữ riêng trên test để tái kiểm, credential/profile Chrome ở `.local/`.

DEC-040 giữ nguyên: chuyển phòng có preview/xác nhận và thu hồi HEAD/quyền cũ nguyên tử theo policy; HEAD phòng đích vẫn tuân thủ một trưởng phòng. Yêu cầu một bước hạ riêng trước khi chuyển là đề xuất đổi quy trình, không phải lỗi của workflow hiện hành. Không đổi tên/ảnh/login, quyền hoặc phòng của người thật.

Kiểm password manager giới hạn Chrome tích hợp, bản cài thật chạy headless; chưa chứng minh extension hoặc mọi trình duyệt. Mobile là viewport mô phỏng, chưa thiết bị thật. Đây là technical self-verification; visual acceptance, business acceptance và pilot authorization là các cổng riêng, chưa được suy ra từ test.
