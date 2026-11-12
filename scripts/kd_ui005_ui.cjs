/* KD-UI-005 live browser evidence. Writes only on the owned clone; no secrets in output. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/kd-ui005');
const target = process.argv[2] || 'clone';
const mode = process.argv[3] || 'before';
assert(['clone', 'dev'].includes(target));
assert(['before', 'after', 'verify', 'hoot', 'regression', 'measure'].includes(mode));
assert(target === 'clone' || ['verify', 'before', 'regression'].includes(mode), 'Dev is read-only.');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert(owner.rehearsal_passed && owner.database === 'tp_tanphat_kdui005_20261107' && owner.http_port === 18789);
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/kd-native001/dataset/dev/credentials.json'), 'utf8'));
const out = path.join(local, 'shots', `${target}-${['hoot', 'regression', 'measure'].includes(mode) ? 'after' : mode}`);
fs.mkdirSync(out, { recursive: true });
const results = [], errors = [], failures = [];
function sourceHashes() {
    const dir = path.join(root, target === 'clone' ? '.local/kd-ui005/source/custom_addons/tp_kd_workspace' : 'custom_addons/tp_kd_workspace');
    const result = {};
    function walk(folder) {
        for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
            if (item.name === '__pycache__' || item.name.endsWith('.pyc')) continue;
            const file = path.join(folder, item.name);
            if (item.isDirectory()) walk(file);
            else result[path.relative(dir, file).split(path.sep).join('/')] = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
        }
    }
    walk(dir); return result;
}
const initialHashes = sourceHashes();
const check = (name, condition, detail) => {
    if (!condition) failures.push(`${name}: ${JSON.stringify(detail)}`);
    else results.push(name);
};
const LEAVES = [
    ['opportunities', 'tp_kd_workspace.action_opportunities'], ['projects', 'tp_kd_workspace.action_projects'],
    ['contracts', 'tp_contract.action_tp_contracts'], ['tasks', 'tp_kd_workspace.action_tasks'],
    ['allocations', 'tp_kd_workspace.action_allocations'], ['productions', 'tp_kd_workspace.action_productions'],
    ['acceptances', 'tp_kd_workspace.action_acceptances'], ['payments', 'tp_kd_workspace.action_payments'],
    ['plans', 'tp_kd_workspace.action_plans'], ['credentials', 'tp_kd_workspace.action_credentials'],
    ['obligations', 'tp_kd_workspace.action_obligations'],
];
async function login(browser, key, options = {}) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'vi-VN', ...options });
    const response = await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db, ...actors[key] } },
    });
    assert((await response.json()).result?.uid, `${key} login failed`);
    return context;
}
async function rpc(context, model, method, args = [], kwargs = {}) {
    const response = await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
        data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } },
    });
    return response.json();
}
async function ok(context, model, method, args = [], kwargs = {}) {
    const body = await rpc(context, model, method, args, kwargs);
    assert(!body.error, `${model}.${method}: ${body.error?.data?.message}`);
    return body.result;
}
function watch(page) {
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
}
async function settle(page) {
    await page.waitForFunction(() => !document.querySelector('.o_loading_indicator'), null, { timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(250);
}
async function shot(page, name, full = false) {
    await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: full });
}
async function openList(page, action) {
    await page.goto(`${base}/odoo/action-${action}`, { timeout: 120000 });
    await page.locator('.o_list_view').first().waitFor({ timeout: 60000 });
    await settle(page);
}
async function openFirst(page) {
    await page.locator('.o_data_row .o_data_cell').first().click();
    await page.locator('.o_action_manager .o_form_view').waitFor({ timeout: 30000 });
    await settle(page);
}
async function main() {
    const browser = await chromium.launch({ headless: true });
    const ctx = { browser, root, local, base, db, target, mode, actors, out, results, errors,
        check, login, rpc, ok, watch, settle, shot, openList, openFirst, LEAVES };
    try {
        if (['before', 'measure'].includes(mode)) {
            const evidence = {};
            for (const width of [1440, 390]) {
                const context = await login(browser, 'editor', { viewport: { width, height: 1000 } });
                for (const [key, action] of LEAVES.slice(0, 2)) {
                    const page = await context.newPage(); watch(page);
                    let requests = 0;
                    page.on('request', r => { if (r.url().includes('/call_kw/')) requests++; });
                    await openList(page, action);
                    if (mode === 'before') await shot(page, `list-${key}-${width}`);
                    const list = requests; requests = 0;
                    await openFirst(page);
                    if (mode === 'before') await shot(page, `form-${key}-${width}`, true);
                    evidence[`${key}-${width}`] = { listRPC: list, formRPC: requests };
                    await page.close();
                }
                await context.close();
            }
            fs.writeFileSync(path.join(out, mode === 'before' ? 'baseline-rpc.json' : 'after-rpc.json'), JSON.stringify(evidence, null, 2));
            check('A four screens captured at desktop/mobile', true);
        } else if (mode === 'hoot') {
            const context = await login(browser, 'editor');
            const page = await context.newPage();
            const logs = [];
            page.on('console', m => logs.push(m.text())); watch(page);
            await page.goto(`${base}/web/tests?headless&debug=assets&filter=tp_kd_workspace`, { timeout: 180000 });
            const deadline = Date.now() + 240000;
            while (!logs.some(l => /Test suite succeeded|Some tests failed/i.test(l)) && Date.now() < deadline) {
                await page.waitForTimeout(500);
            }
            fs.writeFileSync(path.join(out, 'hoot.txt'), await page.locator('body').innerText());
            fs.writeFileSync(path.join(out, 'hoot-console.txt'), logs.join('\n'));
            check('HOOT native widget suite succeeded', logs.some(l => /Test suite succeeded/i.test(l)), logs.slice(-6));
            await context.close();
        } else if (mode === 'regression') {
            await require('./kd_ui003_ui_after.cjs')(ctx);
        } else {
            await require('./kd_ui005_checks.cjs')(ctx);
        }
    } catch (e) {
        failures.push(e.stack || e.message);
        for (const context of browser.contexts()) {
            for (const page of context.pages()) {
                await page.screenshot({ path: path.join(out, 'failure-screen.png'), fullPage: true }).catch(() => {});
                fs.writeFileSync(path.join(out, 'failure-body.txt'), await page.locator('body').innerText().catch(() => ''));
            }
        }
    }
    finally { await browser.close(); }
    if (JSON.stringify(initialHashes) !== JSON.stringify(sourceHashes())) failures.push('Application source changed during browser run.');
    const report = { target, mode, stage: process.env.BP_STAGE || 'all', source_hashes: initialHashes,
        passed: results.length, results, errors: [...new Set(errors)],
        failure: failures.length ? failures : null };
    const filename = mode === 'hoot' ? 'hoot-result.json' : mode === 'regression' ? 'regression-result.json' : 'result.json';
    fs.writeFileSync(path.join(out, filename), JSON.stringify(report, null, 2));
    if (['after', 'verify'].includes(mode)) fs.writeFileSync(path.join(out, `result-${report.stage}.json`), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ target, mode, passed: report.passed, errors: report.errors.length, failures: report.failure }));
    if (report.errors.length || failures.length) process.exitCode = 1;
}
main().catch(e => { console.error(e.message); process.exitCode = 1; });
