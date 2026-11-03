import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

/** Systray marker present on every web client screen of the demo database. */
export class DemoEnvironmentBadge extends Component {
    static template = "tp_demo_workspace.DemoEnvironmentBadge";
}

registry.category("systray").add("tp_demo_workspace.environment_badge", { Component: DemoEnvironmentBadge }, { sequence: 1 });
