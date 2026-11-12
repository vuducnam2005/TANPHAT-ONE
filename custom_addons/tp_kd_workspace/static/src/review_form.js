/** @odoo-module **/
import { onMounted, onWillStart, onWillUnmount } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { kdTableSetup } from "./table/table_tools";
import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

export class KdReviewFormController extends FormController {
    setup() {
        super.setup();
        this.archInfo.activeActions.duplicate = false;
        this.archInfo.activeActions.delete = false;
        onWillStart(async () => {
            const permission = await this.orm.call(this.props.resModel, "get_kd_ui_permissions", []);
            this.canCreate = this.canCreate && permission.create;
        });
    }

    get modelParams() {
        // Urgent beacon saves skip the save hook. Keep native leave confirmation
        // instead of sending a write without the version the actor actually read.
        return { ...super.modelParams, useSendBeaconToSaveUrgently: false };
    }

    async onWillSaveRecord(record, changes) {
        const result = await super.onWillSaveRecord(record, changes);
        if (result !== false && record.resId && record.fields.version &&
            (this.props.resModel !== "tp.bid.package" || record.data.can_head_intervene)) {
            changes.version = record.data.version;
        }
        if (result !== false && record.resId && record.fields.kd_head_version && record.data.kd_is_head) {
            changes.kd_head_version = record.data.kd_head_version;
        }
        return result;
    }
}

registry.category("views").add("tp_kd_review_form", {
    ...formView,
    Controller: KdReviewFormController,
});

// KD-UI-003: same table toolbar (density, reset columns) as the other KH-KD lists.
class KdListController extends kdTableSetup(ListController) {
    setup() {
        super.setup();
        this.activeActions = { ...this.activeActions, delete: false, duplicate: false };
        onWillStart(async () => {
            const permission = await this.orm.call(this.props.resModel, "get_kd_ui_permissions", []);
            this.activeActions.create = this.activeActions.create && permission.create;
        });
    }
}
registry.category("views").add("tp_kd_list", { ...listView, Controller: KdListController });
class KdOpportunityFormController extends KdReviewFormController {
    setup() {
        super.setup();
        this.kdAlive = true;
        onMounted(() => { this.kdRightsTimer = browser.setInterval(() => this.refreshKdRights(), 5000); });
        onWillUnmount(() => { this.kdAlive = false; browser.clearInterval(this.kdRightsTimer); });
    }
    async refreshKdRights() {
        const record = this.model.root;
        if (!this.kdAlive || this.kdChecking || !record?.resId || browser.document.hidden) return;
        this.kdChecking = true;
        try {
            // Never overwrite unsaved input. The save/action itself rechecks backend rights.
            if (await record.isDirty()) return;
            const names = ["kd_can_prepare", "kd_can_submit", "kd_can_edit", "kd_can_edit_money", "kd_money_display"];
            const [flags] = await this.orm.read("crm.lead", [record.resId], names);
            if (this.kdAlive && this.model.root === record && names.some(name => flags[name] !== record.data[name])) {
                await this.model.load();
            }
        } catch (error) {
            if (this.kdAlive && error.data?.name === "odoo.exceptions.AccessError") {
                await this.actionService.doAction("tp_kd_workspace.action_opportunities");
            }
        } finally { this.kdChecking = false; }
    }
}
registry.category("views").add("tp_kd_opportunity_form", { ...formView, Controller: KdOpportunityFormController });
registry.category("views").add("tp_kd_opportunity_list", { ...listView, Controller: KdListController });
