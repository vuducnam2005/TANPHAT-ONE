# TANPHAT ONE — Quy ước tên hệ thống và phân hệ

Thư mục làm việc chính: `C:\TANPHAT ONE`.

Tên sản phẩm thống nhất là **TANPHAT ONE**. Tên công ty Tấn Phát trong hồ sơ doanh nghiệp vẫn là tên pháp nhân. Tên phòng ban là không gian làm việc; phân hệ được đặt theo chức năng để các phòng cùng sử dụng.

| Phân hệ | Tên hiển thị | Hướng tổ chức source |
| --- | --- | --- |
| Điều hành doanh nghiệp | **TP Dashboard** | Màn hình tổng hợp và API reporting theo quyền |
| Quản lý dự án cầu đường | **TP Projects** | Feature `projects`, addon hiện có `tp_project`, kế thừa `project.project` |
| Quản lý khảo sát hiện trường | **TP Survey** | Feature `survey`, addon theo nghiệp vụ khảo sát khi triển khai |
| Quản lý hồ sơ thiết kế | **TP Design** | Feature `design`, addon theo nghiệp vụ thiết kế khi triển khai |
| Quản lý hợp đồng | **TP Contracts** | Feature `contracts`, addon dự kiến `tp_contract` và `tp_allocation` |
| Quản lý tiến độ, giao việc | **TP Tasks** | Feature `tasks`, dùng `project.task` và phần mở rộng cần thiết |
| Quản lý nhân sự | **TP HR** | Feature `hr`, dùng `hr` và addon hiện có `tp_organization` |
| Quản lý tài chính, chi phí | **TP Finance** | Feature `finance`, dùng `account`, `analytic` và các bridge khi triển khai |
| Quản lý văn bản, hồ sơ | **TP Documents** | Feature `documents`, metadata và download kiểm quyền ở backend |

Theo DEC-030 ngày05/11/2026, tên hiển thị hiện hành áp dụng trong menu/view/action/OWL native Odoo của các custom addon. Các từ `Feature` ở bảng trên là nhóm chức năng, không yêu cầu tạo route hoặc ứng dụng React. `frontend/src/shared/config/product.ts` là catalog React legacy được giữ; không dùng nó làm bằng chứng menu native đã có. Home, TP Projects và dashboard đã có; UI native TP Contracts đạt audit kỹ thuật trên test tại CHG-20261106-003 và đã được tái sử dụng, tích hợp dev18069 trong KD-NATIVE-001 tại CHG-20261106-017. Audit độc lập phạm vi tích hợp dev và nghiệm thu nghiệp vụ vẫn riêng. Các tên phân hệ khác không chứng minh chức năng đã triển khai; không thêm menu trống chỉ để đủ danh mục.

Giữ nguyên các tên kỹ thuật đã dùng trong database như `tp_project`, `tp.project.assignment`, XML ID và API `/api/v1/projects`. Tên sản phẩm không buộc addon phải trùng tên hoặc chỉ dùng một addon; backend chia theo trách nhiệm nghiệp vụ và dependency. Mọi tên addon tương lai trong tài liệu kiến trúc là tên kỹ thuật dự kiến.

Database dev/test, credential, filestore và model dữ liệu không đổi khi thay thương hiệu. Runtime sử dụng đường dẫn mới; script xác định root từ vị trí của chính nó, tránh hardcode đường dẫn máy phát triển.


## Ngữ cảnh KH-KD — KD-PROJECT-RESTRUCTURE-001

Trong nguồn test20.0.1.8.0, Dự án là project.project gốc; Hồ sơ dự án/lần tham gia vẫn dùng crm.lead, Đấu thầu dùng tp.bid.package. Chủ đầu tư là kd_investor_id riêng; partner_id cũ ghi Bên ký thương mại, không đổi nghĩa kế toán. Quản lý dự án là thực hiện WBS/task; Quản trị dự án là hồ sơ thương mại/nghĩa vụ trên cùng ID. TP Projects/TP Tasks/TP Contracts và XML ID cũ giữ. Dev18069 đã20.0.1.8.0, source/test/seal/apply đã đối chiếu trong [acceptance](../demo/KD_PROJECT_RESTRUCTURE_001_ACCEPTANCE.md).
