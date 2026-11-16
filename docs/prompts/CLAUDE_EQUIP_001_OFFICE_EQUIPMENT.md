# EQUIP-001 — Kho và quản lý thiết bị văn phòng TANPHAT ONE

**Sau triển khai CHG-010:** module đã chạy trên18069 nhưng chưa nhập nguồn.
Người dùng đã giao nhập hai file local ở CHG-011; dùng
[prompt EQUIP-DATA-001](CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md) cho việc nhập thật.
Hạn chế chưa nhập nguồn trong prompt triển khai lịch sử này không chặn yêu
cầu nhập mới đã được giao; không chạy lại toàn bộ task dựng module.

Làm việc trong `C:\TANPHAT ONE`. Triển khai trực tiếp trên **18069** theo các
slice bên dưới. Đây là phân hệ nghiệp vụ thật trên native Odoo, dùng cùng database,
employee/department/user/partner và shell của HR/KH-KD.

**Yêu cầu cập nhật đã chốt:** tạo **một module riêng “Kho thiết bị văn phòng”**,
addon `tp_equipment`, có thẻ/icon/menu/dashboard/sidebar riêng. Không gộp kho vào
HR hoặc KH-KD. **Chỉ admin hệ thống truy cập và quản lý**; HR, HEAD, technician,
nhân viên và QT-TC không phải admin không được xem/thao tác kho ở giai đoạn này.
Phần này thay phương án nhiều vai trò trong prompt phiên bản đầu.

**Chỉ đạo triển khai mới nhất — CHG-20261114-009:** người dùng yêu cầu làm thẳng
trên 18069, không qua môi trường 18079, không viết/chạy bộ kiểm thử riêng trước
khi áp dụng, lỗi phát sinh sửa trực tiếp. Chỉ đạo này thay cổng test-only của
bản prompt trước và quy tắc test-first trong tài liệu tham khảo cho riêng EQUIP-001.
Không dừng chờ người dùng ra lệnh áp main lần nữa. Vẫn giữ backup trước thay đổi,
bảo toàn dữ liệu/quyền và xem màn hình sau khởi động để bàn giao kết quả nhìn thấy.

## 1. Quyền thực thi và nguyên tắc

- Triển khai, install/upgrade addon cần thiết trực tiếp trên
  `tp_tanphat_dev`, cổng **18069**, PostgreSQL workspace 55432. Sao lưu DB +
  filestore + ghi source/config baseline trước sửa. Không chạy bộ test hoặc
  diễn tập restore trên 18079; không tạo database mới.
- Dừng/khởi động lại đúng Odoo main khi cần upgrade; giữ PostgreSQL và ứng dụng
  không liên quan. Áp từng phần hoàn chỉnh để admin mở được trên 18069 ngay,
  không chỉ lưu source chờ lượt deploy khác.
- Không seed dữ liệu giả vào main, không bulk nhập Excel thật hay đổi quyền/
  tài khoản hiện có ngoài yêu cầu. Chức năng import phải có preview/mapping;
  nhập dữ liệu thật là thao tác riêng khi người dùng giao, không suy từ lệnh code.
- Không tạo DB thiết bị riêng, không DB theo slice. Một database mỗi môi trường;
  giữ nguyên 18079, không restore test đè main.
- Dùng quan hệ employee/department/user/partner thật để cấp phát/ghi nhận,
  không tạo bản sao hoặc cấp quyền kho chỉ vì người đó là người nhận thiết bị.
  Admin lấy từ `base.group_system` ở backend, không theo tên/login/cờ frontend.
- Không commit/push, không xóa dữ liệu/source/module đang có, không sửa `odoo/`
  hoặc `addons/`. Code riêng trong `custom_addons/`, không FE React độc lập.
- “Áp dụng đầy đủ kỹ thuật” nghĩa là đúng native Odoo 20, giao dịch/quyền/dữ
  liệu/UI phù hợp. Không cài OmniRoute/Graphify, Data Lake, microservice,
  package chart hoặc AI agent chỉ để đủ tên công nghệ.

## 2. Đọc trước khi code

1. `AGENTS.md`, `.agents/skills/tanphat-odoo-delivery/SKILL.md`.
2. `docs/PROJECT_STATUS.md`, `docs/AI_CHANGE_WORKFLOW.md`, `docs/DECISIONS.md`,
   `docs/ROADMAP.md`, `docs/HANDOFF_TEMPLATE.md`, `docs/AI_TOOLING_PLAYBOOK.md`.
3. **Thiết kế bắt buộc** `docs/architecture/TP_EQUIPMENT001_BLUEPRINT.md`.
4. `docs/ui/TP_TABLE_FILTER_STANDARD.md`, `docs/ui/TP_TABLE_FILTER_INVENTORY.md`,
   prompt UI-TABLE-FILTER-001 nếu đang chạy; `docs/ui/KD_UI_007_DESIGN.md`.
5. `docs/demo/UI_INPUT_001_ACCEPTANCE.md`,
   `docs/demo/UI_SHELL_UNIFY_001_ACCEPTANCE.md`,
   `docs/architecture/TP_IDENTITY_ORG_001.md`,
   `ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md`.
6. Phân tích riêng `.local/equipment001/SOURCE_ANALYSIS.md` và trích nguồn
   `.local/equipment001/source_extract.json` nếu có. Đây là dữ liệu riêng ngoài
   Git, không chép raw/PII/IP/giá thật vào code, docs hoặc ảnh bàn giao công khai.

Đọc hai workbook gốc **read-only**, xác nhận hash/schema và phân tích lại nếu
file đã đổi hoặc không có bản trích; không chạy macro/external links hay sửa Excel:

```text
\\192.168.1.2\6.tadic\06_cntt_tanphat\2026_tanphat_cntt_thiet-bi_0611.xlsx
\\192.168.1.2\6.tadic\06_cntt_tanphat\TP_TBCNTT_De xuat mua mới.xlsx
```

Đọc skill `frontend-design`, Ponytail nếu có; Playwright chỉ dùng mở/chụp màn
hình để bàn giao nếu tiện, không thiết lập bộ test. Báo đúng công cụ thực dùng,
không gọi việc mở trang/xem ảnh là đã kiểm thử toàn bộ hoặc audit độc lập.
Kế thừa style/token của hệ thống, không áp template dashboard chung.

## 3. Baseline và phối hợp tác vụ

Kiểm git/checkpoint/workflow/module states/runtime, schema main và source paths
thực sự được server load. Chạy `scripts/ai_workflow.py start` trước sửa, giữ
checkpoint đang có. Không finish batch khác hoặc sửa handoff để che code drift.

UI-TABLE-FILTER-001 được báo hoàn tất trên test ở CHG-008; chưa mặc định đã áp
main. Đối chiếu code/module dependency hiện có; chỉ nâng cấp phần phụ thuộc cần
cho EQUIP và bảo toàn chức năng đang dùng, không tự nhận task triển khai toàn
bộ bộ lọc cũ đã được giao riêng. Nếu còn tác vụ khác sửa cùng source/ghi main,
phối hợp thứ tự, không upgrade cùng DB song song. Không mở thêm database.

Trước code xác định model/dependency/field/capability ở S0, dựa vào
source `maintenance`, `hr_maintenance`, `stock`, `purchase` thực tế. Có source
không đồng nghĩa đã cài DB. Ưu tiên `maintenance.equipment`/`maintenance.request`
làm hồ sơ gốc, không dựng một sổ thiết bị custom cạnh một sổ native độc lập.

**Cổng bảo mật quan trọng:** upstream `hr_maintenance` implied Equipment Manager
cho HR officer; maintenance cho internal user đọc rộng theo company. Không cài
nguyên trạng rồi giả định record rule bổ sung sẽ thu hẹp được union quyền.
Thiết kế guard/rule/bridge custom kiểm cả native RPC/public HR/follower/file;
không tự gỡ quyền người thật hoặc sửa group rộng của hệ thống. Nếu chưa cài
`hr_maintenance`, ưu tiên bridge HR có scope riêng, không dependency mặc định
vào addon tự mở quyền. Giải thích lựa chọn trong schema/security note.

## 4. Chức năng phải hoàn thành

### A. Danh mục, thiết bị, hồ sơ chi tiết

- Thiết bị gốc: mã riêng tuần tự unique (khác mã TP nhân viên, không dùng ID
  hoặc STT reset), tên, loại, hãng/model, serial tùy thực tế, ảnh, vị trí, sở hữu,
  ngày mua/cấp/bảo hành và mức xác minh; cấu hình gốc và trường có cấu trúc.
- Người giữ liên kết HR theo ID; thiết bị dùng chung gắn phòng/vị trí; bên thuê/
  bên sửa gắn partner. Sở hữu pháp lý khác native owner/technician user.
- Tách vòng đời, custody/khả dụng, sức khỏe kỹ thuật, sửa chữa, bảo hành và phần
  mềm; không một status chung cho mọi nghĩa. Chưa biết khác 0/False/đã hết hạn.
- Máy cá nhân không thành tài sản công ty/stock receipt của công ty; thuê và
  bên thứ ba có quyền sử dụng riêng, không tự cho bán/cấp ngoài phạm vi. Serial
  xác minh có constraint theo phạm vi hợp lý, serial trống không fake unique.
- Tạo, đọc, sửa, lưu/hủy nháp; nhân bản metadata an toàn với mã mới, bỏ serial/
  custody/current transaction. Xóa thật chỉ draft nhập nhầm chưa tham chiếu
  theo quyền và xác nhận; hồ sơ/giao dịch đã sử dụng dùng ngừng/reverse có lý do.
  Không cascade xóa máy/lịch sử khi xóa employee, supplier hoặc phiếu cha.
- Gắn ảnh/file, ghi chú, lịch sử có actor/ngày/lý do; quyền file/chatter đúng
  field/scope. Hồ sơ HĐH/Office là khai báo + chứng cứ xác minh, không giả giấy phép.
- Phụ kiện/thiết bị con quản lý riêng chỉ khi có định danh; không tự tách nhiều
  màn hình từ text cấu hình thành asset đã kiểm. Dịch vụ FTTH tách khỏi tồn vật lý.

### B. Kho và luồng bàn giao

- Tiếp nhận từng máy: phiếu/line, nguồn giao, nhà cung cấp, ngày, tình trạng,
  serial/giấy tờ nếu biết; nhập từ đề xuất hoặc nguồn độc lập theo quyền.
- Cấp phát nhân viên/phòng/vị trí, thu hồi, điều chuyển, cho mượn/trả, trả thuê;
  preview trước/sau, người giao/nhận, ngày/hạn, phụ kiện/tình trạng, lý do và tệp.
- Reservation/pending nhận/đang vận chuyển nếu giao chưa hoàn tất; hủy đúng
  state giải phóng reservation. Không cấp một máy cùng lúc cho hai đối tượng.
- Một transaction cập nhật phiếu + current custody + availability + audit;
  kiểm state/version và khóa cạnh tranh. Retry không ghi hai giao dịch.
- Phiếu đã ghi bất biến; sai thì correction/reverse liên kết, lý do bắt buộc.
  Bulk action phải có preview/per-record guard và chính sách atomic rõ ràng.
- In/tải biên bản PDF nội bộ, có chỗ xác nhận; không tạo chữ ký hay gọi là duyệt
  chính thức. QR/tem dùng mã/opaque ID, không chứa PII/IP/cost, route phải xác thực.
  Hỗ trợ nhập/quét mã bằng thiết bị quét bàn phím; camera chỉ progressive
  enhancement khi browser cho phép, có phương án nhập tay.

### C. Báo hỏng, bảo trì, sửa chữa, nâng cấp

- Admin ghi nhận báo lỗi/yêu cầu của nhân viên, phân loại/độ ưu tiên và người
  kỹ thuật thực tế; nhân viên/kỹ thuật không được mở module thao tác. Theo dõi
  thời hạn, đang xử lý/gửi NCC, kết quả/nhận lại; actor admin khác người báo lỗi.
- Kế hoạch bảo trì, lịch sử và thông báo in-app/activity theo cấu hình; không
  gửi mail ra ngoài, gọi nhà cung cấp hoặc tự quét mạng. Không lưu credential thiết bị.
  Người nhận activity/follower/native assignment phải là admin được phép;
  kỹ thuật viên thực tế không phải admin chỉ lưu metadata thực hiện, không
  thêm vào native assignee nếu việc đó mở quyền/subscribe ngoài policy.
- Nâng cấp lưu cấu hình/linh kiện trước–sau và chi phí theo quyền. Kết quả sửa
  không tự chuyển thành Tốt nếu không có kết luận; máy còn hỏng không sẵn sàng cấp.
- Bảo hành theo ngày/duration/meter có nguồn; mốc gần hạn người dùng chọn hoặc
  cấu hình, không suy `Còn BH` thành ngày giả. Máy photo theo số bản cần readings
  có ngày/unit và quy tắc đã xác minh; không chỉ countdown ngày.

### D. Đề xuất mua/sửa/nâng cấp và tiến độ thực hiện

- Hồ sơ cha + dòng: đối tượng cần, máy cũ nếu xác minh, nhu cầu/hiện trạng,
  phương án, cấu hình mong muốn, số lượng/đơn vị nếu biết, dự toán Monetary và
  currency/thuế đã biết. Không đổi cột “thành tiền” nguồn thành unit price giả.
- Nháp → gửi rà soát → trả lại bắt buộc lý do → sửa/gửi lại → hoàn tất rà soát.
  Admin thực hiện thao tác trên hệ thống, lưu riêng người lập/xem xét/duyệt
  thực tế theo bằng chứng. Rà soát kỹ thuật khác kết quả phê duyệt chi/BASE;
  không hardcode tên ở Excel hoặc cấp quyền kho cho người có tên trên phiếu.
- Lưu nguồn/ref/file/người ghi và mức kiểm chứng kết quả duyệt theo quy trình
  hiện hành; không gọi footer Excel là đã duyệt, không tự đặt hạn mức. BASE vẫn
  nguồn duyệt theo quyết định hiện hành nếu áp dụng; chưa căn cứ thì chờ xác minh.
- Theo dõi chưa đặt/đang thực hiện/nhận từng phần/đã nhận, link tiếp nhận và máy
  mới. Điều kiện chuyển thực hiện theo ma trận đã đặc tả; chưa được phép thì
  không bật nút chỉ vì reviewer nhấn hoàn tất. Không tạo bằng chứng duyệt giả.
- Tách nhánh mua máy mới, sửa máy cũ và chuyển máy cũ cho người khác; không mất
  trace hoặc tạo hai máy nhận từ một dòng. Không nhận vượt/không nhận lặp, không
  coi đề xuất như PO/vendor bill/thanh toán/tài sản cố định đã ghi sổ.

### E. Kiểm kê, ngừng sử dụng và báo cáo

- Kỳ kiểm kê có snapshot phạm vi, ngày/người phụ trách; dòng kỳ vọng/thực đếm,
  người/vị trí thực tế, tình trạng, quét mã; thiếu/thừa/chưa kiểm/sai vị trí tách rõ.
- Chốt chênh lệch không tự ghi đè giao dịch phát sinh sau snapshot. Preview và
  action điều chỉnh theo quyền/lý do/version, audit không sửa lùi.
- Ngừng sử dụng/mất/trả thuê/đề xuất thanh lý giữ lịch sử, ràng buộc sở hữu và
  phiếu đang mở; căn cứ xử lý theo quy trình ngoài. Không tự ghi giảm kế toán.
- Báo cáo sổ thiết bị, theo người/phòng, tồn khả dụng, sửa/bảo hành, nhu cầu/
  tiến độ nhận, kiểm kê và dữ liệu chưa đầy đủ. Excel đúng filter/scope, đọc lại
  XLSX kiểm nội dung, đúng kiểu tiền/ngày, sum currency, formula-injection guard.

### F. Nhập nguồn, đồng bộ và quyền

- Import preview bắt buộc: batch/file hash/sheet/row/cell/raw/cached/merged
  provenance, gợi ý mapping, xung đột và resolution có người xác nhận; không
  evaluate formula không tin cậy. File đổi cần diff/confirm identity, không
  dùng row/STT làm business key qua phiên bản.
- Không forward-fill tùy ý ô rỗng. Loại riêng section/header, N/a, thiếu thiết
  bị, dịch vụ, máy thật; mỗi dòng có disposition, không âm thầm bỏ qua.
- Tên viết khác/viết tắt/nhóm dùng chung không auto-match, không tạo employee/
  user mới hoặc sửa HR từ Excel. Alias chỉ apply sau xác nhận mapping ID.
- Import đầu kỳ giữ “theo nguồn/chưa xác minh”, không bịa biên bản/ngày/serial/
  giá. Cùng source/hash/apply retry không tạo trùng. Không hồi sinh hồ sơ HR đã xóa.
- Tab/smart button trong HR chỉ admin thấy và dùng cùng equipment ID; không
  làm Thiết bị của tôi/self-service cho non-admin. Đổi tên/ảnh HR nhất quán,
  đổi phòng HR không tự sinh phiếu điều chuyển; admin có cảnh báo xử lý custody.
  Khóa user không chứng minh đã thu hồi tài sản.
- **Admin-only:** chỉ tài khoản internal active có `base.group_system` được
  đọc/ghi/search/export/report/config và thao tác module trong company được phép.
  Không cấp system admin cho người nhận máy hoặc implied từ role HR/KH-KD.
  Không tạo nhóm equipment-manager/non-admin thay thế quyền này trong scope hiện tại.
- Người yêu cầu/người nhận/người kỹ thuật/phê duyệt ngoài vẫn là thông tin
  nghiệp vụ trong phiếu, không là quyền đăng nhập module. Admin nhập/xác minh
  theo bằng chứng, không giả actor nhân viên hoặc thẩm quyền duyệt pháp lý.
- Non-admin không nhận menu/thẻ/count/metadata/row/file của kho qua HR/public HR,
  maintenance native, trực tiếp URL/QR/RPC, export/search/group/dashboard hay mail.
  Không auto-subscribe người nhận/manager làm lộ chatter/file/email. Bảo vệ cả
  managed flag và field ghi trực tiếp; không phá maintenance khác ngoài scope.
- Backend kiểm create/write/unlink/action/domain/search/read/count/group/export/
  file/chatter và native entrypoint; không bypass qua RPC/context giả/admin flag.
  Bảo vệ native cost, owner assignment, scrap và inherited methods, không chỉ
  thêm guard vào controller custom. Nhân viên chưa có user vẫn nhận máy được.

## 5. Giao diện phải nhìn thấy sự thay đổi

Thiết kế theo mục 6 blueprint, dùng nền sáng, sidebar giống format HR/KH-KD,
navbar chung và `TpUserAccountMenu`; không 2 navbar hoặc tài khoản lặp góc phải.
Trang chủ thêm thẻ **Kho thiết bị văn phòng** chỉ admin từ menu server. Module
có dashboard/sidebar/menu riêng; dùng chung style/data không có nghĩa gộp UI
vào phòng ban khác. Non-admin không thấy entrypoint, kể cả có HR/HEAD/native
equipment-manager group; kiểm backend phải từ chối cả truy cập trực tiếp.

- Dashboard là trọng tâm: filter kỳ/phạm vi, KPI có định nghĩa, **donut theo
  loại và tình trạng**, cột theo phòng/vị trí, xu hướng khi đủ lịch sử và bảng
  cần xử lý có action. Màu/legend/tooltip/số liệu thống nhất, click drill-down
  đúng domain. Chưa có giá/lịch sử phải hiển thị thiếu, không tạo chart giả.
- Danh sách gọn, đường kẻ rõ, badge có chữ/màu theo ý nghĩa, row hover nhẹ,
  optional columns, action theo capability/state; filter riêng mọi bảng theo
  DEC-044, cả relation/popup/report/history; server paging 10/20/50/100 và
  export dùng domain đã áp, không lọc trên trang đang tải.
- Chi tiết thiết bị có ảnh/mã/tên, hai badge khả dụng/kỹ thuật, người giữ,
  nút chính hợp lý, tab Tổng quan/Cấu hình/Bàn giao/Sửa chữa/Bảo hành/Phần mềm/
  Tài liệu/Lịch sử. Đề xuất/kiểm kê/giao dịch có form riêng đúng nội dung.
- Ô nhập rõ theo `UI-INPUT-001`; validation/error/readonly khác nhau. Desktop
  1440x900, mobile 390x844, zoom200, keyboard/focus và vùng chạm >=44px.
- Animation chart/panel/tab có mục đích, hover 150–220ms, giảm chuyển động khi
  `prefers-reduced-motion`. Không nhảy layout, flashing hoặc hàng bảng bay vào.
- Chart dùng thư viện đang có phù hợp; không tải CDN hoặc cài chart framework
  mới khi Odoo/stack hiện có đủ. Việt hóa nhãn nghiệp vụ, giữ tên/thuật ngữ đặc thù.

## 6. Các slice và kết quả sau mỗi slice

| Slice | Kết quả có thể kiểm trực tiếp |
| --- | --- |
| S0 | Đọc source/schema/quyền, chốt dependency, backup DB+filestore/source baseline và kế hoạch áp trực tiếp main; không viết AT/bộ test trước code |
| EQUIP-001a | Admin mở module riêng từ Trang chủ → list/detail → tạo/sửa nháp → import preview → cùng asset ở HR admin-only; non-admin không thấy/truy cập, chưa nhập nguồn thật |
| EQUIP-001b | Nhập → cấp → thu hồi/điều chuyển/cho mượn → báo hỏng → sửa/nâng cấp → nhận lại, đủ audit và case race/retry/reversal |
| EQUIP-001c | Đề xuất trả lại/gửi lại và kết quả ngoài đúng guard; nhận từng phần; chức năng kiểm kê/chênh lệch không đè giao dịch mới, không seed fixture main |
| EQUIP-001d | Dashboard donut/cột thật, drill-down, toàn bộ filter và report Excel/PDF/QR; desktop/mobile/roles tốt, dữ liệu trống/lỗi/quyền không vỡ layout |
| EQUIP-001e | Module đã cài/chạy trên 18069, URL/menu và ảnh để admin xem ngay, user guide, ghi chức năng còn thiếu/lỗi đã sửa và backup/rollback; chưa bulk nhập thật hoặc mở role non-admin |

Từng slice hoàn thiện, upgrade main và cập nhật tài liệu rồi tiếp tục; mở ngay
trên 18069 để người dùng xem, không dừng sau khung UI hoặc yêu cầu thêm lệnh
deploy. Gặp lỗi sửa trực tiếp trong phạm vi EQUIP; nếu Odoo không khởi động thì
ưu tiên khôi phục khả năng mở hệ thống, không xóa dữ liệu để né lỗi. Phân biệt
chức năng đã có, phần đang lỗi/chưa xong và mapping chưa xác nhận.

## 7. Tiêu chí chức năng — AT-E01 đến AT-E18

Giữ các ID để mô tả hành vi cần có và tránh bỏ sót khi code. **Đây không phải
yêu cầu viết/chạy test**: không tạo fixture/giao dịch kiểm thử trong main,
không viết acceptance test trước code, không bắt chạy đủ các ca dưới đây mới
đưa lên 18069. Nội dung về race/quyền là ràng buộc backend phải triển khai.

| ID | Điều kiện phải chứng minh |
| --- | --- |
| AT-E01 | Module riêng có thẻ/icon/menu/dashboard/sidebar riêng admin-only; một asset ID dùng ở workspace/HR admin/report, đổi tên/ảnh HR đồng bộ, không bản sao hoặc DB riêng |
| AT-E02 | CRUD/duplicate/archive/delete guard đúng, mã unique không reuse nhầm serial, đã dùng không xóa vật lý, HR delete không cascade mất asset/audit |
| AT-E03 | Import header/merge/reset STT/N/a/service/unknown/formula cache phân loại đúng, mỗi dòng disposition; alias cần confirm, không tạo user/employee hoặc gán tên gần giống |
| AT-E04 | Import replay và file đổi thứ tự không tạo trùng/ghi sai asset; atomicity và conflicts được báo; ngày/giá/ownership nguồn chưa rõ không tự điền |
| AT-E05 | Cấp/thu hồi/điều chuyển/mượn/trả có trước–sau, pending/reservation/cancel; đúng người/phòng/vị trí, máy hỏng không sẵn sàng |
| AT-E06 | Backend có khóa/constraint/version/idempotency chống cấp trùng, stale và retry; không cần chạy race test trên main |
| AT-E07 | Sửa/nâng cấp lưu old/new, vendor/chi phí/quyền/tệp, kết quả nhận lại; máy mới thay máy cũ giữ liên kết không mất custody máy cũ |
| AT-E08 | Đề xuất draft/submit/return reason/resubmit/review đúng actor/state; review không thành BASE approval; thiếu evidence/thẩm quyền không mở bước thực hiện |
| AT-E09 | Nhận từng phần tính đúng còn lại, không nhận vượt/lặp; chưa nhận không tạo tồn; mua RAM/nâng cấp không tự thành một máy tính mới |
| AT-E10 | Kiểm kê snapshot và thực tế tách biệt, chênh lệch/điều chỉnh có quyền/lý do, giao dịch sau snapshot không bị ghi đè |
| AT-E11 | Ngừng/trả thuê/đề xuất thanh lý/mất đúng sở hữu, không bán tài sản cá nhân/thuê như của công ty, không fake posting/accounting/chữ ký |
| AT-E12 | HR org move đổi thông tin hiện hành nhưng không tự chuyển vật lý/lịch sử, khóa user không coi đã thu hồi, offboard hiện tài sản cần xử lý |
| AT-E13 | Admin trong company/scope thao tác đúng; mọi non-admin gồm HR manager/HEAD/technician/staff/native equipment manager bị từ chối menu/action/URL/QR/RPC/read/write/search/count/export/file/chatter/public HR/email; không lộ metadata/tiền/IP qua union privilege hoặc managed flag |
| AT-E14 | Filter từng bảng theo DEC-044, nhiều trang/AND-OR/Clear parent scope/favorite/advanced/pending-applied/dirty relation đúng; count/chart/drill-down/export cùng domain |
| AT-E15 | KPI/donut/cột có định nghĩa và tie-out độc lập; physical vs service/unknown/ownership tách đúng; thiếu dữ liệu/giá không thành 0; datetime/timezone/currency chính xác |
| AT-E16 | Excel đọc lại đúng records/tổng/currency/date, formula injection bị chặn; PDF không giả ký; QR xác thực không public PII/tiền/tệp |
| AT-E17 | UI hỗ trợ desktop/mobile/zoom200/keyboard/reduced-motion, hover/animation/table/detail/form/empty/loading/error; có ảnh thực tế 18069 để bàn giao, không yêu cầu chạy Playwright test |
| AT-E18 | Giữ shell/HR/KH-KD/login/logout hiện có; module thực sự được cài/chạy 18069, có backup; không seed giả/bulk nhập thật hoặc thay role/credential người thật |

Theo lệnh trực tiếp của người dùng, bỏ Odoo/HOOT/E2E/race/regression suites và
cổng 18079 cho task này. Không ghi “test PASS” khi không chạy. Theo dõi lỗi
install/upgrade/assets/runtime, sửa để Odoo mở được; mở menu/module sau khởi
động và chụp ảnh bàn giao, không thử xóa/ghi hồ sơ thật để chứng minh tính năng.

## 8. Bàn giao đầy đủ

Tạo/cập nhật theo scope:

- `docs/architecture/TP_EQUIPMENT001_BLUEPRINT.md` — mapping đã chọn vs đề xuất.
- `docs/security/EQUIP_001_SCHEMA_AND_ACCESS.md` — field/state/capability/guard,
  native privilege audit và nguồn dữ liệu; không tên người thật/password.
- `docs/demo/EQUIP_001_ACCEPTANCE.md` — trạng thái chức năng AT-E01–18 và ảnh
  main; ghi rõ không chạy bộ test theo yêu cầu người dùng, không giả kết quả.
- `docs/demo/EQUIP_001_USER_GUIDE.md` — admin mở module trên 18069 (secret ở ignored
  private), thao tác từng menu/list/detail/tạo/sửa/xóa hợp lệ/import/Excel/biên bản.
- `ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md` — module exact source,
  backup DB+filestore, preservation, exact upgrade/source/URL trên main và cách
  rollback khi lỗi; không yêu cầu rehearsal test hoặc tạo DB. Import thật riêng.
- README addon, `PROJECT_STATUS`, `CHANGELOG`, `ROADMAP`, prompt index và
  `TP_TABLE_FILTER_INVENTORY` với mọi bảng của thiết bị. Không ghi DEC nghiệp vụ
  mới thành đã được user duyệt nếu chỉ là lựa chọn thiết kế.

`git diff --check`, workflow finish/check cho batch của mình với ID mới.
Báo cuối: slice/chức năng thực sự đã có và phần còn lỗi/chưa xong, role/state/
model/module, bảng/filter, backup và ảnh. Gửi link **http://127.0.0.1:18069/odoo**
cùng đường menu **Kho thiết bị văn phòng** để admin dùng ngay. Ghi rõ đã cài/
upgrade phiên bản nào lên 18069, bộ test không chạy theo yêu cầu, mapping/thẩm
quyền còn thiếu. **Không báo hoàn thành khi chỉ có source mà module chưa mở
được trên 18069.** Chưa bulk nhập thật, chưa mở kế toán/khấu hao/thanh toán/
duyệt chính thức hoặc role non-admin.
