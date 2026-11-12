# KD-ACCESS-002 — Hậu kiểm phân quyền KH-KD

Ngày 09/11/2026, Asia/Saigon. Bàn giao: CHG-20261109-004.

**Kết luận: `AUDIT_FAILED_SECURITY_CORRECTION_REQUIRED`.** Quyền đọc dự án,
CRM, tiền và các luồng đã có vượt qua bộ test hiện hành, nhưng ba ca kiểm tra
native bổ sung chứng minh bảo vệ file/chatter chưa kín. Chưa nghiệm thu toàn
bộ phân quyền KH-KD; chưa chuyển sang Project/WBS hoặc pilot.

Đây là hậu kiểm của phiên điều phối đối với bản bàn giao CHG-20261109-003.
Thử giao review cho subagent không chạy được do lỗi model; không tính đó là
một lượt review hoặc bằng chứng đạt. Các kết luận dưới đây dựa trên source và
kết quả chạy lại, không chỉ dựa vào báo cáo của phiên triển khai.

## 1. Baseline và phạm vi kiểm tra

- Làm việc tại `C:\TANPHAT ONE`. Dev vẫn `tp_tanphat_dev`, HTTP18069;
  test là clone owned `tp_tanphat_kdaccess002_20261109`, HTTP19289/PG55432.
- Dev: Workspace20.0.1.6.0, Home20.0.1.4.1, Login20.0.1.1.0.
  Hai addon có delta khớp clone = seal = source dev, 89 file; kiểm lại sau test.
- Không sửa application code/core, không upgrade/restart dev, không thay
  password, group, assignment hoặc grant của tài khoản thật; không commit/push.
  Dev chỉ kiểm đọc nghiệp vụ và đăng nhập. Thử ghi chỉ trên clone bằng dữ liệu giả.
- Bằng chứng mới lưu riêng tại [.local/kd-access002-audit-20261109](../../.local/kd-access002-audit-20261109/),
  không ghi đè báo cáo/ảnh triển khai trong `.local/kd-access002/`.

## 2. Kết quả thực chạy

| Nhóm | Kết quả | Bằng chứng |
| --- | --- | --- |
| Odoo hồi quy 5 addon trên clone | 157/157; 0 failed, 0 test error | `odoo-rerun.json`; log mới `../kd-access002/odoo-tests/20261109T043818989330Z.log` |
| Ma trận 5 tài khoản trên dev | 1.426 kiểm tra đạt, không commit transaction | `dev-rights-rerun.json` |
| Ma trận 5 tài khoản trên clone | 1.426 kiểm tra đạt | `clone-rights-business.json` |
| Thao tác typed/contract trên clone | 274 assertion nghiệp vụ đạt, rollback và đối chiếu account/rights đạt | `clone-rights-business.json`; tương đương 275 khi tính thêm assertion bảo toàn sau rollback |
| Browser dev, 5 context riêng | 112/112; 0 console/page error | `dev-browser.json`, `shots/dev/after/` |
| Native tạo/sửa/tiền/prepare/submit, clone | 30/30; 0 browser error | `native-flows.json`, `shots/clone/after/` |
| Kiểm tra native bổ sung | 3 nhóm lỗi xác nhận, chi tiết mục 3 | `native-route-probes.json`, `native-route-extra.json`, `pdf-preview-probe.json`, `adversarial-orm.json` |

Log hồi quy có cảnh báo thiếu `markdown2` và `PermissionError` của Windows
khi Odoo dọn file rác trong filestore clone. Odoo vẫn báo 157 test đạt, exit0;
đây không phải log sạch hoàn toàn. Chưa thay ACL filesystem hoặc xóa file để
che cảnh báo; cần xử lý vận hành clone riêng, không suy thành lỗi dev.

Không chạy lại HOOT, backup/restore hoặc full source rollback trong hậu kiểm
này vì không đổi code. Các số đó trong CHG-003 là bằng chứng triển khai cũ.
Browser dùng Chromium và mô phỏng mobile, chưa xác nhận thiết bị thật/Safari.

## 3. Ba lỗi phải sửa

### F1 — P1: preview PDF không giữ quyền đọc tiền của hồ sơ cha

Tài khoản `support` không có `financial_read` bị chặn đọc file trực tiếp
(HTTP404), nhưng preview PDF native trả HTTP200 và trang PDF có nội dung giả
đã đặt để kiểm tra. Đã xác nhận chữ trong PDF trả về, không chỉ kiểm status.
File thuộc cơ hội của tài khoản khác, cùng dự án được đọc, trạng thái submitted;
không dùng token chia sẻ.

Điểm cần sửa: `custom_addons/tp_kd_workspace/models/opportunity_access.py:393`
và `security/ir.access.csv:7`. Guard hiện đặt tại `ir.binary._find_record` và
quyền attachment chỉ ràng buộc thao tác đọc. Native preview còn chấp nhận
ownership dựa trên quyền write: kiểm thực tế cho cùng file là read=False,
write=True, ownership không token=True. Đường preview này không đi qua guard
binary đã bổ sung. Điểm native tham khảo là
`addons/mail/controllers/attachment.py:172` và
`addons/mail/models/ir_attachment.py:27`; không sửa các file upstream đó.

Sửa tối thiểu: ràng buộc quyền ở điểm kiểm quyền/hook/controller custom phù hợp,
luôn kiểm actor và hồ sơ cha trước nhánh ownership/sudo. Bao phủ preview,
thumbnail, download và token khi grant bị thu hồi; không mở quyền tiền để chữa UI.
Nếu bỏ qua, người không được xem tiền vẫn có thể đọc nội dung PDF tài chính.

### F2 — P1: upload/delete native bỏ qua điều kiện owner, tiền và khóa sau nộp

Direct ORM create attachment bị từ chối đúng; cùng actor và cùng hồ sơ qua
upload native lại tạo file thành công. Đã xác nhận cả support trên hồ sơ mình
không có quyền tiền, support trên hồ sơ submitted của deputy, và deputy trên
hồ sơ submitted của chính mình. Support cũng xóa được file vừa thêm vào hồ sơ
submitted của người khác qua native delete. Các ca ngoài project bị từ chối,
không kết luận đã vượt toàn bộ phạm vi công ty/dự án.

Điểm cần sửa: `models/opportunity_access.py:321` và `:333`. Các guard mutation
bỏ qua `env.su`, trong khi native upload/delete có nhánh nâng quyền sau khi kiểm
quyền parent/ownership. Native tham khảo `addons/mail/controllers/attachment.py:69`
và `:114`. Đây là lỗi toàn vẹn hồ sơ, không chỉ là thiếu nút hoặc thiếu grant.

Sửa tối thiểu: kiểm policy CRM trước nâng quyền, dùng chung điều kiện với ORM
và row lock hiện có cho cả upload/delete/relink/pending attachment. Owner,
prepare, financial_read và state phải cùng được kiểm. Nếu bỏ qua, căn cứ hồ sơ
đã nộp vẫn thay đổi được dù hành động sửa CRM thông thường bị khóa.

### F3 — P1: native chỉnh tin nhắn trả nội dung chatter đang bị chặn đọc

Support bị từ chối direct read body của một tin nhắn giả gắn CRM, nhưng đường
native chỉnh nội dung trả response có nội dung tài chính giả đó; thao tác sửa
cũng thành công. Tin nhắn do hệ thống fixture tạo với support là author.
Native post cũng cho ghi thêm trao đổi trên hồ sơ submitted của người khác.
Chưa khẳng định mọi tin nhắn của mọi author đều đọc được.

Điểm cần sửa: `security/ir.access.csv:8` và `models/opportunity_access.py:375`.
Hiện chỉ có domain read; các đường native còn dùng fallback parent access,
kiểm author và sudo. Native tham khảo `addons/mail/models/mail_message.py:749`
và `addons/mail/controllers/thread.py:262`. Cần kiểm trước khi serialize body,
attachment hoặc response cập nhật, không chỉ đặt read domain cho direct RPC.

Sửa tối thiểu: hook/controller custom giữ policy nội dung CRM xuyên suốt native
read/post/update, kể cả author hiện tại nhưng đã mất grant. Phân biệt trao đổi
bổ sung và sửa căn cứ đã nộp bằng quy tắc tường minh; chưa có policy thì không
tự mở thao tác. Nếu bỏ qua, quyền chặn chatter không bảo vệ được đường native.

## 4. Phần còn thiếu đã được khai báo đúng

- **Project/WBS scoped create/edit:** chưa triển khai, cả 5 vai chỉ đọc theo
  assignment. Không cấp manager chung để thay cho chức năng còn thiếu.
- **Phân loại file/chatter CRM:** đang chặn gộp theo quyền tiền; support và hồ
  sơ chưa gắn dự án thiếu khả năng cộng tác hồ sơ chung. Cần thiết kế quyền nội
  dung chung/tài chính riêng sau khi sửa F1–F3; việc này không tự giải quyết lỗi.
- **Báo cáo KH-KD:** vẫn dùng lại Tổng quan; task báo cáo riêng chưa triển khai.
- Q2/business acceptance/pilot/BASE/ký/hiệu lực/thực chi không được đóng bởi audit.

## 5. Thứ tự tiếp theo và điều kiện đóng audit

1. Claude thực hiện [prompt correction](../prompts/CLAUDE_KD_ACCESS_002_SECURITY_CORRECTION.md)
   cho F1–F3 trên clone; acceptance test phải tái hiện lỗi trước sửa.
2. Chạy lại ca native bất lợi, thu hồi quyền cùng phiên, scope/state và hồi quy
   5 vai; kiểm không ảnh hưởng file/chatter của model khác và quyền admin hợp lệ.
3. Hậu kiểm lại delta. Chỉ khi đạt và có lệnh áp dev phù hợp mới nâng cấp18069
   theo backup/restore verified và preservation; audit này không tự áp bản sửa.
4. Sau đó mới thiết kế/triển khai Project–WBS theo quyền riêng và tách tài liệu
   CRM chung/tài chính. Không gọi KH-KD hoàn thiện100% ở bước này.

Đã giữ dữ liệu giả/evidence trên clone để tái hiện; runtime clone do phiên audit
mở được dừng khi bàn giao. Dev18069/PG55432 giữ nguyên tiến trình.

### Checkpoint khi bàn giao

Checkpoint có sẵn từ04:42:05UTC, ban đầu source/docs khớp baseline003. Cuối lượt xuất hiện thay đổi tooling `scripts/kd_report001.py` thuộc công việc khác; audit không sửa hoặc nhận là đã test file đó. Không finish checkpoint thay batch khác, không sửa AI_WORKFLOW_STATE.json bằng tay. Source hai addon đã kiểm vẫn khớp seal; git diff --check mặc định đạt. Một lần override core.autocrlf=false tạo báo lỗi CRLF trên file có sẵn; đã bỏ override và kiểm lại đạt, không đổi hàng loạt file. Batch đang sở hữu checkpoint cần đối chiếu tài liệu audit004 trước bàn giao tiếp.
