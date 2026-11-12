/* Clone-only revocation and existing-session cache regression. Always restores exact membership. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const local = path.resolve(__dirname, '../.local/dash-ui001');
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_dashui001_20261104');
assert.equal(owner.http_port, 18159);
const secrets = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../.local/dev-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../.local/native-data003/actor-secrets.json'), 'utf8'));
const base = `http://127.0.0.1:${owner.http_port}`;
async function rpc(context, model, method, args, error = false) {
  const body = await (await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
    data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs: {} } },
  })).json();
  assert(error ? body.error : !body.error, `${method}: unexpected access outcome`);
  return body.result;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  let admin, users, assignment, usersChanged = false, assignmentChanged = false;
  try {
    const contexts = {};
    for (const key of ['admin', 'bao', 'nam']) {
      const context = contexts[key] = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const response = await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db: owner.database,
          ...(key === 'admin' ? { login: 'admin', password: secrets.admin } : actors[key]) } },
      });
      assert((await response.json()).result?.uid);
    }
    admin = contexts.admin;
    const page = await contexts.bao.newPage();
    await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
    await page.locator('.tp_metrics').waitFor();
    users = (await rpc(admin, 'spreadsheet.dashboard', 'read', [[6], ['allowed_user_ids']]))[0].allowed_user_ids;
    await rpc(admin, 'spreadsheet.dashboard', 'write', [[6], { allowed_user_ids: [[3, 29]] }]);
    usersChanged = true;
    await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
    await page.getByRole('heading', { name: 'Không đủ quyền', exact: true }).waitFor();
    assert.equal(await page.locator('.tp_metric').count(), 0);
    for (const [method, args] of [['tp_dashboard_report', [[6], {}]], ['tp_dashboard_action', [[6], 'invoices', {}]], ['read', [[6], ['spreadsheet_data']]]]) {
      await rpc(contexts.bao, 'spreadsheet.dashboard', method, args, true);
    }
    await page.screenshot({ path: path.join(local, 'revoked-no-cached-money.png') });
    await rpc(admin, 'spreadsheet.dashboard', 'write', [[6], { allowed_user_ids: [[6, 0, users]] }]);
    usersChanged = false;
    await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
    await page.locator('.tp_metrics').waitFor();
    assignment = (await rpc(admin, 'tp.project.assignment', 'search_read', [[['project_id', '=', 9], ['user_id', '=', 23], ['active', '=', true]], ['id']]))[0];
    assert(assignment);
    await rpc(admin, 'tp.project.assignment', 'write', [[assignment.id], { active: false }]);
    assignmentChanged = true;
    const report = await rpc(contexts.nam, 'spreadsheet.dashboard', 'tp_dashboard_report', [[5], {}]);
    assert(!report.projects.some(project => project.id === 9));
    assert(!report.rows.some(project => project.id === 9));
    await rpc(contexts.nam, 'spreadsheet.dashboard', 'tp_dashboard_report', [[5], { project_id: 9 }], true);
    await rpc(contexts.nam, 'spreadsheet.dashboard', 'tp_dashboard_action', [[5], 'tasks', {}, 9], true);
    await rpc(admin, 'tp.project.assignment', 'write', [[assignment.id], { active: true }]);
    assignmentChanged = false;
    assert((await rpc(contexts.nam, 'spreadsheet.dashboard', 'tp_dashboard_report', [[5], {}])).projects.some(project => project.id === 9));
    fs.writeFileSync(path.join(local, 'security-revocation.json'), JSON.stringify({ passed: true, dashboardRevokeRestored: true, assignmentRevokeRestored: true, staleCardsRemoved: true }));
    console.log('PASS: dashboard/project revocation; RPC, source read, drilldown and existing-session refresh; restored.');
  } finally {
    if (admin && usersChanged) await rpc(admin, 'spreadsheet.dashboard', 'write', [[6], { allowed_user_ids: [[6, 0, users]] }]);
    if (admin && assignmentChanged) await rpc(admin, 'tp.project.assignment', 'write', [[assignment.id], { active: true }]);
    await browser.close();
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
