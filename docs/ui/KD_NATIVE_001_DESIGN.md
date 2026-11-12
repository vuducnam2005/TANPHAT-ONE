# KD-NATIVE-001 — Thiết kế không gian Kế hoạch Kinh doanh

Ngày 06/11/2026, Asia/Saigon. Phạm vi là quản trị hồ sơ tổng hợp trên dev; không xác nhận pháp lý, kế toán hoặc pilot. Người dùng giao trực tiếp phiên chính thực thi prompt CHG-006. Tái sử dụng UI-CTR-NATIVE-001a đã audit CHG-003.

## Bản đồ màn hình

Home TANPHAT ONE → **Kế hoạch Kinh doanh** → Tổng quan, Cơ hội và hồ sơ thầu, Hồ sơ dự án, TP Contracts, Kế hoạch và công việc, các hồ sơ nghiệp vụ đã triển khai. Mỗi menu chỉ được xuất hiện khi model/view/action thật đã qua kiểm tra.

```text
Tổng quan KH-KD
  Dự án / Người phụ trách / Từ ngày / Đến ngày
  Việc cần xử lý: chờ tôi rà soát | bị trả lại | đến/quá hạn
  Nguồn hồ sơ: cơ hội | hợp đồng | công việc | hồ sơ theo từng domain
  Mỗi nút mở list có đúng domain và quyền actor

Hồ sơ dự án
  Mã + tên / khách hàng / phòng / người phụ trách / hạn
  Smart buttons: cơ hội, hợp đồng, công việc và hồ sơ thực có
  Tabs: tổng quan | kế hoạch | hồ sơ nghiệp vụ | nghĩa vụ

Hồ sơ nghiệp vụ
  Header: action theo capability + state / trạng thái có chữ
  Mã + tên; dự án, phạm vi, owner, reviewer, kỳ/hạn
  Tabs: nội dung | nguồn liên quan | lịch sử lần trình
  Tiền là phần riêng, chỉ tải sau kiểm grant hiện tại
```

## Nhận diện và thao tác

Giữ font hệ thống Odoo hỗ trợ tiếng Việt; không tải font ngoài. Màu nền trắng `#FFFFFF`, chữ `#263445`, xanh hồ sơ `#22577A`, tím action Odoo `#714B67`, cảnh báo `#986500`, trả lại `#A12A35`. Dùng màu kèm chữ và biểu tượng. Tiêu đề 24–28px; nhãn 14px; nội dung 16px; nhịp khoảng cách 8/16/24px. Nhận diện đặc trưng nằm ở dải công việc cần xử lý và các nguồn hồ sơ liên thông, không dựng hero hoặc thẻ KPI trang trí.

Ưu tiên form/list/search/group native, tab để tránh form dài. List có mã, dự án, owner, trạng thái, hạn/kỳ. Kanban cơ hội tắt kéo đổi trạng thái. Form lưu nháp bằng cơ chế Save native; action gửi/trả/mở sửa dùng hộp xác nhận có version và lý do khi bắt buộc. Không có action duyệt/chi tiền/hiệu lực. Hồ sơ đã gửi không sửa trực tiếp; lần trình giữ snapshot và actor/thời điểm. Metadata lịch sử không chứa tiền.

Mobile 390px xếp nhóm dọc, nút chạm tối thiểu 44px, cuộn bảng cục bộ; 768/1440px giữ group hai cột theo native. Focus nhìn rõ, trạng thái không chỉ dựa màu, tắt motion khi reduced-motion. Hủy form theo native; lỗi thiếu trường/ngày/quyền/version phải hướng dẫn khắc phục bằng tiếng Việt. Không tự retry thao tác ghi.

## Inventory preflight

| Nhóm | Backend/native hiện có | Cần bổ sung |
| --- | --- | --- |
| Cơ hội | crm.lead + tp_crm_project_bridge, native CRM | Checklist, nguồn/hình thức/hạn và action chuẩn bị/khai báo nộp trong scope |
| Dự án | project.project + tp_project, native | Hồ sơ tổng hợp và action hồ sơ con |
| Hợp đồng | tp_contract + native 001a đã audit test | Regression và upgrade dev sau backup; không viết lại |
| WBS | project.task chuẩn, manager ghi managed-task | Liên kết hợp đồng/đầu ra; TASK-001 staff denial giữ nguyên |
| Khoán/sản lượng/nghiệm thu/đề nghị | Chưa có model domain runtime | C1/C2/C3/C4 tuần tự; mỗi domain có spec/test/handoff |
| Kế hoạch/chứng chỉ/nghĩa vụ | Chưa có model phục vụ prompt | D tuần tự; dữ liệu kế hoạch không thành kế toán/pháp lý |
| Truyền thông/báo cáo | project.task + dashboard hiện hữu | Task chuẩn, báo cáo mở nguồn đúng quyền |

## Môi trường và cổng

Dev18069 PID23452, PostgreSQL55432, audit clone18169 đang chạy tại preflight; dev không có cờ reload. Addon contract dev1.1.0, checkout1.2.0. Snapshot riêng `.local/kd-native001/`, clone `tp_tanphat_kd001_20261106`/18269 và bản custom source riêng. Không sửa clone audit18169. Grant fixture chỉ dành actor tổng hợp, không mở quản trị grant cho người thật. Quyền WBS chỉ dựa policy manager hiện hành, không dùng admin làm bằng chứng staff.

## Tự kiểm thiết kế

Bỏ phương án trang KPI lớn vì người dùng cần thao tác và tìm hồ sơ; dùng hàng công việc cần xử lý và drilldown. Giữ chrome/font native vì cần nhất quán TANPHAT ONE và giảm phụ thuộc. Mỗi lô chỉ mở menu có nguồn thật, không dựng trạng thái pháp lý giả cho đủ chuỗi.

## Bố cục đã kiểm trên dev

Các màn hình đã có nguồn/model/action thật; smart buttons thay cho các tab kế hoạch/hồ sơ nguồn trong sơ đồ ban đầu. Form và list native, bảng hộp việc cuộn cục bộ trên390/768/1440. Ảnh desktop/mobile đã xem; money tab theo grant, lịch sử có state/actor/lý do. Context cha không được mang view/default sang model con. [Ma trận159assertion dev và giới hạn](../demo/KD_NATIVE_001_ACCEPTANCE.md), [đường bấm/kịch bản](../demo/KD_NATIVE_001_PRESENTATION.md). Không đưa font/React/session mới vào hệ thống.
