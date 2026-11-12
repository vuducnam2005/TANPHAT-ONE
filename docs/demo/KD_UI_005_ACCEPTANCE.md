# KD-UI-005 — Acceptance bốn màn Kinh doanh và dự án

Ngày07/11/2026. CHG-20261107-007. [Thiết kế trước code và as-built](../ui/KD_UI_005_BUSINESS_PROJECT_DESIGN.md), [kế hoạch](../ui/KD_UI_005_BUSINESS_PROJECT_REDESIGN_PLAN.md), [hướng dẫn](KD_UI_005_USER_GUIDE.md). Acceptance được tạo trước code với NOT_RUN; kết quả bên dưới là chạy thực. Tự kiểm implementation không là audit độc lập/business acceptance/pilot.

| ID | Expected / kiểm thực tế | Kết quả / evidence |
| --- | --- | --- |
| BP01 | 4 màn đủ field/action, compiled arch, dataset nguyên | PASS clone: signatures không mất field/button/modifier; chỉ thêm search view. Dữ liệu dev đối chiếu ở cổng vận hành dưới đây |
| BP02 | Tìm/lọc/group/sort/pager/cột/mật độ, count/domain cơ hội | PASS: native search, state filter count bằng search_count, nhóm state, sort RPC, checkbox, cột bật/lưu sau reload/reset, Thoáng/Gọn, pager bản ghi; `result-all.json` |
| BP03 | Native tạo/sửa/save/reopen, Text/Char/tags/tab không mất dữ liệu | PASS: tạo cơ hội bằng autocomplete dự án/khách hàng, sửa/title/checklist/căn cứ/tags/tab/save/reopen; `evidence-all.json`, `opportunity-submitted-1440.png` |
| BP04 | Bid/direct/validation/state/retry đúng backend | PASS: thiếu nguồn/hạn thất bại và ở form, đủ dữ liệu prepare→submitted, retry idempotent, direct không có nút nộp và backend từ chối, write state bị chặn; Odoo `test_bid_actions_and_direct_route` |
| BP05 | Grant/assignment/company/project deny, private link giữ | PASS grant/project/private browser và Odoo scope/revoke/forged-command/inverse; sau browser xóa visible tag + lưu, ORM chỉ đọc xác nhận private link còn nguyên (`native-private-preservation.json`); company/assignment bằng probe ORM rollback clone `scope-probes.json` (3/3: revoke assignment, đọc foreign company, chuyển cơ hội sang foreign project bị từ chối). Không đổi rule/grant |
| BP06 | ProjectListController/domain/code unique/assignment đúng nhóm | PASS: View Tasks giữ, manager tạo/sửa/save/reopen dự án có managed/code; assignment chỉ manager, user thường không ghi cấu hình; unique company/code bị từ chối trong `result-s.json` |
| BP07 | 10 action compiled/runtime, context/model/default/leaf đúng | PASS: compiled10 nút đúng một lần,7 ở button_box; cả10 bấm mở native list và action payload đúng project/default/leaf, loại context cha; Odoo binding/sidebar/Tổng quan và deep link |
| BP08 | Save/discard/Stay/Back/Home/pager, failed save ở lại | PASS: invalid save/invalid dirty Home ở lại, cancel phục hồi, pager trước/sau, breadcrumb/Back; AccessError mô phỏng giữ input/không persist; SessionExpired mô phỏng giữ input/không replay/không persist (`result-s.json`) |
| BP09 | Tên dài tiếng Việt/many2one đầy đủ bằng phím/chạm, null | PASS: tên200+ tiếng Việt wrap, preview bằng Enter/chạm dùng display_name sẵn có; readonly native wrap; ngày form đủ năm; giá trị rỗng giữ native, HOOT empty, không thêm tính toán số |
| BP10 | 360/390/768/1024/1440/1920, zoom125/150/sidebar/scroll | PASS: đúng6width ×2list/2form; doc overflow≤1px,3nút chính≥44px; zoom thật DPR1.25/1.5, sidebar/drawer mở/đóng; ảnh `list-*`, `form-*`, `zoom-*` |
| BP11 | Hover/focus/touch/IME/reduced motion, không hover RPC/remount | PASS: same input connected, IME giữ chữ khi chuyển tab, hover0RPC; OSreduce + preference thực tế; HOOT native autocomplete/XSS/empty/callback |
| BP12 | Hồi quy Home/Tổng quan/hồ sơ khác/CRM/Project/Contracts; data/security | PASS: clone270/270hồi quy, dev269/269hồi quy +130/130bốn màn; dữ liệu/quyền/attachment/module/menu và181file addon khác giữ, chi tiết dưới đây |

## Phản hồi thị giác sau bàn giao — CHG-20261107-008

Người dùng cung cấp ảnh danh sách Cơ hội tại18069/action512 và phản hồi “có khác biệt gì đâu”. Đối chiếu trước–sau cùng1440px/dataset13dòng và XML xác nhận khác biệt thị giác nhỏ: width2cột, ngày đủ năm, hover/target, bộ lọc/search riêng; cấu trúc bảng, thứ tự field, toolbar/sidebar giữ. List Dự án chỉ thêm scope class. Hai form chi tiết được bố trí lại nhiều hơn.

**Trạng thái tổng: TECHNICALLY_VERIFIED_VISUAL_REWORK_REQUIRED. Người dùng chưa chấp nhận thiết kế danh sách.** Các dòng PASS BP01–BP12 phía trên ghi chức năng/quyền/responsive đã kiểm, không có nghĩa đã nghiệm thu mục tiêu “làm lại giao diện” của hai danh sách. Báo hoàn tất4màn ở CHG007 là quá mức so với kết quả nhìn thấy. Cần thiết kế lại2list và so ảnh trước–sau cùng viewport/dataset; chưa sửa ứng dụng trong lượt đính chính008. Bằng chứng source/test/backup/apply CHG007 được giữ nguyên.

## Môi trường và vận hành

Baseline CHG006 checker PASS; checkpoint Home đã đóng. Clone own18789/DB`tp_tanphat_kdui005_20261107`, snapshot/restore/data/source/config trong `.local/kd-ui005/`. Ghi fixture chỉ clone; dev18069 verify chỉ đọc. Test/log/ảnh trước–sau và backup ở private operation folder, không credential trong Git. Không commit/push.

## Bằng chứng clone

- A: snapshot `snapshot-20261107T070920Z`, exact restore576bảng/269blob references, neutralize clone; dev PID giữ. Compiled arch `arch-before/`, `arch-after/`; ảnh trước `shots/clone-before/` cho1440/390.
- B rồi C: `batch-b-result.json`28/28 → `batch-c-result.json`39/39. Lần tổng hợp cuối `shots/clone-after/result-all.json`161/161,0console/pageerror. Bổ sung `result-s.json`4/4 (session mô phỏng và unique code). Hai report đều chứa source hash; không cộng các lần chạy lặp vào tổng.
- Odoo: `.local/kd-ui005/odoo-tests/20261107T073444362201Z.log` và JSON:116/116 (`tp_kd_workspace`43 + `tp_contract`73),0failed/error. HOOT `shots/clone-after/hoot-result.json` và `hoot-console.txt`:5/5,15assertions.
- Ruff wrapper/workspace/test_ui_layout/test_credential; `node --check` runner/checks/widget/regression; tất cả XML addon parse đạt. Field/button signature trước–sau giữ behavior, nhóm/quyền/invisible và owning x2many; chỉ whitelist layout/widget/numeric-date được thiết kế.
- RPC trước/sau: `shots/clone-before/baseline-rpc.json`, `shots/clone-after/after-rpc.json`: cơ hội list2→2, form desktop2→1/mobile1→1; dự án list3→3/form1→1. Không có RPC riêng từ hover/disclosure.
- Visual QA đã mở ảnh mobile390 cơ hội và desktop1440 dự án; tên dài, preview, buttonbox, label trên ô, nội dung thật đọc được. Ảnh trước–sau riêng trong folder private, không đưa dataset vào docs/Git.

## Các lần không đạt trong quá trình sửa

- Fixture năng lực riêng tư ban đầu gán organization (đúng policy có thể thấy) → đổi **fixture clone** thành person theo owner, không sửa rule. Native trim title; form tạo đòi khách hàng/công ty → sửa ca kiểm qua autocomplete theo dữ liệu bắt buộc.
- Sass `min(440px,95vw)` không tương thích libsass → width/max-width; HOOT mock thiếu mail models → khai báo mail models và sửa expectation/whitespace. Sau đó chạy xanh trước apply.
- Nút hồ sơ phụ từng đè pager khi tên dài → ButtonBox native một dropdown, breadcrumb có scope. Clone session expiry gián đoạn ở một số lần navigation lặp; mở record bằng numeric action ID và context riêng cho từng action.
- D lần đầu62check rồi timeout tại nút sidebar: tablet mở drawer nên nút đóng khác desktop; sửa driver theo `.o_tp_kd_sb_close`, không sửa ứng dụng.
- H lần đầu16check có một assertion checkbox đọc DOM trước render → chờ settle; tổng hợp cuối161 xanh.
- Hồi quy lần đầu266check xanh nhưng timeout mở Tổng quan mobile; lưu `regression-first-result.json`/`regression-first-evidence.json`. Driver dùng action ID trả về từ `/web/action/load` cho list/Tổng quan rồi chạy lại toàn các section đã chọn. Không dùng partial266 làm kết quả đạt.

## Giới hạn và rollback

Chromium headless, mobile/touch emulation và zoom Chromium thực; chưa Safari/thiết bị thật. AccessError và hết phiên khi save được mô phỏng response trên clone, không làm hết phiên người dùng dev. Không thay core/session. Không diễn tập rollback trên dev trong batch này.

Rollback delta UI dùng:

```powershell
.\.venv\Scripts\python.exe scripts\kd_ui005.py rollback
```

Khôi phục riêng source `tp_kd_workspace`20.0.1.3.0 từ zip snapshot, upgrade chỉ addon này, so rowset và khởi động lại đúng Odoo dev. Giữ database nghiệp vụ; không restore toàn database để quay giao diện. Ctrl+F5 sau rollback. Backup database/filestore chỉ dùng cho phục hồi toàn môi trường khi người dùng yêu cầu rõ vì sẽ ghi đè dữ liệu phát sinh sau backup.

Audit độc lập, business acceptance và pilot vẫn **PENDING**, cùng các gate Q2/owner/evidence hiện hành. Batch không mở BASE/ký/hiệu lực/hạch toán/tiền thật/upload/grant người thật/TASK-001 hoặc sáu phụ lục.

## Apply và đối chiếu dev18069

- Backup sát áp: `.local/kd-ui005/backup-pre-apply-20261107T075325Z`; consistent exported snapshot khi dev chạy, manifest112file rehash,576bảng,269attachment references kiểm blob SHA1/kích thước; `pg_restore --list` đọc được. Snapshot đầu batch đã restore exact owned clone trước khi triển khai. Không đưa config/secret/dump/filestore vào Git.
- `seal` kiểm hash nguồn Odoo + browser-all + session + HOOT + hồi quy + scope-probes; addon chính vẫn bằng baseline trước copy. Áp đúng55file đã kiểm; log `dev-apply-20261107T075409Z.log`, upgrade riêng `tp_kd_workspace` rc0/0ERROR/CRITICAL, `changed_tables {}`. Bản cài20.0.1.4.0.
- Ngay sau áp:37bảng/3.050dòng nghiệp vụ/user/password/Home Action/grant/private relation/ACL/menu trước=sau (không tính write_date/write_uid);257attachment ngoài asset trước=sau;93module installed trước=sau;5bảng nhóm quyền bổ sung trước=sau. `preservation-after-diff.json`, `extended-after.json`.
- `post-apply-source-blobs.json`:55hash file bản áp=bản seal;269blob references kiểm lại SHA1/kích thước đạt. Dev wrapperPID34528/listener20168 sau restart có chủ đích. PG55432PID4228; các clone18169PID27568/18269PID2232/18489PID24164/18589PID23244/18689PID27164 giữ. Clone owned18789PID27396 giữ để đối chiếu.
- Dev browser b,c,d,h chỉ đọc130/130,0console/pageerror; `shots/dev-verify/result-b,c,d,h.json`. Không chạy guard-write g/s trên dev, không tạo/sửa/lưu/seed/cleanup dữ liệu dev. Các thay đổi cột/mật độ/motion chỉ localStorage trong context thử riêng. Đã mở ảnh dev cơ hội1440/dự án390 để review trực quan.
- Hồi quy dev269/269 (`shots/dev-after/regression-result.json`),0console/pageerror; clone270/270 (`shots/clone-after/regression-result.json`). Các section tables/behaviour/roles/leak/overview đều hoàn tất, không lấy partial lần lỗi. Tổng dev399/399chỉ đọc; không chạy lại chain ghi contract/dossier vì không đổi phạm vi đó, backend116test đã phủ workflow liên kết.
- Đối chiếu cuối sau browser: `preservation-verify-diff.json`37bảng/3.050dòng0đổi, `extended-verify.json`257attachment ngoài asset/93module/5bảng nhóm nguyên. `other-addon-source-preservation.json`:181file addon ngoài workspace bằng snapshot. Runtime `processes-final.json` PG/các clone giữ PID; HTTP18069đạt.
- Trạng thái: **IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT**. Technical self-check PASS; independent audit/business acceptance/pilot PENDING. Handoff `CHG-20261107-007`, `git diff --check` + workflow finish/check ghi trong state sau khi tài liệu cập nhật.
