/* Clone-only committed source delta, native spreadsheet refresh, then restore the source value. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const local = path.resolve(__dirname, '../.local/native-data003');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_data003_20261102');
assert.equal(owner.http_port, 18149);
assert(owner.rehearsal_passed);
const credentials = JSON.parse(fs.readFileSync(path.join(local, 'actor-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(local, 'actors-clone-apply.json'), 'utf8')).actors;
const fixtures = JSON.parse(fs.readFileSync(path.join(local, 'inventory-clone.json'), 'utf8')).bindings;
const line = fixtures.find(row => row.model === 'account.analytic.line' && row.fields.user_id?.[0] === actors.long);
const dashboard = fixtures.find(row => row.xmlid.endsWith('.dashboard_coordination'));
assert(line && dashboard);
const base = `http://127.0.0.1:${owner.http_port}`;
async function rpc(context, model, method, args, kwargs = {}) {
  const response = await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
    data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } },
  });
  const result = await response.json();
  assert(!result.error, `${model}.${method}: ${result.error?.data?.name}`);
  return result.result;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  let writer, viewer, original;
  let changed = false;
  try {
    writer = await browser.newContext();
    viewer = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    for (const [context, key] of [[writer, 'long'], [viewer, 'nam']]) {
      const response = await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db: owner.database, ...credentials[key] } },
      });
      assert.equal((await response.json()).result?.uid, actors[key]);
    }
    original = (await rpc(writer, 'account.analytic.line', 'read', [[line.id], ['unit_amount']]))[0].unit_amount;
    const page = await viewer.newPage();
    const requests = [];
    page.on('response', async response => {
      if (response.url().includes('/account.analytic.line/')) {
        const body = await response.json().catch(() => null);
        if (body) requests.push({ request: response.request().postDataJSON(), response: body });
      }
    });
    const show = async (expected, file) => {
      requests.length = 0;
      await page.goto(`${base}/odoo/dashboards?dashboard_id=${dashboard.id}`);
      await page.locator('.o_web_client').waitFor();
      await page.waitForTimeout(4500);
      await page.screenshot({ path: path.join(local, file), fullPage: true });
      fs.writeFileSync(path.join(local, file + '.rpc.json'), JSON.stringify(requests, null, 2));
      const projectTotals = requests.filter(item => item.request.params.method === 'formatted_read_group')
        .flatMap(item => item.response.result || [])
        .filter(row => row.project_id && typeof row['unit_amount:sum'] === 'number');
      assert(projectTotals.length, 'Dashboard refresh must fetch native timesheet groups');
      assert.equal(projectTotals.reduce((sum, row) => sum + row['unit_amount:sum'], 0), expected);
    };
    await show(84, 'dashboard-live-before.png');
    await rpc(writer, 'account.analytic.line', 'write', [[line.id], { unit_amount: original + 0.5 }]);
    changed = true;
    await show(84.5, 'dashboard-live-delta.png');
    await rpc(writer, 'account.analytic.line', 'write', [[line.id], { unit_amount: original }]);
    changed = false;
    await show(84, 'dashboard-live-restored.png');
    const report = { target: 'clone', actor: 'long', viewer: 'nam', line: line.id,
      original, delta: 0.5, displayedTotals: [84, 84.5, 84], sourceRestored: true, passed: true };
    fs.writeFileSync(path.join(local, 'dashboard-live-probe.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally {
    if (writer && changed && original !== undefined) {
      await rpc(writer, 'account.analytic.line', 'write', [[line.id], { unit_amount: original }]);
    }
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
