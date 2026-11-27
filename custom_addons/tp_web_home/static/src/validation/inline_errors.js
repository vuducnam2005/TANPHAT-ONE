import { Component, onMounted, onPatched, signal, t, useProps } from "@odoo/owl";

/**
 * Error summary for custom OWL forms and screens. Callers pass errors from their own real
 * validators ({id, label, location, message}) and the classified server error;
 * this component never decides what is required. `intro` replaces “Chưa lưu được…” and
 * `note` the closing line on screens where nothing typed is being saved.
 */
export class InlineErrors extends Component {
    static template = "tp_web_home.InlineErrors";
    props = useProps({
        errors: t.array().optional(),
        server: t.any().optional(),
        error: t.any().optional(),
        attempt: t.number().optional(),
        intro: t.string().optional(),
        note: t.string().optional(),
    });
    section = signal.ref();

    get normalizedErrors() {
        return Array.isArray(this.props.errors) ? this.props.errors : [];
    }

    get normalizedServer() {
        return this.props.server || this.props.error || null;
    }

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
        const scope =
            ev.currentTarget.closest(
                '.modal, [role="dialog"], .o_form_renderer, .o_tp_hr_my_profile, .tp-account-security'
            ) || document;
        const field = [...scope.querySelectorAll("[id]")].find((el) => el.id === error.id);
        if (!field) return;
        field.scrollIntoView({ block: "center", inline: "nearest" });
        field.focus({ preventScroll: true });
    }
}
