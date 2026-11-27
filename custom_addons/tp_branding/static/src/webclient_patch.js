// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: service worker on the `/app` scope.
 *
 * Same registration/activation logic as the native webclient, only the scope
 * differs. The legacy registration of this same worker on `/odoo` (this
 * origin, this script) is removed because no page lives there any more; no
 * other registration and no browser storage is touched.
 */

import { Component, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { rpcBus } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { APP_PATH, LEGACY_APP_PATH } from "@tp_branding/brand_urls";
import { HOME_MENU_XMLID } from "@tp_web_home/home/home_catalog";

const SW_SCRIPT_PATH = "/web/service-worker.js";
let pushUnavailableLogged = false;

function syncHomeMenu(menuService) {
    const home = menuService?.getAll?.().find((m) => m.xmlid === HOME_MENU_XMLID);
    if (home && menuService.getCurrentApp?.()?.id !== home.id) {
        menuService.setCurrentMenu(home);
    }
}

function isHomeOrRootPath(pathname) {
    const clean = (pathname || "").replace(/\/+$/, "") || "/";
    return (
        clean === APP_PATH ||
        clean === "/app/trang-chu" ||
        clean === "/app/tp-home" ||
        clean === LEGACY_APP_PATH ||
        clean === "/web"
    );
}

export class TpNotFoundAction extends Component {
    static template = "tp_branding.NotFound";
    props = useProps();

    setup() {
        this.actionService = useService("action");
        this.menuService = useService("menu");
    }

    get params() {
        return this.props?.action?.params || {};
    }

    get requestedPath() {
        return this.params.requestedPath || browser.location.pathname || "";
    }

    get reasonText() {
        if (this.params.kind === "missing_or_denied") {
            return "Bản ghi hoặc đường dẫn bạn vừa mở không tồn tại, đã được dọn dẹp hoặc tài khoản hiện tại chưa được cấp quyền truy cập.";
        }
        return "Đường dẫn bạn truy cập không tồn tại trong hệ thống TANPHAT ONE hoặc đã thay đổi.";
    }

    goBack() {
        let sameOriginReferrer = false;
        try {
            if (document.referrer) {
                sameOriginReferrer =
                    new URL(document.referrer).origin === window.location.origin;
            }
        } catch {
            sameOriginReferrer = false;
        }
        if (window.history.length > 1 && sameOriginReferrer) {
            window.history.back();
            return;
        }
        this.goHome();
    }

    async goHome() {
        await this.actionService.doAction("tp_web_home.action_home", { clearBreadcrumbs: true });
        syncHomeMenu(this.menuService);
    }
}

registry.category("actions").add("tp_branding.not_found", TpNotFoundAction);

// F-0030: Track active RPCs so stuck .o_loading_indicator never lingers after idle settle
let activeRpcCount = 0;
let idleClearTimer = null;
function scheduleIdleIndicatorCheck() {
    if (idleClearTimer) {
        browser.clearTimeout(idleClearTimer);
    }
    if (activeRpcCount <= 0) {
        idleClearTimer = browser.setTimeout(() => {
            if (activeRpcCount <= 0 && typeof document !== "undefined") {
                document.body?.classList?.add("tp-rpc-idle");
            }
        }, 600);
    }
}
rpcBus.addEventListener("RPC:REQUEST", () => {
    activeRpcCount++;
    if (typeof document !== "undefined") {
        document.body?.classList?.remove("tp-rpc-idle");
    }
});
rpcBus.addEventListener("RPC:RESPONSE", () => {
    activeRpcCount = Math.max(0, activeRpcCount - 1);
    scheduleIdleIndicatorCheck();
});

async function unregisterLegacyWorker(serviceWorker) {
    try {
        for (const registration of await serviceWorker.getRegistrations()) {
            const scope = new URL(registration.scope);
            const worker = registration.active || registration.waiting || registration.installing;
            const script = worker ? new URL(worker.scriptURL) : null;
            if (
                scope.origin === window.location.origin &&
                scope.pathname === LEGACY_APP_PATH &&
                script?.pathname === SW_SCRIPT_PATH
            ) {
                await registration.unregister();
            }
        }
    } catch (error) {
        console.warn("TANPHAT ONE: legacy service worker cleanup skipped", error);
    }
}

async function openNotFoundOrHome(webClient, requestedPath, kind = "unknown_route") {
    if (isHomeOrRootPath(requestedPath.split("?")[0])) {
        await webClient.actionService.doAction("tp_web_home.action_home", {
            clearBreadcrumbs: true,
        });
        syncHomeMenu(webClient.menuService);
        return;
    }
    await webClient.actionService.doAction(
        {
            type: "ir.actions.client",
            tag: "tp_branding.not_found",
            name: "Không tìm thấy trang",
            params: { requestedPath, kind },
        },
        { clearBreadcrumbs: true }
    );
    try {
        if (requestedPath && browser.location.pathname + browser.location.search !== requestedPath) {
            browser.history.replaceState(browser.history.state || {}, "", requestedPath);
        }
    } catch {
        // Ignore history state restrictions
    }
}

const webClientPatch = {
    async _loadDefaultApp() {
        const reqPath = this._tpBootRequestedPath || "";
        if (reqPath && !isHomeOrRootPath(reqPath.split("?")[0])) {
            const isDetailId = /\/\d+(?:[/?#]|$)/.test(reqPath);
            await openNotFoundOrHome(
                this,
                reqPath,
                isDetailId ? "missing_or_denied" : "unknown_route"
            );
            return;
        }
        return await super._loadDefaultApp();
    },

    async loadRouterState() {
        const requestedPath = browser.location.pathname + (browser.location.search || "");
        let routerFailed = false;
        this._tpBootRequestedPath = requestedPath;
        try {
            await super.loadRouterState();
        } catch (error) {
            routerFailed = true;
            console.warn("TANPHAT ONE: loadRouterState error, showing branded fallback:", error);
            try {
                await openNotFoundOrHome(this, requestedPath, "missing_or_denied");
            } catch (fallbackError) {
                console.error("TANPHAT ONE: fallback failed:", fallbackError);
                this._tpBootRequestedPath = "";
                await super._loadDefaultApp();
            }
        } finally {
            this._tpBootRequestedPath = "";
        }

        // Post-load check: ensure action manager has active content & clear any slow-boot recovery overlay
        document.getElementById("tp-emergency-recovery")?.remove();
        scheduleIdleIndicatorCheck();
        if (!routerFailed) {
            browser.setTimeout(() => {
                document.getElementById("tp-emergency-recovery")?.remove();
                const actionManager = document.querySelector(".o_action_manager");
                if (
                    this.actionService?.currentController == null &&
                    actionManager &&
                    actionManager.children.length === 0 &&
                    activeRpcCount === 0
                ) {
                    openNotFoundOrHome(this, requestedPath, "unknown_route").catch(() =>
                        super._loadDefaultApp()
                    );
                }
            }, 2000);
        }
    },

    registerServiceWorker() {
        const serviceWorker = navigator.serviceWorker;
        if (!serviceWorker) {
            return;
        }
        unregisterLegacyWorker(serviceWorker);
        serviceWorker
            .register(SW_SCRIPT_PATH, { scope: APP_PATH })
            .then((registration) => {
                if (registration.active && registration.active.state === "activated") {
                    this.serviceWorkerActivationResolvers.resolve();
                } else {
                    const sw =
                        registration.installing || registration.waiting || registration.active;
                    sw?.addEventListener?.("statechange", (e) => {
                        if (e.target.state === "activated") {
                            this.serviceWorkerActivationResolvers.resolve();
                        }
                    });
                }
                serviceWorker.ready.then(() => {
                    if (!serviceWorker.controller) {
                        rpcBus.trigger("CLEAR-CACHES");
                    }
                });
            })
            .catch((error) => {
                console.error("Service worker registration failed, error:", error);
            });
    },
};

patch(WebClient.prototype, webClientPatch);

// F-0015: Suppress sticky red danger toast when browser push service (FCM/GCM) is unavailable
if (typeof WebClient.prototype._subscribePush === "function") {
    patch(WebClient.prototype, {
        async _subscribePush(...args) {
            const origNotification = this.notification;
            const wrappedNotification = origNotification
                ? Object.create(origNotification, {
                      add: {
                          value: (message, options = {}) => {
                              const msgStr = String(message || "");
                              if (
                                  options?.type === "danger" &&
                                  options?.sticky &&
                                  /push service|registration failed|pushmanager|notification/i.test(
                                      msgStr + " " + String(options?.title || "")
                                  )
                              ) {
                                  if (!pushUnavailableLogged) {
                                      pushUnavailableLogged = true;
                                      console.info(
                                          "TANPHAT ONE: Push notification service unavailable in browser; sticky banner suppressed."
                                      );
                                  }
                                  return () => {};
                              }
                              return origNotification.add(message, options);
                          },
                      },
                  })
                : origNotification;
            this.notification = wrappedNotification;
            try {
                return await super._subscribePush(...args);
            } finally {
                this.notification = origNotification;
            }
        },
    });
}

// Emergency boot safety: If WebClient fails to mount after 8s on /app, display recovery banner
if (typeof window !== "undefined" && window.location.pathname.startsWith(APP_PATH)) {
    const recoveryTimer = browser.setTimeout(() => {
        const mounted = document.querySelector(".o_navbar") || document.querySelector(".o_action_manager");
        if (!mounted && document.body) {
            const existing = document.getElementById("tp-emergency-recovery");
            if (!existing) {
                const banner = document.createElement("div");
                banner.id = "tp-emergency-recovery";
                banner.setAttribute(
                    "style",
                    "position:fixed;inset:0;background:#f8f9fa;z-index:999999;display:flex;align-items:center;justify-content:center;font-family:system-ui,-apple-system,sans-serif;padding:24px;"
                );
                banner.innerHTML = `
                    <div style="background:#fff;border-radius:12px;padding:32px;max-width:480px;box-shadow:0 10px 25px rgba(0,0,0,0.1);text-align:center;border:1px solid #e2e8f0;">
                        <h2 style="font-size:20px;font-weight:600;color:#0f172a;margin-bottom:12px;">Hệ thống đang tải hoặc gặp sự cố hiển thị</h2>
                        <p style="font-size:14px;color:#64748b;margin-bottom:24px;line-height:1.5;">Giao diện chưa thể hiển thị thành phần màn hình sau khi làm mới. Vui lòng bấm nút bên dưới để thử lại.</p>
                        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
                            <button id="tp-recovery-reload" style="background:#1766c0;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-weight:600;cursor:pointer;font-size:14px;min-height:44px;">Tải lại trang</button>
                            <button id="tp-recovery-home" style="background:#f1f5f9;color:#0f172a;border:1px solid #cbd5e1;padding:10px 20px;border-radius:8px;font-weight:500;cursor:pointer;font-size:14px;">Về Trang chủ</button>
                            <button id="tp-recovery-login" style="background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;padding:10px 20px;border-radius:8px;font-weight:500;cursor:pointer;font-size:14px;">Đăng nhập lại</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(banner);
                document.getElementById("tp-recovery-reload")?.addEventListener("click", () => window.location.reload());
                document.getElementById("tp-recovery-home")?.addEventListener("click", () => { window.location.href = "/app/trang-chu"; });
                document.getElementById("tp-recovery-login")?.addEventListener("click", () => { window.location.href = "/dang-nhap"; });
            }
        }
    }, 8000);

    browser.setTimeout(() => {
        if (document.querySelector(".o_navbar") || document.querySelector(".o_action_manager")) {
            browser.clearTimeout(recoveryTimer);
            document.getElementById("tp-emergency-recovery")?.remove();
        }
    }, 1500);
}
