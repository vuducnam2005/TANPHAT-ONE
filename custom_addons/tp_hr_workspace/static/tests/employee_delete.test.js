import { describe, expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-dom";
import { assignDialogTestEnv, contains, mockService, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import {
    DELETE_WARNING,
    EmployeeDelete,
    deleteBlockers,
    deleteInputError,
    requestId,
} from "@tp_hr_workspace/delete/employee_delete";

defineMailModels();

// Synthetic data only; no real account or password.
function preview(extra = {}) {
    return {
        count: 1,
        accountCount: 1,
        digest: "synthetic-digest",
        adminLogin: "synthetic.admin",
        employees: [{
            id: 7,
            name: "Nhân viên giả",
            code: "TP-SYN-01",
            sourceCode: "SYN01",
            department: "Phòng giả",
            active: true,
            login: "synthetic.employee",
            accountActive: true,
            delete: [{ label: "Phiên bản hồ sơ (lịch sử công tác)", value: 1 }],
            keep: [{ label: "Lô nhập và file Excel gốc được giữ nguyên", value: 1 }],
            block: [],
            lockBlock: [],
            keepBlock: [],
            ...extra,
        }],
    };
}

describe("HR-DELETE-010 helpers", () => {
    test("warning text is exact and request ids are UUIDs", () => {
        expect(DELETE_WARNING).toBe("Hồ sơ sẽ bị xóa vĩnh viễn khỏi hệ thống. Thao tác này không thể hoàn tác bằng chức năng Bỏ lưu trữ.");
        const id = requestId();
        expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
        expect(requestId()).not.toBe(id);
    });

    test("blockers depend on the account option and input checks stay local", () => {
        const data = preview({ keepBlock: ["Tài khoản còn trưởng phòng/ban"], lockBlock: [] });
        expect(deleteBlockers(data, false)).toHaveLength(1);
        expect(deleteBlockers(data, true)).toHaveLength(0);
        const blocked = preview({ block: [{ label: "Nhân viên – Quản lý", value: 2, hint: "Đổi người quản lý trước." }] });
        expect(deleteBlockers(blocked, true)[0].reasons[0]).toBe("Nhân viên – Quản lý (2): Đổi người quản lý trước.");
        expect(deleteInputError({ reason: " ", password: "x" }).field).toBe("reason");
        expect(deleteInputError({ reason: "Nhập trùng", password: "" }).field).toBe("password");
        expect(deleteInputError({ reason: "Nhập trùng", password: "x" })).toBe(null);
    });
});

describe("HR-DELETE-010 confirmation dialog", () => {
    describe.current.tags("desktop");

    async function mountDelete(executeResult, data = preview()) {
        assignDialogTestEnv();
        const calls = [];
        mockService("orm", {
            call: async (model, method, args) => {
                calls.push({ method, args });
                if (method === "tp_permanent_delete_preview") {
                    return data;
                }
                if (typeof executeResult === "function") {
                    return executeResult(args);
                }
                return executeResult;
            },
        });
        mockService("action", { doAction: async (action) => expect.step(`action:${action}`) });
        await mountWithCleanup(EmployeeDelete, {
            props: { employeeIds: [7], close: () => expect.step("close") },
        });
        return calls;
    }

    test("shows identity, sections, warning, hidden password and focuses the reason", async () => {
        await mountDelete({ ok: true, count: 1 });
        expect(".o_tp_hr_delete_warning").toHaveText(DELETE_WARNING);
        expect(".o_tp_hr_delete_table tbody tr").toHaveCount(1);
        expect(".o_tp_hr_delete_table tbody").toHaveText(/Nhân viên giả.*TP-SYN-01.*Phòng giả.*synthetic\.employee/);
        expect(".o_tp_hr_delete_remove").toHaveText(/Sẽ xóa/);
        expect(".o_tp_hr_delete_keep").toHaveText(/Giữ lại/);
        expect(".o_tp_hr_delete_block").toHaveCount(0);
        expect("#tp_hr_delete_lock").not.toBeChecked();
        expect("#tp_hr_delete_password").toHaveAttribute("type", "password");
        expect("#tp_hr_delete_password").toHaveAttribute("autocomplete", "current-password");
        expect(".o_dialog #tp_hr_delete_reason").toBeFocused();
        expect(".o_tp_hr_delete_confirm").toHaveText("Xác nhận xóa vĩnh viễn");
        expect(".o_tp_hr_delete_confirm").toHaveClass("btn-danger");
        await contains(".o_tp_hr_delete_toggle").click();
        expect("#tp_hr_delete_password").toHaveAttribute("type", "text");
    });

    test("missing reason or password never calls the delete", async () => {
        const calls = await mountDelete({ ok: true, count: 1 });
        await contains(".o_tp_hr_delete_confirm").click();
        expect(".o_tp_hr_delete_error").toHaveText("Vui lòng nhập lý do xóa vĩnh viễn.");
        expect("#tp_hr_delete_reason").toBeFocused();
        await contains("#tp_hr_delete_reason").edit("Hồ sơ giả nhập trùng");
        await contains(".o_tp_hr_delete_confirm").click();
        expect(".o_tp_hr_delete_error").toHaveText("Vui lòng nhập mật khẩu của bạn để xác nhận.");
        expect("#tp_hr_delete_password").toBeFocused();
        expect(calls.map((call) => call.method)).toEqual(["tp_permanent_delete_preview"]);
        expect.verifySteps([]);
    });

    test("wrong password keeps the dialog, clears and refocuses the password", async () => {
        const calls = await mountDelete({ ok: false, field: "password", message: "Mật khẩu chưa đúng. Chưa có hồ sơ nào bị xóa." });
        await contains("#tp_hr_delete_reason").edit("Hồ sơ giả nhập trùng");
        // confirm:false — no Enter here, the red button is the submitter in this test.
        await contains("#tp_hr_delete_password").edit("Synthetic-wrong-010", { confirm: false });
        await contains(".o_tp_hr_delete_confirm").click();
        await animationFrame();
        expect(".o_tp_hr_delete_error").toHaveText(/Mật khẩu chưa đúng/);
        expect("#tp_hr_delete_password").toHaveValue("");
        expect("#tp_hr_delete_password").toBeFocused();
        expect(".o_dialog").toHaveCount(1);
        const execute = calls.find((call) => call.method === "tp_permanent_delete_execute");
        expect(execute.args.slice(0, 5)).toEqual([[7], "Synthetic-wrong-010", "Hồ sơ giả nhập trùng", false, "synthetic-digest"]);
        expect(execute.args[5]).toMatch(/^[0-9a-f-]{36}$/);
        expect.verifySteps([]);
    });

    test("blockers disable the red button until the option or preview changes", async () => {
        await mountDelete({ ok: true, count: 1 }, preview({ keepBlock: ["Tài khoản còn trưởng phòng/ban — chọn khóa tài khoản."] }));
        expect(".o_tp_hr_delete_block").toHaveText(/Đang chặn/);
        expect(".o_tp_hr_delete_confirm").not.toBeEnabled();
        await contains("#tp_hr_delete_lock").check();
        expect(".o_tp_hr_delete_block").toHaveCount(0);
        expect(".o_tp_hr_delete_confirm").toBeEnabled();
    });

    test("cancel closes without any delete request", async () => {
        const calls = await mountDelete({ ok: true, count: 1 });
        await contains("#tp_hr_delete_reason").edit("Hồ sơ giả nhập trùng");
        await contains("#tp_hr_delete_password").edit("Synthetic-only-010", { confirm: false });
        await contains(".modal-footer .btn-outline-secondary").click();
        expect.verifySteps(["close"]);
        expect(calls.map((call) => call.method)).toEqual(["tp_permanent_delete_preview"]);
    });

    test("success (Enter in the password field) sends one request, closes and reloads", async () => {
        const calls = await mountDelete({ ok: true, count: 1, locked: 1, requestId: "x" });
        await contains("#tp_hr_delete_lock").check();
        await contains("#tp_hr_delete_reason").edit("Hồ sơ giả nhập trùng");
        await contains("#tp_hr_delete_password").edit("Synthetic-only-010", { confirm: "enter" });
        await animationFrame();
        expect.verifySteps(["close", "action:soft_reload"]);
        const executes = calls.filter((call) => call.method === "tp_permanent_delete_execute");
        expect(executes).toHaveLength(1);
        expect(executes[0].args[3]).toBe(true);
    });
});
