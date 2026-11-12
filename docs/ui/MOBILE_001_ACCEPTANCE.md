# MOBILE-001 — Nghiệm thu kỹ thuật giao diện mobile/tablet/desktop

**Change:** `CHG-20261104-005` · **Ngày:** 04/11/2026 (Asia/Saigon) · **Trạng thái:** `IMPLEMENTED_VERIFIED_DEV_PENDING_AUDIT`

Phạm vi: Odoo native tại `http://127.0.0.1:18069` (dev) sau khi thử trên clone owned `tp_tanphat_dashui001_20261104`/18159. Một giao diện thích ứng dùng chung; không React mới, không sửa prototype HTML, `odoo/`, `addons/`; không PWA/service worker/offline cache/app. Không đổi workflow, API, quyền, công thức, domain, dữ liệu nghiệp vụ. Đây là nghiệm thu kỹ thuật của người thực thi, **chưa phải** audit độc lập, business acceptance hay pilot.

## 1. Đã thay đổi

| Phần | File | Thay đổi |
| --- | --- | --- |
| Viewport | `custom_addons/tp_web_home/views/tp_web_home_templates.xml` | Kế thừa `web.webclient_bootstrap`: `width=device-width, initial-scale=1` (native có `user-scalable=no` chặn phóng to). Test server `test_backend_viewport_keeps_user_zoom`. |
| Home | `tp_web_home/static/src/home/home_launcher.scss`, `home_button.scss` | <576px: 2 cột thẻ (icon trái, tên VI + gợi ý phải, cao ≥64px); tablet/desktop giữ 4/6/8 cột icon. Nút xóa tìm kiếm và nút Trang chủ ≥44×44, focus nhìn thấy. |
| Drawer | `tp_web_home/static/src/home/burger_menu_patch.js` | Patch drawer native trên điện thoại: Escape đóng; mở thì focus vào nút đóng; đóng thì trả focus về nút ☰. Nút đóng/chạm nền vẫn native. |
| Dashboard | `tp_dashboard_privacy/static/src/dashboard.{js,xml,scss}` | Bộ lọc gập sau nút “Bộ lọc” (đếm bộ lọc, Xóa lọc, tóm tắt); input 16px/44px; chỉ số 2 cột ≤1199px, 1 cột ≤480px, tiền không cắt; bảng cuộn trong vùng riêng + gợi ý + cột dự án dính trái + ô nguồn 44px; gợi ý chạm trên thiết bị cảm ứng; chống chạm kép khi mở nguồn; bỏ `overflow-x:hidden`; biểu tượng `fa` → `oi` native (Odoo 20 không nạp Font Awesome nên các biểu tượng cũ hiển thị rỗng); spinner tắt khi giảm chuyển động. |
| Bộ chọn bảng | cùng file, patch `DashboardMobileSearchPanel` | Chỉ khi đang xem bảng TANPHAT: toàn màn hình, tên không cắt, mục ≥48px, `role=dialog`, Escape/“Quay lại” đóng và trả focus về nút chọn, Enter/Space chọn; nút chọn hiển thị bảng đang xem. Bảng chuẩn khác giữ native. |
| Công cụ | `scripts/mobile001.py`, `mobile001_survey.cjs`, `mobile001_flows.cjs`, `mobile001_zoom.cjs` | Rollout clone/dev: clone `-u` hai addon kèm test; dev chỉ `-u tp_web_home`. Hash bảo toàn có allowlist write_date cho menu/action Home. Kèm khảo sát, luồng thao tác và zoom thật. Evidence private trong `.local/mobile001/`. |

Manifest: `tp_web_home` 20.0.1.0.0 → 20.0.1.1.0 (thêm view). `tp_dashboard_privacy` giữ 20.0.1.1.0 của DASH-UI-001 (chưa bàn giao commit), chỉ đổi static.

## 2. Ma trận kiểm thử

Engine: **Chromium (Playwright 1.64.1) emulation** — `isMobile`/`hasTouch` khi rộng <768. WebKit không cài trong `frontend/node_modules/playwright` nên **chưa kiểm WebKit/Safari**. **Chưa kiểm trên iPhone/Android thật.**

| Viewport | Home | Dashboard tài chính/điều phối | Project/task | Giờ làm/chi phí | CRM/Liên hệ/Nhân sự/Hóa đơn |
| --- | --- | --- | --- | --- | --- |
| 360×800 | khảo sát + luồng | khảo sát + B7 | khảo sát | khảo sát | khảo sát |
| 390×844 | A1/A2 | B1–B6 | C1 | C2/C2b/C3 | khảo sát |
| 430×932 | khảo sát | khảo sát | khảo sát | khảo sát | khảo sát |
| 844×390 (ngang) | A3 | B7 | khảo sát | khảo sát | khảo sát |
| 768×1024 | A3/A4 | B7/B8 | khảo sát | khảo sát | khảo sát |
| 1280×800 | khảo sát | B8 | khảo sát | khảo sát | khảo sát |
| 1440×900 | khảo sát | B8 | khảo sát | khảo sát | khảo sát |
| Zoom thật 125%/150% (cửa sổ 1280, 1440) | đạt | đạt | — | — | — |

“Khảo sát” = `mobile001_survey.cjs`: đo tràn trang/phần tử, vùng chạm <32px, chữ <12px, lỗi console, kèm ảnh chụp từng ô (actor admin, long, khang). Số đo chỉ là tín hiệu; đã xem ảnh các màn hình chính (mục 4).

## 3. Luồng thao tác (`mobile001_flows.cjs`)

Clone (`WRITE=true`, dữ liệu giả) — **20/20 đạt**. Dev chạy cùng script ở chế độ chỉ đọc (`WRITE=false`): xem mục 6.

| Bước | Nội dung | Kết quả clone |
| --- | --- | --- |
| A1 | Home 390: 2 cột, chữ 16px, tìm “du an” → mở TP Projects → nút Trang chủ quay lại | đạt; ô 175×66, nút 44×44 |
| A2 | Drawer native: mở, focus vào nút đóng, Escape đóng, focus về ☰, chạm nền đóng | đạt |
| A3/A4 | Home ngang 844×390 không tràn; 768 giữ lưới 4 cột | đạt |
| B1 | Tài chính 390: bộ lọc gập, chỉ số 1 cột, tiền 1 dòng, không tràn | đạt |
| B2 | Mở bộ lọc, chọn dự án → đếm 1, tóm tắt “DA-2026-001 · toàn bộ thời gian”, Xóa lọc | đạt; select/date 44px, 16px |
| B3 | Làm mới giữ trạng thái; bảng cuộn 644/328px trong vùng riêng, cột dự án đứng yên, ô 44×44, gợi ý hiện | đạt |
| B4 | Chạm kép chỉ số → đúng 1 lần gọi action nguồn; Back về bảng | đạt |
| B5 | Thiết bị offline → native làm mờ nút; online lại → bật. Lỗi tải report → khối lỗi “Thử lại” 44px → phục hồi | đạt |
| B6 | Bộ chọn bảng: 390×844 toàn màn hình, mục 48px không cắt, focus “Quay lại”, Escape trả focus, Enter mở lại, chuyển sang Điều phối | đạt |
| B7/B8 | Điều phối 360/844 ngang; tài chính 768 (2 cột), 1280/1440 (4 cột), bộ lọc mở sẵn trên desktop | đạt |
| C1 | Long: Dự án → công việc → chi tiết → quay lại | đạt |
| C2 | Long: giờ làm mới; nhập “abc” → lỗi ngay trên ô “Thời gian đã dùng”, không lưu; nhập 0:30 → lưu, đúng user | đạt |
| C2b | Long thêm giờ từ tab “Bảng chấm công” của task → Lỗi Truy Cập ghi `project.task` (quyền write task), không có dòng giờ | đạt — **quyền, giữ nguyên** |
| C3 | Long: chi phí mới, chọn sản phẩm bằng hộp chọn toàn màn hình, 50.000 → lưu nháp | đạt |
| C4 | Long vẫn không đặt task “done” (AccessError) | đạt — **quyền, giữ nguyên** |
| D1 | Khang: report 5/6 AccessError, 0 chi phí đọc được, hóa đơn AccessError | đạt |

Dữ liệu giả trên **clone** (không có trên dev — đã truy vấn: Long không tạo chi phí/giờ làm nào trên dev trong ngày):

- chi phí nháp id 13–17 của Long: id 13 tên trống, 0đ; id 14–17 “MOBILE-001 chi phí giả …”, 50.000đ;
- dòng giờ id 43–47: id 45 “/”, 0 giờ, do một lần chạy thử bấm lưu khi native đã điền sẵn dự án; các dòng còn lại 0,5 giờ.

Lần chạy cuối (sau khi chỉnh B1/C1/C2b) tạo id 17/47. Clone là bản owned dùng thử, không phục vụ người dùng.

## 4. Ảnh trước/sau (private, đã tự xem)

- Trước (dev): `.local/mobile001/before-dev/`, `.local/mobile001/before-extra-dev/` — Home 3 cột chen chữ trên 360/390; tiền bị ngắt giữa số ở 768; bộ lọc luôn mở chiếm màn hình; ô nhập 32px/13px; bảng không gợi ý cuộn; nút nguồn nhỏ; gợi ý “di chuột”; bộ chọn bảng 200px cắt tên.
- Sau (clone): `.local/mobile001/flows-clone/*.png`, `.local/mobile001/survey-after-clone/`, `.local/mobile001/zoom-clone/`.
- Sau (dev): `.local/mobile001/survey-after-dev/` (cùng `survey-ts-dev/` và `survey-recheck-dev/` cho các ô chạy lại), `.local/mobile001/flows-dev/`, `.local/mobile001/zoom-dev/`.

Ảnh có tên người/số liệu giả lập nội bộ nên không đưa vào Git.

## 5. Bảo mật và hiệu năng

- Không đổi ACL/rule/group/assignment; report vẫn kiểm quyền backend; drilldown recheck. Khang (ngoài phạm vi) không đọc được report/chi phí/hóa đơn.
- Không localStorage/sessionStorage mới; không cache số liệu; không polling; resize không gọi lại report (B1 đếm 0 request `tp_dashboard_report` khi chụp toàn trang và xoay 390↔844); chống chạm kép khi mở nguồn.
- Phân trang list/kanban native giữ nguyên; không tải toàn bộ bản ghi ở client.
- Guard chia sẻ nội bộ của dashboard giữ nguyên (“Chỉ truy cập nội bộ”).

## 6. Áp dụng dev 18069

- **Upgrade hẹp:** dev đã chạy `tp_dashboard_privacy` 20.0.1.1.0 (DASH-UI-001) nên phần dashboard chỉ là static, restart là nạp. Chỉ chạy `-u tp_web_home` → 20.0.1.1.0 bằng `mobile001.py upgrade-dev`. Script dừng riêng Odoo (`stop_server`), PostgreSQL 55432 vẫn chạy, rồi bật lại. Log upgrade chỉ có cảnh báo native `markdown2`. Trang `/web/login` trả về viewport `width=device-width, initial-scale=1`, HTTP 200.
- **Khảo sát** `survey-after-dev/` (7 viewport × admin/long/khang × 12 route = 252 ô): 0 tràn trang; meta viewport mới ở mọi ô.
  - 6 ô timesheets của admin/khang trên điện thoại timeout ở lần đầu. Trang thật vẫn hiển thị trạng thái trống bình thường; lỗi nằm ở bộ chờ của script, vì `.first()` dính vào thẻ kanban "ghost" bị ẩn. Đã sửa bằng `filter({ visible: true })`; chạy lại riêng route này (`survey-ts-dev/`) thì 21/21 đạt.
  - 28 ô có vùng cuộn nội bộ, giống clone: cột list/kanban native cuộn trong vùng riêng, không phải tràn trang.
- **Phiên hết hạn chập chờn:** 2 ô dev (long tp-projects 1280, khang contacts 844) và 2 ô clone (admin tp-projects 430, khang timesheets 768) hiện hộp thoại native "Phiên làm việc đã hết hạn". Script ghi nhận nhầm là "denied".
  - Log server chỉ có các 403 dashboard đúng quyền; không có lỗi phiên ở mức HTTP.
  - Chạy lại đúng các ô đó (`survey-recheck-dev/`): 8/8 đạt, không lặp lại.
  - Không thuộc thay đổi CSS/JS của batch; chưa xác định nguyên nhân native.
- **Phạm vi dữ liệu:** Long thấy 3 dự án TP Projects, Khang thấy 1 (theo phân công), admin thấy tất cả.
  - Từ chối đúng quyền: CRM, Nhân sự và Hóa đơn với Long/Khang; dashboard 5/6 với Long/Khang (403, 2 lỗi console mỗi bảng).
- **Luồng** `flows-dev/` (`WRITE=false`): **20/20 đạt**. C2/C2b/C3 chỉ mở màn hình rồi dừng, không ghi; C4 chỉ đọc task của Long. Không tạo giờ làm hoặc chi phí trên dev.
- **Zoom thật** `zoom-dev/`: 12/12 đạt (1280/1440 × 125/150% × Home/tài chính/điều phối; DPR 1,25/1,5; 0 tràn).
- **Bảo toàn** `preserve-review-dev-preupgrade-dev-after.json`: 522/538 bảng nguyên. Delta:
  - view mới 1492 `tp_web_home.webclient_bootstrap_user_zoom` cùng XML ID của nó;
  - write_date của menu 314, action 502 và icon menu 398 (giá trị giữ nguyên, checksum giữ nguyên);
  - 4 asset được tái tạo (401, 420–422 → 424–427);
  - trigger auto-vacuum 79 do `-u`, write_date `ir_module_module`, signaling;
  - telemetry login/bus/presence do khảo sát.
  - Chứng từ, dự án/task, giờ làm, chi phí, hóa đơn, user/password/group/ACL/rule/assignment, config/credential/catalog/roles không đổi.
  - Snapshot `dev-before` (chụp đầu lượt) và `dev-preupgrade` chỉ khác presence/bus.
- Ảnh dev đã tự xem: Home 2 cột, bộ lọc mở, bảng cuộn có cột dính, khối lỗi "Thử lại", bộ chọn bảng toàn màn hình. Biểu tượng `oi` hiển thị đúng.
- **Runtime:** clone 18159 đã dừng bằng owned stop; dev 18069 và PG 55432 vẫn chạy; 18109/18119 đóng.

## 7. Giới hạn — tách lỗi UI khỏi quyền/chức năng chưa mở

**Quyền hoặc chức năng chưa mở (không phải lỗi responsive, không mở thêm):**

- Long không có quyền write `project.task`: thêm giờ từ tab task và chuyển trạng thái task bị chặn (RFC TASK-001 chờ quyết định). Long vẫn nhập giờ từ app Giờ làm.
- Long không vào CRM, Nhân sự, Hóa đơn và không tạo Liên hệ. TP Projects chỉ hiện dự án được phân công: Long 3, Khang 1.
- Khang không vào CRM, Nhân sự, Hóa đơn.
- Người không có quyền bảng tổng hợp (Khang, Lan với bảng 5/6) thấy lỗi native “An error occurred while loading the dashboard” và nút Share chuẩn.
- TP Contracts chưa có giao diện native (chỉ API) — không kiểm được trên mobile.

**Giới hạn native Odoo (ghi nhận, không vá trong batch này):**

- Hộp chọn dự án của giờ làm mở với bộ lọc mặc định “Yêu thích của tôi” → “Không tìm thấy bản ghi nào” cho tới khi người dùng bỏ bộ lọc bằng nút tìm kiếm. Native điền sẵn dự án dùng gần nhất.
- Ô many2one trên điện thoại là chỉ đọc (mở hộp chọn), không xóa trống trực tiếp.
- Thông báo “Missing required fields”, nhãn “Reimbursement/Date/Employee (Through a Purchase Receipt)” còn tiếng Anh (thiếu bản dịch native).
- Ô tiền là `type=text` không có `inputmode` → bàn phím chữ trên điện thoại.
- Ô giờ (float_time) cao 25px trong khung trường ~44px; biểu tượng nhỏ trên navbar/list/kanban native <44px; kanban nhóm vuốt ngang.
- Mất mạng: native khóa toàn bộ nút (`o_disabled_offline`) cho tới khi server trả lời; không có hàng đợi offline.
- Ô ngày `type=date` hiển thị theo locale trình duyệt (emulation hiện mm/dd/yyyy; Chromium profile vi-VN hiện dd/mm/yyyy).

**Chưa kiểm:** WebKit/Safari, iPhone/Android thật, trình đọc màn hình thật (chỉ kiểm thuộc tính ARIA/focus), bàn phím ảo che ô nhập (emulation không có bàn phím ảo; đã kiểm ô nằm trong viewport khi focus).
