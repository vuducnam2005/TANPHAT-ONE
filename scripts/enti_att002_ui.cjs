// ENTI-ATTENDANCE-002 browser checks for the attendance screens on the LOCAL test server only
// (port 18179, DB tp_tanphat_test, login from the gitignored .local/test/ui_login.json). Read-only: it opens
// screens, changes filters and resizes the viewport; it does not create, write or delete records.
// Usage: node scripts/enti_att002_ui.cjs   (PORT=18179 by default)
const {chromium} = require('../frontend/node_modules/playwright');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..'), port = process.env.PORT || '18179';
assert.equal(port, '18179', 'only the local test server is allowed');
const base = `http://127.0.0.1:${port}`;
const login = JSON.parse(fs.readFileSync(path.join(root, '.local/test/ui_login.json'), 'utf8'));
assert.equal(login.db, 'tp_tanphat_test');
const out = path.join(root, '.local/enti-att002/ui');
fs.mkdirSync(out, {recursive: true});

const widths = [[1440, 900], [768, 1024], [390, 844], [320, 640]];

(async () => {
    const browser = await chromium.launch({headless: true});
    const context = await browser.newContext({viewport: {width: 1440, height: 900}, acceptDownloads: true});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    page.on('console', (m) => {
        if (m.type() === 'error' && !/service-worker|ServiceWorker|favicon/i.test(m.text())) errors.push('console: ' + m.text());
    });
    const results = [];
    const check = async (name, fn) => {
        await fn();
        results.push(name);
        console.log('PASS ' + name);
    };
    const overflow = () => page.evaluate(() => {
        const ov = document.querySelector('.o_tp_att');
        const bad = [...ov.querySelectorAll('*')].filter((e) => {
            const r = e.getBoundingClientRect();
            return r.width && r.right > innerWidth + 1 && !e.closest('.o_tp_att_table_wrap, .o_tp_att_matrix_wrap, .table-responsive');
        }).slice(0, 5).map((e) => `${e.tagName}.${e.className}:${Math.round(e.getBoundingClientRect().right)}`);
        return {doc: document.documentElement.scrollWidth, inner: innerWidth, own: ov.scrollWidth - ov.clientWidth, bad};
    });
    // Material Symbols in Odoo is a subset font: an unknown ligature renders as nothing (width 0) or a fallback.
    const blankIcons = () => page.evaluate(() => [...document.querySelectorAll('.o_tp_att .oi[data-icon]')]
        .filter((e) => e.offsetParent && e.getBoundingClientRect().width < 4)
        .map((e) => e.dataset.icon));
    const open = async (route, ready) => {
        await page.goto(`${base}/odoo/${route}`);
        await page.locator(ready).first().waitFor({timeout: 90000});
    };
    try {
        await page.goto(`${base}/web/login?db=${login.db}`);
        await page.locator('[name=login]').fill(login.login);
        await page.locator('[name=password]').fill(login.password);
        await page.locator('button[type=submit]').click();
        await page.locator('.o_web_client').waitFor({timeout: 120000});

        await check('overview: header, filters, KPIs, charts, newest marks render', async () => {
            await open('cham-cong', '.o_tp_att_ov_kpis');
            await page.locator('.o_tp_att_ov_donut canvas').waitFor();
            assert.equal(await page.locator('.o_tp_att_ov_kpi').count(), 6);
            assert.ok(await page.locator('.o_tp_att_live').isVisible());
            assert.ok(await page.locator('.o_tp_att_ov_export').isVisible());
            const recent = await page.locator('.o_tp_att_ov_recent_list li').count();
            assert.ok(recent <= 10, 'at most 10 newest marks');
            const grouped = await page.locator('.o_tp_att_ov_when, .o_tp_att_ov_which').evaluateAll((groups) => groups.every((group) => {
                const items = [...group.children];
                const floor = Math.min(...items.map((e) => e.getBoundingClientRect().bottom));
                return items.every((e) => e.getBoundingClientRect().top < floor);
            }));
            assert.ok(grouped, 'period controls and filters each stay on one row at 1440 (reset never alone)');
            assert.deepEqual(await blankIcons(), [], 'every icon glyph exists in the icon font');
        });

        for (const [width, height] of widths) {
            await check(`overview ${width}px: no page overflow, donut fits its card`, async () => {
                await page.setViewportSize({width, height});
                await page.waitForTimeout(400);
                const o = await overflow();
                assert.ok(o.doc <= o.inner && o.own <= 0 && !o.bad.length, JSON.stringify(o));
                const fit = await page.evaluate(() => {
                    const card = document.querySelector('.o_tp_att_ov_status').getBoundingClientRect();
                    const c = document.querySelector('.o_tp_att_ov_donut canvas').getBoundingClientRect();
                    return c.left >= card.left - 1 && c.right <= card.right + 1;
                });
                assert.ok(fit, 'donut inside its card');
                await page.screenshot({path: path.join(out, `overview-${width}.png`), fullPage: false});
            });
        }
        await page.setViewportSize({width: 1440, height: 900});

        for (const [route, ready, label] of [
            ['bang-cong', '.o_tp_att', 'board'],
            ['cong-cua-toi', '.o_tp_att', 'mine'],
            ['nguon-cham-cong', '.o_tp_att', 'sources'],
        ]) {
            await check(`${label}: opens without errors at 1440 and 390`, async () => {
                await open(route, ready);
                await page.waitForTimeout(800);
                assert.deepEqual(await blankIcons(), [], `${label}: every icon glyph exists in the icon font`);
                await page.screenshot({path: path.join(out, `${label}-1440.png`)});
                await page.setViewportSize({width: 390, height: 844});
                await page.waitForTimeout(400);
                const o = await overflow();
                assert.ok(o.doc <= o.inner && !o.bad.length, JSON.stringify(o));
                await page.screenshot({path: path.join(out, `${label}-390.png`)});
                await page.setViewportSize({width: 1440, height: 900});
            });
        }
        await check('Excel import closed: no file picker/upload; sources lists unmapped ENTI people', async () => {
            for (const route of ['bang-cong', 'nguon-cham-cong']) {
                await open(route, '.o_tp_att');
                await page.waitForTimeout(600);
                assert.equal(await page.locator('.o_tp_att input[type=file]').count(), 0, `${route}: no file input`);
                // Only actionable controls count: the closure notice itself says "Đã ngừng nhập tệp Excel".
                const actions = page.locator('.o_tp_att :is(button, a, label, [role=button], [role=menuitem])',
                    {hasText: /Tải tệp|Tải lên|Chọn tệp|Kéo thả|Nhập tệp|Nhập dữ liệu/i});
                assert.equal(await actions.count(), 0, `${route}: no upload action`);
            }
            assert.ok(await page.getByText(/Đã ngừng nhập tệp Excel/).first().isVisible(), 'closure notice shown');
            await page.locator('.o_tp_att_unmapped').waitFor();
            assert.ok(await page.getByText('Đã ngừng nhập · Lịch sử').isVisible(), 'Excel card is history only');
        });
        assert.deepEqual(errors, []);
        console.log(`OK ${results.length} checks; screenshots in ${out}`);
    } catch (error) {
        console.error('FAIL', error.message, errors);
        await page.screenshot({path: path.join(out, 'failure.png')}).catch(() => {});
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
