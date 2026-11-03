import { Component, computed } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { HOME_MENU_XMLID } from "./home_catalog";
import { isModifiedClick } from "./home_launcher";

/** Navbar shortcut back to Home; it goes through menu.selectMenu like the native apps menu. */
export class HomeButton extends Component {
    static template = "tp_web_home.HomeButton";

    homeMenu = computed(() =>
        this.menuService.getAll().find((menu) => menu.xmlid === HOME_MENU_XMLID)
    );

    setup() {
        this.menuService = useService("menu");
    }

    isActive() {
        const home = this.homeMenu();
        return Boolean(home) && this.menuService.getCurrentApp()?.id === home.id;
    }

    href() {
        const home = this.homeMenu();
        const href = `/odoo/${home.actionPath || "action-" + home.actionID}`;
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
