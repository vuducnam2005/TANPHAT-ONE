# HR-UI-011 — Triển khai và khôi phục

Phạm vi: `tp_hr_workspace` 20.0.1.9.0 → 20.0.1.10.0. Giữ bản HR-DELETE-010
và UI-HOME-005 có sẵn. Chỉ hai DB canonical trên cluster 55432; không commit/push.
Không restore test sang main; không tạo DB thứ ba. Một tác vụ ghi trên test.

## Kiểm và áp dụng

1. Dừng đúng test bằng `.local/identity-org001/runtime.ps1 stop test`.
   Upgrade/test `tp_organization,tp_hr_workspace` theo runbook HR-DELETE-010
   (`--test-tags /tp_organization,/tp_hr_workspace --stop-after-init`).
   Với upgrade thuần dùng `--no-http`; HTTP test có thể cần listener test.
2. Mở test, kiểm HOOT HR/Home, browser theo acceptance; lưu ảnh, report và
   backup test trước diễn tập vào `.local`, giữ kín session/credential.
3. Dừng dev, backup main bằng `.local/hr001/ops.py backup tp_tanphat_dev`:
   database.dump, filestore tham chiếu/SHA, source/config, rowsets, sequence.
   Dừng test rồi `ops.py restore-test <backup-main>`; helper sao lưu test trước
   khi thay và xác nhận khớp mọi rowset/blob/sequence. Chạy
   `.local/hr001/neutralize_test.py` trước khi mở HTTP.
4. Lưu snapshot test sau neutralize, upgrade addon HR trên bản sao main; kiểm
   view/count/security/regression. Test thật dùng fixture trong transaction,
   không đưa fixture HTTP mới sang main. Đối chiếu các bảng nghiệp vụ, account,
   password hash, role/grant, mapping, mã TP và blob không thuộc assets.
5. Backup main lần cuối ngay trước áp dụng. Giữ main dừng trong giai đoạn này.
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace --no-http --stop-after-init
   ```
   Đối chiếu business/security rowsets trước khi mở HTTP, start dev; smoke chỉ
   đọc/mở chi tiết/Hủy. Không nhập mật khẩu xác minh, không xóa/khóa/đổi quyền
   hoặc save dữ liệu thật. Kiểm thêm 0 fixture `UI011` trên main.

## Rollback đúng task

Rollback source gốc: `.local/hr-ui011/rollback-source.zip` +
`rollback-source.json` (56 file trước task, gồm cả HR-DELETE-010 đã có).
`source-scope.json` chỉ rõ file thay đổi/thêm và hash bản đã kiểm.
Không dùng git reset/checkout cả addon vì worktree ban đầu đã dirty.

1. Backup main hiện tại; dừng đúng dev. Kiểm SHA256 zip từng entry trước sửa.
2. Trả **11 file application/test đã sửa** theo `source-scope.json` về đúng
   nội dung trong zip. README/tài liệu giữ lịch sử, cập nhật mục rollback riêng.
3. Gỡ đúng 7 file mới trong scope: `models/hr_ui.py`,
   `views/hr_ui.xml`, `tests/test_hr_ui.py`, `static/src/table/table.scss`,
   `static/src/profile/hr_ui.scss`, `static/src/hierarchy/hierarchy.js|.xml`.
   Không đụng các file delete/account/organization/home từ task trước.
4. Upgrade lại `tp_hr_workspace` 20.0.1.9.0. Vì bản cũ không ghi lại các binding
   view/action mới, chỉ trả source rồi upgrade **chưa đủ** để rollback UI an
   toàn. Dùng **backup main cuối ngay trước HR-UI-011** để phục hồi DB+filestore
   theo runbook backup/restore, sau khi đánh giá mọi giao dịch phát sinh sau đó.
   Không restore backup test. Giữ backup, audit và bằng chứng triển khai.
5. Start dev, Ctrl+F5; kiểm menu/action, HR-DELETE-010 và tài khoản chỉ đọc/Hủy.

Không có thay đổi stored business field hoặc migration dữ liệu. Các count mới
không lưu; metadata view/action/menu mới vẫn cần phục hồi khi rollback. Kết quả
backup/diễn tập/áp thực được ghi tại [acceptance](../../docs/demo/HR_UI_011_ACCEPTANCE.md).

## Thực chạy 13/11/2026 — CHG-20261113-002

- BackupA `backup-tp_tanphat_dev-20261113T032204623692Z`600 tables/666 blob refs.
  Restore canonical test từA, backup test032901396088Z;600 rowsets/666 blob/432 sequence
  khớp, neutralize rồi77/77 tests; smoke25/25/0 errors.
- BackupB **`backup-tp_tanphat_dev-20261113T033657607572Z`**600/666 là điểm
  rollback main của task. Snapshot trước nâng cấp khớp600 rowsets củaB.
  Hai phòng mới giữaA/B được giữ; không dùng dữ liệu test để đồng bộ main.
- Runtime main mở lại ngoài start của task. Gate độc quyền đầu fail nhưng lệnh
  upgrade vẫn chạy; không coi lượt đó là chuẩn. Đã dừng đúng runtime và chạy
  lại trong **cùng shell có guard exit code và0 DB sessions**, xác nhận không có
  HTTP sau upgrade; chỉ `-u tp_hr_workspace --no-http --stop-after-init`.
  Khi vận hành lại, mọi gate thất bại phải throw/return trước lệnh phụ thuộc.
- So600 bảng:585 nguyên trướcHTTP,15 delta metadata/crontrigger/signaling;
  ACL953policy/57 group/632 nonassetblob bảo toàn. Smoke main25/25/0 errors/0 business write;
 579rowsets nguyên sau operational login/bus/presence/identity/accountwizardtạm.
  Main40 employee/28 user/9 active/15 phòng/1 HEAD,0 UI011fixture. Cả2runtime đang chạy.
- Chưa thực hiện rollback main; chỉ diễn tập phục hồi mainA→test có kiểm chứng.
  Backup và source rollback giữ tại `.local/hr001/` và `.local/hr-ui011/`.
