# CORP-REPORT-001 — Bổ sung quy trình báo cáo cá nhân hoàn toàn trên web

Ngày 16/11/2026. Phần bổ sung cho [prompt full module đang thực thi](CLAUDE_CORP_REPORT_001_FULL_MODULE.md).
Yêu cầu trực tiếp của người dùng: hiện cá nhân làm báo cáo bằng Excel; cần chuyển toàn bộ việc lập kế hoạch, báo cáo và nhận xét cấp trên sang web.
Đây là phần làm rõ cùng module, không phải yêu cầu khởi tạo lại hoặc viết module thứ hai.

## 1. Cách tiếp nhận khi đang triển khai dở

- Tiếp tục batch/checkpoint hiện có, giữ code/test/dữ liệu test đã làm. Đọc addendum này ở điểm chuyển bước an toàn, đối chiếu phần đã triển khai rồi bổ sung khoảng thiếu; không abort transaction/upgrade đang chạy.
- Không chạy lại từ đầu, reset source, xóa DB, seed lại toàn hệ thống, tạo checkpoint cạnh tranh hoặc đổi ID batch chỉ vì có tài liệu bổ sung.
- Phần đã đáp ứng thì tái sử dụng và kiểm chứng; chỉ bổ sung phần chưa đủ. Cập nhật acceptance/schema/UI/PROJECT_STATUS/CHANGELOG/ROADMAP trong **batch do bạn đang sở hữu**, không finish hộ phiên khác.
- Giữ phạm vi prompt chính: Odoo native, cùng DB/identity/quyền, test18079; chưa tự áp main18069, chưa nhập lịch sử Excel thật hoặc đổi grant/tài khoản thật, không commit/push.
- File addendum do phiên điều phối soạn riêng để tránh sửa đè tài liệu/code/checkpoint của phiên đang chạy. Nó không phải bằng chứng module đã hoàn thành.

## 2. Nguồn Excel và ý nghĩa nghiệp vụ

Đọc chỉ tham khảo file:
`\\192.168.1.2\6.tadic\03_ kehoach_baocao\03_namvd\Q4\202611_tadic_nam_kh_bc_thang-11.xlsx`.

Phiên điều phối đã đọc cấu trúc, không sửa workbook. Có sáu sheet: `KH&BC_Quy`, `KH&BC_Thang`, `KH&BC_Tuan 1`, `KH&BC_Tuan 2`, `KH&BC_Tuan 3`, `ISO_DanhMuc`.
Manifest/trích xuất private: `.local/reporting001/personal_web_source_analysis.json`; SHA256 nguồn `34b3e75cb506e8bece8b7c2a9202fe1710798bdecf56d44204b0eaa0629c67ac` tại lần đọc. Đối chiếu lại nếu dùng bản nguồn mới; không đưa dữ liệu công việc/tên người trong workbook vào Git.

Các cột cần chuyển thành chức năng web:

| Nội dung mẫu | Trên web |
| --- | --- |
| Mục tiêu / Tiêu chí ở quý và tháng | Mục tiêu quý, kế hoạch tháng có cha/con, tiêu chí và owner; tuần liên kết đúng tháng/quý |
| Nhiệm vụ chi tiết | Dòng kế hoạch/công việc ổn định; chọn việc hiện có hoặc đề xuất việc trong quyền, không tạo bản sao mỗi kỳ |
| Đầu ra / Kết quả cụ thể | **Đầu ra dự kiến** được thống nhất ở kế hoạch; hiển thị riêng với kết quả thực hiện |
| Mức ưu tiên | Danh mục có mã/nhãn và màu; cấu hình dùng chung, không nhập text tùy tiện |
| Người thực hiện / Phụ trách / Chủ trì / Phối hợp | HR/user IDs dùng chung; phân biệt người chịu trách nhiệm và người phối hợp, không suy quyền từ text tên |
| Thời hạn | Ngày phải hoàn thành công việc, khác hạn nộp báo cáo |
| Hoàn thành thực tế / Kết quả đã đạt | Nhân viên cập nhật kết quả, ngày/khối lượng nếu phù hợp và minh chứng; không tự biến mô tả thành % hoàn thành |
| Trạng thái | Trạng thái **công việc** riêng, không dùng thay trạng thái gửi/rà/chốt **báo cáo** |
| Vướng mắc / Khắc phục | Vấn đề, cách xử lý, hỗ trợ cần cấp trên, người/hạn xử lý; có thể theo dõi sang kỳ sau |
| Quản lý đánh giá | Nhận xét/đánh giá của cấp trên ở **từng đầu việc**, ngoài nhận xét chung toàn báo cáo; nhân viên đọc/phản hồi nhưng không sửa phần cấp trên |
| Chỉ đạo | Ý kiến/yêu cầu tiếp theo; chuyển thành hành động có owner/hạn/theo dõi khi cần, không chỉ lưu text |

Danh mục workbook có trạng thái công việc và mức đánh giá gợi ý. Đây là nguồn tham khảo cho cấu hình, chưa là quy chế đánh giá nhân sự/lương thưởng. Không chép nguyên công thức Excel: một số dòng ghi biến thể như “Đã hoàn thành”, “Hoàn thành bước đầu” trong khi công thức đếm so sánh nhãn “Hoàn thành”. Web cần mã trạng thái chuẩn và tiêu chí rõ; **“hoàn thành bước đầu” không tự trở thành hoàn thành toàn bộ**.
Tên sheet/tháng và mô tả kỳ trong workbook chưa đủ để nhập lịch sử tự động. Trên web luôn lưu ngày bắt đầu/kết thúc cụ thể; “Tuần 3” phải kèm khoảng ngày, không tự giả định tháng nào cũng có bốn tuần.

## 3. Trải nghiệm nhân viên — không cần mở Excel để nộp hằng kỳ

Từ cùng tài khoản/nhân viên HR hiện có, vào **Báo cáo → Báo cáo của tôi**:

1. Chọn kỳ tuần/tháng/quý hợp lệ; thấy nghĩa vụ, ngày từ–đến, deadline nộp và người nhận/rà được phân công.
2. Bấm **Lập báo cáo**; hệ thống đưa các công việc/kế hoạch thuộc kỳ và quyền của người đó vào bản nháp. Không yêu cầu upload một Excel đã điền, gõ lại hồ sơ người/phòng hoặc tạo nhiệm vụ trùng.
3. Xem đầu ra kế hoạch; nhập kết quả thực tế, vướng mắc/khắc phục, minh chứng và đề xuất kỳ sau bằng input rõ ràng. Có thao tác thêm việc phát sinh với lý do; việc mới không âm thầm sửa mục tiêu quý/tháng đã ban hành.
4. **Lưu nháp** và quay lại sửa được. Phải hiển thị lưu thành công/chưa lưu/lỗi; nếu dùng autosave thì chỉ lưu nháp, có kiểm version và trạng thái rõ, không tự gửi báo cáo hoặc ghi đè bản người khác.
5. **Xem trước → Gửi báo cáo**; kiểm nội dung cần thiết/người nhận, ghi phiên bản/thời gian gửi. Không có reviewer hợp lệ thì hiện hướng dẫn cấu hình/phân công, không báo gửi thành công vào inbox không ai nhận.
6. Theo dõi trạng thái; đọc nhận xét chung và từng đầu việc. Khi bị **Trả lại**, thấy lý do và dòng cần bổ sung; sửa nháp rồi **Gửi lại**, giữ nguyên bản gửi trước.
7. Theo dõi chỉ đạo/công việc cần xử lý, cập nhật phản hồi và kết quả theo quyền. Sang kỳ sau có thể mang phần việc tồn sang **cùng ID**, không nhân đôi kết quả.

Nếu nhân viên được phép đề xuất kế hoạch tuần: có **Đề xuất kế hoạch**, cấp trên rà/thống nhất/ban hành; nhân viên không tự sửa baseline mục tiêu/quyền ban hành. Không bắt mọi kế hoạch do admin kỹ thuật nhập hộ.
Không yêu cầu cá nhân lập tháng/quý nếu không có nghĩa vụ hoặc yêu cầu cụ thể. Báo cáo cá nhân của trưởng phòng khác bản đại diện phòng.

## 4. Trải nghiệm cấp trên và trao đổi hai chiều

- **Chờ tôi rà soát** có số lượng đúng scope/kỳ; xem các bản đã gửi của nhân viên được phân công, không đọc nháp riêng ngoài quyền.
- Mở báo cáo thấy rõ người/phòng/kỳ/phiên bản; mỗi đầu việc có kế hoạch, kết quả, vướng mắc và vùng **Nhận xét của quản lý**.
- Có nhận xét chung, nhận xét từng dòng, mức đánh giá cấu hình được và yêu cầu bổ sung. Mức đánh giá là dữ liệu nghiệp vụ riêng, không ghi vào trạng thái công việc hay tự sửa kết quả của nhân viên.
- Nhận xét công bố cho tác giả phải đọc được trên web; nhân viên có **Phản hồi** đúng luồng. Nội dung nội bộ hạn chế audience phải tách và đánh dấu, không trộn vào phần tác giả được xem.
- **Trả lại** bắt buộc lý do; có thể đánh dấu các dòng cần sửa. Không lặng lẽ chỉnh actual của nhân viên cho khớp ý quản lý. Sau khi tác giả gửi lại, quản lý thấy bản mới và so sánh thay đổi.
- **Chốt báo cáo** theo capability sau rà soát; không tự chốt báo cáo cá nhân của mình. Chốt không có nghĩa mọi đầu việc đã hoàn thành: việc chưa xong vẫn tồn tại và cần xử lý kỳ sau.
- Nhận xét/chỉ đạo có actor, thời gian, report version và line ID nếu gắn dòng. Không tạo thêm snapshot báo cáo đầy đủ chỉ vì một comment; lưu event/review record tối thiểu. Nội dung gắn bản chốt được bảo toàn; sửa nhận xét bằng sự kiện đính chính có lịch sử, không rewrite snapshot.
- Chỉ đạo thành hành động có người nhận/hạn/kết quả; giữ link với đúng report/dòng, không lẫn tác vụ dự án nguồn. Tác giả/người được giao nhận thông báo **trong ứng dụng** theo cấu hình; không tự gửi email/chat ra bên ngoài.
- Reviewer được phân công theo scope và hiệu lực, có ủy nhiệm nếu cần. Không suy cấp trên từ tên/chữ ký trong Excel; thay đổi tổ chức vẫn giữ lịch sử người đã nhận xét, quyền đọc hiện hành kiểm lại.

## 5. UI của trang báo cáo cá nhân và màn rà soát

Không làm trình xem Excel nhúng hoặc form chỉ có upload/download; toàn bộ bước nhập/gửi/rà/phản hồi phải thao tác trực tiếp được.

```text
Báo cáo của tôi                  [Tuần 3: ngày ... – ...] [Trạng thái]
Nhân viên · Phòng ban       Hạn nộp · Người rà soát · Lần gửi
[Kế hoạch và kết quả] [Vướng mắc / Kỳ sau] [Nhận xét] [Lịch sử]

Nhiệm vụ | Đầu ra dự kiến | Hạn | Thực tế | Trạng thái | Nhận xét
  > Mở dòng: người phối hợp, chi tiết kết quả, minh chứng,
             vướng mắc, đánh giá quản lý và phản hồi

[Lưu nháp] [Xem trước] [Gửi báo cáo]            theo quyền/state
```

- Không dàn 11–13 cột hẹp như Excel trên một màn. Giữ cột trọng tâm; thông tin phụ ở expand/drawer/detail; xem đủ dữ liệu nhưng không chồng chữ/nút.
- Phân vùng rõ kế hoạch, kết quả nhân viên, nhận xét cấp trên; field nào ai được sửa thể hiện đúng khả năng backend. Read-only có kiểu hiển thị rõ, không giống ô nhập đang hoạt động.
- Nhãn **Đầu ra dự kiến** và **Kết quả thực tế** không dùng thay cho nhau. Có trạng thái báo cáo và trạng thái công việc riêng, ví dụ báo cáo Đã chốt nhưng công việc Đang làm.
- Nhận xét/trả lại có nhãn màu và vị trí dễ thấy; bấm dòng đang yêu cầu bổ sung mở đúng nội dung, không bắt tìm trong chatter dài.
- Giữ chuẩn sáng/màu/hover/motion/filter/pager/back/mobile của prompt chính; bộ lọc công việc theo trạng thái/ưu tiên/hạn/nguồn và nhận xét cần xử lý. Bảng chưa lưu giữ an toàn x2many/dirty state.
- Dashboard hỗ trợ theo dõi; thao tác soạn và rà soát thực hiện ở màn chuyên biệt, không chỉ có chart mà thiếu nơi làm việc.

## 6. Dữ liệu, quyền và tổng hợp

Tất cả kế hoạch, kết quả, comment/review, version, chỉ đạo nằm cùng DB Odoo của môi trường; cùng user/employee/department/project/task với hệ thống. HR cung cấp danh tính/phòng/avatar; không tạo tài khoản báo cáo mới cho một người đã có account.
Tháng tổng hợp facts/đầu ra từ tuần có link và phân kỳ đúng; quý tổng hợp tháng đối chiếu mục tiêu, người quản lý chỉ bổ sung diễn giải/quyết định thay vì gõ lại từng việc. Tổng hợp phòng/công ty không đếm nhiều lần đầu ra nhiều người cùng tham gia.
Phân biệt số dòng việc đã hoàn thành, tỷ lệ nộp báo cáo, mức đạt mục tiêu và kết luận đánh giá; không dùng một tỷ lệ chung thay tất cả. Nếu metric chưa có định nghĩa, không tính điểm/phần trăm tùy ý.

Backend chặn nhân viên sửa đánh giá/chỉ đạo/actor/người nhận/state/version bằng RPC, create/write hoặc x2many payload, kể cả khi UI đã ẩn field. Cấp trên không vượt scope/phòng/company, người phối hợp không tự đọc cả báo cáo riêng của người khác. Comment, attachment, notification, preview và export giữ audience/finance/HR privacy như prompt chính.

Excel/Word/PDF là đầu ra phục vụ lưu/chia sẻ/trình họp. Quy trình hằng kỳ không phụ thuộc một file phải làm bên ngoài; không tự nhập workbook thật để tạo báo cáo hoặc chấm hoàn thành quá khứ. Nếu sau này cần chuyển lịch sử, tách mapping/đối soát/cho phép nhập thành bước riêng.

## 7. Bổ sung acceptance vào batch đang chạy

Thêm ID không trùng vào acceptance do phiên thực thi đang sở hữu, không thay/xóa các AT cũ. Kiểm thực với ít nhất hai nhân viên, một quản lý, một user ngoài scope giả trên test:

1. Nhân viên từ tài khoản hiện có lập và lưu nháp trên web; kế hoạch/đầu ra/người/phòng đúng nguồn, không upload Excel.
2. Gửi thành công vào inbox đúng quản lý; thiếu người nhận bị chặn có hướng dẫn. Draft không lộ cho người không có quyền.
3. Quản lý nhận xét hai dòng khác nhau và nhận xét chung; nhân viên xem/phản hồi được nhưng sửa đánh giá bằng RPC bị từ chối.
4. Trả lại một dòng kèm lý do → nhân viên bổ sung → gửi lại → quản lý so sánh/chốt; snapshot, actor, comment và phiên bản cũ còn nguyên.
5. Báo cáo Đã chốt còn công việc Đang làm; sang tuần mới giữ task/đầu ra gốc, không tăng khống tổng tháng/quý. Báo cáo gửi lại không tăng số người đã nộp.
6. Tháng/quý lấy đúng kết quả các tuần và kế hoạch cha; tuần giao tháng được phân kỳ đúng, không cộng trùng; dữ liệu thiếu không thành 0.
7. Cấp trên giao chỉ đạo → người nhận phản hồi → theo dõi hoàn thành; retry không tạo trùng. Thông báo nội bộ không lộ nội dung ngoài audience.
8. Export đúng bản/kỳ gồm nội dung kết quả và nhận xét được công bố theo quyền; nội dung quản lý hạn chế không rò qua PDF/Excel/Word/file.
9. Hai tab đồng thời/stale version/retry không mất dữ liệu hoặc ghi đè đánh giá; main18069/tài khoản thật không thay đổi.
10. Desktop/mobile: nhập kết quả dài, mở nhận xét, trả lại, sửa/gửi lại, filter/back/dirty guard; bảng không chồng; reduced motion hoạt động.

Chụp bằng chứng luồng **nhân viên lập → gửi → quản lý nhận xét/trả → sửa/gửi lại → chốt** trên test, private `.local/corp-report001/`; báo đúng bước chưa chạy. Không gọi self-review là audit độc lập hoặc test kỹ thuật là công ty đã duyệt policy.

Khi bàn giao, hướng dẫn một nhân viên làm trọn một kỳ chỉ bằng web. Nếu họ còn phải soạn Excel bên ngoài mới nộp được, yêu cầu bổ sung này **chưa hoàn thành**.
