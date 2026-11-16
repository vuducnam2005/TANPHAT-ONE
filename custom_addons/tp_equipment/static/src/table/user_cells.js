import { Component, t, useProps } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/** EQUIP-UI-002 read-only cells of the "Thiết bị & người sử dụng" table (HR data comes from tp_employee_id). */
const textOf = (value) => {
    if (!value) return "";
    if (typeof value === "object") return value.display_name || "";
    return String(value);
};

export class TpEqHolderCell extends Component {
    static template = "tp_equipment.HolderCell";
    props = useProps({ ...standardFieldProps, emptyText: t.string().optional("Chưa xác định người sử dụng") });
    get employee() {
        const value = this.props.record.data[this.props.name];
        return value && value.id ? value : null;
    }
    get avatarUrl() {
        return this.employee ? `/web/image/hr.employee/${this.employee.id}/avatar_128` : "";
    }
    get code() {
        return this.props.record.data.tp_employee_code || "";
    }
    get archived() {
        return Boolean(this.props.record.data.tp_employee_archived);
    }
    get tooltip() {
        const parts = [textOf(this.employee), this.code, this.archived ? "Người đã nghỉ/cần thu hồi" : ""];
        return parts.filter(Boolean).join(" · ");
    }
}
registry.category("fields").add("tp_eq_holder", {
    component: TpEqHolderCell,
    displayName: "Người sử dụng (HR)",
    supportedTypes: ["many2one"],
    // EQUIP-SIMPLE-003: options="{'empty': ''}" leaves a stock row blank instead of "Chưa xác định…".
    extractProps: ({ options }) => ({ emptyText: options.empty ?? "Chưa xác định người sử dụng" }),
    fieldDependencies: [
        { name: "tp_employee_code", type: "char", readonly: true },
        { name: "tp_employee_archived", type: "boolean", readonly: true },
    ],
});

export class TpEqClampCell extends Component {
    static template = "tp_equipment.ClampCell";
    props = useProps({ ...standardFieldProps, placeholder: t.string().optional(), blank: t.boolean().optional(false) });
    get text() {
        return textOf(this.props.record.data[this.props.name]).trim();
    }
}
registry.category("fields").add("tp_eq_clamp", {
    component: TpEqClampCell,
    displayName: "Văn bản rút gọn 2 dòng",
    supportedTypes: ["char", "text", "many2one", "selection"],
    // options="{'blank': True}": an empty value shows nothing (no "Chưa có ghi chú", no dash).
    extractProps: ({ options }) => ({ placeholder: options.placeholder || "", blank: Boolean(options.blank) }),
});

export class TpEqDeviceCell extends Component {
    static template = "tp_equipment.DeviceCell";
    props = useProps({ ...standardFieldProps, showType: t.boolean().optional(false) });
    get name() {
        return textOf(this.props.record.data[this.props.name]);
    }
    get type() {
        return this.props.showType ? textOf(this.props.record.data.category_id).trim() : "";
    }
    get meta() {
        const data = this.props.record.data;
        return [data.tp_code, data.model].map((v) => textOf(v).trim()).filter(Boolean).join(" · ");
    }
}
registry.category("fields").add("tp_eq_device", {
    component: TpEqDeviceCell,
    displayName: "Thiết bị (tên, mã, model)",
    supportedTypes: ["char"],
    extractProps: ({ options }) => ({ showType: Boolean(options.show_type) }),
    fieldDependencies: [
        { name: "tp_code", type: "char", readonly: true },
        { name: "model", type: "char", readonly: true },
        { name: "category_id", type: "many2one", relation: "maintenance.equipment.category", readonly: true },
    ],
});

/**
 * EQUIP-SIMPLE-003 status badge: always text + colour (blue = in use, teal = stock, orange = check,
 * red = broken, slate = shared/located, grey = draft/retired). Read-only; the label comes from the
 * server selection so no state is invented client-side.
 */
const STATUS_TONES = {
    tp_usage_status: {
        in_use: "use", stock: "stock", shared: "shared", location: "shared",
        vendor: "check", cleanup: "check", unknown: "check", draft: "muted", retired: "muted",
    },
    tp_technical_state: { good: "ok", limited: "check", unverified: "check", broken: "broken" },
};

export class TpEqStatusCell extends Component {
    static template = "tp_equipment.StatusCell";
    props = useProps(standardFieldProps);
    get value() {
        return this.props.record.data[this.props.name] || "";
    }
    get label() {
        const selection = this.props.record.fields[this.props.name]?.selection || [];
        const entry = selection.find(([key]) => key === this.value);
        return entry ? entry[1] : "";
    }
    get tone() {
        return STATUS_TONES[this.props.name]?.[this.value] || "muted";
    }
}
registry.category("fields").add("tp_eq_status", {
    component: TpEqStatusCell,
    displayName: "Trạng thái thiết bị (badge có chữ)",
    supportedTypes: ["selection"],
});

/**
 * EQUIP-SIMPLE-003 row "⋮" menu for rare actions. Every entry calls a backend method; the list is
 * reloaded afterwards (counts follow through the wrapped model.load). No field is written here.
 */
export class TpEqRowMenu extends Component {
    static template = "tp_equipment.RowMenu";
    static components = { Dropdown, DropdownItem };
    props = useProps(standardWidgetProps);
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
    }
    get data() {
        return this.props.record.data;
    }
    get canVerify() {
        return this.data.tp_verification !== "verified" && this.data.tp_lifecycle === "active";
    }
    reload() {
        return this.props.record.model.load();
    }
    async run(method) {
        const result = await this.orm.call("maintenance.equipment", method, [[this.props.record.resId]]);
        if (result && typeof result === "object" && result.type) {
            await this.actionService.doAction(result, { onClose: () => this.reload() });
        }
        return result;
    }
    async verify() {
        await this.orm.call("maintenance.equipment", "action_tp_mark_verified", [[this.props.record.resId]]);
        this.notification.add("Đã ghi nhận đã kiểm tra thực tế.", { type: "success" });
        await this.reload();
    }
}
registry.category("view_widgets").add("tp_eq_row_menu", {
    component: TpEqRowMenu,
    fieldDependencies: [
        { name: "tp_verification", type: "selection" },
        { name: "tp_lifecycle", type: "selection" },
    ],
});
