import { Component, computed, onMounted, onWillDestroy, signal, useOnChange, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { hasTouch } from "@web/core/browser/feature_detection";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { buildCatalog, filterTiles, homeSections, monogram } from "./home_catalog";

const EMPTY_CATALOG = Object.freeze({
    isAdmin: false,
    admin: null,
    tools: [],
    entries: [],
    home: [],
    system: [],
    all: [],
    otherApps: 0,
});

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
    props = useProps({ ...standardActionServiceProps });

    query = signal("");
    panelQuery = signal("");
    panelOpen = signal(false);
    menuState = signal("loading");
    brokenIcons = signal(new Set());
    selectedModule = signal(null);

    searchInput = signal.ref();
    panelInput = signal.ref();
    panelToggle = signal.ref();
    panelTitle = signal.ref();
    detailTitleRef = signal.ref();

    loadSequence = 0;
    composing = false;
    focusPanel = false;
    lastClickedModuleKey = null;

    catalog = computed(() => {
        if (this.menuState() !== "ready") {
            return EMPTY_CATALOG;
        }
        const catalog = buildCatalog(this.menuService.getMenuAsTree("root"), {
            debug: odoo.debug,
            // Session flag for base.group_system; server-filtered menus remain authoritative.
            isSystem: Boolean(user.isSystem),
        });
        const broken = this.brokenIcons();
        const fix = (tile) =>
            broken.has(tile.key) ? { ...tile, icon: { type: "monogram", text: monogram(tile.label) } } : tile;
        return {
            ...catalog,
            home: catalog.home.map(fix),
            system: catalog.system.map(fix),
            all: catalog.all.map(fix),
        };
    });

    tools = computed(() => this.catalog().tools || []);
    sections = computed(() => homeSections(this.catalog(), this.query()));
    visibleEntries = computed(() => this.sections().flatMap((section) => section.tiles));
    panelTiles = computed(() => filterTiles(this.catalog().all, this.panelQuery()));
    hasAdminPanel = computed(() => this.catalog().all.length > 0);

    selectedModuleItem = computed(() => {
        const key = this.selectedModule();
        if (!key) {
            return null;
        }
        return this.catalog().entries.find((m) => m.key === key && !m.menu) || null;
    });

    setup() {
        this.menuService = useService("menu");
        this._onHashChange = () => this.syncFromHash();

        onMounted(() => {
            this.syncFromHash();
            this.loadMenus();
            browser.addEventListener("hashchange", this._onHashChange);
            browser.addEventListener("popstate", this._onHashChange);
        });

        onWillDestroy(() => {
            this.loadSequence++;
            browser.removeEventListener("hashchange", this._onHashChange);
            browser.removeEventListener("popstate", this._onHashChange);
        });

        useOnChange(
            () => [this.selectedModule() || "", Boolean(this.detailTitleRef())],
            (key, hasTitle) => {
                if (key && hasTitle) {
                    this.detailTitleRef()?.focus();
                }
            }
        );

        // Move focus into the panel once it is rendered, only when the user just opened it.
        // Touch devices get the panel title instead of the input, so no keyboard pops up.
        useOnChange(
            () => [Boolean(this.panelInput()), Boolean(this.panelTitle())],
            (hasInput, hasTitle) => {
                if (this.focusPanel && hasInput && hasTitle) {
                    this.focusPanel = false;
                    (hasTouch() ? this.panelTitle() : this.panelInput()).focus();
                }
            }
        );
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
        this.panelQuery.set("");
        this.selectedModule.set(null);
        try {
            // IndexedDB can belong to a previous user. Only a fresh, applied response may
            // unlock the catalog; a failed request must never fall back to cached menus.
            await this.menuService.reload();
            if (!this.menuService.getMenuAsTree("root")) {
                throw new Error("Missing menu root");
            }
            if (sequence === this.loadSequence) {
                this.menuState.set("ready");
                this.syncFromHash();
            }
        } catch {
            if (sequence === this.loadSequence) {
                this.menuState.set("error");
            }
        }
    }

    /** Which empty state applies when Home itself has nothing to show. */
    emptyKind() {
        if (this.menuState() !== "ready" || this.visibleEntries().length) {
            return "";
        }
        if (this.query().trim()) {
            return "search";
        }
        return this.catalog().otherApps ? "switcher" : "none";
    }

    resultMessage() {
        if (this.menuState() === "loading") {
            return "Đang tải không gian làm việc…";
        }
        if (this.menuState() === "error") {
            return "Chưa tải được Trang chủ";
        }
        const count = this.visibleEntries().length;
        if (!this.query().trim()) {
            return `${count} lối vào trên Trang chủ`;
        }
        return count ? `Tìm thấy ${count} lối vào` : "Không có lối vào phù hợp trên Trang chủ";
    }

    onSearchInput(ev) {
        this.query.set(ev.target.value);
    }

    onSearchKeydown(ev) {
        if (isComposing(ev, this.composing)) {
            return;
        }
        if (ev.key === "Escape" && this.query()) {
            ev.preventDefault();
            ev.stopPropagation();
            this.clearSearch();
        } else if (ev.key === "Enter") {
            const [first] = this.visibleEntries();
            if (first) {
                ev.preventDefault();
                this.activate(first);
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
        this.searchInput()?.focus();
    }

    /** Opens a menu entry, toggles the all-apps panel, or opens a placeholder detail view. */
    activate(entry) {
        if (entry.kind === "panel") {
            this.togglePanel();
        } else if (entry.menu) {
            this.menuService.selectMenu(entry.menu);
        } else if (entry.placeholderOnly || !entry.menu) {
            this.lastClickedModuleKey = entry.key;
            this.selectedModule.set(entry.key);
            browser.location.hash = `unit=${entry.key}`;
        }
    }

    onEntryClick(ev, entry) {
        if (entry.menu && isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.activate(entry);
    }

    togglePanel() {
        if (this.panelOpen()) {
            this.closePanel();
        } else if (this.hasAdminPanel()) {
            this.focusPanel = true;
            this.panelQuery.set("");
            this.panelOpen.set(true);
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

    /** Escape clears the panel search first, then closes the panel; it never leaves Home. */
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
        const [first] = this.panelTiles();
        if (first) {
            ev.preventDefault();
            this.menuService.selectMenu(first.menu);
        }
    }

    onIconError(tile) {
        this.brokenIcons.set(new Set(this.brokenIcons()).add(tile.key));
    }
}

registry.category("actions").add("tp_web_home.home", HomeLauncher);
