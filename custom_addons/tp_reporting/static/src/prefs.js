import { proxy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { session } from "@web/session";

/**
 * EQUIP-001 personal display options (same model as KD-UI-002). Presentation only: nothing here
 * changes data, rights or which records the server returns. Stored per database and user.
 */
const PAGE_SIZES = [10, 20, 50, 100];

export function defaults() {
    return { collapsed: false, density: "comfortable", motion: "auto", groups: null };
}

function storageKey() {
    return `tp_reporting_ui:v1:${session.db || ""}:${user.userId || 0}`;
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
        value.groups = raw.groups.filter((g) => typeof g === "string").slice(0, 20);
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

export const reportPrefs = proxy(load());

export function savePrefs(changes = {}) {
    Object.assign(reportPrefs, sanitize({ ...reportPrefs, ...changes }));
    try {
        browser.localStorage.setItem(storageKey(), JSON.stringify(reportPrefs));
    } catch {
        // Private mode or full storage: keep the in-memory value for this tab only.
    }
}

export const REPORT_COLUMN_PREFIXES = new Set();

export function forgetColumns(prefixes) {
    try {
        for (let index = browser.localStorage.length - 1; index >= 0; index--) {
            const key = browser.localStorage.key(index);
            if (key && [...prefixes].some((prefix) => key.startsWith(prefix))) {
                browser.localStorage.removeItem(key);
            }
        }
    } catch {
        // Storage unavailable: nothing stored to forget.
    }
}

export function resetPrefs() {
    try {
        browser.localStorage.removeItem(storageKey());
    } catch {
        // ignore
    }
    forgetColumns(REPORT_COLUMN_PREFIXES);
    Object.assign(reportPrefs, defaults());
}

export const PAGE_SIZE_OPTIONS = PAGE_SIZES;
// One page for lists that must not page (users list); a larger set still pages past it.
export const ALL_ROWS_LIMIT = 1000;

// Only the page length is persisted; no record IDs, domains or search text.
export function tablePageKey(model, action, view) {
    return `tp_reporting_page:v1:${session.db || ""}:${user.userId || 0}:${model}:${action || ""}:${view || ""}`;
}
export function readPageSize(key) {
    try {
        const value = Number(browser.localStorage.getItem(key));
        return PAGE_SIZES.includes(value) ? value : 20;
    } catch {
        return 20;
    }
}
export function writePageSize(key, value) {
    if (!PAGE_SIZES.includes(value)) {
        return;
    }
    try {
        browser.localStorage.setItem(key, String(value));
    } catch {
        // tab remains usable
    }
}

/** Vietnamese search without diacritics: "may in" matches "Máy in". */
export function fold(text) {
    return (text || "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .trim();
}

export function isModifiedClick(ev) {
    return ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0;
}

export const REPORT_APP_XMLID = "tp_reporting.menu_root";
export const LAST_LEAF_KEY = `tp_reporting_ui:last_leaf:${session.db || ""}:${user.userId || 0}`;
