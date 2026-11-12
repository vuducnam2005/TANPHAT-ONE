# KD-ACCESS-001 — Tài khoản dev và kiểm quyền

Lịch sử batch này được giữ nguyên. Quyền CRM mới theo yêu cầu09/11 nằm ở
[KD-ACCESS-002](KD_ACCESS_002_ACCEPTANCE.md); không dùng kỳ vọng “CRM denied”
của batch001 làm ma trận cho batch002. Tool audit001 có mode crm_scope riêng.

Ngày 08/11/2026, Asia/Saigon. Phạm vi: năm tài khoản dev theo yêu cầu trực tiếp;
không xác nhận bổ nhiệm người thật, Q2, business acceptance hoặc pilot.

## Acceptance trước khi triển khai

| Ca | Actor, thao tác | Kết quả bắt buộc |
| --- | --- | --- |
| A01 | Năm alias đăng nhập riêng | Internal user, vi_VN, Asia/Ho_Chi_Minh; đúng company; Home native; không email/HR employee |
| A02 | head/deputy/project_lead/planning/support đọc dự án | Chính xác 8/4/4/4/2 dự án trong registry; ngoài scope/company không read/search/export/relation |
| A03 | Kiểm từng project/KD grant | Capability đúng scope, thiếu/revoked/expired/assignment mất đều bị chặn |
| A04 | deputy/project_lead tạo nháp; head trả; owner sửa/gửi lại | Owner/reviewer/version/state/reason được backend kiểm; không self-review hoặc đổi hồ sơ cũ |
| A05 | planning | Prepare/submit allocation/production/plan/credential; không payment/acceptance/contract-submit/review |
| A06 | support | Chỉ prepare credential của mình; không submit/review/tiền; snapshot/file/export/download kiểm backend |
| A07 | Mọi role | Không Settings/grant admin/HR nhạy cảm/kế toán; không group manager hoặc all-leads; không CRM ngoài scope |
| A08 | Provision lặp và rollback clone | Không nhân user/assignment/grant hoặc reset password; archive/revoke đúng delta, giữ user/dữ liệu cũ |
| A09 | Dev sau backup | Chỉ provision delta đã thử; browser/RPC chỉ đọc; dữ liệu nghiệp vụ và account/password/group cũ giữ |

## Giới hạn source đã biết

Không cấp CRM group hoặc opportunity grant: prepare hiện gồm cả khai báo nộp,
chưa bảo vệ chỉ sửa owner và các trường tiền CRM. Phần này được giữ chưa mở theo
nguyên tắc fail closed của prompt. Không mở tạo project/ghi WBS vì cơ chế hiện tại
đòi manager; dùng assignment reader. Department được ghi trên assignment/grant,
không tạo employee thật hoặc thêm trường user mới chỉ để mô phỏng HR.

## Kết quả tự kiểm kỹ thuật

`IMPLEMENTED_VERIFIED_DEV_WITH_DOCUMENTED_GAPS`, CHG-20261108-003.
Dev `tp_tanphat_dev`/18069/PG55432; clone owned
`tp_tanphat_kdaccess001_20261108`/18989, source/filestore/data-dir riêng.

| Kiểm thực chạy | Kết quả |
| --- | --- |
| Snapshot/restore clone | 576 table rowsets, 269 attachment references khớp trước neutralize; dev giữ PID |
| Odoo hồi quy | 118/118 (45 workspace, 73 contract), 0 failure/error; log cuối `20261108T130009486818Z.log` |
| Exact-role ORM/call_kw audit | 1.426 kiểm clone và 1.426 dev: scope/company/group/capability/read/search/read_group/relation/export/tiền/document/dashboard; giữ password/group/grant cũ |
| Mutation rehearsal clone | 276 kiểm: mọi typed domain được cấp có prepare/submit/return/rework/resubmit; hợp đồng deputy/lead→head; sai owner/reviewer/self/state/version/reason, expiry/revoke/assignment, rerun và rollback; hồ sơ thử rollback toàn bộ |
| HTTP/RPC financial file clone | 60 kiểm: binary document URL, attachment ID URL và direct file RPC cho năm role ở normal/revoked/expired/unassigned. Head/deputy/planning đúng scope tải checksum khớp; support/lead ngoài scope bị403/404; sau revoke/expiry/mất assignment head bị chặn. Rights restore về normal trong finally |
| Chromium native browser | 98 clone và 98 dev; 5 session riêng cùng lúc, Home/Tổng quan/project/list/form/credential/permission/RPC/known-ID; 25 ảnh mỗi môi trường; 0 page/console error ở lượt cuối |
| Backup trước apply | `backup-pre-apply-20261108T130448Z`, 112 file checksum, 576 table, 269 reference, dump `pg_restore --list` đạt |
| Apply | Chỉ `tp_kd_workspace` 20.0.1.5.1; rc0/0error/changed_tables {}; restart riêng Odoo dev, PG và clone khác giữ |
| Provision dev | 5 user, 22 reader assignment, 64 project grant, 258 typed grant; ORM/transaction; mật khẩu riêng từng user, khác clone; lặp không tạo/reset |
| Preservation | 93 table, 4.165→4.574 row; 0 dòng cũ mất/đổi (ngoài write metadata loại theo helper); chỉ delta account/grant và onboarding. 106 blob unique/269 reference giữ; source áp bằng clone; module registry clone/dev bằng; password/account/group cũ giữ bằng so sánh nội bộ |
| Tooling/source | Ruff, node syntax, XML parse, diff-check và workflow checker; không React/core change hoặc commit/push |

Evidence private `.local/kd-access001/`: `clone-audit.json`, `clone-rehearsal.json`,
`clone-browser.json`, `dev-audit.json`, `dev-browser.json`, `dev-apply-result.json`,
`preservation-after-verify-diff.json`, `final-preservation.json`, `shots/clone/`,
`shots/dev/`; credential tách `clone-credentials.json` và `dev-credentials.json`.
File probe riêng `clone-files-{normal,revoked,expired,unassigned}.json`,
`file-fixture.json`; một document+attachment tổng hợp chỉ trên clone, được giữ
đúng journal, không copy lên dev và không đổi registry/hồ sơ dev.
Không đưa tên người/login thật, file private hoặc mật khẩu vào fixture tracked.

## Security và phát sinh native

Nhóm `tp_kd_workspace.group_scoped_staff` chỉ implies `tp_core.group_user`.
Hai restriction đọc global có điều kiện theo nhóm mới: Project phải managed,
đúng company và active assignment; Task phải thuộc project có quyền. Nhóm nhân
viên Odoo vốn đọc được project chung dù không có assignment; rule mới đóng đường
này cho năm user, giữ hành vi reader/admin cũ. Test mới cấp export riêng cho fixture
để kiểm rule backend, không cấp export cho năm user dev.

Source áp: manifest, `security/staff_scope.xml`, hai dòng `security/ir.access.csv`,
test scope và import; không đổi schema/action/capability/API hoặc UI assets.
Department đúng registry và nằm trên grant scope, không tạo HR employee.

Odoo tự sinh 5 welcome task không có project và 35 personal stage cùng 5 task-user
relation khi tạo user (project/project_todo hooks). Đã xác nhận giống clone,
journal ID dưới từng user trong delta; giữ nguyên, không cleanup/xóa trên dev,
không tính vào hồ sơ KH-KD. Rule mới khiến staff không đọc projectless task.

Login đầu tiên Odoo nhận timezone browser `Asia/Saigon`, tương đương múi giờ yêu
cầu; đã kiểm trên clone rồi chuẩn hóa riêng năm account về `Asia/Ho_Chi_Minh`.
Không đổi password. Một lượt browser dev timeout điều hướng list; chạy lại đầy
đủ98kiểm đạt. Lượt Odoo đầu có lỗi exception export trong test mới, đã sửa test để
thực sự kiểm rule và chạy lại118/118; không dùng lượt lỗi để apply.

## Giới hạn

- Cơ hội/CRM chưa cấp cho cả năm alias: prepare hiện gộp khai báo nộp và thiếu
  owner/financial guard theo ma trận. Không cấp salesman/all-leads. Tạo project/
  ghi WBS vẫn cần manager hiện hành, chưa cấp.
- Structured amount/snapshot/document dùng policy hiện có; metadata còn coarse
  theo project. Không có phân loại/redaction tùy ý cho free text/file general;
  không coi đây là cam kết lọc mọi số tiền người dùng gõ vào ghi chú.
- Chromium desktop; chưa Safari/điện thoại thật. Tự kiểm, subagent lỗi model nên
  chưa audit độc lập. Business/Q2/pilot và audit UI cũ riêng; BASE/ký/hiệu lực/
  posting/paid/quản trị grant không mở.

Runbook đăng nhập/đổi vai và rollback exact delta:
[KD_ACCESS_001_USER_GUIDE.md](KD_ACCESS_001_USER_GUIDE.md).
Rerun dev cuối có `dev-idempotency.json`: account/password/rights không đổi;
backup freshness vẫn bắt buộc cho provision mới, rerun chỉ kiểm provenance và
không sửa. Clone18989 đã dừng sau kiểm, giữ DB/source/evidence để review.
Private `LOGIN_HANDOFF.md` liệt kê người–login–role cho chủ dự án, không có mật khẩu.

Next: chủ dự án kiểm năm vai trò theo guide; mở batch CRM riêng nếu cần gỡ gap
owner/prepare-submit/financial. Không tạo giao dịch thử trên dev.
