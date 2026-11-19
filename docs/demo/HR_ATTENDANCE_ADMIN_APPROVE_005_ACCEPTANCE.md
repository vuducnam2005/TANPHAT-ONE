# HR-ATTENDANCE-ADMIN-APPROVE-005 — Nghiệm thu kỹ thuật: Admin chính duyệt điều chỉnh công

- Mã thay đổi: `CHG-20261119-005` (local verified) / addon `tp_hr_attendance` `20.0.3.1.0 → 20.0.3.2.0` (đổi view/menu/ACL + migration, **cần** `-u tp_hr_attendance`). Quyết định: [DEC-060](../DECISIONS.md).
- Phạm vi: mọi đề nghị điều chỉnh công (`tp.hr.attendance.correction`) của mọi phòng ban chỉ chuyển đến và chỉ được Duyệt/Trả lại bởi **Admin chính (admin gốc)** xác định bằng `res.users._tp_is_original_admin()` của `tp_admin_delegation`. Không hardcode login/UID.
- Môi trường kiểm: snapshot cách ly `.local/admin-approve005/snapshot` + DB kiểm thử `tp_tanphat_test`, chỉ dữ liệu giả (`Synthetic ADM005 Persist Co`, người dùng `adm005.persist.*`, mật khẩu ngẫu nhiên chỉ qua biến môi trường). Không duyệt phiếu thật của nhân viên.

## Kết quả kiểm tra kỹ thuật

| Tiêu chí | Bằng chứng | Kết quả |
| --- | --- | --- |
| Người duyệt = Admin chính theo `tp_admin_delegation` | `require_original_admin` → `_tp_is_original_admin()` (nhóm `group_original_admin`, quyền hệ thống, không grant ủy quyền hiệu lực); tra cứu mềm `env.ref(..., raise_if_not_found=False)`, thiếu module thì fail closed | PASS |
| Admin ủy quyền / HR manager / trưởng phòng / phân công không duyệt được | `test_at03c_roles_never_approve_only_original_admin`; kiểm lưu thật: chủ phiếu, HR manager, trưởng phòng đều bị từ chối trên `ĐC00037` | PASS |
| Kiểm ở backend, không chỉ ẩn nút | Duyệt, Trả lại, mở wizard, xác nhận wizard đều qua `_tp_check_reviewer`; menu `Xử lý điều chỉnh` và `tp_can_review` dùng cùng kiểm tra (`test_admin005_menu_follows_original_admin`) | PASS |
| Không người duyệt thay thế | `test_admin005_no_original_admin_means_no_submit_and_no_substitute`: công ty không có Admin chính → Gửi duyệt báo lỗi, phiếu giữ nháp | PASS |
| Luồng nhân viên | Lưu nháp không đổi bảng công; Gửi duyệt → **Chờ admin duyệt**; bị trả → sửa và gửi lại (`test_at06b_own_only_draft_return_and_resubmit`); ghi `state` và tạo phiên qua JSON-RPC bị từ chối (kiểm HTTP) | PASS |
| Không tự duyệt, chặn duyệt hai lần / đồng thời | `test_at06c_self_approval_retry_and_preserved_punch`; khóa `FOR UPDATE` + advisory lock; duyệt lần hai qua HTTP: “Phiếu không còn chờ duyệt (đã được xử lý trước đó).” | PASS |
| Màn admin toàn công ty | Playwright: cột Mã phiếu, Mã TP, Người đề nghị, Phòng, Ngày công, Giờ vào/ra đang ghi, Giờ vào/ra đúng, Giải trình, Minh chứng, Trạng thái, Người xử lý, Thao tác; dòng `ĐC00038` đủ `07:45–17:10` → `8:00–17:00`, nút **Duyệt**/**Trả lại** | PASS |
| Trả lại bắt buộc lý do | Playwright: xác nhận Trả lại không lý do → trường lý do báo lỗi, hộp thoại giữ nguyên; có lý do → “Đã trả lại ĐC00039 cho người đề nghị bổ sung.” | PASS |
| Duyệt ghi dữ liệu thật, tái sử dụng `action_approve` | Wizard → “Đã duyệt ĐC00038 và lưu giờ vào/ra vào bảng công.”; shell mới đọc DB: `approved`, ngày `08:00–17:00`, phiên nguồn `correction` | PASS |
| Báo thành công sau khi lưu, lỗi thì rollback | `test_admin005_failed_approval_rolls_back_everything` (chèn lỗi sau refresh: phiếu vẫn chờ, giờ không đổi, không phiên mới) | PASS |
| Bền vững qua tải lại / đăng nhập lại / khởi động lại | `persist_check.py`: commit → tiến trình mới (registry mới) → HTTP server mới + đăng nhập lại: `ĐC00037` Đã duyệt, người duyệt, thời điểm gửi/xử lý, giờ gốc `07:37–17:05 (Nhập từ báo cáo máy)` | PASS |
| Công của tôi / Bảng công / Tổng quan cùng đọc | Sau khởi động lại: `tp_mine` `08:00–17:00 approved`, bảng công `08:00–17:00`, Tổng quan đạt; chủ phiếu đọc lại qua HTTP | PASS |
| Excel nhập sau không ghi đè | Nhập tệp thứ hai `07:50–17:20` cùng ngày: ngày vẫn `08:00–17:00`, phiên `correction` giữ hiệu lực | PASS |
| Không tính lại đi muộn tổng kỳ | Đi muộn giữ `1 lần / 7 phút` theo tệp trước/sau duyệt và sau nhập lại | PASS |
| Lịch sử | Log `correction_create`, `correction_submit`, `correction_approve`; phiên cũ `superseded_by_id`; Yêu cầu của tôi hiện người xử lý, thời điểm, nhận xét | PASS |
| Kỳ đã chốt | `test_at06d_lock_amendment_and_reopen_require_reason`: Admin chính cần thêm phân công chốt (`can_lock`) và lý do đính chính | PASS |
| Chủ phiếu không thấy nút xử lý | Playwright: chủ phiếu mở `action_review` → 0 nút Duyệt/Trả lại | PASS |
| Không lỗi trình duyệt | 0 `console.error`, 0 `pageerror`, 0 HTTP 5xx trong toàn bộ phiên Playwright | PASS |
| Bộ test addon | `/tp_hr_attendance` 71 test; `TestAttendanceCorrection` 10/10. 8 lỗi còn lại trùng baseline HEAD (`test_access` ×1, `test_directory_privacy` ×1, `test_matrix_compare` ×4, `test_upload` ×2) | PASS (phạm vi) |

## Ảnh và biên bản

- `.local/admin-approve005/ui/queue-desktop.png`: hàng đợi Xử lý điều chỉnh (1440×900).
- `.local/admin-approve005/ui/wizard-approve.png`: hộp thoại xác nhận duyệt.
- `.local/admin-approve005/ui/my-requests.png`: Yêu cầu của tôi sau xử lý.
- `.local/admin-approve005/persist-receipt.json`, `ui-receipt.json`, `ui/ui-results.json`: biên bản máy (không chứa mật khẩu).

## Giới hạn còn lại

- DB chính local và PC server hiện không có phiếu điều chỉnh thật; không tạo phiếu giả ở đó, nên kiểm trên server chỉ đọc (menu theo Admin chính, số phiếu chờ, version).
- Chưa kiểm trên thiết bị iOS/Safari thật. Nghiệm thu nghiệp vụ thuộc quyền người dùng khi có phiếu thật đầu tiên.
