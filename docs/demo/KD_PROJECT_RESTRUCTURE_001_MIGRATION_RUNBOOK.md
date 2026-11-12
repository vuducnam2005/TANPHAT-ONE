# KD-PROJECT-RESTRUCTURE-001 — Migration và rollback

09/11/2026. Runbook cho người vận hành; source20.0.1.8.0 đã áp dev18069, source test=seal=applied89c17f…f927.
Không chạy ví dụ này trên dev khi chưa đủ cổng trong [acceptance](KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md).
Không chứa credential/dump/danh tính người thật. Không duyệt V2 hoặc bàn giao owner.

## Dữ liệu hiện có và phần chưa xác minh

Inventory đọc14project managed và25CRM tại [mapping-dry-run](<C:/TANPHAT ONE/.local/kd-project-restructure001/mapping-dry-run.json>).
Dự án giữ project.project ID, partner_id thương mại và mọi link hiện có. Không có
căn cứ được duyệt để suy investor, chia gói, đoán thắng thầu hoặc giá cả gói từ
expected_revenue; những field này giữ NULL/Chưa xác định. Schema mới chỉ mặc định
tracking=Đang theo dõi, không suy đang thực hiện/kết thúc. Không tạo gói giả cho direct.

Owner/reviewer audit chỉ đọc: project14/14owner legacy; CRM24/25owner chưa thuộc
mapping5actor; allocation18,production25,acceptance17,payment21,plan18 đều có
owner/reviewer legacy. Legacy có nghĩa chưa map vào5actor hiện tại, không kết luận
account vô hiệu. Danh sách exact ID private ở [owner-reconciliation](<C:/TANPHAT ONE/.local/kd-project-restructure001/owner-reconciliation.json>).
Giữ nguyên; chủ nghiệp vụ phải xác minh từng hồ sơ và thẩm quyền bàn giao trước delta.

## Mapping có căn cứ

Utility `custom_addons/tp_kd_workspace/migration_mapping.py` chỉ là hàm operator,
không đăng ký RPC/public action. Mỗi row đủ5key:

```python
{"lead_id": existing_lead_id, "project_id": existing_project_id,
 "package_id": existing_package_id_or_False,
 "source": "tham chiếu bằng chứng", "verified_by": "người xác minh"}
```

Dùng ID Odoo, không dùng tên làm khóa. Chỉ project managed cùng company, cùng bên ký
commercial partner đã xác minh. Lead thiếu partner phải đối chiếu; không tự lấy
partner từ project. Gói optional phải thuộc project, chỉ nhánh bid mới nối gói.
Không thay link đã có sang project/gói khác. Phân công/quyền không tự tăng khi mapping.

1. Lưu nguồn/mapping được duyệt riêng; snapshot DB/filestore/source/config mới.
2. Trong transaction ORM operator được kiểm soát, gọi apply_mapping(env,rows,dry_run=True).
   Xem từng delta và lỗi; dry-run không ghi/journal. Rollback transaction kiểm kê.
3. Khi được phép áp dữ liệu đó, bắt đầu transaction mới, dry-run lại rồi
   apply_mapping(env,rows,dry_run=False,journal=journal). Hàm khóa lead/revalidate,
   ghi qua ORM. Persist journal private sau commit thành công cùng mã batch.
4. Chạy lại cùng mapping phải không có delta/journal mới. Đối chiếu chỉ các field
   tp_project_id/kd_package_id; không đổi company,owner,reviewer,state,file,grant.
5. Rollback dữ liệu: rollback_mapping(env,journal) trong transaction operator mới.
   Chỉ hoàn lại field delta nếu còn bằng after; đã rollback thì no-op, có writer
   khác thì từ chối để đối chiếu. Không restore cả DB đè nghiệp vụ phát sinh.

Odoo tests dùng mapping không rỗng kiểm apply2lần/journal1/rollback2lần, direct
project-only không gói giả và missing partner từ chối cả dry-run/apply. Đây là
fixture; không chứng minh25CRM doanh nghiệp đã được mapping.

## Source và rollback triển khai

Nguồn test tại `.local/kd-project-restructure001/workspace/custom_addons`;
`source-seal.json` chứa SHA256 cả cây, `source-delta-files.json` liệt kê58file,
`source-delta.zip`/`source-delta.patch` đóng gói delta. Static chỉ chạy
`git apply --check --whitespace=error`; delta58file đã copy/verify theo seal lên root. Dùng digest mới nhất
trong acceptance; mọi sửa source sau test làm cổng exact source phải chạy lại.

Backup rehearsal `backup-pre-apply-20261109T131132Z`:122file manifest hash,
578table/295attachment references, restore verified DB owned
`tp_tanphat_kdreport001_backup_131138` (tên kế thừa helper, ownership của task này).
Snapshot trước apply thực cần mới và kiểm writer/source/config, không dùng rehearsal
cũ thay gate. Không đưa dump/filestore/private config vào Git.

Nếu gate đạt và triển khai: chụp preservation trước; kiểm root source vẫn baseline,
chỉ copy delta addon đã seal, upgrade riêng tp_kd_workspace, restart đúng Odoo18069.
Không seed fixture/password hoặc cấp quyền. Đối chiếu source applied=seal, module
version và preservation account/auth/grant/assignment/business/file/config; smoke
5login chỉ đọc. Giữ PG55432 và các runtime khác.

Nếu lỗi: giữ evidence/backup và dừng apply; phục hồi source delta từ maintained-source.zip
đã kiểm, upgrade đúng addon theo bản tương thích. Schema additive không tự drop bảng
mới hoặc xoá nhật ký. Mapping dùng journal như trên. Full DB restore chỉ theo kế hoạch
incident có đánh giá writer mới, không tự đè dev. Apply thực đã đạt, chưa cần rollback dev.83table/4529oldrow giữ,295attachment hash/size đúng; model mới0businessrow, không mapping thật. Source rollback phải giữ các thay đổi sau apply của writer khác nếu có.
