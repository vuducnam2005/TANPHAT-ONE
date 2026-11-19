# TANPHAT ONE — Quy chuẩn thông báo thông tin còn thiếu khi thêm mới/lưu

Ngày: 19/11/2026. Task `FORM-VALIDATION-001`, CHG-20261119-023.
Trạng thái: **đã triển khai cho mọi form native và các form tùy biến HR ghi ở mục 6**;
các màn còn thiếu được ghi rõ ở mục 7, không coi là đã đạt.

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
| Bảng con editable và popup dòng x2many | patch `ListRenderer` + `collectErrors` |
| Hồ sơ nhân viên mới (`hr.employee`) | thêm banner khuyến nghị không chặn lưu: chỉ liệt kê Mã NV (khi đã lưu mà vẫn thiếu), Phòng ban, Chức vụ còn thiếu; không yêu cầu field tự sinh/readonly/ẩn |
| Hợp đồng/phiên bản trên hồ sơ mới | `version_id` ẩn khi chưa có `id` (field tính, không cho nhập) |
| Hồ sơ của tôi (`MyProfile`): lưu hồ sơ, popup kinh nghiệm/học vấn, popup kỹ năng | `InlineErrors`; điều kiện thiếu giống `tp_save_my_resume_line`/`tp_save_my_skill`; backend vẫn kiểm |
| Tài khoản đăng nhập (`AccountCredentials`, đổi tên đăng nhập) | `InlineErrors` + `saveError` trong hộp thoại |

## 7. Chưa áp dụng (còn toast `danger` hoặc lỗi riêng)

| Vị trí | Hiện trạng |
|---|---|
| `tp_hr_workspace` my_profile.js: xóa dòng kinh nghiệm/kỹ năng, mở tùy chọn bảo mật | toast danger (không phải thêm mới) |
| `tp_hr_workspace` table.js: sắp xếp thứ tự nhân viên | toast danger kèm khôi phục vị trí |
| `tp_kd_workspace` overview.js (2 chỗ) | toast danger |
| `tp_web_home` identity_service.js: đăng xuất, mở thông tin cá nhân | toast danger |
| Component OWL tự ghi dữ liệu khác: `tp_equipment` (scan), `tp_hr_attendance` (upload, mine), `tp_kd_workspace` (report center, table tools), `tp_reporting` (person), HR delete/department workspace | có thông báo riêng của màn, chưa chuyển sang `InlineErrors`/`saveError` |

## 8. Giới hạn đã biết

- Mất kết nối: Odoo có chế độ offline riêng; presenter chỉ báo “chưa xác nhận kết
  quả lưu”, không tự gửi lại.
- Lỗi ẩn/khóa chỉ hiển thị khi Odoo vẫn coi là thiếu; presenter không mở quyền hoặc
  hiện field để người dùng nhập.
- Phân loại `ValidationError` dựa trên câu chữ backend (trùng/thiếu/ngày); câu không
  rơi vào nhóm nào hiện là “Dữ liệu chưa hợp lệ”, nội dung vẫn đúng nguyên văn.
- Form OWL tự viết chỉ có lỗi khi màn đó truyền lỗi; chưa có cơ chế tự động.
