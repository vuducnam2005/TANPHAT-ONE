# KD-UI-005 — Thiết kế thực thi bốn màn Kinh doanh và dự án

Ngày 07/11/2026, Asia/Saigon. CHG-20261107-007. Thực thi trực tiếp theo yêu cầu người dùng, sau bàn giao UI-HOME-003 CHG006 và checker PASS. [Kế hoạch](KD_UI_005_BUSINESS_PROJECT_REDESIGN_PLAN.md), [acceptance](../demo/KD_UI_005_ACCEPTANCE.md). Đây là tự kiểm implementation; audit độc lập, business acceptance và pilot giữ riêng.

## A — Inventory trước code

| Màn | XMLID / model | Binding, controller và dữ liệu giữ |
| --- | --- | --- |
| OPP-L | `opportunity_list` / `crm.lead` | `action_opportunities`; `tp_kd_table` → KdTableController/ListController; domain `tp_project_id != False`, 20 dòng, native search/group/sort/pager/resize/checkbox/cột/mật độ |
| OPP-D | `opportunity_form` / `crm.lead` | FormController native; name, type ẩn, partner_id, tp_project_id, kd_source, company_id, user_id, kd_route, kd_deadline; kd_scope Text, kd_checklist Text, kd_receipt Char; inherit `opportunity_credentials` giữ tags/no_create/domain và inverse bảo toàn link riêng |
| PRJ-L | `kd_project_list` / `project.project` | Primary inherit `project.view_project`; `tp_kd_project_list` → KdProjectListController/ProjectListController; `action_projects`, domain tp_managed=True, unique(company_id,tp_code), giữ favourite/View Tasks/cột native |
| PRJ-D | `project_form` / `project.project` | FormController native; name, tp_managed ẩn, tp_code required theo managed, partner_id/company_id/tp_department_id/user_id/kd_deadline/kd_scope/tp_assignment_ids; phân công chỉ `tp_core.group_manager` |

Opportunity header giữ `kd_can_prepare` ẩn; `action_kd_prepare` chỉ identified + can_prepare; `action_kd_record_submission` chỉ preparation + bid + can_prepare. Statusbar readonly, ba state giữ nguyên; submitted luôn có chữ chưa xác minh. Direct không yêu cầu khai báo nộp. Backend kiểm access + assignment/company/department + grant, không sửa rule để trang trí.

Project giữ 10 object action: opportunities (crm.lead, tp_project_id), contracts (tp.contract), tasks (project.task), allocations (tp.allocation), productions (tp.production), acceptances (tp.acceptance), payments (tp.payment.request), plans (tp.periodic.plan), credentials (tp.credential), obligations (tp.obligation). Chín action sau dùng project_id. Giữ `child_context`, defaults của model con, view mapping và `tp_kd_leaf`; không mang form_view_ref/default dự án sang con. Bảy inherit ở allocation/production/acceptance/payment/periodic_plan/credential/obligation.xml tiếp tục thêm vào div[name=button_box].

Compiled arch và ảnh trước lưu riêng `.local/kd-ui005/arch-before/`, `shots/clone-before/`; RPC khi mở từng màn được ghi trong browser evidence. Source baseline là bản CHG006, không reset theo Git (có nhiều thay đổi chưa commit từ trước).

## B — Token, bố cục và review brief trước code

Hồ sơ công trình là trọng tâm: tên và tình trạng dễ đọc, hai cột thông tin nhãn trên ô, phần nội dung có tab rõ; đường viền thay bóng trang trí. Giữ font Odoo tiếng Việt. Nền #F4F6F8, mặt #FFFFFF, nhấn #255F85, navy #17324D, chữ #1F2937, viền #D9E2EC. Nhãn 13px, thân 14–15px, tên 26px desktop/22px mobile; nhịp 8/12/16/24px; sheet tối đa 1440px. Không thêm font/CDN/dependency.

```
OPP-L: [Tạo] [Tìm/lọc/group] [Thoáng/Gọn] [Cột] [Pager]
        Tên | Khách hàng | Tình trạng | Hạn | Phụ trách | Hình thức
OPP-D: Tên đầy đủ + header hành động/state native
        Khách hàng và dự án       | Phụ trách và kế hoạch
        [Phạm vi] [Checklist: Text + căn cứ Char] [Năng lực: tags]
PRJ-L: [Native Project toolbar] Mã | Tên | Khách hàng | Quản lý | Mốc
PRJ-D: Tên / mã
        [Cơ hội] [Hợp đồng] [WBS] + button_box hồ sơ liên quan (overflow native)
        Nhận diện và khách hàng   | Chủ trì và mốc
        [Phạm vi/đầu ra] [Phân công theo nhóm]
```

Review: tránh sao chép dashboard/card kit; không KPI/timeline/progress giả. Ba action chính tách khỏi button_box để nổi rõ, bảy action phụ dùng ButtonBox native có overflow responsive. Anchor và bảy inherit giữ. Hai list và hai form có class `tp_kd_bp_*`; SCSS không sửa `.tp_kd_form` chung hoặc biến body. Title dùng native Text widget trên field Char để wrap khi sửa, không đổi field/model.

Many2one dùng widget nhỏ kế thừa Many2OneField, giữ autocomplete/open/dirty behavior. Bên dưới có disclosure native bằng bàn phím/chạm để đọc toàn bộ display_name đã có trong record; không RPC riêng, không tooltip-only hoặc innerHTML. Không remount input khi mở disclosure.

Motion: hover120ms, focus140ms; không intro hay hiệu ứng tab gây remount; native dropdown/disclosure, không animation lặp. OS reduce và kdPrefs.motion đều tắt transition/animation trong scope. Target44px, focus rõ, mobile một cột, bảng cuộn ngang trong renderer. Không che overflow trang.

## C — Lô và cổng

A inventory/compiled arch/ảnh trước → B cơ hội/search/widget → C dự án/actions → D HOOT/Odoo/browser/responsive/hồi quy/backup/apply. Mỗi bước ghi evidence trong acceptance. Chỉ dữ liệu giả ghi trên clone18789 `tp_tanphat_kdui005_20261107`, source/config/data cô lập `.local/kd-ui005/`. Dev18069 verify chỉ đọc. Source hash Odoo + browser + HOOT phải bằng source áp, backup mới và verified trước upgrade đúng addon. Rollback delta source/view/assets, không restore cả DB đè dữ liệu mới.

## D — As-built

`tp_kd_workspace` 20.0.1.3.0 → 20.0.1.4.0. Đúng hai list/hai form có class riêng; list controller cũ giữ nguyên. Opportunity form vẫn FormController native. Project form đăng ký `tp_kd_bp_project_form`, kế thừa FormController và chỉ thay component ButtonBox: bảy slot object button gộp vào Dropdown native **Hồ sơ liên quan**; không override save/discard/dirty/leave/action. Ba action chính nằm trong sheet; anchor `button_box` và bảy inherit giữ nguyên. Runtime đã bấm đủ mười nút.

`business_project.js/xml/scss` cung cấp Many2OneField subclass với autocomplete native cùng disclosure `details/summary`; đọc `record.data[name].display_name`, escaped text, không RPC/write riêng. Disclosure không remount input; HOOT kiểm chọn liên kết mới, tên rỗng, HTML escape và object callback của dropdown. Không dùng quyền/money/file để bổ sung preview.

Tên Char dùng Text widget native để xuống dòng khi sửa; ngày trên hai form và bảng cơ hội dùng numeric date native để hiển thị đủ năm. Checklist vẫn Text, căn cứ vẫn Char, Năng lực vẫn tags/no_create/domain theo dự án. Không render private raw links. `models/workspace.py` chỉ thêm `search_view_id` vào helper mở `crm.lead`; search riêng lọc trên field hiện có, domain/child_context/default/view/action/security khác giữ.

SCSS chỉ hai list/form và tên menu dropdown riêng; không đổi token body hoặc rule `.tp_kd_form` chung. Breadcrumb tên dài wrap trong vùng sẵn có; native pager và dropdown giữ chỗ. Motion màu/viền 120–140ms; không thêm intro/tab animation vì không cần cho thao tác. OS reduce và `kdPrefs.motion` đều được browser kiểm. Native textarea có thể cao với tên rất dài để đọc hết; không cắt tên để làm đều chiều cao.

## E — Kiểm chứng và giới hạn

- Compiled arch trước/sau: `.local/kd-ui005/arch-before/`, `arch-after/`. So sánh field/button signature không mất behavior/modifier/quyền. Whitelist trình bày: class/width/string/optional/nolabel/colspan/placeholder/rows, widget title/many2one và numeric date options; view search mới là phần thêm chủ đích. Project js_class mới chỉ thay ButtonBox, có HOOT và browser native guard.
- RPC mở màn (desktop1440/mobile390, số call_kw, không tính menu/session): cơ hội list 2→2, form 2→1 desktop/1→1 mobile; dự án list 3→3, form 1→1. `baseline-rpc.json` và `after-rpc.json`; không tăng RPC từ preview/hover.
- Odoo final 116/116 (`tp_kd_workspace`43 + `tp_contract`73); HOOT5/5, 15 assertions; browser tổng hợp161/161, thêm session expiry mô phỏng + unique code4/4; scope3/3rollback, hồi quy270/270. Dev chỉ đọc130+269=399/399;37bảng/3.050dòng và attachment/module/quyền nguyên. Test ghi chỉ clone. Dev chỉ đọc; nguồn test/nguồn áp bị khóa bằng hash.
- Không đổi workflow/state/schema/API/ACL/rule/grant. Backend tests và browser deny kiểm scope/private credential, inverse giữ link không thấy; dữ liệu dev đối chiếu theo hash trước/sau.
- Chromium headless, touch/mobile emulation, zoom thật125/150% trong Chromium settings; chưa thiết bị thật/Safari. Session/AccessError khi lưu được mô phỏng trên clone bằng response lỗi, kiểm không replay/không persist/giữ input. Không thay core session. Có native session expiry gián đoạn ở một số lần điều hướng lặp của clone; bộ kiểm dùng action ID do Odoo trả về và context riêng khi cần, ghi lịch sử lỗi trong acceptance.
- Tự kiểm kỹ thuật, chưa audit độc lập/business acceptance/pilot. Checklist cấu trúc, kết quả thầu chính thức, BASE/ký/hiệu lực/tiền thật/upload/grant người thật/TASK-001 và sáu phụ lục không thuộc batch.

Kết quả hồi quy, backup/apply/verify và lệnh rollback xem [acceptance](../demo/KD_UI_005_ACCEPTANCE.md); thao tác xem [hướng dẫn](../demo/KD_UI_005_USER_GUIDE.md).
