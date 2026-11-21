# TANPHAT ONE — Hướng dẫn & Nghiệm thu Module “Đề nghị & Phê duyệt” (`tp_request` 20.0.1.0.0)

> **Mã thay đổi:** `CHG-20261121-001` (`TP-REQUEST-001`)
>
> **Module:** `custom_addons/tp_request` (`20.0.1.0.0`) + `custom_addons/tp_branding` (`20.0.2.2.0`)
>
> **Ngày hoàn thành:** 21/11/2026

---

## 1. Bảng khảo sát tích hợp (Chức năng đã có → Tái sử dụng → Bổ sung → Rủi ro)

| Nghiệp vụ / Thành phần | Đã có trong hệ thống | Phần tái sử dụng trực tiếp | Phần bổ sung ở `tp_request` | Rủi ro tích hợp & Cách kiểm soát |
| :--- | :--- | :--- | :--- | :--- |
| **Nhân sự, phòng ban, tài khoản** | `hr.employee`, `hr.department`, `res.users`, `tp_organization` | Đọc trực tiếp hồ sơ nhân viên, phòng ban, quản lý trực tiếp (`parent_id`), trưởng phòng (`manager_id`), công ty hiện hành. | Chụp snapshot tên/mã/phòng ban tại thời điểm gửi nhưng vẫn giữ FK tới bản ghi nguồn. | Không suy người duyệt từ chức danh text; thiếu trưởng phòng/quản lý thì cho lưu nháp và chặn gửi rõ ràng. |
| **Admin gốc & Admin ủy quyền (DEC-053/054/062)** | `tp_admin_delegation` (`group_original_admin`, `group_full_admin`, `is_live_admin_user`) | Kiểm quyền admin trực tiếp qua nhóm và trạng thái hiệu lực tại thời điểm thao tác (lock row). | Phân tách `group_request_manager` (quản trị cấu hình loại đề nghị), không chạm `base.group_system` hay chính sách tài khoản admin. | Admin ủy quyền bị thu hồi mất quyền duyệt & quản trị ngay lập tức; giữ nguyên DEC-054/062 (đã hồi quy 37/37 test). |
| **Điều chỉnh công** | `tp_hr_attendance` (`tp.hr.attendance.correction`) | Toàn bộ workflow `action_submit`, `action_approve`, `action_return`, `action_cancel`, khóa kỳ, chống tự duyệt, cập nhật `tp.hr.attendance.day`. | Cầu nối 1-1 (`attendance_bridge.py`, trường `tp_request_id`) đồng bộ một chiều từ nguồn sự thật `tp.hr.attendance.correction` sang `tp.request` (ngữ cảnh `BRIDGE_INTERNAL`). | Tránh lặp write hoặc tạo phiếu trùng: mọi action từ `tp.request` ủy quyền thẳng về `tp.hr.attendance.correction`; không tạo bản ghi song song. |
| **Kho thiết bị** | `tp_equipment` (`maintenance.equipment`, `tp.equipment.move`, `maintenance.request`, `tp.equipment.proposal`) | `free_domain`, `_tp_assign_problem`, `lock_records` (`FOR UPDATE NOWAIT`), `tp.equipment.move` (`assign`/`return`/`loan_return`) + `action_done`, `maintenance.request`, `tp.equipment.proposal`. | Nhân viên chỉ xem danh sách máy đang giao cho chính mình (`tp_my_equipment_options`) không cần quyền kho; người thực hiện cấp phát/đổi máy nguyên tử 1 transaction, bắt buộc xác nhận tình trạng máy cũ khi thu hồi; mua sắm chỉ tạo `tp.equipment.proposal` (không tự tạo tài sản tồn kho). | Chống cấp trùng 1 máy cho 2 đề nghị đã duyệt bằng row-lock + re-check `_tp_assign_problem()` ngay tại bước xác nhận hoàn thành; dữ liệu `tp.equipment.proposal` cũ giữ nguyên. |
| **Hợp đồng & Phê duyệt ngoài (Base)** | `tp_contract` (`tp.approval.reference`) | Giữ nguyên quy trình phê duyệt tài chính/hợp đồng bên ngoài và liên kết bằng chứng hiện có. | Không thay thế, không lưu thông tin đăng nhập Base, không tự gửi/duyệt hồ sơ lên Base. | Không xung đột hợp đồng/tài chính; `tp.request` chỉ chọn dự án trong phạm vi quyền đọc thực tế. |
| **Thông báo, tệp đính kèm, UI chuẩn** | `mail.thread`, `bus.bus`, `ir.attachment`, `tp_web_home` (`InlineErrors`, `saveError`, Home catalog), `tp_branding` | Đăng ký thẻ Trang chủ qua `home_catalog`, dùng `InlineErrors` + `saveError`, đăng ký 7 URL chuẩn `/app/de-nghi/...`. | Tách biệt **Trao đổi** (`mail.message` comment) và **Lịch sử hệ thống** (`tp.request.history` bất biến); guard `ir.attachment` khóa `public=False`/`access_token=False` và kiểm quyền tải `/tp_request/attachment/<id>`. | Không rò rỉ tệp đính kèm ra người ngoài hoặc link công khai; giao diện F5/Back/Forward giữ bộ lọc và vị trí danh sách. |

> **Lưu ý kiểm tra giao diện Base Request:** Phiên thử nghiệm đọc-chỉ trên `https://request.base.vn` gặp cổng reCAPTCHA của `account.base.vn`; tuân thủ nguyên tắc an toàn, phiên không vượt CAPTCHA mà thiết kế trực tiếp từ tri thức nghiệp vụ đã xác minh trong [TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md](../architecture/TP_BASE_REQUEST_BUSINESS_KNOWLEDGE.md) và đặc tả nghiệp vụ TANPHAT ONE.

---

## 2. Hướng dẫn sử dụng theo vai trò

### 2.1. Nhân viên gửi đề nghị
1. Từ **Trang chủ** → mở ứng dụng **Đề nghị & Phê duyệt** (`/app/de-nghi/tong-quan`).
2. Bấm **Tạo đề nghị** → chọn loại đề nghị bằng thẻ trực quan (icon, màu, mô tả).
3. Hệ thống tự điền **Người gửi**, **Mã nhân viên**, **Phòng ban** từ hồ sơ HR. Điền thông tin chuyên biệt (ngày công/giờ vào-ra, thiết bị đang dùng, loại thiết bị cần cấp/mua, nhóm hỗ trợ IT...), đính kèm minh chứng và xem trước **Tuyến phê duyệt tuần tự**.
4. Bấm **Lưu nháp** (nếu cần bổ sung sau hoặc tuyến duyệt chưa cấu hình xong) hoặc **Gửi phê duyệt**.
5. Theo dõi tiến trình trong **Đề nghị của tôi** (`/app/de-nghi/cua-toi`). Khi bị **Trả lại bổ sung**, mở chi tiết → bấm **Chỉnh sửa hồ sơ** → cập nhật → **Lưu & gửi phê duyệt** (tăng phiên bản `v2`, giữ đủ lịch sử cũ). Nếu bị từ chối hoặc đã rút, có thể bấm **Tạo bản đề nghị mới từ hồ sơ này**.

### 2.2. Người phê duyệt
1. Mở **Cần tôi duyệt** (`/app/de-nghi/can-duyet`) hoặc nhấp trực tiếp từ thông báo nội bộ (`/app/de-nghi/ho-so/<id>`).
2. Kiểm tra nội dung, tệp đính kèm, tuyến duyệt tuần tự và hạn xử lý (cảnh báo quá hạn nếu vượt SLA).
3. Nhập nhận xét (bắt buộc khi **Trả lại bổ sung** hoặc **Từ chối**) và chọn thao tác:
   - **Chấp thuận**: chuyển sang bước duyệt tiếp theo hoặc hoàn tất duyệt và đẩy sang hàng đợi **Cần thực hiện**.
   - **Trả lại bổ sung**: bắt buộc ghi lý do, trả hồ sơ về người gửi chỉnh sửa.
   - **Từ chối**: bắt buộc ghi lý do, kết thúc đề nghị (riêng Điều chỉnh công chỉ dùng **Trả lại bổ sung** theo quy tắc backend).
4. Người duyệt **không thể tự duyệt** đề nghị của chính mình và **không thể duyệt vượt cấp** khi bước trước chưa hoàn tất.

### 2.3. Người thực hiện sau duyệt
1. Mở **Cần thực hiện** (`/app/de-nghi/can-thuc-hien`) để xem các đề nghị đã phê duyệt hoàn tất được phân công.
2. Bấm **Nhận việc & bắt đầu thực hiện** → cập nhật tiến độ xử lý (có thể tải thêm biên bản/hình ảnh minh chứng).
3. Với nghiệp vụ thiết bị:
   - **Cấp thiết bị**: chọn thiết bị thực tế đủ điều kiện trong kho → **Xác nhận hoàn thành** (hệ thống tự tạo & hoàn tất phiếu `tp.equipment.move` loại cấp phát).
   - **Đổi thiết bị**: chọn thiết bị mới trong kho + **bắt buộc xác nhận tình trạng thực tế máy cũ** (`Tốt / Hạn chế / Hỏng`) → **Xác nhận hoàn thành** (thu hồi máy cũ và bàn giao máy mới trong 1 giao dịch nguyên tử).
   - **Sửa chữa / báo hỏng**: bấm **Tạo phiếu sửa chữa trong Kho thiết bị** (`maintenance.request`), sau đó xác nhận hoàn thành khi xử lý xong.
   - **Mua bổ sung thiết bị**: bấm **Lập đề xuất mua sắm trong Kho thiết bị** (`tp.equipment.proposal`) — phê duyệt mua **không** tự tạo tài sản tồn kho trước khi mua và nhập kho thực tế.
4. Nếu không thể triển khai, bấm **Không thể thực hiện** và bắt buộc nhập lý do.

### 2.4. Quản trị (`Quản trị` — `/app/de-nghi/quan-tri`)
- Tab **Danh mục loại đề nghị & tuyến duyệt**: thêm/sửa loại đề nghị, cấu hình các bước duyệt tuần tự (`specific_users`, `direct_manager`, `department_manager`, `project_lead`, `admin_group`), SLA theo giờ làm việc, người thực hiện sau duyệt, kích hoạt/ngừng dùng (không xóa cứng loại đã có hồ sơ). Thay đổi chỉ áp cho hồ sơ mới; hồ sơ đã gửi giữ nguyên tuyến cũ.
- Trên chi tiết hồ sơ đang chờ duyệt (trừ Điều chỉnh công), quản trị có nút **Chuyển giao** người duyệt bước hiện tại (bắt buộc nhập lý do, ghi lịch sử bất biến, chặn chuyển cho người gửi).
- Tab **Toàn bộ hồ sơ công ty**: tra cứu, lọc đa tiêu chí và xuất Excel đúng phạm vi công ty.

---

## 3. Ma trận phân quyền

| Năng lực / Phạm vi | Nhân viên thường | Người duyệt (trong tuyến) | Người thực hiện (được phân công) | Người theo dõi | Quản trị Request / Admin ủy quyền | Admin gốc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Lập / sửa nháp / gửi đề nghị của chính mình | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem hồ sơ của chính mình | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xem hồ sơ riêng tư của nhân viên khác | ❌ | Chỉ hồ sơ trong tuyến duyệt | Chỉ hồ sơ đã duyệt được giao | Chỉ hồ sơ được gắn theo dõi | Toàn công ty (trừ nháp người khác) | Toàn công ty (trừ nháp người khác) |
| Chấp thuận / Trả lại / Từ chối | ❌ | ✅ (khi đúng lượt, không tự duyệt) | ❌ | ❌ | Chỉ khi thuộc tuyến duyệt hợp lệ | Chỉ khi thuộc tuyến duyệt hợp lệ |
| Nhận việc / Hoàn thành / Hủy thực hiện | ❌ | ❌ | ✅ (khi `approval_state=approved`) | ❌ | Chỉ khi thuộc nhóm thực hiện hợp lệ | Chỉ khi thuộc nhóm thực hiện hợp lệ |
| Tạo phiếu bàn giao / sửa chữa / đề xuất kho | ❌ | ❌ | Chỉ khi có quyền Kho thiết bị | ❌ | ✅ (nếu có quyền admin thiết bị) | ✅ |
| Quản trị danh mục loại đề nghị & chuyển giao duyệt | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Cấp / thu hồi quyền Admin (DEC-054/062) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (duy nhất) |
| Tải tệp đính kèm `/tp_request/attachment/<id>` | Chỉ hồ sơ có quyền đọc | Chỉ hồ sơ có quyền đọc | Chỉ hồ sơ có quyền đọc | Chỉ hồ sơ có quyền đọc | Hồ sơ trong phạm vi công ty | Hồ sơ trong phạm vi công ty |
| Sửa / Xóa lịch sử hệ thống (`tp.request.history`) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 4. Danh mục 7 loại đề nghị cấu hình sẵn & khả năng mở rộng

| Mã loại | Tên loại đề nghị | Nhóm xử lý | Tuyến duyệt mặc định | Thực hiện sau duyệt | Sẵn sàng trên dữ liệu hiện tại |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ATT_CORRECTION` | Điều chỉnh công | `attendance_correction` | Quy tắc Admin gốc / ủy quyền (`tp_hr_attendance`, DEC-061) | Không (tự cập nhật bảng công khi duyệt) | ✅ Sẵn sàng ngay |
| `EQUIP_ASSIGN` | Cấp phát thiết bị | `equipment_assign` | B1: Nhóm Quản trị (`admin_group`) | Nhóm Quản trị thiết bị (`admin_group`) | ✅ Sẵn sàng ngay |
| `EQUIP_SWAP` | Đổi thiết bị | `equipment_swap` | B1: Nhóm Quản trị (`admin_group`) | Nhóm Quản trị thiết bị (`admin_group`) | ✅ Sẵn sàng ngay |
| `EQUIP_REPAIR` | Sửa chữa / báo hỏng thiết bị | `equipment_repair` | B1: Nhóm Quản trị (`admin_group`) | Nhóm Quản trị thiết bị (`admin_group`) | ✅ Sẵn sàng ngay |
| `EQUIP_PURCHASE` | Đề xuất mua bổ sung thiết bị | `equipment_purchase` | B1: Trưởng phòng (`department_manager`) → B2: Nhóm Quản trị (`admin_group`) | Nhóm Quản trị thiết bị (`admin_group`) | ⚠️ Phụ thuộc cấu hình Trưởng phòng (`hr.department.manager_id`) |
| `IT_SUPPORT` | Hỗ trợ IT | `it_support` | B1: Nhóm Quản trị (`admin_group`) | Nhóm Quản trị (`admin_group`) | ✅ Sẵn sàng ngay |
| `INTERNAL_GENERAL` | Đề nghị nội bộ chung | `general` | B1: Người duyệt cụ thể *(cố ý để trống)* | Người thực hiện cụ thể *(tùy chọn)* | ⚠️ Chờ Admin chọn người duyệt tại `/app/de-nghi/quan-tri` |

**Mở rộng giai đoạn sau (không tạo tab rỗng):** Kiến trúc `tp.request.type` + `tp.request.type.step` đã hỗ trợ thêm mới trực tiếp từ màn Quản trị cho nghỉ phép, công tác, văn phòng phẩm, tạm ứng/thanh toán mà không cần sửa cấu trúc khung.

---

## 5. Các cấu hình dữ liệu còn thiếu để vận hành thật (từ khảo sát PC Server `192.168.1.73`)

1. **Loại `INTERNAL_GENERAL` (Đề nghị nội bộ chung):** Chưa gắn danh sách người duyệt mặc định (để đảm bảo nguyên tắc không tự gán người thật bất kỳ). Quản trị vào `/app/de-nghi/quan-tri` → bấm **Cấu hình ngay** để chọn người duyệt & người thực hiện.
2. **Trưởng phòng ban (`hr.department.manager_id`):** Trên dữ liệu hiện tại mới có **1/13** phòng ban đang gắn Trưởng phòng. Các loại dùng quy tắc `department_manager` (như `EQUIP_PURCHASE`) sẽ cho lưu nháp và chặn gửi với thông báo rõ phòng ban chưa có Trưởng phòng cho tới khi HR cập nhật đủ.
3. **Quản lý trực tiếp (`hr.employee.parent_id`):** Hiện mới có **3/39** nhân viên có quản lý trực tiếp; cần bổ sung nếu sau này cấu hình bước duyệt theo `direct_manager`.
4. **Liên kết tài khoản nhân viên (`hr.employee.user_id`):** Hiện có **12/39** nhân viên đã gắn tài khoản đăng nhập. Nhân viên chưa có tài khoản chưa thể tự lập đề nghị; thiết bị chỉ lọc theo máy đang bàn giao cho đúng hồ sơ nhân viên liên kết.
5. **Chuyên trách IT / Quản trị Request riêng (tùy chọn):** Hiện nhóm `IT_SUPPORT` và thiết bị mặc định trỏ tới nhóm Admin hiệu lực (`admin_group`) để chạy được ngay; công ty có thể gán nhân sự IT/HCNS cụ thể trên `/app/de-nghi/quan-tri` bất cứ lúc nào.

---

## 6. Kết quả kiểm thử tự động & Kiểm chứng kỹ thuật

- **Kiểm cú pháp tĩnh:**
  - Python `py_compile`: 12/12 tệp PASS.
  - XML `ElementTree`: 13/13 tệp PASS.
  - JavaScript `node vm.Script`: 10/10 tệp PASS.
- **Kiểm thử Odoo tự động trên `tp_tanphat_test`** (`--test-tags /tp_request,/tp_branding` và hồi quy `/tp_admin_delegation`):
  - `tp_request`: **12/12 tests PASS** (phủ đủ 18 tình huống bắt buộc: lập/nháp/gửi, báo đúng trường thiếu, chặn gửi khi thiếu người duyệt, bảo mật quyền xem/tải tệp HTTP 403/200, chặn vượt bước 2, thu hồi admin ủy quyền mất quyền ngay, chống tự duyệt kể cả admin, trả lại bắt buộc lý do → sửa → gửi lại tăng version, chống duyệt lặp / stale version / đồng thời `any_one`, cầu nối 1-1 Điều chỉnh công cập nhật bảng công thật, cấp thiết bị chỉ máy kho hợp lệ & chặn cấp trùng 1 máy cho 2 hồ sơ, đổi máy nguyên tử bắt buộc tình trạng máy cũ, mua sắm lập `tp.equipment.proposal` không tạo tồn kho giả, dashboard/list/filter/XLSX khớp 100%, chuyển giao duyệt có audit, khóa tuyến cũ khi đổi cấu hình, lịch sử bất biến & comment không đổi state, route `/app/de-nghi/...` & `/app/de-nghi/ho-so/<id>` trả 200).
  - `tp_branding`: **33/33 tests PASS** (gồm parity Python↔JS của 7 route `/app/de-nghi/...` và HTTP deep-link/redirect).
  - `tp_admin_delegation`: **37/37 tests PASS** (0 hồi quy DEC-053/054/061/062).
  - Asset bundles Odoo 20: JS Assets biên dịch sạch (3.27s), CSS/SCSS Assets biên dịch sạch (1.55s).

---

## 7. Kết quả triển khai PC Server & Kiểm tra Public (21/11/2026)

- **Máy chủ đích:** `192.168.1.73` (`tp-odoo`, DB `tp_tanphat_dev`, URL public `https://tpone.tadic.vn`).
- **Commit phát hành:** `83e0d217` + bản vá libsass `request.scss` (`max-width` thay `min(px, 100%)`).
- **Sao lưu trước triển khai:** `C:\TANPHAT-backups\tp-request001\req001-20261121T113004` (`tp_tanphat_dev.dump` đã kiểm chứng `pg_restore -l`, `filestore.tar.gz`, `source.tar.gz`, `docker.odoo.conf`, `before.txt`, `after.txt`, `upgrade.log`).
- **Kết quả cài đặt/nâng cấp:** 42/42 tệp khớp SHA256, `UPGRADE_EXIT=0`, `UPGRADE_ERRORS=0`, `tp_request=20.0.1.0.0:installed`, `tp_branding=20.0.2.2.0:installed`, `TP_REQUEST_TYPES=7`, `TP_REQUEST_RECORDS=0`, `DRIFT_COUNT=0` (bảo toàn 100% nhân viên, tài khoản, nhóm quyền, thiết bị, đề xuất thiết bị cũ và chấm công).
- **Biên dịch tài nguyên trên container thật:** `web.assets_backend.min.js` (8.795.200 bytes, chứa đầy đủ thành phần `tp_request`), `web.assets_backend.min.css` (1.696.919 bytes, `HAS_ERROR=False`).
- **Kiểm tra truy cập trực tiếp:**
  - `https://tpone.tadic.vn/web/health` và `http://192.168.1.73:8069/web/health`: HTTP `200 {"status": "pass"}`.
  - 7/7 đường dẫn `/app/de-nghi/{tong-quan,cua-toi,can-duyet,can-thuc-hien,theo-doi,quan-tri,ho-so/1}`: HTTP `303 -> https://tpone.tadic.vn/dang-nhap?redirect=...`.
  - `/tp_request/attachment/1` (chưa đăng nhập): HTTP `303` (không lộ tệp đính kèm).
