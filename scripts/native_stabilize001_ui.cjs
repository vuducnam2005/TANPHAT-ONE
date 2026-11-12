/* NATIVE-STABILIZE-001: browser audit of Home, TP dashboards, responsive/zoom, revocation and session
 * on the owned clone 18169 only. Chromium emulation and Chromium page zoom; not a real iPhone/Android test.
 * Credentials and evidence stay in the git-ignored .local folder; the only writes are reversible
 * revoke/restore calls through native_stabilize001.py on the clone. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const owner = JSON.parse(fs.readFileSync(path.join(root, '.local/native-stabilize001/owner.json'), 'utf8'));
if (owner.database !== 'tp_tanphat_stab001_20261105' || owner.http_port !== 18169) throw new Error('Foreign clone owner.');
const base = `http://127.0.0.1:${owner.http_port}`;
const db = owner.database;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const actors = JSON.parse(fs.readFileSync(path.join(root, '.local/native-data003/actor-secrets.json'), 'utf8'));
const audit = JSON.parse(fs.readFileSync(path.join(root, '.local/native-stabilize001/audit-clone.json'), 'utf8'));
const out = path.join(root, '.local/native-stabilize001/ui');
fs.mkdirSync(out, { recursive: true });
const python = path.join(root, '.venv/Scripts/python.exe');
const ONLY = process.env.TP_SECTIONS ? new Set(process.env.TP_SECTIONS.split(',')) : null;
const READY = '.tp_connected_dashboard[aria-busy=false] .tp_metrics';
const REPORT_URL = '**/web/dataset/call_kw/spreadsheet.dashboard/tp_dashboard_report';

const checks = [];
function check(section, name, ok, info = {}) {
  checks.push({ section, name, ok: Boolean(ok), info });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${section} | ${name} | ${JSON.stringify(info).slice(0, 400)}`);
}

function credentials(key) {
  return key === 'admin' ? { login: 'admin', password: secrets.admin } : actors[key];
}

async function login(browser, key, viewport = { width: 1280, height: 800 }) {
  const isMobile = viewport.width < 768;
  const context = await browser.newContext({ viewport, isMobile, hasTouch: isMobile, deviceScaleFactor: 1, locale: 'vi-VN' });
  const response = await context.request.post(`${base}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', method: 'call', params: { db, ...credentials(key) } },
  });
  if (!(await response.json()).result?.uid) throw new Error(`${key} login failed`);
  return context;
}

function watch(page) {
  const log = { console: [], http: [], aborted: [], pageErrors: [] };
  page.on('console', m => { if (m.type() === 'error') log.console.push(m.text().slice(0, 300)); });
  page.on('pageerror', e => log.pageErrors.push(e.message.slice(0, 300)));
  page.on('requestfailed', r => log.aborted.push(`${r.method()} ${r.url().replace(base, '')} ${r.failure()?.errorText}`));
  page.on('response', r => { if (r.status() >= 400) log.http.push(`${r.status()} ${r.url().replace(base, '')}`); });
  return log;
}

function clean(log) {
  return !log.console.length && !log.pageErrors.length && !log.http.length;
}

async function rpc(page, model, method, args, kwargs = {}) {
  return page.evaluate(async ([model, method, args, kwargs]) => {
    const response = await fetch(`/web/dataset/call_kw/${model}/${method}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: { model, method, args, kwargs } }),
    });
    const body = await response.json();
    return body.error ? { error: body.error.data?.name || body.error.message, message: body.error.data?.message } : { ok: body.result };
  }, [model, method, args, kwargs]);
}

/* Layout facts read from the page; screenshots are reviewed separately. */
function geometry() {
  const vw = innerWidth;
  const visible = el => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0;
  };
  const clipped = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(p).overflowX)) return p.getBoundingClientRect().right <= vw + 1;
    }
    return false;
  };
  const name = el => el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim()
    ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  const offenders = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 && !clipped(el)) offenders.push(`${name(el)} right=${Math.round(r.right)}`);
  }
  const table = document.querySelector('.tp_table_scroll');
  const meta = document.querySelector('meta[name=viewport]')?.content || '';
  const small = [...document.querySelectorAll('.tp_connected_dashboard button, .tp_connected_dashboard select, .tp_connected_dashboard input, .o_tp_web_home_tile, .o_tp_web_home_search_input')]
    .filter(visible).filter(el => {
      const r = el.getBoundingClientRect();
      return r.width < 24 || r.height < 24;
    }).map(el => `${name(el)} ${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`);
  return {
    vw, scrollWidth: document.documentElement.scrollWidth,
    pageOverflow: document.documentElement.scrollWidth > vw + 1 || document.body.scrollWidth > vw + 1,
    offenders: offenders.slice(0, 6),
    tableScrollsInside: table ? table.scrollWidth > table.clientWidth + 1 : null,
    tableFits: table ? table.getBoundingClientRect().right <= vw + 1 : null,
    zoomBlocked: /user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0+)?(\D|$)/.test(meta), viewportMeta: meta,
    filterToggleVisible: Boolean(document.querySelector('.tp_filter_toggle')?.offsetParent),
    smallTargets: small.slice(0, 6),
  };
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: false });
}

async function home(browser) {
  for (const key of ['admin', 'khoa', 'long']) {
    const context = await login(browser, key);
    const page = await context.newPage();
    const log = watch(page);
    await page.goto(`${base}/odoo/tp-home`);
    await page.locator('.o_tp_web_home_tile').first().waitFor({ timeout: 30000 });
    const tiles = await page.$$eval('.o_tp_web_home_tile', els => els.map(el => ({
      xmlid: el.dataset.menuXmlid, label: el.querySelector('.o_tp_web_home_label')?.textContent.trim() })));
    // Server menu tree for this actor; Home expands only the TANPHAT ONE root into its action leaves.
    const menus = await (await page.request.get(`${base}/web/webclient/load_menus`)).json();
    const leaves = m => (m.children.length ? m.children.flatMap(id => leaves(menus[id])) : (m.actionID ? [m.xmlid] : []));
    const expected = audit.home[key].apps.map(app => app.xmlid).filter(x => x !== 'tp_web_home.menu_home')
      .flatMap(x => (x === 'tp_core.menu_platform' ? leaves(Object.values(menus).find(m => m && m.xmlid === x)) : [x]));
    const shown = tiles.map(t => t.xmlid);
    check('home', `${key} tiles equal ORM permitted non-empty apps`,
      JSON.stringify([...shown].sort()) === JSON.stringify([...expected].sort()), { shown: shown.length, expected: expected.length,
        missing: expected.filter(x => !shown.includes(x)), extra: shown.filter(x => !expected.includes(x)) });
    check('home', `${key} brand and Vietnamese labels`, (await page.textContent('.o_tp_web_home_brand')).trim() === 'TANPHAT ONE'
      && tiles.every(t => t.label), { labels: tiles.map(t => t.label) });
    const search = page.locator('.o_tp_web_home_search_input');
    await search.fill('du an');
    await page.waitForFunction(n => document.querySelectorAll('.o_tp_web_home_tile').length < n, tiles.length, { timeout: 5000 }).catch(() => {});
    const found = await page.locator('.o_tp_web_home_tile').count();
    await search.fill('khong-co-ung-dung-nay');
    await page.locator('.o_tp_web_home_empty').waitFor({ timeout: 5000 }).catch(() => {});
    const emptyText = await page.locator('.o_tp_web_home_empty_title').textContent().catch(() => '');
    await page.locator('.o_tp_web_home_empty .btn').click();
    await page.waitForFunction(n => document.querySelectorAll('.o_tp_web_home_tile').length === n, tiles.length, { timeout: 5000 }).catch(() => {});
    check('home', `${key} search without accents, empty result and clear`, found > 0 && found < tiles.length
      && emptyText.includes('Không tìm thấy') && await page.locator('.o_tp_web_home_tile').count() === tiles.length, { found, emptyText });
    // Open the first permitted app tile, then come back with the navbar Home button.
    const first = page.locator('.o_tp_web_home_tile').first();
    const label = await first.locator('.o_tp_web_home_label').textContent();
    await first.click();
    await page.waitForURL(url => !url.pathname.endsWith('/tp-home'), { timeout: 20000 });
    await page.locator('.o_action_manager > *').first().waitFor({ timeout: 20000 });
    const opened = page.url().replace(base, '');
    await page.locator('.o_tp_web_home_button').click();
    await page.waitForURL(url => url.pathname.endsWith('/tp-home'), { timeout: 20000 });
    await page.locator('.o_tp_web_home_tile').first().waitFor();
    await page.goBack();
    await page.waitForURL(url => !url.pathname.endsWith('/tp-home'), { timeout: 20000 });
    check('home', `${key} open app, Home button, browser back`, Boolean(opened), { label: label.trim(), opened, back: page.url().replace(base, '') });
    // Deep link straight into an app action with a fresh page load.
    await page.goto(`${base}/odoo/project`);
    const deep = await page.locator('.o_kanban_record, .o_data_row, .o_view_nocontent').first().waitFor({ timeout: 20000 })
      .then(() => true, () => false);
    check('home', `${key} deep link /odoo/project`, deep, { url: page.url().replace(base, '') });
    await shot(page, `home-deeplink-${key}`);
    if (key === 'long') {
      // Long has the Dashboards app (standard menu) but neither TP dashboard: record what he actually sees.
      await page.goto(`${base}/odoo/dashboards`);
      await page.locator('.o_spreadsheet_dashboard_action, .o_action_manager .o_action').first().waitFor({ timeout: 20000 });
      await page.waitForTimeout(2500);
      const names = await page.$$eval('.o_search_panel_category_value, .o_spreadsheet_dashboard_action li, .o_spreadsheet_dashboard_action .list-group-item',
        els => [...new Set(els.map(el => el.textContent.trim()).filter(Boolean))].slice(0, 20));
      const tp = await page.locator('.tp_connected_dashboard').count();
      await shot(page, 'home-dashboards-long');
      check('home', 'long Dashboards app shows no TP dashboard', tp === 0, { names });
    }
    check('home', `${key} console/http clean`, clean(log), log);
    await context.close();
  }
  // Unsaved, invalid form: leaving through Home must not silently drop or save it.
  const context = await login(browser, 'admin');
  const page = await context.newPage();
  const log = watch(page);
  await page.goto(`${base}/odoo/contacts/new`);
  await page.locator('.o_form_view div[name=email] input').waitFor({ timeout: 20000 });
  await page.locator('.o_form_view div[name=email] input').fill('stabilize.probe@example.invalid');
  await page.locator('.o_tp_web_home_button').click();
  await page.waitForTimeout(1500);
  const stayed = page.url().includes('/contacts/new') && await page.locator('.o_form_view').count() > 0;
  const warned = await page.locator('.o_field_invalid, .o_notification.border-danger, .o_notification_manager .o_notification, .modal').count();
  await shot(page, 'home-unsaved-invalid');
  check('home', 'invalid unsaved form blocks Home navigation and warns', stayed && warned > 0, { url: page.url().replace(base, ''), warned });
  await page.locator('.o_form_button_cancel').click().catch(() => {});
  const created = await rpc(page, 'res.partner', 'search_count', [[['email', '=', 'stabilize.probe@example.invalid']]]);
  check('home', 'invalid form was not saved', created.ok === 0, created);
  check('home', 'unsaved probe console clean', !log.pageErrors.length, log);
  await context.close();
}

async function responsive(browser) {
  const viewports = [[360, 800], [390, 844], [768, 1024], [1280, 800], [1440, 900]];
  for (const [width, height] of viewports) {
    const context = await login(browser, 'admin', { width, height });
    const page = await context.newPage();
    const log = watch(page);
    for (const [key, url, ready] of [['home', '/odoo/tp-home', '.o_tp_web_home_tile'],
      ['dash6', '/odoo/dashboards?dashboard_id=6', READY], ['dash5', '/odoo/dashboards?dashboard_id=5', READY]]) {
      await page.goto(base + url);
      await page.locator(ready).first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(400);
      const g = await page.evaluate(geometry);
      await shot(page, `${key}-${width}`);
      if (key !== 'home') {
        await page.locator('.tp_table_scroll').scrollIntoViewIfNeeded();
        await shot(page, `${key}-${width}-table`);
      }
      check('responsive', `${key} ${width}px no page overflow, table scrolls inside, zoom allowed`,
        !g.pageOverflow && !g.offenders.length && !g.zoomBlocked && g.tableFits !== false, g);
      if (key !== 'home') check('responsive', `${key} ${width}px filter toggle matches layout`, g.filterToggleVisible === (width < 768), g);
    }
    check('responsive', `${width}px console/http clean`, clean(log), log);
    await context.close();
  }
}

async function zoom() {
  const results = [];
  for (const width of [1280, 1440]) {
    const profile = path.join(out, `zoom-profile-${width}`);
    fs.rmSync(profile, { recursive: true, force: true });
    const context = await chromium.launchPersistentContext(profile, {
      channel: 'chromium', headless: true, viewport: null, args: [`--window-size=${width},900`], locale: 'vi-VN',
    });
    const settings = await context.newPage();
    try {
      await settings.goto('chrome://settings/appearance');
      await settings.locator('#zoomLevel').waitFor();
      const auth = await (await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db, ...credentials('admin') } } })).json();
      if (!auth.result?.uid) throw new Error('admin login failed');
      const page = await context.newPage();
      const log = watch(page);
      for (const level of [1.25, 1.5]) {
        await settings.locator('#zoomLevel').selectOption(String(level));
        for (const [key, url, ready] of [['home', '/odoo/tp-home', '.o_tp_web_home_tile'],
          ['dash6', '/odoo/dashboards?dashboard_id=6', READY], ['dash5', '/odoo/dashboards?dashboard_id=5', READY]]) {
          await page.goto(base + url);
          await page.locator(ready).first().waitFor({ timeout: 30000 });
          await page.waitForFunction(expected => Math.abs(devicePixelRatio - expected) < 0.01, level);
          await page.waitForTimeout(500);
          const g = await page.evaluate(geometry);
          const cdp = await context.newCDPSession(page);
          const image = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
          fs.writeFileSync(path.join(out, `zoom-${key}-${width}-${level * 100}.png`), Buffer.from(image.data, 'base64'));
          await cdp.detach();
          results.push({ width, level, key });
          check('zoom', `${key} ${width}px @${level * 100}% (css ${g.vw}px) no page overflow`, !g.pageOverflow && !g.offenders.length, g);
        }
      }
      check('zoom', `${width}px zoom console/http clean`, clean(log), log);
    } finally {
      await settings.locator('#zoomLevel').selectOption('1').catch(() => {});
      await context.close();
      fs.rmSync(profile, { recursive: true, force: true });
    }
  }
  return results;
}

async function behaviour(browser) {
  const context = await login(browser, 'admin');
  const page = await context.newPage();
  const log = watch(page);
  await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
  await page.locator(READY).waitFor({ timeout: 30000 });
  const details = await page.$$eval('.tp_metric', els => els.map(el => ({
    label: el.querySelector('.tp_metric_label')?.textContent, value: el.querySelector('strong')?.textContent,
    detail: el.querySelector('small')?.textContent || '' })));
  check('dashboard', 'finance metrics show confirmed scope, values unchanged', details[2]?.detail.includes('không gồm')
    && details[3]?.detail.startsWith('Chưa phải số đã chi.') && details[0]?.value === '4' && details[2]?.value === '6', details);
  const project = await page.$$eval('.tp_filters select option', opts => opts.map(o => ({ value: o.value, text: o.textContent }))
    .find(o => o.text.startsWith('DA-2026-001')));

  // A slow unfiltered response must not overwrite the newer project-filtered response.
  let delayed = 0;
  await page.route(REPORT_URL, async route => {
    const filters = JSON.parse(route.request().postData()).params.args[1];
    if (!filters.project_id && delayed++ === 0) await new Promise(resolve => setTimeout(resolve, 2500));
    await route.continue();
  });
  await page.locator('.tp_refresh').click();
  await page.locator('.tp_filters select').selectOption(project.value);
  await page.waitForTimeout(3500);
  await page.locator(READY).waitFor();
  const afterRace = { summary: await page.textContent('.tp_filter_summary'), invoices: await page.textContent('.tp_metric strong') };
  check('dashboard', 'stale unfiltered response ignored after project filter', delayed === 1
    && afterRace.summary.startsWith('DA-2026-001') && afterRace.invoices === '1', afterRace);
  await page.unroute(REPORT_URL);

  // A failed reload keeps the chosen project in the request and must say so, not "all projects".
  await page.route(REPORT_URL, route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
    jsonrpc: '2.0', id: 1, error: { code: 200, message: 'Odoo Server Error',
      data: { name: 'odoo.exceptions.UserError', message: 'Lỗi giả lập của kiểm thử.', debug: '', arguments: [], context: {} } } }) }));
  await page.locator('.tp_refresh').click();
  await page.locator('.tp_error').waitFor();
  const failed = { summary: await page.textContent('.tp_filter_summary'), select: await page.inputValue('.tp_filters select'),
    error: await page.textContent('.tp_error') };
  await shot(page, 'dash6-error-with-project');
  check('dashboard', 'error state keeps truthful project filter summary', failed.summary.startsWith('Dự án đã chọn')
    && failed.select === project.value && failed.error.includes('Lỗi giả lập'), failed);
  await page.unroute(REPORT_URL);
  await page.locator('.tp_error .btn').click();
  await page.locator(READY).waitFor();
  check('dashboard', 'retry restores project data', (await page.textContent('.tp_filter_summary')).startsWith('DA-2026-001'));

  // Drilldown opens exactly the scoped source records, then the breadcrumb returns.
  await page.locator('.tp_metric').first().click();
  await page.locator('.o_list_view .o_data_row').first().waitFor({ timeout: 20000 });
  const invoiceRows = await page.locator('.o_list_view .o_data_row').count();
  await page.locator('.o_breadcrumb .breadcrumb-item a').first().click();
  await page.locator(READY).waitFor({ timeout: 20000 });
  await page.locator('.tp_filter_clear').click().catch(() => {});
  await page.locator(READY).waitFor();
  await page.locator('.tp_metric').nth(2).click();
  await page.locator('.o_list_view .o_data_row').first().waitFor({ timeout: 20000 });
  const expenseRows = await page.locator('.o_list_view .o_data_row').count();
  await shot(page, 'dash6-drilldown-expenses');
  check('dashboard', 'drilldown rows equal scoped metrics (1 invoice for DA-2026-001, 6 expenses)', invoiceRows === 1 && expenseRows === 6,
    { invoiceRows, expenseRows });
  check('dashboard', 'admin behaviour console/http clean', clean(log), log);
  await context.close();

  // Coordination for a project-assigned reader: numbers equal ORM truth, no money in the RPC payload.
  const khoa = await login(browser, 'khoa');
  const kp = await khoa.newPage();
  const klog = watch(kp);
  const payloads = [];
  kp.on('response', async r => { if (r.url().endsWith('/tp_dashboard_report')) payloads.push(await r.text()); });
  await kp.goto(`${base}/odoo/dashboards?dashboard_id=5`);
  await kp.locator(READY).waitFor({ timeout: 30000 });
  const values = await kp.$$eval('.tp_metric strong', els => els.map(el => el.textContent));
  await kp.waitForTimeout(300);
  check('dashboard', 'khoa coordination equals ORM truth and has no money', values.join('|') === '4|28|4|84,00'
    && payloads.length > 0 && payloads.every(p => !/₫|VND/.test(p)), { values, payloads: payloads.length });
  check('dashboard', 'khoa console/http clean', clean(klog), klog);
  await khoa.close();
}

function toggle(command, actor, kind) {
  return execFileSync(python, ['scripts/native_stabilize001.py', command, '--actor', actor, '--kind', kind],
    { cwd: root, encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }).trim();
}

async function revocation(browser) {
  const context = await login(browser, 'khoa');
  const page = await context.newPage();
  const log = watch(page);
  await page.goto(`${base}/odoo/dashboards?dashboard_id=5`);
  await page.locator(READY).waitFor({ timeout: 30000 });
  const before = await page.request.get(`${base}/web/content/spreadsheet.dashboard/5/spreadsheet_binary_data`);
  let revoked = false;
  try {
    console.log(toggle('revoke', 'khoa', 'coordination'));
    revoked = true;
    await page.locator('.tp_refresh').click();
    await page.locator('.tp_error').waitFor({ timeout: 20000 });
    const refresh = await page.textContent('.tp_error h2');
    await shot(page, 'revoked-refresh');
    const drill = await rpc(page, 'spreadsheet.dashboard', 'tp_dashboard_action', [[5], 'tasks', {}]);
    const report = await rpc(page, 'spreadsheet.dashboard', 'tp_dashboard_report', [[5], {}]);
    const raw = await rpc(page, 'spreadsheet.dashboard', 'read', [[5], ['spreadsheet_data']]);
    const download = await page.request.get(`${base}/web/content/spreadsheet.dashboard/5/spreadsheet_binary_data`);
    await page.goto(`${base}/odoo/dashboards?dashboard_id=5`);
    await page.waitForTimeout(3000);
    const reloaded = await page.locator('.tp_connected_dashboard .tp_metrics').count();
    await shot(page, 'revoked-reload');
    check('revocation', 'revoked user: refresh, drilldown, report, raw read, download, reload all denied',
      refresh.includes('Không đủ quyền') && /AccessError/.test(drill.error || '') && /AccessError/.test(report.error || '')
      && /AccessError/.test(raw.error || '') && download.status() !== 200 && reloaded === 0,
      { refresh, drill, report, raw: raw.error, downloadBefore: before.status(), download: download.status(), reloaded });
  } finally {
    if (revoked) console.log(toggle('restore', 'khoa', 'coordination'));
  }
  await page.goto(`${base}/odoo/dashboards?dashboard_id=5`);
  const restored = await page.locator(READY).waitFor({ timeout: 30000 }).then(() => true, () => false);
  check('revocation', 'restored access works again', restored);
  // Known core gap (report F-DASH-04): a revoked deep link makes the core loader JSON-parse the 403 HTML page.
  const core = log.pageErrors.every(e => e.includes('is not valid JSON')) && log.http.every(h => h === '403 /spreadsheet/dashboard/data/5');
  check('revocation', 'only the known core 403 parse error on revoked deep link', core, { ...log, known_gap: 'F-DASH-04' });
  await context.close();
}

async function session(browser) {
  const a = await login(browser, 'admin');
  const page = await a.newPage();
  await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
  await page.locator(READY).waitFor({ timeout: 30000 });
  const b = await browser.newContext({ storageState: await a.storageState(), locale: 'vi-VN' });
  const old = await b.newPage();
  await old.goto(`${base}/odoo/tp-home`);
  await old.locator('.o_tp_web_home_tile').first().waitFor({ timeout: 20000 });
  await page.locator('.o_user_menu').click();
  await page.locator('[data-menu="logout"]').click();
  await page.waitForURL(url => url.pathname.startsWith('/web/login') || url.pathname === '/odoo', { timeout: 20000 });
  const call = await rpc(old, 'spreadsheet.dashboard', 'tp_dashboard_report', [[6], {}]);
  await old.goto(`${base}/odoo/dashboards?dashboard_id=6`);
  await old.waitForLoadState('networkidle');
  await shot(old, 'session-old-cookie');
  check('session', 'logout invalidates the same session cookie elsewhere (RPC and page)',
    /SessionExpired/.test(call.error || '') && old.url().includes('/web/login'), { call, url: old.url().replace(base, '') });
  await a.close();
  await b.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const zoomRuns = [];
  try {
    for (const [name, fn] of [['home', home], ['responsive', responsive], ['dashboard', behaviour], ['revocation', revocation],
      ['session', session]]) {
      if (ONLY && !ONLY.has(name)) continue;
      try { await fn(browser); } catch (error) { check(name, 'section completed', false, { error: error.message.slice(0, 500) }); }
    }
  } finally {
    await browser.close();
  }
  if (!ONLY || ONLY.has('zoom')) {
    try { zoomRuns.push(...await zoom()); } catch (error) { check('zoom', 'section completed', false, { error: error.message.slice(0, 500) }); }
  }
  const failed = checks.filter(c => !c.ok);
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ engine: 'chromium-emulation+page-zoom', base, checks }, null, 2));
  console.log(JSON.stringify({ passed: checks.length - failed.length, failed: failed.length, zoom: zoomRuns.length }));
  if (failed.length) process.exitCode = 1;
})();
