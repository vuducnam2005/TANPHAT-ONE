import { Component, onWillStart, proxy, usePlugin } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { UIPlugin } from "@web/core/ui/ui_plugin";
import { useService } from "@web/core/utils/hooks";

/**
 * Shared attendance board (HR-ATTENDANCE-001). Read-only for everybody: data comes from
 * tp.hr.attendance.day.tp_board (record rules apply), cells open the read-only day form.
 * Filter, page and mode survive the breadcrumb round-trip through sessionStorage.
 */
export const STATE_ORDER = ["ok", "missing", "review", "no_punch", "no_source", "future"];
export const PAGE_SIZES = [10, 20, 50, 100];
const STORE_KEY = "tp_hr_attendance.board";
const DEFAULTS = { mode: "", month: "", date: "", department: "", search: "", state: "", lock: "", batch: "", page: 1, pageSize: 20 };

export function readStore(key) {
    try {
        return JSON.parse(browser.sessionStorage.getItem(key) || "{}") || {};
    } catch {
        return {}; // Private window / blocked storage: start from defaults.
    }
}

export function writeStore(key, value) {
    try {
        browser.sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
        // Storage unavailable: the board still works, it just forgets the filters.
    }
}

export function shiftMonth(month, delta) {
    const [year, number] = month.split("-").map(Number);
    const value = new Date(Date.UTC(year, number - 1 + delta, 1));
    return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, "0")}`;
}

export function shiftDate(iso, delta) {
    const value = new Date(`${iso}T00:00:00Z`);
    value.setUTCDate(value.getUTCDate() + delta);
    return value.toISOString().slice(0, 10);
}

export function formatDate(iso) {
    return iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : "";
}

export function formatHours(value) {
    if (!value) {
        return "0:00";
    }
    const minutes = Math.round(value * 60);
    return `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, "0")}`;
}

export class AttendanceBoard extends Component {
    static template = "tp_hr_attendance.Board";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ui = usePlugin(UIPlugin);
        this.storeKey = `${STORE_KEY}:${this.mobile ? "m" : "d"}`;
        const saved = readStore(this.storeKey);
        this.state = proxy({ ...DEFAULTS, ...saved, loading: true, error: "", data: null });
        if (!this.state.mode) {
            this.state.mode = this.mobile ? "day" : "month";
        }
        this.request = 0;
        this.searchTimer = null;
        this.formatDate = formatDate;
        this.formatHours = formatHours;
        onWillStart(() => this.load());
    }

    get mobile() {
        return this.ui.size() <= 1;
    }
    get data() {
        return this.state.data;
    }
    get legend() {
        const data = this.data;
        return data ? STATE_ORDER.map((key) => ({ key, label: data.labels[key], count: data.counts[key] || 0 })) : [];
    }
    get chips() {
        const data = this.data;
        if (!data) {
            return [];
        }
        const chips = [];
        if (this.state.department) {
            const dept = data.departments.find((row) => String(row.id) === String(this.state.department));
            chips.push({ key: "department", label: `Phòng: ${dept ? dept.name : this.state.department}` });
        }
        if (this.state.search) {
            chips.push({ key: "search", label: `Tìm: ${this.state.search}` });
        }
        if (this.state.state) {
            chips.push({ key: "state", label: `Tình trạng: ${data.labels[this.state.state] || this.state.state}` });
        }
        if (this.state.lock) {
            chips.push({ key: "lock", label: this.state.lock === "locked" ? "Kỳ đã chốt" : "Kỳ đang mở" });
        }
        if (this.state.batch) {
            const batch = data.batches.find((row) => String(row.id) === String(this.state.batch));
            chips.push({ key: "batch", label: `Lô: ${batch ? batch.name : this.state.batch}` });
        }
        return chips;
    }
    get periodLabel() {
        const data = this.data;
        if (!data) {
            return "";
        }
        if (data.mode === "day") {
            const day = data.dates[0];
            return `${day.weekday}, ${formatDate(day.date)}`;
        }
        return `Tháng ${data.month.slice(5, 7)}/${data.month.slice(0, 4)}`;
    }
    get rangeText() {
        const data = this.data;
        if (!data || !data.total) {
            return "0 nhân viên";
        }
        const first = (data.page - 1) * data.page_size + 1;
        const last = Math.min(data.total, data.page * data.page_size);
        return `${first}–${last} / ${data.total} nhân viên`;
    }

    params() {
        return {
            mode: this.state.mode, month: this.state.month, date: this.state.date,
            department_id: Number(this.state.department) || 0, search: this.state.search,
            state: this.state.state, lock: this.state.lock, batch_id: Number(this.state.batch) || 0,
            page: this.state.page, page_size: this.state.pageSize,
        };
    }

    persist() {
        const value = {};
        for (const key of Object.keys(DEFAULTS)) {
            value[key] = this.state[key];
        }
        writeStore(this.storeKey, value);
    }

    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_board", [this.params()]);
            if (request !== this.request) {
                return;
            }
            this.state.data = data;
            this.state.month = data.month;
            this.state.date = data.mode === "day" ? data.date : this.state.date;
            this.state.page = data.page;
            this.state.pageSize = data.page_size;
            if (this.state.batch && !data.batches.some((row) => String(row.id) === String(this.state.batch))) {
                this.state.batch = "";
            }
            this.persist();
        } catch (error) {
            if (request !== this.request) {
                return;
            }
            if (/SessionExpired/.test(error.data?.name || error.name || "")) {
                throw error;
            }
            this.state.error = /AccessError/.test(error.data?.name || "")
                ? "Bạn không có quyền xem bảng công của công ty đang chọn."
                : error.data?.message || "Không tải được bảng công. Vui lòng thử lại.";
        } finally {
            if (request === this.request) {
                this.state.loading = false;
            }
        }
    }

    setFilter(key, value) {
        this.state[key] = value;
        this.state.page = 1;
        return this.load();
    }
    onSelect(ev, key) {
        return this.setFilter(key, ev.target.value);
    }
    onSearch(ev) {
        const value = ev.target.value;
        browser.clearTimeout(this.searchTimer);
        this.searchTimer = browser.setTimeout(() => this.setFilter("search", value.trim()), 300);
    }
    removeChip(key) {
        return this.setFilter(key, "");
    }
    clearFilters() {
        Object.assign(this.state, { department: "", search: "", state: "", lock: "", batch: "", page: 1 });
        return this.load();
    }
    toggleState(key) {
        return this.setFilter("state", this.state.state === key ? "" : key);
    }
    setMode(mode) {
        if (mode === this.state.mode) {
            return;
        }
        this.state.mode = mode;
        if (mode === "day" && !this.state.date && this.data) {
            this.state.date = this.data.anchor;
        }
        this.state.page = 1;
        return this.load();
    }
    onMonth(ev) {
        if (ev.target.value) {
            return this.setFilter("month", ev.target.value);
        }
    }
    onDate(ev) {
        if (ev.target.value) {
            return this.setFilter("date", ev.target.value);
        }
    }
    step(delta) {
        if (this.state.mode === "day") {
            this.state.date = shiftDate(this.state.date || this.data?.anchor || this.data?.today, delta);
        } else {
            this.state.month = shiftMonth(this.state.month || this.data.month, delta);
        }
        this.state.page = 1;
        return this.load();
    }
    goToday() {
        Object.assign(this.state, { month: "", date: "", page: 1 });
        return this.load();
    }
    openDayColumn(day) {
        this.state.mode = "day";
        this.state.date = day.date;
        this.state.page = 1;
        return this.load();
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    onPageSize(ev) {
        this.state.pageSize = Number(ev.target.value);
        this.state.page = 1;
        return this.load();
    }
    openCell(cell) {
        if (!cell.day_id) {
            return;
        }
        this.persist();
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Ngày công",
            res_model: "tp.hr.attendance.day",
            res_id: cell.day_id,
            views: [[false, "form"]],
            target: "current",
        });
    }
    openImport() {
        this.persist();
        return this.action.doAction("tp_hr_attendance.action_import");
    }
    cellTitle(row, cell) {
        const parts = [`${row.name} · ${formatDate(cell.date)}`, cell.label];
        if (cell.in_time || cell.out_time) {
            parts.push(`Vào ${cell.in_time || "—"} · Ra ${cell.out_time || "—"}`);
        }
        if (cell.day_id) {
            parts.push(`Giờ ghi nhận ${formatHours(cell.hours)} · Công ${cell.units}`);
        }
        if (cell.lock === "locked") {
            parts.push("Kỳ đã chốt");
        }
        return parts.join("\n");
    }
}

registry.category("actions").add("tp_hr_attendance.board", AttendanceBoard);
