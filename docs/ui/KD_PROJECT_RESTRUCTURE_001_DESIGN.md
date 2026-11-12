# KD-PROJECT-RESTRUCTURE-001 — S0 inventory, thiết kế và acceptance

Ngày 09/11/2026. Scope được user giao trực tiếp; V2/TASK-001/người thật/pilot chưa duyệt.
Nguồn riêng: `.local/kd-project-restructure001/workspace`; DB owned
`tp_tanphat_kdproject001_20261109`, HTTP19489, PostgreSQL55432. Dev18069 giữ nguyên.
Baseline CHG009, root checker PASS, không checkpoint active. Snapshot nhất quán
578 bảng/295 attachment, restore exact rowsets/blobs trước neutralize. Clone tắt cron,
SMTP loopback discard; không gửi tích hợp ngoài. Không commit/push.

## Inventory và mapping trước code

`mapping-dry-run.json` private có 14 managed project/25 CRM và ID/owner/partner
thật, không chép vào Git. Giữ project ID cũ. Link CRM→Project rõ giữ nguyên;
không coi partner cũ là chủ đầu tư, không suy submitted là trúng, không coi
expected_revenue là giá gói. Không đủ căn cứ tạo gói từ CRM: không tạo gói giả;
hiển thị CRM chưa gắn gói trong Cần đối chiếu. Migration mặc định additive schema,
không ghi dữ liệu cũ; journal ORM chỉ chạy khi có mapping ID tường minh.
Owner/reviewer cũ không đổi. Danh sách private cần đối chiếu không là lệnh bàn giao.

Nguồn chính: workspace.py/opportunity_access.py/project_project.py và CRM bridge;
native menu workspace.xml cùng reporting/wbs/contract views; sidebar từ menu service;
table_tools giữ paging/filter/columns. F1–F3 còn ở native ownership/sudo/fallback.

## Thiết kế

Màu giữ nhận diện: navy #17324d, trắng #ffffff, nền #f4f7fa, đường bảng #ccd6e0,
thành công #217a58, cảnh báo #9a5a12. Dùng font Odoo hiện có, heading 24/20px,
nội dung 14px; không thêm font/dependency. Nội dung canh trái, tiền theo Odoo.
Điểm nhấn là hai bảng nghiệp vụ có hàng/cột rõ và tiêu đề cố định.
Không nhân đôi dashboard KH-KD cũ thành các card KPI trang trí.

```text
Danh mục Dự án: Mã | Tên | Chủ đầu tư | Đối tác + vai | Phụ trách | Tình trạng | Ghi chú
Đấu thầu: Gói | Dự án | Chủ đầu tư | Đối tác | Phụ trách | Hạn | Tiến trình | Giá gói | Ghi chú
Quản lý: [Dự án] [Sang quản trị]       Quản trị: [Dự án] [Sang quản lý]
         WBS / việc quá hạn                     Hợp đồng / hồ sơ còn thiếu
         Người, hạn, đầu ra                    Khoán / SL / NT / đề nghị
Detail: tên/mã/project, phụ trách + tình trạng; hành động chính nhất quán
        nội dung theo góc nhìn; các bên; hồ sơ nguồn; nhật ký append-only
```

## State/capability trước code

Project: tracking↔executing↔paused; mỗi state mở có thể sang ended.
Ended→tracking/executing/paused cần capability reopen riêng và lý do.
Mọi chuyển cần status capability, scope, reason, version/key; không đổi hợp đồng.
Gói: tracking→participating→awaiting_result; kết quả riêng unknown/won/lost/
cancelled/not_participating, cần căn cứ; không tác động project/gói khác.
CRM giữ identified/preparation/submitted; review typed giữ draft/in_review/returned.
Note thêm mới/correction liên kết event cũ; không sửa/xóa event; không email/follower.
Tạo/sửa metadata, status, reopen, note, WBS create/assign/progress tách grant.
Không tự cấp grant mới cho account dev. Fixture HEAD đủ quyền và thiếu quyền đều kiểm.
Tiền giữ model riêng financial_read + assignment và financial_draft_edit để ghi;
unknown khác0, không cộng khác currency/basis, không trả tiền vào metadata.

## Acceptance trước code

Mỗi hàng: actor/input/action → expected; evidence dự kiến, chưa phải PASS.

|AT|Actor/input/action|Expected|Evidence|
|---|---|---|---|
|A01|Reader chọn project, đổi quản lý/quản trị|2 action/landing/detail; cùng ID/filter|ORM + browser|
|A02|5 vai mở danh mục và action cũ|1 danh mục project, CRM lần tham gia, lịch sử giữ|view/action + browser|
|A03|Owner nhập investor A/counterparty B|CRM/project/contract giữ nghĩa bên ký B|Odoo constraint|
|A04|Owner 1 project/2 gói/2 lần tham gia|kết quả 1 gói không lan; direct không bắt gói|Odoo|
|A05|Reader list/filter/paging/columns|owner trước Date cũ, 10/20/50/100|browser|
|A06|Owner nhiều bên/vai/cross-company|nhiều vai hợp lệ, trùng đúng scope bị chặn|Odoo|
|A07|Tiền 10 tỷ gói/3 tỷ công ty, unknown/0|không cộng nhầm; không rò qua query/export|Odoo|
|A08|Owner status/note; stale/key/retry|actor/time/version/căn cứ; atomic/retry đúng|Odoo|
|A09|Owner note sau submitted/correction|CRM snapshot giữ; file/chatter không bypass|Odoo + HTTP|
|A10|5 fixture/cross-project/company/revoke/expiry|WBS/tiền/hợp đồng độc lập, recheck current|Odoo|
|A11|5 account dev/fixture HEAD/owner cũ|account/grant cũ nguyên; guide nêu thiếu nút|inventory + browser|
|A12|Dry-run/apply twice/rollback mapping|không đoán, idempotent, exact delta|migration probe|
|A13|Support/owner/admin PDF/upload/delete/chatter|nội dung và side effect đúng policy, model khác giữ|HTTP + ORM|
|A14|Reader 2 landing/drilldown|nguồn/câu hỏi khác, done≠NT≠thu tiền|ORM + browser|
|A15|1440/1280/768/390/320/zoom200/keyboard/reduce|responsive, Back/deep link/dirty guard|browser + ảnh thật|
|A16|Reviewer source/backup/restore/apply|exact source; độc lập security trước dev; bảo toàn|seal/restore/smoke|

## Chín yêu cầu → nguồn/AT

1/2/4: workspace + project/bid views, A02/A03/A05.
3/5: project lifecycle + event/wizard, A08/A09.
6: res.partner participation relation, A03/A06.
7: bid amount riêng, A07.
8: native bid action/menu, A04/A05.
9: project perspective action + landing/detail, A01/A10/A14/A15.
Mỗi chặng cập nhật trạng thái riêng. Self-test không là audit độc lập hoặc business/pilot.
