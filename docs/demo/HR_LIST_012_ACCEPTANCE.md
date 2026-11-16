# HR-LIST-012 — Trả danh sách nhân viên về kiểu nhóm cũ

> Cập nhật HR-LIST-013: cơ chế nhóm mặc định có facet và khả năng bỏ nhóm bên dưới đã được thay bằng các nhóm phòng ban cố định. Xem [bản sửa013](HR_LIST_013_ACCEPTANCE.md). Nội dung012 giữ làm lịch sử.

13/11/2026, CHG-20261113-003. Người dùng trực tiếp yêu cầu sửa HR-UI-011 theo
ảnh 2: nhóm phòng ban có dải xanh, không lặp cột Đơn vị/Phòng ban trong từng
dòng nhân viên. Đây là follow-up được phép triển khai và áp main trong cùng
scope HR; không stage/commit/push.

## Kết quả

- Danh sách mặc định nhóm theo `department_id` bằng `default_group_by` native,
  mở sẵn nhóm; dải #CBF3F7 và số “thành viên”. Không ép nhóm bằng model patch.
- Renderer HR đã có tự ẩn cột phòng ban khi group theo phòng ban được giữ.
  Cả header lẫn ô department_id không hiện trong danh sách nhóm; native search
  vẫn có thể đổi/bỏ nhóm, lúc đó cột phòng ban trở lại để không mất ngữ cảnh.
- Bỏ khối tiêu đề/mô tả/kết quả lớn trên bảng nhân viên. Tên dạng chữ, không
  avatar; thứ tự Mã nhân viên / Họ và tên / Số điện thoại / Chức vụ / Tên đăng
  nhập / Tình trạng / Thao tác. Bấm tên/dòng mở hồ sơ, bỏ nút Xem hồ sơ dư.
- Dùng lại màu nút/badge và bố cục native cũ cho danh sách này. Giữ nhãn quản
  lý/tạo tài khoản đúng trạng thái và quyền hiện hành; không khôi phục lỗi
  hiển thị “Xem tài khoản” cho cả hồ sơ chưa có account.
- Giữ một menu Danh sách nhân viên, hồ sơ 5 tab và các màn khác của011.
  Không đổi backend, ACL, mật khẩu, phòng ban, role/grant hoặc dữ liệu.

Truy cập [Danh sách nhân viên trên main](http://127.0.0.1:18069/odoo/action-tp_hr_workspace.action_employees).
`tp_hr_workspace` **20.0.1.10.1**; thay 8 file application/test, không file mới
trong addon. README/guide/status/changelog/roadmap/acceptance cập nhật cùng lượt.

## Kiểm thực chạy

| Kiểm | Kết quả |
| --- | --- |
| Native XML/upgrade | 2 XML hợp lệ, upgrade HR test/main exit0; JS syntax PASS |
| Odoo UI regression | `-u tp_hr_workspace --test-tags /tp_hr_workspace:TestHrUi --no-http --stop-after-init`: **3 tests, 0 failed/0 errors**, [log](../../.local/hr-list012/odoo-ui-tests.log). Không chạy lại cả77 tests nghiệp vụ vì không đổi backend |
| HOOT sau source cuối | **HR36+KD2 =38 tests/171 assertions**, Home30+KD1 =31/179, đều PASS; [HR](../../.local/hr-list012/hoot-hr.txt), [Home](../../.local/hr-list012/hoot-home.txt) |
| Browser test/main | **9/9 nhóm mỗi cổng, 0 console/page errors**: mặc định group/ẩn header+cell phòng/không avatar/không intro/màu nhóm đúng, backend group limit10/20/50/100, tìm mã, mở hồ sơ/quay lại, 1440/1280/390/320 không tràn trang, catalog HR và KH-KD không đổi; [test](../../.local/hr-list012/verify-test.json), [main](../../.local/hr-list012/verify-main.json) |
| Bảo toàn main | So600bảng:588 giữ tuyệt đối trước HTTP,583 sau smoke; delta chỉ metadata/assets/bus/presence/login/device. ACL953 giữ policy (3write_date),57groups nguyên;632nonasset attachment rows và blobs khớp. [rowdiff](../../.local/hr-list012/rowdiff-main-final.json), [blob/ACL](../../.local/hr-list012/preservation-after-smoke.json) |

Lượt đầu màu nhóm bị rule `th` cũ ghi đè: đã sửa specificity scoped đúng rồi
chạy lại đạt. Browser harness có race khi chọn liên tiếp page size; đã chờ
RPC và trạng thái Đang tải kết thúc rồi chạy lại9/9, không sửa app theo lỗi
harness và không tính lượt fail là pass. Còn warning markdown2/icon/Image/GC
WinError5 đã có; không có test failure, blobs kiểm riêng.

## Ảnh đã mở kiểm tra

Cặp1440 dưới cùng admin/route/dataset trên main. Các kích thước khác là ảnh
responsive sau sửa, không tuyên bố có cặp trước cùng kích thước.

- [Trước main1440](../../.local/hr-list012/before-main.png)
- [Sau main1440](../../.local/hr-list012/after-main-1440.png)
- [Sau main1280](../../.local/hr-list012/after-main-1280.png)
- [Sau main390](../../.local/hr-list012/after-main-390.png)
- [Sau main320](../../.local/hr-list012/after-main-320.png)
- [Trước test1440](../../.local/hr-list012/before-test.png) / [Sau test1440](../../.local/hr-list012/after-test-1440.png)

Tự xem desktop đã khớp cấu trúc ảnh tham chiếu: nhóm xanh, hàng chữ, không
phòng lặp. Giữ count thực trong DB; không sửa dữ liệu để khớp số người trong
ảnh cũ. Mobile giả lập; tự review vì subagent model kế thừa không khả dụng.
Người dùng chưa xác nhận visual/business/pilot trong follow-up này.

## Áp dụng và rollback

- Backup DB+filestore main **`backup-tp_tanphat_dev-20261113T043425236788Z`**,
 600tables/666blobrefs, tại `.local/hr001/`.
- Gate0sessions phát hiện Odoo12744/wrapper16760 cùng config main còn sống
  dù listener đã dừng; đã kiểm command line và đóng đúng2process đó. Lệnh
  upgrade đầu được guard từ chối, không chạy. Sau0sessions, seal8file khớp,
  upgrade chỉ HR noHTTP exit0. Một main process mới được mở ngoài lệnh start
  của task sau upgrade; không khởi động bản trùng. Browser main dùng runtime
  đó và đạt9/9. Hai cổng18069/18079 đang chạy.
- Không schema/migration dữ liệu; dùng lại restore rehearsal600/666/432 của
  HR-UI-011 cùng schema. Không restore test lên main, không tạo DB/fixture mới.
- Rollback riêng012: dừng đúng main, trả đúng8file trong
  `.local/hr-list012/rollback-source.zip` theo SHA256 manifest, upgrade lại HR
  20.0.1.10.0 để khôi phục employee list arch, restart/assets và smoke.012 không
  thêm field/view/action/XMLID; không cần xóa metadata của011. Backup main ở
  trên dùng khi cần phục hồi dữ liệu sau đánh giá giao dịch phát sinh.

Workflow finish/check và diff-check ghi trong state/status. Bước tiếp: người
dùng Ctrl+F5 ở18069 và review danh sách; các phạm vi khác giữ handoff011.
