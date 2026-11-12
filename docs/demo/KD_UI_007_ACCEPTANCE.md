# KD-UI-007 — Acceptance và bằng chứng

Ngày 07/11/2026. **Đã triển khai và tự kiểm kỹ thuật** KD-UI-007; `tp_kd_workspace` **20.0.1.5.0** đã upgrade riêng trên database `tp_tanphat_dev`, [dev18069](http://127.0.0.1:18069/odoo). Clone owned18889 `tp_tanphat_kdui007_20261107`. User visual acceptance, audit độc lập, business acceptance và pilot authorization vẫn riêng/chưa được tuyên bố đạt. Người dùng trực tiếp yêu cầu triển khai/áp dev trong lượt này, thay vai trò điều phối mặc định cho đúng task; không commit/push.

| Ca | Actor/thao tác | Kết quả phải quan sát |
| --- | --- | --- |
| A01 | Editor mở đủ 11 nhóm hồ sơ và smart button | Inventory đối chiếu resolved views; ảnh trước và sau |
| A02 | Từng list lọc nhanh/nâng cao, xóa chip/filter | Domain thật, giữ action domain/quyền/saved filter/sort |
| A03 | Fixture 18 và >100 record | 10+8; các mức 10/20/50/100 có RPC limit/offset đúng |
| A04 | Trang cuối rồi đổi filter/size, group và mở/quay lại | Offset hợp lệ; grouped ghi nhóm, pager native giữ |
| A05 | User/database/action/view khác, storage rác/lỗi | Không lẫn prefs, fallback 20; không lưu record/filter |
| A06 | Mỗi technical state, form action | Badge khác màu và có chữ; guard/version/wizard giữ |
| A07 | Readonly x2many và editable/new/dirty | Lọc cả quan hệ đúng quyền; không mất dòng ORM; hướng dẫn lưu |
| A08 | Metadata/no-money/outside scope | RPC/DOM không lộ tiền/file; denied ngoài scope |
| A09 | Tổng quan/Báo cáo, nguồn và drilldown | Filter/size thật; bảng cấu trúc cố định có lý do rõ |
| A10 | 1440/1920/768/390/360, zoom125/150, keyboard/reduced-motion | Không overflow trang/đè header, focus dùng được |
| A11 | Odoo/HOOT/browser/XML/JS/Ruff | Kết quả và source hash thực; không dùng test cũ thay test lượt này |
| A12 | Backup/apply18069/read-only verify | Dump+blob verified; business/security/account/module/attachment giữ |

## Kết quả thực chạy

| Cổng | Lệnh/bằng chứng private | Kết quả |
| --- | --- | --- |
| Baseline/clone | `kd_ui007.py prepare`; `restore-evidence.json` | Restore rehearsal576table/269blob; source riêng, fixture118cơ hội +18dòng quan hệ chỉ clone |
| Inventory A01 | `kd_ui007.py inventory --label after`; `inventory-after.json`, `arch-after/` |38view/43table đã resolve, trừ2view/2table TP Projects ngoài app → **36view/41vị trí bảng KH-KD**:15list chính/hỗ trợ +26bảng con |
| Odoo A06/A08/A11 | `kd_ui007.py test`; `odoo-tests/20261107T103648592721Z.log` | **117/117**: workspace44 +contract73,0failed/0error; gồm boundary100/101/MERGE_MAX và quyền/workflow |
| HOOT A05/A07/A11 | `node scripts/kd_ui007_ui.cjs clone hoot`; `shots/clone-hoot/console.txt` | **11test/40assertions**, gồm6test mới về prefs, model limit/SearchModel, relation dirty, semantic mapping;5test cũ giữ |
| UI A01–A10 | `node scripts/kd_ui007_ui.cjs clone after`; `browser-result.json`, `shots/clone-after/` | **353/353**,0console/pageerror;11list/form/notebook, related popup, tiền/snapshot, native saved filter/group, manager assignment, no-moneyRPC/DOM |
| Hồi quy A04/A06/A08/A10 | `node scripts/kd_ui007_ui.cjs clone regression`; `regression-result.json`, `shots/clone-regression/evidence.json` | **332/332**,0error; contract draft→submit→return→rework→resubmit, stale version, save/discard, optional columns/sort/selection, scope từng actor, outside-app look, keyboard/touch/reduced-motion |
| Zoom A10 | `node scripts/kd_ui007_ui.cjs clone zoom`; `zoom-result.json`, `shots/clone-zoom/` | **24/24**, Chromium zoom thật125/150 qua browser settings,11list +Tổng quan; không gọi deviceScaleFactor là zoom thật |
| Phản hồi muộn/lỗi A04 | `.local/kd-ui007/filter-race.cjs`; `filter-race-result.json`, `filter-race.png`, `filter-error.png` | **3/3**:2RPC đọc đến lệch thứ tự không khôi phục kết quả cũ, thông báo lỗi AccessError mô phỏng và reload phục hồi; không giả là kiểm quyền thật |
| XML/guards A06/A11 | `final-arch-audit.json` |157thay đổi thuộc class/widget/options/limit/decoration-danger, **0thay đổi thuộc tính hành vi ngoài phạm vi**. Inline event forms mới readonly, money gate giữ |
| Lint/assets A11 | Ruff cho tooling/Python thay đổi; `node --check`5runner; Odoo upgrade/HOOT/browser compile XML/QWeb/SCSS/JS | Đạt; không sửa/chạy build React legacy |
| Kiểm cuối A10/A11 | Parse16XML/27Python/6JS, link/fence7tài liệu và `git diff --check`; contrast6cặp badge | Đạt; contrast chữ/nền6.37–7.57:1 (AA chữ thường), đúng token source; workflow finish/check CHG-20261107-012 |
| Source gate A12 | `kd_ui007.py seal` | Source hash Odoo=HOOT=UI=regression=zoom=sealed; source applied bằng source sealed |
| Backup A12 | `kd_ui007.py backup`; `backup-pre-apply-20261107T104300Z/` | **112file manifest/576table/269blob reference**, checksum từng file và pg_restore --list đạt; backup khi dev đang chạy, trước apply dưới15phút |
| Apply A12 | `kd_ui007.py apply`; `dev-apply-20261107T104343Z.log`, `dev-apply-result.json` | rc0,0ERROR/CRITICAL, `changed_tables {}`; restart dev wrapper PID16896, listener20112; SQL module installed20.0.1.5.0 |
| Dev chỉ đọc A12 | `node scripts/kd_ui007_ui.cjs dev verify` và `dev regression`; `shots/dev-verify/result.json`, `shots/dev-regression/result.json` | **329/329 +325/325**,0error;11nhóm/sidebar/filter/size/form/notebook/related/smart/Tổng quan/responsive, không chạy write chain hoặc saved-filter write trên dev |
| Bảo toàn A12 | `preserve/extended --label after`, `deep-preserve.py after`, `verify-preservation.py` | **37bảng/3.050dòng** mở rộng **63bảng/3.602dòng** gồm lịch sử giữ nguyên;257attachment ngoài assets,93module installed,5bảng group,269blob gốc sha1/size,181file addon khác giữ; accounts/password/grants/Home Action giữ |

## Kiểm tra quan sát và phân trang

118record:10/20/50/100row thật, RPC `limit` tương ứng/offset0; trang2 của100còn18, RPC offset100. Tập18record:10+8; lọc ở trang cuối reset offset0, empty không sai trang. Quan hệ18dòng:10+8, popup tìm được dòng ngoài trang hiện tại và parent vẫn đủ18ID. Grouped ghi **nhóm mỗi trang**, native group headers giữ. Saved filter đồng bộ chip/count18; xóa chip không bỏ action domain. Prefs tách database/user/model/action/view, junk/storage unavailable fallback20; Tổng quan giữ default10 tương thích trước.

11nhóm chính: Cơ hội, Dự án, Hợp đồng, Công việc, Giao khoán, Sản lượng, Nghiệm thu, Kế hoạch định kỳ, Thanh toán, Chứng chỉ, Nghĩa vụ. Smart list revision/document/amount/audit; các relation phân công/child/scope/BASE/submission/amount/event/snapshot và wizard draft/return nằm trong [inventory](../ui/KD_UI_007_TABLE_INVENTORY.md). Không bỏ nhóm bảng record nào đã inventory. Wizard mới/dirty khóa lọc và size với giải thích, native ORM/save/discard giữ; không tự lưu để lọc.

Ảnh đã mở kiểm trực tiếp: đủ11list qua3contact sheets `final-contact-1.png` đến`3.png`, chi tiết chứng chỉ/badge dài, hợp đồng, popup snapshot/revision và mobile. Trước: toolbar chỉ density/reset, native filter chưa nổi bật, badge xám/returned đỏ cả dòng. Sau: thanh tìm kiếm riêng, hàng Bộ lọc có chữ +trường phù hợp/nâng cao/xóa, size trực tiếp, badge semantic, returned tên/mã bình thường. Badge cảnh báo chứng chỉ dài đã wrap đầy đủ, có kiểm Range phần chữ thật sau khi phát hiện quy tắc ellipsis native. Mobile có một searchbox native rộng cả hàng, size gọn và Bộ lọc mở panel; không tràn toàn trang. Table có thể cuộn ngang bên trong để đọc cột còn lại.

Desktop1440/1920, tablet768, mobile390/360, sidebar rail/drawer/collapse và zoom125/150 có ảnh/kiểm. Đây là Chromium/headless/touch emulation; chưa kiểm Safari hoặc điện thoại vật lý. Một số lượt trước gặp timeout điều hướng/hộp thoại native và được chạy lại; các result hiện hành trên source sealed đều xanh. Không dùng kết quả fail cũ làm cổng apply.

## Ảnh trước–sau và giới hạn

Ảnh private dưới `C:/TANPHAT ONE/.local/kd-ui007/shots/`. `dev-before/` chụp đủ11list/form +Tổng quan1440/390 bằng editor trên dataset dev gốc; `dev-verify/` chụp sau cùng actor/dataset/viewport. `clone-before/` trước fixture, còn `clone-after/` có fixture test nên không dùng cặp đó để tuyên bố dataset giống nhau. Tên ảnh `list-<nhóm>-1440.png`, `form-<nhóm>-390.png`; ảnh lọc `filtered-<nhóm>-1440.png`; trang2 clone `page2-opportunities-100.png`, `18-records-page2-eight.png`, `relation18-page2.png`; popup và smart list ở cùng folder. Không đưa credential/cookie/dump/filestore vào Git.

Đã mở kiểm ba ảnh ghép dev trước–sau cùng dữ liệu `dev-before-after-opportunities.png`, `dev-before-after-credentials.png`, `dev-before-after-payments.png`: thấy thay đổi toolbar/search/filter/paging rõ, nhãn dài không cắt và returned không đỏ cả dòng. PG55432 PID4228 và các clone18169/18269/18489/18589/18689/18789 giữ PID baseline; chỉ dev và clone owned18889 được restart. Clone owned dừng sau khi hoàn tất để không giữ process test thừa; DB/source/evidence vẫn sẵn cho audit.

Ngoại lệ có lý do: nguồn10nhóm, G01 seven×three và legend là cấu trúc cố định; preview so sánh kế hoạch tối đa12 và chứng chỉ gần hạn tối đa5 có nhãn/đường mở native list đầy đủ; Việc của tôi giữ MERGE_MAX500 và giải thích thu hẹp lọc/mở nguồn. Không pager giả. `expiry_status` không searchable nên lọc theo `valid_to`, ngưỡng30ngày vẫn minh họa. Đề nghị thanh toán không đồng nghĩa thu/chi; submitted chưa xác minh; còn hạn chưa xác minh năng lực. Không đổi ACL/state/schema/API/công thức; backend chỉ PAGE_MAX50→100.

Hướng tất cả bảng KD-UI-007 thay phạm vi bốn màn KD-UI-006; không sửa lịch sử mockup thành đã duyệt. Multi-agent không khả dụng do model kế thừa không được server hỗ trợ; đây là tự kiểm theo Ponytail và test kỹ thuật, không audit độc lập. Xem [hướng dẫn Ctrl+F5 và5bước](KD_UI_007_USER_GUIDE.md). Rollback delta được giữ bằng `scripts/kd_ui007.py rollback` và source baseline/snapshot; không cần rollback trong lượt apply thành công này.
