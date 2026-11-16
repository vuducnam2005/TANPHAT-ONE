import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

export class ReportingFormController extends FormController {
    async beforeExecuteActionButton(params) {
        const proceed = await super.beforeExecuteActionButton(params);
        // Native button handling saves first. Its reloaded token must accompany the transition.
        if (proceed !== false) {
            const record = this.model.root;
            const version = Number.isInteger(record.data.target_version) ? record.data.target_version : Number.isInteger(record.data.document_version)
                ? record.data.document_version : record.data.version;
            if (record.resId && Number.isInteger(version)) {
                await this.model._updateConfig(record.config, {
                    context: { ...record.context, tp_reporting_expected_version: version },
                }, { reload: false });
            }
        }
        return proceed;
    }

    async onWillSaveRecord(record, changes) {
        const proceed = await super.onWillSaveRecord(record, changes);
        if (proceed === false) {
            return false;
        }
        if (record.resId) {
            const version = Number.isInteger(record.data.target_version) ? record.data.target_version : Number.isInteger(record.data.document_version)
                ? record.data.document_version : record.data.version;
            if (Number.isInteger(version)) {
                await this.model._updateConfig(record.config, {
                    context: { ...record.context, tp_reporting_expected_version: version },
                }, { reload: false });
            }
        }
    }
}

registry.category("views").add("tp_reporting_form", {
    ...formView,
    Controller: ReportingFormController,
});
