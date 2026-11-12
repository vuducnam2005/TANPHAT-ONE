# UI-CTR-NATIVE-001a — Audit implementation độc lập

Ngày 06/11/2026 (Asia/Saigon), `CHG-20261106-003`. Audit implementation `CHG-20261106-002` theo [prompt](../prompts/CLAUDE_UI_CTR_NATIVE_001A.md), [đặc tả](../architecture/TP_UI_CTR_NATIVE_001_SPEC.md) và [bàn giao thực thi](UI_CTR_NATIVE_001A_IMPLEMENTATION.md). Vai trò điều phối DEC-022; không sửa application code hoặc áp dev.

**Kết luận: `TECHNICAL_ACCEPTED_TEST_ONLY` cho slice 001a.** Không phát hiện finding cần correction trong phạm vi đã kiểm. Luồng native gọi backend hiện có và các kiểm soát D1/D2 đạt kiểm tra trên implementation thật; AT-17 đạt với mô phỏng ngày/request mới. Đây không phải nghiệm thu nghiệp vụ, pilot authorization, nghiệm thu toàn hệ thống hoặc quyết định chính sách G7.

## 1. Baseline và phạm vi

- Checker đầu lượt PASS cho CHG-20261106-002; không có checkpoint thực thi còn dở. Audit tạo checkpoint riêng trước tài liệu bàn giao, không finish hộ phiên khác.
- Maintained source: **238 file**, digest `ac21fef513ab8a17ba90b5887a58900a7b0ee156e53052ef34311d775bbe25af`, khớp bàn giao CHG002 cả trước và sau kiểm. File browser `.cjs` và translation `.po` ngoài extension checker được so SHA256 riêng với inventory của implementation và đều khớp.
- Review `tp_contract_native.py`, restriction trong `ir.access.csv`, XML/menu/action và test native; đối chiếu helper workflow, grant, assignment, model tài liệu và cơ chế freeze/snapshot hiện có. Không dùng kết quả audit đặc tả để suy implementation đã đạt.
- Chỉ cập nhật báo cáo audit, status, changelog, roadmap và nhãn nghiệm thu trong spec. Evidence/helper audit riêng dưới `.local/ctr-native001-independent-audit/`; không sửa script/test/application đã bàn giao.
- Protected paths `odoo/`, `addons/`, `frontend/src`, `frontend/tests`, `contracts/openapi` không có Git diff. Không reset/clean/stash/stage/commit/push; giữ các thay đổi có sẵn và tài liệu deliverables của người dùng.

## 2. Kiểm độc lập đã thực chạy

| Kiểm | Kết quả và bằng chứng |
| --- | --- |
| Odoo regression trên owned clone | **107/107**, 0 failed/errors/ERROR, đúng DB `tp_tanphat_stab001_20261105`; `tp_contract`73, `tp_project`12, `tp_planning_api`22. Log/verdict mới: `.local/native-stabilize001/odoo-tests/run-20261106T045827388402Z.{log,json}` |
| Runner unit | **18/18** bằng `python -m unittest discover -s scripts/tests -p test_native_stabilize001.py -q` |
| Native browser | **42/42**, Chromium, live owned clone18169 với 5 actor giả; kết quả mới `.local/ctr-native001-independent-audit/browser/browser-result.json` |
| Native UI thực hiện | Nháp→sửa metadata/tiền→gửi→reviewer trả lại→mở sửa→sửa→gửi lại; metadata-only; stale version/tải lại; retry cùng wizard; tài liệu general tải được, financial bị chặn cho reader; outsider không thấy hợp đồng |
| Responsive/zoom | 360/390/768/1280/1440, list/form/wizard; Chromium zoom thật125/150 ở1280/1440. 0 tràn trang theo assertion; 0 console/network lỗi bất ngờ ở 5 actor. Đã xem ảnh desktop, wizard390 và zoom1280/150 |
| Static | Ruff các Python thay đổi PASS; XML parse/manifest literal PASS; `node --check scripts/ctr_native001_ui.cjs` PASS; `scripts/check_contract.py` PASS; `git diff --check` PASS, chỉ cảnh báo LF/CRLF |
| Runtime | Hai probe SQL **read-only=on** vào dev/clone trước và sau browser; evidence `before-browser.json`, `after-browser.json` trong thư mục audit |

Lệnh Odoo:

```powershell
.\.venv\Scripts\python.exe scripts/native_stabilize001.py stop
.\.venv\Scripts\python.exe scripts/native_stabilize001.py odoo-tests --modules tp_contract,tp_project,tp_planning_api --tags /tp_contract,/tp_project,/tp_planning_api --expect-tests 107
.\.venv\Scripts\python.exe scripts/native_stabilize001.py start
```

Runner xác minh owner/config/token và chỉ stop/start/upgrade clone. Không gọi setup hoặc lệnh start tổng. Browser dùng nguyên assertions của implementation, chỉ đổi đường dẫn lưu ảnh/kết quả/profile trong bộ nhớ để giữ bằng chứng tự kiểm cũ. Không seed lại hoặc đổi mật khẩu fixture. Browser tạo thêm một hợp đồng giả và hai submission trên clone theo luồng được test; dev không nhận các dữ liệu này.

## 3. Đối chiếu 24 acceptance và kiểm soát

| Acceptance | Kết luận trong audit |
| --- | --- |
| AT-01 | PASS: menu/list/empty state theo quyền, Home có điểm vào thực tế |
| AT-02 | PASS: tiền và metadata theo grant trên view/read/group/export |
| AT-03 | PASS: tạo nháp qua adapter; quyền tiền bổ sung khi nhập tiền, không nới CRUD hợp đồng |
| AT-04 | PASS: sửa nháp với token form, state/version guard, lỗi stale và tải lại trên browser |
| AT-05 | PASS: submit/resubmit dùng reviewer được chọn, fix summary và backend hiện hành |
| AT-06 | PASS: đúng reviewer, khác người gửi, reason và scope ý kiến được kiểm |
| AT-07 | PASS: begin_rework có lý do, returned→draft qua workflow, snapshot lần trình giữ riêng |
| AT-08 | PASS: tên/file financial theo quyền; tải binary live bằng reader được phép/không được phép; upload không mở |
| AT-09 | PASS: điểm vào RPC hẹp, method private không mở, state/target/payload không ghi trực tiếp |
| AT-10a | PASS: revoke financial_read đóng input, compute và tiền gốc từ request mới |
| AT-10b | PASS: date_end hết hạn qua ORM đóng quyền; không dùng làm bằng chứng hết hạn tự nhiên |
| AT-10c | PASS: staff mất assignment/project thì header/child/input bị chặn |
| AT-10d | PASS: manager còn project/grant nhưng mất assignment chỉ giữ metadata wizard; tiền gốc theo G7; control bỏ guard đọc được |
| AT-10e | PASS: không lưu baseline tiền, cleanup input trong transaction, retry không nhân audit/submission |
| AT-10f | PASS: không relink target/header/child hoặc sửa key/kết quả; kiểm target trước workflow |
| AT-10g | PASS: metadata-only không cần financial_read; payload không chứa amount, tiền gốc giữ nguyên |
| AT-11 | PASS: không mở BASE/review_complete/ký/hiệu lực/hủy/thanh toán |
| AT-12 | PASS: 42 browser assertions cùng responsive/zoom trong phạm vi Chromium |
| AT-13 | PASS trong regression đã chạy lại: Odoo107, runner18, OpenAPI và protected source diff; React9 unit+6 mock E2E là evidence CHG002 đã đọc, không chạy lại vì React/API không đổi |
| AT-14 | PASS: 8 model wizard/child hạn chế theo owner trên ORM/RPC/read/search/count/group/export/web_read/write/unlink/create |
| AT-15 | PASS: nhiều group hoặc broad permission không vượt global restriction; control gỡ owner đọc được |
| AT-16 | PASS: target/company/project/key/context tiền giả mạo bị chuẩn hóa hoặc từ chối |
| AT-17 | PASS: freeze ngày kế tiếp không write grant hoặc gọi invalidate grant helper; `env.clear()` mô phỏng request mới, input/tiền gốc đóng và compute rỗng |
| AT-18 | PASS: owner còn cùng company nhưng mất project không đọc được child/nested header; control gỡ riêng parent-access restriction đọc được |

Native suite có **22 phương thức** cho 22 ID; AT-12 browser và AT-13 regression bổ sung thành 24 ID, không coi số phương thức là số ID. Các ca âm owner/D1/D2 có đối chứng cho thấy restriction/guard thực sự chặn dữ liệu, không chỉ dừng ở thiếu permission xuất dữ liệu.

Source xác nhận `action_confirm()` không nhận payload/action tùy ý, gọi `_tp_run` bằng user hiện tại và không sudo workflow; savepoint bao gồm transition, cleanup và kết quả. Tiền hiện tại chỉ compute không lưu sau guard project + capability; tiền mới ở model riêng có global owner/company/project/grant/assignment restriction. Sudo chỉ đếm input theo spec để tránh gửi thiếu tiền khi rule đã lọc mất dòng. API và ACL tiền gốc không bị sửa.

## 4. Giới hạn và môi trường cuối

- **Dev18069 không áp dụng:** SQL trước/sau xác nhận addon `20.0.1.1.0`, 0 model `tp.contract.native.*`, 0 actor `ctr_native001_*`, 3 hợp đồng/0 submission giữ nguyên tại hai probe. Đây không phải fingerprint toàn bộ database; không suy mọi bảng dev bất biến chỉ từ các số đếm này.
- **Test18169:** addon `20.0.1.2.0`,10 model registry (2 abstract +8 concrete),5 actor giả; cuối browser16 hợp đồng/16 submission so15/14 trước browser. Các ghi đều trên clone.
- Dev18069, PG55432 có sẵn và giữ chạy; clone18169 được dừng để test rồi bật lại, cuối lượt để chạy phục vụ review; demo18109 không mở. Cron0/SMTP loopback9/list_db=False của clone giữ theo cấu hình owned đã đọc.
- Chỉ Chromium viewport emulation và zoom thật; chưa nghiệm thu Safari/WebKit, thiết bị thật hoặc screen reader. AT-17 là mô phỏng thời gian và request, không phải chờ qua ngày trên browser thật.
- **G7 còn mở:** manager có grant còn đọc project nhưng mất assignment vẫn có thể đọc tiền gốc theo baseline; wizard cố ý chặt hơn. Không đổi policy/ACL gốc hoặc coi test này là đã chốt chính sách công ty.
- Q2/grant người thật, business acceptance và pilot vẫn mở. BASE approval/verification, review_complete, ký/hiệu lực, giao khoán/nghiệm thu/thanh toán, upload/phân loại tệp, cancel revision, TASK-001 và apply dashboard dev không được nghiệm thu/mở trong audit này.
- Odoo test trên clone chạy lại có upgrade `tp_contract,tp_project,tp_planning_api` đúng scope; dev không upgrade/restart/seed. Không tự restart dev để nạp source mới dùng chung; áp native lên dev phải là batch migration/test/backup riêng.

## 5. Bước tiếp theo

Phần hợp đồng native 001a có thể được **tái sử dụng** trong kế hoạch KH-KD; không viết lại sáu action hoặc chạy correction D1/D2 lặp lại. Bắt đầu KD-NATIVE-001 theo prompt đã chuẩn bị: inventory delta sau CHG002/003, workspace KH-KD và liên kết nguồn có sẵn, rồi từng domain còn thiếu.

Trước khi chức năng này xuất hiện trên **18069**, thực hiện batch tích hợp có snapshot DB/filestore/source đang sửa, thử clone/upgrade, fixture giả có provenance và kiểm quyền/bảo toàn dữ liệu dev. Audit test hiện tại không tự áp dev hoặc mở người thật. Kịch bản trình bày phải dùng menu/mã hồ sơ mà batch tích hợp đã kiểm; không lấy URL clone làm bằng chứng dev đã có chức năng.
