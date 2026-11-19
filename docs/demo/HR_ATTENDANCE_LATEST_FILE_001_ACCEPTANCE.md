# HR-ATTENDANCE-LATEST-FILE-001 — nghiệm thu kỹ thuật

CHG-20261119-001, addon20.0.3.1.0, nguồn: yêu cầu19/11 và steering tiếp theo.
DEC-059 thay luồng đối chiếu thủ công DEC-058 ở lối upload chính.

| Tiêu chí | Bằng chứng |
| --- | --- |
| Bỏ menu/nút cũ; link bang-cong mở matrix cho importer; Back về overview | Authenticated Chromium1440/390 PASS; viewer fallback giữ quyền cũ |
| Giờ thiếu rõ vào/ra, thời gian xanh/cam, reviewđỏ, nút chi tiết và mobile | 2/2 browser cases PASS,0JSerror; label helper5/5 |
| File mới thay giờ ngày có trong file, không doublecount, idempotent và chống replay nguồn cũ | ORM synthetic TestLatestFile PASS |
| Blank trong file mới gỡ giờ import cũ; ngày ngoài file giữ | ORM PASS; không suy nghỉ |
| Nhiều file theo thứ tự server, file lỗi không mất file tốt | ORM PASS, savepoint/file + companylock |
| Kỳ chốt/giờ lỗi không thay, viewer không import | ORM PASS; approved correction/API guards có source review, chưa fixture riêng cho hai loại này |
| Tổng muộn nguồn thay đúng kỳ, unique applied index | ORM PASS sau flush state nguồn cũ |
| Menu viewer/manager | ORM PASS |
| Cuộn overview/toolbar/sidebar không lộ trắng | 12/12 viewport-modePASS |
| Python/XML/ruff/node | PASS |
| Main backup/upgrade | dump+restore-list+filestore;39employee/28user/7batch/299session/365day,groupdigest giữ |

Scriptbrowser `scripts/tests/test_hr_attendance_latest_ui.cjs` chỉ đọc, nhận session
private qua TP_ATT_STORAGE_STATE; TP_ATT_REVIEW_DATE chọn ngày có case giờ thiếu.
Không upload/filefake trênmain. ORM chỉ chạy DBtest hiện có. Sourcehash và workflow
đúng committedsnapshot; checkpoint/foreignWIP giữ nguyên. Test filestoreGC có warning
Windowspermission; kết quả6/6PASS, không can thiệp các attachment đó.

PCserver đang chờ giao bản và kiểm actual JS/CSS. Không coi assets/login là public
authenticatedE2E. Chưa kiểm iOS/Safari thật, race thực, fixture riêng approved/API
hoặc nghiệp vụ/UAT; không tự replay batch thật cũ. Nguồn lịch sử giữ nguyên.
