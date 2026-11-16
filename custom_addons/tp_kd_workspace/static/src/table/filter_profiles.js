/** @odoo-module **/
import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";

/**
 * KH-KD, TP Contracts & TP Core Filter Profiles (S2).
 */
registerTableFilterProfile("project.project", {
    criteria: [
        { key: "name", field: "name", label: "Dự án / mã", type: "char", placeholder: "Tìm tên hoặc mã dự án…" },
        { key: "tp_department_id", field: "tp_department_id", label: "Phòng chủ trì", type: "many2one", allowEmpty: true },
        { key: "partner_id", field: "partner_id", label: "Đối tác", type: "many2one", allowEmpty: true },
        { key: "kd_lifecycle", field: "kd_lifecycle", label: "Vòng đời", type: "selection", multi: true },
        { key: "kd_deadline", field: "kd_deadline", label: "Hạn dự án", type: "date" },
    ],
});

registerTableFilterProfile("crm.lead", {
    criteria: [
        { key: "name", field: "name", label: "Cơ hội", type: "char", placeholder: "Tìm tên cơ hội…" },
        { key: "partner_id", field: "partner_id", label: "Đối tác / CĐT", type: "many2one", allowEmpty: true },
        { key: "kd_bid_state", field: "kd_bid_state", label: "Trạng thái thầu", type: "selection", multi: true },
        { key: "kd_route", field: "kd_route", label: "Hướng triển khai", type: "selection", multi: true },
        { key: "kd_deadline", field: "kd_deadline", label: "Hạn nộp", type: "date" },
    ],
});

const TASK_CRITERIA = [
    { key: "name", field: "name", label: "Công việc / WBS", type: "char", placeholder: "Tìm hạng mục…" },
    { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
    { key: "kd_responsible_id", field: "kd_responsible_id", label: "Người thực hiện", type: "many2one", allowEmpty: true },
    { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
    { key: "date_deadline", field: "date_deadline", label: "Hạn hoàn thành", type: "datetime" },
];
registerTableFilterProfile("project.task", { criteria: TASK_CRITERIA });
registerTableFilterProfile("project.task::kd_wbs", { criteria: TASK_CRITERIA });
registerTableFilterProfile("project.task::kd_tasks", { criteria: TASK_CRITERIA });

registerTableFilterProfile("tp.contract", {
    criteria: [
        { key: "code", field: "code", label: "Mã HĐ", type: "char", placeholder: "Mã hợp đồng…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "partner_id", field: "partner_id", label: "Đối tác", type: "many2one", allowEmpty: true },
        { key: "contract_type", field: "contract_type", label: "Loại HĐ", type: "selection", multi: true },
        { key: "lifecycle_state", field: "lifecycle_state", label: "Vòng đời", type: "selection", multi: true },
    ],
});

registerTableFilterProfile("tp.allocation", {
    criteria: [
        { key: "code", field: "code", label: "Mã phiếu", type: "char", placeholder: "Mã hoặc tên…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "recipient_department_id", field: "recipient_department_id", label: "Đơn vị nhận", type: "many2one", allowEmpty: true },
        { key: "allocation_kind", field: "allocation_kind", label: "Loại giao khoán", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "date_due", field: "date_due", label: "Hạn", type: "date" },
    ],
});

registerTableFilterProfile("tp.production", {
    criteria: [
        { key: "code", field: "code", label: "Mã phiếu", type: "char", placeholder: "Mã sản lượng…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "owner_id", field: "owner_id", label: "Phụ trách", type: "many2one" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "reconciliation_state", field: "reconciliation_state", label: "Đối chiếu", type: "selection", multi: true },
        { key: "date_due", field: "date_due", label: "Hạn", type: "date" },
    ],
});

registerTableFilterProfile("tp.acceptance", {
    criteria: [
        { key: "code", field: "code", label: "Mã nghiệm thu", type: "char", placeholder: "Mã hồ sơ…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "counterparty_id", field: "counterparty_id", label: "Đối tác", type: "many2one", allowEmpty: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "date_due", field: "date_due", label: "Hạn", type: "date" },
    ],
});

registerTableFilterProfile("tp.periodic.plan", {
    criteria: [
        { key: "code", field: "code", label: "Mã kế hoạch", type: "char", placeholder: "Mã kế hoạch…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "period_kind", field: "period_kind", label: "Loại kỳ", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "period_from", field: "period_from", label: "Từ ngày kỳ", type: "date" },
    ],
});

registerTableFilterProfile("tp.payment.request", {
    criteria: [
        { key: "code", field: "code", label: "Mã đề nghị", type: "char", placeholder: "Mã đề nghị…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "direction", field: "direction", label: "Chiều TT", type: "selection", multi: true },
        { key: "payment_basis", field: "payment_basis", label: "Căn cứ TT", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "date_due", field: "date_due", label: "Hạn thanh toán", type: "date" },
    ],
});

registerTableFilterProfile("tp.obligation", {
    criteria: [
        { key: "code", field: "code", label: "Mã nghĩa vụ", type: "char", placeholder: "Mã / tên…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "checklist_status", field: "checklist_status", label: "Checklist", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "date_due", field: "date_due", label: "Hạn xử lý", type: "date" },
    ],
});

registerTableFilterProfile("tp.credential", {
    criteria: [
        { key: "name", field: "name", label: "Tên hồ sơ", type: "char", placeholder: "Tìm tên chứng chỉ…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "subject_kind", field: "subject_kind", label: "Đối tượng", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "valid_to", field: "valid_to", label: "Hiệu lực đến", type: "date" },
    ],
});

registerTableFilterProfile("tp.project.participation", {
    criteria: [
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "partner_id", field: "partner_id", label: "Đơn vị", type: "many2one" },
        { key: "role", field: "role", label: "Vai trò", type: "selection", multi: true },
        { key: "active", field: "active", label: "Hiệu lực", type: "boolean", positiveLabel: "Đang tham gia", negativeLabel: "Đã ngừng" },
    ],
});

registerTableFilterProfile("tp.bid.package.amount", {
    criteria: [
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "kind", field: "kind", label: "Loại giá trị", type: "selection", multi: true },
        { key: "amount_state", field: "amount_state", label: "Tình trạng", type: "selection", multi: true },
        { key: "tax_basis", field: "tax_basis", label: "Thuế", type: "selection", multi: true },
        { key: "estimate_date", field: "estimate_date", label: "Ngày ước tính", type: "date" },
    ],
});

registerTableFilterProfile("tp.project.update", {
    criteria: [
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "kind", field: "kind", label: "Loại cập nhật", type: "selection", multi: true },
        { key: "actor_id", field: "actor_id", label: "Người cập nhật", type: "many2one" },
        { key: "create_date", field: "create_date", label: "Thời điểm", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.task.update", {
    criteria: [
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "task_id", field: "task_id", label: "Công việc", type: "many2one" },
        { key: "operation", field: "operation", label: "Thao tác", type: "char", placeholder: "create, edit…" },
        { key: "actor_id", field: "actor_id", label: "Người thực hiện", type: "many2one" },
        { key: "create_date", field: "create_date", label: "Thời điểm", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.kd.document", {
    criteria: [
        { key: "name", field: "name", label: "Tên tài liệu", type: "char", placeholder: "Tìm tài liệu…" },
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "confidentiality", field: "confidentiality", label: "Độ mật", type: "selection", multi: true },
        { key: "added_at", field: "added_at", label: "Thời điểm tải", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.contract.revision", {
    criteria: [
        { key: "contract_id", field: "contract_id", label: "Hợp đồng", type: "many2one" },
        { key: "revision_kind", field: "revision_kind", label: "Loại phiên bản", type: "selection", multi: true },
        { key: "review_state", field: "review_state", label: "Rà soát", type: "selection", multi: true },
        { key: "signature_status", field: "signature_status", label: "Chữ ký", type: "selection", multi: true },
        { key: "signed_date", field: "signed_date", label: "Ngày ký", type: "date" },
    ],
});

registerTableFilterProfile("tp.contract.document", {
    criteria: [
        { key: "name", field: "name", label: "Tên tài liệu", type: "char", placeholder: "Tìm tên / tệp…" },
        { key: "contract_id", field: "contract_id", label: "Hợp đồng", type: "many2one" },
        { key: "document_kind", field: "document_kind", label: "Loại tài liệu", type: "selection", multi: true },
        { key: "confidentiality", field: "confidentiality", label: "Độ mật", type: "selection", multi: true },
        { key: "create_date", field: "create_date", label: "Ngày thêm", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.contract.line.amount", {
    criteria: [
        { key: "project_id", field: "project_id", label: "Dự án", type: "many2one" },
        { key: "amount_state", field: "amount_state", label: "Trạng thái xác nhận", type: "selection", multi: true },
        { key: "tax_basis", field: "tax_basis", label: "Cơ sở thuế", type: "selection", multi: true },
        { key: "create_date", field: "create_date", label: "Ngày tạo", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.contract.audit", {
    criteria: [
        { key: "contract_id", field: "contract_id", label: "Hợp đồng", type: "many2one" },
        { key: "action", field: "action", label: "Hành động", type: "selection", multi: true },
        { key: "actor_id", field: "actor_id", label: "Người thực hiện", type: "many2one" },
        { key: "acted_at", field: "acted_at", label: "Thời điểm", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.work.item", {
    criteria: [
        { key: "code", field: "code", label: "Mã hạng mục", type: "char", placeholder: "Tìm mã…" },
        { key: "name", field: "name", label: "Tên hạng mục", type: "char", placeholder: "Tìm tên…" },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang sử dụng", negativeLabel: "Đã lưu trữ" },
    ],
});
