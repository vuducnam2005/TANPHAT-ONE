import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ShowPassword } from "@web/public/show_password";

// Keep the native visibility handler and expose its state to assistive technology.
patch(ShowPassword.prototype, {
    setup() {
        super.setup();
        if (this.el.closest(".tp-native-login")) {
            Object.assign(this.dynamicContent[".o_show_password"], {
                "t-att-aria-pressed": () => String(Boolean(this.showPassword)),
                "t-att-aria-label": () => (this.showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"),
                "t-att-title": () => (this.showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"),
            });
        }
    },
});

// Native login owns captcha/spinner; preserve POST and allow retry after a stalled request.
export class AuthSubmit extends Interaction {
    static selector = ".tp-native-login form";
    dynamicContent = {
        _root: { "t-on-submit": this.onSubmit },
        _window: { "t-on-pageshow": this.reset },
    };
    reset() {
        this.pending = false;
        this.el.removeAttribute("aria-busy");
        for (const button of this.el.querySelectorAll("button.o_btn_loading")) {
            button.disabled = false;
            button.classList.remove("o_btn_loading", "o_btn_keep_loading", "disabled", "pe-none");
            button.removeAttribute("aria-disabled");
            button.querySelector(".o_btn_loading_spinner")?.remove();
        }
    }
    onSubmit(ev) {
        if (ev.defaultPrevented) { return; }
        if (this.pending) { ev.preventDefault(); return; }
        this.pending = true;
        this.el.setAttribute("aria-busy", "true");
        const prevent = ev.preventDefault.bind(ev);
        ev.preventDefault = () => { this.reset(); prevent(); };
        this.waitForTimeout(() => this.reset(), 10000);
    }
}
registry.category("public.interactions").add("tp_web_login.submit", AuthSubmit);
