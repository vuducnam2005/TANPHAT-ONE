/* Run HOOT unit tests for tp_kd_workspace on owned clone 19389 and record source hashes. */
const { chromium } = require("../frontend/node_modules/playwright");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");

const root = path.resolve(__dirname, "..");
const local = path.join(root, ".local/kd-report001");
const secret = JSON.parse(fs.readFileSync(path.join(root, ".local/dev-secrets.json"), "utf8"));

function sourceHashes() {
    const dir = path.join(local, "source/custom_addons/tp_kd_workspace");
    const out = {};
    function walk(d) {
        for (const e of fs.readdirSync(d, { withFileTypes: true })) {
            if (e.name === "__pycache__" || e.name.endsWith(".pyc")) continue;
            const full = path.join(d, e.name);
            if (e.isDirectory()) walk(full);
            else out[path.relative(dir, full).split(path.sep).join("/")] = crypto.createHash("sha256").update(fs.readFileSync(full)).digest("hex");
        }
    }
    walk(dir);
    return out;
}

(async () => {
    const hashes = sourceHashes();
    const browser = await chromium.launch({ headless: true });
    let ok = false;
    const summaries = [];
    const errors = [];
    const failures = [];
    try {
        const context = await browser.newContext();
        const page = await context.newPage();
        await page.goto("http://127.0.0.1:19389/web/login?db=tp_tanphat_kdreport001_20261109", { timeout: 120000 });
        await page.locator("[name=login]").fill("admin");
        await page.locator("[name=password]").fill(secret.admin);
        await page.locator("button[type=submit]").click();
        await page.locator(".o_web_client").waitFor({ timeout: 120000 });

        for (const mod of ["tp_kd_workspace"]) {
            const logs = [];
            const listener = (m) => logs.push(m.text());
            page.on("console", listener);
            await page.goto(`http://127.0.0.1:19389/web/tests?headless&debug=assets&filter=${mod}`, { timeout: 180000 });
            const end = Date.now() + 240000;
            while (!logs.some((l) => /Test suite succeeded|Some tests failed/i.test(l)) && Date.now() < end) {
                await page.waitForTimeout(500);
            }
            const passed = logs.some((l) => /Test suite succeeded/i.test(l));
            fs.writeFileSync(path.join(local, `hoot-${mod}.txt`), (await page.locator("body").innerText()) + "\n" + logs.join("\n"));
            summaries.push({ module: mod, passed });
            page.off("console", listener);
            if (!passed) failures.push(`HOOT failed for ${mod}`);
            assert(passed, `HOOT failed for ${mod}`);
        }
        assert.deepEqual(sourceHashes(), hashes, "Source changed during HOOT run");
        ok = true;
    } catch (e) {
        failures.push(e.message);
    } finally {
        await browser.close();
        const report = { ok: ok && !failures.length && !errors.length, summaries, failures, errors, source_hashes: hashes };
        fs.writeFileSync(path.join(local, "hoot-result.json"), JSON.stringify(report, null, 2));
        console.log(JSON.stringify({ ok: report.ok, summaries }));
        process.exitCode = report.ok ? 0 : 1;
    }
})();
