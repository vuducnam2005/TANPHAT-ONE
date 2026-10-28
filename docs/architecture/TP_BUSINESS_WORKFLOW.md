# TANPHAT ONE — Workflow nghiệp vụ và quy tắc chuyển trạng thái

Đây là blueprint để chốt nghiệp vụ trước khi tạo model/action. Phần nào ghi “thiết kế” chưa phải chức năng đã có. Nền hiện tại mới kiểm chứng đọc project theo quyền.

## 1. Luồng tổng thể

```text
TP Projects → TP Survey → TP Design → TP Contracts → TP Tasks
                                      ↓             ↓
                                  TP Documents  TP Finance
                                      ↓             ↓
                                  TP Dashboard (đọc/tổng hợp theo quyền)
```

Một module chỉ phát hành dữ liệu cho module sau khi hồ sơ đạt state cho phép. Dashboard không tạo trạng thái riêng và không trở thành nơi duyệt.

## 2. Nguyên tắc chung

- Mỗi model có state riêng; không dùng một state chung cho mọi phân hệ.
- Mọi transition chạy ở backend Odoo, trong một transaction.
- Frontend gọi command/action; không gửi state tùy ý qua PATCH.
- Transition kiểm actor capability, company, department, project scope và điều kiện dữ liệu.
- Submit/approve/reject/cancel có lịch sử, người thao tác, thời gian, lý do và request ID.
- Bản đã chốt không xóa vật lý. Revise/cancel tạo lịch sử hoặc chứng từ đảo.
- Approver không được là người nhập/chốt cùng action nếu ma trận quyền cấm.
- Retry chỉ thực hiện với command có idempotency key hoặc đã chứng minh an toàn.
- Tài liệu và file luôn kiểm quyền theo bản ghi nghiệp vụ, không cấp quyền bằng đường dẫn UNC.

## 3. Role/capability nền

| Capability | Ý nghĩa |
| --- | --- |
| `project_reader` | Đọc project và dữ liệu được cấp scope |
| `project_coordinator` | Điều phối dữ liệu draft trong project được giao |
| `department_manager` | Rà soát dữ liệu thuộc phòng ban |
| `contract_creator` | Tạo/sửa draft hợp đồng trong scope |
| `contract_reviewer` | Rà soát và trả lại hồ sơ |
| `contract_approver` | Phê duyệt theo company/giá trị/thẩm quyền |
| `finance_reader` | Đọc số liệu tài chính được cấp quyền |
| `platform_manager` | Cấu hình catalog, project metadata và assignment |
| `system_admin` | Quản trị kỹ thuật, không mặc nhiên là người duyệt nghiệp vụ |

Role là capability; scope company/project/department và trạng thái bản ghi mới quyết định quyền thực tế. Không hardcode user ID.

## 4. TP Projects

| State | Ý nghĩa | Chuyển tiếp hợp lệ |
| --- | --- | --- |
| `draft` | Hồ sơ đang tạo | `submit_review`, `cancel` |
| `review` | Chờ phòng có trách nhiệm rà soát | `activate`, `return_draft`, `cancel` |
| `active` | Được dùng làm hồ sơ chung | `hold`, `complete`, `cancel` |
| `hold` | Tạm dừng có lý do | `resume`, `cancel` |
| `complete` | Đã kết thúc | `reopen` chỉ theo quyền đặc biệt và lý do |
| `cancelled` | Không tiếp tục | Không sửa nghiệp vụ, chỉ đọc lịch sử |

Điều kiện `activate`: mã project, company, phòng chủ trì và người/role scope hợp lệ. Reader không được sửa state. Nền hiện tại mới có `tp_managed` và assignment; state workflow này chưa triển khai.

## 5. TP Contracts

| State | Ý nghĩa | Chuyển tiếp hợp lệ |
| --- | --- | --- |
| `draft` | Bản nháp | `submit_review`, `cancel` |
| `review` | Rà soát nội bộ | `return_draft`, `submit_approval`, `reject` |
| `approval` | Chờ người có thẩm quyền | `approve`, `reject` |
| `approved` | Được phép thực hiện | `start_execution`, `cancel` |
| `executing` | Đang thực hiện | `complete`, `suspend`, `cancel` |
| `suspended` | Tạm dừng | `resume`, `cancel` |
| `completed` | Hoàn tất | Chỉ revise/cancel theo chính sách |
| `rejected` | Bị trả lại | `revise` tạo phiên bản draft mới |
| `cancelled` | Hủy có lý do | Chỉ đọc lịch sử |

Điều kiện `submit_approval`: đối tác, project, company, currency, dòng phạm vi, giá trị và hồ sơ bắt buộc hợp lệ. Phụ lục không sửa trực tiếp bản đã duyệt; tạo `tp.contract.revision` với sequence và ngày hiệu lực.

## 6. Giao khoán và nghiệm thu

- Giao khoán bên ngoài khác giao khoán nội bộ; không tạo PO/vendor bill giả cho khoán nội bộ.
- `parent_allocation_id` bắt buộc cùng company/project; không cho vòng lặp.
- Cấp 2 không cộng vào tổng cấp 1; mỗi dòng phải có nguồn phạm vi.
- Nghiệm thu tách khỏi sản lượng, hóa đơn, tiền thu/chi và giữ lại.
- Acceptance chỉ được chốt khi phạm vi, kỳ, project và bên liên quan hợp lệ; chỉnh sửa sau chốt bằng revise/cancel.

## 7. Cổng triển khai workflow

Trước mỗi workflow phải có:

1. State/transition matrix được chủ nghiệp vụ xác nhận.
2. Role/capability và scope được xác nhận.
3. Điều kiện dữ liệu, trường bắt buộc và lý do reject/cancel.
4. ORM constraint, record rule, action test và API contract.
5. Test valid/invalid transition, user khác scope, retry và lịch sử.
6. UI chỉ hiển thị command người dùng có quyền; trạng thái lấy từ backend.

Thứ tự triển khai: `tp_contract` → `tp_allocation` → `tp_settlement`/reporting → staging import → accounting bridge → mở workspace các phòng tiếp theo.

