# KD-UI-004 — Kế hoạch làm lại Tổng quan KH-KD

Ngày 07/11/2026, Asia/Saigon. Người dùng yêu cầu Tổng quan đẹp hơn, thêm biểu đồ tròn, số liệu logic và nhiều animation. Đây là kế hoạch để giao Claude; chưa thay giao diện/dữ liệu.

## 1. Mục tiêu và nhận xét từ ảnh

Người xem cần nhanh chóng hiểu: bao nhiêu hồ sơ đang xử lý; tập trung ở trạng thái/nhóm nghiệp vụ nào; tôi cần làm gì; dự án nào có công việc cần chú ý. Mỗi số/biểu đồ phải có đường đi đến nguồn.

Ảnh cho thấy bộ lọc và 7 card chiếm nhiều chiều cao, các số quy mô đặt cùng nhóm với việc cá nhân; biểu đồ thanh dài thiếu cơ cấu chung. Bốn số cá nhân bằng0 trong khi phạm vi có nhiều hồ sơ có thể hoàn toàn hợp lệ, không được coi là lỗi dữ liệu rồi nới quyền hoặc thay số.

Theo ảnh: 29 nháp +64 đang rà soát +28 trả lại =121 hồ sơ đang xử lý; tổng 7 nhóm cũng bằng121. Đây chỉ là phép đối chiếu từ ảnh, chưa là truy vấn/audit database; không hardcode vào sản phẩm.

## 2. Bố cục chọn triển khai

```text
[Tổng quan KH-KD / thời điểm dữ liệu]       [Tạo hồ sơ ▾] [Làm mới] [Tùy chọn]
[Dải quy mô: Dự án · Hợp đồng · Phiên bản]  [Xem dữ liệu ▾]
[Dự án ▾] [Người phụ trách ▾] [Từ ngày] [Đến ngày] [Xóa lọc]

Việc của tôi — trong phạm vi đang chọn
[Chờ rà soát] [Bị trả lại] [Quá hạn] [Đến hạn trong 3 ngày]

[Vòng khuyên: cơ cấu hồ sơ][Thanh ngang: hồ sơ theo 7 nhóm nghiệp vụ        ]
[Tổng + chú giải/số/%     ][Cùng bộ đếm trạng thái, chọn để mở đúng nguồn  ]

[WBS theo dự án                         ][Cơ hội / chuẩn bị hồ sơ thầu      ]
[Tab chi tiết: Kế hoạch sản lượng | Hạn năng lực/chứng chỉ                   ]
[Bảng điều hành dự án — chọn cột, sort, pager, thao tác                     ]
[Việc của tôi — tab rà soát / trả lại / đến-quá hạn                         ]
[Bảng nguồn hồ sơ — mở rộng khi cần                                       ]
```

Desktop: cặp biểu đồ chính khoảng1/3 và2/3 vùng nội dung. Dải quy mô dùng ba số nhỏ thay ba card lớn; bốn KPI cá nhân cùng hàng khi đủ rộng. Không bỏ chỉ số hoặc tự ẩn số0. Mobile xếp dọc, bộ lọc thu gọn có chip tóm tắt và giữ trạng thái.

Ở1440×900, zoom100%, sidebar mở: ưu tiên nhìn được header, bộ lọc, việc cá nhân và phần chính cặp chart đầu. Kiểm ảnh thực; không đạt mục tiêu bằng thu chữ quá nhỏ. Chi tiết tải khi mở; bảng giữ chuẩn KD-UI-003.

## 3. Biểu đồ và định nghĩa dữ liệu

| ID | Biểu đồ | Nguồn/ý nghĩa | Tương tác chính |
| --- | --- | --- | --- |
| D01 | Vòng khuyên cơ cấu hồ sơ đang xử lý | `get_kd_dashboard().g01.totals`, 7 model typed, state draft/in_review/returned; mỗi(model,id) hiện hành đếm1lần | Chọn lát/chú giải highlight D02 và mở panel chọn loại hồ sơ trước khi đi nguồn |
| D02 | Thanh ngang xếp chồng hồ sơ theo nghiệp vụ | `g01.rows`, cùng tập/count/màu với D01; đủ7loại | Click đoạn mở list đúng source/state/filter bằng action hiện có |
| D03 | Công việc theo dự án | G02: Hoàn thành(is_closed), Đang mở quá hạn, Đang mở còn lại | Mở task theo dự án/nhóm; xem tất cả ngoài topN |
| D04 | Cơ hội và chuẩn bị hồ sơ thầu | G03: route direct riêng, route bid theo3state hiện có | Click mở đúng lead route/state; không là funnel chuyển đổi |
| D05 | Kế hoạch sản lượng và số đã gửi rà soát | G04: một loại kỳ, nguồn/đơn vị/currency/basis như helper hiện có | Chọn kỳ, mở kế hoạch/sản lượng nguồn; chỉ hiện tiền đúng quyền |
| D06 | Vòng khuyên nhỏ hạn chứng chỉ trong tab chi tiết | G05: Đã hết hạn / Hôm nay đến30ngày / Sau30ngày | Click nguồn đúng nhóm ngày, private restriction giữ nguyên |

### D01 và D02 — điểm nhấn tổng thể

- D01 giữa vòng là tổng3state, nhãn “Hồ sơ đang xử lý”. Không gọi là mọi hồ sơ công ty hoặc % hoàn thành dự án. Chú giải có nhãn, count và%; tỷ trọng=count/tổng3state, làm tròn hợp lý, không sửa count để ép tổng% đã làm tròn thành100.
- Tổng0 hiện vòng trung tính/empty text, không vẽ3phần bằng nhau. Không có quyền khác tập rỗng; giữ availability từ nguồn, chỉ mở rộng metadata read-only có test nếu thiếu.
- D02 cùng thang tuyệt đối theo count, không tự normalize mọi thanh100%. Nhãn nghiệp vụ đầy đủ, tổng cuối dòng, tooltip số phần quá nhỏ. Giữ thứ tự ổn định hoặc sort theo tổng có điều khiển; drilldown dựa source key, không index.
- Hover/focus/tap lát làm nổi chú giải và phần tương ứng D02; không RPC khi hover. Khi chọn trạng thái, giữ mẫu số gốc, làm nổi tập đang chọn và ghi rõ bộ lọc cục bộ; có xóa chọn.
- Tổng D01 gồm nhiều model: chọn lát phải cho chọn loại nguồn có count trước rồi gọi drilldown source+state+filter. Không mở121hồ sơ vào list một model, không thay bằng tab cá nhân, không tạo bảng nghiệp vụ tổng hợp đa năng. D02 vẫn click từng source/state trực tiếp.
- Zero segment không có vùng bấm giả. Tooltip/legend/button phải dùng được qua bàn phím và touch; không dựa màu hoặc hover duy nhất.

### Biểu đồ chuyên đề

- D03 ba nhóm rời, nhãn “Đang mở còn lại” vì đã tách quá hạn. Việc không có hạn nằm ở nhóm này và có số chú thích theo nguồn. TopN ghi rõ đang xem bao nhiêu/toàn tập; tổng không lấy từ topN. Đây là số task, không là tiến độ khối lượng/hợp đồng.
- D04 dùng thanh/cột trục0, giữ “Đã khai báo nộp — chưa xác minh”. Direct không là một giai đoạn của bid. Không suy doanh thu/trúng thầu/tỷ lệ chuyển đổi.
- D05 chưa xác nhận/chưa đủ căn cứ/không dữ liệu khác0. Không cộng tháng/quý/năm hoặc currency/basis khác nhau; tách nhóm/thang theo đơn vị nếu helper chưa đủ để so chung, có thể giữ paired bars từng dòng. Không dựng trend từ snapshot/ngày cập nhật, không gọi sản lượng là tiền thực thu/công nợ/lợi nhuận.
- D06 ngưỡng ngày theo timezone user/logic hiện hành,3tập rời, không thêm nhóm thiếu ngày nếu schema không cho phép. Không suy tình trạng pháp lý từ hạn. D06 tải trong tab, không bày nhiều pie lặp số ngoài trang chính.
- Màn hình dùng tiêu đề nghiệp vụ, không hiển thị mã G01/D01.

## 4. Logic KPI, bộ lọc, quyền

1. Ghi rõ “Việc của tôi” khác “Trong phạm vi được xem”. Một admin có thể xem nhiều nhưng không có việc được giao; không nới assignment/grant hoặc đổi dữ liệu để lấp0.
2. Bốn KPI cá nhân có thể giao nhau, không cộng thành tổng hoặc làm4lát pie. Mỗi số mở đúng inbox nguồn.
3. Đổi nhãn “Còn hạn của tôi” thành “Đến hạn trong3ngày” sau xác nhận domain due hiện hành: deadline trong[hôm nay,hôm nay+4), sau khi tách quá hạn, theo date/datetime/timezone nguồn. Không gọi mọi hồ sơ chưa quá hạn là sắp đến hạn.
4. Dải quy mô hiện không có cùng bộ lọc: project count dùng quyền/project; contract owner dùng create_uid, không lọc ngày; revision có domain/ngày riêng. Tooltip phải ghi đúng; không âm thầm đổi công thức/domain để giả cùng kỳ thống kê.
5. Lọc ngày tùy nguồn: typed date, plan period_from, credential valid_to, task date_deadline, lead kd_deadline. Chú thích cạnh bộ lọc; không gọi chung là ngày hoàn thành/doanh thu.
6. Thời điểm cập nhật là của response đã render thành công; refresh lỗi ghi rõ dữ liệu cũ nếu còn được phép xem, không giả là mới.401/403/revoke/session expiry xử lý dữ liệu nhạy cảm theo cơ chế hiện có.
7. Main/lazy/partial requests cùng filter generation: không response cũ đè mới, không trộn KPI/charts/tables khác scope khi đổi filter/tab/sort nhanh.
8. Backend enforce company/project/assignment/grant; không sudo aggregate rồi che CSS, không client-supplied arbitrary model/domain. Giữ action/context/native form/list và unsaved guard.
9. Không hardcode số ảnh, seed/cleanup/sửa giá trị/state/ngày để đẹp. Không tự tạo health score, % tăng trưởng, forecast hoặc lịch sử khi chưa có nguồn.

## 5. Hướng thẩm mỹ

Điểm nhấn là cặp vòng khuyên/thanh, còn header/KPI/bảng có phân cấp rõ. Giữ shell/sidebar hiện có, không đổi theme toàn hệ thống hoặc dựng hero lớn.

- Nền#F4F6F8, surface trắng, chữ#1F2937, phụ#607287, viền#D9E2EC, action#255F85.
- Nháp#8A9BB0, đang rà soát#255F85, trả lại#A12A35; task hoàn thành#2F7D4F, quá hạn#B45309. Mapping cố định cùng legend/tooltip/charts, không mỗi dự án một màu ngẫu nhiên.
- Font Odoo hỗ trợ tiếng Việt; heading24–28px, section16–18px, thân14–15px, KPI26–32px, số bảng14px tabular. Nhịp8/12/16/24px; radius8–12px; viền/shadow nhẹ theo phân tầng. Không font/CDN mới, gradient/glow phủ toàn trang.
- Một primary “Tạo hồ sơ”, Làm mới/tùy chọn phụ; “Xem dữ liệu” trong menu. Thêm khoảng thở bằng bố cục, không biến mọi ô thành card to giống nhau.
- Tất cả bảng giữ border/column/wrap/pager chuẩn KD-UI-003, không revert badge/header đã sửa.

## 6. Motion spec

| Tình huống | Hiệu ứng | Thời gian | Giới hạn |
| --- | --- | --- | --- |
| D01 lần đầu có dữ liệu | Vẽ cung vòng khuyên | 600–750ms | Một lần lúc vào trang, không xoay lặp |
| Lát/chú giải hover/focus/chọn | Highlight, offset nhẹ và tooltip | 120–180ms | Không đổi count/mẫu số; có touch/keyboard |
| D02/D03 xuất hiện | Thanh mở rộng đến giá trị cuối | 400–550ms | Stagger ngắn, cả nhóm dưới800ms; không replay khi sort bảng |
| KPI đổi dữ liệu | Crossfade giá trị/phản hồi nền | 150–220ms | Số cuối chính xác hiện ngay, không count-up tiền |
| Filter/làm mới | Crossfade dữ liệu/loading | 180–250ms | Không trộn hai response hoặc nhấp nháy cả trang |
| Tab/panel chi tiết | Fade/slide4–8px | 160–220ms | Giữ focus/scroll, không kéo giật trang |
| Nút/card có action | Đổi nền/viền và nhấn nhẹ | 120–160ms | Không làm layout nhảy hoặc giả khả năng bấm |
| Loading | Skeleton đúng layout | Chỉ lúc chờ | Error/empty hết loading; reduced mode tĩnh |

Giữ motion prefs và prefers-reduced-motion: giảm/tắt arc/grow/slide/shimmer, giữ focus/tooltip/thao tác rõ. Không parallax/autoplay/confetti/blink/đếm số lặp. Nút/số cuối dùng ngay, không chờ vẽ xong.

Không rebuild toàn bộ chart ở mỗi hover/patch; cleanup instance/observer/listener/timer/rAF khi unmount. Kiểm vào-ra nhiều lần không tích lũy chart hoặc animation.

## 7. Kỹ thuật và phạm vi

Ưu tiên OWL/QWeb/SCSS scoped trong tp_kd_workspace/static/src/overview; giữ menu/action/XMLID/controller/sidebar/table/form. Không sửa odoo/, addons/, React legacy hoặc quyền/state/write action.

Checkout có web.chartjs_lib và @web/core/utils/chart_hook, có thể dùng bundle nội bộ cho doughnut/bar hoặc SVG/HTML/CSS scoped nếu đủ tương tác. Đọc Chart/OWL API thật. Hook hiện recreate ở onPatched nên cô lập component/config, không replay bởi hover/prefs; không sửa hook core. Không CDN/package/framework/theme mới chỉ để vẽ tròn.

Canvas phải có legend button và tóm tắt số accessible bên ngoài; SVG cũng có label/điều khiển tương đương, không chỉ xuất ảnh chart.

Tái dùng payload/helper read-only. Chỉ mở rộng metadata/availability/whitelisted drilldown read-only tối thiểu khi cần và có test; không đổi công thức/domain quyền/model nghiệp vụ, không dựng API generic/reporting DB/data lake trong task UI.

Giữ fix overflow CHG-20261107-001: root Tổng quan cũng là .o_action, kiểm desktop≥992px/zoom/sidebar/scroll dài. Sticky đúng vùng cuộn, không che dropdown/tooltip hoặc tạo hai thanh cuộn dọc cạnh tranh.

## 8. Các lô và đầu ra

| Lô | Công việc | Kết quả/tiêu chí qua lô |
| --- | --- | --- |
| A | Inventory nguồn/filter/drilldown; wireframe desktop/mobile; metric/motion spec và acceptance trước code | Bố cục D01+D02, tách cá nhân/phạm vi, mọi số có nguồn và cách mở hồ sơ |
| B | Header/filter/quy mô/KPI gọn; D01+D02 liên kết | Màn đầu rõ, mẫu số/tổng khớp, chọn nguồn đúng model, zero/empty/no-permission đúng |
| C | D03–D06, responsive/motion, bảng hiện có | Chart đúng nghĩa, motion/reduced mode đầy đủ, form/list/Back/drilldown còn đúng |
| D | Clone regression/visual QA, snapshot/backup, áp dev18069 và bàn giao | Test/log/ảnh, dữ liệu/quyền bảo toàn, scroll ổn định, hướng dẫn tự kiểm |

Lô A là thiết kế trong prompt thực thi, không yêu cầu xin lại màu/spacing. Khi được giao prompt, Claude làm đủ A–D. Audit độc lập KD-NATIVE-001/KD-UI-002/003/business/pilot vẫn riêng; UI không đóng các cổng đó.

## 9. Acceptance và vận hành

- D01=D02 theo cả hai chiều, ba state rời; ca0/một lát/lát nhỏ/nhiều lát/số lớn/nguồn không readable. Click tổng phải chọn đúng source, không mở nhầm model.
- Cá nhân0/phạm vi>0 đúng nhãn; không cộng KPI hoặc nới quyền. Kiểm mốc due/ngày/timezone và scope của từng số quy mô.
- Race main/lazy/partial, filter/tab/sort/page đồng thời, stale/timestamp/loading/error/session/revoke/expiry, không lộ dữ liệu cũ.
- D03 topN/no-deadline, D04 route/state, D05 tiền/currency/basis/unknown/0, D06 private restriction/biên30ngày và drilldown nguồn.
- Bảng điều hành/Việc của tôi/nguồn, pager/sort/chọn cột/form/wizard/unsaved guard đúng KD-UI-003; không mở edit/upload/grant ngoài policy.
- UI360/390/768/1280/1440/1600/1920px, zoom thật125%/150%, sidebar mở/thu, mouse wheel/touchpad/touch/Back/refresh; app khác không nhận style.
- Motion lần đầu/filter/hover/tab/reduced và cleanup qua nhiều lần vào-ra; chữ/số cuối không phải chờ animation để đọc.
- Ảnh thực trước/sau above-fold/full-page/mobile đã xem lại; so UI với nguồn bằng actor đúng quyền; test Odoo/browser liên quan trên clone, không lấy checker/ảnh làm business acceptance.
- Source/DB/config/data_dir/port clone owned cô lập; không source chung assets chưa kiểm với dev. Trước áp dev: backup source/config/DB/filestore, verify và rollback delta; so dữ liệu nghiệp vụ/user/grant/state/filestore trước/sau. Dev chỉ smoke đọc/điều hướng, test ghi ở clone.
- Không dùng scripts/dev.py stop vì có thể dừng PostgreSQL; chỉ restart Odoo đúng ownership theo tooling/runbook. Không seed/cleanup/commit/push, giữ18069chạy.

Prompt thực thi: [CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md](../prompts/CLAUDE_KD_UI_004_OVERVIEW_REDESIGN.md).
