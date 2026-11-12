# NATIVE-STABILIZE-001 — Nghiệm thu delta đặc tả D1/D2

Ngày **06/11/2026**, Asia/Saigon. `CHG-20261106-001`. Baseline correction: `CHG-20261105-006`. Phạm vi chỉ audit hai finding trong [audit005](NATIVE_STABILIZE_001_DELTA_AUDIT.md), không audit lại toàn bộ nền/dashboard/mobile.

**Kết luận: D1 và D2 đạt ở tầng đặc tả/acceptance. UI-CTR-NATIVE-001a `READY_FOR_TEST_CODE`.** Không còn yêu cầu correction tài liệu D1/D2 trước khi giao code. Đây không phải nghiệm thu implementation: chưa có wizard native, 24 acceptance chưa được chạy trên chức năng đó, chưa có business acceptance hoặc pilot.

## 1. Đối chiếu hai delta

| Finding | Đã đối chiếu độc lập | Kết luận |
|---|---|---|
| D1 — scope của dòng con | Spec §9.2 bổ sung global restriction `crud` `[('wizard_id', 'access', 'read')]` trên `draft.line` và `return.issue`; giữ owner/company. Header tiếp tục kiểm owner/company/project. AT-18 kiểm chính owner sau mất project access qua direct read, search/count, export, web_read, write/unlink/create và nested header; có đối chứng gỡ riêng restriction scope | **PASS_SPEC** |
| D2 — compute tiền và quyền gốc | Spec §9.3 bước 2 yêu cầu `_tp_amount_display_allowed()` kiểm quyền đọc project và `financial_read` từ `_tp_capabilities` hiện tại, trước khi đọc tiền; không lưu/ormcache, không sudo đọc tiền. §12, AT-10a..d/10g, AT-17 và G7 phân biệt staff mất project access với manager còn project/grant; metadata không đòi financial grant. AT-10d có đối chứng bỏ guard | **PASS_SPEC** |

Căn cứ source đã đọc:

- `odoo/orm/domains.py`: toán tử `access` kiểm `_access_domain` của comodel với user hiện tại. Điều kiện explicit khác domain chỉ đi qua owner/company.
- `custom_addons/tp_contract/models/tp_contract_workflow.py:333`: `_tp_capabilities` yêu cầu assignment active; không có thì trả tập rỗng.
- `custom_addons/tp_project/models/tp_project_grant.py:92`: helper capability kiểm grant/capability/project và ngày hiệu lực; `financial_read` không theo phòng ban.
- `custom_addons/tp_contract/security/ir.access.csv`: quyền tiền gốc không yêu cầu assignment riêng khi vẫn có project access. G7 được giữ đúng baseline, không biến correction UI thành sửa policy gốc.

Đã đọc lại JSON probe rollback của audit005: child còn đọc được khi thiếu explicit restriction, bị chặn sau thêm restriction; manager mất assignment vẫn đọc tiền gốc nhưng không còn workflow capability. Đây là bằng chứng lịch sử đã đối chiếu, **không phải probe vừa chạy** ngày06/11.

## 2. Kiểm tra thực hiện trong lượt audit này

| Kiểm | Kết quả |
|---|---|
| `ai_workflow.py check` trước sửa bàn giao | PASS với CHG-20261105-006 |
| Snapshot code độc lập | 234 maintained files, digest `6abcc74a3541323019060d5935b7aa6d874e98192f2fb9e44fa852d6725d957d`, khớp CHG006 và CHG005 |
| Acceptance ID | 24 ID không trùng: AT-01..09, AT-10a..g, AT-11..18 |
| Liên kết | 5 tài liệu correction/spec/handoff không có link file hỏng; kiểm lại các tài liệu thêm/sửa trong lượt audit trước finish |
| Source và bằng chứng | Đối chiếu rule/helper nêu trên và `.local/native-stabilize001-delta-audit/rollback-probes.json` |
| Runtime chỉ đọc | TCP loopback **18069, 18169, 18109 và 55432 đều không mở** tại lần kiểm. Không kết luận dev đang chạy theo handoff cũ; không tự khởi động dịch vụ |

Không chạy Odoo, clone, PostgreSQL hoặc trình duyệt trong lượt này; không cần chạy lại bộ test ứng dụng khi application code không thay đổi. A3 đã đạt audit005 (unit18/18, Odoo29/29 và zero-test exit1); giữ kết luận đó dưới dạng bằng chứng lịch sử, không ghi là test mới chạy.

`git diff --check`, kiểm liên kết/định dạng và `ai_workflow finish/check` phải đạt trước bàn giao CHG-20261106-001. Không commit/push.

## 3. Điều kiện khi chuyển sang code

Giao [prompt UI-CTR-NATIVE-001a](../prompts/CLAUDE_UI_CTR_NATIVE_001A.md). Kết quả cần có là menu/list/form native và wizard chạy lại sáu action backend đã có, xuyên từ nháp → trình → trả lại → bắt đầu chỉnh sửa → trình lại. Code/test trên database test bằng actor/dữ liệu giả; viết AT trước.

- D1/D2 phải được kiểm trên các model thật sau implementation, có đối chứng gỡ restriction/guard; pass thiết kế không thay test runtime.
- **G8/AT-17:** kiểm hết hạn tự nhiên qua ngày, không ghi grant để làm mới cache. Phải đạt trước nghiệm thu chức năng tiền. Nếu baseline còn lỗi, ghi bằng chứng và giới hạn; không nới test hoặc tự sửa policy gốc để báo xanh.
- **G7:** còn mở cho policy tiền gốc; kỳ vọng manager theo baseline đã ghi rõ trong AT-10d, không chặn code wizard test theo đặc tả này.
- **Q2/người thật/pilot:** còn chặn vận hành thật; không chặn implementation bằng fixture đã được cho phép trong DEC-020/021.
- F-DASH-01/02 chỉ được xét áp dev khi người dùng yêu cầu riêng. Không khởi động dev để triển khai UI001a.
- BASE record/verify, ký, thẩm quyền ký, hiệu lực, thanh toán, upload/phân loại tệp, grant thật và TASK-001 tiếp tục ngoài scope.

Phiên điều phối này chỉ cập nhật audit/prompt/handoff. Không sửa application/tooling/ACL/core/React, cấu hình, tài khoản hoặc database.
