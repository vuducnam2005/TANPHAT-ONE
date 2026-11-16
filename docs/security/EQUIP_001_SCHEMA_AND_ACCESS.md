# EQUIP-001 — Schema và quyền truy cập

Ngày 14/11/2026. Trạng thái: `tp_equipment` **20.0.1.2.0** đã nâng cấp bằng `-u` trên main **18069** (CHG-20261114-012) và đã nhập thật hai workbook local qua importer; dashboard, danh sách, chi tiết, đề xuất, đợt nhập desktop/mobile đã được quan sát có dữ liệu. Tài liệu mô tả guard trong source, không là kết quả kiểm thử hay nghiệm thu.

Cập nhật 16/11/2026 (`CHG-20261116-003`, EQUIP-SIMPLE-003 / DEC-047, `tp_equipment` **20.0.1.5.0** qua `-u` trên main 18069): thêm TransientModel `tp.equipment.quick.action`, hai field idempotency trên `tp.equipment.move`, các field tính toán hiển thị trên `maintenance.equipment` và một dòng ACL. Không đổi quyền nhóm, membership hay dữ liệu HR; không thêm bảng nghiệp vụ lưu lâu dài ngoài hai cột mới (NULL với phiếu cũ).

## Kiến trúc và dữ liệu

Addon `tp_equipment` dùng database Odoo chung `tp_tanphat_dev`, cùng `hr.employee`, `hr.department`, `res.partner`. Không tạo HR/database thứ hai; không dùng Excel làm nguồn runtime. Dependency gồm `maintenance`, `hr`, `mail`, `tp_web_home`, `tp_hr_workspace`; không phụ thuộc `hr_maintenance` vì cầu nối upstream có thể implied quyền Maintenance cho HR.

| Model | Vai trò và trạng thái chính |
| --- | --- |
| `maintenance.equipment` | Hồ sơ gốc, mã `tp_code`, serial, sở hữu, kỹ thuật, nguồn và phiên bản; vòng đời `draft/active/retired` |
| `maintenance.request` | Sửa/bảo trì/nâng cấp, tiến trình `new/in_progress/vendor/done/cancel`, kết quả và kỹ thuật sau xử lý |
| `tp.equipment.move` + `.line` | Custody và audit trước/sau; `draft/pending/done/cancel`; phiếu đảo liên kết phiếu gốc |
| `tp.equipment.receipt` + `.line` | Tiếp nhận từng thiết bị; liên kết dòng đề xuất, không nhận vượt/lặp |
| `tp.equipment.proposal` + `.line` | Rà soát `draft/review/returned/reviewed/cancel`; kết quả ngoài `unverified/approved/partial/rejected`; tiến độ suy từ hồ sơ thực hiện; `date_known` phân biệt ngày có trên chứng từ với ngày ghi hệ thống |
| `tp.equipment.inventory` + `.line` | `draft/counting/closed/cancel`; snapshot và thực tế độc lập, thiếu/thừa/chưa đếm tách riêng |
| `tp.equipment.location`, `.software`, `.meter` | Vị trí, khai báo phần mềm/chứng cứ và chỉ số có ngày/đơn vị |
| `tp.equipment.import.batch` + `.line` + `.column` + `.alias` | Nguồn XLSX được làm sạch, mapping có xác nhận, đợt `draft/preview/partial/applied` (`partial` = đã áp dòng đủ thông tin, còn dòng chờ) |
| `tp.equipment.quick.action` (Transient) | Popup Gán / Đổi máy / Trả về kho: `mode` assign/swap/return, `employee_id`, `assign_equipment_ids` / `return_equipment_ids` / `old_equipment_id` / `new_equipment_id`, lý do trả kho `swap/leave/other`, ghi chú, `confirm_unverified`, `expected_versions`, `request_key`; chỉ thu thập lựa chọn, không ghi custody |
| `tp.equipment.dashboard` | Abstract model; thống kê và drill-down trên domain backend, không bảng snapshot giả |

Sở hữu `company/rented/personal/third_party/unknown`, loại quản lý `device/component/service`, custody, kỹ thuật và khả dụng là các chiều riêng. Phần mềm là khai báo, không chứng minh license. Giá/ngày chưa rõ không được suy thành giá 0/ngày giả. `tp_purchase_value_known`, receipt `purchase_value_known`, proposal `estimate_amount_known` và `amount_total_known` giữ khác nhau giữa chưa biết với 0 đã xác nhận. Người nhận không cần tài khoản Odoo; thay đổi phòng HR không tự chuyển thiết bị vật lý.

## Ma trận truy cập và guard

Chỉ user internal active thuộc `base.group_system` được quản lý trong company cho phép; không cấp nhóm thay thế cho HR/HEAD/technician/staff/native Equipment Manager. Menu/thẻ không thay backend authorization. Source có `check_admin`, ACL/domain restriction, guard native CRUD/action/search/report và các model custom; theo dõi mail/files/activities cùng phạm vi. Người nhận/kỹ thuật/người duyệt thực tế là metadata, không tự được cấp role hay subscribe.

Native Maintenance được áp policy admin-only trong scope addon này; không mặc định coi native Maintenance còn phục vụ người ngoài admin. Cần xem ảnh hưởng vận hành này khi rollout. Không đổi login/credential hoặc cấp system admin cho người nhận thiết bị.

`company_scope.py` bổ sung constraint quan hệ cùng company cho thiết bị, move/receipt/proposal và dòng, software/meter; target có company trống là dùng chung, source phải trong company được phép. Có nhiều company được bật không cho phép liên kết chéo company. Giao dịch dùng lock, phiên bản và idempotency; pending giữ chỗ; hoàn tất ghi phiếu/custody/audit trong transaction. Phiếu đã ghi không sửa lùi; đảo/điều chỉnh cần lý do, liên kết và kiểm thay đổi sau đó. Đã sử dụng không xóa vật lý. Kiểm kê chốt kết quả không ghi đè giao dịch sau snapshot; điều chỉnh qua wizard/phiếu riêng. Hoàn tất rà soát đề xuất không tương đương duyệt chi; bước thực hiện cần căn cứ duyệt và dòng được phép. Không tạo PO, bill, thanh toán, khấu hao hay chữ ký pháp lý.

QR dùng token và route xác thực; không public PII/IP/giá. PDF là biểu nội bộ có chỗ xác nhận, không giả chữ ký. Excel/report kiểm admin/company và domain; đầu vào text tránh formula injection. Không gửi mail ngoài, gọi NCC hoặc quét mạng tự động.

**Gán / Đổi máy / Trả về kho (CHG-20261116-003).** Xác nhận popup gọi một RPC `maintenance.equipment.tp_quick_action(payload)`: `check_admin`, chuẩn hóa payload (mode, `request_key` `^[0-9a-f]{16,64}$`, danh sách ID nguyên dương, phiên bản, lý do, ghi chú), khóa máy `lock_records` (theo id, `FOR UPDATE NOWAIT`), kiểm lại company, người nhận đang làm việc, nơi giữ/người giữ hiện tại, phiên bản, phiếu chờ và xác nhận máy chưa xác minh, rồi tạo và `action_done` phiếu `tp.equipment.move` sẵn có (return/loan_return trước, assign sau) trong cùng transaction. Máy gán/thay thế phải thỏa `free_domain`: `tp_custody = stock` **và** `tp_employee_id` rỗng, đang quản lý, device/component, không gắn máy khác, không hỏng, không dòng phiếu pending, không sửa chữa `new/in_progress/vendor`, company được phép. Guard của phiếu từ chối assign/loan máy ghi stock mà còn người giữ, kể cả khi đi đường khác popup. `tp_request_key` (index `btree_not_null`) + `tp_request_hash` (sha256 nội dung) chặn chạy hai lần: cùng mã cùng nội dung trả kết quả cũ, cùng mã khác nội dung bị từ chối; hai field nằm trong write guard của phiếu. Ghi trực tiếp field custody từ client vẫn bị guard `CUSTODY_FIELDS` chặn. ACL: `access_tp_equipment_quick_action_admin` (`base.group_system`, CRUD); model thuộc danh sách hạn chế mail.message/attachment/follower/activity (`common.py`).

Field tính toán mới trên `maintenance.equipment` (không lưu): `tp_usage_status` (Đang sử dụng / Trong kho / Dùng chung / Đặt tại vị trí / Đang sửa ngoài / Cần làm sạch / Chưa rõ người giữ / Nháp / Ngừng quản lý), `tp_short_config`, `tp_can_assign`, `tp_can_swap`, `tp_can_return`. Đề xuất có `need_type` (tính toán + search, suy từ `kind`/`equipment_id` của dòng) và điền phòng ban từ HR khi chọn người đề xuất; không đổi trạng thái/luồng duyệt.

## Nhập nguồn

Nguồn upload không giữ nguyên workbook làm tệp công khai: cell provenance giữ hash/sheet/row/cell/raw/cached/merged dạng đã làm sạch; cột mạng bị loại, không chạy formula. Mapping người/phòng/vị trí chọn ID và xác nhận; alias cần xác nhận riêng, không fuzzy-match hoặc tạo HR/user. Mỗi dòng có disposition. Dòng `unknown/wait/missing` không được tạo hồ sơ: apply chỉ tạo các dòng đã xác nhận, đợt chuyển `partial` và dòng chờ giữ lý do/gợi ý (gợi ý HR không tự gán); admin bổ sung ID/thông tin, xác nhận ánh xạ rồi áp dụng tiếp trên cùng đợt, dòng đã áp không tạo lại. Menu **Dòng nguồn chờ bổ sung** chỉ `base.group_system`. Dòng thiết bị tạo mới mang giá trị xác nhận (phân loại, loại quản lý, sở hữu, tình trạng kỹ thuật, cần thay thế, cấu hình). Hồ sơ nhập ở xác minh `source`, phiếu ghi nhận ban đầu ghi rõ từ Excel, chưa đối chiếu bàn giao; đề xuất nhập ở nháp/chưa xác minh, không tạo thiết bị/phiếu nhận.

Một source hash/company/kind có một batch, apply lại batch đã áp không tạo bản sao. Nguồn sau cần admin xác nhận khác biệt/đợt độc lập và lý do, đối chiếu từng dòng bằng ID. Dòng existing liên kết ID cùng company, không ghi đè business data hoặc provenance gốc; dòng thực sự new phải được xác nhận riêng trước tạo nháp. Nếu chọn nguồn trước, ID existing phải thuộc nguồn đó; hai dòng không ghép cùng một ID. Không tự merge/overwrite lịch sử. STT/dòng không là business key xuyên phiên bản. Đề xuất phải đối chiếu thành tiền và tổng nguồn, không coi thành tiền là unit price.

## Giới hạn bằng chứng

Không chạy Odoo/HOOT/E2E/race/regression theo lệnh người dùng; không seed hoặc tạo giao dịch kiểm thử trên main. Nhập thật CHG-012 tạo 54 hồ sơ thiết bị (xác minh `source`), 54 phiếu ghi nhận ban đầu và 1 đề xuất nháp; replay không tạo thêm bản ghi. Snapshot hash trước/sau giữ HR employee/department, 39 nhân viên, 28 users, membership quyền và company; `res_groups` chỉ đổi `write_date` một nhóm HR do dữ liệu cấu hình chạy lại khi `-u`. Chưa có nghiệm thu nghiệp vụ/pilot; chưa thực hiện ma trận role, race, giao dịch bàn giao/sửa/kiểm kê, PDF hoặc QR. Bằng chứng tại [acceptance](../demo/EQUIP_001_ACCEPTANCE.md) và [runbook](../../ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md).
