# BẢN NGHIỆM THU: HR-DELETE-ASSET-RETURN-001
**TỰ THU HỒI TÀI SẢN CÔNG TY VỀ KHO KHI XÓA VĨNH VIỄN NHÂN VIÊN**

---

## 1. THÔNG TIN CHUNG
- **Mã thay đổi:** `CHG-20261120-011`
- **Mã nhiệm vụ:** `HR-DELETE-ASSET-RETURN-001`
- **Ngày hoàn tất:** 20/11/2026
- **Trạng thái:** `PC_SERVER_APPLIED`
- **Phân hệ liên quan:** `custom_addons/tp_equipment`, `custom_addons/tp_hr_workspace`
- **Phiên bản mới:**
  - `tp_equipment`: **20.0.1.6.0**
  - `tp_hr_workspace`: **20.0.1.20.0**
- **Môi trường đã áp dụng:**
  - Local Test DB: `tp_tanphat_test` (port 18179)
  - Local Dev DB: `tp_tanphat_dev` (port 18069)
  - PC Server (Production): `server-pc` (`192.168.1.73`), container `tp-odoo`, public domain `https://tpone.tadic.vn`

---

## 2. HIỆN TRẠNG BAN ĐẦU & NGUYÊN NHÂN
Ảnh đính kèm từ người dùng: `codex-clipboard-32f25127-6f4c-4ebb-b340-dc5076f5ce76.png`
Khi admin thực hiện xóa vĩnh viễn nhân viên (ví dụ: hồ sơ Trần Đức Lương, ID 69, mã TP072), hộp thoại báo khung đỏ:
**"Đang chặn — chưa thể xóa"** với 3 dòng:
1. *Dòng phiếu bàn giao thiết bị — Người giữ sau (1)*
2. *Dòng phiếu bàn giao thiết bị — Người giữ trước (1)*
3. *Phiếu bàn giao/thu hồi thiết bị — Nhân viên nhận (1)*

**Nguyên nhân:**
- Các trường `target_employee_id`, `from_employee_id`, `to_employee_id` trên các model `tp.equipment.move` và `tp.equipment.move.line` được khai báo là Many2one với ràng buộc `ondelete="restrict"`.
- Cơ chế quét phụ thuộc của `tp_hr_workspace` nhận diện các trường này là liên kết ngoại bắt buộc và tự động xếp vào nhóm `block` nếu chưa có quy trình xử lý an toàn.
- Admin buộc phải mở từng phiếu gỡ thủ công hoặc không xóa được hồ sơ.

---

## 3. GIẢI PHÁP ĐÃ TRIỂN KHAI

### 3.1. Tự động thu hồi tài sản công ty về kho
- Quét toàn bộ thiết bị mà nhân viên đang thực tế nắm giữ (`tp_employee_id = employee`, `company_id = company`, `tp_lifecycle = active`).
- Tự động tạo và hoàn tất phiếu thu hồi `tp.equipment.move` chuẩn nghiệp vụ (loại `return` đối với thiết bị cấp phát cá nhân, loại `loan_return` đối với thiết bị mượn).
- Đưa quyền giữ về kho (`tp_custody = 'stock'`), gỡ người giữ (`tp_employee_id = False`), cập nhật vị trí kho nhận (`tp_location_id = dest_location`).
- **Bảo toàn dữ liệu kỹ thuật:** Giữ nguyên mã tài sản (`tp_code`), số serial, cấu hình, giá trị và tình trạng kỹ thuật (`tp_technical_state`: máy tốt vẫn tốt, máy hỏng vẫn hỏng).

### 3.2. Bảo toàn snapshot lịch sử bàn giao
- Thêm các trường snapshot trên `tp.equipment.move`: `target_employee_name`, `target_employee_code`, `target_employee_dept`, `target_employee_deleted`.
- Thêm các trường snapshot trên `tp.equipment.move.line`: `from_employee_name`, `from_employee_code`, `from_employee_dept`, `from_employee_deleted`, `to_employee_name`, `to_employee_code`, `to_employee_dept`, `to_employee_deleted`.
- Thêm trường snapshot trên `tp.equipment.proposal.line`, `maintenance.request`, `tp.equipment.inventory.line`, `tp.equipment.import.line`, `tp.equipment.import.alias`.
- Khi xóa nhân viên, backend tự động sao lưu họ tên, mã nhân viên, phòng ban tại thời điểm bàn giao vào các trường snapshot, đánh dấu cờ `deleted = True`, sau đó ngắt liên kết FK (`set to NULL`) có kiểm soát bằng quyền nội bộ `tp_equipment_move_internal=INTERNAL`.
- Phương thức `_tp_holder_text` tự động hiển thị tên snapshot kèm nhãn `(Nhân viên đã xóa)`.

### 3.3. Hủy phiếu bàn giao chờ / nháp
- Các phiếu bàn giao đang ở trạng thái `pending` hoặc `draft` có người nhận là nhân viên bị xóa sẽ tự động bị hủy (`state = 'cancel'`), giải phóng giữ chỗ cho tài sản liên quan.

### 3.4. Xử lý tài sản cá nhân và dịch vụ đặc thù
- **Tài sản cá nhân tự trang bị (`tp_ownership == 'personal'`):** Giải phóng quyền giữ, đánh dấu ngừng quản lý và trả lại chủ sở hữu (`tp_lifecycle = 'retired'`, `tp_retire_reason = 'returned_owner'`), **KHÔNG** đưa vào tồn kho công ty.
- **Thiết bị đang gửi sửa ngoài hoặc dịch vụ/license:** Giải phóng phân công người giữ, không tạo phiếu nhập kho vật lý.

### 3.5. Thiết kế lại Hộp thoại Xem trước xóa (Preview Dialog)
- **Nhóm A — Tài sản công ty sẽ thu hồi về kho:** Bảng chi tiết (Mã tài sản, Tên thiết bị, Serial, Tình trạng, Kho nhận, Hành động). Hỗ trợ dropdown chọn kho nhận nếu công ty có nhiều kho.
- **Nhóm B — Phiếu lịch sử bàn giao sẽ được giữ lại:** Tóm tắt danh mục (Loại phiếu, Số lượng, Snapshot bảo toàn).
- **Nhóm C — Phân công / liên kết khác:** Giữ nguyên theo chuẩn `tp_hr_workspace`.
- **Nhóm D — Sẽ xóa:** Hồ sơ nhân viên và các mục liên kết.
- **Nhóm E — Giữ lại:** Nhật ký audit, lịch sử.
- **Nhóm F — Đang chặn (Blockers):** Chỉ xuất hiện khi còn blocker thực sự (ví dụ: công ty chưa có vị trí kho thiết bị nào). Các quan hệ thiết bị an toàn được đưa sang diện tự xử lý khi xác nhận.
- **Thông báo rõ ràng:** *"Xóa vĩnh viễn hồ sơ và thu hồi các tài sản được liệt kê về kho trên hệ thống."*
- **Nút xác nhận:** *"Xác nhận xóa vĩnh viễn"* (sáng khi không còn blocker).

### 3.6. Giao dịch nguyên tử (Atomic Transaction) & Idempotency
- Toàn bộ các bước hủy phiếu nháp, hoàn tất phiếu thu hồi, snapshot & ngắt FK, xóa nhân viên và ghi audit log diễn ra trong **1 transaction Odoo duy nhất**.
- Nếu có bất kỳ bước nào thất bại, toàn bộ thao tác tự động rollback 100%.
- Kiểm soát idempotency key chống bấm đúp hoặc retry lặp thao tác.

---

## 4. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG

Bộ kiểm thử tự động tại `custom_addons/tp_equipment/tests/test_employee_delete_asset_return.py`:

| STT | Tên Test Case | Mục đích | Kết quả |
|---|---|---|:---:|
| 1 | `test_01_equipment_return_on_permanent_delete` | Thu hồi 2 thiết bị (active, loan), bảo toàn tình trạng tốt/hỏng, xóa hồ sơ | **PASS** |
| 2 | `test_02_history_moves_preserved_when_no_assets_held` | Kịch bản Trần Đức Lương (0 thiết bị đang giữ, 3 phiếu lịch sử): 0 blocker, lưu snapshot, xóa hồ sơ | **PASS** |
| 3 | `test_03_equipment_transferred_to_other_not_returned` | Thiết bị đã giao cho người khác không bị thu hồi nhầm về kho | **PASS** |
| 4 | `test_04_department_shared_equipment_not_returned` | Thiết bị dùng chung phòng ban không bị thu hồi khi xóa nhân viên phòng đó | **PASS** |
| 5 | `test_05_pending_move_cancelled_on_delete` | Phiếu chờ bàn giao tự động hủy và giải phóng giữ chỗ tài sản | **PASS** |
| 6 | `test_06_personal_equipment_returned_to_owner` | Thiết bị cá nhân tự trang bị trả lại chủ nhân, không nhập kho công ty | **PASS** |

**Kết quả chạy test trên `tp_tanphat_test`:**
- Module `tp_equipment`: `6 post-tests in 8.42s, 0 failed, 0 error(s) of 6 tests`.
- Hồi quy `tp_hr_workspace`: `3 post-tests in 5.05s, 0 failed, 0 error(s) of 3 tests`.

---

## 5. KẾT QUẢ TRIỂN KHAI PC SERVER (`192.168.1.73`)

### 5.1. Sao lưu an toàn trước triển khai
- Thư mục sao lưu: `C:\TANPHAT-backups\hr-delete-asset-return001\`
- Tệp database dump: `tp_tanphat_dev.dump` (kích thước: 10.418.949 bytes)
- Tệp mã nguồn cũ: `code-pre.tar.gz` (kích thước: 757.946 bytes)

### 5.2. Nâng cấp runtime
- Đã đồng bộ mã nguồn của 2 addon `tp_equipment` và `tp_hr_workspace` vào `C:\Projects\TANPHAT-ONE`.
- Chạy lệnh upgrade trong container `tp-odoo`:
  `docker exec -w /workspace tp-odoo python3 odoo-bin -c /workspace/docker.odoo.conf -d tp_tanphat_dev -u tp_equipment,tp_hr_workspace --no-http --stop-after-init --max-cron-threads=0`
  -> **Exit code 0, 0 ERROR**.
- Khởi động lại container `tp-odoo`:
  `docker restart tp-odoo`

### 5.3. Kiểm tra Health Check
- LAN Endpoint: `http://192.168.1.73:8069/web/health` -> **HTTP 200 OK**.
- Public Domain: `https://tpone.tadic.vn/web/health` -> **HTTP 200 OK**.

### 5.4. Kiểm chứng thực tế trên hồ sơ trong ảnh (Trần Đức Lương, ID 69, mã TP072)
Đã chạy kiểm tra read-only trực tiếp trong container `tp-odoo` trên cơ sở dữ liệu thật:
```
EMPLOYEE: Trần Đức Lương (Code: TP072)
BLOCKERS COUNT: 0
BLOCKERS: []
EQUIPMENT HISTORY COUNT: 3
  - Phiếu bàn giao / thu hồi – Nhân viên nhận: 1 (snapshot: Bảo toàn snapshot: Trần Đức Lương (Mã: TP072))
  - Dòng phiếu bàn giao – Người giữ trước: 1 (snapshot: Bảo toàn snapshot: Trần Đức Lương (Mã: TP072))
  - Dòng phiếu bàn giao – Người giữ sau: 1 (snapshot: Bảo toàn snapshot: Trần Đức Lương (Mã: TP072))
ASSETS TO RETURN: 0
CAN SUBMIT: True
```

**Đánh giá:**
- Toàn bộ 3 blocker trước đây đã được loại bỏ hoàn toàn.
- Các phiếu lịch sử được bảo toàn snapshot đúng họ tên và mã nhân viên.
- Nút xác nhận xóa vĩnh viễn đã sẵn sàng (`CAN SUBMIT = True`).
- **Tuân thủ cam kết:** Không xóa nhân viên thật số 69; hồ sơ vẫn giữ nguyên 100% trong cơ sở dữ liệu để người dùng tự xem và kiểm chứng trực tiếp trên giao diện!
