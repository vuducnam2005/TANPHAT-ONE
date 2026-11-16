# TANPHAT ONE — Quy chuẩn bộ lọc cho mọi bảng dữ liệu

Ngày: 14/11/2026. Task `UI-TABLE-FILTER-001`, quyết định `DEC-044`.
Trạng thái: **SPEC_READY — chưa triển khai trong lượt lập tài liệu này**.

## 1. Mục tiêu và phạm vi

Người dùng yêu cầu mọi bảng trong hệ thống có cách tìm/lọc phù hợp với nội dung,
bao gồm những phòng ban phát triển sau này. Một cách thao tác chung, nhưng mỗi
bảng có các tiêu chí riêng; không đưa một bộ lọc phòng ban/trạng thái chung vào
mọi bảng bất kể ý nghĩa. Bộ lọc không cấp quyền và không sửa dữ liệu.

Áp dụng cho danh sách chính, danh sách mở từ smart button, bảng trong chi tiết,
bảng con nhiều dòng, hộp thoại chọn bản ghi, lịch sử/audit, bảng báo cáo và các
ứng dụng Odoo hiện đang sử dụng. Bao gồm màn hình quản trị mà người dùng có
quyền truy cập. Không cài thêm ứng dụng chỉ để đáp ứng danh mục này.

Mỗi vị trí bảng cần một dòng inventory: `module / menu / action / model / view /
vị trí bảng con`. Không chỉ dùng model làm định danh: Danh sách nhân viên,
Hồ sơ cần bổ sung, Lưu trữ và Chưa có tài khoản dùng cùng `hr.employee` nhưng
có phạm vi bắt buộc và mục đích khác nhau.

## 2. Cách trình bày chung

- Giữ ô tìm kiếm native; bên dưới có hàng **Lọc theo** với khoảng 3–5 tiêu chí
  thường dùng của bảng, nút **Áp dụng**, **Xóa bộ lọc**, **Bộ lọc nâng cao**.
  Bảng danh mục đơn giản có thể chỉ cần tìm theo tên và 1–2 tiêu chí có nghĩa.
- Ô có nhãn rõ, khung đủ tương phản, trạng thái focus/lỗi/chưa chọn rõ ràng;
  dùng token `UI-INPUT-001`, nền sáng và phong cách chung của hệ thống.
- Phân biệt **Tất cả** với **Chưa khai báo**. Ví dụ loại hình lao động trống
  không được tự coi là dài hạn; chưa có tài khoản khác tài khoản bị khóa.
- Hiển thị chip điều kiện **đang áp dụng** và số kết quả; xóa từng chip được.
  Giá trị đang chọn nhưng chưa bấm Áp dụng không được coi là điều kiện có hiệu lực.
  Khi điều kiện đã áp thay đổi từ search/favorite native, thanh lọc phải đồng bộ.
- Giữ số dòng 10/20/50/100 và pager hiện có. Danh sách có nhóm ghi đúng đơn vị
  nhóm/bản ghi; không ghi chọn 10 là 10 nhân viên nếu pager đang phân 10 nhóm.
- Mobile thu gọn bộ lọc vào panel/drawer có số điều kiện đang dùng, giữ được
  nội dung đã chọn; điều khiển chạm tối thiểu 44px, không tràn ngang cả trang.
- Có nhãn bàn phím, focus rõ, Esc đóng panel, trả focus về nút mở. Animation
  mở/đóng nhẹ khoảng 150–200ms; tôn trọng `prefers-reduced-motion`, không animation
  hàng dữ liệu làm người dùng tưởng kết quả còn thay đổi.

Ví dụ Danh sách nhân viên:

```text
Tìm mã, tên, tên đăng nhập…                         Hiển thị 20 [▼]
Lọc theo: [Phòng ban ▼] [Chức vụ ▼] [Loại hình ▼] [Tình trạng ▼]
          [Áp dụng] [Xóa bộ lọc] [Bộ lọc nâng cao]
Đang lọc: [Kế hoạch Kinh doanh ×] [Mở ×]              … kết quả
```

Không thay sidebar, menu, bố cục danh sách/chi tiết hoặc quyền nghiệp vụ để thêm
hàng lọc. Không áp khung lọc cho biểu mẫu một bản ghi hay thẻ KPI đơn thuần.

## 3. Quy tắc lọc dữ liệu

1. Mỗi tiêu chí ánh xạ tới field thật, kiểu dữ liệu và operator/search method
   đã kiểm chứng. Trường compute không searchable phải dùng domain lên dữ liệu
   gốc hoặc search method được kiểm thử; không domain vào text hiển thị cho đẹp.
2. Các chiều khác nhau kết hợp **AND**; nhiều giá trị cùng một chiều kết hợp
   **OR**. Ví dụ phòng A hoặc B, đồng thời tài khoản Mở. many2one dùng ID, không
   lấy tên người/phòng làm khóa. Giữ cách nhóm OR của bộ lọc native.
3. Domain cuối = phạm vi action/parent bắt buộc AND điều kiện người dùng;
   ORM tiếp tục áp ACL, record rule, công ty và grant. **Xóa bộ lọc chỉ xóa
   điều kiện tùy chọn**, không gỡ domain, `active_test`, phạm vi parent hoặc quyền.
4. HR giữ `department_id` là nhóm đầu tiên theo HR-LIST-013 kể cả sau khi xóa
   facet, đổi favorite hoặc lọc một phòng. Lưu trữ không đồng nghĩa Khóa tài khoản.
5. Ngày từ/đến có kiểm tra thứ tự. `date` dùng ngày nghiệp vụ; `datetime` dùng
   timezone người dùng và khoảng nửa mở đến đầu ngày kế tiếp, không cắt mất giây
   cuối ngày. Không tự đặt ngưỡng “sắp hết hạn” nếu chưa có chính sách hiện hành.
6. Tiền theo currency/precision Odoo. Chỉ có bộ lọc tiền khi có quyền field;
   không so sánh trực tiếp các đồng tiền khác nhau. Không tự mở lọc tiền vì
   người dùng được xem danh sách hoặc sửa nháp.
7. Lọc trên **toàn bộ tập bản ghi hợp lệ ở server**, rồi mới đếm/sắp xếp/phân
   trang. Không lọc bằng JavaScript trên 20 dòng đang nhìn thấy rồi gọi là đầy đủ.
8. Áp dụng lọc đưa offset về đầu; giữ sort/cột hợp lệ. Mở chi tiết rồi quay lại
   giữ bộ lọc đã áp và trang hợp lệ. Kết quả bất đồng bộ cũ không ghi đè kết quả
   truy vấn mới; lỗi tải giữ điều kiện đã áp và có cách thử lại.
9. Xuất Excel/CSV dùng đúng domain **đã áp**, không dùng giá trị đang nhập dở.
   Nếu xuất các dòng được chọn phải ghi rõ phạm vi đó. Count/tổng/bảng/biểu đồ
   cùng phạm vi và công thức đã có; không cộng dữ liệu ngoài quyền hoặc đổi KPI.
10. Trường hợp không có kết quả hiển thị lý do/hướng dẫn đổi lọc; dữ liệu trống,
    đang tải, lỗi truy vấn và không có quyền phải có cách thể hiện riêng.

## 4. Quyền và sự riêng tư

- Backend kiểm quyền cho cả query, `name_search`, danh sách lựa chọn, count,
  tổng tiền, group-by, drill-down và export. Không `sudo()` để dựng tùy chọn.
- Field bị cấm không xuất hiện qua bộ lọc nâng cao, autocomplete, nhãn chip,
  error hay request trực tiếp. Không thể dò một khoản tiền/tên người ngoài phạm
  vi thông qua số kết quả, bucket, nhóm hoặc gợi ý.
- Đổi tài khoản/công ty/phòng/quyền hoặc hết phiên phải loại dữ liệu cũ. Không
  dùng cache chung cho người dùng, không lưu dữ liệu nhân viên/tiền/từ khóa nhạy
  cảm vào URL hay persistent browser storage. Favorite native theo quyền Odoo;
  tùy chọn hiển thị nếu lưu phải phân biệt database/user/company/action/view.
- Không mở rộng self-service `Thông tin cá nhân` thành danh sách toàn công ty.
  Không đưa mật khẩu vào bộ lọc hoặc log. Giữ CSV/Excel formula-injection guard.

## 5. Tái sử dụng trong Odoo native

Danh sách native dùng **một SearchModel**, search view/domain/facet/favorite và
relational model/pager hiện có. Rà và mở rộng `KdTableTools`/`HrTableTools` trước;
chỉ tách phần tương tác chung nhỏ khi có người gọi thật. Không viết filter engine
mới, không thêm React/Ant Design, không patch toàn cục ListRenderer để ép mọi view.

OWL report/dashboard giữ service và contract backend hiện hành, đồng bộ cùng
quy tắc lọc và phạm vi; không buộc một SearchModel vào màn hình không dùng native
list. Odoo app chuẩn bổ sung qua inherited search view trong `custom_addons/`,
không sửa `odoo/` hoặc `addons/`. Không tự thay schema để đủ số ô lọc.

Bảng con đã lưu phải giữ domain parent và lọc toàn bộ relation hợp lệ ở server.
Với x2many đang tạo mới/có dòng chưa lưu: không tự save/discard, không làm mất
ORM commands hoặc dòng bị ẩn. Nếu chưa lọc an toàn được, vô hiệu hóa và ghi
**Lưu hoặc hủy thay đổi để lọc bảng này**; giữ luồng thao tác gốc.

Bảng cấu trúc tĩnh, ví dụ vài dòng so sánh trước/sau của một sự kiện, có thể
ghi `N/A` nếu lọc không giúp gì. Inventory phải có lý do cụ thể, người/role chịu
trách nhiệm review và đường mở danh sách đầy đủ nếu có. Không miễn trừ cả nhóm
popup/lịch sử chỉ vì khó làm. Bảng hữu hạn/bị cap phải ghi rõ giới hạn; không
biến cap 500 dòng thành con số “toàn bộ” hoặc phân trang giả.

## 6. Checklist bắt buộc khi phát triển phòng ban hoặc bảng mới

Không đánh dấu hoàn thành UI bảng nếu chưa có đủ các mục sau (hoặc `N/A` có lý do):

- [ ] Đăng ký tất cả vị trí bảng, kể cả smart button, popup, bảng con và báo cáo.
- [ ] Xác định actor, action/view, domain bắt buộc, scope công ty/phòng/dự án.
- [ ] Chọn các tiêu chí theo nội dung; ghi nhãn tiếng Việt, field/operator,
      searchable, empty/unknown, ngày/tiền và phân quyền field.
- [ ] Thanh lọc dễ thấy; nâng cao/facet/favorite đồng bộ; phân biệt pending/applied.
- [ ] AND/OR, Xóa, grouped pager, count, export và drill-down khớp toàn bộ dữ liệu.
- [ ] Không mất draft/x2many hoặc nới quyền khi lọc/đổi trang/quay lại chi tiết.
- [ ] Test trên nhiều trang, kết hợp nhiều điều kiện, không có kết quả và thử lại.
- [ ] Test âm theo vai trò/công ty/grant; options/count/export không rò dữ liệu.
- [ ] Ảnh desktop/mobile và keyboard/reduced-motion; đánh giá trước/sau cùng bối cảnh.
- [ ] Inventory, acceptance, hướng dẫn dùng và status có đường dẫn bằng chứng.

## 7. Tài liệu thực hiện

- [Inventory hiện hành và phần cần mở rộng](TP_TABLE_FILTER_INVENTORY.md).
- [Prompt triển khai UI-TABLE-FILTER-001](../prompts/CLAUDE_UI_TABLE_FILTER_001.md).
- [Inventory KH-KD lịch sử KD-UI-007](KD_UI_007_TABLE_INVENTORY.md): nguồn đối
  chiếu, cần resolve lại view hiện tại; không coi thống kê 07/11 là coverage hôm nay.
- [Quy trình thay đổi](../AI_CHANGE_WORKFLOW.md), [mẫu bàn giao](../HANDOFF_TEMPLATE.md).
