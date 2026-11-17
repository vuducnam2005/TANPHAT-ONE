# VI-WEB-002 — Lý do, đối chiếu danh tính và tiếng Việt

Ngày 17/11/2026; CHG-20261117-006/007/008. Trạng thái: **đã áp 18069 và PC server, còn giới hạn được ghi rõ dưới đây**. Tiếp tục yêu cầu trên `/app/action-528/35` và hai ảnh người dùng cung cấp.

## Nguyên nhân và bản sửa

- **Thiếu Lý do:** hành động cấp/thu hồi tạo transient trước khi mở form, nhưng trường `reason` bắt buộc ở database. Người dùng chưa kịp nhập đã nhận lỗi. Hành động sửa/lưu trữ hồ sơ được ủy quyền có cùng lỗi. Cho phép trống lúc mở; form và backend vẫn bắt lý do khi xác nhận, kể cả trường hợp chỉ nhập khoảng trắng. Giữ xác thực lại, tài khoản đích, khóa, scope và audit.
- **Đối chiếu danh tính:** form cũ xuất JSON ID/checksum, ảnh gốc quá lớn và thiếu nhãn. Form mới dùng nhãn rõ, hai ảnh thu nhỏ 128px, hộp thoại vừa màn hình và kết quả tiếng Việt. Backend vẫn giữ digest, kiểm đồng thời, snapshot trước/sau và ảnh gốc khi đồng bộ. Chỉ mở/hủy không đổi tên hoặc ảnh.
- **Tiếng Việt:** bổ sung catalog native và cache dịch theo namespace `web`, `mail`… cho `vi`/`vi_VN`; giữ bản Việt native và en_US. FullCalendar thiếu nhãn tuần dài trong locale Việt, nên addon bổ sung đúng locale trước khi khởi tạo lịch. Không sửa core hoặc thay DOM.
- **Dashboard mẫu:** phản hồi native thiếu `translation_namespace`; ô nhãn tĩnh của mẫu cũng không dùng công thức `_t`. Route kế thừa bổ sung namespace và dịch những ô literal khớp catalog của module nguồn. Giữ auth/readonly và mọi từ chối native; không ghi database, đổi công thức/số hoặc phản hồi en_US/dashboard thật.

## Môi trường, source và sao lưu

Hai commit chức năng **35e1c11f** và **73ffae56** đã push `origin/main`, áp trực tiếp trên 18069 rồi triển khai PC server. Gói đầu 90 tệp và delta 11 tệp có tổng cộng 92 tệp riêng biệt; tất cả khớp SHA256 từ commit. Giữ các thay đổi Reporting, branding, login và sidebar của phiên khác.

| Addon | Phiên bản trên 18069 và PC server |
| --- | --- |
| tp_admin_delegation | 20.0.1.0.1 |
| tp_hr_workspace | 20.0.1.11.6 |
| tp_i18n_vi | 20.0.1.1.1 |

Backup local: `.local/admin-delegate001/backup-dev-vi-web002/`, gồm dump 9.646.950 byte, filestore ZIP 254.446.424 byte, source/config và checksum. Dump đã đọc được mục lục.

Backup server: `C:/TANPHAT-backups/vi-web002/20261117T164626/` và bản tiếp theo `20261117T170450/`. Bản sau gồm dump 9.341.539 byte, filestore 28.564.607 byte, source/config 4.477.936 byte, mục lục pg_restore và SHA256. Hai lần upgrade đều exit0/0ERROR; runtime sau restart có 0ERROR và 0FileNotFoundError. Không đổi tunnel/DNS. Chưa diễn tập phục hồi toàn DB.

## Kết quả kiểm

| Phạm vi | Kết quả và bằng chứng private |
| --- | --- |
| Catalog | 10.494 mục PASS: không trùng/fuzzy/trống, placeholder; hook chạy lặp, bản Việt native và en_US. `scripts/check_vi_catalog.py`. |
| Source runtime | 2.177 tham chiếu XML ID/source khớp registry ở cả hai môi trường. Ruff, Python/XML và kiểm locale lịch đạt. |
| Backend | Mở cấp/thu hồi được khi chưa nhập lý do; `False`/khoảng trắng bị từ chối. Identity digest còn nguyên. Smoke dùng transaction rollback, không tạo grant thật. |
| Hai hộp thoại | 35/35 trên 18069 và public, tại 1440/768/390/320px. Ảnh decode, kích thước giới hạn, không JSON/hash hoặc cuộn ngang; Esc đóng. Public dùng đúng hồ sơ35. |
| Màn hình | Main rà14 màn; public có13 màn tải được và Reporting bị native AccessError vì admin server thiếu nhóm Báo cáo có trước. Không tự cấp nhóm để kiểm. Lịch/Settings/dashboard chờ renderer thật, có nhãn Tuần47, hướng dẫn Barcode và tiêu đề/cột mẫu tiếng Việt. 0 lỗi JavaScript hoặc cuộn ngang ở các màn đã rà. |
| Dashboard mẫu | Checker12 tổ hợp ngôn ngữ/sample/namespace và việc giữ native denial đạt. Public API200, có namespace,23 ô nhãn được dịch; mọi giá trị snapshot khác giữ nguyên so file upstream. Anonymous303. |
| Bảo toàn | Local20 bảng giữ fingerprint đến cuối. Server20 bảng/base URL/ledger0/0 giữ ngay sau cả hai lần cài; các bảng user/group/nghiệp vụ giữ đến cuối. Ở mốc cài đầu chỉ lịch cron tự tiến. Không cấp/thu hoặc xác nhận đối chiếu người thật. |

Evidence ở `.local/vi-web002/`: các thư mục `dev-verified`, `public-verified`, `dev-final-vi`, `public-final-vi`, `public-sample-final`; log upgrade, fingerprint và manifest source. Ảnh loading đầu của Lịch/Bảng tổng hợp không được tính là màn đạt; đã chờ renderer rồi kiểm lại.

## Ảnh và từng loại tệp

Nguyên nhân ảnh của DEPLOY-MEDIA-001 là149 blob thiếu vật lý tại filestore thật; đã phục hồi add-only theo size/checksum ở bản trước. Lượt này không đổi ACL/public để chữa ảnh.

| Loại | Kết quả sau deploy |
| --- | --- |
| Filestore/ảnh/đính kèm hiện có | 666 stored rows/169 blob:0 thiếu,0 khác checksum/size; Docker mount đúng. 83/83 kiểm origin/public đạt. |
| Excel | Export HR từ dữ liệu hiện có qua HTTPS200,9749 byte,MIME đúng; đọc được2 sheet. `no-store`, anonymous303. Không có XLSX attachment thật lưu sẵn để kiểm. |
| PDF | Export nhãn thiết bị qua HTTPS200,29028 byte,MIME/header/EOF đúng; `no-store`, anonymous303. Bản trước đã xem1 trang bằng PDF viewer. Không có PDF attachment thật lưu sẵn trên server. |
| Word | Không có DOCX attachment thật trên server để kiểm tải/đọc thực tế. Fixture lịch sử trên test không thay cho mẫu thật. Không upload dữ liệu giả lên main/server. |

## Độ phủ và giới hạn

Catalog gồm5.247 mục overlay,5.243 mục namespace và4 mục thông báo server, có6.694 nguồn khác nhau giữa overlay/namespace (so với148 nguồn của bản cũ). Không dùng số lượng thuật ngữ làm bằng chứng đã kiểm thủ công toàn bộ web.

Phần mở rộng dùng dịch tự động chuỗi UI upstream công khai, có kiểm định dạng và rà mẫu; thông báo quan trọng/thuật ngữ đang dùng được rà thủ công. Không gửi database, hồ sơ, credential hoặc filestore tới dịch vụ dịch.39 tham chiếu metadata cũ không khớp runtime được loại;387 mục vẫn bằng nguồn là tên riêng, ví dụ hoặc thuật ngữ kỹ thuật không được thêm tự động.

Chưa nghiệm thu mọi thuật ngữ, popup, role và luồng chuyên sâu. Tên người, nội dung nhập tay, mã kỹ thuật và một số giá trị mẫu ngoài catalog vẫn giữ nguyên; ví dụ `379 days`/`Not Paid` trong dữ liệu mẫu. Không thay dữ liệu nhập tay thành nhãn Việt.

Không chạy suite Odoo tạo fixture trên main/server,18079 hoặc DB clone; các test hồi quy mới đã lưu trong source nhưng chưa chạy. Không xác nhận grant/sync thật; chưa kiểm trọn luồng multiworker hoặc mọi nghiệp vụ của delegate. Không có audit độc lập vì subagent không khởi tạo được với model runtime hiện tại.

Coverage quyền ADMIN-DELEGATE-001 vẫn theo [bản riêng](../security/ADMIN_DELEGATE_001_COVERAGE.md): còn CRUD của một số model/phòng và multiworker; sửa dialog không đóng các gap này. Technical acceptance, business acceptance và pilot vẫn riêng. Không tự chọn người thật nhận quyền.

Bộ lọc N/A: không thêm bảng hoặc đổi domain/count/export; chỉ đổi form transient và bản dịch. Không phát triển filter engine khác.

## Hoàn bản trước

Giữ backup và source đã commit. Khi cần rollback, hoàn đúng scope source, restart mọi worker để bỏ cache bổ sung rồi nạp lại catalog native/overlay cũ với overwrite. Gỡ addon đơn thuần không xóa các bản dịch model đã ghi. Không tự restore toàn DB đè dữ liệu mới; chưa diễn tập rollback.
