# TANPHAT ONE — Quy chuẩn thông báo thông tin còn thiếu khi thêm mới/lưu

Ngày: 19/11/2026. Task `FORM-VALIDATION-001`, CHG-20261119-023; mở rộng
`FORM-VALIDATION-002`, CHG-20261119-027 (thao tác xóa/sắp xếp/mở trong màn tự viết).
Trạng thái: **đã triển khai cho mọi form native, các form tùy biến HR và các thao tác
ghi ở mục 6**; phần còn lại ghi rõ ở mục 7, không coi là đã đạt.

## 1. Mục tiêu

Thay toast chung “Thiếu thông tin bắt buộc” (tự biến mất, không nói thiếu gì) bằng
một khối lỗi nằm trong form, nói rõ **thông tin nào, ở tab/nhóm nào, sửa thế nào**,
bấm vào để đi tới đúng ô. Dữ liệu đã nhập luôn được giữ. Giao diện chỉ trình bày
trạng thái hợp lệ mà Odoo đã tính; không tự quyết định ô nào bắt buộc, không thay
quy định nghiệp vụ, không thêm giá trị giả để vượt kiểm tra. Backend vẫn kiểm tra
mọi lần lưu và là nguồn quyết định cuối cùng.

## 2. Nguồn lỗi (không danh sách cứng)

| Nguồn | Lấy từ | Ghi chú |
|---|---|---|
| Thiếu bắt buộc | `Record._unsetRequiredFields` sau `_checkValidity` | `required` trên field hoặc view, kể cả biểu thức theo bản ghi |
| Sai định dạng | `Record._invalidFields` do widget không parse được | ngày, số, chuỗi có định dạng |
| Bảng con | các dòng x2many có `_invalidFields` | Odoo chỉ kiểm dòng đầu lỗi; presenter kiểm thêm các dòng đã sửa khác |
| Từ chối khi lưu | lỗi RPC của `web_save`/`create`/`write` | giữ nguyên câu chữ backend |

`boolean`, `integer`, `float`, `monetary`: Odoo không coi 0/False là thiếu, nên
presenter cũng không đánh `*` và không báo thiếu cho các loại này.

## 3. Cách trình bày

- **Khối tổng hợp** đầu `.o_form_sheet` (`role="alert"`): “Chưa lưu được. Vui lòng
  kiểm tra N thông tin:” rồi từng dòng `Nhãn — Tab / Nhóm` + cách sửa. Câu cuối:
  “Dữ liệu đã nhập được giữ nguyên.” Khối chỉ cuộn vào tầm nhìn một lần cho mỗi lần
  lưu lỗi, không cướp focus.
- **Nhãn** là nhãn người dùng đang thấy: `<label for string>` hiển thị trước, rồi
  `string` của node view, cuối cùng mới là `string` model. Không hiện tên kỹ thuật.
- **Vị trí** ghép từ các `page`/`group` có `string`; không có thì “Thông tin chung”.
- **Bảng con**: `Chứng chỉ — dòng 2: Tên chứng chỉ`. Bấm vào mở tab, đưa dòng vào
  chế độ sửa (bảng editable) hoặc mở popup dòng, rồi focus đúng cột.
- **Tại ô**: khung đỏ (UI-INPUT-001 `.o_field_invalid`), câu lỗi `.tp_validation_inline`
  dưới ô, `aria-invalid="true"`.
- **Tab**: số lỗi `.tp_validation_count` trên tab chứa lỗi (kèm chữ ẩn “lỗi cần sửa”).
- **Dấu `*`**: chỉ trên nhãn của ô thực sự bắt buộc, đang sửa được, không phải số/
  boolean. Ô readonly, tự sinh hoặc ẩn không có `*`. Form mới có một dòng giải thích
  `*` cho tới khi có lỗi.
- **Cập nhật trực tiếp**: sau lần lưu lỗi đầu, sửa ô nào thì dòng lỗi đó biến mất
  ngay; không cần bấm lưu lại. Lưu thành công hoặc hủy thì xóa trạng thái lỗi.
- **Không nhảy focus lặp lại**: focus chỉ di chuyển khi người dùng bấm vào một lỗi.
- **Popup/wizard/quick-create**: khối lỗi nằm trong popup, popup giữ nguyên khi lỗi.
- **Mobile**: cùng khối lỗi, xuống dòng theo bề rộng; không tràn ngang.

## 4. Câu chữ theo loại lỗi

| Trường hợp | Câu |
|---|---|
| Thiếu chuỗi | Vui lòng nhập {Nhãn}. |
| Thiếu lựa chọn/ngày/quan hệ | Vui lòng chọn {Nhãn}. |
| Bảng bắt buộc trống | Vui lòng thêm ít nhất một dòng {Nhãn}. |
| Bảng có dòng lỗi | Bảng {Nhãn} có dòng chưa hợp lệ. Mở bảng để kiểm tra các dòng được đánh dấu. |
| Ngày sai định dạng | Ngày chưa đúng định dạng. Vui lòng nhập lại theo mẫu ngày đang dùng hoặc chọn trong lịch. |
| Số sai | Vui lòng nhập {Nhãn} là số hợp lệ. |
| Định dạng khác | Giá trị {Nhãn} chưa đúng định dạng. Vui lòng kiểm tra lại. |
| Bắt buộc nhưng đang khóa | Thông tin bắt buộc này đang khóa với tài khoản của bạn. Vui lòng liên hệ người quản trị. |
| Bắt buộc nhưng bị ẩn | Nhãn hiện “Thông tin không hiển thị”, không có link; câu: liên hệ người quản trị. Không lộ tên trường. |

Lỗi khi lưu được phân loại bằng `saveError()`:

| Loại (`data-kind`) | Khi nào | Nội dung |
|---|---|---|
| `required` / `duplicate` / `date` / `validation` | `ValidationError` | câu backend nguyên văn, tiêu đề theo loại |
| `access` | `AccessError` | câu backend hoặc “liên hệ người quản trị” |
| `missing` | `MissingError` | bản ghi có thể đã bị xóa, tải lại |
| `business` | `UserError`/`RedirectWarning` | câu backend nguyên văn |
| `connection` | mất kết nối | chưa xác nhận kết quả, tải lại trước khi thử lại |
| `system` | lỗi khác | câu chung; **không** hiện traceback, tên trường, giá trị |

Tiêu đề nói đúng thao tác người dùng vừa làm: `saveError(error, {verb, write, note})`.

- `verb` mặc định “lưu”; màn khác truyền “xóa”, “sắp xếp”, “mở hồ sơ”, “thêm mới”,
  “mở cài đặt bảo mật” → “Không có quyền xóa”, “Máy chủ từ chối sắp xếp”, “Lỗi hệ
  thống khi mở hồ sơ”.
- `write: false` cho thao tác không ghi dữ liệu (mở hồ sơ, mở màn thêm mới, mở cài
  đặt bảo mật): mất kết nối thì báo “Chưa kết nối được máy chủ nên chưa {verb} được.
  Kiểm tra kết nối rồi thử lại.”, vì không có kết quả nào cần xác nhận lại.
- `note` thay câu cuối “Dữ liệu đã nhập được giữ nguyên.” khi màn không có dữ liệu
  nhập: “Danh sách chưa thay đổi.”, “Tài khoản chưa thay đổi.”, “Đã khôi phục vị trí
  cũ trong danh sách.”, “Bộ lọc và số liệu đang xem được giữ nguyên.” Khi có `note`
  thì không thêm câu giải thích dấu `*`.

Hộp thoại lỗi RPC native của Odoo vẫn giữ nguyên; khối trong form là thông tin bổ sung.

## 5. Kỹ thuật (một presenter dùng chung)

`tp_web_home/static/src/validation/`:

- `validation.js`: `collectErrors`, `fieldMessage`, `saveError`, component
  `ValidationSummary`; patch `Record` (`_displayInvalidFieldNotification`,
  `_checkValidity`, `_save`, `_discard`), `FormCompiler` (chèn summary),
  `FormArchParser` (`tpLabels`), `FormLabel` (`tpRequired`), `Notebook` (số lỗi),
  `ListRenderer` (summary dòng đang sửa), `Field` (câu dưới ô).
- `inline_errors.js/xml`: `InlineErrors` cho form OWL tự viết; caller truyền lỗi từ
  validator thật của màn đó (`{id, label, location, message}`) và `saveError(error)`.
  `intro` thay câu mở “Chưa lưu được. Vui lòng kiểm tra” khi thao tác không phải lưu
  (vd. “Chưa mở được màn thêm mới. Vui lòng kiểm tra”), `note` thay câu cuối.
- `validation.scss`: style trong phạm vi `.tp_validation_*`, `.tp_required_*`; không
  `!important`, không đụng CSS toàn hệ thống. Rule `::after "*"` cũ trong
  `inputs/inputs.scss` đã gỡ để không có hai dấu `*`.

Toast native vẫn dùng khi không có renderer đăng ký (không có nơi hiển thị) và khi
sửa nhiều dòng một lúc (multi-edit), vì Odoo hủy bản ghi ngay sau đó.

Màn mới: form view native tự có. Form OWL tự viết phải dùng `InlineErrors` +
`saveError`, không gọi `notification.add(..., {type: "danger"})` cho lỗi lưu, và vẫn
gọi backend để kiểm tra.

## 6. Đã áp dụng

| Phạm vi | Cách |
|---|---|
| Mọi form view native (trang, popup, wizard, quick-create mở form) của mọi module | patch toàn cục |
| Công của tôi: điều chỉnh công và thu hồi đề nghị (CHG-20261123-010) | `InlineErrors` + `saveError`, lỗi ngày/giờ/lý do theo validator và backend; giữ state khi gửi lỗi, chỉ xác nhận thành công sau RPC |
| Bảng con editable và popup dòng x2many | patch `ListRenderer` + `collectErrors` |
| Hồ sơ nhân viên mới (`hr.employee`) | thêm banner khuyến nghị không chặn lưu: chỉ liệt kê Mã NV (khi đã lưu mà vẫn thiếu), Phòng ban, Chức vụ còn thiếu; không yêu cầu field tự sinh/readonly/ẩn |
| Hợp đồng/phiên bản trên hồ sơ mới | `version_id` ẩn khi chưa có `id` (field tính, không cho nhập) |
| Hồ sơ của tôi (`MyProfile`): lưu hồ sơ, popup kinh nghiệm/học vấn, popup kỹ năng | `InlineErrors`; điều kiện thiếu giống `tp_save_my_resume_line`/`tp_save_my_skill`; backend vẫn kiểm |
| Tài khoản đăng nhập (`AccountCredentials`, đổi tên đăng nhập) | `InlineErrors` + `saveError` trong hộp thoại |
| Xóa nhân viên (`employee_delete`) | `InlineErrors` trong hộp thoại (đã có trước CHG-027) |
| Hồ sơ của tôi: xóa dòng kinh nghiệm/học vấn, xóa kỹ năng, mở cài đặt bảo mật (CHG-027) | khối lỗi trong đúng thẻ người dùng thao tác (Kinh nghiệm & học vấn, Kỹ năng, Tài khoản; hoặc thẻ “chưa liên kết hồ sơ” khi không có hồ sơ nhân viên); mỗi lúc một khối; đổi tab thì xóa; không toast |
| Danh sách nhân viên: kéo thả sắp xếp (CHG-027) | khối lỗi phía trên bảng: “Máy chủ từ chối sắp xếp” + câu backend + “Đã khôi phục vị trí cũ trong danh sách.”; thứ tự cũ khôi phục như trước; lần kéo sau xóa khối; không toast |
| Tổng quan KD: mở hồ sơ từ số liệu, thêm mới, mở dự án (CHG-027) | khối lỗi dưới thanh cảnh báo của Tổng quan; bộ lọc/số liệu giữ nguyên. Thêm công việc/WBS khi chưa chọn Dự án: báo trước, **không gọi máy chủ**, mở bộ lọc, bấm tới ô Dự án; backend `action_kd_create` vẫn kiểm |
| Ba công cụ cá nhân (`tp_personal_tools`, CHG-20261125-006 & CHG-20261125-008): ngăn chi tiết Công việc của tôi (`TodoDetailDrawer`, báo kết quả/xác nhận), hộp thoại Đưa vào lịch (`ScheduleTaskDialog`), hộp thoại Tạo/Sửa lịch & Đặt phòng họp (`CalendarEventDialog`), Tạo trao đổi mới / Nhóm Dự án-Phòng ban (`CreateChatDialog`), Chuyển tin nhắn thành việc (`MessageToTaskDialog`), Chia sẻ liên kết (`ShareToDiscussDialog`, `ShareItemDialog`) và khôi phục kéo thả Kanban/FullCalendar khi lỗi | `InlineErrors` + `saveError` trong đúng ngăn/hộp thoại hoặc thanh thông báo trên bảng lịch/bảng việc; kiểm tiêu đề, khoảng giờ bắt đầu < kết thúc, xung đột đặt phòng họp đồng thời, ngày kết thúc lặp và thành viên/nguồn nhóm tại đúng trường kèm khối tổng hợp, không dùng toast `danger` cho lỗi lưu/kéo thả |
| Văn phòng số & Yêu cầu phê duyệt mở rộng (`tp_digital_office`, `tp_request 20.0.2.0.0`, CHG-20261125-009): biểu mẫu Thông báo nội bộ, Biên bản họp (kèm kiểm tra dòng đầu việc kết luận), Nghỉ phép, Công tác hiện trường và Tạm ứng/Chi phí | `InlineErrors` + `saveError` hiển thị rõ tên trường/bảng con thiếu thông tin (tiêu đề, kết luận trước phát hành, đối tượng nhận, ngày nghỉ/công tác, địa điểm công tác, số tiền đề nghị), giữ nguyên dữ liệu nhập, không dùng toast `danger` cho lỗi lưu |
| Điều hành & Quản trị dự án (`tp_enterprise_governance`, CHG-20261125-010): biểu mẫu ghi nhận chỉ tiêu tài chính có nguồn, điều chỉnh mốc tiến độ WBS, khởi tạo bộ hồ sơ giao nộp | `InlineErrors` + `saveError` kiểm tra kỳ dữ liệu, nguồn chứng từ gốc, số tiền, lý do điều chỉnh mốc tiến độ, dự án và tên bộ hồ sơ ngay trong màn hình, không dùng toast `danger` |
| Tuyển dụng, Thiết bị khảo sát, Đối soát đầu vào Lương & Trợ lý AI (`tp_enterprise_ops`, CHG-20261125-011): biểu mẫu Nhu cầu tuyển dụng, Hồ sơ ứng viên, Đặt lịch phỏng vấn, Tiếp nhận nhân sự trúng tuyển, Cập nhật hạn kiểm định thiết bị khảo sát, Đối soát kỳ công lương và câu lệnh Trợ lý AI | `InlineErrors` + `saveError` kiểm tra vị trí/phòng ban tuyển dụng, họ tên ứng viên, trùng CCCD/email/SĐT khi tiếp nhận nhân sự, hạn hiệu chuẩn máy khảo sát, cổng khóa quy chế lương và câu hỏi trợ lý ngay trong màn hình, không dùng toast `danger` |

## 7. Chưa áp dụng hoặc cố ý giữ cách khác

Sau CHG-027 không còn `notification.add(..., {type: "danger"})` cho lỗi lưu/ghi trong
`custom_addons/*/static/src`; chỉ còn hai toast danger có chủ đích của menu người
dùng (dòng đầu bảng).

| Vị trí | Hiện trạng | Lý do |
|---|---|---|
| `tp_web_home` identity_service.js: đăng xuất, mở thông tin cá nhân từ menu người dùng | toast danger | thao tác từ menu trên cùng, không có form/màn để đặt khối lỗi; `user_menu_logout.test.js` khóa hành vi này |
| Hồ sơ của tôi: chọn ảnh đại diện sai loại hoặc quá 5 MB | toast cảnh báo (`warning`), kiểm trước khi gửi | không có ô nhập để gắn lỗi; chưa chuyển |
| `tp_reporting` person | lỗi riêng trong màn (`state.error`) | file đang có thay đổi chưa commit của tác vụ khác; chuyển sau khi tác vụ đó đóng |
| `tp_equipment` (scan), `tp_hr_attendance` (upload, công của tôi), `tp_kd_workspace` (report center, table tools) | lỗi riêng trong màn (`state.error`), không toast danger | chưa đổi sang `InlineErrors`/`saveError`, nên câu chữ chưa theo bảng mục 4 |

## 8. Giới hạn đã biết

- Mất kết nối: Odoo có chế độ offline riêng; với thao tác ghi presenter chỉ báo “chưa
  xác nhận kết quả {verb}”, không tự gửi lại.
- Lỗi ẩn/khóa chỉ hiển thị khi Odoo vẫn coi là thiếu; presenter không mở quyền hoặc
  hiện field để người dùng nhập.
- Phân loại `ValidationError` dựa trên câu chữ backend (trùng/thiếu/ngày); câu không
  rơi vào nhóm nào hiện là “Dữ liệu chưa hợp lệ”, nội dung vẫn đúng nguyên văn.
- Form OWL tự viết chỉ có lỗi khi màn đó truyền lỗi; chưa có cơ chế tự động.
- Kéo thả sắp xếp: khối lỗi chỉ được xóa khi kéo thả lần sau hoặc khi màn danh sách
  được mở lại; chuyển trang/lọc không tự xóa khối.
