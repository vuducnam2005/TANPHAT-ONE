# Roadmap và chuẩn bị kết nối dữ liệu thật

## 1. Mục tiêu chuyển đổi

Dashboard frontend mẫu chỉ là lớp đọc số liệu. Khi Odoo có sổ giao dịch chuẩn, thay MockRepository bằng adapter Odoo/API theo đúng DTO v1. Không chuyển logic vào component và không để Excel trở thành database lâu dài. Trong thời gian song song, Excel là nguồn đối chiếu được đóng băng theo snapshot; Odoo là nguồn hiển thị khi reconciliation đạt.

## 2. Lộ trình đề xuất

### Giai đoạn R0 — Chốt quyết định (P0)

- Bổ sung đúng `Phan_tich_nghiep_vu.docx` và owner cho từng KPI.
- Chốt crosswalk danh mục hạng mục, loại thầu phụ, đơn vị nội bộ và timezone.
- Chốt mô hình snapshot: thời điểm ghi sổ, thời điểm hiệu lực, quy ước ngày sửa/hủy.
- Chốt role HĐQT/TGĐ, GĐDA, Ban KD/Kế hoạch, QT-TC, phòng nhận khoán.
- Quyết định API hay ORM method, và ai là owner backend/module.

**Cổng:** data contract v1 được ký duyệt, không còn KPI không có nguồn.

### Giai đoạn R1 — Chạy dashboard mock trong Odoo (P1)

- Hoàn thành addon action/menu, fixture ẩn danh, bốn trang, test và screenshot QA.
- Chứng minh OWL/Chart.js với commit Odoo 20 hiện tại.
- Không dùng dữ liệu NAS hoặc static thật.

**Cổng:** [06_IMPLEMENTATION_PLAN.md](06_IMPLEMENTATION_PLAN.md) Phase 0–4 đạt; demo cho lãnh đạo bằng nhãn “Dữ liệu mẫu”.

### Giai đoạn R2 — Xây ledger Odoo tối thiểu (P0 cho dữ liệu thật)

Đề xuất model thẩm định, chưa tạo trong lượt này:

| Đối tượng | Model đề xuất | Trường tối thiểu |
| --- | --- | --- |
| Dự án | `tp.project` kế thừa `project.project` hoặc model được duyệt | code duy nhất, tên, CĐT, owner, company, timezone, trạng thái |
| Danh mục hạng mục | `tp.work.item` | key chuẩn, tên hiển thị, nhóm chuyên môn, bước công việc, aliases được duyệt |
| Đối tác | `res.partner` + loại/vai trò | contractor/investor, mã TQ/NB, liên hệ, MST, company |
| Sổ CĐT | `tp.client.transaction` | project, item, event, amounts, operation, root_transaction_id, sequence, effective, documents |
| Sổ thầu phụ | `tp.contractor.transaction` | project, contractor, parent allocation, item, type, amounts, operation/effective |
| Chứng từ | `ir.attachment` hoặc DMS được duyệt | access-controlled relation, checksum, document type, URL không lộ NAS |

Luật `effective` nên tính ở server từ root/sequence và không cho client tự quyết. Sửa/hủy append-only, lý do bắt buộc, record rule không cho xóa vật lý sau khi có giao dịch. Phụ lục lưu giá trị mới toàn hạng mục, có ngày hiệu lực và chứng từ.

**Cổng:** ORM constraints, access rights, record rules, migration test và audit log đã review. Chưa có cổng này thì không gọi dữ liệu mock là dữ liệu production.

### Giai đoạn R3 — Adapter thật và song song Excel (P1)

- Tạo OdooRepository trả cùng DTO v1, có server aggregation/pagination.
- Tải một dự án thí điểm, không import toàn công ty.
- Đối chiếu Excel theo item/contractor/root/metric bằng report che dữ liệu nhạy cảm.
- Xử lý tên hạng mục alias đã duyệt; record không map vào `unmapped` và không cộng im lặng.
- Hiển thị snapshot source/version và giờ đồng bộ; không hứa realtime nếu job chưa có.
- Duy trì export/Excel report chỉ nếu lãnh đạo cần trong giai đoạn chuyển tiếp.

**Cổng:** sai số tiền bằng0 theo snapshot; count/item/root khớp; cấp2 không double count; quyền xem đúng scope; owner ký report.

### Giai đoạn R4 — Phân quyền và vận hành (P1)

| Role | Phạm vi xem dự kiến | Hành động dashboard |
| --- | --- | --- |
| HĐQT/TGĐ | Toàn công ty/company được ủy quyền | Xem overview, cảnh báo, drill-down chứng từ được phép |
| Phó TGĐ | Mảng/khu vực được giao | Xem overview và dự án trong scope |
| GĐDA | Dự án phụ trách | Xem dự án, item, đơn vị, giao dịch |
| Ban KD/Kế hoạch | Dự án/contract được phụ trách | Xem hai phía và lịch sử |
| QT-TC | Dự án/tài chính được phân quyền | Xem thanh toán, công nợ, chứng từ |
| Phòng nhận khoán | Dự án/parent allocation của phòng | Xem scope phòng; cấp2 không lộ ngoài quyền |
| Admin kỹ thuật | Vận hành module, không tự được xem tài chính nếu policy tách | Cấu hình/diagnostics |

Đây là ma trận cần nghiệp vụ phê duyệt, không phải security đã cài. Odoo record rules là lớp bắt buộc; UI ẩn menu không phải bảo mật. Kiểm thử quyền bằng user thật/synthetic, company và dự án ngoài scope. Attachment URL phải kiểm quyền lần nữa.

### Giai đoạn R5 — Mở rộng đa dự án và hiệu năng (P2)

- Company-wide overview với aggregate server/materialized view khi cần.
- Bộ lọc năm/CĐT/GĐDA/phòng/khu vực sau khi field và quyền đã có.
- Cache theo snapshot + user/company scope, invalidation sau transaction commit.
- Pagination server, export được phân quyền, audit refresh.
- Mobile/read-only nếu có nhu cầu đã đo; không mặc định làm PWA/offline.
- Cảnh báo cấu hình ngưỡng: công nợ quá hạn, tồn chưa NT, giữ lại đến hạn; cần owner, ngày đến hạn và dữ liệu không có trong workbook hiện tại.

## 3. Di chuyển dữ liệu Excel

### Mapping và kiểm soát

1. Nạp danh mục hạng mục và alias sau khi làm sạch; không tạo item từ mỗi chuỗi không dấu.
2. Nạp danh bạ đối tác; chuẩn hóa mã TQ/NB, tên, liên hệ và loại. Không sử dụng cột tìm kiếm H/I/J làm master data.
3. Nạp project từ DATA D6:D8; unique code theo company, kiểm tra năm/mã.
4. Nạp NHAT_KY_TC và NHAT_KY vào hai ledger side riêng; giữ ID, ID GỐC, thao tác, thứ tự và link chứng từ đã được cấp quyền.
5. Recompute effective server-side; báo stream trùng/mất ID/root bất thường.
6. Recompute current contract theo phụ lục mới nhất; không biến giá trị điều chỉnh thành phần chênh.
7. Recompute cấp 1/2 và allocation parent; dòng cấp2 không cộng tổng công ty.
8. Đối chiếu ChuDauTu/Thauphu/TP_* chỉ như view kiểm tra; không import view thành giao dịch.
9. Lưu mapping run ID, source file hash, import time, actor và report mismatch. Không overwrite import đã phát hành; dùng correction transaction.

### Dữ liệu cần hỏi thêm

- Ngày sự kiện nghiệp vụ riêng với ngày ghi sổ/sửa.
- Có cho phép nhiều công ty/chi nhánh hay chỉ company Tấn Phát.
- Mã danh bạ có ổn định qua nhiều năm và hợp nhất nhà cung cấp ra sao.
- Tỷ lệ giữ lại theo hợp đồng có hiệu lực từ ngày nào.
- Cách phân bổ khoán mẹ cho nhiều hạng mục và xử lý con vượt mẹ.
- Hồ sơ NAS sẽ chuyển sang `ir.attachment`/DMS nào, ai được đọc.
- Giao dịch tiền từ file Kế toán/Master có field đối chiếu nào; workbook PKH không đủ để thay kế toán.
- Có cần số dư theo thời điểm hay chỉ snapshot hiện tại.

## 4. Rủi ro và phương án giảm thiểu

| Rủi ro | Hậu quả | Giảm thiểu |
| --- | --- | --- |
| Chuyển Excel cache thành nguồn thật | Sai do stale formula/macro | Đóng băng hash, recalc bằng Excel bản copy, đối chiếu ledger độc lập |
| Trùng cấp2 | Phóng đại chi phí | Server filter level1 cho company total; test B07/B08 |
| Tên hạng mục không chuẩn | So sai doanh thu/chi phí | Danh mục master + alias approval; unmapped alert |
| Xem số âm là vi phạm | Quyết định sai | Label tạm ứng/chưa NT; không score severity khi chưa có owner |
| Không có ngày hiệu lực | Báo cáo lịch sử sai | Chỉ snapshot hiện tại; thêm business event date trước time series lịch sử |
| ORM/API không đồng nhất DTO | UI rẽ nhánh theo source | Contract test Mock vs Odoo, schema version |
| Quyền chỉ làm ở UI | Lộ số liệu/chứng từ | Record rules/server scope + attachment auth + tests |
| Odoo 20 OWL alpha | Lỗi lifecycle/upgrade | Pin commit, spike, HOOT, không patch core |
| Chart quá nhiều điểm | Chậm/tràn | Aggregate server/downsample, fallback table, đo p95 |
| NAS URL lộ path | Mất kiểm soát chứng từ | Attachment proxy/ACL, không đưa UNC vào browser |

## 5. Quyết định kỹ thuật cần ghi thành ADR

- ADR-001: Odoo 20 client action và OWL 3, không React/app riêng.
- ADR-002: Repository DTO là ranh giới, Mock → Odoo adapter.
- ADR-003: Append-only ledger, root ID/sequence/effective, không xóa vật lý.
- ADR-004: Tổng thầu phụ chỉ cấp1; cấp2 là view riêng.
- ADR-005: Tiền integer VND, null/zero/negative semantics và tỷ lệ không trần.
- ADR-006: Chart.js dùng web.chartjs_lib v4.5, không thêm CDN/library.
- ADR-007: Dữ liệu thật không nằm static; fixture ẩn danh và source hash ngoài public bundle.
- ADR-008: Phân quyền server-side và attachment access trước go-live.

## 6. Checklist go live

- [ ] Source commit và Odoo version được pin trong CI.
- [ ] Venv/requirements và PostgreSQL dev/prod đã ghi runbook; backup/restore thử thành công.
- [ ] `custom_addons` nằm ngoài core; manifest/assets/license/security đã review.
- [ ] Data contract v1 và owner KPI đã ký; API/ORM contract có version.
- [ ] Reconciliation Excel → Odoo pass với hash/snapshot cụ thể.
- [ ] Quy tắc sửa/hủy/phụ lục/cấp2/parent allocation có audit log.
- [ ] Permission matrix và attachment access test pass.
- [ ] Dashboard có loading/empty/error/stale, a11y, responsive và chart fallback.
- [ ] Không còn raw Excel, UNC path, người liên hệ, tiền thật trong static/Git/log public.
- [ ] Monitoring thời gian tải, lỗi repository, snapshot age và mismatch có owner xử lý.
- [ ] Quy trình rollback addon và cắt chuyển Excel đã diễn tập.
- [ ] Lãnh đạo duyệt cách diễn giải số âm/vượt nghiệm thu và các cảnh báo.
