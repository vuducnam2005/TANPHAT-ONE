# Kho thiết bị văn phòng — Hướng dẫn admin

Cập nhật 15/11/2026. `tp_equipment` **20.0.1.4.2** chạy trên main **18069** (CHG-20261115-004: bảng **Thiết bị & người sử dụng** hiển thị hết trên một trang, không chia 20 dòng; các bảng khác vẫn chọn 10/20/50/100 dòng mỗi trang) (CHG-20261115-003: ô tìm nhanh không phân biệt dấu, ví dụ gõ "thuy" hay "thùy" đều khớp tên ghi "Thuỳ"; thiết bị trong file nguồn chưa khớp chắc người dùng HR nằm ở **Quản trị dữ liệu → Dòng nguồn chờ bổ sung** đến khi admin xác nhận) (giao diện `EQUIP-UI-001` / `CHG-20261114-014`, bảng người sử dụng theo HR, dashboard nâng cấp và nút Quay lại `EQUIP-UI-002` / `UI-BACK-001` / `CHG-20261115-002`). Chưa nghiệm thu các giao dịch nghiệp vụ (bàn giao, sửa chữa, kiểm kê) có dữ liệu.

**Đã nhập dữ liệu thật (CHG-012, EQUIP-DATA-001):** từ hai workbook local, kho hiện có 54 hồ sơ đã đăng ký (53 thiết bị vật lý, 1 dịch vụ đường truyền), mỗi hồ sơ có một phiếu **Ghi nhận ban đầu** đã hoàn tất, cùng 1 đề xuất nháp 5 dòng. Mọi hồ sơ ở trạng thái **Chưa kiểm tra thực tế**: dữ liệu lấy từ Excel, chưa phải kết quả kiểm kê hay biên bản bàn giao. Vì vậy **Sẵn sàng cấp** bằng 0 cho đến khi admin xác nhận đã kiểm tra thực tế. Còn 10 dòng nguồn chờ bổ sung (xem phần nhập XLSX bên dưới). Cập nhật CHG-20261115-005: admin xác nhận dòng nguồn #63 thuộc HR #57 và đăng ký **TB-00055**, nay 55 hồ sơ (54 vật lý, 1 dịch vụ), 55 phiếu Ghi nhận ban đầu, còn **9** dòng chờ.

## Kho gọn — Thiết bị và Yêu cầu đề xuất (CHG-20261116-003)

Cập nhật 16/11/2026 (`CHG-20261116-007`): `tp_equipment` **20.0.1.5.1** trên main **18069** (EQUIP-SIMPLE-003 / DEC-047). Sidebar Kho chỉ còn **Thiết bị** và **Yêu cầu đề xuất**. Mở [Thiết bị](http://127.0.0.1:18069/odoo/kho-thiet-bi). Đường dẫn cũ của Tổng quan mở thẳng danh sách Thiết bị.

**Đọc danh sách.** Chọn **Tất cả**, **Đang sử dụng** (máy đang giao hoặc cho mượn một nhân viên) hoặc **Trong kho** (máy trong kho, chưa có người giữ); số bên cạnh là số máy thật của từng phạm vi. Ở hàng bộ lọc bên dưới có **Phòng ban**, **Loại thiết bị**, nút lọc nhanh **Máy in** (bấm để lọc nhanh cả **Máy in** và **Máy photocopy / đa năng**, kết hợp được với Đang sử dụng / Trong kho / Phòng ban), cùng nút **Bộ lọc** (lọc theo Người sử dụng, Tình trạng máy, Tìm nhanh). Mỗi dòng có Thiết bị (tên, loại, mã/cấu hình ngắn), Người sử dụng, Phòng ban, Trạng thái, Tình trạng máy và Ghi chú. Ô tìm kiếm không phân biệt dấu. Bấm **Xem** để mở chi tiết; menu **⋮** có Sửa thông tin, Lịch sử bàn giao, Xác nhận đã kiểm tra thực tế (với máy chưa xác minh) và In nhãn QR. Nút **Phạm vi nâng cao** mở hồ sơ nháp, ngừng quản lý, tất cả hồ sơ, dòng nguồn chờ bổ sung, lịch sử/phiếu chờ bàn giao, sửa chữa và cấu hình. Nếu đầu bảng báo "máy trong kho còn ghi người giữ — cần rà soát", mở máy đó và làm sạch dữ liệu trước; hệ thống không tự xóa người giữ và không cho gán máy đó.

**Thêm thiết bị.** Bấm **Thêm thiết bị**, điền tên, loại và các thông tin đã biết (hãng, model, serial, CPU, RAM, ổ lưu trữ, tình trạng, ghi chú, ảnh); thông tin chưa rõ thì để trống. Mã do hệ thống cấp khi lưu; máy mới vào **Trong kho**, chưa có người giữ. **Sửa thông tin** (menu ⋮) dùng cùng form ngắn và không đổi người giữ.

**Gán thiết bị** (nút **Gán** trên máy Trong kho):

1. Chọn người sử dụng (nhân viên HR đang làm việc; người đã nghỉ/lưu trữ không nhận được máy).
2. Chọn một hoặc nhiều máy. Danh sách chỉ gồm máy **trong kho, chưa có người giữ**, đang quản lý, không hỏng, không chờ bàn giao hay sửa chữa. Nếu không còn máy phù hợp, cửa sổ báo "Không có thiết bị trong kho chưa được gán".
3. Đọc tóm tắt. Với máy **Chưa kiểm tra thực tế**, tích ô xác nhận đã kiểm tra.
4. Xác nhận một lần. Hệ thống lập phiếu bàn giao và hoàn tất; máy chuyển sang Đang sử dụng.

**Đổi máy** (nút **Đổi máy** trên máy Đang sử dụng):

1. Máy đang dùng và người sử dụng được điền sẵn.
2. Chọn máy mới. Chỉ chọn được máy trong kho, chưa có người giữ; không chọn được máy của người khác hay chính máy cũ.
3. Đọc tóm tắt (máy cũ về kho, máy mới giao cho cùng người) rồi xác nhận. Một lần xác nhận làm cả hai việc; nếu có lỗi thì không thay đổi gì.

**Trả về kho** (nút **Trả kho** trên máy Đang sử dụng):

1. Kiểm danh sách máy cần trả (các máy của cùng một người).
2. Chọn lý do **Đổi máy**, **Nghỉ việc** hoặc **Thu hồi khác**; thêm ghi chú nếu cần.
3. Xác nhận: máy về Trong kho, bỏ người giữ; tình trạng kỹ thuật giữ nguyên.

Nếu hệ thống báo "Thiết bị đã có người sử dụng hoặc không còn trong kho, vui lòng chọn thiết bị khác" hoặc "Máy đã thay đổi, vui lòng tải lại", máy vừa bị thao tác ở nơi khác: đóng cửa sổ, tải lại danh sách rồi chọn lại. Bấm **Hủy**/**Đóng** thì không có gì thay đổi. Không còn thao tác "Chuyển người dùng" trực tiếp: muốn chuyển máy sang người khác thì **Trả kho** rồi **Gán**.

**Yêu cầu đề xuất.** Bấm **Mới**, chọn người đề xuất (phòng ban điền từ HR), nhu cầu **Mua mới**, **Đổi máy** hoặc **Sửa hoặc nâng cấp**, thiết bị hiện tại (khi đổi/sửa), lý do, cấu hình mong muốn và dự toán nếu đã biết, rồi bấm **Gửi**. Gửi chỉ chuyển hồ sơ sang rà soát: hệ thống **không** tự duyệt, mua, nhập kho hay gán máy. Ghi nhận duyệt ngoài, hủy, in và lập phiếu nhập/bàn giao/sửa đã ẩn khỏi màn này.

**Mức kiểm chứng:** các thao tác trên mới được kiểm qua giao diện đến bước mở cửa sổ rồi **Hủy**, cùng các lần gọi backend bị từ chối có chủ đích; **chưa** thực hiện một lần gán, đổi, trả hay gửi đề xuất thật. Khi sẵn sàng, admin tự xác nhận luồng nghiệp vụ trên một máy cụ thể (xem [acceptance](EQUIP_001_ACCEPTANCE.md)).

## Mở và đọc tổng quan

> Từ CHG-20261116-003 sidebar không còn Tổng quan, Thiết bị tồn kho và Quản trị dữ liệu. Các mục dưới đây mô tả giao diện 20.0.1.4.x, giữ để tra cứu; màn nâng cao mở qua **Phạm vi nâng cao**.

Đăng nhập bằng tài khoản internal active có quyền quản trị hệ thống tại [TANPHAT ONE](http://127.0.0.1:18069/odoo), chọn thẻ **Kho thiết bị văn phòng**. Sidebar dùng menu Odoo và tài khoản chung gồm **4 mục chính**: **Tổng quan**, **Thiết bị & người sử dụng**, **Thiết bị tồn kho** và **Đề xuất mua thiết bị**, cùng nhóm thu gọn **Quản trị dữ liệu** ở cuối thanh trái (mở khi cần thao tác bàn giao, phiếu nhập, sửa chữa, kiểm kê, nhập XLSX hoặc cấu hình danh mục). Trong **Quản trị dữ liệu** có thêm **Thiết bị dùng chung & chưa xác định người** (thiết bị đặt tại phòng ban/vị trí hoặc chưa ghi người giữ) và **Tất cả hồ sơ thiết bị** (mọi hồ sơ, gồm dịch vụ và hồ sơ ngừng quản lý). HR/HEAD/nhân viên/kỹ thuật không phải admin không có quyền mở kho. Chọn đúng company trước thao tác. Các liên kết thiết bị/người/phòng/vị trí/phiếu phải cùng company hoặc target dùng chung, kể cả khi bật nhiều company.

Tổng quan có header gồm bộ lọc **Phòng ban**, **Vị trí**, nút **Lọc thêm** (chọn khoảng ngày mua/nhận), **Áp dụng**, **Làm mới** và **Xuất Excel**. Ngày lọc là ngày đã khai báo của hồ sơ hiện tại, không phải tồn kho lịch sử. Bên dưới là **4 thẻ KPI màu**: **Tổng thiết bị** (xanh navy), **Đang sử dụng** (teal, gồm giao nhân viên và dùng chung), **Trong kho** (xanh dương) và **Đề xuất đang mở** (tím); bấm **Xem danh sách** để mở đúng tập. Hàng tiếp theo: **Phân bổ thiết bị** (donut có tổng ở giữa, chú giải số và %; bấm một lát để mở thiết bị của nhóm đó) và **Thiết bị theo loại** (thanh dày, nhãn đầy đủ, số và % ở cuối, các loại ít gộp vào **Khác**). Sau đó là **Thiết bị theo phòng ban** (tách riêng **Trong kho**, **Dùng chung**, **Chưa xác định phòng ban**) cạnh **Đề xuất gần đây**, rồi **Thiết bị cần chú ý** và **Chất lượng dữ liệu** (thu gọn, bấm để mở). Nhấn chú giải, thanh hoặc liên kết để mở danh sách cùng domain. Phần đề xuất/cần xử lý vẫn giữ định nghĩa phạm vi riêng; chưa biết ngày/giá/lịch sử không được thay bằng số liệu giả. **Xuất Excel** dùng domain đang áp.

## Hồ sơ và bàn giao

Vào **Thiết bị & người sử dụng** để xem thiết bị đang giao cho một nhân viên HR xác định (giao hoặc mượn). Bảng có các cột **Người sử dụng** (ảnh, tên, mã nhân viên HR), **Phòng ban** (phòng hiện tại trong HR), **Loại thiết bị**, **Thiết bị** (tên và mã), **Tình trạng** và **Ghi chú** hỏng hóc/tình trạng thực tế; nội dung dài hiển thị 2 dòng, rê chuột để xem đủ. Bảng này không gồm thiết bị trong kho, dùng chung hoặc chưa ghi người giữ; xem các nhóm đó ở **Thiết bị tồn kho**, **Thiết bị dùng chung & chưa xác định người** hoặc **Tất cả hồ sơ thiết bị**. Lọc, số dòng, phân trang và **Xuất Excel** luôn theo đúng phạm vi của màn đang mở. Có thể tạo nháp mới và khai tên/phân loại/sở hữu/nguồn thực tế. Chỉ điền serial/ngày/giá khi có căn cứ. Đánh dấu giá trị đã biết khi xác nhận: chưa biết khác giá 0 đã xác nhận; dòng tiếp nhận/dự toán đề xuất cũng có cờ xác nhận tương ứng. Dịch vụ/đường truyền chọn loại quản lý riêng. Kiểm tra rồi đăng ký vào kho; tình trạng kỹ thuật, xác minh và khả dụng được hiển thị riêng. Nhân bản là hồ sơ mới, không kế thừa serial/custody như một thiết bị đã có.

Màn hình danh sách không gắn sẵn chip lọc mặc định gây chật ô tìm kiếm. Thanh lọc chỉ giữ 2 tiêu chí hay dùng nhất (ví dụ **Phân loại** và **Nơi giữ**; hoặc **Rà soát** và **Kết quả duyệt** ở Đề xuất) cùng nút **Bộ lọc** để mở drawer tiêu chí nâng cao, sau đó bấm **Áp dụng** (hoặc **Xóa lọc**). Bấm nút **Xem** trên mỗi dòng để mở màn hình chi tiết. Tất cả count/phân trang/export phải hiểu theo domain đã áp, không chỉ trang đang nhìn. Trong form chi tiết thiết bị, khối **Ai đang sử dụng / Đang ở đâu** hiển thị ảnh nhân sự HR (hoặc badge tồn kho) cùng 3 tab chính (**Thông tin**, **Sử dụng & bàn giao**, **Lịch sử**) và các khối thông tin kỹ thuật có thể đóng/mở gọn. Trong HR, admin có thể mở thiết bị của cùng employee, không tạo bản sao.

**Quay lại:** mọi màn chi tiết có một nút **← Quay lại** ở đầu trang (rê chuột để thấy màn sẽ về, ví dụ `Quay lại: Thiết bị & người sử dụng`). Nút về đúng danh sách đã mở, giữ bộ lọc, trang và số dòng mỗi trang. Khi mở chi tiết từ đường dẫn trực tiếp, nút về danh sách phù hợp với nơi giữ hiện tại (người sử dụng, tồn kho, dùng chung hoặc tất cả hồ sơ). Nếu đang sửa chưa lưu, hệ thống hỏi **Lưu rồi quay lại**, **Bỏ thay đổi** hoặc **Ở lại**. Cửa sổ bật lên giữ nút **Đóng**/**Hủy**; dashboard và danh sách không có nút này. Quy ước chung: [UI-BACK-001](../ui/UI_BACK_001_STANDARD.md).

Vào **Nghiệp vụ → Phiếu bàn giao / thu hồi**, chọn loại cấp phát/thu hồi/điều chuyển/mượn/trả/gửi sửa/nhận sửa/ngừng. Điền người/vị trí đích, ngày, phụ kiện/tình trạng và lý do; xem dữ liệu trước/sau, xác nhận chờ bàn giao rồi hoàn tất khi thực tế đã giao nhận. Pending giữ chỗ; hủy phải đúng trạng thái. Nếu báo phiên bản thay đổi, mở lại và đối chiếu hồ sơ mới trước khi làm tiếp. Sai phiếu hoàn tất dùng đảo phiếu có lý do khi còn hợp lệ, không sửa lịch sử trực tiếp. Chỉ nháp nhập nhầm chưa tham chiếu mới được xóa theo guard.

## Sửa chữa, đề xuất và kiểm kê

**Sửa chữa / bảo trì:** admin ghi riêng người báo lỗi/người kỹ thuật thực tế, hạn xử lý, NCC, chi phí có nguồn và kết quả. Gửi/nhận sửa ngoài đi qua phiếu bàn giao. Chỉ kết luận kỹ thuật sau xử lý khi có căn cứ; hoàn tất không mặc định biến máy hỏng thành Tốt.

**Đề xuất mua / sửa / nâng cấp:** tạo hồ sơ/dòng → gửi rà soát → trả lại có lý do hoặc hoàn tất rà soát. Nhập kết quả duyệt ngoài theo chứng cứ; chưa xác minh thì giữ chờ, không lấy tên footer Excel làm duyệt. Chỉ dòng được duyệt và đủ điều kiện có thể tạo tiếp nhận/sửa/chuyển. Tiếp nhận từng phần theo thực nhận, không nhập vượt/lặp; đề xuất chưa là tồn kho hay chứng từ thanh toán.

**Kiểm kê thiết bị:** chọn phạm vi, bắt đầu để chụp snapshot; đếm/quét mã và ghi người/vị trí/tình trạng thực tế. Chưa đếm khác thiếu, thiết bị ngoài snapshot khác thừa đã xác minh. Chốt kết quả không đổi custody tự động. Xem đề xuất điều chỉnh, ghi lý do và kiểm phiên bản trước tạo phiếu điều chỉnh. Không ghi đè giao dịch mới phát sinh sau ngày bắt đầu.

## Nhập XLSX có xem trước

Chức năng tạo dữ liệu thật; chỉ dùng khi có phạm vi nhập được giao và đã backup. Hai đợt thật đã chạy ở CHG-012: **NDL-00001** (danh mục thiết bị, trạng thái **Đã áp dụng một phần — còn dòng chờ**) và **NDL-00002** (đề xuất, **Đã áp dụng**).

1. Vào **Nhập nguồn có xem trước**, chọn loại nguồn/company và tải XLSX.
2. Xem sheet/cột/cell provenance đã làm sạch; kiểm header, phần nhóm, ô gộp, công thức/cached và dòng tổng. Không tự kéo dữ liệu qua ô trống.
3. Phân loại từng dòng: tiêu đề, dịch vụ, N/a, chờ xác minh, bỏ qua có lý do, thiết bị hoặc dòng đề xuất. Dòng chưa rõ để **Chờ xác minh** / **Thiếu thông tin** kèm lý do, không ép thành thiết bị.
4. Chọn đúng ID nhân viên/phòng/vị trí; alias ở **Cấu hình → Ánh xạ tên nguồn** cần admin xác nhận. Không dùng tên gần giống để tự ghép hoặc tạo HR/user.
5. Xác nhận nội dung/ID từng dòng áp dụng; đề xuất phải khớp tổng nguồn. Kiểm kỹ trước Apply vì sẽ tạo nháp thật.
6. Nguồn cùng hash mở lại batch cũ; apply lại không tạo trùng. Với nguồn sau, ghi lý do và xác nhận đối chiếu phiên bản/đợt độc lập. Mỗi dòng chọn **Định danh đã có** cùng ID hoặc **Thực sự mới**, ghi lý do và xác nhận định danh. Existing chỉ tạo liên kết với ID gốc, không cập nhật đè hồ sơ/provenance. New mới tạo nháp. Nếu chọn nguồn trước, ID existing phải thuộc nguồn đó; không ghép hai dòng vào cùng ID. Không dùng STT/tên tệp để xác định máy.
7. Với dòng thiết bị tạo mới, nhóm **Giá trị xác nhận cho hồ sơ tạo mới** trên form dòng chứa phân loại, loại quản lý, sở hữu, tình trạng kỹ thuật, cần thay thế, hãng và cấu hình. Admin kiểm các giá trị này trước khi xác nhận dòng.
8. Có thể áp dụng khi vẫn còn dòng chờ: các dòng đủ thông tin được tạo, đợt chuyển sang **Đã áp dụng một phần — còn dòng chờ**. Dòng chờ giữ lý do và gợi ý (gợi ý nhân viên HR chỉ là gợi ý, không tự gán).

**Xử lý dòng chờ:** mở **Dòng nguồn chờ bổ sung** (menu admin) hoặc nút cùng tên trên đợt. Đọc cột **Lý do / giải quyết**. Với dòng chờ xác minh người dùng: kiểm đúng nhân viên trong HR (không sửa tên HR, không tạo nhân viên mới), chọn ID nhân viên, đổi xử lý sang **Tạo thiết bị nháp**, kiểm giá trị xác nhận rồi bấm **Xác nhận ánh xạ** trên dòng. Với dòng thiếu thông tin: bổ sung phân loại / hãng / model từ căn cứ thực tế. Sau đó quay lại đợt và bấm **Áp dụng dòng đã xác nhận**; dòng đã áp dụng trước đó không bị tạo lại.

**Đề xuất nhập từ Excel:** tạo một hồ sơ đề xuất ở trạng thái rà soát **Nháp**, kết quả duyệt **Chưa xác minh**, không tạo thiết bị hay phiếu nhận. Nếu chứng từ không ghi ngày, ô **Ngày có trên chứng từ?** bỏ trống và form ghi rõ ngày đề xuất là ngày ghi hệ thống. Tên ở chân tệp không phải phê duyệt. Dòng thay thế máy cũ không tự nối với thiết bị theo tên; admin chọn thiết bị cũ đã xác minh nếu có căn cứ.

## Tệp, in và giới hạn

QR/tem cần đăng nhập admin; có thể nhập mã bằng bàn phím hoặc máy quét bàn phím. PDF nội bộ không phải biên bản đã ký. Bảo hành ngày và số đếm là căn cứ khác nhau. File/chatter chỉ trong quyền kho; không thêm follower ngoài admin.

Không chạy bộ test theo yêu cầu người dùng; không seed hoặc tạo giao dịch giả. Sau nhập CHG-012, sổ thiết bị XLSX có 54 dòng/18 cột (hai tiêu đề cột native Maintenance còn tiếng Anh); chưa kiểm PDF/QR, ma trận role/race hoặc giao dịch bàn giao/sửa/kiểm kê thật. Snapshot sau nhập giữ 39 nhân viên/28 users và membership quyền; có 54 thiết bị + 54 phiếu ghi nhận ban đầu, 0 yêu cầu sửa/tiếp nhận. Bằng chứng runtime và phần còn thiếu theo [acceptance](EQUIP_001_ACCEPTANCE.md); backup/rollback theo [runbook](../../ops/runbooks/EQUIP_001_DEPLOY_IMPORT_AND_ROLLBACK.md).
