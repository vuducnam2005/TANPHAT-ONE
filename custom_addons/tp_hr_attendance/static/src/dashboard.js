import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { STATE_COLORS, STATE_ORDER, TOTAL_COLOR, cellNote, formatDate, readStore, rpcError, stepPeriod, writeStore } from "./common";
import { AttPager, PersonDialog, SourceStrip } from "./parts";
import { openAttendanceUpload } from "./upload/upload";

/**
 * "Tổng quan chấm công" (HR-ATTENDANCE-SIMPLE-002). One scope (company, department, period) drives the three
 * KPIs, the chips, the chart and the drill list: day → one main state per person (donut, denominator = active
 * employees); week (Mon–Sun) / month → distinct people and daily bars. Starts at the real today.
 */
const STORE_KEY = "tp_hr_attendance.overview";
const MODES = [["day", "Ngày"], ["week", "Tuần"], ["month", "Tháng"]];
const RADIUS = 70;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export class AttendanceDashboard extends Component {
    static template = "tp_hr_attendance.Dashboard";
    static components = { AttPager, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        const saved = readStore(STORE_KEY);
        this.state = proxy({
            mode: ["day", "week", "month"].includes(saved.mode) ? saved.mode : "day", date: "",
            department: saved.department || "", search: "", drill: "", drillDate: "", page: 1, pageSize: saved.pageSize || 20,
            loading: true, error: "", data: null,
        });
        this.modes = MODES;
        this.colors = STATE_COLORS;
        this.totalColor = TOTAL_COLOR;
        this.cellNote = cellNote;
        this.formatDate = formatDate;
        this.request = 0;
        this.searchTimer = null;
        onWillStart(() => this.load());
    }

    get data() {
        return this.state.data;
    }
    get isDay() {
        return this.data?.mode === "day";
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
    get showLatest() {
        const data = this.data;
        return Boolean(data?.source.latest_date) && !(data.mode === "day" && data.start === data.source.latest_date);
    }
    /** SVG donut arcs; the denominator is the employee total (each person has exactly one state that day). */
    get donut() {
        const data = this.data;
        const total = data?.kpis.total || 0;
        let offset = 0;
        return (data?.donut || []).map((slice) => {
            const length = total ? (slice.value / total) * CIRCUMFERENCE : 0;
            const arc = { ...slice, color: STATE_COLORS[slice.key], dash: `${length} ${CIRCUMFERENCE - length}`, offset: -offset,
                percent: total ? Math.round((slice.value / total) * 100) : 0 };
            offset += length;
            return arc;
        });
    }
    get legendStates() {
        const data = this.data;
        return data ? STATE_ORDER.filter((key) => key !== "leave" || data.has_leave_source).map((key) => ({ key, label: data.labels[key], color: STATE_COLORS[key] })) : [];
    }
    get bars() {
        const data = this.data;
        const max = Math.max(1, data?.kpis.total || 0);
        return (data?.daily || []).map((day) => {
            const segments = STATE_ORDER.filter((key) => day.counts[key]).map((key) => ({
                key, value: day.counts[key], color: STATE_COLORS[key], height: (day.counts[key] / max) * 100, label: data.labels[key],
            }));
            const title = day.future ? `${day.weekday} ${formatDate(day.date)}: chưa đến`
                : `${day.weekday} ${formatDate(day.date)}: ` + segments.map((seg) => `${seg.label} ${seg.value}`).join(", ");
            return { ...day, segments, title };
        });
    }
    get drillTitle() {
        const data = this.data;
        if (!data) {
            return "";
        }
        const names = { all: "Tất cả nhân viên", attention: "Cần kiểm tra / thiếu giờ" };
        const base = names[data.drill] || data.labels[data.drill] || "Danh sách";
        return data.drill_date ? `${base} · ngày ${formatDate(data.drill_date)}` : base;
    }

    params() {
        return {
            mode: this.state.mode, date: this.state.date, department_id: Number(this.state.department) || 0, search: this.state.search,
            drill: this.state.drill, drill_date: this.state.drillDate, page: this.state.page, page_size: this.state.pageSize,
        };
    }

    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_overview", [this.params()]);
            if (request !== this.request) {
                return;
            }
            Object.assign(this.state, { data, date: data.date, drill: data.drill, page: data.page, pageSize: data.page_size });
            writeStore(STORE_KEY, { mode: data.mode, department: this.state.department, pageSize: data.page_size });
        } catch (error) {
            if (request === this.request) {
                this.state.error = rpcError(error, "Không tải được tổng quan chấm công. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
            }
        }
    }

    reset(changes) {
        Object.assign(this.state, { page: 1 }, changes);
        return this.load();
    }
    setMode(mode) {
        return this.reset({ mode, drill: "", drillDate: "" });
    }
    step(delta) {
        return this.reset({ ...stepPeriod(this.state.mode, this.data, delta), drillDate: "" });
    }
    goToday() {
        return this.reset({ date: this.data?.today || "", drillDate: "" });
    }
    goLatest() {
        return this.reset({ mode: "day", date: this.data.source.latest_date, drill: "", drillDate: "" });
    }
    onDate(ev) {
        if (ev.target.value) {
            return this.reset({ date: ev.target.value, drillDate: "" });
        }
    }
    onMonth(ev) {
        if (ev.target.value) {
            return this.reset({ date: `${ev.target.value}-01`, drillDate: "" });
        }
    }
    onDepartment(ev) {
        return this.reset({ department: ev.target.value });
    }
    onSearch(ev) {
        const value = ev.target.value;
        browser.clearTimeout(this.searchTimer);
        this.searchTimer = browser.setTimeout(() => this.reset({ search: value.trim() }), 300);
    }
    drillTo(drill, drillDate = "") {
        return this.reset({ drill, drillDate });
    }
    openDay(day) {
        if (!day.future) {
            return this.drillTo("all", day.date);
        }
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    setSize(size) {
        return this.reset({ pageSize: size });
    }
    openPerson(row) {
        this.dialog.add(PersonDialog, { params: { employee_id: row.employee_id, mode: "week", date: row.date } });
    }
    openBoard(period) {
        const params = period ? { from: period.from, to: period.to } : {};
        return this.action.doAction({ type: "ir.actions.client", tag: "tp_hr_attendance.board", name: "Bảng chấm công", params });
    }
    openSources() {
        return this.action.doAction("tp_hr_attendance.action_sources");
    }
    openUpload() {
        openAttendanceUpload(this.env, { onApplied: () => this.load(), onOpenPeriod: (period) => this.openBoard(period) });
    }
}

registry.category("actions").add("tp_hr_attendance.dashboard", AttendanceDashboard);
