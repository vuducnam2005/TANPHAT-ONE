# TANPHAT ONE — Lộ trình lập trình và kiểm chứng

**Phiên bản:** PLAN-v1, 28/10/2026. **Loại:** kế hoạch điều phối; không triển khai chức năng trong phiên này.  
**Chủ trương đã xác nhận:** phiên chính lập kế hoạch, tổng hợp ý tưởng, phân tích, review/test kết quả Claude và phát prompt. Claude thực thi từng batch ở phiên riêng khi người dùng giao prompt.

`PROJECT_STATUS.md` là trạng thái hiện hành; `ROADMAP.md` là danh mục task. Tài liệu này giữ thứ tự phụ thuộc, đầu ra và tiêu chí nghiệm thu dự kiến. Các mốc tương lai là đề xuất, không tự chốt nghiệp vụ công ty hoặc mở pilot.

## 1. Điểm xuất phát đã có bằng chứng

| Nội dung | Thực tế đã có | Ý nghĩa đối với lộ trình |
| --- | --- | --- |
| Nền | Odoo 20 + React/TypeScript/Vite riêng; một PostgreSQL database mỗi môi trường; API session/scope | Kế thừa source; không xây lại auth/backend/database từ đầu |
| Đọc dự án/hợp đồng | CTR-001, project list/detail, quyền tiền theo project | Mở rộng vertical slice đang có |
| Nháp hợp đồng | Create/edit/amendment, submit, return, begin rework và resubmit | Không code lại CTR-002a |
| Sửa lỗi gần nhất | CHG-020: enum/currency, self-review picker/backend, legacy pending guard | Baseline kỹ thuật cho các batch sau |
| Kiểm chứng CHG-020 | 79 Odoo, 22 Vitest, 3 mock E2E, 2 live E2E; hai HTTP request race/replay đạt | Đây là kết quả lịch sử CHG-020; không phải test mới chạy trong lượt lập kế hoạch |
| Chưa đủ | Q2-A/B, bundle khử dữ liệu thực tế, owner/evidence/sign-off; grant ledger, policy metadata/export/file, môi trường pilot | Tách khỏi phần test fixture đã được giao thiết kế |
| Pháp lý/tài chính | BASE là nơi duyệt chính thức; action ký/hiệu lực/thu chi chưa mở | Mỗi action phải có cổng riêng trước khi triển khai |

Quy tắc giữ nguyên: backend enforce quyền/state/tiền; không sửa `odoo/` hoặc `addons/`; không nhân bản `res.users`, `res.partner`, `hr.department`, `project.project` hay sổ kế toán; không đọc Excel/NAS làm database runtime; credential/hồ sơ thật ở ngoài Git.

## 2. Phân loại công việc và cổng thực thi

| Làn | Ví dụ | Đủ điều kiện khi | Phạm vi cho phép |
| --- | --- | --- | --- |
| M — Maintenance đã có | Sửa V01/V02; regression workflow hiện có | Hành vi đã chốt, lỗi tái hiện được, test fixture/DEC-020/021 đủ | Sửa đúng lỗi; không thêm nghiệp vụ/capability/state |
| F — Tính năng hoặc tooling mới trên test | Runner cô lập, tìm kiếm project, inbox, grant ledger | Đặc tả của chính batch và acceptance rõ; người dùng giao prompt; policy mới còn thiếu phải giữ riêng | Dữ liệu giả, model/API/UI đúng scope; không tự chuyển thành pilot |
| P — Pilot nghiệp vụ | Nhóm KD được chỉ định dùng draft-review | Q2 và Q liên quan đúng action, bundle, owner, UAT charter, security/ops đạt | Chỉ project/actor/dữ liệu/action được cho phép |
| O — Phát hành/vận hành | HTTPS, staging, migration, backup ngoài máy | Scope môi trường rõ, rollback, owner và Q14 liên quan | Không dùng dev làm production; deployment/cutover theo yêu cầu riêng |

Thiếu Q2 người thật không chặn M hoặc tooling F độc lập. Ngược lại, đặt tên “test-only” không tự cho phép tạo workflow nghiệp vụ chưa có đặc tả. Inbox/acknowledgement là tính năng mới F, không gọi là maintenance CTR-002a. Không tự đổi `review_complete`, BASE, ký, hiệu lực hoặc grant thật qua một bugfix.

AUTH-002 là một batch F độc lập được theo dõi trong [đặc tả AUTH-002](TP_AUTH002_LOGIN_SPEC.md) và [ROADMAP](../ROADMAP.md), song song với các batch C00–C17 nhưng không thuộc thứ tự contracts. Slice 1 chỉ xử lý React/session notice; slice 2 mới xử lý template native Odoo và handoff 2FA trên database test cô lập. Không dùng mục F này để mở dev, pilot hoặc thay thế cổng người dùng giao prompt.

## 3. Cách tổ chức một batch Claude

Một batch làm một kết quả dùng được xuyên backend → security → API → React → test. Không giao một prompt xây cả phân hệ lớn hoặc viết toàn bộ backend rồi để frontend/security đến cuối.

1. **Baseline:** đọc instructions/status/decision/readiness, Git status/diff, checkpoint và runtime. Nếu có code Claude chưa bàn giao, audit batch đó trước; không reset, không `finish` thay để che lệch.
2. **Gate:** nêu rõ làn, scope, action/field/capability nào đã chốt và phần nào còn Q. Prompt triển khai chỉ phát khi acceptance của batch đủ cụ thể.
3. **Implementation:** start checkpoint; tận dụng model/rule/API đã có; schema/ORM → quyền → action transaction/version/idempotency/audit → OpenAPI/types → UI.
4. **Technical acceptance:** test có ý nghĩa cho ca bình thường, bị từ chối, scope, state, rollback, retry/race và field/file theo phần thay đổi. Không lấy số lượng test làm mục tiêu.
5. **Handoff:** source diff + lệnh/log thực chạy + giới hạn + status/changelog/architecture và `finish/check` đúng change ID.
6. **Audit phiên chính:** review code/test độc lập và chạy lại phần cần thiết trên test cô lập; nếu thiếu bằng chứng ghi chưa kiểm. Trả correction prompt khi có lỗi. Phiên chính không tự sửa code ứng dụng.
7. **Business/release:** technical acceptance, business acceptance và quyền pilot là ba kết luận riêng. Commit/push/deploy chỉ thực hiện khi người dùng yêu cầu tương ứng.

## 4. Bản đồ tổng thể

| Chặng | Các batch dự kiến | Kết quả sau chặng | Cổng chính |
| --- | --- | --- | --- |
| G0 — Baseline | C00 kiểm baseline; C01 môi trường test tái lập | Claude và phiên chính chạy cùng một quy trình kiểm chứng, không phụ thuộc helper riêng một máy | CHG-020; không đổi nghiệp vụ |
| G1 — Contracts sẵn sàng review | C02 UX nhập liệu; C03 quyền record/field/file/export | Nhóm test thao tác hồ sơ thuận tiện; có bảng bằng chứng dữ liệu được phép/bị chặn | Policy hiện có; Q2/Q11 cho phần thay đổi quyền mới |
| G2 — Pilot Contracts giới hạn | C04 grant lifecycle; C05 inbox; C06 staging/ops; UAT-P1 | Một project và nhóm KD được chỉ định dùng draft→review→return→rework | Q2, bundle, owner, security, Q14; Q khác chỉ khi scope phụ thuộc |
| G3 — Hợp đồng đầy đủ hơn | C07 review complete; C08 BASE record/verify; C09 ký/hiệu lực | Hồ sơ phân biệt rõ rà soát, kết quả BASE, bằng chứng ký và hiệu lực | Q1/Q2/Q3/Q4/Q8 theo từng action |
| G4 — Quản trị dự án/giao khoán | C10 project/task tối thiểu; C11 allocation | Giao trách nhiệm và theo dõi khoán cha/con có lịch sử | Q9, Q7/Q8, contract baseline hợp lệ |
| G5 — Thực hiện và tài chính | C12 sản lượng; C13 nghiệm thu; C14 payment request; C15 accounting bridge | Truy chuỗi từ phạm vi đến chứng từ, không đồng nhất đề nghị với tiền | Q4/Q6/Q8 và chủ nghiệp vụ từng khâu |
| G6 — Dữ liệu/báo cáo | C16 staging import; C17 báo cáo/KPI | Import có đối chiếu, báo cáo theo quyền và nguồn đã xác minh | Q12/Q13; model nguồn ổn định |
| G7 — Các phòng khác | Survey/Design/Tasks/HR/Documents và cơ hội/thầu theo nhu cầu | Mở từng workflow chuyên môn, giữ một nền chung | Q5/Q9/Q10/Q11; owner/chức năng Odoo thực có |

Pilot P1 ở G2 chỉ dùng draft-review và các quyền được phê chuẩn, không cần chờ G3–G7 xong. Báo cáo tác nghiệp từ nguồn đã có có thể phát hành sớm; KPI tiền chỉ phát hành khi nguồn và công thức của chính KPI đạt cổng. C00–C17 là mã batch điều phối, không thay task ID nghiệp vụ trong ROADMAP.

## 5. Chi tiết các batch gần nhất

### C00 — Kiểm baseline, tiếp nhận thay đổi Claude

**Task:** COORD-001; chỉ review. **Trạng thái:** CHG-020 có bàn giao kỹ thuật; từng lần Claude mới phải kiểm delta từ baseline đó.

- Đọc Git diff và `AI_WORKFLOW_STATE.json`; xác định thay đổi sẵn có, thay đổi Claude, checkpoint và source version. Không lấy HEAD làm toàn bộ phiên bản khi working tree còn chưa commit.
- Phân biệt log đã chạy với kế hoạch test; kiểm khả năng tái lập, guard company/project/department, tiền, snapshot/version/idempotency/audit.
- Kết quả: danh sách finding có file/dòng/reproduction/expected/test, verdict và một next action. Nếu không có diff mới hoặc concern mới, không chạy lại cả bộ ứng dụng chỉ cho tài liệu.

### C01 — Tooling test cô lập có thể dùng lại

**Task đề xuất:** FND-002. **Làn:** F. **Có thể giao prompt code riêng ngay vì không bổ sung nghiệp vụ.** [Prompt cụ thể](../prompts/CLAUDE_C01_ISOLATED_TEST_RUNTIME.md).

**Hiện trạng:** live spec đã có trong workspace bàn giao nhưng `frontend/tests/e2e/contract-workflow-live.spec.ts` và `runtime.py`, seed fixture, race report/helper của CHG-020 chưa được commit trong Git hiện tại. Người khác checkout Git chưa thể tái lập full live/race chỉ từ source được bàn giao.

**Code dự kiến:** tool dưới `scripts/`, test tooling, config example không secret, runbook và chỉnh test harness nếu cần. Chỉ chuẩn hóa logic tạo/start/status/test/stop của instance fake; không thay workflow, model nghiệp vụ hay dữ liệu dev.

**Yêu cầu:** exact test database/origin allowlist, ownership marker, data-dir riêng, fixture idempotent, secrets sinh local, fail khi đụng instance không sở hữu; không recursive delete/reset/drop DB; cleanup dừng đúng process nó tạo. Report có source fingerprint, lệnh, exit/summary, target DB và assertions đã thực thi; không chỉ file JSON “passed”. Chặn reuse Vite proxy sai database/origin.

**Nhìn thấy sau batch:** từ checkout có dependency chuẩn bị, người chạy dùng tài liệu trong Git để dựng fake instance, chạy live UI và race độc lập, lấy report rồi dừng. Không cần bản helper cá nhân.

**Test nghiệm thu:** refuses dev DB/wrong origin/foreign marker/port conflict; second prepare không nhân fixture/reset password; failed test trả nonzero; hai session thật cùng chờ lock trước khi thả; khác key 200+409, cùng key replay, mỗi version/audit/outbox/idempotency +1; dev rowset/config/secrets/filestore không bị ghi bởi tool. Giữ trạng thái dịch vụ ban đầu.

**Giới hạn:** dùng PostgreSQL local đã có nếu được nhận diện đúng; không cần Docker/microservice/CI/server mới. Không commit `.local`, credential, trace/video hoặc business sample.

### C02 — Hoàn thiện thao tác nháp trên web

**Task đề xuất:** CTR-002a.2. **Làn:** F. **Trước code:** lập UI/API acceptance hẹp; giữ nguyên state/capability/amount policy đã có.

- Dùng API project hiện có để search/pagination thay giới hạn 20 bản đầu; đảm bảo người dùng tìm được project thứ 21+ trong scope.
- Chọn đối tác qua query allowlist đúng company/scope nếu được chọn trong batch; không tự làm partner bắt buộc trước submit. Rule partner required vẫn là câu hỏi nghiệp vụ riêng.
- Rà soát hiển thị currency, amount confirmed/unconfirmed/null/0, sửa dòng và return reason; giữ server validation, version/conflict và idempotency.
- Đầu ra: tạo/sửa/gửi hồ sơ không bị mắc vì project picker, người dùng hiểu field bị khóa/lỗi quyền/stale version; không có action pháp lý mới.
- Test: nhiều trang project, deep link/reload, keyboard/mobile, không project ngoài scope, partner ngoài scope, ca draft-review với backend thật. Test hình thức/hover bổ sung khi có thay đổi UI; không redesign login hoặc toàn bộ shell.

### C03 — Bịt rò rỉ metadata, tài liệu và export

**Task đề xuất:** SEC-002/DOC-001a. **Làn:** F; business policy mới cần Q2/Q11.

- Tạo ma trận field nào reader/reviewer/financial reader được thấy, gồm BASE provenance/decision_reason/authority_source, filename, reason/issues/fix summary, audit/outbox, export và download.
- Với policy đã chốt: sửa allowlist/redaction và check ORM/RPC/API/search/read_group/export/file; không chỉ ẩn UI. Free-text cần quy tắc nhập/phân loại và khả năng redaction theo nghiệp vụ; regex quét số không phải bằng chứng đã ngăn rò tiền.
- Quyền `financial.export` nếu làm là capability/action mới, phải có scope/RFC và không suy tự động từ `financial_read`. Không tự đổi lịch sử grant hoặc migration mở quyền.
- Đầu ra: bộ role fixture chứng minh user chỉ metadata A/tiền B không lấy tiền A bằng đường khác; tải file sau revoke bị từ chối.
- Test: không có grant, grant khác project/company, expired/revoked, kết hợp nhiều role, direct URL/API/RPC/export, cache và request sau revoke. Không đưa chuỗi nhạy cảm vào error/log.

## 6. Các batch để mở pilot giới hạn

### C04 — Vòng đời cấp/thu hồi quyền có audit

**Task:** IAM-001 trong phạm vi nền TP Projects/TP HR. **Cổng:** Q2-B/Q11, decision/provision/revoke actor và người xác nhận; không suy từ chức danh.

**Nội dung:** data lifecycle grant với hiệu lực/thời hạn, lý do/evidence, actor quyết định và actor thực hiện, ledger; cấp/revoke/handover theo exact project/capability. Không đổi actor lịch sử. Cùng hay khác người quyết định/thao tác là policy công ty, không tự đặt default.

**Đầu ra:** operator được ủy quyền biết ai đang có quyền gì, căn cứ nào, hết hạn khi nào và revoke được truy vết. Test fixture trước; user thật chỉ sau gate P.

**Nghiệm thu:** không self-grant theo policy được chốt, không provision ngoài quyết định, duplicate/expiry/retry/race đúng, mất quyền ở request sau, không leak payload tiền qua replay cache. API/UI quản trị chỉ trong scope actor. Pilot có thể dùng quy trình operator có audit được owner chấp nhận; không bắt buộc xây cả phân hệ HR trước.

### C05 — Inbox và delivery của event

**Task:** NTF-001. **Đây là tính năng mới F, không gọi là CTR-002a maintenance.**

**Trước code:** chốt event đang có, recipient theo scope, cấu trúc inbox, delivered/read/ack nghĩa gì, API/error, dedup và retention. Xác nhận nếu thêm model/action; tách notify state khỏi state hợp đồng. Retention thực tế chưa có căn cứ thì không auto purge record trong production.

**Nội dung:** event/outbox trong transaction; delivery retry/dedup, inbox chỉ trả metadata được phép và link; link recheck quyền hiện tại. Đầu tiên chỉ in-app. Không gửi Slack/email/BASE hoặc thông báo cho người thật trong batch test.

**Đầu ra:** actor fixture thấy hồ sơ cần review/bị trả, không mở từng hồ sơ để tìm. Notification thất bại không chạy lại transition.

**Nghiệm thu:** lỗi rồi retry không trùng; worker crash/concurrent delivery; user mất quyền không đọc inbox/file; không có tiền trong payload không được phép; acknowledgement nếu có phải CSRF/idempotent/audit phù hợp. Không mặc nhiên coi C05 bắt buộc với mọi pilot; owner có thể chấp nhận cơ chế nhận việc được quản lý khác, có gap ghi rõ.

### C06 — Môi trường pilot và diễn tập nâng cấp/phục hồi

**Task:** OPS-002. **Làn:** O. **Cổng:** Q14 theo phạm vi, người vận hành và kế hoạch sự cố.

**Nội dung:** staging tách dev/test, cấu hình secrets ngoài Git, HTTPS/same-origin/session, migration có source version, backup database+filestore+config, nơi lưu ngoài máy và restore đối chiếu, rollback cùng database/filestore/source.

**Đầu ra:** có runbook dựng/nâng cấp/phục hồi, report restore và owner hỗ trợ; không phát hành production chỉ vì chạy được Vite. Đánh giá và xử lý/giới hạn INFO filestore GC WinError 5 trước khi hứa độ ổn định tệp; MFA thật chỉ kết luận khi thực sự kiểm.

**Nghiệm thu:** restore chạy được login/API/scope/attachment; migration không mất dữ liệu, fail có đường rollback; đo RPO/RTO so mục tiêu được chốt; không lộ secret; biết ai nhận incident. Deploy/cutover phải được người dùng giao riêng.

### UAT-P1 — Pilot draft-review của Ban KD

Không cần chờ BASE/ký/hiệu lực/thanh toán hay toàn bộ G3–G7. Đầu ra bắt buộc là **pilot charter**: một project, actor được bổ nhiệm, quyền, action, môi trường, dataset được phép, khoảng thời gian, owner hỗ trợ/rollback, tiêu chí dừng và mã bằng chứng UAT. Ghi tại readiness, không tạo danh sách nhân sự/hồ sơ thật trong Git.

Chạy normal, return/rework/resubmit, không quyền, khác scope, revoke/expiry, stale/retry; owner KD nghiệm thu thao tác và người phụ trách quyền kiểm phạm vi. Nếu chỉ fake/sanitized rehearsal thì ghi rehearsal; không gọi đó là pilot người thật đã được phê chuẩn. Hạn mức Q1, evidence BASE Q3, hiệu lực/thuế/correction Q4/Q8 chỉ là cổng khi pilot mở những hành vi tương ứng; không yêu cầu đóng đồng loạt nếu chỉ draft-review.

## 7. Hợp đồng từ review đến hiệu lực — tách ba batch

| Batch | Điều kiện trước code | Nội dung và kết quả người dùng | Nghiệm thu trọng tâm |
| --- | --- | --- | --- |
| C07 / CTR-002b | Q2-A, reviewer/completer/checklist và đường sửa sai accepted | Action hoàn tất review cho đúng snapshot; hiển thị review complete; không đồng nhất với BASE approved | Đúng actor/version/state, return/complete race, audit, thiếu checklist bị chặn; snapshot bất biến |
| C08 / CTR-003 | Q2-A/Q3 và Q1/Q4 khi xác minh thẩm quyền/tiền phụ thuộc | Record rồi verify/dispute kết quả BASE gắn revision/submission/evidence/hash; state dùng enum hiện có, không thêm `declared` nếu chưa có | Sai revision/hash, bằng chứng thiếu/trùng, quyền record/verify, amount/currency, decision BASE khác verification; không approve thay BASE |
| C09 / CTR-004 | Q1/Q4/Q8, người xác nhận ký/hiệu lực, ngày hồi tố và correction/cancel | Ghi bằng chứng ký/thẩm quyền; xác nhận hiệu lực và phụ lục theo ngày; lịch sử giữ bản trước. Tích hợp chữ ký điện tử nếu cần là scope khác | Approved nhưng chưa ký chưa hiệu lực; ngày trùng/hồi tố/thiếu authority bị chặn; phụ lục thay thế tổng 100→110, không cộng 210; correction/void có audit và tác động downstream |

C07/C08/C09 đều có RFC/action/data/API/UI/test/migration riêng trước triển khai. Q2 đã giải quyết cho fixture DEC-021 không tự chốt completer, verifier hoặc người xác nhận pháp lý.

## 8. Dự án, giao khoán, thực hiện và kế toán

| Batch | Đầu vào | Kết quả code và mục đích | Điều kiện nghiệm thu |
| --- | --- | --- | --- |
| C10 / PRJ-002 + task slice hẹp | Q9, owner và lifecycle/hold/handover; BASE vẫn giữ giao việc chính thức nếu chưa quyết định thay | Quản lý dự án, assignment, kế hoạch/WBS cần thiết; nhiệm vụ có một owner và kết quả/bàn giao. Kế thừa `project.project`/`project.task`, không dùng `active` làm toàn bộ state nghiệp vụ | Chuyển trạng thái, owner/scope, revoke/handover, stale/retry; task complete không thành nghiệm thu tiền. Chọn batch project và task riêng khi scope lớn |
| C11 / ALC-001 | Contract scope hợp lệ, Q7 vượt mẹ và Q8 điều chỉnh | Khoán cha/con theo project/company/currency/basis; cấp 1/2, hồ sơ điều chỉnh | Cấm cycle/sai parent/sai project; policy vượt mẹ đúng; cấp1=70 và con=30+35 thì tổng vẫn 70, không 135; không tạo PO/bill giả cho khoán nội bộ |
| C12 / STL-001a | Phạm vi thực hiện, người lập/xác nhận, Q4/Q8 liên quan | Nhật ký sản lượng theo hạng mục/kỳ/evidence, return/correction | Không trùng kỳ/phạm vi, null/0/âm đúng policy, không tự tạo acceptance/invoice/cash |
| C13 / STL-001b | Biên bản mẫu, bên/người ký, Q4/Q8 | Hồ sơ nghiệm thu gắn sản lượng/phạm vi và evidence; review khác xác nhận | Thiếu ký không confirmed, partial acceptance, correction/void không xóa lịch sử, không tự phát tiền |
| C14 / STL-001c | Terms thanh toán/tạm ứng/giữ lại, Q4/Q8 và Q6 nếu gắn nguồn kế toán | Đề nghị thanh toán, return/resubmit, links acceptance/contract/advance/retention | Không biến request thành cash/paid; tạm ứng theo terms không cần NT giả; không bù/giữ lại hai lần; BASE reference đúng bản |
| C15 / FIN-001 | Nguồn kế toán, Q4/Q6/Q8, chart/tax/currency và module thực có | Bridge sang Odoo Accounting cho invoice/payment/reconcile; reuse `account.move` và object thanh toán tương ứng phiên bản | Partial/multiple payment, reversal/refund, kỳ khóa, duplicate và phân bổ; nguồn missing không thành 0; không tạo ledger kế toán cạnh Odoo |

Tách đường pháp lý của hợp đồng thầu phụ khỏi khoán nội bộ. Không phải dự án nào cũng cần toàn bộ C10–C15 mới dùng được Contracts. Khi mở chuỗi đầy đủ, UAT đi qua một project từ contract→allocation→acceptance/request→accounting, gồm đường bị trả và sửa sai.

## 9. Import, báo cáo và mở các phòng khác

**C16 / IMP-001:** model đích ổn định, Q12 mapping/cutover/reconcile accepted. Lưu batch/file hash/provenance, staging/quarantine, preview lỗi, release qua ORM và đối chiếu; import lại không tạo trùng. Khởi đầu sample giả, sau đó bundle khử dữ liệu được phép. Không chạy macro/external link hoặc import toàn bộ Excel doanh nghiệp khi chưa nghiệm thu mapping. Test mismatch/rollback/re-import/correction và totals theo currency.

**C17 / RPT-001:** Q13 định nghĩa owner/công thức/kỳ/freshness/threshold; dữ liệu nguồn nào chưa có thì báo missing. Aggregate chỉ records/field user có quyền, kiểm cả user metadata A/tiền B, cache invalidation và export. Sản lượng/NT/hóa đơn/cash là các chỉ số khác nhau. Không dựng reporting database hoặc KPI tài chính giả để điền đủ dashboard.

**G7 — các slice theo nhu cầu:** Survey (Q5/Q10, evidence hiện trường), Design/KCS (Q5/Q10, hồ sơ/version/review/release), HR/Documents (Q2/Q11, hồ sơ/bàn giao, tận dụng `hr`/`ir.attachment`), cơ hội/thầu (Q1/Q3, reuse `crm.lead` nếu module phù hợp). Dùng source của phiên bản/edition thực tế; không giả định `documents` hoặc `approvals` có sẵn. Không tạo thư mục/addon rỗng cho đủ chín tên phân hệ.

## 10. Bộ đầu ra bắt buộc sau mỗi batch

1. **Kết quả sử dụng:** một câu nêu actor thao tác được gì, trạng thái/dữ liệu nào thay đổi và demo route/API.
2. **Phạm vi:** task ID/làn/CHG-ID, source fingerprint hoặc Git base+working diff; file thêm/sửa/xóa, model/schema/action/capability/API/route.
3. **Bằng chứng:** lệnh test thực chạy, database/origin, số pass/fail/skip, assertion, log/report/screenshot không secret; phân biệt mock/live/chưa chạy. Exit 0 không thay summary Odoo.
4. **An toàn dữ liệu:** migration/backup/restore khi có schema, test scope/field/file/export, audit/version/idempotency/retry/race cho mutation; không chỉ UI screenshot.
5. **Bàn giao:** status/changelog/architecture/readiness bị ảnh hưởng, workflow finish/check; chưa có xác nhận công ty thì không ghi accepted giả.
6. **Giới hạn:** lỗi còn mở, action chưa mở, phần chưa test, gap với owner/impact/next action; có cần rollback hay không.

Claude ghi `implementation complete`/`tests reported` cho kết quả của mình; phiên chính mới kết luận audit. Một batch không cần thêm test mirror implementation cho text/CSS, nhưng mutation/security/schema phải có test hành vi có ý nghĩa.

## 11. Trạng thái và tiêu chí chuyển batch

| Trạng thái | Nghĩa | Bước tiếp |
| --- | --- | --- |
| PLANNED / SPEC_REQUIRED | Có định hướng, còn action/field/policy cần chốt | Phiên chính hoàn thiện đặc tả của batch gần nhất, không giao prompt mơ hồ |
| READY_FOR_TEST_CODE | Scope/acceptance cho dữ liệu giả đủ; chưa mở người thật | Người dùng giao prompt cho Claude; đây là chỉ thị triển khai batch đó |
| IMPLEMENTED_PENDING_AUDIT | Claude báo đã làm, chưa audit độc lập | Phiên chính review diff + test, ghi finding |
| TECHNICAL_ACCEPTED | Audit/test đạt đúng scope | Có thể làm batch độc lập tiếp; vẫn kiểm business gate trước dùng thật |
| BUSINESS_ACCEPTED / PILOT_READY | Owner đúng scope đã nghiệm thu, ops và charter đủ | Mở pilot đúng phạm vi khi người dùng yêu cầu |
| NEEDS_FIX / BLOCKED | Có bug hoặc thiếu đầu vào bắt buộc | Prompt sửa lỗi hoặc bổ sung decision; không ghép thêm feature |

Không đổi `TECHNICAL_ACCEPTED` thành `PILOT_READY` chỉ vì có nhiều test. Không bắt đóng toàn bộ Q1–Q14 trước một batch không phụ thuộc chúng. Roadmap không ấn định ngày hoàn tất khi chưa biết năng lực/số người/owner; ước lượng từng batch sau khi scope và gap ổn định.

## 12. Cách dùng kế hoạch ở phiên chính

Quy trình làm việc, prompt khung và mẫu yêu cầu audit nằm ở [AI_COORDINATION_WORKFLOW](../AI_COORDINATION_WORKFLOW.md). Prompt code cụ thể gần nhất là [C01 — môi trường test cô lập](../prompts/CLAUDE_C01_ISOLATED_TEST_RUNTIME.md). C02 trở đi cần đặc tả cuối cùng của chính batch trước khi phát prompt; chưa coi các đoạn mô tả trong roadmap là OpenAPI/action matrix hoàn chỉnh.

Sau mỗi kết quả Claude, người dùng quay về phiên chính với task/change ID và nơi lưu source. Phiên chính trực tiếp kiểm workspace được phép, đưa verdict/finding/bằng chứng và prompt sửa hoặc prompt kế tiếp. Không cần người dùng tự kiểm kỹ thuật, không yêu cầu gửi secret/log nhạy cảm qua chat.
