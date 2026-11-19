# Hồ sơ HR responsive và tìm tên trực tiếp

Task HR-PROFILE-RESPONSIVE-UI-001 + LIVE-NAME-SEARCH, CHG-20261119-020; 19/11/2026.

Người dùng giao thực thi “làm đi” sau khi chốt prompt. Reference gồm yêu cầu hồ sơ thiết kế và ảnh thanh tìm kiếm. Mục tiêu là bố cục đọc được trên mọi tab và gợi ý/lọc tên ngay khi gõ N → Na → Nam. Technical verification tách nghiệm thu hình thức/nghiệp vụ của người dùng.

## Hành vi

Danh sách nhân viên bỏ search lớn; giữ hàng lọc, native Lọc/Nhóm/Ưa thích, facets và xuất Excel. Ô Họ tên tự tìm sau250ms, gợi ý15người đầu cùng mã TP và cách xem toàn bộ kết quả trong bảng. ORM tìm toàn population hợp lệ, áp action domain/company/context/ACL/record rule; không sudo, không tải hồ sơ riêng tư. Chọn dùng ID; sửa chữ bỏ ID; xóa chữ chỉ gỡ tên. Không tự áp các tiêu chí khác còn pending. Async stale responses và Vietnamese composition được kiểm.

Chỉnh SCSS nguồn hiện có: navy#172b4d, nhãn#475569, value15px, heading18px, tên23–26px; card tự cao theo nội dung, minmax(0,1fr), container queries theo vùng sau sidebar, nhãn xếp trên giá trị khi hẹp, tabs cuộn riêng, bảng cuộn nội bộ, popup theo viewport/dvh. Giữ action/backend permission, phiên bản hồ sơ và chatter; nút đổi chức vụ gọn với tooltip. Không đổi schema/workflow/API hoặc ghi hồ sơ thật.

File chính: `tp_hr_workspace/static/src/table/live_name_filter.js/xml`, table.js/xml, profile/employee_profile.scss, profile/account_credentials.scss, my_profile/my_profile.scss, views/workspace.xml; `tp_web_home/static/src/search/table_filter_bar.js` hỗ trợ áp riêng criterion; filter_domain.js lưu text hoặc ID gợi ý. Manifest HR20.0.1.17.0/Home20.0.1.9.1. Search bảng khác không bật live mode.

## Kiểm thực

- `node scripts/tests/test_hr_employee_live_filter.cjs`: PASS substring/exactID/pending/applied/mandatorydomain/company/race/clear/error/composition.
- AST/XML/Node syntax, libsass3SCSS và compile7nativeOWL templates: PASS.
- Local upgrade18069 exit0/0ERROR; snapshot hash tài khoản, credential, lock/grant, group/company, roster/resource/sequence và nghiệp vụ giữ; chỉ module version thay đổi. Không18079 hoặc fixturemain.
- Browser Chromium dùng phiên hợp lệ hiện có: PASS9width320/360/390/430/768/1024/1280/1440/1920 ×7tab; live search/noresults/exactselection/pendingdepartment/clear+applieddepartment; edit/cancel tại390x600 và viewport thấp850x480/844x390/390x320; popup tài khoản390x360. Clear-before-debounce/bàn phím/reduced-motion và long-text stress chỉ DOM PASS. HOOT48test243assertion PASS. Ảnh/log chỉ trong ignored `.local/hr-profile-live001/` để giữ dữ liệu nhân viên ngoàiGit.

## Môi trường và backup

Local runtime isolated candidate `.local/hr-profile-live001/main-candidate`; backup `.local/hr-profile-live001/main-backup-20261119T153938`, dump/pg_restore-list/filestore DB-referenced/source/config/SHA256. Không nhận foreign WIP/reporting/branding/sidebar. PCserver/public đang chờ chốt release. Workflow seal snapshot HEAD+scope; giữ checkpoint18/11 của batch khác.

## Giới hạn

Chưa physicaldevice/iOS/Safari; CSSzoom125/150/200 và landscape/thấp PASS; chưa native browser zoom. Chưa kiểm authenticated public bằng người dùng thật, chưa business acceptance. Browser phiên admin gốc; không đổi phiên/quyền để kiểm mọi vai trò. My Profile chỉ kiểm khung vì actor hiện tại chưa liên kết hồ sơ; không tuyên bố full-data tabs đã kiểm. Không fixture trùng tên/nhiều trang trênmain; logic ID và query server đã kiểm cô lập. Browser phiên admin gốc; không đổi phiên/quyền để kiểm mọi vai trò. My Profile chỉ kiểm khung vì actor hiện tại chưa liên kết hồ sơ; không tuyên bố full-data tabs đã kiểm. Không fixture trùng tên/nhiều trang trênmain; logic ID và query server đã kiểm cô lập. Không test ghi/sửa/khóa/reset tài khoản hoặc hồ sơ thật; backend quyền không đổi. Không coi unit/geometry PASS là nghiệm thu thị giác; cần xem ảnh và computedstyles sau transition.
