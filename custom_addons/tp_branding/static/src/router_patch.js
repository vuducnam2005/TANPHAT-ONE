// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002, SYSTEM-URL-001:
 * Standardized hierarchical business URLs under `/app` on native router.
 *
 * Uses the documented extension points of `@web/core/browser/router` (the
 * `router` object is patchable: "state <-> url conversions can be patched if
 * needed in a custom webclient").
 *
 * - `stateToUrl`: Transforms native state / action into canonical business URLs
 *   (e.g. `/app/nhan-su/nhan-vien/44`, `/app/nhan-su/nhan-vien/tao-moi`)
 *   instead of technical identifiers like `action-528`.
 * - `urlToState`: Parses hierarchical business URLs back to native Odoo state
 *   and actions for full deep-link, reload (F5), and backward compatibility.
 * - In-app navigation: click listener captures clicks on `/app/...` internal links.
 * - History: Back/Forward popstate preserved without full page reloads.
 *
 * No core Odoo modifications, no independent frontend or replaceState masking.
 */

import { browser } from "@web/core/browser/browser";
import { router, routerBus } from "@web/core/browser/router";
import { patch } from "@web/core/utils/patch";
import {
    APP_PATH,
    LEGACY_APP_PATH,
    brandHref,
    isAppPath,
    isLegacyAppPath,
} from "@tp_branding/brand_urls";
import {
    buildBrandedUrl,
    findRouteByAction,
    getActionIdByXmlId,
    parseBrandedUrl,
} from "@tp_branding/brand_routes";

const LEGACY_PREFIX_RE = /^\/odoo(?=[/?#]|$)/;

// > 0 while the native parser runs: it calls `router.stateToUrl` itself and
// expects the native `/odoo` vocabulary back.
let nativeDepth = 0;

// State of an internal link clicked on an `/app` page, exposed through
// `router.current` until the next push/replace or history move, exactly like
// the native click listener does with the router's private state.
let pending = null;

function hasHashState(hash) {
    return Boolean(hash) && hash !== "#" && hash.includes("=");
}

patch(router, {
    get current() {
        if (pending) {
            if (pending.href === browser.location.href) {
                return pending.state;
            }
            pending = null;
        }
        return super.current;
    },

    stateToUrl(state) {
        // When native parser runs internally, return standard native vocabulary
        if (nativeDepth) {
            return super.stateToUrl(state);
        }

        // Try mapping the active action in state to a standardized business route
        const activeAction = state?.actionStack?.at(-1) || state;
        const actionIdentifier = activeAction?.action;
        const resId = activeAction?.resId !== undefined ? activeAction.resId : state?.resId;

        const route = findRouteByAction(actionIdentifier);
        if (route) {
            const isNew = resId === "new";
            const businessPath = buildBrandedUrl(route, { resId, isNew });
            if (businessPath) {
                // Get native search query from super.stateToUrl (preserves ?debug=, filters, etc.)
                nativeDepth++;
                let nativeUrl;
                try {
                    nativeUrl = super.stateToUrl(state);
                } finally {
                    nativeDepth--;
                }
                const queryIndex = nativeUrl.indexOf("?");
                const query = queryIndex !== -1 ? nativeUrl.slice(queryIndex) : "";
                return businessPath + query;
            }
        }

        // Fallback: standard native URL with /odoo -> /app prefix swap
        const url = super.stateToUrl(state);
        return url.replace(LEGACY_PREFIX_RE, APP_PATH);
    },

    urlToState(urlObj) {
        const { pathname, hash } = urlObj;
        const fromApp = isAppPath(pathname);
        let target = urlObj;

        if (fromApp) {
            target = new URL(urlObj.href);

            // 1. Handle legacy hash state: /app#action=...
            if (pathname === APP_PATH && hasHashState(hash)) {
                target.pathname = "/web";
            } else {
                // 2. Check if pathname matches a registered business route
                const parsed = parseBrandedUrl(pathname);
                if (parsed.route) {
                    const route = parsed.route;
                    let actionId = null;
                    if (route.action_xml_id) {
                        actionId = getActionIdByXmlId(route.action_xml_id) || route.action_xml_id;
                    } else if (route.action_tag) {
                        actionId = route.action_tag;
                    } else if (route.native_slug) {
                        actionId = route.native_slug;
                    }

                    if (actionId) {
                        let nativeSegment;
                        if (
                            typeof actionId === "number" ||
                            (typeof actionId === "string" && actionId.includes("."))
                        ) {
                            nativeSegment = `action-${actionId}`;
                        } else {
                            nativeSegment = actionId;
                        }

                        let nativeSub = `/${nativeSegment}`;
                        if (parsed.isNew || parsed.resId === "new") {
                            nativeSub += "/new";
                        } else if (typeof parsed.resId === "number") {
                            nativeSub += `/${parsed.resId}`;
                        }

                        target.pathname = `${LEGACY_APP_PATH}${nativeSub}`;
                    } else {
                        target.pathname = LEGACY_APP_PATH + pathname.slice(APP_PATH.length);
                    }
                } else {
                    target.pathname = LEGACY_APP_PATH + pathname.slice(APP_PATH.length);
                }
            }
        }

        const before = target.href;
        let state;
        nativeDepth++;
        try {
            state = super.urlToState(target);
        } finally {
            nativeDepth--;
        }

        if (fromApp || target.href !== before) {
            // Keep URL in address bar canonical and branded
            const parsed = parseBrandedUrl(pathname);
            if (parsed.canonicalUrl) {
                const searchAndHash = (urlObj.search || "") + (urlObj.hash || "");
                urlObj.href = brandHref(
                    parsed.canonicalUrl + searchAndHash,
                    browser.location.origin
                );
            } else {
                urlObj.href = brandHref(target.href, browser.location.origin);
            }
        }
        return state;
    },

    pushState(...args) {
        pending = null;
        return super.pushState(...args);
    },

    replaceState(...args) {
        pending = null;
        return super.replaceState(...args);
    },
});

if (router.shareUrl) {
    // Native shares `/scoped_app` links as `/odoo`; share the branded URL.
    router.shareUrl = async function shareBrandedUrl() {
        const url = browser.location.href.replace("/scoped_app", APP_PATH);
        await browser.navigator.share({ url, title: document.title }).catch((e) => {
            if (!(e instanceof DOMException && e.name === "AbortError")) {
                throw e;
            }
        });
    };
}

// History moves always replace a pending click state.
browser.addEventListener(
    "popstate",
    () => {
        pending = null;
    },
    true
);

/**
 * In-app navigation for internal links on `/app` pages (native parity with
 * the `/odoo` listener of the router; modifier clicks and `_blank` keep the
 * browser behaviour so "open in new tab" works).
 */
browser.addEventListener("click", (ev) => {
    if (
        ev.defaultPrevented ||
        ev.button !== 0 ||
        ev.ctrlKey ||
        ev.metaKey ||
        ev.shiftKey ||
        ev.altKey ||
        !isAppPath(browser.location.pathname) ||
        !(ev.target instanceof Element) ||
        ev.target.closest("[contenteditable]")
    ) {
        return;
    }
    const a = ev.target.closest("a");
    const href = a?.getAttribute("href");
    if (!href || href.startsWith("#") || a.target === "_blank" || a.hasAttribute("download")) {
        return;
    }
    let url;
    try {
        url = new URL(a.href);
    } catch {
        return;
    }
    const path = url.pathname;
    const isWebclientPath = isAppPath(path) || isLegacyAppPath(path);
    if (url.host !== browser.location.host || !(path === "/web" || isWebclientPath)) {
        return;
    }
    ev.preventDefault();
    const state = router.urlToState(url);
    if (isWebclientPath && url.hash) {
        browser.history.pushState({}, "", brandHref(url.href, browser.location.origin));
    }
    pending = { state, href: browser.location.href };
    browser.setTimeout(() => routerBus.trigger("ROUTE_CHANGE"));
});

// Boot: re-read the URL with the patched parser before the webclient mounts
// (the router parsed `/app/...` with the native parser at import time).
if (isAppPath(browser.location.pathname)) {
    const url = new URL(browser.location.href);
    router.replaceState(router.urlToState(url), { replace: true, sync: true });
}
