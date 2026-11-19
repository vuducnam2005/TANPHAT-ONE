import { onWillUnmount } from "@odoo/owl";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Domain } from "@web/core/domain";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";

// Composition must finish before the native autocomplete debounce starts.
export class HrNameAutoComplete extends AutoComplete {
    static template = "tp_hr_workspace.NameAutoComplete";
    onCompositionStart() {
        this.composing = true;
        this.debouncedProcessInput.cancel();
        this.close();
    }
    onCompositionEnd() {
        this.composing = false;
        super.onInput();
    }
    onInput(ev) {
        if (!this.composing && !ev?.isComposing) return super.onInput();
    }
    onInputKeydown(ev) {
        if (!this.composing && !ev.isComposing) return super.onInputKeydown(ev);
    }
}

export class HrEmployeeFilterBar extends TpTableFilterBar {
    static template = "tp_hr_workspace.EmployeeFilterBar";
    static components = { ...TpTableFilterBar.components, HrNameAutoComplete, SearchBarMenu };

    setup() {
        super.setup();
        this.advancedDropdown = useDropdownState();
        this.state.nameReset = 0;
        this.nameRequest = 0;
        onWillUnmount(() => { this.nameRequest++; this.disposed = true; });
    }

    get liveNamesEnabled() {
        return this.resModel === "hr.employee" && !this.env.inDialog &&
            !this.actionContext.tp_filter_profile && !this.actionContext.tp_hr_relation;
    }

    get criteria() {
        return super.criteria.map(c => this.liveNamesEnabled && c.key === "name"
            ? { ...c, recordSuggestions: true } : c);
    }

    nameValue(criterion) {
        const value = this.state.pending[criterion.key];
        return value?.label ?? value ?? "";
    }

    onNameInput({ inputValue }, criterion) {
        if (this.blocked || this.disposed) return;
        this.nameRequest++;
        this.state.pending[criterion.key] = inputValue;
        // Apply this one field without submitting other unfinished criteria.
        return this.applyFilters(criterion.key);
    }

    nameSuggestionDomain(criterion) {
        const search = this.env.searchModel;
        const domains = [search.globalDomain];
        for (const group of search._getGroups()) {
            const items = group.activeItems.filter(item =>
                search.searchItems[item.searchItemId]?.tpFilterKey !== criterion.key);
            domains.push(Domain.or(items.map(item => search._getSearchItemDomain(item)).filter(Boolean)));
        }
        if (search.display.searchPanel) domains.push(search._getSearchPanelDomain());
        return Domain.and(domains).toList(search.domainEvalContext);
    }

    nameSources(criterion) {
        return [{ placeholder: "Đang tìm nhân viên…", options: async (query) => {
            const seq = ++this.nameRequest;
            const search = this.env.searchModel;
            const domain = this.nameSuggestionDomain(criterion);
            const scope = JSON.stringify([search.context, domain]);
            if (!query.trim() || this.blocked) return [];
            try {
                const rows = await this.orm.searchRead(this.resModel,
                    Domain.and([domain, [[criterion.field, "ilike", query.trim()]]]).toList(),
                    ["name", "tp_employee_code"], { limit: 16, context: search.context });
                if (this.disposed || seq !== this.nameRequest ||
                    scope !== JSON.stringify([search.context, this.nameSuggestionDomain(criterion)])) return [];
                const options = rows.slice(0, 15).map(row => ({
                    label: row.name + (row.tp_employee_code ? ` · ${row.tp_employee_code}` : ""),
                    onSelect: () => {
                        this.nameRequest++;
                        this.state.pending[criterion.key] = { id: row.id, label: row.name };
                        this.applyFilters(criterion.key);
                    },
                }));
                if (rows.length > 15) options.push({ label: "Xem tất cả kết quả trong bảng",
                    onSelect: () => this.onNameInput({ inputValue: query }, criterion) });
                return options.length ? options : [{ label: "Không có nhân viên phù hợp" }];
            } catch {
                return this.disposed || seq !== this.nameRequest ? [] : [{ label: "Không tải được gợi ý. Hãy thử lại." }];
            }
        } }];
    }

    async clearAllFilters() {
        if (this.blocked) return;
        this.nameRequest++;
        this.state.nameReset++;
        return super.clearAllFilters();
    }

    removeFacet(facet) {
        if (this.blocked) return;
        this.nameRequest++;
        if (Object.values(this.env.searchModel.searchItems).some(item =>
            item.groupId === facet.groupId && item.tpFilterKey === "name")) {
            this.state.pending.name = "";
            this.state.nameReset++;
        }
        return super.removeFacet(facet);
    }

    openAdvanced() {
        if (!this.liveNamesEnabled) return super.openAdvanced();
        if (!this.blocked) this.advancedDropdown.open();
    }
}
