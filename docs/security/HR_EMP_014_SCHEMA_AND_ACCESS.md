# HR-EMP-014 — Schema và quyền

Ngày 13/11/2026; addon `tp_hr_workspace` 20.0.1.11.0. Không đổi REST/OpenAPI,
core Odoo, `tp_contract` KH-KD hoặc `employee_type_id`.

| Dữ liệu | Nơi lưu / tái sử dụng | Ý nghĩa và quyền |
| --- | --- | --- |
| Phân loại quản trị | `hr.version.tp_employment_kind`; `hr.employee` related `version_id`, `inherited=True` | short_term/long_term/outsourced; nullable, tracking, nhóm HR, ghi cần quyền sửa employee |
| Ngày lao động | Native `hr.version.contract_date_start`, `contract_date_end`, `fixed_term` và related employee | Giữ validation/copy/sync thời hạn native; không tạo bộ ngày song song |
| Giấy tờ | `tp.hr.contract.document` kế thừa mail.thread | employee restrict, company related stored; name/number/kind/signed_date/note; không state ký/duyệt/hiệu lực |
| Ngày thuê khoán | `tp.hr.contract.document.service_start`, `service_end` | Chỉ loại outsourced; end cần start và end≥start; labor bị chặn ghi các ngày này |
| Tệp | Binary attachment `file`, `appendix` và tên tệp | Native attachment/download kiểm model cha; không public/token/rebind |
| Liên kết phiên bản | `hr.version.tp_contract_document_id`; employee related + One2many papers | Đúng employee/company; labor dùng cùng khoảng ngày trong các phiên bản active liên kết; copy version dùng lại giấy tờ, sang kỳ lao động khác bỏ liên kết kế thừa |
| Chất lượng hồ sơ | `hr.employee.tp_missing_basic` compute/search; `_tp_missing_domain()` | code trống OR department trống OR (job và source title đều trống); cùng nguồn cho list/KPI/drilldown/XLSX |
| Đối chiếu danh tính | `tp.hr.employee.audit.action=identity` dùng audit hiện có | Metadata kỹ thuật ở audit append-only theo admin/company; event mới ghi lời nghiệp vụ rõ trong chatter |

Hai ACL `access_tp_hr_contract_hr` (read) và `access_tp_hr_contract_write`
(create/update) giới hạn HR, company_ids và quyền read/write trên employee.
Không ACL delete. Backend kiểm employee write cả trên ghi/tạo version có
classification/document (kể cả context default), và trên create/update giấy
tờ. Hộp thêm dùng context phiên bản riêng, validate đúng nhân viên và liên kết
trong cùng transaction; lỗi rollback cả giấy tờ. Không sudo để ghi phân loại.

Không chuyển giấy tờ sang employee/kind khác, không unlink giấy tờ. FK restrict
được cơ chế preview HR-DELETE-010 nhận diện như phụ thuộc độc lập và chặn xóa
employee. Không đổi password/session/role/mapping/luồng xóa.

Attachment giữ native access theo model/record. Addon chặn public/access_token,
generate_access_token và rebind tệp đang thuộc hợp đồng. KH-KD không HR bị chặn
đọc/export/tải trực tiếp. Quyền tiền/lương native không đổi, không có field
lương trong exporter. Không thể tự suy nội dung nhạy cảm của file người dùng
upload; HR cần chỉ lưu giấy tờ phù hợp phạm vi người đọc được giao.

Renderer mail chỉ đổi phần trình bày sự kiện HR: envelope danh tính đúng bộ
keys và đúng employee trên notification/tracking, có giới hạn kích thước và
JSON decoder, escape lời giải thích. Ghi chú không nhận diện giữ nguyên. Không
sửa body cũ, không xóa tracking/audit, không can thiệp lọc quyền field của mail.
Các nhãn tracking HR được chuyển trong cấu trúc HTML có phạm vi, không regex
toàn DOM. Ngày giờ do mail/native dùng ngôn ngữ và timezone của người dùng.

Danh sách HR và Excel đều dùng related version nguồn duy nhất. Dữ liệu trống
không được backfill loại hình/hợp đồng. Tệp Excel ghi literal strings, chỉ
công thức tổng do server tạo, giữ cột/giá trị theo quyền backend.

[Hướng dẫn](../demo/HR_EMP_014_USER_GUIDE.md) ·
[Kiểm chứng](../demo/HR_EMP_014_ACCEPTANCE.md) ·
[Triển khai và rollback](../../ops/runbooks/HR_EMP_014_DEPLOY_AND_ROLLBACK.md).
