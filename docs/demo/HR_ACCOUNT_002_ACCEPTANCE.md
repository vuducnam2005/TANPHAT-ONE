# HR-ACCOUNT-002 — Form tài khoản và thông báo tiếng Việt

12/11/2026, CHG-20261112-005. Phản hồi trực tiếp sau HR-ACCOUNT-ROLE-001;
tiếp tục quyền triển khai/test/backup-restore/áp main trong task. Technical
verification tách khỏi người dùng duyệt hình thức/nghiệp vụ và cho phép pilot.

## Hành vi

- Xác thực admin native trước. Hộp xác thực và sai mật khẩu giải thích bằng
  tiếng Việt: dùng mật khẩu tài khoản đang đăng nhập.
- Form OWL một cột có ba ô **Tên đăng nhập / Mật khẩu mới / Nhập lại mật khẩu**;
  mỗi ô có nhãn, input cao 46px, chú thích, focus; có Hiện/Ẩn, lỗi inline,
  Đang lưu, Tạo tài khoản/Hủy. Đặt lại cùng form, tên đăng nhập chỉ đọc.
- User, mật khẩu, mapping, audit cùng transaction; hủy không tạo user.
  Quyền/company/protected user/unique/retry/concurrency giữ backend;
  hash và policy Odoo giữ nguyên, không đổi policy độ dài runtime.
- Password mới chỉ ở RAM và RPC submit; không field transient, context,
  localStorage, yêu cầu identity chờ hoặc chatter. Server kiểm session native
  600 giây, không tin context RPC giả xác thực; hết hạn mở lại, không tự replay.
- Việt hóa thông báo luồng tài khoản/mật khẩu/quyền/xác thực; preview giữ phạm
  vi nghiệp vụ/phòng/dự án. Chưa kiểm kê dịch mọi addon/màn hình Odoo khác.

## Bằng chứng private

`.local/hr-account002/` bị Git ignore, chứa fixture/log/ảnh có dữ liệu cá nhân:

| Kiểm tra | Kết quả |
| --- | --- |
| Odoo trước restore | `backend-reviewed.log`: 28 ca, 0 failed/0 errors; create/duplicate/retry/rollback/password validation/noHTTP, reset/audit rollback và HR/role/lock/login/TOTP/CSRF |
| Browser | `browser-result.json`: 8 nhóm đạt, 0 console/pageerror; no-reauth/forged context deny, native wrong-password Việt, inputs/keyboard/reduced/validation/Hiện-Ẩn/cancel/duplicate/loading, create/login/reset/old-password deny/staff deny, hai race cùng employee/cùng login và retry |
| Password persistence | `secrets-result.json`: không password column trên account wizard, không password mới trong identity request/chatter, native hash khác plaintext |
| HOOT | HR18+2dependency=20tests/83assertions; Home28+1dependency=29tests/166assertions đạt |
| Ảnh cuối | `before-main-desktop.png`, `before-main-mobile.png` → `after-desktop-18069.png`, `after-mobile-18069.png`: cùng admin/hồ sơ28/dataset/main/1440×1100 và390×1100; chỉ mở/hủy, không tạo/reset người thật |
| Source rollback | `rollback-source.zip/json`: 46 file gốc SHA256 khớp; `rollback-new-files.json`: 7 file mới; không reset dirty worktree |

Ảnh desktop/mobile đã mở tự đánh giá. Lỗi OWL4 t-model, modal chồng và matcher/
timing harness đã sửa rồi chạy lại; không tính lượt fail là pass. GC assets
WinError5/markdown2 warning Windows còn; kiểm blob riêng. Chưa có audit độc lập
(subagent lỗi model kế thừa không khả dụng), chưa điện thoại vật lý. Không chạy
React vì không đổi React/API. Kết quả restore/final/apply ghi ở PROJECT_STATUS
và runbook; thao tác hiện hành theo [guide](HR_ACCOUNT_ROLE_001_USER_GUIDE.md).

## Restore và áp dụng cuối

Rehearsal backup main `20261112T041738740882Z`: restore test596rowsets/
643blobrefs/429sequences khớp và neutralize trước HTTP. Odoo source cuối sau
restore: `backend-restored.log`28ca0failed0errors; HOOT20/29 đạt lại. Clean UI
`smoke-18079.json` và main `smoke-18069.json`: xác thực Việt/label rõ/một modal,
1440×1100/390×1100/320×844, focus/nooverflow/hủy giữ chưa có tài khoản,0errors.

Main dừng đúng PID/config, backup cuối
`.local/hr001/backup-tp_tanphat_dev-20261112T042518138326Z`, upgrade HR20.0.1.3.0
và login20.0.1.4.0 noHTTP/no seed; restart/read-only smoke đạt. Cả2cổng giữ
39nhân viên/27users/13phòng ban/7mappings/1HEAD theo baseline thực tế đầu lượt;
79bảng nghiệp vụ/quyền và617nonassetblob khớp, groups/implied/company giữ nguyên, ACL policy giữ (2 dòng đổi write metadata do upgrade). Mốc CHG004 ghi26users/6mapping/612blob là lịch sử; baseline private
trước lần sửa follow-up đã có27/7/617, không phải do migration lượt này tạo.
Fixture giả đã loại bằng restore. Không đổi tài khoản/mật khẩu/mapping/role
người thật, không stage/commit/push. Source seal53file khớp sau main.

Ảnh `before-*`/`after-*` không kèm `main` hoặc cổng là khảo sát trên test trước
restore, khác dataset sạch về mapping của hồ sơ63; chỉ dùng cặp main ở trên
để so sánh cuối. Lượt smoke đầu sau restore dùng nhầm hồ sơ đã có tài khoản và
inventory cũ hard-code26/6 đã được đối chiếu baseline/hash rồi sửa harness;
không thay dữ liệu để làm test đạt.
