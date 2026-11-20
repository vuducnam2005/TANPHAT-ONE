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
    EQ_APP_XMLID,
    eqPrefs,
    LAST_LEAF_KEY,
    resetPrefs,
    savePrefs,
} from "../prefs";

const GROUP_ICONS = {
    "tp_equipment.menu_group_admin": "tune",
    "tp_equipment.menu_group_equipment": "widgets",
    "tp_equipment.menu_group_operations": "swap_horiz",
    "tp_equipment.menu_group_service": "settings_applications",
    "tp_equipment.menu_group_reports": "bar_chart",
    "tp_equipment.menu_group_config": "tune",
};
const LEAF_ICONS = {
    "tp_equipment.menu_equipment_all": "widgets",
    "tp_equipment.menu_proposals": "article",
};
const BODY_CLASSES = [
    "o_tp_eq_shell",
    "o_tp_eq_rail",
    "o_tp_eq_mobile",
    "o_tp_eq_compact",
    "o_tp_eq_reduce_motion",
];
const FOCUSABLE = "a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex='-1'])";

function readLastLeaf() {
    try {
        return Number(browser.sessionStorage.getItem(LAST_LEAF_KEY)) || 0;
    } catch {
        return 0;
    }
}
export function writeLastLeaf(id) {
    try {
        if (id) {
            browser.sessionStorage.setItem(LAST_LEAF_KEY, String(id));
        } else {
            browser.sessionStorage.removeItem(LAST_LEAF_KEY);
        }
    } catch {
        // sessionStorage unavailable: active leaf falls back to the first matching menu.
    }
}

/** Display options shared by the sidebar footer and the Overview toolbar. */
export class TpEquipmentPrefs extends Component {
    static template = "tp_equipment.Prefs";
    prefs = eqPrefs;

    setDensity(density) {
        savePrefs({ density });
    }
    setMotion(motion) {
        savePrefs({ motion });
    }
    toggleCollapsed() {
        savePrefs({ collapsed: !eqPrefs.collapsed });
    }
    reset() {
        resetPrefs();
    }
}

/**
 * Left navigation for the office-equipment app (EQUIP-001, same model as KD-UI-002). The tree comes only from the native menu service (already
 * filtered by groups on the server): no RPC, no hard-coded menu ID. Navigation goes through
 * menu.selectMenu, so unsaved-form handling and breadcrumbs stay native.
 */
export class TpEquipmentSidebar extends Component {
    static template = "tp_equipment.Sidebar";
    static components = { Dropdown, TpEquipmentPrefs, TpUserAccountMenu };

    prefs = eqPrefs;
    panel = signal.ref();
    search = signal.ref();

    app = computed(() => {
        const app = this.menu.getCurrentApp();
        return app && app.xmlid === EQ_APP_XMLID ? app : null;
    });
    mode = computed(() => {
        const size = this.ui.size();
        return size <= 1 ? "mobile" : size <= 3 ? "tablet" : "desktop";
    });
    rail = computed(
        () =>
            !this.state.drawer &&
            ((this.mode() === "tablet") || (this.mode() === "desktop" && eqPrefs.collapsed))
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
                    icon: GROUP_ICONS[node.xmlid] || "apps",
                    leaves,
                });
            } else if (node.actionID) {
                entries.push({
                    type: "leaf",
                    id: node.id,
                    name: node.name,
                    leaf: node,
                    icon: LEAF_ICONS[node.xmlid] || "pie_chart",
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
        onWillDestroy(() => document.body.classList.remove(...BODY_CLASSES));
        onPatched(() => {
            const target = this.focusAfterPatch;
            this.focusAfterPatch = null;
            if (target === "panel") {
                this.panel()?.querySelector(FOCUSABLE)?.focus();
            } else if (target === "toggle") {
                document.querySelector(".o_tp_eq_menu_toggle, .o_tp_eq_sb_collapse")?.focus();
            }
        });
    }

    applyBodyClasses() {
        const on = Boolean(this.app());
        const body = document.body;
        body.classList.toggle("o_tp_eq_shell", on);
        body.classList.toggle("o_tp_eq_rail", on && this.rail());
        body.classList.toggle("o_tp_eq_mobile", on && this.mode() === "mobile");
        body.classList.toggle("o_tp_eq_compact", on && eqPrefs.density === "compact");
        body.classList.toggle("o_tp_eq_reduce_motion", on && eqPrefs.motion === "reduced");
        if (!on && this.lastApp) {
            writeLastLeaf(0);
        }
        this.lastApp = on;
    }

    /** Active leaf = equipment leaf whose action is the current one; ties go to the last clicked leaf. */
    syncActive() {
        this.state.drawer = false;
        if (!this.app()) {
            this.state.active = 0;
            return;
        }
        const leaves = this.leaves();
        const current = this.action.currentController?.action;
        let matches = current
            ? leaves.filter(
                  (l) =>
                      (current.id && l.actionID === current.id) ||
                      (current.path && l.actionPath === current.path)
              )
            : [];
        // Actions built by the server (Overview drilldowns, smart buttons, "open
        // source") carry the leaf menu XML ID in their context; nothing is written anywhere.
        const hint = current?.context?.tp_eq_leaf;
        if (!matches.length && hint) {
            matches = leaves.filter((l) => l.xmlid === hint);
        }
        if (!matches.length && this.pendingLeaf) {
            // A leaf whose menu runs a server action opens another action id.
            matches = leaves.filter((l) => l.id === this.pendingLeaf);
        }
        if (!matches.length && !this.state.active) {
            // Reload/deep link: the leaf this tab last used, else the breadcrumb root from the URL.
            const last = readLastLeaf();
            matches = leaves.filter((l) => l.id === last);
            if (!matches.length) {
                const root = router.current.actionStack?.[0]?.action;
                matches = leaves.filter(
                    (l) => root && (l.actionPath === root || String(l.actionID) === String(root))
                );
            }
        }
        if (!matches.length && !leaves.some((l) => l.id === this.state.active)) {
            // EQUIP-SIMPLE-003: an old link, last-leaf or leaf hint pointing at a hidden menu
            // (Tổng quan, Tồn kho, Quản trị dữ liệu…) falls back to one of the two visible leaves.
            const model = current?.res_model || "";
            const fallback = model.startsWith("tp.equipment.proposal")
                ? "tp_equipment.menu_proposals"
                : "tp_equipment.menu_equipment_all";
            matches = leaves.filter((l) => l.xmlid === fallback);
        }
        if (!matches.length) {
            return; // e.g. a native action reached from an equipment form keeps the current leaf
        }
        const last = readLastLeaf();
        const pick = matches.find((m) => m.id === last) || matches[0];
        if (pick.id !== last) {
            writeLastLeaf(pick.id);
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
        return this.leaves().find((l) => l.id === this.state.active)?.name || "Kho thiết bị văn phòng";
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
        return eqPrefs.groups !== null && eqPrefs.groups.includes(group.key);
    }

    toggleGroup(group) {
        const open = new Set(eqPrefs.groups === null ? [] : eqPrefs.groups);
        if (open.has(group.key)) {
            open.delete(group.key);
        } else {
            open.add(group.key);
        }
        savePrefs({ groups: [...open] });
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
        writeLastLeaf(leaf.id);
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
            savePrefs({ collapsed: false });
        } else {
            this.openDrawer();
        }
    }

    collapse() {
        savePrefs({ collapsed: true });
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

WebClient.components = { ...WebClient.components, TpEquipmentSidebar };
