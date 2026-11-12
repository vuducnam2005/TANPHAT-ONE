# KD-ACCESS-002 — Inventory

Ngày 09/11/2026. Baseline CHG-20261109-002 đã bàn giao; workflow check PASS,
không checkpoint khác. Yêu cầu thực hiện trực tiếp của người dùng mở ngoại lệ
triển khai cho batch này và bỏ nhãn công ty trên navbar; không đổi res.company.

Clone owned: `tp_tanphat_kdaccess002_20261109`, port19289, PostgreSQL55432.
Restore ban đầu576bảng/295attachment reference khớp snapshot dev; source/config/
filestore riêng. Danh tính và credential chỉ private `.local/kd-access001/`.
Inventory JSON riêng `.local/kd-access002/`; không xuất hash/password ra log.

| Alias | Assignment reader | Project grant | Typed grant | Opportunity grant trước |
| --- | ---: | ---: | ---: | ---: |
| head | 8 | 16 | 56 | 0 |
| deputy | 4 | 20 | 84 | 0 |
| project_lead | 4 | 20 | 84 | 0 |
| planning | 4 | 8 | 32 | 0 |
| support | 2 | 0 | 2 | 0 |

Nguồn: journal KD-ACCESS-001 đối chiếu lại bằng ORM trước ghi. Cả năm dùng
group_scoped_staff → tp_core.group_user → internal; không sales/admin/manager.
Account khác có assignment trên registry được liệt kê private theo ID, không
suy danh tính/role từ tên; giữ nguyên và không cấp delta nếu thiếu mapping.

Kiểm lại dev bằng ORM: cả năm cùng company ID1, đơn vị ID18 theo journal;
group trực tiếp duy nhất `tp_kd_workspace.group_scoped_staff` (ID57). Implied
baseline là `tp_core.group_user` và quyền nền native; sau batch thêm
`base.group_allow_export` bằng implication của group chuyên môn, không cấp sales.
Bốn account khác có assignment trên registry là actor/operator lịch sử, không
có mapping thuộc năm tài khoản nhân sự; không áp delta hoặc chiếm dụng account đó.

Menu/action chung: Home → KH-KD → `action_overview`, `action_opportunities`,
`action_projects`, `action_tasks`, `tp_contract.action_tp_contracts_list`,
`action_allocations/productions/acceptances/plans/payments/credentials/obligations`.
Báo cáo KH-KD hiện dùng lại `action_overview`; chưa có trung tâm báo cáo riêng.
Tài khoản dùng native preferences của current user. Nút tạo/gửi/trả và tiền
vẫn kiểm capability/owner/reviewer/state sau khi model/menu đã đọc được.

Đường kiểm: CRM search/name_search/read/create/write/copy/archive/unlink,
read_group/order/domain/export, related/report/dashboard, file/chatter;
typed7domain và contract owner/reviewer/version/reason; Project/Task chỉ đọc.

Phân loại gap trước sửa: CRM không có grant/ACL chuyên môn (cấu hình); prepare
gộp submit, thiếu owner/state/money guard (backend); Project-create/WBS-write
chỉ manager, chưa có action scoped (NOT_IMPLEMENTED); support submit/money và
quản trị grant bị từ chối là đúng policy. Không mở TASK-001 trong batch này.
