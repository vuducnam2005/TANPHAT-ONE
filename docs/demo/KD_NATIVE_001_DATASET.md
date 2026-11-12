# KD-NATIVE-001 — Bộ dữ liệu tổng hợp lưu trong Odoo

Ngày 06/11/2026. Dataset `KD_NATIVE_001_REALISTIC_V1`, namespace `tp_kd_native001_realistic_v1`. Nội dung tổng hợp sát nghiệp vụ, không phải hồ sơ thực tế của công ty. Bản ghi nằm trong PostgreSQL của Odoo; manifest chỉ dùng nhận diện và đối chiếu.

Người dùng đã chọn **giữ254, ghi rõ thiếu6phụ lục**. Workflow audited không cho `create_amendment` khi còn revision đang xử lý; task chưa mở `review_complete`. Không tạo trạng thái pháp lý hoặc loại hồ sơ khác để bù mục tiêu260.

| Nhóm | Số đã kiểm trên clone18269 | Dev18069 |
| --- | ---: | --- |
| Khách hàng/đối tác | 12 | 12 |
| Cơ hội/hồ sơ thầu | 12 | 12 |
| Dự án | 8 | 8 |
| Hợp đồng | 10 | 10 |
| Phụ lục | 0 (thiếu6) | 0 (thiếu6) |
| WBS/công việc | 100 | 100 |
| Giao khoán | 16 | 16 |
| Sản lượng | 24 | 24 |
| Hồ sơ nghiệm thu | 16 | 16 |
| Đề nghị thanh toán/đối chiếu | 20 | 20 |
| Kế hoạch định kỳ | 16 | 16 |
| Năng lực/chứng chỉ | 12 | 12 |
| Nghĩa vụ/checklist | 8 | 8 |
| **Tổng nghiệp vụ** | **254** | **254** |

Không cộng actor, grant, assignment, revision gốc, dòng tiền hoặc event vào254. Mỗi môi trường có số registry hỗ trợ riêng; không suy ID dev từ clone. Tái sử dụng công ty, VND và phòng Kế hoạch Kinh doanh với `owned=false`; không nhận ownership dữ liệu cũ.

Tám mã dự án: `KD26-ANP`, `KD26-HLM`, `KD26-NTH`, `KD26-DVT`, `KD26-BSN`, `KD26-PLC`, `KD26-THA`, `KD26-HPT`. Hợp đồng `KD26-HD-01`…`KD26-HD-10`. Hồ sơ có mã `KD26-GK-01`…16, `KD26-SL-01`…24, `KD26-NT-01`…16, `KD26-TT-01`…20, `KD26-KH-01`…16, `KD26-NL-01`…12, `KD26-NV-01`…08. Stable key dùng chữ thường và dấu gạch dưới; WBS `task_01_01`…`task_08_06`. Ba dự án đầu có chuỗi CRM→hợp đồng→WBS→khoán→sản lượng→nghiệm thu→đề nghị→nghĩa vụ. Các dự án sau phân bố theo mức chuẩn bị, không ép đủ chứng từ.

Kế hoạch gồm12tháng, quý1/2/4 và năm2026 trên An Phú; không cộng tháng/quý/năm. Ngày mốc cố định của dataset là06/11/2026; quá hạn7ngày, đến hạn3ngày, chứng chỉ30ngày là kịch bản minh họa. Tiền dùng VND, căn cứ và trạng thái riêng, chưa xác nhận khác0; hồ sơ không đồng nghĩa đã ký, có hiệu lực, nghiệm thu ngoài hoặc tiền đã thu/chi. Chứng chỉ là hồ sơ năng lực tổ chức tổng hợp; quyền cá nhân được kiểm riêng trong test.

Registry bền trong DB: `tp.kd.dataset` và `tp.kd.dataset.entry`, cùng external IDs. Entry ghi model/ID/key/owned/category/checksum/status; danh tính bất biến, không cấp ACL cho người dùng thường. Manifest private tại `.local/kd-native001/dataset/<clone|dev>/manifest.json` có dependency và drift. Credential tại `credentials.json` cùng thư mục; không đưa password, dump hoặc filestore vào Git.

Lệnh từ `C:\TANPHAT ONE`:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/kd_native001_dataset.py inventory --target dev --dataset KD_NATIVE_001_REALISTIC_V1
.\.venv\Scripts\python.exe -X utf8 scripts/kd_native001_dataset.py verify --target dev --dataset KD_NATIVE_001_REALISTIC_V1
.\.venv\Scripts\python.exe -X utf8 scripts/kd_native001_dataset.py cleanup --target dev --dataset KD_NATIVE_001_REALISTIC_V1
```

`cleanup` mặc định chỉ dry-run, xuất `cleanup-last.json`; không sửa DB. Chọn bằng registry, không bằng prefix tên/project. Công cụ từ chối `--apply` trên dev trong task này. Khi có yêu cầu dọn sau này, phải backup mới, clone-test, review dependency/drift và mở batch cho đúng dev; không bỏ guard bằng sửa cờ tùy tiện. Mẫu apply **chỉ cho clone owned18269**, cần chuỗi chính xác:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/kd_native001_dataset.py cleanup --target clone --dataset KD_NATIVE_001_REALISTIC_V1 --apply --confirm tp_tanphat_kd001_20261106:KD_NATIVE_001_REALISTIC_V1
```

Chỉ unlink nháp owned, không có lịch sử/tham chiếu ngoài/sửa đổi và được policy model cho phép. Giữ master/actor/grant/support/audit, hồ sơ đã gửi và mọi dependency liên quan. Không reset state, xóa log, SQL cascade hoặc hứa dọn sạch. Không tự archive vì các typed model chưa có semantics loại khỏi tập làm việc; số archive hiện0. Native child chỉ đi theo unlink cha khi cũng owned, checksum khớp và model cho phép. Dữ liệu được phát triển thêm sau seed được giữ và báo drift; seed lặp không reset password, workflow hoặc ghi đè sửa đổi.

Mốc clone tại CHG-20261106-016: rehearsal13check đạt, gồm target/confirmation guard, dry-run không ghi, seed lặp tạo0, giữ sửa đổi/password, tham chiếu attachment ngoài chặn dọn và rollback bảo toàn tất cả rowsets. Diễn tập trong savepoint:15entry unlink,0archive,1117retained,3referenced; **đã rollback**,254bản ghi vẫn còn. Đây là số entry kỹ thuật của clone, không phải số hồ sơ bị xóa lâu dài. Browser26check và restart/fresh UI login đã chứng minh sửa nháp seed còn sau refresh, đăng xuất/đăng nhập lại và restart. Hồi quy132/132, log `20261106T072512099223Z.log`; hồi quy cuối CHG-20261106-017 đạt133/133, xem [ma trận nghiệm thu](KD_NATIVE_001_ACCEPTANCE.md).

Chưa áp cleanup trên dev; yêu cầu giữ dữ liệu sau tạo tiếp tục có hiệu lực.

## Kết quả dev18069 — CHG-20261106-017

`tp_tanphat_dev`: verify254đạt sau seed, seed lặp và restart. Seed lần đầu tạo666record cấp công cụ (gồm hỗ trợ), lần2tạo0/reuse666. Registry chính1453entry:1450owned/3referenced. Có drift được giữ: bản sửa UI của `KD26-SL-04`, liên kết của partner/project và partner của actor sau đăng nhập; không reseed đè để làm manifest sạch giả.

Để chứng minh người dùng tự tạo ngoài seed, browser tạo **14hồ sơ riêng**, dataset `KD_NATIVE_001_UI_PROBES_V1`, namespace `tp_kd_native001_ui_v1`, registry362entry tại lần chốt. Manifest private `ui-manifest.json` cùng thư mục dev ghi toàn bộ entry/category/checksum;4welcome task cá nhân do OdooBot tạo cho4actor được nhận diện là support, không cộng vào100WBS hoặc14hồ sơ. UI manifest có348support/14business theo JSON thực; số lượng hỗ trợ có thể tăng theo phiên nên dùng registry làm nguồn.

| Nhóm/model | Seed chính | Hồ sơ UI ngoài seed | Tổng lô nghiệp vụ mới | Toàn DB dev, gồm baseline/inactive |
| --- | ---: | ---: | ---: | ---: |
| res.partner | 12 | 0 | 12 | 44 (có4partner actor) |
| crm.lead | 12 | 2 | 14 | 24 |
| project.project | 8 | 0 | 8 | 15 |
| tp.contract | 10 | 1 | 11 | 14 |
| Phụ lục | 0 | 0 | 0 | Không tạo thêm |
| project.task/WBS | 100 | 2 | 102 | 163 (gồm4welcome task) |
| tp.allocation | 16 | 2 | 18 | 18 |
| tp.production | 24 | 1 | 25 | 25 |
| tp.acceptance | 16 | 1 | 17 | 17 |
| tp.payment.request | 20 | 1 | 21 | 21 |
| tp.periodic.plan | 16 | 2 | 18 | 18 |
| tp.credential | 12 | 1 | 13 | 13 |
| tp.obligation | 8 | 1 | 9 | 9 |
| **Tổng cơ cấu nghiệp vụ mới** | **254** | **14** | **268** | Không cộng số toàn DB khác loại |

14hồ sơ UI gồm một kế hoạch của lượt probe phải chạy lại, đã được giữ và nhận diện; không âm thầm xóa để làm đẹp số. Welcome tasks/actor/grant/revision gốc/lịch sử không tính vào268. Sau này dọn cần review **cả hai registry** riêng; CLI hiện hỗ trợ dataset chính, từ chối mọi apply dev. UI registry dùng để nhận diện, không có lệnh dọn tự động được mở trong task. Không nhận ownership bản ghi baseline hoặc bổ sung của người dùng chỉ vì trùng project.

Dry-run cuối dev xuất `cleanup-last.json`; các draft candidate chưa bị xóa. Dữ liệu được giữ toàn bộ. Report snapshot/restore, preservation, browser và sự cố vận hành tại [nghiệm thu](KD_NATIVE_001_ACCEPTANCE.md).
