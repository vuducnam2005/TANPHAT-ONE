# Trung tâm Báo cáo — UI thực thi CORP-REPORT-001

Ngày 16/11/2026 · CHG-20261116-008. Thiết kế và source native Odoo/OWL, test18079. Tài liệu này mô tả triển khai; không thay nghiệm thu trực quan/nghiệp vụ hoặc cho phép áp main18069.

## Shell và ngôn ngữ hình ảnh

Giữ navbar, tài khoản, identity và nút Quay lại chung từ `tp_web_home`. Addon đăng ký Home catalog và tái sử dụng cấu trúc/token sidebar HR/KH-KD/Kho ngay trong addon Báo cáo: nền navy, rộng264px/rail, icon, tìm chức năng, nhóm/collapse/mobile drawer và footer tài khoản chung. Navbar giữ cùng shell, ẩn menu tài khoản trên navbar theo pattern Kho khi sidebar có footer để tránh trùng. Theo yêu cầu trực tiếp người dùng giữa batch, thay sidebar trắng ban đầu; ảnh ban đầu không đại diện thiết kế sidebar cuối. Menu lấy từ menu service đã lọc quyền. Bảy mục: Tổng quan; Mục tiêu và kế hoạch; Báo cáo của tôi; Báo cáo phòng ban; Báo cáo công ty; Việc cần xử lý; Mẫu và lịch. Mục không được quyền có thể không xuất hiện.

Nền `#F4F7FB`, chữ `#182B49`, thao tác `#2563EB`, đã chốt `#0F8A70`, cần xử lý `#D97706`, lỗi `#C73C4B`. Font của shell, không CDN; bảng 13px, heading 26px; khoảng cách16–24px. Nền hàng xen kẽ, hover nhạt, số dùng format Odoo/locale. Màu luôn đi cùng nhãn.

Dashboard: tiêu đề và pending kỳ/phòng → phạm vi/ngày áp dụng/Hiện hành/thời điểm cập nhật → KPI mở danh sách → hai panel chart lớn → mốc định tính → chỉ đạo. Donut260px; panel≥370px desktop; responsive stack mobile. Donut dùng nghĩa vụ trong kỳ làm mẫu số; legend mở đúng domain backend. Plan/actual scale riêng theo từng chỉ tiêu cùng đơn vị, thiếu actual hiện Chưa có nguồn. Không tính tiền hoặc tổng hợp nghiệp vụ ở browser. Mốc định tính không bị ép thành phần trăm. Tooltip native có giá trị/đơn vị; legend và thanh là button dùng bàn phím/chạm.

## Danh sách và chi tiết

`ReportingListController` (`js_class=tp_reporting_list`) tái sử dụng `TpTableFilterBar` + SearchModel. Tối đa năm tiêu chí thường dùng; native search/advanced/favorite còn đủ field searchable. Pending khác applied, cùng chiều OR/khác chiều AND theo helper dùng chung. Backend lọc trước count/sort/page. Native pager và chọn10/20/50/100; native optional columns; action state giữ filter/sort/offset khi mở rồi Quay lại. Không lưu nội dung/tiền/từ khóa vào localStorage. Excel list ghi rõ xuất toàn bộ theo applied domain, không ngầm xuất trang hiện tại.

Cột mặc định kế hoạch: Nội dung, Người phụ trách, Loại kỳ, Đến ngày, Kế hoạch, Đơn vị, Trạng thái. Báo cáo: Nội dung, Người phụ trách, Phòng ban, Loại kỳ, Hạn, Trạng thái; cột phụ ẩn tùy chọn. Dòng báo cáo cá nhân nhúng giữ năm cột: Nhiệm vụ, Đầu ra dự kiến, Hạn công việc, Kết quả thực tế, Trạng thái việc. Mở dòng để xem số lượng có/chưa có nguồn, phối hợp, ưu tiên, minh chứng và nguyên nhân; không dàn toàn bộ cột Excel.

Form hai cột và notebook: phạm vi/người chịu trách nhiệm; kỳ/hạn/phiên bản; kết quả/công việc; vướng mắc/kỳ tới; nguồn/bao phủ; chỉ tiêu tiền riêng; phiên bản; nhận xét; lịch sử. Form kế hoạch có cây con qua liên kết cha/con và bảng phân bổ, mốc ban đầu so với hiện hành. Mỗi bảng nhúng có lối mở bảng đầy đủ cố định domain cha; embedded dirty giữ native commands, phải lưu/hủy trước điều hướng.

`ReportingFormController` gắn plan/document/line/directive và nội dung mẫu. Native hook gửi `tp_reporting_expected_version` từ version đã đọc; standalone line/nội dung mẫu dùng `document_version`; chỉ đạo dùng version riêng. Native button lưu trước rồi lấy token vừa reload để gửi transition. Giữ native save/error/dirty/back guard. Line readonly khi report không còn draft/returned; backend vẫn kiểm quyền độc lập.

## Cá nhân hoàn toàn trên web

Nhân viên mở nghĩa vụ → Lập báo cáo → chọn người nhận hợp lệ → Đưa kế hoạch vào báo cáo → nhập kết quả/minh chứng → Lưu nháp → Xem trước native modal → Gửi. Thiếu reviewer hợp lệ bị backend chặn, không thành inbox vô chủ. Hạn công việc tách hạn nộp; trạng thái công việc tách trạng thái report. Actual chưa có nguồn khác actual0 đã biết qua `quantity_known`.

Nút Chờ tôi rà soát mở native inbox đúng reviewer/state. Nhận xét là bản ghi bất biến riêng: quản lý chọn đầu việc/đánh giá/audience; nhân viên thêm phản hồi bằng chọn Nhận xét cha. Không gửi `review_ids` sửa report qua x2many. Nhận xét công bố khác nội bộ. Trả lại/điều chỉnh mở reason wizard có version; tác giả sửa bản hiện hành rồi gửi lại, snapshot cũ giữ nguyên. Preview/snapshot/so sánh hai bản gần nhất dùng HTML an toàn từ server, không raw JSON. Export Word/Excel/PDF có nút trên report; snapshot có xuất đúng bản lịch sử.

## Responsive, trạng thái và kiểm chứng

Desktop sidebar cố định trong grid;≤800px thành drawer, Escape đóng, Tab trap và trả focus về nút mở. Mobile controls≥44px; bảng chỉ cuộn trong renderer. `prefers-reduced-motion` bỏ animation; bình thường bar reveal450ms một lần khi data mới, hover không đổi kích thước.

Dashboard tách loading/empty/error/access; lỗi làm bỏ data cũ, SessionExpired/Forbidden được rethrow về native session dialog. Scope chỉ nhận danh sách backend có quyền, không cache xuyên session.

Kiểm đã chạy: XML parse, `node --check`, `git diff --check`; harness actual-source Node8 assertions chart/concurrency đạt. Có HOOT source cho denominator/domain/null, stale response/session và token form, nhưng không gọi là HOOT PASS khi chưa chạy browser runner. Bằng chứng thực tiếp tục tại `.local/corp-report001/ui/`; chưa có browser result tại thời điểm ghi mục này. Năm viewport dự kiến1440×900,1366×768,768×1024,390×844,375×812; emulation không là thiết bị thật.

Inventory đầy đủ tại [TP_TABLE_FILTER_INVENTORY.md](TP_TABLE_FILTER_INVENTORY.md), mục CORP-REPORT-001. Technical verification, visual feedback, business acceptance và main authorization ghi riêng ở [acceptance](../demo/CORP_REPORT_001_ACCEPTANCE.md).

Bộ chọn reviewer dùng RPC eligible-reviewer của chính report đã lưu và native record.update ID; person single/multi dùng tp.report.people.get_options với purpose cố định, server search tối đa100. Không mở res.users toàn công ty hoặc nối bằng tên. Mọi picker vẫn kiểm scope lúc save.
