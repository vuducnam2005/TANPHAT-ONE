/** @odoo-module **/
import {
    Component,
    computed,
    onMounted,
    onWillDestroy,
    proxy,
    signal,
    useEffect,
    usePlugin,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { UIPlugin } from "@web/core/ui/ui_plugin";
import { useBus, useService } from "@web/core/utils/hooks";
import { WebClient } from "@web/webclient/webclient";
import { TpUserAccountMenu } from "@tp_web_home/identity/user_account_menu";
import {
    LAST_LEAF_KEY,
    REQ_APP_XMLID,
    isModifiedClick,
    reqPrefs,
    saveReqPrefs,
} from "../prefs";

const LEAF_ICONS = {
    "tp_request.menu_overview": "dashboard",
    "tp_request.menu_mine": "description",
    "tp_request.menu_to_approve": "fact_check",
    "tp_request.menu_to_execute": "engineering",
    "tp_request.menu_watching": "visibility",
    "tp_request.menu_admin": "tune",
};

const BODY_CLASSES = [
    "o_tp_req_shell",
    "o_tp_req_rail",
    "o_tp_req_mobile",
    "o_tp_req_reduce_motion",
];

function readLastLeaf() {
    try {
        return Number(browser.sessionStorage.getItem(LAST_LEAF_KEY)) || 0;
    } catch {
        return 0;
    }
}

function writeLastLeaf(id) {
    try {
        if (id) {
            browser.sessionStorage.setItem(LAST_LEAF_KEY, String(id));
        } else {
            browser.sessionStorage.removeItem(LAST_LEAF_KEY);
        }
    } catch {
        // ignore
    }
}

export class TpRequestSidebar extends Component {
    static template = "tp_request.Sidebar";
    static components = { TpUserAccountMenu };

    prefs = reqPrefs;
    panel = signal.ref();

    app = computed(() => {
        const app = this.menu.getCurrentApp();
        return app && app.xmlid === REQ_APP_XMLID ? app : null;
    });

    mode = computed(() => {
        const size = this.ui.size();
        return size <= 1 ? "mobile" : size <= 3 ? "tablet" : "desktop";
    });

    rail = computed(
        () =>
            !this.state.drawer &&
            (this.mode() === "tablet" || (this.mode() === "desktop" && reqPrefs.collapsed))
    );

    leaves = computed(() => {
        const app = this.app();
        if (!app) {
            return [];
        }
        const tree = this.menu.getMenuAsTree(app.id);
        return (tree.childrenTree || [])
            .filter((node) => node.actionID)
            .map((node) => ({
                ...node,
                icon: LEAF_ICONS[node.xmlid] || "description",
            }));
    });

    setup() {
        this.menu = useService("menu");
        this.action = useService("action");
        this.orm = useService("orm");
        this.busService = useService("bus_service");
        this.ui = usePlugin(UIPlugin);
        this.state = proxy({
            drawer: false,
            active: 0,
            counts: { to_approve: 0, to_execute: 0, mine_returned: 0, overdue: 0 },
        });
        this.pendingLeaf = 0;

        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
            this.syncActive();
            if (this.app()) {
                this.refreshCounts();
            }
        });
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => {
            this.syncActive();
            if (this.app()) {
                this.refreshCounts();
            }
        });
        useBus(this.env.bus, "TP_REQUEST:REFRESH_COUNTS", () => this.refreshCounts());

        this.busService.subscribe("tp_request/updated", () => {
            if (this.app()) {
                this.refreshCounts();
                this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED");
            }
        });

        useEffect(() => this.applyBodyClasses());
        onMounted(() => {
            this.syncActive();
            if (this.app()) {
                this.refreshCounts();
            }
        });
        onWillDestroy(() => document.body.classList.remove(...BODY_CLASSES));
    }

    async refreshCounts() {
        try {
            const counts = await this.orm.silent.call("tp.request", "tp_sidebar_counts", []);
            if (counts) {
                Object.assign(this.state.counts, counts);
            }
        } catch {
            // keep last known counts
        }
    }

    badgeFor(leaf) {
        if (leaf.xmlid === "tp_request.menu_to_approve") {
            return this.state.counts.to_approve || 0;
        }
        if (leaf.xmlid === "tp_request.menu_to_execute") {
            return this.state.counts.to_execute || 0;
        }
        if (leaf.xmlid === "tp_request.menu_mine") {
            return this.state.counts.mine_returned || 0;
        }
        return 0;
    }

    badgeKind(leaf) {
        if (leaf.xmlid === "tp_request.menu_mine") {
            return "is-warn";
        }
        return "is-primary";
    }

    applyBodyClasses() {
        const on = Boolean(this.app());
        const body = document.body;
        body.classList.toggle("o_tp_req_shell", on);
        body.classList.toggle("o_tp_req_rail", on && this.rail());
        body.classList.toggle("o_tp_req_mobile", on && this.mode() === "mobile");
        body.classList.toggle("o_tp_req_reduce_motion", on && reqPrefs.motion === "reduced");
        if (!on) {
            writeLastLeaf(0);
        }
    }

    syncActive() {
        this.state.drawer = false;
        if (!this.app()) {
            this.state.active = 0;
            return;
        }
        const leaves = this.leaves();
        const current = this.action.currentController?.action;
        let match = current
            ? leaves.find(
                  (l) =>
                      (current.id && l.actionID === current.id) ||
                      (current.path && l.actionPath === current.path)
              )
            : null;
        if (!match && this.pendingLeaf) {
            match = leaves.find((l) => l.id === this.pendingLeaf);
        }
        if (!match) {
            const last = readLastLeaf();
            match = leaves.find((l) => l.id === last) || leaves[0];
        }
        if (match) {
            this.state.active = match.id;
            writeLastLeaf(match.id);
        }
    }

    activeLabel() {
        return this.leaves().find((l) => l.id === this.state.active)?.name || "Đề nghị & Phê duyệt";
    }

    href(leaf) {
        return router.stateToUrl({ action: leaf.actionPath || leaf.actionID });
    }

    onLeafClick(ev, leaf) {
        if (isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.pendingLeaf = leaf.id;
        writeLastLeaf(leaf.id);
        this.state.drawer = false;
        Promise.resolve(this.menu.selectMenu(leaf)).finally(() => {
            this.pendingLeaf = 0;
        });
    }

    toggleCollapse() {
        saveReqPrefs({ collapsed: !reqPrefs.collapsed });
    }

    openDrawer() {
        this.state.drawer = true;
    }

    closeDrawer() {
        this.state.drawer = false;
    }
}

WebClient.components = { ...WebClient.components, TpRequestSidebar };
