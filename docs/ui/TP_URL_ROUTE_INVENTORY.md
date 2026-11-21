# Bảng kiểm kê đường dẫn toàn hệ thống TANPHAT ONE (TP_URL_ROUTE_INVENTORY)

> **Mã tài liệu:** TP-URL-INV-001  
> **Nhiệm vụ:** SYSTEM-URL-001  
> **Áp dụng:** Toàn bộ màn hình hệ thống trên domain `https://tpone.tadic.vn`  
> **Ngày lập:** 20/11/2026  
> **Phiên bản:** 1.0.0  

---

## 1. Tổng hợp phân hệ và cấu trúc URL

Hệ thống TANPHAT ONE bao gồm 6 nhóm phân hệ nghiệp vụ chính và phân hệ quản trị hệ thống:

| Phân hệ | Tiền tố URL chuẩn | Tên hiển thị phân hệ | Đối tượng người dùng chính |
| :--- | :--- | :--- | :--- |
| **Trang chủ** | `/app/trang-chu` | Trang chủ điều hành | Toàn bộ cán bộ nhân viên |
| **TP HR (Nhân sự)** | `/app/nhan-su/...` | Quản lý nhân sự | Ban Giám đốc, Nhân sự, Nhân viên |
| **TP HR (Chấm công)** | `/app/nhan-su/cham-cong/...` | Chấm công & dữ liệu ENTI | Ban Giám đốc, Nhân sự, Cán bộ chấm công, Nhân viên |
| **TP KH-KD** | `/app/khkd/...` | Kế hoạch Kinh doanh & Dự án | Ban Giám đốc, Phòng KH-KD, Quản lý dự án |
| **TP Thiết bị** | `/app/thiet-bi/...` | Quản lý thiết bị & kho | Ban Giám đốc, Quản lý thiết bị, Nhân viên |
| **TP Báo cáo** | `/app/bao-cao/...` | Báo cáo điều hành | Ban Giám đốc, Trưởng phòng, Nhân viên |
| **Quản trị hệ thống** | `/app/quan-tri/...` | Cài đặt & Quản trị | Quản trị gốc, Quản trị ủy quyền (`tp_admin_delegation`) |

---

## 2. Bảng kê chi tiết từng màn hình (Inventory)

### 2.1. Phân hệ Trang chủ

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Trang chủ** | Trang chủ | `tp_web_home.menu_home` | `tp_web_home.action_home`<br>*(tag: `tp_web_home.home`)* | `/app/tp-home` | `/app/trang-chu` | `base.group_user` (Mọi nhân viên) | Trang chủ launcher chứa các catalog phân hệ |

---

### 2.2. Phân hệ Nhân sự (`nhan-su`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | **Tổng quan nhân sự (Admin)** | Nhân sự | `tp_hr_workspace.menu_hr` | `tp_hr_workspace.action_overview`<br>*(tag: `tp_hr_workspace.overview`)* | `/app/tp-hr` | `/app/nhan-su/tong-quan` | `hr.group_hr_user`, `group_full_admin` | Dashboard thống kê nhân sự toàn diện |
| 3 | **Tổng quan nhân sự (Nhân viên)** | Nhân sự | `tp_hr_workspace.menu_hr` | `tp_hr_workspace.action_public_overview`<br>*(tag: `tp_hr_workspace.overview`)* | `/app/tp-hr-tong-quan` | `/app/nhan-su/tong-quan` | `base.group_user` (Chỉ xem theo DEC-062) | Dashboard rút gọn thông tin chung |
| 4 | **Danh sách nhân viên** | Nhân sự | `tp_hr_workspace.menu_employees` | `tp_hr_workspace.action_employees`<br>*(model: `hr.employee`)* | `/app/action-528` | `/app/nhan-su/nhan-vien` | `base.group_user` (quyền xem chung; ẩn 3 tab nhạy cảm) | - Danh sách: `/app/nhan-su/nhan-vien`<br>- Chi tiết: `/app/nhan-su/nhan-vien/<id>`<br>- Tạo mới: `/app/nhan-su/nhan-vien/tao-moi` |
| 5 | **Phòng ban và đơn vị** | Nhân sự | `tp_hr_workspace.menu_departments` | `tp_hr_workspace.action_departments`<br>*(model: `hr.department`)* | `/app/action-531` | `/app/nhan-su/phong-ban` | `hr.group_hr_user`, `group_full_admin` | - Danh sách: `/app/nhan-su/phong-ban`<br>- Chi tiết: `/app/nhan-su/phong-ban/<id>`<br>- Tạo mới: `/app/nhan-su/phong-ban/tao-moi` |
| 6 | **Chức vụ** | Nhân sự | `tp_hr_workspace.menu_jobs` | `tp_hr_workspace.action_jobs`<br>*(model: `hr.job`)* | `/app/action-532` | `/app/nhan-su/chuc-vu` | `hr.group_hr_user`, `group_full_admin` | - Danh sách: `/app/nhan-su/chuc-vu`<br>- Chi tiết: `/app/nhan-su/chuc-vu/<id>`<br>- Tạo mới: `/app/nhan-su/chuc-vu/tao-moi` |
| 7 | **Hồ sơ cần bổ sung** | Nhân sự | `tp_hr_workspace.menu_missing` | `tp_hr_workspace.action_missing`<br>*(model: `hr.employee`)* | `/app/action-xxx` | `/app/nhan-su/ho-so-can-bo-sung` | `hr.group_hr_user`, `group_full_admin` | - Danh sách: `/app/nhan-su/ho-so-can-bo-sung`<br>- Chi tiết: `/app/nhan-su/ho-so-can-bo-sung/<id>` |
| 8 | **Lưu trữ nhân viên** | Nhân sự | `tp_hr_workspace.menu_archived` | `tp_hr_workspace.action_archived`<br>*(model: `hr.employee`)* | `/app/action-xxx` | `/app/nhan-su/luu-tru` | `hr.group_hr_user`, `group_full_admin` | - Danh sách: `/app/nhan-su/luu-tru`<br>- Chi tiết: `/app/nhan-su/luu-tru/<id>` |
| 9 | **Hồ sơ của tôi** | Nhân sự | `tp_hr_workspace.menu_my_profile` | `tp_hr_workspace.action_my_profile`<br>*(tag: `tp_hr_workspace.my_profile`)* | `/app/my-profile` | `/app/nhan-su/ho-so-cua-toi` | `base.group_user` (Cá nhân tự phục vụ) | Thông tin cá nhân, bằng cấp, kỹ năng, tài khoản |
| 10 | **Phòng ban của tôi** | Nhân sự | `tp_hr_workspace.menu_department_workspace` | `tp_hr_workspace.action_department_workspace`<br>*(tag: `tp_department_workspace`)* | `/app/action-540` | `/app/nhan-su/phong-ban-cua-toi` | `base.group_user` (Theo phòng ban của user) | Workspace trao đổi & công việc phòng ban |
| 11 | **Nhật ký xóa hồ sơ và sửa mã** | Nhân sự | `tp_hr_workspace.menu_audit` | `tp_hr_workspace.action_employee_audit`<br>*(model: `tp.hr.employee.audit`)* | `/app/action-542` | `/app/nhan-su/nhat-ky-ho-so` | `base.group_system`, `group_full_admin` | - Danh sách: `/app/nhan-su/nhat-ky-ho-so`<br>- Chi tiết: `/app/nhan-su/nhat-ky-ho-so/<id>` |

---

### 2.3. Phân hệ Chấm công (`nhan-su/cham-cong`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 12 | **Tổng quan chấm công** | Chấm công | `tp_hr_attendance.menu_dashboard` | `tp_hr_attendance.action_dashboard`<br>*(tag: `tp_hr_attendance.dashboard`)* | `/app/cham-cong` | `/app/nhan-su/cham-cong/tong-quan` | `base.group_user` | Dashboard 3 thẻ gọn, danh sách quẹt live ENTI |
| 13 | **Công của tôi** | Chấm công | `tp_hr_attendance.menu_mine` | `tp_hr_attendance.action_mine`<br>*(tag: `tp_hr_attendance.mine`)* | `/app/cong-cua-toi` | `/app/nhan-su/cham-cong/cua-toi` | `base.group_user` | Lịch công tháng, giờ vào/ra thực tế của cá nhân |
| 14 | **Cấu hình kết nối (ENTI)** | Chấm công | `tp_hr_attendance.menu_enti_config` | `tp_hr_attendance.action_enti_config`<br>*(model: `tp.hr.attendance.enti.config.wizard`)* | `/app/action-xxx` | `/app/nhan-su/cham-cong/cau-hinh` | `group_attendance_officer`, `group_full_admin` | Cấu hình API, mật khẩu, tunnel máy chấm công |
| 15 | **Đối chiếu nhân viên ENTI** | Chấm công | `tp_hr_attendance.menu_enti_mapping` | `tp_hr_attendance.action_enti_mapping`<br>*(model: `tp.hr.attendance.enti.mapping`)* | `/app/action-xxx` | `/app/nhan-su/cham-cong/doi-chieu-nhan-vien` | `group_attendance_officer`, `group_full_admin` | - Danh sách: `/app/nhan-su/cham-cong/doi-chieu-nhan-vien`<br>- Chi tiết: `/app/nhan-su/cham-cong/doi-chieu-nhan-vien/<id>` |
| 16 | **Nhật ký đồng bộ chấm công** | Chấm công | `tp_hr_attendance.menu_sources` | `tp_hr_attendance.action_enti_logs`<br>*(model: `tp.hr.attendance.enti.log`)* | `/app/nguon-cham-cong` | `/app/nhan-su/cham-cong/nhat-ky-dong-bo` | `group_attendance_officer`, `group_full_admin` | - Danh sách: `/app/nhan-su/cham-cong/nhat-ky-dong-bo`<br>- Chi tiết: `/app/nhan-su/cham-cong/nhat-ky-dong-bo/<id>` |
| 17 | **Xử lý điều chỉnh công** | Chấm công | `tp_hr_attendance.menu_review` | `tp_hr_attendance.action_review`<br>*(model: `tp.hr.attendance.correction`)* | `/app/action-xxx` | `/app/nhan-su/cham-cong/dieu-chinh` | Duyệt: Admin chính & Admin ủy quyền (DEC-061) | - Danh sách: `/app/nhan-su/cham-cong/dieu-chinh`<br>- Chi tiết: `/app/nhan-su/cham-cong/dieu-chinh/<id>`<br>- Tạo đề nghị: `/app/nhan-su/cham-cong/dieu-chinh/tao-moi` |
| 18 | **Chốt kỳ công** | Chấm công | `tp_hr_attendance.menu_periods` | `tp_hr_attendance.action_periods`<br>*(model: `tp.hr.attendance.period`)* | `/app/action-632` | `/app/nhan-su/cham-cong/chot-ky` | `group_attendance_officer`, `group_full_admin` | - Danh sách: `/app/nhan-su/cham-cong/chot-ky`<br>- Chi tiết: `/app/nhan-su/cham-cong/chot-ky/<id>` |
| 19 | **Bảng ngày công** | Chấm công | `tp_hr_attendance.menu_days` | `tp_hr_attendance.action_days`<br>*(model: `tp.hr.attendance.day`)* | `/app/action-622` | `/app/nhan-su/cham-cong/bang-cong` | `group_attendance_officer`, `group_full_admin` | - Danh sách: `/app/nhan-su/cham-cong/bang-cong`<br>- Chi tiết: `/app/nhan-su/cham-cong/bang-cong/<id>` |
| 20 | **Tổng đi muộn theo kỳ** | Chấm công | `tp_hr_attendance.menu_late` | `tp_hr_attendance.action_late`<br>*(model: `tp.hr.attendance.late`)* | `/app/action-636` | `/app/nhan-su/cham-cong/di-muon` | `group_attendance_officer`, `group_full_admin` | Báo cáo tổng hợp số phút muộn nhân sự |

---

### 2.4. Phân hệ Kế hoạch Kinh doanh (`khkd`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 21 | **Tổng quan KH-KD** | KH-KD | `tp_kd_workspace.menu_overview` | `tp_kd_workspace.action_overview`<br>*(model: `tp.kd.overview`)* | `/app/action-510` | `/app/khkd/tong-quan` | Phòng KH-KD, Ban Giám đốc | Dashboard điều hành kinh doanh & dự án |
| 22 | **Dự án tiềm năng** | KH-KD | `tp_kd_workspace.menu_opportunities` | `tp_kd_workspace.action_opportunities`<br>*(model: `crm.lead`)* | `/app/action-512` | `/app/khkd/du-an-tiem-nang` | Phòng KH-KD, Ban Giám đốc | - Danh sách: `/app/khkd/du-an-tiem-nang`<br>- Chi tiết: `/app/khkd/du-an-tiem-nang/<id>`<br>- Tạo mới: `/app/khkd/du-an-tiem-nang/tao-moi` |
| 23 | **Đấu thầu** | KH-KD | `tp_kd_workspace.menu_packages` | `tp_kd_workspace.action_packages`<br>*(model: `tp.bid.package`)* | `/app/action-522` | `/app/khkd/dau-thau` | Phòng KH-KD, Ban Giám đốc | - Danh sách: `/app/khkd/dau-thau`<br>- Chi tiết: `/app/khkd/dau-thau/<id>`<br>- Tạo mới: `/app/khkd/dau-thau/tao-moi` |
| 24 | **Hồ sơ thầu** | KH-KD | `tp_kd_workspace.menu_reconcile` | `tp_kd_workspace.action_reconcile`<br>*(model: `crm.lead`)* | `/app/action-523` | `/app/khkd/ho-so-thau` | Phòng KH-KD, Ban Giám đốc | - Danh sách: `/app/khkd/ho-so-thau`<br>- Chi tiết: `/app/khkd/ho-so-thau/<id>` |
| 25 | **Hợp đồng (TP Contracts)** | KH-KD | `tp_kd_workspace.menu_contracts` | `tp_contract.action_tp_contracts_list`<br>*(model: `tp.contract`)* | `/app/action-xxx` | `/app/khkd/hop-dong` | Phòng KH-KD, Ban Giám đốc | - Danh sách: `/app/khkd/hop-dong`<br>- Chi tiết: `/app/khkd/hop-dong/<id>`<br>- Tạo mới: `/app/khkd/hop-dong/tao-moi` |
| 26 | **Quản lý dự án** *(Thực hiện)* | KH-KD | `tp_kd_workspace.menu_management` | `tp_kd_workspace.action_management`<br>*(model: `tp.project.perspective`)* | `/app/action-524` | `/app/khkd/quan-ly-du-an` | Quản lý dự án, Ban Giám đốc | Góc nhìn điều hành tiến độ, hiện trường và sản lượng |
| 27 | **Quản trị dự án** *(Giám sát)* | KH-KD | `tp_kd_workspace.menu_governance` | `tp_kd_workspace.action_governance`<br>*(model: `tp.project.perspective`)* | `/app/action-525` | `/app/khkd/quan-tri-du-an` | Ban Giám đốc, Quản trị viên | Góc nhìn giám sát pháp lý, tài chính, hợp đồng |
| 28 | **Báo cáo KH-KD** | KH-KD | `tp_kd_workspace.menu_reports` | `tp_kd_workspace.action_reports`<br>*(model: `tp.kd.report.center`)* | `/app/action-xxx` | `/app/khkd/bao-cao` | Phòng KH-KD, Ban Giám đốc | Báo cáo doanh thu, tiến độ và tỷ lệ trúng thầu |
| 29 | **Hạng mục / WBS** | KH-KD | `tp_kd_workspace.menu_wbs` | `tp_kd_workspace.action_wbs`<br>*(model: `project.task`)* | `/app/action-526` | `/app/khkd/wbs` | Quản lý dự án, Phòng KH-KD | - Danh sách: `/app/khkd/wbs`<br>- Chi tiết: `/app/khkd/wbs/<id>` |

---

### 2.5. Phân hệ Thiết bị (`thiet-bi`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 30 | **Tổng quan thiết bị** | Thiết bị | `tp_equipment.menu_dashboard` | `tp_equipment.action_dashboard`<br>*(tag: `tp_equipment.dashboard`)* | `/app/tong-quan-thiet-bi` | `/app/thiet-bi/tong-quan` | Ban Giám đốc, Quản lý thiết bị | Dashboard KPI thiết bị, tỷ lệ sử dụng, cảnh báo |
| 31 | **Danh sách thiết bị** | Thiết bị | `tp_equipment.menu_equipment` | `tp_equipment.action_equipment`<br>*(model: `maintenance.equipment`)* | `/app/kho-thiet-bi` | `/app/thiet-bi/danh-sach` | Quản lý thiết bị | - Danh sách: `/app/thiet-bi/danh-sach`<br>- Chi tiết: `/app/thiet-bi/danh-sach/<id>`<br>- Tạo mới: `/app/thiet-bi/danh-sach/tao-moi` |
| 32 | **Thiết bị tồn kho** | Thiết bị | `tp_equipment.menu_equipment_stock` | `tp_equipment.action_equipment_stock`<br>*(model: `maintenance.equipment`)* | `/app/ton-kho-thiet-bi` | `/app/thiet-bi/ton-kho` | Quản lý thiết bị | - Danh sách: `/app/thiet-bi/ton-kho`<br>- Chi tiết: `/app/thiet-bi/ton-kho/<id>` |
| 33 | **Yêu cầu đề xuất thiết bị** | Thiết bị | `tp_equipment.menu_proposals` | `tp_equipment.action_proposals`<br>*(model: `tp.equipment.proposal`)* | `/app/de-xuat-thiet-bi` | `/app/thiet-bi/de-xuat` | Mọi nhân viên đề xuất / Quản lý duyệt | - Danh sách: `/app/thiet-bi/de-xuat`<br>- Chi tiết: `/app/thiet-bi/de-xuat/<id>`<br>- Tạo mới: `/app/thiet-bi/de-xuat/tao-moi` |
| 34 | **Phiếu bàn giao / thu hồi** | Thiết bị | `tp_equipment.menu_moves` | `tp_equipment.action_moves`<br>*(model: `tp.equipment.move`)* | `/app/phieu-thiet-bi` | `/app/thiet-bi/phieu-ban-giao` | Quản lý thiết bị | - Danh sách: `/app/thiet-bi/phieu-ban-giao`<br>- Chi tiết: `/app/thiet-bi/phieu-ban-giao/<id>` |
| 35 | **Sửa chữa / bảo trì** | Thiết bị | `tp_equipment.menu_repairs` | `tp_equipment.action_repairs`<br>*(model: `maintenance.request`)* | `/app/sua-chua-thiet-bi` | `/app/thiet-bi/sua-chua` | Quản lý thiết bị | - Danh sách: `/app/thiet-bi/sua-chua`<br>- Chi tiết: `/app/thiet-bi/sua-chua/<id>` |
| 36 | **Kiểm kê thiết bị** | Thiết bị | `tp_equipment.menu_inventories` | `tp_equipment.action_inventories`<br>*(model: `tp.equipment.inventory`)* | `/app/kiem-ke-thiet-bi` | `/app/thiet-bi/kiem-ke` | Quản lý thiết bị | - Danh sách: `/app/thiet-bi/kiem-ke`<br>- Chi tiết: `/app/thiet-bi/kiem-ke/<id>` |

---

### 2.6. Phân hệ Báo cáo (`bao-cao`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 37 | **Tổng quan báo cáo** | Báo cáo | `tp_reporting.menu_dashboard` | `tp_reporting.action_dashboard`<br>*(tag: `tp_reporting.dashboard`)* | `/app/bao-cao-tong-quan` | `/app/bao-cao/tong-quan` | `base.group_user` (Mọi nhân viên) | Dashboard tổng hợp nghĩa vụ, mục tiêu, kết quả |
| 38 | **Mục tiêu và kế hoạch** | Báo cáo | `tp_reporting.menu_plans` | `tp_reporting.action_plans`<br>*(model: `tp.report.plan`)* | `/app/bao-cao-plans` | `/app/bao-cao/muc-tieu` | Ban Giám đốc, Trưởng phòng | - Danh sách: `/app/bao-cao/muc-tieu`<br>- Chi tiết: `/app/bao-cao/muc-tieu/<id>`<br>- Tạo mới: `/app/bao-cao/muc-tieu/tao-moi` |
| 39 | **Báo cáo của tôi (Cá nhân)** | Báo cáo | `tp_reporting.menu_personal` | `tp_reporting.action_personal`<br>*(model: `tp.report.document`)* | `/app/bao-cao-personal` | `/app/bao-cao/ca-nhan` | `base.group_user` (Cá nhân) | - Danh sách: `/app/bao-cao/ca-nhan`<br>- Chi tiết: `/app/bao-cao/ca-nhan/<id>`<br>- Tạo mới: `/app/bao-cao/ca-nhan/tao-moi` |
| 40 | **Báo cáo phòng ban** | Báo cáo | `tp_reporting.menu_department` | `tp_reporting.action_department`<br>*(model: `tp.report.document`)* | `/app/bao-cao-department` | `/app/bao-cao/phong-ban` | Trưởng phòng, Quản lý | - Danh sách: `/app/bao-cao/phong-ban`<br>- Chi tiết: `/app/bao-cao/phong-ban/<id>`<br>- Tạo mới: `/app/bao-cao/phong-ban/tao-moi` |
| 41 | **Báo cáo công ty** | Báo cáo | `tp_reporting.menu_company` | `tp_reporting.action_company`<br>*(model: `tp.report.document`)* | `/app/bao-cao-company` | `/app/bao-cao/cong-ty` | Ban Giám đốc | - Danh sách: `/app/bao-cao/cong-ty`<br>- Chi tiết: `/app/bao-cao/cong-ty/<id>` |
| 42 | **Chờ tôi rà soát** | Báo cáo | `tp_reporting.menu_my_review` | `tp_reporting.action_my_review`<br>*(model: `tp.report.document`)* | `/app/bao-cao-cho-ra-soat` | `/app/bao-cao/cho-ra-soat` | Người có quyền duyệt báo cáo | - Danh sách: `/app/bao-cao/cho-ra-soat`<br>- Chi tiết: `/app/bao-cao/cho-ra-soat/<id>` |

---

### 2.7. Phân hệ Quản trị hệ thống (`quan-tri`)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL trước SYSTEM-URL-001 | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 43 | **Cài đặt hệ thống** | Quản trị | `base.menu_administration` | `base.action_server_action` | `/app/action-xxx` | `/app/quan-tri/cai-dat` | `base.group_system` | Màn hình cấu hình thông số hệ thống |
| 44 | **Tài khoản người dùng** | Quản trị | `base.menu_users` | `base.action_res_users`<br>*(model: `res.users`)* | `/app/users` | `/app/quan-tri/tai-khoan` | `group_full_admin`, `base.group_system` | - Danh sách: `/app/quan-tri/tai-khoan`<br>- Chi tiết: `/app/quan-tri/tai-khoan/<id>`<br>- Tạo mới: `/app/quan-tri/tai-khoan/tao-moi` |
| 45 | **Ứng dụng hệ thống** | Quản trị | `base.menu_module_tree` | `base.open_module_tree`<br>*(model: `ir.module.module`)* | `/app/apps` | `/app/quan-tri/ung-dung` | `base.group_system` | - Danh sách: `/app/quan-tri/ung-dung`<br>- Chi tiết: `/app/quan-tri/ung-dung/<id>` |
| 46 | **Thông tin công ty** | Quản trị | `base.menu_action_res_company_form` | `base.action_res_company_form`<br>*(model: `res.company`)* | `/app/companies` | `/app/quan-tri/cong-ty` | `base.group_system` | - Danh sách: `/app/quan-tri/cong-ty`<br>- Chi tiết: `/app/quan-tri/cong-ty/<id>` |

---

### 2.8. Phân hệ Đề nghị & Phê duyệt (`de-nghi` — `tp_request` 20.0.1.0.0)

| STT | Tên hiển thị | Phân hệ | Menu XML ID | Action XML ID / Tag | URL cũ / Alias | URL chuẩn mới | Quyền truy cập | Trang con / Biến thể |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 47 | **Tổng quan Đề nghị** | Đề nghị & Phê duyệt | `tp_request.menu_overview` | `tp_request.action_overview`<br>*(tag: `tp_request.dashboard`)* | `/app/de-nghi`, `/app/de-nghi-tong-quan` | `/app/de-nghi/tong-quan` | `base.group_user` | KPI vai trò, biểu đồ Chart.js dữ liệu thật, hàng đợi cần xử lý |
| 48 | **Đề nghị của tôi** | Đề nghị & Phê duyệt | `tp_request.menu_mine` | `tp_request.action_mine`<br>*(tag: `tp_request.list`)* | `/app/de-nghi-cua-toi` | `/app/de-nghi/cua-toi` | `base.group_user` | Tab trạng thái, lọc đa tiêu chí, xuất Excel đúng quyền |
| 49 | **Cần tôi duyệt** | Đề nghị & Phê duyệt | `tp_request.menu_to_approve` | `tp_request.action_to_approve`<br>*(tag: `tp_request.list`)* | `/app/de-nghi-can-duyet` | `/app/de-nghi/can-duyet` | `base.group_user` | Hồ sơ đang đến lượt người đăng nhập phê duyệt |
| 50 | **Cần thực hiện** | Đề nghị & Phê duyệt | `tp_request.menu_to_execute` | `tp_request.action_to_execute`<br>*(tag: `tp_request.list`)* | `/app/de-nghi-can-thuc-hien` | `/app/de-nghi/can-thuc-hien` | `base.group_user` | Hồ sơ đã duyệt chờ người thực hiện triển khai |
| 51 | **Theo dõi** | Đề nghị & Phê duyệt | `tp_request.menu_watching` | `tp_request.action_watching`<br>*(tag: `tp_request.list`)* | `/app/de-nghi-theo-doi` | `/app/de-nghi/theo-doi` | `base.group_user` | Hồ sơ được cấp quyền theo dõi hoặc đã tham gia duyệt/thực hiện |
| 52 | **Quản trị Đề nghị** | Đề nghị & Phê duyệt | `tp_request.menu_admin` | `tp_request.action_admin`<br>*(tag: `tp_request.admin`)* | `/app/de-nghi-quan-tri` | `/app/de-nghi/quan-tri` | `group_request_manager`, `group_original_admin`, `group_full_admin`, `base.group_system` | Danh mục loại đề nghị & tuyến duyệt + Toàn bộ hồ sơ công ty |
| 53 | **Chi tiết hồ sơ đề nghị** | Đề nghị & Phê duyệt | *(Mở từ danh sách / thông báo)* | `tp_request.action_detail`<br>*(tag: `tp_request.detail`)* | `/app/de-nghi-ho-so/<id>` | `/app/de-nghi/ho-so/<id>` | Theo quyền từng hồ sơ (`tp.request` read) | Chi tiết 2 cột, tuyến tuần tự, phê duyệt, thực hiện, trao đổi, lịch sử bất biến |

---

## 3. Quy tắc ánh xạ tương thích ngược (Backward Compatibility Mapping)

Để đảm bảo người dùng mở các bookmark cũ, liên kết trong email hoặc chatter không gặp lỗi, hệ thống tự động nhận diện và chuẩn hoá các định danh cũ:

| Đường dẫn cũ / Link kỹ thuật | Xử lý khi truy cập | URL chuẩn hoá hiển thị |
| :--- | :--- | :--- |
| `/app/action-528` hoặc `/odoo/action-528` | Nhận diện action ID 528 của `tp_hr_workspace.action_employees` | `/app/nhan-su/nhan-vien` |
| `/app/action-528/44` | Mở đúng chi tiết nhân viên ID 44 | `/app/nhan-su/nhan-vien/44` |
| `/app/tp-home` | Nhận diện alias Trang chủ | `/app/trang-chu` |
| `/app/tp-hr` | Nhận diện alias Tổng quan TP HR | `/app/nhan-su/tong-quan` |
| `/app/cham-cong` | Nhận diện alias Tổng quan chấm công | `/app/nhan-su/cham-cong/tong-quan` |
| `/app/cong-cua-toi` | Nhận diện alias Công của tôi | `/app/nhan-su/cham-cong/cua-toi` |
| `/app/my-profile` | Nhận diện alias Thông tin cá nhân | `/app/nhan-su/ho-so-cua-toi` |
| `/app/kho-thiet-bi` | Nhận diện alias Kho thiết bị | `/app/thiet-bi/danh-sach` |
| `/app/tong-quan-thiet-bi` | Nhận diện alias Tổng quan thiết bị | `/app/thiet-bi/tong-quan` |
| `/app/bao-cao-tong-quan` | Nhận diện alias Tổng quan báo cáo | `/app/bao-cao/tong-quan` |
| `/app/users` | Nhận diện alias Danh sách người dùng | `/app/quan-tri/tai-khoan` |
| `/app/apps` | Nhận diện alias Danh sách ứng dụng | `/app/quan-tri/ung-dung` |
| `/app/companies` | Nhận diện alias Danh sách công ty | `/app/quan-tri/cong-ty` |
| `/web#action=528&id=44` | Chuyển đổi từ hash URL cũ Odoo native | `/app/nhan-su/nhan-vien/44` |
