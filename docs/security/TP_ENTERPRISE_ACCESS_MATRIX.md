# TANPHAT ONE — Ma trận Phân quyền, Toàn vẹn Dữ liệu & Chống xung đột đồng thời

**Áp dụng xuyên suốt Đợt 0 – Đợt 5**  
**Tuân thủ bắt buộc các quyết định hiện hành:** `DEC-030`, `DEC-044`, `DEC-053`, `DEC-054`, `DEC-057`, `DEC-060`, `DEC-061`, `DEC-062`, `DEC-063`, `DEC-064`, `DEC-065`.

---

## 1. Nguyên tắc Bảo mật & Quản trị Tài khoản Bất biến

1. **Tách quyền Admin gốc vs Admin ủy quyền (`DEC-053/054/062`):**
   - **Admin gốc (`tp_admin_delegation.group_original_admin`):** Duy nhất có quyền cấp/thu hồi quyền admin, khóa/mở và quản lý tài khoản của admin ủy quyền; không bao giờ suy đoán admin gốc chỉ từ `base.group_system` hay `uid`.
   - **Admin ủy quyền (`tp_admin_delegation.group_full_admin` còn grant hiệu lực):** Toàn quyền quản trị nghiệp vụ các phòng ban, nhưng **không được** cấp/thu quyền admin, **không được** sửa thông tin tài khoản/hồ sơ của Admin gốc hoặc của Admin ủy quyền ngang cấp khác (kể cả khi đang khóa).
   - **Thu hồi quyền có hiệu lực tức thì:** Khi thu hồi grant admin hoặc chuyển phòng/thu hồi `tp.project.grant`, mọi lời gọi ORM/RPC, xuất file, danh sách người duyệt và kênh bus thời gian thực phải kiểm tra lại quyền hiện hành, không tin vào trạng thái cache trên trình duyệt.
2. **Không suy thẩm quyền tài chính / ký duyệt pháp lý từ quyền kỹ thuật:** Quyền xem/nhập số tiền hợp đồng và đối soát tài chính kiểm tra riêng qua capability tài chính (`tp.project.grant` `financial_read`, nhóm tài chính báo cáo/đối soát).
3. **Duyệt điều chỉnh công (`DEC-060/061`):** Chỉ Admin gốc và Admin ủy quyền có grant hiệu lực trong công ty duyệt/trả lại điều chỉnh công; tuyệt đối chặn tự duyệt phiếu của chính mình.

---

## 2. Ma trận Vai trò × Phân hệ × Phạm vi Dữ liệu

| Phân hệ / Đối tượng | Nhân viên nội bộ (`base.group_user`) | Trưởng phòng / Chủ trì dự án | Quản trị chuyên môn (HR / KH-KD / Kho / Request) | Admin ủy quyền hiệu lực (`DEC-053/061/062`) | Admin gốc (`DEC-054/062`) |
|---|---|---|---|---|---|
| **Việc cá nhân (`project.task` mở rộng)** | Xem/sửa việc tự tạo; xem việc dự án/cuộc họp/tin nhắn được giao; kéo sắp xếp bảng cá nhân của riêng mình; bấm *Báo xong* việc được giao | Giao việc trong phạm vi phòng/dự án; *Xác nhận kết quả* đầu việc mình giao/chủ trì | Theo phạm vi dự án/phòng được cấp | Toàn phạm vi nghiệp vụ (không lộ việc riêng tư `project_id=False` của người khác nếu không liên quan) | Như Admin ủy quyền |
| **Lịch làm việc & Phòng họp (`calendar.event`, `tp.meeting.room`)** | Tạo/sửa lịch của mình; đặt phòng họp trống; phản hồi RSVP lời mời; lịch `private` người khác chỉ thấy `'Bận'` | Tổ chức lịch họp phòng/dự án; chủ trì biên bản họp | Quản trị danh mục phòng họp (`tp.meeting.room`) | Quản trị danh mục phòng họp & lịch công ty (vẫn giữ che `'Bận'` lịch cá nhân riêng tư theo rule) | Toàn quyền |
| **Trao đổi (`discuss.channel`, `mail.message`)** | Chat trực tiếp, tạo nhóm, tham gia kênh phòng/dự án mình thuộc về; chuyển tin được phép đọc thành việc | Quản lý thành viên nhóm dự án/phòng mình phụ trách | Quản trị kênh thông tin chung | Không tự động chèn vào hội thoại riêng tư của nhân viên | Không tự động chèn vào hội thoại riêng tư |
| **Biên bản họp (`tp.meeting.minute`)** | Xem biên bản cuộc họp mình tham dự hoặc được giao đầu việc | Thư ký soạn nháp; Chủ trì xác nhận & phát hành (tạo task 1 lần); điều chỉnh có revision + lý do | Xem trong phạm vi dự án/phòng được cấp | Quản trị nghiệp vụ theo công ty | Toàn quyền |
| **Thông báo nội bộ (`tp.announcement`)** | Đọc thông báo thuộc phạm vi đối tượng nhận; bấm **Xác nhận đã đọc** theo phiên bản | Ban hành thông báo cấp phòng (khi được phân quyền); theo dõi tỷ lệ xác nhận của phòng | Ban hành/thay thế/thu hồi thông báo công ty; xem báo cáo người chưa xác nhận | Ban hành/quản trị thông báo công ty | Toàn quyền |
| **Yêu cầu phê duyệt (`tp.request`)** | Gửi/rút đề nghị của mình (Nghỉ phép, Công tác, Điều chỉnh công, Thiết bị, IT, Tạm ứng/Chi phí) | Duyệt/trả lại/từ chối bước được cấu hình (chặn tự duyệt) | Thực hiện sau duyệt (`executor`) và cập nhật kết quả thực hiện | Cấu hình loại đề nghị & duyệt bước `admin_group` | Toàn quyền cấu hình & duyệt bước `admin_group` |
| **Dự án, WBS, Hồ sơ NAS (`project.project`, `tp.project.dossier`)** | Xem dự án/hạng mục/hồ sơ được phân công; báo cáo tiến độ & tải minh chứng | Quản lý WBS, phụ thuộc, baseline (có lý do), xác nhận kết quả & phát hành hồ sơ kỹ thuật | KH-KD quản trị danh mục dự án, hợp đồng, giao khoán, nghiệm thu, đề nghị TT; ẩn tiền nếu thiếu grant tiền | Toàn phạm vi dự án & tài chính quản trị trong công ty | Toàn quyền |
| **Tuyển dụng, Nhân sự, Chứng chỉ, Đầu vào Lương** | Tự sửa trường cho phép trên hồ sơ của mình (`DEC-065`); xem danh bạ công việc đồng nghiệp (ẩn lương/CCCD/HĐ) | Đề xuất nhu cầu tuyển dụng phòng; tham gia đánh giá phỏng vấn ứng viên được mời | HR quản lý ứng viên, chuyển trúng tuyển sang `hr.employee` (kiểm trùng), quản lý chứng chỉ & bảng đối soát đầu vào lương | Toàn phạm vi HR/Kho/Tuyển dụng (trừ sửa peer admin / admin gốc `DEC-062`) | Toàn quyền + duy nhất cấp/thu Admin (`DEC-054`) |

---

## 3. Kiểm soát Tương tranh, Chống Thao tác Lặp & Toàn vẹn Giao dịch (Section M)

| Tình huống nhạy cảm | Cơ chế khóa & Chống trùng ở Backend | Hành vi khi xung đột / lỗi |
|---|---|---|
| **Hai người đặt cùng phòng họp trùng khung giờ** | `SELECT id FROM tp_meeting_room WHERE id = %s FOR UPDATE` trước khi kiểm tra giao thoa `[start, stop)` của các `calendar.event` active chưa hủy | Giao dịch đến sau nhận `ValidationError` rõ tên sự kiện/khung giờ đang giữ phòng; không bao giờ ghi 2 lịch trùng phòng |
| **Phát hành biên bản họp / Bấm lại hoặc F5** | Khóa dòng `tp.meeting.minute` `FOR UPDATE` + kiểm tra `action_item.task_id` đã tồn tại + `operation_token` | Mỗi dòng đầu việc chỉ sinh đúng 1 `project.task`; sửa biên bản sau phát hành tạo revision, không xóa task đã giao |
| **Chuyển tin nhắn chat thành công việc** | Kiểm tra quyền đọc `mail.message` + `TpPersonalOperationLog.acquire_or_replay` theo `operation_token` | Retry khi rớt mạng trả về đúng `task_id` đã tạo, không nhân đôi công việc |
| **Xác nhận đã đọc thông báo nội bộ** | Ràng buộc duy nhất `UNIQUE(announcement_id, user_id, acked_version)` + `ON CONFLICT` / khóa kiểm tra | Bấm đúp chỉ ghi 1 bản ghi xác nhận đúng thời điểm đầu tiên; nâng `version` trọng yếu yêu cầu xác nhận cho `version` mới |
| **Duyệt / Thu hồi đề nghị đồng thời (`tp.request`)** | `lock_rows(request, nowait=True)` (`FOR UPDATE NOWAIT`) + kiểm tra lại `approval_state` | Chỉ 1 thao tác thắng; thao tác còn lại nhận thông báo trạng thái thực tế mới nhất |
| **Gán / Đổi thiết bị kho (`tp_equipment`)** | Khóa bản ghi `maintenance.equipment` + kiểm tra `tp_custody == 'stock'` và `tp_employee_id == False` (kèm kiểm tra hiệu chuẩn với máy khảo sát) | Chặn gán chéo hoặc gán trùng cùng 1 máy cho 2 người |
| **Tải tệp đính kèm / Hồ sơ dự án / Tệp CV tuyển dụng** | Mọi route tải tệp kiểm tra `check_access('read')` trên bản ghi nghiệp vụ cha (`project.task`, `tp.project.dossier`, `hr.applicant`, `tp.contract.document`) | Không dùng `public=True` để lách quyền xem trước; đổi ID trên URL trả `403/404` |
