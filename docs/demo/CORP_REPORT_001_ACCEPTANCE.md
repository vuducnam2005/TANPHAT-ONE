# CORP-REPORT-001 — Acceptance trước triển khai

Ngày 16/11/2026, CHG-20261116-008. Phạm vi: `tp_tanphat_test`, localhost:18079.
Technical verification, phản hồi trực quan, business acceptance và cho phép main là bốn cổng riêng. Main chưa được phép áp.

Baseline: workflow CHG-20261116-007 PASS; không active checkpoint trước lượt này; test HTTP dừng, không phiên DB test khác. Boundary private `.local/corp-report001/boundary-before.json`, patch/status trước sửa. Không có màn Báo cáo cũ; ảnh before là shell hiện hữu, không dựng before giả.

| ID | Actor / tiền điều kiện | Thao tác | Kỳ vọng | Test/evidence | Kết quả |
| --- | --- | --- | --- | --- | --- |
| AT-PLAN-01 | Người lập được giao scope, quý giả | Quý → ba tháng phân bổ không đều → tuần | Đúng cha/company/kỳ/đơn vị; không chia đều; phần chưa phân bổ rõ | Odoo + browser | NOT RUN |
| AT-PLAN-02 | Người ban hành và người lập khác nhau | Trình/ban hành/trả/revision/copy/chuyển tiếp | Baseline giữ; vượt/chu trình/sai parent bị chặn; copy không kéo actual | Odoo + browser | NOT RUN |
| AT-PERIOD-01 | Tuần giao tháng/quý/năm | Phân bổ theo ngày; deadline/gia hạn | Header tuần gốc, mỗi dòng trong tháng cha; không nhân task; Asia/Saigon | Odoo | NOT RUN |
| AT-WORKFLOW-01 | Nhân viên + reviewer giả | Nháp/gửi/rà/trả/sửa/gửi/chốt/revision | Lý do bắt buộc; exact snapshots/template versions bất biến; trực tiếp write/unlink bị chặn | Odoo + browser | NOT RUN |
| AT-WORKFLOW-02 | Hai request/reviewer, stale version | Retry/double click/key khác payload | Một event/snapshot; stale bị từ chối; transaction giữ nguyên khi lỗi | Odoo + HTTP race | NOT RUN |
| AT-ROLLUP-01 | Nhiều người/phòng cùng task | Tổng hợp snapshot cá nhân → phòng → công ty | Dedup source/contribution; dependency exact version; child đổi không sửa parent cũ | Odoo | NOT RUN |
| AT-ROLLUP-02 | Có thiếu/miễn/gia hạn/quá hạn | Theo dõi nghĩa vụ/chốt thiếu | Mẫu số từ nghĩa vụ; exception có quyền/lý do; thiếu bao phủ vẫn hiện | Odoo + browser | NOT RUN |
| AT-MONEY-01 | Supplier/confirmer/viewer riêng | Nhập số có nguồn/xác nhận/overlap/currency/tax | Null khác zero; self-confirm chặn; chưa xác nhận không vào tổng; tách flow/stock/milestone/cumulative | Odoo + export | NOT RUN |
| AT-SECURITY-01 | Self/manager/company/outside/revoked/expired/multicompany | ORM/RPC/read_group/name_search/count/chart/export/deep link | Không lộ cá nhân/nháp/tiền/HR ngoài assignment; không tự rà mình; payload scope không mở quyền | Odoo + HTTP | NOT RUN |
| AT-SECURITY-02 | Snapshot và evidence đã gửi | Thử sửa/xóa/file public/token/download sau revoke | Lịch sử/evidence bất biến; tải kiểm quyền hiện hành; no-store | Odoo + HTTP | NOT RUN |
| AT-UI-01 | >100 dòng, text dài, mọi tab | AND/OR/pending/applied/clear/sort/10-20-50-100/back/dirty | Lọc server trước count/page/export; native favorite đồng bộ; không mất relation draft | Browser + native harness | NOT RUN |
| AT-UI-02 | Mọi list/detail/popup | Desktop 1440/1366, tablet768, mobile390/375 | Không tràn trang/chồng cột; drawer/focus/touch44px; empty/error/retry tách biệt | Screenshots + browser | NOT RUN |
| AT-CHART-01 | Nghĩa vụ/metric hợp lệ và trống | Donut/bar/KPI/drill/keyboard/touch | Chart lớn đầu; tổng loại trừ khớp; cùng unit/scope; không chart giả/NaN; reduced motion | Browser + Odoo | NOT RUN |
| AT-EXPORT-01 | Nháp và snapshot, restricted finance | Xuất Excel/Word/PDF filtered/full/selected | Đúng kỳ/domain/version/quyền; injection guard; nhiều trang/Việt/ngắt trang; không cắt âm thầm | Readback + render | NOT RUN |
| AT-INTEGRATION-01 | HR/project canonical, chuyển phòng | Mở identity/link/nguồn/home | Cùng ID/session/shell; history giữ snapshot; nguồn vẫn kiểm quyền; không write state nguồn | Odoo + browser | NOT RUN |
| AT-OPS-01 | Test canonical đã backup, HTTP dừng | Install/upgrade/rerun/restore rehearsal | Không trùng menu/config/fixture; backup DB/filestore/source/config khớp; main không đổi | Runtime log + fingerprints | NOT RUN |
| AT-OPS-02 | Module trên test | Smoke HR/KH-KD/Kho/Home/login | Không lỗi assets/layout ngoài scope; không credential/grant thật đổi | Browser + fingerprint | NOT RUN |

Default lịch T2–CN, timezone Asia/Saigon và assignment đều là cấu hình thử, chưa là nội quy công ty. Fixture chỉ marker CORP-REPORT-001 trên test; không nhập hai Word thật.

## Addendum cá nhân hoàn toàn trên web — cùng batch/checkpoint

Nguồn: [prompt bổ sung](../prompts/CLAUDE_CORP_REPORT_001_PERSONAL_WEB_ADDENDUM.md), người dùng giao trong khi triển khai. Không khởi tạo lại module/DB. Hai nhân viên, một quản lý, một user ngoài scope đều là fixture test.

| ID | Actor / thao tác | Kỳ vọng | Evidence | Kết quả |
| --- | --- | --- | --- | --- |
| AT-WEB-01 | Nhân viên lập từ kế hoạch → nhập kết quả dài → lưu nháp → mở lại | Đầu ra dự kiến khác thực tế; identity/source đúng; không upload Excel | Odoo + browser | NOT RUN |
| AT-WEB-02 | Gửi báo cáo có/thiếu reviewer | Vào đúng inbox; thiếu reviewer chặn và hướng dẫn; quản lý không đọc nháp riêng | Odoo + browser | NOT RUN |
| AT-WEB-03 | Quản lý nhận xét hai dòng + chung; nhân viên phản hồi | Review riêng actor/version/line; nhân viên không sửa đánh giá bằng RPC/x2many; internal audience tách | Odoo + browser | NOT RUN |
| AT-WEB-04 | Trả một dòng → nhân viên sửa → gửi lại → so sánh → chốt | Lý do/needs-change rõ, old snapshot/comments/actor còn nguyên | Odoo + browser | NOT RUN |
| AT-WEB-05 | Chốt khi một đầu việc đang làm → kỳ sau | Report finalized không làm task done; stable ID và không tăng khống facts/tỷ lệ nộp | Odoo | NOT RUN |
| AT-WEB-06 | Tổng hợp tuần→tháng→quý, tuần giao tháng | Đúng phân kỳ/đơn vị/kế hoạch gốc; missing khác zero; dedup source | Odoo | NOT RUN |
| AT-WEB-07 | Giao chỉ đạo → recipient phản hồi/hoàn thành/retry | Theo dõi actor/hạn/kết quả, không nhân chỉ đạo; in-app notification đúng audience | Odoo + browser | NOT RUN |
| AT-WEB-08 | Xuất ba định dạng với published/internal review | Đúng bản/kỳ/comments công bố; không lộ nội dung nội bộ | Odoo + readback/render | NOT RUN |
| AT-WEB-09 | Hai tab stale/retry/write đánh giá | Không mất dữ liệu/ghi đè review; main/accounts thật giữ | Odoo + HTTP race | NOT RUN |
| AT-WEB-10 | Desktop/mobile cả chuỗi author→review→return→resubmit | Nhập dài/filter/back/dirty/reduced-motion, không chồng; ảnh từng bước | Browser | NOT RUN |
