/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formView } from "@web/views/form/form_view";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { kdPrefs, PAGE_SIZE_OPTIONS } from "../prefs";
import { TpKdPrefs } from "../sidebar/sidebar";

const STATE_STORAGE_PREFIX = "tp_kd_report_state_v1";
const COL_STORAGE_PREFIX = "tp_kd_report_cols_v1";

export function reportStateKey() {
    return `${STATE_STORAGE_PREFIX}:${session.db || "default"}:${user.userId || 0}`;
}

export function reportColumnKey(reportKey) {
    return `${COL_STORAGE_PREFIX}:${session.db || "default"}:${user.userId || 0}:${reportKey || "R01"}`;
}

export function defaultFilterValues() {
    return {
        period_preset: "",
        date_from: "",
        date_to: "",
        project_id: "",
        owner_id: "",
        status: "",
        sub_filter: "",
    };
}

export function readReportState() {
    try {
        const raw = browser.sessionStorage.getItem(reportStateKey());
        if (!raw) {
            return null;
        }
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object") {
            return null;
        }
        return parsed;
    } catch {
        return null;
    }
}

export function writeReportState(stateSnapshot) {
    try {
        browser.sessionStorage.setItem(reportStateKey(), JSON.stringify(stateSnapshot));
    } catch {
        // Ignore storage quota / privacy mode errors
    }
}

export function readVisibleColumns(reportKey, columns) {
    const defaults = {};
    for (const col of columns || []) {
        defaults[col.key] = col.default_visible !== false;
    }
    try {
        const raw = browser.localStorage.getItem(reportColumnKey(reportKey));
        if (!raw) {
            return defaults;
        }
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object") {
            return defaults;
        }
        const out = { ...defaults };
        for (const col of columns || []) {
            if (!col.optional) {
                out[col.key] = true;
            } else if (typeof parsed[col.key] === "boolean") {
                out[col.key] = parsed[col.key];
            }
        }
        return out;
    } catch {
        return defaults;
    }
}

export function writeVisibleColumns(reportKey, map) {
    try {
        browser.localStorage.setItem(reportColumnKey(reportKey), JSON.stringify(map));
    } catch {
        // Ignore storage errors
    }
}

export function computePeriodDates(preset, todayStr) {
    const baseStr = todayStr || new Date().toISOString().slice(0, 10);
    const parts = baseStr.split("-").map((n) => Number(n));
    const y = parts[0] || 2026;
    const m = parts[1] || 1;
    const pad = (n) => String(n).padStart(2, "0");
    const lastDay = (year, month) => new Date(year, month, 0).getDate();

    if (preset === "this_month") {
        const end = lastDay(y, m);
        return { date_from: `${y}-${pad(m)}-01`, date_to: `${y}-${pad(m)}-${pad(end)}` };
    }
    if (preset === "this_quarter") {
        const qStart = Math.floor((m - 1) / 3) * 3 + 1;
        const qEnd = qStart + 2;
        const end = lastDay(y, qEnd);
        return { date_from: `${y}-${pad(qStart)}-01`, date_to: `${y}-${pad(qEnd)}-${pad(end)}` };
    }
    if (preset === "this_year") {
        return { date_from: `${y}-01-01`, date_to: `${y}-12-31` };
    }
    return { date_from: "", date_to: "" };
}

function isAccessFailure(err) {
    const name = err?.data?.name || err?.name || "";
    const msg = err?.data?.message || err?.message || "";
    return (
        name.includes("AccessError") ||
        name.includes("AccessDenied") ||
        name.includes("SessionExpired") ||
        msg.includes("không có quyền") ||
        msg.includes("Access Denied")
    );
}

function extractErrorMessage(err, fallback) {
    return err?.data?.message || err?.message || fallback;
}

export class KdReportCenter extends Component {
    static template = "tp_kd_workspace.ReportCenter";
    static components = { Dropdown, DropdownItem, TpKdPrefs };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.prefs = kdPrefs;
        this.seq = 0;

        const restored = readReportState();
        const initialFilters = restored?.applied ? { ...defaultFilterValues(), ...restored.applied } : defaultFilterValues();
        const initialPageSize = PAGE_SIZE_OPTIONS.includes(Number(restored?.pageSize)) ? Number(restored.pageSize) : 20;

        this.state = proxy({
            reportKey: restored?.reportKey || "R01",
            pending: { ...initialFilters },
            applied: { ...initialFilters },
            groupBy: restored?.groupBy || "",
            sortBy: restored?.sortBy || "",
            sortDir: restored?.sortDir === "desc" ? "desc" : "asc",
            page: Math.max(1, Number(restored?.page) || 1),
            pageSize: initialPageSize,
            search: restored?.search || "",
            filtersOpen: false,
            loading: true,
            exporting: false,
            intro: true,
            denied: false,
            error: "",
            dateError: "",
            data: null,
            visibleCols: {},
        });

        onWillStart(async () => {
            await this.loadReport();
            this.state.intro = false;
        });
    }

    rootClass() {
        return {
            "is-busy": this.state.loading,
            "is-intro": this.state.intro && !this.prefs.reducedMotion,
            "is-reduced": this.prefs.reducedMotion,
        };
    }

    persistCurrentState() {
        writeReportState({
            reportKey: this.state.reportKey,
            applied: { ...this.state.applied },
            groupBy: this.state.groupBy,
            sortBy: this.state.sortBy,
            sortDir: this.state.sortDir,
            page: this.state.page,
            pageSize: this.state.pageSize,
            search: this.state.search,
        });
    }

    hasPendingChanges() {
        const p = this.state.pending;
        const a = this.state.applied;
        return (
            String(p.period_preset || "") !== String(a.period_preset || "") ||
            String(p.date_from || "") !== String(a.date_from || "") ||
            String(p.date_to || "") !== String(a.date_to || "") ||
            String(p.project_id ?? "") !== String(a.project_id ?? "") ||
            String(p.owner_id ?? "") !== String(a.owner_id ?? "") ||
            String(p.status || "") !== String(a.status || "") ||
            String(p.sub_filter || "") !== String(a.sub_filter || "")
        );
    }

    hasAnyFilter() {
        const a = this.state.applied;
        return Boolean(
            a.period_preset ||
                a.date_from ||
                a.date_to ||
                a.project_id !== "" ||
                a.owner_id !== "" ||
                a.status ||
                a.sub_filter ||
                this.state.search
        );
    }

    toggleMobileFilters() {
        this.state.filtersOpen = !this.state.filtersOpen;
    }

    setPendingPeriod(preset) {
        this.state.pending.period_preset = preset;
        if (preset === "this_month" || preset === "this_quarter" || preset === "this_year") {
            const dates = computePeriodDates(preset, this.state.data?.today);
            this.state.pending.date_from = dates.date_from;
            this.state.pending.date_to = dates.date_to;
        } else if (!preset) {
            this.state.pending.date_from = "";
            this.state.pending.date_to = "";
        }
        this.state.dateError = "";
    }

    setPendingField(field, ev) {
        const val = ev.target.value;
        if (field === "date_from" || field === "date_to") {
            this.state.pending[field] = val || "";
            this.state.pending.period_preset = (this.state.pending.date_from || this.state.pending.date_to) ? "custom" : "";
            this.state.dateError = "";
            return;
        }
        if (field === "project_id") {
            if (!val) {
                this.state.pending.project_id = "";
            } else if (val === "unassigned") {
                this.state.pending.project_id = "unassigned";
            } else {
                this.state.pending.project_id = Number(val);
            }
            return;
        }
        if (field === "owner_id") {
            this.state.pending.owner_id = val ? Number(val) : "";
            return;
        }
        this.state.pending[field] = val || "";
    }

    async applyFilters() {
        const p = this.state.pending;
        if (p.date_from && p.date_to && p.date_from > p.date_to) {
            this.state.dateError = "Khoảng ngày không hợp lệ: 'Từ ngày' không được lớn hơn 'Đến ngày'.";
            return;
        }
        this.state.dateError = "";
        this.state.applied = { ...p };
        this.state.page = 1;
        await this.loadReport();
    }

    async resetFilters() {
        const clean = defaultFilterValues();
        this.state.pending = { ...clean };
        this.state.applied = { ...clean };
        this.state.search = "";
        this.state.dateError = "";
        this.state.page = 1;
        await this.loadReport();
    }

    async selectReport(reportKey) {
        if (reportKey === this.state.reportKey && this.state.data) {
            return;
        }
        this.state.reportKey = reportKey;
        // Keep shared period/project/owner filters, reset report-specific status/sub_filter/group/sort
        this.state.pending.status = "";
        this.state.pending.sub_filter = "";
        if (this.state.pending.project_id === "unassigned" && !["R02", "R05"].includes(reportKey)) {
            this.state.pending.project_id = "";
        }
        this.state.applied = { ...this.state.pending };
        this.state.groupBy = "";
        this.state.sortBy = "";
        this.state.sortDir = "asc";
        this.state.page = 1;
        await this.loadReport();
    }

    onTabKeydown(ev, idx) {
        const catalog = this.state.data?.catalog || [];
        if (!catalog.length) {
            return;
        }
        let targetIdx = -1;
        if (ev.key === "ArrowRight") {
            targetIdx = (idx + 1) % catalog.length;
        } else if (ev.key === "ArrowLeft") {
            targetIdx = (idx - 1 + catalog.length) % catalog.length;
        } else if (ev.key === "Home") {
            targetIdx = 0;
        } else if (ev.key === "End") {
            targetIdx = catalog.length - 1;
        }
        if (targetIdx >= 0) {
            ev.preventDefault();
            const nextKey = catalog[targetIdx].key;
            this.selectReport(nextKey);
            const root = ev.currentTarget?.closest?.(".o_tp_kd_rc") || document.querySelector(".o_tp_kd_rc");
            const btn = root?.querySelector(`[data-report-tab="${nextKey}"]`);
            btn?.focus();
        }
    }

    async changeGroupBy(ev) {
        this.state.groupBy = ev.target.value || "";
        this.state.page = 1;
        await this.loadReport();
    }

    async changeSortBy(ev) {
        this.state.sortBy = ev.target.value || "";
        this.state.page = 1;
        await this.loadReport();
    }

    async toggleSortDir() {
        this.state.sortDir = this.state.sortDir === "asc" ? "desc" : "asc";
        this.state.page = 1;
        await this.loadReport();
    }

    async sortByColumn(col) {
        if (!col.sortable) {
            return;
        }
        const sortKey = col.key.endsWith("_display") ? col.key.replace("_display", "") : col.key;
        if (this.state.sortBy === sortKey) {
            this.state.sortDir = this.state.sortDir === "asc" ? "desc" : "asc";
        } else {
            this.state.sortBy = sortKey;
            this.state.sortDir = "asc";
        }
        this.state.page = 1;
        await this.loadReport();
    }

    async onSearchInput(ev) {
        this.state.search = ev.target.value || "";
        this.state.page = 1;
        await this.loadReport();
    }

    async clearSearch() {
        if (!this.state.search) {
            return;
        }
        this.state.search = "";
        this.state.page = 1;
        await this.loadReport();
    }

    async changePageSize(ev) {
        const size = Number(ev.target.value);
        if (!PAGE_SIZE_OPTIONS.includes(size)) {
            return;
        }
        this.state.pageSize = size;
        this.state.page = 1;
        await this.loadReport();
    }

    async goToPage(page) {
        const totalPages = this.state.data?.pagination?.total_pages || 1;
        const target = Math.max(1, Math.min(totalPages, Number(page) || 1));
        if (target === this.state.page) {
            return;
        }
        this.state.page = target;
        await this.loadReport();
    }

    async onChartItemClick(item) {
        if (item.filter_status) {
            const next = this.state.applied.status === item.filter_status ? "" : item.filter_status;
            this.state.pending.status = next;
            this.state.applied.status = next;
            this.state.page = 1;
            await this.loadReport();
        } else if (item.filter_sub) {
            const next = this.state.applied.sub_filter === item.filter_sub ? "" : item.filter_sub;
            this.state.pending.sub_filter = next;
            this.state.applied.sub_filter = next;
            this.state.page = 1;
            await this.loadReport();
        }
    }

    toggleColumn(col) {
        if (!col.optional) {
            return;
        }
        const next = { ...this.state.visibleCols, [col.key]: !this.state.visibleCols[col.key] };
        this.state.visibleCols = next;
        writeVisibleColumns(this.state.reportKey, next);
    }

    resetColumns() {
        const cols = this.state.data?.columns || [];
        const defaults = {};
        for (const col of cols) {
            defaults[col.key] = col.default_visible !== false;
        }
        this.state.visibleCols = defaults;
        writeVisibleColumns(this.state.reportKey, defaults);
    }

    visibleColumns() {
        const cols = this.state.data?.columns || [];
        return cols.filter((col) => !col.optional || this.state.visibleCols[col.key] !== false);
    }

    optionalColumns() {
        return (this.state.data?.columns || []).filter((col) => col.optional);
    }

    donutSlices(items, total) {
        if (!total || !items?.length) {
            return [];
        }
        let offset = 0;
        const slices = [];
        for (const item of items) {
            if (!item.value) {
                continue;
            }
            const length = (item.value / total) * 100;
            slices.push({
                ...item,
                dash: `${length} ${100 - length}`,
                offset: -offset,
            });
            offset += length;
        }
        return slices;
    }

    async loadReport() {
        const seq = ++this.seq;
        this.state.loading = true;
        this.state.error = "";
        try {
            const res = await this.orm.call(
                "tp.kd.report.center",
                "get_kd_report",
                [
                    this.state.reportKey,
                    this.state.applied,
                    this.state.groupBy || false,
                    this.state.sortBy || false,
                    this.state.sortDir,
                    this.state.page,
                    this.state.pageSize,
                    this.state.search,
                ]
            );
            if (seq !== this.seq) {
                return;
            }
            this.state.denied = false;
            this.state.data = res;
            this.state.groupBy = res.applied_filters.group_by;
            this.state.sortBy = res.applied_filters.sort_by;
            this.state.sortDir = res.applied_filters.sort_dir;
            this.state.page = res.pagination.page;
            this.state.visibleCols = readVisibleColumns(res.report_key, res.columns);
            this.persistCurrentState();
        } catch (err) {
            if (seq !== this.seq) {
                return;
            }
            if (isAccessFailure(err)) {
                this.state.data = null;
                this.state.denied = true;
                this.state.error = extractErrorMessage(err, "Quyền truy cập của bạn đã thay đổi hoặc hết phiên.");
            } else {
                this.state.error = extractErrorMessage(err, "Không tải được dữ liệu báo cáo. Vui lòng thử lại.");
            }
        } finally {
            if (seq === this.seq) {
                this.state.loading = false;
            }
        }
    }

    async openDrill(kind, payload) {
        this.persistCurrentState();
        try {
            const act = await this.orm.call("tp.kd.report.center", "action_kd_report_open", [kind, payload]);
            await this.action.doAction(act);
        } catch (err) {
            if (isAccessFailure(err)) {
                this.state.data = null;
                this.state.denied = true;
                this.state.error = extractErrorMessage(err, "Bạn không còn quyền mở hồ sơ nguồn này.");
            } else {
                this.state.error = extractErrorMessage(err, "Không mở được hồ sơ nguồn.");
            }
        }
    }

    async exportExcel() {
        if (this.state.exporting || this.state.denied) {
            return;
        }
        this.state.exporting = true;
        this.state.error = "";
        try {
            const res = await this.orm.call(
                "tp.kd.report.center",
                "export_kd_report_xlsx",
                [
                    this.state.reportKey,
                    this.state.applied,
                    this.state.groupBy || false,
                    this.state.sortBy || false,
                    this.state.sortDir,
                    this.state.search,
                ]
            );
            const binaryStr = window.atob(res.content_base64);
            const bytes = new Uint8Array(binaryStr.length);
            for (let i = 0; i < binaryStr.length; i++) {
                bytes[i] = binaryStr.charCodeAt(i);
            }
            const blob = new Blob([bytes], {
                type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = res.filename || `TANPHAT_KD_${this.state.reportKey}.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 2000);
        } catch (err) {
            if (isAccessFailure(err)) {
                this.state.data = null;
                this.state.denied = true;
                this.state.error = extractErrorMessage(err, "Bạn không còn quyền xuất báo cáo này.");
            } else {
                this.state.error = extractErrorMessage(err, "Xuất file Excel không thành công.");
            }
        } finally {
            this.state.exporting = false;
        }
    }
}

registry.category("views").add("tp_kd_report_center", {
    ...formView,
    Controller: KdReportCenter,
});
