// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: native components that build `/odoo/...` hrefs
 * without the router (menus, many2one "open record" link) and the vendor
 * subscription entry of the user menu.
 *
 * The hrefs only matter for "open in new tab"/copy link: the click handlers
 * of these components keep their native in-app navigation.
 */

import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { Many2One } from "@web/views/fields/many2one/many2one";
import { NavBar } from "@web/webclient/navbar/navbar";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { brandUrl } from "@tp_branding/brand_urls";

// Vendor licence/subscription dashboard (module `mysubscription`): kept for
// system administrators, not shown in the user menu of other users.
const ADMIN_ONLY_USER_MENU_ITEMS = new Set(["mysubscription_user_menu"]);

patch(NavBar.prototype, {
    getMenuItemHref(payload) {
        return brandUrl(super.getMenuItemHref(payload));
    },
});

patch(Many2One.prototype, {
    get linkHref() {
        return brandUrl(super.linkHref);
    },
});

patch(UserMenu.prototype, {
    getElements() {
        const elements = super.getElements();
        if (user.isSystem) {
            return elements;
        }
        return elements.map((element) =>
            element && ADMIN_ONLY_USER_MENU_ITEMS.has(element.id)
                ? { ...element, hide: true }
                : element
        );
    },
});
