// Playwright verification for HR-UNIFIED-READONLY-UI-001 (Admin vs Employee parity + 3 hidden tabs).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

const FORBIDDEN_TABS = ['Hợp đồng lao động', 'Lịch sử hoạt động', 'Tài khoản và phân quyền'];
const FORBIDDEN_SECRETS = ['SYN-SECRET-CONTRACT-DOC', 'HD-SYN-999', 'SYN-SECRET-HISTORY-NOTE', 'SYN-SECRET-CCCD-999'];

async function run() {
    const f = JSON.parse(fs.readFileSync(process.env.TP_HR_UNIFIED_FIXTURE, 'utf8'));
    assert.equal(new URL(f.base).port, '18079');
    const browser = await chromium.launch({ headless: true });
    const errors = [];
    const checks = [];
    const apiBodies = [];
    let page;
    try {
        const context = await browser.newContext({ locale: 'vi-VN' });
        await context.addCookies(f.cookies);
        page = await context.newPage();
        page.setDefaultTimeout(45000);
        page.on('pageerror', (e) => errors.push(e.message));
        page.on('response', async (resp) => {
            if (f.role === 'employee' && resp.url().includes('/web/dataset/call_kw')) {
                try {
                    const text = await resp.text();
                    apiBodies.push({ url: resp.url(), text });
                } catch {
                    // ignore stream/aborted responses
                }
            }
        });

        const listAction = f.role === 'admin'
            ? 'tp_hr_workspace.action_employees'
            : 'tp_hr_workspace.action_directory';
        const overviewAction = f.role === 'admin'
            ? 'tp_hr_workspace.action_overview'
            : 'tp_hr_workspace.action_public_overview';

        for (const [size, width, height] of [['desktop', 1440, 900], ['mobile', 390, 844]]) {
            await page.setViewportSize({ width, height });

            // 1. Overview Dashboard
            await page.goto(`${f.base}/app/action-${overviewAction}`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_hr_overview .o_tp_hr_kpis').waitFor();
            assert.equal(await page.locator('.o_tp_hr_overview h1').innerText(), 'Tổng quan nhân sự');
            if (f.role === 'employee') {
                assert.ok(await page.locator('.o_tp_hr_overview .o_tp_hr_readonly_badge').isVisible());
                assert.equal(await page.locator('.o_tp_hr_overview button:has-text("Thêm nhân viên")').count(), 0);
                assert.equal(await page.locator('.o_tp_hr_overview button:has-text("Xuất Excel")').count(), 0);
                assert.equal(await page.locator('.o_tp_hr_quality, .o_tp_hr_accounts').count(), 0);
            } else {
                assert.ok(await page.locator('.o_tp_hr_quality').isVisible());
            }
            const ovOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
            assert.equal(ovOverflow, false, `${f.role}-${size}: overview horizontal page overflow`);
            await page.screenshot({ path: path.join(f.output, `${f.role}-${size}-overview.png`) });
            checks.push(`${f.role}-${size}: overview rendered cleanly`);

            // 2. Employee List + Department Grouping + Custom Drag-Drop Order
            await page.goto(`${f.base}/app/action-${listAction}`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_hr_employee_list .o_list_table tbody .o_group_header').first().waitFor();
            // No giant repeated heading "Danh bạ nhân viên"
            assert.equal(await page.locator('.o_tp_hr_list_heading').count(), 0);
            // Verify custom department order & employee order within first dept
            const groupTexts = await page.locator('.o_group_header').allInnerTexts();
            const idxFirst = groupTexts.findIndex((t) => t.includes(f.deptFirstName));
            const idxSecond = groupTexts.findIndex((t) => t.includes(f.deptSecondName));
            assert.ok(idxFirst >= 0 && idxSecond >= 0 && idxFirst < idxSecond, `Department order mismatch: ${groupTexts}`);
            const rowNames = await page.locator('.o_data_row .o_tp_hr_identity_content').allInnerTexts();
            const posColleague = rowNames.findIndex((t) => t.includes(f.colleagueName));
            const posSelf = rowNames.findIndex((t) => t.includes(f.selfName));
            assert.ok(posColleague >= 0 && posSelf >= 0 && posColleague < posSelf, `Employee custom order mismatch: ${rowNames}`);
            // Verify avatar renders in unified identity cell
            assert.ok((await page.locator('.o_data_row .o_tp_hr_identity_content img').count()) >= 2);
            if (f.role === 'employee') {
                assert.equal(await page.locator('.o_list_button_add:visible').count(), 0);
                assert.equal(await page.locator('.o_tp_hr_export:visible').count(), 0);
                assert.equal(await page.locator('.o_tp_hr_draggable_row').count(), 0);
                assert.ok(await page.locator('.o_tp_hr_list_readonly_badge').isVisible());
            }
            const listOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
            assert.equal(listOverflow, false, `${f.role}-${size}: list horizontal page overflow`);
            await page.screenshot({ path: path.join(f.output, `${f.role}-${size}-list.png`) });
            checks.push(`${f.role}-${size}: list grouped with saved dept+employee order and avatars`);

            // 3. Filter Bar (search colleague by code/name)
            if (size === 'desktop') {
                const filterBar = page.locator('.tp_filter_bar');
                await filterBar.waitFor();
                const textInput = filterBar.locator('input[type="text"], input[type="search"]').first();
                await textInput.fill(f.role === 'employee' ? f.colleagueCode : f.colleagueName);
                await filterBar.getByRole('button', { name: 'Áp dụng' }).click();
                await page.waitForTimeout(700);
                const filteredNames = await page.locator('.o_data_row .o_tp_hr_identity_content').allInnerTexts();
                assert.ok(filteredNames.some((t) => t.includes(f.colleagueName)), `Filter missed colleague: ${filteredNames}`);
                assert.ok(!filteredNames.some((t) => t.includes(f.selfName)), `Filter did not narrow: ${filteredNames}`);
                await page.screenshot({ path: path.join(f.output, `${f.role}-${size}-filter.png`) });
                checks.push(`${f.role}-${size}: filter bar narrowed to colleague`);
            }

            // 4. Switch from Own Profile (My Profile) -> Colleague Detail (check zero stale data & 3 hidden tabs!)
            if (f.role === 'employee') {
                await page.goto(`${f.base}/app/action-tp_hr_workspace.action_my_profile`, { waitUntil: 'domcontentloaded' });
                await page.locator('.o_tp_hr_my_profile').waitFor();
                await page.locator('.o_tp_hr_my_profile').getByText(f.selfName).first().waitFor();
                // Clear collected API bodies right before opening colleague so we inspect colleague responses strictly
                apiBodies.length = 0;
            }

            await page.goto(`${f.base}/app/action-${listAction}/${f.colleagueId}`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_hr_employee_form .o_tp_hr_header').waitFor();
            const headerName = await page.locator('.o_tp_hr_name').innerText();
            assert.ok(headerName.includes(f.colleagueName), `Wrong profile opened: ${headerName}`);
            const tabLabels = (await page.locator('.o_notebook .nav-link').allInnerTexts()).map((t) => t.trim());
            const pageText = await page.locator('.o_tp_hr_employee_form').innerText();

            if (f.role === 'employee') {
                for (const forbidden of FORBIDDEN_TABS) {
                    assert.ok(!tabLabels.some((t) => t.includes(forbidden)), `Forbidden tab visible: ${forbidden} in ${tabLabels}`);
                    assert.ok(!pageText.includes(forbidden), `Forbidden tab text leaked in form: ${forbidden}`);
                }
                for (const secret of FORBIDDEN_SECRETS) {
                    assert.ok(!pageText.includes(secret), `Confidential secret leaked in DOM: ${secret}`);
                    for (const entry of apiBodies) {
                        assert.ok(!entry.text.includes(secret), `Confidential secret leaked in API ${entry.url}: ${secret}`);
                    }
                }
                assert.equal(await page.locator('.o_tp_hr_edit:visible, .o_tp_hr_save:visible').count(), 0);
                assert.ok(await page.locator('.o_tp_hr_employee_form .o_tp_hr_readonly_badge').isVisible());
                assert.ok(await page.getByRole('button', { name: 'Quay lại' }).first().isVisible());
                // Also inspect work_information tab
                await page.locator('.o_notebook .nav-link:has-text("Hồ sơ và năng lực")').click();
                await page.waitForTimeout(250);
                await page.locator('.o_notebook .nav-link:has-text("Tổng quan")').click();
                await page.waitForTimeout(250);
            } else {
                for (const expected of FORBIDDEN_TABS) {
                    assert.ok(tabLabels.some((t) => t.includes(expected)), `Admin missing tab ${expected}: ${tabLabels}`);
                }
            }
            const detailOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
            assert.equal(detailOverflow, false, `${f.role}-${size}: detail horizontal page overflow`);
            await page.screenshot({ path: path.join(f.output, `${f.role}-${size}-detail.png`) });
            checks.push(`${f.role}-${size}: detail parity & tab visibility verified (${tabLabels.join(', ')})`);
        }

        // 5. Employee direct URL to admin action_employees must be blocked/redirected (not showing admin form)
        if (f.role === 'employee') {
            await page.setViewportSize({ width: 1440, height: 900 });
            await page.goto(`${f.base}/app/action-tp_hr_workspace.action_employees/${f.colleagueId}`, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(1500);
            const bodyText = await page.locator('body').innerText();
            for (const secret of FORBIDDEN_SECRETS) {
                assert.ok(!bodyText.includes(secret), `Secret leaked on direct admin URL: ${secret}`);
            }
            checks.push('employee: direct admin employee URL blocked/redirected with zero secret leak');
        }

        assert.deepEqual(errors, [], `Page errors: ${errors.join(' | ')}`);
        fs.writeFileSync(path.join(f.output, `${f.role}-result.json`), JSON.stringify({ checks, errors }, null, 2));
        console.log(JSON.stringify({ role: f.role, checks, errors }));
    } catch (error) {
        if (page) {
            await page.screenshot({ path: path.join(f.output, `${f.role}-failure.png`) });
            fs.writeFileSync(path.join(f.output, `${f.role}-failure.html`), await page.content());
        }
        console.error(JSON.stringify({ role: f.role, errors, message: error.message, stack: error.stack }));
        process.exit(1);
    } finally {
        await browser.close();
    }
}

run();
