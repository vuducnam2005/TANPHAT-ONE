import { Component, onPatched, proxy, signal, t, useProps } from "@odoo/owl";

/** Lower case, no Vietnamese diacritics: "Ngân hàng Đông Á" → "ngan hang dong a". */
export function foldBankText(text) {
    return String(text || "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase();
}

/** Holder name as banks print it: no diacritics, upper case, single spaces. */
export function bankHolderName(text) {
    return foldBankText(text).replace(/\s+/g, " ").trim().toUpperCase();
}

/** "0123456789012" → "0123 4567 8901 2" (display only). */
export function formatAccountNumber(number) {
    return String(number || "").replace(/(.{4})(?=.)/g, "$1 ");
}

/** Coloured bank mark: the bank's short code on its brand colour (generated, not a logo). */
export class TpBankBadge extends Component {
    static template = "tp_hr_bank.BankBadge";
    props = useProps({ bank: t.any().optional(), size: t.string().optional() });

    get style() {
        const bank = this.props.bank;
        if (!bank?.color) {
            return "";
        }
        return `background-color: ${bank.color}; color: ${bank.text_color || "#FFFFFF"};`;
    }
}

let nextPickerId = 0;

/**
 * Searchable bank list (combobox + listbox). Matching ignores accents and case and looks at the
 * short name, full name, code, badge and NAPAS BIN; prefix matches come first.
 */
export class TpBankPicker extends Component {
    static template = "tp_hr_bank.BankPicker";
    static components = { TpBankBadge };
    props = useProps({
        banks: t.array(),
        value: t.any().optional(),
        onSelect: t.function(),
        id: t.string().optional(),
        invalid: t.boolean().optional(),
        disabled: t.boolean().optional(),
        placeholder: t.string().optional(),
    });

    setup() {
        nextPickerId += 1;
        this.uid = `o_tp_bank_picker_${nextPickerId}`;
        this.list = signal.ref();
        this.state = proxy({ open: false, query: "", active: 0 });
        onPatched(() => {
            const list = this.list();
            const active = list?.querySelector(".is-active");
            if (active) {
                active.scrollIntoView({ block: "nearest" });
            }
        });
    }

    get selected() {
        const id = Number(this.props.value || 0);
        return (this.props.banks || []).find((bank) => bank.id === id) || null;
    }

    get inputValue() {
        if (this.state.open) {
            return this.state.query;
        }
        return this.selected?.short_name || "";
    }

    /** Shown under the closed picker: the full legal name and NAPAS BIN of the chosen bank. */
    get selectedHint() {
        const bank = this.selected;
        if (!bank) {
            return "";
        }
        return bank.bin ? `${bank.name} · BIN ${bank.bin}` : bank.name;
    }

    get placeholderText() {
        if (this.state.open) {
            return "Gõ tên, mã hoặc BIN ngân hàng…";
        }
        return this.props.placeholder || "Chọn ngân hàng";
    }

    get countLabel() {
        const found = this.filtered.length;
        if (!this.state.query.trim()) {
            return `${(this.props.banks || []).length} ngân hàng`;
        }
        return found ? `Tìm thấy ${found} ngân hàng` : "Không có ngân hàng phù hợp";
    }

    get filtered() {
        const banks = this.props.banks || [];
        const query = foldBankText(this.state.query).trim();
        if (!query) {
            return banks;
        }
        const compact = query.replace(/\s+/g, "");
        const starts = [];
        const contains = [];
        for (const bank of banks) {
            const keys = [bank.short_name, bank.code, bank.badge].map(foldBankText);
            const all = [...keys, foldBankText(bank.name), bank.bin || ""];
            if (keys.some((key) => key.startsWith(query) || key.replace(/\s+/g, "").startsWith(compact))) {
                starts.push(bank);
            } else if (all.some((key) => key.includes(query) || key.replace(/\s+/g, "").includes(compact))) {
                contains.push(bank);
            }
        }
        return [...starts, ...contains];
    }

    optionId(bank) {
        return `${this.uid}_opt_${bank.id}`;
    }

    get activeOptionId() {
        const bank = this.state.open ? this.filtered[this.state.active] : null;
        return bank ? this.optionId(bank) : "";
    }

    open() {
        if (this.props.disabled || this.state.open) {
            return;
        }
        const index = this.selected ? this.filtered.findIndex((bank) => bank.id === this.selected.id) : 0;
        Object.assign(this.state, { open: true, query: "", active: Math.max(index, 0) });
    }

    close() {
        Object.assign(this.state, { open: false, query: "" });
    }

    toggle() {
        if (this.state.open) {
            this.close();
        } else {
            this.open();
        }
    }

    choose(bank) {
        this.close();
        this.props.onSelect(bank);
    }

    onInput(ev) {
        Object.assign(this.state, { open: true, query: ev.target.value, active: 0 });
    }

    onKeydown(ev) {
        const options = this.filtered;
        switch (ev.key) {
            case "ArrowDown":
            case "ArrowUp": {
                ev.preventDefault();
                if (!this.state.open) {
                    this.open();
                    return;
                }
                const step = ev.key === "ArrowDown" ? 1 : -1;
                const last = Math.max(options.length - 1, 0);
                this.state.active = Math.min(Math.max(this.state.active + step, 0), last);
                return;
            }
            case "Home":
            case "End":
                if (this.state.open && options.length) {
                    ev.preventDefault();
                    this.state.active = ev.key === "Home" ? 0 : options.length - 1;
                }
                return;
            case "Enter":
                if (this.state.open) {
                    ev.preventDefault();
                    const bank = options[this.state.active];
                    if (bank) {
                        this.choose(bank);
                    }
                }
                return;
            case "Escape":
                if (this.state.open) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    this.close();
                }
                return;
            case "Tab":
                this.close();
                return;
        }
    }
}
