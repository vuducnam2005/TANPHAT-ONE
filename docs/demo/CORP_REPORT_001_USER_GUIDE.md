# Trung tâm Báo cáo — hướng dẫn dùng trên web

Ngày16/11/2026 · CORP-REPORT-001 · test18079. Đây là hướng dẫn theo source đã triển khai, không phải biên bản nghiệm thu. Main18069 chưa được giao áp module. Lịch, người rà/chốt và danh mục đánh giá ở test là cấu hình thử, chưa là quy chế công ty.

Mở [TANPHAT ONE test](http://127.0.0.1:18079/odoo), đăng nhập bằng tài khoản giả được bàn giao qua file private `.local/corp-report001/credentials.json`, chọn thẻ **Báo cáo** ở Home. Không ghi password vào tài liệu Git hoặc dùng tài khoản thật để thử luồng. Menu, dữ liệu và nút xuất hiện theo quyền đã cấp; không có menu không có nghĩa được phép mở link ngoài phạm vi.

## Nhân viên làm trọn một kỳ

1. **Báo cáo của tôi → Nghĩa vụ / Lập báo cáo**. Mở nghĩa vụ đúng tuần/ngày; kiểm người phụ trách, phòng, hạn nộp và gia hạn/miễn nếu có. Bấm **Lập báo cáo**. Có thể tạo nháp trực tiếp khi được yêu cầu; không cần upload Excel.
2. Nhập tên dễ hiểu và khoảng ngày rõ; tuần dùng lịch T2–CN mặc định kỹ thuật, tháng/quý đúng ngày đầu/cuối kỳ. Chọn **Người nhận / rà soát** đã được phân công hiệu lực. Nhân viên chỉ phải lập tháng/quý khi được yêu cầu, không tự nhân ba bộ nghĩa vụ.
3. Lưu nháp rồi bấm **Đưa kế hoạch vào báo cáo** để lấy các kế hoạch tuần đã ban hành của chính mình trong kỳ. Không tạo task trùng. Mỗi dòng giữ kế hoạch nguồn và mã đầu ra để chống cộng trùng khi tổng hợp.
4. Mở một dòng trong **Kết quả và công việc**. Đọc **Đầu ra dự kiến**, nhập **Kết quả thực tế**, trạng thái công việc, vướng mắc/khắc phục và minh chứng. Hạn công việc khác hạn nộp báo cáo. Khi có số lượng thực hiện, bật **Đã có số thực hiện** rồi nhập số; chưa có nguồn giữ chưa biết, số0 đã biết vẫn là0. Không tự đổi mô tả thành phần trăm.
5. Nếu có việc phát sinh, thêm dòng mới với nội dung, ngày, mã đầu ra nguồn, kết quả và nguyên nhân. Không sửa ngầm mục tiêu cha đã ban hành. Điền kết quả nổi bật, vướng mắc, kiến nghị và kỳ tới.
6. **Lưu** bằng điều khiển native. Nếu có lỗi, đọc thông báo và giữ nội dung đang sửa; không bấm gửi nhiều lần. **Quay lại** giữ danh sách/lọc/trang trước; native hỏi khi còn thay đổi chưa lưu.
7. Bấm **Xem trước** để đọc bản nháp ngay trên web, đóng rồi sửa nếu cần. Bấm **Gửi báo cáo** khi nội dung đủ. Thiếu người rà hợp lệ bị chặn có hướng dẫn cấu hình; chỉ xem thành công khi trạng thái đã gửi và có phiên bản trong **Phiên bản**.
8. Mở **Nhận xét và phản hồi** để đọc nhận xét công bố và dòng cần bổ sung. Bấm **Thêm nhận xét / phản hồi**, chọn **Nhận xét cha**, viết trả lời mới. Không sửa đè đánh giá/actor hoặc nội dung quản lý đã viết.
9. Khi **Trả lại**, đọc lý do và nhận xét ở đúng đầu việc, sửa nội dung nháp rồi gửi lại. Snapshot đã gửi trước vẫn tồn tại. **So sánh phiên bản** đối chiếu các bản được quyền xem; không lấy số hiện hành thay số lịch sử.
10. Report **Đã chốt** vẫn có thể chứa việc **Đang làm**. Sang kỳ sau giữ liên kết cùng task/nguồn và phạm vi đóng góp, không sao chép số actual cũ để tăng tổng. Chỉ đạo nhận riêng nằm ở **Việc cần xử lý**.

## Cấp trên rà và trao đổi

1. Từ danh sách báo cáo chọn **Chờ tôi rà soát**. Inbox chỉ lấy bản reviewer được phân công trong trạng thái đã gửi/đang rà. Không dùng quyền quản lý để sửa nháp riêng của nhân viên.
2. Mở báo cáo, kiểm người/phòng/kỳ/phiên bản và **Bắt đầu rà**. Đọc đầu ra kế hoạch và actual từng dòng, minh chứng, nguyên nhân và kiến nghị.
3. Trong **Nhận xét và phản hồi**, bấm **Thêm nhận xét / phản hồi**. Chọn đầu việc để nhận xét riêng, hoặc để trống cho ý kiến chung; chọn Đáp ứng/Cần bổ sung/Ý kiến theo danh mục thử. **Công bố cho tác giả** cho nhân viên đọc/phản hồi; **Nội bộ người rà** có audience hạn chế. Không coi đánh giá thử là điểm HR/lương thưởng.
4. Bấm **Yêu cầu sửa**, nhập lý do bắt buộc trong popup, xác nhận. Khi cần sửa một dòng, ghi nhận xét **Cần bổ sung** đúng dòng. Không thay actual của nhân viên. Sau khi tác giả gửi lại, mở phiên bản/so sánh để kiểm thay đổi.
5. Chốt bằng capability được cấp khi đủ điều kiện. Không tự rà/chốt báo cáo cá nhân của mình. Bản chốt giữ snapshot và dependency; nguồn đổi sau đó không tự ghi lại lịch sử.
6. Muốn sửa nhận xét đã công bố, tạo **Đính chính nhận xét** mới trỏ bản cũ; muốn phản hồi dùng **Nhận xét cha**. Không xóa/rewrite lịch sử.

## Mục tiêu quý, tháng và tuần

Vào **Mục tiêu và kế hoạch**, lập mục tiêu quý có owner, phòng/company, ngày, chỉ tiêu/đơn vị hoặc đầu ra định tính. Trình → người có quyền ban hành. **Lập kế hoạch tháng** giữ cha quý; nhập phân bổ thật, không tự chia đều. Từ tháng **Giao việc tuần**, chọn người làm, hạn và nguồn task hiện có. Kiểm **Đã phân bổ / Chưa phân bổ**, hệ thống chặn sai kỳ/cha/đơn vị/vượt mục tiêu khi ban hành. **Mốc ban đầu và điều chỉnh** so số đã ban hành với hiện hành. Điều chỉnh có lý do và phiên bản; không sửa ngầm baseline.

## Phòng ban và công ty

Người có assignment mở **Báo cáo phòng ban** hoặc **Báo cáo công ty**; tạo đúng cấp/kỳ, chọn mẫu, dùng **Tổng hợp bản nguồn**. Kiểm phần bao phủ/nghĩa vụ, dependency và phiên bản nguồn; việc không đủ/nguồn trùng không được tự coi là đủ. Phòng tổng hợp cá nhân, công ty tổng hợp đúng bản phòng đã chốt. Nhập phần giải thích/kiến nghị của cấp đó, không sửa bản con thay tác giả. Thiếu bao phủ cần đúng capability và lý do, không giả lập đủ người nộp.

Finance là vùng quyền riêng: mở chỉ tiêu có nguồn chỉ khi có capability; ghi định nghĩa, đơn vị, cơ sở thuế, nguồn/ngày/người cung cấp và phạm vi chống trùng. Missing/ước lượng/chờ xác nhận khác confirmed và khác số0. Người xác nhận đúng quyền kiểm nguồn; không tự biến đề nghị thanh toán thành doanh thu/tiền thực nhận.

## Chỉ đạo, lịch và xuất

**Việc cần xử lý** theo dõi owner, hạn, trạng thái và report nguồn. Người nhận bấm Bắt đầu rồi Hoàn thành; người có quyền chỉ đạo có thể tạo task trong dự án được phép hoặc theo dõi ngay tại đây. Không đổi workflow nguồn khác.

**Mẫu và lịch** dành cho người cấu hình: mẫu/sections, lịch/ngày/múi giờ/đối tượng, assignment theo company/phòng/cấp/người và hiệu lực. Tạo nghĩa vụ theo lịch có chủ đích. Nhắc trong ứng dụng chỉ bật trong scope/lịch được phép; không gửi email/chat người thật. Không suy quyền từ tên/chức danh trong Excel.

Danh sách dùng tìm kiếm native, **Lọc theo → Áp dụng**, Xóa lọc, Bộ lọc nâng cao và favorite. Chưa Áp dụng thì bảng/chart/export vẫn theo điều kiện cũ. Clear không xóa phạm vi cố định. Chọn10/20/50/100 dòng; mở detail rồi Quay lại để giữ lọc/trang. Bảng con có nút Lọc/tìm toàn bộ để truy vấn toàn tập đúng cha.

Excel trên danh sách xuất toàn bộ **bộ lọc đã áp**, không chỉ trang đang xem. Report detail xuất Excel/Word/PDF trong quyền, nháp có nhãn Nháp. Muốn bản lịch sử: mở **Phiên bản**, chọn snapshot rồi dùng **Excel/Word/PDF bản này**. Tệp chứa đúng snapshot/audience, không phải ảnh chụp dashboard. Kiểm quyền vẫn áp khi tải; không chia sẻ URL file như public link.

## Khi gặp lỗi và cổng còn lại

- Báo bản đã thay đổi: giữ nội dung cần thiết riêng, tải lại và đối chiếu phiên bản mới; không dùng retry để ghi đè người khác.
- Thiếu người nhận: nhờ người cấu hình assignment review đúng company/phòng/cấp/người/hiệu lực. Không tự cấp quyền cho mình.
- Không có nguồn: bổ sung source hoặc để thiếu; không nhập0 cho đẹp biểu đồ.
- Hết phiên: đăng nhập lại bằng native login, đọc lại bản hiện hành trước khi thao tác.

Bằng chứng/test thật ghi ở [acceptance](CORP_REPORT_001_ACCEPTANCE.md), ảnh private `.local/corp-report001/ui/`. Tại lúc viết hướng dẫn chưa xác nhận browser flow đầy đủ; hướng dẫn không phải PASS, nghiệm thu nghiệp vụ hay cho phép pilot/main. Chỉ test bằng fixture; không nhập lịch sử Excel thật/đổi grant người thật, không commit/push.
