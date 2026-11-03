import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { PROJECTION_MODEL, loadInto, openRecord } from "../shared/utils";

export class DemoFinance extends Component {
    static template = "tp_demo_workspace.Finance";
    static components = { ControlPanel };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = proxy({ loading: true, error: null, data: null });
        this.load();
    }

    load() {
        return loadInto(this.state, () => this.orm.call(PROJECTION_MODEL, "get_finance", []));
    }

    openContract(row) {
        return openRecord(this.actionService, "tp.contract", row.id);
    }

    openAmounts() {
        return this.actionService.doAction("tp_demo_workspace.action_demo_line_amounts");
    }
}

registry.category("actions").add("tp_demo_workspace.finance", DemoFinance);
