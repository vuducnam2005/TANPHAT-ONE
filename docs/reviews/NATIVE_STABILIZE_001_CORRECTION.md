# NATIVE-STABILIZE-001 — Correction A1/A2/A3

**Kết luận hiện hành 06/11/2026 — CHG-20261106-001:** audit độc lập D1/D2 của correction006 đạt ở tầng đặc tả (`PASS_SPEC`); 001a `READY_FOR_TEST_CODE`. [Audit chấp nhận](NATIVE_STABILIZE_001_D1_D2_ACCEPTANCE_AUDIT.md), [prompt code](../prompts/CLAUDE_UI_CTR_NATIVE_001A.md). Chưa có wizard để nghiệm thu implementation; G7/G8 và Q2/pilot vẫn mở. Kết luận NEEDS_FIX005/chờ audit006 phía dưới là lịch sử.

**Correction delta D1/D2 — CHG-20261105-006: `CORRECTED_PENDING_AUDIT_DELTA_D1_D2`.** Xem [mục 7](#7-correction-delta-d1d2--chg-20261105-006). Đây là tự kiểm, chờ audit đúng hai delta.

**Audit delta độc lập sau correction — CHG-20261105-005:** A3 đạt; A1/A2 còn D1/D2, kết luận `NEEDS_FIX`. [Báo cáo](NATIVE_STABILIZE_001_DELTA_AUDIT.md), [prompt correction hẹp](../prompts/CLAUDE_NATIVE_STABILIZE_001_DELTA_CORRECTION.md). Mục 1–6 dưới là tự kiểm CHG004 được giữ làm lịch sử, chưa thay thế verdict độc lập.

**Change ID:** `CHG-20261105-004` · **Ngày:** 05/11/2026 (Asia/Saigon) · **Trạng thái:** `CORRECTED_PENDING_AUDIT_DELTA`

Báo cáo này là **tự kiểm** của phiên thực thi, trả lời [audit độc lập CHG-20261105-003](NATIVE_STABILIZE_001_INDEPENDENT_AUDIT.md). Báo cáo audit giữ nguyên. Đây không phải technical acceptance độc lập, không phải business acceptance và không cho phép pilot.

## 1. Phạm vi và ràng buộc đã giữ

- **Đã sửa:**
  - đặc tả [UI-CTR-NATIVE-001](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md) cho A1/A2;
  - runner `scripts/native_stabilize001.py` cho A3;
  - test tooling mới `scripts/tests/test_native_stabilize001.py`.
- **Không đổi:**
  - application code, core, React;
  - ACL ứng dụng, chứng từ, user/password/grant thật;
  - hai sửa dashboard F-DASH-01/02 đã audit đạt (`tp_dashboard_privacy`).
- **Chưa tạo:** wizard, form, menu hợp đồng, policy hay capability mới.
- **Runtime:**
  - chỉ chạy test trên clone sở hữu `tp_tanphat_stab001_20261105`/18169, với `--no-http` và `--stop-after-init`;
  - dev 18069 không upgrade, seed hay apply; demo 18109 không dựng;
  - không commit, không push.
- **Baseline:** `ai_workflow check` đạt cho CHG-20261105-003 và không có checkpoint đang mở. `start` cho CHG-20261105-004 chạy trước lần sửa đầu tiên.

## 2. A1 (P1) — owner và phạm vi wizard transient

**Finding:** đặc tả cũ giả định transient mặc định chỉ cho người tạo đọc record. Audit tái hiện được rằng user khác vẫn đọc/sửa được với permission tương đương.

**Căn cứ đã đọc lại trong source Odoo 20:**

- `odoo/orm/models_transient.py:10-15`: `TransientModel` dùng cùng ACL/rule như `Model`, không có owner rule tự động.
- `BaseModel._access_domain` (`odoo/orm/models.py`): `ir.access` có group là permission, được OR; không group là restriction, được AND.
- `odoo/orm/models.py:3857-3861`, `4269-4273`: ORM bỏ `create_uid` khỏi vals create/write.

**Sửa trong đặc tả:**

| Vị trí | Nội dung |
|---|---|
| Dòng 5–8 | Ghi chú correction và trạng thái "chờ audit delta" |
| Mục 9, dòng 166–175 | Bỏ giả định cũ; ghi căn cứ source Odoo 20 |
| 9.1, dòng 177–187 | Danh sách model wizard và wizard-line; chỉ `amount.input` có tiền |
| 9.2, dòng 189–202 | Permission và **restriction** owner (`create_uid`/`wizard_id.create_uid`), company và `project_id access read` cho từng model. Lý do owner phải là restriction: tổ hợp group không mở rộng được quyền. `sudo` chỉ dùng cho một phép đếm |
| 9.4, dòng 235–244 | `create` đọc lại target bằng quyền user; server đặt `project_id`/`company_id`/`key` và bỏ giá trị client gửi |
| 9.5, dòng 246–264 | `action_confirm` không tham số; từ chối `env.su`; kiểm owner và `check_access`; kiểm target contract/revision/project/company; payload chỉ dựng từ record của chính wizard; `_tp_run` kiểm lại capability |
| §14 | AT-09 (tham số thừa, `copy`) |
| §14 | AT-14: user khác gọi read/search/search_read/search_count/read_group/web_read/export/write/unlink/copy/`call_kw action_confirm` trên **mỗi** model |
| §14 | AT-15: tổ hợp `group_user` + `group_manager` + `hr_expense` + `base.group_system`, permission tạm không domain; gỡ restriction thì test phải fail |
| §14 | AT-16: giả mạo `revision_id`/`contract_id`/company, `project_id`/`key` do client gửi, `scope_key` lạ |

## 3. A2 (P2) — bản sao tiền sau revoke/expiry

**Finding:** chỉ chặn ở bước xác nhận là chưa đủ. Bản sao tiền trong transient, payload hay baseline vẫn có thể đọc được sau khi thu hồi.

**Thiết kế đã chọn** (mục 9.3, dòng 204–233):

1. **Không lưu baseline.** Bỏ quy tắc "so với giá trị nạp lúc mở" ở mục 8 (dòng 153–157). Không lưu số tiền hiện tại, tổng hay payload dựng sẵn. Idempotency chỉ lưu HMAC.
2. **Tiền hiện tại chỉ hiển thị qua `current_amount_text`** (`store=False`, `compute_sudo=False`), tính lại bằng quyền user ở mỗi request: `read`, `web_read`, `onchange`, export.
3. **Tiền mới chỉ nằm ở `tp.contract.native.amount.input`.** Model này có restriction `crud` gồm `project access read`, `tp_financial_read_granted` và assignment `active`.
   - Revoke, expiry hoặc tắt assignment có hiệu lực từ request kế tiếp với read/search/web_read/read_group/export/write/unlink/create.
   - User không có `financial_read` không tạo được bản ghi.
4. **`default_get`/`onchange` chỉ trả metadata**, dùng quyền user, không `sudo`.
5. **Xác nhận thành công thì xóa `amount.input`** trong cùng transaction, sau đó `state = done`.
6. **Chống relink:** các trường target bất biến sau create; `copy()` bị chặn. Hợp đồng không đổi được project (`tp_contract.py:74-88`).
7. **Ghi rõ giới hạn:** không thu lại được dữ liệu đã tới trình duyệt.

**Luồng metadata giữ nguyên:**

- Không cần `financial_read`.
- `edit_draft` bỏ khóa `lines` hoặc gửi dòng không có `amount`.
- Backend giữ số tiền (`_parse_edit_draft`, `_tp_touches_money`).

**Sửa thêm:**

- Mục 10 (dòng 275–293): version từ `default_get`, `key` sinh ở server, replay theo user.
- Mục 12 (dòng 318–338): các kênh transient; revoke áp cho mọi bản sao.
- AT-03.
- AT-10 (a/b/c: revoke, expiry, assignment), AT-10d (metadata), AT-10e (không baseline, xóa sau thành công), AT-10f (relink).
- AT-17 (hết hạn tự nhiên).

**Gap mới, không sửa vì ngoài scope:**

- **G7:** rule gốc `line_amount_financial_reader` cho manager có grant nhưng không có assignment đọc tiền. Không đổi ACL ứng dụng; chờ người dùng quyết định.
- **G8:** chưa kiểm chứng việc hết hạn tự nhiên theo ngày có bị cache `_access_domain` giữ lại hay không; cần AT-17.

## 4. A3 (P2) — runner `odoo-tests` không fail

**Finding:** `odoo_tests` in JSON rồi thoát 0 dù process lỗi, summary fail/error, 0 test hay thiếu summary. Log được ghi nối vào cùng một file.

**Sửa trong `scripts/native_stabilize001.py`:**

| Dòng | Nội dung |
|---|---|
| 12 | `import re` |
| 426–432 | Regex theo đúng định dạng Odoo: `odoo/service/server.py:598`, `odoo/tests/result.py:120, 207` |
| 435–450 | `tag_modules`: lấy module từ `--test-tags`, bỏ tag âm |
| 457–511 | `evaluate_test_run` là hàm thuần. `ok` chỉ khi đủ mọi điều kiện bên dưới |
| 514–548 | `odoo_tests`: xem chi tiết bên dưới |
| 602 | `--expect-tests` tùy chọn |
| 620 | `sys.exit(odoo_tests(...))` |

Điều kiện để `evaluate_test_run` trả `ok`:

- process trả 0;
- có đúng một summary, đúng database ở cả prefix lẫn nội dung;
- `failed == 0`, `errors == 0`, `total > 0`;
- mỗi module có trong tag có ít nhất một test chạy;
- số dòng `Starting` bằng `total`;
- không có dòng ERROR/CRITICAL;
- không có dòng summary/test nào cũ hơn thời điểm bắt đầu;
- nếu truyền `--expect-tests` thì `total` phải khớp. Không hardcode 29.

`odoo_tests` làm các việc sau:

- kiểm `target_config('clone')` (owner.json và token trong DB);
- kiểm database, `http_port` của owner và `clone.conf`;
- log mới cho mỗi lần chạy, `odoo-tests/run-<UTC>.log`; từ chối nếu đường dẫn đã tồn tại;
- lưu verdict JSON;
- trả 0 hoặc 1.

**Test tooling** `scripts/tests/test_native_stabilize001.py`, 18 ca:

- **Evaluate:**
  - pass;
  - process exit 1;
  - failed/errors;
  - 0 test;
  - thiếu summary hoặc thiếu log;
  - log cũ;
  - log nối hai lần chạy;
  - sai database;
  - module tag không có test;
  - lệch số `Starting`;
  - `--expect-tests`;
  - dòng ERROR;
  - parse tag.
- **Command:**
  - pass trả 0 với đúng `-d`/`--test-tags`/log;
  - sáu ca lỗi trả 1;
  - `main` propagate exit 1;
  - sai port/database bị từ chối trước khi chạy process;
  - không dùng lại log đã tồn tại.

## 5. Kiểm chứng đã chạy

| Lệnh / bằng chứng | Kết quả |
|---|---|
| `.venv\Scripts\python.exe -m unittest scripts.tests.test_native_stabilize001 -v` | 18/18 OK |
| Mutation trong bản sao ở scratchpad: tắt lần lượt 14 quy tắc (returncode, stale, failed, errors, zero, multiple, wrong DB, missing summary, started mismatch, error lines, return code, `sys.exit`, port, reuse log) | 14/14 bị test bắt (`FAILED`) |
| Toàn bộ test tooling: `test_native_stabilize001`, `native_data003`, `ai_workflow`, `dash_ui001`, `backup_restore`, `ui_demo` | 63/63 OK |
| `ruff check scripts/native_stabilize001.py scripts/tests/test_native_stabilize001.py` | All checks passed |
| `git diff --check` | Không lỗi (chỉ cảnh báo LF/CRLF có sẵn) |
| `evaluate_test_run` trên log Odoo thật cũ: `odoo-tests-run1.log`, `run2.log` (lỗi fixture trước khi sửa), `odoo-tests.log` (pass) | run1/run2 → `tests_errored`, `error_log_lines`; pass → `ok`, 29 test (18 + 11); dùng lại log pass với thời điểm bắt đầu mới → `stale_log_lines` |
| `native_stabilize001.py odoo-tests` trên clone 18169 (đã dừng HTTP; owner/token/port đã kiểm) | **EXIT 0**, 29/29, `tp_dashboard_privacy` 18, `tp_web_home` 11. Log `.local/native-stabilize001/odoo-tests/run-20261105T125703971580Z.log` |
| `odoo-tests --modules tp_web_home --tags /tp_web_home:TpStab001NoSuchClass` (clone) | Odoo trả 0 với "0 tests"; runner trả **EXIT 1** (`no_tests`, `no_tests_for_tag:tp_web_home`). Log `run-20261105T125750710709Z.log` |
| Trạng thái sau chạy | Clone 18169 không listen; dev 18069 vẫn chạy, không bị gọi ghi; demo 18109 không chạy; `revocations.json` `{}`; `clone.conf` giữ smtp 127.0.0.1:9, `max_cron_threads = 0`, `list_db = False`; log nằm trong `.local/` (git-ignored) |

Không chạy test trình duyệt hay ORM probe trong lượt này, vì F-DASH-01/02 không đổi. Không có code wizard nào để test runtime cho A1/A2: kiểm chứng A1/A2 ở lượt này là đối chiếu đặc tả với source, còn test là acceptance cho lượt code sau.

## 6. Giới hạn và bước tiếp theo

- **A1/A2 mới là đặc tả.** Chưa có model/rule để chạy AT-10..AT-17. Lượt code sau phải viết test trước và chứng minh test fail khi gỡ restriction.
- **Hết hạn tự nhiên (G8) chưa kiểm chứng.** Rule gốc cho manager không có assignment (G7) cần người dùng quyết định.
- **Ca fail thật trên Odoo chỉ có zero-test.** Ca test assertion fail thật dùng log cũ run1/run2 cộng unit test. Lý do: không thêm test lỗi vào source.
- **Đề xuất `READY_FOR_TEST_CODE` cho 001a chỉ có hiệu lực sau audit delta A1/A2/A3.** Lượt này không tự ghi technical acceptance độc lập, business acceptance hay pilot.
- **Next action:** audit delta độc lập cho CHG-20261105-004. Sau khi đạt mới phát prompt code UI-CTR-NATIVE-001a, chỉ trên DB test. Áp F-DASH-01/02 lên dev chỉ khi người dùng yêu cầu riêng.
- **Vẫn ngoài scope:** BASE, ký, hiệu lực, thanh toán, upload, grant người thật, TASK-001.

## 7. Correction delta D1/D2 — CHG-20261105-006

**Ngày:** 05/11/2026 (Asia/Saigon) · **Trạng thái:** `CORRECTED_PENDING_AUDIT_DELTA_D1_D2` · trả lời [audit delta CHG-20261105-005](NATIVE_STABILIZE_001_DELTA_AUDIT.md).

**Baseline:** `ai_workflow check` đạt cho CHG-20261105-005, không có checkpoint mở; `start` chạy trước khi sửa.

**Phạm vi:**
- Chỉ sửa đặc tả, acceptance và bàn giao.
- Không sửa `custom_addons/`, `odoo/`, `addons/`, `frontend/`, runner hay API.
- Không mở state, action hay capability mới. A3 đã đạt audit nên giữ nguyên.

### 7.1 D1 — phạm vi trên model con

**Sửa trong [đặc tả](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md):**

| Vị trí | Nội dung |
|---|---|
| Mục 9.2, bảng (dòng 204) | `draft.line`/`return.issue` giữ owner và company, thêm restriction `crud` `[('wizard_id', 'access', 'read')]`. `amount.input` giữ nguyên |
| Mục 9.2 (dòng 207–212) | Lý do không suy phạm vi dòng con từ `wizard_id.create_uid`; cách `access` lấy `_access_domain('read')` của header cho user hiện tại |
| AT-18 (dòng 419) | Chính owner, cùng company, mất project access |

**Đối chiếu căn cứ:**
- `odoo/orm/models.py:4913-4916`: security domain được tối ưu bằng môi trường sudo.
- `models.py:3622-3628`: restriction model cha chỉ tự thêm cho `_inherits`.
- `odoo/orm/domains.py:1926-1950`: `access` hợp lệ cho Many2one, thay bằng `_access_domain(operation)` của comodel với `sudo(False)`.
- Header có restriction owner + company + `project_id access read` (mục 9.2). Vì vậy dòng con theo đúng phạm vi header.
- Probe `.local/native-stabilize001-delta-audit/rollback-probes.json`:
  - `child_after_parent_deny`: `direct_read` true, `search_count` 1;
  - `child_after_explicit_parent_access`: false, 0.

  Kết quả này khớp thiết kế đã chọn.

**AT-18 kiểm:**
- Theo id cụ thể: `read`, `search`, `search_count`, `search_read`, `read_group`, `export_data`, `web_read`, `write`, `unlink`, `create`.
- Nested `web_read` của header không lộ tên dòng hay ý kiến.
- Đối chứng: gỡ **riêng** restriction `wizard_id access read` thì ca âm phải fail.
- Ca này tách khỏi AT-14 (khác owner) và AT-16 (khác company/target).

### 7.2 D2 — tiền hiển thị trong wizard và quyền tiền gốc

**Sửa trong đặc tả:**

| Vị trí | Nội dung |
|---|---|
| Mục 9.3 bước 2 (dòng 228–244) | Guard `_tp_amount_display_allowed()` trên header chạy trước mọi lần tính `current_amount_text`: project `has_access('read')` và `'financial_read' in _tp_capabilities(project, department)`. Thiếu quyền thì rỗng; mất phạm vi thì `AccessError` qua restriction 9.2. Không `sudo()` đọc tiền; metadata không phụ thuộc guard |
| Mục 9.3 bước 3 (dòng 249) | Restriction `amount.input` không phụ thuộc group: manager mất assignment cũng bị chặn |
| Mục 12 (dòng 362–381) | Tách tiền trong wizard (chặn với mọi group), workflow (403 với mọi group) và tiền gốc (theo ACL baseline: thu hồi/hết hạn grant thì chặn; mất assignment chỉ chặn khi mất project access; manager còn grant vẫn đọc được — G7). Bỏ tuyên bố cũ rằng mất assignment luôn chặn tiền gốc |
| AT-10a..AT-10d (dòng 405–408) | Các ca a/b/c/d theo prompt (bảng dưới) |
| AT-10g (dòng 411) | Ca metadata-only giữ nguyên nội dung, đổi ID từ AT-10d để không trùng; thêm `current_amount_text` rỗng |
| AT-17 (dòng 418) | Giữ ca hết hạn tự nhiên, thêm `current_amount_text` rỗng; chưa ghi đạt (G8) |
| G7 (dòng 431) và mục 16 | G7 là quyết định policy riêng chưa chốt; dẫn probe audit delta; không đổi ACL gốc, grant/capability hay backend |

| Ca | Thay đổi | Tiền trong wizard | Tiền gốc |
|---|---|---|---|
| AT-10a | Thu hồi grant | Bị chặn | Bị chặn ở request kế tiếp |
| AT-10b | Hết hạn grant do đổi `date_end` | Bị chặn | Bị chặn ở request kế tiếp |
| AT-10c | Staff mất assignment và project access | Header, dòng con và tiền đều bị chặn | Bị chặn |
| AT-10d | Manager mất assignment, còn project access và grant | `amount.input` bị chặn, `current_amount_text` rỗng, `action_confirm` 403 | Không kỳ vọng bị chặn: ghi nhận đọc được theo ACL baseline (G7) |

AT-10d có đối chứng: patch guard luôn trả `True` thì khẳng định `current_amount_text` rỗng phải fail.

**Đối chiếu căn cứ:**
- `tp_contract_workflow.py:333-346`: `_tp_capabilities` trả tập rỗng khi không có assignment active.
- `tp_project_grant.py:92-112`: `_tp_has_capability` và `_active_grant_domain` kiểm `active` và `date_end >= context_today`.
- `odoo/orm/models.py:3464`: `has_access`.
- Probe `manager_assignment`:
  - `after_revoke`: `original_money_readable` true, `financial_read_in_workflow` false;
  - `after_financial_grant_revoke`: `original_money_readable` false.

  Kết quả này khớp AT-10d và G7.

### 7.3 Kiểm chứng lượt này

| Kiểm tra | Kết quả |
|---|---|
| Code digest (`ai_workflow.snapshot`) | `6abcc74a3541323019060d5935b7aa6d874e98192f2fb9e44fa852d6725d957d`, 234 file, **khớp** CHG-20261105-005 |
| ID acceptance trong đặc tả | Không trùng: AT-01..AT-09, AT-10a..AT-10g, AT-11..AT-18 |
| Link tương đối trong các tài liệu đã sửa | Không có link hỏng |
| `git diff --check` | Đạt |
| `ai_workflow finish/check` | Ghi ở CHANGELOG CHG-20261105-006 |

**Không chạy lại** test ứng dụng, runner hay trình duyệt, vì batch này chỉ sửa tài liệu và code không đổi. Không chạy Odoo, clone hay dev. Không upgrade, seed hay apply dev 18069; không dựng demo 18109; không commit/push.

### 7.4 Giới hạn và bước tiếp theo

- **D1/D2 vẫn là đặc tả.** AT-10a..AT-10g, AT-17, AT-18 chỉ chạy được khi có wizard ở lượt code 001a. Test phải viết trước và chứng minh fail khi gỡ restriction/guard.
- **G7 và G8 vẫn mở.** G7 là policy tiền gốc cho manager không có assignment; G8 là hết hạn tự nhiên với access cache.
- **Phiên này không tự ghi** audit độc lập đạt, technical acceptance, business acceptance hay pilot.
- **Next action:** audit đúng hai delta D1/D2. Khi đạt mới giao code UI-CTR-NATIVE-001a trên DB test, viết AT trước.
- **Không đổi:** F-DASH-01/02 chưa áp dev. BASE, ký, hiệu lực, thanh toán, upload, grant người thật và TASK-001 vẫn ngoài scope.
