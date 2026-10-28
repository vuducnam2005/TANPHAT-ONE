# BIZ-001 — Bằng chứng và ca nghiệm thu

**Trạng thái:** tài liệu phân tích, dữ liệu mẫu không phải dữ liệu runtime.  
**Bản sao đọc:** .local/biz-001/manifest.json. Macro, external link và nguồn NAS không được chạy.

Gốc nguồn là `\\192.168.1.2\6.3 Tadic_Thu viec\ERP`. S01/S05 ở gốc, S02/S03/S04 ở `Ban KD`. Hash nhận diện đúng bản đã phân tích; không khẳng định đây là quy chế đang có hiệu lực pháp lý mới nhất. Pxxx/Txx là nhãn paragraph/table trong bản trích S01 do script phân tích tạo; ảnh là embedded workflow tương ứng. Workbook đọc cả công thức lẫn cached value, không tính lại và không kiểm chứng macro/crawl runtime. S02 được trích text và xem ảnh cả trang.

## 1. Registry nguồn

| Mã | Nguồn | SHA-256 | Vai trò |
| --- | --- | --- | --- |
| S01 | Quy trinh nghiep vu TanPhat JSC_V1.0.docx | 7b1c94c32c89f02697dac9a4cf9a70f07d61a312d3b14ea73ac7f74d6259b413 | Quy trình cấp công ty, RACI, đấu thầu, hợp đồng, nghiệm thu |
| S02 | T4.2026-Phân công nhiệm vụ Ban Kinh doanh.pdf | 1401320f6078e638545647f079bcdb08f072f0c3ce53ef9c70d6b0ae3582a651 | Trách nhiệm năm vai trò Ban KD |
| S03 | Mẫu PKH - Quản trị dự án v10_5.xlsm | 4ee0ff2750586ecc0992e6e869d97bf8be4f2d9727540f785344eecac04ba2ab | Form, sổ giao dịch, revision/void, KPI và cảnh báo |
| S04 | DA Temp.xlsm | b09872dd439f199e5f80818d6f91e79d54966728c93b10792a50d126bd173db7 | Kiểm tra biến thể của sổ giao dịch |
| S05 | Master_Quan_tri_chung_v10_5.xlsm | 381afeded55883939f52ea65cdd8a6656d67e931bfcbd0402d7628b94c507e99 | Import/snapshot, tổng hợp và đối chiếu PKH–KT |

## 2. Bằng chứng đã dùng

| Mã | Vị trí | Phát hiện | Tác động thiết kế |
| --- | --- | --- | --- |
| E01 | S01 P026–P028 | Mỗi task có một owner; task nhận phải vào BASE để theo dõi/điều phối/duyệt chi | owner/task và BASE reference là hai quan hệ khác nhau |
| E02 | S01 P041–P044 | TGĐ lãnh đạo, ký/duyệt trong phạm vi; delegation có nhưng không nêu hạn mức | không suy ra signatory threshold |
| E03 | S01 P045–P063 | KD chủ trì đấu thầu, hợp đồng, kế hoạch, nghiệm thu/thanh quyết toán | KD là đầu mối nghiệp vụ, chưa phải quyền Odoo tự động |
| E04 | S01 ảnh 2,3,4,5,9; T02 | Có luồng đấu thầu → hợp đồng → kế hoạch/giao khoán → KCS/nghiệm thu → thanh toán; QT-TC/Kế toán kiểm tra | tách review, ký, nghiệm thu và posting |
| E05 | S03 HDSD B103–B112 | Contract original chỉ ở giao dịch gốc; contract updated là giá trị mới cả hạng mục; production/acceptance/invoice/cash/retention là cột riêng | revision snapshot và typed records |
| E06 | S03 HDSD B117 | Các ô tiền có thể để trống; chỉ hạng mục bắt buộc | null khác zero; không ép dữ liệu thiếu thành 0 |
| E07 | S03 HDSD B110 | Nhãn “GT phải xuất hóa đơn” được hướng dẫn bằng giá trị VAT đã xuất lần này | model dùng invoiced_amount, không nhầm nghĩa vụ phải xuất |
| E08 | S03 HDSD B121–B127 | Ví dụ minh họa tách giá gốc 1.2b, giá mới 1.3b, production 780m, acceptance/invoice 650m, cash 585m, retention 65m | số trong tài liệu chỉ dùng làm kiểm tra logic; ca code dùng dữ liệu giả lập |
| E09 | S03 HDSD B139–B143, B247–B255; S05 HDSD B14, 07_GiaTriKhoan_PhongBan | Cấp 1 là thầu phụ công ty + khoán nội bộ; cấp 2 là thầu phụ của phòng; không cộng cấp 2 lần hai; con vượt mẹ cảnh báo | parent_id, aggregate cấp 1 và warning |
| E10 | S03 HDSD B189–B210, B353–B358; S04 NHAT_KY_TC L5:O9 | Nhật ký append-only; latest hiệu lực theo root; bản mới thay bản cũ; không xóa vật lý | revision/void và effectivity |
| E11 | S03 HDSD B199 | Sửa dòng có thể reset ngày về hôm nay | không copy macro behavior; giữ business_date |
| E12 | S05 HDSD B5–B8, LOG_Import | Crawl nightly/snapshot được mô tả nhưng chưa chứng minh service đang chạy; import lại thay snapshot project | provenance/freshness theo source |
| E13 | S05 HDSD B12 | “Tỷ suất lợi nhuận” chỉ là (NT chính − NT thầu phụ)/NT chính theo cohort | không gọi là profit kế toán đầy đủ |
| E14 | S05 HDSD B15–B16 | Một cột cảnh báo ưu tiên có thể che cảnh báo khác; coverage/unmapped cần báo riêng | giữ danh sách warnings độc lập |
| E15 | S05 HDSD B18–B19, 08_DoiChieu_2Phong G5:I6 | Đối chiếu hai phòng; 1.000 VND là ngưỡng cảnh báo; thiếu KT là chưa có số | không dùng ngưỡng cho duyệt, không biến missing thành zero |
| E16 | S05 HDSD B22 | Năm báo cáo lấy bốn ký tự đầu mã project | phân biệt cohort và accounting period |
| E17 | S03 TU_DIEN B70:E70 | Catalog trộn discipline với design stage | tách work item, stage và event description |
| E18 | S02 trang 1; runtime security hiện có | Responsibility không cấp legal sign; coordinator hiện chỉ đọc; admin có thể bypass kỹ thuật | capability backend, không hardcode tên người |

S04 chứa các pattern revision và acceptance/payment đại diện, nhưng không có hợp đồng ký thật hoặc bằng chứng phê duyệt; không dùng nó để kết luận compliance.

## 3. Ca nghiệm thu giả lập

Các ca dưới đây không phải hàng thật, không chạy Odoo trong BIZ-001 và không dùng giá trị S03 làm fixture. Số tiền giả lập tính theo triệu VND, cùng basis không xét thuế; giả định này chỉ cho phép kiểm logic quản trị, không cấu hình thuế doanh nghiệp.

| Ca | Dữ liệu giả lập | Kết quả mong đợi |
| --- | --- | --- |
| C1 — revision snapshot | Contract A bản gốc 100, phụ lục revision 110 có effective date sau ngày ký | Bản gốc vẫn đọc được; as-of trước hiệu lực là 100; sau hiệu lực là 110; không cộng 100 + 110 |
| C2 — cấp khoán | Allocation cha cấp 1 là 70; hai con cấp 2 là 30 và 45 cùng project | Tổng project là 70; cấp 2 hiển thị riêng; cảnh báo vượt cha; không tạo nghĩa vụ vendor thứ hai |
| C3 — acceptance/cash | Production 100; acceptance 80; invoice 80; cash 72; retention 8; payment request còn pending | Năm record riêng; pending không thành paid; support không nhận 80/72/8; FINANCE nhận để đối chiếu |
| C4 — BASE rejected | Revision review; BASE trả rejected kèm lý do | Không effective; lý do bất biến; revise tạo version mới; caller khác scope bị 403/404 theo policy |
| C5 — null và zero | Một event không có cash; event khác cash xác nhận bằng 0 | API trả null và 0 khác nhau; dashboard không gọi null là zero |
| C6 — sửa hồi tố | Acceptance business_date tháng trước nhưng recorded_at hôm nay | Báo cáo as-of ghi rõ basis; không tự đổi business_date thành hôm nay |

Ba hồ sơ giả lập đại diện được diễn giải để chuyển thành test sau:

1. **Hợp đồng P-A:** hai hạng mục gốc 60 + 40 = 100. Phụ lục chỉ đổi hạng mục 60 thành 70: snapshot mới 70 + 40 = 110, chênh 10. Ngày ký 10/10, hiệu lực 01/11: số tại 31/10 vẫn 100; tại 01/11 là 110 khi đủ bằng chứng. Sửa giảm 70 xuống 50 cho tổng mới 90; đổi về 0 cho tổng mới 40. Không dùng điều kiện giá mới > 0 để bỏ mất thay đổi hợp lệ. Hủy draft phụ lục không làm mất hiệu lực bản gốc.
2. **Giao khoán P-B:** một khoán nội bộ cấp 1 là 70, hai thầu phụ phòng cấp 2 là 30 và 45. Tổng quản trị cấp 1 = 70, tổng con = 75, vượt 5; phần phòng giữ = -5 là cảnh báo, không ép thành 0. Nếu cùng project có thầu phụ công ty cấp 1 thêm 20 thì tổng cấp 1 = 90, không phải 165. Mã/tên đơn vị trùng ở project khác không được liên kết nhầm cha.
3. **Thực hiện P-C:** production 100, acceptance 80, invoice 80, cash 72, retention 8. Chênh production/acceptance = 20; acceptance/cash = 8; acceptance/invoice = 0. Khi retention 8 còn treo đúng điều khoản, phần chênh ngoài retention = 0; chưa thể kết luận hết nghĩa vụ hợp đồng/thuế hoặc đã đến hạn. Sửa cash từ 72 thành 70 làm tổng cash còn 70, không thành 142; void event cash đó đưa đóng góp event về 0, không xóa lịch sử. Với tiền kế toán posted, phải dùng chứng từ đảo phù hợp thay vì xóa event nguồn.

## 4. Ma trận quyền âm

| Tình huống | Kết quả bắt buộc |
| --- | --- |
| SUPPORT đọc detail contract financial | Không có amount/cost/margin/cash/retention trong DTO; download financial attachment bị từ chối |
| PROJECT_OWNER khác project đọc URL đoán được | 403 hoặc 404 nhất quán, không lộ record |
| Người lập gọi record_base_result | Bị từ chối nếu thiếu capability/authority; không đổi state bằng PATCH |
| BASE pending gọi make_effective | Bị từ chối, giữ pending |
| Cấp 2 không có parent hoặc khác company | Constraint/validation fail |
| Retry cùng command key | Idempotent; payload khác bị từ chối |
| Admin break-glass tải file | Có audit riêng; không xem đó là quyền nghiệp vụ thông thường |
| User đọc metadata A, financial.read chỉ ở B | Không xem amount/aggregate/financial file A kể cả qua native RPC hoặc group tài chính chung |
| BASE approved nhưng evidence pending | Không được chốt hiệu lực; giao diện ghi rõ kết quả chưa xác minh |
| Đổi scope/amount sau BASE approved | Approval của version cũ không áp dụng; version mới phải có căn cứ phù hợp |
| Ký hợp đồng nhưng chưa đủ điều kiện hiệu lực | Giữ signed, chưa effective; không suy từ ngày upload |
| BASE reference bị thu hồi sau posted payment | Chặn action mới liên quan, mở xử lý; không auto-đảo/xóa payment |
| Request approved, chưa có payment hoặc chỉ trả một phần | Cash thực tế không đổi hoặc chỉ phản ánh phần đã trả; không tự nhận paid toàn bộ |
| SUPPORT có task chứa link financial file | Từ chối download nếu chưa grant; audit/filename/notification không lộ tiền |
| Thu hồi financial.read khi phiên còn đăng nhập | Request/tải tệp sau thu hồi bị chặn; cache không giữ số của scope cũ |

## 5. Giới hạn và cổng tiếp theo

- Chưa có hồ sơ thật đã khử dữ liệu để xác nhận signatory, bốn mắt, thuế/gross-net, ngày hiệu lực và nghiệp vụ tạm ứng/giữ lại.
- Chưa có feed kế toán thật; S05 không chứng minh đối chiếu đã thành công.
- CTR-001 (`CHG-20261028-006`) đã chuyển phần đọc thành Odoo/API/E2E test với dữ liệu giả lập: C1 và hồ sơ P-A (60 + 40 = 100; phụ lục 70 + 40 = 110; as-of 31/10 là 100, 01/11 là 110, không 210); C5 cho dòng hợp đồng (chưa xác nhận là null, 0 là 0, tổng chưa đủ thì không có giá trị); BASE approved/verified nhưng chưa ký/hiệu lực; kết quả BASE khai báo hiển thị chưa xác minh. Ma trận quyền âm đã có test cho: reader không có grant (không amount trong ORM/`read_group`/export/API, tải tệp financial bị từ chối), URL khác project trả 404, metadata A + financial B, grant hết hạn/thu hồi chặn request sau, tài liệu financial cần grant kể cả khi có link.
- Chưa test vì chưa có action ghi: sửa giảm/về 0 của phụ lục, hủy draft, record/verify BASE, make_effective, idempotency, audit break-glass; C2–C4, C6 và P-B/P-C thuộc CTR-002/ALC/STL.
- Khi thu thập hồ sơ đại diện, ghi source hash, che tên/số tiền nếu đưa vào test, và cập nhật câu hỏi Q1–Q8 trong workflow chính.

Lượt CHG-20261028-013 kiểm lại năm hash **bản sao cục bộ** và inventory tài liệu được cung cấp; chưa nhận thêm bundle hợp đồng thực tế khử dữ liệu đủ chuỗi, không xác nhận hash trực tiếp trên NAS trong lượt này. [Readiness 7.1.2](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#712-inventory-hồ-sơ-còn-cần-và-ba-bundle-mô-phỏng-sim-p1) giữ danh sách hồ sơ còn cần, ba walkthrough SIM-P1 có từng chặng/guard/evidence/gap và nhật ký riêng. Không đưa hồ sơ thật/hash giả vào các ca mô phỏng, không nhận SIM-P1 là nghiệm thu hoặc test action.

