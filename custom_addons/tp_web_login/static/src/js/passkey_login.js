import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { UserSwitch } from "@web/core/user_switch/user_switch";
import { PasskeyLogin } from "@auth_passkey/interactions/passkey_login";
import * as passkeyLib from "@auth_passkey/../lib/simplewebauthn";
import { PasskeyUnsupportedError, describePasskeyError, reportPasskeyFailure } from "./passkey_errors";

// The page navigates on success; if it does not (stalled POST), allow a retry.
const SUBMIT_RETRY_DELAY = 20000;

/**
 * Native flow kept as is (start-auth -> browser assertion -> native POST of the
 * login form). This patch only adds visible state and errors instead of
 * swallowing them in the console.
 */
patch(PasskeyLogin.prototype, {
    setup() {
        super.setup(...arguments);
        this.tpBusy = false;
        this.tpLabel = this.el.querySelector("span");
        this.tpLabelText = this.tpLabel?.textContent || "";
        this.dynamicContent._window = { "t-on-pageshow": () => this.tpReset() };
    },

    get tpFeedback() {
        return this.el.closest(".o_login_auth")?.querySelector(".tp-passkey-feedback");
    },

    tpSetBusy(busy, label = "") {
        this.tpBusy = busy;
        this.el.classList.toggle("tp-is-busy", busy);
        if (busy) {
            this.el.setAttribute("aria-busy", "true");
            this.el.setAttribute("aria-disabled", "true");
        } else {
            this.el.removeAttribute("aria-busy");
            this.el.removeAttribute("aria-disabled");
        }
        if (this.tpLabel) {
            this.tpLabel.textContent = busy && label ? label : this.tpLabelText;
        }
    },

    tpShowFeedback(message, tone) {
        const box = this.tpFeedback;
        if (!box) {
            return;
        }
        box.textContent = message;
        // classList, not a nested template literal: the production minifier drops its leading space.
        box.classList.remove("alert", "alert-danger", "alert-info", "alert-warning");
        if (message) {
            box.classList.add("alert", "alert-" + tone);
        }
        box.setAttribute("role", tone === "danger" ? "alert" : "status");
    },

    tpReset() {
        clearTimeout(this.tpRetryTimer);
        const form = document.querySelector("form.oe_login_form");
        const type = form?.querySelector("input[name='type']");
        if (type?.value === "webauthn") {
            // A back/forward restore must not turn the next password submit into a passkey one.
            type.value = "password";
            form.querySelector("input[name='webauthn_response']").value = "";
        }
        this.tpSetBusy(false);
    },

    async onClick(ev) {
        ev?.preventDefault();
        if (this.tpBusy) {
            return false;
        }
        this.tpSetBusy(true, "Đang chờ xác thực trên thiết bị…");
        this.tpShowFeedback("", "info");
        let auth;
        try {
            if (!passkeyLib.browserSupportsWebAuthn()) {
                throw new PasskeyUnsupportedError();
            }
            const serverOptions = await this.waitFor(rpc("/auth/passkey/start-auth"));
            auth = await this.waitFor(passkeyLib.startAuthentication(serverOptions));
        } catch (error) {
            const { kind, message } = describePasskeyError(error, "login");
            reportPasskeyFailure("login", kind, error);
            this.tpReset();
            this.tpShowFeedback(message, "danger");
            return false;
        }
        const form = document.querySelector("form.oe_login_form");
        form.querySelector("input[name='webauthn_response']").value = JSON.stringify(auth);
        form.querySelector("input[name='type']").value = "webauthn";
        // Not "logged in" yet: the server still verifies signature, challenge, origin and RP ID.
        this.tpSetBusy(true, "Đang kiểm tra khóa truy cập…");
        this.tpShowFeedback("Thiết bị đã xác thực. Máy chủ đang kiểm tra khóa truy cập…", "info");
        this.tpRetryTimer = this.waitForTimeout(() => {
            this.tpReset();
            this.tpShowFeedback("Máy chủ phản hồi chậm. Hãy kiểm tra mạng và thử lại.", "warning");
        }, SUBMIT_RETRY_DELAY);
        form.submit();
        return false;
    },
});

// Native UserSwitch hides the whole form (and its server error) when several
// accounts are remembered. A passkey POST has no login, so keep feedback visible.
patch(UserSwitch.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.form?.querySelector(":scope > .alert-danger, :scope > .alert-success")) {
            this.state.displayUserChoice = false;
            this.form.classList.remove("d-none");
        }
    },
});
