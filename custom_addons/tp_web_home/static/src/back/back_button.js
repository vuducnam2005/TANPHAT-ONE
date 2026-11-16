import { Component, proxy, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { BACK_EXCLUDED_MODELS, backTooltip, leaveRecordAndGoBack } from "./back_navigation";

/** The shared "← Quay lại" control (one per detail screen, rendered by the ControlPanel). */
export class TpBackButton extends Component {
    static template = "tp_web_home.BackButton";
    props = useProps();

    setup() {
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.state = proxy({ busy: false });
    }
    get tooltip() {
        return backTooltip(this.env);
    }
    async onClick() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            await leaveRecordAndGoBack(this.env, {
                actionService: this.actionService,
                dialogService: this.dialogService,
                record: this.env.model?.root,
            });
        } finally {
            if (this.state) {
                this.state.busy = false;
            }
        }
    }
}

ControlPanel.components = { ...ControlPanel.components, TpBackButton };

patch(ControlPanel.prototype, {
    /** Record detail screens of the main action stack only (no dialog, list, dashboard or settings). */
    get tpShowBack() {
        const env = this.env;
        const config = env.config || {};
        if (env.inDialog || config.noBreadcrumbs || config.viewType !== "form") {
            return false;
        }
        const root = env.model?.root;
        return Boolean(root && root.resModel && !BACK_EXCLUDED_MODELS.has(root.resModel));
    },
});
