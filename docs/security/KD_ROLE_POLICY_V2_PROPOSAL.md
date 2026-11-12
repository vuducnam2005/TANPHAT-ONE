# Đề xuất V2 — Vai trò và quyền phòng Kế hoạch Kinh doanh

## Cập nhật riêng HEAD — KD-HEAD-001, 10/11/2026

DEC-033 và [prompt triển khai](../prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md)
đã cho phép cụ thể hóa **riêng HEAD**: quản lý nghiệp vụ KH-KD toàn phòng, gồm
dữ liệu mới và hồ sơ nhân viên khác. Đã áp dev18069 riêng delta
[ma trận HEAD](KD_ACCESS_002_ROLE_MATRIX.md#kd-head-001--delta-head-đã-xây-dựng-10112026).
**Full211/211 và dev apply/preservation đã đạt**, xem
[acceptance](../demo/KD_HEAD_001_ACCEPTANCE.md); không nhận đây là nghiệm thu
nghiệp vụ/pilot hoặc triển khai toàn V2. Các đề xuất DEPUTY/PROJECT_LEAD/
PLANNING/SUPPORT ở phần lịch sử bên dưới vẫn chờ duyệt và giữ quyền hiện hữu.

- Role `tp.kd.department.role` do vận hành được ủy quyền provision bằng user ID,
  company/phòng, thời hạn và lý do; query/action/file dùng cùng scope động.
  Project phải managed đúng phòng; CRM trước project cần team active đúng
  company/phòng. Hết hạn/thu hồi role mất quyền, không dựa whitelist tám dự án.
- Can thiệp nháp giữ người chịu trách nhiệm, actor thật, thời gian, lý do,
  version và snapshot trước–sau, kể cả tiền ở model được bảo vệ. Task cho HEAD
  cập nhật thay nhưng giữ assignee. Contract dùng business owner riêng;
  không suy owner từ tài khoản kỹ thuật tạo bản ghi.
- Nhận reviewer/phân công là action có audit. Contract giữ reviewer gốc của
  submission và reviewer được giao hiện hành; báo cáo/hộp việc đi theo người
  hiện hành. Không tự review bản mình gửi hoặc bản cùng vòng mình can thiệp;
  chuyển owner không xóa dấu can thiệp. Mở sửa bắt đầu vòng độc lập mới theo
  action hiện có. Typed dossier còn giữ owner khác reviewer.
- File nháp được thêm/lưu trữ có lý do/version/checksum, giữ bytes và audit.
  Căn cứ đã nằm trong lần gửi tiếp tục khóa sau rework; file mới thêm ở nháp
  rework có thể lưu trữ nếu chưa trở thành căn cứ lần gửi. Chặn public/token/
  relink/direct mutation; tài liệu general/financial có guard riêng, chứng chỉ
  không mở dữ liệu HR gốc. CRM thêm/lưu trữ file và trao đổi qua command có audit.
- Người nhận phải có scope/capability hiện hành, backend kiểm lại khi xác nhận;
  chọn owner/reviewer/assignee không cấp thêm grant. Team membership riêng lẻ
  không tự mở quyền nhận CRM trước project. HEAD không quản trị grant/user/group.
- Provisioning delta: ngừng active96dòng cũ của riêng HEAD
  (8assignment/16project grant/72KD grant), thêm1role phòng và1event tạo role,
  journal private giữ trước–sau. Kết quả clone/dev và bảo toàn bốn actor còn lại
  chờ acceptance; không coi con số thiết kế này là bằng chứng dev đã đổi.

BASE/ký/hiệu lực, xác nhận chuyên môn, kế toán/paid, HR nhạy cảm và admin không
được mở từ delta HEAD. Quyền điều phối nghiệp vụ không là quyền cấp bảo mật.
Phần dưới giữ nguyên đề xuất và test/căn cứ lịch sử; câu “chưa viết prompt/chưa
duyệt” của V2 không phủ định ủy quyền triển khai riêng HEAD đã ghi ở đây.

## Baseline đề xuất V2 ngày09/11/2026

Ngày09/11/2026. **`PROPOSED_PENDING_USER_APPROVAL`**.
CHG-20261109-005 là batch tài liệu, chưa thay quyền hoặc ứng dụng.
Người dùng yêu cầu trình bày lại toàn bộ quyền để duyệt trước khi viết prompt
triển khai; tài liệu này không phải prompt, lệnh cấp quyền hoặc quyết định đã duyệt.

## 1. Căn cứ và giới hạn

- S01: quy trình nghiệp vụ công ty; S02: phân công Ban KD tháng04/2026.
  Đã đọc lại bản trích S02 tại `.local/biz-001/S02.txt`, đối chiếu
  [registry nguồn và E01–E18](../architecture/TP_KD_EVIDENCE_AND_ACCEPTANCE.md).
  NAS không truy cập được tại lượt này; không nhận bản trích là văn bản nhân sự
  còn hiệu lực hiện tại hoặc tự xác nhận quyền ký từ mô tả chủ trì ký kết.
- [Workflow KD mục1,2,7](../architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md):
  KD_HEAD dự kiến có contract draft/submit và financial draft edit; preset dev
  hiện hạn chế hơn. Đây là chênh giữa thiết kế và cấu hình đã triển khai.
- DEC-013/014/017/029/030/031 trong [sổ quyết định](../DECISIONS.md): BASE duyệt
  chính thức giai đoạn đầu; tiền theo scope; TADIC/TACICO cùng pháp nhân; native
  Odoo và ưu tiên KH-KD. Mẫu vai trò không thay assignment/grant cụ thể.
- [Ma trận runtime cũ](KD_ACCESS_002_ROLE_MATRIX.md) và
  [audit004](../reviews/KD_ACCESS_002_INDEPENDENT_AUDIT.md) là hiện trạng;
  V2 chỉ thay baseline dự kiến khi được người dùng duyệt đúng phạm vi.
  F1–F3 vẫn mở, Project/WBS scoped write chưa triển khai.
- Không sao chép danh tính/credential vào tài liệu Git. Vai trò dưới đây dùng
  mã chức năng, mapping tài khoản cá nhân giữ tại kho private hiện có.

## 2. Mẫu vai trò

| Mã | Vai trò | Trách nhiệm chính và phạm vi đề xuất |
| --- | --- | --- |
| KD_HEAD | Trưởng Ban Kinh doanh | Điều hành mọi nghiệp vụ KH-KD trong công ty/đơn vị được giao; toàn bộ dự án thuộc Ban, kể cả dự án mới được tiếp nhận đúng phạm vi |
| KD_DEPUTY | Phó phòng kiêm chủ trì | Điều phối và xử lý dự án được giao; đọc báo cáo hợp đồng/khoán toàn Ban để làm nhiệm vụ tổng hợp; nhiệm vụ khác toàn Ban cần ủy nhiệm |
| KD_PROJECT_LEAD | Chủ trì dự án | Chủ trì xuyên suốt cơ hội–hợp đồng–kế hoạch–khoán–nghiệm thu–đề nghị thanh toán của dự án được giao |
| KD_PLANNING | Dự toán và kế hoạch | Lập dự toán/đề xuất tài chính, kế hoạch, phiếu giao việc, hồ sơ năng lực và phối hợp hồ sơ; có thể kiêm chủ trì dự án khi được phân công riêng |
| KD_SUPPORT | Hỗ trợ hồ sơ | Pháp lý/năng lực/chứng chỉ, cập nhật dữ liệu và tài liệu được giao; hỗ trợ từng phần dự toán/thanh toán/thầu phụ, không tự thành chủ trì |

Đây là phạm vi động theo tổ chức và phân công được phê duyệt, không khóa vào
8/4/4/4/2 dự án giả của dev. Cùng chức danh không tự có cùng quyền nếu phạm vi
được giao khác nhau. Bổ nhiệm/kiêm nhiệm phải được cấp rõ, có ngày hiệu lực.

## 3. Nguyên tắc áp dụng chung

1. Tách xem, tạo, sửa nháp, gửi, rà soát, phân công, xuất, nhập và loại bỏ hồ sơ.
   Đọc dự án không kéo theo quyền tiền, giấy tờ nhân sự hoặc quản trị tài khoản.
2. Mỗi hồ sơ/task có một người chịu trách nhiệm. Người tạo, người phối hợp,
   người sửa, reviewer và người quyết định bên ngoài được ghi riêng.
3. Đề xuất trưởng ban được can thiệp nháp trong toàn Ban bằng thao tác có lý do,
   lưu version/người sửa/thông báo, không âm thầm đổi owner hoặc dữ liệu của nhân viên.
   Deputy/lead xử lý hồ sơ trong phạm vi họ chủ trì; support/planning chỉ sửa
   trường và phần việc được giao. Chức danh không mở quyền toàn bản ghi qua mọi field.
4. Khi đã gửi rà soát, dùng trả lại/mở lại sửa theo workflow. Bản đã ký, hiệu lực,
   nghiệm thu hoặc chốt phải có revision/correction và căn cứ; không sửa đè/xóa.
5. Đề xuất người lập hoặc người sửa nội dung không tự xác nhận kết quả rà soát
   của chính phiên bản đó. Trưởng ban lập/sửa thì deputy đủ năng lực hoặc lãnh
   đạo/người được chỉ định rà soát. Rà soát tài chính/kỹ thuật vẫn đúng chuyên môn.
   Đây là kiểm soát đề xuất, chưa khẳng định công ty đã ban hành quy tắc bốn mắt.
6. Tiền đọc, tiền sửa và tiền xuất là ba quyền độc lập. Tiền nháp chỉ sửa trong
   đúng nghiệp vụ được lập; không sửa giá trị bản đã ký hoặc số kế toán thực tế.
7. File/chatter/dashboard/report/search/export/preview/download cùng phạm vi
   dữ liệu. Không tự phân loại nội dung bằng từ khóa và coi là đã hết dữ liệu nhạy cảm.
8. Quyền tự hết hạn/thu hồi khi đổi phân công; không giữ quyền tiền cũ chỉ vì đã
   xem hồ sơ. Hệ thống kiểm lại ở backend và không để cache trả dữ liệu sai scope.

## 4. Ma trận A — Xem dữ liệu và báo cáo

Toàn Ban ở bảng này chỉ là KH-KD được giao trong cùng công ty, không phải mọi
phòng ban hoặc công ty khác. Chỉ mục/báo cáo không cho drill xuống nội dung chưa được cấp.

| Nội dung | HEAD | DEPUTY | PROJECT_LEAD | PLANNING | SUPPORT |
| --- | --- | --- | --- | --- | --- |
| Dashboard/metadata công việc KH-KD | Toàn Ban | Toàn Ban để điều phối/tổng hợp | Dự án được giao | Dự án/task được giao | Công việc/hồ sơ được giao |
| CRM gắn dự án | Toàn Ban | Được giao; danh mục chung phục vụ điều phối | Dự án được giao | Hồ sơ được giao | Phần thông tin chung được giao |
| CRM chưa có dự án | Toàn Ban | Owner/collaborator/team được phân công | Owner/collaborator được giao | Hồ sơ được giao | Phần hồ sơ chung được giao |
| Hợp đồng/phụ lục, khoán — nội dung chung | Toàn Ban | Toàn Ban phục vụ báo cáo | Dự án được giao | Phần cần cho công việc | Metadata/phần được giao |
| Giá trị và báo cáo hợp đồng/khoán | Toàn Ban | Đọc số liệu/báo cáo hợp đồng và khoán toàn Ban; không tự sửa ngoài scope | Dự án được giao quản trị | Giá/dự toán/ngân sách của việc được giao; toàn dự án chỉ khi kiêm chủ trì | Không mặc định |
| Chi tiết tiền nghiệm thu/request/công nợ | Toàn Ban trong phạm vi quản trị KH-KD | Dự án trực tiếp chủ trì hoặc ủy nhiệm; không tự kéo từ quyền báo cáo hợp đồng/khoán | Dự án được giao quản trị | Chỉ phần việc có cấp quyền tiền riêng | Không mặc định |
| Hồ sơ năng lực công ty đã phát hành | Theo quyền tài liệu | Theo công việc | Theo dự án/gói thầu | Theo công việc | Được giao chuẩn bị/phát hành đúng bộ |
| Bộ năng lực tài chính dùng dự thầu | Đọc bản được cấp | Đúng hồ sơ dự thầu | Đúng dự án/gói thầu | Được giao chuẩn bị | Được cấp đúng bộ tài liệu, mục đích và thời hạn |
| Chứng chỉ/hồ sơ nhân sự dùng dự thầu | Bản nghiệp vụ cần dùng | Đúng dự án | Đúng dự án | Được giao chuẩn bị | Chứng chỉ và dữ liệu phục vụ hồ sơ được giao |
| Lương/tài khoản ngân hàng/giấy tờ HR gốc | Không từ vai trò KH-KD | Không | Không | Không | Không |

Quyền đọc số liệu toàn Ban cho deputy là đề xuất rõ để đáp ứng trách nhiệm
tổng hợp hợp đồng/khoán trong S02; không mặc định toàn bộ tài chính công ty.
Nếu triển khai phân biệt quyền đọc báo cáo và đọc bản ghi, phải đảm bảo query,
drill, export và file đúng policy; không dùng group đọc tiền toàn hệ thống để thay thế.

## 5. Ma trận B — Tạo, sửa nháp, gửi hồ sơ

`Đủ` = tạo, sửa nháp, gửi rà soát/khai báo theo workflow đúng nghiệp vụ; không
phải duyệt chính thức. Mọi ô có điều kiện theo scope ở mục4 và field được giao.

| Nghiệp vụ | HEAD | DEPUTY | PROJECT_LEAD | PLANNING | SUPPORT |
| --- | --- | --- | --- | --- | --- |
| Khách hàng/liên hệ | Tạo và quản lý thông tin KD; sửa master dùng chung qua người phụ trách dữ liệu | Tạo/cập nhật thông tin KD đúng scope | Tạo/cập nhật liên hệ của hồ sơ mình | Nhập phần được giao | Nhập phần được giao, không gộp/xóa đối tác chung |
| Cơ hội, khảo sát nhu cầu, checklist thầu | Đủ toàn Ban | Đủ phần chủ trì | Đủ phần được giao | Lập/sửa phần dự toán/kế hoạch/năng lực | Lập/sửa phần pháp lý/năng lực/checklist được giao |
| Giá dự thầu/dự toán | Đủ toàn Ban, nháp | Đủ dự án chủ trì | Đủ dự án chủ trì, có dữ liệu chuyên môn phối hợp | Lập/sửa/gửi phần dự toán được giao | Hỗ trợ phần được giao, tiền cần cấp riêng |
| Khai báo hồ sơ thầu đã nộp/kết quả bên ngoài | Thực hiện trong Ban, có bằng chứng | Hồ sơ chủ trì | Hồ sơ chủ trì | Chỉ khi được giao đầu mối nộp | Chỉ hoàn tất phần chuẩn bị, không tự khai báo kết quả cuối |
| Hợp đồng/phụ lục | Đủ toàn Ban | Đủ dự án chủ trì | Đủ dự án chủ trì | Góp dự toán/điều khoản được giao; Đủ khi kiêm chủ trì | Nhập metadata/tập hợp file nháp được giao, không sửa điều khoản/giá trị chủ đạo hoặc gửi thay owner |
| Kế hoạch sản lượng/doanh thu | Đủ toàn Ban | Tổng hợp và lập phần được giao | Dự án chủ trì | Lập/sửa/gửi kế hoạch được giao | Cập nhật dữ liệu đầu vào được giao |
| Giao khoán/thầu phụ | Đủ toàn Ban | Đủ dự án chủ trì | Đủ dự án chủ trì | Chuẩn bị khối lượng/dự toán/phiếu giao theo giao việc | Tập hợp hồ sơ/nhập phần được giao |
| Sản lượng/theo dõi tiến độ | Điều phối và kiểm tra toàn Ban | Dự án chủ trì | Dự án chủ trì | Chuẩn bị/tổng hợp được giao | Cập nhật đầu vào có nguồn |
| Hồ sơ nghiệm thu | Đủ về hồ sơ quản trị; không thay xác nhận kỹ thuật | Đủ dự án chủ trì | Đủ dự án chủ trì | Soạn/đối chiếu phần được giao; không gửi cuối nếu chưa là owner | Tập hợp biên bản/tài liệu được giao |
| Đề nghị tạm ứng/thanh toán | Đủ phần hồ sơ KH-KD | Đủ dự án chủ trì | Đủ dự án chủ trì | Chuẩn bị/đối chiếu phần được giao; không tự đánh dấu tiền đã trả | Tập hợp chứng từ theo task; tiền cần cấp riêng |
| Hồ sơ năng lực/pháp lý/chứng chỉ | Quản lý, rà soát bản phát hành | Lập/gửi phần được giao | Lập/gửi phần được giao | Lập/gửi phần được giao | Tạo/cập nhật nháp/gửi rà soát đúng bộ; không tự xác nhận chứng chỉ hợp lệ hoặc công bố bản cuối |
| Nghĩa vụ/thời hạn hợp đồng, thanh lý | Quản lý phần hồ sơ toàn Ban | Dự án chủ trì | Dự án chủ trì | Theo dõi lịch và phần được giao | Nhắc hạn/tập hợp tài liệu; không xác nhận nghĩa vụ tiền đã hết |

Planning/support được gửi phần việc của mình để reviewer xử lý. Điều này khác
gửi toàn bộ hợp đồng/request hoặc khai báo đã nộp thầu. Không tạo state chung
mới chỉ để hiện nút gửi; mapping action thực tế phải đặc tả trước từng slice.

## 6. Ma trận C — Dự án, WBS và phân công

| Thao tác | HEAD | DEPUTY | PROJECT_LEAD | PLANNING | SUPPORT |
| --- | --- | --- | --- | --- | --- |
| Tạo dự án | Tạo dự án thuộc Ban, đúng đơn vị và mã | Lập hồ sơ dự án mới, gửi trưởng ban xác nhận scope/owner | Đề xuất mở dự án | Chuẩn bị dữ liệu | Nhập thông tin đề xuất được giao |
| Sửa thông tin dự án | Toàn Ban, có lịch sử | Dự án chủ trì; không tự đổi company/đơn vị | Dự án chủ trì, trường quản trị cho phép | Trường kế hoạch được giao | Trường mô tả được giao |
| Tạo/cấu trúc WBS | Toàn Ban | Dự án chủ trì | Dự án chủ trì | Soạn kế hoạch/WBS phần được giao | Không đổi cấu trúc |
| Giao task/đổi người phụ trách | Trong Ban; đề nghị phối hợp phòng khác | Thành viên dự án chủ trì | Thành viên dự án chủ trì | Soạn phiếu giao; phát hành khi được giao điều phối cụ thể | Không giao lại người khác; cập nhật task mình |
| Thay baseline tiến độ/phạm vi | Quyết định nội bộ theo căn cứ, giữ bản trước | Đề xuất và thực hiện khi được giao | Đề xuất và thực hiện khi được giao | Chuẩn bị đề xuất thay đổi | Không |
| Đổi chủ trì/phân công dự án | Quyết định trong scope Ban | Đề nghị; quyết định thay khi có ủy nhiệm có hạn | Đề nghị bàn giao | Đề nghị | Đề nghị |
| Lưu trữ/đóng hồ sơ quản trị dự án | Có căn cứ, chỉ rõ nghĩa vụ tồn | Đề nghị | Đề nghị | Chuẩn bị đối chiếu | Tập hợp tài liệu |

Phân công người ngoài Ban là đề nghị/phối hợp với đơn vị nhận, không tự cấp
quyền HR hoặc quản lý công việc toàn phòng khác. Giao việc Odoo giai đoạn đầu
giữ tham chiếu BASE nếu đó là nơi giao việc chính thức. Tạo WBS không tự xác
nhận phần trăm kỹ thuật thực tế, chất lượng hoặc nghiệm thu chuyên môn.

## 7. Rà soát, sửa sai và loại bỏ

- HEAD rà soát thương mại/quản trị KH-KD toàn Ban khi được chọn reviewer;
  không tự thay review tài chính QT-TC hoặc kiểm tra kỹ thuật của phòng chuyên môn.
- DEPUTY là reviewer thay thế hoặc reviewer trong phạm vi phân công; LEAD có
  thể review nghiệp vụ dự án khi được chỉ định và không tự review bản mình lập/sửa.
- PLANNING review dự toán/kế hoạch theo năng lực được giao; không tự có review
  mọi hợp đồng. SUPPORT được kiểm checklist/đề nghị bổ sung, không kết luận cuối.
- Return phải có lý do. Sửa bản đã gửi phải qua trả lại/mở sửa; action hiện chưa
  có thì ghi gap, không tự viết state hoặc mở nút để bỏ qua workflow.
- Đề xuất ưu tiên hủy/lưu trữ nháp có lý do. Xóa vĩnh viễn chỉ bản tạo nhầm,
  chưa gửi/chưa tham chiếu/chưa dùng báo cáo và đúng quyền; lịch sử audit vẫn giữ.
  HEAD xử lý trong Ban; người khác chỉ đề nghị/loại nháp thuộc nghiệp vụ mình
  được giao nếu model cho phép. Không xóa hợp đồng/khoán/chứng từ đã chốt.
- Sửa sau ký/hiệu lực: lập đề nghị/phụ lục/revision, giữ bản gốc; quản trị KH-KD
  không tự xác nhận thẩm quyền ký hoặc hiệu lực pháp lý của thay đổi.

## 8. Tài liệu, tiền, trao đổi, nhập và xuất

- Hồ sơ chung: được đọc/tải/tạo nháp/trao đổi đúng hồ sơ hoặc bộ tài liệu được giao.
- Hồ sơ tài chính dự án: cần quyền đọc tiền phù hợp đến đúng domain/hồ sơ;
  quyền sửa và phát hành tách riêng. Chatter về tiền kế thừa hạn chế của nội dung.
- Bộ năng lực tài chính doanh nghiệp để dự thầu: bản phát hành được duyệt từ
  chủ tài liệu; người hỗ trợ có thể nhận quyền đọc/tải đúng bộ để làm thầu.
  Đây là cấp quyền tài liệu hữu hạn, không mở số tiền/công nợ của mọi dự án.
- Chứng chỉ nhân sự: chỉ dữ liệu chuyên môn cần cho thầu. Hồ sơ HR gốc, lương,
  giấy tờ cá nhân không thuộc phạm vi mặc định kể cả HEAD.
- Trao đổi chung và trao đổi tài chính phải thể hiện phạm vi. Không có thiết kế
  phân loại/guard thì chưa mở cộng tác tài chính; không dùng quét từ khóa để cam kết an toàn.
- Upload/download/preview/thumbnail/đường dẫn cũ phải kiểm cùng quyền; chia sẻ
  public không phải quyền mặc định. Phát hành ngoài công ty cần bước riêng có lưu vết.
- Xuất: HEAD toàn dữ liệu KH-KD được cấp; DEPUTY báo cáo hợp đồng/khoán toàn Ban
  và hồ sơ dự án chủ trì; LEAD dự án mình; PLANNING đúng bảng được giao;
  SUPPORT metadata và bộ tài liệu đã được cho phát hành. Không kéo field tiền/HR
  ngoài scope trong export/report/search/audit.
- Nhập Excel hàng loạt: quyền riêng theo mẫu/domain, staging/kiểm trùng/sai scope
  trước ghi. HEAD chấp thuận lô; deputy/lead/planning chỉ chạy trong quyền ghi
  được giao, support chuẩn bị file. Không được dùng import để ghi state/amount
  hoặc master data vượt quyền. Chức năng import chưa có phải triển khai riêng.

## 9. BASE, chữ ký, tài chính thực tế và cấp quyền

| Việc | Đề xuất trách nhiệm |
| --- | --- |
| Chuẩn bị hồ sơ trình BASE | Owner, người phối hợp được giao; HEAD điều phối |
| Ghi link/kết quả được khai báo từ BASE | Owner hoặc người ghi nhận được chỉ định đúng scope; không chuyển thành verified |
| Đối chiếu bằng chứng BASE | Người được chỉ định, đề xuất khác người nhập đối với bước cần chốt; QT-TC tham gia phần tài chính |
| Duyệt BASE/ký/hiệu lực pháp lý | Chưa gán cho cả5preset; cần văn bản và quyền trên hệ thống nguồn |
| Ghi nhận bản ký/hiệu lực/đóng nghĩa vụ | Action chuyên biệt sau căn cứ thẩm quyền; không tự mở từ preset HEAD |
| Hóa đơn, hạch toán, thanh toán thực tế, đối chiếu ngân hàng | QT-TC/Kế toán và người được ủy quyền; KH-KD chuẩn bị/đọc trạng thái đúng scope |
| Quyết định phân công và quyền KH-KD tiêu chuẩn | HEAD trong Ban; không tự cấp quyền tiền/nhạy cảm mới cho chính mình; deputy thay khi có ủy nhiệm |
| Quyết định quyền tài chính/HR ngoài Ban, ngoại lệ hoặc quyền cho HEAD | Chủ dữ liệu/lãnh đạo được ủy quyền quyết định, không do HEAD tự mở |
| Thực hiện cấp/thu hồi quyền | Quản trị thực hiện theo quyết định đã lưu; sau này có thể dùng action scoped cho preset chuẩn đã duyệt |
| Tài khoản hệ thống | Admin tạo/khóa/reset, quản lý phân quyền kỹ thuật; KH-KD đề nghị, không truy cập Settings để tự sửa group |

Mỗi quyền ghi user/role, company/đơn vị/project/hồ sơ, capability, người quyết
định/thực hiện, lý do, ngày bắt đầu/kết thúc và audit. Không sao chép toàn bộ
quyền khi đổi nhân viên. Owner/reviewer/ủy nhiệm cũ phải xử lý khi bàn giao.
Mọi người chỉ sửa tùy chọn cá nhân được Odoo cho phép; không xem mật khẩu của
người khác, không tự bật quyền quản trị hoặc thay chính sách đăng nhập công ty.

## 10. Ví dụ mong đợi sau khi triển khai được nghiệm thu

1. HEAD mở toàn KH-KD và tạo nháp hợp đồng; người khác phù hợp rà soát. HEAD
   sửa nháp nhân viên có lý do/lịch sử; không sửa đè bản đã gửi hoặc đã ký.
2. DEPUTY tổng hợp số hợp đồng/khoán toàn Ban, nhưng không sửa dự án khác chỉ
   vì báo cáo nhìn được số liệu; chi tiết tiền request ngoài scope vẫn bị chặn.
3. LEAD theo dõi dự án mình từ cơ hội đến request; không tự xác nhận tiền đã về.
4. PLANNING lập dự toán/kế hoạch; khi được giao làm chủ trì thì nhận quyền
   bổ sung đúng dự án, không phải cấp role chủ trì cho tất cả dự án đang xem.
5. SUPPORT chuẩn bị hồ sơ pháp lý/chứng chỉ/bộ năng lực tài chính được phát hành;
   không vì được giao một file mà xem mọi giá trị hợp đồng hoặc lương nhân viên.

## 11. Các điểm người dùng duyệt ở bước này

- HEAD quản lý nghiệp vụ toàn Ban, gồm lập/sửa nháp và can thiệp nháp có lưu vết.
- DEPUTY đọc số liệu hợp đồng/khoán toàn Ban để tổng hợp; ghi ngoài scope cần giao thêm.
- PLANNING có quyền chuyên môn và có thể kiêm chủ trì theo từng dự án.
- SUPPORT làm hồ sơ theo phần việc, được nhận bộ tài liệu nhạy cảm hữu hạn khi cần.
- Người lập/sửa không tự kết luận review cùng phiên bản; draft/final/BASE/kế toán tách biệt.
- HEAD quyết định phân công/quyền chuẩn trong Ban; IT thao tác, ngoại lệ/ngoài Ban cần chủ dữ liệu.

User duyệt thiết kế V2 chưa có nghĩa văn bản ủy quyền ký/hạn mức đã được cung cấp,
Q2 doanh nghiệp/pilot đã nghiệm thu hoặc quyền đã áp dev. Không viết prompt
triển khai V2 cho tới khi user duyệt; prompt correction F1–F3 đã có là việc
sửa lỗi cũ riêng. Sau duyệt cần map từng capability/field/action với source,
chốt acceptance test và triển khai từng nhóm trên test trước khi áp dev.
