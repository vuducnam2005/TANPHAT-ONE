/* MOBILE-001: real Chromium page zoom (125%, 150%) via a disposable private profile; Home and both TP dashboards. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const root = path.resolve(__dirname, '..');
const owner = JSON.parse(fs.readFileSync(path.join(root, '.local/dash-ui001/owner.json'), 'utf8'));
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const out = path.join(root, '.local/mobile001', `zoom-${target}`);
fs.mkdirSync(out, { recursive: true });
const ROUTES = [
  ['home', '/odoo/tp-home', '.o_tp_web_home_tile'],
  ['dash6', '/odoo/dashboards?dashboard_id=6', '.tp_connected_dashboard[aria-busy=false] .tp_metrics'],
  ['dash5', '/odoo/dashboards?dashboard_id=5', '.tp_connected_dashboard[aria-busy=false] .tp_metrics'],
];

(async () => {
  const results = [];
  for (const width of [1280, 1440]) {
    const profile = path.join(out, `profile-${width}`);
    const context = await chromium.launchPersistentContext(profile, {
      channel: 'chromium', headless: true, viewport: null, args: [`--window-size=${width},900`], locale: 'vi-VN',
    });
    const errors = [];
    const settings = await context.newPage();
    try {
      await settings.goto('chrome://settings/appearance');
      await settings.locator('#zoomLevel').waitFor();
      const auth = await (await context.request.post(`${base}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', method: 'call', params: { db, login: 'admin', password: secrets.admin } },
      })).json();
      assert(auth.result?.uid, 'admin login failed');
      const page = await context.newPage();
      page.on('pageerror', e => errors.push(e.message));
      for (const zoom of [1.25, 1.5]) {
        await settings.locator('#zoomLevel').selectOption(String(zoom));
        for (const [key, url, ready] of ROUTES) {
          await page.goto(base + url);
          await page.locator(ready).first().waitFor({ timeout: 20000 });
          await page.waitForFunction(expected => Math.abs(devicePixelRatio - expected) < 0.01, zoom);
          await page.waitForTimeout(600);
          const geometry = await page.evaluate(() => {
            const scrollers = [...document.querySelectorAll('.tp_connected_dashboard, .o_content, .o_tp_web_home')];
            const filters = document.querySelector('.tp_filter_toggle');
            const grid = document.querySelector('.o_tp_web_home_grid, .o_tp_web_home_apps');
            return {
              devicePixelRatio, cssWidth: innerWidth,
              pageOverflow: document.documentElement.scrollWidth > innerWidth,
              regionOverflow: scrollers.some(el => el.scrollWidth > el.clientWidth + 1),
              filterToggleVisible: Boolean(filters && filters.offsetParent),
              homeColumns: grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : null,
              moneyWrapped: [...document.querySelectorAll('.tp_metric strong')].some(el =>
                el.getBoundingClientRect().height > parseFloat(getComputedStyle(el).lineHeight) * 1.5),
            };
          });
          assert(!geometry.pageOverflow && !geometry.regionOverflow, `${key} ${zoom} overflow ${JSON.stringify(geometry)}`);
          assert(!geometry.moneyWrapped, `${key} ${zoom} money wrapped`);
          const cdp = await context.newCDPSession(page);
          const shot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
          fs.writeFileSync(path.join(out, `${key}-${width}-${zoom * 100}.png`), Buffer.from(shot.data, 'base64'));
          await cdp.detach();
          results.push({ width, zoom, key, geometry });
          console.log(JSON.stringify({ width, zoom, key, ...geometry }));
        }
      }
      assert.deepEqual(errors, []);
    } finally {
      await settings.locator('#zoomLevel').selectOption('1').catch(() => {});
      await context.close();
    }
    fs.rmSync(profile, { recursive: true, force: true });
  }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ target, passed: true, engine: 'chromium-page-zoom', results }, null, 2));
  console.log(JSON.stringify({ target, passed: true, checks: results.length }));
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
