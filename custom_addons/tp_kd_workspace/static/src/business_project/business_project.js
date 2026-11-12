/** @odoo-module **/
import { registry } from "@web/core/registry";
import { buildM2OFieldDescription, Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { ButtonBox } from "@web/views/form/button_box/button_box";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

/** Native autocomplete/opening stays mounted; disclosure reads only the already loaded value. */
export class KdBusinessMany2OneField extends Many2OneField {
    static template = "tp_kd_workspace.BusinessMany2OneField";

    get fullName() {
        return this.props.record.data[this.props.name]?.display_name || "";
    }
}

registry.category("fields").add("tp_kd_bp_many2one", buildM2OFieldDescription(KdBusinessMany2OneField));

/** Same native slots/dropdown/actions, with the seven secondary links in one compact menu. */
export class KdBusinessRelatedBox extends ButtonBox {
    static template = "tp_kd_workspace.BusinessRelatedBox";
    get visibleButtons() { return []; }
    get additionalButtons() {
        return Object.entries(this.props.slots).filter(([, slot]) => this.isSlotVisible(slot)).map(([key]) => key);
    }
    get isFull() { return false; }
}
export class KdBusinessProjectFormController extends FormController {
    static components = { ...FormController.components, ButtonBox: KdBusinessRelatedBox };
}
registry.category("views").add("tp_kd_bp_project_form", {
    ...formView, Controller: KdBusinessProjectFormController,
});
