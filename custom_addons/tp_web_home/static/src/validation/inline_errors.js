import { Component, onMounted, onPatched, signal, t, useProps } from "@odoo/owl";

/**
 * Error summary for custom OWL forms. Callers pass errors from their own real
 * validators ({id, label, location, message}) and the classified server error;
 * this component never decides what is required.
 */
export class InlineErrors extends Component {
    static template = "tp_web_home.InlineErrors";
    props = useProps({ errors: t.array(), server: t.any().optional(), attempt: t.number().optional() });
    section = signal.ref();

    setup() {
        let shownAttempt = 0;
        const reveal = () => {
            const attempt = this.props.attempt || 0;
            if (attempt !== shownAttempt && this.section()) {
                this.section().scrollIntoView({ block: "nearest", inline: "nearest" });
            }
            shownAttempt = attempt;
        };
        onMounted(reveal);
        onPatched(reveal);
    }

    focusError(error, ev) {
        const scope = ev.currentTarget.closest('.modal, [role="dialog"], .o_form_renderer, .o_tp_hr_my_profile') || document;
        const field = [...scope.querySelectorAll("[id]")].find((el) => el.id === error.id);
        if (!field) return;
        field.scrollIntoView({ block: "center", inline: "nearest" });
        field.focus({ preventScroll: true });
    }
}
