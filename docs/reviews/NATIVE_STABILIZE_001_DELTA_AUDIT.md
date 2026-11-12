# NATIVE-STABILIZE-001 — Audit delta correction A1/A2/A3

Ngày 05/11/2026, Asia/Saigon. `CHG-20261105-005`. Baseline: correction `CHG-20261105-004`; checker đạt trước khi bắt đầu. Vai trò điều phối DEC-022: đọc source, chạy kiểm chứng trên clone, ghi finding và prompt; không triển khai wizard hoặc áp dev.

**Kết luận: `NEEDS_FIX` cho đặc tả UI-CTR-NATIVE-001a. A3 đạt; A1/A2 đã cải thiện nhưng mỗi phần còn một thiếu sót cụ thể.** Đây là vấn đề trong thiết kế chưa được code, không phải kết luận wizard hợp đồng đang chạy có lỗ hổng.

## 1. Kết quả theo hạng mục

| Mục | Kết luận | Căn cứ |
|---|---|---|
| A1 — Owner, target và phạm vi transient | **PARTIAL — D1/P2** | Owner global restriction, company, target do server đặt và confirm không tham số đã rõ. Tuy nhiên `draft.line`/`return.issue` chỉ có owner/company, thiếu kiểm quyền đọc project/header trực tiếp |
| A2 — Tiền trong wizard sau thu hồi | **PARTIAL — D2/P2** | Không lưu baseline, tách `amount.input`, có restriction grant/assignment và xóa khi thành công là phù hợp. Compute tiền hiện tại chưa kiểm assignment; AT-10/§12 mâu thuẫn G7 về quyền đọc tiền gốc của manager |
| A3 — Công cụ chạy test | **PASS cho phạm vi correction** | Unit 18/18; chạy Odoo thật 29/29 → exit 0; chạy tag không có test, Odoo exit 0 nhưng runner exit 1. Lint đạt |

## 2. D1/P2 — Dòng con cần restriction phạm vi riêng

**Vị trí:** [spec mục 9.2](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md), dòng 196 của baseline004. Hai model `tp.contract.native.draft.line` và `tp.contract.native.return.issue` có global restriction owner qua `wizard_id.create_uid` và company qua `wizard_id.company_id`; không có `project access` hoặc `wizard_id access read` như header. `amount.input` đã có project restriction riêng, không thuộc thiếu sót này.

**Tình huống:** user tự mở wizard khi còn phân công, rồi mất quyền đọc project. Header bị chặn nhưng user vẫn là owner, vẫn cùng company. Gọi trực tiếp RPC vào model con có thể đọc tên dòng hoặc nội dung ý kiến, dù không mở được header.

**Đã tái hiện bằng probe tương đương trên clone:** dùng hai transient chuẩn `project.template.create.wizard` và `project.template.role.to.users.map`, thêm ACL tương ứng trong transaction thử. Header lấy scope từ `template_id`; child lấy owner từ `wizard_id.create_uid`. Dự án, assignment, wizard và role đều giả lập. Sau tắt assignment và làm mới access cache để mô phỏng request kế tiếp:

| Phép kiểm | Kết quả |
|---|---|
| Staff còn đọc project | Không |
| Đọc trực tiếp header / tìm header | `AccessError` / 0 |
| Đọc trực tiếp child / tìm child | **Đọc được / 1** |
| Bổ sung global restriction child `[('wizard_id', 'access', 'read')]` rồi đọc/tìm | `AccessError` / 0 |

Tất cả rollback, không gọi action tạo dự án từ template. Không cài model wizard hợp đồng để làm probe.

**Căn cứ source:** `odoo/orm/models.py:4913-4916` tối ưu security domain bằng môi trường sudo; domain đi qua owner/company không tự kéo quyền đọc header vào. `_access_domain` chỉ tự thêm restriction parent cho quan hệ `_inherits` (`models.py:3622-3628`), không cho mọi Many2one. Vì vậy không suy quyền child từ quan hệ cha–con.

**Correction tối thiểu:** giữ owner/company và thêm global restriction `crud` tường minh trên hai model con: `wizard_id access read`, hoặc project access tương đương. Thêm acceptance sau khi mất project access với direct read/search/web_read/export/write và nested header. Chứng minh gỡ restriction scope thì ca âm thất bại; không chỉ kiểm khác owner.

## 3. D2/P2 — Compute tiền và AT thu hồi assignment phải cùng quy tắc

**Vị trí:** [spec mục 9.3 bước 2](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md) dòng 213–215; §12 dòng 332; AT-10 dòng 362; G7 dòng 384 của baseline004.

Compute `current_amount_text` chỉ được mô tả đọc `tp.contract.line.amount` bằng quyền user. Trong khi đó A2/AT-10 yêu cầu mất assignment thì compute rỗng và đọc tiền gốc bị chặn. Chính G7 và ACL gốc xác nhận một ngoại lệ: manager có `financial_read`, còn quyền đọc project, vẫn đọc được tiền gốc khi không có assignment. `compute_sudo=False` tự nó không thêm điều kiện assignment.

**Đã kiểm bằng dữ liệu giả và rollback:** tạo project/hợp đồng/revision/dòng tiền thử, dùng một actor manager fixture có grant. Không in số tiền vào báo cáo.

| Trạng thái | Đọc project | Đọc tiền gốc | Có `financial_read` trong `_tp_capabilities` |
|---|---|---|---|
| Có assignment active và grant | Có | Có | Có |
| Tắt assignment, giữ grant | Có | **Có** | **Không** |
| Thu hồi thêm grant | Có | Không | Không |

**Correction tối thiểu, không đổi policy/ACL gốc:**

1. Compute tiền trong **wizard** kiểm rõ project readable + assignment active + `financial_read` còn hiệu lực ở request hiện tại, tái sử dụng helper capability phù hợp; thiếu quyền trả rỗng hoặc bị chặn bởi restriction scope. Chỉ sau kiểm đó mới đọc tiền bằng quyền user. Metadata không đòi quyền tiền.
2. Tách AT-10: thu hồi/hết hạn grant; mất assignment của staff mất project access; mất assignment của manager vẫn có project access/grant. Ca manager phải chặn tiền trong wizard và thao tác workflow; không đòi ACL gốc chưa sửa phải chặn tiền gốc.
3. Sửa §12 và G7 để khớp: không tuyên bố mất assignment luôn thu hồi quyền đọc tiền gốc cho mọi group. G7 là policy baseline còn mở; không dùng lượt này để siết ACL, đổi grant hoặc suy quyền từ chức danh.

Không cần người dùng chốt lại thẩm quyền để sửa mâu thuẫn đặc tả này. Nếu muốn thay quyền đọc tiền gốc thì đó là quyết định riêng ngoài correction.

## 4. Kiểm chứng độc lập thực chạy

| Kiểm tra | Kết quả / bằng chứng |
|---|---|
| `python -m unittest scripts.tests.test_native_stabilize001 -v` | **18/18 đạt**. `.local/native-stabilize001-delta-audit/runner-unit.log` |
| `ruff check scripts/native_stabilize001.py scripts/tests/test_native_stabilize001.py` | Đạt |
| `native_stabilize001.py odoo-tests --expect-tests 29` | **Exit 0, 29/29**, dashboard privacy18 + Home11; log `run-20261105T130930855231Z.log` và verdict JSON tương ứng trong `.local/native-stabilize001/odoo-tests/` |
| `odoo-tests --modules tp_web_home --tags /tp_web_home:TpStab001NoSuchClass` | **Runner exit 1**, `no_tests`, `no_tests_for_tag:tp_web_home`; Odoo process exit0,total0. Log `run-20261105T131036653652Z.log` và verdict JSON tương ứng |
| Probe D1/D2 | `.local/native-stabilize001-delta-audit/probe.py`, `rollback-probes.json`, `probe-console.log`; chỉ clone sở hữu `tp_tanphat_stab001_20261105`; explicit rollback; kiểm lại transaction mới còn 0 project/contract/wizard/role/ACL thử |
| Source trước bàn giao | 234 maintained code files, digest `6abcc74a3541323019060d5935b7aa6d874e98192f2fb9e44fa852d6725d957d`, khớp CHG004. Không sửa application/tooling/ACL/core/React |
| Runtime sau kiểm | Dev18069 vẫn PID15892; clone18169/demo18109 không listen. Không upgrade/seed/apply dev; clone cron/SMTP giữ vô hiệu hóa; không commit/push |

Không chạy lại browser78/ORM9 actor×2 của audit003 vì không đổi app/dashboard; các kết quả đó là bằng chứng lịch sử, không gọi là test vừa chạy. Không kiểm lại toàn bộ dashboard/mobile/data003 hay nghiệp vụ pháp lý. A1/A2 chưa có wizard thật để chạy acceptance; probe chứng minh semantics của source hiện tại và mâu thuẫn thiết kế.

G8 (hết hạn tự nhiên qua ngày) tiếp tục là ca bắt buộc AT-17 trước nghiệm thu implementation; chưa có bằng chứng mới để đóng. Q2 người thật/pilot không được đóng bởi audit kỹ thuật.

## 5. Bước tiếp theo

Giao [prompt correction delta D1/D2](../prompts/CLAUDE_NATIVE_STABILIZE_001_DELTA_CORRECTION.md). Chỉ sửa phần đặc tả/acceptance và bàn giao liên quan, giữ A3 đã đạt. Audit lại đúng hai delta; khi đạt mới phát prompt code UI-CTR-NATIVE-001a trên DB test, viết AT trước.

F-DASH-01/02 chưa áp dev; việc áp cần yêu cầu riêng của người dùng. BASE, ký, hiệu lực, thanh toán, upload, grant người thật và TASK-001 vẫn ngoài scope.
