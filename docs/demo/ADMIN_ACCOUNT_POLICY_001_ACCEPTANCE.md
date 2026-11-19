# ADMIN-ACCOUNT-POLICY-001 — Quản lý tài khoản admin

Ngày 19/11/2026. Yêu cầu trực tiếp trong tệp người dùng đính kèm; DEC-062 thay quy tắc thu hồi admin trước khi khóa. Phiên chính được giao triển khai hạng mục này.

## Hành vi

- Admin gốc khóa/mở và quản lý tài khoản admin ủy quyền theo chức năng hiện có, giữ bảo vệ tài khoản hệ thống/chính mình và admin gốc cuối cùng.
- Admin ủy quyền A chỉ đọc tài khoản/hồ sơ của admin ủy quyền B, kể cả khi B đã khóa. Chỉ admin gốc cấp/thu hồi admin. A tiếp tục quản trị nghiệp vụ và nhân viên thường theo quyền hiện hành.
- Backend kiểm người thực hiện thực tế, không lấy quyền từ `sudo` hoặc context client. Cùng helper phân loại admin gốc, admin ủy quyền và nhân viên cho capability và guard.
- Guard kiểm cả user, employee, partner, resource, phiên bản HR, liên kết trực tiếp/default/commands, unlink/archive và batch. Hồ sơ tương ứng được bảo vệ; tham chiếu trong dự án/thiết bị/báo cáo không làm nghiệp vụ bị khóa theo.
- UI có loại tài khoản rõ ràng; peer profile chỉ đọc và giải thích: “Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.” Đổi tên đăng nhập, khóa/mở/reset/sửa hồ sơ không hiện cho peer.
- Khóa dùng `active`, `tp_hr_locked`, `tp_lock_revision` hiện có. Session cũ không được khôi phục sau mở khóa. Không sửa sổ cấp quyền; mở lại giữ grant còn hiệu lực, không tạo grant mới.
- Nhật ký append-only có actor, target, thời gian, lý do và trước/sau phù hợp. Chỉ metadata cho credential/avatar, không lưu mật khẩu hoặc token.

## Phạm vi và nghiệm thu

Phiên bản đã kiểm: `tp_admin_delegation` **20.0.2.1.0**, `tp_hr_workspace` **20.0.1.16.0**. Không đổi API/React/core Odoo. Không tạo bảng nghiệp vụ mới; bộ lọc không đổi, form/popup là N/A, audit dùng model và search hiện có.

Test thực hiện trên `tp_tanphat_test` hiện có sau backup tại `.local/admin-account-policy001/test-backup-20261119T143137`. Backup gồm dump custom đã đọc bằng pg_restore-list, filestore được DB tham chiếu + manifest SHA256, source/config; không sao tệp GC dư không được DB tham chiếu. Tài khoản thử có tiền tố Synthetic, rollback sau test; không khóa/reset/cấp quyền người thật.

Kết quả kiểm thực, commit và receipt triển khai được bổ sung sau khi chạy. Technical verification, nghiệm thu hình thức/nghiệp vụ và pilot authorization là các kết luận riêng. Không tuyên bố authenticated public E2E bằng người thật hoặc iOS/Safari thật nếu chưa chạy.

## Kết quả kiểm thực

Odoo 40/40 PASS, 0 failed / 0 errors (tests-5.log): toàn addon admin delegation, login rename backend/HTTP/browser và account-role regression. Tag mới gồm 7 TransactionCase + 2 HttpCase; kiểm lock/unlock ledger/groups không đổi, audit reason/actor/target/revision, phiên cũ bị từ chối, login mới khóa có thông báo và mở lại đăng nhập được; peer writes mọi trường/sudo/context/inactive/bulk/profile/contact/resource/hr.version/link/unlink bị chặn; ordinary management/self service và original-only grant/revoke giữ.

Race 2/2 PASS (race.log), PostgreSQL hai giao dịch độc lập: rename+rename và create+rename cùng login có đúng một winner; fixture đã cleanup. Lệnh python -m scripts.tests.test_hr_login_rename_race --config .local/admin-account-policy001/runtime-test.conf; không chạy trên main/server.

Playwright 1440x900 và 390x844 PASS: original khóa/mở qua lý do + xác nhận, trạng thái DB/reload đúng và 3 nhãn loại tài khoản; peer employee profile và native res.users chỉ đọc, không rename/reset/lock/edit/menu thao tác, 0 pageerror. Hồi quy rename dialog/unique/inline/cancel/save/reload/mobile PASS. Screenshot/result ignored .local/admin-account-policy/browser và .local/hr-login-rename-impl001/browser.

Ruff, AST Python, XML parse, Node syntax và scoped git diff --check PASS. Review chéo phát hiện/sửa self-rule áp rộng nhầm ordinary HR và menu mobile native vẫn hiện; khóa target dùng exclusive advisory theo namespace grant, không đổi scope revision. Các lần đầu lỗi fixture cookie/HR role/sequence/config API và selector icon đã sửa, không giảm guard để làm test xanh. Chưa authenticated public E2E bằng người thật/iOS/Safari thật; không khóa/reset/cấp quyền người thật. Kiểm kỹ thuật không thay nghiệm thu nghiệp vụ.

## Đã áp local và PC server — CHG-20261119-019

App **3442143c** đã push; **HR20.0.1.16.0/admin20.0.2.1.0** đang chạy trên local18069 và PCserver. Hai upgrade exit0/0ERROR. Nguồn server28/28SHA256 đúng release; giữ nguyên addon ngoài scope. PC backup `C:\TANPHAT-backups\admin-account-policy001\admin-account018-20261119T150313` gồm dump10.191.206B, restore-list15.790mục, filestore628mục/32.038.793B, source/config và SHA256. Local backup `.local/admin-account-policy001/main-backup-20261119T150023`: dump/restore-list, filestore DB-referenced150.508.243B, source/config/SHA256.

Fingerprint trước/sau giữ39nhân viên/32tài khoản, groups/implied, login/password/active/lock revision/admin scope revision, liên kết company/partner/resource/roster, ledger đầy đủ (không chỉ state) và số liệu nghiệp vụ. Không khóa/reset/cấp/thu tài khoản người thật. Local0grant; PC5grant live, original có manage=true trên cả5, nhãn Admin ủy quyền; peer readonly/manage=false/rename=false đúng giữa từng cặp. Probe READ ONLY **13/13 local, 68/68 PC server**.

Public [https://eight-championships-launches-plaintiff.trycloudflare.com](https://eight-championships-launches-plaintiff.trycloudflare.com) health/login200; bundle JS/CSS phục vụ thực có readonly/controller/rename và khớp SHA256 server. JS `/web/assets/a7d4b26/web.assets_web.min.js`, CSS `/web/assets/73d8d48/web.assets_web.min.css`. Không đăng nhập mới để đá phiên người dùng; authenticated public E2E bằng người thật và iOS/Safari thật NOT_RUN. Browser synthetic1440/390px và Odoo40/40/race2/2 đã kiểm riêng trước deploy.

Cách dùng: Ctrl+F5, mở **TP HR → Danh sách nhân viên → hồ sơ → Tài khoản và phân quyền → Khóa / mở tài khoản**. Admin gốc thấy “Khóa tài khoản” khi Mở, “Mở tài khoản” khi Khóa, nhập lý do và xác nhận như cũ. Admin ngang hàng chỉ đọc và thấy giải thích; nút Đổi tên đăng nhập/reset/sửa không hiện. Khóa không thu admin; mở không cấp lại quyền đã thu. Nghiệm thu nghiệp vụ/hình thức chờ người dùng, không tự thao tác tài khoản thật để minh họa.

Bằng chứng ignored `.local/admin-account-policy001/`: tests-5.log, race.log, local-result.json, local-readonly.json, local-assets.json, server-receipt.json, server-readonly.json, server-assets.json, public-assets.json, manifest và deploy-output.txt; ảnh `.local/admin-account-policy/browser/`. Snapshot/checksum và kiểm này không chứng minh toàn bộ hệ thống không còn lỗi.
