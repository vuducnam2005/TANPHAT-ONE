# HR-DELETE-010 — Xóa vĩnh viễn nhân viên, xác minh lại mật khẩu admin mỗi lần xóa

12/11/2026 Asia/Saigon, CHG-20261112-016. Yêu cầu trực tiếp của người dùng;
thay chính sách “chỉ xóa hồ sơ nhập nhầm” của HR-CORRECTION-008 (DEC-041) bằng
DEC-042. Kiểm trên `tp_tanphat_test:18079` với dữ liệu giả, sao lưu main và diễn
tập restore trước khi áp lên `tp_tanphat_dev:18069`. Không sửa `odoo/`/`addons/`,
không frontend riêng, không DB thứ ba, không stage/commit/push.

Tiêu chí dưới đây được viết **trước** khi triển khai; mục “Kết quả” ở cuối ghi
bằng chứng sau khi kiểm.

## 1. Luồng và nhãn

- AC-01 Admin hệ thống (cùng công ty, có quyền quản lý nhân sự) chọn một hoặc
  nhiều nhân viên ở danh sách hoặc mở chi tiết → **Tác vụ → Xóa vĩnh viễn nhân
  viên**. Người dùng khác không thấy tác vụ và gọi trực tiếp cũng bị từ chối.
- AC-02 Hộp thoại hiện: họ tên, mã TP, phòng ban, tài khoản đăng nhập, số hồ sơ;
  ba nhóm **Sẽ xóa / Giữ lại / Đang chặn** kèm lý do; ô lý do bắt buộc; cảnh báo
  đúng nguyên văn: “Hồ sơ sẽ bị xóa vĩnh viễn khỏi hệ thống. Thao tác này không
  thể hoàn tác bằng chức năng Bỏ lưu trữ.”
- AC-03 Ô mật khẩu của chính admin đang đăng nhập (ẩn mặc định, có nút hiện/ẩn,
  không có ô tên đăng nhập admin khác). Nút đỏ **Xác nhận xóa vĩnh viễn** và nút
  **Hủy**. Có trạng thái đang xử lý; không chồng nhiều modal; dùng được bằng bàn
  phím và trên mobile; sidebar không đổi.
- AC-04 Thành công: đóng hộp thoại, thông báo số hồ sơ đã xóa, nạp lại danh sách
  (từ chi tiết thì quay về danh sách nhân viên).
- AC-05 Sai mật khẩu: không thay đổi dữ liệu, báo lỗi tiếng Việt, xóa ô mật khẩu
  và đưa focus về ô mật khẩu. Thiếu lý do/mật khẩu: báo ngay, không gọi xóa.
- AC-06 **Hủy**: không ghi gì (không audit, không khóa tài khoản).
- AC-07 Lô nhiều hồ sơ: một lần xác nhận; tất cả hoặc không có hồ sơ nào bị xóa.
- AC-08 **Lưu trữ** vẫn là thao tác riêng, giữ nguyên tên; không tự đổi xóa thành
  lưu trữ hay ngược lại.

## 2. Xóa thật

- AC-10 Sau khi xóa, `hr.employee` không còn trong DB: không có trong danh sách
  thường, danh sách đã lưu trữ (`active_test=False`), tìm kiếm, export, bộ đếm và
  dashboard HR.
- AC-11 Không chặn chỉ vì hồ sơ nhập từ Excel, có mã nguồn, có version/resource/
  avatar/log tự sinh hoặc có trao đổi trên chính hồ sơ.
- AC-12 Không còn bản ghi mồ côi: version, kỹ năng, quá trình công tác, resource,
  chatter/follower/hoạt động/lịch hẹn gửi, tệp đính kèm và `ir.model.data` của
  hồ sơ và của các bản ghi kèm theo đều bị xóa qua ORM (blob dùng chung để GC của
  Odoo xử lý, không xóa file vật lý trực tiếp).

## 3. Xác minh lại mật khẩu mỗi lần xóa

- AC-20 Backend kiểm: `base.group_system`, `hr.group_hr_manager`, phạm vi công ty
  đang làm việc, phiên hợp lệ của đúng người gọi, mật khẩu thuộc tài khoản đang
  đăng nhập. Không nhận cờ `is_admin`/context từ frontend.
- AC-21 Mỗi yêu cầu xóa đều kiểm mật khẩu vừa nhập, kể cả ngay sau khi vừa xác
  minh danh tính native (10 phút) hoặc vừa xóa hồ sơ khác. Không dùng
  `@check_identity`, không đọc/ghi `identity-check-last`.
- AC-22 Dùng `_check_credentials` + giới hạn thử sai `_assert_can_auth` của Odoo;
  không tự so hash. Quá số lần sai: báo chờ, không xóa.
- AC-23 Mật khẩu chỉ ở state hộp thoại và tham số request; không vào transient
  model, DB, context chờ, localStorage, URL, audit, log, screenshot/trace. Xóa
  khỏi state khi đóng/kết thúc.
- AC-24 Kiểm mật khẩu và xóa trong cùng một request cuối.
- AC-25 Hành vi HR-AUTH-FOCUS-009 giữ nguyên (sidebar, autofill, focus, Tab).

## 4. Quan hệ dữ liệu

| Model/quan hệ | Xóa cùng | Giữ | Chặn | Lý do |
|---|---|---|---|---|
| `hr.version` (employee_id, cascade) | ✓ | | | Lịch sử phiên bản thuộc riêng hồ sơ; chatter/tệp/xmlid của version được quét qua ORM |
| `resource.resource` của hồ sơ | ✓ | | | Native `hr.employee.unlink` xóa resource riêng |
| `hr.employee.skill`, `hr.resume.line`, `hr.employee.location`, `hr.employee.departure`, nhãn nhân viên (rel) | ✓ | | | Dữ liệu con cascade, chỉ thuộc hồ sơ; tệp chứng chỉ quét qua ORM |
| Chatter, follower, hoạt động, lịch gửi, tệp đính kèm, `ir.model.data` của hồ sơ | ✓ | | | Cơ chế native `mail.thread`/`BaseModel.unlink` |
| Partner liên hệ công việc | ✓ nếu không còn dùng | ✓ nếu còn dùng | | Giữ khi gắn tài khoản hoặc còn tham chiếu khác (chứng từ, tin nhắn...) |
| `tp.hr.import.line.employee_id` | | ✓ (set null) | | Giữ dòng nhập, mã nguồn, tên/phòng ban gốc; audit ghi lô/dòng |
| `tp.hr.import.batch`, file Excel | | ✓ | | Không xóa lô/file vì xóa một nhân viên |
| Tài khoản `res.users` | | ✓ mặc định | ✓ nếu tài khoản hệ thống/admin/chính mình/portal/công ty khác/gắn hồ sơ khác | Tùy chọn “Xóa hồ sơ và khóa tài khoản”: khóa bằng cơ chế sẵn có, kết thúc phiên, thu hồi HEAD/phân công/quyền dự án/nhóm phạm vi |
| Vai trò HEAD/phân công/quyền KD khi **không** khóa tài khoản | | | ✓ | Phải chọn khóa tài khoản hoặc hạ quyền trước; không để quyền treo |
| Công việc đang chờ của tài khoản (task, lead, hồ sơ trình...) | | ✓ (cần bàn giao) | | Không đổi owner/reviewer tự động |
| Nhân viên khác có Quản lý/Huấn luyện viên là hồ sơ này | | | ✓ | Đổi người quản lý/huấn luyện trước |
| `hr.department.manager_id` | | | ✓ | Đổi trưởng phòng trước |
| Chấm công/timesheet, chi phí, nghỉ (resource leaves), tuyển dụng, mẫu hợp đồng dùng ở hồ sơ khác | | | ✓ | Dữ liệu nghiệp vụ độc lập; dùng Lưu trữ |
| Tham chiếu lưu trữ khác chưa biết (m2o/m2m/many2one_reference) | | | ✓ | Báo model, số bản ghi, cách xử lý |

- AC-30 Không gỡ FK, không thêm DELETE CASCADE, không đổi owner/reviewer, không
  báo “đã xóa” khi bị chặn.
- AC-31 Không xóa tài khoản; không xóa tài khoản hệ thống/root/admin/chính mình;
  không khóa tài khoản không được chọn.
- AC-32 Nhập lại Excel có mã nguồn hoặc mã TP của hồ sơ đã xóa: dòng thành
  **xung đột cần đối chiếu**, không tự tạo lại; mã TP đã xóa không bao giờ cấp lại.

## 5. Thực thi và audit

- AC-40 Trước khi xóa: khóa advisory theo công ty, khóa dòng `FOR UPDATE`, tính
  lại kế hoạch và so digest với bản xem trước; dữ liệu đổi sau xem trước (liên
  kết mới, tài khoản/vai trò đổi) → từ chối, không ghi gì.
- AC-41 Mọi lỗi giữa chừng rollback toàn bộ (audit, khóa tài khoản, xóa).
- AC-42 Gửi lại/bấm hai lần cùng `request_id`: không xóa lần hai, không trùng
  audit (unique `request_id` + hồ sơ).
- AC-43 Audit bền vững `tp.hr.employee.audit` (`permanent_delete`): admin, thời
  điểm, ID/mã, tên tối thiểu, mã nguồn, lý do, phạm vi (số bản ghi xóa/giữ, tài
  khoản giữ/khóa, quyền thu hồi), kết quả xác minh mật khẩu (không lưu mật khẩu),
  request ID. Không chép thông tin cá nhân khác.

## 6. Kiểm thử bắt buộc (18079, dữ liệu giả)

Xóa hồ sơ nhập tay và hồ sơ roster; kiểm `active_test=False`; sidecar; không mồ
côi. Mật khẩu đúng/sai/trống; hỏi lại ngay sau xác minh native và sau một lần
xóa. User thường, HR manager, HEAD không admin, admin công ty khác bị từ chối;
RPC/context giả không vượt; Hủy không ghi; không lộ mật khẩu. Blocker có giải
thích; lô hỗn hợp không xóa một phần; rollback giữa chừng; preview cũ bị từ chối;
đồng thời/retry/double-click; chỉ khóa tài khoản đã xác nhận; mã không cấp lại;
nhập lại không tạo lại. Hồi quy: tạo/đặt lại tài khoản, khóa/mở, chuyển phòng/
HEAD, sidebar/autofill/focus, danh sách/dashboard/export/bộ đếm, tài liệu dùng
chung. Công cụ: Ruff, test Odoo, XML/asset/HOOT/Playwright, `git diff --check`.

## 7. Kết quả

Phiên bản: `tp_organization` 20.0.2.2.0, `tp_hr_workspace` 20.0.1.9.0. Bằng chứng
chỉ ở `.local/hr-delete010/` (không vào Git). Chỉ lượt cuối của mỗi bài được tính
đạt; các lượt lỗi liệt kê riêng bên dưới.

### 7.1 Test 18079 (dữ liệu giả)

- **Odoo** `/tp_organization,/tp_hr_workspace`: **74 tests, 0 failed, 0 error**
  (`test-run-4.log`, chạy sau lần sửa source cuối). Dòng ERROR “bad query” là test
  ràng buộc duy nhất cố ý; traceback WinError 5 khi dọn GC là nhiễu môi trường.
- **Ruff**, XML/manifest, `git diff --check`: đạt.
- **HOOT**: `@tp_hr_workspace` **33 tests / 149 assertions**; hồi quy
  `@tp_web_home` (sidebar/autofill/focus 009) **30 tests / 173 assertions**.
- **Playwright** (Chrome headless, tài khoản admin giả `hr010.admin`, lượt dữ liệu
  giả thứ 3): **30/30 bước đạt, 0 lỗi console/page** (`delete-flow.json`, ảnh
  `shots/`, không ảnh nào có mật khẩu). Phủ: menu tác vụ (không còn Delete native),
  tiêu đề/cảnh báo nguyên văn/danh tính/số hồ sơ, Sẽ xóa/Giữ lại/Đang chặn, mật khẩu
  ẩn mặc định và Hiện/Ẩn, Tab ×12 giữ focus trong hộp thoại, Escape/Hủy không gửi
  yêu cầu, thiếu lý do/mật khẩu báo đúng ô, sai mật khẩu (lỗi tiếng Việt, xóa ô và
  focus lại, không xóa), mật khẩu không có trong URL/localStorage/sessionStorage/
  cookie, xóa đúng bằng Enter, hồ sơ biến mất khỏi danh sách và tìm kiếm đã lưu trữ,
  lô có hồ sơ bị chặn (model/số lượng/gợi ý, nút đỏ tắt, không xóa phần nào), tài
  khoản giữ bị chặn khi còn quyền → chọn “Xóa hồ sơ và khóa tài khoản”, lô 2 hồ sơ
  cùng một xác nhận, hồ sơ đã lưu trữ xóa được và form quay về danh sách, dữ liệu đổi
  sau xem trước bị từ chối kèm “Xem trước lại”, mobile 390px nút ≥44px không tràn.
- **Đối chiếu DB sau trình duyệt** (`verify-flow.txt`, chỉ đọc): 5 hồ sơ đã xóa
  không còn kể cả `active_test=False`; 0 resource/version/tin nhắn/tệp/follower mồ
  côi; hồ sơ “Chỉ hủy” và quản lý còn nguyên. Tài khoản chọn khóa: còn tồn tại,
  `active=False`, `tp_hr_locked`, `tp_lock_revision=1`, bỏ nhóm phạm vi KD, partner
  giữ; vai trò HEAD giả `active=False`. 5 dòng audit `permanent_delete` có người
  thực hiện, request ID, kết quả xác minh; lô 2 hồ sơ chung một request; **0 dòng
  audit và 0 tham số cấu hình chứa mật khẩu**; mã TP đã xóa không có ở hồ sơ sống
  và mốc cấp mã lớn hơn mã đã xóa.

### 7.2 Lượt lỗi không tính đạt

| Lượt | Kết quả | Nguyên nhân | Xử lý |
|---|---|---|---|
| Odoo 1 | 1 failed, 2 error / 74 | Test giới hạn thử sai (ngưỡng native 10 lần/60s) đọc sai khóa lỗi; thiếu `flush_all` nên dòng nhập chưa thấy khi lập kế hoạch; test chặn quan hệ độc lập (gợi ý Huấn luyện viên) sai kỳ vọng | Sửa test/plan |
| Odoo 2 | 0 failed, 2 error / 74 | `set_param` không có ở Odoo 20 (dùng `set_int`); audit thiếu khóa `import_lines` | Sửa test/plan |
| Odoo 3 | 0 failed, 1 error / 74 | Chuỗi dịch dùng placeholder tên `source` trùng tham số của `Environment._()` | Đổi thành `source_code` |
| HOOT 1 | Test sai mật khẩu lỗi | Helper `edit()` tự nhấn Enter nên form gửi trước khi test bấm nút (ứng dụng đúng: Enter là xác nhận) | Test dùng `confirm:false`/`"enter"` rõ ràng |
| Trình duyệt 1 | 16/19 rồi dừng | Harness đọc `tp.kd.department.role` bằng admin giả không có quyền; vài bước đọc DOM trước khi OWL vẽ | Kiểm qua audit, thêm chờ `until()`; tạo bộ dữ liệu giả mới |
| Trình duyệt 2 | 27/27 rồi dừng | Ở 390px ô tìm kiếm Odoo bị ẩn nên không mở được hộp thoại | Mở hộp thoại rồi mới thu viewport; tạo bộ dữ liệu giả mới |

### 7.3 Backup và diễn tập restore (main → test)

- Backup main A (dừng đúng runtime dev, 0 phiên):
  `backup-tp_tanphat_dev-20261112T141132721082Z`. Backup test trước khi ghi đè:
  `backup-tp_tanphat_test-20261112T141211113291Z`.
- Restore A vào **test** (không DB thứ ba): **600 bảng, 661 blob, 432 sequence**
  khớp, neutralize trước khi mở HTTP (cron, mail server, uuid, base URL).
- Upgrade bản sao: 0 ERROR; **74 tests, 0 failed, 0 error** (`rehearsal-tests.log`).
- So từng dòng trước/sau upgrade (`rowdiff-rehearsal.json`, `dumpcmp-rehearsal.json`):
  23 bảng đổi, **chỉ metadata** (ir_model*/ACL/action/menu/view/nhóm); 1 tin nhắn
  “Access created” của ACL wizard cũ bị gỡ cùng ACL, 1 tracking đổi tên server
  action; 1 dòng audit 008 có thêm cột mới rỗng. Không đổi dữ liệu nghiệp vụ.
  Hai bảng wizard 008 còn lại (mỗi bảng 1 dòng tạm), giữ nguyên.
- Thống kê chỉ đọc trên bản sao main (`eligibility-tp_tanphat_test.json`, rollback):
  40 hồ sơ (40 đang dùng, 7 có tài khoản); **0 bị chặn bởi dữ liệu độc lập**; 33
  xóa được (không tài khoản), 3 xóa được và giữ tài khoản, 4 phải chọn “Xóa hồ sơ
  và khóa tài khoản” (tài khoản còn trong nhóm kinh doanh, 1 còn là trưởng phòng/
  ban). 39 hồ sơ có dòng nhập Excel sẽ được giữ.
- Smoke chỉ đọc trên bản sao (thử script trước main): 8/8 đạt.

### 7.4 Áp main 18069

- Dừng đúng runtime dev, 0 phiên main. Backup cuối B:
  `backup-tp_tanphat_dev-20261112T141836737342Z` (600 bảng, 661 blob ref). So
  dòng A ↔ ngay trước upgrade: **0 thay đổi**.
- Upgrade `tp_organization,tp_hr_workspace` với `--no-http`: exit 0, 0 ERROR; cảnh
  báo giống hệt diễn tập và có từ trước (`main-upgrade.log`).
- So dòng trước/sau (`rowdiff-main.json`): cùng 23 bảng, cùng số thêm/bớt/đổi như
  diễn tập. Khác duy nhất `ir_model_fields_selection`: 35 dòng đổi so với 34, đều là
  thứ tự múi giờ `res.partner.tz` do core Odoo sắp lại (34 dòng) và 1 dòng `action`
  của audit; 5 lựa chọn mới giống diễn tập. Không đổi dữ liệu nghiệp vụ.
- Smoke chỉ đọc bằng admin (`main_smoke.cjs`, `main-smoke.json`): **8/8 đạt, 0 lỗi
  console/page**. Menu Tác vụ có “Xóa vĩnh viễn nhân viên” và “Lưu trữ”, không còn
  “Xóa hồ sơ nhập nhầm”/Delete; hộp thoại TP10001 đủ tiêu đề, cảnh báo nguyên văn,
  Sẽ xóa/Giữ lại; ô mật khẩu rỗng, ẩn, `current-password`; lô 2 hồ sơ; menu nhật ký
  chỉ đọc. **Không nhập mật khẩu, không bấm nút đỏ**; yêu cầu xóa bị chặn cứng ở
  trình duyệt: 0 lần gửi, 2 lần xem trước.
- So dòng sau smoke (`rowdiff-main-smoke.json`): chỉ phiên đăng nhập/bus/presence/
  device log và 3 bundle asset tạo lại. Main: **40 hồ sơ, 27 tài khoản (8 đang
  dùng), 1 dòng audit, 0 dòng `permanent_delete`** — không xóa/khóa hồ sơ hay tài
  khoản thật nào.
- Cả hai runtime đang chạy (18079, 18069). DB test hiện là bản sao main đã
  neutralize ở phiên bản 010; bộ dữ liệu giả 1–3 đã mất theo restore
  (`fixture.json` chỉ còn giá trị lịch sử).

### 7.5 Giới hạn và việc chưa làm

- Chưa phủ: extension quản lý mật khẩu, trình duyệt khác Chrome, mobile vật lý,
  module nghiệp vụ chưa cài (chấm công/chi phí/nghỉ/tuyển dụng): được chặn qua quét
  quan hệ chung nhưng chưa có dữ liệu thật để thử. Visual/business/pilot riêng.
- Hai bảng wizard 008 còn trong DB (không DROP thủ công; rollback 008 dùng lại).
- Quy tắc “phải hạ trưởng phòng trước khi chuyển” (gap của 008) **chưa bắt đầu**.
- Không stage/commit/push.
