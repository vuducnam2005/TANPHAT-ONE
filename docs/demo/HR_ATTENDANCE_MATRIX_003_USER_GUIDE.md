# HR-ATTENDANCE-MATRIX-003 — Hướng dẫn sử dụng Bảng dữ liệu theo file & Đối chiếu A/B

Phạm vi: `tp_hr_attendance` `20.0.3.0.0` (`DEC-058`), dành cho nhân sự / cán bộ nhập công có phân quyền `import`. Nhân viên thường tiếp tục dùng `Tổng quan chấm công`, `Bảng chấm công` và `Công của tôi` trên dữ liệu đã áp dụng.

## 1. Tải nhiều file Excel và giữ riêng từng nguồn

1. Vào **Chấm công → Bảng công theo file (Vào/Ra)** (hoặc bấm trực tiếp nút **Bảng công theo file (Vào/Ra)** / **Đối chiếu A/B** / **Nhập Excel máy chấm công** ngay trên **Tổng quan chấm công** và **Bảng chấm công**).
2. Kéo-thả hoặc chọn cùng lúc nhiều tệp `.xlsx` xuất từ máy chấm công. Mỗi tệp được phân tích độc lập: tệp lỗi sẽ báo lý do ngay và không làm mất các tệp hợp lệ còn lại.
3. Mỗi tệp hợp lệ được cấp mã lô riêng (`LÔ-xxxxx`), lưu checksum SHA-256, tên file gốc, kỳ nguồn, từng sheet, người tải và thời điểm ở trạng thái **Đã đọc / Lưu nguồn – Chưa áp dụng vào bảng tổng hợp** (`preview`).
4. Hệ thống tự chuyển sang màn **Bảng dữ liệu theo file** rộng toàn trang; bạn có thể đóng/mở lại bất kỳ lúc nào để xem các lô đã lưu theo quyền công ty. Với lô `preview` chưa áp dụng, có thể bấm **Bỏ qua nguồn** (bắt buộc nhập lý do để lưu lịch sử kiểm toán).

## 2. Xem Bảng dữ liệu theo file

- **Hai dòng mỗi nhân viên (`Vào` / `Ra`)**: giữ nguyên mã nhân viên theo Excel (`TP0xx`), tách bạch **ID máy** và **Mã HR** (`TP100xx`). Người chưa map HR và người không có giờ nào trong kỳ vẫn hiển thị đầy đủ để đối chiếu.
- **Nhóm đơn vị nguồn**: các dòng nhóm đơn vị từ file Excel có thể thu gọn / mở rộng và không bị đếm nhầm vào số nhân viên.
- **Tùy chọn cột phụ**: bật/tắt `Mã HR`, `ID máy`, `Chức vụ (Nguồn tệp)`, `Vắng mặt (Theo Excel)`. Số *Vắng mặt* chỉ là số nguồn cả kỳ trong Excel, không thay thế *Nghỉ đã xác nhận* của HR.
- **Bộ lọc chuẩn `DEC-044`**: chọn lô/file, sheet, khoảng ngày trong kỳ, đơn vị nguồn, tìm theo tên / mã Excel / mã HR / ID máy, tình trạng đối chiếu; bấm **Áp dụng** hoặc **Xóa bộ lọc** (có chip điều kiện).
- **Lọc khoảng ngày hẹp hơn kỳ nguồn**: chỉ cột ngày trong khoảng được hiển thị, còn nhóm **Đi muộn (`Lần` / `Phút`)** vẫn giữ nguyên tổng đúng cả kỳ nguồn theo Excel (không tự chia ngày).
- **Phân trang & Xuất Excel**: phân trang `10 / 20 / 50 / 100` theo nhân viên (hai dòng `Vào / Ra` luôn đi cùng nhau); nút **Xuất Excel** xuất đúng lô, sheet và bộ lọc đang xem.

## 3. Đối chiếu hai nguồn A/B trước khi tổng hợp

1. Bấm **Đối chiếu** trên thanh công cụ (hoặc nút *Đối chiếu với file khác* trong form Lô nhập).
2. Chọn **Nguồn A** (tệp/lô + sheet) và **Nguồn B** (tệp/sheet khác, hoặc chọn *(Chỉ so với dữ liệu hiện tại của hệ thống)*).
3. Hệ thống ghép theo `(Công ty, Nhân viên HR đã map, Ngày công)`. Người chưa map HR hoặc sai lệch tên (`name_conflict`) không tự gộp theo họ tên.
4. Ô ngoài phạm vi ngày của một file được gắn nhãn **Ngoài phạm vi tệp**, khác với **Ô trống trong kỳ** và **Không có trong tệp**.
5. **5 nhóm đối chiếu** (bấm trực tiếp vào thẻ thống kê hoặc lọc *Chỉ xem sai khác*):
   - **Giống nhau**: hai nguồn có cùng giờ chuẩn hóa / cùng tổng muộn.
   - **Chỉ có ở A / Chỉ có ở B**: chỉ một bên có dữ liệu (không coi ô trống của bên kia là nghỉ).
   - **Khác giờ hoặc số liệu**: khác giờ Vào/Ra hoặc khác tổng muộn — **không bao giờ tự ghi đè theo file mới hơn và không tự nối Giờ Vào của A với Giờ Ra của B**.
   - **Chưa đủ căn cứ / Thiếu mapping**: chưa map HR, ký hiệu lạ, ô gộp, giờ lỗi hoặc tổng muộn bất nhất.
6. **Áp dụng phần giống & mới hợp lệ**: đưa các ô `Giống nhau`, `Chỉ có ở A`, `Chỉ có ở B` (không nằm trong kỳ chốt / điều chỉnh đã duyệt) vào dữ liệu hiệu lực. Với ô giống nhau giữa A và B, hệ thống chỉ giữ **1 phiên công duy nhất** kèm chứng từ nguồn của cả hai lô (`source_batch_ids`); nếu còn sai khác, lô mang trạng thái `partial`.
7. **Xử lý từng sai khác**: chọn trực tiếp `A`, `B`, `Giữ` hoặc `Sau` trên từng ô ngày hoặc tổng Đi muộn đúng kỳ → nhập **Lý do / Căn cứ** (bắt buộc khi thay dữ liệu đã áp dụng) → bấm **Xác nhận & Lưu**. Hệ thống không cho ghi đè kỳ đã chốt hoặc ngày đã có phiếu điều chỉnh được duyệt, và kiểm tra dữ liệu mới nhất trước khi lưu để chống ghi đè đồng thời.
8. **Xuất đối chiếu**: tải file `.xlsx` gồm sheet *Đối chiếu theo ngày* và *Đối chiếu đi muộn kỳ* đúng theo bộ lọc đang chọn.
