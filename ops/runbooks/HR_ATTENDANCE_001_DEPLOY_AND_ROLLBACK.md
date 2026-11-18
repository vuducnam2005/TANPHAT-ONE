# Giao bản chấm công, nâng cấp và hoàn nguyên

Chỉ deploy source đã commit/push. Không copy working tree có foreign diff. Local dùng tp_tanphat_dev/18069/PG55432; PC server dùng C:\Projects\TANPHAT-ONE, tp-odoo/tp-postgres, /workspace/docker.odoo.conf và bind docker_data\filestore → /var/lib/odoo/filestore. Không mở18079, không import lại nguồn hoặc seed người/công để kiểm tra UI.

1. Đóng gói `git archive <SHA> custom_addons/tp_hr_attendance` dạng LF. Manifest private ghi commit, version, SHA256 của toàn bộ addon ở baseline đã áp và release mới. Hash chuẩn hóa CRLF→LF; kiểm không có file mới ngoài scope.
2. Chép archive/manifest vào `.local/hr-attendance001/<label>-release.tar.gz` và `<label>-manifest.json` trên server. Giao script [deploy-hr-attendance.ps1](deploy-hr-attendance.ps1) đúng commit, chạy `powershell -File ... -Label s3` (hoặc s4).
3. Script từ chối trước mutation nếu file hiện tại lệch baseline hoặc file mới đã tồn tại. Dừng đúng container, backup dump và pg_restore-list, filestore, source/config, checksum rồi giải nén, kiểm hash release. Dùng **-u tp_hr_attendance**, không -i; container nâng cấp tạm cùng image/network/filestore. Cuối cùng khởi động tp-odoo, không restart tunnel. Lỗi upgrade phải kiểm log và hoàn nguyên trước khi nghiệm thu.
4. Local cũng backup dump/filestore/source/config và kiểm restore-list trước `-u`, dừng process sở hữu đúng18069 rồi khởi động lại. Không dùng fixture suite trên DB đang dùng.
5. Kiểm version, source hash, roster/user/phòng/nhóm/nguồn công/baseURL trước-sau. Public: anonymous về đăng nhập, đăng nhập hợp lệ, mở màn vừa giao, avatar và bundle, console/5xx. Chỉ đọc/mở/hủy form, không phân công, gửi/duyệt/chốt thật để smoke.

Hoàn nguyên: dừng tp-odoo, khôi phục source/config từ backup đúng môi trường và dùng -u bản trước nếu schema tương thích; kiểm log rồi khởi động. Nếu cần rollback schema/dữ liệu đầy đủ, dùng dump **cùng server và cùng backup** với filestore của nó trong thời gian bảo trì; không restore local/test đè server. Giữ bằng chứng trước khi hoàn nguyên. Chưa diễn tập restore đầy đủ trong batch này.

S4 `20.0.1.2.0` dùng baseline S3 `14eaf388` cho toàn bộ addon. Ngoài dashboard/CSV,
có field groups liên hệ và restriction `ir.access` cho hồ sơ cá nhân của native20;
build này không có model `ir.rule`. Backup đúng DB/filestore/config trước nâng cấp.
Kiểm sau áp: proxy export employee bị chặn với non-HR, field metadata/đọc/domain/order
liên hệ riêng bị từ chối, work-phone/avatar/self-profile vẫn hoạt động; source công
và roster không đổi. Không coi ca resume trống hoặc bộ test không DB là bằng chứng
tải certificate với hồ sơ thật; không tạo chứng từ giả trênmain để lấp ca này.

## SIMPLE-002 `20.0.2.0.0` (`CHG-20261118-019`)

Release cùng quy trình trên, label `has002`, script/manifest private trong `.local/hr-attendance-simple002/`.
Khác S4: release **xóa** 3 file `board.scss`/`dashboard.scss`/`mine.scss` (manifest liệt kê asset tường minh,
xóa để source khớp commit) và thêm `data/`, model `late/logic/overview/source`, `upload/`, `sources.*`.
`-u tp_hr_attendance` tạo bảng `tp_hr_attendance_late/_source/_source_code/_event` và tham số
`tp_hr_attendance.reference_hours` (`noupdate`); không migration dữ liệu cũ, không đụng session/day/
correction/period. Kiểm sau áp: version, đếm session/day/late/event/source/batch, roster/user/nhóm/base URL
trước-sau; public: Tổng quan/Bảng chấm công/Nguồn dữ liệu mở được, API *Chưa cấu hình*, 0 lỗi console/5xx.

**Không** nhập Excel thật trên server khi deploy; HR tự nhập qua nút *Nhập Excel máy chấm công* (xem trước
rồi mới ghi). Hoàn nguyên code: khôi phục `source-config.tar.gz` của đúng backup rồi `-u tp_hr_attendance`;
4 bảng mới để lại, bản cũ không đọc tới (chưa diễn tập). Hoàn nguyên đầy đủ dùng dump + filestore cùng backup.

## MATRIX-003 `20.0.3.0.0` (`CHG-20261118-029` / `030`)

Release theo quy trình `git archive <SHA> custom_addons/tp_hr_attendance` (giữ `mtime` theo commit trên mỗi tệp để Odoo tạo lại hash asset), label `ham003`, code commit `b7765bd1`, nâng cấp `20.0.2.0.0 → 20.0.3.0.0`.
- Backup local `.local/hr-attendance-matrix003/backup-ham003-20261118-163916` (`tp_tanphat_dev.dump` `10.049.947`B, `restore-list.txt` `15.600` mục, `filestore.zip` `294.237.435`B/`1.027` tệp, `SHA256SUMS.txt`).
- Backup PC server `C:\TANPHAT-backups\hr-attendance-matrix003\ham003-20261118T171946` (`tp_tanphat_dev.dump` `9.701.510`B/`15.600` mục, `filestore.tar.gz` `34.387.973`B, `source-config.tar.gz` `257.100`B, `SHA256SUMS.json`).
- `-u tp_hr_attendance` chạy migration idempotent `migrations/20.0.3.0.0/post-migrate.py` (`_tp_migrate_matrix_003`): tạo 3 bảng `tp_hr_attendance_snapshot_person`, `tp_hr_attendance_snapshot_cell`, `tp_hr_attendance_resolution`, cấp `batch_code` (`LÔ-xxxxx`) và dựng snapshot từ `file_data` đính kèm, gắn provenance đa lô cho các session/late hiện có mà **không** nhập lại công, không tạo/sửa `hr.employee`, giữ nguyên 100% số liệu hiệu lực, kỳ chốt và điều chỉnh đã duyệt.
- Không nhập Excel giả/thật để test trên DB chính/server; sau deploy kiểm version, bảng snapshot, counts `session`/`day`/`late`/`employee`/`users`/`web.base.url`, tải trực tiếp HTTP assets `web.assets_backend` qua `https://hybrid-send-ready-ballot.trycloudflare.com`, `/web/health`, và Playwright ẩn danh `0` lỗi console/5xx.
- Hoàn nguyên: dừng `tp-odoo`, khôi phục `source-config` từ backup đúng môi trường rồi `-u tp_hr_attendance` (hoặc khôi phục đầy đủ dump + filestore cùng backup trong khung bảo trì).

### Sửa cờ snapshot `CHG-20261118-036` (không đổi version)

- Chỉ đổi Python `models/attendance_matrix.py` (và test). Không đổi schema hay version `20.0.3.0.0`, nên giao bằng cách chép tệp vào checkout và khởi động lại `tp-odoo`; không cần `-u tp_hr_attendance`.
- Trước khi giao: backup DB + filestore + nguồn như các bản trước; kiểm `SELECT snapshot_state, snapshot_version, count(*) FROM tp_hr_attendance_batch GROUP BY 1,2` và số lô có snapshot nhưng chưa `ready`.
- Sau khi giao: health 200, log không ERROR, URL public mở được. Lô nào có snapshot mà còn `pending` sẽ tự về `ready` ở lần mở ma trận, đối chiếu hoặc xuất đầu tiên; không cần sửa DB tay.
- Hoàn nguyên: khôi phục `models/attendance_matrix.py` từ `source-config.tar.gz` của backup rồi khởi động lại `tp-odoo`. Cờ `ready` đã ghi là đúng với dữ liệu nên giữ nguyên.
