import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { PROJECTION_MODEL, loadInto, openList, openProjectOverview, openRecord } from "../shared/utils";

const LENS_STORAGE_KEY = "tp_demo_workspace.lens";

export class DemoDashboard extends Component {
    static template = "tp_demo_workspace.Dashboard";
    static components = { ControlPanel };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = proxy({ loading: true, error: null, data: null, lens: this.readLens() });
        this.load();
    }

    load() {
        return loadInto(this.state, () => this.orm.call(PROJECTION_MODEL, "get_dashboard", []));
    }

    // Lenses only reorder lanes on screen; data and rights stay the same.
    readLens() {
        try {
            return window.localStorage.getItem(LENS_STORAGE_KEY) || "executive";
        } catch {
            return "executive";
        }
    }

    onLensChange(ev) {
        this.state.lens = ev.target.value;
        try {
            window.localStorage.setItem(LENS_STORAGE_KEY, this.state.lens);
        } catch {
            // Storage may be blocked; the lens still applies for this view.
        }
    }

    get lanes() {
        const data = this.state.data;
        const lens = data.lenses.find((item) => item.key === this.state.lens) || data.lenses[0];
        const byKey = Object.fromEntries(data.lanes.map((lane) => [lane.key, lane]));
        return lens.order.map((key) => byKey[key]).filter(Boolean);
    }

    get lensValue() {
        const data = this.state.data;
        return data.lenses.some((item) => item.key === this.state.lens) ? this.state.lens : data.lenses[0].key;
    }

    openKpi(kpi) {
        return openList(this.actionService, kpi, kpi.label);
    }

    openNode(chain, node) {
        if (node.overview) {
            return openProjectOverview(this.actionService, node.overview);
        }
        return openList(this.actionService, node, `${chain.code} · ${node.label}`);
    }

    openAttention(item) {
        if (item.res_model) {
            return openRecord(this.actionService, item.res_model, item.res_id);
        }
        return openList(this.actionService, item, item.title);
    }

    openModule(module) {
        if (!module.locked && module.action) {
            return this.actionService.doAction(module.action);
        }
    }
}

registry.category("actions").add("tp_demo_workspace.dashboard", DemoDashboard);
