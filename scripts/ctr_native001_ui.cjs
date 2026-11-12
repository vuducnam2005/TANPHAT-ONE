/* UI-CTR-NATIVE-001a: native Odoo browser acceptance, owned clone and synthetic actors only.
 * Chromium emulation; traces/video disabled so credentials never enter artifacts. */
const { chromium, expect } = require('../frontend/node_modules/@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const folder = path.join(root, '.local/native-stabilize001/ctr-native001');
const owner = JSON.parse(fs.readFileSync(path.join(root, '.local/native-stabilize001/owner.json')));
if (owner.workspace !== root || owner.http_port !== 18169 || owner.database !== 'tp_tanphat_stab001_20261105') throw Error('Foreign test target');
const fixture = JSON.parse(fs.readFileSync(path.join(folder, 'fixture.json')));
const credentials = JSON.parse(fs.readFileSync(path.join(folder, 'credentials.json')));
const base = 'http://127.0.0.1:18169';
const checks = [];
function check(name, ok, detail) {
  checks.push({ name, ok: !!ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`);
  if (!ok) throw Error(name + ': ' + JSON.stringify(detail));
}
async function rpc(context, model, method, args = [], kwargs = {}) {
  const r = await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, { data: {
    jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs },
  }});
  const body = await r.json();
  if (body.error) throw Error(body.error.data?.message || body.error.message);
  return body.result;
}
async function login(browser, role, width=1280) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, isMobile: width < 768,
    hasTouch: width < 768, deviceScaleFactor: 1, locale: 'vi-VN' });
  const body = await (await context.request.post(`${base}/web/session/authenticate`, { data: {
    jsonrpc: '2.0', method: 'call', params: { db: owner.database, ...credentials[role] },
  }})).json();
  if (body.result?.uid !== fixture.users[role]) throw Error('Synthetic login failed');
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
  return { context, page, errors };
}
async function openList(page) {
  await page.goto(`${base}/odoo/action-${fixture.list_action}`);
  await page.locator('.o_list_view').waitFor();
}
async function openRevision(page, id) {
  await page.goto(`${base}/odoo/tp.contract.revision/${id}`);
  await page.locator('.o_form_view').waitFor();
}
async function fill(page, name, value) {
  await page.locator(`[name="${name}"] input, [name="${name}"] textarea`).first().fill(value);
}
async function choose(page, name, text) {
  const input = page.locator(`[name="${name}"] input`).first();
  await input.fill(text);
  await page.getByRole('option').filter({ hasText: text }).first().click();
}
async function confirm(page, text) {
  await page.locator('.modal footer').getByRole('button', { name: text, exact: true }).click();
  await page.locator('.modal').waitFor({ state: 'hidden' });
  await page.locator('.o_form_view').waitFor();
}
async function screen(page, name) {
  // Wait for Odoo's mobile dialog slide and the compositor after viewport/zoom changes.
  await page.waitForTimeout(350);
  if (await page.evaluate(() => devicePixelRatio === 1)) {
    await page.screenshot({ path: path.join(folder, name + '.png'), animations: 'disabled' });
    return;
  }
  const cdp = await page.context().newCDPSession(page);
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
  fs.writeFileSync(path.join(folder, name + '.png'), Buffer.from(shot.data, 'base64'));
  await cdp.detach();
}
async function noOverflow(page, name) {
  // The mobile modal slides in from the right; inspect its settled layout.
  await page.waitForTimeout(500);
  const dimensions = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth,
    dialogs: [...document.querySelectorAll('.modal-dialog, .modal-content')].filter(el => el.getBoundingClientRect().width).map(el => {
      const r = el.getBoundingClientRect(); return { left: r.left, right: r.right };
    }), zoomBlocked: /user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0+)?(\D|$)/.test(document.querySelector('meta[name=viewport]')?.content || '') }));
  check(name, dimensions.scroll <= dimensions.width + 1 && !dimensions.zoomBlocked
    && dimensions.dialogs.every(r => r.left >= -1 && r.right <= dimensions.width + 1), dimensions);
}
async function actualZoom() {
  for (const width of [1280, 1440]) {
    const context = await chromium.launchPersistentContext(path.join(folder, `zoom-profile-${width}-${Date.now()}`), {
      channel: 'chromium', headless: true, viewport: null, args: [`--window-size=${width},900`], locale: 'vi-VN',
    });
    try {
      const settings = await context.newPage();
      await settings.goto('chrome://settings/appearance');
      await settings.locator('#zoomLevel').waitFor();
      const auth = await (await context.request.post(`${base}/web/session/authenticate`, { data: {
        jsonrpc: '2.0', method: 'call', params: { db: owner.database, ...credentials.editor },
      }})).json();
      if (auth.result?.uid !== fixture.users.editor) throw Error('Zoom fixture login failed');
      const page = await context.newPage();
      for (const zoom of [1.25, 1.5]) {
        await settings.locator('#zoomLevel').selectOption(String(zoom));
        await openList(page);
        await page.waitForFunction(expected => Math.abs(devicePixelRatio - expected) < 0.01, zoom);
        await noOverflow(page, `AT-12 real Chromium zoom list ${width}/${zoom}`);
        await screen(page, `zoom-list-${width}-${zoom * 100}`);
        await page.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true }).click();
        await page.locator('.modal [name="project_id"] input').waitFor();
        await noOverflow(page, `AT-12 real Chromium zoom wizard ${width}/${zoom}`);
        await screen(page, `zoom-wizard-${width}-${zoom * 100}`);
      }
    } finally { await context.close(); }
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const editor = await login(browser, 'editor');
    const { page, context } = editor;
    await page.goto(`${base}/odoo/tp-home`);
    await page.locator('.o_tp_web_home_tile').filter({ hasText: 'TP Contracts' }).waitFor();
    check('AT-01 Home TP Contracts tile', true);
    await openList(page);
    await expect(page.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true })).toBeVisible();
    check('AT-01 native list and create entry', true);
    await page.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true }).click();
    await choose(page, 'project_id', 'Cầu An Bình');
    const code = `HD-BROWSER-${Date.now()}`;
    await fill(page, 'code', code);
    await fill(page, 'name', 'Hợp đồng kiểm thử giao diện native');
    await fill(page, 'revision_name', 'Bản gốc qua trình duyệt');
    await choose(page, 'currency_id', 'VND');
    await page.locator('[name="line_ids"] .o_field_x2many_list_row_add button').click();
    await page.locator('[name="line_ids"] [name="scope_key"] input').fill('KS');
    await page.locator('[name="line_ids"] [name="name"] input').fill('Khảo sát hiện trường');
    await page.getByRole('button', { name: 'Lưu nháp', exact: true }).click();
    await page.locator('.modal').waitFor({ state: 'hidden' });
    const contracts = await rpc(context, 'tp.contract', 'search_read', [[['code', '=', code]], ['aggregate_version']]);
    const contractId = contracts[0].id;
    const revisions = await rpc(context, 'tp.contract.revision', 'search_read', [[['contract_id', '=', contractId]], ['review_state']]);
    const revisionId = revisions[0].id;
    check('AT-03 native browser creates draft', revisions[0].review_state === 'draft');
    await page.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fill(page, 'revision_name', 'Bản gốc đã chỉnh sửa');
    await page.getByRole('tab', { name: 'Nhập giá trị mới' }).click();
    await page.locator('[name="amount_input_ids"] .o_field_x2many_list_row_add button').click();
    await fill(page, 'scope_key', 'KS');
    await page.locator('div[name="amount_state"] input').click();
    await page.locator('.o-dropdown--menu').getByText(/^(Confirmed|Đã xác nhận)$/, { exact: true }).click();
    await fill(page, 'value', '7654321');
    await page.locator('div[name="tax_basis"] input').click();
    await page.locator('.o-dropdown--menu').getByText(/^(Excluding Tax|Chưa thuế)$/, { exact: true }).click();
    await confirm(page, 'Lưu nháp');
    check('AT-04 native browser edits metadata and money', true);
    await screen(page, 'draft-desktop');
    await page.getByRole('button', { name: 'Trình rà soát', exact: true }).click();
    await choose(page, 'reviewer_id', 'Kiểm thử hợp đồng — reviewer');
    await confirm(page, 'Trình rà soát');
    check('AT-05 native browser submits', true);
    await screen(page, 'in-review-desktop');

    const reviewer = await login(browser, 'reviewer');
    await openRevision(reviewer.page, revisionId);
    await reviewer.page.getByRole('button', { name: 'Trả lại để chỉnh sửa', exact: true }).click();
    await fill(reviewer.page, 'reason', 'Cần bổ sung mô tả phạm vi khảo sát');
    await confirm(reviewer.page, 'Trả lại để chỉnh sửa');
    check('AT-06 native browser reviewer returns', true);
    await screen(reviewer.page, 'returned-desktop');

    await openRevision(page, revisionId);
    await page.getByRole('button', { name: 'Bắt đầu chỉnh sửa lại', exact: true }).click();
    await fill(page, 'reason', 'Bổ sung theo ý kiến rà soát');
    await confirm(page, 'Bắt đầu chỉnh sửa lại');
    await page.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fill(page, 'revision_name', 'Bản gốc bổ sung phạm vi');
    await confirm(page, 'Lưu nháp');
    await page.getByRole('button', { name: 'Trình rà soát lại', exact: true }).click();
    await choose(page, 'reviewer_id', 'Kiểm thử hợp đồng — reviewer');
    await fill(page, 'fix_summary', 'Đã bổ sung phạm vi theo ý kiến');
    await confirm(page, 'Trình rà soát');
    const submissions = await rpc(context, 'tp.contract.submission', 'search_read', [[['revision_id', '=', revisionId]], ['sequence', 'outcome']]);
    check('AT-05/07 browser rework and resubmit', submissions.length === 2 && submissions.some(s => s.outcome === 'pending'));

    const metadata = await login(browser, 'metadata');
    await openRevision(metadata.page, fixture.revision_id);
    await metadata.page.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await expect(metadata.page.getByRole('tab', { name: 'Nhập giá trị mới' })).toHaveCount(0);
    await fill(metadata.page, 'revision_name', 'Bản gốc sửa metadata từ trình duyệt');
    await confirm(metadata.page, 'Lưu nháp');
    check('AT-10g metadata-only browser flow', true);
    await metadata.page.getByRole('button', { name: 'Chỉnh sửa nháp', exact: true }).click();
    await fill(metadata.page, 'revision_name', 'Tên chưa lưu vì version cũ');
    const concurrent = await rpc(context, 'tp.contract.native.draft', 'create', [{
      contract_id: fixture.contract_id, revision_id: fixture.revision_id, revision_name: 'Thay đổi đồng thời qua actor giả',
    }]);
    await rpc(context, 'tp.contract.native.draft', 'action_confirm', [[concurrent]]);
    await metadata.page.locator('.modal footer').getByRole('button', { name: 'Lưu nháp', exact: true }).click();
    await expect(metadata.page.getByText(/Hồ sơ vừa được cập nhật ở nơi khác/)).toBeVisible();
    await metadata.page.getByRole('button', { name: 'Tải lại hồ sơ', exact: true }).click();
    check('AT-04 stale version tells browser to reload', true);
    const retry = await rpc(context, 'tp.contract.native.draft', 'create', [{
      contract_id: fixture.contract_id, revision_id: fixture.revision_id, revision_name: 'Kiểm thử lặp cùng wizard',
    }]);
    const retry1 = await rpc(context, 'tp.contract.native.draft', 'action_confirm', [[retry]]);
    const retry2 = await rpc(context, 'tp.contract.native.draft', 'action_confirm', [[retry]]);
    check('AT-10e browser RPC retry returns same result', retry1.res_id === retry2.res_id);
    const reader = await login(browser, 'reader');
    await openList(reader.page);
    await expect(reader.page.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true })).toHaveCount(0);
    const documents = await rpc(reader.context, 'tp.contract.document', 'search_read', [
      [['contract_id', '=', fixture.contract_id]], ['file_name'],
    ]);
    check('AT-08 reader cannot see financial filename', documents.length === 1 && documents[0].id === fixture.documents.general);
    for (const kind of ['general', 'financial']) {
      const file = await reader.context.request.get(`${base}/web/content?model=tp.contract.document&id=${fixture.documents[kind]}&field=file&download=true`);
      check(`AT-08 browser binary ${kind}`, kind === 'general' ? file.status() === 200 : file.status() === 403 || file.status() === 404);
    }
    const outsider = await login(browser, 'outsider');
    await openList(outsider.page);
    await expect(outsider.page.getByText('Chưa có hợp đồng trong các dự án bạn được phân công.')).toBeVisible();
    check('AT-01 read-only and outside scope', true);

    for (const width of [360, 390, 768, 1280, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await openList(page);
      await noOverflow(page, `AT-12 list ${width}`);
      await screen(page, `list-${width}`);
      await page.getByRole('button', { name: 'Tạo nháp hợp đồng', exact: true }).click();
      await page.locator('.modal [name="project_id"] input').waitFor();
      await noOverflow(page, `AT-12 wizard ${width}`);
      await screen(page, `wizard-${width}`);
      await page.locator('footer button[special="cancel"]').click();
      await openRevision(page, revisionId);
      await noOverflow(page, `AT-12 revision ${width}`);
      await screen(page, `revision-${width}`);
    }
    await actualZoom();
    for (const [role, actor] of Object.entries({ editor, reviewer, metadata, reader, outsider })) {
      check(`AT-12 console/network ${role}`, actor.errors.length === 0, actor.errors);
    }
    fs.writeFileSync(path.join(folder, 'browser-result.json'), JSON.stringify({ database: owner.database,
      origin: base, engine: 'Chromium emulation', contractId, revisionId, checks }, null, 2));
  } catch (error) {
    let i = 0;
    for (const context of browser.contexts()) for (const page of context.pages()) {
      await screen(page, `failure-${i}`);
      fs.writeFileSync(path.join(folder, `failure-${i++}.txt`), await page.locator('body').innerText());
    }
    fs.writeFileSync(path.join(folder, 'browser-failure.json'), JSON.stringify({ error: error.message, checks }, null, 2));
    throw error;
  } finally { await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
