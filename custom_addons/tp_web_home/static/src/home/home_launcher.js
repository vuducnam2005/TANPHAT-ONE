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

const EMPTY_DASHBOARD = Object.freeze({
    meta: {
        updated_at: "",
        updated_short: "",
        timezone: "Asia/Ho_Chi_Minh",
    },
    kpis: {
        hr: { key: "hr", label: "Nhân sự", status: "loading", count: null, can_open: false },
        requests: {
            key: "requests",
            label: "Yêu cầu phê duyệt",
            status: "loading",
            count: null,
            can_open: false,
        },
        tasks: { key: "tasks", label: "Công việc", status: "loading", count: null, can_open: false },
        stock: { key: "stock", label: "Tồn kho", status: "loading", count: null, can_open: false },
    },
    agenda: {
        status: "loading",
        items: [],
        total_today: 0,
        has_more: false,
    },
    charts: {
        status: "loading",
        total: 0,
        scope_key: "my_work",
        scope_label: "Công việc của tôi",
        scope_options: [{ key: "my_work", label: "Công việc của tôi" }],
        can_filter_department: false,
        department_key: "",
        department_label: "Tất cả phòng ban",
        department_options: [{ key: "", label: "Tất cả phòng ban" }],
        period_key: "this_month",
        period_label: "Tháng này",
        period_options: [
            { key: "this_month", label: "Tháng này" },
            { key: "this_month_strict", label: "Có hạn trong tháng" },
            { key: "this_week", label: "Tuần này" },
            { key: "this_quarter", label: "Quý này" },
            { key: "all", label: "Tất cả kỳ" },
        ],
        period_rule_note: "",
        attribution_note: "",
        bar: { rows: [], series: [] },
        donut: { center_count: 0, center_label: "Công việc", slices: [] },
    },
});

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
    static components = { Dropdown, DropdownItem, ErrorHandler, TpIdentityAvatar, InlineErrors };
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
    dashboard = signal(EMPTY_DASHBOARD);
    taskFilters = signal({
        period: "this_month",
        task_scope: "",
        department_key: "",
    });
    actionError = signal(null);

    brokenIcons = signal(new Set());
    selectedModule = signal(null);
    delegatedAdmin = signal(false);
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

    catalog = computed(() => {
        if (this.menuState() !== "ready") {
            return EMPTY_CATALOG;
        }
        const catalog = buildCatalog(this.menuService.getMenuAsTree("root"), {
            debug: odoo.debug,
            isSystem: Boolean(user.isSystem),
            isDelegated: this.delegatedAdmin(),
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

    drawerGroups = computed(() => buildDrawerGroups(this.catalog(), this.panelQuery()));
    panelTiles = computed(() =>
        filterTiles(this.catalog().userApps || [], this.panelQuery())
    );
    hasAppsDrawer = computed(
        () =>
            (this.catalog().entries?.length || 0) > 0 ||
            (this.catalog().userApps?.length || 0) > 0
    );

    // Navbar Global Search results (Chức năng + Tài liệu)
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
        const k = this.dashboard().kpis || EMPTY_DASHBOARD.kpis;
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

        // Optional mail.store & native MessagingMenu systray lookup (graceful when `mail` not installed in unit tests)
        this.mailStore = this.env.services?.["mail.store"] || null;
        const mailSystray = registry.category("systray").get("mail.messaging_menu", null);
        this.MessagingSystrayComponent = mailSystray?.Component || null;
        this.messagingSystrayProps = mailSystray?.props ? mailSystray.props() : {};

        // Chart.js hooks
        this.barChart = useHomeChart(() =>
            buildDepartmentBarSpec(this.dashboard().charts, (deptKey, segKey) =>
                this.onDrilldownBar(deptKey, segKey)
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

    barCanvasMinWidth() {
        const count = this.dashboard().charts?.bar?.rows?.length || 0;
        return count > 6 ? `${count * 84}px` : "100%";
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
        const hash = browser.location.hash || "";
        const match = hash.match(/(?:unit|detail)=([a-z0-9_-]+)/);
        let key = match ? match[1] : null;
        if (key === "tech") {
            key = "technical";
        }
        const found = key ? this.catalog().entries.find((m) => m.key === key && !m.menu) : null;
        if (found) {
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
        try {
            await this.menuService.reload();
            if (!this.destroyed && sequence === this.loadSequence) {
                this.syncHomeApp();
            }
            let capabilities = { delegated: false };
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
                    capabilities = { delegated: false };
                }
            }
            if (!this.menuService.getMenuAsTree("root")) {
                throw new Error("Missing menu root");
            }
            if (sequence === this.loadSequence) {
                this.delegatedAdmin.set(Boolean(capabilities.delegated));
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
        }
        const filters = this.taskFilters();
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
            if (data && typeof data === "object" && data.kpis) {
                this.dashboard.set(data);
                if (data.charts?.status === "ok") {
                    this.taskFilters.set({
                        period: data.charts.period_key || filters.period,
                        task_scope: data.charts.scope_key || "",
                        department_key: data.charts.department_key || "",
                    });
                }
                this.dashboardState.set("ready");
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
            period: ev.target.value || "this_month",
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
                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    res_model: doc.res_model,
                    res_id: doc.res_id,
                    views: [[false, "form"]],
                    view_mode: "form",
                });
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
                    const appMenu = this.menuService.getAll().find((m) => m.xmlid === dd.menu_xmlid);
                    if (appMenu) {
                        this.menuService.setCurrentMenu(appMenu);
                    }
                }
                await this.actionService.doAction(dd.action_xmlid);
                return;
            }
            if (dd.type === "rpc_action" && dd.method) {
                const args =
                    dd.method === "get_tp_home_task_drilldown_action"
                        ? [this.taskFilters()]
                        : [];
                const action = await rpc(`/web/dataset/call_kw/res.users/${dd.method}`, {
                    model: "res.users",
                    method: dd.method,
                    args,
                    kwargs: {},
                });
                if (action) {
                    if (card.key === "hr") {
                        const hrMenu = this.menuService
                            .getAll()
                            .find((m) => m.xmlid === "tp_hr_workspace.menu_hr");
                        if (hrMenu) {
                            this.menuService.setCurrentMenu(hrMenu);
                        }
                    } else if (card.key === "stock") {
                        const eqMenu = this.menuService
                            .getAll()
                            .find((m) => m.xmlid === "tp_equipment.menu_root");
                        if (eqMenu) {
                            this.menuService.setCurrentMenu(eqMenu);
                        }
                    }
                    await this.actionService.doAction(action);
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

    async onDrilldownBar(departmentKey, segmentKey) {
        await this._executeTaskDrilldown({
            ...this.taskFilters(),
            bar_department_key: departmentKey || "",
            bar_segment: segmentKey || "",
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
                await this.actionService.doAction(action);
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
                    this.menuService.setCurrentMenu(todoMenu);
                    await this.actionService.doAction(todoMenu.actionID, {
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
                    this.menuService.setCurrentMenu(calMenu);
                    await this.actionService.doAction(calMenu.actionID, {
                        additionalContext: { active_id: item.res_id },
                    });
                    return;
                }
            }
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: item.res_model,
                res_id: item.res_id,
                views: [[false, "form"]],
                view_mode: "form",
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

    openPersonalShortcut(xmlid) {
        const menu = this.menuService.getAll().find((m) => m.xmlid === xmlid);
        if (menu) {
            this.agendaModalOpen.set(false);
            this.helpOpen.set(false);
            this.menuService.selectMenu(menu);
        }
    }

    hasMenuXmlid(xmlid) {
        return Boolean(this.menuService.getAll().find((m) => m.xmlid === xmlid && m.actionID));
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
