import {
    Component,
    computed,
    onPatched,
    onWillDestroy,
    proxy,
    signal,
    useEffect,
    usePlugin,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { UIPlugin } from "@web/core/ui/ui_plugin";
import { useBus, useService } from "@web/core/utils/hooks";
import { WebClient } from "@web/webclient/webclient";
import { TpUserAccountMenu } from "@tp_web_home/identity/user_account_menu";
import {
    fold,
    isModifiedClick,
    HR_APP_XMLID,
    hrPrefs,
    LAST_LEAF_KEY,
    resetPrefs,
    savePrefs,
} from "../prefs";

const GROUP_ICONS = {
    "tp_hr_workspace.menu_group_employees": "group",
    "tp_hr_workspace.menu_group_organization": "account_tree",
    "tp_hr_workspace.menu_group_records": "article",
    "tp_hr_workspace.menu_group_payment": "database",
    "tp_hr_workspace.menu_group_admin": "tune",
};
const BODY_CLASSES = [
    "o_tp_hr_shell",
    "o_tp_hr_rail",
    "o_tp_hr_mobile",
    "o_tp_hr_compact",
    "o_tp_hr_reduce_motion",
];
const FOCUSABLE = "a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex='-1'])";

function readLastLeaf(key = LAST_LEAF_KEY) {
    try {
        return Number(browser.sessionStorage.getItem(key)) || 0;
    } catch {
        return 0;
    }
}
export function writeLastLeaf(id, key = LAST_LEAF_KEY) {
    try {
        if (id) {
            browser.sessionStorage.setItem(key, String(id));
        } else {
            browser.sessionStorage.removeItem(key);
        }
    } catch {
        // sessionStorage unavailable: active leaf falls back to the first matching menu.
    }
}

/** Display options shared by the sidebar footer and the Overview toolbar. */
export class TpHrPrefs extends Component {
    static template = "tp_hr_workspace.Prefs";
    prefs = hrPrefs;

    setDensity(density) {
        savePrefs({ density });
    }
    setMotion(motion) {
        savePrefs({ motion });
    }
    toggleCollapsed() {
        savePrefs({ collapsed: !hrPrefs.collapsed });
    }
    reset() {
        resetPrefs();
    }
}

/**
 * Left navigation for the TP HR app. The tree comes only from the native menu service (already
 * filtered by groups on the server): no RPC, no hard-coded menu ID. Navigation goes through
 * menu.selectMenu, so unsaved-form handling and breadcrumbs stay native.
 */
const EMPTY_ICONS = {};
const HR_BODY_CLASSES = {
    shell: "o_tp_hr_shell",
    rail: "o_tp_hr_rail",
    mobile: "o_tp_hr_mobile",
    compact: "o_tp_hr_compact",
    reduceMotion: "o_tp_hr_reduce_motion",
};

export class TpHrSidebar extends Component {
    static template = "tp_hr_workspace.Sidebar";
    static components = { Dropdown, TpHrPrefs, TpUserAccountMenu };

    get appXmlid() {
        return HR_APP_XMLID;
    }
    get appTitle() {
        return "TP HR";
    }
    get appMark() {
        return "HR";
    }
    get appIcon() {
        return "";
    }
    get sidebarId() {
        return "tp_hr_sidebar";
    }
    get searchInputId() {
        return "tp_hr_function_search";
    }
    get lastLeafKey() {
        return LAST_LEAF_KEY;
    }
    get prefsComponent() {
        return TpHrPrefs;
    }
    get groupIcons() {
        return GROUP_ICONS;
    }
    get leafIcons() {
        return EMPTY_ICONS;
    }
    get bodyClassConfig() {
        return HR_BODY_CLASSES;
    }
    get prefs() {
        return hrPrefs;
    }
    saveAppPrefs(changes) {
        savePrefs(changes);
    }
    resetAppPrefs() {
        resetPrefs();
    }

    panel = signal.ref();
    search = signal.ref();

    app = computed(() => {
        const app = this.menu.getCurrentApp();
        return app && app.xmlid === this.appXmlid ? app : null;
    });
    mode = computed(() => {
        const size = this.ui.size();
        return size <= 1 ? "mobile" : size <= 3 ? "tablet" : "desktop";
    });
    rail = computed(
        () =>
            !this.state.drawer &&
            ((this.mode() === "tablet") || (this.mode() === "desktop" && this.prefs.collapsed))
    );
    entries = computed(() => {
        const app = this.app();
        if (!app) {
            return [];
        }
        const tree = this.menu.getMenuAsTree(app.id);
        const entries = [];
        for (const node of tree.childrenTree || []) {
            const leaves = (node.childrenTree || []).filter((child) => child.actionID);
            if (leaves.length) {
                entries.push({
                    type: "group",
                    id: node.id,
                    key: node.xmlid || String(node.id),
                    name: node.name,
                    icon: this.groupIcons[node.xmlid] || "apps",
                    leaves,
                });
            } else if (node.actionID) {
                entries.push({
                    type: "leaf",
                    id: node.id,
                    name: node.name,
                    leaf: node,
                    icon: this.leafIcons[node.xmlid] || "pie_chart",
                });
            }
        }
        return entries;
    });
    leaves = computed(() =>
        this.entries().flatMap((e) => (e.type === "leaf" ? [e.leaf] : e.leaves))
    );
    visible = computed(() => {
        const q = fold(this.state.query);
        if (!q) {
            return this.entries();
        }
        const result = [];
        for (const entry of this.entries()) {
            if (entry.type === "leaf") {
                if (fold(entry.name).includes(q)) {
                    result.push(entry);
                }
                continue;
            }
            const groupHit = fold(entry.name).includes(q);
            const leaves = entry.leaves.filter((l) => groupHit || fold(l.name).includes(q));
            if (leaves.length) {
                result.push({ ...entry, leaves });
            }
        }
        return result;
    });

    setup() {
        this.menu = useService("menu");
        this.action = useService("action");
        this.ui = usePlugin(UIPlugin); // size() is a signal: the layout follows breakpoints
        this.state = proxy({ query: "", drawer: false, active: 0 });
        this.focusAfterPatch = null;
        this.lastApp = null;
        this.pendingLeaf = 0;

        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.syncActive());
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.syncActive());
        useEffect(() => this.applyBodyClasses());
        onWillDestroy(() => document.body.classList.remove(...Object.values(this.bodyClassConfig)));
        onPatched(() => {
            const target = this.focusAfterPatch;
            this.focusAfterPatch = null;
            if (this.ui.activeElement() !== document) {
                return; // Native dialogs own focus, including while the drawer is being patched.
            }
            if (target === "panel") {
                this.panel()?.querySelector(FOCUSABLE)?.focus();
            } else if (target === "toggle") {
                document.querySelector(
                    `.o_tp_hr_menu_toggle[aria-controls="${this.sidebarId}"], #${this.sidebarId} .o_tp_hr_sb_collapse`
                )?.focus();
            }
        });
    }

    applyBodyClasses() {
        const on = Boolean(this.app());
        const body = document.body;
        const cls = this.bodyClassConfig;
        const prefs = this.prefs;
        body.classList.toggle(cls.shell, on);
        body.classList.toggle(cls.rail, on && this.rail());
        body.classList.toggle(cls.mobile, on && this.mode() === "mobile");
        body.classList.toggle(cls.compact, on && prefs.density === "compact");
        body.classList.toggle(cls.reduceMotion, on && prefs.motion === "reduced");
        if (!on && this.lastApp) {
            writeLastLeaf(0, this.lastLeafKey);
        }
        this.lastApp = on;
    }

    resolveFallbackLeaf(leaves, current, controllerModel = "") {
        const model = controllerModel || current?.res_model;
        const map = {
            "hr.job": ["tp_hr_workspace.menu_jobs"],
            "hr.department": ["tp_hr_workspace.menu_departments"],
            "hr.work.location": ["tp_hr_workspace.menu_locations"],
            "hr.employee.category": ["tp_hr_workspace.menu_categories"],
            "tp.hr.import.batch": ["tp_hr_workspace.menu_import"],
            "tp.hr.employee.audit": ["tp_hr_workspace.menu_employee_audit"],
            "tp.bank": ["tp_hr_bank.menu_tp_bank"],
            "hr.employee": ["tp_hr_workspace.menu_employees", "tp_hr_workspace.menu_directory"],
            "hr.employee.public": ["tp_hr_workspace.menu_directory"],
        };
        const candidates = map[model] || [];
        for (const xmlid of candidates) {
            const hit = leaves.filter((l) => l.xmlid === xmlid);
            if (hit.length) {
                return hit;
            }
        }
        return [];
    }

    /** Active leaf = app leaf whose action is the current one; ties go to the last clicked leaf. */
    syncActive() {
        this.state.drawer = false;
        if (!this.app()) {
            this.state.active = 0;
            return;
        }
        const leaves = this.leaves();
        const current = this.action.currentController?.action;
        const controllerModel = this.action.currentController?.props?.resModel || "";
        const isRelationalSubView = Boolean(
            controllerModel && current?.res_model && controllerModel !== current.res_model
        );
        let matches =
            current && !isRelationalSubView
                ? leaves.filter(
                      (l) =>
                          (current.id && l.actionID === current.id) ||
                          (current.path && l.actionPath === current.path)
                  )
                : [];
        // KD-UI-003: actions built by the server (Overview drilldowns, smart buttons, "open
        // source") carry the leaf menu XML ID in their context; nothing is written anywhere.
        const hint = !isRelationalSubView ? current?.context?.tp_hr_leaf : "";
        if (!matches.length && hint) {
            matches = leaves.filter((l) => l.xmlid === hint);
        }
        if (!matches.length && (current || controllerModel)) {
            matches = this.resolveFallbackLeaf(leaves, current, controllerModel);
        }
        if (!matches.length && this.pendingLeaf) {
            // A leaf whose menu runs a server action (TP Contracts) opens another action id.
            matches = leaves.filter((l) => l.id === this.pendingLeaf);
        }
        if (!matches.length && !this.state.active) {
            // Reload/deep link: the leaf this tab last used, else the breadcrumb root from the URL.
            const last = readLastLeaf(this.lastLeafKey);
            matches = leaves.filter((l) => l.id === last);
            if (!matches.length) {
                const root = router.current.actionStack?.[0]?.action;
                matches = leaves.filter(
                    (l) => root && (l.actionPath === root || String(l.actionID) === String(root))
                );
            }
        }
        if (!matches.length) {
            return; // e.g. a native action reached from a TP HR form keeps the current leaf
        }
        const last = readLastLeaf(this.lastLeafKey);
        const pick = matches.find((m) => m.id === last) || matches[0];
        if (pick.id !== last) {
            writeLastLeaf(pick.id, this.lastLeafKey);
        }
        if (pick.id !== this.state.active) {
            this.state.active = pick.id;
            const group = this.entries().find(
                (e) => e.type === "group" && e.leaves.some((l) => l.id === pick.id)
            );
            if (group && !this.isOpen(group)) {
                this.toggleGroup(group);
            }
        }
    }

    activeLabel() {
        return this.leaves().find((l) => l.id === this.state.active)?.name || this.appTitle;
    }

    href(leaf) {
        const href = router.stateToUrl({ action: leaf.actionPath || leaf.actionID });
        return odoo.debug ? `${href}?debug=${encodeURIComponent(odoo.debug)}` : href;
    }

    isGroupActive(group) {
        return group.leaves.some((l) => l.id === this.state.active);
    }

    isOpen(group) {
        if (this.state.query.trim()) {
            return true;
        }
        return this.prefs.groups === null || this.prefs.groups.includes(group.key);
    }

    toggleGroup(group) {
        const all = this.entries().filter((e) => e.type === "group").map((e) => e.key);
        const open = new Set(this.prefs.groups === null ? all : this.prefs.groups);
        if (open.has(group.key)) {
            open.delete(group.key);
        } else {
            open.add(group.key);
        }
        this.saveAppPrefs({ groups: [...open] });
    }

    onGroupClick(group) {
        if (this.rail()) {
            // Rail shows only icons: expand the navigation and show this group.
            if (!this.isOpen(group)) {
                this.toggleGroup(group);
            }
            this.expand();
            return;
        }
        this.toggleGroup(group);
    }

    onLeafClick(ev, leaf) {
        if (isModifiedClick(ev)) {
            return; // new tab/window: let the browser follow the real href
        }
        ev.preventDefault();
        writeLastLeaf(leaf.id, this.lastLeafKey);
        this.pendingLeaf = leaf.id; // read by syncActive() during this navigation only
        Promise.resolve(this.menu.selectMenu(leaf)).finally(() => {
            this.pendingLeaf = 0;
        });
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value;
    }

    clearSearch() {
        this.state.query = "";
        this.search()?.focus();
    }

    expand() {
        if (this.mode() === "desktop") {
            this.saveAppPrefs({ collapsed: false });
        } else {
            this.openDrawer();
        }
    }

    collapse() {
        this.saveAppPrefs({ collapsed: true });
        this.focusAfterPatch = "toggle";
    }

    openDrawer() {
        this.state.drawer = true;
        this.focusAfterPatch = "panel";
    }

    closeDrawer() {
        if (this.state.drawer) {
            this.state.drawer = false;
            this.focusAfterPatch = "toggle";
        }
    }

    onKeydown(ev) {
        if (ev.key === "Escape") {
            if (this.state.query && ev.target === this.search()) {
                ev.preventDefault();
                ev.stopPropagation();
                this.clearSearch();
            } else if (this.state.drawer) {
                ev.preventDefault();
                ev.stopPropagation();
                this.closeDrawer();
            }
            return;
        }
        if (ev.key === "Tab" && this.state.drawer) {
            const items = [...this.panel().querySelectorAll(FOCUSABLE)].filter(
                (el) => el.offsetParent !== null
            );
            if (!items.length) {
                return;
            }
            const first = items[0];
            const last = items[items.length - 1];
            if (ev.shiftKey && document.activeElement === first) {
                ev.preventDefault();
                last.focus();
            } else if (!ev.shiftKey && document.activeElement === last) {
                ev.preventDefault();
                first.focus();
            }
        }
    }
}

WebClient.components = { ...WebClient.components, TpHrSidebar };


