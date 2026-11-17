# ADMIN-DELEGATE-002 — Nghiệm thu quyền quản trị được ủy quyền theo phạm vi

Ngày 18/11/2026 (Asia/Saigon), CHG-20261118-002 trở đi. Ma trận actor/action/
nguồn lập **trước** khi sửa application, cập nhật theo evidence thực chạy.
Nguồn: [prompt](../prompts/CLAUDE_ADMIN_DELEGATE_002_COMPLETE_SCOPED_ADMIN.md),
[audit chỉ đọc](../security/ADMIN_DELEGATE_002_READONLY_AUDIT.md),
[policy](../security/ADMIN_DELEGATE_001_POLICY.md),
[coverage](../security/ADMIN_DELEGATE_001_COVERAGE.md).

Chỉ thị: áp main 18069 và PC server theo từng slice, commit/push/deploy ngay,
không bắt 18079, không tạo clone/DB khác. Không đổi quyền/assignment người
thật, không grant/revoke thử, không fixture/CRUD phá dữ liệu trên main/server.
Evidence private nằm trong `.local/admin-delegate002/` (ignored): không đưa
danh tính, cookie, mật khẩu, dump hoặc dữ liệu HR vào Git.

## 1. Actor và nguồn thử

| Actor | Môi trường | Cách dùng |
| --- | --- | --- |
| Admin chính (`base.group_system`) | Main 18069, PC server | RPC/shell chỉ đọc; browser admin. |
| Delegate thật đang có ledger hiệu lực | Chỉ PC server (ledger 1/1) | Odoo shell `SET TRANSACTION READ ONLY` + `with_user`, rollback cuối lượt. Không đăng nhập bằng mật khẩu của họ. |
| Nhân viên thường | Main/server | Chỉ đọc `has_access`/count qua `with_user`, rollback. |
| Delegate trên main | Không có ledger (0/0) | Không cấp thử → ca delegate trên main ghi NOT_RUN. |

Nguồn hợp lệ: company/phòng/parent xác định ở backend. Phòng được bảo vệ của
delegate = `_tp_delegation_scope` (hồ sơ nhân viên, vai trò KD, assignment/
grant dự án, CRM team, assignment báo cáo). Unknown, mixed với phòng mình
hoặc khác company giữ baseline.

## 2. Ma trận actor → action → nguồn (lập trước code)

| Miền | Action/RPC | Admin chính | Delegate ngoài phòng | Delegate tại phòng mình / unknown / mixed |
| --- | --- | --- | --- | --- |
| HR | `tp.hr.workspace.get_overview`, KPI/chart/filter, `action_employees`, xuất XLSX | Như cũ | Đọc projection whitelist cùng scope, không nhóm HR, `can_create=false` | Bị loại khỏi tổng hợp/danh sách; baseline danh bạ |
| HR | Account/metadata wizard | Như cũ | Giữ target guard + reauth đã có | Baseline |
| HR | Chấm công import/duyệt/chốt | Assignment | Không mở từ ủy quyền; cấm tự duyệt | Baseline |
| Kho | `tp.equipment.dashboard.get_dashboard`, `open_ui_detail`, `maintenance.equipment.tp_main_summary` | Như cũ | Chạy trên thiết bị đọc được theo scope; không đổi `common.is_admin` | Thiết bị phòng mình/unknown không vào |
| Kho | `tp.equipment.proposal` đọc | Như cũ | Đề xuất người/phòng khác xác định ngoài phòng | Đề xuất của mình/phòng mình/unknown: baseline |
| Kho | Gán/đổi/trả stock chưa có chủ | Như cũ | Kiểm lại dưới lock, đổi máy nguyên tử | Target phòng mình bị chặn |
| KH-KD | Project/WBS/CRM/hợp đồng ghi | Như cũ | Qua command/wizard có sẵn trên record ngoài phòng | Mixed/own: baseline |
| Báo cáo | Dashboard/document/obligation | Lỗi baseline server → sửa riêng: system ngụ ý vai trò cấu hình (không phải reviewer) | Đọc obligation/directive/kế hoạch ngoài phòng; không tự duyệt/chốt, không snapshot/tài chính | Own/mixed: baseline |
| Báo cáo (S2 áp) | Dashboard, hồ sơ, kế hoạch, nghĩa vụ, chỉ đạo, phản hồi, xuất | System ngụ ý cấu hình + người dùng Báo cáo; hàng nghiệp vụ vẫn theo assignment, tự cấp bị chặn | Đọc hồ sơ cá nhân đã gửi/hồ sơ phòng, cả cây kế hoạch, nghĩa vụ, chỉ đạo, phản hồi công khai khi mọi nguồn truy được ngoài phòng; snapshot chỉ đọc; không ghi/duyệt/chốt/tài chính | Nháp/trả lại của người khác, tài chính, cấp công ty, nguồn trộn/unknown: baseline |
| Mọi miền | Settings/Apps, security/ACL/server action, cài module, cấp tiếp admin | Chỉ admin chính | Bị chặn | Bị chặn |

## 3. Bảng AD2

Trạng thái: `PASS` chỉ cho actor/action/nguồn ghi trong evidence; `PARTIAL`
có bằng chứng một phần; `NOT_RUN` chưa chạy. Static check không là PASS ghi.

| ID | Điều kiện | Trạng thái | Evidence / giới hạn |
| --- | --- | --- | --- |
| AD2-01 | Ledger thực, không hardcode actor | PASS (đọc) | Server: actor lấy từ ledger hiệu lực 1/1, capability/scope sống; không grant/revoke thử. |
| AD2-02 | HR/Kho dashboard delegate nhất quán | PASS (đọc) | Server S1: HR KPI = danh sách, Kho 10 ô = danh sách, 0 dòng phòng mình; browser render NOT_RUN. |
| AD2-03 | KH-KD ghi ngoài phòng qua đường thật | NOT_RUN | Slice 4. |
| AD2-04 | Gán/đổi/trả stock, race, mixed/own/unknown | NOT_RUN | Slice 3. |
| AD2-05 | Reporting baseline + delegate | PARTIAL | S2: admin chính vào dashboard/hồ sơ/nghĩa vụ, tự cấp bị chặn (main). Nhánh dữ liệu chưa chạy thật: main 0 hồ sơ/kế hoạch/snapshot; logic SQL kiểm trên CTE tổng hợp; 6 ca Odoo NOT_RUN. |
| AD2-06 | Baseline phòng mình/kiêm nhiệm giữ | NOT_RUN | |
| AD2-07 | RPC/context/nested/import/default không lách | NOT_RUN | |
| AD2-08 | Thu hồi phiên cũ/worker | NOT_RUN | Không grant/revoke thử trên main/server. |
| AD2-09 | Nhân viên thường không mở thêm | PARTIAL | Slice 1 main + server: HR/Kho dashboard, summary, XLSX AccessError; đề xuất 0; không thêm menu. S2 main: 10 model Báo cáo và dashboard vẫn AccessError như HEAD, không menu Báo cáo. Các slice sau kiểm lại. |
| AD2-10 | Browser thực tế desktop/mobile | NOT_RUN | |

## 4. Kết quả theo slice

Cập nhật sau mỗi slice đã áp.

### Slice 1 — HR overview, Kho dashboard/summary/đề xuất (A, B, C-đọc)

- Code: `tp_hr_workspace` thêm hook `_tp_population_source`/`_tp_action_domain`
  (admin/HR giữ nguyên; `can_create` theo quyền tạo thật). `tp_admin_delegation`
  `hr_overview.py`: chỉ actor không có nhóm HR và có ledger; scope phòng của
  mình phải đầy đủ, chọn id bằng quyền của chính actor (công ty đang xem,
  phòng xác định, khác phòng mình), rồi đếm/xuất trên đúng các id đó. Drill-down
  chỉ nhận field whitelist (mã, phòng, chức vụ, tài khoản, liên hệ công việc,
  loại hình) và toán tử `= != in not in`; field private/HR-only/đường dẫn quan hệ
  bị từ chối. Không cấp nhóm HR.
- Kho: `check_admin(env, self)` cho dashboard/drill-down/summary, không đổi
  `common.is_admin`. Đếm chạy bằng quyền đọc đã scope của actor; dòng "Dòng nguồn
  chờ bổ sung" ẩn khi không đọc được lô nhập thay vì báo 0. Đề xuất/dòng/nhật ký
  rà soát đọc được khi người cần, người nhận và thiết bị cũ đều xác định ngoài
  phòng mình; đề xuất do actor tạo/ghi/cần giữ baseline. Ghi/tạo/workflow đề
  xuất vẫn chỉ admin chính.
- Navigation: thêm lá "Tổng quan" HR khi scope đầy đủ, "Yêu cầu đề xuất" Kho khi
  đọc được; nhãn "Quản trị được ủy quyền" trên hai dashboard.
- Kiểm tĩnh: AST/XML/CSV đạt; Ruff đạt cho file mới/sửa (2 lỗi có sẵn ở
  `tp_equipment/models/dashboard.py` HEAD giữ nguyên). Kiểm thuần không DB bộ
  lọc projection: 7 domain hợp lệ nhận, 10 domain sai/HR-only/private/quá dài
  bị từ chối bằng `ValidationError`. Hai ca Odoo mới trong `tests/` NOT_RUN
  (không fixture trên main/server, không 18079/clone).
- Main 18069: backup `.local/admin-delegate002/backup-s1-*` (dump 9.932.588B,
  filestore 998 mục, nguồn/config, `pg_restore -l`, SHA256). Chỉ
  `-u tp_admin_delegation` (HR/Kho chỉ đổi method và template tĩnh; tránh kéo
  Reporting đang dở của batch khác), exit 0/0 ERROR; 20 bảng fingerprint giữ
  nguyên, ledger 0/0. Probe chỉ đọc: admin chính HR 39 hồ sơ/9 đơn vị, drill-down,
  XLSX, Kho 55 hồ sơ, summary, đề xuất 1 và menu như cũ; nhân viên thường vẫn
  AccessError ở HR overview/XLSX/Kho dashboard/summary, đề xuất đếm 0, không thêm
  menu, không đọc Settings.
- PC server (`955c9625`): preflight 16/16 tệp đúng baseline; backup
  `C:/TANPHAT-backups/admin-delegate002/s1-20261118T004531` (dump 9.568.047B,
  filestore 32.054.505B/606 mục, source-config, `pg_restore -l` 15.437 dòng,
  SHA256); `-u tp_admin_delegation` exit 0/0 ERROR, checksum 16/16. Snapshot nhân
  viên 39/tài khoản 29/nhóm/roster/thiết bị 55/đề xuất/ledger/ngày công 252/
  baseURL trước và sau giống hệt, chỉ đổi version.
- Probe chỉ đọc trên server (`SET TRANSACTION READ ONLY` + `with_user`, rollback;
  actor lấy từ ledger hiệu lực 1/1, không hardcode):
  - Delegate: HR tổng 35 = danh sách 35, có tài khoản 8 = 8, thiếu thông tin 0 = 0,
    8 đơn vị, 0 hồ sơ/đơn vị/catalog thuộc phòng mình; lọc phòng mình → 0; lọc
    `private_email` bị từ chối; XLSX tạo được; `can_create` false; có nhãn ủy quyền.
    Kho 24 thiết bị; 10 ô KPI/phân bổ/chất lượng đang hiển thị mở đúng số dòng đã đếm, 0 dòng
    phòng mình; không thấy dòng lô nhập; summary chạy. Đề xuất đọc được 0/1 (bản
    hiện có không thỏa điều kiện ngoài phòng), không quyền ghi/tạo. Không Settings,
    không ghi nhóm, không tạo ledger, không `base.group_system`/nhóm HR. Menu thêm
    Tổng quan HR và Yêu cầu đề xuất, không có menu Quản trị.
  - Admin chính: HR 39/9 đơn vị, Kho 54 vật lý/55 hồ sơ, 10 ô KPI khớp danh sách (ô lô nhập mở action chuỗi domain như cũ),
    đề xuất 1, Settings như cũ. Nhân viên thường: AccessError toàn bộ HR/Kho,
    đề xuất 0, chỉ menu dự án vốn có.
  - Gọi RPC thẳng `open_ui_detail('pending_import')` vẫn trả action cho delegate dù
    dashboard đã ẩn → S1b thêm `check_access` lô/dòng nhập (admin chính vẫn mở).
- Public không đăng nhập: `/web/health` 200, `/dang-nhap` 200, `/web/login` và
  `/odoo` chuyển hướng như cũ. Browser có phiên delegate: NOT_RUN (không dùng mật
  khẩu/phiên của người thật).

### Slice 2 — Báo cáo: baseline admin chính và scope đọc ủy quyền (E)

- Chẩn đoán trước khi sửa (server, chỉ đọc): admin chính có `base.group_system`
  nhưng không có nhóm Báo cáo → dashboard/hồ sơ/nghĩa vụ AccessError
  (`dashboard.py:20`); delegate dừng ở nghĩa vụ (`dashboard.py:29`). Scope cũ
  của delegate mở nháp cá nhân chưa có snapshot (trái baseline riêng tư) và bỏ
  sót mọi hồ sơ đã gửi.
- Admin chính: `data/reporting_admin.xml` cho `base.group_system` ngụ ý
  `tp_reporting.group_reporting_config` (vai trò cấu hình đã chốt, kéo theo
  người dùng Báo cáo). Hàng nghiệp vụ vẫn theo `_tp_report_domain`/assignment:
  không thành reviewer, không thấy nháp người khác, tự cấp assignment vẫn
  AccessError. Không `sudo()` dashboard, không cấp nhóm cho mọi actor, không sửa
  core. Đặt ở `tp_admin_delegation` vì `tp_reporting` đang có source dở của
  batch khác.
- Delegate (`models/reporting_scope.py`), một scope dùng chung cho list/form/
  dashboard/export:
  - nguồn có company/phòng/owner xác định ngoài phòng mình; owner là nhân viên
    hiện tại của phòng xác định, không có hồ sơ khác ở phòng mình/không phòng;
  - hồ sơ cá nhân đã gửi (không nháp/trả lại) và hồ sơ phòng; không giá trị tài
    chính, dự án (nếu có) phải mở;
  - dòng hiện tại, mọi payload snapshot bất biến (header company/phòng/owner
    khớp hồ sơ; plan/project/task trong payload), dòng carry/rollup và
    dependency phải trỏ tới nguồn cũng mở; lặp tới điểm cố định;
  - kế hoạch mở theo cả cây quý → tháng → tuần, một nút phòng mình/unknown/khác
    company/mồ côi đóng cả cây;
  - nghĩa vụ; chỉ đạo khi cả chỉ đạo và hồ sơ gốc ngoài phòng; phản hồi
    `published`; lịch sử; nội dung phần mẫu theo hồ sơ (override chỉ cho
    delegate, nhân viên thường giữ AccessError).
  - Ghi/nộp/rà soát/chốt/chỉ đạo/hợp nhất/tài chính/assignment giữ capability;
    đổi company/phòng/owner/hồ sơ/kế hoạch/cha trên nguồn ngoài phòng bị chặn
    dưới lock. Dashboard thêm nhãn "Quản trị được ủy quyền" và ghi chú số thực
    hiện chỉ cộng báo cáo đã gửi có nguồn mở.
- Navigation: gốc Báo cáo mở dashboard; lá Tổng quan, Kế hoạch, Chỉ đạo và
  "Báo cáo ngoài phòng" (menu ẩn, chỉ thêm khi đọc được, không tạo/sửa/xóa)
  theo capability sống. Settings/Apps/cấu hình Báo cáo giữ admin chính.
- Kiểm tĩnh: Ruff/AST/XML đạt. Logic SQL: chạy đúng câu lệnh của module trên
  CTE tổng hợp cùng tên bảng (không DDL/DML, giao dịch chỉ đọc, rollback) —
  5/5 hồ sơ có dòng/payload/header không truy được bị loại, 4 cạnh nguồn
  (origin, rollup thiếu gốc, dependency thiếu/không phải số), cây kế hoạch bỏ
  nhánh khác company và nút mồ côi. 6 ca Odoo trong `test_reporting_scope.py`
  (nháp riêng, cây kế hoạch, nghĩa vụ/chỉ đạo/dashboard, admin cấu hình không
  thẩm quyền, task/carry/tài chính) NOT_RUN theo chính sách.
- Main 18069: backup `.local/admin-delegate002/backup-s2-20261118T011220` (dump
  9.933.725B, filestore 998 mục, nguồn/config, SHA256). Chỉ
  `-u tp_admin_delegation`, exit 0/0 ERROR; chạy lần hai sau khi thay dòng ACL
  đọc nội dung phần cho mọi nhân viên bằng override chỉ delegate (dòng cũ đã bị
  gỡ). Fingerprint 26 bảng: chỉ `res_groups_implied_rel` +1 và version.
- Probe chỉ đọc main: admin chính có nhóm cấu hình/người dùng Báo cáo; 10 model
  và dashboard chạy (0 dòng), 13 menu Báo cáo, tự cấp AccessError; nhân viên
  thường không nhóm Báo cáo vẫn AccessError cả 10 model/dashboard, không menu.
  Main/server có 0 hồ sơ/kế hoạch/snapshot/nghĩa vụ/chỉ đạo nên nhánh dữ liệu
  chưa chạy thật; delegate trên main NOT_RUN (ledger 0/0).
