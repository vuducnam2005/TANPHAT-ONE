# HR-POSITION-003 — Đổi chức vụ, bổ nhiệm và hạ quyền dễ tìm

12/11/2026, CHG-20261112-006. Người dùng yêu cầu làm rõ nơi nâng/hạ chức vụ
trên danh sách HR. Tiếp tục phạm vi triển khai/test/áp main của task HR hiện tại;
không commit/push hoặc thử thay chức vụ/quyền người thật.

## Hành vi và phạm vi

- Admin có **Đổi chức vụ** ngay trên mỗi dòng danh sách và dưới tên trong hồ sơ.
- Cửa sổ hiển thị nhân viên, phòng ban, chức vụ và vai trò hiện tại. Chọn **Đổi
  chức vụ trong hồ sơ** hoặc **Bổ nhiệm / hạ quyền KH-KD**. Hai thao tác quyền
  ghi rõ **Bổ nhiệm Trưởng phòng / Trưởng ban KH-KD** và **Chuyển về Nhân viên
  KH-KD**; có lựa chọn đổi cả chức vụ HR cùng transaction.
- Nhánh chức vụ dùng được khi chưa có account, không tự đổi quyền hay tạo user.
  Chỉ chọn job active thuộc đúng công ty/phòng hoặc danh mục chung, có lý do,
  preview, digest/rowlocks/snapshot mới và audit nguyên tử. Hủy không ghi.
- Nhánh quyền vẫn dùng adapter staff↔HEAD, guard company/protected user/scope/
  nguồn quyền bổ sung/revocation hiện hành. Không triển khai quyền phòng khác.
  Giao diện giải thích rõ nếu thiếu tài khoản hoặc bộ quyền chưa triển khai.
- Native view/action/SCSS trong custom addon; không thêm model/ACL/role engine,
  không sửa core/React/API. `change_kind` mới thuộc transient wizard hiện có.

## Kiểm thử thực chạy

Evidence private `.local/hr-position003/`, không đưa dữ liệu cá nhân vào Git.

| Gate | Kết quả |
| --- | --- |
| Backend trước restore | `backend.log`: 24 ca HR, 0 failed/0 errors; role/identity/lock/stale/rollback hồi quy và nhánh job mới |
| Browser fixture | `browser-result.json`: 6 nhóm đạt,0console/pageerror; vào từ row, đổi job giữ quyền, bổ nhiệm cấp access đúng scope, hạ cả job/quyền thu hồi phiên cũ, mobile native job picker/noaccount không tạo user, hủy sau preview không ghi |
| HOOT trước restore | HR20tests/83assertions và Home29tests/166assertions đạt; không thêm unit test UI chỉ lặp view |
| Backend sau restore | `backend-restored.log`:24 ca HR,0failed/0errors; chỉ nâng cấp HR nên login backend không chạy lại |
| HOOT sau restore | HR20tests/83assertions và Home29tests/166assertions đạt; logs tại `.local/hr001/hoot-18079/` |
| Clean smoke hai cổng | `smoke-18079.json` và `smoke-18069.json`:4nhóm mỗi cổng,0errors; list/profile entry, desktop/mobile, lựa chọn rõ, focus/nooverflow, hủy giữ job/quyền người thật |
| Static | Ruff HR đạt;10XML HR/login parse đạt; `git diff --check` đạt |
| Source rollback | `rollback-source.zip/json`:53file gốc, không thêm file source; giữ dirty worktree |
| Thiết kế | [Wireframe](../ui/HR_POSITION_003_DESIGN.md), ảnh trước–sau1440×1100/390×1100 cùng route/role/dataset sạch cuối |

Browser harness đầu dùng role search_count trong scope chỉ thấy role của chính
actor nên báo0 dù target đã được cấp HEAD; đã chuyển sang đọc business role và
kiểm access dự án thực. Mobile picker native hiển thị danh sách lựa chọn riêng,
không fill input readonly; đã kiểm thao tác chọn thật và rerun đầy đủ đạt.
Không dùng lượt fail làm bằng chứng pass. Fixture chỉ ở test, đã loại bằng
restore trước áp main. GCassetsWinError5/markdown2warning Windows giữ giới hạn,
filestore phải kiểm riêng. Chưa điện thoại vật lý hoặc audit độc lập vì model
kế thừa của subagent không khả dụng. Visual/business/pilot do người dùng duyệt.

Hướng dẫn thao tác hiện hành: [guide](HR_ACCOUNT_ROLE_001_USER_GUIDE.md).

## Restore, áp main và bảo toàn

- Rehearsal backup `.local/hr001/backup-tp_tanphat_dev-20261112T045025670054Z`;
  restore canonical test596rowsets/643blobrefs/429sequences khớp rồi neutralize
  UUID/baseURL/cron/SMTP và chạy backend/HOOT/smoke trên source cuối. Không DBthứ3.
- Main dừng đúng PID/config, backup cuối
  `.local/hr001/backup-tp_tanphat_dev-20261112T050005254157Z`, upgrade chỉ
  `tp_hr_workspace`20.0.1.4.0 với `--no-http --stop-after-init`, start18069 và
  smoke đạt. Login giữ20.0.1.4.0; không seed/test ghi nghiệp vụ trên main.
- Source53file seal khớp;79bảng nghiệp vụ/quyền,617nonassetblob giữ nguyên.
  ACL không thêm/xóa/đổi policy, chỉ2write_date thay do upgrade; groups/implied/
  company giữ. Cả2cổng39employee/27user/8active/13phòng/9đơn vị có người/
  7mapping/1HEAD. Không sửa chức vụ/account/password/role/assignment/grant thật.
- Ảnh main trước–sau cùng route/role/dataset sạch và viewport1440×1100/390×1100:
  `before-list.png`, `before-profile.png`, `before-dialog-{desktop,mobile}.png`
  → `after-list-18069.png`, `after-profile-18069.png`,
  `after-dialog-{desktop,mobile}-18069.png`, `after-role-{desktop,mobile}-18069.png`.
  Đã mở ảnh thật để tự đánh giá; mobile là giả lập trình duyệt.
- Rollback riêng follow-up:53file gốc SHA256,0filemới. Dùng helper
  `.local/hr-position003/ops.py rollback` theo [runbook](../../ops/runbooks/HR_ACCOUNT_ROLE_001_DEPLOY_AND_ROLLBACK.md),
  rồi upgrade HR để trả views; không restore DB cũ khi đã có giao dịch mới.

Technical verification đạt; người dùng xem18069 để duyệt hình thức/nghiệp vụ.
Pilot authorization và audit độc lập vẫn riêng; không commit/push.
