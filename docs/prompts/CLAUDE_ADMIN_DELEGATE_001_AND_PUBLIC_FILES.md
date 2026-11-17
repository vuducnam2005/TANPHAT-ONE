# ADMIN-DELEGATE-001 + DEPLOY-MEDIA-001 — Quản trị được ủy quyền và tệp trên máy chủ

Ngày 17/11/2026. Prompt CHG-20261117-003, DEC-050. **Chỉ chuẩn bị; chưa code/cấp quyền/sửa server.**

## 1. Mục tiêu và thứ tự làm

Làm việc trong `C:\TANPHAT ONE`, vai trò thực thi. Hoàn thành hai phần sau,
giữ một database cho mỗi môi trường, một tài khoản riêng cho mỗi người và
giao diện native OWL/QWeb/SCSS hiện hành. Không dựng FE hoặc tài khoản admin
thứ hai cho người được ủy quyền. Không commit/push.

1. **DEPLOY-MEDIA-001:** chẩn đoán ảnh nhân viên không hiện sau deploy;
   kiểm cả ảnh, PDF, Word, Excel và file đính kèm qua link public. Chuẩn bị
   bản sửa có bằng chứng, không kết luận thiếu filestore chỉ từ screenshot.
2. **ADMIN-DELEGATE-001:** admin chính cấp/thu hồi quyền quản trị cho người
   dùng bất kỳ thuộc hệ thống nội bộ; người đó quản trị các phòng khác nhưng
   **tại phòng mình vẫn giữ nguyên quyền nghiệp vụ trước khi cấp**.

Đọc AGENTS/PROJECT_STATUS/CHANGELOG/AI_CHANGE_WORKFLOW/ROADMAP/DECISIONS,
skill `.agents/skills/tanphat-odoo-delivery/SKILL.md`, policy quyền, chuẩn
filter và runbook liên quan. Theo start/finish/check đúng batch; giữ foreign
diff và checkpoint của batch khác. Viết acceptance trước sửa application.

Baseline tài liệu CHG-20261117-002 ghi branding đã áp test/main/server:
`tp_branding` 20.0.1.0.0, URL `/app`, `/dang-nhap`, credit TADIC và login
UI-LOGIN-002 giữ. Đây là bàn giao trước, không thay kiểm source/runtime hiện tại.
Local: test18079 `tp_tanphat_test`, main18069 `tp_tanphat_dev`, PG55432.
Server theo runbook: Docker `tp-odoo`, `192.168.1.73:8069`, bind mount
`C:\Projects\TANPHAT-ONE`, workdir `/workspace`, config
`/workspace/docker.odoo.conf`. Xác minh trước chạy; không dùng lệnh container
cũ `/etc/odoo/odoo.conf` khi topology thực khác.
Public: `https://hybrid-send-ready-ballot.trycloudflare.com`.

## 2. Quyền admin chính và quyền được ủy quyền

Đặt nhãn **Quản trị chính**, **Quản trị được ủy quyền**, **Người dùng nghiệp vụ**.
Đây là hai trục độc lập: quyền quản trị hệ thống và vai trò/chức vụ phòng ban.
Cấp ủy quyền không làm nhân viên thành trưởng phòng, không thêm assignment,
quyền tiền, chữ ký, quyền duyệt/chốt hoặc chức vụ mới trong phòng mình.

| Tác vụ | Admin chính | Quản trị được ủy quyền |
| --- | --- | --- |
| Xem các phòng ban và công cụ quản trị đã triển khai | Như hiện tại | Có, theo backend; placeholder vẫn ghi Đang phát triển |
| Xem/lập/sửa/xóa nghiệp vụ thuộc phòng mình | Như hiện tại | **Đúng quyền nghiệp vụ vốn có**, không tăng quyền đọc/tiền/duyệt/xóa |
| Xem/lập/sửa/xóa dữ liệu thuộc phòng khác | Như hiện tại | Như khả năng admin hiện có trong phạm vi công ty được phép, giữ điều kiện state/workflow/lịch sử |
| Quản lý hồ sơ nhân viên/tài khoản thường của phòng khác | Như hiện tại | Có qua action đã kiểm quyền, giữ bảo vệ self/tài khoản đặc quyền |
| Thay chức vụ, phòng ban, quyền của chính mình | Theo policy hiện có | Không, kể cả thông qua HR/config/import/phiên bản hồ sơ |
| Cấp/thu hồi ủy quyền; cấp nhóm admin/quyền bảo mật | Có | Không; không tự cấp, không cấp tiếp cho người khác |
| Sửa/khóa/xóa/reset tài khoản admin chính hoặc user đặc quyền khác | Theo policy hiện có | Không |
| Sửa security rules, server action Python, module hoặc DB/system credentials | Theo policy hiện có | Không; các công cụ có thể phá giới hạn chỉ dành admin chính |

Nêu rõ đây là quản trị **có giới hạn bắt buộc theo yêu cầu**, không phải
superuser. Không hứa vừa cấp toàn quyền hạ tầng vừa ngăn người đó sửa policy.
Không thay baseline admin chính thành quyền superuser nếu hiện không có.
Không hardcode login `admin`, tên nhân viên hoặc số UID làm tiêu chí quyền.
Xác định thẩm quyền admin chính từ cơ chế hiện có và giữ nhóm được bảo vệ;
không tự bổ nhiệm người thật mới trong quá trình cài module.

**Ví dụ bắt buộc:** nhân viên KH-KD chỉ đọc/sửa hồ sơ được giao → cấp ủy quyền
→ vẫn chỉ đọc/sửa đúng các hồ sơ và trường tiền đã được giao ở KH-KD,
không tự đổi chức vụ/duyệt hồ sơ của mình; có thể quản trị hồ sơ ở phòng khác
như admin trong phạm vi được phép → thu hồi → mất toàn bộ phần thêm,
còn nguyên quyền KH-KD gốc.

## 3. Phạm vi phòng ban phải xác định ở backend

Lập bảng model/action/field/caller và nguồn xác định company/department thực.
Sử dụng ID/quan hệ đang có, ví dụ HR hiện hành, `tp_department_id` của dự án,
phòng ban trên report và nguồn/parent của dòng con, tài liệu, CRM/hợp đồng.

- Không xét quyền theo tab đang mở, URL, tham số context/frontend, tên phòng
  hoặc tên người dùng. Mở hồ sơ KH-KD từ HR/Reporting/URL khác vẫn là KH-KD.
- Mô hình quyền: baseline nghiệp vụ hiện hành cộng phần quản trị được ủy quyền
  cho đối tượng thuộc phòng khác; không cộng phần thêm nếu đối tượng thuộc
  phòng mình hoặc giao thoa phòng mình. Role/grant nghiệp vụ hợp lệ cấp riêng
  sau này vẫn hiệu lực, không đóng băng toàn bộ quyền vào một snapshot cũ.
- Hồ sơ liên phòng, chưa xác định được phòng hoặc có nguồn từ phòng mình:
  dùng baseline, không mặc định quyền cao. Dữ liệu chung toàn công ty như
  danh mục/kho phải có rule theo tác vụ rõ; ngoại lệ quản trị không cho phép
  sửa HR/danh tính/grant để vượt quyền KH-KD.
- Không được chuyển phòng sở hữu của hồ sơ để lách. Kiểm cả trước/sau khi
  create/write, đổi parent/owner/project/company; cross-department transfer
  có ảnh hưởng quyền dành admin chính hoặc đúng workflow chuyên biệt hiện có.
- Người kiêm nhiệm nhiều phòng: bảo vệ mọi phòng nghiệp vụ đang có trách nhiệm
  hiệu lực; không lấy `limit=1` để bỏ sót. Chuyển phòng hợp lệ do admin chính
  thực hiện phải tính lại phạm vi ngay, thu hồi đường quyền cũ tương ứng.
- Dashboard/filter/options/count/export, search/read_group, báo cáo tổng hợp
  chỉ lấy hợp của các tập được phép; không dùng tổng toàn công ty để lộ hồ sơ
  ở phòng mình mà baseline cấm. File/chatter/history đi theo quyền nguồn.
- Tất cả model chưa được rà soát: baseline, không mở quyền tự động. Ghi
  coverage/gap cụ thể, không báo full hệ thống khi mới sửa menu HR.

## 4. Triển khai quyền, chặn tự nâng quyền và thu hồi

Đọc kỹ ít nhất các caller thực tế sau rồi chọn thay đổi nhỏ đủ dùng:
`tp_hr_workspace/models/hr_account_wizard.py` (`_tp_account_admin`, tạo/khóa/
reset), `hr_role.py`, `department_transfer.py`, `workspace_scope.py`,
`identity.py`, `my_profile.py`, `tp_organization` (employee/version/resource),
`tp_project` (department_role/assignment/grant), `tp_kd_workspace` (native
security/grant), `tp_contract`, `tp_reporting` và `tp_equipment/models/common.py`.
Home hiện phụ thuộc menu tree, `user.isSystem` và native menu groups; quyền
Kho và nhiều action HR hiện kiểm `base.group_system` độc lập.

- Dùng cơ chế riêng/capability rõ cho ủy quyền, reuse helper/ACL/rules hiện có.
  Không cấp `base.group_system`, `base.group_erp_manager`, `tp_core.group_manager`
  hoặc nhóm implied rộng cho delegate để làm menu hiện rồi chặn bằng CSS.
  Không sửa core `odoo/`, `addons/`, không patch toàn cục `has_group/check_access`.
- Lưu admin cấp, user nhận, company/phạm vi, trạng thái, thời điểm cấp/thu,
  lý do, admin thu hồi; lịch sử giữ, chỉ admin chính thay đổi qua action.
  Không tạo framework policy mới hoặc sao chép toàn bộ quyền mỗi lần cấp.
- Backend chặn trực tiếp và gián tiếp self-escalation: chức vụ/vai trò,
  group/implied group, grant/assignment, phòng ban/company, user/employee/resource
  link, alternate employee/version, clone/import/nested relational commands,
  reset password/API key/MFA/impersonation của tài khoản đặc quyền.
  Không cho A cấp quyền cho B để B nâng quyền lại cho A.
- Chặn đổi cơ cấu/manager của phòng mình nếu qua đó làm thay đổi thẩm quyền.
  Thông tin cá nhân vốn được tự sửa vẫn cho sửa theo allowlist hiện hành.
- Cấp account khác không được truyền groups tùy ý; target user/employee/company
  phải kiểm lại ở server. Delegate không sửa chính bản ghi ủy quyền của mình.
- ACL Odoo là cộng quyền, group record rules có thể OR; thêm một deny group
  không đủ. Chứng minh tác động của rules/field groups và custom `sudo()`.
  Nếu cần `sudo`, giữ actor gốc, kiểm operation/scope/fields trước nâng quyền,
  không để controller/wizard bỏ qua policy. Không tin flag context từ client.
- Thu hồi có hiệu lực cho request tiếp theo sau transaction commit, kể cả tab
  cũ, direct RPC/API và nhiều worker; invalidate đúng cache/menu/identity/quyền.
  Request ghi phải đọc quyền mới ngay trước ghi và đồng bộ với thu hồi để
  request chờ không dùng quyền đã bị rút. Giao dịch đã commit trước đó không
  tự đảo ngược; dữ liệu đã tải xuống không thể thu hồi khỏi máy người dùng.
- Thu hồi không xóa nhóm/assignment/quyền nghiệp vụ gốc hoặc thay mật khẩu;
  không khóa tài khoản khi chỉ hạ quyền quản trị. Nếu bắt đăng nhập lại thì
  phải là biện pháp bổ sung, backend vẫn chặn phiên cũ ngay.

## 5. Giao diện quản trị

Tích hợp vào chi tiết nhân viên/tài khoản hiện có, không tạo trang quản trị
song song. Phân biệt **Chức vụ**, **Vai trò nghiệp vụ**, **Quyền quản trị**.
Hiện badge Người dùng nghiệp vụ/Quản trị được ủy quyền/Quản trị chính và phần
giải thích phạm vi thực. Giữ trạng thái tài khoản Mở/Khóa/Chưa có tài khoản riêng.

Admin chính có **Cấp quyền quản trị** / **Thu hồi quyền quản trị**, modal
preview phạm vi, lý do và xác thực lại admin bằng cơ chế sẵn có. Không hiển
thị/lưu mật khẩu plaintext. Delegate chỉ xem mô tả quyền của mình, không có
nút tự bổ nhiệm. Menu/home/admin tools cùng layout hiện hành, backend trả
capability thật; không giả `isSystem` để hiện toàn bộ công cụ kỹ thuật.

Nếu thêm cột/filter quyền quản trị, theo DEC-044, đồng bộ count/page/export,
đăng ký inventory, không đụng thứ tự phòng ban/mã TP/avatar đã có. Nền sáng,
nút rõ, hover nhẹ/reduced-motion, tiếng Việt, mobile; task không redesign cả HR.

## 6. Chẩn đoán ảnh và tài liệu trên public — không đoán nguyên nhân

Ảnh người dùng gửi hiện placeholder tại danh sách HR. Kiểm đọc ngày17/11:

- Anonymous: `/dang-nhap`200 đúng title, favicon200 đúng ICO, logo mark200 PNG.
- Đã xác thực admin bằng credential cấu hình sẵn, không in secret hoặc reset:
  đọc39 hồ sơ HR và metadata ảnh; ba URL ảnh nhân viên trả cùng PNG6314byte,
  cùng SHA1 (phù hợp ảnh fallback, không là bằng chứng ảnh gốc đã đọc được).
- Hai attachment ảnh partner tải HTTP200 nhưng0byte, checksum không khớp.
  Đối chiếu thêm ba ảnh gốc HR: public HTTP200/0byte; blob local tương ứng
  **tồn tại và checksum khớp metadata server**, gồm một ảnh3.263.360byte.
  Đây là bằng chứng public không phục vụ đúng blob, nghiêng về filestore/
  mount/đọc file; **chưa kiểm trực tiếp filesystem/log origin server** nên
  chưa chốt chính xác thiếu file hay đường đọc/cấu hình.
- Chưa tìm được mẫu PDF/DOCX/XLSX trong truy vấn attachment binary có dung
  lượng0–10MB theo MIME/đuôi file đã thử; không suy ra mọi tài liệu hoạt động
  hoặc toàn database không có tài liệu. Chưa upload file thử lên server.

Evidence private: `.local/admin-delegate001/public_media_probe.json`,
`public_files_authenticated_probe.json`, `public_files_origin_comparison.json`.
Các RPC đã chạy chỉ authenticate/search_read; không thay nghiệp vụ/quyền,
không phục hồi blob, không sửa cấu hình. Metadata ảnh/binary size truthy
không chứng minh file vật lý còn đọc được.

1. Với phiên được phép và record thực có ảnh: capture URL ảnh/network/console,
   status/redirect chain/MIME/magic bytes/kích thước/payload thực. So sánh
   local18069, origin server và HTTPS public đúng cùng record/source; không
   so hai ID khác dữ liệu rồi kết luận tunnel lỗi. Không in cookie/token/PII.
2. Xác định ảnh lưu binary DB hay attachment: `hr.employee.image_*`, `avatar_*`,
   `res.users`/`res.partner`, đồng bộ identity và public employee view. Phân biệt
   ảnh thật chưa từng upload, placeholder hợp lệ, SVG avatar, sai field widget,
   lỗi ACL/session, HTML200 giả ảnh, 404/403/500 và file thiếu vật lý.
3. Kiểm `ir_attachment` metadata `store_fname/checksum/file_size/mimetype` và
   `data_dir/filestore/<database-thực>` trong container, mount volume, quyền
   đọc, case-sensitive path Linux, file tồn tại/hash. DB dump không tự mang
   theo filestore nếu không phải gói backup có tệp. Kiểm đúng DB nguồn/đích.
4. Nếu thiếu: lập manifest thiếu/khác trước, đối chiếu backup/nguồn cùng DB;
   phục hồi **chỉ blob đã xác minh checksum** vào đúng volume bằng quy trình
   an toàn, backup phần bị chạm, không restore cả DB lên server để chữa ảnh,
   không overwrite blob tốt hoặc tạo avatar giả để che dữ liệu thất lạc.
5. Kiểm `/web/image`, `/web/content`, preview/download/Range PDF, route custom,
   company logo/static asset, relative URL và URL host LAN/localhost, HTTPS,
   trusted forwarded headers, CSRF/session/cookie, CSP/mixed content,
   access token theo native. Kiểm branding `/app` không rewrite file/RPC thành
   HTML login; không global replace hoặc đổi toàn tunnel cho một lỗi avatar.
6. Kiểm response/cache Cloudflare/proxy/SW: không cache private attachment
   thành public, không trả file của phiên cũ. Không đổi `ir_attachment.public`
   hàng loạt, mở `/web/content` vô điều kiện hoặc bỏ record rules.
7. Kiểm ảnh/đính kèm ở HR, hợp đồng, KH-KD, Kho, Reporting và avatar account
   cùng nguồn. Xem PDF trong web khi hỗ trợ; Word/Excel gốc ít nhất tải/mở đúng
   định dạng. Không tuyên bố browser có thể render DOCX/XLSX chỉ vì download200;
   không gửi tài liệu nội bộ sang Google/Microsoft viewer ngoài khi chưa được giao.
8. Khi file nguồn thật không có: báo rõ record/file nào thiếu và nguồn cần bổ
   sung ở bằng chứng private. Không hứa phục hồi nếu không còn blob/backup.

Có quyền truy cập hợp lệ sẵn thì dùng để kiểm; không reset mật khẩu, đoán
credential hoặc xin người dùng gửi mật khẩu vào chat. Nếu thiếu phiên/quyền
SSH/Docker, vẫn kiểm công khai/source và hoàn thiện bản sửa/test độc lập;
ghi đúng phần server/record private **CHƯA KIỂM**, không báo đã kiểm đầy đủ.
Không login admin qua LAN nếu làm đổi `web.base.url`; kiểm origin read-only
hoặc bằng phiên không gây thay cấu hình, giữ host public như runbook.

## 7. Acceptance và kiểm thử bắt buộc

Tạo acceptance trước code, actor/env/action/expected/evidence/result. Dữ liệu
giả và thay quyền thử chỉ ở canonical18079, không tạo DB/task hoặc thử cấp
quyền/CRUD người thật trên main/server. Tối thiểu các nhóm sau:

| ID | Kết quả cần chứng minh |
| --- | --- |
| AD01 | Cấp cho hai user ở hai phòng khác nhau; không đổi chức vụ/role/assignment/grant gốc; admin chính vẫn như trước |
| AD02 | Baseline phòng mình trước/sau cấp giống nhau cho đọc/tiền/lập/sửa/xóa/submit/review/chốt/file/export; hồ sơ ngoài phân công vẫn bị chặn |
| AD03 | Phòng khác CRUD theo khả năng admin và state; hồ sơ đã chốt/lịch sử vẫn đúng workflow, company khác không tự mở |
| AD04 | Self promotion/group/grant/transfer/link/version/import/relational command/reparent/context spoof đều bị chặn ở RPC, không chỉ nút UI |
| AD05 | Không chiếm tài khoản admin, không reset mật khẩu/tạo API key/khóa admin hoặc cấp lại delegation; ordinary account action đúng scope vẫn dùng được |
| AD06 | Thu hồi khi tab/user vẫn đang đăng nhập; request tiếp theo/direct API/file/export/multiworker hết quyền thêm, baseline còn; kiểm race grant/revoke/write |
| AD07 | Đổi phòng do admin chính, đa phòng, shared/unknown-source record; đổi parent/scope/bulk nhiều phòng không vượt quyền hoặc ghi một phần |
| AD08 | Dashboard/count/filter/many2one/search/read_group/chatter/attachment/export không lộ tập bị cấm; không phải union rule mở cả KH-KD |
| AD09 | Home và trang chi tiết đúng badge/nút/menu; mobile/keyboard/reduced-motion; người không được cấp không đổi; lock account không thành revoke delegation giả |
| MD01 | Ảnh thật HR/user/avatar cùng record qua local/origin/public trả ảnh đúng; ảnh chưa có hiện placeholder đúng, không giả PASS bằng placeholder |
| MD02 | File ảnh/PDF/DOCX/XLSX thực có quyền: preview nếu hỗ trợ + download; MIME/magic/size/hash so nguồn, Unicode filename, đúng nội dung; file thiếu phân loại rõ |
| MD03 | Anonymous/sai quyền/cross-company/token hết hiệu lực không lấy được tài liệu riêng qua direct URL/cache; public logo vẫn xem được |
| MD04 | Deploy/restart container giữ blob/mount; `/app` và legacy URLs, session/HTTPS/redirect/file/query/SW không lỗi; không HTML200 giả hoặc private cache |

Test Python/Odoo cho security/actions/race/migration, XML/manifest/Ruff và
OWL/HOOT nếu chạm JS; Playwright với assertion request/image decode/download
bytes, không chỉ screenshot/HTTP200. Static code scan không là runtime test.
Không chạy React tests khi không sửa legacy. Ghi PASS/FAIL/NOT_RUN riêng.

## 8. Rollout và bàn giao

Chuẩn bị hai bản thay đổi và acceptance riêng, sửa lỗi media không phụ thuộc
chờ hoàn tất quyền ủy quyền. Hoàn thiện code/test/release trước khi hỏi áp dụng.
Yêu cầu này giao **viết prompt và kiểm tra**, không tự chọn user thật để cấp
quyền hoặc tự deploy policy mới lên server. Nếu phiên thực thi đã có chỉ thị
trực tiếp áp task này lên18069/server thì tiếp tục trong quyền đó, không hỏi lại.
Chỉ thị triển khai branding trước không tự cấp quyền đổi policy/người thật lần này.

Backup đúng DB/filestore/code/config của môi trường trước áp; diễn tập trên
test theo rủi ro, rollout có thứ tự và rollback đã kiểm. Không restore test
đè main hoặc đổi DNS/restart tunnel làm mất URL public. Khi chỉ được viết
prompt, ghi rõ website/main/server chưa sửa; không coi patch local là server fix.

Bàn giao `docs/security/ADMIN_DELEGATE_001_POLICY.md`, coverage model/route/
file, acceptance, user guide thao tác admin và runbook deploy/rollback;
cập nhật PROJECT_STATUS/CHANGELOG/ROADMAP, filter inventory nếu thay bảng.
Logs/ảnh/HAR/manifest thiếu blob tại `.local/admin-delegate001/` ignored,
không đưa cookie/token/password/binary hồ sơ thật vào Git.

Báo cáo cuối tiếng Việt: admin cấp/thu ở đâu; ma trận quyền thật; ví dụ một
nhân viên KH-KD trước/cấp/thu; root cause media bằng chứng; ảnh/file nào xem
được và nơi nào chưa kiểm; môi trường áp/chưa áp; test/gap và rollback.
Chưa cấp quyền cho người thật nếu chưa được chỉ rõ tài khoản; không commit/push.
