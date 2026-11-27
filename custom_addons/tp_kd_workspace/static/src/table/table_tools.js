/** @odoo-module **/
import { Component, proxy, useProps, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { ProjectListController } from "@project/views/project_project_list/project_project_list_controller";
import { projectProjectListView } from "@project/views/project_project_list/project_project_list_view";
import { forgetColumns, KD_COLUMN_PREFIXES, kdPrefs, savePrefs, PAGE_SIZE_OPTIONS, tablePageKey, readPageSize, writePageSize } from "../prefs";
import { useBus } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import { Domain } from "@web/core/domain";
import { deserializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSetupAction } from "@web/search/action_hook";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import "./filter_profiles";

class KdSearchBar extends SearchBar {
    static template = "tp_kd_workspace.SearchBar";
}

/**
 * KD-UI-003 table toolbar: density (same source as the sidebar ⚙) and "reset columns" for the
 * list currently open. Presentation only: no RPC, no record value, no column hard-coded.
 * The column chooser itself stays the native optional-columns dropdown in the table header.
 */
export class KdTableTools extends Component {
    static template = "tp_kd_workspace.TableTools";
    static components = { InlineErrors };
    props = useProps();
    prefs = kdPrefs;
    pageSizes = PAGE_SIZE_OPTIONS;

    setup() {
        KD_COLUMN_PREFIXES.add(this.columnPrefix);
        this.state = proxy({
            field: "",
            value: "",
            busy: false,
            open: false,
            headCreate: false,
            contractCreate: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,
        });
        onWillStart(async () => {
            try {
                if (this.controller.props.resModel === "project.project") {
                    const rights = await this.env.services.orm.call("project.project", "get_kd_ui_permissions", []);
                    this.state.headCreate = Boolean(rights?.head_create);
                } else if (this.controller.props.resModel === "tp.contract") {
                    const rights = await this.env.services.orm.call("tp.contract", "get_kd_ui_permissions", []);
                    this.state.contractCreate = Boolean(rights?.can_create_contract);
                }
            } catch (err) {
                this.state.attempt += 1;
                this.state.serverError = saveError(err, { verb: "kiểm tra quyền thao tác bảng", write: false });
            }
        });
        useBus(this.env.searchModel, "update", () => render(this));
    }

    async createHeadProject() {
        this.state.serverError = null;
        try {
            const action = await this.env.services.orm.call("project.project", "action_kd_head_new_project", []);
            await this.env.services.action.doAction(action);
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "mở hộp tạo dự án KH-KD", write: false });
        }
    }

    get filters() {
        return this.env.searchModel.getSearchItems((item) => item.type === "filter" && !item.custom).slice(0, 8);
    }
    get filterFields() {
        const names = ["kd_bid_state", "state", "review_state", "lifecycle_state", "tp_latest_review_state",
            "project_id", "tp_project_id", "partner_id", "user_id", "owner_id", "kd_responsible_id",
            "period_kind", "allocation_kind", "direction", "payment_basis", "checklist_status", "subject_kind",
            "credential_kind", "contract_type", "reconciliation_state", "kd_route", "name", "code",
            "actor_id", "action", "amount_state", "revision_kind", "scope_key", "reference",
            "state_before", "state_after", "outcome", "decision", "verification_state", "authority_status",
            "signature_status", "signature_authority_status", "effectivity_status", "document_kind", "file_name",
            "base_reference", "reference_kind", "subject_id", "counterparty_id", "recipient_department_id",
            "department_id", "tp_department_id", "role", "source_status", "measure",
            "date_due", "kd_deadline", "date_deadline", "period_from", "period_to", "valid_to",
            "kd_lifecycle", "kd_investor_id", "stage", "investor_id", "deadline", "package_id", "kind", "tax_basis"];
        const fields = this.env.searchModel.searchViewFields;
        return names.filter((name) => fields[name]?.searchable !== false && fields[name] &&
            ["selection", "many2one", "char", "text", "date", "datetime"].includes(fields[name].type))
            .map((name) => ({ ...fields[name], name }));
    }
    get selectedField() {
        return this.filterFields.find((field) => field.name === this.state.field) || this.filterFields[0];
    }
    get blocked() { return Boolean(this.controller.editedRecord); }
    async changeSize(ev) {
        const limit = Number(ev.target.value);
        if (this.blocked || !PAGE_SIZE_OPTIONS.includes(limit)) return;
        this.state.busy = true;
        this.state.serverError = null;
        try {
            await this.controller.model.root.load({ limit, offset: 0 });
            writePageSize(this.controller.kdPageKey, limit);
            render(this.controller);
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "đổi số dòng hiển thị", write: false });
        } finally { this.state.busy = false; }
    }
    toggleFilter(item) {
        if (!this.blocked) this.env.searchModel.toggleSearchItem(item.id);
    }
    clearFilters() {
        if (!this.blocked) this.env.searchModel.clearFilters();
    }
    addFilter() {
        const field = this.selectedField;
        const value = this.state.value.trim();
        if (this.blocked || !field || !value) return;
        const isDate = ["date", "datetime"].includes(field.type);
        const operator = isDate ? "<=" : field.type === "selection" ? "=" : "ilike";
        const domainValue = field.type === "datetime" ? serializeDateTime(deserializeDate(value).endOf("day")) : value;
        const label = field.selection?.find(([key]) => key === value)?.[1] || value;
        this.env.searchModel.createNewFilters([{
            description: `${field.string}${isDate ? ' đến hết ngày' : ''}: ${label}`,
            domain: new Domain([[field.name, operator, domainValue]]).toString(),
            custom: true,
        }]);
        this.state.value = "";
    }
    onFilterKey(ev) {
        if (ev.key === "Enter") { ev.preventDefault(); this.addFilter(); }
    }
    advanced() {
        this.controller.rootRef()?.querySelector('.o_searchview_dropdown_toggler')?.click();
    }

    get controller() {
        return this.props.controller;
    }

    /** Same parts as ListRenderer.createViewKey(): model, "list", view id (missing id -> ""). */
    get columnPrefix() {
        const controller = this.controller;
        return `optional_fields,${[controller.props.resModel, "list", controller.env.config.viewId].join(",")},`;
    }

    get optionalColumns() {
        return (this.controller.archInfo.columns || []).filter((col) => col.optional);
    }

    get compact() {
        return this.prefs.density === "compact";
    }

    setDensity(density) {
        savePrefs({ density });
    }

    /** Forget only this view's stored optional columns, then show the arch defaults again. */
    resetColumns() {
        forgetColumns([this.columnPrefix]);
        const active = proxy(this.controller.optionalActiveFields);
        for (const col of this.optionalColumns) {
            active[col.name] = col.optional === "show";
        }
    }
}

export class KdQuickFilters extends KdTableTools {
    static template = "tp_kd_workspace.QuickFilters";
    static components = { TpTableFilterBar, InlineErrors };
}

const kdTableSetup = (Base) =>
    class extends Base {
        static template = "tp_kd_workspace.ListView";
        static components = { ...Base.components, SearchBar: KdSearchBar, KdTableTools, KdQuickFilters };
        setup() {
            super.setup();
            useSetupAction({ getGlobalState: () => this.kdEnabled ? {
                tpKdListState: {
                    key: this.kdPageKey, limit: this.model.root.limit, offset: this.model.root.offset,
                    orderBy: this.model.root.orderBy.map(order => ({ ...order })),
                },
            } : {} });
        }
        get kdEnabled() {
            // Views using js_class="tp_kd_*" belong to KH-KD / TP Contracts regardless of deep-link or current app menu state.
            return true;
        }
        get kdPageKey() {
            return tablePageKey(this.props.resModel, this.env.config.actionId,
                this.props.context?.tp_kd_relation || this.env.config.viewId);
        }
        get modelParams() {
            const params = super.modelParams;
            if (!this.kdEnabled || this.props.state?.modelState) return params;
            const saved = this.props.globalState?.tpKdListState;
            if (saved?.key === this.kdPageKey && PAGE_SIZE_OPTIONS.includes(saved.limit) &&
                Number.isInteger(saved.offset) && saved.offset >= 0 && Array.isArray(saved.orderBy)) {
                return { ...params, config: { ...params.config, limit: saved.limit,
                    offset: saved.offset, orderBy: saved.orderBy } };
            }
            return { ...params, limit: readPageSize(this.kdPageKey) };
        }
    };

/** Plain KH-KD list (opportunities): native list behaviour + table toolbar. */
export class KdTableController extends kdTableSetup(ListController) {}
registry.category("views").add("tp_kd_table", { ...listView, Controller: KdTableController });

/** KH-KD project list: keeps the native project list controller (View Tasks, favourites). */
export class KdProjectListController extends kdTableSetup(ProjectListController) {}
registry.category("views").add("tp_kd_project_list", {
    ...projectProjectListView,
    Controller: KdProjectListController,
});

export { kdTableSetup };
