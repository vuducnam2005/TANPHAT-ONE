import { Component, onWillStart, proxy, t, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class ReportingPersonField extends Component {
    static template = "tp_reporting.PersonField";
    props = useProps({ ...standardFieldProps, purpose: t.string() });
    state = proxy({ busy: false, choices: [], error: "", search: "" });
    setup() { this.orm = useService("orm"); this.seq = 0; onWillStart(() => this.load()); }
    get value() { return this.props.record.data[this.props.name]; }
    get multi() { return this.props.record.fields[this.props.name].type === "many2many"; }
    get selected() { return this.multi ? this.value.records.map(r => ({ id: r.resId, display_name: r.data.display_name })) : this.value ? [this.value] : []; }
    isSelected(id) { return this.selected.some(item => item.id === id); }
    async load() {
        if (this.props.readonly) return;
        const seq = ++this.seq;
        this.state.busy = true; this.state.error = "";
        const record = this.props.record;
        try {
            const choices = await this.orm.call("tp.report.people", "get_options", [this.props.purpose, record.resModel, record.resId || false, record.data.company_id?.id || false, record.data.department_id?.id || false, this.state.search]);
            if (seq === this.seq) this.state.choices = choices;
        } catch (error) {
            if (["odoo.http.session.SessionExpiredException", "werkzeug.exceptions.Forbidden"].includes(error.exceptionName || error.data?.name)) throw error;
            if (seq === this.seq) { this.state.choices = []; this.state.error = "Chọn công ty/phòng đúng phạm vi rồi tải lại danh sách người."; }
        } finally { if (seq === this.seq) this.state.busy = false; }
    }
    async select(ev) {
        const id = Number(ev.target.value);
        const choice = this.state.choices.find(item => item.id === id);
        await this.props.record.update({ [this.props.name]: choice ? { id, display_name: choice.display_name } : false });
    }
    async toggle(choice) { await this.value.addAndRemove(this.isSelected(choice.id) ? { remove: [choice.id] } : { add: [choice.id] }); }
}
registry.category("fields").add("tp_reporting_person", {
    component: ReportingPersonField, supportedTypes: ["many2one", "many2many"],
    extractProps: ({ options }) => ({ purpose: options.purpose || "plan" }),
});
