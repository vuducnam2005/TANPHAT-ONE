# HR-ATTENDANCE-001 — Policy quyền, trường, route, export và file

Ngày 17/11/2026 · Batch `CHG-20261117-020` · Áp dụng prompt
[HR-ATTENDANCE-001](../prompts/CLAUDE_HR_ATTENDANCE_001_AND_DIRECTORY_READONLY.md)
và thiết kế [TP_HR_ATTENDANCE_AND_DIRECTORY_DRAFT](../architecture/TP_HR_ATTENDANCE_AND_DIRECTORY_DRAFT.md).

Policy này là mặc định kỹ thuật theo prompt, không phải quyết định nghiệp vụ mới.
Quy tắc tính công, ca, người duyệt cụ thể vẫn do HR/Ban lãnh đạo xác nhận.

## 1. Vai trò

| Vai trò | Điều kiện backend | Được làm | Không được |
| --- | --- | --- | --- |
| Nhân viên nội bộ | `base.group_user`, user đang hoạt động, công ty được phép | Vào TP HR (nhãn **Chỉ xem**), danh bạ whitelist, bảng công chung ngày/tháng, Tổng quan công, Công của tôi, phiếu đề nghị của mình | Tạo/sửa/xóa nhân viên, công, ca, kỳ, quy tắc, mapping; xem phiếu/minh chứng người khác; export danh bạ/công người khác |
| Người phụ trách công | Bản ghi **Phân công xử lý công** đang hiệu lực (`tp.hr.attendance.assignment`) với capability `review`/`lock`/`import` và phạm vi phòng | Duyệt/trả phiếu, chốt/mở kỳ, nhập dữ liệu trong phạm vi | Tự duyệt phiếu của mình; xử lý ngoài phòng/company được giao |
| Trưởng phòng | Như nhân viên | Như nhân viên | Không suy quyền duyệt từ chức danh/HEAD KH-KD; cần phân công riêng |
| HR manager / admin | `hr.group_hr_manager` | Giữ toàn bộ CRUD HR hiện có; nhập dữ liệu công; cấu hình quy tắc, mapping mã máy, phân công | Không tự thành người duyệt nếu chưa tự phân công; không sửa công kỳ chốt ngoài đính chính |
| Admin được ủy quyền | `tp_admin_delegation` hiện hành | Baseline nhân viên + entry ủy quyền hiện có | Không mở private HR/hợp đồng/lương |
| Ẩn danh / portal / khóa | — | — | Mọi route/RPC nội bộ về `/dang-nhap` hoặc bị từ chối |

Không cấp `hr.group_hr_user`/`hr.group_hr_manager` cho mọi người; không patch
`has_group`/`check_access`. Nhóm duy nhất mới là `tp_hr_attendance.group_attendance_officer`
(chỉ cấp ACL đọc dữ liệu xử lý), được đồng bộ từ bản ghi phân công.

## 2. Danh bạ — trường chia sẻ

Nguồn: model native `hr.employee.public` (read-only SQL view; ACL native chỉ
`read` cho `base.group_user`). Directory views chỉ khai báo whitelist:

| Hiển thị | Field |
| --- | --- |
| Mã TP | `tp_employee_code` |
| Họ tên, avatar | `name`, `avatar_128/1024` (identity thật) |
| Phòng/đơn vị, chức vụ | `department_id`, `job_id`, `job_title` |
| Quản lý trực tiếp | `parent_id` |
| Email/điện thoại công việc | `work_email`, `work_phone` |
| Nơi làm việc, công ty | `work_location_id`, `company_id` |
| Sinh nhật (ngày/tháng) | `birthday_public_display_string` — chỉ có giá trị khi cờ chia sẻ native bật |

Không hiển thị trong danh bạ: `mobile_phone` (chưa phân loại là số công việc),
`user_id`/login, trạng thái tài khoản/bảo mật, API key, nhóm quyền. S4 giới hạn
mobile và biến thể chuẩn hóa/định dạng, `phone`/`email` liên kết tài khoản bằng
field groupsHR trên cả employee/public; work_phone/work_email công việc giữ chia sẻ.

Private (field `groups="hr.group_hr_user"` native + TP): hợp đồng/file, lương,
phụ cấp, CCCD/hộ chiếu/thuế/BHXH/ngân hàng, địa chỉ nhà, liên hệ khẩn cấp, gia
đình, sức khỏe, kỷ luật, đánh giá, ngày sinh đầy đủ, điện thoại/email riêng.
Nhân viên thường không có ACL `hr.employee`: native chỉ trả field công khai qua
`hr.employee.public` (proxy đọc); đọc, lọc, đếm hoặc sắp xếp theo field private bị
AccessError; tạo/sửa/xóa/sao chép bị từ chối. S4 bổ sung restriction không nhóm
trên `hr.resume.line` bằng `ir.access` native20: non-HR chỉ hồ sơ của mình,
HR giữ phạm vi đã có; description/certificate/download/export theo quyền nguồn.
Native user/resource IDs và kỹ năng công việc giữ để native consumers hoạt động;
các ID này không cho phép đọc thông tin bảo mật tài khoản hoặc hồ sơ riêng.

## 3. Bảng công — trường chia sẻ

| Model | Đọc | Ghi |
| --- | --- | --- |
| `tp.hr.attendance.day` (tổng hợp ngày) | Mọi nhân viên, cùng công ty | Chỉ qua import/duyệt/đính chính (server, sau kiểm actor) |
| `tp.hr.attendance.session` (phiên vào-ra) | Mọi nhân viên, cùng công ty | Như trên |
| `tp.hr.attendance.period` (kỳ) | Mọi nhân viên (trạng thái chốt) | Người có capability `lock` |
| `tp.hr.attendance.correction` (phiếu) | Chủ phiếu; người xử lý trong phạm vi; HR manager | Chủ phiếu khi nháp; chuyển trạng thái qua action backend |
| `tp.hr.attendance.batch/line` (nhập, staging) | HR manager, người có capability `import` | Như trên |
| `tp.hr.attendance.code` (mapping mã máy) | HR manager, người phụ trách | HR manager |
| `tp.hr.attendance.rule` (quy tắc công) | Mọi nhân viên (để hiểu "Chưa xác nhận") | HR manager |
| `tp.hr.attendance.assignment` | HR manager, chính người được phân công | HR manager |
| `tp.hr.attendance.log` (audit) | HR manager, người phụ trách | Không ai (chỉ server ghi) |

Trường chia sẻ của ngày công: ngày, mã TP, nhân viên, phòng tại ngày công, giờ
vào/ra, số phiên, giờ ghi nhận, giờ theo lịch, công xác nhận, trạng thái dữ
liệu/chốt, thời điểm cập nhật nguồn, version. Không có lý do nghỉ, ghi chú HR,
nội dung/minh chứng điều chỉnh, GPS/ảnh/sinh trắc. Nghỉ chỉ hiện **Nghỉ đã duyệt**.

## 4. Export và file

- `hr.employee.public.export_data` và proxy `hr.employee.export_data`: chỉ HR (`hr.group_hr_user`); người khác AccessError.
- `tp.hr.attendance.day/session.export_data`: HR/người phụ trách theo company;
  nhân viên chỉ khi mọi dòng là của chính mình, whitelist scalar công khai, không field liên kết.
- `tp_export_my_attendance`: CSV UTF-8 BOM8 cột ngày/giờ/công/trạng thái/kỳ/nguồn;
  owner từ session, month/state/lock đã áp; không nhận field hoặc owner client.
  Chống công thức ô, không tạo attachment/token. Employee thiếu mapping bị từ chối rõ.
- Minh chứng phiếu: `ir.attachment` gắn `res_model=tp.hr.attendance.correction`,
  quyền theo record phiếu (native), không public, không token chia sẻ.
- File Excel nguồn: attachment của lô nhập, chỉ HR/người nhập; không vào Git.

## 5. Route

| Route / action | Quyền |
| --- | --- |
| `/app/nhan-su` (server action entry) | `base.group_user`; HR → Tổng quan HR, người khác → Danh bạ |
| `/app/danh-ba` | `base.group_user` |
| `/app/cham-cong`, `/app/bang-cong`, `/app/cong-cua-toi` | `base.group_user` (client action, dữ liệu qua ORM có rule) |
| `/app/tp-hr`, các action HR hiện có | Giữ nguyên `hr.group_hr_user`/`manager` |
| Native `hr_attendance` (kiosk, systray, `/hr_attendance/*`) | **Không cài** |

## 6. Vì sao không cài `hr_attendance` native

Build 20 của `hr_attendance` kéo theo `hr_work_entry`, `base_geolocalize`, `barcodes`;
thêm route public theo token (`/hr_attendance/<token>`, `create_employee`,
`manual_selection`), check-in trên systray cho mọi user có hồ sơ, crons tự
check-out/vắng mặt và overtime. Mỗi đường này là một cửa ghi công cho viewer,
trái policy; tắt từng đường cần override nhiều controller native. Vì vậy dùng
model nhỏ `tp.hr.attendance.*` cùng DB, có lineage, field tương thích
`hr.attendance` (`employee_id`, `check_in`, `check_out`, `worked_hours`) để có
thể chuyển sang native sau khi được duyệt.

## 7. Nhập dữ liệu và mapping

- Mã máy = cột `ID` (hoặc `Mã nhân viên` số) trong báo cáo máy. Mapping vào hồ
  sơ qua bảng `tp.hr.attendance.code`. Đề xuất mapping chỉ khi mã máy trùng
  `tp_source_code` của hồ sơ **và** họ tên (bỏ dấu) khớp; tên khác → Xung đột,
  không có hồ sơ → Chưa mapping. Không dùng STT, Odoo ID hoặc chỉ tên.
- Không tạo/sửa nhân viên, user, phòng ban, chức vụ, mã TP từ file công.
- Khóa chống trùng: `(nhân viên, ngày công, giờ vào, giờ ra)` trên toàn công ty,
  bất kể file/sheet/lần nhập. Cùng nhân viên-ngày nhưng giờ khác → Xung đột chờ
  đính chính, không ghi đè.
- Thiếu giờ ra / ra trước vào / giờ không đọc được: giữ staging, ngày công hiện
  **Thiếu giờ ra/Cần kiểm tra**, không điền giờ giả.
- UTC trong DB; ngày công và giờ hiển thị theo `Asia/Ho_Chi_Minh` (tz lịch/nhân viên).
- Cột tổng hợp của máy (Đi muộn, Vắng mặt, Tổng công, Ghi chú) **không nhập**.

## 8. Công thức

- Giờ ghi nhận = tổng thời lượng các phiên vào-ra đầy đủ (không lấy min/max punch).
- Giờ theo lịch, công xác nhận: chỉ khi có **Quy tắc công đã xác nhận**
  (`tp.hr.attendance.rule`, HR manager xác nhận) phủ ngày, phòng và thứ đó. Giờ
  theo lịch = phần giao của các phiên với khung giờ của quy tắc (giờ bắt đầu–kết
  thúc, theo giờ `Asia/Ho_Chi_Minh`) trừ khoảng nghỉ trưa của quy tắc; công =
  min(giờ theo lịch, giờ chuẩn một công)/giờ chuẩn một công, làm tròn 2 số. Không
  dùng `resource.calendar` để khỏi suy quy tắc từ lịch mặc định chưa được HR xác
  nhận. Không có quy tắc → **Chưa xác nhận** (null, không phải 0); thứ không thuộc
  quy tắc → **Ngoài lịch**. Đưa quy tắc về nháp → mọi ngày phủ bởi nó trở lại
  **Chưa xác nhận**.
- Không tính đi muộn, phạt, nghỉ không phép, tăng ca hoặc lương.

## 9. S3 — Phiếu và kỳ chốt

Owner từ session/company, chỉ sửa nháp/trả. Reviewer active đúng company/phòng và khác owner; HR manager chỉ đọc sau gửi, không ngầm có quyền duyệt. Thu hồi assignment bỏ read scope reviewer ngay, người từng xử lý không tự giữ quyền. Minh chứng cấm public/token/reparent, chỉ owner sửa khi nháp/trả. Giải trình/ý kiến ở phiếu riêng, không vào log chung. Duyệt khóa phiếu và công ty, giữ phiên gốc inactive; retry từ chối. Kỳ chốt cần capability lock toàn công ty; đính chính cần review+lock+lý do, tăng version, giữ log. Chốt không xác nhận công/lương; recompute do đổi rule bỏ qua kỳ chốt. Odoo regression mới chưa chạy, không xác nhận race multiworker bằng kiểm source.
