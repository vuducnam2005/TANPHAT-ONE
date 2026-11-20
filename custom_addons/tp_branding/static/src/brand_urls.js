// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * TANPHAT ONE URL vocabulary for the webclient (BRAND-WHITELABEL-002, SYSTEM-URL-001).
 * Mirrors `tp_branding/brand_urls.py`.
 */

import { parseBrandedUrl } from "./brand_routes";

export const BRAND_NAME = "TANPHAT ONE";
export const BRAND_CREDIT = "Phát triển bởi TADIC";
export const APP_PATH = "/app";
export const LEGACY_APP_PATH = "/odoo";
export const LOGIN_PATH = "/dang-nhap";
export const RESET_PATH = "/quen-mat-khau";

// Real static routes under /odoo that are not webclient paths.
const UNBRANDED_PATHS = new Set(["/odoo/offline"]);

export function isAppPath(path) {
    return path === APP_PATH || path.startsWith(APP_PATH + "/");
}

export function isLegacyAppPath(path) {
    if (UNBRANDED_PATHS.has(path)) {
        return false;
    }
    return path === LEGACY_APP_PATH || path.startsWith(LEGACY_APP_PATH + "/");
}

/**
 * `/odoo...` -> `/app...` and canonicalize legacy aliases/actions to business URLs.
 */
export function brandPath(path) {
    let target = path;
    if (isLegacyAppPath(path)) {
        target = APP_PATH + path.slice(LEGACY_APP_PATH.length);
    }
    if (isAppPath(target)) {
        const parsed = parseBrandedUrl(target);
        if (parsed.canonicalUrl) {
            return parsed.canonicalUrl;
        }
    }
    return target;
}

/** `/app...` -> `/odoo...` for a local path, anything else unchanged. */
export function nativePath(path) {
    if (isAppPath(path)) {
        return LEGACY_APP_PATH + path.slice(APP_PATH.length);
    }
    return path;
}

function isLocalUrl(url) {
    return (
        typeof url === "string" &&
        url.startsWith("/") &&
        !url.startsWith("//") &&
        !url.startsWith("/\\")
    );
}

function splitUrl(url) {
    let cut = url.length;
    for (const sep of ["?", "#"]) {
        const idx = url.indexOf(sep);
        if (idx !== -1 && idx < cut) {
            cut = idx;
        }
    }
    return [url.slice(0, cut), url.slice(cut)];
}

/** Brand a relative URL (`/odoo/x?y#z` -> `/app/x?y#z` or canonical business URL). */
export function brandUrl(url) {
    if (!isLocalUrl(url)) {
        return url;
    }
    const [path, rest] = splitUrl(url);
    return brandPath(path) + rest;
}

/** Native Odoo URL from branded relative URL. */
export function nativeUrl(url) {
    if (!isLocalUrl(url)) {
        return url;
    }
    const [path, rest] = splitUrl(url);
    return nativePath(path) + rest;
}

/** Brand an absolute URL of this origin, anything else unchanged. */
export function brandHref(href, origin) {
    if (typeof href !== "string" || !origin || !href.startsWith(origin + "/")) {
        return brandUrl(href);
    }
    return origin + brandUrl(href.slice(origin.length));
}

/** `"<page> | TANPHAT ONE"`, never doubled, `TANPHAT ONE` when empty. */
export function brandTitle(title) {
    const clean = (title || "").trim();
    if (!clean || clean === "Odoo" || clean === BRAND_NAME) {
        return BRAND_NAME;
    }
    if (clean.endsWith("| " + BRAND_NAME)) {
        return clean;
    }
    return `${clean} | ${BRAND_NAME}`;
}
