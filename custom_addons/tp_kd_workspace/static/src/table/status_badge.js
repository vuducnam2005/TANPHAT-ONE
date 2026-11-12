/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BadgeField, badgeField } from "@web/views/fields/badge/badge_field";
import { SelectionField, selectionField } from "@web/views/fields/selection/selection_field";
import { today } from "@web/core/l10n/dates";
import { DateTimeField, dateField, dateTimeField } from "@web/views/fields/datetime/datetime_field";

const REVIEW = { draft: "neutral", in_review: "info", returned: "danger", review_complete: "success", cancelled: "neutral" };
const MONEY = { unconfirmed: "warning", confirmed: "info" };
export const STATUS_TONES = {
    "crm.lead": { kd_bid_state: { identified: "info", preparation: "progress", submitted: "warning" } },
    "project.task": { state: { "01_in_progress": "progress", "02_changes_requested": "warning", "03_approved": "success", "04_waiting_normal": "info", "1_done": "success", "1_canceled": "neutral" } },
    "tp.contract": { tp_latest_review_state: REVIEW, lifecycle_state: { not_effective: "neutral", effective: "success", suspended: "warning", execution_completed: "success", liquidated: "neutral", terminated: "neutral" } },
    "tp.contract.revision": {
        review_state: REVIEW, signature_status: { unsigned: "neutral", signed_recorded: "info" },
        signature_authority_status: { pending: "warning", confirmed: "info" },
        effectivity_status: { not_effective: "neutral", effective_recorded: "success" },
    },
    "tp.obligation": { state: REVIEW, checklist_status: { missing: "warning", collecting: "progress", internal_checked: "success" } },
    "tp.contract.line.amount": { amount_state: MONEY },
    "tp.contract.submission": { outcome: { pending: "info", returned: "danger", review_complete: "success" } },
    "tp.approval.reference": {
        decision: { pending: "warning", approved: "info", rejected: "danger", cancelled: "neutral" },
        verification_state: { pending: "warning", verified: "info", disputed: "danger" },
        authority_status: { unconfirmed: "warning", confirmed: "info" },
    },
};
for (const model of ["tp.allocation", "tp.production", "tp.acceptance", "tp.payment.request", "tp.periodic.plan", "tp.credential"]) {
    STATUS_TONES[model] = { state: REVIEW, reconciliation_state: { unreconciled: "warning", needs_evidence: "warning" } };
}
for (const model of ["tp.allocation", "tp.production", "tp.acceptance", "tp.payment.request", "tp.periodic.plan", "tp.credential", "tp.obligation"]) {
    STATUS_TONES[`${model}.event`] = { state_before: REVIEW, state_after: REVIEW };
    STATUS_TONES[`${model}.amount`] = { amount_state: MONEY };
    STATUS_TONES[`${model}.event.amount`] = { amount_state: MONEY };
}
STATUS_TONES["tp.contract.audit"] = { state_before: REVIEW, state_after: REVIEW };
STATUS_TONES["tp.payment.request"].reconciliation_state = { pending: "warning", missing_documents: "warning", internal_checked: "info" };
STATUS_TONES["tp.periodic.plan.amount"].source_status = { no_data: "neutral", unknown: "warning", comparable: "info", no_posted_evidence: "warning" };
STATUS_TONES["tp.contract.native.amount.input"] = { amount_state: MONEY };
export function statusTone(model, field, value) {
    return STATUS_TONES[model]?.[field]?.[value] || "neutral";
}
export class KdStatusBadge extends BadgeField {
    get enabled() { return this.env.services.menu?.getCurrentApp()?.xmlid === "tp_kd_workspace.menu_kd"; }
    get badgeClass() {
        if (this.env.services.menu?.getCurrentApp()?.xmlid !== "tp_kd_workspace.menu_kd") return super.badgeClass;
        if (this.props.record.resModel === "tp.credential" && this.props.name === "expiry_status") {
            const days = this.props.record.data.valid_to?.diff(today(), "days").days;
            return `tp_kd_badge tp_kd_tone_${days < 0 ? 'danger' : days <= 30 ? 'warning' : 'info'}`;
        }
        return `tp_kd_badge tp_kd_tone_${statusTone(this.props.record.resModel, this.props.name, this.props.record.data[this.props.name])}`;
    }
}
registry.category("fields").add("tp_kd_badge", { ...badgeField, component: KdStatusBadge });
class KdTextBadge extends KdStatusBadge { static template = "tp_kd_workspace.TextBadge"; }
registry.category("fields").add("tp_kd_text_badge", { ...badgeField, component: KdTextBadge });

// Preserve the original selection editor, and plain text outside the workspace.
export class KdStatusSelection extends SelectionField {
    static template = "tp_kd_workspace.StatusSelection";
    static components = { ...SelectionField.components, KdStatusBadge };
    get colored() {
        return this.props.readonly && this.env.services.menu?.getCurrentApp()?.xmlid === "tp_kd_workspace.menu_kd";
    }
}
registry.category("fields").add("tp_kd_selection", { ...selectionField, component: KdStatusSelection });

// Use the native picker/formatter/timezone and include the year in workspace dates.
class KdDateTime extends DateTimeField {
    getFormattedValue(index, numeric = this.props.numeric) {
        return super.getFormattedValue(index,
            this.env.services.menu?.getCurrentApp()?.xmlid === "tp_kd_workspace.menu_kd" || numeric);
    }
}
registry.category("fields").add("tp_kd_date", { ...dateField, component: KdDateTime });
registry.category("fields").add("tp_kd_datetime", { ...dateTimeField, component: KdDateTime });
