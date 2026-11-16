/** @odoo-module **/
import { Component, onWillStart, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { View } from "@web/views/view";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { PAGE_SIZE_OPTIONS, tablePageKey, readPageSize, writePageSize } from "../prefs";
import { buildRelationSearchArch } from "@tp_web_home/search/relation_search_helper";

class KdRelationDialog extends Component {
    static template = "tp_kd_workspace.RelationDialog";
    static components = { Dialog, View };
    props = useProps();
}

export class KdRelationField extends X2ManyField {
    static template = "tp_kd_workspace.RelationField";
    pageSizes = PAGE_SIZE_OPTIONS;
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        onWillStart(async () => {
            if (this.enabled && !this.blocked) {
                await this.list.load({ limit: readPageSize(this.pageKey), offset: 0 });
            }
        });
    }
    get isHrContext() {
        const appXmlid = this.env.services.menu?.getCurrentApp()?.xmlid;
        return (
            appXmlid === "tp_hr_workspace.menu_hr" ||
            Boolean(this.props.context?.tp_hr_relation) ||
            Boolean(this.props.record?.resModel?.startsWith("hr.")) ||
            Boolean(this.props.record?.resModel?.startsWith("tp.hr."))
        );
    }
    get enabled() {
        return this.props.viewMode === "list";
    }
    get pageKey() {
        return tablePageKey(this.props.record.resModel, this.env.config.actionId,
            `${this.env.config.viewId || ''}:${this.props.name}`);
    }
    get blocked() {
        return !this.props.record.resId || this.props.record.dirty || Boolean(this.list.editedRecord);
    }
    async changeSize(ev) {
        const limit = Number(ev.target.value);
        if (this.blocked || !PAGE_SIZE_OPTIONS.includes(limit) || await this.props.record.isDirty()) return;
        await this.pagerProps.onUpdate({ limit, offset: 0 });
        writePageSize(this.pageKey, limit);
    }
    async filterAll() {
        if (this.blocked || await this.props.record.isDirty()) return;
        const jsClass = this.isHrContext ? "tp_hr_table" : "tp_kd_table";
        const arch = this.archInfo.xmlDoc.cloneNode(true);
        arch.setAttribute("js_class", jsClass);
        arch.setAttribute("create", "false");
        arch.setAttribute("edit", "false");
        arch.setAttribute("delete", "false");
        arch.removeAttribute("editable");
        arch.querySelectorAll("button,control").forEach((el) => el.remove());
        const searchArch = buildRelationSearchArch(arch, this.props.relatedFields);
        const context = Object.fromEntries(Object.entries(this.props.context).filter(([key]) =>
            !key.endsWith("_view_ref") && !key.startsWith("default_") && !key.startsWith("search_default_") &&
            !["active_id", "active_ids", "active_model"].includes(key)));
        this.dialog.add(KdRelationDialog, {
            title: this.props.string || this.field.string,
            viewProps: {
                resModel: this.list.resModel, type: "list", jsClass,
                arch: new XMLSerializer().serializeToString(arch), fields: this.props.relatedFields,
                relatedModels: { [this.list.resModel]: { fields: this.props.relatedFields } },
                domain: [["id", "in", this.list.currentIds.filter((id) => typeof id === "number")]],
                context: {
                    ...context,
                    ...(this.isHrContext
                        ? { tp_hr_relation: `${this.props.record.resModel}:${this.props.name}` }
                        : { tp_kd_relation: `${this.props.record.resModel}:${this.props.name}` }),
                },
                searchViewArch: searchArch, searchViewFields: this.props.relatedFields,
                searchMenuTypes: ["filter", "groupBy"],
                display: { controlPanel: {} },
                readonly: true, allowOpenAction: false,
            },
        });
    }
}
registry.category("fields").add("tp_kd_relation", { ...x2ManyField, component: KdRelationField });
