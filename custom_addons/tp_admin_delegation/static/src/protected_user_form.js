/** @odoo-module **/
import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

export class ProtectedUserFormController extends FormController {
    static template = "tp_admin_delegation.ProtectedUserForm";

    async onRootLoaded() {
        await super.onRootLoaded();
        this.canEdit = Boolean(this.archInfo.activeActions.edit && !this.props.preventEdit
            && !this.model.root.data.tp_account_profile_readonly);
        if (this.model.root.data.tp_account_profile_readonly && this.model.root.isInEdition) {
            await this.model.root.switchMode("readonly");
        }
    }

    get actionMenuItems() {
        const items = super.actionMenuItems;
        return this.model.root.data.tp_account_profile_readonly ? {...items, action: []} : items;
    }
}

registry.category("views").add("tp_admin_protected_user_form", {
    ...formView, Controller: ProtectedUserFormController,
});
