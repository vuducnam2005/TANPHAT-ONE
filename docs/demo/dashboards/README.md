# Dashboard native TANPHAT ONE — DASH-UI-001

04/11/2026, `CHG-20261104-001`. Đã áp dụng lên dev18069; XML ID/record giữ nguyên: `tp_native_data002_20261102.dashboard_coordination` (ID5), `.dashboard_finance_draft` (ID6). Không dùng seeder DATA002 để ghi đè cấu hình DATA003.

Native Odoo giữ app, điều hướng, menu thu gọn và mobile selector. Addon `tp_dashboard_privacy` bổ sung OWL trong action native, chỉ cho hai binding có `settings.tpDashboard.version=1`. Các thẻ/chart/bảng/drilldown dùng cùng phép tổng hợp ORM ở backend theo actor thực, không có sudo nguồn nghiệp vụ hoặc cache tiền dùng chung. Dashboard chuẩn vẫn dùng spreadsheet và Share native. Không sửa core/React/prototype/workflow/allowlist/group.

## Chênh lệch biểu đồ và dữ liệu hiện tại

| Trạng thái | Expense ID | VND |
| --- | --- | ---: |
| Đang soạn | 10,12 | 810.000 |
| Chờ duyệt | 7 | 1.250.000 |
| Đã duyệt | 8,9,11 | 5.100.000 |
| Tổng | 6 đề nghị | 7.160.000 |

Mốc DATA003 là 810.000 /3.100.000 /3.250.000 đồng. Expense11 (An Hòa,1.850.000) đã được **Administrator** duyệt lúc **04/11/2026 08:44:55 Asia/Saigon**, trước task này: write_date UTC01:44:55, activity message1018 và tracking message1020 (01:44:56 UTC) ghi Đã gửi duyệt→Đã phê duyệt, quản lý Nam→Administrator. Đây là thay đổi chứng từ, không phải lỗi cache/công thức. Không sửa hồ sơ dev để ép khớp lịch sử. Bốn invoice vẫn draft/tổng801.000.000 đồng, chưa/gồm thuế bằng nhau vì fixture không có thuế. Bằng chứng nguồn/dòng/state/currency/domain/history: `.local/dash-ui001/inspect-dev*.json`.

## Nguồn, công thức và bộ lọc

Phạm vi cố định bằng ID từ XML ID fixture, company1; chỉ tính phần phân bổ vào dự án được phép đang chọn. Không suy quan hệ bằng tên hoặc `invoice_origin`. Mặc định **Toàn bộ thời gian**; cùng bộ lọc dự án/ngày cho thẻ, chart, bảng và action mở nguồn.

| Chỉ tiêu | Định nghĩa backend | Ngày lọc |
| --- | --- | --- |
| Số hóa đơn nháp | Số `account.move` fixture duy nhất, `move_type=out_invoice`, `state=draft`, có phân bổ dương vào scope | `invoice_date` |
| Giá trị hóa đơn nháp gồm thuế | Tổng dòng `display_type=product`: `price_total × tỷ lệ analytic` | `invoice_date` |
| Chưa thuế, thông tin phụ | Như trên, dùng `price_subtotal` | `invoice_date` |
| Số đề nghị chi phí | Số `hr.expense` fixture duy nhất thuộc `draft/submitted/approved`, có phân bổ dương vào scope. Từ NATIVE-STABILIZE-001 (clone, chưa áp dev) thẻ ghi “Gồm Đang soạn, Chờ duyệt, Đã duyệt; không gồm Đã ghi sổ, Đang/Đã thanh toán, Bị từ chối.”; thẻ tổng thêm “Chưa phải số đã chi.” | `date` |
| Tổng chi phí / cơ cấu trạng thái | `total_amount` theo tiền tệ công ty nhân tỷ lệ analytic; tổng theo ba state thứ tự cố định | `date` |
| Chart và bảng tài chính | Cùng kết quả backend; theo dự án: số invoice/giá trị gồm thuế/chi phí ba state | Như từng nguồn trên |
| Công việc / hoàn tất | `project.task` theo project/company/rule; hoàn tất chỉ `state=1_done` | `create_date`, theo timezone tài khoản |
| Giờ làm / số dòng | Tổng `account.analytic.line.unit_amount` / số dòng theo project/company/rule | `date` |
| Dự án có dữ liệu | Số dự án có task hoặc dòng giờ trong scope/kỳ | Theo hai nguồn điều phối |

Ngày đầu/cuối bao gồm; công việc dùng biên ngày UTC từ timezone user. Invoice không có ngày bị loại khi chọn khoảng ngày; không thay bằng ngày kế toán. Quyền/project/company được kiểm lại mỗi request. Lỗi ACL/network không biến thành0.

Phân bổ nhiều dự án dùng tỷ lệ JSON analytic từng dòng/chi phí, không cộng nguyên chứng từ cho từng dự án. Chứng từ có thể xuất hiện nhiều hàng; thẻ tổng đếm duy nhất. Odoo currency làm tròn từng dòng/chi phí; phần chênh làm tròn gán ổn định vào project ID cuối trong scope được phép, trước lọc dự án. Key analytic có nhiều chiều không được cộng lặp. Từ chối nhánh chứa nhiều dự án, nhiều dự án chung account, phân bổ âm/vượt100% hoặc invoice khác tiền tệ công ty; chưa có quy tắc quy đổi. Phân bổ0% không tăng số chứng từ. Chưa phân bổ/ngoài scope không tính vào tổng dự án.

Drilldown backend trả action theo đúng ID có đóng góp và quyền hiện tại. Native list mở **chứng từ đầy đủ**: tổng nguyên chứng từ có thể lớn hơn phần phân bổ trên dashboard khi chia nhiều dự án. Giải thích số liệu trên UI ghi rõ giới hạn này; không cộng footer list thay tổng phân bổ. Không có lợi nhuận, doanh thu, thu/chi thực tế, tiến độ hay quá hạn mới. Đã duyệt chi phí không đồng nghĩa đã thanh toán.

## Giao diện và giới hạn

- Tài chính: đầu trang ngắn, nhãn giả lập,4 chỉ số,thanh ngang hóa đơn theo dự án và vòng cơ cấu chi phí ba trạng thái (bổ sung CHG-20261104-004), bảng dự án và Giải thích số liệu. Điều phối dùng thanh công việc tím/giờ làm xanh và định nghĩa task/giờ hiện có.
- Thanh25px có lưới và5 mốc từ0; tiền trên trục dùng Triệu đồng, nhãn/tooltip cho số đồng chính xác. Vòng chi phí hiển thị tổng backend ở tâm, chú giải xám/vàng/xanh kèm số tiền/tỷ trọng trong phạm vi đang xem; tổng0 chỉ là vòng nền, không vẽ phân bổ giả. Phần trăm/geometry/tick ở trình duyệt chỉ trình bày, không tính lại tiền nghiệp vụ. Không legend Tổng. Mobile xếp dọc, chỉ bảng cuộn ngang.
- Hover/focus làm nổi thanh/cung tương ứng, đồng bộ chú giải/tâm vòng, mở tooltip có tên đầy đủ và giá trị backend. Tooltip dùng popover native, có thể rê chuột vào, Escape đóng, không cướp focus. Tab/Enter hoặc tap mở cùng action nguồn; mobile không phụ thuộc hover để đọc số. Hiệu ứng140ms và tắt khi prefers-reduced-motion. Refresh/unmount xóa tooltip cũ.
- Làm mới truy vấn thật, giữ filter. “Lấy dữ liệu lúc” do backend ghi khi trả kết quả, không phải thời điểm chứng từ cuối cùng đổi. Loading/empty/denied/error+retry tách riêng; xóa card cũ khi bắt đầu request, bỏ response cũ về muộn.
- Internal Share được thay bằng Chỉ truy cập nội bộ; guard backend create/repoint/token cũ giữ nguyên. Chỉ đọc cờ privacy bằng sudo theo guard cũ; nguồn dữ liệu không nâng quyền. Dashboard chuẩn khác giữ Share.

**Mobile (MOBILE-001, CHG-20261104-005):** chỉ đổi trình bày, không đổi report backend/công thức/domain/quyền. ≤700px: bộ lọc gập sau nút “Bộ lọc” (số bộ lọc đang áp dụng, Xóa lọc, dòng tóm tắt dự án/khoảng ngày), input16px/44px; ≤1199px chỉ số2 cột, ≤480px1 cột, tiền không cắt giữa số. Bảng chi tiết cuộn trong vùng riêng có gợi ý, cột Mã/tên dự án dính bên trái, ô mở nguồn44px. Thiết bị cảm ứng hiện gợi ý chạm thay gợi ý di chuột. Chống chạm kép khi mở nguồn. Bộ chọn bảng native trên điện thoại (khi đang xem bảng TANPHAT): toàn màn hình, tên không cắt, Escape/Quay lại đóng và trả focus, Enter/Space chọn. Biểu tượng chuyển từ `fa` (Odoo20 không còn nạp Font Awesome) sang `oi` native; spinner tắt khi giảm chuyển động. Mất mạng thiết bị: Odoo native làm mờ nút đến khi server trả lời lại; lỗi tải report hiện khối lỗi + Thử lại. Bằng chứng: [MOBILE-001 acceptance](../../ui/MOBILE_001_ACCEPTANCE.md).

Native spreadsheet không cung cấp phép phân bổ analytic hai nguồn cùng bộ lọc dự án đúng nghĩa; vì vậy dùng OWL bổ sung trong action native. Workbook còn pivot để kiểm nguồn, không phải vùng đang trình bày theo filter. Edit spreadsheet không chỉnh được thẻ/chart OWL. Không thêm public export/share. Source list chưa có view từng phần phân bổ.

## Generator và apply/verify

| File | Vai trò |
| --- | --- |
| `build_templates.py` | Generator connected_view gắn kind/version/scope, bỏ IFERROR và invoice_origin grouping của finance connected |
| `tp_project_coordination.template.json` | Workbook/cấu hình điều phối hiện hành |
| `tp_invoice_expense_connected.template.json` | Workbook/cấu hình tài chính hiện hành DATA003/DASH-UI-001 |
| `tp_invoice_expense_draft.template.json` | Lịch sử DATA002, không áp lên connected |
| `scripts/dashboard_templates.py` | Resolve token bằng binding ID, dùng chung bởi công cụ apply và DATA003 links |
| `scripts/dash_ui001.py` | Snapshot/clone/inspect/guarded apply/verify/upgrade-dev; không seed user hoặc chứng từ |

Token PROJECT/INVOICE/EXPENSE_IDS, CID và PID_* được resolve bằng ID, không chứa kết quả tiền. `native_data003.py links` kiểm cùng hai template và **từ chối drift**, không tự ghi đè workbook hoặc quay chart cũ. Không chạy actors/actions/seeder cũ để sửa UI.

```powershell
.\.venv\Scripts\python.exe docs/demo/dashboards/build_templates.py
# Trên operation đã có đúng owner/restore rehearsal:
.\.venv\Scripts\python.exe scripts/dash_ui001.py inspect --target dev
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target clone --mode dry-run
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target clone --mode apply
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target clone --mode verify
# Sau clone test và evidence gates:
.\.venv\Scripts\python.exe scripts/dash_ui001.py upgrade-dev
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target dev --mode dry-run
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target dev --mode apply
.\.venv\Scripts\python.exe scripts/dash_ui001.py apply --target dev --mode verify
```

Apply chỉ ghi workbook/tên của đúng hai record đã kiểm. ID/allowlist/group/company/internal flag phải khớp baseline. Nếu current khác baseline lẫn target, dừng để reconcile user edit. Reapply created0/updated0. Baseline inspect-<target>.json không ghi đè; lần đọc sau vào -current.json. Không xóa owner/checkpoint để ép chạy lại.

Snapshot `.local/dash-ui001/snapshot-20261104T015714Z/`130 checksum; restore clone `tp_tanphat_dashui001_20261104` port18159/data-dir riêng/cron+mail neutralized:538 rowset/249 blob reference exact. Không dựng lại demo18109/18119. Upgrade chỉ addon privacy, dùng `stop_server` để dừng riêng Odoo. Một lần dùng nhầm CLI `dev.py stop` dừng cả PG làm upgrade không kết nối được: đã khởi động lại, so sánh538/538 bảng/config/credential/catalog/roles nguyên trước khi dùng đúng hàm upgrade, không seed/reset password. Chi tiết test và bàn giao tại [DASH_UI_001_HANDOFF.md](../DASH_UI_001_HANDOFF.md).
