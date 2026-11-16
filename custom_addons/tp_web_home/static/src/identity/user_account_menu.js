import { Component, t, useProps } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { useService } from "@web/core/utils/hooks";

/**
 * Shared circular avatar with deterministic monogram fallback when no partner image
 * exists or when loading fails.
 */
export class TpIdentityAvatar extends Component {
    static template = "tp_web_home.TpIdentityAvatar";

    setup() {
        this.props = useProps({
            size: t.number().optional(28),
            className: t.string().optional(""),
        });
        this.identity = useService("tp_identity");
    }

    onError() {
        this.identity.markAvatarFailed();
    }
}

/**
 * Shared user account trigger + personal profile & logout dropdown for custom workspace sidebars.
 * Reads live identity from tp_identity and triggers self-service profile or native logout.
 */
export class TpUserAccountMenu extends Component {
    static template = "tp_web_home.TpUserAccountMenu";
    static components = { Dropdown, DropdownItem, TpIdentityAvatar };

    setup() {
        this.props = useProps({
            collapsed: t.boolean().optional(false),
            position: t.string().optional("top-start"),
            onBeforeOpenProfile: t.function().optional(),
            onBeforeLogout: t.function().optional(),
        });
        this.identity = useService("tp_identity");
        this.dropdown = useDropdownState();
    }

    async onOpenProfile() {
        this.dropdown.close();
        if (this.props.onBeforeOpenProfile) {
            this.props.onBeforeOpenProfile();
        }
        await this.identity.openPersonalProfile();
    }

    async onLogout() {
        this.dropdown.close();
        if (this.props.onBeforeLogout) {
            this.props.onBeforeLogout();
        }
        await this.identity.logout();
    }
}
