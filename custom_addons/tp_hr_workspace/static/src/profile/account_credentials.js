import { Component, proxy, signal, useProps, onWillDestroy } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useDialogOpener } from "@tp_web_login/js/identitycheck";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

class HrAccountController extends FormController {
    setup() {
        super.setup();
        this.rememberCredentialOpener = useDialogOpener(this.rootRef);
    }
    async beforeExecuteActionButton(params) {
        const result = await super.beforeExecuteActionButton(params);
        if (result !== false && ["action_prepare_credentials", "action_reset_password", "action_open_change_login"].includes(params.name)) {
            this.rememberCredentialOpener(params.name);
        }
        return result;
    }
}

registry.category("views").add("tp_hr_account", { ...formView, Controller: HrAccountController });

export function loginError(login, currentLogin) {
    if (!login.trim()) return "Vui lòng nhập tên đăng nhập.";
    if (/\s/.test(login.trim()) || Array.from(login.trim()).length > 254) return "Nhập tên đăng nhập không chứa khoảng trắng, tối đa 254 ký tự.";
    if (/\p{C}/u.test(login.trim())) return "Tên đăng nhập không được chứa ký tự điều khiển hoặc ký tự ẩn.";
    if (login.trim() === currentLogin) return "Tên đăng nhập mới phải khác tên đăng nhập hiện tại.";
    return "";
}

export function credentialError({login, password, confirmation}, minLength, reset) {
    if (!reset && loginError(login)) return loginError(login);
    if (!password.trim()) return "Vui lòng nhập mật khẩu mới.";
    if (password !== password.trim()) return "Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng.";
    if (password.length < minLength) return `Mật khẩu cần có ít nhất ${minLength} ký tự.`;
    if (password !== confirmation) return "Hai mật khẩu chưa giống nhau. Vui lòng nhập lại.";
    return "";
}

export function credentialErrors(values, minLength, reset) {
    const errors = [];
    const add = (id, label, message) => { if (message) errors.push({id, label, message, location: "Thông tin tài khoản"}); };
    if (!reset) add("tp_account_login", "Tên đăng nhập", loginError(values.login));
    add("tp_account_password", "Mật khẩu mới", credentialError({...values, confirmation: values.password}, minLength, true));
    add("tp_account_confirmation", "Nhập lại mật khẩu", !values.confirmation ? "Vui lòng nhập lại mật khẩu mới."
        : values.password !== values.confirmation ? "Hai mật khẩu chưa giống nhau. Vui lòng nhập lại." : "");
    return errors;
}

export class AccountCredentials extends Component {
    static template = "tp_hr_workspace.AccountCredentials";
    static components = { Dialog, InlineErrors };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.loginInput = signal.ref();
        this.passwordInput = signal.ref();
        useAutofocus({ ref: this.props.reset ? this.passwordInput : this.loginInput });
        this.state = proxy({login: this.props.login, password: "", confirmation: "", visible: false, busy: false, attempted: false, attempt: 0, server: null});
        onWillDestroy(() => { this.state.password = ""; this.state.confirmation = ""; });
    }
    get errors() { return this.state.attempted ? credentialErrors(this.state, this.props.minLength, this.props.reset) : []; }
    fieldError(id) { return this.errors.find(e => e.id === id)?.message || ""; }
    async submit(ev) {
        ev?.preventDefault();
        if (this.state.busy) return;
        this.state.attempted = true; this.state.server = null;
        if (this.errors.length) { this.state.attempt++; return; }
        this.state.busy = true;
        try {
            const args = this.props.reset ? [this.state.password, this.state.confirmation] : [this.state.login.trim(), this.state.password, this.state.confirmation];
            await this.orm.call("tp.hr.account.wizard", this.props.reset ? "action_set_password" : "action_create_user", [[this.props.wizardId], ...args]);
            this.state.password = ""; this.state.confirmation = "";
            this.props.close();
            this.notification.add(this.props.reset ? "Đã đặt lại mật khẩu thành công." : "Đã tạo tài khoản riêng cho nhân viên.", {type: "success"});
            await this.action.doAction("soft_reload");
        } catch (error) {
            this.state.server = saveError(error);
            this.state.attempt++;
        } finally { this.state.busy = false; }
    }
}

registry.category("actions").add("tp_hr_workspace.credentials", async function (env, action) {
    await env.services.action.doAction({ type: "ir.actions.act_window_close" });
    env.services.dialog.add(AccountCredentials, action.params);
});

export class ChangeLogin extends Component {
    static template = "tp_hr_workspace.ChangeLogin";
    static components = { Dialog, InlineErrors };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.loginInput = signal.ref();
        useAutofocus({ ref: this.loginInput });
        this.state = proxy({ login: "", busy: false, attempted: false, attempt: 0, server: null });
    }
    get errors() {
        const message = this.state.attempted && loginError(this.state.login, this.props.currentLogin);
        return message ? [{id: "tp_login_new", label: "Tên đăng nhập mới", message, location: "Đổi tên đăng nhập"}] : [];
    }
    async submit(ev) {
        ev?.preventDefault();
        if (this.state.busy) return;
        this.state.attempted = true; this.state.server = null;
        if (this.errors.length) { this.state.attempt++; return; }
        this.state.busy = true;
        try {
            await this.orm.call("tp.hr.account.wizard", "action_change_login", [[this.props.wizardId], this.state.login.trim()]);
            this.props.close();
            this.notification.add("Đã đổi tên đăng nhập. Nhân viên cần đăng nhập lại bằng tên mới; mật khẩu giữ nguyên.", { type: "success" });
            await this.action.doAction("soft_reload");
        } catch (error) {
            this.state.server = saveError(error);
            this.state.attempt++;
        } finally { this.state.busy = false; }
    }
}

registry.category("actions").add("tp_hr_workspace.change_login", async function (env, action) {
    await env.services.action.doAction({ type: "ir.actions.act_window_close" });
    env.services.dialog.add(ChangeLogin, action.params);
});
