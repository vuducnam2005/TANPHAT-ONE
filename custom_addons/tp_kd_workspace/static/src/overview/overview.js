import { Component, onMounted, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import {
    kdPrefs,
    LAST_LEAF_KEY,
    PAGE_SIZE_OPTIONS,
    PROJECT_COLUMNS,
    REPORTS_XMLID,
    savePrefs,
} from "../prefs";
import { TpKdPrefs } from "../sidebar/sidebar";

import { statusTone } from "../table/status_badge";

const MODEL = "tp.kd.overview";
const TASK_TOP = 8;
const INTRO_MS = 900; // donut sweep 700ms; bars 480ms + 6 × 40ms stagger (< 800ms)
const DONUT_MIN = 1.2; // minimum visual arc (of 100) for a non-zero slice; numbers stay exact
const DONUT_GAP = 0.8;
const STATES = ["draft", "in_review", "returned"];
const STATE_META = {
    draft: { label: "Nháp", tone: "draft" },
    in_review: { label: "Đang rà soát", tone: "review" },
    returned: { label: "Trả lại", tone: "returned" },
};
const TASK_META = [
    { key: "done", label: "Hoàn thành", tone: "done" },
    { key: "overdue", label: "Đang mở quá hạn", tone: "warn" },
    { key: "open", label: "Đang mở còn lại", tone: "open" },
];
const BID_LABELS = {
    identified: "Đang tìm hiểu",
    preparation: "Đang chuẩn bị",
    submitted: "Đã khai báo nộp — chưa xác minh",
};
const CRED_META = [
    { key: "expired", tone: "returned" },
    { key: "soon", tone: "warn" },
    { key: "later", tone: "done" },
];
const TAB_LABELS = { review: "Chờ tôi rà soát", returned: "Trả lại cho tôi", due: "Sắp đến hạn / quá hạn" };
const LIST_LINKS = [
    { name: "projects", label: "Hồ sơ dự án" },
    { name: "opportunities", label: "Hồ sơ dự án và hồ sơ thầu" },
    { name: "contracts", label: "Hợp đồng — TP Contracts" },
    { name: "revisions", label: "Phiên bản hợp đồng" },
    { name: "tasks", label: "Kế hoạch và công việc" },
];
const SCALE_ITEMS = [
    {
        key: "projects",
        label: "Dự án",
        hint: "Dự án do KH-KD quản lý mà bạn được xem. Áp bộ lọc Dự án; không áp ngày và người phụ trách.",
    },
    {
        key: "contracts",
        label: "Hợp đồng",
        hint: "Hợp đồng mọi trạng thái trong các dự án đang chọn. Người phụ trách = người tạo hợp đồng; không áp bộ lọc ngày.",
    },
    {
        key: "revisions",
        label: "Phiên bản",
        hint: "Phiên bản hợp đồng mọi trạng thái rà soát trong các dự án đang chọn. Lọc ngày theo ngày ghi nhận phiên bản; không áp người phụ trách.",
    },
];
const DATE_NOTE =
    "Từ ngày/Đến ngày áp theo ngày riêng của từng nguồn: giao khoán, sản lượng, nghiệm thu, thanh toán, nghĩa vụ — ngày chứng từ; " +
    "kế hoạch định kỳ — ngày bắt đầu kỳ; năng lực/chứng chỉ — ngày hết hạn; công việc — hạn công việc; hồ sơ dự án — hạn hồ sơ; " +
    "phiên bản hợp đồng — ngày ghi nhận. Số dự án và hợp đồng không lọc theo ngày.";
const ACCESS_ERRORS = /AccessError|AccessDenied|SessionExpired/;
const PERCENT = new Intl.NumberFormat("vi-VN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const RATIO = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 });

let nextUid = 0;

function emptyFilters() {
    return { project_id: false, owner_id: false, date_from: false, date_to: false };
}

/**
 * orm.call returns the backend action as-is; only /web/dataset/call_button
 * runs the server-side clean_action that derives `views` from `view_mode`.
 * Do the same derivation here so window actions open the same views.
 */
function withViews(action) {
    if (action?.type !== "ir.actions.act_window" || action.views) {
        return action;
    }
    const modes = (action.view_mode || "list,form").split(",").map((m) => m.trim());
    const single = modes.length === 1 && action.view_id;
    const viewId = Array.isArray(action.view_id) ? action.view_id[0] : action.view_id;
    return {
        ...action,
        views: modes.map((m) => [single ? viewId : false, m === "tree" ? "list" : m]),
    };
}

function errorMessage(error, fallback = "Không tải được dữ liệu.") {
    return error?.data?.message || error?.message || fallback;
}

/** Access/session failures (Odoo JSON-RPC AccessError/AccessDenied/SessionExpired, code 100, HTTP 401/403). */
function isAccessError(error) {
    const name = error?.exceptionName || error?.data?.name || "";
    return error?.code === 100 || [401, 403].includes(error?.status) || ACCESS_ERRORS.test(name);
}

/**
 * KD-UI-004 Overview. Replaces only the rendering of the existing overview form action (js_class),
 * so the menu, action and deep links stay the same. Every number comes from tp.kd.overview helpers
 * that run with the user's rights; every click calls a whitelisted server action (action_kd_open /
 * action_kd_create / project.project action_kd_*). The client never adds money or mixes units.
 *
 * Consistency: `gen` is the filter generation (filter change, clear, refresh); each part (projects,
 * mine, detail, sources) also has its own `seq`. A response is applied only while both are current, so
 * an old answer never overwrites a newer one and a partial refresh never blocks the main loading flag.
 */
export class TpKdOverview extends Component {
    static template = "tp_kd_workspace.Overview";
    static components = { Dropdown, DropdownItem, InlineErrors, TpKdPrefs };

    props = useProps();
    prefs = kdPrefs;
    columns = PROJECT_COLUMNS;
    pageSizes = PAGE_SIZE_OPTIONS;
    workTone(work) {
        const models = { allocation: "tp.allocation", production: "tp.production", acceptance: "tp.acceptance", payment: "tp.payment.request", plan: "tp.periodic.plan", credential: "tp.credential", obligation: "tp.obligation", contract: "tp.contract.revision", opportunity: "crm.lead", task: "project.task" };
        const field = work.source === "contract" ? "review_state" : work.source === "opportunity" ? "kd_bid_state" : "state";
        return "tp_kd_badge tp_kd_tone_" + statusTone(models[work.source], field, work.state);
    }
    listLinks = LIST_LINKS;
    scaleItems = SCALE_ITEMS;
    states = STATES;
    stateMeta = STATE_META;
    taskMeta = TASK_META;
    bidLabels = BID_LABELS;
    tabLabels = TAB_LABELS;
    dateNote = DATE_NOTE;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.menu = useService("menu");
        this.uid = ++nextUid;
        this.gen = 0;
        this.seq = { projects: 0, mine: 0, detail: 0, sources: 0 };
        this.detailGen = { plan: -1, cred: -1 };
        this.introTimer = null;
        this.state = proxy({
            loading: true,
            stale: false,
            denied: false,
            error: "",
            dateError: "",
            actionErrors: [],
            actionError: null,
            actionAttempt: 0,
            data: null,
            filters: emptyFilters(),
            filtersOpen: false,
            detail: "plan",
            periodKind: "month",
            plan: null,
            cred: null,
            taskAll: false,
            sel: null,
            intro: false,
            busy: { projects: false, mine: false, detail: false, sources: false },
            projects: { search: "", order: "code asc", offset: 0, data: null },
            mine: { tab: "review", offset: 0, data: null },
            sourcesOpen: this.openedFromReports(),
            sources: null,
        });
        onWillStart(() => this.reload());
        onMounted(() => {
            this.mounted = true;
            this.armIntro();
        });
        onWillUnmount(() => browser.clearTimeout(this.introTimer));
    }

    openedFromReports() {
        try {
            const reports = this.menu.getAll().find((m) => m.xmlid === REPORTS_XMLID);
            const last = Number(browser.sessionStorage.getItem(LAST_LEAF_KEY)) || 0;
            return Boolean(reports && reports.id === last);
        } catch {
            return false;
        }
    }

    // ------------------------------------------------------------------ motion
    reducedMotion() {
        if (kdPrefs.motion === "reduced") {
            return true;
        }
        try {
            return browser.matchMedia("(prefers-reduced-motion: reduce)").matches;
        } catch {
            return false;
        }
    }

    /**
     * One intro per mount, when data is first shown: the class is set in the same render as the charts
     * (no painted frame before the sweep) and removed after INTRO_MS, so later patches never replay it.
     */
    startIntro() {
        if (this.introPlayed) {
            return;
        }
        this.introPlayed = true;
        if (this.reducedMotion()) {
            return;
        }
        this.state.intro = true;
        if (this.mounted) {
            this.armIntro();
        }
    }

    armIntro() {
        if (!this.state.intro) {
            return;
        }
        browser.clearTimeout(this.introTimer);
        this.introTimer = browser.setTimeout(() => {
            this.state.intro = false;
        }, INTRO_MS);
    }

    rootClass() {
        return {
            [this.props.className || ""]: Boolean(this.props.className),
            "is-intro": this.state.intro,
            "is-reduced": kdPrefs.motion === "reduced",
            "is-loading": this.state.loading && Boolean(this.state.data),
        };
    }

    // ------------------------------------------------------------------ data
    filters() {
        const f = this.state.filters;
        return {
            project_id: f.project_id || false,
            owner_id: f.owner_id || false,
            date_from: f.date_from || false,
            date_to: f.date_to || false,
        };
    }

    current(gen, kind, seq) {
        return gen === this.gen && (!kind || seq === this.seq[kind]);
    }

    /** New filter generation: main payload + first-screen tables; detail/sources load beside it. */
    async reload() {
        const filters = this.filters();
        if (filters.date_from && filters.date_to && filters.date_from > filters.date_to) {
            this.state.error = '"Từ ngày" không được lớn hơn "Đến ngày".';
            this.state.loading = false;
            return;
        }
        const gen = ++this.gen;
        const pSeq = ++this.seq.projects;
        const mSeq = ++this.seq.mine;
        this.state.loading = true;
        this.refreshPart("detail");
        if (this.state.sourcesOpen) {
            this.refreshPart("sources");
        } else {
            this.state.sources = null; // closed table: reload on next open with current filters
        }
        try {
            const [data, projects, mine] = await Promise.all([
                this.orm.call(MODEL, "get_kd_dashboard", [filters]),
                this.fetchProjects(filters),
                this.fetchMine(filters),
            ]);
            if (!this.current(gen)) {
                return;
            }
            Object.assign(this.state, { data, stale: false, denied: false, error: "" });
            if (pSeq === this.seq.projects) {
                this.state.projects.data = projects;
            }
            if (mSeq === this.seq.mine) {
                this.state.mine.data = mine;
            }
            this.startIntro();
        } catch (error) {
            if (this.current(gen)) {
                this.fail(error, "main");
            }
        } finally {
            if (this.current(gen)) {
                this.state.loading = false;
                if (pSeq === this.seq.projects) {
                    this.state.busy.projects = false;
                }
                if (mSeq === this.seq.mine) {
                    this.state.busy.mine = false;
                }
            }
        }
    }

    fetchProjects(filters = this.filters()) {
        const p = this.state.projects;
        return this.orm.call(MODEL, "get_kd_project_rows", [filters, p.search, p.order, p.offset, kdPrefs.pageSize]);
    }

    fetchMine(filters = this.filters()) {
        const m = this.state.mine;
        return this.orm.call(MODEL, "get_kd_my_work", [filters, m.tab, m.offset, kdPrefs.pageSize]);
    }

    fetchDetail(filters = this.filters()) {
        return this.state.detail === "plan"
            ? this.orm.call(MODEL, "get_kd_plan_compare", [filters, this.state.periodKind])
            : this.orm.call(MODEL, "get_kd_credential_expiry", [filters]);
    }

    fetchSources(filters = this.filters()) {
        return this.orm.call(MODEL, "get_kd_source_table", [filters]);
    }

    /** Partial refresh (table page, tab, detail chart, source table) guarded by gen + its own seq. */
    async refreshPart(kind) {
        const gen = this.gen;
        const seq = ++this.seq[kind];
        const detail = this.state.detail;
        const fetcher = { projects: "fetchProjects", mine: "fetchMine", detail: "fetchDetail", sources: "fetchSources" };
        this.state.busy[kind] = true;
        try {
            const result = await this[fetcher[kind]]();
            if (!this.current(gen, kind, seq)) {
                return;
            }
            if (kind === "detail") {
                this.state[detail] = result;
                this.detailGen[detail] = gen;
            } else if (kind === "sources") {
                this.state.sources = result;
            } else {
                this.state[kind].data = result;
            }
        } catch (error) {
            if (this.current(gen, kind, seq)) {
                this.fail(error, kind);
            }
        } finally {
            if (seq === this.seq[kind]) {
                this.state.busy[kind] = false;
            }
        }
    }

    /**
     * Network/server error: keep what is shown; a failed main refresh marks it stale (the time of the
     * last good answer stays). Access/session error: wipe every number, table and detail; only the
     * message remains.
     */
    fail(error, part) {
        if (isAccessError(error)) {
            this.gen++;
            for (const kind of Object.keys(this.seq)) {
                this.seq[kind]++;
                this.state.busy[kind] = false;
            }
            this.detailGen = { plan: -1, cred: -1 };
            Object.assign(this.state, {
                data: null,
                plan: null,
                cred: null,
                sources: null,
                sel: null,
                loading: false,
                stale: false,
                denied: true,
                error: errorMessage(error, "Bạn không còn quyền xem dữ liệu này."),
            });
            this.state.projects.data = null;
            this.state.mine.data = null;
            return;
        }
        if (part === "main") {
            this.state.stale = Boolean(this.state.data);
        }
        this.state.error = errorMessage(error);
    }

    // ------------------------------------------------------------------ actions
    /**
     * FORM-VALIDATION-002: a failed open/create stays on the overview as an error block
     * (classified like a form save), never a vanishing toast; filters and numbers stay put.
     */
    async run(model, method, args, verb = "mở hồ sơ") {
        this.state.actionErrors = [];
        this.state.actionError = null;
        try {
            const action = await this.orm.call(model, method, args);
            await this.action.doAction(withViews(action));
        } catch (error) {
            this.state.actionError = saveError(error, { verb, write: false, note: "Bộ lọc và số liệu đang xem được giữ nguyên." });
            this.state.actionAttempt++;
        }
    }

    open(key, params = {}) {
        return this.run(MODEL, "action_kd_open", [key, this.filters(), params]);
    }

    create(kind) {
        if (kind === "task" && !this.state.filters.project_id) {
            // Same rule as action_kd_create; the server still checks it.
            this.state.filtersOpen = true;
            this.state.actionError = null;
            this.state.actionErrors = [{ id: "tp_kd_filter_project", label: "Dự án", location: "Bộ lọc",
                message: "Chọn Dự án trên Tổng quan trước khi thêm công việc / WBS." }];
            this.state.actionAttempt++;
            return;
        }
        return this.run(MODEL, "action_kd_create", [kind, this.state.filters.project_id || false], "thêm mới");
    }

    projectAction(method, projectId) {
        return this.run("project.project", method, [[projectId]]);
    }

    // ------------------------------------------------------------------ filters
    setFilter(key, ev) {
        const raw = ev.target.value;
        this.state.actionErrors = [];
        this.state.filters[key] = key.endsWith("_id") ? Number(raw) || false : raw || false;
        const f = this.state.filters;
        if (f.date_from && f.date_to && f.date_to < f.date_from) {
            // Same rule as the server (`_domain`); no request is sent for an impossible range.
            this.state.dateError = "Đến ngày phải từ ngày bắt đầu trở đi.";
            return;
        }
        this.state.dateError = "";
        this.state.projects.offset = 0;
        this.state.mine.offset = 0;
        this.reload();
    }

    clearFilters() {
        this.state.filters = emptyFilters();
        this.state.dateError = "";
        this.state.projects.offset = 0;
        this.state.projects.search = "";
        this.state.mine.offset = 0;
        this.reload();
    }

    activeFilters() {
        const f = this.state.filters;
        return [f.project_id, f.owner_id, f.date_from, f.date_to].filter(Boolean).length;
    }

    hasFilters() {
        return Boolean(this.activeFilters() || this.state.projects.search || this.state.dateError);
    }

    toggleFilters() {
        this.state.filtersOpen = !this.state.filtersOpen;
    }

    formatWindow(window) {
        return window ? `${this.formatDate(window.from)} – ${this.formatDate(window.to)}` : "";
    }

    // ------------------------------------------------------------------ D01 donut + D02 bars
    percent(value, total) {
        return total ? `${PERCENT.format((value * 100) / total)}%` : "0%";
    }

    /** Visual arcs only (pathLength 100). Legend and centre always show the exact counts. */
    donut(parts) {
        const live = parts.filter((p) => p.value > 0);
        const total = live.reduce((sum, p) => sum + p.value, 0);
        if (!total) {
            return [];
        }
        const small = live.filter((p) => (p.value * 100) / total < DONUT_MIN);
        const bigTotal = total - small.reduce((sum, p) => sum + p.value, 0);
        const room = 100 - small.length * DONUT_MIN;
        const gap = live.length > 1 ? DONUT_GAP : 0;
        let start = 0;
        return live.map((p) => {
            const arc = small.includes(p) ? DONUT_MIN : (p.value * room) / bigTotal;
            const len = Math.max(arc - gap, 0.4);
            const slice = { ...p, dash: `${len.toFixed(3)} ${(100 - len).toFixed(3)}`, offset: (-start).toFixed(3) };
            start += arc;
            return slice;
        });
    }

    g01Parts() {
        const totals = this.state.data.g01.totals;
        return STATES.map((s) => ({ key: s, value: totals[s], tone: STATE_META[s].tone }));
    }

    g01Info() {
        const rows = this.state.data.g01.rows;
        const blocked = rows.filter((r) => !r.available).length;
        return { blocked, none: blocked === rows.length, total: this.state.data.g01.totals.total };
    }

    select(state) {
        this.state.sel = this.state.sel === state ? null : state;
    }

    clearSelection() {
        this.state.sel = null;
    }

    onPairKey(ev) {
        if (ev.key === "Escape" && this.state.sel) {
            ev.stopPropagation();
            this.clearSelection();
        }
    }

    barMax(rows, key = "total") {
        return Math.max(1, ...rows.map((r) => r[key]));
    }

    width(value, max) {
        return max ? `${Math.max((value * 100) / max, value ? 1.5 : 0).toFixed(2)}%` : "0%";
    }

    // ------------------------------------------------------------------ D03 tasks / D04 opportunities
    taskRows() {
        const rows = this.state.data?.g02.rows || [];
        return this.state.taskAll ? rows : rows.slice(0, TASK_TOP);
    }

    toggleTasks() {
        this.state.taskAll = !this.state.taskAll;
    }

    leadMax() {
        const g = this.state.data?.g03;
        return g ? Math.max(1, g.direct, ...Object.values(g.bid)) : 1;
    }

    // ------------------------------------------------------------------ D05 plan / D06 credential (lazy)
    setDetail(detail) {
        if (this.state.detail === detail) {
            return;
        }
        this.state.detail = detail;
        if (this.detailGen[detail] !== this.gen) {
            this.refreshPart("detail");
        }
    }

    onDetailKey(ev) {
        if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(ev.key)) {
            ev.preventDefault();
            const next = this.state.detail === "plan" ? "cred" : "plan";
            const target = ev.key === "Home" ? "plan" : ev.key === "End" ? "cred" : next;
            this.setDetail(target);
            ev.currentTarget.querySelector(`#tp_kd_tab_${target}`)?.focus();
        }
    }

    setPeriod(ev) {
        this.state.periodKind = ev.target.value;
        this.detailGen.plan = -1;
        this.refreshPart("detail");
    }

    /** Bars of one plan row on that row's own scale (same currency/basis); from the server ratio. */
    planBars(row) {
        if (row.ratio !== null && row.ratio !== undefined) {
            return row.ratio <= 100
                ? { target: 100, source: row.ratio }
                : { target: 10000 / row.ratio, source: 100 };
        }
        return { target: row.target_bar ? 100 : 0, source: row.source_bar ? 100 : 0 };
    }

    /** Server ratio (already rounded to 1 decimal) written the Vietnamese way: 17,5%. */
    ratioText(ratio) {
        return `${RATIO.format(ratio)}%`;
    }

    planTone(row) {
        if (row.status !== "comparable" || row.ratio === null) {
            return "muted";
        }
        return row.ratio >= 100 ? "done" : row.ratio >= 70 ? "info" : "warn";
    }

    credParts() {
        const b = this.state.cred.buckets;
        return CRED_META.map((m) => ({ key: m.key, value: b[m.key], tone: m.tone }));
    }

    credLabel(key) {
        const bounds = this.state.cred?.bounds;
        if (!bounds) {
            return key;
        }
        return {
            expired: `Đã hết hạn (trước ${this.formatDate(bounds.today)})`,
            soon: `Hôm nay – 30 ngày (${this.formatDate(bounds.today)} – ${this.formatDate(bounds.soon_until)})`,
            later: `Sau 30 ngày (sau ${this.formatDate(bounds.soon_until)})`,
        }[key];
    }

    credTotal() {
        const b = this.state.cred?.buckets;
        return b ? b.expired + b.soon + b.later : 0;
    }

    // ------------------------------------------------------------------ project table
    hasColumn(key) {
        return kdPrefs.columns.includes(key);
    }

    toggleColumn(key) {
        const columns = this.hasColumn(key)
            ? kdPrefs.columns.filter((k) => k !== key)
            : [...kdPrefs.columns, key];
        savePrefs({ columns });
    }

    sortBy(key) {
        const [field, dir] = this.state.projects.order.split(" ");
        this.state.projects.order = `${key} ${field === key && dir === "asc" ? "desc" : "asc"}`;
        this.state.projects.offset = 0;
        this.refreshPart("projects");
    }

    sortState(key) {
        const [field, dir] = this.state.projects.order.split(" ");
        return field === key ? (dir === "asc" ? "ascending" : "descending") : "none";
    }

    onProjectSearch(ev) {
        this.state.projects.search = ev.target.value;
        this.state.projects.offset = 0;
        this.refreshPart("projects");
    }

    onProjectSearchKey(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onProjectSearch(ev);
        }
    }

    page(kind, delta) {
        const part = this.state[kind];
        const total = part.data?.total || 0;
        const offset = part.offset + delta * kdPrefs.pageSize;
        if (offset < 0 || offset >= total || (kind === "mine" && offset + kdPrefs.pageSize > 500)) {
            return;
        }
        part.offset = offset;
        this.refreshPart(kind);
    }

    setPageSize(ev) {
        savePrefs({ pageSize: Number(ev.target.value) });
        this.state.projects.offset = 0;
        this.state.mine.offset = 0;
        this.refreshPart("projects");
        this.refreshPart("mine");
    }

    range(kind) {
        const part = this.state[kind];
        const total = part.data?.total || 0;
        if (!total) {
            return "0";
        }
        const end = Math.min(part.offset + kdPrefs.pageSize, total);
        return `${part.offset + 1}–${end} / ${total}`;
    }

    canPage(kind, delta) {
        const part = this.state[kind];
        const offset = part.offset + delta * kdPrefs.pageSize;
        return offset >= 0 && offset < (part.data?.total || 0) &&
            (kind !== "mine" || offset + kdPrefs.pageSize <= 500);
    }

    // ------------------------------------------------------------------ my work
    setTab(tab, reveal = false) {
        if (this.state.mine.tab !== tab) {
            this.state.mine.tab = tab;
            this.state.mine.offset = 0;
            this.refreshPart("mine");
        }
        if (reveal) {
            // KPI click: bring "Việc của tôi" into view and move focus there (one-shot, no polling).
            const section = document.getElementById("tp_kd_mine");
            section?.scrollIntoView({ block: "start", behavior: this.reducedMotion() ? "auto" : "smooth" });
            section?.focus({ preventScroll: true });
        }
    }

    tabCount(tab) {
        const k = this.state.data?.kpis;
        if (!k) {
            return 0;
        }
        return tab === "due" ? k.due + k.overdue : k[tab];
    }

    // ------------------------------------------------------------------ source table
    toggleSources() {
        this.state.sourcesOpen = !this.state.sourcesOpen;
        if (this.state.sourcesOpen && !this.state.sources) {
            this.refreshPart("sources");
        }
    }

    formatDate(value) {
        if (!value) {
            return "";
        }
        const [y, m, d] = value.split("-");
        return `${d}/${m}/${y}`;
    }
}

registry.category("views").add("tp_kd_overview", {
    type: "form",
    Controller: TpKdOverview,
});
