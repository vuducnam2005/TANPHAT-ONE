# KD-NATIVE-001 — Ma trận nghiệm thu thực thi

Ngày 06/11/2026. **IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT** trong phạm vi đã chốt254; thiếu6phụ lục theo quyết định người dùng. Test riêng18269 và dev18069 ghi riêng. Dữ liệu tổng hợp; technical verification không là business acceptance/pilot. Evidence private `.local/kd-native001/`.

| ID | Nhóm / actor / tiền điều kiện | Thao tác và kết quả bắt buộc | Test18269 | Dev18069 | Evidence |
| --- | --- | --- | --- | --- | --- |
| KD01 | Cơ hội; fixture chuẩn bị, project trong scope | Tạo/sửa, khách hàng/dự án, checklist/hạn, chuẩn bị/khai báo nộp; giao trực tiếp không cần nộp thầu giả | BACKEND_A4 / BROWSER_A10 phạm vi A | PASS A10; dataset27 | `dataset/dev/ui/a-browser.json` |
| KD02 | Dự án; reader/manager theo quyền | Mở tổng hợp, tạo/mở con đúng project, quay lại, cùng project.project | BACKEND_A4 / BROWSER_A10 phạm vi A | PASS mở nguồn và tạo con2 | `dataset/dev/project-child.json` |
| KD03 | Hợp đồng; editor + reviewer riêng, grants hiện tại | Nháp→gửi→trả có lý do→mở sửa→sửa→gửi lại; lịch sử/version persist | PASS73backend/42browser clone18269 | PASS contract13; thiếu6phụ lục theo gate đã chấp nhận | `dataset/dev/ui/contract-browser.json` |
| KD04 | WBS; manager fixture, staff đối chứng | Cha-con, owner/hạn/đầu ra/hợp đồng; manager tạo/sửa/giao; staff vẫn deny TASK-001 | PASS manager/staff trong A4 và D3; browser WBS5/5 | PASS WBS5 + staff deny final9 | `dataset/dev/ui/wbs-browser.json` |
| KD05 | Khoán; prepare/submit/review fixture | CRUD nháp, submit/return/rework/resubmit, cha-con, scope, cấp2 không cộng tổng | PASS10backend/12browser | PASS C1 12 + tạo con2 | `dataset/dev/ui/c1-browser.json` |
| KD06 | Sản lượng; grants đúng scope | CRUD/submit/return/rework/resubmit; kỳ/nguồn/task; không thành nghiệm thu ngoài | PASS C2 backend3 + regression10 / browser12 | PASS C2 12 + sửa seed/relogin | `dataset/dev/ui/c2-browser.json` |
| KD07 | Nghiệm thu; grants đúng scope | CRUD/submit/return/rework/resubmit, nguồn/phạm vi/đợt; chỉ hồ sơ nội bộ | PASS C3 backend2 + regression13 / browser12 | PASS C3 12 | `dataset/dev/ui/c3-browser.json` |
| KD08 | Đề nghị; grants đúng scope | CRUD/submit/return/rework/resubmit, kỳ/hạn, nguồn nghiệm thu hoặc căn cứ tạm ứng; không paid | PASS C4 backend2 + regression15 / browser12 | PASS C4 12 | `dataset/dev/ui/c4-browser.json` |
| KD09 | Nghĩa vụ; actor được phép | Checklist nội bộ có lịch sử, mở hồ sơ nguồn/thiếu; không thanh lý pháp lý | PASS D3 backend3 + regression21 / browser18 | PASS D3 18 | `dataset/dev/ui/d3-browser.json` |
| KD10 | Kế hoạch định kỳ; actor có quyền | Tháng/quý/năm, mục tiêu/đối chiếu đúng nguồn/kỳ; chưa xác nhận khác0 | PASS D1 backend2 + regression17 / browser12 | PASS D1 12 | `dataset/dev/ui/d1-browser.json` |
| KD11 | Năng lực/chứng chỉ; actor được phép | Tạo/sửa, còn/sắp/hết hạn, tìm phạm vi/mở cơ hội sử dụng; không chứng chỉ giả pháp lý | PASS D2 backend2 + regression19 / browser15 | PASS D2 15 | `dataset/dev/ui/d2-browser.json` |
| KD12 | Truyền thông/báo cáo; task manager + reader | Task/đầu ra native, báo cáo mở record nguồn, không gửi ra ngoài | PASS D3 và WBS5/5 | PASS WBS5/D3drilldown | `dataset/dev/ui/wbs-browser.json` |
| KD13 | Metadata/ngoài scope/cross-company | Không đọc tiền/files/count/export ngoài quyền, target FK phải kiểm backend | PASS backend133 trên clone, các ca âm/quyền/version/retry | PASS metadata money search/export deny; scope theo actor fixture | `dataset/dev/final-ui.json` |
| KD14 | Workflow | Thiếu reason, stale version, retry/race, sửa/xóa sau gửi bị chặn; không side effect một phần | PASS backend133 trên clone, các ca âm/quyền/version/retry | PASS typed stale/version; contract2submission | `dataset/dev/ui/contract-browser.json` |
| KD15 | Browser actor thường | 390/768/1440, không tràn trang, back/refresh/deep link; lỗi không báo thành công | PASS từng lô và dataset/browser mới | PASS responsive390/768/1440, refresh/deep link; có caveat phiên | `dataset/dev/browser.json` |
| KD16 | Dataset254 (đã chốt) | 12 nhóm/8project/100task;3chuỗi, registry/manifest/FK/chronology/unknown, không double count | PASS254/rehearsal13/browser26/restart | PASS254 +14UI riêng;8project/3chuỗi; thiếu6phụ lục | `dataset/dev/manifest.json` |
| KD17 | Persistence/idempotence | Seed2lần không trùng/reset password/overwrite; giữ sửa sau seed; relogin/restart còn record | PASS254/rehearsal13/browser26/restart | PASS seedlặp0/relogin/restart/giữ sửa | `dataset/dev/restart-persistence.json` |
| KD18 | Cleanup riêng | Dry-run không ghi; ownership/dependency/changed-record guard; clone unlink/archive/retained đúng policy | PASS rehearsal13, rollback15unlink/0archive | DRY_RUN_ONLY; KHÔNG APPLY | `dataset/dev/cleanup-last.json` |
| KD19 | Ops | Backup DB/filestore/config/source dirty + checksum, restore exact; dữ liệu cũ bảo toàn | PASS538bảng/249blob | PASS preservation22bảng;3assetcache được tạo lại;249blob nguyên | `../kd-native001-integration/preservation.json` |

Các mã và ID đã đọc từ dev nằm trong hướng dẫn trình bày và manifest; evidence trong bảng tính từ .local/kd-native001, trừ đường dẫn integration được nêu riêng. Giới hạn pháp lý/tài chính là ranh giới biểu diễn, không thay lý do bỏ thao tác quản trị hồ sơ.

Browser cold-start C4 lượt đầu nhận session-expired ở get_views; lượt đăng nhập mới chạy đủ12/12, không auto-retry mutation. Dev đã kiểm đăng nhập mới, đăng xuất/đăng nhập lại và đăng nhập sau restart; giới hạn phiên chập chờn vẫn được giữ trong bàn giao, không sửa cơ chế session trong scope.

D2 test-first ban đầu lỗi setup trùng grant opportunity; đã sửa fixture rồi chạy21/21. Browser lượt đầu nút project bị gom trong Thêm; lượt sau probe rời trang trước save xong tạo trùng hồ sơ clone. Probe cuối đợi response và assert1record,15/15; drilldown CRM dùng list/form KH-KD. Không xóa evidence lỗi.

D3 cuối: browser18/18 và WBS5/5; số19 nêu trong commentary là nhầm đếm, JSON18 là nguồn evidence. Hồi quy131/131 gồm workspace24/contract73/project12/planning22, log065514261217Z.

## Chốt tích hợp CHG-20261106-017

- Hồi quy cuối **133/133**: workspace26/contracts73/project12/planning22, log `.local/kd-native001/odoo-tests/20261106T080849721869Z.log`. Cài mới từ restore98/98 tại `.local/kd-native001-integration/odoo-tests/20261106T073356157766Z.log`. Không chạy bộ test tạo fixture backend trên dev.
- Dev browser **159/159 assertion**: A10 + contract13 + C1/C2/C3/C4 mỗi12 + D1 12 + D2 15 + D3 18 + WBS5 =121; dataset27 + search/filter/group/deny9 + project-create-child2 =159. Fresh UI login sau restart thêm1probe đạt. Evidence dưới `.local/kd-native001/dataset/dev/`, hoàn toàn riêng clone. Count assertion gồm login/layout, không gọi159ca nghiệp vụ độc lập.
- Source tái sử dụng UI001a; thêm registry/tool dữ liệu và chỉnh `__init__` không import tests khi runtime thường. Handoff016 đã có132; sửa context đổi model có RED1/1 rồi GREEN133. Dynamic action trước sửa kế thừa `form_view_ref` dự án khiến New trên hồ sơ con lỗi field `tp_managed`; nay bỏ view/default/search_default/active context cha, đặt default con rõ. Test kiểm10action và browser tạo con đúng canonical project trên clone/dev. Chỉ sửa method Python, không đổi quyền/workflow/API.
- Backup sát tích hợp `.local/kd-native001-integration/snapshot-20261106T073215Z`: DB/filestore/private config/secrets/maintained dirty+untracked source, upstream và frontend archive, cùng nguồn trước task cho runtime cũ. Manifest/checksum và restore **538rowsets/249blob exact** trên DB owned `tp_tanphat_kd001_restore_20261106` trước neutralize. Backup đầu phiên053207Z cũng giữ nguyên. Không dùng restore toàn DB để dọn lô.
- Bảo toàn theo hash từng dòng trên22bảng (bỏ write_date/write_uid, dùng common columns trước/sau migration): user/password/group, partner/đơn vị/nhân sự, project/task/assignment/grant, contract/revision/line/money/submission, account/expense/timesheet và attachment.21bảng không mất/đổi dòng baseline; attachment chỉ3cache `/web/assets/` IDs424/425/426 được Odoo tạo lại.249blob cũ vẫn cùngSHA1. Không account.move/payment/reconcile mới; module/grant/actor mới thuộc fixture. Không suy mọi bảng DB bất biến.
- **Sự cố vận hành được ghi nhận:** khi kiểm persistence, đã gọi nhầm CLI `scripts/dev.py stop`, làm PostgreSQL cũng dừng; `dev.py start` đã khởi động lại. Không gọi setup/upgrade/seed password qua CLI đó. Cấu hình/secrets so backup không đổi; DB/biểu mẫu/baseline/blob đã kiểm lại, dev18069/clone18169/clone18269 vàPG55432 sẵn sàng lại. Clone owned18269 được restart riêng sau đó. Bản sửa context áp bằng `native.dev.stop_server/start_server` chỉ Odoo, không PG. Không coi sự cố này là quy trình được phép cho lần sau.
- Migration đầu exit0 nhưng log có ERROR import test framework từ addon init; checker đã chặn, giữ log và dev dừng. Sửa init trên clone, hồi quy132 và normal-start sạch rồi mới tiếp tục. Lượt test chọn tag project nhưng không upgrade module có120test bị runner từ chối, không claim PASS; lượt cuối133tag đủ. Probe form/group/smartbutton và session có lượt lỗi được giữ; bản ghi phát sinh không bị xóa để che lỗi.
- Bộ seed254giữ nguyên, thiếu6phụ lục theo quyết định trực tiếp.14hồ sơ UI ngoài seed có registry riêng,4welcome task là support. Dry-run cleanup dev không ghi; không cleanup apply dev. Không business acceptance/pilot; Q2/G7/TASK-001, BASE/ký/hiệu lực/thu chi thật/upload/grant thật giữ gate.

## Giới hạn còn lại

Phiên native đôi lúc hiện session-expired khi automation điều hướng/login; lượt đăng nhập mới đạt, không retry ghi tự động hoặc sửa core/session. Cần đăng nhập và mở sẵn hồ sơ trước trình bày, kiểm state nếu gặp lỗi. WinError5 filestoreGC trên clone là INFO cũ được giữ log, không xóa blob để làm log sạch. Chỉ Chromium emulation; chưa Safari/thiết bị thật/trình đọc màn hình. Kết quả là tự kiểm triển khai, chờ audit độc lập/nghiệm thu nghiệp vụ theo quy trình riêng.


## Phục hồi khi cần

Bản sửa context chỉ đổi Python, có nguồn trước sửa tại .local/kd-native001-integration/pre-context-fix-source/; rollback phần này bằng đối chiếu/copy đúng delta rồi restart riêng Odoo qua scripts.dev.stop_server/start_server, giữ DB/254seed/14UI. Không gọi CLI dev.py stop vì nó dừng cả PostgreSQL. Nếu lỗi schema từ lô tích hợp, dùng snapshot073215Z gồm dump/filestore/config/source và kiểm owner/checksum trước khi restore; đánh giá, bảo toàn mọi chỉnh sửa sau snapshot trước, không restore toàn DB để dọn mẫu. Clone restore exact đã là bằng chứng khả năng phục hồi; không phải lệnh tự động phục hồi dev hiện đang đạt.
