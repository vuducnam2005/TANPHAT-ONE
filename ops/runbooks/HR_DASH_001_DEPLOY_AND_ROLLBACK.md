# HR-DASH-001 — triển khai và phục hồi

CHG-20261111-010. Phạm vi: tp_web_login20.0.1.2.0 và
tp_hr_workspace20.0.1.1.0; main18069/test18079, PostgreSQL55432.
Không commit/push. Không reset tài khoản hoặc seed main.

## Bản sao lưu và nguồn phục hồi

Bộ snapshot main trước nâng cấp:
.local/hr001/backup-tp_tanphat_dev-20261111T092100242854Z.
Chứa database.dump, filestore, source.zip, private/config,
manifest SHA256, rowset fingerprint và sequence inventory.
File bí mật và dữ liệu nhân viên chỉ nằm ở .local ngoài Git.

Rollback source theo task:
.local/hr-dash001/rollback-source.zip, metadata rollback-source.json.
Bản gốc các file sửa được đối chiếu hash với checkpoint CHG-20261111-009.
Source.zip trong snapshot DB được tạo khi code mới đã có trong workspace;
**dùng rollback-source.zip cho phiên bản source trước task**, không lấy
source mới trong snapshot DB làm bản cũ.

## Trình tự đã chọn

1. Dừng test đúng PID/config, sao lưu test.
2. Backup main; restore **chỉ vào database test chuẩn**.
3. Đối chiếu tất cả595rowsets/636blob references/428sequences trước neutralize.
4. Neutralize test UUID/baseURL/cron/mail; SMTP127.0.0.1:9.
5. Upgrade2module và test Odoo; HOOT/browser/Excel; tài khoản giả chỉ test.
6. Dừng main, backup cuối, kiểm restore snapshot cuối trên test và upgrade lại.
7. Áp đúng source đã kiểm lên main bằng upgrade2module; mở main;
   smoke chỉ đọc và đối chiếu roster/quyền/các bảng nghiệp vụ/blob không phải assets.
8. Test cuối ở trạng thái sạch theo main đã sao lưu, không giữ fixture giả.

Upgrade test dùng .local/test/odoo.conf, database tp_tanphat_test,
-u tp_web_login,tp_hr_workspace --test-enable --test-tags /tp_hr_workspace,/tp_web_login
--stop-after-init. Main dùng .local/odoo.conf, tp_tanphat_dev, cùng2module,
--no-http --stop-after-init. Không chạy tests/fixtures trên main.

## Lưu ý restore schema cũ

Restore đầu đã dừng an toàn vì FK mới
tp_hr_account_wizard_expected_user_id_fkey trong test không có trong dump
schema cũ. Đã đối chiếu đúng bảng nguồn/đích/định nghĩa, chỉ gỡ FK này trên
test đã backup, rồi restore lại. Không DROP CASCADE, không chạm main.
Helper private dùng transaction-size25. Evidence cuối ở
.local/hr001/restore-evidence.json; lần restore fail không được xem là đạt.
Windows có thể giữ socket sau terminate; chỉ chạy lại HTTP tests khi cổng
được giải phóng, không đổi sang database/cổng ngoài quy ước.

## Khi cần rollback

Chặn người dùng thao tác; dừng đúng main runtime, sao lưu trạng thái hiện tại.
Khôi phục **chỉ file của task** theo rollback-source.json; giữ các thay đổi
khác có sẵn. Gỡ các file mới trong manifest đúng danh sách sau khi kiểm path.
Upgrade cùng2module để trả view/assets về bản cũ. Cột DB mới có thể giữ nguyên
nếu không được code cũ dùng; không xóa dữ liệu nhân viên.

Nếu cần phục hồi dữ liệu, ưu tiên restore snapshot vào test kiểm chứng trước;
phục hồi main là thao tác riêng khi xác định phạm vi dữ liệu phát sinh sau
snapshot. Không tự restore test đè main. Người dùng đổi khóa/mở sau rollout
cần được bảo toàn hoặc đối chiếu khi rollback.

Evidence riêng tư .local/hr-dash001/: logs Odoo, tested-source,
main-preservation, UI screenshots/XLSX, HOOT và lock-e2e result.

## HR-DASH-002 — static assets, CHG-20261112-001

Không thay Python/model/manifest/data view hoặc schema. Sau test18079,
sao lưu cuối main tại
`.local/hr001/backup-tp_tanphat_dev-20261112T014402981715Z`,595bảng/
636blobrefs/checksum/dump/config/source/filestore. Áp đúng static source đã
seal bằng runtime main khởi động lại; không cần module upgrade, migration
hoặc restore. Không chạy helper setup/seed/restore chỉ để refresh assets.

Main được terminal khác mở08:44:46 ngày12/11; start guard từ chối listener
thứ hai. Đã kiểm commandline/config/workspace/PID và browser; không giả định
độc quyền. Dừng runtime Windows phải kiểm cả venv parent và Python child
đều là Odoo cùng workspace/config, không dừng mọi Python hoặc PostgreSQL.

Rollback **chỉ file của HR-DASH-002** theo
`.local/hr-dash002/rollback-source.json` và zip cùng tên. Bản này lấy từ
snapshot trước sửa100554262290Z; source.zip trong snapshot cuối chứa bản
mới đã test. Giữ các thay đổi có trước task trong dirty worktree.
Sau khôi phục source, restart đúng main; kiểm compile assets, dashboard,
list/profile và population. Không restore test đè main, không cần trả DB
về trước chỉ vì đổi giao diện. Nếu có lỗi dữ liệu khác, giữ hiện trạng và
đánh giá restore riêng theo runbook chuẩn.

Main sau smoke giữ79bảng/612nonassetblob, ACL/rule/company/implied-group;
seal15file HR gồmSCSS khớp. Snapshot mọi595rowsets chỉ đổi6bảng kỹ thuật
assets/bus/presence/device/login/transient wizard. Evidence `.local/hr-dash002/`.


## HR-DASH-002 — phản hồi sidebar, CHG-20261112-002

Static-only: sidebar SCSS palette navy Kinh doanh + JS mapping icon `group`.
Test18079 đạt rồi backup main
`.local/hr001/backup-tp_tanphat_dev-20261112T020356030758Z`
(595bảng/638blobrefs/checksum), restart đúng parent/child theo config và
smoke18069 đạt. Không upgrade/migration/restore. Dashboard giữ sáng.
Rollback riêng thay đổi002 lấy3file trong
`.local/hr-sidebar002/rollback-source/`, gồm sidebar.scss/sidebar.js và
scripts/hr_dash002_checks.cjs; sau đó restart đúng runtime, kiểm màu/icon,
nav và dashboard. Không dùng rollback toàn HR-DASH-002 CHG001 để trả riêng
sidebar. Seal/preservation/ảnh ở `.local/hr-sidebar002/`;79bảng nghiệp vụ/
quyền và612nonassetblob giữ,5bảng kỹ thuật đổi do assets/login/presence.
