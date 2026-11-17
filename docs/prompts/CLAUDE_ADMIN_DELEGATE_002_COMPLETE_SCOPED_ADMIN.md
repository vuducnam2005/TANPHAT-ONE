# ADMIN-DELEGATE-002 — Hoàn thiện quyền quản trị được ủy quyền

Làm việc trong `C:\TANPHAT ONE`. Đây là prompt **triển khai ứng dụng**, tiếp nối
ADMIN-DELEGATE-001, không chạy lại phần cấp quyền/media của prompt cũ.

## 1. Mục tiêu và baseline bắt buộc

Đọc AGENTS.md, PROJECT_STATUS, CHANGELOG, AI_CHANGE_WORKFLOW, DEC-050/051,
skill `.agents/skills/tanphat-odoo-delivery/SKILL.md`,
[audit hiện hành](../security/ADMIN_DELEGATE_002_READONLY_AUDIT.md),
policy/coverage/acceptance001, delivery policy17/11 và source thực tế.
Viết acceptance theo actor/action/source **trước sửa code**.

Kiểm17/11, bàn giao18/11: server có1 delegation hiệu lực, actor có hồ sơ nhân
viên TADIC, capability trả delegated và scope đầy đủ. Local không có delegation.
Các số này là snapshot, phải đọc lại; không coi local là bản sao quyền server.
Runtime: delegation20.0.1.0.1, HR20.0.1.12.0, attendance20.0.1.2.0,
equipment20.0.1.5.1, Reporting20.0.1.1.0. Source27tệp đã đối chiếu máy chủ.

Đã tái hiện bằng `with_user` thật, transaction read-only:

1. Delegate bị chặn `tp.hr.workspace.get_overview`, admin chính mở được.
2. Delegate bị chặn `tp.equipment.dashboard.get_dashboard` và
   `maintenance.equipment.tp_main_summary`, admin chính mở được.
3. Delegate không đọc được `tp.equipment.proposal`.
4. Reporting dashboard: delegate lỗi obligation, **admin chính cũng lỗi
   document**. Tách lỗi baseline admin khỏi phần cộng quyền delegate.
5. Project/task/CRM adapter chỉ cộng read; Reporting chỉ mở đọc subset đơn
   giản; quick assign/swap/return, tồn kho và đề xuất còn baseline.
6. HR list get_view đã trả arch/models, chưa browser render bằng delegate.
   Không nhắc lỗi ListArchParser lịch sử như một lỗi đã tái hiện hôm nay.

## 2. Quy tắc quyền phải giữ

- Admin chính cấp/thu delegation qua ledger, lý do và reauthentication đang có.
  Không tự grant/revoke, reset mật khẩu, đổi group/assignment người thật để thử.
- Cấp quản trị là một trục riêng; **phòng mình vẫn đúng quyền nghiệp vụ hiện
  hành**, gồm quyền đọc, tiền, duyệt/chốt, sửa/xóa. Không đóng băng baseline khi cấp;
  thay đổi phân công hợp lệ từ admin chính vẫn cập nhật theo nguồn sống.
- Ngoài phòng, quản trị các chức năng đã triển khai như admin ứng dụng trong
  company được ủy quyền, giữ validation/state/history và phân tách người duyệt.
  Chưa triển khai vẫn hiện Đang phát triển, không tạo addon rỗng.
- Không tự nâng chức vụ, chuyển chính mình sang phòng khác, đổi employee/user/
  company/team/assignment/grant để vòng scope. Bảo vệ mọi phòng kiêm nhiệm và
  liên kết employee phiên bản hiện hành/lịch sử liên quan theo policy001.
- Delegate không cấp tiếp admin, sửa security/system/ACL/server action, cài
  module hoặc quản lý credential/tài khoản đặc quyền. Quy trình thay vai trò,
  chuyển phòng và phân công duyệt đã dành admin chính vẫn giữ cổng đó.
- Không cấp `base.group_system`, superuser, nhóm HR/Report manager toàn cục,
  HEAD hay grant tiền để làm giao diện chạy. Không patch core/has_group/isSystem.
- Mỗi nguồn phải có company/phòng/parent được xác định ở backend. Unknown,
  mixed với phòng mình hoặc ngoài company giữ baseline; lọc/export/nested RPC
  không được mở rộng. Read-only thành công không chứng minh quyền ghi.

## 3. Triển khai theo từng miền

Tái sử dụng addon `tp_admin_delegation`, helper scope/locks, wizard/workflow
gốc và native OWL/QWeb. Không tạo engine quyền hoặc FE mới.

### A. Ma trận quyền và điều hướng

Lập inventory model → action/RPC → nguồn company/phòng → read/create/edit/
delete/submit/review → file/chatter/export → trước/cấp/thu. Ghi rõ nơi được
mở thêm, ngoại lệ có chủ ý và gap. Phân biệt model ACL với quyền ghi thực
qua wizard; không chỉ kiểm nút hoặc `has_access` cấp model.

Home/sidebar/dashboard phải nhận capability sống, nhãn Quản trị được ủy quyền
và lời giải thích ngắn. Entry phải mở action thực có quyền; không dẫn vào
dashboard luôn AccessError hoặc giả dữ liệu trống khi backend lỗi.
Settings/Apps và chức năng bảo mật vẫn chỉ dành admin chính. Giữ layout chung,
avatar/tên và tiếng Việt; trạng thái permission/error phải dễ hiểu.

### B. Nhân sự và chấm công

- Tổng quan HR mở theo cùng nguồn nhân viên được quyền; KPI/chart/filter/
  drilldown/pager/export thống nhất scope. Không bắt delegate có nhóm HR rộng.
- Hoàn thiện xem hồ sơ, tạo/sửa thông tin nghiệp vụ cho nhân viên phòng khác
  qua action scoped; account create/lock/unlock/reset giữ target guard và
  reauthentication. Không mở native write/unlink cả model để né wizard.
- Dữ liệu riêng tư/hợp đồng/lương/tài liệu áp quyền trên record + field/file
  thật. Giữ policy danh bạ/chấm công chỉ đọc cho nhân viên thường, che dữ liệu
  người khác. Nếu cần mở trường HR cho delegate ngoài phòng, dùng projection/
  action whitelist scoped; không bỏ `groups` toàn cục hoặc dùng sudo trả toàn bộ.
- Xóa/lưu trữ giữ chính sách bản chốt/liên kết, kiểm target đặc quyền và mật
  khẩu admin đúng phiên. Nếu xóa vĩnh viễn vẫn là quyền admin chính, ghi rõ
  ngoại lệ và ẩn nút; không tuyên bố delegate có full HR CRUD.
- Chấm công giữ assignment import/review/lock và cấm tự duyệt. Hiển thị thiếu
  phân công rõ ràng; không tự bổ nhiệm reviewer hoặc sửa công thật khi audit.

### C. Kho thiết bị

- Sửa dashboard/summary/list/detail/đề xuất có cùng nguồn scope, không đổi
  `common.is_admin(env)` thành True cho mọi delegate.
- Giữ giao diện đơn giản đang chốt: ai dùng thiết bị gì/phòng nào, trong kho,
  gán/đổi/trả và yêu cầu đề xuất. Không phục hồi các tab nghiệp vụ đã bỏ.
- Bổ sung policy rõ cho thiết bị **trong kho dùng chung công ty**: có thể cho
  delegate xem kho rảnh trong company để chọn cấp cho phòng khác, nhưng phải
  kiểm lại dưới lock mọi thiết bị/người/phòng nguồn và đích. Không suy rằng
  stock là phòng khác hoặc cho dùng đường stock để đổi thiết bị ở phòng mình.
- Gán/đổi chỉ chọn thiết bị còn trong kho, chưa có người giữ và đủ điều kiện
  gốc. Đổi máy phải nguyên tử trả A/gán B; thất bại không đổi bên nào. Máy có
  chủ, sai company, version cũ hoặc target phòng mình vượt baseline bị chặn.
- Proposal do người/phòng khác gửi: xem/xử lý đúng workflow admin ứng dụng;
  đề xuất actor/phòng mình giữ baseline, không tự duyệt qua quyền ủy quyền.
- Lịch sử thiếu nguồn phòng frozen không tự mở vì người giữ hiện tại đã đổi
  phòng. Bổ sung snapshot tương lai nếu cần; không bịa nguồn lịch sử cũ.

### D. KH-KD, dự án và hợp đồng

- Hoàn thiện thao tác dự án, WBS/task, CRM/hồ sơ dự án, đấu thầu, hợp đồng và
  các tab đã có **ngoài phòng được bảo vệ**. Tái sử dụng command/wizard/backend;
  không chỉ thêm read hoặc nút create trên UI rồi bị backend chặn.
- Mọi scope từ project/header/parent và CRM team/nguồn liên quan phải hợp lệ;
  record hỗn hợp có nguồn phòng mình không được coi toàn bộ là ngoài phòng.
- Giữ revision/state/idempotency, actor thật và audit; không ghi state trực
  tiếp. Chức năng ký/hiệu lực/tài chính chưa có không tự mở chỉ để đạt checklist.
- Quyền tiền/tài liệu ở phòng mình không tăng. Không tự cấp HEAD/assignment
  cho delegate để mở action; adapter phải giới hạn đúng record ngoài phòng.

### E. Trung tâm Báo cáo

- Sửa riêng lỗi baseline admin chính không vào được dashboard/document/
  obligation theo đúng quyền quản trị ứng dụng đã chốt. Không giải quyết bằng
  `sudo()` toàn dashboard hoặc cấp nhóm rộng cho mọi actor.
- Bổ sung scope đọc/thao tác hợp lệ ngoài phòng cho mục tiêu quý → tháng →
  tuần, kế hoạch, báo cáo cá nhân/phòng, nghĩa vụ nộp, nhận xét/chỉ đạo và xuất.
  Không đổi người lập thành reviewer hoặc cho tự chốt báo cáo của mình.
- Report tổng hợp/snapshot/value/carry/dependency phải truy nguồn thực,
  kể cả payload lịch sử. Tách/phân rã phần được phép hoặc từ chối rõ nguồn
  hỗn hợp; không dùng department header để mở số liệu phòng actor.
- Tổng hợp chỉ phần được phép phải ghi phạm vi hiển thị, không gắn nhãn toàn
  công ty cho số chưa đủ. Nguồn chưa xác nhận vẫn chưa xác nhận, không coi là0.
- Không sửa payload snapshot đã chốt; dùng revise/cancel có lý do và workflow.

## 4. Thu hồi, dữ liệu và các đường vòng

Giữ ledger SQL live, authority/source lock và revision để request cũ không
ghi bằng quyền đã thu. Áp mọi adapter mới cho search/read/count/group/filter
options/many2one/export/XLSX/PDF/file/chatter/bulk/nested commands.

Thu hồi bỏ phần quyền cộng thêm, giữ group/assignment và quyền nghiệp vụ gốc.
Không khóa user/đổi mật khẩu để giả làm thu hồi. Tab mở cũ xử lý AccessError
đúng, không trả dữ liệu cũ như request mới. Không hứa thu hồi được file đã tải.
Không thêm public token hoặc stream sudo để sửa lỗi ảnh/tài liệu.

## 5. Acceptance phải có bằng chứng

| ID | Điều kiện đạt |
| --- | --- |
| AD2-01 | Phát hiện ledger thực; không ghi lại 0/0 lịch sử như hiện tại; không hardcode actor. |
| AD2-02 | HR/Kho dashboard delegate ngoài phòng chạy; scope/count/chart/drilldown nhất quán. |
| AD2-03 | Project/CRM/WBS và workflow Contract/KH-KD ngoài phòng có đường thao tác thật, nêu rõ ngoại lệ. |
| AD2-04 | Gán/đổi/trả thiết bị đúng stock chưa có chủ; race hai người chọn một máy không gán trùng; mixed/own/unknown bị chặn. |
| AD2-05 | Reporting admin baseline được xử lý riêng; delegate đọc/thao tác đúng nguồn, cấm tự duyệt và rò snapshot/tài chính. |
| AD2-06 | Tại mọi phòng actor/kiêm nhiệm, quyền nghiệp vụ/tiền trước-cấp-thu giữ baseline sống; không thay chức vụ/group. |
| AD2-07 | Direct RPC, context giả, nested command, import/default/clone/transfer, account reset không lách self/security/đặc quyền. |
| AD2-08 | Thu hồi ở phiên cũ/đang mở wizard và cấu hình worker thực: request mới bị chặn, quyền gốc giữ. |
| AD2-09 | Nhân viên thường chỉ xem danh bạ/công như trước; file/private field/export không mở thêm. |
| AD2-10 | Browser HR/Kho/KH-KD/Báo cáo thực tế, desktop/mobile, modal/back/filter/pager/export có evidence; lỗi thiếu quyền hiển thị rõ. |

Ghi từng hàng PASS/PARTIAL/NOT_RUN với actor/source/env/command/log. Kết quả
Odoo test001 hoặc model `get_view` không thay browser bản cuối; hai transaction
DB không thay bằng chứng nhiều worker; suite cũ không chứng minh source mới.

## 6. Giao bản ngay theo chỉ thị mới

- Áp local18069 và PC server hiện tại, push Git/deploy từng slice đã hoàn tất;
  không chờ hỏi lại rollout. **Không bắt qua18079, không tạo clone/DB khác.**
- Xác minh source/diff/server/dependency trước sửa; giữ Reporting/branding/
  login/sidebar và hunk docs batch khác. Không broad pull/copy dirty tree,
  không `git add .`, không nhận foreign source là đã kiểm.
- Trước thay schema/quyền/dữ liệu: backup DB/filestore/source/config đúng
  môi trường, checksum và khả năng đọc backup; chuẩn bị rollback đúng gói.
- Kiểm AST/Ruff/XML/JS phù hợp và test thuần không DB; kiểm chỉ đọc runtime/
  smoke public với quyền actor thực. Không tạo fixture/grant thử, CRUD phá dữ
  liệu, sửa công, chốt báo cáo hoặc reset tài khoản thật trên main/server.
  Không chuyển suite có fixture sang DB đang dùng. Ca ghi/race chưa thể chạy
  theo chính sách hiện tại phải ghi NOT_RUN; không biến static check thành PASS.
- Server `server-pc`, Docker `tp-odoo`, source `C:\Projects\TANPHAT-ONE`,
  runtime `/workspace/docker.odoo.conf`, DB `tp_tanphat_dev` — kiểm lại trước dùng.
  Public `https://hybrid-send-ready-ballot.trycloudflare.com`; đăng nhập origin
  public để giữ baseURL. Không đổi tunnel/domain hoặc mở port mới.
- Cập nhật version/coverage/policy/acceptance/guide/filter inventory khi chạm
  UI bảng; ghi rõ phần chưa đủ. Giữ start/finish/check đúng batch, không seal
  application dở của phiên khác. Commit/push đúng phạm vi, deploy chính commit
  và đối chiếu checksum; lỗi thì sửa hoặc rollback, báo trạng thái thật.

Cuối lượt trả lời: đã sửa gì, admin chính/delegate làm được gì, ngoại lệ nào
giữ, việc chưa kiểm, commitSHA/phiên bản/backup/URL đã áp và cách người dùng
mở thử bằng tài khoản đang có. Không nói hoàn thiện toàn bộ nếu còn action
quan trọng chưa có adapter hoặc chỉ hiện menu nhưng bấm vào bị lỗi.
