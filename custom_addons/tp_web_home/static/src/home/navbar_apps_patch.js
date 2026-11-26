import { signal } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { TpAppSwitcher } from "./app_switcher";
import { resolveAppDisplayLabel } from "./home_catalog";

NavBar.components = {
    ...NavBar.components,
    TpAppSwitcher,
};

patch(NavBar.prototype, {
    setup() {
        this.tpAppsOpen = signal(false);
        this.tpAppsDesktopBtn = signal.ref();
        super.setup();
    },

    get tpCurrentAppLabel() {
        return resolveAppDisplayLabel(this.currentApp);
    },

    toggleTpAppsSwitcher() {
        this.tpAppsOpen.set(!this.tpAppsOpen());
    },

    closeTpAppsSwitcher({ restoreFocus = true } = {}) {
        const wasOpen = this.tpAppsOpen();
        this.tpAppsOpen.set(false);
        if (wasOpen && restoreFocus) {
            requestAnimationFrame(() => {
                const trigger = this.ui.isSmall ? this.menuApps() : this.tpAppsDesktopBtn();
                trigger?.focus();
            });
        }
    },

    async onTpSubMenuSelected(section) {
        if (!section) {
            return;
        }
        await this.menuService.selectMenu(section);
        this.tpAppsOpen.set(false);
    },
});
