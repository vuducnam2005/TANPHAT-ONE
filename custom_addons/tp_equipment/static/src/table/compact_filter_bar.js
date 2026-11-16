import { onWillUnmount, proxy } from "@odoo/owl";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";

const INLINE_KEYS = {
    "maintenance.equipment": ["category_id", "tp_custody"],
    "maintenance.equipment::equipment": ["category_id", "tp_custody"],
    "maintenance.equipment::equipment_stock": ["category_id", "tp_technical_state"],
    "maintenance.equipment::equipment_users": ["tp_current_department_id", "category_id"],
    "maintenance.equipment::equipment_main": ["tp_current_department_id", "category_id"],
    "tp.equipment.proposal::proposal_simple": ["requester_department_id", "review_state"],
    "maintenance.equipment::equipment_shared": ["tp_custody", "category_id"],
    "tp.equipment.proposal": ["review_state", "approval_state"],
    "tp.equipment.move": ["move_type", "state"],
    "tp.equipment.move.line": ["move_type", "to_employee_id"],
    "maintenance.request": ["tp_state", "tp_request_kind"],
    "tp.equipment.receipt": ["source", "state"],
    "tp.equipment.inventory": ["state", "scope"],
    "tp.equipment.import.batch": ["kind", "state"],
};

export class TpEquipmentFilterBar extends TpTableFilterBar {
    static template = "tp_equipment.CompactFilterBar";

    setup() {
        super.setup();
        this.ui = proxy({ drawerOpen: false });
        const onDocPointer = (ev) => {
            if (!this.ui.drawerOpen) return;
            const el = ev.target;
            if (el?.closest?.(".tp_eq_drawer_anchor") || el?.closest?.(".o-autocomplete--dropdown-menu")) {
                return;
            }
            this.ui.drawerOpen = false;
        };
        document.addEventListener("pointerdown", onDocPointer);
        onWillUnmount(() => document.removeEventListener("pointerdown", onDocPointer));
    }

    get _profileLookupKey() {
        const resModel = this.props.controller?.props?.resModel || this.env.searchModel.resModel;
        const ctxKey = this.props.controller?.props?.context?.tp_filter_profile;
        return ctxKey ? `${resModel}::${ctxKey}` : resModel;
    }

    get inlineCriteria() {
        const all = this.criteria || [];
        if (!all.length) return [];
        const wanted = INLINE_KEYS[this._profileLookupKey] || INLINE_KEYS[this.env.searchModel.resModel];
        if (wanted) {
            const matched = wanted.map((k) => all.find((c) => c.key === k)).filter(Boolean);
            if (matched.length) return matched.slice(0, 2);
        }
        return all.filter((c) => c.type !== "char").slice(0, 2);
    }

    // EQUIP-SIMPLE-003: the Tất cả / Đang sử dụng / Trong kho segment is shown by the header control,
    // not as a filter chip, and is not counted as a "Bộ lọc".
    get activeFacets() {
        const segGroups = new Set(
            this.env.searchModel
                .getSearchItems((item) => item.type === "filter" && item.name?.startsWith("seg_"))
                .map((item) => item.groupId)
        );
        return super.activeFacets.filter((facet) => !segGroups.has(facet.groupId));
    }

    get drawerCriteria() {
        const inlineSet = new Set(this.inlineCriteria.map((c) => c.key));
        return (this.criteria || []).filter((c) => !inlineSet.has(c.key));
    }

    get printerFilterItem() {
        if (this._profileLookupKey !== "maintenance.equipment::equipment_main") {
            return null;
        }
        return this.env.searchModel.getSearchItems(
            (item) => item.type === "filter" && item.name === "q_printer_copier"
        )[0] || null;
    }

    get printerFilterActive() {
        return Boolean(this.printerFilterItem?.isActive);
    }

    togglePrinterFilter() {
        const item = this.printerFilterItem;
        if (!this.blocked && item) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }

    get drawerBadgeCount() {
        const totalActive = this.activeFilterCount || 0;
        let inlineActive = this.printerFilterActive ? 1 : 0;
        for (const c of this.inlineCriteria) {
            const val = this.state.applied?.[c.key];
            if (Array.isArray(val) ? val.length > 0 : Boolean(val && (val.id || val.isFalse || val.from || val.to || (typeof val === "string" && val !== "all" && val.trim())))) {
                inlineActive += 1;
            }
        }
        return Math.max(totalActive - inlineActive, 0);
    }

    get drawerButtonLabel() {
        const n = this.drawerBadgeCount;
        return n > 0 ? `Bộ lọc (${n})` : "Bộ lọc";
    }

    toggleDrawer() {
        this.ui.drawerOpen = !this.ui.drawerOpen;
    }

    closeDrawer() {
        this.ui.drawerOpen = false;
    }

    openAdvanced() {
        this.ui.drawerOpen = false;
        super.openAdvanced();
    }

    async applyAndClose() {
        await this.applyFilters();
        if (!this.validationErrors.length && !this.state.error) {
            this.ui.drawerOpen = false;
        }
    }

    onBarKeyDown(ev) {
        if (ev.key === "Escape" && this.ui.drawerOpen) {
            ev.stopPropagation();
            this.ui.drawerOpen = false;
        }
    }
}
