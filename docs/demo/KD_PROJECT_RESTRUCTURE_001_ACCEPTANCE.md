# KD-PROJECT-RESTRUCTURE-001 — Báo cáo kiểm chứng và cổng nghiệm thu

Ngày 09/11/2026 (Asia/Saigon). Căn cứ: [prompt triển khai](../prompts/CLAUDE_KD_PROJECT_RESTRUCTURE_001.md), [thiết kế và 16 AT trước code](../ui/KD_PROJECT_RESTRUCTURE_001_DESIGN.md), DEC-030/DEC-032. Báo cáo này ghi bằng chứng kỹ thuật hiện có; không ký thay chủ nghiệp vụ.

**Kết luận hiện tại: `IMPLEMENTED_VERIFIED_DEV_PENDING_BUSINESS_VISUAL_PILOT`.** Đã triển khai20.0.1.8.0 lên dev18069 sau đủ cổng kỹ thuật, audit quyền độc lập và backup/restore mới. Hai khu vực dùng cùng project ID, đầy đủ backend/quyền/migration/UI. Năm tài khoản hiện có smoke chỉ đọc đạt; quyền/owner thật giữ. Business/visual/pilot và V2/người thật vẫn riêng.

## Các chặng đã thực hiện

| Chặng | CHG | Kết quả |
| --- | --- | --- |
| S0 | CHG-20261109-010 | Inventory/design/16AT trước code, baseline/snapshot/restore và mapping dry-run14project25CRM. |
| S1 | CHG-20261109-011 | F1–F3 tái hiện trước sửa3fail/4 rồi4/4, full168; final audit trong S4 đóng correction đúng scope. |
| S2 | CHG-20261109-012 | Model/capability/quan hệ/nhật ký, targeted8/full176. |
| S3 | CHG-20261109-013 | Hai landing/detail/list/menu,9yêu cầu, source riêng và final185/HOOT20/UI61+29. |
| S4 | CHG-20261109-014 | Independent110, final seal, backup/restore mới, gatedapplydev, preservation83table4529row, smoke53/5login, guide/ảnh thật. |


## 1. Nguồn, runtime và phạm vi kết luận

| Hạng mục | Trạng thái được chứng minh |
| --- | --- |
| Nguồn triển khai | `C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/`; addon `tp_kd_workspace` **20.0.1.8.0** |
| Source seal | SHA256 cây canonical manifest: `89c17f28511daceaf3f064faecad6064517756c50de04dcab8d52d827f0df927`; xem [seal][seal] và [kết quả Odoo cuối][odoo-result]. Digest là cả cây custom_addons của workspace, không chỉ một file/addon. |
| Nơi kiểm chức năng | Clone owned `tp_tanphat_kdproject001_20261109`, HTTP **19489**, PostgreSQL **55432**; cron/integrations đã neutralize. Fixture mới chỉ dùng trên test. |
| Root/dev hiện tại | Root `custom_addons/tp_kd_workspace` và dev **18069 / tp_tanphat_dev** hiện **20.0.1.8.0**. Source test=seal=applied `89c17f…f927`; baseline root trước apply `421349…d504` được giữ đến lúc gate đạt. [Apply](<C:/TANPHAT ONE/.local/kd-project-restructure001/dev-apply-result.json>) xác nhận58file đúng addon; PostgreSQL PID13900 giữ, dev wrapper25404/listener10096. Clone19489 đã dừng sau kiểm; DB/source/fixture/evidence giữ để audit, không drop dữ liệu. |
| Hồi quy cuối | **185 test, 0 failed, 0 error**; source trước/sau test không đổi. Không dùng số test của batch trước thay kết quả này. |
| Ngoài kết luận | Không phê duyệt toàn KD-ROLE-V2/TASK-001, không cấp quyền/reassign người thật, không xác nhận BASE/ký/hiệu lực/hạch toán/thanh toán/chất lượng nghiệm thu. Không commit/push. |

## 2. Chín yêu cầu → implementation/action/AT

Các link source bên dưới trỏ **workspace kiểm thử**;58file delta đã áp đúng vào root/dev18069 và digest hai cây trùng nhau. [Source chính][source], [view/action/menu][views], [perspective backend][perspective], [OWL perspective][owl], [task command][tasks] và [test chức năng][functional-tests] là đường kiểm trực tiếp.

| # | Yêu cầu | Kết quả triển khai và action có thể review | AT / bằng chứng |
| --- | --- | --- | --- |
| 1 | Dùng Dự án thay Cơ hội trong luồng KH-KD | Một danh mục `project.project`; `action_projects` mở danh mục Dự án. `crm.lead` giữ hồ sơ/lần tham gia và link nguồn; không tạo project thứ hai. Entry cũ có đường sang hai góc nhìn. | A01/A02; view/action và UI project list. Native deep link/detail reload và Back đã kiểm; form/action cũ giữ đường chuyển. |
| 2 | Chủ đầu tư | `kd_investor_id` riêng; giữ `partner_id` là bên ký thương mại. Test investor A/bên ký B với CRM–Project–Contract cùng nghĩa; Overview field partner cũ ghi “Bên ký thương mại”. | A03; `test_investor_a_counterparty_b_same_project`; [ảnh danh mục][shot-projects]. |
| 3 | Tình trạng dự án | `kd_lifecycle`: Đang theo dõi/Đang thực hiện/Tạm dừng/Kết thúc, độc lập CRM bid và review state. `action_kd_status` mở command với quyền, lý do, version/key; reopen có capability riêng. | A08; status/stale/retry/reopen regression; [ảnh command][shot-status]. |
| 4 | Người phụ trách trước một hạn | Package list dùng `owner_id` trước `deadline`; CRM giữ hạn chuẩn bị/nộp cũ, không tách hai hạn. Native table tools giữ filter/paging/cột. | A05; UI check “owner precedes single deadline”; [ảnh gói][shot-packages]. Project/package và parties/history/amount list đã kiểm tìm/lọc/cột/số dòng; fixture21+21 chứng minh offset10/20. |
| 5 | Cập nhật tình trạng/ghi chú/lịch sử | `action_kd_status`, `action_kd_note`, `action_kd_history`; `tp.project.update` append-only/correction. Task có `tp.task.update` trước/sau; nút native lưu thay đổi thật trên clone. | A08/A09; event actor/version/snapshot/retry tests; UI status+note; [ảnh lịch sử][shot-history]. Audit quyền cuối PASS, xem mục7. |
| 6 | Đối tác nhiều bên, nhiều vai | `tp.project.participation` tái sử dụng `res.partner`, scope project/package và role; cùng bên nhiều vai, chặn trùng đúng scope/vai. `action_kd_parties`, ngừng quan hệ có lý do, giữ lịch sử. | A03/A06; `test_partners_many_roles_and_duplicate_scope`; [ảnh các bên][shot-parties]. Audit độc lập kiểm outsider read/search/name_search/export và foreign-company partner bị chặn. |
| 7 | Dự kiến giá gói khác phần công ty | `tp.bid.package.amount` tách `package_total`, `company_offer`, `company_share`; unknown/0 riêng, tiền tệ/thuế/nguồn/ngày và version. Không đổi nghĩa `expected_revenue`; không cộng ba nghĩa tiền. | A07; test 10 tỷ tổng/3 tỷ phần công ty, unknown→0, read/export/search/group/revoke; [ảnh giá trị][shot-amounts]. |
| 8 | Đấu thầu trong Kinh doanh và dự án | `menu_opportunities`→`action_packages`; `tp.bid.package` nhiều gói/project; CRM nhiều lần tham gia/gói. Cần đối chiếu giữ CRM thiếu link; nhánh direct không cần gói giả. | A04/A05/A12; multi-package/attempt/outcome isolation và direct mapping tests; [ảnh gói][shot-package-detail]. |
| 9 | Quản lý thực hiện khác quản trị thương mại | `action_management`/`management_landing`/`project_management_form` đối chiếu task/WBS/người/hạn/đầu ra. `action_governance`/`governance_landing`/`project_governance_form` đối chiếu bảy nguồn thương mại/nghĩa vụ. Switch giữ cùng project ID; WBS và tiến độ cùng `project.task`. | A01/A10/A14/A15; perspective domain/drilldown tests; [quản lý][shot-management] / [quản trị][shot-governance]. |

## 3. Ma trận A01–A16 và giới hạn

`Đạt trên test` chỉ áp dụng điều được mô tả và source seal ở mục1. `Một phần` nghĩa là có bằng chứng cụ thể nhưng chưa phủ hết AT; `Chờ` không được suy thành PASS. Không cộng các assertion UI/HTTP với Odoo test thành một tổng nghiệm thu.

| AT | Trạng thái | Bằng chứng cụ thể / phần chưa đủ |
| --- | --- | --- |
| A01 | **Đạt trên test** | Hai menu/action/landing/detail, cùng ID; UI61 switch/selection, extra10 Back chọn dự án. Native Back và breadcrumb giữ exact page/filter/sort trên fixture21project/21package sau correction hook. |
| A02 | **Đạt phạm vi kiểm** | Một project gốc, CRM là lần tham gia. Caller cũ dashboard/review_document/workspace mở governance; XMLID cũ có switch. Deep link/list/detail reload trong nav QA, source review giữ lịch sử và quyền. |
| A03 | **Đạt trên test** | Investor A/bên ký B khác nhau; CRM–Project–Contract giữ nghĩa thương mại cũ. |
| A04 | **Đạt trên test** | Hai gói/nhiều lần tham gia, outcome một gói không lan; direct/project-only không gói giả. |
| A05 | **Đạt trên test** | Owner trước một deadline. Native project/package10/20/50/100 và offset10/20, previous, clear, sort/cột/filter; parties/history/amounts25kiểm toolbar. Không sửa date cũ. |
| A06 | **Đạt phạm vi kiểm** | Nhiều vai/trùng đúng scope; independent outsider khác project bị chặn read/search/name_search/export và cross-company partner relation bị từ chối. Tái sử dụng res.partner. |
| A07 | **Đạt trên test** | Tổng gói10tỷ khác phần công ty3tỷ; unknown khác0; stale version bị chặn. Read/search/order/group/export/relational và revoke tiền được kiểm. Không có tổng mới cộng khác nghĩa/currency/thuế. |
| A08 | **Đạt trên test** | Reason/version/key/retry/reopen; actor/time/event immutable. Native status/note/progress thay backend thật. Task snapshots representative name/đầu ra trước/sau được assert. Hai cursor chứng minh lock contention; chưa chạy committed winner/loser race. |
| A09 | **Đạt phạm vi security đã kiểm** | Note/correction sau submitted giữ CRM snapshot. Guard direct/message-parent/defaults, nội dung/ownership/author fallback/side effect được hậu kiểm. P1 public/token context tìm thêm đã sửa, regression trước3fail/1→sau1/1; external legacy public/token cũng bị chặn. |
| A10 | **Đạt phạm vi kiểm** | Capability WBS/assign/progress tách money/contract/genericwrite. UI5fixture và5account cũ trên clone; independent revoke/expiry/assignment/current scope + stale/retry/lock đã chạy. Chưa có fresh multicompany HTTP toàn ma trận5vai. |
| A11 | **Đạt kỹ thuật, policy người thật riêng** | Năm actor cũ đọc10landing checks trên clone; fixture mục tiêu có action thật. Owner/reviewer legacy được kiểm kê và guide lý do thiếu nút. Không reassign/cấp grant người thật. Postapply smoke53checks/5login và preservation83table/4529oldrow giữ, gồm password/hash/MFA/passkey/grant/assignment/owner; không reassign. |
| A12 | **Đạt trên test; dữ liệu thật cần đối chiếu** |14project/25CRM giữ link/owner/file; investor/package chưa rõNULL. Mapping nonempty dry-run/apply2lần/journal1/rollback2lần; direct không gói, missing partner bị từ chối sớm. Chưa áp mapping thật. |
| A13 | **Hậu kiểm độc lập PASS phạm vi correction** |57ORM+36sharing/A06+17HTTP=110assertion. PDF/download đúng actor, denied bytes/response và submitted update/post/upload/delete/thumbnail. Public/portal token cũ cũng không đọc CRM bytes. Report/gate exact source ở mục7. |
| A14 | **Đạt trên test** | Management task/người/hạn/đầu ra; governance7nguồn/gói/cần đối chiếu, count+drilldown đúng scope. Không done=NT hoặc đề nghị=đã trả, không tỷ lệ project giả. |
| A15 | **Đạt Chromium phạm vi kiểm** |1440/1280/768/390/320; actual zoom200% cả2landing DPR2/width712/overflow0. Detailproject/package390/320 no overflow; drawer keyboard/Escape, reduced-motion0s, deep link/dirty cancel/continue/discard. Backpage/sort đã sửa bằng native action globalState. Reload vẫn bỏ facet tạm: dùng Favorites. Chưa thử thiết bị thật/browser khác. |
| A16 | **Đạt kỹ thuật triển khai** |Source test=seal=applied89c17…; backup mới131132Z/restore131138578table295attachment, upgrade riêng addon0error. Dev20.0.1.8.0, smoke53checks/5login0JSerror/no mutation,83table4529oldrow trước/sau upgrade/smoke giữ và295file checksum/size đúng. |

## 4. Kiểm thử thực chạy và evidence

| Kiểm tra | Kết quả / file |
| --- | --- |
| Odoo5addon | `final_test.py` gọi `run.py test`: update/test `tp_kd_workspace,tp_project,tp_contract,tp_crm_project_bridge,tp_web_home` trên clone, `--stop-after-init --no-http`. **185/185**, 0failed/0error; [JSON][odoo-result], [log][odoo-log], [runner][test-runner]. |
| UI chính | [ui.cjs][ui-runner] / [ui-result.json][ui-result]: **61 checks PASS,0 JS errors trên final seal** theo rerun toàn bộ bằng session mới. Bao gồm real-clone read, fixture capabilities, status/note/progress, columns/paging/responsive. Một lần thử trước gặp Odoo Session Expired ở deputy; một lần final khác timeout do technical modal chặn click; đã xác thực lại và chạy lại trọn61checks, không nhận lần dở là PASS. |
| UI bổ sung | [extra.cjs][extra-runner] / [extra-result.json][extra-result]: **10 checks PASS**, progress theo assignee/Back, planning scoped WBS, drawer/reduced-motion. Rerun source cuối đã đạt. |
| HOOT | [hoot.txt][hoot]: **20 tests/78 assertions PASS** trên final seal sau upgrade; gồm component/helper suite trong addon. |
| HTTP native | [security-http.json][http]: **17 checks PASS do reviewer độc lập chạy lại**, xem report/gate. |
| Zoom thật | [zoom.cjs][zoom-runner] đổi browser appearance zoomLevel=2; [zoom-result.json][zoom] ghi DPR2/width712/overflow0 cho management và governance; ảnh `management-zoom200.png`, `governance-zoom200.png`. Ảnh cũ tên `200-percent-equivalent` chỉ mô phỏng viewport, không dùng thay zoom thật. |
| Static/patch | [static-result.json][static]: **20 XML parse,10 JS node --check** + Ruff22Python PASS, root `git diff --check` và patch `git apply --check --whitespace=error` PASS. Delta58file kiểm khả năng áp; patch chỉ kiểm check;58file delta đã copy theo seal khi apply. Không chạy React typecheck/build vì React không đổi. |
| Native lists/navigation | [Related25](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-related-result.json>) PASS; [production29](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-pagination-production-assets-result.json>) và [kết quả cuối29](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-pagination-result.json>) PASS sau upgrade cuối. Temporaryreloadfacet2failed là hành vi native được ghi riêng; Backpage/sort đã sửa và đạt. |
| Dev smoke | [dev-smoke-result.json](<C:/TANPHAT ONE/.local/kd-project-restructure001/dev-smoke-result.json>):53checks/5login,0JSerrors/no dataset mutation;2landing/detail/project/package/native mobile. |
| Review completeness | [review-completeness.md][completeness] có findings trước correction và re-review: entry form/WBS command/direct mapping/package capability/investor label/sidebar leaf/metric đã chỉnh source. Missing-counterparty và task snapshot có regression trên source cuối. Review này không phải security audit. |

Log test có cảnh báo thiếu `markdown2` và filestore GC Windows `WinError5` ở các lần chạy trong log tích lũy. Dòng tổng kết cuối vẫn0failed/0error185tests; không dùng kết quả này để tuyên bố vận hành filestore/markdown đã hết giới hạn.

## 5. Migration, bảo toàn và backup

Inventory/dry-run private [mapping-dry-run.json][mapping] kiểm14 managed projects/25 CRM. Schema additive; giữ project ID, bên ký, hợp đồng/phụ lục, file, owner/reviewer, grant và lịch sử. Không đủ căn cứ thì investor/package giữ NULL, không suy submitted thành won hay expected_revenue thành giá cả gói; màn Cần đối chiếu là công việc cần xử lý bằng evidence ID tường minh.

[Utility mapping][mapping-source] dùng ORM và validation company/project/counterparty, journal delta và rollback chính xác; phép thử non-empty/idempotent/rollback ở A12 là fixture, không phải báo cáo đã mapping25CRM thật. Operator phải có mapping nguồn/người kiểm chứng, không tự ghép theo tên; thiếu bên ký phải đối chiếu trước dry-run/apply. Owner/reviewer legacy được kiểm kê riêng; nhu cầu bàn giao người thật vẫn mở, giữ các account/grant dev hiện có.

[Restore snapshot ban đầu][restore] xác nhận578bảng/295blob references trước neutralize. [Rehearsal backup mới][backup] xác nhận backup mới trước apply `backup-pre-apply-20261109T131132Z`, restore vào `tp_tanphat_kdreport001_backup_131138`,578bảng/295attachment references; [manifest][backup-manifest] có122file. Đây là backup mới dùng cho apply thực13:15UTC; root source/DB/config và owner runtime được kiểm lại ngay trước áp. Lần stop đầu từ chối vì launcher tương đối, chưa sửa source/DB; sau khi xác minh PID/cwd/source/config/db tường minh, chỉ đúng wrapper10720/listener22988 được dừng. Không tắt PG hoặc clone. Báo cáo không đưa dump, secret, owner names hay nội dung hồ sơ vào Git.

## 6. Ảnh thật và giới hạn so sánh

Evidence dưới `.local/kd-project-restructure001/shots/` là ảnh ứng dụng thật, không phải mockup. [Before Overview][before-overview], [before Projects][before-projects], [before Opportunities][before-opportunities] là dev baseline20.0.1.7.0; ảnh after là clone19489, gồm dữ liệu fixture tổng hợp để thử thao tác. Role HEAD/viewport1440 tương ứng nhưng **dataset và environment khác**, nên đây là chứng cứ thay đổi chức năng/bố cục, chưa là so sánh pixel trước–sau cùng dataset.

Ảnh **dev sau apply**: [quản lý](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-management.png>), [quản trị](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-governance.png>), [chi tiết](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-governance-detail.png>), [mobile](<C:/TANPHAT ONE/.local/kd-project-restructure001/shots/dev/head-governance-390.png>). Năm account/viewport/dataset hiện có, không seed mới.

Ảnh clone chọn lọc: [quản lý1440][shot-management], [quản trị1440][shot-governance], [detail quản lý][shot-management-detail], [detail quản trị][shot-governance-detail], [gói thầu][shot-package-detail], [các bên][shot-parties], [lịch sử][shot-history], [management320][shot-mobile], [governance390][shot-governance-mobile], [zoom200% quản lý][shot-zoom-management] và [zoom200% quản trị][shot-zoom-governance]. Mobile/tablet là emulation viewport trong Chromium trên Windows, không là thử thiết bị thật.

## 7. Cổng triển khai và phần còn thiếu

- **AUDIT-FINAL PASS phạm vi quyền**: [review độc lập](<C:/TANPHAT ONE/.local/kd-project-restructure001/review-final-permissions.md>), [gate JSON](<C:/TANPHAT ONE/.local/kd-project-restructure001/review/final-permissions-gate.json>). 110assertion chạy trên runtime bd916…, sau đó reviewer đối chiếu4dấu phẩy test và hook bảng89c17…; backend/controller/ACL giữ byte, JS chỉ khôi phục limit/offset/order. Không gọi source comparison là rerun110.
- **UI-FINAL**: UI61/extra10/HOOT20(78assertion); [nav main](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-result.json>)39pass/2fail reloadfacet tạm/3notproven lúc chỉ1–2row. [Related25](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-related-result.json>)PASS. [Paging29](<C:/TANPHAT ONE/.local/kd-project-restructure001/nav-pagination-result.json>) trên fixture21+21 đóng offset/Back/mobile. Production bundle sau upgrade đã đạt29/29, root source/trạng thái trước và sau đúng seal. Hai fail BrowserBack trước correction và staleasset attempt được giữ riêng, không dùng làm PASS.
- Full reload bỏ facet tìm kiếm tạm là hành vi native, dùng Favorites. Back/breadcrumb trên bản sửa phải giữ page/filter/sort, không coi guide là thay test.
- **Dev18069/A16 PASS kỹ thuật**: [apply](<C:/TANPHAT ONE/.local/kd-project-restructure001/dev-apply-result.json>), [smoke53](<C:/TANPHAT ONE/.local/kd-project-restructure001/dev-smoke-result.json>), [preservation83table](<C:/TANPHAT ONE/.local/kd-project-restructure001/preservation-after-smoke-diff.json>), [source/files](<C:/TANPHAT ONE/.local/kd-project-restructure001/post-apply-source-files.json>). New package/amount/participation/projectevent/taskevent model counts đều0 trên dev, không fixture hoặc inferred mapping.83table4529oldrow giữ qua upgrade+smoke;295attachment kiểm hash/size. Account/auth/config/module set giữ. [Guide](KD_PROJECT_RESTRUCTURE_001_USER_GUIDE.md) chỉ đúng menu và vì sao5actor chưa có capability cập nhật mới.
- **Chưa phê duyệt** business acceptance, visual feedback, pilot, toàn V2/TASK-001 hoặc quyền/owner người thật. Thiếu mapping căn cứ investor/package và owner/reviewer thật vẫn cần chủ nghiệp vụ xử lý; không suy đoán.
- **Giới hạn kiểm**: Chromium/emulation; không thiết bị vật lý/browser khác; concurrency là two-cursor lock+stale/retry, chưa committed winner/loser; multicompany actor matrix HTTP toàn bộ chưa chạy, A06 ORM đã kiểm. Log còn markdown2/WinError5 GC, không nhận đã sửa runtime này.

Xem [hướng dẫn](KD_PROJECT_RESTRUCTURE_001_USER_GUIDE.md) và [migration/rollback](KD_PROJECT_RESTRUCTURE_001_MIGRATION_RUNBOOK.md). Cách thao tác/quyền và dữ liệu chưa rõ được ghi tách khỏi technical acceptance.

[source]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/models/project_restructure.py>
[views]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/views/project_restructure.xml>
[perspective]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/models/project_perspective.py>
[owl]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/static/src/project/perspective.js>
[tasks]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/models/scoped_task.py>
[functional-tests]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/tests/test_project_restructure.py>
[mapping-source]: <C:/TANPHAT ONE/.local/kd-project-restructure001/workspace/custom_addons/tp_kd_workspace/migration_mapping.py>
[seal]: <C:/TANPHAT ONE/.local/kd-project-restructure001/source-seal.json>
[odoo-result]: <C:/TANPHAT ONE/.local/kd-project-restructure001/final-odoo-result.json>
[odoo-log]: <C:/TANPHAT ONE/.local/kd-project-restructure001/tests.log>
[test-runner]: <C:/TANPHAT ONE/.local/kd-project-restructure001/final_test.py>
[ui-runner]: <C:/TANPHAT ONE/.local/kd-project-restructure001/ui.cjs>
[ui-result]: <C:/TANPHAT ONE/.local/kd-project-restructure001/ui-result.json>
[extra-runner]: <C:/TANPHAT ONE/.local/kd-project-restructure001/extra.cjs>
[extra-result]: <C:/TANPHAT ONE/.local/kd-project-restructure001/extra-result.json>
[hoot]: <C:/TANPHAT ONE/.local/kd-project-restructure001/hoot.txt>
[http]: <C:/TANPHAT ONE/.local/kd-project-restructure001/security-http.json>
[zoom-runner]: <C:/TANPHAT ONE/.local/kd-project-restructure001/zoom.cjs>
[zoom]: <C:/TANPHAT ONE/.local/kd-project-restructure001/zoom-result.json>
[static]: <C:/TANPHAT ONE/.local/kd-project-restructure001/static-result.json>
[completeness]: <C:/TANPHAT ONE/.local/kd-project-restructure001/review-completeness.md>
[mapping]: <C:/TANPHAT ONE/.local/kd-project-restructure001/mapping-dry-run.json>
[owners]: <C:/TANPHAT ONE/.local/kd-project-restructure001/owner-reconciliation.json>
[restore]: <C:/TANPHAT ONE/.local/kd-project-restructure001/restore-evidence.json>
[backup]: <C:/TANPHAT ONE/.local/kd-project-restructure001/backup-restore-result.json>
[backup-manifest]: <C:/TANPHAT ONE/.local/kd-project-restructure001/backup-pre-apply-20261109T131132Z/manifest.json>
[before-overview]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/before/head-overview-1440.png>
[before-projects]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/before/head-projects-1440.png>
[before-opportunities]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/before/head-opportunities-1440.png>
[shot-projects]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-project-list.png>
[shot-packages]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-package-list.png>
[shot-package-detail]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-package-detail.png>
[shot-status]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-status-command.png>
[shot-history]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-project-history.png>
[shot-parties]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-partners.png>
[shot-amounts]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-package-amounts.png>
[shot-management]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-management-1440.png>
[shot-governance]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-governance-1440.png>
[shot-management-detail]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-management-detail.png>
[shot-governance-detail]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-governance-detail.png>
[shot-mobile]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-management-320.png>
[shot-governance-mobile]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/head-governance-390.png>
[shot-zoom-management]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/management-zoom200.png>
[shot-zoom-governance]: <C:/TANPHAT ONE/.local/kd-project-restructure001/shots/after/governance-zoom200.png>
