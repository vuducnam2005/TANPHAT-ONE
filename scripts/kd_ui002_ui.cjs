/* KD-UI-002 browser evidence. Credentials, RPC payloads and images stay in .local (private). */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/kd-ui002');
const target = process.argv[2] || 'clone';
const mode = process.argv[3] || 'before';
assert(['clone', 'dev'].includes(target) && ['before', 'after', 'verify'].includes(mode));
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_kdui002_20261106');
assert.equal(owner.http_port, 18289);
assert(owner.rehearsal_passed);
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/kd-native001/dataset/dev/credentials.json'), 'utf8'));
const out = path.join(local, 'shots', `${target}-${mode}`);
fs.mkdirSync(out, { recursive: true });
const results = [];
const errors = [];
function check(name, condition, detail) {
  if (!condition) throw new Error(`${name}${detail ? `: ${JSON.stringify(detail)}` : ''}`);
  results.push(name);
}

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
async function ok(context, model, method, args, kwargs) {
  const body = await rpc(context, model, method, args, kwargs);
  assert(!body.error, `${model}.${method}: ${body.error?.data?.message}`);
  return body.result;
}
function watch(page) {
  page.on('pageerror', error => errors.push(`pageerror ${error.message}`));
  page.on('console', msg => { if (msg.type() === 'error') errors.push(`console ${msg.text()}`); });
}
async function settle(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(600);
}
async function shot(page, name, full = false) {
  await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: full });
}
async function openOverview(page) {
  await page.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);
  await page.locator('.o_action_manager .o_action').first().waitFor();
  await settle(page);
}

async function before(browser) {
  for (const [w, h, label] of [[1440, 1000, '1440'], [1024, 900, '1024'], [390, 844, '390']]) {
    const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
    const page = await context.newPage();
    watch(page);
    await openOverview(page);
    await shot(page, `overview-${label}`);
    await shot(page, `overview-${label}-full`, true);
    if (w === 1440) {
      await page.goto(`${base}/odoo/action-tp_kd_workspace.action_allocations`);
      await page.locator('.o_list_view').waitFor();
      await settle(page);
      await shot(page, 'list-allocation-1440');
      await page.locator('.o_data_row').first().click();
      await page.locator('.o_form_view').waitFor();
      await settle(page);
      await shot(page, 'form-allocation-1440');
    }
    if (w === 390) {
      const burger = page.locator('.o_mobile_menu_toggle, .o_navbar_apps_menu button, button[title="Menu"]').first();
      if (await burger.count()) {
        await burger.click();
        await settle(page);
        await shot(page, 'mobile-menu-390');
      }
    }
    await context.close();
  }
  results.push('before screenshots captured');
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    if (mode === 'before') await before(browser);
    else await require('./kd_ui002_ui_after.cjs')({ browser, base, db, login, ok, rpc, watch, settle, shot, openOverview, check, out, errors, target, mode });
  } finally {
    await browser.close();
  }
  const summary = { target, mode, results, errors: [...new Set(errors)] };
  fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify({ target, mode, passed: results.length, errors: summary.errors.length }));
}
main().catch(error => {
  fs.writeFileSync(path.join(out, 'failure.txt'), String(error.stack || error));
  console.error('FAIL', error.message);
  process.exit(1);
});
