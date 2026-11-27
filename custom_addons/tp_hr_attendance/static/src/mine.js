import { Component, onMounted, onWillStart, onWillUnmount, proxy, signal, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { HrListController } from "@tp_hr_workspace/table/table";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";
import { TpTime24Field } from "@tp_web_home/inputs/time24";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import {
    PAGE_SIZES,
    downloadBase64,
    formatHours,
    mineStatusInfo,
    readStore,
    rpcError,
    stepPeriod,
    writeStore,
} from "./common";
import { useAttendanceLive } from "./live";
import { AttPager, SourceStrip } from "./parts";

/**
 * "Công của tôi" (HR-ATTENDANCE-MINE-UI-001).
 * The employee is always resolved on the backend from the session user (tp_mine / tp_export_mine ignore any client id).
 * Supports standalone menu and compact embedded tab inside "Thông tin cá nhân".
 */
const STORE_KEY = "tp_hr_attendance.mine.v2";
const MODES = [
    ["week", "Tuần"],
    ["month", "Tháng"],
];
const STATE_OPTIONS = [
    ["", "Tất cả tình trạng"],
    ["out_recorded", "Đủ vào/ra"],
    ["working", "Chờ ghi nhận giờ ra"],
    ["attention", "Thiếu giờ / Cần kiểm tra"],
    ["missing_in", "Thiếu giờ vào"],
    ["missing_out", "Thiếu giờ ra"],
    ["review", "Cần kiểm tra"],
    ["absent", "Vắng theo lịch"],
    ["no_punch", "Chưa chấm công"],
    ["rest", "Nghỉ theo lịch"],
    ["no_source", "Chưa có dữ liệu"],
    ["leave", "Nghỉ đã xác nhận"],
    ["future", "Ngày tương lai"],
];
const MAX_EVIDENCE_BYTES = 10 * 1024 * 1024;
const WEEKDAY_OPTIONS = [
    ["", "Tất cả các ngày"],
    ["workdays", "Thứ 2 – Thứ 6"],
    ["weekend", "Thứ 7 – Chủ nhật"],
    ["0", "Thứ 2"],
    ["1", "Thứ 3"],
    ["2", "Thứ 4"],
    ["3", "Thứ 5"],
    ["4", "Thứ 6"],
    ["5", "Thứ 7"],
    ["6", "Chủ nhật"],
];

const CORRECTION_BUS_TYPE = "tp_hr_attendance/correction_updated";

function parseClockToFloat(value) {
    const match = /^(\d{2}):(\d{2})$/.exec(value);
    if (!match) {
        return null;
    }
    const hours = Number(match[1]);
    const minutes = Number(match[2]);
    if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
        return null;
    }
    return hours + minutes / 60;
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = String(reader.result || "");
            const comma = result.indexOf(",");
            resolve(comma >= 0 ? result.slice(comma + 1) : result);
        };
        reader.onerror = () => reject(new Error("Không đọc được tệp minh chứng."));
        reader.readAsDataURL(file);
    });
}

export class CorrectionFormDialog extends Component {
    static template = "tp_hr_attendance.CorrectionFormDialog";
    static components = { Dialog, InlineErrors, TpTime24Field };
    props = useProps();
    evidenceInput = signal.ref();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        const req = this.props.request || null;
        this.state = proxy({
            workDate: this.props.workDate || req?.workDate || "",
            requestedIn: (req ? req.requested_in : this.props.requestedIn) || "",
            requestedOut: (req ? req.requested_out : this.props.requestedOut) || "",
            reason: req?.reason || "",
            evidenceName: req?.evidence_name || "",
            evidenceFile: null,
            readingFile: false,
            busy: false,
            attempt: 0,
            submitAttempt: false,
            serverError: null,
        });
    }

    get title() {
        return this.props.request ? `Sửa đề nghị ${this.props.request.name}` : "Đề nghị điều chỉnh công";
    }

    hasFieldError(field) {
        return this.fieldErrors.some((err) => err.id === `tp_att_correction_${field}`);
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errors = [];
        const add = (field, label, message) => errors.push({ id: `tp_att_correction_${field}`, label, message });
        const inFloat = parseClockToFloat(this.state.requestedIn);
        const outFloat = parseClockToFloat(this.state.requestedOut);
        if (!this.state.workDate) {
            add("date", "Ngày công", "Vui lòng chọn ngày công cần điều chỉnh.");
        }
        if (inFloat === null) {
            add("in", "Giờ vào đề nghị", "Vui lòng nhập giờ vào hợp lệ (00:00–23:59).");
        }
        if (outFloat === null) {
            add("out", "Giờ ra đề nghị", "Vui lòng nhập giờ ra hợp lệ (00:00–23:59).");
        } else if (inFloat !== null && outFloat <= inFloat) {
            add("out", "Giờ ra đề nghị", "Giờ ra phải sau giờ vào trong cùng ngày công.");
        }
        if (this.state.submitAttempt && !this.state.reason.trim()) {
            add("reason", "Lý do / giải trình", "Nhập giải trình / lý do trước khi gửi duyệt.");
        }
        return errors;
    }

    async onFileChange(ev) {
        const file = ev.target.files?.[0];
        if (!file || this.state.busy || this.state.readingFile) {
            return;
        }
        if (file.size > MAX_EVIDENCE_BYTES) {
            ev.target.value = "";
            this.state.serverError = {
                kind: "validation",
                title: "Tệp minh chứng quá lớn",
                message: "Dung lượng tệp minh chứng tối đa là 10 MB.",
            };
            this.state.attempt++;
            return;
        }
        this.state.readingFile = true;
        try {
            this.state.evidenceFile = await readFileAsBase64(file);
            this.state.evidenceName = file.name;
            this.state.serverError = null;
        } catch (err) {
            ev.target.value = "";
            this.state.serverError = { kind: "validation", title: "Không đọc được minh chứng", message: err.message };
            this.state.attempt++;
        } finally {
            this.state.readingFile = false;
        }
    }

    clearFile() {
        if (this.state.busy || this.state.readingFile) {
            return;
        }
        this.state.evidenceFile = false;
        this.state.evidenceName = "";
        this.evidenceInput().value = "";
    }

    async save(submit) {
        if (this.state.busy || this.state.readingFile) {
            return;
        }
        this.state.serverError = null;
        this.state.submitAttempt = submit;
        this.state.attempt++;
        if (this.fieldErrors.length) {
            return;
        }
        const vals = {
            work_date: this.state.workDate,
            requested_in: parseClockToFloat(this.state.requestedIn),
            requested_out: parseClockToFloat(this.state.requestedOut),
            reason: this.state.reason.trim() || false,
        };
        if (this.state.evidenceFile !== null) {
            vals.evidence_file = this.state.evidenceFile;
            vals.evidence_name = this.state.evidenceName || false;
        }
        this.state.busy = submit ? "submit" : "draft";
        try {
            const res = await this.orm.call("tp.hr.attendance.correction", "tp_save_and_submit", [
                vals,
                this.props.request?.id || false,
                Boolean(submit),
                this.operationToken,
            ]);
            const sent = submit && res.state === "submitted";
            let notice = "Đề nghị đã đổi trạng thái. Đang cập nhật danh sách.";
            if (sent) {
                notice = "Đã gửi đề nghị điều chỉnh cho admin";
            } else if (!submit && ["draft", "returned"].includes(res.state)) {
                notice = "Đã lưu bản nháp đề nghị điều chỉnh.";
            }
            this.notification.add(notice, { type: sent ? "success" : "info" });
            this.props.onSaved?.(res.work_date);
            this.props.close();
        } catch (error) {
            this.state.serverError = saveError(error, { verb: submit ? "gửi duyệt" : "lưu nháp" });
        } finally {
            this.state.busy = false;
        }
    }
}

export class WithdrawDialog extends Component {
    static template = "tp_hr_attendance.WithdrawDialog";
    static components = { Dialog, InlineErrors };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = proxy({ reason: "", busy: false, attempt: 0, serverError: null });
    }

    async confirm() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.serverError = null;
        this.state.attempt++;
        try {
            await this.orm.call("tp.hr.attendance.correction", "action_withdraw", [
                [this.props.request.id],
                this.state.reason.trim() || false,
            ]);
            this.notification.add("Đã thu hồi", { type: "success" });
            this.props.onDone?.();
            this.props.close();
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "thu hồi" });
        } finally {
            this.state.busy = false;
        }
    }
}

export class MyAttendance extends Component {
    static template = "tp_hr_attendance.Mine";
    static components = { AttPager, InlineErrors, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        let bus = null;
        try {
            bus = useService("bus_service");
        } catch {
            bus = null;
        }
        const saved = readStore(STORE_KEY);
        const savedMode = MODES.some(([key]) => key === saved.mode) ? saved.mode : "month";
        const savedPageSize = PAGE_SIZES.includes(Number(saved.pageSize)) ? Number(saved.pageSize) : 100;
        this.state = proxy({
            mode: savedMode,
            date: "",
            from: "",
            to: "",
            draftState: "",
            draftWeekday: "",
            appliedState: "",
            appliedWeekday: "",
            page: 1,
            pageSize: savedPageSize,
            mobileFiltersOpen: false,
            expandedDate: "",
            loading: true,
            refreshing: false,
            exporting: false,
            serverError: null,
            attempt: 0,
            data: null,
        });
        this.modes = MODES;
        this.weekdayOptions = WEEKDAY_OPTIONS;
        this.skeletonRows = [0, 1, 2, 3, 4, 5];
        this.mineStatusInfo = mineStatusInfo;
        this.formatHours = formatHours;
        this.request = 0;
        // ENTI-ATTENDANCE-002: a punch synced by the server shows here without F5 (bus + visible-tab fallback poll).
        this.live = useAttendanceLive({
            refresh: () => (this.state.loading || this.state.exporting ? false : this.load({ silent: true })),
            relevant: (payload) => {
                const data = this.data;
                const dates = payload.dates || [];
                return Boolean(data?.has_employee) && (!dates.length || dates.some((day) => day >= data.start && day <= data.end));
            },
        });

        const onKeyDown = (ev) => {
            if (ev.key !== "Escape") {
                return;
            }
            if (this.state.mobileFiltersOpen) {
                this.state.mobileFiltersOpen = false;
                document.querySelector(".o_tp_mine_filter_toggle")?.focus();
            }
        };
        let unsubCorrection = null;
        onMounted(() => {
            document.addEventListener("keydown", onKeyDown);
            if (bus) {
                try {
                    unsubCorrection = bus.subscribe(CORRECTION_BUS_TYPE, () => {
                        if (!this.state.loading && !this.state.exporting) {
                            this.load({ silent: true });
                        }
                    });
                    bus.start();
                } catch {
                    unsubCorrection = null;
                }
            }
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", onKeyDown);
            if (typeof unsubCorrection === "function") {
                unsubCorrection();
            }
            this.request++;
        });
        onWillStart(() => this.load());
    }

    get data() {
        return this.state.data;
    }

    get isEmbedded() {
        return Boolean(this.props.embedded);
    }

    get stateOptions() {
        const hasLeave = Boolean(this.data?.has_leave_source);
        return STATE_OPTIONS.filter(([key]) => key !== "leave" || hasLeave);
    }

    get summary() {
        return (
            this.data?.summary || {
                total_days: 0,
                recorded_days: 0,
                complete_days: 0,
                working_days: 0,
                attention_days: 0,
                missing_days: 0,
                review_days: 0,
                absent_days: 0,
                no_punch_days: 0,
                rest_days: 0,
                no_source_days: 0,
                leave_days: 0,
                future_days: 0,
            }
        );
    }

    get late() {
        return this.data?.late || { state: "none", count: null, minutes: null, source: "", text: "Chưa có số liệu" };
    }

    /** "enti": summed day by day from ENTI for exactly the viewed period; "excel": an imported machine period total. */
    get lateOrigin() {
        if (this.late.source === "ENTI" || (this.late.state === "exact" && !this.late.source)) {
            return "enti";
        }
        return this.late.state === "exact" ? "excel" : "";
    }

    get latePeriodHint() {
        if (this.late.state === "exact") {
            return null;
        }
        const periods = this.data?.file_periods || [];
        return periods.find((item) => item.has_late) || null;
    }

    get hasPendingChanges() {
        return (
            this.state.draftState !== this.state.appliedState ||
            this.state.draftWeekday !== this.state.appliedWeekday
        );
    }

    get appliedChips() {
        const chips = [];
        if (this.state.appliedState) {
            const found = STATE_OPTIONS.find(([key]) => key === this.state.appliedState);
            chips.push({
                key: "state",
                title: "Tình trạng",
                label: found ? found[1] : this.state.appliedState,
            });
        }
        if (this.state.appliedWeekday) {
            const found = WEEKDAY_OPTIONS.find(([key]) => key === this.state.appliedWeekday);
            chips.push({
                key: "weekday",
                title: "Ngày",
                label: found ? found[1] : this.state.appliedWeekday,
            });
        }
        return chips;
    }

    get activeFilterCount() {
        return this.appliedChips.length;
    }

    get hasAnyFilterOrDraft() {
        return Boolean(
            this.state.appliedState ||
            this.state.appliedWeekday ||
            this.state.draftState ||
            this.state.draftWeekday
        );
    }

    get anyRowHasDetail() {
        return Boolean(this.data?.rows?.some((row) => row.has_detail));
    }

    get rangeBannerText() {
        if (!this.data) {
            return "";
        }
        if (this.data.mode === "month") {
            return `${this.data.period_label} (${this.data.range_display})`;
        }
        if (this.data.mode === "week") {
            return `Tuần ${this.data.range_display}`;
        }
        return `Khoảng ngày: ${this.data.range_display}`;
    }

    get resultSummaryText() {
        if (!this.data) {
            return "";
        }
        const total = this.data.total ?? 0;
        const periodDays = this.data.period_days ?? total;
        if (this.activeFilterCount > 0) {
            return `Tìm thấy ${total} / ${periodDays} ngày trong kỳ`;
        }
        return `${total} ngày trong kỳ`;
    }

    buildQueryParams(includePage = true) {
        const params = {
            mode: this.state.mode,
            date: this.state.date,
            from: this.state.from,
            to: this.state.to,
            state: this.state.appliedState,
            weekday: this.state.appliedWeekday,
        };
        if (includePage) {
            params.page = this.state.page;
            params.page_size = this.state.pageSize;
        }
        return params;
    }

    /** ``silent``: automatic refresh — no dimming / loading bar, and a failure keeps what is already shown. */
    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state[silent ? "refreshing" : "loading"] = true;
        if (!silent) {
            this.state.serverError = null;
        }
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.day", "tp_mine", [this.buildQueryParams(true)]);
            if (request !== this.request) {
                return;
            }
            this.state.data = data;
            if (data.has_employee) {
                Object.assign(this.state, {
                    date: data.date,
                    from: data.start,
                    to: data.end,
                    page: data.page || 1,
                    pageSize: data.page_size || this.state.pageSize,
                });
                writeStore(STORE_KEY, {
                    mode: data.mode === "range" ? "month" : data.mode,
                    pageSize: this.state.pageSize,
                });
            }
            this.state.serverError = null;
            this.live.loaded();
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.serverError = saveError(error, { verb: "tải công cá nhân" });
                this.state.attempt++;
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
                this.state.refreshing = false;
                this.live.flush();
            }
        }
    }

    resetPeriod(changes) {
        Object.assign(
            this.state,
            {
                expandedDate: "",
                page: 1,
            },
            changes
        );
        return this.load();
    }

    setMode(mode) {
        return this.resetPeriod({ mode, date: this.state.from || this.state.date });
    }

    step(delta) {
        if (!this.data) {
            return;
        }
        return this.resetPeriod(stepPeriod(this.state.mode, this.data, delta));
    }

    goToday() {
        return this.resetPeriod({
            mode: this.state.mode === "range" ? "month" : this.state.mode,
            date: this.data?.today || "",
        });
    }

    onDate(ev) {
        if (ev.target.value) {
            return this.resetPeriod({ date: ev.target.value });
        }
    }

    onMonth(ev) {
        if (ev.target.value) {
            return this.resetPeriod({ date: `${ev.target.value}-01` });
        }
    }

    openFilePeriod(item) {
        return this.resetPeriod({ mode: "range", from: item.from, to: item.to });
    }

    onDraftState(ev) {
        this.state.draftState = ev.target.value;
    }

    onDraftWeekday(ev) {
        this.state.draftWeekday = ev.target.value;
    }

    applyFilters() {
        Object.assign(this.state, {
            appliedState: this.state.draftState,
            appliedWeekday: this.state.draftWeekday,
            page: 1,
            expandedDate: "",
            mobileFiltersOpen: false,
        });
        return this.load();
    }

    clearFilters() {
        Object.assign(this.state, {
            draftState: "",
            draftWeekday: "",
            appliedState: "",
            appliedWeekday: "",
            page: 1,
            expandedDate: "",
            mobileFiltersOpen: false,
        });
        return this.load();
    }

    removeChip(key) {
        if (key === "state") {
            this.state.draftState = "";
            this.state.appliedState = "";
        } else if (key === "weekday") {
            this.state.draftWeekday = "";
            this.state.appliedWeekday = "";
        }
        this.state.page = 1;
        this.state.expandedDate = "";
        return this.load();
    }

    quickFilterAttention() {
        if (this.state.appliedState === "attention") {
            return this.removeChip("state");
        }
        Object.assign(this.state, {
            draftState: "attention",
            appliedState: "attention",
            page: 1,
            expandedDate: "",
        });
        return this.load();
    }

    setPage(page) {
        this.state.page = page;
        this.state.expandedDate = "";
        return this.load();
    }

    setPageSize(size) {
        Object.assign(this.state, { pageSize: size, page: 1, expandedDate: "" });
        return this.load();
    }

    toggleRow(row) {
        if (!row.has_detail) {
            return;
        }
        this.state.expandedDate = this.state.expandedDate === row.date ? "" : row.date;
    }

    isExpanded(dateIso) {
        return this.state.expandedDate === dateIso;
    }

    cellMissingLabel(row, side) {
        if (row.state === "missing") {
            if (side === "in" && !row.in) {
                return "Thiếu giờ vào";
            }
            if (side === "out" && !row.out) {
                return "Thiếu giờ ra";
            }
        }
        if (row.state === "working" && side === "out" && !row.out) {
            return "Chờ ghi nhận giờ ra";
        }
        if (row.state === "review" && ((side === "in" && !row.in) || (side === "out" && !row.out))) {
            return "Cần kiểm tra";
        }
        return "";
    }

    sourceName(code) {
        if (code === "enti") {
            return "Đồng bộ ENTI";
        }
        if (code === "correction") {
            return "Điều chỉnh đã duyệt";
        }
        if (code === "excel") {
            return "Excel máy chấm công";
        }
        if (code === "api") {
            return "API máy chấm công";
        }
        return code || "";
    }

    async exportOwn() {
        if (this.state.exporting) {
            return;
        }
        this.state.exporting = true;
        this.state.serverError = null;
        try {
            downloadBase64(await this.orm.call("tp.hr.attendance.day", "tp_export_mine", [this.buildQueryParams(false)]));
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "xuất công cá nhân" });
            this.state.attempt++;
        } finally {
            this.state.exporting = false;
            this.live.flush();
        }
    }

    openRequest(workDate = "") {
        const defaultDate = workDate || this.data?.today || "";
        const row = this.data?.rows.find((row) => row.date === defaultDate);
        this.dialog.add(CorrectionFormDialog, {
            workDate: defaultDate,
            requestedIn: row?.in,
            requestedOut: row?.out,
            onSaved: (savedDate) => {
                if (savedDate) {
                    this.state.expandedDate = savedDate;
                }
                this.load();
            },
        });
    }

    openEditRequest(req, workDate = "") {
        this.dialog.add(CorrectionFormDialog, {
            request: req,
            workDate,
            onSaved: (savedDate) => {
                if (savedDate) {
                    this.state.expandedDate = savedDate;
                }
                this.load();
            },
        });
    }

    openWithdraw(req) {
        this.dialog.add(WithdrawDialog, {
            request: req,
            onDone: () => this.load(),
        });
    }

    async reopenDraft(req, workDate = "") {
        this.state.serverError = null;
        try {
            await this.orm.call("tp.hr.attendance.correction", "action_reopen_draft", [[req.id]]);
            await this.load();
            this.openEditRequest({ ...req, state: "draft" }, workDate);
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "mở lại bản nháp" });
            this.state.attempt++;
        }
    }

    openRequests() {
        return this.action.doAction("tp_hr_attendance.action_my_requests");
    }

    openStandalone() {
        return this.action.doAction("tp_hr_attendance.action_mine");
    }
}

registry.category("actions").add("tp_hr_attendance.mine", MyAttendance);

const CONTENT = {
    "tp.hr.attendance.period": [
        "Chốt kỳ công",
        "Rà soát các ngày và đề nghị trước khi chốt. Chỉ Admin hoặc người được phân công chốt kỳ thực hiện.",
        "Tạo kỳ công",
        "Chưa có kỳ công",
    ],
    "tp.hr.attendance.log": [
        "Nhật ký chấm công",
        "Lịch sử thao tác và phiên bản, không chứa giải trình hoặc minh chứng cá nhân.",
        "",
        "Chưa có nhật ký",
    ],
};
patch(HrListController.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.props.resModel === "tp.hr.attendance.correction") {
            let bus = null;
            try {
                bus = useService("bus_service");
            } catch {
                bus = null;
            }
            let unsub = null;
            let timer = null;
            onMounted(() => {
                if (bus) {
                    try {
                        unsub = bus.subscribe(CORRECTION_BUS_TYPE, () => {
                            browser.clearTimeout(timer);
                            timer = browser.setTimeout(() => {
                                this.model?.load?.();
                            }, 200);
                        });
                        bus.start();
                    } catch {
                        unsub = null;
                    }
                }
            });
            onWillUnmount(() => {
                browser.clearTimeout(timer);
                if (typeof unsub === "function") {
                    unsub();
                }
            });
        }
    },
    get hrContent() {
        if (this.props.resModel === "tp.hr.attendance.correction") {
            if (this.props.context?.tp_review_queue) {
                return [
                    "Xử lý điều chỉnh công",
                    "Phiếu chờ duyệt từ các phòng ban; chỉ Admin (Admin gốc hoặc Admin được ủy quyền đang hiệu lực) duyệt hoặc trả lại.",
                    "",
                    "Không có phiếu chờ xử lý",
                ];
            }
            return [
                "Yêu cầu điều chỉnh công của tôi",
                "Các phiếu điều chỉnh giờ chấm công cá nhân của bạn; lưu nháp hoặc gửi Admin duyệt.",
                "Tạo đề nghị",
                "Chưa có đề nghị",
            ];
        }
        return CONTENT[this.props.resModel] || super.hrContent;
    },
});

TpHrMyProfile.components = { ...TpHrMyProfile.components, MyAttendance };

patch(TpHrMyProfile.prototype, {
    setup() {
        super.setup(...arguments);
        this.tabs = [...this.tabs, { id: "attendance", label: "Công của tôi", icon: "calendar_today" }];
    },
});
