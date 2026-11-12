/* Live DASH-UI-001 verification; credentials, RPC evidence and images remain private. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/dash-ui001');
const target = process.argv[2] || 'clone';
const before = process.argv.includes('--before');
assert(['clone', 'dev'].includes(target));
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_dashui001_20261104');
assert.equal(owner.http_port, 18159);
assert(owner.rehearsal_passed);
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/native-data003/actor-secrets.json'), 'utf8'));
const baseline = JSON.parse(fs.readFileSync(path.join(local, `inspect-${target}.json`), 'utf8'));
const out = path.join(process.env.TP_DASH_EVIDENCE_DIR || local, `ui-${target}${before ? '-before' : ''}`);
fs.mkdirSync(out, { recursive: true });
const results = [];
function check(name, condition) { assert(condition, name); results.push(name); }
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
async function login(browser, key, options = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, ...options });
  const credentials = key === 'admin' ? { login: 'admin', password: secrets.admin } : actors[key];
  const response = await context.request.post(`${base}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db, ...credentials } },
  });
  assert((await response.json()).result?.uid, `${key} login failed`);
  return context;
}
async function run() {
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const context = await login(browser, 'admin');
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    if (before) {
      for (const id of [6, 5]) {
        await page.goto(`${base}/odoo/dashboards?dashboard_id=${id}`);
        await page.locator('.o-spreadsheet').waitFor();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(out, `${id}-1440.png`) });
      }
    } else {
      const invoiceIds = baseline.invoices.map(r => r.id);
      const expenseIds = baseline.expenses.map(r => r.id);
      const expenses = await ok(context, 'hr.expense', 'search_read', [[['id', 'in', expenseIds], ['state', 'in', ['draft', 'submitted', 'approved']]], ['id', 'state', 'total_amount', 'date']]);
      const truth = Object.fromEntries(['draft', 'submitted', 'approved'].map(s => [s, expenses.filter(r => r.state === s).reduce((sum, r) => sum + r.total_amount, 0)]));
      const data = await ok(context, 'spreadsheet.dashboard', 'tp_dashboard_report', [[6], {}]);
      for (const state of Object.keys(truth)) assert.equal(data.raw[state], truth[state]);
      assert.equal(data.raw.invoice_count, invoiceIds.length);
      assert.equal(data.raw.expense_count, expenses.length);
      fs.writeFileSync(path.join(out, 'source-report.json'), JSON.stringify({ truth, data }, null, 2));
      results.push('source current state totals equal report');
      for (const [id, source] of [[6, 'invoices'], [5, 'tasks']]) {
        const report = await ok(context, 'spreadsheet.dashboard', 'tp_dashboard_report', [[id], {}]);
        for (const project of report.projects) {
          const filtered = await ok(context, 'spreadsheet.dashboard', 'tp_dashboard_report', [[id], { project_id: project.id }]);
          assert.equal(filtered.rows.length, 1);
          const action = await ok(context, 'spreadsheet.dashboard', 'tp_dashboard_action', [[id], source, { project_id: project.id }]);
          const records = await ok(context, action.res_model, 'search_read', [action.domain, ['id']]);
          assert.equal(records.length, filtered.raw[id === 6 ? 'invoice_count' : 'tasks']);
        }
        results.push(`${id} project report/table/drilldown`);
        const empty = await ok(context, 'spreadsheet.dashboard', 'tp_dashboard_report', [[id], { date_from: '2100-01-01' }]);
        assert(empty.empty);
        results.push(`${id} empty date filter`);
      }
      for (const id of [6, 5]) {
        for (const width of [1440, 1280, 390]) {
          await page.setViewportSize({ width, height: 1000 });
          await page.goto(`${base}/odoo/dashboards?dashboard_id=${id}`);
          try { await page.locator('.tp_metrics').waitFor(); } catch (error) {
            await page.screenshot({ path: path.join(out, 'load-failure.png') });
            console.error(JSON.stringify({ errors, text: (await page.locator('body').innerText()).slice(-4000) }));
            throw error;
          }
          check(`${id}/${width} internal share hidden`, !(await page.getByRole('button', { name: /Share|Chia sẻ/ }).count()));
          assert.equal(await page.locator('.tp_metric').count(), 4);
          assert.equal(await page.locator('.tp_chart').count(), 2);
          const overflow = await page.evaluate(() => ({ page: document.documentElement.scrollWidth > innerWidth,
            content: [...document.querySelectorAll('.tp_connected_dashboard,.o_content')].some(e => e.scrollWidth > e.clientWidth + 1) }));
          check(`${id}/${width} no page overflow`, !overflow.page && !overflow.content);
          await page.screenshot({ path: path.join(out, `${id}-${width}.png`), fullPage: true });
          if (width === 1440) {
            await page.locator('.tp_details').scrollIntoViewIfNeeded();
            await page.screenshot({ path: path.join(out, `${id}-table-1440.png`) });
          }
        }
      }
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
      await page.locator('.tp_metrics').waitFor();
      await page.getByLabel('Dự án', { exact: true }).selectOption('8');
      await page.waitForFunction(() => document.querySelectorAll('.tp_details tbody tr').length === 1);
      assert.equal(await page.locator('tbody tr').count(), 1);
      check('project filter visible', (await page.locator('.tp_metrics').innerText()).includes('310.000.000'));
      await page.getByLabel('Từ ngày', { exact: true }).fill('2100-01-01');
      await page.locator('.tp_empty').waitFor();
      results.push('UI project/date/empty');
      const resetReport = page.waitForResponse(response => response.url().includes('/tp_dashboard_report'));
      await page.getByRole('button', { name: 'Xóa bộ lọc' }).click();
      await resetReport;
      await page.locator('.tp_metrics').waitFor();
      await page.waitForFunction(() => !document.querySelector('.tp_refresh').disabled);
      await page.getByRole('button', { name: 'Làm mới', exact: true }).focus();
      assert.equal(await page.evaluate(() => document.activeElement?.textContent?.trim()), 'Làm mới');
      await page.keyboard.press('Enter');
      await page.locator('.tp_metrics').waitFor();
      results.push('keyboard refresh');
      // Inject only transport responses, never turn permission/network failures into zero.
      for (const mode of ['network', 'permission']) {
        await page.route('**/web/dataset/call_kw/spreadsheet.dashboard/tp_dashboard_report', route => mode === 'network'
          ? route.abort() : route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ jsonrpc: '2.0', error: { code: 200, message: 'Odoo Server Error', data: { name: 'odoo.exceptions.AccessError', message: 'Forbidden test source', arguments: ['Forbidden test source'] } } }) }));
        await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
        await page.locator('.tp_error').waitFor();
        assert.equal(await page.locator('.tp_metric').count(), 0);
        await page.unroute('**/web/dataset/call_kw/spreadsheet.dashboard/tp_dashboard_report');
        await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
        await page.locator('.tp_metrics').waitFor();
        results.push(`${mode} error retry no zero`);
      }
      await page.locator('.tp_metric').first().click();
      await page.locator('.o_list_view').waitFor();
      assert.equal(await page.locator('.o_data_row').count(), 4);
      results.push('UI KPI opens actual four source invoices');
      await page.goBack();
      await page.locator('.tp_metrics').waitFor();
      await page.getByRole('button', { name: 'Thu gọn danh sách', exact: true }).click();
      await page.getByRole('button', { name: 'Mở danh sách bảng tổng hợp', exact: true }).click();
      await page.getByRole('button', { name: 'Điều phối dự án', exact: true }).focus();
      await page.keyboard.press('Enter');
      await page.getByRole('heading', { name: 'Điều phối dự án', exact: true }).waitFor();
      results.push('sidebar collapse/expand and keyboard selection');
      for (const [key, allowed] of [['nam', [5]], ['khoa', [5]], ['bao', [6]], ['khang', []]]) {
        const actor = await login(browser, key);
        for (const id of [5, 6]) {
          const response = await rpc(actor, 'spreadsheet.dashboard', 'tp_dashboard_report', [[id], {}]);
          check(`${key}/${id} report access`, allowed.includes(id) ? !!response.result : !!response.error);
          const action = await rpc(actor, 'spreadsheet.dashboard', 'tp_dashboard_action', [[id], id === 6 ? 'invoices' : 'tasks', {}]);
          check(`${key}/${id} drilldown access`, allowed.includes(id) ? !!action.result : !!action.error);
          const raw = await rpc(actor, 'spreadsheet.dashboard', 'read', [[id], ['spreadsheet_data']]);
          check(`${key}/${id} raw access`, allowed.includes(id) ? !!raw.result : !!raw.error);
          const share = await rpc(actor, 'spreadsheet.dashboard.share', 'action_get_share_url', [{ dashboard_id: id, name: 'Forbidden fictional share' }]);
          check(`${key}/${id} public share denied`, !!share.error);
        }
        if (allowed.length) {
          const ap = await actor.newPage();
          await ap.goto(`${base}/odoo/dashboards?dashboard_id=${allowed[0]}`);
          await ap.locator('.tp_metrics').waitFor();
          check(`${key} UI access`, !(await ap.locator('.tp_error').count()));
          await ap.screenshot({ path: path.join(out, `${key}-1440.png`) });
        }
        await actor.close();
      }
      await page.goto(`${base}/odoo/dashboards?dashboard_id=1`);
      await page.getByRole('button', { name: /Share|Chia sẻ/ }).waitFor();
      check('standard dashboard share retained', !(await page.locator('.tp_connected_dashboard').count()));
      // Failed network injection is expected to log one network error.
      const unexpected = errors.filter(e => !/ERR_FAILED|Failed to fetch|Failed to load resource/.test(e));
      assert.deepEqual(unexpected, []);
    }
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ target, before, passed: true, assertions: results, errors }, null, 2));
    console.log(JSON.stringify({ target, before, passed: results.length, consoleErrors: errors.length }));
    await context.close();
  } finally { await browser.close(); }
}
run().catch(error => { console.error(error.stack); process.exitCode = 1; });
