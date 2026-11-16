# HR-EMP-014 — Triển khai và rollback

Phạm vi `tp_hr_workspace` 20.0.1.10.2 → 20.0.1.11.0. Chỉ `tp_tanphat_dev`
(18069) và `tp_tanphat_test` (18079), cluster workspace55432. Không tạo DB,
không restore test đè main, không seed giả lên main, không commit/push.

## Gate trước khi áp

1. Giữ checkpoint workflow và các thay đổi có sẵn; source HR trước task ở
   `.local/hr-emp014/rollback-source.zip` và manifest SHA25663 file.
2. Backup test; backup mainA gồm DB/filestore/config/source, kiểm dump TOC,
   referenced blobs/hash và sequence. Dừng test đúng config, zero session rồi
   restore mainA vào canonical test; kiểm rowsets/blobs/sequences chính xác,
   neutralize trước HTTP. Helper restore lịch sử chỉ cho phép bảng/sequence
   thừa đã review; nếu test đã có schema014 thì phải dừng để review đúng schema,
   không bypass assert hoặc drop cascade tùy ý.
3. Upgrade HR trên bản sao main, kiểm Odoo/HOOT/browser/Excel, quyền HR/KH-KD,
   version/date/file/delete preview, responsive/keyboard/reduced motion. Chỉ
   fixture giả trên test. Giữ các log fail và kết quả chạy lại riêng.
4. Seal application source sau test. Dừng dev đúng config/PID, kiểm không còn
   listener/orphan hoặc DB session. Trong một script fail-fast: snapshot hash
   mọi bảng/cột cũ, backup mainB cuối, rồi `-u tp_hr_workspace --no-http
   --stop-after-init`. Mọi gate fail phải dừng trước lệnh phụ thuộc.
5. Trước mở HTTP, so toàn bộ cột cũ; business/auth/roles/groups/mappings/source
   giữ, policy ACL cũ giữ (write_date metadata có thể đổi), chỉ hai ACL mới
   đã nêu. Kiểm referenced nonasset blobs giữ, new contract table rỗng và các
   field classification/link đều NULL. Kiểm không có fixtureEMP014 trên main.
6. Start dev, smoke chỉ đọc/mở/Hủy/export; kiểm lại business/auth/blob và source
   seal, mở ảnh để tự đánh giá. Login/bus/presence có thể tạo metadata vận hành,
   phải phân loại delta thực tế, không gọi toàn DB bất biến.

Lệnh nâng cấp nằm sau các guard trong script triển khai private:

```powershell
.\.venv\Scripts\python.exe -X utf8 odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_hr_workspace --no-http --stop-after-init
```

## Rollback

Schema mới có bảng giấy tờ, cột version, ACL/view và audit selection. Trả source
đơn thuần không đủ. Không hạ version module rồi tuyên bố rollback đã xong.

1. Dừng thao tác, backup main hiện tại và giữ toàn bộ giấy tờ/tệp/audit mới.
   Đánh giá giao dịch kể từ mainB và xác định phương án bảo toàn chúng trước
   khi phục hồi. Không tự chạy restore main chỉ vì có backup.
2. Đối chiếu `source-scope.json` với zip/hash trước task. Chỉ trả đúng file
   đã thay của014, gỡ đúng file mới014; giữ mọi thay đổi các task trước. Không
   git reset/checkout cả addon, không đụng core hoặc `.git`.
3. Phục hồi **DB và filestore mainB của main** theo runbook backup/restore và
   thẩm quyền vận hành hiện hành, sau đánh giá giao dịch; không dùng bản test.
   Bản backup source cùngB chứa source014, nên source rollback phải lấy zip
   HR trước task, không mặc định giải nén sourceB là bản cũ.
4. Kiểm version cũ/schema/view/ACL/business/auth/blob và restart đúng config;
   smoke list/profile/account/delete preview bằng đọc/Hủy. Ghi handoff rollback
   riêng, không xóa bằng chứng014.

Kết quả restore/apply thực và backupB chính xác được ghi ở
[acceptance](../../docs/demo/HR_EMP_014_ACCEPTANCE.md). Chưa diễn tập rollback
main sau khi có giao dịch014; không coi restore mainA→test là nghiệm thu nghiệp vụ.

## Thực chạy — 13/11/2026

- MainA064107775807Z restore test exact600tables/666refs/432sequences, neutralize.
- **Rollback toàn task:** `backup-tp_tanphat_dev-20261113T073121361307Z`
  (mainB trước schema014). Backup073223659391Z chứa schema014; correction cuối
  có `backup-tp_tanphat_dev-20261113T074320617876Z`601tables/666refs. Giữ cả ba.
- Source cuối67file,17modified+4new so63file snapshot trước task. Không gỡ file
  các task cũ. Bản sửa cuối gồm copy/link version và mobile accountbadge.
- Upgrade cuối `upgrade-main-corrected.log`, zeroDBsessions trước/sau/noHTTP;
  gates phát hiện orphan/probe chồng dừng; lần so archive trước correction phải
  dùng cả delta operational từ smoke trước, không giả định baseline mới làB.
- So originalcolumns từ archiveB600bảng (COPY ONLY cho bảng kế thừa), business,
  password/auth/role/company/mapping và632nonassetblob giữ. Main0paper/newfieldsNULL,
 0EMP014fixture; smoke6/6 chỉđọc/Hủy/export,577rowsetsnguyên/23metadata-operationaldelta.
  Hai runtime đang chạy; workflowCHG005. [Acceptance](../../docs/demo/HR_EMP_014_ACCEPTANCE.md)
  ghi logfail/rerun/ảnh và các giới hạn. Chưa thực hiện rollback main.
