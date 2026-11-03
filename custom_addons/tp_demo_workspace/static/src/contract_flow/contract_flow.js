import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { PROJECTION_MODEL, loadInto, openList, openRecord } from "../shared/utils";

// The review cycle drawn left to right; review_complete and cancelled sit apart.
const CYCLE = ["draft", "in_review", "returned"];

export class DemoContractFlow extends Component {
    static template = "tp_demo_workspace.ContractFlow";
    static components = { ControlPanel };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = proxy({ loading: true, error: null, data: null });
        this.load();
    }

    load() {
        return loadInto(this.state, () => this.orm.call(PROJECTION_MODEL, "get_contract_flow", []));
    }

    get cycleStates() {
        const byKey = Object.fromEntries(this.state.data.review_states.map((item) => [item.key, item]));
        return CYCLE.map((key) => byKey[key]);
    }

    get outerStates() {
        return this.state.data.review_states.filter((item) => !CYCLE.includes(item.key));
    }

    stateLabel(key) {
        return this.state.data.review_states.find((item) => item.key === key)?.label || key;
    }

    openState(item) {
        return openList(
            this.actionService,
            {
                action: this.state.data.action,
                domain: [["project_id.tp_code", "=like", "DEMO-%"], ["review_state", "=", item.key]],
            },
            `Phiên bản · ${item.label}`
        );
    }

    openRevision(revision) {
        return openRecord(this.actionService, "tp.contract.revision", revision.id);
    }

    openAll() {
        return this.actionService.doAction(this.state.data.action);
    }
}

registry.category("actions").add("tp_demo_workspace.contract_flow", DemoContractFlow);
