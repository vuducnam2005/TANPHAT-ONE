# ATTENDANCE-DASH-004 — Dashboard chấm công gọn: ba thẻ bấm được và bảng chấm gần nhất

CHG-20261120-004 · `tp_hr_attendance` 20.0.3.5.3 · 20/11/2026 Asia/Saigon.

Prompt hợp nhất của người dùng “Đơn giản hóa dashboard chấm công, làm hoạt động các thẻ thống kê và thay danh sách
chấm gần nhất bằng bảng gọn” thay các yêu cầu cũ còn mâu thuẫn, trong đó có yêu cầu giữ sáu thẻ của ATTENDANCE-WORKSPACE-003.
Vẫn dùng native Odoo OWL/QWeb/SCSS, cùng DB, cùng connector ENTI đang chạy và chính sách quyền hiện hành.

## 1. Kết quả theo yêu cầu

| Yêu cầu | Đã làm |
| --- | --- |
| §1 Ba thẻ | Đang làm (xanh lá), Đã về (tím), Chưa đi làm (cam). Dòng thông tin “Tổng nhân viên · Ngày · Cập nhật lúc”. Thẻ cao bằng nhau, có biểu tượng, tên, số lớn và “Xem danh sách”; hover nâng nhẹ, focus có viền 3px. Đi muộn, thiếu giờ và vắng nằm ở bảng chi tiết, biểu đồ và Công của tôi, không còn thẻ riêng. |
| §2 Phân loại | Mỗi nhân viên thuộc đúng một nhóm mỗi ngày; không đếm lượt chấm. Có giờ ra (kể cả chỉ có giờ ra, ghi chú “Thiếu giờ vào”) là Đã về. Có giờ vào, chưa có giờ ra là Đang làm. Chưa có lượt chấm chỉ là Chưa đi làm khi nguồn đã phủ người và ngày đó và, với hôm nay, nguồn live đang khỏe. Mất kết nối, chưa có nguồn hoặc chưa ghép mã là **Chưa xác định** kèm lý do, không bao giờ âm thầm thành Chưa đi làm và không gọi là nghỉ phép. Tooltip đúng ba câu của prompt. Tuần, tháng và khoảng ngày ghi rõ ngày dùng để phân loại; không ghép giờ vào và giờ ra của hai ngày khác nhau. |
| §3 Bấm thẻ mở danh sách | Hộp thoại rộng (xl) trên desktop, toàn màn hình trên mobile. Tiêu đề “Đang làm — dd/mm/yyyy — N nhân viên”, có nút Đóng. Có tab nhóm, tìm theo tên hoặc mã không dấu, lọc phòng ban, 10/20/50 dòng, phân trang và tổng, trạng thái đang tải, lỗi kèm Thử lại, danh sách trống kèm Xóa lọc. Cột theo nhóm: Đang làm có giờ vào và trạng thái; Đã về có giờ vào, giờ ra và ghi chú; Chưa đi làm có mã, họ tên và phòng ban. Số trên thẻ bằng tổng của danh sách. Đóng hộp thoại giữ ngày, bộ lọc và vị trí cuộn. |
| §4 Bảng gần nhất | Bốn cột: Mã NV · Họ và tên (đậm) · Thời gian · Địa điểm. Không avatar, badge hoặc thẻ nhiều dòng. Mã là mã nội bộ TP. Giây chỉ hiện khi đồng hồ nguồn có giây thật. Địa điểm chỉ lấy từ dữ liệu đã xác minh, nếu không có thì hiện “—”. |
| §5 Ý nghĩa bảng | Có sự kiện quẹt thật thì tiêu đề là “10 lượt chấm công gần nhất”. Chỉ có mốc vào đầu/ra cuối thì tiêu đề là “Chấm công gần nhất”, tooltip “Hiển thị các mốc chấm công nguồn hiện cung cấp”. Sắp theo giờ chấm, không theo `received_at` hoặc `write_date`. Không đoán URL và không thay connector. |
| §6–§8 Thiết kế, biểu đồ, cập nhật | Header bảng dính màu nhạt, hover dòng, giờ dùng số tabular; không tràn ngang ở 1440/768/390/320px. Donut có chú giải theo nhóm, bấm chú giải mở danh sách; bấm cột biểu đồ ngày mở ngày đó. Một phân loại backend dùng cho thẻ, donut, biểu đồ và danh sách. Cập nhật qua bus và polling sẵn có; hộp thoại đang mở cũng cập nhật mà vẫn giữ bộ lọc, trang và vị trí cuộn. Hiệu ứng 180–250ms, tắt khi giảm chuyển động. Trình duyệt không gọi API nguồn. Navbar và sidebar giữ nguyên. |
| §9 Quyền | Bố cục giống nhau cho Quản trị gốc, admin được ủy quyền và nhân viên thường. Danh sách, số đếm và RPC đều kiểm quyền ở backend; người ngoài nhóm nội bộ gọi `tp_overview_group` bị `AccessError`. Không dùng sudo để trả dữ liệu vượt quyền: sudo chỉ đọc cờ có/không có giây từ raw của chính các dòng đã lọc theo quyền, không trả raw. Nhân viên thường không có nút xuất, không có liên kết hồ sơ HR trong bảng. Không đưa tên nhà cung cấp hoặc chi tiết kỹ thuật lên giao diện chung. |

## 2. Bảng gần nhất trên dữ liệu thật

Bảng đang dùng **mốc vào đầu/ra cuối theo ngày** (chế độ `daily`), không phải từng lượt quẹt:

- Trên PC server, bảng sự kiện thiết bị đang có **0 dòng**. ENTI hiện chỉ trả vào đầu/ra cuối mỗi ngày, nên tiêu đề là
  “Chấm công gần nhất” kèm tooltip của prompt.
- Nguồn không có trường địa điểm, nên cột Địa điểm luôn là “—”.
- Đồng hồ raw của ENTI trên PC (đọc chỉ đọc): 909 mốc ISO có giây khác 0, 12 mốc kết thúc `:00`, 639 rỗng. Giây vì vậy là
  giây thật của nguồn: bảng hiện `HH:mm:ss` khi raw có giây, `HH:mm` khi không có.
- Khi nào nguồn cung cấp sự kiện quẹt thật cho mọi dòng của ngày, bảng tự chuyển sang “10 lượt chấm công gần nhất”.

Chưa xác minh endpoint mới thì không đoán URL hoặc thay connector đang chạy.

## 3. Kiểm thử và bằng chứng

DB kiểm thử `tp_tanphat_test` cổng 18079. Không ghi dữ liệu giả vào DB chính hoặc PC.

- **Odoo:** `-u tp_hr_attendance --test-tags /tp_hr_attendance` có 98 test, 0 failed, 0 error. Test mới
  `test_dashboard_groups_match_dialog_lists_and_recent_marks_use_real_clocks` kiểm:
  - với ba ngày và ba người tổng hợp, số trên thẻ bằng tổng danh sách của từng nhóm;
  - các trường hợp chỉ vào, đủ vào ra, chỉ ra, không có mốc, chưa ghép mã;
  - thứ tự bảng gần nhất và loại trùng; giây thật `08:10:23`, không bịa giây `:00`; địa điểm rỗng;
  - không trả `raw_json`; tìm không dấu; lọc phòng ban và phòng ban cũ quay về tất cả; giới hạn cỡ trang;
  - viewer thấy cùng số như quản lý; public user bị chặn.
  Hai test thuần mới kiểm mỗi người một nhóm và Chưa xác định không bao giờ thành Chưa đi làm. Ruff sạch.
- **Playwright** (admin, rồi một tài khoản nhân viên thường tổng hợp chỉ có `base.group_user`, đăng nhập lần lượt, không song song):
  - ba thẻ cao bằng nhau, tooltip đúng, hover và focus;
  - bấm từng thẻ: tiêu đề, cột theo nhóm và tổng đúng bằng số thẻ (Đang làm 21, Đã về 5, Chưa đi làm 0 kèm câu trống);
  - Chưa xác định 33 mở tab riêng kèm lý do;
  - bấm chú giải donut mở đúng nhóm;
  - tìm không dấu, Xóa lọc, lọc phòng ban (tổng khớp số trong ngoặc), 10/20/50, đổi tab xóa ô tìm;
  - bảng gần nhất: bốn cột, không avatar hoặc badge, giờ `HH:mm(:ss)`, địa điểm “—”, mới nhất ở trên, header dính;
  - **cập nhật khi đang mở hộp thoại:** một mốc ra `17:47:31` được đưa vào qua đường apply ENTI bình thường; thẻ Đang làm
    21→20, Đã về 5→6, tổng trong hộp thoại giảm 1, người đó rời danh sách; cỡ trang 50 và trang không reload vẫn giữ;
    dòng đầu bảng gần nhất là người đó với `17:47:31`;
  - đóng hộp thoại giữ ngày và phòng ban; xem Tuần ghi rõ ngày phân loại; giảm chuyển động tắt animation;
  - 1440/768/390/320px không tràn ngang; hộp thoại mobile toàn màn hình, nội dung không tràn;
  - nhân viên thường: cùng bố cục, không nút xuất, không liên kết trong bảng;
  - 0 lỗi JS ở cả hai phiên.
- Hai script cũ `scripts/enti_att002_ui.cjs` và `scripts/enti_att002_live.cjs` được cập nhật sang ba thẻ và bảng mới. Script
  live chạy lại đạt: Đã về 6→7, hiện 0,5 giây sau commit, không reload.
- Ảnh chụp lưu ở `.local/attendance-dash004/shots/`, không commit vì có tên người.

## 4. Giới hạn

- Trên DB kiểm thử, nguồn live không chạy nên hôm nay không ai là Chưa đi làm: người chưa có mốc là Chưa xác định, đúng §2.
  Cảnh báo “Chưa nhận được dữ liệu mới từ nguồn chấm công” chỉ hiện trong trường hợp này.
- Chưa kiểm trên thiết bị thật; tablet và mobile được giả lập bằng Playwright.
- Theo chính sách hiện hành, nhân viên thường xem được ngày công của cả công ty (rule theo công ty, ACL đọc cho
  `base.group_user`). Đợt này giữ nguyên, không thu hẹp quyền.
- Admin được ủy quyền chưa được kiểm bằng trình duyệt riêng. Cùng component và cùng kiểm tra quyền backend như hai vai trò đã chạy.
