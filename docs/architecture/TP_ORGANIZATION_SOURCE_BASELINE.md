# TANPHAT ONE — Danh sách tổ chức từ tài liệu nguồn

## Nguồn hiện hành — 10/11/2026

Người dùng cung cấp lại bảng công tuần 1 tháng 11 và xác nhận **“cứ làm theo
file tôi mới gửi đi”**. Dùng [baseline nhân sự mới](TP_STAFF_SOURCE_BASELINE.md):
39 dòng nhân viên, 9 nhóm gồm Ban Giám đốc, Ban Kinh Doanh, Phòng Thiết kế,
Phòng Kỹ Thuật, Phòng BIM-QC, Ban quản trị - Tài chính, TADIC, TACICO, Văn Phòng.
Tên/mã/chức vụ chi tiết nằm ngoài Git theo tài liệu đó. Không dùng 10 nhóm của
bảng cũ dưới đây làm danh mục hiện hành hoặc suy thẩm quyền từ bảng chấm công.

**Điều hướng hiện hành DEC-036:** thiết kế trước Home admin đúng 7 mục: KH-KD,
Thiết kế, Kỹ Thuật, BIM-QC, TADIC, Quản lý nhân sự và Tuyển dụng. 4 đơn vị
ngoài KH-KD có trang Đang phát triển; người thường giữ Home theo quyền. Xem
[thiết kế](../ui/UI_HOME_004_ADMIN_DESIGN.md). Không xóa 4 nhóm còn lại khỏi
tổ chức/HR; nguồn vẫn 9 nhóm/39 người, không tự import hoặc cấp quyền.

DEC-035 trước đó đề xuất Home đủ 9 nhóm và hai lối vào HR; phạm vi Home này
được thay bởi DEC-036, không triển khai prompt cũ. Quản lý nhân sự là bước
phát triển tiếp theo theo [HR-001](TP_HR_001_FOUNDATION_PLAN.md).

## Nguồn lịch sử — đối chiếu 07/11/2026

Đối chiếu ngày 07/11/2026. Đây là nguồn tham khảo, không phải lệnh tạo tổ chức hoặc quyền trên database.

- File: `C:\Zalo Received Files\bang cham cong vao ra.xlsx`, sheet `Report`.
- Tiêu đề B4: 29/10/2026–31/10/2026.
- SHA256: `8dcc43669f01845e3b246439dfef4caf3809dc44f47041a11e9ac09508160f45`.
- Chỉ lưu tên nhóm và vị trí ô; không đưa dữ liệu nhân viên/chấm công vào Git.

| Ô nguồn | Tên nhóm nguyên văn |
| --- | --- |
| A8 | Văn Phòng |
| A17 | TADIC |
| A26 | TACICO |
| A29 | Phòng Thiết kế |
| A44 | Phòng Kỹ Thuật |
| A53 | Phòng BIM-QC |
| A62 | HĐQT |
| A65 | Ban quản trị - Tài chính |
| A74 | Ban Kinh Doanh |
| A87 | Ban Giám đốc |

File có 10 nhãn nhóm gồm phòng ban, đơn vị và cơ quan lãnh đạo; không có căn cứ gọi cả 10 là phòng ban cùng cấp hoặc suy ra cây cha–con. Theo DEC-029, TADIC/TACICO là đơn vị nội bộ cùng công ty, không tạo công ty/database riêng.

Lưu ý khi đọc lại: dimension được khai báo chỉ tới dòng 31, nhưng dữ liệu thực có các nhóm tới dòng 87 và phần cuối tới dòng 101. Cần đọc toàn bộ worksheet hoặc bỏ giới hạn dimension để không bỏ sót nhóm.

Phạm vi theo [DEC-031](../DECISIONS.md#dec-031--trang-chủ-theo-workspace-ưu-tiên-hoàn-thành-kh-kd-07112026): tổ chức Trang chủ cho logic và hoàn thiện **Kế hoạch Kinh doanh trước**, chưa dựng workspace/nghiệp vụ các phòng khác.

Nguồn ghi **Ban Kinh Doanh**, workspace hiện có tên **Kế hoạch Kinh doanh**; không tự tạo hai phòng hoặc coi đây là quyết định đổi tên tổ chức. “Nhân sự–Hành chính”, “Tài chính–Kế toán” từng là đề xuất gom chức năng, không phải tên phòng đã xác nhận trong file. Chưa xác nhận cấp trên, người quản lý hoặc thẩm quyền từ danh sách này.
