# KH-KD — Kiểm chứng chênh lệch thao tác HEAD/SUPPORT

Ngày 09/11/2026. CHG-20261109-006. Phạm vi: kiểm tra phản ánh SUPPORT
có thể thêm/sửa/xóa dự án, hợp đồng trong khi HEAD ít tác vụ hơn.
Đây là kiểm chứng hẹp, không thay kết luận audit KD-ACCESS-002 hoặc duyệt V2.

## Kết quả quan sát thực tế

- Đăng nhập riêng HEAD và SUPPORT trên dev18069, chỉ đọc nghiệp vụ.
  SUPPORT có hai lựa chọn Tạo hồ sơ: cơ hội/hồ sơ thầu và năng lực/chứng chỉ;
  HEAD chỉ có cơ hội/hồ sơ thầu. Danh sách dự án/hợp đồng của cả hai không
  hiện nút tạo; form đầu tiên đọc được không có ô nhập chỉnh sửa.
- RPC `has_access` trên bản ghi trong scope ở dev: cả hai được đọc
  `project.project` và `tp.contract`, không được create/write/unlink.
  `get_kd_ui_permissions`: CRM create=true cho cả hai; credential create=true
  cho SUPPORT và false cho HEAD. Không dùng riêng việc ẩn nút làm bằng chứng quyền.
- Trên clone owned `tp_tanphat_kdaccess002_20261109`, source ba addon
  `tp_project`, `tp_contract`, `tp_kd_workspace` khớp source dev:
  mỗi vai thử create/write/unlink dự án managed trong scope,
  create/write/unlink hợp đồng và xác nhận wizard tạo hợp đồng native.
  Cả 14 thao tác bị AccessError; savepoint/transaction rollback và đối chiếu
  số bản ghi/tên dự án-hợp đồng giữ nguyên. Lệnh unlink dự án gặp kiểm quyền
  task phụ thuộc trước; không suy rộng kết quả này cho mọi cấu trúc dự án.
- Chưa tái hiện được khả năng SUPPORT lưu thêm/sửa/xóa dự án hoặc hợp đồng
  theo phản ánh. Chưa thử mọi bản ghi, route, tài khoản hoặc cấu trúc dự án.
  Không suy kết quả hẹp thành toàn bộ hệ thống an toàn; F1–F3 audit004 vẫn mở.

## Nguyên nhân chênh lệch và hướng xử lý

Preset `POLICY` trong `scripts/kd_access001.py` cấp HEAD quyền tiền và
commercial review, typed hồ sơ chỉ review; SUPPORT được prepare credential.
KD-ACCESS-002 mở opportunity prepare cho cả hai. Vì vậy HEAD ít mục tạo hơn
SUPPORT là kết quả có thật của preset, không phải chức danh tự sinh quyền.
Preset này chưa đáp ứng hướng trưởng ban quản lý nghiệp vụ toàn Ban đã đề xuất.

Giữ [đề xuất V2](../security/KD_ROLE_POLICY_V2_PROPOSAL.md) chờ người dùng
duyệt: HEAD cần quyền nghiệp vụ lập/sửa nháp, điều phối/phân công và kiểm soát
báo cáo; SUPPORT làm hồ sơ trong phạm vi được giao. Tách thẩm quyền hệ thống,
BASE, ký và chứng từ đã chốt; không mở xóa vật lý hồ sơ có lịch sử cho đủ nút.
Chưa viết prompt triển khai V2 hoặc đổi quyền, tài khoản, mật khẩu hay dữ liệu dev.

## Bằng chứng và giới hạn bàn giao

Bằng chứng private ignored ở `.local/kd-role-ui-investigation-20261109/`:
`dev-ui.json`, `dev-backend-rights.json`, `clone-write-probes.json` và tám ảnh
danh sách/chi tiết theo hai vai. Không đưa danh tính hoặc credential vào Git.
Một lần in JSON sau kiểm clone lỗi encoding console cp1258; JSON kết quả đã
ghi đầy đủ trước lỗi và đã đọc lại. Có cảnh báo markdown2 thiếu; không cài thêm.
Dev18069 giữ chạy; clone HTTP vẫn dừng, không upgrade/restart/apply.

Không sửa application code; không commit/push. Subagent không khởi chạy được
do lỗi model kế thừa, kiểm chứng do phiên chính thực hiện. Checkpoint công việc
khác được giữ; không finish hoặc sửa AI_WORKFLOW_STATE thay batch đó.
