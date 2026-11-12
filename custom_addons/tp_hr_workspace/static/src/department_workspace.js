import { Component, onWillStart, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { useProps } from "@odoo/owl";

export class DepartmentWorkspace extends Component {
    static template = "tp_hr_workspace.DepartmentWorkspace";
    props = useProps({...standardActionServiceProps});
    workspace = signal(null);
    setup() {
        const orm = useService("orm");
        onWillStart(async () => this.workspace.set(await orm.call("res.users", "get_tp_department_workspace", [])));
    }
}
registry.category("actions").add("tp_department_workspace", DepartmentWorkspace);
