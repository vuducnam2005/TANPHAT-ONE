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

## 3. PC server (`tp_tanphat_dev`, https://tpone.tadic.vn)

Điền sau khi áp, theo `result.json` và kiểm giao diện.
