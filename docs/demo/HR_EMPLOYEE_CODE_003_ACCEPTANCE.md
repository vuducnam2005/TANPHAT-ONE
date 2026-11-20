# HR-EMPLOYEE-CODE-003 — Nghiệm thu mã nhân viên TP + 3 chữ số

Phạm vi: `tp_organization` 20.0.2.3.0, `tp_hr_attendance` 20.0.3.5.5.
[Runbook áp và hoàn nguyên](../../ops/runbooks/HR_EMPLOYEE_CODE_003_DEPLOY_AND_ROLLBACK.md).
Bảng mapping có dữ liệu nhân viên thật chỉ nằm trong thư mục backup trên PC, không
có trong Git.

## 1. Quy tắc

| Trường hợp | Kết quả |
| --- | --- |
| TP10001 / TP10009 / TP10060 / TP10065 / TP10125 | TP001 / TP009 / TP060 / TP065 / TP125 |
| Đã là TP001–TP999 | Giữ nguyên |
| TP11000, TP20000, TP1, TP0001, thiếu mã, trùng sau khi chuyển | Xung đột: báo ID + mã + lý do, không ghi |
| Số thuộc hồ sơ đã xóa hoặc đã đổi mã (cả hai dạng) | Xung đột, không cấp lại |
| Mã nguồn không ra đúng mã mới | Xung đột |
| Hết dải TP999 | Báo lỗi và dừng, không sinh TP1000 |

Mã ENTI (`maNV`, `keyNV`) và mapping ENTI → nhân viên giữ nguyên. Khi ENTI có mã
`TP032` còn nội bộ có `TP032` của người khác, hệ thống không ghép theo mã. Chỉ dùng
`keyNV`, mapping đã xác nhận, hoặc họ tên duy nhất. Tên trùng thì để gợi ý và chờ
người xác nhận.

## 2. Kiểm tự động (local `tp_tanphat_test`, dữ liệu giả)

| Kiểm | Test |
| --- | --- |
| 5 ví dụ, alias hai dạng, giá trị không chuyển | `test_code_format_rule` |
| Chuyển giữ ID, tên, phòng, quản lý, user, mật khẩu, lưu trữ; audit + chatter; chạy lại không đổi | `test_conversion_keeps_identity_links_and_is_idempotent` |
| Xung đột (trùng, ngoài dải, thiếu, đã xóa, mã nguồn lệch) báo và không ghi | `test_conversion_reports_conflicts_without_writing` |
| Nhập lại sau chuyển giữ mã mới, không tạo trùng; mã nguồn 1060 bị chặn | `test_reimport_after_conversion_keeps_new_code` |
| Cấp tiếp số cao nhất; bỏ qua mã đã lưu trữ/xóa (cả dạng cũ); không dùng lại số đã rollback | `test_next_code_*`, `test_archived_*`, `test_code_deleted_under_former_form_stays_retired`, `test_rolled_back_*` |
| Hết dải dừng, không TP1000 | `test_band_end_stops_and_out_of_rule_codes`, `test_source_above_band_is_a_conflict` |
| Chỉ correction nội bộ đổi được mã | `test_code_change_only_through_internal_correction` |
| Bản sao mã ở ngày công/đề nghị được làm mới; giờ, công, kỳ khóa giữ nguyên; đồng bộ lại không trùng, không quay về mã cũ | `test_code_conversion_refreshes_attendance_copies_only` |
| Mã ENTI không chọn một trong hai người cùng tên | `test_enti_code_never_picks_one_of_same_name_employees` |

Chạy `/tp_organization,/tp_hr_attendance,/tp_hr_workspace` trên bản commit
`13fc1283` (ghi log UTF-8): 225 test, mọi test CODE-003 đạt, 9 fail + 3 error. Cả
12 lỗi này cũng lỗi trên `befbee7f` (trước thay đổi), không thuộc phạm vi tác vụ:

- `TestEmployeeCorrection`: `test_batch_rolls_back_mid_process`,
  `test_independent_links_block_with_resolution_hint`,
  `test_permanent_delete_removes_profile_and_owned_rows` (guard
  `tp_admin_delegation`; chạy chung bộ có lúc ra SerializationFailure);
- `TestEmployeeDeleteHttp`: `test_account_kept_by_default_or_locked_on_request`,
  `test_native_login_throttle_applies`,
  `test_other_users_companies_and_forged_flags_are_denied`,
  `test_password_checked_on_every_request_and_retry_is_idempotent`,
  `test_stale_preview_and_blockers_delete_nothing`;
- `TestEmployeeLoginRename.test_rename_preserves_identity_password_permissions_and_export`;
- `TestEmployeeLoginRenameHttp.test_browser_dialog_validation_save_reload_and_mobile`
  và `TestUnifiedReadonlyBrowserHttp.test_browser_admin_vs_employee_parity_and_hidden_tabs_desktop_mobile`
  (`odoo.define is not a function`);
- `TestDashboardLock.test_job_filter_quality_catalog_export` (ô A2 không có tên
  chức danh).

## 3. PC server (`tp_tanphat_dev`, https://tpone.tadic.vn)

Áp 20/11/2026 15:00 giờ VN, commit `13fc1283`. Trước khi áp đã xác minh: DB duy nhất
`tp_tanphat_dev`, container `tp-odoo` (dbfilter `^tp_tanphat_dev$`), nguồn khớp
`befbee7f`, phiên bản module khớp. Chỉ ghi số lượng, không ghi tên.

| Kiểm | Kết quả |
| --- | --- |
| Precheck chỉ đọc | 40 hồ sơ (39 đang dùng, 1 lưu trữ, 1 công ty), số 1–72, 0 trùng sau chuyển, 0 ngoài quy tắc, 0 thiếu; số đã thu hồi (TP10070, TP10071, TP20000) không ai giữ |
| Upgrade | exit 0, log 0 ERROR, nguồn 101/101 khớp release |
| Chuyển mã | 40/40; dạng mã trước 0 mới/40 cũ, sau 40 mới/0 cũ; 0 trùng |
| Ví dụ | TP001, TP009, TP060, TP065 có người giữ; TP125 chưa có (số cao nhất 72) |
| Chạy lại kế hoạch | 40/40 `keep`, không đổi gì |
| Mã cấp tiếp | TP073 (sequence 73; TP070/TP071 của hồ sơ đã xóa không cấp lại) |
| Giữ nguyên | ID/danh tính 40 hồ sơ, 32 tài khoản (login + hash mật khẩu), 109 liên kết quyền, roster, version, 780 ngày công, 793 phiên, kỳ/đề nghị, ENTI mapping 39, cron, khóa ngoại tới hồ sơ |
| Audit | 32 dòng cũ khớp md5; thêm 40 `code_correction`, mỗi dòng cũ − 10000 = mới |
| Thông báo | 40 ghi chú chatter nội bộ không người nhận; hàng đợi mail 82 → 82, thông báo 0 → 0 |
| Bản sao mã chấm công | Ngày công/đề nghị lệch 0 trước và sau |
| Chu kỳ ENTI sau khởi động lại | Xong 15:05, 39 người từ ENTI; mapping không đổi, 0 ngày trùng, 0 mã cũ, 0 ERROR log |
| Quét mã cũ trong DB | Chỉ còn ở audit, chatter và preview wizard tạm (lịch sử, giữ nguyên) |
| Dữ liệu màn hình (ORM, chỉ đọc) | Danh sách 40/40 mã mới; tổng quan ngày, bảng công tháng, công của một người, Công của tôi, Hồ sơ của tôi: 0 mã cũ |
| Tìm kiếm | “Mã hoặc tên” và tìm chấm công: TP060 → 1, TP10060 → 0 |
| Excel mới | HR 40 mã mới / 0 cũ; Bảng chấm công 39 mã mới / 0 cũ |

Backup `C:\TANPHAT-backups\hr-employee-code003\code003-20261120T150009`: dump +
restore-list, filestore, source, config, snapshot trước/sau, log upgrade, mapping
đã áp và danh sách ID sau áp (riêng tư), SHA256.

Script áp dừng ở key `audit_history`. Phép kiểm lấy các dòng audit cũ hơn 1 phút
tại thời điểm chụp, nên snapshot sau tính cả 40 dòng mới. Lịch sử cũ đã đối chiếu
riêng và khớp; script nay so đúng các dòng có trước khi áp.

Chưa xem giao diện bằng trình duyệt đã đăng nhập, vì pane chưa đăng nhập. Dữ liệu
màn hình đã kiểm phía server như bảng trên.
