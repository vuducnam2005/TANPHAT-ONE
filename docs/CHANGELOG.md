# TANPHAT ONE — Nhật ký thay đổi

Mỗi lượt thay đổi code hoặc quyết định kiến trúc ghi một mục ngắn. Không ghi credential, dữ liệu thật hoặc log chứa bí mật.

## CHG-20261028-003 — OPS-001: backup và phục hồi dev cô lập

- Phạm vi: script backup/restore, hướng dẫn vận hành và bằng chứng thực chạy; không sửa model/API/frontend hoặc seed dữ liệu vào dev.
- Backup: snapshot nhất quán khi tạm dừng Odoo dev 18,95 giây, 314 bảng public, 37 tham chiếu attachment/27 blob, database dump 3.043.333 byte; source archive tại commit `d9e8ccdc`. Backup và credential giới hạn quyền, nằm ngoài Git.
- Kết quả: giải nén source từ backup; restore vào cluster mới cổng 55442, Odoo 18089, database/filestore riêng; 314 bảng/fingerprint và 37 attachment khớp trước neutralize; probe 2 attachment chỉ tồn tại ở bản sao; cluster/Odoo cô lập đã dừng; dev gốc smoke lại đạt.
- Kiểm thử tooling/tích hợp: 21 unit tests đạt, Ruff đạt; anonymous 401, planner/admin login + `/me` + list/detail DTO + query validation, 37 lượt tải tệp khớp SHA1/size và kiểm attachment theo scope đạt. Báo cáo cuối ở `.local/ops-001/rehearsals/20261028T064405723351Z/report.json`.
- Hướng dẫn: `ops/runbooks/BACKUP_RESTORE.md`. Chưa có lịch backup, backup ngoài máy hoặc phục hồi trên host khác.
- Next: BIZ-001 — đối chiếu 2–3 hồ sơ đại diện và chốt ma trận quyền/trạng thái.

## CHG-20261028-002 — Chốt baseline Git và publish handoff

- Phạm vi: kiểm chứng local `main` với `origin/main`, rà soát các file handoff đang chờ commit và chuẩn bị publish toàn bộ thay đổi hiện tại.
- Đã thay đổi: cập nhật trạng thái GIT-001 đã hoàn tất, chuyển Next action sang OPS-001, chốt DEC-010 và cập nhật roadmap; không sửa model/API/giao diện/database.
- Kiểm tra: `git fetch --prune origin`; local/remote cùng ở `a25a0182`; `git status`; kiểm tra credential-like patterns trong file dự kiến commit; checker trước lượt đạt.
- Publish: commit/push lên `origin/main` sẽ là baseline handoff mới của source hiện tại; xác nhận sau push bằng `git status` và `git rev-list`.
- Giới hạn: chưa diễn tập backup/restore, chưa xác minh production hoặc khôi phục hai commit ID cũ không tồn tại.
- Next: OPS-001.

## CHG-20261028-001 — AI handoff và workflow nghiệp vụ

- Phạm vi: tạo `AGENTS.md`, trạng thái dự án, quy trình bàn giao, workflow nghiệp vụ, changelog và checker local.
- Đã thay đổi: mọi phiên AI có thứ tự đọc bắt buộc; mỗi phiên code phải cập nhật status/changelog; state/role/transition của các phân hệ được phân biệt giữa thiết kế và đã triển khai.
- Kiểm chứng trạng thái: local hiện có baseline `82e9ea27`/`a25a0182`; bổ sung DEC-010 để phiên sau không thực hiện lại phục hồi Git theo ghi chú cũ. Không sửa metadata hoặc tạo commit trong lượt này.
- Kiểm thử: checker unit test 11/11 đạt; Ruff đạt; `git diff --check` đạt; kiểm tra `start`/`finish`/`check` đạt.
- Giới hạn: checker không thay thế Git, review nghiệp vụ, security test hoặc phê duyệt của người dùng.
- Next: xử lý Git baseline, rồi chốt state/role matrix cho TP Projects và TP Contracts.

## 2026-10-28 — Foundation và naming

- **Phạm vi:** Odoo foundation, project access, API v1, React workspace, naming TANPHAT ONE, chín tên phân hệ.
- **Đã có:** `tp_core`, `tp_organization`, `tp_project`, `tp_api`, `tp_planning_api`; frontend đọc project theo session Odoo.
- **Kiểm thử:** Odoo 10 tests đạt; OpenAPI live đạt; frontend typecheck/build/unit/prototype/E2E đạt; smoke đạt.
- **Quyết định:** một PostgreSQL database cho mỗi môi trường; quyền dùng company/project/assignment; technical addon identifiers giữ ổn định.
- **Giới hạn:** chưa có contracts, allocations, settlements, import hoặc production; Git metadata cần baseline sạch.
- **Next:** chốt state/role matrix và triển khai `tp_contract` read vertical slice.

## Mẫu mục nhập

```text
## CHG-YYYYMMDD-NNN — <tên thay đổi>
- Phạm vi:
- Đã thay đổi:
- Workflow/model/API bị ảnh hưởng:
- Kiểm thử:
- Giới hạn:
- Next:
```
