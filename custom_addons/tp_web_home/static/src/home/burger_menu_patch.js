import { patch } from "@web/core/utils/patch";
import { BurgerMenu } from "@web/webclient/burger_menu/burger_menu";
import { useListener } from "@odoo/owl";

/**
 * MOBILE-001: the native phone navigation drawer closes with its X button or the backdrop,
 * but not with Escape, and keyboard focus stays behind it. Add Escape-to-close, move focus
 * into the drawer when it opens and back to the toggle when it closes. No menu or rights change.
 */
function focusWhenRendered(selector, frames = 20) {
    const element = document.querySelector(selector);
    if (element) {
        element.focus();
    } else if (frames > 0) {
        requestAnimationFrame(() => focusWhenRendered(selector, frames - 1));
    }
}

patch(BurgerMenu.prototype, {
    setup() {
        super.setup();
        useListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.state.isBurgerOpened) {
                ev.preventDefault();
                ev.stopPropagation();
                this._closeBurger();
            }
        }, true);
    },
    _openBurger() {
        super._openBurger();
        focusWhenRendered(".o_burger_menu .o_sidebar_close");
    },
    _closeBurger() {
        const wasOpen = this.state.isBurgerOpened;
        super._closeBurger();
        if (wasOpen) {
            focusWhenRendered(".o_mobile_menu_toggle");
        }
    },
});
