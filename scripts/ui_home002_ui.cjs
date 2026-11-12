/* Home browser evidence. Credentials and captured runtime menus stay in .local. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/ui-home002');
const target = process.argv[2] || 'clone';
const mode = process.argv[3] || 'before';
assert(['clone', 'dev'].includes(target));
assert(['before', 'after', 'verify', 'hoot'].includes(mode));
assert(target !== 'dev' || ['verify', 'before'].includes(mode));
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json')));
assert.equal(owner.http_port, 18589);
assert.equal(owner.database, 'tp_tanphat_home002_20261107');
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const secret = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json')));
const kd = JSON.parse(fs.readFileSync(path.join(root, '.local/kd-native001/dataset/dev/credentials.json')));
const actors = { admin: { login: 'admin', password: secret.admin }, kd: kd.editor };
if (target === 'clone' && fs.existsSync(path.join(local, 'fixture-credentials.json'))) {
    Object.assign(actors, JSON.parse(fs.readFileSync(path.join(local, 'fixture-credentials.json'))));
}
const out = path.join(local, 'shots', `${target}-${mode}`);
fs.mkdirSync(out, { recursive: true });
const results = [], errors = [];
function sourceHashes() {
    const folder = path.join(target === 'clone' ? path.join(local, 'source') : root, 'custom_addons/tp_web_home');
    const hashes = {};
    function walk(dir) {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
            if (entry.name === '__pycache__' || entry.name.endsWith('.pyc')) continue;
            const full = path.join(dir, entry.name);
            if (entry.isDirectory()) walk(full);
            else hashes[path.relative(folder, full).replaceAll('\\', '/')] = crypto.createHash('sha256').update(fs.readFileSync(full)).digest('hex');
        }
    }
    walk(folder);
    return hashes;
}
const homeSelector = '.o_tp_web_home';
const tileSelector = '.o_tp_web_home_tile';
function check(name, condition, detail) {
    results.push({ name, ok: Boolean(condition), detail });
    if (!condition) throw new Error(`${name}: ${JSON.stringify(detail)}`);
}
async function login(browser, actor, options = {}) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN', ...options });
    const response = await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db, ...actors[actor] } },
    });
    assert((await response.json()).result?.uid, `${actor}: login failed`);
    return context;
}
function watch(page) {
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('response', r => { if (r.status() >= 400 && /\/tp_web_home\/static\//.test(r.url())) errors.push(`${r.status()} ${r.url()}`); });
}
async function home(page) {
    await page.goto(`${base}/odoo/tp-home`);
    await page.locator(tileSelector).first().waitFor({ timeout: 30000 });
    await page.waitForTimeout(250);
}
async function shot(page, name, full = false) {
    const original = page.viewportSize();
    if (full) {
        const height = await page.locator(homeSelector).evaluate(el => el.scrollHeight);
        await page.setViewportSize({ width: original.width, height: Math.min(height + 80, 5000) });
        await page.waitForTimeout(100);
    }
    await page.screenshot({ path: path.join(out, name + '.png') });
    if (full) await page.setViewportSize(original);
}
async function inventory(page) {
    return page.locator(tileSelector).evaluateAll(els => els.map(el => ({
        xmlid: el.dataset.menuXmlid, href: el.getAttribute('href'),
        label: el.querySelector('.o_tp_web_home_label')?.textContent,
        group: el.closest('section')?.getAttribute('aria-label'),
    })));
}
async function main() {
    const browser = await chromium.launch({ headless: true });
    try {
        if (mode === 'hoot') {
            const context = await login(browser, 'admin');
            const page = await context.newPage();
            const logs = [];
            page.on('console', msg => logs.push(msg.text()));
            page.on('pageerror', e => errors.push(e.message));
            await page.goto(`${base}/web/tests?headless&debug=assets&filter=tp_web_home`, { timeout: 180000 });
            const deadline = Date.now() + 240000;
            while (!logs.some(line => /Test suite succeeded|Some tests failed/i.test(line)) && Date.now() < deadline) {
                await page.waitForTimeout(500);
            }
            const body = await page.locator('body').innerText();
            fs.writeFileSync(path.join(out, 'hoot.txt'), body);
            fs.writeFileSync(path.join(out, 'console.txt'), logs.join('\n'));
            await page.screenshot({ path: path.join(out, 'hoot.png'), fullPage: true });
            console.log(JSON.stringify({ title: await page.title(), summary: body.slice(0, 1800), console: logs.slice(-15) }));
            check('HOOT completed successfully', /test suite succeeded/i.test(logs.join('\n')), body.slice(0, 500));
            return;
        }
        for (const actor of ['admin', 'kd']) {
            const context = await login(browser, actor);
            const page = await context.newPage();
            watch(page);
            await home(page);
            const items = await inventory(page);
            fs.writeFileSync(path.join(out, `${actor}-inventory.json`), JSON.stringify(items, null, 2));
            const menus = await (await context.request.get(`${base}/web/webclient/load_menus`)).json();
            fs.writeFileSync(path.join(out, `${actor}-menus.json`), JSON.stringify(menus, null, 2));
            await shot(page, `${actor}-desktop-1440`);
            await shot(page, `${actor}-desktop-full`, true);
            await page.setViewportSize({ width: 390, height: 844 });
            await shot(page, `${actor}-mobile-390`);
            await shot(page, `${actor}-mobile-full`, true);
            check(`${actor}: baseline captured`, items.length > 0);
            await context.close();
        }
        if (mode !== 'before') {
            await require('./ui_home002_checks.cjs')({ browser, login, actors, base, db, out, local, target,
                check, watch, home, shot, inventory, results, errors, chromium });
        }
    } catch (error) {
        results.push({ name: 'suite completed', ok: false, detail: error.message });
        throw error;
    } finally {
        await browser.close();
        fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify({ target, mode, ok: results.every(r => r.ok) && !errors.length, results, errors, source_hashes: sourceHashes() }, null, 2));
    }
    console.log(JSON.stringify({ target, mode, checks: results.length, errors: errors.length }));
    if (errors.length) process.exitCode = 1;
}
main().catch(e => { console.error(e.message); process.exitCode = 1; });
