/* Live native UI + RPC assertions. Credentials/screenshots/reports stay in .local. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const local = path.join(root, '.local/native-data003');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
const secrets = JSON.parse(fs.readFileSync(path.join(local, 'actor-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(local, `actors-${target}-apply.json`), 'utf8')).actors;
const fixtures = JSON.parse(fs.readFileSync(path.join(local, `inventory-${target}.json`), 'utf8')).bindings;
function fixture(suffix) {
  const row = fixtures.find(row => row.xmlid.endsWith('.' + suffix));
  assert(row, `Missing fixture ${suffix}`);
  return row;
}
const project = fixture('project_cau');
const work = fixtures.find(row => row.model === 'project.task' && row.fields.project_id?.[0] === project.id
  && row.fields.user_ids.includes(actors.long));
const base = target === 'dev' ? 'http://127.0.0.1:18069' : `http://127.0.0.1:${owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const out = path.join(local, `ui-${target}`);
fs.mkdirSync(out, { recursive: true });
const results = [];
async function rpc(context, model, method, args = [], kwargs = {}) {
  const response = await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
    data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } },
  });
  return response.json();
}
async function okRpc(context, model, method, args, kwargs) {
  const result = await rpc(context, model, method, args, kwargs);
  assert(!result.error, `${model}.${method} failed: ${result.error?.data?.name}`);
  return result.result;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const key of Object.keys(actors)) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      try {
        const login = await context.request.post(`${base}/web/session/authenticate`, {
          data: { jsonrpc: '2.0', method: 'call', params: { db, ...secrets[key] } },
        });
        assert.equal((await login.json()).result?.uid, actors[key], `${key} login`);
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
        if (key === 'khang') {
          for (const [model, ids, fields] of [
            ['project.project', [project.id], ['name']], ['project.task', [work.id], ['name']],
            ['hr.expense', [fixture('expense_00').id], ['total_amount']],
            ['account.move', [fixture('invoice_00').id], ['amount_total']],
          ]) {
            const result = await rpc(context, model, 'read', [ids, fields]);
            assert(result.error, `outside ${model}.read must fail`);
            results.push({ actor: key, test: `RPC denied ${model}`, passed: true });
          }
          const event = fixture('event_02');
          const calendar = await okRpc(context, 'calendar.event', 'read', [[event.id], ['name', 'description']]);
          assert.notEqual(calendar[0].name, event.fields.name);
          assert(!calendar[0].description);
          results.push({ actor: key, test: 'private event details masked', passed: true });
          for (const [model, row, fields] of [
            ['discuss.channel', fixture('channel_survey_design'), ['name']],
            ['spreadsheet.dashboard', fixture('dashboard_finance_draft'), ['spreadsheet_data']],
          ]) {
            assert((await rpc(context, model, 'read', [[row.id], fields])).error);
            results.push({ actor: key, test: `private ${model} RPC denied`, passed: true });
          }
          const employee = fixtures.find(row => row.model === 'hr.employee' && row.fields.user_id?.[0] === actors.khang);
          assert((await rpc(context, 'account.analytic.line', 'create', [{
            name: 'DATA003 forbidden cross-scope RPC', project_id: project.id, task_id: work.id,
            employee_id: employee.id, unit_amount: 0.5,
          }])).error);
          results.push({ actor: key, test: 'cross-scope timesheet create RPC denied', passed: true });
        }
        if (key === 'bao') {
          assert((await rpc(context, 'spreadsheet.dashboard.share', 'action_get_share_url', [{
            dashboard_id: fixture('dashboard_finance_draft').id, name: 'Forbidden public snapshot',
          }])).error);
          results.push({ actor: key, test: 'public financial share RPC denied', passed: true });
        }
        const routes = [{ name: 'home', url: '/odoo/tp-home' }, { name: 'expenses', url: '/odoo/expenses' }];
        if (key === 'long') routes.push({ name: 'tasks', url: '/odoo/all-tasks' }, { name: 'timesheets', url: '/odoo/timesheets' },
                                      { name: 'calendar', url: '/odoo/calendar' }, { name: 'discuss', url: '/odoo/discuss' });
        if (key === 'nam') routes.push({ name: 'crm-link', url: `/odoo/crm/${fixture('lead_00').id}`, expect: 'Dự án thực hiện' },
                                     { name: 'coordination', url: `/odoo/dashboards?dashboard_id=${fixture('dashboard_coordination').id}` });
        if (key === 'bao') routes.push({ name: 'invoices', url: '/odoo/customer-invoices' },
                                     { name: 'finance-dashboard', url: `/odoo/dashboards?dashboard_id=${fixture('dashboard_finance_draft').id}` });
        for (const width of [1440, 375]) {
          await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
          for (const route of routes) {
            const before = errors.length;
            await page.goto(base + route.url, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_web_client').waitFor({ timeout: 30000 });
            await page.locator('.o_action_manager .o_action, .o_action_manager .o_view_controller, .o_home_menu, .o_tp_web_home, .o-mail-Discuss').first().waitFor({ timeout: 30000 });
            if (route.name.includes('dashboard') || route.name === 'coordination') {
              await page.waitForTimeout(4000);
            } else {
              await page.waitForTimeout(1000);
            }
            assert.equal(errors.length, before, `${key}/${route.name}/${width} console: ${errors.slice(before).join(';')}`);
            const text = await page.locator('body').innerText();
            assert(!text.includes('Odoo Client Error'), 'No client error');
            if (route.expect) assert(text.includes(route.expect), `${route.name} expected label`);
            if (route.name === 'home') {
              assert(text.includes('TANPHAT ONE'));
              if (key === 'khang') assert(!text.includes('Hóa đơn'));
            }
            const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
            assert(!overflow, `${key}/${route.name}/${width} horizontal overflow`);
            await page.screenshot({ path: path.join(out, `${key}-${route.name}-${width}.png`), fullPage: true });
            results.push({ actor: key, route: route.name, width, passed: true, consoleErrors: 0, overflow });
          }
        }
        if (['long', 'nam', 'bao'].includes(key)) {
          await page.setViewportSize({ width: 1440, height: 1000 });
          await page.goto(base + '/odoo/expenses', { waitUntil: 'domcontentloaded' });
          await page.locator('.o_view_controller').first().waitFor({ timeout: 30000 });
          for (const zoom of [1.25, 1.5]) {
            await page.evaluate(z => { document.body.style.zoom = z; }, zoom);
            await page.waitForTimeout(500);
            assert(!(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)));
            await page.screenshot({ path: path.join(out, `${key}-expenses-zoom-${zoom}.png`), fullPage: true });
            results.push({ actor: key, route: 'expenses', width: 1440, zoom, passed: true });
          }
        }
      } finally { await context.close(); }
      fs.writeFileSync(path.join(local, `ui-${target}.json`), JSON.stringify(results, null, 2));
      console.log(`${target} UI ${key}: ${results.length} cumulative checks passed`);
    }
  } finally {
    fs.writeFileSync(path.join(local, `ui-${target}.json`), JSON.stringify(results, null, 2));
    await browser.close();
  }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
