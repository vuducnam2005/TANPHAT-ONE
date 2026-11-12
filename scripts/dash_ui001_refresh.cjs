/* Clone-only source changes, actual report refresh, and native source restoration. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const local = path.resolve(__dirname, '../.local/dash-ui001');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_dashui001_20261104');
assert.equal(owner.http_port, 18159);
assert(owner.rehearsal_passed);
const credentials = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../.local/native-data003/actor-secrets.json'), 'utf8'));
const fixtures = JSON.parse(fs.readFileSync(path.join(local, 'inspect-clone.json'), 'utf8')).bindings;
const timesheet = fixtures.find(row => row.model === 'account.analytic.line' && row.fields.user_id?.[0] === 21);
const expense = fixtures.find(row => row.model === 'hr.expense' && row.fields.employee_id?.[0] === 17);
assert(timesheet && expense);
const base = `http://127.0.0.1:${owner.http_port}`;
async function rpc(context, model, method, args, kwargs = {}) {
  const body = await (await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
    data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } },
  })).json();
  assert(!body.error, `${model}.${method}: ${body.error?.data?.message}`);
  return body.result;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  const report = [];
  try {
    for (const probe of [
      { writer: 'long', viewer: 'nam', id: 5, model: 'account.analytic.line', record: timesheet.id,
        field: 'unit_amount', delta: 0.5, metric: 'hours' },
      { writer: 'son', viewer: 'bao', id: 6, model: 'hr.expense', record: expense.id,
        field: 'total_amount_currency', delta: 10000, metric: 'draft' },
    ]) {
      const writer = await browser.newContext();
      const viewer = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      for (const [context, key] of [[writer, probe.writer], [viewer, probe.viewer]]) {
        const result = await (await context.request.post(`${base}/web/session/authenticate`, {
          data: { jsonrpc: '2.0', method: 'call', params: { db: owner.database, ...credentials[key] } },
        })).json();
        assert(result.result?.uid);
      }
      const original = (await rpc(writer, probe.model, 'read', [[probe.record], [probe.field]]))[0][probe.field];
      const page = await viewer.newPage();
      const values = [];
      let changed = false;
      const collect = async name => {
        const responsePromise = page.waitForResponse(response => response.url().includes('/tp_dashboard_report'));
        if (name === 'before') await page.goto(`${base}/odoo/dashboards?dashboard_id=${probe.id}`);
        else await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
        const body = await (await responsePromise).json();
        assert(!body.error);
        values.push(body.result.raw[probe.metric]);
        await page.locator('.tp_metrics').waitFor();
        await page.screenshot({ path: path.join(local, `refresh-${probe.id}-${name}.png`) });
      };
      try {
        await collect('before');
        await rpc(writer, probe.model, 'write', [[probe.record], { [probe.field]: original + probe.delta }]);
        changed = true;
        await collect('changed');
        assert.equal(values[1], values[0] + probe.delta);
        await rpc(writer, probe.model, 'write', [[probe.record], { [probe.field]: original }]);
        changed = false;
        await collect('restored');
        assert.equal(values[2], values[0]);
        report.push({ ...probe, original, displayed: values, restored: true });
      } finally {
        if (changed) await rpc(writer, probe.model, 'write', [[probe.record], { [probe.field]: original }]);
        await viewer.close(); await writer.close();
      }
    }
    fs.writeFileSync(path.join(local, 'refresh-results.json'), JSON.stringify({ passed: true, report }, null, 2));
    console.log(JSON.stringify({ passed: true, report }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
