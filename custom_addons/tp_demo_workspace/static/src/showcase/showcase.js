import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { PROJECTION_MODEL, loadInto } from "../shared/utils";

// Screen-reader text for the stepper dots, which carry state by colour and shape.
const STEP_STATES = {
    done: " — đã xong",
    current: " — đang ở bước này",
    returned: " — bị trả lại",
    todo: " — chưa tới",
};

/**
 * One component for every illustrative screen (survey, design, request, bid,
 * staffing). Rows come from the projection, already cut to the caller's
 * projects and financial grants; only status and text filters run here.
 */
export class DemoShowcase extends Component {
    static template = "tp_demo_workspace.Showcase";
    static components = { ControlPanel };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        const params = this.props.action.params || {};
        const context = this.props.action.context || {};
        this.screen = params.screen;
        this.state = proxy({
            loading: true,
            error: null,
            data: null,
            projectId: context.active_id || false,
            status: "",
            query: "",
            selectedKey: null,
        });
        this.load();
    }

    load() {
        return loadInto(this.state, () =>
            this.orm.call(PROJECTION_MODEL, "get_showcase", [this.screen], { project_id: this.state.projectId || false })
        );
    }

    onProjectChange(ev) {
        this.state.projectId = parseInt(ev.target.value) || false;
        this.state.selectedKey = null;
        this.props.updateActionState?.({ active_id: this.state.projectId });
        return this.load();
    }

    onStatusChange(ev) {
        this.state.status = ev.target.value;
    }

    onQueryInput(ev) {
        this.state.query = ev.target.value;
    }

    get statuses() {
        const seen = new Map();
        for (const row of this.state.data.rows) {
            seen.set(row.status, row.status_label);
        }
        return [...seen].map(([key, label]) => ({ key, label }));
    }

    get rows() {
        const query = this.state.query.trim().toLowerCase();
        return this.state.data.rows.filter((row) => {
            if (this.state.status && row.status !== this.state.status) {
                return false;
            }
            if (!query) {
                return true;
            }
            const haystack = [row.key, row.name, row.project, ...Object.values(row.columns)].join(" ").toLowerCase();
            return haystack.includes(query);
        });
    }

    get selected() {
        const rows = this.rows;
        return rows.find((row) => row.key === this.state.selectedKey) || rows[0] || null;
    }

    select(row) {
        this.state.selectedKey = row.key;
    }

    stepState(step) {
        return STEP_STATES[step.state] || "";
    }
}

registry.category("actions").add("tp_demo_workspace.showcase", DemoShowcase);
