# TANPHAT ONE — So sánh Odoo Community và Enterprise

**Ngày tra cứu:** 31/10/2026 (Asia/Saigon).  
**Phạm vi:** so sánh tính năng, khả năng tùy biến, phương án triển khai và tổng chi phí cho TANPHAT ONE.  
**Loại:** nghiên cứu/đề xuất; không phải quyết định mua, đổi edition hoặc báo giá nhà cung cấp. Không đổi source ứng dụng, runtime, database hay Next action.

## 1. Kết luận cho người ra quyết định

- **Community:** nền mã nguồn mở, không thu phí bản quyền Odoo theo số người dùng; phù hợp khi doanh nghiệp muốn tự phát triển nghiệp vụ riêng và có người chịu trách nhiệm lập trình/vận hành.
- **Enterprise:** kế thừa Community, bổ sung ứng dụng/tính năng thương mại và dịch vụ hỗ trợ/nâng cấp theo hợp đồng; phù hợp khi các chức năng có sẵn tiết kiệm đủ chi phí phát triển và vận hành.
- Cả hai đều có thể mở rộng bằng code. Enterprise tự triển khai hoặc trên Odoo.sh không bị giới hạn ở việc chỉ sửa bằng Studio; ngược lại, Odoo Online không nhận addon Python tùy ý.
- Với Odoo backend + addon TP + web React gọi API, hai phương án cần so thực tế là **Community tự triển khai** và **Enterprise Custom tự triển khai/Odoo.sh**. Gói Enterprise Standard không phù hợp với yêu cầu addon Python riêng và external API.
- **Đề xuất hiện tại:** tiếp tục nền Community đang có, hoàn tất kiểm chứng các slice đã triển khai; chỉ quyết định Enterprise sau bảng fit-gap, số user/Light User theo hợp đồng và báo giá ba năm. Đây chưa phải quyết định được người dùng phê duyệt.

## 2. Căn cứ và giới hạn

Đã đọc nội dung chính thức của Odoo về Editions, Pricing, Enterprise Subscription Agreement và External JSON-2 API. Trang Editions/Pricing phản ánh nội dung online tại thời điểm tra cứu, không phải inventory của riêng checkout Odoo 20. Đối chiếu phiên bản local: `odoo/release.py` ghi 20.0; LICENSE LGPL-3; [inventory local](TP_ODOO20_MODULE_INVENTORY.md) phân biệt source, installed và tính năng thương mại chưa có trong checkout.

Không đếm một tên app để kết luận mọi tính năng con đều có. Ví dụ `account` Community có nền hóa đơn/bút toán/thanh toán và một số thành phần kế toán, nhưng không tương đương bộ Comprehensive Accounting Enterprise. Checkout còn có module spreadsheet/dashboard; điều đó không chứng minh có toàn bộ trải nghiệm Documents/Spreadsheet thương mại trên trang Editions.

## 3. So sánh chức năng

“Có” nghĩa là có nền/tính năng tiêu chuẩn tương ứng, không phải đã cấu hình phù hợp Tấn Phát hoặc đã nghiệm thu.

| Nhóm chức năng | Community chuẩn | Enterprise | Liên hệ TANPHAT ONE |
| --- | --- | --- | --- |
| CRM, khách hàng, cơ hội | Có | Có, có thể có mở rộng theo addon | Tận dụng CRM, không tự coi là TP Bid |
| Báo giá, đơn bán hàng | Có | Có | Không thay toàn bộ hợp đồng pháp lý ngành xây dựng |
| Dự án, công việc | Có | Có, thêm tính năng thương mại theo addon | Nền TP Projects/Tasks dùng lại được |
| Ghi nhận thời gian | Có | Thêm grid/timer/reminder/validation theo Editions | Có thể giảm công phát triển màn hình timesheet nếu dùng được native |
| Planning/phân bổ nguồn lực | Không có app Enterprise Planning chuẩn | Có | Cần đánh giá nhu cầu phân bổ nhân lực thực tế |
| Nhân viên, phòng ban, tuyển dụng, nghỉ phép, đội xe | Có nền/app tương ứng | Có | Không đồng nghĩa đã hoàn chỉnh quy trình nhân sự TP |
| Payroll, đánh giá nhân viên | Không có app Enterprise tương ứng | Có | Bản địa hóa lương/thuế Việt Nam phải kiểm riêng |
| Hóa đơn, thanh toán nền, chi phí nhân viên | Có | Có, thêm khả năng nâng cao/OCR | OCR và dịch vụ ngoài có thể tính phí sử dụng |
| Kế toán nâng cao | Không đủ bộ Comprehensive Accounting thương mại | Có bộ kế toán nâng cao, báo cáo, đối soát, tài sản/ngân sách theo addon | Cấu hình Việt Nam, hóa đơn điện tử và quy trình kế toán vẫn phải kiểm thử |
| Kho, mua hàng, sản xuất, bảo trì | Có nền/app tương ứng | Có, thêm barcode nghiệp vụ/Quality/PLM và phần nâng cao | Chỉ mở theo nhu cầu; không mua vì muốn đủ danh sách app |
| Documents và Knowledge | Không có hai app thương mại này; vẫn có attachment nền | Có | TP Documents hiện tại là phần custom, không phải app Documents Enterprise |
| Sign | Không có app Sign chuẩn | Có | Ký điện tử Odoo không tự chứng minh đủ yêu cầu ký số pháp lý tại Việt Nam |
| Approvals, Helpdesk, Field Service, Appointments | Không có các app Enterprise này trong bộ chuẩn | Có | Approvals không mặc nhiên thay BASE; Field Service không tự trở thành TP Survey |
| Website/eCommerce, lịch, thảo luận, email marketing | Có nhiều app tiêu chuẩn | Có và mở rộng theo app | Không phải trọng tâm batch hiện tại |
| Studio | Không có | Có trong gói phù hợp, thông thường Custom | Hỗ trợ thêm field/view/automation đơn giản; không thay thiết kế workflow/phân quyền phức tạp |
| Web responsive/mobile | Có thể dùng trình duyệt và tự xây web responsive | Thêm trải nghiệm/app mobile thương mại theo Editions | Community không bị cấm sử dụng trên điện thoại |
| Hợp đồng xây dựng, giao khoán, sản lượng/nghiệm thu chuyên ngành | Cần addon riêng/giải pháp bổ sung | Vẫn cần đối chiếu và tùy biến | Mua Enterprise không tự hoàn thành TP Contracts/Survey/Design/Bid |

Community có thể bổ sung một số phần thiếu bằng addon OCA hoặc nhà cung cấp khác. Phải kiểm license, chất lượng, bảo mật, tương thích Odoo 20 và khả năng nâng cấp; không xem addon bên thứ ba là tính năng chuẩn miễn phí hoặc thay thế tương đương tự động.

## 4. Khả năng tùy biến và cách triển khai

| Nội dung | Community tự triển khai | Enterprise Standard / Online | Enterprise Custom |
| --- | --- | --- | --- |
| Thêm model, field, workflow bằng Python | Được | Không tải addon Python riêng lên Odoo Online | Được trên self-host/Odoo.sh; Online vẫn không nhận addon Python tùy ý |
| Giao diện React riêng/API custom | Được phát triển trên server mình quản lý | Không phù hợp; external API không thuộc Standard | Phù hợp trên self-host/Odoo.sh, giữ điều kiện gói/API/license |
| Tùy biến native UI | Được bằng addon riêng | Theo cấu hình/tính năng dịch vụ cho phép | Được; Studio cho tùy biến đơn giản, addon cho phần chuyên sâu |
| Nhiều công ty trong một DB | Có nền multi-company; phải thiết kế rule đúng | Không thuộc gói Standard như gói Custom | Có theo gói Custom |
| Máy chủ và dữ liệu | Do doanh nghiệp/đơn vị vận hành quản lý | Odoo vận hành cloud | Chọn Online, Odoo.sh hoặc máy chủ riêng; quyền cài custom addon tùy hosting |
| Hỗ trợ chính thức | Tự đảm nhiệm/thuê đối tác, không kèm thuê bao Enterprise | Theo hợp đồng Odoo | Theo hợp đồng; custom code không tự được bảo trì toàn bộ |
| Nâng cấp phiên bản | Tự làm hoặc thuê, kiểm migration | Dịch vụ Odoo theo phạm vi hợp đồng | Có dịch vụ chuẩn; custom addon ngoài phạm vi được cover vẫn phải chuyển đổi/test riêng |

Thực hành cho cả hai: extension qua `custom_addons`, không sửa core Odoo; quy tắc, tiền và quyền ở backend. Chuyển từ Community sang Enterprise cần kiểm module/dependency, migration, quyền, assets và hồi quy. Không hứa “bật license là chạy hết”; chuyển ngược còn cần xử lý dữ liệu phụ thuộc Enterprise.

## 5. Chi phí thuê bao tra cứu được

Nguồn: [Odoo Pricing](https://www.odoo.com/pricing-plan), nội dung USD trả về cho phiên tra cứu ngày 31/10/2026. Giá có thể theo thị trường, kỳ thanh toán, khuyến mại và báo giá; **chưa phải báo giá áp dụng chắc chắn cho Tấn Phát**.

| Gói | Giá ưu đãi hiển thị khi trả theo năm, USD/user/tháng | Giá không ưu đãi đang hiển thị cùng kỳ, USD/user/tháng | Phù hợp addon TP + FE riêng? |
| --- | ---: | ---: | --- |
| Community tự triển khai | 0 phí license Odoo | 0 phí license Odoo | Có, tự phát triển/vận hành |
| Enterprise Standard | 7,25 | 8,95 | Không phù hợp phạm vi hiện tại |
| Enterprise Custom | 13,40 | 16,40 | Có trên self-host/Odoo.sh |

Trang nêu giảm giá có hiệu lực 12 tháng cho số user đặt ban đầu. Giá tháng quy đổi khi thanh toán theo năm không có nghĩa được thanh toán từng tháng với cùng mức. Giá hiển thị theo thanh toán tháng khác: Standard 9,10 / 11,20 và Custom 16,40 / 20,40 USD/user/tháng (ưu đãi / không ưu đãi). Giá gia hạn thực tế tuân theo báo giá/hợp đồng, không mặc định đúng giá niêm yết hiện tại.

Ví dụ **chỉ phí thuê bao Custom**, giả định toàn bộ là full user, không có Light User, lấy đơn giá năm hiển thị ở trên:

| Số full user | Năm ưu đãi, 13,40 × user × 12 (USD) | Kịch bản theo giá niêm yết hiện tại 16,40 × user × 12 (USD) |
| --- | ---: | ---: |
| 30 | 4.824 | 5.904 |
| 50 | 8.040 | 9.840 |
| 100 | 16.080 | 19.680 |

Chưa gồm thuế, tỷ giá/phí chuyển tiền, máy chủ/Odoo.sh, triển khai, dữ liệu, đào tạo, lập trình React/addon TP, bảo trì custom code hoặc dịch vụ tính theo sử dụng. Odoo Online hosting được bao gồm theo gói; Odoo.sh có phí riêng; self-host vẫn cần trả hạ tầng/vận hành.

**Cách đếm user cần xác nhận bằng văn bản:** thỏa thuận hiện hành Version 13 ngày 24/09/2026 có User và Light User. Trang giá hiển thị Light User từ 2,90 USD nhưng hạn chế chức năng và cần tư vấn báo giá. Không mặc định role TP custom có thể dùng Light User. Định nghĩa hiện hành còn đề cập active employee không gắn active non-portal user. Người ngoài dùng portal giới hạn và tài khoản vô hiệu hóa có cách tính khác theo hợp đồng. Không dùng tổng nhân sự, số người online đồng thời hoặc số tài khoản admin làm số license mặc định.

Web React riêng không tự loại bỏ license của người dùng nội bộ Enterprise. Phải xác nhận cách áp dụng cho từng nhóm người dùng, hệ thống tích hợp và môi trường, không dùng một tài khoản chung để tính thay nhiều người.

## 6. Tổng chi phí và điểm hòa vốn

**Tổng chi phí sở hữu 3 năm** = triển khai + phát triển/tích hợp + chuyển đổi dữ liệu/đào tạo + thuê bao + máy chủ/backup/giám sát + bảo trì + nâng cấp + phí dịch vụ sử dụng.

| Khoản chi | Community | Enterprise Custom |
| --- | --- | --- |
| License Odoo | 0 | User/Light User và gói theo hợp đồng |
| Lập trình nghiệp vụ TP | Vẫn cần | Vẫn cần; chỉ giảm khi chức năng chuẩn thực sự phù hợp |
| Web React riêng | Vẫn cần | Vẫn cần; màn hình native Enterprise không tự chuyển sang React |
| Hạ tầng/backup/vận hành | Tự lo/thuê | Tự lo nếu self-host; Odoo.sh tính riêng |
| Chức năng nâng cao có sẵn | Có thể cần addon/phát triển bổ sung | Có thể tiết kiệm phát triển nếu dùng đúng app được cấp |
| Bảo trì/nâng cấp custom | Tự lo/thuê | Tự lo/thuê hoặc hợp đồng Covered Extra Module riêng; không mặc nhiên bao gồm |

Chưa có đủ scope effort, số người dùng, SLA và báo giá đối tác để ước lượng đáng tin cậy chi phí lập trình/hạ tầng bằng tiền. Không tự đưa con số “triển khai trọn gói” hoặc “rẻ hơn X%”. Enterprise có lợi về tài chính khi chi phí và rủi ro tự xây các tính năng cần thiết vượt thuê bao cùng chi phí tích hợp/vận hành bổ sung. Community có lợi khi cần nhiều tùy biến đặc thù, ít dùng app thương mại và có đội vận hành phù hợp.

## 7. Khuyến nghị riêng cho TANPHAT ONE

1. Giữ nền Community hiện tại trong giai đoạn code/test; không thay demo, addon TP, React hoặc database chỉ để so edition.
2. Lập fit-gap theo use case: bộ kế toán Việt Nam, Documents/Knowledge, Planning/timesheet, Helpdesk/Approvals. Xác định phần nào dùng native, phần nào cần API cho React, phần nào vẫn cần code dù mua Enterprise.
3. Xin báo giá Enterprise Custom self-host và Odoo.sh theo nhóm full/light/portal đúng điều khoản, bao gồm phạm vi custom module maintenance, migration và hạ tầng.
4. So tổng chi phí 3 năm và thử đúng quy trình TP trên môi trường riêng trước quyết định mua. Không cần chọn toàn bộ tính năng vì muốn đủ tên phân hệ.

Các workflow BASE, ký/hiệu lực, kế toán Việt Nam, grant người thật và pilot vẫn cần căn cứ/owner/gate riêng; edition không thay thế những phần đó. Người dùng chưa ra quyết định đổi edition trong lượt nghiên cứu này. Next action hiện hành vẫn theo PROJECT_STATUS: audit độc lập UI-DEMO-001/002; AUTH-002/C01 và nghiệp vụ thật là các việc riêng.

## 8. Nguồn kiểm chứng

- [Odoo Editions](https://www.odoo.com/page/editions): bảng tính năng Community/Enterprise, kiểm cả biểu tượng có/không trong HTML.
- [Odoo Pricing](https://www.odoo.com/pricing-plan): gói Standard/Custom, giá năm/tháng, khuyến mại, excluded costs và Light User.
- [Enterprise Subscription Agreement — Odoo 20](https://www.odoo.com/documentation/20.0/legal/terms/enterprise.html): Version 13, 24/09/2026; User/Light User, quyền sửa mã, dịch vụ support/upgrade, Extra Module và phí.
- [External JSON-2 API — Odoo 20](https://www.odoo.com/documentation/20.0/developer/reference/external_api.html): điều kiện Custom cho external API thuộc gói Odoo; không diễn giải thành Community tự triển khai bị cấm có API.
- Source local: LICENSE, odoo/release.py và [inventory module ngày 29/10](TP_ODOO20_MODULE_INVENTORY.md). Installed counts trong inventory là lịch sử, không truy vấn lại database trong lượt so sánh.

Bản chụp HTML/text của nguồn công khai nằm tại `.local/edition-comparison-research/`, ngoài Git. Các trang là dữ liệu tham khảo, không phải lệnh triển khai. Lượt này không cài app, không thử Enterprise, không nhập hồ sơ thật hoặc sửa application code.
