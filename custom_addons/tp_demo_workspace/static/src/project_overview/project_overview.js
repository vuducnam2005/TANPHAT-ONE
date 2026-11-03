import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { PROJECTION_MODEL, loadInto, openList, openRecord } from "../shared/utils";

export class DemoProjectOverview extends Component {
    static template = "tp_demo_workspace.ProjectOverview";
    static components = { ControlPanel };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        const context = this.props.action.context || {};
        this.state = proxy({ loading: true, error: null, data: null, projectId: context.active_id || false });
        this.load();
    }

    load() {
        return loadInto(this.state, () =>
            this.orm.call(PROJECTION_MODEL, "get_project_overview", [], { project_id: this.state.projectId || false })
        );
    }

    onProjectChange(ev) {
        this.state.projectId = parseInt(ev.target.value) || false;
        // Keep the selected project in the URL so a reload or breadcrumb keeps context.
        this.props.updateActionState?.({ active_id: this.state.projectId });
        return this.load();
    }

    get selectedId() {
        return this.state.data?.project?.id || false;
    }

    openSection(key, label) {
        const data = this.state.data;
        return openList(this.actionService, data.actions[key], `${data.project.code} · ${label}`);
    }

    openProjectForm() {
        return openRecord(this.actionService, "project.project", this.state.data.project.id);
    }

    openRecord(model, id) {
        return openRecord(this.actionService, model, id);
    }

    openScreen(xmlid) {
        return this.actionService.doAction(xmlid);
    }

    stageWidth(stage) {
        const total = this.state.data.task_stages.reduce((sum, item) => sum + item.count, 0) || 1;
        return `width: ${Math.max((stage.count / total) * 100, 4)}%`;
    }
}

registry.category("actions").add("tp_demo_workspace.project_overview", DemoProjectOverview);
