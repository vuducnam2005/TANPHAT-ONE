# HR-EMP-014 — Checklist và bằng chứng

Ngày 13/11/2026. Yêu cầu trực tiếp trong tệp người dùng đính kèm; cho phép
triển khai/test/backup-restore/áp main trong task này, không commit/push.
Baseline CHG-20261113-004, HR-LIST-013. Các thay đổi có sẵn được giữ nguyên.
Technical verification, visual/business acceptance và pilot là các kết luận riêng.

## Checklist trước triển khai

| Actor / môi trường | Thao tác và kết quả cần quan sát | Bằng chứng cần giữ |
| --- | --- | --- |
| HR, test18079 | Lưu Ngắn hạn/Dài hạn/Thuê khoán/để trống; danh sách, hồ sơ, phiên bản và Excel cùng nguồn; lịch sử/future không đổi current | ORM + browser + đọc XLSX |
| HR, test18079 | Ngày lao động dùng hr.version; metadata giấy tờ không nhân bản khi thêm phiên bản; thuê khoán có ngày riêng, không ghi ngày lao động | ORM/action/native form |
| HR/KH-KD, test18079 | HR đúng công ty đọc/ghi; KH-KD không HR bị từ chối RPC/export/file; lương giữ nhóm manager; attachment không public/token | ORM + HTTP |
| HR, test18079 | Ngày kết thúc trước bắt đầu bị từ chối; chuyển giấy tờ sang nhân viên/công ty khác bị từ chối | ORM |
| HR/admin, test18079 | Chưa có hợp đồng hiện hướng dẫn và nút đúng quyền; upload không tự xác nhận ký/hiệu lực/lương | Browser + ORM |
| HR, test18079 | Cột Mã → Tên → Chức vụ → Loại hình → Điện thoại → Login → Tình trạng; filter/paging10/20/50/100; xóa tìm kiếm vẫn group phòng ban | Playwright desktop/mobile |
| HR, test18079 | Hồ sơ thiếu có ghi chú, tiêu chí mã/phòng/(job và source title đều thiếu), nhãn từng dòng và nút bổ sung; sửa đủ rời danh sách; overview/drilldown/Excel thống nhất | ORM + browser + XLSX |
| HR/admin, test18079 | Phiên bản hồ sơ khác Lịch sử hoạt động; xem không tạo version; event mới rõ actor/time/reason, event cũ tóm tắt có kiểm soát và body gốc giữ | ORM + browser |
| HR, test18079 | Bỏ menu báo cáo trùng, giữ Tổng quan/chart/Xuất Excel nhân sự; có filter/time/scope và literal strings | Browser + đọc XLSX |
| Admin, test18079 | Hồ sơ giấy tờ mới chặn xóa có bảo vệ, preview nêu dependency; HR-DELETE-010/password/account/role không đổi | Odoo regression |
| HR, test18079 | 1440/1280/390/320, bàn phím/focus/reduced-motion, không lỗi console/page; KH-KD không đổi renderer | Playwright + ảnh trước/sau |
| Operator, main18069 | Backup DB+filestore; restore trên test chuẩn đã backup, neutralize; migrate/test; backup main cuối; độc quyền noHTTP upgrade; đối chiếu business/auth/blob; smoke chỉ đọc/mở/Hủy | Ops logs + fingerprints |

## Thiết kế dữ liệu đã triển khai

- `hr.version.tp_employment_kind`, kế thừa qua `hr.employee.version_id`: phân
  loại quản trị ba giá trị, False là chưa khai báo; không đổi employee_type_id.
- Metadata giấy tờ trên model HR riêng, employee/company có restrict; các
  phiên bản liên kết cùng hồ sơ giấy tờ. Ngày hợp đồng lao động chỉ dùng native
  contract_date_start/end/fixed_term. Ngày thuê khoán chỉ thuộc giấy tờ thuê khoán.
- Không payroll, bảo hiểm, chấm công, ký/duyệt điện tử hoặc giao khoán dự án.

## Kết quả

**IMPLEMENTED_VERIFIED_MAIN_APPLIED — CHG-20261113-005.** HR20.0.1.11.0
trên18079 và18069. Technical verification đạt; visual/business acceptance và
pilot chưa được người dùng xác nhận. Không stage/commit/push.

### Field/model, lịch sử và UI

- Phân loại nằm trên `hr.version`, employee related qua `version_id`; ba giá
  trị và trống có tracking/quyền HR + employee write. Không backfill nhân viên.
  Ngày lao động/fixed_term dùng native. `tp.hr.contract.document` chỉ giữ metadata,
  tệp và ngày thuê khoán; các phiên bản cùng kỳ dùng chung giấy tờ.
- Native tạo bản copy trước khi áp các giá trị mới. Link giấy tờ `copy=False`,
  action `create_version` chủ động kế thừa link sau khi đã có ngày phù hợp;
  bản trước kỳ đầu/sang kỳ khác không nhận nhầm giấy tờ. Giữ current khi xem
  past/future. Hộp thêm link nguyên tử đúng phiên bản/employee, không dùng
  One2many default khiến core `default_get` lỗi dictionary size.
- Hồ sơ có sáu tab. Contract summary, nhãn current/past/future, ngày đã khai báo,
  metadata/form file, phụ lục, xem giấy tờ và phiên bản dùng native. Không có
  state đã ký/hiệu lực, duyệt, lương, bảo hiểm, chấm công hoặc ký điện tử.
- Chức vụ → Loại hình → Số điện thoại; group phòng ban cố định013, clear search,
  paging10/20/50/100, optional columns và account actions giữ. Badge loại hình
  xanh dương/tím/vàng/xám khác account. Mobile cho badge tài khoản xuống dòng
  để tên không bị ép thành từng chữ ở320px; giữ shell sáng hiện hành.
- Tiêu chí thiếu dùng cùng helper: code OR department OR (job và source title
  đều trống). Có ghi chú không tạo bản sao, nhãn lý do từng dòng, nút mở edit,
  empty tích cực chỉ về ba tiêu chí. Fixture sau chuyển phòng+kèm chức vụ qua
  workflow cũ rời danh sách. Main còn1hồ sơ thiếu nền; không tự sửa hồ sơ thật.
- Lịch sử khó đọc do event identity cũ ghi trực tiếp JSON/hash vào body và
  header/tracking HR có nhãn tiếng Anh/None. Renderer chỉ nhận envelope hệ
  thống HR đúng keys/employee, escape tóm tắt; body gốc và ghi chú người dùng
  giữ. Event mới ghi lời nghiệp vụ + audit riêng; không rewrite hàng loạt.
  Có hiệu lực từ / Trạng thái tài khoản / Chưa thiết lập; Được mời giữ nguyên.
  Smart button Phiên bản hồ sơ, tab Lịch sử hoạt động. Chưa có bằng chứng đây
  là server fault từ ảnh; lỗi default_get tái hiện độc lập đã được sửa.
- `menu_reports` inactive, giữ XML ID/action. Tổng quan vẫn có chart/table và
  **Xuất Excel nhân sự**; filter loại hình + metadata thời điểm/phạm vi. Không
  đổi giao diện KH-KD, API/React/core hoặc account/password/role/mã/chuyển phòng.

### Kiểm thực chạy

Evidence private tại `.local/hr-emp014/`, giữ kín fixture/session/credential.

| Kiểm | Kết quả / bằng chứng |
| --- | --- |
| Odoo cuối | **86/86**,0failed0errors, `odoo-final-all-corrected2.log`: `/tp_organization,/tp_hr_workspace`, upgrade2addon trên canonical test sau restore. Gồm9 test hợp đồng: bốn phân loại, version source/shared paper/past trước kỳ đầu, ngày, ACL/company/salary/file, delete dependency, atomic dialog/forged link, employee default-context write guard, missing/XLSX, history originals |
| HOOT | HR38 + KD2 = **40tests/190assertions** sau correction; Home30 + KD1 = **31/179**. Log `.local/hr-auth-focus009/hoot-tp_hr_workspace.txt`, `hoot-tp_web_home.txt`;0pageerror |
| Browser test | `acceptance-test.json`: **11nhóm/0console-pageerrors**: list/group/clear/paging,6tab/cancel/version, history/old body/invited, classification save, native add/cancel/save, missing note/reasons, overview/filter/XLSX/menu, HR/KD file/RPC/export,1280/390/320 keyboard/reduced motion |
| Browser mở rộng | `extra.cjs` quan sát native search filter + fixed grouping, future/current navigation, upload+delete preview dependency; fixture hoàn tất qua transfer/job workflow. `extra-missing-test.json` và `extra-empty-test.json` PASS sau reload; `past-test.json` PASS sau correction: xem2025/giữcurrent2026+paper, không tự tạo version khi xem |
| Browser main cuối | `acceptance-main.json`: **6nhóm/0errors** trên source cuối: list/group/clear/paging,6tab/read/edit/Hủy/version,overview/filter/export/menu,1280/390/320 focus/reduced motion. Không save nghiệp vụ/nguy hiểm trên main |
| XLSX đọc lại | `xlsx-test.json`, `xlsx-main.json`:10cột, literal string data, autofilter/freeze, metadata time/scope/filter, server total/cache SUM khớp. Test unknown42/missing1; main unknown40/missing1. Không lương/password/hash/technical columns, chỉ công thức SUM do server tạo. Unit dùng tên bắt đầu `=` xác minh chống formula input |
| Tĩnh | Ruff HR PASS, XML13 PASS, JS syntax kiểm các file đổi PASS, `git diff --check` PASS. Không dùng React legacy tests thay native |

Các lượt fail giữ riêng: import helper/Odoo20 BinaryBytes, fixture guard,
selector/timing/equality harness; core default_get, version copy link trước áp
ngày đã sửa có regression. Lượt59test chỉ HR không được gọi là full2addon;
lượt cuối86 mới là kết quả đầy đủ. Odoo vẫn có warning GC WinError5/markdown2
Windows đã gặp trước task; không gọi warning-free. Phiên browser thỉnh thoảng
hết hạn sau thao tác nhiều vai trò; rerun bằng phiên mới đạt, không thay session
policy trong task này. Không tính các lượt fail là pass.

### Restore, main và bảo toàn

1. Backup test trước; mainA `backup-tp_tanphat_dev-20261113T064107775807Z` →
   canonical test, exact **600tables/666blobrefs/432sequences**, neutralize rồi
   upgrade/test. `.local/hr001/restore-evidence.json` verified+neutralized.
   Không database thứ ba và không restore test lên main.
2. **BackupB rollback trước lần nâng cấp014 đầu tiên:**
   `.local/hr001/backup-tp_tanphat_dev-20261113T073121361307Z`600tables/666refs.
   Source trước task: zip/hash63file; source cuối67file,17modified+4new so trước
   task (`source-scope.json`), không đụng source các task cũ.
3. Stop đúng config, xử lý venv child còn pool, zero sessions/noHTTP upgrade.
   Gate trước upgrade đầu chặn orphan đúng. Sau upgrade, probe đọc của chính
   lượt kiểm chồng với post-gate nên dừng; đã reapply độc quyền. Backup073223
   chứa schema014, **không** dùng thayB cho rollback toàn task. Correction cuối
   có backupC `backup-tp_tanphat_dev-20261113T074320617876Z`601tables/666refs và
   upgrade log `upgrade-main-corrected.log`. Không bỏ gate khi fail.
4. Reconcile từ **archiveB**, mọi cột cũ của600bảng: **577 rowsets giữ nguyên**
   sau smoke; delta23bảng gồm schema/view/action/ACL/module/cron/signaling và
   login/device/bus/presence/assets. Existing history body/tracking/audit giữ;
   chỉ thêm2notification tạo ACL. Reconcile dùng `ONLY` để tránh tính bảng kế
   thừa ir_actions hai lần, không lấy snapshot đã có schema mới làm baseline.
5. `metadata-main-smoke.json`:953ACL cũ giữ policy, thêm đúng2ACL,3write_date
   metadata thay;57groups,28users (gồm hash password),73partners và632nonasset
   rows+blob/hash giữ. Employee/version/dept/job/mapping/role/assignment/grant,
   công ty/nhóm và dữ liệu nghiệp vụ cũ nguyên. Main **40employee/28user/
   9active/15department**,0EMP014fixture,0paper,classification/link NULL toàn bộ.
6. Cả2runtime đang chạy. Main chỉ đọc/mở/Hủy/export. `archive-main-smoke.json`,
   `metadata-main-smoke.json` và source seal là bằng chứng; không tuyên bố toàn
   DB bất biến vì metadata vận hành/assets có thay đổi.

### Ảnh đã mở tự đánh giá

- Cặp main cùng admin/route/dataset40/1440×900:
  `.local/hr-emp014/before-main.png` → `after-main-list-1440.png`.
- `drilldown-test.json` và `drilldown-main.json` PASS: nút export tải file, menu Tổng quan giữ active sau export; missing drilldown có ghi chú và menu Danh sách nhân viên active.
- Main `after-main-contract-1440.png`, `after-main-contract-390.png`,
  `after-main-contract-320.png`, `after-main-overview.png` và list1280/390/320.
- Test `after-test-history.png`, `document-test.png`, `missing-empty-test.png`,
  `missing-complete-test.png`, `filter-test.png`, `versions-test.png`,
  `past-test.png`. Ảnh test có fixture45người; không coi cùng dataset với ảnh
  test-before40người. Một ảnh testcontract ban đầu chụp trong fade giữ riêng;
  ảnh cuối main dùng animation-disabled/chờ pane ổn định.

### Giới hạn và next action

Chưa test điện thoại vật lý, chưa audit độc lập (subagent lỗi model kế thừa),
chưa nghiệm thu visual/business/pilot. Không có payroll/insurance/attendance/
signing/payment hoặc chuẩn hóa hợp đồng thật. Không tự phân loại/sửa hồ sơ
người thật. Main còn1hồ sơ thiếu nền; HR rà soát theo quyền sau khi người dùng
duyệt. Đọc [guide](HR_EMP_014_USER_GUIDE.md),
[schema/quyền](../security/HR_EMP_014_SCHEMA_AND_ACCESS.md) và
[rollback](../../ops/runbooks/HR_EMP_014_DEPLOY_AND_ROLLBACK.md).
Next: người dùng tải lại18069, kiểm Danh sách → Hợp đồng/Lịch sử và Tổng quan;
ghi phản hồi giao diện/nghiệp vụ riêng. Ngoài task trở lại vai điều phối.
