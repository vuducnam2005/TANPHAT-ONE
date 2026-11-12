# KH-KD — Phân tích yêu cầu sau cuộc họp ngày 09/11/2026

Task **KD-BIZ-REFINE-001**, batch **CHG-20261109-007**.
Trạng thái **MEETING_REQUIREMENTS_CAPTURED_DESIGN_PROPOSED**.
Đây là phân tích/hướng triển khai; chưa sửa ứng dụng/database, chưa duyệt schema,
trạng thái, quyền hoặc áp dev. Nội dung cuộc họp do người dùng thuật lại.

**Cập nhật tiếp CHG-20261109-008:** người dùng đã yêu cầu tách riêng hai khu
vực Quản lý dự án/Quản trị dự án và viết prompt hoàn thiện các ý sau họp.
Xem DEC-032 và [prompt triển khai](../prompts/CLAUDE_KD_PROJECT_RESTRUCTURE_001.md).
Nội dung phân tích ban đầu dưới đây giữ nguồn gốc; danh mục state/model và
quyền người thật chưa tự chuyển thành quyết định đã duyệt hoặc code đã chạy.

## 1. Yêu cầu được ghi nhận

1. Thay cách gọi cơ hội thành dự án.
2. Bỏ nhãn khách hàng, giữ chủ đầu tư.
3. Tình trạng hồ sơ đổi thành tình trạng dự án ở màn đang thảo luận.
4. Người phụ trách đứng trước hạn chuẩn bị/nộp.
5. Tình trạng có ghi chú/bình luận tùy chỉnh.
6. Thêm cột đối tác.
7. Thêm dự kiến giá trị gói thầu.
8. Thêm Đấu thầu trong Kinh doanh và dự án.
9. Phân biệt quản lý dự án và quản trị dự án.

Người dùng đã làm rõ trực tiếp: ý4 chỉ **đổi thứ tự cột**, không yêu cầu tách
hai hạn; đối tác **có nhiều loại, cần ghi rõ vai trò từng bên**.
Danh mục trạng thái, định nghĩa tiền, model mới và cách gọi quản lý/quản trị
ở phần dưới là đề xuất, không nhận là quyết định đã duyệt của lãnh đạo.

## 2. Hiện trạng đối chiếu source

| Đang có | Ý nghĩa và khoảng cách |
| --- | --- |
| `crm.lead`, `kd_route`, `tp_project_id` | Đang ghép theo dõi cơ hội và chuẩn bị/nộp thầu; có liên kết TP Project |
| `project.project` mở rộng `tp_project` | Có mã/phòng chủ trì/assignment, chưa có lifecycle KH-KD riêng được chốt; ghi managed project còn giới hạn manager |
| `kd_bid_state` | Tìm hiểu, chuẩn bị, khai báo nộp chưa xác minh; không phải lifecycle dự án hoặc kết quả thầu |
| `user_id`, `kd_deadline` | Có sẵn, list đang đặt hạn trước người phụ trách; deadline hiện là Date |
| `partner_id` | UI Khách hàng / chủ đầu tư; bridge bắt CRM và Project cùng commercial partner |
| `expected_revenue` | Giá trị CRM có guard tiền; chưa đủ căn cứ gọi là tổng giá trị gói thầu |
| `res.partner` | Tái sử dụng danh bạ; thiếu quan hệ các bên tham gia theo vai trò/project/gói |
| Source/scope/checklist/receipt/chatter | Không thay được nhật ký tình trạng; submitted khóa căn cứ, file/chatter còn finding F1–F3 |

Source: `custom_addons/tp_kd_workspace/models/workspace.py`,
`models/opportunity_access.py`, `views/workspace.xml`,
`custom_addons/tp_crm_project_bridge/models/crm_lead.py`,
`custom_addons/tp_project/models/project_project.py`.
Căn cứ: [tổng hợp nghiệp vụ](TP_KD_BUSINESS_RECAP_AND_GAPS.md),
[workflow/quyền](TP_KD_WORKFLOW_AND_PERMISSIONS.md),
[registry nguồn](TP_KD_EVIDENCE_AND_ACCEPTANCE.md).
Không đọc lại NAS trong lượt này hoặc xác nhận văn bản nhân sự cũ còn hiệu lực.

## 3. Tổ chức dữ liệu và menu đề xuất

Lấy **Dự án** làm hồ sơ nhận diện dùng chung từ lúc tiếp cận. Không tạo dự án
thứ hai khi trúng thầu/triển khai. Mở hồ sơ sớm không tự tạo hợp đồng, quyền
tiền, quyết định tham gia thầu hoặc kế hoạch thi công/thực hiện.

```text
Dự án — một mã/ID dùng chung
├── Chủ đầu tư và các bên tham gia theo vai trò
├── Gói thầu A → các lần tham gia/nộp và kết quả có căn cứ
├── Gói thầu B → các lần tham gia/nộp và kết quả có căn cứ
└── Hợp đồng/phụ lục → WBS → giao khoán → sản lượng
    → nghiệm thu → đề nghị thanh toán/đối chiếu QT-TC
```

Nhánh giao trực tiếp không cần gói thầu giả. Gói trượt/dừng không tự kết thúc
các gói khác hoặc cả dự án. Hợp đồng vẫn có scope/quan hệ riêng; sơ đồ trên
không áp đặt một gói chỉ có đúng một hợp đồng.

Menu Kinh doanh và dự án: **Dự án** và **Đấu thầu**. Hồ sơ dự án hiện có trở
thành chi tiết của danh mục Dự án, không để hai danh mục trùng ý nghĩa.
Giữ nhóm Hợp đồng/triển khai/Sản lượng/Thanh toán cùng liên kết project chung.
Tái sử dụng `project.project`, `res.partner`, `tp_contract` và bridge hiện có.

Chưa chốt model/addon gói thầu mới. Đặc tả cần xác định `crm.lead` đại diện hồ
sơ kinh doanh, gói hay lần tham gia; giữ ID/lịch sử cho tới khi mapping rõ.
Không đổi nhãn toàn CRM rồi coi CRM và Project tự trở thành một thực thể.

## 4. Chi tiết thiết kế đề xuất

### Nhãn, cột và hạn

- Màn Dự án: Mã | Tên dự án | Chủ đầu tư | Đối tác | Người phụ trách |
  Tình trạng dự án | Ghi chú. Hạn/giá gói có trong phần các gói liên quan;
  nếu tổng hợp lên project phải chỉ rõ gói hoặc mốc gần nhất.
- Màn Đấu thầu: Mã/tên gói | Dự án | Chủ đầu tư | Đối tác | Người phụ trách |
  Hạn chuẩn bị / nộp | Tình trạng dự thầu | Dự kiến giá trị gói | Ghi chú.
- Người phụ trách đứng trước hạn theo xác nhận. Chưa tách hai deadline;
  nếu cần giờ/phút nộp thì chốt độ chính xác/múi giờ riêng.
- Giữ bộ lọc, phân trang, tùy chọn cột và badge màu; tiền theo quyền. Nội dung
  dài xem trong chi tiết, không buộc bảng phải hiển thị tất cả cột cùng lúc.

### Ba loại trạng thái và ghi chú

| Loại | Trả lời câu hỏi | Ví dụ đề xuất, chưa chốt |
| --- | --- | --- |
| Tình trạng dự án | Đang theo dõi hay thực hiện dự án? | Đang theo dõi, đang thực hiện, tạm dừng, kết thúc |
| Tình trạng dự thầu | Gói/lần tham gia đang ở đâu? | Đánh giá, chuẩn bị, đã nộp/chờ kết quả, có kết quả, dừng |
| Rà soát hồ sơ | Lập/rà soát hồ sơ tới đâu? | Nháp, đang rà soát, bị trả lại theo model hiện có |

Không đổi `kd_bid_state` thành lifecycle dự án bằng nhãn dịch. Không coi
submitted hiện có là nộp đã xác minh, trúng thầu, ký hoặc hiệu lực. Kết quả
thầu cần tách trúng/trượt/hủy/không tham gia, có căn cứ và actor được phép ghi.

Đề xuất nút **Cập nhật tình trạng** và **Thêm ghi chú** trong chi tiết. Người
có quyền chọn trạng thái chuẩn, nhập diễn biến; lưu actor, thời gian, trước/sau,
căn cứ và version. Ghi chú sau nộp là sự kiện mới, không sửa căn cứ bản đã nộp.
Chữ tự do bổ sung cho trạng thái để vẫn lọc/tổng hợp được. Cấu hình danh mục
trạng thái là quyền riêng, không cho mọi người tự thêm/xóa state workflow.
Quyền note không tự cấp quyền submit/review/đổi state/tiền. Nhật ký/file/
chatter cần cùng policy đọc/ghi/đính kèm; không dùng comment làm kênh lộ tiền.
Không mở lại chatter CRM rộng trước khi correction F1–F3 được kiểm chứng.

### Chủ đầu tư và các đối tác

Dùng nhãn Chủ đầu tư ở KH-KD nhưng không đổi nghĩa khách hàng toàn Odoo.
Phân biệt chủ đầu tư, bên mời thầu, tổng thầu/bên ký trực tiếp, thành viên/chủ
trì liên danh, đơn vị phối hợp và thầu phụ. Danh mục vai trò cụ thể còn là đề xuất.
Tái sử dụng `res.partner`, thêm quan hệ vai trò theo project/gói; một bên có
thể nhiều vai, nhiều bên cùng vai, không nhập chuỗi tên rời hoặc tạo trùng danh bạ.

Ví dụ làm thầu phụ: Chủ đầu tư=A, bên ký trực tiếp/tổng thầu=B. Bridge hiện
bắt CRM/project cùng commercial partner nên không chỉ đổi chữ rồi coi dữ liệu
đúng. Cần mapping field bên nào, rà constraint/guard và giữ counterparty hợp
đồng. Dữ liệu cũ chưa rõ vai để cần đối chiếu, không tự nhận là chủ đầu tư.
Cột Đối tác tóm tắt tên kèm vai trò, mở chi tiết các bên và phạm vi tham gia.

### Dự kiến giá trị gói thầu

Tách tổng dự kiến giá gói, giá công ty chào, phần việc công ty dự kiến nhận,
và giá hợp đồng đã ký. Không dùng `expected_revenue` cho cả bốn; chỉ tái sử
dụng cho nghĩa đã xác nhận sau kiểm dữ liệu. Không tạo số giả để lấp cột.
Ví dụ giả định gói10tỷ/phần việc công ty3tỷ: không nhận10tỷ là doanh thu công
ty, không cộng tổng project và gói con lần nữa.

Field cần currency, cơ sở thuế/chưa xác định, nguồn/ngày cập nhật và tính chất
ước tính/có căn cứ. Chưa biết khác0; không cộng khác currency/basis.
Giữ policy tiền hiện hành mặc định. Nếu giá gói công khai được cho xem rộng
hơn giá dự thầu nội bộ, cần quyết định riêng; thêm cột không tự mở tiền qua
list/export/domain/file/comment cho mọi người.

## 5. Quản lý và quản trị: quy ước sản phẩm đề xuất

Không coi đây là định nghĩa duy nhất của ngành hoặc chức danh pháp lý đã chốt.

| Nội dung | Quản lý thực hiện dự án | Quản trị dự án phía KH-KD |
| --- | --- | --- |
| Trọng tâm | Ai làm gì, khi nào, tiến độ/chất lượng/đầu ra | Phạm vi cam kết, hợp đồng, giá/khoán, hiệu quả, rủi ro/nghĩa vụ |
| Công cụ | WBS, giao việc, nguồn lực, bàn giao/chất lượng | Thầu, hợp đồng/phụ lục, khoán, sản lượng/NT, đề nghị thanh toán/đối chiếu QT-TC |
| Tham gia | Chủ nhiệm/chủ trì chuyên môn, điều phối/phòng thực hiện | Chủ trì KH-KD, trưởng Ban, QT-TC/lãnh đạo đúng scope |

Cùng project/dữ liệu, hai góc nhìn theo quyền; một người có thể kiêm vai.
Không tạo hai database/hai dự án. KH-KD không thay chuyên môn hoặc hạch toán/
thu chi kế toán. BASE tiếp tục duyệt chính thức. Trưởng Ban quản lý nghiệp vụ
không mặc nhiên thành administrator hoặc người ký mọi hợp đồng.

## 6. Trình tự làm tiếp và tiêu chí

1. **Đặc tả/mapping trước code:** tình huống giả một dự án/nhiều gói/nhiều
   đối tác, cả giao trực tiếp; chốt vai bên ký/chủ đầu tư, nghĩa tiền, trạng
   thái/actor và note. Mapping read-only CRM–Project cũ, đánh dấu trùng/thiếu link.
2. **Nền dữ liệu/quyền:** correction F1–F3 riêng; thống nhất V2 và quyền tạo/
   ghi dự án sớm/phân công; thiết kế field/quan hệ/nhật ký, migration có preview/
   idempotency/rollback. Không cấp platform manager chỉ để đủ nút.
3. **UI native Dự án/Đấu thầu:** cùng project ID, nhãn/cột/form đúng vai,
   đối tác/giá gói; test trước, không tự áp18069 trong batch phân tích này.
4. **Tình trạng/note/báo cáo:** action backend kiểm scope/role/state/version,
   lịch sử có căn cứ, dashboard project/gói/hồ sơ không đếm trùng.
5. **Walkthrough/áp dụng:** kiểm5vai, dữ liệu cũ/mới; nguồn test khớp bản áp,
   backup/restore verified và chỉ thị triển khai tương ứng trước áp dev.

Acceptance: một dự án/hai gói không trùng project; nhiều vai đối tác; đổi
một gói không tự đổi dự án/gói khác; note không ghi đè bản nộp; owner trước
hạn; quyền tiền đủ cả list/export/file/query; null khác0; không mất liên kết/
lịch sử cũ; xử lý cập nhật đồng thời; đúng người lập/rà soát thực sự dùng được nút.

## 7. Bàn giao

Chỉ tài liệu/status/changelog/roadmap; chưa sửa DEC thành quyết định duyệt.
Không code/DB/account/password/runtime/commit/push. V2/F1–F3/gate cũ giữ riêng.
Subagent lỗi model kế thừa, đây là phân tích phiên chính, không là audit độc lập.
Giữ checkpoint công việc khác, không finish hoặc sửa AI_WORKFLOW_STATE thay.
Kiểm link/diff/source digest; không chạy Odoo tests cho tài liệu.
Next: đặc tả mapping/state/field/acceptance trước prompt triển khai.
