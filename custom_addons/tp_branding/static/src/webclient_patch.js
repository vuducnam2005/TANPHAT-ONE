// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: service worker on the `/app` scope.
 *
 * Same registration/activation logic as the native webclient, only the scope
 * differs. The legacy registration of this same worker on `/odoo` (this
 * origin, this script) is removed because no page lives there any more; no
 * other registration and no browser storage is touched.
 */

import { rpcBus } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { APP_PATH, LEGACY_APP_PATH } from "@tp_branding/brand_urls";

const SW_SCRIPT_PATH = "/web/service-worker.js";

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
                    sw.addEventListener("statechange", (e) => {
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
