# HR-001 — Kế hoạch xây nền quản lý nhân sự

**Cập nhật thực thi 11/11/2026:** `IMPLEMENTED_VERIFIED_MAIN_PENDING_BUSINESS_VISUAL_PILOT`.
HR-001 đã áp source/module lên main `tp_tanphat_dev`/18069 sau backup và restore
kiểm chứng trên test chuẩn: 39 employee/39 version, 9 đơn vị có nhân viên trong
14 danh mục, mã TP và retry cùng nguồn cho 39 dòng bỏ qua. Dọn đúng 3 hồ sơ mẫu,
archive 16 actor theo manifest; giữ 25 identity, thông tin xác thực/nhóm và HEAD.
Năm tài khoản KH-KD còn chờ đối chiếu danh tính, không tự liên kết nhân viên.
Backend cuối 28 kiểm đạt; HOOT HR 10/Home 28 (kèm dependency 12/29); UI test
13 kịch bản có CRUD đạt trước fresh restore. Test sau restore: 11 kiểm chỉ đọc
đạt, 0 pageerror; 5 actor KH-KD giữ HEAD capability chỉ ở HEAD, list nghiệp vụ
rỗng nên không có hồ sơ thật để mở detail. Smoke chỉ đọc main11/11đạt,0pageerror; xem [acceptance](../demo/HR_001_ACCEPTANCE.md)
cho bằng chứng cuối và giới hạn kiểm detail khi không có dữ liệu nghiệp vụ.
Backup `025345789849Z` đã restore kiểm chứng 592 bảng/261 blob/424 sequence;
đối soát bảo toàn private 621 blob đạt, 0 vi phạm. Bằng chứng và mapping giữ
private `.local/hr001/`. Nghiệm thu nghiệp vụ, phản hồi giao diện và pilot chưa
được xác nhận bởi kiểm kỹ thuật. Phần kiểm kê/kế hoạch cũ dưới đây là lịch sử.

**Ưu tiên 11/11/2026 — DEC-038:** kế hoạch triển khai hiện hành đã mở rộng tại
[Roster và workspace HR](TP_HR_001_ROSTER_WORKSPACE_PLAN.md),
[prompt](../prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md). Nguồn mới có hai
sheet cùng 39 người/9 nhóm, mã TP, cleanup account phù hợp, UI/dashboard/Excel và
rollout 18069 sau test. Runtime mới có 3 employee HR scenario/9 department/3 job,
chưa dọn ở phiên lập prompt; inventory dưới đây là lịch sử. Model native thực
tế `_inherits={'hr.version':'version_id'}` (version_id compute), current_version_id
store; không triển khai dựa trên mô tả giản lược cũ chỉ dùng current_version_id.

**Ngày:** 10/11/2026 (Asia/Saigon). **Trạng thái:** S0_INVENTORIED_SPECIFICATION_READY.  
Người dùng chọn module Quản lý nhân sự làm bước phát triển tiếp sau Trang chủ admin UI-HOME-004.
Đặc tả này được lập sau khi đối chiếu source Odoo 20 và database runtime `tp_tanphat_dev` thực tế. Chưa code nghiệp vụ HR hoặc import nhân sự thật trong đợt này.

---

## 1. Kiểm kê hiện trạng thực tế (Runtime Dev 18069 / `tp_tanphat_dev`)

**Ghi chú sau bảo trì OPS-CLEAN-001 / DEC-037 (10/11/2026):** số12nhân viên
và12version dưới đây là kiểm kê lịch sử trước dọn. Phạm vi người dùng đã chốt
xóa hồ sơ nhân viên mẫu, giữ tài khoản/quyền/phòng ban/cấu hình; nguồn39người
vẫn private và chưa nhập. Kiểm kê runtime mới theo `docs/PROJECT_STATUS.md`.
S1 dùng test chuẩn `tp_tanphat_test`/18079, không tạo clone DB theo task hoặc
seed mẫu lên main18069; đối chiếu lại HR/user links trước khi thực thi S1.

### 1.1 Trạng thái module và model
- **Module `hr`**: Đã cài đặt (phiên bản `20.0.1.1`).
- **Module `hr_recruitment`**: Chưa cài đặt (`uninstalled`, `latest_version: None`).
- **Module `tp_organization`**: Đã cài đặt (`20.0.1.0.0`), bổ sung trường `tp_code` cho `hr.department` kèm ràng buộc unique `(company_id, tp_code)`.
- **Kiến trúc Odoo 20**:
  - `hr.employee` không lưu trực tiếp `department_id`, `job_id`, `identification_id`, `wage`. Các trường này nằm trên model `hr.version` (phiên bản hợp đồng/hồ sơ nhân sự), liên kết với nhân viên qua `current_version_id` (trường delegate/related).
  - `hr.employee.public`: Model danh bạ công khai, lọc các trường riêng tư cho người dùng nội bộ thông thường.
  - Tuyệt đối không tạo model `tp.employee` song song làm phân mảnh nguồn dữ liệu.

### 1.2 Dữ liệu hiện hữu trên database
- **Phòng ban (`hr_department`)**: Hiện có 7 bản ghi:
  - ID 1: Administration / Quản trị
  - ID 2: Planning and Business - DEV (`tp_code: 'KHKD'`)
  - ID 18: Kế hoạch Kinh doanh
  - ID 19: Khảo sát
  - ID 20: Thiết kế
  - ID 21: Tài chính Kế toán
  - ID 22: Hành chính Nhân sự
- **Chức danh công việc (`hr_job`)**: Hiện có **0** bản ghi (chưa khai báo chức danh).
- **Nhân viên (`hr_employee`)**: Hiện có **12** bản ghi mẫu (IDs 13–24), tương ứng 12 bản ghi `hr_version` (IDs 13–24):
  - 11 bản ghi liên kết với user test cũ `staff.*@example.invalid` (từ dữ liệu NATIVE_DATA_003).
  - 1 bản ghi `Ngô Thị Hà` (ID 23) có `user_id = NULL`.
  - 5 tài khoản KH-KD (`kd.thuyanh`, `kd.tuananh`, `kd.thanh`, `kd.huong`, `kd.lananh`) chưa từng được liên kết với bất kỳ bản ghi `hr.employee` nào.
- **Chứng chỉ và năng lực**:
  - `tp_kd_workspace` đang quản lý chứng chỉ tại model `tp.credential` ("Hồ sơ năng lực và chứng chỉ tổng hợp"), chia thành `organization` (tổ chức) và `person` (cá nhân), phục vụ báo cáo R06.
  - Phân hệ HR nền tảng sẽ tích hợp/tham chiếu canonical `tp.credential` khi quản lý chứng chỉ nhân viên, tránh tạo bảng trùng lặp hoặc mâu thuẫn bảo mật.

---

## 2. Đặc tả lát cắt đầu tiên (HR-001 S0 & S1)

### 2.1 Danh sách và chi tiết nhân viên (List & Form)
- **Giao diện danh sách (Tree/List View)**:
  - Hiển thị các cột rõ ràng: Mã nhân viên (mã nguồn/nội bộ), Họ và tên, Phòng ban (`department_id` qua version), Chức danh (`job_id` qua version), Email công việc, Điện thoại công việc, Trạng thái hoạt động (`active`).
  - Tìm kiếm (Search View): Tìm theo tên, mã nhân viên, số điện thoại, email.
  - Lọc (Filters): Nhân viên đang làm việc (`active=True`), Nhân viên lưu trữ (`active=False`), Chưa có phòng ban, Chưa gán chức danh.
  - Nhóm (Group By): Theo Phòng ban (`department_id`), Theo Chức danh (`job_id`), Theo Công ty (`company_id`).
  - Phân trang: Chuẩn native Odoo (80 dòng/trang).
- **Giao diện chi tiết (Form View)**:
  - Header: Nút Lưu trữ/Khôi phục (`archive`/`unarchive`).
  - Khối định danh chính: Ảnh đại diện, Họ và tên, Chức vụ hiển thị.
  - Tab "Thông tin công việc": Phòng ban, Chức danh, Quản lý trực tiếp (để trống nếu chưa xác nhận nguồn), Địa điểm làm việc, Email/điện thoại công việc.
  - Tab "Thông tin cá nhân (Riêng tư)": CCCD/Hộ chiếu, Ngày sinh, Nơi sinh, Giới tính, Tình trạng hôn nhân, Địa chỉ thường trú, Số điện thoại cá nhân, Người liên hệ khẩn cấp.
  - Tab "Năng lực & Chứng chỉ": Danh sách chứng chỉ liên kết từ `tp.credential`.
  - Tab "Cài đặt nhân sự": Loại nhân viên, Ngày bắt đầu (chỉ nhập khi có nguồn), User liên kết (`user_id` — tùy chọn, không bắt buộc).

### 2.2 Ranh giới dữ liệu Chung vs Riêng (Public vs Private)
| Nhóm dữ liệu | Các trường cụ thể | Ai được xem? |
| --- | --- | --- |
| **Công khai (Public Directory)** | Họ tên, Phòng ban, Chức danh, Email công việc, Điện thoại công việc, Vị trí bàn làm việc | Mọi nhân viên nội bộ (`base.group_user`) qua `hr.employee.public` |
| **Bảo mật nhân sự (Private Profile)** | CCCD, Hộ chiếu, Ngày sinh, Địa chỉ riêng, Điện thoại riêng, Người thân khẩn cấp | Chỉ bản thân nhân viên (nếu có user liên kết) và Nhân sự (`hr.group_hr_user`, `hr.group_hr_manager`) |
| **Bảo mật tài chính (Payroll/Wage)** | Lương cơ bản (`wage`), phụ cấp, tài khoản ngân hàng, thông tin thuế | Chỉ Quản trị nhân sự (`hr.group_hr_manager`) và Kế toán lương (lát cắt sau) |

### 2.3 Ma trận phân quyền
| Quyền / Hành động | Nhân viên thường (`base.group_user`) | Chuyên viên HR (`hr.group_hr_user`) | Quản trị HR (`hr.group_hr_manager`) | Admin hệ thống (`base.group_system`) |
| --- | :---: | :---: | :---: | :---: |
| Xem danh bạ nhân viên | Đọc (Public) | Đọc toàn bộ | Đọc toàn bộ | Đọc toàn bộ |
| Xem hồ sơ riêng tư (CCCD, địa chỉ) | Chỉ hồ sơ của mình | Xem toàn bộ | Xem toàn bộ | Xem toàn bộ |
| Tạo mới / Sửa thông tin nhân viên | Không | Tạo & Sửa | Tạo & Sửa | Tạo & Sửa |
| Lưu trữ (Archive) nhân viên | Không | Không | Cho phép | Cho phép |
| Quản lý Phòng ban / Chức danh | Đọc | Đọc | Tạo & Sửa | Tạo & Sửa |
| Xem tiền lương / Thù lao | Không | Không | Cho phép | Cho phép |

---

## 3. Kế hoạch đối chiếu nguồn nhân sự (39 người / 9 nhóm)

Nguồn dữ liệu tham khảo hiện hành: file `202611_tanphat_chamcong_tuan1.xlsx` (DEC-034), 39 dòng thuộc 9 nhóm.
Danh mục chi tiết được bảo vệ ngoài Git tại `.local/staff-reference-20261110/`.

### Nguyên tắc xử lý khi triển khai nhập liệu (Chặng S2 sau này):
1. **Không tạo tài khoản tự động**: Tuyệt đối không mặc định mỗi nhân viên đều có tài khoản user Odoo. Chỉ tạo nhân viên (`hr.employee` + `hr.version`), trường `user_id` để `NULL`.
2. **Không bịa thông tin**: Những thông tin không có trong bảng công tuần 1 (như email, số điện thoại, ngày vào làm, mức lương, quản lý trực tiếp) bắt buộc để trống, không tự suy đoán.
3. **Giữ nguyên văn chức vụ nguồn**: Ví dụ "Trường phòng", "Kế toán trường", "TV",... được lưu trữ trung thực vào trường nguồn; có thể ánh xạ sang `hr.job` chuẩn hóa qua bảng mapping rõ ràng.
4. **Phương án Dry-run**:
   - Đối chiếu theo mã nhân viên nguồn và công ty.
   - Báo cáo trùng lặp, cảnh báo nhân viên đã tồn tại trước khi ghi thật.
   - Idempotency: chạy lại kịch bản nhập liệu không tạo thêm bản ghi trùng.
   - Có kịch bản hoàn tác (rollback) bảo toàn 12 bản ghi test cũ và dữ liệu hiện hành.

---

## 4. Lộ trình triển khai cụ thể

- **S0 (Hiện tại)**: Hoàn thành kiểm kê schema Odoo 20, trạng thái runtime dev 18069, xác định ranh giới public/private và lập đặc tả lát cắt đầu tiên (không code, không import).
- **S1 (Lát cắt đầu tiên trên Clone)**:
  - Tinh chỉnh view list, search, form cho `hr.employee` và `hr.version`.
  - Khởi tạo danh mục chức danh `hr_job` mẫu theo các chức vụ thực tế.
  - Viết test kiểm thử quyền truy cập public vs private và các thao tác thêm/sửa/lưu trữ.
- **S2 (Đối chiếu và Import có kiểm soát)**:
  - Chạy dry-run 39 nhân sự từ bảng nguồn.
  - Rà soát đối chiếu với 5 tài khoản KH-KD hiện hữu (chỉ liên kết khi có xác nhận chính thức).
  - Áp dụng vào dev sau khi sao lưu và kiểm chứng.
- **S3 (Báo cáo & Tích hợp)**:
  - Báo cáo cơ cấu nhân sự theo phòng ban/chức danh, xuất Excel bảo mật.
  - Tích hợp hồ sơ năng lực với `tp.credential` của KH-KD.
- **Các phân hệ tiếp sau**:
  - Tuyển dụng (`hr_recruitment`): cài đặt và thiết lập quy trình ứng viên.
  - Chấm công, nghỉ phép, tính lương: cần quy chế doanh nghiệp riêng trước khi triển khai.
