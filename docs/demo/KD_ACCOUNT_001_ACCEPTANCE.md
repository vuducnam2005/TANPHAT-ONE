# KD-ACCOUNT-001 — Tài khoản trong thanh bên KH-KD

Ngày 08/11/2026, Asia/Saigon; CHG-20261108-004. Yêu cầu trực tiếp từ người dùng và ảnh thanh bên: thêm **Tài khoản** ngay trên **Tùy chọn hiển thị**, bấm để chỉnh hồ sơ cá nhân. Ảnh là tham chiếu vị trí, không là lệnh thay đổi dữ liệu hoặc quyền.

## Hành vi và cách dùng

1. Mở [KH-KD trên dev 18069](http://127.0.0.1:18069/odoo/action-tp_kd_workspace.action_overview); Ctrl+F5 nếu còn tài nguyên cũ.
2. Bấm **Tài khoản** ở cuối thanh bên, phía trên **Tùy chọn hiển thị**. Khi thu gọn, dùng biểu tượng người; điện thoại mở **Menu KH-KD** trước.
3. Hộp hồ sơ của chính người đăng nhập có ảnh đại diện, tên, email, điện thoại; các thẻ **Tùy chọn**, **Lịch**, **Bảo mật** theo Odoo đang cài.
4. **Cập nhật tùy chọn** lưu và nạp lại giao diện theo Odoo; **Hủy bỏ** bỏ thay đổi. Nên lưu hồ sơ nghiệp vụ đang làm trước khi lưu tùy chọn cá nhân.
5. Đổi mật khẩu trong **Bảo mật → Đổi mật khẩu**; Odoo có thể yêu cầu xác nhận danh tính. Lượt triển khai này không đổi mật khẩu.

Dùng cùng callback `preferencesItem()` của menu người dùng Odoo, lấy action native rồi gắn `user.userId`; không có màn hồ sơ tự xây hoặc nhóm quyền mới. Giữ màu navy `#17324d`, chữ `#dce6f0`, accent `#7fb3d5`, font/kích thước/focus/rail có sẵn; không thêm SCSS. Menu điện thoại đóng trước khi mở hộp hồ sơ.

## Tiêu chí và bằng chứng

| Tiêu chí | Actor / thao tác | Bằng chứng |
| --- | --- | --- |
| Vị trí, tên và bố cục | Năm vai trò KH-KD + quản trị; desktop 1440×1000 | Ảnh cùng actor/dataset/route trước và sau; bounding box và accessible name |
| Đúng hồ sơ | Mở bằng Enter, đọc profile, mở thẻ Bảo mật | Request `res.users.web_read` chỉ đúng UID hiện hành; không có trường sửa nhóm quyền |
| Responsive | Rail và mobile 390×844 | Nút hoạt động, không tràn ngang, drawer/backdrop đóng, focus trong modal và trả về Menu KH-KD |
| Lưu/hủy | Chỉ support trên clone | Sửa phone rồi hủy; lưu/mở lại và khôi phục giá trị gốc bằng UI, có finally khôi phục nếu assertion lỗi |
| Giữ nội dung đang sửa | Chỉ clone; tạo form chứng chỉ chưa lưu, mở/hủy tài khoản | Giá trị tên form vẫn nguyên; không bấm lưu hồ sơ |
| Hồi quy | Mọi actor | Tùy chọn hiển thị còn mở, rail/menu/route và nút đổi mật khẩu native hoạt động |
| Bảo toàn dev | Upgrade riêng addon; browser chỉ đọc và hủy | Rowset account/password/assignment/grant/nghiệp vụ và attachment/nhóm/module trước–sau |

Source thay đổi: `custom_addons/tp_kd_workspace/static/src/sidebar/sidebar.js`, `sidebar.xml`, manifest `20.0.1.5.2`. Không đổi model/security/workflow/API/schema. Source ứng dụng sửa trên clone cô lập trước; exact hash test/seal/apply, baseline guard tránh ghi đè thay đổi khác. Không commit/push.

Tooling `scripts/kd_account001.py` tái sử dụng chuỗi snapshot/restore/backup/apply hiện có; `scripts/kd_account001_ui.cjs` có guard không lưu profile trên dev, redaction mật khẩu trong lỗi Playwright. Credential dùng private file sẵn có, không lưu vào tracked source/tài liệu. Artifact, log, ảnh, dump/config chỉ trong ignored `.local/kd-account001/`.

## Kết quả cuối

- Clone: Odoo **45/45**, browser **107** kiểm tra/6 actor, 0 failure/0 error; ảnh đã mở kiểm. Log test `20261108T133821061090Z`, kết quả `.local/kd-account001/clone-browser.json`.
- Backup `backup-pre-apply-20261108T135314Z`: **116 checksum, 576 bảng, 294 attachment reference**, verified. Dev upgrade chỉ workspace rc0/0error/`changed_tables {}`; SQL installed `20.0.1.5.2`, source khớp exact seal.
- Dev browser **103** kiểm tra/6 actor, 0 failure/0 error, chỉ mở/xem/hủy. Sau browser **37 bảng/3.416 dòng**, 282 attachment ngoài asset, 93 module và 5 bảng nhóm giữ nguyên; 294 reference/110 blob unique checksum/kích thước đạt, 181 file addon khác nguyên. Password/assignment/grant giữ.
- Dev listener18069 PID21080 (wrapper30472), PG55432 PID4228 giữ; clone19089 đã dừng, DB/source/evidence giữ. Ruff, JS syntax, XML và diff kiểm đạt; workflow finish/check bàn giao cùng lượt.

## Vận hành và giới hạn

Clone owned: `tp_tanphat_kdaccount001_20261108`, cổng 19089; source/config/filestore riêng, mail/cron neutralized. Snapshot phục hồi đúng 576 bảng/294 attachment reference trước thay đổi. Dev đích `tp_tanphat_dev`, cổng 18069/PG55432. Backup verified trước áp bắt buộc dưới 15 phút; chỉ restart Odoo dev.

Chạy lại: `.venv\Scripts\python.exe -X utf8 scripts/kd_account001.py test` khi clone dừng; `start`, sau đó `node scripts/kd_account001_ui.cjs clone`. Browser dev dùng `node scripts/kd_account001_ui.cjs dev` chỉ mở/xem/hủy. `seal` yêu cầu source Odoo test = browser test; `backup` rồi `apply` kiểm fresh backup/seal/baseline. Rollback delta source/assets: `scripts/kd_account001.py rollback`, chỉ addon này từ snapshot owned rồi upgrade; không restore toàn DB hoặc thay user/grant.

Code và tooling đã được subagent review độc lập trong lượt này; kiểm runtime do phiên chính thực hiện. Chromium desktop/mobile mô phỏng, chưa thiết bị thật/Safari. Các audit UI cũ, business acceptance, Q2 và pilot giữ riêng.

Lượt browser thăm dò đầu có báo hết phiên khi điều hướng full page sau reload; log có transient tương tự trước thao tác lưu, chưa có bằng chứng do profile hoặc thay đổi mới. Lượt thử chặn service worker gây lỗi đăng ký native nên không dùng làm gate. Dùng lại service worker bình thường và chuyển qua link sidebar native như người dùng. Không sửa core Odoo để che hiện tượng này; giữ log private để đối chiếu.

Kết quả chạy cuối và backup/apply được ghi trong `PROJECT_STATUS.md` cùng nhật ký CHG-20261108-004. Next: người dùng kiểm vị trí/nội dung hồ sơ trên dev và phản hồi hình thức.
