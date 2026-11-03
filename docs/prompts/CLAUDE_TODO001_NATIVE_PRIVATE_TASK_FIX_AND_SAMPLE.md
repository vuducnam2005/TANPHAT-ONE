# TODO-001 — Sửa quyền To-do và nạp việc cá nhân giả lập

Copy toàn bộ nội dung trong khối dưới để giao Claude. Người dùng chọn Claude thực thi ngày 02/11/2026; phiên chính chưa sửa application code hoặc nạp thành công To-do.

```text
Làm việc trong C:\TANPHAT ONE. Task TODO-001: sửa quyền To-do native và thêm dữ liệu giả cho tài khoản admin trên dev 18069. Không commit/push. Không sửa odoo/ hoặc addons/.

Đọc AGENTS.md, docs/PROJECT_STATUS.md, docs/AI_CHANGE_WORKFLOW.md, docs/CHANGELOG.md, docs/DECISIONS.md, docs/demo/ODOO_NATIVE_SAMPLE_DATA.md. Kiểm git status/diff, checkpoint và runtime; giữ mọi thay đổi có sẵn. Chọn CHG-ID mới chưa dùng, chạy ai_workflow.py start trước sửa. Không tự setup/reset database, đổi mật khẩu hoặc cấp grant/nhóm cho người thật.

Bằng chứng đã có:
- To-do native dùng project.task nhưng project_id=False, parent_id=False, is_template=False và user_ids chứa người đang đăng nhập; action project_todo.project_task_action_todo, path /odoo/to-do; mặc định lọc is_closed=False.
- Local helper .local/native-data-20261102/seed_todo.py dry-run thất bại ngay record đầu: admin id=2 tạo được, write/unlink=True, read=False. Mọi lần thử đã rollback; namespace tp_native_todo_20261102 chưa có binding. 28 task dự án cũ giữ nguyên.
- Nghi phạm: custom_addons/tp_project/security/ir.access.csv, task_platform_scope hiện ['|', ('project_id.tp_managed', '=', False), ('project_id', 'access', 'read')]. project_id trống không khớp đường quan hệ như dự kiến. task_platform_write_scope cũng cần kiểm với user thường. Đây là ir.access của Odoo 20; không thiết kế theo ir.rule cũ.
- Snapshot dev trước thử: .local/native-data-20261102/backup-20261102T025223Z/ (database+canonical filestore+manifest, pg_restore --list đạt, chưa rehearsal restore snapshot mới). Không in secrets.

1. Tái hiện trên database test cô lập trước khi sửa. Kiểm source/runtime domain thực tế, chứng minh nguyên nhân, không chỉ bỏ assertion hoặc dùng sudo để làm test xanh.

2. Sửa tối thiểu trong custom_addons/tp_project/:
- Nhánh no-project phải đi qua giới hạn TP để quy tắc native tiếp tục quyết định private task của ai.
- Hướng read đề xuất: ['|', ('project_id', '=', False), '|', ('project_id.tp_managed', '=', False), ('project_id', 'access', 'read')].
- Hướng write đề xuất cho user không là TP manager: ['|', ('project_id', '=', False), ('project_id.tp_managed', '=', False)]. Giữ nhánh manager hiện có. Chỉ áp dụng sau khi test xác nhận đúng.
- Không bỏ global rule, không cho phép mọi người đọc mọi task, không cấp TP manager để né lỗi, không dùng sudo ở API/UI; không biến To-do thành task thuộc dự án chỉ để tránh domain.
- Giữ nguyên company scope, assignment/grant và quyền native. project_id=False chỉ là điều kiện vượt qua lớp giới hạn TP, không phải cấp quyền riêng tư cho toàn hệ thống.
- Thêm regression tests vào bộ test tp_project hiện có. Giữ project_todo là module tùy chọn; không thêm dependency mới chỉ phục vụ demo. Nếu cần test với project_todo, cài riêng trên test DB.

3. Test bắt buộc trên DB test tách biệt, dữ liệu giả:
- User A tạo/đọc/sửa/xóa To-do của A; chuyển personal stage và đánh dấu hoàn tất hoạt động đúng.
- User B không được đọc/search/write/unlink To-do riêng của A, kể cả khi B là Project/TP manager mà không được chia sẻ; không suy mọi manager được xem việc cá nhân.
- Chia sẻ To-do cho B bằng user_ids thì quyền đúng theo native; không mở cho C.
- Cách ly công ty vẫn đúng với task có company_id; không ép To-do không company có chính sách khác native.
- Managed project/task: có assignment đọc được; ngoài assignment bị chặn; user thường không ghi managed task. Không đổi assignment/grant cũ.
- Unmanaged project/task vẫn theo quyền native; không làm lộ task dự án follower-only.
- Ruff cho phần Python test và Odoo tests tp_project; test tích hợp project_todo trên test DB. Ghi đúng pass/fail/skip và lệnh.

4. Sau khi test đạt mới áp dụng dev theo yêu cầu đã có:
- Chụp backup mới trước upgrade/nạp nếu dev đã thay đổi; xác định đúng process/port/db/data-dir. Chỉ update addon cần thiết bằng quy trình dự án, không upgrade all. Giữ PostgreSQL dùng chung, demo18109 và test DB khác. Không chỉ chỉnh quyền thủ công trên DB mà bỏ source.
- Dùng helper local seed_todo.py làm đầu vào đã chuẩn bị; kiểm và sửa tương thích nếu cần, không coi là đã nghiệm thu. Chỉ chạy apply khi dry-run rollback đạt; verify bằng registry mới phải created=0.
- Tạo 14 To-do cho admin: Inbox 3, Today 3, This Week 2, This Month 2, Later 2; Done 2. Mặc định Open hiển thị 12 việc.
- Nội dung gồm chuẩn bị họp, nhắc trao đổi hồ sơ, danh mục tài liệu và liên hệ khách hàng. Dùng mã/tham chiếu bốn dự án DA-2026-001…004 trong mô tả khi phù hợp; không sao chép 28 task dự án. Nếu ngày chạy khác 02/11/2026, điều chỉnh lịch theo Asia/Saigon và ghi ngày cơ sở.
- project_id=False, chỉ gán admin, personal stage đúng chủ sở hữu; giữ ghi chú giả lập trong mô tả/XML ID, tên việc tự nhiên. Không tạo mail/lời mời hoặc activity gửi cho người khác. Không import hồ sơ thật, không thêm tiền/hợp đồng/duyệt/ký/thanh toán/grant.
- Dùng namespace tp_native_todo_20261102 và transaction nguyên tử/idempotent. Không đổi task/stage/dữ liệu có sẵn; nếu stage hiện tại không khớp helper, đối chiếu đúng user/ID, không reset hay đổi tên tùy tiện.

5. Kiểm live qua phiên admin không sudo:
- Action To-do đúng domain, Open thấy đủ 12, bỏ Open thấy 14, Kanban chia đúng năm cột đang mở và Done khi chọn Closed; các thẻ mở/sửa được.
- Thử chuyển cột, hoàn tất/mở lại trên một record giả rồi trả về trạng thái mẫu; không giữ bản thử thừa.
- planner.dev không thấy hoặc gọi trực tiếp đọc được To-do riêng của admin. Test phải kiểm bản thân quyền, không chỉ bộ lọc action.
- Project/TP Projects vẫn cùng bốn ID, 28 task cũ giữ nguyên; timesheet, chi phí, hóa đơn, user/grant/mail không thay ngoài phạm vi được phép. Không nhầm tổng project.task với số task thuộc project vì To-do cũng dùng model này.

6. Bàn giao:
Cập nhật docs/PROJECT_STATUS.md, docs/CHANGELOG.md, docs/demo/ODOO_NATIVE_SAMPLE_DATA.md và tài liệu security liên quan nếu cần. Không tự ghi DEC mới chưa được quyết định. Ghi file/source/DB đã đổi, lỗi gốc, test, snapshot, dữ liệu thực nạp, URL và tài khoản admin (không mật khẩu). Giữ Next action audit UI-DEMO-001/002, AUTH-002/C01 và cổng nghiệp vụ riêng.
Chạy git diff --check, ai_workflow.py finish đúng CHG-ID mới với kết quả thực, ai_workflow.py check. Bất kỳ test fail phải xử lý hoặc báo rõ trước khi apply dev; không ghi test đạt chỉ vì workflow checker pass. Báo cuối ngắn, có cách mở /odoo/to-do và F5.
```
