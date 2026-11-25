import { Component, computed } from "@odoo/owl";
import { router } from "@web/core/browser/router";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { HOME_MENU_XMLID } from "./home_catalog";
import { isModifiedClick } from "./home_launcher";

function str(val) {
    return typeof val === "string" ? val : "";
}

/** Navbar shortcut back to Home; also keeps active app menu synced on Back/Forward & Home routes. */
export class HomeButton extends Component {
    static template = "tp_web_home.HomeButton";

    homeMenu = computed(() =>
        this.menuService.getAll().find((menu) => menu.xmlid === HOME_MENU_XMLID)
    );

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.syncAppWithAction());
    }

    syncAppWithAction() {
        const current = this.actionService.currentController?.action;
        if (!current) {
            return;
        }
        const home = this.homeMenu();
        const isHome =
            str(current.tag) === "tp_web_home.home" ||
            str(current.xml_id) === "tp_web_home.action_home" ||
            str(current.path) === "tp-home" ||
            Boolean(home && current.id && current.id === home.actionID);
        if (isHome) {
            if (home && this.menuService.getCurrentApp()?.id !== home.id) {
                this.menuService.setCurrentMenu(home);
            }
            return;
        }

        const stack = router.current?.actionStack || [];
        const rootAction = stack[0]?.action;
        const menus = this.menuService.getAll();
        let matches = [];
        if (rootAction) {
            matches = menus.filter(
                (m) => m.actionID && (m.actionID === rootAction || m.actionPath === rootAction)
            );
        }
        if (!matches.length && stack.length <= 1 && typeof current.id === "number") {
            matches = menus.filter((m) => m.actionID === current.id);
        }
        if (!matches.length) {
            return;
        }
        const curApp = this.menuService.getCurrentApp();
        if (curApp && matches.some((m) => m.appID === curApp.id)) {
            return;
        }
        const preferred =
            matches.find((m) => str(this.menuService.getMenu?.(m.appID)?.xmlid).startsWith("tp_")) ||
            matches[0];
        if (preferred?.appID) {
            this.menuService.setCurrentMenu(preferred.appID);
        }
    }

    isActive() {
        const home = this.homeMenu();
        return Boolean(home) && this.menuService.getCurrentApp()?.id === home.id;
    }

    href() {
        const home = this.homeMenu();
        const href = router.stateToUrl({ action: home.actionPath || home.actionID });
        return odoo.debug ? `${href}?debug=${encodeURIComponent(odoo.debug)}` : href;
    }

    onClick(ev) {
        if (isModifiedClick(ev)) {
            return;
        }
        ev.preventDefault();
        this.menuService.selectMenu(this.homeMenu());
    }
}

registry
    .category("systray")
    .add("tp_web_home.home_button", { Component: HomeButton }, { sequence: 1100 });
