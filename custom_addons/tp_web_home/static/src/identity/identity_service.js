import { proxy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { post } from "@web/core/network/http_service";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { imageUrl, redirect } from "@web/core/utils/urls";

/**
 * Compute deterministic 1-2 character uppercase initials from a display name.
 * Falls back to "?" when no non-whitespace letter exists.
 */
export function computeInitials(name) {
    const parts = String(name || "")
        .trim()
        .split(/[\s·/,-]+/)
        .filter(Boolean);
    if (!parts.length) {
        return "?";
    }
    if (parts.length === 1) {
        return parts[0].slice(0, 1).toUpperCase();
    }
    return (parts[0].slice(0, 1) + parts[parts.length - 1].slice(0, 1)).toUpperCase();
}

/**
 * Convert an Odoo write_date string or numeric token into a stable cache-busting query token.
 */
function cacheBuster(writeDate, revision) {
    if (writeDate && revision) {
        return `${writeDate}-${revision}`;
    }
    if (writeDate) {
        return String(writeDate);
    }
    return revision ? String(revision) : undefined;
}

/**
 * Execute native Odoo logout with explicit failure notification.
 * Keeps native dirty-form beforeunload behavior and never fakes logout on error.
 */
export async function performNativeLogout({ notification, pwa } = {}) {
    let route = "/web/session/logout";
    if (pwa?.isScopedApp && pwa.startUrl) {
        route += `?redirect=${encodeURIComponent(pwa.startUrl)}`;
    }
    try {
        browser.navigator.serviceWorker?.controller?.postMessage("user_logout");
        const url = await post(route, { csrf_token: odoo.csrf_token }, "url");
        if (!url || typeof url !== "string") {
            throw new Error("Missing logout redirect URL");
        }
        redirect(url);
        return true;
    } catch {
        notification?.add(_t("Không thể đăng xuất. Vui lòng thử lại."), {
            title: _t("Đăng xuất thất bại"),
            type: "danger",
        });
        return false;
    }
}

/**
 * Open the user's self-service personal profile via a registered workspace handler
 * (e.g. TP HR full profile) or fall back cleanly to native res.users preferences.
 */
export async function openPersonalProfileAction(env) {
    const action = env.services?.action;
    const orm = env.services?.orm;
    const notification = env.services?.notification;
    try {
        const providerRegistry = registry.category("tp_personal_profile");
        const handler = providerRegistry.contains("handler")
            ? providerRegistry.get("handler")
            : null;
        if (typeof handler === "function") {
            return await handler(env);
        }
        if (orm && action && user.userId) {
            const actionDescription = await orm.call("res.users", "action_get", []);
            actionDescription.res_id = user.userId;
            return await action.doAction(actionDescription);
        }
        return false;
    } catch {
        notification?.add(_t("Không thể mở thông tin cá nhân. Vui lòng thử lại."), {
            title: _t("Lỗi mở hồ sơ"),
            type: "danger",
        });
        return false;
    }
}

export const tpIdentityService = {
    dependencies: [],
    start(env) {
        const state = proxy({
            overridePartnerId: null,
            overrideName: "",
            overrideWriteDate: "",
            revision: 0,
            avatarFailed: false,
            loggingOut: false,
        });

        const onIdentityChanged = (payload) => {
            if (!payload || !user.partnerId || payload.partner_id !== user.partnerId) {
                return;
            }
            state.overridePartnerId = payload.partner_id;
            if (payload.name) {
                state.overrideName = String(payload.name);
                try {
                    user.name = state.overrideName;
                } catch {
                    // user may be frozen/getter-only in tests
                }
            }
            if (payload.write_date) {
                state.overrideWriteDate = String(payload.write_date);
                try {
                    user.writeDate = state.overrideWriteDate;
                } catch {
                    // ignore in mocked environments
                }
            }
            state.revision += 1;
            state.avatarFailed = false;

            try {
                const selfUser = env.services["mail.store"]?.self_user;
                if (selfUser) {
                    if (payload.name) {
                        selfUser.name = String(payload.name);
                        if (selfUser.partner_id) {
                            selfUser.partner_id.name = String(payload.name);
                        }
                    }
                    if (payload.write_date && selfUser.partner_id) {
                        selfUser.partner_id.write_date = String(payload.write_date);
                    }
                }
            } catch {
                // mail store is optional
            }
        };

        let unsubscribe = null;
        let destroyed = false;
        const attachBus = () => {
            if (destroyed || unsubscribe) {
                return true;
            }
            const bus = env.services?.bus_service;
            if (bus && typeof bus.subscribe === "function") {
                const unsub = bus.subscribe("tp.identity/changed", onIdentityChanged);
                unsubscribe = typeof unsub === "function" ? unsub : () => {};
                return true;
            }
            return false;
        };
        const waitForBus = (remaining = 10) => {
            if (destroyed || attachBus() || remaining <= 0) {
                return;
            }
            Promise.resolve().then(() => waitForBus(remaining - 1));
        };
        waitForBus();

        const getPartnerId = () => user.partnerId || null;
        const getName = () => {
            const partnerId = getPartnerId();
            if (partnerId && state.overridePartnerId === partnerId && state.overrideName) {
                return state.overrideName;
            }
            return String(user.name || user.login || "").trim();
        };
        const getWriteDate = () => {
            const partnerId = getPartnerId();
            if (partnerId && state.overridePartnerId === partnerId && state.overrideWriteDate) {
                return state.overrideWriteDate;
            }
            return user.writeDate || "";
        };

        return {
            state,
            get partnerId() {
                return getPartnerId();
            },
            get name() {
                return getName();
            },
            get initials() {
                return computeInitials(getName());
            },
            get avatarUrl() {
                const partnerId = getPartnerId();
                if (!partnerId || state.avatarFailed) {
                    return "";
                }
                const unique = cacheBuster(getWriteDate(), state.revision);
                return imageUrl("res.partner", partnerId, "avatar_128", unique ? { unique } : {});
            },
            get avatarFailed() {
                return state.avatarFailed;
            },
            get loggingOut() {
                return state.loggingOut;
            },
            markAvatarFailed() {
                state.avatarFailed = true;
            },
            resetAvatarFailure() {
                state.avatarFailed = false;
            },
            async openPersonalProfile() {
                return await openPersonalProfileAction(env);
            },
            async logout() {
                if (state.loggingOut) {
                    return false;
                }
                state.loggingOut = true;
                try {
                    return await performNativeLogout({
                        notification: env.services.notification,
                        pwa: env.services.pwa,
                    });
                } finally {
                    state.loggingOut = false;
                }
            },
            destroy() {
                destroyed = true;
                if (typeof unsubscribe === "function") {
                    unsubscribe();
                    unsubscribe = null;
                }
            },
        };
    },
};

registry.category("services").add("tp_identity", tpIdentityService);
