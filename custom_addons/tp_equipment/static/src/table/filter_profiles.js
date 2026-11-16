import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";

/** DEC-044 filter profiles of the office-equipment tables (fields must be searchable). */
const EQUIPMENT_CRITERIA = [
    { key: "tp_search", field: "tp_search", label: "Tên / mã / serial", type: "char", placeholder: "Tên, mã TB, serial, model…" },
    { key: "category_id", field: "category_id", label: "Phân loại", type: "many2one", allowEmpty: true },
    { key: "tp_custody", field: "tp_custody", label: "Nơi giữ", type: "selection", multi: true },
    { key: "tp_employee_id", field: "tp_employee_id", label: "Người đang giữ", type: "many2one", allowEmpty: true },
    { key: "tp_current_department_id", field: "tp_current_department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
    { key: "tp_location_id", field: "tp_location_id", label: "Vị trí", type: "many2one", allowEmpty: true },
    { key: "tp_availability", field: "tp_availability", label: "Khả dụng", type: "selection", multi: true },
    { key: "tp_technical_state", field: "tp_technical_state", label: "Tình trạng kỹ thuật", type: "selection", multi: true },
    { key: "tp_warranty_state", field: "tp_warranty_state", label: "Bảo hành", type: "selection", multi: true },
    { key: "tp_ownership", field: "tp_ownership", label: "Sở hữu", type: "selection", multi: true },
    { key: "tp_purchase_date", field: "tp_purchase_date", label: "Ngày mua / nhận", type: "date" },
];
const EQUIPMENT_STOCK_CRITERIA = [
    { key: "tp_search", field: "tp_search", label: "Tên / mã / serial", type: "char", placeholder: "Tên, mã TB, serial, model…" },
    { key: "category_id", field: "category_id", label: "Phân loại", type: "many2one", allowEmpty: true },
    { key: "tp_technical_state", field: "tp_technical_state", label: "Tình trạng kỹ thuật", type: "selection", multi: true },
    { key: "tp_availability", field: "tp_availability", label: "Khả năng cấp phát", type: "selection", multi: true },
    { key: "tp_location_id", field: "tp_location_id", label: "Vị trí kho", type: "many2one", allowEmpty: true },
    { key: "tp_warranty_state", field: "tp_warranty_state", label: "Bảo hành", type: "selection", multi: true },
    { key: "tp_purchase_date", field: "tp_purchase_date", label: "Ngày mua / nhận", type: "date" },
];
// EQUIP-UI-002: the users table scope (identified HR employee) lives in the action domain; no "Nơi giữ" here.
const EQUIPMENT_USER_CRITERIA = [
    { key: "tp_search", field: "tp_search", label: "Tìm nhanh", type: "char", placeholder: "Tên NV, mã NV, mã TB, model…" },
    { key: "tp_current_department_id", field: "tp_current_department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
    { key: "category_id", field: "category_id", label: "Loại thiết bị", type: "many2one", allowEmpty: true },
    { key: "tp_employee_id", field: "tp_employee_id", label: "Người sử dụng", type: "many2one" },
    { key: "tp_technical_state", field: "tp_technical_state", label: "Tình trạng", type: "selection", multi: true },
    { key: "tp_warranty_state", field: "tp_warranty_state", label: "Bảo hành", type: "selection", multi: true },
    { key: "tp_ownership", field: "tp_ownership", label: "Sở hữu", type: "selection", multi: true },
    { key: "tp_purchase_date", field: "tp_purchase_date", label: "Ngày mua / nhận", type: "date" },
];
const EQUIPMENT_SHARED_CRITERIA = [
    { key: "tp_search", field: "tp_search", label: "Tìm nhanh", type: "char", placeholder: "Tên, mã TB, serial, model…" },
    { key: "tp_custody", field: "tp_custody", label: "Nơi giữ", type: "selection", multi: true },
    { key: "category_id", field: "category_id", label: "Loại thiết bị", type: "many2one", allowEmpty: true },
    { key: "tp_current_department_id", field: "tp_current_department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
    { key: "tp_location_id", field: "tp_location_id", label: "Vị trí", type: "many2one", allowEmpty: true },
    { key: "tp_technical_state", field: "tp_technical_state", label: "Tình trạng", type: "selection", multi: true },
    { key: "tp_warranty_state", field: "tp_warranty_state", label: "Bảo hành", type: "selection", multi: true },
];
registerTableFilterProfile("maintenance.equipment", { criteria: EQUIPMENT_CRITERIA });
// EQUIP-SIMPLE-003: the single "Thiết bị" list. Scope + segment live in backend domains; these criteria add
// accent-insensitive search (tp_search: name, code, serial, model, brand, HR name/code) and 4 filters.
const EQUIPMENT_MAIN_CRITERIA = [
    { key: "tp_search", field: "tp_search", label: "Tìm nhanh", type: "char", placeholder: "Tên, mã TB, serial, tên / mã NV…" },
    { key: "tp_current_department_id", field: "tp_current_department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
    { key: "tp_employee_id", field: "tp_employee_id", label: "Người sử dụng", type: "many2one", allowEmpty: true },
    { key: "category_id", field: "category_id", label: "Loại thiết bị", type: "many2one", allowEmpty: true },
    { key: "tp_technical_state", field: "tp_technical_state", label: "Tình trạng máy", type: "selection", multi: true },
];
registerTableFilterProfile("maintenance.equipment::equipment_main", { criteria: EQUIPMENT_MAIN_CRITERIA });
registerTableFilterProfile("maintenance.equipment::equipment_users", { criteria: EQUIPMENT_USER_CRITERIA });
registerTableFilterProfile("maintenance.equipment::equipment_shared", { criteria: EQUIPMENT_SHARED_CRITERIA });
registerTableFilterProfile("maintenance.equipment::equipment", { criteria: EQUIPMENT_CRITERIA });
registerTableFilterProfile("maintenance.equipment::equipment_stock", { criteria: EQUIPMENT_STOCK_CRITERIA });

registerTableFilterProfile("maintenance.equipment.category", {
    criteria: [
        { key: "name", field: "name", label: "Phân loại", type: "char", placeholder: "Tên phân loại…" },
        { key: "tp_asset_class", field: "tp_asset_class", label: "Loại quản lý", type: "selection", multi: true },
    ],
});

registerTableFilterProfile("tp.equipment.location", {
    criteria: [
        { key: "name", field: "name", label: "Vị trí", type: "char", placeholder: "Tên hoặc mã vị trí…" },
        { key: "department_id", field: "department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
        { key: "work_location_id", field: "work_location_id", label: "Địa điểm làm việc", type: "many2one", allowEmpty: true },
    ],
});

registerTableFilterProfile("tp.equipment.move", {
    criteria: [
        { key: "name", field: "name", label: "Số phiếu", type: "char", placeholder: "PBG-…" },
        { key: "move_type", field: "move_type", label: "Loại phiếu", type: "selection", multi: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "target_employee_id", field: "target_employee_id", label: "Nhân viên nhận", type: "many2one", allowEmpty: true },
        { key: "target_department_id", field: "target_department_id", label: "Phòng ban nhận", type: "many2one", allowEmpty: true },
        { key: "date", field: "date", label: "Ngày lập", type: "date" },
    ],
});
registerTableFilterProfile("tp.equipment.move.line", {
    criteria: [
        { key: "equipment_id", field: "equipment_id", label: "Thiết bị", type: "many2one" },
        { key: "move_type", field: "move_type", label: "Loại phiếu", type: "selection", multi: true },
        { key: "to_employee_id", field: "to_employee_id", label: "Người nhận", type: "many2one", allowEmpty: true },
        { key: "from_employee_id", field: "from_employee_id", label: "Người giao", type: "many2one", allowEmpty: true },
        { key: "date", field: "date", label: "Ngày lập", type: "date" },
    ],
});
registerTableFilterProfile("tp.equipment.receipt", {
    criteria: [
        { key: "name", field: "name", label: "Số phiếu", type: "char", placeholder: "PNK-…" },
        { key: "document_ref", field: "document_ref", label: "Số chứng từ", type: "char" },
        { key: "source", field: "source", label: "Nguồn nhập", type: "selection", multi: true },
        { key: "supplier_id", field: "supplier_id", label: "Nhà cung cấp", type: "many2one", allowEmpty: true },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true },
        { key: "date", field: "date", label: "Ngày nhập", type: "date" },
    ],
});

registerTableFilterProfile("maintenance.request", { criteria: [
    {
        "key": "name",
        "field": "name",
        "label": "Nội dung",
        "type": "char"
    },
    {
        "key": "equipment_id",
        "field": "equipment_id",
        "label": "Thiết bị",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "tp_kind",
        "field": "tp_kind",
        "label": "Loại yêu cầu",
        "type": "selection",
        "multi": true
    },
    {
        "key": "tp_state",
        "field": "tp_state",
        "label": "Tiến trình",
        "type": "selection",
        "multi": true
    },
    {
        "key": "tp_reporter_employee_id",
        "field": "tp_reporter_employee_id",
        "label": "Người báo",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "tp_vendor_id",
        "field": "tp_vendor_id",
        "label": "Đơn vị sửa",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "tp_deadline",
        "field": "tp_deadline",
        "label": "Hạn xử lý",
        "type": "date"
    }
] });

registerTableFilterProfile("tp.equipment.proposal", { criteria: [
    {
        "key": "name",
        "field": "name",
        "label": "Số đề xuất",
        "type": "char"
    },
    {
        "key": "title",
        "field": "title",
        "label": "Nội dung",
        "type": "char"
    },
    {
        "key": "requester_employee_id",
        "field": "requester_employee_id",
        "label": "Người cần",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "requester_department_id",
        "field": "requester_department_id",
        "label": "Bộ phận",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "review_state",
        "field": "review_state",
        "label": "Rà soát",
        "type": "selection",
        "multi": true
    },
    {
        "key": "approval_state",
        "field": "approval_state",
        "label": "Kết quả duyệt",
        "type": "selection",
        "multi": true
    },
    {
        "key": "progress",
        "field": "progress",
        "label": "Tiến độ",
        "type": "selection",
        "multi": true
    },
    {
        "key": "date",
        "field": "date",
        "label": "Ngày",
        "type": "date"
    }
] });

registerTableFilterProfile("tp.equipment.proposal.line", { criteria: [
    {
        "key": "description",
        "field": "description",
        "label": "Nội dung",
        "type": "char"
    },
    {
        "key": "kind",
        "field": "kind",
        "label": "Phương án",
        "type": "selection",
        "multi": true
    },
    {
        "key": "equipment_id",
        "field": "equipment_id",
        "label": "Máy cũ",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "progress",
        "field": "progress",
        "label": "Tiến độ",
        "type": "selection",
        "multi": true
    }
] });

registerTableFilterProfile("tp.equipment.proposal.review", { criteria: [
    {
        "key": "action",
        "field": "action",
        "label": "Thao tác",
        "type": "selection",
        "multi": true
    },
    {
        "key": "user_id",
        "field": "user_id",
        "label": "Người ghi",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "state_to",
        "field": "state_to",
        "label": "Kết quả",
        "type": "selection",
        "multi": true
    }
] });

registerTableFilterProfile("tp.equipment.inventory", { criteria: [
    {
        "key": "name",
        "field": "name",
        "label": "Số kỳ",
        "type": "char"
    },
    {
        "key": "title",
        "field": "title",
        "label": "Nội dung",
        "type": "char"
    },
    {
        "key": "scope",
        "field": "scope",
        "label": "Phạm vi",
        "type": "selection",
        "multi": true
    },
    {
        "key": "state",
        "field": "state",
        "label": "Trạng thái",
        "type": "selection",
        "multi": true
    },
    {
        "key": "date",
        "field": "date",
        "label": "Ngày",
        "type": "date"
    }
] });

registerTableFilterProfile("tp.equipment.inventory.line", { criteria: [
    {
        "key": "equipment_id",
        "field": "equipment_id",
        "label": "Thiết bị",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "equipment_code",
        "field": "equipment_code",
        "label": "Mã",
        "type": "char"
    },
    {
        "key": "count_state",
        "field": "count_state",
        "label": "Kiểm đếm",
        "type": "selection",
        "multi": true
    },
    {
        "key": "result",
        "field": "result",
        "label": "Chênh lệch",
        "type": "selection",
        "multi": true
    },
    {
        "key": "actual_employee_id",
        "field": "actual_employee_id",
        "label": "Người giữ thực tế",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "actual_location_id",
        "field": "actual_location_id",
        "label": "Vị trí thực tế",
        "type": "many2one",
        "allowEmpty": true
    }
] });

registerTableFilterProfile("tp.equipment.import.batch", { criteria: [
    {
        "key": "name",
        "field": "name",
        "label": "Đợt nhập",
        "type": "char"
    },
    {
        "key": "file_name",
        "field": "file_name",
        "label": "Tên tệp",
        "type": "char"
    },
    {
        "key": "kind",
        "field": "kind",
        "label": "Nguồn",
        "type": "selection",
        "multi": true
    },
    {
        "key": "state",
        "field": "state",
        "label": "Trạng thái",
        "type": "selection",
        "multi": true
    }
] });

registerTableFilterProfile("tp.equipment.import.line", { criteria: [
    {
        "key": "sheet_name",
        "field": "sheet_name",
        "label": "Sheet",
        "type": "char"
    },
    {
        "key": "disposition",
        "field": "disposition",
        "label": "Phân loại",
        "type": "selection",
        "multi": true
    },
    {
        "key": "name",
        "field": "name",
        "label": "Nội dung",
        "type": "char"
    },
    {
        "key": "employee_id",
        "field": "employee_id",
        "label": "Nhân viên",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "department_id",
        "field": "department_id",
        "label": "Phòng ban",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "location_id",
        "field": "location_id",
        "label": "Vị trí",
        "type": "many2one",
        "allowEmpty": true
    }
] });

registerTableFilterProfile("tp.equipment.import.column", { criteria: [
    {
        "key": "sheet_name",
        "field": "sheet_name",
        "label": "Sheet",
        "type": "char"
    },
    {
        "key": "source_label",
        "field": "source_label",
        "label": "Tiêu đề nguồn",
        "type": "char"
    },
    {
        "key": "target_field",
        "field": "target_field",
        "label": "Trường đích",
        "type": "selection",
        "multi": true
    }
] });

registerTableFilterProfile("tp.equipment.import.alias", { criteria: [
    {
        "key": "source_text",
        "field": "source_text",
        "label": "Tên nguồn",
        "type": "char"
    },
    {
        "key": "employee_id",
        "field": "employee_id",
        "label": "Nhân viên",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "department_id",
        "field": "department_id",
        "label": "Phòng ban",
        "type": "many2one",
        "allowEmpty": true
    },
    {
        "key": "location_id",
        "field": "location_id",
        "label": "Vị trí",
        "type": "many2one",
        "allowEmpty": true
    }
] });

registerTableFilterProfile("tp.equipment.software", { criteria: [
    { key: "name", field: "name", label: "Tên / phiên bản", type: "char" },
    { key: "kind", field: "kind", label: "Loại", type: "selection", multi: true },
    { key: "license_declared", field: "license_declared", label: "Khai báo", type: "selection", multi: true },
    { key: "license_check", field: "license_check", label: "Kiểm chứng", type: "selection", multi: true },
] });
registerTableFilterProfile("tp.equipment.meter", { criteria: [
    { key: "date", field: "date", label: "Ngày đọc", type: "date" },
    { key: "source", field: "source", label: "Nguồn", type: "selection", multi: true },
    { key: "note", field: "note", label: "Ghi chú", type: "char" },
] });
registerTableFilterProfile("tp.equipment.receipt.line", { criteria: [
    { key: "name", field: "name", label: "Thiết bị", type: "char" },
    { key: "serial_no", field: "serial_no", label: "Serial", type: "char" },
    { key: "category_id", field: "category_id", label: "Phân loại", type: "many2one" },
    { key: "technical_state", field: "technical_state", label: "Tình trạng", type: "selection", multi: true },
] });

// EQUIP-SIMPLE-003 "Yêu cầu đề xuất": person, department, need, date, review state.
registerTableFilterProfile("tp.equipment.proposal::proposal_simple", { criteria: [
    { key: "name", field: "name", label: "Số đề xuất", type: "char", placeholder: "Số đề xuất…" },
    { key: "title", field: "title", label: "Nội dung", type: "char", placeholder: "Nội dung đề xuất…" },
    { key: "requester_employee_id", field: "requester_employee_id", label: "Người đề xuất", type: "many2one", allowEmpty: true },
    { key: "requester_department_id", field: "requester_department_id", label: "Phòng ban", type: "many2one", allowEmpty: true },
    { key: "need_type", field: "need_type", label: "Nhu cầu", type: "selection", multi: true },
    { key: "date", field: "date", label: "Ngày đề xuất", type: "date" },
    { key: "review_state", field: "review_state", label: "Trạng thái rà soát", type: "selection", multi: true },
] });
