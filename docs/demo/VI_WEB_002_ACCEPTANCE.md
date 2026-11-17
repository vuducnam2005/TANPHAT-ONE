# VI-WEB-002 — Lỗi lý do, hộp đối chiếu và tiếng Việt

Ngày 17/11/2026, CHG-20261117-006/007. Người dùng báo lỗi tại `/app/action-528/35` trên public và yêu cầu Việt hóa toàn web, đồng thời sửa bố cục hộp Đối chiếu danh tính. Phạm vi này tiếp tục bản ADMIN-DELEGATE-001 đã giao; không tự cấp người thật hoặc mở rộng quyền nghiệp vụ.

## Nguyên nhân và thay đổi

- Hành động cấp/thu hồi tạo transient trước khi mở form, nhưng `reason` bắt buộc ở database. Người dùng chưa kịp nhập đã nhận lỗi. Hai hành động sửa/lưu trữ hồ sơ được ủy quyền có cùng lỗi. Cho phép lý do trống lúc mở; form vẫn bắt nhập và backend từ chối cả chuỗi trống/khoảng trắng khi xác nhận. Giữ xác thực lại, khóa bản ghi, tài khoản đích, scope, thu hồi và audit.
- Hộp đối chiếu xuất thẳng JSON ID/checksum trong `preview`, trường không có nhãn và ảnh gốc không giới hạn. Thay bằng nhãn và kết quả tiếng Việt, ảnh đọc từ bản thu nhỏ 128px, dialog vừa màn hình và hai cột ảnh co được. Digest, kiểm tra đồng thời và snapshot trước/sau vẫn ở backend; không đồng bộ tên/ảnh khi chỉ mở hoặc hủy.
- `base`/`web` thiếu bản Việt của chính thông báo lỗi; nhiều catalog mới còn trống hoặc giữ nguyên tiếng Anh. Mở rộng `tp_i18n_vi` qua catalog native, bổ sung cache theo namespace trong hook `ir.http`; không sửa core hoặc thay DOM. JavaScript/Python giữ cơ chế dịch, định dạng và placeholder gốc. Không đổi ngôn ngữ tài khoản hàng loạt, dữ liệu nhập tay, API payload hoặc tên sản phẩm.

## Tiêu chí và kiểm chứng

| Tiêu chí | Cách kiểm / bằng chứng |
| --- | --- |
| Admin mở cấp/thu hồi được trước khi nhập lý do | Mở/hủy trên hồ sơ có sẵn; kiểm reason trống và tài khoản đích chốt đúng. Không xác nhận cấp/thu hồi thật. |
| Không thể bỏ lý do | Backend smoke trong transaction rollback với `False` và khoảng trắng; browser nhấn xác nhận khi trống phải giữ dialog và báo trường thiếu. |
| Bố cục đọc được | 1440/768/390/320px; hai ảnh tải thật, thumbnail giới hạn, không JSON/hash, không cuộn ngang trong dialog, Esc đóng được. |
| Bản dịch không phá source | `scripts/check_vi_catalog.py`: PO không trùng/fuzzy/trống, placeholder, XML, hook chạy lặp, bản Việt native và en_US giữ đúng. Kiểm XML ID/source trên registry đang chạy bằng thao tác đọc. |
| Dữ liệu/quyền giữ nguyên | Fingerprint user/group/HR/nghiệp vụ trước/sau; ledger vẫn 0, không chọn người nhận, không upload tệp thử vào main/server. |
| Native UI | HR, Trao đổi, Việc cá nhân, Lịch, Liên hệ, CRM, Dự án, Giờ làm việc, Kho, Báo cáo, Cài đặt; chờ nội dung tải xong, kiểm console, public và các hộp thoại liên quan. |

Catalog hiện có 5.247 mục overlay và 5.243 mục bổ sung namespace, 6.694 nguồn khác nhau (có mục dùng chung giữa catalog). Bổ sung khoảng 6.546 nguồn so với bản 148 mục trước; thêm 4 mục thông báo server ở catalog riêng. Trong phần mở rộng tự động, 39 tham chiếu metadata cũ không khớp runtime được loại; 387 mục dịch vẫn bằng nguồn được giữ ngoài bản thêm (định danh, ví dụ, tên riêng và thuật ngữ kỹ thuật cần bảo toàn). Hai nhãn kiểm trực quan cuối được bổ sung theo source runtime: `Week ` và hướng dẫn Barcode Lookup. FullCalendar thiếu `weekTextLong` trong locale `vi`, nên asset bổ sung đúng locale trước khi khởi tạo lịch; không sửa core/DOM hoặc locale khác. Không nhận số mục là bằng chứng kiểm thủ công từng màn hình.

Chuỗi nguồn gửi dịch tự động chỉ lấy từ catalog upstream công khai; không có nội dung database, hồ sơ, credential hoặc filestore. Các thông báo quan trọng/thuật ngữ đang dùng được rà thủ công; phần chuyên sâu có kiểm định dạng và rà mẫu, chưa được người dùng nghiệm thu thuật ngữ. Không dịch dữ liệu mẫu tiếng Anh thành dữ liệu doanh nghiệp.

## Môi trường và giao bản

Đã áp trên 18069, đang chuẩn bị PC server. Bằng chứng private `.local/vi-web002/`; backup local `.local/admin-delegate001/backup-dev-vi-web002/` gồm dump 9.646.950 byte đã đọc được mục lục, filestore ZIP 254.446.424 byte và manifest checksum. Chỉ nâng cấp `tp_admin_delegation` 20.0.1.0.1, `tp_hr_workspace` 20.0.1.11.6, `tp_i18n_vi` 20.0.1.1.0. PC server đã áp commit35e1c11f,90/90tệp checksum,upgrade0/0ERROR;backup C:/TANPHAT-backups/vi-web002/20261117T164626. Patch dashboard20.0.1.1.1 đã áp18069, đang giao tiếp server.

Kiểm local: catalog 10.494 mục PASS; Ruff/XML/Python AST và kiểm locale lịch PASS; 2.177 tham chiếu XML ID/source khớp registry. Backend mở cấp/thu hồi không lý do, từ chối `False`/khoảng trắng và kiểm digest trong transaction rollback. Browser 35/35 ở 1440/768/390/320px, 14 màn hình chính không lỗi trang. Fingerprint 20 bảng, base URL và ledger 0/0 giữ nguyên; chỉ phiên bản 3 addon đổi. Các log upgrade thành công exit0/0ERROR. Không có audit độc lập vì subagent không khởi tạo được với model runtime hiện tại.

Public35/35 ở4kíchthước;13màn tải được và Reporting báo từ chối do nhóm hiện có, không đổi quyền để kiểm.0JSerror/overflow;Lịch/Bảng tổng hợp đã chờ renderer sau ảnh loading đầu. Backend2177refs/rollback PASS.20bảng ngay saucài/baseURL/ledger0/0giữ;cuối chỉcron tựtiến. Media83/83,666row/169blobđủ/hashđúng;Excel2sheet vàPDF hợp lệ/no-store/anonymous303. Không có attachment PDF/Word/Excel thật trênserver.

Dashboard mẫu thiếu namespace trong native response;20.0.1.1.1 bổ sung namespace và dịch các ô literal khớp catalog nguồn trên phản hồi tiếng Việt, không thay dữ liệu lưu, công thức/số hoặc en_US. Kiểm12tổhợp phản hồi và native denial khôngDB PASS. Nội dung mẫu/tên riêng không có trong catalog có thể vẫn giữ tiếng Anh, ví dụ giá trị mẫu ngày/số hoặc trạng thái nhập dưới dạng dữ liệu; không nhận là đã dịch mọi dữ liệu.

Không chạy suite Odoo tạo fixture trên main/server; không chạy hoặc thay DB18079/clone. Test hồi quy Odoo mới được lưu trong source để chạy ở môi trường được phép sau này. Smoke hiện tại chỉ dùng hồ sơ có sẵn, mở/hủy hoặc transaction rollback; không chứng minh trọn luồng cấp thật, chỉnh danh tính thật, delegate profile hoặc multiworker.

N/A bộ lọc: không thêm bảng hay đổi domain/count/export; chỉ đổi bản dịch và form transient. Coverage quyền nghiệp vụ ADMIN-DELEGATE-001 vẫn theo [bản riêng](../security/ADMIN_DELEGATE_001_COVERAGE.md), không được nhận là đã đóng các gap quyền chỉ từ sửa dialog.

Rollback: giữ backup trước áp; hoàn source đúng phạm vi, khởi động lại mọi worker để bỏ cache dịch bổ sung, nâng cấp lại các addon tương ứng. Không tự phục hồi toàn DB đè dữ liệu mới. Catalog model đã import cần nạp lại bản native/overlay cũ với overwrite nếu muốn hoàn bản dịch; gỡ addon đơn thuần không xóa các giá trị đã dịch.
