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
| KH-KD | Project/WBS/CRM/hợp đồng ghi | Như cũ | Qua command/wizard có sẵn trên record ngoài phòng (S4 áp: tình trạng/ghi chú/lịch sử/giá gói thầu; CRM/HEAD/hồ sơ KD là ngoại lệ) | Mixed/own/unknown: baseline |
| Báo cáo | Dashboard/document/obligation | Lỗi baseline server → sửa riêng: system ngụ ý vai trò cấu hình (không phải reviewer) | Đọc obligation/directive/kế hoạch ngoài phòng; không tự duyệt/chốt, không snapshot/tài chính | Own/mixed: baseline |
| Báo cáo (S2 áp) | Dashboard, hồ sơ, kế hoạch, nghĩa vụ, chỉ đạo, phản hồi, xuất | System ngụ ý cấu hình + người dùng Báo cáo; hàng nghiệp vụ vẫn theo assignment, tự cấp bị chặn | Đọc hồ sơ cá nhân đã gửi/hồ sơ phòng, cả cây kế hoạch, nghĩa vụ, chỉ đạo, phản hồi công khai khi mọi nguồn truy được ngoài phòng; snapshot chỉ đọc; không ghi/duyệt/chốt/tài chính | Nháp/trả lại của người khác, tài chính, cấp công ty, nguồn trộn/unknown: baseline |
| Kho (S3 áp) | Gán / Đổi máy / Trả về kho (`tp_quick_action`, popup) | Như cũ | Kho chung chỉ hiện máy rảnh để chọn; người nhận và máy trả/đổi phải ở phòng khác xác định; khóa máy NOWAIT + nguồn FOR SHARE, kiểm lại company/phòng/version/người giữ rồi chạy đúng RPC gốc trong một giao dịch | Người nhận/máy ở phòng mình, không phòng, khác company, máy có chủ, version cũ: bị chặn; tệp/chatter/sửa/nhãn của máy kho: baseline |
| Mọi miền | Settings/Apps, security/ACL/server action, cài module, cấp tiếp admin | Chỉ admin chính | Bị chặn | Bị chặn |

## 3. Bảng AD2

Trạng thái: `PASS` chỉ cho actor/action/nguồn ghi trong evidence; `PARTIAL`
có bằng chứng một phần; `NOT_RUN` chưa chạy. Static check không là PASS ghi.

| ID | Điều kiện | Trạng thái | Evidence / giới hạn |
| --- | --- | --- | --- |
| AD2-01 | Ledger thực, không hardcode actor | PASS (đọc) | Server: actor lấy từ ledger hiệu lực 1/1, capability/scope sống; không grant/revoke thử. |
| AD2-02 | HR/Kho dashboard delegate nhất quán | PASS (đọc) | Server S1: HR KPI = danh sách, Kho 10 ô = danh sách, 0 dòng phòng mình; browser render NOT_RUN. |
| AD2-03 | KH-KD ghi ngoài phòng qua đường thật | PARTIAL | S4: dự án ngoài phòng mở qua ủy quyền dùng command gốc cho metadata/đối tác/tình trạng/ghi chú/WBS/giao việc/gói thầu của mình/workflow hợp đồng; lịch sử dự án/công việc và giá gói thầu đọc được. Ngoại lệ có chủ đích: tiến độ task (người được giao/HEAD), gói thầu owner khác và thao tác HEAD hợp đồng, ghi CRM hồ sơ dự án (owner-only, chưa adapter), hồ sơ KD baseline. Server sau deploy (delegate ledger 1/1, chỉ đọc): lịch sử dự án/công việc từ không đọc → đọc theo scope (tổng 0/0 dòng), command dự án/công việc và workflow hợp đồng mở, không nhóm CRM/HEAD, không tạo CRM. Main/server 0 dự án được quản lý: hành vi theo bản ghi và ghi thật NOT_RUN. |
| AD2-04 | Gán/đổi/trả stock, race, mixed/own/unknown | PARTIAL | S3: adapter khóa + kiểm lại rồi chạy RPC gốc; main probe chỉ đọc: admin chính như cũ, nhân viên thường 0 máy kho/không tạo popup/AccessError. Server sau deploy (delegate ledger 1/1, chỉ đọc): 7/7 máy rảnh chỉ đọc, 0 ghi/tệp/chatter, popup tạo được, người nhận 35 (0 phòng mình/0 không phòng), in nhãn máy kho AccessError; `tp_quick_action` tới khóa nguồn; người nhận phòng mình và trả máy phòng mình AccessError, người nhận ngoài phòng hợp lệ, máy có chủ UserError. Gán/đổi/trả thật, race hai người và 2 ca Odoo NOT_RUN theo chính sách. |
| AD2-05 | Reporting baseline + delegate | PARTIAL | S2 main + server: admin chính vào dashboard/hồ sơ/nghĩa vụ, tự cấp bị chặn; delegate thật có dashboard nhãn ủy quyền và 9 model đọc, 0 dòng phòng mình, không ghi/assignment. Nhánh dữ liệu chưa chạy thật: cả hai nơi 0 hồ sơ/kế hoạch/snapshot; logic SQL kiểm trên CTE tổng hợp; 6 ca Odoo NOT_RUN. |
| AD2-06 | Baseline phòng mình/kiêm nhiệm giữ | PARTIAL (đọc) | Scope phòng mình gộp hồ sơ nhân viên, vai trò KD, assignment/grant dự án, CRM team, assignment báo cáo; scope chưa đầy đủ thì từ chối. Server: HR 0 hồ sơ/đơn vị phòng mình, lọc phòng mình → 0 (S1); Kho 0 dòng phòng mình (S1); Báo cáo 0 dòng phòng mình (S2); người nhận 0 phòng mình, người nhận/trả máy phòng mình AccessError (S3). Dự án phòng mình không đổi chỉ có ca Odoo S4 (NOT_RUN). Chưa có actor kiêm nhiệm thật để kiểm riêng; ghi thật NOT_RUN. |
| AD2-07 | RPC/context/nested/import/default không lách | PARTIAL | S1: drill-down HR chỉ whitelist field/toán tử (kiểm thuần 17 ca), lọc `private_email` bị từ chối trên server. S1b: RPC thẳng `open_ui_detail('pending_import')` của delegate trên server AccessError (admin chính vẫn mở). S3: `tp_quick_action` bỏ context lạ (`clean_context`), sentinel chạy RPC gốc không giả được qua JSON-RPC, `default_get` chỉ đóng dấu version cho máy đọc được, replay chỉ trả kết quả của chính người gửi. S4: ghi chỉ qua command gốc có version/mã thao tác. Import/nested write thật và fuzz context NOT_RUN. |
| AD2-08 | Thu hồi phiên cũ/worker | NOT_RUN | Thiết kế: mỗi lần đọc/ghi kiểm ledger sống (`_tp_has_admin_delegation`, `lock=True` khi ghi), không ormcache tập ủy quyền; các ca Odoo S3/S4 có bước thu hồi nhưng NOT_RUN. Không grant/revoke thử trên main/server; phiên cũ/nhiều worker chưa chạy. |
| AD2-09 | Nhân viên thường không mở thêm | PARTIAL | Slice 1 main + server: HR/Kho dashboard, summary, XLSX AccessError; đề xuất 0; không thêm menu. S2 main + server: 10 model Báo cáo và dashboard vẫn AccessError như trước, không menu Báo cáo (server giống hệt probe trước deploy). S3 main + server: 0/7 máy kho rảnh, không tạo popup, `tp_quick_action`/mở popup/in nhãn AccessError (server giống hệt trước deploy). S4 main + server: lịch sử dự án/công việc, command, tạo CRM giống hệt trước deploy (chỉ đổi tên module override `_kd_money_read`). |
| AD2-10 | Browser thực tế desktop/mobile | NOT_RUN | Không đăng nhập bằng mật khẩu/phiên người thật, không tạo tài khoản thử. Chỉ smoke public không đăng nhập (`/web/health`, `/dang-nhap`, chuyển hướng `/web/login`, `/odoo`) sau mỗi slice. |

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
- PC server `42682b51`: preflight 12/12 tệp đúng baseline; backup
  `C:/TANPHAT-backups/admin-delegate002/s2-20261118T012716` (dump 9.568.634B,
  filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng,
  SHA256); `-u tp_admin_delegation` exit 0/0 ERROR, checksum 12/12. Snapshot nhân
  viên 39/tài khoản 29/nhóm người dùng/roster/thiết bị/đề xuất/ledger/ngày công/
  Báo cáo (0 hồ sơ/kế hoạch/snapshot/nghĩa vụ/chỉ đạo/assignment)/baseURL giữ;
  chỉ đổi version và `res_groups_implied_rel` 88 → 89. Kiểm SQL chỉ đọc trên dữ
  liệu server trước deploy: 0 hồ sơ/snapshot nên không có payload thật để đối
  chiếu.
- Probe chỉ đọc trên server trước/sau deploy (`SET TRANSACTION READ ONLY` +
  `with_user`, rollback; actor lấy từ ledger hiệu lực 1/1, không hardcode):
  - Admin chính: trước AccessError cả 10 model và dashboard → sau có nhóm cấu
    hình/người dùng Báo cáo (không tài chính), 10 model và dashboard chạy, menu
    Báo cáo đầy đủ, tự cấp assignment AccessError.
  - Delegate: trước lỗi nghĩa vụ/chỉ đạo/snapshot/phản hồi/lịch sử/dashboard →
    sau 9 model và dashboard chạy (nhãn "Quản trị được ủy quyền", thêm ghi chú),
    assignment vẫn AccessError; 0 dòng phòng mình/không phòng/khác company/của
    chính mình, 0 quyền ghi; menu thêm Tổng quan, Kế hoạch, Chỉ đạo, Báo cáo
    ngoài phòng; không Settings, không nhóm Báo cáo/system.
  - Nhân viên thường: kết quả giống hệt probe trước deploy (AccessError 10 model
    và dashboard, không menu Báo cáo).
- Public không đăng nhập: `/web/health` 200, `/dang-nhap` 200, `/web/login` và
  `/odoo` chuyển hướng như cũ. Browser phiên delegate NOT_RUN (không dùng mật
  khẩu/phiên người thật).

### Slice 3 — Kho: máy rảnh trong kho chung và Gán / Đổi máy / Trả về kho (C)

- Chính sách: kho dùng chung công ty không bao giờ là "phòng khác". Delegate
  chỉ thấy máy **rảnh** (trong kho, chưa có người giữ, đang quản lý, không hỏng,
  không chờ bàn giao/sửa) của công ty có ủy quyền để chọn gán/đổi cho phòng
  khác; máy thay thế mua cho người ở phòng mình/không rõ bị ẩn. Đọc này chỉ cho
  danh sách chọn: tệp, chatter, lịch sử, sửa thông tin, in nhãn, đăng ký, tạo
  phiếu trên máy kho vẫn baseline (`_tp_equipment_delegate_check` từ chối máy
  không do phòng khác giữ). Không suy kho là phòng khác, không dùng đường kho
  để đổi máy của phòng mình.
- `models/equipment_handover.py`: delegate gọi đúng `tp_quick_action` (popup
  gốc gọi qua cùng RPC). Thứ tự: capability sống dưới lock → chuẩn hóa payload,
  replay chỉ trả kết quả của chính người đó → khóa máy `ORDER BY id FOR UPDATE
  NOWAIT` (hai người chọn một máy: người sau nhận "đang được xử lý") → khóa
  nguồn FOR SHARE (máy, parent/replaces, người giữ, version HR, phòng, công ty)
  → kiểm lại: một công ty, công ty trong phạm vi và có ủy quyền, scope phòng
  mình đầy đủ, người nhận có phòng hiện tại xác định ngoài phòng mình và không
  phải chính mình, máy trả/đổi do phòng khác giữ, máy mới còn trong kho chưa có
  chủ → chạy `_tp_quick_run` gốc dưới `sudo` có sentinel nội bộ (JSON-RPC không
  giả được), trong savepoint, kiểm hậu điều kiện. Đổi máy = trả A và gán B
  trong một giao dịch; lỗi bất kỳ không đổi bên nào. Version cũ, máy có chủ,
  sai company, người nghỉ, chưa xác minh chưa xác nhận: lỗi như đường gốc.
  Phiếu ghi `create_uid`/`done_by_id` là delegate; follower lọc như gốc.
- Popup `tp.equipment.quick.action`: dòng ACL nhân viên với domain rỗng +
  override chỉ delegate (thấy popup do chính mình tạo); danh sách người nhận bỏ
  phòng mình và người không phòng; version chỉ cho máy đã đọc được. Nhân viên
  thường vẫn không mở được popup.
- Đề xuất của người/phòng khác: S1 chỉ đọc; duyệt/trả lại/thực hiện đề xuất qua
  ủy quyền **chưa có adapter** (gap). Đề xuất của chính mình/phòng mình giữ
  baseline, không tự duyệt.
- Lịch sử: phiếu thiếu phòng frozen (giữ theo người) không mở, không suy từ
  phòng hiện tại của người giữ (giữ nguyên S1).
- Giao diện giữ bản đơn giản: không thêm tab/menu; nhãn ủy quyền nói rõ kho
  chung chỉ để chọn máy rảnh.
- Kiểm tĩnh: Ruff/AST/CSV đạt. 2 ca Odoo mới trong `test_equipment_scope.py`
  (kho chỉ đọc để chọn; gán/đổi/trả chỉ ngoài phòng, replay, máy đã có chủ, đổi
  hỏng không đổi gì, version cũ, thu hồi) NOT_RUN theo chính sách.
- Main 18069: backup `.local/admin-delegate002/backup-s3-20261118T014719` (dump
  9.934.366B, filestore 998 mục, nguồn/config, SHA256). Chỉ
  `-u tp_admin_delegation` → 20.0.1.3.0, exit 0/0 ERROR. Fingerprint 26 bảng giữ
  nguyên, chỉ đổi version. Probe chỉ đọc: 7 máy kho rảnh; admin chính thấy/ghi
  7, mở popup, in nhãn như cũ; nhân viên thường 0 máy, không tạo popup, mở
  popup/in nhãn/`tp_quick_action` AccessError. Delegate trên main NOT_RUN
  (ledger 0/0).
- PC server `1a248463`: preflight 10/10 tệp đúng baseline; backup
  `C:/TANPHAT-backups/admin-delegate002/s3-20261118T015400` (dump 9.570.622B,
  filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng,
  SHA256). `-u tp_admin_delegation` exit 0/0 ERROR, checksum 10/10. Snapshot
  nhân viên/tài khoản/nhóm/roster/thiết bị (55)/đề xuất/ledger/ngày công/Báo
  cáo/baseURL giữ, chỉ đổi version.
- Probe server chỉ đọc (delegate lấy từ ledger 1/1, không đổi quyền ai):
  - Trước deploy: delegate 0 máy kho, không tạo popup, mở popup/in nhãn/
    `tp_quick_action` AccessError; 24 thiết bị giữ ngoài phòng như S1.
  - Sau deploy: 7/7 máy rảnh thấy được (0 bị ẩn), 0 ghi, 0 tệp, 0 chatter; tạo
    popup được (0 popup cũ); người nhận 35, 0 thuộc phòng mình, 0 không phòng;
    mở Gán và `default_get` chạy; in nhãn máy kho AccessError (kho chỉ để
    chọn); 24 thiết bị giữ ngoài phòng giữ nguyên.
  - `tp_quick_action` dừng ở khóa nguồn vì giao dịch chỉ đọc; kiểm chính sách
    trực tiếp: người nhận phòng mình AccessError, trả máy phòng mình
    AccessError, người nhận ngoài phòng hợp lệ, chọn máy đã có chủ UserError.
  - Admin chính và nhân viên thường giống hệt trước deploy.
- Public: `/web/health` 200, `/dang-nhap` 200, `/web/login` và `/odoo` chuyển
  hướng như cũ. Gán/đổi/trả thật, race hai phiên, browser phiên delegate
  NOT_RUN (không dùng mật khẩu/phiên người thật, không CRUD dữ liệu thật).

### Slice 4 — KH-KD: tình trạng/ghi chú/lịch sử dự án và giá gói thầu ngoài phòng (D)

- Chẩn đoán từ source: adapter 001 đã cho dự án ngoài mọi phòng được bảo vệ
  (không hợp đồng/CRM nguồn phòng mình hoặc chưa rõ) capability KD `prepare`,
  `financial.read`/`financial.draft_edit`/hợp đồng và mở `tp.project.command`/
  `tp.task.command` theo `create_uid`. Vì vậy delegate đã sửa metadata, đối tác,
  tạo gói thầu (owner là chính mình), tạo/sửa/giao việc WBS và chạy workflow
  hợp đồng nháp/nộp/rà soát bằng đường gốc. Lỗ còn lại: `_kd_money_read` đòi
  phân công dự án (delegate không bao giờ được cấp), nên nút Tình trạng/Ghi
  chú ẩn, `_kd_apply` từ chối status/note, lịch sử dự án và giá gói thầu không
  đọc được.
- `business_scope.py`: `_kd_money_read` = baseline **hoặc** (đọc được và
  `other_project(lock=True)`: ủy quyền sống, `tp_managed`, phòng dự án ngoài
  phòng mình, nguồn hợp đồng/CRM/team không thuộc phòng mình/không rõ; khóa
  FOR SHARE project/hợp đồng/CRM/team khi ghi). `tp.project.update`/
  `tp.task.update` đọc theo cùng scope dự án. Ghi vẫn qua command gốc: phiên
  bản, mã thao tác, `tp.project.update` ghi actor là delegate. Không cấp
  assignment, KD grant, HEAD; tiền/tài liệu ở dự án phòng mình không tăng
  (ca test kiểm `_kd_money_read`/`kd_can_status`/`kd_can_note` dự án phòng mình
  không đổi sau khi cấp).
- Ngoại lệ giữ (không cấp HEAD, chưa có adapter):
  - Báo tiến độ task: chỉ người được giao hoặc HEAD; delegate giao việc được
    nhưng không báo thay.
  - Sửa gói thầu của owner khác, giao owner/tài liệu/nhận rà soát hợp đồng:
    HEAD.
  - CRM hồ sơ dự án: workflow theo owner (admin chính cũng không chuẩn bị/nộp
    thay owner); delegate không có nhóm CRM; ghi CRM qua ủy quyền chưa có
    adapter.
  - Hồ sơ KD (giao khoán/sản lượng/nghiệm thu/thanh toán/năng lực/nghĩa vụ/kế
    hoạch): baseline. Ký/hiệu lực/tài chính chưa có: không mở.
  - Cấu hình dự án, phân công, KD grant: admin chính.
- Kiểm tĩnh: Ruff/AST đạt. 2 ca Odoo mới trong `test_business_scope.py`
  (tình trạng/ghi chú/lịch sử qua command + dự án phòng mình không đổi + thu
  hồi; WBS giao việc, tiến độ vẫn của người được giao, dự án phòng mình từ chối)
  NOT_RUN theo chính sách.
- Main 18069: backup `.local/admin-delegate002/backup-s4-20261118T020749` (dump
  9.934.484B, filestore 998 mục, nguồn/config, SHA256). Chỉ
  `-u tp_admin_delegation` → 20.0.1.4.0, exit 0/0 ERROR, cảnh báo giống S3.
  Fingerprint 26 bảng giữ, chỉ đổi version. Probe chỉ đọc (kết nối READ ONLY):
  0 dự án được quản lý/0 hợp đồng/0 CRM gắn dự án/0 hồ sơ KD; admin chính và
  nhân viên thường đọc lịch sử theo baseline, override `_kd_money_read` nạp
  đúng module. Delegate trên main NOT_RUN (ledger 0).
- PC server `f91d699c`: preflight 7/7 tệp đúng baseline; backup
  `C:/TANPHAT-backups/admin-delegate002/s4-20261118T050616` (dump 9.570.166B,
  filestore 29.819.146B/597 mục, source-config, `pg_restore -l` 15.437 dòng,
  SHA256). `-u tp_admin_delegation` exit 0/0 ERROR, checksum 7/7. Snapshot
  nhân viên/tài khoản/nhóm/roster/thiết bị/đề xuất/ledger/ngày công/nhóm ngụ
  ý/Báo cáo/baseURL giữ, chỉ đổi version.
- Probe server chỉ đọc (kết nối READ ONLY, delegate lấy từ ledger 1/1, không
  đổi quyền ai), 49 khóa so trước/sau deploy, chỉ 5 khóa đổi:
  - Delegate: `tp.project.update`/`tp.task.update` đọc False → True; đếm dòng
    0/0 (tổng 0/0). Command dự án/công việc, workflow hợp đồng như trước; không
    `scoped_staff`/`core_user`/CRM/system, 0 vai trò HEAD, tạo CRM bị chặn.
  - Override `_kd_money_read` của cả ba actor trỏ module ủy quyền; admin chính
    và nhân viên thường không đổi giá trị nào khác.
  - Server có 0 dự án được quản lý, 0 công việc, 0 hợp đồng, 0 gói thầu, 0 CRM
    gắn dự án, 0 hồ sơ KD: đi qua bản ghi NOT_RUN.
- Public: `/web/health` 200, `/dang-nhap` 200, `/web/login` → `/dang-nhap`,
  `/odoo` → `/app` như cũ. Command thật, race, browser phiên delegate NOT_RUN.

## 5. Tổng kết batch (S1–S4)

| Trạng thái | AD2 |
| --- | --- |
| PASS (đọc) | AD2-01, AD2-02 |
| PARTIAL | AD2-03, AD2-04, AD2-05, AD2-06, AD2-07, AD2-09 |
| NOT_RUN | AD2-08 (thu hồi phiên cũ/worker), AD2-10 (browser) |

- Admin chính: giữ toàn quyền như cũ; cấp/thu ủy quyền qua ledger có lý do và
  xác thực lại; S2 vào được Báo cáo với vai trò cấu hình (không reviewer, không
  tự cấp).
- Delegate (ngoài phòng mình, cùng company, nguồn xác định): HR tổng quan/
  drill-down whitelist/XLSX; Kho dashboard/summary/đề xuất đọc, máy rảnh để chọn
  và Gán/Đổi/Trả qua RPC gốc; Báo cáo đọc hồ sơ đã gửi/kế hoạch/nghĩa vụ/chỉ
  đạo/phản hồi công khai; KH-KD dự án ngoài phòng qua command gốc (metadata,
  đối tác, tình trạng, ghi chú, WBS, giao việc, gói thầu của mình, workflow hợp
  đồng, lịch sử, giá gói thầu). Không Settings/Apps/ACL/server action/module,
  không cấp tiếp admin, không nhóm HR/Báo cáo toàn cục, không HEAD/assignment.
- Phòng mình, unknown, mixed, khác company: baseline ở mọi miền.
- Gap chưa có adapter: duyệt/trả lại/thực hiện đề xuất Kho qua ủy quyền; ghi
  CRM hồ sơ dự án; hồ sơ KD (giao khoán/sản lượng/nghiệm thu/thanh toán/năng
  lực/nghĩa vụ/kế hoạch); phiếu thiết bị thiếu phòng frozen không mở. Ngoại lệ có
  chủ đích: tiến độ task, gói thầu owner khác, thao tác HEAD hợp đồng; chấm công
  import/duyệt/chốt không mở từ ủy quyền.
- Chưa kiểm: 10 ca Odoo mới/sửa (cần môi trường test được phép, không
  18079/clone/fixture trên main/server), ghi thật/race/thu hồi trên dữ liệu thật,
  browser phiên delegate desktop/mobile, nhiều worker.
