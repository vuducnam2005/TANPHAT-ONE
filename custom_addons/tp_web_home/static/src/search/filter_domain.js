/** @odoo-module **/
import { Domain } from "@web/core/domain";
import { deserializeDate, serializeDateTime } from "@web/core/l10n/dates";

const FILTER_PROFILES = new Map();

const SKIP_AUTO_FIELDS = new Set([
    "id",
    "create_uid",
    "write_uid",
    "write_date",
    "message_follower_ids",
    "activity_ids",
]);

const AUTO_SUPPORTED_TYPES = new Set(["selection", "many2one", "char", "boolean", "date", "datetime"]);

/**
 * Register a declarative filter profile for a model or `(model, profileKey)`.
 * Criteria entries: `{ key, field, label, type, multi?, allowEmpty?, options?, domain?, placeholder?, positiveLabel?, negativeLabel? }`.
 */
export function registerTableFilterProfile(key, profile) {
    FILTER_PROFILES.set(key, profile);
}

/**
 * Resolve the best-matching filter profile for the open list view, scoped to fields returned by Odoo `get_views`.
 */
export function resolveTableFilterProfile(resModel, context = {}, searchViewFields = {}) {
    const candidates = [
        context?.tp_filter_profile ? `${resModel}::${context.tp_filter_profile}` : null,
        context?.tp_kd_relation ? `${resModel}::relation:${context.tp_kd_relation}` : null,
        context?.tp_hr_relation ? `${resModel}::relation:${context.tp_hr_relation}` : null,
        resModel,
    ].filter(Boolean);

    let matched = null;
    for (const key of candidates) {
        if (FILTER_PROFILES.has(key)) {
            matched = FILTER_PROFILES.get(key);
            break;
        }
    }

    const rawCriteria = matched?.criteria || buildFallbackCriteria(searchViewFields);
    const criteria = rawCriteria
        .map((c) => hydrateCriterion(c, searchViewFields))
        .filter(Boolean);

    return {
        title: matched?.title || "Bộ lọc",
        criteria,
    };
}

function hydrateCriterion(criterion, searchViewFields) {
    if (criterion.type === "preset") {
        // Preset options are checked against declared dependencies on searchViewFields when specified.
        const guardFields = criterion.requireFields || [];
        if (guardFields.some((fname) => !searchViewFields[fname])) {
            return null;
        }
        return { ...criterion, key: criterion.key || criterion.field };
    }
    const fieldMeta = searchViewFields[criterion.field];
    if (!fieldMeta || fieldMeta.searchable === false) {
        return null;
    }
    const type = criterion.type || fieldMeta.type;
    if (!AUTO_SUPPORTED_TYPES.has(type)) {
        return null;
    }
    const label = criterion.label || fieldMeta.string || criterion.field;
    const base = {
        ...criterion,
        key: criterion.key || criterion.field,
        label,
        type,
    };
    if (type === "selection") {
        base.options = criterion.options || fieldMeta.selection || [];
    } else if (type === "many2one") {
        base.relation = criterion.relation || fieldMeta.relation;
        if (!base.relation) {
            return null;
        }
        base.relationDomain = criterion.domain ?? fieldMeta.domain ?? [];
    }
    return base;
}

function buildFallbackCriteria(searchViewFields) {
    const entries = Object.entries(searchViewFields || {})
        .filter(([name, meta]) => meta && meta.searchable !== false && !SKIP_AUTO_FIELDS.has(name) && AUTO_SUPPORTED_TYPES.has(meta.type));
    const priority = { many2one: 0, selection: 1, date: 2, datetime: 2, boolean: 3, char: 4 };
    entries.sort((a, b) => (priority[a[1].type] ?? 9) - (priority[b[1].type] ?? 9));
    return entries.slice(0, 4).map(([name, meta]) => ({
        key: name,
        field: name,
        label: meta.string || name,
        type: meta.type,
        multi: meta.type === "selection",
    }));
}

export function createEmptyCriterionValue(criterion) {
    if (criterion.type === "date" || criterion.type === "datetime") {
        return { from: "", to: "" };
    }
    if (criterion.type === "selection" || criterion.type === "preset") {
        return criterion.multi !== false ? [] : "";
    }
    if (criterion.type === "many2one") {
        return null;
    }
    if (criterion.type === "boolean") {
        return "all";
    }
    return "";
}

export function cloneCriterionValue(criterion, value) {
    if (value == null) {
        return createEmptyCriterionValue(criterion);
    }
    if (Array.isArray(value)) {
        return [...value];
    }
    if (typeof value === "object") {
        return { ...value };
    }
    return value;
}

export function valuesEqual(criterion, a, b) {
    if (criterion.recordSuggestions && (a?.id || b?.id)) {
        return a?.id === b?.id && a?.label === b?.label;
    }
    if (criterion.type === "date" || criterion.type === "datetime") {
        return (a?.from || "") === (b?.from || "") && (a?.to || "") === (b?.to || "");
    }
    if (criterion.type === "many2one") {
        return (a?.id ?? null) === (b?.id ?? null) && Boolean(a?.isFalse) === Boolean(b?.isFalse);
    }
    if (Array.isArray(a) || Array.isArray(b)) {
        const arrA = Array.isArray(a) ? a : a ? [a] : [];
        const arrB = Array.isArray(b) ? b : b ? [b] : [];
        if (arrA.length !== arrB.length) {
            return false;
        }
        return arrA.every((item, idx) => item === arrB[idx]);
    }
    return (a ?? "") === (b ?? "");
}

export function isCriterionEmpty(criterion, value) {
    if (criterion.type === "date" || criterion.type === "datetime") {
        return !(value?.from || value?.to);
    }
    if (criterion.type === "many2one") {
        return !value || (value.id == null && !value.isFalse);
    }
    if (criterion.type === "boolean") {
        return !value || value === "all";
    }
    if (Array.isArray(value)) {
        return value.length === 0;
    }
    return typeof value === "string" ? value.trim() === "" : !value;
}

/**
 * Validate a criterion's pending value and return a Vietnamese error string or `null`.
 */
export function validateCriterionValue(criterion, value) {
    if (criterion.type === "date" || criterion.type === "datetime") {
        const from = value?.from || "";
        const to = value?.to || "";
        if (from && to && from > to) {
            return `${criterion.label}: "Từ ngày" không được lớn hơn "Đến ngày".`;
        }
    }
    return null;
}

/**
 * Convert a single criterion + value into `{ description, domain, snapshot }`, or `null` when empty.
 */
export function buildCriterionFilter(criterion, value) {
    const error = validateCriterionValue(criterion, value);
    if (error) {
        throw new Error(error);
    }
    if (isCriterionEmpty(criterion, value)) {
        return null;
    }
    const snapshot = cloneCriterionValue(criterion, value);

    if (criterion.type === "char") {
        if (criterion.recordSuggestions && value?.id) {
            return {
                description: `${criterion.label}: ${value.label}`,
                domain: new Domain([["id", "=", value.id]]).toString(),
                snapshot,
            };
        }
        const trimmed = String(value).trim();
        return {
            description: `${criterion.label}: ${trimmed}`,
            domain: new Domain([[criterion.field, "ilike", trimmed]]).toString(),
            snapshot,
        };
    }

    if (criterion.type === "boolean") {
        const flag = value === "true" || value === true;
        const text = flag ? criterion.positiveLabel || "Có" : criterion.negativeLabel || "Không";
        return {
            description: `${criterion.label}: ${text}`,
            domain: new Domain([[criterion.field, "=", flag]]).toString(),
            snapshot: flag ? "true" : "false",
        };
    }

    if (criterion.type === "many2one") {
        if (value.isFalse) {
            return {
                description: `${criterion.label}: Chưa khai báo`,
                domain: new Domain([[criterion.field, "=", false]]).toString(),
                snapshot,
            };
        }
        return {
            description: `${criterion.label}: ${value.label}`,
            domain: new Domain([[criterion.field, "=", value.id]]).toString(),
            snapshot,
        };
    }

    if (criterion.type === "selection") {
        const keys = Array.isArray(value) ? value : [value];
        const parts = [];
        const labels = [];
        for (const key of keys) {
            if (key === "__false__") {
                parts.push(new Domain([[criterion.field, "=", false]]));
                labels.push("Chưa khai báo");
            } else {
                parts.push(new Domain([[criterion.field, "=", key]]));
                const opt = (criterion.options || []).find(([k]) => String(k) === String(key));
                labels.push(opt ? opt[1] : String(key));
            }
        }
        const combined = parts.length === 1 ? parts[0] : Domain.or(parts);
        return {
            description: `${criterion.label}: ${labels.join(" hoặc ")}`,
            domain: combined.toString(),
            snapshot,
        };
    }

    if (criterion.type === "preset") {
        const keys = Array.isArray(value) ? value : [value];
        const parts = [];
        const labels = [];
        for (const key of keys) {
            const preset = (criterion.options || []).find((opt) => opt.key === key);
            if (preset) {
                parts.push(new Domain(preset.domain));
                labels.push(preset.label);
            }
        }
        if (!parts.length) {
            return null;
        }
        const combined = parts.length === 1 ? parts[0] : Domain.or(parts);
        return {
            description: `${criterion.label}: ${labels.join(" hoặc ")}`,
            domain: combined.toString(),
            snapshot,
        };
    }

    if (criterion.type === "date" || criterion.type === "datetime") {
        const from = value.from || "";
        const to = value.to || "";
        const clauses = [];
        if (criterion.type === "date") {
            if (from) clauses.push([criterion.field, ">=", from]);
            if (to) clauses.push([criterion.field, "<=", to]);
        } else {
            // Convert local day boundaries in user TZ (e.g. Asia/Ho_Chi_Minh) to UTC using half-open [from 00:00, to+1d 00:00).
            if (from) clauses.push([criterion.field, ">=", serializeDateTime(deserializeDate(from).startOf("day"))]);
            if (to) clauses.push([criterion.field, "<", serializeDateTime(deserializeDate(to).plus({ days: 1 }).startOf("day"))]);
        }
        const rangeLabel = from && to ? `${from} → ${to}` : from ? `từ ${from}` : `đến ${to}`;
        return {
            description: `${criterion.label}: ${rangeLabel}`,
            domain: new Domain(clauses).toString(),
            snapshot,
        };
    }

    return null;
}
