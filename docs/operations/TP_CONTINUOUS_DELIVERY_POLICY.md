# Giao bản liên tục — chỉ thị người dùng ngày17/11/2026

Người dùng yêu cầu: **"làm đến đâu thì pushgit và deploy lên pc sever luôn",
"ko cần test trên cổng18079 nữa"**. Đây là quyền push/deploy cho các hạng mục
được giao, áp dụng từ chỉ thị này đến khi có chỉ thị mới hơn. Không phải yêu
cầu xóa DBtest, đưa dữ liệu giả vào server hoặc triển khai các ý tưởng chưa giao code.

## Một hạng mục hoàn tất

Là phần chức năng/sửa lỗi đã thực hiện đủ scope có thể dùng được, hoặc bộ
tài liệu đã hoàn chỉnh. Chia phần lớn thành hạng mục nhỏ dùng được; không
đợi toàn module mới giao. Không coi từng dòng code hoặc bản đang lỗi là release.

1. Đọc status và source/server thực tế; giữ checkpoint/diff của batch khác.
2. Thực hiện đúng scope, kiểm cú pháp/build và hành vi cần thiết. Không bắt
   mở18079/testDB trước deploy; không tự chuyển bộ test ghi dữ liệu sang main.
3. Chuẩn bị backup/rollback đúng môi trường trước thay đổi schema/dữ liệu/
   quyền/tệp; không dùng backup local thay backup server. Kiểm gói source,
   dependency và cấu hình; không deploy khi đã biết lỗi làm hỏng hệ thống.
4. Commit file/hunk đúng batch, push lên remote/branch đã cấu hình. Không
   `git add .`, force-push, reset, nhận diff người khác hoặc push unpushed
   commit chưa xác định phạm vi. Không đưa secret, dump, filestore, hồ sơ nhân viên lên Git.
5. Deploy chính bản vừa push lên PCserver hiện có, áp18069 nếu task cần;
   upgrade/restart đúng service/module có thay đổi. Không copy cả working
   tree chứa code dở lên server. Nếu chênh lệch baseline/dependency chưa nằm
   trên Git, xác định và báo đúng trước, không nhận là code mình đã kiểm.
6. Kiểm public: đăng nhập/session, màn/action vừa đổi, dữ liệu/ảnh/tệp liên
   quan, lỗi server và quyền truy cập. Không tạo người giả/cấp quyền người
   thật/CRUD phá dữ liệu để smoke. Lỗi do release thì sửa ngay hoặc rollback.
   Với asset native, kiểm nội dung JS/CSS do URL bundle mới thực sự phục vụ;
   Odoo tính phiên bản theo đường dẫn và mtime, không theo hash nội dung.
   Gói tar phải giữ mtime commit/file mới cho static asset; không để mặc định0
   hoặc dùng lại mtime cũ cho nội dung mới. Restart/upgrade đơn thuần không
   bảo đảm vô hiệu hóa bundle cũ. Xem [ca HR](../../ops/runbooks/HR_EMPLOYEE_ORDER_DEPLOY_AND_ROLLBACK.md).
7. Bàn giao commitSHA, push thành công/thất bại, source SHA/checksum đã deploy,
   môi trường/version/publicURL, backup, kiểm thực và phần chưa kiểm. Lỗi
   mạng/SSH/Git credentials thì báo đúng bước lỗi, không nói đã deploy.

## Phạm vi quyền

- Không hỏi lại quyền commit/push/deploy từng hạng mục mà người dùng đã giao.
- Không coi quy tắc rollout là quyền đoán user được cấp admin, xóa dữ liệu
  ngoài task, mua domain/đổiDNS, mở file private hoặc chốt nghiệp vụ chưa rõ.
- Ý tưởng/thiết kế/prompt vẫn là tài liệu; không tự code module chỉ vì đã có
  ý tưởng. Phiên điều phối không tự chuyển vai trò sang code ứng dụng.
- Test18079 và DBtest được giữ; chỉ sử dụng khi người dùng yêu cầu hoặc cho
  phép về sau. Không tự thay18079 bằng DB clone/cổngtest khác để lách chỉ thị.
- Không bỏ kiểm tra cơ bản/cú pháp/ACL chỉ vì bỏ môi trườngtest. Không tuyên
  bố suite/UAT/audit đạt khi chưa chạy. Không tạo suite mới cho thay đổi tài liệu.
- Nếu chỉ sửa tài liệu: commit/push và đồng bộ tệp source trên PCserver;
  không cần restart/upgrade runtime hoặc phục hồi DB. Việc đó không chứng
  minh các chức năng mô tả trong tài liệu đã được triển khai.

## Môi trường và bảo toàn

Theo bàn giao hiện tại: local18069/`tp_tanphat_dev`; test18079 giữ nguyên;
Docker PCserver `192.168.1.73`, container `tp-odoo`, source
`C:\Projects\TANPHAT-ONE`, runtime `/workspace/docker.odoo.conf`. Kiểm lại
trước thao tác. Giữ tunnel/domain/session/config và volume filestore đúng
DB; không restore test đè main. Không restart tunnel chỉ để deploy source.

Nếu một batch khác đang triển khai: không chiếm checkpoint hoặc deploy code
dở của họ. Có thể commit riêng policy/docs không chạm application; không
`ai_workflow finish` thay batch đó. Chủ batch phải tích hợp tài liệu mới khi
chốt bàn giao, ghi rõ mốc source/runtime thực tế.
