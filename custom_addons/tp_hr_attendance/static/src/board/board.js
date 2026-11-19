import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { cellNote, downloadBase64, formatDate, readStore, rpcError, stepPeriod, writeStore } from "../common";
import { useAttendanceLive } from "../live";
import { AttPager, LateDialog, PeriodTable, PersonDialog, SourceStrip } from "../parts";

/**
 * "Bảng chấm công" (HR-ATTENDANCE-SIMPLE-002). Day: Nhân viên · Phòng ban · Thứ/ngày · Giờ vào · Giờ ra.
 * Week / month / free range ("Khoảng ngày"): Nhân viên · Phòng ban · Số lần đi muộn · Tổng phút muộn (ENTI late
 * minutes, or an exact historical Excel period). Always canonical data: tp.hr.attendance.day.tp_sheet (record rules
 * apply); Excel file import is closed (ENTI-ATTENDANCE-002) and old Excel periods stay reachable as history links.
 * Mode, department and page size survive the breadcrumb round-trip; the date always starts at today.
 */
const STORE_KEY = "tp_hr_attendance.sheet";
const MODES = [["day", "Ngày"], ["week", "Tuần"], ["month", "Tháng"]];
const DAY_STATES = [
    ["", "Tất cả"], ["attention", "Cần kiểm tra / thiếu giờ"], ["out_recorded", "Đã ghi nhận ra"], ["working", "Đang làm"],
    ["missing", "Thiếu giờ vào/ra"], ["review", "Cần kiểm tra"], ["no_punch", "Chưa chấm công"], ["no_source", "Chưa có dữ liệu"],
];

export class AttendanceBoard extends Component {
    static template = "tp_hr_attendance.Board";
    static components = { AttPager, PeriodTable, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        const saved = readStore(STORE_KEY);
        const params = this.props.action?.params || {};
        const period = params.from && params.to ? { mode: "range", from: params.from, to: params.to } : {};
        this.state = proxy({
            mode: ["day", "week", "month"].includes(saved.mode) ? saved.mode : "day", date: "", from: "", to: "",
            department: saved.department || "", search: "", dayState: "", page: 1, pageSize: saved.pageSize || 20,
            ...period, loading: true, error: "", data: null,
        });
        this.modes = MODES;
        this.dayStates = DAY_STATES;
        this.cellNote = cellNote;
        this.formatDate = formatDate;
        this.request = 0;
        this.searchTimer = null;
        // ENTI-ATTENDANCE-002: new punches appear without F5 (server bus notification, visible-tab fallback poll).
        this.live = useAttendanceLive({
            refresh: () => (this.state.loading || this.state.exporting ? false : this.load({ silent: true })),
            relevant: (payload) => {
                const data = this.data;
                const dates = payload.dates || [];
                return Boolean(data) && (!dates.length || dates.some((day) => day >= data.start && day <= data.end));
            },
        });

        onWillStart(() => this.load());
        onWillUnmount(() => {
            browser.clearTimeout(this.searchTimer);
            this.request++;
        });
    }

    get data() {
        return this.state.data;
    }
    /** Follows the loaded data, so a mode switch never renders day rows in the period table (or back). */
    get isDay() {
        return (this.data ? this.data.mode : this.state.mode) === "day";
    }
    /** File periods that contain the viewed day (the source of its machine late total). */
    get dayPeriods() {
        const data = this.data;
        return data && this.isDay ? data.file_periods.filter((item) => item.has_late && item.from <= data.start && data.start <= item.to) : [];
    }
    /** File periods overlapping a non-matching range: offered as exact views instead of a guessed total. */
    get overlapPeriods() {
        const data = this.data;
        if (!data || this.isDay || data.is_file_period) {
            return [];
        }
        return data.file_periods.filter((item) => item.from <= data.end && item.to >= data.start).slice(0, 4);
    }
    get title() {
        const data = this.data;
        if (!data) {
            return "";
        }
        if (this.isDay) {
            return data.start === data.today ? `Hôm nay · ${data.period_label}` : data.period_label;
        }
        return data.is_file_period ? `Kỳ nguồn Excel (lịch sử) ${data.period_label}` : data.period_label;
    }

    params() {
        return {
            mode: this.state.mode, date: this.state.date, from: this.state.from, to: this.state.to,
            department_id: Number(this.state.department) || 0, search: this.state.search,
            state: this.isDay ? this.state.dayState : "", page: this.state.page, page_size: this.state.pageSize,
        };
    }

    /** ``silent``: automatic refresh — no loading indicator, and a failure keeps the rows already shown. */
    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state.loading = true;
        if (!silent) {
            this.state.error = "";
        }
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.day", "tp_sheet", [this.params()]);
            if (request !== this.request) {
                return;
            }
            Object.assign(this.state, { data, date: data.date, page: data.page, pageSize: data.page_size });
            if (data.mode === "range") {
                Object.assign(this.state, { from: data.start, to: data.end });
            }
            writeStore(STORE_KEY, { mode: data.mode === "range" ? "day" : data.mode, department: this.state.department, pageSize: data.page_size });
            this.state.error = "";
            this.live.loaded();
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.error = rpcError(error, "Không tải được bảng chấm công. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
                this.live.flush();
            }
        }
    }

    reset(changes) {
        Object.assign(this.state, { page: 1 }, changes);
        return this.load();
    }
    setMode(mode) {
        const anchor = this.state.mode === "range" ? this.state.from : this.state.date;
        return this.reset({ mode, date: anchor || "", dayState: "" });
    }
    step(delta) {
        return this.reset(stepPeriod(this.state.mode, this.data, delta));
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
    onRange(key, ev) {
        const value = ev.target.value;
        if (!value) {
            return;
        }
        const changes = { [key]: value };
        const from = key === "from" ? value : this.state.from;
        const to = key === "to" ? value : this.state.to;
        if (to < from) {
            changes[key === "from" ? "to" : "from"] = value;
        }
        return this.reset(changes);
    }
    /** Free date range (ENTI-ATTENDANCE-002 replaced the former "Kỳ theo file" picker); starts from the viewed period. */
    openRange() {
        if (this.state.mode === "range") {
            return;
        }
        const from = this.data?.start || this.state.date;
        return this.reset({ mode: "range", from, to: this.data?.end || from });
    }
    /** Historical machine late total of an old Excel period (read-only history). */
    openFilePeriod(item) {
        return this.reset({ mode: "range", from: item.from, to: item.to });
    }
    onDepartment(ev) {
        return this.reset({ department: ev.target.value });
    }
    onDayState(ev) {
        return this.reset({ dayState: ev.target.value });
    }
    onSearch(ev) {
        const value = ev.target.value;
        browser.clearTimeout(this.searchTimer);
        this.searchTimer = browser.setTimeout(() => this.reset({ search: value.trim() }), 300);
    }
    clearFilters() {
        return this.reset({ department: "", search: "", dayState: "" });
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    setSize(size) {
        return this.reset({ pageSize: size });
    }

    openPerson(row) {
        const params = this.isDay
            ? { employee_id: row.id, mode: "day", date: this.data.start }
            : { employee_id: row.id, mode: "range", from: this.data.start, to: this.data.end };
        this.dialog.add(PersonDialog, { params });
    }
    openLate(item) {
        this.dialog.add(LateDialog, {
            label: item.label, params: { from: item.from, to: item.to, department_id: Number(this.state.department) || 0, search: this.state.search },
        });
    }
    openSources() {
        return this.action.doAction("tp_hr_attendance.action_sources");
    }
    async exportSheet() {
        try {
            downloadBase64(await this.orm.call("tp.hr.attendance.day", "tp_export_sheet", [this.params()]));
        } catch (error) {
            this.state.error = rpcError(error, "Không xuất được bảng chấm công. Vui lòng thử lại.");
        }
    }
}

registry.category("actions").add("tp_hr_attendance.board", AttendanceBoard);
