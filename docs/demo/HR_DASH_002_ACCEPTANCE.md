# HR-DASH-002 — Nghiệm thu kỹ thuật

CHG-20261112-001 và cập nhật sidebar CHG-20261112-002. Thực thi yêu cầu trực tiếp của người dùng; không commit/push.
Thiết kế tại [bố cục sáng](../ui/HR_DASH_002_LIGHT_CHART_DESIGN.md), hướng dẫn
tại [guide HR](HR_DASH_001_USER_GUIDE.md). Visual/business/pilot do người dùng
xác nhận riêng; đây là tự kiểm, không audit độc lập.

## Ca kiểm và bằng chứng

Actor admin, population hiện hữu trên `tp_tanphat_test`18079; không seed
hoặc sửa dữ liệu nhân sự để tạo biểu đồ. Ảnh trước–sau cùng1440/390×1100,
role, route và population39hồ sơ/9đơn vị có người/6liên kết.

| Ca | Điều kiện quan sát | Kết quả test18079 |
| --- | --- | --- |
| H2-01 | Header/filter/5KPI, icon render, một navbar | Đạt Playwright, ảnh thật |
| H2-02 | Donut260–320px, đủ nhóm, tổng bằng KPI, màu không trùng tập hiện hữu và giữ sau lọc | Đạt helper/HOOT/Playwright; khoảng297px ở1440 |
| H2-03 | Tooltip tên/số/%, đồng bộ hover/focus, Escape, Space mở đúng đơn vị | Đạt HOOT và browser |
| H2-04 | Đủ chức vụ, giảm dần/tie ổn định, cùng thang0, thanh18px, drilldown đúng | Đạt helper/HOOT/browser; đủ11nhóm hiện hữu không cuộn |
| H2-05 | Bảng tìm riêng, 10/20/50/100; account mở/khóa là phần đã liên kết | Đạt browser/domain, không ghi tài khoản |
| H2-06 | Company/filter/population, XLSX và list cùng scope; catalog giữ khi rỗng; race/loadedFilters | Regression HOOT/browser/XLSX đạt; backend không đổi |
| H2-07 | OS dark + CSS dark thực: dashboard/input/tooltip sáng; sidebar navy theo phản hồi CHG002 | CHG001 kiểm dashboard/input/tooltip; CHG002 kiểm lại dashboard và sidebar, palette đúng cả2cổng |
| H2-08 | 1440/1024/768/390/320, CSSzoom200, reduced-motion, touch/drawer | Đạt Playwright; không tràn overview; touch là emulation |
| H2-09 | Danh sách nhóm,6tab hồ sơ, dialog tài khoản/hiển thị Mở/Khóa/Chưa liên kết | Đạt browser chỉ đọc; không thao tác lock/write |
| H2-10 | Loading/empty/error/retry, chặn export khi lỗi, không console/pageerror liên quan | Đạt HOOT + browser response injection;0console/pageerror |

Lệnh thực chạy:

```powershell
node scripts/hr001_hoot.cjs
$env:HR_EVIDENCE_DIR='.local/hr-dash002'
node scripts/hr_dash001_ui.cjs
node scripts/hr_dash002_checks.cjs
```

HOOT:15HR +2dependency =17tests/72assertions; Home28 +1dependency =
29tests/166assertions. XML parse và Node syntax đạt. Không chạy backend
Odoo suite hoặc React build vì không đổi Python/model/security/React.

Evidence private `.local/hr-dash002/`: `before-1440.png`, `before-390.png`,
`before-population.json`, `ui-18079/` và `checks-18079/`.
HOOT tại `.local/hr001/hoot-18079/`. Ảnh desktop/mobile/dark đã mở tự đánh giá.
Một lượt SCSS fail vì Sass không hỗ trợ min(px,%), OWL inline if fail và
selector/test timing sai đã được sửa và rerun; không tính lượt fail là pass.

## Áp main và bàn giao

**IMPLEMENTED_VERIFIED_MAIN_APPLIED.** Main18069 đạt cùng5nhóm regression và
7nhóm kiểm bổ sung như test18079,0pageerror/0consoleerror liên quan.
KPI/biểu đồ/XLSX giữ39hồ sơ/9đơn vị có người/6liên kết. Ảnh main ở
`.local/hr-dash002/ui-18069/`, `checks-18069/` đã xem desktop/mobile/dark.

Backup cuối trước áp:
`.local/hr001/backup-tp_tanphat_dev-20261112T014402981715Z`,595bảng/
636tham chiếu blob, dump/source/config/filestore và checksum. Rollback source
đúng bản trước sửa tại `.local/hr-dash002/rollback-source.zip` và manifest;
không dùng source mới trong snapshot cuối làm source cũ.

Chỉ static assets, không module upgrade/migration/restore; không tạo DB thứ ba.
Seal riêng bao phủ tất cả15file static HR, gồm SCSS vốn không nằm trong checker.
Gate preservation sau smoke đạt79bảng/612blob không phải assets,15file
static source/test khớp seal; ACL/rule/company membership/implied group
khớp backup. Toàn595rowsets chỉ đổi6bảng kỹ thuật: assets, bus/presence,
device/login log và transient account wizard. Mở “Xem tài khoản” tạo wizard
tạm theo native; không bấm lưu/lock/unlock/reset, không đổi hồ sơ hoặc user.

Main được terminal khác mở lại lúc08:44:46 ngày12/11; lệnh start có guard
đã từ chối chạy thêm listener. Đã đối chiếu PID25400/parent29432,
config `.local/odoo.conf`, workspace source và smoke. Không gọi đây là
maintenance độc quyền. Trước đó đã dừng cả parent/child Odoo đúng config
để tránh nhầm child của venv với toàn runtime. Không đổi config của main.

Workflow finish/check và git diff --check ghi tại status/changelog.
Chưa kiểm điện thoại vật lý, chưa có audit độc lập (subagent không khởi
tạo được với model kế thừa); visual/business/pilot chờ người dùng.


## Phản hồi sidebar — CHG-20261112-002

Người dùng yêu cầu sidebar cùng màu Kinh doanh và icon nhân viên trước
“Nhân viên”. Đã áp18069 sau kiểm18079: nền23/50/77, mục chọn34/71/106,
chữ220/230/240, icon native `group` render font/ligature đúng trước nhãn.
Dashboard giữ244/247/251 và chart trắng. Bằng chứng sidebar trắng CHG001
ở trên là lịch sử; yêu cầu hiện tại là sidebar navy cố định.

Playwright `.local/hr-sidebar002/verify.cjs` chạy trên cả2cổng: desktop1440,
mobile390, rail/drawer/icon, tìm không dấu, focus/Escape/trả focus, mở native
Danh sách nhân viên/quay Tổng quan39, OSdark + CSSdark thực/reduced-motion,
0console/pageerror. Ảnh trước–sau trong `.local/hr-sidebar002/`, đã mở ảnh
main/test desktop/mobile tự kiểm. HOOT18079 HR17tests72assertions,
Home29tests166assertions; XML/Node syntax/diff đạt. Không chạy lại suite
backend/React vì source tương ứng không đổi; chưa điện thoại vật lý/audit
độc lập. Verifier kỳ vọng codepoint thay ligature, đợi hidden như visible và
allowlist presence sai tên đã sửa theo source; chỉ rerun đạt được tính pass.

Backup mới `.local/hr001/backup-tp_tanphat_dev-20261112T020356030758Z`,
595bảng/638blobrefs. Rollback chỉ3file trong
`.local/hr-sidebar002/rollback-source/`; source trong backup cuối là bản
mới đã test. Main restart parent/child đã kiểm config/workspace; không
upgrade/migration/restore. SealSCSS/JS/CJS khớp, preservation79bảng/612blob
không phải assets đạt;5bảng kỹ thuật đổi. Visual/business/pilot chờ người dùng.
