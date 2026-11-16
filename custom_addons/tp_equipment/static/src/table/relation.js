/** @odoo-module **/
import { Component, onWillStart, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { Domain } from "@web/core/domain";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { getFieldDomain } from "@web/model/relational_model/utils";
import { View } from "@web/views/view";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { buildRelationSearchArch } from "@tp_web_home/search/relation_search_helper";
import { PAGE_SIZE_OPTIONS, tablePageKey, readPageSize, writePageSize } from "../prefs";

// Native fields_get need not expose inverse_name. Explicit server relation contracts.
const INVERSES = {
    "maintenance.equipment:tp_child_ids": "tp_parent_id",
    "maintenance.equipment:tp_move_line_ids": "equipment_id",
    "maintenance.equipment:maintenance_ids": "equipment_id",
    "maintenance.equipment:tp_meter_ids": "equipment_id",
    "maintenance.equipment:tp_software_ids": "equipment_id",
    "maintenance.request:tp_move_ids": "maintenance_request_id",
    "tp.equipment.move:line_ids": "move_id",
    "tp.equipment.receipt:line_ids": "receipt_id",
    "tp.equipment.proposal:line_ids": "proposal_id",
    "tp.equipment.proposal:review_ids": "proposal_id",
    "tp.equipment.inventory:line_ids": "inventory_id",
    "tp.equipment.inventory:move_ids": "inventory_id",
    "tp.equipment.import.batch:line_ids": "batch_id",
    "tp.equipment.import.batch:column_ids": "batch_id",
    "tp.equipment.location:equipment_ids": "tp_location_id",
    "maintenance.equipment.category:equipment_ids": "category_id",
    "hr.employee:tp_equipment_ids": "tp_employee_id",
};
class EquipmentRelationDialog extends Component {
    static template = "tp_equipment.RelationDialog";
    static components = { Dialog, View };
    props = useProps();
}
export class EquipmentRelationField extends X2ManyField {
    static template = "tp_equipment.RelationField";
    pageSizes = PAGE_SIZE_OPTIONS;
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        onWillStart(async () => {
            if (this.enabled && !this.blocked) await this.list.load({ limit: readPageSize(this.pageKey), offset: 0 });
        });
    }
    get enabled() { return this.props.viewMode === "list"; }
    get pageKey() {
        return tablePageKey(this.props.record.resModel, this.env.config.actionId,
            `${this.env.config.viewId || ""}:${this.props.name}`);
    }
    get blocked() {
        return !this.props.record.resId || this.props.record.dirty || Boolean(this.list.editedRecord);
    }
    get relationDomain() {
        const inverse = INVERSES[`${this.props.record.resModel}:${this.props.name}`];
        if (inverse) return [[inverse, "=", this.props.record.resId]];
        const ids = this.list.currentIds.filter((id) => typeof id === "number");
        // A bounded many2many selector is complete only when all persisted IDs are known.
        if (this.isMany2Many && ids.length === this.list.count) return [["id", "in", ids]];
        return null;
    }
    async changeSize(ev) {
        const limit = Number(ev.target.value);
        if (this.blocked || !PAGE_SIZE_OPTIONS.includes(limit) || await this.props.record.isDirty()) return;
        await this.pagerProps.onUpdate({ limit, offset: 0 });
        writePageSize(this.pageKey, limit);
    }
    async filterAll() {
        if (this.blocked || !this.relationDomain || await this.props.record.isDirty()) return;
        const arch = this.archInfo.xmlDoc.cloneNode(true);
        arch.setAttribute("js_class", "tp_equipment_table");
        for (const attr of ["create", "edit", "delete", "import", "export_xlsx"]) arch.setAttribute(attr, "false");
        arch.removeAttribute("editable");
        arch.removeAttribute("open_form_view");
        arch.querySelectorAll("button,control,header").forEach((node) => node.remove());
        for (const node of arch.querySelectorAll("*")) {
            for (const attr of [...node.attributes]) {
                if (attr.value.includes("parent.")) node.removeAttribute(attr.name);
            }
            if (node.tagName === "field") node.setAttribute("readonly", "True");
        }
        const context = Object.fromEntries(Object.entries(this.props.context || {}).filter(([key]) =>
            !key.endsWith("_view_ref") && !key.startsWith("default_") && !key.startsWith("search_default_") &&
            !key.endsWith("_internal") && !["active_id", "active_ids", "active_model", "tp_filter_profile"].includes(key)));
        const domain = Domain.and([this.relationDomain,
            getFieldDomain(this.props.record, this.props.name, this.props.domain)]).toList();
        this.dialog.add(EquipmentRelationDialog, {
            title: this.props.string || this.field.string,
            viewProps: {
                resModel: this.list.resModel, type: "list", jsClass: "tp_equipment_table",
                arch: new XMLSerializer().serializeToString(arch), fields: this.props.relatedFields,
                relatedModels: { [this.list.resModel]: { fields: this.props.relatedFields } },
                domain, context, searchViewArch: buildRelationSearchArch(arch, this.props.relatedFields),
                searchViewFields: this.props.relatedFields, searchMenuTypes: ["filter", "groupBy"],
                display: { controlPanel: {} }, readonly: true, allowOpenAction: false,
            },
        });
    }
}
registry.category("fields").add("tp_equipment_relation", { ...x2ManyField, component: EquipmentRelationField });
