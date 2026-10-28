# Kế hoạch triển khai Tan Phat Executive Dashboard

Kế hoạch này bắt đầu sau khi tài liệu được duyệt. Lượt hiện tại chỉ tạo tài liệu, chưa tạo module hoặc cài package. P0 là điều kiện chặn, P1 cần cho bản dashboard dùng được, P2 phục vụ chất lượng/mở rộng.

Ước tính cho một lập trình viên đã biết Odoo/OWL, 1 ngày công = 8 giờ. S = 0,25–0,5 ngày, M = 0,5–1,5 ngày, L = 1,5–3 ngày cho từng gói việc; các gói có thể chồng lấp nên không cộng máy móc từng dòng. Chưa gồm thời gian chờ dữ liệu/owner và xử lý hạ tầng ngoài dự án.

| Phase | Ngày công dự kiến | Độ phức tạp | Phụ thuộc/cổng vào |
| --- | --- | --- | --- |
| 0 Môi trường | 0,5–2 | M, có bất định Windows/DB | Runtime và DB dev |
| 1 Khảo sát | 1–2 bổ sung | M | Audit hiện tại + BA/snapshot đúng phiên bản |
| 2 Thiết kế/spike | 1,5–2,5 | M/L vì OWL alpha | Phase0; contract lõi Phase1 |
| 3 Giao diện | 5–8 | L | Spike action/chart + fixture được kiểm |
| 4 Kiểm thử | 2–3 | M/L | Dữ liệu golden + bốn trang |
| 5 Tài liệu mở rộng | 0,5–1 | M | Contract/UI đã ổn định |

Tổng khung khoảng 10,5–18,5 ngày công. Đây là ước tính lập kế hoạch, cần hiệu chỉnh sau spike và chốt BA. Việc chưa có BA/crosswalk không chặn dựng shell/mock synthetic; chỉ chặn công bố KPI hoặc bộ lọc chịu ảnh hưởng như đã xác minh.

## Nguyên tắc thực hiện

- Mỗi phase có cổng nghiệm thu; không bắt đầu page khi data contract chưa có owner.
- Không sửa `addons/` hoặc `odoo/`; module mới nằm ở `custom_addons/tanphat_dashboard`.
- Không đặt dữ liệu tài chính thật trong static assets, Git hoặc fixture frontend.
- Một PR/commit nhỏ theo feature; test và tài liệu đi cùng thay đổi contract.
- Không thêm dependency ngoài khi Odoo Web đã có API đáp ứng.

## Phase 0 — Chuẩn bị môi trường (P0)

**Mục tiêu:** Có runtime Odoo 20 chạy được trên database phát triển, xác nhận addons path và khả năng build asset.

| Việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Tạo venv Python 3.12 cho source | ngoài Git hoặc `.venv/` ignored | quyền máy | P0 | M |
| Cài requirements.txt theo runtime được chốt | venv/pip lock nội bộ | venv | P0 | M |
| Xác nhận passlib/lxml/cbor2/sass và import `odoo` | smoke script ngoài repo | cài package | P0 | S |
| Xác nhận PostgreSQL version, port, user, DB dev | cấu hình local ngoài Git | PostgreSQL service | P0 | M |
| Tạo config `odoo-dev.conf` ngoài source tracked | thư mục cấu hình riêng ngoài Git hoặc secrets manager | DB + paths | P0 | S |
| Đặt addons path core + custom_addons | config | thư mục module | P0 | S |
| Chạy `odoo-bin --stop-after-init` và `/web` | logs local | config | P0 | M |
| Chạy một web unit-test hiện có qua `/web/tests` | không thay core | Odoo chạy | P1 | M |

**Bàn giao:** log startup sạch, URL local, database dev rỗng/được phép, lệnh reproducible và README ngắn cho môi trường.

**Nghiệm thu:** `python odoo-bin --version` chạy; server listen đúng port; Apps List mở; không có secret trong Git; `addons_path` ghi nhận custom_addons. Hiện trạng khảo sát cho thấy phase này chưa đạt vì `passlib` thiếu và TCP 5432 bị từ chối.

## Phase 1 — Khảo sát và khóa dữ liệu (P0)

**Mục tiêu:** Chốt định nghĩa, fixture ẩn danh và golden reconciliation trước khi dựng UI.

| Việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Bổ sung đúng `Phan_tich_nghiep_vu.docx`/phiên bản owner | kho tài liệu nội bộ ngoài Git public | người nghiệp vụ | P0 | S |
| Xác nhận workbook được dùng: tên, SHA, ngày snapshot | `docs/source/README.md` | file gốc | P0 | S |
| Chốt crosswalk “Khảo sát” vs “Khảo sát địa hình” | `docs/dashboard/05_DATA_CONTRACT.md` | BA + PKH | P0 | M |
| Viết bảng mapping 2 nhật ký, ChuDauTu, Thauphu | data contract | audit | P0 | M |
| Thiết kế effective ledger test cases; triển khai khi có skeleton Phase2 | `static/tests/fixtures/ledger_cases.js` ở lượt code | mapping | P0 | M |
| Tạo fixture synthetic: sửa, xóa, phụ lục, cấp 1/2, null/0/âm | fixture file ngoài data thật | owner KPI | P0 | M |
| Tính golden totals độc lập từ snapshot copy có quyền | `docs/reconciliation/` ngoài public repo | workbook | P0 | L |
| Chốt danh sách KPI/alert owner và ngưỡng | requirements doc | lãnh đạo/PKH/QT-TC | P0 | M |

**Bàn giao:** data dictionary, schema v1, fixture read-only, bảng expected totals và danh sách quyết định còn chờ.

**Nghiệm thu:** mọi KPI có nguồn và công thức; mỗi số phân biệt zero/null và ambiguous_zero; fixture không chứa tên/tiền thật; expected totals đối chiếu từng hạng mục và tổng cấp 1; cấp 2 không làm đổi tổng cấp 1. Những điểm BA chưa xác nhận được ghi rõ và khóa tính năng chịu ảnh hưởng.

## Phase 2 — Thiết kế kỹ thuật và spike OWL (P0/P1)

**Mục tiêu:** Chứng minh client action, props/state, Chart.js và layout chạy đúng source Odoo 20 hiện tại.

| Việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Tạo skeleton `custom_addons/tanphat_dashboard` | addon root | Phase 0 | P0 | S |
| Viết manifest/menu/action tối thiểu | `__manifest__.py`, `views/*_menus.xml` | root | P0 | S |
| Spike registry action + template + useProps | `static/src/app/spike_action.*` | Odoo chạy | P0 | S |
| Spike useChart load/destroy và fallback table | `static/src/shared/charts/*` | web.chartjs_lib | P0 | M |
| Chốt token SCSS và CSS namespace | `static/src/styles/tokens.scss` | UI/UX doc | P1 | S |
| Chốt route/query state/snapshot metadata | `static/src/app/navigation_state.js` | contract | P0 | M |
| Chốt repository interface và Result/Error | `features/dashboard_data/repository_contract.js` | schema | P0 | M |
| Hoàn thiện architecture README | addon README | quyết định | P1 | S |

**Bàn giao:** action mở từ menu, render một KPI fixture, chart tải một lần và hủy được, lint/format cơ bản, sơ đồ component.

**Nghiệm thu:** không sửa core; action tag/menu khớp; không lỗi OWL compatibility; chart không còn instance sau unmount; route đổi không tạo request cũ ghi đè; bundle chỉ dùng web/chart.js có sẵn.

## Phase 3 — Xây dựng giao diện (P1)

**Mục tiêu:** Hoàn thiện bốn trang và repository mock theo wireframe, giữ UI độc lập nguồn dữ liệu.

| Nhóm việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Shell/rail/header/breadcrumb | `static/src/shared/shell/*`, `app/*` | spike, tokens | P1 | M |
| Project selector + filter bar | `static/src/shared/filters/*` | Project DTO | P1 | M |
| KPI card, metric pair, formatters | `shared/kpi`, `shared/formatting` | KPI DTO | P1 | M |
| Chart panel + table fallback | `shared/charts` | ChartSpec | P1 | L |
| Alert list + explanation | `shared/alerts` | Alert DTO | P1 | S |
| Table/pager/sort/column visibility | `shared/table` | item/contractor DTO | P1 | L |
| Overview page | `features/overview/*` | shared | P1 | M |
| Investor page | `features/investor/*` | table/repository | P1 | M |
| Contractors hierarchy | `features/contractors/*` | level grouping | P1 | L |
| Detail page/panel/history | `features/detail/*` | transaction DTO | P1 | L |
| Mock repository + filter recompute | `features/dashboard_data/*` | fixture + aggregate utility | P1 | L |
| Loading/empty/error/stale states | `shared/states` | all pages | P1 | M |
| Responsive/a11y pass | SCSS + templates | rendered pages | P1 | M |

**Bàn giao:** bốn route trong action, fixture label, filter xuyên trang, drill-down context, bảng fallback chart, responsive desktop/tablet.

**Nghiệm thu:** không component nào import cấu trúc Excel; KPI/table/chart dùng cùng snapshot; cấp 2 không cộng; null/0/âm đúng quy tắc; keyboard/focus/aria hoạt động; không fake link chứng từ.

## Phase 4 — Kiểm thử và đối chiếu (P0/P1)

**Mục tiêu:** Chứng minh đúng số và ổn định frontend trước demo.

| Việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Unit effective ledger/aggregate | `static/tests/effective_ledger.test.js`, `aggregates.test.js` | repo mock | P0 | M |
| Contract/schema validation | `data_contract.test.js` | DTO | P0 | S |
| Repository/filter/snapshot race | `repository.test.js`, `filters.test.js` | services | P0 | M |
| Component/action tests bằng HOOT | `dashboard_action.test.js`, `overview.test.js` | Odoo server/assets | P1 | M |
| Chart lifecycle/leak | `chart_lifecycle.test.js` | useChart | P1 | M |
| A11y/keyboard/reduced-motion | `accessibility.test.js` | templates | P1 | M |
| Golden reconciliation với Excel | script/fixture riêng, không raw commit | phase 1 | P0 | L |
| Browser viewport visual review | screenshot QA nội bộ | phase 3 | P1 | M |
| Performance fixture lớn | benchmark script | phase 3 | P2 | M |

**Bàn giao:** test report, reconciliation report, ảnh kiểm tra viewport, danh sách known limitations.

**Nghiệm thu:** test nghiệp vụ ở [07_TEST_PLAN.md](07_TEST_PLAN.md) đạt; sai số integer tiền = 0; mỗi mismatch có owner/quyết định; không có console error/leak; chart và table có fallback.

## Phase 5 — Chuẩn bị thay nguồn (P1/P2)

**Mục tiêu:** Chuẩn bị thiết kế cắm adapter Odoo thật mà không phá UI. Phase này chỉ bàn giao tài liệu/API contract và điểm mở rộng; triển khai backend hoặc adapter thật nằm ở roadmap riêng.

| Việc | File/thư mục | Phụ thuộc | Ưu tiên | Độ phức tạp |
| --- | --- | --- | --- | --- |
| Chốt model/API owner và quyền đề xuất | `08_FUTURE_ROADMAP.md` + ADR | nghiệp vụ/backend owner | P0 | M |
| Định nghĩa method, DTO, aggregate và pagination | `05_DATA_CONTRACT.md` | schema v1 | P1 | M |
| Mô tả điểm inject OdooRepository/DTO validator | `04_FRONTEND_ARCHITECTURE.md` | interface mock | P1 | S |
| Đặc tả contract test Mock/ORM cho lượt sau | `07_TEST_PLAN.md` | expected DTO | P1 | S |
| Liệt kê alert cần field/ngưỡng mới | roadmap | owner cảnh báo | P2 | S |
| Đặc tả company/project scope và permission matrix | roadmap + data contract | role đề xuất | P1 | M |
| Lập runbook snapshot/reconciliation/cắt chuyển | roadmap | Excel reconciliation | P1 | M |

**Bàn giao:** API contract version, đặc tả adapter, permission matrix dự kiến, runbook migration/reconciliation và phương án đa dự án.

**Nghiệm thu:** method/DTO/error/scope mô tả đầy đủ; biết rõ adapter sẽ gọi đâu và kiểm quyền ở đâu; có tiêu chí server từ chối ngoài scope, không gửi raw attachments/NAS và đối chiếu timestamp/provenance. Không yêu cầu server thật hoặc adapter thật trong phase frontend này.

## 7. Thứ tự Codex nên thực hiện ở lượt sau

1. Kiểm tra user đã cung cấp đúng `Phan_tich_nghiep_vu.docx` và owner KPI.
2. Hoàn thành Phase 0, ghi lệnh chạy trong README cục bộ.
3. Tạo skeleton + spike action, chưa tạo page lớn.
4. Tạo schema, fixture ẩn danh và effective-ledger tests trước UI.
5. Tạo shell, filter và formatter; sau đó làm Overview.
6. Làm bảng Investor, rồi hierarchy Contractor, rồi Detail.
7. Chạy test/reconciliation mỗi khi KPI hoặc aggregate thay đổi.
8. Review screenshot desktop/tablet, keyboard và reduced motion.
9. Chỉ sau cổng mock đạt mới quyết định ORM/API adapter.

## 8. Quyết định cần xác minh trước chức năng tương ứng

- Path custom addon và cấu hình addons path trên máy dev/CI.
- Bộ tên hạng mục dùng chung giữa CĐT và thầu phụ, đặc biệt “Khảo sát”/“Khảo sát địa hình”.
- Owner/ngưỡng các cảnh báo và cách phân biệt tạm ứng.
- Phạm vi khoán mẹ khi một phòng nhận nhiều hạng mục.
- Ai được xem toàn công ty, theo dự án hay theo phòng khi có dữ liệu thật.
- API/ORM model nào thay Excel, thời điểm snapshot và timezone nghiệp vụ.
- Có cần export Excel song song không; nếu có, export ở backend sau khi contract ổn định.

## 9. Checklist giao Codex thực hiện tiếp

- [ ] Đọc đủ tám tài liệu và guideline Odoo; áp dụng frontend-design cho implementation.
- [ ] Xác minh lại commit, Python, PostgreSQL và config; không chạy với DB chưa rõ.
- [ ] Khởi động Odoo dev và chứng minh asset/test runner hoạt động.
- [ ] Tạo custom addon chỉ phụ thuộc web, action/menu/props theo OWL3.
- [ ] Chốt schema, fixture ẩn danh và các trường BA còn thiếu; không gán source thật cho mock.
- [ ] Viết test hiệu lực/phụ lục/cấp1-cấp2; đối chiếu raw snapshot riêng.
- [ ] Xây shell, KPI, filters, table, ChartPanel và state components.
- [ ] Hoàn thiện Overview → Investor → Contractors → Detail.
- [ ] Kiểm filter scope, race request, snapshot consistency và drill-down.
- [ ] Review viewport/keyboard/contrast/reduced-motion, sửa lỗi nhìn thấy.
- [ ] Chạy HOOT, install/update smoke test và reconciliation; báo test chưa chạy.
- [ ] Bàn giao module/README và known limitations; chỉ thiết kế điểm kết nối backend cho roadmap.
