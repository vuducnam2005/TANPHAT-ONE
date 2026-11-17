import { Component, useProps, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { listView } from "@web/views/list/list_view";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { formatDateTime } from "@web/core/l10n/dates";
import { render } from "@web/owl2/utils";
import { PAGE_SIZE_OPTIONS, tablePageKey, readPageSize, writePageSize } from "../prefs";

export class HrListModel extends RelationalModel {
    _getNextConfig(currentConfig, params) {
        const nextConfig = super._getNextConfig(currentConfig, params);
        if (
            nextConfig.resModel === "hr.employee" &&
            !nextConfig.isMonoRecord &&
            !nextConfig.context?.tp_hr_relation &&
            nextConfig.fields?.department_id
        ) {
            // Department sections belong to the list layout, independent of search facets.
            const groupBy = nextConfig.groupBy || [];
            nextConfig.groupBy = ["department_id", ...groupBy.filter((name) => name !== "department_id")];
        }
        return nextConfig;
    }
}

export class HrTableTools extends Component {
    static template = "tp_hr_workspace.TableTools";
    props = useProps();
    pageSizes = PAGE_SIZE_OPTIONS;
    state = proxy({busy:false, error:""});
    async changeSize(ev) {
        const controller = this.props.controller;
        const limit = Number(ev.target.value);
        if (this.state.busy || controller.editedRecord || !PAGE_SIZE_OPTIONS.includes(limit)) return;
        this.state.busy = true;
        this.state.error = "";
        try {
            await controller.model.root.load({limit, offset: 0});
            writePageSize(controller.hrPageKey, limit);
            render(controller);
        } catch {
            this.state.error = "Không tải được trang. Hãy chọn lại số dòng để thử lại.";
            ev.target.value = String(controller.model.root.limit);
        } finally { this.state.busy = false; }
    }
}

export class HrListRenderer extends ListRenderer {
    static template = "tp_hr_workspace.ListRenderer";
    static recordRowTemplate = "tp_hr_workspace.RecordRow";
    static groupRowTemplate = "tp_hr_workspace.GroupRow";
    get getEmptyRowIds() { return []; }
    getActiveColumns() {
        const columns = super.getActiveColumns();
        return this.props.list.resModel === "hr.employee" && this.props.list.groupBy?.includes("department_id")
            ? columns.filter(column => column.name !== "department_id") : columns;
    }
    getGroupText(group) {
        return `${group.count} ${this.props.list.resModel === "hr.employee" ? "thành viên" : "bản ghi"}`;
    }
    hrGroupLabel(group) {
        return this.props.list.resModel === "hr.employee" && group.groupByField.name === "department_id" && !group.value
            ? "Chưa khai báo phòng ban" : group.displayName;
    }
}

const TABLE_CONTENT = {
    "hr.employee": ["Danh sách nhân viên", "Thông tin công việc, liên hệ và tài khoản trong phạm vi được xem.", "Thêm nhân viên", "Chưa có nhân viên"],
    "hr.department": ["Phòng ban và đơn vị", "Cơ cấu tổ chức, người quản lý và nhân viên đang sử dụng hồ sơ.", "Thêm phòng ban", "Chưa có phòng ban"],
    "hr.job": ["Chức vụ", "Vị trí nhân sự và phòng ban áp dụng. Chức vụ không tự cấp quyền hệ thống.", "Thêm chức vụ", "Chưa có chức vụ"],
    "hr.work.location": ["Nơi làm việc", "Quản lý địa điểm để phân công nơi làm việc cho nhân viên.", "Thêm nơi làm việc", "Chưa có nơi làm việc"],
    "hr.employee.category": ["Nhãn nhân viên", "Phân loại hồ sơ bằng nhãn; nhãn không thay đổi phòng ban hoặc quyền.", "Thêm nhãn nhân viên", "Chưa có nhãn nhân viên"],
    "tp.hr.import.batch": ["Nhập và đối chiếu", "Chọn tệp, xem trước và đối chiếu trước khi áp dụng vào hồ sơ.", "Tạo lô nhập", "Chưa có lô nhập"],
    "hr.employee.public": ["Danh bạ nhân viên", "Chỉ xem: thông tin công việc của đồng nghiệp. Hợp đồng, lương và thông tin riêng tư không hiển thị.", "", "Chưa có nhân viên"],
    "tp.hr.import.line": ["Đối chiếu từng dòng", "Rà soát ánh xạ và xử lý xung đột trước khi áp dụng lô nhập.", "", "Không có dòng đối chiếu"],
};

import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";
import "./filter_profiles";

export class HrListController extends ListController {
    static template = "tp_hr_workspace.ListView";
    static components = {...ListController.components, HrTableTools, TpTableFilterBar};
    get className() { return `${super.className || ""} o_tp_hr_table${this.props.resModel === "hr.employee" ? " o_tp_hr_employee_list" : ""}`; }
    get hrContent() { return TABLE_CONTENT[this.props.resModel] || [this.env.config.displayName || "Danh sách HR", "Quản lý danh mục nhân sự trong phạm vi được xem.", "Thêm mới", "Chưa có dữ liệu"]; }
    get hrHasFilters() { return Boolean(this.env.searchModel?.facets.length); }
    get hrMissing() { return Boolean(this.props.context?.tp_hr_missing); }
    clearHrFilters() { this.env.searchModel.clearQuery(); }
    get hrPageKey() { return tablePageKey(this.props.resModel, this.env.config.actionId, this.env.config.viewId); }
    get modelParams() {
        const params = super.modelParams;
        if (params.config) {
            params.config.openGroupsByDefault = true;
        }
        const limit = readPageSize(this.hrPageKey);
        return this.props.state?.modelState ? params : {...params, limit, groupsLimit: limit};
    }
}

registry.category("views").add("tp_hr_table", {
    ...listView,
    Model: HrListModel,
    Controller: HrListController,
    Renderer: HrListRenderer,
    buttonTemplate: "tp_hr_workspace.ListButtons",
});

export class HrIdentityCell extends Component {
    static template = "tp_hr_workspace.IdentityCell";
    props = useProps(standardFieldProps);
    get isEmployee() { return this.props.record.resModel === "hr.employee"; }
}
registry.category("fields").add("tp_hr_identity", {component: HrIdentityCell, supportedTypes: ["char"]});

export class HrActiveCell extends Component {
    static template = "tp_hr_workspace.ActiveCell";
    props = useProps(standardFieldProps);
}
registry.category("fields").add("tp_hr_active", {component: HrActiveCell, supportedTypes: ["boolean"]});

export class HrEmploymentCell extends Component {
    static template = "tp_hr_workspace.EmploymentCell";
    props = useProps(standardFieldProps);
    get value() { return this.props.record.data[this.props.name] || ""; }
    get label() { return {short_term:"Ngắn hạn", long_term:"Dài hạn", outsourced:"Thuê khoán"}[this.value] || "Chưa khai báo"; }
    change(ev) { return this.props.record.update({[this.props.name]: ev.target.value || false}); }
}
registry.category("fields").add("tp_hr_employment", {component: HrEmploymentCell, supportedTypes: ["selection"]});

export class HrCountCell extends Component {
    static template = "tp_hr_workspace.CountCell";
    props = useProps(standardFieldProps);
    setup() { this.orm = useService("orm"); this.action = useService("action"); }
    async open() { const action = await this.orm.call(this.props.record.resModel, "action_tp_employees", [[this.props.record.resId]]); return this.action.doAction(action); }
}
registry.category("fields").add("tp_hr_count", {component: HrCountCell, supportedTypes: ["integer"]});

export class HrDateTimeCell extends Component {
    static template = "tp_hr_workspace.DateTimeCell";
    props = useProps(standardFieldProps);
    get value() { const value = this.props.record.data[this.props.name]; return value ? formatDateTime(value, {format: "dd/MM/yyyy HH:mm:ss"}) : ""; }
}
registry.category("fields").add("tp_hr_datetime", {component: HrDateTimeCell, supportedTypes: ["datetime"]});

