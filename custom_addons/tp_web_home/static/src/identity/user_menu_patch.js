import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { TpIdentityAvatar } from "./user_account_menu";

Object.assign(UserMenu.components, { TpIdentityAvatar });

patch(UserMenu.prototype, {
    setup() {
        super.setup();
        this.tpIdentity = useService("tp_identity");
        this.tpAccountAction = useService("action");
    },

    get userName() {
        return this.tpIdentity.name || this._tpFallbackUserName;
    },

    set userName(value) {
        this._tpFallbackUserName = value;
    },

    get source() {
        return this.tpIdentity.avatarUrl || this._tpFallbackSource;
    },

    set source(value) {
        this._tpFallbackSource = value;
    },

    onAvatarImageError() {
        this.tpIdentity.markAvatarFailed();
    },

    /**
     * Present "Thông tin cá nhân" and "Đăng xuất" in UserMenu / BurgerUserMenu without
     * removing underlying registry entries or background services such as IM status.
     */
    getElements() {
        const items = [
            {
                type: "item",
                id: "personal_profile",
                description: _t("Thông tin cá nhân"),
                callback: () => this.tpIdentity.openPersonalProfile(),
                sequence: 10,
            },
        ];
        items.push({
            type: "item", id: "account_security", description: _t("Tài khoản & Bảo mật"),
            callback: () => this.tpAccountAction.doAction("tp_web_login.action_account_security"), sequence: 20,
        });
        const logout = super.getElements().find((el) => el.id === "logout");
        if (logout) {
            items.push({
                ...logout,
                description: _t("Đăng xuất"),
                callback: () => this.tpIdentity.logout(),
                sequence: 100,
            });
        }
        return items;
    },
});
