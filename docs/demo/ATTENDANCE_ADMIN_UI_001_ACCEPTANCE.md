# ATTENDANCE-ADMIN-UI-001 — Quản trị chấm công và xuất bảng công

Change `CHG-20261120-002`, ngày 20/11/2026 Asia/Saigon. Addon `tp_hr_attendance` **20.0.3.5.2**.
Trạng thái: **VERIFIED_RELEASE_READY**. Technical acceptance khác phản hồi hình thức và nghiệm thu nghiệp vụ.

## 1. Phạm vi cuối cùng do người dùng chốt

- Làm lại trang **Quản trị chấm công**: kết nối và số liệu thực; xuất bảng công;
  nhân viên cần đối chiếu; các lượt đồng bộ gần đây; thao tác xử lý công theo quyền.
- Bỏ phần nhập/lịch sử Excel trên màn và menu. Backend nhập mới đã chặn từ DEC-063;
  không bật lại, không drop dữ liệu cũ. Xuất trực tiếp bằng `tp_export_sheet` hiện có.
- Cấu hình native tách thông tin tài khoản và đồng bộ khoảng ngày; mapping ưu tiên
  tên/nhân viên/trạng thái, cột phụ tùy chọn; log có tìm/lọc và form chi tiết chỉ đọc.
- Bổ sung dashboard theo ảnh người dùng: bỏ chú giải bên cạnh donut, hover hiện trạng thái,
  số lượng, tỷ lệ; cột10 người gần nhất rộng60% trên desktop; bỏ nhãn đồng bộ và giờ cập nhật.
  Giữ sáu KPI/màu/bộ lọc/biểu đồ dưới; không đổi Công của tôi, cron hoặc dữ liệu/quyền.

Prompt ATTENDANCE-WORKSPACE-003/CHG-001 là mốc chuẩn bị trước khi người dùng đính chính.
Các thay đổi rộng về credential/security/migration/Công của tôi không thuộc release này;
diff đã lưu riêng dưới `.local/attendance-workspace003/superseded-broad-implementation`.

## 2. Thiết kế và dữ liệu

OWL/QWeb/SCSS trong addon, cùng session/backend Odoo. Giữ màu nền sáng/navy/blue
của TP HR; không sửa sidebar toàn hệ thống. Trang quản trị dùng dữ liệu hiện có,
không dựng máy Online/Offline hoặc số liệu giả. Trạng thái đồng bộ theo health backend;
ngày công nhận được là bản ghi nguồn, không được mô tả thành ngày công đã duyệt.

DTO nguồn thêm ngày/phòng ban hợp lệ cho xuất, số chờ đối chiếu, tối đa5 log mới nhất
theo company và ACL đọc thật; không trả log message/raw payload mới trong preview.
Không đổi capability hoặc rule; form/method sync, mapping, chốt và export vẫn kiểm backend.
Export gửi kỳ/phòng, không gửi page/page_size và dùng nguyên workbook chuẩn hiện có.

Hai danh sách ở trang quản trị là preview giới hạn5, không phải bảng đầy đủ. Nút Mở
đối chiếu/Mở nhật ký dẫn action native có SearchModel/domain/count/pager/export hiện có.
Nút Chờ xác nhận/Chưa khớp reset filter còn lại để không vô tình OR cả hai trạng thái.
Xem [inventory bộ lọc](../ui/TP_TABLE_FILTER_INVENTORY.md) cho coverage/N/A preview.

## 3. Kiểm thử và bằng chứng

Môi trường kiểm: database **tp_tanphat_test** hiện có, cổng **18079**, cron tắt;
không tạo DB/cổng mới. Backup đầy đủ dump/restore-list/config/filestore TAR đã kiểm
ở `D:\TANPHAT-backups\attendance-workspace003`. Hai actor `workspace003.test.*` chỉ
được tạo trong test, không đăng nhập làm văng phiên người dùng main/PC.

| Kiểm | Kết quả thực chạy |
| --- | --- |
| Python/Ruff phần thay đổi, XML, JS syntax, SCSS, diff whitespace | PASS |
| Node `scripts/tests/test_attendance_admin_ui.cjs` | PASS: quyền xuất, range sai không RPC, đúng params không phân trang, giữ ô đang nhập qua polling, filter đối chiếu độc lập |
| Odoo `/tp_hr_attendance` |96 test,2 assertion cũ yêu cầu menu nhập; sửa đúng kỳ vọng mới và chạy lại2 test:0 failed/0 errors. Các test còn lại đã đạt. Không nới backend assertion nhập bị chặn. |
| Ảnh trước |8 ảnh sources/config/mapping/log ×1440/390 tại `.local/attendance-workspace003/admin-before`,0 lỗi JS |
| Ảnh sau admin |16 ảnh sources/config/mapping/log ×1440/768/390/320 tại `.local/attendance-workspace003/admin-after`,0 lỗi JS |
| Dashboard bổ sung |PASS4width, không component/document overflow;10 người gần nhất, đủ6KPI, không legend/badge/timestamp.1440: recent666px/donut444px; hover thực `Đủ giờ vào/ra:5 người (8.5%)`. Evidence `.local/attendance-workspace003/after/results.json` |
| XLSX tải thật |PASS3 tệp từ UI (week/month/range-dept), đúng params; openpyxl2sheet/freezeF9-D4/kiểu ngày-giờ; reconciler3kỳ `ok:true`,0problems. Chưa mở trực tiếp Microsoft Excel |
| Vai trò |Odoo shell rollback: delegate được mở nguồn, employee AccessError. Browser2actor test HTTP403 login nên NOT RUN visual; ảnh browser chỉ original. Không đổi auth/quyền để ép test xanh |

Preview HTML dựng từ style/merge/độ rộng của workbook tuần đã được chụp và xem: tiêu đề, tên/ngày/giờ và ghi chú mẫu rõ, không cắt chữ/####. Đây không phải render Microsoft Excel; ảnh riêng `.local/attendance-workspace003/admin-after/export-week-preview.png`.

Lỗi phát hiện và đã sửa: Owl hiện tại không hỗ trợ `t-model` theo cú pháp cũ;
đã dùng value/change; browser chạy lại mới có16 ảnh đạt. Dữ liệu form xuất chỉ
khởi tạo ở lần tải đầu, polling không thay tháng/ngày/phòng đang chọn.

## 4. Baseline, giao bản và giới hạn

PC trước release: `tp_hr_attendance`20.0.3.5.1, health200. Local18069 thực tế chạy
sealed candidate FORM-VALIDATION002 tại `.local/validation002/main-candidate/runtime.conf`,
addon và DB20.0.3.3.0; đây là chênh lệch với mô tả source bàn giao trước. Không áp
release mới lên local cũ vì sẽ kéo các hạng mục không thuộc batch. PC là mục tiêu deploy.

Foreign WIP ở Reporting/Home/sidebar/policy đã tồn tại trước lượt; không stage/deploy.
Checkpoint gốc giữ nguyên. Workflow release được kiểm trên snapshot source Git cộng
đúng diff batch, không nhận foreign code thành đã nghiệm thu. Workspace tổng thể vẫn
có thể FAIL checker do WIP của phiên khác; xem kết quả seal và danh sách commit riêng.

Chưa kiểm thiết bị vật lý, chưa người dùng duyệt hình thức hoặc nghiệp vụ. Không
nhận thay nghiệm thu của HR. Backup/commit/deploy/public smoke sẽ được ghi sau kiểm cuối.
