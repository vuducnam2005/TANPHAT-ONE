# TANPHAT ONE — Cổng sẵn sàng lập trình

**Ngày:** 28/10/2026. **Trạng thái:** quy tắc làm việc theo yêu cầu người dùng: chuẩn bị rõ đến mức người lập trình chỉ triển khai theo nghiệp vụ đã chốt. Không đồng nghĩa toàn bộ hệ thống hoặc tất cả Q1–Q14 phải đóng trước mọi slice.

## 1. Quy tắc chuyển giai đoạn

Mỗi slice phải qua `Preparation → Business Review → Ready for Code → Implementation → Technical Acceptance → Business Acceptance`. Không bắt đầu **một implementation mới** khi còn mục bắt buộc ở `open/proposed` hoặc chưa có người xác nhận đúng thẩm quyền. Có một ngoại lệ hẹp cho **test-slice maintenance** đã được người dùng cho phép: chỉ sửa lỗi validation/regression hoặc guard trực tiếp của CTR-002a-P1, không thêm state, capability, phạm vi nghiệp vụ hoặc quyền người thật; ngoại lệ này không mở pilot. Thông tin thiếu phải được nêu cụ thể. AI chỉ chọn thiết kế trong phạm vi người dùng đã giao (ví dụ DEC-021); không suy quyết định thiết kế test thành thẩm quyền, hạn mức, thuế, hiệu lực, quyền người thật hoặc quy chế công ty đã ban hành.

Source đã có (CTR-001/CTR-002a) được giữ nguyên; việc đã code trên test không tự đóng cổng nghiệp vụ. CTR-002a.1 đã hoàn tất technical acceptance trên test; kết quả và giới hạn được ghi tại [readiness 7.1.6](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#716-technical-acceptance-ctr-002a1--chg-20261028-020). Không mở thêm action để che các mục chuẩn bị còn thiếu.

## 2. Bộ đầu vào bắt buộc của một slice

| Mã | Điều kiện phải có trước code | Bằng chứng/đầu ra | Trạng thái TP Contracts hiện tại |
| --- | --- | --- | --- |
| RFC-01 | Mục tiêu, phạm vi, trigger, điểm kết thúc, trong/ngoài phạm vi | Một bản scope có version, owner và tiêu chí hoàn tất | Proposed; CTR-002a-P1 đã có scope test, phạm vi nghiệp vụ thật chưa nghiệm thu |
| RFC-02 | Người lập/soát/record/verify BASE; người quyết định và thao tác grant/revoke; scope và bàn giao | Q2-A/Q2-B có người/role được công ty chỉ định, căn cứ và ngày xác nhận; với CTR-002a-P1, chính sách giới hạn test được ghi ở mục 5 | Công ty `open/proposed`; chính sách test được người dùng giao AI quyết định, không phải bổ nhiệm người thật |
| RFC-03 | State/transition, actor/capability, guard, reason, version, audit, notify và đường sửa sai | Action matrix không còn quyết định nghiệp vụ bắt buộc để người code tự suy; self-review và money-review rule được ghi rõ cho CTR-002a-P1 | Thiết kế test đã có; công ty-wide/legal policy vẫn `proposed` |
| RFC-04 | Field, kiểu dữ liệu, required/nullable, unique key, nguồn, validation và quan hệ | Data dictionary + mapping source/model/DTO; null khác 0 | Có baseline; cần đối chiếu hồ sơ thật và chốt các field của slice |
| RFC-05 | Quyền record/field/file/search/export/audit; grant lifecycle; tiền và metadata riêng | Ma trận quyền có case được phép/bị chặn và người xác nhận | Có đề xuất/runtime test; Q2, export, free-text và ledger còn gap |
| RFC-06 | Hồ sơ đại diện đủ chuỗi và ngoại lệ | 2–3 bundle khử dữ liệu có version/hash, người review và kết luận cho implementation nghiệp vụ/pilot | Chưa có bundle thực tế đủ điều kiện; SIM-P1 chỉ mô phỏng. Không chặn maintenance V01/V02/self-review của test slice |
| RFC-07 | Màn hình, thao tác, trường nhập, thông báo lỗi, loading/conflict và bàn giao | Wireframe/flow đủ để triển khai; không tự thêm bước quyết định nghiệp vụ | Có UI test CTR-002a; cần review với nghiệp vụ đã chốt |
| RFC-08 | API command/query, DTO allowlist, error, CSRF, version/idempotency, transaction | OpenAPI và contract checklist khớp action matrix | CTR-002a.1 đã kiểm V01/V02, security, idempotency và transaction trên test; pilot API vẫn chưa mở |
| RFC-09 | Từng yêu cầu có ca nghiệm thu normal/negative/return/correction/retry/concurrent tương ứng | Traceability requirement → action → field → permission → acceptance case | Có ca thiết kế/test; chưa có đối chiếu và ký nhận nghiệp vụ thực tế |
| RFC-10 | Không còn quyết định nghiệp vụ bắt buộc chưa trả lời trong slice | Gap list có kết luận accepted/rejected/deferred, owner, scope, evidence, ngày/version; deferred phải chứng minh không ảnh hưởng slice | Chưa đạt |

`Ready for Code` chỉ được ghi khi RFC-01…10 đạt cho **phạm vi slice được chọn**, owner nghiệp vụ xác nhận và người dùng chọn chuyển giai đoạn. Với maintenance test-slice, ghi `maintenance-authorized` và chứng minh không đổi state/capability/scope; không gọi đó là `Ready for Code` của nghiệp vụ thật. Không dùng checker, AI review, fixture hoặc “test xanh” thay cho xác nhận công ty.

### 2.1. Phân loại cổng hiện tại theo phạm vi

Việc người dùng giao AI quyết định chính sách CTR-002a-P1 đã đóng các lựa chọn thiết kế trong phạm vi **test fixture** theo DEC-020/DEC-021. Không hỏi lại các lựa chọn đó trong RFC-02/RFC-03/RFC-05. Chúng vẫn phải mở cho người dùng thật, pilot và các action pháp lý.

| Phạm vi | RFC đã đủ hoặc được chấp nhận | RFC còn mở | Ý nghĩa |
| --- | --- | --- | --- |
| `CTR-002a-test-maintenance` | RFC-01 scope; RFC-03 state/capability theo DEC-021; RFC-04 data baseline; RFC-05 fixture grant/scope; RFC-07 UI; RFC-08 API security; RFC-09 acceptance cases | Technical acceptance đã đạt: V01/V02, self-review guard, HTTP regression, live UI→API→Odoo và race hai request; nghiệp vụ thật vẫn ngoài phạm vi | Đã triển khai và nghiệm thu kỹ thuật theo CHG-20261028-020; không thêm state, capability, actor thật hoặc nghiệp vụ mới |
| `CTR-002a-test-implementation` | Các RFC trên và DEC-020/021 | Technical acceptance của CTR-002a.1 đã đạt theo mục 2.2–2.3; business acceptance công ty vẫn chưa có | Test slice đạt về kỹ thuật; không phải nghiệm thu nghiệp vụ và không mở pilot |
| `TP Contracts pilot/real-users` | Chỉ có baseline đề xuất và chính sách test tham khảo | RFC-02 Q2-A/Q2-B, RFC-06 bundle thực tế, owner/evidence/sign-off, RFC-10 gap công ty | Chưa được code mở rộng, cấp grant người thật hoặc dùng dữ liệu thật |

### 2.2. Handoff đã thực hiện cho CTR-002a.1

Lượt maintenance đã thực hiện và kiểm chứng đúng vertical slice sau:

1. V01 đạt: enum nhận list/object/null/boolean trả `400 invalid_request`, không làm rò `TypeError` qua controller.
2. V02 đạt: currency rỗng/khoảng trắng/null trả `400 invalid_request`; currency không tồn tại nhưng đúng kiểu trả `422 unknown_currency`; PATCH bỏ currency giữ nguyên, `vnd` chuẩn hóa thành VND.
3. Self-review đạt: `reviewer_id` khác actor gửi ở submit/resubmit; picker loại actor hiện tại; pending submission cũ tự gán không có `return_review` và direct return trả `422 reviewer_ineligible`, không sửa snapshot/lịch sử.
4. HTTP regression đạt cho các ca trên cùng kiểm chứng `401/403/404/409/422`, CSRF, company/project/department scope, idempotency và không phát sinh side effect khi lỗi.
5. Live UI→API→Odoo và race hai request đạt trên instance/database test tách biệt; `tp_tanphat_dev` không bị thay đổi.

Tiêu chí hoàn tất maintenance: test model/API mới đạt; typecheck, unit/build và E2E liên quan đạt; Odoo test trên database test đạt; `git diff --check` và `ai_workflow.py check` đạt; không có thay đổi BASE, ký, hiệu lực, thanh toán, grant người thật, state hoặc capability ngoài DEC-021. Nếu phát hiện quyết định nghiệp vụ mới, dừng code và quay lại Preparation.

### 2.3. Traceability và kết quả CTR-002a.1

| Yêu cầu | Điểm triển khai/kiểm chứng | Kết quả nghiệm thu |
| --- | --- | --- |
| V01 enum chỉ nhận chuỗi hợp lệ | `tp_contract_workflow.py`: `_choice`, `_parse_header`, `_parse_amount`; HttpCase trong `test_contract_workflow_api.py` | Đạt: POST/PATCH với `[]`, `{}`, `null`, `true`, `false` cho `contract_type`, amount `state`, `tax_basis`: 400, đúng `details.field`, request ID, không 500 hoặc side effect |
| V02 currency bắt buộc khi được gửi | `_parse_header`, `_tp_currency`; OpenAPI error descriptions | Đạt: POST/PATCH blank/whitespace/null: 400; unknown currency: 422; PATCH bỏ field giữ nguyên; `vnd` thành VND; không state/version/audit/outbox/idempotency dở |
| SR01 tách người gửi/reviewer mỗi lần gửi | `_tp_submit_review`, `_tp_eligible_reviewers`; `GET /contracts/{id}/reviewers` | Đạt: picker không trả actor có cả submit/review capability; submit/resubmit trực tiếp cho mình trả 422; reviewer khác đủ quyền thành công |
| SR03 không tự return pending cũ | `_tp_available_actions`, `_tp_return_review`; OpenAPI return error descriptions | Đạt: self-assigned pending ẩn action + trực tiếp 422; caller khác reviewer vẫn 403; snapshot/actor/version/lịch sử không đổi; không có repair/reassign |
| Quyền tiền giữ nguyên DEC-021 | Capability/action checks, DTO/financial models, tests quyền hiện có | Đạt: sender thiếu `financial_read` không submit; reviewer thiếu quyền không được chọn; sửa/xóa tiền cần thêm `financial_draft_edit`; không mở file/tiền cho reader |
| Rollback và retry | Workflow transaction, idempotency, audit/outbox | Đạt: ca âm giữ nguyên state/version và số record liên quan; failed key dùng lại với payload đúng; replay không tạo side effect/bản ghi trùng |
| Tích hợp và cạnh tranh | Test instance riêng với database/HTTP/data-dir được kiểm tách dev; actor fixture | Đạt trên `tp_tanphat_ctr002a_verify`: UI→API→Odoo, stale/retry; hai request cùng version cho 200+409 và cùng key cho 200+200 replay; audit/outbox/idempotency chỉ tăng một lần |

Giữ hành vi test hiện có trong maintenance: partner vẫn optional; chưa thêm partner search; submit vẫn yêu cầu đủ lines/amount confirmed và một tax basis; project picker 20 project đầu là hạn chế đã biết. Fixture chỉ dùng project nằm trong danh sách để kiểm luồng này; kết quả đó không chứng minh picker đã phủ toàn bộ project. Các cải tiến này thuộc preparation tiếp theo trước mở rộng, không được lén ghép vào bugfix. Reason bắt buộc khi return; danh sách issue chi tiết là optional. Text reason/issue/fix summary có thể được người đọc metadata thấy, vì vậy fixture không ghi số tiền hoặc thông tin tài chính trong text.

Owner thiết kế test: AI theo ủy quyền người dùng (DEC-021), version `CTR-002a.1-P1`, ngày 28/10/2026; owner công ty/pilot chưa được bổ nhiệm. Đầu vào test là dữ liệu giả và hai actor KD/reviewer khác nhau, thêm actor reader/outside-project/other-company để kiểm âm. Không cần nhập Excel thật hoặc bundle công ty để thực hiện maintenance này.

## 3. Phân công chuẩn bị

AI tự làm: đọc/đối chiếu tài liệu và source; lập scope, RACI đề xuất, action matrix, dictionary, quyền, wireframe, API contract, case nghiệm thu, traceability và gap list; kiểm tính nhất quán và cập nhật bàn giao.

Công ty/người dùng cung cấp hoặc xác nhận: vai trò được phân công, phạm vi ủy quyền, quy tắc quyền/thẩm quyền, hồ sơ khử dữ liệu, định nghĩa tiền/thuế/ngày hiệu lực/ngoại lệ khi slice cần; kết luận từng đề xuất và owner nghiệm thu. AI hỏi từng nhóm nhỏ, nêu ảnh hưởng nếu chưa có câu trả lời, tiếp tục phần độc lập; không hỏi chung chung “có đồng ý hết không”.

## 4. Thứ tự chuẩn bị hiện tại

1. Giữ scope đã triển khai cho TP Contracts: nháp/gửi/trả/sửa/gửi lại; không mở BASE/legal/payment/grant người thật.
2. CTR-002a-test-maintenance đã hoàn tất technical acceptance theo mục 2.2–2.3; không còn backlog V01/V02/self-review/live/race trong test slice này. DEC-020/DEC-021 vẫn chỉ áp dụng cho test fixture.
3. Chốt Q2-A trước (lập/soát/record/verify và scope/căn cứ); Q2-B tiếp theo cho quyền/grant/bàn giao. Thu thập câu trả lời theo từng hành động, không yêu cầu trả lời cả Q1–Q14; đây là cổng pilot/real-users.
4. Đối chiếu bundle thực tế khử dữ liệu; giữ đoạn chưa runtime ở mức walkthrough tài liệu, không nhận mô phỏng là UAT.
5. Với pilot/real-users, hoàn thiện RFC-01…09 và traceability; ghi từng gap RFC-10. Nếu thiếu dữ liệu, nêu chính xác đầu vào/người cung cấp và phần bị chặn.
6. Chủ nghiệp vụ review và ghi kết luận trong [nhật ký readiness 7.1](TP_BIZ002_ACCEPTANCE_AND_READINESS.md#71-nhật-ký-quyết-định-và-nghiệm-thu-điền-khi-review). Chỉ sau đó mới đề xuất mốc Ready for Code cho slice pilot/real-users.

## 5. Chính sách giới hạn CTR-002a-P1 do người dùng giao AI quyết định

Đây là quyết định thiết kế có giới hạn cho vòng nháp/gửi rà soát/trả lại trên **test với fixture**, không phải quy chế pháp lý, không bổ nhiệm nhân sự và không đóng Q2-A/Q2-B cho pilot.

| Hành động | Vai trò và quyền trong slice | Quy tắc cùng/khác người | Quyền tiền và phạm vi | Kết quả cần lưu |
| --- | --- | --- | --- | --- |
| Lập/sửa nháp | Người lập KD được assignment đúng project/department; `contract_draft_edit`; sửa tiền thêm `financial_read` + `financial_draft_edit` | Có thể lập và sửa cùng người | Company/project/department của assignment; không tự cấp grant | Version, actor, thời điểm, audit |
| Gửi rà soát | Người gửi có assignment, `contract_submit`, `financial_read`; server chọn reviewer từ danh sách đủ điều kiện | Người gửi **không được** là reviewer của chính lần gửi đó; áp dụng cả resubmit | Reviewer phải cùng project/department, `contract_review_commercial` + `financial_read` | Snapshot metadata/financial tách ACL, reviewer, hash, version, audit/outbox |
| Rà soát/trả lại | Reviewer được chọn của submission; `contract_review_commercial` + `financial_read`; return cần reason, issue chi tiết optional | Reviewer khác người gửi; không mặc định cấm người này lập draft ở vòng khác | Không sửa payload gốc hoặc BASE/legal/payment | Return reason/issues, actor/time, state/version, notify người gửi |

Nguyên tắc trên không suy quyền từ chức danh, không tạo quyền ký/duyệt BASE, không mở `grant.manage`, `financial.export`, người dùng thật hoặc pilot. CHG-20261028-020 đã đồng bộ backend để từ chối self-review và loại người gửi khỏi reviewer picker; xem kết quả mục 2.2–2.3. Người dùng cũng giao AI chọn **review thương mại có kiểm tra số tiền**, vì vậy submit/review đều cần `financial_read`, còn sửa tiền mới cần `financial_draft_edit`.

Các điểm chưa được người dùng giao quyết định và phải giữ trong RFC-10 trước implementation nghiệp vụ rộng hơn: đối tác có bắt buộc trước submit hay chỉ trước ký; project picker phải search/pagination hay giới hạn có chủ ý; có cho submit khi amount `unconfirmed` hoặc tax basis `mixed` hay không. Đề xuất mặc định để review: đối tác là optional trong draft nhưng phải có trước submit; project picker phải search/pagination; submit chỉ khi amount confirmed và một tax basis. Nếu áp dụng các đề xuất này, ghi version/owner trong readiness trước code.

## 6. Bàn giao khi đạt cổng

Bản bàn giao code phải có: scope/version, quyết định đã chốt, action/state matrix, field/validation, quyền/file policy, API và UI flow, acceptance cases, migration/test-data plan, ngoài phạm vi, gap không ảnh hưởng và tiêu chí hoàn tất. Người code không tự đổi nghiệp vụ; phát hiện mâu thuẫn thì ghi issue và quay lại Preparation cho phần bị ảnh hưởng, không tự chọn default.

Mỗi thay đổi nghiệp vụ sau khi chốt phải có version và impact tới model/API/UI/test; sửa source phải cập nhật status/changelog/workflow theo `AGENTS.md`.
