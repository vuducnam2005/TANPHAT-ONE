import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TpBankBadge, TpBankPicker } from "./bank_picker";

/** Many2one to tp.bank shown as the searchable bank picker (bank account form used by HR). */
export class TpBankPickerField extends Component {
    static template = "tp_hr_bank.BankPickerField";
    static components = { TpBankBadge, TpBankPicker };
    props = useProps(standardFieldProps);

    setup() {
        this.orm = useService("orm");
        this.state = proxy({ banks: [] });
        onWillStart(async () => {
            this.state.banks = await this.orm.call("tp.bank", "tp_bank_catalog", []);
        });
    }

    get value() {
        return this.props.record.data[this.props.name]?.id || false;
    }

    get selected() {
        return this.state.banks.find((bank) => bank.id === this.value) || null;
    }

    get label() {
        return this.selected?.short_name || this.props.record.data[this.props.name]?.display_name || "";
    }

    onSelect(bank) {
        this.props.record.update({ [this.props.name]: { id: bank.id, display_name: bank.short_name } });
    }
}

registry.category("fields").add("tp_bank_picker", {
    component: TpBankPickerField,
    displayName: "Bank picker",
    supportedTypes: ["many2one"],
});

/** The coloured bank mark for the catalogue list/form (reads badge, color, text_color). */
export class TpBankBadgeField extends Component {
    static template = "tp_hr_bank.BankBadgeField";
    static components = { TpBankBadge };
    props = useProps(standardFieldProps);

    get bank() {
        const data = this.props.record.data;
        return { badge: data.badge, color: data.color, text_color: data.text_color };
    }
}

registry.category("fields").add("tp_bank_badge", {
    component: TpBankBadgeField,
    displayName: "Bank badge",
    supportedTypes: ["char"],
});
