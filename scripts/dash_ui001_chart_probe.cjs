/* Read-only regression for chart hover/focus, SVG geometry and native source actions. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/dash-hover001');
const out = path.join(local, `charts-${target}`);
fs.mkdirSync(out, { recursive: true });
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : 18159}`;
const secrets = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json'), 'utf8'));
const checks = [];
function check(name, valid) { assert(valid, name); checks.push(name); }

(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const auth = await (await context.request.post(`${base}/web/session/authenticate`, {
      data: { jsonrpc: '2.0', method: 'call', params: { db: target === 'dev' ? 'tp_tanphat_dev' : 'tp_tanphat_dashui001_20261104', login: 'admin', password: secrets.admin } },
    })).json();
    assert(auth.result?.uid);
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    for (const id of [6, 5]) {
      await page.goto(`${base}/odoo/dashboards?dashboard_id=${id}`);
      await page.locator('.tp_metrics').waitFor();
      const bar = page.locator('.tp_bar_row').first();
      await bar.hover();
      await page.locator('.tp_chart_tooltip').waitFor();
      const tooltip = page.locator('.tp_chart_tooltip');
      check(`${id} exact hover detail`, (await tooltip.innerText()).includes('Cầu Sông Xanh'));
      check(`${id} backend exact value`, (await tooltip.innerText()).includes(id === 6 ? '310.000.000' : '8 Công việc'));
      check(`${id} active bar`, await bar.evaluate(el => el.classList.contains('tp_active')));
      check(`${id} peer dimmed`, await page.locator('.tp_bar_row').nth(1).evaluate(el => Number(getComputedStyle(el).opacity) < 1));
      check(`${id} tick grid`, await page.locator('.tp_axis').first().locator('span').count() === 5);
      check(`${id} visible bar thickness`, await page.locator('.tp_bar_track').first().evaluate(el => el.getBoundingClientRect().height >= 24));
      await page.screenshot({ path: path.join(out, `${id}-bar-hover.png`) });
      await tooltip.hover();
      await page.waitForTimeout(250);
      check(`${id} hoverable tooltip`, await tooltip.isVisible());
      await page.keyboard.press('Escape');
      await tooltip.waitFor({ state: 'hidden' });
      await page.mouse.move(10, 10);
      await bar.focus();
      await tooltip.waitFor();
      check(`${id} focus keeps keyboard`, await bar.evaluate(el => document.activeElement === el));
      const described = await bar.getAttribute('aria-describedby');
      check(`${id} accessible detail link`, described && await page.locator(`#${described}`).count() === 1);
      await page.keyboard.press('Escape');
      await tooltip.waitFor({ state: 'hidden' });
      check(`${id} escape retains focus`, await bar.evaluate(el => document.activeElement === el));
      await page.emulateMedia({ reducedMotion: 'reduce' });
      check(`${id} reduced motion`, await page.locator('.tp_bar_fill').first().evaluate(el => getComputedStyle(el).transitionDuration === '0s'));
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      const actionResponse = page.waitForResponse(response => response.url().includes('/tp_dashboard_action'));
      await page.keyboard.press('Enter');
      const action = (await (await actionResponse).json()).result;
      await page.locator('.o_list_view').waitFor();
      check(`${id} chart opens scoped native source`, action.domain[0][2].length === (id === 6 ? 1 : 8));
    }
    await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
    await page.locator('.tp_donut_slice').first().waitFor();
    const slices = page.locator('.tp_donut_slice');
    check('three state sectors', await slices.count() === 3);
    const paint = await slices.evaluateAll(elements => elements.map(el => getComputedStyle(el).stroke));
    check('three distinct state colors', new Set(paint).size === 3 && !paint.includes('none'));
    const legend = page.locator('.tp_legend_row');
    await legend.nth(2).hover();
    await page.locator('.tp_chart_tooltip').waitFor();
    await page.waitForFunction(() => {
      const sector = document.querySelectorAll('.tp_donut_slice')[2];
      return sector.classList.contains('tp_active') && parseFloat(getComputedStyle(sector).strokeWidth) > 26;
    });
    check('legend highlights corresponding sector', await slices.nth(2).evaluate(el => el.classList.contains('tp_active') && parseFloat(getComputedStyle(el).strokeWidth) > 26));
    check('donut updates center', (await page.locator('.tp_donut_center').innerText()).includes('5.100.000'));
    check('donut percentage explanation', (await page.locator('.tp_chart_tooltip').innerText()).includes('71,2%'));
    await page.screenshot({ path: path.join(out, '6-donut-hover.png') });
    await page.keyboard.press('Escape');
    await page.mouse.move(10, 10);
    // The SVG curve has a much smaller hit area than its bounding box; target a visible
    // point on the first sector, based on its actual SVG geometry.
    const point = await slices.nth(0).evaluate(el => {
      const point = el.getPointAtLength(el.getTotalLength() * 0.03);
      const transformed = new DOMPoint(point.x, point.y).matrixTransform(el.getScreenCTM());
      return { x: transformed.x, y: transformed.y };
    });
    await page.mouse.move(point.x, point.y);
    await page.locator('.tp_chart_tooltip').waitFor();
    check('SVG sector hover', (await page.locator('.tp_chart_tooltip').innerText()).includes('810.000'));
    await page.keyboard.press('Escape');
    await legend.nth(2).focus();
    const expenseActionResponse = page.waitForResponse(response => response.url().includes('/tp_dashboard_action'));
    await page.keyboard.press('Enter');
    const expenseAction = (await (await expenseActionResponse).json()).result;
    await page.locator('.o_list_view').waitFor();
    check('state legend source domain', JSON.stringify(expenseAction.domain[0][2]) === '[8,9,11]');
    await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
    await page.locator('.tp_metrics').waitFor();
    await page.getByLabel('Dự án', { exact: true }).selectOption('10');
    await page.waitForFunction(() => document.querySelectorAll('.tp_details tbody tr').length === 1);
    check('single state fills complete circle', await page.locator('.tp_donut_slice').first().getAttribute('stroke-dasharray') === '100 0');
    await page.getByLabel('Từ ngày', { exact: true }).fill('2100-01-01');
    await page.locator('.tp_empty').waitFor();
    const empty = await page.locator('.tp_donut_slice').evaluateAll(elements => elements.every(el => el.getAttribute('stroke-dasharray') === '0 100'));
    check('empty filter never paints false sector', empty);
    check('empty filter has no percentage NaN', !(await page.locator('.tp_donut_chart').innerText()).includes('NaN'));
    for (const width of [1440, 1280, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(`${base}/odoo/dashboards?dashboard_id=6`);
      await page.locator('.tp_metrics').waitFor();
      await page.locator('.tp_charts').scrollIntoViewIfNeeded();
      await page.mouse.move(10, 10);
      await page.locator('.tp_chart_tooltip').waitFor({ state: 'hidden' });
      if (width === 1440) await page.screenshot({ path: path.join(out, '6-chart-idle.png') });
      await page.locator('.tp_legend_row').nth(2).hover();
      await page.locator('.tp_chart_tooltip').waitFor();
      const bounds = await page.locator('.tp_chart_popover').boundingBox();
      check(`${width} tooltip stays in viewport`, bounds.x >= 0 && bounds.x + bounds.width <= width + 1);
      check(`${width} no content overflow`, await page.evaluate(() => [...document.querySelectorAll('.tp_connected_dashboard,.o_content')].every(el => el.scrollWidth <= el.clientWidth + 1)));
      await page.screenshot({ path: path.join(out, `6-chart-${width}.png`) });
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(`${base}/odoo/dashboards?dashboard_id=5`);
    await page.locator('.tp_metrics').waitFor();
    await page.locator('.tp_charts').scrollIntoViewIfNeeded();
    await page.locator('.tp_bar_row').nth(5).hover();
    await page.locator('.tp_chart_tooltip').waitFor();
    await page.screenshot({ path: path.join(out, '5-chart-hover.png') });
    await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
    await page.locator('.tp_metrics').waitFor();
    check('refresh removes old tooltip', await page.locator('.tp_chart_tooltip').count() === 0);
    const touchContext = await browser.newContext({ storageState: await context.storageState(), hasTouch: true,
      isMobile: true, viewport: { width: 390, height: 1000 } });
    const touchPage = await touchContext.newPage();
    touchPage.on('pageerror', error => errors.push(error.message));
    await touchPage.goto(`${base}/odoo/dashboards?dashboard_id=6`);
    await touchPage.locator('.tp_metrics').waitFor();
    const tapResponse = touchPage.waitForResponse(response => response.url().includes('/tp_dashboard_action'));
    await touchPage.locator('.tp_legend_row').nth(1).tap();
    const tapAction = (await (await tapResponse).json()).result;
    await touchPage.locator('.o_list_view').waitFor();
    check('touch opens source without needing hover', JSON.stringify(tapAction.domain[0][2]) === '[7]');
    await touchContext.close();
    check('no console or runtime errors', errors.length === 0);
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ passed: true, target, checks, errors }, null, 2));
    console.log(JSON.stringify({ target, passed: checks.length, errors }));
    await context.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
