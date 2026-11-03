import { _t } from "@web/core/l10n/translation";

export const PROJECTION_MODEL = "tp.demo.workspace";

// Native read-only forms of the demo; the canonical models keep their rules.
export const FORM_VIEWS = {
    "project.project": "tp_demo_workspace.view_demo_project_form",
    "project.task": "tp_demo_workspace.view_demo_task_form",
    "tp.contract": "tp_demo_workspace.view_demo_contract_form",
    "tp.contract.revision": "tp_demo_workspace.view_demo_revision_form",
    "tp.contract.document": "tp_demo_workspace.view_demo_document_form",
    "crm.lead": "tp_demo_workspace.view_demo_lead_form",
};

/**
 * Open a native window action with the domain computed by the projection,
 * so the list shows exactly the records behind the number that was clicked.
 */
export async function openList(actionService, target, name) {
    const action = await actionService.loadAction(target.action);
    const title = name || action.display_name || action.name;
    await actionService.doAction({
        ...action,
        domain: target.domain,
        name: title,
        display_name: title,
    });
}

export function openRecord(actionService, resModel, resId) {
    return actionService.doAction({
        type: "ir.actions.act_window",
        res_model: resModel,
        res_id: resId,
        views: [[false, "form"]],
        context: { form_view_ref: FORM_VIEWS[resModel] },
    });
}

export function openProjectOverview(actionService, projectId) {
    return actionService.doAction("tp_demo_workspace.action_demo_project_overview", {
        additionalContext: { active_id: projectId },
    });
}

export function describeError(error) {
    const name = error?.data?.name || "";
    if (name.endsWith("AccessError")) {
        return { denied: true, message: _t("Không có quyền xem nội dung này.") };
    }
    return { denied: false, message: error?.data?.message || error?.message || _t("Không tải được dữ liệu.") };
}

/**
 * Load a projection into ``state`` without blocking the first render, so the
 * loading skeleton is visible and errors land in ``state.error``.
 */
export async function loadInto(state, loader) {
    state.loading = true;
    state.error = null;
    try {
        state.data = await loader();
    } catch (error) {
        state.data = null;
        state.error = describeError(error);
    } finally {
        state.loading = false;
    }
}
