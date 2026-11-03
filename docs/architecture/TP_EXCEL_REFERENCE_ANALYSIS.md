# Phân tích chọn lọc bộ Excel ERP tham khảo

**Mã tham chiếu:** `REF-ERP-EXCEL-20261029`  
**Ngày đọc:** 29/10/2026  
**Nguồn:** thư mục ERP trên NAS do người dùng cung cấp; đường dẫn đầy đủ giữ trong manifest ngoài Git.  
**Phạm vi:** đọc cấu trúc và ý nghĩa nghiệp vụ để thiết kế TANPHAT ONE; không phải nghiệm thu dữ liệu hay phê duyệt quy trình kế toán.

## 1. Cách đọc và ranh giới

Các file `.xlsx`/`.xlsm` được đọc ở chế độ chỉ đọc bằng `openpyxl`; file `.xls` được đọc cấu trúc/cached values bằng `xlrd`. Không chạy VBA, không refresh external links, không recalculation và không import vào Odoo. Không lưu số tiền, tên tài khoản, tên cá nhân, nội dung giao dịch thô hoặc credential vào repository. Manifest và hash đầy đủ nằm ngoài Git tại `.local/excel_reference_review/manifest.json`. Các nhận định bên dưới là `Observed` hoặc `Proposed`, theo [sổ nghiên cứu](TP_REFERENCE_RESEARCH_AND_HANDOFF.md); không tự trở thành `User-confirmed` hay runtime evidence.

Snapshot kiểm kê đầu có 8 workbook nghiệp vụ, 2 workbook tài khoản/danh sách dùng thử và 1 file khóa. Lần quét lại cuối lượt chỉ còn 10 workbook; file khóa tạm thời không còn. Ba đường dẫn dưới được loại khỏi nội dung đọc:

- `ERPcons (Lâm Phạm)\Danh sách sử dụng thử phần mềm ERP Lâm Phạm.xlsx`
- `ERPcons (Lâm Phạm)\Thông tin tài khoản dùng thử ERP_Tấn Phát.xlsx`
- `ERPcons (Lâm Phạm)\~$Thông tin tài khoản dùng thử ERP_Tấn Phát.xlsx`

## 2. Inventory

| Mã | File | Kết quả chọn lọc |
|---|---|---|
| XL01 | `251231 Quỹ tiền mặt tấn phát.xlsx` | Sổ quỹ tiền mặt, sao kê ngân hàng, dự án/thầu phụ và số dư lũy kế |
| XL02 | `260416 Dư nợ vay BIDV-MB-Bắc Á.xlsx` | Hạn mức, khoản vay, đáo hạn, lãi, trả nợ và phân bổ theo dự án/thầu phụ |
| XL03 | `260420.BCTC thu chi Tấn Phát.xlsx` | Kế hoạch tiền dự kiến thu và dự kiến chi; không phải sổ kế toán đã ghi sổ |
| XL04 | `Master_Quan_tri_chung_v10_5.xlsm` | Master tổng hợp, đối chiếu hai phòng, import/snapshot, từ điển và dashboard |
| XL05 | `Ban KD\Mẫu PKH - Quản trị dự án v10_5.xlsm` | Mẫu kế hoạch dự án, hạng mục, thầu phụ và nhật ký giao dịch |
| XL06 | `Ban KD\DA Temp.xlsm` | Biến thể mẫu PKH, có thêm các sổ/khoán nội bộ theo phòng |
| XL07 | `P.Ke toan\Cong trinh do dang vao hoan thanh.xlsx` | Sản lượng, nghiệm thu, thanh toán/tạm ứng theo kỳ và chuyển năm |
| XL08 | `P.Ke toan\Theo dõi dự án.xls` | Mẫu lịch sử công nợ, VAT, doanh thu–giá vốn, thuế, CCDC, khấu hao, lãi vay, tồn kho |

Chỉ mục dưới giúp lần sau xác định đúng phiên bản và vị trí bằng chứng; không dùng tên file làm căn cứ duy nhất. Mã Sxx là thứ tự sheet trong manifest, dùng khi nhãn sheet chứa tên đối tác/cá nhân. Không phải mọi ô trong một vùng đều có dữ liệu hoặc đều được xác nhận; locator chỉ dẫn tới cấu trúc đã đọc.

| Mã | SHA-256 đầu 12 ký tự | Sheet/range hoặc cấu trúc đã đọc |
| --- | --- | --- |
| XL01 | `31b2f905c94f` | `T12 !A3:G142` (sổ quỹ), `BIDV!A1:I62`, `MB!A4:J36`, `Vietin!A3:H17` (bảng sao kê); có sheet ẩn/working copy |
| XL02 | `5b0d912dde58` | `MB!A1:N84`, `BACA!A2:M41`, `BIDV!A2:T144`; tổng 14 sheet, 10 ẩn; vùng S03/S14 có lỗi công thức/cache |
| XL03 | `a3baaf8dbc4d` | `Thu!A1:F21`, header `A10:F10`; `Chi!A1:E113`, header `A9:E9`; dự kiến thu/chi |
| XL04 | `381afeded558` | `HDSD!A1:F34`, `TU_DIEN!A1:E111`, `LOG_Import!A1:F504`, `08_DoiChieu_2Phong!A1:L510`, `07_GiaTriKhoan_PhongBan!A1:J54` |
| XL05 | `e34052d2986f` | `HDSD!A1:G420`, `TU_DIEN!A1:E112`, `DATA!A1:N48`, `NHAT_KY_TC!A1:R504`, `NHAT_KY!A1:S504`; 11 sheet |
| XL06 | `b09872dd439f` | Cùng nhóm sheet cấu trúc PKH; `NHAT_KY_TC!A1:R504`, `NHAT_KY!A1:S504`; có sheet bổ sung theo phòng |
| XL07 | `c84bac04eab0` | `dở dang bidv.sl!A4:X76`, `11 tháng.2025!A4:K62`, `1 tháng cuối 2025 !A4:N70` |
| XL08 | `79b711af772e` | `Du co 331-2011!A4:X14`, `BC DT-GV!A5:H8`, `dư có 131!A6:Z38`, `KH TSCD  !A5:P37`, `BC lai Vay!A5:O23`, `BC NXT!A6:L24`; cached structure only |

Giới hạn kỹ thuật: thống kê cấu trúc OOXML giới hạn tối đa 10.000 dòng và 180 cột mỗi sheet; các bảng nghiệp vụ đã nhận diện nằm trong phạm vi này. Các dimension rất lớn như XFB hoặc dòng 1.048.576 chưa được kiểm từng ô. Không gọi đây là kiểm toán từng ô, kiểm chứng phép tính hay kiểm đầy đủ macro.

### Cảnh báo phiên bản PKH

Hash hiện tại của XL05 là `e34052d2986f…`. [Registry BIZ-001](TP_KD_EVIDENCE_AND_ACCEPTANCE.md) trước đây dùng S03 có hash `4ee0ff275058…`; bản sao/manifest cũ ở `.local/biz-001/`. Chênh hash chứng minh file thay đổi, chưa chứng minh quy tắc nghiệp vụ thay đổi. Chỉ bằng chứng/mapping phụ thuộc trực tiếp S03 cần gắn `legacy snapshot; current copy pending re-baseline`, đặc biệt E05–E11 và E17. Trước khi tái sử dụng như biểu mẫu hiện hành phải re-hash, đối chiếu sheet/range/ý nghĩa công thức và có người nghiệp vụ xác nhận. Không đổi hash registry lịch sử để che chênh lệch.

S01/S02/S04/S05 là nguồn riêng; các DEC đã được người dùng xác nhận giữ nguyên phạm vi. Quan sát XL01/XL03 và các workbook khác không bị mất giá trị chỉ vì XL05 đổi hash; các ca mô phỏng cũng không tự thành sai hoặc thành UAT thất bại. Lượt này chưa thực hiện diff toàn bộ snapshot cũ–mới.

## 3. Kiến thức nên tiếp thu

### 3.1 TP Projects, Contracts và Tasks

Các mẫu PKH/Master cho thấy một dự án có kế hoạch riêng, hạng mục, chủ đầu tư, thầu phụ và nhật ký theo thời gian. Nên giữ quan hệ rõ giữa `project`, `contract`, `contract line`, `assignment/work item` và `subcontractor`. Dùng mã/ID ổn định; không dùng tên hiển thị hoặc một ô Excel làm khóa.

Các cột được tách thành hợp đồng gốc, hợp đồng cập nhật, sản lượng thực hiện, nghiệm thu, phải xuất hóa đơn, đã thanh toán, giữ lại và còn phải thanh toán. Đây là căn cứ quan trọng để không gộp các mốc sau thành một số “đã thực hiện”.

Hướng dẫn và cấu trúc `NHAT_KY_TC`/`NHAT_KY` mô tả mẫu append-only: sửa hoặc hủy bằng dòng mới, giữ dòng gốc, có mã giao dịch gốc và trạng thái hiệu lực. Chưa chạy macro để kiểm cơ chế này được thực thi thế nào. TANPHAT nên chuyển ý tưởng thành revision/event/audit có actor, thời điểm, lý do, version và provenance; việc chốt/void phải tuân thủ policy đã được xác nhận.

Riêng nhãn “GT phải xuất hóa đơn” có lịch sử lệch giữa tên cột và hướng dẫn diễn giải trong E07 của BIZ-001. Không map thành nghĩa vụ xuất hóa đơn hoặc số đã xuất chỉ từ nhãn; phải đối chiếu `TU_DIEN`/hướng dẫn của đúng phiên bản và xác nhận với Kế toán. “Tỷ suất lợi nhuận” quản trị theo các cột nghiệm thu cũng không tự là lợi nhuận kế toán đầy đủ.

Thầu phụ cấp 1 và thầu phụ cấp 2 phải có quan hệ cha–con và quy tắc tổng hợp riêng. Không cộng thầu phụ của phòng lần nữa vào tổng công ty. Đây là quy tắc cần kiểm bằng constraint và cảnh báo, không chỉ bằng công thức dashboard.

### 3.2 TP Finance: actual, forecast và obligation phải tách

XL01 cho thấy sổ tiền mặt và sao kê ngân hàng là quan sát dòng tiền; chúng không tự là `account.move` đã ghi sổ hoặc đã đối chiếu. Khi có import trong tương lai, cần giữ `source_observation`, dòng sao kê, batch, row hash, mapping, bằng chứng và trạng thái reconcile. Chuyển tiền giữa các tài khoản của công ty, khoản vay gốc, phí/lãi, tạm ứng, lương và thanh toán dự án phải được phân loại riêng.

XL03 cho thấy “dự kiến thu” và “dự kiến chi” là kế hoạch. Vì vậy phải tách `forecast_snapshot/forecast_line` khỏi `payment_request`, `account.move`, payment và cash event. Forecast không được biến thành tiền đã thu/đã chi chỉ vì ngày dự kiến đã qua.

XL02 bổ sung mô hình cần thiết cho hạn mức tín dụng: `facility`/lender, drawdown, maturity, principal, interest, repayment và allocation. Phân bổ khoản vay tới project/contract/subcontractor có thể nhiều–nhiều, cần amount/currency/basis, phần còn lại và phép đối chiếu. Tài sản bảo đảm/bảo lãnh chỉ được ghi như bằng chứng có kiểu và trạng thái; workbook chưa đủ căn cứ cho giá trị pháp lý, giải chấp, lãi suất cơ sở, tiền tệ hoặc quyền phê duyệt.

Qua các header/vùng XL07/XL08 ở chỉ mục trên, đề xuất thiết kế giữ riêng `business_date` (ngày nghiệp vụ), `as_of` (chốt số liệu đến ngày nào) và `known_at` (khi nào hệ thống biết số liệu). Đây là thiết kế TANPHAT đề xuất, không phải ba field đã tồn tại sẵn trong workbook. Sản lượng thực hiện không đồng nghĩa nghiệm thu; nghiệm thu không đồng nghĩa hóa đơn; hóa đơn không đồng nghĩa tiền thu. Báo cáo hết năm cần snapshot, không ghi đè lịch sử. Các cầu nối doanh thu–giá vốn, VAT, công nợ, khấu hao, lãi vay và nhập–xuất–tồn phải có policy kế toán và chứng từ riêng. XL08 có nhãn kỳ 2011/2013/2023/2025; không xem các mẫu đó là chính sách hiện hành.

### 3.3 Chất lượng và giới hạn nguồn

- XL02 có 2 external-link parts. Vùng S03 có cached errors và S14 có nhiều cached errors/công thức `#REF!`; các cột ngày trộn datetime/text/blank. Đây là lỗi ở vùng đã đọc, chưa chứng minh mọi tổng đều sai; cần cách ly và đối chiếu từng số trước khi dùng cho báo cáo.
- XL01 có sheet ẩn/bản note và range định dạng lớn. Không tự cộng working copy thành nguồn tiền thứ hai, không coi ô trống là bằng không hoặc đã được phân bổ.
- XL03 mang tên “BCTC” nhưng bố cục đọc được là dự kiến thu–chi quản trị; chưa có căn cứ gọi là báo cáo tài chính theo chuẩn kế toán hoặc đã kiểm toán.
- XL04–XL06 có VBA; chưa phân tích hoặc chạy VBA nên không xác nhận tính bất biến, crawl hàng đêm hay cơ chế bảo vệ dữ liệu là runtime hoạt động.
- XL08 chưa lấy được công thức BIFF gốc; VBA/external links của định dạng này chưa audit. Chỉ các header/cấu trúc cached đã đọc được dùng làm tham khảo.
- Chưa đối chiếu số liệu giữa 8 file, chưa xác nhận tính đầy đủ, trùng lặp, người duyệt, kỳ khóa sổ, chính sách thuế hoặc chứng từ hợp pháp.

### 3.4 Import, đối chiếu và dashboard

Master có `LOG_Import`, từ điển nghiệp vụ, tổng hợp và đối chiếu Phòng Kế hoạch–Kế toán. TANPHAT có thể tiếp thu các lớp sau:

1. vùng tiếp nhận/staging bất biến, giữ nguồn, sheet/range, hash, batch và thời điểm;
2. kiểm tra schema, dòng không map đưa vào quarantine;
3. mapping master data bằng ID chuẩn, không dùng text tự do;
4. đối chiếu hai nguồn với trạng thái khớp/lệch/thiếu và người xử lý;
5. dashboard chỉ đọc số liệu đã có provenance và trạng thái chất lượng;
6. từ điển giải thích ý nghĩa trường, null/zero/unknown và đơn vị tính.

Các công thức Excel chỉ là bằng chứng về cách người dùng đang tổng hợp. Khi chuyển sang Odoo, rule phải được viết thành model/service/test và có owner xác nhận.

## 4. Phân loại áp dụng cho TANPHAT ONE

| Nhóm | Áp dụng | Cách làm |
|---|---|---|
| Adopt | revision/event append-only; tách production–acceptance–invoice–cash; project/subcontractor scope; import log; snapshot/as-of; reconcile; dictionary | Đưa vào đặc tả model, API, security và test sau khi owner nghiệp vụ xác nhận |
| Adapt | ledger tiền mặt/ngân hàng; forecast thu–chi; loan allocation; dashboard cảnh báo; cấp 1/cấp 2 | Thiết kế lại theo Odoo, company/project scope, currency/Decimal, chứng từ và grant; không bê công thức Excel nguyên xi |
| Reference only | VAT, doanh thu–giá vốn, thuế, CCDC, khấu hao, nhập–xuất–tồn, collateral/legal semantics | Chỉ dùng để đặt câu hỏi và lập mapping với Kế toán/QT-TC; chưa đủ căn cứ mở runtime |
| Reject for runtime | macro/external link không kiểm chứng, hidden working copy, cached formula coi là chứng từ chuẩn, công thức hardcode hoặc suy quyền từ chức danh | Không dùng làm database runtime hoặc tự chuyển thành accounting posting; giữ bản gốc/hash/cache làm bằng chứng có kiểm soát ngoài Git khi cần. Không đưa tên cá nhân/tài khoản/số tiền thật vào Git hoặc seed |

## 5. Tác động tới phạm vi hiện hành

- **TP Projects/Contracts:** bổ sung yêu cầu snapshot, revision, line/assignment, parent–child subcontractor và provenance; không mở thêm state hợp đồng chỉ vì Excel có thêm cột.
- **TP Finance:** chuẩn bị đặc tả actual/forecast/obligation, bank/cash observation, loan facility và reconciliation; chưa mở Finance posting hoặc payment thật.
- **TP Dashboard:** chỉ hiển thị số liệu có nguồn, kỳ, trạng thái và phạm vi quyền; cảnh báo lệch là danh sách độc lập, không che lẫn nhau.
- **Import:** làm sau khi có owner, mapping ID, cutover và tiêu chí đối chiếu; không import trực tiếp workbook thật.
- **Data Lake:** không phát sinh quyết định mở lake/connector. DP-001 vẫn có recommendation `DEFER`, chưa phải DEC; Odoo tiếp tục là nguồn sự thật. Nhu cầu import/snapshot không tự chứng minh cần Data Lake.

## 6. Các gap cần xác nhận trước khi code Finance/Import

1. Phiên bản XL05 nào là chuẩn hiện hành và ai ký xác nhận?
2. Ai sở hữu mapping project/contract/subcontractor và xử lý dòng không map?
3. Quy tắc ghi nhận production, acceptance, invoice, cash, retention, VAT, doanh thu và giá vốn là gì?
4. Facility/loan ID, currency, rate basis, repayment, collateral và allocation có chứng từ nào?
5. Kỳ khóa sổ, `as_of`, `known_at`, correction/void và quy trình đối chiếu ai chịu trách nhiệm?
6. Grant nào được xem số tiền, hồ sơ tài chính và export; ai cấp/thu hồi?

Chỉ khi các câu hỏi thuộc phạm vi slice đã có owner, evidence và decision mới chuyển thành model/API/test. Các file này giúp TANPHAT thiết kế đúng ranh giới dữ liệu; chúng không thay quy chế công ty, chính sách kế toán, phê duyệt BASE hoặc quyết định Data Lake.

## 7. Vị trí trong lộ trình

Đây là nguồn đầu vào thiết kế tương lai, không thay [Next task hiện hành](../PROJECT_STATUS.md) hoặc [master plan](TP_CODE_EXECUTION_MASTER_PLAN.md). Trước mắt vẫn audit AUTH-002 slice 2. Khi người dùng chọn chuẩn bị slice Finance/Import/Reporting, bắt đầu bằng từ điển chỉ tiêu, mapping nguồn–model và tình huống đối chiếu bằng dữ liệu giả; không triển khai đồng thời mọi miền xuất hiện trong Excel.

