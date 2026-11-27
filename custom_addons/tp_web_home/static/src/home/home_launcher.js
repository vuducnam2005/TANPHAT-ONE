import {
    Component,
    computed,
    onMounted,
    onWillDestroy,
    signal,
    useOnChange,
    useProps,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { hasTouch } from "@web/core/browser/feature_detection";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { ErrorHandler } from "@web/core/utils/components";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { session } from "@web/session";
import { TpIdentityAvatar } from "../identity/user_account_menu";
import { InlineErrors } from "../validation/inline_errors";
import { saveError } from "../validation/validation";
import { TpAppSwitcher } from "./app_switcher";
import {
    buildCatalog,
    buildDrawerGroups,
    filterTiles,
    HOME_MENU_XMLID,
    homeSections,
    monogram,
} from "./home_catalog";
import {
    buildDepartmentBarSpec,
    buildStatusDonutSpec,
    useHomeChart,
} from "./home_charts";

const EMPTY_CATALOG = Object.freeze({
    isAdmin: false,
    isDelegated: false,
    homeMode: "employee",
    admin: null,
    tools: [],
    entries: [],
    home: [],
    system: [],
    all: [],
    userApps: [],
    extraUserApps: [],
    quickGrid: [],
    searchableFunctions: [],
    otherApps: 0,
});

function buildInitialEmptyDashboard(isAdminHint = false) {
    if (isAdminHint) {
        return {
            home_mode: "admin",
            apps_title: "Ứng dụng theo phòng ban",
            meta: { updated_at: "", updated_short: "", timezone: "Asia/Ho_Chi_Minh" },
            cards: [
                { key: "hr", card_kind: "metric", label: "Nhân sự", status: "loading", count: null, can_open: false, theme: "blue", icon_name: "kpi-hr" },
                { key: "requests", card_kind: "metric", label: "Yêu cầu phê duyệt", status: "loading", count: null, can_open: false, theme: "purple", icon_name: "kpi-requests" },
                { key: "tasks", card_kind: "metric", label: "Công việc", status: "loading", count: null, can_open: false, theme: "green", icon_name: "kpi-tasks" },
                { key: "stock", card_kind: "metric", label: "Tồn kho", status: "loading", count: null, can_open: false, theme: "amber", icon_name: "kpi-stock" },
            ],
            kpis: {},
            agenda: { status: "loading", items: [], total_today: 0, has_more: false },
            charts: {
                status: "loading",
                mode: "admin",
                total: 0,
                scope_key: "managed",
                scope_label: "Phạm vi quản lý",
                scope_options: [{ key: "managed", label: "Phạm vi quản lý" }],
                can_filter_department: false,
                department_key: "",
                department_label: "Tất cả phòng ban",
                department_options: [{ key: "", label: "Tất cả phòng ban" }],
                period_key: "this_month",
                period_label: "Trong tháng này",
                period_options: [
                    { key: "this_week", label: "Trong tuần này" },
                    { key: "this_month", label: "Trong tháng này" },
                    { key: "all", label: "Tất cả kỳ" },
                ],
                bar: { kind: "department", title: "Tình hình công việc", rows: [], series: [] },
                donut: { title: "Tỷ lệ công việc", center_count: 0, center_label: "Công việc", slices: [] },
            },
        };
    }
    return {
        home_mode: "employee",
        apps_title: "Ứng dụng của bạn",
        meta: { updated_at: "", updated_short: "", timezone: "Asia/Ho_Chi_Minh" },
        cards: [
            { key: "emp_tasks", card_kind: "metric", label: "Việc chưa hoàn thành", status: "loading", count: null, can_open: false, theme: "blue", icon_name: "kpi-tasks" },
            { key: "emp_requests", card_kind: "metric", label: "Yêu cầu của tôi chờ duyệt", status: "loading", count: null, can_open: false, theme: "purple", icon_name: "kpi-requests" },
            { key: "emp_calendar", card_kind: "metric", label: "Lịch hẹn hôm nay", status: "loading", count: null, can_open: false, theme: "green", icon_name: "calendar" },
            { key: "emp_attendance", card_kind: "status", label: "Chấm công hôm nay", status: "loading", count: null, display_text: "", can_open: false, theme: "amber", icon_name: "clock" },
        ],
        kpis: {},
        agenda: { status: "loading", items: [], total_today: 0, has_more: false },
        charts: {
            status: "loading",
            mode: "employee",
            total: 0,
            scope_key: "my_work",
            scope_label: "Công việc của tôi",
            scope_options: [{ key: "my_work", label: "Công việc của tôi" }],
            can_filter_department: false,
            department_key: "",
            department_label: "Tất cả phòng ban",
            department_options: [{ key: "", label: "Tất cả phòng ban" }],
            period_key: "this_week",
            period_label: "Trong tuần này",
            period_options: [
                { key: "this_week", label: "Trong tuần này" },
                { key: "this_month", label: "Trong tháng này" },
                { key: "all", label: "Tất cả kỳ" },
            ],
            bar: { kind: "daily", title: "Công việc của tôi theo ngày", rows: [], series: [] },
            donut: { title: "Tỷ lệ công việc của tôi", center_count: 0, center_label: "Công việc", slices: [] },
        },
    };
}

const VI_NUMBER = new Intl.NumberFormat("vi-VN");

/** A click the browser should handle itself (new tab/window, download, non-primary button). */
export function isModifiedClick(ev) {
    return ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0;
}

/** True while an IME is composing: Enter/Escape then belong to the input method. */
function isComposing(ev, composing) {
    return ev.isComposing || composing || ev.keyCode === 229;
}

export class HomeLauncher extends Component {
    static template = "tp_web_home.HomeLauncher";
    static components = {
        Dropdown,
        DropdownItem,
        ErrorHandler,
        TpIdentityAvatar,
        InlineErrors,
        TpAppSwitcher,
    };
    props = useProps({ ...standardActionServiceProps });

    // Search, Drawers & Overlays
    query = signal("");
    searchFocused = signal(false);
    docResults = signal([]);
    docLoading = signal(false);
    activeSearchIdx = signal(-1);

    panelQuery = signal("");
    panelOpen = signal(false);
    navDrawerOpen = signal(false);
    helpOpen = signal(false);
    agendaModalOpen = signal(false);
    agendaPageData = signal(null);
    agendaPageLoading = signal(false);

    // Core Home & Dashboard state
    menuState = signal("loading");
    dashboardState = signal("loading");
    dashboard = signal(buildInitialEmptyDashboard(Boolean(user.isSystem)));
    taskFilters = signal({
        period: "",
        task_scope: "",
        department_key: "",
    });
    actionError = signal(null);

    brokenIcons = signal(new Set());
    selectedModule = signal(null);
    delegatedAdmin = signal(false);
    serverFullAdmin = signal(null);
    bellSystrayFailed = signal(false);

    // Refs for keyboard focus management
    searchInput = signal.ref();
    panelInput = signal.ref();
    panelToggle = signal.ref();
    panelTitle = signal.ref();
    hamburgerBtn = signal.ref();
    navCloseBtn = signal.ref();
    helpBtn = signal.ref();
    helpCloseBtn = signal.ref();
    agendaAllBtn = signal.ref();
    agendaCloseBtn = signal.ref();
    detailTitleRef = signal.ref();

    loadSequence = 0;
    dashboardSeq = 0;
    docSearchSeq = 0;
    docSearchTimer = null;
    busRefreshTimer = null;
    composing = false;
    focusPanel = false;
    focusNavDrawer = false;
    focusHelp = false;
    focusAgendaModal = false;
    lastClickedModuleKey = null;

    /**
     * Authoritative Home Mode ("admin" vs "employee"):
     * - When dashboard payload has arrived from server, uses `dashboard().home_mode`.
     * - Otherwise uses server `get_tp_admin_capabilities` (if available) or `user.isSystem`.
     */
    effectiveIsAdmin = computed(() => {
        if (this.dashboardState() === "ready" && this.dashboard()?.home_mode) {
            return this.dashboard().home_mode === "admin";
        }
        const srv = this.serverFullAdmin();
        if (srv !== null) {
            return Boolean(srv);
        }
        return Boolean(user.isSystem);
    });

    homeMode = computed(() => {
        if (this.effectiveIsAdmin() || this.delegatedAdmin()) {
            return "admin";
        }
        return "employee";
    });

    catalog = computed(() => {
        if (this.menuState() !== "ready") {
            return EMPTY_CATALOG;
        }
        const isSys = this.effectiveIsAdmin();
        const mode = this.homeMode();
        const catalog = buildCatalog(this.menuService.getMenuAsTree("root"), {
            debug: odoo.debug,
            isSystem: isSys,
            isDelegated: this.delegatedAdmin(),
            homeMode: mode,
        });
        const broken = this.brokenIcons();
        const fix = (tile) =>
            broken.has(tile.key)
                ? { ...tile, icon: { type: "monogram", text: monogram(tile.label || tile.name) } }
                : tile;
        return {
            ...catalog,
            home: catalog.home.map(fix),
            system: catalog.system.map(fix),
            all: catalog.all.map(fix),
            userApps: catalog.userApps.map(fix),
            extraUserApps: catalog.extraUserApps.map(fix),
        };
    });

    tools = computed(() => this.catalog().tools || []);
    sections = computed(() => homeSections(this.catalog(), this.query()));
    visibleEntries = computed(() => this.sections().flatMap((section) => section.tiles));
    quickGridTiles = computed(() => this.catalog().quickGrid || []);

    appsPanelTitle = computed(() => {
        if (this.dashboardState() === "ready" && this.dashboard()?.apps_title) {
            return this.dashboard().apps_title;
        }
        return this.homeMode() === "admin" ? "Ứng dụng theo phòng ban" : "Ứng dụng của bạn";
    });

    barChartTitle = computed(
        () =>
            this.dashboard().charts?.bar?.title ||
            (this.homeMode() === "admin" ? "Tình hình công việc" : "Công việc của tôi theo ngày")
    );

    donutChartTitle = computed(
        () =>
            this.dashboard().charts?.donut?.title ||
            (this.homeMode() === "admin" ? "Tỷ lệ công việc" : "Tỷ lệ công việc của tôi")
    );

    drawerGroups = computed(() => buildDrawerGroups(this.catalog(), this.panelQuery()));
    panelTiles = computed(() =>
        filterTiles(this.catalog().userApps || [], this.panelQuery())
    );
    hasAppsDrawer = computed(
        () =>
            (this.catalog().entries?.length || 0) > 0 ||
            (this.catalog().userApps?.length || 0) > 0
    );

    matchedFunctions = computed(() => {
        const q = this.query().trim();
        if (!q || this.menuState() !== "ready") {
            return [];
        }
        return filterTiles(this.catalog().searchableFunctions || [], q).slice(0, 8);
    });

    combinedSearchItems = computed(() => {
        const funcs = this.matchedFunctions().map((item) => ({
            kind: "function",
            uid: `fn-${item.key || item.xmlid}`,
            item,
        }));
        const docs = (this.docResults() || []).map((doc) => ({
            kind: "document",
            uid: `doc-${doc.key}`,
            doc,
        }));
        return [...funcs, ...docs];
    });

    showSearchDropdown = computed(
        () => Boolean(this.searchFocused() && this.query().trim().length > 0)
    );

    selectedModuleItem = computed(() => {
        const key = this.selectedModule();
        if (!key) {
            return null;
        }
        return this.catalog().entries.find((m) => m.key === key && !m.menu) || null;
    });

    kpiCards = computed(() => {
        const dash = this.dashboard();
        if (Array.isArray(dash?.cards) && dash.cards.length) {
            return dash.cards.map((c) => ({
                ...c,
                iconName: c.icon_name || c.iconName || "kpi-tasks",
                theme: c.theme || "blue",
            }));
        }
        const k = dash?.kpis || {};
        if (k.emp_tasks || k.emp_attendance) {
            return [
                { ...k.emp_tasks, theme: "blue", iconName: "kpi-tasks" },
                { ...k.emp_requests, theme: "purple", iconName: "kpi-requests" },
                { ...k.emp_calendar, theme: "green", iconName: "calendar" },
                { ...k.emp_attendance, theme: "amber", iconName: "clock" },
            ];
        }
        return [
            { ...k.hr, theme: "blue", iconName: "kpi-hr" },
            { ...k.requests, theme: "purple", iconName: "kpi-requests" },
            { ...k.tasks, theme: "green", iconName: "kpi-tasks" },
            { ...k.stock, theme: "amber", iconName: "kpi-stock" },
        ];
    });

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.identity = useService("tp_identity");
        this.userDropdown = useDropdownState();
        this.bellDropdown = useDropdownState();

        this.mailStore = this.env.services?.["mail.store"] || null;
        const mailSystray = registry.category("systray").get("mail.messaging_menu", null);
        this.MessagingSystrayComponent = mailSystray?.Component || null;
        this.messagingSystrayProps = mailSystray?.props ? mailSystray.props() : {};

        this.barChart = useHomeChart(() =>
            buildDepartmentBarSpec(this.dashboard().charts, (hit) =>
                this.onDrilldownBar(hit)
            )
        );
        this.donutChart = useHomeChart(() =>
            buildStatusDonutSpec(this.dashboard().charts, (sliceKey) =>
                this.onDrilldownDonut(sliceKey)
            )
        );

        this.destroyed = false;
        this._unsubscribeBus = null;
        this._onHashChange = () => this.syncFromHash();
        this._onDocPointerDown = (ev) => {
            const rootEl = ev.target?.closest?.(".tp-home-search-wrap");
            if (!rootEl && this.searchFocused()) {
                this.searchFocused.set(false);
            }
        };

        onMounted(() => {
            if (document.body) {
                document.body.classList.add("o_tp_home_active");
            }
            this.syncHomeApp();
            this.syncFromHash();
            this.loadMenus();
            this.loadDashboard();
            this._attachRealtimeBus();
            browser.addEventListener("hashchange", this._onHashChange);
            browser.addEventListener("popstate", this._onHashChange);
            document.addEventListener("pointerdown", this._onDocPointerDown);
        });

        onWillDestroy(() => {
            this.destroyed = true;
            this.loadSequence++;
            this.dashboardSeq++;
            this.docSearchSeq++;
            if (this.docSearchTimer) {
                browser.clearTimeout(this.docSearchTimer);
            }
            if (this.busRefreshTimer) {
                browser.clearTimeout(this.busRefreshTimer);
            }
            if (typeof this._unsubscribeBus === "function") {
                this._unsubscribeBus();
                this._unsubscribeBus = null;
            }
            document.body?.classList?.remove("o_tp_home_active");
            browser.removeEventListener("hashchange", this._onHashChange);
            browser.removeEventListener("popstate", this._onHashChange);
            document.removeEventListener("pointerdown", this._onDocPointerDown);
        });

        useOnChange(
            () => [this.selectedModule() || "", Boolean(this.detailTitleRef())],
            (key, hasTitle) => {
                if (key && hasTitle) {
                    this.detailTitleRef()?.focus();
                }
            }
        );

        useOnChange(
            () => [Boolean(this.panelInput()), Boolean(this.panelTitle())],
            (hasInput, hasTitle) => {
                if (this.focusPanel && hasInput && hasTitle) {
                    this.focusPanel = false;
                    (hasTouch() ? this.panelTitle() : this.panelInput()).focus();
                }
            }
        );

        useOnChange(
            () => [Boolean(this.navCloseBtn())],
            (hasBtn) => {
                if (this.focusNavDrawer && hasBtn) {
                    this.focusNavDrawer = false;
                    this.navCloseBtn()?.focus();
                }
            }
        );

        useOnChange(
            () => [Boolean(this.helpCloseBtn())],
            (hasBtn) => {
                if (this.focusHelp && hasBtn) {
                    this.focusHelp = false;
                    this.helpCloseBtn()?.focus();
                }
            }
        );

        useOnChange(
            () => [Boolean(this.agendaCloseBtn())],
            (hasBtn) => {
                if (this.focusAgendaModal && hasBtn) {
                    this.focusAgendaModal = false;
                    this.agendaCloseBtn()?.focus();
                }
            }
        );
    }

    _attachRealtimeBus() {
        const bus = this.env.services?.bus_service;
        if (!bus || typeof bus.subscribe !== "function") {
            return;
        }
        const scheduleRefresh = () => {
            if (this.destroyed || document.hidden) {
                return;
            }
            if (this.busRefreshTimer) {
                browser.clearTimeout(this.busRefreshTimer);
            }
            this.busRefreshTimer = browser.setTimeout(() => {
                if (!this.destroyed) {
                    this.loadDashboard({ silent: true });
                }
            }, 900);
        };
        const unsub1 = bus.subscribe("tp_request/updated", scheduleRefresh);
        const unsub2 = bus.subscribe("tp_hr_attendance/correction_updated", scheduleRefresh);
        this._unsubscribeBus = () => {
            if (typeof unsub1 === "function") {
                unsub1();
            }
            if (typeof unsub2 === "function") {
                unsub2();
            }
        };
    }

    // ------------------------------------------------------------------
    // Formatting & Display Helpers
    // ------------------------------------------------------------------
    get displayUserName() {
        return this.identity?.name || user.name || user.login || "Người dùng";
    }

    get bellUnreadCount() {
        try {
            return Number(this.mailStore?.messagingMenu?.globalCounter || 0);
        } catch {
            return 0;
        }
    }

    formatCount(value) {
        if (typeof value !== "number" || Number.isNaN(value)) {
            return "—";
        }
        return VI_NUMBER.format(value);
    }

    barCanvasNeedsScroll() {
        const bar = this.dashboard().charts?.bar;
        const count = bar?.rows?.length || 0;
        if (bar?.kind === "daily") {
            return count > 14;
        }
        return count > 10;
    }

    barCanvasMinWidth() {
        const bar = this.dashboard().charts?.bar;
        const count = bar?.rows?.length || 0;
        if (bar?.kind === "daily") {
            return count > 14 ? `${count * 34}px` : "100%";
        }
        return count > 10 ? `${count * 64}px` : "100%";
    }

    resultMessage() {
        if (this.menuState() === "loading") {
            return "Đang tải không gian làm việc…";
        }
        if (this.menuState() === "error") {
            return "Chưa tải được Trang chủ";
        }
        const q = this.query().trim();
        if (!q) {
            return `${this.quickGridTiles().length} lối vào nhanh trên Trang chủ`;
        }
        const total = this.combinedSearchItems().length;
        return total ? `Tìm thấy ${total} kết quả` : "Không có kết quả phù hợp";
    }

    emptyKind() {
        if (this.menuState() !== "ready") {
            return "";
        }
        if (this.quickGridTiles().length > 0) {
            return "";
        }
        return this.catalog().otherApps ? "switcher" : "none";
    }

    // ------------------------------------------------------------------
    // Menu & Dashboard Loading
    // ------------------------------------------------------------------
    syncHomeApp() {
        if (this.destroyed) {
            return;
        }
        const home = this.menuService.getAll().find((m) => m.xmlid === HOME_MENU_XMLID);
        if (home && this.menuService.getCurrentApp()?.id !== home.id) {
            this.menuService.setCurrentMenu(home);
        }
    }

    syncFromHash() {
        if (this.menuState() !== "ready") {
            return;
        }
        let pendingKey = null;
        try {
            pendingKey = browser.sessionStorage?.getItem("tp_pending_home_unit") || null;
            if (pendingKey) {
                browser.sessionStorage?.removeItem("tp_pending_home_unit");
            }
        } catch {
            pendingKey = null;
        }
        const hash = browser.location.hash || "";
        const match = hash.match(/(?:unit|detail)=([a-z0-9_-]+)/);
        let key = match ? match[1] : pendingKey;
        if (key === "tech") {
            key = "technical";
        }
        const found = key ? this.catalog().entries.find((m) => m.key === key && !m.menu) : null;
        if (found) {
            if (pendingKey && !match) {
                try {
                    window.history?.replaceState(
                        window.history.state,
                        "",
                        `${browser.location.pathname}${browser.location.search}#unit=${found.key}`
                    );
                } catch {
                    // Ignore history API restrictions in test sandboxes
                }
            }
            this.selectedModule.set(found.key);
        } else if (this.selectedModule()) {
            this.selectedModule.set(null);
            if (this.lastClickedModuleKey) {
                const btn = document.querySelector(`[data-module="${this.lastClickedModuleKey}"]`);
                btn?.focus();
            }
        }
    }

    onBackClick() {
        const old = this.selectedModule();
        this.selectedModule.set(null);
        if (browser.location.hash) {
            browser.location.hash = "";
        }
        if (old) {
            const btn = document.querySelector(`[data-module="${old}"]`);
            btn?.focus();
        }
    }

    async loadMenus() {
        const sequence = ++this.loadSequence;
        this.menuState.set("loading");
        this.panelOpen.set(false);
        this.navDrawerOpen.set(false);
        this.panelQuery.set("");
        this.selectedModule.set(null);
        this.delegatedAdmin.set(false);
        this.serverFullAdmin.set(null);
        try {
            await this.menuService.reload();
            if (!this.destroyed && sequence === this.loadSequence) {
                this.syncHomeApp();
            }
            let capabilities = { delegated: false, is_full_admin: null };
            if (session.tp_admin_delegation) {
                try {
                    capabilities = await rpc(
                        "/web/dataset/call_kw/res.users/get_tp_admin_capabilities",
                        {
                            model: "res.users",
                            method: "get_tp_admin_capabilities",
                            args: [],
                            kwargs: {},
                        }
                    );
                } catch {
                    capabilities = { delegated: false, is_full_admin: null };
                }
            }
            if (!this.menuService.getMenuAsTree("root")) {
                throw new Error("Missing menu root");
            }
            if (sequence === this.loadSequence) {
                this.delegatedAdmin.set(Boolean(capabilities.delegated));
                if (typeof capabilities.is_full_admin === "boolean") {
                    this.serverFullAdmin.set(capabilities.is_full_admin);
                }
                this.menuState.set("ready");
                this.syncFromHash();
            }
        } catch {
            if (sequence === this.loadSequence) {
                this.menuState.set("error");
            }
        }
    }

    async loadDashboard({ silent = false } = {}) {
        const seq = ++this.dashboardSeq;
        this.actionError.set(null);
        if (!session.tp_home_dashboard) {
            this.dashboardState.set("unavailable");
            return;
        }
        if (!silent) {
            this.dashboardState.set("loading");
            this.dashboard.set(buildInitialEmptyDashboard(this.effectiveIsAdmin()));
        }
        const filters = this.taskFilters();
        const prevMode = this.dashboard()?.home_mode || "";
        try {
            const data = await rpc("/web/dataset/call_kw/res.users/get_tp_home_dashboard", {
                model: "res.users",
                method: "get_tp_home_dashboard",
                args: [filters],
                kwargs: {},
            });
            if (this.destroyed || seq !== this.dashboardSeq) {
                return;
            }
            if (data && typeof data === "object" && (data.kpis || data.cards)) {
                const nextMode = data.home_mode || (data.charts?.mode === "admin" ? "admin" : "");
                if (prevMode && nextMode && prevMode !== nextMode && filters.period) {
                    // Admin grant/revoke switched Home mode: reload once with clean default period/scope
                    this.taskFilters.set({ period: "", task_scope: "", department_key: "" });
                    this.dashboard.set(data);
                    this.dashboardState.set("ready");
                    this.loadDashboard({ silent: true });
                    return;
                }
                this.dashboard.set(data);
                if (data.charts?.status === "ok") {
                    this.taskFilters.set({
                        period: data.charts.period_key || filters.period,
                        task_scope: data.charts.scope_key || "",
                        department_key: data.charts.department_key || "",
                    });
                }
                this.dashboardState.set("ready");
                this.syncFromHash();
            } else {
                this.dashboardState.set("unavailable");
            }
        } catch {
            if (!this.destroyed && seq === this.dashboardSeq) {
                this.dashboardState.set("error");
            }
        }
    }

    onRetryAll() {
        this.loadMenus();
        this.loadDashboard();
    }

    onRefreshDashboard() {
        this.loadDashboard({ silent: this.dashboardState() === "ready" });
    }

    // ------------------------------------------------------------------
    // Task & Chart Filter Handlers
    // ------------------------------------------------------------------
    onPeriodChange(ev) {
        this.taskFilters.set({
            ...this.taskFilters(),
            period: ev.target.value || "",
        });
        this.loadDashboard({ silent: true });
    }

    onTaskScopeChange(ev) {
        this.taskFilters.set({
            ...this.taskFilters(),
            task_scope: ev.target.value || "",
            department_key: "",
        });
        this.loadDashboard({ silent: true });
    }

    onDepartmentFilterChange(ev) {
        this.taskFilters.set({
            ...this.taskFilters(),
            department_key: ev.target.value || "",
        });
        this.loadDashboard({ silent: true });
    }

    // ------------------------------------------------------------------
    // Navbar Search (Functions + Server Documents, IME-Safe)
    // ------------------------------------------------------------------
    onSearchFocus() {
        this.searchFocused.set(true);
    }

    onSearchInput(ev) {
        const val = ev.target.value;
        this.query.set(val);
        this.searchFocused.set(true);
        this.activeSearchIdx.set(-1);

        if (this.docSearchTimer) {
            browser.clearTimeout(this.docSearchTimer);
        }
        const trimmed = val.trim();
        if (!trimmed || !session.tp_home_dashboard) {
            this.docSearchSeq++;
            this.docResults.set([]);
            this.docLoading.set(false);
            return;
        }
        this.docLoading.set(true);
        const seq = ++this.docSearchSeq;
        this.docSearchTimer = browser.setTimeout(async () => {
            try {
                const res = await rpc("/web/dataset/call_kw/res.users/search_tp_home_global", {
                    model: "res.users",
                    method: "search_tp_home_global",
                    args: [trimmed, 6],
                    kwargs: {},
                });
                if (!this.destroyed && seq === this.docSearchSeq) {
                    this.docResults.set(Array.isArray(res?.documents) ? res.documents : []);
                    this.docLoading.set(false);
                }
            } catch {
                if (!this.destroyed && seq === this.docSearchSeq) {
                    this.docResults.set([]);
                    this.docLoading.set(false);
                }
            }
        }, 220);
    }

    onSearchKeydown(ev) {
        if (isComposing(ev, this.composing)) {
            return;
        }
        const items = this.combinedSearchItems();
        if (ev.key === "ArrowDown" && items.length) {
            ev.preventDefault();
            this.searchFocused.set(true);
            this.activeSearchIdx.set((this.activeSearchIdx() + 1) % items.length);
            return;
        }
        if (ev.key === "ArrowUp" && items.length) {
            ev.preventDefault();
            this.searchFocused.set(true);
            const cur = this.activeSearchIdx();
            this.activeSearchIdx.set(cur <= 0 ? items.length - 1 : cur - 1);
            return;
        }
        if (ev.key === "Escape") {
            if (this.query()) {
                ev.preventDefault();
                ev.stopPropagation();
                this.clearSearch();
            } else if (this.searchFocused()) {
                ev.preventDefault();
                this.searchFocused.set(false);
            }
            return;
        }
        if (ev.key === "Enter") {
            const idx = this.activeSearchIdx();
            const chosen = idx >= 0 && idx < items.length ? items[idx] : items[0];
            if (chosen) {
                ev.preventDefault();
                this.activateSearchResult(chosen);
            }
        }
    }

    onCompositionStart() {
        this.composing = true;
    }

    onCompositionEnd() {
        this.composing = false;
    }

    clearSearch() {
        this.query.set("");
        this.docResults.set([]);
        this.docLoading.set(false);
        this.activeSearchIdx.set(-1);
        this.searchInput()?.focus();
    }

    async activateSearchResult(entry) {
        this.searchFocused.set(false);
        if (entry.kind === "function") {
            this.activate(entry.item);
            return;
        }
        if (entry.kind === "document" && entry.doc) {
            await this.openDocumentHit(entry.doc);
        }
    }

    async _openCanonicalRecordForm(resModel, resId, options = {}) {
        const modelToXmlid = {
            "hr.employee": "tp_hr_workspace.action_employees",
            "hr.employee.public": "tp_hr_workspace.action_directory",
            "hr.department": "tp_hr_workspace.action_departments",
            "tp.contract": "tp_contract.action_tp_contracts_list",
            "project.project": "tp_kd_workspace.action_projects",
            "project.task": "tp_kd_workspace.action_tasks",
            "crm.lead": "tp_kd_workspace.action_opportunities",
            "tp.bid.package": "tp_kd_workspace.action_packages",
            "maintenance.equipment": "tp_equipment.action_equipment",
            "tp.equipment.move": "tp_equipment.action_moves",
            "tp.equipment.proposal": "tp_equipment.action_proposals",
            "tp.request": "tp_request.action_detail",
            "calendar.event": "calendar.action_calendar_event",
            "tp.report.document": "tp_reporting.action_personal",
            "tp.report.plan": "tp_reporting.action_plans",
        };
        const xmlid = modelToXmlid[resModel];
        if (xmlid) {
            try {
                const base = await this.actionService.loadAction(xmlid);
                if (base && base.type === "ir.actions.act_window") {
                    const formPair =
                        (base.views || []).find((v) => v[1] === "form") || [false, "form"];
                    await this.actionService.doAction(
                        {
                            ...base,
                            res_model: resModel,
                            res_id: resId,
                            views: [formPair],
                            view_mode: "form",
                        },
                        options
                    );
                    return;
                }
            } catch {
                // Fall back to direct act_window below if module action is inaccessible
            }
        }
        await this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: resModel,
                res_id: resId,
                views: [[false, "form"]],
                view_mode: "form",
            },
            options
        );
    }

    async openDocumentHit(doc) {
        this.actionError.set(null);
        try {
            if (doc.menu_xmlid) {
                const rootApp = this.menuService.getAll().find((m) => m.xmlid === doc.menu_xmlid);
                if (rootApp) {
                    this.menuService.setCurrentMenu(rootApp);
                }
            }
            if (doc.action_xmlid) {
                await this.actionService.doAction(doc.action_xmlid, {
                    additionalContext: doc.action_params || {},
                });
                return;
            }
            if (doc.res_model && doc.res_id) {
                await this._openCanonicalRecordForm(doc.res_model, doc.res_id);
            }
        } catch (error) {
            this.actionError.set(
                saveError(error, {
                    verb: "mở tài liệu",
                    write: false,
                    note: "Trạng thái Trang chủ đang xem được giữ nguyên.",
                })
            );
        }
    }

    // ------------------------------------------------------------------
    // Navigation, Shortcuts, KPI & Chart Drilldowns
    // ------------------------------------------------------------------
    activate(entry) {
        if (!entry) {
            return;
        }
        if (entry.kind === "panel") {
            this.openPanel();
        } else if (entry.menu) {
            this.panelOpen.set(false);
            this.navDrawerOpen.set(false);
            this.menuService.selectMenu(entry.menu);
        } else if (entry.placeholderOnly || !entry.menu) {
            this.panelOpen.set(false);
            this.navDrawerOpen.set(false);
            this.lastClickedModuleKey = entry.key;
            this.selectedModule.set(entry.key);
            browser.location.hash = `unit=${entry.key}`;
        }
    }

    onEntryClick(ev, entry) {
        if (entry?.menu && isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.activate(entry);
    }

    _activateModuleContext(appXmlid, leafXmlid = "") {
        const allMenus = this.menuService.getAll();
        const appMenu = appXmlid ? allMenus.find((m) => m.xmlid === appXmlid) : null;
        const leafMenu = leafXmlid ? allMenus.find((m) => m.xmlid === leafXmlid) : null;
        if (leafMenu?.id) {
            const lastLeafStorageMap = {
                "tp_hr_workspace.menu_hr": "tp_hr_ui:last_leaf",
                "tp_kd_workspace.menu_kd": "tp_kd_ui:last_leaf",
                "tp_equipment.menu_root": "tp_eq_ui:last_leaf",
                "tp_request.menu_root": "tp_req_ui:last_leaf",
                "tp_hr_attendance.menu_root": "tp_att_ui:last_leaf",
            };
            const storageKey = lastLeafStorageMap[appXmlid];
            if (storageKey) {
                try {
                    browser.sessionStorage?.setItem(storageKey, String(leafMenu.id));
                } catch {
                    // Ignore private mode / storage restrictions
                }
            }
        }
        const target = appMenu || (leafMenu?.appID ? this.menuService.getMenu?.(leafMenu.appID) || leafMenu : leafMenu);
        if (target) {
            this.menuService.setCurrentMenu(target);
        }
    }

    async onKpiClick(card) {
        if (!card?.can_open || !card.drilldown) {
            return;
        }
        this.actionError.set(null);
        const dd = card.drilldown;
        try {
            if (dd.type === "client_action" && dd.action_xmlid) {
                if (dd.request_mode) {
                    const storageKey = `tp_req_ui:${session?.db || "tp"}:${session?.uid || 0}:list:${dd.request_mode}`;
                    try {
                        browser.sessionStorage?.setItem(
                            storageKey,
                            JSON.stringify({ tab: dd.request_tab || "all", page: 1 })
                        );
                    } catch {
                        // Ignore storage quota / private mode
                    }
                }
                if (dd.menu_xmlid) {
                    this._activateModuleContext(dd.menu_xmlid, dd.leaf_xmlid || "");
                }
                await this.actionService.doAction(dd.action_xmlid, {
                    clearBreadcrumbs: true,
                    additionalContext: dd.attendance_today
                        ? { tp_focus_date: dd.attendance_today }
                        : {},
                });
                return;
            }
            if (dd.type === "rpc_action" && dd.method) {
                const args =
                    dd.method === "get_tp_home_task_drilldown_action"
                        ? [{ ...this.taskFilters(), ...(dd.params || {}) }]
                        : [];
                const action = await rpc(`/web/dataset/call_kw/res.users/${dd.method}`, {
                    model: "res.users",
                    method: dd.method,
                    args,
                    kwargs: {},
                });
                if (action) {
                    const ctx = action.context && typeof action.context === "object" ? action.context : {};
                    if (card.key === "hr") {
                        this._activateModuleContext(
                            "tp_hr_workspace.menu_hr",
                            ctx.tp_hr_leaf || "tp_hr_workspace.menu_employees"
                        );
                    } else if (card.key === "stock") {
                        this._activateModuleContext(
                            "tp_equipment.menu_root",
                            ctx.tp_eq_leaf || "tp_equipment.menu_equipment_all"
                        );
                    } else if (card.key === "tasks") {
                        const hasKd = this.menuService
                            .getAll()
                            .some((m) => m.xmlid === "tp_kd_workspace.menu_kd");
                        this._activateModuleContext(
                            hasKd ? "tp_kd_workspace.menu_kd" : "project.menu_main_pm",
                            ctx.tp_kd_leaf || "tp_kd_workspace.menu_tasks"
                        );
                    } else if (card.key === "emp_calendar") {
                        this._activateModuleContext(
                            "calendar.mail_menu_calendar",
                            "calendar.calendar_event_menu"
                        );
                    } else if (card.key === "emp_tasks") {
                        this._activateModuleContext("project_todo.menu_todo_todos");
                    }
                    await this.actionService.doAction(action, { clearBreadcrumbs: true });
                }
            }
        } catch (error) {
            this.actionError.set(
                saveError(error, {
                    verb: "mở danh sách chi tiết",
                    write: false,
                    note: "Bộ lọc và số liệu Trang chủ đang xem được giữ nguyên.",
                })
            );
        }
    }

    async onDrilldownBar(hit, legacySegment) {
        const payload =
            typeof hit === "object" && hit !== null
                ? hit
                : { departmentKey: hit || "", dayKey: "", segmentKey: legacySegment || "" };
        await this._executeTaskDrilldown({
            ...this.taskFilters(),
            bar_department_key: payload.departmentKey || "",
            bar_day_key: payload.dayKey || "",
            bar_segment: payload.segmentKey || "",
        });
    }

    async onDrilldownDonut(bucketKey) {
        if (!bucketKey) {
            return;
        }
        await this._executeTaskDrilldown({
            ...this.taskFilters(),
            donut_bucket: bucketKey,
        });
    }

    async _executeTaskDrilldown(drillParams) {
        this.actionError.set(null);
        try {
            const action = await rpc(
                "/web/dataset/call_kw/res.users/get_tp_home_task_drilldown_action",
                {
                    model: "res.users",
                    method: "get_tp_home_task_drilldown_action",
                    args: [drillParams],
                    kwargs: {},
                }
            );
            if (action) {
                const ctx = action.context && typeof action.context === "object" ? action.context : {};
                if (this.homeMode() === "employee") {
                    this._activateModuleContext("project_todo.menu_todo_todos");
                } else {
                    const hasKd = this.menuService
                        .getAll()
                        .some((m) => m.xmlid === "tp_kd_workspace.menu_kd");
                    this._activateModuleContext(
                        hasKd ? "tp_kd_workspace.menu_kd" : "project.menu_main_pm",
                        ctx.tp_kd_leaf || "tp_kd_workspace.menu_tasks"
                    );
                }
                await this.actionService.doAction(action, { clearBreadcrumbs: true });
            }
        } catch (error) {
            this.actionError.set(
                saveError(error, {
                    verb: "mở danh sách công việc",
                    write: false,
                    note: "Bộ lọc và biểu đồ đang xem được giữ nguyên.",
                })
            );
        }
    }

    // ------------------------------------------------------------------
    // Agenda Actions & Paginated Modal
    // ------------------------------------------------------------------
    async onAgendaItemClick(item) {
        if (!item) {
            return;
        }
        this.agendaModalOpen.set(false);
        this.actionError.set(null);
        try {
            if (item.kind === "task") {
                const todoMenu = this.menuService
                    .getAll()
                    .find((m) => m.xmlid === "project_todo.menu_todo_todos");
                if (todoMenu && item.route) {
                    this._activateModuleContext("project_todo.menu_todo_todos");
                    await this.actionService.doAction(todoMenu.actionID, {
                        clearBreadcrumbs: true,
                        additionalContext: { active_id: item.res_id },
                        props: { resId: item.res_id },
                    });
                    return;
                }
            } else if (item.kind === "meeting") {
                const calMenu = this.menuService
                    .getAll()
                    .find((m) => m.xmlid === "calendar.mail_menu_calendar");
                if (calMenu && item.route) {
                    this._activateModuleContext(
                        "calendar.mail_menu_calendar",
                        "calendar.calendar_event_menu"
                    );
                    await this.actionService.doAction(calMenu.actionID, {
                        clearBreadcrumbs: true,
                        additionalContext: { active_id: item.res_id },
                    });
                    return;
                }
            }
            await this._openCanonicalRecordForm(item.res_model, item.res_id, {
                clearBreadcrumbs: true,
            });
        } catch (error) {
            this.actionError.set(
                saveError(error, {
                    verb: "mở chi tiết mục hôm nay",
                    write: false,
                    note: "Danh sách trên Trang chủ được giữ nguyên.",
                })
            );
        }
    }

    async onOpenLinkedTask(ev, linkedTask) {
        ev.stopPropagation();
        if (!linkedTask?.id) {
            return;
        }
        await this.onAgendaItemClick({
            kind: "task",
            res_model: "project.task",
            res_id: linkedTask.id,
            route: linkedTask.route,
        });
    }

    async openCreateTaskShortcut() {
        const todoMenu = this.menuService
            .getAll()
            .find((m) => m.xmlid === "project_todo.menu_todo_todos" && m.actionID);
        if (!todoMenu) {
            return;
        }
        this.agendaModalOpen.set(false);
        this.helpOpen.set(false);
        this.actionError.set(null);
        this._activateModuleContext("project_todo.menu_todo_todos");
        try {
            const baseAction = await this.actionService.loadAction(todoMenu.actionID);
            if (baseAction && baseAction.type === "ir.actions.client") {
                await this.actionService.doAction(
                    {
                        ...baseAction,
                        params: { ...(baseAction.params || {}), resId: "new", openCreate: true },
                    },
                    {
                        clearBreadcrumbs: true,
                        additionalContext: { tp_open_create: true },
                        props: { resId: "new" },
                    }
                );
                return;
            }
            if (baseAction && typeof baseAction === "object") {
                const formPair =
                    (baseAction.views || []).find((v) => v[1] === "form") || [false, "form"];
                await this.actionService.doAction(
                    {
                        ...baseAction,
                        views: [formPair],
                        view_mode: "form",
                        res_id: false,
                        target: "current",
                    },
                    { clearBreadcrumbs: true }
                );
                return;
            }
            await this.actionService.doAction(todoMenu.actionID, {
                clearBreadcrumbs: true,
                additionalContext: { tp_open_create: true },
                props: { resId: "new" },
            });
        } catch (error) {
            this.actionError.set(
                saveError(error, {
                    verb: "mở biểu mẫu tạo việc mới",
                    write: false,
                    note: "Trang chủ đang xem được giữ nguyên.",
                })
            );
        }
    }

    _resolveMenuActionTarget(xmlid) {
        const all = this.menuService.getAll();
        const menu = all.find((m) => m.xmlid === xmlid);
        if (!menu) {
            return null;
        }
        if (menu.actionID) {
            return { appMenu: menu, leafMenu: menu };
        }
        const tree = this.menuService.getMenuAsTree(menu.id);
        const queue = [...(tree?.childrenTree || [])];
        while (queue.length) {
            const node = queue.shift();
            if (node?.actionID) {
                return { appMenu: menu, leafMenu: node };
            }
            if (node?.childrenTree?.length) {
                queue.push(...node.childrenTree);
            }
        }
        return null;
    }

    async openPersonalShortcut(xmlid) {
        const resolved = this._resolveMenuActionTarget(xmlid);
        if (!resolved) {
            return;
        }
        this.agendaModalOpen.set(false);
        this.helpOpen.set(false);
        this.actionError.set(null);
        const { appMenu, leafMenu } = resolved;
        this._activateModuleContext(appMenu.xmlid || xmlid, leafMenu.xmlid || "");
        try {
            await this.actionService.doAction(leafMenu.actionID, { clearBreadcrumbs: true });
        } catch {
            this.menuService.selectMenu(leafMenu);
        }
    }

    hasMenuXmlid(xmlid) {
        return Boolean(this._resolveMenuActionTarget(xmlid));
    }

    async openAgendaAllModal() {
        this.focusAgendaModal = true;
        this.agendaModalOpen.set(true);
        await this.loadAgendaModalPage(1);
    }

    async loadAgendaModalPage(page) {
        this.agendaPageLoading.set(true);
        try {
            const res = await rpc("/web/dataset/call_kw/res.users/get_tp_home_agenda_page", {
                model: "res.users",
                method: "get_tp_home_agenda_page",
                args: [page, 10],
                kwargs: {},
            });
            if (!this.destroyed) {
                this.agendaPageData.set(res);
            }
        } catch {
            if (!this.destroyed) {
                this.agendaPageData.set({ status: "error", items: [], total: 0, page: 1, max_page: 1 });
            }
        } finally {
            if (!this.destroyed) {
                this.agendaPageLoading.set(false);
            }
        }
    }

    closeAgendaModal() {
        this.focusAgendaModal = false;
        this.agendaModalOpen.set(false);
        this.agendaAllBtn()?.focus();
    }

    onAgendaModalKeydown(ev) {
        if (ev.key === "Escape" && !isComposing(ev, this.composing)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.closeAgendaModal();
        }
    }

    // ------------------------------------------------------------------
    // Drawers, All Apps Panel, Help & Identity Menu
    // ------------------------------------------------------------------
    toggleNavDrawer() {
        if (this.navDrawerOpen()) {
            this.closeNavDrawer();
        } else {
            this.panelOpen.set(false);
            this.helpOpen.set(false);
            this.panelQuery.set("");
            this.focusNavDrawer = true;
            this.navDrawerOpen.set(true);
        }
    }

    closeNavDrawer() {
        this.focusNavDrawer = false;
        this.navDrawerOpen.set(false);
        this.panelQuery.set("");
        this.hamburgerBtn()?.focus();
    }

    onNavDrawerKeydown(ev) {
        if (ev.key === "Escape" && !isComposing(ev, this.composing)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.closeNavDrawer();
        }
    }

    openPanel() {
        if (this.hasAppsDrawer()) {
            this.navDrawerOpen.set(false);
            this.helpOpen.set(false);
            this.focusPanel = true;
            this.panelQuery.set("");
            this.panelOpen.set(true);
        }
    }

    togglePanel() {
        if (this.panelOpen()) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    closePanel() {
        this.focusPanel = false;
        this.panelOpen.set(false);
        this.panelQuery.set("");
        (this.panelToggle() || this.searchInput())?.focus();
    }

    onPanelInput(ev) {
        this.panelQuery.set(ev.target.value);
    }

    clearPanelSearch() {
        this.panelQuery.set("");
        this.panelInput()?.focus();
    }

    onPanelKeydown(ev) {
        if (ev.key !== "Escape" || isComposing(ev, this.composing)) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        if (this.panelQuery() && ev.target === this.panelInput()) {
            this.clearPanelSearch();
        } else {
            this.closePanel();
        }
    }

    onPanelSearchKeydown(ev) {
        if (isComposing(ev, this.composing) || ev.key !== "Enter") {
            return;
        }
        const firstGroup = this.drawerGroups()[0];
        const firstItem = firstGroup?.items?.[0];
        if (firstItem) {
            ev.preventDefault();
            this.activate(firstItem);
        }
    }

    toggleHelp() {
        if (this.helpOpen()) {
            this.closeHelp();
        } else {
            this.panelOpen.set(false);
            this.navDrawerOpen.set(false);
            this.focusHelp = true;
            this.helpOpen.set(true);
        }
    }

    closeHelp() {
        this.focusHelp = false;
        this.helpOpen.set(false);
        this.helpBtn()?.focus();
    }

    onHelpKeydown(ev) {
        if (ev.key === "Escape" && !isComposing(ev, this.composing)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.closeHelp();
        }
    }

    async onOpenPersonalProfile() {
        this.userDropdown.close();
        this.helpOpen.set(false);
        await this.identity.openPersonalProfile();
    }

    async onOpenAccountSecurity() {
        this.userDropdown.close();
        this.helpOpen.set(false);
        await this.actionService.doAction("tp_web_login.action_account_security");
    }

    async onUserLogout() {
        this.userDropdown.close();
        await this.identity.logout();
    }

    onIconError(tile) {
        this.brokenIcons.set(new Set(this.brokenIcons()).add(tile.key));
    }

    onBellSystrayError() {
        this.bellSystrayFailed.set(true);
    }
}

registry.category("actions").add("tp_web_home.home", HomeLauncher);
