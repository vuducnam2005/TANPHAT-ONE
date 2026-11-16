# EQUIP-UI-001 — Làm lại giao diện Kho thiết bị, gọn và trực quan

**Phản hồi tiếp CHG-20261115-001:** dùng
[EQUIP-UI-002 / UI-BACK-001](CLAUDE_EQUIP_UI_002_USERS_AND_GLOBAL_BACK.md) để
tách menu Người sử dụng khỏi list tổng/stock, bổ sung HR/ghi chú rõ, Quay lại
toàn hệ thống và nâng tiếp dashboard. Không chạy lại toàn bộ task UI-001 hoặc
dùng phạm vi list tổng bên dưới để giữ stock trong màn người sử dụng.

Làm việc trong `C:\TANPHAT ONE`. Triển khai trực tiếp **18069**,
database `tp_tanphat_dev`, theo chỉ đạo EQUIP hiện hành. Không commit/push.

## 1. Mục tiêu và phạm vi

Người dùng đã xem bản có dữ liệu và không hài lòng: giao diện đơn sơ, ít màu,
lọc chiếm quá nhiều diện tích, biểu đồ quá thấp, bảng dài và nhãn trạng thái
đè sang cột khác. Cần **thay đổi bố cục và cách trình bày rõ rệt**, không chỉ
đổi vài màu/bo góc. Ưu tiên giao diện đẹp, thao tác đơn giản, đọc được ngay.

Nhu cầu chính chỉ gồm:

1. Biết đang quản lý những thiết bị gì và ai/phòng nào đang sử dụng.
2. Biết thiết bị nào đang nằm trong kho.
3. Ghi nhận, theo dõi nhu cầu mua thiết bị của nhân viên.
4. Xem tổng quan có biểu đồ lớn, rõ và màu sắc có ý nghĩa.

Giữ native Odoo20/OWL/QWeb/SCSS, cùng database/session/HR và shell hiện có.
Reuse `tp_equipment`; không tách React, tạo app thứ hai hoặc cài Ant Design.
Style chỉ trong scope Kho thiết bị, không làm đổi HR/KH-KD/Home/login.

Đây là việc thiết kế và triển khai UI, không phát triển thêm quy trình ERP.
Không xóa dữ liệu/model/phiếu/nguồn nhập, không reset hay seed lại để làm đẹp.
Giữ admin-only `base.group_system` và backend kiểm quyền/company. Trong lượt
này admin **ghi nhận đề xuất do nhân viên gửi** với HR ID; không tự mở portal/
quyền kho cho toàn bộ nhân viên chỉ vì tên chức năng có chữ “nhân viên”.

## 2. Đọc và ghi nhận trước khi làm

Đọc AGENTS.md, PROJECT_STATUS, AI_CHANGE_WORKFLOW, ROADMAP, DECISIONS (DEC-030,
044, 045), skill `.agents/skills/tanphat-odoo-delivery/SKILL.md`, cùng:

- `custom_addons/tp_equipment/README.md`, `__manifest__.py`.
- `static/src/dashboard/dashboard.{js,xml,scss}` và `models/dashboard.py`.
- `static/src/table/`, `static/src/form/`, `static/src/sidebar/`, `prefs.js`.
- `views/menus.xml`, `equipment_views.xml`, `proposal_views.xml` và các caller.
- Helper dùng chung `tp_web_home/static/src/search/` trước khi thay cách lọc.
- `docs/ui/TP_TABLE_FILTER_STANDARD.md`, `TP_TABLE_FILTER_INVENTORY.md`.
- `docs/demo/EQUIP_001_USER_GUIDE.md` và runbook EQUIP.

Baseline CHG-012: đã nhập thật một phần; còn dòng nguồn chờ xử lý. Đọc baseline
thực tế trước làm, không ép DB về số cũ. Lưu số lượng/ID/hash thiết bị/phiếu/
đề xuất/binding nhập, HR/user/quyền và chụp giao diện trước bằng admin.

Chạy workflow start trước sửa; phối hợp checkpoint nếu có tác vụ khác. Backup
mới DB + filestore + source trước upgrade, giữ private ở `.local/equip-ui001/`.
Theo yêu cầu người dùng: làm trực tiếp main18069, không18079/clone/database mới,
không bộ test riêng/fixture giả. Vẫn xem giao diện sau đổi và sửa lỗi thực tế;
không tuyên bố test PASS khi không chạy. Không hỏi lại quyền áp main đã được giao.

Hai ảnh người dùng là tham chiếu lỗi bố cục hiện tại; có thể đọc từ:

- `C:\Users\vuduc\AppData\Local\Temp\codex-clipboard-a5044a2d-26ca-40af-830f-a59ae81c383a.png`
- `C:\Users\vuduc\AppData\Local\Temp\codex-clipboard-377f20bc-2de9-4f9f-a657-2161984aa611.png`

Nếu ảnh Temp không còn, chụp lại main để phân tích; không dừng chỉ vì thiếu ảnh.

## 3. Thu gọn điều hướng: bốn mục chính

| Mục chính | Nội dung chính |
| --- | --- |
| Tổng quan | Bốn số liệu cần biết, hai biểu đồ lớn, việc cần chú ý gọn |
| Thiết bị & người sử dụng | Danh sách thiết bị; xem ai/phòng/vị trí nào đang giữ; mở chi tiết và thao tác |
| Thiết bị tồn kho | Thiết bị vật lý thực sự ở kho, gồm cả máy chưa kiểm tra/hỏng |
| Đề xuất mua thiết bị | Nhu cầu do nhân viên/phòng ban gửi và tình hình xử lý |

Sidebar cùng format HR/KH-KD: icon đúng nghĩa, active dễ nhận, hover nhẹ; giữ
avatar/tên/người dùng và collapse/mobile drawer. Không nhồi thêm lớp navbar.

Phần phụ **Quản trị dữ liệu** đặt dưới, mặc định đóng, chứa nhập Excel/dòng
chờ bổ sung/phân loại/vị trí. Chỉ admin thấy theo quyền backend. Đưa lịch sử
cấp–thu hồi vào chi tiết thiết bị; các menu sửa/bảo trì/kiểm kê/QR/ngừng quản
lý/phiếu nâng cao chuyển vào nhóm phụ mặc định đóng hoặc “Thêm”. Không dùng
các chức năng này làm nội dung trung tâm trên dashboard nữa.

Reuse XMLID/action hiện có và sửa cây menu server đúng quyền; không hardcode
numeric menu ID, không xóa route/record vì thu gọn sidebar. Kiểm mapping active,
deep link/back/reload sau chuyển menu; không chỉ lọc giả bằng JS. Nếu cần thêm
action/menu Tồn kho thì thêm tối thiểu; giữ action Sẵn sàng cấp phát cũ vì hai
ý nghĩa khác nhau. Không đổi tên action đó thành Tồn kho rồi giữ domain sai.

Giữ truy cập tất cả hồ sơ (kể cả dịch vụ/nháp/ngừng quản lý) trong phần quản
trị/lọc phù hợp. Thu gọn điều hướng không làm các hồ sơ này biến mất vĩnh viễn.

## 4. Thiết kế thị giác phải cụ thể

Giao diện **sáng**, nền xanh xám rất nhạt, bề mặt trắng; giữ shell navy của
TANPHAT ONE. Không dùng dashboard tối. Xây token scoped cho Kho thiết bị:

| Vai trò | Màu định hướng |
| --- | --- |
| Màu chính, thao tác chính | Xanh dương `#2563EB` |
| Đang sử dụng / dữ liệu con người | Xanh teal `#0F766E` |
| Tốt / đủ điều kiện | Xanh lá `#15803D` |
| Chờ kiểm tra / chờ xử lý | Hổ phách `#B45309`, nền nhạt `#FEF3C7` |
| Hỏng / lỗi / không đạt | Đỏ `#B91C1C`, nền nhạt `#FEE2E2` |
| Đề xuất / nhóm dữ liệu phụ | Tím `#7C3AED` |

Không cần ép từng mã hex nếu tương phản chưa đạt, nhưng phải giữ ý nghĩa màu
thống nhất dashboard/bảng/detail. Nhãn trạng thái luôn có chữ/icon, không chỉ
màu; màu biểu đồ gắn với key/category ID, không đổi theo thứ tự khi lọc.

Dùng font đang có hỗ trợ tiếng Việt, không phụ thuộc CDN mới; phân cấp rõ:
tiêu đề24–28px, số KPI28–36px, nội dung14–15px, chú thích12–13px. Padding
16–24px, gap16–20px; input/button40–44px; card bo12–16px, shadow nhẹ có chủ
đích. Tránh nền gradient khắp nơi và mọi thành phần cùng một kiểu card.

## 5. Dashboard: biểu đồ lớn phải ở đầu, không bắt kéo xuống

Bố cục desktop mục tiêu:

```text
Tổng quan thiết bị                         [Làm mới] [Xuất Excel]
[Phòng ban ▼] [Vị trí ▼] [Lọc thêm]          [Áp dụng] [Xóa lọc]

[Tổng thiết bị] [Đang sử dụng] [Trong kho] [Đề xuất đang mở]

┌───────────────────────────┬──────────────────────────────────┐
│ PHÂN BỔ THIẾT BỊ          │ CƠ CẤU LOẠI THIẾT BỊ             │
│ Donut lớn + tổng ở giữa   │ Biểu đồ thanh ngang lớn          │
│ số lượng, %, chú giải rõ  │ Nhãn đầy đủ + số từng loại       │
└───────────────────────────┴──────────────────────────────────┘

Thiết bị theo phòng ban          Đề xuất mới / việc cần chú ý
```

Đây là cấu trúc phải triển khai, không chỉ mockup. Header gọn48–60px; dải lọc
desktop một hàng khoảng44–56px; KPI90–112px; khu chart320–360px. Ở1440×900,
hai chart chính phải nằm trọn trong vùng nhìn đầu tiên sau shell; ở1366×768
thấy ngay phần biểu đồ chính và nhãn, không bị filter/công việc đang mở đẩy
xuống dưới. Xem thực tế ở browser zoom100%, không zoom nhỏ để làm đủ tiêu chí.

- Donut đường kính khoảng240–280px desktop, chữ tổng đọc rõ, legend có số và
  tỷ lệ. Biểu đồ thanh có trục/nhãn/số lượng rõ, không chỉ một danh sách chữ
  giả làm biểu đồ. Tooltip và bấm phần biểu đồ/legend mở danh sách đúng domain.
- Khu biểu đồ **nằm ngay dưới KPI**. Chuyển Công việc đang mở/Cần xử lý/ghi
  chú dài xuống dưới hoặc nhóm gọn. Không đặt khối giải thích dài trên chart.
- Bốn KPI có icon/nền accent riêng; số liệu trung tâm, nhãn ngắn. Định nghĩa
  chi tiết ở tooltip/nút thông tin; thông tin thiết yếu về nguồn/chưa kiểm tra
  vẫn có một nhãn gọn dễ thấy, không giấu để tạo cảm giác đã xác minh.
- Không vẽ tăng trưởng/tháng giả vì file chỉ là snapshot. Không thêm chart
  vô nghĩa để trang đầy hơn. Dữ liệu0/thiếu hiển thị rõ, không bịa tỷ lệ.
- Trên mobile chart xếp dọc, không ép hai chart bé tí; cho thấy chart đầu sớm
  sau KPI2×2. Skeleton/empty/error gọn, lỗi có Tải lại và không phá layout.

### Định nghĩa số liệu: sửa hiển thị, không sửa dữ liệu cho đẹp

Mỗi nhóm dùng domain backend rõ ràng, cùng scope/company. Danh mục chính là
thiết bị vật lý đang quản lý; loại dịch vụ và linh kiện đã nằm trong bộ máy
khỏi tổng vật lý như quy tắc hiện tại. Hồ sơ dịch vụ vẫn ở mục phụ phù hợp.

- **Trong kho**: vật lý, lifecycle active, nơi giữ stock; không lọc riêng
  availability available. Đủ điều kiện cấp phát là một chỉ tiêu con khác.
- **Đang sử dụng**: vật lý đang quản lý, nơi giữ employee/department/location/
  loan theo HOLDING_CUSTODY hiện có; đây là trạng thái ghi trên sổ, không phải
  xác nhận đang sử dụng thực tế. Nhãn ai giữ/vị trí phải thể hiện đúng.
- **Donut phân bổ** dùng các tập loại trừ nhau: Đang sử dụng, Trong kho,
  Khác/chưa xác định. Cùng mẫu số tổng vật lý đang quản lý; tổng số/tỷ lệ khớp.
  Không đưa “Chưa xác minh” vào cùng donut này vì nó có thể trùng hai nhóm đầu.
- **Đề xuất đang mở** đếm hồ sơ chưa hủy/chưa hoàn tất theo state/progress thật;
  có nháp thì thể hiện nháp, không chỉ đếm review rồi làm hồ sơ mới biến mất.
  Không cộng số dòng đề xuất thành số hồ sơ hoặc thành thiết bị tồn.
- Bộ lọc mỗi chart/KPI/list/export thống nhất cùng nhóm. Lọc vị trí thiết bị
  không có nghĩa vị trí đề xuất; đặt scope thiết bị/đề xuất rõ, không âm thầm
  lọc loại dữ liệu này bằng field của loại khác.

Reuse aggregation/drill-down backend `tp.equipment.dashboard`; chỉ thêm/sửa
helper/domain tối thiểu cần cho cách trình bày này. Không hardcode số baseline,
không kéo toàn bộ DB về JS rồi tự tính, không viết lại workflow/model nghiệp vụ.

## 6. Bỏ bộ lọc có sẵn trong input, thay bằng bộ lọc gọn đẹp

Yêu cầu “bỏ bộ lọc có sẵn trong ô tìm kiếm” nghĩa là bỏ chip/preset mặc định
như **Chưa ngừng quản lý** đang nằm trong ô, đồng thời bỏ dải9nút preset luôn
hiện và hai lớp search/filter lặp như ảnh. Không xóa backend domain/quyền.

Toolbar chuẩn của từng list:

```text
[Tìm tên, mã thiết bị, serial…] [Phân loại ▼] [Người sử dụng ▼]
[Bộ lọc (n)]                       [Thêm thiết bị] [Xuất Excel]
Đang lọc: chỉ hiện tiêu chí do người dùng chọn       54 kết quả
```

- Một ô search text duy nhất, không nhét facet/chip preset vào input; placeholder
  theo nội dung từng bảng. Không render thêm ô tìm tên/mã thứ hai ở dưới.
- Hai select nhanh theo bảng và một nút Bộ lọc mở popover/drawer các tiêu chí
  còn lại. Có label rõ, caret, focus/border đậm vừa đủ, nền trắng; không panel
  filter hai/ba hàng chiếm nửa màn hình khi chưa cần dùng.
- Bộ lọc nâng cao nằm trong drawer/Thêm, không chiếm hàng nút chính. Giữ khả
  năng nhóm/lưu bộ lọc hiện có nếu còn dùng, không nhân đôi UI cơ chế native.
- Bỏ `search_default_not_retired` khỏi UX ô search bằng xử lý đúng action/view;
  nếu phạm vi chỉ hồ sơ đang quản lý thì ghi tên/phạm vi ở tiêu đề hoặc domain
  hành động và vẫn có lối mở tất cả/ngừng quản lý. Không chỉ CSS hide chip mà
  để tiêu chí ẩn không thể biết hoặc bỏ. Bộ lọc tự chọn của người dùng vẫn phải
  xem/xóa được ở dòng chip riêng bên dưới toolbar.
- Áp dụng/Xóa lọc rõ ràng; pending khác applied; xóa lọc giữ domain chức năng,
  company và quyền. Count/paging/Excel cùng domain, reset page khi đổi lọc.
- Dùng SearchModel/helper dùng chung; thêm tùy chọn compact/collapse scoped
  EQUIP hoặc component cục bộ mỏng nếu cần. Không patch toàn hệ thống để tất
  cả HR/KH-KD cũng mất bộ lọc theo yêu cầu riêng của kho.

Tiêu chí theo bảng: Thiết bị lọc loại/người giữ/phòng/tình trạng/sở hữu; Tồn
kho lọc loại/tình trạng/khả năng cấp/vị trí; Đề xuất lọc người yêu cầu/phòng/
rà soát/khoảng ngày có thật. Ngày chưa biết khác ngày hôm nay. Bảng phụ vẫn có
lọc đúng nội dung theo DEC-044, có thể thu gọn theo cùng format.

## 7. Bảng: không chồng badge, đọc được và không quá nhiều cột

Thứ tự cột mặc định theo màn hình:

| Bảng | Cột chính |
| --- | --- |
| Thiết bị & người sử dụng | Mã; Thiết bị (model phụ trong ô); Phân loại; Người/phòng/vị trí đang giữ; Phòng ban; Tình trạng; Nơi giữ; Thao tác |
| Thiết bị tồn kho | Mã; Thiết bị; Phân loại; Vị trí kho; Tình trạng; Khả năng cấp phát; Thao tác |
| Đề xuất mua | Mã; Nội dung; Nhân viên/bộ phận yêu cầu; Ngày chứng từ nếu biết; Chi phí dự kiến; Rà soát; Kết quả duyệt; Thao tác |

Sở hữu/bảo hành/serial và trường phụ qua chọn cột hoặc chi tiết; không ép đủ
12cột vào màn laptop. Rà soát và duyệt của đề xuất là hai chiều riêng, không
tô “Đã duyệt” chỉ từ reviewed. Chi phí chưa biết hiển thị “Chưa có”, không0giả.

Header xanh nhạt, đường phân cách hàng/cột rõ nhưng nhẹ; zebra nhẹ, hover nền
xanh nhạt; dòng chọn rõ. Min row56–64px khi nội dung ngắn, tên dài clamp2dòng
và tooltip/chi tiết đầy đủ, không biến mỗi hàng thành một khối200px. Không sửa
chuỗi tên/nguyên văn trong DB để rút gọn giao diện.

**Sửa tận gốc lỗi badge:** `table.scss` hiện đặt ô badge overflow visible,
badge nowrap/max-width none; nội dung dài tràn sang cột bên cạnh. Bỏ cách này
trong scope EQUIP: cấp độ rộng cột phù hợp, badge max-width100%, cho wrap đúng
hoặc dùng nhãn ngắn tương đương + tooltip. Ví dụ “Cần kiểm tra trước khi cấp”
có thể trình bày “Chờ kiểm tra” với giải thích đầy đủ; không đổi state thật.
Không absolute position/negative margin để che lỗi hoặc cắt mất dữ liệu quan trọng.

Các nhóm trạng thái: Tốt xanh lá; Hạn chế/Chờ kiểm tra hổ phách; Hỏng đỏ; Chưa
xác định xám; Đang dùng xanh teal; Trong kho xanh dương; Đề xuất tím. Tooltip
và focus/touch phải đọc được, không phụ thuộc hover chuột để biết hết thông tin.

Giữ chọn dòng, sort, ẩn/hiện cột, pager10/20/50/100, số kết quả và export theo
quyền. Thao tác hiển thị **Xem** và menu `⋯` gọn; không một dãy nhiều nút màu
ở từng hàng. Sticky header dùng được trong vùng cuộn bảng; tránh nhiều thanh
cuộn dọc lồng nhau, cuộn ngang nếu cần chỉ trong vùng bảng.

## 8. Chi tiết thiết bị và đề xuất phải cùng phong cách

Thiết bị: header tên/mã/icon/phân loại, badge tình trạng/sở hữu rõ; khối **Ai
đang sử dụng / Đang ở đâu** nổi bật, HR avatar/tên/ID cùng nguồn. Ba phần chính
Thông tin, Sử dụng & bàn giao, Lịch sử; thông số sâu/bảo hành/nguồn/QR trong
khối thu gọn. Input có nhãn và khung rõ, dữ liệu chỉ đọc phân biệt với sửa.

Hành động chính theo state/quyền: Sửa nháp/Đăng ký/Cấp thiết bị/Thu hồi/Chuyển
người giữ, gọi action/wizard hiện có. Gom hành động ít dùng vào Thêm. Không
cho sửa người giữ trên hồ sơ đã đăng ký bằng write trực tiếp thay phiếu.

Đề xuất: form gọn để admin chọn nhân viên/bộ phận, ghi nhu cầu, cấu hình/lý do,
chi phí dự kiến nếu có, kèm tệp; dưới là bảng dòng rõ và lịch sử xử lý. Giữ
những dòng sửa/nâng cấp/chuyển máy đã nhập, dù menu chính tên mua thiết bị.
Rà soát/kết quả duyệt hiển thị tách biệt, điều kiện duyệt/nhận hiện có giữ.

Không tự tạo receipt/approval hoặc đổi tình trạng thiết bị để minh họa UI.
Không tự xóa hồ sơ đã chốt, phiếu opening, import provenance hay10dòng chờ.

## 9. Hiệu ứng và nhiều thiết bị

Hover150–200ms cho nút/menu/dòng; drawer180–220ms; biểu đồ xuất hiện/cập nhật
250–450ms có chủ đích. Không animation vô hạn, không làm chậm nhập liệu hoặc
gây layout shift. Dùng opacity/transform thích hợp, giữ số thật khi giảm chuyển
động; tôn trọng prefers-reduced-motion và tùy chọn hệ thống hiện có.

Desktop1440×900/1366×768, tablet1024×768/768×1024, mobile390×844/375×812:
grid/chart/filter không đè nhau; mobile drawer menu/filter, chart full-width,
bảng có vùng cuộn và cột ưu tiên. Nút44px trên cảm ứng, bàn phím/focus dùng
được; tiếng Việt có dấu không bị cắt. Zoom125% vẫn đọc/thao tác được.

Không thu nhỏ font cả hệ thống, không đổi độ rộng/sidebar HR/KH-KD để làm vừa.
Không dùng overflow hidden cả trang để che lỗi tràn. Bảo toàn vị trí/scroll
thích hợp khi đi chi tiết rồi quay lại danh sách.

## 10. Triển khai và bàn giao nhìn thấy được

Thứ tự: ghi thiết kế ngắn/token/wireframe trong `.local/equip-ui001/` → sửa
dashboard và domain hỗ trợ → sidebar → toolbar/filter/table → chi tiết → áp
đúng addon/asset trên18069 → mở browser, chụp trước/sau cùng role/viewport/data.
Không kết thúc ở kế hoạch/mockup; người dùng cần xem giao diện đã đổi thật.

Không bắt xác nhận bản thiết kế hoặc áp main lần nữa. Không đụng số liệu thật
để chụp hình; ảnh/DOM/download chứa dữ liệu chỉ giữ ignored. Nếu cần sửa helper
dùng chung thì giới hạn bằng option/context mặc định giữ nguyên ứng dụng khác.

Đối chiếu vận hành sau áp: hai chart ở đầu desktop, bốn mục menu chính, input
search sạch không chip mặc định, filter mở/đóng/clear, badge dài không overlap,
đổi trang/cột/export, mở detail/back và trạng thái hiển thị trên mobile. Xem
console/network và tự sửa lỗi trong scope. Giữ snapshot/binding/HR/user/quyền
so baseline; không đánh bộ test/AT PASS từ ảnh hoặc lint.

Cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP, EQUIP guide/design/acceptance và
inventory bộ lọc cho màn đổi. Chạy kiểm source tối thiểu (Ruff nếu Python đổi,
XML/manifest/JS/assets theo phạm vi), git diff --check, workflow finish/check
bằng change ID mới. Không bắt test18079 hoặc chạy toàn bộ suite trái chỉ đạo.

Báo cuối: URL18069; ảnh dashboard/list/detail desktop/mobile đã tự xem; bảng
menu cũ→mới/đưa vào phụ; file sửa và version đã áp; dữ liệu/quyền còn nguyên;
giới hạn chưa kiểm. Chỉ hoàn thành khi giao diện đã thay đổi rõ theo brief,
chart nằm trên, bảng không đè chữ và thao tác đọc dữ liệu thật được.
