import { Component, proxy, signal, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

/**
 * QR / barcode lookup (EQUIP-001). Works with a keyboard-wedge scanner: the scanner "types" the
 * label content and sends Enter. Only an opaque token, a code or a serial is sent; the server
 * checks admin rights again and answers the same way for unknown and foreign tokens.
 */
export class TpEquipmentScan extends Component {
    static template = "tp_equipment.Scan";
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.input = signal.ref();
        useAutofocus({ ref: this.input });
        this.allowed = Boolean(user.isSystem);
        this.state = proxy({ value: "", busy: false, error: "", recent: [] });
    }

    async submit(ev) {
        ev?.preventDefault();
        const value = this.state.value.trim();
        if (!value || this.state.busy || !this.allowed) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            const result = await this.orm.call("maintenance.equipment", "tp_scan_lookup", [value]);
            if (result?.id) {
                this.state.value = "";
                this.state.recent = [
                    { id: result.id, name: result.name },
                    ...this.state.recent.filter((r) => r.id !== result.id),
                ].slice(0, 5);
                await this.open(result.id);
            } else {
                this.state.error = result?.error || "Không tìm thấy thiết bị.";
                this.input.el?.select();
            }
        } finally {
            this.state.busy = false;
        }
    }

    open(resId) {
        return this.action.doAction("tp_equipment.action_equipment_all_records", {
            props: { resId },
            viewType: "form",
        });
    }
}

registry.category("actions").add("tp_equipment.scan", TpEquipmentScan);
