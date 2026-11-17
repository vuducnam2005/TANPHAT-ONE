# Giao bản chấm công, nâng cấp và hoàn nguyên

Chỉ deploy source đã commit/push. Không copy working tree có foreign diff. Local dùng tp_tanphat_dev/18069/PG55432; PC server dùng C:\Projects\TANPHAT-ONE, tp-odoo/tp-postgres, /workspace/docker.odoo.conf và bind docker_data\filestore → /var/lib/odoo/filestore. Không mở18079, không import lại nguồn hoặc seed người/công để kiểm tra UI.

1. Đóng gói `git archive <SHA> custom_addons/tp_hr_attendance` dạng LF. Manifest private ghi commit, version, SHA256 của toàn bộ addon ở baseline đã áp và release mới. Hash chuẩn hóa CRLF→LF; kiểm không có file mới ngoài scope.
2. Chép archive/manifest vào `.local/hr-attendance001/<label>-release.tar.gz` và `<label>-manifest.json` trên server. Giao script [deploy-hr-attendance.ps1](deploy-hr-attendance.ps1) đúng commit, chạy `powershell -File ... -Label s3` (hoặc s4).
3. Script từ chối trước mutation nếu file hiện tại lệch baseline hoặc file mới đã tồn tại. Dừng đúng container, backup dump và pg_restore-list, filestore, source/config, checksum rồi giải nén, kiểm hash release. Dùng **-u tp_hr_attendance**, không -i; container nâng cấp tạm cùng image/network/filestore. Cuối cùng khởi động tp-odoo, không restart tunnel. Lỗi upgrade phải kiểm log và hoàn nguyên trước khi nghiệm thu.
4. Local cũng backup dump/filestore/source/config và kiểm restore-list trước `-u`, dừng process sở hữu đúng18069 rồi khởi động lại. Không dùng fixture suite trên DB đang dùng.
5. Kiểm version, source hash, roster/user/phòng/nhóm/nguồn công/baseURL trước-sau. Public: anonymous về đăng nhập, đăng nhập hợp lệ, mở màn vừa giao, avatar và bundle, console/5xx. Chỉ đọc/mở/hủy form, không phân công, gửi/duyệt/chốt thật để smoke.

Hoàn nguyên: dừng tp-odoo, khôi phục source/config từ backup đúng môi trường và dùng -u bản trước nếu schema tương thích; kiểm log rồi khởi động. Nếu cần rollback schema/dữ liệu đầy đủ, dùng dump **cùng server và cùng backup** với filestore của nó trong thời gian bảo trì; không restore local/test đè server. Giữ bằng chứng trước khi hoàn nguyên. Chưa diễn tập restore đầy đủ trong batch này.
