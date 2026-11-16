# UI-TABLE-FILTER-001 — Bộ lọc đúng nội dung cho toàn bộ bảng TANPHAT ONE

Làm việc trong `C:\TANPHAT ONE`.

## 1. Mục tiêu và quyền thực thi

Triển khai bộ lọc phù hợp từng bảng trên toàn hệ thống đang dùng, bắt đầu HR,
tiếp đến KH-KD và các ứng dụng Odoo hiện có. Giữ cách thao tác nhất quán và
lưu coverage để phòng ban sau này không bỏ sót. Không chỉ thêm ô tìm kiếm chung
hay một dropdown giống nhau cho mọi bảng. Làm thay đổi nhìn thấy được và có
ảnh trước/sau chứng minh, không chỉ sửa tài liệu.

Prompt này giao **triển khai và kiểm thử trên `tp_tanphat_test` / 18079**.
**Không áp/upgrade/seed/ghi main `tp_tanphat_dev` / 18069** trong task này.
Sau test bàn giao source, bằng chứng và kế hoạch áp main để người dùng quyết định
riêng. Không commit/push. Không sửa dữ liệu thật hoặc mật khẩu/tài khoản/quyền.

## 2. Đọc và kiểm baseline trước code

- `AGENTS.md`, `.agents/skills/tanphat-odoo-delivery/SKILL.md`.
- `docs/PROJECT_STATUS.md`, `docs/AI_CHANGE_WORKFLOW.md`, `docs/DECISIONS.md`,
  `docs/ROADMAP.md`, `docs/HANDOFF_TEMPLATE.md`, `docs/AI_TOOLING_PLAYBOOK.md`.
- `docs/ui/TP_TABLE_FILTER_STANDARD.md` — quy chuẩn bắt buộc, `DEC-044`.
- `docs/ui/TP_TABLE_FILTER_INVENTORY.md` — phân tích nguồn, chưa phải kiểm runtime.
- `docs/ui/KD_UI_007_TABLE_INVENTORY.md`, `docs/ui/KD_UI_007_DESIGN.md`,
  `docs/demo/KD_UI_007_ACCEPTANCE.md`.
- `docs/demo/HR_LIST_013_ACCEPTANCE.md`, `docs/demo/HR_EMP_014_ACCEPTANCE.md`,
  `docs/demo/UI_INPUT_001_ACCEPTANCE.md`, `docs/demo/UI_SHELL_UNIFY_001_ACCEPTANCE.md`.
- `ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md`.

Dùng skill `frontend-design` cho UI, Ponytail cho tái sử dụng, Playwright cho
bằng chứng nếu có. Đọc SKILL.md thật, báo skill đã dùng; không cài Graphify,
OmniRoute hoặc dependency mới chỉ để hoàn thành task bảng.

Kiểm `git status`, checkpoint, workflow checker và runtime/source hiện hành.
Không xóa thay đổi có sẵn; không finish thay batch khác. Chạy
`scripts/ai_workflow.py start` trước sửa. Tái sử dụng DB test theo runbook,
một tác vụ ghi tại một thời điểm, không tạo thêm DB theo task. Nếu schema/registry
test khác main, ghi rõ baseline và đồng bộ theo runbook; không restore test đè main.

## 3. Inventory runtime và acceptance trước triển khai

Resolve các menu/action/view đang dùng theo role, đối chiếu XML kế thừa đã merge,
`fields_get`, searchability và domain bắt buộc. Ghi từng vị trí theo mẫu inventory:
list chính, smart button, bảng con, popup chọn, wizard, audit, report, bảng trong
dashboard và ứng dụng native đang dùng ngoài HR/KH-KD. Không đếm model thay cho
vị trí bảng; cùng model khác action có thể cần bộ lọc khác.

Đọc `HrTableTools`, `KdTableTools`, `KdRelationField`, search views và report service
trước thiết kế. Phân biệt **đã có native search**, **thiếu lọc nhanh dễ thấy**,
**thiếu mapping đúng nội dung**, **N/A có lý do**. Coverage KD-UI-007 là lịch sử
07/11; kiểm bổ sung dự án/đấu thầu, HR hợp đồng/lịch sử và thay đổi mới.

Ghi acceptance AT-F01–AT-F12 ở mục 7 trước code. Không cần dừng xin xác nhận
routine design; chỉ ghi gap có căn cứ và giữ các scope không phụ thuộc tiếp tục.

## 4. Thiết kế và triển khai

### 4.1 UI dùng chung

- Một ô search native; hàng **Lọc theo** có tiêu chí đúng nội dung bảng, **Áp dụng**,
  **Xóa bộ lọc**, **Bộ lọc nâng cao**, chip đang áp và số kết quả.
- Khoảng 3–5 filter chính; danh mục nhỏ dùng ít hơn. Advanced chứa phần còn lại
  được phép tìm, không render dày đặc tất cả cột thành input.
- Nền sáng, label tiếng Việt, ô chọn/input khung rõ; dùng token `UI-INPUT-001`.
  Không chỉnh sidebar/định danh/người dùng. Menu hiện hành có **Thông tin cá nhân**
  và **Đăng xuất**, không quay lại yêu cầu logout-only cũ.
- Giữ 10/20/50/100 và pager hiện có; grouped list ghi đúng nhóm/bản ghi. Mobile
  panel thu gọn, keyboard/focus, empty/loading/error, reduced motion đầy đủ.
- Chọn giá trị chưa Áp dụng không tác động export/count/bảng; không có hai bộ
  state native/custom chạy độc lập. Chip/favorite/native search cập nhật ngược
  vào toolbar; nếu domain nâng cao không thể biểu diễn, giữ facet và báo có điều
  kiện nâng cao, không âm thầm bỏ điều kiện đó khi Apply.

### 4.2 Theo từng nhóm bảng

Thực hiện đủ inventory, không chỉ ví dụ bên dưới:

1. **Nhân viên**: Phòng ban, Chức vụ, Loại hình lao động, Tình trạng tài khoản;
   tìm mã/tên/login. Tình trạng: Mở / Khóa / Chưa có tài khoản.
2. **Cần bổ sung / Lưu trữ / Chưa có tài khoản**: filter riêng phù hợp từng action;
   giữ domain bắt buộc, context active/archive và nhóm phòng ban đầu tiên.
3. **Phòng ban/chức vụ/nơi làm việc/danh mục HR**: tên, cấp trên, quản lý, loại,
   đang dùng theo field thật; không tạo filter nghiệp vụ không liên quan.
4. **Nhập/đối chiếu**: lô theo trạng thái/người/ngày/tệp; dòng theo action,
   phòng, mã nguồn/xung đột; giữ quan hệ batch và các dòng chưa lưu.
5. **Hợp đồng HR/phiên bản/audit/lịch sử/bảng con hồ sơ**: lọc đúng loại/ngày/
   người/mã/action; không đồng nhất hợp đồng giấy tờ và phiên bản hồ sơ.
6. **KH-KD**: cấu hình riêng Dự án, Đấu thầu, Quản lý dự án, Quản trị dự án,
   Hợp đồng/phụ lục, WBS/Công việc, Phân công, Giao khoán, Kế hoạch, Sản lượng,
   Nghiệm thu, Đề nghị thanh toán, Chứng chỉ, Nghĩa vụ, tài liệu/audit và bảng con.
   Các state BASE/rà soát/ký/hiệu lực không dùng thay cho nhau.
7. **Báo cáo/Tổng quan**: mỗi bảng/báo cáo có tiêu chí có nghĩa; kỳ/dự án/chủ trì
   đồng bộ backend, biểu đồ/drill-down và Excel, giữ khác biệt mục đích hai khu vực.
8. **Odoo app hiện có**: bổ sung search view qua custom inheritance khi thiếu;
   không cài thêm ứng dụng. Bảng chọn bản ghi, quản trị, tài liệu và popup không
   bỏ sót; tiêu chí theo model/actor/parent thực tế.

Nếu filter cần field chưa tồn tại, ghi gap và dùng field nguồn/search method
hợp lệ nếu đủ nghĩa. Không tự tạo state, ngưỡng quá hạn hay mô hình nghiệp vụ mới.

### 4.3 Tính đúng và bảo mật

- Reuse SearchModel/domain/search view/facet/favorite native; tái sử dụng code
  HR/KD, chỉ chia sẻ phần nhỏ có người gọi thật. Report OWL giữ service đã có;
  không viết engine chung mới hoặc thêm React/Ant Design.
- AND giữa các tiêu chí, OR trong nhiều lựa chọn cùng tiêu chí. many2one theo ID;
  xử lý Tất cả/Chưa khai báo, null/0, date/datetime/timezone theo quy chuẩn.
- Filter ở server trên toàn dataset được phép, sau đó count/order/page; export
  dùng cùng domain đã áp, có nhãn nếu chỉ xuất dòng chọn. Giữ guard formula injection.
- Options/autocomplete/count/group/tổng/export đều kiểm ACL/rule/company/grant,
  không `sudo` hoặc enumerate danh bạ ngoài scope. Người không có quyền tiền
  không dò được tiền qua filter/field nâng cao/options/count/error/RPC trực tiếp.
- Giữ action/parent domain, `active_test` và scope khi Clear; giữ department
  grouping HR; đổi role/company/hết phiên không hiện cache của người trước.
- X2many đã lưu lọc toàn relation ở server; đang dirty/new giữ toàn ORM commands,
  không tự save/discard/ẩn mất dòng. Vô hiệu hóa kèm lý do khi chưa lọc an toàn.
- Bảng cấu trúc tĩnh chỉ N/A khi nêu rõ lý do và role review; không miễn trừ
  tất cả popup. Bảng cap có nhãn giới hạn và đường mở nguồn, không paging giả.
- Không sửa `odoo/`, `addons/`, React legacy; code trong `custom_addons/`.
  Không thay state/action workflow, quyền người thật, file/chatter hay posting.

## 5. Thứ tự làm để hoàn thành toàn phạm vi

1. **S0 — Kiểm kê + AT**: inventory action/view/field/quyền hiện hành, ảnh baseline.
2. **S1 — HR**: hoàn thiện toolbar/filter và các action/bảng con HR; test hợp lệ/âm.
3. **S2 — KH-KD**: reuse KD-UI-007, điều chỉnh cấu hình theo bảng mới, test report/export.
4. **S3 — Ứng dụng native còn lại**: đóng coverage menu/action/table đang dùng,
   ghi N/A có lý do, regression shell/menu/forms.
5. **S4 — Nghiệm thu trên 18079 và bàn giao**: ảnh, test, hướng dẫn và runbook áp main.

Không dừng sau S1 rồi tuyên bố hoàn thành toàn hệ thống. Nếu có blocker thực,
ghi chính xác vị trí chưa đạt và tiếp tục các phần độc lập. Không đánh DONE cho
phòng ban đang placeholder; quy chuẩn/checklist là đầu vào cho đợt phát triển sau.

## 6. Dữ liệu và môi trường kiểm thử

Chỉ dùng dữ liệu giả cho thao tác ghi trên test. Fixture định danh/idempotent,
đủ hơn một trang, nhiều phòng, nhiều trạng thái, khác company và quyền tiền.
Không đưa PII/credential/ảnh hồ sơ thật vào Git hoặc báo cáo. Tái sử dụng test
runner hiện có; không phát sinh cả bộ framework mới. Không sửa password thật
để chụp ảnh. Bằng chứng browser ở `.local/` ignored, session có tên riêng.

## 7. Acceptance bắt buộc

Mỗi AT ghi actor, bảng/action, setup, thao tác, kết quả mong đợi/thực tế và evidence.

| ID | Kết quả phải chứng minh |
| --- | --- |
| AT-F01 | Coverage đủ mọi vị trí đang dùng trong inventory; bảng nào đã có/đã bổ sung/N/A/còn thiếu rõ ràng; không chỉ list HR |
| AT-F02 | Toolbar đúng nội dung từng bảng, nhãn dễ hiểu; không bộ lọc vô nghĩa; pending/applied, native facet/favorite/advanced sync hai chiều, không mất domain nâng cao |
| AT-F03 | Nhiều trang: kết quả đúng cả các bản ghi ngoài trang đầu; AND/OR nhiều lựa chọn đúng; page về đầu khi Apply; sort/cột và back từ detail giữ đúng |
| AT-F04 | Clear từng chip/tất cả không gỡ domain của missing/archived/pending, parent hay scope; HR luôn nhóm phòng ban đầu tiên; đơn vị pager đúng |
| AT-F05 | Chưa khai báo/0/False, khóa/chưa có tài khoản/lưu trữ khác nhau; date from>to báo lỗi, cuối ngày/timezone, đồng tiền khác nhau xử lý đúng |
| AT-F06 | Admin, HR, HEAD KH-KD, nhân sự scope hạn chế, người không quyền tiền và công ty khác: query/options/count/group/export/error/RPC không lộ dữ liệu hoặc nới quyền |
| AT-F07 | Bảng con/popup chọn/smart button lọc đúng parent trên toàn relation; new/dirty không mất dòng, commands, selection hoặc save/discard ngầm; snapshot readonly giữ nguyên |
| AT-F08 | Count/bảng/biểu đồ/drill-down/Excel cùng điều kiện đã áp; đọc lại XLSX và kiểm bộ record thật, không chỉ kiểm file tải được; export selection có nhãn rõ |
| AT-F09 | Empty/loading/error/retry và race đổi filter nhanh: response cũ không ghi đè; đổi company/role/hết phiên bỏ dữ liệu cũ; không persist từ khóa nhạy cảm |
| AT-F10 | Desktop 1440x900 và mobile 390x844 + zoom 200%, keyboard/focus/labels/reduced motion; filter không tràn trang, giữ giá trị khi đóng mở panel |
| AT-F11 | Các luồng thêm/sửa/dirty form, mở chi tiết, account lock, logout và sidebar hiện hành không hồi quy; xác nhận không sửa main 18069 |
| AT-F12 | Tài liệu/entrypoint cho phòng ban mới có checklist bộ lọc, mapping/backend scope, count/export/mobile và evidence; không tuyên bố deployed khi chỉ test |

Chạy XML/assets/OWL/HOOT hiện có; Odoo tests liên quan cho domain/security/search
method/backend; Playwright E2E đủ các nhóm khác cách xử lý; Ruff nếu sửa Python;
`git diff --check`; upgrade/test chỉ trên 18079. Mỗi vị trí có verification,
nhóm dùng cùng cơ chế có thể dùng test tham số; không copy test mirror code.
Chỉ chạy React typecheck khi thật sự sửa legacy (ngoài phạm vi mặc định này).

## 8. Bàn giao

- Cập nhật inventory với nguồn/runtime, field/operator, actor, domain, coverage
  và link test/ảnh; cập nhật quy chuẩn nếu cần, không tự đổi quyết định đã xác nhận.
- Tạo `docs/demo/UI_TABLE_FILTER_001_ACCEPTANCE.md` (AT-F01–12 và coverage),
  `docs/demo/UI_TABLE_FILTER_001_USER_GUIDE.md` (cách lọc từng nhóm, Xóa,
  favorite, xuất đúng kết quả, giới hạn dirty/cap).
- Cập nhật `PROJECT_STATUS`, `CHANGELOG`, `ROADMAP`, prompt index và README addon
  phù hợp. Giữ checklist trong `AGENTS`, `AI_CHANGE_WORKFLOW`, `HANDOFF_TEMPLATE`.
- Ghi runbook backup DB+filestore, restore verification trên test theo quy trình
  hiện có, exact source, module upgrade và read-only smoke/rollback cho lần áp main
  **sau khi được giao riêng**; không restore test đè main hoặc tạo thêm DB.
- `scripts/ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN --check "<thực chạy>"`
  rồi `scripts/ai_workflow.py check`. Không commit/push.

Báo cuối: số bảng/action đã kiểm và trạng thái từng nhóm; ví dụ filter HR/KD;
component/search view/backend đổi; test thực chạy/kết quả; ảnh trước/sau; gap và
N/A; đường dùng trên test. Xác nhận **18069 chưa áp**, chưa đổi dữ liệu/quyền/
workflow nghiệp vụ, và nêu chính xác bước cần làm để áp main khi người dùng giao.
