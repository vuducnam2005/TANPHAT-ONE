# UI-INPUT-001 — Chuẩn hóa ô nhập, ô chọn và ô ngày trên giao diện native

13/11/2026, CHG-20261113-009. Yêu cầu trực tiếp: người dùng phải nhận ra ngay ô
nào sửa được, chỉ đọc, bắt buộc, đang focus hoặc có lỗi. Ô sửa được có khung đủ
4 cạnh ngay ở trạng thái thường. Chỉ đổi giao diện và khả năng sử dụng; quyền,
điều kiện readonly, xác thực, guard nghiệp vụ, trạng thái và dữ liệu giữ
nguyên. Kèm yêu cầu bổ sung: Danh sách nhân viên hiện avatar trước họ tên.
Không stage/commit/push.

## Nguyên nhân gốc

- Core `web/views/fields/fields.scss`: `.o_input` chỉ có viền dưới.
- Core `web/views/form/form_controller.scss`: viền đó trong suốt cho tới khi
  hover/focus, nên ô sửa được trông như chữ thường.
- Many2one ẩn mũi tên cho tới khi hover; ô ngày chỉ có icon lịch trên thiết bị cảm ứng.
- Các module tự viết màu viền riêng: #9fb0c0, #c4d1e2, #b6c6d5, `--kd-line`…
  Vì vậy cùng một trạng thái lại có nhiều màu.

## Token và nơi đặt

Nguồn duy nhất là [input_tokens.css](../../custom_addons/tp_web_home/static/src/inputs/input_tokens.css),
nằm trong `tp_web_home` có sẵn (không tạo addon mới). Tệp được nạp vào
`web.assets_backend` qua glob và vào `tp_web_login.assets_login` qua manifest.
Quy tắc áp vào các widget Odoo nằm ở [inputs.scss](../../custom_addons/tp_web_home/static/src/inputs/inputs.scss).

| Token | Giá trị | Tương phản trên #fff |
| --- | --- | --- |
| nền / chữ / nhãn | #FFFFFF / #172B4D / #334155 | chữ 14:1 |
| placeholder | #64748B | 4.7:1 |
| viền / viền hover | #7A8CA5 / #52627A | 3.4:1 |
| focus | #2563EB + vòng 3px rgba(37,99,235,.22) | 5.2:1 |
| lỗi | #B91C1C, nền #FFF7F7, viền trong 1px | 6.5:1 |
| chỉ đọc / vô hiệu | nền #F1F5F9 / #E2E8F0 | — |
| hình dạng | bo góc 6px, đệm ngang 10px, cao 38px, chữ 14px | — |
| <768px hoặc cảm ứng | cao 44px, chữ 16px (iOS không tự zoom) | — |

- Selector luôn gắn với `.o_form_editable`, `.o_field_widget` và `.o_input`;
  không có selector trần kiểu `input, select, textarea {}`. Không dùng hàng
  loạt `!important`.
- Ô lồng nhau (tags, autocomplete), checkbox/radio/toggle, ô file và ô trong
  danh sách không được đóng khung.
- Dưới md, khung ô có viền của Odoo m3 là khung duy nhất.
- `prefers-reduced-motion` tắt hiệu ứng chuyển.

## Danh mục màn hình

| Khu vực | Màn hình đã rà (18079) | Kết quả |
| --- | --- | --- |
| Shared | Đăng nhập; Cài đặt; hộp xác minh admin (`tp_web_login` identitycheck) | Ô mật khẩu chỉ một khung, nút mắt bên phải. Mở hộp thì trung tính, chưa báo lỗi trước khi gõ. Focus vẫn ở ô mật khẩu |
| HR | Danh sách nhân viên; hồ sơ (xem, sửa 6 tab); tạo mới 6 tab; Phòng ban, Chức vụ (list + form); Nơi làm việc, Nhãn nhân viên (mới); Nhập và đối chiếu (list + mới); Tổng quan HR; hộp Đổi chức vụ | Khung 4 cạnh. Mũi tên many2one/selection luôn hiện. Có icon lịch. Phòng ban/Chức vụ bị khóa có nền xám, căn trái. Có dấu `*` theo `required`. Danh sách hiện avatar trước tên |
| KH-KD | Tổng quan; Hồ sơ dự án/hồ sơ thầu (list, form, tab, mới); Hợp đồng (list + form); Dự án (list); Dự án mới; Báo cáo | Khung, icon lịch và ô tìm dùng token chung. Ô tiêu đề giữ cỡ chữ lớn |
| Core | Contact Tags: dòng sửa trong danh sách | Ô đang sửa có viền trong 1px, focus 2px xanh. Chiều cao dòng giữ 40.5px |

Module SCSS chuyển màu cứng sang token và bỏ khung trùng:
- `tp_hr_workspace`: employee_profile, account_credentials, employee_delete,
  overview, table, hr_ui.
- `tp_kd_workspace`: business_project, overview, report_center, tables007.
- `tp_web_login`: login.css, identitycheck.scss.

Avatar: `employee_list` dùng widget `tp_hr_identity` có sẵn cho field `name`.
Ảnh `avatar_128` native tải lazy; nhân viên chưa có ảnh dùng ảnh chữ cái mặc
định của Odoo.

## Trạng thái đã kiểm

| Trạng thái | Cách kiểm | Kết quả |
| --- | --- | --- |
| Thường / hover / focus | `hr-new-hover`, `hr-new-focus`, ô tìm | Viền #7A8CA5 → #52627A → #2563EB + vòng focus |
| Lỗi bắt buộc | HR tạo mới, bấm Lưu khi trống rồi Hủy | Viền và nền đỏ; giá trị đã gõ giữ nguyên; báo “Thiếu thông tin bắt buộc”; 0 `web_save` |
| Chỉ đọc trong chế độ sửa | Phòng ban/Chức vụ bị khóa (desktop + 390) | Nền #F1F5F9, không khung, không mũi tên |
| Dòng sửa trong danh sách | Contact Tags “Mới”, rồi Escape | Cao 40.5 → 40.5; viền trong; 0 lưu |
| Giảm chuyển động | 390, `reducedMotion: reduce` | 0 lỗi; transition none |
| Vô hiệu | Chỉ có trong CSS (`:disabled`) | Không gặp ô `disabled` trên các màn đã rà |

## Kiểm đã chạy

| Kiểm | Kết quả |
| --- | --- |
| Odoo | `tp_tanphat_test` `-u tp_hr_workspace,tp_web_home --test-tags /tp_hr_workspace,/tp_web_home`: **0 failed, 0 error(s) of 73 tests** ([log](../../.local/ui-input001/odoo-tests.log)). `test_hr_ui.py` kiểm widget `tp_hr_identity` |
| HOOT | `scripts/hr001_hoot.cjs`: `tp_hr_workspace` và `tp_web_home` **passed** |
| Tĩnh | Ruff PASS; libsass biên dịch inputs/identitycheck; `git diff --check` exit 0 (chỉ cảnh báo CRLF có sẵn) |
| Playwright 18079 | Trước/sau ở 1440, 1280, 390, 320 với cùng admin, route và dữ liệu giả. Lượt cuối (sau mọi chỉnh) ở 1440 và 390: 0 lỗi mới. Còn 2 lỗi có sẵn (xem Giới hạn) |
| Smoke main 18069 | Chỉ đọc, `READONLY=1`: trình duyệt chặn mọi `call_button`, `web_save/create/write/unlink/copy/action_*`. 1440 có 17 màn, 390 có 9 màn: **0 lỗi, 0 lệnh bị chặn** (không có lệnh ghi nào được thử) |

## Ảnh trước–sau (private, `.local/ui-input001/`)

- Trước: `shots-before-18079/` (170 ảnh, 4 viewport).
- Sau lượt đầu: `shots-after-18079/` (166 ảnh, 4 viewport). Chụp trước 3 chỉnh
  cuối: nhãn mobile, ô khóa mobile, màu viền highlight.
- Bản cuối: `shots-final-18079/` (1440 và 390).
- Trạng thái: `shots-states-18079/` (error-required, error-focus,
  search-focus, list-editable-row). `step3-fail` và `skill-type-open` là ảnh
  lượt script hỏng, không dùng làm bằng chứng.
- Giảm chuyển động: `shots-after-reduced-18079/`.
- Main: `shots-main-18069/`.
- Cặp nên xem: `hr-form-edit-1440`, `hr-new-focus-1440`, `dlg-identity-1440`,
  `kd-opportunity-new-1440`, `hr-list-390`.

## Áp main và rollback

- Version: `tp_web_home` 20.0.1.7.0, `tp_web_login` 20.0.1.4.2,
  `tp_hr_workspace` 20.0.1.11.4, `tp_kd_workspace` 20.0.1.9.1. Không
  model/ACL/schema/data.
- Backup **`.local/hr001/backup-tp_tanphat_dev-20261113T122622455720Z`**
  (601 bảng, 656 blob references, SHA1 từng blob).
- Các bước: dừng dev → `-u tp_web_home,tp_web_login,tp_hr_workspace,tp_kd_workspace
  --no-http --stop-after-init` (exit 0; 0 ERROR; còn cảnh báo `<i>` thiếu
  title có sẵn) → start 18069 → smoke chỉ đọc.
- Rollback source: `.local/ui-input001/rollback-source.zip` và
  `rollback-source.json`.
  - Gồm 18 tệp dựng lại bằng cách đảo đúng các chỉnh đã ghi.
  - Kiểm: áp lại chỉnh thì ra đúng tệp hiện tại; 9 tệp trùng HEAD.
- Cách rollback:
  1. Dừng dev.
  2. Trả 18 tệp từ zip, kiểm SHA256.
  3. Xóa `tp_web_home/static/src/inputs/`.
  4. `-u` lại 4 module `--no-http`, rồi start và smoke.
  - Không cần restore DB, vì thay đổi chỉ là asset/view.
- Không chỉ xóa `input_tokens.css`: các SCSS module dùng token không có
  fallback, xóa riêng tệp này sẽ mất viền.

## Giới hạn và phần chưa kiểm

- Lỗi có sẵn, không đổi:
  - Dự án KD: bấm dòng không mở form (survey timeout).
  - Admin không có quyền tạo `tp.contract` (AccessError ở onchange, khi mở
    hợp đồng mới).
  - Nhãn tiếng Anh: “Sex”, “Issued by Government”, “VISA & WORK PERMIT”.
  - “Họ và tên” dùng placeholder làm nhãn.
  - KD “Dự án liên quan” có 2 ô chung một nhãn; “Bên ký” hiện “—”.
- Môi trường Windows (core, không sửa):
  - `FilesystemSessionStore` đôi khi báo “user is not connected” khi có
    request song song; chạy lại thì đạt.
  - Filestore GC WinError 5 để lại 661 tệp `.__gc` trên test. 0 tệp còn
    được attachment tham chiếu, nên không mất dữ liệu.
- Chưa chụp riêng:
  - Trình soạn HTML, ô tải tệp, tags trong dialog.
  - Hộp tài khoản nhân viên (`account_credentials`) và hộp xóa nhân viên
    (đã đổi token nhưng chưa mở trên trình duyệt).
  - Dòng sửa KD sau quyền tiền; form Dự án KD.
  - Ảnh cuối 1280/320 sau 3 chỉnh mobile cuối (ảnh 1280/320 hiện có là lượt
    sau đầu tiên).
- Mobile là giả lập Chromium; chưa thử điện thoại thật, autofill extension
  hay forced-colors thật.
- Nghiệm thu giao diện và nghiệp vụ do người dùng xác nhận trên 18069 (Ctrl+F5).
