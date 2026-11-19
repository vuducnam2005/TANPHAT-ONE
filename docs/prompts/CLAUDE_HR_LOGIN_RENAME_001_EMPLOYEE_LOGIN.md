# HR-LOGIN-RENAME-001 — Đổi tên đăng nhập nhân viên

Ngày 19/11/2026, Asia/Saigon. Nguồn: yêu cầu trực tiếp của người dùng
“BỔ SUNG: CHO PHÉP ĐỔI TÊN ĐĂNG NHẬP NHÂN VIÊN”.
Trạng thái: **PROMPT_READY; có WIP backend chưa bàn giao, chưa nghiệm thu tính năng**.
Lượt điều phối `CHG-20261119-009` chỉ tạo prompt và bàn giao tài liệu.

## Prompt giao phiên thực thi

Làm việc trong `C:\TANPHAT ONE`. Task **HR-LOGIN-RENAME-001**, một vertical
slice TP HR native: người có quyền quản lý tài khoản đổi login của đúng user
đã liên kết với nhân viên, giữ danh tính và mọi quyền/dữ liệu khác.
Chọn CHG-ID triển khai mới chưa dùng; không dùng lại CHG-009 của prompt.
Người dùng đã yêu cầu commit/push đúng scope và deploy PC server sau hoàn tất;
không xin lại quyền cho cùng hạng mục, không bắt buộc qua cổng 18079.

Đọc `AGENTS.md`, status, workflow, naming, roadmap, decisions, handoff,
`.agents/skills/tanphat-odoo-delivery/SKILL.md`,
`docs/AI_COORDINATION_WORKFLOW.md`,
`docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md`,
`docs/ui/TP_TABLE_FILTER_STANDARD.md` và inventory tương ứng.
Áp dụng DEC-030/044/053/054/057. Không sửa `odoo/`, `addons/` hoặc làm React
frontend mới. Chỉ đổi API/OpenAPI nếu thực sự thay contract hiện có.

### 1. Baseline phải tiếp nhận trước khi sửa

- HEAD điều phối đã quan sát: `69c22467`; app HR gần nhất `2c397ffb`,
  `tp_hr_workspace` `20.0.1.14.0`, Xuất Excel nhân viên đã giao local/PC server.
  Đọc lại HEAD/runtime thực tế khi nhận prompt, không áp máy móc mốc này.
- Local `scripts/dev.py status`: 18069/`tp_tanphat_dev` và PostgreSQL đang nghe.
  Checkpoint `.local/ai-workflow/active.json` có từ
  `2026-11-18T04:47:10.530617+00:00`; `ai_workflow.py check` FAIL vì code khác
  bản bàn giao. Đây là lệch đã có, không phải tính năng này đã kiểm đạt.
- Đã có WIP chưa commit trong `models/hr_account_wizard.py` và
  `models/hr_history.py` của HR: helper validation/unique/audit,
  `action_open_change_login`, `action_change_login`,
  `action_open_change_login_dialog`, `_tp_change_user_login`, action audit
  `login_change`. Phải đọc diff, xác định provenance và kiểm lại trước tái dùng;
  không coi WIP là bản ứng dụng đã bàn giao hoặc tự nhận là code mới của mình.
- Có nhiều WIP khác (reporting/branding/sidebar/tài liệu...). Không reset,
  stash, xóa hoặc triển khai chúng. Chạy `ai_workflow.py start` để resume
  checkpoint hiện có; không xóa checkpoint hoặc `finish` thay batch khác.
  Tách gói HEAD + đúng diff task để kiểm/bàn giao khi working tree còn lẫn.

Các điểm WIP cần sửa/kiểm, chưa phải kết luận test runtime:

1. WIP thêm regex chỉ chữ thường ASCII và `LOWER(login)`; baseline tạo tài
   khoản chỉ trim, cấm rỗng/khoảng trắng, tối đa 254 ký tự. Native
   `res.users._get_login_domain` dùng so sánh `=` và constraint `UNIQUE(login)`.
   Không có căn cứ chuyển toàn hệ thống sang login chữ thường/không phân biệt
   hoa thường. Không dùng WIP để tự chốt policy mới.
2. WIP kiểm trong action HR nhưng chưa có lớp xử lý đổi login tương ứng ở
   `res.users.write`: phải kiểm đường ORM/RPC/import/API trực tiếp, audit và
   duplicate/race; context người gọi gửi lên không phải giấy phép.
3. Action client `tp_hr_workspace.change_login` được trả về trong WIP nhưng
   chưa thấy đăng ký UI/assets hoặc nút trong `views/workspace.xml` tại mốc
   rà soát. Phải hoàn thành xuyên backend → UI → reload → kiểm thử.
4. Wizard đã có `_employee()` khóa employee/resource và đối chiếu
   `expected_user_id`; không tự lấp lại expected từ liên kết hiện tại khi
   người dùng xác nhận, vì sẽ làm mất kiểm stale. Kiểm quyền lại sau khóa,
   không tin readonly field/context do client gửi làm căn cứ phân quyền.

### 2. Các điểm tích hợp hiện có

| Nguồn | Trách nhiệm cần tái sử dụng |
| --- | --- |
| `custom_addons/tp_hr_workspace/models/hr_workspace.py` | `tp_user_login` related `user_id.login`, đang `store=True, readonly=True`; account status, `action_open_account_dialog`, export schema `_build_xlsx` |
| `custom_addons/tp_hr_workspace/models/hr_account_wizard.py` | Wizard tài khoản, `_employee`, `_tp_account_admin`, tạo/reset/khóa tài khoản, guard liên kết danh tính |
| `custom_addons/tp_hr_workspace/views/workspace.xml` | Chi tiết nhân viên `page_account`, `.o_tp_hr_account_actions`, account wizard |
| `custom_addons/tp_hr_workspace/static/src/profile/account_credentials.*` | Mẫu Dialog native OWL, lỗi gần input, busy, focus và `soft_reload` |
| `custom_addons/tp_hr_workspace/static/src/profile/employee_profile.js` | Form controller và focus nút mở thao tác tài khoản |
| `custom_addons/tp_admin_delegation/models/hr_accounts.py` | `tp_can_manage_account`, policy công ty/actor/target tài khoản hiện hành |
| `custom_addons/tp_admin_delegation/models/guards.py` | Guard DEC-054 của `res.users.write`, `_is_protected_original_target`; không suy admin gốc từ group system |
| `custom_addons/tp_admin_delegation/views/native_navigation.xml`, `views/hr_profile.xml` | Form HR kế thừa và đường xem hồ sơ của admin; tránh nút chỉ hiện trên một lối mở |
| `custom_addons/tp_hr_workspace/models/hr_history.py` và model `tp.hr.employee.audit` | Lịch sử/audit sẵn có; không tạo sổ danh tính cạnh tranh |
| `custom_addons/tp_hr_workspace/models/my_profile.py`, `controllers/export.py` | DTO hiển thị login và xuất Excel có quyền; đọc nguồn related hiện có |
| `custom_addons/tp_web_login/models/res_users.py`, `models/session_guard.py` | Khóa HR và một phiên web/PWA theo database/user; giữ DEC-057 |

Đọc thêm caller và MRO thực tế trước sửa. Không thêm phụ thuộc ngược HR →
admin delegation gây vòng dependency; policy bridge đặt ở lớp addon thích hợp.
Chỉ sửa addon/manifest/test thực sự cần, không tạo addon riêng rỗng cho đổi login.

### 3. Giao diện bắt buộc

- Vị trí chính: **TP HR → Danh sách nhân viên → chi tiết → Tài khoản →
  Đổi tên đăng nhập**. Hiển thị khi có `user_id` và người đang thao tác được
  policy quản lý tài khoản hiện hành cho phép với đúng target/công ty.
- Hộp thoại có nhân viên đang sửa (readonly), tên đăng nhập hiện tại
  (readonly), tên đăng nhập mới, **Lưu thay đổi** và **Hủy**.
- Giải thích đúng: **“Sau khi đổi, sử dụng tên mới cho lần đăng nhập tiếp
  theo. Mật khẩu giữ nguyên.”** Bổ sung rõ tài khoản được đổi cần đăng nhập
  lại bằng tên mới; không nói đổi mật khẩu hoặc tự tạo alias.
- Nhân viên chưa có tài khoản giữ thao tác **Tạo tài khoản riêng** hiện có,
  không có nút đổi tên. Không yêu cầu tạo lại employee hoặc user.
- Validate ngay dưới ô nhập; backend trả lỗi thì dialog còn mở, giữ input
  để sửa và không hiện thông báo thành công. Không lộ login trùng thuộc ai.
- Nút Lưu chống bấm đôi, trạng thái đang lưu; focus input khi mở, Enter lưu,
  Hủy/Esc không ghi, trả focus nút mở khi đóng. Desktop/mobile dùng được.
  Lỗi mạng/5xx không biến thành thiếu quyền/hết phiên hoặc tự gửi lại lệnh ghi.
- Sau thành công reload model/list/account dialog bằng cơ chế native đang có,
  cập nhật giá trị related; không vá DOM hoặc giữ một tên login độc lập ở UI.
  Nếu cần identity check hiện hành thì tái sử dụng, không hỏi/đổi mật khẩu mới.

### 4. Backend, dữ liệu và đồng thời

- Đổi **`res.users.login` trên đúng `employee.user_id`**. Khóa/đọc lại liên kết
  trong transaction, chặn hộp thoại cũ khi user hoặc login nguồn đã đổi theo
  cách kiểm phiên bản phù hợp; không chuyển sang target khác một cách âm thầm.
- Giữ user ID, employee ID, resource/partner link, password hash, avatar,
  phòng ban, chức vụ, company, nhóm/quyền, trạng thái khóa/archive, grant ledger
  và lịch sử nghiệp vụ. Không gọi create/reset password/sync identity ngoài
  nhu cầu chỉ đổi login; không tạo hồ sơ hoặc sao chép user.
- `tp_user_login` tiếp tục là related của `user_id.login` với đặc tính lưu
  hiện có; không biến thành cột tên độc lập, không cho RPC/import ghi trực tiếp
  related để né kiểm quyền/audit ở nguồn.
- Dùng quy tắc validation đã chứng minh từ luồng login/create hiện hành:
  trim ngoài, chặn rỗng/chỉ khoảng trắng/khoảng trắng bên trong, tối đa 254 ký
  tự; xử lý ký tự điều khiển/đầu vào không hợp lệ an toàn. Giữ nguyên quy tắc
  hoa/thường của xác thực, không tự lowercase/casefold hoặc cấm uppercase/Unicode
  bằng regex mới không có căn cứ. Cùng input phải được hiểu như nhau ở UI,
  create, rename và lần đăng nhập tiếp theo. Không đổi các login đang có.
- Duplicate kiểm **toàn database**, mọi company, cả inactive/archive/HR-locked,
  bỏ chính user đang sửa; không bị `active_test` hoặc record rule che trùng.
  Không tự thêm hậu tố, đổi user khác hoặc gộp user.
- Xác minh constraint `res_users_login_key` đang tồn tại và hiệu lực tại runtime;
  tái sử dụng UNIQUE(login) native làm hàng rào cuối cho race qua mọi đường ghi.
  Không coi `search_count`/advisory lock riêng action là constraint toàn hệ thống.
  Nếu thực tế có normalization khác thì chứng minh, kiểm collision/migration
  trước; tuyệt đối không tự sửa user thật để làm index chạy được.
- Vi phạm unique trong savepoint chuyển thành lỗi tiếng Việt rõ cho ô login;
  xử lý đúng constraint liên quan, không nuốt mọi lỗi DB. Hai yêu cầu cạnh tranh
  một tên phải chỉ có một bên thành công; bên thua không đổi login/audit/quyền.
- Đổi login và audit phải atomic. Lỗi validation, quyền, unique hoặc ghi audit
  thì rollback toàn bộ. Không commit thủ công trong model action.

### 5. Quyền trên mọi đường gọi và audit

- Cùng policy quản lý tài khoản hiện hành áp ở backend cho mở dialog, submit,
  HR action, trực tiếp `res.users.write`, RPC/API/import và đường related.
  Quyền đọc hồ sơ/HR/chức danh không tự cấp quyền đổi login. Nhân viên thường
  không tự đổi qua Hồ sơ cá nhân, Preferences hoặc request trực tiếp.
- `tp_can_manage_account` hiện chặn tự thao tác, protected system/original
  admin/share và user có công ty ngoài phạm vi; giữ các giới hạn hiện hành.
  Không dùng task này để mở self-service, đổi quyền admin hoặc thu hẹp admin
  được cấp về phòng ban theo policy cũ.
- Admin được cấp không đổi login admin gốc hoặc quản trị credential admin khác
  trái DEC-054. Dùng helper xác định admin gốc/source guard đang có, không
  hardcode username hoặc chỉ xét `base.group_system`. Không nới guard admin gốc.
- Trước `sudo` phải kiểm actor gốc/target/scope; vẫn giữ actor gốc khi audit.
  Nếu cần capability nội bộ dùng sentinel không thể giả qua JSON/context;
  không tin boolean như `skip_check`, `is_admin`, `from_wizard` từ client.
- Đường ghi được phép nào cũng phải validate, unique và lưu audit đúng một lần;
  không cho write trực tiếp có quyền bỏ qua audit. Giữ CLI/module loader hợp lệ
  theo convention bảo mật hiện hành, không tạo lối bypass HTTP bằng superuser.
- Tái sử dụng audit bất biến có người thực hiện, thời gian server, account ID,
  employee ID, tên cũ và mới. Lịch sử nghiệp vụ cũ giữ snapshot gốc; không sửa
  các log lịch sử cho “đồng bộ”. Không ghi password/hash/token/session nonce
  hoặc credential vào chatter, log, response, evidence hoặc Git.

### 6. Đồng bộ và phiên đăng nhập

- Sau lưu và mở lại/reload, list nhân viên, chi tiết, quản lý tài khoản,
  màn nghiệp vụ đang hiển thị login và Excel nhân viên xuất mới phải cùng tên
  từ nguồn DB. Rà mọi caller/DTO/cache liên quan; không tự đổi nhãn người thực
  hiện hay nội dung snapshot lịch sử vốn cần bảo toàn. Không sửa file Excel đã
  xuất trước đó hoặc dùng Excel làm database.
- HTTP login bằng tên mới + cùng mật khẩu thành công; tên cũ thất bại.
  Không thêm alias/fallback đăng nhập bằng tên cũ hoặc tự giữ phiên qua login cũ.
- Native `_get_session_token_fields()` chứa `login`: đổi login làm phiên cũ
  không còn hợp lệ. Giữ chính sách một thiết bị theo user ID (DEC-057), MFA,
  HR lock và cơ chế re-login hiện có; không tự tạo session mới hoặc tự xác thực
  lại bằng mật khẩu quản trị. Thông báo rõ việc cần đăng nhập lại, không gọi đổi
  login là “đã đăng nhập nơi khác” nếu không có sự kiện đó.

### 7. Kiểm thử và bằng chứng bắt buộc

Đọc/tái sử dụng `tests/test_account_role.py`, `test_hr_workspace.py`,
`test_employee_export.py`, `tp_admin_delegation/tests` và
`tp_web_login/tests/test_native_login.py`, test focus/credentials/session hiện có.
Chỉ thêm test cho rủi ro/thay đổi thực. Mọi fixture hoặc login ghi thử chỉ dùng
dữ liệu giả trên môi trường đã được phép; **không đổi tài khoản người thật để
thử, kể cả đổi rồi hoàn tác; không chạy fixture trên main/server**. Không tự
tạo DB/cổng/clone mới, không bắt buộc mở 18079. Nếu thiếu môi trường ghi an
toàn thì ghi rõ NOT_RUN, không thay bằng khẳng định đã đạt.

| Ca | Kết quả và bằng chứng cần bàn giao |
| --- | --- |
| Admin đủ quyền đổi login user thường | Cùng user/employee/resource/partner IDs; nguồn `res.users.login` và related đổi sau lưu/reload |
| Bảo toàn | So snapshot password hash (chỉ so, không xuất), avatar hash, quyền/group/grant, phòng ban/company/job, trạng thái user, liên kết và số lịch sử nghiệp vụ; chỉ login/audit/metadata hợp lệ đổi |
| Trống/khoảng trắng/ký tự/độ dài/hoa thường | UI và backend cùng convention hiện hành; lỗi tại input, nguồn và audit giữ nguyên |
| Trùng active/locked/archive/khác company | Bị chặn toàn DB, không lộ user trùng, không sửa user nào |
| Thiếu quyền/giả context/self-profile | Action/wizard và ORM/RPC/import/related trực tiếp đều từ chối; không có side effect |
| Admin được cấp → admin gốc | Mọi đường bị chặn; quyền quản trị nghiệp vụ bình thường giữ nguyên |
| Hai rename hoặc create + rename cùng tên | Hai giao dịch độc lập/connection, đúng môi trường được phép: chỉ một success, không login trùng, bên thua giữ tên cũ/audit không có success giả |
| Dialog stale/đổi liên kết/quyền trong khi mở | Backend không đổi nhầm target hoặc dùng quyền cũ; báo mở lại dialog |
| Audit lỗi/unique lỗi | Rollback cả login và audit; không thông báo thành công |
| UI/no-account/Hủy/keyboard/mobile | Đúng vị trí/visibility, giữ tạo tài khoản cũ, không ghi khi Hủy, không lỗi JS/tràn ngang, focus hợp lệ |
| Đồng bộ/Excel | List/detail/account/DTO theo quyền sau reload; export XLSX thật qua exporter hiện có chứa tên mới, không có password/token |
| Login/phiên | Dữ liệu giả: tên mới+cùng password OK, tên cũ fail, cookie cũ bị xử lý theo native, re-login và một thiết bị/MFA/HR lock giữ |

Chạy Python AST/Ruff phù hợp, XML/assets/OWL và browser cho UI thực; test ORM/
security/HTTP/race phù hợp môi trường. Không gọi mock là test Odoo/HTTP thật.
Không chạy React build toàn bộ vì đổi native HR. Kiểm bảng/list/search/export
bị ảnh hưởng theo DEC-044; cập nhật inventory coverage hoặc N/A có lý do nếu
chỉ thêm dialog không có bảng, không tự thêm filter engine hoặc bảng audit mới.

### 8. Giao bản, rollback và đầu ra

1. Cập nhật status/changelog, tài liệu quyền/kiến trúc có đổi, acceptance tại
   `docs/demo/HR_LOGIN_RENAME_001_ACCEPTANCE.md`; ghi từng PASS/FAIL/NOT_RUN,
   lệnh/log an toàn, ảnh UI đúng nguồn, không nhận business acceptance thay user.
2. `git diff --check`, kiểm scope và workflow. Không `finish` snapshot lẫn WIP
   của batch khác để báo PASS; seal đúng gói sạch đã kiểm và giữ checkpoint gốc
   theo quy trình handoff hiện hành, nêu rõ lệch tồn tại nếu còn.
3. Bump manifest addon thực sự đổi; xác định rõ có cần `-u` do view/audit/
   security thay. Commit/push đúng phạm vi, không `git add .`, không force push,
   không mang reporting/branding/sidebar dở vào release.
4. Kiểm baseline PC server hiện có: alias `server-pc`, địa chỉ bàn giao
   `192.168.1.73`, checkout `C:/Projects/TANPHAT-ONE`, container `tp-odoo`,
   mount `/workspace` (phải kiểm lại). Backup **riêng từng môi trường** DB +
   filestore + source/config + SHA256 trước upgrade/đổi quyền/dữ liệu; kiểm
   dump đọc được. Không dùng backup local thay server hoặc restore test đè main.
5. Deploy đúng commit đã push lên local18069/PC server theo policy; upgrade/
   restart đúng module/service, giữ tunnel/domain. Asset có mtime mới và kiểm
   JS/CSS bundle thực public bằng nội dung/checksum, không chỉ nhìn file source.
   Smoke không đổi login người thật hoặc đăng nhập đá phiên người đang dùng.
6. Lỗi do release thì sửa hoặc rollback có bảo toàn dữ liệu mới; không restore
   snapshot cũ máy móc. Chưa đủ bằng chứng phải ghi đúng giới hạn, không báo đã
   kiểm đăng nhập/đổi tên khi mới kiểm health/asset.
7. Bàn giao vị trí thao tác, commit SHA/push, addon version, môi trường/public
   URL thực, backup/rollback, test đã chạy/chưa chạy và bằng chứng bảo toàn.
   Chỉ đánh `MAIN_AND_PC_SERVER_APPLIED` sau xác minh runtime thực; prompt này
   không phải bằng chứng tính năng đã triển khai.

Ngoài scope: cấp/thu admin, đổi phòng/vai trò, tạo lại danh tính, tự đổi login
người thật, alias/SSO mới, redesign login/branding/reporting, thay chính sách
một thiết bị hoặc migration đồng loạt tên tài khoản.
