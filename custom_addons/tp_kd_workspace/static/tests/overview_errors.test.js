import { describe, expect, test } from "@odoo/hoot";
import { makeServerError } from "@web/../tests/web_test_helpers";
import { TpKdOverview } from "@tp_kd_workspace/overview/overview";

/** FORM-VALIDATION-002: open/create failures stay on the overview instead of a danger toast. */
function overview(call) {
    const comp = Object.create(TpKdOverview.prototype);
    comp.state = { filters: { project_id: false }, filtersOpen: false, actionErrors: [], actionError: null, actionAttempt: 0 };
    comp.orm = { call };
    comp.action = { doAction: async () => expect.step("doAction") };
    comp.notification = { add: (message, { type }) => expect.step(type) };
    return comp;
}

describe("KD overview open/create errors", () => {
    test("adding a task without a project points to the project filter before any call", async () => {
        const comp = overview(async () => expect.step("rpc"));
        await comp.create("task");
        expect.verifySteps([]);
        expect(comp.state.filtersOpen).toBe(true);
        expect(comp.state.actionErrors).toEqual([{ id: "tp_kd_filter_project", label: "Dự án", location: "Bộ lọc",
            message: "Chọn Dự án trên Tổng quan trước khi thêm công việc / WBS." }]);
        expect(comp.state.actionAttempt).toBe(1);
    });

    test("a server refusal is classified with the action the user tried and kept on screen", async () => {
        const comp = overview(async () => {
            throw makeServerError({ type: "AccessError", description: "Bạn chưa có quyền tạo loại hồ sơ này." });
        });
        await comp.create("payment");
        expect.verifySteps([]);
        expect(comp.state.actionError).toEqual({ kind: "access", title: "Không có quyền thêm mới",
            message: "Bạn chưa có quyền tạo loại hồ sơ này.", note: "Bộ lọc và số liệu đang xem được giữ nguyên." });
        await comp.projectAction("action_kd_open_contracts", 7);
        expect(comp.state.actionError.title).toBe("Không có quyền mở hồ sơ");
        expect(comp.state.actionAttempt).toBe(2);
    });

    test("a successful open clears the previous error", async () => {
        const comp = overview(async (model, method, args) => {
            expect.step(`${model}.${method}`);
            return { type: "ir.actions.act_window", res_model: "project.project", views: [[false, "form"]] };
        });
        comp.state.actionError = { kind: "system", title: "x", message: "y" };
        comp.state.actionErrors = [{ id: "tp_kd_filter_project" }];
        comp.state.filters.project_id = 3;
        await comp.create("task");
        expect.verifySteps(["tp.kd.overview.action_kd_create", "doAction"]);
        expect(comp.state.actionError).toBe(null);
        expect(comp.state.actionErrors).toEqual([]);
    });
});
