import { Component, computed, onMounted, onWillStart, signal, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { buildTiles, filterTiles, groupTiles, monogram } from "./home_catalog";

/** A click the browser should handle itself (new tab/window, download, non-primary button). */
export function isModifiedClick(ev) {
    return ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0;
}

/**
 * The menu service may first render menus cached in IndexedDB, which are shared by every
 * user of the browser. The page always starts a fresh /web/webclient/load_menus request
 * (odoo.loadMenusPromise); wait for it and for the menu service to apply it, so Home never
 * shows the catalog of a previous session.
 */
async function waitForFreshMenus() {
    if (!odoo.loadMenusPromise) {
        return;
    }
    try {
        await odoo.loadMenusPromise;
    } catch {
        return;
    }
    // The menu service applies the response in promise callbacks: one macrotask later they ran.
    await new Promise((resolve) => browser.setTimeout(resolve));
}

export class HomeLauncher extends Component {
    static template = "tp_web_home.HomeLauncher";
    props = useProps({ ...standardActionServiceProps });

    query = signal("");
    brokenIcons = signal(new Set());
    searchInput = signal.ref();

    tiles = computed(() =>
        buildTiles(this.menuService.getMenuAsTree("root"), odoo.debug).map((tile) =>
            this.brokenIcons().has(tile.key)
                ? { ...tile, icon: { type: "monogram", text: monogram(tile.label) } }
                : tile
        )
    );
    visibleTiles = computed(() => filterTiles(this.tiles(), this.query()));
    groups = computed(() => groupTiles(this.visibleTiles()));

    setup() {
        this.menuService = useService("menu");
        this.ui = useService("ui");
        onWillStart(waitForFreshMenus);
        onMounted(() => {
            if (!this.ui.isSmall) {
                this.searchInput()?.focus();
            }
        });
    }

    resultMessage() {
        const count = this.visibleTiles().length;
        if (!this.query().trim()) {
            return `${count} ứng dụng`;
        }
        return count ? `Tìm thấy ${count} ứng dụng` : "Không tìm thấy ứng dụng phù hợp";
    }

    onSearchInput(ev) {
        this.query.set(ev.target.value);
    }

    onSearchKeydown(ev) {
        if (ev.key === "Escape" && this.query()) {
            ev.preventDefault();
            ev.stopPropagation();
            this.clearSearch();
        } else if (ev.key === "Enter") {
            const [first] = this.visibleTiles();
            if (first) {
                ev.preventDefault();
                this.menuService.selectMenu(first.menu);
            }
        }
    }

    clearSearch() {
        this.query.set("");
        this.searchInput()?.focus();
    }

    onTileClick(ev, tile) {
        if (isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.menuService.selectMenu(tile.menu);
    }

    onIconError(tile) {
        this.brokenIcons.set(new Set(this.brokenIcons()).add(tile.key));
    }
}

registry.category("actions").add("tp_web_home.home", HomeLauncher);
