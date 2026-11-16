# HR-LIST-013 — Nhóm phòng ban cố định trong danh sách nhân viên

13/11/2026, CHG-20261113-004. Phản hồi trực tiếp của người dùng kèm hai ảnh
thay cơ chế nhóm mặc định có facet của012: phòng ban là cách trình bày cố
định, không phải thẻ nhóm có nút ×. Chỉ sửa danh sách nhân viên; các màn HR
khác và workflow hiện có giữ nguyên. Đây là follow-up triển khai được yêu cầu
trực tiếp; sau lượt này trở lại vai điều phối mặc định. Không stage/commit/push.

## Kết quả và source

`tp_hr_workspace` **20.0.1.10.2**, bốn file application/test:

- `static/src/table/table.js`: `HrListModel` kế thừa RelationalModel chỉ trong
  `tp_hr_table`; với hr.employee list luôn thêm department_id đầu groupBy trước
  native config normalization/cache handling. Không patch model toàn cục.
- `views/workspace.xml`: bỏ default_group_by và bộ chọn group-by phòng ban;
  giữ field tìm theo đơn vị để lọc domain thật. SearchModel không có facet
  phòng ban mặc định; xóa tìm kiếm/bộ lọc/nhóm phụ vẫn giữ nhóm phòng ban.
- `static/tests/hr_mounted.test.js`: kiểm mount không facet, nhóm/cột đúng,
  tìm không có kết quả rồi xóa; bỏ bộ lọc và nhóm phụ vẫn giữ nhóm phòng ban.
  Test danh mục khác vẫn được bỏ nhóm thành bảng phẳng.
- `__manifest__.py`: patch version. Không backend/ACL/API/schema/migration.

Giữ dải xanh #CBF3F7, số thành viên, cột chữ và các nút native của012.
Không hiện header/ô Đơn vị / Phòng ban ở từng nhân viên. Bấm tên/dòng mở hồ
sơ 5 tab; tìm kiếm, sắp xếp và phân trang vẫn dùng backend/rules Odoo.

## Kiểm đã chạy

| Kiểm | Kết quả |
| --- | --- |
| XML / JS | workspace.xml parse PASS; node --check table.js và hr_mounted.test.js PASS |
| Odoo test | TestHrUi **3/3, 0 failed/0 errors** trên test18079; [log](../../.local/hr-list013/odoo-ui-tests.log) |
| HOOT | HR37+KD2 = **39 tests PASS**, Home30+KD1 = **31 PASS**; [HR](../../.local/hr-list013/hoot-hr.txt), [Home](../../.local/hr-list013/hoot-home.txt) |
| Browser | **9/9 nhóm mỗi cổng test18079/main18069, 0 console/page errors**: không facet, cố định nhóm sau xóa tìm kiếm, backend group limit10/20/50/100, profile/back,4viewport1440/1280/390/320, HR catalog và KH-KD isolation; [test](../../.local/hr-list013/verify-test.json), [main](../../.local/hr-list013/verify-main.json) |
| Main preservation | 588/600 rowsets nguyên trước HTTP;583/600 sau smoke.17delta chỉ metadata/assets/cron/signaling/bus/presence/login/device. Business/auth/version/role/code/audit không đổi; ACL953policy/57groups/632nonasset attachment rows+blob SHA giữ; [rowdiff](../../.local/hr-list013/rowdiff-main-final.json), [preservation](../../.local/hr-list013/preservation-after-smoke.json) |

Lượt HOOT đầu thất bại do callback kiểm RPC trả về assertion và selector nhãn
facet của test không khớp; đã sửa test rồi chạy lại toàn bộ đạt. Browser harness
có race page-size: đã chờ đúng response hoàn tất và UI render, chạy lại9/9.
Không tính lượt fail là pass, không sửa application để che lỗi test.
Không chạy lại77backend tests vì không đổi model/security/workflow. Tự review
source/callers vì subagent model kế thừa không khả dụng; không gọi là audit độc
lập. Mobile là giả lập. Visual/business/pilot cần người dùng xác nhận riêng.

## Ảnh trước–sau

Cùng admin/route/dataset/viewport1440 trên mỗi môi trường; ảnh desktop main,
test và mobile test390 đã mở tự xem. Không đổi dữ liệu để khớp ảnh tham chiếu.

- [Main trước1440](../../.local/hr-list013/before-main.png) / [main sau1440](../../.local/hr-list013/after-main-1440.png)
- [Test trước1440](../../.local/hr-list013/before-test.png) / [test sau1440](../../.local/hr-list013/after-test-1440.png)
- [Main1280](../../.local/hr-list013/after-main-1280.png), [main390](../../.local/hr-list013/after-main-390.png), [main320](../../.local/hr-list013/after-main-320.png)

## Apply và rollback

- Backup main **backup-tp_tanphat_dev-20261113T060634715405Z**,600tables/
  666blobrefs tại `.local/hr001/`; source trước sửa013 có riêng ZIP+SHA256.
- Dừng đúng main listener/config và wrapper; xác nhận **0 session khác** rồi
  upgrade chỉ HR với --no-http --stop-after-init trong cùng shell có exit-code
  guard. Exit0; xác nhận main chưa nghe HTTP, đối chiếu bảo toàn rồi start.
- Test/main đều version20.0.1.10.2;40employee/28users/9active. Main15department,
  test13department giữ nguyên. Cả18069/18079 chạy. Không DB/fixture mới,
  không restore test đè main. Reuse restore rehearsal011 cùngschema600/666/432;
  không chạy lại restore cho bản sửa static/view này.
- Rollback riêng013: dừng đúng main, trả đúng4file từ
  `.local/hr-list013/rollback-source.zip`, kiểm SHA256 trong
  `rollback-source.json`; upgrade HR20.0.1.10.1 noHTTP, restart/assets và smoke.
  Không rollback toàn011/012. Nếu cần restore DB, đánh giá giao dịch mới trước
  dùng backup; không dùng test làm nguồn main.

Bước tiếp: Ctrl+F5 [Danh sách nhân viên main](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_employees)
và review. README/guide/roadmap/status/changelog cập nhật cùng lượt;012 giữ
lịch sử kèm thông báo cơ chế nhóm đã được013 thay thế.
