# Hướng dẫn trình bày nghiệp vụ KH-KD trên Odoo

Ngày soạn 06/11/2026. Đây là kịch bản mục tiêu để dùng sau khi phiên thực thi hoàn thành và cung cấp menu, mã hồ sơ cùng kết quả test thật. Hiện không coi các màn hình dự kiến dưới đây là đã được triển khai.

## Mục tiêu của buổi trình bày

Cho lãnh đạo thấy phòng KH-KD tiếp nhận và quản lý một dự án như thế nào; ai làm, bàn giao cho ai, hồ sơ nào còn thiếu và số liệu nào cần theo dõi. Dùng một dự án chính xuyên suốt để người xem không phải tự nối dữ liệu từ nhiều ứng dụng.

Lời mở đầu đề xuất:

> Em xin trình bày cách tổ chức nghiệp vụ phòng Kế hoạch Kinh doanh trên TANPHAT ONE. Em dùng một bộ hồ sơ minh họa để đi từ cơ hội đến hợp đồng, kế hoạch thực hiện, nghiệm thu và hồ sơ thanh toán. Trong mỗi bước, em sẽ chỉ ra người phụ trách, hồ sơ đầu ra và việc cần phối hợp với phòng chuyên môn hoặc QT-TC. Phần đang trình bày là để thống nhất cách làm trước khi sử dụng dữ liệu thực tế.

## Trước buổi họp

1. Mở http://127.0.0.1:18069/odoo; dùng tài khoản hiện có đã được phiên thực thi kiểm tra. Không đoán tài khoản hoặc đổi mật khẩu trước buổi họp.
2. Đọc docs/demo/KD_NATIVE_001_PRESENTATION.md sau khi file được thực thi tạo ra: chọn đúng dự án chính, hợp đồng cần trả lại và hồ sơ cần cảnh báo. Chưa có file này thì chưa có căn cứ kết luận đã sẵn sàng trình diễn.
3. Chuẩn bị hai phiên trình duyệt riêng cho người lập và reviewer; dùng hai browser profile hoặc một cửa sổ thường và một cửa sổ riêng tư. Không đổi user trong cùng session rồi để tab cũ thao tác nhầm.
4. Chọn đúng kỳ/bộ lọc, kiểm ngày/hạn và chạy thử luồng nháp một lần. Không thử ghi đè bản hồ sơ đã gửi hoặc sửa số liệu cũ để làm đẹp báo cáo.
5. Dùng record riêng cho thao tác trực tiếp. Nếu muốn trở về tình trạng đầu, tạo bộ hồ sơ nháp mới theo quy trình, không xóa lịch sử hoặc khôi phục đè toàn database.

## Thứ tự trình bày trong 12 đến 15 phút

| Thời gian | Màn hình mục tiêu | Thao tác và điều cần chứng minh | Lời dẫn gợi ý |
| --- | --- | --- | --- |
| 1 phút | Home → Kế hoạch Kinh doanh → Tổng quan | Chỉ số công việc/hồ sơ; chọn một dự án và mở nguồn. | Phòng có một nơi để biết việc nào cần xử lý và ai đang phụ trách. Mỗi con số đều mở được hồ sơ phía sau. |
| 1 phút | CRM → cơ hội | Mở khách hàng, nguồn cơ hội, người theo dõi, hạn dự thầu và dự án liên kết. | KH-KD tiếp nhận cơ hội, đánh giá và chuẩn bị hồ sơ. Dự án giao trực tiếp có thể không qua thầu. |
| 1 phút | TP Projects → dự án chính | Mã dự án, khách hàng, chủ trì, phòng phối hợp và các hồ sơ liên quan. | Đây là hồ sơ trung tâm; hợp đồng, công việc và các đợt thực hiện cùng gắn vào một dự án. |
| 3 phút | TP Contracts → nháp → gửi → trả lại → mở bản sửa → gửi lại | Dùng người lập và reviewer; nhập lý do trả lại; chỉ lịch sử và bản sửa. | Rà soát có người chịu trách nhiệm, lý do và lịch sử. Bản đã gửi được giữ để đối chiếu; sửa theo một bản tiếp theo. Rà soát chưa phải phê duyệt BASE hoặc ký. |
| 1 đến 2 phút | Kế hoạch và công việc | Mở WBS, mốc, phòng nhận, owner, hạn và đầu ra. | Việc lớn được chia thành đầu việc có người chịu trách nhiệm và kết quả bàn giao. Phòng chuyên môn thực hiện kỹ thuật; KH-KD theo dõi và điều phối. |
| 1 phút | Giao khoán và thầu phụ | Khoán nội bộ, khoán cấp 1/cấp 2 và phạm vi liên quan. | Khoán con giải thích cách phân bổ của khoán cha; tổng công ty không cộng cả hai để tránh tính trùng. |
| 1 đến 2 phút | Sản lượng → nghiệm thu | Mở một kỳ và một đợt; chỉ phần thực hiện khác phần được nghiệm thu. | Đã làm xong công việc chưa có nghĩa đã có biên bản nghiệm thu. Mỗi đợt cần phạm vi và căn cứ riêng. |
| 1 đến 2 phút | Đề nghị thanh toán → đối chiếu → tổng hợp | Mở request; chỉ liên kết hóa đơn và tình trạng nguồn tiền; quay về dashboard. | Số tiền đề nghị, hóa đơn và tiền đã thu là những thông tin riêng. Nếu chưa có chứng từ ghi sổ thì báo cáo ghi rõ, không coi đề nghị là tiền đã nhận. |
| 1 phút | Kế hoạch định kỳ → năng lực/chứng chỉ → việc cần xử lý | Một mục tiêu tháng, một chứng chỉ sắp hết hạn và một hồ sơ thiếu. | Ngoài từng dự án, KH-KD còn theo dõi kế hoạch sản lượng/doanh thu, năng lực và công việc thương hiệu được giao. |

Nếu một công đoạn mới chỉ có hồ sơ hoặc màn hình đọc, nói rõ như vậy. Chỉ bấm nút sau khi runbook thực thi xác nhận đã test bằng actor tương ứng. Không nói đã thay BASE, đã có hiệu lực hoặc đã thanh toán chỉ vì nhìn thấy một trạng thái.

## Cách giải thích các con số

Ví dụ thuần minh họa, cùng đơn vị triệu đồng và cùng cơ sở thuế: giá trị hợp đồng 1.000; đã thực hiện 400; đã nghiệm thu 350; hóa đơn đã phát hành hợp lệ 300; thực thu có căn cứ 250.

- 50 giữa thực hiện và nghiệm thu là phần cần tiếp tục hoàn thiện/xác nhận nghiệm thu.
- 50 giữa nghiệm thu và hóa đơn là phần cần kiểm tra điều kiện lập hóa đơn.
- 50 giữa hóa đơn và thực thu cần đối chiếu hạn, tạm ứng, giữ lại và chứng từ; không tự gọi tất cả là nợ quá hạn.
- Các chênh lệch này không phải lợi nhuận. Giá trị hợp đồng dự thảo không đưa vào tổng hợp đồng có hiệu lực.

Đây là ví dụ để giải thích khái niệm, không phải số liệu đã kiểm trên database18069. Khi trình bày màn hình thật, dùng số và nguồn mà runbook bàn giao đã xác nhận.

## Lời kết và đề nghị lãnh đạo xác nhận

> Em đề xuất dùng dự án làm trục liên kết hồ sơ. KH-KD theo dõi cơ hội, hợp đồng và kế hoạch; các phòng chuyên môn cập nhật kết quả và bàn giao; QT-TC đối chiếu hóa đơn, thu chi. Nhờ vậy lãnh đạo có thể xem tiến độ, tình trạng hồ sơ và nghĩa vụ còn tồn theo từng dự án. Em xin ý kiến về người chịu trách nhiệm từng bước, hồ sơ bắt buộc và các điểm cần ưu tiên trước khi đưa dữ liệu thực tế vào sử dụng.

Các nội dung cần chốt: người lập/rà soát/ghi nhận và xác minh kết quả BASE; thẩm quyền ký/duyệt theo văn bản; người quyết định cấp/thu hồi quyền xem tiền; checklist hồ sơ từng đợt; cơ sở thuế/nguồn kế toán; cách xử lý vượt khoán, giữ lại và sửa sai sau chốt.

## Câu hỏi thường gặp

**Sao phải có cả Project và TP Projects?** Cùng model và dữ liệu dự án. TP Projects là phần tổ chức/mở rộng hồ sơ theo nghiệp vụ Tấn Phát, không phải nhập dự án lần hai.

**KH-KD có làm thay phòng kỹ thuật và kế toán không?** KH-KD chủ trì hồ sơ và điều phối; phòng chuyên môn chịu trách nhiệm thực hiện/kiểm tra kỹ thuật; QT-TC/kế toán phụ trách nghiệp vụ tài chính và hạch toán theo phân công.

**Có thay BASE ngay không?** Chưa. BASE vẫn là nơi phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận tham chiếu/kết quả khi có quy trình đủ căn cứ. Không tuyên bố có đồng bộ BASE nếu chưa triển khai, kiểm chứng.

**Đã sử dụng chính thức được chưa?** Buổi này nhằm kiểm tra luồng và lấy ý kiến. Chỉ những chức năng có test và bàn giao mới được xác nhận đã chạy trên dev; vận hành thật cần owner, quyền, hồ sơ và nghiệm thu riêng.

**Vì sao chưa hiện tiền thực thu?** Chưa có nguồn kế toán/đối chiếu hợp lệ thì hệ thống ghi rõ còn thiếu. Hóa đơn nháp và hồ sơ đề nghị không chứng minh đã thu tiền.

## Căn cứ và giới hạn

Nội dung nghiệp vụ được tổng hợp từ Quy trinh nghiep vu TanPhat JSC_V1.0.docx, T4.2026-Phân công nhiệm vụ Ban Kinh doanh.pdf, các biểu mẫu PKH/DA Temp/Master và bộ phân tích KH-KD/BIZ-002 trong repository. Cần chốt bản biểu mẫu đang sử dụng trước khi nhập dữ liệu thật. Phân công công việc không tự tạo quyền ký, quyền xem tiền hoặc phê duyệt chính thức.
