# HR-EMPLOYEE-ORDER — Kiểm kỹ thuật và nghiệm thu

Cập nhật 18/11/2026 (Asia/Saigon). Phiên bản: `tp_hr_workspace` **20.0.1.13.1**, `tp_admin_delegation` **20.0.2.0.1**.

Nguồn: [DEC-044/053/054](../DECISIONS.md), [quy chuẩn bộ lọc](../ui/TP_TABLE_FILTER_STANDARD.md), [inventory HR-T01](../ui/TP_TABLE_FILTER_INVENTORY.md), [hướng dẫn sử dụng](HR_EMPLOYEE_ORDER_USER_GUIDE.md), [policy giao bản](../operations/TP_CONTINUOUS_DELIVERY_POLICY.md).

## Bản sửa hiện hành — CHG-20261118-026

HR `20.0.1.13.1` đã áp18069; PC server chờ gói này được push/deploy. Người dùng yêu cầu bỏ sáu chấm, kéo trực tiếp từ hàng. Click thường vẫn mở hồ sơ; checkbox/nút/link/input không khởi động kéo. Sort/filter và backend quyền/company/department/anchors giữ như gói trước.

Lỗi đã tái hiện: native draggable bật `body.pe-none`; khi thả trên placeholder, `elementsFromPoint` không có table hoặc dòng nguồn, khiến nhánh cũ bỏ RPC âm thầm và hàng về cũ. Bản sửa dùng tọa độ cuối của pointerup trong bounds phòng nguồn, cùng kiểm group/parent native. Server log60phút không có reorder xác nhận lần kéo trước chưa tới backend.

| Kiểm đã chạy | Kết quả và giới hạn |
| --- | --- |
| Browser native, tracked script `scripts/tests/test_hr_employee_order_browser.cjs` | PASS3template không có handle, native sortable và sortStart/sortStop thật, tái hiện pe-none+placeholder, kéo lên/xuống đúng RPC/anchors, khác phòng/ngoài bảng khôngRPC, save lỗi reload, nút/checkbox không kéo,0pageerror. Lifecycle/model/RPC vẫn mock |
| Node VM + backend thuần/action mock | PASS click thường delegates, drag chặn mở hồ sơ/checkbox, sort/filter/pagination/viewer và lỗi lưu; backend12/12 |
| ORM thật sau backup, luôn rollback | PASS action lên/xuống, flush/invalidate/SQL đọc lại, sequence dense, anchor khác phòng và viewer bị chặn; fresh READ ONLY cursor xác nhận SHA256 employee/version/company/users/group-rel không đổi |
|18069| HR20.0.1.13.1, upgrade chỉ HR exit0/0ERROR; backup `.local/hr-order-row/backup-20261118T163542`, restore15.600mục, filestore1.027file; snapshot chỉ moduleversion đổi |

Chưa chạy full HOOT (4ca source), full authenticated renderer/persist sau commit bằng browser, đăng nhập lại/máy khác hoặc PostgreSQL race. Không lấy browser mock hay rollback transaction làm bằng chứng persist qua giao dịch commit. Không tạo fixture/login/đổi phòng người thật, không18079. Nghiệm thu người dùng riêng.

## Gói ban đầu và evidence lịch sử

Các kết quả20.0.1.13.0 dưới đây là lịch sử trước phản hồi lỗi và bản sửa026; phần kiểm mới dùng bảng trên.

## Trạng thái bàn giao

**Đã áp dụng 18069 và PC server, kiểm kỹ thuật có giới hạn. Chưa nghiệm thu trực quan/nghiệp vụ hoặc cho phép pilot bởi người dùng.** Kết quả mock không chứng minh thao tác kéo thật đã lưu PostgreSQL.

- Backend unit thuần và action thật qua mock ORM: **12/12 PASS**. Bao gồm actor chỉ đọc, quyền đọc/ghi toàn bộ hồ sơ ảnh hưởng, anchor khác phòng/công ty hoặc đã thay đổi/lưu trữ, ID không hợp lệ, token RPC giả, phân trang và chỉ ghi `sequence`.
- Node VM harness: **PASS**. Browser biên dịch **3 template native** và chạy sortable thật trên DOM dựng riêng, pointer kéo lên/xuống/cross-department/ngoài bảng với RPC mock: **PASS**. Evidence ignored: `.local/hr-employee-order/native-drag-result.json`. Đây chưa phải renderer đầy đủ trên danh sách Odoo thật, chưa xác nhận persist/reload dữ liệu thật.
- Có **3 HOOT static tests**, **NOT_RUN**: route public `/web/tests` yêu cầu xác thực; không coi harness thay thế kết quả HOOT.
- Nâng cấp local: **exit0 / 0ERROR**. Probe chỉ đọc **16/16 PASS**. Snapshot trước/sau chỉ thay module/schema/thứ tự khởi tạo; giữ **39 nhân viên, 28 tài khoản, 55 thiết bị, 365 dòng công ngày, 0 grant**, dữ liệu nghiệp vụ được đối chiếu không đổi. Schema sequence đã có, migration khởi tạo giá trị distinct đã persist; chưa thực hiện reorder nghiệp vụ thật.
- Backup local trước nâng cấp: `.local/auth-hr-finish/backup-20261118T155327`; dump **10.052.120B**, filestore **294.236.851B / 1.025 file**, danh mục restore **15.598** mục.

## Ma trận tiêu chí và bằng chứng

| Mã | Thao tác/kỳ vọng | Kết quả đã kiểm | Phần còn thiếu |
| --- | --- | --- | --- |
| HEO-01 | Admin/HR có quyền ghi kéo lên/xuống trong cùng phòng; lưu, thông báo, reload giữ thứ tự; không mở form/checkbox | Template native và sortable thật với pointer trên DOM dựng riêng/RPC mock PASS | Chưa chạy full renderer với dữ liệu thật; chưa xác nhận ghi DB, thông báo và reload sau reorder thật; chưa nghiệm thu desktop/mobile trực quan |
| HEO-02 | Danh sách/Danh bạ dùng `sequence,id`, migration giữ cấu trúc nghiệp vụ | Source/model/view mặc định `sequence,id`; local schema/migration và probe chỉ đọc PASS; sequence khởi tạo distinct đã persist | Chưa chứng minh thứ tự từng dòng trước/sau bằng browser thật; PC server chưa áp |
| HEO-03 | Chặn kéo khác phòng/ngoài bảng; RPC anchor khác phòng/công ty và ghi sequence trực tiếp bị từ chối | Pointer mock cross-department/ngoài bảng PASS; backend action mock chặn anchor khác scope; token context giả bị chặn; payload hợp lệ chỉ ghi sequence | Chưa gọi mutation RPC thật trên local/server; không chuyển phòng thật để test |
| HEO-04 | Đổi sort/lọc ẩn nhân viên khóa kéo; lọc phòng riêng vẫn cho phép; có reset | Node VM harness và source rules PASS | HOOT3 NOT_RUN; chưa kiểm tổ hợp filter/sort trên renderer thật và responsive |
| HEO-05 | Chèn theo before/after trên toàn phòng, giữ nhân viên ngoài trang | Unit thuật toán và action mock đầy đủ hồ sơ PASS; client chỉ gửi moved/anchor IDs; sequence cập nhật đúng toàn phòng | Chưa test phân trang nhiều nhân viên thật bằng ORM/browser |
| HEO-06 | Tuần tự reorder/create/transfer, chống snapshot cũ; lỗi lưu khôi phục UI | Helper được unit xác nhận khóa advisory `(761101,company_id)` theo thứ tự công ty và MVCC `UPDATE res_company SET id=id`; action kiểm hai anchor liền nhau; source dùng transaction Odoo/native retry | Chưa chạy race PostgreSQL hai kết nối hoặc lỗi RPC trên full renderer. MVCC sentinel giữ nguyên giá trị và write_date công ty; không phải khóa761158 theo phòng |
| HEO-07 | Người chỉ đọc không có quyền reorder hoặc ghi sequence | Backend mock từ chối trước lock/write; kiểm ACL mọi hồ sơ ảnh hưởng; context RPC không giả được token nội bộ | Chưa mutation bằng actor thật; chưa kiểm ẩn tay nắm trên renderer thật của actor chỉ đọc |
| HEO-08 | Admin gốc và admin được cấp dùng quyền quản lý nhân viên hợp lệ, giữ DEC-054 | Probe chỉ đọc nằm trong16/16; guard chỉ cho ngoại lệ token nội bộ với đúng trường sequence; action mock xác nhận chỉ ghi sequence | Chưa reorder thật bằnguid2/uid43; không tuyên bố nghiệm thu nghiệp vụ/admin từ mock |
| HEO-09 | Backup, upgrade local/server, giữ dữ liệu và smoke public | Local backup và upgrade0/0ERROR; snapshot/probe local đạt như trên | PC server đã giao cfc1af70, backup/upgrade0ERROR/checksum37/37/ORM20; xem phần giao bản cuối tài liệu |

## Giới hạn và cổng còn mở

Không chạy18079; không tạo actor/dữ liệu giả, không thử ghi/reorder/chuyển phòng thật trên main/server. Các test hành vi ghi chỉ dùng mock; migration schema/sequence khởi tạo là thay đổi runtime đã áp local trong nâng cấp được ủy quyền. Chưa chạy race thật, full renderer/persist/reload, HOOT và nghiệm thu trực quan/nghiệp vụ người dùng. PC server đã triển khai và kiểm chứng như mục CHG-024 dưới đây; không dùng smoke/mock thay nghiệm thu ghi nghiệp vụ.

## Giao bản PC server — CHG-20261118-024

- Code `cfc1af7033b84e432512daca9ecffe391aab9391` đã push `origin/main`, deploy đúng37/37 checksum lên PC server hiện có; upgrade `tp_hr_workspace,tp_admin_delegation,tp_web_login` exit0/0ERROR. Runtime: HR20.0.1.13.0, auth20.0.2.0.1, admin20.0.2.0.1; API20.0.1.2.0 giữ.
- Backup server `C:/TANPHAT-backups/auth-hr-finish/auth-hr023-20261118T160600`: dump9.703.292B, filestore29.880.555B/609 archive entries, source-config2.124.283B, restore15.598, SHA256SUMS. Snapshot trước/sau chỉ đổi modules; giữ39 nhân viên/32 user/55 thiết bị/456 ngày công/nhóm quyền/ledger/roster/baseURL. Không so số liệu server với datasetlocal.
- Probe ORM server trong READ ONLY20/20 PASS: sequence phân biệt theo phòng, thứ tự private/public, combined list views, Admin gốc+4admin grant có capability sắp xếp, viewer không có capability và bị chặn action trực tiếp, direct sequence write củaadmin bị chặn, trang QWeb hết phiên render đúng. Không thực thi reorder/nghiệp vụ ghi để kiểm.
- Playwright anonymous + HTTP + trang hết phiên render từ QWeb19/19 PASS: loginlocal/public desktop1440×900/mobile390×844, không tràn, API401, đúng copy/nút/hrefHome;0lỗiJS. Trang hết phiên dùng HTML do ORM render và browser route mock để kiểm hình thức, không gọi là A/B loginE2E.
- Preflight phát hiện inventoryserver là prefix cũ chính xác của tài liệu đã commit; chỉ thiếu các mục chấm công đã commit. Đã đối chiếu rồi đồng bộ bản Git đầy đủ, không mất nội dung riêng. Source sidebar lệch có sẵn được giữ, không thuộc gói. Không restarttunnel, không dùng18079 hoặc tạo actor/đổi phòng người thật.
- Các ca NOT_RUN nêu trên vẫn giữ: đầy đủA/B thật/MFA/multiworker/race/HOOT/ghi reorder rồi reload ởDB đang dùng. Nghiệm thu trực quan và nghiệp vụ người dùng riêng. Bản sửa đã giao; người dùng tự kiểm hai thiết bị và thao tác thứ tự thực tế vào thời điểm phù hợp.

Kiểm assets sau deploy (CHG-20261118-025): native `web.assets_backend` biên dịch trong READ ONLY **561 CSS / 1.786 JS / 75 khối XML**, không lỗi CSS, không lưu asset attachment. Đây là kiểm biên dịch bundle thực; full browser login/HOOT và các ca NOT_RUN vẫn giữ.
