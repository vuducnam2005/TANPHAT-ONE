// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * Guard against host-injected WebView bridge errors (for example Zalo iOS
 * WKWebView evaluating `zaloJSV2` inside external web pages).
 *
 * Unlike third-party <script> tags, WKWebView.evaluateJavaScript executes in
 * the document global scope with the page URL as filename, so Odoo's core
 * errorService cannot classify it as ThirdPartyScriptError and opens a blocking
 * ClientErrorDialog. We suppress only that non-app host ReferenceError without
 * creating any fake `window.zaloJSV2` stub and without masking real app errors.
 */

import { UncaughtClientError, UncaughtPromiseError } from "@web/core/errors/error_service";
import { registry } from "@web/core/registry";

const EXTERNAL_ZALO_VAR_RE = /\bzaloJSV2\b/;
const BUNDLE_PATH_RE = /(?:\/web\/assets\/|\/static\/(?:src|lib)\/)/i;
const JS_FILE_PATH_RE = /\.m?js$/i;
const STACK_JS_FRAME_RE = /\.m?js(?:\?[^:\s]*)?:\d+/i;

let warnedOnce = false;

function hasAppScriptOrigin(filename, stack) {
    if (filename) {
        const cleanFile = filename.split(/[?#]/, 1)[0];
        if (BUNDLE_PATH_RE.test(cleanFile) || JS_FILE_PATH_RE.test(cleanFile)) {
            return true;
        }
    }
    if (stack && (BUNDLE_PATH_RE.test(stack) || STACK_JS_FRAME_RE.test(stack))) {
        return true;
    }
    return false;
}

/**
 * Return true only for an uncaught ReferenceError referencing `zaloJSV2`
 * injected into global document scope outside any application JS bundle.
 */
export function isExternalWebViewHostError(uncaughtError, originalError) {
    if (!uncaughtError) {
        return false;
    }
    const isClientOrPromiseError =
        uncaughtError instanceof UncaughtClientError ||
        uncaughtError instanceof UncaughtPromiseError ||
        String(uncaughtError.name || "").startsWith("UncaughtClientError") ||
        String(uncaughtError.name || "").startsWith("UncaughtPromiseError");
    if (!isClientOrPromiseError) {
        return false;
    }

    const ev = uncaughtError.event || uncaughtError.unhandledRejectionEvent;
    const errorName = originalError?.name || "";
    const rawMessage = String(
        originalError?.message || ev?.message || uncaughtError.message || ""
    );
    const isReferenceError =
        originalError instanceof ReferenceError ||
        errorName === "ReferenceError" ||
        /\bReferenceError\b/.test(rawMessage);
    if (!isReferenceError || !EXTERNAL_ZALO_VAR_RE.test(rawMessage)) {
        return false;
    }

    const filename = String(ev?.filename || "");
    const stack = String(originalError?.stack || uncaughtError.traceback || "");
    return !hasAppScriptOrigin(filename, stack);
}

/**
 * Error handler registered before `defaultHandler` to keep Zalo/WebView host
 * injection errors from interrupting users with a blocking ClientErrorDialog.
 */
export function tpExternalWebViewErrorHandler(env, error, originalError) {
    if (!isExternalWebViewHostError(error, originalError)) {
        return false;
    }
    error.event?.preventDefault?.();
    error.unhandledRejectionEvent?.preventDefault?.();
    if (!warnedOnce) {
        warnedOnce = true;
        console.warn(
            "TANPHAT ONE: ignored external WebView host error:",
            originalError?.message || error?.event?.message || error?.message
        );
    }
    return true;
}

registry
    .category("error_handlers")
    .add("tpExternalWebViewErrorHandler", tpExternalWebViewErrorHandler, { sequence: 2 });
