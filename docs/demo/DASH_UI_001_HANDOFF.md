# DASH-UI-001 — Bàn giao triển khai native dashboard

04/11/2026 (Asia/Saigon), `CHG-20261104-001`, DEC-028. **IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT**. Technical verification của phiên thực thi; audit độc lập, business acceptance và pilot authorization chưa có. [Runbook/công thức/bộ lọc/giới hạn](dashboards/README.md).

## Bổ sung biểu đồ và hover (CHG-20261104-004)

Yêu cầu tiếp nối của người dùng ngày04/11: biểu đồ trực quan hơn và có hover. Đã áp dụng/kiểm native dev18069 sau clone, trong quyền thực thi riêng DEC-028. Chỉ JS/XML/SCSS tại `custom_addons/tp_dashboard_privacy/static/src/`, không đổi backend/công thức/quyền/filter/workbook/XML ID. Chia component biểu đồ và dùng popover native; không thêm thư viện, endpoint hoặc reporting storage.

- Thanh so sánh dày25px với lưới5 mốc từ0, nhãn đầy đủ và số backend chính xác. Hai nguồn điều phối phân biệt tím/xanh. Dòng0 giữ mốc0 thay vì vẽ thanh có độ dài giả.
- Chi phí là vòng xám/vàng/xanh theo thứ tự đang soạn/chờ duyệt/đã duyệt, tổng backend ở tâm, số tiền và tỷ trọng trong chú giải. Hover/focus làm nổi cung và đổi tâm sang trạng thái tương ứng; nguồn của tỷ trọng là đúng ba giá trị chart hiện đang lọc. Phần trăm làm tròn1 chữ số; có thể không cộng đúng100% do làm tròn. Geometry/tick/percentage trình bày ở JS, không tính lại tiền nghiệp vụ; tổng và số tiền vẫn dùng display backend. Khi tổng0, chỉ vẽ vòng nền.
- Tooltip hiện tên/mã đầy đủ, giá trị exact và tỷ trọng (với vòng); có thể hover vào tooltip, Escape đóng, focus ở lại nút. Chú giải là button thật dùng Tab/Enter/tap mở cùng native action đã recheck backend. Mobile luôn đọc được số, không phụ thuộc hover; hiệu ứng140ms tắt theo reduced motion. Refresh/unmount đóng tooltip, không giữ số từ report cũ.

Kiểm thực chạy cho bản bổ sung:

| Kiểm tra | Kết quả | Evidence private dưới `.local/dash-hover001/` |
| --- | --- | --- |
| Native UI/RPC hồi quy |60 kiểm mỗi môi trường clone/dev;1440/1280/390;actor/filter/empty/error/source/share giữ đạt | `ui-clone/results.json`, `ui-dev/results.json` |
| Biểu đồ |43 kiểm mỗi môi trường: hover exact, peer dimming, grid/geometry, tooltip hover/Escape/focus, đúng action source, SVG sector/legend/center,0/100%, mobile bounds, reduced motion, refresh cleanup, touch tap | `charts-clone/results.json`, `charts-dev/results.json` |
| Zoom Chromium thật |125%/150% hai dashboard mỗi môi trường;DPR đúng,0 overflow/page errors | `zoom-*-results.json` |
| Asset/syntax | SCSS compile bằng LibSass, XML parse, `node --check`4 JS/CJS đổi đạt; bundle native thực tải qua UI | Log kiểm/static validation |

Probe biểu đồ0 console/runtime error; mỗi ma trận UI có1 network error cố ý kiểm retry,0 lỗi không mong đợi. Không chạy lại Odoo/React tests vì không đổi Python/model/security/React. Lần clone đầu bắt lỗi LibSass `min()` với `calc()`, đã sửa thành width/max-width trước dev. Một probe dev timeout lần cold-load khi chạy song song; chạy tuần tự lại và final probe43 đạt. Không tính các lần thất bại là đạt.

Backup3 source `before-dashboard.*`, checkpoint trước sửa, hash538 bảng trước/sau; dùng clone owned đã có restore rehearsal, không seed dữ liệu thử mới. Dev chỉ `stop_server/start_server` riêng Odoo để tái tạo asset, PostgreSQL tiếp tục; không upgrade addon hoặc apply workbook. Bảo toàn527/538 bảng nguyên, các chứng từ/workbook/user/password/group/ACL/rule/assignment không đổi;3 attachment asset417–419 được thay bằng420–422.249 blob từ snapshot gốc của task và249 reference hiện tại kiểm đạt; file config/credential/catalog/roles nguyên.

**Thao tác đồng thời được bảo toàn:** log server ghi session Odoo đang mở khác lưu Settings lúc13:35:44 (06:35:44UTC), trước dev restart: transient settings1 và30 config parameter44–73 mới, company1 chỉ write_date, cron29 nextcall/write metadata, signaling. Phân loại riêng tại `concurrent-settings.json`, `preserve-diff.json`, `preservation-review.json`; không đọc/in giá trị credential, không rollback và không nghiệm thu nội dung cài đặt đó. Không tuyên bố mọi cấu hình DB giữ nguyên trong lượt hover.

Ảnh desktop/mobile/tooltip thật đã tự xem: `charts-dev/6-chart-1440.png`, `6-chart-390.png`, `5-chart-hover.png`. `finance-hover.gif` ghép hai trạng thái thật cùng viewport để minh họa idle/hover; không là walkthrough HTML. Các bằng chứng CHG-001 bên dưới là lịch sử lần triển khai đầu; ảnh/kết quả mới nằm ở thư mục riêng nêu trên. Clone18159 đã dừng sau kiểm, dev18069/PG55432 tiếp tục,18109/18119 đóng. Next action vẫn audit độc lập DASH-UI-001; không business/pilot acceptance, không commit/push.

## Kết quả trên dev18069

Hai dashboard native ID5,6/XML ID cũ đã áp dụng và kiểm trực tiếp; addon `tp_dashboard_privacy`20.0.1.1.0. Không commit/push. Không sửa React/prototype/core Odoo, workflow, ACL/group/allowlist/password hoặc chứng từ dev. OWL trong native action, report bằng actor ORM không sudo dữ liệu nguồn; không tạo reporting database/snapshot tổng runtime.

Tài chính:4 hóa đơn nháp801.000.000 đồng gồm thuế,6 đề nghị chi phí7.160.000 đồng. Cơ cấu chi phí hiện810.000/1.250.000/5.100.000. Nguyên nhân khác mốc02/11: Administrator duyệt expense11 An Hòa1.850.000 lúc04/11 08:44:55, tracking1020 lưu trạng thái/chuyển quản lý, trước task. Không sửa ngược dữ liệu. Điều phối:4 dự án,28 task,4 hoàn tất,84 giờ. Không KPI tiến độ/quá hạn/lợi nhuận/thu tiền mới.

Thẻ/chart/bảng/action cùng nguồn, scope và filter; invoice relation dùng analytic distribution trên dòng, không invoice_origin. Làm tròn tiền ở Odoo, unique document count. Hiện toàn bộ thời gian hoặc ngày nguồn rõ ràng; nội bộ chặn Share cả UI lẫn guard backend cũ; dashboard chuẩn Share giữ native. Refresh thật và fetched_at do server; loading/empty/denied/retry không hiển thị số0 cho lỗi. Sidebar đủ tên/thu gọn/phím; mobile xếp dọc, bảng cuộn riêng.

## Môi trường và bảo toàn

- Baseline Git sạch ở `e1dacf4d` (03/11 16:07:01+07:00), kế sau commit nguồn `f54fd83f`; workflow check CHG-20261103-001 đạt, start trước sửa. Mốc HEAD được hiệu chỉnh bằng log/reflog ở CHG-20261104-003; task không tạo commit. Snapshot private130 checksum `.local/dash-ui001/snapshot-20261104T015714Z/` có dump/filestore/source/config; restore clone owned `tp_tanphat_dashui001_20261104` port18159/data-dir riêng đạt538 rowset/249 blob reference exact trước neutralize cron/mail.
- Chỉ upgrade privacy và apply hai dashboard sau clone tests. Apply dev [5,6]; verify/reapply0 create/update. `native_data003.py links --target dev --mode verify`0 drift. Giữ XML ID/quyền và snapshot baseline của người dùng; guarded apply từ chối workbook/name/access drift, không overwrite ngoài scope.
- Một lần dùng nhầm CLI `dev.py stop` dừng PG; lần upgrade đầu không kết nối được DB. Đã bật lại, đối chiếu538/538 bảng/config/credential/catalog/roles nguyên, dùng `stop_server` để dừng riêng Odoo rồi upgrade đúng. Clone có connection cũ sau PG restart, đã restart owned clone; không đổi credential để xử lý lỗi đăng nhập đó. Đã ghi sự cố, không coi lần thất bại là upgrade thành công.
- Đối chiếu cuối bằng `scripts/dash_ui001_preserve.py`: **528/538 bảng nguyên**, 10 bảng có delta đã đối chiếu: `spreadsheet_dashboard`, `ir_attachment`, `ir_module_module`, `ir_module_module_dependency`, `bus_bus`, `ir_cron_trigger`, `orm_signaling_registry`, `res_users_log`, `res_device_log`, `mail_presence`. Phạm vi thay đổi chỉ dashboard5/6, attachment404/405 workbook,3 asset native thay phiên bản, module metadata/3 dependency và telemetry. Chứng từ, task/timesheet, user/password/group, ACL/rule/assignment không đổi. File cấu hình/secret/PG roles/catalog nguyên; **249 blob gốc và 249 reference hiện tại kiểm đạt**;3 old asset reference được thay bởi regeneration, blob gốc giữ checksum; không xóa business file. Evidence `preservation-acceptance.json` và `preserve-final.json` private. Không fingerprint toàn nội dung DB khác; chỉ catalog/owner/role chung.

## Kiểm thử thực chạy

| Nhóm | Lệnh / kết quả | Evidence private dưới `.local/dash-ui001/` |
| --- | --- | --- |
| Odoo upgrade + regression clone | `python -X utf8 odoo-bin -c .local/dash-ui001/clone.conf -d tp_tanphat_dashui001_20261104 -u tp_dashboard_privacy --test-enable --test-tags /tp_dashboard_privacy --stop-after-init --no-http`:17 tests,0 failed/0 errors | `odoo-tests-release.log` |
| Tool | `python -m unittest discover -s scripts/tests -p test_dash_ui001.py -q`:5 đạt; DATA003 guard9 đạt | Lệnh hiện hành trong Git |
| Lint/syntax/tài liệu | Ruff trên addon/generator/tooling/test đổi; Node --check trên JS/CJS đổi; XML parse; generator chạy lại giữ nguyên byte3 template; local Markdown link/fence đạt; `git diff --check` đạt, staged diff rỗng | `final-static-validation.json`, kết quả bàn giao/checker |
| UI + RPC clone/dev | `node scripts/dash_ui001_ui.cjs clone/dev`:60 kiểm mỗi môi trường | `ui-clone/results.json`, `ui-dev/results.json` |
| Browser zoom thật | `node scripts/dash_ui001_zoom.cjs clone/dev`:125%/150%,2 dashboard;DPR1,25/1,5;0 overflow/page error | `zoom-*-results.json`, `zoom-*.png` |
| Refresh nguồn clone | `node scripts/native_data003_dashboard_probe.cjs --dash-ui001`:Long/Nam84→84,5→84 giờ;Sơn/Bảo draft810.000→820.000→810.000;source restore | `refresh-results.json`,6 ảnh |
| Revoke clone | `node scripts/dash_ui001_security.cjs`:dashboard allowance + project assignment revoke;RPC/raw/drilldown/refresh bị chặn hoặc loại project,card cũ xóa;exact quyền restore | `security-revocation.json`, `revoked-no-cached-money.png` |
| Smoke dev | `python scripts/dev.py smoke`:native session,JSON401,scope project/contract/financial grant đạt | `dev-smoke.log` |
| Idempotent/drift | apply dev lần2 và verify hai môi trường0 update/create;DATA003 links verify0 drift;unit guard chặn edited workbook/access | `apply-*.json`, `links-verify.log` |
| Bảo toàn | `python scripts/dash_ui001_preserve.py`: đạt;538 bảng được đối chiếu,249 blob gốc/249 reference hiện kiểm đạt | `preservation-acceptance.json`, `preserve-final.json` |

Ma trận UI gồm admin, Nam/Khoa điều phối, Bảo kế toán, Khang ngoài scope; desktop1440/1280, mobile390; tổng/trạng thái/table/drilldown/date/project/empty,source list thật4 invoice,sidebar collapse/phím và keyboard refresh. Error/retry test cố ý gây1 console network error mỗi ma trận; **0 lỗi console không mong đợi**, không ghi nhầm tổng console bằng0. Odoo test có INFO filestore GC WinError5 cũ, chưa sửa ở task này. Không chạy React test/build vì không sửa React.

## Ảnh trước/sau đã tự xem

Ảnh private, không đưa dữ liệu runtime vào Git:

- Trước: `ui-dev-before/6-1440.png`, `ui-dev-before/5-1440.png`; IAB `finance-before.jpg`, `coordination-before.jpg`.
- Sau: `ui-dev/6-1440.png`, `5-1440.png`, `6-1280.png`, `5-1280.png`, `6-390.png`, `5-390.png`; bảng `6-table-1440.png`, `5-table-1440.png`; zoom `zoom-dev-*.png`.
- So sánh ghép từ ảnh nguyên màn hình thật: `finance-before-after.png`, `coordination-before-after.png`. Đây là montage trình bày, không phải HTML walkthrough.

## Giới hạn và tiếp theo

Native source list mở nguyên chứng từ: khi chia nhiều dự án, tổng trên chứng từ có thể lớn hơn phần phân bổ dashboard. Vùng Giải thích số liệu ghi rõ, chưa có view từng phần phân bổ. Edit spreadsheet không chỉnh thẻ/chart OWL. Không quy đổi invoice khác tiền tệ công ty; ambiguous/shared-account/negative/over100% allocation trả lỗi kiểm nguồn, không đoán. Không có snapshot/export chia sẻ công khai mới.

Snapshot/backup giữ private; rollback UI cần backup workbook/source tương ứng, kiểm current còn bằng after rồi hoàn tác đúng phần, không restore cả dev hoặc uninstall privacy khi đã có dữ liệu nội bộ. Không dùng seeder DATA002/actors/actions để sửa UI. Đã dừng clone bằng owned stop sau kiểm:18159/18109/18119 không có listener; dev18069/PG55432 tiếp tục, dev login HTTP200. Tab dev giữ ở dashboard tài chính.

Next action: audit độc lập DASH-UI-001 theo source/report/evidence; nếu đạt mới ghi technical acceptance độc lập. DATA003/TASK-001/Home/To-do/VI/AUTH/Q2/owner/evidence và business/pilot vẫn gate riêng.

Ghi nhận workspace dùng chung: trong lúc hoàn tất kiểm tra có tài liệu CHG-20261104-002/DEC-029 từ phiên khác tại status/changelog/decisions/database design. Giữ nguyên nội dung đó. Snapshot checker hiện tại bao gồm tài liệu đang có; DASH-UI-001 không triển khai hoặc nghiệm thu cơ cấu tổ chức.
