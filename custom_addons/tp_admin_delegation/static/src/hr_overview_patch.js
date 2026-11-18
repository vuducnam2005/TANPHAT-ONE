/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { HrOverview } from "@tp_hr_workspace/overview/overview";

patch(HrOverview.prototype, {
    get checklist() {
        const domain = this.state.data?.missing_contact_domain;
        return super.checklist.map((item) =>
            item.key === "missing_contact" && domain ? { ...item, domain } : item
        );
    },
});
