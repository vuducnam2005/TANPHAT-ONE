import { Component, onWillStart, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatDate, formatHours, readStore, shiftMonth, writeStore } from "./board/board";

const COLORS = { ok: "#1e8a4c", missing: "#e49a01", review: "#b42318", no_punch: "#6b7a8a", no_source: "#b8c6d0" };

export class AttendanceDashboard extends Component {
    static template = "tp_hr_attendance.Dashboard";
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const saved = readStore("tp_att_dashboard");
        delete saved.search; // Search terms stay in memory, never persisted across sessions.
        writeStore("tp_att_dashboard", saved);
        this.state = proxy({month: "", department_id: "", search: "", detail_state: "attention", detail_date: "", lock: "", page: 1, page_size: 20, ...saved, data: null, loading: true, error: ""});
        this.draft = proxy({month: saved.month || "", department_id: saved.department_id || "", search: saved.search || ""});
        this.formatDate = formatDate;
        this.formatHours = formatHours;
        this.request = 0;
        onWillStart(() => this.load());
    }
    get data() { return this.state.data; }
    get legend() { return Object.keys(COLORS).map(key => ({key, label: this.data.labels[key], count: this.data.counts[key], color: COLORS[key]})); }
    get donutStyle() {
        let angle = 0;
        const segments = this.legend.map(item => {
            const start = angle;
            angle += this.data.total ? item.count / this.data.total * 100 : 0;
            return item.color + " " + start + "% " + angle + "%";
        });
        return "conic-gradient(" + segments.join(",") + ")";
    }
    get dailyMax() { return Math.max(1, ...this.data.daily.map(row => Object.values(row.counts).reduce((a,b) => a+b, 0))); }
    params() {
        const result = {};
        for (const key of ["month", "department_id", "search", "detail_state", "detail_date", "lock", "page", "page_size"]) result[key] = this.state[key];
        return result;
    }
    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_dashboard", [this.params()]);
            if (request !== this.request) return;
            this.state.data = data;
            this.state.month = data.month;
            if (!this.draft.month) this.draft.month = data.month;
            this.state.page = data.page;
            const {search, ...stored} = this.params();
            writeStore("tp_att_dashboard", stored);
        } catch (error) {
            if (request !== this.request) return;
            if (/SessionExpired/.test(error.data?.name || error.name || "")) throw error;
            this.state.error = error.data?.message || "Không tải được tổng quan công. Vui lòng thử lại.";
        } finally { if (request === this.request) this.state.loading = false; }
    }
    filter(key, value) { this.state[key] = value; this.state.page = 1; return this.load(); }
    apply() { Object.assign(this.state, this.draft, {page: 1, detail_date: ""}); return this.load(); }
    clear() { Object.assign(this.draft, {month: this.data?.month || this.state.month || this.draft.month, department_id: "", search: ""}); Object.assign(this.state, this.draft, {detail_state: "attention", detail_date: "", lock: "", page: 1}); return this.load(); }
    get chips() {
        const chips = [];
        if (this.state.month) chips.push({key: "month", label: "Kỳ: " + this.state.month});
        if (this.state.department_id) chips.push({key: "department_id", label: "Phòng: " + (this.data?.departments.find(dept => String(dept.id) === String(this.state.department_id))?.name || this.state.department_id)});
        if (this.state.search) chips.push({key: "search", label: "Nhân viên / mã TP: " + this.state.search});
        return chips;
    }
    removeChip(key) {
        this.draft[key] = "";
        this.state[key] = "";
        this.state.page = 1;
        if (key === "month") this.state.detail_date = "";
        return this.load();
    }
    step(delta) { return this.filter("month", shiftMonth(this.state.month, delta)); }
    clearDetail() { this.state.detail_date = ""; this.state.lock = ""; return this.filter("detail_state", "all"); }
    previousPage() { this.state.page--; return this.load(); }
    nextPage() { this.state.page++; return this.load(); }
    focusDate(day) { this.state.detail_state = "all"; return this.filter("detail_date", day); }
    open(row) {
        if (!row.day_id) return;
        return this.action.doAction({type: "ir.actions.act_window", res_model: "tp.hr.attendance.day", res_id: row.day_id, views: [[false, "form"]], name: "Ngày công"});
    }
}
registry.category("actions").add("tp_hr_attendance.dashboard", AttendanceDashboard);
