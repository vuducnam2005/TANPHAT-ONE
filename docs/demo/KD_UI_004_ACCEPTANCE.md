# KD-UI-004 — Acceptance Tổng quan KH-KD

Ngày 07/11/2026. Thiết kế: [KD_UI_004_OVERVIEW_DESIGN.md](../ui/KD_UI_004_OVERVIEW_DESIGN.md). Kế hoạch: [KD_UI_004_OVERVIEW_REDESIGN_PLAN.md](../ui/KD_UI_004_OVERVIEW_REDESIGN_PLAN.md). Change ID CHG-20261107-003.

Đây là technical acceptance của giao diện. Không thay business acceptance, audit độc lập hay pilot. Cột "Bằng chứng" điền ở lô D; số liệu là của clone (dữ liệu = snapshot dev 07/11/2026), log/ảnh nằm trong `.local/kd-ui004/` (ảnh clone `shots/clone-after/`, dev `shots/dev-verify/`, số `overview-evidence.json`), không vào Git.

Môi trường: clone owned `tp_tanphat_kdui004_20261107` cổng 18489, source cô lập `.local/kd-ui004/source`; dev 18069 chỉ smoke đọc sau khi áp.

## A. Số liệu và đối chiếu nguồn

| ID | Tiêu chí | Cách kiểm | Bằng chứng |
| --- | --- | --- | --- |
| A1 | Tâm vòng khuyên = `g01.totals.total` = Σ `g01.rows[].total` | browser: đọc DOM so payload RPC cùng actor | Clone, 4 actor (editor/reviewer/metadata/planner): tâm 121 = `totals.total` = Σ 7 dòng (18+25+17+21+18+13+9). `overview-evidence.json` → `recon`. |
| A2 | Mỗi state: chú giải = `g01.totals[state]` = Σ đoạn D02 cùng state | browser | Nháp 29 / Đang rà soát 64 / Trả lại 28 = chú giải = Σ đoạn cùng state trên 7 thanh, cả 4 actor. |
| A3 | Mỗi đoạn D02 = `search_count` domain của `action_kd_open('g01', source, state)` cùng actor | browser + RPC | 21 cặp (7 nguồn × 3 state) DOM = `search_count` domain `action_kd_open('g01')` cùng actor (vd. Sản lượng rà soát 13 = 13), cả 4 actor (`recon.*.drill`). |
| A4 | % chú giải = count/tổng (1 số thập phân), không ép tổng 100 | browser | 24,0% / 52,9% / 23,1% (vi-VN, 1 chữ số); tổng 100,0% không ép. |
| A5 | Tổng 0 → empty state; không quyền → thông báo không quyền (khác rỗng); một phần không quyền → ghi chú | Odoo test + browser lọc dự án không có hồ sơ | Odoo `test_whitelist_scope_and_create_permissions`; browser lọc ngày 2099-01-01 → tâm 0 + câu rỗng (`after-empty-filter-1440.png`); payload giả rỗng/không quyền/một phần không quyền (`after-mock-empty|noaccess|partial-1440.png`). |
| A6 | Ba state rời nhau; mỗi (model,id) đếm 1 lần (`_read_group` theo state) | Odoo test hiện có `test_g01_*` | Odoo `test_g01_states_kpis_and_my_work_match_sources` (đếm `_read_group` theo state). |
| A7 | 4 KPI = `kpis.review/returned/overdue/due`; nhãn "Đến hạn trong 3 ngày" khớp `due_window` [hôm nay, hôm nay+3] | Odoo test + browser tooltip | reviewer 68/0/0/0, editor 0/29/39/41, planner 0/0/17/16; `due_window` 07/11–10/11/2026 hiện trong ô; Odoo `test_due_tab_is_overdue_plus_due_of_current_owner`. |
| A8 | Dải quy mô = `kpis.projects/contracts/revisions`; tooltip nêu đúng ngày/người phụ trách áp dụng | browser | reviewer Dự án 8 / Hợp đồng 11 / Phiên bản 11, planner 14/14/15 = `kpis.*`; tooltip nêu đúng quy tắc ngày/người phụ trách; lọc ngày giữ nguyên Dự án/Hợp đồng, lọc người phụ trách giữ nguyên Dự án/Phiên bản. |
| A9 | Công việc: 3 nhóm = `g02.totals`; top N "Đang xem X/Y"; ghi chú việc chưa có hạn = `g02.no_deadline` | browser | reviewer Hoàn thành 0 / quá hạn 17 / đang mở 85 = `g02.totals` (planner 4/23/103); "Đang xem 8/8"; ghi chú việc chưa có hạn = `no_deadline` 2; drill KD26-ANP quá hạn 3 = 3, đang mở 17 = 17. |
| A10 | Cơ hội: bid 3 state + direct riêng = `g03`; tổng = `g03.total`; nhãn "Đã khai báo nộp — chưa xác minh" | browser | Đấu thầu 3/2/5 + Chỉ định 4, tổng 14 = `g03`; planner không quyền CRM → `available=false`, không hiện số; nhãn "Đã khai báo nộp — chưa xác minh". |
| A11 | Kế hoạch: chưa xác nhận/chưa có mục tiêu/chưa đủ căn cứ không hiện 0; mỗi dòng ghi tiền tệ + căn cứ thuế; không cộng kỳ/tiền | Odoo test + browser | reviewer/editor 12 dòng (14 trong phạm vi, giới hạn helper — G-3); mỗi dòng có tiền tệ + căn cứ; KD26-KH-10 17% (500.000.000 ₫ / 85.000.000 ₫), dòng khác "Chưa so sánh", chưa xác nhận không hiện 0, không cộng kỳ/tiền; metadata/planner không quyền tiền → 14 loại trừ, không dòng tiền. Odoo `test_g04_period_kind_unconfirmed_zero_and_money_scope`; `after-plan-1440.png`. |
| A12 | Chứng chỉ: 3 nhóm = `buckets`; mốc ngày = `bounds`; drilldown khớp | Odoo test + browser | Hết hạn 3 / 30 ngày 4 / sau 30 ngày 6 = `buckets`, nhãn theo `bounds`; drill từng nhóm = `search_count`. Odoo `test_g05_credential_date_boundaries`; `after-cred-1440.png`. |

## B. Tương tác và drilldown

| ID | Tiêu chí | Bằng chứng |
| --- | --- | --- |
| B1 | Hover/focus lát hoặc chú giải làm nổi D02, **không** phát sinh RPC | Hover từng state: D02 nổi đúng state, 0 request `call_kw` (đếm qua route) — `after-hover-1440.png`. |
| B2 | Chọn lát giữ mẫu số, mở panel nguồn; nút nguồn mở đúng model + state + bộ lọc; không mở tổng vào một model | Bấm lát/chú giải (0 RPC khi chọn): tâm giữ 121, "Đang chọn: Đang rà soát 64 · 52,9% trên 121 hồ sơ", 7 nút 9/13/9/11/10/7/5 = các dòng có state đó; nút mở list đúng model + state (`after-select-1440.png`, `after-select-390.png`). |
| B3 | Esc/"Bỏ chọn" xóa chọn; bàn phím Tab/Enter dùng được chú giải và panel | Tab tới chú giải + Enter chọn; Esc và "Bỏ chọn" xóa chọn; tab chi tiết End/Home chuyển và focus tab. |
| B4 | Đoạn D02 = 0 không có nút; đoạn > 0 mở đúng list, sidebar tô đúng mục, Back về Tổng quan | 4 actor: đoạn 0 và chú giải 0 không có nút; đoạn > 0 mở list, breadcrumb về Tổng quan. |
| B5 | Công việc/cơ hội/chứng chỉ/kế hoạch mở đúng nhóm | Công việc theo dự án/nhóm, Đấu thầu/Chỉ định, nhóm chứng chỉ, tên + thanh nguồn kế hoạch mở đúng list/form, pager = số. |
| B6 | Bảng điều hành: sort, chọn cột, pager, menu Thao tác, mở dự án giữ KD-UI-003 | Pager bảng dự án "… / Y" = `get_kd_project_rows.total`; sort, chọn cột, menu Thao tác qua hồi quy KD-UI-003 (E2). |
| B7 | Việc của tôi: KPI bấm chuyển tab và cuộn tới; pager; mở hồ sơ | Bấm KPI Bị trả lại → tab Bị trả lại `aria-selected`, khung Việc của tôi cuộn vào màn hình. |
| B8 | Bảng nguồn mở khi cần, số khớp | Bảng nguồn đóng sẵn; mở ra từng ô (tất cả/rà soát/trả lại/quá hạn/đến hạn) = `get_kd_source_table`. |

## C. Nhất quán dữ liệu

| ID | Tiêu chí | Bằng chứng |
| --- | --- | --- |
| C1 | Đổi bộ lọc nhanh (response cũ trễ hơn) → màn hình theo bộ lọc mới nhất | Route giả trễ response lọc cũ → màn hình theo lọc mới nhất, không bị đè. |
| C2 | Partial (trang bảng/tab) trong lúc tải chính không làm kẹt loading | Sort bảng dự án đang chạy khi bắt đầu làm mới toàn bộ: `aria-busy` 0, không kẹt loading, sort giữ "descending". |
| C3 | Lỗi mạng khi làm mới → giữ dữ liệu, nhãn "chưa làm mới được" và thời điểm cũ | Chặn mạng khi Làm mới → giữ số, "Dữ liệu lúc … — chưa làm mới được", giờ cũ (`after-stale-1440.png`); console chỉ 1 dòng `net::ERR_FAILED` do test chặn. |
| C4 | Lỗi quyền/phiên → xóa dữ liệu đang hiện, chỉ còn thông báo | Response AccessError/401 → xóa số, bảng, tab; chỉ còn "Không hiển thị số liệu" (`after-denied-1440.png`). |

## D. Motion và giao diện

| ID | Tiêu chí | Bằng chứng |
| --- | --- | --- |
| D1 | Vòng khuyên vẽ một lần ≈700ms; thanh grow < 800ms; không replay khi sort/chọn cột/hover | Một `tp-kd-ov-sweep` 700ms; `tp-kd-ov-grow` 480ms trễ 0–280ms (40ms/thanh), tổng < 800ms; fade 180ms, tab 200ms; transition khác ≤ 250ms; `is-intro` gỡ; sort/hover/chọn không phát lại. |
| D2 | Reduced (OS hoặc tùy chọn): không animation intro/grow/shimmer | Tùy chọn "Giảm chuyển động" và OS `prefers-reduced-motion`: 0 animation intro/grow/shimmer. |
| D3 | Vào-ra Tổng quan nhiều lần: không lỗi console, không tích lũy | Vào–ra Tổng quan 5 lần: luôn 1 root `.o_tp_kd_ov`, 0 lỗi console. |
| D4 | 1440×900 màn đầu thấy header, bộ lọc, KPI và phần chính cặp biểu đồ | 1440×900: đầu trang 129px, lọc 225px, KPI 371px, cặp vòng + thanh kết thúc 787px < 900 (`after-overview-1440x900.png`). |
| D5 | 360/390/768/1280/1440/1600/1920px không cuộn ngang trang; zoom 125%/150%; sidebar mở/thu | 1440/1440 thu sidebar/1920/1600/1280/768/390/360 + zoom 125/150%: cuộn ngang trang 0, tràn Tổng quan 0 (`after-overview-*.png`, `after-filters-390.png`). |
| D6 | Lăn chuột/touchpad cuộn Tổng quan (fix CHG-20261107-001) mọi viewport ≥992px và mobile; không 2 thanh cuộn dọc | Mọi viewport: lăn chuột cuộn được Tổng quan, đúng 1 thanh cuộn dọc (`overflow-y: auto`). |
| D7 | App khác (CRM/Project) không nhận style Tổng quan | Discuss, CRM: không có `.o_tp_kd_ov`, token `--kd-bg` rỗng. |
| D8 | Không hiển thị mã G01/D01 trên màn hình | 4 actor: text màn hình không có mã G0x/D0x. |

## E. Hồi quy và vận hành

| ID | Tiêu chí | Bằng chứng |
| --- | --- | --- |
| E1 | Odoo tests `/tp_kd_workspace` xanh trên clone | Clone 114/114 (`tp_kd_workspace` 41 + `tp_contract` 73), log `odoo-tests/20261107T042619942834Z.log`. Lần đầu 11 lỗi `tearDownClass` (GC filestore không xóa được 2 tệp tạm ReadOnly do Odoo ghi asset đồng thời trên Windows); xóa 2 tệp tạm trên clone, chạy lại xanh. |
| E2 | Hồi quy browser KD-UI-003 (bảng, form, sidebar, quyền, responsive, chống lộ, Tổng quan) xanh | Clone 334 mục hồi quy KD-UI-003 trong 823/823; dev chỉ đọc 326 mục trong 806/806; 0 lỗi console. |
| E3 | Ruff cho Python đổi; XML/JS/SCSS assets biên dịch không lỗi | Ruff 0.16.1 `check` sạch (dashboard.py, test_dashboard.py, manifest, kd_ui004.py); upgrade clone/dev 0 ERROR; bundle tải không lỗi trên 7 viewport. |
| E4 | Backup dev đã verify trước áp; sau áp 30 bảng nghiệp vụ không đổi; dev 18069 chạy | Backup `backup-pre-apply-20261107T042737Z` verify (112 tệp, 576 bảng, 269 attachment); apply `dev-apply-20261107T042759Z.log` rc 0, 0 lỗi, `changed_tables {}` 30 bảng/1118 dòng; dev PID 2680 HTTP 200; 18169/18269/55432 không đổi PID. |
| E5 | Dev verify chỉ đọc: số liệu khớp nguồn, không lỗi console | Dev verify 806/806 chỉ đọc: số = clone, 23 cặp drilldown khớp cho reviewer, 4 actor cùng tâm 121; rowset sau verify = sau áp, `write_date` nghiệp vụ mới nhất 06/11 08:10 UTC (`shots/dev-verify/`). |
