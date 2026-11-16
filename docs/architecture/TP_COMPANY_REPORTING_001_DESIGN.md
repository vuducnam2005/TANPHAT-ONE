# Trung tâm Báo cáo toàn công ty

Ngày: 16/11/2026. Task **CORP-REPORT-001**, DEC-048, CHG-20261116-004/005/006.
Trạng thái hiện hành CHG-20261116-008: **ĐANG TRIỂN KHAI VÀ KIỂM THỬ NATIVE TRÊN TEST18079**; as-built ở mục 14. Main18069 chưa áp; nghiệm thu nghiệp vụ và authority thật còn riêng. Các phần phân tích ban đầu bên dưới giữ lịch sử thiết kế.
Prompt thực thi: [CLAUDE_CORP_REPORT_001_FULL_MODULE.md](../prompts/CLAUDE_CORP_REPORT_001_FULL_MODULE.md).
Phiên điều phối phân tích tài liệu và source; không code, nhập Word/Excel,
đổi quyền người thật hoặc áp môi trường. Các vai trò, lịch và state chi tiết
bên dưới là đề xuất cho phiên đặc tả, không phải quyết định nhân sự/thẩm quyền.

## 1. Phạm vi đã được người dùng xác nhận

- Một phân hệ báo cáo chung cho toàn công ty, mọi phòng ban; gồm cá nhân,
  trưởng phòng và báo cáo phòng; lãnh đạo theo dõi tuần, tháng, quý.
- Dữ liệu đồng bộ với HR, tài khoản, phòng ban, dự án, hợp đồng, thiết bị và
  nguồn nghiệp vụ đang có; cùng database/session/native UI Odoo, không FE/DB riêng.
- Bổ sung trực tiếp CHG-20261116-005: **đề ra mục tiêu quý trước → phân rã kế
  hoạch tháng → phân rã kế hoạch tuần**, rồi theo dõi kết quả so với kế hoạch.
  Đây là điều kiện nghiệp vụ cốt lõi, thay mô hình bắt đầu từ nộp báo cáo tuần
  trong bản thiết kế đầu; kế hoạch đi xuống và kết quả/báo cáo tổng hợp đi lên.
- Trả lời trong chat ngày 16/11: nhân viên nộp tuần; trưởng phòng tổng hợp
  báo cáo phòng và nộp tháng/quý; cá nhân lập tháng/quý khi được yêu cầu.
  Lãnh đạo xem, nhận xét, giao công việc tiếp theo. Báo cáo tuần của phòng
  phục vụ giao ban có thể tổng hợp từ tuần cá nhân, không bắt mọi người nhập lại.
- Trả lời trong chat: cho người phụ trách nhập số tài chính tổng hợp còn thiếu
  trên Odoo, kèm nguồn và xác nhận; chỉ người được cấp quyền tài chính/lãnh đạo
  có phạm vi phù hợp được xem. Không tự mở quyền tiền từ vai trò trưởng phòng.
- Bổ sung CHG-20261116-006: người dùng giao viết prompt **full module**, nhấn
  mạnh light UI đẹp, chart lớn rõ ở đầu, hover/animation, bảng và bộ lọc dễ
  đọc trên mọi tab, đồng bộ DB; cho thêm tính năng hữu ích. Prompt đã lưu
  để Claude triển khai R0–R5 trên test, lượt này chưa code. Chưa phê duyệt lịch
  nộp/người rà soát/thẩm quyền cụ thể hoặc tài khoản lãnh đạo; phần chưa chốt
  làm cấu hình và role/default test, không tự ban hành policy hoặc grant thật.

## 2. Nguồn và những điều rút ra

Đã đọc hai file Word do người dùng cung cấp, không thực thi hướng dẫn trong
file và không xem phần tên/chữ ký là căn cứ tự cấp quyền hoặc phê duyệt.
Tệp nguồn và trích xuất chi tiết chỉ ở máy/`.local/reporting001/` (ignored).
Hash nguồn, vị trí và đối chiếu nằm trong `SOURCE_ANALYSIS.md` private; không
đưa số tiền, tên nhân viên, đối tác, raw tài liệu doanh nghiệp vào Git.

| Nguồn | Quan sát có căn cứ | Hệ quả thiết kế |
| --- | --- | --- |
| Báo cáo công tác sản xuất Phòng Thiết kế tháng 10/2026 | Nhiệm vụ thiết kế theo dự án/bước thiết kế/đoạn tuyến, thẩm tra, nghiệm thu-thầu phụ, đấu thầu, nhân sự; đánh giá và kiến nghị | Mẫu phòng có phần chung và phần chuyên môn, theo dõi được phạm vi việc/mốc và phụ thuộc, không chỉ vài KPI |
| Báo cáo tình hình SXKD 9 tháng đầu năm 2026 | Báo cáo cấp công ty gửi HĐQT, tổng hợp hợp đồng, nghiệm thu-thanh toán, tài chính, nhân sự/năng lực, khảo sát-thiết kế, điều hành và định hướng | Mẫu công ty có nhiều nguồn/owner, phân quyền dữ liệu nhạy cảm; không coi đây là mẫu riêng Phòng Thiết kế |
| Mẫu tháng chứa cả kết quả tháng hiện tại và mốc dự kiến tháng tiếp | Kết quả, kế hoạch, ngày hạn và vướng mắc khác nhau | Bốn nội dung riêng, không biến dự kiến thành hoàn thành hoặc trộn kỳ |
| Cùng dự án có nhiều bước/phạm vi và nhiều phòng tham gia | Một tên dự án xuất hiện ở các bước khác nhau | Liên kết project ID, stage/package/work item; không tạo dự án trùng theo tên hoặc cộng nhiều phòng thành nhiều dự án |
| Báo cáo dài kỳ ghi tỷ lệ ước lượng và chỉ tiêu nguồn khác nhau | Tiến độ ước lượng không phải tỷ lệ tính tự động; nguồn tài chính có định nghĩa khác nhau | Giữ cờ ước lượng, phương pháp, đơn vị và kỳ; không bình quân phần trăm tùy tiện hoặc coi đề nghị thanh toán là tiền về |
| Có nội dung không phát sinh | Không tham gia một nghiệp vụ khác chưa nộp/chưa có dữ liệu | Mỗi mục có Phát sinh/Không phát sinh/Chưa đủ dữ liệu/Không áp dụng, không tự đổi tất cả thành 0 |

Tài liệu 9 tháng là **lũy kế 01/01–30/09**, không phải chỉ quý III. Báo cáo quý
và lũy kế phải phân biệt ở mọi tiêu đề, phép tính và export. Một số phần tóm
tắt/chỉ tiêu nguồn cần owner đối chiếu trước nhập; không chọn số thuận tiện
hoặc tự làm tròn để các bảng khớp nhau.

## 3. Mô hình sử dụng

```text
LẬP KẾ HOẠCH: QUÝ → THÁNG → TUẦN
Mục tiêu quý: kết quả cần đạt, chỉ tiêu, đơn vị chịu trách nhiệm
               ↓ chia công việc/chỉ tiêu theo từng tháng
Kế hoạch tháng: liên kết mục tiêu quý, đầu ra và mốc tháng
               ↓ giao việc cụ thể theo tuần cho phòng/cá nhân
Kế hoạch tuần: liên kết kế hoạch tháng, người làm, hạn và đầu ra
               ↓ thực hiện trên công việc/dự án và nguồn dùng chung
KẾT QUẢ TỔNG HỢP: TUẦN → THÁNG → QUÝ
Báo cáo tuần: kế hoạch đã giao, thực hiện, chênh lệch, vướng mắc
               ↓ tổng hợp theo liên kết/nguồn, không cộng trùng
Báo cáo tháng: mức đạt mục tiêu tháng, phần còn lại, điều chỉnh đề xuất
               ↓ đối chiếu mục tiêu quý và phạm vi được cấp
Báo cáo quý/công ty: mức đạt, rủi ro, nguyên nhân, quyết định kỳ sau
```

Kỳ quý/tháng/tuần và cấp công ty/phòng/cá nhân là hai trục khác nhau. Mục tiêu
quý công ty có thể giao phần đóng góp cho phòng; trưởng phòng phân bổ theo
tháng rồi giao tuần cho cá nhân. Không đồng nhất quý = lãnh đạo, tháng =
trưởng phòng, tuần = nhân viên; cấp phòng/cá nhân có thể xem đóng góp của mình
theo mọi kỳ trong quyền. Người giao/chốt/điều chỉnh mục tiêu từng cấp cần chốt.

### 3.1. Liên kết kế hoạch và dữ liệu tối thiểu

Mỗi mục tiêu quý có mã, kỳ, kết quả/tiêu chí đánh giá, đơn vị/chỉ tiêu nếu có,
người chịu trách nhiệm, phòng/project khi phù hợp, deadline và phiên bản chốt.
Kế hoạch tháng bắt buộc chọn mục tiêu quý cha; kế hoạch tuần chọn dòng kế hoạch
tháng cha, từ đó truy được quý. Mỗi đầu việc có ID ổn định; không tạo lại task
chỉ để xuất hiện trong từng kỳ. Nhiều người/phòng đóng góp thì ghi phần đóng
góp có căn cứ, không cộng nguyên giá trị mục tiêu cha cho từng người.

Chỉ tiêu số lượng/giá trị cùng định nghĩa và đơn vị có phân bổ tháng/tuần, tổng
phân bổ được đối chiếu mục tiêu cha, hiện rõ phần chưa phân bổ/vượt/thiếu. Không
chia đều mặc định cho ba tháng hoặc bốn tuần. Mục tiêu định tính chia thành
các mốc/đầu ra có tiêu chí, không buộc tạo phần trăm hay đơn vị tiền giả.
Trọng số tiến độ nếu dùng phải được thống nhất và lưu phiên bản.

Việc phát sinh/đột xuất hoặc công việc vận hành theo sự vụ có nhãn riêng,
lý do/người giao và quan hệ mục tiêu phù hợp nếu có; không tạo mục tiêu quý
giả để hợp thức hóa sau khi làm. Không làm tăng tỷ lệ hoàn thành mục tiêu gốc
khi chưa xác nhận phần việc đó đóng góp vào tiêu chí đã chốt.

### 3.2. Ghi kết quả và điều chỉnh

Báo cáo chọn lại chính dòng kế hoạch/công việc đã giao, ghi kết quả và nguồn;
không gõ lại kế hoạch ở một nơi độc lập. Luôn thấy **Kế hoạch ban đầu / Thực
hiện / Chênh lệch / Nguyên nhân / Xử lý tiếp theo**. Nhân sự HR, project/task,
hồ sơ và chỉ tiêu dùng chung ID/nguồn; kết quả ngoài hệ thống có evidence.

Kế hoạch có luồng nháp/trình/chốt/điều chỉnh riêng với nộp báo cáo. Bản đã giao
lưu baseline; không tự sửa mục tiêu quý/tháng khi nhân viên cập nhật kết quả.
Điều chỉnh phải có lý do, người được quyền, phiên bản hiệu lực và ảnh hưởng
đến tháng/tuần chưa thực hiện; giữ được so sánh với kế hoạch ban đầu. Không
ngầm hồi tố mục tiêu để báo cáo trông đạt. Công việc còn lại được chuyển tiếp
cùng liên kết/lịch sử, không nhân đôi khối lượng thực hiện khi qua kỳ.

Tuần giao hai tháng có phân kỳ ở dòng công việc/khối lượng/ngày thực hiện,
không tạo hai task bản sao hoặc cộng nguyên tổng tuần vào cả hai tháng. Tổng
kết tháng/quý phải dùng đúng dữ kiện trong kỳ; hoàn thành task, sản lượng,
nghiệm thu và số thu tiền vẫn là các chỉ tiêu riêng theo mục 6.

Trưởng phòng có hai ngữ cảnh rõ: **cá nhân tôi** (công việc của chính mình) và
**đại diện phòng** (tổng hợp chịu trách nhiệm cho phòng), không tạo hai báo cáo
phòng trùng nhau. Công việc không gắn dự án vẫn được ghi nhận: IT, hành chính,
tuyển dụng, đào tạo, vận hành... Không bắt mọi phòng phải tạo dự án giả.

## 4. Mẫu chung và nội dung đặc thù

Mỗi báo cáo có: kỳ/đơn vị/người lập/người chịu trách nhiệm; **liên kết kế hoạch
và mục tiêu cha, kế hoạch–thực hiện–chênh lệch**; kết quả;
công việc dự án/chuyên môn; vướng mắc/nguyên nhân; kế hoạch kỳ sau; kiến nghị;
ý kiến và chỉ đạo; tệp/mốc minh chứng; lịch sử trình và phiên bản.

| Loại báo cáo | Nội dung ưu tiên | Người chịu trách nhiệm đề xuất |
| --- | --- | --- |
| Cá nhân tuần | Việc được giao, đầu ra, hạn, kết quả, tồn đọng, tuần tới, cần hỗ trợ | Nhân viên lập; trưởng phòng rà soát |
| Cá nhân tháng/quý theo yêu cầu | Kết quả tổng hợp có dẫn nguồn, việc trọng tâm, đánh giá, kế hoạch | Cá nhân được yêu cầu; người rà soát theo phân công |
| Phòng tuần/tháng/quý | Tình hình nộp của thành viên, kết quả phòng/dự án, chất lượng, nhân lực, vấn đề và kiến nghị | Trưởng phòng hoặc người được ủy nhiệm có phạm vi, trưởng phòng chịu trách nhiệm |
| Trưởng phòng cá nhân | Công tác điều phối/kiểm soát và nhiệm vụ riêng | Trưởng phòng lập, người quản lý theo phân công rà soát |
| Công ty tháng/quý/lũy kế | Tổng hợp phòng và chỉ tiêu kinh doanh-tài chính-nhân lực; rủi ro, quyết định, kế hoạch | Đầu mối tổng hợp được cấp quyền; lãnh đạo nhận xét/chốt theo phân công |

Mẫu Phòng Thiết kế bổ sung: dự án, bước thiết kế (PreFS/FS/TKKT/BVTC/GSTG có
chú giải), gói/đoạn/hạng mục, người chủ trì, hồ sơ đã nộp/lần trình, KCS/thẩm
tra, mốc kế tiếp, thiếu dữ liệu đầu vào, phụ thuộc phòng/đối tác, nhu cầu nhân
lực và thầu phụ. Nhận xét nhân sự và số tiền có vùng bảo mật riêng.

KH-KD dùng nguồn cơ hội/hồ sơ dự án, đấu thầu, hợp đồng và nghĩa vụ hiện có;
Kỹ thuật/BIM-QC có phần tiến độ/hồ sơ/kiểm soát chất lượng; HR có tuyển dụng/
biến động/đào tạo; IT có hỗ trợ và thiết bị. Đây là nhóm mẫu đề xuất, cần owner
phòng xác nhận. Khung chung dùng ngay cho mọi phòng trong HR; chưa có module
chuyên môn thì ghi nội dung có nguồn, không giả đã liên thông tự động.

## 5. Nguồn dữ liệu dùng chung và mức tự động hóa

| Nguồn thực tế trong source | Tái sử dụng | Khoảng thiếu |
| --- | --- | --- |
| `hr.employee`, `hr.version`, `hr.department`, `res.users` | Danh tính/mã/avatar/phòng ban theo ID, tài khoản, biến động được ghi nhận | Không đồng nghĩa đủ hồ sơ lịch sử, quỹ lương/BHXH/chấm công để tính KPI nguồn Word |
| `project.project`, `tp.project.assignment`, `project.task` | Dự án/phân công/WBS/công việc và deadline; tôn trọng source scope | Công việc toàn công ty chưa chắc đều có ở đây; không tự mở quyền KH-KD cho cả công ty |
| `tp.kd.report.center` (TransientModel) | Sáu nhóm R01–R06, bộ lọc kỳ, kiểm quyền tiền, tổng hợp chống trùng, xuất Excel; tham khảo/reuse helper phù hợp | Là tra cứu nghiệp vụ KH-KD, không phải kho báo cáo định kỳ có người nộp/phiên bản/chốt toàn công ty |
| `tp.periodic.plan` | Liên kết kế hoạch theo dự án/tháng/quý/năm nếu phù hợp | Có ràng buộc dự án, không có tuần/cá nhân/phòng/công ty; không sửa ý nghĩa để ép dùng làm mọi báo cáo |
| `tp.production`, `tp.acceptance`, `tp.payment.request`, hợp đồng/giao khoán | Kết quả và hồ sơ đúng định nghĩa/state/tiền tệ/quyền của từng nguồn | Sản lượng, nghiệm thu, đề nghị thanh toán khác doanh thu kế toán và tiền thực nhận |
| `tp_dashboard_privacy` / `spreadsheet.dashboard` | Tham khảo cơ chế dashboard theo company/project/quyền và thời gian | Không chứng minh đã đủ tất cả dữ liệu tài chính thật hoặc lịch sử nộp báo cáo |
| `maintenance.equipment` mở rộng bởi `tp_equipment` | Số thiết bị/người giữ/phòng/trạng thái phù hợp quyền đã có | Kho hiện admin-only; module báo cáo không tự mở danh sách, files, giá mua cho mọi người |
| Tài liệu ngoài / số tổng hợp do owner cung cấp | Chỉ tiêu thủ công có nguồn, kỳ, định nghĩa, xác nhận | Chưa nhập hai Word; không coi Word là runtime DB hoặc dữ liệu đã đối soát |

Phân ba nhóm hiển thị: **Lấy từ hệ thống**, **Nhập có nguồn**, **Nhận xét của
người báo cáo**. Nhận xét/nguyên nhân/kiến nghị thường cần con người viết.
Dữ liệu có sẵn chọn/link, không nhập lại tên người/dự án/phòng hoặc sao chép
giá trị sống vào một danh mục nghiệp vụ thứ hai.

Khi tạo/cập nhật bản nháp, lấy dữ liệu hiện hành có ngày giờ và nguồn. Bản đã
gửi lưu snapshot của lần trình; cập nhật nguồn sau đó hiện cảnh báo chênh lệch,
không sửa nội dung đã gửi. Người lập được trả lại để sửa rồi gửi phiên bản mới.
Bản đã chốt giữ nguyên cho lần xuất cũ; sửa sai bằng revision có lý do và người
có quyền, công ty tổng hợp dùng phiên bản nào phải lưu rõ dependency đó.

## 6. Quy tắc tính và số liệu tài chính nhập có nguồn

- Mỗi chỉ tiêu có định nghĩa, đơn vị, tiền tệ/cơ sở thuế nếu là tiền, cách lọc
  theo ngày, nguồn/record ID, kỳ, người lập/xác nhận và trạng thái xác minh.
  Thiếu dữ liệu khác 0; số kế hoạch/ước lượng khác số thực hiện được xác nhận.
- Nhập số tổng hợp có chứng từ/tệp hoặc đường dẫn nội bộ được cấp quyền, ngày
  chốt và phạm vi bao phủ. Chưa xác nhận thì gắn nhãn và không trộn vào tổng
  chính thức. Rà soát báo cáo không tự phê duyệt nghiệp vụ/ký/sản lượng/kế toán.
- Một số liệu có nguồn tự động và số nhập ngoài chồng phạm vi thì phải đối
  chiếu/chọn nguồn có thẩm quyền; không cộng cả hai. Nhập tổng phòng và các dòng
  dự án thành phần không cùng đi vào tổng công ty nếu đã chứa nhau.
- Một công việc chung nhiều người là một đầu ra ở tổng phòng/công ty; ghi đóng
  góp từng người riêng, không nhân bản đầu ra/giá trị vì nhiều báo cáo nhắc tới.
- Cùng dự án nhiều bước thiết kế là cùng project ID, phân biệt stage/package;
  xác định rõ đếm dự án hay đếm hồ sơ/gói/bước. Tỷ lệ ước tính giữ nhãn ước tính;
  tổng tiến độ cần trọng số/phạm vi được chốt, không lấy trung bình tùy tiện.
- Kỳ tuần giao tháng phải lọc đúng ngày của dữ kiện; tháng/quý không cộng mù
  các tổng tuần chồng kỳ hoặc cộng lại lũy kế. Chỉ tiêu phát sinh được cộng;
  tồn tại thời điểm (nhân sự, máy trong kho, công nợ) lấy snapshot cuối kỳ.
- Báo cáo chuyển phòng dùng thông tin phòng theo thời điểm/kỳ có bằng chứng
  (HR version nếu có), không để thay phòng hiện tại viết lại báo cáo lịch sử.
  Người mới nhận quản lý/ủy quyền được xem theo scope được cấp, không theo tên.
- Lãnh đạo nhìn đủ trạng thái Có dữ liệu/Chưa có nguồn/Chờ xác nhận; không để
  phòng chưa nộp khiến dashboard trông như không có vướng mắc hoặc kết quả bằng 0.
- Số phải nộp lấy từ danh sách nghĩa vụ báo cáo của kỳ (nhân viên/phòng được
  yêu cầu, miễn/ủy nhiệm/gia hạn có căn cứ), không dùng mọi tài khoản đang active.
  Bản chính mỗi company/loại kỳ/phạm vi/owner chỉ có một hồ sơ, các lần trình
  là phiên bản; chỉnh sửa không làm tăng số người đã nộp hoặc đếm lại kết quả.

## 7. Luồng và quyền đề xuất

Quyền kế hoạch riêng: lập/sửa nháp, phân rã/giao, trình/chốt và điều chỉnh
baseline theo company/phòng/người/phạm vi được cấp; không suy quyền sửa mục
tiêu quý từ quyền nộp báo cáo tuần. Người được giao thấy mục tiêu cha liên
quan đã công bố trong phạm vi phù hợp, không tự thấy toàn bộ mục tiêu hoặc
số tiền của phòng khác. Người giao/chốt ở mỗi cấp còn cần xác nhận mục 12.

State riêng của báo cáo: **Nháp → Đã gửi → Đang rà soát → Đã chốt**;
nhánh **Trả lại có lý do → sửa → gửi lại**. Đây là đề xuất mới, chưa tạo enum;
trước code kiểm pattern/mixin tái sử dụng, không dùng state hợp đồng làm state báo cáo.
Gửi/chốt nguyên tử, kiểm quyền/scope/state/version, chống retry tạo bản trình
trùng, audit actor/thời gian/lý do/nguồn/phiên bản. Không generic RPC ghi state.

| Vai trò logic | Được làm | Phạm vi và giới hạn |
| --- | --- | --- |
| Nhân viên | Lập/sửa nháp, chọn việc có quyền, gửi/nhận trả lại báo cáo của mình | Không xem báo cáo cá nhân người khác hoặc tiền do chỉ có tài khoản |
| Trưởng phòng | Xem báo cáo được gửi trong phòng phụ trách, yêu cầu sửa, lập/tổng hợp/chốt cấp phòng nếu được cấp | Nhiệm kỳ/ủy quyền rõ, có thể kiêm nhiều phòng theo grant; không tự duyệt báo cáo cá nhân của mình |
| Đầu mối tổng hợp | Theo dõi thiếu/trễ, hợp nhất các bản phòng đã chốt, bổ sung tóm tắt | Không tự sửa kết quả cá nhân/bản phòng đã chốt hoặc thấy tiền ngoài quyền |
| Người cung cấp số tài chính | Nhập/chỉnh nháp số được phân công, đính nguồn | Quyền nhập khác quyền xác nhận; người xác nhận được chỉ định, không suy từ chức danh |
| Lãnh đạo | Xem tổng hợp/chi tiết báo cáo được công bố, nhận xét/chỉ đạo/chốt theo quyền | Quyền tài chính/nhân sự nhạy cảm/phòng ban cụ thể độc lập, chưa gán cho tài khoản thật |
| Admin kỹ thuật | Cấu hình mẫu, lịch, vai trò theo quy trình có audit | Không tự được ghi nhận là người duyệt/xác nhận số nghiệp vụ thay người có thẩm quyền |

Đặc tả capability dự kiến: own edit/submit, department read/review/publish,
company consolidate/read/publish, finance input/verify/read, configure.
Không suy quyền từ text chức vụ hoặc tên trên chữ ký Word; cơ chế HEAD hiện
có `tp.kd.department.role` là KH-KD, chưa mặc nhiên cho mọi trưởng phòng toàn
công ty. Cần chọn cách dùng chung có migration/compatibility trước code.

Bản công bố được kiểm audience ở cấp báo cáo, section/field và attachment.
Có quyền đọc báo cáo không tự có quyền mở hồ sơ nguồn. Đầu mối thu thập chỉ đọc
nguồn được phép; thêm phạm vi thu thập phải có capability rõ, không sudo gom
mọi thứ. Không lộ field tài chính qua RPC/HTML/chart/tooltip/export/chatter/files.
Nhận xét cá nhân/HR nhạy cảm tách khỏi báo cáo phòng công bố rộng. Khi thu hồi
quyền/chuyển phòng, server và export kiểm lại; nguồn cache không sống qua logout.

## 8. Kiến trúc kỹ thuật tối thiểu

Đề xuất addon chức năng **`tp_reporting`**, cùng database Odoo, không là một
phòng ban mới. Tên UI **Báo cáo** / **Trung tâm Báo cáo**; reuse shell, HR identity,
SearchModel/filter/export/back hiện có. Chưa tạo addon hoặc schema trong lượt này.

Khung phụ thuộc nền HR/project/mail/tp_core; kết nối nghiệp vụ cụ thể chỉ theo
module thật có, không bắt mọi phòng cài đủ quy trình KH-KD mới nộp được báo cáo.
Không sao chép cả engine R01–R06 hoặc mở framework provider/plugin/ETL mới.

Các model dự kiến, cần rà source và chốt schema trước code:

- Kỳ/lịch/mẫu báo cáo: xác định loại kỳ, phạm vi bắt buộc, deadline và người nhận.
- Mục tiêu/kế hoạch phân rã quý → tháng → tuần: liên kết cha/con, owner/phạm
  vi, tiêu chí/đơn vị/mốc, phân bổ và baseline/revision; liên kết task/nguồn
  hiện có. Không thay nghĩa `tp.periodic.plan` gắn dự án để ép mọi phòng dùng.
- Hồ sơ báo cáo: owner cá nhân/phòng/công ty, company, kỳ, template version,
  author/reviewer/publisher, scope, workflow/version và lần trình liên quan.
- Dòng công việc/kết quả: link `project.task`/project khi có hoặc nội dung
  ngoài dự án, đầu ra/ngày/kết quả/vướng mắc/kỳ tới và nguồn, không tạo việc trùng.
- Chỉ tiêu có nguồn: typed unit/currency/method, nguồn hệ thống hoặc thủ công,
  người xác nhận và evidence; có chống trùng/ngăn overlap khi tổng hợp.
- Lần trình/snapshot, ý kiến/chỉ đạo và nguồn report con: lịch sử append,
  bản chốt bất biến, revision không xóa bản đã công bố.

Nhận xét lãnh đạo có thể chuyển thành `project.task` khi phù hợp project scope;
việc không dự án dùng bản theo dõi hành động tối thiểu. Không ghi bản comment
xong coi như đã giao/đã hoàn thành việc. Có owner/hạn/trạng thái và link báo cáo.

## 9. Giao diện đề xuất

```text
Báo cáo
├─ Tổng quan điều hành          (theo quyền)
├─ Mục tiêu và kế hoạch         (Quý → Tháng → Tuần)
├─ Báo cáo của tôi
├─ Báo cáo phòng ban            (theo quyền)
├─ Báo cáo công ty              (theo quyền)
├─ Việc cần xử lý               (chỉ đạo, vướng mắc, chờ rà)
└─ Cấu hình mẫu và lịch         (admin được cấp)
```

Đây là một layout chung với nội dung/nút theo quyền, không giao diện admin
riêng, không navbar thứ hai. Không biến mỗi phòng hoặc tuần/tháng/quý thành
một menu; dùng bộ chọn kỳ/phòng/người/trạng thái, có lưu điều kiện và Quay lại.

Mục tiêu và kế hoạch có cây quý/tháng/tuần, mở rộng theo quyền để thấy mục
tiêu cha, kế hoạch con, người phụ trách, hạn, phân bổ và thực hiện/chênh lệch.
Thao tác Lập kế hoạch tháng từ mục tiêu quý và Giao việc tuần từ tháng giữ
liên kết sẵn; không bắt nhập lại nội dung mục tiêu. Dashboard có thể đi từ
quý xuống tháng/tuần đến công việc nguồn; chart % chỉ khi có định nghĩa hợp lệ.

Lãnh đạo mở vào tổng quan của kỳ: phòng đã gửi/chưa gửi/quá hạn, kết quả trọng
tâm, mốc bị chậm, vấn đề cần quyết định, chỉ tiêu có nguồn, kế hoạch kế tiếp.
Chart ở trên: cột so sánh kế hoạch-thực hiện khi có cùng đơn vị/nguồn; donut
trạng thái nộp hoặc tình trạng công việc cùng mẫu số; xu hướng chỉ khi đủ dữ
liệu nhiều kỳ. Không dùng % hay animation để làm đẹp dữ liệu chưa có.

Click số/điểm biểu đồ mở đúng bản phòng/dòng công việc có quyền; hiển thị kỳ,
live hay bản chốt, nguồn, thời điểm và mức xác minh. Bảng phòng cho biết ai
chưa nộp nhưng không lộ nội dung nháp/nhân sự nhạy cảm cho mọi người.
Form dùng các section rõ: kết quả, chuyên môn/dự án, vướng mắc, kỳ sau,
kiến nghị, ý kiến và lịch sử. Nhập liệu ngắn, chọn nguồn/link hơn gõ lại.

Light theme, typography/input/bảng/sidebar/hover/motion dùng token hiện tại;
chart rõ ở desktop, mobile đọc/gửi/duyệt được theo quyền và giảm animation
theo reduced-motion. Áp DEC-044 cho mọi bảng/picker/con/export và DEC-046 back.
Prompt CHG-006 giao xuất Excel chi tiết, Word/PDF báo cáo đúng snapshot, có kỳ/phiên
bản/ngày lập/người lập và masking đúng quyền; file Word ký không tự phát sinh.

## 10. Lộ trình thực thi đề xuất

| Giai đoạn | Việc thực hiện | Kết quả nhìn/thao tác được | Cổng tối thiểu |
| --- | --- | --- | --- |
| R0 — Chốt đặc tả | Mục tiêu/chỉ tiêu quý, cách phân rã tháng-tuần, mẫu chung + Thiết kế, lịch, quyền và ca nghiệm thu | Bản đồ mục tiêu–kế hoạch–kết quả/nguồn, quyền/state và UI rõ | Mục 12 làm cấu hình/default test chưa ban hành; mapping/source/AT trước code, không tự cấp policy/người thật |
| R1 — Mục tiêu và kế hoạch | Core chung mọi phòng: lập mục tiêu quý, phân rã tháng, giao tuần; liên kết task/HR, trình/chốt/baseline/revision | Xem được cây quý → tháng → tuần đến người/đầu ra/hạn và phần chưa phân bổ | Quan hệ cha/kỳ/scope hợp lệ, không chia đều/ép %, không đổi baseline trái quyền, không nhân bản task |
| R2 — Báo cáo cá nhân | Chọn kế hoạch tuần đã giao, ghi kết quả/vướng mắc/phát sinh, gửi/trả/sửa/gửi lại; tháng/quý theo yêu cầu | Nhân viên nộp kết quả so với kế hoạch; trưởng phòng có danh sách chờ | Scope cá nhân/company/phòng, đúng kỳ/plan version/state/version/retry, không rò file/tiền |
| R3 — Báo cáo phòng | Tổng hợp tuần lên tháng/quý theo mục tiêu và nguồn; bổ sung chuyên môn, review/chốt; pilot Thiết kế/KH-KD | Trưởng phòng thấy mức đạt kế hoạch, chênh lệch, nguyên nhân, tồn và kỳ sau | Không trùng việc/giá trị/kỳ; so kế hoạch gốc/điều chỉnh; bản cũ bất biến |
| R4 — Báo cáo công ty | Tổng hợp bản phòng và mục tiêu quý công ty; chỉ tiêu ngoài có nguồn/xác nhận; dashboard lãnh đạo/chỉ đạo | Xem đạt mục tiêu quý đến từng tháng/tuần/phòng/người trong quyền và việc cần xử lý | Không cộng lũy kế/chồng kỳ hoặc đề nghị-thực thu; quyền tiền/bản công bố/nguồn đúng |
| R5 — Hoàn thiện và mở rộng | Mẫu chuyên môn còn lại, xuất Excel/Word/PDF kế hoạch-kết quả, lịch nhắc hạn | Các phòng dùng chung luồng, có mẫu riêng và bản báo cáo trình họp | Nghiệm thu mẫu/số; lịch nhắc chỉ tạo khi được giao, không tự mail bên ngoài |

Không định ngày hoàn thành tùy ý khi chưa ước lượng source/schema. Dùng dữ
liệu giả trên DB test tách môi trường theo quy trình dự án khi giao code;
ngoại lệ triển khai trực tiếp main chỉ áp cho task Kho đã có, không tự mở
rộng thành quyền deploy module Báo cáo. Chưa cấp tài khoản/grant người thật
hoặc import hai Word trong lượt thiết kế này. Không commit/push.

## 11. Ca nghiệm thu cần đưa vào prompt thực thi

1. Nhân viên chỉ thấy/lập/sửa/gửi báo cáo của mình trong company hợp lệ.
2. Trưởng phòng được đúng phòng/nhiệm kỳ/ủy nhiệm, không tự duyệt cá nhân mình;
   nhân viên chuyển phòng và vai trò bị thu hồi không giữ quyền cũ.
3. Cá nhân được yêu cầu tháng/quý, không mặc nhiên tất cả phải nộp cả ba kỳ;
   trưởng phòng cá nhân khác hồ sơ đại diện phòng.
4. Một đầu ra nhiều người/đa phòng, dự án nhiều bước, công việc ngoài dự án
   tổng hợp đúng, không nhân bản/mất hoặc cộng chồng tiền.
5. Trả lại thiếu lý do, sai state, stale version, hai reviewer, retry trùng và
   payload khác đều có kết quả đúng; audit/lần trình không bị ghi đè.
6. Tuần giao tháng, quý, múi giờ Asia/Saigon và lũy kế 9 tháng giữ đúng kỳ;
   tồn cuối kỳ khác tổng phát sinh; thiếu nguồn khác 0/không phát sinh.
7. Nháp/lần đã gửi/bản chốt, source thay đổi, revision và report con đổi bản
   không âm thầm sửa báo cáo lịch sử; so sánh nguồn/phiên bản rõ ràng.
8. Nhập tiền ngoài thiếu nguồn/xác nhận, chồng số nguồn tự động, khác tiền tệ/
   cơ sở thuế, người xem không có quyền bị xử lý đúng; không suy tiền thực thu.
9. Quyền tiền và HR kiểm ở RPC/domain/section/chart/tooltip/search/export/
   attachments/chatter; người đọc báo cáo không tự mở được hồ sơ nguồn.
10. Tạo/dùng phiếu, nhận xét/chỉ đạo, xuất báo cáo không tự tạo bút toán,
    BASE approval, chữ ký, effectivity, thanh toán hoặc grant người thật.
11. Desktop/mobile, load/empty/error, nội dung dài/filter/pager/back/unsaved
    guard, xuất đúng kỳ/phiên bản/quyền; mọi bảng có inventory theo DEC-044.
12. Mẫu Thiết kế giữ rõ kết quả kỳ này và việc kỳ sau; số ước lượng/nội dung
    chưa phát sinh không biến thành số đã xác nhận; các nguồn nội bộ được bảo vệ.
13. Tháng truy được mục tiêu quý, tuần truy được tháng/quý; chặn cha khác
    company/kỳ/phạm vi/chu trình. Phân bổ có phần chưa chia/vượt/thiếu rõ;
    định tính không ép thành %, không chia đều tháng/tuần tùy tiện.
14. Kết quả liên kết kế hoạch đúng phiên bản; không ghi đè mục tiêu gốc, việc
    tồn chuyển kỳ không cộng trùng; việc phát sinh có nhãn/lý do và không
    ngầm tăng mức đạt. Người không có quyền không sửa/chốt mục tiêu hoặc kế hoạch.

## 12. Thông tin cấu hình cần chốt trước dùng nghiệp vụ thật

Theo CHG-006, các thiếu dưới đây không ngăn xây core đầy đủ: prompt yêu cầu
làm cấu hình và role/default test tường minh; tuần lịch T2–CN chỉ là mặc định
kỹ thuật test, khác lịch ngày làm việc/deadline. Không coi việc chạy fixture
là công ty đã chốt thẩm quyền/lịch/chỉ tiêu. Bản prompt ghi rõ guard ban hành,
revision, nhập-xác nhận số và quy tắc phạm vi trong khi chờ cấu hình chính thức.

- Người lập/giao/chốt/điều chỉnh mục tiêu quý và kế hoạch tháng/tuần từng cấp;
  tiêu chí đầu ra/trọng số nếu có, cách xử lý phân bổ thiếu/vượt, việc phát
  sinh và chuyển tiếp. Trật tự quý → tháng → tuần đã được người dùng chốt,
  không cần hỏi lại có dùng phân rã hay không.
- Lịch tuần của công ty: T2–T6 hay T2–T7, giờ chốt; hạn nộp cá nhân/phòng,
  deadline tháng/quý, ai được gia hạn. Đề xuất nhãn ngày từ–đến minh bạch;
  chưa cấu hình ngày giờ tùy ý hoặc tạo automation.
- Danh sách người phụ trách/rà/chốt từng phòng, người thay thế, đầu mối tổng
  hợp công ty; lịch sử hiệu lực ủy nhiệm. Tên trên báo cáo chỉ là nguồn tham khảo.
- Tài khoản lãnh đạo nào xem phòng nào/cá nhân nào/tiền và thông tin nhân sự
  nào; người nhập và xác nhận các nhóm tài chính. Không mặc định mọi trưởng
  phòng được xem lương hoặc toàn bộ báo cáo cá nhân ngoài phòng.
- Nhóm chỉ tiêu tài chính đầu tiên, định nghĩa/kỳ/đơn vị/source để đối chiếu;
  mapping project/stage và nguồn công việc của Phòng Thiết kế hiện có hay chưa.
- Mẫu công bố và ưu tiên định dạng thực tế (prompt đã giao Excel/Word/PDF);
  quy tắc sửa bản chốt và ai chốt ở
  mỗi cấp. Tách rõ nhận xét báo cáo với phê duyệt nghiệp vụ gốc.

## 13. Bàn giao lượt phân tích

Source review đọc các file report_center/reporting/periodic_plan/review_document/
scoped_task của `tp_kd_workspace`, project/assignment/HEAD của `tp_project`, HR
scope/role/transfer và dashboard privacy. Đây là đọc source, không audit
runtime/module mới đã chạy. Baseline workflow CHG-20261116-003.

Trích xuất Word chỉ đọc, kiểm hash, lưu private và không nhập DB. Hai câu trả
lời người dùng và bổ sung mục tiêu quý → tháng → tuần ở mục 1 là quyết định
xác nhận; schema/UI/role chi tiết/lộ trình
còn là đề xuất. Source maintained không đổi; cập nhật docs/status/decision/
roadmap/changelog cùng lượt, kiểm link/fence/diff và workflow. Nghiệm thu luồng
Kho CHG-003 vẫn mở riêng, không đóng khi chuyển sang thiết kế Báo cáo.

Bổ sung CHG-006: lưu prompt full module với spec UI từng tab, filter/table/
detail, chart lớn ở đầu và AT/integration/security/export/test/deploy boundary.
Workflow baseline tại lúc viết prompt FAIL do source đổi sẵn sau CHG-005,
chưa có active checkpoint; giữ private boundary và state cũ, không finish hộ
source chưa kiểm. Lượt này chỉ đổi docs; không triển khai reporting hoặc
thay DB/runtime/user/grant. Next: Claude đối chiếu batch hiện hành rồi code
R0–R5 trên canonical test18079; main18069 cần lệnh triển khai riêng.

## 14. As-built CHG-20261116-008 — triển khai native trên test

Ngày 16/11/2026. Mục này mô tả source thực thi, thay phần schema đề xuất khi có khác biệt; không thay quyết định doanh nghiệp trong các mục trên. Main18069 chưa được phép áp. Tài liệu schema/quyền chi tiết: [CORP_REPORT_001_SCHEMA_AND_ACCESS](../security/CORP_REPORT_001_SCHEMA_AND_ACCESS.md).

Addon `tp_reporting` dùng Odoo20 native/OWL trong cùng DB/session/HR/project. Cây `tp.report.plan` quarter→month→week có ban hành, baseline đầu tiên và revision history; `plan_issue` tách quyền đề xuất tuần của nhân viên. `tp.report.document` unique theo company/cấp/đối tượng/kỳ, personal/department/company; `line` là facts có ngày/nguồn/contribution và work_status riêng report state. Đầu ra dự kiến, phần kế hoạch của dòng, actual và unknown/zero là trường riêng, không lấy toàn bộ target cha làm kế hoạch của mọi dòng.

Report gửi tới reviewer active được assignment đúng scope/level/hiệu lực. `snapshot` bất biến lưu exact template/sections/facts/dependency; `review` bất biến gắn snapshot/line/version cho nhận xét, reply và correction, tách published/internal. Return sửa phần nháp hiện hành rồi gửi phiên bản mới; finalize không tự hoàn thành work_status. UI có preview, reason dialog và so sánh hai snapshot; scoped native form gửi optimistic version trước save/action. Raw draft writes của user thường thiếu version bị từ chối; command khóa row/kiểm state/actor/version và idempotency key, sentinel nội bộ không giả được từ JSON.

Tổng hợp phòng/công ty và cá nhân tháng/quý dùng bản eligible, header giao kỳ và facts đúng ngày, khử trùng contribution/date/unit, lưu đúng snapshot ID/version đã dùng. Tuần giao tháng không bị bỏ hoặc cộng nguyên sang hai tháng. Personal month/quarter chỉ khi có obligation/yêu cầu; nghĩa vụ là mẫu số nộp, miễn/gia hạn có lý do, không xóa. Batch existence của submission không đọc private draft chỉ để tính coverage. Plan/task/HR là nguồn ID thật; adapter tài chính tự động chưa được coi là đã tích hợp.

Finance tách `metric/value`, currency/tax/định nghĩa/coverage/source/provider/confirmer/status; không self-confirm, không xác nhận nguồn đã vào snapshot, không đổi định nghĩa đã được dùng trong snapshot. Enter, confirm và full read/export có capability riêng. General snapshot không có tiền; relation finance snapshot đóng chỉ ID và đọc theo quyền hiện hành. File finance phải bound value riêng; report reader không tự có quyền tải minh chứng tiền. Attachment tải lại quyền parent, không token/public bypass, byte/binding của file đã gửi không đổi.

Directive có source snapshot/line, recipient/hạn/result/evidence/version/request identity/history, chuyển task chỉ khi project cho phép. Notification Odoo bus trong ứng dụng dùng thông điệp chung, không gửi email/chat hoặc nội dung internal/tiền. Lịch tạo nghĩa vụ/nhắc là explicit action được scope và `reminders_enabled`; chưa bật cron/policy thật. Mẫu kỹ thuật common/design/business/company có sections và nội dung web; sao chép cấu trúc/carryforward giữ provenance và không mang actual/xác nhận sang kỳ mới.

ACL bản Odoo20 là **ir.access permission + restriction domain**, không ir.rule/ir.model.access. Menu phòng/công ty theo assignment hiện hành; plan ancestors chỉ ban hành và thuộc chuỗi việc đã giao. Superuser vẫn là quyền quản trị kỹ thuật; config user thường bị chặn tự cấp/sửa quyền mình. Assignment/lịch/metric mặc định và fixture đều chưa thành thẩm quyền/nội quy được doanh nghiệp phê duyệt.

Bằng chứng root tại `.local/corp-report001/tests7.log`: 25 tests executed, 0 failed, 0 errors (~6s/2164 queries). Không dùng kết quả này chứng nhận các thay đổi hardening sau tests7; lượt tests8/browser/HTTP/export sẽ ghi ở acceptance khi thực chạy. Kiểm tĩnh Ruff/compile/diff-check không phải nghiệm thu nghiệp vụ. Multi-company, race transaction thực, tải file sau revoke, rollback filestore và hình thức export/browser nhiều viewport cần bằng chứng riêng; không tự đánh PASS từ source.
