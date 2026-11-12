# UI-CTR-NATIVE-001a — Bàn giao implementation trên DB test

Ngày 06/11/2026 (Asia/Saigon), `CHG-20261106-002`. Thực hiện theo [prompt](../prompts/CLAUDE_UI_CTR_NATIVE_001A.md), [đặc tả](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md) và audit đặc tả D1/D2 `CHG-20261106-001`.

**Kết quả: `IMPLEMENTED_VERIFIED_TEST_PENDING_AUDIT`.** Giao diện native TP Contracts và adapter gọi sáu action CTR-002a, chỉ trên DB test bằng dữ liệu giả. Đây là tự kiểm của phiên thực thi, chờ audit implementation bởi phiên khác; không phải business acceptance hoặc pilot authorization. Người dùng trực tiếp giao phiên chính tiếp tục Claude hết token, ngoại lệ hẹp của DEC-022. Không stage/commit/push.

## 1. Baseline và thay đổi

Resume checkpoint `2026-11-06T01:52:38.396835+00:00`, không xóa/ghi đè. Baseline audit001: 234 maintained code files, digest `6abcc74a3541323019060d5935b7aa6d874e98192f2fb9e44fa852d6725d957d`. Delta Claude có sẵn là test native và import test; chưa có implementation. Working tree có nhiều thay đổi của các batch trước, được giữ nguyên, không stage file nào.

| File | Thay đổi |
| --- | --- |
| `custom_addons/tp_contract/models/tp_contract_native.py` | 5 header transient (`draft`, `amendment`, `submit`, `return`, `rework`), `draft.line`, `return.issue`, `amount.input`; adapter dùng user hiện tại gọi `_tp_run`, không workflow song song |
| `custom_addons/tp_contract/security/ir.access.csv` | Thêm 32 permission/restriction owner/company/project/financial, không đổi ACL gốc |
| `custom_addons/tp_contract/views/tp_contract_native_views.xml` | Menu TP Contracts dưới nền tảng, tích hợp catalog Home; list/search/form chỉ đọc và wizard nghiệp vụ, tài liệu/binary, lịch sử, BASE chỉ đọc |
| `custom_addons/tp_contract/__manifest__.py`, `models/__init__.py`, `i18n/vi.po` | Addon `20.0.1.2.0`, nạp XML/model sau model gốc, bổ sung tham chiếu nhãn tiếng Việt |
| `custom_addons/tp_contract/tests/test_contract_native_ui.py`, `tests/__init__.py` | 22 phương thức Odoo cho 22 AT, AT-12/13 chạy riêng. Sửa fixture export để thực sự đi đến record restriction; kiểm form virtual và version context |
| `custom_addons/tp_contract/tests/test_contract_access.py` | Ca admin không có tiền mặc định chỉ xét project giả mới của test; clone có grant admin explicit từ batch khác, không được coi là quyền mặc định |
| `custom_addons/tp_planning_api/tests/test_contract_workflow_api.py` | N07 gửi body rỗng cho guard kiểm trước body, tránh Windows reset socket do bytes chưa đọc; giữ status/code/no-store và test malformed/non-object JSON, không đổi API |
| `scripts/ctr_native001.py`, `scripts/ctr_native001_ui.cjs` | Seed actor/fixture giả trên clone đã kiểm ownership; browser acceptance, ảnh và kết quả trong `.local` |

Target/project/company/key/result/state do server kiểm soát. Version giữ giá trị form đưa lên; không refresh version trong `create()` để che xung đột. Header/form gốc chỉ đọc, không nới ACL để chuẩn CRUD ghi được. `action_confirm(self)` không nhận action/payload tùy ý; không sudo workflow, không ghi thẳng state/submission/version. Workflow cũ giữ scope/capability, transaction, concurrency, idempotency, audit và outbox.

Tiền hiện tại chỉ compute không lưu bằng quyền user sau guard D2. Tiền mới chỉ nằm ở `amount.input`; global restriction có grant và assignment active, bị chặn từ request sau revoke/expiry. Chỉ có sudo **đếm** dòng input để phát hiện dữ liệu bị rule lọc, không đọc giá trị. Decimal/currency precision được kiểm trước payload; thành công xóa input trong transaction, retry cùng wizard không nhân audit/submission.

Browser đã phát hiện và sửa ba vấn đề: reviewer của form chưa lưu thiếu project; quyền tiền chưa recompute khi chọn project; token readonly không được web_save gửi và cache Odoo khi mở lại cùng revision. Năm form wizard dùng `force_save` cho version; nút workflow mang version hiện trên form; action kết quả có context version mới và bỏ `default_*` cũ để tải lại đúng revision. Token là concurrency, không phải quyền; stale thật vẫn trả cảnh báo tiếng Việt và nút tải lại. AT-04 có kiểm cấu trúc/context cùng ca stale; browser lặp edit/submit sau rework.

Không thêm OWL/SCSS hoặc thay theme; áp dụng `frontend-design` phù hợp nền native. Không sửa core, React, API/OpenAPI/session/login, state/capability hay policy G7.

## 2. Môi trường và cách chạy

- Reuse owned clone `tp_tanphat_stab001_20261105`, HTTP loopback `18169`, PostgreSQL `55432`; owner workspace/token/DB đã được script xác minh trước ORM/upgrade/start/stop. Không snapshot mới từ dev.
- Config `.local/native-stabilize001/clone.conf`, data/filestore `.local/native-stabilize001/data`; cron0, SMTP `127.0.0.1:9`, list_db=False, mail được isolate trong fixture helper. Không đưa config/credential/filestore vào Git.
- Khi mở phiên, dev18069 PID23452 và PostgreSQL55432 đã chạy, khác quan sát audit001. Chỉ đọc trạng thái dev; không start/stop/restart/upgrade/seed/apply dev hoặc demo18109.
- Fixture browser: project164, contract349/revision409; general document61/financial62; actor editor349/reviewer350/metadata351/reader352/outsider353. Bindings `tp_ctr_native001.*`, tên và hợp đồng ghi rõ giả lập. Browser tạo thêm `HD-BROWSER-*` để lưu bằng chứng, không dùng Excel/NAS/người thật.
- URL kiểm thử: <http://127.0.0.1:18169/odoo/tp-home>. Credential chỉ đọc tại `.local/native-stabilize001/ctr-native001/credentials.json`; chọn actor phù hợp, không copy password vào Git/báo cáo.

Chạy từ `C:\TANPHAT ONE`:

```powershell
.\.venv\Scripts\python.exe scripts/native_stabilize001.py stop
.\.venv\Scripts\python.exe scripts/native_stabilize001.py odoo-tests --modules tp_contract,tp_project,tp_planning_api --tags /tp_contract,/tp_project,/tp_planning_api
.\.venv\Scripts\python.exe scripts/native_stabilize001.py start
# Chỉ cần seed khi chưa có fixture; helper reuse binding, không sửa account thật.
.\.venv\Scripts\python.exe scripts/ctr_native001.py
& 'C:/Program Files/nodejs/node.exe' scripts/ctr_native001_ui.cjs
```

Runner sinh log/verdict mới, kiểm DB/summary/module/tag/N>0/fail/error/ERROR, không suy pass từ exit0 của Odoo. Dừng clone HTTP trước mỗi Odoo test. Không dùng lệnh start tổng.

## 3. RED/GREEN và evidence

Tất cả đường dẫn evidence dưới đây tương đối với `C:\TANPHAT ONE`; file `.local` riêng tư, ngoài Git.

| Bằng chứng | Kết quả |
| --- | --- |
| RED trước application implementation: `.local/native-stabilize001/odoo-tests/run-20261106T030839444525Z.{log,json}` | 22 failed, 0 errors do thiếu model/view/menu, không dùng lỗi môi trường/import làm TDD |
| RED bổ sung AT-04 khi browser phát hiện mở lại: `run-20261106T034602692789Z` cùng thư mục | 1 failed, 0 errors: thiếu token version ở form/nút native |
| GREEN hồi quy `run-20261106T033629103164Z`, sau đó `run-20261106T034646034610Z` | Mỗi lượt107/107, contract73 + project12 + planning_api22; gồm native22 |
| Các lượt lỗi được giữ: `run-20261106T033758016959Z`, `run-20261106T035037554726Z` | N07 Windows `WinError10054`, không lỗi assertion nghiệp vụ native; runner trả nonzero. Connection:close thử ban đầu không ổn định nên thay bằng zero-byte body cho pre-body guard |
| Tag gõ thiếu tên method `run-20261106T034534450921Z` | 0 test, runner từ chối; không tính RED hoặc GREEN |
| GREEN cuối `run-20261106T035229356222Z`, lặp sau fix N07 `run-20261106T035740655789Z` | Mỗi lượt107/107, 0 failed/errors/ERROR, đúng DB và đủ3 module. Không lấy lượt có lỗi làm GREEN |
| Browser cuối `.local/native-stabilize001/ctr-native001/browser-result.json` | 42/42, contract967/revision1134, xem §6 |

Đối chứng security chạy trong transaction test và rollback: AT-15 thêm permission rộng vẫn bị owner restriction; gỡ owner restriction thì đọc được. AT-18 gỡ riêng child scope restriction, giữ owner/company thì child read/count mở lại. AT-10d bỏ guard hiển thị thì tiền baseline xuất hiện. Các control xác nhận ca âm có tác dụng, không xfail hoặc nới kỳ vọng để xanh.

AT-17/G8 dùng `freeze_time` 06→07/11, grant hết ngày06. Sau khi warm quyền/tiền ngày06, sang ngày07 chỉ flush/`env.clear()` để mô phỏng transaction/request kế tiếp; **không write grant hoặc gọi `_invalidate_grant_access` khi đổi ngày**. Input và tiền gốc bị chặn, compute wizard rỗng. Đóng G8 kỹ thuật trong phạm vi ca này; không thay policy G7 hoặc tuyên bố đã kiểm thiết bị/người thật.

## 4. Ma trận đủ 24 acceptance

Tên test dưới đây nằm trong `TestContractNativeUi` trừ AT-12/13. PASS là kết quả thực chạy, không chỉ là có mã test. Odoo methods có thêm subtest/negative/control; tổng22 methods không phải24 methods.

| ID | Test/evidence | Kết quả và phạm vi |
| --- | --- | --- |
| AT-01 | `test_at01_menu_list_and_empty_state`; browser Home/list/outsider | PASS: catalog/menu, scope và trạng thái rỗng, entry create theo capability |
| AT-02 | `test_at02_money_follows_grants_in_views_groups_and_exports` | PASS: list không tiền; form/read_group/export/grant theo project; không mặc định manager/admin |
| AT-03 | `test_at03_create_contract_draft`; browser create | PASS: đủ quyền/metadata-only, tiền0/unconfirmed, sai phòng ban/no department/mã trùng |
| AT-04 | `test_at04_edit_draft_version_header_and_state`; browser edit/reentry/stale | PASS: version/audit/header phụ lục/state; token form/force_save/context, browser edit lại sau rework và stale thật |
| AT-05 | `test_at05_submit_and_resubmit`; browser submit/resubmit | PASS: reviewer/không tự rà soát, completeness/fix summary/retry/submission/audit/outbox |
| AT-06 | `test_at06_return_review`; browser reviewer return | PASS: reviewer được giao, lý do, scope snapshot và outbox |
| AT-07 | `test_at07_begin_rework`; browser rework | PASS: bắt buộc lý do, returned→draft và khóa lần sau |
| AT-08 | `test_at08_documents_follow_confidentiality`; browser binary | PASS: financial tên/tệp theo quyền; general theo project; khóa document/attachment sau submit; fixture chỉ test helper |
| AT-09 | `test_at09_direct_rpc_stays_narrow` | PASS: private method RPC, direct protected write, target ngoài scope, tham số thừa/copy bị chặn |
| AT-10a | `test_at10a_revoked_financial_read_closes_wizard_money` | PASS: revoke grant, các kênh đọc/ghi input bị chặn; metadata còn, tiền wizard/gốc đóng |
| AT-10b | `test_at10b_expired_financial_read_closes_wizard_money` | PASS: expiry bằng ORM write date_end; không nhầm với natural expiry |
| AT-10c | `test_at10c_staff_without_assignment_loses_the_wizard` | PASS: staff mất assignment/project; header/child/input/gốc bị chặn |
| AT-10d | `test_at10d_manager_without_assignment_keeps_metadata_only` | PASS: manager còn project/grant, wizard tiền đóng và confirm403; tiền gốc đọc được theo G7; bỏ guard thấy tiền |
| AT-10e | `test_at10e_no_money_baseline_and_cleanup`; browser RPC retry | PASS: schema không baseline/payload tiền, cleanup và done retry, HMAC |
| AT-10f | `test_at10f_targets_cannot_be_relinked` | PASS: immutable header/child; thiếu grant; SQL target lệch bị từ chối trước `_tp_run` |
| AT-10g | `test_at10g_metadata_flow_without_financial_read`; browser metadata | PASS: metadata không cần financial_read, payload không amount, tiền DB giữ nguyên |
| AT-11 | `test_at11_out_of_scope_actions_are_absent` | PASS: không mở BASE verify/review_complete/ký/hiệu lực/hủy/thanh toán |
| AT-12 | `scripts/ctr_native001_ui.cjs`, ảnh và browser-result | PASS: Chromium, viewport360/390/768/1280/1440; zoom thật125/150 ở1280/1440; console/network0 lỗi |
| AT-13 | Full Odoo107, React contracts9 unit+6 mock E2E, OpenAPI validator | PASS, không đổi React/API/OpenAPI; các lượt lỗi và fix test transport được ghi riêng |
| AT-14 | `test_at14_wizards_belong_to_their_owner` | PASS: cả8 model, owner khác ORM/call_kw/read/search/count/group/web_read/export/write/unlink/copy và create child |
| AT-15 | `test_at15_group_combinations_do_not_bypass_the_owner` | PASS: group_user+manager+system, hr_expense user/team approver có trong clone; permission OR và control gỡ owner |
| AT-16 | `test_at16_forged_targets_and_payloads` | PASS: cross target/company/project/key, scope_key và default_amount giả mạo |
| AT-17 | `test_at17_natural_grant_expiry_applies_the_next_day` | PASS: không write/invalidate grant lúc đổi ngày; env/cache request mới, input/gốc/compute đóng |
| AT-18 | `test_at18_owner_without_project_access_loses_child_rows` | PASS: chính owner mất project, direct child và nested header qua các kênh; control gỡ riêng scope mở lại |

## 5. Giới hạn và rollback

G7 policy tiền gốc còn mở: manager còn project access/grant có thể đọc tiền gốc sau mất assignment; wizard chặt hơn theo D2. Không tự sửa ACL gốc. Q2 người cấp grant thật, business acceptance và pilot authorization chưa có. BASE record/verify, review_complete, ký/thẩm quyền ký/hiệu lực, thanh toán/nghiệm thu/giao khoán, hủy revision, đổi reviewer, upload/phân loại tệp, grant thật, TASK-001 và áp dashboard F-DASH dev tiếp tục ngoài scope.

Chỉ Chromium emulation và Chromium page zoom thật, chưa WebKit/Safari, thiết bị iOS/Android hoặc screen reader thật. Chuỗi core Odoo còn một số tiếng Anh. Filestore GC trên Windows có INFO `WinError5` tồn tại từ clone, không phải test summary failure; giữ log, không sửa core hoặc xóa filestore để làm xanh.

Không uninstall `tp_contract`: addon còn chứa hồ sơ/backend cần bảo toàn. Rollback an toàn là dừng clone bằng runner và giữ DB/evidence; nếu cần dựng lại, dùng quy trình clone sở hữu đã kiểm từ snapshot riêng theo yêu cầu mới. Không drop DB, xóa hồ sơ hay restore đè dev trong lượt này. Source chưa commit nên review scope rồi chỉ revert delta UI001a nếu người dùng yêu cầu; không reset/clean working tree đang có thay đổi khác.

## 6. Kiểm cuối và bàn giao

| Kiểm cuối thực chạy | Kết quả |
| --- | --- |
| Odoo trên clone, runner command §2 | `run-20261106T035740655789Z`:107/107,0 failed/errors,0 ERROR; contract73/project12/planning_api22; gồm native22 |
| `python -m unittest discover -s scripts/tests -p test_native_stabilize001.py -q` | 18/18 |
| React từ `frontend/`: `npm.cmd exec vitest run src/features/contracts`; `npm.cmd exec playwright test tests/e2e/contracts.spec.ts tests/e2e/contract-workflow.spec.ts` | 9 unit +6 mock E2E đạt; npm.cmd ở `C:/Program Files/nodejs/`, không sửa React. Log cuối: `.local/native-stabilize001/ctr-native001/react-unit.log`, `react-e2e.log` |
| Ruff các Python thay đổi; XML parse/manifest literal; `node --check scripts/ctr_native001_ui.cjs` | PASS |
| `python scripts/check_contract.py` | PASS OpenAPI, không `--live` vào dev; contract không đổi |
| Browser native trên clone18169 | 42/42; nháp→sửa→trình→trả lại→rework→sửa→trình lại, metadata-only/stale/reload/RPC retry/binary; reader/outsider đúng scope |
| Responsive/zoom | list/form/wizard360/390/768/1280/1440, Chromium zoom thật125/150 ở1280/1440;0 tràn trang sau modal slide ổn định; bảng cuộn trong vùng;0 console/network lỗi ngoài binary403/404 dự kiến |
| Ảnh đã xem ở `.local/native-stabilize001/ctr-native001/` | `draft-desktop.png`, `wizard-360.png`, `revision-390.png`, `list-768.png`, `zoom-wizard-1280-150.png`: đủ nhãn/nút native, không cắt wizard; vùng dài cuộn dọc |
| Link tài liệu và bảng AT | 9 tài liệu link file tồn tại;24 ID đúng tập và không trùng |
| `git diff --check` | PASS, chỉ cảnh báo LF/CRLF sẵn có; không whitespace error |
| Scope nguồn | So checkpoint234→238 maintained files,10 file code thêm/đổi,0 xóa; thêm `vi.po` và browser `.cjs` không thuộc extension checker. Inventory/hash riêng `.local/native-stabilize001/ctr-native001/source-inventory.json`. `git diff --quiet -- odoo addons frontend/src frontend/tests contracts/openapi` không có delta |

Browser lỗi cũ được giữ trong `browser-before-version-context/` và `browser-failure.json`; không dùng chúng thay kết quả cuối. Một ca geometry lúc modal đang slide được sửa trong test bằng đợi500ms trước đo, không sửa CSS hay nới ngưỡng; ảnh cuối đã nhìn trực tiếp. Dữ liệu browser các lượt trước giữ trên clone để audit.

SQL cuối dùng transaction **read-only=on** trên cả dev/clone, evidence `.local/native-stabilize001/ctr-native001/final-runtime.json`: dev `tp_contract` vẫn `20.0.1.1.0`,0 model `tp.contract.native.*`,0 actor `ctr_native001_*`; clone `20.0.1.2.0`,10 model registry gồm2 abstract +8 concrete,5 actor giả. PID file dev là wrapper5068, listener18069 là23452, có sẵn từ09:18:17+07:00 và không đổi trong task. Không coi PID file wrapper là PID HTTP.

**Runtime cuối:** clone18169 để chạy phục vụ review (wrapper25260, HTTP7164), cron/SMTP/list_db vẫn cô lập; dev18069 listener23452 và PG55432 PID3376 giữ nguyên. Dừng clone khi không cần bằng runner §2. Credential private path ở §2, không đưa vào báo cáo.

Bàn giao `CHG-20261106-002` qua `scripts/ai_workflow.py finish` rồi `check`; hash/trạng thái checker ở `docs/AI_WORKFLOW_STATE.json`. Checker chỉ xác nhận source/handoff nhất quán, không thay kết quả kiểm thử/audit.

**Next action:** phiên khác audit implementation, matrix24 AT, log/evidence và D1/D2/AT-17. Không tự áp dev sau test xanh. Technical acceptance độc lập, business acceptance và pilot authorization vẫn ghi riêng.
