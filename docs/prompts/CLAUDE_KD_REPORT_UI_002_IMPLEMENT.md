# Prompt tiếp theo — KD-REPORT-UI-002 triển khai trên test

**Tài liệu chuẩn bị, chưa phải lệnh đã giao thực thi.** Chỉ dùng khi người dùng
chấp nhận/chỉnh thiết kế và trực tiếp giao prompt này. Mặc định S0–S4 test-only;
áp dev18069 là S5 cần lệnh riêng. Không commit/push.

Làm việc trong `C:\TANPHAT ONE`. Task `KD-REPORT-UI-002-IMPLEMENT`, lane F
giao diện/báo cáo test, chọn CHG-ID mới chưa dùng. Đọc AGENTS.md, status,
workflow, naming, decisions, roadmap, handoff, skill tanphat-odoo-delivery,
AI_COORDINATION_WORKFLOW và master plan. Đọc:

- [Kế hoạch đã chuẩn bị](../ui/KD_REPORT_UI_002_REDESIGN_PLAN.md), mục2 G01–G09,
  mục6 ma trận6report, mục7 workbook và mục9 A01–A17.
- `docs/prompts/CLAUDE_KD_REPORT_UI_002_PLAN.md` để giữ nguyên ranh giới/nghĩa số.
- `docs/demo/KD_REPORT_001_ACCEPTANCE.md`, `KD_REPORT_001_USER_GUIDE.md`,
  `KD_PROJECT_RESTRUCTURE_001_USER_GUIDE.md` và acceptance restructure mới nhất.
- Model/controller/caller `custom_addons/tp_kd_workspace/models/report_center.py`,
  `controllers/report_export.py`, `static/src/report_center/report_center.js`,
  `.xml`, `.scss`, tests backend và HOOT hiện có; lần theo MoneyAccumulator,
  grant/assignment, record rules, personal certificate, source actions/prefs.
- `.local/kd-report-ui002/preview.html`, hai mẫu R01/R05 và ảnh baseline nếu
  còn trên máy. Nếu mất artifact local, dùng đặc tả tracked làm căn cứ; không
  nói đã xem artifact không tồn tại. Không lấy fixture preview làm business data.

## 1. Kết quả và phạm vi

Theo phương án được người dùng chọn (đề xuất A), làm đủ6report dễ đọc, full-name
chooser, applied scope rõ,3–4KPI chính, chart đúng nghĩa, cột tổng hợp/chi tiết
riêng, filter/search/group/sort/page10/20/50/100, nguồn có quyền, export UX và
workbook3sheet có màu/typed/filter/freeze. Giữ native OWL/QWeb/SCSS và session
Odoo. Không thêm React/Ant Design/report framework/job engine.

Chỉ sửa trong `tp_kd_workspace` các file report trên, test tương ứng, manifest
assets/version khi cần và runner test theo convention repository. Backend chỉ
thêm DTO đo lường/label/aggregate từ tập được phép, sửa presentation parity
G01/G02/G04/G09 đã tái hiện và builder workbook hiện hữu. API/OpenAPI chỉ khi
contract API thực sự thay, không mở rộng REST vì native UI.

Ngoài phạm vi: `odoo/`, `addons/`, React legacy, workflow/formula/state gốc,
ngưỡng cảnh báo3/30ngày, thuế/currency rounding, real grants/users/passwords,
mapping/investor/package/attempt, mở policy export mới, hai landing Quản lý/
Quản trị/Tổng quan, config/login/CSRF/transport rewrite hoặc database dev18069.
Không apply clone changes lên dev khi mới xong test.

## 2. S0 bắt buộc trước sửa

Kiểm git status/diff, checkpoint/handoff, runtime/module version. Baseline
plan CHG016 quan sát dev20.0.1.8.0, code đã có nhiều diff của batch trước;
không reset/clean/stage file không liên quan. Không setup/upgrade/restart dev
để mở phiên. Dùng private workspace/clone DB/data-dir/port riêng theo runner
đã có và quyền của yêu cầu triển khai; seed chỉ fixture giả trên clone.

Nếu checkpoint thuộc công việc khác, giữ và báo delta; không `finish` thay.
Khi đủ baseline chạy `ai_workflow.py start`, ghi scope/acceptance vào commentary.

Tạo regression đỏ trước các correction:

1. Search còn k<Nrows nhưng KPI/chart/count/exclusion không đổi theo k; sau sửa
   mọi chỉ tiêu phải được tạo từ cùng tập đã lọc, **không đổi công thức**.
2. R01 contract_type_label/R06 owner_label và tất cả sortable header đối chiếu
   whitelist thật; sort đúng raw key hoặc bỏ tín hiệu sort không hỗ trợ.
3. Pending khi đổi report không âm thầm chuyển thành applied; test hai nhánh xuất.
4. Metadata XLSX `can_view_money` thiếu key: sửa nhãn trung thực từ capability/
   masked data hiện có, không giả toàn quyền hoặc nới scope.
5. Nhãn ngày R03 phải nói đúng `date` của model hiện tại, không dùng field tên
   acceptance_date/request_date không có; không đổi điều kiện kỳ.

Nếu repro phủ nhận nhận định source, ghi kết quả và bỏ correction không cần.
Không âm thầm sửa nghiệp vụ để khiến fixture/biểu đồ đẹp hơn.

## 3. Thiết kế cần giữ

Mục4–6plan là spec. Nội dung14–16px/KPI26–32px, navy/blue/teal/amber/red/gray
có label/icon, đủ contrast, khoảng thở, không cắt tên report, chỉ một sidebar
hiện hữu. Cách tính/nguồn ở disclosure; cảnh báo ảnh hưởng tổng vẫn hiện ngắn.
Money label tiếng Việt, numeric gốc do Odoo; JS không tự tính tổng tiền.

R01 giữ gốc/phụ lục mới nhất/hiệu lực là3góc nhìn độc lập (gốc100→phụ lục110,
hiệu lực110, không210). R02 vẫn CRM grain cho tới khi có mapping được giao;
`submitted` là khai báo nộp chưa xác minh, không thắng thầu. R03 năm chỉ tiêu
trong bốn chặng, thu/chi riêng, không suy cash, không time-series giả. R04
cha70/con65tách, không135, internal/subcontract không đồng nghĩa level1/2.
R05 mine/scope riêng, count định danh, trạng thái có thể giao nhau, SLA nguồn.
R06 certificate/person/org/obligation riêng, còn hạn không xác thực pháp lý,
usage liên kết không nhân count. Không thêm KPI khi source chưa hỗ trợ.

Report/filter/search/group/sort/page/source Back phải coherent. Ngày sai có
message, pending/applied rõ; drawer/modal keyboard/focus/Escape,200%zoom,
mobile/table-only scroll, reduced-motion. Stale response không phục hồi tiền
đã bị thu hồi; successful rescope cũng thay dữ liệu cũ, không chỉ AccessError.

## 4. Export và quyền

Dùng `_build_xlsx_download`/`_compute_full_report`/sanitizer/guards hiện có cho
cả RPC và HTTP; không pipeline song song hoặc sudo. Dialog nêu current report,
applied kỳ/phạm vi/search/group/sort/cột/timestamp,3sheet và toàn bộ kết quả
lọc. Pending có “Áp dụng và xuất”/“Xuất theo bộ lọc đang áp dụng”; chống double
click, đúng file khi đổi report, lỗi/retry, không % giả/success giả.

Workbook đúng `Tong_quan`, `Tong_hop_nhom`, `Chi_tiet`: navy title/blue header,
metric cột riêng, tiền/currency/basis riêng, typed number/date/text ID0001,
date dd/mm/yyyy, auto-filter/freeze/print/repeat header, no merges trong vùng
lọc, số0khác unknown/forbidden/not-applicable. Hạn Excel15digit ghi rõ và giữ
exact text thay vì im lặng làm tròn. Sanitize mọi text; số âm vẫn number;
không external links/hidden money/cache/formula leak.

Hiện report dùng assignment+financial_read, không có financial_export riêng.
**Giữ policy hiện hành**, ghi giới hạn; nếu yêu cầu mới cần tách capability,
dừng riêng phần phụ thuộc và xin quyết định policy, không tự thêm/quy grant.
Download luôn check quyền hiện tại cả RPC/HTTP, mixedAfinancial/Bmetadata/
Cinaccessible, credential cá nhân. Không đổi route GET/POST/CSRF trong UI batch.

Đo in-memory/base64 trên clone fixture500/5.000rows: thời gian/bytes/peak RSS
đo được, không bịa số; chỉ cân nhắc HTTPbinary sau có nhu cầu đo được. Không queue.

## 5. Kiểm chứng và bàn giao

Thực hiện acceptance A01–A16plan trên clone: test backend report/security,
HOOT state/filter/export, XML/assets/JS/lint theo phần đổi; browser6report,
5fixture personas (Trưởng/Phó/Chủ trì/Kế hoạch/Hỗ trợ) với matrix grants thật
trong clone, cross-scope và revoke giữa xem→refresh/drill/RPCexport/HTTPexport.
Không suy quyền từ tên vai trò. Test>100rows/download toàn bộ/IDset/totals,
web–file parity cùng filter, money traps, null/0/negative/multi-bucket/date
biên, injection, empty/error/no-money/race, Back, mobile/zoom/keyboard/motion.

Đọc lại XLSX bằng openpyxl/ZIP, render từng sheet và ghi giới hạn Excel thật.
Lưu ảnh trước-sau cùng viewport/role/filter/dataset, log test thực; không dùng
PASS lịch sử CHG009/014 làm test mới. Request token/files/auth/secret ngoài Git.
Không chạy ứng dụng toàn bộ khi chỉ sửa docs, nhưng code security/model phải
có Odoo tests liên quan; quan sát ảnh không thay permission/backend audit.

Cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP và workflow/spec bị ảnh hưởng.
`git diff --check`, `ai_workflow finish --change-id <ID_mới> --check <kết_quả_thật>`
rồi `check`. Đầu ra: source diff scoped, source seal, logs/ảnh/file download,
matrix acceptance pass/fail/skip, limitations, rollback/apply plan chưa chạy.
Đề nghị review độc lập trước technical acceptance; visual/business/pilot giữ
riêng. Không commit/push. Nếu muốn áp18069: người dùng phải giao S5 riêng,
fresh backup+restore verified trước apply và preservation sau, không suy
quyền apply từ việc người dùng đã chọn thiết kế.
