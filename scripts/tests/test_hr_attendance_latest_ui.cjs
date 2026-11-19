// Read-only browser checks against an existing private session; no uploads or business writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

async function run() {
    const base = process.env.TP_ATT_BASE_URL || 'http://127.0.0.1:18069';
    const output = process.env.TP_ATT_OUTPUT || '.local/attendance-ui001/browser';
    assert(process.env.TP_ATT_STORAGE_STATE, 'Provide private TP_ATT_STORAGE_STATE');
    fs.mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ headless: true });
    const errors = [], results = [];
    try {
        const context = await browser.newContext({ storageState: process.env.TP_ATT_STORAGE_STATE, locale: 'vi-VN' });
        const page = await context.newPage();
        page.setDefaultNavigationTimeout(60000);
        page.on('pageerror', e => errors.push(e.message));
        for (const width of [1440, 390]) {
            await page.setViewportSize({ width, height: 900 });
            await page.goto(`${base}/app/cham-cong`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_att_overview[aria-busy=false]').waitFor();
            assert.equal(await page.getByRole('button', { name: 'Bảng chấm công', exact: true }).count(), 0);
            await page.getByRole('button', { name: 'Tuần', exact: true }).click();
            await page.locator('.o_tp_att_overview[aria-busy=false]').waitFor();
            await page.locator('.o_tp_att_toolbar input[type=date]').fill(process.env.TP_ATT_REVIEW_DATE || '2026-11-09');
            await page.locator('.o_tp_att_toolbar input[type=date]').dispatchEvent('change');
            await page.locator('.o_tp_att_overview[aria-busy=false]').waitFor();
            await page.locator('.o_tp_att_attention_intro').waitFor();
            await Promise.all([
                page.waitForResponse(response => response.url().includes('/tp_overview')),
                page.locator('.o_tp_att_pager select').selectOption('100'),
            ]);
            await page.locator('.o_tp_att_overview[aria-busy=false]').waitFor();
            await page.locator('.o_tp_att_attention_intro').evaluate(el => el.scrollIntoView({ block: 'start' }));
            const missing = page.locator('.o_tp_att_issue.o_missing').first();
            assert(await missing.count() > 0, 'Existing dataset should contain a missing-time example');
            assert.match(await missing.innerText(), /Thiếu giờ (vào|ra)/);
            await page.screenshot({ path: path.join(output, `${width}-attention.png`) });
            const detail = page.locator('.o_tp_att_detail_btn').first();
            await detail.click();
            await page.locator('.o_tp_att_dialog').waitFor();
            await page.keyboard.press('Escape');
            // Historical links render the matrix directly for an authorized processor.
            await page.goto(`${base}/app/bang-cong`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_att_matrix_screen[aria-busy=false]').waitFor();
            await page.getByRole('heading', { name: 'Bảng công Vào/Ra', exact: true }).waitFor();
            assert.equal(await page.locator('.o_cell_tag').filter({ hasText: /^(Trùng|Khác giờ)$/ }).count(), 0);
            assert.equal(await page.getByRole('option', { name: /Trùng giờ đã có|Khác dữ liệu/ }).count(), 0);
            assert(await page.locator('.o_tp_att_matrix_screen table tbody tr').count() > 0);
            const bounds = await page.evaluate(() => ({ w: innerWidth, scroll: document.scrollingElement.scrollWidth }));
            assert(bounds.scroll <= bounds.w + 1, 'Matrix must scroll inside its container');
            await page.screenshot({ path: path.join(output, `${width}-matrix.png`) });
            await page.getByRole('button', { name: 'Quay lại Tổng quan', exact: true }).click();
            await page.locator('.o_tp_att_overview[aria-busy=false]').waitFor();
            results.push({ width, matrix: true, detail: true, noDuplicateLabels: true, bounds });
        }
        assert.deepEqual(errors, []);
    } finally {
        fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({ base, results, errors }, null, 2));
        await browser.close();
    }
    console.log(`PASS ${results.length} responsive navigation/detail cases; no JS errors`);
}
run().catch(error => { console.error(error); process.exitCode = 1; });
