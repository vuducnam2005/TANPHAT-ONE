# KD-UI-004 — Thiết kế Tổng quan KH-KD (lô A)

Ngày 07/11/2026, Asia/Saigon. Triển khai [kế hoạch KD-UI-004](KD_UI_004_OVERVIEW_REDESIGN_PLAN.md) theo [prompt thực thi](../prompts/CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md). Change ID triển khai: CHG-20261107-003. Tài liệu này viết trước code; mục 11 ghi phần đã điều chỉnh khi triển khai.

Phạm vi chỉ là giao diện native của action Tổng quan (`tp_kd_workspace.action_overview`, js_class `tp_kd_overview`). Menu, action, XML ID, sidebar, bảng/list/form KD-UI-003, quyền, state, transition, công thức và write action giữ nguyên.

## 1. Quyết định kỹ thuật

| Chủ đề | Quyết định | Lý do |
| --- | --- | --- |
| Thư viện vẽ | SVG/HTML/CSS scoped trong OWL template, **không** dùng `web.chartjs_lib`/`chart_hook` | Hook hiện tạo lại chart ở `onPatched` nên mỗi hover/prefs/patch sẽ rebuild/animate lại; canvas cần thêm lớp legend/tóm tắt accessible. SVG cho phép nút thật (focus/keyboard/touch), số cuối hiện ngay, không cần cleanup instance Chart.js, không tải thêm bundle. Không sửa hook core, không CDN. |
| Vẽ vòng khuyên | `<circle pathLength="100">` mỗi lát dùng `stroke-dasharray: p (100-p)` và offset cộng dồn | Không cần lượng giác, hiệu ứng vẽ cung bằng một mask cố định `stroke-dashoffset 100→0`. |
| Animation | CSS keyframes/transition, gắn class một lần; `t-key` theo giá trị cho KPI crossfade; `t-key` theo tab cho fade/slide panel | Không rAF/observer/listener riêng; một timer gỡ class intro được clear ở `onWillUnmount`. |
| Dữ liệu | Tái dùng `get_kd_dashboard`, `get_kd_plan_compare`, `get_kd_credential_expiry`, `get_kd_project_rows`, `get_kd_my_work`, `get_kd_source_table`, `action_kd_open` | Không API mới. Backend chỉ thêm metadata đọc: cửa sổ ngày KPI, mốc ngày chứng chỉ, đơn vị tiền/căn cứ thuế từng dòng kế hoạch (mục 9). |
| Class tương thích | Giữ `.o_tp_kd_ov`, `.o_tp_kd_kpis`, `.o_tp_kd_g01 .o_tp_kd_seg_btn`, `.o_tp_kd_total_btn`, `.o_tp_kd_projects`, `.o_tp_kd_proj_name`, `.o_tp_kd_row_menu`, `.o_tp_kd_table(_wrap)` | Bộ hồi quy KD-UI-003 (B10/B19) tiếp tục chạy không đổi. |

## 2. Nguồn dữ liệu và ngữ nghĩa từng số

Mọi helper chạy bằng quyền người xem (record rule + KD grant), bộ lọc chỉ nhận `project_id`, `owner_id`, `date_from`, `date_to` (whitelist ở `_kd_filter`).

| Phần tử | Helper/khóa | Model | Grain | State/nhóm | Lọc ngày | Lọc người phụ trách | Tiền | Availability | Drilldown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dải quy mô — Dự án | `kpis.projects` | project.project | 1 dự án `tp_managed` | — | **không** | **không** | — | đếm 0 nếu không đọc được | `list/projects` |
| Dải quy mô — Hợp đồng | `kpis.contracts` | tp.contract | 1 hợp đồng | mọi state | **không** | người tạo (`create_uid`) | — | `readable.contracts` | `list/contracts` |
| Dải quy mô — Phiên bản | `kpis.revisions` | tp.contract.revision | 1 phiên bản | mọi review_state | `recorded_at` | **không** | — | `readable.revisions` | `list/revisions` |
| KPI Chờ rà soát | `kpis.review` | 7 typed + revision | 1 hồ sơ mỗi model | `in_review`, reviewer = tôi, có grant review | ngày nguồn | owner nguồn | — | model không đọc được → 0 | tab `review` |
| KPI Bị trả lại | `kpis.returned` | 7 typed + revision | 1 hồ sơ | `returned`, owner/người lập = tôi | ngày nguồn | owner nguồn | — | như trên | tab `returned` |
| KPI Quá hạn | `kpis.overdue` | 6 typed (không gồm kế hoạch định kỳ) + task + lead | 1 hồ sơ | hạn < hôm nay, chưa đóng | ngày nguồn | owner = tôi (bắt buộc) | — | như trên | tab `due` |
| KPI Đến hạn trong 3 ngày | `kpis.due` (+`kpis.due_window`) | như trên | 1 hồ sơ | hôm nay ≤ hạn ≤ hôm nay+3 | ngày nguồn | owner = tôi | — | như trên | tab `due` |
| Vòng khuyên hồ sơ đang xử lý | `g01.totals` | 7 typed: allocation, production, acceptance, payment, plan, credential, obligation | (model,id) đếm 1 lần | draft / in_review / returned (rời nhau) | ngày nguồn | owner_id | — | `g01.rows[].available` | chọn lát → chọn nguồn → `g01` |
| Thanh 7 nhóm | `g01.rows` | như trên | như trên | như trên | như trên | như trên | — | dòng `available=false` ghi "không có quyền xem" | đoạn → `g01` source+state; nhãn → `list/<source>` |
| Công việc theo dự án | `g02` | project.task | 1 task | Hoàn thành (`is_closed`), Đang mở quá hạn, Đang mở còn lại (gồm việc không hạn) | `date_deadline` | `user_ids` | — | `g02.available` | `task` bucket+project |
| Cơ hội và hồ sơ thầu | `g03` | crm.lead | 1 cơ hội | bid: identified/preparation/submitted; direct riêng | `kd_deadline` | `user_id` | — | `g03.available` | `lead` route(+bid_state) |
| Kế hoạch sản lượng | `get_kd_plan_compare` | tp.periodic.plan (+amount measure=production) | 1 kế hoạch, một loại kỳ | target confirmed/unconfirmed/missing; source_status | `period_from` | owner_id | currency/căn cứ thuế từng dòng; chỉ khi `_kd_money_allowed` | `available`, `excluded` | `plan`, `plan_sources` |
| Hạn năng lực/chứng chỉ | `get_kd_credential_expiry` | tp.credential | 1 hồ sơ | Đã hết hạn (< hôm nay), Hôm nay–30 ngày, Sau 30 ngày | `valid_to` | owner_id | — | `available`; private do record rule | `credential` bucket |

"Ngày nguồn" của typed model: `date` (allocation/production/acceptance/payment/obligation), `period_from` (plan), `valid_to` (credential). Thời điểm "hôm nay" là `context_today` theo timezone người dùng. Task so `date_deadline` (datetime) với mốc ngày theo logic hiện hành; không đổi công thức trong task UI (gap G-4).

Kiểm chứng nhãn "Đến hạn trong 3 ngày": `_kd_mine(prefix, "due")` lấy hạn `< hôm nay + 4 ngày`; `kpis.due = tổng due − overdue`, overdue là hạn `< hôm nay`. Vậy `kpis.due` đếm hạn trong [hôm nay, hôm nay+3] — đúng "hôm nay và 3 ngày tới". Tooltip ghi mốc cụ thể từ `kpis.due_window`.

Bốn KPI cá nhân có thể giao nhau (một hồ sơ trả lại có thể quá hạn), không cộng, không làm lát vòng khuyên.

## 3. Bố cục

### Desktop ≥ 1200px (1440×900, sidebar mở, vùng nội dung ~1130px)

```text
┌ Tổng quan KH-KD                         [Tạo hồ sơ ▾] [⟳ Làm mới] [Xem dữ liệu ▾] [⚙] ┐
│ Dữ liệu lúc 09:52 07/11 · trong phạm vi quyền   Dự án 8 · Hợp đồng 11 · Phiên bản 11 ⓘ │
├ [Dự án ▾][Người phụ trách ▾][Từ ngày][Đến ngày][Xóa lọc]  ⓘ Ngày lọc tùy nguồn          ┤
├ Việc của tôi — trong phạm vi đang chọn                                                  ┤
│ [68 Chờ rà soát] [0 Bị trả lại] [0 Quá hạn] [0 Đến hạn trong 3 ngày]                    │
├──────────────────────┬──────────────────────────────────────────────────────────────────┤
│ Hồ sơ đang xử lý     │ Hồ sơ đang xử lý theo nhóm nghiệp vụ                             │
│   ◯ 121              │ Giao khoán        ███▓▓▓▓▓▓▒▒▒                          18       │
│ ■ Nháp 29 · 24%      │ Sản lượng tự khai ████▓▓▓▓▓▓▓▓▒▒▒▒                       25       │
│ ■ Đang rà soát 64    │ … 7 nhóm, cùng thang tuyệt đối                                   │
│ ■ Trả lại 28         │                                                                  │
│ [panel chọn nguồn khi đã chọn một lát]                                                   │
├──────────────────────┴───────────────┬──────────────────────────────────────────────────┤
│ Công việc theo dự án (top 8/Y)       │ Cơ hội và chuẩn bị hồ sơ thầu                     │
├──────────────────────────────────────┴──────────────────────────────────────────────────┤
│ [Kế hoạch sản lượng | Hạn năng lực / chứng chỉ]  (tải khi mở)                           │
├ Bảng điều hành dự án (giữ KD-UI-003)            │ Việc của tôi (tab)                    ┤
└ Bảng tổng hợp theo nguồn hồ sơ (mở khi cần)                                             ┘
```

Màn đầu 1440×900 thấy header, dải quy mô, bộ lọc, 4 KPI và phần chính của cặp vòng khuyên/thanh (chữ ≥ 13px).

### Tablet 768–1199px

Cặp chính xếp 2 cột 5/7 từ 992px; dưới 992px vòng khuyên trên, thanh dưới. Công việc/cơ hội xếp dọc. KPI 4 cột ≥ 768px.

### Mobile < 768px

Header 2 dòng (tiêu đề + dải quy mô; nút gọn icon). Bộ lọc thu trong `<details>` "Bộ lọc" có chip tóm tắt số bộ lọc đang áp; KPI lưới 2×2; vòng khuyên 180px và chú giải dưới; thanh 7 nhóm nhãn trên, thanh dưới; bảng cuộn ngang trong khung (KD-UI-003). Không cuộn ngang trang.

## 4. Thẩm mỹ

Token gắn trên `.o_tp_kd_ov` (không rò ra app khác):

| Token | Giá trị | Dùng cho |
| --- | --- | --- |
| `--kd-bg` / `--kd-card` | #F4F6F8 / #FFFFFF | nền / bề mặt |
| `--kd-ink` / `--kd-muted` / `--kd-line` | #1F2937 / #607287 / #D9E2EC | chữ / phụ / viền |
| `--kd-action` | #255F85 | nút chính, link |
| `--kd-draft` / `--kd-review` / `--kd-returned` | #8A9BB0 / #255F85 / #A12A35 | 3 trạng thái hồ sơ (vòng khuyên, thanh, chú giải, panel) |
| `--kd-done` / `--kd-warn` / `--kd-open` | #2F7D4F / #B45309 / #7FA7C6 | task hoàn thành / quá hạn / đang mở còn lại; chứng chỉ hết hạn dùng `--kd-returned`, ≤30 ngày `--kd-warn`, sau 30 ngày `--kd-done` |

Chữ: tiêu đề trang 24px, tiêu đề khu 16px, thân 14px, KPI 28px, số trong vòng 30px, số bảng 14px `tabular-nums`. Nhịp 8/12/16/24px; radius 10px card, 8px nút/ô. Bóng nhẹ một tầng. Không font/CDN/gradient/hero mới. Một nút primary "Tạo hồ sơ" (chỉ khi có quyền tạo); Làm mới và ⚙ là nút phụ; "Xem dữ liệu" là menu.

## 5. Vòng khuyên và thanh 7 nhóm

- Tâm vòng: tổng 3 state, nhãn "Hồ sơ đang xử lý". Chú giải mỗi state: chấm màu, nhãn, count, % = count/tổng (1 chữ số thập phân, `vi-VN`); không ép tổng % thành 100.
- Tổng 0: vòng trung tính + "Chưa có hồ sơ nháp, đang rà soát hoặc trả lại trong phạm vi lọc". Mọi nhóm không có quyền: "Bạn chưa có quyền xem các loại hồ sơ này" (khác tập rỗng). Một phần nhóm không có quyền: ghi "N nhóm không có quyền xem, không tính vào tổng".
- Lát nhỏ: count > 0 luôn có chiều dài tối thiểu 1,2 đơn vị (trực quan); số và % trong chú giải là số thật.
- Hover/focus lát hoặc chú giải: làm nổi state, D02 làm mờ state khác (`data-hl`), không RPC. Click/tap/Enter: chọn state → giữ mẫu số, tâm thêm dòng "Đang chọn: Đang rà soát 64 · 52,9%", mở panel "Chọn loại hồ sơ để mở" liệt kê các nhóm có count > 0 cho state đó (nút → `action_kd_open('g01', {source, state})`), nhóm count 0 không có nút, nhóm không quyền ghi rõ. Nút "Bỏ chọn" và phím Esc xóa chọn. Không mở tổng nhiều model vào một list hoặc tab cá nhân.
- Thanh: cùng thang tuyệt đối (max tổng dòng), thứ tự cố định theo nghiệp vụ; nhãn đầy đủ (bấm mở toàn bộ nguồn), tổng cuối dòng; đoạn count > 0 là nút có `aria-label` đầy đủ, đoạn 0 không render. Đối chiếu: Σ dòng theo state = tổng state; Σ tổng dòng = tâm vòng.

## 6. Biểu đồ chuyên đề

- **Công việc theo dự án**: 3 nhóm rời "Hoàn thành", "Đang mở quá hạn", "Đang mở còn lại"; top 8 theo quá hạn rồi đang mở; "Đang xem 8/Y dự án" + nút xem toàn bộ; tổng 3 nhóm lấy từ `g02.totals` (toàn tập, không từ top). Ghi chú "Trong nhóm đang mở còn lại có N việc chưa có hạn". Đây là số task, không là tiến độ khối lượng.
- **Cơ hội và chuẩn bị hồ sơ thầu**: khối "Đấu thầu" 3 thanh ngang trục 0 (Đã xác định, Đang chuẩn bị, Đã khai báo nộp — chưa xác minh) và khối "Chỉ định thầu" riêng; tổng (`.o_tp_kd_total_btn`). Không funnel, không tỷ lệ trúng/doanh thu.
- **Kế hoạch sản lượng** (tab, tải khi mở): chọn một loại kỳ; mỗi dòng một kế hoạch: kỳ, mã, dự án, đơn vị tiền + căn cứ thuế, cặp thanh "Mục tiêu đã xác nhận" và "Sản lượng nguồn", thang **riêng từng dòng** (không so chéo dòng khác tiền/căn cứ). Chưa xác nhận/chưa có mục tiêu/chưa đủ căn cứ hiện chữ, không hiện 0. Không cộng kỳ/tiền; không trend.
- **Hạn năng lực/chứng chỉ** (tab): vòng khuyên nhỏ 3 tập rời "Đã hết hạn", "Hôm nay – 30 ngày", "Sau 30 ngày" với mốc ngày cụ thể (`bounds`), chú giải là nút mở đúng nhóm; danh sách 5 hồ sơ sắp hết hạn gần nhất. Không suy tình trạng pháp lý.

## 7. Motion

| Tình huống | Hiệu ứng | Thời gian | Cài đặt |
| --- | --- | --- | --- |
| Vòng khuyên lần đầu có dữ liệu | mask vẽ cung 0→360° | 700ms ease-out | class `is-intro` một lần khi mount có dữ liệu; gỡ sau 900ms |
| Thanh 7 nhóm / công việc lần đầu | `scaleX(0→1)` từ trái, stagger 40ms | 480ms, cả nhóm < 800ms | cùng `is-intro`; phần tử giữ `t-key` nên filter/sort không replay |
| Đổi số liệu (filter/làm mới) | lát/thanh chuyển `stroke-dasharray`/`width` | 240ms | transition CSS |
| KPI đổi giá trị | crossfade + nền nhạt | 180ms | `t-key` theo giá trị |
| Đang tải lại | vùng dữ liệu mờ 0.6, không nhấp nháy trang | 200ms | `aria-busy` |
| Hover/focus lát, chú giải, tooltip | nổi lát (stroke dày), làm mờ phần khác | 150ms | CSS |
| Tab chi tiết | fade + trượt 6px | 200ms | `t-key` theo tab |
| Nút/card có action | đổi nền/viền, nhấn `translateY(1px)` | 140ms | CSS |
| Loading lần đầu | skeleton đúng bố cục | chỉ lúc chờ | shimmer; reduced → tĩnh |

`prefers-reduced-motion` và tùy chọn "Giảm chuyển động" (class `is-reduced` + `body.o_tp_kd_reduce_motion`) tắt intro/grow/slide/shimmer; số cuối và nút luôn dùng được ngay (không chờ animation).

## 8. Nhất quán dữ liệu

- `gen` (thế hệ bộ lọc) tăng khi đổi bộ lọc/xóa lọc/làm mới; mỗi phần (projects, mine, detail, sources) có `seq` riêng. Response chỉ áp khi `gen` và `seq` của phần còn hiện hành → không response cũ đè mới, không trộn scope.
- `loading` chỉ tắt bởi lần tải hiện hành; partial refresh không làm hỏng cờ của lần tải chính.
- Thời điểm "Dữ liệu lúc …" là `updated_at` của response chính đã render. Lỗi mạng/máy chủ khi đã có dữ liệu: giữ dữ liệu, gắn nhãn "Dữ liệu lúc … — chưa làm mới được".
- Lỗi quyền/phiên (`AccessError`, `AccessDenied`, `SessionExpired`, HTTP 401/403): xóa toàn bộ dữ liệu đang hiện (số, bảng, tab chi tiết) và chỉ hiện thông báo.

## 9. Thay đổi backend tối thiểu (đọc)

| Khóa thêm | Nơi | Ý nghĩa | Test |
| --- | --- | --- | --- |
| `kpis.due_window` = `{from, to}` | `get_kd_dashboard` | hôm nay và hôm nay+3 (ngày người dùng) | `test_due_tab_is_overdue_plus_due_of_current_owner` |
| `bounds` = `{today, soon_until}` | `get_kd_credential_expiry` | mốc hôm nay / hôm nay+30 | `test_g05_credential_date_boundaries` |
| `rows[].currency`, `rows[].basis_label` | `get_kd_plan_compare` | mã tiền tệ và nhãn căn cứ thuế của dòng mục tiêu; `null` nếu chưa có dòng | `test_g04_period_kind_unconfirmed_zero_and_money_scope` |

Không đổi domain, quyền, công thức, state hay drilldown.

## 10. Rủi ro và gap đã biết

- G-1 Dải quy mô không cùng bộ lọc (mục 2) — tooltip ghi rõ, không đổi công thức.
- G-2 KPI cá nhân 0 trong khi phạm vi > 0 là hợp lệ (người xem không được giao) — không nới quyền.
- G-3 Kế hoạch sản lượng chỉ 12 kế hoạch gần nhất của một loại kỳ (giới hạn helper hiện có, có ghi "còn N kế hoạch cũ hơn").
- G-4 Task so `date_deadline` (datetime UTC) với mốc ngày: việc hạn trong hôm nay có thể rơi vào nhóm khác tùy giờ — logic hiện hành, ghi nhận, không sửa trong task UI.
- G-5 Audit độc lập KD-NATIVE-001/KD-UI-002/003, business acceptance và pilot vẫn riêng.

## 11. Điều chỉnh khi triển khai

Ghi lại chỗ cài đặt thực tế khác mục 3–8; không đổi ngữ nghĩa số, quyền hay drilldown.

| Mục | Thiết kế ban đầu | Cài đặt thực tế | Lý do |
| --- | --- | --- | --- |
| 7 Intro thanh | `scaleX(0→1)` | `clip-path: inset(0 100% 0 0)` → `inset(0)` (keyframe `tp-kd-ov-grow` 480ms, stagger `--i` × 40ms) | `scaleX` kéo méo bo góc và chữ trong đoạn; clip giữ nguyên hình. |
| 7 Intro vòng | mask | `stroke-dasharray` + keyframe `tp-kd-ov-sweep` 700ms; `INTRO_MS = 900` gỡ `is-intro` | Không cần SVG mask; một lần mỗi mount, reduced bỏ qua. |
| 5 Hover liên kết | thuộc tính `data-hl` do JS đặt | CSS `:has()` sinh bằng `@each` theo 3 state trên khung cặp; JS không đổi state khi hover | Hover không render lại OWL, chắc chắn 0 RPC. |
| 5 Panel chọn nhóm | trong cột vòng khuyên | trải ngang cả khung cặp (dưới vòng + thanh), tạo bởi `select(state)`; Esc qua `onPairKey` | Đủ chỗ cho 7 nút ở 1280px trở xuống. |
| 5 Chú giải | dòng chấm + nhãn | ô (tile) bấm được, cao tối thiểu 40px: chấm màu, nhãn, count, % | Vùng bấm lớn hơn, dễ chạm trên mobile. |
| 5 Đoạn hẹp | — | đoạn quá hẹp đẩy số xuống dòng bị cắt (`flex-wrap` + `::before`), số vẫn ở `title`/`aria-label` và tổng dòng | Không hiện chữ số bị cắt ở 360px. |
| 3 Dải quy mô | trong hàng KPI | nằm ở đầu trang, ngoài `.o_tp_kd_kpis` | Tách quy mô phạm vi khỏi KPI cá nhân, tránh cộng nhầm. |
| 6 Kế hoạch | cặp thanh cùng thang dòng | thang từng dòng do máy chủ trả (`target_bar`, `source_bar`); nhãn phải dùng `ratioText()` (vi-VN, tối đa 1 chữ số) từ `ratio` máy chủ hoặc "Chưa so sánh" | Không tính tỷ lệ/tiền ở frontend. |
| 2 Bộ lọc ngày | — | client chặn `date_to < date_from` với "Đến ngày phải từ ngày bắt đầu trở đi." trước khi gọi RPC | Tránh tải vô nghĩa; backend giữ nguyên. |
| 8 Lỗi phiên | `AccessError`/`SessionExpired`/401/403 | thêm: response 401/403 không phải JSON tới dưới dạng `ConnectionLostError` có status → cũng xóa dữ liệu | Odoo trả HTML khi phiên hết hạn. |
| 7 Đang tải lại | mờ 0.6 | thêm `pointer-events: none` trên vùng dữ liệu khi `is-loading` | Không bấm vào số sắp bị thay. |
| 3 Menu "Xem dữ liệu" | chỉ khi có dữ liệu | hiện cả khi chưa có dữ liệu; danh sách tự kiểm ACL | Lối vào danh sách không phụ thuộc biểu đồ. |
| Test | — | `data-source`, `data-project`, `data-bucket`, `data-bid`, `data-route`, `data-kpi`, `data-key`, `data-plan` trên nút/đoạn | Kiểm thử trình duyệt không dựa vào `nth-child`/text. |
| Vận hành | — | asset tĩnh được cache tới khi restart Odoo; mỗi lần đổi XML/JS/SCSS phải `kd_ui004.py stop/start` trên clone (hoặc `apply` trên dev) | Tránh kiểm nhầm bundle cũ. |

Kiểm thử trình duyệt dùng chờ có giới hạn thay vì `networkidle` (bus/service worker của Odoo không bao giờ rảnh) và quay lại bằng breadcrumb thay vì nút Back (Back có thể đua với đẩy URL của web client).
