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
        document.body?.classList?.remove("o_tp_home_active");

        const stack = router.current?.actionStack || [];
        const rootAction = stack[0]?.action;
        const isRootStaleHome = Boolean(
            rootAction === "tp-home" || (home && rootAction && rootAction === home.actionID)
        );
        const menus = this.menuService
            .getAll()
            .filter((m) => m.xmlid !== HOME_MENU_XMLID && (!home || m.appID !== home.id));

        const leafHint =
            current?.context?.tp_hr_leaf ||
            current?.context?.tp_kd_leaf ||
            current?.context?.tp_eq_leaf ||
            "";
        let matches = [];
        if (leafHint) {
            matches = menus.filter((m) => m.xmlid === leafHint);
        }
        if (!matches.length && rootAction && !isRootStaleHome) {
            matches = menus.filter(
                (m) => m.actionID && (m.actionID === rootAction || m.actionPath === rootAction)
            );
        }
        if (!matches.length && (stack.length <= 1 || isRootStaleHome)) {
            matches = menus.filter(
                (m) =>
                    m.actionID &&
                    ((typeof current.id === "number" && m.actionID === current.id) ||
                        (current.path && m.actionPath === current.path))
            );
        }
        if (!matches.length) {
            return;
        }
        const curApp = this.menuService.getCurrentApp();
        if (curApp && curApp.id !== home?.id && matches.some((m) => m.appID === curApp.id)) {
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
