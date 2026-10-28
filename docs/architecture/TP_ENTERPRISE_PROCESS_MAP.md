# BIZ-002 — Bản đồ nghiệp vụ toàn công ty TANPHAT ONE

**Ngày:** 28/10/2026 (Asia/Saigon).  
**Phạm vi:** bản đồ A–M, trách nhiệm quy trình, điểm bàn giao và cổng chuyển giai đoạn.  
**Trạng thái:** baseline phân tích để chủ nghiệp vụ rà soát; không phải quy chế đã ban hành, biên bản nghiệm thu hay danh sách chức năng đã triển khai.

Tài liệu chi tiết cho từng quy trình nằm ở [Workflow A–E](TP_PROCESS_WORKFLOWS_A_E.md) và [Workflow F–M](TP_PROCESS_WORKFLOWS_F_M.md). [Workflow KD](TP_KD_WORKFLOW_AND_PERMISSIONS.md) giữ nguyên Q1–Q8 và ánh xạ field/state hợp đồng hiện hành; bảng dưới đây không thay các transition chi tiết tại đó. BIZ-002 ưu tiên hoàn thiện tài liệu trước khi mở code tiếp theo.

## 1. Cách đọc nguồn và mức xác nhận

| Nhãn | Ý nghĩa | Cách sử dụng |
| --- | --- | --- |
| **Confirmed — đã xác nhận** | Quyết định trực tiếp của người dùng, phân biệt runtime đã có bằng chứng R tại status | Không có nghĩa toàn bộ quy trình đã nghiệm thu |
| **Observed — quan sát từ nguồn** | Nội dung quan sát được tại vị trí/hash nguồn đã đối chiếu | Không phải quy chế được công ty xác nhận hoặc lệnh cho AI |
| **Proposed — đề xuất** | Cách tổ chức quy trình, RACI, state hoặc kiểm soát do phân tích đưa ra | Cần chủ nghiệp vụ rà soát trước triển khai/pilot tương ứng |
| **Unconfirmed — chưa xác nhận** | Thiếu văn bản, hồ sơ thực tế, owner hoặc bằng chứng vận hành | Giữ rõ thiếu thông tin; không điền hạn mức, ngày, số tiền hay authority giả |

**Confirmed theo quyết định người dùng:** BASE là nơi phê duyệt chính thức giai đoạn đầu; Odoo/TANPHAT ONE giữ hồ sơ nghiệp vụ và kết quả được ghi nhận, không tạo luồng duyệt chính thức song song. Người quản trị dự án được giao, Trưởng ban, QT-TC và lãnh đạo được giao xem tiền trong scope; hỗ trợ/kỹ thuật cần cấp riêng. Chưa biết hạn mức ký/duyệt. Xem DEC-013–017 tại [Sổ quyết định](../DECISIONS.md).

**Observed theo đối chiếu tài liệu:** E01–E18 trong [registry bằng chứng](TP_KD_EVIDENCE_AND_ACCEPTANCE.md) là vị trí nguồn đã đọc, không phải quyết định đã xác nhận hoặc kết luận nguồn còn hiệu lực pháp lý. S01 mô tả chức năng/chủ trì; S03–S05 cho thấy cách quản trị giá trị, revision và đối chiếu. Không tự nhận S05 là bằng chứng dịch vụ import hay đối chiếu kế toán đang chạy.

Các đoạn S01 bổ sung dưới đây dùng cùng hash/phiên bản S01 trong registry, theo nhãn paragraph/table của bản trích `.local/biz-001/S01.txt`: P064–P074 (QT-TC, kế toán, văn phòng, HR), P084–P098 (khảo sát, thiết kế, BIM/KCS), P101–P111 (Văn phòng Miền Nam, CNTT, TVGS), T02 (CT/TH/PH) và T03 (ánh xạ phân hệ đề xuất của tài liệu nguồn). Không sao chép tên người hoặc dữ liệu doanh nghiệp thực tế vào bản đồ.

**Proposed:** ranh giới A–M, cách bàn giao, RACI ở mục 4 và khung trạng thái ở mục 5 là thiết kế phân tích. **Unconfirmed:** phân quyền phê duyệt/ký chính thức, tiêu chuẩn hồ sơ từng loại, cam kết thời gian và owner cụ thể phải được xác minh theo mục 7.

## 2. Bản đồ xuyên công ty

~~~mermaid
flowchart LR
    A["A. Cơ hội / đấu thầu"] --> B["B. Dự án"]
    A --> C["C. Hợp đồng / phụ lục"]
    B --> C
    B --> D["D. Kế hoạch / giao việc"]
    C --> D
    C --> E["E. Giao khoán / thầu phụ"]
    D --> F["F. Khảo sát"]
    D --> G["G. Thiết kế / BIM / KCS"]
    E --> F
    E --> G
    F --> G
    F --> H["H. Sản lượng / nghiệm thu / request"]
    G --> H
    H --> I["I. Hóa đơn / tiền / công nợ"]
    C -. "tạm ứng theo điều khoản" .-> H
    I -. "nghĩa vụ còn tồn" .-> B
    J["J. Hồ sơ / văn bản"] -. "liên kết phiên bản suốt vòng đời" .-> C
    J -.-> G
    J -.-> H
    K["K. Nhân sự / phân công / quyền"] -. "scope và năng lực" .-> B
    K -.-> D
    L["L. KPI / báo cáo"] -. "đọc có kiểm quyền" .-> B
    L -.-> H
    L -.-> I
    M["M. Import / audit / notify / backup / incident"] -. "kiểm soát xuyên suốt" .-> J
    BASE["BASE: phê duyệt chính thức"] -. "reference đúng hồ sơ / bản" .-> A
    BASE -.-> C
    BASE -.-> H
~~~

Mũi tên biểu diễn đầu vào hoặc liên kết, không phải điều kiện bắt buộc mọi hồ sơ đi qua. Có đường giao trực tiếp không đấu thầu; project có thể mở từ giai đoạn dự thầu; hợp đồng, khoán và nghiệm thu có nhiều bản/đợt. Khảo sát không bắt buộc trước mọi thiết kế; dự án CNTT hoặc TVGS đi theo D/H với đầu ra chuyên môn riêng. Tạm ứng có thể trước nghiệm thu, không tạo nghiệm thu giả. J/K/L/M phục vụ cả A–I, các cạnh nét đứt chỉ minh họa.

Đóng task, phát hành hồ sơ kỹ thuật, nghiệm thu, duyệt request, ghi hóa đơn và thực trả là các sự kiện riêng. Hoàn thành dự án không mặc nhiên có nghĩa thanh lý mọi hợp đồng, hết công nợ hoặc giải tỏa giữ lại.

## 3. Danh mục A–M: bắt đầu, kết thúc và đầu ra

Các điểm bắt đầu/kết thúc dưới đây là **Proposed** dựa trên nguồn ghi ở cột cuối. “Kết thúc” là kết thúc một hồ sơ/đợt, có thể mở revision hoặc kỳ mới; không xóa lịch sử.

| Mã / quy trình | Điểm bắt đầu | Điểm kết thúc / bàn giao | Hồ sơ và nơi sử dụng | Căn cứ / khoảng trống chính |
| --- | --- | --- | --- | --- |
| **A — Cơ hội, đấu thầu** | Nhận thông tin CĐT/đối tác/gói thầu hoặc chủ trương phát triển | Không tham gia/thua/rút có lý do; hoặc kết quả trúng/giao trực tiếp đủ căn cứ chuyển B/C | Cơ hội, gói thầu, hồ sơ năng lực, phương án, hồ sơ nộp và kết quả; TP Projects/TP Documents | E02–E04, S01 P048–P063/T02; Unconfirmed: thẩm quyền tham gia, liên danh và tiêu chuẩn nộp |
| **B — Vòng đời dự án** | Cần quản trị scope từ cơ hội, trúng thầu hoặc giao trực tiếp | Hoàn thành/hủy có căn cứ, hồ sơ đóng và danh sách nghĩa vụ còn tồn; tiếp tục theo dõi I/J nếu cần | Project, company, mã, phòng chủ trì, owner, assignment, phạm vi và mốc; TP Projects | E01–E04, E18; Unconfirmed: điều kiện mở/đóng/reopen và owner phê chuẩn |
| **C — Hợp đồng, phụ lục** | Có nhu cầu đàm phán/ký hoặc sửa phạm vi pháp lý | Bản ký/hiệu lực được ghi nhận riêng; theo dõi đến thanh lý/chấm dứt, nghĩa vụ còn tồn chuyển H/I/J | Hợp đồng, revision, dòng scope, điều khoản, BASE reference, chữ ký, hiệu lực; TP Contracts | E03–E08/E10; Q1–Q4/Q8; CTR-001 mới đọc, không có action ghi |
| **D — Kế hoạch, giao việc** | Nhận nhiệm vụ từ đối tác/lãnh đạo hoặc cần phân rã phạm vi B/C | Kết quả được người có trách nhiệm tiếp nhận hoặc trả lại/hủy có lý do | WBS, nhiệm vụ một owner, đầu ra, hạn, phụ thuộc, BASE reference; TP Tasks/TP Projects | E01/E03/E04, S01 T02; Unconfirmed: chi tiết thay đổi hạn/đầu ra và nghiệm thu task |
| **E — Khoán, thầu phụ** | Phạm vi cần giao cho phòng hoặc đối tác và có căn cứ thực hiện | Phần khoán hoàn tất/chấm dứt, kết quả/đối chiếu chuyển H/I; nghĩa vụ hợp đồng theo C | Khoán nội bộ, thầu phụ công ty cấp 1, thầu phụ phòng cấp 2 có cha; TP Contracts/TP Projects/TP Finance | E09, S01 P059–P061; Q7/Q8; lương khoán sang K/I, không tạo vendor bill giả |
| **F — Khảo sát** | Có nhiệm vụ/đề cương, phạm vi và phân công được phép thực hiện | Hồ sơ khảo sát được kiểm tra và bàn giao có biên nhận hoặc trả lại sửa | Đề cương, nhật ký, dữ liệu gốc, kết quả nội nghiệp, biên bản hiện trường và bản bàn giao; TP Survey/TP Documents | E04, S01 P084–P089/T02; Unconfirmed: checklist, tiêu chuẩn và thẩm quyền theo loại khảo sát |
| **G — Thiết kế, BIM, thẩm tra, KCS** | Nhận nhiệm vụ, đầu vào được kiểm tra và version thiết kế cần thực hiện | Bản hồ sơ đủ kiểm soát chất lượng/phát hành, có biên nhận; hoặc vòng sửa có lý do | Hồ sơ bước thiết kế, mô hình, checklist/issues, kết quả thẩm tra/KCS, bản phát hành; TP Design/TP Documents | S01 P090–P098/T02; E17; Unconfirmed: người ký từng bước, tiêu chuẩn release và phối hợp thẩm định ngoài |
| **H — Sản lượng, nghiệm thu, request, tạm ứng, giữ lại** | Có kết quả thực hiện, đợt nghiệm thu hoặc điều khoản tạm ứng/giải tỏa giữ lại | Từng record được xác nhận/ghi nhận hoặc trả lại; request có kết quả BASE đúng bản chuyển I, vẫn theo dõi khoản chưa trả | Sản lượng, biên bản NT, đề nghị thanh toán, căn cứ tạm ứng/giữ lại; TP Projects/TP Finance/TP Contracts | E04–E10; Q4/Q8; sản lượng ≠ nghiệm thu ≠ request ≠ tiền |
| **I — Hóa đơn, thu chi, công nợ, đối chiếu** | Có nghĩa vụ/chứng từ hóa đơn, giao dịch tiền hoặc kỳ đối chiếu | Chứng từ hạch toán/đối chiếu đúng quyền, chênh lệch xử lý hoặc giao owner; số dư/giữ lại chuyển kỳ khi còn | Invoice, payment, phân bổ, reconciliation, lịch nghĩa vụ và bằng chứng; TP Finance | E07/E12–E16, S01 P064–P072; Q4/Q6/Q8; chưa có feed/bridge kế toán |
| **J — Văn bản, hồ sơ, phiên bản, lưu trữ** | Nhận/tạo tài liệu ở bất kỳ A–I/K/M | Bản phát hành/bàn giao/lưu được định danh, phân loại, truy xuất; hết hạn xử lý theo chính sách đã xác nhận | Metadata, version, hash, phân loại general/financial, liên kết nghiệp vụ, biên nhận; TP Documents | E01/E04/E10/E18, S01 P028/P074/P098; Unconfirmed: retention, con dấu, bản gốc và quyền hủy lưu |
| **K — Nhân sự, năng lực, phân công, quyền** | Tuyển/tiếp nhận/điều chuyển/nghỉ việc; nhu cầu assignment/grant hoặc chứng chỉ | Hồ sơ cập nhật, quyền cấp/đổi/thu hồi có kiểm chứng; nghĩa vụ bàn giao và lương chuyển đúng owner | Hồ sơ HR hạn chế, năng lực/chứng chỉ, assignment/grant có scope và thời hạn; TP HR/TP Projects | E18, S01 P063/P073/T03; Q2; Unconfirmed: quy chế HR/lương khoán và người cấp grant |
| **L — KPI, báo cáo, cảnh báo** | Kỳ báo cáo hoặc yêu cầu đọc dữ liệu trong quyền | Báo cáo ghi kỳ, basis, nguồn/freshness/coverage; chênh lệch giao owner, chưa xác nhận phải gắn nhãn | Tiến độ, chất lượng, sản lượng, NT, tiền, chênh lệch, warning; TP Dashboard | E05–E17; Q4–Q6; không tự gọi NT chính trừ NT cấp 1 là lợi nhuận kế toán |
| **M — Kiểm soát dữ liệu và vận hành** | File import, transition, thông báo, lịch backup hoặc incident | Import được kiểm/đối chiếu trước phát hành; audit bảo vệ; backup có restore evidence; incident khắc phục và bàn giao | Staging/provenance, audit, thông báo có scope, backup/restore report, incident log; dùng xuyên hệ thống | E10–E16/E18, S01 P103–P107; OPS-001 chỉ đạt local; RPO/RTO, ngoài máy, production chưa xác nhận |

Không tạo thêm phân hệ hiển thị chỉ để đặt tên A/L/M. Các mã là nhóm quy trình; tên sản phẩm/phân hệ theo [Quy ước tên](TP_PRODUCT_NAMING.md). Mua sắm/tài sản, thương hiệu, CNTT và TVGS trong S01 được nhận diện tại A/E/I/J/K/M hoặc tuyến D/H; workflow chuyên ngành chi tiết còn thiếu, không được coi là đã đặc tả đủ chỉ từ bản đồ này.

## 4. RACI ở mức quy trình

**Toàn bộ ma trận này là Proposed.** S01 T02 chỉ có CT (chủ trì), TH (thực hiện), PH (phối hợp), chưa xác nhận đầy đủ R/A/C/I. Không chuyển CT thành người được ký/duyệt pháp lý. A dưới đây là **một đầu mối chịu trách nhiệm quy trình** được chỉ định trong scope, không phải approver BASE hoặc người ký; các vai trò có thể do cùng người đảm nhiệm chỉ khi quy chế cho phép. R thực hiện; C được hỏi ý kiến; I được nhận thông tin đúng quyền. Mỗi hồ sơ/task cụ thể phải có một owner, không chỉ ghi tên tập thể.

| Quy trình | R — thực hiện | A — đầu mối chịu trách nhiệm (đề xuất) | C — phối hợp/rà soát | I — nhận kết quả đúng scope | Nguồn / lưu ý |
| --- | --- | --- | --- | --- | --- |
| A | KD; chuyên môn thực hiện giải pháp; CNTT/TVGS theo lĩnh vực | Trưởng ban KD hoặc owner cơ hội được giao | BIM-QC, Thiết kế, Kỹ thuật, QT-TC | Lãnh đạo được giao; chủ dự án sau khi hình thành | E02–E04, S01 T02; quyết định tham gia/ký cần authority riêng |
| B | Chủ dự án và điều phối được giao | Giám đốc/chủ dự án được chỉ định | KD, trưởng phòng thực hiện, QT-TC | Lãnh đạo, người được phân công | E01/E03/E18; S01 P029; chưa chốt một chức danh áp dụng mọi project |
| C | KD/chủ trì hồ sơ hợp đồng | Trưởng ban KD hoặc owner hợp đồng được chỉ định | QT-TC, chuyên môn, người có thẩm quyền | Chủ dự án, phòng thực hiện; support chỉ metadata/bản che tiền | E03/E04/E18; A không tự có quyền ký |
| D | Điều phối kế hoạch và từng task owner | Chủ dự án | Trưởng phòng nhận việc, KD, đối tác khi liên quan | Lãnh đạo, bên phụ thuộc | E01/E03; mỗi task một owner, tham chiếu BASE |
| E | KD và phòng nhận khoán | Owner khoán cấp công ty được chỉ định; cấp 2 có owner riêng | QT-TC, chuyên môn, chủ dự án | Lãnh đạo đúng scope; phòng/đối tác nhận đúng phần | E09, S01 P059–P061; cha-con không đổi người chịu trách nhiệm pháp lý |
| F | Kỹ thuật/đội khảo sát hoặc thầu phụ trong scope | Chủ trì khảo sát được giao | BIM-QC/KCS, Thiết kế, chủ dự án | KD, bên nhận đầu vào thiết kế | S01 P084–P089/T02; người kiểm tra không mặc định người phát hành |
| G | Thiết kế/BIM-QC theo gói; người thẩm tra/KCS được giao | Chủ nhiệm thiết kế/chủ trì gói được chỉ định | Kỹ thuật, BIM-QC/KCS, chủ dự án; TVGS khi có yêu cầu | KD, đối tác nhận bản phát hành theo quyền | S01 P090–P098/T02; vai trò sản xuất và kiểm tra phải phân biệt |
| H | KD/Kế hoạch lập hồ sơ; chuyên môn xác nhận kết quả | Owner nghiệm thu/request được giao | Chủ dự án, phòng thực hiện, QT-TC, đối tác | Người record/verify BASE được giao; I nhận hồ sơ hợp lệ | E03–E08; chuyên môn, thương mại và duyệt chi là các trách nhiệm riêng |
| I | Kế toán/QT-TC theo quyền chứng từ | Đầu mối QT-TC được chỉ định | KD, chủ dự án, đối tác/ngân hàng khi liên quan | Lãnh đạo và người xem tiền được giao | S01 P064–P072, E15; posting/reconcile theo kế toán, không do KD tự kết luận |
| J | Văn thư/chủ hồ sơ; người chuẩn bị bản phát hành | Owner hồ sơ theo loại tài liệu được chỉ định | Chủ dự án, chủ nhiệm thiết kế, QT-TC, CNTT | Người nhận hồ sơ có quyền; bên ngoài qua kênh được phép | S01 P028/P074/P098; chưa xác nhận một owner lưu trữ toàn công ty |
| K | QT-TC/HR; quản trị quyền thực hiện quyết định đã có | Đầu mối nhân sự/quyền được chỉ định cho từng loại quyết định | Trưởng phòng, chủ dự án, CNTT, người cấp grant được chỉ định | Người bị tác động và owner bàn giao, hạn chế hồ sơ HR | S01 P073/T03, E18; Q2 còn mở, runtime grant hiện chỉ superuser cấp |
| L | Người lập báo cáo/KD/QT-TC theo chỉ tiêu | Owner chỉ tiêu/báo cáo được chỉ định | Owner dữ liệu, chuyên môn, CNTT | Lãnh đạo/người dùng đúng scope | E12–E17; tổng hợp không được mở rộng quyền tiền |
| M | CNTT/vận hành; owner dữ liệu sửa mapping/reconcile | Owner được giao theo import, backup hoặc incident | Owner nghiệp vụ, QT-TC, người phụ trách quyền | Người bị ảnh hưởng/lãnh đạo tùy mức sự cố | S01 P103–P107, E10–E16/E18; owner vận hành không tự quyết dữ liệu nghiệp vụ |

Người phê duyệt chính thức trên BASE, người record kết quả, người verify bằng chứng và người ký hợp đồng cần được chỉ định riêng theo Q1–Q3. Không mặc định họ trùng A/R, không tự đặt quy tắc bốn mắt khi chưa xác nhận. Mọi I/C vẫn chịu hạn chế company/project/department, hồ sơ nhân sự và quyền tiền.

## 5. Khung trạng thái và chuyển giai đoạn

Đây là **Proposed ở mức bản đồ**, dùng để đọc các điểm bàn giao; không phải một state machine chung hoặc enum để triển khai hàng loạt. Khung chi tiết A–M thuộc hai tài liệu workflow; hợp đồng đã có ánh xạ runtime tại mục 4.4 của workflow KD.

| Trục riêng | Ý nghĩa khung | Điều kiện bàn giao phải kiểm | Không được suy ra |
| --- | --- | --- | --- |
| Chuẩn bị/rà soát hồ sơ | Nháp → gửi rà soát → trả lại/hoàn tất rà soát | Đúng version, owner, scope, trường/evidence tối thiểu; trả lại có lý do | Hoàn tất rà soát = BASE approved |
| Quyết định ngoài hệ thống | Chờ kết quả → ghi quyết định BASE; evidence chưa kiểm/đã kiểm/tranh chấp riêng | Reference đúng hồ sơ/bản, actor/thời điểm quyết định, evidence, authority và người verify | Upload ảnh = verified; BASE approved = ký/hiệu lực/đã trả |
| Thực hiện | Được phép thực hiện → đang làm/tạm dừng → nộp kết quả → tiếp nhận/trả lại | Căn cứ thực hiện, đầu vào/đầu ra, phạm vi, lý do dừng/hủy và người nhận | Task hoàn tất = sản lượng/NT tiền được xác nhận |
| Phát hành/hiệu lực | Bản kiểm soát → bản phát hành hoặc bản ký/hiệu lực theo domain | KCS cho hồ sơ kỹ thuật; chữ ký/thẩm quyền/ngày/điều kiện hiệu lực cho hợp đồng | KCS = phê duyệt của CĐT; ngày upload = ngày hiệu lực |
| Nghĩa vụ và kế toán | Request, NT, hóa đơn, tiền, giữ lại có trạng thái/phân bổ riêng | Cùng company/project/scope/currency/basis; chứng từ và điều khoản đúng đợt | Request approved = paid; acceptance trừ cash = công nợ đến hạn |
| Bản và sửa sai | Nháp sửa được; đã chốt tạo revision/correction/void có liên kết | Lý do, quyền, tác động đến downstream và báo cáo; kế toán posted theo đảo chuẩn | Sửa mới được xóa bản cũ hoặc tự đảo payment |
| Kết thúc/lưu trữ | Hoàn thành/chấm dứt theo từng đối tượng → bàn giao lưu | Checklist hồ sơ, nghĩa vụ tồn, owner tiếp tục theo dõi; reopen có lý do | Đóng project = thanh lý hợp đồng = hết giữ lại |

Mọi transition chi tiết cần actor/capability, company/project/department scope, state trước, guard dữ liệu, state sau, lý do, evidence/version, audit và người nhận thông báo. Action ghi chạy transaction Odoo, kiểm đồng thời và retry; frontend chỉ gọi action. Những nguyên tắc này xác định yêu cầu thiết kế, không tuyên bố đã có action runtime.

## 6. Hợp đồng bàn giao liên phòng

Một bàn giao phải xác định **bên giao, một owner nhận, đối tượng/ID, version/hash, scope, danh sách đầu ra, hạn nếu đã thống nhất, mức bảo mật, bằng chứng nhận/trả lại và việc còn tồn**. Thiếu dữ liệu phải trả về trạng thái thiếu/chưa xác nhận, không thay bằng 0 hoặc tự coi đã nhận. Link NAS/BASE là provenance; không thay database nghiệp vụ Odoo, không tự cấp quyền tải file.

| Điểm | Bên giao → bên nhận | Gói bàn giao tối thiểu (Proposed) | Cổng/ngoại lệ cần giữ |
| --- | --- | --- | --- |
| A → B/C | KD → owner dự án/KD hợp đồng | Kết quả thầu/giao trực tiếp, phạm vi, đối tác, hồ sơ và quyết định liên quan | Không có kết quả thì giữ project giai đoạn dự thầu; không gọi đã ký |
| B/C → D/E | Chủ dự án/KD → phòng thực hiện/phòng nhận khoán | ID dự án, scope/version, đầu ra, mốc, một owner, căn cứ được phép làm, điều khoản cần biết | Bản chưa hiệu lực ghi nhãn; thực hiện sớm cần căn cứ riêng được xác nhận |
| D/E → F/G | Điều phối/phòng nhận → chủ trì chuyên môn | Task/gói, đầu vào được kiểm, tiêu chuẩn/checklist, phụ thuộc, reference BASE khi có | Quyền task không cấp tiền; chuyển phần kỹ thuật/bản che tiền cho người không grant |
| F → G | Kỹ thuật → chủ nhiệm thiết kế/BIM | Dữ liệu gốc, phương pháp, kết quả kiểm tra, hạn chế/chưa đủ, version bàn giao | Thiết kế phải biết đầu vào tạm; sửa khảo sát tạo thông báo tác động đúng bản |
| F/G → H | Chủ trì chuyên môn/KCS → KD/Kế hoạch | Bản kiểm/phát hành, bằng chứng giao nhận, khối lượng/kỳ/phạm vi và tồn tại | Chưa KCS không gắn nhãn phát hành đạt; phát hành không tự thành NT tiền |
| H → I | KD/Kế hoạch → QT-TC/Kế toán | Biên bản/điều khoản, request đúng version, kết quả BASE có nhãn xác minh, cơ sở thuế/currency, tạm ứng/giữ lại | QT-TC trả hồ sơ thiếu có lý do; request không tạo payment; tạm ứng không bắt buộc NT giả |
| I → H/B/L | QT-TC → owner request/dự án/báo cáo | Chứng từ hóa đơn/tiền, phân bổ, trạng thái đối chiếu, ngày/kỳ, chênh lệch và owner xử lý | Tiền chưa đối chiếu mang nhãn observation; không trình bày như posted/reconciled |
| B/C/H/I → J | Owner nghiệp vụ → owner lưu trữ | Checklist đóng, hồ sơ/bản cuối, nghĩa vụ tồn/owner, phân loại, reference và lịch sử | Thanh lý còn giữ lại phải giữ theo dõi; retention/xóa lưu chưa chốt |
| K → các owner/M | HR/người quyết định quyền → chủ dự án/vận hành | Quyết định phân công/thu hồi, scope, thời hạn, người thực hiện và kết quả kiểm tra | Thu hồi phải tác động request sau; tài khoản admin không thay quyết định nghiệp vụ |
| Các owner → L | Owner dữ liệu → owner báo cáo | Kỳ, chỉ tiêu/công thức, nguồn, basis/currency, coverage/freshness và mức xác nhận | Báo cáo không cộng cấp 2 hai lần, không gộp null=0 hoặc các basis khác nhau |
| M ↔ owner dữ liệu | Vận hành → owner nghiệp vụ → vận hành | Batch/hash/mapping, lỗi/reconcile hoặc incident/tác động, quyết định xử lý và bằng chứng hoàn tất | Không phát hành import lỗi hoặc dùng backup thành công thay restore test; thông báo/audit theo cùng quyền |

Không phát tán tiền qua tiêu đề, mô tả, tên file, notification, audit hoặc báo cáo tổng hợp cho người chỉ có metadata. Các file/hồ sơ tài chính cần grant đúng project; I trong RACI không phải danh sách gửi email tự động. Tài liệu này không yêu cầu gửi thông báo ra ngoài.

## 7. Khoảng trống và cổng rà soát

Q1–Q8 giữ nguyên định danh/nội dung ở [workflow KD](TP_KD_WORKFLOW_AND_PERMISSIONS.md); không đánh số lại hoặc coi câu hỏi đã đóng trong BIZ-002. Các đầu mối sau là **Proposed** để thu thập bằng chứng, không phải phân công nhân sự đã có hiệu lực.

| Khoảng trống (Unconfirmed) | Phạm vi / liên quan | Đầu mối rà soát đề xuất | Bằng chứng để chốt / phần được tiếp tục |
| --- | --- | --- | --- |
| Thẩm quyền, hạn mức, phân tách lập/soát/record/verify, người cấp grant, BASE evidence | A/C/E/H/K; Q1–Q3 | Lãnh đạo, KD, QT-TC | Văn bản và 2–3 hồ sơ khử dữ liệu; tiếp tục phân tích/read và draft trên test độc lập, giữ đóng action xác minh/chốt liên quan |
| Thuế, currency/basis, ngày hiệu lực/hồi tố, kỳ khóa, nguồn kế toán | C/H/I/L; Q4/Q6 | QT-TC/Kế toán và KD | Chứng từ/điều khoản và ca đối chiếu; chưa công bố công nợ/thuế/as-of chính thức từ observation |
| Catalog hạng mục/bước thiết kế và mapping | A/D/F/G/L/M; Q5 | BIM-QC, Thiết kế, Kỹ thuật, KD | Catalog/mapping được duyệt; không tự gộp bằng tên hoặc discipline trộn stage |
| Vượt khoán, correction/void sau chốt, tạm ứng/giữ lại | E/H/I; Q7/Q8 | KD, QT-TC, chủ dự án | Quy chế và hồ sơ ngoại lệ; trước đó cảnh báo vượt mẹ, không auto-block/auto-đảo/xóa |
| RACI và tiêu chuẩn bàn giao từng phòng | A–M | Owner quy trình và lãnh đạo được giao | Rà soát mỗi hàng RACI, chỉ định A/owner cụ thể, checklist đầu vào/đầu ra, SLA nếu có; không tự điền SLA |
| Tiêu chuẩn kỹ thuật/phát hành/thẩm tra và thay đổi đầu vào | F/G/J | Kỹ thuật, Thiết kế, BIM-QC, chủ dự án | Đề cương, checklist KCS, log issue, bản phát hành/biên nhận; phân biệt KCS nội bộ với chấp thuận bên ngoài |
| HR, lương khoán, dữ liệu cá nhân, chứng chỉ, on/offboarding | K/E/I/J | QT-TC/HR, trưởng phòng, KD | Quy chế và hồ sơ khử dữ liệu; không suy payroll từ nghiệm thu khoán hoặc dùng quyền project để đọc HR |
| Lưu trữ, bản gốc, con dấu, retention/hủy lưu; mua sắm/tài sản, CNTT/TVGS chuyên ngành | J/K/M và tuyến A–I | QT-TC, CNTT, owner chuyên ngành | Chính sách/tình huống cụ thể; mới nhận diện liên kết, chưa đủ workflow chi tiết chuyên ngành |
| Ownership KPI và vận hành production | L/M | KD, QT-TC, CNTT, lãnh đạo | Công thức/kỳ/owner được rà soát; lịch backup, retention/mã hóa/ngoài máy, RPO/RTO và incident drill; OPS-001 local không đủ nghiệm thu production |

**Điều kiện hoàn tất baseline tài liệu BIZ-002:** A–M có ranh giới, RACI đề xuất, đầu ra/bàn giao, workflow chi tiết và gaps truy được nguồn; link/nội dung nhất quán với status và quyết định hiện hành. **Điều kiện nghiệm thu nghiệp vụ:** chủ nghiệp vụ rà soát RACI/khung state bằng hồ sơ khử dữ liệu và ghi quyết định cho từng gap liên quan. Hai mức này khác nhau; việc có đủ tài liệu không tự mở code, pilot hoặc production.

## 8. Ranh giới runtime được đối chiếu

Theo [PROJECT_STATUS](../PROJECT_STATUS.md) và [source structure](TP_PLATFORM_SOURCE_STRUCTURE.md), nền đọc project/assignment đã có; CTR-001 đọc hợp đồng/revision/phạm vi, BASE reference và tài liệu đã kiểm trên dev với dữ liệu giả lập. `financial_read` đã có theo user + project; chỉ superuser cấp khi Q2 chưa chốt. Project coordinator và Platform Manager không tự có tiền/quyền duyệt; superuser có khả năng truy cập kỹ thuật.

Các workflow ghi của A–M, tích hợp BASE, bridge kế toán, import thật, nghiệp vụ khảo sát/thiết kế/HR và vận hành production chưa được coi là triển khai chỉ vì xuất hiện trong bản đồ. Tài liệu này không đổi model/API, không chạy setup/upgrade, không nhập dữ liệu và không thay trạng thái runtime.
