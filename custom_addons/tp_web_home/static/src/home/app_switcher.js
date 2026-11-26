import {
    Component,
    computed,
    onWillDestroy,
    signal,
    t,
    useEffect,
    useProps,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { hasTouch } from "@web/core/browser/feature_detection";
import { router } from "@web/core/browser/router";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { useBus, useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import {
    buildCatalog,
    buildDrawerGroups,
    HOME_MENU_XMLID,
    monogram,
    resolveAppDisplayLabel,
} from "./home_catalog";

const FOCUSABLE_SELECTOR =
    'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';

function isModifiedClick(ev) {
    return ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0;
}

function isComposing(ev, composing) {
    return ev.isComposing || composing || ev.keyCode === 229;
}

/**
 * Unified TANPHAT ONE App Switcher (`UI-APPS-001`).
 * Single source of truth for:
 * 1. Top-left 9-dot Navbar Apps Menu across all applications (`.o_navbar_apps_menu`).
 * 2. Home Navigation Menu (`☰` on Trang chủ).
 * 3. "Tất cả ứng dụng" panel on Trang chủ.
 * 4. Mobile App Switcher sheet (`<= 767.98px`).
 */
export class TpAppSwitcher extends Component {
    static template = "tp_web_home.TpAppSwitcher";

    props = useProps({
        open: t.boolean(),
        panelId: t.string().optional(),
        anchorMode: t.string().optional(),
        catalogOverride: t.any().optional(),
        currentAppSections: t.any().optional(),
        onActivateEntry: t.function().optional(),
        onSelectSubMenu: t.function().optional(),
        onClose: t.function(),
    });

    query = signal("");
    activeTab = signal("all");
    subMenusExpanded = signal(false);
    brokenIcons = signal(new Set());

    // Live server-verified admin capability state when rendered outside HomeLauncher
    liveIsAdmin = signal(
        typeof session.tp_home_is_admin === "boolean"
            ? session.tp_home_is_admin
            : Boolean(user.isSystem)
    );
    liveIsDelegated = signal(
        typeof session.tp_home_is_delegated === "boolean"
            ? session.tp_home_is_delegated
            : false
    );

    panelRef = signal.ref();
    searchInputRef = signal.ref();
    titleRef = signal.ref();

    composing = false;
    capSeq = 0;
    destroyed = false;
    _prevBodyOverflow = null;

    effectiveCatalog = computed(() => {
        const override = this.props.catalogOverride;
        const isSys =
            typeof session.tp_home_is_admin === "boolean"
                ? this.liveIsAdmin()
                : Boolean(user.isSystem) || this.liveIsAdmin();
        const base =
            override ||
            buildCatalog(this.menuService.getMenuAsTree("root"), {
                debug: odoo.debug,
                isSystem: isSys,
                isDelegated: this.liveIsDelegated(),
                homeMode: isSys || this.liveIsDelegated() ? "admin" : "employee",
            });
        const broken = this.brokenIcons();
        if (!broken.size) {
            return base;
        }
        const fix = (tile) =>
            broken.has(tile.key)
                ? {
                      ...tile,
                      switcherIcon: "",
                      icon: { type: "monogram", text: monogram(tile.label || tile.name) },
                  }
                : tile;
        return {
            ...base,
            entries: (base.entries || []).map(fix),
            system: (base.system || []).map(fix),
            extraUserApps: (base.extraUserApps || []).map(fix),
        };
    });

    allGroups = computed(() => buildDrawerGroups(this.effectiveCatalog(), ""));
    filteredGroups = computed(() => buildDrawerGroups(this.effectiveCatalog(), this.query()));

    tabs = computed(() => {
        const nonEmpty = this.allGroups();
        if (!nonEmpty.length) {
            return [];
        }
        return [
            { key: "all", label: "Tất cả" },
            ...nonEmpty.map((grp) => ({
                key: grp.key,
                label: grp.tabLabel || grp.label,
            })),
        ];
    });

    visibleGroups = computed(() => {
        const selected = this.activeTab();
        const groups = this.filteredGroups();
        if (!selected || selected === "all") {
            return groups;
        }
        const validTab = this.allGroups().some((g) => g.key === selected);
        if (!validTab) {
            return groups;
        }
        return groups.filter((g) => g.key === selected);
    });

    homeMenu = computed(() =>
        this.menuService.getAll().find((m) => m.xmlid === HOME_MENU_XMLID)
    );

    homeHref = computed(() => {
        const home = this.homeMenu();
        if (!home) {
            return "/app/trang-chu";
        }
        const href = router.stateToUrl({ action: home.actionPath || home.actionID });
        return odoo.debug ? `${href}?debug=${encodeURIComponent(odoo.debug)}` : href;
    });

    isOnHome = computed(() => {
        const home = this.homeMenu();
        const cur = this.menuService.getCurrentApp();
        return Boolean(
            (home && cur && cur.id === home.id) ||
                document.body?.classList?.contains("o_tp_home_active")
        );
    });

    currentAppId = computed(() => this.menuService.getCurrentApp()?.id || null);

    currentAppName = computed(() => resolveAppDisplayLabel(this.menuService.getCurrentApp()));

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");

        // Close automatically ONLY after a real navigation commits (respects dirty-form beforeLeave cancel!)
        useBus(this.env.bus, "ACTION_MANAGER:UPDATE", () => {
            if (this.props.open) {
                this._closeWithoutFocusRestore();
            }
        });

        useBus(this.env.bus, "MENUS:APP-CHANGED", () => {
            if (!this.props.catalogOverride) {
                this._refreshCapabilities();
            }
        });

        useEffect(
            () => {
                if (!this.props.open) {
                    this._unlockBodyScroll();
                    return;
                }
                this.query.set("");
                this.activeTab.set("all");
                this.subMenusExpanded.set(false);

                if (!this.props.catalogOverride) {
                    this._refreshCapabilities();
                }

                const mode = this.props.anchorMode || "navbar";
                if (mode === "mobile" || window.innerWidth <= 768) {
                    this._lockBodyScroll();
                }

                const frame = browser.requestAnimationFrame?.(() => {
                    if (this.destroyed || !this.props.open) {
                        return;
                    }
                    const target = hasTouch() ? this.titleRef() : this.searchInputRef();
                    target?.focus();
                });

                return () => {
                    if (frame) {
                        browser.cancelAnimationFrame?.(frame);
                    }
                    this._unlockBodyScroll();
                };
            },
            () => [this.props.open, this.props.anchorMode]
        );

        onWillDestroy(() => {
            this.destroyed = true;
            this.capSeq++;
            this._unlockBodyScroll();
        });
    }

    _lockBodyScroll() {
        if (document.body && this._prevBodyOverflow === null) {
            this._prevBodyOverflow = document.body.style.overflow || "";
            document.body.style.overflow = "hidden";
        }
    }

    _unlockBodyScroll() {
        if (document.body && this._prevBodyOverflow !== null) {
            document.body.style.overflow = this._prevBodyOverflow;
            this._prevBodyOverflow = null;
        }
    }

    async _refreshCapabilities() {
        if (!session.tp_admin_delegation) {
            this.liveIsAdmin.set(
                typeof session.tp_home_is_admin === "boolean"
                    ? session.tp_home_is_admin
                    : Boolean(user.isSystem)
            );
            this.liveIsDelegated.set(false);
            return;
        }
        const seq = ++this.capSeq;
        try {
            const caps = await rpc("/web/dataset/call_kw/res.users/get_tp_admin_capabilities", {
                model: "res.users",
                method: "get_tp_admin_capabilities",
                args: [],
                kwargs: {},
            });
            if (!this.destroyed && seq === this.capSeq && caps && typeof caps === "object") {
                if (typeof caps.is_full_admin === "boolean") {
                    this.liveIsAdmin.set(caps.is_full_admin);
                } else {
                    this.liveIsAdmin.set(Boolean(user.isSystem));
                }
                this.liveIsDelegated.set(Boolean(caps.delegated));
            }
        } catch {
            // Keep session-initialized baseline on transient network errors
        }
    }

    _closeWithoutFocusRestore() {
        this._unlockBodyScroll();
        this.props.onClose?.({ restoreFocus: false });
    }

    closeWithFocusRestore() {
        this._unlockBodyScroll();
        this.props.onClose?.({ restoreFocus: true });
    }

    isCurrentItem(item) {
        const curId = this.currentAppId();
        return Boolean(curId && item?.menu?.id && curId === item.menu.id && !this.isOnHome());
    }

    selectTab(tabKey) {
        this.activeTab.set(tabKey || "all");
    }

    resetSearchAndTab() {
        this.query.set("");
        this.activeTab.set("all");
        this.searchInputRef()?.focus();
    }

    onSearchInput(ev) {
        this.query.set(ev.target.value);
    }

    clearSearch() {
        this.query.set("");
        this.searchInputRef()?.focus();
    }

    onCompositionStart() {
        this.composing = true;
    }

    onCompositionEnd() {
        this.composing = false;
    }

    onSearchKeydown(ev) {
        if (isComposing(ev, this.composing)) {
            return;
        }
        if (ev.key === "Enter") {
            const firstItem = this.visibleGroups()[0]?.items?.[0];
            if (firstItem) {
                ev.preventDefault();
                this.activateItem(firstItem);
            }
        }
    }

    onPanelKeydown(ev) {
        if (isComposing(ev, this.composing)) {
            return;
        }
        if (ev.key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            if (this.query() && ev.target === this.searchInputRef()) {
                this.clearSearch();
            } else {
                this.closeWithFocusRestore();
            }
            return;
        }
        if (ev.key === "Tab") {
            const panel = this.panelRef();
            if (!panel) {
                return;
            }
            const focusables = [...panel.querySelectorAll(FOCUSABLE_SELECTOR)].filter(
                (el) => el.offsetParent !== null
            );
            if (!focusables.length) {
                return;
            }
            const first = focusables[0];
            const last = focusables[focusables.length - 1];
            if (ev.shiftKey && document.activeElement === first) {
                ev.preventDefault();
                last.focus();
            } else if (!ev.shiftKey && document.activeElement === last) {
                ev.preventDefault();
                first.focus();
            }
        }
    }

    async onHomeClick(ev) {
        if (isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        if (this.isOnHome()) {
            if (browser.location.hash) {
                browser.location.hash = "";
            }
            this._closeWithoutFocusRestore();
            return;
        }
        const home = this.homeMenu();
        if (home) {
            await this.menuService.selectMenu(home);
        }
    }

    onCardClick(ev, item) {
        if (item?.menu && isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.activateItem(item);
    }

    async activateItem(item) {
        if (!item) {
            return;
        }
        if (this.props.onActivateEntry) {
            this._unlockBodyScroll();
            this.props.onActivateEntry(item);
            return;
        }
        if (item.menu) {
            await this.menuService.selectMenu(item.menu);
            return;
        }
        const home = this.homeMenu();
        if (home && home.actionID && item.key) {
            await this.actionService.doAction(home.actionID, {
                clearBreadcrumbs: true,
                onActionReady: () => {
                    try {
                        browser.sessionStorage?.setItem("tp_pending_home_unit", item.key);
                    } catch {
                        // Ignore storage quota / private mode
                    }
                    this.menuService.setCurrentMenu(home);
                    this._closeWithoutFocusRestore();
                },
            });
            window.dispatchEvent(new HashChangeEvent("hashchange"));
        }
    }

    toggleSubMenus() {
        this.subMenusExpanded.set(!this.subMenusExpanded());
    }

    async onSubMenuClick(sec) {
        if (!sec?.actionID) {
            return;
        }
        if (this.props.onSelectSubMenu) {
            await this.props.onSelectSubMenu(sec);
            return;
        }
        await this.menuService.selectMenu(sec);
    }

    flattenSubMenus(sections) {
        const result = [];
        const walk = (nodes, prefix = "") => {
            for (const n of nodes || []) {
                const label = prefix ? `${prefix} › ${n.name}` : n.name;
                if (n.childrenTree?.length) {
                    walk(n.childrenTree, label);
                } else if (n.actionID) {
                    result.push({ ...n, flatLabel: label });
                }
            }
        };
        walk(sections || []);
        return result;
    }

    onIconError(item) {
        if (item?.key) {
            this.brokenIcons.set(new Set(this.brokenIcons()).add(item.key));
        }
    }
}
