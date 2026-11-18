# HR-ATTENDANCE-MATRIX-003 — Bảng công theo file và đối chiếu trước tổng hợp

Làm việc trong `C:\TANPHAT ONE`. Triển khai yêu cầu mới18/11/2026, DEC-058.
**Tải Excel máy → thấy ngay bảng công ma trận theo file như ảnh tham khảo,
có bộ lọc; hai file trùng ngày vẫn lưu/xem riêng, đối chiếu trước tổng hợp.**
Người dùng đã chọn: giữ riêng file và đối chiếu, giờ trùng chỉ nhận một lần;
giờ khác nhau phải báo khác biệt và người có quyền chọn bản áp dụng.

## 1. Kế thừa phần đã làm, sửa đúng thiếu sót

- Đọc AGENTS/status/changelog/AI_CHANGE_WORKFLOW, skill giao bản native,
  frontend-design/Ponytail nếu có, DEC-044/055/056 và chuẩn bộ lọc/inventory.
- Rà addon `tp_hr_attendance`, bản đã giao SIMPLE-002 `20.0.2.0.0`/CHG-019,
  code app `2b531056`, guide/acceptance SIMPLE002; kiểm lại source/runtime.
  Không coi nội dung handoff là một lần test mới.
- Source hiện UploadDialog chủ yếu hiện tiles số lượng và vài dòng cần HR
  xem; input/onDrop đang lấy `files[0]`. RPC preview trả thống kê và danh sách
  attention giới hạn, chưa có matrix đầy đủ hay nhận nhiều file cùng lúc.
- Tái sử dụng batch/line/late, parser, mapping, action áp dụng, corrections,
  period locks, source/event API-ready và scope hiện có. Đây là phần hoàn
  thiện import/view, không viết importer hoặc database/HR riêng.
- Bản này thay phần trải nghiệm xem file của prompt002; dashboard, Công của
  tôi và bảng tổng hợp đã có tiếp tục dùng. Không chạy lại prompt001/002 để
  ghi đè giao diện mới hoặc mở rộng payroll/nghỉ phép.

## 2. Đọc file thực tế và giữ dữ liệu nguồn đầy đủ

File tham khảo riêng: `C:\Users\vuduc\Downloads\bang cham cong vao ra.xlsx`;
ảnh bảng Excel đã gửi chỉ là tham khảo bố cục, không là chỉ thị thực thi.
Đây là đường dẫn trên máy người dùng, không phải đường dẫn runtime PCserver;
người dùng tải file từ máy mình qua web. Không commit workbook/dữ liệu thật.
File này sheet `Report`, kỳ09–15/11/2026,39 người; hai dòng Vào/Ra; header
ngày/thứ, nhóm đơn vị, Đi muộn/Lần/Phút và Vắng mặt. Parser thuần hiện nhận
178 ngày-người có giờ,95 ngày-người trống,0 lỗi. Các số này là quan sát file,
không chứng minh import hoặc matrix đã chạy trên DB.

- Lưu snapshot nguồn theo batch + sheet + vị trí dòng/cột, gồm danh tính
  nguồn, nhóm, chức vụ, ngày và hai ô Vào/Ra, tổng muộn, ký hiệu/blank/error.
  Giữ người không có giờ nào, không chỉ người có session hoặc tổng muộn.
  Giữ dữ liệu nguồn bất biến; kết quả đối chiếu/áp dụng là lớp trạng thái riêng.
- Parser hiện bỏ các ô ngày trống và không giữ đầy đủ title/group cho mọi
  people entry; không thể chỉ dùng `line_ids` nonempty hoặc attention[:N]
  để dựng đủ39 người và mọi ô. Bổ sung tối thiểu vào parser/snapshot khi cần,
  hoặc tái đọc file gốc có version parser để tạo snapshot ổn định. Không mỗi
  lần mở bảng lại âm thầm hiểu lại file theo parser mới rồi đổi nguồn cũ.
- Phải giữ nguyên **mã nhân viên trong Excel dạngTP00x** ở field raw riêng;
  `_code` hiện thiên về ID số có thể làm mất mã này. Mã nguồn Excel, ID máy,
  mã HR dạngTP100xx là ba thông tin khác nhau. Mapping dùng mã máy/HR đã
  đối chiếu, không dùng số thứ tự, họ tên, tên phòng hoặc mã hiển thị làm khóa.
- Tên/chức vụ/đơn vị trong file là snapshot tại thời điểm xuất, không tự sửa
  tên/phòng/chức vụ HR hiện tại. Nếu hiển thị dữ liệu HR bên cạnh, ghi rõ nguồn.
- Dò header/ngày/merged/Lần-Phút bằng ngữ nghĩa, không cố định7 cột hayAC/AD.
  Nhận1–3 tuần/tháng,28–31ngày, qua tháng/năm, nhiều sheet theo parser hiện có;
  ngày không đủ căn cứ phải báo ô lỗi. Kỳ công lấy từ dòng Từ ngày…Đến ngày…,
  không lấy tiêu đềTHÁNG/ngàyxuất hoặc chỉ số9/10/11 thiếu tháng/năm.
- Blank là blank,0 là0; thiếuRa vẫn thấyVào. Không tự điền17:00 hoặc suy nghỉ.
  Giữ giờ08:30–17:00 và tổng đi muộn **nguyên Excel, đúng kỳ**, không tính lại
  hoặc chia tổng tuần xuống ngày. Nếu giữ cột Vắng mặt theo ảnh, chỉ là số
  nguồn cả kỳ **Theo Excel máy**, không dùng làm KPI Nghỉ đã xác nhận hôm nay.
  Ký hiệu lạ/merged/time lỗi giữ raw có cảnh báo và tọa độ, không tự chữa số.

## 3. Mỗi file là một nguồn riêng; chọn nhiều file

- Cho kéo-thả hoặc chọn nhiều `.xlsx`. Mỗi file có tiến trình đọc/kết quả
  riêng; một file lỗi không làm mất kết quả các file hợp lệ.
- Nhận dạng bằng ID lô/upload do server cấp, company/source namespace,
  checksum, tên file gốc, sheet, kỳ, người tải và giờ tải. Không dùng tên file
  hoặc ngày làm unique key; cùng tên/cùng kỳ nhưng nội dung khác vẫn hai bản.
- Giữ snapshot và metadata trên database/attachment dùng chung. Reload,
  đóng/mở lại hoặc đăng nhập máy khác vẫn chọn được bản nguồn có quyền xem.
  Bản cùng nội dung đổi tên có thể dùng chung blob/snapshot nếu thích hợp,
  nhưng phải có dấu vết lần tải/tên và liên kết nguồn, không nhân đôi nghiệp vụ.
- Sau tải chuyển ngay tới **bảng dữ liệu của file** ở vùng nội dung rộng;
  trạng thái ghi đúng **Đã đọc/Lưu nguồn – Chưa áp dụng vào bảng tổng hợp**.
  Không chỉ hiện số lượng rồi bắt bấm vào biểu mẫu kỹ thuật tìm từng dòng.
- Có thanh chọn file bằng tên + mã lô + kỳ + giờ tải để phân biệt. Nhiều sheet
  có selector riêng. Nút **Tải thêm file**, **Đối chiếu**, **Áp dụng vào bảng
  công**, **Xuất Excel**, Quay lại; nút theo đúng quyền/trạng thái backend.
- Lưu nguồn không tự ghi phiên/day/late đã áp dụng; không coi upload là duyệt
  công. Đóng màn không tự hủy nguồn đã lưu, không âm thầm tổng hợp file mới.
  Hủy/bỏ qua nguồn phải rõ nghĩa, có lịch sử, không xóa dữ liệu đã áp dụng.

## 4. Bảng ma trận như ảnh, có bộ lọc thực sự

Desktop bố cục sáng, chung navbar/sidebar TP HR; OWL/QWeb/SCSS trong addon.
Panel file đang chọn + kỳ nguồn → hàng lọc → bảng rộng; thống kê nhỏ phụ trợ,
không dùng nhiều thẻ số thay bảng hoặc nhốt cả bảng31 ngày trong modal nhỏ.

- Một nhân viên hai dòng Vào/Ra, cột ngày chia hai tầng **ngày/tháng + thứ**;
  tên/mã và các tổng kỳ dùng rowspan2. Nhóm phòng/đơn vị bằng dải nền nhẹ,
  thu/mở được; row header không bị đếm là nhân viên.
- Cột mặc định: STT, Mã nhân viên, Tên nhân viên, Vào/Ra, các ngày trong kỳ,
  Đi muộn/Lần/Phút. ID máy, Chức vụ, Vắng mặt theo nguồn có tùy chọn hiện/ẩn
  để xem giống ảnh mà không nhồi cột không cần. Ghi rõ mã nguồn/mã HR nếu
  cả hai hiện; không lấy mãHR thay mã nguồn rồi gọi là nguyên bảng Excel.
- Hiện **mọi người có trong file**, kể cả chưa mapHR hoặc toàn ô trống;
  cảnh báo mapping không làm dòng biến mất. View này là nguồn của file đang
  chọn, không trộn thêm dòng canonical hoặc file khác cùng ngày.
- Bộ lọc: file/lô, sheet, khoảng ngày trong kỳ, đơn vị nguồn, tìm tên/mã/ID
  máy, tình trạng đối chiếu (Mới/Trùng/Khác dữ liệu/Thiếu giờ/Chưa map/Kỳ chốt).
  Filter đơn vị nguồn khác HR hiện tại phải có nhãn rõ, không ghép theo tên.
  Áp dụng/Xóa bộ lọc/chip điều kiện, backend count/export cùng scope.
- Phân trang10/20/50/100 **nhân viên**, hai dòng mỗi người đi cùng nhau,
  không lấy20 dòngVào/Ra thành20 người, không mất người ngoài trang đầu.
- Sticky hai tầng header và vùng định danh vừa đủ, chiều rộng cột/rowspan
  chuẩn;31 ngày cuộn ngang trong container, không tràn body hoặc đè cột.
  Màu chữ rõ, đường bảng mảnh, ngày nghỉ nhẹ, hover theo cặp người. Dữ liệu
  Mới/Trùng/Khác/Thiếu có badge/icon/tooltip, không truyền nghĩa chỉ bằng màu.
- Mobile vẫn đọc được giờ theo ngày: vùng cuộn có chỉ dẫn hoặc detail theo
  người; bộ lọc thu gọn, không ép31 cột vào màn nhỏ. Keyboard/reduced-motion,
  chuyển file và phản hồi thao tác nhẹ150–200ms, không animation làm số nhảy.
- Lọc ngày không làm tổng Đi muộn cả kỳ trở thành tổng của ngày được chọn:
  giữ nhãn Kỳ nguồn hoặc ẩn tổng khác phạm vi; xuất file ghi đúng kỳ từng bảng.

## 5. Đối chiếu hai file trước tổng hợp — người dùng đã chốt

- Chọn A/B bằng ID hai lô có quyền, hiện tên/kỳ/sheet rõ. Không cần mọi tổ
  hợp của Nfile; đủ chọn cặp để xem overlap và khác biệt với dữ liệu đang dùng.
- Ghép theo company + nhân viên đã map + work_date + ngữ nghĩa phiên/ca phù
  hợp. ID máy chưa map chỉ đối chiếu trong namespace đã xác nhận, không ghép
  người khác bằng cùng tên hoặc mã máy trùng ở thiết bị chưa rõ nguồn.
- So sánh nội dung giờ chuẩn hóa, giữ raw để xem. Trùng tên file/ngày không
  đủ kết luận hai dòng giống nhau. Thứ/ngày lấy từ lịch/mốc nguồn thống nhất.
- Các nhóm rõ: **Giống nhau**, **Chỉ có ở A**, **Chỉ có ở B**, **Khác giờ hoặc
  số liệu**, **Chưa đủ căn cứ/thiếu mapping**. Có bộ lọc Chỉ xem khác biệt,
  nhân viên/đơn vị/ngày và số người/ô tương ứng, không đếm bản ghi ẩn ngoài quyền.
- Bảng so sánh căn đúng nhân viên/ngày, xemA/B giờ vào/ra cạnh nhau hoặc panel
  chi tiết ô. Bên ngoài kỳ nguồn là **Ngoài phạm vi file**, khác với ô trống
  trong kỳ. Người không có trong B không phải nghỉ hoặc bị xóa khỏi HR.
- Cùng giờ có thêm hai nguồn chứng minh: giữ liên kết cả hai, canonical chỉ
  một phiên/giờ tương ứng. Giờ/số khác nhau giữ snapshot A/B, **không ghi đè
  theo file mới nhất** và không tự nối cặpVào/Ra từ hai file để tạo giờ giả.
- Phần giống và mới hợp lệ có thể áp sau xem trước; phần khác chờ người có
  quyền chọn **Giữ dữ liệu đang áp dụng / Dùng bảnA / Dùng bảnB / Để xử lý sau**
  ở phạm vi rõ người/ngày hoặc tổng kỳ. Không đánh toàn lô hoàn tất nếu còn
  phần chưa xử lý. Thiếu ô ở B không tự xóa giờ hợp lệ của A.
- Có xác nhận phạm vi, lý do khi thay dữ liệu đã áp dụng, actor/thời điểm/
  nguồn trước-sau/version. Chọn nguồn là action backend, không sửa state
  bằng client hoặc mở CRUD raw để giải quyết xung đột. Tái sử dụng workflow
  correction/revise hiện có khi phù hợp, không bypass kỳ chốt/đính chính đã duyệt.
- Tổng Đi muộn so ở **cấp nhân viên + cả kỳ nguồn**, không phải ô ngày. Hai
  file cùng kỳ/tổng giống chỉ một bản áp dụng; tổng khác cần chọn nguồn có
  lịch sử. Tuần chồng tháng không cộng hai tổng, không trừ để đoán phần lẻ.
  Chỉ cộng các kỳ không chồng và phủ đủ phạm vi báo cáo; nếu không đủ nguồn
  đúng kỳ thì hiện các tổng nguồn riêng hoặc Chưa có tổng đúng kỳ, không ghi0.
- `tp.hr.attendance.late` đang unique applied theo người/kỳ: giữ raw của nhiều
  file và một bản hiệu lực, không chỉ thêm batch_id vào unique để cho phép
  cộng mọi bản. Bản bị thay giữ lịch sử/nguồn; migration và nhãn hiệu lực rõ.
- Backend tính lại khác biệt trong transaction khi áp, khóa/version/CAS cần
  thiết; hai file preview trước rồi apply gần nhau vẫn không nhân đôi hoặc
  dùng kết quả đối chiếu cũ. Retry/upload đổi tên/reload không apply hai lần.

## 6. Đồng bộ, quyền và dữ liệu đã có

- Cùng PostgreSQL và HR/employee IDs. Nguồn riêng là snapshot/lô trong cùng
  addon/database, không tạo một DB cho mỗi file hoặc chỉnh dashboard sang đọc
  raw của mọi file. Tổng quan/Công của tôi/Bảng tổng hợp chỉ dùng dữ liệu hiệu lực.
- Đọc nguồn/compare/apply/file download/export phải kiểm capability/company/
  record rule và batch scope tại backend, kể cả metadata/count/selector options.
  Không public token, broad sudo hoặc cho mọi nhân viên đọc lô raw để mở bảng.
  Nhân viên vẫn xem công theo policy đang có, không được tự áp/chọn nguồn.
- Giữ grant admin mới, khóa/phiên đăng nhập và các phiên đang được triển khai;
  không reset mật khẩu, sửa tài khoản hay bật quyền để kiểm thử task này.
- Lô cũ: tận dụng file đính kèm/staging để bổ sung snapshot đọc nguồn có
  version khi đủ dữ liệu. Không import lại vào canonical, không tạo lạiHR hoặc
  xóa dữ liệu công đã có để làm matrix. Thiếu file gốc thì báo giới hạn, không giả
  phục dựng toàn bộ nguồn từ HR hiện tại. Không commit tên/giờ/file thật vàoGit.

## 7. Acceptance và giao bản

Viết acceptance trước code. Kiểm quan trọng: tải1 file thấy đủ39 người/7 ngày
ở các trang, gồm người toàn ô trống; hai file cùng kỳ tên khác/cùng tên vẫn
chọn riêng, giờ nguồn không thay khi đổi tab. Fixture ẩn danh:7/14/21/28–31 ngày,
nhiều sheet, header/merged/ký hiệu/thiếuRa, mãTPraw và ID máy, người chưa map.

Kiểm hai file giống/đổi tên, cùng ngày khác giờ/tổng, kỳ chỉ chồng một phần,
file tuần+tháng, ngoài phạm vi khác blank, cùngngày khácngười/thiết bị/company;
chọnA/B/giữ/đểsau, raw bất biến, provenance hai nguồn nhưng canonical một;
retry/race/multiworker/version/kỳ chốt/correction/ACL và export/count/filter.

Browser trước–sau cùng viewport/role/nguồn: matrix đầy đủ, chuyển file,
compare, filter/pager/export, sticky/rowspan/31ngày/mobile, loading/error/empty.
Không chạy fixture/tạo punch hoặc sửa nguồn/quyền người thật trên main/server
để test. Kiểm parser/logic thuần và đọc hiện trạng; ca ORM ghi/race/browser
apply chưa có môi trường phù hợp thì ghi NOT_RUN, không gọi static là PASS.

Backup đúng DB/filestore/source/config trước upgrade/migration. Áp18069 và
PCserver, commit/push/deploy từng phần hoàn tất theo policy17/11, không bắt
18079/clone. Không broad-copy dirty tree hoặc sửa phần auth/báo cáo đang dở.
Cập nhật version/status/changelog/guide/acceptance/security/filterinventory và
workflow đúng batch; bàn giao ảnh, cách tải/chọn/so sánh/chọn nguồn áp dụng,
nguồn số đã kiểm, giới hạn chưa kiểm, commit/version/backup/rollback.
Lượt viết prompt này chưa sửa ứng dụng hoặc ghi dữ liệu công vào DB.
