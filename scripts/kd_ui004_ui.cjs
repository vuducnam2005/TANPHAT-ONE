/* KD-UI-004 browser evidence (Tổng quan redesign). Credentials, RPC payloads and images stay in .local.
 *
 * node scripts/kd_ui004_ui.cjs <clone|dev> <before|after|verify>
 *   before  screenshots of the current Overview (above-fold + full + mobile) before the redesign
 *   after   clone: KD-UI-004 Overview checks (KD4_STAGE) + KD-UI-003 regression stages (KD_STAGE)
 *   verify  dev 18069: same checks read-only (no write chain, no typed edit, no wizard)
 */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/kd-ui004');
const target = process.argv[2] || 'clone';
const mode = process.argv[3] || 'before';
assert(['clone', 'dev'].includes(target) && ['before', 'after', 'verify'].includes(mode));
assert(target === 'clone' || mode !== 'after', 'dev runs verify only (read-only)');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_kdui004_20261107');
assert.equal(owner.http_port, 18489);
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
const VIEWPORTS = [[1440, 900], [1920, 1080], [1600, 900], [1280, 800], [768, 1024], [390, 844], [360, 780]];

async function login(browser, key, options = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN', ...options });
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
/** The Overview scrolls inside its own `.o_action` root, so a page screenshot only shows the viewport:
 * grow the viewport to the scroll height for the full capture, then restore it. */
async function shotFull(page, name) {
  const size = page.viewportSize();
  const extra = await page.evaluate(() => {
    const el = document.querySelector('.o_tp_kd_ov');
    return el ? el.scrollHeight - el.clientHeight : 0;
  });
  await page.setViewportSize({ width: size.width, height: Math.min(size.height + Math.max(extra, 0), 9000) });
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(out, `${name}.png`) });
  await page.setViewportSize(size);
  await page.waitForTimeout(300);
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
async function openOverview(page) {
  await page.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);
  await page.locator('.o_tp_kd_ov').first().waitFor({ timeout: 30000 });
  await settle(page);
}

async function before(browser) {
  for (const [w, h] of VIEWPORTS) {
    const context = await login(browser, 'reviewer', { viewport: { width: w, height: h } });
    const page = await context.newPage();
    watch(page);
    await openOverview(page);
    await shot(page, `before-overview-${w}x${h}`);
    if ([1440, 390].includes(w)) await shotFull(page, `before-overview-${w}-full`);
    await context.close();
  }
  results.push('before screenshots captured');
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const ctx = { browser, base, db, login, ok, rpc, watch, settle, shot, shotFull, openList, openFirst, openOverview,
    check, out, errors, target, mode, LEAVES, actors, VIEWPORTS, local };
  try {
    if (mode === 'before') {
      await before(browser);
    } else {
      const failures = [];
      if (process.env.KD4_STAGE !== 'none') {
        try {
          await require('./kd_ui004_ui_overview.cjs')(ctx);
        } catch (error) {
          failures.push(`overview4: ${String(error.message || error).slice(0, 1500)}`);
        }
      }
      if (process.env.KD_STAGE !== 'none') {
        // KD-UI-003 regression (tables, forms, sidebar, roles, responsive, leak, Overview tables/scroll).
        const regression = path.join(out, 'regression');
        fs.mkdirSync(regression, { recursive: true });
        try {
          await require('./kd_ui003_ui_after.cjs')({ ...ctx, out: regression });
        } catch (error) {
          failures.push(`regression: ${String(error.message || error).slice(0, 1500)}`);
        }
      }
      check(`all suites (${failures.length} failed)`, failures.length === 0, failures);
    }
  } finally {
    await browser.close();
  }
  const summary = { target, mode, results, errors: [...new Set(errors)] };
  fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify({ target, mode, passed: results.length, errors: summary.errors.length }));
}
main().catch(error => {
  fs.writeFileSync(path.join(out, 'failure.txt'), String(error.stack || error));
  const summary = { target, mode, results, errors: [...new Set(errors)], failure: String(error.message || error) };
  fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(summary, null, 2));
  console.error('FAIL', String(error.message || error).slice(0, 3000));
  process.exit(1);
});
