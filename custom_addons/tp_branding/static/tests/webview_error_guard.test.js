// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import { describe, expect, test } from "@odoo/hoot";
import { makeTestApp, mockService } from "@web/../tests/web_test_helpers";
import { UncaughtClientError } from "@web/core/errors/error_service";
import { isExternalWebViewHostError } from "@tp_branding/webview_error_guard";

describe("tp_branding webview_error_guard", () => {
    test("matches Zalo iOS WKWebView global ReferenceError without app JS frame", () => {
        const err = new ReferenceError("Can't find variable: zaloJSV2");
        Object.defineProperty(err, "stack", {
            value: "global code@https://tpone.tadic.vn/app/trang-chu:1:21",
        });
        const uncaught = new UncaughtClientError("Uncaught Javascript Error > Can't find variable: zaloJSV2");
        uncaught.event = {
            filename: "https://tpone.tadic.vn/app/trang-chu",
            lineno: 1,
            colno: 21,
        };
        uncaught.cause = err;

        expect(isExternalWebViewHostError(uncaught, err)).toBe(true);
    });

    test("matches V8/Android WebView ReferenceError for zaloJSV2", () => {
        const err = new ReferenceError("zaloJSV2 is not defined");
        Object.defineProperty(err, "stack", {
            value: "ReferenceError: zaloJSV2 is not defined\n    at <anonymous>:1:1",
        });
        const uncaught = new UncaughtClientError("Uncaught Javascript Error > zaloJSV2 is not defined");
        uncaught.event = { filename: "", lineno: 0, colno: 0 };
        uncaught.cause = err;

        expect(isExternalWebViewHostError(uncaught, err)).toBe(true);
    });

    test("does not suppress errors originating from app asset JS bundles", () => {
        const err = new ReferenceError("Can't find variable: zaloJSV2");
        Object.defineProperty(err, "stack", {
            value: "fn@https://tpone.tadic.vn/web/assets/8f258d2/web.assets_web.min.js:120:5",
        });
        const uncaught = new UncaughtClientError("Uncaught Javascript Error > Can't find variable: zaloJSV2");
        uncaught.event = {
            filename: "https://tpone.tadic.vn/web/assets/8f258d2/web.assets_web.min.js",
            lineno: 120,
            colno: 5,
        };
        uncaught.cause = err;

        expect(isExternalWebViewHostError(uncaught, err)).toBe(false);
    });

    test("does not suppress unrelated ReferenceError or TypeError", () => {
        const refErr = new ReferenceError("Can't find variable: missingAppVar");
        Object.defineProperty(refErr, "stack", {
            value: "global code@https://tpone.tadic.vn/app/trang-chu:1:1",
        });
        const uncaughtRef = new UncaughtClientError("Uncaught Javascript Error > Can't find variable: missingAppVar");
        uncaughtRef.event = { filename: "https://tpone.tadic.vn/app/trang-chu", lineno: 1, colno: 1 };
        expect(isExternalWebViewHostError(uncaughtRef, refErr)).toBe(false);

        const typeErr = new TypeError("Cannot read properties of undefined (reading 'zaloJSV2')");
        const uncaughtType = new UncaughtClientError("Uncaught Javascript Error");
        uncaughtType.event = { filename: "https://tpone.tadic.vn/app/trang-chu", lineno: 1, colno: 1 };
        expect(isExternalWebViewHostError(uncaughtType, typeErr)).toBe(false);
    });

    test("suppresses dialog for injected zaloJSV2 ErrorEvent while keeping real errors visible", async () => {
        let dialogsAdded = 0;
        mockService("dialog", {
            add() {
                dialogsAdded += 1;
                expect.step("dialog.add");
            },
        });
        await makeTestApp();

        expect.errors(2);
        const zaloErr = new ReferenceError("Can't find variable: zaloJSV2");
        Object.defineProperty(zaloErr, "stack", {
            value: "global code@https://tpone.tadic.vn/app/trang-chu:1:21",
        });
        window.dispatchEvent(
            new ErrorEvent("error", {
                message: "ReferenceError: Can't find variable: zaloJSV2",
                filename: "https://tpone.tadic.vn/app/trang-chu",
                lineno: 1,
                colno: 21,
                error: zaloErr,
            })
        );
        await Promise.resolve();
        await Promise.resolve();
        expect(dialogsAdded).toBe(0);
        expect(window.zaloJSV2).toBe(undefined);

        const realErr = new ReferenceError("realAppBug is not defined");
        Object.defineProperty(realErr, "stack", {
            value: "ReferenceError: realAppBug is not defined\n    at https://tpone.tadic.vn/web/assets/1/web.assets_web.min.js:10:2",
        });
        window.dispatchEvent(
            new ErrorEvent("error", {
                message: "ReferenceError: realAppBug is not defined",
                filename: "https://tpone.tadic.vn/web/assets/1/web.assets_web.min.js",
                lineno: 10,
                colno: 2,
                error: realErr,
            })
        );
        await expect.waitForSteps(["dialog.add"]);
        expect(dialogsAdded).toBe(1);
        expect.verifyErrors([
            "ReferenceError: Can't find variable: zaloJSV2",
            "ReferenceError: realAppBug is not defined",
        ]);
    });
});
