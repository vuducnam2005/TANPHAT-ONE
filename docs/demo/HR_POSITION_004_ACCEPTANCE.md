# HR-POSITION-004 — Đổi trong chi tiết và một trưởng phòng mỗi phòng

12/11/2026, CHG-20261112-007. Yêu cầu trực tiếp của người dùng tiếp tục task HR.
Thay entry list của003; không tự thay chức vụ, account hoặc quyền người thật.

## Kết quả sản phẩm

- Danh sách không còn Đổi chức vụ; bấm dòng/tên để mở chi tiết, nút nằm ngay
  dưới tên. Xem tài khoản giữ nguyên; bỏ CSS xếp hai nút để dòng gọn lại.
- Chỉ một HEAD active cho mỗi company/department; preview/apply bổ nhiệm người
  khác báo tên người hiện tại và yêu cầu hạ cấp trước. Hạ cũ → bổ nhiệm mới qua
  workflow hiện có, lý do/preview/scope/revocation/audit, không tự thay thế.
- Extension cùng model role trong addon HR dùng unique index để chặn trực tiếp,
  reactivation và race. Active chưa thu hồi giữ vị trí dù user khóa hoặc ngày
  hiệu lực chưa tới/hết. Chức vụ HR không tự tạo quyền; phòng ngoài KH-KD chưa
  được mở bộ quyền mới. Không thêm model/ACL/React/API/core hoặc role engine.
- Snapshot role thêm HEAD của phòng, cursor mới đọc đúng environment mới.
  Thiết kế trước sửa: [wireframe004](../ui/HR_POSITION_004_DESIGN.md).

## Kiểm thử thực chạy

Evidence private `.local/hr-position004/`, không đưa ảnh HR/credential vào Git.

| Gate | Kết quả |
| --- | --- |
| Preflight main | Không có company/department với hơn1HEAD active; không tự sửa dữ liệu để đạt |
| Backend HR | `backend-fixed.log` và `backend-restored.log`:26ca,0failed/0errors; chặn preview/apply khi có HEAD, hạ trước/bổ nhiệm sau, index direct/reactivation/scope và hồi quy quyền/job |
| HEAD regression | `head-regression.log`:4ca `tp_project:TestDepartmentRole`,0failed/0errors sau restore |
| Browser fixture | `browser-result.json`:8nhóm đạt,0console/pageerror; detail-only, job giữ quyền, scoped promote/demote+old-session deny, replacement sau demotion, named error giữ incumbent, noaccount mobile picker, hủy không ghi |
| Race HTTP | `race-result.json`:2admin sessions cùng preview phòng trống,2apply đồng thời →1thành công/1bị chặn snapshot mới, chỉ1HEAD; không ghi dữ liệu thật |
| HOOT sau restore | `.local/hr001/hoot-18079/` và bản sao `hoot-restored/`:HR20tests83assertions/Home29tests166assertions đạt |
| Clean smoke | `smoke-18079.json`, `smoke-18069.json`:4nhóm mỗi cổng đạt0errors; detail-only/desktop1440×1100/mobile390×1100/focus/nooverflow/cancel giữ job/quyền thật |
| Static | Ruff HR/XML10/diff check đạt; index đúng và0duplicate scopes cả2DB bằng SQL đọc |

Lượt backend đầu lỗi fixture chưa có group platform/department khác công ty;
đã sửa test đúng policy, không nới production guard. Browser đầu lỗi selector
Đóng trùng header/footer, rồi thiếu general job của fixture; đã sửa harness/
fixture và chạy lại tuần tự đủ8nhóm đạt. Một race được khởi chạy khi browser
đang chờ picker; không dùng lượt đó để kết luận browser đạt, đã rerun tuần tự.
Clean smoke đầu chạy cùng HOOT gặp500 asset do WinError5 ghi filestore trên
Windows; giữ log/lượt fail và kiểm lại riêng sau asset generation. Không tính
lượt fail là pass. GCassetsWinError5/markdown2warning giữ giới hạn môi trường.

## Restore và bàn giao

Backup rehearsal `.local/hr001/backup-tp_tanphat_dev-20261112T051846939786Z`;
restore canonical test596rowsets/643blobrefs/429sequences khớp rồi neutralize
UUID/baseURL/cron/SMTP, loại toàn bộ fixture trước backend/HEAD/HOOT/smoke cuối.
Source seal53file và rollback53filegốc SHA256,0filemới. Không DB thứ3 hoặc
restore test sang main. Snapshot main trước áp79bảng/617nonassetblob giữ nguyên.

Main dừng đúng PID/config, backup cuối
`.local/hr001/backup-tp_tanphat_dev-20261112T052315995362Z`, upgrade chỉHR20.0.1.5.0
noHTTP/stop-after-init, start18069/clean smoke đạt. Login giữ20.0.1.4.0. Source53file
seal khớp,79bảng/617nonassetblob bảo toàn; ACL policy giữ,2write_date đổi do
upgrade, groups/implied/company giữ. Cả2cổng39employee/27user/8active/13phòng/
9đơn vị có người/7mapping/1HEAD. Không đổi job/account/password/role/grant thật.
Ảnh trước–sau cùng route/role/dataset/viewport ở `before-{list,profile}.png` →
`after-{list,profile}-18069.png`, dialog/role desktop/mobile có hậu kiểm cả2cổng;
đã mở ảnh thật tự đánh giá. Ảnh named error dùng fixture giả trước restore.
Rollbacksource không tự gỡ indexSQL; xem [runbook](../../ops/runbooks/HR_ACCOUNT_ROLE_001_DEPLOY_AND_ROLLBACK.md)
nếu cần trả policy003, không xóa role/audit hoặc unique user/company/department cũ.
Technical verification, visual/business acceptance và pilot authorization tách
riêng. Chưa điện thoại vật lý; subagent không khởi tạo được vì model kế thừa
không khả dụng nên không có audit độc lập. Không stage/commit/push.
