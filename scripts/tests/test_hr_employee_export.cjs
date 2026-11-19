// Uses an existing session; only search, selection and export, with no business writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

async function run() {
    const base = process.env.TP_HR_EXPORT_BASE || 'http://127.0.0.1:18069';
    const output = path.resolve(process.env.TP_HR_EXPORT_OUTPUT || '.local/hr-employee-xlsx001/browser');
    fs.mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ headless: true });
    const errors = [], requests = [], results = [];
    try {
        const context = await browser.newContext({
            storageState: process.env.TP_HR_EXPORT_STATE || '.local/attendance-ui001/local-state.json',
            viewport: { width: 1440, height: 900 }, locale: 'vi-VN',
        });
        const page = await context.newPage();
        page.setDefaultNavigationTimeout(90000);
        page.on('pageerror', (error) => errors.push(error.message));
        page.on('request', (request) => {
            if (request.url().includes('/get_employee_export_summary')) {
                requests.push(request.postDataJSON().params.args[0]);
            }
        });
        const route = `${base}/app/action-tp_hr_workspace.action_employees`;
        const open = async () => {
            await page.locator('.o_tp_hr_export').click();
            await page.locator('.o_tp_hr_export_count').waitFor();
            return page.locator('.o_tp_hr_export_dialog');
        };
        const count = async () => Number((await page.locator('.o_tp_hr_export_count strong').innerText()).trim());
        const waitCount = (value) => page.waitForFunction((expected) =>
            Number(document.querySelector('.o_tp_hr_export_count strong')?.textContent) === expected, value);
        const close = () => page.getByRole('dialog').getByRole('button', { name: 'Đóng', exact: true }).last().click();
        const download = async (name) => {
            const event = page.waitForEvent('download');
            await page.getByRole('dialog').getByRole('button', { name: 'Xuất Excel', exact: true }).click();
            const file = await event;
            assert.equal(await file.failure(), null);
            await file.saveAs(path.join(output, `${name}.xlsx`));
            await page.locator('.o_tp_hr_export_dialog').waitFor({ state: 'hidden' });
        };
        await page.goto(route, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_tp_hr_export').waitFor({ timeout: 60000 });
        await open();
        const total = await count();
        assert(total > 0);
        assert(await page.locator('input[value="selected"]').isDisabled());
        assert(await page.locator('input[value="filtered"]').isChecked());
        await page.screenshot({ path: path.join(output, 'dialog-desktop.png') });
        await download('all-filtered');
        results.push('Default full population count and real XLSX download');

        const header = page.locator('tr.o_group_header').first();
        if (await header.count()) await header.click();
        await open();
        assert.equal(await count(), total);
        await download('collapsed');
        results.push('Collapsed department still exports full population');

        const nameInput = page.getByPlaceholder('Tìm họ tên…');
        await nameInput.fill('Nguyễn');
        await open();
        assert.equal(await count(), total);
        await close();
        results.push('Unapplied draft filter does not alter export');
        await page.getByRole('button', { name: 'Áp dụng', exact: true }).click();
        await page.locator('.o_tp_hr_export').waitFor();
        await open();
        const filtered = await count();
        assert(filtered > 0 && filtered < total, `filtered=${filtered} total=${total} domain=${JSON.stringify(requests.at(-1).domain)}`);
        assert(requests.at(-1).domain.length > 0);
        await download('filtered');
        results.push('Applied native SearchModel filter exports matching population');

        await page.locator('.o_data_row .o_list_record_selector input').first().check();
        await open();
        await page.locator('input[value="selected"]').check();
        await waitCount(1);
        assert.equal(await count(), 1);
        await download('selected');
        results.push('Selected employees have an independent exact count');
        await open();
        await page.locator('input[value="all"]').check();
        await waitCount(total);
        assert.equal(await count(), total);
        await download('all-managed');
        results.push('All-managed scope includes records outside the current filter');

        await page.goto(route, { waitUntil: 'domcontentloaded' });
        await page.getByRole('button', { name: 'Bộ lọc nâng cao', exact: true }).click();
        await page.getByRole('menuitemcheckbox', { name: 'Chưa có tài khoản', exact: true }).click();
        await open();
        const advanced = await count();
        assert(advanced > 0 && advanced < total);
        assert(JSON.stringify(requests.at(-1).domain).includes('tp_account_status'));
        await download('advanced');
        results.push('Native advanced filter is included in the export domain');

        await page.setViewportSize({ width: 390, height: 844 });
        await page.goto(route, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_tp_hr_export').waitFor();
        await open();
        assert.equal(await count(), total);
        const box = await page.getByRole('dialog').boundingBox();
        assert(box.width <= 390);
        await page.screenshot({ path: path.join(output, 'dialog-mobile.png') });
        await page.keyboard.press('Escape');
        await page.locator('.o_tp_hr_export_dialog').waitFor({ state: 'hidden' });
        results.push('Mobile layout fits viewport and Escape closes dialog');
        assert.deepEqual(errors, []);
        fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ results, total, filtered, advanced, errors }, null, 2));
        console.log(JSON.stringify({ results, total, filtered, advanced, errors }, null, 2));
    } finally {
        await browser.close();
    }
}
run().catch((error) => { console.error(error); process.exit(1); });
