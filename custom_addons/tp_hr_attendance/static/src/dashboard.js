import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { CHART_COLORS, baseOptions, useLiveChart } from "./charts";
import { GROUP_COLORS, GROUP_ORDER, STATE_ORDER, attendanceIssue, downloadBase64, formatDate, readStore, rpcError, stepPeriod, writeStore } from "./common";
import { GroupDialog } from "./group_dialog";
import { useAttendanceLive } from "./live";
import { AttPager, PersonDialog } from "./parts";

/**
 * "Tổng quan chấm công" (ENTI-ATTENDANCE-002, ATTENDANCE-DASH-004). One scope (period, department, name/code)
 * drives three group cards — Đang làm, Đã về, Chưa đi làm (people, never punches, on one classification day) —
 * the donut, the daily trend, the compact newest-marks table and the detail table; the status filter only picks
 * the detail rows. A card opens the group list in a dialog (``GroupDialog``) with the same backend numbers.
 * Data come from one backend call (``tp_overview``); the server syncs the attendance source and wakes this screen
 * through the bus (``tp_hr_attendance/updated``), so new marks appear without F5, also in an open group dialog.
 * A slow fallback poll runs only while the tab is visible. Filters survive every automatic refresh; only changed
 * figures and new marks are highlighted.
 */
const STORE_KEY = "tp_hr_attendance.overview.v2";
const MODES = [["day", "Ngày"], ["week", "Tuần"], ["month", "Tháng"], ["range", "Khoảng ngày"]];
const HIGHLIGHT_MS = 2400;
const GROUP_CARDS = [
    { key: "working", icon: "login" },
    { key: "done", icon: "logout" },
    { key: "not_started", icon: "schedule" },
];

export class AttendanceDashboard extends Component {
    static template = "tp_hr_attendance.Dashboard";
    static components = { AttPager };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        const saved = readStore(STORE_KEY);
        const mode = MODES.some(([key]) => key === saved.mode) ? saved.mode : "day";
        const range = mode === "range" && saved.from && saved.to;
        this.state = proxy({
            mode: mode === "range" && !range ? "day" : mode, date: "", from: range ? saved.from : "", to: range ? saved.to : "",
            department: saved.department || "", search: saved.search || "", status: saved.status || "attention",
            page: 1, pageSize: saved.pageSize || 100,
            loading: true, refreshing: false, exporting: false, error: "", exportError: "", data: null, fresh: {},
        });
        this.modes = MODES;
        this.groupCards = GROUP_CARDS;
        this.groupDialogs = new Set();
        this.formatDate = formatDate;
        this.attendanceIssue = attendanceIssue;
        this.request = 0;
        this.timers = { search: null, highlight: null };
        this.donut = useLiveChart(() => this.donutSpec());
        this.trend = useLiveChart(() => this.trendSpec());
        this.lateChart = useLiveChart(() => this.lateSpec());
        this.autoRefresh = useAttendanceLive({ refresh: () => this.refresh(), relevant: (payload) => this.isRelevant(payload) });

        onWillStart(() => this.load());
        onWillUnmount(() => {
            browser.clearTimeout(this.timers.search);
            browser.clearTimeout(this.timers.highlight);
            this.closeGroup?.();
            this.request++; // Ignore any answer that arrives after leaving the screen.
        });
    }

    // ----------------------------------------------------------------- view data
    get data() {
        return this.state.data;
    }
    get kpis() {
        return this.state.data?.kpis;
    }
    get groups() {
        return this.state.data?.groups;
    }
    get heading() {
        const data = this.data;
        if (!data) {
            return "";
        }
        if (data.mode === "day") {
            return data.start === data.today ? `Hôm nay · ${data.period_label}` : data.period_label;
        }
        return data.mode === "week" ? `Tuần ${data.period_label} (T2–CN)` : data.period_label;
    }
    get statusOptions() {
        const data = this.data;
        const options = [["attention", "Cần kiểm tra / thiếu giờ"], ["all", "Tất cả"], ["late", "Có đi muộn"]];
        for (const key of STATE_ORDER) {
            if (data && (key !== "leave" || data.has_leave_source)) {
                options.push([key, data.labels[key]]);
            }
        }
        return options;
    }
    get statusTitle() {
        const found = this.statusOptions.find(([key]) => key === this.state.status);
        return found ? found[1] : "Danh sách";
    }
    get unit() {
        return this.data?.mode === "day" ? "người" : "nhân viên-ngày";
    }
    /** Donut legend: the groups of the classification day that have people ("Chưa xác định" in grey). */
    get legend() {
        const groups = this.groups;
        if (!groups?.total) {
            return [];
        }
        return GROUP_ORDER.filter((key) => key !== "unknown" || groups.counts.unknown).map((key) => ({
            key, label: groups.labels[key], value: groups.counts[key],
            percent: Math.round((groups.counts[key] * 1000) / groups.total) / 10,
        }));
    }
    get donutLabel() {
        const parts = this.legend.map((item) => `${item.label}: ${item.value} nhân viên (${item.percent}%)`);
        return [`Biểu đồ tình trạng ngày ${this.groups.date_label}, tổng ${this.groups.total} nhân viên`, ...parts].join(". ");
    }
    get unknownText() {
        const groups = this.groups;
        const reasons = Object.entries(groups?.reasons || {});
        // One reason: its label is enough (the count is already in front); several: label and count each.
        return reasons.map(([key, value]) => (reasons.length > 1 ? `${groups.reason_labels[key]}: ${value}` : groups.reason_labels[key]))
            .join(" · ");
    }
    get lateKnown() {
        return (this.data?.trend || []).some((day) => day.late_minutes !== null);
    }
    get hasFilters() {
        const state = this.state;
        return Boolean(state.department || state.search || state.status !== "attention" || state.mode !== "day" || state.date);
    }
    percent(value, total) {
        return total ? Math.round((value * 100) / total) : 0;
    }
    isFresh(key) {
        return Boolean(this.state.fresh[key]);
    }

    // -------------------------------------------------------------------- charts
    donutSpec() {
        const items = this.legend.filter((item) => item.value);
        if (!items.length) {
            return null;
        }
        return {
            type: "doughnut",
            data: {
                labels: items.map((item) => item.label),
                datasets: [{
                    data: items.map((item) => item.value),
                    backgroundColor: items.map((item) => GROUP_COLORS[item.key]),
                    borderColor: "#ffffff", borderWidth: 2, hoverOffset: 8,
                }],
            },
            options: baseOptions({
                cutout: "66%",
                layout: { padding: 8 },
                interaction: { mode: "nearest", intersect: true },
                onClick: (_event, elements) => elements.length && this.openGroup(items[elements[0].index].key),
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.label}: ${context.parsed} nhân viên (${items[context.dataIndex].percent}%)`,
                            footer: () => "Bấm để xem danh sách",
                        },
                    },
                },
            }),
        };
    }

    trendSpec() {
        const trend = this.data?.trend || [];
        if (!trend.length) {
            return null;
        }
        const dim = (color, day) => (this.data.mode === "day" && !day.selected ? `${color}59` : color);
        const labels = this.groups.labels;
        const series = ["working", "done", "not_started"].map((key) => [key, labels[key], GROUP_COLORS[key]]);
        return {
            type: "bar",
            data: {
                labels: trend.map((day) => `${day.weekday} ${day.label}`),
                datasets: series.map(([key, label, color]) => ({
                    label, key,
                    data: trend.map((day) => (day.future ? null : day.groups[key])),
                    backgroundColor: trend.map((day) => dim(color, day)),
                    borderRadius: 4, maxBarThickness: 18, categoryPercentage: 0.78, barPercentage: 0.9,
                })),
            },
            options: baseOptions({
                onClick: (_event, elements) => elements.length && this.openDay(trend[elements[0].index]),
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: CHART_COLORS.text, autoSkip: true, maxRotation: 0 } },
                    y: { beginAtZero: true, suggestedMax: Math.max(1, this.kpis?.people || 1),
                         ticks: { precision: 0, color: CHART_COLORS.muted }, grid: { color: CHART_COLORS.grid } },
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                const day = trend[items[0].dataIndex];
                                return `${day.weekday_full} ${formatDate(day.date)}`;
                            },
                            label: (context) => ` ${context.dataset.label}: ${context.parsed.y ?? "—"} nhân viên`,
                            footer: (items) => {
                                const day = trend[items[0].dataIndex];
                                if (day.future) {
                                    return "Chưa đến";
                                }
                                const unknown = day.groups.unknown ? `${labels.unknown}: ${day.groups.unknown} · ` : "";
                                return `${unknown}bấm để xem ngày này`;
                            },
                        },
                    },
                },
            }),
        };
    }

    lateSpec() {
        const trend = this.data?.trend || [];
        if (!trend.some((day) => day.late_minutes !== null)) {
            return null;
        }
        return {
            type: "bar",
            data: {
                labels: trend.map((day) => `${day.weekday} ${day.label}`),
                datasets: [{
                    label: "Tổng phút muộn",
                    data: trend.map((day) => day.late_minutes),
                    backgroundColor: trend.map((day) => (day.late_complete ? CHART_COLORS.warn : `${CHART_COLORS.warn}80`)),
                    borderRadius: 4, maxBarThickness: 22,
                }],
            },
            options: baseOptions({
                scales: {
                    x: { grid: { display: false }, ticks: { color: CHART_COLORS.text, autoSkip: true, maxRotation: 0 } },
                    y: { beginAtZero: true, ticks: { precision: 0, color: CHART_COLORS.muted }, grid: { color: CHART_COLORS.grid } },
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                const day = trend[items[0].dataIndex];
                                return `${day.weekday_full} ${formatDate(day.date)}`;
                            },
                            label: (context) => {
                                const day = trend[context.dataIndex];
                                return day.late_minutes === null ? " Chưa có số liệu đi muộn"
                                    : ` ${day.late_minutes} phút · ${day.late_people} người đi muộn`;
                            },
                            footer: (items) => {
                                const day = trend[items[0].dataIndex];
                                return day.late_minutes !== null && !day.late_complete ? "Một số người chưa có số liệu đi muộn" : "";
                            },
                        },
                    },
                },
            }),
        };
    }

    // ---------------------------------------------------------------- loading
    params() {
        const state = this.state;
        return {
            mode: state.mode, date: state.date, from: state.from, to: state.to,
            department_id: Number(state.department) || 0, search: state.search, status: state.status,
            page: state.page, page_size: state.pageSize,
        };
    }
    scopeKey(params) {
        const { page, page_size, status, ...scope } = params;
        return JSON.stringify(scope);
    }

    /** ``silent``: an automatic refresh — keep the screen as it is, then highlight only what changed. */
    async load({ silent = false } = {}) {
        const request = ++this.request;
        const params = this.params();
        this.state[silent ? "refreshing" : "loading"] = true;
        if (!silent) {
            this.state.error = "";
        }
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.day", "tp_overview", [params]);
            if (request !== this.request) {
                return;
            }
            const before = this.state.data;
            const sameScope = silent && before && this.loadedScope === this.scopeKey(params);
            this.loadedScope = this.scopeKey(params);
            this.autoRefresh.loaded();
            Object.assign(this.state, {
                data, date: data.date, status: data.status, page: data.page, pageSize: data.page_size, error: "",
            });
            if (data.mode === "range") {
                Object.assign(this.state, { from: data.start, to: data.end });
            }
            if (sameScope) {
                this.highlight(before, data);
            }
            if (silent) {
                for (const dialog of this.groupDialogs) {
                    dialog.refresh(); // An open group list follows the same automatic update.
                }
            }
            writeStore(STORE_KEY, {
                mode: data.mode, from: data.mode === "range" ? data.start : "", to: data.mode === "range" ? data.end : "",
                department: this.state.department, search: this.state.search, status: data.status, pageSize: data.page_size,
            });
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.error = rpcError(error, "Không tải được tổng quan chấm công. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
                this.state.refreshing = false;
                this.autoRefresh.flush(); // A notification that arrived during this load.
            }
        }
    }

    highlight(before, after) {
        const fresh = {};
        const seen = new Set((before.recent || []).map((row) => row.key));
        for (const row of after.recent || []) {
            if (!seen.has(row.key)) {
                fresh[row.key] = true;
            }
        }
        if (before.groups?.date === after.groups?.date) {
            for (const key of GROUP_ORDER) {
                if (before.groups.counts[key] !== after.groups.counts[key]) {
                    fresh[`group:${key}`] = true;
                }
            }
        }
        if (!Object.keys(fresh).length) {
            return;
        }
        this.state.fresh = fresh;
        browser.clearTimeout(this.timers.highlight);
        this.timers.highlight = browser.setTimeout(() => {
            this.state.fresh = {};
        }, HIGHLIGHT_MS);
    }

    /** Automatic refresh (bus / poll / tab shown): never while the user is loading or exporting something. */
    refresh() {
        if (this.state.loading || this.state.refreshing || this.state.exporting) {
            return false;
        }
        this.load({ silent: true });
    }

    /** A bus notification matters when it touches a shown day (period or trend) or changes the sync health. */
    isRelevant(payload) {
        const data = this.data;
        if (!data) {
            return false;
        }
        const trend = data.trend || [];
        const low = trend.length && trend[0].date < data.start ? trend[0].date : data.start;
        const high = trend.length && trend[trend.length - 1].date > data.end ? trend[trend.length - 1].date : data.end;
        const dates = payload.dates || [];
        return !dates.length || dates.some((day) => day >= low && day <= high)
            || Boolean(payload.health && payload.health !== data.source?.health);
    }

    // ---------------------------------------------------------------- filters
    reset(changes) {
        Object.assign(this.state, { page: 1 }, changes);
        return this.load();
    }
    setMode(mode) {
        if (mode === this.state.mode) {
            return;
        }
        if (mode === "range") {
            const data = this.data;
            return this.reset({ mode, from: data?.start || "", to: data?.end || "" });
        }
        return this.reset({ mode });
    }
    step(delta) {
        if (this.data) {
            return this.reset(stepPeriod(this.state.mode, this.data, delta));
        }
    }
    goToday() {
        return this.reset({ mode: this.state.mode === "range" ? "day" : this.state.mode, date: this.data?.today || "" });
    }
    onDate(ev) {
        if (ev.target.value) {
            return this.reset({ date: ev.target.value });
        }
    }
    onMonth(ev) {
        if (ev.target.value) {
            return this.reset({ date: `${ev.target.value}-01` });
        }
    }
    onRange(side, ev) {
        const value = ev.target.value;
        if (!value) {
            return;
        }
        const next = { from: this.state.from, to: this.state.to, [side]: value };
        if (next.from && next.to && next.to < next.from) {
            next[side === "from" ? "to" : "from"] = value;
        }
        return this.reset(next);
    }
    onDepartment(ev) {
        return this.reset({ department: ev.target.value });
    }
    onSearch(ev) {
        const value = ev.target.value;
        browser.clearTimeout(this.timers.search);
        this.timers.search = browser.setTimeout(() => this.reset({ search: value.trim() }), 300);
    }
    onStatus(ev) {
        return this.setStatus(ev.target.value);
    }
    setStatus(status) {
        return this.reset({ status });
    }
    clearFilters() {
        browser.clearTimeout(this.timers.search);
        return this.reset({ mode: "day", date: "", from: "", to: "", department: "", search: "", status: "attention" });
    }
    openDay(day) {
        if (day && !day.future) {
            return this.reset({ mode: "day", date: day.date });
        }
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    setSize(size) {
        return this.reset({ pageSize: size });
    }

    // ---------------------------------------------------------------- actions
    /** Scope of the group dialog: exactly what the dashboard shows (period, department, search, classification day). */
    groupScope() {
        const data = this.data;
        return {
            mode: data.mode, date: data.date, from: data.start, to: data.end,
            department_id: Number(this.state.department) || 0, search: this.state.search, class_date: data.groups.date,
        };
    }
    /** One group list at a time: opening another card replaces the open dialog (never a hidden combination). */
    openGroup(group) {
        if (!this.data?.groups) {
            return;
        }
        this.closeGroup?.();
        const groups = this.data.groups;
        const close = this.dialog.add(GroupDialog, {
            group, labels: groups.labels, counts: groups.counts, count: groups.counts[group], date: groups.date,
            scope: () => this.groupScope(),
            register: (dialog) => {
                this.groupDialogs.add(dialog);
                return () => this.groupDialogs.delete(dialog);
            },
        }, { onClose: () => {
            if (this.closeGroup === close) {
                this.closeGroup = null;
            }
        } });
        this.closeGroup = close;
    }
    openPerson(row) {
        this.dialog.add(PersonDialog, { params: { employee_id: row.employee_id, mode: "week", date: row.date } });
    }
    openBoard() {
        return this.action.doAction({ type: "ir.actions.client", tag: "tp_hr_attendance.board", name: "Bảng chấm công" });
    }
    async exportExcel() {
        if (this.state.exporting || !this.data) {
            return;
        }
        Object.assign(this.state, { exporting: true, exportError: "" });
        try {
            const data = this.data;
            const file = await this.orm.call("tp.hr.attendance.day", "tp_export_sheet", [{
                mode: data.mode, date: data.date, from: data.start, to: data.end,
                department_id: Number(this.state.department) || 0, search: this.state.search,
            }]);
            downloadBase64(file);
        } catch (error) {
            // Shown above the filters, next to the button the user pressed (no toast).
            this.state.exportError = rpcError(error, "Không xuất được Excel. Dữ liệu trên màn hình không thay đổi; vui lòng thử lại.");
        } finally {
            this.state.exporting = false;
            this.autoRefresh.flush();
        }
    }
}

registry.category("actions").add("tp_hr_attendance.dashboard", AttendanceDashboard);
