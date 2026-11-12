/* MOBILE-001 touch-flow acceptance on native Odoo (Chromium emulation, not a real device).
 * clone: may create fake timesheet/expense rows as the actor's own permissions allow; dev: read-only flows only.
 * Credentials and evidence stay in .local/mobile001; passwords are never printed. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const WRITE = target === 'clone';
const owner = JSON.parse(fs.readFileSync(path.join(root, '.local/dash-ui001/owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_dashui001_20261104');
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/native-data003/actor-secrets.json'), 'utf8'));
const out = path.join(root, '.local/mobile001', `flows-${target}`);
fs.mkdirSync(out, { recursive: true });
const stamp = new Date().toISOString().replace(/\D/g, '').slice(0, 14);
const results = [];

function credentials(key) {
  return key === 'admin' ? { login: 'admin', password: secrets.admin } : actors[key];
}

async function session(browser, key, viewport, extra = {}) {
  const isMobile = viewport.width < 768 || Boolean(extra.mobile);
  const context = await browser.newContext({ viewport, isMobile, hasTouch: isMobile, deviceScaleFactor: 1, locale: 'vi-VN' });
  const response = await context.request.post(`${base}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db, ...credentials(key) } },
  });
  const uid = (await response.json()).result?.uid;
  assert(uid, `${key} login failed`);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  return { context, page, errors, uid };
}

async function rpc(page, model, method, args, kwargs = {}) {
  const response = await page.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
    data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } },
  });
  return response.json();
}

async function shot(page, name, full = false) {
  if (full) {
    // Grow the emulated screen to the scroll container height so the whole board is in one image.
    const size = page.viewportSize();
    const height = await page.evaluate(() => {
      const el = document.querySelector('.tp_connected_dashboard, .o_tp_web_home, .o_content');
      return el ? el.scrollHeight + el.getBoundingClientRect().top + 8 : document.documentElement.scrollHeight;
    });
    await page.setViewportSize({ width: size.width, height: Math.min(Math.ceil(height), 6000) });
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(out, `${name}.png`) });
    await page.setViewportSize(size);
    await page.waitForTimeout(200);
  } else {
    await page.screenshot({ path: path.join(out, `${name}.png`) });
  }
}

async function step(name, fn) {
  const row = { name };
  try {
    row.detail = await fn();
    row.passed = true;
  } catch (error) {
    row.passed = false;
    row.error = error.message.split('\n').slice(0, 3).join(' ');
  }
  results.push(row);
  console.log(JSON.stringify({ step: name, passed: row.passed, error: row.error }));
}

/* Facts about the current layout; screenshots are still viewed by a human/agent. */
function layout() {
  const vw = innerWidth;
  const overflowing = [...document.querySelectorAll('body *')].filter(el => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height || r.right <= vw + 1) return false;
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(p).overflowX)) return p.getBoundingClientRect().right > vw + 1;
    }
    return true;
  }).length;
  return { innerWidth: vw, pageOverflow: document.documentElement.scrollWidth > vw, overflowing };
}

async function noOverflow(page) {
  const facts = await page.evaluate(layout);
  assert(!facts.pageOverflow && !facts.overflowing, JSON.stringify(facts));
  return facts;
}

async function box(locator) {
  const b = await locator.boundingBox();
  assert(b, 'element not visible');
  return { w: Math.round(b.width), h: Math.round(b.height), x: Math.round(b.x), y: Math.round(b.y) };
}

/* Native many2one on phones opens a full-screen select dialog (desktop: autocomplete). Some fields
 * (timesheet project) start that dialog with the native "My Favorites" facet; remove it like a user would. */
async function pickMany2one(page, scope, field) {
  await scope.locator(`.o_field_widget[name=${field}] input`).click();
  const modal = page.locator('.modal').last();
  await modal.waitFor();
  await page.waitForTimeout(1500);
  const records = modal.locator('.o_kanban_record:not(.o_kanban_ghost), .o_data_row');
  let removed = [];
  if (!(await records.count())) {
    await modal.locator('.o_control_panel_navigation button:has([data-icon=search])').first().click();
    await page.waitForTimeout(600);
    removed = await page.locator('.o_searchview_facet').allInnerTexts();
    await page.locator('.o_searchview_facet .o_facet_remove').first().click();
    await page.waitForTimeout(1500);
  }
  const dialog = await box(modal.locator('.modal-content').first());
  const text = (await records.first().innerText()).split('\n')[0];
  await records.first().click();
  await modal.waitFor({ state: 'detached', timeout: 8000 }).catch(() => {});
  return { text: text.slice(0, 40), removedFacets: removed, dialog };
}

async function openDashboard(page, id) {
  await page.goto(`${base}/odoo/dashboards?dashboard_id=${id}`);
  await page.locator('.tp_metrics').waitFor({ timeout: 30000 });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const phone = { width: 390, height: 844 };
  try {
    // ---------------- A. Home, search, open app, back; drawer ----------------
    {
      const { context, page, errors } = await session(browser, 'admin', phone);
      await step('A1 home phone: 2 columns, search, open TP Projects, Home button back', async () => {
        await page.goto(`${base}/odoo/tp-home`);
        await page.locator('.o_tp_web_home_tile').first().waitFor();
        const columns = await page.evaluate(() => getComputedStyle(document.querySelector('.o_tp_web_home_grid')).gridTemplateColumns.split(' ').length);
        assert.equal(columns, 2);
        const tile = await box(page.locator('.o_tp_web_home_tile').first());
        assert(tile.h >= 44 && tile.w >= 140, JSON.stringify(tile));
        await noOverflow(page);
        await shot(page, 'A1-home-390');
        const input = page.locator('.o_tp_web_home_search_input');
        const fontSize = await input.evaluate(el => parseFloat(getComputedStyle(el).fontSize));
        assert(fontSize >= 16, 'search font ' + fontSize);
        await input.fill('du an');
        await page.waitForTimeout(300);
        const labels = await page.locator('.o_tp_web_home_label').allInnerTexts();
        assert(labels.some(l => /TP Projects|Project/.test(l)), labels.join('|'));
        const clear = await box(page.locator('.o_tp_web_home_search_clear'));
        assert(clear.w >= 44 && clear.h >= 44, JSON.stringify(clear));
        await shot(page, 'A1-home-search-390');
        await page.locator('.o_tp_web_home_tile', { hasText: 'TP Projects' }).click();
        await page.locator('.o_data_row, .o_kanban_record, .o_view_nocontent').first().waitFor();
        const home = page.locator('.o_tp_web_home_button');
        const homeBox = await box(home);
        assert(homeBox.w >= 44 && homeBox.h >= 44, JSON.stringify(homeBox));
        await home.click();
        await page.locator('.o_tp_web_home_tile').first().waitFor();
        return { columns, tile, fontSize, labels: labels.length, clear, homeBox, url: page.url().replace(base, '') };
      });
      await step('A2 native drawer: opens, Escape closes, focus returns', async () => {
        const toggle = page.locator('.o_mobile_menu_toggle');
        await toggle.click();
        await page.locator('.o_burger_menu').waitFor();
        await shot(page, 'A2-drawer-390');
        await page.waitForTimeout(300);
        const inside = await page.evaluate(() => document.activeElement?.classList.contains('o_sidebar_close'));
        assert(inside, 'focus not moved into drawer');
        await page.keyboard.press('Escape');
        await page.locator('.o_burger_menu').waitFor({ state: 'hidden', timeout: 5000 });
        await page.waitForTimeout(300);
        const back = await page.evaluate(() => document.activeElement?.classList.contains('o_mobile_menu_toggle'));
        assert(back, 'focus not returned to drawer toggle');
        await page.locator('.o_mobile_menu_toggle').click();
        await page.locator('.o_burger_menu').waitFor();
        await page.waitForTimeout(300);
        await page.locator('.modal-backdrop').click({ position: { x: 10, y: 400 } });
        await page.locator('.o_burger_menu').waitFor({ state: 'hidden', timeout: 5000 });
        return { focusInside: inside, focusReturned: back, outsideTapCloses: true };
      });
      await step('A3 home landscape 844x390 and tablet 768', async () => {
        await page.setViewportSize({ width: 844, height: 390 });
        await page.waitForTimeout(400);
        const landscape = await noOverflow(page);
        const columns = await page.evaluate(() => getComputedStyle(document.querySelector('.o_tp_web_home_grid')).gridTemplateColumns.split(' ').length);
        await shot(page, 'A3-home-landscape-844');
        await page.setViewportSize(phone);
        return { landscape, columns };
      });
      assert.deepEqual(errors, []);
      await context.close();
    }
    {
      const { context, page } = await session(browser, 'admin', { width: 768, height: 1024 });
      await step('A4 home tablet 768: icon grid kept', async () => {
        await page.goto(`${base}/odoo/tp-home`);
        await page.locator('.o_tp_web_home_tile').first().waitFor();
        const columns = await page.evaluate(() => getComputedStyle(document.querySelector('.o_tp_web_home_grid')).gridTemplateColumns.split(' ').length);
        assert.equal(columns, 4);
        await noOverflow(page);
        await shot(page, 'A4-home-768');
        return { columns };
      });
      await context.close();
    }

    // ---------------- B. Dashboard on phone ----------------
    {
      const { context, page, errors } = await session(browser, 'admin', phone);
      const actionCalls = [];
      page.on('request', r => { if (r.url().includes('tp_dashboard_action')) actionCalls.push(r.url()); });
      await step('B1 finance dashboard 390: folded filters, metrics 1 column, no overflow', async () => {
        await openDashboard(page, 6);
        const toggle = page.locator('.tp_filter_toggle');
        assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
        assert(!(await page.locator('.tp_filters').isVisible()));
        const toggleBox = await box(toggle);
        assert(toggleBox.h >= 44);
        const refresh = await box(page.locator('.tp_refresh'));
        assert(refresh.h >= 44);
        const metricColumns = await page.evaluate(() => getComputedStyle(document.querySelector('.tp_metrics')).gridTemplateColumns.split(' ').length);
        assert.equal(metricColumns, 1);
        const values = await page.locator('.tp_metric strong').evaluateAll(els => els.map(el => ({ text: el.innerText, lines: Math.round(el.getBoundingClientRect().height / parseFloat(getComputedStyle(el).lineHeight)) })));
        assert(values.every(v => v.lines <= 1), JSON.stringify(values));
        await noOverflow(page);
        await shot(page, 'B1-finance-390');
        // Resizing (rotation, full-page capture) must not refetch the report.
        let reports = 0;
        const count = request => { if (request.url().includes('tp_dashboard_report')) reports += 1; };
        page.on('request', count);
        await shot(page, 'B1-finance-390-full', true);
        await page.setViewportSize({ width: 844, height: 390 });
        await page.waitForTimeout(400);
        await page.setViewportSize(phone);
        await page.waitForTimeout(400);
        page.off('request', count);
        assert.equal(reports, 0, 'report refetched on resize');
        return { toggleBox, refresh, metricColumns, values, reportsOnResize: reports };
      });
      await step('B2 filter disclosure: open, choose project, count, summary, clear', async () => {
        await page.locator('.tp_connected_dashboard[aria-busy=false] .tp_metrics').waitFor();
        await page.waitForTimeout(500);
        await page.locator('.tp_filter_toggle').click();
        await page.waitForTimeout(300);
        assert.equal(await page.locator('.tp_filter_toggle').getAttribute('aria-expanded'), 'true');
        const select = page.locator('.tp_filters select');
        const selectBox = await box(select);
        const font = await select.evaluate(el => parseFloat(getComputedStyle(el).fontSize));
        assert(selectBox.h >= 44 && font >= 16, JSON.stringify({ selectBox, font }));
        const dates = await page.locator('.tp_filters input[type=date]').evaluateAll(els => els.map(el => ({ h: el.getBoundingClientRect().height, f: parseFloat(getComputedStyle(el).fontSize), label: el.closest('label')?.innerText.trim() })));
        assert(dates.every(d => d.h >= 44 && d.f >= 16 && d.label), JSON.stringify(dates));
        await shot(page, 'B2-filters-open-390');
        const option = await select.locator('option').nth(1).getAttribute('value');
        await select.selectOption(option);
        await page.locator('.tp_metrics').waitFor();
        await page.waitForTimeout(300);
        const count = await page.locator('.tp_filter_count').innerText();
        const summary = await page.locator('.tp_filter_summary').innerText();
        assert.equal(count.trim(), '1');
        assert(!/Tất cả dự án/.test(summary), summary);
        await page.locator('.tp_filter_toggle').click();
        await shot(page, 'B2-filter-active-closed-390');
        await page.locator('.tp_filter_clear').click();
        await page.locator('.tp_metrics').waitFor();
        await page.waitForTimeout(300);
        assert.equal(await page.locator('.tp_filter_count').count(), 0);
        return { selectBox, font, dates, count, summary };
      });
      await step('B3 refresh keeps state; table sticky first column, 44px cells, hint', async () => {
        const before = await page.locator('.tp_data_meta').innerText();
        const reloaded = page.waitForResponse(r => r.url().includes('tp_dashboard_report'));
        await page.locator('.tp_refresh').click();
        await reloaded;
        await page.locator('.tp_connected_dashboard[aria-busy=false] .tp_metrics').waitFor();
        await page.waitForTimeout(300);
        const scroll = page.locator('.tp_table_scroll');
        await scroll.scrollIntoViewIfNeeded();
        const hint = await page.locator('.tp_table_hint').isVisible();
        assert(hint, 'table hint hidden');
        const cell = await box(page.locator('.tp_details td button').first());
        assert(cell.h >= 44 && cell.w >= 44, JSON.stringify(cell));
        const geometry = await scroll.evaluate(el => {
          const first = el.querySelector('tbody th');
          const before = first.getBoundingClientRect().left;
          el.scrollLeft = el.scrollWidth;
          const after = first.getBoundingClientRect().left;
          return { scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, scrolled: el.scrollLeft, before: Math.round(before), after: Math.round(after) };
        });
        assert(Math.abs(geometry.before - geometry.after) <= 1, 'first column moved ' + JSON.stringify(geometry));
        await page.waitForTimeout(200);
        await shot(page, 'B3-table-scrolled-390');
        await scroll.evaluate(el => { el.scrollLeft = 0; });
        await noOverflow(page);
        return { before, hint, cell, geometry };
      });
      await step('B4 double tap on metric opens source once; back returns to dashboard', async () => {
        await page.locator('.tp_connected_dashboard').evaluate(el => { el.scrollTop = 0; });
        actionCalls.length = 0;
        const metric = page.locator('.tp_metric:not([disabled])').first();
        await metric.dblclick();
        await page.locator('.o_list_view, .o_kanban_view, .o_form_view').first().waitFor({ timeout: 20000 });
        await page.waitForTimeout(800);
        const calls = actionCalls.length;
        assert.equal(calls, 1, 'tp_dashboard_action calls ' + calls);
        await shot(page, 'B4-source-390');
        await page.goBack();
        await page.locator('.tp_metrics').waitFor({ timeout: 20000 });
        return { calls };
      });
      await step('B5 offline (native offline mode) and failed load: error with retry, then recovers', async () => {
        await page.locator('.tp_connected_dashboard[aria-busy=false] .tp_metrics').waitFor();
        // Device offline: native Odoo greys out buttons (o_disabled_offline) until the server answers again.
        await context.setOffline(true);
        try {
          await page.locator('.tp_refresh.o_disabled_offline').waitFor({ timeout: 10000 });
          await shot(page, 'B5-device-offline-390');
        } finally {
          await context.setOffline(false);
        }
        await page.locator('.tp_refresh:not(.o_disabled_offline)').waitFor({ timeout: 30000 });
        // Server/network failure of the report request itself: TANPHAT error block with a 44px retry.
        await page.route('**/tp_dashboard_report', route => route.abort('connectionreset'));
        try {
          await page.locator('.tp_refresh').click();
          await page.locator('.tp_error').waitFor({ timeout: 20000 });
        } finally {
          await page.unroute('**/tp_dashboard_report');
        }
        const message = await page.locator('.tp_error p').innerText();
        const retry = await box(page.locator('.tp_error .btn'));
        assert(retry.h >= 44, JSON.stringify(retry));
        await shot(page, 'B5-load-error-390');
        await page.locator('.tp_error .btn:not(.o_disabled_offline)').waitFor({ timeout: 30000 });
        await page.locator('.tp_error .btn').click();
        await page.locator('.tp_connected_dashboard[aria-busy=false] .tp_metrics').waitFor({ timeout: 20000 });
        const text = await page.locator('.tp_metric strong').first().innerText();
        return { message, retry, text };
      });
      await step('B6 mobile dashboard picker: full width, focus, Escape, keyboard open, switch board', async () => {
        const toggle = page.locator('.tp_mobile_dashboard_toggle');
        const toggleBox = await box(toggle);
        await toggle.click();
        const panel = page.locator('.tp_mobile_dashboard_panel');
        await panel.waitFor();
        await page.waitForTimeout(200);
        const panelBox = await box(panel);
        assert(panelBox.w >= phone.width - 1, JSON.stringify(panelBox));
        const focused = await page.evaluate(() => document.activeElement?.classList.contains('o_mobile_search_button'));
        assert(focused, 'back button not focused');
        const items = await panel.locator('.o_search_panel_category_value').evaluateAll(els => els.map(el => ({ h: Math.round(el.getBoundingClientRect().height), text: el.innerText.trim(), clipped: el.querySelector('.o_search_panel_label_title').scrollWidth > el.querySelector('.o_search_panel_label_title').clientWidth + 1 })));
        assert(items.every(i => i.h >= 44 && !i.clipped), JSON.stringify(items));
        await shot(page, 'B6-picker-390');
        await page.keyboard.press('Escape');
        await panel.waitFor({ state: 'detached', timeout: 5000 });
        await page.waitForTimeout(200);
        const back = await page.evaluate(() => document.activeElement?.classList.contains('tp_mobile_dashboard_toggle'));
        assert(back, 'focus not returned to toggle');
        await page.keyboard.press('Enter');
        await panel.waitFor();
        await panel.locator('.o_search_panel_category_value', { hasText: 'Điều phối' }).first().click();
        await page.locator('.tp_connected_dashboard h1', { hasText: 'Điều phối' }).waitFor({ timeout: 20000 });
        await page.locator('.tp_metrics').waitFor();
        await noOverflow(page);
        await shot(page, 'B6-coord-390-full', true);
        return { toggleBox, panelBox, items };
      });
      await step('B7 dashboards at 360, landscape 844x390 and 768', async () => {
        const facts = {};
        for (const vp of [{ width: 360, height: 800 }, { width: 844, height: 390 }]) {
          await page.setViewportSize(vp);
          await page.waitForTimeout(400);
          facts[vp.width] = await noOverflow(page);
          await shot(page, `B7-coord-${vp.width}`);
        }
        await page.setViewportSize(phone);
        return facts;
      });
      assert.deepEqual(errors, []);
      await context.close();
    }
    for (const vp of [{ width: 768, height: 1024 }, { width: 1280, height: 800 }, { width: 1440, height: 900 }]) {
      const { context, page, errors } = await session(browser, 'admin', vp);
      await step(`B8 finance dashboard ${vp.width}: metrics readable, no overflow`, async () => {
        await openDashboard(page, 6);
        const metricColumns = await page.evaluate(() => getComputedStyle(document.querySelector('.tp_metrics')).gridTemplateColumns.split(' ').length);
        const values = await page.locator('.tp_metric strong').evaluateAll(els => els.map(el => ({ text: el.innerText, lines: Math.round(el.getBoundingClientRect().height / parseFloat(getComputedStyle(el).lineHeight)) })));
        assert(values.every(v => v.lines <= 1), JSON.stringify(values));
        assert(await page.locator('.tp_filters').isVisible(), 'desktop filters must stay open');
        assert(!(await page.locator('.tp_filter_toggle').isVisible()), 'desktop has no filter toggle');
        await noOverflow(page);
        await shot(page, `B8-finance-${vp.width}`);
        return { metricColumns, values };
      });
      assert.deepEqual(errors, []);
      await context.close();
    }

    // ---------------- C. Project -> tasks -> task (Long, phone) ----------------
    {
      const { context, page, errors, uid } = await session(browser, 'long', phone);
      await step('C1 Long: Project -> tasks -> task detail -> back', async () => {
        await page.goto(`${base}/odoo/project`);
        await page.locator('.o_kanban_record').first().waitFor();
        await noOverflow(page);
        await shot(page, 'C1-projects-390');
        await page.locator('.o_kanban_record').first().click();
        await page.locator('.o_kanban_record, .o_data_row, .o_view_nocontent').first().waitFor();
        await page.waitForTimeout(600);
        await shot(page, 'C1-tasks-390');
        const record = page.locator('.o_kanban_record:not(.o_kanban_ghost)').first();
        await record.click();
        await page.locator('.o_form_view').waitFor();
        await page.waitForTimeout(600);
        await noOverflow(page);
        await shot(page, 'C1-task-form-390');
        const title = await page.locator('.o_form_view .o_field_widget[name=name] input, .o_form_view .o_field_widget[name=name] textarea, .o_form_view .o_field_widget[name=name] span').first().evaluate(el => el.value || el.innerText).catch(() => '');
        await page.goBack();
        await page.locator('.o_kanban_record, .o_data_row').first().waitFor();
        return { title: title.slice(0, 40) };
      });
      await step('C2 Long: timesheet form, error near required field, save fake hours (clone only)', async () => {
        await page.goto(`${base}/odoo/timesheets`);
        await page.locator('.o_control_panel').waitFor();
        await page.waitForTimeout(800);
        await noOverflow(page);
        await shot(page, 'C2-timesheets-390');
        if (!WRITE) return { skipped: 'dev is read-only' };
        await page.locator('.o_control_panel button:has-text("Mới")').first().click();
        const form = page.locator('.o_form_view').first();
        await form.waitFor();
        await page.waitForTimeout(600);
        // Native validation: unparsable hours (and the project, when native has not prefilled the last one used).
        // The error must sit on the field itself and nothing may be saved.
        const prefilled = await form.locator('.o_field_widget[name=project_id] input').inputValue();
        await form.locator('.o_field_widget[name=unit_amount] input').fill('abc');
        await page.locator('.o_form_button_save:visible').first().click();
        await page.locator('.o_field_invalid[name=unit_amount]').waitFor({ timeout: 8000 });
        const invalid = await page.locator('.o_field_invalid[name]').evaluateAll(els => els.map(el => el.getAttribute('name')));
        assert(prefilled || invalid.includes('project_id'), JSON.stringify(invalid));
        const invalidBox = await box(page.locator('.o_field_invalid[name=unit_amount]'));
        assert(invalidBox.y >= 0 && invalidBox.y + invalidBox.h <= phone.height, 'invalid field off screen');
        const notification = await page.locator('.o_notification').first().innerText().catch(() => '');
        await shot(page, 'C2-timesheet-invalid-390');
        const project = prefilled ? { prefilledByNative: prefilled.slice(0, 40) } : await pickMany2one(page, form, 'project_id');
        await shot(page, 'C2-timesheet-project-picked-390');
        const name = form.locator('.o_field_widget[name=name] input, .o_field_widget[name=name] textarea').first();
        await name.fill(`MOBILE-001 giờ giả ${stamp}`);
        const hours = form.locator('.o_field_widget[name=unit_amount] input').first();
        await hours.fill('0:30');
        const hoursBox = await box(hours);
        assert(hoursBox.y >= 0 && hoursBox.y + hoursBox.h <= phone.height, 'hours input off screen ' + JSON.stringify(hoursBox));
        await noOverflow(page);
        await shot(page, 'C2-timesheet-form-390');
        await page.locator('.o_form_button_save:visible').first().click();
        await page.waitForTimeout(1500);
        const rows = await rpc(page, 'account.analytic.line', 'search_read', [[['name', '=', `MOBILE-001 giờ giả ${stamp}`]]], { fields: ['unit_amount', 'user_id', 'project_id', 'task_id'] });
        const problem = await page.locator('.o_error_dialog, .modal .modal-body').allInnerTexts().then(t => t.join(' / ').slice(0, 200));
        await shot(page, 'C2-timesheet-saved-390');
        assert(rows.result?.length === 1, 'not saved: ' + (problem || JSON.stringify(rows.error?.data?.message || rows.result)));
        assert.equal(rows.result[0].user_id[0], uid);
        return { invalid, notification: notification.slice(0, 80), project, hoursBox, saved: { hours: rows.result[0].unit_amount, project: rows.result[0].project_id?.[1]?.slice(0, 30), task: rows.result[0].task_id } };
      });
      await step('C2b Long: hours from the task tab are refused by the task write right (kept, not opened)', async () => {
        if (!WRITE) return { skipped: 'dev is read-only' };
        const tasks = await rpc(page, 'project.task', 'search_read', [[['user_ids', 'in', [uid]]]], { fields: ['id'], limit: 1 });
        await page.goto(`${base}/odoo/project.task/${tasks.result[0].id}`);
        await page.locator('.o_form_view').waitFor();
        await page.locator('.o_notebook .nav-link', { hasText: 'Bảng chấm công' }).click();
        await page.locator('.o_field_widget[name=timesheet_ids]').getByText('Thêm Timesheets').click();
        const modal = page.locator('.modal').last();
        await modal.waitFor();
        await modal.locator('.o_field_widget[name=name] input, .o_field_widget[name=name] textarea').first().fill(`MOBILE-001 tab task ${stamp}`);
        await modal.locator('.o_field_widget[name=unit_amount] input').fill('0:15');
        await shot(page, 'C2b-task-timesheet-dialog-390');
        await modal.locator('.modal-footer .btn-primary').first().click();
        const denied = page.locator('.modal:has-text("Lỗi Truy Cập")').last();
        await denied.waitFor({ timeout: 10000 });
        const message = (await denied.innerText()).replace(/\s+/g, ' ').slice(0, 400);
        assert(/project\.task/.test(message), 'refusal is not the task write right: ' + message);
        await shot(page, 'C2b-task-write-denied-390');
        const rows = await rpc(page, 'account.analytic.line', 'search_read', [[['name', '=', `MOBILE-001 tab task ${stamp}`]]], { fields: ['id'] });
        assert.equal(rows.result?.length, 0, 'line saved despite error');
        await page.goto(`${base}/odoo/tp-home`);
        const leave = page.locator('.modal-footer .btn-primary');
        if (await leave.first().isVisible().catch(() => false)) await leave.first().click();
        await page.locator('.o_tp_web_home_tile').first().waitFor();
        return { refused: /project\.task/.test(message), message };
      });
      await step('C3 Long: expense form on phone, save fake draft expense', async () => {
        await page.goto(`${base}/odoo/expenses`);
        await page.locator('.o_control_panel').waitFor();
        await page.waitForTimeout(800);
        await noOverflow(page);
        await shot(page, 'C3-expenses-390');
        if (!WRITE) return { skipped: 'dev is read-only' };
        await page.goto(`${base}/odoo/expenses/new`);
        const form = page.locator('.o_form_view').first();
        await form.waitFor();
        await page.waitForTimeout(800);
        await form.locator('.o_field_widget[name=name] input, .o_field_widget[name=name] textarea').first().fill(`MOBILE-001 chi phí giả ${stamp}`);
        let category = null;
        if (await form.locator('.o_field_widget[name=product_id] input').isVisible().catch(() => false)) {
          category = await pickMany2one(page, form, 'product_id').catch(error => ({ skipped: error.message.split('\n')[0] }));
        }
        const amount = form.locator('.o_field_widget[name=total_amount_currency] input').first();
        await amount.fill('50000');
        const amountMode = await amount.evaluate(el => el.getAttribute('inputmode') || el.type);
        await noOverflow(page);
        await shot(page, 'C3-expense-form-390');
        await page.locator('.o_form_button_save:visible').first().click();
        await page.waitForTimeout(1500);
        const rows = await rpc(page, 'hr.expense', 'search_read', [[['name', '=', `MOBILE-001 chi phí giả ${stamp}`]]], { fields: ['state', 'employee_id', 'total_amount'] });
        assert(rows.result?.length === 1, JSON.stringify(rows.error?.data?.message || rows.result));
        assert.equal(rows.result[0].state, 'draft');
        await shot(page, 'C3-expense-saved-390');
        return { category, amountMode, saved: { state: rows.result[0].state, total: rows.result[0].total_amount } };
      });
      await step('C4 Long: still cannot finish a task (permission kept, not a responsive bug)', async () => {
        const tasks = await rpc(page, 'project.task', 'search_read', [[['user_ids', 'in', [uid]]]], { fields: ['id', 'state'], limit: 1 });
        assert(tasks.result?.length, 'no task for Long');
        if (!WRITE) return { skipped: 'dev is read-only', readable: true };
        const done = await rpc(page, 'project.task', 'write', [[tasks.result[0].id], { state: '1_done' }]);
        assert(done.error, 'task state write unexpectedly allowed');
        return { blocked: done.error.data?.name };
      });
      assert.deepEqual(errors, []);
      await context.close();
    }

    // ---------------- D. Out-of-scope actor ----------------
    {
      const { context, page } = await session(browser, 'khang', phone);
      await step('D1 Khang: no finance/coordination dashboard data, no Long project records', async () => {
        const report = {};
        for (const id of [5, 6]) {
          const r = await rpc(page, 'spreadsheet.dashboard', 'tp_dashboard_report', [[id], {}]);
          assert(r.error && !r.result, `dashboard ${id} returned data`);
          report[id] = r.error.data?.name;
        }
        const expenses = await rpc(page, 'hr.expense', 'search_read', [[]], { fields: ['total_amount'] });
        const invoices = await rpc(page, 'account.move', 'search_read', [[['move_type', '=', 'out_invoice']]], { fields: ['amount_total'] });
        assert(!(expenses.result?.length), 'Khang reads expenses');
        assert(!(invoices.result?.length), 'Khang reads invoices');
        await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
        await page.waitForTimeout(3000);
        await shot(page, 'D1-khang-dashboard-390');
        const leaked = await page.locator('.tp_metric strong').count();
        assert.equal(leaked, 0, 'Khang sees metrics');
        return { report, expenses: expenses.result?.length ?? expenses.error?.data?.name, invoices: invoices.result?.length ?? invoices.error?.data?.name };
      });
      await context.close();
    }
  } finally {
    const passed = results.length > 0 && results.every(r => r.passed);
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ target, passed, write: WRITE, stamp, engine: 'chromium-emulation', results }, null, 2));
    console.log(JSON.stringify({ target, passed, steps: results.length, failed: results.filter(r => !r.passed).map(r => r.name) }));
    await browser.close();
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
