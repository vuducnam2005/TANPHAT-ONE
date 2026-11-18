# TANPHAT ONE — Sổ quyết định

## DEC-057 — Một phiên web hoạt động, đăng nhập mới thay phiên cũ (18/11/2026)

- **Yêu cầu trực tiếp:** mỗi tài khoản chỉ đăng nhập một nơi; đăng nhập nơi
  mới thì máy đang dùng báo tài khoản được đăng nhập ở nơi khác và có nút
  Đăng nhập lại; sau xác thực lại vào Trang chủ.
- **Cách triển khai:** một phiên browser/PWA cho mỗi database/user, nhiều
  tab cùng cookie không đá nhau. Browser/profile/thiết bị có phiên khác là
  login mới; không nhận diện phần cứng bằng IP hoặc dùng tên login nối DB.
- Chỉ thay sau xác thực thành công/MFA hoàn tất, giữ guard HR lock/admin,
  identity recheck và nguồn admin gốc; login sai/refresh/cron/API integration
  không thay winner. Áp cả admin gốc và admin được cấp, không tự đổi quyền.
- Backend thu hồi ngay khi giao dịch mới commit và chặn truy cập cookie cũ;
  bus báo đúng đời phiên, fallback khi online/focus. Máy offline nhận khi
  kết nối lại, không hứa báo tức thì; old logout không được xóa phiên mới.
- [Prompt](prompts/CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md) có race,
  cache/JSON-RPC/API/file, no-mutation-replay, cutover legacy và rollback.
  Đây mới là policy/prompt, chưa sửa code/DB hoặc thu hồi phiên người thật.
  Thực thi giao18069/PCserver theo policy17/11, không bắt18079.


## DEC-056 — Nhập Excel máy tự tạo bảng công, giữ tổng đi muộn nguồn (18/11/2026)

- Người dùng chưa thực thi prompt002; bổ sung vào cùng bản. Kéo-thả/chọn
  Excel xuất máy, hệ thống tự nhận kỳ và nhân viên, xem trước rồi nhập;
  không buộc gõ từng dòng hoặc chuyển template. Hỗ trợ1–3tuần/tháng và phạm
  vi hợp lệ, không cố định7cột hoặc vị trí cột Đi muộn.
- Chốt cuối của người dùng: **08:30–17:00** (thay17:30 vừa nói trước đó),
  **giữ số lần/phút đi muộn trong Excel**, không tính lại theo giờ vào.
  Chưa có dữ liệu từng ngày thì không chia/copy tổng kỳ xuống ngày; số muộn
  phải có kỳ/nguồn, không cộng lặp hoặc chồng tuần-tháng.
- Đã đọc file riêng:39người,kỳ09–15/11; hai dòngVào/Ra, có nhómĐi muộn/Lần/
  Phút. Parser hiện nhận giờ nhưng bỏ tổng; kết quả đọc không là importDB.
  Mã máy dùng mapping HR, không ghép tên hoặc nhầm mãTP00x vớiTP100xx.
- UI gọn: ngày/chi tiết chỉ nhận diện cần thiết và thứ-ngày/giờ vào/ra;
  tổng kỳ chỉ nhận diện và số lần/tổngphút. Không hiện côngngàyđêm/tăngca/
  tổnggiờ/vềsớm/lương; không xóa model/lịch sử đang dùng. Giờ thiếu vẫn
  hiện giờ có thật, không tạo giờra hoặc suy nghỉ từ ôtrống.
- Bổ sung DEC-055; dashboard/ngày-tuần-tháng/API-ready/privacy/quyền admin
  DEC-053/054 giữ nguyên. Mới prompt/tài liệu, chưa application hoặc import.


## DEC-055 — Chấm công gọn theo ngày/tuần/tháng, API máy chuẩn bị sau Excel (18/11/2026)

- **Yêu cầu trực tiếp:** một dashboard tổng nhân viên, người nghỉ hôm nay và
  người đã về, quản lý theo ngày/tuần/tháng; dữ liệu Excel đã import được giữ.
  Chuẩn bị điểm tích hợp API máy để dữ liệu về web trực tiếp về sau.
- [Prompt SIMPLE002](prompts/CLAUDE_HR_ATTENDANCE_SIMPLE_002_DASHBOARD_AND_API_READY.md)
  tái sử dụng addon/day/session/mapping HR và cùng DB. UI gọn, sáng, chart rõ,
  filter/list/drilldown cùng nguồn. Các chức năng nâng cao đã có chỉ chuyển
  khỏi menu thường nếu cần, không xóa bảng/data/workflow/lịch sử.
- Định nghĩa trong prompt là hướng triển khai dựa nguồn: nghỉ phải có xác nhận,
  không chấm/nguồn cũ không là nghỉ; latestOUT/IN lại và lịch đủ căn cứ mới xác
  định Đã về, nếu chưa đủ chỉ Đã ghi nhận ra. Phải hiển thị ngày/mốc nguồn và
  không dùng ngày Excel cũ như hôm nay/realtime; người khác đơn vị ngày-người.
- Model session hiện bắt cảIN/OUT nên API-ready phải nhận được punch đơn;
  contract/normalizer/adapter chung là phạm vi chuẩn bị. Chưa có hãng/API/auth/
  chiều sự kiện/lịch ca/network: liveconnector mặc định tắt, không publicwrite
  hoặc giả kết nối. Không làm data lake, payroll, sinh trắc hoặc nghỉ phép phức tạp.
- DEC-053/054 về admin vẫn giữ; không tự cấp quyền trong task chấm công.
  Mới viết prompt/policy, chưa triển khai hoặc nhập lại dữ liệu. Thực thi giao
  từng phần lên18069/PCserver theo policy17/11, không bắt18079/clone/fixturemain.

## DEC-054 — Chỉ admin gốc được cấp hoặc thu hồi admin (18/11/2026)

- **Bổ sung trực tiếp:** admin được cấp không có quyền phân người khác làm
  admin; chỉ admin thật/admin gốc được thực hiện. Đây là ngoại lệ mới của
  DEC-053; không khôi phục ranh giới phòng ban DEC-050.
- Admin được cấp vẫn toàn quyền quản trị nghiệp vụ mọi phòng, kể cả phòng
  mình. Quản lý tài khoản thường/vai trò nghiệp vụ không được làm phát sinh
  admin trực tiếp hoặc gián tiếp. Chỉ admin gốc cấp/thu admin và sửa nguồn
  xác định admin gốc; admin được cấp không tự cấp, cấp tiếp hoặc thu admin khác.
- Bắt buộc kiểm actor admin gốc ở backend, không chỉ ẩn nút hoặc xét nhóm
  system chung. Chặn ledger/group/implied/nested/import/API/sudo và việc
  chiếm credential/source admin gốc. Công cụ sửa security/chạy code/cài module
  có thể vòng qua ngoại lệ này dành admin gốc; nghiệp vụ không bị hạn chế phòng.
- [Prompt ADMIN-FULL-001](prompts/CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md) đã sửa
  tại cùng file; đoạn cũ cho admin thứ hai cấp tiếp không còn hiệu lực.
  Giữ migration grant đang hiệu lực khi giao Claude thực thi, provenance và
  thu hồi về quyền nghiệp vụ hợp lệ. Lượt chốt này chưa sửa runtime/người thật.

- **Triển khai runtime ADMIN-FULL-001:** Đã áp tại `custom_addons/tp_admin_delegation` `20.0.2.0.0` trên cả `18069` và `PC server` (commit ứng dụng `bec79ccb`, `CHG-20261118-012` / `CHG-20261118-015`, backup `18069` `.local/admin-full001/backup-af001-20261118T120130` & `PC server` `C:\TANPHAT-backups\admin-full001\af001-20261118T122710`; đã nâng tự động `uid=43` sang `group_full_admin`, seed `group_original_admin` cho `uid=2`; xem [nghiệm thu](demo/ADMIN_FULL_001_ACCEPTANCE.md)).

## DEC-053 — Người được cấp admin có toàn quyền như admin hiện tại (18/11/2026)

- **Yêu cầu trực tiếp mới:** tài khoản được cấp quyền admin là admin thứ hai,
  toàn quyền như admin thật, không ràng buộc phòng ban. Áp cả phòng của chính
  họ, phòng khác, dữ liệu chung và chức năng quản trị mà admin hiện tại có.
- **Thay DEC-050 ở phần xung đột:** bỏ own-department baseline và chỉ-other-
  department khi user đã là full admin; không giữ nhãn delegate nhưng quyền
  thực chỉ đọc/adapter hạn chế. **Ngoại lệ theo bổ sung DEC-054:** admin được
  cấp không cấp/thu quyền admin; chỉ admin gốc quản lý thẩm quyền đó. Các
  nghiệp vụ và phòng ban còn lại vẫn theo DEC-053.
- Chức danh/phòng nhân viên không tự đổi khi cấp admin. Thu hồi bỏ quyền admin
  được quản lý và giữ quyền nghiệp vụ hợp lệ. Workflow/validation mà admin
  hiện tại cũng phải tuân thủ và bảo vệ user hệ thống/admin cuối vẫn giữ.
  Không phải cấp UID1/SSH/PostgreSQL hay bỏ quyền riêng tư của nhân viên thường.
- Người dùng giao viết [prompt triển khai](prompts/CLAUDE_ADMIN_FULL_001_SECOND_ADMIN.md).
  Khi giao Claude thực thi, chuyển các grant hiện đang hiệu lực sang mô hình
  full admin theo yêu cầu này; không tạo thêm người hoặc tự chọn user mới.
  Native groups/quyền phải có nguồn gốc để thu hồi đúng, không restore snapshot
  nhóm cũ đè thay đổi vai trò hợp lệ trong lúc là admin.
- **Trạng thái:** chính sách đã được người dùng chốt; lượt này mới tài liệu,
  chưa đổi application, nhóm người thật, grant hoặc dữ liệu. Policy17/11 tiếp
  tục áp: push/deploy từng phần hoàn tất, không bắt18079; backup/kiểm/rollback.

## DEC-048 — Báo cáo toàn công ty dùng chung dữ liệu và luồng tổng hợp (16/11/2026)

**Bổ sung trực tiếp CHG-20261116-006:** người dùng yêu cầu viết prompt triển khai
**full module**, gồm dashboard sáng/đẹp với biểu đồ lớn rõ, hover/animation,
bảng không chồng chéo và bộ lọc theo nội dung trên mọi tab; dữ liệu đồng bộ
cùng một DB trong từng môi trường. Được đề xuất/thực hiện thêm tính năng hữu
ích phù hợp module. [Prompt thực thi R0–R5](prompts/CLAUDE_CORP_REPORT_001_FULL_MODULE.md)
đã lưu; lượt điều phối chưa triển khai code. Các default lịch/thẩm quyền kỹ
thuật dùng cho cấu hình/test không phải policy/grant người thật. Chưa có yêu
cầu áp module Báo cáo lên main18069; ngoại lệ Kho không tự mở rộng.

**Bổ sung trực tiếp CHG-20261116-005:** phải đề ra mục tiêu quý trước, phân rã
thành kế hoạch tháng rồi kế hoạch tuần. Kế hoạch đi quý → tháng → tuần;
kết quả tổng hợp tuần → tháng → quý để đối chiếu mục tiêu. Mỗi kế hoạch con
liên kết cha, có người chịu trách nhiệm/đầu ra/hạn; công ty-phòng-cá nhân là
trục phân công, không đồng nhất với ba loại kỳ. Không tự chia đều chỉ tiêu,
ghi đè baseline hoặc coi việc phát sinh là mục tiêu gốc đã hoàn thành. Đề xuất
lộ trình cập nhật R0–R5: xây mục tiêu/phân rã trước báo cáo; kế hoạch được chốt
và điều chỉnh theo quyền có lịch sử, chi tiết thẩm quyền cần xác nhận.

- **Yêu cầu trực tiếp:** phân tích hai báo cáo Word, định hướng phân hệ báo cáo
  cho mọi phòng ban, cá nhân/trưởng phòng/phòng và lãnh đạo xem theo tuần,
  tháng, quý; dữ liệu đồng bộ toàn hệ thống.
- **Đã xác nhận qua trả lời trong chat:** nhân viên nộp báo cáo tuần; cá nhân
  lập tháng/quý khi được yêu cầu; trưởng phòng tổng hợp phòng/nộp tháng-quý;
  lãnh đạo xem, nhận xét và giao việc tiếp theo. Cho người phụ trách nhập số
  tài chính tổng hợp chưa có trên Odoo, kèm nguồn và xác nhận, chỉ người có
  quyền phù hợp được xem. Chưa xác nhận lịch nộp, reviewer/publisher hay grant
  cho tài khoản lãnh đạo cụ thể.
- **Thiết kế đề xuất:** [CORP-REPORT-001](architecture/TP_COMPANY_REPORTING_001_DESIGN.md),
  một chức năng Báo cáo native/cùng DB/identity, mẫu chung và section đặc thù
  phòng; source tự động + số nhập có nguồn + nhận xét, lưu phiên bản đã gửi/
  chốt. Addon `tp_reporting`, UI/schema/role/state/lộ trình R0–R5 là đề xuất,
  chưa code hoặc coi là policy doanh nghiệp đã ban hành.
- **Ranh giới:** báo cáo tháng Phòng Thiết kế và báo cáo SXKD 9 tháng cấp công
  ty có phạm vi khác nhau; 9 tháng là lũy kế, không là quý III. Giữ phân biệt
  sản lượng/nghiệm thu/đề nghị thanh toán/doanh thu/thực thu. Quyền báo cáo
  không tự mở source/files/tiền/HR; không phê duyệt nghiệp vụ gốc từ báo cáo.
- **Trạng thái:** CHG-20261116-004/005 phân tích, CHG-006 lưu prompt full module;
  chưa triển khai/nhập Word,
  đổi runtime/DB/user/quyền hoặc deploy. Ngoại lệ main trực tiếp của Kho không
  tự áp sang task Báo cáo. Luồng Kho CHG-003 còn chờ admin nghiệm thu riêng;
  không commit/push.

## DEC-047 — Kho đơn giản: thiết bị, người giữ và yêu cầu đề xuất (16/11/2026)

**Bổ sung xác nhận CHG-20261116-002, trước khi người dùng chạy prompt:** máy
thay thế chỉ là máy trong kho và không có người giữ hiện tại. Máy có người
giữ không được dùng để đổi/gán, kể cả cùng người hoặc người đã nghỉ việc;
không đổi chéo. Chọn trên UI và xác nhận backend đều bắt buộc cùng điều kiện,
kiểm lại sau khóa/version. Nếu bị gán trong lúc đang chọn, từ chối và giữ máy
cũ nguyên trạng. Thu gọn còn Gán/Đổi/Trả kho; không nút Chuyển người dùng trực
tiếp, cần trả kho thực tế rồi gán cho người khác. Không tự bỏ người giữ hoặc
sửa sở hữu pháp lý để làm máy đủ điều kiện. Lượt này chỉ sửa prompt/docs.

- **Nguồn đã xác nhận:** người dùng yêu cầu viết prompt sửa toàn bộ Kho để biết
  ai dùng máy gì/phòng nào/thông tin máy, chọn thiết bị có sẵn để gán/đổi,
  trả kho khi đổi máy/nghỉ việc, bỏ tab không cần và giữ yêu cầu đề xuất.
- **Thiết kế thực thi trong phạm vi đã giao:** chỉ hai mục `Thiết bị` và
  `Yêu cầu đề xuất`; một bảng thiết bị có bộ lọc Tất cả/Đang sử dụng/Trong kho.
  Gán, đổi, thu hồi bằng popup ngắn; phiếu và lịch sử tự ghi
  qua backend hiện có. Đổi máy là một transaction; chọn HR/máy bằng ID, không
  nhập tên tay hoặc tạo bản sao. Một nhân viên được giữ nhiều thiết bị.
- **Thay phạm vi UI cũ:** bỏ dashboard/tab nghiệp vụ kho sâu khỏi điều hướng
  hoạt động, thay nhóm sidebar Quản trị dữ liệu trong DEC-045/UI-001/UI-002.
  Không xóa bảng/bản ghi/lịch sử/nguồn nhập; trường hợp dùng chung/chưa rõ/sửa
  ngoài/ngừng quản lý vẫn truy cập phù hợp, không ép thành hai trạng thái giả.
  Trả kho không đồng nghĩa máy tốt; nghỉ việc/khóa account không tự giả đã trả.
- **Giữ nguyên:** cùng DB/HR, admin-only, phân quyền backend, DEC-044 bộ lọc và
  DEC-046 Quay lại; chỉ đạo EQUIP main18069 sau backup, không18079/bộ test riêng,
  không fixture/nhập lại; không mở self-service, BASE/mua/duyệt chi/kế toán.
- **Trạng thái:** CHG-20261116-001/002 chỉ [prompt](prompts/CLAUDE_EQUIP_SIMPLE_003.md)
  và tài liệu; chưa triển khai, không thay dữ liệu/quyền/runtime, không commit/push.

## DEC-046 — Quay lại thống nhất ở mọi màn chi tiết (15/11/2026)

- **Yêu cầu trực tiếp:** người dùng muốn nút Quay lại khi mở bất kỳ chi tiết
  nào, áp dụng toàn hệ thống. Hướng sản phẩm đã xác nhận; chi tiết triển khai
  trong [prompt](prompts/CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md) chưa code.
- **Thiết kế giao thực hiện:** một nút cùng format trên native form/custom
  detail đang cài, bao gồm HR/KH-KD/Kho và app/cấu hình có quyền. Reuse action
  stack/breadcrumb để về đúng màn giữ filter/page; fallback deep link đúng
  scope. Popup giữ Đóng/Hủy đúng ngữ cảnh, bảo vệ chưa lưu, không history.back
  mù/forceLeave, không tạo trùng nút HR hoặc cache PII qua logout.
- **Ghi nhớ cho phát triển:** component/helper dùng chung trong addon chung
  hiện có, không sửa core hoặc làm router mới. Inventory từng loại detail,
  coverage và giới hạn trước báo toàn hệ thống; màn mới áp cùng quy ước.
- **Trạng thái:** CHG-20261115-001 lập prompt; CHG-20261115-002 đã triển khai
  trên main 18069 (`tp_web_home` 20.0.1.8.0, `tp_hr_workspace` 20.0.1.11.5),
  quy ước và inventory tại [UI-BACK-001](ui/UI_BACK_001_STANDARD.md). Màn mới
  đăng ký fallback qua `tp_back_fallbacks`, không tự vẽ nút. KH-KD/hợp đồng chưa
  quan sát có dữ liệu; chờ người dùng xem trực quan.

## DEC-045 — Chuẩn bị kho thiết bị văn phòng dùng chung dữ liệu và giao diện (14/11/2026)

**Làm rõ danh sách CHG-20261115-001:** Thiết bị & người sử dụng chỉ gồm máy
gắn nhân viên xác định, không lẫn stock; dùng loại/tình trạng/ghi chú và HR ID/
phòng ban hiện tại. Thiết bị dùng chung/chưa rõ/tồn vẫn còn lối xem phù hợp,
không đổi dữ liệu để tách UI. [Prompt EQUIP-UI-002](prompts/CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md)
thay cách dùng list tổng cho menu người sử dụng trong prompt cũ; kèm nâng tiếp
dashboard và DEC-046 Quay lại dùng chung. Chưa triển khai trong CHG-001;
đã áp main 18069 ở CHG-20261115-002 (`tp_equipment` 20.0.1.4.0): list người sử
dụng 26 dòng có nhân viên HR, menu dùng chung/chưa rõ người và tất cả hồ sơ.

**Điều chỉnh giao diện CHG-20261114-013:** người dùng yêu cầu đơn giản hóa kho,
ưu tiên ai sử dụng/thiết bị tồn/đề xuất mua; giao diện sáng nhiều màu, biểu đồ
lớn ở đầu, bảng rõ không đè ô, filter thiết kế lại và bỏ preset trong ô search.
[Prompt EQUIP-UI-001](prompts/CLAUDE_EQUIP_UI_001_SIMPLIFY_AND_REDESIGN.md)
đề xuất bốn mục chính và nhóm nâng cao đóng; không xóa dữ liệu/chức năng nền.
Đây là phạm vi UI mới, chưa triển khai trong CHG-013. Giữ admin-only, admin
ghi nhận nhu cầu nhân viên; không mở thêm role/portal. Bộ lọc chủ động vẫn theo
DEC-044, chỉ thu gọn trình bày riêng EQUIP; scope/backend không bị xóa khi bỏ
chip mặc định. Giữ chỉ đạo main trực tiếp/backup/không18079 hoặc bộ test.

**Phạm vi nhập mới CHG-20261114-011:** người dùng đã giao nhập dữ liệu thật từ
hai file local `C:\2026_tanphat_cntt_thiet-bi_0611.xlsx` và
`C:\TP_TBCNTT_De xuat mua mới.xlsx` lên main18069; đường dẫn đề xuất gửi lặp
không tạo nguồn thứ ba. [Prompt nhập](prompts/CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md)
thay hạn chế chưa nhập nguồn của lượt code trước trong riêng hai file này.
Backup mới, cùng DB/HR/admin-only, không18079/bộ test theo yêu cầu; apply và
đăng ký phần đủ điều kiện, giữ phần chưa rõ, không biến đề xuất thành tồn hoặc
duyệt mua. CHG-011 mới chuẩn bị tài liệu, chưa nhập hoặc sửa application.

**Chỉ đạo mới nhất CHG-20261114-009:** người dùng yêu cầu triển khai trực tiếp
18069, bỏ môi trường test 18079 và bộ kiểm thử riêng cho EQUIP-001, lỗi phát
sinh sửa trực tiếp. Thay cổng test-first/test-only của prompt cũ trong riêng
task này; không cần hỏi lại quyền áp main. Backup DB+filestore, giữ dữ liệu/
tài khoản, cài/upgrade đúng dependency và mở module admin để xem ngay. Không
tuyên bố đã test khi bỏ test; không tự bulk nhập nguồn thật/tạo fixture, mở
quyền non-admin hoặc duyệt chi/kế toán từ quyền code. Phiên điều phối chỉ sửa
prompt/tài liệu, chưa thực thi deploy trong CHG-009.

**Làm rõ theo yêu cầu tiếp theo, CHG-20261114-007:** một module riêng **Kho thiết
bị văn phòng**, addon `tp_equipment`, thẻ/icon/menu/dashboard/sidebar riêng;
chỉ admin `base.group_system` truy cập/quản lý theo company/scope. HR/KH-KD/
technician/staff không phải admin không được xem/thao tác kể cả qua native RPC,
file/chatter/public HR. Vẫn dùng chung database và liên kết employee/department
gốc. Thay phương án nhiều role/self-service trong bản thiết kế đầu; chưa code.

- **Nguồn yêu cầu đã xác nhận:** người dùng giao đọc hai workbook thiết bị/
  đề xuất mua tại NAS, phân tích kỹ và viết prompt xây kho thiết bị văn phòng,
  dùng chung database/dữ liệu đồng bộ, đủ thao tác và giao diện giống nền HR/
  KH-KD, đẹp/trực quan, có hover/animation. Lượt này là chuẩn bị, không giao phiên
  điều phối sửa application code hoặc nhập dữ liệu thật.
- **Thiết kế đề xuất:** [blueprint EQUIP-001](architecture/TP_EQUIPMENT001_BLUEPRINT.md)
  gồm danh mục/tiếp nhận, cấp–thu hồi–điều chuyển–mượn/trả, sửa/nâng cấp, đề xuất,
  kiểm kê và báo cáo. Tái sử dụng maintenance gốc, cầu nối HR có scope riêng và
  native OWL/QWeb/SCSS; không DB riêng hay danh tính bản sao. Capability, state
  và schema trong blueprint là thiết kế cần AT/test, chưa phải policy công ty.
- **Phân biệt:** dòng đề xuất không là thiết bị đã mua, footer ký không chứng
  minh đã duyệt; còn mapping/thẩm quyền/ngày/serial/giá cần xác minh. Dịch vụ,
  tài sản cá nhân/thuê và thiết bị công ty có ý nghĩa khác nhau. Không mở
  kế toán/khấu hao/thanh toán/phê duyệt chính thức từ hai workbook.
- **Bàn giao ban đầu, cổng môi trường đã được CHG-009 thay thế ở trên:**
  [prompt](prompts/CLAUDE_EQUIP_001_OFFICE_EQUIPMENT.md) cho S0 và EQUIP-001a–e,
  AT-E01–18 nay là tiêu chí hành vi, không bắt viết/chạy test. Phân tích thật ở `.local/`
  ignored; không đưa workbook/raw/PII/IP/giá thật vào Git.

## DEC-044 — Mọi bảng có bộ lọc đúng nội dung, dùng làm cổng cho phòng ban mới (14/11/2026)

- **Nguồn xác nhận:** người dùng yêu cầu tất cả bảng toàn hệ thống có bộ lọc
  riêng theo nội dung, phân tích/viết prompt và lưu để không bỏ sót khi phát
  triển phòng ban khác. Yêu cầu sản phẩm đã xác nhận; chi tiết tương tác/field
  trong đặc tả là phương án triển khai cần kiểm trên source và test.
- **Quyết định:** áp dụng [quy chuẩn](ui/TP_TABLE_FILTER_STANDARD.md) và
  [inventory](ui/TP_TABLE_FILTER_INVENTORY.md) cho list, bảng con, popup,
  smart button, lịch sử, báo cáo và ứng dụng native đang dùng. Một cách thao tác
  chung; tiêu chí theo từng bảng/action, không áp cùng một bộ lọc vô nghĩa.
  Cổng phát triển bảng/phòng ban mới phải có mapping, security, paging/count/
  export, mobile và bằng chứng; ngoại lệ N/A có lý do và role review.
- **Kiến trúc:** kế thừa DEC-030/023, native Odoo và backend enforce scope/quyền;
  tái sử dụng SearchModel/search view/công cụ HR–KH-KD. Không tạo state/engine
  nghiệp vụ, frontend độc lập hoặc mở grant tiền chỉ để thêm filter.
- **Trạng thái:** CHG-20261114-005 chỉ lập tài liệu/prompt `SPEC_READY`, không
  sửa application code/runtime/dữ liệu. [Prompt](prompts/CLAUDE_UI_TABLE_FILTER_001.md)
  giao triển khai trên test 18079 khi người dùng đưa cho Claude; áp main 18069
  là bước được giao riêng. Không thay thế nghiệm thu hình thức/nghiệp vụ/pilot.

## DEC-043 — Thống nhất Trang chủ dùng chung, điểm truy cập danh tính theo ngữ cảnh và UserMenu chỉ còn Đăng xuất (14/11/2026)

- **Bối cảnh:** Trước đây `tp_web_home` tách hai cây giao diện Trang chủ theo `this.isAdmin()` (`UI-HOME-003` cho non-admin và `UI-HOME-004`/`005` cho admin), `UserMenu` còn nhiều mục phụ (`Tài khoản và tùy chọn`, `Hỗ trợ`, `Shortcuts`, `Online`, `My Subscription`, phần lặp tên), đồng thời sidebar HR và KH-KD có nút `"Tài khoản"` mở preferences song song với cụm người dùng trên navbar.
- **Quyết định:**
  1. Dùng một template và hệ lưới Trang chủ thống nhất (`#tp-unified-home`, nền gradient sáng xanh + sóng nhẹ, tiêu đề `"Trang chủ"` / `"Không gian làm việc của TANPHAT ONE"`, lưới 3 cột desktop giữ nguyên kích thước thẻ đơn lẻ); nội dung các nhóm (`Phòng ban và đơn vị`, `Nhân sự và tuyển dụng`, `Công cụ cá nhân`) và công cụ/placeholder quản trị do menu server + `user.isSystem` quyết định; bỏ fallback `hr.menu_hr_root` ở mục `Quản lý nhân sự` để không lộ thẻ HR cho người không có quyền workspace HR. (Cập nhật phần tách layout của `DEC-031`/`DEC-036`, giữ nguyên nguyên tắc quyền backend).
  2. Mỗi màn hình chỉ giữ **một** điểm truy cập danh tính: Trang chủ & ứng dụng native dùng `UserMenu` trên navbar; workspace HR & KH-KD dùng component dùng chung `<TpUserAccountMenu>` ở cuối sidebar (hỗ trợ `.is-rail` và mobile drawer) và ẩn cụm `.o_user_menu` / `.o_mobile_menu_toggle` ở navbar theo class `body.o_tp_hr_shell, body.o_tp_kd_shell`. Không tạo addon mới hay dependency vòng: dịch vụ `tp_identity` và component đặt trong `tp_web_home`.
  3. Dropdown người dùng (navbar, `BurgerUserMenu` và sidebar) trình bày đúng 2 mục theo xác nhận của người dùng: **`Thông tin cá nhân`** (mở màn hình tự phục vụ `tp_hr_workspace.action_my_profile` tại `/odoo/my-profile` qua registry `tp_personal_profile`, fallback `res.users` `action_get` cho tài khoản chưa gắn nhân sự; cho phép nhân viên xem toàn bộ 6 tab kể cả hợp đồng ở chế độ chỉ đọc + tải bản lưu của chính mình qua `/tp_hr/my_contract/...`, đồng thời chỉnh sửa các trường cá nhân trong allowlist và đồng bộ trực tiếp về hồ sơ `hr.employee` + ảnh đại diện của Admin HR; khóa chặt `Họ tên`, `mã NV`, `phòng ban`, `chức vụ`, `hợp đồng`, `phân quyền` ở backend) và **`Đăng xuất`** (`performNativeLogout()`, tái sử dụng `/web/session/logout` + CSRF + service worker, giữ nguyên `im_status` & systray).

## DEC-042 — Xóa vĩnh viễn nhân viên có xác minh lại mật khẩu quản trị (12/11/2026)

Yêu cầu trực tiếp HR-DELETE-010, không commit/push. Thay DEC-041 phần “chỉ xóa
hồ sơ nhập nhầm”: admin chủ động chọn hồ sơ → Tác vụ → “Xóa vĩnh viễn nhân viên”
xóa thật `hr.employee` (không lưu trữ, không còn trong danh sách đang dùng/lưu
trữ, tìm kiếm, xuất dữ liệu). “Lưu trữ” vẫn là thao tác riêng; xóa không bao giờ
tự đổi thành lưu trữ. Nguồn Excel, mã nguồn và sidecar tự sinh không chặn xóa.
Mã/ưu tiên mã nhân viên của DEC-041 giữ nguyên: mã TP đã xóa không bao giờ cấp lại.

Quyền: chỉ `base.group_system` có quyền quản lý nhân sự, hồ sơ trong công ty đang
chọn, phiên HTTP hợp lệ của chính tài khoản đó; không nhận cờ admin từ frontend.
Mật khẩu: admin đang đăng nhập nhập lại mật khẩu của chính mình trong yêu cầu cuối
cùng; backend gọi native `_check_credentials` bên trong native `_assert_can_auth`
(dùng chung giới hạn thử sai/cooldown của đăng nhập), mỗi lần xóa kiểm lại, không
dùng lại 10 phút của `check_identity`, không ghi timestamp xác minh chung. Mật
khẩu chỉ ở state giao diện và request kiểm tra, xóa khỏi state khi gửi/đóng; không
lưu DB/transient/context/log/audit/URL.

Quan hệ: dòng sở hữu (phiên bản hồ sơ, kỹ năng, quá trình, địa điểm, nghỉ việc,
resource) và chatter/người theo dõi/hoạt động/tệp/xmlid của chúng bị xóa qua ORM,
không xóa blob vật lý trực tiếp. Dòng nhập, lô và file Excel giữ (dòng chỉ bỏ liên
kết, giữ mã nguồn); nhập lại danh tính đã xóa thành xung đột. Liên hệ công việc
riêng không còn dùng thì xóa, còn dùng thì giữ. Dữ liệu nghiệp vụ độc lập (quản lý
trực tiếp, quản lý phòng ban, chấm công, chi phí...) chặn kèm model, số lượng và
gợi ý; không gỡ FK, không cascade, không tự đổi người phụ trách.

Tài khoản: mặc định giữ nguyên; nếu tài khoản còn vai trò/phân công/quyền dự án,
KH-KD hoặc nhóm kinh doanh thì phải chọn “Xóa hồ sơ và khóa tài khoản” (khóa,
tăng revision để kết thúc phiên, tắt vai trò/phân công/quyền trong công ty, gỡ
nhóm nhân viên phạm vi) hoặc hạ quyền trước. Không khóa/xóa tài khoản hệ thống,
root, admin, chính mình hoặc có công ty ngoài phạm vi; không xóa tài khoản.

Thực thi: preview có digest; yêu cầu cuối khóa advisory theo công ty và `FOR
UPDATE` hồ sơ/resource/tài khoản, tính lại kế hoạch, so với preview và dữ liệu đã
commit (cursor đọc riêng); lệch thì từ chối cả lô. Lô một xác nhận, tất cả-hoặc-
không; `request_id` duy nhất cho mỗi hộp thoại nên bấm lặp/thử lại không xóa hai
lần. Audit bền vững (`tp.hr.employee.audit`, không FK) ghi người làm, lý do, mã,
mã nguồn, phòng/chức vụ, tài khoản và lựa chọn, phần đã xóa/giữ, request; không
ghi mật khẩu hoặc toàn bộ thông tin cá nhân; không ai sửa/xóa audit.

## DEC-041 — Xóa hồ sơ nhập nhầm, mã nhân viên và mật độ giao diện (12/11/2026)

> Phần xóa hồ sơ của quyết định này được thay bằng DEC-042 (HR-DELETE-010); phần mã nhân viên và mật độ giao diện giữ hiệu lực.

Yêu cầu trực tiếp HR-CORRECTION-008, không commit/push. Hồ sơ nhân viên chỉ xóa
vĩnh viễn qua “Xóa hồ sơ nhập nhầm”: admin hệ thống cùng công ty, backend kiểm
từng hồ sơ, lý do bắt buộc, lô tất cả-hoặc-không, audit độc lập còn sau khi xóa.
Chỉ hồ sơ nhập tay chưa dùng (không roster/tài khoản/vai trò/phân công/quyền/tài
liệu/trao đổi/lịch sử/tham chiếu); còn lại lưu trữ. Không Delete native, không
context bypass, không cascade user/partner/tài liệu/nghiệp vụ. Lưu trữ tách khỏi
khóa tài khoản.

Mã nhân viên `TP` + số: mã hợp lệ cao nhất (gồm lưu trữ và audit) + 1, không dùng
ID, không đánh lại, không tái dùng, chấp nhận khoảng trống; mã roster giữ. Mã sai
chỉ sửa cho hồ sơ nhập tay chưa dùng, có audit; xung đột chỉ báo cáo.

Việt hóa qua catalog/template Odoo, không thay chữ DOM lúc chạy; tên sản phẩm,
mã, login giữ. Thu gọn bằng token SCSS dùng chung, không zoom/scale/root font;
sidebar giữ nguyên; mobile ≥44px. Chi tiết:
[acceptance](demo/HR_CORRECTION_008_ACCEPTANCE.md).

## DEC-040 — Danh tính chung và chuyển phòng tức thời (12/11/2026)

Yêu cầu trực tiếp IDENTITY-ORG-001 cho phép phiên chính triển khai/test/backup/
restore kiểm chứng/áp main, không commit/push; ngoại lệ điều phối chỉ task này.
HR quản lý tên chính thức/phòng/chức vụ hiện hành; user/partner giữ danh tính
tài khoản, không đổi login/auth. Ảnh hai chiều qua mapping ID duy nhất, giữ ảnh
thật; xung đột cần admin chọn. Không public private_email hoặc sửa partner khách.

Admin chuyển phòng qua preview/lý do/locks/audit nguyên tử, default staff, HEAD
chọn rõ/unique incumbent. Mặc định revoke HEAD cũ và kết thúc scope cấp riêng;
kiêm nhiệm chỉ giữ sau xác nhận. Workspace là cửa vào, data/tiền theo capability.
History/future không làm đổi scope current; chưa điều chuyển hẹn ngày/khác công ty.
Menu/action/backend/session enforce cùng scope, không cần restart mỗi chuyển.
Nguồn, giới hạn và kết quả: [identity](architecture/TP_IDENTITY_ORG_001.md).

Ghi quyết định hiện hành, lý do và phạm vi. Khi thay đổi, thêm bản thay thế và chỉ rõ quyết định bị thay; không sửa lịch sử thành điều chưa từng được chọn.

## DEC-039 — Tài khoản cá nhân và quản trị HEAD trong HR (12/11/2026)

**Tinh chỉnh CHG-20261112-007:** yêu cầu trực tiếp chỉ đặt Đổi chức vụ trong
chi tiết nhân viên, bỏ khỏi danh sách. Mỗi company/phòng chỉ một HEAD active;
phải hạ người hiện tại trước khi bổ nhiệm nhân viên khác, không tự thay thế.
Wizard báo rõ người hiện tại, kiểm preview/apply và unique index ở backend
chặn cả provisioning trực tiếp/reactivation/race. Role chưa thu hồi vẫn giữ
vị trí dù user khóa hoặc ngày hiệu lực chưa tới/hết; job HR không tự cấp quyền.
Không thay role/chức vụ người thật để test, giữ ngoại lệ thực thi trong task HR.

**Tinh chỉnh CHG-20261112-006:** phản hồi "nâng/hạ chức vụ ở đâu, làm dễ hiểu"
đưa Đổi chức vụ ra danh sách và đầu hồ sơ. Tái dùng role wizard, tách rõ đổi
chức vụ HR (lý do/preview/audit, không đổi quyền, dùng được khi chưa account)
và Bổ nhiệm/Chuyển về nhân viên KH-KD (quyền backend hiện hành, optional đổi
cả chức vụ nguyên tử). Không mở ma trận quyền phòng khác hoặc suy quyền theo
tên chức vụ. Tiếp tục quyền thực thi/test/áp main trong cùng task HR.

**Tinh chỉnh theo phản hồi người dùng — CHG-20261112-005:** form tạo tài khoản
có tên đăng nhập, mật khẩu và nhập lại mật khẩu trên cùng màn hình, nhãn/chú
thích rõ và thông báo tiếng Việt. Xác thực danh tính Odoo trước khi nhập mật
khẩu mới; submit kiểm session native còn hiệu lực, tạo user/password/mapping/
audit nguyên tử. Đặt lại cùng form, login chỉ đọc; không lưu password mới ở
transient/context/yêu cầu xác thực chờ/lịch sử. Giữ native hashing và policy.
Thay cách nhập qua change.password.wizard của CHG004, không thay policy quyền.

Yêu cầu trực tiếp HR-ACCOUNT-ROLE-001 cho phép triển khai/test/backup-restore/
áp main trong task này, ngoại lệ vai điều phối DEC-022; không commit/push.
Mỗi nhân viên dùng user riêng, không chọn/liên kết/gỡ user có sẵn. Thay phần
giao diện liên kết của DEC-038; giữ mapping hợp lệ, constraint user/company,
tài khoản hệ thống và lịch sử. Không tự cấp user cho toàn bộ roster.

Admin đúng company tạo user mới hoặc đổi staff ↔ HEAD KH-KD trong hồ sơ qua
preview/lý do/scope/audit nguyên tử, tái sử dụng tp.kd.department.role và guard
superuser hẹp. HEAD theo DEC-033/current matrix; chức vụ HR không cấp quyền.
Hạ role chặn nguồn quyền quản lý cấp riêng xung đột và giữ/liệt kê quyền riêng
hợp lệ. Phiên cũ bị thu hồi. Phòng khác chưa có bộ role thì báo chưa triển khai.
Tình trạng tài khoản là Mở/Khóa/Chưa có tài khoản, tách archive hồ sơ.

Giao diện native năm tab, sidebar navy/nội dung sáng, account & permissions rõ;
password theo Odoo native. Không mở thêm quy trình ký/hiệu lực/thanh toán, HR
toàn công ty cho HEAD hoặc hệ thống role mới. [Guide](demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md),
[security](security/HR_ACCOUNT_ROLE_001_SECURITY.md), [acceptance](demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md).
Technical verification, visual/business acceptance và pilot authorization tách riêng.

## DEC-038 — HR native, roster mới, mã TP và xử lý tài khoản phù hợp (11/11/2026)

**Lệnh thực thi trực tiếp 11/11/2026 — CHG-20261111-002:** người dùng giao phiên
này thực hiện đầy đủ prompt, dùng đúng file nguồn, test `tp_tanphat_test`18079
trước, backup/restore kiểm chứng rồi áp `tp_tanphat_dev`18069; không commit/push.
Đây là ngoại lệ vai điều phối DEC-022 trong scope HR-001, không thay thẩm quyền
nghiệm thu nghiệp vụ/pilot hoặc cho phép payroll/tuyển dụng thiếu quy chế.
Kết quả thực tế xem status và [acceptance](demo/HR_001_ACCEPTANCE.md).

**Người dùng yêu cầu soạn kế hoạch/prompt:** dọn mẫu, đưa hồ sơ nhân viên cùng
phòng ban từ bảng công mới vào HR; mã số nguồn đổi thành mã TP (60 → TP10060),
chức năng HR thực, sidebar theo KH-KD và dashboard có biểu đồ tròn.

- Nguồn roster mới là `bang cham cong vao ra (1).xlsx`, hai sheet cùng 39 người/
  9 nhóm, không 78 người; metadata/hash và đối chiếu tại [kế hoạch HR](architecture/TP_HR_001_ROSTER_WORKSPACE_PLAN.md).
  Thay nguồn danh mục của DEC-034 cho lần nhập này, giữ lịch sử nguồn cũ.
- Mã nghiệp vụ TP+(10000+mã nguồn); không đổi PK/FK Odoo. Lưu mã nguồn riêng,
  kiểm unique, import idempotent; dùng model HR/version hiện hữu.
- Người dùng trả lời rõ: **“Liên kết hồ sơ nhân viên; giữ quyền KH-KD”**.
  Không cấp tất cả account KD quyền quản lý HR, không tự tạo 39 users. Chưa chỉ
  định người thật làm HR; main dùng admin, test actor giả cho kiểm quyền.
- Sau khi biết mapping alias còn mơ hồ, người dùng chỉ đạo lấy file mới làm
  chuẩn và **“có thể xóa những tài khoản hiện tại đi nếu thấy nó không phù hợp
  với file excel”**. Cách triển khai đề xuất là archive/disable account mẫu
  xác minh không phù hợp, có audit/backup và giữ admin/kỹ thuật. Mơ hồ danh
  tính để pending, không chuyển quyền sang người khác. Đây không phải lệnh
  hard-delete user/log/identity hoặc khóa account thật chưa đủ căn cứ.
- Phạm vi prompt gồm code/test/roster và rollout main 18069 sau backup/restore
  kiểm chứng, dùng test chuẩn 18079 theo DEC-037. Phiên soạn prompt chỉ đọc và
  viết tài liệu, chưa thực thi thay đổi ứng dụng/database/tài khoản.
- “Đầy đủ” lượt này là HR Foundation (hồ sơ/danh mục/import/quyền/UI/dashboard/
  Excel); chấm công/lương/nghỉ phép/tuyển dụng đầy đủ cần quy chế và đầu vào
  riêng. Không nhập giờ vào-ra hoặc bịa KPI từ workbook danh mục.

Chi tiết giao việc tại [prompt HR-001](prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md).

## DEC-037 — Dọn dữ liệu mẫu và chuẩn hóa hai database local (10/11/2026)

**Yêu cầu trực tiếp và phạm vi đã xác nhận:** xóa dữ liệu nghiệp vụ mẫu; giữ
tài khoản, quyền và cấu hình. Giữ một database chính cùng một database test.

- Local dùng `tp_tanphat_dev`/18069 và `tp_tanphat_test`/18079 trên cluster
  workspace55432; giữ `postgres`, `template0`, `template1`. Không xóa bảng/schema
  Odoo, không thay service PostgreSQL khác hoặc source ứng dụng.
- Dọn đúng sample namespace/binding và phụ thuộc đã kiểm kê; giữ tài khoản,
  mật khẩu, nhóm/ACL/rule và HEAD role. Assignment/grant của dự án mẫu đi cùng
  dự án bị xóa; không coi đó là quyền toàn hệ thống phải cấp lại tự động.
- Backup database+filestore; diễn tập restore và dọn trên bản riêng, đối chiếu
  phần giữ lại và đăng nhập trước main. Bỏ database cũ theo danh sách chính xác
  sau khi kiểm bản lưu. Archive riêng tư không đưa Git.
- Test chuẩn tách filestore/session, tắt cron/SMTP và đổi UUID/URL. Tái sử dụng
  với một tác vụ ghi/migrate tại một thời điểm; không tiếp tục tạo DB theo task
  nếu chưa có yêu cầu riêng. Phát triển dữ liệu giả trên test trước; áp source/
  migration được giao lên main, không chép test đè main.
- Không reset sequence, đổi mật khẩu, nhập roster thật, gỡ module hoặc mở quyền
  xóa lịch sử trong ứng dụng. Danh mục/công ty và cấu hình Internal của Odoo
  giữ lại dù có tên DEV. Baseline HR12 mẫu trước đây chuyển thành lịch sử sau
  bảo trì; nguồn39người còn ngoài DB. Kết quả thật theo status và
  [runbook](../ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md).

## DEC-036 — Thiết kế Home admin với 7 mục; nhân sự là chặng tiếp (10/11/2026)

**Yêu cầu trực tiếp:** chỉ hiển thị Kế hoạch Kinh doanh, Phòng Thiết kế,
Phòng Kỹ Thuật, Phòng BIM-QC, TADIC, Quản lý nhân sự và Tuyển dụng ở màn
admin; thiết kế trước, bước phát triển tiếp theo là module quản lý nhân sự.

- Thay phạm vi Home của DEC-035: đúng 7 mục, nhóm thành 5 phòng/đơn vị và
  2 chức năng nhân sự. KH-KD mở workspace hiện hữu; 4 đơn vị còn lại có trang
  Đang phát triển; HR/recruitment theo trạng thái module và quyền thực tế.
- Chỉ khung Home quản trị thay đổi. Người thường giữ Home/menu nghiệp vụ
  theo quyền hiện có; không suy HEAD KH-KD là quản trị hệ thống. Thiết kế đề
  xuất nhận diện admin bằng `base.group_system`; đây chưa phải thay đổi nhóm
  hoặc security runtime. Không cấp quyền HR từ việc thêm thẻ Home.
- Không đưa 4 nhóm còn lại lên khung này không có nghĩa xóa tổ chức hoặc
  nhân viên: nguồn DEC-034 vẫn 39 người/9 nhóm. Không tự import, tạo account,
  chuyển phòng hoặc sửa grant từ thay đổi điều hướng.
- Lượt hiện tại chỉ [thiết kế và preview](ui/UI_HOME_004_ADMIN_DESIGN.md),
  chuẩn bị [prompt triển khai mới](prompts/CLAUDE_UI_HOME_004_ADMIN_ONLY.md)
  và [kế hoạch HR-001](architecture/TP_HR_001_FOUNDATION_PLAN.md). Không sửa
  ứng dụng/DB/dev. Prompt Home cũ giữ lịch sử và được đánh dấu đã thay thế.
- HR phát triển tiếp từ hồ sơ nhân viên, tổ chức/chức danh và quyền; sau đó
  nhập roster có đối chiếu, báo cáo và tuyển dụng. Chấm công/nghỉ phép/lương
  cần quy tắc riêng; không coi nghiệp vụ HR toàn công ty đã được xác nhận.

## DEC-035 — Home đủ phòng/đơn vị và lối vào HR/Tuyển dụng (10/11/2026)

**Yêu cầu trực tiếp:** đưa các phòng lên Home, ngoài KH-KD khi bấm ghi “Đang
phát triển”, thiết kế gọn/đẹp, thêm Quản lý nhân sự và Tuyển dụng.

- Bổ sung phạm vi khung Home ở DEC-031: theo 9 nhóm nguồn mới DEC-034,
  1 workspace KH-KD hiện hữu, 8 landing placeholder riêng. Không thêm HĐQT từ
  bảng cũ hoặc tạo hai workspace KH-KD/Ban Kinh Doanh trùng nhau.
- Hai thẻ Quản lý nhân sự/Tuyển dụng là chức năng dùng chung, không phải hai
  phòng mới. Prompt quy định mở module native đã cài/có quyền; thiếu quyền khác
  chưa triển khai. Không suy HEAD có quyền HR hoặc tự cài/cấp nhóm HR trong batch Home.
- Chỉ thêm khung và lối vào; ưu tiên nghiệp vụ KH-KD, không triển khai đầy đủ
  phòng khác hoặc nhập nhân viên thật. Giữ DEC-029/030/033 và vai trò điều phối.
- [UI-HOME-004](prompts/CLAUDE_UI_HOME_004_DEPARTMENTS_HR_RECRUITMENT.md) giao
  clone-test/ảnh trước–sau, backup/restore verified rồi áp18069. Soạn prompt
  không phải đã sửa giao diện, cài module hoặc nghiệm thu chức năng HR.

## DEC-034 — Dùng bảng nhân sự tuần 1 tháng 11 làm nguồn hiện hành (10/11/2026)

Người dùng cung cấp `202611_tanphat_chamcong_tuan1.xlsx`, rồi xác nhận
**“cứ làm theo file tôi mới gửi đi”** khi được hỏi về khác biệt với phân công cũ.

- Dùng danh sách/phòng/chức vụ trong nguồn mới cho hồ sơ kiến thức và kế hoạch;
  giữ tài liệu cũ làm lịch sử, không lấy nhiệm vụ cũ ghi đè nhóm trong file mới.
- Kiểm được 39 dòng/9 nhóm, mã không trùng, tên/mã/chức vụ đối chiếu XML; kỳ
  02–07/11/2026, hash và locator ở [baseline](architecture/TP_STAFF_SOURCE_BASELINE.md).
- Tên/mã nhân viên trích xuất lưu ngoài Git; bảng công không tự là sơ đồ quản
  lý, danh mục tài khoản, căn cứ thẩm quyền duyệt hoặc tình trạng lao động.
  Không tự mapping sang user/grant, chuyển phòng hay import vào DB.

## DEC-033 — HEAD toàn quyền nghiệp vụ KH-KD (10/11/2026)

**Yêu cầu trực tiếp:** “viết prompt cho tôi thùy anh (trưởng phòng) sẽ toàn quyền
trong phòng kinh doanh”. Người dùng đã chốt hướng phân quyền HEAD; việc cấp
quyền thực tế chưa thực hiện trong lượt soạn prompt này.

- Thay hướng HEAD chỉ đọc/rà soát và giới hạn vài dự án preset bằng quyền quản
  lý toàn nghiệp vụ KH-KD, kể cả hồ sơ nhân viên khác và dự án mới thuộc phòng.
  Chi tiết triển khai/test tại [KD-HEAD-001](prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md).
- Diễn giải triển khai: đầy đủ lập/sửa nháp, gửi/gửi lại, rà soát/trả lại hồ sơ
  người khác, phân công, Project/WBS, đọc/sửa tiền nháp và file/báo cáo/XLSX trong
  đúng company/department. Không hardcode tên hoặc scope hữu hạn của seed cũ.
- Toàn quyền nghiệp vụ vẫn theo state/phiên bản/audit và self-review hiện hành;
  không sửa/xóa lịch sử hoặc tự suy thẩm quyền BASE/ký/hiệu lực/kế toán/thực chi.
  Không đồng nghĩa admin hệ thống, quyền đọc mọi phòng hoặc cấp grant bảo mật
  cho người khác. Chưa xác nhận hạn mức ký hoặc quy chế bốn mắt toàn công ty.
- Đây là delta HEAD cụ thể, không duyệt toàn bộ V2 hoặc thay quyền bốn actor
  còn lại. Prompt giao clone-test/backup/restore verified rồi áp HEAD dev18069;
  không phải tuyên bố đã áp, đã kiểm runtime quyền hoặc đã nghiệm thu/pilot.

## DEC-032 — Tách Quản lý dự án và Quản trị dự án trong KH-KD (09/11/2026)

**Người dùng yêu cầu trực tiếp:** “tách riêng 2 cái quản lý và quản trị dự án đó ra”
và viết prompt triển khai, hoàn thiện các mục đã bàn với lãnh đạo.

- Hai khu vực điều hướng/action/góc nhìn riêng trong workspace KH-KD:
  Quản lý dự án tập trung WBS, công việc, tiến độ, phân công và đầu ra;
  Quản trị dự án tập trung hồ sơ thương mại/hợp đồng, khoán, sản lượng,
  nghiệm thu, đề nghị thanh toán và nghĩa vụ. Cùng hồ sơ gốc/project ID,
  không nhân bản dữ liệu hoặc database theo hai tên gọi.
- Scope prompt gồm chín ý và hai làm rõ tại
  [phân tích cuộc họp](architecture/TP_KD_MEETING_REFINEMENT_20261109.md):
  Người phụ trách đứng trước hạn, đối tác nhiều loại có vai trò; thêm Dự án/
  Chủ đầu tư/tình trạng-nhật ký/giá gói/Đấu thầu đúng quan hệ nghiệp vụ.
- Xác nhận này là yêu cầu tách chức năng và giao chuẩn bị prompt thực thi,
  không phải hoàn tất code, duyệt mọi dòng KD-ROLE-V2, mở TASK-001 cho người
  thật hoặc thay thẩm quyền BASE/ký/hiệu lực/kế toán. Các trạng thái/field/
  capability chi tiết trong prompt là baseline triển khai/test, không tự
  trở thành quy chế pháp lý đã được công ty phê duyệt.
- Giữ DEC-030/031 và vai trò điều phối. Phiên này chỉ viết
  [prompt KD-PROJECT-RESTRUCTURE-001](prompts/CLAUDE_KD_PROJECT_RESTRUCTURE_001.md),
  chưa chạy hoặc áp ứng dụng. Mục tiêu dev18069 qua test/audit/backup/restore;
  correction F1–F3 và quyền người thật chưa duyệt giữ cổng tương ứng.

## DEC-031 — Trang chủ theo workspace, ưu tiên hoàn thành KH-KD (07/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** đồng ý gom nghiệp vụ theo workspace, rồi làm rõ: “những phòng ban khác không quan trọng đâu bây giờ tôi muốn setup sẵn giao diện trang chủ cho logic trước thoi còn nghiẹp vụ và chức năng các thứ thì phạm vi hiện tại đang làm cho phòng kinh doanh, cứ hoàn thành phòng kinh doanh trước đã”.

- Trang chủ ưu tiên **Kế hoạch Kinh doanh** và công cụ cá nhân theo quyền; bỏ lưới “Ứng dụng nghiệp vụ” khỏi nội dung chính cho nhân viên. Chức năng KH-KD truy cập trong workspace, cùng model/action/dữ liệu hiện có.
- Quản trị hệ thống có “Tất cả ứng dụng” và thiết lập theo quyền. Người thường vẫn giữ đường native tới công cụ khác đã được cấp; không thu hồi/mở quyền vì ẩn lưới.
- Hiện không dựng workspace/nghiệp vụ các phòng khác hoặc thẻ giả. Hoàn thành KH-KD trước; catalog có thể mở rộng sau, không nhân bản dữ liệu theo phòng.
- Giữ DEC-023/029/030, session/Home Action, dữ liệu/quyền/workflow và gate nghiệp vụ/pilot. [Danh sách tổ chức nguồn](architecture/TP_ORGANIZATION_SOURCE_BASELINE.md) không phải lệnh tạo cây phòng ban hoặc đổi tên Ban Kinh Doanh.

[Prompt UI-HOME-003](prompts/CLAUDE_UI_HOME_003_KD_FIRST.md) là bước thực thi tiếp theo; CHG-20261107-005 chỉ chuẩn bị tài liệu, chưa sửa application/runtime.

## KD-NATIVE-001 — Giữ254, thiếu6phụ lục (06/11/2026)

Người dùng trả lời trực tiếp: “Giữ254, ghi rõ thiếu6phụ lục”. Action audited `create_amendment` cần không còn revision đang xử lý; task chưa cho mở `review_complete`. Quyết định này thay mục tiêu260 tại7A/CHG006 cho kết quả bàn giao task:254bản ghi nghiệp vụ,10hợp đồng/0phụ lục, các nhóm khác giữ cơ cấu. Không mở gate pháp lý hoặc tạo model dự kiến phụ lục để bù. Prompt260giữ lịch sử, bàn giao ghi rõ chênh6.

## KD-NATIVE-001 — Quyền thực thi và trình diễn dev (06/11/2026)

Người dùng trực tiếp giao phiên chính thực hiện toàn `deliverables/PROMPT_KHKD_NATIVE_18069.md`, bổ sung7A–7C/CHG006, tuần tự các lô, clone-test rồi tích hợp dev18069 sau backup/restore. Ngoại lệ DEC-022 chỉ KD-NATIVE-001; cho custom addon/model/native UI và dataset tổng hợp bền260 mục tiêu, không commit/push hoặc cleanup dữ liệu mới trên dev. Không hỏi lại quyền tích hợp đã cho. Đây không là business acceptance/pilot hoặc cấp grant người thật; Q2/TASK-001/pháp lý/BASE/ký/hiệu lực/hạch toán/tiền thật giữ nguyên. Chỉ ghi số thực sau khi seed/verify dev, không coi mục tiêu là số đã tạo.

## DEC-030 — Giao diện chính phát triển trong Odoo (05/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** “tôi quyết định sẽ phát triển fe dựa trên odoo chứ ko tác riêng fe ra nữa”. Giao diện chính TANPHAT ONE dùng native Odoo, view/action chuẩn và OWL/QWeb/SCSS trong `custom_addons/` khi cần. DEC-030 thay lựa chọn frontend độc lập trong DEC-001 và định hướng login React chính ở DEC-012; giữ backend Odoo, dữ liệu, session, API và các kết quả đã có. Đây là quyết định hướng phát triển, chưa tự chuyển route/login hoặc triển khai UI còn thiếu.

- Giữ nguyên DEC-002/003/013/014/017/023/029: một database mỗi môi trường, không sửa core, BASE duyệt chính thức giai đoạn đầu, quyền tiền và workspace theo scope; TADIC/TACICO cùng công ty.
- Source React, OpenAPI, API và test lịch sử được bảo toàn; không xóa/gỡ/ngừng dịch vụ hoặc rewrite workflow chỉ vì đổi hướng. Chuyển từng luồng sang native phải có task, test và kiểm hồi quy riêng.
- Native Odoo được dùng ORM/RPC theo cơ chế chuẩn; action/model backend tiếp tục enforce state/capability/company/project/financial scope. Không bypass bằng direct state write, sudo hoặc chỉ ẩn nút.
- TP Contracts chưa có UI native đầy đủ. Backend draft/submit/return/rework đã có; cần đặc tả rồi triển khai menu/list/form/action native tái sử dụng đúng backend, không code lại nghiệp vụ. Quyết định này không xác nhận hạn mức, cấp quyền người thật hoặc mở pilot.

Xem [hướng hiện hành và phần cần chuyển](architecture/TP_NATIVE_ODOO_DIRECTION.md). Lượt CHG-20261105-001 chỉ cập nhật hướng dẫn/tài liệu; chưa sửa application code hoặc runtime.

## DEC-029 — TADIC và TACICO là đơn vị nội bộ cùng công ty (04/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** TADIC và TACICO là đơn vị nội bộ cùng công ty, không phải hai pháp nhân riêng. Không tạo `res.company`, database, bộ khách hàng hoặc dự án trùng chỉ để phân biệt hai đơn vị này. Giữ một database cho mỗi môi trường theo DEC-002 và workspace theo quyền theo DEC-023.

**Hệ quả thiết kế:** tổ chức hai đơn vị dưới cùng công ty; ánh xạ vào cây phòng ban/đơn vị hiện có sau khi xác định cấp trên và mã đơn vị. Phân công dự án và quyền dữ liệu được kiểm tra ở backend; cùng công ty không đồng nghĩa tự được xem tiền, hồ sơ nhân sự hoặc dự án của đơn vị khác. Chưa xác nhận đơn vị cha, người quản lý, quyền duyệt hoặc mô hình phân bổ chi phí; không suy ra những quyền này từ tên đơn vị.

Lượt xác nhận chỉ cập nhật tài liệu. Không tạo đơn vị/tài khoản, đổi schema, seed dữ liệu thật hoặc điều chỉnh quyền trên runtime. Xem [thiết kế database](architecture/TP_DATABASE_DESIGN.md#1-phương-án-chọn).

## DASH-UI-001 — Thực thi riêng dashboard native (04/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-028 | Người dùng giao trực tiếp task và cho triển khai/kiểm thử/handoff; áp dụng CHG-20261104-001 | Phiên chính được sửa đúng dashboard UI/reporting native18069 sau snapshot/clone. Ưu tiên native; OWL/SCSS/backend report giới hạn addon custom và hai binding được giao khi native spreadsheet thiếu phép phân bổ/filter đúng. | Ngoại lệ chỉ DASH-UI-001; DEC-022 mặc định giữ nguyên. Không đổi workflow/quyền/allowlist/chứng từ/password, core/React/prototype, commit/push hay dựng demo cũ. Dữ liệu hiện tại thắng mốc lịch sử khi có tracking bằng chứng. Technical verification không thay audit độc lập/business/pilot. [Runbook](demo/dashboards/README.md). |

## DEC-022 — Phiên chính điều phối, Claude triển khai

**Ngoại lệ trực tiếp 06/11/2026, CHG-20261106-002:** người dùng giao phiên chính chạy nốt `CLAUDE_UI_CTR_NATIVE_001A.md` vì Claude hết token. Cho thực thi UI001a trên DB test với fixture, acceptance trước implementation; không áp dev, không commit/push. Ngoại lệ này không đổi policy nghiệp vụ hoặc vai trò điều phối mặc định ở task khác.

**Trạng thái:** người dùng xác nhận trực tiếp ngày 28/10/2026. Phiên chính lập kế hoạch, tổng hợp nội dung/ý tưởng, phân tích, kiểm source/test lại kết quả Claude và phát prompt; không trực tiếp sửa application code trong vai trò này. Claude triển khai từng batch được giao, chạy test và cập nhật handoff. Phiên chính audit độc lập, đưa finding/correction hoặc next prompt; technical acceptance không thay xác nhận nghiệp vụ/pilot. Đây là phương thức làm việc, không phải quyết định mở thêm chức năng hoặc phê chuẩn toàn bộ roadmap. Người dùng có thể đổi vai trò/phạm vi bằng chỉ thị trực tiếp. Xem [quy trình điều phối](AI_COORDINATION_WORKFLOW.md).

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-001 | Hướng frontend đã được DEC-030 thay thế ngày 05/11/2026 | Lịch sử: web riêng gọi API Odoo; backend modular monolith giữ nguyên | Giao diện chính hiện là native Odoo; không xóa source/API cũ |
| DEC-002 | Đã áp dụng ở dev | Một PostgreSQL database cho mỗi môi trường, dùng chung các phòng | Dùng ORM chuẩn, company/project/assignment scope; staging/production chưa được dựng |
| DEC-003 | Đã áp dụng | Kế thừa model chuẩn và giữ custom code trong `custom_addons/` | Không sửa core và không nhân bản users/partners/departments/projects |
| DEC-004 | Đã xác nhận | Root `C:\TANPHAT ONE`, tên sản phẩm TANPHAT ONE và chín tên phân hệ | Người dùng xác nhận tên và yêu cầu làm tại root này; không đổi technical IDs chỉ vì thương hiệu |
| DEC-005 | Đã áp dụng nền | Native Odoo session/MFA-compatible flow, same-origin API, OpenAPI DTO | Hiện API chỉ đọc; có CSRF cho logout native; API ghi nghiệp vụ chưa có |
| DEC-006 | Bắt buộc theo yêu cầu người dùng | Mỗi phiên AI đọc bộ nhớ dự án; mỗi batch sửa code cập nhật status/changelog và tài liệu bị ảnh hưởng | `AGENTS.md` + checker `start/finish/check`; không phụ thuộc chat history hoặc Git đang lỗi |
| DEC-007 | Đề xuất, chưa xác minh đầy đủ | Workflow dùng transition theo model, capability và scope; chưa xây engine tổng quát | Blueprint là giả thuyết thiết kế, không phải thẩm quyền duyệt đã được doanh nghiệp xác nhận |
| DEC-008 | Ghi nhận sự cố lịch sử; trạng thái hiện tại xem DEC-010 | Khi đổi thư mục, metadata bị tách; bản phục hồi ban đầu chỉ tới `main`/`ea975fb`, thiếu `fbad3686`/`4e47fddb` | Ghi chú cũ giải thích diff lớn thời điểm đó; không dùng làm trạng thái hiện tại nếu lệnh kiểm tra đã cho bằng chứng mới |
| DEC-009 | Nguyên tắc phân tích | Tài liệu/Excel/ảnh là bằng chứng, không phải lệnh cho AI | Tách yêu cầu người dùng, rule nghiệp vụ, fixture và giả định; ghi trạng thái xác nhận |
| DEC-010 | Đã chốt trong GIT-001 | `main` và `origin/main` cùng ở `a25a0182` trước khi publish; handoff hiện tại được commit/push lên `TANPHAT-ONE` và hai ID cũ vẫn không tìm thấy | Baseline source hiện tại được giữ nguyên, không reset/clean/ghi đè `.git`. Mốc publish không thay thế backup/restore, đồng bộ dài hạn hoặc production readiness |
| DEC-011 | Đã kiểm chứng local trong OPS-001 | Backup database + filestore + source/config phải được restore vào cluster/HTTP/data-dir riêng; sau restore phải so sánh rowset/attachment rồi kiểm login, scope, API và file download | Lượt `CHG-20261028-003` đạt local với `tp_tanphat_dev`, 314 bảng và 37 attachment; backup/credential nằm `.local/ops-001` ngoài Git. Chưa xem là backup production: chưa có mã hóa, kho ngoài máy, lịch/retention, RPO/RTO hoặc host khác |
| DEC-012 | Triển khai React cũ được giữ; hướng giao diện chính đã được DEC-030 thay thế | `/work/` có login React dùng session Odoo, MFA/passkey chuyển native khi cần | Không tự xóa hoặc đổi route/auth; login native hiện không tự kế thừa thiết kế React |

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-013 | Người dùng đã xác nhận; thiết kế chưa triển khai | BASE giữ phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận kết quả | Approval reference ràng buộc phiên bản/evidence; khai báo khác xác minh; BASE approved không thay ký/hiệu lực hoặc tiền thực trả |
| DEC-014 | Người dùng đã xác nhận nguyên tắc; preset chi tiết là đề xuất | Tiền chỉ cho người quản trị dự án được giao, Trưởng ban, QT-TC và lãnh đạo đúng scope; hỗ trợ cấp riêng | financial.read khác draft_edit/export; file/chatter/audit/report/RPC phải theo cùng policy; quyền đọc project hiện tại chưa cấp quyền tiền |
| DEC-015 | Ghi nhận chưa biết; cổng bắt buộc cho action liên quan | Không đặt hạn mức ký/duyệt hoặc tự suy thẩm quyền từ chức danh; bốn mắt chưa xác nhận | Q1–Q3 của BIZ-001 chặn xác minh/chốt pháp lý/pilot liên quan, không chặn read schema hoặc draft development độc lập trên test |
| DEC-016 | Quy tắc mẫu đã đối chiếu; snapshot domain là đề xuất | Giá cập nhật PKH là tổng mới theo phạm vi, không phải delta; các sự kiện sản lượng/nghiệm thu/hóa đơn/tiền tách nhau; cấp 2 không cộng tổng lần hai | Snapshot revision đầy đủ dựng từ bản trước/phụ lục có provenance; không copy điều kiện giá dương cuối/ID toàn cục hoặc bảng transaction đa năng; hồ sơ pháp lý/thuế/hồi tố còn cần xác nhận |
| DEC-017 | Đã áp dụng ở dev trong CTR-001 | `financial_read` là `tp.project.grant` theo user + project (lý do, thời hạn, thu hồi); số tiền nằm ở model riêng (`tp.contract.line.amount`, `tp.approval.reference.amount`) có access domain theo grant; tài liệu phân loại `general`/`financial`. Grant chỉ superuser cấp khi Q2 chưa chốt; Platform Manager/admin không có tiền mặc định; API đọc đặt trong `tp_planning_api` | Field group toàn cục không giới hạn được theo từng project; model riêng làm ORM read/search/`read_group`/export, RPC, API và tệp cùng bị chặn. Không suy grant từ chức danh khi chưa có văn bản phân công; admin/superuser vẫn có khả năng truy cập kỹ thuật |

DEC-013–017 cụ thể hóa baseline ở DEC-007 và thay phần chưa chốt về lựa chọn nơi duyệt/cách hiểu giá trong mẫu. Văn bản thẩm quyền, bốn mắt, điều khoản giữ lại/thuế/ngày hiệu lực và chính sách correction sau chốt vẫn chưa được coi là xác nhận chỉ từ blueprint hoặc fixture. Xem [BIZ-001](architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md).

## DEC-023 — Một nền giao diện chung, workspace theo phòng ban và quyền

**Nguyên văn người dùng đã chốt:** “Một nền giao diện chung cho toàn hệ thống, nhưng mỗi phòng ban có workspace, menu, dashboard, trường dữ liệu và nút thao tác khác nhau theo vai trò và quyền.”

**Trạng thái:** người dùng xác nhận trực tiếp ngày 29/10/2026 nguyên tắc dùng một nền giao diện chung cho toàn hệ thống, còn trải nghiệm thay đổi theo phòng ban/vai trò/quyền. TANPHAT ONE không tạo một frontend lặp lại cho từng phòng ban; cũng không coi việc ẩn nút trên frontend là biện pháp bảo mật. Các cơ chế technical dưới đây là khung đề xuất để đặc tả dần, không phải danh mục menu, route, field hoặc capability đã được công ty phê duyệt.

| Quy tắc | Áp dụng |
| --- | --- |
| Common shell | **Nguyên tắc đã chốt:** một nền giao diện chung. Thành phần như thương hiệu, tìm kiếm, thông báo, tài khoản là thiết kế UX đề xuất. |
| Department workspace | **Nguyên tắc đã chốt:** mỗi phòng/vai trò có trải nghiệm khác nhau. Danh sách workspace, navigation, KPI và quick action cụ thể cần domain owner/spec riêng. |
| Shared detail | **Đề xuất kỹ thuật:** tái sử dụng bản ghi canonical khi một hồ sơ được nhiều phòng cùng xử lý; route, section và field cụ thể còn phải đặc tả theo domain. |
| Backend authority | **Nguyên tắc kiến trúc:** quyền phải được enforce ở backend theo các quyết định security hiện hành. DTO/`allowed_actions` là cách triển khai đề xuất, chưa mở thêm capability. |
| User context | **Đề xuất kỹ thuật:** một người có thể có nhiều assignment/workspace; không thay thế kiểm tra quyền trên từng record. |

**Cơ sở/ảnh hưởng:** mô hình này phù hợp với cách tổ chức role-based workspace phổ biến trong Odoo, SAP Fiori, Dynamics 365 và Salesforce, đồng thời phù hợp các quan sát đã ghi về Base/IMIS2. Đây là quyết định UX/kiến trúc của TANPHAT ONE; các menu, field, dashboard và capability cụ thể của từng phòng vẫn phải có đặc tả/owner riêng. Các route frontend dùng một app; addon backend tiếp tục chia theo nghiệp vụ và nguồn dữ liệu, không chia theo phòng ban.

## DEC-024 — Demo native Odoo toàn hệ thống cho lãnh đạo

**Trạng thái:** người dùng xác nhận trực tiếp ngày 30/10/2026 hai lựa chọn: “Dựng native Odoo để demo trước” và “Dựng khung toàn hệ thống”. Phiên chính tiếp tục điều phối và viết prompt; Claude triển khai.

**Phạm vi đã cho phép:** khung trình diễn bằng Odoo native trên môi trường riêng, dữ liệu giả; tận dụng module/model sẵn có, bổ sung common workspace/dashboard/menu và màn hình minh họa có nhãn cho phần chưa triển khai. Giữ chín tên phân hệ hiện hành; CRM/Request/Bid được giới thiệu như mục bổ sung, không tự trở thành nghiệp vụ đã nghiệm thu. Cho phép fixture actor/grant theo policy hiện có trong DB demo, không cấp quyền người thật.

**Ranh giới:** đây là bản trình diễn ưu tiên trước, không thay DEC-001/023 về frontend React + API Odoo hoặc DEC-013/017 về BASE/quyền tiền. Không mở production/pilot, không nâng cấp DB dev/test, không tự nghiệm thu AUTH-002 còn pending. Chức năng dự kiến và chức năng runtime phải phân biệt trên UI/tài liệu. Prompt tại [UI-DEMO-001](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md); việc viết prompt không chứng minh đã có demo chạy được.

## BIZ-002 — Ưu tiên thiết kế nghiệp vụ trước code (28/10/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-018 | Người dùng xác nhận phạm vi và thứ tự | Lượt BIZ-002 chỉ phân tích/viết tài liệu toàn công ty A–M, bắt đầu chi tiết từ KD; hoàn thiện quy trình, dữ liệu, quyền, quy tắc và nghiệm thu trước code. Người dùng quyết định chuyển giai đoạn | Thay ưu tiên Next action hướng CTR-002 của CHG-008; giữ nguyên CTR-001 đã bàn giao/read runtime. Không sửa source/schema, setup/upgrade/seed/credential, commit/push hoặc tự nhắn chat khác |
| DEC-019 | Nguyên tắc thiết kế đã yêu cầu; chi tiết là đề xuất | Một nguồn sự thật theo phần: workflow KD giữ mapping contract/Q1–Q8, BIZ-002 mở rộng A–M/RACI/dictionary/tích hợp/KPI/scenario/readiness; phân biệt U quyết định người dùng, O quan sát nguồn, D thiết kế, Q chưa đủ căn cứ, R runtime | [Bộ thiết kế BIZ-002](architecture/TP_BIZ002_DESIGN_PACKAGE.md); Q9–Q14 bổ sung theo domain. Không coi source Excel/ảnh, walkthrough hoặc checker là quy chế được công ty duyệt; không ledger/workflow engine song song |

RACI/capability/transition mới, policy field/export/attachment, SLA/threshold/retention và mô hình tích hợp chỉ trở thành quy tắc được áp dụng sau cổng theo [readiness](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md); chưa có quyết định nào đóng Q1–Q14 trong lượt tài liệu này. DEC-013–017 tiếp tục hiệu lực trong phạm vi đã ghi.

## CTR-002a — Mở code draft/submit/return chỉ trên test (28/10/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-020 | Người dùng xác nhận 28/10/2026 | Cho phép chuyển CTR-002a-P1 sang code chỉ trên database test với dữ liệu giả và actor fixture, dù Q2 còn mở: draft/sửa draft, submit → `in_review`, trả lại có lý do → `returned`, sửa và submit lại. Q2 vẫn chặn người dùng thật/pilot | Capability CTR-002a là grant theo project + phòng ban do superuser/fixture tạo; không cấp cho user thật, không suy từ chức danh. Ngoài phạm vi: BASE approved/verified, chữ ký/thẩm quyền ký, effectivity, nghiệm thu/thanh toán/giao khoán, cancel revision, quản trị grant người dùng thật |
| DEC-021 | Người dùng giao AI quyết định cho CTR-002a-P1 ngày 28/10/2026; giới hạn ở test/thiết kế | Người lập KD có assignment được draft/edit/submit; commercial reviewer phải khác người gửi của từng submission; vì vòng review có kiểm tra số tiền nên sender/reviewer cần `financial_read`; sửa tiền thêm `financial_draft_edit`. Không suy quyền từ chức danh; không mở legal/BASE/payment/grant người thật | Đây là chính sách kỹ thuật/nghiệp vụ giới hạn cho test fixture, không phải quy tắc bốn mắt toàn công ty, không bổ nhiệm Q2-A/Q2-B hoặc thẩm quyền ký; backend phải enforce self-review và UI loại người gửi |

## VI-002 — Một bộ nhãn tiếng Việt cho `tp_contract` (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-025 | Người dùng xác nhận 02/11/2026 (“Use new catalog”) | Nhãn selection của `tp_contract` lấy theo `custom_addons/tp_contract/i18n/vi.po` (VI-001). Catalog của `tp_demo_workspace` dùng cùng bản dịch theo từng XML ID, và chuỗi cứng của demo cũng đổi theo. | Đóng G9 trong source, không đổi state key, XML ID, domain hay dữ liệu. Runtime demo18109 chưa nâng cấp. Nhãn React contracts (G10): người dùng chọn giữ nguyên ngày 02/11/2026 (“Leave React as is”), nên React và Odoo tạm hiện hai cách viết. |

## NATIVE-DATA-003 — Yêu cầu prompt dữ liệu mẫu liên thông (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-026 | Người dùng yêu cầu soạn prompt, chưa thực thi | Chuẩn bị bộ dữ liệu mẫu hiện có trên dev 18069 thành tình huống vận hành liên thông theo người dùng/dự án/chứng từ; tái sử dụng ID, giữ nguồn gốc giả lập, chứng minh bằng actor/action/quyền và dữ liệu nguồn. [Prompt NATIVE-DATA-003](prompts/CLAUDE_NATIVE_DATA003_CONNECTED_OPERATIONS.md) mô tả phạm vi để giao Claude sau. | Không coi đây là nghiệm thu hoặc lệnh chạy migrator ở phiên viết prompt. Phạm vi đề xuất khi giao thực thi gồm actor giả/login, linkage và native action an toàn; policy managed-task/TP workflow và posting/thu chi dev cần batch riêng, không tự mở người dùng thật/pilot hoặc phục hồi demo cũ. |

## NATIVE-DATA-003 — Chuyển vai trò thực thi giới hạn (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-027 | Người dùng xác nhận trực tiếp “Chuyển vai trò: thực thi trong phiên này”; đã áp dụng phần an toàn CHG-014 | Cho phiên chính triển khai đúng prompt NATIVE-DATA-003 ở dev18069 sau snapshot/clone. Cho bật login actor giả, hierarchy/linkage, bridge CRM→Project và correction security B3 có spec/test riêng; native submit/approve chỉ khi không posting/payment hoặc gửi ra ngoài. | Ngoại lệ vai trò chỉ task này, không thay DEC-022 mặc định hay DEC-001/013/017/020/021. Ba addon bridge/timesheet scope/dashboard privacy đã clone-test rồi cài dev. Không mở generic managed-task write, TP workflow/grant hoặc hạch toán/thu chi dev. Kết quả `PARTIAL_WITH_GAPS`, [TASK-001](architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md) chờ policy; [runbook/evidence](demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md). Technical audit/business/pilot vẫn riêng, không suy ra từ chuyển vai trò. |


## HR-DASH-001 — Thực thi dashboard và khóa tài khoản (11/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-039 | Người dùng yêu cầu trực tiếp; đã triển khai CHG-20261111-010 | Phiên chính thực thi prompt HR-DASH-001 trong scope này; kiểm18079, backup/restore kiểm chứng, áp18069, không commit/push. Bổ sung khóa/mở, cột Tình trạng Khóa/Mở/Chưa liên kết; thông báo đăng nhập bị khóa và Gửi phản hồi placeholder. | Giữ native Odoo; khóa user tách archive employee. Admin đúng company nhập lý do, bảo vệ tài khoản hệ thống/self; nativeactive + cờHR/tokenrevision, session cũ không hồi sinh. Chỉ thông báo khóa sau credential đúng; feedback chưa gửi backend. Không sửa roster/quyền/password người thật để test. Ngoại lệ vai trò chỉ task, visual/business/pilot riêng; xem guide HR-DASH-001. |
