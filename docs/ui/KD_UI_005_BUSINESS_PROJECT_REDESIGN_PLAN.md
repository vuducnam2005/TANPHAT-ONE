# KD-UI-005 — Thiết kế lại Kinh doanh và dự án

Ngày 07/11/2026, Asia/Saigon. **Trạng thái lúc soạn: PLAN_AND_PROMPT_READY.** Tiến độ thực thi CHG-20261107-007 xem [acceptance](../demo/KD_UI_005_ACCEPTANCE.md) và [as-built](KD_UI_005_BUSINESS_PROJECT_DESIGN.md). Phạm vi người dùng giao: hai mục trong nhóm Kinh doanh và dự án của KH-KD, gồm danh sách và màn hình chi tiết, đẹp hơn, rõ thao tác, có hover/animation.

## 1. Phạm vi và điểm bàn giao

| Màn hình | Nội dung cần hoàn thiện | Kết quả người dùng nhận được |
| --- | --- | --- |
| OPP-L | Danh sách Cơ hội và hồ sơ thầu | Bảng dễ đọc, thấy tên, khách hàng, tình trạng, hạn và phụ trách; tìm/lọc/chọn cột thuận tiện |
| OPP-D | Chi tiết/tạo/sửa cơ hội và hồ sơ thầu | Nhận diện hồ sơ, trạng thái và thao tác chính rõ; thông tin chia khối; ba tab chi tiết phù hợp nghiệp vụ |
| PRJ-L | Danh sách Hồ sơ dự án | Mã/tên/khách hàng/phụ trách/mốc rõ; giữ bảng và tính năng Project native |
| PRJ-D | Chi tiết/tạo/sửa dự án | Nhận diện dự án, thông tin chủ trì, phạm vi và phân công rõ; mở các hồ sơ liên quan đúng dự án |

Không thay Tổng quan, Home, các nhóm hồ sơ khác hoặc nghiệp vụ/phân quyền. Chỉ kiểm hồi quy các nơi có liên kết qua lại. Native Odoo + view/action + OWL/QWeb/SCSS có scope; giữ một nguồn dữ liệu và session.

**Có phiên khác đang thực thi:** lúc preflight checker còn đạt CHG-20261107-005, sau đó xuất hiện checkpoint `2026-11-07T06:25:22.075303+00:00` và `scripts/ui_home003.py`. Phiên lập kế hoạch gọi `start` thì nhận `RESUME`; không tạo checkpoint riêng, không finish/xóa/ghi đè checkpoint đang có. Lượt này chỉ tạo hai tài liệu KD-UI-005, không ghi status/changelog/roadmap/state đang do phiên triển khai sở hữu. Khi thực thi, đọc lại trạng thái mới, cập nhật bàn giao chủ trong batch CHG mới sau khi UI-HOME-003 đã kết thúc. Không lấy ghi nhận tại thời điểm này làm runtime bất biến.

[Prompt cho Claude](../prompts/CLAUDE_KD_UI_005_BUSINESS_PROJECT.md). Khung chung vẫn theo DEC-030/031; hoàn thiện KH-KD trước các phòng khác.

## 2. Quan sát và căn cứ

Ảnh người dùng gửi: `codex-clipboard-8d1163b4-0faa-43d2-b4ec-b7245a3c7837.png` và `codex-clipboard-f4bf428b-99ae-4bc9-973a-406f316bc242.png`, ngày 07/11/2026. Không sao chép ảnh/dữ liệu hồ sơ vào Git.

| Quan sát từ ảnh | Source đã đối chiếu | Hướng sửa dự kiến |
| --- | --- | --- |
| Form dài, khoảng trắng lớn, tên hồ sơ quá nổi so với nội dung | Hai form ở [workspace.xml](../../custom_addons/tp_kd_workspace/views/workspace.xml); form dùng hai group và notebook, style sheet chung | Header gọn, thông tin quan trọng xếp sát hợp lý, chiều cao theo nội dung |
| Nhãn khách hàng xuống dòng xấu; tên dự án bị cắt | [table.scss](../../custom_addons/tp_kd_workspace/static/src/table/table.scss) chỉ wrap many2one readonly; form native ưu tiên edit khi được phép | Nhãn trên ô; cung cấp đường đọc đầy đủ cho many2one khi đang sửa, giữ autocomplete native |
| Trạng thái tách khỏi thông tin, còn khó hiểu khai báo nội bộ | `kd_bid_state` có ba giá trị; nút chuyển trạng thái được backend kiểm | Đưa tình trạng gần tên/hành động, giữ chữ “chưa xác minh” nhìn thấy |
| Thiếu phân cấp giữa thông tin chính và tab | `kd_scope`, `kd_checklist`, `kd_receipt`, `kd_credential_ids` đã có | Nội dung từng tab rõ mục đích, trạng thái rỗng có hướng dẫn ngắn |
| Dự án có nhiều hồ sơ liên quan cần sắp lại | Form gốc có 3 smart button; 7 inherit thêm button vào `button_box` | Giữ 10 đường liên kết, ba nhóm chính nổi hơn, phần còn lại gom hợp lý bằng cơ chế native |

Đây là phân tích ảnh và source, chưa phải kết quả audit browser/CSS của bản mới. Tên chứa `seed` hoặc mã kiểm tra trong ảnh là dữ liệu hiện có; giữ nguyên, không sửa/hide tên để làm đẹp giao diện.

## 3. Thiết kế chung

Hướng hình ảnh: bàn làm việc quản trị hồ sơ công trình; sidebar xanh navy hiện tại, nội dung sáng, đường phân khối rõ, bảng có viền, thao tác xanh nhất quán. Điểm nhấn nằm ở tên hồ sơ và thao tác cần làm, không biến mọi nhóm thành một thẻ lớn có bóng.

| Thành phần | Quy định |
| --- | --- |
| Màu nền/bề mặt | `#F4F6F8` / `#FFFFFF` |
| Màu nhấn/khung sidebar | `#255F85` / `#17324D`, giữ token sẵn có |
| Chữ/đường phân cách | `#1F2937` / `#D9E2EC` |
| Chữ và kích cỡ | Font Odoo hiện có hỗ trợ tiếng Việt; thân 14–15px, nhãn 13–14px, tên hồ sơ 24–28px desktop, 20–24px mobile |
| Bố cục | Nội dung canh trái; rộng theo action container, tối đa dự kiến 1440px; khoảng cách 8/12/16/24px |
| Form | Nhãn trên ô cho thông tin dễ dài; hai khối chính desktop, một cột khi thiếu chiều rộng thực tế; không chiều cao cố định hoặc khoảng đệm lớn để lấp trang |
| Bảng | Giữ viền/cột/sticky/resize/pager/Thoáng–Gọn/chọn cột native từ KD-UI-003; đo lại khi sidebar mở/thu và zoom |
| Trạng thái | Có nhãn chữ; màu hỗ trợ phân biệt, không dùng màu đơn độc |

Header/control panel và statusbar không đè nhau khi cuộn. Ưu tiên sticky native; nếu cần sticky thêm, giới hạn một vùng hành động và đo offset thật. Không thêm scrollbar dọc lồng nhau hoặc dùng `overflow:hidden` để che lỗi.

### OPP-L — Bảng cơ hội

Toolbar giữ Tạo mới nếu được phép, tìm kiếm, bộ lọc/group/favorite native, tùy chọn cột, mật độ, phân trang. Bổ sung search view riêng nếu thiếu, chỉ lọc trên field/domain hiện có: tình trạng hồ sơ, hình thức, người phụ trách, dự án; không mở rộng tập dữ liệu.

Thứ tự cột chính: tên hồ sơ → khách hàng/chủ đầu tư → tình trạng hồ sơ → hạn chuẩn bị/nộp → phụ trách → hình thức. Dự án/nguồn/phạm vi là cột tùy chọn theo thiết kế hiện có. Giữ đọc đủ tên/trạng thái, không ép dòng đồng chiều cao khi tên dài. Dòng hover nhẹ, có focus/checkbox, bấm mở form native. Không thêm kanban hoặc KPI trong batch này.

### OPP-D — Chi tiết cơ hội và hồ sơ thầu

```text
Cơ hội và hồ sơ thầu / Tên hồ sơ              [Điều hướng bản ghi]
Tên hồ sơ đầy đủ                   [Thao tác theo trạng thái/quyền]
Tình trạng hồ sơ + “Chưa xác minh” khi đã khai báo nộp
┌ Khách hàng và dự án ──────────┬ Phụ trách và kế hoạch ─────────┐
│ Khách hàng / chủ đầu tư       │ Người phụ trách                │
│ Dự án liên quan — đọc đủ tên  │ Hình thức                      │
│ Nguồn thông tin, công ty      │ Hạn chuẩn bị / nộp             │
└──────────────────────────────┴─────────────────────────────────┘
[Phạm vi / gói thầu] [Checklist hồ sơ] [Năng lực sử dụng]
Nội dung theo tab, đọc/sửa bằng field native đúng quyền
```

- Giữ `name`, `partner_id`, `tp_project_id`, `kd_source`, `company_id`, `user_id`, `kd_route`, `kd_deadline`; tránh lặp cùng field ở hai vị trí có thể cùng sửa.
- Tab Phạm vi: `kd_scope`, rộng vừa đọc, chiều cao theo nội dung.
- Tab Checklist: `kd_checklist` hiện là **Text**, `kd_receipt` là Char. Trình bày thành hai phần rõ; không tạo checkbox có lưu hoàn tất/tỷ lệ từ văn bản hoặc biến căn cứ khai báo thành attachment/upload.
- Tab Năng lực: chỉ `kd_credential_ids` đã được lọc quyền, giữ chọn hồ sơ có sẵn, `no_create`. Không lộ `kd_credential_link_ids`, không làm mất liên kết riêng tư khi user sửa danh sách nhìn thấy. Không ép đổi widget tag thành bảng nếu chưa có thiết kế/kiểm chứng inverse/command.
- Nút chính `action_kd_prepare`, `action_kd_record_submission` chỉ hiện/chạy theo điều kiện đang có. `kd_bid_state` không cho click ghi trực tiếp. Luồng `direct` không được vẽ như phải nộp thầu hoặc đã nộp thành công.
- Không thêm nút Trúng thầu/Ký/Duyệt/Upload/Tạo hợp đồng từ cơ hội nếu backend chưa hỗ trợ. Ghi rõ thao tác chưa lưu và dùng Save/Discard/Stay native; không tự đặt chế độ Xem/Sửa mới làm thay native autosave/dirty guard.
- Many2one: khi readonly cho wrap; khi edit giữ autocomplete/dropdown và nút mở native. Nếu input không thể wrap, cho preview đầy đủ bằng text an toàn từ giá trị đang đọc, dùng được bàn phím/chạm, không chỉ tooltip hover; không thêm RPC đọc hồ sơ ngoài quyền.

### PRJ-L — Bảng dự án

Mã dự án → tên dự án → khách hàng/chủ đầu tư → quản lý dự án → mốc bàn giao; phòng chủ trì/công ty và cột native phụ vẫn tùy chọn. Kế thừa `tp_kd_project_list`/`ProjectListController`, không thay bằng list thường làm mất View Tasks/favorite. Giữ domain `tp_managed=True` và unique mã theo công ty; không thay dữ liệu để sửa cách hiển thị.

### PRJ-D — Chi tiết Hồ sơ dự án

```text
Hồ sơ dự án / Mã dự án                      [Điều hướng bản ghi]
Tên dự án đầy đủ                         [Lưu/hủy native khi sửa]
Mã dự án — khách hàng — phòng chủ trì (thông tin sẵn có)
[Cơ hội / thầu]  [Hợp đồng]  [Kế hoạch / WBS]  [Hồ sơ liên quan]
┌ Nhận diện và khách hàng ─────┬ Chủ trì và mốc bàn giao ───────┐
│ Mã, khách hàng, công ty       │ Phòng chủ trì, quản lý, mốc    │
└──────────────────────────────┴────────────────────────────────┘
[Phạm vi / đầu ra] [Phân công — chỉ người được quyền]
```

- Giữ field/model; không tạo trạng thái dự án, timeline, % tiến độ, doanh thu hoặc tổng tiền mới.
- Giữ 3 action chính cơ hội/hợp đồng/WBS và 7 action đã có: giao khoán, sản lượng, nghiệm thu, đề nghị thanh toán, kế hoạch định kỳ, năng lực/chứng chỉ, nghĩa vụ. Dùng native smart-button/overflow để gọn, không 10 nút lớn cùng hàng, không số lượng giả.
- Giữ anchor `div[name=button_box]` cho 7 inherit hiện tại; kiểm **compiled arch** tất cả addon, không chỉ form gốc. Nếu cần thay cấu trúc thì phải cập nhật/test mọi inherit liên quan trong scope, tránh nút bị mất/trùng/không click được.
- “Phân công” chỉ đúng nhóm hiện tại; user thường đọc hồ sơ trong scope không tự được sửa dự án/phân công. Không biến màn này thành quản trị grant người thật.
- Mở hồ sơ liên quan giữ action/domain/default đúng project, `child_context` loại default/view cũ, `tp_kd_leaf` tô đúng sidebar. Không rò context form dự án sang model khác.

## 4. Hover và animation có mục đích

| Tương tác | Hiệu ứng dự kiến | Giới hạn |
| --- | --- | --- |
| Hover dòng bảng | Đổi nền 120ms, focus rõ | Không dịch chuyển cột/dòng; không RPC |
| Nút/link/input | Màu/viền/focus 120–160ms, phản hồi nhấn nhẹ | Không rung/nảy, không trông như đã lưu khi chưa lưu |
| Chuyển tab | Fade ngắn 140–180ms nếu không remount nội dung | Không mất field chưa lưu, vị trí cuộn hay focus |
| Mở nhóm hồ sơ liên quan | Mở/đóng 160–200ms nếu cần custom | Không đẩy mất vùng thao tác hoặc làm kẹt bàn phím |
| Lần mở form | Một lần rất nhẹ, tối đa 180ms, có thể bỏ nếu gây flash | Không chạy lại khi gõ/patch/đổi field; không animate toàn bảng theo từng dòng |

Tôn trọng cả `prefers-reduced-motion` và `kdPrefs.motion`: chế độ giảm chuyển động tắt animation/transform không cần thiết; chức năng vẫn hoàn chỉnh. Không thêm thư viện animation/CDN/font ngoài.

## 5. Lộ trình và đầu ra từng lô

| Lô | Việc làm | Đầu ra dùng để kiểm |
| --- | --- | --- |
| A — Inventory và mẫu | Đối chiếu action/view/field/quyền, compiled arch, ảnh trước; wireframe 4 màn, acceptance và token có scope | Thiết kế thực thi, ảnh trước, bảng ánh xạ/ngoài scope; chưa áp dev |
| B — Cơ hội và hồ sơ thầu | Bảng/search và form/tabs/nút/many2one; native create/save/transition trên clone | OPP-L/OPP-D hoàn chỉnh ở desktop/mobile, thử bid/direct/quyền/validation; ảnh sau |
| C — Hồ sơ dự án | Bảng/controller và form/action liên quan/phân công | PRJ-L/PRJ-D hoàn chỉnh; 10 đường action đúng context/scope, ảnh sau |
| D — Hoàn thiện và tích hợp | Hover/motion/responsive/keyboard; hồi quy, backup sát áp, apply18069, verify chỉ đọc, runbook/rollback | Giao diện đã tự kiểm trên18069 với bằng chứng; audit độc lập và nghiệp vụ vẫn riêng |

Không cam kết thời lượng khi chưa tái hiện runtime. Thực thi tuần tự trong cùng phiên có checkpoint; không giao hai AI cùng sửa shared XML/SCSS.

## 6. Ca nghiệm thu bắt buộc

| ID | Điều phải chứng minh |
| --- | --- |
| BP01 | Bốn màn đủ nội dung/field/action đúng inventory; không nút giả, không đổi tên/dọn dataset |
| BP02 | OPP-L: tìm/lọc/group/sort/pager/chọn cột/Thoáng–Gọn, tên/trạng thái dài đọc được, count/domain đúng baseline |
| BP03 | OPP-D: tạo/sửa/lưu/mở lại, tab Text/Char/năng lực đúng field, không mất dữ liệu khi chuyển tab |
| BP04 | Bid identified→preparation cần đủ nguồn/phạm vi/hạn/checklist; khai báo nộp cần căn cứ; sai state/thiếu dữ liệu bị từ chối; direct không khai báo nộp |
| BP05 | User thiếu grant hoặc assignment/company/project bị từ chối đúng; không mở quyền tiền/file; private credential không lộ và vẫn được bảo toàn khi sửa phần thấy được |
| BP06 | PRJ-L giữ ProjectListController/tính năng native, domain và mã; PRJ-D giữ phân công chỉ manager, user thường không tự sửa cấu hình dự án |
| BP07 | 10 action liên quan đúng model/view/domain/default/leaf; không context form cha, nút trùng/mất do inheritance; thử từ sidebar/Tổng quan/deep link |
| BP08 | Save/Discard/Stay, đổi bản ghi/trang/Back/Home, lỗi validation/AccessError/session giữ; không rời form hoặc gửi action khi lưu thất bại |
| BP09 | Tên 200+ ký tự, tiếng Việt, null khác0, ngày đủ thông tin, many2one đang sửa có cách đọc đầy đủ bằng chuột/bàn phím/chạm; không chỉ title tooltip |
| BP10 | 360/390/768/1024/1440/1920px, zoom125/150%, sidebar mở/thu, label/input/dropdown/statusbar/smart buttons, scroll/sticky; bảng cuộn ngang trong vùng bảng, không tràn toàn trang |
| BP11 | Hover/tab/nhóm mở/animation/reduced-motion/keyboard/focus/touch; không remount input, mất chữ/IME/caret hoặc RPC do hover |
| BP12 | Home/Tổng quan/KH-KD khác/CRM-Project ngoài workspace/TP Contracts không rò style; dữ liệu/quyền/attachment/menu ngoài delta UI giữ nguyên sau apply |

Viết acceptance/test theo hành vi trước code; test Odoo liên quan, browser thực tế, HOOT nếu thêm JS/widget/controller. Test ghi chỉ trên clone bằng dữ liệu giả; dev verify chỉ đọc sau backup. Ruff/XML/JS/assets phù hợp và workflow checker khi bàn giao. Batch lập kế hoạch này chỉ kiểm tài liệu, không chạy application tests.

## 7. Ranh giới kỹ thuật và hoàn tất

Code chính nằm trong `custom_addons/tp_kd_workspace`; thêm class riêng cho **hai** list/form và SCSS riêng. Không dùng `.tp_kd_form` chung để thay form của 10 nhóm khác. Tái sử dụng token, không đổi biến ở `body.o_tp_kd_shell` cho toàn app. Không sửa `odoo/`, `addons/`, React, API, security, state, grant hoặc model chỉ để làm layout.

Backend helper chỉ được điều chỉnh binding view/context nếu chứng minh cần để bốn màn mở đúng và giữ nguyên domain/security; kiểm hồi quy riêng. Khác biệt nghiệp vụ thật phải ghi gap cho batch sau, không tự nới phạm vi. Checklist dạng cấu trúc, quản lý kết quả thầu chính thức và hồ sơ phê duyệt không được coi đã có vì form mới đẹp hơn.

**Tiêu chí xong:** bốn màn dùng được với role phù hợp, nhìn rõ hồ sơ/tiếp theo làm gì/đường sang hồ sơ liên quan, hover/motion ổn định và thân thiện mobile, test/evidence đủ, dữ liệu/quyền nguyên. Sau đó audit độc lập và người dùng review; không đánh dấu toàn KH-KD hoàn tất hoặc mở pilot từ một batch giao diện.
