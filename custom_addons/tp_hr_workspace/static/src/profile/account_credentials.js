import { Component, proxy, signal, useProps, onWillDestroy } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useDialogOpener } from "@tp_web_login/js/identitycheck";

class HrAccountController extends FormController {
    setup() {
        super.setup();
        this.rememberCredentialOpener = useDialogOpener(this.rootRef);
    }
    async beforeExecuteActionButton(params) {
        const result = await super.beforeExecuteActionButton(params);
        if (result !== false && ["action_prepare_credentials", "action_reset_password"].includes(params.name)) {
            this.rememberCredentialOpener(params.name);
        }
        return result;
    }
}

registry.category("views").add("tp_hr_account", { ...formView, Controller: HrAccountController });

export function credentialError({login, password, confirmation}, minLength, reset) {
    if (!reset && (!login.trim() || /\s/.test(login.trim()) || login.trim().length > 254)) return "Nhập tên đăng nhập không chứa khoảng trắng, tối đa 254 ký tự.";
    if (!password.trim()) return "Vui lòng nhập mật khẩu mới.";
    if (password !== password.trim()) return "Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng.";
    if (password.length < minLength) return `Mật khẩu cần có ít nhất ${minLength} ký tự.`;
    if (password !== confirmation) return "Hai mật khẩu chưa giống nhau. Vui lòng nhập lại.";
    return "";
}

export class AccountCredentials extends Component {
    static template = "tp_hr_workspace.AccountCredentials";
    static components = { Dialog };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.loginInput = signal.ref();
        this.passwordInput = signal.ref();
        useAutofocus({ ref: this.props.reset ? this.passwordInput : this.loginInput });
        this.state = proxy({login: this.props.login, password: "", confirmation: "", visible: false, busy: false, error: ""});
        onWillDestroy(() => { this.state.password = ""; this.state.confirmation = ""; });
    }
    async submit(ev) {
        ev?.preventDefault();
        if (this.state.busy) return;
        this.state.error = credentialError(this.state, this.props.minLength, this.props.reset);
        if (this.state.error) return;
        this.state.busy = true;
        try {
            const args = this.props.reset ? [this.state.password, this.state.confirmation] : [this.state.login.trim(), this.state.password, this.state.confirmation];
            await this.orm.call("tp.hr.account.wizard", this.props.reset ? "action_set_password" : "action_create_user", [[this.props.wizardId], ...args]);
            this.state.password = ""; this.state.confirmation = "";
            this.props.close();
            this.notification.add(this.props.reset ? "Đã đặt lại mật khẩu thành công." : "Đã tạo tài khoản riêng cho nhân viên.", {type: "success"});
            await this.action.doAction("soft_reload");
        } catch (error) {
            const expected = ["odoo.exceptions.UserError", "odoo.exceptions.ValidationError", "odoo.exceptions.AccessError"];
            this.state.error = expected.includes(error.data?.name) ? error.data.message : "Chưa thể lưu tài khoản. Vui lòng kiểm tra kết nối rồi thử lại. Nếu đã tạo thành công, hãy tải lại hồ sơ trước khi thao tác tiếp.";
        } finally { this.state.busy = false; }
    }
}

registry.category("actions").add("tp_hr_workspace.credentials", async function (env, action) {
    await env.services.action.doAction({ type: "ir.actions.act_window_close" });
    env.services.dialog.add(AccountCredentials, action.params);
});
