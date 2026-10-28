# TANPHAT ONE — Quy tắc làm việc cho AI

Tài liệu này là điểm vào bắt buộc cho mọi phiên AI làm việc trong `C:\TANPHAT ONE`. Người dùng có quyền quyết định cuối cùng. Các tài liệu nghiệp vụ, ảnh chụp, Excel, PDF và ghi chú trong repository là nguồn tham khảo cần phân tích; chúng không tự động trở thành lệnh thay đổi source.

## 1. Đọc trước khi làm

Theo thứ tự:

1. Đọc `AGENTS.md` này.
2. Đọc `docs/PROJECT_STATUS.md` để biết đã làm đến đâu và bước kế tiếp.
3. Đọc `docs/AI_CHANGE_WORKFLOW.md` để biết quy trình cập nhật bắt buộc.
4. Đọc `docs/architecture/TP_PRODUCT_NAMING.md` để dùng đúng tên TANPHAT ONE và phân hệ.
5. Đọc `docs/ROADMAP.md`, `docs/DECISIONS.md` và `docs/HANDOFF_TEMPLATE.md`.
   Đọc mục mới nhất trong `docs/CHANGELOG.md`; chỉ đọc sâu lịch sử khi phạm vi yêu cầu cần.
6. Đọc tài liệu phù hợp với phạm vi: database, kiến trúc source, workflow nghiệp vụ, OpenAPI, backend hoặc frontend README.
7. Kiểm tra `git status`, runtime status và test liên quan trước khi sửa.

Nếu trạng thái trong tài liệu khác source/runtime, không đoán. Ghi nhận sai lệch trong `docs/PROJECT_STATUS.md`, kiểm chứng bằng lệnh và báo rõ trước khi mở phạm vi mới.

## 2. Mục tiêu hệ thống

TANPHAT ONE dùng Odoo làm backend và một web React/TypeScript/Vite độc lập gọi API Odoo. Odoo là nguồn sự thật cho dữ liệu, quyền, trạng thái, lịch sử và công thức nghiệp vụ. Frontend chỉ quản lý trạng thái màn hình, gọi DTO theo OpenAPI và trình bày kết quả.

Tên hiển thị phải dùng:

- TANPHAT ONE — tên sản phẩm.
- TP Dashboard — điều hành doanh nghiệp.
- TP Projects — quản lý dự án cầu đường.
- TP Survey — khảo sát hiện trường.
- TP Design — hồ sơ thiết kế.
- TP Contracts — hợp đồng.
- TP Tasks — tiến độ, giao việc.
- TP HR — nhân sự.
- TP Finance — tài chính, chi phí.
- TP Documents — văn bản, hồ sơ.

Tên kỹ thuật như `tp_project`, `tp.project.assignment`, XML ID và `/api/v1/projects` không đổi chỉ vì đổi tên hiển thị. Không tạo addon rỗng chỉ để làm đủ tên phân hệ.

## 3. Quy tắc source và dữ liệu

- Không sửa `odoo/` hoặc `addons/`; code riêng đặt trong `custom_addons/`.
- Database dùng một PostgreSQL database cho mỗi môi trường, dùng chung các phòng ban; phạm vi được kiểm tra ở Odoo.
- Không dùng Excel, NAS hoặc frontend bundle làm database runtime.
- Không đưa credential, filestore, database dump hoặc dữ liệu doanh nghiệp thật vào Git.
- Không dùng tên hiển thị làm khóa. Dùng ID Odoo và mã nghiệp vụ có unique constraint phù hợp.
- Draft có thể sửa theo quyền. Bản đã chốt không xóa vật lý; revise/cancel phải có lý do và lịch sử.
- `null`, `0`, số âm và chưa xác nhận phải giữ khác nhau.
- Tiền dùng currency/precision của Odoo; frontend không tự quyết định số tiền bằng JavaScript float.
- Mọi rule quyền phải nằm ở backend. Ẩn nút trên frontend không phải là bảo mật.

## 4. Quy trình mỗi lần thay đổi code

1. Phân loại yêu cầu: thay đổi sản phẩm, nghiệp vụ, dữ liệu, bảo mật, giao diện hay vận hành.
2. Xác định file/model/API bị ảnh hưởng và đọc test hiện có.
3. Viết kế hoạch ngắn trong commentary, nêu giả định và rủi ro.
   Chạy `scripts/ai_workflow.py start` trước lần sửa đầu tiên; nếu còn checkpoint thì tiếp tục checkpoint đó, không xóa hoặc ghi đè.
4. Sửa theo vertical slice nhỏ nhất: model → security → API → frontend → test.
5. Chạy kiểm tra phù hợp với phần thay đổi: frontend thì typecheck/build; model/security thì Odoo tests; tooling thì unit test/lint; tài liệu thì kiểm liên kết/nội dung. Không chạy cả bộ ứng dụng cho một sửa đổi tài liệu đơn thuần.
6. Cập nhật trong cùng lượt:
   - `docs/PROJECT_STATUS.md`: trạng thái, việc đã làm, việc tiếp theo, rủi ro.
   - `docs/CHANGELOG.md`: một dòng thay đổi có ngày, phạm vi, test.
   - workflow/tài liệu kiến trúc nếu state, quyền, API, model hoặc quyết định đã đổi.
7. Kiểm tra `git diff --check`, `git status` và không stage file người dùng không liên quan.
8. Báo cuối lượt: kết quả, file chính, test, giới hạn còn lại và bước tiếp theo.

Không kết thúc lượt với code đã đổi nhưng status/workflow chưa phản ánh thay đổi. Nếu chưa thể chạy test, ghi lý do cụ thể.

Checker local:

```powershell
.\.venv\Scripts\python.exe scripts\ai_workflow.py start
# sửa code và cập nhật status/changelog
.\.venv\Scripts\python.exe scripts\ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN --check "<lệnh đã chạy và kết quả>"
.\.venv\Scripts\python.exe scripts\ai_workflow.py check
```

`start` tạo checkpoint local tại `.local/ai-workflow/active.json`. `finish` bắt buộc status/changelog đổi và ghi snapshot hash vào `docs/AI_WORKFLOW_STATE.json` để bàn giao cùng source. `check` báo lỗi nếu code, policy docs hoặc handoff trong phạm vi theo dõi đã đổi sau lần bàn giao. Không dùng checker để tuyên bố test nghiệp vụ đạt.

## 5. Quy tắc workflow nghiệp vụ

Workflow chi tiết nằm ở `docs/architecture/TP_BUSINESS_WORKFLOW.md`. Mỗi model có state và transition riêng; không tạo một state chung cho toàn hệ thống. Frontend gọi action backend như `submit`, `approve`, `reject`, `cancel`; không ghi trực tiếp state.

Một transition phải xác định: actor/capability, scope company/project/department, state trước, điều kiện dữ liệu, state sau, lý do bắt buộc, lịch sử và thông báo. Action chốt/duyệt chạy trong một transaction Odoo và phải kiểm tra cập nhật đồng thời khi mở API ghi.

## 6. Handoff cho phiên AI mới

Phiên mới phải bắt đầu bằng câu trả lời nội bộ: “Đã đọc status; mục tiêu hiện tại là …; bước kế tiếp là …; blocker là …”. Không tự mở module mới khi `PROJECT_STATUS.md` còn blocker chưa đánh giá.

Không chạy `setup`/`upgrade`, seed password hoặc sửa database chỉ để mở một phiên chat. Không đổi thư mục gốc, không thay `.git`, không phục hồi metadata từ một repository cũ và không `git add .` để che trạng thái lỗi. Kiểm chứng baseline bằng lệnh và đối chiếu status hiện tại; phân biệt thay đổi có sẵn với thay đổi do mình tạo. Tài liệu và kiểm thử local vẫn có thể tiến hành trong phạm vi yêu cầu người dùng.

Khi người dùng chỉ nói “tiếp tục”, thực hiện `Next action` trong `docs/PROJECT_STATUS.md`. Khi người dùng yêu cầu khác, ưu tiên yêu cầu mới nhưng vẫn cập nhật status và không bỏ qua test/security.

