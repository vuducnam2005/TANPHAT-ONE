# HR-EMPLOYEE-XLSX-001 — Xuất danh sách nhân viên

Ngày19/11/2026 · CHG-20261119-006 · `tp_hr_workspace`20.0.1.14.0 · MAIN_AND_PC_SERVER_APPLIED.

## Cách dùng

Vào TP HR → Danh sách nhân viên → **Xuất Excel**. Desktop: cạnh Thêm nhân viên; mobile: nút rõ trong thanh điều hướng. Có ở danh sách nhân viên native và các danh sách HR liên quan, không ở popup quan hệ.

- **Theo bộ lọc đang áp dụng** (mặc định): tất cả kết quả tìm kiếm/bộ lọc nâng cao đã áp, gồm nhóm thu gọn và trang sau. Điều kiện đang nhập chưa Áp dụng chưa ảnh hưởng file.
- **Toàn bộ nhân viên trong quyền quản lý**: các công ty đang chọn và quyền bản ghi/trường hiện có, kể cả lưu trữ; bỏ bộ lọc đang xem.
- **Các nhân viên đã chọn**: chỉ bật khi có chọn dòng; chọn toàn bộ kết quả giữ cả domain đã áp. ID thêm từ client vẫn giao với domain/quyền.

Dialog ghi rõ tổng nhân viên, không lấy tổng nhóm. Export đọc DB hiện hành; không đọc Excel nguồn hoặc thứ tự DOM.

## Cấu trúc và cột thực

Sheet **Danh sách nhân viên** có10 cột: STT, Mã nhân viên, Họ và tên, Phòng ban, Chức vụ, Loại hình lao động, Số điện thoại, Email công việc, Tên đăng nhập, Tình trạng tài khoản. Phân nhóm phòng, STT liên tục; Mở/Khóa/Chưa có tài khoản có chữ+màu, riêng với hồ sơ đang quản lý/lưu trữ.

Sheet **Dữ liệu chi tiết** có57 cột thực dưới đây với admin trên18069. Field không được quyền đọc bị bỏ; giá trị chưa khai báo để trống hoặc nhãn nullable, không suy đoán. Một dòng/nhân viên, không merge/hàng phòng trong vùng dữ liệu; AutoFilter toàn bảng. Không xuất lương, ngân hàng, credential, session, binary hoặc nội dung đính kèm.

| # | Cột |
| --- | --- |
| 1 | STT |
| 2 | Mã nhân viên |
| 3 | Họ và tên |
| 4 | Phòng ban |
| 5 | Chức vụ |
| 6 | Loại hình lao động |
| 7 | Số điện thoại |
| 8 | Email công việc |
| 9 | Tên đăng nhập |
| 10 | Tình trạng tài khoản |
| 11 | Tình trạng hồ sơ |
| 12 | Điện thoại công việc |
| 13 | Công ty |
| 14 | Chức danh mô tả |
| 15 | Chức vụ nguồn |
| 16 | Quản lý trực tiếp |
| 17 | Người hướng dẫn |
| 18 | Nơi làm việc |
| 19 | Địa chỉ làm việc |
| 20 | Lịch làm việc |
| 21 | Nhãn nhân viên |
| 22 | Họ tên pháp lý |
| 23 | Ngày sinh |
| 24 | Giới tính |
| 25 | Quốc tịch |
| 26 | Nơi sinh |
| 27 | Quốc gia nơi sinh |
| 28 | Điện thoại cá nhân |
| 29 | Email cá nhân |
| 30 | Địa chỉ cá nhân |
| 31 | Phường / Xã |
| 32 | Quận / Huyện |
| 33 | Tỉnh / Thành phố |
| 34 | Mã bưu chính |
| 35 | Quốc gia cư trú |
| 36 | Số CCCD / CMND |
| 37 | Số hộ chiếu |
| 38 | Hạn hộ chiếu |
| 39 | Số giấy phép lao động |
| 40 | Hạn giấy phép lao động |
| 41 | Số thị thực |
| 42 | Hạn thị thực |
| 43 | Tình trạng hôn nhân |
| 44 | Họ tên vợ / chồng |
| 45 | Ngày sinh vợ / chồng |
| 46 | Số con phụ thuộc |
| 47 | Trình độ học vấn |
| 48 | Chuyên ngành |
| 49 | Liên hệ khẩn cấp |
| 50 | Điện thoại khẩn cấp |
| 51 | Ngày hiệu lực hồ sơ |
| 52 | Ngày bắt đầu hợp đồng hiện tại |
| 53 | Ngày kết thúc hợp đồng hiện tại |
| 54 | Ngày hết thử việc |
| 55 | Ngày nghỉ việc |
| 56 | Thông tin cần bổ sung |
| 57 | Ghi chú |

Sheet **Hợp đồng lao động** chỉ tạo khi có dữ liệu và quyền đọc `tp.hr.contract.document`/`hr.version`, cùng công ty/phạm vi nhân viên. Cột: STT, Mã nhân viên, Họ và tên, Phòng ban, Số hợp đồng, Tên/trích yếu, Loại giấy tờ, Ngày ký, Ngày bắt đầu/kết thúc thuê khoán, Ghi chú hợp đồng, Ngày bắt đầu/kết thúc hợp đồng. Một nhân viên có nhiều hợp đồng thành nhiều dòng tại sheet này; hai sheet danh sách vẫn một dòng/người. Native kỳ hợp đồng trùng được gộp theo cặp ngày; không tải file đính kèm.

## Thứ tự và schema

Baseline không có field lưu thứ tự phòng tùy chỉnh. Thêm `hr.department.tp_sequence` (index, mặc định10) và `_order=tp_sequence,id`; native handle tại Phòng ban và đơn vị. Migration một lần khởi tạo theo `name,id` trước đây, giữ thứ tự cũ. Không sắp nhân viên theo tên/chức vụ/mã/trưởng phòng. Mọi sheet lặp nhân viên theo phòng `tp_sequence,id`, rồi `employee.sequence,id`, phòng chưa khai báo cuối. Export không write sequence hoặc hồ sơ.

`employee_export_order_key` pure test đổi sequence hai nhân viên, đổi sequence phòng và kiểm tie bằngID đều đúng. ORM READ ONLY đối chiếu toàn bộ thứ tự DB với hai sheet. Chưa thực hiện kéo ghi/reload người thật vì người dùng cấm đổi dữ liệu thật để thử; Odoo fixture tests đã bổ sung nhưng chưa chạy trên DB đang dùng. Không gọi kết quả pure/readonly là kiểm persist giao dịch thật.

## Kiểm tra kỹ thuật

| Kiểm tra | Kết quả |
| --- | --- |
| Workbook pure tests: literal formula, text điện thoại/mã, ngày/số0, quyền field, empty,123 dòng, thứ tự thay đổi | 5/5 PASS |
| Employee order backend pure hồi quy | 12/12 PASS |
| ORM18069 `SET TRANSACTION READ ONLY`: count/order/2sheet/selected/select-all/domain lỗi/credential/non-HR/ID&company giả/date granularity | 22/22 PASS |
| Browser dùng lại phiên admin hiện có, không đăng nhập mới | 8/8 PASS, 0JSerror;1440×900 và390×844 |
| File thực tải từ endpoint: đầy đủ/nhóm đóng/all-managed39, tìmNguyễn15, nâng cao chưa tài khoản31, chọn1 | 6/6 parse/cardinality/unique/order/no-formula PASS |
| Excel desktop mở read-only và xuất PDF workbook minh họa | PASS; navy/header/nhóm/xuống dòng/status/phone số0 được kiểm ảnh |
| Python AST, XML, Ruff, Node syntax | PASS |

Workbook chính A3 ngang, fit1trang theo chiều rộng; chi tiết A4 ngang85% để chia panel nhiều trang mà không ép57cột vào1trang; lặp header, footer số trang, freezeD7, mã/điện thoại/giấy tờ text và ngàyExcel dd/mm/yyyy. Ghi chú wrap và hàng tự tăng chiều cao.

Ảnh và workbook minh họa không chứa dữ liệu nhân sự thật: `.local/hr-employee-xlsx001/workbook-preview-crop.png`, `workbook-preview.xlsx`, `workbook-preview.pdf`. Workbook/screenshot thật để kiểm chỉ nằm trong ignored `.local/hr-employee-xlsx001/browser`, không đưa Git.

## Triển khai và giới hạn

Local18069 đã backup `.local/hr-employee-xlsx001/backup-20261119T114145` (dump/restore-list15787entry,filestore1077file,source/config,SHA256), upgrade chỉHR exit0; snapshot employee39/roster/employeeSequence/users/groups/implied/equipment/attendance/grants/baseURL giữ nguyên; chỉ versionHR đổi. Không18079, không fixture trên main/server, không reset login hoặc thay session winner.

PC server: đã giao app2c397ffb, xem biên bản phía dưới. Giữ tunnel và các addon ngoài scope. Rollback cần giữ trạng thái mới, restore đồng bộ dump+filestore+source/config từ backup server; không dùng backup local thay server. Không rollback tự động bằng cách xóa field/sequence.

Technical verification như trên; chưa là business/visual acceptance của người dùng hoặc pilot authorization mới. Chưa có real-device iOS/Safari và authenticated browser E2E public.

## Giao bản PC server — CHG-20261119-008

- App commit **2c397ffb19a060696472004a5b805f93601ef9c3**, đã push `origin/main`; moduleHR **20.0.1.14.0**, local18069 và PCserver. Chỉ áp16tệp trongscope, đúngSHA256; `-u tp_hr_workspace` exit0/0ERROR; cácmodulekhác giữversion cũ tại thời điểm giao.
- Backup server **C:/TANPHAT-backups/hr-employee-xlsx001/hr-xlsx006-20261119T120938**: dump10.163.359B, restore-list15.787entry; filestore32.737.554B/631entry; source-config2.193.386B; SHA256SUMS.json. Đây làbackupserver riêng, không dùngbackup18069 thay thế.
- Snapshot trước/sau giữ39employee/32user, digestemployeeSequence/roster/groups/implied/ledger/equipment/480ngày công/baseURL; chỉversionHR đổi. Server READ ONLY22/22PASS,39employee/57cột/3sheet, gồm từ chối nonHR/credential/domainlỗi vàID/companygiả.
- Public `https://eight-championships-launches-plaintiff.trycloudflare.com`: health/login200. CSS `/web/assets/73d8d48/web.assets_web.min.css`1.632.606B, SHA256 `3dda3b6e09d97c753d55c896cb0592cc2cdb8ff1430fc6f2a50136eb6c98cff2`; JS `/web/assets/e1de7bf/web.assets_web.min.js`8.480.014B, SHA256 `bd588a0bbc30d9f0dd839a51d13b5deb9f59f6b79fdd7b2d83700a4e7e9d9cd7`. Bytes/SHA256giốngserver, đã kiểm selector/function/dialog mới.
- Không ra lệnh thay cấu hình/restart tunnel; quan sát container tunnel restart trong lúc origin dừng và public đã hồi phục. Chưa authenticated public browserE2E: không có phiênadminserver hợp lệ sẵn để tái dùng; không tạo loginmới thayphiên. Browser8/8 làlocal với phiêncó sẵn. Technical verification chưa thaybusiness/visual acceptance của người dùng.
- Người dùng Ctrl+F5, TP HR → Danh sách nhân viên → Xuất Excel. Thứ tựphòng chỉnh ở Phòng ban và đơn vị; thứ tựnhân viên dùngkéo cảhàng cùngphòng hiện có. Không chạyfixtures hoặc thaythứtự thật để thử. GiữWIP/checkpointngoài scope; workflowsealGit trongsnapshot riêng.
