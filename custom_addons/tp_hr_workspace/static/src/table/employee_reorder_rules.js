export const REORDER_LOCK_GUIDANCE =
    "Về thứ tự tùy chỉnh và bỏ bộ lọc nhân viên để sắp xếp";
export const REORDER_SUCCESS_TOAST = "Đã cập nhật thứ tự nhân viên";

/**
 * Return true if domain explicitly requires active = true.
 */
export function domainHasExplicitActiveTrue(domain) {
    if (!Array.isArray(domain)) {
        return false;
    }
    for (const token of domain) {
        if (
            Array.isArray(token) &&
            token.length === 3 &&
            token[0] === "active" &&
            token[1] === "=" &&
            token[2] === true
        ) {
            return true;
        }
    }
    return false;
}

/**
 * Inspect an Odoo domain array and return true ONLY if every condition restricts
 * solely company scope, active = true, or department_id (so no active employees
 * inside any displayed department are hidden).
 */
export function isDepartmentCompleteDomain(domain) {
    if (!Array.isArray(domain) || domain.length === 0) {
        return true;
    }
    for (const token of domain) {
        if (typeof token === "string") {
            if (token === "!") {
                return false;
            }
            if (token === "&" || token === "|") {
                continue;
            }
            return false;
        }
        if (!Array.isArray(token) || token.length !== 3) {
            return false;
        }
        const [field, op, val] = token;
        if (field === 1 && op === "=" && val === 1) {
            continue;
        }
        if (field === "company_id" && (op === "=" || op === "in")) {
            continue;
        }
        if (field === "active" && op === "=" && val === true) {
            continue;
        }
        if (
            field === "department_id" &&
            (op === "=" || op === "in" || op === "child_of")
        ) {
            continue;
        }
        return false;
    }
    return true;
}

/**
 * Return true when list.orderBy uses the saved custom department order (sequence ASC, id ASC).
 */
export function isCustomEmployeeOrder(orderBy) {
    if (!Array.isArray(orderBy) || orderBy.length === 0) {
        return true;
    }
    const first = orderBy[0];
    if (!first || first.name !== "sequence" || first.asc === false) {
        return false;
    }
    if (orderBy.length === 1) {
        return true;
    }
    if (
        orderBy.length === 2 &&
        orderBy[1]?.name === "id" &&
        orderBy[1]?.asc !== false
    ) {
        return true;
    }
    return false;
}

/**
 * Compute full drag-and-drop eligibility and lock reason for TP HR Employee List.
 */
export function analyzeEmployeeReorderState({
    resModel,
    isGrouped,
    groupBy,
    orderBy,
    domain,
    context,
    displayName,
    canReorderSession,
    readonly,
    canEditView,
}) {
    const authorized = Boolean(canReorderSession && !readonly && canEditView !== false);
    const isArchivedAction =
        context?.active_test === false && !domainHasExplicitActiveTrue(domain);
    const isPendingAction =
        Boolean(context?.tp_hr_pending) || displayName === "Chưa có tài khoản";
    const isEmployeeMainSurface =
        resModel === "hr.employee" &&
        !context?.tp_hr_relation &&
        !context?.tp_hr_missing &&
        !isArchivedAction &&
        !isPendingAction;

    if (!authorized || !isEmployeeMainSurface) {
        return {
            showHandleColumn: false,
            canDrag: false,
            showLockBanner: false,
            isCustomOrder: true,
            hasEmployeeFilter: false,
        };
    }

    const singleDeptGroup =
        Boolean(isGrouped) &&
        Array.isArray(groupBy) &&
        groupBy.length === 1 &&
        groupBy[0] === "department_id";
    const customOrder = isCustomEmployeeOrder(orderBy);
    const domainComplete = isDepartmentCompleteDomain(domain);
    const hasEmployeeFilter = !singleDeptGroup || !domainComplete;
    const canDrag = singleDeptGroup && customOrder && domainComplete;

    return {
        showHandleColumn: true,
        canDrag,
        showLockBanner: !canDrag,
        isCustomOrder: customOrder,
        hasEmployeeFilter,
    };
}
