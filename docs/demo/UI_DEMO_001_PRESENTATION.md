# UI-DEMO-001 — Kịch bản trình diễn TANPHAT ONE (5–7 phút)

Môi trường: `http://127.0.0.1:18109/odoo` trên máy trình diễn, database `tp_tanphat_demo_ui001`,
**toàn bộ là dữ liệu trình diễn**. Mật khẩu lấy tại `.local/ui-demo-001/credentials.json`, không đọc to hay chiếu lên màn hình.
Trạng thái: `IMPLEMENTED_PENDING_AUDIT` — điều phối viên rà soát trước khi trình lãnh đạo.

**Chuẩn bị 5 phút trước:** `scripts\ui_demo.py status` báo `odoo_listening: true`; mở mỗi màn hình một lần để Odoo dựng asset;
dùng hai cửa sổ trình duyệt (một cửa sổ riêng tư cho `demo.kysu`) và để cửa sổ đang chiếu ở phía trước — tab bị ẩn sẽ tải chậm.
Trong danh sách app chỉ bấm **"TANPHAT ONE – Demo"**; mục "TANPHAT ONE" bên cạnh là app nền sẵn có (danh sách dự án native),
không phải màn hình trình diễn.

Từ UI-DEMO-002, các nhóm công việc dùng tiếng Việt. Mở **Tất cả phân hệ** (điện thoại:
**Phân hệ**) để giới thiệu toàn cảnh và tìm nhanh “hop dong”, “du an” hoặc “request”.
Tên chuẩn TP nằm dưới tên Việt; mỗi phần minh họa có nhãn. Đóng bảng bằng Esc trước
khi trình bày nội dung. Kỹ sư không có nhóm Kinh doanh hoặc kết quả CRM/Dự thầu.
Điều hướng đã chạy và kiểm hai actor ngày 31/10/2026; [bàn giao UI-DEMO-002](UI_DEMO_002_HANDOFF.md)
có mapping/ảnh/test. Trạng thái vẫn chờ audit độc lập trước buổi trình bày chính thức.

## Thông điệp chính

1. Một nền tảng, một giao diện cho các mảng TANPHAT ONE quản lý.
2. Dự án là trục nối cơ hội, hợp đồng, công việc và hồ sơ.
3. Các phòng dùng chung nền tảng; menu và dữ liệu theo quyền ở backend, không phải ẩn nút.
4. Nói rõ phần nào đã chạy thật, phần nào là "Minh họa định hướng".

## Trình tự

| Phút | Màn hình (tài khoản) | Nói gì | Chỉ vào đâu |
|---|---|---|---|
| 0:00–0:45 | TP Dashboard (`demo.lanhdao`) | Đây là trang điều hành: số dự án, công việc mở, quá hạn, hợp đồng đang rà soát, cơ hội CRM | Dải "Dữ liệu trình diễn"; bấm KPI "Công việc quá hạn" → danh sách đúng 4 việc |
| 0:45–1:45 | Chuỗi dự án trên Dashboard → Tổng quan dự án Cầu Sông Xanh | Một dự án nối hợp đồng, công việc, tài liệu; cơ hội cùng khách hàng là liên kết minh họa | Bảng hợp đồng (trạng thái vòng đời tách khỏi rà soát), thanh giai đoạn công việc, vùng tài liệu thông thường/tài chính |
| 1:45–2:45 | Hợp đồng & hồ sơ → Luồng rà soát (TP Contracts) | Rà soát phiên bản là luồng thật đang có: nháp → chờ rà soát → trả lại → sửa lại, có lý do và lịch sử | Ô "Trả lại" với lý do; tầng BASE, ký, hiệu lực ghi "Ngoài phạm vi demo" |
| 2:45–3:30 | Nguồn lực → Tổng hợp tài chính (TP Finance) | Giá trị hợp đồng lấy từ dòng hợp đồng thật; chỉ cộng phiên bản đã rà soát xong; không gộp khác tiền tệ; không có lợi nhuận | Cột "Đã nghiệm thu", "Đã thu" có nhãn minh họa; bảng nguồn số liệu |
| 3:30–4:15 | TP Tasks, TP HR, TP Documents | Công việc theo giai đoạn; danh bạ nhân sự công khai, không có lương; tài liệu chia thông thường/tài chính | Kanban công việc; "Năng lực và phân bổ (minh họa)" |
| 4:15–5:00 | Kinh doanh: CRM, Dự thầu; Đề nghị BASE | CRM dùng `crm.lead` thật; Dự thầu và Đề nghị là minh họa định hướng; BASE vẫn là nơi duyệt | Bộ lọc dự án/trạng thái, chi tiết mẫu, mục "Ngoài phạm vi" |
| 5:00–6:15 | Đăng nhập `demo.kysu` (cửa sổ riêng) | Cùng một nền tảng, nhưng kỹ sư chỉ thấy dự án được giao, không thấy tiền, không thấy CRM/Dự thầu | Dashboard 1 dự án; Finance khóa; tài liệu tài chính không có trong danh sách và không tải trực tiếp được |
| 6:15–7:00 | Kết | Bước tiếp: rà soát demo, chốt phạm vi phân hệ kế tiếp theo ROADMAP | — |

## Câu hỏi thường gặp

- **Số liệu có thật không?** Không. Tên, số tiền, tệp đều giả lập, đánh dấu "(DEMO)".
- **Đã duyệt hợp đồng trên hệ thống chưa?** Chưa. Demo chỉ có rà soát nội bộ; phê duyệt vẫn trên BASE; ký, hiệu lực, nghiệm thu, thanh toán chưa mở.
- **Đổi góc nhìn trên Dashboard có đổi quyền không?** Không. Góc nhìn chỉ sắp xếp lại; quyền do tài khoản quyết định.
- **Giao diện này là sản phẩm chính thức?** Không. Đây là demo native Odoo; frontend React chính thức không đổi.

## Không làm trong buổi trình diễn

- Không đăng nhập bằng `admin`, không bật chế độ developer, không mở Settings.
- Không mở app "TANPHAT ONE" (không có chữ Demo), "Ứng dụng" hay các app native khác trong lúc trình diễn.
- Không tạo/sửa dữ liệu (các tài khoản demo chỉ có quyền đọc).
- Không chiếu tệp `credentials.json`.
