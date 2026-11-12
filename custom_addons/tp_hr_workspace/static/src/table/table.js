import { Component, useProps, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { listView } from "@web/views/list/list_view";
import { patch } from "@web/core/utils/patch";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { render } from "@web/owl2/utils";
import { PAGE_SIZE_OPTIONS, tablePageKey, readPageSize, writePageSize } from "../prefs";

export class HrTableTools extends Component {
    static template = "tp_hr_workspace.TableTools";
    props = useProps();
    pageSizes = PAGE_SIZE_OPTIONS;
    state = proxy({busy:false});
    async changeSize(ev) {
        const controller = this.props.controller;
        const limit = Number(ev.target.value);
        if (this.state.busy || controller.editedRecord || !PAGE_SIZE_OPTIONS.includes(limit)) return;
        this.state.busy = true;
        try {
            await controller.model.root.load({limit, offset: 0});
            writePageSize(controller.hrPageKey, limit);
            render(controller);
        } finally { this.state.busy = false; }
    }
}

export class HrRelationalModel extends RelationalModel {
    _getNextConfig(currentConfig, params) {
        const config = super._getNextConfig(currentConfig, params);
        if (config.resModel === "hr.employee" && (!config.groupBy || !config.groupBy.length)) {
            config.groupBy = ["department_id"];
            config.openGroupsByDefault = true;
        }
        return config;
    }
}

export class HrListRenderer extends ListRenderer {
    getGroupText(group) {
        return `${group.count} thành viên`;
    }
}

patch(ListRenderer.prototype, {
    getGroupText(group) {
        return `${group.count} thành viên`;
    },
});

export class HrListController extends ListController {
    static template = "tp_hr_workspace.ListView";
    static components = {...ListController.components, HrTableTools};
    get hrPageKey() { return tablePageKey(this.props.resModel, this.env.config.actionId, this.env.config.viewId); }
    get modelParams() {
        const params = super.modelParams;
        if (params.config) {
            params.config.openGroupsByDefault = true;
        }
        return this.props.state?.modelState ? params : {...params, limit: readPageSize(this.hrPageKey)};
    }
}

registry.category("views").add("tp_hr_table", {
    ...listView,
    Controller: HrListController,
    Model: HrRelationalModel,
    Renderer: HrListRenderer,
});

