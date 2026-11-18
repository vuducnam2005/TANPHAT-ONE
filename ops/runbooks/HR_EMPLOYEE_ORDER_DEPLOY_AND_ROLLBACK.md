# HR-EMPLOYEE-ORDER / AUTH-SESSION-001 — giao bản và khôi phục

Cập nhật 18/11/2026. Đây là hướng dẫn vận hành, không xác nhận đã chạy deploy hoặc nghiệm thu nghiệp vụ.

## Gói triển khai

Chỉ giao slice đã commit, theo danh sách file và checksum do phiên điều phối bàn giao:

| Addon | Phiên bản đích |
| --- | --- |
| `tp_hr_workspace` | `20.0.1.13.0` |
| `tp_admin_delegation` | `20.0.2.0.1` |
| `tp_web_login` | `20.0.2.0.1` |

Không đóng gói toàn bộ working tree đang có WIP của hạng mục khác; giữ nguyên những thay đổi đó. Ghi commit SHA, đường dẫn file, SHA256 của gói và phiên bản thực chạy vào biên bản giao bản. Không đưa credential, dump hoặc filestore vào Git.

Local hiện chạy nguồn cô lập tại `.local/auth-hr-finish/candidate-20261118T155325/custom_addons`, qua `runtime.conf`, cùng database của `18069`. Đây là staging source, không phải database test riêng: không chạy fixture hoặc thử ghi giả tại đây. Trước khi chuyển nguồn, đối chiếu gói đã commit và checksum; không trỏ runtime về toàn bộ source WIP. Không bắt buộc qua `18079`, không tạo/xóa database test.

PC server: checkout `C:/Projects/TANPHAT-ONE`, container `tp-odoo`, network `tanphat-one_default`. Dùng cấu hình, database và volume thực tế đã kiểm chứng trên môi trường đó; không tự suy đường dẫn host/container từ cấu hình local. Giữ tunnel đang chạy, không restart tunnel.

## Trình tự áp dụng

1. Kiểm nguồn/version đang chạy, health và snapshot chỉ đọc dữ liệu/quyền cần bảo toàn. Đối chiếu gói đúng scope; bảo toàn source WIP và cấu hình hiện có.
2. **Từng môi trường phải có backup riêng trước upgrade:** database, filestore cùng database, source/config đang chạy. Ghi thời gian, vị trí, SHA256, kiểm danh mục dump/archive đọc được và phương án phục hồi; giữ secret ngoài Git. Không dùng backup local thay backup server.
3. Triển khai chính các file đã commit, kiểm checksum sau chép. Dừng worker ứng dụng theo cách vận hành hiện có để không có hai runtime phục vụ cùng DB trong lúc upgrade. Giữ PostgreSQL và tunnel theo cấu hình đang dùng.
4. Chạy Odoo bằng executable/config/database của chính môi trường, chỉ nâng ba addon: `-u tp_hr_workspace,tp_admin_delegation,tp_web_login --stop-after-init`. Không `-u all`, không seed actor/password và không chạy suite sinh fixture trên DB đang dùng. Kiểm exit code và log; lỗi upgrade thì chưa mở phục vụ.
5. Khởi động đúng runtime đã giao, kiểm phiên bản ba addon và health. Đối chiếu snapshot: nhân sự/phòng/chức vụ/mã/tài khoản/nhóm quyền, dữ liệu thiết bị/chấm công và `web.base.url`. Migration thứ tự có thể đổi `sequence` theo thiết kế nhưng phải giữ thứ tự hiển thị hiện có và trường nghiệp vụ khác.
6. Kiểm assets/XML/OWL và URL public bằng đọc không phá dữ liệu. Dùng browser mock cho kéo thả/lỗi/RPC âm; không tự tạo fixture hoặc đổi thứ tự nhân viên thật để smoke. Với đăng nhập mới thay phiên cũ, không đăng nhập tài khoản thật chỉ để kiểm rồi đá phiên người dùng. Chỉ kiểm bằng actor/phương thức đã được người dùng cho phép rõ ràng.
7. Ghi commit, checksum, version runtime, backup, lệnh/kết quả thực chạy và phần `NOT_RUN` trong bàn giao; tách technical acceptance, business acceptance và pilot authorization. Lỗi thì sửa gói hoặc thực hiện rollback đã đánh giá bên dưới.

## Rollback

- Ghi lỗi, thời điểm và các ghi mới từ sau backup; tạm dừng phục vụ nếu cần tránh ghi tiếp. Giữ bản source/config và backup hiện tại trước khôi phục.
- Không coi checkout commit cũ rồi restart là rollback đầy đủ: HR thêm trường `sequence`, public employee SQL view và migration khởi tạo thứ tự; AUTH thay session policy/token. Phải kiểm tương thích source/schema/view và session của phiên bản đích trước khi hạ nguồn. Không tự xóa cột hoặc tái tạo view theo phỏng đoán; chuẩn bị migration sửa tiến hoặc kế hoạch hạ tương thích cụ thể.
- Ưu tiên sửa tiến hoặc khôi phục gói source đã biết tương thích với DB hiện tại. Chỉ upgrade lại đúng addon cần thiết theo kế hoạch đã kiểm chứng; không chạy migration khởi tạo thứ tự lặp để che lỗi.
- **Không restore DB cũ một cách máy móc.** Full restore chỉ sau khi đánh giá rõ dữ liệu phát sinh sau backup sẽ mất gì, cách bảo toàn/đối soát và quyết định khôi phục phù hợp quyền người dùng đã giao. DB và filestore phải cùng snapshot nhất quán; giữ bản hiện trạng trước restore. Không restore test đè main/server.
- Sau khôi phục, kiểm health, version/schema/view, dữ liệu/quyền và URL public; đánh giá phiên AUTH cũ có cần đăng nhập lại theo policy. Không nới DEC-054 hoặc tắt kiểm session để qua smoke. Ghi rõ trạng thái khôi phục và giới hạn còn lại.

## Tài liệu đối chiếu

- [HR acceptance](../../docs/demo/HR_EMPLOYEE_ORDER_ACCEPTANCE.md), [HR user guide](../../docs/demo/HR_EMPLOYEE_ORDER_USER_GUIDE.md).
- [AUTH policy](../../docs/security/AUTH_SESSION_001_POLICY.md), [AUTH acceptance](../../docs/demo/AUTH_SESSION_001_ACCEPTANCE.md), [AUTH user guide](../../docs/demo/AUTH_SESSION_001_USER_GUIDE.md).
- [Continuous delivery](../../docs/operations/TP_CONTINUOUS_DELIVERY_POLICY.md).

Nếu acceptance lịch sử còn ghi upgrade hai addon hoặc ca ghi trên dữ liệu thật, dùng scope ba addon và giới hạn kiểm an toàn của gói bàn giao hiện tại; sửa trạng thái evidence theo kết quả thực tế, không suy PASS từ kế hoạch.
