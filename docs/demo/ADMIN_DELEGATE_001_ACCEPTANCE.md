# ADMIN-DELEGATE-001 — Kiểm chứng quyền quản trị được ủy quyền

Ngày 17/11/2026 (Asia/Saigon), CHG-20261117-004, DEC-050.
Ma trận được lập trước sửa application, cập nhật từ evidence thực chạy.
Yêu cầu trực tiếp cho phép áp main18069, commit/push và deploy PC server;
không tự chọn tài khoản thật nhận quyền. Fixture và ca cấp/thu thử chỉ dùng
database canonical `tp_tanphat_test`. Chưa cấp delegation cho người thật.

**Cập nhật tiếp tục17/11: MAIN_APPLIED_PARTIAL_COVERAGE; SERVER_RELEASE_PENDING.** 18069cài exit0/0ERROR,20fingerprint bảng/baseURLgiữ, ledger0/0. Browseradmin4/4,HOOT48/48/243assertions. HRsafe view khớp focusedmanifest hr-view-focused2(1/1); chỉ3fileHR khácR11. Không chạy thêm18079/fixture main-server. Mục pending lịch sử bên dưới giữ theo snapshot; delegateHR browser cuối vẫn NOT_RUN.

**Kết luận snapshot trước: PARTIAL — các ca kỹ thuật đã chạy đạt, còn thiếu coverage
và kiểm giao diện sau sửa HR.** R11 đạt 35/35 ca addon, hồi quy R2 đạt 77/77;
hai bộ này không chứng minh toàn bộ AD01–AD09 hoặc toàn hệ thống đã đủ CRUD
phòng khác. Source HR safe view đang thay đổi sau snapshot R11; chờ kiểm bản
tích hợp cuối. AD09 chưa PASS. Main/server chờ chủ batch ghi kết quả áp thực
tế vào bảng môi trường bên dưới.

Nguồn: [prompt](../prompts/CLAUDE_ADMIN_DELEGATE_001_AND_PUBLIC_FILES.md),
[policy](../security/ADMIN_DELEGATE_001_POLICY.md),
[coverage](../security/ADMIN_DELEGATE_001_COVERAGE.md).
Evidence riêng tư: `.local/admin-delegate001/`. Các đường dẫn evidence dưới
đây là tệp local ignored, không đi cùng bản Git. Không đưa cookie, token,
mật khẩu, dump, filestore hoặc hồ sơ nhân sự vào Git.

## 1. Môi trường và hiệu lực bằng chứng

| Môi trường | Phạm vi đã kiểm | Trạng thái hiện tại / phần cần bổ sung |
| --- | --- | --- |
| Test: `tp_tanphat_test`, PostgreSQL workspace55432 | Odoo model/security test chạy tiến trình riêng `--stop-after-init`, HTTP port18179; cùng database test, không tạo DB theo task | PASS snapshot R11 35/35, focused P1 2/2 và hồi quy R2 77/77. Source manifest đi cùng mỗi lượt; HR safe view thay sau R11 nên chưa niêm phong source tích hợp cuối. |
| Test HTTP: `127.0.0.1:18079`, cùng `tp_tanphat_test` | Phiên delegate giả giữ cookie qua cấp/thu; Home/browser smoke; HTTP file; race bằng hai transaction PostgreSQL riêng | 23/23 kiểm AD06 và 7/7 kiểm race nguồn thiết bị đạt. HTTP hiện kiểm một tiến trình Odoo; chưa có bằng chứng nhiều Odoo worker. HR safe view/browser cần chạy lại. |
| Main: `tp_tanphat_dev`/18069 | Chờ ghi backup, install/upgrade, fingerprint quyền/dữ liệu và smoke sau áp | PENDING — chủ batch cập nhật bằng evidence thực; không suy từ kết quả test hoặc source đã push. Không chạy fixture/cấp thử cho người thật tại đây. |
| PC server: Docker `tp-odoo`, `192.168.1.73:8069` và URL public hiện hành | Chờ ghi backup, checksum source, install/upgrade, restart và smoke public của addon delegation | PENDING — chủ batch cập nhật bằng evidence thực. Kết quả phục hồi media là hạng mục riêng, không xác nhận addon delegation đã deploy. |

`PASS` dưới đây chỉ áp cho actor/action/source đã nêu; `PARTIAL` nghĩa là có
bằng chứng đạt nhưng chưa đủ toàn hàng yêu cầu; `NOT_RUN` là chưa chạy hoặc
chưa có bằng chứng. Một assertion từ chối đúng không có nghĩa mọi action
trên model đó đã được kiểm. Số assertion/race và số ca Odoo là các đơn vị
khác nhau, không cộng thành một tỷ lệ nghiệm thu chung.

## 2. Sổ bằng chứng

| Mã | Evidence private trong `.local/admin-delegate001/` | Kết quả và giới hạn |
| --- | --- | --- |
| E01 | `tests-test-r10.log`, `tests-result-r10.json`, `tests-source-r10.json` | 33/33, 0 failed/0 errors, exit0. Mốc cũ trước hai regression context-default; giữ để truy vết, dùng E02 cho bản guard mới hơn. |
| E02 | `tests-test-r11.log`, `tests-result-r11.json`, `tests-source-r11.json` | 35/35, 0 failed/0 errors, exit0; footer dòng9346. Gồm delegation12, business scope9, HR profile4, baseline2, Kho4, Reporting4. Chưa gồm thay đổi HR safe view sau lượt này. |
| E03 | `tests-test-p1-focused.log`, `tests-result-p1-focused.json`, `tests-source-p1-focused.json` | 2/2 PASS, exit0: chặn identity qua `default_*` và khóa/tăng revision cho subject `default_user_id` khi tạo responsibility. Hai ca này cũng có trong E02, không tính thêm ca độc lập. |
| E04 | `regression-test-r1.log`/`regression-result-r1.json`; `regression-test-r2.log`/`regression-result-r2.json`/`regression-source-r2.json` | Mốc cũ64/64; R2 mở rộng77/77, 0 failed/0 errors, exit0, footer dòng11386. Project access/private todo/department role, HR account/identity và contract access/workflow; không là hồi quy mọi addon/action. Log có lỗi unique constraint được ca âm chủ ý bắt; kết quả cuối runner là0 failed/0 errors. |
| E05 | `ad06-results.json`, `ad06-console.log`, `ad06-source.json` | 23/23 assertion đạt: cùng cookie trước/cấp/thu với project/file/account; ghi trước thì thu hồi đợi commit, snapshot cũ sau thu hồi bị serialization failure và request mới bị chặn. Có assertion giữ fixture để browser dùng; chưa phải bằng chứng dọn toàn fixture. |
| E06 | `ad06-equipment-results.json`, `ad06-equipment-console.log` | 7/7 assertion đạt: admin chuyển phòng người giữ trước thì stale write bị serialization failure; write trước thì transfer đợi commit; request mới metadata/meter bị chặn khi nguồn đã thành phòng actor. Fixture bổ sung equipment/employee/resource/category đã dọn, danh sách còn lại rỗng. |
| E07 | `ui-test/result.json`, ảnh trong `ui-test/`, `delegate-browser-inspect.json` | 6/6 smoke đạt: form admin, section quản trị, Home delegate, không có Settings, mobile Home không tràn, focus tìm kiếm bằng phím. Đây là lát cắt browser cũ, chưa bao phủ HR list/detail bằng delegate và toàn modal. |
| E08 | `hoot-18079/result.json` | HOOT47/47, 240 assertions đạt ở lượt cũ. Lượt48 của thay đổi Home mới còn PENDING khi cập nhật tài liệu; chỉ đổi thành PASS sau có log/result tương ứng. Không thay bằng chứng browser HR. |
| E09 | `runtime-summary.json` | Tóm tắt hỗ trợ, không thay raw log. Hiện ghi `source_matches_final_unit_manifest:false`, lý do HR native view gặp `ListArchParser` / field `tp_employment_kind` undefined; chờ backend sửa safe view, upgrade/restart và DOM verification. |

## 3. Ma trận AD01–AD09

Mọi actor thử dưới đây là synthetic trên test. Admin chính dùng quyền hiện
có; delegate không được thêm nhóm system/HR/HEAD chỉ để test chạy được.

| ID / mức hiện tại | Hành động và kết quả đã có | Chưa đủ / điều kiện để đóng hàng |
| --- | --- | --- |
| **AD01 — PASS kỹ thuật** | E02: cấp cho hai user khác phòng, thu hồi, ledger bất biến/main-only; group/company/identity trước–sau giữ nguyên. E02 business scope: không tạo assignment/grant hoặc thêm system/platform group để mở dự án/hợp đồng. E05: cấp/thu trên actor giả đang đăng nhập. | PASS cho đường backend đã chạy. Thao tác đủ modal tái xác thực native bằng browser thuộc AD09; nghiệm thu nghiệp vụ và chọn người thật chưa thực hiện. |
| **AD02 — PARTIAL** | E02/E05: dự án được phân công phòng mình vẫn đọc được; dự án phòng mình ngoài phân công vẫn bị chặn; count và financial capability phòng mình không được mở thêm. File phòng mình hợp lệ giữ được sau cấp/thu. Kho search/count/export giữ scope own; quyền export fixture đã có trước. HR job metadata của đồng nghiệp và Reporting schedule CRUD hợp lệ từ trước còn dùng trong/sau delegation; self promotion vẫn bị chặn. | NOT_RUN: ma trận trước/cấp/thu đầy đủ cho mọi CRUD/submit/review/chốt/file/export tại KH-KD, Reporting, HR và mọi loại tiền. Hồi quy77 ca kiểm workflow/ACL gốc, không thay cho so sánh delegation từng action ở phòng actor. |
| **AD03 — PARTIAL** | E02: tạo hợp đồng nháp ngoài phòng qua workflow với scoped staff và với plain internal user; actor/create_uid đúng, không phát sinh business grant. HR profile adapter tạo/sửa metadata/lưu trữ hồ sơ chưa nối user ngoài phòng, có lý do, từ chối mục tiêu/phạm vi sai. Kho metadata, repair create/edit/start/finish, software/meter theo nguồn đã kiểm. Reporting chỉ thêm đọc report cá nhân đơn giản ngoài phòng; task/value/snapshot/carry không được mở thêm. | **Chưa có full CRUD phòng khác.** Project/task/CRM CUD giữ baseline; hợp đồng assign owner/document add-remove/take review vẫn cần HEAD. Reporting shared/aggregate/value/snapshot và CUD/review/chốt không mở thêm. HR private fields giữ groups; không xóa vật lý/đổi phòng/role. NOT_RUN: vòng duyệt/chốt/chỉnh sửa bản chốt bằng delegate, delegated cross-company đầy đủ, browser/file mỗi miền. |
| **AD04 — PARTIAL** | E02/E03: backend chặn direct/sudo, self job promotion, user groups/company, employee/resource/version link, nested commands, clone identity, responsibility/grant, HR import, reparent thiết bị, mixed bulk và boolean-context giả. Regression mới kiểm `default_employee_id`, `default_user_id`, `default_resource_id`, `default_current_version_id`, `default_work_contact_id`, phòng mặc định và subject fence. HR account/profile adapter loại context client khi tạo. | Các ca ORM đã nêu PASS. NOT_RUN: phát lại toàn bộ payload tấn công qua JSON-RPC/REST/browser cho từng model/route, API-key/MFA target và mọi biến thể field default/lệnh quan hệ. Không dùng static guard scan để kết luận mọi đường của toàn hệ thống đều đã thử. |
| **AD05 — PARTIAL** | E02: ordinary account ngoài phòng được create qua wizard, lock/unlock/reset; target tự thân và delegate khác bị chặn, context không cấy admin partner/system group. Wizard mở trước revoke bị từ chối sau revoke. E05: cùng cookie account target ngoài phòng mở sau grant và mất sau revoke. Chặn cấp tiếp/ledger trực tiếp ở backend. | Reset positive test thay `_require_recent_identity` bằng mock để tách logic target; không là test nhập mật khẩu/tái xác thực browser. NOT_RUN: API key/MFA/portal/HEAD/security-writer target qua native UI, toàn chuỗi A→B→A và ma trận mọi company/alternate identity bằng HTTP. Không reset tài khoản thật để bổ sung evidence. |
| **AD06 — PARTIAL** | E05 23/23 và E06 7/7: phiên HTTP cũ mất project/file/account ngoài phòng sau revoke, own baseline còn. Hai transaction PostgreSQL thật kiểm write→revoke và stale write sau revoke; khóa nguồn Kho kiểm hai thứ tự transfer/write, dùng transfer wizard HR native. E02 cũng kiểm thu hồi wizard, binary và search/count/export model. | **Chưa kiểm nhiều Odoo worker.** HTTP chạy một tiến trình; hai DB transaction không chứng minh signaling/cache liên worker. NOT_RUN: export đang mở qua HTTP, toàn route/API/file, tab UI tự cập nhật và grant/revoke/write trên cấu hình nhiều worker. Request đã commit trước revoke không tự đảo; file đã tải không thể thu hồi. |
| **AD07 — PARTIAL** | E02: nhiều responsibility/phòng được hợp vào vùng bảo vệ; unknown responsibility đóng phần thêm. Contract nguồn giao thoa, CRM unknown kể cả archived, thiết bị own/stock/mixed parent/bulk/reparent không mở thêm. Admin đổi nguồn assignment project/team/department tăng scope revision; chuyển phòng người giữ thiết bị hợp lệ đóng scope đã đọc. E06 xác nhận thứ tự lock với transaction cạnh tranh. | PASS cho các nguồn/ca âm đã nêu. NOT_RUN: mọi dạng shared record/alternate HR identity/cross-company và mọi bulk action của từng phân hệ; không tuyên bố toàn bộ nguồn lịch sử đã được tái dựng. History thiếu snapshot phòng gốc, vendor/location/proposal/inventory giữ baseline. |
| **AD08 — PARTIAL** | E02: project và Kho search/count, Kho export_data, repair chatter native, private attachment/binary stream sau thu hồi; Reporting report nguồn task/value/snapshot/carry bị chặn. Chatter tạo qua parent write và Python sentinel, context boolean không mở generic create. E05 file HTTP theo quyền cùng cookie. | NOT_RUN: tất cả dashboard/filter/options/many2one/read_group/pager/count/export trước–sau trên mọi UI; custom XLSX/PDF/QR Kho qua browser với actor delegate; chatter/file của mỗi miền và token/cache/public của mọi route. Dashboard Kho, danh mục chung, stock/shared/import giữ baseline; menu mở không xác nhận dashboard đã được adapter hóa. |
| **AD09 — PARTIAL, HR UI đang sửa** | E07 6/6 Home/admin smoke và E08 HOOT47 đã đạt. E02 menu scope whitelist, không mở Settings/Apps, revoke đưa menu về baseline; backend lock/unlock account tách biệt ledger delegation. | Lỗi browser HR native list: `ListArchParser` báo field `tp_employment_kind` undefined với delegate không có HR group; safe view đang sửa sau R11. NOT_RUN trên bản cuối: delegate HR list/detail/dialog/profile/account, đầy đủ badge/nút/reason/preview/re-auth/cancel, user thường, khóa tài khoản, keyboard xuyên modal, reduced-motion và desktop/mobile cùng dữ liệu. HOOT48 mới chờ kết quả. Không ghi AD09 PASS trước kiểm DOM/browser sau sửa. |

## 4. Nguyên nhân đã xử lý và giới hạn có chủ ý

- **Quyền không thể suy từ một group/menu:** Odoo20 cộng permission nhưng còn
  restriction, field groups và capability riêng. Adapter cộng domain ngoài
  phòng tại model cụ thể, giữ callback/quyền nghiệp vụ gốc; không giả
  `has_group`/`isSystem` hoặc cấp nhóm HR/system để vượt cổng. E02/E04 kiểm
  phạm vi được nêu trong ma trận, chưa xác nhận full admin mọi model.
- **Lách create bằng context-default:** guard cũ đọc riêng `vals` trước khi
  Odoo bổ sung mặc định, có thể bỏ sót employee/user đích. Đã xét giá trị
  effective từ default và vals, khóa đúng subject khi tạo responsibility;
  E03 2/2 và E02 35/35 đạt cho bản sửa này.
- **Race dùng quyền/nguồn cũ:** request ghi giữ shared authority/source locks;
  thay quyền/nguồn dùng fence tương ứng. E05/E06 chứng minh thứ tự commit và
  serialization failure bằng transaction thật. Đây chưa là test nhiều worker.
- **HR private và lỗi native view là hai việc riêng:** giữ groups cho trường
  riêng tư nhằm tránh mở lương/hồ sơ nhạy cảm ngay trong phòng actor. List/form
  cho delegate phải dùng tập field hợp lệ; lỗi parse `tp_employment_kind`
  đang được sửa ở safe view. Unit guard PASS không chứng minh view render được.
- **Nguồn shared/lịch sử chưa rõ:** Reporting aggregate/value/snapshot/carry,
  Kho stock/vendor/proposal/inventory hoặc history thiếu frozen department
  không được cấp thêm chỉ vì header hiện tại ở phòng khác. Gaps này là giới
  hạn implementation hiện có so với yêu cầu full CRUD, cần scope/adapter/test
  tiếp nếu muốn mở rộng; không đổi thành PASS bằng mô tả policy.

## 5. Cổng còn lại

1. Chốt safe HR view, chạy check phù hợp và kiểm browser bằng delegate; ghi
   source manifest cuối cùng, kết quả HOOT mới, ảnh/DOM và lỗi console thực tế.
   R11/R2 vẫn giữ là các snapshot PASS trước thay đổi đó.
2. Chủ batch ghi môi trường đã áp thực tế, backup/fingerprint/smoke/checksum;
   chỉ cập nhật ô main/server sau có kết quả. Dọn fixture test còn giữ cho
   browser và ghi evidence dọn riêng; E06 chỉ xác nhận fixture bổ sung Kho.
3. Chạy hoặc giữ NOT_RUN có lý do cho các hàng còn thiếu, nhất là nhiều worker,
   workflow/full CRUD, HR private và Reporting shared. Không dùng triển khai
   kỹ thuật để tự xác nhận nghiệm thu nghiệp vụ hoặc cho người thật nhận quyền.

Đây là kiểm kỹ thuật và review trong cùng nhóm thực thi, chưa là audit độc lập,
phản hồi hình thức của người dùng, nghiệm thu nghiệp vụ hoặc pilot authorization.
Kết quả media và nguyên nhân thiếu blob ở
[DEPLOY-MEDIA-001](DEPLOY_MEDIA_001_ACCEPTANCE.md), tách khỏi delegation.

## 6. Tiếp tục và rollout

Evidence mới: backup-dev-resume/ (dump9.601.550byte,924filestore entries/code/config/checksum), install-dev-resume.log exit0/0ERROR; dev-resume-before/after-install.json20bảng giữhash, baseURLgiữ, ledger0/0. ui-dev/result.json4/4; hoot-main-resume/result.json48/48/243assertions. Asset kỹ thuật mới, không user/nghiệp vụ giả. resume-media-result.json83/83,server665rows/168blob; PDF/Word/Excel0mẫu. Review cùng phiên; subagent không khởi tạo được do modelruntime. ServerReporting chưa cài, dùng dependencyGit hiện hành, không mang foreigndiff Reporting. Không chạmDBtest; fixture giả cũ vẫn giữ.
