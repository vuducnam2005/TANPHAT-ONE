# HR-LOGIN-RENAME-001 — Đổi tên đăng nhập nhân viên

Ngày 19/11/2026; CHG-20261119-013. Người dùng giao trực tiếp triển khai. Trạng thái: **TECHNICAL_VERIFIED, RELEASE_READY**; kết quả môi trường áp ghi trong receipt cuối tài liệu.

## Vị trí thao tác

1. Đăng nhập bằng tài khoản có quyền quản lý tài khoản theo phân quyền hiện hành.
2. **TP HR → Danh sách nhân viên → chọn nhân viên → Tài khoản và phân quyền → Đổi tên đăng nhập**. Trong hộp **Quản lý tài khoản** cũng có cùng thao tác.
3. Kiểm tra đúng nhân viên/tên hiện tại, nhập tên mới, chọn **Lưu thay đổi**. Lỗi hiện ngay dưới ô; Hủy không ghi dữ liệu.
4. Nhân viên đăng nhập lại bằng tên mới với mật khẩu đang dùng. Nhập đúng hoa/thường; tên cũ không còn đăng nhập được.

Nhân viên chưa có tài khoản tiếp tục dùng **Tạo tài khoản riêng**, không có nút đổi tên. Người không đủ quyền không thấy nút và gọi RPC/import trực tiếp cũng bị từ chối. Tài khoản hệ thống và chính mình được bảo vệ theo chính sách quản lý tài khoản hiện hành. Admin gốc được đổi login admin được cấp; admin được cấp không đổi login admin gốc hoặc admin khác.

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

## PC server và public đã áp — CHG-20261119-014

App commit `0ba04faf88f03f34400e628968ff6624e9a5f82c` đã push origin/main. PC áp16/16tệp đúngSHA256 vàmtimeGit; nâng riêng HR/admin exit0/0ERROR, đang chạy **20.0.1.15.0 / 20.0.2.0.2**. Backup `C:\TANPHAT-backups\hr-login-rename-impl001\hr-login013-20261119T133244`: dump10.191.650B/restore-list15.789mục, filestore636entry/34.322.377B, source/config2.234.534B vàSHA256. Không restart tp-tunnel.

Snapshot trước/sau:39nhân viên/32tài khoản không đổi; credentials digest (login/password/active/partner), company membership/resource links/roster/sequence/department/job/groups/implied/equipment/grants/days/baseURL giữ nguyên; chỉ2moduleversion đổi. Không đổi login/mật khẩu người thật để thử. Probe ORM read-only17/17PASS trên local và17/17PASS trênPC: related/source/unique/native token/action/audit/quyền thường+sudo/export đọc đúng tên hiện tại.

Public [https://eight-championships-launches-plaintiff.trycloudflare.com](https://eight-championships-launches-plaintiff.trycloudflare.com) trả health/login200. JS `/web/assets/993d7c1/web.assets_web.min.js`8.484.470B SHA256`efbc0887c4d0b8008f810d6a6fd63445c172f5895c00f5320e2827e2e7d7b819`; CSS `/web/assets/73d8d48/web.assets_web.min.css`1.632.606B SHA256`3dda3b6e09d97c753d55c896cb0592cc2cdb8ff1430fc6f2a50136eb6c98cff2`. Cảhai khớpbytes/SHA256server; JS có action/dialog/input/check tên/re-login mới. Local health/login200, JS6a2b665/CSS34096a9 có code mới; compile bundle đầu tiên chậm gây timeout, request sau vàbundle thực đã đạt, không sửa source để né.

Bằng chứng ignored: local-result.json, local-readonly.log, local-assets.json, deploy-output.txt, server-receipt-raw.json, server-readonly-result.json, server-assets.json, public-assets.json tại `.local/hr-login-rename-impl001/`. Tiếp tục không dùng tài khoản thật để rename/login thử; authenticated public E2E vàiOS/Safari thật NOT_RUN. Technical acceptance đạt cho scope đã nêu; business/visual acceptance chờ người dùng. Tải lạiCtrl+F5 rồi mở đúng vị trí đầu tài liệu.

## Sửa visibility admin được ủy quyền — CHG-20261119-016

Ảnh sau giao bản014 cho thấy thiếu nút trên hồ sơ Trần Phương Đông. PC probe read-only xác nhận admin gốc đang xem admin được cấp; bản trước dùng guard khóa/reset vốn chặn mọi admin nên tp_can_change_login=false. Bản sửa **HR20.0.1.15.1/admin20.0.2.0.3** thêm ngoại lệ chỉ cho đổi login: admin gốc đổi admin được cấp; delegate không sửa original/adminpeer/self, tài khoản hệ thống và khóa/reset giữ bảo vệ. Cả form chính, form delegated, wizard và mọi đường res.users.write dùng cùng kiểm backend; wizard không ẩn nút do capability lock/reset=false.

Kiểm thực testDB có backup riêng: **8/8PASS**, gồm5backend rename, 2HttpCase và1reset regression. Browser synthetic originaladmin → target có grant active kiểm nút hiện nhưng reset vẫn ẩn, rename/duplicate/Cancel/reload/390px/Escape0error. Snapshot ảnh so bytes (Odoo BinaryValueAttachment cần so nội dung), grant active/ID/hash/password/nhóm/link giữ. Fixture class reset sequence vềfloor và restore sauclass để không phụ thuộc dải mã đã tiêu thụ bởi nextval ngoài transaction; không sửa sequence người thật. Race/nativeunique không thay, bằng chứng013 vẫn áp dụng.

Backup test `.local/hr-login-rename-fix016/test-backup-20261119T135937`: dump/restore-list/source/config/SHA256; filestore restore theo filestore-restore.json gồm baseZIP013 +delta và currentmanifest (blob có địa chỉ nội dung bất biến). Không clone/restoreDB. Browser evidence mới tại `.local/hr-login-rename-impl001/browser/`, logs tests-verified.log tại thư mụcfix016. Không đổi login người thật. CUA thử chọn cửa sổ Cốc Cốc bị công cụ dừng do chưa hỗ trợ URLpolicy; không tiếp tục điều khiển/bypass, không coi là kiểm UI trực tiếp người dùng. Runtime receipt sau deploy nằm cuối mục này.

## Bản sửa đã áp local/PC server — CHG-20261119-017

App `cf4cf11411cd0d89b2e76c5d7be4723ef9817c37` đã push origin/main và áp **HR 20.0.1.15.1 / admin 20.0.2.0.3**. Local18069 và PC đều upgrade exit 0, 0 ERROR. PC backup `C:\TANPHAT-backups\hr-login-rename-fix016\hr-login016-20261119T140905`: dump 10.182.487 B, restore-list 15.790 mục, filestore 630 mục / 33.846.814 B, source/config 2.254.942 B và SHA256. Local backup `.local/hr-login-rename-fix016/main-backup-20261119T140631`: dump 10.480.205 B, filestore 1.700.605.234 B, source/config/restore-list/SHA256.

Probe read-only **21/21 PASS trên từng môi trường**, nguồn server **10/10 SHA256**. Đúng hồ sơ Trần Phương Đông, employee 63 trên PC, admin gốc có `tp_can_change_login=true`; target là admin được cấp và `tp_can_manage_account=false`, nên chỉ rename được mở, khóa/reset không đổi. Native view có nút và biểu thức hiển thị đúng. Local cùng employee là nhân viên thường, được quản lý tài khoản theo quyền sẵn có; không sửa grant/role người thật để làm giống server. Snapshot trước/sau giữ 39 nhân viên, 32 tài khoản và digest login/password/active/partner/company/resource/roster/groups/implied/sequence/equipment/ledger/days/baseURL; chỉ version HR/admin thay đổi. Chấm công PC 20.0.3.3.0 và local 20.0.3.1.0 giữ nguyên.

Vị trí ngay trên ảnh người dùng: **Tài khoản và phân quyền → cột Tài khoản cá nhân → dưới Chức vụ nhân sự, trên Quyền bổ sung đang giữ → Đổi tên đăng nhập**. Tải lại Ctrl+F5 và mở lại hồ sơ để native view/capability nạp lại. Nút trong hộp Quản lý tài khoản cũng dùng capability rename riêng.

Public [https://eight-championships-launches-plaintiff.trycloudflare.com](https://eight-championships-launches-plaintiff.trycloudflare.com) health/login 200; JS `/web/assets/ae4c8b5/web.assets_web.min.js` 8.484.498 B SHA256 `d4432e9aa8711f44279e8428a7ebdac45961a3445b32069690bc7bd80150f22e`, CSS `/web/assets/73d8d48/web.assets_web.min.css` 1.632.606 B SHA256 `3dda3b6e09d97c753d55c896cb0592cc2cdb8ff1430fc6f2a50136eb6c98cff2`, khớp server. Actual bundle có dialog/inline validation/re-login. Bản sửa không thay static JS; bundle giữ nguyên URL của release attendance gần nhất là phù hợp.

Bằng chứng ignored tại `.local/hr-login-rename-fix016/`: tests-verified.log, local-result.json, local-readonly-result.json, local-assets.json, deploy-output.txt, server-receipt.json, server-readonly-result.json, server-assets.json, public-assets.json. Không đổi tên hoặc mật khẩu tài khoản người thật. CUA Cốc Cốc bị công cụ dừng URL policy; không bypass và không tuyên bố kiểm UI trực tiếp cửa sổ người dùng. Authenticated public E2E bằng người thật, iOS/Safari thật NOT_RUN; browser fixture độc lập và Odoo 8/8 đã đạt. Technical acceptance đạt phạm vi này; người dùng nghiệm thu hình thức/nghiệp vụ sau tải lại.
