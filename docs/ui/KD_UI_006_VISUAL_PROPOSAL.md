# KD-UI-006 — Đề xuất thay bố cục Kinh doanh và dự án

Ngày 07/11/2026. CHG-20261107-009. Người dùng không ưng giao diện KD-UI-005 và yêu cầu đề xuất chỉnh lại. Đây là bản mẫu thiết kế với dữ liệu minh họa, chưa triển khai vào Odoo/18069. [Bản đang có và phản hồi](../demo/KD_UI_005_ACCEPTANCE.md#phản-hồi-thị-giác-sau-bàn-giao--chg-20261107-008).

## Hướng chọn trước khi dựng mẫu

Màn hình phục vụ đọc, tìm và xử lý hồ sơ cầu đường hằng ngày. Điểm nhấn là **tên hồ sơ gắn với khách hàng và tình trạng**, không phải dashboard số liệu. Giữ khung điều hướng hiện hành; thay cấu trúc vùng nội dung để khác biệt nhìn thấy rõ.

| Thành phần | Đề xuất |
| --- | --- |
| Màu | Navy #17364B (khung hiện có), xanh #245F80 (hành động), chữ #203547, nền #F3F6F8, viền #DFE7EC; amber #946517 cho cảnh báo chưa xác minh |
| Chữ | Segoe UI/system, hỗ trợ tiếng Việt và gần native Windows/Odoo; tên trang26px, tên hồ sơ24px, tên dòng14–15px semibold, thông tin phụ12–13px |
| Danh sách | Tiêu đề và nút tạo tách khỏi hàng tìm/lọc. Bộ lọc tình trạng lộ rõ. Tên và khách hàng cùng một ô hai tầng; hạn, người phụ trách, hình thức và tình trạng có vị trí ổn định; giảm đường kẻ dọc và nhãn lặp |
| Chi tiết | Tiêu đề gọn + hành động native; nội dung chính khoảng2/3, thông tin phụ trách/dự án khoảng1/3; các mục ngắn mở sẵn, nội dung dài trong tab. Hết kiểu nhiều ô rời nằm trong khoảng trắng lớn |
| Liên kết dự án | Ba đường Cơ hội/Hợp đồng/WBS nổi rõ, bảy đường phụ gom có nhãn. Không thêm số đếm giả |
| Motion | Hover/focus120ms, mở vùng160ms nếu không remount field; tắt theo OS và preference; không animation lặp |

```
Danh sách: [Tên trang + phạm vi]                              [Tạo hồ sơ]
           [Tất cả] [Đang tìm hiểu] [Đang chuẩn bị] [Đã khai báo nộp]
           [Tìm tên/khách hàng...]              [Lọc] [Nhóm] [Cột]
           Hồ sơ + khách hàng | Tình trạng | Hạn | Phụ trách | Hình thức

Chi tiết:  [Quay về danh sách]                            [Lưu/Hủy native]
           Tên hồ sơ                                 Tình trạng + action
           [Phạm vi / Checklist / Năng lực]          Dự án, khách hàng
           Nội dung và ô nhập theo chiều đọc        Phụ trách, hạn, hình thức
```

Review trước code: bỏ dải KPI/card thống kê vì không giúp xử lý hồ sơ và dễ tạo cảm giác template; giữ nguyên sidebar/chrome để không biến task bốn màn thành đổi theme toàn hệ thống. Không thêm state dự án, tiến độ, tiền, lịch sử duyệt hoặc upload chưa có backend. Nhãn “Đã khai báo nộp” luôn đi với “Chưa xác minh”. Count trong mẫu chỉ lấy từ chính các dòng minh họa đang lọc.

## Yêu cầu mới sau đề xuất — CHG-20261107-011

Người dùng tiếp tục phản hồi giao diện ít thay đổi và yêu cầu bộ lọc, chọn số dòng,
màu trạng thái cho **toàn bộ bảng KH-KD**. Hướng triển khai hiện tại chuyển sang
[KD-UI-007](../prompts/CLAUDE_KD_UI_007_ALL_TABLES_FILTERS_STATUS.md), rộng hơn bốn
màn của mẫu này. Giữ mẫu làm tham khảo; không coi phản hồi mới là chấp nhận hình
thức của mẫu, không đợi một bước duyệt mẫu bốn màn để bắt đầu task mới đã giao.

## Ràng buộc khi triển khai thật

Giữ model/field/action/ACL/domain/private links hiện hành. Native search/group/sort/pager/checkbox/chọn cột và ProjectListController phải giữ; bố trí ô hai tầng có thể cần renderer có scope và kiểm sorting/export/optional columns riêng. Form vẫn dùng FormController, không tự viết chế độ lưu/autosave. Màn nhỏ xếp một cột; bảng cuộn trong vùng riêng, không cắt tên để che lỗi.

Bản mẫu HTML chỉ thể hiện thiết kế, tương tác tìm/lọc/chuyển màn/đọc nhóm liên quan với dữ liệu giả; không là frontend runtime, không gọi RPC/REST, không có credential. Không áp vào18069 trong lượt đề xuất. Sau phản hồi thiết kế mới triển khai slice native, clone-test và backup trước apply theo quy trình đã giao. Technical self-check, visual acceptance, business acceptance và pilot ghi riêng.

## Bản mẫu và tự kiểm thiết kế

[Mở HTML bốn màn](../../deliverables/kd-ui006-proposal/index.html). Chọn các nút ở dải trên cùng để đổi màn; tìm tiếng Việt không dấu, lọc tình trạng, mở form, đổi tab và nhóm hồ sơ liên quan là tương tác minh họa. Những nút workflow chỉ nêu vị trí, không thực thi nghiệp vụ.

| Màn | Desktop1440 | Mobile390 |
| --- | --- | --- |
| Danh sách cơ hội | [Ảnh](../../deliverables/kd-ui006-proposal/opportunities-1440.png) | [Ảnh](../../deliverables/kd-ui006-proposal/opportunities-390.png) |
| Chi tiết cơ hội | [Ảnh](../../deliverables/kd-ui006-proposal/opportunity-1440.png) | [Ảnh](../../deliverables/kd-ui006-proposal/opportunity-390.png) |
| Danh sách dự án | [Ảnh](../../deliverables/kd-ui006-proposal/projects-1440.png) | [Ảnh](../../deliverables/kd-ui006-proposal/projects-390.png) |
| Chi tiết dự án | [Ảnh](../../deliverables/kd-ui006-proposal/project-1440.png) | [Ảnh](../../deliverables/kd-ui006-proposal/project-390.png) |

Playwright14kiểm bản mẫu đạt:8layout (4màn×2width) không tràn toàn trang; lọc3dòng preparation từ8dòng minh họa, tìm `hoa lam`, mở dòng, tab Checklist,7liên kết phụ và Escape. Không pageerror. [Report](../../deliverables/kd-ui006-proposal/verification.json). Đã mở ảnh desktop và mobile để review; đây không là test Odoo/ACL/native controller hay nghiệm thu của người dùng.

Trong mẫu cơ hội, phần Checklist ở tab Phạm vi là bản đọc nhanh; ô sửa chỉ ở tab Checklist. Khi triển khai, đọc từ cùng field đã tải, không nhân bản ô nhập hoặc thêm RPC. Đầu ra dự án là nội dung minh họa của `kd_scope`, không tạo field/workflow mới. Count chỉ của dataset giả, không dùng như số liệu doanh nghiệp. Khung sidebar/chrome chỉ tái hiện bối cảnh, không đề xuất đổi theme toàn ứng dụng.

Trạng thái **MOCKUP_READY_FOR_VISUAL_REVIEW**. Chưa có visual acceptance; chưa mở pilot hoặc đóng backlog KD-UI-005 từ bản mẫu.
