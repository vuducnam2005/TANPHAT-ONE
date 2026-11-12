const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const PORT = process.env.PORT || '18079';
const DB = process.env.DB || 'tp_tanphat_test';
const base = `http://127.0.0.1:${PORT}`;
const secretPath = path.resolve(__dirname, '..', '.local', 'dev-secrets.json');
const secret = JSON.parse(fs.readFileSync(secretPath, 'utf8'));
const outDir = path.resolve(__dirname, '..', '.local', 'hr_verification');
fs.mkdirSync(outDir, { recursive: true });

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    console.log(`[TEST] Connecting to ${base} on db ${DB}...`);
    await page.goto(`${base}/web/login?db=${DB}`);
    await page.locator('[name=login]').fill('admin');
    await page.locator('[name=password]').fill(secret.admin);
    await page.locator('button[type=submit]').click();
    await page.locator('.o_web_client').waitFor({ timeout: 60000 });

    // Step 1: Employee List - verify default auto-unfolded groups WITHOUT search facet
    console.log('[TEST] Checking Employee List default grouping and clean search bar...');
    await page.goto(`${base}/odoo/tp-hr`);
    await page.locator('.o_tp_hr_sidebar').waitFor({ timeout: 30000 });
    
    // Click "Danh sách nhân viên"
    await page.locator('.o_tp_hr_sidebar').getByRole('link', { name: 'Danh sách nhân viên', exact: true }).click();
    await page.locator('.o_list_table').waitFor({ timeout: 30000 });
    await page.waitForTimeout(3000);

    // Verify search bar has NO facets (facet count === 0)
    const facetCount = await page.locator('.o_searchview .o_searchview_facet').count();
    console.log(`[TEST] Search bar facet count: ${facetCount} (expected 0)`);
    assert.equal(facetCount, 0, `Expected 0 search facets in search bar, got ${facetCount}`);

    // Verify groups exist and are expanded
    const groupHeaders = await page.locator('.o_group_header').count();
    console.log(`[TEST] Found ${groupHeaders} department group headers`);
    assert(groupHeaders >= 9, `Expected at least 9 department group headers, got ${groupHeaders}`);

    const rows = await page.locator('.o_list_table tbody tr.o_data_row').count();
    console.log(`[TEST] Found ${rows} employee rows visible in the grouped list view`);
    assert(rows >= 30, `Expected at least 30 employee rows unfolded, got ${rows}`);

    // Verify "Chức vụ" column header exists
    const jobTh = await page.locator('th[data-name="job_id"]').count();
    console.log(`[TEST] "Chức vụ" column header present: ${jobTh > 0}`);
    assert(jobTh > 0, '"Chức vụ" column header not found');

    const shot1 = path.join(outDir, `employee-list-auto-unfolded-${PORT}.png`);
    await page.screenshot({ path: shot1, fullPage: false });
    console.log(`[TEST] Saved screenshot: ${shot1}`);

    // Step 2: Test Drilldown from Dashboard overview also stays grouped!
    console.log('[TEST] Checking Dashboard drilldown maintains department grouping...');
    await page.goto(`${base}/odoo/tp-hr`);
    await page.locator('.o_tp_hr_overview .o_tp_hr_kpis').waitFor({ timeout: 30000 });
    // Click on first department in overview table
    const deptBtn = page.locator('.o_tp_hr_charts tbody button').first();
    if (await deptBtn.count() > 0) {
        await deptBtn.click();
        await page.locator('.o_list_table').waitFor({ timeout: 30000 });
        await page.waitForTimeout(2000);
        const drilldownGroups = await page.locator('.o_group_header').count();
        console.log(`[TEST] Drilldown view has ${drilldownGroups} group header(s)`);
        assert(drilldownGroups >= 1, 'Expected drilldown to be grouped by department');
    }

    // Step 3: Sidebar menu "Chức vụ"
    console.log('[TEST] Checking Sidebar "Chức vụ" menu...');
    await page.goto(`${base}/odoo/tp-hr`);
    await page.locator('.o_tp_hr_sidebar').waitFor({ timeout: 30000 });
    const orgBtn = page.locator('.o_tp_hr_sidebar button.o_tp_hr_sb_group_btn').filter({ hasText: 'Tổ chức' });
    if (await orgBtn.count() > 0) {
        const isOpen = await orgBtn.getAttribute('aria-expanded');
        if (isOpen === 'false') {
            await orgBtn.click();
            await page.waitForTimeout(500);
        }
    }
    const jobMenu = page.locator('aside#tp_hr_sidebar a:has-text("Chức vụ")');
    assert(await jobMenu.count() > 0, 'Sidebar menu "Chức vụ" not found');
    await jobMenu.first().click();
    await page.locator('.o_list_table').waitFor({ timeout: 30000 });
    await page.waitForTimeout(2000);

    const jobRows = await page.locator('.o_list_table tbody tr.o_data_row').count();
    console.log(`[TEST] Found ${jobRows} job positions in Quản lý chức vụ`);
    assert(jobRows >= 10, `Expected at least 10 job positions, got ${jobRows}`);

    const shot2 = path.join(outDir, `job-positions-list-${PORT}.png`);
    await page.screenshot({ path: shot2, fullPage: false });
    console.log(`[TEST] Saved screenshot: ${shot2}`);

    // Step 4: Open a Job Form
    console.log('[TEST] Checking Job Form view...');
    const openFormBtn = page.locator('.o_list_record_open_form_view button').first();
    if (await openFormBtn.count() > 0) {
        await openFormBtn.click();
    } else {
        await page.locator('.o_list_table tbody tr.o_data_row').first().click();
    }
    await page.locator('.o_form_view').waitFor({ timeout: 15000 });
    await page.waitForTimeout(2000);

    const shot3 = path.join(outDir, `job-form-view-${PORT}.png`);
    await page.screenshot({ path: shot3, fullPage: false });
    console.log(`[TEST] Saved screenshot: ${shot3}`);

    // Step 5: Employee Form Tab 1
    console.log('[TEST] Checking Employee Form Tab 1 Chức vụ field...');
    await page.locator('.o_tp_hr_sidebar').getByRole('link', { name: 'Danh sách nhân viên', exact: true }).click();
    await page.locator('.o_list_table').waitFor({ timeout: 30000 });
    await page.waitForTimeout(2000);

    await page.locator('.o_list_table tbody tr.o_data_row td[name="name"]').first().click();
    await page.locator('.o_tp_hr_employee_form').waitFor({ timeout: 15000 });
    await page.waitForTimeout(2000);

    const jobField = page.locator('[name="job_id"]');
    assert(await jobField.count() > 0, 'job_id field not found in form');
    console.log('[TEST] job_id field verified in Employee Form');

    const shot4 = path.join(outDir, `employee-form-overview-job-${PORT}.png`);
    await page.screenshot({ path: shot4, fullPage: false });
    console.log(`[TEST] Saved screenshot: ${shot4}`);

    await browser.close();
    console.log('[TEST] ALL VERIFICATIONS PASSED SUCCESSFULLY!');
})();
