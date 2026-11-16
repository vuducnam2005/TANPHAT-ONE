# EQUIP-001 — Trạng thái chức năng và bằng chứng

Cập nhật 16/11/2026 (`CHG-20261116-003`, `tp_equipment` **20.0.1.5.0**, EQUIP-SIMPLE-003 / DEC-047): **IMPLEMENTED_RUNTIME_OBSERVED_MAIN_PENDING_ADMIN_FLOW_CHECK**. Kho gọn còn **Thiết bị** + **Yêu cầu đề xuất**, Gán / Đổi máy / Trả về kho chỉ với máy trong kho chưa có người giữ. Mức bằng chứng từng mục ở bảng **EQUIP-SIMPLE-003** bên dưới; **không** đánh PASS toàn bộ: chưa thực hiện gán/đổi/trả/gửi đề xuất thật, chưa chạy test suite, transaction hay race.

Cập nhật 15/11/2026 (`CHG-20261115-003`, `tp_equipment` **20.0.1.4.1**): tìm nhanh trên bảng người sử dụng không phân biệt dấu/vị trí dấu thanh, màn rỗng mở từ dashboard hiển thị chữ (không thẻ HTML) và không có nút Mới. Thiết bị chưa thấy trong bảng là dòng nguồn #63 đang chờ xác minh người sử dụng (tên nguồn khác HR ở dấu thanh; gợi ý HR #57, không tự gán).

Cập nhật 15/11/2026: **EQUIP-UI-002 / UI-BACK-001 đã áp main 18069** (`CHG-20261115-002`, `tp_equipment` **20.0.1.4.0**, `tp_web_home` **20.0.1.8.0**, `tp_hr_workspace` **20.0.1.11.5**) — bảng người sử dụng chỉ thiết bị có nhân viên HR (26, 0 stock), menu dùng chung/chưa rõ người (20) và tất cả hồ sơ (54), dashboard nâng cấp, nút Quay lại thống nhất theo [chuẩn UI-BACK-001](../ui/UI_BACK_001_STANDARD.md). Chờ người dùng xem trực quan; giới hạn kỹ thuật/nghiệp vụ bên dưới vẫn giữ.

Ngày 14/11/2026. Trạng thái: **RUNTIME_UI_REDESIGNED_OBSERVED_WITH_REAL_DATA** (`CHG-20261114-014`, `tp_equipment` **20.0.1.3.0** trên main **18069**; dữ liệu thật nhập từ `CHG-20261114-012`: 54 hồ sơ thiết bị, 54 phiếu ghi nhận ban đầu, 1 đề xuất nháp `DX-00001`, 2 đợt nhập). Đã quan sát đầy đủ UI mới (`EQUIP-UI-001`) trên `18069` qua Playwright ở desktop (`1440×900`, `1366×768`), tablet (`1024×768`, `768×1024`) và mobile (`390×844`) với `consoleErrors: 0, pageErrors: 0, serverErrors: 0`, xuất Excel HTTP 200 và bảo toàn DB chỉ khác version module. Vẫn giữ tách biệt **Chưa chạy bộ test Odoo/HOOT/18079 hoặc các flow bàn giao/sửa/kiểm kê có dữ liệu**, chưa xác nhận business acceptance hay pilot authorization.

## Các mốc được ghi riêng

| Mốc | Trạng thái |
| --- | --- |
| Source implementation / tự review (`20.0.1.3.0`) | Đã cài/nâng cấp thành công qua `-u tp_equipment`; Ruff, compileall, XML parse và `node --check` đạt |
| Runtime upgrade main `18069` | `tp_equipment` **20.0.1.3.0** chạy trên `tp_tanphat_dev`; giữ nguyên 39 nhân viên HR, 28 user, 99 group rel, 54 thiết bị, 54 phiếu, 1 đề xuất (`PRESERVATION_DIFFS: ['modules']`) |
| Quan sát UI mới (`EQUIP-UI-001`) trước–sau | Đã chụp và kiểm tra ảnh trước–sau trên `18069` (`.local/equip-ui001/screens/{before,after}/`): 2 biểu đồ nằm gọn màn đầu (`bottom: 641` ở cả `1440×900` và `1366×768`), sidebar 4 mục + accordion `Quản trị dữ liệu`, không còn chip mặc định (`searchChips: []`), `overflowBadges: 0`, tablet/mobile không tràn ngang, lọc tương tác + chi tiết `TB-00022` & `DX-00001` đạt |
| Runtime main `18069` — `EQUIP-UI-002` / `UI-BACK-001` (`20.0.1.4.0`, CHG-20261115-002) | Backup `.local/equip-ui002/backup-pre-ui002/`; `-u` exit 0; `preservation-final.json` so baseline chỉ khác `modules` (18 bảng HR/user/quyền/thiết bị/phiếu/đề xuất/nhập/nguồn giữ hash) |
| Quan sát UI-002 | Playwright `verify_ui002.mjs` 42 PASS/0 FAIL/0 console error ở 1440×900, 1366×768, 768×1024, 390×844, 375×812: list người sử dụng 26 (0 stock), lọc phòng/loại khớp DB, trang 2 + 10 dòng/trang giữ khi quay lại, drill-down KPI/thanh loại đúng tập, 3 deep link về đúng list, dirty/lỗi lưu ở lại, popup không nút; `check_export.mjs` xuất 26/7/20 dòng khớp list. HOOT `tp_web_home` 44/44, `tp_hr_workspace` 40/40 |
| Gán dòng nguồn #63 → HR #57 (dữ liệu, CHG-20261115-005) | Admin xác nhận trong chat; backup `.local/equip-ui002/backup-pre-link63/`; chạy thử rollback rồi chạy thật; TB-00055 đang quản lý nơi giữ HR #57, 1 phiếu Ghi nhận ban đầu; bảng người sử dụng 27, dòng chờ 9; `preservation-after-link63.json` chỉ khác thiết bị/phiếu/dòng nhập; `verify_link63.mjs` 9 PASS/0 FAIL/0 console error |
| Hiển thị hết bảng người sử dụng (`20.0.1.4.2`, CHG-20261115-004) | Backup `.local/equip-ui002/backup-pre-fix004/`; `-u` exit 0; `verify_fix004.mjs` 11 PASS/0 FAIL/0 console error (26/26 một trang, pager 1-26 / 26, quay lại từ form, tìm/xóa tìm, drill-down; bảng khác vẫn 20/trang); `preservation-after-fix004.json` chỉ khác version module |
| Fix tìm kiếm/màn rỗng (`20.0.1.4.1`, CHG-20261115-003) | Backup `.local/equip-ui002/backup-pre-fix003/`; `-u` exit 0; shell rollback 4 cách gõ (có/không dấu, khác vị trí dấu thanh, chữ hoa) khớp HR #57; `verify_fix003.mjs` 11 PASS/0 FAIL/0 console error; `preservation-after-fix003.json` chỉ khác version module |
| Kho gọn EQUIP-SIMPLE-003 (`20.0.1.5.0`, CHG-20261116-003) | Backup `.local/equip-simple003/backup-pre-simple003/`; `-u` exit 0; `baseline-after.json` so `baseline-before.json` chỉ khác version module và 2 cột NULL mới của phiếu; `verify_simple003.mjs` quan sát UI + probe từ chối (chi tiết bảng EQUIP-SIMPLE-003); chưa giao dịch thật/test suite/race |
| Technical acceptance | Chưa kết luận đủ chức năng khi bộ test giao dịch / race / role / relation nhiều trang chưa chạy |
| Business acceptance | Chưa được người dùng nghiệm thu |
| Pilot authorization | Chưa ghi nhận; quyền áp main trực tiếp không đồng nghĩa nghiệm thu/pilot |

> Lưu ý lịch sử bên dưới (CHG-010) mô tả snapshot rỗng ban đầu trước CHG-012 (`EQUIP-DATA-001`) và CHG-014 (`EQUIP-UI-001`). Với CHG-014, backup tiền UI lưu tại `.local/equip-ui001/backup-pre-ui/` và bằng chứng ảnh/metrics lưu tại `.local/equip-ui001/`.

Người dùng đã cho phép triển khai trực tiếp `tp_tanphat_dev`/18069 sau backup, bỏ 18079 và bộ test riêng. Không bulk nhập thật, seed hoặc tạo giao dịch kiểm thử. Snapshot runtime đọc trực tiếp do phiên chính ghi nhận: **39 nhân viên, 28 users** và **0 thiết bị, 0 phiếu bàn giao, 0 phiếu tiếp nhận, 0 yêu cầu sửa chữa**. Vì vậy ảnh dashboard/list trống là bằng chứng trung thực, không dùng dữ liệu giả để tạo biểu đồ. Những số này là snapshot, không khẳng định dữ liệu luôn trống về sau.

## EQUIP-SIMPLE-003 — mức bằng chứng từng mục (CHG-20261116-003)

Mức: **UI** = quan sát Playwright trên main 18069 bằng tài khoản admin, chỉ mở/đóng, không xác nhận/lưu; **RPC đọc** = gọi đọc qua session admin; **Probe từ chối** = gọi `tp_quick_action`/`write` với dữ liệu sai, backend từ chối nên không ghi; **Source** = chỉ có trong mã, chưa chạy; **Chưa kiểm** = không thực hiện trong lượt này.

| Mục | Mức bằng chứng | Kết quả / giới hạn |
| --- | --- | --- |
| Hai menu Thiết bị / Yêu cầu đề xuất; 22 menu cũ ẩn | UI + đọc DB | Sidebar và menu gốc chỉ có 2 mục; menu cũ `active=False`, XML ID/action/path giữ nguyên |
| Danh sách một bảng, 3 segment và số đếm | UI + RPC đọc | Tất cả 54 / Đang sử dụng 27 / Trong kho 7; pager khớp số đếm từng segment; `cleanup` = 0 nên không có cảnh báo làm sạch |
| Cột, badge, nút theo trạng thái, menu ⋮ | UI | 6 cột + Thao tác (1440, có sidebar); nút Đổi máy / Trả kho trên dòng máy Đang sử dụng (popup mở từ nút dòng), dòng máy Đặt tại vị trí chỉ Xem + Trả kho; Gán mở từ nút đầu trang và có trên chi tiết máy Trong kho (nút Gán trên dòng máy Trong kho chỉ có trong source/arch, lượt cuối không bấm); ⋮ có 4 mục |
| Tìm kiếm không dấu | UI + RPC đọc | `máy` và `may` cùng 15 dòng |
| Popup Gán chỉ máy trong kho, chưa có người giữ | UI | Picker 7/7 dòng đều stock + không người giữ; chọn người không có nút tạo mới; mở rồi Hủy, **không xác nhận** |
| Popup Đổi máy | UI | Người sử dụng chỉ đọc; danh sách máy mới 7/7 stock + không người giữ; mở rồi Hủy |
| Popup Trả về kho | UI | 3 lý do Đổi máy / Nghỉ việc / Thu hồi khác; mở rồi Hủy |
| Backend từ chối máy có người giữ (gán, đổi sang B có chủ) | Probe từ chối | "Thiết bị đã có người sử dụng hoặc không còn trong kho, vui lòng chọn thiết bị khác" |
| Backend từ chối A = B, mã yêu cầu sai, ghi custody trực tiếp | Probe từ chối | "Máy mới phải khác máy đang dùng." · "Thiếu mã yêu cầu; mở lại cửa sổ thao tác." · guard phiếu bàn giao |
| Từ chối B ghi Trong kho nhưng còn người giữ | Source | Probe **bỏ qua**: dữ liệu không có máy như vậy (`cleanup` = 0); không tạo dữ liệu để thử |
| Idempotency (gửi lại cùng mã; cùng mã khác nội dung) | Source | Probe **bỏ qua**: chưa có thao tác nhanh nào được chạy thật trên main |
| Đổi máy nguyên tử, khóa, race, version thay đổi giữa chừng | Source | Chưa chạy transaction/race; không simulate-rollback trên main theo chỉ đạo |
| Gán / Đổi / Trả thật tạo phiếu và đổi nơi giữ | Chưa kiểm | Không giao dịch trên main; admin cần tự xác nhận trên một máy cụ thể |
| Không còn "Chuyển người dùng"; custody chỉ đọc trên chi tiết | UI | Form máy Đang sử dụng: 0 nút chuyển, 0 ô custody sửa được; nút theo trạng thái |
| Quay lại và link cũ | UI | 1 nút Quay lại, quay về giữ segment; `tong-quan-thiet-bi` → `kho-thiet-bi`; `ton-kho-thiet-bi` vẫn mở; 0 dialog lỗi |
| Thêm thiết bị (form ngắn) | UI | Form 11 trường + Lưu/Hủy; mở rồi Hủy, **chưa lưu** thiết bị nào |
| Yêu cầu đề xuất rút gọn, không tự duyệt/mua/nhập/gán | UI + Source | List 6 cột, form chỉ nút **Gửi**; chưa gửi đề xuất nào; luồng không tự duyệt là source |
| Responsive | UI | Tablet 820 và mobile 390 không tràn trang; 1366/1280 có sidebar thì bảng cuộn ngang trong khung bảng |
| Bảo toàn dữ liệu | Đọc DB trước/sau | 18 bảng HR/user/quyền/company/thiết bị/phiếu/đề xuất/nhập/vị trí/loại giữ count và hash; `tp_equipment_move` chỉ thêm 2 cột NULL (hash bỏ 2 cột này khớp trước) |
| Nâng cấp và kiểm tĩnh | Lệnh thực chạy | `-u tp_equipment` exit 0, 0 ERROR; ruff file đã đổi, compileall, 23 XML, ACL CSV, 13 JS syntax đạt; ruff toàn addon còn 2 lỗi cũ ở `dashboard.py` (không đổi) |
| Test suite Odoo/HOOT/E2E | Chưa kiểm | Không chạy theo chỉ đạo; `tp_equipment` chưa có HOOT riêng |

Ảnh trước khi sửa code không được chụp; bằng chứng "trước" là `baseline-before.json` phía DB và backup. Admin nên xem UI rồi tự xác nhận luồng nghiệp vụ: Gán một máy trong kho cho một nhân viên, Đổi máy, Trả về kho, rồi kiểm phiếu trong **Phạm vi nâng cao → Lịch sử bàn giao**.

## AT-E01 đến AT-E18

Source các mục đã có; bằng chứng runtime chỉ giới hạn quan sát dưới đây. **Không đánh AT PASS**: cột cuối giữ rõ flow chưa thực hiện, không gộp source review với test hoặc nghiệm thu.

| ID | Phạm vi | Triển khai trong source | Bằng chứng / flow chưa kiểm chứng |
| --- | --- | --- | --- |
| AT-E01 | Module riêng, HR chung, admin-only | Addon/menu/thẻ/dashboard/sidebar riêng; một `maintenance.equipment`, HR liên kết cùng ID | Menu/dashboard main đã mở; ảnh desktop/mobile. HR bridge và non-admin entrypoint chưa chạy |
| AT-E02 | CRUD/duplicate/archive/delete | Mã/serial và lifecycle guard; duplicate reset metadata định danh/custody; hồ sơ đã dùng không xóa vật lý | Không tạo/nhân bản/xóa thiết bị thật để thử; chưa kiểm flow archive và FK runtime |
| AT-E03 | Import source phức tạp | XLSX preview provenance đã làm sạch; mapping cột, disposition từng dòng, ID/alias xác nhận | Không upload/apply workbook thật; header/merge/N/a/formula/cached trên nguồn chưa chạy |
| AT-E04 | Replay và phiên bản nguồn | Hash/company/kind chống batch trùng; apply replay; nguồn sau đối chiếu ID existing giữ nguyên hoặc dòng new xác nhận | Chưa apply/retry/đổi thứ tự nguồn; không tuyên bố đồng bộ ghi đè dữ liệu existing |
| AT-E05 | Custody, pending, reservation | Move draft/pending/done/cancel, preview trước/sau, target custody và hủy giải phóng | Cấp/thu hồi/điều chuyển/mượn/trả chưa thực hiện trên main |
| AT-E06 | Race/retry/stale | Lock, version, idempotency và guard cập nhật đồng thời trong source | Không chạy race suite; chưa tạo double-submit hoặc stale transaction thật |
| AT-E07 | Repair/upgrade | Maintenance request mở rộng, kỹ thuật trước/sau, kết quả, chi phí, gửi/nhận sửa liên kết move | Chưa thực hiện báo hỏng/gửi NCC/nhận sửa/nâng cấp; không kết luận máy Tốt tự động |
| AT-E08 | Rà soát và duyệt ngoài | Review tách approval evidence; return/resubmit; execution theo dòng đủ điều kiện | Chưa chạy review/return/evidence wizard; không coi footer Excel hoặc reviewed là duyệt chi |
| AT-E09 | Tiếp nhận từng phần | Receipt/line liên kết proposal, guard số lượng/lặp và thiết bị thực nhận | Chưa nhận từng phần/vượt/retry; chưa tạo tồn thật |
| AT-E10 | Kiểm kê/chênh lệch | Snapshot/count/close tách custody; adjust preview/lý do/version, move riêng | Chưa bắt đầu kỳ/chốt/điều chỉnh; chưa chứng minh giao dịch sau snapshot trong runtime |
| AT-E11 | Nghỉ/mất/trả thuê/thanh lý | Ownership/lifecycle guard và move có lý do; không tự ghi giảm kế toán | Chưa thực hiện flow kết thúc; không tạo PO/bill/posting/chữ ký |
| AT-E12 | HR đổi phòng/offboard | Phòng hiện tại từ HR, employee archived warning, không auto transfer | Chưa đổi HR thật; chưa kiểm khóa tài khoản và cảnh báo bằng giao dịch |
| AT-E13 | Quyền admin/company/file/native | Backend guards/ACL restriction, mail/file/admin-only; `company_scope.py` kiểm quan hệ cùng company, shared target cho phép | Chưa chạy ma trận role/URL/RPC/file/export/union privilege. Không coi ẩn menu là chứng minh bảo mật |
| AT-E14 | Filter/domain/paging | Profiles/table tools và search native; dashboard/detail/export chung domain; filter nội dung | Danh sách chính trống đã mở; chưa đối chiếu nhiều trang/AND-OR/favorites/relation trên dữ liệu |
| AT-E15 | KPI/chart/số liệu thật | KPI định nghĩa rõ; donut loại/kỹ thuật, cột phòng/vị trí; vật lý/service tách; known flags tiền và kỳ theo ngày nguồn | Dashboard trống đã quan sát desktop/mobile, workload repair/proposal có định nghĩa scope riêng. Chưa tie-out dữ liệu độc lập; không bịa xu hướng/tổng tiền khi thiếu nguồn |
| AT-E16 | Excel/PDF/QR | Route admin/company, export domain và text guard; PDF nội bộ; QR token xác thực | Đã tải sổ thiết bị XLSX rỗng 18 cột. Chưa kiểm XLSX/PDF có dữ liệu hoặc quét QR thiết bị thật |
| AT-E17 | Responsive/accessibility | Layout sáng, vùng chạm/focus/keyboard và reduced motion; empty/loading/error | Đã quan sát dashboard desktop 1440×900/mobile 390×844; không có tràn ngang trong màn đã mở. Zoom200/keyboard/chart nonempty/error chưa quan sát đầy đủ |
| AT-E18 | Main chạy và giữ baseline | Dependency/shell chung; backup pre + resume; chỉ update `tp_equipment` | Upgrade 20.0.1.1.0 thành công; snapshot giữ 39 nhân viên/28 users và 0 dòng equipment/request/move/receipt. Chưa kiểm lại mọi login/logout flow; không seed/import/test suite |

## Bằng chứng runtime cuối lượt

**CHG-20261116-003 (EQUIP-SIMPLE-003), ignored `.local/equip-simple003/`:** `backup-pre-simple003/`, `baseline-{before,after}.json`, `upgrade-simple003.log`, `upgrade-simple003-2.log`, `verify_simple003.mjs`, `verify-simple003.json` + `verify-run-4.log` (lượt đầy đủ cuối), `verify-simple003-from-*.json` (lượt chạy tiếp trước đó), ảnh `screens-after/01…20-*.png`. URL: [Thiết bị](http://127.0.0.1:18069/odoo/kho-thiet-bi), [Yêu cầu đề xuất](http://127.0.0.1:18069/odoo/de-xuat-thiet-bi).

**CHG-20261115-005 (gán dòng nguồn #63), ignored `.local/equip-ui002/`:** `backup-pre-link63/`, `verify_link63.mjs`, `verify-link63.json`, `screens/link63-*.png`, `preservation-{pre,after}-link63.json`.

**CHG-20261115-004 (hiển thị hết bảng người sử dụng), ignored `.local/equip-ui002/`:** `verify_fix004.mjs`, `verify-fix004.json`, `screens/fix004-users-all-rows*.png`, `upgrade-fix004-*.log`, `preservation-{pre,after}-fix004.json`.

**CHG-20261115-003 (fix tìm kiếm/màn rỗng), ignored `.local/equip-ui002/`:** `verify_fix003.mjs`, `verify-fix003.json`, `screens/fix003-users-search-*-help.png`, `screens/fix003-users-search-unaccented.png`, `upgrade-fix003-*.log`, `preservation-{pre,after}-fix003.json`.

**CHG-20261115-002 (EQUIP-UI-002 / UI-BACK-001), ignored `.local/equip-ui002/`:**

- URL: [Tổng quan](http://127.0.0.1:18069/odoo/tong-quan-thiet-bi), [Thiết bị & người sử dụng](http://127.0.0.1:18069/odoo/kho-thiet-bi), [Thiết bị tồn kho](http://127.0.0.1:18069/odoo/ton-kho-thiet-bi), [Dùng chung & chưa xác định người](http://127.0.0.1:18069/odoo/thiet-bi-dung-chung), [Tất cả hồ sơ](http://127.0.0.1:18069/odoo/ho-so-thiet-bi), [Đề xuất](http://127.0.0.1:18069/odoo/de-xuat-thiet-bi).
- Ảnh `screens/`: `dashboard-*`, `users-*`, `users-fit-*`, `stock-*`, `shared-*`, `device-form-*` (5 viewport), `users-filter-page2-size10-1440x900.png`, `unsaved-dialog-1440x900.png`, `popup-form-1440x900.png`, `hr-employee-1440x900.png`; `kd-*-empty-list`/`contract-empty-list` ghi nhận KH-KD/hợp đồng chưa có bản ghi.
- Kết quả: `verify-results.json`/`verify-run.log` (42 PASS), `coverage-probe.json`, `hoot-*.txt`, `upgrade-*.log`, `export-*.xlsx`, `baseline-before.json`, `preservation-final.json`.

**Lịch sử CHG-010:**

- Main `tp_tanphat_dev`/18069: `tp_equipment` **20.0.1.1.0** nâng cấp thành công và mở được module.
- URL: [TANPHAT ONE main](http://127.0.0.1:18069/odoo) → **Kho thiết bị văn phòng**.
- Log cuối ở ignored `.local/equip001-main/upgrade-final.log` và `upgrade-final4.log`; ảnh trong `.local/equip001-main/screens/`.
- Dashboard: `tong-quan-thiet-bi-1440.png`, `tong-quan-thiet-bi-390.png`; các danh sách chính và form mới chưa lưu cũng có ảnh trong cùng thư mục. `capture-full.json` giữ lượt quan sát đầy đủ; `capture.json` giữ lượt cuối sau nâng cấp/Việt hóa import và hiển thị tiền chưa biết.
- Quan sát: không có console error, HTTP 500 hoặc tràn ngang trong phạm vi các màn đã mở. Đây là quan sát runtime, không là kết quả suite.
- Đã tải sổ thiết bị XLSX rỗng **18 cột**; chưa kiểm nội dung báo cáo có dữ liệu/PDF/QR.
- Snapshot runtime giữ **39 nhân viên, 28 users**; equipment/request/move/receipt đều **0**, không phát sinh thay đổi dòng nghiệp vụ.
- Không chạy bộ test/18079 theo lệnh người dùng; không seed, nhập thật hoặc tạo giao dịch kiểm thử. Không thực hiện ma trận role/race hoặc nonempty business flows.

## Bảo toàn và giới hạn

Giới hạn CHG-20261115-002: chưa chạy test Python Odoo trên DB thật; `tp_equipment` chưa có bộ HOOT riêng (fallback Kho kiểm bằng trình duyệt); KH-KD/hợp đồng có 0 bản ghi nên chưa quan sát nút Quay lại trên form có dữ liệu; URL chỉ có model/link many2one vẫn mở form `maintenance` gốc (có từ trước); file Excel còn vài tiêu đề tiếng Anh từ field gốc; bảng người sử dụng ở tablet/mobile cuộn ngang trong khung bảng (trang không tràn). 10 dòng nguồn chờ không được xử lý hoặc đoán.

Backup trước Claude: `.local/equip001-main/backup-main-pre/`; backup trước resume: `.local/equip001-main/backup-main-resume/`. Có DB+filestore/source ở các điểm riêng; resume dump **8.894.993 bytes**, filestore **770 tệp**; không coi tồn tại backup là đã chạy restore verification. Credential/workbook/PII/dump/filestore không vào Git.

Các known flags `tp_purchase_value_known`, receipt `purchase_value_known`, proposal `estimate_amount_known` và `amount_total_known` phân biệt chưa biết với số 0 đã xác nhận. Source import sau chỉ liên kết ID existing không ghi đè business data/provenance gốc; dòng thực sự mới cần xác nhận riêng trước tạo nháp. Không có tự đồng bộ/merge overwrite lịch sử.

Xem [schema/quyền](../security/EQUIP_001_SCHEMA_AND_ACCESS.md), [hướng dẫn admin](EQUIP_001_USER_GUIDE.md), [runbook](../../ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md). Chỉ nâng từng trạng thái khi có bằng chứng thực tế tương ứng.
