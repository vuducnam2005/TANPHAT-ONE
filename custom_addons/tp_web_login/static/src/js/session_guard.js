import { Component, onMounted, onPatched, proxy, signal } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { UncaughtPromiseError } from "@web/core/errors/error_service";
import {
    ConnectionAbortedError,
    ConnectionLostError,
    RPCError,
    rpcBus,
} from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export const SESSION_REPLACED_REASON = "session_replaced";
export const SESSION_CUTOVER_REASON = "session_cutover";

export const REPLACED_COPY = Object.freeze({
    title: "Tài khoản của bạn đang được đăng nhập ở nơi khác.",
    detail: "Phiên làm việc trên thiết bị này đã kết thúc. Vui lòng đăng nhập lại để tiếp tục.",
});

export const CUTOVER_COPY = Object.freeze({
    title: "Hệ thống vừa cập nhật phiên đăng nhập.",
    detail: "Phiên làm việc hiện tại cần được làm mới. Vui lòng đăng nhập lại để tiếp tục.",
});

const POLL_VISIBLE_MS = 4000;
const POLL_MAX_BACKOFF_MS = 30000;

/**
 * Extract explicit server session-termination cause ("session_replaced" | "session_cutover")
 * without ever misclassifying network errors, 403 AccessError, 400/422 validation, 500, or
 * normal session expiration / account lock.
 */
export function extractSessionEndReason(error) {
    if (!error) {
        return null;
    }
    if (error instanceof ConnectionLostError || error instanceof ConnectionAbortedError) {
        return null;
    }
    const isRpc = error instanceof RPCError || error?.name === "RPC_ERROR";
    if (!isRpc) {
        return null;
    }
    const ctxReason = error?.data?.context?.tp_session_reason;
    if (ctxReason === SESSION_REPLACED_REASON || ctxReason === SESSION_CUTOVER_REASON) {
        return ctxReason;
    }
    const excName = String(error?.exceptionName || error?.data?.name || "");
    if (excName.endsWith("TpSessionReplacedException")) {
        return SESSION_REPLACED_REASON;
    }
    if (excName.endsWith("TpSessionCutoverException")) {
        return SESSION_CUTOVER_REASON;
    }
    return null;
}

export function resolveReloginUrl(rawUrl) {
    if (typeof rawUrl === "string" && rawUrl.startsWith("/") && !rawUrl.startsWith("//")) {
        return rawUrl;
    }
    return "/dang-nhap?redirect=%2Fapp%2Ftrang-chu";
}

let activeGuardInstance = null;

export const tpSessionGuardService = {
    dependencies: [],
    start(env) {
        const state = proxy({
            ended: false,
            reason: null,
            hadUnsavedHint: false,
            reloggingIn: false,
        });

        const uid = user.userId || session.uid || null;
        const sessionTag = session.tp_session_tag || null;
        const isTestMode = Boolean(session.test_mode);

        let destroyed = false;
        let pollTimer = null;
        let consecutiveErrors = 0;
        let checkInFlight = null;
        let unsubscribeBus = null;
        let busRef = null;
        let broadcastChannel = null;

        const clearPollTimer = () => {
            if (pollTimer !== null) {
                browser.clearTimeout(pollTimer);
                pollTimer = null;
            }
        };

        const scrubWorkspaceDomAndCaches = () => {
            try {
                rpcBus.trigger("CLEAR-CACHES");
            } catch {
                // ignore in isolated tests
            }
            try {
                env.services?.dialog?.closeAll?.();
            } catch {
                // optional dialog service
            }
            const doc = browser.document;
            if (!doc) {
                return;
            }
            doc.documentElement?.classList.add("tp-session-ended-active");
            doc.body?.classList.add("tp-session-ended-active");
            for (const el of doc.querySelectorAll(".o_action_manager")) {
                el.replaceChildren();
                el.style.setProperty("display", "none", "important");
            }
            for (const el of doc.querySelectorAll(".o_main_navbar, .o_navbar")) {
                el.style.setProperty("display", "none", "important");
            }
        };

        const suppressBeforeUnload = (ev) => {
            if (state.ended || state.reloggingIn) {
                ev.stopImmediatePropagation();
            }
        };

        const enterEndedState = (reason, { broadcast = true } = {}) => {
            if (destroyed || state.ended) {
                return;
            }
            if (reason !== SESSION_REPLACED_REASON && reason !== SESSION_CUTOVER_REASON) {
                return;
            }
            const doc = browser.document;
            if (doc?.querySelector(".o_form_dirty, .o_field_invalid")) {
                state.hadUnsavedHint = true;
            }
            state.reason = reason;
            state.ended = true;

            clearPollTimer();
            try {
                busRef?.stop?.();
            } catch {
                // ignore worker stop errors
            }
            scrubWorkspaceDomAndCaches();

            if (broadcast && broadcastChannel && sessionTag) {
                try {
                    broadcastChannel.postMessage({
                        type: "tp_session_ended",
                        reason,
                        tag: sessionTag,
                    });
                } catch {
                    // BroadcastChannel may be closed
                }
            }
            // Dispose the entire old webclient, including service caches, pending
            // callbacks and workspace timers. A standalone document owns re-login.
            // Its public route validates the server tombstone, never a client reason.
            browser.document.documentElement.style.visibility = "hidden";
            browser.location.replace("/tp/session-ended");
        };

        const checkSessionNow = async () => {
            if (destroyed || state.ended || !uid || isTestMode) {
                return;
            }
            if (browser.navigator && browser.navigator.onLine === false) {
                return;
            }
            if (checkInFlight) {
                return checkInFlight;
            }
            checkInFlight = (async () => {
                try {
                    const response = await browser.fetch("/web/session/check", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/json",
                            "X-Odoo-Skip-Session-Rotation-Interval": "1",
                        },
                        body: JSON.stringify({
                            jsonrpc: "2.0",
                            method: "call",
                            params: {},
                            id: Date.now(),
                        }),
                    });
                    if (!response.ok) {
                        consecutiveErrors += 1;
                        return;
                    }
                    const payload = await response.json();
                    consecutiveErrors = 0;
                    if (payload?.error) {
                        const syntheticRpcErr = new RPCError();
                        syntheticRpcErr.code = payload.error.code;
                        syntheticRpcErr.message = payload.error.message;
                        syntheticRpcErr.data = payload.error.data;
                        syntheticRpcErr.exceptionName = payload.error.data?.name;
                        const reason = extractSessionEndReason(syntheticRpcErr);
                        if (reason) {
                            enterEndedState(reason, { broadcast: true });
                        }
                    }
                } catch {
                    // Network error / offline: backoff only, never falsely report session_replaced.
                    consecutiveErrors += 1;
                } finally {
                    checkInFlight = null;
                }
            })();
            return checkInFlight;
        };

        const scheduleNextPoll = () => {
            clearPollTimer();
            if (destroyed || state.ended || !uid || isTestMode) {
                return;
            }
            const doc = browser.document;
            if (doc && doc.visibilityState === "hidden") {
                return;
            }
            if (browser.navigator && browser.navigator.onLine === false) {
                return;
            }
            const factor = Math.min(8, 2 ** Math.min(consecutiveErrors, 3));
            const delay = Math.min(POLL_MAX_BACKOFF_MS, POLL_VISIBLE_MS * factor);
            pollTimer = browser.setTimeout(async () => {
                await checkSessionNow();
                scheduleNextPoll();
            }, delay);
        };

        const onRpcResponse = (ev) => {
            const reason = extractSessionEndReason(ev?.detail?.error);
            if (reason) {
                enterEndedState(reason, { broadcast: true });
            }
        };

        const onBusSessionReplaced = (payload) => {
            if (!payload || payload.reason !== SESSION_REPLACED_REASON) {
                return;
            }
            if (sessionTag && payload.replaced_tag && payload.replaced_tag !== sessionTag) {
                return;
            }
            enterEndedState(SESSION_REPLACED_REASON, { broadcast: true });
        };

        const onBusDisconnect = () => {
            if (!destroyed && !state.ended) {
                checkSessionNow();
                scheduleNextPoll();
            }
        };

        const attachBus = () => {
            if (destroyed || unsubscribeBus || !uid) {
                return Boolean(unsubscribeBus);
            }
            const bus = env.services?.bus_service;
            if (bus && typeof bus.subscribe === "function") {
                busRef = bus;
                const unsub = bus.subscribe("tp.auth/session_replaced", onBusSessionReplaced);
                unsubscribeBus = typeof unsub === "function" ? unsub : () => {};
                if (typeof bus.addEventListener === "function") {
                    bus.addEventListener("BUS:DISCONNECT", onBusDisconnect);
                }
                if (!isTestMode && typeof bus.start === "function") {
                    Promise.resolve()
                        .then(() => bus.start())
                        .catch(() => {});
                }
                return true;
            }
            return false;
        };

        const waitForBus = (remaining = 12) => {
            if (destroyed || attachBus() || remaining <= 0) {
                return;
            }
            Promise.resolve().then(() => waitForBus(remaining - 1));
        };

        const onVisibilityChange = () => {
            if (destroyed || state.ended) {
                return;
            }
            if (browser.document?.visibilityState === "visible") {
                consecutiveErrors = 0;
                checkSessionNow();
                scheduleNextPoll();
            } else {
                clearPollTimer();
            }
        };

        const onWindowFocus = () => {
            if (!destroyed && !state.ended) {
                checkSessionNow();
            }
        };

        const onWindowOnline = () => {
            if (!destroyed && !state.ended) {
                consecutiveErrors = 0;
                checkSessionNow();
                scheduleNextPoll();
            }
        };

        const onPageShow = (ev) => {
            if (state.ended) {
                scrubWorkspaceDomAndCaches();
                return;
            }
            if (ev?.persisted) {
                // A bfcache restore must pass backend authentication before any
                // private DOM becomes visible or a suspended callback resumes.
                browser.location.reload();
            }
        };

        const onPageHide = () => {
            // This style is saved in bfcache with the document. It intentionally
            // remains hidden on restore until the authenticated reload completes.
            browser.document.documentElement.style.visibility = "hidden";
        };

        if (uid) {
            rpcBus.addEventListener("RPC:RESPONSE", onRpcResponse);
            browser.addEventListener("beforeunload", suppressBeforeUnload, { capture: true });
            browser.addEventListener("focus", onWindowFocus);
            browser.addEventListener("online", onWindowOnline);
            browser.addEventListener("pageshow", onPageShow);
            browser.addEventListener("pagehide", onPageHide);
            browser.document?.addEventListener("visibilitychange", onVisibilityChange);

            if (sessionTag && typeof BroadcastChannel !== "undefined") {
                try {
                    broadcastChannel = new BroadcastChannel(
                        `tp_session_guard:${session.db || ""}:${uid}:${sessionTag}`
                    );
                    broadcastChannel.onmessage = (ev) => {
                        const msg = ev?.data;
                        if (
                            msg?.type === "tp_session_ended" &&
                            msg.tag === sessionTag &&
                            (msg.reason === SESSION_REPLACED_REASON ||
                                msg.reason === SESSION_CUTOVER_REASON)
                        ) {
                            enterEndedState(msg.reason, { broadcast: false });
                        }
                    };
                } catch {
                    broadcastChannel = null;
                }
            }

            waitForBus();
            scheduleNextPoll();
        }

        const relogin = async () => {
            if (state.reloggingIn) {
                return;
            }
            state.reloggingIn = true;
            const targetUrl = resolveReloginUrl(session.tp_relogin_url);
            try {
                browser.navigator?.serviceWorker?.controller?.postMessage?.("user_logout");
                const csrfToken = globalThis.odoo?.csrf_token || "";
                if (csrfToken && typeof browser.fetch === "function") {
                    const body = new URLSearchParams({
                        csrf_token: csrfToken,
                        redirect: targetUrl,
                    });
                    await browser.fetch("/web/session/logout", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                        },
                        body: body.toString(),
                    });
                }
            } catch {
                // Proceed to same-origin login page even if stale session cookie was already rotated.
            } finally {
                if (browser.location && typeof browser.location.replace === "function") {
                    browser.location.replace(targetUrl);
                } else if (browser.location) {
                    browser.location.href = targetUrl;
                }
            }
        };

        const api = {
            state,
            enterEndedState,
            scrubWorkspaceDomAndCaches,
            checkSessionNow,
            relogin,
            destroy() {
                destroyed = true;
                if (activeGuardInstance === api) {
                    activeGuardInstance = null;
                }
                clearPollTimer();
                rpcBus.removeEventListener("RPC:RESPONSE", onRpcResponse);
                browser.removeEventListener("beforeunload", suppressBeforeUnload, { capture: true });
                browser.removeEventListener("focus", onWindowFocus);
                browser.removeEventListener("online", onWindowOnline);
                browser.removeEventListener("pageshow", onPageShow);
                browser.removeEventListener("pagehide", onPageHide);
                browser.document?.removeEventListener("visibilitychange", onVisibilityChange);
                if (busRef && typeof busRef.removeEventListener === "function") {
                    busRef.removeEventListener("BUS:DISCONNECT", onBusDisconnect);
                }
                if (typeof unsubscribeBus === "function") {
                    unsubscribeBus();
                    unsubscribeBus = null;
                }
                if (broadcastChannel) {
                    try {
                        broadcastChannel.close();
                    } catch {
                        // ignore
                    }
                    broadcastChannel = null;
                }
            },
        };
        activeGuardInstance = api;
        return api;
    },
};

registry.category("services").add("tp_session_guard", tpSessionGuardService);

export function tpSessionReplacedErrorHandler(env, error, originalError) {
    if (!(error instanceof UncaughtPromiseError)) {
        return false;
    }
    const guard = env.services?.tp_session_guard || activeGuardInstance;
    const reason = extractSessionEndReason(originalError);
    if (reason) {
        error.unhandledRejectionEvent?.preventDefault?.();
        guard?.enterEndedState?.(reason, { broadcast: true });
        return true;
    }
    if (
        guard?.state?.ended &&
        (originalError instanceof RPCError ||
            originalError instanceof ConnectionLostError ||
            originalError instanceof ConnectionAbortedError)
    ) {
        error.unhandledRejectionEvent?.preventDefault?.();
        return true;
    }
    return false;
}

registry
    .category("error_handlers")
    .add("tpSessionReplacedErrorHandler", tpSessionReplacedErrorHandler, { sequence: 1 });

export class TpSessionEndedOverlay extends Component {
    static template = "tp_web_login.SessionEndedOverlay";

    reloginBtnRef = signal.ref();

    setup() {
        this.guard = useService("tp_session_guard");
        const focusButton = () => {
            if (this.guard.state.ended) {
                this.guard.scrubWorkspaceDomAndCaches?.();
                this.reloginBtnRef()?.focus?.();
            }
        };
        onMounted(focusButton);
        onPatched(focusButton);
    }

    get titleText() {
        return this.guard.state.reason === SESSION_CUTOVER_REASON
            ? CUTOVER_COPY.title
            : REPLACED_COPY.title;
    }

    get detailText() {
        return this.guard.state.reason === SESSION_CUTOVER_REASON
            ? CUTOVER_COPY.detail
            : REPLACED_COPY.detail;
    }

    onKeydown(ev) {
        if (ev.key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            this.reloginBtnRef()?.focus?.();
            return;
        }
        if (ev.key === "Tab") {
            ev.preventDefault();
            this.reloginBtnRef()?.focus?.();
        }
    }

    onRelogin() {
        return this.guard.relogin();
    }
}

registry
    .category("main_components")
    .add("TpSessionEndedOverlay", { Component: TpSessionEndedOverlay });
