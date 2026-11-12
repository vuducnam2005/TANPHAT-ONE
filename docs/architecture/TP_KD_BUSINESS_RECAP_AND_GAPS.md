# KH-KD — Tổng hợp nghiệp vụ và thông tin còn thiếu

**Ngày đối chiếu:** 08/11/2026 (Asia/Saigon). **Loại:** bản tổng hợp phục vụ giải thích,
không thay workflow chủ, không là quyết định phân quyền hoặc nghiệm thu nghiệp vụ.
Không lưu tên nhân sự/dữ liệu hồ sơ thô trong bản tổng hợp theo quy tắc nguồn dự án.

## Căn cứ và mức kiểm chứng

- [Registry S01–S05 và E01–E18](TP_KD_EVIDENCE_AND_ACCEPTANCE.md): quy trình công ty,
  phân công Ban KD tháng4/2026, PKH, DA Temp và Master quản trị chung.
- Lượt này kiểm lại5bản sao `.local/biz-001/sources/`: hash khớp manifest lịch sử.
  Đã đọc lại S01/S02 extract và mở ảnh phân công để đối chiếu trách nhiệm.
- Không truy cập lại được5đường dẫn NAS đã cung cấp. Không khẳng định văn bản/phân công
  chưa đổi tại ngày08/11/2026. Không yêu cầu người dùng cấp lại dữ liệu chỉ để giải thích khung đã có.
- [Cảnh báo phiên bản PKH](TP_EXCEL_REFERENCE_ANALYSIS.md#cảnh-báo-phiên-bản-pkh):
  snapshot S03 cũ khác XL05 quan sát29/10; phần mapping phụ thuộc biểu mẫu cần re-baseline.
- [Workflow/quyền](TP_KD_WORKFLOW_AND_PERMISSIONS.md), [readiness](TP_BIZ002_ACCEPTANCE_AND_READINESS.md)
  và [workflow native](TP_KD_NATIVE_001_WORKFLOW.md) giúp phân biệt quy trình nguồn,
  thiết kế đề xuất và chức năng hồ sơ đang triển khai. UI KD-UI-007 không đóng business/pilot.

## Nghiệp vụ của phòng

Theo S01 P045–P063, Ban KD có bốn mảng: cơ hội/đấu thầu; quản trị hợp đồng;
kế hoạch–giao khoán–nghiệm thu/thanh quyết toán; năng lực/thương hiệu.
Đây là đầu mối thị trường và điều phối thương mại của dự án tư vấn khảo sát/thiết kế,
không thay trách nhiệm chuyên môn của phòng thực hiện hoặc hạch toán của kế toán.

Luồng điển hình:

1. Thu thập cơ hội, đánh giá và trình chủ trương; có nhánh giao trực tiếp.
2. Chuẩn bị giải pháp/giá/hồ sơ pháp lý–năng lực, liên danh nếu có; kiểm và nộp thầu, lưu kết quả.
3. Đàm phán hợp đồng chính/thầu phụ, rà soát phạm vi–giá–điều khoản; bản duyệt, ký và hiệu lực riêng.
4. Lập kế hoạch, phiếu giao việc, giao khoán; phân công một đầu mối chính và các bên phối hợp.
5. Theo dõi tiến độ/sản lượng; phòng chuyên môn khảo sát/thiết kế/BIM-QC kiểm chất lượng và bàn giao.
6. Tổng hợp hồ sơ nghiệm thu theo đợt/phạm vi/đối tác; kiểm căn cứ và phần bị trả lại.
7. Lập đề nghị thu/chi theo điều khoản, phối hợp QT-TC và kế toán về hóa đơn, tiền thực tế/công nợ.
8. Quyết toán/thanh lý, theo dõi nghĩa vụ/giữ lại còn tồn và lưu hồ sơ truy xuất được.

Project có thể mở trước khi có hợp đồng; tạm ứng có thể trước nghiệm thu; sản lượng,
nghiệm thu, thu/chi lặp nhiều đợt. Phụ lục và sửa sai quay lại đúng hồ sơ/phiên bản liên quan.
Năng lực/chứng chỉ, truyền thông, kế hoạch định kỳ và báo cáo là việc xuyên suốt, không chỉ cuối luồng.

## Vai trò từ tài liệu S02, chưa khẳng định nhân sự hiện hành

| Vị trí trong phân công tháng4/2026 | Trọng tâm trách nhiệm nguồn |
| --- | --- |
| Trưởng Ban Kinh doanh | Chiến lược/kế hoạch năm, tiếp cận dự án, phân công và kiểm soát thầu/hợp đồng/giá/rủi ro, báo cáo lãnh đạo; chủ trì quản trị TACICO |
| Phó phòng / Chủ trì dự án | Dự án được giao từ thầu tới thanh quyết toán; tiến độ/hồ sơ/khoán, tổng hợp báo cáo quản trị hợp đồng và phối hợp QT-TC |
| Chủ trì dự án | Theo dõi dự án được giao, tiến độ, đàm phán, khoán, cập nhật quản trị và hồ sơ QT-TC |
| Dự toán & Kế hoạch | Dự toán/đề xuất tài chính, dự án được giao, năng lực nhân sự đấu thầu, phiếu giao việc và phối hợp QT-TC |
| Học việc / Hồ sơ | Pháp lý/năng lực dự thầu, chứng chỉ, cập nhật dữ liệu và hồ sơ năng lực/truyền thông; hỗ trợ công việc được giao |

Đây là5vị trí/phân công nhân sự trong nguồn, không phải5role phần mềm loại trừ nhau.
Chủ trì KD khác chủ nhiệm/chủ trì thiết kế. Lãnh đạo, QT-TC/kế toán, phòng kỹ thuật/
thiết kế/BIM-QC, chủ đầu tư và thầu phụ là bên phối hợp, không tự thành nhân sự Ban KD.
Nhiệm vụ “chủ trì ký kết” không đủ chứng minh cá nhân có thẩm quyền ký mọi hợp đồng.

## Thông tin đã có

- Các nhóm công việc, điểm phối hợp và hồ sơ quản trị theo S01/S02.
- Cấu trúc project/hợp đồng/phụ lục/hạng mục/khoán cấp1–2 và các sự kiện sản lượng,
  nghiệm thu/hóa đơn/thu chi; cách phân biệt bản cập nhật tổng với phát sinh theo snapshot nguồn.
- Một việc có một người/đơn vị chịu trách nhiệm chính; phân công và BASE reference tách biệt.
- Người dùng đã chọn BASE làm nơi duyệt chính thức giai đoạn đầu; TANPHAT quản trị hồ sơ,
  rà soát và ghi nhận tham chiếu/kết quả, chưa có connector được kiểm chứng.
- Nguyên tắc xem tiền theo người được giao quản trị/trưởng ban/QT-TC/lãnh đạo đúng scope;
  hỗ trợ cấp riêng. Đọc metadata, sửa, xuất và cấp quyền không tự bao hàm nhau.
- Đã có phương án hai actor cho CTR-002a test theo quyền người dùng giao AI quyết định;
  đây không phải khoảng trống thiết kế lại, cũng chưa là bổ nhiệm người thật toàn công ty.
- Các ma trận thiết kế, checklist, kịch bản mô phỏng và hồ sơ native có dữ liệu mẫu;
  chúng không thay bộ hồ sơ thực tế và sign-off của chủ nghiệp vụ.

## Khoảng trống để áp dụng thực tế

| Nhóm | Thông tin/bằng chứng cần bổ sung | Đầu mối phù hợp |
| --- | --- | --- |
| Nhân sự/phân công hiện hành và Q2 | S02 còn áp dụng không; dự án/đầu mối lập–soát–ghi nhận/xác minh BASE; người quyết định và thao tác cấp/thu hồi quyền | Trưởng ban/chủ nghiệp vụ, lãnh đạo và IT theo phân công |
| Q1 | Thẩm quyền/hạn mức/ủy quyền ký, duyệt thầu/hợp đồng/khoán/chi; không lấy ngưỡng đối chiếu1.000VND làm hạn mức | Lãnh đạo, QT-TC/pháp chế |
| Q3 | Mẫu BASE đúng nhóm, đường duyệt/thứ tự, người quyết định, bản hồ sơ và chứng cứ; khả năng API/export nếu cần tích hợp | Người vận hành BASE/KD |
| Walkthrough B01–B03 | 2–3chuỗi hồ sơ thực tế đã che dữ liệu: bình thường, trả–sửa–gửi lại, phụ lục/correction và bàn giao; có người kết luận/gap | Chủ trì KD và QT-TC |
| Q4/Q6 | Thuế/trước-sau VAT, nguồn chứng từ, kỳ, làm tròn, tạm ứng/thu hồi/giữ lại, phân bổ thu–chi và công nợ | QT-TC/kế toán |
| Q7/Q8 | Quy chế khoán/cấp cha-con, vượt mẹ cảnh báo hay chặn, thay đổi khoán/giá và sửa sau nghiệm thu/thanh lý | KD/QT-TC/lãnh đạo |
| Q5/Q9/Q10 | Danh mục hạng mục/giai đoạn, mở–dừng–đóng dự án, bàn giao chủ trì, ai kiểm chuyên môn/KCS và checklist đủ điều kiện | KD và chủ chuyên môn |
| Q11 | File nhạy cảm, quyền chia sẻ/xuất/lưu trữ, nghỉ/điều chuyển và thu hồi quyền | Chủ hồ sơ/HR/IT theo phân công |
| Q12 | PKH/Master bản dùng chính thức, quy tắc mã/mapping, dữ liệu chuyển đổi và người đối chiếu | Người giữ sổ KD/QT-TC |
| Q13 | Công thức/kỳ/nguồn/owner của KPI, đặc biệt sản lượng/doanh thu/lợi nhuận/dòng tiền | KD/QT-TC/lãnh đạo |
| Q14 | Vận hành production, thời gian phục hồi/mức mất dữ liệu chấp nhận, backup/lưu trữ ngoài máy | Ops/IT/lãnh đạo |

Không phải chờ toàn bộ Q để tiếp tục code/test giao diện/hồ sơ đã cho phép. Mỗi action
thực tế cần đúng phần nghiệp vụ/thẩm quyền/bằng chứng liên quan; không biến “còn thiếu xác nhận”
thành tuyên bố “chưa hiểu nghiệp vụ” hoặc coi thiết kế/mẫu/demo là xác nhận công ty.

Ưu tiên thu thập thực tế: cập nhật phân công → chốt lập/soát/thẩm quyền theo phạm vi →
walkthrough2–3hồ sơ → đối chiếu quy tắc tiền/khoán/KPI và ghi sign-off/gap.
