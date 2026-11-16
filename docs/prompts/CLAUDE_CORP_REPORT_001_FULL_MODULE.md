# CORP-REPORT-001 — Triển khai đầy đủ Trung tâm Báo cáo TANPHAT ONE

Ngày giao prompt: 16/11/2026. Bản prompt: CHG-20261116-006. Ngôn ngữ UI: tiếng Việt.
Đây là **prompt thực thi**, thay bước chỉ phân tích bằng triển khai R0–R5 dưới đây.
Tài liệu gốc: [thiết kế nghiệp vụ](../architecture/TP_COMPANY_REPORTING_001_DESIGN.md), DEC-048.

## 0. Nhiệm vụ và phạm vi thực thi

Làm việc trong `C:\TANPHAT ONE`. Bạn là phiên Claude triển khai, được sửa application code trong phạm vi prompt này.
Xây hoàn chỉnh phân hệ **Báo cáo / Trung tâm Báo cáo**, addon đề xuất `tp_reporting`, bằng Odoo native/OWL/QWeb/SCSS.
Phân hệ phục vụ cá nhân, trưởng phòng, mọi phòng ban và lãnh đạo; cùng nền giao diện và dữ liệu với hệ thống hiện có.
Không kết thúc ở thiết kế, mockup, dashboard tĩnh, menu rỗng hay chỉ làm R1. Triển khai lần lượt đến R5; nếu bị ngắt, bàn giao chính xác phần đã chạy và tiếp tục phần còn lại.

Hai luồng bắt buộc:

```text
Mục tiêu QUÝ → Kế hoạch THÁNG → Giao việc TUẦN → Thực hiện
       ↑              ↑                ↑            │
Đánh giá QUÝ ← Tổng hợp THÁNG ← Báo cáo TUẦN ← Kết quả
```

Trọng tâm hình thức: **giao diện sáng, đẹp, có màu sắc có nghĩa; dashboard có biểu đồ lớn ở đầu trang; bảng rõ ràng, không chồng chữ/cột; bộ lọc đúng từng nội dung; màn chi tiết và popup đều được thiết kế**. Hover và animation phải giúp hiểu thao tác.

Phạm vi môi trường:

- Code, cài/upgrade và kiểm thử trên **18079 / `tp_tanphat_test`** trước; PostgreSQL workspace **55432**. Một database dùng chung mọi module **trong từng môi trường**.
- Main **18069 / `tp_tanphat_dev`** là database khác môi trường, không phải DB riêng của phòng ban. Không để test ghi vào main hoặc hai Odoo cùng ghi một DB để giả vờ đồng bộ.
- Không tự tạo DB theo tên task; không restore test đè main. Kiểm tra quyền sở hữu phiên ghi test và runbook trước khi sử dụng.
- Hoàn thiện module chạy được trên test, mở URL cho người dùng xem, chuẩn bị backup/deploy/rollback main. **Lượt giao prompt này chưa cho phép áp module Báo cáo lên 18069**. Ngoại lệ triển khai main trực tiếp của task Kho trước đây không mở rộng sang task này.
- Không nhập hai Word thành dữ liệu thật, không sửa tài khoản/grant người thật; sử dụng vai trò và dữ liệu giả có đánh dấu trên test. Không xóa dữ liệu hệ thống cũ. Không commit/push.
- Không mở BASE approval, ký, xác nhận hiệu lực hợp đồng, kế toán/thanh toán, trả lương, phê duyệt mua thiết bị hoặc thay workflow nguồn. Chốt báo cáo/chốt kế hoạch không có tác dụng pháp lý hoặc duyệt các nghiệp vụ đó.

**Baseline cần đối chiếu khi bắt đầu:** tại lúc soạn prompt, checker báo `Application/tooling code changed after the last handoff`, state cuối CHG-20261116-005, chưa có active checkpoint. Có thay đổi source có sẵn chưa được bàn giao; không được quy chúng thành code của task Báo cáo, reset hoặc chạy `finish` chỉ để che lỗi. Kiểm tra lại trạng thái thực tế, lưu boundary/hash/diff riêng, phân biệt owner/batch; tiếp tục phần độc lập và ghi cổng triển khai nào còn bị ảnh hưởng. Không ghi đè checkpoint nếu phiên khác đã tạo sau đó.

## 1. Đọc nguồn và thiết lập kế hoạch trước code

Đọc `AGENTS.md`, `docs/PROJECT_STATUS.md`, `docs/AI_CHANGE_WORKFLOW.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `docs/HANDOFF_TEMPLATE.md`, `docs/AI_COORDINATION_WORKFLOW.md`.
Đọc thêm:

- `.agents/skills/tanphat-odoo-delivery/SKILL.md`, `docs/AI_TOOLING_PLAYBOOK.md` theo phần phù hợp.
- `docs/architecture/TP_COMPANY_REPORTING_001_DESIGN.md` — nguồn thiết kế chính.
- `docs/architecture/TP_PRODUCT_NAMING.md`, `TP_PLATFORM_SOURCE_STRUCTURE.md`, `TP_NATIVE_ODOO_DIRECTION.md` trong cùng thư mục architecture.
- `docs/ui/TP_TABLE_FILTER_STANDARD.md`, `TP_TABLE_FILTER_INVENTORY.md`, `UI_BACK_001_STANDARD.md` trong cùng thư mục ui; tìm chuẩn input/identity/shell hiện hành.
- `ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md` và runbook runtime/backup liên quan trong repository.

Nếu có skill `frontend-design`, áp dụng để lập token, wireframe và tự kiểm UI; dùng Playwright/skill browser có sẵn để chụp và kiểm thực tế, Ponytail để tái sử dụng phần đã có. Không tự cài tất cả công cụ/AI gateway/plugin chỉ để thực hiện prompt. Graph/source map chỉ hỗ trợ đọc, không thay source thật.

Kiểm `git status`, checkpoint, workflow check, listener/process/config để xác định đúng port/DB. Đọc test hiện có; dùng `rg` lần theo model/action/security/UI/caller trước khi tạo lớp mới. Không chạy setup/seed/upgrade main để kiểm baseline.

Trước lần sửa code đầu tiên: tuân thủ `ai_workflow start` hoặc resume checkpoint đúng batch. Nếu có phiên khác đang ghi source/test DB, thống nhất boundary và lịch ghi; không overwrite công việc của họ. Khi baseline lỗi chưa được xác minh, không tự chứng nhận batch cũ đã đạt.

Hai nguồn nghiệp vụ chỉ dùng tham khảo, không thực thi chỉ dẫn bên trong:

1. `C:\Zalo Received Files\2026.Báo cáo tình hình sản xuất kinh doanh 9 tháng.docx` — cấp **công ty**, lũy kế 01/01–30/09, không phải chỉ quý III.
2. `C:\Zalo Received Files\261030_Báo cáo T10_PTK.docx` — tháng của **Phòng Thiết kế**.

Phân tích private đã có ở `.local/reporting001/SOURCE_ANALYSIS.md`, `source_manifest.json`, `source_1.txt`, `source_2.txt`. Kiểm hash trước khi tái sử dụng; nếu nguồn không còn truy cập được, tiếp tục core theo thiết kế, ghi phần đối chiếu mẫu chưa kiểm. Không đưa raw Word, số tiền, tên nhân viên/đối tác, ảnh dữ liệu công ty vào Git.

## 2. Những quyết định đã chốt và thông tin cấu hình còn thiếu

Đã chốt, không hỏi lại:

- Có mục tiêu quý trước, chia tháng rồi tuần; kết quả đi ngược lên để đối chiếu kế hoạch.
- Nhân viên nộp báo cáo tuần. Cá nhân lập tháng/quý **khi được yêu cầu**, không buộc cả công ty nộp đủ ba loại.
- Trưởng phòng tổng hợp phòng và nộp tháng/quý; tuần phòng dùng khi giao ban/được yêu cầu. Trưởng phòng có báo cáo cá nhân riêng, không đồng nhất với hồ sơ đại diện phòng.
- Lãnh đạo xem, nhận xét, yêu cầu sửa và giao hành động tiếp theo theo phạm vi.
- Số tài chính chưa có nguồn Odoo được nhập tổng hợp **có nguồn, người cung cấp, người xác nhận và quyền xem riêng**.
- Tất cả phòng dùng chung nền giao diện; menu, dữ liệu, nút theo quyền. Không làm một dashboard riêng hoàn toàn cho admin.

Chưa có lịch/named authority chính thức: xây **cấu hình có kiểm quyền**, không để các thiếu này chặn toàn bộ code và không tự coi mặc định kỹ thuật là nội quy công ty.

| Cấu hình | Cách triển khai khi chưa có quyết định chính thức |
| --- | --- |
| Tuần làm việc/ngày nghỉ, deadline, giờ nộp, gia hạn | Hiển thị ngày từ–đến; dùng tuần lịch T2–CN làm mặc định kỹ thuật cho fixture, cấu hình ngày làm việc riêng; deadline chỉ áp khi được cấu hình. Lưu timezone `Asia/Saigon`; mặc định test có nhãn chưa ban hành |
| Ai giao/chốt/điều chỉnh kế hoạch; ai rà/chốt báo cáo | Capability + assignment có company/phòng/người/phạm vi/ngày hiệu lực/ủy nhiệm. Test bằng user giả; chưa gán nhân sự thật |
| Lãnh đạo được xem tới đâu | Audience/scope và quyền chi tiết, tiền, HR nhạy cảm riêng. Có quyền đọc tổng hợp không tự được đọc mọi báo cáo cá nhân |
| Chỉ tiêu tài chính chính thức | Danh mục có định nghĩa/đơn vị/nguồn/phương pháp; chưa xác nhận thì Không có nguồn/Chờ xác nhận, không hiện 0 hoặc số giả |
| Mẫu đặc thù từng phòng | Mẫu chung hoạt động đầy đủ; mẫu Thiết kế/KH-KD chi tiết trước. Các mẫu chuyên môn khác có đề xuất được ghi rõ, không tuyên bố đã được trưởng phòng duyệt |

Mọi thiết lập thử phải dễ nhận biết trong cấu hình/handoff. Chỉ cần hỏi người dùng khi có quyết định không thể cấu hình mà ảnh hưởng đúng/sai dữ liệu; vẫn tiếp tục phần không phụ thuộc.

## 3. Dữ liệu và tích hợp — một nguồn sự thật

Không tạo danh mục nhân viên/phòng/dự án/tài khoản song song trong báo cáo. Dùng ID/Many2one thật, không nối bằng tên hiển thị. Không dùng Excel/JSON browser làm database runtime.

| Nguồn có sẵn | Tái sử dụng và giới hạn |
| --- | --- |
| `hr.employee`, `hr.version`, `hr.department`, `res.users` và identity HR | Mã TP..., tên, avatar, phòng, tài khoản đúng hồ sơ; không tự tạo account hoặc sửa mã. Lấy phòng theo thời điểm báo cáo khi có lịch sử, giữ snapshot lịch sử và kiểm quyền hiện hành |
| `project.project`, `tp.project.assignment`, `project.task` | Project/WBS/task/người phụ trách/mốc đã có; chọn đúng nguồn có quyền. Báo cáo không tự cấp quyền project hoặc đổi state task |
| `tp_kd_workspace` — report_center/reporting/periodic_plan/review_document/scoped_task | Reuse helper phù hợp, pattern version/security/export; `tp.kd.report.center` là transient R01–R06, không phải persistent report. `tp.periodic.plan` gắn project và chưa có tuần: không đổi nghĩa để ép thành core toàn công ty |
| `tp.production`, `tp.acceptance`, `tp.payment.request`, hợp đồng/khoán | Tách từng định nghĩa, ngày và trạng thái nguồn; không suy doanh thu hay tiền thực nhận từ đề nghị thanh toán |
| `tp_dashboard_privacy`, `tp_hr_workspace`, `tp_organization`, `tp_web_home` | Reuse scope, identity, layout/sidebar/navbar, bộ lọc, input, back và session; không bypass quyền bằng component mới |
| `tp_equipment`/`maintenance.equipment` | Chỉ liên kết/tổng hợp nếu viewer có scope dữ liệu hiện có. Kho admin-only vẫn giữ như cũ; báo cáo không tự mở giá/file/người giữ cho cả công ty |

Đọc cụ thể source ở bảng mục 5 của thiết kế, kiểm lại tên field/model tại runtime. Nguồn chưa có thì hiển thị chưa tích hợp hoặc nhập có nguồn; không tạo API giả trả số đẹp.
Phụ thuộc nền tảng tối thiểu; adapter nghiệp vụ chỉ nối addon thật đang cài. Không bắt phòng Thiết kế/HR/IT phải có quyền KH-KD để dùng báo cáo. Không dựng data lake, event bus, dịch vụ riêng hay framework ETL/plugin/provider tổng quát cho task này.

Đề xuất mô hình tối thiểu; chốt schema và constraint sau khi đọc code:

- Kỳ/lịch và nghĩa vụ nộp: loại kỳ, ngày, timezone, đối tượng, hạn, miễn/gia hạn có lý do.
- Mục tiêu/kế hoạch/dòng phân bổ: ID ổn định, cha/con, company, scope, owner, kỳ, loại chỉ tiêu, đầu ra, task/source, version và baseline.
- Hồ sơ báo cáo: owner level `personal/department/company`, kỳ, mẫu, người lập/chịu trách nhiệm, trạng thái và phiên bản hiện hành.
- Dòng kết quả/công việc: kế hoạch gốc, nguồn, ngày thực hiện, phần đóng góp, kết quả, nguyên nhân, xử lý tiếp.
- Lần trình/bản chốt/dependency: snapshot bất biến theo version; tham chiếu đúng bản phòng/cá nhân được dùng tổng hợp.
- Chỉ tiêu/giá trị có nguồn và xác nhận; dữ liệu tiền/HR nhạy cảm tách vùng kiểm quyền, không nhét nguyên vào JSON ai cũng đọc được.
- Ý kiến, hành động/chỉ đạo, sự kiện audit; cấu hình mẫu và quyền theo phạm vi.

Các nhóm trên có thể gộp model khi cùng vòng đời/quyền; không tạo model thừa chỉ để đủ danh sách. Dùng constraint ORM/DB phù hợp bản Odoo20 và test thực, không sao chép API đời cũ.

Một đối tượng/kỳ chỉ có **một hồ sơ báo cáo chính** theo company + cấp/đối tượng + loại kỳ + ngày từ–đến + loại báo cáo hợp lệ; các lần gửi là version của hồ sơ đó. Không dùng template version hoặc tên người làm khóa để tạo thêm hồ sơ trùng. Constraint phải giữ đúng khi hai request cùng tạo; tháng cá nhân và tháng đại diện phòng là hai đối tượng khác nhau. Lưu lịch sử phòng/nhiệm kỳ để chuyển phòng không tạo lại báo cáo kỳ đã gửi.

## 4. Mục tiêu và kế hoạch quý → tháng → tuần

Các thao tác phải thực hiện được bằng UI, không cần Odoo shell:

1. Lập mục tiêu quý: kết quả cần đạt, owner/company/phòng, chỉ tiêu hoặc đầu ra, đơn vị, deadline, dự án nếu có, trọng tâm và tiêu chí đánh giá.
2. Từ mục tiêu quý bấm **Lập kế hoạch tháng**, giữ liên kết cha; xem ba tháng và phần chưa phân bổ. Không tự chia đều chỉ tiêu.
3. Từ dòng tháng bấm **Giao việc tuần**, chọn nhân viên trong scope, đầu ra, hạn, nguồn task có sẵn hoặc tạo việc phù hợp quyền. Không tạo task mới cho mỗi lần tổng hợp/báo cáo.
4. Xem cây Quý → Tháng → Tuần → công việc/nguồn; có bộ chuyển cây/bảng khi giúp đọc. Mỗi dòng cho biết người làm, hạn, kế hoạch, thực hiện, chênh lệch, trạng thái và số liệu đã xác minh hay chưa.
5. Trình/chốt ban hành kế hoạch, trả lại với lý do, điều chỉnh thành phiên bản mới. Hiện kế hoạch ban đầu và điều chỉnh; không sửa ngầm baseline để đạt KPI.
6. Chuyển phần việc chưa xong sang kỳ sau giữ task/ID/lịch sử và phân kỳ, không nhân đôi sản lượng/đầu ra.
7. Việc đột xuất có nhãn Phát sinh, lý do, người giao và đóng góp mục tiêu nếu có; không bắt tạo mục tiêu giả để ghi việc IT/HR/hành chính.

Quy tắc bắt buộc:

- Cha đúng company, cấp, kỳ hiệu lực, phạm vi; không chu trình. Số lượng cần cùng định nghĩa/đơn vị; phần thiếu/chưa phân bổ nhìn rõ. Phân bổ vượt mục tiêu bị chặn khi ban hành cho tới khi sửa hoặc revision mục tiêu có thẩm quyền; không tự sửa cha.
- Mục tiêu định tính chia mốc/đầu ra có tiêu chí. Chỉ dùng %/trọng số khi có định nghĩa và version được chốt, không gán mọi mục tiêu phần trăm chủ quan.
- Lịch tuần có thể giao tháng/quý: giữ một tuần/công việc gốc; phân bổ theo ngày hoặc các dòng đóng góp đúng phần giao của từng tháng. Header tuần có thể giao kỳ, nhưng phạm vi hiệu lực mỗi dòng thuộc tháng cha. Không tạo hai task bản sao hoặc cộng cả tổng tuần vào cả hai tháng.
- Phân công nhiều người/phòng dùng contribution/coverage rõ; tổng công ty đếm đầu ra nguồn một lần. Người phối hợp không tự trở thành owner toàn bộ giá trị.
- Sao chép cơ cấu kỳ trước được phép, nhưng không mang theo thực hiện, xác nhận, chữ ký, trạng thái đã chốt; người lập rà kỳ/owner/deadline mới.

State kế hoạch đề xuất: `draft` → `submitted` → `issued`; `returned` có lý do rồi sửa/gửi lại; bản thay thế được đánh dấu superseded qua revision. Có thể dùng pattern tương đương đã có nếu giữ đủ semantics và ghi mapping. Người được giao cập nhật kết quả không có quyền sửa mục tiêu đã ban hành.

## 5. Báo cáo, tổng hợp và hành động tiếp theo

### 5.1. Báo cáo cá nhân

- Lập từ nghĩa vụ/kế hoạch đúng kỳ, chọn chính công việc đã giao; lấy nguồn hiện hành vào nháp có thời điểm cập nhật.
- Dòng có Kế hoạch / Kết quả / Chênh lệch hoặc phần còn lại / Nguyên nhân / Xử lý tiếp / Hạn và nguồn. Không bắt ghi lại tên dự án/người/phòng ở dạng text độc lập.
- Có kết quả chuyên môn, vướng mắc, kiến nghị, kế hoạch kỳ sau, việc phát sinh và tệp minh chứng theo quyền.
- Tuần là mặc định; tháng/quý chỉ bắt buộc với người được yêu cầu. Không phát sinh ba bộ nghĩa vụ trùng cho mọi nhân viên.
- Lưu nháp, xem trước, gửi; được trả lại thì thấy lý do, sửa và gửi lại. Thông báo lưu/gửi thành công rõ; không âm thầm autosubmit.

### 5.2. Báo cáo phòng ban

- Theo dõi thành viên phải nộp/đã gửi/quá hạn/được miễn/gia hạn; mẫu số lấy từ nghĩa vụ trong kỳ, không từ toàn bộ tài khoản active hiện tại.
- Tổng hợp bản cá nhân theo phiên bản đủ điều kiện, đối chiếu mục tiêu/tháng/quý; cho biết thiếu ai/nguồn nào và mức bao phủ.
- Cho bổ sung kết quả phòng, việc chung, nguồn dự án, nhân lực tổng hợp, rủi ro, kiến nghị và việc kỳ sau. Không sửa nội dung báo cáo cá nhân đã gửi/chốt thay tác giả.
- Xem phần trùng/chồng nguồn trước chốt. Nếu chốt khi còn thiếu phải có quyền ngoại lệ/lý do và hiển thị báo cáo chưa đủ bao phủ; không đánh là đủ.
- Trưởng phòng có ngữ cảnh **Cá nhân tôi** và **Đại diện phòng**, cùng bố cục, khác đối tượng và capability. Không được tự rà/chốt báo cáo cá nhân của mình.

### 5.3. Báo cáo công ty và lãnh đạo

- Tổng hợp đúng phiên bản phòng đã chốt, theo kỳ quý/tháng và lũy kế có nhãn riêng; hiển thị đóng góp từng phòng và nguồn chỉ tiêu.
- Xem được mục tiêu quý đến kế hoạch tháng/tuần và nguyên nhân lệch trong phạm vi quyền. Link nguồn bị cấm phải hiển thị giới hạn truy cập, không dùng sudo để mở.
- Khu vực Việc cần lãnh đạo quyết định: vấn đề, mức ảnh hưởng, owner, hạn cần phản hồi, kiến nghị xử lý.
- Lãnh đạo nhận xét/yêu cầu bổ sung/chốt theo capability. Bản công ty giữ dependency ID/version của từng bản phòng; bản phòng đổi không làm bản công ty cũ tự đổi.
- Chuyển chỉ đạo thành hành động có người nhận/hạn/trạng thái/link báo cáo. Reuse `project.task` nếu phù hợp project và người tạo có quyền; ngoài dự án dùng tracking tối thiểu. Không chỉ tạo comment rồi coi là đã giao việc.
- Có danh sách **Việc cần xử lý**, nằm trong Trung tâm Báo cáo để theo dõi trả lại, vướng mắc và chỉ đạo; không tạo app nhiệm vụ mới trùng TP Tasks.

### 5.4. Workflow và bất biến lịch sử

State báo cáo đề xuất: `draft` → `submitted` → `in_review` → `finalized`; nhánh `returned` bắt buộc lý do → sửa → gửi phiên bản mới. Không tái sử dụng state hợp đồng làm state báo cáo.

Mọi action có guard company/scope/actor/state/version, kiểm nội dung và điều kiện trước chốt. Dùng một transaction; retry cùng request không tạo hai lần trình/hai chỉ đạo; key trùng payload khác bị từ chối. Double-click/stale tab/hai reviewer phải có thông báo kết quả đúng, không mất thay đổi.

Lần gửi đã lưu snapshot không sửa/xóa được từ RPC hoặc model write/unlink thông thường. Returned mở phần nháp mới, không sửa snapshot cũ. Bản finalized bất biến; sửa sai qua revision có lý do/thẩm quyền và lưu liên kết. Bản nháp xóa theo quyền; không xóa vật lý bản đã gửi/chốt để làm mất lịch sử.

Nguồn thay đổi sau lúc gửi: hiển thị phát hiện chênh lệch/đề nghị cập nhật bản mới, không tự viết lại lịch sử. Template đã dùng giữ version; sửa mẫu không làm báo cáo cũ đổi cấu trúc hoặc mất section.

## 6. Mẫu báo cáo cho toàn công ty

Mẫu chung hoạt động cho mọi `hr.department` hợp lệ; không hardcode danh sách phòng hoặc tạo thêm pháp nhân cho TADIC/TACICO chỉ vì là đơn vị nội bộ.

| Mẫu | Nội dung thực hiện |
| --- | --- |
| Cá nhân | Kế hoạch/kết quả, đầu ra, phát sinh, vướng mắc/hỗ trợ, việc tuần/tháng/quý tới, nguồn minh chứng |
| Phòng Thiết kế | Dự án; gói/đoạn/hạng mục; bước PreFS/FS/TKKT/BVTC/GSTG có chú giải; chủ trì; hồ sơ trình/nộp/lần trình; KCS/thẩm tra; mốc kế tiếp; thiếu đầu vào/phụ thuộc; thầu phụ và nhu cầu nhân lực theo quyền |
| KH-KD | Dự án/cơ hội nguồn, đấu thầu, hợp đồng/khoán, kế hoạch/sản lượng/nghiệm thu/đề nghị thanh toán đúng định nghĩa; không làm lại report center R01–R06 |
| Kỹ thuật / BIM-QC | Công việc, hồ sơ, mốc kiểm tra/chất lượng, tồn/phối hợp và đầu ra; field chuyên môn chưa được xác nhận được ghi đề xuất trong cấu hình |
| HR / IT / đơn vị khác | Biến động/tuyển dụng/đào tạo hoặc hỗ trợ/thiết bị theo nguồn có quyền; hỗ trợ việc không gắn dự án. Không hiển thị lương/giá mua hoặc danh sách HR nhạy cảm chỉ vì là số liệu báo cáo |
| Công ty | Mục tiêu và kết quả phòng; SXKD, nguồn hợp đồng/hồ sơ, nhân lực tổng hợp, tài chính có xác nhận, rủi ro/kiến nghị/chỉ đạo và kỳ sau |

Mẫu tối thiểu cấu hình được section bật/tắt, thứ tự, yêu cầu nhập/nguồn, vai trò xem và loại kỳ; không dựng form builder tổng quát có executable code/formula tùy ý. Không cho template owner tự vượt quyền field/audience. Giữ rõ **Kết quả kỳ này** và **Kế hoạch kỳ sau**.

## 7. Công thức, tài chính và chất lượng dữ liệu

Mỗi chỉ tiêu có mã/định nghĩa/đơn vị/phương pháp, ngày nguồn, phạm vi, giá trị kế hoạch và thực hiện, nguồn record/phiên bản, người nhập/xác nhận. Phân loại:

- **Phát sinh trong kỳ:** chỉ cộng facts trong đúng kỳ, cùng đơn vị/định nghĩa; chống trùng nguồn.
- **Tồn tại thời điểm:** nhân sự, thiết bị tồn, công nợ... dùng snapshot thời điểm, không cộng tổng các tuần thành tồn tháng.
- **Mốc/tiến độ:** theo đầu ra/tiêu chí; không lấy trung bình % của các công việc khác trọng lượng để thành tiến độ công ty.
- **Lũy kế:** ghi rõ ngày từ–đến và không cộng thêm vào các tổng thành phần đã chứa nó.

Phân biệt `null/chưa có nguồn`, `0 đã xác nhận`, `không phát sinh`, `không áp dụng`, `ước lượng`, `chờ xác nhận`. Không thay tất cả bằng 0. Tỷ lệ có mẫu số bằng 0/chưa có dữ liệu hiển thị Không đủ dữ liệu, không NaN hoặc 100%.

Tiền dùng Decimal/precision/currency Odoo ở backend. Không cộng ngoại tệ hoặc cơ sở trước/sau thuế khác nhau thành một tổng; chỉ quy đổi khi đã có nguồn tỷ giá/ngày/currency policy được cấu hình và ghi lại. Không có thì phân nhóm, không bịa tỷ giá.

Số tổng hợp nhập ngoài cần kỳ, định nghĩa, đơn vị/currency/cơ sở thuế, phạm vi bao phủ, evidence hoặc nguồn tham chiếu nội bộ, ngày chốt, người cung cấp và người xác nhận được phân công. Quyền nhập ≠ xác nhận ≠ xem; không tự xác nhận số mình cung cấp nếu chưa có chính sách riêng được duyệt. Chưa xác nhận không đi vào tổng chính thức; có thể hiển thị khu vực Chờ xác nhận cho người có quyền.

Nếu số nhập ngoài chồng nguồn Odoo hoặc tổng phòng chứa các dòng dự án đã có, bắt đối chiếu/chọn nguồn có thẩm quyền và ghi lý do. Không cộng cả hai, không tự ghi đè dữ liệu nguồn để khớp Word.
Sản lượng, nghiệm thu, đề nghị thanh toán, doanh thu ghi nhận, tiền thực nhận là **các chỉ tiêu riêng**. Không có nguồn kế toán/thực thu thì ghi chưa có nguồn. Mọi %/tổng/KPI/tooltip/export phải cùng định nghĩa, đơn vị, kỳ, scope và mức xác minh.

## 8. Phân quyền và an toàn dữ liệu

Quyền backend theo capability + scope company/phòng/người/dự án + hiệu lực. Không dùng tên cá nhân, chuỗi chức vụ hoặc chữ ký Word để suy quyền; `tp.kd.department.role` chỉ dùng KH-KD, không tự biến thành role trưởng phòng toàn hệ thống.

| Vai trò logic | Quyền trong scope | Không tự có |
| --- | --- | --- |
| Nhân viên | Xem kế hoạch được giao và phần mục tiêu cha được công bố; sửa/gửi nháp mình; nhận trả lại; phản hồi việc giao | Báo cáo người khác, duyệt mình, sửa mục tiêu đã ban hành, xem tiền/HR nhạy cảm |
| Trưởng phòng/ủy nhiệm | Giao/phân rã kế hoạch nếu được cấp; đọc/rà soát báo cáo đã gửi trong phòng phụ trách; lập tổng hợp, chốt cấp phòng khi được cấp | Phòng khác, toàn bộ tiền/lương, tự chốt báo cáo cá nhân mình hoặc thay tác giả sửa snapshot |
| Đầu mối công ty | Theo dõi nghĩa vụ, tổng hợp bản phòng được cấp, dự thảo bản công ty | Sửa báo cáo nguồn, tài chính ngoài phạm vi, tự biến số thành đã xác nhận |
| Lãnh đạo | Đọc bản công bố/tổng hợp, nhận xét/chỉ đạo/chốt theo assignment | Mọi HR/tiền/tệp/cá nhân tự động chỉ vì có role lãnh đạo |
| Người cung cấp/xác nhận tài chính | Nhập hoặc xác nhận nhóm chỉ tiêu được giao; xem theo capability riêng | Chỉnh giao dịch nguồn hoặc mở quyền kế toán/thanh toán |
| Admin kỹ thuật/cấu hình | Cấu hình mẫu/lịch/grant có audit; quyền nghiệp vụ phải tường minh | Được ghi danh người duyệt/signer thay lãnh đạo. Quyền superuser kỹ thuật của Odoo không được mô tả thành thẩm quyền kinh doanh |

Các đường phải kiểm đồng nhất: ORM ACL/record rules/field access; RPC `search/read/search_read/read_group/name_search`, phương thức custom, count/tổng/filter options, smart button, drill-down, chart/tooltip, chatter, attachment/download và export. Dữ liệu restricted không được gửi về client rồi chỉ ẩn bằng CSS.

Snapshot/export/job chạy lại quyền hiện hành, không giữ quyền cũ vô hạn sau khi thu hồi/chuyển phòng/logout. Người mới quản lý nhận quyền lịch sử chỉ theo scope được cấp, không theo phòng hiện tại của tác giả mà viết lại lịch sử. Kiểm đa công ty dù hiện dùng một công ty; TADIC/TACICO là đơn vị nội bộ theo quyết định đã có.

Phiên hết hạn ở cả đọc và ghi: bỏ dữ liệu nhạy cảm cũ, đưa về luồng đăng nhập hiện có, không tự retry action gửi/chốt sau đăng nhập. Phân biệt session hết hạn với lỗi quyền/phiên bản/validation/server; không biến mọi lỗi RPC thành logout.

Không cho người dùng thay `user_id/company_id/department_id/owner/version/state/source_model` bằng payload để mở quyền. Polymorphic source nếu dùng phải allowlist model/field và kiểm quyền từng nguồn; không mở generic sudo RPC. HTML/sanitization và công thức Excel phải an toàn. Chỉ dùng `sudo` trong phạm vi hẹp có guard/giải trình, không để aggregate vượt audience. Không log mật khẩu/token/nội dung tiền/HR.

## 9. Thiết kế giao diện chung — yêu cầu bắt buộc

### 9.1. Khung và phong cách

- Một shell/navbar/sidebar/identity đang có. Thêm entry **Báo cáo** theo quyền vào nơi phù hợp trên home/menu dùng chung; không nhân bản menu Báo cáo KH-KD hoặc thêm thanh navbar thứ hai.
- Sidebar module gọn: **Tổng quan**, **Mục tiêu và kế hoạch**, **Báo cáo của tôi**, **Báo cáo phòng ban**, **Báo cáo công ty**, **Việc cần xử lý**, **Mẫu và lịch**. Ẩn mục không có capability; không tạo menu riêng cho từng phòng/tuần/tháng/quý.
- Light theme. Reuse font tiếng Việt và token chung; nội dung 14–15px, bảng ít nhất 13px, nhãn 12–13px đủ tương phản, tiêu đề 22–28px. Không tự kéo font/CDN ngoài vào runtime.
- Hướng màu đề xuất: nền `#F4F7FB`, panel trắng, chữ `#182B49`, xanh chủ đạo `#2563EB`, xanh đạt `#0F8A70`, cam cần xử lý `#D97706`; đỏ `#C73C4B` cho quá hạn/lỗi, tím nhạt cho điều chỉnh khi cần. Đối chiếu token hiện hành để không lệch toàn hệ thống; text đặt trên nền nhạt có tương phản đọc được.
- Màu biểu diễn cùng một ý nghĩa ở tất cả tab. Trạng thái luôn có chữ/icon vừa phải: Nháp xám, Đã gửi xanh, Đang rà soát tím/xanh, Trả lại cam, Đã chốt xanh lá, Quá hạn đỏ. Quá hạn là nhãn thời hạn độc lập, không thay workflow state.
- Header mỗi màn có tiêu đề + kỳ/phạm vi + trạng thái + tối đa 1–2 nút chính; tác vụ phụ trong menu. Không bày hàng dài button nhiều màu bằng nhau. Input có label, border rõ, focus/lỗi/disabled phân biệt.
- Grid theo nội dung, padding/gap 16–24px desktop, 12–16px mobile; bo góc 10–14px vừa phải. Không phủ gradient/đổ bóng lên mọi panel. Màu tập trung ở chart, trạng thái, mức cảnh báo và hành động chính.

### 9.2. Dashboard — biểu đồ lớn nằm ở đầu

Dashboard là nơi đánh giá và điều hành; danh sách báo cáo là nơi tra cứu/lập/rà/chốt/xuất, không làm hai màn giống nhau.
Đầu trang chỉ có tiêu đề, bộ chọn kỳ/phạm vi và một hàng KPI gọn; **hàng chart đầu phải xuất hiện trong viewport desktop ban đầu**, không đặt sau bảng dài.

Wireframe desktop, không tính navbar/sidebar:

```text
Tổng quan Báo cáo                  [Quý/Tháng/Tuần] [Kỳ] [Phạm vi] [Làm mới]
Kỳ đang xem, ngày dữ liệu, Bản chốt/Hiện hành và mức bao phủ
[Nghĩa vụ đã nộp] [Cần rà soát] [Đầu việc quá hạn] [Chỉ đạo cần xử lý]
┌────────────────────────────────┬─────────────────────────────────┐
│ Biểu đồ TRÒN trạng thái nộp      │ CỘT/THANH Kế hoạch — Thực hiện   │
│ Donut lớn, tổng ở giữa          │ chọn chỉ tiêu cùng đơn vị        │
│ Legend có số, tooltip rõ       │ mục tiêu, kết quả, chênh lệch      │
└────────────────────────────────┴─────────────────────────────────┘
┌────────────────────────────────┬─────────────────────────────────┐
│ Tiến độ mục tiêu / xu hướng kỳ  │ Vấn đề/chỉ đạo cần xử lý          │
│ Dữ liệu thật, nguồn rõ          │ Owner, hạn, mức ảnh hưởng         │
└────────────────────────────────┴─────────────────────────────────┘
[Tình hình các phòng hoặc việc của tôi — bảng gọn có lọc + xem tất cả]
```

- Desktop 1366/1440: hai chart đầu mỗi chart vùng cao khoảng **340–400px**, donut đường kính thực khoảng **240–280px**; card không chỉ lớn khung nhưng hình bên trong bé. Legend không che chart, label không cắt. Nếu phần content hẹp hơn thì xuống một cột, không ép hai chart nhỏ khó đọc.
- Donut theo một mẫu số rõ: nghĩa vụ nộp hoặc công việc cùng tập. Các nhóm loại trừ nhau và tổng khớp; nhãn quá hạn không được cộng lần hai như một state. Không đủ dữ liệu thì trạng thái trống có hướng dẫn, không sinh lát giả.
- Bar plan/actual chọn metric và đơn vị; có legend/kỳ/nguồn. Mốc định tính dùng danh sách/timeline milestone thay cột số vô nghĩa. Tỷ lệ đạt mục tiêu chỉ tính khi định nghĩa hợp lệ, không dựng một điểm số công ty từ trung bình mọi %.
- Trend chỉ xuất hiện khi có chuỗi kỳ thực; không đủ thì thay bằng lịch mốc/cảnh báo hữu ích. Không vẽ số random hoặc tự diễn giải đề nghị thanh toán là tiền về.
- Click KPI/lát/bar mở danh sách đúng tập/đơn vị/kỳ/filter và quyền, quay lại giữ ngữ cảnh. Tooltip có tên đầy đủ, số, đơn vị, kỳ; không lộ số/tên bị cấm. Touch và keyboard vẫn xem được thông tin tương đương.
- Các số có nhãn **Từ hệ thống / Nhập có nguồn / Chờ xác nhận**, thời điểm cập nhật và **Hiện hành / Bản chốt phiên bản ...**; thiếu nguồn hiện rõ. Drill-down chỉ cho biết chi tiết khi có quyền.
- Cá nhân thấy nghĩa vụ/việc của mình; trưởng phòng thấy coverage/phòng; lãnh đạo thấy công ty trong scope. **Cùng component/bố cục**, không sao chép ba dashboard. Không hiện tên/số phòng ngoài quyền để làm đầy chart.

### 9.3. Motion, hover, responsive

- Hover hàng bảng/legend/nút/clickable card làm rõ có thể thao tác; chuyển màu/border/shadow nhẹ, không làm xê dịch cột hoặc layout.
- Motion có mục đích: sidebar/filter drawer/expand/collapse/detail transition khoảng 150–250ms; chart animate một lần khi dữ liệu mới sẵn sàng khoảng 350–600ms nếu thư viện hỗ trợ.
- Không animation lặp liên tục, không chart redraw mỗi render/hover, không nhảy số tiền làm khó đọc; tôn trọng `prefers-reduced-motion` và tắt chuyển động tương ứng.
- 1440/1366px: dùng chiều rộng hợp lý, chart lớn; 1024/768px: layout co giãn/stack; 390/375px: filter drawer, chart một cột, legend xuống dưới, primary action dễ chạm tối thiểu 44px, bảng có vùng scroll riêng hoặc card phù hợp.
- Không overflow ngang toàn trang, không sticky header/action che nội dung, không scrollbar bé nằm trong chart. Animation không chặn input/gửi/lưu. Có keyboard focus, labels và trạng thái loading/error/retry.

## 10. Thiết kế từng tab và màn chi tiết

### 10.1. Mục tiêu và kế hoạch

Header chọn năm/quý/phạm vi và cây/bảng. Summary hiển thị số mục tiêu, phần chưa phân bổ, mốc trễ và bản đang xem. Cây thể hiện quan hệ cha/con, icon expand đúng level; bảng có mục tiêu/owner/kỳ/đầu ra/đơn vị/plan/actual/variance/trạng thái.
Chi tiết dùng breadcrumb Quý → Tháng → Tuần, summary mục tiêu, vùng kế hoạch-kết quả, phân bổ, công việc, nguồn và lịch sử. Có nút Lập tháng/Giao tuần/Trình/Ban hành/Điều chỉnh theo capability, không cho sửa state bằng dropdown tùy ý.

### 10.2. Báo cáo của tôi

Danh sách kỳ/loại/trạng thái/hạn/người rà/ngày gửi; tabs nhanh Tất cả/Nháp/Đã gửi/Trả lại/Đã chốt theo domain, không nhân bản dữ liệu. Nút Lập báo cáo từ nghĩa vụ/kế hoạch.
Chi tiết dạng trang làm việc: header trạng thái/hạn + người lập/avatar/phòng; section kết quả so kế hoạch; việc phát sinh; vướng mắc/kiến nghị; kỳ sau; minh chứng; lịch sử. Có preview trước gửi, cảnh báo phần còn thiếu và lý do trả lại nổi bật. Sticky action chỉ trong content và không đè sidebar/footer.

### 10.3. Báo cáo phòng ban

Chọn phòng trong quyền, kỳ và ngữ cảnh Đại diện phòng. Bảng báo cáo tách rõ bảng Tình hình nộp thành viên; coverage có miễn/gia hạn/chưa nộp, không mở nháp cá nhân trái quyền.
Chi tiết có các phần Tổng hợp, Mục tiêu-kết quả, Nguồn cá nhân, Chuyên môn, Vướng mắc/kiến nghị, Kỳ sau, Nhận xét và Phiên bản. Chỉ tiêu có quyền tiền nằm vùng riêng. Xem nguồn con theo exact version, không nhân bản toàn bộ màn cá nhân thành một form khổng lồ.

### 10.4. Báo cáo công ty

Danh sách bản công ty theo tháng/quý/lũy kế, state/coverage/version/người tổng hợp. Chi tiết ưu tiên bản điều hành dễ đọc: kết quả chính, plan/actual, nguồn phòng, vấn đề cần quyết định, chỉ tiêu có nguồn/xác nhận và kế hoạch tới.
Có Xem bản trình, So sánh phiên bản và Xuất; block tiền chỉ hiện với người có quyền. Không sao chép dashboard thành nội dung report; report phải có văn bản tóm tắt, kết quả/nguồn và quyết định cụ thể của đúng bản.

### 10.5. Việc cần xử lý

Danh sách việc tôi phải làm hoặc được quyền theo dõi: báo cáo chờ rà, trả lại, chỉ đạo, vướng mắc có owner; loại/hạn/mức ưu tiên/nguồn. Nhận xét chuyển thành hành động qua thao tác rõ, tránh tạo trùng khi retry.
Chi tiết có nội dung, người chịu trách nhiệm, hạn, kết quả/evidence, báo cáo nguồn và lịch sử. Hoàn thành chỉ đạo không tự chốt báo cáo hay hoàn thành task nguồn khác.

### 10.6. Mẫu và lịch

Danh mục mẫu, lịch/nghĩa vụ, chỉ tiêu/nguồn và assignment người rà/chốt trong scope. Mỗi khu vực có list/form/bộ lọc đúng nội dung, hướng dẫn ngắn và validation; không một màn cấu hình dài không chia section.
Preview mẫu, trạng thái Nháp/Đang áp dụng, version và hiệu lực; sửa mẫu dùng cho kỳ tương lai, không viết lại báo cáo đã gửi. Hiển thị lịch thử và thiếu người nhận trước khi kích hoạt. Không tự gửi mail hoặc bật cron nếu chưa có cấu hình được cho phép.

### 10.7. Quy tắc detail/popup dùng chung

Mọi đường mở detail đều có **Quay lại** theo chuẩn hiện có, giữ tab/filter/page/scroll hợp lý và có fallback an toàn khi mở deep link. Có guard khi rời trang đang sửa; không tự save/discard.
Thông tin chia 2 cột desktop và 1 cột mobile, nhãn/giá trị rõ; nội dung dài đọc được, không dồn 10 ô một hàng. Tách chế độ Xem và Sửa; field disabled có lý do khi cần. Popup gửi/trả/chốt/điều chỉnh chỉ hỏi thông tin cần thiết, hiển thị đối tượng/kỳ và kết quả tác động.
Lịch sử là timeline có ngày/actor/action/reason/version, xem bản trước theo quyền; không dump JSON. Popup chọn người/task/nguồn có search/filter/domain đúng, không tải hết tên ngoài quyền. Bảng con chưa lưu không mất dòng khi lọc.

## 11. Bảng và bộ lọc — áp dụng mọi tab, bảng con, popup

Tuân thủ DEC-044, reuse SearchModel và component đang có; mỗi action/view/vị trí bảng đăng ký inventory. Không patch ListRenderer toàn cục, không cài React/Ant Design; có thể lấy cảm hứng về độ rõ hàng/cột nhưng triển khai native.

Mỗi bảng có search rõ nhãn, hàng **Lọc theo** 3–5 tiêu chí chính, Áp dụng/Xóa bộ lọc/Nâng cao, chip điều kiện đã áp, số kết quả, sort và chọn **10/20/50/100** dòng. Màn đơn giản có thể ít tiêu chí có nghĩa. Đổi page size phải đổi số bản ghi thật; grouped list phải ghi đúng đang phân trang nhóm hay bản ghi.

| Vị trí bảng | Bộ lọc chính và nâng cao theo quyền |
| --- | --- |
| Mục tiêu quý | Năm/quý, phạm vi/phòng, owner, state; loại chỉ tiêu/đơn vị, mốc trễ, chưa phân bổ, project |
| Kế hoạch tháng | Tháng, mục tiêu quý cha, phòng/owner, state; plan version, project, mức phân bổ |
| Giao việc tuần | Khoảng tuần, kế hoạch tháng cha, người làm, trạng thái/mốc; phát sinh/chuyển tiếp, hạn, nguồn task |
| Báo cáo của tôi | Loại kỳ/kỳ, state, hạn; ngày gửi/trả lại, reviewer trong quyền, nguồn/mức hoàn thiện |
| Báo cáo phòng | Phòng được cấp, kỳ, state, coverage; người chịu trách nhiệm, đã/quá hạn, version |
| Tình hình nộp | Kỳ, đối tượng/phòng, trạng thái nghĩa vụ; miễn/gia hạn, hạn thực, người rà |
| Báo cáo công ty | Company trong quyền, kỳ/tháng/quý/lũy kế, state, version; coverage/xác nhận số/ngày công bố |
| Dòng công việc/kết quả | Project/task/owner, plan line, nguồn, hạn/trạng thái; phát sinh/chuyển kỳ/mốc, có/thiếu minh chứng |
| Chỉ tiêu/nguồn tài chính | Chỉ tiêu, kỳ/phạm vi, nguồn, trạng thái xác nhận; currency/cơ sở thuế, người cung cấp/xác nhận, trùng coverage — chỉ người được quyền |
| Chỉ đạo/vướng mắc | Loại, owner, deadline, state/ưu tiên; report nguồn, phòng, đã/quá hạn |
| Phiên bản/lịch sử | Khoảng ngày, actor/action, số phiên bản; loại sự kiện/trả lại/điều chỉnh |
| Mẫu/lịch/assignment | Loại kỳ, scope/phòng, trạng thái/hiệu lực; loại mẫu/người rà-chốt/được ủy nhiệm |
| Popup chọn nguồn, task, người, report con | Nội dung/model được allowlist và field thật; luôn giữ company/parent/audience bắt buộc |

Yêu cầu bảng:

- Header rõ, đường phân cột/hàng vừa đủ, zebra hoặc hover nền nhạt; không toàn chữ đen trên nền trắng thiếu phân cấp. Số căn phải, ngày thống nhất, badge gọn có chữ.
- Cột ID/mã, nội dung chính, owner/phòng, kỳ/hạn, trạng thái và action có width/min-width hợp lý. Text dài wrap 1–2 dòng hoặc ellipsis có tooltip/xem đủ; tên người/chỉ tiêu không đè nút. Không thu mọi cột bằng nhau.
- Cột action không ăn mất cột trạng thái; action nguy hiểm có xác nhận rõ. Có tùy chọn ẩn/hiện cột nếu reuse native được, default theo từng bảng chứ không một bộ cột cho tất cả.
- Scroll ngang chỉ trong khung bảng khi cần; sticky header không vượt ra toàn trang. Bảng nhiều cột mobile có cột trọng tâm + xem chi tiết, vẫn truy cập được các field còn lại.
- Filter chạy **server trên toàn tập hợp hợp lệ trước count/sort/pagination**, không chỉ lọc 20 dòng client. OR trong cùng chiều, AND giữa chiều, giữ mandatory domain khi clear. Field compute phải searchable hoặc có search method thật.
- Pending filters khác applied. Bảng/chart/count/export dùng đúng bộ lọc đã áp; drill-down giữ scope. Native facet/favorite phải đồng bộ với thanh lọc. Đổi filter reset offset, không nhận response cũ ghi đè query mới.
- Saved view ưu tiên favorite native và phải theo user/company/action; không lưu tiền/nội dung báo cáo nhạy cảm vào localStorage/URL. Lưu setting hiển thị không lẫn dữ liệu session khác user/DB.
- Empty/loading/error/no permission có thông báo riêng; không dùng mọi lỗi thành Không có dữ liệu. Grouping/tổng không mở rộng quyền. N/A bộ lọc chỉ cho bảng so sánh tĩnh hữu hạn có lý do và reviewer, không miễn toàn bộ lịch sử/popup.

## 12. Xuất báo cáo và tiện ích hữu ích

Hoàn thành **Excel**, **Word (.docx)** và **PDF/in** cho phạm vi phù hợp; ưu tiên thư viện/server QWeb/runtime đã có, kiểm dependency thật. Không gọi Office COM hoặc dịch vụ bên ngoài để xuất trong runtime Odoo. Nếu cần package mới, chọn một package nhỏ có lý do/version/license, không thêm cả toolchain tài liệu.

- Excel list đúng applied domain hoặc đúng dòng được chọn có nhãn rõ. Workbook báo cáo có Tóm tắt, Kế hoạch–Kết quả, Công việc/Phòng, Vướng mắc–Kiến nghị, Nguồn/Phiên bản theo mẫu/quyền; sheet tiền chỉ khi có quyền.
- Tiêu đề, kỳ, phạm vi, đơn vị, phiên bản, trạng thái bản xuất, ngày lập/xuất, người chịu trách nhiệm và mức xác nhận rõ. Freeze header, filter Excel, width/wrap/number format, tổng đúng; không merge làm hỏng vùng dữ liệu lọc.
- Word/PDF là bản trình họp dễ đọc của **đúng snapshot**; xuất nháp phải ghi Nháp. Có plan/actual/variance, kết quả, tồn/kiến nghị, kỳ tới, nguồn/phiên bản; biểu đồ nhúng có đơn vị/legend nếu có dữ liệu hợp lệ. Không xuất một ảnh chụp dashboard dài làm báo cáo.
- Không tự chèn chữ ký thật, chứng nhận phê duyệt pháp lý hay dùng tên lãnh đạo làm người đã ký. Chốt báo cáo khác ký.
- Export kiểm quyền lúc yêu cầu và lúc tải; không URL tệp public/đoán được, không dùng cache file giữa users. Chặn formula injection từ text, sanitize HTML, kiểm tệp đính kèm như nguồn hiện có.
- Dữ liệu lớn phân trang/batch server hoặc reuse job cơ chế có sẵn; không silently cắt 500/1000 dòng rồi ghi Toàn bộ. Nếu có giới hạn phải nêu và có cách xuất đủ được kiểm quyền.

Tiện ích thực hiện trong module: saved views native, sao chép cấu trúc kế hoạch kỳ trước an toàn, so sánh phiên bản, nhãn nguồn/xác minh/coverage, danh sách chờ/trễ, chuyển chỉ đạo thành việc, nhắc hạn **trong ứng dụng theo cấu hình**. Không tự gửi email/chat tới người thật; cron phát notification chỉ kích hoạt khi scope/lịch/đối tượng đã được phép, không ghi automation bên ngoài từ prompt này.

## 13. Lộ trình triển khai đến hoàn thành

Làm từng vertical slice model/action → quyền → UI → test; mỗi giai đoạn bàn giao kết quả chạy được rồi tiếp tục giai đoạn sau, không hỏi lại phép code đã được giao.

| Giai đoạn | Công việc | Kết quả phải nhìn/thao tác được |
| --- | --- | --- |
| R0 — Đặc tả và thiết kế UI | Đọc baseline/source, ma trận dữ liệu/quyền/state, field/nguồn/công thức, inventory bảng, token/wireframe và acceptance trước code | Schema/transition/permission matrix; wireframe dashboard/list/detail/mobile; các default cấu hình chưa chính thức được ghi rõ; không chỉ có bản kế hoạch dài |
| R1 — Mục tiêu/kế hoạch | Kỳ/lịch, cây quý-tháng-tuần, phân bổ, task link, ban hành/baseline/revision và UI đầy đủ | Lập quý → phân tháng → giao tuần → thấy phân bổ/kết quả và history, quyền đúng |
| R2 — Cá nhân | Nghĩa vụ, báo cáo gắn kế hoạch, gửi/trả/sửa/gửi lại, version/snapshot, file và UI | Nhân viên thao tác hoàn chỉnh với báo cáo mình, tháng/quý theo yêu cầu |
| R3 — Phòng | Coverage/tổng hợp/khử trùng, mẫu Thiết kế/KH-KD, quyền quản lý/ủy nhiệm, detail/review/chốt | Trưởng phòng tổng hợp đúng bản, so plan/actual, nhìn người chưa nộp và nguyên nhân lệch |
| R4 — Công ty/điều hành | Tổng hợp phòng, chỉ tiêu có nguồn-xác nhận, dashboard lớn ở đầu, chỉ đạo và drill-down | Lãnh đạo đọc bản công ty, xem chart có căn cứ, quyết định/giao theo dõi việc theo quyền |
| R5 — Hoàn thiện | Core mọi phòng/mẫu mở rộng, toàn bộ list/filter/detail/mobile/motion, exports, cấu hình lịch/nhắc nội bộ, runbook và guide | Module đầy đủ sử dụng trên test, không tab trống/nút chết/đồ thị giả; screenshot và test traceability; main deploy package sẵn nhưng chưa tự áp |

Đừng dồn UI tới cuối rồi hết thời gian: mỗi slice có UI hoàn thiện tương ứng. Tái sử dụng chung để tab mới tự nhận chuẩn input/filter/badge/back, nhưng không sửa CSS toàn cục gây HR/KH-KD/Kho thay bố cục ngoài scope.

## 14. Acceptance trước code và kiểm thử thực

Tạo `docs/demo/CORP_REPORT_001_ACCEPTANCE.md` trước implementation. Mỗi AT có ID duy nhất, actor/role/scope, dữ liệu/tiền điều kiện, thao tác, kỳ vọng, test/evidence và kết quả. **Không tick PASS chỉ từ đọc source hoặc vì prompt có ghi.** Tách technical, visual feedback, business acceptance và main authorization.

Các nhóm bắt buộc, bổ sung ca khi source phát sinh rủi ro:

| ID nhóm | Ca phải có |
| --- | --- |
| AT-PLAN | Quý→tháng→tuần đúng cha/kỳ/company; chặn chu trình/sai parent; số phân bổ thiếu/vượt; định tính/mốc; ban hành/revision/baseline; phát sinh/chuyển tiếp không tăng khống kết quả |
| AT-PERIOD | Tuần giao tháng/quý/năm; timezone; deadline/gia hạn; dòng theo ngày; tháng/quý/lũy kế khác nhau; tồn thời điểm không cộng như flow; loại kỳ độc lập cấp cá nhân/phòng/công ty |
| AT-WORKFLOW | Lưu nháp/gửi/rà/trả lại có lý do/sửa/gửi lại/chốt/revision; chặn state write/unlink trái phép; stale/double click/concurrent reviewers/idempotent retry và payload khác; snapshot/template/bản con không đổi lịch sử |
| AT-ROLLUP | Một task nhiều người/nhiều phòng, nhiều bước cùng project, việc không dự án, tổng phòng+chi tiết cùng nguồn, kế hoạch vs thực hiện khác đơn vị; không đếm trùng/thiếu; coverage/miễn/late đúng nghĩa vụ |
| AT-MONEY | Thiếu nguồn/xác nhận, self-confirm trái chính sách, overlap nhập+auto, currency/tax khác, null/0/ước lượng; tách production/acceptance/request/revenue/receipts; số chưa xác minh không vào tổng chính thức |
| AT-SECURITY | User ngoài company/phòng, người bị thu hồi/chuyển phòng, trưởng phòng tự rà mình, ủy nhiệm hết hạn; đọc/chỉnh owner/scope bằng RPC; tiền/HR qua read_group/search/name_search/count/filter/tooltip/export/file/chatter/deep link/cache |
| AT-UI | Mọi tab/list/detail/popup; bộ lọc đúng trường/AND-OR/pending-applied/clear/sort/pager 10-20-50-100; >100 bản ghi, text dài, stale query; back và unsaved guard; empty/loading/error/retry, no permission; header/chart/table không chồng |
| AT-CHART | Donut tổng đúng và category loại trừ nhau, đúng mẫu số; plan/actual cùng unit; thiếu source/zero denominator; lớn/rõ ở trên; drill-down đồng domain; tooltip/touch/keyboard không lộ quyền; reduced motion |
| AT-EXPORT | Excel/Word/PDF đúng kỳ/domain/snapshot/quyền; text Việt/nhiều trang/cột dài/số tiền/missing; Excel injection; nháp ghi nháp; quyền bị thu hồi khi tải; không cắt dữ liệu âm thầm |
| AT-INTEGRATION | Cùng ID/identity/avatar/phòng/project, thay đổi HR mới phản ánh màn hiện hành mà không viết lại report cũ; home theo quyền cùng shell; không ghi state nguồn/BASE/ký/hiệu lực/payment/grant người thật |
| AT-OPS | Install/upgrade trên test, chạy lại không trùng config/menu; regression HR/KH-KD/Kho/home/login; backup đầy đủ DB+filestore+code/config và quy trình restore được kiểm chứng trong test canonical, không thêm DB rác |

Fixture giả đủ để thấy tính năng: tối thiểu một quý, ba tháng, các tuần liên quan; nhiều phòng/người/role giả; >100 dòng list; hai kỳ có xu hướng khi cần; dữ liệu đủ state, định tính/định lượng, vướng mắc, thiếu nguồn, long text và tiền restricted. Dùng tên/amount tổng hợp giả, seed idempotent/cleanup có marker; không trộn vào main hoặc tạo tài khoản trùng người thật. Phân bố không đồng đều để test không tự chia đều.

Chạy và ghi lệnh thực, log private, exit code:

1. `git diff --check`.
2. Ruff theo cấu hình repo trên Python bị thay đổi; XML/manifest/assets validation. Typecheck/build/test legacy FE chỉ khi thực sự sửa legacy đó; không bịa `npm typecheck` cho OWL.
3. Odoo tests model/security/workflow/period/aggregation/export/concurrency trên `tp_tanphat_test` và install/upgrade addon đúng command/config repo. Không dùng DB main cho tests; khóa phiên ghi test để không ghi đè phiên khác.
4. OWL/HOOT tests hoặc harness native hiện dùng cho chart/filter/list/detail/actions/session; chạy browser Playwright độc lập trên 18079.
5. Kiểm UI ở 1440×900, 1366×768, 768×1024, 390×844 và 375×812; desktop/mobile có scroll/tooltip/filter drawer/detail/back; keyboard và reduced motion. Emulation không được gọi là đã test điện thoại thật.
6. Screenshot trước/sau cùng viewport/role/dataset; review trực tiếp ảnh dashboard, mỗi dạng list/detail và popup lỗi/returned. Lưu `.local/corp-report001/` ignored; không đưa ảnh/số liệu công ty vào Git. Nếu là addon mới chưa có before, chụp shell/nguồn hiện tại và ghi không có màn reporting cũ, không dựng ảnh before giả.
7. Mở thử Excel/Word/PDF đã xuất: kiểm cell/tổng/quyền, render Word/PDF khi có công cụ, nhìn chart/ngắt trang/font, không chỉ kiểm file tồn tại. Không có renderer thì ghi giới hạn kiểm hình thức cụ thể.
8. Backup/restore rehearsal theo runbook bằng canonical test, giữ main không đổi. Không tự cài compiler/service/toolchain lớn hoặc tạo DB ngoài DEC-037; nếu công cụ thiếu ghi đúng phần chưa chạy và chuẩn bị lệnh, không kết luận rehearsal đạt.
9. Self-review touched code và caller: quyền, count/source tổng hợp, invalid transitions, race/retry, snapshot, export và performance. Không dùng N+1 từng người/task, không tải toàn bộ báo cáo vào browser để tính chart. Ghi số dòng/truy vấn/thời gian đã đo, không bịa benchmark.

## 15. Tài liệu, handoff và điều kiện hoàn tất

Cập nhật trong cùng batch:

- `docs/PROJECT_STATUS.md`, `docs/CHANGELOG.md`, `docs/ROADMAP.md` và `custom_addons/tp_reporting/README.md`.
- `docs/architecture/TP_COMPANY_REPORTING_001_DESIGN.md`: schema/state/source/formula thật, điểm khác thiết kế và default chưa ban hành.
- `docs/security/CORP_REPORT_001_SCHEMA_AND_ACCESS.md`: quyền/scope/finance/HR/attachments/snapshots/export và đối tượng test; không chứa credential.
- `docs/ui/CORP_REPORT_001_DESIGN.md` + `TP_TABLE_FILTER_INVENTORY.md`: tất cả action/table/subtable/picker, filter/operator/domain/page/export/evidence hoặc N/A có lý do.
- `docs/demo/CORP_REPORT_001_ACCEPTANCE.md` và `CORP_REPORT_001_USER_GUIDE.md`: bước sử dụng theo nhân viên/trưởng phòng/lãnh đạo/cấu hình, screenshot private được trỏ theo quy trình.
- `ops/runbooks/CORP_REPORT_001_DEPLOY_AND_ROLLBACK.md`: backup, update module/dependencies/assets, smoke, rollback code+DB+filestore tương thích; bước main chỉ thực hiện sau yêu cầu triển khai riêng.
- `docs/DECISIONS.md` chỉ khi có quyết định mới **do người dùng xác nhận**; không biến giả định kỹ thuật/default test thành thẩm quyền doanh nghiệp. OpenAPI/types chỉ cập nhật khi thực sự đổi API public.

Dùng CHG ID mới đúng ngày, không dùng lại ID của prompt. Chạy `scripts/ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN --check "<kiểm tra thực và kết quả>"`, rồi `scripts/ai_workflow.py check` **khi boundary/batch hợp lệ và docs phản ánh đúng code**. Nếu baseline/phiên khác còn thay đổi chưa xác minh, ghi blocker và không finish hộ để tạo PASS giả; giữ checkpoint cần tiếp tục.

Không tuyên bố full module hoàn tất nếu còn tab rỗng, button không action, bảng chưa filter/page đúng, chart fake/bé/ở cuối trang, detail mặc định chưa thiết kế, source/quyền/snapshot/export chưa kiểm, hoặc ca acceptance quan trọng chưa chạy. Phần chưa có dữ liệu chuyên môn thật phải ghi rõ ở UI và handoff, không lấy fixture làm số thật.

Phản hồi cuối cho người dùng bằng tiếng Việt, ngắn và cụ thể:

1. URL 18079 và nơi bấm mở **Báo cáo**; tài khoản test được bàn giao qua file private/quy trình credential, không ghi password trong tài liệu Git.
2. Những màn đã làm, ảnh dashboard/list/detail đại diện và khác biệt nhìn thấy được.
3. Hướng dẫn demo: lập mục tiêu quý → chia tháng → giao tuần → nhân viên gửi → trưởng phòng trả/sửa/chốt → công ty tổng hợp → lãnh đạo giao việc → xuất Excel/Word/PDF.
4. Model/action/security/tích hợp đã đổi, dữ liệu/phiên bản dùng chung ra sao, default nào cần chủ doanh nghiệp cấu hình.
5. Test đã chạy/thất bại/chưa chạy cùng bằng chứng; tự kiểm khác audit độc lập, test kỹ thuật khác nghiệm thu nghiệp vụ.
6. Main18069 **đã hay chưa áp** (theo prompt này là chưa), backup/deploy package đã chuẩn bị; bước tiếp theo cụ thể.
7. Xác nhận không commit/push, không nhập Word thật/đổi quyền người thật, không mở BASE/ký/hiệu lực/kế toán/thanh toán.

Hãy triển khai đủ các phần đã giao trong phạm vi test. Không dừng ở việc trả lại một kế hoạch hoặc báo đã xong vì mới tạo menu.
