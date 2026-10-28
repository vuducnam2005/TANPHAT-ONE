# BIZ-002 — Bộ thiết kế nghiệp vụ TANPHAT ONE

**Ngày:** 28/10/2026, Asia/Saigon. **Loại công việc:** phân tích và tài liệu; không mở chức năng ứng dụng. **Trạng thái:** bản thiết kế để công ty nghiệm thu, chưa phải quy chế ban hành.

## 1. Rà soát khoảng trống trước khi hoàn thiện

| Phạm vi | Đã có gì tại đầu lượt | Còn thiếu gì | Tài liệu giải quyết | Thứ tự |
| --- | --- | --- | --- | --- |
| Baseline | BIZ-001, CTR-001 đọc; handoff CHG-008 | Đối chiếu source/checkpoint/NAS và ưu tiên mới | Mục 2; PROJECT_STATUS | 0 |
| Bản đồ toàn công ty A–M | Sơ đồ KD và điểm phối hợp | Ranh giới quy trình, RACI, gói bàn giao và đường ngoại lệ | [Bản đồ](TP_ENTERPRISE_PROCESS_MAP.md) | 1 |
| A cơ hội/thầu | E02–E04 | Action, kết quả nộp/thua/rút/giao trực tiếp, trùng cơ hội | [Workflow A–E](TP_PROCESS_WORKFLOWS_A_E.md) | 2 |
| B dự án | Assignment/read hiện có, khung state | Kế hoạch, hold/reopen/close và bàn giao owner | Workflow A–E | 2 |
| C hợp đồng | BIZ-001 chi tiết; CTR-001 read đã có | Làm rõ hủy review, correction, tác động hồi tố và cổng ghi | Workflow A–E + BIZ-001 | 2 |
| D giao việc | E01 một owner; khung task | Nhận/trả việc, phối hợp, quá hạn, nhận bàn giao và reopen | Workflow A–E | 2 |
| E giao khoán | E09 cấp 1/2, chống cộng trùng | Action điều chỉnh/quyết toán, nguồn phạm vi, vượt mẹ | Workflow A–E | 2 |
| F/G khảo sát/thiết kế | Luồng S01 và bước KCS | State kỹ thuật, review, issue/revision, đầu vào/đầu ra cụ thể | [Workflow F–M](TP_PROCESS_WORKFLOWS_F_M.md) | 3 |
| H/I thực hiện/tài chính | Tách domain và ca C3 | Tạm ứng/giữ lại, payment allocation, chứng từ/đối chiếu | Workflow F–M; [Tích hợp/KPI](TP_BIZ002_INTEGRATION_AND_REPORTING.md) | 3 |
| J/K hồ sơ/nhân sự/quyền | Attachment contract và assignment | Phân loại/version/chia sẻ/lưu; joiner/mover/leaver, ủy quyền | Workflow F–M; [Dữ liệu/quyền](TP_DATA_DICTIONARY_AND_ACCESS_MATRIX.md) | 3 |
| L/M báo cáo/vận hành | E12–E16, rehearsal OPS-001 | Định nghĩa KPI, freshness, import/reconcile, audit/notification/incident | Workflow F–M; Tích hợp/KPI | 4 |
| Dữ liệu và quyền toàn công ty | Database design + grant đọc contract | Từ điển field, ERD, nguồn chuẩn, ma trận scope/field/file | Dữ liệu/quyền | 4 |
| Nghiệm thu và chuyển giai đoạn | BIZ-001 C1–C6, Q1–Q8 | Kịch bản A–M bình thường/sửa sai/ngoại lệ; owner câu hỏi và gate từng slice | [Nghiệm thu/readiness](TP_BIZ002_ACCEPTANCE_AND_READINESS.md) | 5 |
| Bàn giao | Next action cũ nghiêng về CTR-002 | Ưu tiên nghiệp vụ trước code, liên kết một nguồn sự thật | PROJECT_STATUS, ROADMAP, DECISIONS, CHANGELOG; workflow chính | 6 |

## 2. Baseline đã kiểm chứng khi lập gói (CHG-20261028-009)

- Git ban đầu sạch; HEAD `0c3083fb` (CHG-008). Không có `.local/ai-workflow/active.json` trước lượt; `ai_workflow.py check` đạt CHG-008. Đã `start` checkpoint riêng cho tài liệu. Không có draft `tp_contract`/grant chưa bàn giao cần đóng thay: source thực tế là read slice đã có trong CHG-006. Không chạy test cũ để biến thành kết quả mới.
- `dev.ps1 status`: Odoo/PostgreSQL dev lắng nghe, cấu hình tồn tại. Không setup, upgrade, seed, sửa database hoặc credential.
- Registry S01–S05 và E01–E18 giữ tại [bằng chứng BIZ-001](TP_KD_EVIDENCE_AND_ACCEPTANCE.md). SHA-256 của cả năm bản NAS và bản sao đọc khớp manifest trong lượt này. Tái sử dụng `.local/biz-001` sau khi kiểm hash; không chạy macro/external link, không thêm file nguồn hay dữ liệu thật vào Git.
- Có sai lệch diễn đạt trong tài liệu cũ: mở đầu workflow/source structure vẫn nói contract chưa runtime, dù CTR-001 đã có read slice; database mô tả `verification_state` là declared/verified dù code là pending/verified/disputed. Lượt này sửa mô tả theo source; không nâng mức đảm bảo runtime hoặc bổ sung transition bằng tài liệu.

## 3. Cách đọc và phân loại căn cứ

**U — yêu cầu người dùng đã xác nhận:** Odoo + React/TypeScript riêng, một PostgreSQL database/môi trường; BASE duyệt chính thức giai đoạn đầu; tiền theo phân công/scope, hỗ trợ cấp riêng; chín tên phân hệ; ưu tiên thiết kế trước code. U không chứng minh chức năng đã triển khai.

**O — quan sát từ nguồn:** S01–S05/E01–E18 và vị trí trích dẫn cụ thể; xác định được nội dung mẫu tại hash đã ghi, không khẳng định đã là quy chế hiện hành toàn công ty. **D — đề xuất thiết kế:** RACI, capability, state/action mới, kiểm soát và ca giả lập. **Q — chưa đủ căn cứ:** phải có người phụ trách xác nhận trước cổng liên quan. **R — runtime đã kiểm chứng trước đây:** chỉ dùng cho read slice/nền theo status; tách khỏi D và khỏi kết quả kiểm tài liệu lượt này.

Mọi nội dung thiết kế mới mặc định là D nếu không gắn U/O/R. Trường hợp nguồn không đủ, tài liệu nêu Q và đầu mối theo vai trò; không gán tên người hoặc chức danh thành thẩm quyền ký. Không tự tạo hạn mức, SLA, quy chế bốn mắt hay bắt tất cả biên bản phải có BASE.

## 4. Một nguồn sự thật cho mỗi phần

| Nội dung | Tài liệu chủ | Quan hệ với tài liệu cũ |
| --- | --- | --- |
| Hiện trạng/next action | [PROJECT_STATUS](../PROJECT_STATUS.md) | Chỉ một status hiện hành |
| Cổng/ưu tiên công việc | [ROADMAP](../ROADMAP.md), [DECISIONS](../DECISIONS.md) | Không dùng bảng thiết kế làm lịch phát triển đã cam kết |
| Luật workflow chung | [TP_BUSINESS_WORKFLOW](TP_BUSINESS_WORKFLOW.md) | Là điểm vào; không sao lại toàn bộ bảng state |
| Bản đồ và RACI liên phòng | TP_ENTERPRISE_PROCESS_MAP | Đọc trước khi đi vào action |
| A–E/F–M | Hai tài liệu workflow | C giữ state code của BIZ-001 mục 4.4; không tạo bộ enum cạnh tranh |
| Quy tắc KD/contract đã phân tích | [TP_KD_WORKFLOW_AND_PERMISSIONS](TP_KD_WORKFLOW_AND_PERMISSIONS.md) | Giữ Q1–Q8 và mapping CTR-001; BIZ-002 bổ sung các phần còn thiếu |
| Nguồn và ca BIZ-001 | TP_KD_EVIDENCE_AND_ACCEPTANCE | Không chép bản trích doanh nghiệp vào tài liệu mới |
| Khái niệm field/quyền/ERD | TP_DATA_DICTIONARY_AND_ACCESS_MATRIX | [Database design](TP_DATABASE_DESIGN.md) giữ schema thực tế và hướng triển khai; dictionary mới không tuyên bố migration |
| Nguồn KPI, ranh giới tích hợp, màn hình/API | TP_BIZ002_INTEGRATION_AND_REPORTING | Không sửa OpenAPI hoặc sinh client trong lượt này |
| Kịch bản, câu hỏi và checklist code | TP_BIZ002_ACCEPTANCE_AND_READINESS | Thiết kế được walkthrough, chưa phải UAT công ty hay test ứng dụng |
| Tổ chức source | [TP_PLATFORM_SOURCE_STRUCTURE](TP_PLATFORM_SOURCE_STRUCTURE.md) | Không tạo addon rỗng hoặc workflow engine chung |

## 5. Mức hoàn thiện và điều kiện sử dụng

Bộ tài liệu bao phủ A–M ở mức thiết kế có truy vết, state/action, dữ liệu/quyền và ca giả lập. Phần A–E/H có căn cứ KD sâu hơn; F/G/J/K/M và chi tiết kế toán/thuế cần chủ chuyên môn nghiệm thu nên chỉ có khung có điều kiện. Không có quy trình mới nào được coi là công ty phê chuẩn chỉ vì viết đủ bảng.

Q1–Q14 vẫn mở theo cổng tại readiness; mỗi mã có đầu mối theo vai trò, hồ sơ cần bổ sung và slice bị chặn. Không biến việc hoàn tất baseline tài liệu thành quyết định đóng các Q.

Quyết định chuyển sang code thuộc người dùng. Khi được chuyển giai đoạn, chỉ chọn slice có checklist đủ ở tài liệu readiness; giữ cổng Q còn mở cho phần phụ thuộc. BIZ-002 không mở lại CTR-001 hoặc tự bắt đầu CTR-002. Cần ưu tiên nghiệm thu thiết kế và hồ sơ khử dữ liệu trước khi mở rộng ứng dụng.

Phạm vi có thể chọn gần nhất sau quyết định chuyển giai đoạn là CTR-002a tối thiểu trên test với actor fixture/scope và draft/submit/return; chưa mở hủy bản gửi, grant admin, BASE/legal hoặc dữ liệu thật khi Q còn liên quan. Từng slice A–M có checklist riêng trong readiness. BIZ-002 không tuyên bố đã đủ điều kiện pilot/production.

CHG-20261028-013 bổ sung [Q2-P1](TP_KD_WORKFLOW_AND_PERMISSIONS.md#74-ma-trận-q2-p1--trách-nhiệm-và-quyền-cần-xác-nhận) với 11 hành động; [readiness 7.1](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#71-nhật-ký-quyết-định-và-nghiệm-thu-điền-khi-review) ghi phản hồi yêu cầu tiếp tục phân tích, inventory thiếu bundle đủ điều kiện, SIM-P1 ba bundle bàn giấy và CTR-002a-P1 action/fixture/version/test gate. Vai trò/Q2 và các bundle chưa được công ty accepted; local source hashes khớp không thay bằng chứng hồ sơ hoặc xác nhận NAS hiện hành. Runtime đang dừng theo status, khác baseline lịch sử mục 2.

## 6. Chỉ mục nghiệm thu A–M

| Mã | Quy trình | Tài liệu chi tiết | Ca bình thường / ngoại lệ | Cổng chính |
| --- | --- | --- | --- | --- |
| A | Cơ hội, đánh giá tham gia, đấu thầu, kết quả | [A–E](TP_PROCESS_WORKFLOWS_A_E.md) | A-N / A-X | Q1, Q3 |
| B | Dự án, phân công, kế hoạch, hold/complete/cancel | [A–E](TP_PROCESS_WORKFLOWS_A_E.md) | B-N / B-X | Q9 |
| C | Hợp đồng, phụ lục, ký, hiệu lực, thanh lý | [A–E](TP_PROCESS_WORKFLOWS_A_E.md), [KD](TP_KD_WORKFLOW_AND_PERMISSIONS.md) | C-N / C-X | Q1–Q4, Q8 |
| D | Giao việc, nhận/trả, phối hợp, quá hạn, bàn giao | [A–E](TP_PROCESS_WORKFLOWS_A_E.md) | D-N / D-X | Q9 |
| E | Giao khoán, thầu phụ cấp 1/2, điều chỉnh, quyết toán | [A–E](TP_PROCESS_WORKFLOWS_A_E.md) | E-N / E-X | Q7, Q8 |
| F | Khảo sát hiện trường | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | F-N / F-X | Q5, Q10 |
| G | Thiết kế, BIM, review/KCS, phát hành/revision | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | G-N / G-X | Q5, Q10 |
| H | Sản lượng, nghiệm thu, request, tạm ứng, giữ lại | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | H-N / H-X | Q4, Q8 |
| I | Hóa đơn, thu/chi, công nợ, đối chiếu, kế toán | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | I-N / I-X | Q4, Q6, Q8 |
| J | Hồ sơ, version, chia sẻ, lưu trữ | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | J-N / J-X | Q11, Q14 |
| K | Tổ chức, HR, bàn giao, cấp/thu hồi quyền | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | K-N / K-X | Q1, Q2, Q11 |
| L | Dashboard, KPI, cảnh báo, báo cáo | [F–M](TP_PROCESS_WORKFLOWS_F_M.md), [tích hợp/KPI](TP_BIZ002_INTEGRATION_AND_REPORTING.md) | L-N / L-X | Q4, Q6, Q13 |
| M | Import, audit, notification, backup/restore, incident | [F–M](TP_PROCESS_WORKFLOWS_F_M.md) | M-N / M-X | Q12, Q14 |
