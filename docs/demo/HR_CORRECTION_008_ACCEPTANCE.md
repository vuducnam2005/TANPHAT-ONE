# HR-CORRECTION-008 — Xóa hồ sơ nhập nhầm, sửa mã nhân viên, Việt hóa và thu gọn giao diện

12/11/2026 Asia/Saigon, CHG-20261112-013. Yêu cầu trực tiếp; đã kiểm trên
`tp_tanphat_test:18079`, diễn tập restore bản sao main, rồi áp lên
`tp_tanphat_dev:18069`. Baseline HR-COMPACT-007 (CHG-20261112-010) và
IDENTITY-ORG-001 (011/012) được giữ. Không sửa `odoo/`/`addons/`, không frontend
riêng, không DB thứ ba, không restore test sang main. Không stage/commit/push.

Phiên bản: `tp_organization` 20.0.2.1.0, `tp_hr_workspace` 20.0.1.8.0;
`tp_i18n_vi` 20.0.1.0.0 và `tp_web_home` 20.0.1.5.0 nạp lại catalog/asset.
Nguồn: 26 file sửa và 10 file mới (danh sách trong runbook).

## 1. Xóa hồ sơ nhập nhầm và lưu trữ

- Danh sách nhân viên → chọn hồ sơ → **Tác vụ → Xóa hồ sơ nhập nhầm** (chỉ admin
  hệ thống cùng công ty). Backend kiểm từng hồ sơ rồi hiện họ tên, mã, cảnh báo
  xóa vĩnh viễn; bắt buộc nhập lý do; nút **Xác nhận xóa**. Audit
  `tp.hr.employee.audit` lưu tên/mã/lý do/người làm/thời điểm, không có FK tới
  hồ sơ nên vẫn còn sau khi xóa. Menu **Nhật ký xóa hồ sơ và sửa mã** chỉ đọc.
- Chỉ xóa được hồ sơ nhập tay chưa dùng: không thuộc roster/lô nhập, không có tài
  khoản, vai trò, phân công, quyền dự án, tài liệu, trao đổi do người dùng viết,
  hoạt động, lịch sử phiên bản thật hoặc tham chiếu từ bảng khác. Version đầu và
  resource do Odoo tự tạo không chặn và bị xóa theo cơ chế native; partner liên
  hệ công việc được giữ. Không xóa user, partner, tài liệu hay nghiệp vụ.
- Không đạt: hộp thoại ghi “Không xóa được”, liệt kê lý do tiếng Việt từng hồ sơ
  và đưa nút **Lưu trữ nhân viên**. Lưu trữ không khóa tài khoản; khóa/thu hồi vẫn
  ở Tài khoản & phân quyền như trước.
- Lô nhiều hồ sơ là tất cả hoặc không: một hồ sơ bị chặn thì không xóa hồ sơ nào;
  lỗi giữa chừng rollback toàn bộ.
- Nút Xóa native của nhân viên bị bỏ khỏi menu Tác vụ; `unlink` qua RPC/native
  vẫn bị chặn (sentinel Python nội bộ, không nhận context từ client). Action
  native “Delete employee” của `hr_timesheet` được gỡ binding. Không cấp thêm
  quyền xóa rộng.

Kết quả: test dùng hồ sơ giả — A (`TP10071`, `TP10073`) xóa đúng, có audit;
B (`TP10072`, `TP10074`) bị chặn và được lưu trữ. Dữ liệu giả đã bị loại khỏi
test bằng restore bản sao main. Main không xóa hay lưu trữ hồ sơ nào. Kiểm tra
chỉ đọc trên main: 40 hồ sơ, 39 bị chặn vì từ danh sách nhân sự (7 trong đó còn
tài khoản), chỉ hồ sơ id 67 `TP10070` (nhập tay, chưa dùng) đủ điều kiện nếu admin
muốn xóa.

## 2. Mã nhân viên

- Nguyên nhân: `tp_organization/data/employee_sequence.xml` đặt
  `number_next=20000` trong `noupdate`, nên hồ sơ nhập tay đầu tiên trên main
  (id 67, 12/11 06:48) nhận `TP20000` thay vì nối tiếp roster TP10001–TP10069.
- Sửa: sequence khởi tạo 10001; cấp mã = mã hợp lệ cao nhất (TP10001–TP19999, so
  theo số, gồm hồ sơ lưu trữ và mã trong audit kể cả hồ sơ đã xóa) + 1. Không dùng
  employee.id, không đánh lại số, không tái dùng mã, chấp nhận khoảng trống. Giữ
  unique constraint; khóa advisory theo công ty để hai giao dịch không cùng mã.
  Mã roster giữ nguyên; đổi mã chỉ qua correction nội bộ có audit.
- Migration `tp_organization` 20.0.2.1.0: kiểm kê mã TP2xxxx; chỉ đổi mã cũ của
  hồ sơ nhập tay chưa dùng, ghi audit và chatter; trường hợp khác chỉ báo cáo,
  không tự gộp. Main/test: đúng một mã — id 67 `TP20000 → TP10070`, không xung đột.
- Mã kế tiếp thực tế: **test TP10071, main TP10071** (sequence đồng bộ 10071).

## 3. Việt hóa

Cơ chế Odoo: overlay `tp_i18n_vi/i18n/vi.po` thêm 111 mục (action server/window
của HR/project, chuỗi JS của web), `tp_organization/i18n/vi.po` cho nhãn mã/nguồn
và ràng buộc, template `tp_web_home` cho bộ đếm chọn. Nạp bằng
`-u ... --i18n-overwrite`; main chỉ đổi các mục overlay (đối chiếu theo cột).

- Đã kiểm: bộ đếm “Đã chọn 1 hồ sơ”/“Đã chọn tất cả N hồ sơ”; hộp xác nhận có
  tiêu đề và nút cụ thể thay “Confirmation”/“Ok” (“Xác nhận áp dụng đối chiếu”,
  “Áp dụng đối chiếu”, “Xác nhận xóa”, “Hủy”); xác nhận xóa nhiều dòng, hộp thoại
  không xóa được, lỗi chung, nhân bản, sửa nhiều dòng; menu Tác vụ HR (Xuất, Nhân
  bản, Lưu trữ, Bỏ lưu trữ, Gửi email, Tạo phiên bản hồ sơ mới; action “Cho nghỉ
  việc” cũng đã dịch); tìm kiếm/bộ lọc/nhóm/khoảng ngày/điều
  kiện; pager; hộp thoại xuất dữ liệu; tải tệp/ảnh; xác minh danh tính, ẩn/hiện
  mật khẩu; tooltip danh sách; placeholder tìm kiếm.
- Màn hình: HR danh sách/chi tiết/tài khoản/vai trò/chức vụ/chuyển phòng, Home,
  KH-KD danh sách/chi tiết/tổng quan, To-do của người dùng thường. Admin và một
  người dùng thường giả trên test không còn từ tiếng Anh phổ biến; placeholder
  `%s`/`%(n)s` giữ nguyên (test catalog kiểm).
- Giữ nguyên: TANPHAT ONE, TP HR, mã TP…, login. “Administrator” trên navbar là
  tên tài khoản (dữ liệu), không dịch; nhãn vai trò dùng “Quản trị hệ thống” /
  “Quản trị viên”.
- Migration `tp_hr_workspace` 20.0.1.8.0 chuyển sang vi_VN các tài khoản cá nhân
  do wizard tạo còn en_US (nhận diện qua chatter “Đã tạo tài khoản cá nhân”):
  main 1 tài khoản `tranphuongdong`.
- Chưa xử lý: hộp xác nhận xóa một bản ghi native ở model khác (ví dụ To-do) dùng
  bản dịch vui của catalog `web` (“Tạm biệt, dữ liệu!”, “bốc hơi”); đã là tiếng
  Việt nhưng chưa trang trọng. Không khẳng định toàn bộ Odoo đã được dịch.

## 4. Thu gọn giao diện (trừ sidebar)

Token dùng chung trong `tp_web_home/static/src/density/density.scss` và các SCSS
HR/KD/Home; không zoom/scale, không đổi root font (16px), không selector toàn cục
có tác dụng phụ; không chồng thêm lên HR-COMPACT-007.

Main, admin, cùng route/dữ liệu, 100%:

| Phần | Trước | Sau |
|---|---|---|
| Navbar | 56px | 48px |
| Control panel chi tiết HR | 81.3px | 71.3px |
| Ô nhập trong form/modal | 46px, 16px | 36.5px, 15px |
| Nhãn form | 16px | 15px |
| Tab chi tiết | 49.5px | 45.5px |
| Header modal | 51.3px | 48.3px |
| Chi tiết HR 1440 / 1280 | 748 / 772px | 684 / 684px (−8.6% / −11.4%) |
| Dòng bảng KH-KD | 49.7px, th 43px | 43.7px, th 39px |
| Dòng bảng HR | 40px | 40px (đã gọn từ trước) |

Mobile 390: nút/ô nhập ≥44px, không tràn ngang, bảng cuộn trong khung. Sidebar:
computed style giống hệt trước/sau ở 28 lần đo; khác biệt duy nhất là mục mới
“Nhật ký xóa hồ sơ và sửa mã” (cùng style mục con) và chiều cao sidebar +8px vì
navbar thấp hơn. Dòng KH-KD 43.7px hơi cao hơn mục tiêu 40px do badge và chữ hai
dòng; không ép nhỏ thêm.

## 5. Bằng chứng kiểm

- Odoo test trên 18079: 84 tests 0 failed 0 error (`tp_organization`,
  `tp_hr_workspace`, `tp_i18n_vi`, `tp_web_home`), gồm 16 case mới: xóa đủ điều
  kiện có audit bền; chặn native/không quyền; chặn hồ sơ đã dùng kèm lý do; lô
  tất cả-hoặc-không và rollback giữa chừng; lưu trữ giữ trạng thái tài khoản; hộp
  thoại chỉ có lối vào được bảo vệ; mã kế tiếp theo mã hợp lệ cao nhất; bỏ qua
  sequence cũ; bỏ qua mã lưu trữ/đã xóa; hết dải/so chuỗi; giao dịch rollback
  không tái dùng mã; roster và nhập tay không đè nhau; đổi mã chỉ qua correction;
  migration chỉ đổi mã nhập tay chưa dùng. 4 dòng log “bad query” là test ràng
  buộc unique cố ý.
- Đồng thời: 2 giao dịch thật cấp `TP10075`/`TP10076`, giao dịch sau chờ 1.66s,
  không trùng (`concurrency.json`).
- Diễn tập: restore backup main vào test 597 bảng/653 blob/430 sequence khớp,
  neutralize, upgrade cho đúng mapping và mã kế tiếp; 191 tests 0 failed 0 error
  (thêm `/tp_project:TestDepartmentRole`, `/tp_kd_workspace`).
- HOOT mỗi cổng: Home 30 tests/173 assertions, HR 21/86, KD 22/85.
- Browser: luồng xóa/chặn/lưu trữ bằng hồ sơ giả (test); người dùng thường và
  admin không còn từ tiếng Anh phổ biến; zoom 200% không tràn; 18 điểm Tab đều có
  viền focus; 0 lỗi console. Layout 8 route × 4 viewport (1440/1280/1024/390)
  trước/sau mỗi cổng. Smoke main chỉ đọc: bộ đếm, menu Tác vụ, hộp thoại chặn
  hồ sơ roster rồi bấm Hủy; chỉ sinh một bản ghi wizard tạm (TransientModel,
  Odoo tự dọn), không audit/xóa/lưu trữ.
- Ruff, XML, `git diff --check`, kiểm khoảng trắng 36 file đạt.
- Preservation main: delta theo bảng/cột bằng đúng diễn tập (3 bảng mới, view/
  menu/action/ACL mới, bản dịch overlay, id 67 đổi mã, sequence, lang 1 tài khoản,
  6 message hệ thống); khác duy nhất `ir_model_fields_selection.sequence` 34/32
  là chỉ số thứ tự metadata.

Ảnh và JSON ở `.local/hr-correction008/` (`shots/before|after-18079|18069-*`,
`shots/main-*.png`, `layout-*.json`, `rowdiff-*.json`, `dumpcmp-*.json`,
`eligibility-*.json`, `codes-*.json`); không đưa vào Git.

## 6. Môi trường và rollback

- 18079: đang chạy trên bản sao main đã neutralize và upgrade; không còn dữ liệu
  giả; mã kế tiếp TP10071.
- 18069: backup cuối `.local/hr001/backup-tp_tanphat_dev-20261112T101939483900Z`
  (597 bảng/653 blob) → upgrade 4 addon → chạy lại → smoke đạt.
- Rollback: [runbook](../../ops/runbooks/HR_CORRECTION_008_DEPLOY_AND_ROLLBACK.md).

## 7. Chuyển phòng ban (câu hỏi kèm)

Đã có: chi tiết nhân viên → Thông tin công việc → **Chuyển phòng ban** (admin,
preview, lý do, bàn giao, audit; IDENTITY-ORG-001). Chuyển trưởng phòng (ví dụ
Thùy Anh, HEAD Kế hoạch Kinh doanh, sang Kế toán) hiện **không bị chặn**: preview
báo và khi áp sẽ tự thu hồi vai trò trưởng phòng cũ. Chỉ chặn khi phòng đích đã
có trưởng phòng mà lại chọn bổ nhiệm, người có nhóm quyền đặc biệt, tài khoản đa
công ty, giữ HEAD ở công ty khác, hoặc phòng/chức vụ/lý do không hợp lệ. Muốn
“không cho chuyển trưởng phòng, phải hạ cấp trước” là thay đổi quy tắc riêng, chưa
làm trong task này.

Giới hạn: tự review (không có kiểm độc lập); mobile giả lập; chưa nghiệm thu
nghiệp vụ/pilot. Next: Ctrl+F5 trên 18069 và review.
