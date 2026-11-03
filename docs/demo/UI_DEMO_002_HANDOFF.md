# UI-DEMO-002 — Bàn giao điều hướng demo

**Change:** CHG-20261030-005. **Ngày:** triển khai 30/10/2026, kiểm cuối và bàn giao 31/10/2026 (Asia/Saigon).
**Trạng thái:** `IMPLEMENTED_PENDING_AUDIT`. Technical acceptance, business acceptance và pilot authorization chưa được cấp trong batch này.

## Kết quả sử dụng

Hàng tab dài/dấu cộng của app Demo chuyển thành hai tầng desktop: nhận diện TANPHAT ONE + Demo, nút **Tất cả phân hệ**, tiện ích native; bên dưới là **Tổng quan**, **Dự án & công việc**, **Hợp đồng & hồ sơ**, **Kinh doanh**, **Nguồn lực**, **Đề nghị**. Dưới 992px dùng nút **Phân hệ** và dialog cuộn trong màn hình. Nhóm Kinh doanh chỉ xuất hiện khi server trả menu được phép.

Panel có tên Việt, tên TP chuẩn, mô tả công việc, leaf mở trực tiếp và nhãn minh họa. Tìm `hop dong`, `hợp đồng`, `contract`, `du an`, `dau thau`, `request`; không phân biệt dấu/hoa thường và chỉ tìm menu được xem. Có xóa tìm và hướng dẫn khi rỗng. Không tìm dữ liệu hồ sơ.

| Actor | Trước | Sau | Khác biệt quyền giữ nguyên |
| --- | --- | --- | --- |
| `demo.lanhdao` | 12 phân hệ, 17 leaf | 12 phân hệ, 17/17 leaf mở đúng | 3 dự án, grant tài chính hiện có, CRM/Bid |
| `demo.kysu` | 10 phân hệ, 15 leaf | 10 phân hệ, 15/15 leaf mở đúng | 1 dự án, không CRM/Bid, không số tiền/tệp tài chính; Hợp đồng và Finance vẫn mở theo scope |

[Bảng mapping đầy đủ 17 leaf, tên Việt/tên chuẩn/menu XML ID/action XML ID và trước/sau từng actor](../architecture/TP_UI_DEMO_001_SPEC.md#mapping-trướcsau-theo-actor). Snapshot JSON cây menu thật trước/sau và danh sách leaf đã bấm ở `.local/ui-demo-002/review/{menus-before,menus-after,live-matrix}.json`.

## File và tích hợp native

| File dưới `custom_addons/tp_demo_workspace/` | Delta |
| --- | --- |
| `static/src/navigation/navigation_catalog.js` | Metadata theo XML ID, chỉ enrich leaf trong menu tree server, tìm không dấu/alias, nhận diện active |
| `static/src/navigation/navigation.js` | Component navbar/dialog; gọi `menu.selectMenu(actualMenu)`, nghe lifecycle action native, focus/cleanup |
| `static/src/navigation/navigation.xml` | QWeb inheritance chỉ app Demo; nhóm/dropdown/panel tìm; app khác giữ template native |
| `static/src/navigation/navigation.scss` | Namespace demo và portal, token xanh/mực, responsive, focus và reduced motion |
| `views/tp_demo_menus.xml` | Sáu nhóm, nhãn Việt, parent/sequence; giữ leaf XML ID/action/groups |
| `static/tests/navigation/navigation_catalog.test.js` | Sáu HOOT tests logic/quyền/active và cập nhật window controller không phát action phụ |
| `tests/test_demo_navigation.py`, `tests/__init__.py` | Hai test cây menu thật 17/15 leaf và action identity; thêm import test |
| `__manifest__.py` | Khai báo HOOT assets; feature được nạp qua backend asset glob hiện có |
| `README.md` | Cách dùng, ranh giới, bằng chứng navigation |

Tài liệu cùng batch: `docs/PROJECT_STATUS.md`, `docs/CHANGELOG.md`, `docs/ROADMAP.md`, `docs/architecture/TP_UI_DEMO_001_SPEC.md`, runbook, kịch bản UI-DEMO-001, tài liệu này và state do workflow checker sinh.

NavBar không có registry cho component template, vì vậy dùng patch tĩnh tối thiểu `NavBar.components` để đăng ký hai component. Không override `setup`/`adapt`, không copy WebClient/NavBar, không patch router/menu/action service. Custom section chỉ có khi current app là `tp_demo_workspace.menu_demo_root`; app khác vẫn dùng vùng `appSubMenus`/More với hợp đồng đo kích thước 46px. Dialog/dropdown dùng component Odoo, listener dùng Owl lifecycle và đóng dialog khi launcher unmount.

Nguồn menu là `/web/webclient/load_menus` qua menu service. Không hardcode numeric DB ID, tạo route giả, suy quyền từ login/chức danh, thêm ACL/grant hoặc gọi action phụ để đồng bộ active. Context/domain/breadcrumb/history do Odoo giữ.

## Snapshot phạm vi

Checkpoint bắt đầu `2026-10-30T07:00:41Z`; lượt tiếp tục dùng `ai_workflow.py start` nhận `RESUME`, giữ nguyên checkpoint. Tài liệu status còn `PROMPT_READY` khi tiếp nhận trong khi source navigation đã có; đã kiểm diff/hash trước khi đồng bộ bàn giao, không coi đây là batch khác.

Baseline nằm tại `.local/ui-demo-002/baseline_*_20261030_135845.*`, gồm Git status, diff ngoài scope, hash addon và **SCSS**. `scope-verification.json` xác nhận:

- Code theo checkpoint ngoài `tp_demo_workspace` không đổi; 25 tracked diff ngoài bốn file handoff giữ nguyên.
- Cả sáu SCSS có trước task đều cùng SHA-256: shared, dashboard, project overview, contract flow, finance, showcase. Chỉ thêm SCSS navigation.
- Model/projection/seed, ACL/security, action/view nghiệp vụ, React/OpenAPI/API, login/AUTH-002, tooling chung và `odoo/`/`addons/` không đổi trong task.
- Thay đổi có sẵn trong worktree được giữ nguyên; không stage/commit/push/deploy, reset/clean/stash hoặc sửa Git metadata.

Skill đã dùng: `C:/Users/vuduc/.codex/skills/frontend-design/SKILL.md` và `skills/odoo-web-guidelines/SKILL.md` cùng guideline JS/SCSS/assets. Thiết kế bám màu CHG-003 và nhóm công việc cầu đường; dùng icon Odoo local, không CDN/theme mới. Công cụ Windows `computer-use` được thử cho zoom nhưng lỗi nhận diện cửa sổ; kiểm zoom hoàn thành qua native Chromium Settings trong profile test riêng.

## Kiểm thử thực chạy

Các lệnh chạy từ `C:\TANPHAT ONE`. Bằng chứng dưới `.local` chỉ có trên máy này, không được coi là CI/UAT hoặc hồ sơ người dùng thật.

| Lệnh/kiểm | Target | Kết quả cuối | Bằng chứng |
| --- | --- | --- | --- |
| `.\.venv\Scripts\python.exe scripts\ui_demo.py test` | `tp_tanphat_demo_ui001_test`, HTTP 18119 | **21 passed, 0 failed, 0 errors**, không skip được báo | `.local/ui-demo-001/logs/test.log`, run PID 24712; bản trích `.local/ui-demo-002/review/odoo-test-final.log` |
| `node .local/ui-demo-002/review/hoot_nav.cjs` / `/web/tests?filter=tp_demo_workspace` | Demo 18109, HOOT trong browser | **6/6 passed**, 0 failed/skipped trên runner | `hoot-navigation.png`; runner shadow DOM nên body.innerText chỉ trả banner, ảnh đã xem trực tiếp |
| `node .local/ui-demo-002/review/live_matrix.cjs` | Demo 18109, hai actor | **17/17 + 15/15** leaf, action/active/search/reload/history/app roundtrip đạt | `live-matrix.json`, ảnh |
| `node .local/ui-demo-002/review/keyboard_context.cjs` | Demo 18109 | 6 nhóm kiểm đạt: Enter/Space, Tab/Shift+Tab, Esc/focus, mobile breadcrumb, native logout | `keyboard-context.json` |
| `node .local/ui-demo-002/review/project_context.cjs` | Demo 18109, hai actor | Giữ `DEMO-DUONG-02` qua dashboard link, panel/dropdown, reload, contracts + back/forward; kỹ sư 1 lựa chọn | `project-context.json`; lần đầu dùng sai selector, sửa script theo DOM và chạy lại đạt, không sửa application |
| `node .local/ui-demo-002/review/final_ui_checks.cjs` | Demo 18109, hai actor | **10 viewport + 4 zoom thật đạt**; 44 bước Tab/Shift+Tab/panel không che focus; reduced motion đạt | `final-ui-checks.json`, ảnh final |
| `python -m ruff check custom_addons/tp_demo_workspace/tests/test_demo_navigation.py custom_addons/tp_demo_workspace/tests/__init__.py custom_addons/tp_demo_workspace/__manifest__.py` qua `.venv` | File Python/manifest delta | Đạt sau sắp import test | Output lệnh; không thay Python nghiệp vụ |
| XML parse + local Markdown links/nội dung, `git diff --check`, `ai_workflow.py finish/check` | Source/handoff | Ghi kết quả thực trong state checker | `docs/AI_WORKFLOW_STATE.json` |

Viewport ở cả hai actor: 1440×900, 1366×768, 1024×768, 768×768, 375×812. Zoom thật chọn **Page zoom** trong `chrome://settings/appearance` của profile Chromium riêng: 125%/150%, xác nhận `devicePixelRatio` 1.25/1.5 và CSS viewport 1139/949 trên cửa sổ rộng 1440. Không dùng CSS zoom/viewport giả để tuyên bố đạt zoom thật. Ảnh zoom cuối dùng CDP capture toàn surface vì clip CSS của Playwright cắt ảnh khi browser zoom; `--zoom-only` chụp lại và kiểm lại bốn ca zoom. Các ma trận có 0 console error và 0 HTTP lỗi không giải thích.

Log Odoo là append-only, có lỗi thử nghiệm cũ trước các bản sửa; kết luận chỉ dựa run cuối PID 24712 kết thúc **31/10/2026 00:16:21 Asia/Saigon**. Cảnh báo `markdown2` chưa cài, INFO filestore GC `PermissionError [WinError 5]` và AccessError mong đợi của ca quyền âm vẫn hiện; run cuối không có ERROR/test failure. Dòng thống kê nội bộ “31 tests” gồm fixture/setup; dòng kết quả chuẩn là **21 tests**, không cộng hai số. Không chạy React typecheck/build hoặc test tooling chung vì không đổi chúng; 10 unit guard UI-DEMO-001 vẫn là kết quả lịch sử riêng.

## Ảnh cuối đã tự xem

Thư mục: `C:\TANPHAT ONE\.local\ui-demo-002\review\`. Chỉ có dữ liệu giả, không mật khẩu/session. Các ảnh panel desktop có phần tiếp theo cuộn bên trong, không mất mục cuối.

| Nội dung | Ảnh |
| --- | --- |
| Desktop toàn thanh + dashboard đã tải | [desktop-1440.png](../../.local/ui-demo-002/review/desktop-1440.png) |
| Panel trên/dưới đủ phân hệ | [panel-1440.png](../../.local/ui-demo-002/review/panel-1440.png), [panel-lower-1440.png](../../.local/ui-demo-002/review/panel-lower-1440.png) |
| Dropdown Hợp đồng | [contracts-dropdown-1440.png](../../.local/ui-demo-002/review/contracts-dropdown-1440.png) |
| Tìm không dấu | [search-hop-dong-1440.png](../../.local/ui-demo-002/review/search-hop-dong-1440.png) |
| Kỹ sư | [engineer-1440.png](../../.local/ui-demo-002/review/engineer-1440.png), [engineer-finance-1440.png](../../.local/ui-demo-002/review/engineer-finance-1440.png) |
| Mobile / panel 375px | [desktop-375.png](../../.local/ui-demo-002/review/desktop-375.png), [desktop-375-panel.png](../../.local/ui-demo-002/review/desktop-375-panel.png), [engineer-375-panel.png](../../.local/ui-demo-002/review/engineer-375-panel.png) |
| App khác sau rời Demo | [other-app-1440.png](../../.local/ui-demo-002/review/other-app-1440.png) |
| Zoom thật 125% / 150% | [lanhdao-zoom-125-panel.png](../../.local/ui-demo-002/review/lanhdao-zoom-125-panel.png), [lanhdao-zoom-150-panel.png](../../.local/ui-demo-002/review/lanhdao-zoom-150-panel.png) |

## Runtime và bước tiếp theo

Demo để chạy tại **http://127.0.0.1:18109/odoo**, database `tp_tanphat_demo_ui001`, localhost, owner guard đúng. Sau lần gián đoạn runtime đã dừng, lượt tiếp tục dùng `ui_demo.py start` để mở lại; giữ credential cũ. DB test sở hữu riêng dùng cho test và process test đã tự dừng. Profile/cửa sổ browser kiểm thử đã đóng và trả zoom về 100%; runtime demo tiếp tục chạy.

```powershell
.\.venv\Scripts\python.exe scripts\ui_demo.py status
# Nếu runtime đang dừng:
.\.venv\Scripts\python.exe scripts\ui_demo.py start
```

Không chạy `prepare`/`seed` để chỉ mở lại demo. Đăng nhập actor trong [runbook](../../ops/runbooks/UI_DEMO_001.md), mật khẩu lấy ở file local theo runbook và không đưa vào chat/ảnh/Git.

Next action: phiên điều phối audit độc lập UI-DEMO-001/002, gồm scope/quyền/route/bằng chứng và phân biệt thật/minh họa. Hồ sơ C1 legacy do fixture gán lifecycle vẫn là điểm audit UI-DEMO-001; AUTH-002 slice 2 và C01 giữ là task riêng. Chưa mở dữ liệu thật, BASE approval, ký/hiệu lực/thanh toán, grant thật hoặc pilot.
