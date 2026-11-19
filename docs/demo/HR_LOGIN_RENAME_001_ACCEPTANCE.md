# HR-LOGIN-RENAME-001 — Đổi tên đăng nhập nhân viên

Ngày 19/11/2026; CHG-20261119-013. Người dùng giao trực tiếp triển khai. Trạng thái: **TECHNICAL_VERIFIED, RELEASE_READY**; kết quả môi trường áp ghi trong receipt cuối tài liệu.

## Vị trí thao tác

1. Đăng nhập bằng tài khoản có quyền quản lý tài khoản theo phân quyền hiện hành.
2. **TP HR → Danh sách nhân viên → chọn nhân viên → Tài khoản và phân quyền → Đổi tên đăng nhập**. Trong hộp **Quản lý tài khoản** cũng có cùng thao tác.
3. Kiểm tra đúng nhân viên/tên hiện tại, nhập tên mới, chọn **Lưu thay đổi**. Lỗi hiện ngay dưới ô; Hủy không ghi dữ liệu.
4. Nhân viên đăng nhập lại bằng tên mới với mật khẩu đang dùng. Nhập đúng hoa/thường; tên cũ không còn đăng nhập được.

Nhân viên chưa có tài khoản tiếp tục dùng **Tạo tài khoản riêng**, không có nút đổi tên. Người không đủ quyền không thấy nút và gọi RPC/import trực tiếp cũng bị từ chối. Tài khoản hệ thống, chính mình và admin được bảo vệ theo chính sách quản lý tài khoản hiện hành; admin được cấp không đổi login admin gốc.

## Thiết kế và bảo toàn dữ liệu

- Cập nhật res.users.login của cùng tài khoản; tp_user_login tiếp tục related user_id.login lưu sẵn, không tạo nguồn tên riêng. Không tạo user/employee, bí danh, hậu tố hoặc sửa tài khoản khác.
- Loại bỏ khoảng trắng ở hai đầu; từ chối rỗng/khoảng trắng bên trong/ký tự ẩn hoặc điều khiển/quá254ký tự/tên hiện tại. Giữ chữ hoa/thường đúng native login; không LOWER(login). Trùng kiểm toàn DB không lọc active/company, cuối cùng native UNIQUE(login) bảo vệ hai transaction đồng thời.
- Khóa employee/resource/user và kiểm lại liên kết/quyền/tên cũ khi lưu. res.users.write dùng cùng guard cho RPC/API/import; sudo không thay quyền actor. UID1 CLI giữ quy ước framework; không phải quyền nhân viên thường.
- Audit tp.hr.employee.audit + chatter: actor, UTC timestamp, userID, tên cũ/mới. Audit append-only, cùng savepoint với rename; lỗi audit rollback login. Không log password/token.
- Không sửa password, group/company, partner/avatar, department/job, user/employee/resource ID hoặc lịch sử cũ. Login nằm trong native session token nên phiên cũ cần đăng nhập lại; không tạo session/alias policy khác. Thông báo rõ trong dialog và sau lưu.
- Danh sách/chi tiết/tài khoản/DTO/export đọc nguồn res.users hoặc related. Sau lưu native soft_reload tải lại. Các màn khác đang mở cần tải lại để lấy dữ liệu mới; không tuyên bố realtime cho tab cache chưa reload.

## Kiểm tra thực chạy

| Kiểm | Kết quả/bằng chứng |
| --- | --- |
| Odoo TestEmployeeLoginRename | 4/4 PASS: rename bảo toàn, blank/invalid/duplicate inactive/company/locked, direct write/import/sudo/self/ordinary từ chối, stale link/login, original admin/delegate, audit rollback và bất biến |
| Hồi quy account | 5/5 PASS: tạo, duplicate/retry, rollback tạo, password validation/reauth/reset rollback, bảo vệ binding |
| HttpCase | 2/2 PASS: real HTTP auth cũ trước đổi/mới sau đổi với cùng password; cũ và sai case sau đổi thất bại; native token trước/sau khác; browser dialog thật |
| Playwright Chromium | desktop1440×900 và viewport390×844: mở từ native form, blank/space/duplicate inline giữ cũ, Hủy, Lưu/reload, mở lại tên mới, Escape, 0 pageerror |
| Excel | Exporter XLSX thật + openpyxl: có login mới, không có login cũ; userID/permission/employee link giữ |
| Race PostgreSQL | đổi–đổi và tạo–đổi bằng 2 transaction độc lập: mỗi cặp đúng1thành công/1duplicate, còn đúng1user cùng tên; cleanup synthetic |
| Tĩnh | AST Python/XML, Ruff, Node syntax, JS validator8case, git diff --check PASS |

Test chỉ dùng DB tp_tanphat_test hiện có; backup `.local/hr-login-rename-impl001/test-backup-20261119T125912` gồm dump9.092.771B/restore-list, filestore6.328.825.687B/source/config/SHA256. Không tạo DB mới, không restore lên main/server. Race fixture cleanup; HttpCase/backend rollback. Logs và ảnh ở `.local/hr-login-rename-impl001/`: backend-regression.log, http-final-live.log, race.log, browser/result.json và account-before.png/duplicate-inline.png/account-after.png/dialog-mobile.png. Không đưa cookie/fixture riêng vào Git.

Probe expired-session JSON-RPC trên Windows bị socket reset, nên không coi response đó là PASS. Kiểm token native thật trước/sau rename và HTTP authentication cũ/mới bằng cookie độc lập đã đạt. GC test có WinError5 từ filestore lịch sử; không sửa/xóa blob. Không chạy toàn bộ HOOT, full suite dự án, trình duyệt iOS/Safari thật hoặc đăng nhập mới bằng tài khoản thật để tránh thay phiên người đang dùng. Technical verification không thay cho nghiệm thu nghiệp vụ/hình thức của người dùng.

## Local18069 đã áp — CHG-20261119-013

Nâng riêng HR/admin thành công exit0/0ERROR, đang chạy20.0.1.15.0/20.0.2.0.2 tại `.local/hr-login-rename-impl001/main-candidate/runtime.conf`. Backup `.local/hr-login-rename-impl001/main-backup-20261119T132213`: dump10.477.809B/restore-list, filestore1.692.120.615B, source/config vàSHA256. Snapshot trước/sau chỉ2moduleversion đổi; digest login/password/active/partner, company memberships, resource links/roster/groups/department/job/sequence và dữ liệu nghiệp vụ không đổi. Probe ORM read-only17/17PASS, gồm related login/export hiện tại, quyền/capability, views, audit action và unique constraint. Giữ runtime chấm công local20.0.3.1.0 hiện có, không áp WIP phiên khác. PCserver chờ receipt thực sau commit/push.
