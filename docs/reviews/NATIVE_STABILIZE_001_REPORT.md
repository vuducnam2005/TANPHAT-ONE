# NATIVE-STABILIZE-001 — Audit và khắc phục nền Odoo native

**Audit độc lập 05/11/2026:** xem [kết quả CHG-20261105-003](NATIVE_STABILIZE_001_INDEPENDENT_AUDIT.md). Hai bản sửa dashboard đạt kiểm chứng trong scope; toàn batch/đặc tả hợp đồng `NEEDS_FIX` do A1/A2/A3. Kết luận READY ở báo cáo tự kiểm này đã bị audit override; dev chưa apply.

**Correction 05/11/2026:** [CHG-20261105-004](NATIVE_STABILIZE_001_CORRECTION.md) sửa A1/A2 trong đặc tả và A3 trong runner. Đang chờ audit delta; báo cáo tự kiểm 002 bên dưới giữ nguyên làm lịch sử.

**Change ID:** `CHG-20261105-002` · **Ngày:** 05/11/2026 (Asia/Saigon) · **Trạng thái:** `IMPLEMENTED_ON_CLONE_PENDING_AUDIT`

Báo cáo này là **tự kiểm** của phiên thực thi. Nó không phải audit độc lập, không phải nghiệm thu nghiệp vụ và không cho phép pilot. Các bản sửa chỉ được áp dụng và kiểm trên clone cô lập 18169. Dev 18069 chưa nhận bản sửa nào.

## 1. Phạm vi và môi trường

| Mục | Giá trị |
| --- | --- |
| Baseline | `ai_workflow.py start` lúc 2026-11-05T09:48:41Z, 232 file trong phạm vi theo dõi. Working tree đã có thay đổi chưa commit của CHG-20261104-00x/CHG-20261105-001 trước lượt này (Home/MOBILE/DASH), không nhận là của lượt này. |
| Nguồn dev | `tp_tanphat_dev` trên PG 55432, Odoo 18069. Lượt này chỉ đọc. |
| Snapshot | `.local/native-stabilize001/snapshot-20261105T095544Z/`: dump, filestore, source zip, `baseline.json` (fingerprint 538 bảng trong cùng transaction REPEATABLE READ) và `manifest.json` có sha256. Thư mục `failed-snapshot-20261105T095510Z/` của lần chụp đầu bị lỗi được giữ nguyên làm bằng chứng, không xóa. |
| Clone sở hữu | DB `tp_tanphat_stab001_20261105`, HTTP 127.0.0.1:18169, data_dir `.local/native-stabilize001/data`, `dbfilter` đúng một DB, `list_db=False`, `max_cron_threads=0`, `workers=0`, SMTP 127.0.0.1:9 (gửi ra không đi đâu). Ownership ghi tại `owner.json`; token riêng không đưa vào Git. |
| Restore evidence | `restore-evidence.json`: 538 bảng khớp, 249 blob reference, `neutralized=true`. |
| Trình duyệt | Playwright Chromium từ `frontend/node_modules`. **Chỉ là emulation Chromium** (viewport, `isMobile`, touch) và zoom trang Chromium. Không thử trên iPhone/Android, Safari hay Firefox thật. |
| Actor | Fixture NATIVE-DATA-003: admin; Khoa và Nam (điều phối, team approver chi phí); Long, Sơn, Hương, Lan, Khang (nhân viên); Bảo (kế toán). Không đổi mật khẩu, nhóm hay grant của người thật. Chỉ thu hồi tạm quyền dashboard của Khoa trên clone, rồi khôi phục; `revocations.json` hiện là `{}`. |

## 2. Tổng hợp kết quả

| Khu vực | Kết quả trên clone 18169 |
| --- | --- |
| A. Home | 22/22 PASS cho admin, Khoa và Long. Tile khớp đúng tập app có quyền và có nội dung theo ORM (15/12/12). Đã kiểm: tìm không dấu, kết quả rỗng, mở app, nút Home, back, deep link `/odoo/project`. Form không hợp lệ chưa lưu chặn Home, hiện cảnh báo và không lưu. Console và HTTP sạch. |
| B. Dashboard | 8/8 PASS hành vi, 3/3 PASS thu hồi quyền. ORM audit cho 9 actor × 2 dashboard. Số liệu khớp nguồn. Đã kiểm: chặn stale response, lỗi và thử lại, drilldown kiểm lại quyền, thu hồi chặn mọi kênh. Hai lỗi P3 đã sửa (F-DASH-01, F-DASH-02). |
| C. Responsive | 30/30 PASS tại 360/390/768/1280/1440 cho Home và hai dashboard. 14/14 PASS zoom 125/150% tại 1280/1440. Không tràn ngang cấp trang. Bảng cuộn trong vùng riêng khi hẹp. Viewport cho phép phóng to. |
| Phiên | 1/1 PASS: đăng xuất làm cookie cũ mất hiệu lực ở nơi khác (RPC trả `SessionExpiredException`, trang chuyển về `/web/login?redirect=…`). |
| D. Liên kết dữ liệu | Nối theo ID/FK, không có model project thứ hai. Có quan sát dữ liệu (mục 5), không sửa dữ liệu dev. |
| TASK-001 | Vẫn chặn. Probe trên clone: Long đọc được task 57, ghi bị `AccessError`, state giữ `01_in_progress`. Đã ghi đề xuất và câu hỏi vào RFC. |
| Tổng UI probe | `{"passed":78,"failed":0}`; 48 ảnh trong `.local/native-stabilize001/ui/`. Đã xem trực tiếp các ảnh 360px, lỗi có lọc, Bảng tổng hợp của Long và deep link sau thu hồi. |

## 3. Finding đã sửa

### F-DASH-01 — Thẻ chi phí không nói rõ phạm vi trạng thái (P3, nhãn số liệu)

- **Ảnh hưởng:** Thẻ “Số đề nghị chi phí trong phạm vi” và “Tổng giá trị đề nghị chi phí” không có dòng phụ. Backend chỉ tính `draft/submitted/approved`, nhưng thẻ không nói số này loại Đã ghi sổ, Đang/Đã thanh toán và Bị từ chối. Người xem có thể hiểu nhầm đây là số đã chi.
- **File/dòng:** `custom_addons/tp_dashboard_privacy/models/dashboard_report.py:20-21` (`EXPENSE_SCOPE`), `:167-170` (`detail` của hai thẻ).
- **Actor/môi trường:** admin và Bảo (có quyền dashboard tài chính ID 6), clone 18169.
- **Tái hiện:** mở “Tổng quan hóa đơn và chi phí” rồi xem hai thẻ chi phí. Phần `detail` trống; chỉ tiêu đề trang ghi chung “Chưa phản ánh doanh thu hoặc thu/chi thực tế”.
- **Kỳ vọng và căn cứ:** Yêu cầu NATIVE-STABILIZE-001 tách “approved expense ≠ paid”. Định nghĩa backend `STATES` ba trạng thái và [runbook dashboard](../demo/dashboards/README.md) “Số đề nghị chi phí … `draft/submitted/approved`”.
- **Thực tế trước sửa:** thẻ không có giải thích phạm vi.
- **Sửa:** chỉ thêm `detail`. Không đổi tên chỉ số, công thức hay giá trị. Thẻ tổng có thêm “Chưa phải số đã chi.” ở đầu.
- **Kiểm chứng sau sửa:**
  - Test hồi quy `test_expense_metrics_exclude_refused_and_state_their_scope` dùng 3 chi phí giả lập: draft 10, approved 20, refused 40. Kết quả `expense_count = 2`, các trạng thái (10, 0, 20), drilldown chỉ có 2 ID, `detail` có “không gồm … Bị từ chối”.
  - UI probe “finance metrics show confirmed scope, values unchanged”: vẫn 4 hóa đơn, 801.000.000 ₫, 6 đề nghị, 7.160.000 ₫.

### F-DASH-02 — Lỗi tải khi đang lọc dự án lại hiện “Tất cả dự án được phép” (P3, phạm vi hiển thị sai)

- **Ảnh hưởng:** Khi tải lỗi, danh sách dự án bị xóa (đúng, để không giữ tên cũ), nhưng tóm tắt và ô chọn lại ghi “Tất cả dự án được phép”, trong khi request và nút Thử lại vẫn mang `project_id` đã chọn. Người dùng thấy sai phạm vi đang xem.
- **File/dòng:** `custom_addons/tp_dashboard_privacy/static/src/dashboard.js:124-135` (`unlistedProject`, `filterSummary`), `custom_addons/tp_dashboard_privacy/static/src/dashboard.xml:99`.
- **Actor/môi trường:** admin, dashboard ID 6, clone 18169. Lỗi được giả lập trong Playwright bằng route chặn RPC report.
- **Tái hiện:** chọn DA-2026-001, cho lần tải kế tiếp lỗi, rồi xem tóm tắt bộ lọc và ô Dự án.
- **Kỳ vọng:** trạng thái lỗi vẫn nói đúng bộ lọc đang áp dụng và không làm lộ tên dự án cũ.
- **Thực tế trước sửa:** tóm tắt ghi “Tất cả dự án được phép · toàn bộ thời gian”.
- **Sửa:** khi dự án đã chọn không còn trong danh sách, tóm tắt và option hiển thị “Dự án đã chọn” (không có tên). Thử lại giữ nguyên bộ lọc.
- **Kiểm chứng sau sửa:**
  - UI probe “error state keeps truthful project filter summary” cho kết quả `Dự án đã chọn · toàn bộ thời gian` và select giữ giá trị 8. “retry restores project data” PASS.
  - Ảnh `ui/dash6-error-with-project.png` đã xem.
  - `dashboard.js` qua `node --check` (ESM). OWL template biên dịch trong bundle không lỗi console.

Hai bản sửa đều nằm trong file chưa được commit từ batch DASH-UI-001 (`dashboard_report.py`, `static/`, `test_dashboard_report.py` là untracked trước lượt này). Phần do lượt này thêm có comment `NATIVE-STABILIZE-001`.

## 4. Gap chưa sửa và lý do

| Mã | Mức | Actor | Quan sát (clone 18169) | Căn cứ / lý do chưa sửa | Đề xuất |
| --- | --- | --- | --- | --- | --- |
| F-HOME-01 | P3 (chính sách) | Khoa, Long (mọi `base.group_user`) | Home có tile “Ứng dụng Odoo” (`base.menu_management`). | Odoo chuẩn: `addons/base_install_request/views/ir_module_module_views.xml:14-15` gán menu cho `base.group_user_regular` để nhân viên gửi yêu cầu cài module. Ẩn đi là đổi chính sách, chưa có quyết định; không sửa `addons/`. | Người dùng quyết định có ẩn cho nhân viên không. Nếu ẩn thì override `group_ids` trong custom addon và thêm test Home. |
| F-HOME-02 | P3 | Long và các nhân viên không có dashboard | “Bảng tổng hợp” mở ra trang “Không có bảng điều khiển nào khả dụng”, vẫn thấy menu “Cấu hình” và nút “Share” (ảnh `ui/home-dashboards-long.png`). Không lộ dữ liệu: danh sách dashboard rỗng, ORM `AccessError`. | Menu gốc `spreadsheet_dashboard` theo nhóm chuẩn. Ẩn app theo việc có dashboard hay không là quy tắc động, chưa có đặc tả. | Quyết định cùng F-HOME-01: ẩn app cho người chưa được cấp dashboard, hoặc giữ và thêm hướng dẫn. |
| F-DASH-04 | P3 | Khoa sau khi bị thu hồi | Deep link tới dashboard 5 hiện “An error occurred while loading the dashboard” (tiếng Anh). Console có `403 /spreadsheet/dashboard/data/5` và lỗi parse JSON vì server trả HTML. | Lỗi ở action dashboard core khi nhận 403. **Không lộ dữ liệu:** refresh, drilldown, report, đọc raw, download và reload đều bị chặn (probe revocation PASS). Sửa cần patch OWL core trong custom addon; mức ưu tiên thấp hơn lỗi số liệu. | Task nhỏ riêng: patch hiển thị “Không đủ quyền” tiếng Việt cho 403, kèm test HOOT/Playwright. |
| F-I18N-01 | P4 | Mọi actor | Còn chuỗi tiếng Anh: nút “Share”, thông báo lỗi dashboard core, tile “Project” (app Project chuẩn) đứng cạnh “TP Projects”. | Chuỗi từ core/addon chuẩn; DB này chưa có bản dịch. Không sửa `addons/`. Việc tồn tại cả “Project” và “TP Projects” là câu hỏi đặt tên theo `TP_PRODUCT_NAMING.md`. | Bổ sung bản dịch hoặc override nhãn trong custom addon sau khi người dùng chốt tên. |
| F-UI-01 | P4 | admin, Bảo, Khoa (desktop) | Ở ≥1280px, nút số trong ô bảng dashboard chỉ rộng bằng chữ số, 7–18 × 26 px (`dashboard.xml:140`). Ở 360–768px không có target nhỏ. | Chuột trên desktop vẫn dùng được, ô bảng rộng nên có thể đạt ngoại lệ khoảng cách WCAG 2.5.8; chưa đo đầy đủ. Không phải lỗi chặn. | Thêm `min-width`/padding cho nút trong ô khi làm lượt UI dashboard kế tiếp. |
| F-UI-02 | P4 | Mọi actor | Ô ngày hiện placeholder `mm/dd/yyyy` của Chromium dù context `vi-VN`. | Placeholder do trình duyệt vẽ theo locale hệ điều hành; giá trị gửi backend vẫn là ISO. Chưa kiểm trên trình duyệt thật của người dùng. | Kiểm lại trên máy thật; nếu cần thì dùng date picker của Odoo. |

Không phát hiện lộ dữ liệu, lỗi quyền, mất dữ liệu hay sai số liệu trong phạm vi đã kiểm.

## 5. Liên kết dữ liệu (chỉ quan sát, không sửa dữ liệu)

| Dự án | CRM (`crm.lead.tp_project_id`) | Task | Dòng giờ | Chi phí (analytic) | Hóa đơn (analytic) |
| --- | --- | --- | --- | --- | --- |
| DA-2026-001 | 11 | 8 | 8 | 7, 8 | 4 |
| DA-2026-002 | 13 | 7 | 7 | 9, 12 | 5 |
| DA-2026-003 | 15 | 6 | 5 | 10 | 6 |
| DA-2026-004 | 18 | 7 | **0** | 11 | 10 |
| DEV-001, DEV-002 | — | 0 | 0 | — | — |

- Mọi chiều đối chiếu đều rỗng: không có task khác company, timesheet thiếu task, task và project lệch, analytic lệch, CRM và partner/company lệch, hay hóa đơn và partner lệch.
- Liên kết CRM → Project chỉ có một chiều (`tp_project_id` trên lead). Project không có trường ngược.
- 6/10 lead chưa gắn dự án (ID 12, 14, 16, 17, 19, 20; giai đoạn “Mới” hoặc “Đủ điều kiện”). Đây có thể là trạng thái hợp lệ trước khi thắng thầu; cần chủ nghiệp vụ xác nhận, không suy diễn.
- DA-2026-004 có 7 task nhưng 0 dòng giờ. Đây là đặc điểm của bộ dữ liệu mẫu, không phải lỗi liên kết.
- Không có model project thứ hai. `tp.project.assignment` và `tp.project.grant` là phần mở rộng phân quyền của `project.project`. Không nhân bản fixture.
- Dashboard tài chính tính lại theo ORM khớp UI: hóa đơn 801.000.000 ₫ (4 bản nháp, chưa thuế 801.000.000 ₫); chi phí 810.000 + 1.250.000 + 5.100.000 = 7.160.000 ₫ (6 đề nghị). Đây là hóa đơn **nháp**, không phải doanh thu đã ghi sổ hay tiền đã thu; chi phí là đề nghị, không phải tiền đã chi.
- Dashboard điều phối: 4 dự án, 28 task, 4 hoàn tất, 84,00 giờ. Khớp truy vấn superuser cho admin, Khoa và Nam; payload không có tiền. Long, Sơn, Hương, Lan và Khang bị `AccessError` ở cả hai dashboard. Khoa, Nam và các nhân viên bị chặn dashboard tài chính; chỉ admin và Bảo đọc được.

## 6. TASK-001

- **Không đổi code hay quyền.** `task_platform_write_scope` vẫn chỉ cho `tp_core.group_manager` ghi task thuộc dự án được quản lý. Không đảo test từ deny sang allow và không gọi là đã sửa.
- **Probe clone** (`task001-clone.json`): Long đọc task 57 (DA-2026-001) OK; ghi `state` bị `AccessError`; state sau vẫn `01_in_progress`; transaction rollback.
- [RFC TASK-001](../architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md) có thêm mục “Đề xuất cụ thể để quyết định”:
  - action backend `action_tp_report_progress(target_state, expected_write_date, reason=None)` kiểm assignment, state cho phép, version và lý do, ghi lịch sử, không mở `write` chung;
  - 7 câu hỏi mở cho người dùng hoặc chủ nghiệp vụ. Trạng thái RFC vẫn PROPOSED.

## 7. Đặc tả TP Contracts native

[TP_UI_CTR_NATIVE_001_SPEC.md](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md) gồm:

- Phạm vi 001a; menu và danh sách; form hợp đồng, bản gốc/phụ lục, dòng, số tiền và tài liệu.
- Ma trận actor, field, tiền và tệp.
- Nút → wizard → `_tp_run` với đúng state và method hiện có.
- Version, idempotency, audit; RPC native; lỗi; kênh lộ dữ liệu; responsive và tiếng Việt.
- AT-01..AT-13 và gap G1–G6.

Kết luận: **READY_FOR_TEST_CODE cho 001a** (đọc, tạo/sửa nháp, phụ lục nháp, gửi, trả lại có lý do, mở lại sửa, gửi lại). **Chưa sẵn sàng** cho tải tệp lên (G1: chưa có action/capability upload), hủy, đổi người review và mọi bước BASE, hoàn tất review, ký, hiệu lực hay thanh toán. Không thêm state hay capability mới. Q2 vẫn chặn người dùng thật và pilot.

## 8. Thay đổi trong lượt

| File | Loại |
| --- | --- |
| `custom_addons/tp_dashboard_privacy/models/dashboard_report.py` | F-DASH-01: `EXPENSE_SCOPE` và `detail` |
| `custom_addons/tp_dashboard_privacy/static/src/dashboard.js`, `dashboard.xml` | F-DASH-02 |
| `custom_addons/tp_dashboard_privacy/tests/test_dashboard_report.py` | 1 test hồi quy mới |
| `scripts/native_stabilize001.py`, `scripts/native_stabilize001_ui.cjs` | Tooling: snapshot, clone, start/stop, audit, dev-drift, odoo-tests, task001, revoke/restore; UI probe |
| `docs/architecture/TP_UI_CTR_NATIVE_001_SPEC.md` | Đặc tả mới (không code) |
| `docs/architecture/RFC_TASK_001_MANAGED_TASK_PROGRESS.md` | Thêm đề xuất và câu hỏi |
| `docs/reviews/NATIVE_STABILIZE_001_REPORT.md`, status, changelog, roadmap, runbook dashboard | Bàn giao |

Bảo mật:

- Không đổi ACL, rule, group, grant, sudo hay route.
- `sudo()` mới chỉ có trong fixture test để tạo dữ liệu giả lập; report vẫn chạy bằng quyền của user test.
- Không đổi API, OpenAPI hay React. Không sửa `odoo/`, `addons/`. Không chạy React build vì không đụng legacy React.

## 9. Kiểm thử đã thực chạy

| Kiểm | Lệnh/nguồn | Kết quả |
| --- | --- | --- |
| Ruff | `ruff check custom_addons/tp_dashboard_privacy custom_addons/tp_web_home scripts/native_stabilize001.py` | All checks passed |
| XML | parse 5 file XML của `tp_dashboard_privacy` và `tp_web_home` | OK |
| JS | `node --check` cho `scripts/native_stabilize001_ui.cjs` và `dashboard.js` (ESM) | OK |
| Python tooling | `py_compile scripts/native_stabilize001.py` | OK |
| Odoo tests | `native_stabilize001.py odoo-tests`: `-u tp_dashboard_privacy,tp_web_home --test-enable --test-tags /tp_dashboard_privacy,/tp_web_home` trên clone đã dừng | `0 failed, 0 error(s) of 29 tests` (18 `tp_dashboard_privacy`, 11 `tp_web_home`). Hai lần chạy trước fail do fixture của chính test mới (thiếu quyền tạo employee, thiếu product); đã sửa fixture, log giữ ở `odoo-tests-run1.log` và `odoo-tests-run2.log`. |
| Browser/security | `native_stabilize001_ui.cjs` toàn bộ section trên clone | 78 PASS / 0 FAIL |
| ORM security | `native_stabilize001.py audit` (`audit-clone.json`) | 9 actor × Home/dashboard/drilldown; không có `drill_mismatch` |
| TASK-001 | `native_stabilize001.py task001` | Deny giữ nguyên |
| Dev drift | `native_stabilize001.py dev-drift` | 538 bảng; chỉ `bus_bus`, `mail_presence`, `res_device_log` đổi số dòng hoặc nội dung |
| Diff | `git diff --check` | OK (chỉ cảnh báo LF/CRLF) |

**Giới hạn:**

- Chromium emulation, không có thiết bị thật.
- Đăng nhập trong probe đi qua `/web/session/authenticate`, chưa gõ form đăng nhập.
- Hết phiên được kiểm bằng logout ở nơi khác, chưa chờ hết hạn theo thời gian.
- Không chạy lại test `tp_core`, `tp_project`, `tp_contract` vì không đổi.
- Không có HOOT test cho F-DASH-02; kiểm bằng Playwright.
- Không kiểm export/share bằng UI ngoài phần đã có trong probe revocation và runbook DASH.

## 10. Dev 18069

- Không upgrade, seed, apply hay sửa dữ liệu. `GET /web/login` trả 200.
- So với snapshot, chỉ 3 bảng phiên/hiện diện tăng dòng (`bus_bus` 3590→3596, `res_device_log` 345→347, `mail_presence` đổi nội dung). Không bảng nghiệp vụ nào đổi.
- Dev **vẫn chạy code cũ**: F-DASH-01 và F-DASH-02 chưa có trên dev.

## 11. Mở lại môi trường thử

```powershell
.\.venv\Scripts\python.exe scripts\native_stabilize001.py start
# mở http://127.0.0.1:18169/web/login bằng actor fixture (mật khẩu trong thư mục private, ngoài Git)
.\.venv\Scripts\python.exe scripts\native_stabilize001.py stop
```

Script từ chối chạy nếu `owner.json` không khớp DB và cổng 18169. Clone đang **dừng**. Snapshot, clone và evidence giữ trong `.local/native-stabilize001/`.

## 12. Bước tiếp theo đề xuất

Audit độc lập lượt này cùng DASH-UI-001. Sau khi đạt, người dùng quyết định có áp F-DASH-01/02 lên dev 18069 bằng snapshot → upgrade `tp_dashboard_privacy` → probe chỉ đọc hay không. Không áp trong lượt này.
