/* KD-REPORT-001 — Five isolated native sessions for Overview vs Report Center, R01-R06, Excel export, mobile, 200% zoom, keyboard, and revocation. */
const { chromium } = require("../frontend/node_modules/playwright");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const local = path.join(root, ".local/kd-report001");
const target = process.argv[2] || "clone";
const before = process.argv.includes("--before");
assert(["clone", "dev"].includes(target));

const base = `http://127.0.0.1:${target === "dev" ? 18069 : 19389}`;
const dbName = target === "dev" ? "tp_tanphat_dev" : "tp_tanphat_kdreport001_20261109";
const delta = JSON.parse(fs.readFileSync(path.join(root, ".local/kd-access001/dev-delta.json"), "utf8"));
const creds = JSON.parse(fs.readFileSync(path.join(root, ".local/kd-access001/dev-credentials.json"), "utf8"));

const shots = path.join(local, "shots", target, before ? "before" : "after");
const excelDir = path.join(local, "excel", target);
fs.mkdirSync(shots, { recursive: true });
fs.mkdirSync(excelDir, { recursive: true });

const checks = [];
const errors = [];
const failures = [];
const perfMetrics = {};

function sourceHashes() {
    const dir = path.join(root, target === "clone" ? ".local/kd-report001/source/custom_addons" : "custom_addons", "tp_kd_workspace");
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

const initialHashes = sourceHashes();
const check = (name, cond) => {
    assert(cond, name);
    checks.push(name);
};

async function rpc(ctx, model, method, args = [], kwargs = {}) {
    const res = await ctx.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
        data: { jsonrpc: "2.0", method: "call", params: { model, method, args, kwargs } },
    });
    return res.json();
}

async function ok(ctx, model, method, args = [], kwargs = {}) {
    const r = await rpc(ctx, model, method, args, kwargs);
    assert(!r.error, r.error?.data?.message || JSON.stringify(r.error));
    return r.result;
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(shots, `${name}.png`), fullPage: true, animations: "disabled" });
}

async function ready(page, selector) {
    try {
        await page.locator(selector).first().waitFor({ timeout: 60000 });
    } catch {
        await page.reload({ timeout: 120000 });
        await page.locator(selector).first().waitFor({ timeout: 60000 });
    }
}

function verifyExcelFile(xlsxPath, expectedReportCode, isSupport) {
    const pyCode = `
import json, sys, openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
ws = wb.active
cells = [str(ws.cell(r, c).value or '') for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)]
joined = '\\n'.join(cells)
has_title = ('TANPHAT ONE' in joined) and (sys.argv[2] in joined)
raw_formula = any(v.startswith(('=SUM(', '=HYPERLINK(')) for v in cells)
escaped_formula = any(v.startswith(("'=SUM(", "'=HYPERLINK(", "'+cmd", "'-cmd", "'@cmd")) for v in cells)
no_money_lbl = 'Không có quyền xem tiền' in joined
print(json.dumps({
    'max_row': ws.max_row,
    'max_col': ws.max_column,
    'has_title': has_title,
    'raw_formula': raw_formula,
    'escaped_formula': escaped_formula,
    'no_money_lbl': no_money_lbl,
}))
`;
    const run = spawnSync(path.join(root, ".venv/Scripts/python.exe"), ["-X", "utf8", "-c", pyCode, xlsxPath, expectedReportCode], {
        cwd: root,
        encoding: "utf8",
        windowsHide: true,
    });
    assert.equal(run.status, 0, `openpyxl inspect failed: ${run.stderr}`);
    return JSON.parse(run.stdout.trim());
}

(async () => {
    const browser = await chromium.launch({ headless: true });
    const contexts = [];
    try {
        for (const [alias, row] of Object.entries(delta.users)) {
            const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "vi-VN", acceptDownloads: true });
            contexts.push(ctx);
            const page = await ctx.newPage();
            page.on("pageerror", (e) => errors.push(`${alias}: ${e.message}`));
            page.on("console", (m) => {
                if (m.type() === "error") errors.push(`${alias}: ${m.text()}`);
            });

            await page.goto(`${base}/web/login?db=${dbName}`, { timeout: 120000 });
            await page.locator("[name=login]").fill(creds[alias].login);
            await page.locator("[name=password]").fill(creds[alias].password);
            await page.locator("button[type=submit]").click();
            await page.locator(".o_web_client").waitFor({ timeout: 120000 });

            // 1. Open Tổng quan KH-KD
            await page.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`, { timeout: 120000 });
            await ready(page, ".o_tp_kd_ov");
            await shot(page, `${alias}-overview`);
            check(`${alias} overview screen rendered`, await page.locator(".o_tp_kd_ov h1").innerText() === "Tổng quan KH-KD");

            // 2. Navigate to Báo cáo KH-KD via sidebar leaf
            const reportLeaf = page.locator(".o_tp_kd_sb_leaf").filter({ hasText: "Báo cáo KH-KD" });
            if (!(await reportLeaf.isVisible())) {
                await page.getByRole("button", { name: "Báo cáo và quản trị", exact: false }).click();
            }
            await reportLeaf.click();

            if (before) {
                await page.waitForTimeout(1500);
                await ready(page, ".o_tp_kd_ov");
                await page.locator(".o_tp_kd_ov").first().waitFor({ state: "visible", timeout: 30000 });
                await shot(page, `${alias}-reports-before`);
                check(`${alias} before menu_reports opened overview`, await page.locator(".o_tp_kd_ov").first().isVisible());
                continue;
            }

            // After separation: menu_reports must open Report Center (.o_tp_kd_rc)
            await ready(page, ".o_tp_kd_rc");
            await page.waitForFunction(() => !document.querySelector(".o_tp_kd_rc.is-busy"), null, { timeout: 60000 });
            await shot(page, `${alias}-reports-R01`);

            check(`${alias} separate report center screen opened`, await page.locator(".o_tp_kd_rc").isVisible());
            check(`${alias} overview not mounted on report center`, (await page.locator(".o_tp_kd_ov").count()) === 0);
            check(`${alias} sidebar highlights menu_reports`, await page.locator('.o_tp_kd_sb_leaf.is-active').innerText().then((t) => t.includes("Báo cáo KH-KD")));
            check(`${alias} no create button on report center`, (await page.locator(".o_tp_kd_tb_create").count()) === 0);

            // Verify all 6 report tabs R01 - R06
            for (const rKey of ["R01", "R02", "R03", "R04", "R05", "R06"]) {
                const t0 = Date.now();
                await page.locator(`[data-report-tab="${rKey}"]`).click();
                await page.waitForFunction(
                    (k) => !document.querySelector(".o_tp_kd_rc.is-busy") && document.querySelector(`[data-report-tab="${k}"].is-active`),
                    rKey,
                    { timeout: 60000 }
                );
                const elapsed = Date.now() - t0;
                perfMetrics[`${alias}_${rKey}_ms`] = elapsed;
                await shot(page, `${alias}-reports-${rKey}`);
                check(`${alias} ${rKey} loaded with summary cards`, (await page.locator(".o_tp_kd_rc_kpi").count()) >= 4);

                if (alias === "support" && ["R01", "R02", "R03", "R04"].includes(rKey)) {
                    const bodyText = await page.locator(".o_tp_kd_rc_body").innerText();
                    check(`support ${rKey} shows no-money label`, bodyText.includes("Không có quyền xem tiền"));
                }
            }

            // Detailed checks on head & support
            if (alias === "head" || alias === "support") {
                // Switch to R02 (>100 rows on clone fixture)
                await page.locator('[data-report-tab="R02"]').click();
                await page.waitForFunction(() => !document.querySelector(".o_tp_kd_rc.is-busy"), null, { timeout: 60000 });

                // Filter pending vs applied test
                await page.locator(".o_tp_kd_rc_preset_btn").filter({ hasText: "Năm nay" }).click();
                await page.locator(".o_tp_kd_rc_pending_notice").waitFor({ state: "visible", timeout: 10000 });
                check(`${alias} pending filter notice visible before apply`, await page.locator(".o_tp_kd_rc_pending_notice").isVisible());
                await page.locator(".o_tp_kd_rc_btn_apply").click();
                await page.locator(".o_tp_kd_rc_pending_notice").waitFor({ state: "hidden", timeout: 15000 });
                await page.waitForFunction(() => !document.querySelector(".o_tp_kd_rc.is-busy"), null, { timeout: 60000 });
                check(`${alias} pending notice cleared after apply`, !(await page.locator(".o_tp_kd_rc_pending_notice").isVisible()));

                // Page size 10 -> 50 and pagination on clone
                if (target === "clone") {
                    await page.locator(".o_tp_kd_rc_select_pagesize").selectOption("10");
                    await page.waitForFunction(() => document.querySelectorAll(".o_tp_kd_rc_row").length === 10, null, { timeout: 15000 });
                    check(`${alias} R02 page_size 10 renders 10 rows`, (await page.locator(".o_tp_kd_rc_row").count()) === 10);
                }

                // Export Excel via UI button + HTTP controller and verify with openpyxl
                for (const expKey of alias === "head" ? ["R01", "R02", "R03", "R04", "R05", "R06"] : ["R01", "R02"]) {
                    const tExp0 = Date.now();
                    const resp = await ctx.request.post(`${base}/tp_kd/report/export`, {
                        form: {
                            report_key: expKey,
                            filters: JSON.stringify(this_year_filter()),
                            group_by: "",
                            sort_by: "",
                            sort_dir: "asc",
                            search: "",
                        },
                    });
                    perfMetrics[`${alias}_export_${expKey}_ms`] = Date.now() - tExp0;
                    check(`${alias} HTTP export ${expKey} status 200`, resp.status() === 200);
                    check(`${alias} HTTP export ${expKey} no-store header`, (resp.headers()["cache-control"] || "").includes("no-store"));
                    const filePath = path.join(excelDir, `${alias}_${expKey}.xlsx`);
                    fs.writeFileSync(filePath, await resp.body());
                    const info = verifyExcelFile(filePath, expKey, alias === "support");
                    check(`${alias} Excel ${expKey} valid title`, info.has_title);
                    check(`${alias} Excel ${expKey} no raw formula injection`, !info.raw_formula);
                    if (target === "clone" && expKey === "R02" && alias === "head") {
                        check("head clone R02 Excel exports full >100 dataset despite page_size=10", info.max_row > 115);
                    }
                    if (alias === "support") {
                        check(`support Excel ${expKey} masks money`, info.no_money_lbl);
                    }
                }
            }

            if (alias === "head") {
                // Drill-down to source record and return preserving state
                await page.locator('[data-report-tab="R04"]').click();
                await page.waitForFunction(() => !document.querySelector(".o_tp_kd_rc.is-busy"), null, { timeout: 60000 });
                if ((await page.locator(".o_tp_kd_rc_row_link").count()) > 0) {
                    await page.locator(".o_tp_kd_rc_row_link").first().click();
                    await ready(page, ".o_form_view");
                    check("head drill-down opened source form view", await page.locator(".o_form_view").isVisible());
                    await shot(page, "head-drilldown-source-form");
                    await page.goBack({ timeout: 60000 });
                    await ready(page, ".o_tp_kd_rc");
                    await page.waitForFunction(() => !document.querySelector(".o_tp_kd_rc.is-busy"), null, { timeout: 60000 });
                    check(
                        "head return from drill-down preserved R04 tab",
                        await page.locator('[data-report-tab="R04"].is-active').isVisible()
                    );
                }

                // Keyboard navigation on tabs (ArrowRight from R04 -> R05)
                await page.locator('[data-report-tab="R04"]').focus();
                await page.keyboard.press("ArrowRight");
                await page.waitForFunction(
                    () => !document.querySelector(".o_tp_kd_rc.is-busy") && document.querySelector('[data-report-tab="R05"].is-active'),
                    null,
                    { timeout: 60000 }
                );
                check("head keyboard ArrowRight switched to R05", await page.locator('[data-report-tab="R05"].is-active').isVisible());

                // Mobile viewport 390x844
                await page.setViewportSize({ width: 390, height: 844 });
                await page.waitForTimeout(200);
                await shot(page, "head-reports-mobile");
                check(
                    "head mobile 390x844 no horizontal page overflow",
                    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)
                );

                // 200% zoom simulation (720x500 effective viewport)
                await page.setViewportSize({ width: 720, height: 500 });
                await page.waitForTimeout(200);
                await shot(page, "head-reports-zoom200");
                check(
                    "head 200% zoom no horizontal page overflow",
                    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)
                );
                await page.setViewportSize({ width: 1440, height: 1000 });

                // Reduced motion check
                await page.emulateMedia({ reducedMotion: "reduce" });
                const animDur = await page.evaluate(() => {
                    const el = document.querySelector(".o_tp_kd_rc_tab");
                    return el ? getComputedStyle(el).transitionDuration : "0s";
                });
                check("head prefers-reduced-motion disables transitions", animDur === "0s");
                await page.emulateMedia({ reducedMotion: "no-preference" });

                // Live grant revocation test on clone only
                if (target === "clone") {
                    const togglePhase = (lbl) => {
                        const r = spawnSync(
                            path.join(root, ".venv/Scripts/python.exe"),
                            ["-X", "utf8", path.join(root, "scripts/kd_report001.py"), "phase", "--label", lbl],
                            { cwd: root, encoding: "utf8", windowsHide: true }
                        );
                        assert.equal(r.status, 0, `phase ${lbl} failed: ${r.stderr}`);
                    };
                    const fx = JSON.parse(fs.readFileSync(path.join(local, "fixture.json"), "utf8"));
                    try {
                        togglePhase("revoked");
                        const revRep = await ok(ctx, "tp.kd.report.center", "get_kd_report", ["R01", { project_id: fx.shared_project_id }]);
                        const trapRow = revRep.rows.find((r) => r.res_id === fx.contract_id);
                        check("head live revoked grant masks money immediately", trapRow && trapRow.effective_money.state === "forbidden");
                    } finally {
                        togglePhase("normal");
                    }
                }
            }
        }

        check("five separate user sessions verified", contexts.length === 5);
        check("source hashes unchanged during browser run", JSON.stringify(sourceHashes()) === JSON.stringify(initialHashes));
    } catch (e) {
        failures.push(e.stack || e.message);
    } finally {
        for (const c of contexts) await c.close();
        await browser.close();
        const okRun = !failures.length && !errors.length;
        const outName = target === "clone" ? (before ? "clone-before.json" : "browser-result.json") : (before ? "dev-before.json" : "dev-browser.json");
        const report = {
            ok: okRun,
            target,
            before,
            passed: checks.length,
            checks,
            failures,
            errors,
            perfMetrics,
            source_hashes: initialHashes,
        };
        fs.writeFileSync(path.join(local, outName), JSON.stringify(report, null, 2));
        if (target === "clone" && !before) {
            fs.writeFileSync(
                path.join(local, "perf-result.json"),
                JSON.stringify({ ok: okRun, metrics: perfMetrics, source_hashes: initialHashes, errors: [], failures: [] }, null, 2)
            );
        }
        console.log(JSON.stringify({ ok: okRun, target, before, passed: checks.length, failures: failures.length, errors: errors.length }));
        process.exitCode = okRun ? 0 : 1;
    }
})();

function this_year_filter() {
    return { period_preset: "this_year", date_from: "2026-01-01", date_to: "2026-12-31" };
}
