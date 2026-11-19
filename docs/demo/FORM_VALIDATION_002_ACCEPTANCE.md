# Lỗi thao tác hiện trong màn thay cho toast

Task FORM-VALIDATION-002, CHG-20261119-027; 19/11/2026.

Người dùng chọn “Làm tiếp ở đây” cho câu hỏi “Chuyển tiếp các màn còn dùng toast sang
khối lỗi trong form?”. Bản này chuyển các màn còn ở mục 7 của
[quy chuẩn validation](../ui/TP_FORM_VALIDATION_STANDARD.md) sang cùng khối lỗi
`InlineErrors` + `saveError` mà FORM-VALIDATION-001 dùng. Kết quả theo từng màn ghi ở
mục 6 và mục 7 của quy chuẩn.

## Hành vi

- **Hồ sơ của tôi**: xóa dòng kinh nghiệm/học vấn, xóa kỹ năng hoặc mở cài đặt bảo mật mà
  máy chủ từ chối thì khối lỗi hiện ngay trong thẻ vừa thao tác (Kinh nghiệm & học vấn,
  Kỹ năng, Tài khoản; với tài khoản chưa gắn hồ sơ nhân viên là thẻ thông báo đó). Tiêu đề
  nói đúng thao tác: “Không có quyền xóa”, “Máy chủ từ chối xóa”, “Không có quyền mở cài
  đặt bảo mật”. Câu cuối: “Danh sách chưa thay đổi.” hoặc “Tài khoản chưa thay đổi.” Mỗi lúc
  chỉ có một khối; đổi tab thì khối mất.
- **Danh sách nhân viên — kéo thả sắp xếp**: máy chủ từ chối thì thứ tự cũ được khôi phục
  như trước, và khối “Máy chủ từ chối sắp xếp” + câu backend nguyên văn + “Đã khôi phục vị
  trí cũ trong danh sách.” hiện phía trên bảng. Lần kéo sau xóa khối.
- **Tổng quan KD**: mở hồ sơ từ số liệu, thêm mới hoặc mở dự án mà bị từ chối/mất kết nối
  thì khối lỗi hiện dưới thanh cảnh báo; vẫn ở Tổng quan, bộ lọc và số liệu giữ nguyên
  (“Bộ lọc và số liệu đang xem được giữ nguyên.”). Thêm “Công việc / WBS” khi chưa chọn Dự
  án: báo trước “Dự án — Bộ lọc: Chọn Dự án trên Tổng quan trước khi thêm công việc / WBS.”,
  **không gọi máy chủ**, mở bộ lọc, bấm vào lỗi thì tới ô Dự án; backend `action_kd_create`
  vẫn kiểm như cũ.
- Thao tác chỉ mở màn (không ghi dữ liệu) mà mất kết nối: “Chưa kết nối được máy chủ nên
  chưa mở hồ sơ được. Kiểm tra kết nối rồi thử lại.”, không còn câu “chưa xác nhận kết
  quả lưu” vốn chỉ đúng cho thao tác ghi.
- Khối lỗi dùng chung nay cao theo nội dung trong mọi kiểu khung chứa. Trước bản sửa,
  trong khung flex dọc cao 100% (Tổng quan KD) khối cao 908px ở 1440 và 704px ở 390, đẩy
  toàn bộ Tổng quan xuống dưới. Form native đo lại không đổi một pixel.

Không đổi quy định bắt buộc, quyền, dữ liệu, workflow hoặc API; không thêm giá trị giả;
backend vẫn kiểm mọi lần ghi. Câu backend giữ nguyên văn; lỗi hệ thống chỉ hiện câu chung.

## File

- `tp_web_home` 20.0.1.11.0: `validation.js` (`saveError` nhận `verb`, `write`, `note`),
  `validation.xml` (câu mở/câu cuối theo thao tác), `validation.scss` (chiều cao khối),
  `inline_errors.js/xml` (prop `intro`, `note`), test `validation.test.js`.
- `tp_hr_workspace` 20.0.1.19.0: `my_profile.js/xml`, `table.js/xml` (renderer danh sách
  nhân viên), test `hr_profile.test.js`, `employee_reorder.test.js`.
- `tp_kd_workspace` 20.0.1.10.0: `overview.js/xml`, test mới `overview_errors.test.js`.
- Docs: quy chuẩn validation (mục 4–8), file này.

## Kiểm thực

Không ghi dữ liệu thật: kịch bản browser chạy với guard chặn mọi RPC ghi (`web_save`,
`create`, `write`, `unlink`, `action_*`, `tp_reorder_*`…) và trả lỗi mô phỏng; không xóa,
sắp xếp, tạo hoặc đổi quyền/khóa tài khoản nào.

| Hạng mục | Kết quả |
|---|---|
| HOOT `@tp_web_home` | 59 test (60 kể cả 1 test KD khớp bộ lọc) / 307 assertion PASS; thêm 3 test: tên thao tác trong tiêu đề, thao tác không ghi, câu cuối riêng |
| HOOT `@tp_hr_workspace` | 50 test (52 kể cả 2 test KD) / 256 assertion PASS; thêm test xóa/bảo mật lỗi trong đúng thẻ, không toast; test sắp xếp bị từ chối: khối lỗi trên bảng, thứ tự cũ trở lại, không toast |
| HOOT `@tp_kd_workspace` | 25 test / 96 assertion PASS; 3 test mới: kiểm trước thêm công việc không gọi máy chủ, AccessError khi thêm mới/mở dự án, mở thành công xóa lỗi |
| HOOT toàn bộ module đã cài | 1438 PASS, 11 FAIL; cả 11 là test core (`@web` tooltip/mobile, `@mail`, `@resource`) đã fail ở CHG-20261119-023, không liên quan |
| Odoo Python test | không chạy lại: bản này không đổi Python, view server hoặc dữ liệu; chỉ asset JS/XML OWL/SCSS và phiên bản manifest |
| Browser — Hồ sơ của tôi 1440/390 (admin chưa gắn hồ sơ nhân viên) | mở cài đặt bảo mật bị từ chối (AccessError mô phỏng): khối `access` “Không có quyền mở cài đặt bảo mật … Tài khoản chưa thay đổi.” trong thẻ, trong tầm nhìn; 0 toast |
| Browser — kéo thả sắp xếp 1440 | UserError mô phỏng: khối `business` “Máy chủ từ chối sắp xếp / Kiểm thử: phòng ban đang khóa sắp xếp. / Đã khôi phục vị trí cũ trong danh sách.” trên bảng; thứ tự 4 nhân viên trước/sau giống hệt; 0 toast |
| Browser — Tổng quan KD 1440/390 | mở hồ sơ từ số liệu bị từ chối: khối `access` “Không có quyền mở hồ sơ”, vẫn ở Tổng quan; mất kết nối: khối `connection` “Chưa kết nối được máy chủ nên chưa mở hồ sơ được…”; mỗi lúc 1 khối; khối cao 104px (1440) / 125px (390), đầu trang và bộ lọc vẫn thấy; 0 toast |
| Browser — form native (nhân viên mới) trước/sau sửa SCSS | khối lỗi cùng vị trí và kích thước 1086×129 (1440), 340×167 (390); nội dung không đổi |
| Chung | không tràn ngang; 0 lỗi console |

Chưa kiểm bằng browser (đã có HOOT): xóa kinh nghiệm/kỹ năng trong Hồ sơ của tôi (tài
khoản admin không có hồ sơ nhân viên), menu thêm mới và kiểm trước thêm công việc trên
Tổng quan KD (admin không có loại thêm mới nào). Không cấp thêm quyền hoặc tạo hồ sơ để
thử.

Kết quả và ảnh: `.local/validation002/screens-*-final.json`, `.local/validation002/shots/`
(`myprofile-security-*`, `employee-reorder-desktop`, `kd-open-refused-*`, `geo-*-before/after`).

## Môi trường

| Môi trường | Trạng thái ở mốc ghi này |
|---|---|
| Local `tp_tanphat_dev` (18069) | Đã upgrade `tp_web_home` 20.0.1.10.0 → 20.0.1.11.0, `tp_hr_workspace` 20.0.1.18.0 → 20.0.1.19.0, `tp_kd_workspace` 20.0.1.9.1 → 20.0.1.10.0; exit 0, 0 ERROR, cảnh báo giống lần trước (86). Snapshot nhân viên/user/nhóm/roster/phiên bản/thiết bị/ledger/công/khóa/tài khoản/công ty/resource/base_url không đổi. `tp_hr_attendance` local giữ nguồn đang chạy (20.0.3.3.0): ENTI-LIVE-001 (20.0.3.4.x) là tác vụ khác, chưa áp local, bản này không áp thay |
| Backup local | `.local/validation002/main-backup-20261119T193650`: dump + `pg_restore -l`, filestore 186 file DB tham chiếu (0 thiếu), config riêng, source cũ 3 module, SHA256 |
| Test `tp_tanphat_test` (18079) | không dùng |
| PC server | Đã áp `70cf30a8` (CHG-20261119-028): Home 20.0.1.10.0 → 20.0.1.11.0, HR 20.0.1.18.0 → 20.0.1.19.0, KD 20.0.1.9.1 → 20.0.1.10.0, exit 0 / 0 ERROR; trước deploy nguồn 18 file khớp `dea9de54`. Xem receipt dưới |

## Giới hạn

- Chưa physical device/iOS/Safari; kiểm desktop/mobile bằng viewport.
- Toast danger của menu người dùng (đăng xuất, mở thông tin cá nhân) giữ có chủ đích;
  `tp_reporting` person chưa chuyển vì đang có thay đổi chưa commit của tác vụ khác. Xem
  mục 7 quy chuẩn.
- Hộp thoại lỗi RPC native của Odoo vẫn có thể xuất hiện cùng khối lỗi trong màn.
- Ảnh chụp và log chỉ lưu trong `.local/validation002/` (bị ignore) để không đưa dữ liệu
  nhân viên vào Git. Technical verification khác nghiệm thu nghiệp vụ.

## Receipt PC server — CHG-20261119-028

- Commit app `70cf30a872f7354be4c2d305491a58224aa98223`; gói `form-validation027`, 23 file, checksum từng file khớp sau giải nén.
- Trước deploy: nguồn 18 file scope = `dea9de54`; mọi module `tp_*` đã cài có phiên bản nguồn = DB; không có module chờ cài/nâng cấp, không có container upgrade khác.
- Backup `C:\TANPHAT-backups\form-validation002\form-validation027-20261119T214803`: `tp_tanphat_dev.dump` + `restore-list.txt` (15928 mục), `filestore.tar.gz` (623 mục), source/config, SHA256SUMS.
- Upgrade `-u tp_web_home,tp_hr_workspace,tp_kd_workspace` exit 0, 0 ERROR; snapshot trước/sau giống hệt ngoài phiên bản 3 module (ngày công 724 = 724; cron ENTI chạy mỗi phút nên mục này chỉ được phép tăng). `tp_hr_attendance` 20.0.3.4.1 không đổi; 10 phút sau restart không có ERROR.
- Public `https://eight-championships-launches-plaintiff.trycloudflare.com`: `/web/health` 200, `/dang-nhap` 200; bundle JS `e1aad712…`, CSS `3e5f447c…` bằng SHA256 bản server, có `tp_web_home.InlineErrors`, câu “Chưa kết nối được máy chủ nên chưa”, `tpReorderError`, `tp_kd_filter_project`, và `.tp_validation_summary{flex: 0 0 auto; width: 100%; …}`.
- Server còn các file chưa commit của phiên khác và `tp_branding` chưa track (có từ trước); bản này không thay đổi chúng.
- Người dùng bấm Ctrl+F5 để tải bundle mới.
