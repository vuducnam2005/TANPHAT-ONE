/** @odoo-module **/
import { Component, onWillUnmount, proxy, signal, toRaw, useListener, useProps } from "@odoo/owl";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Domain } from "@web/core/domain";
import { KeepLast } from "@web/core/utils/concurrency";
import { useBus, useService } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import {
    buildCriterionFilter,
    cloneCriterionValue,
    createEmptyCriterionValue,
    isCriterionEmpty,
    resolveTableFilterProfile,
    validateCriterionValue,
    valuesEqual,
} from "./filter_domain";

export class TpTableFilterBar extends Component {
    static template = "tp_web_home.TableFilterBar";
    static components = { AutoComplete };
    props = useProps();
    rootRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.uiService = useService("ui");
        this.keepLastMap = new Map();
        this.applySeq = 0;

        const model = toRaw(this.props.controller?.model);
        this.state = proxy({
            mobileOpen: false,
            openPopoverKey: null,
            pending: {},
            applied: {},
            m2oInputs: {},
            busy: false,
            error: model?.__tpFilterError || "",
        });

        this._initValuesFromCriteria();
        this.syncFromSearchModel();

        useBus(this.env.searchModel, "update", () => {
            this.syncFromSearchModel();
            render(this);
        });

        if (model && typeof model.load === "function") {
            model.__tpFilterBar = this;
            onWillUnmount(() => {
                if (model.__tpFilterBar === this) {
                    model.__tpFilterBar = null;
                }
            });
            if (!model.__tpFilterWrappedLoad) {
                const origLoad = model.load.bind(model);
                model.__tpFilterWrappedLoad = true;
                model.load = async (params) => {
                    const bar = model.__tpFilterBar;
                    try {
                        const res = await origLoad(params);
                        model.__tpFilterError = "";
                        if (bar && bar.state.error) {
                            bar.state.error = "";
                            render(bar);
                        }
                        return res;
                    } catch (err) {
                        if (bar && (bar._filterTriggered || bar.hasAnyValue) && model.isReady?.()) {
                            const msg = "Không tải được dữ liệu theo bộ lọc. Vui lòng thử lại.";
                            model.__tpFilterError = msg;
                            bar.state.error = msg;
                            bar.state.busy = false;
                            render(bar);
                            return;
                        }
                        throw err;
                    } finally {
                        if (bar) {
                            bar._filterTriggered = false;
                        }
                    }
                };
            }
        }

        const closeIfOutsideMulti = (ev) => {
            if (!this.state.openPopoverKey) return;
            const activeWrap = ev.target?.closest?.(".tp_filter_item");
            const inSameMulti =
                activeWrap?.dataset?.filterKey === this.state.openPopoverKey &&
                Boolean(ev.target?.closest?.(".tp_filter_multi_wrap"));
            if (!inSameMulti) {
                this.state.openPopoverKey = null;
            }
        };
        useListener(window, "pointerdown", closeIfOutsideMulti, true);
        useListener(window, "focusin", closeIfOutsideMulti, true);

        useListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.state.openPopoverKey) {
                this.state.openPopoverKey = null;
            }
        });
    }

    get resModel() {
        return this.props.controller?.props?.resModel || this.env.searchModel.resModel;
    }

    get actionContext() {
        return this.props.controller?.props?.context || {};
    }

    get profile() {
        return resolveTableFilterProfile(
            this.resModel,
            this.actionContext,
            this.env.searchModel.searchViewFields || {}
        );
    }

    get criteria() {
        return this.profile.criteria;
    }

    get blocked() {
        return Boolean(this.props.blocked ?? this.props.controller?.editedRecord);
    }

    get quickFilters() {
        return this.props.quickFilters || [];
    }

    get validationErrors() {
        const errors = [];
        for (const criterion of this.criteria) {
            const err = validateCriterionValue(criterion, this.state.pending[criterion.key]);
            if (err) {
                errors.push(err);
            }
        }
        return errors;
    }

    get hasPendingChanges() {
        return this.criteria.some(
            (c) => !valuesEqual(c, this.state.pending[c.key], this.state.applied[c.key])
        );
    }

    get hasAnyValue() {
        return (
            this.criteria.some((c) => !isCriterionEmpty(c, this.state.pending[c.key])) ||
            this.activeFilterCount > 0
        );
    }

    get activeFacets() {
        return (this.env.searchModel.facets || []).filter((f) => f.type !== "groupBy");
    }

    get activeFilterCount() {
        return this.activeFacets.length;
    }

    get resultCountText() {
        const root = this.props.controller?.model?.root;
        if (!root || !this.props.controller?.model?.isReady?.()) {
            return "";
        }
        const count = root.count ?? 0;
        return root.isGrouped ? `${count} nhóm kết quả` : `${count} kết quả`;
    }

    _initValuesFromCriteria() {
        for (const criterion of this.criteria) {
            if (!(criterion.key in this.state.pending)) {
                this.state.pending[criterion.key] = createEmptyCriterionValue(criterion);
            }
            if (!(criterion.key in this.state.applied)) {
                this.state.applied[criterion.key] = createEmptyCriterionValue(criterion);
            }
            if (criterion.type === "many2one" && !(criterion.key in this.state.m2oInputs)) {
                this.state.m2oInputs[criterion.key] = "";
            }
        }
    }

    syncFromSearchModel() {
        this._initValuesFromCriteria();
        const searchModel = this.env.searchModel;
        const activeItems = new Map();
        for (const q of searchModel.query || []) {
            const item = searchModel.searchItems?.[q.searchItemId];
            if (item?.tpFilterKey) {
                activeItems.set(item.tpFilterKey, item.tpFilterValue);
            }
        }
        for (const criterion of this.criteria) {
            const prevApplied = this.state.applied[criterion.key];
            const prevPending = this.state.pending[criterion.key];
            const untouched = valuesEqual(criterion, prevPending, prevApplied);
            const nextApplied = activeItems.has(criterion.key)
                ? cloneCriterionValue(criterion, activeItems.get(criterion.key))
                : createEmptyCriterionValue(criterion);
            this.state.applied[criterion.key] = nextApplied;
            if (untouched) {
                this.state.pending[criterion.key] = cloneCriterionValue(criterion, nextApplied);
                if (criterion.type === "many2one") {
                    this.state.m2oInputs[criterion.key] = nextApplied?.label || "";
                }
            }
        }
    }

    toggleQuickFilter(item) {
        if (!this.blocked) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }

    togglePopover(key) {
        if (this.blocked) return;
        this.state.openPopoverKey = this.state.openPopoverKey === key ? null : key;
    }

    isOptionSelected(criterionKey, optionKey) {
        const val = this.state.pending[criterionKey];
        return Array.isArray(val) ? val.includes(optionKey) : val === optionKey;
    }

    toggleMultiOption(criterion, optionKey) {
        if (this.blocked) return;
        const current = Array.isArray(this.state.pending[criterion.key])
            ? [...this.state.pending[criterion.key]]
            : [];
        const idx = current.indexOf(optionKey);
        if (idx >= 0) {
            current.splice(idx, 1);
        } else {
            current.push(optionKey);
        }
        this.state.pending[criterion.key] = current;
    }

    multiSummaryLabel(criterion) {
        const val = this.state.pending[criterion.key];
        if (!Array.isArray(val) || !val.length) {
            return "Tất cả";
        }
        const labels = val.map((k) => {
            if (k === "__false__") return "Chưa khai báo";
            if (criterion.type === "preset") {
                return (criterion.options || []).find((o) => o.key === k)?.label || k;
            }
            return (criterion.options || []).find(([ok]) => String(ok) === String(k))?.[1] || k;
        });
        return labels.length <= 2 ? labels.join(", ") : `${labels.length} đã chọn`;
    }

    setSingleValue(criterion, value) {
        this.state.pending[criterion.key] = value;
    }

    setDateBound(criterion, bound, value) {
        const current = this.state.pending[criterion.key] || { from: "", to: "" };
        this.state.pending[criterion.key] = { ...current, [bound]: value || "" };
    }

    onTextKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.applyFilters();
        }
    }

    m2oSources(criterion) {
        return [
            {
                placeholder: "Đang tải...",
                options: async (query) => {
                    let keepLast = this.keepLastMap.get(criterion.key);
                    if (!keepLast) {
                        keepLast = new KeepLast();
                        this.keepLastMap.set(criterion.key, keepLast);
                    }
                    let searchDomain = [];
                    if (Array.isArray(criterion.relationDomain)) {
                        searchDomain = criterion.relationDomain;
                    } else if (typeof criterion.relationDomain === "string" && criterion.relationDomain.trim()) {
                        try {
                            searchDomain = new Domain(criterion.relationDomain).toList();
                        } catch {
                            searchDomain = [];
                        }
                    }
                    try {
                        const rows = await keepLast.add(
                            this.orm.call(criterion.relation, "name_search", [], {
                                name: query || "",
                                domain: searchDomain,
                                operator: "ilike",
                                limit: 15,
                            })
                        );
                        const opts = (rows || []).map(([id, label]) => ({
                            label,
                            onSelect: () => this.selectM2o(criterion, { id, label }),
                        }));
                        if (criterion.allowEmpty && (!query || "chưa khai báo".includes(query.toLowerCase()))) {
                            opts.unshift({
                                label: "Chưa khai báo",
                                onSelect: () => this.selectM2o(criterion, { isFalse: true, label: "Chưa khai báo" }),
                            });
                        }
                        if (!opts.length) {
                            opts.push({ label: "Không có kết quả phù hợp" });
                        }
                        return opts;
                    } catch {
                        return [{ label: "Không tải được danh sách gợi ý" }];
                    }
                },
            },
        ];
    }

    selectM2o(criterion, selected) {
        this.state.pending[criterion.key] = selected;
        this.state.m2oInputs[criterion.key] = selected?.label || "";
    }

    clearM2o(criterion) {
        this.state.pending[criterion.key] = null;
        this.state.m2oInputs[criterion.key] = "";
    }

    onM2oInput({ inputValue }, criterion) {
        this.state.m2oInputs[criterion.key] = inputValue;
        if (!inputValue.trim()) {
            this.state.pending[criterion.key] = null;
        }
    }

    async applyFilters(onlyKey = null) {
        if (this.blocked || (!onlyKey && this.validationErrors.length)) {
            return;
        }
        this.state.openPopoverKey = null;
        this.state.error = "";
        const rawModel = toRaw(this.props.controller?.model);
        if (rawModel) {
            rawModel.__tpFilterError = "";
        }

        const prefilters = [];
        try {
            for (const criterion of this.criteria) {
                if (onlyKey && criterion.key !== onlyKey) continue;
                const built = buildCriterionFilter(criterion, this.state.pending[criterion.key]);
                if (built) {
                    prefilters.push({
                        description: built.description,
                        domain: built.domain,
                        custom: true,
                        tpFilterKey: criterion.key,
                        tpFilterValue: built.snapshot,
                    });
                }
            }
        } catch (err) {
            this.state.error = err.message || "Giá trị lọc không hợp lệ.";
            return;
        }

        const seq = ++this.applySeq;
        this.state.busy = true;
        this._filterTriggered = true;
        const searchModel = this.env.searchModel;
        const prevBlock = searchModel.blockNotification;
        try {
            searchModel.blockNotification = true;
            // Remove previous managed groups cleanly while preserving user's native SearchBar/GroupBy/Favorite facets.
            const managedGroups = new Set();
            for (const q of searchModel.query || []) {
                const item = searchModel.searchItems?.[q.searchItemId];
                if (item?.tpFilterKey && (!onlyKey || item.tpFilterKey === onlyKey)) {
                    managedGroups.add(item.groupId);
                }
            }
            for (const groupId of managedGroups) {
                searchModel.deactivateGroup(groupId);
            }
            // Add one criterion per SearchModel groupId so distinct criteria AND together.
            for (const pf of prefilters) {
                searchModel.createNewFilters([pf]);
            }
            searchModel.blockNotification = prevBlock;
            await searchModel._notify();
            if (seq === this.applySeq) {
                this.syncFromSearchModel();
            }
        } catch {
            searchModel.blockNotification = prevBlock;
            if (seq === this.applySeq) {
                this.state.error = "Không tải được dữ liệu theo bộ lọc. Vui lòng thử lại.";
            }
        } finally {
            if (seq === this.applySeq) {
                this.state.busy = false;
            }
        }
    }

    async clearAllFilters() {
        if (this.blocked) return;
        this.state.openPopoverKey = null;
        this.state.error = "";
        const rawModel = toRaw(this.props.controller?.model);
        if (rawModel) {
            rawModel.__tpFilterError = "";
        }
        for (const criterion of this.criteria) {
            this.state.pending[criterion.key] = createEmptyCriterionValue(criterion);
            if (criterion.type === "many2one") {
                this.state.m2oInputs[criterion.key] = "";
            }
        }
        const seq = ++this.applySeq;
        this.state.busy = true;
        this._filterTriggered = true;
        try {
            if (this.props.onClearAll) {
                await this.props.onClearAll();
            } else {
                await this.env.searchModel.clearFilters();
            }
            if (seq === this.applySeq) {
                this.syncFromSearchModel();
            }
        } catch {
            if (seq === this.applySeq) {
                this.state.error = "Không xóa được bộ lọc. Vui lòng thử lại.";
            }
        } finally {
            if (seq === this.applySeq) {
                this.state.busy = false;
            }
        }
    }

    removeFacet(facet) {
        if (!this.blocked) {
            this.env.searchModel.deactivateGroup(facet.groupId);
        }
    }

    openAdvanced() {
        if (this.blocked) return;
        if (this.props.onAdvanced) {
            this.props.onAdvanced();
            return;
        }
        this.props.controller?.rootRef?.()?.querySelector(".o_searchview_dropdown_toggler")?.click();
    }
}
