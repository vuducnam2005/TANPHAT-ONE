# HR-001 — Kế hoạch hồ sơ nhân sự, nhập nguồn mới và workspace

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

**Ngày:** 11/11/2026. **Trạng thái hiện hành:** `IMPLEMENTED_VERIFIED_MAIN_PENDING_BUSINESS_VISUAL_PILOT`.
Trạng thái lúc soạn kế hoạch: `PROMPT_READY_NOT_IMPLEMENTED` (lịch sử).
Yêu cầu hiện hành mở rộng HR Foundation S0/S1: dữ liệu nhân sự thật từ file mới,
mã TP, dọn mẫu/account không phù hợp, sidebar theo KH-KD, dashboard và Excel.
DEC-038 ghi phạm vi. [Prompt thực thi](../prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md).

## 1. Căn cứ đã kiểm

- Workbook mới `C:\Zalo Received Files\bang cham cong vao ra (1).xlsx`,
  hash `8b1ed1f254ac56288da30b53a2fe3bb9858c18b995743c7d45fb686129b5f8ff`.
  Hai sheet `Tuần 1`, `Tuan 2`, kỳ B4 ngày 09–10/11/2026; không suy kỳ từ tên sheet.
- A6:E6 là STT/mã/tên/ID/chức vụ. Mỗi sheet 39 dòng; 78 dòng gộp 39 người,
  mã B/D khớp, không conflict danh tính/nhóm/chức vụ giữa hai sheet.
  Kiểm reader và XML độc lập; không sửa file hoặc nhập giờ vào/ra.
- 9 nhóm: Văn Phòng 4, TADIC 4, TACICO 1, Phòng Thiết kế 9, Phòng Kỹ Thuật 4,
  Phòng BIM-QC 3, Ban quản trị - Tài chính 4, Ban Kinh Doanh 6, Ban Giám đốc 4.
- So nguồn 10/11: giữ 39 người/9 nhóm, 3 mã có thay đổi nhãn chức vụ. Không dùng
  nguồn cũ ghi đè file mới, không suy 3 quyết định nhân sự pháp lý.
- Runtime read-only ngày 11/11: 3 employee/3 version/9 department/3 job,
 25 users/22 active, CRM 0/contract 0, một project Internal. Các employee mới có
 XMLID `hr.employee_mw/employee_eg/employee_sj` thuộc HR onboarding scenario;
 chưa dọn trong phiên lập prompt. Lần dọn 10/11 vẫn là lịch sử đúng thời điểm.
- Source native `hr.employee.load_demo_data()` nạp HR scenario; đường UI gọi
  qua `HrEmployeeActionHelper.loadDemoData`. Không có bằng chứng ai bấm hoặc
  call nào đã tạo; chỉ xác định nguồn binding và cơ chế có thể nạp lại.
- `hr`, `hr_skills`, `tp_organization` có; attendance/leave/recruitment chưa cài.
  `hr.employee` kế thừa `hr.version` qua `version_id`; current_version_id store.
- Chi tiết nhân viên/account mapping/before inventory trong private
  `.local/hr-plan-20261111/`; không đưa danh tính/ID nguồn vào tracked docs.

## 2. Quy tắc sản phẩm và dữ liệu

- Mã nghiệp vụ = TP+(10000+mã nguồn), ví dụ 60 → TP10060. Giữ khóa Odoo/FK và
  mã nguồn riêng. Không dùng STT, CCCD, barcode/PIN hoặc userID thay mã nguồn.
- Nhập employee không tự tạo user, cấp HR hoặc chuyển quyền KD. Người dùng
  xác nhận liên kết hồ sơ, giữ quyền KH-KD; sau đó cho phép bỏ account hiện hữu
  nếu không phù hợp nguồn. Dùng archive/disable có manifest, giữ lịch sử và
  admin/kỹ thuật, không hard-delete 25 users.
- Alias rút gọn có nhiều ứng viên: chưa có whitelist danh tính user → mã nguồn.
  Chỉ link khi đủ căn cứ. Mơ hồ để chưa link; không tự chuyển đặc quyền cũ
  sang người khác hoặc khóa người thật chỉ vì tên viết tắt. Không chặn các
  chặng độc lập bởi việc thiếu mapping.
- Chức vụ/đơn vị theo file; có raw source và mapping chuẩn. Không suy job,
  hợp đồng, quản lý, ngày vào làm, giới tính hoặc tiền lương nếu thiếu nguồn.
  Native default kỹ thuật không phải dữ liệu nghiệp vụ đã xác nhận.
- Giữ department KH-KD hiện hữu đang làm scope HEAD; mapping rõ thay vì tạo
  phòng trùng. TADIC/TACICO cùng company. Không tự suy hierarchy 9 nhóm.
- Các thao tác/aggregate/export bảo mật ở backend; staff qua public directory,
  HR riêng và quyền lương giữ native. Hồ sơ nhân viên và hợp đồng TP Contracts
  là hai miền khác nhau.

## 3. Lộ trình và đầu ra

| Chặng | Phạm vi | Kết quả có thể nghiệm thu |
| --- | --- | --- |
| A | Re-inventory, backup, dọn mẫu HR/account trên test, chặn nạp mẫu lại | Manifest giữ/archive/xóa/chưa rõ, 3 fixture có căn cứ được xử lý, tài khoản/admin/KH-KD không gán nhầm |
| B | Metadata mã TP, mapping đơn vị, preview/import idempotent bằng ORM | 39 nhân viên thật/9 nhóm nguồn, không 78 người; mã TP đúng và retry 0 trùng |
| C | CRUD hồ sơ, version, danh mục, kỹ năng/hồ sơ, public/private | List/form và thêm/sửa/lưu trữ/khôi phục thực; phân quyền/model/file kiểm được |
| D | Sidebar/bảng/form và Home HR theo format KH-KD | Một navbar, sidebar trái menu thật, mọi bảng search/filter/group/page 10/20/50/100, responsive/hover/motion |
| E | Overview và báo cáo Excel | Donut 39 người/9 đơn vị, KPI/bảng/drilldown/export cùng nguồn/quyền/filter; không số giả |
| F | Kiểm tra hồi quy, backup/restore, áp main 18069 và import nguồn thật | Main dùng được, roster/dashboard/export đối chiếu đúng, KD giữ hoạt động, workflow/guide/rollback |

Mỗi chặng có acceptance/tests trước và handoff. Không dừng ở thiết kế khi được
giao prompt thực thi, không đánh dấu chặng sau hoàn thành vì đã có sidebar/menu.
Test dùng DB chuẩn 18079 với độc quyền ghi; không tạo taskDB. Không reset toàn
test đè main; áp code/migration/import đã kiểm. Prompt cho phép rollout đúng
phạm vi lên 18069 sau cổng kỹ thuật/backup, không mở payroll hoặc pilot công ty.

## 4. Khung chức năng HR Foundation

Nhân viên: list/form, mã/đơn vị/chức danh, tìm/lọc/nhóm, tạo/sửa/kiểm trùng,
lưu trữ/khôi phục, phiên bản công tác, tài khoản liên kết, lịch sử. Tổ chức:
danh mục/đếm nhân viên, sơ đồ theo quan hệ có dữ liệu. Hồ sơ: trường/file cá
nhân có quyền, kỹ năng native, chứng chỉ canonical có scope. Vận hành dữ liệu:
preview/import/history, báo thiếu trường, đối chiếu account. Báo cáo: tổng hợp
và XLSX có filter/whitelist/chống formula injection. Không hard-delete hồ sơ
đã nhập/có lịch sử; lưu trữ hồ sơ khác khóa user hoặc quyết định nghỉ việc.

Dashboard ưu tiên cơ cấu, chất lượng và thao tác: KPI hồ sơ/đơn vị/chờ liên kết,
donut theo đơn vị, thanh ngang đối chiếu, bảng thiếu thông tin. Population có
định nghĩa, filter và drilldown tương ứng; không lấy active=True làm xác nhận
nhân viên chính thức. Thiếu ngày công/lương/ngày vào-nghỉ không vẽ chỉ số đó.

Tái sử dụng phong cách KH-KD có adapter HR riêng cho các component đang gắn
cứng KD_APP_XMLID/prefs/capability. Không sao toàn phần nghiệp vụ/đồng thời
hai sidebar hoặc refactor platform lớn. Giữ Home admin 7 mục và login hiện hữu.

## 5. Đầu vào còn cần cho các chặng mở rộng

| Mảng tiếp theo | Thông tin còn thiếu |
| --- | --- |
| Danh tính/account | Whitelist alias user → mã nguồn; ai được dùng/cấp tài khoản, ai phụ trách HR thực tế |
| Cơ cấu | Quan hệ quản lý trực tiếp, hierarchy và địa điểm làm việc đã xác nhận |
| Hồ sơ | Ngày sinh/liên hệ/ngày vào làm/hợp đồng/chứng chỉ và phạm vi người được xem |
| Chấm công | Lịch/ca/múi giờ/nghỉ/ngoại lệ, cách ghép nhiều lượt vào-ra, công trường, tăng ca và phê duyệt |
| Nghỉ phép | Loại phép/quỹ phép/ngày lễ/ủy quyền/duyệt |
| Lương/BHXH/thuế | Công thức, mức lương/phụ cấp/khấu trừ/chu kỳ/chốt và người có quyền |
| Tuyển dụng/đánh giá | Quy trình ứng viên/tiêu chí/vòng duyệt/bảo quản CV và thang đánh giá |

Các mục này không cản hồ sơ/mã/roster/sidebar/dashboard nền. Không coi đầy đủ
HR Foundation là đã hoàn thành toàn nghiệp vụ nhân sự/lương/tuyển dụng.

## 6. Giới hạn của phiên lập kế hoạch

Đã đọc workbook, độc lập kiểm XML, so nguồn trước, kiểm source và SELECT
runtime. Đã chuẩn bị prompt/decision/handoff. Chưa dọn 3 employee, archive user,
link user, nhập 39 người, tạo module hoặc sửa giao diện. Quyền cũ và dữ liệu hiện
hữu chưa bị đổi. Prompt được giao cho phiên thực thi kế tiếp; đây không phải
nghiệm thu nghiệp vụ, audit độc lập hay xác nhận pilot.
