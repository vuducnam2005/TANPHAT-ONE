# TANPHAT ONE — Sổ quyết định

## DEC-041 — Xóa hồ sơ nhập nhầm, mã nhân viên và mật độ giao diện (12/11/2026)

Yêu cầu trực tiếp HR-CORRECTION-008, không commit/push. Hồ sơ nhân viên chỉ xóa
vĩnh viễn qua “Xóa hồ sơ nhập nhầm”: admin hệ thống cùng công ty, backend kiểm
từng hồ sơ, lý do bắt buộc, lô tất cả-hoặc-không, audit độc lập còn sau khi xóa.
Chỉ hồ sơ nhập tay chưa dùng (không roster/tài khoản/vai trò/phân công/quyền/tài
liệu/trao đổi/lịch sử/tham chiếu); còn lại lưu trữ. Không Delete native, không
context bypass, không cascade user/partner/tài liệu/nghiệp vụ. Lưu trữ tách khỏi
khóa tài khoản.

Mã nhân viên `TP` + số: mã hợp lệ cao nhất (gồm lưu trữ và audit) + 1, không dùng
ID, không đánh lại, không tái dùng, chấp nhận khoảng trống; mã roster giữ. Mã sai
chỉ sửa cho hồ sơ nhập tay chưa dùng, có audit; xung đột chỉ báo cáo.

Việt hóa qua catalog/template Odoo, không thay chữ DOM lúc chạy; tên sản phẩm,
mã, login giữ. Thu gọn bằng token SCSS dùng chung, không zoom/scale/root font;
sidebar giữ nguyên; mobile ≥44px. Chi tiết:
[acceptance](demo/HR_CORRECTION_008_ACCEPTANCE.md).

## DEC-040 — Danh tính chung và chuyển phòng tức thời (12/11/2026)

Yêu cầu trực tiếp IDENTITY-ORG-001 cho phép phiên chính triển khai/test/backup/
restore kiểm chứng/áp main, không commit/push; ngoại lệ điều phối chỉ task này.
HR quản lý tên chính thức/phòng/chức vụ hiện hành; user/partner giữ danh tính
tài khoản, không đổi login/auth. Ảnh hai chiều qua mapping ID duy nhất, giữ ảnh
thật; xung đột cần admin chọn. Không public private_email hoặc sửa partner khách.

Admin chuyển phòng qua preview/lý do/locks/audit nguyên tử, default staff, HEAD
chọn rõ/unique incumbent. Mặc định revoke HEAD cũ và kết thúc scope cấp riêng;
kiêm nhiệm chỉ giữ sau xác nhận. Workspace là cửa vào, data/tiền theo capability.
History/future không làm đổi scope current; chưa điều chuyển hẹn ngày/khác công ty.
Menu/action/backend/session enforce cùng scope, không cần restart mỗi chuyển.
Nguồn, giới hạn và kết quả: [identity](architecture/TP_IDENTITY_ORG_001.md).

Ghi quyết định hiện hành, lý do và phạm vi. Khi thay đổi, thêm bản thay thế và chỉ rõ quyết định bị thay; không sửa lịch sử thành điều chưa từng được chọn.

## DEC-039 — Tài khoản cá nhân và quản trị HEAD trong HR (12/11/2026)

**Tinh chỉnh CHG-20261112-007:** yêu cầu trực tiếp chỉ đặt Đổi chức vụ trong
chi tiết nhân viên, bỏ khỏi danh sách. Mỗi company/phòng chỉ một HEAD active;
phải hạ người hiện tại trước khi bổ nhiệm nhân viên khác, không tự thay thế.
Wizard báo rõ người hiện tại, kiểm preview/apply và unique index ở backend
chặn cả provisioning trực tiếp/reactivation/race. Role chưa thu hồi vẫn giữ
vị trí dù user khóa hoặc ngày hiệu lực chưa tới/hết; job HR không tự cấp quyền.
Không thay role/chức vụ người thật để test, giữ ngoại lệ thực thi trong task HR.

**Tinh chỉnh CHG-20261112-006:** phản hồi "nâng/hạ chức vụ ở đâu, làm dễ hiểu"
đưa Đổi chức vụ ra danh sách và đầu hồ sơ. Tái dùng role wizard, tách rõ đổi
chức vụ HR (lý do/preview/audit, không đổi quyền, dùng được khi chưa account)
và Bổ nhiệm/Chuyển về nhân viên KH-KD (quyền backend hiện hành, optional đổi
cả chức vụ nguyên tử). Không mở ma trận quyền phòng khác hoặc suy quyền theo
tên chức vụ. Tiếp tục quyền thực thi/test/áp main trong cùng task HR.

**Tinh chỉnh theo phản hồi người dùng — CHG-20261112-005:** form tạo tài khoản
có tên đăng nhập, mật khẩu và nhập lại mật khẩu trên cùng màn hình, nhãn/chú
thích rõ và thông báo tiếng Việt. Xác thực danh tính Odoo trước khi nhập mật
khẩu mới; submit kiểm session native còn hiệu lực, tạo user/password/mapping/
audit nguyên tử. Đặt lại cùng form, login chỉ đọc; không lưu password mới ở
transient/context/yêu cầu xác thực chờ/lịch sử. Giữ native hashing và policy.
Thay cách nhập qua change.password.wizard của CHG004, không thay policy quyền.

Yêu cầu trực tiếp HR-ACCOUNT-ROLE-001 cho phép triển khai/test/backup-restore/
áp main trong task này, ngoại lệ vai điều phối DEC-022; không commit/push.
Mỗi nhân viên dùng user riêng, không chọn/liên kết/gỡ user có sẵn. Thay phần
giao diện liên kết của DEC-038; giữ mapping hợp lệ, constraint user/company,
tài khoản hệ thống và lịch sử. Không tự cấp user cho toàn bộ roster.

Admin đúng company tạo user mới hoặc đổi staff ↔ HEAD KH-KD trong hồ sơ qua
preview/lý do/scope/audit nguyên tử, tái sử dụng tp.kd.department.role và guard
superuser hẹp. HEAD theo DEC-033/current matrix; chức vụ HR không cấp quyền.
Hạ role chặn nguồn quyền quản lý cấp riêng xung đột và giữ/liệt kê quyền riêng
hợp lệ. Phiên cũ bị thu hồi. Phòng khác chưa có bộ role thì báo chưa triển khai.
Tình trạng tài khoản là Mở/Khóa/Chưa có tài khoản, tách archive hồ sơ.

Giao diện native năm tab, sidebar navy/nội dung sáng, account & permissions rõ;
password theo Odoo native. Không mở thêm quy trình ký/hiệu lực/thanh toán, HR
toàn công ty cho HEAD hoặc hệ thống role mới. [Guide](demo/HR_ACCOUNT_ROLE_001_USER_GUIDE.md),
[security](security/HR_ACCOUNT_ROLE_001_SECURITY.md), [acceptance](demo/HR_ACCOUNT_ROLE_001_ACCEPTANCE.md).
Technical verification, visual/business acceptance và pilot authorization tách riêng.

## DEC-038 — HR native, roster mới, mã TP và xử lý tài khoản phù hợp (11/11/2026)

**Lệnh thực thi trực tiếp 11/11/2026 — CHG-20261111-002:** người dùng giao phiên
này thực hiện đầy đủ prompt, dùng đúng file nguồn, test `tp_tanphat_test`18079
trước, backup/restore kiểm chứng rồi áp `tp_tanphat_dev`18069; không commit/push.
Đây là ngoại lệ vai điều phối DEC-022 trong scope HR-001, không thay thẩm quyền
nghiệm thu nghiệp vụ/pilot hoặc cho phép payroll/tuyển dụng thiếu quy chế.
Kết quả thực tế xem status và [acceptance](demo/HR_001_ACCEPTANCE.md).

**Người dùng yêu cầu soạn kế hoạch/prompt:** dọn mẫu, đưa hồ sơ nhân viên cùng
phòng ban từ bảng công mới vào HR; mã số nguồn đổi thành mã TP (60 → TP10060),
chức năng HR thực, sidebar theo KH-KD và dashboard có biểu đồ tròn.

- Nguồn roster mới là `bang cham cong vao ra (1).xlsx`, hai sheet cùng 39 người/
  9 nhóm, không 78 người; metadata/hash và đối chiếu tại [kế hoạch HR](architecture/TP_HR_001_ROSTER_WORKSPACE_PLAN.md).
  Thay nguồn danh mục của DEC-034 cho lần nhập này, giữ lịch sử nguồn cũ.
- Mã nghiệp vụ TP+(10000+mã nguồn); không đổi PK/FK Odoo. Lưu mã nguồn riêng,
  kiểm unique, import idempotent; dùng model HR/version hiện hữu.
- Người dùng trả lời rõ: **“Liên kết hồ sơ nhân viên; giữ quyền KH-KD”**.
  Không cấp tất cả account KD quyền quản lý HR, không tự tạo 39 users. Chưa chỉ
  định người thật làm HR; main dùng admin, test actor giả cho kiểm quyền.
- Sau khi biết mapping alias còn mơ hồ, người dùng chỉ đạo lấy file mới làm
  chuẩn và **“có thể xóa những tài khoản hiện tại đi nếu thấy nó không phù hợp
  với file excel”**. Cách triển khai đề xuất là archive/disable account mẫu
  xác minh không phù hợp, có audit/backup và giữ admin/kỹ thuật. Mơ hồ danh
  tính để pending, không chuyển quyền sang người khác. Đây không phải lệnh
  hard-delete user/log/identity hoặc khóa account thật chưa đủ căn cứ.
- Phạm vi prompt gồm code/test/roster và rollout main 18069 sau backup/restore
  kiểm chứng, dùng test chuẩn 18079 theo DEC-037. Phiên soạn prompt chỉ đọc và
  viết tài liệu, chưa thực thi thay đổi ứng dụng/database/tài khoản.
- “Đầy đủ” lượt này là HR Foundation (hồ sơ/danh mục/import/quyền/UI/dashboard/
  Excel); chấm công/lương/nghỉ phép/tuyển dụng đầy đủ cần quy chế và đầu vào
  riêng. Không nhập giờ vào-ra hoặc bịa KPI từ workbook danh mục.

Chi tiết giao việc tại [prompt HR-001](prompts/CLAUDE_HR_001_NATIVE_ROSTER_WORKSPACE.md).

## DEC-037 — Dọn dữ liệu mẫu và chuẩn hóa hai database local (10/11/2026)

**Yêu cầu trực tiếp và phạm vi đã xác nhận:** xóa dữ liệu nghiệp vụ mẫu; giữ
tài khoản, quyền và cấu hình. Giữ một database chính cùng một database test.

- Local dùng `tp_tanphat_dev`/18069 và `tp_tanphat_test`/18079 trên cluster
  workspace55432; giữ `postgres`, `template0`, `template1`. Không xóa bảng/schema
  Odoo, không thay service PostgreSQL khác hoặc source ứng dụng.
- Dọn đúng sample namespace/binding và phụ thuộc đã kiểm kê; giữ tài khoản,
  mật khẩu, nhóm/ACL/rule và HEAD role. Assignment/grant của dự án mẫu đi cùng
  dự án bị xóa; không coi đó là quyền toàn hệ thống phải cấp lại tự động.
- Backup database+filestore; diễn tập restore và dọn trên bản riêng, đối chiếu
  phần giữ lại và đăng nhập trước main. Bỏ database cũ theo danh sách chính xác
  sau khi kiểm bản lưu. Archive riêng tư không đưa Git.
- Test chuẩn tách filestore/session, tắt cron/SMTP và đổi UUID/URL. Tái sử dụng
  với một tác vụ ghi/migrate tại một thời điểm; không tiếp tục tạo DB theo task
  nếu chưa có yêu cầu riêng. Phát triển dữ liệu giả trên test trước; áp source/
  migration được giao lên main, không chép test đè main.
- Không reset sequence, đổi mật khẩu, nhập roster thật, gỡ module hoặc mở quyền
  xóa lịch sử trong ứng dụng. Danh mục/công ty và cấu hình Internal của Odoo
  giữ lại dù có tên DEV. Baseline HR12 mẫu trước đây chuyển thành lịch sử sau
  bảo trì; nguồn39người còn ngoài DB. Kết quả thật theo status và
  [runbook](../ops/runbooks/SAMPLE_DATA_CLEANUP_AND_TEST.md).

## DEC-036 — Thiết kế Home admin với 7 mục; nhân sự là chặng tiếp (10/11/2026)

**Yêu cầu trực tiếp:** chỉ hiển thị Kế hoạch Kinh doanh, Phòng Thiết kế,
Phòng Kỹ Thuật, Phòng BIM-QC, TADIC, Quản lý nhân sự và Tuyển dụng ở màn
admin; thiết kế trước, bước phát triển tiếp theo là module quản lý nhân sự.

- Thay phạm vi Home của DEC-035: đúng 7 mục, nhóm thành 5 phòng/đơn vị và
  2 chức năng nhân sự. KH-KD mở workspace hiện hữu; 4 đơn vị còn lại có trang
  Đang phát triển; HR/recruitment theo trạng thái module và quyền thực tế.
- Chỉ khung Home quản trị thay đổi. Người thường giữ Home/menu nghiệp vụ
  theo quyền hiện có; không suy HEAD KH-KD là quản trị hệ thống. Thiết kế đề
  xuất nhận diện admin bằng `base.group_system`; đây chưa phải thay đổi nhóm
  hoặc security runtime. Không cấp quyền HR từ việc thêm thẻ Home.
- Không đưa 4 nhóm còn lại lên khung này không có nghĩa xóa tổ chức hoặc
  nhân viên: nguồn DEC-034 vẫn 39 người/9 nhóm. Không tự import, tạo account,
  chuyển phòng hoặc sửa grant từ thay đổi điều hướng.
- Lượt hiện tại chỉ [thiết kế và preview](ui/UI_HOME_004_ADMIN_DESIGN.md),
  chuẩn bị [prompt triển khai mới](prompts/CLAUDE_UI_HOME_004_ADMIN_ONLY.md)
  và [kế hoạch HR-001](architecture/TP_HR_001_FOUNDATION_PLAN.md). Không sửa
  ứng dụng/DB/dev. Prompt Home cũ giữ lịch sử và được đánh dấu đã thay thế.
- HR phát triển tiếp từ hồ sơ nhân viên, tổ chức/chức danh và quyền; sau đó
  nhập roster có đối chiếu, báo cáo và tuyển dụng. Chấm công/nghỉ phép/lương
  cần quy tắc riêng; không coi nghiệp vụ HR toàn công ty đã được xác nhận.

## DEC-035 — Home đủ phòng/đơn vị và lối vào HR/Tuyển dụng (10/11/2026)

**Yêu cầu trực tiếp:** đưa các phòng lên Home, ngoài KH-KD khi bấm ghi “Đang
phát triển”, thiết kế gọn/đẹp, thêm Quản lý nhân sự và Tuyển dụng.

- Bổ sung phạm vi khung Home ở DEC-031: theo 9 nhóm nguồn mới DEC-034,
  1 workspace KH-KD hiện hữu, 8 landing placeholder riêng. Không thêm HĐQT từ
  bảng cũ hoặc tạo hai workspace KH-KD/Ban Kinh Doanh trùng nhau.
- Hai thẻ Quản lý nhân sự/Tuyển dụng là chức năng dùng chung, không phải hai
  phòng mới. Prompt quy định mở module native đã cài/có quyền; thiếu quyền khác
  chưa triển khai. Không suy HEAD có quyền HR hoặc tự cài/cấp nhóm HR trong batch Home.
- Chỉ thêm khung và lối vào; ưu tiên nghiệp vụ KH-KD, không triển khai đầy đủ
  phòng khác hoặc nhập nhân viên thật. Giữ DEC-029/030/033 và vai trò điều phối.
- [UI-HOME-004](prompts/CLAUDE_UI_HOME_004_DEPARTMENTS_HR_RECRUITMENT.md) giao
  clone-test/ảnh trước–sau, backup/restore verified rồi áp18069. Soạn prompt
  không phải đã sửa giao diện, cài module hoặc nghiệm thu chức năng HR.

## DEC-034 — Dùng bảng nhân sự tuần 1 tháng 11 làm nguồn hiện hành (10/11/2026)

Người dùng cung cấp `202611_tanphat_chamcong_tuan1.xlsx`, rồi xác nhận
**“cứ làm theo file tôi mới gửi đi”** khi được hỏi về khác biệt với phân công cũ.

- Dùng danh sách/phòng/chức vụ trong nguồn mới cho hồ sơ kiến thức và kế hoạch;
  giữ tài liệu cũ làm lịch sử, không lấy nhiệm vụ cũ ghi đè nhóm trong file mới.
- Kiểm được 39 dòng/9 nhóm, mã không trùng, tên/mã/chức vụ đối chiếu XML; kỳ
  02–07/11/2026, hash và locator ở [baseline](architecture/TP_STAFF_SOURCE_BASELINE.md).
- Tên/mã nhân viên trích xuất lưu ngoài Git; bảng công không tự là sơ đồ quản
  lý, danh mục tài khoản, căn cứ thẩm quyền duyệt hoặc tình trạng lao động.
  Không tự mapping sang user/grant, chuyển phòng hay import vào DB.

## DEC-033 — HEAD toàn quyền nghiệp vụ KH-KD (10/11/2026)

**Yêu cầu trực tiếp:** “viết prompt cho tôi thùy anh (trưởng phòng) sẽ toàn quyền
trong phòng kinh doanh”. Người dùng đã chốt hướng phân quyền HEAD; việc cấp
quyền thực tế chưa thực hiện trong lượt soạn prompt này.

- Thay hướng HEAD chỉ đọc/rà soát và giới hạn vài dự án preset bằng quyền quản
  lý toàn nghiệp vụ KH-KD, kể cả hồ sơ nhân viên khác và dự án mới thuộc phòng.
  Chi tiết triển khai/test tại [KD-HEAD-001](prompts/CLAUDE_KD_HEAD_001_DEPARTMENT_FULL_CONTROL.md).
- Diễn giải triển khai: đầy đủ lập/sửa nháp, gửi/gửi lại, rà soát/trả lại hồ sơ
  người khác, phân công, Project/WBS, đọc/sửa tiền nháp và file/báo cáo/XLSX trong
  đúng company/department. Không hardcode tên hoặc scope hữu hạn của seed cũ.
- Toàn quyền nghiệp vụ vẫn theo state/phiên bản/audit và self-review hiện hành;
  không sửa/xóa lịch sử hoặc tự suy thẩm quyền BASE/ký/hiệu lực/kế toán/thực chi.
  Không đồng nghĩa admin hệ thống, quyền đọc mọi phòng hoặc cấp grant bảo mật
  cho người khác. Chưa xác nhận hạn mức ký hoặc quy chế bốn mắt toàn công ty.
- Đây là delta HEAD cụ thể, không duyệt toàn bộ V2 hoặc thay quyền bốn actor
  còn lại. Prompt giao clone-test/backup/restore verified rồi áp HEAD dev18069;
  không phải tuyên bố đã áp, đã kiểm runtime quyền hoặc đã nghiệm thu/pilot.

## DEC-032 — Tách Quản lý dự án và Quản trị dự án trong KH-KD (09/11/2026)

**Người dùng yêu cầu trực tiếp:** “tách riêng 2 cái quản lý và quản trị dự án đó ra”
và viết prompt triển khai, hoàn thiện các mục đã bàn với lãnh đạo.

- Hai khu vực điều hướng/action/góc nhìn riêng trong workspace KH-KD:
  Quản lý dự án tập trung WBS, công việc, tiến độ, phân công và đầu ra;
  Quản trị dự án tập trung hồ sơ thương mại/hợp đồng, khoán, sản lượng,
  nghiệm thu, đề nghị thanh toán và nghĩa vụ. Cùng hồ sơ gốc/project ID,
  không nhân bản dữ liệu hoặc database theo hai tên gọi.
- Scope prompt gồm chín ý và hai làm rõ tại
  [phân tích cuộc họp](architecture/TP_KD_MEETING_REFINEMENT_20261109.md):
  Người phụ trách đứng trước hạn, đối tác nhiều loại có vai trò; thêm Dự án/
  Chủ đầu tư/tình trạng-nhật ký/giá gói/Đấu thầu đúng quan hệ nghiệp vụ.
- Xác nhận này là yêu cầu tách chức năng và giao chuẩn bị prompt thực thi,
  không phải hoàn tất code, duyệt mọi dòng KD-ROLE-V2, mở TASK-001 cho người
  thật hoặc thay thẩm quyền BASE/ký/hiệu lực/kế toán. Các trạng thái/field/
  capability chi tiết trong prompt là baseline triển khai/test, không tự
  trở thành quy chế pháp lý đã được công ty phê duyệt.
- Giữ DEC-030/031 và vai trò điều phối. Phiên này chỉ viết
  [prompt KD-PROJECT-RESTRUCTURE-001](prompts/CLAUDE_KD_PROJECT_RESTRUCTURE_001.md),
  chưa chạy hoặc áp ứng dụng. Mục tiêu dev18069 qua test/audit/backup/restore;
  correction F1–F3 và quyền người thật chưa duyệt giữ cổng tương ứng.

## DEC-031 — Trang chủ theo workspace, ưu tiên hoàn thành KH-KD (07/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** đồng ý gom nghiệp vụ theo workspace, rồi làm rõ: “những phòng ban khác không quan trọng đâu bây giờ tôi muốn setup sẵn giao diện trang chủ cho logic trước thoi còn nghiẹp vụ và chức năng các thứ thì phạm vi hiện tại đang làm cho phòng kinh doanh, cứ hoàn thành phòng kinh doanh trước đã”.

- Trang chủ ưu tiên **Kế hoạch Kinh doanh** và công cụ cá nhân theo quyền; bỏ lưới “Ứng dụng nghiệp vụ” khỏi nội dung chính cho nhân viên. Chức năng KH-KD truy cập trong workspace, cùng model/action/dữ liệu hiện có.
- Quản trị hệ thống có “Tất cả ứng dụng” và thiết lập theo quyền. Người thường vẫn giữ đường native tới công cụ khác đã được cấp; không thu hồi/mở quyền vì ẩn lưới.
- Hiện không dựng workspace/nghiệp vụ các phòng khác hoặc thẻ giả. Hoàn thành KH-KD trước; catalog có thể mở rộng sau, không nhân bản dữ liệu theo phòng.
- Giữ DEC-023/029/030, session/Home Action, dữ liệu/quyền/workflow và gate nghiệp vụ/pilot. [Danh sách tổ chức nguồn](architecture/TP_ORGANIZATION_SOURCE_BASELINE.md) không phải lệnh tạo cây phòng ban hoặc đổi tên Ban Kinh Doanh.

[Prompt UI-HOME-003](prompts/CLAUDE_UI_HOME_003_KD_FIRST.md) là bước thực thi tiếp theo; CHG-20261107-005 chỉ chuẩn bị tài liệu, chưa sửa application/runtime.

## KD-NATIVE-001 — Giữ254, thiếu6phụ lục (06/11/2026)

Người dùng trả lời trực tiếp: “Giữ254, ghi rõ thiếu6phụ lục”. Action audited `create_amendment` cần không còn revision đang xử lý; task chưa cho mở `review_complete`. Quyết định này thay mục tiêu260 tại7A/CHG006 cho kết quả bàn giao task:254bản ghi nghiệp vụ,10hợp đồng/0phụ lục, các nhóm khác giữ cơ cấu. Không mở gate pháp lý hoặc tạo model dự kiến phụ lục để bù. Prompt260giữ lịch sử, bàn giao ghi rõ chênh6.

## KD-NATIVE-001 — Quyền thực thi và trình diễn dev (06/11/2026)

Người dùng trực tiếp giao phiên chính thực hiện toàn `deliverables/PROMPT_KHKD_NATIVE_18069.md`, bổ sung7A–7C/CHG006, tuần tự các lô, clone-test rồi tích hợp dev18069 sau backup/restore. Ngoại lệ DEC-022 chỉ KD-NATIVE-001; cho custom addon/model/native UI và dataset tổng hợp bền260 mục tiêu, không commit/push hoặc cleanup dữ liệu mới trên dev. Không hỏi lại quyền tích hợp đã cho. Đây không là business acceptance/pilot hoặc cấp grant người thật; Q2/TASK-001/pháp lý/BASE/ký/hiệu lực/hạch toán/tiền thật giữ nguyên. Chỉ ghi số thực sau khi seed/verify dev, không coi mục tiêu là số đã tạo.

## DEC-030 — Giao diện chính phát triển trong Odoo (05/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** “tôi quyết định sẽ phát triển fe dựa trên odoo chứ ko tác riêng fe ra nữa”. Giao diện chính TANPHAT ONE dùng native Odoo, view/action chuẩn và OWL/QWeb/SCSS trong `custom_addons/` khi cần. DEC-030 thay lựa chọn frontend độc lập trong DEC-001 và định hướng login React chính ở DEC-012; giữ backend Odoo, dữ liệu, session, API và các kết quả đã có. Đây là quyết định hướng phát triển, chưa tự chuyển route/login hoặc triển khai UI còn thiếu.

- Giữ nguyên DEC-002/003/013/014/017/023/029: một database mỗi môi trường, không sửa core, BASE duyệt chính thức giai đoạn đầu, quyền tiền và workspace theo scope; TADIC/TACICO cùng công ty.
- Source React, OpenAPI, API và test lịch sử được bảo toàn; không xóa/gỡ/ngừng dịch vụ hoặc rewrite workflow chỉ vì đổi hướng. Chuyển từng luồng sang native phải có task, test và kiểm hồi quy riêng.
- Native Odoo được dùng ORM/RPC theo cơ chế chuẩn; action/model backend tiếp tục enforce state/capability/company/project/financial scope. Không bypass bằng direct state write, sudo hoặc chỉ ẩn nút.
- TP Contracts chưa có UI native đầy đủ. Backend draft/submit/return/rework đã có; cần đặc tả rồi triển khai menu/list/form/action native tái sử dụng đúng backend, không code lại nghiệp vụ. Quyết định này không xác nhận hạn mức, cấp quyền người thật hoặc mở pilot.

Xem [hướng hiện hành và phần cần chuyển](architecture/TP_NATIVE_ODOO_DIRECTION.md). Lượt CHG-20261105-001 chỉ cập nhật hướng dẫn/tài liệu; chưa sửa application code hoặc runtime.

## DEC-029 — TADIC và TACICO là đơn vị nội bộ cùng công ty (04/11/2026)

**Đã xác nhận trực tiếp bởi người dùng:** TADIC và TACICO là đơn vị nội bộ cùng công ty, không phải hai pháp nhân riêng. Không tạo `res.company`, database, bộ khách hàng hoặc dự án trùng chỉ để phân biệt hai đơn vị này. Giữ một database cho mỗi môi trường theo DEC-002 và workspace theo quyền theo DEC-023.

**Hệ quả thiết kế:** tổ chức hai đơn vị dưới cùng công ty; ánh xạ vào cây phòng ban/đơn vị hiện có sau khi xác định cấp trên và mã đơn vị. Phân công dự án và quyền dữ liệu được kiểm tra ở backend; cùng công ty không đồng nghĩa tự được xem tiền, hồ sơ nhân sự hoặc dự án của đơn vị khác. Chưa xác nhận đơn vị cha, người quản lý, quyền duyệt hoặc mô hình phân bổ chi phí; không suy ra những quyền này từ tên đơn vị.

Lượt xác nhận chỉ cập nhật tài liệu. Không tạo đơn vị/tài khoản, đổi schema, seed dữ liệu thật hoặc điều chỉnh quyền trên runtime. Xem [thiết kế database](architecture/TP_DATABASE_DESIGN.md#1-phương-án-chọn).

## DASH-UI-001 — Thực thi riêng dashboard native (04/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-028 | Người dùng giao trực tiếp task và cho triển khai/kiểm thử/handoff; áp dụng CHG-20261104-001 | Phiên chính được sửa đúng dashboard UI/reporting native18069 sau snapshot/clone. Ưu tiên native; OWL/SCSS/backend report giới hạn addon custom và hai binding được giao khi native spreadsheet thiếu phép phân bổ/filter đúng. | Ngoại lệ chỉ DASH-UI-001; DEC-022 mặc định giữ nguyên. Không đổi workflow/quyền/allowlist/chứng từ/password, core/React/prototype, commit/push hay dựng demo cũ. Dữ liệu hiện tại thắng mốc lịch sử khi có tracking bằng chứng. Technical verification không thay audit độc lập/business/pilot. [Runbook](demo/dashboards/README.md). |

## DEC-022 — Phiên chính điều phối, Claude triển khai

**Ngoại lệ trực tiếp 06/11/2026, CHG-20261106-002:** người dùng giao phiên chính chạy nốt `CLAUDE_UI_CTR_NATIVE_001A.md` vì Claude hết token. Cho thực thi UI001a trên DB test với fixture, acceptance trước implementation; không áp dev, không commit/push. Ngoại lệ này không đổi policy nghiệp vụ hoặc vai trò điều phối mặc định ở task khác.

**Trạng thái:** người dùng xác nhận trực tiếp ngày 28/10/2026. Phiên chính lập kế hoạch, tổng hợp nội dung/ý tưởng, phân tích, kiểm source/test lại kết quả Claude và phát prompt; không trực tiếp sửa application code trong vai trò này. Claude triển khai từng batch được giao, chạy test và cập nhật handoff. Phiên chính audit độc lập, đưa finding/correction hoặc next prompt; technical acceptance không thay xác nhận nghiệp vụ/pilot. Đây là phương thức làm việc, không phải quyết định mở thêm chức năng hoặc phê chuẩn toàn bộ roadmap. Người dùng có thể đổi vai trò/phạm vi bằng chỉ thị trực tiếp. Xem [quy trình điều phối](AI_COORDINATION_WORKFLOW.md).

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-001 | Hướng frontend đã được DEC-030 thay thế ngày 05/11/2026 | Lịch sử: web riêng gọi API Odoo; backend modular monolith giữ nguyên | Giao diện chính hiện là native Odoo; không xóa source/API cũ |
| DEC-002 | Đã áp dụng ở dev | Một PostgreSQL database cho mỗi môi trường, dùng chung các phòng | Dùng ORM chuẩn, company/project/assignment scope; staging/production chưa được dựng |
| DEC-003 | Đã áp dụng | Kế thừa model chuẩn và giữ custom code trong `custom_addons/` | Không sửa core và không nhân bản users/partners/departments/projects |
| DEC-004 | Đã xác nhận | Root `C:\TANPHAT ONE`, tên sản phẩm TANPHAT ONE và chín tên phân hệ | Người dùng xác nhận tên và yêu cầu làm tại root này; không đổi technical IDs chỉ vì thương hiệu |
| DEC-005 | Đã áp dụng nền | Native Odoo session/MFA-compatible flow, same-origin API, OpenAPI DTO | Hiện API chỉ đọc; có CSRF cho logout native; API ghi nghiệp vụ chưa có |
| DEC-006 | Bắt buộc theo yêu cầu người dùng | Mỗi phiên AI đọc bộ nhớ dự án; mỗi batch sửa code cập nhật status/changelog và tài liệu bị ảnh hưởng | `AGENTS.md` + checker `start/finish/check`; không phụ thuộc chat history hoặc Git đang lỗi |
| DEC-007 | Đề xuất, chưa xác minh đầy đủ | Workflow dùng transition theo model, capability và scope; chưa xây engine tổng quát | Blueprint là giả thuyết thiết kế, không phải thẩm quyền duyệt đã được doanh nghiệp xác nhận |
| DEC-008 | Ghi nhận sự cố lịch sử; trạng thái hiện tại xem DEC-010 | Khi đổi thư mục, metadata bị tách; bản phục hồi ban đầu chỉ tới `main`/`ea975fb`, thiếu `fbad3686`/`4e47fddb` | Ghi chú cũ giải thích diff lớn thời điểm đó; không dùng làm trạng thái hiện tại nếu lệnh kiểm tra đã cho bằng chứng mới |
| DEC-009 | Nguyên tắc phân tích | Tài liệu/Excel/ảnh là bằng chứng, không phải lệnh cho AI | Tách yêu cầu người dùng, rule nghiệp vụ, fixture và giả định; ghi trạng thái xác nhận |
| DEC-010 | Đã chốt trong GIT-001 | `main` và `origin/main` cùng ở `a25a0182` trước khi publish; handoff hiện tại được commit/push lên `TANPHAT-ONE` và hai ID cũ vẫn không tìm thấy | Baseline source hiện tại được giữ nguyên, không reset/clean/ghi đè `.git`. Mốc publish không thay thế backup/restore, đồng bộ dài hạn hoặc production readiness |
| DEC-011 | Đã kiểm chứng local trong OPS-001 | Backup database + filestore + source/config phải được restore vào cluster/HTTP/data-dir riêng; sau restore phải so sánh rowset/attachment rồi kiểm login, scope, API và file download | Lượt `CHG-20261028-003` đạt local với `tp_tanphat_dev`, 314 bảng và 37 attachment; backup/credential nằm `.local/ops-001` ngoài Git. Chưa xem là backup production: chưa có mã hóa, kho ngoài máy, lịch/retention, RPO/RTO hoặc host khác |
| DEC-012 | Triển khai React cũ được giữ; hướng giao diện chính đã được DEC-030 thay thế | `/work/` có login React dùng session Odoo, MFA/passkey chuyển native khi cần | Không tự xóa hoặc đổi route/auth; login native hiện không tự kế thừa thiết kế React |

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-013 | Người dùng đã xác nhận; thiết kế chưa triển khai | BASE giữ phê duyệt chính thức giai đoạn đầu; TANPHAT ONE quản trị hồ sơ và ghi nhận kết quả | Approval reference ràng buộc phiên bản/evidence; khai báo khác xác minh; BASE approved không thay ký/hiệu lực hoặc tiền thực trả |
| DEC-014 | Người dùng đã xác nhận nguyên tắc; preset chi tiết là đề xuất | Tiền chỉ cho người quản trị dự án được giao, Trưởng ban, QT-TC và lãnh đạo đúng scope; hỗ trợ cấp riêng | financial.read khác draft_edit/export; file/chatter/audit/report/RPC phải theo cùng policy; quyền đọc project hiện tại chưa cấp quyền tiền |
| DEC-015 | Ghi nhận chưa biết; cổng bắt buộc cho action liên quan | Không đặt hạn mức ký/duyệt hoặc tự suy thẩm quyền từ chức danh; bốn mắt chưa xác nhận | Q1–Q3 của BIZ-001 chặn xác minh/chốt pháp lý/pilot liên quan, không chặn read schema hoặc draft development độc lập trên test |
| DEC-016 | Quy tắc mẫu đã đối chiếu; snapshot domain là đề xuất | Giá cập nhật PKH là tổng mới theo phạm vi, không phải delta; các sự kiện sản lượng/nghiệm thu/hóa đơn/tiền tách nhau; cấp 2 không cộng tổng lần hai | Snapshot revision đầy đủ dựng từ bản trước/phụ lục có provenance; không copy điều kiện giá dương cuối/ID toàn cục hoặc bảng transaction đa năng; hồ sơ pháp lý/thuế/hồi tố còn cần xác nhận |
| DEC-017 | Đã áp dụng ở dev trong CTR-001 | `financial_read` là `tp.project.grant` theo user + project (lý do, thời hạn, thu hồi); số tiền nằm ở model riêng (`tp.contract.line.amount`, `tp.approval.reference.amount`) có access domain theo grant; tài liệu phân loại `general`/`financial`. Grant chỉ superuser cấp khi Q2 chưa chốt; Platform Manager/admin không có tiền mặc định; API đọc đặt trong `tp_planning_api` | Field group toàn cục không giới hạn được theo từng project; model riêng làm ORM read/search/`read_group`/export, RPC, API và tệp cùng bị chặn. Không suy grant từ chức danh khi chưa có văn bản phân công; admin/superuser vẫn có khả năng truy cập kỹ thuật |

DEC-013–017 cụ thể hóa baseline ở DEC-007 và thay phần chưa chốt về lựa chọn nơi duyệt/cách hiểu giá trong mẫu. Văn bản thẩm quyền, bốn mắt, điều khoản giữ lại/thuế/ngày hiệu lực và chính sách correction sau chốt vẫn chưa được coi là xác nhận chỉ từ blueprint hoặc fixture. Xem [BIZ-001](architecture/TP_KD_WORKFLOW_AND_PERMISSIONS.md).

## DEC-023 — Một nền giao diện chung, workspace theo phòng ban và quyền

**Nguyên văn người dùng đã chốt:** “Một nền giao diện chung cho toàn hệ thống, nhưng mỗi phòng ban có workspace, menu, dashboard, trường dữ liệu và nút thao tác khác nhau theo vai trò và quyền.”

**Trạng thái:** người dùng xác nhận trực tiếp ngày 29/10/2026 nguyên tắc dùng một nền giao diện chung cho toàn hệ thống, còn trải nghiệm thay đổi theo phòng ban/vai trò/quyền. TANPHAT ONE không tạo một frontend lặp lại cho từng phòng ban; cũng không coi việc ẩn nút trên frontend là biện pháp bảo mật. Các cơ chế technical dưới đây là khung đề xuất để đặc tả dần, không phải danh mục menu, route, field hoặc capability đã được công ty phê duyệt.

| Quy tắc | Áp dụng |
| --- | --- |
| Common shell | **Nguyên tắc đã chốt:** một nền giao diện chung. Thành phần như thương hiệu, tìm kiếm, thông báo, tài khoản là thiết kế UX đề xuất. |
| Department workspace | **Nguyên tắc đã chốt:** mỗi phòng/vai trò có trải nghiệm khác nhau. Danh sách workspace, navigation, KPI và quick action cụ thể cần domain owner/spec riêng. |
| Shared detail | **Đề xuất kỹ thuật:** tái sử dụng bản ghi canonical khi một hồ sơ được nhiều phòng cùng xử lý; route, section và field cụ thể còn phải đặc tả theo domain. |
| Backend authority | **Nguyên tắc kiến trúc:** quyền phải được enforce ở backend theo các quyết định security hiện hành. DTO/`allowed_actions` là cách triển khai đề xuất, chưa mở thêm capability. |
| User context | **Đề xuất kỹ thuật:** một người có thể có nhiều assignment/workspace; không thay thế kiểm tra quyền trên từng record. |

**Cơ sở/ảnh hưởng:** mô hình này phù hợp với cách tổ chức role-based workspace phổ biến trong Odoo, SAP Fiori, Dynamics 365 và Salesforce, đồng thời phù hợp các quan sát đã ghi về Base/IMIS2. Đây là quyết định UX/kiến trúc của TANPHAT ONE; các menu, field, dashboard và capability cụ thể của từng phòng vẫn phải có đặc tả/owner riêng. Các route frontend dùng một app; addon backend tiếp tục chia theo nghiệp vụ và nguồn dữ liệu, không chia theo phòng ban.

## DEC-024 — Demo native Odoo toàn hệ thống cho lãnh đạo

**Trạng thái:** người dùng xác nhận trực tiếp ngày 30/10/2026 hai lựa chọn: “Dựng native Odoo để demo trước” và “Dựng khung toàn hệ thống”. Phiên chính tiếp tục điều phối và viết prompt; Claude triển khai.

**Phạm vi đã cho phép:** khung trình diễn bằng Odoo native trên môi trường riêng, dữ liệu giả; tận dụng module/model sẵn có, bổ sung common workspace/dashboard/menu và màn hình minh họa có nhãn cho phần chưa triển khai. Giữ chín tên phân hệ hiện hành; CRM/Request/Bid được giới thiệu như mục bổ sung, không tự trở thành nghiệp vụ đã nghiệm thu. Cho phép fixture actor/grant theo policy hiện có trong DB demo, không cấp quyền người thật.

**Ranh giới:** đây là bản trình diễn ưu tiên trước, không thay DEC-001/023 về frontend React + API Odoo hoặc DEC-013/017 về BASE/quyền tiền. Không mở production/pilot, không nâng cấp DB dev/test, không tự nghiệm thu AUTH-002 còn pending. Chức năng dự kiến và chức năng runtime phải phân biệt trên UI/tài liệu. Prompt tại [UI-DEMO-001](prompts/CLAUDE_UI001_NATIVE_ODOO_DEMO.md); việc viết prompt không chứng minh đã có demo chạy được.

## BIZ-002 — Ưu tiên thiết kế nghiệp vụ trước code (28/10/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-018 | Người dùng xác nhận phạm vi và thứ tự | Lượt BIZ-002 chỉ phân tích/viết tài liệu toàn công ty A–M, bắt đầu chi tiết từ KD; hoàn thiện quy trình, dữ liệu, quyền, quy tắc và nghiệm thu trước code. Người dùng quyết định chuyển giai đoạn | Thay ưu tiên Next action hướng CTR-002 của CHG-008; giữ nguyên CTR-001 đã bàn giao/read runtime. Không sửa source/schema, setup/upgrade/seed/credential, commit/push hoặc tự nhắn chat khác |
| DEC-019 | Nguyên tắc thiết kế đã yêu cầu; chi tiết là đề xuất | Một nguồn sự thật theo phần: workflow KD giữ mapping contract/Q1–Q8, BIZ-002 mở rộng A–M/RACI/dictionary/tích hợp/KPI/scenario/readiness; phân biệt U quyết định người dùng, O quan sát nguồn, D thiết kế, Q chưa đủ căn cứ, R runtime | [Bộ thiết kế BIZ-002](architecture/TP_BIZ002_DESIGN_PACKAGE.md); Q9–Q14 bổ sung theo domain. Không coi source Excel/ảnh, walkthrough hoặc checker là quy chế được công ty duyệt; không ledger/workflow engine song song |

RACI/capability/transition mới, policy field/export/attachment, SLA/threshold/retention và mô hình tích hợp chỉ trở thành quy tắc được áp dụng sau cổng theo [readiness](architecture/TP_BIZ002_ACCEPTANCE_AND_READINESS.md); chưa có quyết định nào đóng Q1–Q14 trong lượt tài liệu này. DEC-013–017 tiếp tục hiệu lực trong phạm vi đã ghi.

## CTR-002a — Mở code draft/submit/return chỉ trên test (28/10/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-020 | Người dùng xác nhận 28/10/2026 | Cho phép chuyển CTR-002a-P1 sang code chỉ trên database test với dữ liệu giả và actor fixture, dù Q2 còn mở: draft/sửa draft, submit → `in_review`, trả lại có lý do → `returned`, sửa và submit lại. Q2 vẫn chặn người dùng thật/pilot | Capability CTR-002a là grant theo project + phòng ban do superuser/fixture tạo; không cấp cho user thật, không suy từ chức danh. Ngoài phạm vi: BASE approved/verified, chữ ký/thẩm quyền ký, effectivity, nghiệm thu/thanh toán/giao khoán, cancel revision, quản trị grant người dùng thật |
| DEC-021 | Người dùng giao AI quyết định cho CTR-002a-P1 ngày 28/10/2026; giới hạn ở test/thiết kế | Người lập KD có assignment được draft/edit/submit; commercial reviewer phải khác người gửi của từng submission; vì vòng review có kiểm tra số tiền nên sender/reviewer cần `financial_read`; sửa tiền thêm `financial_draft_edit`. Không suy quyền từ chức danh; không mở legal/BASE/payment/grant người thật | Đây là chính sách kỹ thuật/nghiệp vụ giới hạn cho test fixture, không phải quy tắc bốn mắt toàn công ty, không bổ nhiệm Q2-A/Q2-B hoặc thẩm quyền ký; backend phải enforce self-review và UI loại người gửi |

## VI-002 — Một bộ nhãn tiếng Việt cho `tp_contract` (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-025 | Người dùng xác nhận 02/11/2026 (“Use new catalog”) | Nhãn selection của `tp_contract` lấy theo `custom_addons/tp_contract/i18n/vi.po` (VI-001). Catalog của `tp_demo_workspace` dùng cùng bản dịch theo từng XML ID, và chuỗi cứng của demo cũng đổi theo. | Đóng G9 trong source, không đổi state key, XML ID, domain hay dữ liệu. Runtime demo18109 chưa nâng cấp. Nhãn React contracts (G10): người dùng chọn giữ nguyên ngày 02/11/2026 (“Leave React as is”), nên React và Odoo tạm hiện hai cách viết. |

## NATIVE-DATA-003 — Yêu cầu prompt dữ liệu mẫu liên thông (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-026 | Người dùng yêu cầu soạn prompt, chưa thực thi | Chuẩn bị bộ dữ liệu mẫu hiện có trên dev 18069 thành tình huống vận hành liên thông theo người dùng/dự án/chứng từ; tái sử dụng ID, giữ nguồn gốc giả lập, chứng minh bằng actor/action/quyền và dữ liệu nguồn. [Prompt NATIVE-DATA-003](prompts/CLAUDE_NATIVE_DATA003_CONNECTED_OPERATIONS.md) mô tả phạm vi để giao Claude sau. | Không coi đây là nghiệm thu hoặc lệnh chạy migrator ở phiên viết prompt. Phạm vi đề xuất khi giao thực thi gồm actor giả/login, linkage và native action an toàn; policy managed-task/TP workflow và posting/thu chi dev cần batch riêng, không tự mở người dùng thật/pilot hoặc phục hồi demo cũ. |

## NATIVE-DATA-003 — Chuyển vai trò thực thi giới hạn (02/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-027 | Người dùng xác nhận trực tiếp “Chuyển vai trò: thực thi trong phiên này”; đã áp dụng phần an toàn CHG-014 | Cho phiên chính triển khai đúng prompt NATIVE-DATA-003 ở dev18069 sau snapshot/clone. Cho bật login actor giả, hierarchy/linkage, bridge CRM→Project và correction security B3 có spec/test riêng; native submit/approve chỉ khi không posting/payment hoặc gửi ra ngoài. | Ngoại lệ vai trò chỉ task này, không thay DEC-022 mặc định hay DEC-001/013/017/020/021. Ba addon bridge/timesheet scope/dashboard privacy đã clone-test rồi cài dev. Không mở generic managed-task write, TP workflow/grant hoặc hạch toán/thu chi dev. Kết quả `PARTIAL_WITH_GAPS`, [TASK-001](architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md) chờ policy; [runbook/evidence](demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md). Technical audit/business/pilot vẫn riêng, không suy ra từ chuyển vai trò. |


## HR-DASH-001 — Thực thi dashboard và khóa tài khoản (11/11/2026)

| ID | Trạng thái | Quyết định | Cơ sở/ảnh hưởng |
| --- | --- | --- | --- |
| DEC-039 | Người dùng yêu cầu trực tiếp; đã triển khai CHG-20261111-010 | Phiên chính thực thi prompt HR-DASH-001 trong scope này; kiểm18079, backup/restore kiểm chứng, áp18069, không commit/push. Bổ sung khóa/mở, cột Tình trạng Khóa/Mở/Chưa liên kết; thông báo đăng nhập bị khóa và Gửi phản hồi placeholder. | Giữ native Odoo; khóa user tách archive employee. Admin đúng company nhập lý do, bảo vệ tài khoản hệ thống/self; nativeactive + cờHR/tokenrevision, session cũ không hồi sinh. Chỉ thông báo khóa sau credential đúng; feedback chưa gửi backend. Không sửa roster/quyền/password người thật để test. Ngoại lệ vai trò chỉ task, visual/business/pilot riêng; xem guide HR-DASH-001. |
