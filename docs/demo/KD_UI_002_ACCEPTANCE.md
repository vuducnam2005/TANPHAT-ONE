# KD-UI-002 — Acceptance sidebar và Tổng quan KH-KD

Viết trước khi code, ngày 06/11/2026. Kết quả từng mục được ghi ở mục "Evidence" sau khi chạy. Thứ tự là clone `tp_tanphat_kdui002_20261106` (cổng 18289), sau đó dev 18069. Đây là technical acceptance; không phải business acceptance hay pilot.

## A. Backend / report (Odoo tests, tag `/tp_kd_workspace`)

| ID | Kiểm | Kỳ vọng |
| --- | --- | --- |
| R1 | G01 từng model × state | Bằng `search_count(I(m,'all') + state)` trong env actor. 3 phần rời nhau, tổng = count all. |
| R2 | G01 drilldown | `action_kd_open('g01')` trả domain đếm ra đúng số của segment. |
| R3 | G02 | done + overdue + open = tổng task từng dự án. Task không hạn thuộc "còn lại". Task đã đóng mà quá hạn vẫn tính là hoàn thành. Drilldown bằng count. |
| R4 | G03 | Đếm theo `kd_route` × `kd_bid_state` khớp `search_count`. Nhánh direct đếm riêng. |
| R5 | G04 kỳ | Lọc theo month khác quarter/year, không cộng chéo. Nếu chưa xác nhận hoặc nguồn không comparable thì value = None (không phải 0) và có nhãn trạng thái. 0 thật (confirmed + comparable) = 0. Mục tiêu 0 thì không có %. |
| R6 | G04 quyền | Actor không có financial_read hoặc mất assignment thì không có value/tooltip, chỉ có số plan bị loại. Grant một phần thì chỉ có plan của dự án được phép. Sau khi thu hồi, lần gọi tiếp không còn value. |
| R7 | G05 biên ngày | Hôm qua là hết hạn. Hôm nay và hôm nay+30 thuộc nhóm "trong 30 ngày". Hôm nay+31 thuộc nhóm "sau 30 ngày". |
| R8 | KPI và Việc của tôi | Tổng tab = Σ `search_count` từng nguồn. Phân trang không đổi tổng. Mỗi dòng mở đúng (model,id). |
| R9 | Bảng dự án | Sort whitelist, tìm theo mã/tên/khách hàng, phân trang. Count từng dòng khớp domain drilldown. |
| R10 | Whitelist | key/kind/order/tab/state/bucket lạ thì UserError. project_id ngoài quyền thì UserError, không lộ tên. Không có tham số model/domain. |
| R11 | Outsider | User không có dự án thấy 0 và danh sách rỗng, không lỗi. Metadata không đọc được tiền. |
| R12 | Tạo hồ sơ | Danh sách kind chỉ gồm loại được phép. `action_kd_create` cho kind không được phép thì AccessError/UserError. Form mở có `default_project_id`. |
| R13 | Regression | Test hiện có của `tp_kd_workspace` và TP Contracts vẫn xanh. Menu lá giữ XMLID và action. |

## B. Trình duyệt (Playwright, `scripts/kd_ui002_ui.cjs`)

| ID | Kiểm |
| --- | --- |
| B1 | Sidebar hiện trên Tổng quan, list, form, Contracts và WBS của KH-KD. Home và app khác không có sidebar, không có class `o_tp_kd_shell`. |
| B2 | Nhóm mở/đóng bằng chuột và Enter/Space. `aria-expanded`/`aria-controls` đúng. Submenu ẩn không nhận focus. |
| B3 | Active và ancestor đúng khi click, deep link, refresh và Back/Forward. Tổng quan và Báo cáo KH-KD (cùng action) giữ đúng lá đã chọn. |
| B4 | Tìm "nghiem thu" (không dấu) tự mở nhóm và hiện lá khớp. Không khớp thì hiện "Không tìm thấy". Xóa tìm thì trở lại trạng thái trước. |
| B5 | Thu gọn/mở rộng sidebar được lưu sau reload. Tùy chọn mật độ/chuyển động được lưu. Khôi phục mặc định chỉ xóa key UI. |
| B6 | Form có thay đổi chưa lưu, bấm lá khác thì native vẫn xử lý lưu/hủy. Không mất dữ liệu. |
| B7 | Ở 390px: nút Menu mở drawer. Đóng được bằng Escape, backdrop và X. Focus trở về nút. Không tràn ngang trang. |
| B8 | Tổng quan: số trên mỗi segment G01–G05 và ô bảng bằng số record của list nguồn mở ra khi bấm (đối chiếu từng cái). |
| B9 | Filter dự án, refresh và xóa bộ lọc đều có loading. Request cũ không ghi đè. Lỗi giữ số cũ và nhãn cũ. |
| B10 | Bảng dự án: tìm, sort, phân trang, chọn cột, "Thao tác ▾" mở đúng action. |
| B11 | Tạo hồ sơ ▾ mở form/wizard đúng loại với dự án mặc định. Đóng mà không lưu thì không tạo record. |
| B12 | Ảnh trước/sau ở 1440/1024/390 (cộng 360/768 và zoom 125/150%) không có lỗi console/asset mới. |

## C. Áp dev

Snapshot DB, filestore, config private và source dirty kèm checksum. Clone chạy bằng restore exact. Trước khi áp phải có test clone xanh và hash source tested bằng source áp. Chỉ dừng đúng process Odoo dev. Upgrade `tp_kd_workspace`. Rowset hash của bảng nghiệp vụ trước/sau phải bằng nhau. Khởi động lại dev, chạy probe trình duyệt trên 18069. Rollback bằng `scripts/kd_ui002.py rollback`, khôi phục source module từ snapshot rồi upgrade; không restore DB.

## Evidence

Chạy ngày 06/11/2026 (CHG-20261106-020). Evidence nằm trong `.local/kd-ui002/` (không đưa vào Git). Không in credential.

### A. Backend

| Mục | Kết quả |
| --- | --- |
| R1–R12 | `tp_kd_workspace` **33/33** trên clone. Log `odoo-tests/20261106T133126592713Z.log`. `test_whitelist_scope_and_create_permissions` kiểm thêm `project_actions` lọc theo quyền và method gọi được trên `project.project`. |
| R13 | `tp_contract` **73/73** trên clone. Log `odoo-tests/20261106T133044551080Z.log`. Menu lá giữ XMLID/action; 5 nhóm cha mới trong `views/workspace.xml`. |
| Lint | `ruff` đạt cho `models/dashboard.py`. |

Lần gọi `kd_ui002.py test --tags /tp_contract` (log `20261106T133023469105Z`) báo `no_tests` vì script chỉ `-u tp_kd_workspace`. Đây không phải lỗi test; đã chạy lại đúng module như trên.

### Đối chiếu biểu đồ với danh sách nguồn (B8)

Với mỗi đoạn biểu đồ và mỗi KPI, script gọi `action_kd_open` đúng như khi bấm, rồi `search_count` domain trả về bằng chính user đó. Có 4 vai trò: reviewer, editor, planner, metadata. File: `shots/clone-after/chart-vs-source.json` và `shots/dev-verify/chart-vs-source.json`.

| Vai trò | G01 | G02 | G03 | G05 | KPI | G04 (văn bản) |
| --- | --- | --- | --- | --- | --- | --- |
| reviewer | 21/21 | 16/16 | 4/4 | 3/3 | 3/3 | 12 kỳ |
| editor | 21/21 | 16/16 | 4/4 | 3/3 | 3/3 | 12 kỳ |
| planner | 21/21 | 25/25 | không đọc được CRM: khối hiện "chưa có quyền" | 3/3 | 3/3 | 14 kế hoạch bị loại vì không có quyền tiền; không trả giá trị |
| metadata | 21/21 | 16/16 | 4/4 | 3/3 | 3/3 | 14 kế hoạch bị loại vì không có quyền tiền; không trả giá trị |

Tổng **193/193** phép so số khớp, trên cả clone và dev 18069.

G04 không phải số đếm, nên được ghi dạng văn bản: mục tiêu/nguồn/nhãn trạng thái của 12 kỳ. Hầu hết là "Chưa có dữ liệu nguồn" hoặc "Chưa đủ căn cứ so sánh", đúng như dataset. Phép tính G04 được test ở R5/R6.

Ví dụ reviewer, G01 Giao khoán: Nháp 5, Đang rà soát 9, Trả lại 4. Danh sách mở ra có đúng 5, 9, 4 dòng.

KPI "Chờ tôi rà soát" = 68 = tổng tab "Việc của tôi".

### B. Trình duyệt

| Môi trường | Kết quả | Ảnh |
| --- | --- | --- |
| Clone 18289 | **231/231** kiểm, 0 lỗi console/page. Log `ui-after-all.log`, `shots/clone-after/result.json`. | `shots/clone-after/` |
| Dev 18069 | **230/230**, 0 lỗi. Bỏ B6 có chủ đích: không gõ vào form nghiệp vụ trên dev. B11 chỉ mở form rồi Hủy. Log `ui-dev-verify.log`. | `shots/dev-verify/` |

| ID | Evidence |
| --- | --- |
| B1 | Sidebar trên Tổng quan/list/form. Rời app thì không còn `o_tp_kd_shell`. Section menu navbar bị ẩn trong KH-KD. |
| B2 | Nhóm đổi `aria-expanded` bằng chuột và Enter. Submenu đóng có `visibility:hidden`. Ảnh: `sidebar-submenu-toggled.png`. |
| B3 | Lá active sau click, deep link `action_allocations` và breadcrumb back. |
| B4 | "nghiem thu" ra "Hồ sơ nghiệm thu"; Escape xóa ô tìm. Ảnh: `sidebar-search.png`. |
| B5 | Rail giữ sau reload; Gọn và Giảm chuyển động gắn class; Khôi phục mặc định xóa. Ảnh: `sidebar-collapsed.png`, `prefs-open.png`. |
| B6 | Clone: form mới có tên, bấm lá "Tổng quan", Odoo giữ form và báo "Missing required fields". Không tạo record, đã Hủy. Ảnh: `dirty-form-leave.png`. |
| B7 | 390/360: drawer nhận focus, Escape đóng, focus về nút "Menu KH-KD". Không tràn ngang. Ảnh: `drawer-390.png`, `drawer-360.png`. |
| B8 | Bảng đối chiếu ở trên. G01 segment mở list đúng số dòng. Ảnh: `drill-g01-list.png`. |
| B9 | Đổi filter/refresh có request id; lỗi giữ số cũ (code review). |
| B10 | Sort đổi `aria-sort`; menu "Thao tác" mở action dòng. Ảnh: `project-row-actions.png`. |
| B11 | Editor: "Tạo hồ sơ ▾" liệt kê 9 loại được phép; chọn Giao khoán khi đang lọc dự án thì form mới có dự án điền sẵn. Ảnh: `create-menu-editor.png`, `create-form-editor.png`. Reviewer không có nút. |
| B12 | 1440/1024/768/390/360 và zoom 125/150%: không tràn ngang trang, 0 lỗi console. Ảnh: `overview-*.png`. |

Ảnh trước–sau:

- `shots/clone-before/`: overview 1440/1024/390, list/form giao khoán, menu mobile 390.
- `shots/clone-after/` và `shots/dev-verify/`: cùng màn hình, cộng sidebar mở/thu gọn/submenu/tìm, prefs, drawer, drilldown, form từ Việc của tôi, các vai trò.

### C. Áp dev

- Backup snapshot `snapshot-20261106T091107Z`: DB dump, filestore, config private, source, **112/112 checksum khớp** khi kiểm ngay trước khi áp.
- Drift dev từ snapshot đến trước khi áp: chỉ `bus_bus`, `ir_attachment`, `mail_presence`, `res_device_log`.
- Hash source main bằng hash source clone đã test.
- `apply` chỉ dừng PID Odoo dev trong `.local/odoo.pid`, đã đối chiếu là process cha của listener 18069. PostgreSQL không bị dừng.
- `-u tp_kd_workspace`: returncode 0, không có dòng ERROR/CRITICAL. Log `dev-apply-20261106T131322Z.log`.
- Rowset 31 bảng nghiệp vụ trước/sau **giống hệt**: `changed_tables = {}` (`dev-apply-result.json`). Ví dụ: `res_users` 20, `project_task` 163, `tp_kd_grant` 320, `tp_allocation` 18, `tp_production` 25, `tp_payment_request` 21.
- Drift sau áp và sau browser verify: chỉ metadata module (`ir_ui_menu` +5 nhóm, `ir_model_data` +5, view/action/ACL được ghi lại khi upgrade, `ir_cron_trigger` +1) và bảng phiên/log. Không có bảng nghiệp vụ.
- Dev chạy lại, HTTP 200 trên `/web/login`.
- Rollback: `scripts/kd_ui002.py rollback` khôi phục source module từ `maintained-source.zip` rồi upgrade, không restore DB.

Đây là technical acceptance. Business acceptance, audit KD-NATIVE-001, Q2, G7 và pilot vẫn mở.
