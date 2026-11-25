import {
    onMounted,
    onWillStart,
    onWillUnmount,
    proxy,
    t,
    useListener,
    useProps,
} from "@odoo/owl";
import { AttendeeCalendarCommonRenderer } from "@calendar/views/attendee_calendar/common/attendee_calendar_common_renderer";
import { AttendeeCalendarController } from "@calendar/views/attendee_calendar/attendee_calendar_controller";
import { AttendeeCalendarRenderer } from "@calendar/views/attendee_calendar/attendee_calendar_renderer";
import { attendeeCalendarView } from "@calendar/views/attendee_calendar/attendee_calendar_view";
import { browser } from "@web/core/browser/browser";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { router, routerBus } from "@web/core/browser/router";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import {
    CalendarCommonRenderer,
    calendarCommonRendererProps,
} from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";
import { TpShareToDiscussDialog } from "../shared/share_to_discuss_dialog";
import { TpCalendarEventDialog } from "./calendar_event_dialog";
import { TpCalendarPopover } from "./calendar_popover";

const { DateTime } = luxon;

const HOUR_24_FMT = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
};

const MINI_WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const AGENDA_PAGE_SIZES = [10, 20, 50, 100];

const CALENDAR_COLOR_PALETTE = [
    { id: 1, hex: "#1766c0", label: "Xanh dương" },
    { id: 2, hex: "#0d8a7b", label: "Xanh teal" },
    { id: 3, hex: "#b76a08", label: "Cam hổ phách" },
    { id: 4, hex: "#c83542", label: "Đỏ đô" },
    { id: 5, hex: "#6d28d9", label: "Tím đậm" },
    { id: 10, hex: "#16805d", label: "Xanh lục" },
];

function extractDeepLinkEventId(props) {
    const candidates = [
        router.current?.event_id,
        props?.context?.default_calendar_event_id,
        props?.resId,
    ];
    for (const c of candidates) {
        const n = Number(c);
        if (Number.isInteger(n) && n > 0) {
            return n;
        }
    }
    const path = browser.location?.pathname || "";
    const m = path.match(/\/app\/ca-nhan\/lich-lam-viec\/(\d+)/);
    if (m) {
        return Number(m[1]);
    }
    const sp = new URLSearchParams(browser.location?.search || "");
    const qId = Number(sp.get("event_id") || 0);
    return Number.isInteger(qId) && qId > 0 ? qId : 0;
}

export class TpPersonalCalendarCommonRenderer extends AttendeeCalendarCommonRenderer {
    static components = {
        ...CalendarCommonRenderer.components,
        Popover: TpCalendarPopover,
    };
    props = useProps({
        ...calendarCommonRendererProps,
        onDragResizeError: t.function().optional(),
    });

    setup() {
        super.setup();
        // Force 24-hour clock across all TANPHAT ONE Calendar views
        this.timeFormat = "HH:mm";
    }

    get options() {
        return {
            ...super.options,
            allDayText: "Cả ngày",
            slotLabelFormat: HOUR_24_FMT,
            eventTimeFormat: HOUR_24_FMT,
            scrollTime: "08:00:00",
            businessHours: {
                daysOfWeek: [1, 2, 3, 4, 5, 6],
                startTime: "08:30",
                endTime: "17:00",
            },
            moreLinkContent: (args) => `+${args.num} lịch khác`,
        };
    }

    onEventDrop(info) {
        this.fc().unselect();
        const forceAllDay = info.oldEvent.allDay !== info.event.allDay;
        const recordPayload = this.fcEventToRecord(info.event, forceAllDay);
        this.props.model
            .updateRecord(recordPayload)
            .then((res) => {
                // If user cancelled recurrence scope dialog, revert visual position cleanly
                if (res === false) {
                    info.revert();
                }
            })
            .catch((err) => {
                info.revert();
                this.props.onDragResizeError?.(err);
            });
    }

    onEventResize(info) {
        this.fc().unselect();
        const recordPayload = this.fcEventToRecord(info.event);
        this.props.model
            .updateRecord(recordPayload)
            .then((res) => {
                if (res === false) {
                    info.revert();
                }
            })
            .catch((err) => {
                info.revert();
                this.props.onDragResizeError?.(err);
            });
    }
}

export class TpPersonalCalendarRenderer extends AttendeeCalendarRenderer {
    static components = {
        ...AttendeeCalendarRenderer.components,
        day: TpPersonalCalendarCommonRenderer,
        week: TpPersonalCalendarCommonRenderer,
        month: TpPersonalCalendarCommonRenderer,
    };
}

export class TpPersonalCalendarController extends AttendeeCalendarController {
    static template = "tp_personal_tools.PersonalCalendarController";
    static components = {
        ...AttendeeCalendarController.components,
        InlineErrors,
        TpColleaguePicker,
    };

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this.MINI_WEEKDAYS = MINI_WEEKDAYS;
        this.AGENDA_PAGE_SIZES = AGENDA_PAGE_SIZES;
        this.CALENDAR_COLOR_PALETTE = CALENDAR_COLOR_PALETTE;
        this.searchTimer = null;
        this.agendaSeq = 0;

        const savedMode = browser.localStorage.getItem("tp_personal_calendar_mode");
        const defaultMode =
            savedMode && ["day", "week", "month", "agenda"].includes(savedMode)
                ? savedMode
                : this.uiService.isSmall
                  ? "agenda"
                  : "week";

        const nowDt = DateTime.local();

        this.tpState = proxy({
            viewMode: defaultMode, // 'day' | 'week' | 'month' | 'agenda'
            sidebarOpenDesktop: true,
            sidebarOpenMobile: false,
            miniCursorIso: nowDt.startOf("month").toISODate(),

            // Sidebar bootstrap data
            myCalendars: [],
            sharedCalendars: [],
            colleagueFilters: [],
            showNewCalForm: false,
            newCalName: "",
            newCalColor: 2,
            newCalPrivacy: "public",
            newCalShareUsers: [],
            creatingCal: false,

            // Search & Agenda state
            searchQuery: "",
            agendaLoading: false,
            agendaGroups: [],
            agendaTotal: 0,
            agendaPage: 1,
            agendaPageSize: 20,
            agendaFiltersOpen: false,
            agendaDateFrom: "",
            agendaDateTo: "",
            agendaResponseState: "",
            agendaPrivacy: "",
            agendaOrganizer: [],

            // Error banner (e.g., drag/resize permission error or invalid deep link)
            bannerError: null,
        });

        onWillStart(async () => {
            await this.refreshSidebarBootstrap();
            if (this.tpState.viewMode === "agenda") {
                await this.loadAgenda();
            }
        });

        onMounted(() => {
            document.body.classList.add("o_tp_personal_calendar_active");
            if (
                ["day", "week", "month"].includes(this.tpState.viewMode) &&
                this.model.scale !== this.tpState.viewMode
            ) {
                this.model.load({ scale: this.tpState.viewMode });
            }
            const deepEventId = extractDeepLinkEventId(this.props);
            if (deepEventId > 0) {
                this.openDeepLinkedEvent(deepEventId);
            }
        });

        onWillUnmount(() => {
            document.body.classList.remove("o_tp_personal_calendar_active");
            if (this.searchTimer) {
                clearTimeout(this.searchTimer);
            }
        });

        useBus(routerBus, "ROUTE_CHANGE", () => {
            const deepEventId = extractDeepLinkEventId(this.props);
            if (deepEventId > 0) {
                this.openDeepLinkedEvent(deepEventId);
            }
        });

        useListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.tpState.sidebarOpenMobile) {
                this.tpState.sidebarOpenMobile = false;
            }
        });
    }

    get rendererProps() {
        return {
            ...super.rendererProps,
            onDragResizeError: (err) => {
                this.tpState.bannerError = saveError(err, { verb: "đổi thời gian sự kiện" });
            },
        };
    }

    async refreshSidebarBootstrap() {
        try {
            const boot = await this.orm.call("calendar.event", "tp_get_calendar_bootstrap", []);
            this.tpState.myCalendars = boot?.my_calendars || [];
            this.tpState.sharedCalendars = boot?.shared_calendars || [];
            this.tpState.colleagueFilters = boot?.colleague_filters || [];
        } catch {
            // Keep existing state on transient error
        }
    }

    get activePeriodLabel() {
        const d = this.date || DateTime.local();
        const mode = this.tpState.viewMode;
        if (mode === "day") {
            const wdNames = [
                "",
                "Thứ hai",
                "Thứ ba",
                "Thứ tư",
                "Thứ năm",
                "Thứ sáu",
                "Thứ bảy",
                "Chủ nhật",
            ];
            return `${wdNames[d.weekday] || ""}, ${d.toFormat("dd/MM/yyyy")}`;
        }
        if (mode === "week") {
            const { start, end } = this.model.visibleRange || {
                start: d.startOf("week"),
                end: d.endOf("week"),
            };
            if (start.month === end.month) {
                return `Tháng ${start.toFormat("MM/yyyy")} (${start.toFormat("dd")} – ${end.toFormat(
                    "dd/MM"
                )})`;
            }
            return `${start.toFormat("dd/MM")} – ${end.toFormat("dd/MM/yyyy")}`;
        }
        if (mode === "agenda") {
            if (this.tpState.agendaDateFrom && this.tpState.agendaDateTo) {
                const f = this.tpState.agendaDateFrom.split("-").reverse().join("/");
                const tStr = this.tpState.agendaDateTo.split("-").reverse().join("/");
                return `${f} – ${tStr}`;
            }
            return `Tháng ${d.toFormat("MM/yyyy")} · Danh sách`;
        }
        return `Tháng ${d.toFormat("MM/yyyy")}`;
    }

    get miniCalendarTitle() {
        const cur = DateTime.fromISO(this.tpState.miniCursorIso || DateTime.local().toISODate());
        return `Tháng ${cur.toFormat("MM / yyyy")}`;
    }

    get miniCalendarWeeks() {
        const cur = DateTime.fromISO(
            this.tpState.miniCursorIso || DateTime.local().toISODate()
        ).startOf("month");
        const firstMondayOffset = (cur.weekday + 6) % 7;
        let iter = cur.minus({ days: firstMondayOffset });
        const todayIso = DateTime.local().toISODate();
        const selectedIso = (this.date || DateTime.local()).toISODate();
        const weeks = [];
        for (let w = 0; w < 6; w++) {
            const days = [];
            for (let i = 0; i < 7; i++) {
                const iso = iter.toISODate();
                days.push({
                    iso,
                    dayNum: iter.day,
                    inMonth: iter.month === cur.month,
                    isToday: iso === todayIso,
                    isSelected: iso === selectedIso,
                });
                iter = iter.plus({ days: 1 });
            }
            weeks.push({ key: `w_${w}`, days });
        }
        return weeks;
    }

    moveMiniMonth(delta) {
        const cur = DateTime.fromISO(this.tpState.miniCursorIso || DateTime.local().toISODate());
        this.tpState.miniCursorIso = cur.plus({ months: delta }).startOf("month").toISODate();
    }

    async onSelectMiniDate(iso) {
        const target = DateTime.fromISO(iso).startOf("day");
        this.tpState.miniCursorIso = target.startOf("month").toISODate();
        this.tpState.sidebarOpenMobile = false;
        if (this.tpState.viewMode === "agenda") {
            this.tpState.agendaDateFrom = iso;
            this.tpState.agendaDateTo = target.plus({ days: 14 }).toISODate();
            this.tpState.agendaPage = 1;
            await this.loadAgenda();
            return;
        }
        await this.model.load({ date: target });
    }

    async switchViewMode(mode) {
        if (!["day", "week", "month", "agenda"].includes(mode)) {
            return;
        }
        this.tpState.viewMode = mode;
        browser.localStorage.setItem("tp_personal_calendar_mode", mode);
        if (mode === "agenda") {
            await this.loadAgenda();
        } else {
            await this.model.load({ scale: mode });
        }
    }

    async navigatePeriod(direction) {
        if (this.tpState.viewMode === "agenda") {
            const today = DateTime.local();
            if (direction === "today") {
                this.tpState.agendaDateFrom = today.toISODate();
                this.tpState.agendaDateTo = today.plus({ days: 30 }).toISODate();
            } else {
                const baseFrom = this.tpState.agendaDateFrom
                    ? DateTime.fromISO(this.tpState.agendaDateFrom)
                    : today;
                const shift = direction === "next" ? 14 : -14;
                const nextFrom = baseFrom.plus({ days: shift });
                this.tpState.agendaDateFrom = nextFrom.toISODate();
                this.tpState.agendaDateTo = nextFrom.plus({ days: 30 }).toISODate();
            }
            this.tpState.agendaPage = 1;
            await this.loadAgenda();
            return;
        }
        this.setDate(direction);
        const nextDt =
            direction === "today"
                ? DateTime.local()
                : direction === "next"
                  ? this.model.date.plus({ [`${this.model.scale}s`]: 1 })
                  : this.model.date.minus({ [`${this.model.scale}s`]: 1 });
        this.tpState.miniCursorIso = nextDt.startOf("month").toISODate();
    }

    toggleSidebarButton() {
        if (this.uiService.isSmall || window.innerWidth < 1024) {
            this.tpState.sidebarOpenMobile = !this.tpState.sidebarOpenMobile;
        } else {
            this.tpState.sidebarOpenDesktop = !this.tpState.sidebarOpenDesktop;
        }
    }

    onSearchInput(ev) {
        this.tpState.searchQuery = ev.target.value || "";
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        this.searchTimer = setTimeout(async () => {
            if (this.tpState.viewMode === "agenda") {
                this.tpState.agendaPage = 1;
                await this.loadAgenda();
            } else if (this.tpState.searchQuery.trim()) {
                // Switch seamlessly to Agenda search results when searching by keyword
                this.tpState.viewMode = "agenda";
                this.tpState.agendaPage = 1;
                await this.loadAgenda();
            }
        }, 240);
    }

    clearSearch() {
        this.tpState.searchQuery = "";
        if (this.tpState.viewMode === "agenda") {
            this.tpState.agendaPage = 1;
            this.loadAgenda();
        }
    }

    async onToggleCalendarItem(calItem, ev) {
        const checked = Boolean(ev.target.checked);
        calItem.checked = checked;
        try {
            await this.orm.call("calendar.event", "tp_toggle_calendar_visibility", [
                calItem.calendar_user_id,
                checked,
            ]);
            await this.reloadCurrentView();
        } catch (err) {
            calItem.checked = !checked;
            this.tpState.bannerError = saveError(err, { verb: "bật/tắt hiển thị lịch" });
        }
    }

    async onAddColleagueFilter(items) {
        const picked = items?.[0];
        if (!picked?.partner_id) {
            return;
        }
        try {
            await this.orm.call("calendar.event", "tp_manage_colleague_filter", [
                "add",
                picked.partner_id,
                true,
            ]);
            await this.refreshSidebarBootstrap();
            await this.reloadCurrentView();
        } catch (err) {
            this.tpState.bannerError = saveError(err, { verb: "thêm bộ lọc đồng nghiệp" });
        }
    }

    async onToggleColleagueFilter(colItem, ev) {
        const active = Boolean(ev.target.checked);
        colItem.active = active;
        try {
            await this.orm.call("calendar.event", "tp_manage_colleague_filter", [
                "toggle",
                colItem.partner_id,
                active,
            ]);
            await this.reloadCurrentView();
        } catch (err) {
            colItem.active = !active;
        }
    }

    async onRemoveColleagueFilter(colItem) {
        try {
            await this.orm.call("calendar.event", "tp_manage_colleague_filter", [
                "remove",
                colItem.partner_id,
                false,
            ]);
            await this.refreshSidebarBootstrap();
            await this.reloadCurrentView();
        } catch (err) {
            this.tpState.bannerError = saveError(err, { verb: "gỡ đồng nghiệp khỏi bộ lọc" });
        }
    }

    async onCreateNewCalendar() {
        const clean = this.tpState.newCalName.trim();
        if (!clean || this.tpState.creatingCal) {
            return;
        }
        this.tpState.creatingCal = true;
        this.tpState.bannerError = null;
        try {
            const boot = await this.orm.call("calendar.event", "tp_create_user_calendar", [
                clean,
                Number(this.tpState.newCalColor || 2),
                this.tpState.newCalPrivacy || "public",
                this.tpState.newCalShareUsers.map((u) => u.user_id),
            ]);
            this.tpState.myCalendars = boot?.my_calendars || [];
            this.tpState.sharedCalendars = boot?.shared_calendars || [];
            this.tpState.newCalName = "";
            this.tpState.newCalShareUsers = [];
            this.tpState.showNewCalForm = false;
            this.notification.add(`Đã tạo lịch "${clean}".`, { type: "success" });
            await this.reloadCurrentView();
        } catch (err) {
            this.tpState.bannerError = saveError(err, { verb: "tạo lịch mới" });
        } finally {
            this.tpState.creatingCal = false;
        }
    }

    async reloadCurrentView() {
        if (this.tpState.viewMode === "agenda") {
            await this.loadAgenda();
        } else {
            await this.model.load();
        }
    }

    async loadAgenda() {
        const seq = ++this.agendaSeq;
        this.tpState.agendaLoading = true;
        this.tpState.bannerError = null;
        try {
            const checkedCalIds = [
                ...this.tpState.myCalendars.filter((c) => c.checked).map((c) => c.id),
                ...this.tpState.sharedCalendars.filter((c) => c.checked).map((c) => c.id),
            ];
            const activePartnerIds = this.tpState.colleagueFilters
                .filter((f) => f.active)
                .map((f) => f.partner_id);
            const res = await this.orm.call("calendar.event", "tp_get_calendar_agenda", [
                {
                    q: this.tpState.searchQuery.trim(),
                    date_from: this.tpState.agendaDateFrom,
                    date_to: this.tpState.agendaDateTo,
                    calendar_ids: checkedCalIds,
                    partner_ids: activePartnerIds,
                    response_state: this.tpState.agendaResponseState,
                    privacy: this.tpState.agendaPrivacy,
                    organizer_id: this.tpState.agendaOrganizer[0]?.user_id || 0,
                    page: this.tpState.agendaPage,
                    page_size: this.tpState.agendaPageSize,
                },
            ]);
            if (seq !== this.agendaSeq) {
                return;
            }
            this.tpState.agendaGroups = res?.groups || [];
            this.tpState.agendaTotal = res?.total_count || 0;
            this.tpState.agendaPage = res?.page || 1;
            if (!this.tpState.agendaDateFrom && res?.date_from) {
                this.tpState.agendaDateFrom = res.date_from;
            }
            if (!this.tpState.agendaDateTo && res?.date_to) {
                this.tpState.agendaDateTo = res.date_to;
            }
        } catch (err) {
            if (seq === this.agendaSeq) {
                this.tpState.bannerError = saveError(err, {
                    verb: "tải danh sách lịch làm việc",
                    write: false,
                });
            }
        } finally {
            if (seq === this.agendaSeq) {
                this.tpState.agendaLoading = false;
            }
        }
    }

    get activeAgendaFilterChips() {
        const chips = [];
        if (this.tpState.searchQuery.trim()) {
            chips.push({
                key: "q",
                label: `Từ khóa: "${this.tpState.searchQuery.trim()}"`,
                clear: () => {
                    this.tpState.searchQuery = "";
                },
            });
        }
        if (this.tpState.agendaResponseState) {
            const map = {
                accepted: "Đã chấp nhận",
                tentative: "Chưa chắc chắn",
                declined: "Đã từ chối",
                needsAction: "Chờ phản hồi",
            };
            chips.push({
                key: "rsvp",
                label: `Phản hồi: ${map[this.tpState.agendaResponseState] || ""}`,
                clear: () => {
                    this.tpState.agendaResponseState = "";
                },
            });
        }
        if (this.tpState.agendaPrivacy) {
            const map = {
                public: "Công khai nội bộ",
                confidential: "Chỉ nội bộ công ty",
                members_only: "Chỉ thành viên lịch",
                private: "Riêng tư",
            };
            chips.push({
                key: "priv",
                label: `Riêng tư: ${map[this.tpState.agendaPrivacy] || ""}`,
                clear: () => {
                    this.tpState.agendaPrivacy = "";
                },
            });
        }
        if (this.tpState.agendaOrganizer.length) {
            chips.push({
                key: "org",
                label: `Chủ trì: ${this.tpState.agendaOrganizer[0].name}`,
                clear: () => {
                    this.tpState.agendaOrganizer = [];
                },
            });
        }
        return chips;
    }

    async removeAgendaChip(chip) {
        chip.clear();
        this.tpState.agendaPage = 1;
        await this.loadAgenda();
    }

    async resetAgendaFilters() {
        const today = DateTime.local();
        this.tpState.searchQuery = "";
        this.tpState.agendaResponseState = "";
        this.tpState.agendaPrivacy = "";
        this.tpState.agendaOrganizer = [];
        this.tpState.agendaDateFrom = today.startOf("week").toISODate();
        this.tpState.agendaDateTo = today.plus({ days: 30 }).toISODate();
        this.tpState.agendaPage = 1;
        await this.loadAgenda();
    }

    get agendaTotalPages() {
        return Math.max(1, Math.ceil(this.tpState.agendaTotal / this.tpState.agendaPageSize));
    }

    async changeAgendaPage(nextPage) {
        const clamped = Math.max(1, Math.min(nextPage, this.agendaTotalPages));
        if (clamped === this.tpState.agendaPage) {
            return;
        }
        this.tpState.agendaPage = clamped;
        await this.loadAgenda();
    }

    async changeAgendaPageSize(ev) {
        this.tpState.agendaPageSize = Number(ev.target.value) || 20;
        this.tpState.agendaPage = 1;
        await this.loadAgenda();
    }

    // ------------------------------------------------------------------
    // Create / Edit / Deep-link Event Dialog overrides
    // ------------------------------------------------------------------
    onClickAddButton() {
        const baseDt = this.date || DateTime.local();
        const now = DateTime.local();
        const nextHour = Math.min(Math.max(now.hour + 1, 8), 16);
        const startDt = baseDt.set({ hour: nextHour, minute: 0, second: 0 });
        const stopDt = startDt.plus({ hours: 1 });
        this.openEventDialog(0, {
            allday: false,
            startIso: startDt.toFormat("yyyy-MM-dd'T'HH:mm"),
            stopIso: stopDt.toFormat("yyyy-MM-dd'T'HH:mm"),
            startDate: startDt.toISODate(),
            stopDate: stopDt.toISODate(),
        });
    }

    createRecord(record) {
        if (!this.model.canCreate) {
            return Promise.resolve();
        }
        const isAllDay = Boolean(record?.isAllDay);
        const startDt = record?.start || DateTime.local().plus({ hours: 1 }).startOf("hour");
        const endDt =
            record?.end && record.end.isValid
                ? record.end
                : isAllDay
                  ? startDt
                  : startDt.plus({ hours: 1 });
        return this.openEventDialog(0, {
            allday: isAllDay,
            startIso: startDt.toFormat("yyyy-MM-dd'T'HH:mm"),
            stopIso: endDt.toFormat("yyyy-MM-dd'T'HH:mm"),
            startDate: startDt.toISODate(),
            stopDate: endDt.toISODate(),
            title: record?.title || "",
        });
    }

    async editRecord(record) {
        const id = Number(record?.id || 0);
        if (!id) {
            return this.createRecord(record);
        }
        return this.openEventDialog(id, null);
    }

    async openDeepLinkedEvent(eventId) {
        try {
            const card = await this.orm.call("calendar.event", "tp_get_event_detail_card", [
                eventId,
            ]);
            if (card?.day_key && ["day", "week", "month"].includes(this.tpState.viewMode)) {
                await this.model.load({ date: DateTime.fromISO(card.day_key) });
            }
            await this.openEventDialog(eventId, null, true);
        } catch (err) {
            this.tpState.bannerError = saveError(err, {
                verb: "mở liên kết lịch làm việc",
                write: false,
            });
        }
    }

    openEventDialog(eventId, initialSlot = null, clearDeepLinkOnClose = false) {
        return new Promise((resolve) => {
            this.displayDialog(
                TpCalendarEventDialog,
                {
                    eventId: Number(eventId || 0),
                    initialSlot,
                    onSaved: async () => {
                        await this.reloadCurrentView();
                    },
                    onDeleted: async () => {
                        await this.reloadCurrentView();
                    },
                },
                {
                    onClose: () => {
                        if (
                            clearDeepLinkOnClose &&
                            /\/app\/ca-nhan\/lich-lam-viec\/\d+/.test(
                                browser.location?.pathname || ""
                            )
                        ) {
                            browser.history.replaceState({}, "", "/app/ca-nhan/lich-lam-viec");
                        }
                        resolve();
                    },
                }
            );
        });
    }

    async deleteRecord(record) {
        const id = Number(record?.id || 0);
        if (!id) {
            return;
        }
        if (!record?.rawRecord?.user_can_edit) {
            this.tpState.bannerError = {
                title: "Không có quyền xóa lịch",
                summary: "Chỉ người chủ trì hoặc chủ sở hữu lịch mới được xóa sự kiện này.",
                items: [],
            };
            return;
        }
        this.dialogService.add(ConfirmationDialog, {
            title: "Xóa sự kiện lịch",
            body: `Bạn có chắc chắn muốn xóa "${record.title || "sự kiện này"}" không?`,
            confirmLabel: "Xóa sự kiện",
            confirmClass: "btn-danger",
            cancelLabel: "Giữ lại",
            confirm: async () => {
                try {
                    await this.model.unlinkRecord(id);
                    this.notification.add("Đã xóa sự kiện.", { type: "success" });
                    if (this.tpState.viewMode === "agenda") {
                        await this.loadAgenda();
                    }
                } catch (err) {
                    this.tpState.bannerError = saveError(err, { verb: "xóa sự kiện" });
                }
            },
            cancel: () => {},
        });
    }

    onShareAgendaCard(card) {
        if (!card || card.is_masked_private) {
            return;
        }
        this.dialogService.add(TpShareToDiscussDialog, {
            targetModel: "calendar.event",
            targetId: card.id,
            targetTitle: card.name,
        });
    }

    async onQuickAgendaRsvp(card, statusKey) {
        try {
            await this.orm.call("calendar.event", "change_attendee_status", [
                [card.id],
                statusKey,
                card.recurrency ? "self_only" : false,
            ]);
            this.notification.add("Đã cập nhật phản hồi lời mời.", { type: "success" });
            await this.loadAgenda();
        } catch (err) {
            this.tpState.bannerError = saveError(err, { verb: "phản hồi lời mời" });
        }
    }
}

export const tpPersonalCalendarView = {
    ...attendeeCalendarView,
    Controller: TpPersonalCalendarController,
    Renderer: TpPersonalCalendarRenderer,
};

registry.category("views").add("tp_personal_calendar", tpPersonalCalendarView);
