import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class ReportingReviewerField extends Component {
    static template = "tp_reporting.ReviewerField";
    props = useProps(standardFieldProps);
    state = proxy({ busy: false, choices: [], error: "" });
    setup() {
        this.orm = useService("orm");
        onWillStart(() => this.load());
    }
    get value() { return this.props.record.data[this.props.name]; }
    async load() {
        if (!this.props.record.resId || this.props.readonly) return;
        this.state.busy = true;
        this.state.error = "";
        try {
            this.state.choices = await this.orm.call("tp.report.document", "get_reviewer_options", [[this.props.record.resId]]);
        } catch (error) {
            this.state.choices = [];
            if (["odoo.http.session.SessionExpiredException", "werkzeug.exceptions.Forbidden"].includes(error.exceptionName || error.data?.name)) throw error;
            this.state.error = "Không tải được người nhận. Vui lòng thử lại.";
        } finally { this.state.busy = false; }
    }
    async change(ev) {
        const id = Number(ev.target.value);
        const choice = this.state.choices.find(item => item.id === id);
        await this.props.record.update({ [this.props.name]: choice ? { id: choice.id, display_name: choice.display_name } : false });
    }
}
registry.category("fields").add("tp_reporting_reviewer", {
    component: ReportingReviewerField,
    supportedTypes: ["many2one"],
});
