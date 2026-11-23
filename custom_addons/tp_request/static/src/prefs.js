/** @odoo-module **/
import { proxy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";

export const REQ_APP_XMLID = "tp_request.menu_root";
export const LAST_LEAF_KEY = "tp_request.last_leaf.v1";
const PREFS_KEY = "tp_request.prefs.v1";

export const DEFAULT_PREFS = {
    collapsed: false,
    motion: "auto",
};

function readJson(storage, key, fallback = {}) {
    try {
        const raw = storage?.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch {
        return fallback;
    }
}

function writeJson(storage, key, val) {
    try {
        storage?.setItem(key, JSON.stringify(val));
    } catch {
        // Storage unavailable in private mode
    }
}

export const reqPrefs = proxy({
    ...DEFAULT_PREFS,
    ...readJson(browser.localStorage, PREFS_KEY, {}),
});

export function saveReqPrefs(patch) {
    Object.assign(reqPrefs, patch);
    writeJson(browser.localStorage, PREFS_KEY, {
        collapsed: reqPrefs.collapsed,
        motion: reqPrefs.motion,
    });
}

export function foldText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[đĐ]/g, "d")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
}

export function isModifiedClick(ev) {
    return Boolean(ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0);
}

/**
 * Persist list filter/page/scroll state per database + user + mode in sessionStorage
 * so clicking "Quay lại" or browser Back restores filters, page, and list position.
 */
function listStateKey(mode) {
    const db = session?.db || "tp";
    const uid = session?.uid || 0;
    return `tp_request.list.${db}.${uid}.${mode}`;
}

export function readListState(mode) {
    const saved = readJson(browser.sessionStorage, listStateKey(mode), null);
    return saved?.pageSizeVersion === 2 ? saved : { ...saved, page_size: 100 };
}

export function writeListState(mode, state) {
    writeJson(browser.sessionStorage, listStateKey(mode), { ...state, pageSizeVersion: 2 });
}

export function writeLastListMode(mode) {
    try {
        browser.sessionStorage?.setItem("tp_request.last_mode", String(mode || "mine"));
    } catch {
        // ignore
    }
}

export function readLastListMode() {
    try {
        return browser.sessionStorage?.getItem("tp_request.last_mode") || "mine";
    } catch {
        return "mine";
    }
}

export const MODE_TO_ACTION = {
    overview: "tp_request.action_overview",
    mine: "tp_request.action_mine",
    to_approve: "tp_request.action_to_approve",
    to_execute: "tp_request.action_to_execute",
    watching: "tp_request.action_watching",
    admin: "tp_request.action_admin",
};

export const APPROVAL_BADGE = {
    draft: { cls: "is-draft", icon: "edit_note", label: "Nháp" },
    pending: { cls: "is-pending", icon: "schedule", label: "Chờ duyệt" },
    returned: { cls: "is-returned", icon: "undo", label: "Trả lại bổ sung" },
    approved: { cls: "is-approved", icon: "check_circle", label: "Đã duyệt" },
    rejected: { cls: "is-rejected", icon: "cancel", label: "Từ chối" },
    withdrawn: { cls: "is-withdrawn", icon: "remove_circle_outline", label: "Đã rút / hủy" },
};

export const EXEC_BADGE = {
    not_applicable: { cls: "is-na", icon: "remove", label: "—" },
    waiting_approval: { cls: "is-draft", icon: "hourglass_empty", label: "Chờ duyệt xong" },
    pending: { cls: "is-pending", icon: "pending_actions", label: "Chờ thực hiện" },
    in_progress: { cls: "is-progress", icon: "autorenew", label: "Đang thực hiện" },
    done: { cls: "is-approved", icon: "task_alt", label: "Hoàn thành" },
    cancelled: { cls: "is-rejected", icon: "block", label: "Không thực hiện" },
};

export const PRIORITY_BADGE = {
    normal: { cls: "is-normal", label: "Bình thường" },
    high: { cls: "is-high", label: "Cao" },
    urgent: { cls: "is-urgent", label: "Khẩn cấp" },
};

export function formatFileSize(bytes) {
    const num = Number(bytes || 0);
    if (num < 1024) return `${num} B`;
    if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`;
    return `${(num / (1024 * 1024)).toFixed(1)} MB`;
}

export function extractErrorMessage(err, fallback = "Không thể thực hiện thao tác. Vui lòng thử lại.") {
    return (
        err?.data?.message ||
        err?.message?.data?.message ||
        (typeof err?.message === "string" ? err.message : "") ||
        fallback
    );
}

/**
 * Open a request detail page at canonical URL /app/de-nghi/ho-so/<id>.
 */
export async function openRequestDetail(actionService, requestId, fromMode = "") {
    if (fromMode) {
        writeLastListMode(fromMode);
    }
    return actionService.doAction("tp_request.action_detail", {
        additionalContext: { tp_request_id: Number(requestId), tp_from_mode: fromMode },
        props: { resId: Number(requestId) },
    });
}
