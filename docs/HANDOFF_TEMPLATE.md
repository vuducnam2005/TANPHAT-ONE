# Mẫu bàn giao một phiên AI

Copy nội dung cần thiết vào `PROJECT_STATUS.md` và một mục mới trong `CHANGELOG.md`; không tạo thêm bản status cạnh tranh cho mỗi phiên.

```markdown
## CHG-YYYYMMDD-NNN — Tên việc

- Ngày/giờ: ISO 8601 với timezone; ID duy nhất trong ngày.
- Mục tiêu người dùng:
- Task ID: tham chiếu ROADMAP, hoặc nêu việc mới phát sinh.
- Đã thay đổi: đường dẫn file + hành vi trước/sau.
- Nghiệp vụ/quyền/API/schema bị ảnh hưởng:
- Quyết định: DEC-ID; ghi đã xác nhận hay mới đề xuất.
- Kiểm tra thực chạy: lệnh + kết quả; nếu không chạy nêu lý do.
- Còn thiếu/blocker: điều kiện cụ thể và tác động.
- Next action: một bước khả thi, có đầu vào và tiêu chí xong.
```

`PROJECT_STATUS.md` phải có dòng đơn (không in đậm):

```text
Last change: `CHG-YYYYMMDD-NNN`
```

Khi bị ngắt giữa chừng, phiên sau dùng checkpoint đang có, ghi những gì thực tế còn dở và chạy lại kiểm tra liên quan. Không ghi “đã xong” hoặc “test đạt” dựa trên kế hoạch.

Gợi ý mở chat mới:

> Làm việc trong `C:\TANPHAT ONE`. Đọc `AGENTS.md`, `docs/PROJECT_STATUS.md`, `docs/CHANGELOG.md`, `docs/ROADMAP.md` và `docs/DECISIONS.md` trước. Tiếp tục Next action phù hợp với yêu cầu hiện tại. Mỗi lần sửa code phải cập nhật bàn giao và chạy checker theo `docs/AI_CHANGE_WORKFLOW.md`.
