# EQUIP-SIMPLE-003 — Thu gọn Kho: thiết bị, người dùng và yêu cầu đề xuất

Làm việc trong `C:\TANPHAT ONE`. Bạn là phiên thực thi: triển khai hoàn chỉnh,
không chỉ lập kế hoạch. Prompt do phiên điều phối chuẩn bị ngày 16/11/2026,
theo yêu cầu mới nhất của người dùng; DEC-047. Chỉ đạo này thay phạm vi giao diện
Kho phức tạp của EQUIP-001/UI-001/UI-002, giữ dữ liệu và các bảo vệ backend.

**Bổ sung đã chốt trước khi triển khai — CHG-20261116-002:** máy thay thế chỉ
được chọn khi đang trong kho và chưa có người giữ. Máy có người giữ, kể cả cùng
người hoặc người đã nghỉ việc, không được dùng làm máy thay thế. Không đổi chéo
hai máy đang có chủ, không chuyển trực tiếp để lách quy tắc: cần thu hồi thực tế
về kho trước rồi mới gán/đổi. “Chưa có chủ” ở đây là chưa có người giữ hiện tại,
không phải field sở hữu pháp lý `tp_ownership` (công ty/thuê/cá nhân).

## 1. Kết quả người dùng cần

Một nơi đơn giản để biết **thiết bị gì — ai đang dùng — thuộc phòng nào —
thông tin/tình trạng máy ra sao**. Admin chọn thiết bị và nhân viên có sẵn để
gán; đổi máy hoặc thu hồi về kho bằng vài thao tác. Có thêm nơi ghi nhận yêu
cầu đề xuất thiết bị. Không bắt người dùng tự tạo phiếu, nhập lại tên/cấu hình
hoặc đi qua quy trình quản lý kho chuyên sâu.

Chỉ sửa trong `custom_addons/` và tài liệu liên quan. Native Odoo20/OWL/QWeb/SCSS;
không sửa `odoo/`, `addons/`, không thêm frontend React hoặc database riêng.
Giữ chung DB, nhân viên, phòng ban, avatar, tài khoản với HR/KH-KD.
Kho vẫn chỉ dành cho admin `base.group_system`; chọn nhân viên làm người giữ/
người đề xuất không cấp cho họ quyền truy cập Kho.

## 2. Đọc baseline rồi triển khai trực tiếp main

Đọc `AGENTS.md`, `docs/PROJECT_STATUS.md`, `docs/AI_CHANGE_WORKFLOW.md`,
`docs/DECISIONS.md` (DEC-044/045/046/047),
`.agents/skills/tanphat-odoo-delivery/SKILL.md`,
`docs/ui/TP_TABLE_FILTER_STANDARD.md`, `docs/ui/UI_BACK_001_STANDARD.md`,
`docs/security/EQUIP_001_SCHEMA_AND_ACCESS.md` và
`ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md`.

Đọc source và các caller liên quan trước sửa:

- `custom_addons/tp_equipment/models/{equipment,move,wizard,proposal,hr_employee,common,dashboard}.py`.
- `views/{equipment_views,move_views,proposal_views,menus,wizard_views}.xml`.
- `static/src/{sidebar,table,form,dashboard}`, `prefs.js`, `back_fallbacks.js`,
  controller xuất Excel, ACL và guard mail/attachment.
- Shared shell, bộ lọc và nút Quay lại của `tp_web_home`; HR chỉ đọc khi cần,
  tránh sửa lan sang phân hệ khác.

Kiểm git status/checkpoint, chạy `scripts/ai_workflow.py start` trước sửa;
không finish/xóa checkpoint của phiên khác. Lưu baseline ID và hash dữ liệu.

Người dùng đã cho phép làm trực tiếp `tp_tanphat_dev` cổng **18069**. Backup mới
DB + filestore + source/config metadata trong `.local/equip-simple003/` trước
khi áp thay đổi. Không ghi secret, dữ liệu nhân sự, ảnh hoặc dump vào Git.
Không tạo/chạy 18079, clone, fixture hoặc bộ test riêng cho task Kho này.
Không hỏi lại quyền áp main; không setup, seed, nhập lại Excel hay xóa dữ liệu.
Không commit/push. Sau upgrade đúng module cần thiết, mở 18069 để người dùng xem.

## 3. Điều hướng: chỉ hai mục

```text
Kho thiết bị văn phòng
├─ Thiết bị             ← màn mặc định khi mở Kho
└─ Yêu cầu đề xuất
```

Gỡ menu/tab dư khỏi sidebar, menu native và các nút tắt: Tổng quan riêng,
Quản trị dữ liệu, kiểm kê, sửa chữa, QR, phiếu nhập, phiếu bàn giao, báo cáo,
đang chờ, sẵn sàng cấp... Không giữ cả một nhóm chức năng phụ dưới sidebar.
Không chỉ dùng CSS che trong khi menu native vẫn hiện đầy đủ.

Đây là thu gọn giao diện, **không DROP bảng, uninstall addon, xóa thiết bị,
đề xuất, nguồn nhập hoặc lịch sử**. Backend phiếu đang bảo vệ việc chuyển máy
được tái sử dụng và tự chạy phía sau. Lịch sử nằm ngay trong chi tiết thiết bị.
Dữ liệu nguồn chờ xác minh, dịch vụ, hồ sơ ngừng quản lý vẫn có đường truy cập
admin phù hợp qua bộ lọc nâng cao/hộp thông tin dữ liệu hoặc Cài đặt; không
thêm menu sidebar thứ ba. Ghi rõ nơi truy cập trong hướng dẫn bàn giao.
Giữ XML ID/action có dependency; xử lý menu cũ, last-leaf đã lưu, home card,
dashboard drill-down/back fallback và deep link cũ để không mở màn rỗng/lỗi.

## 4. Một danh sách thiết bị dùng chung

Không tạo bản sao thiết bị theo nhân viên/kho. Một thiết bị có một bản ghi,
đổi người giữ hoặc trả kho vẫn cùng ID, mã, serial, cấu hình và lịch sử.

Phía trên danh sách chỉ cần tiêu đề, ba số tóm tắt nhỏ theo dữ liệu thật,
nút **Thêm thiết bị**, **Gán thiết bị**, **Xuất Excel**; không dashboard đồ sộ.
Dùng bộ lọc nhanh dạng segmented: **Tất cả / Đang sử dụng / Trong kho**.

Bảng ưu tiên các cột:

| Cột | Nội dung |
| --- | --- |
| Thiết bị | Tên + mã TB; nhãn loại thiết bị rõ ràng |
| Người sử dụng | Avatar, tên, mã nhân viên lấy từ HR ID; không nhập tên tay |
| Phòng ban | Phòng ban hiện tại từ HR; máy dùng chung ghi đúng đơn vị/vị trí |
| Trạng thái | Đang sử dụng / Trong kho; trường hợp khác hiển thị đúng nguồn |
| Tình trạng máy | Tốt / Hạn chế / Hỏng / Chưa xác minh theo field thật |
| Ghi chú | Ghi chú kỹ thuật, hỏng hóc; không có ghi Chưa có ghi chú |
| Thao tác | Xem và các nút phù hợp; tác vụ ít dùng trong menu ba chấm |

Màn mặc định bao gồm thiết bị vật lý/linh kiện độc lập đang quản lý, kể cả
stock, có người giữ, dùng chung hoặc chưa rõ người. Không nhân bản linh kiện
đã gắn trong máy thành một máy độc lập; giữ liên kết và thông tin trong chi tiết.
Dịch vụ, nháp/ngừng quản lý xem qua phạm vi nâng cao có nhãn, không làm mất dữ liệu.

Trạng thái hiển thị lấy từ `tp_custody`, `tp_lifecycle` và helper hiện có;
không tạo enum hai trạng thái để ghi đè mọi loại dữ liệu cũ.
`stock` = Trong kho; employee/loan có HR ID = Đang sử dụng. Department/location
ghi Dùng chung/Đặt tại vị trí, không giả tên nhân viên; vendor ghi Đang sửa ngoài;
chưa rõ không tự biến thành stock. Trong kho có thể có máy hỏng/chưa kiểm tra,
không đồng nghĩa sẵn sàng cấp. Tách tình trạng kỹ thuật khỏi trạng thái sử dụng.

Tìm theo tên/mã/serial máy, tên/mã HR; giữ tìm không dấu hiện có. Bộ lọc gọn,
đúng nội dung: phòng ban, người dùng, loại máy, tình trạng; không chip preset
nhét vào ô tìm. Dùng backend domain thống nhất cho list/count/chọn máy/Excel;
clear filter giữ scope company/quyền. Giữ cách xem tất cả hiện có, không tự quay
về 20 dòng; nếu có giới hạn/pager phải ghi đúng, không tải xong một trang rồi
lọc bằng JS như thể đó là toàn bộ dữ liệu.

## 5. Ba thao tác trực tiếp, không bắt lập phiếu

Dùng popup ngắn, ô chọn có tìm kiếm, không quick-create nhân viên hoặc thiết bị
trong luồng gán. Tên/phòng ban/avatar/cấu hình tự lấy theo ID. Một người có thể
giữ nhiều thiết bị; mỗi máy chỉ có một nơi giữ/người giữ hiện tại.

### Gán thiết bị

Từ thanh công cụ hoặc dòng máy Trong kho: chọn nhân viên HR đang hoạt động,
chọn một hoặc nhiều máy có sẵn **trong kho và chưa có người giữ**, xem tóm tắt
rồi **Xác nhận gán**. Không có chế độ hiện/chọn máy đang có người giữ.
Mỗi lựa chọn máy hiện mã, tên, cấu hình ngắn, tình trạng; không nhập lại dữ liệu.
Nhân viên không cần có tài khoản đăng nhập. Không giới hạn chỉ KH-KD: chọn được
nhân viên bất kỳ thuộc phạm vi công ty admin được quản lý.

Máy hỏng/ngừng quản lý/đang sửa/chờ giao không thể cấp. Máy chưa kiểm tra có
cảnh báo xác nhận rõ theo guard hiện tại; không âm thầm đánh dấu đã xác minh.
Máy đang có người giữ phải thu hồi thực tế bằng Trả về kho trước; không chuyển
trực tiếp từ người cũ sang người mới trong giao diện đơn giản này.

### Đổi máy

Từ máy đang dùng hoặc tìm nhân viên: hiện máy hiện tại, chọn rõ máy cũ cần đổi,
chọn máy thay thế từ danh sách **chỉ gồm máy trong kho và chưa có người giữ**.
Đây là điều kiện bắt buộc, không phải bộ lọc mặc định có thể bỏ. Domain tối
thiểu là `tp_custody = stock` AND `tp_employee_id = False`, cùng điều kiện
company/vòng đời/tình trạng/chờ bàn giao hợp lệ. Máy ghi stock nhưng còn người
giữ do dữ liệu không nhất quán cũng bị loại và báo cần xử lý dữ liệu; không
tự xóa người giữ để làm máy đủ điều kiện.
Nếu nhân viên giữ nhiều máy, chỉ thu hồi máy được chọn; không thu hồi cả bộ máy
một cách ngầm định. Máy thay thế đã có người giữ, kể cả người nhận hiện tại
hoặc nhân viên nghỉ việc, đều không được chọn. Không cho đổi chéo máy có chủ.

Ví dụ thao tác cho người dùng tự thực hiện:
`Thuỳ Anh đang giữ máy A → chọn máy B trong kho → Xác nhận đổi máy`.
Kết quả: A về kho, bỏ người giữ; B gán Thuỳ Anh; danh sách/HR chi tiết/lịch sử
cập nhật cùng nguồn. Đây là ví dụ hướng dẫn, không tự đổi máy thật để quay demo.
Chặn chọn A làm B. **Một lần xác nhận, một transaction**: lỗi ở bước nào phải
rollback cả trả A và gán B, không để người dùng mất máy hoặc có phiếu dở dang.

Nếu không có máy đáp ứng, hiển thị Không có thiết bị trong kho chưa được gán;
không mở rộng danh sách sang máy có chủ. Nếu B vừa được admin khác gán trước
khi xác nhận, báo Thiết bị đã có người sử dụng hoặc không còn trong kho,
vui lòng chọn thiết bị khác; A và toàn bộ lịch sử/phiếu phải giữ nguyên.

### Trả về kho

Từ dòng máy hoặc nhân viên: chọn chính xác thiết bị cần thu hồi, lý do ngắn
(Đổi máy / Nghỉ việc / Thu hồi khác; có ô ghi chú), xem tóm tắt, xác nhận.
Thiết bị về stock, bỏ liên kết người giữ hiện tại, giữ lịch sử và tình trạng
kỹ thuật; không tự sửa máy thành Tốt. Nhận lại được thiết bị đang hỏng và
thiết bị của nhân viên đã lưu trữ/nghỉ việc. Có thể thu hồi nhiều thiết bị
được chọn trong một lần; lỗi phải rollback toàn bộ thao tác đã xác nhận.

Khóa tài khoản/lưu trữ HR **không chứng minh máy đã trả**. Không auto trả kho
khi khóa/xóa nhân viên. Hiện cảnh báo Người đã nghỉ/cần thu hồi, vẫn thấy máy
cho đến khi admin xác nhận đã nhận. Không thay quy tắc xóa/lưu trữ HR trong task.

Không có nút Chuyển người dùng trực tiếp trong UI mới. Chuyển cho nhân viên
khác thực hiện Trả về kho rồi Gán thiết bị. Backend/phiếu điều chuyển lịch sử
vẫn giữ, không xóa model hoặc sửa nghĩa dữ liệu cũ.

### Backend cho cả ba thao tác

Tái sử dụng `maintenance.equipment`, `tp.equipment.move`, `.line`,
`action_done()`/guard hiện có. Source hiện cho phép hoàn tất phiếu hợp lệ từ
draft, vì vậy không bắt người dùng đi qua Nháp → Chờ giao → Hoàn tất trên UI.
Nếu cần helper/wizard điều phối, thêm nhỏ trong chính addon; không framework mới.

- Một RPC nghiệp vụ cho toàn bộ thao tác; không ghép trả/gán bằng hai RPC từ JS.
- Kiểm admin, company, người nhận active, state, version của cả máy cũ/mới.
  Khóa các máy theo thứ tự ID ổn định, kiểm lại sau khóa; chỉ chọn domain ở UI
  không đủ bảo vệ khỏi dữ liệu cũ hoặc RPC trực tiếp.
- Luồng Gán/Đổi kiểm bắt buộc máy nhận đang stock và không có người giữ sau khi
  khóa, trước khi trả máy cũ. RPC cố truyền ID máy có chủ phải bị từ chối dù
  người gọi là admin; không tự biến thành transfer/thu hồi máy người khác hoặc
  cho override xác nhận để vượt điều kiện. Các guard khác vẫn giữ nguyên.
- Retry cùng request/idempotency key và cùng payload trả lại cùng kết quả,
  không sinh phiếu trùng; dùng lại key với payload khác phải báo xung đột.
- Xung đột hiển thị Máy đã thay đổi, vui lòng tải lại; không ghi đè người giữ.
  Hủy popup không tạo phiếu/đổi state; lỗi không commit một nửa.
- Backend tạo lịch sử/phiếu tự động: ai, lúc nào, từ ai/ở đâu đến ai/ở đâu,
  thiết bị/version, lý do và request. Không cho JS tự ghi custody/employee/state.
- Đổi máy gắn được hai vế vào cùng yêu cầu để truy vết; không xóa phiếu cũ.
  Giữ hạn chế quyền file/chatter/export và không dùng `sudo` để bỏ guard.

## 6. Chi tiết thiết bị và tạo mới

Chi tiết có `← Quay lại` dùng chuẩn chung, giữ nguồn lọc/vị trí; nút Sửa,
Gán/Đổi máy/Trả kho theo trạng thái thực và quyền backend.
Nội dung: ảnh/icon + mã/tên; khối Người đang dùng/Phòng ban/Trạng thái;
loại/hãng/model/serial/cấu hình; tình trạng + ghi chú hỏng; lịch sử thu gọn.
Không cho sửa tay người giữ/custody trong form để né action.

Thêm thiết bị là form ngắn, tối thiểu tên/loại, thông tin nhận diện/cấu hình,
tình trạng/ghi chú; mã do hệ thống cấp. Giữ validation đăng ký hiện tại, serial
không bịa, chưa biết không đổi thành 0. Nếu có bước đăng ký cần thiết, thực hiện
qua backend trong nút lưu hợp lệ, không bắt mở thêm tab Phiếu nhập.
Không tự tạo máy mới khi người dùng chỉ định gán máy có sẵn.

## 7. Yêu cầu đề xuất

Tái sử dụng `tp.equipment.proposal` và `.line`, không tạo Request/BASE mới.
Admin ghi nhận đề xuất thay nhân viên, chưa mở portal/self-service/quyền non-admin.
Danh sách có mã, người đề xuất, phòng ban, ngày, nội dung, trạng thái rà soát,
Xem. Tìm/lọc người, phòng, loại nhu cầu, ngày, trạng thái đúng backend.

Form ngắn: chọn nhân viên, phòng ban tự lấy; nhu cầu Mua mới/Đổi máy/Sửa hoặc
nâng cấp; loại máy, số lượng cần, lý do, thiết bị hiện tại nếu liên quan, file
kèm nếu có. Đổi máy ánh xạ đúng loại nghiệp vụ hiện có; không tùy tiện đổi nghĩa
của dữ liệu nguồn. Giá dự kiến chỉ là ước tính, không bắt nhập nếu chưa biết.

Hiển thị gọn các action rà soát đã có: Lưu nháp, Gửi, Trả lại có lý do, Gửi lại,
Hoàn tất rà soát theo state. Không thêm hàng loạt nút duyệt BASE/mua hàng/kế toán.
Không gộp review/approval/execution thành một trạng thái giả. Hồ sơ cũ, dòng
nguồn, giá trị và căn cứ duyệt giữ nguyên; chưa xác minh phải ghi đúng như vậy.
Hoàn tất rà soát không có nghĩa Đã mua/Đã duyệt/Đã cấp. Không tự tăng tồn, tạo
máy hoặc gán thiết bị khi chỉ ghi đề xuất; việc cấp máy làm ở mục Thiết bị.

## 8. Giao diện đơn giản nhưng chỉn chu

Giữ light theme và shell/sidebar/avatar chung với HR/KH-KD. Không dựng navbar
thứ hai. Tái sử dụng token sẵn có: nền xám sáng, bảng trắng có đường chia cột/
hàng rõ, chữ dễ đọc, input viền rõ, header sticky; tên dài không đè ô kế bên.
Xanh dương cho đang sử dụng, xanh ngọc cho trong kho, cam cho cần kiểm tra,
đỏ cho hỏng/cảnh báo. Badge luôn có chữ; không dùng mỗi màu để truyền nghĩa.

Nút chính rõ, nút nguy cơ tách biệt, toolbar gọn; hover nhẹ, popup/notification
150–200ms, tôn trọng reduced-motion. Không animation vô hạn, không thêm chart
chiếm chỗ hoặc thư viện mới chỉ để làm đẹp. Desktop/tablet/mobile dùng được,
bảng cuộn ngang trong vùng riêng, popup không vượt viewport, focus/keyboard rõ.
Loading/empty/lỗi nói rõ và có hướng xử lý; sau lưu refresh đúng list/counter/
chi tiết, không cần F5, không mất bộ lọc hay nhảy sang phân hệ khác.

## 9. Tiêu chí bàn giao và giới hạn xác minh

Ghi các tiêu chí hành vi trước code; người dùng đã bỏ cổng chạy bộ test/18079
cho Kho, không tự thêm lại. Vẫn lint Python đã sửa, parse XML/manifest/JS phù
hợp, kiểm upgrade/assets và quan sát 18069 bằng phiên browser riêng, chụp ảnh
trước/sau danh sách, chi tiết, popup gán/đổi/thu hồi và đề xuất.
Đọc DOM trước thao tác; không tạo fixture, đổi máy thật, xác minh nguồn hay
gửi đề xuất thật chỉ để có ảnh/đánh PASS. Hủy popup không đổi DB. Không mô phỏng
giao dịch rồi rollback trên main để giả như chưa đụng dữ liệu (sequence có thể tăng).

Checklist để đối chiếu triển khai và hướng dẫn người dùng nghiệm thu:

1. Chỉ hai menu; mở Kho vào Thiết bị; menu cũ/back/deep link không lỗi.
2. Thiết bị hiện đúng người/phòng HR; stock không có người giữ giả; dữ liệu
   dùng chung/chưa rõ/ngừng quản lý không bị mất do thu gọn UI.
3. Gán chọn máy trong kho chưa có người giữ/HR có sẵn; nhân viên không cần
   login; một người giữ nhiều máy. Không có nút chuyển trực tiếp.
4. Đổi A sang B: B bắt buộc stock và không có người giữ; một xác nhận, A về
   kho/B sang người nhận. B có chủ (kể cả cùng người hoặc người nghỉ việc),
   không còn stock, dữ liệu stock nhưng vẫn có người giữ, hoặc bị gán trong
   lúc popup đang mở đều bị từ chối; A không đổi, không sinh phiếu dở dang.
5. Trả kho có lịch sử; nghỉ việc không tự giả đã thu hồi; muốn chuyển cho
   người khác cần trả kho thực tế rồi gán. Không có máy hợp lệ thì báo rõ.
6. Máy đã được admin khác gán, version cũ, key retry/payload khác, company khác,
   non-admin và máy hỏng/chờ giao phải bị xử lý đúng tại backend.
7. Đề xuất ghi/tra cứu được, không tự duyệt/mua/tạo tồn; giữ hồ sơ cũ.
8. Bộ lọc/count/Excel cùng tập, popup hủy không đổi dữ liệu; HR/KH-KD/shell vẫn dùng được.

Mục nào chỉ đọc source, chỉ xem UI hoặc chưa chạy giao dịch phải ghi đúng mức
bằng chứng; không đánh tất cả PASS. Nêu rõ chưa chạy bộ test/giao dịch/race nếu
đã bỏ qua; hướng dẫn admin tự xác nhận nghiệp vụ sau khi xem giao diện.

Cập nhật README addon, hướng dẫn và acceptance Kho, schema/access nếu đổi,
filter inventory, runbook nếu cần; `PROJECT_STATUS`, `CHANGELOG`, `ROADMAP` và
prompt index. Decision mới chỉ ghi điều người dùng đã xác nhận, không bịa duyệt.
Chạy `git diff --check`, `scripts/ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN`
với kết quả thực chạy và `scripts/ai_workflow.py check`.

Báo cáo cuối ngắn: đã áp 18069 hay chưa, phiên bản/file chính, menu đã bỏ,
backup ở đâu, số lượng dữ liệu trước/sau và mọi thay đổi có chủ ý; kết quả
thực kiểm/giới hạn, ảnh private, URL mở và hướng dẫn 3 thao tác. Không commit/push.
