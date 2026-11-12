# Nhân sự — Nguồn tham khảo hiện hành

**Cập nhật thực thi 11/11/2026:** `IMPLEMENTED_VERIFIED_MAIN_PENDING_BUSINESS_VISUAL_PILOT`.
HR-001 đã áp source/module lên main `tp_tanphat_dev`/18069 sau backup và restore
kiểm chứng trên test chuẩn: 39 employee/39 version, 9 đơn vị có nhân viên trong
14 danh mục, mã TP và retry cùng nguồn cho 39 dòng bỏ qua. Dọn đúng 3 hồ sơ mẫu,
archive 16 actor theo manifest; giữ 25 identity, thông tin xác thực/nhóm và HEAD.
Năm tài khoản KH-KD còn chờ đối chiếu danh tính, không tự liên kết nhân viên.
Backend cuối 28 kiểm đạt; HOOT HR 10/Home 28 (kèm dependency 12/29); UI test
13 kịch bản có CRUD đạt trước fresh restore. Test sau restore: 11 kiểm chỉ đọc
đạt, 0 pageerror; 5 actor KH-KD giữ HEAD capability chỉ ở HEAD, list nghiệp vụ
rỗng nên không có hồ sơ thật để mở detail. Smoke chỉ đọc main11/11đạt,0pageerror; xem [acceptance](../demo/HR_001_ACCEPTANCE.md)
cho bằng chứng cuối và giới hạn kiểm detail khi không có dữ liệu nghiệp vụ.
Backup `025345789849Z` đã restore kiểm chứng 592 bảng/261 blob/424 sequence;
đối soát bảo toàn private 621 blob đạt, 0 vi phạm. Bằng chứng và mapping giữ
private `.local/hr001/`. Nghiệm thu nghiệp vụ, phản hồi giao diện và pilot chưa
được xác nhận bởi kiểm kỹ thuật. Phần kiểm kê/kế hoạch cũ dưới đây là lịch sử.

**Cập nhật:** 11/11/2026 (Asia/Saigon). **Phạm vi:** danh sách nhân viên,
nhóm đơn vị và chức vụ theo bảng công; không tự cập nhật nhân sự hoặc quyền Odoo.

## Nguồn mới 11/11/2026 — ưu tiên cho HR-001 / DEC-038

Người dùng cấp `C:\Zalo Received Files\bang cham cong vao ra (1).xlsx` và
chỉ đạo dùng file vừa gửi. SHA256
`8b1ed1f254ac56288da30b53a2fe3bb9858c18b995743c7d45fb686129b5f8ff`.
Hai sheet `Tuần 1`, `Tuan 2` cùng ghi kỳ 09–10/11/2026 tại B4, header A6:E6.
Mỗi sheet 39 dòng; cả 78 dòng cùng 39 người duy nhất thuộc 9 nhóm. B/D khớp trên tất
cả dòng, STT reset theo nhóm; không dùng STT hay OdooID làm mã nguồn. Reader
và XML độc lập đối chiếu danh tính khớp, không đổi file; không lưu giờ vào-ra.

Số nhóm/người như bảng lịch sử dưới, thứ tự khác. So roster 10/11 có 3 mã đổi
nhãn chức vụ; bản mới ưu tiên, không suy thành quyết định điều chuyển/hợp đồng.
Mã hiển thị đề nghị đã được người dùng yêu cầu: TP+(10000+mã nguồn),60 → TP10060;
PK Odoo không đổi. Chi tiết private `.local/hr-plan-20261111/verified-roster.json`
và runtime/account reconciliation; không đưa danh tính vào tracked files.

Người dùng yêu cầu nạp trong phiên thực thi prompt HR, không phải lệnh nhập
ngay ở phiên này. [Kế hoạch](TP_HR_001_ROSTER_WORKSPACE_PLAN.md) và
[prompt](../prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md) thay lộ trình nguồn
cũ cho lần nhập kế tiếp; các số liệu/giới hạn dưới đây giữ lịch sử 10/11.

## Nguồn và xác nhận

- Người dùng cung cấp lại `C:\Zalo Received Files\202611_tanphat_chamcong_tuan1.xlsx`.
- Sheet `Report`, tiêu đề tại B2; kỳ tại B3: **02/11/2026–07/11/2026**.
- SHA-256: `05478102e7b76e56f8796d7ea7a057ed5f8ded3c92dec38309297d730ace982f`.
- Header A5:E5: STT, Mã nhân viên, Tên nhân viên, ID, Chức vụ.
- Người dùng xác nhận khi được hỏi về khác biệt phân công cũ:
  **“cứ làm theo file tôi mới gửi đi”**. Đây là nguồn danh mục hiện hành,
  không dùng tài liệu phân công cũ để ghi đè nhóm/chức vụ trong file mới.

## Kết quả kiểm kê

| Nhóm nguyên văn | Ô nhóm | Số dòng nhân viên |
| --- | --- | ---: |
| Ban Giám đốc | A7 | 4 |
| Ban Kinh Doanh | A16 | 6 |
| Phòng Thiết kế | A29 | 9 |
| Phòng Kỹ Thuật | A48 | 4 |
| Phòng BIM-QC | A57 | 3 |
| Ban quản trị - Tài chính | A64 | 4 |
| TADIC | A73 | 4 |
| TACICO | A82 | 1 |
| Văn Phòng | A85 | 4 |
| **Tổng** | | **39** |

Đây là 9 nhóm trong bảng công, không khẳng định 9 phòng cùng cấp hoặc quan hệ
cha–con. Không tự thêm HĐQT từ file cũ vào danh mục mới; sự vắng mặt của nhóm
không chứng minh thay đổi cơ cấu pháp lý. TADIC/TACICO giữ DEC-029: đơn vị nội bộ.

## Bản chi tiết ngoài Git

Danh tính, mã và chức vụ đầy đủ lưu riêng ở `.local/staff-reference-20261110/`:

- `DANH_SACH_NHAN_VIEN.md`: danh sách theo nhóm, chức vụ nguyên văn và ô nguồn.
- `staff-directory.json`: 39 dòng với mã nguồn, tên, nhóm, chức vụ và provenance.
- `previous-source-comparison.json`: đối chiếu với bảng 29–31/10/2026.
- `manifest.json`: hash nguồn/kết quả và kiểm tra đối chiếu XML độc lập.

Không đưa danh sách tên, ID nhân viên hoặc dữ liệu chấm công thô vào Git.
Chỉ trích A:E và nhóm; không lưu giờ vào/ra trong bản tổng hợp. Mã nhân viên/
ID của file không phải `res.users.id` hoặc `hr.employee.id`.

## Khác biệt và cách sử dụng

- Nguồn mới có 39 dòng/9 nhóm; nguồn cũ 38 dòng/10 nhóm. Đối chiếu bằng mã
  nguồn: 1 mã chỉ có ở file mới, 0 mã chỉ có ở file cũ, 5 mã có thay đổi tên
  nhóm hoặc chức vụ. Không gọi đó là tuyển mới/nghỉ/điều chuyển đã ban hành.
- Ban Kinh Doanh hiện có 6 người trong file, không dùng nhóm 5 tài khoản
  KH-KD hiện hữu làm danh sách nhân sự đầy đủ. Vai planning trong cấu hình
  tài khoản cũ cần đối chiếu riêng; không suy từ tên gần giống hoặc nhiệm vụ cũ.
- Chức vụ giữ nguyên văn, kể cả cách ghi “Trường phòng”, “Kế toán trường”,
  “TV”. Nhãn hiển thị chuẩn hóa có thể đề xuất riêng, không sửa file gốc.
- Chưa có báo cáo quản lý trực tiếp, email/login, toàn bộ hồ sơ lao động
  hoặc quyền bảo mật từ bảng công. Không tự tạo user, đổi tên/chuyển phòng/
  thu hồi quyền tài khoản thật hoặc import 39 nhân viên vào database.
- Kiểm mới: đọc hết 114 dòng thay vì chỉ dimension, 39 mã không trùng,
  STT 1–39 đủ, tổng nhóm = 39; tên/mã/chức vụ đối chiếu độc lập bằng XML
  trong XLSX; hash file gốc trước/sau giữ nguyên. Không chạy macro/recalc.

Theo yêu cầu tiếp theo, danh mục nhóm được dùng soạn khung Trang chủ tại
[UI-HOME-004 admin-only](../prompts/CLAUDE_UI_HOME_004_ADMIN_ONLY.md).
Đây không phải lệnh import hồ sơ nhân sự hoặc triển khai các phòng khác.

DEC-036 chọn 5 phòng/đơn vị và 2 chức năng HR cho Home admin, không thay
danh mục nguồn 9 nhóm/39 người. [HR-001](TP_HR_001_FOUNDATION_PLAN.md) là kế
hoạch tiếp theo; chưa import hoặc liên kết tài khoản từ danh sách này.
