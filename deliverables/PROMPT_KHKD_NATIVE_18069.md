# Prompt triển khai KH-KD trực tiếp trên Odoo 18069

Ngày soạn và bổ sung yêu cầu giao diện 06/11/2026, CHG-20261106-004; bổ sung bộ dữ liệu sát thực tế lưu database và phương án dọn riêng theo CHG-20261106-005, chốt cơ cấu260record tại CHG-20261106-006. Copy toàn bộ phần dưới vào phiên AI thực thi có quyền truy cập source. Dùng một phiên thực thi cho các lô phụ thuộc nhau; không chạy song song với phiên đang sửa TP Contracts hoặc nền native trên cùng checkout.

```text
Làm việc trong C:\TANPHAT ONE.
Task: KD-NATIVE-001 — Dựng không gian nghiệp vụ phòng Kế hoạch Kinh doanh trên native Odoo để trình bày trực tiếp với lãnh đạo.

MỤC TIÊU VÀ QUYỀN THỰC THI
Người dùng yêu cầu triển khai, không chỉ lập kế hoạch. Kết quả cuối phải mở và sử dụng được tại http://127.0.0.1:18069/odoo, database dev hiện hành tp_tanphat_dev sau khi kiểm tra đúng cấu hình/ownership.
Được bổ sung custom addon, giao diện native và dữ liệu giả có nguồn gốc rõ; được nâng cấp đúng addon liên quan trên dev sau khi test đạt và có backup phục hồi được. Không hỏi lại quyền đưa bản trình diễn đã kiểm tra lên 18069. Đây là cho phép trình diễn trên dev, chưa phải nghiệm thu nghiệp vụ, vận hành thật hoặc thay quy chế công ty.
Người dùng yêu cầu nhiều dữ liệu tự tạo sát thực tế và lưu trực tiếp database để dùng lâu dài, sau này có thể dọn riêng. “Dữ liệu thật tự tạo” được hiểu là bản ghi database thật có nội dung tổng hợp, không phải hồ sơ hoạt động có thật của công ty. Áp dụng mục7A–7C; không chỉ đổ JSON vào frontend, dùng dữ liệu tạm mất sau restart hoặc chỉ tạo3 hồ sơ để chụp ảnh.
Thực hiện theo các lô bên dưới. Đừng chỉ thêm menu, trang tĩnh, số liệu hardcode hoặc nút không hoạt động rồi báo hoàn tất.
Không commit/push; không sửa odoo/ hoặc addons/; không tách frontend React hay tạo một cổng demo mới làm đầu ra chính.

BASELINE ĐÃ ĐƯỢC AUDIT
UI-CTR-NATIVE-001a đã đạt TECHNICAL_ACCEPTED_TEST_ONLY theo CHG-20261106-003: Odoo107/107, native browser42/42, runner18/18. Đọc docs/reviews/UI_CTR_NATIVE_001A_INDEPENDENT_AUDIT.md và implementation report; dùng lại model/action/wizard/24 AT, không viết lại luồng hợp đồng hoặc quay về sửa đặc tả D1/D2 đã đạt.
Đây là bằng chứng trên test18169, không phải native contract đã được nâng cấp trên dev18069. Lần kiểm hiện hành dev vẫn dùng tp_contract20.0.1.1.0, test20.0.1.2.0; phải kiểm lại runtime trước thao tác. Code dùng chung checkout nên không tùy tiện restart dev để nạp code mới trước backup và nâng cấp có kiểm soát.
Nếu bàn giao hiện hành đã có batch mới sau CHG-20261106-004, đọc delta và tiếp tục đúng phạm vi, không reset về số phiên bản hoặc hash lịch sử.

1. PREFLIGHT VÀ BÀN GIAO
Đọc AGENTS.md; docs/PROJECT_STATUS.md; docs/CHANGELOG.md; docs/AI_CHANGE_WORKFLOW.md; docs/AI_COORDINATION_WORKFLOW.md; docs/DECISIONS.md; docs/ROADMAP.md.
Đọc các tài liệu phù hợp trong docs/architecture/:
- TP_PRODUCT_NAMING.md và TP_NATIVE_ODOO_DIRECTION.md.
- TP_KD_WORKFLOW_AND_PERMISSIONS.md; TP_KD_EVIDENCE_AND_ACCEPTANCE.md.
- TP_BIZ002_ACCEPTANCE_AND_READINESS.md; TP_BIZ002_INTEGRATION_AND_REPORTING.md.
- TP_PROCESS_WORKFLOWS_A_E.md và TP_PROCESS_WORKFLOWS_F_M.md.
- TP_UI_CTR_NATIVE_001_SPEC.md; RFC_TASK_001_MANAGED_TASK_PROGRESS.md.
Đọc docs/prompts/CLAUDE_UI_CTR_NATIVE_001A.md; docs/demo/NATIVE_DATA_003_CONNECTED_OPERATIONS.md; tài liệu dashboard hiện hành; ops/runbooks/BACKUP_RESTORE.md.

Kiểm git status/diff, runtime, các module thực sự installed, model/action/security/view đã có. Tài liệu cũ có chỗ ghi CTR chỉ đọc: phải ưu tiên đối chiếu source và bàn giao mới nhất, không suy trạng thái runtime từ một đoạn lịch sử.
Lập bảng ngắn chức năng — đã chạy — đã có backend — cần bổ sung — giới hạn. Không đọc/in mật khẩu, token hoặc dữ liệu nhân sự/tài chính thật.
Xác định dev/test có dùng chung source và chế độ reload/assets hay không. Nếu có, clone DB chưa đủ để gọi là thay đổi test-only: chụp baseline phục hồi trước sửa source, tránh dev tự nạp delta chưa kiểm; dùng bản source copy thuộc task cho runtime test khi cần, rồi tích hợp delta đã đạt vào checkout chính ở bước áp dev. Không reset checkout dirty hoặc mượn source/clone của phiên khác để đạt sự cô lập.
Kiểm .local/ai-workflow/active.json. Nếu là checkpoint của chính phiên được tiếp tục, tiếp tục đúng batch và bàn giao trước khi mở lô mới. Nếu của phiên khác còn hoạt động/chưa rõ ownership, không xóa, finish hộ hoặc chạy start ghi đè; báo cụ thể xung đột và làm tài liệu độc lập trong lúc chờ bàn giao. Không sửa chồng cùng model/view.
Với baseline hợp lệ, chạy ai_workflow.py start trước sửa. Mỗi lô có CHG-ID, test và finish/check riêng; không nhận thay đổi có sẵn là của mình.

2. PHẠM VI NGHIỆP VỤ
Phòng KH-KD là đầu mối cơ hội/đấu thầu, quản trị hợp đồng, kế hoạch, giao khoán, điều phối nghiệm thu và hồ sơ thanh quyết toán. Phòng chuyên môn thực hiện kỹ thuật; QT-TC/kế toán kiểm tra tài chính, hóa đơn, hạch toán và tiền theo trách nhiệm. Người có thẩm quyền quyết định/ký theo căn cứ riêng.

Luồng điển hình cần trình bày:
Cơ hội/đấu thầu → hợp đồng/phụ lục → kế hoạch thực hiện → giao khoán/thầu phụ → sản lượng → nghiệm thu → đề nghị thanh toán/đối chiếu → thanh quyết toán/lưu hồ sơ.
Có nhánh giao trực tiếp không qua thầu; tạm ứng trước nghiệm thu; nghiệm thu và thanh toán nhiều đợt. Không ép mọi hồ sơ qua một chuỗi cứng.
Thêm nhiệm vụ thường xuyên: kế hoạch sản lượng/doanh thu tháng-quý-năm; hồ sơ năng lực/chứng chỉ; theo dõi thương hiệu/truyền thông được giao; báo cáo quản trị tháng. Không biến phần truyền thông thành một dự án website hoặc mạng xã hội mới.

2A. YÊU CẦU GIAO DIỆN VÀ THAO TÁC BẮT BUỘC
Đầu ra là không gian làm việc có hồ sơ và thao tác backend thật trên dữ liệu giả. Người trình bày có thể tự tạo một hồ sơ mới ngoài dữ liệu seed, sửa, lưu, mở lại và thực hiện bước tiếp theo; không phụ thuộc một đường bấm hardcode dành riêng cho buổi diễn.
Trước code, viết bản thiết kế ngắn trong docs/ui/KD_NATIVE_001_DESIGN.md: bản đồ màn hình, bố cục sơ bộ, màu/chữ/khoảng cách, trường chính, nút theo state/capability và cách dùng trên điện thoại. Áp dụng skill frontend-design nếu có. Theo nhận diện và nền Odoo/TANPHAT ONE hiện hữu; tùy biến có mục đích, không tạo bộ giao diện hoặc font tải ngoài làm điều kiện chạy. Bản thiết kế này là đầu vào thực thi, không phải một vòng xin xác nhận mới cho những lựa chọn giao diện thông thường.

Màn hình Tổng quan KH-KD:
- Ưu tiên công việc cần xử lý: hồ sơ chờ mình rà soát, hồ sơ bị trả lại, việc đến/quá hạn, hồ sơ thầu đến hạn, chứng chỉ sắp hết hạn.
- Có bộ lọc dự án, người phụ trách và kỳ khi phù hợp. Mỗi bộ đếm/chỉ số mở được danh sách nguồn đúng filter và scope; truy vấn tiền/count không làm lộ thông tin ngoài quyền.
- Hiển thị lối vào các nhóm công việc; có thao tác “Tạo hồ sơ” với các loại actor được phép. Không chỉ có các thẻ số lớn không bấm được.

Hồ sơ dự án là điểm nhìn tổng hợp:
- Nhìn thấy mã, khách hàng, đơn vị/phòng chủ trì, người phụ trách, giai đoạn và mốc/hạn chính.
- Các nhóm thông tin: tổng quan, hợp đồng/phụ lục, kế hoạch/WBS, giao khoán, sản lượng/nghiệm thu, đề nghị thanh toán, nghĩa vụ/hồ sơ còn thiếu. Dùng tab/smart button/view phù hợp, không dồn mọi trường vào một form dài.
- Từ dự án tạo được hồ sơ con đúng quyền, tự điền đúng project/company; có thể mở chi tiết và quay lại. Backend vẫn kiểm liên kết, không chỉ dựa vào default/context của giao diện.
- Tiến trình tổng hợp chỉ phản ánh trạng thái hồ sơ nguồn; không ép dự án chỉ có một hồ sơ hoặc chỉ được đi qua tám bước một lần. Có thể nhiều hợp đồng/đợt thực hiện song song.

Danh sách và biểu mẫu:
- List/search/group/filter cho tác nghiệp; Kanban cho pipeline cơ hội hoặc hồ sơ có trạng thái phù hợp. Kéo thả chỉ bật nếu gọi đúng action được bảo vệ; không cho đổi state bằng write trực tiếp.
- Cột dễ đọc: mã/tên, dự án/khách hàng, người phụ trách, trạng thái, hạn/kỳ và cảnh báo. Tiền chỉ hiển thị theo grant; ghi rõ đơn vị và căn cứ, không dùng màu làm dấu hiệu duy nhất.
- Nút đặt tên theo việc: “Tạo mới”, “Lưu nháp”, “Gửi rà soát”, “Trả lại”, “Mở bản sửa”, “Gửi lại”; tên gọi nhất quán với backend hiện hữu. Actor không có quyền không thấy action ghi; actor đúng quyền hiểu được điều kiện còn thiếu theo thông báo an toàn.
- Trả lại có lý do, thấy được lý do và lần trình trước khi sửa. Lịch sử có người thực hiện, thời điểm và chuyển trạng thái; không đưa số tiền vào lịch sử mà actor metadata-only đọc được.
- Kiểm lỗi trường bắt buộc, ngày/kỳ, liên kết sai, phiên bản cũ và thao tác lặp; thông báo tiếng Việt hướng dẫn bước khắc phục. Không tự thử lại thao tác ghi sau hết phiên hoặc che lỗi backend bằng thông báo thành công.
- Có trạng thái đang tải/chưa có dữ liệu/lỗi tải thích hợp, giữ thay đổi chưa lưu theo cơ chế native. Làm rõ cách hủy thao tác trong form, không có nút giả.
- Lưu trữ/xóa nháp chỉ khi policy hiện có cho phép và không có tham chiếu cản trở; hồ sơ đã gửi/chốt không xóa vật lý. Không mở quyền unlink hàng loạt để tạo cảm giác đủ CRUD.

Chất lượng trình bày:
- Rõ thứ bậc tiêu đề, trạng thái, dữ liệu và action chính; ít trang trí, không làm lại giao diện marketing.
- Ưu tiên tài nguyên/màu/chữ hiện hữu, đọc tốt tiếng Việt, có hover/focus phản hồi thao tác, giảm motion theo hệ điều hành.
- Desktop có thể đọc bảng và hồ sơ cạnh nhau khi phù hợp; mobile ưu tiên nội dung/action cần thiết, dialog không vượt màn hình, touch target khoảng44px và không tràn ngang toàn trang. Bảng rộng được cuộn cục bộ có chỉ dẫn.

2B. MA TRẬN ĐẦU RA ĐỂ NGHIỆM THU
Lập docs/demo/KD_NATIVE_001_ACCEPTANCE.md trước implementation; mở rộng bảng dưới thành test ID, actor, tiền điều kiện, thao tác, kết quả, evidence và môi trường. Mỗi dòng phải có kết luận riêng, không dùng một ảnh Home làm bằng chứng cho cả hệ thống.

| Nhóm nghiệp vụ | Giao diện và thao tác tối thiểu cần đạt | Phân biệt bắt buộc |
| --- | --- | --- |
| Cơ hội/hồ sơ thầu | Tạo/sửa cơ hội, liên kết khách hàng/dự án; theo dõi hạn/checklist/hồ sơ thầu và tình trạng chuẩn bị/nộp theo action đã đặc tả | Nhánh thầu và giao trực tiếp; kết quả khai báo chưa xác minh không phải trúng thầu đã có quyết định |
| Dự án | Mở hồ sơ tổng hợp, lọc/mở/tạo hồ sơ con theo quyền, đi và quay về đúng dự án | Cùng project.project, không nhân đôi dự án giữa hai menu |
| Hợp đồng/phụ lục | Tạo/sửa nháp, gửi, actor khác trả lại có lý do, mở bản sửa, sửa và gửi lại; xem lần trình/lịch sử | Dùng lại UI001a; bản nháp/đang rà soát chưa phải đã ký/có hiệu lực |
| Kế hoạch thực hiện/WBS | Xem cây/nhóm đầu việc và mốc; actor fixture có quyền hợp lệ tạo/sửa/giao việc theo policy đã có; liên kết hợp đồng/đầu ra | Không nới write managed-task/TASK-001; ghi riêng thao tác nào còn bị policy chặn |
| Giao khoán | Tạo/sửa/gửi/trả lại/sửa gửi lại hồ sơ khoán nội bộ/thầu phụ; cha-con và nguồn hợp đồng đúng scope | Cấp2 không cộng lại vào tổng công ty; hồ sơ khoán chưa phải giao khoán đã có thẩm quyền duyệt |
| Sản lượng | Tạo/sửa/gửi/trả lại/sửa gửi lại hồ sơ kết quả theo kỳ/đợt, liên kết task/phạm vi và nguồn khoán/hợp đồng | Sản lượng tự khai/đã rà nội bộ không thành nghiệm thu bên ngoài |
| Nghiệm thu | Tạo/sửa/gửi/trả lại/sửa gửi lại hồ sơ đợt nghiệm thu; mở được sản lượng/phạm vi liên quan | Đề xuất/đang rà nội bộ khác biên bản được bên có thẩm quyền xác nhận |
| Đề nghị thanh toán/đối chiếu | Tạo/sửa/gửi/trả lại/sửa gửi lại hồ sơ đề nghị, xem hạn/đợt/nguồn nghiệm thu hoặc căn cứ tạm ứng; mở chứng từ liên quan khi có quyền | Đề nghị khác phê duyệt và tiền đã trả; không bắt mọi tạm ứng phải có nghiệm thu |
| Thanh quyết toán/nghĩa vụ | Xem tổng hợp, lọc và mở hồ sơ còn thiếu/nghĩa vụ tồn; cập nhật checklist nội bộ có lịch sử theo quyền | Không nút xác nhận thanh lý pháp lý; kết thúc công việc vẫn có thể còn giữ lại/công nợ/bảo hành |
| Kế hoạch định kỳ | Tạo/sửa kế hoạch tháng/quý/năm, nhập mục tiêu có quyền và xem đối chiếu đúng nguồn/kỳ | Kế hoạch không phải doanh thu kế toán; thiếu căn cứ thì giữ chưa xác nhận |
| Năng lực/chứng chỉ | Tạo/sửa hồ sơ giả, theo dõi hạn, tìm theo phạm vi và mở nơi đang sử dụng trong hồ sơ thầu | Quyền dữ liệu cá nhân/tệp; không tạo chứng chỉ hoặc chữ ký giả có vẻ hợp pháp |
| Truyền thông/báo cáo tháng | Theo dõi nhiệm vụ và đầu ra truyền thông bằng task chuẩn có quyền; mở báo cáo và đi tới hồ sơ nguồn | Không tạo hệ thống xuất bản mới hoặc tự gửi ra ngoài |

Không tự hứa hoàn tất mọi policy của công ty trong task này. Nếu một dòng bị chặn bởi policy có thực, ghi rõ thao tác/gate bị chặn và hoàn tất phần độc lập an toàn; không thay bằng nút giả, không công bố toàn bộ KD-NATIVE-001 hoàn tất khi còn dòng bắt buộc chưa đạt. Giới hạn nghiệp vụ pháp lý/tài chính nêu ở cột cuối không phải lý do bỏ chức năng quản trị hồ sơ đã được cho phép.

3. LÔ A — WORKSPACE KH-KD VÀ LIÊN KẾT ĐÃ CÓ
Giữ Home TANPHAT ONE hiện tại. Thêm một điểm vào rõ ràng “Kế hoạch Kinh doanh”, hiển thị theo quyền.
Menu theo công việc:
- Tổng quan.
- Cơ hội và hồ sơ thầu.
- Hồ sơ dự án.
- Hợp đồng và phụ lục — TP Contracts.
- Kế hoạch và công việc.
- Giao khoán và thầu phụ.
- Sản lượng và nghiệm thu.
- Đề nghị thanh toán và đối chiếu.
- Năng lực và chứng chỉ.
- Báo cáo KH-KD.
Chỉ đưa menu vào bản bàn giao khi có dữ liệu và thao tác tương ứng; không để mục rỗng cho đủ danh sách.
Ưu tiên list/form/search/group/filter và smart button chuẩn Odoo; OWL/QWeb/SCSS khi cần. Nếu có skill thiết kế giao diện phù hợp thì đọc và áp dụng. Tiếng Việt dễ hiểu, giữ TANPHAT ONE và các tên phân hệ TP đã chốt; tương thích desktop và điện thoại, hỗ trợ bàn phím, focus rõ và giảm chuyển động.
Không xây lại Home, login/session, React shell hoặc cơ chế quyền.
Trong hồ sơ dự án, có phần tổng hợp và smart button sang cơ hội, hợp đồng, công việc, giao khoán, sản lượng, nghiệm thu và đề nghị thanh toán; các nút chỉ xuất hiện cho hồ sơ/chức năng có thật và đúng quyền. Từ nguồn có đường quay lại dự án; bộ lọc mặc định giữ đúng dự án đang trình bày.
Cơ hội/hồ sơ thầu phải theo dõi được khách hàng, nguồn, phạm vi/gói thầu, hình thức thầu hoặc giao trực tiếp, người phụ trách, hạn, checklist, tình trạng chuẩn bị/nộp và kết quả có căn cứ. Tái sử dụng CRM, chỉ bổ sung model hồ sơ thầu riêng khi inventory và đặc tả cho thấy cần; không tạo một CRM thứ hai hoặc hệ thống đấu thầu điện tử mới.

Tái sử dụng:
- res.partner cho khách hàng/đối tác.
- crm.lead cho cơ hội; tp_crm_project_bridge cho liên kết dự án hiện có.
- project.project có tp_managed cho TP Projects. Project và TP Projects không phải hai kho dự án.
- project.task cho WBS/công việc; cha-con là phân rã đầu việc và kết quả bàn giao. Không tự thêm một model task cạnh model chuẩn.
- hr.department, hr.employee và tp_organization cho tổ chức. TADIC/TACICO là đơn vị nội bộ, không tạo pháp nhân riêng.
- account.move, expense, timesheet và liên kết analytic đang có, đúng scope/quyền từng nguồn.

4. LÔ B — HỢP ĐỒNG NATIVE VÀ KẾ HOẠCH CÓ THAO TÁC
Tái sử dụng UI-CTR-NATIVE-001a đã đạt audit CHG-20261106-003. Chỉ đối chiếu delta hiện hành và kiểm regression khi tích hợp; không dựng hợp đồng thứ hai cạnh tp_contract hoặc lặp lại vòng correction đặc tả đã đạt.
Phải thao tác được: tạo/sửa nháp → gửi rà soát → reviewer trả lại với lý do → mở bản sửa theo backend → sửa → gửi lại.
Giữ draft, in_review, returned và cơ chế version/submission/audit/idempotency/concurrency hiện có. Bản returned bị đóng băng phải qua begin_rework theo backend; không sửa đè bản đã gửi. Không viết trực tiếp review_state. Không mở review_complete, BASE, ký, hiệu lực hoặc hủy nếu slice hiện hành chưa cho phép.
Kiểm restrictions owner/company/project của wizard và model con; kiểm tiền khi revoke/expiry/assignment thay đổi. Giữ nguyên 24 AT của spec, gồm AT-17/G8 hết hạn tự nhiên. Không giảm test để công bố đạt; nếu có lỗi quyền thì không triển khai nhánh lỗi lên dev. Không tự thay policy G7 ngoài phạm vi.
Kế hoạch dự án: đầu việc/WBS, phòng phụ trách, một người chịu trách nhiệm chính, người phối hợp, hạn, đầu ra, mốc bàn giao và liên kết dự án/hợp đồng. Không đổi TASK-001 bằng cách mở write toàn project.task. Nếu policy chưa được chốt, giữ nguyên deny và trình bày bằng actor giả đang có quyền hợp lệ; nêu hạn chế. Không dùng toàn quyền admin làm bằng chứng nhân viên được thao tác.

5. LÔ C — BỔ SUNG HỒ SƠ GIAO KHOÁN, SẢN LƯỢNG, NGHIỆM THU VÀ ĐỀ NGHỊ THANH TOÁN
Đối chiếu inventory trước khi chọn addon/model. Dùng model có kiểu nghiệp vụ cho từng hồ sơ, không nhét mọi thứ vào note hoặc một bảng giao dịch tiền chung. Viết đặc tả lô nhỏ và test trước khi triển khai; chỉ custom_addons và tooling liên quan.
Chia C thành C1 giao khoán, C2 sản lượng, C3 hồ sơ nghiệm thu, C4 đề nghị thanh toán/đối chiếu; mỗi phần làm model/action → security → native UI → test → handoff trước phần phụ thuộc tiếp theo. D làm tương tự theo kế hoạch định kỳ → năng lực/chứng chỉ → báo cáo. Tiếp tục tuần tự tới đầu ra đã giao; không dừng ở workspace/menu rồi coi là xong, không dồn mọi domain vào một thay đổi lớn khó kiểm.
Mỗi hồ sơ phải có mã, dự án, company, người/phòng phụ trách, ngày, kỳ, phạm vi hoặc dòng hợp đồng liên quan, trạng thái hồ sơ, liên kết trước/sau, lịch sử và version khi cần. Số tiền/currency/basis phải tách khỏi metadata theo cơ chế quyền hiện có. Không sao chép số tiền nhạy cảm sang chatter/compute/related/export để né grant.

Giao khoán: tách nội bộ và thầu phụ; cấp 1 của công ty và cấp 2 thuộc khoán cha. Liên kết task/phòng/đối tác và phạm vi. Tổng công ty không cộng khoán cấp 2 lần nữa; vượt khoán cha cảnh báo theo tài liệu, không tự đặt chính sách chặn cứng chưa được chốt.
Sản lượng: khối lượng/kết quả đã thực hiện theo kỳ và căn cứ, không tự gọi là đã được khách hàng nghiệm thu.
Nghiệm thu: phạm vi, đợt, số lượng/giá trị theo quyền, đối tượng nghiệm thu, tình trạng hồ sơ và căn cứ. Tách rà soát nội bộ khỏi xác nhận chuyên môn và biên bản bên ngoài.
Đề nghị thanh toán: loại thu/chi/tạm ứng nếu áp dụng, đối tác, hợp đồng/đợt nghiệm thu, số tiền đề nghị, hạn dự kiến, hồ sơ kèm và tình trạng đối chiếu. Không biến nút gửi hồ sơ thành đã duyệt hoặc đã trả tiền.
Luồng thao tác tối thiểu cho các hồ sơ mới: lập/sửa nháp → gửi rà soát → trả lại có lý do → sửa/gửi lại; chỉ thêm kết luận rà soát nếu có đặc tả actor/guard rõ, kết luận ấy không tạo thẩm quyền pháp lý.
Chính sách chưa được công ty chốt giữ proposed/unconfirmed. Không vì Q2 người thật còn mở mà bỏ toàn bộ phần trình diễn bằng fixture; không dùng fixture để mở vận hành thật.
Thanh quyết toán/lưu: màn hình tổng hợp nghĩa vụ, hồ sơ còn thiếu, giữ lại/công nợ nếu có nguồn và lịch sử. Chưa có căn cứ thì không cung cấp nút xác nhận thanh lý hợp pháp hoặc tự xóa nghĩa vụ tồn.

6. LÔ D — KẾ HOẠCH ĐỊNH KỲ, NĂNG LỰC VÀ BÁO CÁO
Kế hoạch tháng/quý/năm: mục tiêu sản lượng/doanh thu, kỳ, owner và nguồn đối chiếu. Phân biệt doanh thu kế hoạch với doanh thu kế toán. Kế hoạch chưa được xác nhận hiển thị tình trạng hồ sơ phù hợp.
Năng lực/chứng chỉ: tổ chức/cá nhân, loại chứng chỉ, phạm vi, ngày hiệu lực/hết hạn, owner cập nhật, dự án/hồ sơ thầu sử dụng. Dữ liệu cá nhân theo quyền; minh họa bằng người giả, không công khai hồ sơ thật.
Truyền thông: có thể dùng project.task/hoạt động chuẩn để theo dõi công việc và tài liệu bàn giao, không tạo hệ thống đăng bài mới.
Báo cáo KH-KD phải drill down đến record nguồn: pipeline cơ hội; hồ sơ cần xử lý/trả lại; hợp đồng dự thảo; hợp đồng có hiệu lực khi thật sự đủ căn cứ; kế hoạch so với thực hiện; giao khoán; sản lượng; nghiệm thu; đề nghị thanh toán; chứng chỉ sắp hết hạn.
Các chỉ số tiền phải có nhãn và nguồn rõ: giá trị dự thảo/giá trị hiệu lực, sản lượng, nghiệm thu, hóa đơn nháp/đã ghi sổ, số tiền đề nghị, tiền thực thu/chi, tạm ứng và giữ lại. Không cộng giá trị dự thảo vào hợp đồng hiệu lực. Không tính request approved là paid. Không dùng khoảng cách giữa các chỉ tiêu làm lợi nhuận.
Giữ dashboard hiện có, chỉ mở rộng phần phục vụ KH-KD với regression phù hợp; không tự ghi đè template/binding cũ để ép khớp. F-DASH-01/02 chỉ áp nếu nằm trong dependency thực tế đã kiểm, không biến task này thành sửa mọi dashboard.
Chưa có dữ liệu phải ghi “Chưa có dữ liệu” hoặc “Chưa có chứng từ ghi sổ”; không dựng tiền đã thu giả trong KPI thật. Phân biệt chưa biết, zero và người dùng không có quyền; count/aggregate cũng không được rò rỉ.

7. DỮ LIỆU TRÌNH DIỄN
Chỉ dữ liệu giả. Ưu tiên liên kết các dự án/đối tác mẫu hiện hữu nếu inventory xác minh đúng. Không đổi giá trị hoặc trạng thái mẫu cũ chỉ để đạt một câu chuyện mới.
Phân vai minh họa: chủ trì KH-KD lập/sửa/gửi; người rà soát được chỉ định trả lại và không tự rà hồ sơ mình gửi; hỗ trợ xem/cập nhật metadata theo capability được cấp nhưng không mặc nhiên có tiền; QT-TC/lãnh đạo xem tài chính đúng phạm vi fixture. Dùng capability backend tường minh, không suy quyền từ tên chức danh, không mở màn hình quản trị grant. Đây là phân vai cho kịch bản giả, không phải bổ nhiệm hoặc nghiệm thu Q2 người thật.
Cần 3 tình huống:
A. Một dự án xuyên suốt: cơ hội → dự án → hợp đồng → WBS/kế hoạch → khoán → sản lượng/nghiệm thu → đề nghị thanh toán → tổng hợp hồ sơ/nghĩa vụ. Các bước chưa đủ căn cứ là hồ sơ dự kiến/đang rà soát, không giả thành đã có hiệu lực.
B. Một hợp đồng có nội dung thiếu để thao tác gửi → trả lại có lý do → mở bản sửa → gửi lại. Người gửi và reviewer là hai actor fixture hợp lệ theo backend.
C. Một hồ sơ cần xử lý: gần hạn/chậm hạn/chứng chỉ sắp hết hạn/thiếu hồ sơ hoặc số liệu cần đối chiếu. Ngưỡng cảnh báo minh họa phải cấu hình/ghi là minh họa, không gán thành quy định công ty.
Tên tự nhiên, mã duy nhất, quan hệ bằng FK. Lưu namespace/provenance/manifest ngoài dữ liệu thật; chạy seed lại không trùng hoặc đổi password. Không xóa bản ghi hiện có và không dựng bản demo cũ tp_demo_workspace.
Không tự bịa URL/quyết định BASE, chữ ký hoặc tài liệu đã xác minh. Tệp mẫu nếu cần phải ghi rõ là minh họa, không có chữ ký giả. Upload thực hiện theo gate riêng; không bật upload hợp đồng ngoài spec để kịp buổi trình bày.
Không post hóa đơn, không ghi nhận thu/chi/reconcile vào chứng từ dev hiện có. Khi chưa có nguồn tiền thật hợp lệ, trình bày kế hoạch/đề nghị và tình trạng đối chiếu. Kế toán ghi sổ và luồng tiền thật là slice sau.
Giữ dữ liệu minh họa truy nguyên được; hướng dẫn người trình bày nói rõ dữ liệu dùng để kiểm tra quy trình. Không tuyên bố đây là kết quả hoạt động thực tế của công ty.

7A. QUY MÔ VÀ TÍNH SÁT THỰC TẾ
Mục tiêu là khoảng260 bản ghi nghiệp vụ/đầu việc, không tính log và dòng con kỹ thuật. Đây là cơ cấu mục tiêu sau khi các domain tương ứng triển khai; báo số thực tạo/reuse/missing theo từng model, không bịa model/state hoặc thêm dữ liệu vô nghĩa để đủ số. Giữ mã lô kỹ thuật ổn định như KD_NATIVE_001_REALISTIC_V1.

| Nhóm | Mục tiêu | Nội dung |
| --- | --- | --- |
| Khách hàng/đối tác | 12 | Khách hàng, đối tác khảo sát/thiết kế và nhà thầu phụ giả lập; cùng res.partner, không tạo mỗi module một khách hàng |
| Cơ hội/gói thầu | 12 | Cơ hội đang tìm hiểu, đang chuẩn bị hồ sơ, đã nộp theo mô hình có thật; có cả thầu và giao trực tiếp |
| Dự án | 8 | Tư vấn khảo sát/thiết kế đường giao thông, cầu, hạ tầng và giám sát; các quy mô/kỳ/hạn khác nhau |
| Hợp đồng/phụ lục | 16 | 10 hợp đồng và6 phụ lục nháp/phiên bản có liên kết hợp lệ; state theo action đã có |
| WBS/công việc | 100 | Gói công việc khảo sát, thiết kế, phối hợp, kiểm tra, bàn giao; có cha-con, owner, hạn và đầu ra; gồm vài việc truyền thông/báo cáo |
| Hồ sơ giao khoán | 16 | Nội bộ/thầu phụ, cấp1/cấp2; phạm vi và tổng không trùng |
| Hồ sơ sản lượng | 24 | Nhiều kỳ/đợt trên cùng dự án; có hoàn thành một phần, chưa đối chiếu, cần bổ sung |
| Hồ sơ nghiệm thu | 16 | Nhiều đợt, nguồn sản lượng và phạm vi; tình trạng hồ sơ/rà soát đúng quyền |
| Đề nghị thanh toán/đối chiếu | 20 | Tạm ứng, theo đợt và hồ sơ cần bổ sung; chưa biến thành đã thanh toán hoặc chứng từ đã ghi sổ |
| Kế hoạch định kỳ | 16 | 12 kế hoạch tháng của cùng năm,3 quý chọn để đối chiếu và1 năm; kỳ/đơn vị/phạm vi không chồng số |
| Năng lực/chứng chỉ | 12 | Tổ chức/cá nhân giả lập, đang còn hạn/sắp hết hạn/đã hết hạn; không phát hành chứng chỉ giả |
| Checklist nghĩa vụ/hồ sơ | 8 | Theo dự án, có phần còn thiếu và bên chịu trách nhiệm; không tự xác nhận thanh lý |

Tên hiển thị dùng tiếng Việt tự nhiên, ví dụ dự án “Tư vấn khảo sát và lập thiết kế tuyến kết nối Khu công nghiệp An Phú”, “Khảo sát địa hình, địa chất cầu Hòa Lâm”, “Thiết kế cải tạo tuyến đường ven sông Nam Thành”. Đây là tên tình huống tổng hợp, không khẳng định công ty đã nhận các dự án này. Mã hợp đồng/gói thầu/dự án có định dạng dễ đọc, duy nhất và không chiếm lại mã thật.
Giá trị minh họa đa dạng theo quy mô, chẳng hạn350 triệu–8,5 tỷ VND; căn cứ thuế/giá trước-sau thuế ghi rõ là giả định của từng tình huống, không suy thuế suất pháp lý. Dùng monetary/Decimal và precision Odoo; không tạo số dư/lợi nhuận/tiền đã thu bằng cách lấy chênh tùy ý.
Lấy ngày hiện hành của hệ thống làm mốc rồi tạo quá hạn7ngày, đến hạn3ngày, chứng chỉ sắp hết hạn30ngày, các kỳ đã qua/hiện tại/sắp tới. Ghi các khoảng này là kịch bản minh họa, không tự gán SLA/quy định công ty. Không sửa ngày/state của dữ liệu mẫu cũ để làm số liệu mới.
Không thu thập hoặc sao chép MST, CCCD, số tài khoản, điện thoại, email cá nhân, địa chỉ hay danh tính thật vào bộ mẫu. Email nếu field bắt buộc dùng miền reserved example.invalid, trường không bắt buộc có thể bỏ trống. Cá nhân giả chỉ tạo khi thật sự cần cho quan hệ actor/chứng chỉ; không thêm hàng loạt tài khoản login hoặc thay password người đang có.

7B. PERSISTENCE VÀ TÍNH NHẤT QUÁN
Tạo record qua ORM/action hợp lệ, commit có kiểm soát sau test; hồ sơ phải còn sau refresh, đăng xuất/đăng nhập lại và restart đúng môi trường trong bước nghiệm thu. Không dùng direct SQL insert/update để né validation/quyền/workflow; seed có đặc quyền kỹ thuật không thay bằng chứng actor thường thao tác được.
Dùng chung ID khách hàng, dự án, nhân sự/đơn vị và hợp đồng giữa CRM/Project/TP Contracts/các hồ sơ mới. Có ít nhất3 dự án liên thông đầy đủ ở phạm vi quản trị hồ sơ;5 dự án còn lại phân bố hợp lý theo tình huống và giai đoạn thực tế. Không ép dự án mới có đủ nghiệm thu/thanh toán, không tạo hồ sơ không liên quan chỉ để lấp bảng.
Với contract, seed qua các action được phép để có nháp/in_review/returned/rework; không viết state đã ký/có hiệu lực bằng đặc quyền. Với domain mới, chỉ dùng state/action đã qua spec/test của lô. Chênh số lượng hợp đồng/phụ lục so nguồn thầu là bình thường khi có giải thích quan hệ, không tạo orphan.
Phải kiểm: chronology và kỳ hợp lệ, company/project xuyên suốt, phạm vi nghiệm thu theo nguồn, đề nghị không đồng nghĩa chi tiền, không cộng trùng phụ lục và khoán cấp2; unknown không thay bằng0. Dashboard/list/drilldown phải dùng cùng nguồn record và phân quyền; dữ liệu chuẩn bị cho nhiều state không được làm phát sinh chứng từ pháp lý giả.
Seed lặp lại phải idempotent theo dataset/external key: không tạo trùng, không ghi đè sửa đổi người dùng đã làm sau seed, không tự reset action để phục dựng kịch bản. Nếu record của bộ mẫu đã đổi thì giữ lại/báo drift; chỉ bổ sung record thiếu khi xác minh khóa còn phù hợp.
Trên dev chặn tác dụng phụ từ riêng thao tác seed: không gửi email/SMS/webhook, không phát hành chứng từ hoặc chạy tích hợp ngoài. Dùng cơ chế context/queue đã kiểm trong scope; không tắt hoặc thay cấu hình dịch vụ của toàn dev để làm dữ liệu. Không tự tạo hóa đơn posted, payment, reconcile hoặc chuyển tiền.

7C. NHẬN DIỆN VÀ DỌN RIÊNG SAU NÀY
Tên record không cần nhét chữ “DEMO/TEST” vào mọi tên. Tuy nhiên phải lưu provenance bền trong database bằng external IDs/registry thích hợp, kèm dataset ID và stable record key; không chỉ dựa vào tên, ghi chú, ngày tạo hoặc một file cục bộ để chọn đối tượng xóa. Khi reuse record cũ, đánh dấu referenced, tuyệt đối không nhận ownership của record đó.
Xuất manifest private theo DB/environment gồm model, ID, external key, owned/referenced, dependency và trạng thái/checksum cần thiết; hướng dẫn ghi rõ đây là dữ liệu tổng hợp. DB registry và manifest phải khớp sau khi seed; không đưa credential/dump/filestore vào Git.
Viết và kiểm thử công cụ quản lý bộ dữ liệu trước khi áp dev: inventory/verify, cleanup dry-run và apply có target/ownership guard. Không chạy cleanup apply trên dev trong task hiện tại; người dùng chỉ yêu cầu khả năng dọn sau này. Ghi lệnh thực tế và cách chọn dataset vào docs/demo/KD_NATIVE_001_DATASET.md.
Dry-run phải liệt kê record thuộc lô, record reuse và liên kết từ bên ngoài; không chọn xóa theo prefix tên hoặc chỉ theo project_id. Không xóa DB/module, không truncate bảng, không tắt FK hoặc dùng SQL cascade. Đối tác/phòng ban/người dùng/chứng từ đã có và record không owned không nằm trong phạm vi dọn.
Áp dụng policy đã có: chỉ unlink nháp được phép và không có tham chiếu cần giữ; với hồ sơ đã trình/chốt/audit hoặc bị chính sách chặn thì archive khi model hỗ trợ, giữ nguyên lịch sử và nêu rõ phần tồn. Không viết đường bypass xóa log, hoàn tác state hoặc hủy chứng từ để cam kết “xóa sạch một nút”. Nếu model chưa có cơ chế loại khỏi tập làm việc thì báo giới hạn, không giả định thêm active=False là đủ.
Nếu record ngoài lô đang tham chiếu tới record mẫu hoặc người dùng đã phát triển hồ sơ thành dữ liệu vận hành, dừng cleanup phần liên quan và báo dependency cụ thể. Archive không được coi là xóa: xác minh báo cáo/aggregate/drilldown theo semantics của từng model; không sửa công thức tài chính chỉ để giấu số. Chỉ restore snapshot khi đã đánh giá việc giữ mọi thay đổi sau snapshot; không xem restore toàn DB là cách dọn mặc định.
Test trên clone: seed2lần không trùng/không đổi password, giữ chỉnh sửa sau seed, registry/manifest khớp, persistence qua phiên/restart, cleanup dry-run không ghi dữ liệu, cleanup chỉ chạm owned đúng policy, tham chiếu ngoài lô bị chặn và dữ liệu baseline vẫn nguyên. Báo thực tế số record unlink/archive/retained khi diễn tập; không xóa bộ mới trên dev sau khi bàn giao.

8. TEST VÀ ĐƯA LÊN 18069
Trước thay dev, tạo snapshot DB + filestore + cấu hình private + toàn bộ source đang chạy, kể cả uncommitted và file mới, có manifest/checksum. Tool OPS-001 cũ có thể từ chối source dirty và chỉ lưu committed source: đọc điều kiện thực tế, dùng tooling snapshot/clone đã có phù hợp, không commit/reset/stash để lách. Kiểm khả năng restore vào clone owned cô lập; không dùng backup thiếu source khớp runtime.
Clone/test dùng DB/data-dir/cổng riêng, tắt SMTP/cron/tích hợp ngoài; không sửa đè clone của phiên khác. Mọi code/model/migration/seed chạy thử trên test trước. Cổng tạm để kiểm thử không thay đầu ra 18069.
Test backend: transitions dương/âm; reason; record/version bất biến sau gửi; retry/race; liên kết cùng company/project; ngoài scope/cross company bị chặn; quyền metadata/tiền/files/count/export; actor lập/review/quan sát; thu hồi và hết hạn quyền; không cộng trùng khoán và phụ lục.
Test kế toán/báo cáo: chỉ tiêu đúng nguồn/state/currency/basis; hóa đơn nháp không thành khoản đã ghi sổ/đã thu; unknown khác zero; bộ lọc và drilldown cùng scope, không hardcode số.
Test UI trên browser thật: menu → list → form → create/edit → submit → return → rework/resubmit; back/refresh/deep link, lỗi quyền/state/version; responsive 390/768/1440, không tràn ngang toàn trang; không console error bất ngờ. Chạy bằng actor thường, không chỉ admin.
Đối chiếu từng dòng ma trận2B; kiểm hồ sơ do người dùng tự tạo ngoài seed, quan hệ từ dự án tới hồ sơ con, tìm/lọc/nhóm và drilldown. Có evidence trước/sau thao tác, ghi rõ actor, code hồ sơ và môi trường; không lấy screenshot test18169 làm bằng chứng đã chạy dev18069.
Chạy Ruff, XML/assets, Odoo test đúng database/tag có số lượng test > 0; kiểm exit code và summary mới. API/OpenAPI/React chỉ kiểm phần bị thay hoặc regression cần thiết, không thay chúng nếu không có nhu cầu.
Khi lô đạt, nâng cấp đúng addon và áp seed có kiểm soát lên dev18069 theo quyền người dùng đã cho ở trên. Chỉ restart đúng process sở hữu, không dừng PostgreSQL/process không liên quan. Kiểm trước/sau dữ liệu, user/group/grant, chứng từ và blob cũ; phân loại thay đổi dự kiến và phát sinh.
Nếu lỗi, rollback đúng lô theo kế hoạch đã thử, bảo toàn dữ liệu; không drop/reset DB, không xóa toàn bộ .local, không restart mọi Python/PostgreSQL. Không công bố cả lô đạt nếu chỉ một phần được kiểm. Phần độc lập an toàn tiếp tục được thực hiện và báo rõ phần chưa đạt.
Cuối cùng giữ Odoo18069 chạy, không mở lại demo18109.

9. BÀN GIAO DÙNG ĐỂ TRÌNH BÀY
Tạo/cập nhật docs/demo/KD_NATIVE_001_PRESENTATION.md gồm:
- URL/menu thực tế của từng bước, mã record trong 3 tình huống, thông tin actor/role cần dùng; mật khẩu chỉ lưu private, không in trong báo cáo/Git.
- Kịch bản thao tác 12–15 phút: màn hình mở → nút bấm → điều cần quan sát → lời nói ngắn → kết quả mong đợi.
- Bước nào thao tác đã chạy, bước nào đọc hồ sơ/dự kiến, bước nào chưa triển khai. Không suy phần đã có từ menu hoặc một screenshot.
- Cách tạo thêm một hồ sơ nháp khi sếp yêu cầu; cách đổi actor để trình bày return/rework; cách xử lý phiên hết hạn trước buổi họp.
- Bảng chỉ số, định nghĩa, nguồn, cách kiểm tổng; danh sách gap và câu hỏi cần lãnh đạo xác nhận.
Kèm ảnh chụp các màn hình chính và bằng chứng test an toàn; tài liệu nghiệp vụ ngắn mô tả người làm, đầu vào, đầu ra và handoff.
Hoàn tất docs/ui/KD_NATIVE_001_DESIGN.md và docs/demo/KD_NATIVE_001_ACCEPTANCE.md; bảng nghiệm thu phải phản ánh riêng test và dev. Ghi tiến độ từng lô với kết quả sử dụng được sau lô, không chỉ số file hoặc số dòng code. Giao diện nhìn thấy được chưa đủ: action phải persist và mở lại đúng dữ liệu sau refresh/đăng nhập lại.
Cập nhật PROJECT_STATUS, CHANGELOG, ROADMAP và spec/workflow bị ảnh hưởng. Chỉ thêm DECISIONS cho quyết định trực tiếp có căn cứ; không tự ghi Q2/G7/ủy quyền đã được công ty xác nhận. Ghi rõ yêu cầu hiện tại cho phép trình diễn dev18069 nhưng không mở pilot thật.
Chạy git diff --check; scripts/ai_workflow.py finish --change-id CHG-YYYYMMDD-NNN --check theo kết quả thực; scripts/ai_workflow.py check.

BÁO CÁO CUỐI
1. Đã mở được gì trên 18069, URL và cách đăng nhập bằng tài khoản hiện có, không lộ mật khẩu.
2. Lô nào đã triển khai/test/áp dev; model/view/security/nguồn dữ liệu dùng lại và phần thêm.
3. 3 tình huống với mã hồ sơ và đường bấm; không ghi ID/URL đoán.
4. Test thực chạy, log, kết quả; backup/restore và bảo toàn dữ liệu cũ.
   Kèm bảng số lượng từng model thực có trên dev, dataset ID/manifest, cách kiểm provenance và hướng dẫn dry-run dọn riêng; không chỉ báo mục tiêu260 là số đã tạo.
5. Kịch bản trình bày và danh sách giới hạn còn lại.
6. Xác nhận không mở phê duyệt BASE, ký/hiệu lực, thanh toán/hạch toán thật, upload ngoài gate, grant người thật hoặc nới TASK-001 trái policy; không commit/push.
```
