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

Danh mục tên dùng chung trong frontend nằm tại `frontend/src/shared/config/product.ts`. Menu hiện có sử dụng **TP Projects**. Các phân hệ khác mới được xác lập tên, chưa được coi là đã triển khai hoặc thêm đường dẫn chưa có chức năng.

Giữ nguyên các tên kỹ thuật đã dùng trong database như `tp_project`, `tp.project.assignment`, XML ID và API `/api/v1/projects`. Tên sản phẩm không buộc addon phải trùng tên hoặc chỉ dùng một addon; backend chia theo trách nhiệm nghiệp vụ và dependency. Mọi tên addon tương lai trong tài liệu kiến trúc là tên kỹ thuật dự kiến.

Database dev/test, credential, filestore và model dữ liệu không đổi khi thay thương hiệu. Runtime sử dụng đường dẫn mới; script xác định root từ vị trí của chính nó, tránh hardcode đường dẫn máy phát triển.
