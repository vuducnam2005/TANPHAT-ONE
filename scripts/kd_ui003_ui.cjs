/* KD-UI-003 browser evidence (tables + detail screens). Credentials, RPC payloads and images stay in .local. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/kd-ui003');
const target = process.argv[2] || 'clone';
const mode = process.argv[3] || 'before';
assert(['clone', 'dev'].includes(target) && ['before', 'after', 'verify'].includes(mode));
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_kdui003_20261106');
assert.equal(owner.http_port, 18389);
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

// Leaf -> action path. Contracts open through the TP Contracts server action (same as the sidebar menu).
const LEAVES = [
  ['opportunities', 'tp_kd_workspace.action_opportunities'],
  ['projects', 'tp_kd_workspace.action_projects'],
  ['contracts', 'tp_contract.action_tp_contracts'],
  ['tasks', 'tp_kd_workspace.action_tasks'],
  ['allocations', 'tp_kd_workspace.action_allocations'],
  ['productions', 'tp_kd_workspace.action_productions'],
  ['acceptances', 'tp_kd_workspace.action_acceptances'],
  ['payments', 'tp_kd_workspace.action_payments'],
  ['plans', 'tp_kd_workspace.action_plans'],
  ['credentials', 'tp_kd_workspace.action_credentials'],
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
  await page.waitForTimeout(500);
}
async function shot(page, name, full = false) {
  await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: full });
}
async function openList(page, action) {
  await page.goto(`${base}/odoo/action-${action}`);
  await page.locator('.o_list_view').first().waitFor({ timeout: 20000 });
  await settle(page);
}
async function openFirst(page) {
  await page.locator('.o_list_view .o_data_row .o_data_cell').first().click();
  await page.locator('.o_form_view').first().waitFor({ timeout: 20000 });
  await settle(page);
}

async function before(browser) {
  for (const [w, h, label, leaves] of [
    [1440, 1000, '1440', LEAVES.map(l => l[0])],
    [390, 844, '390', ['tasks', 'opportunities', 'allocations']],
  ]) {
    const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
    const page = await context.newPage();
    watch(page);
    await page.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);
    await page.locator('.o_action_manager .o_action').first().waitFor();
    await settle(page);
    await shot(page, `overview-${label}`);
    await page.close();
    for (const [key, action] of LEAVES.filter(l => leaves.includes(l[0]))) {
      if (fs.existsSync(path.join(out, `list-${key}-${label}.png`))) continue;
      const leafPage = await context.newPage();  // one page per leaf: long sessions crash headless Chromium
      watch(leafPage);
      await openList(leafPage, action);
      await shot(leafPage, `list-${key}-${label}`);
      if (await leafPage.locator('.o_data_row').count()) {
        await openFirst(leafPage);
        await shot(leafPage, `form-${key}-${label}`, w > 400);
      }
      await leafPage.close();
    }
    await context.close();
  }
  const context = await login(browser, 'metadata');
  const page = await context.newPage();
  watch(page);
  await openList(page, 'tp_kd_workspace.action_allocations');
  await openFirst(page);
  await shot(page, 'form-allocations-metadata-1440', true);
  await context.close();
  results.push('before screenshots captured');
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    if (mode === 'before') await before(browser);
    else await require('./kd_ui003_ui_after.cjs')({ browser, base, db, login, ok, rpc, watch, settle, shot, openList, openFirst, check, out, errors, target, mode, LEAVES, actors });
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
