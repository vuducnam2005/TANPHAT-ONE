# KD-UI-007 — Thiết kế triển khai

Ngày 07/11/2026, Asia/Saigon. Yêu cầu trực tiếp cho phép phiên hiện tại triển khai và áp dev sau kiểm thử; không commit/push. Hướng tất cả bảng thay phạm vi bốn màn của KD-UI-006; mẫu cũ chưa được nghiệm thu.

Native Odoo giữ một SearchModel, một relational model và pager. Thanh tìm kiếm native nằm ở hàng đầu; hàng bộ lọc nhanh có chữ, bộ lọc nâng cao và xóa lựa chọn ở hàng sau. Bộ lọc được tạo từ field/search item thật, chips dùng facet native. Chọn 10/20/50/100 trực tiếp thay limit/offset của model; mặc định 20, lưu theo database/user/action/view. Grouped ghi đơn vị nhóm và giữ pager con native.

Màu: sidebar #17324D, nền #F4F7FB, mặt bảng #FFFFFF, header #EAF1F8, viền #D8E3EF, chữ #1F2937, primary #1D4ED8. Giữ font native dễ đọc, tiêu đề 20px, dữ liệu 14px; tên/mã có ưu tiên bề rộng. Ba vùng tiêu đề/tìm kiếm, lọc và bảng rõ ràng. Badge semantic theo model/field/value: xám nháp; xanh dương rà soát; tím thực hiện; vàng chưa xác minh; đỏ trả lại; xanh lá chỉ hoàn thành thật. Không tô đỏ cả dòng returned.

Các bảng con dùng widget riêng chỉ được gắn vào view KH-KD; quan hệ ORM giữ nguyên. Saved readonly mở danh sách liên quan theo domain ID chính xác để lọc server-side cả quan hệ. Editable/new/dirty vô hiệu lọc với giải thích “Lưu thay đổi để lọc”; pager native vẫn bảo toàn lệnh ORM. Bảng nguồn/legend số dòng cố định có nhãn số dòng, không pager giả. Dashboard giữ nguồn, công thức, stale/error và MERGE_MAX; PAGE_MAX tối đa 100 có test ranh giới.

Desktop thấy nhãn số dòng và Bộ lọc. Mobile toolbar xuống dòng, chip/table cuộn trong vùng riêng; không tràn toàn trang. Button/panel transition 180ms, không animation row/tiền; reduced motion giữ. Quyền, context/version, dirty guard và controller backend không đổi.

Kiểm ảnh thực cùng actor/dataset/viewport trước–sau, đọc ảnh sau từng nhóm. Test kỹ thuật, phản hồi hình thức, business acceptance và pilot authorization là các kết luận riêng.

## Kết cấu đã triển khai

`table_tools.js/xml` dùng mixin trên ba controller hiện có: list thường, ProjectListController và list có guard. Không patch ListRenderer/Pager toàn hệ thống. Bộ lọc nhanh lấy item thật của SearchModel; bộ lọc theo trường dùng whitelist và metadata searchable từng model, native facets/favourites/group-by giữ một nguồn state. Không RPC lấy toàn bộ hồ sơ/người để dựng dropdown. Date/datetime dùng formatter/picker native và có năm; widget chỉ đổi cách trình bày khi đang ở app KH-KD.

SearchBar native có template kế thừa riêng của controller KH-KD, luôn hiện trên mobile thay vì thu thành icon. Ngoài app dùng lại điều kiện native; không tạo ô tìm kiếm thứ hai. Bộ chọn số dòng giữ một hàng ở360/390px, nút Bộ lọc mở vùng nhập còn chip native đi cùng search.

`relation_tools.js/xml` kế thừa X2ManyField, chỉ gắn vào các view trong inventory. Popup readonly dùng toàn `currentIds`, backend kiểm quyền lại; không ghi lại quan hệ bằng tập đã lọc. Bảy popup lịch sử có form readonly rõ ràng, trong đó năm popup có bảng snapshot giá trị với điều kiện `parent.can_read_money`. Các biểu thức quyền, action/context/version và guard gốc giữ nguyên.

`status_badge.js` ánh xạ model + field + technical value; hết hạn chứng chỉ dựa `valid_to`/ngày native, giữ ngưỡng minh họa 30 ngày. `tables007.scss` nạp cuối, có scope shell/widget; sửa cả cell, widget và badge để nhãn dài wrap đầy đủ qua quy tắc ellipsis native. Màu ở badge, bỏ decoration đỏ cả dòng returned. Dropdown native dùng ký tự mũi tên có font sẵn.

Backend chỉ nâng validation `PAGE_MAX` từ 50 lên 100, có test nhận 100/từ chối 101; `MERGE_MAX=500`, các công thức và quyền không đổi. Hai bảng record Tổng quan có lựa chọn100; nguồn/legend cố định có nhãn, preview kế hoạch12/chứng chỉ5 có đường mở native list đầy đủ. Phiên bản addon đích `20.0.1.5.0`.
