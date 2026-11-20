# HR-EMPLOYEE-CODE-003 — Áp và hoàn nguyên mã nhân viên TP + 3 chữ số

Phạm vi: `tp_organization` 20.0.2.3.0 và `tp_hr_attendance` 20.0.3.5.5. Không
sửa core Odoo. Không đổi constraint unique, guard sửa mã hay quyền. Không tạo,
xóa hay tạo lại nhân viên. Không đổi tài khoản, login hay mật khẩu.

## Quy tắc

- Mã mới: `TP` + đúng 3 chữ số, dải TP001–TP999.
- Mã cũ TP10001–TP10999 → số − 10000. Ví dụ TP10001 → TP001, TP10060 → TP060,
  TP10125 → TP125.
- Mã đã đúng dạng giữ nguyên.
- Mã ngoài cả hai dạng (TP11000, TP20000, TP1, TP0001…), thiếu mã, hoặc trùng sau
  khi chuyển là **xung đột**. Không cắt số cuối, không tự cấp số khác.
- Cũng là xung đột:
  - số thuộc hồ sơ đã xóa hoặc đã đổi mã (audit, ở cả hai dạng);
  - mã nguồn không ra đúng mã mới.

  Có xung đột thì migration dừng và không ghi gì.
- Cấp mã mới:
  - Nối tiếp số cao nhất đã cấp (hồ sơ và audit, cả hai dạng). Không dùng lại mã
    đã lưu trữ hoặc xóa.
  - Hết dải thì báo lỗi và dừng, không sinh TP1000.
  - Nhập danh sách dùng mã nguồn đã xác minh; mã nguồn > 999 là xung đột.
- Bản sao mã trong `tp.hr.attendance.day` và `tp.hr.attendance.correction` được
  làm mới theo `employee_id` + `company_id`. Kỳ đã khóa cũng làm mới; giờ, công
  và trạng thái giữ nguyên.
- Audit, log và file Excel nguồn giữ nguyên dạng gốc.
- Mã ENTI (`maNV`, `keyNV`) và mapping ENTI → nhân viên giữ nguyên. Mã ENTI không
  bao giờ được so với mã TP nội bộ để chọn người.

## Áp lên PC server

1. **Đóng gói.** Chạy `git archive <SHA>` cho hai addon, nội dung LF. Manifest
   private ghi:
   - `commit`, `parent`, `version`;
   - hash baseline (nội dung của parent, `MISSING` cho file mới) và hash release;
   - `removed`.

   Hash chuẩn hóa CRLF→LF như [script](deploy-hr-employee-code003.ps1).
2. **Chép lên PC.** Đặt `<label>-release.tar.gz` và `<label>-manifest.json` vào
   `C:\Projects\TANPHAT-ONE\.local\hr-employee-code003\` trên PC. Script phải
   đúng commit. Chạy `powershell -File ops\runbooks\deploy-hr-employee-code003.ps1
   -Label code003`.
3. **Script từ chối trước khi đổi bất cứ gì** nếu:
   - nguồn lệch baseline;
   - một module đã cài có version trên đĩa khác DB (vì `-u` lan sang các module
     phụ thuộc).
4. **Script thực hiện theo thứ tự:**
   - dừng `tp-odoo`;
   - snapshot `before`;
   - backup dump + restore-list, filestore, source hai addon, config vào
     `C:\TANPHAT-backups\hr-employee-code003\<label>-<time>\`;
   - giải nén, kiểm checksum, đóng dấu thời gian;
   - chạy `-u tp_organization,tp_hr_attendance` trong container tạm;
   - snapshot `after` trước khi Odoo chạy lại;
   - luôn khởi động lại `tp-odoo`.
5. **Snapshot gồm:**
   - Hồ sơ: số lượng/ID, tên/nguồn/active/thứ tự, user/quản lý/phòng/chức danh,
     version.
   - Tài khoản: users (login + hash mật khẩu, chỉ dạng md5 tổng), nhóm quyền.
   - Chấm công: ngày công (giờ/công/trạng thái), phiên, đề nghị, kỳ, ENTI
     mapping/ngày, mã nguồn máy.
   - Khác: cron, base URL, hàng đợi mail/thông báo, mọi khóa ngoại tới
     `hr_employee`.

   Chỉ được đổi các key: phiên bản module, mã, dạng mã, số dòng audit, sequence,
   bản sao mã chấm công, ghi chú chatter. Lịch sử audit cũ (mọi dòng có trước khi
   áp) phải giữ nguyên; upgrade chỉ được thêm dòng mới. Key khác lệch, còn mã
   ngoài dải hoặc bản sao chưa làm mới thì script báo lỗi để kiểm.
6. **Bằng chứng riêng** (chỉ trên PC, không đưa lên Git): `mapping-applied.txt`
   (ID hồ sơ, mã cũ → mã mới) lấy từ log migration, nằm cùng backup.
7. **Nghiệm thu trên https://tpone.tadic.vn:**
   - danh sách/hồ sơ/Hồ sơ của tôi, dashboard, Bảng công/Công của tôi, gần đây;
   - người dùng thiết bị, KD, báo cáo, chọn nhân viên, lọc/tìm;
   - Excel mới hiện mã mới;
   - ít nhất một chu kỳ ENTI gắn đúng người, không trùng, không quay lại mã cũ.

## Hoàn nguyên

Chỉ dùng khi nghiệm thu thất bại:

1. Dừng `tp-odoo`.
2. `pg_restore --clean --if-exists` dump trong thư mục backup vào
   `tp_tanphat_dev`.
3. Giải nén `source.tar.gz` đè hai addon. Nếu cần, khôi phục filestore từ
   `filestore.tar.gz`.
4. Khởi động `tp-odoo` và so snapshot với `before`.

Không hoàn nguyên bằng tìm-thay chuỗi trong DB.
