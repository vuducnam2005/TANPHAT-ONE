import { onWillDestroy, signal } from "@odoo/owl";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { imageUrl } from "@web/core/utils/urls";

patch(UserMenu.prototype, {
    setup() {
        super.setup();
        this.tpIdentity = signal(null);
        const originalSource = this.source;
        Object.defineProperties(this, {
            userName: {get: () => this.tpIdentity()?.name || user.name},
            source: {get: () => this.tpIdentity()?.source || originalSource},
        });
        const bus = useService("bus_service");
        const store = useService("mail.store");
        const changed = (identity) => {
            if (identity.partner_id !== user.partnerId) return;
            this.tpIdentity.set({name: identity.name, source: imageUrl("res.partner", user.partnerId, "avatar_128", {unique: identity.write_date})});
            store.insert({"res.partner": [{id: identity.partner_id, name: identity.name, write_date: identity.write_date}]});
        };
        bus.subscribe("tp.identity/changed", changed);
        onWillDestroy(() => bus.unsubscribe("tp.identity/changed", changed));
    },
});
