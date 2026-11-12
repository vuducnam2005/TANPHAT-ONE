/* Actual Chromium page zoom in a disposable private browser profile. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const local = path.resolve(__dirname, '../.local/dash-ui001');
const output = process.env.TP_DASH_EVIDENCE_DIR || local;
fs.mkdirSync(output, { recursive: true });
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json'), 'utf8'));
assert.equal(owner.database, 'tp_tanphat_dashui001_20261104');
assert.equal(owner.http_port, 18159);
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const secrets = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../.local/dev-secrets.json'), 'utf8'));
(async () => {
  const context = await chromium.launchPersistentContext(path.join(local, `zoom-${target}-profile`), {
    channel: 'chromium', headless: true, viewport: null, args: ['--window-size=1440,1000'],
  });
  const errors = [], results = [];
  const settings = await context.newPage();
  try {
    await settings.goto('chrome://settings/appearance');
    await settings.locator('#zoomLevel').waitFor();
    const auth = await (await context.request.post(`${base}/web/session/authenticate`, {
      data: { jsonrpc: '2.0', method: 'call', params: { db: target === 'dev' ? 'tp_tanphat_dev' : owner.database,
        login: 'admin', password: secrets.admin } },
    })).json();
    assert(auth.result?.uid);
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    for (const zoom of [1.25, 1.5]) {
      await settings.locator('#zoomLevel').selectOption(String(zoom));
      for (const id of [6, 5]) {
        await page.goto(`${base}/odoo/dashboards?dashboard_id=${id}`);
        await page.locator('.tp_metrics').waitFor();
        await page.waitForFunction(expected => Math.abs(devicePixelRatio - expected) < 0.01, zoom);
        const geometry = await page.evaluate(() => ({ devicePixelRatio, innerWidth, outerWidth,
          overflow: document.documentElement.scrollWidth > innerWidth || [...document.querySelectorAll('.tp_connected_dashboard,.o_content')].some(el => el.scrollWidth > el.clientWidth + 1) }));
        assert(!geometry.overflow);
        const cdp = await context.newCDPSession(page);
        const screenshot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
        fs.writeFileSync(path.join(output, `zoom-${target}-${id}-${zoom * 100}.png`), Buffer.from(screenshot.data, 'base64'));
        await cdp.detach();
        results.push({ zoom, id, geometry });
      }
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, `zoom-${target}-results.json`), JSON.stringify({ passed: true, results, errors }, null, 2));
    console.log(JSON.stringify({ target, passed: true, results }));
  } finally {
    await settings.locator('#zoomLevel').selectOption('1').catch(() => {});
    await context.close();
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
