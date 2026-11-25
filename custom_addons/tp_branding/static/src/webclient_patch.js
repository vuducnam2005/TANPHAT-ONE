// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: service worker on the `/app` scope.
 *
 * Same registration/activation logic as the native webclient, only the scope
 * differs. The legacy registration of this same worker on `/odoo` (this
 * origin, this script) is removed because no page lives there any more; no
 * other registration and no browser storage is touched.
 */

import { browser } from "@web/core/browser/browser";
import { rpcBus } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { APP_PATH, LEGACY_APP_PATH } from "@tp_branding/brand_urls";
import { HOME_MENU_XMLID } from "@tp_web_home/home/home_catalog";

const SW_SCRIPT_PATH = "/web/service-worker.js";

function syncHomeMenu(menuService) {
    const home = menuService?.getAll?.().find((m) => m.xmlid === HOME_MENU_XMLID);
    if (home && menuService.getCurrentApp?.()?.id !== home.id) {
        menuService.setCurrentMenu(home);
    }
}

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

patch(WebClient.prototype, {
    async loadRouterState() {
        try {
            await super.loadRouterState();
        } catch (error) {
            console.error("TANPHAT ONE: loadRouterState error, attempting fallback:", error);
            try {
                await this.actionService.doAction("tp_web_home.action_home", {
                    clearBreadcrumbs: true,
                });
                syncHomeMenu(this.menuService);
            } catch (fallbackError) {
                console.error("TANPHAT ONE: fallback to home failed:", fallbackError);
                await this._loadDefaultApp();
            }
        }

        // Post-load check: ensure action manager has active content
        browser.setTimeout(() => {
            const actionManager = document.querySelector(".o_action_manager");
            if (actionManager && actionManager.children.length === 0) {
                console.warn("TANPHAT ONE: Action manager empty after boot, loading default home...");
                this.actionService
                    .doAction("tp_web_home.action_home", { clearBreadcrumbs: true })
                    .then(() => syncHomeMenu(this.menuService))
                    .catch(() => this._loadDefaultApp());
            }
        }, 500);
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
});

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
                            <button id="tp-recovery-reload" style="background:#0284c7;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-weight:500;cursor:pointer;font-size:14px;">Tải lại trang</button>
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
