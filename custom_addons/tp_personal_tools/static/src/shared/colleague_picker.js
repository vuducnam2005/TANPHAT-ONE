import { Component, onWillUnmount, proxy, useListener, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Shared colleague picker across Việc cá nhân, Lịch làm việc, and Trao đổi.
 * Uses `res.users.tp_search_colleagues` (active internal users + public dept/job only).
 */
export class TpColleaguePicker extends Component {
    static template = "tp_personal_tools.ColleaguePicker";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.debounceTimer = null;
        this.reqSeq = 0;
        this.state = proxy({
            query: "",
            open: false,
            loading: false,
            results: [],
        });

        useListener(window, "pointerdown", (ev) => {
            if (!this.state.open) {
                return;
            }
            if (!ev.target?.closest?.(".tp-pt-colleague-picker")) {
                this.state.open = false;
            }
        });

        onWillUnmount(() => {
            if (this.debounceTimer) {
                clearTimeout(this.debounceTimer);
            }
        });
    }

    get selectedItems() {
        return this.props.selected || [];
    }

    get selectedKeyField() {
        return this.props.keyField || "user_id";
    }

    isSelected(item) {
        const key = this.selectedKeyField;
        return this.selectedItems.some((s) => s[key] === item[key]);
    }

    get availableResults() {
        return this.state.results.filter((item) => !this.isSelected(item));
    }

    async fetchColleagues(q) {
        const seq = ++this.reqSeq;
        this.state.loading = true;
        try {
            const rows = await this.orm.call("res.users", "tp_search_colleagues", [
                q || "",
                25,
                Boolean(this.props.includeSelf),
            ]);
            if (seq === this.reqSeq) {
                this.state.results = Array.isArray(rows) ? rows : [];
            }
        } catch {
            if (seq === this.reqSeq) {
                this.state.results = [];
            }
        } finally {
            if (seq === this.reqSeq) {
                this.state.loading = false;
            }
        }
    }

    onFocus() {
        if (this.props.disabled) {
            return;
        }
        this.state.open = true;
        if (!this.state.results.length) {
            this.fetchColleagues(this.state.query);
        }
    }

    onInput(ev) {
        this.state.query = ev.target.value || "";
        this.state.open = true;
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.debounceTimer = setTimeout(() => {
            this.fetchColleagues(this.state.query);
        }, 200);
    }

    onKeydown(ev) {
        if (ev.key === "Escape" && this.state.open) {
            ev.stopPropagation();
            this.state.open = false;
        }
    }

    selectItem(item) {
        if (this.props.disabled) {
            return;
        }
        this.state.query = "";
        if (this.props.multiple === false) {
            this.state.open = false;
            this.props.onChange?.([item]);
            return;
        }
        const next = [...this.selectedItems, item];
        this.props.onChange?.(next);
    }

    removeItem(item) {
        if (this.props.disabled) {
            return;
        }
        const key = this.selectedKeyField;
        if (this.props.lockedId && item[key] === this.props.lockedId) {
            return;
        }
        const next = this.selectedItems.filter((s) => s[key] !== item[key]);
        this.props.onChange?.(next);
    }
}
