# HR-EMPLOYEE-ORDER / AUTH-SESSION-001 — giao bản và khôi phục

Cập nhật 18/11/2026. Đây là hướng dẫn vận hành, không xác nhận đã chạy deploy hoặc nghiệm thu nghiệp vụ.

## Gói triển khai

Chỉ giao slice đã commit, theo danh sách file và checksum do phiên điều phối bàn giao:

| Addon | Phiên bản đích |
| --- | --- |
| `tp_hr_workspace` | `20.0.1.13.2` |
| `tp_admin_delegation` | `20.0.2.0.1` |
| `tp_web_login` | `20.0.2.0.1` |

Bản thả mượt `20.0.1.13.2` (CHG-20261118-031) chỉ nâng `tp_hr_workspace`. **Candidate phải dựng từ HEAD hiện hành:** `tp_hr_attendance` phụ thuộc `tp_hr_workspace`, nên `-u tp_hr_workspace` cũng nâng chấm công bằng code trong candidate; candidate cũ sẽ hạ cấp chấm công và xóa cột (sự cố local 18069 lúc 17:14 ngày 18/11/2026). Kiểm version mọi addon phụ thuộc trong candidate trước khi upgrade.

Bản sửa kéo cả dòng `20.0.1.13.1` chỉ nâng `tp_hr_workspace`; AUTH/admin giữ phiên bản đã giao, không chạy lại migration của chúng. Không đóng gói toàn bộ working tree đang có WIP của hạng mục khác; giữ nguyên những thay đổi đó. Ghi commit SHA, đường dẫn file, SHA256 của gói và phiên bản thực chạy vào biên bản giao bản. Không đưa credential, dump hoặc filestore vào Git.

Local hiện chạy nguồn cô lập tại `.local/hr-order-row/candidate-20261118T163523/custom_addons`, qua `runtime.conf`, cùng database của `18069`. Đây là staging source, không phải database test riêng: không chạy fixture hoặc thử ghi giả tại đây. Trước khi chuyển nguồn, đối chiếu gói đã commit và checksum; không trỏ runtime về toàn bộ source WIP. Không bắt buộc qua `18079`, không tạo/xóa database test.

PC server: checkout `C:/Projects/TANPHAT-ONE`, container `tp-odoo`, network `tanphat-one_default`. Dùng cấu hình, database và volume thực tế đã kiểm chứng trên môi trường đó; không tự suy đường dẫn host/container từ cấu hình local. Giữ tunnel đang chạy, không restart tunnel.

## Trình tự áp dụng

1. Kiểm nguồn/version đang chạy, health và snapshot chỉ đọc dữ liệu/quyền cần bảo toàn. Đối chiếu gói đúng scope; bảo toàn source WIP và cấu hình hiện có.
2. **Từng môi trường phải có backup riêng trước upgrade:** database, filestore cùng database, source/config đang chạy. Ghi thời gian, vị trí, SHA256, kiểm danh mục dump/archive đọc được và phương án phục hồi; giữ secret ngoài Git. Không dùng backup local thay backup server.
3. Triển khai chính các file đã commit, kiểm checksum sau chép. Dừng worker ứng dụng theo cách vận hành hiện có để không có hai runtime phục vụ cùng DB trong lúc upgrade. Giữ PostgreSQL và tunnel theo cấu hình đang dùng.
4. Chạy Odoo bằng executable/config/database của chính môi trường; bản sửa kéo cả dòng chỉ nâng `-u tp_hr_workspace --stop-after-init`. Gói AUTH/HR ban đầu từng nâng ba addon. Không `-u all`, không seed actor/password và không chạy suite sinh fixture trên DB đang dùng. Kiểm exit code và log; lỗi upgrade thì chưa mở phục vụ.
5. Khởi động đúng runtime đã giao, kiểm phiên bản ba addon và health. Đối chiếu snapshot: nhân sự/phòng/chức vụ/mã/tài khoản/nhóm quyền, dữ liệu thiết bị/chấm công và `web.base.url`. Migration thứ tự có thể đổi `sequence` theo thiết kế nhưng phải giữ thứ tự hiển thị hiện có và trường nghiệp vụ khác.
6. Kiểm assets/XML/OWL và URL public bằng đọc không phá dữ liệu. Với HR kéo cả hàng, chạy `python scripts/tests/test_hr_employee_order_served_assets.py --base-url <URL>` ở local và public; kiểm JS/CSS thực được `/web/bundle/web.assets_web` tham chiếu. Biên dịch source trong bộ nhớ, version addon và checksum source chưa chứng minh browser nhận đúng bundle. Dùng browser mock cho kéo thả/lỗi/RPC âm; không tự tạo fixture hoặc đổi thứ tự nhân viên thật để smoke. Với đăng nhập mới thay phiên cũ, không đăng nhập tài khoản thật chỉ để kiểm rồi đá phiên người dùng. Chỉ kiểm bằng actor/phương thức đã được người dùng cho phép rõ ràng.
7. Ghi commit, checksum, version runtime, backup, lệnh/kết quả thực chạy và phần `NOT_RUN` trong bàn giao; tách technical acceptance, business acceptance và pilot authorization. Lỗi thì sửa gói hoặc thực hiện rollback đã đánh giá bên dưới.

## Rollback

- Ghi lỗi, thời điểm và các ghi mới từ sau backup; tạm dừng phục vụ nếu cần tránh ghi tiếp. Giữ bản source/config và backup hiện tại trước khôi phục.
- Không coi checkout commit cũ rồi restart là rollback đầy đủ: HR thêm trường `sequence`, public employee SQL view và migration khởi tạo thứ tự; AUTH thay session policy/token. Phải kiểm tương thích source/schema/view và session của phiên bản đích trước khi hạ nguồn. Không tự xóa cột hoặc tái tạo view theo phỏng đoán; chuẩn bị migration sửa tiến hoặc kế hoạch hạ tương thích cụ thể.
- Ưu tiên sửa tiến hoặc khôi phục gói source đã biết tương thích với DB hiện tại. Chỉ upgrade lại đúng addon cần thiết theo kế hoạch đã kiểm chứng; không chạy migration khởi tạo thứ tự lặp để che lỗi.
- **Không restore DB cũ một cách máy móc.** Full restore chỉ sau khi đánh giá rõ dữ liệu phát sinh sau backup sẽ mất gì, cách bảo toàn/đối soát và quyết định khôi phục phù hợp quyền người dùng đã giao. DB và filestore phải cùng snapshot nhất quán; giữ bản hiện trạng trước restore. Không restore test đè main/server.
- Sau khôi phục, kiểm health, version/schema/view, dữ liệu/quyền và URL public; đánh giá phiên AUTH cũ có cần đăng nhập lại theo policy. Không nới DEC-054 hoặc tắt kiểm session để qua smoke. Ghi rõ trạng thái khôi phục và giới hạn còn lại.

## Tài liệu đối chiếu

- [HR acceptance](../../docs/demo/HR_EMPLOYEE_ORDER_ACCEPTANCE.md), [HR user guide](../../docs/demo/HR_EMPLOYEE_ORDER_USER_GUIDE.md).
- [AUTH policy](../../docs/security/AUTH_SESSION_001_POLICY.md), [AUTH acceptance](../../docs/demo/AUTH_SESSION_001_ACCEPTANCE.md), [AUTH user guide](../../docs/demo/AUTH_SESSION_001_USER_GUIDE.md).
- [Continuous delivery](../../docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md).

Kiểm ORM thực cho bản sửa được thực hiện trong giao dịch luôn rollback sau backup; đối chiếu bằng cursor mới để xác nhận không giữ thay đổi. Không commit thao tác thử hoặc đăng nhập tài khoản đang dùng chỉ để kiểm. Dùng scope addon và kết quả thực của gói bàn giao mới nhất; không suy PASS từ kế hoạch hoặc kết quả lịch sử.

## Giao bản sửa kéo cả hàng — CHG-20261118-027

- Application commit `b9c3040cee006af788c85b0059daf08f4c7661db` đã push `origin/main`; PC server nhận đúng15/15checksum. Runtime18069/PCserver: HR20.0.1.13.1, chỉ upgradeHR exit0/0ERROR. AUTH/admin không đổi.
- Backup local `.local/hr-order-row/backup-20261118T163542`: dump10.049.127B, filestore294.237.435B/1.027file, source-config321.909B, restore15.600mục; SHA256. PC `C:/TANPHAT-backups/hr-order-row/hr-row026-20261118T164222`: dump9.707.147B, filestore32.133.010B/614archiveentry, source-config2.158.233B, restore15.600mục; SHA256. Snapshot từng môi trường chỉ versionHR đổi; sequence, roster, user/group/ledger/equipment/days/baseURL giữ. Không so datasetlocal vớiserver.
- Native browser regression/VM/backend12/12 và realORM7checks trong rollback PASS. READONLY probe local/server6/6; candidate normalized7/7khớpcommit. Local assets561CSS/1786JS/75XML (6.443.819JSbyte); server561/1786/75 (6.443.990JSbyte), css_errors=[]; biên dịch trong bộ nhớ không lưu attachment. AnonymousHTTP/login local/public desktop1440/mobile390:11/11PASS,0JSerror. Public `https://hybrid-send-ready-ballot.trycloudflare.com`; không restarttunnel.
- Khởi động18069 bằng phiên tiến trình Odoo duy trì sau khi helper background kết thúc; listener và smoke cuối đạt. Runtimeconfig `.local/hr-order-row/candidate-20261118T163523/runtime.conf`; giữ cùng DB/filestore. Gói source cô lập không nạp WIP attendance/reporting/sidebar/branding; checkpoint gốc giữ, workflow026/027 kiểm trong snapshot sạch đúng scope.
- Full authenticated browser/HOOT/persist qua transaction commit/máy khác/race chưa chạy. Không fixture/login/đổi phòng hoặc lưu reorder thử trên DB đang dùng; realORM thử luôn rollback và freshcursor xác nhận nguyên trạng. Nghiệm thu người dùng riêng. Đây là tài liệu xác nhận giao bản, đồng bộ source không restart/upgrade tiếp.

## Cổng asset thực — từ CHG-20261118-028

Odoo version bundle theo URL+mtime. Gói tar static phải đặt `TarInfo.mtime` theo thời gian commit/file; không để mặc định0, không bảo toàn mtimecũ khi nội dung đổi. Với helperpack hiện tại dùng timestamp từ `git log -1 --format=%ct <target> -- <path>`. Không sửa core Odoo hoặc thêm cachebuster cho URLimmutablecũ.

Nếu checksum source đúng nhưng UI còncũ: lưu evidenceURL/bytes/hash nội dung thực, đối chiếu mtimefile và generatedattachment; backupsource+metadata, cập nhậtmtime đúngasset đãdeploy rồi restartworker để xóa cacheRAM. Không xóa hàng loạt ir.attachment/filestore. Tải lại `/web/bundle/web.assets_web`, JS/CSS ở URLmới và chạy checker trên cả local/public. HTTP200, versionaddon và in-memorycompile chưa đủ.

```powershell
.\.venv\Scripts\python.exe scripts/tests/test_hr_employee_order_served_assets.py --base-url http://127.0.0.1:18069 --output .local/hr-order-asset/local-served-check.json
.\.venv\Scripts\python.exe scripts/tests/test_hr_employee_order_served_assets.py --base-url https://hybrid-send-ready-ballot.trycloudflare.com --output .local/hr-order-asset/public-served-check.json
```

Kết quả xử lý028: public JSf3195e5→c7831b0, CSS41f50d0→e08d09c; thực tải8/8PASS khôngtaynắm/hit-testcũ. Backupmetadata/source3file tại `.local/hr-order-asset/source-before-20261118T095446Z` trênPC; sourcehashb9c3040c giữ nguyên. Người dùng tải lại trang để nhận URLmới; nghiệm thu visual/persist qua session thật riêng.
