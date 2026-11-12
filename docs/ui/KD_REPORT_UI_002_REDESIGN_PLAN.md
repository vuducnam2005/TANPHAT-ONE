# KD-REPORT-UI-002 — Thiết kế lại sáu báo cáo KH-KD

Ngày 09/11/2026, Asia/Saigon. Batch `CHG-20261109-016`.
Trạng thái: `DESIGN_PREVIEW_READY_PENDING_USER_REVIEW`.
Phạm vi: kế hoạch, preview độc lập và hai workbook giả lập. **Chưa triển khai ứng dụng.**

## 1. Kết quả đề xuất và ranh giới

Chọn **A — Không gian phân tích**: tên báo cáo đầy đủ, kỳ/phạm vi đang áp dụng và nút Xuất Excel ở đầu; một bộ chọn báo cáo; bộ lọc gọn; 3–4 KPI; biểu đồ đúng câu hỏi; bảng tổng hợp/chi tiết có cột đo lường riêng. B — Bảng đối chiếu là phương án so sánh cho người thường xuyên đọc nhiều dòng. Cả hai có trong preview để người dùng chuyển đổi.

- Giữ native Odoo, OWL/QWeb/SCSS, session, model/action và quyền backend. Dùng lại `tp.kd.report.center`, `MoneyAccumulator`, parser/filter/builder và hai đường xuất hiện có; không xây report engine/React/queue mới.
- Không đổi công thức, trạng thái, ngưỡng cảnh báo, assignment/grant, owner hoặc mapping doanh nghiệp. Không sửa application code, database nghiệp vụ, cấu hình, restart/upgrade dev18069; không commit/push.
- Hai khu vực Quản lý dự án/Quản trị dự án và màn Tổng quan giữ mục đích riêng. Báo cáo phục vụ đọc theo kỳ, đối chiếu và xuất file.
- Nguồn căn cứ: [prompt được giao](../prompts/CLAUDE_KD_REPORT_UI_002_PLAN.md), [thiết kế cũ](KD_REPORT_001_DESIGN.md), [acceptance lịch sử](../demo/KD_REPORT_001_ACCEPTANCE.md), [hướng dẫn sau restructure](../demo/KD_PROJECT_RESTRUCTURE_001_USER_GUIDE.md), source hiện tại. Technical acceptance, người dùng duyệt hình thức, business acceptance và pilot authorization là bốn kết luận riêng.

## 2. Baseline và mức bằng chứng

`ai_workflow check` trước làm việc PASS CHG015; checkpoint mới được `start` trước tạo artifact. Git có nhiều thay đổi sẵn có của các batch trước, không reset/stage. `dev.py status` xác nhận Odoo/PostgreSQL đang nghe; truy vấn SELECT trong transaction read-only xác nhận `tp_kd_workspace=20.0.1.8.0`, `tp_contract=20.0.1.2.0`. Listener Odoo18069 PID10096, PostgreSQL55432 PID13900; không restart.

Khảo sát mới bằng Playwright: một tài khoản fixture có sẵn, alias trong `baseline/observations.json`; cùng session/quyền, `Tất cả kỳ`, không lọc dự án/người; desktop1440×1000 và mobile390×844; lần lượt R01–R06. Đã chụp màn đầu và vùng bảng, 0 `pageerror`. Đăng nhập chỉ tạo session/log kỹ thuật của Odoo; không gửi action ghi nghiệp vụ, thay tài khoản hoặc grant. Không tải Excel thật trong lượt này; nhận định workbook hiện tại dựa source. Không chạy lại Odoo/HOOT hoặc nhận test lịch sử là test mới.

| Báo cáo | Điều nhìn thấy ở runtime / vị trí ảnh | Hướng giải quyết |
| --- | --- | --- |
| R01 Dự án và hợp đồng | `baseline/R01-desktop.png`: 6 KPI rơi thành hàng5+1; số tiền dài cùng `excluding_tax`/`Original`/`_effective_revision` lấn giá trị. `R01-table.png`: cột tên/dự án hẹp, hàng xuống nhiều dòng | 4 KPI chính, tiền rút gọn có số chính xác; nhãn tiếng Việt; phân bổ chiều rộng tên và các cột tiền riêng |
| R02 Hồ sơ dự án và hồ sơ thầu | `R02-desktop.png`: 6 KPI, giải thích khai báo nộp/chưa xác minh dài; một thẻ tiền không khả dụng chiếm cùng trọng lượng. Source vẫn CRM | 4 KPI hồ sơ/chuẩn bị/khai báo nộp/quá hạn; thông báo legacy/mapping ngắn; không gọi số hồ sơ là số gói thầu |
| R03 Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán | `R03-desktop.png`: tên tab bị cắt; 5 số tiền + một thẻ thực thu/chi chưa có nguồn khiến bảng nằm dưới màn đầu. Mobile nút Excel mất chữ | Bốn vùng so sánh; đề nghị thu/chi tách hai dòng và hai cột; biểu đồ thanh nhóm cùng đơn vị; không tổng chéo |
| R04 Giao khoán và thầu phụ | `R04-desktop.png`: 5 KPI; tổng cấp1/cấp2 là đoạn text tiền dài; nhóm vẫn nhét chỉ tiêu trong một ô | 4 KPI và bảng riêng Trần cấp1/Phân bổ cấp2/Cảnh báo; chart cấu trúc/cảnh báo, không cộng cha-con |
| R05 Tình trạng xử lý và trách nhiệm hồ sơ | `R05-desktop.png`: 6 KPI, điều cần xử lý cạnh tổng hồ sơ; chart thiên về đếm nguồn. `R05-table.png`: hàng cao, tên/dự án khó quét nhanh | Ưu tiên quá hạn/sắp hạn/đang rà soát/việc của tôi; chart người phụ trách × nhóm hạn, bảng nguồn/hạn/trách nhiệm rõ |
| R06 Năng lực, chứng chỉ và nghĩa vụ hồ sơ | `R06-desktop.png`: 5 KPI, tab bị cắt; chứng chỉ và nghĩa vụ cùng vùng đếm; “còn hạn” cần giữ chú thích chưa xác minh | Tách chứng chỉ/nhân sự/tổ chức và nghĩa vụ; 4 KPI hết hạn/sắp hạn/thiếu/tổng chứng chỉ; không tô xanh vì chỉ còn hạn |

Ảnh nằm trong [baseline local](../../.local/kd-report-ui002/baseline/observations.json). `Rxx-mobile.png` có đủ sáu báo cáo; chữ tên đầy đủ trong h1 nhưng bộ chọn vẫn ellipsis; toolbar chỉ icon, khoảng trống lớn trước bộ chọn. DOM đo bảng13,5px, hai tab clipped ở desktop; source đặt KPI18px và phụ chú11,5–13px. Bảng tổng hợp hiện gom badge vào cột “Chỉ tiêu tổng hợp theo nhóm”. Đây là đánh giá UI, không phải audit hoàn chỉnh backend/quyền.

### Sai lệch tài liệu/source cần giữ rõ

| Mã | Bằng chứng source hiện tại | Xử lý trong chặng code sau |
| --- | --- | --- |
| G01 — Phạm vi search | `report_center.py:2608–2625`: search lọc rows/groups sau khi builder đã tính KPI/chart; chỉ tính lại tiền totals. Có nguy cơ bảng khác KPI/chart | Tái hiện trên test với tập N, search còn k<N; tính mọi trình bày từ cùng tập đã lọc, giữ nguyên công thức và phạm vi quyền |
| G02 — Header sort | R01 `contract_type_label` và R06 `owner_label` gắn sortable nhưng thiếu whitelist backend | Đối chiếu toàn bộ header; dùng đúng raw key được whitelist hoặc bỏ affordance sai; không sort tiền bằng chuỗi |
| G03 — Pending | `selectReport()` sao pending sang applied; export dùng applied nhưng không có hộp lựa chọn | Không âm thầm áp dụng khi chuyển báo cáo. Giữ pending theo report hoặc báo “Áp dụng / Bỏ thay đổi / Ở lại”; hộp xuất có hai lựa chọn rõ |
| G04 — Excel/quyền | `_build_xlsx_download:2907` đọc `can_view_money` không có trong full DTO; metadata có thể báo không quyền dù dòng tiền được phép | Tái hiện và sửa nhãn capability trung thực theo dữ liệu đã che; không mở quyền |
| G05 — Export policy | `_financial_project_ids:302–318` dùng assignment + `financial_read`; không có guard `financial_export` riêng trong report/controller | Giữ đúng policy đang chạy; không tuyên bố read=export là policy đã được công ty duyệt. Nếu muốn tách capability: đặc tả/quyết định riêng, chặn phần phụ thuộc, không thêm grant ngầm |
| G06 — Transport | OWL gọi RPC lấy base64→Blob; controller có GET/POST `auth=user, csrf=False`, no-store. Thiết kế cũ mô tả POST+CSRF và tên builder khác | Ghi đúng hiện trạng; chưa đổi route/CSRF/transport trong batch UI. Kiểm cả hai đường theo session/quyền; hardening nếu cần là phạm vi được duyệt riêng |
| G07 — Workbook | Một sheet Rxx_BaoCao; metadata/KPI/nhóm/chi tiết nối dọc; ngày text; không AutoFilter/freeze/print settings | Đổi trình bày builder hiện hữu thành ba sheet; không nhân đôi pipeline dữ liệu |
| G08 — R02 sau restructure | `_build_r02` đọc `crm.lead`; project→gói→lần tham gia đã có riêng. 14project/25CRM còn mapping chưa xác nhận theo handoff trước | Đặt nhãn hồ sơ CRM/Chưa liên kết; không suy gói/chủ đầu tư/kết quả. KPI gói/lần tham gia chỉ sau batch mapping/report riêng |
| G09 — Ngày/nhãn | R03 catalog ghi acceptance_date/request_date, thực tế builder dùng `rec.date`; R05 nhiều nguồn ngày khác nhau. Tìm kiếm thực tế lowercase9field, không có chuẩn hóa dấu như guide cũ | Nhãn ngày bám code thực tế; giải thích trong “Cách tính”; không âm thầm đổi kỳ hoặc mở search toàn cột |

Các gap G01–G06 mới là source review, **chưa tái hiện bằng regression/runtime export**. Không dùng chúng để mở lại finding F1–F3 của restructure đã được sửa và kiểm ở CHG014. [Audit source chi tiết](../../.local/kd-report-ui002/source_audit.md).

## 3. Hai phương án bố cục

| | A — Không gian phân tích (đề xuất) | B — Bảng đối chiếu |
| --- | --- | --- |
| Thứ tự | Tên/kỳ/Excel → chọn báo cáo → lọc → KPI → chart có ngữ cảnh → tổng hợp/chi tiết | Tên/kỳ/Excel → chọn báo cáo/lọc → bảng rộng → khối KPI và chart mở rộng phía dưới |
| Phù hợp | Lãnh đạo xem kỳ và nhân viên đối chiếu/xuất; dễ hiểu cảnh báo trước khi đọc dòng | Nhân viên đã quen báo cáo, ưu tiên nhiều dòng trên màn đầu |
| Đánh đổi | Tốn chiều cao cho 3–4 KPI và một chart; cho thu gọn chart | Khó thấy biến động/cảnh báo khi mới mở; cần chủ động mở phân tích |
| Mobile | Tiêu đề wrap, Excel có chữ, filter drawer, KPI2cột, chart/bảng một cột | Bảng cuộn ngang xuất hiện sớm; phân tích dưới accordion |

Chọn A vì sáu báo cáo phục vụ cả tổng hợp lẫn đối chiếu. Dùng chiều rộng cho bảng, hạn chế khối giải thích và không thêm sidebar thứ hai. B là wireframe so sánh, chưa đề xuất triển khai hai chế độ runtime cùng lúc.

```text
A desktop — trong shell Odoo, một sidebar hiện hữu
┌ Báo cáo KH-KD / Tên đầy đủ                          [Xuất Excel] ┐
│ Kỳ đã áp dụng · phạm vi · dữ liệu lúc...       [Nguồn] [Làm mới] │
│ [Chọn báo cáo: tên đầy đủ, danh sách wrap 2 cột khi mở]          │
│ [Kỳ] [Dự án] [Phụ trách] [Lọc thêm] [Áp dụng]                    │
│ Đang áp dụng... / Có thay đổi chưa áp dụng                      │
│ KPI1                KPI2                KPI3              KPI4 │
│ Biểu đồ trả lời câu hỏi                  Cảnh báo/nhóm nổi bật  │
│ [Tổng hợp nhóm] [Chi tiết]        [Nhóm theo] [Tìm] [Chọn cột]   │
│ Mã | Tên/dự án | Trạng thái | Chỉ tiêu A | B | Ngày | Mở nguồn   │
│ Tổng toàn kết quả theo đơn vị           [10/20/50/100] [← 1 →]  │
│ [Cách tính và nguồn ▾]                                         │
└───────────────────────────────────────────────────────────────┘
B desktop: cùng header/lọc; bảng đứng trước; [Phân tích ▾] chứa KPI/chart.

Mobile390px                     Drawer lọc / hộp xuất
┌ Tên đầy đủ, tự xuống dòng ┐    ┌ Bộ lọc                 [Đóng] ┐
│ Kỳ/phạm vi               │    │ Kỳ / từ-đến / dự án           │
│ [Xuất Excel] [Bộ lọc]    │    │ Phụ trách / trạng thái        │
│ [Chọn báo cáo ▾]        │    │ [Đặt lại] [Áp dụng]           │
│ KPI1          KPI2       │    ├ Xuất Rxx / kỳ đang áp dụng    ┤
│ KPI3          KPI4       │    │ Toàn bộ N kết quả / 3 sheet   │
│ Chart / cảnh báo         │    │ [Áp dụng và xuất]             │
│ Tổng hợp / Chi tiết     │    │ [Xuất theo bộ lọc áp dụng]     │
│ [Bảng cuộn ngang riêng]  │    └───────────────────────────────┘
│ Số dòng / trang / nguồn  │
└──────────────────────────┘
```

## 4. Token màu, chữ và quy tắc tương tác

Contrast theo WCAG sRGB; tỷ lệ dưới đây của chữ màu trên trắng, làm tròn2chữ số. Token nền nhạt không dùng làm chữ. Web/Excel dùng chung ý nghĩa, có nhãn/icon để đọc được khi in đen trắng.

| Token | Hex | Contrast/trắng | Vai trò |
| --- | --- | --- | --- |
| navy | `#17324D` | 13.13:1 | Shell, tiêu đề workbook |
| blue | `#155EEF` | 5.41:1 | Chọn/lọc, số liệu, nút Excel chữ trắng; không hàm ý đã duyệt |
| teal | `#087E70` | 4.97:1 | Kết quả đã xác nhận đúng state nguồn |
| amber | `#9A6700` | 4.87:1 | Chờ/chưa xác định/sắp hạn; nền `#FFF4D6` |
| red | `#B42318` | 6.57:1 | Quá hạn, lỗi, vượt; nền `#FEECEB` |
| gray | `#475467` | 7.69:1 | Chưa có nguồn/không áp dụng, văn bản phụ |
| canvas/line | `#F4F7FB` / `#D0D5DD` | Không dùng làm chữ | Nền sáng, đường chia cột/hàng |

Font dùng stack native `Segoe UI, Arial, sans-serif` có đủ dấu tiếng Việt. Nội dung15px/line-height1,5; bảng14–15px; header cột14px semibold; tiêu đề24px desktop/21–22px mobile; KPI30–32px/26px. Chú thích ít nhất13px, không hạ zoom để ép cột. Khoảng cách section24px, field12–16px; hàng bảng tối thiểu44px; touch target44px. Không có đoạn giải thích dài trong ô giá trị.

Tiền: số gọn `12,45 tỷ VND` chỉ khi một bucket; focus/tooltip và dòng chi tiết cho giá trị gốc chính xác. Nhiều tiền tệ/cơ sở thuế hiển thị “Xem2nhóm”, không quy đổi hoặc cộng tổng chung. Map selection thực tế sang “Hợp đồng gốc”, “Phụ lục”, “Chưa thuế”, “Giá trị hợp đồng hiệu lực”; giữ key kỹ thuật trong source/metadata kỹ thuật, không đưa vào nhãn người dùng. Không gọi `submitted` là trúng thầu; còn hạn chưa xác minh dùng màu trung tính/hổ phách.

Chuyển động chỉ phản hồi thao tác150–200ms; không animation trang trí khi dữ liệu đổi. Focus visible2px, Tab/Enter/Escape đầy đủ, modal/drawer giữ focus và trả focus đúng nút mở; `prefers-reduced-motion` tắt transition. ARIA status cho pending/loading/xuất xong, alert cho lỗi. Mobile cuộn ngang trong table container, không tràn toàn trang; sticky header/cột chỉ thêm sau kiểm giao nhau/200%.

## 5. Bộ lọc, bảng và nguồn

- Kỳ mặc định giữ hành vi hiện hữu, không tự chuyển Tất cả kỳ thành Tháng này. Preset Tất cả kỳ/Tháng/Quý/Năm/Tùy chọn; dòng tóm tắt luôn cho biết ngày đầu-cuối và trường ngày của report. Chưa có ngày không tự thuộc kỳ; số bị loại có thông báo.
- Hàng chính: kỳ, dự án, phụ trách, Áp dụng. Nâng cao: trạng thái/phân loại riêng report, ngày tùy chọn; chỉ hiện option backend trả về. R02/R05 có “Chưa gắn dự án” theo khả năng nguồn; không thêm R06 option mà parser chưa hỗ trợ.
- Pending khác applied bằng lời nhắc: “Đã đổi bộ lọc. Bảng và Excel vẫn dùng …”. Khi chuyển report không lén áp pending. Search/group/sort là một phần phạm vi kết quả và phải vào metadata xuất; thống nhất một định nghĩa với backend, không tự filter tiền ở JS.
- Chart click có nhãn “Lọc …”, cập nhật applied rõ và reset trang1; thông báo số kết quả. Chỉ chart có mapping filter hợp lệ mới click; còn lại là chart tĩnh có bảng dữ liệu tương đương. Drilldown gọi `open_kd_report_source`, backend kiểm lại quyền; không tự dựng URL bỏ guard.
- Một dòng bảng = một record theo grain báo cáo. Cột mã100–130px, tên260–320px, dự án180–220px, trạng thái140–180px, tiền160–190px, ngày120px. Số căn phải/tabular; tên căn trái/wrap có kiểm soát; ngày dd/mm/yyyy; zebra rất nhẹ, hover/focus rõ, header có đường phân cột. Tên đầy đủ xem trong nguồn/chi tiết hàng, không ép toàn tên thành cột50px.
- Tổng hợp nhóm dùng cột riêng; currency/basis thành cột hoặc nhóm độc lập. Chi tiết có chọn cột phụ (đối tác/reviewer/ghi chú), sort đúng whitelist, search có nhãn phạm vi9field hiện có, chọn10/20/50/100, phân trang server; tổng lấy toàn kết quả đã lọc, không lấy trang hiện tại.
- Quay lại từ nguồn giữ report/filter/group/sort/search/page/page-size/visible columns theo db+uid hiện có. Danh sách nguồn rộng hơn báo cáo phải ghi rõ và chuyển domain đúng khi backend hỗ trợ; không hứa list nguồn luôn khớp kỳ/search hiện nay.

## 6. Ma trận thiết kế sáu báo cáo

### R01 — Dự án và hợp đồng

- Câu hỏi: dự án nào có hợp đồng, bao nhiêu bản đang xử lý, giá trị hiệu lực đã xác nhận là bao nhiêu?
- KPI: Dự án trong phạm vi; Tổng hợp đồng; Hợp đồng đã ghi nhận hiệu lực; Giá trị hiệu lực theo bucket. Đang xử lý/gốc/phụ lục là chỉ tiêu mở rộng.
- Chart: thanh ngang số hợp đồng theo vòng đời (hồ sơ/hiệu lực/đóng), mẫu số là tổng hợp đồng đã lọc; không donut tiền lẫn gốc/phụ lục. Số tiền bằng0 vẫn là0, chưa có bản hiệu lực là “Chưa có hợp đồng hiệu lực xác nhận”.
- Tổng hợp theo dự án: Dự án | Số HĐ | Đang xử lý | Tiền tệ | Cơ sở thuế | HĐ gốc | Phụ lục mới nhất | HĐ hiệu lực. Ba cột giá trị là ba góc nhìn, **không có cột tổng cộng ba cột**.
- Chi tiết: Mã/tên HĐ, dự án, loại HĐ, phụ trách, vòng đời/review, ngày mốc; ba cột tiền riêng; optional đối tác/số phiên bản. Mở contract nguồn.
- Ngày: ngày hiệu lực của revision hiệu lực; fallback đúng builder (ngày hiệu lực/latest ký), as-of cuối kỳ hoặc hôm nay. Không đổi sang “phát sinh doanh thu”. Excel: tiêu đề/phạm vi/rule as-of; nhóm dự án×currency×basis, detail từng HĐ; mẫu R01 minh họa gốc100→phụ lục110→hiệu lực110.

### R02 — Hồ sơ dự án và hồ sơ thầu (ngữ cảnh Dự án và đấu thầu)

- Câu hỏi: hồ sơ tham gia ở bước nào, ai phụ trách, hồ sơ nào quá hạn/chưa liên kết gói?
- KPI hiện có: Tổng hồ sơ CRM; Đang chuẩn bị; Đã khai báo nộp—chưa xác minh; Quá hạn chưa nộp. Không đổi count CRM thành count project/package/attempt. Giá trị dự kiến để mở rộng theo quyền.
- Chart: thanh ngang các bước đã nhận diện/chuẩn bị/khai báo nộp; không dùng funnel chuyển đổi/tỷ lệ thắng khi chưa có sự kiện/phân mẫu theo cohort.
- Tổng hợp: Phụ trách hoặc trạng thái | Số hồ sơ | Chuẩn bị | Khai báo nộp | Quá hạn | Chưa gắn dự án. Cột chưa mapping gói chỉ bổ sung khi builder có dữ liệu thật; không suy từ tên.
- Chi tiết: Mã, hồ sơ, dự án, gói đã liên kết nếu có, **phụ trách trước hạn**, trạng thái, hạn nộp; optional đối tác, hình thức, chứng chỉ, giá dự kiến. Ngày hiện có `kd_deadline`, không phải ngày nộp thực tế. Drill CRM; nếu hiển thị gói phải qua action đã bảo vệ riêng.
- Excel giữ grain hồ sơ CRM, nhãn legacy/Chưa liên kết. R02 nâng cấp project→package→attempt là backlog riêng cần mapping và test unique; không gộp vào UI polish.

### R03 — Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán

- Câu hỏi: năm số liệu ở bốn chặng đang ở mức nào, có hồ sơ chưa xác nhận nào bị loại?
- Bốn vùng KPI: Kế hoạch; Sản lượng; Nghiệm thu; Đề nghị thanh toán (hai dòng Đề nghị thu/Đề nghị chi). Thực thu/chi ghi “Chưa có chứng từ kế toán” trong ghi chú, không điền0.
- Chart: thanh đặt cạnh nhau theo dự án và cùng currency/basis;5series (kế hoạch, sản lượng, nghiệm thu, đề nghị thu, đề nghị chi), legend và đơn vị rõ. Không stacked sum, không đường thời gian thiếu nguồn kỳ; nhiều bucket chọn một bucket cụ thể.
- Tổng hợp: Dự án | Tiền tệ | Cơ sở thuế | Kế hoạch | Sản lượng | Nghiệm thu | Đề nghị thu | Đề nghị chi | Chưa xác nhận. Chi tiết thêm nguồn/mã/hồ sơ/kỳ hoặc ngày/trạng thái/phụ trách, các ô không cùng chặng là “Không áp dụng”.
- Ngày: kế hoạch/sản lượng lấy kỳ giao nhau `period_from..period_to`; nghiệm thu/đề nghị dùng `date` thực tế. **Không phân bổ theo tỷ lệ ngày giao kỳ** nếu builder chưa làm; giải thích “hồ sơ giao kỳ được tính theo quy tắc nguồn”. Không cộng năm series hay thu-trừ-chi thành tiền thực. Drill từng model nguồn, Excel cùng grain và cột.

### R04 — Giao khoán và thầu phụ

- KPI: Tổng hồ sơ; Giá trị khoán cấp1; Phân bổ cấp2 (đối chiếu); Hồ sơ cảnh báo vượt. Số nội bộ/thầu phụ hiển thị bên chart.
- Chart: số hồ sơ nội bộ/thầu phụ theo cấp; hoặc thanh cha với con để đối chiếu cùng bucket, không stacked cấp1+cấp2. Không bổ sung tỷ lệ trên HĐ hiệu lực vì source hiện chưa có mẫu số bảo đảm.
- Tổng hợp: Dự án | Số cấp1 | Số cấp2 | Tiền tệ/cơ sở thuế | Trần cấp1 | Phân bổ cấp2 | Số cảnh báo. Chi tiết: Mã/tên, bên nhận/vai trò, cấp, hồ sơ cha, phụ trách, hạn, trạng thái, tiền cấp1/2 và cảnh báo.
- Ngày `date_due`; overrun giữ warning nguồn, không phát minh ngưỡng80/90%. Khi tiền cha/con không đủ xác nhận/cùng basis: “Chưa đủ dữ liệu đối chiếu”, không xanh0vượt. Drill allocation. Excel tách cấp/grain; tổng công ty chỉ cấp1.

### R05 — Tình trạng xử lý và trách nhiệm hồ sơ

- KPI: Quá hạn; Đến hạn≤3ngày; Đang chờ rà soát; Việc của tôi cần xử lý. Tổng số hồ sơ định danh hiện cạnh tên bảng; bốn KPI có thể giao nhau, **không cộng lại**.
- Chart: stacked bar theo người phụ trách, phân nhóm hạn loại trừ nhau (Quá hạn / Đến hạn≤3ngày / Trong hạn / Chưa đặt hạn), chỉ trên hồ sơ còn mở. Tổng trạng thái rà soát trình bày bảng riêng, không trộn vào denominator hạn. Nếu builder chưa trả owner×SLA, bổ sung aggregate từ rows đã kiểm quyền, không tạo SLA mới.
- Tổng hợp: Phụ trách | Tổng hồ sơ | Đang rà soát | Bị trả | Quá hạn | Sắp hạn | Chưa hạn; nhóm theo nguồn vẫn có. Chi tiết: Mã, nguồn, hồ sơ/dự án, phụ trách, người rà soát, trạng thái nguồn, hạn, mức hạn, trách nhiệm và Mở hồ sơ.
- Ngày theo nguồn: contract revision effective/create; CRM deadline; task deadline; các nguồn còn lại date_due. Không gọi mọi ngày là ngày đến hạn pháp lý. “Việc của tôi” theo builder hiện tại khác tất cả hồ sơ user có quyền.
- Excel không tiền; ba sheet có as-of09/11/2026 giả lập, rule3ngày; đếm duy nhất theo model+ID; cùng hồ sơ vừa review vừa quá hạn chỉ tính một trong tổng. Mẫu thứ hai dành R05.

### R06 — Năng lực, chứng chỉ và nghĩa vụ hồ sơ

- KPI: Tổng chứng chỉ định danh; Chứng chỉ hết hạn; Sắp hết hạn≤30ngày; Nghĩa vụ còn thiếu. Tổng nghĩa vụ là số phụ; chứng chỉ tổ chức/cá nhân và checklist không chung denominator.
- Chart: hai panel thanh trạng thái hạn chứng chỉ / tình trạng nghĩa vụ. Hết hạn `<hôm nay`, sắp hạn `hôm nay..hôm nay+30`, chưa hạn riêng; còn hạn chưa xác minh giữ nhãn. Ngưỡng30ngày là cảnh báo minh họa hiện có, không xác nhận pháp lý.
- Tổng hợp: Nhóm hồ sơ | Chủ thể | Số chứng chỉ | Hết hạn | Sắp hạn | Số nghĩa vụ | Còn thiếu (không áp dụng là —). Chi tiết: Mã/tên, loại/chủ thể, dự án, phụ trách, tình trạng rà soát/hồ sơ, ngày hết hạn/hạn nghĩa vụ, số hồ sơ sử dụng; gắn nhiều lead không nhân số chứng chỉ.
- Ngày `valid_to` / `date_due`; personal certificate theo rule owner/reviewer/scope đã có; không lộ tên cá nhân/usage ngoài quyền qua chart/Excel. Không có tiền trong report này. Drill credential/obligation; workbook tương lai cùng hai grain có cột loại rõ.

## 7. Luồng Xuất Excel và thiết kế workbook

Nút **Xuất Excel** màu blue, icon tải kèm chữ, vị trí đầu desktop và cạnh bộ lọc mobile. Mở dialog read-only cấu hình trước tải:

1. Tên đầy đủ/mã báo cáo đang chọn, kỳ ngày thực tế, dự án/phụ trách/trạng thái/search/group/sort; scope cột mặc định **đầy đủ cột report được phép xuất**, không phụ thuộc cột ẩn trên web. Chưa triển khai tùy chọn xuất cột đang nhìn để tránh hiểu nhầm.
2. “Toàn bộ kết quả đã lọc”, số dòng chỉ khi tính được bằng quyền hiện tại; không hứa count cũ là count lúc tải. Một report/lần; không tự xuất cả6.
3. Ba sheet `Tong_quan`, `Tong_hop_nhom`, `Chi_tiet`; tên file `TANPHAT_KD_Rxx_<ky>_<pham-vi-an-toan>_<thoi-diem>.xlsx`. Chuẩn hóa kí tự filesystem; không đưa tên nhạy cảm ngoài quyền vào filename.
4. Pending: cho **Áp dụng và xuất** (đợi backend trả applied hợp lệ rồi xuất) hoặc **Xuất theo bộ lọc đang áp dụng**; Hiển thị rõ hai phạm vi. Ngày sai chặn nhánh áp dụng; đóng dialog không đổi dữ liệu.
5. Đang xuất: nút khóa chống lặp, spinner + “Đang tạo file”; không % giả. Xong: tên file/số dòng nếu server trả; trình duyệt đã bắt đầu tải không đồng nghĩa người dùng đã lưu file. Lỗi: thông báo cụ thể + Thử lại; mất quyền/session xóa số liệu nhạy cảm và không giữ preview tiền cũ. Đổi report/filter giữa request phải bỏ kết quả cũ, không gán file sai tên.

Workbook:

| Sheet | Nội dung / quy tắc định dạng |
| --- | --- |
| Tong_quan | Tiêu đề navy, tên/kỳ/phạm vi, người xuất/thời điểm tính,3–4KPI và số phụ, unit/basis/exclusion/nguồn/cách tính; label số là count hoặc amount riêng. Ghi “Tính lúc xuất”, không hứa snapshot bất biến |
| Tong_hop_nhom | Một nhóm/bucket một dòng; mỗi metric một cột typed, header xanh, dòng tổng tách currency/basis; AutoFilter/freeze đúng hàng; không tổng khác ý nghĩa |
| Chi_tiet | Toàn bộ kết quả lọc, một record/grain; numeric money/count, date thật format dd/mm/yyyy, mã0001text; cột đơn vị/thuế/trạng thái giá trị riêng; AutoFilter/freeze, không merge trong vùng sort/filter |

Nền trắng/zebra nhạt; title16–18pt, body11–12pt; trạng thái dùng cùng palette và chữ/icon; hàng tổng navy/blue nhạt; column widths theo loại, wrap tên/header, row height đủ, landscape/fit1page ngang nhưng chiều dọc tự do; print title repeat header. Không thu font để ép bảng rất rộng vào A4; chọn giấy phù hợp/A3 hoặc chia bảng khi cần.

Numeric chỉ khi đã xác nhận và có quyền; `0` giữ0; chưa biết/không áp dụng/không quyền là nhãn riêng, không ép0. Không giấu tiền trong hidden sheet/column/chart/cache/formula/metadata. Thực tế Excel giữ khoảng15chữ số có nghĩa: nếu giá trị vượt giới hạn, cột numeric để trống có nhãn “Vượt độ chính xác Excel”, cột giá trị gốc text đã sanitize và rule loại khỏi SUM; không lặng lẽ làm tròn. Không đổi currency precision/công thức Odoo trong UI. `MoneyAccumulator` hiện có float: kế hoạch không tuyên bố arbitrary precision, cần kiểm biên so với currency rounding trước code export.

Text qua `_sanitize_excel_text`, tắt auto-formula/URL, giữ số âm thật kiểu number; không external links/macro. Download recheck quyền hiện tại cả RPC/HTTP, không `sudo` hoặc dùng cache của người khác; phân biệt count metadata không tiền với financial scope. Chưa tách financial_export thì mô tả đúng G05, không tự cấp capability.

### Hai mẫu giả lập

- [Mẫu R01](../../.local/kd-report-ui002/R01_MAU_GIA_LAP_2026-11.xlsx): hợp đồng gốc/phụ lục/hiệu lực độc lập, bucket tiền và tình trạng giá trị rõ.
- [Mẫu R05](../../.local/kd-report-ui002/R05_MAU_GIA_LAP_2026-11.xlsx): trách nhiệm/trạng thái/hạn, không có dữ liệu doanh nghiệp thật.

Cả hai có đúng3sheet, provenance “MẪU GIẢ LẬP”, không nối DB. Mẫu thể hiện thiết kế workbook, không phải file tải từ dev. Kiểm cấu trúc/kiểu ô/tổng/filter/freeze/style và render từng sheet được ghi trong `excel_verification.json`, `excel_render_verification.json` và `EXCEL_SAMPLE_NOTES.md`. Renderer có thể hiển thị mã0001thành1; XLSX gốc giữ string0001đã kiểm riêng. Chưa kiểm tương tác trong Excel desktop/in giấy. Preview HTML dùng tập giả khác mẫu Excel; chỉ được gọi là web–file parity khi chặng code chạy cùng fixture/filter thật.

### Giới hạn in-memory và kế hoạch đo

Source hiện dựng tất cả rows + BytesIO + XLSX + base64 JSON + Blob, base64 tăng khoảng33% dung lượng wire trước overhead. Lượt plan không benchmark export dev. Chặng test đo fixture500/5.000rows: số dòng, bytes XLSX/base64, elapsed server/download, peak RSS và UI lock; mỗi report một lượt warm sau baseline, có kết quả thay vì phần trăm giả. Ngân sách đề xuất để thảo luận:5.000rows hoàn tất<10s ở máy test, peak delta<150MB, không làm request đọc nhỏ bị treo. Đây là mục tiêu thiết kế, chưa là SLA đã đạt. Nếu đo vượt ngân sách mới cân nhắc HTTP binary đang có để tránh base64; giữ lại guard/metadata/contract. Chưa có lý do dựng queue/job engine.

## 8. Lộ trình triển khai và phạm vi file

| Chặng | Đầu ra quan sát được | File / phụ thuộc / rủi ro | Tiêu chí xong |
| --- | --- | --- | --- |
| S0 Baseline + tái hiện gap | Fixture cô lập, ảnh6report, test đỏ G01–G04, bảng chính sách export hiện hành | `tests/test_report_center.py`, `static/tests/report_center.test.js`; đọc model/controller/prefs/drill callers; clone/data-dir/port riêng | Repro số web/file/search/sort/pending; phân biệt source gap với policy mới; không sửa dev |
| S1 Shell/filter | Full-name chooser, header/Excel, filter chính/nâng cao, pending/applied, mobile | `report_center.js/.xml/.scss`; tái sử dụng prefs/session key/service; không sidebar mới | Keyboard/200%/mobile; chuyển report không ngầm áp pending; response cũ bị bỏ |
| S2 Sáu report/chart/table | KPI đúng trọng tâm, nhãn Việt, cột nhóm typed riêng, chart semantics theo mục6 | Cùng3file + `models/report_center.py` chỉ DTO/aggregation trên tập lọc, label/correctness G01/G02/G09. Không đổi model nguồn/state/quyền | Sáu report mỗi report ít nhất1case bình thường/rỗng/thiếu/multi-bucket; công thức gốc/phụ lục/chặng/cha-con/distinct giữ |
| S3 Workbook/export UX | Dialog phạm vi,3sheet typed/style/freeze/filter, phản hồi tải; sửa G04 metadata | Builder `_build_xlsx_download`, RPC caller, controller kiểm tương thích; dùng parser/guard cũ; xlsxwriter sẵn có | File tải thật toàn kết quả; metadata/counts/totals web–file khớp fixture và quyền; không external/hidden leak |
| S4 Test và review độc lập | Odoo/HOOT/browser/XLSX evidence,5vai trò, revoke, mobile, đo export | Mở rộng test hiện có và runner riêng theo convention repo; không chạy test suite ghi trên dev | Acceptance dưới đây đạt có log/ảnh cùng role/filter; reviewer độc lập; visual/business/pilot còn riêng |
| S5 Áp dev khi được giao riêng | Fresh backup+restore kiểm chứng, apply seal đã test, preservation,5login chỉ đọc | Runbook hiện có, manifest chỉ tăng version khi có code; không apply bằng prompt test-only | Người dùng giao áp18069; backup/restore DB+filestore+source/version; before-after rows/grants/accounts/files; rollback sẵn |

Không sửa `odoo/`, `addons/`, React legacy/API/OpenAPI hoặc hai landing management/governance. API/OpenAPI chỉ cập nhật nếu contract API thực sự thay. R02 package KPI/mapping, capability export mới, CSRF hardening và precision overhaul là backlog riêng có gate; không chèn ngầm S2/S3.

## 9. Acceptance trước code

Các mục dưới là **chưa chạy trên ứng dụng mới**, dùng để giao triển khai; bản preview chỉ chứng minh trình bày/tương tác giả lập.

| Mã | Actor / thao tác / điều kiện | Kết quả và bằng chứng cần có |
| --- | --- | --- |
| A01 | Cả5vai trò mở R01–R06 desktop1440×1000/mobile390×844 | Tên đầy đủ không ellipsis; chữ14–16px, KPI26–32px; Excel có chữ; ảnh từng report cùng fixture/filter trước-sau |
| A02 | Đổi kỳ/dự án/phụ trách chưa Apply, đổi report, mở xuất | Applied/bảng/file không đổi âm thầm; hai nhánh xuất cho phạm vi đúng; ngày sai hiện lỗi; test HOOT+browser |
| A03 | Tập>100rows; search còn7rows, group/sort/page-size10/20/50/100, trang cuối | KPI/chart/groups/totals/detail/file cùng7rows, total không theo trang; header sortable tất cả thật sự sort; server whitelist; kiểm read+download |
| A04 | R01 gốc100→phụ lục110, correction, draft, hai currency/basis | Hiệu lực110 theo as-of/guard nguồn; không210; không cộng chéo tiền tệ/thuế; web/file exact + currency rounding |
| A05 | R03 4chặng, thu và chi, kỳ giao nhau, thiếu ngày |5cột riêng; không cộng chặng hay suy cash; quy tắc kỳ/ngày giữ; Excel date numeric; dữ liệu thiếu không0 |
| A06 | R04 cha70, con30+35, sau đó fixture vượt hợp lệ theo guard; thiếu tiền | Tổng cấp1=70, cấp2=65riêng, không135; cảnh báo theo nguồn; chưa biết không thành “không vượt” |
| A07 | R05 một hồ sơ review+quá hạn; R06 một credential gắn nhiều leads | Tổng định danh một lần; mine khác scope; hạn3/30ngày đúng biên; person/org/obligation đúng quyền, chưa xác minh không gọi hợp lệ |
| A08 | Trưởng/Phó/Chủ trì/Kế hoạch/Hỗ trợ với mixed grants và assignment | Actor có quyền tiền dự ánA, metadataB: chỉ tổng tiềnA, không leakB qua chart/tooltips/JSON/Excel/cache/filename; Hỗ trợ không tiền, no hidden cells/formulas/cache |
| A09 | Thu hồi grant/assignment hoặc session giữa xem→export, cross-project ID, cross-company | Request kế tiếp recheck; xóa số cũ, file không trả tiền đã mất quyền; trực tiếp RPC+HTTP, source/form/file access được kiểm lại; không dùng menu hiding làm bảo mật |
| A10 | Xuất khi đang trang2/10, search/group/cột ẩn; dataset thay trước tải | File đầy đủ kết quả hiện được phép,3sheet đúng; metadata kỳ/phạm vi/timestamp/cột; không hứa snapshot/count cũ; so độc lập model source và row IDs |
| A11 | Workbook hai reports tiền/trạng thái | Date thật, numeric đúng precision, mã0001text,0/unknown/forbidden/negative khác; AutoFilter/freeze/no merged data; style/header/print; check openpyxl+render từng sheet+Excel người dùng |
| A12 | Text =,+,-,@,tab,CR; số âm thật; Unicode/filename; vượt15digit | Text không thành formula/link; số âm numeric; giá trị lớn chính xác theo rule; không macro/external/hidden money; quét ZIP/XML saved file |
| A13 | Empty/loading/server error/no-money/retry/doubleclick | Có hướng dẫn; không chart bịa/tiền cũ; không duplicate export; success chỉ file đúng report; aria-live/alert đúng |
| A14 | Keyboard Tab/Enter/Escape, focus, zoom200%, reduced-motion | Không mất thao tác/focus; drawer/modal không focus lọt ra; bảng scroll riêng; không toàn trang overflow; chart có bảng tương đương; Chromium giả lập ghi rõ chưa thiết bị thật |
| A15 | Mở nguồn từ từng grain, quay Back | Đúng model/ID/quyền; giữ applied/group/search/page/size/columns; list nguồn nếu chưa filter tương đương phải báo rõ |
| A16 | Test500/5.000rows, compare Tổng quan và hai khu vực dự án | Ghi timing/bytes/RSS thật, không engine mới khi chưa đo; regression separation/menu/native permission; ảnh và log không chứa secrets |
| A17 | Nếu giao áp18069 sau review | Snapshot/restore verified, exact tested source seal, preservation dữ liệu/account/grant/attachment/module version; rollback rehearsal; không coi backup local là production readiness |

## 10. Bàn giao, kiểm chứng và bước tiếp

- [Preview tương tác A/B và6report](../../.local/kd-report-ui002/preview.html) — file tĩnh local; có nhãn dữ liệu giả lập. Ảnh `preview-shots/Rxx-desktop.png`, `Rxx-mobile.png`, `variant-B-desktop.png`, `export-dialog.png` hỗ trợ xem khi HTML không mở được trong app.
- Có thể mở [preview trên máy này](http://127.0.0.1:18762/preview.html) khi server file tĩnh local còn chạy; [ảnh desktop/mobile](../../.local/kd-report-ui002/desktop-mobile-preview.png) luôn xem được từ file. Preview không nối Odoo/DB. KPI/chart là fixture thiết kế cố định; tìm/lọc/nhóm/sort/phân trang chỉ mô phỏng cục bộ, chưa tính lại toàn bộ chỉ tiêu. Date-range picker, chọn cột, cập nhật dữ liệu và thu hồi quyền thật là acceptance triển khai tương lai, không nhận đã có từ HTML.
- [Prompt code tiếp theo](../prompts/CLAUDE_KD_REPORT_UI_002_IMPLEMENT.md) chỉ thực thi sau khi người dùng giao, mặc định test/clone riêng. Chưa cho phép áp18069.
- Các phép kiểm thực chạy và giới hạn cuối lượt: xem status/changelog CHG016 và `.local/kd-report-ui002/verification.json`. Hash ứng dụng trước-sau phải giống nhau; kiểm link/artifact/diff/workflow; không lấy `finish/check` thay nghiệm thu nghiệp vụ.
- Bước tiếp: người dùng xem A/B và hai workbook, chọn/chỉnh hình thức; sau đó giao prompt S0–S4. G08 mapping và G05 policy export tiếp tục là cổng riêng, không chặn những phần UI tái sử dụng đã đủ căn cứ.

Kiểm thực chạy của batch thiết kế: 18 ảnh baseline cùng session/phạm vi; 63 kiểm tra Playwright preview đạt, 0 lỗi JavaScript; hai XLSX × ba sheet được đọc lại/render; kiểm 405 file ứng dụng/tooling trước–sau không đổi; links/artifacts và `git diff --check` đạt. Chưa kiểm ứng dụng mới, export thật dev, Odoo/HOOT mới, Excel desktop hoặc thiết bị thật. `git diff --check` có warning CRLF của các file đã thay đổi sẵn từ trước, không có lỗi whitespace. Preview HTTP localhost18762 là process riêng, dev18069 và PostgreSQL giữ PID trước–sau.
