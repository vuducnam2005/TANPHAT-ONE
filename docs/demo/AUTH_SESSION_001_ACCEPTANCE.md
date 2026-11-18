# AUTH-SESSION-001 — Nghiệm thu Một phiên đăng nhập hoạt động cho mỗi tài khoản

Ngày lập tiêu chí trước code: 18/11/2026 (Asia/Saigon). Cập nhật bản hiệu chỉnh `tp_web_login` **20.0.2.0.1** ngày 18/11/2026; `tp_api` giữ **20.0.1.2.0**.

Nguồn: [prompt triển khai](../prompts/CLAUDE_AUTH_SESSION_001_SINGLE_ACTIVE_LOGIN.md), [DEC-057](../DECISIONS.md), [chính sách phiên](../security/AUTH_SESSION_001_POLICY.md), [hướng dẫn](AUTH_SESSION_001_USER_GUIDE.md), [ADMIN-FULL-001 / DEC-053/054](ADMIN_FULL_001_ACCEPTANCE.md), [quy trình giao bản liên tục](../operations/TP_CONTINUOUS_DELIVERY_POLICY.md).

## 1. Trạng thái bản hiện tại và giới hạn kiểm chứng

- **Kỹ thuật thuần/mock:** `scripts/tests/test_auth_session_001.py` **8/8 PASS**; `node scripts/tests/test_auth_session_frontend.cjs` **PASS**; Ruff, cú pháp JS, XML và kiểm diff đúng phạm vi **PASS**. Đây không phải bằng chứng race thực hoặc nghiệm thu nghiệp vụ.
- **18069:** upgrade bản `20.0.2.0.1` exit **0**, **0 ERROR**; snapshot trước/sau chỉ thay `modules`, dữ liệu nghiệp vụ/quyền giữ nguyên. Probe chỉ đọc **16/16 PASS**, gồm render QWeb trang hết phiên và guard người chỉ xem. Backup `C:/TANPHAT ONE/.local/auth-hr-finish/backup-20261118T155327`: dump **10.052.120 B**, filestore **294.236.851 B / 1.025 mục**, danh sách restore **15.598 mục**; có source/config trong bộ backup.
- **PC server bản 20.0.2.0.1:** **APPLIED** `cfc1af70`, checksum37/37, upgrade0/0ERROR, ORMreadonly20/20; chi tiết giao bản ở cuối tài liệu.
- **Đăng nhập A/B thực, MFA đầy đủ, đa worker và race giao dịch của bản hiện tại:** **NOT_RUN**. Không có credential được phép dùng để kiểm; không reset mật khẩu, tạo actor giả hoặc thay phiên người đang làm việc trên main/server. Không bắt buộc kiểm18079 và không chạy lại18079 trong lượt hiệu chỉnh này.
- **Trực quan/nghiệp vụ người dùng và cho phép pilot:** **CHỜ NGƯỜI DÙNG XÁC NHẬN**. Người dùng tự chọn tài khoản và thời điểm kiểm hai thiết bị; lần đăng nhập mới sẽ thay phiên đang dùng.

## 2. Hiệu chỉnh so với 20.0.2.0.0

Odoo dùng PostgreSQL `REPEATABLE READ`; chỉ lấy advisory lock rồi SELECT trên cursor request không làm mới snapshot. Bản `20.0.2.0.1` giữ shared transaction lock `(761157, uid)` trên request ghi và đọc winner bằng **cursor primary mới sau khi lấy khóa**, kiểm lại bằng cursor mới ở precommit. Khóa request giữ đến hết giao dịch nghiệp vụ để login mới không vượt qua điểm commit. Route readonly cũng kiểm winner qua primary mới thay vì snapshot request/replica cũ. Login dùng `SELECT ... FOR UPDATE`; hook đăng nhập hoàn tất loại binding precommit của danh tính vừa được thay để giữ luồng native chuyển người dùng trong cùng cookie.

Khi nhận lý do hết phiên hợp lệ, frontend che document và **hard navigation cùng origin tới `/tp/session-ended`**. Route public này kiểm tombstone server, không tin mã lý do do client gửi; trả trang QWeb riêng với `Cache-Control: no-store, private`, đúng thông báo và liên kết **Đăng nhập lại** về trang thương hiệu rồi Trang chủ. Document mới loại webclient cũ cùng callback, cache và timer; đây là trang độc lập, không còn dùng overlay OWL làm màn cuối. `pagehide` ẩn document trước snapshot bfcache; `pageshow` persisted reload qua xác thực backend khi document vẫn ẩn. Unit frontend kiểm đúng thứ tự che/xóa DOM trước navigation, không navigation lặp và bfcache không tự hiện lại.

## 3. Bằng chứng lịch sử — chỉ bản 20.0.2.0.0

Các kết quả dưới đây giữ để truy vết, **không được tính là chạy lại hoặc PASS toàn bộ bản 20.0.2.0.1**:

- Odoo `HttpCase` `TestNativeLogin` trên `tp_tanphat_test`18079: **10/10 PASS** (HR lock, TOTP tiếng Việt/cancel, CSRF/open redirect và thay cookie phiên).
- Playwright bốn context trên18079: **24/24 PASS**, desktop1440×900/mobile390×844/reduced motion; bus khoảng**1,18 giây**, fallback khoảng**0,83 giây**, không JS page error/HTTP5xx. Ảnh và summary: `.local/auth-session001/e2e-18079/`. Các ảnh ghi overlay cũ, không phải ảnh trang QWeb mới.
- Probe PostgreSQL cũ: **8/8 PASS** về hành vi khóa/compare-and-clear được kiểm. Probe dùng psycopg2 isolation mặc định, **không chứng minh race request Odoo REPEATABLE READ, nhiều worker hoặc precommit ghi trễ**. Probe từng ghi trong savepoint rồi rollback; không coi đây là probe read-only và không chạy lại trên main/server trong lượt này.
- Hồ sơ cũ ghi upgrade18069 và PC server, health/login/API smoke và bảo toàn snapshot. Bản hiệu chỉnh cần bằng chứng rollout riêng; trạng thái hiện tại tại mục1.

## 4. Ma trận nghiệm thu bản 20.0.2.0.1

| Mã | Tiêu chí | Bằng chứng hiện tại | Trạng thái / phần còn lại |
| --- | --- | --- | --- |
| AS-01 | B login thành công thay A; cookie A bị chặn API/RPC/file không phụ thuộc JS; đúng thông báo và một nút | Unit kiểm winner/lý do; local render trang QWeb PASS; lịch sử A/B chỉ bản cũ | **PARTIAL**; A/B và file trực tiếp bản mới **NOT_RUN** |
| AS-02 | A đăng nhập lại cùng origin về Trang chủ, B bị thay; logout cũ không xóa winner mới | Unit compare-and-clear PASS; route trang độc lập dùng URL relogin server | **PARTIAL**; luồng login thật trên trang mới **NOT_RUN** |
| AS-03 | Sai password/OTP, MFA chưa xong không thay winner; hoàn tất MFA mới thay | Hook native finalize được giữ; lịch sử HttpCase/TOTP bản cũ | **NOT_RUN** toàn luồng MFA và A/B bản mới |
| AS-04 | Nhiều tab một cookie không đá nhau; hai user độc lập | Source giữ generation khi cùng winner; lịch sử browser/khóa bản cũ | **NOT_RUN** browser đa tab/hai user bản mới |
| AS-05 | Đa worker/login đồng thời/rollback/SID rotation/ghi in-flight không vi phạm cutover | Mock8/8 gồm snapshot request cũ đọc winner mới sau khóa, readonly snapshot cũ và logout compare-and-clear; fresh cursor + shared lock/precommit và login row lock đã sửa | **PARTIAL**; race Odoo REPEATABLE READ đa kết nối thực và rollback/login đồng thời **NOT_RUN**; PG8/8 cũ không thay bằng chứng này |
| AS-06 | Bus/fallback; hủy đời webclient cũ, không render response trễ hoặc lộ DOM bfcache; desktop/mobile | Frontend harness PASS: hide/scrub trước hard navigation đúng một lần, bfcache hidden đến reload; local QWeb render PASS | **PARTIAL**; browser trang mới, response trễ thực, offline/focus/PWA/bfcache và đo bus/fallback bản mới **NOT_RUN**; độ trễ lịch sử không phải đo mới |
| AS-07 | Tách replaced/cutover với mạng/quyền/hết hạn, không replay mutation | Unit8/8 và source giữ mã lỗi; trang độc lập không có payload mutation | **PARTIAL**; network/403/browser integration bản mới **NOT_RUN** |
| AS-08 | Giữ HR lock, admin DEC-053/054, identity recheck và stateless API integration | Snapshot local giữ dữ liệu/quyền; probe16/16 gồm guard người chỉ xem; lịch sử HttpCase bản cũ | **PARTIAL**; thực auth/khóa/MFA/API key bản mới **NOT_RUN** |
| AS-09 | Backup, upgrade18069/PC server, smoke public, bảo toàn nghiệp vụ |18069 exit0/0ERROR, snapshot chỉ modules; backup và probe16/16 tại mục1 | **LOCAL_APPLIED_PC_PENDING** |
| AS-10 | Người dùng kiểm hai thiết bị thật, xác nhận trực quan/độ trễ/về Trang chủ | Chưa thực hiện; không suy từ unit hoặc smoke | **NOT_RUN — CHỜ NGƯỜI DÙNG** |

## Giao bản PC server — CHG-20261118-024

- Code `cfc1af7033b84e432512daca9ecffe391aab9391` đã push `origin/main`, deploy đúng37/37 checksum lên PC server hiện có; upgrade `tp_hr_workspace,tp_admin_delegation,tp_web_login` exit0/0ERROR. Runtime: HR20.0.1.13.0, auth20.0.2.0.1, admin20.0.2.0.1; API20.0.1.2.0 giữ.
- Backup server `C:/TANPHAT-backups/auth-hr-finish/auth-hr023-20261118T160600`: dump9.703.292B, filestore29.880.555B/609 archive entries, source-config2.124.283B, restore15.598, SHA256SUMS. Snapshot trước/sau chỉ đổi modules; giữ39 nhân viên/32 user/55 thiết bị/456 ngày công/nhóm quyền/ledger/roster/baseURL. Không so số liệu server với datasetlocal.
- Probe ORM server trong READ ONLY20/20 PASS: sequence phân biệt theo phòng, thứ tự private/public, combined list views, Admin gốc+4admin grant có capability sắp xếp, viewer không có capability và bị chặn action trực tiếp, direct sequence write củaadmin bị chặn, trang QWeb hết phiên render đúng. Không thực thi reorder/nghiệp vụ ghi để kiểm.
- Playwright anonymous + HTTP + trang hết phiên render từ QWeb19/19 PASS: loginlocal/public desktop1440×900/mobile390×844, không tràn, API401, đúng copy/nút/hrefHome;0lỗiJS. Trang hết phiên dùng HTML do ORM render và browser route mock để kiểm hình thức, không gọi là A/B loginE2E.
- Preflight phát hiện inventoryserver là prefix cũ chính xác của tài liệu đã commit; chỉ thiếu các mục chấm công đã commit. Đã đối chiếu rồi đồng bộ bản Git đầy đủ, không mất nội dung riêng. Source sidebar lệch có sẵn được giữ, không thuộc gói. Không restarttunnel, không dùng18079 hoặc tạo actor/đổi phòng người thật.
- Các ca NOT_RUN nêu trên vẫn giữ: đầy đủA/B thật/MFA/multiworker/race/HOOT/ghi reorder rồi reload ởDB đang dùng. Nghiệm thu trực quan và nghiệp vụ người dùng riêng. Bản sửa đã giao; người dùng tự kiểm hai thiết bị và thao tác thứ tự thực tế vào thời điểm phù hợp.
