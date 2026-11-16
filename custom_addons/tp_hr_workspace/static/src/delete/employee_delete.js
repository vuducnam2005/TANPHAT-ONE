import { Component, proxy, signal, useProps, onWillStart, onWillDestroy } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { useAutofocus, useService } from "@web/core/utils/hooks";

/** HR-DELETE-010: one confirmation, the admin's own password, all or nothing. */
export const DELETE_WARNING = "Hồ sơ sẽ bị xóa vĩnh viễn khỏi hệ thống. Thao tác này không thể hoàn tác bằng chức năng Bỏ lưu trữ.";
const EXPECTED = ["odoo.exceptions.UserError", "odoo.exceptions.ValidationError", "odoo.exceptions.AccessError"];

/** UUID v4 for the idempotent request id (the server only accepts this format). */
export function requestId() {
    if (globalThis.crypto?.randomUUID) {
        return globalThis.crypto.randomUUID();
    }
    const bytes = new Uint8Array(16);
    globalThis.crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Reasons that stop the deletion for the chosen account option (shown before submit). */
export function deleteBlockers(preview, lockAccounts) {
    const result = [];
    for (const employee of preview?.employees || []) {
        const reasons = [
            ...employee.block.map((item) => (item.value !== "" ? `${item.label} (${item.value})` : item.label) + (item.hint ? `: ${item.hint}` : "")),
            ...(lockAccounts ? employee.lockBlock : employee.keepBlock),
        ];
        if (reasons.length) {
            result.push({ id: employee.id, name: employee.name, code: employee.code, reasons });
        }
    }
    return result;
}

/** Client-side check before calling the server; the server checks again. */
export function deleteInputError({ reason, password }) {
    if (!reason.trim()) {
        return { field: "reason", message: "Vui lòng nhập lý do xóa vĩnh viễn." };
    }
    if (!password) {
        return { field: "password", message: "Vui lòng nhập mật khẩu của bạn để xác nhận." };
    }
    return null;
}

export class EmployeeDelete extends Component {
    static template = "tp_hr_workspace.EmployeeDelete";
    static components = { Dialog };
    props = useProps();
    warning = DELETE_WARNING;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.reasonInput = signal.ref();
        this.passwordInput = signal.ref();
        useAutofocus({ ref: this.reasonInput });
        this.requestId = requestId();
        this.state = proxy({
            loading: true, loadError: "", preview: null, reason: "", password: "", visible: false,
            lockAccounts: false, busy: false, error: "", errorField: "", stale: false,
        });
        onWillStart(() => this.load());
        onWillDestroy(() => this.clearPassword());
    }

    get employeeIds() {
        return this.props.employeeIds || [];
    }
    get blockers() {
        return deleteBlockers(this.state.preview, this.state.lockAccounts);
    }
    get canSubmit() {
        return !this.state.loading && !this.state.busy && this.state.preview && !this.blockers.length;
    }
    section(key) {
        const rows = [];
        for (const employee of this.state.preview?.employees || []) {
            for (const item of employee[key]) {
                rows.push({ employee: employee.name, label: item.label, value: item.value, hint: item.hint || "" });
            }
        }
        return rows;
    }

    clearPassword() {
        this.state.password = "";
        this.state.visible = false;
        const input = this.passwordInput();
        if (input) {
            input.value = "";
        }
    }
    focus(field) {
        const input = field === "reason" ? this.reasonInput() : this.passwordInput();
        input?.focus();
    }

    async load() {
        this.state.loading = true;
        this.state.loadError = "";
        try {
            this.state.preview = await this.orm.call("hr.employee", "tp_permanent_delete_preview", [this.employeeIds]);
            this.state.stale = false;
        } catch (error) {
            this.state.preview = null;
            this.state.loadError = EXPECTED.includes(error.data?.name) ? error.data.message : "Chưa tải được thông tin hồ sơ. Vui lòng kiểm tra kết nối rồi thử lại.";
        } finally {
            this.state.loading = false;
        }
    }
    async reloadPreview() {
        this.state.error = "";
        this.state.errorField = "";
        await this.load();
    }

    async submit(ev) {
        ev?.preventDefault();
        if (!this.canSubmit) {
            return;
        }
        const invalid = deleteInputError(this.state);
        if (invalid) {
            this.state.error = invalid.message;
            this.state.errorField = invalid.field;
            this.focus(invalid.field);
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        this.state.errorField = "";
        const password = this.state.password;
        this.clearPassword();
        let result;
        try {
            result = await this.orm.call("hr.employee", "tp_permanent_delete_execute", [
                this.employeeIds, password, this.state.reason, this.state.lockAccounts, this.state.preview.digest, this.requestId,
            ]);
        } catch (error) {
            this.state.busy = false;
            if (EXPECTED.includes(error.data?.name)) {
                this.state.error = error.data.message;
                this.state.stale = error.data.name === "odoo.exceptions.UserError";
            } else {
                this.state.error = "Chưa nhận được kết quả từ máy chủ. Hãy nhập lại mật khẩu và bấm xác nhận lần nữa; hệ thống không xóa lặp lại một yêu cầu đã hoàn tất.";
            }
            this.state.errorField = "password";
            this.focus("password");
            return;
        }
        this.state.busy = false;
        if (!result?.ok) {
            this.state.error = result?.message || "Chưa xác minh được mật khẩu. Chưa có hồ sơ nào bị xóa.";
            this.state.errorField = result?.field || "password";
            this.focus(this.state.errorField);
            return;
        }
        this.props.close();
        const parts = [`Đã xóa vĩnh viễn ${result.count} hồ sơ nhân viên.`];
        if (result.locked) {
            parts.push(`Đã khóa ${result.locked} tài khoản.`);
        }
        this.notification.add(parts.join(" "), { type: "success" });
        const controller = this.action.currentController;
        if (controller?.props?.type === "form") {
            await this.action.doAction("tp_hr_workspace.action_employees", { clearBreadcrumbs: true });
        } else {
            await this.action.doAction("soft_reload");
        }
    }
}

registry.category("actions").add("tp_hr_workspace.employee_delete", async function (env, action) {
    env.services.dialog.add(EmployeeDelete, { employeeIds: action.params?.employeeIds || [] });
});
