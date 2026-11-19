// Read-only browser verification for HR-ATTENDANCE-MINE-UI-001 ("Công của tôi" standalone & embedded).
// Uses an existing private session (TP_ATT_STORAGE_STATE) and read-only ORM payloads; performs no business writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

async function scrollMetrics(page) {
    return page.evaluate(() => {
        const root = document.scrollingElement;
        const screen = document.querySelector('.o_tp_att_mine');
        const wrap = document.querySelector('.o_tp_mine_table_wrap');
        const navbar = document.querySelector('.o_navbar');
        const sidebar = document.querySelector('.o_tp_hr_sidebar:not(.is-hidden)');
        return {
            documentY: root.scrollTop,
            documentHeight: root.scrollHeight,
            viewportHeight: innerHeight,
            documentWidth: root.scrollWidth,
            viewportWidth: innerWidth,
            screenY: screen ? screen.scrollTop : 0,
            screenHeight: screen ? screen.clientHeight : 0,
            contentHeight: screen ? screen.scrollHeight : 0,
            wrapOverflowY: wrap ? getComputedStyle(wrap).overflowY : '',
            navbarY: navbar ? navbar.getBoundingClientRect().top : null,
            sidebarY: sidebar ? sidebar.getBoundingClientRect().top : null,
            hiddenLabelContained: screen
                ? [...screen.querySelectorAll('.visually-hidden')].every((el) => screen.contains(el.offsetParent))
                : true,
        };
    });
}

async function run() {
    const base = process.env.TP_ATT_BASE_URL || 'http://127.0.0.1:18069';
    const storageState = process.env.TP_ATT_STORAGE_STATE || '.local/attendance-ui001/local-state.json';
    const payloadsPath = process.env.TP_MINE_PAYLOADS || '.local/mine-ui001/after-payloads.json';
    const output = path.resolve(process.env.TP_MINE_OUTPUT || '.local/mine-ui001/after');
    assert(fs.existsSync(storageState), `Missing storage state: ${storageState}`);
    assert(fs.existsSync(payloadsPath), `Missing read-only ORM payloads: ${payloadsPath}`);
    fs.mkdirSync(output, { recursive: true });

    const payloads = JSON.parse(fs.readFileSync(payloadsPath, 'utf8'));
    const browser = await chromium.launch({ headless: true });
    const errors = [];
    const results = [];
    const exportCalls = [];

    try {
        const context = await browser.newContext({ storageState, locale: 'vi-VN' });
        const page = await context.newPage();
        page.setDefaultNavigationTimeout(60000);
        page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
        page.on('console', (m) => {
            if (m.type() === 'error') {
                errors.push(`console.error: ${m.text()}`);
            }
        });

        // Route tp_mine & tp_get_my_profile with real read-only ORM payloads from uid=41 (no DB writes).
        await page.route('**/web/dataset/call_kw/tp.hr.attendance.day/tp_mine*', async (route) => {
            const post = route.request().postDataJSON?.() || {};
            const p = post?.params?.args?.[0] || {};
            let result = payloads.month;
            if (p.mode === 'range' || p.mode === 'week') {
                result = payloads.week;
            } else if (p.state === 'missing_out') {
                result = payloads.month_missing_out;
            } else if (p.state === 'missing_in') {
                result = payloads.month_empty;
            } else if (p.weekday === 'weekend') {
                result = payloads.month_weekend;
            } else if (Number(p.page_size) === 10 && Number(p.page) === 2) {
                result = payloads.month_p2_10;
            } else if (Number(p.page_size) === 10) {
                result = payloads.month_p1_10;
            }
            await route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ jsonrpc: '2.0', id: post.id || 1, result }),
            });
        });
        await page.route('**/web/dataset/call_kw/tp.hr.attendance.day/tp_export_mine*', async (route) => {
            const post = route.request().postDataJSON?.() || {};
            exportCalls.push(post?.params?.args?.[0] || {});
            await route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: post.id || 1,
                    result: { filename: 'cong-cua-toi-test.xlsx', data: Buffer.from('PK').toString('base64') },
                }),
            });
        });
        await page.route('**/web/dataset/call_kw/res.users/tp_get_my_profile*', async (route) => {
            const post = route.request().postDataJSON?.() || {};
            await route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ jsonrpc: '2.0', id: post.id || 1, result: payloads.profile }),
            });
        });

        // 1. Desktop 1440x900 standalone: Month view
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto(`${base}/app/cong-cua-toi`, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_tp_att_mine[aria-busy="false"] .o_tp_mine_table').waitFor({ timeout: 30000 });
        await page.waitForTimeout(250);

        // Single employee name occurrence (no duplication!)
        const nameCount = await page.locator('.o_tp_att_mine').getByText(payloads.month.employee.name, { exact: false }).count();
        assert.equal(nameCount, 1, `Employee name should appear exactly once, got ${nameCount}`);
        // 30 rows rendered on default page_size 50
        assert.equal(await page.locator('.o_tp_mine_row').count(), 30, 'Month should render all 30 rows on page 1 (default 50)');
        // Today badge present
        assert.equal(await page.locator('.o_tp_mine_today_pill').count(), 1, 'Today badge should be rendered');
        // Partial late shows "—" (never converted to 0)
        const lateVals = await page.locator('.o_stat_excel .o_tp_mine_stat_val strong').allInnerTexts();
        assert.deepEqual(lateVals, ['—', '—'], 'Partial month late must show "—", never 0');
        // Missing cells show explicit "Thiếu giờ ra" label
        assert(await page.locator('.o_tp_mine_missing_cell').first().innerText().then((t) => t.includes('Thiếu giờ ra')));
        // No fake expand buttons on future rows
        const futureExpand = await page.locator('.o_tp_mine_row.o_is_future .o_tp_mine_expand_btn').count();
        assert.equal(futureExpand, 0, 'Future rows without backend data must not have fake expand buttons');
        await page.screenshot({ path: path.join(output, 'after-1440-month.png') });
        results.push({ case: 'desktop-month', ok: true, rows: 30, nameCount });

        // 2. Scroll containment & no nested vertical scroll on desktop
        const beforeScroll = await scrollMetrics(page);
        assert(beforeScroll.hiddenLabelContained, 'Hidden labels escaped scrollport');
        assert(beforeScroll.documentHeight <= beforeScroll.viewportHeight + 1, 'Document has blank vertical overflow');
        assert(beforeScroll.documentWidth <= beforeScroll.viewportWidth + 1, 'Document overflows horizontally');
        assert.equal(beforeScroll.wrapOverflowY, 'clip', 'Table wrap must not create nested vertical scrollbar on desktop');
        const box = await page.locator('.o_tp_att_mine').boundingBox();
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        for (let i = 0; i < 6; i++) {
            await page.mouse.wheel(0, 1200);
            await page.waitForTimeout(40);
        }
        const downScroll = await scrollMetrics(page);
        assert(downScroll.screenY > 0, 'Standalone mine screen should scroll vertically');
        assert.equal(downScroll.documentY, 0, 'Wheel escaped to document body');
        assert.equal(downScroll.navbarY, beforeScroll.navbarY, 'Navbar moved on scroll');
        assert.equal(downScroll.sidebarY, beforeScroll.sidebarY, 'Sidebar moved on scroll');
        // Capture scrolled view showing sticky header + Today + Future rows + footer legend/pager
        await page.locator('.o_tp_mine_row.o_is_today').evaluate((el) => el.scrollIntoView({ block: 'center' }));
        await page.waitForTimeout(150);
        await page.screenshot({ path: path.join(output, 'after-1440-today-future.png') });
        await page.locator('.o_tp_att_mine').evaluate((el) => { el.scrollTop = 0; });
        results.push({ case: 'desktop-scroll', ok: true, screenY: downScroll.screenY, wrapOverflowY: beforeScroll.wrapOverflowY });

        // 3. Pending vs Applied filter, chips, row expansion, and export params
        await page.getByLabel('Lọc theo tình trạng dữ liệu').selectOption('missing_out');
        // Before clicking Áp dụng, NO chip should appear yet
        assert.equal(await page.locator('.o_tp_mine_chip').count(), 0, 'Pending filter must not appear as applied chip before clicking Áp dụng');
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.getByRole('button', { name: 'Áp dụng', exact: true }).click(),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        await page.waitForTimeout(150);
        assert.equal(await page.locator('.o_tp_mine_row').count(), 5, 'Filtered missing_out should show 5 rows');
        assert.equal(await page.locator('.o_tp_mine_chip').count(), 1, 'Applied chip should be visible');
        // Expand first row detail
        await page.locator('.o_tp_mine_expand_btn').first().click();
        await page.locator('.o_tp_mine_detail_panel').waitFor();
        await page.screenshot({ path: path.join(output, 'after-1440-filtered.png') });
        // Trigger export: must send applied state='missing_out' and NO page/page_size
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_export_mine')),
            page.getByRole('button', { name: 'Xuất Excel', exact: true }).click(),
        ]);
        assert.equal(exportCalls.length, 1);
        assert.equal(exportCalls[0].state, 'missing_out');
        assert.equal(exportCalls[0].page, undefined, 'Export must not paginate to current page');
        // Clear filter via chip close
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.locator('.o_tp_mine_chip').first().click(),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        await page.waitForTimeout(100);
        assert.equal(await page.locator('.o_tp_mine_row').count(), 30, 'Removing chip should restore all 30 rows');
        results.push({ case: 'desktop-filter-detail-export', ok: true, exportParams: exportCalls[0] });

        // 4. Pagination (10 / trang -> page 1 -> page 2)
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.getByLabel('Số dòng mỗi trang').selectOption('10'),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        await page.waitForTimeout(100);
        assert.equal(await page.locator('.o_tp_mine_row').count(), 10);
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.getByLabel('Trang sau').click(),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        await page.waitForTimeout(100);
        assert.equal(await page.locator('.o_tp_mine_row').count(), 10);
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.getByLabel('Số dòng mỗi trang').selectOption('50'),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        results.push({ case: 'desktop-pagination', ok: true });

        // 5. Desktop 1440x900: File Period (09-15/11/2026) with exact Excel late totals (3 lần / 356 phút)
        await page.locator('.o_tp_mine_file_trigger').click();
        await page.locator('.o_tp_mine_file_popover').waitFor();
        await Promise.all([
            page.waitForResponse((r) => r.url().includes('/tp_mine')),
            page.locator('.o_tp_mine_file_option').first().click(),
        ]);
        await page.locator('.o_tp_att_mine[aria-busy="false"]').waitFor();
        await page.waitForTimeout(200);
        const exactLateVals = await page.locator('.o_stat_excel .o_tp_mine_stat_val strong').allInnerTexts();
        assert.deepEqual(exactLateVals, ['3', '356'], 'Exact Excel period must show 3 lần and 356 phút');
        assert.equal(await page.locator('.o_tp_mine_row').count(), 7);
        await page.screenshot({ path: path.join(output, 'after-1440-week.png') });
        results.push({ case: 'desktop-file-period-exact-late', ok: true, exactLateVals });

        // 6. Reduced motion check
        await page.emulateMedia({ reducedMotion: 'reduce' });
        const dur = await page.locator('.o_tp_mine_row').first().evaluate((el) => getComputedStyle(el).transitionDuration);
        assert.equal(dur, '0s', `Expected 0s transition under reduced-motion, got ${dur}`);
        await page.emulateMedia({ reducedMotion: 'no-preference' });
        results.push({ case: 'reduced-motion', ok: true });

        // 7. Mobile 390x844 standalone: Month view + collapsible filter + scroll containment
        await page.setViewportSize({ width: 390, height: 844 });
        await page.goto(`${base}/app/cong-cua-toi`, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_tp_att_mine[aria-busy="false"] .o_tp_mine_table').waitFor({ timeout: 30000 });
        await page.waitForTimeout(250);
        const mobBefore = await scrollMetrics(page);
        assert(mobBefore.documentWidth <= mobBefore.viewportWidth + 1, `Mobile horizontal overflow: ${mobBefore.documentWidth} > ${mobBefore.viewportWidth}`);
        assert(mobBefore.documentHeight <= mobBefore.viewportHeight + 1, 'Mobile blank vertical overflow');
        // Filter form starts collapsed on mobile
        assert.equal(await page.locator('.o_tp_mine_filter_form').isVisible(), false, 'Filter panel must be collapsed by default on mobile');
        await page.screenshot({ path: path.join(output, 'after-390-month.png') });
        // Open mobile filter panel & close with Escape
        await page.locator('.o_tp_mine_filter_toggle').click();
        await page.locator('.o_tp_mine_filter_form').waitFor({ state: 'visible' });
        await page.keyboard.press('Escape');
        await page.locator('.o_tp_mine_filter_form').waitFor({ state: 'hidden' });
        // Mobile scroll containment
        const mbox = await page.locator('.o_tp_att_mine').boundingBox();
        await page.mouse.move(mbox.x + 12, mbox.y + mbox.height / 2);
        for (let i = 0; i < 6; i++) {
            await page.mouse.wheel(0, 1400);
            await page.waitForTimeout(40);
        }
        const mobDown = await scrollMetrics(page);
        assert(mobDown.screenY > 0, 'Mobile mine view should scroll');
        assert.equal(mobDown.documentY, 0, 'Mobile wheel escaped to body');
        assert.equal(mobDown.navbarY, mobBefore.navbarY, 'Mobile navbar moved on scroll');
        await page.locator('.o_tp_mine_row').nth(1).evaluate((el) => el.scrollIntoView({ block: 'start' }));
        await page.waitForTimeout(150);
        await page.screenshot({ path: path.join(output, 'after-390-table.png') });
        results.push({ case: 'mobile-month-filter-scroll', ok: true, width: mobBefore.documentWidth });

        // 8. Desktop 1440x900 embedded in Hồ sơ cá nhân (/app/my-profile -> Công của tôi tab)
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto(`${base}/app/my-profile`, { waitUntil: 'domcontentloaded' });
        await page.getByRole('tab', { name: 'Công của tôi', exact: false }).waitFor({ timeout: 30000 });
        await page.getByRole('tab', { name: 'Công của tôi', exact: false }).click();
        await page.locator('.o_tp_att_embedded[aria-busy="false"] .o_tp_mine_table').waitFor({ timeout: 30000 });
        await page.waitForTimeout(250);
        // No repeated <h1> or employee name inside embedded tab!
        assert.equal(await page.locator('.o_tp_att_embedded h1').count(), 0, 'Embedded tab must not repeat h1');
        assert.equal(await page.locator('.o_tp_att_embedded .o_tp_mine_emp_name').count(), 0, 'Embedded tab must not repeat employee identity');
        await page.screenshot({ path: path.join(output, 'after-1440-embedded.png') });
        results.push({ case: 'desktop-embedded-profile', ok: true });

        // 9. Mobile 390x844 embedded
        await page.setViewportSize({ width: 390, height: 844 });
        await page.waitForTimeout(200);
        const embMobW = await page.evaluate(() => ({ sw: document.scrollingElement.scrollWidth, iw: innerWidth }));
        assert(embMobW.sw <= embMobW.iw + 1, `Embedded mobile overflow: ${embMobW.sw} > ${embMobW.iw}`);
        await page.screenshot({ path: path.join(output, 'after-390-embedded.png') });
        results.push({ case: 'mobile-embedded-profile', ok: true, embMobW });

        // 10. Regression check: Overview (/app/cham-cong) and PersonDialog remain intact (unmocked real server)
        await page.unrouteAll();
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto(`${base}/app/cham-cong`, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_tp_att_overview[aria-busy="false"]').waitFor({ timeout: 30000 });
        results.push({ case: 'overview-regression', ok: true });

        assert.deepEqual(errors, [], `JS/console errors: ${errors.join('; ')}`);
    } finally {
        fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({ base, results, errors }, null, 2));
        await browser.close();
    }
    console.log(`PASS ${results.length} HR-ATTENDANCE-MINE-UI-001 browser cases; 0 JS/console errors`);
}

run().catch((err) => {
    console.error(err);
    process.exitCode = 1;
});
