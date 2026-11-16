import { Component, EventBus, proxy, useProps } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { useSetupAction } from "@web/search/action_hook";
import { download } from "@web/core/network/download";
import { TpEquipmentFilterBar } from "./compact_filter_bar";
import {
    ALL_ROWS_LIMIT,
    EQ_COLUMN_PREFIXES,
    eqPrefs,
    forgetColumns,
    PAGE_SIZE_OPTIONS,
    readPageSize,
    savePrefs,
    tablePageKey,
    writePageSize,
} from "../prefs";
import "./filter_profiles";

/** Page size (server paging 10/20/50/100, or all rows on SHOW_ALL_PROFILES), density and "reset columns". */
export class TpEquipmentTableTools extends Component {
    static template = "tp_equipment.TableTools";
    props = useProps();
    prefs = eqPrefs;
    pageSizes = PAGE_SIZE_OPTIONS;

    setup() {
        EQ_COLUMN_PREFIXES.add(this.columnPrefix);
        this.state = proxy({ busy: false });
        useBus(this.env.searchModel, "update", () => render(this));
    }

    get controller() {
        return this.props.controller;
    }
    get blocked() {
        return Boolean(this.controller.editedRecord);
    }
    get compact() {
        return this.prefs.density === "compact";
    }
    get columnPrefix() {
        const c = this.controller;
        return `optional_fields,${[c.props.resModel, "list", c.env.config.viewId].join(",")},`;
    }
    get optionalColumns() {
        return (this.controller.archInfo.columns || []).filter((col) => col.optional);
    }
    get showAllText() {
        const root = this.controller.model.root;
        if (root.count > root.limit) {
            return `Hiển thị ${root.limit} / ${root.count} ${root.isGrouped ? "nhóm" : "dòng"} mỗi trang`;
        }
        return `Hiển thị tất cả ${root.count} ${root.isGrouped ? "nhóm" : "dòng"}`;
    }
    async changeSize(ev) {
        const limit = Number(ev.target.value);
        if (this.blocked || !PAGE_SIZE_OPTIONS.includes(limit)) {
            return;
        }
        this.state.busy = true;
        try {
            await this.controller.model.root.load({ limit, offset: 0 });
            writePageSize(this.controller.eqPageKey, limit);
            render(this.controller);
        } finally {
            this.state.busy = false;
        }
    }
    setDensity(density) {
        savePrefs({ density });
    }
    resetColumns() {
        forgetColumns([this.columnPrefix]);
        const active = proxy(this.controller.optionalActiveFields);
        for (const col of this.optionalColumns) {
            active[col.name] = col.optional === "show";
        }
    }
    async exportXlsx() {
        if (this.blocked || this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            await download({
                url: "/tp_equipment/export.xlsx",
                data: { model: this.controller.props.resModel,
                        domain: JSON.stringify(this.controller.model.root.domain) },
            });
        } finally {
            this.state.busy = false;
        }
    }

    get canExport() {
        return ["maintenance.equipment", "maintenance.request", "tp.equipment.move", "tp.equipment.move.line",
                "tp.equipment.receipt", "tp.equipment.proposal", "tp.equipment.inventory",
                "tp.equipment.inventory.line", "tp.equipment.import.batch"].includes(this.controller.props.resModel);
    }
}

// Scoped tables that list every row on one page instead of 10/20/50/100 paging.
const SHOW_ALL_PROFILES = ["equipment_users", "equipment_main"];
// Tables that show no preset chips at all (EQUIP-SIMPLE-003: only search + department/user/type/condition).
const NO_QUICK_FILTER_PROFILES = ["equipment_main"];
const MAIN_PROFILE = "equipment_main";
const SEGMENTS = { in_use: "seg_in_use", stock: "seg_stock" };

/**
 * EQUIP-SIMPLE-003 (DEC-047) header of the single "Thiết bị" list: 3 real counts of the scope (backend
 * tp_main_summary, same action domain as the list and XLSX), the Tất cả / Đang sử dụng / Trong kho segmented
 * control (toggles the seg_* filters of the search view: backend domain, no JS filtering) and the labelled
 * "Phạm vi nâng cao" entry to drafts, retired records, services, mounted components and pending source rows.
 */
export class TpEquipmentMainHeader extends Component {
    static template = "tp_equipment.MainHeader";
    static components = { Dropdown, DropdownItem };
    props = useProps();
    advancedScopes = [
        { section: "Hồ sơ thiết bị" },
        { xmlid: "tp_equipment.action_equipment_all_records", label: "Tất cả hồ sơ (gồm dịch vụ, linh kiện đã gắn)" },
        { xmlid: "tp_equipment.action_equipment_draft", label: "Hồ sơ nháp" },
        { xmlid: "tp_equipment.action_equipment_retired", label: "Ngừng quản lý" },
        { section: "Dữ liệu nguồn & lịch sử" },
        { xmlid: "tp_equipment.action_import_pending", label: "Dòng nguồn chờ bổ sung" },
        { xmlid: "tp_equipment.action_move_lines", label: "Lịch sử bàn giao" },
        { xmlid: "tp_equipment.action_moves_pending", label: "Phiếu chờ bàn giao" },
        { xmlid: "tp_equipment.action_repairs", label: "Sửa chữa / bảo trì" },
        { section: "Cấu hình" },
        { xmlid: "tp_equipment.action_category", label: "Phân loại thiết bị" },
        { xmlid: "tp_equipment.action_location", label: "Vị trí đặt thiết bị" },
    ];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = proxy({ counts: null, failed: false });
        useBus(this.env.searchModel, "update", () => render(this));
        useBus(this.props.controller.eqBus, "reloaded", () => this.loadCounts());
        this.loadCounts();
    }
    get blocked() {
        return Boolean(this.props.controller.editedRecord);
    }
    async loadCounts() {
        try {
            this.state.counts = await this.orm.call("maintenance.equipment", "tp_main_summary", []);
            this.state.failed = false;
        } catch {
            this.state.failed = true;
        }
    }
    count(key) {
        const value = this.state.counts?.[key];
        return Number.isInteger(value) ? value : "…";
    }
    get segItems() {
        const names = Object.values(SEGMENTS);
        const items = this.env.searchModel.getSearchItems((item) => item.type === "filter" && names.includes(item.name));
        return Object.fromEntries(items.map((item) => [item.name, item]));
    }
    get segment() {
        const items = this.segItems;
        const inUse = Boolean(items.seg_in_use?.isActive);
        const stock = Boolean(items.seg_stock?.isActive);
        if (inUse && stock) {
            return "mixed";
        }
        return inUse ? "in_use" : stock ? "stock" : "all";
    }
    get segments() {
        return [
            { key: "all", label: "Tất cả", count: this.count("total") },
            { key: "in_use", label: "Đang sử dụng", count: this.count("in_use") },
            { key: "stock", label: "Trong kho", count: this.count("stock") },
        ];
    }
    async setSegment(key) {
        if (this.blocked || key === this.segment) {
            return;
        }
        const searchModel = this.env.searchModel;
        const items = this.segItems;
        const groupId = (items.seg_in_use || items.seg_stock)?.groupId;
        const target = items[SEGMENTS[key]];
        const previous = searchModel.blockNotification;
        searchModel.blockNotification = true;
        try {
            if (groupId !== undefined) {
                searchModel.deactivateGroup(groupId);
            }
        } finally {
            searchModel.blockNotification = previous;
        }
        if (target) {
            searchModel.toggleSearchItem(target.id);
        } else {
            await searchModel._notify();
        }
    }
    openScope(scope) {
        if (!this.blocked) {
            this.actionService.doAction(scope.xmlid);
        }
    }
}

const QUICK_FILTER_EXCLUDES = {
    equipment_users: ["q_available", "q_in_use", "q_draft", "q_printer_copier"],
    equipment_shared: ["q_available", "q_in_use", "q_draft", "q_archived_holder", "q_printer_copier"],
};

export class TpEquipmentQuickFilters extends Component {
    static template = "tp_equipment.QuickFilters";
    static components = { TpEquipmentFilterBar };
    props = useProps();

    setup() {
        useBus(this.env.searchModel, "update", () => render(this));
    }
    get controller() {
        return this.props.controller;
    }
    get blocked() {
        return Boolean(this.controller.editedRecord);
    }
    get filters() {
        // Scoped tables hide quick filters that contradict their fixed backend domain (EQUIP-UI-002).
        const profile = this.controller.props.context?.tp_filter_profile;
        if (NO_QUICK_FILTER_PROFILES.includes(profile)) {
            return [];
        }
        const hidden = QUICK_FILTER_EXCLUDES[profile] || [];
        return this.env.searchModel
            .getSearchItems((item) => item.type === "filter" && !item.custom && item.name?.startsWith("q_")
                && !hidden.includes(item.name))
            .slice(0, 9);
    }
    advanced() {
        this.controller.rootRef?.()?.querySelector(".o_searchview_dropdown_toggler")?.click();
    }
    clearFilters() {
        if (!this.blocked) {
            this.env.searchModel.clearFilters();
        }
    }
}

export const eqTableSetup = (Base) =>
    class extends Base {
        static template = "tp_equipment.ListView";
        static components = { ...Base.components, TpEquipmentTableTools, TpEquipmentQuickFilters, TpEquipmentMainHeader };
        setup() {
            super.setup();
            // EQUIP-SIMPLE-003: every list reload (popup closed, search changed, row menu action) refreshes the
            // header counts; the reload itself keeps the current search, so filters survive without F5.
            this.eqBus = new EventBus();
            if (this.eqMain) {
                const model = this.model;
                const load = model.load;
                model.load = async (...args) => {
                    const result = await load.apply(model, args);
                    this.eqBus.trigger("reloaded");
                    return result;
                };
            }
            useSetupAction({
                getGlobalState: () => ({
                    tpEqListState: {
                        key: this.eqPageKey,
                        limit: this.model.root.limit,
                        offset: this.model.root.offset,
                        orderBy: this.model.root.orderBy.map((order) => ({ ...order })),
                    },
                }),
            });
        }
        get eqPageKey() {
            return tablePageKey(this.props.resModel, this.env.config.actionId, this.env.config.viewId);
        }
        get eqMain() {
            return this.props.context?.tp_filter_profile === MAIN_PROFILE;
        }
        get eqShowAll() {
            return SHOW_ALL_PROFILES.includes(this.props.context?.tp_filter_profile);
        }
        get modelParams() {
            const params = super.modelParams;
            if (this.props.state?.modelState) {
                return params;
            }
            const saved = this.props.globalState?.tpEqListState;
            const allowed = this.eqShowAll ? [ALL_ROWS_LIMIT] : PAGE_SIZE_OPTIONS;
            if (
                saved?.key === this.eqPageKey &&
                allowed.includes(saved.limit) &&
                Number.isInteger(saved.offset) &&
                saved.offset >= 0 &&
                Array.isArray(saved.orderBy)
            ) {
                return {
                    ...params,
                    config: { ...params.config, limit: saved.limit, offset: saved.offset, orderBy: saved.orderBy },
                };
            }
            return { ...params, limit: this.eqShowAll ? ALL_ROWS_LIMIT : readPageSize(this.eqPageKey) };
        }
    };

export class TpEquipmentListController extends eqTableSetup(ListController) {}
registry.category("views").add("tp_equipment_table", { ...listView, Controller: TpEquipmentListController });
