import { Component, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";

/**
 * UI-BACK-001 (DEC-046) — one "← Quay lại" for detail screens.
 * Return = restore the previous controller of the action stack (filters, sort, group, page and
 * scroll come back with it). Deep links without a previous screen fall back to an action xmlid
 * registered per model in `tp_back_fallbacks`. Never window.history, never a URL, never a write.
 */
export const HOME_ACTION = "tp_web_home.action_home";
export const backFallbacks = registry.category("tp_back_fallbacks");
// Native screens that are not record details (no back button there).
export const BACK_EXCLUDED_MODELS = new Set(["res.config.settings", "base.module.upgrade", "base.module.uninstall"]);

const XMLID_RE = /^[a-z0-9_]+\.[A-Za-z0-9_]+$/;

export function previousBreadcrumb(env) {
    const crumbs = env.config?.breadcrumbs || [];
    return crumbs.length > 1 ? crumbs.at(-2) : null;
}

/** Registered fallback action xmlid for a model (a string or a function of the record data), else null. */
export function registeredBackFallback(resModel, data = {}) {
    let target = null;
    if (resModel && backFallbacks.contains(resModel)) {
        const entry = backFallbacks.get(resModel);
        try {
            target = typeof entry === "function" ? entry(data || {}) : entry;
        } catch {
            target = null;
        }
    }
    return typeof target === "string" && XMLID_RE.test(target) ? target : null;
}

/**
 * Where "Quay lại" goes without a previous screen: the model's registered list, else the list of
 * the action this form belongs to (its own workspace), else Home.
 */
export function resolveBackFallback(resModel, data = {}, config = {}) {
    const registered = registeredBackFallback(resModel, data);
    if (registered) {
        return registered;
    }
    const multi = (config.views || []).some(([, type]) => ["list", "kanban"].includes(type));
    if (Number.isInteger(config.actionId) && config.actionId > 0 && multi) {
        return config.actionId;
    }
    return HOME_ACTION;
}

export function backTooltip(env) {
    const prev = previousBreadcrumb(env);
    const name = prev && (prev.name || "").toString().trim();
    return name ? `Quay lại: ${name}` : "Quay lại danh sách";
}

export class TpUnsavedBackDialog extends Component {
    static template = "tp_web_home.UnsavedBackDialog";
    static components = { Dialog };
    props = useProps();
    choose(choice) {
        this.props.resolve(choice);
        this.props.close();
    }
}

export function askUnsavedChoice(dialogService) {
    return new Promise((resolve) => {
        let done = false;
        const once = (choice) => {
            if (!done) {
                done = true;
                resolve(choice);
            }
        };
        dialogService.add(TpUnsavedBackDialog, { resolve: once }, { onClose: () => once("stay") });
    });
}

/** Restore the previous screen, else open the fallback action (clears the stale stack). */
/**
 * Async variant used by navigation: a registered fallback may be async and receives
 * `{ resId, orm }` so it can read (never write) the few fields it needs when the opened
 * form does not carry them (e.g. a model-only deep link served by another form view).
 */
export async function resolveBackTarget(resModel, data = {}, config = {}, extra = {}) {
    let target = null;
    if (resModel && backFallbacks.contains(resModel)) {
        const entry = backFallbacks.get(resModel);
        try {
            target = typeof entry === "function" ? await entry(data || {}, extra || {}) : entry;
        } catch {
            target = null;
        }
    }
    if (typeof target === "string" && XMLID_RE.test(target)) {
        return target;
    }
    return resolveBackFallback(null, {}, config);
}

export async function navigateBack(env, actionService, { resModel, resId, data } = {}) {
    const prev = previousBreadcrumb(env);
    if (prev) {
        await actionService.restore(prev.jsId);
        return true;
    }
    const target = await resolveBackTarget(resModel, data, env.config || {}, { resId, orm: env.services?.orm });
    await actionService.doAction(target, { clearBreadcrumbs: true });
    return true;
}

/**
 * Leave a form record through its unsaved-changes guard:
 *  - "Ở lại": nothing happens; - "Bỏ thay đổi": record.discard() then leave;
 *  - "Lưu và quay lại": leave only when record.save() succeeds (invalid/errored saves stay).
 */
export async function leaveRecordAndGoBack(env, { actionService, dialogService, record }) {
    if (record && (await record.isDirty())) {
        const choice = await askUnsavedChoice(dialogService);
        if (choice === "stay") {
            return false;
        }
        if (choice === "save") {
            const saved = await record.save();
            if (!saved) {
                return false;
            }
        } else if (choice === "discard") {
            await record.discard();
        } else {
            return false;
        }
    }
    return navigateBack(env, actionService, { resModel: record?.resModel, resId: record?.resId, data: record?.data });
}
