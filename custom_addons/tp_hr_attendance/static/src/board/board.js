import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { cellNote, downloadBase64, formatDate, lateText, readStore, stepPeriod, writeStore } from "../common";
import { useAttendanceLive } from "../live";
import { AttPager, LateDialog, PersonDialog, SourceStrip } from "../parts";

const STORE_KEY = "tp_hr_attendance.sheet";
const MODES = [["day", "Ngày"], ["week", "Tuần"], ["month", "Tháng"]];
const DAY_STATES = [
    ["", "Tất cả tình trạng"],
    ["attention", "Cần kiểm tra / thiếu giờ"],
    ["out_recorded", "Đủ vào/ra"],
    ["working", "Đang làm"],
    ["missing", "Thiếu giờ vào/ra"],
    ["review", "Cần kiểm tra"],
    ["absent", "Vắng theo lịch"],
    ["leave", "Nghỉ đã xác nhận"],
    ["no_punch", "Chưa chấm công"],
    ["rest", "Nghỉ theo lịch"],
    ["no_source", "Chưa có dữ liệu"],
];

export class AttendanceBoard extends Component {
    static template = "tp_hr_attendance.Board";
    static components = { AttPager, InlineErrors, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        const saved = readStore(STORE_KEY);
        const params = this.props.action?.params || {};
        const period = params.from && params.to ? { mode: "range", from: params.from, to: params.to } : {};
        const initDept = saved.department || "";
        this.state = proxy({
            mode: ["day", "week", "month"].includes(saved.mode) ? saved.mode : "day",
            date: "",
            from: "",
            to: "",
            draftDepartment: initDept,
            draftSearch: "",
            draftState: "",
            department: initDept,
            search: "",
            dayState: "",
            page: 1,
            pageSize: saved.pageSize || 100,
            mobileFilterOpen: false,
            mobileView: "cards",
            ...period,
            loading: true,
            exporting: false,
            serverError: null,
            attempt: 0,
            data: null,
        });
        this.modes = MODES;
        this.cellNote = cellNote;
        this.formatDate = formatDate;
        this.lateText = lateText;
        this.request = 0;
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
            this.request++;
        });
    }

    get data() {
        return this.state.data;
    }
    get dayStates() {
        const hasLeave = Boolean(this.data?.has_leave_source);
        return DAY_STATES.filter(([key]) => key !== "leave" || hasLeave);
    }
    get hasPendingFilterDiff() {
        return (
            String(this.state.draftDepartment || "") !== String(this.state.department || "") ||
            this.state.draftSearch.trim() !== this.state.search ||
            this.state.draftState !== this.state.dayState
        );
    }
    get appliedChips() {
        const chips = [];
        if (this.state.department) {
            const dept = (this.data?.departments || []).find((d) => String(d.id) === String(this.state.department));
            chips.push({ key: "department", label: `Phòng: ${dept ? dept.name : this.state.department}` });
        }
        if (this.state.search) {
            chips.push({ key: "search", label: `Tìm: ${this.state.search}` });
        }
        if (this.state.dayState) {
            const st = DAY_STATES.find(([k]) => k === this.state.dayState);
            chips.push({ key: "state", label: `Tình trạng: ${st ? st[1] : this.state.dayState}` });
        }
        return chips;
    }
    get groups() {
        const groups = new Map();
        for (const row of this.data?.rows || []) {
            const key = row.department_id || 0;
            if (!groups.has(key)) {
                groups.set(key, { id: key, name: row.department || "Chưa có phòng ban", rows: [] });
            }
            groups.get(key).rows.push(row);
        }
        return [...groups.values()];
    }
    cellTitle(cell) {
        const base = `${this.formatDate(cell.date)} · ${cell.label || ""}`;
        const note = cell.conflict_note || cell.leave_note || "";
        return note ? `${base} · ${note}` : base;
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
            mode: this.state.mode,
            date: this.state.date,
            from: this.state.from,
            to: this.state.to,
            department_id: Number(this.state.department) || 0,
            search: this.state.search,
            state: this.state.dayState,
            page: this.state.page,
            page_size: this.state.pageSize,
        };
    }

    /** ``silent``: automatic refresh — no loading indicator, and a failure keeps the rows already shown. */
    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state.loading = true;
        if (!silent) {
            this.state.serverError = null;
        }
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.day", "tp_sheet", [this.params()]);
            if (request !== this.request) {
                return;
            }
            Object.assign(this.state, { data, date: data.date, page: data.page, pageSize: data.page_size, serverError: null });
            if (data.mode === "range") {
                Object.assign(this.state, { from: data.start, to: data.end });
            }
            writeStore(STORE_KEY, { mode: data.mode === "range" ? "day" : data.mode, department: this.state.department, pageSize: data.page_size });
            this.live.loaded();
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.serverError = saveError(error, { verb: "tải bảng chấm công" });
                this.state.attempt++;
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
        return this.reset({ mode, date: anchor || "" });
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
    openRange() {
        if (this.state.mode === "range") {
            return;
        }
        const from = this.data?.start || this.state.date;
        return this.reset({ mode: "range", from, to: this.data?.end || from });
    }
    openFilePeriod(item) {
        return this.reset({ mode: "range", from: item.from, to: item.to });
    }
    applyFilters() {
        return this.reset({
            department: this.state.draftDepartment,
            search: this.state.draftSearch.trim(),
            dayState: this.state.draftState,
            mobileFilterOpen: false,
        });
    }
    onFilterKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.applyFilters();
        } else if (ev.key === "Escape" && this.state.mobileFilterOpen) {
            this.state.mobileFilterOpen = false;
        }
    }
    removeChip(key) {
        if (key === "department") {
            Object.assign(this.state, { draftDepartment: "", department: "" });
        } else if (key === "search") {
            Object.assign(this.state, { draftSearch: "", search: "" });
        } else if (key === "state") {
            Object.assign(this.state, { draftState: "", dayState: "" });
        }
        this.state.page = 1;
        return this.load();
    }
    clearFilters() {
        return this.reset({
            draftDepartment: "",
            draftSearch: "",
            draftState: "",
            department: "",
            search: "",
            dayState: "",
            mobileFilterOpen: false,
        });
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
        if (this.state.exporting || !this.data) {
            return;
        }
        this.state.exporting = true;
        this.state.serverError = null;
        try {
            downloadBase64(await this.orm.call("tp.hr.attendance.day", "tp_export_sheet", [this.params()]));
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "xuất bảng chấm công" });
            this.state.attempt++;
        } finally {
            this.state.exporting = false;
            this.live.flush();
        }
    }
}

registry.category("actions").add("tp_hr_attendance.board", AttendanceBoard);
