import { proxy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { defaults } from "@tp_hr_workspace/prefs";

export const ATT_APP_XMLID = "tp_hr_attendance.menu_root";
export const ATT_LAST_LEAF_KEY = "tp_att_ui:last_leaf";

function identity() {
    return `${session.db || ""}:${user.userId || 0}:${user.activeCompanies?.map((c) => c.id).join(",") || ""}:tp_att`;
}

function storageKey() {
    return `tp_att_ui:v1:${identity()}`;
}

function sanitize(raw) {
    const value = defaults();
    if (!raw || typeof raw !== "object") {
        return value;
    }
    if (typeof raw.collapsed === "boolean") {
        value.collapsed = raw.collapsed;
    }
    if (["comfortable", "compact"].includes(raw.density)) {
        value.density = raw.density;
    }
    if (["auto", "reduced"].includes(raw.motion)) {
        value.motion = raw.motion;
    }
    if (Array.isArray(raw.groups)) {
        value.groups = raw.groups.filter((g) => typeof g === "string").slice(0, 30);
    }
    return value;
}

function load() {
    try {
        return sanitize(JSON.parse(browser.localStorage.getItem(storageKey()) || "null"));
    } catch {
        return defaults();
    }
}

export const attPrefs = proxy(load());

export function saveAttPrefs(changes = {}) {
    Object.assign(attPrefs, sanitize({ ...attPrefs, ...changes }));
    try {
        browser.localStorage.setItem(storageKey(), JSON.stringify(attPrefs));
    } catch {
        // unavailable storage keeps this tab usable
    }
}

export function resetAttPrefs() {
    try {
        browser.localStorage.removeItem(storageKey());
    } catch {
        // unavailable
    }
    Object.assign(attPrefs, defaults());
}
