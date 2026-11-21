import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";

function initialsOf(name) {
    const parts = String(name || "").trim().split(/[\s·/,-]+/).filter(Boolean);
    if (!parts.length) {
        return "?";
    }
    if (parts.length === 1) {
        return parts[0].slice(0, 1).toUpperCase();
    }
    return (parts[0].slice(0, 1) + parts[parts.length - 1].slice(0, 1)).toUpperCase();
}

export class AccountSecurity extends Component {
    static template = "tp_web_login.AccountSecurity";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.state = proxy({
            data: null,
            error: "",
            notice: "",
            busy: false,
            status: "all",
            limit: 10,
            offset: 0,
            lang: "",
            tz: "",
            saved: false,
            avatarVersion: 0,
            avatarFailed: false,
            pwOpen: false,
            pwBusy: false,
            pwSuccess: "",
            pwServerError: "",
            pwCurrent: "",
            pwNew: "",
            pwConfirm: "",
            pwShowCurrent: false,
            pwShowNew: false,
            pwShowConfirm: false,
            pwErrors: { current: "", next: "", confirm: "" },
        });
        onWillStart(() => this.load());
    }

    get initials() {
        return initialsOf(this.state.data?.name || this.state.data?.login);
    }

    get totalPages() {
        const count = this.state.data?.session_count || 0;
        return Math.max(1, Math.ceil(count / this.state.limit));
    }

    get currentPage() {
        return Math.floor(this.state.offset / this.state.limit) + 1;
    }

    roleChipClass(roleCode) {
        if (roleCode === "original_admin") {
            return "tp-security-chip is-role-original";
        }
        if (roleCode === "granted_admin" || roleCode === "system_admin") {
            return "tp-security-chip is-role-admin";
        }
        if (roleCode === "hr_manager") {
            return "tp-security-chip is-role-hr";
        }
        return "tp-security-chip is-role-employee";
    }

    sessionChipClass(row) {
        if (row.state === "current") {
            return "tp-security-chip is-enabled";
        }
        if (row.state === "ended_uncleaned") {
            return "tp-security-chip is-warning";
        }
        return "tp-security-chip";
    }

    date(value) {
        return value ? formatDateTime(deserializeDateTime(value)) : "Không giới hạn";
    }

    dateOrDash(value) {
        return value ? formatDateTime(deserializeDateTime(value)) : "Chưa có dữ liệu";
    }

    onAvatarError() {
        this.state.avatarFailed = true;
    }

    async load() {
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("res.users", "tp_my_security", [], {
                status: this.state.status,
                limit: this.state.limit,
                offset: this.state.offset,
            });
            this.state.lang = this.state.data.lang;
            this.state.tz = this.state.data.tz;
        } catch (error) {
            this.state.error = error.data?.message || "Không tải được thông tin bảo mật. Vui lòng thử lại.";
        }
    }

    togglePasswordForm() {
        this.state.pwOpen = !this.state.pwOpen;
        this.state.pwServerError = "";
        this.state.pwErrors = { current: "", next: "", confirm: "" };
        if (!this.state.pwOpen) {
            this.resetPasswordInputs();
        } else {
            this.state.pwSuccess = "";
        }
    }

    resetPasswordInputs() {
        this.state.pwCurrent = "";
        this.state.pwNew = "";
        this.state.pwConfirm = "";
        this.state.pwShowCurrent = false;
        this.state.pwShowNew = false;
        this.state.pwShowConfirm = false;
        this.state.pwErrors = { current: "", next: "", confirm: "" };
        this.state.pwServerError = "";
    }

    onPasswordInput(field, event) {
        const value = event.target.value;
        if (field === "current") {
            this.state.pwCurrent = value;
            if (this.state.pwErrors.current) {
                this.state.pwErrors.current = "";
            }
        } else if (field === "next") {
            this.state.pwNew = value;
            if (this.state.pwErrors.next) {
                this.state.pwErrors.next = "";
            }
            if (this.state.pwConfirm && this.state.pwErrors.confirm) {
                this.state.pwErrors.confirm = value === this.state.pwConfirm ? "" : "Xác nhận mật khẩu mới chưa khớp.";
            }
        } else if (field === "confirm") {
            this.state.pwConfirm = value;
            if (this.state.pwErrors.confirm) {
                this.state.pwErrors.confirm = "";
            }
        }
        this.state.pwServerError = "";
    }

    togglePasswordVisibility(field) {
        if (field === "current") {
            this.state.pwShowCurrent = !this.state.pwShowCurrent;
        } else if (field === "next") {
            this.state.pwShowNew = !this.state.pwShowNew;
        } else if (field === "confirm") {
            this.state.pwShowConfirm = !this.state.pwShowConfirm;
        }
    }

    validatePasswordForm() {
        const errors = { current: "", next: "", confirm: "" };
        if (!this.state.pwCurrent) {
            errors.current = "Vui lòng nhập mật khẩu hiện tại.";
        }
        if (!this.state.pwNew || !this.state.pwNew.trim()) {
            errors.next = "Vui lòng nhập mật khẩu mới.";
        }
        if (!this.state.pwConfirm) {
            errors.confirm = "Vui lòng nhập lại mật khẩu mới để xác nhận.";
        } else if (this.state.pwNew !== this.state.pwConfirm) {
            errors.confirm = "Xác nhận mật khẩu mới chưa khớp.";
        }
        this.state.pwErrors = errors;
        return !errors.current && !errors.next && !errors.confirm;
    }

    async submitPasswordChange(event) {
        event.preventDefault();
        if (this.state.pwBusy) {
            return;
        }
        this.state.pwSuccess = "";
        this.state.pwServerError = "";
        if (!this.validatePasswordForm()) {
            return;
        }
        this.state.pwBusy = true;
        try {
            await this.orm.call("res.users", "tp_change_my_password", [
                this.state.pwCurrent,
                this.state.pwNew,
                this.state.pwConfirm,
            ]);
            this.resetPasswordInputs();
            this.state.pwOpen = false;
            this.state.pwSuccess = "Đã đổi mật khẩu thành công. Phiên hiện tại vẫn được giữ; các thiết bị tin cậy cũ đã được hủy.";
            await this.load();
        } catch (error) {
            const msg = error.data?.message || "Chưa đổi được mật khẩu. Vui lòng kiểm tra lại và thử lại.";
            if (msg.includes("Mật khẩu hiện tại")) {
                this.state.pwErrors = { ...this.state.pwErrors, current: msg };
            } else if (msg.includes("Xác nhận mật khẩu")) {
                this.state.pwErrors = { ...this.state.pwErrors, confirm: msg };
            } else if (msg.includes("mật khẩu mới")) {
                this.state.pwErrors = { ...this.state.pwErrors, next: msg };
            } else {
                this.state.pwServerError = msg;
            }
        } finally {
            this.state.pwBusy = false;
        }
    }

    async filter(event) {
        this.state[event.target.name] = event.target.name === "limit" ? Number(event.target.value) : event.target.value;
        this.state.offset = 0;
        await this.load();
    }

    preference(event) {
        this.state[event.target.name] = event.target.value;
    }

    async page(direction) {
        this.state.offset = Math.max(0, this.state.offset + direction * this.state.limit);
        await this.load();
    }

    async run(operation, recordId = null, successMessage = "") {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        this.state.notice = "";
        try {
            const result = await this.orm.call("res.users", "tp_security_action", [operation, recordId]);
            if (result && typeof result === "object" && result.type) {
                await this.action.doAction(result, { onClose: () => this.load() });
            } else if (successMessage) {
                this.state.notice = successMessage;
            }
            await this.load();
        } catch (error) {
            this.state.error = error.data?.message || "Thao tác chưa hoàn tất. Vui lòng thử lại.";
        } finally {
            this.state.busy = false;
        }
    }

    confirm(operation, recordId, body, successMessage = "") {
        this.dialog.add(ConfirmationDialog, {
            title: "Xác nhận thay đổi bảo mật",
            body,
            confirmLabel: "Tiếp tục",
            cancelLabel: "Hủy",
            confirm: () => this.run(operation, recordId, successMessage),
        });
    }

    async savePreferences(values = null) {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.saved = false;
        this.state.error = "";
        try {
            await this.orm.call("res.users", "tp_save_my_preferences", [values || { lang: this.state.lang, tz: this.state.tz }]);
            this.state.saved = true;
            this.state.avatarFailed = false;
            this.state.avatarVersion++;
        } catch (error) {
            this.state.error = error.data?.message || "Chưa lưu được tùy chọn cá nhân.";
        } finally {
            this.state.busy = false;
        }
    }

    async avatar(event) {
        const file = event.target.files?.[0];
        if (!file) {
            return;
        }
        if (!file.type.startsWith("image/") || file.size > 5 * 1024 * 1024) {
            this.state.error = "Vui lòng chọn ảnh tối đa 5 MB.";
            return;
        }
        const reader = new FileReader();
        reader.onload = () => this.savePreferences({ image_1920: String(reader.result).split(",")[1] });
        reader.onerror = () => {
            this.state.error = "Không đọc được ảnh. Vui lòng chọn lại.";
        };
        reader.readAsDataURL(file);
        event.target.value = "";
    }

    back() {
        const previous = this.env.config?.breadcrumbs?.at(-2);
        return previous ? this.action.restore(previous.jsId) : this.action.doAction("tp_web_home.action_home");
    }
}

registry.category("actions").add("tp_web_login.account_security", AccountSecurity);
