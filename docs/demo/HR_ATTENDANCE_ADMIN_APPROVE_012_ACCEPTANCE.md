# HR-ATTENDANCE-ADMIN-APPROVE-012 — Nghiệm thu kỹ thuật: admin được ủy quyền duyệt điều chỉnh công

- Mã thay đổi: `CHG-20261119-012` / addon `tp_hr_attendance` `20.0.3.2.0 → 20.0.3.3.0` (Python/view/ACL/JS + migration, **cần** `-u tp_hr_attendance`). Quyết định: [DEC-061](../DECISIONS.md), sửa [DEC-060](../DECISIONS.md) ở phần người duyệt.
- Yêu cầu: “quyền admin là toàn quyền chừ việc tự bổ nhiệm quyền admin cho người khác thôi”. Admin được ủy quyền (Full Admin có grant đang hiệu lực trong `tp_admin_delegation`) nhận và Duyệt/Trả lại đề nghị điều chỉnh công như Admin chính. Chỉ việc cấp/thu hồi quyền admin vẫn thuộc riêng Admin chính (DEC-054).
- Môi trường kiểm: snapshot cách ly `.local/admin-approve012/snapshot` + DB kiểm thử `tp_tanphat_test`, chỉ dữ liệu giả (`Synthetic ADM012 Persist Co`, người dùng `adm012.persist.*`, mật khẩu ngẫu nhiên không in ra). Không duyệt phiếu thật của nhân viên.

## Kết quả kiểm tra kỹ thuật

| Tiêu chí | Bằng chứng | Kết quả |
| --- | --- | --- |
| Người duyệt = Admin chính + admin ủy quyền đang hiệu lực ở đúng công ty | `correction_admins` / `require_correction_admin`: `_tp_is_original_admin()` hoặc `_tp_has_live_admin_grant(company)` (đọc sổ ủy quyền bằng SQL, không phụ thuộc công ty đang chọn); không hardcode login/UID; thiếu `tp_admin_delegation` thì fail closed | PASS |
| Grant theo công ty | `test_admin012_delegate_returns_own_blocked_and_revoke_is_immediate`: grant ở công ty A không cho duyệt phiếu công ty B | PASS |
| HR manager / trưởng phòng / người được phân công không có grant thì không duyệt | `test_at03c_roles_never_approve_only_admins`; kiểm lưu thật: chủ phiếu, HR manager, trưởng phòng bị từ chối trên `ĐC00062` | PASS |
| Admin ủy quyền duyệt bằng luồng hiện có | Wizard → “Đã duyệt ĐC00062 và lưu giờ vào/ra vào bảng công.”; tiến trình mới đọc DB: `approved`, ngày `08:00–17:00`, phiên nguồn `correction`, giờ gốc `07:37–17:05 (Nhập từ báo cáo máy)` giữ trong lịch sử | PASS |
| Admin ủy quyền trả lại, lý do bắt buộc | HTTP: trả lại không lý do bị từ chối; có lý do → “Đã trả lại ĐC00063 cho người đề nghị bổ sung.” | PASS |
| Không tự duyệt, không người thay thế | Phiếu của chính admin ủy quyền chỉ chuyển cho Admin chính; tự duyệt bị từ chối. Công ty không có admin nào khác → Gửi duyệt bị chặn, phiếu giữ nháp | PASS |
| Chặn duyệt hai lần | Admin chính duyệt lại phiếu admin ủy quyền đã duyệt: “Phiếu không còn chờ duyệt (đã được xử lý trước đó).” | PASS |
| Thu hồi có hiệu lực ngay | Thu hồi grant: sổ ủy quyền `revoked`, mất `base.group_system`, phiên web cũ bị kết thúc, danh sách người nhận chỉ còn Admin chính. Đăng nhập lại sau thu hồi (`persist_check012b.py`, `ĐC00064`): search rỗng; read, mở duyệt, duyệt, trả lại, xác nhận wizard đều `AccessError`; Admin chính duyệt được | PASS |
| Bền vững qua khởi động lại / đăng nhập lại | `persist_check012.py` 17/17: commit → tiến trình mới (registry mới) → HTTP server mới + đăng nhập lại; chủ phiếu đọc lại trạng thái, người xử lý, thời điểm | PASS |
| Excel nhập sau không ghi đè, không tính lại đi muộn | Nhập lại `07:50–17:20`: ngày vẫn `08:00–17:00`; đi muộn giữ `1 lần / 7 phút` | PASS |
| Lịch sử | Log `correction_create`, `correction_submit`, `correction_approve`; Yêu cầu của tôi hiện người xử lý, thời điểm, nhận xét | PASS |
| Kỳ đã chốt | `test_at06d_lock_amendment_and_reopen_require_reason`: vẫn cần phân công chốt (`can_lock`) và lý do đính chính | PASS |
| Giao diện admin ủy quyền | Playwright 2 lượt (`ui_check012.py`): menu `Xử lý điều chỉnh` có trong menu của admin ủy quyền; dòng có giờ hiện tại/đề nghị, nút **Duyệt**/**Trả lại**; Duyệt `ĐC00065`/`ĐC00080`, Trả lại `ĐC00066`/`ĐC00081` (trả lại trống lý do bị chặn); DB đọc lại khớp | PASS |
| Chủ phiếu | Không có menu `Xử lý điều chỉnh`, 0 nút Duyệt/Trả lại; Yêu cầu của tôi hiện `Đã duyệt`/`Trả lại`, người xử lý `adm012.persist.delegate` và lý do | PASS |
| Ô Minh chứng trống | Trước: cột Minh chứng in chữ `false` khi không có tệp (lỗi hiển thị từ bản 005). Sau: ô trống, phiếu có tệp hiện tên tệp và nút tải | PASS |
| Không lỗi trình duyệt | 0 `console.error`, 0 `pageerror`, 0 HTTP 5xx | PASS |
| Bộ test addon | `TestAttendanceCorrection` 11/11. Bộ `/tp_hr_attendance` chỉ còn các lỗi trùng baseline HEAD (`test_access` ×1, `test_directory_privacy` ×1, `test_matrix_compare` ×4, `test_upload` ×2). Ruff đạt cho các tệp đã sửa | PASS (phạm vi) |

## Ảnh và biên bản

- `.local/admin-approve012/ui/ui2/queue-delegate.png`: hàng đợi của admin ủy quyền (ô Minh chứng trống / có tệp).
- `.local/admin-approve012/ui/ui2/wizard-approve-delegate.png`, `my-requests-delegate.png`.
- `.local/admin-approve012/persist-receipt.json`, `persist-receipt-b.json`, `ui-receipt.json`, `ui-receipt-ui2.json`: biên bản máy (không chứa mật khẩu).

## Giới hạn còn lại

- DB kiểm thử `tp_tanphat_test` dùng chung với phiên khác; kiểm cuối chạy ngay sau `-u` lên `20.0.3.3.0` (đã kiểm phiên bản module và không còn dòng ACL cũ).
- Main local và PC server không có phiếu điều chỉnh thật; không tạo phiếu giả ở đó, nên kiểm sau giao bản chỉ đọc (danh sách admin nhận duyệt, menu, version, bundle).
