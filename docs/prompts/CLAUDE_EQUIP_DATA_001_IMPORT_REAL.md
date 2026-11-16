# EQUIP-DATA-001 — Nhập hai workbook thật vào Kho thiết bị trên 18069

Làm việc trong `C:\TANPHAT ONE`.

## 1. Kết quả phải có và quyền thực hiện

Module `tp_equipment` đã chạy trên main nhưng kho còn trống vì lượt EQUIP-001
chưa nhập Excel. Lần này người dùng **đã yêu cầu nhập dữ liệu thật từ hai file
dưới vào database chính và hiển thị ngay trên 18069**. Thực hiện nhập, không
dừng ở phân tích, viết script, màn xem trước hoặc hướng dẫn người dùng tự nhập.

1. `C:\2026_tanphat_cntt_thiet-bi_0611.xlsx`
2. `C:\TP_TBCNTT_De xuat mua mới.xlsx`

File số 2 được người dùng gửi lặp đường dẫn: chỉ có **hai workbook khác nhau**.
Không nhập file đề xuất hai lần. Không hỏi lại quyền nhập/áp main đã được giao.
Chỉ admin quản lý module; không đổi quyền, tài khoản hoặc danh sách HR.

Môi trường: `tp_tanphat_dev`, HTTP **18069**, PostgreSQL workspace **55432**.
Theo chỉ đạo trực tiếp và DEC-045: làm trên main, không dùng 18079, không tạo
database khác, không viết/chạy bộ test riêng hoặc tạo dữ liệu giả. Vẫn backup
trước ghi, xử lý lỗi và đối chiếu kết quả nhập thật; không báo test PASS khi
không chạy test. Không commit/push.

## 2. Đọc source và sao lưu trước khi ghi

Đọc `AGENTS.md`, `docs/PROJECT_STATUS.md`, `docs/AI_CHANGE_WORKFLOW.md`,
DEC-045 trong `docs/DECISIONS.md`, cùng:

- `custom_addons/tp_equipment/README.md` và các model/view/import/export liên quan.
- `docs/security/EQUIP_001_SCHEMA_AND_ACCESS.md`.
- `docs/architecture/TP_EQUIPMENT001_BLUEPRINT.md`.
- `ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md`.
- `docs/demo/EQUIP_001_USER_GUIDE.md`.
- `.local/equipment001/SOURCE_ANALYSIS.md` và các bản trích riêng cùng thư mục.

Kiểm `git status`, workflow/checkpoint, process/config/DB main thực tế; không
đụng batch đang ghi đồng thời. Chạy workflow `start` trước sửa. Không xóa hoặc
finish checkpoint của tác vụ khác. Tạo **backup mới** DB + filestore + source
đang chạy và manifest/hash dưới `.local/equip-data001/`; ghi đủ điểm phục hồi.
Không dùng backup trước lúc module hoàn thiện thay backup trước nhập.

Chụp baseline số lượng/ID/binding của thiết bị, đề xuất, import batch và HR/
department/user/group để phân biệt có sẵn với tạo mới. Kiểm batch đã preview/
applied và nhập dở trước đó, kể cả bản ghi inactive; tiếp tục thay vì tạo trùng.

Đọc workbook bằng `openpyxl`, cả công thức và cached values; không chạy công
thức/macro/external link, không sửa file gốc. Tính lại hash hai file local:

| File | SHA-256 của bản đã phân tích |
| --- | --- |
| Danh mục thiết bị | `3d8d3ed9d4a0c2cb3bacad2536302b44ce68e8567bcf6590e92a94304c70f03c` |
| Đề xuất mua mới | `95291f7a5926316cc7c89b7847abc8b7b1c94d46c2d2d551eac2b2953a9db6c1` |

Nếu hash khác, đọc và đối chiếu lại nội dung mới; không áp số đếm/kết luận cũ
một cách máy móc. Workbook, raw extract, giá, PII, IP/MAC, ảnh dữ liệu, backup
và báo cáo nhập chi tiết chỉ nằm ở vùng ignored/private, không đưa vào Git.

## 3. Dùng bộ nhập hiện có, khắc phục đúng chỗ còn thiếu

Tái sử dụng `tp.equipment.import.batch`, `.line`, `.column`, `.alias` và
`maintenance.equipment`; không tạo app/database hoặc importer engine thứ hai.
Kiểm implementation thực tế trước gọi, các điểm vào hiện có:

- Nạp file qua create/write của batch, `action_preview()`.
- Phân loại dòng, ánh xạ và `action_confirm_mapping()`.
- `action_apply()` tạo thiết bị **nháp** hoặc một đề xuất có nhiều dòng.
- Hoàn thiện thiết bị nháp rồi `action_tp_register()` để đăng ký quản lý.

Source CHG-010 mới chuyển một số trường cơ bản: tên/cấu hình/tình trạng/người
giữ; thiết bị mới mặc định ownership unknown, chưa có category. Không coi bước
apply này là đã nhập đầy đủ file. Bổ sung tối thiểu mapping/field/action trong
`custom_addons/tp_equipment/` nếu cần để giữ dữ liệu phần 4–5 và xử lý tiếp dòng
còn chờ. Tái dùng field hiện có; không sửa `odoo/` hoặc `addons/`.

Không INSERT/UPDATE SQL nghiệp vụ, sửa trực tiếp state, truyền cờ bypass hay
tắt constraint để nhập cho xong. Gọi ORM/action bằng actor admin đúng company;
giữ transaction/lock/audit/idempotency. SQL read-only đối chiếu được phép.
Nếu sửa schema/source, cập nhật version đúng quy trình, upgrade đúng addon và
restart đúng runtime main; không tự áp toàn bộ batch filter hoặc addon khác.

## 4. Nhập danh mục thiết bị đúng nghĩa

Nguồn chính là sheet `thiet bi`, header dòng 2. Sheet `dashboard` chỉ có nhãn,
không phải danh sách thiết bị hoặc số liệu KPI để nhập.

Ánh xạ đầy đủ các cột nguồn có dữ liệu:

| Nội dung Excel | Cách nhập |
| --- | --- |
| Mã/STT | Lưu đối chiếu nguồn; sinh `tp_code` bằng sequence. STT reset giữa nhóm, không là khóa |
| Người sử dụng | HR employee ID hoặc department/location đúng nghĩa; giữ tên nguồn nếu chưa xác định |
| Phân loại | Category có thật, tạo danh mục tối thiểu theo nguồn nếu thiếu; không tạo máy từ N/a |
| Thuộc sở hữu | Company/personal/rented/third_party/unknown theo bằng chứng; giữ ghi chú gốc |
| Hãng SX & Model | Hãng/model và tên dễ hiểu; chưa tách được thì giữ nguyên văn, không đoán |
| Thông số/cấu hình/màn hình | Field kỹ thuật khi chắc chắn + ghi chú nguyên văn; không tự tách phụ kiện thành thêm tài sản |
| HĐH/Office | Dùng phần mềm/ghi chú hiện có; trạng thái nguồn không thành xác minh bản quyền |
| Trạng thái và tình trạng/bảo trì | Tình trạng kỹ thuật theo nguồn + nhu cầu thay thế riêng + ghi chú, vẫn chưa kiểm tra thực địa |
| Ngày cấp/đưa vào sử dụng | Ngày chính xác chỉ khi có; giá trị tháng/năm/tương đối giữ ở `tp_date_source` |
| Bảo hành | `tp_warranty_source` và căn cứ phù hợp; không suy ngày hết hạn khi thiếu mốc/điều kiện |
| IP/MAC | Giữ chính sách importer loại khỏi dữ liệu lưu; không quét mạng, không đưa raw vào log/Git |

Phân tích trước thấy **70 dòng đánh STT**, phải có bảng giải trình đủ 70 dòng:
61 dòng phân loại rõ vật lý, 1 ứng viên WiFi thiếu phân loại, 1 dòng chưa đủ
thông tin máy, 1 dịch vụ FTTH và 6 dòng N/a. Đây là đối chiếu **dòng nguồn**,
không phải cam kết có 70 tài sản hoặc đã xác minh 61/62 tài sản.

- Dòng 56–61 N/a: giữ trong đối chiếu, không tạo 6 thiết bị giả.
- Dòng 65 chưa đủ loại/model/cấu hình: chờ bổ sung, không tạo máy chỉ từ tên
  người và trạng thái hoạt động.
- Dòng 8 WiFi: chỉ phân loại AP nếu model/nội dung đủ căn cứ; ghi nhận cách
  diễn giải, nếu chưa đủ thì chờ. Không để dòng này chặn các dòng rõ ràng.
- Dòng 11 FTTH: ghi dịch vụ bằng loại `service` nếu model hỗ trợ phù hợp; nếu
  chưa nhập được thì giữ đối chiếu riêng có lý do, không cộng vào vật lý.
- B4:B11 merge là vị trí Phòng mạng. Chỉ fill trong merged range; không
  forward-fill cột trống toàn sheet. VP/nhóm phòng/máy số là vị trí hoặc nhãn,
  không phải nhân viên. TADIC là đơn vị nội bộ, không sinh công ty mới.
- Hai màn hình có tên giống nhau là hai dòng riêng; không merge theo tên/STT.
  Không tạo thêm màn hình chỉ vì cấu hình máy có nhắc màn hình đi kèm.
- Cấu hình có công thức dùng cached value và giữ provenance đã làm sạch;
  nội dung mâu thuẫn/lạ giữ ghi chú cần kiểm tra, không tự sửa thông số.
- Nguồn không có giá mua/serial chắc chắn: giữ unknown, không lấy tiền đề xuất
  làm giá mua, không dùng 0 hoặc hôm nay thay giá trị thiếu.

HR là nguồn danh tính dùng chung. Đối chiếu tên đầy đủ duy nhất trong cùng
company với HR hiện có, lưu employee/department ID + căn cứ. Khác chính tả,
tên ngắn hoặc nhiều ứng viên chỉ là gợi ý; không fuzzy-match rồi tự xác nhận,
không sửa tên HR, tạo người/user/phòng ban hoặc cấp quyền kho. Tái sử dụng
alias đã được xác nhận; alias mới thiếu căn cứ giữ chờ.

Nơi giữ và tình trạng ban đầu là thông tin **theo nguồn**, chưa chứng minh
bàn giao/kiểm kê thực tế. Chỉ nhóm Kho thực sự mới được gán `stock`; không gán
mọi dòng chưa tìm ra người thành “Trong kho”. Các máy rõ danh tính nhưng chưa
rõ người giữ phải giữ nháp/chờ mapping và không tăng tồn khả dụng giả.

Thực hiện apply và đăng ký các hồ sơ đủ điều kiện bằng action hiện có, giữ
`tp_verification=source`. Category/ownership/custody ban đầu phải được chuẩn
bị trước đăng ký vì sau đó có guard lịch sử. `action_tp_register()` sinh phiếu
opening: ghi rõ “Ghi nhận ban đầu từ Excel, chưa đối chiếu bàn giao thực tế”,
ngày hiện tại là **ngày ghi hệ thống**, không là ngày cấp/mua/nhận lịch sử.
Không tạo phiếu bàn giao/nhập mua/phê duyệt giả, không gọi mark_verified.

Đối với dòng còn thiếu: nhập phần đủ trước, giữ dòng nguồn + lý do + việc
cần bổ sung trong danh sách chờ có thể xử lý tiếp. `action_apply()` hiện chặn
unknown/wait/missing và khóa batch applied: không lách bằng cách đánh mọi
dòng là đã xác nhận. Nếu dùng skip có lý do để áp phần đủ, báo rõ đó là dòng
chưa nhập và bảo đảm có cách tiếp tục an toàn trên cùng binding, không tạo
batch/file giả mới hoặc làm mất dòng; bổ sung action nhỏ nếu thực sự cần.

## 5. Nhập đề xuất mua mới, không biến thành hàng đã có

Sheet1: header dòng 2, **5 dòng nội dung từ dòng 3–7**, một dòng tổng.
Nhập một hồ sơ đề xuất có 5 dòng chi phí theo nguồn; không tạo 5 thiết bị tồn.
Đối chiếu từng thành tiền cached và tổng độc lập với phân tích riêng trong
`.local/equipment001/SOURCE_ANALYSIS.md`. Không chép giá thực vào tài liệu Git.

Giữ người/bộ phận theo nguồn, cấu hình mong muốn, hiện trạng lỗi và phương án.
Phân loại mua mới/sửa/nâng cấp đúng nội dung; một dòng bao gồm mua máy và sửa/
chuyển máy cũ thì giữ đủ các ý trong mô tả/phương án, **không nhân đôi chi phí**
hoặc tự chia tiền cho những công việc không có giá riêng. STT reset không là ID.

Tiền nguồn là thành tiền dự kiến từng dòng, không mặc định đơn giá. Không bịa
số lượng/VAT/nhà cung cấp/ngày đề xuất/biên bản/approval. Nếu field ngày bắt buộc
đang tự lấy hôm nay, phân biệt ngày ghi hệ thống với ngày chứng từ chưa biết;
sửa tối thiểu cách thể hiện/field nếu cần để không lưu ngày giả làm ngày nguồn.

Giữ `review_state=draft`, `approval_state=unverified`; footer có tên người duyệt
không phải bằng chứng đã duyệt. Không tạo approval, receipt, purchase order,
hóa đơn, thanh toán hoặc tự đánh hoàn tất. Máy photo có thể liên quan nguồn
danh mục ở thời điểm khác: không tự kết luận cùng máy hoặc đã mua từ tên giống.
Mapping người ngắn/không rõ được giữ text + chờ xác minh; không chặn nhập nội
dung và số tiền rõ ràng của đề xuất.

## 6. Ghi bền vững, chống trùng và hiển thị ngay

- Giữ unique `(company, kind, SHA-256)` và binding hash/sheet/row của phiên bản
  nguồn. Trùng hash mở batch cũ; replay không tạo thêm thiết bị/đề xuất/phiếu
  opening. Nguồn đã thay đổi phải đối chiếu ID, không mặc định cùng row là cùng
  tài sản và không ghi đè dữ liệu đã sửa sau nhập.
- Mỗi đơn vị áp dụng hợp lệ phải nguyên tử; lỗi rollback phần giao dịch đó,
  báo lỗi và số đã commit thật. Không nuốt lỗi rồi báo toàn bộ thành công.
- Sau hoàn tất, dữ liệu đọc từ PostgreSQL qua Odoo, không còn phụ thuộc file
  Excel/JSON ở máy hoặc dữ liệu hardcode frontend. Refresh/restart không mất.
- Mở admin ở 18069: Thiết bị văn phòng, Chi tiết, Nháp/chờ bổ sung, Đề xuất,
  Đối chiếu nguồn và Tổng quan thiết bị. Dữ liệu phải hiện dưới filter/domain
  đúng; không bỏ scope/quyền để chữa màn trống. Tải lại dashboard từ DB.
- KPI/biểu đồ/drill-down/list/export cùng công thức và domain: tách vật lý,
  dịch vụ, công ty/cá nhân/thuê, nơi giữ, nháp, chưa xác minh. Không cộng đề xuất
  vào tồn hoặc tổng tiền dự kiến vào giá trị thiết bị. Không tô toàn bộ “Tốt”.
- Xem một số hồ sơ đã nhập thuộc nhóm cá nhân/phòng dùng chung/đặt tại vị trí/
  kho, một đề xuất và liên kết HR hiện có. Quan sát bộ lọc/phân trang/export
  của dữ liệu thật, chụp giao diện desktop/mobile ở `.local/equip-data001/`.
  Đây là đối chiếu vận hành sau nhập theo yêu cầu, không tuyên bố bộ test đạt.

## 7. Bàn giao bắt buộc

Lưu báo cáo riêng `.local/equip-data001/IMPORT_REPORT.md` và mapping từng dòng:
file hash/sheet/row → disposition → Odoo ID/code hoặc lý do chờ/bỏ qua.
Báo số **thực tế**: mới, có sẵn/liên kết, đăng ký, nháp, dịch vụ, N/a, chờ,
lỗi; các nhóm phân loại không đếm trùng và giải trình đủ dòng nguồn.
Đề xuất: số hồ sơ/số dòng/tổng dự kiến đối chiếu; phần chưa xác minh ghi riêng.
Chỉ báo thành công sau commit và đọc lại main, không từ số lượng preview.

Cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP, hướng dẫn và runbook nhập; nếu sửa
schema/quyền/UI bảng thì cập nhật đúng tài liệu liên quan/inventory DEC-044.
Tài liệu tracked chỉ ghi mô tả và số đếm tổng hợp, không raw/PII/giá nguồn.
Chạy `git diff --check` và `ai_workflow finish/check` với ID mới. Chỉ lint/parse
cần thiết nếu sửa source; không tự thêm cổng test 18079 hoặc đòi lại quyền main.

Báo cuối bằng tiếng Việt: đã nhập gì thật, hiện xem ở menu/URL nào, backup ở
đâu, còn dòng nào cần thông tin gì và vì sao; source nào sửa/upgrade nếu có.
Xác nhận HR/user/quyền và dữ liệu phòng khác bảo toàn; không commit/push.
Không kết luận đã kiểm kê, bàn giao, được duyệt mua hoặc nghiệm thu nghiệp vụ
chỉ từ việc nhập Excel thành công.
