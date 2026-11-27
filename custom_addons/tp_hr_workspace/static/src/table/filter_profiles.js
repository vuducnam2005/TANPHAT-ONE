/** @odoo-module **/
import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";

/**
 * HR Table Filter Profiles (S1 — TP HR).
 * Each criterion uses native SearchModel fields validated against get_views searchViewFields.
 */
registerTableFilterProfile("hr.employee", {
    criteria: [
        { key: "name", field: "name", label: "Họ tên", type: "char", placeholder: "Tìm họ tên…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "job_id", field: "job_id", label: "Chức vụ", type: "many2one", allowEmpty: true },
        { key: "tp_employment_kind", field: "tp_employment_kind", label: "Loại hình", type: "selection", multi: true, allowEmpty: true },
        { key: "tp_account_status", field: "tp_account_status", label: "Tài khoản", type: "selection", multi: true },
    ],
});

registerTableFilterProfile("hr.employee::missing", {
    criteria: [
        { key: "name", field: "name", label: "Họ tên", type: "char", placeholder: "Tìm họ tên…" },
        {
            key: "missing_reason",
            type: "preset",
            label: "Loại thông tin thiếu",
            multi: true,
            requireFields: ["tp_employee_code", "department_id", "job_id"],
            options: [
                { key: "code", label: "Thiếu mã nhân viên", domain: [["tp_employee_code", "=", false]] },
                { key: "dept", label: "Chưa có phòng ban", domain: [["department_id", "=", false]] },
                { key: "job", label: "Chưa có chức vụ", domain: ["&", ["job_id", "=", false], ["tp_source_title", "=", false]] },
            ],
        },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "tp_employment_kind", field: "tp_employment_kind", label: "Loại hình", type: "selection", multi: true, allowEmpty: true },
    ],
});

registerTableFilterProfile("hr.employee::archived", {
    criteria: [
        { key: "name", field: "name", label: "Họ tên", type: "char", placeholder: "Tìm họ tên…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "job_id", field: "job_id", label: "Chức vụ", type: "many2one", allowEmpty: true },
        { key: "tp_employment_kind", field: "tp_employment_kind", label: "Loại hình", type: "selection", multi: true, allowEmpty: true },
        { key: "tp_account_status", field: "tp_account_status", label: "Tài khoản", type: "selection", multi: true },
    ],
});

registerTableFilterProfile("hr.employee::pending", {
    criteria: [
        { key: "name", field: "name", label: "Họ tên", type: "char", placeholder: "Tìm họ tên…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "job_id", field: "job_id", label: "Chức vụ", type: "many2one", allowEmpty: true },
        { key: "tp_employment_kind", field: "tp_employment_kind", label: "Loại hình", type: "selection", multi: true, allowEmpty: true },
        { key: "active", field: "active", label: "Hồ sơ", type: "boolean", positiveLabel: "Đang làm việc", negativeLabel: "Đã lưu trữ" },
    ],
});

registerTableFilterProfile("hr.employee.public::directory", {
    criteria: [
        { key: "tp_search_identity", field: "tp_search_identity", label: "Họ tên / Mã NV", type: "char", placeholder: "Tìm họ tên hoặc mã NV…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "job_id", field: "job_id", label: "Chức vụ", type: "many2one", allowEmpty: true },
        { key: "work_location_id", field: "work_location_id", label: "Nơi làm việc", type: "many2one", allowEmpty: true },
    ],
});

registerTableFilterProfile("hr.department", {
    criteria: [
        { key: "name", field: "name", label: "Phòng ban", type: "char", placeholder: "Tên phòng ban…" },
        { key: "parent_id", field: "parent_id", label: "Đơn vị cấp trên", type: "many2one", allowEmpty: true },
        { key: "manager_id", field: "manager_id", label: "Quản lý", type: "many2one", allowEmpty: true },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang hoạt động", negativeLabel: "Đã lưu trữ" },
    ],
});

registerTableFilterProfile("hr.job", {
    criteria: [
        { key: "name", field: "name", label: "Chức vụ", type: "char", placeholder: "Tên chức vụ…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang sử dụng", negativeLabel: "Đã lưu trữ" },
    ],
});

registerTableFilterProfile("hr.work.location", {
    criteria: [
        { key: "name", field: "name", label: "Địa điểm", type: "char", placeholder: "Tên địa điểm…" },
        { key: "location_type", field: "location_type", label: "Loại địa điểm", type: "selection", multi: true },
        { key: "address_id", field: "address_id", label: "Địa chỉ", type: "many2one", allowEmpty: true },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang dùng", negativeLabel: "Đã lưu trữ" },
    ],
});

registerTableFilterProfile("hr.employee.category", {
    criteria: [
        { key: "name", field: "name", label: "Tên nhãn", type: "char", placeholder: "Nhập tên nhãn…" },
    ],
});

registerTableFilterProfile("hr.resume.line.type", {
    criteria: [
        { key: "name", field: "name", label: "Loại năng lực", type: "char", placeholder: "Nhập tên loại…" },
        { key: "is_course", field: "is_course", label: "Khóa học", type: "boolean", positiveLabel: "Khóa đào tạo", negativeLabel: "Mục khác" },
    ],
});

registerTableFilterProfile("hr.skill.type", {
    criteria: [
        { key: "name", field: "name", label: "Loại kỹ năng", type: "char", placeholder: "Nhập tên kỹ năng…" },
        { key: "is_certification", field: "is_certification", label: "Chứng chỉ", type: "boolean", positiveLabel: "Là chứng chỉ", negativeLabel: "Kỹ năng thường" },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang dùng", negativeLabel: "Đã lưu trữ" },
    ],
});

registerTableFilterProfile("tp.hr.import.batch", {
    criteria: [
        { key: "name", field: "name", label: "Tên lô", type: "char", placeholder: "Tìm tên lô…" },
        { key: "file_name", field: "file_name", label: "Tệp nguồn", type: "char", placeholder: "Tên tệp…" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "create_date", field: "create_date", label: "Ngày tạo", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.hr.import.line", {
    criteria: [
        { key: "name", field: "name", label: "Họ tên nguồn", type: "char", placeholder: "Họ tên…" },
        { key: "source_code", field: "source_code", label: "Mã nguồn", type: "char", placeholder: "Mã NV…" },
        { key: "action", field: "action", label: "Kết quả đối chiếu", type: "selection", multi: true },
        { key: "department_id", field: "department_id", label: "Đơn vị đối chiếu", type: "many2one", allowEmpty: true },
        { key: "review_update", field: "review_update", label: "Đã rà soát", type: "boolean", positiveLabel: "Đã rà soát", negativeLabel: "Chưa rà soát" },
    ],
});

registerTableFilterProfile("tp.hr.employee.audit", {
    criteria: [
        { key: "employee_code", field: "employee_code", label: "Mã NV", type: "char", placeholder: "Mã nhân viên…" },
        { key: "action", field: "action", label: "Hành động", type: "selection", multi: true },
        { key: "account_action", field: "account_action", label: "Tài khoản", type: "selection", multi: true },
        { key: "actor_id", field: "actor_id", label: "Người thực hiện", type: "many2one" },
        { key: "create_date", field: "create_date", label: "Thời điểm", type: "datetime" },
    ],
});

registerTableFilterProfile("tp.hr.contract.document", {
    criteria: [
        { key: "employee_id", field: "employee_id", label: "Nhân viên", type: "many2one" },
        { key: "number", field: "number", label: "Số hợp đồng", type: "char", placeholder: "Số HĐ…" },
        { key: "kind", field: "kind", label: "Loại hợp đồng", type: "selection", multi: true },
        { key: "signed_date", field: "signed_date", label: "Ngày ký", type: "date" },
    ],
});

registerTableFilterProfile("tp.bank", {
    criteria: [
        { key: "short_name", field: "short_name", label: "Ngân hàng / Mã / BIN", type: "char", placeholder: "Tìm tên, mã hoặc BIN…" },
        { key: "kind", field: "kind", label: "Phân loại", type: "selection", multi: true },
        { key: "napas_transfer", field: "napas_transfer", label: "Chuyển nhanh NAPAS", type: "boolean", positiveLabel: "Hỗ trợ NAPAS", negativeLabel: "Chưa hỗ trợ" },
        { key: "active", field: "active", label: "Trạng thái", type: "boolean", positiveLabel: "Đang dùng", negativeLabel: "Ngừng dùng" },
    ],
});
