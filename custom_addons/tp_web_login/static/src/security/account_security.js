import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";

export class AccountSecurity extends Component {
    static template = "tp_web_login.AccountSecurity";
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.state = proxy({ data: null, error: "", busy: false, status: "all", limit: 10, offset: 0, lang: "", tz: "", saved: false, avatarVersion: 0 });
        onWillStart(() => this.load());
    }
    date(value) { return value ? formatDateTime(deserializeDateTime(value)) : "Không giới hạn"; }
    async load() {
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("res.users", "tp_my_security", [], {
                status: this.state.status, limit: this.state.limit, offset: this.state.offset,
            });
            this.state.lang = this.state.data.lang;
            this.state.tz = this.state.data.tz;
        } catch (error) {
            this.state.error = error.data?.message || "Không tải được thông tin bảo mật. Vui lòng thử lại.";
        }
    }
    async filter(event) {
        this.state[event.target.name] = event.target.name === "limit" ? Number(event.target.value) : event.target.value;
        this.state.offset = 0;
        await this.load();
    }
    preference(event) { this.state[event.target.name] = event.target.value; }
    async page(direction) {
        this.state.offset = Math.max(0, this.state.offset + direction * this.state.limit);
        await this.load();
    }
    async run(operation, recordId = null) {
        if (this.state.busy) return;
        this.state.busy = true;
        this.state.error = "";
        try {
            const result = await this.orm.call("res.users", "tp_security_action", [operation, recordId]);
            if (result && typeof result === "object" && result.type) {
                await this.action.doAction(result, { onClose: () => this.load() });
            }
            await this.load();
        } catch (error) {
            this.state.error = error.data?.message || "Thao tác chưa hoàn tất. Vui lòng thử lại.";
        } finally {
            this.state.busy = false;
        }
    }
    confirm(operation, recordId, body) {
        this.dialog.add(ConfirmationDialog, {
            title: "Xác nhận thay đổi bảo mật", body,
            confirmLabel: "Tiếp tục", cancelLabel: "Hủy",
            confirm: () => this.run(operation, recordId),
        });
    }
    async savePreferences(values = null) {
        if (this.state.busy) return;
        this.state.busy = true;
        this.state.saved = false;
        this.state.error = "";
        try {
            await this.orm.call("res.users", "tp_save_my_preferences", [values || { lang: this.state.lang, tz: this.state.tz }]);
            this.state.saved = true;
            this.state.avatarVersion++;
        } catch (error) {
            this.state.error = error.data?.message || "Chưa lưu được tùy chọn cá nhân.";
        } finally { this.state.busy = false; }
    }
    async avatar(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith("image/") || file.size > 5 * 1024 * 1024) {
            this.state.error = "Vui lòng chọn ảnh tối đa 5 MB."; return;
        }
        const reader = new FileReader();
        reader.onload = () => this.savePreferences({ image_1920: String(reader.result).split(",")[1] });
        reader.onerror = () => { this.state.error = "Không đọc được ảnh. Vui lòng chọn lại."; };
        reader.readAsDataURL(file);
        event.target.value = "";
    }
    back() {
        const previous = this.env.config?.breadcrumbs?.at(-2);
        return previous ? this.action.restore(previous.jsId) : this.action.doAction("tp_web_home.action_home");
    }
}
registry.category("actions").add("tp_web_login.account_security", AccountSecurity);
