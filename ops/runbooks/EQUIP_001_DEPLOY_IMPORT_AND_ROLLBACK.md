# EQUIP-001 — Áp main, nhập nguồn và rollback

**Cập nhật CHG-20261116-007 (EQUIP-SIMPLE-003 — lọc nhanh Máy in):** `tp_equipment` **20.0.1.5.1** trên main `18069` (`tp_tanphat_dev`) sau backup `.local/equip-simple003-printer/backup-pre-printer/` (`tp_tanphat_dev.dump` **9.285.317 bytes**, `filestore/` **883 tệp**, `src/tp_equipment` `20.0.1.5.0` **65 tệp**, `manifest.json`). Update `-u tp_equipment --no-http --stop-after-init --logfile .local/equip-simple003-printer/upgrade.log` exit `0`, `0 ERROR`. Chỉ đổi view search + static filter bar; bảo toàn 18 bảng DB (`TOP_DIFFS: ['modules']`).

**Cập nhật CHG-20261116-003 (EQUIP-SIMPLE-003 / DEC-047):** `tp_equipment` **20.0.1.5.0** trên main `18069` (`tp_tanphat_dev`) sau backup `.local/equip-simple003/backup-pre-simple003/` (`tp_tanphat_dev.dump` **9.259.433 bytes**, `filestore/` **855 tệp**, `src/` gồm `tp_equipment` 20.0.1.4.2 và `tp_web_home`, `manifest.json` có sha256 dump/filestore, tạo 16/11/2026 09:48 Asia/Saigon). Update `-u tp_equipment --stop-after-init` exit 0, logfile không có dòng ERROR (`upgrade-simple003.log`, `upgrade-simple003-2.log`; cảnh báo "Logging error" chỉ do mã hóa console Windows, dùng `--logfile` + `PYTHONIOENCODING=utf-8`). Không đổi `tp_web_home`, HR, KD hay module khác. Sau mọi sửa static (SCSS/OWL/JS) phải khởi động lại server để bundle cache trong bộ nhớ được làm mới, `-u` không đủ; lần tải đầu sau khởi động có thể trả 500 cho bundle JS (lỗi đổi tên tệp filestore trên Windows), tải lại là hết. Rollback: dừng 18069, khôi phục dump + filestore của điểm backup này cùng source `src/tp_equipment` (20.0.1.4.2); hai cột mới `tp_request_key`/`tp_request_hash` trên `tp_equipment_move` là NULL với mọi phiếu hiện có nên phục hồi source cũ cũng không mất dữ liệu nghiệp vụ. Chưa chạy restore verification.

**Cập nhật CHG-20261114-014 (EQUIP-UI-001):** đã triển khai thiết kế lại UI `tp_equipment` lên **20.0.1.3.0** trên main `18069` (`tp_tanphat_dev`) sau backup riêng tại `.local/equip-ui001/backup-pre-ui/` (DB dump + filestore + source `20.0.1.2.0` + `manifest.json`). Không dùng `18079`, không tạo dữ liệu giả, không chạy bộ test nghiệp vụ; kiểm chứng Playwright `verify_after.mjs` đạt `consoleErrors: 0, pageErrors: 0, serverErrors: 0` và kiểm tra bảo toàn DB (`PRESERVATION_DIFFS: ['modules']` chỉ đổi phiên bản `tp_equipment`).

**Cập nhật CHG-20261114-012:** đã nhập thật hai workbook local theo
[EQUIP-DATA-001](../../docs/prompts/CLAUDE_EQUIP_DATA_001_IMPORT_REAL.md) trên main18069 sau
backup mới; module lên 20.0.1.2.0. Chi tiết ở mục “Nâng cấp và nhập thật CHG-012”. Những dòng
“không import”/“chưa nhập” dưới đây mô tả lượt triển khai CHG-010.

Ngày 14/11/2026. Môi trường duy nhất trong lượt này: `tp_tanphat_dev`, HTTP `18069`, PostgreSQL workspace `55432`. **Đã nâng cấp `tp_equipment` 20.0.1.1.0 trên main 18069**; log thành công đã quan sát: `.local/equip001-main/upgrade-final4.log`. Mọi delta sau log này cần log update mới, không suy source vừa sửa đã tự áp. Không dùng `18079`, không tạo database task, không test suite/seed/import theo lệnh người dùng.

## Baseline và backup

Source addon: `C:\TANPHAT ONE\custom_addons\tp_equipment`, phiên bản source/DB đã ghi nhận `20.0.1.1.0`. Không commit/push trong lượt này. Module đã được cài trong phiên Claude dang dở, lần tiếp tục dùng **`-u tp_equipment`**, không `-i`.

Các điểm backup đang có trên máy, đều ignored/private:

| Điểm | Đường dẫn | Nội dung nhìn thấy |
| --- | --- | --- |
| Trước thay đổi Claude | `.local/equip001-main/backup-main-pre/` | `tp_tanphat_dev.dump`, `filestore/`, `backup_manifest.json`, source archive/hash và git status |
| Trước tiếp tục phiên dang dở | `.local/equip001-main/backup-main-resume/` | `tp_tanphat_dev.dump` **8.894.993 bytes**, `filestore/` **770 files**, `source_tp_equipment/` phiên Claude chưa hoàn chỉnh |
| Trước nhập thật CHG-012 | `.local/equip-data001/backup-pre-import/` | `tp_tanphat_dev.dump`, `filestore/` **786 files** + hash, `source_tp_equipment/` 20.0.1.1.0, `manifest.json` |
| Trước thiết kế lại UI CHG-014 (`EQUIP-UI-001`) | `.local/equip-ui001/backup-pre-ui/` | `tp_tanphat_dev.dump`, `filestore/`, `tp_equipment_src/` **20.0.1.2.0**, `manifest.json` |
| Trước Kho gọn CHG-20261116-003 (`EQUIP-SIMPLE-003`) | `.local/equip-simple003/backup-pre-simple003/` | `tp_tanphat_dev.dump` **9.259.433 bytes**, `filestore/` **855 files**, `src/tp_equipment` 20.0.1.4.2 + `src/tp_web_home`, `manifest.json` |

Backup `resume` giữ trạng thái phiên Claude dang dở: source snapshot **chưa hoàn chỉnh**, không phải bản module có thể phục hồi riêng rồi coi là chạy an toàn. Backup `pre` có database **trước khi cài addon**. Phải chọn điểm phục hồi cùng bộ source + DB + filestore tương thích, không tráo hai mốc. Sự có mặt của backup không đồng nghĩa restore đã được chạy/kiểm thử; **chưa restore** trong lượt này. Không đưa dump, filestore, workbook thật, nội dung source extract hoặc credential vào Git. Đối chiếu manifest/hash và độ đầy đủ DB+filestore trước nâng cấp; giữ hai điểm riêng để không mất đường quay lại trạng thái trước Claude. Đảm bảo không có tác vụ schema/ghi đồng thời.

## Nâng cấp đúng source

Dừng runtime main bằng quy trình hiện có; đối chiếu process/config/database/port, giữ nguyên các account/data. Từ thư mục gốc, lệnh module update có phạm vi:

```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local/odoo.conf -d tp_tanphat_dev -u tp_equipment --stop-after-init
```

Config phải trỏ đúng cluster workspace `55432` và data directory main; không in nội dung credential. Không thêm `--test-enable`, không tạo fixture hoặc gọi helper clone/seed lịch sử. Đọc log lỗi registry/XML/assets, sửa lỗi trong scope rồi chạy lại update. Khởi động lại main bằng launcher hiện hành, xác nhận [Odoo 18069](http://127.0.0.1:18069/odoo), mở **Kho thiết bị văn phòng** bằng admin và chụp ảnh giao diện đọc; không tạo/xóa hồ sơ thật để chứng minh hoạt động.

Ghi riêng: lệnh và mã thoát, version DB, runtime HTTP/registry/assets, ảnh desktop/mobile và giới hạn. Install/upgrade/open menu là quan sát vận hành, không ghi “test PASS”. Không mở cổng HR/HEAD/staff/native technician. Không cài `hr_maintenance`; nếu phiên cũ đã xử lý bridge này, giữ log và xác nhận trạng thái thực tế, không uninstall lặp theo suy đoán.

### Bằng chứng vận hành đã ghi nhận

- Source/DB: `tp_equipment` **20.0.1.1.0**, main `tp_tanphat_dev:18069`.
- Update thành công: `.local/equip001-main/upgrade-final4.log`, registry loaded, stop-after-init kết thúc bình thường. Nếu tiếp tục sửa source, ghi log update mới trước khi bàn giao source đó.
- URL [Odoo 18069](http://127.0.0.1:18069/odoo), menu **Kho thiết bị văn phòng**.
- Ảnh/DOM và capture summary: `.local/equip001-main/screens/`. Dashboard `tong-quan-thiet-bi-1440.png` / `tong-quan-thiet-bi-390.png`; danh sách chính rỗng và form mới **chưa lưu** đã mở ở 1440px. Capture ghi không console error/HTTP 500/overflow trong phạm vi quan sát. Không suy ảnh này chứng minh transaction hoặc quyền mọi vai trò.
- Excel sổ rỗng `.local/equip001-main/screens/so-thiet-bi-empty.xlsx` đã đọc lại **18 cột**; chưa có hồ sơ thiết bị để kiểm nội dung nhiều dòng/tổng/currency.
- Đối chiếu snapshot/hash trước–sau: giữ **39 employee / 28 user**, equipment/request/move/receipt đều **0**; `.local/equip001-main/preservation-after.json`. Không tạo giao dịch giả để chụp ảnh.
- Bộ test/AT suites: **không chạy theo yêu cầu người dùng**. Không 18079, seed hay import dữ liệu thật.
- Relation filter đã có source và assets: parent domain đầy đủ, khóa khi chưa lưu/dirty, dialog readonly. Chưa có dữ liệu thật để thao tác dialog/phân trang nhiều trang hay xác nhận giao dịch.
- Technical observation, business acceptance và pilot authorization ghi riêng; việc mở màn hình rỗng không thay thế nghiệm thu nghiệp vụ.

### Nâng cấp và nhập thật CHG-012 (EQUIP-DATA-001)

- Backup mới trước mọi thay đổi: `.local/equip-data001/backup-pre-import/` gồm dump `tp_tanphat_dev`, filestore (786 tệp + hash), source `tp_equipment` 20.0.1.1.0 và `manifest.json` hash các bảng HR/user/quyền/thiết bị.
- Source 20.0.1.2.0: chỉ `-u tp_equipment` (log `.local/equip-data001/upgrade-1.log`, registry loaded), restart main bằng launcher; `hr_maintenance` vẫn uninstalled. Thay đổi JS/XML dashboard cần restart để bundle assets mới được tạo.
- Nhập bằng ORM với admin (driver private `.local/equip-data001/import_real.py`, các pha prepare/apply/replay/summary; log từng pha cùng thư mục). Không SQL ghi nghiệp vụ, không cờ bỏ guard, không `mark_verified`.
- Kết quả đọc lại: NDL-00001 `partial` (54 hồ sơ đăng ký + 54 phiếu ghi nhận ban đầu; 10 dòng chờ), NDL-00002 `applied` (DX-00001 nháp/chưa xác minh, 5 dòng). Replay không tạo thêm bản ghi; tải lại cùng hash bị từ chối. Sequence NDL-00003/00004 bị bỏ qua do lần thử trùng rollback.
- Bảo toàn: `.local/equip-data001/preservation-after.json` — hash HR employee/version/department, users, group membership, company không đổi; `res_groups` chỉ đổi `write_date` nhóm HR do `data/config.xml` chạy lại khi `-u` (implied/membership không đổi).
- Báo cáo từng dòng và ảnh desktop/mobile: `.local/equip-data001/IMPORT_REPORT.md`, `.local/equip-data001/screens/` (private, có tên người/giá — không đưa vào Git).

**Áp dụng tiếp dòng chờ:** mở **Dòng nguồn chờ bổ sung** (`/odoo/dong-nguon-thiet-bi-cho`), xác nhận ID nhân viên HR đúng hoặc bổ sung thông tin thiết bị, xác nhận ánh xạ dòng, rồi **Áp dụng dòng đã xác nhận** trên NDL-00001. Đợt chuyển `applied` khi hết dòng chờ. Không tạo đợt mới cho cùng tệp; không sửa tên trong HR để khớp nguồn.

**Rollback riêng phần nhập CHG-012:** dữ liệu nhập đã có phiếu ghi nhận hoàn tất; không xóa tay hồ sơ/phiếu. Nếu cần quay lại trước nhập, dừng main, lưu thêm backup hiện trạng (để giữ giao dịch phát sinh sau nhập), rồi khôi phục bộ `backup-pre-import` (DB + filestore + source 20.0.1.1.0 cùng lúc) theo mục rollback dưới đây.

## Nhập dữ liệu thật là bước riêng

Mỗi lần nhập nguồn mới cần phạm vi riêng. Khi có phạm vi nhập: backup mới, xác định company và loại nguồn; upload vào preview, đối chiếu provenance cell đã làm sạch và phân loại từng dòng. Không thực thi formula/forward-fill tùy ý; không lưu IP/MAC/credential từ nguồn. Chọn ID HR và xác nhận alias, không fuzzy-match hoặc tạo employee/user.

Xác nhận mapping từng dòng áp dụng trước apply; dòng chưa rõ giữ wait/missing có lý do, đợt sẽ ở `partial` và áp dụng tiếp sau khi bổ sung; nguồn đề xuất cần đối chiếu thành tiền và tổng, không đổi thành đơn giá giả. Cùng hash/company/kind mở lại batch cũ; apply replay không tạo trùng. Với nguồn sau cùng loại, xác nhận đối chiếu phiên bản/đợt độc lập và lý do cấp batch/dòng. Dòng existing phải chọn ID cùng company (thuộc nguồn trước nếu có chọn), chỉ liên kết mà không ghi đè business data/provenance; dòng thực sự new xác nhận riêng mới tạo nháp. Không tự merge/overwrite lịch sử, không ghép hai dòng vào một ID. Không dùng tên tệp/STT làm định danh. Lưu nguồn và hồ sơ tạo ra ở mức chưa xác minh, không bịa ngày/serial/biên bản/duyệt.

## Rollback khi không mở được hệ thống

Ưu tiên sửa lỗi source trong scope khi bảo toàn dữ liệu. Nếu cần rollback, dừng runtime và lưu thêm DB+filestore+source hiện trạng để bảo toàn giao dịch phát sinh. Chọn đúng điểm `pre`, `resume` hoặc `backup-pre-import` cùng bộ source/database/filestore tương thích (`backup-pre-import` là điểm gần nhất có module chạy được, trước dữ liệu nhập CHG-012); `pre` DB chưa có addon, còn source `resume` chưa hoàn chỉnh nên không phục hồi riêng snapshot đó như bản module chạy được; so sánh thay đổi phát sinh sau backup và thống nhất phương án bảo toàn trước restore có mất dữ liệu. Không tự xóa dữ liệu thật hoặc restore test đè main.

Khôi phục source bằng snapshot của điểm đã chọn, không reset toàn repo hay metadata `.git`; người dùng có thể có thay đổi không liên quan. Phục hồi DB/filestore main theo runbook vận hành được kiểm soát, giữ account/owner/config, rồi restart và xác nhận đọc runtime. Không cung cấp lệnh DROP/restore mù trong runbook này. Ghi rõ điểm phục hồi, người thực hiện, thời điểm, dữ liệu phát sinh được bảo toàn và log. Không tạo database thứ ba để rehearsal trong task này.

Xem [schema/quyền](../../docs/security/EQUIP_001_SCHEMA_AND_ACCESS.md), [hướng dẫn](../../docs/demo/EQUIP_001_USER_GUIDE.md) và [acceptance](../../docs/demo/EQUIP_001_ACCEPTANCE.md). Technical acceptance, business acceptance và pilot authorization ghi riêng.
