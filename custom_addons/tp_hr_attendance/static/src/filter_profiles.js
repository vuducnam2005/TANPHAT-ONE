/** @odoo-module **/
import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";

registerTableFilterProfile("tp.hr.attendance.correction::corrections", {
    criteria: [
        { key: "name", field: "name", label: "Mã phiếu", type: "char" },
        { key: "employee_name", field: "employee_name", label: "Nhân viên / mã TP", type: "char" },
        { key: "department_id", field: "department_id", label: "Phòng", type: "many2one" },
        { key: "work_date", field: "work_date", label: "Ngày công", type: "date" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "reviewer_id", field: "reviewer_id", label: "Người xử lý", type: "many2one" },
    ],
});
registerTableFilterProfile("tp.hr.attendance.period::periods", {
    criteria: [
        { key: "name", field: "name", label: "Kỳ công", type: "char" },
        { key: "date_from", field: "date_from", label: "Từ ngày", type: "date" },
        { key: "date_to", field: "date_to", label: "Đến ngày", type: "date" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection" },
        { key: "locked_by", field: "locked_by", label: "Người chốt", type: "many2one" },
    ],
});

/**
 * HR-ATTENDANCE-001 table filter profiles (DEC-044 inventory: docs/ui/TP_TABLE_FILTER_INVENTORY.md).
 * Every criterion maps to a stored field present in the action's search view.
 */
registerTableFilterProfile("tp.hr.attendance.day::days", {
    criteria: [
        { key: "employee_name", field: "employee_name", label: "Nhân viên / Mã TP", type: "char", placeholder: "Tên hoặc mã TP…" },
        { key: "work_date", field: "work_date", label: "Ngày công", type: "date" },
        { key: "department_id", field: "department_id", label: "Phòng", type: "many2one", allowEmpty: true },
        { key: "data_state", field: "data_state", label: "Tình trạng dữ liệu", type: "selection", multi: true },
        { key: "lock_state", field: "lock_state", label: "Trạng thái kỳ", type: "selection" },
    ],
});

registerTableFilterProfile("tp.hr.attendance.batch::batches", {
    criteria: [
        { key: "name", field: "name", label: "Lô / tệp", type: "char", placeholder: "Tên lô hoặc tệp…" },
        { key: "period_from", field: "period_from", label: "Kỳ từ ngày", type: "date" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "applied_by", field: "applied_by", label: "Người áp dụng", type: "many2one", allowEmpty: true },
        {
            key: "attention",
            type: "preset",
            label: "Cần xử lý",
            multi: true,
            requireFields: ["conflict_count", "unmapped_count"],
            options: [
                { key: "conflict", label: "Có xung đột", domain: [["conflict_count", ">", 0]] },
                { key: "unmapped", label: "Có dòng chưa đối chiếu", domain: [["unmapped_count", ">", 0]] },
            ],
        },
    ],
});

registerTableFilterProfile("tp.hr.attendance.line::import_lines", {
    criteria: [
        { key: "source_name", field: "source_name", label: "Tên trong tệp", type: "char", placeholder: "Tên trong tệp…" },
        { key: "machine_code", field: "machine_code", label: "Mã máy", type: "char", placeholder: "Mã máy…" },
        { key: "work_date", field: "work_date", label: "Ngày công", type: "date" },
        { key: "sheet_name", field: "sheet_name", label: "Trang", type: "char", placeholder: "Tên trang…" },
        { key: "state", field: "state", label: "Kết quả", type: "selection", multi: true },
        { key: "kind", field: "kind", label: "Loại dòng", type: "selection", multi: true },
        { key: "issue_open", field: "issue_open", label: "Đang chờ xử lý", type: "boolean" },
    ],
});

registerTableFilterProfile("tp.hr.attendance.code::codes", {
    criteria: [
        { key: "machine_code", field: "machine_code", label: "Mã máy", type: "char", placeholder: "Mã máy…" },
        { key: "employee_id", field: "employee_id", label: "Nhân viên", type: "many2one" },
        { key: "source", field: "source", label: "Nguồn", type: "selection" },
    ],
});

registerTableFilterProfile("tp.hr.attendance.rule::rules", {
    criteria: [
        { key: "name", field: "name", label: "Tên quy tắc", type: "char", placeholder: "Tên quy tắc…" },
        { key: "date_from", field: "date_from", label: "Áp dụng từ", type: "date" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection" },
    ],
});

registerTableFilterProfile("tp.hr.attendance.assignment::assignments", {
    criteria: [
        { key: "user_id", field: "user_id", label: "Người phụ trách", type: "many2one" },
        { key: "can_import", field: "can_import", label: "Nhập dữ liệu", type: "boolean" },
        { key: "can_review", field: "can_review", label: "Xuất bảng công phạm vi", type: "boolean" },
        { key: "can_lock", field: "can_lock", label: "Chốt kỳ", type: "boolean" },
        { key: "active", field: "active", label: "Đang hiệu lực", type: "boolean" },
    ],
});

registerTableFilterProfile("tp.hr.attendance.log::logs", {
    criteria: [
        { key: "action", field: "action", label: "Thao tác", type: "char", placeholder: "Thao tác…" },
        { key: "actor_id", field: "actor_id", label: "Người thực hiện", type: "many2one" },
        { key: "model", field: "model", label: "Đối tượng", type: "char", placeholder: "Đối tượng…" },
        { key: "create_date", field: "create_date", label: "Thời điểm", type: "datetime" },
    ],
});
