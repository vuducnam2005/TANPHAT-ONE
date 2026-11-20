// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: browser tab title `"<page> | TANPHAT ONE"`.
 *
 * Patches the owner (TitlePlugin) instead of writing `document.title` after
 * render, so the native effect stays the only writer and nothing flashes.
 * The notification counter prefix `(n)` and the `" - "` part separator are
 * kept as native.
 */

import { computed } from "@odoo/owl";
import { TitlePlugin } from "@web/core/browser/title_plugin";
import { patch } from "@web/core/utils/patch";
import { brandTitle } from "@tp_branding/brand_urls";

patch(TitlePlugin.prototype, {
    setup() {
        this.title = computed(() => {
            const prefix = this.prefix() ? this.prefix() + " " : "";
            const name = Object.values(this.titleParts()).join(" - ");
            return prefix + brandTitle(name);
        });
        super.setup();
    },
});
