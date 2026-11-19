import { Component, onMounted, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { HrListController } from "@tp_hr_workspace/table/table";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";
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
    ["no_punch", "Chưa chấm công"],
    ["no_source", "Chưa có dữ liệu"],
    ["leave", "Nghỉ đã xác nhận"],
    ["future", "Ngày tương lai"],
];
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

export class MyAttendance extends Component {
    static template = "tp_hr_attendance.Mine";
    static components = { AttPager, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        try {
            this.busService = useService("bus_service");
        } catch (_) {
            this.busService = null;
        }
        const saved = readStore(STORE_KEY);
        const savedMode = MODES.some(([key]) => key === saved.mode) ? saved.mode : "month";
        const savedPageSize = PAGE_SIZES.includes(Number(saved.pageSize)) ? Number(saved.pageSize) : 50;
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
            fileMenu: false,
            mobileFiltersOpen: false,
            expandedDate: "",
            loading: true,
            exporting: false,
            error: "",
            data: null,
        });
        this.modes = MODES;
        this.weekdayOptions = WEEKDAY_OPTIONS;
        this.skeletonRows = [0, 1, 2, 3, 4, 5];
        this.mineStatusInfo = mineStatusInfo;
        this.formatHours = formatHours;
        this.request = 0;
        this.pollTimer = null;

        const onKeyDown = (ev) => {
            if (ev.key !== "Escape") {
                return;
            }
            if (this.state.fileMenu) {
                this.state.fileMenu = false;
                document.querySelector(".o_tp_mine_file_trigger")?.focus();
            } else if (this.state.mobileFiltersOpen) {
                this.state.mobileFiltersOpen = false;
                document.querySelector(".o_tp_mine_filter_toggle")?.focus();
            }
        };
        const onDocumentClick = (ev) => {
            if (this.state.fileMenu && !ev.target.closest?.(".o_tp_mine_file_wrap")) {
                this.state.fileMenu = false;
            }
        };
        onMounted(() => {
            document.addEventListener("keydown", onKeyDown);
            document.addEventListener("click", onDocumentClick);
            this.pollTimer = browser.setInterval(() => {
                if (!document.hidden && !this.state.loading) {
                    this.load();
                }
            }, 30000);
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", onKeyDown);
            document.removeEventListener("click", onDocumentClick);
            if (this.pollTimer) {
                browser.clearInterval(this.pollTimer);
            }
        });
        onWillStart(async () => {
            if (this.busService) {
                try {
                    this.busService.addChannel("tp_hr_attendance_channel");
                    this.busService.subscribe("enti_sync_completed", () => {
                        if (!this.state.loading) {
                            this.load();
                        }
                    });
                } catch (_) {}
            }
            await this.load();
        });
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
                no_punch_days: 0,
                no_source_days: 0,
                leave_days: 0,
                future_days: 0,
            }
        );
    }

    get late() {
        return this.data?.late || { state: "none", count: null, minutes: null, source: "", text: "Chưa có số liệu" };
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
        return `Kỳ theo file: ${this.data.range_display}`;
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

    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_mine", [this.buildQueryParams(true)]);
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
        } catch (error) {
            if (request === this.request) {
                this.state.error = rpcError(error, "Không tải được công cá nhân. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
            }
        }
    }

    resetPeriod(changes) {
        Object.assign(
            this.state,
            {
                fileMenu: false,
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

    toggleFileMenu() {
        this.state.fileMenu = !this.state.fileMenu;
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
        if (code === "excel") {
            return "Excel máy chấm công";
        }
        if (code === "api") {
            return "API máy chấm công";
        }
        return "";
    }

    async exportOwn() {
        if (this.state.exporting) {
            return;
        }
        this.state.exporting = true;
        this.state.error = "";
        try {
            downloadBase64(await this.orm.call("tp.hr.attendance.day", "tp_export_mine", [this.buildQueryParams(false)]));
        } catch (error) {
            this.state.error = rpcError(error, "Không xuất được công cá nhân. Vui lòng thử lại.");
        } finally {
            this.state.exporting = false;
        }
    }

    async openRequest(workDate = "") {
        const context = workDate ? { default_work_date: workDate } : {};
        await this.action.doAction(
            {
                type: "ir.actions.act_window",
                name: "Đề nghị điều chỉnh công",
                res_model: "tp.hr.attendance.correction",
                views: [[false, "form"]],
                target: "new",
                context,
            },
            { onClose: () => this.load() }
        );
    }

    openRequests() {
        return this.action.doAction("tp_hr_attendance.action_my_requests");
    }
}

registry.category("actions").add("tp_hr_attendance.mine", MyAttendance);

const CONTENT = {
    "tp.hr.attendance.correction": ["Đề nghị điều chỉnh công", "Phiếu riêng của người đề nghị; chỉ admin (admin gốc hoặc admin được ủy quyền) duyệt hoặc trả lại.", "Tạo đề nghị", "Chưa có đề nghị"],
    "tp.hr.attendance.period": ["Chốt kỳ công", "Rà soát các ngày và đề nghị trước khi chốt. Quyền chốt cần phân công riêng.", "Tạo kỳ công", "Chưa có kỳ công"],
    "tp.hr.attendance.batch": ["Nhập dữ liệu công", "Xem trước và đối chiếu nguồn trước khi ghi nhận giờ công.", "Tạo lô nhập", "Chưa có lô nhập"],
    "tp.hr.attendance.log": ["Nhật ký chấm công", "Lịch sử thao tác và phiên bản, không chứa giải trình hoặc minh chứng cá nhân.", "", "Chưa có nhật ký"],
};
patch(HrListController.prototype, {
    get hrContent() {
        return CONTENT[this.props.resModel] || super.hrContent;
    },
});

patch(TpHrMyProfile, { components: { ...TpHrMyProfile.components, MyAttendance } });
patch(TpHrMyProfile.prototype, {
    setup() {
        super.setup(...arguments);
        this.tabs = [...this.tabs, { id: "attendance", label: "Công của tôi", icon: "calendar_month" }];
    },
});
